"""Read-only inventory metrics. Never probes or mutates application services."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def metrics(path):
    services = json.loads(Path(path).read_text())['services']
    lines = ['# TYPE diddi_observe_service_info gauge',
             '# TYPE diddi_observe_collection_enabled gauge']
    for item in services:
        labels = {'service_name': item['name'], 'environment': item['environment'],
                  'deployment_id': item['deployment_id'], 'component': item['component']}
        serialized = ','.join(f'{k}={json.dumps(v)}' for k, v in labels.items())
        lines.append(f'diddi_observe_service_info{{{serialized},state={json.dumps(item["state"])}}} 1')
        for signal in ('metrics', 'otlp', 'logs', 'health'):
            enabled = bool(item.get(signal, {}).get('enabled', False))
            lines.append(f'diddi_observe_collection_enabled{{{serialized},signal="{signal}"}} {int(enabled)}')
    return '\n'.join(lines) + '\n'


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/alerts':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        if length > 1048576:
            self.send_error(413)
            return
        self.rfile.read(length)
        # Deliberately local-only; never forwards to email/chat/webhooks.
        print(json.dumps({'event':'observe.alert.received','bytes':length}), flush=True)
        self.send_response(202)
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            data = b'{"status":"ok"}'
        elif self.path == '/metrics':
            data = metrics(os.getenv('REGISTRY_PATH', '/registry/services.json')).encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 9108), Handler).serve_forever()
