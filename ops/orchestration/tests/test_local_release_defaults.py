"""Default policy tests only; no real Gradle/production/network."""
from argparse import Namespace
from pathlib import Path
import importlib.util
import os
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('defaults_o', Path(__file__).resolve().parents[1]/'cyf_orchestrator.py')
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)

class LocalReleaseDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.meta = Path(self.temp.name)/'local-release-metadata.init.gradle'
        self.meta.write_bytes((O.ROOT/'ops/ci/aliyun-flow'/self.meta.name).read_bytes())
        self.args = Namespace(dependency_cache_home=None, run_uid=None)
        self.argv = ['gradle', '--console=plain', '-I', str(self.meta), ':starter:bootJar']
        self.patch = patch.dict(os.environ)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        for name in ('CYF_LOCAL_RELEASE_OPT_IN', 'CYF_LOCAL_GRADLE_ACTIVE', 'CYF_FLOW_GRADLE_ACTIVE'):
            os.environ.pop(name, None)

    def resolve(self):
        return O.local_release_cache_defaults(self.args, self.argv)

    def enable(self):
        os.environ.update(CYF_LOCAL_RELEASE_OPT_IN='1', CYF_LOCAL_GRADLE_ACTIVE='1')

    def test_nonrelease_diagnostics_unchanged(self):
        effective, policy = self.resolve()
        self.assertEqual(self.argv, effective)
        self.assertIsNone(policy)
        self.assertIsNone(self.args.dependency_cache_home)

    def test_default_enables_both_caches_and_records_policy(self):
        self.enable()
        with patch.object(O.os, 'geteuid', return_value=0): effective, policy = self.resolve()
        self.assertIn('--build-cache', effective)
        self.assertNotIn('--build-cache', self.argv)
        self.assertEqual('/var/cache/cyf-gradle-local', policy['dependency_cache_home'])
        self.assertTrue(policy['compile_cache'])
        self.assertEqual(64, len(policy['metadata_sha256']))

    def test_defaults_idempotent_and_exact_argv_can_be_bound_before_fixture(self):
        self.enable()
        effective, a = self.resolve()
        self.argv = effective
        twice, b = self.resolve()
        self.assertEqual(effective, twice)
        self.assertEqual(a, b)
        self.assertEqual(1, twice.count('--build-cache'))

    def test_explicit_no_compile_cache_respected(self):
        self.enable()
        self.argv.append('--no-build-cache')
        effective, policy = self.resolve()
        self.assertEqual(self.argv, effective)
        self.assertFalse(policy['compile_cache'])
        self.assertIsNotNone(self.args.dependency_cache_home)

    def test_explicit_cache_home_respected(self):
        self.enable()
        self.args.dependency_cache_home = Path('/synthetic/private-home')
        _, policy = self.resolve()
        self.assertEqual('/synthetic/private-home', policy['dependency_cache_home'])

    def test_delegated_identity_has_separate_default_home(self):
        self.enable()
        self.args.run_uid = 61001
        _, policy = self.resolve()
        self.assertEqual('/var/cache/cyf-gradle-local-61001', policy['dependency_cache_home'])

    def test_missing_local_context_or_flow_context_refused(self):
        self.enable()
        os.environ['CYF_LOCAL_GRADLE_ACTIVE'] = '0'
        with self.assertRaises(SystemExit): self.resolve()
        os.environ['CYF_LOCAL_GRADLE_ACTIVE'] = '1'
        os.environ['CYF_FLOW_GRADLE_ACTIVE'] = '1'
        with self.assertRaises(SystemExit): self.resolve()

    def test_missing_or_duplicate_init_refused(self):
        self.enable()
        self.argv = ['gradle', ':starter:bootJar']
        with self.assertRaises(SystemExit): self.resolve()
        self.argv += ['-I', str(self.meta), '-I', str(self.meta)]
        with self.assertRaises(SystemExit): self.resolve()

    def test_stale_or_tampered_policy_refused(self):
        self.enable()
        self.meta.write_text('// old policy without test freshness')
        with self.assertRaises(SystemExit): self.resolve()

    def test_symlink_init_refused(self):
        self.enable()
        real = self.meta.with_name('real')
        self.meta.rename(real)
        self.meta.symlink_to(real)
        with self.assertRaises(SystemExit): self.resolve()

    def test_conflicting_flags_refused(self):
        self.enable()
        self.argv += ['--build-cache', '--no-build-cache']
        with self.assertRaises(SystemExit): self.resolve()

    def test_accepted_evidence_with_other_policy_does_not_skip_gradle(self):
        self.enable()
        args = Namespace(task_id='T', heavy=False, cwd=Path(self.temp.name),
            tree_sha='a'*40, selector='synthetic', fixture_digest='synthetic',
            artifact=None, command=self.argv, dependency_cache_home=None, run_uid=None, run_gid=None)
        item = {'owner': {'mode': 'writer'}, 'current_gate': 'targeted_verification',
                'exact_sha_tree': {'tree_sha': 'a'*40}}
        key = O.evidence_key(args.tree_sha, args.selector, args.fixture_digest)
        with ExitStack() as stack:
            stack.enter_context(patch.object(O, 'load_ledger', return_value={'tasks': {'T': item}}))
            stack.enter_context(patch.object(O, 'verify_exact_worktree', return_value=args.cwd))
            stack.enter_context(patch.object(O, 'record_gradle_resource_telemetry'))
            stack.enter_context(patch.object(O, 'dependency_cache_environment', return_value=None))
            stack.enter_context(patch.object(O, 'load_json', return_value={'records': {key:
                {'result': 'accepted', 'release_cache_policy': {'metadata_sha256': 'different'}}}}))
            write = stack.enter_context(patch.object(O, 'atomic_write'))
            stack.enter_context(patch.object(O, 'EVIDENCE_LOCK', Path(self.temp.name)/'evidence.lock'))
            stack.enter_context(patch.object(O, 'GRADLE_LOCK', Path(self.temp.name)/'gradle.lock'))
            run = stack.enter_context(patch.object(O.subprocess, 'run'))
            run.return_value.returncode = 0
            with redirect_stdout(StringIO()) as out:
                self.assertEqual(0, O.cmd_gradle(args))
            self.assertEqual(1, run.call_count)
            effective = run.call_args[0][0]
            self.assertIn('--build-cache', effective)
            record = write.call_args[0][1]['records'][key]
            self.assertEqual(effective, record['effective_argv'])
            self.assertTrue(record['release_cache_policy']['compile_cache'])
            self.assertNotIn('EVIDENCE_HIT', out.getvalue())
