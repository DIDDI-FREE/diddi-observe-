"""Synthetic-only probe: explicit exercises generate a metric and a correlated file log."""
import datetime
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOCK = threading.Lock()
COUNT = 0


class Handler(BaseHTTPRequestHandler):
    def respond(self, data, kind='application/json'):
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.end_headers()
        self.wfile.write(data.encode())

    def do_POST(self):
        global COUNT
        if self.path != '/exercise':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError()
            trace = json.loads(self.rfile.read(length))['trace_id']
            if not isinstance(trace, str) or not re.fullmatch('[0-9a-f]{32}', trace):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            self.send_error(400)
            return
        entry = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'level': 'info', 'event': 'synthetic.file', 'trace_id': trace,
                 'message': 'Synthetic observability validation; no business traffic',
                 'token': 'NEVER_STORE_THIS'}
        with LOCK:
            path = Path('/var/log/inputs/synthetic/pilot.log')
            if path.exists() and path.stat().st_size > 1048576:
                path.replace(path.with_suffix('.previous'))
            with path.open('a') as out:
                out.write(json.dumps(entry) + '\n')
            COUNT += 1
        self.respond(json.dumps({'trace_id': trace, 'synthetic': True}))

    def do_GET(self):
        if self.path == '/ready':
            self.respond('{"status":"ready"}')
        elif self.path == '/metrics':
            token = Path('/secrets/synthetic.metrics').read_text().strip()
            if self.headers.get('Authorization') != 'Bearer ' + token:
                self.send_error(403)
                return
            with LOCK:
                count = COUNT
            self.respond(
                '# TYPE diddi_http_server_requests_total counter\n'
                f'diddi_http_server_requests_total{{method="POST",route="/exercise",status_code="200"}} {count}\n'
                '# TYPE diddi_http_server_request_duration_seconds histogram\n'
                f'diddi_http_server_request_duration_seconds_bucket{{method="POST",route="/exercise",le="0.1"}} {count}\n'
                f'diddi_http_server_request_duration_seconds_bucket{{method="POST",route="/exercise",le="+Inf"}} {count}\n'
                f'diddi_http_server_request_duration_seconds_sum{{method="POST",route="/exercise"}} {count * 0.01}\n'
                f'diddi_http_server_request_duration_seconds_count{{method="POST",route="/exercise"}} {count}\n'
                f'diddi_worker_heartbeat_timestamp_seconds{{worker_type="synthetic"}} {time.time()}\n',
                'text/plain; version=0.0.4')
        else:
            self.send_error(404)

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
