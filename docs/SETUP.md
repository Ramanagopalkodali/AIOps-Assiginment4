# Setup and run inside your Ubuntu VM

## 1. Environment and folders

```bash
conda activate aiops
cd ~/DA3408-A4-clean
mkdir -p evidence/{logs,screenshots,results,video}
chmod +x scripts/*.sh
python -m pip check
```

Your packages are already installed. requirements.txt records the selected
application dependency versions, not every package in your aiops environment.
Save `python -m pip freeze > requirements-installed.txt` after checks. The
setup_python.sh script is for a fresh isolated .venv only; do not run it for
your current aiops setup. Python 3.10 or newer is supported.

## 2. Tests and dashboard

```bash
set -o pipefail
bash scripts/run_tests.sh 2>&1 | tee evidence/logs/unit_tests.txt
python scripts/build_dashboard.py
```

Take a screenshot of the test summary showing all eleven tests passing. The
deliberate corrupt-image test logs an expected exception; the final test status
determines success. The API tests use a stub model, not downloaded BLIP.

## 3. Download model

```bash
python -u scripts/setup_model.py 2>&1 | tee evidence/logs/model_setup.txt
ls -lh models/blip-base/
```

Wait for `Saved:` and a complete model.safetensors/config/processor/tokenizer
directory. If it seems quiet, monitor `du -sh ~/.cache/huggingface/hub` from a
second terminal before deciding it has stalled. Migrated complete models do not
need downloading again. Capture the successful save/listing, not an interrupted
download. Initial setup needs Internet; runtime uses local files only.

## 4. Start the three terminals

In each terminal first run `conda activate aiops` and `cd ~/DA3408-A4-clean`.

Terminal 1:

```bash
set -o pipefail
bash scripts/run_backend.sh 2>&1 | tee evidence/logs/backend.log
```

Wait for CPU model ready and Application startup complete. Terminal 2:

```bash
bash scripts/run_app.sh 2>&1 | tee evidence/logs/streamlit.log
```

Terminal 3:

```bash
bash scripts/run_receiver.sh
```

Open http://127.0.0.1:8501 in Ubuntu. A separate temporary terminal can verify:

```bash
curl -fsS http://127.0.0.1:8000/healthz | tee evidence/results/backend_health.json
curl -fsS http://127.0.0.1:8001/metrics > evidence/results/metrics_before_requests.txt
```

Capture health ready/device CPU and model-ready=1. Do not start multiple backend
instances or use uvicorn reload/multiple workers: that duplicates models/exporters.

## 5. Single and Bulk input placement

Copy your own photos using Ubuntu's file manager:

- Single examples: demo_inputs/single/
- Bulk source photographs: demo_inputs/bulk/photos/

In Single mode upload one image from demo_inputs/single, generate a caption and
download the CSV into evidence/results/single_caption.csv. Capture the photograph
and actual caption together.

Create a bulk ZIP:

```bash
python scripts/make_bulk_zip.py demo_inputs/bulk/photos demo_inputs/bulk/archives/demo.zip
```

Upload that ZIP in Bulk mode. For a longer measured workload, use `--copies 3`
with a total of no more than 60 entries and disclose repeated photos. Copying
actual photos does not fabricate inference: each entry is processed for real.
Capture Bulk results, save CSV to evidence/results and compare live resource
graphs once monitoring is configured.

Limits: 20 MiB per image; 100 MiB uploaded ZIP; 200 MiB expanded; 60 images.
ZIPs are not extracted. Invalid archives are rejected; corrupt image members
produce error rows while valid members continue. Captions may be inaccurate.
The CSV initially downloads to your browser's download folder unless you choose
another destination; move it to evidence/results yourself.

## 6. Monitoring and recording

Follow docs/MONITORING.md for node_exporter and monitoring configuration. Then
run `python scripts/check_services.py`; output files go in evidence/logs.
Capture actual targets/metrics/dashboard/alerts and the video as described in
docs/EVIDENCE.md. If changing generated dashboard JSON in Grafana, export your
final version back to grafana/dashboard.json. Rerunning the generator overwrites
that file. The dashboard refresh remains 5 seconds.

## 7. Stop and restart

Stop app/receiver terminals with Ctrl+C. Stop monitoring containers with
`docker compose down`; named volumes persist without -v. Your pre-existing
Grafana is outside this Compose project and is not stopped by this command.
Do not delete existing Docker volumes, environments or the previous repository.
For later starts, activate aiops and rerun the launch scripts; no reinstall.
