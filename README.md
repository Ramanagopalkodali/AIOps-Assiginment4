# Caption Lab — DA3408 Assignment 4

Caption Lab is a local, CPU-only image captioning app built with Streamlit and `Salesforce/blip-image-captioning-base`. It captions one uploaded image or processes a ZIP of images and exports the results as CSV. Prometheus collects application and Ubuntu host metrics, Grafana presents them in a live dashboard, and Alertmanager sends alerts to a local receiver.

## Repository at a glance

```text
DA3408-A4-clean/
├── src/caption_app/          # Streamlit UI, CPU captioning backend, image handling, metrics
├── scripts/                  # Model setup, launchers, dashboard generation, service checks
├── monitoring/
│   ├── prometheus.yml        # Scrapes the app and node_exporter
│   ├── rules.yml             # Prometheus alert rules
│   └── alertmanager.yml      # Alert routing
├── grafana/
│   ├── dashboard.json        # Grafana dashboard for submission
│   └── provisioning/         # Dashboard and data source configuration
├── demo_inputs/
│   ├── single/               # Single-image example
│   └── bulk/
│       ├── photos/           # 22 source photos
│       └── archives/         # Normal 22-image ZIP and messy test ZIP
├── models/blip-base/         # Locally downloaded BLIP model
├── evidence/
│   ├── logs/                 # Metrics, target checks, tests and application logs
│   ├── results/              # Caption CSVs for single, bulk and messy bulk
│   └── screenshots/          # Application and monitoring evidence
├── tests/                    # API and image-input tests
├── AI_Attributio_Prompts.md  # AI prompts used
├── AI_DISCLOSUREs.md         # AI-use disclosure
├── compose.yml               # Prometheus and Alertmanager services
├── README.md                 # Project overview and instructions
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Python project configuration
```

## First-time setup on Ubuntu

Docker Engine and the Docker Compose plugin must already be installed. The first setup requires internet access to download Python packages, Docker images and the BLIP model.

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

sudo systemctl enable --now prometheus-node-exporter
docker compose --profile fresh-grafana up -d
```

Wait for the model setup script to print `Saved:`. The `fresh-grafana` profile starts Grafana along with Prometheus and Alertmanager on a machine where port 3000 is free. The application launch scripts use `.venv` automatically.

For later runs, you do not need to repeat the installation or model download. Open separate terminals, run `cd ~/AIOps-Assiginment4` in each, and start `bash scripts/run_backend.sh`, `bash scripts/run_app.sh` and `bash scripts/run_receiver.sh`.

## Run on the prepared Ubuntu VM
Open a separate terminal for each process that stays running.

**Terminal 1 — Prometheus, Alertmanager, node exporter and Grafana**

```bash
cd ~/AIOps-Assiginment4
sudo systemctl start prometheus-node-exporter
docker compose -f compose.yml up -d
docker start grafana
```

If Grafana is already running, the last command can be skipped.

**Terminal 2 — captioning backend and application metrics**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_backend.sh
```

Wait for the CPU model to report ready.

**Terminal 3 — Streamlit app**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_app.sh
```

**Terminal 4 — local alert receiver**

```bash
cd ~/AIOps-Assiginment4
bash scripts/run_receiver.sh
```

**Terminal 5 — Grafana connection forwarder, if not already running**

```bash
A4_DOCKER_GATEWAY=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')
socat TCP-LISTEN:9091,bind="$A4_DOCKER_GATEWAY",fork,reuseaddr TCP:127.0.0.1:9090
```

Prometheus runs on **9090**. Port **9091** forwards the existing standalone Grafana container to that server. Leave the `socat` terminal open. A fresh Grafana installation needs a Prometheus datasource whose UID matches the references in `grafana/dashboard.json`.

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

## Reproduce the demo

1. In **Single**, upload `demo_inputs/single/images.jpeg` and generate a caption. The exported example is `evidence/results/single_captions.csv`.
2. In **Bulk**, upload `demo_inputs/bulk/archives/bulk_22_images.zip`. Download the results as CSV; the saved example is `evidence/results/bulk_captions.csv`.
3. For error handling, upload `demo_inputs/bulk/archives/messy_bulk.zip`. It combines the original valid images with unreadable image entries. Valid images can still receive captions, while the bad entries produce error rows; the saved example is `evidence/results/messy_bulky_captions.csv`. This is a **partial job**, not rejection of the whole archive.
4. Run Bulk again while watching Grafana to compare image activity with CPU and memory use.

To check the services or run the repository tests:
activate the environment and.
```bash
cd ~/AIOps-Assiginment4
python scripts/check_services.py
bash scripts/run_tests.sh
```

For the alert path, keep Prometheus, Alertmanager and `scripts/run_receiver.sh` running; stop the backend, wait for `CaptionAppDown` to fire on the Alerts page, then restart the backend and check for the resolved notification. Do this before the final video because a backend restart resets its live counters.

## Submission and notes

The assignment requests the GitHub code, including `monitoring/prometheus.yml`, the exported `grafana/dashboard.json`, and about a **one-minute video** of the dashboard refreshing every **5 seconds**. The CSVs, screenshots and logs in `evidence/` support the demonstration. Record and add the video separately; the tree shown for this revision contains only `evidence/video/README.md`.

The Python Prometheus Summary produces `_sum` and `_count` series, although the assignment text calls the count suffix `_total`. The exported `grafana/dashboard.json` is the final dashboard; if `scripts/build_dashboard.py` is rerun, check its datasource UID before importing the regenerated JSON. Dashboard query assistance is documented in `AI_PROMPTS_DASHBOARD.md`, and the use of ChatGPT is described in `AI_DISCLOSURE.md`.
