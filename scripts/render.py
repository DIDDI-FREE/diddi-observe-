"""Deterministic configs from a reviewed registry; does not contact services."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {'grafana': 'grafana/grafana:13.3.1', 'prometheus': 'prom/prometheus:v3.16.0',
            'loki': 'grafana/loki:3.7.10', 'tempo': 'grafana/tempo:3.1.1',
            'alloy': 'grafana/alloy:v1.21.3', 'gateway': 'nginx:1.31.8-alpine',
            'blackbox': 'prom/blackbox-exporter:v0.29.1'}


def validate(data):
    ids = set()
    for s in data['services']:
        for k in ('id', 'name', 'deployment_id', 'component'):
            if not re.fullmatch(r'[a-z][a-z0-9-]{0,62}', s[k]):
                raise ValueError(f'Invalid {k}: {s[k]}')
        if s['id'] in ids:
            raise ValueError('Duplicate registry id')
        ids.add(s['id'])
        if s['state'] not in ('inventoried', 'connected', 'conformant-v1'):
            raise ValueError('Invalid state')
        if s['environment'] not in ('development', 'test', 'staging', 'production', 'unknown'):
            raise ValueError('Invalid environment')
        if s['state'] != 'inventoried' and not s.get('evidence'):
            raise ValueError('Connection/conformance requires evidence')
        for signal in ('metrics', 'health'):
            cfg = s.get(signal, {})
            if not cfg.get('enabled'):
                continue
            u = urlparse(cfg['url'])
            if u.scheme not in ('https', 'http') or not u.hostname or u.username or u.password or u.query or u.fragment:
                raise ValueError('Invalid collection URL')
            if u.scheme == 'http' and not cfg.get('isolated_network'):
                raise ValueError('HTTP requires an explicitly isolated network')
            if signal == 'metrics' and cfg.get('auth') != 'bearer':
                raise ValueError('Metrics require bearer auth')
        if any(s.get(k, {}).get('enabled') for k in ('metrics', 'health', 'otlp', 'logs')):
            if s['environment'] == 'unknown' or not s.get('owner'):
                raise ValueError('Enabled service needs owner and environment')


def labels(s):
    return dict(service_name=s['name'], environment=s['environment'],
                deployment_id=s['deployment_id'], component=s['component'])


def prometheus(data):
    jobs = []
    for name, target, path in [('prometheus', 'prometheus:9090', '/metrics'),
                               ('alloy', 'alloy:12345', '/metrics'),
                               ('loki', 'loki:3100', '/metrics'),
                               ('tempo', 'tempo:3200', '/metrics'),
                               ('registry', 'registry:9108', '/metrics'),
                               ('blackbox', 'blackbox:9115', '/metrics')]:
        jobs.append({'job_name': 'observe-' + name, 'metrics_path': path,
                     'static_configs': [{'targets': [target], 'labels': {'service_name': 'diddi-observe', 'component': name, 'environment': 'staging', 'deployment_id': 'observe-local'}}]})
    for s in data['services']:
        m = s.get('metrics', {})
        if m.get('enabled'):
            u = urlparse(m['url'])
            jobs.append({'job_name': 'service-' + s['id'], 'scheme': u.scheme,
                         'metrics_path': u.path or '/metrics', 'sample_limit': 20000,
                         'authorization': {'credentials_file': '/run/secrets/' + s['id'] + '.metrics'},
                         'static_configs': [{'targets': [u.netloc], 'labels': labels(s)}]})
        h = s.get('health', {})
        if h.get('enabled'):
            jobs.append({'job_name': 'health-' + s['id'], 'scrape_interval': '30s',
                         'metrics_path': '/probe', 'params': {'module': ['http_ready']},
                         'static_configs': [{'targets': [h['url']], 'labels': labels(s)}],
                         'relabel_configs': [
                             {'source_labels': ['__address__'], 'target_label': '__param_target'},
                             {'source_labels': ['__param_target'], 'target_label': 'instance'},
                             {'target_label': '__address__', 'replacement': 'blackbox:9115'}]})
    return {'global': {'scrape_interval': '15s', 'scrape_timeout': '5s', 'evaluation_interval': '15s'},
            'scrape_configs': jobs}


def alloy(data):
    parts = ['logging {\n  level = "info"\n  format = "json"\n}', '''
otelcol.processor.memory_limiter "bounded" {
  check_interval = "1s"
  limit = "384MiB"
  spike_limit = "96MiB"
  output {
    traces = [otelcol.processor.batch.central.input]
    logs = [otelcol.processor.batch.central.input]
  }
}
otelcol.processor.batch "central" {
  timeout = "5s"
  send_batch_size = 512
  send_batch_max_size = 1024
  output {
    traces = [otelcol.exporter.otlp.tempo.input]
    logs = [otelcol.exporter.otlphttp.loki.input]
  }
}
otelcol.storage.file "queue" { directory = "/var/lib/alloy/queue" }
otelcol.exporter.otlp "tempo" {
  client {
    endpoint = "tempo:4317"
    tls { insecure = true }
  }
  sending_queue {
    enabled = true
    queue_size = 1024
    storage = otelcol.storage.file.queue.handler
  }
  retry_on_failure { max_elapsed_time = "300s" }
}
otelcol.exporter.otlphttp "loki" {
  client { endpoint = "http://loki:3100/otlp" }
  sending_queue {
    enabled = true
    queue_size = 1024
    storage = otelcol.storage.file.queue.handler
  }
  retry_on_failure { max_elapsed_time = "300s" }
}
loki.write "central" {
  endpoint { url = "http://loki:3100/loki/api/v1/push" }
}
''']
    for i, s in enumerate(data['services']):
        ident = s['id'].replace('-', '_')
        if s.get('otlp', {}).get('enabled'):
            attrs = {'service.namespace': 'diddi', 'service.name': s['name'],
                     'deployment.environment.name': s['environment'],
                     'diddi.deployment.id': s['deployment_id'], 'diddi.component': s['component']}
            statements = [f'set(attributes["{k}"], "{v}")' for k,v in attrs.items()]
            resources = ',\n      '.join(json.dumps(x) for x in statements)
            parts.append(f'''
otelcol.receiver.otlp "{ident}" {{
  http {{ endpoint = "0.0.0.0:{4400+i}" }}
  output {{
    traces = [otelcol.processor.transform.{ident}.input]
    logs = [otelcol.processor.transform.{ident}.input]
  }}
}}
otelcol.processor.transform "{ident}" {{
  error_mode = "propagate"
  trace_statements {{
    context = "resource"
    statements = [{resources}]
  }}
  log_statements {{
    context = "resource"
    statements = [{resources}]
  }}
  trace_statements {{
    context = "span"
    statements = [
      "delete_matching_keys(attributes, \\"(?i).*?(authorization|password|secret|token|cookie|email|phone|url.full|db.statement).*\\")",
    ]
  }}
  log_statements {{
    context = "log"
    statements = [
      "delete_matching_keys(attributes, \\"(?i).*?(authorization|password|secret|token|cookie|email|phone).*\\")",
    ]
  }}
  output {{
    traces = [otelcol.processor.memory_limiter.bounded.input]
    logs = [otelcol.processor.memory_limiter.bounded.input]
  }}
}}
'''.replace('\\"','\\"'))
        if s.get('logs', {}).get('enabled'):
            trusted = json.dumps(labels(s)).replace(': ', ' = ')
            parts.append(f'''
local.file_match "{ident}" {{
  path_targets = [{{__path__ = "/var/log/inputs/{s['id']}/*.log"}}]
}}
loki.source.file "{ident}" {{
  targets = local.file_match.{ident}.targets
  forward_to = [loki.process.{ident}.receiver]
}}
loki.process "{ident}" {{
  stage.json {{
    expressions = {{ timestamp = "timestamp || ts || at", level = "level", trace_id = "trace_id" }}
    drop_malformed = true
  }}
  stage.timestamp {{
    source = "timestamp"
    format = "RFC3339Nano"
    action_on_failure = "skip"
  }}
  stage.replace {{
    expression = `(?i)"(?:password|secret|token|authorization|cookie|otp|pin)"\\s*:\\s*"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)"`
    replace = "[REDACTED]"
  }}
  stage.static_labels {{ values = {trusted} }}
  stage.label_drop {{ values = ["filename"] }}
  forward_to = [loki.write.central.receiver]
}}
''')
    return '\n'.join(parts)


def nginx(data):
    locations = []
    for i,s in enumerate(data['services']):
        if s.get('otlp', {}).get('enabled'):
            for signal in ('traces', 'logs'):
                locations.append(f'''
    location = /otlp/{s['id']}/v1/{signal} {{
      limit_except POST {{ deny all; }}
      auth_basic "DiddiObserve ingestion";
      auth_basic_user_file /etc/nginx/auth/{s['id']}.htpasswd;
      limit_req zone=ingestion burst=40 nodelay;
      proxy_pass http://alloy:{4400+i}/v1/{signal};
      proxy_set_header Authorization "";
    }}''')
    return '''events { worker_connections 512; }
http {
  server_tokens off;
  access_log off;
  limit_req_zone $binary_remote_addr zone=ingestion:10m rate=20r/s;
  client_max_body_size 4m;
  proxy_connect_timeout 5s;
  proxy_read_timeout 10s;
  server {
    listen 8443 ssl;
    ssl_certificate /etc/nginx/tls/tls.crt;
    ssl_certificate_key /etc/nginx/tls/tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    add_header X-Content-Type-Options nosniff always;
    location = /gateway-health { return 200 'ok'; }
''' + '\n'.join(locations) + '''
    location /otlp/ { return 404; }
    location / {
      proxy_pass http://grafana:3000;
      proxy_set_header Host $http_host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
    }
  }
}
'''


def compose(data):
    services = {}
    mounts = {
        'grafana': ['./config/grafana:/etc/grafana/provisioning:ro', './dashboards:/var/lib/grafana/dashboards:ro', 'grafana-data:/var/lib/grafana', './secrets/grafana_admin:/run/secrets/grafana_admin:ro'],
        'prometheus': ['./generated/prometheus.yaml:/etc/prometheus/prometheus.yml:ro', 'prometheus-data:/prometheus'],
        'loki': ['./config/loki.yaml:/etc/loki/config.yaml:ro', 'loki-data:/loki'],
        'tempo': ['./config/tempo.yaml:/etc/tempo/config.yaml:ro', 'tempo-data:/var/tempo'],
        'alloy': ['./generated/config.alloy:/etc/alloy/config.alloy:ro', 'alloy-data:/var/lib/alloy', './runtime/inputs:/var/log/inputs:ro'],
        'gateway': ['./generated/nginx.conf:/etc/nginx/nginx.conf:ro', './secrets/tls.crt:/etc/nginx/tls/tls.crt:ro', './secrets/tls.key:/etc/nginx/tls/tls.key:ro'],
        'blackbox': ['./config/blackbox.yaml:/etc/blackbox/config.yaml:ro']}
    for s in data['services']:
        if s.get('metrics', {}).get('enabled'):
            mounts['prometheus'].append(f'./secrets/{s["id"]}.metrics:/run/secrets/{s["id"]}.metrics:ro')
        if s.get('otlp', {}).get('enabled'):
            mounts['gateway'].append(f'./secrets/{s["id"]}.htpasswd:/etc/nginx/auth/{s["id"]}.htpasswd:ro')
    commands = {
        'prometheus': ['--config.file=/etc/prometheus/prometheus.yml','--storage.tsdb.path=/prometheus','--storage.tsdb.retention.time=30d','--storage.tsdb.retention.size=10GB'],
        'loki': ['-config.file=/etc/loki/config.yaml'],
        'tempo': ['-config.file=/etc/tempo/config.yaml', '-backend-scheduler.provider.work.compaction.block-retention=168h', '-backend-worker.compaction.block-retention=168h'],
        'alloy': ['run','--stability.level=public-preview','--server.http.listen-addr=0.0.0.0:12345','--storage.path=/var/lib/alloy','/etc/alloy/config.alloy'],
        'blackbox': ['--config.file=/etc/blackbox/config.yaml']}
    for name,image in VERSIONS.items():
        services[name] = {'image': image, 'restart': 'unless-stopped', 'networks': ['backend'],
                          'volumes': mounts[name], 'logging': {'driver': 'json-file', 'options': {'max-size':'10m','max-file':'5'}},
                          'security_opt': ['no-new-privileges:true'], 'mem_limit': '1g' if name in ('grafana','prometheus','tempo') else '512m'}
        if name in commands:
            services[name]['command'] = commands[name]
    services['grafana']['environment'] = {
        'GF_SECURITY_ADMIN_PASSWORD__FILE': '/run/secrets/grafana_admin',
        'GF_AUTH_ANONYMOUS_ENABLED': 'false', 'GF_USERS_ALLOW_SIGN_UP': 'false',
        'GF_SECURITY_COOKIE_SECURE': 'true', 'GF_SERVER_ROOT_URL': '${GRAFANA_ROOT_URL:-https://localhost:19443/}',
        'GF_ANALYTICS_REPORTING_ENABLED': 'false', 'GF_ANALYTICS_CHECK_FOR_UPDATES':'false',
        'GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH':'/var/lib/grafana/dashboards/platform.json'}
    services['gateway']['ports'] = ['${OBSERVE_BIND:-127.0.0.1}:${OBSERVE_PORT:-19443}:8443']
    services['gateway']['networks'] = ['frontend', 'backend']
    services['gateway']['depends_on'] = ['grafana','alloy']
    services['alloy']['depends_on'] = ['loki','tempo']
    services['registry'] = {'build': {'context': '.', 'dockerfile':'app/Dockerfile'},
                            'restart':'unless-stopped','networks':['backend'],
                            'volumes':['./registry/services.json:/registry/services.json:ro'],
                            'read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
                            'mem_limit':'128m','logging':{'driver':'json-file','options':{'max-size':'10m','max-file':'5'}}}
    services['init-storage'] = {
        'build': {'context': '.', 'dockerfile': 'app/Dockerfile'},
        'user': '0:0', 'network_mode': 'none', 'restart': 'no',
        'command': ['python', '-c', 'import os; [os.chown(p,10001,10001) for p in ("/volumes/tempo","/volumes/loki")]'],
        'volumes': ['tempo-data:/volumes/tempo', 'loki-data:/volumes/loki'],
        'read_only': True, 'cap_drop': ['ALL'], 'cap_add': ['CHOWN'],
        'security_opt': ['no-new-privileges:true'], 'mem_limit': '64m'}
    for name in ('tempo', 'loki'):
        services[name]['depends_on'] = {'init-storage': {'condition': 'service_completed_successfully'}}
    return {'name':'${COMPOSE_PROJECT_NAME:-diddi-observe}', 'services':services,
            'networks':{'backend':{'internal':True},'frontend':{}},
            'volumes':{n+'-data':{} for n in ['grafana','prometheus','loki','tempo','alloy']}}


def outputs(data):
    return {'generated/prometheus.yaml': yaml.safe_dump(prometheus(data),sort_keys=False),
            'generated/config.alloy':alloy(data),'generated/nginx.conf':nginx(data),
            'compose.yaml':yaml.safe_dump(compose(data),sort_keys=False)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--demo',action='store_true')
    args=parser.parse_args()
    data=json.loads((ROOT/'registry/services.json').read_text())
    if args.demo:
        data['services'].append(json.loads((ROOT/'tests/synthetic-registration.json').read_text()))
    validate(data)
    for name,content in outputs(data).items():
        if args.demo and name.startswith('generated/'):
            name=name.replace('generated/','generated/demo/')
        if args.demo and name=='compose.yaml':
            continue
        path=ROOT/name
        if args.check:
            if not path.exists() or path.read_text()!=content:
                raise SystemExit(f'Stale generated file: {name}')
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8',newline='\n')
    if args.demo:
        (ROOT/'generated/demo/services.json').write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':
    main()
