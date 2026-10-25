# Monitoring configuration and your existing Grafana

The refactor preserves the monitoring stack and changes configuration paths.
It does not reconfigure your running Docker containers merely by being extracted.

## Files

- monitoring/prometheus.yml: app/node/Prometheus/Alertmanager scrapes, 5s interval.
- monitoring/rules.yml: availability, readiness, node and high-CPU alerts.
- monitoring/alertmanager.yml: local webhook at 127.0.0.1:9001.
- grafana/dashboard.json: 32 panels, fixed Prometheus datasource UID `prometheus`.
- grafana/provisioning/: standalone Grafana provisioning.
- compose.yml: Prometheus and Alertmanager by default; fresh Grafana opt-in.

node_exporter runs natively in Ubuntu to monitor the VM:

```bash
sudo apt update
sudo apt install -y prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
curl -fsS http://127.0.0.1:9100/metrics
```

Use your existing Docker installation, not a second installation. Validate config:

```bash
docker compose config -q
docker compose run --rm --entrypoint /bin/promtool prometheus check config /etc/prometheus/prometheus.yml
docker compose run --rm --entrypoint /bin/amtool alertmanager check-config /etc/alertmanager/alertmanager.yml
```

`docker compose up -d` starts only Prometheus and Alertmanager. They use Linux
host networking and loopback endpoints. Backend/receiver must run separately.
Targets: http://127.0.0.1:9090/targets. Alerts: http://127.0.0.1:9090/alerts.
Alertmanager: http://127.0.0.1:9093. Receiver: http://127.0.0.1:9001.

## Important: your running Grafana uses Docker bridge networking

It already occupies port 3000 and has volume grafana-storage. Keep both. Do NOT
enable the fresh-grafana profile on this VM. `localhost:9090` configured inside
that Grafana container refers to the Grafana container, not Ubuntu. The default
Prometheus listener is Ubuntu loopback only, so pointing Grafana at a guessed
bridge gateway does not fix connectivity by itself.

Existing-Grafana connectivity/datasource provisioning still needs to be adapted
for the current VM before end-to-end dashboard verification. That configuration
was pending before this restructuring and is not claimed as tested by this ZIP.
Do not delete/recreate Grafana or its persistent volume as an automatic workaround.
After connectivity is configured, create/use the Prometheus datasource with UID
`prometheus` (or update the dashboard references to your actual datasource UID),
then import grafana/dashboard.json into existing Grafana.

## Optional standalone fresh VM path

Only on a machine without Grafana on port 3000:

```bash
docker compose --profile fresh-grafana up -d
```

The standalone Grafana shares Linux host networking with Prometheus, so its
provisioned localhost datasource works. Initial login is admin /
caption-local-demo-change-me; change the password if prompted. This is not your
existing container's password. Named volumes persist account state.

## Real alert demonstration

With monitoring, app and local receiver working: stop only the backend; allow
roughly 30–60s for scrape/evaluation/for/grouping delays; capture CaptionAppDown
firing and the receiver notification. Restart the backend and capture resolved.
Actual deliveries are saved to evidence/logs/alerts.jsonl. Counters reset on
backend restart; run a fresh workload before final recording.
