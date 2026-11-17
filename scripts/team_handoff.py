"""Generate secret-free team contracts; update local env files without rotating secrets."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def settings(service):
    common = {'ENVIRONMENT':'staging', 'OTEL_EXPORTER_OTLP_HEADERS':''}
    if service == 'diddifree-id':
        common.update(DIDDI_DEPLOYMENT_ID='diddifree-id-staging', METRICS_AUTH_TOKEN='',
                      OTEL_ENABLED='true', OTEL_EXPORTER_OTLP_TRACES_ENDPOINT='http://169.58.70.37:19480/otlp/diddifree-id/v1/traces',
                      OTEL_EXPORTER_OTLP_CERTIFICATE='',
                      OBSERVABILITY_LOG_FILE='/var/log/diddifree/observability.jsonl',
                      OBSERVABILITY_LOG_VOLUME_NAME='diddifree-id-observability-logs-staging')
    else:
        common.update(DEPLOYMENT_ID='diddisend-staging', METRICS_BEARER_TOKEN='',
                      OTEL_EXPORTER_OTLP_ENDPOINT='http://169.58.70.37:19480/otlp/diddisend', OTEL_EXPORTER_OTLP_LOGS_ENDPOINT='http://169.58.70.37:19480/otlp/diddisend/v1/logs',
                      OTEL_LOGS_ENABLED='true', OTEL_EXPORTER_OTLP_CA_FILE='',
                      OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE_FILE='', OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE='')
    return common

def contract(service):
    return {
        'handoff_version':'1.0.0', 'protocol_version':'1.1.3', 'log_schema_version':'1.0.0',
        'service':service, 'environment':'staging', 'deployment_id':service+'-staging',
        'status':'public_http_mvp', 'owner_contact':None, 'deployed_sha':None,
        'ingress':{'base_url':'http://169.58.70.37:19480', 'proxy':'public IP gateway', 'public_ingress_verified':False,
                   'tls':{'enabled':False,'verify':True,'trust':'system-public-ca-when-https','custom_ca_required':False,'client_certificate_required':False},
                   'traces_path':'/otlp/'+service+'/v1/traces', 'logs_path':'/otlp/'+service+'/v1/logs'},
        'metrics':{'path':'/metrics' if service=='diddifree-id' else '/internal/metrics',
                   'transport':'private-network-scrape','auth':'bearer','scrape_enabled':False},
        'logs':{'transport':'file-jsonl' if service=='diddifree-id' else 'otlp-http',
                'volume_name':'diddifree-id-observability-logs-staging' if service=='diddifree-id' else None,
                'producer_path':'/var/log/diddifree/observability.jsonl' if service=='diddifree-id' else None,
                'collector_mount_mode':'read-only' if service=='diddifree-id' else None,
                'central_collection_verified':False},
        'secret_file_reference':'secrets/onboarding/'+service+'.env',
        'environment_variables':settings(service),
        'notes':['No secrets in this contract. Empty secret values are placeholders, not instructions to erase installed credentials.',
                 'HTTP is publicly accessible on port 19480 for this staging MVP; HTTPS is not an activation prerequisite.',
                 'No change to business logic, log schema, metric names or OTP policy.'],
    }

def outputs():
    return {'docs/teams/'+s+'.json':json.dumps(contract(s),indent=2,ensure_ascii=False)+'\n'
            for s in ('diddifree-id','diddisend')}

def update_private_env(service):
    path = ROOT/'secrets/onboarding'/ (service+'.env')
    old = dict(line.split('=',1) for line in path.read_text().splitlines() if line and not line.startswith('#') and '=' in line)
    token = 'METRICS_AUTH_TOKEN' if service=='diddifree-id' else 'METRICS_BEARER_TOKEN'
    for key in (token,'OTEL_EXPORTER_OTLP_HEADERS'):
        if not old.get(key):
            raise ValueError('Missing existing credential; no implicit generation: '+service+'/'+key)
    updated = {**old, **settings(service)}
    for key in (token,'OTEL_EXPORTER_OTLP_HEADERS'):
        updated[key]=old[key]
    path.write_text('# Public IP HTTP MVP: existing credentials preserved; no custom CA needed.\n'+
                    ''.join(k+'='+v+'\n' for k,v in updated.items()),encoding='utf-8',newline='\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--update-private-env',action='store_true')
    args=parser.parse_args()
    for name, content in outputs().items():
        path=ROOT/name
        if args.check:
            assert path.read_text(encoding='utf-8')==content, 'Stale '+name
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8',newline='\n')
    if args.update_private_env:
        for service in ('diddifree-id','diddisend'):
            update_private_env(service)
        print('Team env files updated; credential values preserved and not displayed.')
