# Caption Lab — DA3408 Assignment 4

Caption Lab is a local, CPU-only image captioning application. A Streamlit interface accepts one image or a ZIP of images; a FastAPI backend runs `Salesforce/blip-image-captioning-base` and returns captions that can be downloaded as CSV. Prometheus collects application and Ubuntu system metrics, Grafana displays the live dashboard, and Alertmanager forwards alerts to a local receiver.

## Repository at a glance

```text
AIOps-Assiginment4/
├── src/caption_app/          # Streamlit UI, CPU backend, image validation, metrics
├── scripts/                  # Setup, launchers, dashboard generator, service checks
├── monitoring/               # Prometheus scrape config, rules, Alertmanager config
├── grafana/                  # Dashboard JSON and provisioning
├── demo_inputs/              # Local single-image and bulk-upload examples, if provided
├── models/blip-base/         # Model downloaded during setup; not required in Git
├── evidence/                 # Local logs, CSV results and screenshots, if provided
├── tests/                    # API and image-input tests
├── AI_Attributio_Prompts.md  # AI prompt attribution
├── AI_DISCLOSUREs.md         # AI-use disclosure
├── compose.yml               # Prometheus, Alertmanager and optional Grafana
├── README.md
├── requirements.txt          # Python dependencies
└── pyproject.toml
```

Generated model weights, personal demo photos and runtime evidence might not be included in a Git clone. Check `git ls-files demo_inputs evidence models` to see which examples are tracked. The commands below work with your own JPG, PNG or WebP images.

## First-time setup on Ubuntu

