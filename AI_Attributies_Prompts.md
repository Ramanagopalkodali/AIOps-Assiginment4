# AI attribution and PromQL prompts

This file accompanies `AI_DISCLOSUREs.md`. It records the AI-assisted query work for this Caption Lab repository. The source files also contain attribution: `scripts/build_dashboard.py` records the dashboard prompt and panel-level explanations, and `monitoring/rules.yml` records the alert prompt. This table is an index of the queries in `grafana/dashboard.json`, **not** a claim that every panel was created with a separate chat prompt.

## Prompts recorded in the code

**Dashboard-wide prompt** (recorded at the top of `scripts/build_dashboard.py`):

> Build an accessible captioning observability dashboard with five-second refresh. Order health, work, latency, then VM resources. Use linear labeled axes, units, legends and explanatory stories. Distinguish series by dash/point shapes as well as Okabe-Ito colors. Correlate bulk activity with VM CPU/RAM on shared time. Use histogram_quantile for p95, rate(sum)/rate(count) for weighted mean latency, and clearly label metric reset behavior and VM versus process measurements.

**Visible-story prompt** (recorded beside the dashboard text panels in the same script):

> Add concise visible stories above every pair of plots and label Time as the shared x-axis, with browser-local timezone and linear y-axis units.

**Alert-rule prompt** (recorded in `monitoring/rules.yml`):

> Create local monitoring alerts for a CPU captioning app: unavailable exporter, unavailable model, node exporter down, and VM CPU >80%. Use sustained conditions, labels and explanations. Never invent measurements.

**High-CPU expression prompt** (recorded beside that rule):

> Compute Ubuntu VM non-idle CPU percent averaged over cores, with rate over one minute, and alert above 80% for 30 seconds.

The dashboard descriptions include shorter `AI prompt:` notes. Those are **recorded query instructions/explanations**, not an invented transcript of a separate conversation for each panel. Where no specific note exists, the dashboard-wide prompt is the recorded attribution.

## Prometheus alert rules

| Alert | PromQL from `monitoring/rules.yml` | Recorded prompt/origin |
|---|---|---|
| `CaptionAppDown` | `up{job="caption_app"} == 0` | Alert-rule prompt above: unavailable exporter. |
| `CaptionModelNotReady` | `caption_model_ready{job="caption_app"} == 0` | Alert-rule prompt above: unavailable model. |
| `NodeExporterDown` | `up{job="node"} == 0` | Alert-rule prompt above: node exporter down. |
| `VMCPUHigh` | `100 * (1 - avg(rate(node_cpu_seconds_total{job="node",mode="idle"}[1m]))) > 80` | High-CPU expression prompt above. |

These are the four rules in the original monitoring configuration. Do not copy alert names or thresholds from another student's repository into this attribution.

## Grafana dashboard panels

The following expressions were read from `grafana/dashboard.json` in the provided project copy. `single`/`bulk` and `success`/`error` rows may be generated as multiple series from one Python template. A panel's `AI prompt:` description is summarized in the third column when present; the full note remains in the generator and dashboard JSON.

