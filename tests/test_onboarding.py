import json
import sys
import unittest
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import onboarding_profile
import portainer
import render
import copy

class OnboardingTests(unittest.TestCase):
    def test_only_authorized_routes_and_health(self):
        output = onboarding_profile.outputs()
        registry = json.loads(output['config/onboarding/services.json'])
        for s in registry['services']:
            if s['id'] in ('diddisend', 'diddifree-id'):
                self.assertTrue(s['otlp']['enabled'])
                self.assertTrue(s['health']['enabled'])
                self.assertTrue(s['metrics']['enabled'])
                self.assertEqual(s['logs']['enabled'], s['id'] == 'diddifree-id')
                self.assertEqual(s['state'], 'inventoried')
                for signal in ('logs', 'traces'):
                    self.assertIn('location = /otlp/' + s['id'] + '/v1/' + signal, output['config/onboarding/nginx.conf'])
            elif s['id'] == 'diddigo':
                self.assertTrue(s['otlp']['enabled'])
                self.assertTrue(s['metrics']['enabled'])
                self.assertFalse(any(s[k]['enabled'] for k in ('health','logs')))
            elif s['id'] == 'diddipay':
                self.assertTrue(s['metrics']['enabled'])
                self.assertTrue(s['otlp']['enabled'])
                self.assertFalse(s['logs']['enabled'])
                for signal in ('logs', 'traces'):
                    self.assertIn('/otlp/diddipay/v1/' + signal, output['config/onboarding/nginx.conf'])
            elif s['id'] == 'diddicomms':
                self.assertTrue(s['metrics']['enabled'])
                self.assertFalse(any(s[k]['enabled'] for k in ('health','otlp','logs')))
            elif s['id'] != 'synthetic':
                self.assertFalse(any(s[k]['enabled'] for k in ('otlp','health','metrics','logs')))
        self.assertEqual(output['config/onboarding/nginx.conf'].count('location = /synthetic-test'), 1)
        self.assertIn('http://diddi-observe-alloy-1:4402', output['config/onboarding/nginx.conf'])
        self.assertNotIn('http://alloy:', output['config/onboarding/nginx.conf'])
        self.assertIn('diddi-observe-blackbox-1:9115', output['config/onboarding/prometheus.yaml'])

    def test_http_is_ingestion_only_and_published_on_dedicated_port(self):
        nginx = onboarding_profile.outputs()['config/onboarding/nginx.conf']
        private = nginx[nginx.index('    listen 8080;'):]
        self.assertIn('auth_basic_user_file /etc/nginx/auth/diddisend.htpasswd', private)
        self.assertIn('location / { return 404; }', private)
        self.assertNotIn('grafana', private)
        config = yaml.safe_load(portainer.render())
        self.assertIn('${OBSERVE_HTTP_BIND:-0.0.0.0}:${OBSERVE_HTTP_PORT:-19480}:8080', config['services']['gateway']['ports'])

    def test_network_scope(self):
        cfg = yaml.safe_load(portainer.render())
        for name, s in cfg['services'].items():
            if name in ('prometheus','blackbox','gateway'):
                self.assertIn('source-id', s['networks'])
                self.assertIn('source-send', s['networks'])
            else:
                self.assertNotIn('source-id', s.get('networks', []))
                self.assertNotIn('source-send', s.get('networks', []))

    def test_public_http_exception_is_staging_only(self):
        registry = json.loads(onboarding_profile.outputs()['config/onboarding/services.json'])
        go = next(s for s in registry['services'] if s['id'] == 'diddigo')
        render.validate(registry)
        go['environment'] = 'production'
        with self.assertRaises(ValueError):
            render.validate(registry)
        go['environment'] = 'staging'
        go['metrics'].pop('public_http_mvp')
        with self.assertRaises(ValueError):
            render.validate(registry)

    def test_generated_current(self):
        for name, content in onboarding_profile.outputs().items():
            self.assertEqual((onboarding_profile.ROOT / name).read_text(), content)

    def test_id_file_scope_and_storage(self):
        registry = json.loads(onboarding_profile.outputs()['config/onboarding/services.json'])
        identity = next(s for s in registry['services'] if s['id'] == 'diddifree-id')
        self.assertEqual([s['path'] for s in identity['logs']['sources']],
                         ['/var/log/diddifree/observability-api.jsonl', '/var/log/diddifree/observability-worker.jsonl'])
        cfg = yaml.safe_load(portainer.render())
        alloy = cfg['services']['alloy']
        self.assertIn('id-observability-logs:/var/log/diddifree:ro', alloy['volumes'])
        self.assertIn('alloy-data:/var/lib/alloy', alloy['volumes'])
        self.assertIn('--storage.path=/var/lib/alloy', alloy['command'])
        self.assertNotIn('docker.sock', portainer.render())
        identity['logs']['sources'][0]['path'] += '.1'
        with self.assertRaises(ValueError):
            render.validate(registry)
