# Caption Lab — DA3408 Assignment 4

CPU-only Single-image and Bulk-ZIP captioning with application metrics, Ubuntu
node metrics, a Grafana dashboard and a local alerting pipeline.

This is the complete restructured repository. Use it in Ubuntu VirtualBox on your
Mac. Your existing aiops Conda environment remains installed; no reinstall is
needed. The complete walkthrough is [docs/SETUP.md](docs/SETUP.md).

## Repository layout

| Path | Purpose |
|---|---|
| src/caption_app/ui.py | Streamlit uploads, preview, results and CSV download |
| src/caption_app/backend.py | CPU BLIP API and separate metrics exporter |
| src/caption_app/metrics.py | Counters, gauges, histograms and three Summaries |
| src/caption_app/image_inputs.py | Bounded image/ZIP validation |
| src/caption_app/paths.py | Stable project/model paths |
| scripts/ | Launchers, model setup, dashboard generator, checks, migration |
| monitoring/ | prometheus.yml, alert rules and Alertmanager configuration |
| grafana/ | Dashboard JSON and provisioning |
| demo_inputs/single/ | Your real Single-mode photographs |
| demo_inputs/bulk/photos/ | Your real Bulk-mode photographs |
| demo_inputs/bulk/archives/ | ZIPs generated from those photographs |
| evidence/screenshots/ | Your actual screenshots |
| evidence/logs/ | Test, model, backend, scrape and alert logs |
| evidence/results/ | Caption CSVs and metric captures |
| evidence/video/ | Final dashboard recording |
| models/blip-base/ | Downloaded weights; excluded from Git |
| tests/ | Upload and API tests |
| docs/ | Setup, migration, metrics/viva, evidence and validation guidance |

Only folder instructions are bundled in demo_inputs and evidence. Supply your own
photos and collect real results; no invented pictures, captions or measurements
are included. Uploads are processed in memory and are not automatically saved.

## Start with your installed environment

```bash
conda activate aiops
cd ~/DA3408-A4-clean
chmod +x scripts/*.sh
bash scripts/run_tests.sh
python scripts/build_dashboard.py
```

Expected: eleven tests pass; 32 dashboard panels are generated (22 metric panels
and 10 visible Text panels). Then download the model if not already migrated:

```bash
python -u scripts/setup_model.py
```

Terminal 1: `bash scripts/run_backend.sh`

Terminal 2: `bash scripts/run_app.sh`

Terminal 3: `bash scripts/run_receiver.sh`

Run `conda activate aiops` and `cd ~/DA3408-A4-clean` in each terminal first.
Launchers set the src package path; do not run backend.py directly by file path.

Open http://127.0.0.1:8501 in Ubuntu. All inference remains on CPU. Services expose
API 8000, app metrics 8001, Streamlit 8501, Prometheus 9090, node_exporter 9100,
Alertmanager 9093, local receiver 9001 and your existing Grafana 3000.

## Existing Grafana

Your existing Grafana already occupies port 3000. The Grafana service in compose.yml
is now opt-in under profile fresh-grafana; ordinary compose up does not create a
second Grafana. Keep your grafana-storage volume. Monitoring connectivity to the
existing bridge-network container still needs configuring; see docs/MONITORING.md.
The profile is for a fresh standalone installation only, not your current VM.

## Assignment coverage

Code includes Single/Bulk CPU captioning, a separate exporter, Counter/Gauge/
Histogram/Summary, short actual session labels, node scraping, readable dashboard
stories/time labels, bulk-resource correlation and local alerts. Three Summaries
cover job duration, encoded image bytes and successful caption length. Raw IDs are
shortened to 12 safe characters for a small demo; prefixes can collide.

Final deliverables still require real runs: GitHub source (including
monitoring/prometheus.yml), dashboard JSON, roughly one-minute video at 5s refresh
and truthful AI disclosure. See [docs/EVIDENCE.md](docs/EVIDENCE.md).

## Migration and verification

[docs/MIGRATION.md](docs/MIGRATION.md) explains changed commands and copying local
data. [docs/VALIDATION.md](docs/VALIDATION.md) distinguishes checks performed here
from tests and demonstrations still needed on your VM. Previous test results do
not automatically validate the refactored layout. Review AI_DISCLOSURE.md before
submission and retain your own edits from the previous project.