| Panel | Exact PromQL expression(s) | Recorded prompt / query intent |
|---|---|---|
| Application exporter | `up{job="caption_app"}` | Dashboard-wide prompt; no separate panel prompt recorded |
| Caption model ready | `caption_model_ready{job="caption_app"}` | Dashboard-wide prompt; no separate panel prompt recorded |
| Ubuntu node exporter | `up{job="node"}` | Dashboard-wide prompt; no separate panel prompt recorded |
| Active bulk jobs | `caption_active_jobs{mode="bulk"}` | Dashboard-wide prompt; no separate panel prompt recorded |
| Successful images • per mode | `sum(rate(caption_images_total{status="success",mode="single"}[1m]))`<br>`sum(rate(caption_images_total{status="success",mode="bulk"}[1m]))` | Panel note: sum the rate of successful image counters separately for Single and Bulk; preserve mode comparison |
| Accepted jobs in progress | `caption_active_jobs{mode="single"}`<br>`caption_active_jobs{mode="bulk"}` | Dashboard-wide prompt; no separate panel prompt recorded |
| Model inference • mean and p95 | `sum(rate(caption_inference_seconds_sum[2m])) / sum(rate(caption_inference_seconds_count[2m]))`<br>`histogram_quantile(0.95, sum by (le) (rate(caption_inference_seconds_bucket[2m])))` | Panel note: weighted mean = sum(rate(duration_sum))/sum(rate(duration_count)); approximate p95 = histogram_quantile over summed buckets |
| Per-image latency • decode + queue + inference | `sum(rate(caption_image_duration_seconds_sum{mode="single"}[2m])) / sum(rate(caption_image_duration_seconds_count{mode="single"}[2m]))`<br>`sum(rate(caption_image_duration_seconds_sum{mode="bulk"}[2m])) / sum(rate(caption_image_duration_seconds_count{mode="bulk"}[2m]))` | Panel note: calculate weighted per-mode mean image latency from histogram sums and counts |
| Whole-job duration • Summary | `sum(rate(caption_job_duration_seconds_sum{mode="single"}[5m])) / sum(rate(caption_job_duration_seconds_count{mode="single"}[5m]))`<br>`sum(rate(caption_job_duration_seconds_sum{mode="bulk"}[5m])) / sum(rate(caption_job_duration_seconds_count{mode="bulk"}[5m]))` | Panel note: mean full-job duration = Summary sum rate divided by Summary observation count rate, per mode |
| Images attempted since backend start | `sum(caption_images_total{mode="single",status="success"})`<br>`sum(caption_images_total{mode="single",status="error"})`<br>`sum(caption_images_total{mode="bulk",status="success"})`<br>`sum(caption_images_total{mode="bulk",status="error"})` | Panel note: sum image counters by mode and success/error outcome |
| Ubuntu VM CPU • correlate with bulk | `100 * (1 - avg(rate(node_cpu_seconds_total{job="node",mode="idle"}[1m])))`<br>`caption_active_jobs{mode="bulk"}` | Panel note: VM CPU percent = 100*(1-mean(rate(idle CPU seconds[1m]))) over VM cores |
| Ubuntu VM memory • correlate with bulk | `100 * (1 - node_memory_MemAvailable_bytes{job="node"} / node_memory_MemTotal_bytes{job="node"})`<br>`caption_active_jobs{mode="bulk"}` | Panel note: used-memory percent = 100*(1-MemAvailable/MemTotal) |
| Ubuntu root filesystem • used space | `100 * (1 - node_filesystem_avail_bytes{job="node",mountpoint="/",fstype!~"tmpfs\|overlay"} / node_filesystem_size_bytes{job="node",mountpoint="/",fstype!~"tmpfs\|overlay"})` | Panel note: root filesystem used percent = 100*(1-avail/size), select mountpoint=/ and exclude tmpfs/overlay |
| Inference-process RAM and model weights | `caption_process_memory_bytes`<br>`caption_model_weight_bytes` | Dashboard-wide prompt; no separate panel prompt recorded |
| Jobs completed by outcome | `sum(caption_jobs_total{status="success"})`<br>`sum(caption_jobs_total{status="partial"})`<br>`sum(caption_jobs_total{status="error"})` | Panel note: sum completed job counters for success/partial/error separately |
| Client sessions • image activity | `sum by (client) (caption_images_total{status="success"})` | Panel note: show successful image counts by the first 12 safe characters of the actual browser session ID |
| Inference-process CPU | `caption_process_cpu_percent` | Dashboard-wide prompt; no separate panel prompt recorded |
| Rejected uploads | `caption_rejected_uploads_total` | Dashboard-wide prompt; no separate panel prompt recorded |
| Uploaded input bytes • rate | `sum(rate(caption_upload_bytes_total{mode="single"}[1m]))`<br>`sum(rate(caption_upload_bytes_total{mode="bulk"}[1m]))` | Panel note: show rate of accepted uploaded-byte counters separately by mode |
| Prometheus firing alerts | `sum(ALERTS{alertstate="firing"}) or vector(0)` | Dashboard-wide prompt; no separate panel prompt recorded |
| Encoded image size • Summary mean | `sum(rate(caption_image_upload_bytes_sum{mode="single"}[5m])) / sum(rate(caption_image_upload_bytes_count{mode="single"}[5m]))`<br>`sum(rate(caption_image_upload_bytes_sum{mode="bulk"}[5m])) / sum(rate(caption_image_upload_bytes_count{mode="bulk"}[5m]))` | Panel note: weighted mean bytes per attempted image = sum(rate(caption_image_upload_bytes_sum[5m])) / sum(rate(caption_image_upload_bytes_count[5m])), separately by mode |
| Generated caption length • Summary mean | `sum(rate(caption_length_characters_sum{mode="single"}[5m])) / sum(rate(caption_length_characters_count{mode="single"}[5m]))`<br>`sum(rate(caption_length_characters_sum{mode="bulk"}[5m])) / sum(rate(caption_length_characters_count{mode="bulk"}[5m]))` | Panel note: weighted mean Unicode characters per successful caption = sum(rate(caption_length_characters_sum[5m])) / sum(rate(caption_length_characters_count[5m])), separately by mode |

## Checking the logic by hand

The project README gives manual arithmetic from a captured 22-image bulk job: `67.342 / 22 ≈ 3.06` seconds of inference per successful image, and `22 / 68.119 ≈ 0.32` successful images per second over the whole job. These are recorded-run averages; `rate()` uses a selected scrape window. For VM CPU, `100 × (1 − mean idle fraction)` converts node-exporter idle-time rates to percent. For VM RAM, `100 × (1 − MemAvailable / MemTotal)` gives used percent. The p95 from `histogram_quantile()` is estimated from cumulative histogram buckets.

These calculations and the full query list should be compared with the final exported `grafana/dashboard.json` and `evidence/logs/actual_app_metrics.txt` before submission. If a panel is edited or added in Grafana, update this index and the source attribution.
