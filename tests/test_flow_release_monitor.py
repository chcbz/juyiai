import contextlib
import importlib.machinery
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'ops/ci/aliyun-flow/flow-release-monitor.py'


def load():
    return importlib.machinery.SourceFileLoader('flow_release_monitor', str(SCRIPT)).load_module()


class FlowReleaseMonitorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='flow-release-monitor-')
        self.path = pathlib.Path(self.tmp.name) / 'state.json'
        self.monitor = load()
        self.target = {
            'task_id': 'FLOW-RELEASE-MONITOR-20260912',
            'pipeline': '5260799',
            'run': '20',
            'expected_commit': 'a' * 40,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def config(self):
        return {'targets': [self.target], 'state': str(self.path)}

    def state(self):
        return json.loads(self.path.read_text())

    def source(self, commits=None, repo='https://github.com/chcbz/juyiai-api.git', branch='develop'):
        return {'repo': repo, 'branch': branch,
                'commits': ['a' * 40] if commits is None else commits}

    def flow_process(self, sources, status='SUCCESS'):
        process = mock.Mock(returncode=0)
        process.communicate.return_value = (json.dumps({
            'org': self.monitor.FLOW_ORG, 'pipeline': self.target['pipeline'],
            'run': self.target['run'], 'status': status, 'sources': sources,
        }).encode('utf-8'), b'')
        return process

    def test_expected_in_history_is_not_head_and_exits_two_after_mail_acceptance(self):
        commits = ['b' * 40, 'a' * 40, 'b' * 40]
        process = self.flow_process([self.source(commits=commits)])
        with mock.patch.object(self.monitor.subprocess, 'Popen', return_value=process), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(('SUCCESS', commits), self.monitor._flow_status(self.target))
            self.assertEqual(2, self.monitor.check(self.config()))
            self.assertEqual(2, self.monitor.check(self.config()))
        mail.assert_called_once()
        self.assertIn('SHA不匹配', mail.call_args[0][0])
        self.assertNotIn('已匹配', mail.call_args[0][1])
        notices = next(iter(self.state()['targets'].values()))['notices']
        self.assertNotIn('success_expected_commit', notices)

    def test_head_matches_with_unsorted_history_and_is_deduplicated(self):
        process = self.flow_process([self.source(commits=['a' * 40, '0' * 40])])
        with mock.patch.object(self.monitor.subprocess, 'Popen', return_value=process), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(0, self.monitor.check(self.config()))
            self.assertEqual(0, self.monitor.check(self.config()))
        mail.assert_called_once()
        self.assertIn('已匹配', mail.call_args[0][1])

    def test_wrong_repo_or_branch_rejected_without_success_notification(self):
        for source in [self.source(repo='https://github.com/chcbz/juyiai-web.git'),
                       self.source(repo='https://other.invalid/chcbz/jia.git'),
                       self.source(repo='https://gitee.com/other/jia.git'),
                       self.source(branch='master'), self.source(branch=None)]:
            with self.subTest(source=source):
                process = self.flow_process([source])
                with mock.patch.object(self.monitor.subprocess, 'Popen', return_value=process), \
                     mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
                    self.assertTrue(self.monitor._observe_target(self.target, {}))
                mail.assert_not_called()

    def test_missing_or_multiple_sources_are_ambiguous(self):
        for sources in [None, [], [self.source(), self.source()],
                        [self.source(), self.source(repo='https://other.invalid/jia.git')]]:
            with self.subTest(sources=sources):
                with mock.patch.object(self.monitor.subprocess, 'Popen',
                                       return_value=self.flow_process(sources)), \
                     mock.patch.object(self.monitor, '_send_email') as mail:
                    self.assertTrue(self.monitor._observe_target(self.target, {}))
                mail.assert_not_called()

    def test_invalid_first_commit_cannot_promote_valid_history_to_head(self):
        for commits in [[None, 'a' * 40], ['invalid', 'a' * 40], ['a' * 40 + '\n']]:
            with self.subTest(commits=commits):
                with mock.patch.object(self.monitor.subprocess, 'Popen',
                                       return_value=self.flow_process([self.source(commits=commits)])):
                    with self.assertRaisesRegex(self.monitor.ObservationError, 'flow_sources_invalid'):
                        self.monitor._flow_status(self.target)

    def test_missing_head_cannot_match_success(self):
        with mock.patch.object(self.monitor.subprocess, 'Popen',
                               return_value=self.flow_process([self.source(commits=[])])), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(2, self.monitor.check(self.config()))
        self.assertIn('SHA不匹配', mail.call_args[0][0])

    def test_all_four_pipelines_require_their_component_repository(self):
        for pipeline, repo in [('5260799', 'jia.git'), ('5263690', 'jia.git'),
                               ('4403172', 'cyf-web-kit.git'), ('5263692', 'cyf-web-kit.git')]:
            with self.subTest(pipeline=pipeline):
                self.target['pipeline'] = pipeline
                source = self.source(repo='https://gitee.com/chcbz/' + repo)
                with mock.patch.object(self.monitor.subprocess, 'Popen',
                                       return_value=self.flow_process([source])):
                    self.assertEqual(('SUCCESS', ['a' * 40]), self.monitor._flow_status(self.target))

    def test_failure_and_cancellation_exit_two_even_when_mail_accepted(self):
        for status in ('FAIL', 'CANCELED'):
            with self.subTest(status=status):
                with mock.patch.object(self.monitor, '_flow_status', return_value=(status, ['a' * 40])), \
                     mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
                    self.assertEqual(2, self.monitor.check(self.config()))
                    self.assertEqual(2, self.monitor.check(self.config()))
                mail.assert_called_once()

    def test_existing_three_attempt_receipt_is_preserved(self):
        record = {'attempts': 3, 'accepted': False,
                  'receipt': {'accepted_by_mail_helper': False, 'inbox_delivery': 'unknown'}}
        state = {'version': 1, 'targets': {self.monitor._target_key(self.target): {
            'last_observation': {'kind': 'status', 'status': 'FAIL', 'commits': ['0' * 40, 'a' * 40]},
            'notices': {'terminal_fail': record}}}}
        self.path.write_text(json.dumps(state))
        with mock.patch.object(self.monitor.subprocess, 'Popen', return_value=self.flow_process(
                [self.source(commits=['a' * 40, '0' * 40])], status='FAIL')), \
             mock.patch.object(self.monitor, '_send_email') as mail:
            self.assertEqual(2, self.monitor.check(self.config()))
        mail.assert_not_called()
        self.assertEqual(record, next(iter(self.state()['targets'].values()))['notices']['terminal_fail'])

    def test_success_with_capped_unaccepted_mail_still_requires_controller(self):
        record = {'attempts': 3, 'accepted': False,
                  'receipt': {'accepted_by_mail_helper': False, 'inbox_delivery': 'unknown'}}
        state = {'version': 1, 'targets': {self.monitor._target_key(self.target): {
            'last_observation': {'kind': 'status', 'status': 'SUCCESS', 'commits': ['a' * 40]},
            'notices': {'success_expected_commit': record}}}}
        self.path.write_text(json.dumps(state))
        for enabled in (True, False):
            config = self.config()
            config['mail_enabled'] = enabled
            with mock.patch.object(self.monitor, '_flow_status', return_value=('SUCCESS', ['a' * 40])), \
                 mock.patch.object(self.monitor, '_send_email') as mail:
                self.assertEqual(2, self.monitor.check(config))
                self.assertEqual(2, self.monitor.check(config))
            mail.assert_not_called()
            saved = next(iter(self.state()['targets'].values()))
            self.assertEqual(record, saved['notices']['success_expected_commit'])

    def test_success_is_deduplicated_and_receipt_is_not_inbox_claim(self):
        with mock.patch.object(self.monitor, '_flow_status', return_value=('SUCCESS', ['a' * 40])), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(0, self.monitor.check(self.config()))
            self.assertEqual(0, self.monitor.check(self.config()))
        mail.assert_called_once()
        self.assertIn('Flow成功，线上版本/业务验收仍需主控核验', mail.call_args[0][1])
        saved = self.state()
        record = next(iter(saved['targets'].values()))['notices']['success_expected_commit']
        self.assertTrue(record['accepted'])
        self.assertEqual('unknown', record['receipt']['inbox_delivery'])

    def test_sha_mismatch_notifies_once_and_requires_controller(self):
        with mock.patch.object(self.monitor, '_flow_status', return_value=('SUCCESS', ['b' * 40])), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(2, self.monitor.check(self.config()))
            self.assertEqual(2, self.monitor.check(self.config()))
        mail.assert_called_once()
        subject, body = mail.call_args[0]
        self.assertIn('SHA不匹配', subject)
        self.assertIn('需主控核验', body)
        record = next(iter(self.state()['targets'].values()))['notices']['success_sha_mismatch']
        self.assertTrue(record['accepted'])
        self.assertEqual('unknown', record['receipt']['inbox_delivery'])

    def test_terminal_failure_retries_email_at_most_three_times(self):
        with mock.patch.object(self.monitor, '_flow_status', return_value=('FAIL', [])), \
             mock.patch.object(self.monitor, '_send_email', return_value=False) as mail:
            self.assertEqual(2, self.monitor.check(self.config()))
            self.assertEqual(2, self.monitor.check(self.config()))
            self.assertEqual(2, self.monitor.check(self.config()))
            self.assertEqual(2, self.monitor.check(self.config()))
        self.assertEqual(3, mail.call_count)
        record = next(iter(self.state()['targets'].values()))['notices']['terminal_fail']
        self.assertEqual(3, record['attempts'])
        self.assertFalse(record['accepted'])

    def test_timeout_alerts_only_after_three_consecutive_observation_errors(self):
        with mock.patch.object(self.monitor, '_flow_status', side_effect=self.monitor.ObservationError('flow_timeout')), \
             mock.patch.object(self.monitor, '_send_email', return_value=True) as mail:
            self.assertEqual(0, self.monitor.check(self.config()))
            self.assertEqual(0, self.monitor.check(self.config()))
            self.assertEqual(0, self.monitor.check(self.config()))
            self.assertEqual(0, self.monitor.check(self.config()))
        mail.assert_called_once()
        self.assertIn('flow_timeout', mail.call_args[0][1])

    def test_flow_subprocess_timeout_is_safely_classified(self):
        process = mock.Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired(['node'], 30), (b'', b'')]
        with mock.patch.object(self.monitor.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(self.monitor.ObservationError, 'flow_timeout'):
                self.monitor._flow_status(self.target)
        process.kill.assert_called_once()

    def test_flow_and_mail_commands_are_bounded_and_do_not_inherit_output(self):
        flow = mock.Mock(returncode=0)
        flow.communicate.return_value = (json.dumps({
            'org': self.monitor.FLOW_ORG, 'pipeline': '5260799', 'run': '20',
            'status': 'RUNNING', 'sources': [self.source(commits=[])]}).encode('utf-8'), b'untrusted')
        mail = mock.Mock(returncode=0)
        mail.communicate.return_value = (b'', b'')
        with mock.patch.object(self.monitor.subprocess, 'Popen', side_effect=[flow, mail]) as popen:
            self.assertEqual(('RUNNING', []), self.monitor._flow_status(self.target))
            self.assertTrue(self.monitor._send_email('safe-subject', 'safe-body'))
        self.assertEqual(['node', self.monitor.FLOW_COMMAND, 'status', '--org', self.monitor.FLOW_ORG,
                          '--pipeline', '5260799', '--run', '20', '--credentials-file',
                          self.monitor.CREDENTIALS_FILE], popen.call_args_list[0][0][0])
        self.assertEqual([self.monitor.MAIL_COMMAND, 'safe-subject', 'safe-body'], popen.call_args_list[1][0][0])
        self.assertEqual(self.monitor.FLOW_TIMEOUT_SECONDS, flow.communicate.call_args[1]['timeout'])

    def test_main_does_not_emit_flow_or_error_output(self):
        payload = json.dumps(self.config())
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.monitor, '_flow_status', side_effect=self.monitor.ObservationError('flow_output_invalid')), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(0, self.monitor.main(['--check', '--config', payload]))
        self.assertEqual('', stdout.getvalue())
        self.assertEqual('', stderr.getvalue())

    def test_mail_disabled_pauses_without_attempt_or_receipt_and_resumes_pending_notice(self):
        config = self.config()
        config['mail_enabled'] = False
        with mock.patch.object(self.monitor, '_flow_status', return_value=('FAIL', [])), \
             mock.patch.object(self.monitor, '_send_email') as mail:
            self.assertEqual(2, self.monitor.check(config))
            self.assertEqual(2, self.monitor.check(config))
        mail.assert_not_called()
        saved = self.state()
        target_state = next(iter(saved['targets'].values()))
        self.assertEqual({'reason': 'mail_disabled'}, saved['mail_paused'])
        self.assertNotIn('notices', target_state)
        self.assertEqual({'kind': 'status', 'status': 'FAIL', 'commits': []},
                         target_state['last_observation'])

        config['mail_enabled'] = True
        with mock.patch.object(self.monitor, '_flow_status', return_value=('FAIL', [])), \
             mock.patch.object(self.monitor, '_send_email', return_value=False) as mail:
            self.assertEqual(2, self.monitor.check(config))
        mail.assert_called_once()
        saved = self.state()
        self.assertNotIn('mail_paused', saved)
        record = next(iter(saved['targets'].values()))['notices']['terminal_fail']
        self.assertEqual(1, record['attempts'])
        self.assertFalse(record['accepted'])
        self.assertEqual({'accepted_by_mail_helper': False, 'inbox_delivery': 'unknown'},
                         record['receipt'])

    def test_mail_enabled_rejects_non_boolean_values(self):
        for value in (0, 1, 'false', None, [], {}):
            with self.subTest(value=value):
                config = self.config()
                config['mail_enabled'] = value
                with self.assertRaisesRegex(self.monitor.ConfigurationError, 'mail_enabled_invalid'):
                    self.monitor._validate_config(config)
                self.assertEqual(2, self.monitor.main(['--check', '--config', json.dumps(config)]))

    def test_mail_resume_uses_only_remaining_attempts_and_keeps_cap(self):
        record = {'attempts': 2, 'accepted': False,
                  'receipt': {'accepted_by_mail_helper': False, 'inbox_delivery': 'unknown'}}
        state = {'version': 1, 'targets': {self.monitor._target_key(self.target): {
            'last_observation': {'kind': 'status', 'status': 'FAIL', 'commits': []},
            'notices': {'terminal_fail': record}}}}
        self.path.write_text(json.dumps(state))
        paused = self.config()
        paused['mail_enabled'] = False
        with mock.patch.object(self.monitor, '_flow_status', return_value=('FAIL', [])), \
             mock.patch.object(self.monitor, '_send_email') as mail:
            self.assertEqual(2, self.monitor.check(paused))
        mail.assert_not_called()
        self.assertEqual(record, next(iter(self.state()['targets'].values()))['notices']['terminal_fail'])

        resumed = self.config()
        with mock.patch.object(self.monitor, '_flow_status', return_value=('FAIL', [])), \
             mock.patch.object(self.monitor, '_send_email', return_value=False) as mail:
            self.assertEqual(2, self.monitor.check(resumed))
            self.assertEqual(2, self.monitor.check(resumed))
        self.assertEqual(1, mail.call_count)
        saved_record = next(iter(self.state()['targets'].values()))['notices']['terminal_fail']
        self.assertEqual(3, saved_record['attempts'])
        self.assertEqual(record['receipt'], saved_record['receipt'])

    def test_multiple_targets_keep_error_notice_attempts_separate(self):
        second = dict(self.target, task_id='FLOW-SECOND', pipeline='5263690', run='21',
                      expected_commit='b' * 40)
        config = {'targets': [self.target, second], 'state': str(self.path)}
        with mock.patch.object(self.monitor, '_flow_status',
                               side_effect=[self.monitor.ObservationError('flow_timeout'),
                                            self.monitor.ObservationError('flow_output_invalid')] * 3), \
             mock.patch.object(self.monitor, '_send_email', return_value=False) as mail:
            self.assertEqual(0, self.monitor.check(config))
            self.assertEqual(0, self.monitor.check(config))
            self.assertEqual(2, self.monitor.check(config))
        self.assertEqual(2, mail.call_count)
        saved = self.state()['targets']
        self.assertEqual(1, saved[self.monitor._target_key(self.target)]['notices']
                         ['observation_error_flow_timeout']['attempts'])
        self.assertEqual(1, saved[self.monitor._target_key(second)]['notices']
                         ['observation_error_flow_output_invalid']['attempts'])

    def test_rejects_unapproved_pipeline_and_org(self):
        config = self.config()
        config['targets'][0]['pipeline'] = '1'
        self.assertEqual(2, self.monitor.main(['--check', '--config', json.dumps(config)]))
        config = self.config()
        config['org'] = 'other'
        self.assertEqual(2, self.monitor.main(['--check', '--config', json.dumps(config)]))


if __name__ == '__main__':
    unittest.main()
