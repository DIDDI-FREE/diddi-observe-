import json
import sys
import unittest
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import onboarding_profile
import portainer

class OnboardingTests(unittest.TestCase):
    def test_only_authorized_routes_and_health(self):
        output = onboarding_profile.outputs()
        registry = json.loads(output['config/onboarding/services.json'])
        for s in registry['services']:
            if s['id'] in ('diddisend', 'diddifree-id'):
                self.assertTrue(s['otlp']['enabled'])
                self.assertTrue(s['health']['enabled'])
                self.assertFalse(s['metrics']['enabled'])
                self.assertFalse(s['logs']['enabled'])
                self.assertEqual(s['state'], 'inventoried')
                for signal in ('logs', 'traces'):
                    self.assertIn('location = /otlp/' + s['id'] + '/v1/' + signal, output['config/onboarding/nginx.conf'])
            elif s['id'] != 'synthetic':
                self.assertFalse(any(s[k]['enabled'] for k in ('otlp','health','metrics','logs')))
        self.assertEqual(output['config/onboarding/nginx.conf'].count('location = /synthetic-test'), 1)
        self.assertIn('http://diddi-observe-alloy-1:4402', output['config/onboarding/nginx.conf'])
        self.assertNotIn('http://alloy:', output['config/onboarding/nginx.conf'])
        self.assertIn('diddi-observe-blackbox-1:9115', output['config/onboarding/prometheus.yaml'])

    def test_network_scope(self):
        cfg = yaml.safe_load(portainer.render())
        for name, s in cfg['services'].items():
            if name in ('prometheus','blackbox','gateway'):
                self.assertIn('source-id', s['networks'])
                self.assertIn('source-send', s['networks'])
            else:
                self.assertNotIn('source-id', s.get('networks', []))
                self.assertNotIn('source-send', s.get('networks', []))

    def test_generated_current(self):
        for name, content in onboarding_profile.outputs().items():
            self.assertEqual((onboarding_profile.ROOT / name).read_text(), content)
