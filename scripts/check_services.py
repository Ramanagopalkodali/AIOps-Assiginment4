"""Read-only live checks. Save real exporter output and actual service health."""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

root = Path(__file__).resolve().parents[1]
evidence = root / 'evidence' / 'logs'
evidence.mkdir(parents=True, exist_ok=True)
checks = {}
for name, url in {
    'caption_api': 'http://127.0.0.1:8000/healthz',
    'caption_metrics': 'http://127.0.0.1:8001/metrics',
    'streamlit': 'http://127.0.0.1:8501/_stcore/health',
    'node_exporter': 'http://127.0.0.1:9100/metrics',
    'prometheus': 'http://127.0.0.1:9090/-/ready',
    'grafana': 'http://127.0.0.1:3000/api/health',
    'alertmanager': 'http://127.0.0.1:9093/-/ready',
    'local_receiver': 'http://127.0.0.1:9001/',
}.items():
    try:
        response = requests.get(url, timeout=5)
        checks[name] = {'ok': response.ok, 'http_status': response.status_code}
        if name == 'caption_metrics' and response.ok:
            (evidence / 'actual_app_metrics.txt').write_text(response.text)
    except requests.RequestException as exc:
        checks[name] = {'ok': False, 'error': str(exc)}
try:
    response = requests.get('http://127.0.0.1:9090/api/v1/targets', timeout=5)
    response.raise_for_status()
    targets = response.json()
    (evidence / 'actual_prometheus_targets.json').write_text(json.dumps(targets, indent=2))
    for target in targets['data']['activeTargets']:
        checks['scrape_' + target['labels']['job']] = {'ok': target['health'] == 'up', 'health': target['health']}
except (requests.RequestException, ValueError, KeyError) as exc:
    checks['scrape_targets'] = {'ok': False, 'error': str(exc)}
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'checks': checks}
(evidence / 'actual_service_checks.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(c['ok'] for c in checks.values()) else 1)
