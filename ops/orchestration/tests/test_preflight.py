import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

P = load('preflight', ROOT / 'preflight.py')
O = load('orchestrator_preflight_test', ROOT / 'cyf_orchestrator.py')


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cyf-preflight-test-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@example.invalid')
        for path in ['build.gradle', 'settings.gradle', 'gradlew', 'package.json', 'package-lock.json', 'fixture.json']:
            (self.repo / path).write_text('{}\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.head = self.git('rev-parse', 'HEAD')
        self.tree = self.git('rev-parse', 'HEAD^{tree}')
        self.ledger = {'tasks': {'T': {'owner': {'agent': 'owner', 'mode': 'writer'},
            'current_gate': 'implementing', 'exact_sha_tree': {'commit_sha': self.head, 'tree_sha': self.tree}}}}
        self.args = Namespace(task_id='T', cwd=self.repo, component='api', baseline='HEAD',
                              selector=':service:test --tests Example', fixture=['fixture.json'])

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo)] + list(args), stderr=subprocess.STDOUT,
                                       universal_newlines=True).strip()

    def report(self):
        return P.collect(self.args, self.ledger)

    def test_clean_matches_and_never_claims_ready(self):
        r = self.report()
        self.assertTrue(r['task_exact_match'])
        self.assertTrue(r['worktree_clean'])
        self.assertEqual('NOT_RUN', r['verification']['execution'])
        self.assertIn('NOT_BUILD', r['verdict'])
        self.assertEqual('present', r['fixtures'][0]['status'])

    def test_dirty_is_advisory_and_does_not_change_ledger_or_index(self):
        (self.repo / 'new.txt').write_text('keep')
        before = json.dumps(self.ledger, sort_keys=True)
        index = (self.repo / '.git/index').read_bytes()
        stream = StringIO()
        with redirect_stdout(stream):
            self.assertEqual(0, P.dispatch(self.args, self.ledger))
        self.assertFalse(json.loads(stream.getvalue())['worktree_clean'])
        self.assertEqual(before, json.dumps(self.ledger, sort_keys=True))
        self.assertEqual(index, (self.repo / '.git/index').read_bytes())
        self.assertEqual('keep', (self.repo / 'new.txt').read_text())

    def test_mismatched_task_baseline_is_reported(self):
        self.ledger['tasks']['T']['exact_sha_tree']['tree_sha'] = 'a' * 40
        self.assertIn('TASK_BASELINE_MISMATCH', [x['code'] for x in self.report()['findings']])

    def test_unavailable_baseline_does_not_fetch(self):
        self.args.baseline = 'refs/remotes/absent/develop'
        self.assertEqual('unavailable', self.report()['baseline']['status'])

    def test_detached_head(self):
        self.git('checkout', '--detach', '-q')
        self.assertIsNone(self.report()['branch'])

    def test_linked_worktree(self):
        target = Path(self.temp.name) / 'linked'
        self.git('worktree', 'add', '--detach', str(target), 'HEAD')
        self.args.cwd = target
        self.assertTrue(self.report()['task_exact_match'])

    def test_older_baseline_reports_head_only_count(self):
        (self.repo / 'second').write_text('second')
        self.git('add', '.'); self.git('commit', '-qm', 'second')
        self.args.baseline = self.head
        self.assertEqual(1, self.report()['baseline']['head_only_commits'])

    def test_baseline_ahead_reports_not_contained(self):
        (self.repo / 'second').write_text('second')
        self.git('add', '.'); self.git('commit', '-qm', 'second')
        self.args.baseline = self.git('rev-parse', 'HEAD')
        self.git('checkout', '--detach', '-q', self.head)
        r = self.report()
        self.assertEqual(1, r['baseline']['baseline_only_commits'])
        self.assertIn('BASELINE_NOT_CONTAINED', [x['code'] for x in r['findings']])

    def test_missing_fixture_and_outside_symlink(self):
        outside = Path(self.temp.name) / 'secret'
        outside.write_text('DO_NOT_PRINT')
        (self.repo / 'link').symlink_to(outside)
        self.args.fixture = ['missing.json', 'link', '../secret']
        r = self.report()
        self.assertEqual(['missing', 'outside_repository', 'outside_repository'], [x['status'] for x in r['fixtures']])
        self.assertNotIn('DO_NOT_PRINT', json.dumps(r))

    def test_fixture_contents_not_read(self):
        with patch.object(Path, 'read_text', side_effect=AssertionError('must not read content')):
            self.assertEqual('present', self.report()['fixtures'][0]['status'])

    def test_web_route_and_missing_tool(self):
        self.args.component = 'web'
        with patch.object(P.shutil, 'which', return_value=None):
            r = self.report()
        self.assertEqual('frontend_Flow_4403172', r['verification']['route'])
        self.assertIn('TOOL_MISSING:node', [x['code'] for x in r['findings']])

    def test_unknown_task_and_subdirectory_are_errors(self):
        self.args.task_id = 'unknown'
        with self.assertRaises(ValueError): self.report()
        self.args.task_id = 'T'
        self.args.cwd = self.repo / 'child'; self.args.cwd.mkdir()
        with self.assertRaises(ValueError): self.report()

    def test_non_git_path_safe_error(self):
        self.args.cwd = Path(self.temp.name)
        stream = StringIO()
        with redirect_stdout(stream): self.assertEqual(2, P.dispatch(self.args, self.ledger))
        self.assertEqual('ERROR', json.loads(stream.getvalue())['status'])

    def test_selector_never_executed_and_git_is_read_only(self):
        self.args.selector = 'touch SHOULD_NOT_EXIST; ./gradlew test'
        original = P.subprocess.run
        calls = []
        def guard(command, **kwargs):
            calls.append(command)
            self.assertEqual('git', command[0])
            self.assertIn(command[5], ['rev-parse', 'status', 'symbolic-ref', 'rev-list'])
            self.assertEqual('0', kwargs['env']['GIT_OPTIONAL_LOCKS'])
            return original(command, **kwargs)
        with patch.object(P.subprocess, 'run', side_effect=guard): self.report()
        self.assertTrue(calls)
        self.assertFalse((self.repo / 'SHOULD_NOT_EXIST').exists())

    def test_parser_dispatch_no_save_or_notification(self):
        args = O.build_parser().parse_args(['preflight', 'T', '--cwd', str(self.repo),
                                          '--component', 'api', '--baseline', 'HEAD'])
        stream = StringIO()
        with patch.object(O, 'load_ledger', return_value=self.ledger), \
             patch.object(O, 'save_ledger', side_effect=AssertionError('write')), \
             patch.object(O, 'emit_notification', side_effect=AssertionError('notify')), redirect_stdout(stream):
            self.assertEqual(0, args.func(args))
        self.assertIn('SELECTOR_NOT_SET', [x['code'] for x in json.loads(stream.getvalue())['findings']])


if __name__ == '__main__':
    unittest.main()
