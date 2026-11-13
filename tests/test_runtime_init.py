import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import bcrypt

spec = importlib.util.spec_from_file_location('runtime_init', Path(__file__).resolve().parents[1] / 'app/runtime_init.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'registry').mkdir()
        (self.root / 'registry/services.json').write_text(json.dumps({'services': [
            {'id': 'demo', 'otlp': {'enabled': True}, 'metrics': {'enabled': True}}]}))
        self.paths = patch.object(runtime, 'Path', lambda p: self.root / str(p).lstrip('/'))
        self.paths.start()
        self.addCleanup(self.paths.stop)
        self.chown = patch.object(runtime.os, 'chown', create=True)
        self.chown.start()
        self.addCleanup(self.chown.stop)
        self.env = patch.dict(os.environ, {'OTLP_PASSWORDS_JSON': '{"demo":"unit-password"}',
                                         'METRICS_TOKENS_JSON': '{"demo":"unit-token"}',
                                         'TLS_CERT_PEM': '', 'TLS_KEY_PEM': '',
                                         'OBSERVE_TLS_HOST': 'localhost'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_credentials_from_environment_and_certificate_preserved(self):
        runtime.main()
        cert = (self.root / 'gateway-secret/tls.crt').read_bytes()
        hashed = (self.root / 'gateway-secret/demo.htpasswd').read_text().strip().split(':')[1]
        self.assertTrue(bcrypt.checkpw(b'unit-password', hashed.encode()))
        self.assertEqual((self.root / 'metrics-secret/demo.metrics').read_text(), 'unit-token\n')
        runtime.main()
        self.assertEqual((self.root / 'gateway-secret/tls.crt').read_bytes(), cert)

    def test_incomplete_tls_input_rejected(self):
        os.environ['TLS_CERT_PEM'] = 'incomplete'
        with self.assertRaisesRegex(ValueError, 'provided together'):
            runtime.main()

    def test_missing_enabled_service_password_rejected(self):
        os.environ['OTLP_PASSWORDS_JSON'] = '{}'
        with self.assertRaisesRegex(ValueError, 'Missing OTLP password'):
            runtime.main()
