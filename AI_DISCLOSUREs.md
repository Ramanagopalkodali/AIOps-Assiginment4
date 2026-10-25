# AI usage disclosure — DA3408 Assignment 4

## Tools used

- **OpenAI ChatGPT / Codex:** Helped plan and generate the application code, instrumentation, monitoring configuration, Grafana queries and dashboard, tests, setup commands and documentation; helped reorganize the project and troubleshoot the Ubuntu VM deployment.
- **Claude (Anthropic):** Provided a review of the proposed assignment coverage and suggestions about labels, Summaries, dashboard presentation and evidence. I used that review to decide which changes were necessary; it was not the source of my measured results.

## How AI contributed

1. **Concepts and metric design.** AI explained Counter versus Gauge, Histogram versus Summary, client labels, scrape targets, `rate()`, `histogram_quantile()`, and how to compare bulk captioning activity with Ubuntu CPU and RAM.
2. **Code and configuration.** AI assisted with the Streamlit/FastAPI CPU captioning app, input handling, `prometheus_client` instrumentation, Prometheus and Alertmanager configuration, Grafana dashboard generation, and tests. The dashboard and alert-query prompts recorded in the project are indexed in [`AI_Attributio_Prompts.md`](AI_Attributio_Prompts.md). The source files retain attribution near complex generated expressions.
3. **Troubleshooting and presentation.** AI helped explain the difference between the API on port 8000, metrics on 8001, Prometheus on 9090 and the existing Grafana container on 3000; it also helped with datasource connectivity, the repository structure and the README.

## What I ran and reviewed

I ran Single and Bulk captioning on the Ubuntu VirtualBox guest and inspected the returned captions and CSV results. I also tried a ZIP containing valid and unreadable image members to observe the partial result. I collected application metrics, Prometheus target status, service checks, screenshots and logs in `evidence/` on my VM. The README's 22-image example and its arithmetic refer to my recorded run; those numbers should be checked against the saved exporter snapshot before submission.

I am responsible for explaining the implementation and the PromQL logic during evaluation. For example, the recorded bulk run reports 67.342 seconds of inference across 22 successful images, giving approximately 3.06 seconds per image; the whole job took 68.119 seconds, giving approximately 0.32 completed images per second over that job. A dashboard `rate()` is a different, windowed calculation. A Python Summary exports `_sum` and `_count`; the Counter suffix is `_total`.

The model's captions, screenshots, CSVs, service status, and performance numbers are outputs from real local runs. AI did not generate or fabricate those experimental results. This disclosure describes AI assistance rather than claiming the initial code and queries were written independently.
