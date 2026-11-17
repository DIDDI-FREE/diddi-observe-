"""One-time staging credentials and CA. All private material stays under secrets/."""
import base64
import datetime as dt
import ipaddress
import json
import secrets
from team_handoff import settings
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'secrets/onboarding'

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    if (DEST / 'central-env.json').exists():
        raise SystemExit('Already provisioned; reuse existing files instead of rotating implicitly.')
    env = json.loads((DEST / 'previous-env.json').read_text())
    values = {e['name']: e['value'] for e in env}
    passwords = json.loads(values.get('OTLP_PASSWORDS_JSON', '{}'))
    tokens = json.loads(values.get('METRICS_TOKENS_JSON', '{}'))
    now = dt.datetime.now(dt.timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'DIDDI Observe Staging CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now-dt.timedelta(minutes=5)).not_valid_after(now+dt.timedelta(days=365))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False), critical=True)
          .sign(ca_key, hashes.SHA256()))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'diddi-observe-gateway-1')]))
            .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-dt.timedelta(minutes=5)).not_valid_after(now+dt.timedelta(days=90))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('diddi-observe-gateway-1'),x509.IPAddress(ipaddress.ip_address('169.58.70.37'))]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256()))
    def private(k):
        return k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    ca_pem = ca.public_bytes(serialization.Encoding.PEM).decode()
    (DEST/'ca.key').write_text(private(ca_key))
    (DEST/'server.key').write_text(private(key))
    (DEST/'ca.pem').write_text(ca_pem)
    (DEST/'server.pem').write_text(cert.public_bytes(serialization.Encoding.PEM).decode())
    public = ROOT / 'docs/certs/diddi-observe-staging-ca.pem'
    public.parent.mkdir(exist_ok=True)
    public.write_text(ca_pem, newline='\n')
    for name in ('diddisend','diddifree-id'):
        passwords[name] = secrets.token_urlsafe(36)
        tokens[name] = secrets.token_urlsafe(36)
        header = 'Authorization=Basic '+base64.b64encode((name+':'+passwords[name]).encode()).decode()
        module = settings(name)
        module['OTEL_EXPORTER_OTLP_HEADERS'] = header
        module['METRICS_BEARER_TOKEN' if name=='diddisend' else 'METRICS_AUTH_TOKEN'] = tokens[name]
        (DEST/(name+'.env')).write_text(''.join(k+'='+v+'\n' for k,v in module.items()), newline='\n')
    values.update(OTLP_PASSWORDS_JSON=json.dumps(passwords), METRICS_TOKENS_JSON=json.dumps(tokens),
                  TLS_CERT_B64=base64.b64encode(cert.public_bytes(serialization.Encoding.PEM)).decode(), TLS_KEY_B64=base64.b64encode(private(key).encode()).decode(),
                  OBSERVE_PILOT_PREFIX='onboarding-', COMPOSE_PROFILES='synthetic',
                  OBSERVE_SOURCE_NETWORKS_EXTERNAL='true', OBSERVE_ID_NETWORK='diddi-auth_default', OBSERVE_SEND_NETWORK='diddisend-backend_default')
    (DEST/'central-env.json').write_text(json.dumps([dict(name=k,value=v) for k,v in values.items()]))
    (DEST/'auth.json').write_text(json.dumps(dict(base='https://169.58.70.37:19443',admin=values['GRAFANA_ADMIN_PASSWORD'],passwords=passwords)))
    print('Provisioned two independent credential pairs; private values not printed.')
    print('CA SHA256: '+ca.fingerprint(hashes.SHA256()).hex())
    print('Server certificate expires: '+cert.not_valid_after_utc.isoformat())

if __name__ == '__main__':
    main()
