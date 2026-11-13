"""Build a reproducible, opt-in synthetic profile without activating real modules."""
import json
from pathlib import Path
import sys
import yaml
import render
import portainer

ROOT = Path(__file__).resolve().parents[1]


def outputs():
    registry = json.loads((ROOT / 'registry/services.json').read_text())
    fixture = json.loads((ROOT / 'tests/synthetic-registration.json').read_text())
    fixture.update(deployment_id='observe-pilot', owner='observability-test')
    registry['services'].append(fixture)
    render.validate(registry)
    nginx = render.nginx(registry).replace('    location /otlp/', '''    location = /synthetic-test {
      limit_except POST { deny all; }
      auth_basic "Synthetic test";
      auth_basic_user_file /etc/nginx/auth/synthetic.htpasswd;
      limit_req zone=ingestion burst=10 nodelay;
      proxy_set_header Authorization "";
      proxy_pass http://synthetic:8000/exercise;
    }
    location /otlp/''')
    config = yaml.safe_load(portainer.render())
    for name in ('prometheus', 'alloy', 'gateway', 'registry', 'init-storage'):
        config['services'][name]['build']['target'] = 'synthetic-' + name
    init = config['services']['init-storage']
    init['volumes'].append('log-inputs:/var/log/inputs')
    config['services']['synthetic'] = {
        'build': {'context': '.', 'dockerfile': 'Dockerfile', 'target': 'synthetic'},
        'pull_policy': 'build', 'restart': 'unless-stopped', 'networks': ['backend'],
        'user': '65534:65534', 'read_only': True, 'cap_drop': ['ALL'],
        'security_opt': ['no-new-privileges:true'], 'mem_limit': '64m',
        'volumes': ['metrics-secret:/secrets:ro', 'log-inputs:/var/log/inputs'],
        'depends_on': {'init-storage': {'condition': 'service_completed_successfully'}},
        'logging': {'driver': 'json-file', 'options': {'max-size': '10m', 'max-file': '2'}},
    }
    config['services']['gateway']['depends_on']['synthetic'] = {'condition': 'service_started'}
    return {
        'config/synthetic/prometheus.yaml': yaml.safe_dump(render.prometheus(registry), sort_keys=False),
        'config/synthetic/config.alloy': render.alloy(registry),
        'config/synthetic/nginx.conf': nginx,
        'config/synthetic/services.json': json.dumps(registry, indent=2) + '\n',
        'compose.portainer.synthetic.yaml': yaml.safe_dump(config, sort_keys=False),
    }


if __name__ == '__main__':
    for name, content in outputs().items():
        path = ROOT / name
        if '--check' in sys.argv:
            assert path.read_text() == content, 'Stale ' + name
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
