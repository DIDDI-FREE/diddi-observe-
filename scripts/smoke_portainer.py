"""Verify the build-based deployment locally; uses only public certificate export."""
import base64
import json
import os
import ssl
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

project = os.environ.get('COMPOSE_PROJECT_NAME', 'observe-build-test')
base = os.environ.get('OBSERVE_TEST_URL', 'https://localhost:19445')
auth = 'Basic ' + base64.b64encode(('admin:' + os.environ['GRAFANA_ADMIN_PASSWORD']).encode()).decode()
with tempfile.TemporaryDirectory() as folder:
    cert = Path(folder) / 'tls.crt'
    subprocess.run(['docker', 'cp', project + '-gateway-1:/etc/nginx/tls/tls.crt', str(cert)], check=True)
    context = ssl.create_default_context(cafile=str(cert))

    def get(path):
        request = urllib.request.Request(base + path, headers={'Authorization': auth})
        with urllib.request.urlopen(request, context=context, timeout=10) as response:
            return json.load(response)

    deadline = time.monotonic() + 120
    while True:
        try:
            assert get('/api/health')['database'] == 'ok'
            assert len(get('/api/search?tag=diddi&type=dash-db')) == 6
            assert len(get('/api/v1/provisioning/alert-rules')) == 4
            result = get('/api/datasources/proxy/uid/prometheus/api/v1/query?' + urllib.parse.urlencode({'query': 'up{job=~"observe-.*"}'}))['data']['result']
            assert len(result) == 6 and all(row['value'][1] == '1' for row in result), result
            break
        except Exception:
            if time.monotonic() >= deadline:
                raise
            time.sleep(3)
print('PASS TLS, authenticated Grafana, six dashboards, four alerts and six healthy scrape targets')
