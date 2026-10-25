# Validation of the restructured source export

Checked in the preparation environment:

- Python sources parse, shell scripts pass bash -n, YAML and TOML parse.
- Package-relative imports are updated; src package discovery and project/model
  paths resolve to the new repository rather than a source subfolder.
- The relocated dashboard generator writes grafana/dashboard.json successfully.
- The dashboard has 32 panels (22 metrics, 10 visible stories) and 5s refresh.
- Compose bind-mount sources exist in their new locations. A fresh Grafana is
  opt-in, protecting against accidentally creating a second Grafana on port 3000.
- Six actual image/ZIP unit tests passed under the new package layout.
- The migration helper was checked with temporary fixture files: copies retained
  source data and did not overwrite destination files.

Five API tests are included but skipped in the preparation environment because
its API dependencies are unavailable. Your VM previously passed all eleven tests
on the prior layout; rerun all eleven with `bash scripts/run_tests.sh` on this
layout before trusting the refactor. A skipped API test is not a passed API test.

Not run here: BLIP download/inference, Docker pulls/startup, promtool/amtool,
actual Grafana rendering, live scrape/alert delivery or video recording. YAML
parsing is not equivalent to Prometheus or Docker runtime validation. Existing
Grafana datasource connectivity remains a separate pending VM configuration.

No runtime model outputs, screenshots or performance numbers were fabricated.
The arithmetic examples in METRICS_AND_VIVA.md are explanatory examples only.
