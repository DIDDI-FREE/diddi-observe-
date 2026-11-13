import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render',ROOT/'scripts/render.py')
render=importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'registry/services.json').read_text())
        self.demo=json.loads((ROOT/'tests/synthetic-registration.json').read_text())

    def test_real_services_disabled(self):
        render.validate(self.data)
        for s in self.data['services']:
            self.assertEqual(s['state'],'inventoried')
            self.assertFalse(any(s[k]['enabled'] for k in ('metrics','health','otlp','logs')))

    def test_public_plain_http_rejected(self):
        self.demo['metrics'].pop('isolated_network')
        with self.assertRaises(ValueError):render.validate({'services':[self.demo]})

    def test_credentials_in_url_rejected(self):
        self.demo['metrics']['url']='https://user:password@example.test/metrics'
        with self.assertRaises(ValueError):render.validate({'services':[self.demo]})

    def test_unauthenticated_scrape_rejected(self):
        self.demo['metrics']['auth']='none'
        with self.assertRaises(ValueError):render.validate({'services':[self.demo]})

    def test_false_compliance_rejected(self):
        self.demo['state']='conformant-v1'
        with self.assertRaises(ValueError):render.validate({'services':[self.demo]})

    def test_config_injection_rejected(self):
        self.demo['id']='x"; evil'
        with self.assertRaises(ValueError):render.validate({'services':[self.demo]})

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):render.validate({'services':[self.demo,self.demo]})

    def test_gateway_routes_are_exact_and_per_service(self):
        text=render.nginx({'services':[self.demo]})
        self.assertIn('location = /otlp/synthetic/v1/traces',text)
        self.assertIn('/etc/nginx/auth/synthetic.htpasswd',text)
        self.assertIn('location /otlp/ { return 404; }',text)

    def test_base_has_no_host_socket_or_backend_ports(self):
        cfg=render.compose(self.data)
        for name,s in cfg['services'].items():
            if name!='gateway':self.assertNotIn('ports',s)
            self.assertNotIn('docker.sock',json.dumps(s))
        self.assertTrue(cfg['networks']['backend']['internal'])

    def test_generated_files_are_current(self):
        for name,value in render.outputs(self.data).items():
            self.assertEqual((ROOT/name).read_text(),value,name)

    def test_dashboards_have_unique_identity_and_no_zero_fill(self):
        dashboards=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'dashboards').glob('*.json')]
        self.assertEqual(len(dashboards),6)
        self.assertEqual(len({d['uid'] for d in dashboards}),6)
        self.assertNotIn('or vector(0)',json.dumps(dashboards))


if __name__=='__main__':unittest.main()
