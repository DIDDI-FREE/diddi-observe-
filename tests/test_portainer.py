import sys
import unittest
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import portainer


class PortainerTests(unittest.TestCase):
    def test_packaged_configs_no_host_mounts(self):
        config = yaml.safe_load(portainer.render())
        for name, service in config['services'].items():
            self.assertEqual(service['build']['target'], name)
            for mount in service.get('volumes', []):
                self.assertIn(mount.split(':')[0], config['volumes'], mount)


    def test_secrets_are_runtime_only(self):
        config = yaml.safe_load(portainer.render())
        self.assertNotIn('prepare', config['services'])
        for service in config['services'].values():
            self.assertNotIn('args', service['build'])
        self.assertIn('GRAFANA_ADMIN_PASSWORD:?', config['services']['grafana']['environment']['GF_SECURITY_ADMIN_PASSWORD'])
        self.assertEqual(config['services']['gateway']['depends_on']['init-storage']['condition'], 'service_completed_successfully')

    def test_generated_file_current(self):
        self.assertEqual((portainer.ROOT / 'compose.portainer.yaml').read_text(), portainer.render())
