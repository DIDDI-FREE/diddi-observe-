"""Prepare TLS and per-source credentials from runtime environment, never build args."""
import datetime
import base64
import ipaddress
import json
import os
import re
from pathlib import Path
import bcrypt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def main():
    for directory in ('/volumes/tempo', '/volumes/loki'):
        os.chown(directory, 10001, 10001)
    gateway = Path('/gateway-secret')
    metrics = Path('/metrics-secret')
    gateway.mkdir(exist_ok=True)
    metrics.mkdir(exist_ok=True)
    cert_path, key_path = gateway / 'tls.crt', gateway / 'tls.key'
    cert, key = os.getenv('TLS_CERT_PEM', ''), os.getenv('TLS_KEY_PEM', '')
    cert_b64, key_b64 = os.getenv('TLS_CERT_B64', ''), os.getenv('TLS_KEY_B64', '')
    if cert_b64 or key_b64:
        if cert or key:
            raise ValueError('Use either PEM or base64 TLS input, not both')
        if not cert_b64 or not key_b64:
            raise ValueError('TLS_CERT_B64 and TLS_KEY_B64 must be provided together')
        cert = base64.b64decode(cert_b64, validate=True).decode('ascii')
        key = base64.b64decode(key_b64, validate=True).decode('ascii')
    if bool(cert) != bool(key):
        raise ValueError('TLS_CERT_PEM and TLS_KEY_PEM must be provided together')
    if cert:
        parsed_cert = x509.load_pem_x509_certificate(cert.encode())
        parsed_key = serialization.load_pem_private_key(key.encode(), password=None)
        encoding, form = serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        if parsed_cert.public_key().public_bytes(encoding, form) != parsed_key.public_key().public_bytes(encoding, form):
            raise ValueError('TLS certificate and key do not match')
        cert_path.write_text(cert, newline='\n')
        key_path.write_text(key, newline='\n')
    elif not cert_path.exists() and not key_path.exists():
        host = os.getenv('OBSERVE_TLS_HOST', 'localhost')
        try:
            identity = x509.IPAddress(ipaddress.ip_address(host))
        except ValueError:
            identity = x509.DNSName(host)
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                       .public_key(private.public_key()).serial_number(x509.random_serial_number())
                       .not_valid_before(now - datetime.timedelta(minutes=5))
                       .not_valid_after(now + datetime.timedelta(days=30))
                       .add_extension(x509.SubjectAlternativeName([identity]), critical=False)
                       .sign(private, hashes.SHA256()))
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        print('Created staging self-signed certificate, valid for 30 days.', flush=True)
    elif not cert_path.exists() or not key_path.exists():
        raise ValueError('Incomplete stored TLS certificate/key pair')
    key_path.chmod(0o600)
    cert_path.chmod(0o644)
    passwords = json.loads(os.getenv('OTLP_PASSWORDS_JSON', '{}'))
    tokens = json.loads(os.getenv('METRICS_TOKENS_JSON', '{}'))
    services = json.loads(Path('/registry/services.json').read_text())['services']
    for service in services:
        identifier = service['id']
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,62}', identifier):
            raise ValueError('Invalid registry identifier')
        if identifier == 'synthetic' and Path('/var/log/inputs').exists():
            folder = Path('/var/log/inputs/synthetic')
            folder.mkdir(exist_ok=True)
            os.chown(folder, 65534, 65534)
        if service.get('otlp', {}).get('enabled'):
            password = passwords.get(identifier)
            if not isinstance(password, str) or not password:
                raise ValueError('Missing OTLP password for ' + identifier)
            target = gateway / (identifier + '.htpasswd')
            target.write_text(identifier + ':' + bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() + '\n')
            target.chmod(0o644)
        if service.get('metrics', {}).get('enabled'):
            token = tokens.get(identifier)
            if not isinstance(token, str) or not token or '\n' in token or '\r' in token:
                raise ValueError('Missing/invalid metrics token for ' + identifier)
            target = metrics / (identifier + '.metrics')
            target.write_text(token + '\n')
            target.chmod(0o644)
    print('Storage and runtime credentials ready; values not logged.', flush=True)


if __name__ == '__main__':
    main()
