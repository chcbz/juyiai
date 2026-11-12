"""Release-controller wiring regression; no builds, network or production writes."""
import ast
import importlib.util
from pathlib import Path
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SOURCE = Path(__file__).resolve().parents[1] / 'local_release.py'


class ReleaseRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse(SOURCE.read_text())
        self.runs = {node.args[0].value: node for node in ast.walk(self.tree)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                     and node.func.id == 'run' and node.args
                     and isinstance(node.args[0], ast.Constant)}

    def test_web_helper_and_tls_preflight_use_original_system_python(self):
        for stage in ('web-install', 'preflight-web-tls'):
            command = self.runs[stage].args[1]
            self.assertIsInstance(command, ast.List)
            self.assertEqual('/usr/bin/python3', command.elts[0].value)
            self.assertEqual(['-I', '-B'], [x.value for x in command.elts[1:3]])
        self.assertIn('urlopen', ast.unparse(self.runs['preflight-web-tls']))
        self.assertNotIn('unverified', SOURCE.read_text())

    def test_only_builds_enter_deadline_cgroup(self):
        timed = [name for name, call in self.runs.items()
                 if any(k.arg == 'build' and isinstance(k.value, ast.Constant)
                        and k.value.value is True for k in call.keywords)]
        self.assertEqual({'web-build', 'api-build'}, set(timed))
        self.assertIn("str(int(budget))", SOURCE.read_text())

    def test_diagnostics_and_fake_ci_identity_are_removed(self):
        for value in ('CYF_API_STARTUP_DIAGNOSTICS', 'PIPELINE_', 'CYF_FLOW_', 'CI_COMMIT'):
            self.assertIn(value, SOURCE.read_text())
        self.assertIn("env.pop(key, None)", SOURCE.read_text())

    def test_exact_source_backup_and_full_wall_are_verified(self):
        for text in ("git('status', '--porcelain')", "sha(api_record['backup']) != before_api",
                     "result['buildSeconds']", "ARTIFACT_ATTESTATION=MATCH"):
            self.assertIn(text, SOURCE.read_text())

    def test_budget_excludes_installation_preflight_and_smoke(self):
        spec = importlib.util.spec_from_file_location('local_release_budget', SOURCE)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        stages = [{'name': 'preflight', 'seconds': 100},
                  {'name': 'web-build', 'build': True, 'seconds': 200},
                  {'name': 'api-install', 'build': False, 'seconds': 900}]
        self.assertEqual(200, runner.build_seconds(stages))
        self.assertEqual(400, runner.remaining_build_seconds(stages))
        stages.append({'name': 'api-build', 'build': True, 'seconds': 400})
        with self.assertRaisesRegex(RuntimeError, 'test/build/package'):
            runner.remaining_build_seconds(stages)
        web_install = ast.unparse(self.runs['web-install'])
        self.assertNotIn('remaining', web_install)
        run = next(n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef) and n.name == 'run')
        self.assertIsInstance(run.body[0], ast.If)
        self.assertEqual('build', ast.unparse(run.body[0].test))


if __name__ == '__main__':
    unittest.main()
