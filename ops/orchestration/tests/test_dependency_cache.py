"""Isolated cache policy tests. No Gradle/network/production access."""
import importlib.util
import os
from pathlib import Path
from argparse import Namespace
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
import json

spec = importlib.util.spec_from_file_location('cache_orchestrator', Path(__file__).resolve().parents[1] / 'cyf_orchestrator.py')
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)

class DependencyCacheTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'cache'
        self.args = Namespace(dependency_cache_home=self.home, run_uid=None, run_gid=None)
        self.patch = patch.dict(os.environ)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        os.environ.pop('GRADLE_USER_HOME', None)

    def prepare(self, command=None):
        return O.dependency_cache_environment(self.args, command or ['gradle', '--no-build-cache'])

    def test_opt_in_default_unchanged(self):
        self.assertIsNone(O.dependency_cache_environment(Namespace(), ['gradle']))
        self.assertFalse(self.home.exists())

    def test_creates_private_home_and_preserves_other_environment(self):
        os.environ['CYF_MAVEN_USERNAME'] = 'synthetic'
        env = self.prepare()
        self.assertEqual(str(self.home), env['GRADLE_USER_HOME'])
        self.assertEqual('synthetic', env['CYF_MAVEN_USERNAME'])
        self.assertEqual(0o700, self.home.stat().st_mode & 0o777)
        self.assertNotIn('GRADLE_USER_HOME', os.environ)

    def test_reuses_cache_data_without_copies_or_deletion(self):
        self.prepare()
        (self.home/'caches').mkdir()
        (self.home/'caches'/'synthetic.jar').write_bytes(b'keep')
        self.prepare()
        self.assertEqual(b'keep', (self.home/'caches'/'synthetic.jar').read_bytes())

    def test_rejects_implicit_configuration(self):
        for name in ('gradle.properties', 'init.gradle', 'init.gradle.kts'):
            with self.subTest(name=name):
                self.home.mkdir(mode=0o700, exist_ok=True)
                file = self.home/name
                file.write_text('synthetic')
                with self.assertRaises(SystemExit): self.prepare()
                self.assertEqual('synthetic', file.read_text())
                file.unlink()

    def test_rejects_implicit_init_scripts(self):
        self.home.mkdir(mode=0o700)
        (self.home/'init.d').mkdir()
        self.prepare()  # Empty directory is inert.
        (self.home/'init.d'/'injected.gradle').write_text('synthetic')
        with self.assertRaises(SystemExit): self.prepare()

    def test_rejects_symlink_home_and_ancestor(self):
        real = Path(self.temp.name)/'real'
        real.mkdir(mode=0o700)
        self.home.symlink_to(real, target_is_directory=True)
        with self.assertRaises(SystemExit): self.prepare()
        self.args.dependency_cache_home = self.home/'nested'
        with self.assertRaises(SystemExit): self.prepare()
        self.assertFalse((real/'nested').exists())

    def test_rejects_nonprivate_home(self):
        self.home.mkdir(mode=0o755)
        with self.assertRaises(SystemExit): self.prepare()
        self.assertEqual(0o755, self.home.stat().st_mode & 0o777)

    def test_rejects_wrong_owner(self):
        self.home.mkdir(mode=0o700)
        self.args.run_uid = os.geteuid()+10000
        with self.assertRaises(SystemExit): self.prepare()

    def test_rejects_relative_path(self):
        self.args.dependency_cache_home = Path('relative-cache')
        with self.assertRaises(SystemExit): self.prepare()

    def test_rejects_conflicting_environment(self):
        os.environ['GRADLE_USER_HOME'] = '/synthetic/other'
        with self.assertRaises(SystemExit): self.prepare()
        os.environ['GRADLE_USER_HOME'] = str(self.home)
        self.prepare()

    def test_rejects_cli_override(self):
        for arg in ('-g', '-g=/other', '-g/other', '--gradle-user-home', '--gradle-user-home=/other', '-Dgradle.user.home=/other'):
            with self.subTest(arg=arg), self.assertRaises(SystemExit): self.prepare(['gradle', arg])

    def test_file_instead_of_directory_rejected(self):
        self.home.write_text('synthetic')
        self.home.chmod(0o600)
        with self.assertRaises(SystemExit): self.prepare()

    def test_serialized_gradle_passes_cache_environment_and_reports_elapsed(self):
        args = Namespace(task_id='T', heavy=False, cwd=Path(self.temp.name),
                         tree_sha='a'*40, selector='synthetic', fixture_digest='synthetic',
                         artifact=None, command=['gradle', '--no-build-cache'],
                         dependency_cache_home=self.home, run_uid=None, run_gid=None)
        item = {'owner': {'mode': 'writer'}, 'current_gate': 'targeted_verification',
                'exact_sha_tree': {'tree_sha': 'a'*40}}
        ledger = {'tasks': {'T': item}}
        from contextlib import ExitStack
        with ExitStack() as stack:
            stack.enter_context(patch.object(O, 'load_ledger', return_value=ledger))
            stack.enter_context(patch.object(O, 'verify_exact_worktree', return_value=args.cwd))
            stack.enter_context(patch.object(O, 'record_gradle_resource_telemetry'))
            stack.enter_context(patch.object(O, 'load_json', return_value={'records': {}}))
            stack.enter_context(patch.object(O, 'atomic_write'))
            stack.enter_context(patch.object(O, 'EVIDENCE_LOCK', Path(self.temp.name)/'evidence.lock'))
            stack.enter_context(patch.object(O, 'GRADLE_LOCK', Path(self.temp.name)/'gradle.lock'))
            stack.enter_context(patch.object(O.time, 'monotonic', side_effect=[10.0, 12.345]))
            run = stack.enter_context(patch.object(O.subprocess, 'run'))
            run.return_value.returncode = 0
            with redirect_stdout(StringIO()) as out:
                self.assertEqual(0, O.cmd_gradle(args))
            self.assertEqual(str(self.home), run.call_args[1]['env']['GRADLE_USER_HOME'])
            self.assertEqual(args.cwd.as_posix(), run.call_args[1]['cwd'])
            timing = [x for x in out.getvalue().splitlines() if x.startswith('GRADLE_EXECUTION_TIMING ')][0]
            self.assertEqual(2.345, json.loads(timing.split(' ', 1)[1])['elapsed_seconds'])
            self.assertIn('EVIDENCE_STORED', out.getvalue())
