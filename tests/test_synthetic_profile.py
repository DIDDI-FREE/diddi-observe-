import json
from pathlib import Path
import sys
import unittest
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import synthetic_profile


class SyntheticProfileTests(unittest.TestCase):
    def test_only_fixture_enabled(self):
        output = synthetic_profile.outputs()
        registry = json.loads(output['config/synthetic/services.json'])
        enabled = [s['id'] for s in registry['services'] if any(s.get(k, {}).get('enabled') for k in ('metrics','logs','otlp','health'))]
        self.assertEqual(enabled, ['synthetic'])
        conf = yaml.safe_load(output['compose.portainer.synthetic.yaml'])
        self.assertNotIn('ports', conf['services']['synthetic'])
        prom = yaml.safe_load(output['config/synthetic/prometheus.yaml'])
        self.assertTrue(next(j for j in prom['scrape_configs'] if j['job_name'] == 'observe-registry')['honor_labels'])
        self.assertIn('auth_basic_user_file /etc/nginx/auth/synthetic.htpasswd', output['config/synthetic/nginx.conf'])

    def test_generated_current(self):
        for name, content in synthetic_profile.outputs().items():
            self.assertEqual((synthetic_profile.ROOT / name).read_text(), content, name)
