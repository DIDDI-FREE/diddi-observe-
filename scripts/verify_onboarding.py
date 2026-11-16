"""Verify central routes with empty OTLP envelopes, strict TLS, and Grafana reads."""
import base64
import datetime
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def main():
    auth = json.loads((ROOT/'secrets/onboarding/auth.json').read_text())
    ctx = ssl.create_default_context(cafile=str(ROOT/'docs/certs/diddi-observe-staging-ca.pem'))
    def basic(user, password):
        return 'Basic '+base64.b64encode((user+':'+password).encode()).decode()
    admin = basic('admin', auth['admin'])
    def request(path, authorization=admin, body=None):
        headers = {'Content-Type':'application/json'}
        if authorization:
            headers['Authorization'] = authorization
        req = urllib.request.Request(auth['base']+path, headers=headers, data=None if body is None else json.dumps(body).encode())
        try:
            with urllib.request.urlopen(req,context=ctx,timeout=15) as r:
                raw = r.read()
                return r.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            return e.code, {}
    checks = []
    for service in ('diddisend','diddifree-id'):
        other = 'diddifree-id' if service == 'diddisend' else 'diddisend'
        for signal in ('logs','traces'):
            path = '/otlp/'+service+'/v1/'+signal
            for mode, credentials, expected in (
                ('unauthenticated',None,401),
                ('wrong-service',basic(other,auth['passwords'][other]),401),
                ('authorized',basic(service,auth['passwords'][service]),200)):
                code, _ = request(path,credentials,{})
                checks.append(dict(service=service,signal=signal,mode=mode,http=code))
                assert code == expected, checks[-1]
    status, dashboards = request('/api/search?tag=diddi&type=dash-db')
    assert status == 200 and len(dashboards) == 6
    status, rules = request('/api/prometheus/grafana/api/v1/rules')
    assert status == 200
    states = [dict(uid=r['uid'],state=r['state'],health=r['health']) for g in rules['data']['groups'] for r in g['rules']]
    assert len(states) == 4 and all(r['health']=='ok' for r in states)
    query = 'probe_success{job=~"health-(diddisend|diddifree-id)"}'
    status, metrics = request('/api/datasources/proxy/uid/prometheus/api/v1/query?'+urllib.parse.urlencode({'query':query}))
    assert status == 200
    probes = [dict(service=s['metric']['service_name'],value=s['value'][1]) for s in metrics['data']['result']]
    assert len(probes)==2 and all(s['value']=='1' for s in probes), probes
    report = dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),tls_verified=True,routes=checks,dashboards=len(dashboards),alerts=states,private_readiness=probes,producer_ingestion_verified=False)
    dest=ROOT/'test-results/onboarding-verification.json'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
