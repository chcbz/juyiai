"""Portable builder CLI plans only; never builds, contacts hosts or reads auth."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BUILDER = Path(__file__).resolve().parents[1] / 'runtime_build.py'

class RuntimeBuildCliTest(unittest.TestCase):
    def command(self, root):
        return [sys.executable, str(BUILDER), '--source', str(root),
                '--output', str(root / 'missing-parent/output'), '--node', '/fixture/node',
                '--dependencies', str(root), '--codex-bin', '/fixture/codex',
                '--commit', 'a' * 40, '--tree', 'b' * 40, '--build-id', 'fixture', '--plan-only']

    def test_plan_records_additive_selector_without_creating_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = subprocess.run(self.command(root) + ['--regression-test', 'conf/codex-bridge/test/image-input.test.mjs'], capture_output=True, text=True)
            self.assertEqual(0, p.returncode, p.stderr)
            plan = json.loads(p.stdout)
            self.assertEqual(600, plan['limitSeconds'])
            self.assertEqual(['conf/codex-bridge/test/image-input.test.mjs'], plan['additionalTests'])
            self.assertFalse((root / 'missing-parent').exists())

    def test_additional_selector_cannot_escape_source(self):
        with tempfile.TemporaryDirectory() as d:
            for value in ('../other.test.mjs', '/absolute.test.mjs', 'not-a-node-test.py'):
                p = subprocess.run(self.command(Path(d)) + ['--regression-test', value], capture_output=True, text=True)
                self.assertNotEqual(0, p.returncode)
                self.assertIn('source-relative', p.stderr)

if __name__ == '__main__':
    unittest.main()
