# Evidence and final submission

The brief explicitly asks for GitHub code, Grafana dashboard JSON, and about a
minute of dashboard recording at five-second refresh. AI disclosure follows the
course-wide policy. Screenshots/logs below support verification; do not treat
every suggested screenshot as a separately mandated deliverable.

| Evidence | Save location |
|---|---|
| Eleven updated/refactored tests pass | evidence/logs/unit_tests.txt and screenshots/01_tests.png |
| Model saved successfully | evidence/logs/model_setup.txt and screenshots/02_model.png |
| Real CPU readiness / model ready=1 | evidence/results/backend_health.json and screenshots/03_health.png |
| Single photograph and caption | screenshots/04_single.png; results/single_caption.csv |
| Bulk captions, successes/errors | screenshots/05_bulk.png; results/bulk_captions.csv |
| Counters/gauges/histograms/three Summaries/client labels | results/actual_metrics.txt |
| Prometheus app and node targets UP | screenshots/06_targets.png; logs/actual_prometheus_targets.json |
| Visible graph stories, units, legends and CPU/RAM correlation | screenshots/07_dashboard_*.png |
| Actual firing/resolved alert delivery | screenshots/08_alert_*.png; logs/alerts.jsonl |
| Roughly 60–75s dashboard video with 5s refresh | evidence/video/dashboard_demo.mp4 |

Record during an actual bulk upload. Show health/work first, latency next, then
Ubuntu resources correlated with bulk jobs; scroll slowly so the Text-panel
stories and plot labels are legible. X-axis Time is named in those visible Text
panels; Grafana provides native timestamp ticks. Validate colors/line markers on
screen, not only in JSON. A gap before samples is not zero latency.

Final dashboard: export from actual Grafana to grafana/dashboard.json after edits.
Put monitoring/prometheus.yml in the GitHub repo and clearly link its path from
README. Save the installed environment with `python -m pip freeze >
requirements-installed.txt`. Personalize AI_DISCLOSURE.md to state actual tools,
changes and verification. Understand the metrics and PromQL for your viva.

Demo photos, model weights and evidence data are ignored by Git by default. Add
selected real evidence intentionally with `git add -f PATH` if needed. Do not
upload private photos unintentionally. Large video files should use the TA's
specified submission method rather than an oversized Git commit. Keep the repo
private until the deadline when instructed, while granting evaluators access.