Use Ubuntu 24.04 on a 64-bit x86 or ARM machine with adequate free disk space and memory. Install [Docker Engine and the Compose plugin](https://docs.docker.com/engine/install/ubuntu/) first. Confirm that `docker compose version` and `docker info` work for your user. Initial setup needs internet access for packages, container images and model weights; inference later reads the local model.

```bash
sudo apt update
sudo apt install -y git python3-venv prometheus-node-exporter

cd ~
git clone https://github.com/Ramanagopalkodali/AIOps-Assiginment4.git
cd ~/AIOps-Assiginment4

bash scripts/setup_python.sh
source .venv/bin/activate
python -u scripts/setup_model.py
bash scripts/run_tests.sh
```

`setup_python.sh` creates `.venv` in the cloned repository and installs the application dependencies. Wait for the model setup script to print `Saved:`. The model is stored in `models/blip-base/`; a fresh clone cannot run inference until this step finishes. The tests use a stub model and should pass independently of a live captioning run.

Start node_exporter and the monitoring containers:

```bash
cd ~/AIOps-Assiginment4
sudo systemctl enable --now prometheus-node-exporter
docker compose --profile fresh-grafana up -d
docker compose ps
```

The `fresh-grafana` profile is for a machine **without another Grafana using port 3000**. It starts Grafana alongside Prometheus and Alertmanager. These containers use Ubuntu host networking, so no port-9091 forwarder is needed. Prometheus is at `127.0.0.1:9090` and Grafana at `127.0.0.1:3000` inside Ubuntu. On first login, use the Grafana credentials configured in `compose.yml` and change the password when prompted.

The provisioned Prometheus datasource has UID `prometheus`. Before relying on the dashboard, check that the datasource UID referenced in `grafana/dashboard.json` matches it. A dashboard exported from a different Grafana installation may contain another UID; update the datasource reference or provisioning UID and reload Grafana if needed. The dashboard's JSON must be the working version you submit.

## Run after setup

Use separate Ubuntu terminals. The launch scripts automatically activate `.venv` when it exists; you do not need Conda. Keep the backend, Streamlit and alert receiver terminals open.

**Terminal 1 — start monitoring if it is stopped:**

```bash
cd ~/AIOps-Assiginment4
sudo systemctl start prometheus-node-exporter
docker compose --profile fresh-grafana up -d
```

**Terminal 2 — CPU captioning backend and metrics exporter:**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_backend.sh
```

Wait for `CPU model ready`. The API runs on port 8000 and `/metrics` runs separately on port 8001.

**Terminal 3 — Streamlit application:**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_app.sh
```

**Terminal 4 — local alert receiver:**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_receiver.sh
```

For a later run, start with this section; there is no need to reinstall packages or download the model again. Do not start multiple backend instances: each would try to load its own model and bind the same ports.

## Open and check

| Page | Address in Ubuntu |
|---|---|
| Streamlit | http://127.0.0.1:8501 |
| Application metrics | http://127.0.0.1:8001/metrics |
| Prometheus targets | http://127.0.0.1:9090/targets |
| Grafana | http://127.0.0.1:3000 |
| Prometheus alerts | http://127.0.0.1:9090/alerts |

Check that `caption_app` and `node` are **UP** on the Targets page. The **Caption Lab** dashboard should show health, image throughput, latency, bulk activity and Ubuntu CPU/RAM/disk data. Select **Last 15 minutes** and **5s refresh**. Short-window rate panels may show no value until images are processed.

## Metrics and simple calculations

The application exporter is at `http://127.0.0.1:8001/metrics`. These are the main families to look for; Python and process metrics on the same page come from `prometheus_client` automatically.

| Type | Example | What it tells us |
|---|---|---|
| Counter | `caption_images_total{mode,status,client}` | Attempted images by Single/Bulk and success/error |
| Counter | `caption_jobs_total{mode,status,client}` | Completed upload jobs by outcome |
| Gauge | `caption_active_jobs{mode}`; `caption_model_ready` | Current work and whether BLIP is ready |
| Gauge | `caption_process_memory_bytes` | Resident memory used by the backend process |
| Histogram | `caption_inference_seconds` | Per-image model inference time, with `_bucket`, `_sum`, `_count` series |
| Summary | `caption_job_duration_seconds` | Full accepted job time, with `_sum` and `_count` series |

The `mode`, `status` and `client` labels help separate workloads and outcomes. A client label is a request grouping, not a count of unique people. More metric families, including per-image duration, uploaded bytes and caption length, are in `src/caption_app/metrics.py` and the saved `evidence/logs/actual_app_metrics.txt`.

**One captured 22-image bulk run:** the exporter showed 22 successful bulk images, one successful bulk job, `caption_model_ready = 1`, 67.342 seconds of total model inference time and 68.119 seconds for the full job. These values belong to that run; counters reset when the backend restarts.

| Calculation | Manual reading of that run | Dashboard query idea |
|---|---|---|
| Mean inference time | `67.342 / 22 ≈ 3.06 seconds/image` | `sum(rate(caption_inference_seconds_sum{mode="bulk"}[5m])) / sum(rate(caption_inference_seconds_count{mode="bulk"}[5m]))` |
| Whole-job average throughput | `22 / 68.119 ≈ 0.32 images/second` | `sum(rate(caption_images_total{mode="bulk",status="success"}[5m]))` |
| Mean full-job time | `68.119 / 1 = 68.119 seconds/job` | `sum(rate(caption_job_duration_seconds_sum{mode="bulk"}[5m])) / sum(rate(caption_job_duration_seconds_count{mode="bulk"}[5m]))` |
| CPU used | `100 × (1 − idle fraction)` | Based on `rate(node_cpu_seconds_total{mode="idle"}[5m])` |
| RAM used | `100 × (1 − available bytes / total bytes)` | Based on `node_memory_MemAvailable_bytes` and `node_memory_MemTotal_bytes` |

The manual throughput is an average over the job; a Prometheus `rate()` uses a selected scrape window, so its displayed value need not equal 0.32. A histogram percentile is estimated with `histogram_quantile()` from `_bucket` counts, not calculated exactly from the total time. During evaluation, I can explain these divisions and the units rather than treating the PromQL as a black box.

## Reproduce single and bulk captioning

If the demo images or archives are present in your clone, use `demo_inputs/single/images.jpeg` for Single and `demo_inputs/bulk/archives/bulk_22_images.zip` for Bulk. Otherwise, put your own image in `demo_inputs/single/` and JPG, PNG or WebP photos in `demo_inputs/bulk/photos/`, then build a ZIP:

```bash
cd ~/AIOps-Assiginment4
mkdir -p demo_inputs/single demo_inputs/bulk/photos demo_inputs/bulk/archives evidence/results
source .venv/bin/activate
python scripts/make_bulk_zip.py demo_inputs/bulk/photos demo_inputs/bulk/archives/demo.zip
```

Open Streamlit, choose **Single image**, upload one photo, generate the caption and download its CSV. Then choose **Bulk ZIP**, upload the ZIP and download the bulk CSV. Save your actual results in `evidence/results/`. The app accepts at most 60 image entries; its UI also lists upload size limits. Caption quality should be judged from the returned text, not inferred from successful processing alone.

If `demo_inputs/bulk/archives/messy_bulk.zip` is present, it demonstrates a mixed archive: valid image members receive captions, unreadable image members produce error rows, and the accepted job has `partial` status. Non-image entries and Mac metadata are ignored. An invalid ZIP archive itself is rejected. This extra test is optional for the assignment.

To demonstrate a resource correlation, process a bulk ZIP while viewing the dashboard's **active bulk jobs**, **VM CPU** and **VM memory** panels on the same time range.

To save a live service and metrics check after all services are running:

```bash
cd ~/AIOps-Assiginment4
source .venv/bin/activate
python scripts/check_services.py
bash scripts/run_tests.sh
```

## Alerts

`monitoring/rules.yml` defines exporter, model-readiness, node-exporter and high-CPU alerts. `monitoring/alertmanager.yml` sends notifications to the receiver started in Terminal 4. To demonstrate `CaptionAppDown`, leave Prometheus, Alertmanager and the receiver running, stop the backend with Ctrl+C, wait for the rule to fire in Prometheus, then restart the backend and check for a resolved notification. A backend restart resets its application counters, so generate new workload before recording final graphs.

## Submission

The assignment deliverables are the GitHub source repository, including `monitoring/prometheus.yml`, the final `grafana/dashboard.json`, and an approximately **one-minute** dashboard recording with **5-second refresh**. Add the actual video and ensure evaluators can access it. Keep screenshots, CSVs and logs in `evidence/` if you choose to include them; do not describe local files as committed unless `git ls-files` shows them. If a separate course instruction requires a **2–5-minute working-demo video**, provide that recording as well.

AI assistance and prompts are documented in `AI_DISCLOSUREs.md` and `AI_Attributio_Prompts.md` (the spellings used in this repository). Review those files so they accurately describe the work you performed. Complex generated PromQL or regex should retain the prompt used in its configuration comments.

## Author's prepared VM

The author demonstrated the project from `~/DA3408-A4-clean` using an existing `aiops` Conda environment and a separate Grafana container. That VM needed a Docker-bridge connection forwarder on port 9091. The fresh-clone steps above use the repository's `.venv` and the Compose-managed Grafana profile instead.
