"""Synthetic HTTP fixture only. No dependencies on live DIDDI services."""
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            token = Path('/secrets/synthetic.metrics').read_text().strip()
            if self.headers.get('Authorization') != 'Bearer ' + token:
                self.send_error(403)
                return
            data = ('# TYPE diddi_http_server_requests_total counter\n'
                    'diddi_http_server_requests_total{method="GET",route="/demo",status_code="200"} 42\n'
                    '# TYPE diddi_http_server_request_duration_seconds histogram\n'
                    'diddi_http_server_request_duration_seconds_bucket{method="GET",route="/demo",le="0.1"} 40\n'
                    'diddi_http_server_request_duration_seconds_bucket{method="GET",route="/demo",le="+Inf"} 42\n'
                    'diddi_http_server_request_duration_seconds_sum{method="GET",route="/demo"} 4.2\n'
                    'diddi_http_server_request_duration_seconds_count{method="GET",route="/demo"} 42\n'
                    f'diddi_worker_heartbeat_timestamp_seconds{{worker_type="demo"}} {time.time()}\n')
        elif self.path == '/ready':
            data = '{"status":"ready"}'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4' if self.path == '/metrics' else 'application/json')
        self.end_headers()
        self.wfile.write(data.encode())

    def log_message(self, *_):
        pass


ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
