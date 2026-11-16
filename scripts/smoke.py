"""End-to-end local synthetic test, through TLS and authenticated Grafana proxy."""
import base64
import datetime
import json
import os
import secrets
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=os.getenv('OBSERVE_TEST_URL','https://localhost:19443')
REMOTE = bool(os.getenv('OBSERVE_AUTH_FILE'))
AUTH = json.loads(Path(os.environ['OBSERVE_AUTH_FILE']).read_text()) if REMOTE else {}
INSECURE = os.getenv('OBSERVE_INSECURE_TLS') == '1'
CTX=ssl._create_unverified_context() if INSECURE else ssl.create_default_context(cafile=os.getenv('OBSERVE_CA_FILE',str(ROOT/'secrets/tls.crt')))
ADMIN='Basic '+base64.b64encode(('admin:'+(AUTH['admin'] if REMOTE else (ROOT/'secrets/grafana_admin').read_text().strip())).encode()).decode()
INGEST='Basic '+base64.b64encode(('synthetic:'+(AUTH['synthetic'] if REMOTE else (ROOT/'secrets/synthetic.password').read_text().strip())).encode()).decode()


def request(path,data=None,auth=ADMIN):
    headers={'Content-Type':'application/json'}
    if auth:headers['Authorization']=auth
    req=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers=headers)
    with urllib.request.urlopen(req,context=CTX,timeout=10) as r:
        content=r.read()
        return json.loads(content) if content else {}


def eventually(label,fn,seconds=90):
    deadline=time.monotonic()+seconds
    last='not ready'
    while time.monotonic()<deadline:
        try:
            if fn():
                print('PASS '+label,flush=True)
                return
        except Exception as e:last=type(e).__name__+': '+str(e)[:160]
        time.sleep(2)
    raise AssertionError(label+': '+last)


def query(expr):
    return request('/api/datasources/proxy/uid/prometheus/api/v1/query?'+urllib.parse.urlencode({'query':expr}))['data']['result']


def logs(selector):
    return request('/api/datasources/proxy/uid/loki/loki/api/v1/query_range?'+urllib.parse.urlencode({'query':selector,'limit':100}))['data']['result']


def main():
    eventually('Grafana healthy',lambda:request('/api/health')['database']=='ok')
    for authorization in (None,'Basic '+base64.b64encode(b'synthetic:wrong').decode()):
        try:request('/otlp/synthetic/v1/traces',{},authorization)
        except urllib.error.HTTPError as e:assert e.code==401,e.code
        else:raise AssertionError('Unauthenticated ingestion accepted')
    print('PASS unauthorized ingestion refused',flush=True)
    trace=secrets.token_hex(16)
    span=secrets.token_hex(8)
    now=time.time_ns()
    resource={'attributes':[{'key':'service.name','value':{'stringValue':'forged-service'}},{'key':'service.version','value':{'stringValue':'smoke-v1'}}]}
    result=request('/otlp/synthetic/v1/traces',{'resourceSpans':[{'resource':resource,'scopeSpans':[{'scope':{'name':'diddi-smoke'},'spans':[{'traceId':trace,'spanId':span,'name':'synthetic.request','kind':2,'startTimeUnixNano':str(now),'endTimeUnixNano':str(now+10000000),'attributes':[{'key':'password','value':{'stringValue':'NEVER_STORE_THIS'}}]}]}]}]},INGEST)
    assert not result.get('partialSuccess'),result
    body=json.dumps({'event':'synthetic.completed','trace_id':trace,'message':'local test only'})
    result=request('/otlp/synthetic/v1/logs',{'resourceLogs':[{'resource':resource,'scopeLogs':[{'scope':{'name':'diddi-smoke'},'logRecords':[{'timeUnixNano':str(now),'observedTimeUnixNano':str(now),'severityNumber':9,'severityText':'INFO','body':{'stringValue':body},'traceId':trace,'spanId':span,'attributes':[{'key':'token','value':{'stringValue':'NEVER_STORE_THIS'}}]}]}]}]},INGEST)
    assert not result.get('partialSuccess'),result
    if REMOTE:
        request('/synthetic-test', {'trace_id': trace}, INGEST)
        eventually('exercise metric recorded', lambda:bool(query('diddi_http_server_requests_total{service_name="synthetic",route="/exercise"} >= 1')))
    else:
        folder=ROOT/'runtime/inputs/synthetic'
        folder.mkdir(parents=True,exist_ok=True)
        with (folder/'smoke.log').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'level':'info','event':'synthetic.file','trace_id':trace,'token':'NEVER_STORE_THIS'})+'\n')
    eventually('authenticated Prometheus scrape',lambda:bool(query('up{job="service-synthetic"} == 1')))
    eventually('registry preserves source identity',lambda:bool(query('diddi_observe_service_info{service_name="synthetic",environment="test"} == 1')))
    eventually('readiness probe',lambda:bool(query('probe_success{job="health-synthetic"} == 1')))
    eventually('OTLP logs in Loki',lambda:bool(logs('{service_name="synthetic",deployment_environment_name="test"} |= "'+trace+'"')))
    eventually('file logs in Loki',lambda:bool(logs('{service_name="synthetic",environment="test"} |= "'+trace+'"')))
    def check_trace():
        data=request('/api/datasources/proxy/uid/tempo/api/traces/'+trace)
        serialized=json.dumps(data)
        assert 'NEVER_STORE_THIS' not in serialized
        assert 'forged-service' not in serialized
        return 'synthetic.request' in serialized
    eventually('trace persisted; trusted identity and attribute redaction',check_trace)
    for selector in ['{service_name="synthetic",deployment_environment_name="test"}','{service_name="synthetic",environment="test"}']:
        assert 'NEVER_STORE_THIS' not in json.dumps(logs(selector+' |= "'+trace+'"'))
    dashboards=request('/api/search?tag=diddi&type=dash-db')
    assert len(dashboards)==6,len(dashboards)
    assert len(request('/api/v1/provisioning/alert-rules'))>=4
    report={'result':'passed','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dashboards':len(dashboards),'trace_id':trace,
            'scope':'synthetic only; no business service changes or external notifications',
            'target': BASE, 'tls_verified': not INSECURE}
    (ROOT/'test-results').mkdir(exist_ok=True)
    (ROOT/'test-results/smoke.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS 6 dashboards, alert provisioning and correlated signals; report in test-results/smoke.json',flush=True)


if __name__=='__main__':main()
