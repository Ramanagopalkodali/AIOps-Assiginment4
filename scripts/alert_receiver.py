"""Local-only Alertmanager webhook sink; saves actual alerts, never sample alerts."""
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / 'evidence' / 'logs' / 'alerts.jsonl'
LOG.parent.mkdir(parents=True, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = LOG.read_bytes()[-100000:] if LOG.exists() else b'No alerts received yet.\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 1_000_000:
            self.send_error(413)
            return
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self.send_error(400)
            return
        record = {'received_at': datetime.now(timezone.utc).isoformat(), 'payload': data}
        with LOG.open('a') as output:
            output.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')


if __name__ == '__main__':
    print('Alert receiver: http://127.0.0.1:9001 (Ctrl+C stops)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 9001), Handler).serve_forever()
