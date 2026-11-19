"""Generate secret-free team contracts; update local env files without rotating secrets."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def settings(service):
    if service not in ('diddifree-id','diddisend','diddigo','diddipay'):
        raise ValueError('Unknown service: '+service)
    common = {
        'ENVIRONMENT':'staging', 'OTEL_SERVICE_NAME':service,
        'OTEL_EXPORTER_OTLP_PROTOCOL':'http/protobuf',
        'OTEL_EXPORTER_OTLP_HEADERS':'', 'OTEL_LOGS_ENABLED':'true',
        'OTEL_EXPORTER_OTLP_ENDPOINT':'http://169.58.70.37:19480/otlp/'+service,
        'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT':'http://169.58.70.37:19480/otlp/'+service+'/v1/logs',
        'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT':'http://169.58.70.37:19480/otlp/'+service+'/v1/traces',
    }
    if service == 'diddifree-id':
        common.update(DIDDI_DEPLOYMENT_ID=service+'-staging', METRICS_AUTH_TOKEN='',
                      OTEL_ENABLED='true', OTEL_EXPORTER_OTLP_CERTIFICATE='')
    else:
        common.update(DEPLOYMENT_ID=service+'-staging', METRICS_BEARER_TOKEN='',
                      OTEL_EXPORTER_OTLP_CA_FILE='', OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE_FILE='',
                      OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE='')
    if service == 'diddipay':
        for key in ('OTEL_EXPORTER_OTLP_ENDPOINT','OTEL_EXPORTER_OTLP_LOGS_ENDPOINT','OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'):
            common[key] = common[key].replace('http://169.58.70.37:19480', 'https://logs-otel.diddifree.com')
        # Existing metrics credentials stay in the producer; this handoff is OTLP only.
        common.pop('METRICS_BEARER_TOKEN')
    return common

def contract(service):
    result = {
        'handoff_version':'1.0.0', 'protocol_version':'2.0.0', 'protocol_reference':'DIDDI-Observability-v1.md', 'log_schema_version':'1.0.0',
        'service':service, 'environment':'staging', 'deployment_id':service+'-staging',
        'status':'logs_traces_metrics_received' if service in ('diddisend','diddigo') else 'traces_metrics_received_file_worker_received_otlp_logs_migration_required', 'owner_contact':None, 'deployed_sha':None,
        'ingress':{'base_url':'http://169.58.70.37:19480', 'proxy':'public IP gateway', 'public_ingress_verified':True,
                   'https_base_url':'https://logs-otel.diddifree.com', 'https_requires_custom_ca':False,
                   'tls':{'enabled':False,'verify':True,'trust':'system-public-ca-when-https','custom_ca_required':False,'client_certificate_required':False},
                   'traces_path':'/otlp/'+service+'/v1/traces', 'logs_path':'/otlp/'+service+'/v1/logs'},
        'metrics':{'path':'/metrics' if service in ('diddifree-id','diddigo') else '/internal/metrics',
                   'transport':'prometheus-http-scrape','auth':'bearer','scrape_enabled':True},
        'logs':{'transport':'otlp-http/protobuf',
                'migration_required':service=='diddifree-id',
                'current_transport':'file-jsonl' if service=='diddifree-id' else 'otlp-http/protobuf',
                'central_collection_verified':service in ('diddisend','diddigo'),
                'verification_scope':'target OTLP transport; ID file worker evidence does not validate OTLP logs'},
        'protocol_conformance_verified':False,
        'traces':{'central_collection_verified':True},
        'implementation_required':service=='diddifree-id',
        'verification_date':'2026-11-18',
        'secret_file_reference':'secrets/onboarding/'+service+'.env',
        'environment_variables':settings(service),
        'notes':['No secrets in this contract. Empty secret values are placeholders, not instructions to erase installed credentials.',
                 'HTTP is publicly accessible on port 19480 for this staging MVP; HTTPS is not an activation prerequisite.',
                 'No change to business logic, log schema, metric names or OTP policy.',
                 'Target configuration, not proof of deployment. ID must migrate file collection to OTLP with a coordinated cutover; preserve installed credentials.',
                 'Existing HTTP staging endpoints remain accepted; HTTPS is available. No automatic URL change.'],
    }

    if service == 'diddipay':
        result.update(status='central_configuration_prepared_not_deployed',
                      implementation_required=True, verification_date=None)
        result['ingress'].update(base_url='https://logs-otel.diddifree.com', public_ingress_verified=False)
        result['ingress']['tls']['enabled'] = True
        result['logs'].update(current_transport=None, central_collection_verified=False,
                             verification_scope='OTLP producer receipt not yet verified')
        result['traces']['central_collection_verified'] = False
        result['notes'] = [
            'Target configuration only. Central routes are not deployed or verified yet.',
            'Preserve the existing metrics endpoint and token; no business secret is reused.',
            'No custom CA, shared log volume or Docker socket is required.',
            'API and worker reception must be verified independently before claiming conformity.',
        ]
    return result

def outputs():
    return {'docs/teams/'+s+'.json':json.dumps(contract(s),indent=2,ensure_ascii=False)+'\n'
            for s in ('diddifree-id','diddisend','diddigo','diddipay')}

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
