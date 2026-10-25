# Metrics, PromQL and viva reference

## Know what each type represents

| Type | Metric | Meaning / labels |
|---|---|---|
| Counter | caption_images_total | Attempted images; mode, status, short session ID |
| Counter | caption_jobs_total | Finished accepted jobs; mode, success/partial/error, client |
| Counter | caption_upload_bytes_total | Accepted compressed/upload bytes, per mode and short session ID |
| Counter | caption_rejected_uploads_total | Rejected oversized/malformed requests |
| Gauge | caption_active_jobs | Current accepted jobs, including lock wait, per mode |
| Gauge | caption_model_ready | Loaded model availability: 0/1 |
| Gauge | caption_model_weight_bytes | Parameter/buffer memory; not all process RAM |
| Gauge | caption_process_memory_bytes | Actual backend RSS |
| Gauge | caption_process_cpu_percent | Process CPU: 100% means one full core |
| Gauge | caption_last_bulk_images | Last accepted ZIP image count |
| Histogram | caption_inference_seconds | Model.generate wall time; excludes queue/decode |
| Histogram | caption_image_duration_seconds | Per-image decode + queue + inference time |
| Summary | caption_job_duration_seconds | Entire accepted Single/Bulk job duration; mode and client |
| Summary | caption_image_upload_bytes | Encoded bytes per attempted image, including corrupt entries; mode and client |
| Summary | caption_length_characters | Unicode characters per successful caption, including spaces; mode and client |

Histograms export `_bucket`, `_sum`, `_count`. Python Summary exports `_sum`
and `_count`. The PDF's Summary wording says `_total`; that is not the standard
Python Summary suffix. This implementation uses a real Summary plus real Counter
metrics with `_total`; it does not rename Summary observations or invent a type.
Python Summary does not compute quantiles; p95 comes from a Histogram estimate.

## Manually work through the queries

1. Throughput: `sum(rate(caption_images_total{status="success"}[1m]))`.
   If successful image count increases by 12 across 60 seconds, the simple average
   is 12/60 = 0.2 images/second. Prometheus rate also handles resets/extrapolation.
2. Mean inference time: sum(rate(duration_sum)) / sum(rate(duration_count)).
   If the sum grows by 40 seconds and count grows by 10, mean is 4 seconds/image.
   Sum across series before division for a weighted average.
3. p95: `histogram_quantile(0.95, sum by (le) (rate(caption_inference_seconds_bucket[2m])))`.
   Buckets are cumulative; le is the inclusive upper boundary. Prometheus finds
   the bucket containing rank 0.95*N and interpolates, so this is approximate.
   For 100 observations and counts <=5s:90, <=10s:98, the interpolation is
   5 + (95-90)/(98-90)*(10-5) = 8.125s. This is an explanatory example, not a result.
4. VM CPU: 100*(1-mean(rate(idle CPU seconds[1m]))). If the average idle fraction
   is 0.65, VM CPU is 35%. The mean normalizes over VM CPU cores.
5. VM RAM: 100*(1-MemAvailable/MemTotal). For total 8 GiB and available 3 GiB,
   usage is 62.5%. MemAvailable differs from MemFree.
6. Root disk: 100*(1-avail/size). The mountpoint filter selects the VM root disk;
   filesystem selection excludes tmpfs/overlay. This does not measure Mac storage.
7. Job Summary mean: rate(job_duration_sum)/rate(job_duration_count). Bulk records
   one full job observation, not one Summary event per image. A 10-image ZIP is
   one job and 10 image attempts.
8. `up` reports a successful Prometheus scrape. `caption_model_ready` reports
   a loaded model. Keep both: exporter UP can coexist with model-not-ready.

## Labels and privacy/cardinality

Each Streamlit browser session gets a random session ID. The backend retains the
first 12 safe characters of that actual ID as the `client` label, rather than
hashing sessions into 64 buckets. Non-alphanumeric characters other than `_` and
`-` are removed; empty results become `anonymous`. Short prefixes can still
collide, so do not treat them as unique people. The API returns `client_session`.

The label is present on image/job/byte counters and all three Summaries.
Histograms and active-job gauges remain mode-only to avoid multiplying bucket
series per session. This is for a small local coursework demo: use a few browser
sessions, not an unbounded public deployment. New session labels create new time
series until the exporter restarts. Image filenames and raw IPs are not labels.

For both new Summary means, sum the rates across client labels BEFORE dividing:
`sum(rate(metric_sum[5m])) / sum(rate(metric_count[5m]))`, selecting each mode.
Image-size observations use len(encoded_image_bytes), excluding ZIP container
and compression overhead; one observation is recorded for every attempted image.
Caption length uses len(caption_text), including spaces, only for successes.
These counts need not match when corrupt images occur. Length is not quality.

## Seven plotting commandments

| Requirement | Where implemented |
|---|---|
| Inclusive palette | Okabe-Ito colors; status also has explicit UP/DOWN text |
| Markers relevant across media | Points, solid/dashed lines, varied point sizes and text legends |
| Appropriate axes | Metric-specific y-axis labels, native time ticks and visible X-axis: Time labels in every row |
| Explicit scales and units | Linear y-axes, seconds, percent, bytes, counts, images/s |
| Legends for multiple variables | Bottom table legends with last and max values |
| Title/subtitle | Brief chart titles and visible Text-panel subtitles above every pair of graphs |
| Plot story | Visible row stories explain the paired graphs, semantics and bulk/resource correlation |

Inspect the actual Grafana rendering after startup. The JSON is configured for
these choices; final legibility also depends on window size and Grafana behavior.
The generated dashboard has 22 metric panels and 10 visible Text panels (32 total).
Keep each row story and its graphs together in recordings or screenshots. Query
implementation details also remain in hover descriptions for the viva. Grafana
time-series panels use native time ticks; the shared axis is explicitly named in
the visible Text panels, not via an unsupported custom x-axis setting.

## Questions to prepare

- Why sequential bulk inference? It bounds memory and shares one loaded model.
- Why separate frontend/backend processes? Streamlit reruns do not reset metrics
  or repeatedly load weights; exporter continues during long requests.
- Why Counter for images and Gauge for active jobs? Completed work accumulates;
  active work increases and decreases.
- Why Histogram for p95? Python Summary provides sum/count, not local quantiles.
- Why can process CPU exceed 100%? Its denominator is one core; VM CPU is the
  average non-idle fraction across all VM cores.
- Which resources are monitored? Ubuntu guest system plus inference-process
  resources. Streamlit's own process is not included in backend RSS; VM metrics
  include all Ubuntu processes, including Streamlit and monitoring containers.
- What does an alert's `for: 15s` mean? The condition must remain true for that
  duration before firing. Scrape/evaluation/grouping add delivery delay.
- What happens after restart? App counters reset; Prometheus history persists.
- Does the model need the internet? Only initial setup downloads it; runtime
  scripts enforce local-files-only/offline mode.
- What happens with bad images? Error rows are returned and counted; valid ZIP
  members continue, and active job gauges are decremented in finally blocks.
- Can this prove caption accuracy? No. Captions must be inspected; this assignment
  emphasizes instrumentation and observability rather than measured caption quality.

## Source references

- Assignment 4.pdf supplied by the student: authoritative task requirements.
- https://huggingface.co/Salesforce/blip-image-captioning-base — CPU BLIP usage/model card.
- https://prometheus.github.io/client_python/instrumenting/summary/ — Summary semantics.
- https://docs.docker.com/engine/install/ubuntu/ — Ubuntu/architecture support.

All numeric examples above are arithmetic teaching examples, not measured VM data.
