"""CPU BLIP inference API on 8000; independent Prometheus exporter on 8001."""
import io
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import psutil
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from prometheus_client import start_http_server
from . import metrics as m
from .image_inputs import MAX_IMAGE_BYTES, MAX_UPLOAD_BYTES, decode_image, zip_images

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('caption')
from .paths import ROOT
MODEL_DIR = ROOT / 'models' / 'blip-base'
engine = None
load_error = None
inference_lock = threading.Lock()


class CaptionEngine:
    def __init__(self):
        import torch
        from transformers import BlipForConditionalGeneration, BlipProcessor
        self.torch = torch
        torch.set_num_threads(max(1, int(os.getenv('CAPTION_THREADS', '2'))))
        self.processor = BlipProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True, use_fast=False)
        self.model = BlipForConditionalGeneration.from_pretrained(
            str(MODEL_DIR), local_files_only=True, use_safetensors=True).to('cpu').eval()
        size = sum(t.numel() * t.element_size() for t in self.model.parameters())
        size += sum(t.numel() * t.element_size() for t in self.model.buffers())
        m.MODEL_BYTES.set(size)

    def caption(self, image, mode):
        # One model instance, one inference at a time: predictable CPU/RAM use.
        with inference_lock, self.torch.inference_mode():
            inputs = self.processor(images=image, return_tensors='pt')
            start = time.perf_counter()
            output = self.model.generate(**inputs, max_new_tokens=30, num_beams=1, do_sample=False)
            elapsed = time.perf_counter() - start
            m.INFERENCE.labels(mode).observe(elapsed)
            return self.processor.decode(output[0], skip_special_tokens=True), elapsed


def watch_process(stop):
    process = psutil.Process()
    process.cpu_percent(None)
    while not stop.wait(1):
        m.PROCESS_RAM.set(process.memory_info().rss)
        m.PROCESS_CPU.set(process.cpu_percent(None))


@asynccontextmanager
async def lifespan(app):
    global engine, load_error
    server, thread = start_http_server(8001, addr='127.0.0.1')
    stop = threading.Event()
    monitor = threading.Thread(target=watch_process, args=(stop,), daemon=True)
    monitor.start()
    try:
        engine = CaptionEngine()
        m.READY.set(1)
        log.info('CPU model ready; API 8000; exporter 8001')
    except Exception as exc:
        load_error = str(exc)
        m.READY.set(0)
        log.exception('Model load failed. Run scripts/setup_model.py first.')
    yield
    stop.set()
    monitor.join(timeout=2)
    m.READY.set(0)
    server.shutdown()
    server.server_close()


app = FastAPI(title='DA3408 CPU Captioning', lifespan=lifespan)


@app.get('/healthz')
def health():
    if engine is None:
        raise HTTPException(503, 'Model unavailable; check backend terminal and run setup_model.py.')
    return {'status': 'ready', 'device': 'cpu', 'model': 'Salesforce/blip-image-captioning-base'}


@app.post('/caption')
def caption(file: UploadFile = File(...), mode: Literal['single', 'bulk'] = Form(...),
            session_id: str = Form('anonymous', max_length=128)):
    if engine is None:
        raise HTTPException(503, 'Model unavailable; check backend terminal.')
    limit = MAX_IMAGE_BYTES if mode == 'single' else MAX_UPLOAD_BYTES
    try:
        data = file.file.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Upload exceeds the size limit.')
        images = [(file.filename or 'image', data)] if mode == 'single' else zip_images(data)
    except Exception as exc:
        m.REJECTED.inc()
        raise HTTPException(400, str(exc)) from exc
    finally:
        file.file.close()
    client = m.client_session(session_id)
    start = time.perf_counter()
    m.ACTIVE.labels(mode).inc()
    m.UPLOAD_BYTES.labels(mode, client).inc(len(data))
    if mode == 'bulk':
        m.LAST_BULK.set(len(images))
    rows = []
    try:
        for name, payload in images:
            begin = time.perf_counter()
            m.IMAGE_BYTES.labels(mode, client).observe(len(payload))
            try:
                image = decode_image(payload)
                text, seconds = engine.caption(image, mode)
                rows.append({'file': name, 'caption': text, 'status': 'success',
                             'inference_seconds': round(seconds, 3), 'error': ''})
                m.IMAGES.labels(mode, 'success', client).inc()
                m.CAPTION_LENGTH.labels(mode, client).observe(len(text))
            except Exception:
                log.exception('Failed image in %s job', mode)
                rows.append({'file': name, 'caption': '', 'status': 'error',
                             'inference_seconds': None, 'error': 'Unreadable image or inference failure; check backend log.'})
                m.IMAGES.labels(mode, 'error', client).inc()
            finally:
                m.IMAGE_TIME.labels(mode).observe(time.perf_counter() - begin)
        successes = sum(row['status'] == 'success' for row in rows)
        status = 'success' if successes == len(rows) else ('partial' if successes else 'error')
        m.JOBS.labels(mode, status, client).inc()
        return {'mode': mode, 'status': status, 'client_session': client, 'results': rows,
                'elapsed_seconds': round(time.perf_counter() - start, 3)}
    finally:
        m.ACTIVE.labels(mode).dec()
        m.JOB_TIME.labels(mode, client).observe(time.perf_counter() - start)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000, workers=1)
