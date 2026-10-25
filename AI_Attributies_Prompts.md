# AI Assistance — Grafana Dashboard

I asked ChatGPT to help turn my application's `caption_*` metrics and the Ubuntu `node_exporter` metrics into a useful dashboard. The following are **edited, specific versions of my requests**, not verbatim chat transcripts.

## Prompts used

1. **Metric coverage:** “Use the captioning app's Counters, Gauges, Histograms and Summary series to show application availability and model readiness, completed Single and Bulk images, throughput, inference latency, active jobs and upload errors. Distinguish success, partial and failed work where the metric labels allow it.”
2. **Host correlation:** “Put Bulk activity next to Ubuntu CPU and RAM usage from `node_exporter`, with disk utilization nearby. Make it possible to see whether processing a ZIP coincides with a resource spike, rather than showing unrelated system graphs.”
3. **Panel design:** “The dashboard has too many similar line plots. Use readable status values for health, time-series plots for rates and latency, and suitable bars, gauges or timelines for counts and availability. Arrange the panels from high-level health to workload and then host resources.”
4. **Seven plotting rules:** “Use an inclusive palette and a second visual distinction such as line style or panel type. Give charts short titles and subtitles, explanatory descriptions, named axes, explicit units and linear/log scale choices, and legends whenever more than one series appears.”
5. **Troubleshooting:** “The app and Prometheus metrics are live, but imported Grafana panels say ‘No data.’ Check whether the dashboard JSON refers to a different Prometheus datasource UID, keep the working Prometheus connection, and retain the 5-second refresh setting.”
6. **Explanation:** “Explain the PromQL for images per second, mean inference time, latency percentiles and CPU/RAM use so I can calculate and describe each result during evaluation.”

The final panel queries and presentation settings are in `grafana/dashboard.json`; the dashboard generator is `scripts/build_dashboard.py`. An imported dashboard must reference the UID of the working Grafana Prometheus datasource. Regenerating the JSON can restore an older UID, so check the datasource reference before importing it again.

## Calculations I should be able to explain

| Measure | Logic |
|---|---|
| Image throughput | `rate()` of an image Counter, usually grouped by `mode`; units are images/second. |
| Mean inference time | Rate of the duration Summary or Histogram `_sum` divided by rate of its `_count`; units are seconds/image. |
| Latency percentile | `histogram_quantile()` applied to a rate of cumulative `_bucket` series; the result is an estimate. |
| Active jobs | A Gauge showing the current number of jobs, rather than a cumulative total. |
| Host CPU/RAM/disk | `node_exporter` metrics converted to percentages or bytes with explicit units. |

Rate panels can be blank when no recent images were processed or when too few samples exist. The metric's `client` label groups requests; it should not be interpreted as a count of unique people.
