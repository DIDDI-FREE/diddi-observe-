"""Prepare only the two authorized sources, without claiming producer readiness."""
import json
from pathlib import Path
import sys
import yaml
import render
import synthetic_profile

ROOT = Path(__file__).resolve().parents[1]

def outputs():
    source = synthetic_profile.outputs()
    registry = json.loads(source['config/synthetic/services.json'])
    targets = {
        'diddifree-id': ('DiddiFreeID team', 'diddi-auth-app-1:8000', '/metrics', '/health/ready'),
        'diddisend': ('DiddiSend team', 'diddisend-backend-api-1:8000', '/internal/metrics', '/ready'),
    }
    for service in registry['services']:
        if service['id'] not in targets:
            continue
        owner, host, metrics, health = targets[service['id']]
        service.update(owner=owner, state='inventoried')
        service['otlp']['enabled'] = True
        service['health'] = dict(enabled=True, url='http://' + host + health, isolated_network=True)
        service['metrics'].update(enabled=False, url='http://' + host + metrics, isolated_network=True)
    render.validate(registry)
    # Retain the authenticated synthetic exercise route used by the smoke test.
    nginx = render.nginx(registry)
    pilot = source['config/synthetic/nginx.conf']
    location = pilot[pilot.index('    location = /synthetic-test'):pilot.index('    location /otlp/')]
    nginx = nginx.replace('    location /otlp/', location + '    location /otlp/')
    return {
        'config/onboarding/services.json': json.dumps(registry, indent=2) + '\n',
        'config/onboarding/prometheus.yaml': yaml.safe_dump(render.prometheus(registry), sort_keys=False),
        'config/onboarding/config.alloy': render.alloy(registry),
        'config/onboarding/nginx.conf': nginx,
    }

if __name__ == '__main__':
    for name, content in outputs().items():
        path = ROOT / name
        if '--check' in sys.argv:
            assert path.read_text() == content, 'Stale ' + name
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
