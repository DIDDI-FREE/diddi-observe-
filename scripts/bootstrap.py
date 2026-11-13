"""Create LOCAL credentials and certificate. Never overwrites existing secrets."""
import argparse
import datetime
import ipaddress
import json
import secrets
import subprocess
import sys
from pathlib import Path
import bcrypt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT=Path(__file__).resolve().parents[1]


def write_once(path, content):
    if not path.exists():
        path.write_bytes(content if isinstance(content,bytes) else content.encode())
        path.chmod(0o600)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--demo',action='store_true')
    args=p.parse_args()
    folder=ROOT/'secrets'
    folder.mkdir(exist_ok=True)
    folder.chmod(0o700)
    (ROOT/'runtime/inputs').mkdir(parents=True,exist_ok=True)
    write_once(ROOT/'.env',(ROOT/'.env.example').read_text())
    write_once(folder/'grafana_admin',secrets.token_urlsafe(32)+'\n')
    (folder/'grafana_admin').chmod(0o644)
    if not (folder/'tls.key').exists() and not (folder/'tls.crt').exists():
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'DiddiObserve local test')])
        now=datetime.datetime.now(datetime.timezone.utc)
        cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
              .public_key(key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now-datetime.timedelta(minutes=5))
              .not_valid_after(now+datetime.timedelta(days=30))
              .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False)
              .sign(key,hashes.SHA256()))
        write_once(folder/'tls.key',key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        write_once(folder/'tls.crt',cert.public_bytes(serialization.Encoding.PEM))
    if not (folder/'tls.key').exists() or not (folder/'tls.crt').exists():
        raise SystemExit('Incomplete TLS key/certificate pair; repair manually.')
    data=json.loads((ROOT/'registry/services.json').read_text())
    if args.demo:
        data['services'].append(json.loads((ROOT/'tests/synthetic-registration.json').read_text()))
    for s in data['services']:
        if s.get('otlp',{}).get('enabled'):
            password_file=folder/(s['id']+'.password')
            write_once(password_file,secrets.token_urlsafe(32)+'\n')
            password=password_file.read_text().strip().encode()
            write_once(folder/(s['id']+'.htpasswd'),s['id']+':'+bcrypt.hashpw(password,bcrypt.gensalt()).decode()+'\n')
            (folder/(s['id']+'.htpasswd')).chmod(0o644)
        if s.get('logs',{}).get('enabled'):
            (ROOT/'runtime/inputs'/s['id']).mkdir(parents=True,exist_ok=True)
        if s['id']=='synthetic':
            write_once(folder/'synthetic.metrics',secrets.token_urlsafe(32)+'\n')
        elif s.get('metrics',{}).get('enabled') and not (folder/(s['id']+'.metrics')).exists():
            raise SystemExit(f'Install the existing service scrape token in secrets/{s["id"]}.metrics; no token was invented.')
        if s.get('metrics',{}).get('enabled'):
            (folder/(s['id']+'.metrics')).chmod(0o644)
    subprocess.run([sys.executable,str(ROOT/'scripts/render.py')],check=True)
    if args.demo:
        subprocess.run([sys.executable,str(ROOT/'scripts/render.py'),'--demo'],check=True)
    print('Local credentials ready (not printed). Grafana login: admin. Password: secrets/grafana_admin.')
    print('Certificate valid for localhost/127.0.0.1 only; replace it before remote deployment.')


if __name__=='__main__':main()
