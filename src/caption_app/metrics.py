"""Application metrics live in the inference process, independent of Streamlit reruns."""
import re
from prometheus_client import Counter, Gauge, Histogram, Summary, disable_created_metrics

disable_created_metrics()
IMAGES = Counter('caption_images_total', 'Attempted images by outcome', ['mode', 'status', 'client'])
JOBS = Counter('caption_jobs_total', 'Completed jobs by outcome', ['mode', 'status', 'client'])
ACTIVE = Gauge('caption_active_jobs', 'Jobs in progress, including waiting for the CPU', ['mode'])
READY = Gauge('caption_model_ready', '1 when model is available for inference')
MODEL_BYTES = Gauge('caption_model_weight_bytes', 'Model parameter and buffer bytes; excludes runtime overhead')
LAST_BULK = Gauge('caption_last_bulk_images', 'Number of image members in the most recent accepted bulk job')
REJECTED = Counter('caption_rejected_uploads_total', 'Rejected requests / archives')
UPLOAD_BYTES = Counter('caption_upload_bytes_total', 'Accepted uploaded bytes', ['mode', 'client'])
INFERENCE = Histogram('caption_inference_seconds', 'Model.generate wall time, excluding queue/decode', ['mode'],
                      buckets=(0.25, 0.5, 1, 2, 5, 10, 20, 40, 80, 160, 320))
IMAGE_TIME = Histogram('caption_image_duration_seconds', 'Per-image decode, queue and inference wall time', ['mode'],
                       buckets=(0.5, 1, 2, 5, 10, 20, 40, 80, 160, 320, 640))
JOB_TIME = Summary('caption_job_duration_seconds', 'Full accepted job wall time', ['mode', 'client'])
IMAGE_BYTES = Summary('caption_image_upload_bytes', 'Encoded bytes per attempted image, including corrupt images', ['mode', 'client'])
CAPTION_LENGTH = Summary('caption_length_characters', 'Unicode characters per successful generated caption, including spaces', ['mode', 'client'])
PROCESS_RAM = Gauge('caption_process_memory_bytes', 'Inference process resident memory in bytes')
PROCESS_CPU = Gauge('caption_process_cpu_percent', 'Process CPU percent; 100 percent equals one full CPU core')


def client_session(session_id):
    """Readable first 12 safe characters of the supplied session ID, not a hash bucket.

    Intended for a small local coursework demo. New sessions create new series;
    short prefixes can still collide and must not be treated as unique people.
    """
    return re.sub(r'[^A-Za-z0-9_-]', '', session_id)[:12] or 'anonymous'


for _mode in ('single', 'bulk'):
    ACTIVE.labels(_mode).set(0)
    INFERENCE.labels(_mode)
    IMAGE_TIME.labels(_mode)
    JOB_TIME.labels(_mode, 'anonymous')
    IMAGE_BYTES.labels(_mode, 'anonymous')
    CAPTION_LENGTH.labels(_mode, 'anonymous')
    UPLOAD_BYTES.labels(_mode, 'anonymous')
    for _status in ('success', 'error'):
        IMAGES.labels(_mode, _status, 'anonymous')
    for _status in ('success', 'partial', 'error'):
        JOBS.labels(_mode, _status, 'anonymous')
