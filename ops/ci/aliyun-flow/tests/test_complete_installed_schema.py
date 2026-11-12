"""Offline adversarial tests for same-installed-artifact schema completion."""
from __future__ import print_function

import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'ops/ci/aliyun-flow/auto/complete-installed-schema.py'
loader = importlib.machinery.SourceFileLoader('complete_installed_schema_test_module', str(SCRIPT))
completion = loader.load_module()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


FAKE_RUNNER = r'''#!/usr/bin/python3
from __future__ import print_function
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys

key = %r
root = Path(%r)
spec = json.loads((root / 'scenario.json').read_text())[key]
operation = 'apply' if sys.argv[1:] == ['--apply'] else 'plan'
if sys.argv[1:] not in ([], ['--apply']):
    raise SystemExit(23)
password_name = spec['passwordEnv']
password_ok = hashlib.sha256(os.environ.get(password_name, '').encode()).hexdigest() == spec['passwordSha256']
held = []
for raw in spec['wrapperLocks']:
    with Path(raw).open('r+') as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            held.append(True)
        else:
            held.append(False)
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
calls = root / 'calls.jsonl'
with calls.open('a') as stream:
    stream.write(json.dumps({
        'key': key, 'operation': operation, 'argv': sys.argv[1:],
        'envKeys': sorted(os.environ), 'passwordOk': password_ok,
        'wrapperLocksHeld': held,
    }, sort_keys=True) + '\n')
state_path = root / 'tables.json'
state = json.loads(state_path.read_text())
mode = spec.get('fail', {}).get(operation)
statuses = {}
for table in spec['tables']:
    if state.get(table):
        statuses[table] = {'status': 'existing_equivalent'}
    elif operation == 'plan':
        statuses[table] = {'status': 'planned_create'}
    else:
        statuses[table] = {'status': 'created_equivalent'}
if operation == 'apply':
    for table in spec['tables']:
        if not state.get(table):
            if mode == 'before_create':
                statuses[table] = {'status': 'create_backend_error_absent'}
                break
            state[table] = True
            if mode == 'after_first_create':
                statuses[table] = {'status': 'create_backend_error_equivalent'}
                break
    state_path.write_text(json.dumps(state, sort_keys=True))
status = 'failed' if mode else 'pass'
report = {
    'schema_version': 1,
    'operation': operation,
    'status': status,
    'transaction_model': 'mysql_ddl_autocommit_per_create_no_rollback_or_drop',
    'lock_order': spec['lockOrder'],
    'binding': spec['binding'],
    'candidate': spec['candidate'],
    'tables': statuses,
}
if mode:
    report['error'] = 'fixture_' + mode
if spec.get('candidateMismatch') and operation == spec.get('candidateMismatchOperation', 'plan'):
    report['candidate']['sql_sha256'] = '0' * 64
if spec.get('passWithFailureExit') and operation == spec.get('passWithFailureExitOperation', 'plan'):
    status = 'pass'
    report['status'] = 'pass'
    print(json.dumps(report, sort_keys=True, separators=(',', ':')))
    raise SystemExit(9)
print(json.dumps(report, sort_keys=True, separators=(',', ':')))
raise SystemExit(1 if mode else 0)
'''


class CompleteInstalledSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-schema-completion-', dir='/tmp')
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.uid = os.geteuid()
        self.gid = os.getegid()
        self.original_api = copy.deepcopy(completion.API_BINDING)
        self.original_runners = copy.deepcopy(completion.RUNNERS)

        self.runtime = completion.Runtime(self.uid, self.gid)
        self.runtime.production = False
        self.runtime.protected_directories = ()
        self.runtime.bundle_uid = self.uid
        self.runtime.runner_gid = self.gid
        self.runtime.destination = self.mkdir('installed', 0o700)
        self.runtime.state_root = self.mkdir('state', 0o700)
        self.runtime.record = self.runtime.state_root / 'record.json'
        self.runtime.jar = self.root / 'service/cyf-api-kit.jar'
        self.runtime.jar.parent.mkdir(mode=0o700)
        self.runtime.coordination_lock = self.file('coord.lock', b'', 0o600)
        self.runtime.release_lock = self.file('release.lock', b'', 0o600)
        self.runtime.curl = self.file(
            'curl', b'#!/usr/bin/python3\nimport json\nprint(json.dumps({"apiVersion":"V3","status":{"code":"UP"}}))\n',
            0o755)
        self.runtime.health_url = 'http://fixture.invalid/actuator/health'
        self.runtime.jar_mode = 0o600
        self.runtime.runner_mode = 0o755
        self.runtime.state_mode = 0o700

        self.bundle = self.mkdir('bundle', 0o700)
        candidate_root = self.bundle
        for part in ('ops', 'ci', 'aliyun-flow', 'host'):
            candidate_root = candidate_root / part
            candidate_root.mkdir(mode=0o700)
        self.candidate_root = candidate_root
        self.fixture = self.mkdir('runner-fixture', 0o700)
        self.secret = {
            'f06': 'f06-offline-secret-never-report',
            'e05': 'e05-offline-secret-never-report',
        }
        self.tables = {
            'agent_task_artifact_outcome': True,
            'agent_task_artifact_outcome_decision': False,
            'agent_work_item_reassignment': False,
        }
        (self.fixture / 'tables.json').write_text(json.dumps(self.tables, sort_keys=True))
        self.before = {}
        self.candidate = {}
        for key in completion.RUNNER_ORDER:
            name = completion.RUNNERS[key]['name']
            before = ('#!/bin/sh\n# old %s\nexit 99\n' % key).encode('utf-8')
            self.file_at(self.runtime.destination / name, before, 0o755)
            self.before[key] = digest(before)
            candidate = (FAKE_RUNNER % (key, str(self.fixture))).encode('utf-8')
            self.file_at(self.candidate_root / name, candidate, 0o755)
            self.candidate[key] = digest(candidate)
            completion.RUNNERS[key]['candidateSha256'] = self.candidate[key]
            self.file_at(self.runtime.state_root / completion.RUNNERS[key]['passwordFile'],
                         self.secret[key].encode('utf-8'), 0o600)

        jar = b'fixed-offline-api49-jar'
        self.file_at(self.runtime.jar, jar, 0o600)
        completion.API_BINDING.update({
            'pipelineId': '5260799', 'runId': '49',
            'sourceCommitSha': '4' * 40, 'sourceTreeSha': '5' * 40,
            'jarSha256': digest(jar), 'receiptSha256': '7' * 64,
        })
        record = {
            'schema_version': 2, 'status': 'installed', 'phase': 'installed',
            'recovery': 'not_required', 'ticket_sha256': '8' * 64,
            'source_commit_sha': completion.API_BINDING['sourceCommitSha'],
            'source_tree_sha': completion.API_BINDING['sourceTreeSha'],
            'run_id': completion.API_BINDING['runId'],
            'receipt_sha256': completion.API_BINDING['receiptSha256'],
            'candidate_sha256': completion.API_BINDING['jarSha256'],
            'previous_sha256': '9' * 64,
            'backup': str(self.runtime.state_root / (
                'backups/20260913T000000Z-%s-123.jar' % completion.API_BINDING['jarSha256'])),
            'candidate_stop_rc': 0, 'timestamp': '20260913T000000Z',
        }
        self.file_at(self.runtime.record, encoded(record), 0o600)
        self.ops_run = '731'
        self.env = {'PIPELINE_ID': '5264702', 'BUILD_NUMBER': self.ops_run}
        self.scenario = {}
        for key in completion.RUNNER_ORDER:
            spec = completion.RUNNERS[key]
            self.scenario[key] = {
                'passwordEnv': spec['passwordEnv'],
                'passwordSha256': digest(self.secret[key].encode('utf-8')),
                'wrapperLocks': [str(self.runtime.coordination_lock),
                                 str(self.runtime.release_lock)],
                'tables': spec['tables'], 'lockOrder': spec['lockOrder'],
                'binding': completion.expected_binding(),
                'candidate': {
                    'resource_outer': 'BOOT-INF/lib/jia-agent-mapper-1.1.2-SNAPSHOT.jar',
                    'resource_inner': spec['resourceInner'],
                    'sql_sha256': spec['sqlSha256'],
                    'tables': spec['tables'],
                    'statement_policy': 'exact_create_table_if_not_exists_only',
                },
                'fail': {},
            }
        self.write_scenario()

    def tearDown(self):
        completion.API_BINDING.clear()
        completion.API_BINDING.update(self.original_api)
        completion.RUNNERS.clear()
        completion.RUNNERS.update(self.original_runners)
        self.tmp.cleanup()

    def mkdir(self, relative, mode):
        path = self.root / relative
        path.mkdir(mode=mode)
        return path

    def file(self, relative, data, mode):
        path = self.root / relative
        self.file_at(path, data, mode)
        return path

    def file_at(self, path, data, mode):
        path.write_bytes(data)
        path.chmod(mode)
        os.chown(str(path), self.uid, self.gid)

    def write_scenario(self):
        path = self.fixture / 'scenario.json'
        path.write_text(json.dumps(self.scenario, sort_keys=True))
        path.chmod(0o600)

    def write_manifest(self, action='verify', changes=None):
        value = {
            'schemaVersion': 1, 'action': action,
            'opsFlow': {'pipelineId': '5264702', 'runId': self.ops_run},
            'installedApi': copy.deepcopy(completion.API_BINDING),
            'runners': {
                key: {'beforeSha256': self.before[key],
                      'candidateSha256': self.candidate[key]}
                for key in completion.RUNNER_ORDER
            },
        }
        if changes:
            changes(value)
        path = self.bundle / completion.MANIFEST_NAME
        if path.exists():
            path.unlink()
        self.file_at(path, encoded(value), 0o600)
        return value

    def calls(self):
        path = self.fixture / 'calls.jsonl'
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def table_state(self):
        return json.loads((self.fixture / 'tables.json').read_text())

    def reports(self):
        root = self.runtime.state_root / 'schema-completion/operations-reports'
        values = []
        if root.exists():
            for path in root.iterdir():
                values.extend(json.loads(line) for line in path.read_text().splitlines())
        return values

    def run_action(self, action):
        self.write_manifest(action)
        return completion.execute(action, self.bundle, self.env, self.runtime)

    def assert_no_apply(self):
        self.assertFalse(any(value['operation'] == 'apply' for value in self.calls()))

    def test_verify_installs_exact_candidates_and_plans_both_with_partial_f06_present(self):
        result = self.run_action('verify')
        self.assertEqual(result['status'], 'pass')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()],
                         [('f06', 'plan'), ('e05', 'plan')])
        self.assert_no_apply()
        self.assertEqual(result['plans']['f06']['tables']['agent_task_artifact_outcome']['status'],
                         'existing_equivalent')
        self.assertEqual(result['plans']['f06']['tables']['agent_task_artifact_outcome_decision']['status'],
                         'planned_create')
        for key in completion.RUNNER_ORDER:
            installed = self.runtime.destination / completion.RUNNERS[key]['name']
            self.assertEqual(digest(installed.read_bytes()), self.candidate[key])
        backups = list((self.runtime.state_root / 'schema-completion/tooling-backups').glob('*/*.before'))
        self.assertEqual(len(backups), 2)
        self.assertFalse(result['applicationLifecycleInvoked'])
        self.assertFalse(result['businessCompletionClaimed'])

    def test_large_jar_binding_uses_streaming_digest_not_payload_read(self):
        observed = []
        real_read = completion.read_stable

        def observed_read(path, *args, **kwargs):
            observed.append(Path(path))
            return real_read(path, *args, **kwargs)

        with mock.patch.object(completion, 'read_stable', side_effect=observed_read):
            value = completion.validate_record_and_jar(self.runtime)
        self.assertEqual(value['jarSignature'][2], self.runtime.jar.stat().st_size)
        self.assertIn(self.runtime.record, observed)
        self.assertNotIn(self.runtime.jar, observed)

    def test_installed_artifact_mismatch_fails_before_runner_install_or_attempt(self):
        record = json.loads(self.runtime.record.read_text())
        record['candidate_sha256'] = '0' * 64
        self.runtime.record.write_bytes(encoded(record))
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'installed_record_binding_mismatch')
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.runtime.state_root / 'schema-completion').exists())
        for key in completion.RUNNER_ORDER:
            installed = self.runtime.destination / completion.RUNNERS[key]['name']
            self.assertEqual(digest(installed.read_bytes()), self.before[key])

    def test_symlinked_bundle_path_is_rejected_before_persistence(self):
        self.write_manifest('complete')
        linked = self.root / 'linked-bundle'
        linked.symlink_to(self.bundle, target_is_directory=True)
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', linked, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'bundle_path_invalid')
        self.assertFalse((self.runtime.state_root / 'schema-completion').exists())
        self.assertEqual(self.calls(), [])

    def test_candidate_digest_or_path_substitution_fails_before_persistence(self):
        candidate = self.candidate_root / completion.RUNNERS['f06']['name']
        candidate.write_bytes(candidate.read_bytes() + b'\n# tampered')
        candidate.chmod(0o755)
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'candidate_digest_mismatch')
        self.assertFalse((self.runtime.state_root / 'schema-completion').exists())
        self.assertEqual(self.calls(), [])

    def test_first_plan_failure_prohibits_every_apply(self):
        self.scenario['f06']['fail']['plan'] = 'metadata_mismatch'
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'f06_plan_failed')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()], [('f06', 'plan')])
        self.assert_no_apply()
        self.assertEqual(self.table_state(), self.tables)

    def test_second_plan_failure_prohibits_every_apply(self):
        self.scenario['e05']['fail']['plan'] = 'metadata_mismatch'
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'e05_plan_failed')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()],
                         [('f06', 'plan'), ('e05', 'plan')])
        self.assert_no_apply()
        self.assertEqual(self.table_state(), self.tables)

    def test_complete_preserves_partial_first_table_and_orders_f06_before_e05(self):
        result = self.run_action('complete')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()], [
            ('f06', 'plan'), ('e05', 'plan'), ('f06', 'apply'), ('e05', 'apply')])
        self.assertEqual(self.table_state(), {
            'agent_task_artifact_outcome': True,
            'agent_task_artifact_outcome_decision': True,
            'agent_work_item_reassignment': True,
        })
        self.assertEqual(
            result['applies']['f06']['tables']['agent_task_artifact_outcome']['status'],
            'existing_equivalent')
        for call in self.calls():
            expected = completion.RUNNERS[call['key']]['passwordEnv']
            self.assertEqual(call['envKeys'], sorted(['LC_ALL', 'PATH', expected]))
            self.assertTrue(call['passwordOk'])
            self.assertEqual(call['wrapperLocksHeld'], [True, True])

    def test_first_apply_partial_create_is_retained_and_e05_is_not_applied(self):
        self.scenario['f06']['fail']['apply'] = 'after_first_create'
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'f06_apply_failed')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()], [
            ('f06', 'plan'), ('e05', 'plan'), ('f06', 'apply')])
        state = self.table_state()
        self.assertTrue(state['agent_task_artifact_outcome'])
        self.assertTrue(state['agent_task_artifact_outcome_decision'])
        self.assertFalse(state['agent_work_item_reassignment'])
        failed = [event for event in self.reports()
                  if event.get('runner') == 'f06' and event.get('operation') == 'apply'][-1]
        self.assertEqual(failed['runnerReport']['status'], 'failed')
        self.assertEqual(
            failed['runnerReport']['tables']['agent_task_artifact_outcome_decision']['status'],
            'create_backend_error_equivalent')

    def test_second_apply_failure_preserves_successful_f06_and_never_rolls_back(self):
        self.scenario['e05']['fail']['apply'] = 'before_create'
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'e05_apply_failed')
        self.assertEqual([(c['key'], c['operation']) for c in self.calls()], [
            ('f06', 'plan'), ('e05', 'plan'), ('f06', 'apply'), ('e05', 'apply')])
        state = self.table_state()
        self.assertTrue(state['agent_task_artifact_outcome'])
        self.assertTrue(state['agent_task_artifact_outcome_decision'])
        self.assertFalse(state['agent_work_item_reassignment'])
        retained = [event for event in self.reports()
                    if event.get('runner') == 'f06' and event.get('operation') == 'apply']
        self.assertEqual(retained[-1]['runnerReport']['status'], 'pass')
        self.assertFalse(any(event.get('event') == 'rollback'
                             for event in self.reports()))
        self.assertFalse(any(event.get('disposition', '').startswith('restored')
                             for event in self.reports()))

    def test_verify_then_fresh_complete_reuses_immutable_original_backups(self):
        verified = self.run_action('verify')
        self.assertEqual(verified['status'], 'pass')
        self.ops_run = '732'
        self.env['BUILD_NUMBER'] = self.ops_run
        completed = self.run_action('complete')
        self.assertEqual(completed['status'], 'pass')
        installed_events = [event for event in self.reports()
                            if event.get('event') == 'runner_installed']
        dispositions = [event['disposition'] for event in installed_events]
        self.assertEqual(dispositions.count('installed_candidate'), 2)
        self.assertEqual(dispositions.count('candidate_already_installed'), 2)
        backups = list((self.runtime.state_root /
                        'schema-completion/tooling-backups').glob('*/*.before'))
        self.assertEqual(len(backups), 2)

    def test_complete_attempt_is_one_shot_even_after_failure(self):
        self.scenario['e05']['fail']['apply'] = 'before_create'
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError):
            completion.execute('complete', self.bundle, self.env, self.runtime)
        first_calls = list(self.calls())
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertIn(caught.exception.code,
                      ('operation_report_exists', 'complete_attempt_already_exists'))
        self.assertEqual(self.calls(), first_calls)
        markers = list((self.runtime.state_root / 'schema-completion/attempt-markers').iterdir())
        self.assertEqual(len(markers), 1)

    def test_report_candidate_mismatch_is_fail_closed_before_apply(self):
        self.scenario['f06']['candidateMismatch'] = True
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'runner_report_candidate_invalid')
        self.assert_no_apply()

    def test_false_pass_text_cannot_override_failing_exit(self):
        self.scenario['f06']['passWithFailureExit'] = True
        self.write_scenario()
        self.write_manifest('complete')
        with self.assertRaises(completion.CompletionError) as caught:
            completion.execute('complete', self.bundle, self.env, self.runtime)
        self.assertEqual(caught.exception.code, 'runner_exit_status_disagrees_with_report')
        self.assert_no_apply()

    def test_no_lifecycle_command_and_secrets_never_enter_operations_results(self):
        commands = []
        real_run = completion.subprocess.run

        def observed_run(argv, *args, **kwargs):
            commands.append(list(argv))
            return real_run(argv, *args, **kwargs)

        with mock.patch.object(completion.subprocess, 'run', side_effect=observed_run):
            result = self.run_action('complete')
        invoked = [Path(argv[0]).name for argv in commands]
        self.assertEqual(invoked, [
            'curl', 'curl', 'cyf-api-additive-schema',
            'cyf-api-e05-additive-schema', 'curl',
            'cyf-api-additive-schema', 'cyf-api-e05-additive-schema'])
        serialized = json.dumps(result, sort_keys=True)
        report_root = self.runtime.state_root / 'schema-completion'
        serialized += ''.join(path.read_text(errors='replace')
                              for path in report_root.rglob('*') if path.is_file())
        for secret in self.secret.values():
            self.assertNotIn(secret, serialized)
        self.assertNotIn('systemctl', serialized)
        self.assertNotIn('cyf-api-kit start', serialized)
        self.assertFalse(result['applicationRestarted'])
        self.assertFalse(result['applicationArtifactOrInstalledRecordChanged'])
        self.assertFalse(result['featureFlagsChanged'])


if __name__ == '__main__':
    unittest.main()
