"""Generate build-based Portainer Compose; configs are packaged in images."""
import sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]

def render():
    config = yaml.safe_load((ROOT / 'compose.yaml').read_text())
    services = config['services']
    for name, service in services.items():
        service.pop('image', None)
        service['build'] = {'context': '.', 'dockerfile': 'Dockerfile', 'target': name}
        service['pull_policy'] = 'build'
        service['volumes'] = [v for v in service.get('volumes', []) if not v.startswith('./')]
    grafana = services['grafana']
    grafana['environment'].pop('GF_SECURITY_ADMIN_PASSWORD__FILE')
    grafana['environment']['GF_SECURITY_ADMIN_PASSWORD'] = '${GRAFANA_ADMIN_PASSWORD:?Set Grafana initial admin password}'
    grafana['environment']['GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH'] = '/opt/diddi/dashboards/platform.json'
    services['alloy']['volumes'].append('log-inputs:/var/log/inputs:ro')
    services['gateway']['volumes'] += ['gateway-secret:/etc/nginx/tls:ro', 'gateway-secret:/etc/nginx/auth:ro']
    services['prometheus']['volumes'].append('metrics-secret:/run/secrets:ro')
    init = services['init-storage']
    init['command'] = ['python', '/app/runtime_init.py']
    init['cap_add'] = ['CHOWN', 'FOWNER', 'DAC_OVERRIDE']
    init['volumes'] += ['gateway-secret:/gateway-secret', 'metrics-secret:/metrics-secret']
    init['environment'] = {
        'OBSERVE_TLS_HOST': '${OBSERVE_TLS_HOST:-localhost}',
        'TLS_CERT_PEM': '${TLS_CERT_PEM:-}', 'TLS_KEY_PEM': '${TLS_KEY_PEM:-}',
        'OTLP_PASSWORDS_JSON': '${OTLP_PASSWORDS_JSON:-{}}',
        'METRICS_TOKENS_JSON': '${METRICS_TOKENS_JSON:-{}}',
    }
    init['tmpfs'] = ['/tmp']
    for name in ('gateway', 'prometheus'):
        deps = services[name].get('depends_on', {})
        if isinstance(deps, list):
            deps = {n: {'condition': 'service_started'} for n in deps}
        deps['init-storage'] = {'condition': 'service_completed_successfully'}
        services[name]['depends_on'] = deps
    config['volumes'].update({key: {} for key in ('gateway-secret','metrics-secret','log-inputs')})
    return yaml.safe_dump(config, sort_keys=False)

if __name__ == '__main__':
    path = ROOT / 'compose.portainer.yaml'
    content = render()
    if '--check' in sys.argv:
        assert path.read_text() == content, 'Stale compose.portainer.yaml'
    else:
        path.write_text(content, encoding='utf-8', newline='\n')
