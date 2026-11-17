import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import team_handoff

class TeamHandoffTests(unittest.TestCase):
    def test_private_ingress_requires_no_ca(self):
        for service in ('diddifree-id','diddisend'):
            c=team_handoff.contract(service)
            self.assertEqual(c['ingress']['base_url'],'http://diddi-observe-gateway-1:8080')
            self.assertFalse(c['ingress']['public_ingress_verified'])
            self.assertFalse(c['ingress']['tls']['custom_ca_required'])
            self.assertTrue(c['ingress']['tls']['verify'])
            self.assertEqual(c['log_schema_version'],'1.0.0')
            for k,v in c['environment_variables'].items():
                if any(x in k for x in ('CA_FILE','CERTIFICATE','KEY_FILE','TOKEN','HEADERS')):
                    self.assertEqual(v,'',k)

    def test_module_transport_is_preserved(self):
        self.assertEqual(team_handoff.contract('diddifree-id')['logs']['transport'],'file-jsonl')
        self.assertEqual(team_handoff.contract('diddisend')['logs']['transport'],'otlp-http')

    def test_env_migration_preserves_credentials_and_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as d, patch.object(team_handoff,'ROOT',Path(d)):
            folder=Path(d)/'secrets/onboarding';folder.mkdir(parents=True)
            for service, token in [('diddisend','METRICS_BEARER_TOKEN'),('diddifree-id','METRICS_AUTH_TOKEN')]:
                p=folder/(service+'.env')
                p.write_text(token+'=test-token\nOTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic test-value==\nOTP_LOG_PLAINTEXT=true\n')
                team_handoff.update_private_env(service)
                values=dict(x.split('=',1) for x in p.read_text().splitlines() if x and not x.startswith('#'))
                self.assertEqual(values[token],'test-token')
                self.assertEqual(values['OTEL_EXPORTER_OTLP_HEADERS'],'Authorization=Basic test-value==')
                self.assertEqual(values['OTP_LOG_PLAINTEXT'],'true')

    def test_generated_files(self):
        for name, content in team_handoff.outputs().items():
            self.assertEqual((team_handoff.ROOT/name).read_text(encoding='utf-8'),content)
            json.loads(content)
