"""Lightweight template contract checks; no app builds or cloud side effects."""
import importlib.util
import pathlib
import re
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]


class FlowResourceSplitTest(unittest.TestCase):
    def test_defaults_keep_heavy_work_without_external_wait_or_deployment(self):
        for name in ('frontend-develop-release.yaml', 'backend-develop-release.yaml'):
            text = (BASE / 'templates' / name).read_text()
            self.assertIn('resource-offloaded CI', text)
            self.assertIn('ArtifactUpload', text)
            self.assertNotIn('PDF_PAIR_WAIT', text)
            self.assertNotIn('PDF_PAIR_GATE', text)
            self.assertNotRegex(text, r'(?m)^\s*(deploy|deployment):')
            self.assertNotIn('VMDeploy', text)
            self.assertNotRegex(text, r'while[^\n]*(?:ready-|ready_file|readyFile)')

    def test_frontend_preserves_execution_and_phase_measurements(self):
        text = (BASE / 'templates/frontend-develop-release.yaml').read_text()
        for command in ('npm ci --include=dev', 'npm run test', 'npm run build'):
            self.assertEqual(text.count(command), 1)
        self.assertIn('JavaScriptCodeScan', text)
        for phase in ('runtime', 'install', 'test', 'build'):
            self.assertIn('phase ' + phase + '.begin', text)
            self.assertIn('phase ' + phase + '.end', text)
        self.assertIn('sha256sum -c -', text)
        self.assertIn('package_version:packageVersion', text)

    def test_rendered_backend_keeps_original_policy_and_no_deployment(self):
        spec = importlib.util.spec_from_file_location('prepare_backend_ci', BASE / 'prepare-backend-ci.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = module.render((BASE / 'templates/backend-develop-release.yaml').read_text(),
                             (BASE / 'backend-ci-run.sh').read_text())
        self.assertIn('Backend resource-offloaded CI', text)
        self.assertNotIn('@CYF_TOOL_BUNDLE_', text)
        self.assertIn('gradle', text)
        self.assertIn('--flow-ci', text)
        self.assertIn('CYF_FLOW_PHASE', text)
        self.assertNotIn('VMDeploy', text)
        self.assertNotIn('PDF_PAIR_', text)
        policy = (BASE / 'backend-ci-policy.json').read_text()
        self.assertIn('validateLayering', policy)
        self.assertIn(':starter:bootJar', policy)
        self.assertIn('--tests', policy)


if __name__ == '__main__':
    unittest.main()
