"""Validate the release entry's external config boundary without a Web build."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'local-web-build.mjs'
NODE = '/home/isp/apps/node/bin/node'


class WebRuntimeConfigTest(unittest.TestCase):
    def invoke(self, overrides):
        with tempfile.TemporaryDirectory(dir=str(SCRIPT.parent)) as folder:
            root = Path(folder)
            source = root / 'source'
            vite = source / 'node_modules/vite/dist/node'
            vite.mkdir(parents=True)
            (source / 'package.json').write_text('{"type":"module"}')
            (source / 'node_modules/vite/package.json').write_text('{"type":"module"}')
            (vite / 'index.js').write_text(
                "import {writeFileSync} from 'node:fs';\n"
                "export const loadEnv = () => Object.fromEntries(Object.entries(process.env).filter(([k]) => k.startsWith('VITE_')));\n"
                "export const build = ({build}) => writeFileSync(build.outDir + '.called', 'yes');\n")
            output = root / 'dist'
            env = {k: v for k, v in os.environ.items() if not k.startswith('VITE_')}
            env.update(overrides)
            result = subprocess.run([NODE, str(SCRIPT), str(source), str(output)],
                                    env=env, capture_output=True, text=True)
            metadata = root / 'runtime-config.json'
            return (result.returncode, result.stderr,
                    (root / 'dist.called').exists(),
                    json.loads(metadata.read_text()) if metadata.exists() else None)

    def test_missing_api_address_stops_before_build(self):
        rc, err, built, metadata = self.invoke({})
        self.assertNotEqual(rc, 0)
        self.assertIn('VITE_API_BASE_URL', err)
        self.assertFalse(built)
        self.assertIsNone(metadata)

    def test_missing_client_stops_before_build(self):
        rc, err, built, metadata = self.invoke({'VITE_API_BASE_URL': 'https://api.example.test'})
        self.assertNotEqual(rc, 0)
        self.assertIn('VITE_OAUTH_CLIENT_ID', err)
        self.assertFalse(built)
        self.assertIsNone(metadata)

    def test_external_config_is_recorded_before_build(self):
        config = {'VITE_API_BASE_URL': 'https://api.example.test', 'VITE_OAUTH_CLIENT_ID': 'test-client'}
        rc, err, built, metadata = self.invoke(config)
        self.assertEqual(rc, 0, err)
        self.assertTrue(built)
        self.assertEqual(metadata, config)


if __name__ == '__main__':
    unittest.main()
