import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('orchestrator_flow_ci', ROOT / 'ops/orchestration/cyf_orchestrator.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FlowCiTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cyf-backend-flow-ci.', dir='/tmp')
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        (self.root / 'build').mkdir()
        self.raw = (ROOT / 'ops/ci/aliyun-flow/backend-ci-policy.json').read_bytes()
        self.policy = json.loads(self.raw)
        self.env = dict(PIPELINE_ID='5260799', BUILD_NUMBER='198', CI_COMMIT_REF_NAME='develop',
                        CI_COMMIT_SHA='a' * 40, CYF_FLOW_GRADLE_ACTIVE='1',
                        CYF_FLOW_COMPILE_CACHE_OPT_IN='1', CYF_FLOW_SHORT_LIVED_TEST_JVM='1',
                        CYF_EXPERIMENT=str(self.root), CYF_FLOW_BUILD_ROOT=str(self.root / 'build'))
        self.args = argparse.Namespace(task_id='FLOW-CI-5260799', tree_sha='b' * 40,
                         selector=self.policy['selector'], fixture_digest=hashlib.sha256(self.raw).hexdigest(),
                         dependency_cache_home=None, run_uid=None, run_gid=None, flow_ci=True,
                         heavy=False, cwd=self.root, artifact=None)
        self.command = [v.replace('$CYF_EXPERIMENT', str(self.root)).replace(
            '$CYF_FLOW_BUILD_ROOT', str(self.root / 'build')) for v in self.policy['argv']]
        self.args.command = self.command

    def context(self):
        with mock.patch.dict(os.environ, self.env, clear=True):
            return m.flow_ci_context(self.args, self.command)

    def test_source_is_current_flow_commit_not_human_snapshot(self):
        self.assertEqual(self.context()['exact_sha_tree'], {'commit_sha': 'a' * 40, 'tree_sha': 'b' * 40})
        self.env['CI_COMMIT_SHA'] = 'c' * 40
        self.assertEqual(self.context()['exact_sha_tree']['commit_sha'], 'c' * 40)

    def test_branch_names_are_not_an_execution_allowlist(self):
        self.assertNotIn('branches', self.policy)
        for branch in ('develop', 'master', 'codex/new-skill-optimization', 'release/2026.11', ''):
            self.env['CI_COMMIT_REF_NAME'] = branch
            self.context()

    def test_wrong_or_missing_flow_identity_rejected(self):
        for name, value in [('PIPELINE_ID', '5264702'), ('BUILD_NUMBER', ''),
                            ('CI_COMMIT_SHA', 'short'),
                            ('CYF_FLOW_GRADLE_ACTIVE', ''), ('CYF_FLOW_COMPILE_CACHE_OPT_IN', ''),
                            ('CYF_FLOW_SHORT_LIVED_TEST_JVM', ''), ('CYF_LOCAL_RELEASE_OPT_IN', '1')]:
            with self.subTest(name=name):
                before = dict(self.env)
                self.env[name] = value
                with self.assertRaises(SystemExit):
                    self.context()
                self.env = before

    def test_policy_task_and_fixture_must_match(self):
        for field in ('task_id', 'selector', 'fixture_digest'):
            previous = getattr(self.args, field)
            setattr(self.args, field, 'wrong')
            with self.assertRaises(SystemExit):
                self.context()
            setattr(self.args, field, previous)

    def test_argv_cannot_drop_tests_or_add_deploy(self):
        for command in (self.command[:-1], self.command + ['publish'],
                        [v for v in self.command if v != 'validateLayering']):
            with mock.patch.dict(os.environ, self.env, clear=True), self.assertRaises(SystemExit):
                m.flow_ci_context(self.args, command)

    def test_stale_output_and_symlink_rejected(self):
        output = self.root / 'build/old.jar'
        output.write_bytes(b'stale')
        with self.assertRaises(SystemExit):
            self.context()
        output.unlink()
        (self.root / 'build/gradle-output.log').symlink_to(self.root / 'outside')
        with self.assertRaises(SystemExit):
            self.context()

    def test_new_output_log_is_allowed(self):
        (self.root / 'build/gradle-output.log').write_text('')
        self.context()

    def test_no_ledger_and_no_evidence_reuse_even_for_same_input(self):
        key = m.evidence_key(self.args.tree_sha, self.args.selector, self.args.fixture_digest)
        cache = {'records': {key: {'result': 'accepted', 'release_cache_policy': None}}}
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(m, 'load_ledger', side_effect=AssertionError('must not read human ledger')), \
                mock.patch.object(m, 'verify_exact_worktree', return_value=self.root) as verify, \
                mock.patch.object(m, 'load_json', return_value=cache), \
                mock.patch.object(m, 'atomic_write', side_effect=AssertionError('must not store whole-run cache')), \
                mock.patch.object(m, 'record_gradle_resource_telemetry'), \
                mock.patch.object(m, 'GRADLE_LOCK', self.root / 'gradle.lock'), \
                mock.patch.object(m, 'EVIDENCE_LOCK', self.root / 'evidence.lock'), \
                mock.patch.object(m, 'emit_notification') as notify, \
                mock.patch.object(m.subprocess, 'run', return_value=argparse.Namespace(returncode=0)) as run:
            self.assertEqual(m.cmd_gradle(self.args), 0)
            run.assert_called_once()
            self.assertEqual(verify.call_count, 2)
            notify.assert_not_called()

    def test_exact_worktree_rejects_head_and_dirty_source(self):
        item = self.context()
        responses = [str(self.root), 'c' * 40, 'b' * 40, '']
        with mock.patch.object(m.subprocess, 'check_output', side_effect=responses), self.assertRaises(SystemExit):
            m.verify_exact_worktree(self.root, item, self.args.tree_sha)
        responses = [str(self.root), 'a' * 40, 'b' * 40, ' M build.gradle']
        with mock.patch.object(m.subprocess, 'check_output', side_effect=responses), self.assertRaises(SystemExit):
            m.verify_exact_worktree(self.root, item, self.args.tree_sha)


if __name__ == '__main__':
    unittest.main()
