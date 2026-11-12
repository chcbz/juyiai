"""Offline-only E05 post-install hook tests; never touch F06 globals or MySQL.

Admission is fixed-SQL permission for an already-created, source-verified Run.
The controller verifies source/tree and the required ancestor before authorizing;
the original deploy chain verifies successful same-run cloud test/build receipt,
JAR and healthy installation before this hook. Final Flow SUCCESS is an outcome,
not a permission field, prerequisite or synthetic receipt. No CI-only rebuild.
"""
import contextlib
import fcntl
import grp
import hashlib
import importlib.machinery
import inspect
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
DEPLOY = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-flow-deploy'
loader = importlib.machinery.SourceFileLoader('cyf_api_flow_deploy_e05_test', str(DEPLOY))
deploy = loader.load_module()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


class ApiFlowDeployE05Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-api-flow-deploy-e05-', dir='/tmp')
        self.base = Path(self.tmp.name)
        self.base.chmod(0o700)
        self.state = self.base / 'state'
        self.state.mkdir(mode=0o700)
        self.bin = self.base / 'bin'
        self.bin.mkdir(mode=0o700)
        self.release_lock = self.base / 'cyf-release-api.lock'
        self.release_lock.touch(mode=0o660)
        os.chown(self.release_lock, 0, grp.getgrnam('isp').gr_gid)
        self.release_lock.chmod(0o660)
        self.runner = self.bin / 'cyf-api-e05-additive-schema'
        self.calls = self.base / 'runner-calls'
        self.observed = self.base / 'runner-observed.json'
        self.context = {
            'pipeline_id': '5260799',
            'run_id': '46',
            'source_commit_sha': '5' * 40,
            'source_tree_sha': '6' * 40,
            'receipt_sha256': '7' * 64,
            'jar_sha256': '8' * 64,
        }
        self.previous = {
            'E05_SCHEMA_RUNNER': deploy.E05_SCHEMA_RUNNER,
            'E05_SCHEMA_RESULTS': deploy.E05_SCHEMA_RESULTS,
            'E05_SCHEMA_STATE_ROOT': deploy.E05_SCHEMA_STATE_ROOT,
            'E05_SCHEMA_RECORD': deploy.E05_SCHEMA_RECORD,
            'E05_SCHEMA_ACTIVATION_FILE': deploy.E05_SCHEMA_ACTIVATION_FILE,
            'E05_SCHEMA_PASSWORD_FILE': deploy.E05_SCHEMA_PASSWORD_FILE,
            'E05_RELEASE_LOCK': deploy.E05_RELEASE_LOCK,
            'E05_SCHEMA_RUNNER_SHA256': deploy.E05_SCHEMA_RUNNER_SHA256,
        }
        deploy.E05_SCHEMA_RUNNER = self.runner
        deploy.E05_SCHEMA_RESULTS = self.state / 'e05-schema-results'
        deploy.E05_SCHEMA_STATE_ROOT = self.state
        deploy.E05_SCHEMA_RECORD = self.state / 'record.json'
        deploy.E05_SCHEMA_ACTIVATION_FILE = self.state / 'e05-schema-activation.json'
        deploy.E05_SCHEMA_PASSWORD_FILE = self.state / 'e05-schema-password'
        deploy.E05_RELEASE_LOCK = self.release_lock
        self.old_e05_env = os.environ.get(deploy.E05_SCHEMA_PASSWORD_ENV)
        os.environ[deploy.E05_SCHEMA_PASSWORD_ENV] = 'attacker-inherited-secret'
        self.write_record()
        deploy.E05_SCHEMA_PASSWORD_FILE.write_text('offline-file-secret')
        deploy.E05_SCHEMA_PASSWORD_FILE.chmod(0o600)
        self.write_runner(self.report('pass'), 0)
        deploy.E05_SCHEMA_RUNNER_SHA256 = hashlib.sha256(self.runner.read_bytes()).hexdigest()
        self.write_activation()

    def tearDown(self):
        for name, value in self.previous.items():
            setattr(deploy, name, value)
        if self.old_e05_env is None:
            os.environ.pop(deploy.E05_SCHEMA_PASSWORD_ENV, None)
        else:
            os.environ[deploy.E05_SCHEMA_PASSWORD_ENV] = self.old_e05_env
        self.tmp.cleanup()

    def report(self, status, error=None, table_status='created_equivalent', binding=True,
               candidate=True, failed_table=False):
        value = {
            'schema_version': 1,
            'operation': 'apply',
            'status': status,
            'transaction_model': 'mysql_ddl_autocommit_per_create_no_rollback_or_drop',
            'lock_order': ['e05_runner_file_lock', 'e05_mysql_named_lock'],
            'tables': {
                'agent_work_item_reassignment': {'status': table_status},
            },
        }
        if binding:
            value['binding'] = {
                'organization': '5fb7d76ee6f9d07f148529c7',
                'pipeline': self.context['pipeline_id'],
                'run': self.context['run_id'],
                'source_commit': self.context['source_commit_sha'],
                'source_tree': self.context['source_tree_sha'],
                'jar_sha256': self.context['jar_sha256'],
                'receipt_sha256': self.context['receipt_sha256'],
            }
        if candidate:
            value['candidate'] = {
                'resource_outer': 'BOOT-INF/lib/jia-agent-mapper-1.1.2-SNAPSHOT.jar',
                'resource_inner': 'db/agent-work-item-reassignment-e05.sql',
                'sql_sha256': deploy.E05_SCHEMA_SQL_SHA256,
                'tables': ['agent_work_item_reassignment'],
                'statement_policy': 'exact_create_table_if_not_exists_only',
            }
        if error is not None:
            value['error'] = error
        if failed_table:
            value['failed_table'] = 'agent_work_item_reassignment'
        return value

    def write_record(self, **changes):
        value = {
            'schema_version': 2,
            'status': 'installed',
            'phase': 'installed',
            'recovery': 'not_required',
            'ticket_sha256': '9' * 64,
            'source_commit_sha': self.context['source_commit_sha'],
            'source_tree_sha': self.context['source_tree_sha'],
            'run_id': self.context['run_id'],
            'receipt_sha256': self.context['receipt_sha256'],
            'candidate_sha256': self.context['jar_sha256'],
            'previous_sha256': 'a' * 64,
            'backup': str(self.state / 'backups/fixture.jar'),
            'candidate_stop_rc': 0,
            'timestamp': '20260913T000000Z',
        }
        value.update(changes)
        deploy.E05_SCHEMA_RECORD.write_bytes(encoded(value))
        deploy.E05_SCHEMA_RECORD.chmod(0o600)

    def activation(self, **changes):
        value = {
            'schema_version': 1,
            'feature': 'M4-E05-additive-schema',
            'status': 'enabled_once',
            'authorization': deploy.E05_ACTIVATION_AUTHORIZATION,
            'pipeline_id': self.context['pipeline_id'],
            'run_id': self.context['run_id'],
            'source_commit_sha': self.context['source_commit_sha'],
            'source_tree_sha': self.context['source_tree_sha'],
            'verified_api_ancestor_sha': deploy.E05_REQUIRED_API_COMMIT_SHA,
            'sql_sha256': deploy.E05_SCHEMA_SQL_SHA256,
            'runner_sha256': deploy.E05_SCHEMA_RUNNER_SHA256,
        }
        value.update(changes)
        return value

    def write_activation(self, **changes):
        deploy.E05_SCHEMA_ACTIVATION_FILE.write_bytes(encoded(self.activation(**changes)))
        deploy.E05_SCHEMA_ACTIVATION_FILE.chmod(0o600)

    def write_runner(self, report, return_code, stderr=''):
        script = '''#!/usr/bin/python3
import fcntl, json, os
from pathlib import Path
lock = Path(%r)
calls = Path(%r)
observed = Path(%r)
count = int(calls.read_text()) + 1 if calls.exists() else 1
calls.write_text(str(count))
with lock.open('r+') as stream:
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        release_lock_held = True
    else:
        release_lock_held = False
observed.write_text(json.dumps({
    'argv': __import__('sys').argv[1:],
    'env': dict(os.environ),
    'release_lock_held': release_lock_held,
}, sort_keys=True))
print(%r)
if %r:
    print(%r, file=__import__('sys').stderr)
raise SystemExit(%d)
''' % (str(self.release_lock), str(self.calls), str(self.observed),
       json.dumps(report, sort_keys=True, separators=(',', ':')), bool(stderr), stderr,
       return_code)
        self.runner.write_text(script)
        self.runner.chmod(0o755)

    def result(self):
        return json.loads((deploy.E05_SCHEMA_RESULTS / 'run-46.json').read_text())

    def admitted(self):
        value = deploy.load_e05_activation(self.context)
        self.assertEqual(value['status'], 'admitted')
        return value

    def test_exact_admission_runs_apply_once_under_release_lock_with_child_only_secret(self):
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        result = self.result()
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['activation_claim'], 'schema_only_not_feature_activation')
        self.assertEqual(result['verified_api_ancestor_sha'], deploy.E05_REQUIRED_API_COMMIT_SHA)
        self.assertEqual(result['runner_report']['binding']['jar_sha256'], self.context['jar_sha256'])
        self.assertEqual(self.calls.read_text(), '1')
        observed = json.loads(self.observed.read_text())
        self.assertTrue(observed['release_lock_held'])
        self.assertEqual(observed['argv'], ['--apply'])
        self.assertEqual(sorted(observed['env']), ['CYF_E05_MYSQL_PASSWORD', 'LC_ALL', 'PATH'])
        self.assertEqual(observed['env'][deploy.E05_SCHEMA_PASSWORD_ENV], 'offline-file-secret')
        evidence = ''.join(path.read_text(errors='replace')
                           for path in deploy.E05_SCHEMA_RESULTS.iterdir())
        self.assertNotIn('offline-file-secret', evidence)
        self.assertNotIn('attacker-inherited-secret', evidence)
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        self.assertEqual(self.calls.read_text(), '1')
        result_dir = deploy.E05_SCHEMA_RESULTS.stat()
        self.assertEqual(result_dir.st_mode & 0o777, 0o700)
        self.assertEqual((result_dir.st_uid, result_dir.st_gid), (0, 0))
        for path in deploy.E05_SCHEMA_RESULTS.iterdir():
            info = path.stat()
            self.assertEqual(info.st_mode & 0o777, 0o600)
            self.assertEqual((info.st_uid, info.st_gid), (0, 0))

    def test_partial_autocommit_failure_is_preserved_and_same_run_never_retries(self):
        self.write_runner(
            self.report('failed', 'create_statement_failed',
                        table_status='create_backend_error_equivalent', failed_table=True),
            9, stderr='fixture create returned an error after durable CREATE')
        deploy.E05_SCHEMA_RUNNER_SHA256 = hashlib.sha256(self.runner.read_bytes()).hexdigest()
        self.write_activation()
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 9)
        first = self.result()
        self.assertEqual(first['status'], 'failed')
        self.assertEqual(first['runner_exit_code'], 9)
        self.assertEqual(first['runner_report']['tables']['agent_work_item_reassignment']['status'],
                         'create_backend_error_equivalent')
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 9)
        self.assertEqual(self.calls.read_text(), '1')
        self.assertEqual(self.result(), first)

    def test_interrupted_running_state_is_not_retried(self):
        deploy.ensure_e05_results_directory()
        running = deploy.e05_schema_state(
            self.context, 'running', '2026-09-13T00:00:00.000000Z',
            activation_sha256=self.admitted()['sha256'],
            action='inspect durable metadata; do not rerun')
        deploy.write_e05_schema_state(
            deploy.e05_schema_paths('46')['state'], running, create=True)
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.result()['status'], 'running')

    def test_admitted_attempt_is_durable_before_release_lock_acquisition(self):
        original = deploy.acquire_e05_release_lock
        observed = []

        def stop_at_lock(path):
            observed.append(self.result()['status'])
            raise deploy.SchemaIntegrationError('offline_stop_at_release_lock', 'fixture stop')

        deploy.acquire_e05_release_lock = stop_at_lock
        try:
            self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        finally:
            deploy.acquire_e05_release_lock = original
        self.assertEqual(observed, ['running'])
        self.assertEqual(self.result()['error'], 'offline_stop_at_release_lock')
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())

    def test_missing_or_stale_exact_run_admission_never_invokes_runner(self):
        deploy.E05_SCHEMA_ACTIVATION_FILE.unlink()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        self.assertIn('root_only_exact_run_activation_missing', output.getvalue())
        self.assertFalse(self.calls.exists())
        self.assertFalse(deploy.E05_SCHEMA_RESULTS.exists())
        self.write_activation(run_id='45')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        self.assertIn('activation_is_for_a_different_exact_release', output.getvalue())
        self.assertFalse(self.calls.exists())
        self.write_activation(source_commit_sha='0' * 40)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        self.assertFalse(self.calls.exists())

    def test_fixed_sql_permission_admits_without_final_flow_success_claim(self):
        self.write_activation(
            authorization='controller_authorized_fixed_additive_sql_exact_run_once')
        admission = self.admitted()
        self.assertEqual(set(admission['value']), {
            'schema_version', 'feature', 'status', 'authorization', 'pipeline_id',
            'run_id', 'source_commit_sha', 'source_tree_sha',
            'verified_api_ancestor_sha', 'sql_sha256', 'runner_sha256',
        })
        self.assertFalse(self.calls.exists())  # Permission itself performs no DDL.
        self.assertFalse(deploy.E05_SCHEMA_RESULTS.exists())
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 0)
        self.assertEqual(self.result()['activation_claim'], 'schema_only_not_feature_activation')
        self.assertEqual(self.calls.read_text(), '1')

    def test_final_flow_success_claim_is_not_an_authorization_or_required_field(self):
        for changes in (
                {'authorization': 'controller_verified_cloud_success_exact_source_once'},
                {'flow_status': 'SUCCESS'}):
            with self.subTest(changes=changes):
                self.write_activation(**changes)
                with self.assertRaises(deploy.SchemaIntegrationError) as caught:
                    deploy.maybe_apply_e05_schema_after_install(self.context)
                self.assertEqual(caught.exception.code, 'e05_activation_contract_invalid')
                self.assertFalse(self.calls.exists())
                self.assertFalse(deploy.E05_SCHEMA_RESULTS.exists())

    def test_admission_does_not_replace_same_run_healthy_installed_record(self):
        self.write_record(status='failed', phase='rolling_back', recovery='restored_healthy')
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertEqual(self.result()['error'], 'same_run_installed_record_missing')
        self.assertFalse(self.calls.exists())  # A healthy restored OLD API is insufficient.

    def test_activation_is_root_only_exact_and_requires_corrected_api_proof_field(self):
        self.write_activation(verified_api_ancestor_sha='0' * 40)
        with self.assertRaises(deploy.SchemaIntegrationError) as caught:
            deploy.maybe_apply_e05_schema_after_install(self.context)
        self.assertEqual(caught.exception.code, 'e05_activation_contract_invalid')
        self.assertFalse(self.calls.exists())
        source = self.base / 'activation-source'
        source.write_bytes(encoded(self.activation()))
        source.chmod(0o600)
        deploy.E05_SCHEMA_ACTIVATION_FILE.unlink()
        deploy.E05_SCHEMA_ACTIVATION_FILE.symlink_to(source)
        with self.assertRaises(deploy.SchemaIntegrationError) as caught:
            deploy.maybe_apply_e05_schema_after_install(self.context)
        self.assertEqual(caught.exception.code, 'e05_activation_metadata_unsafe')
        self.assertFalse(self.calls.exists())

    def test_wrong_same_run_installed_record_fails_durably_before_runner(self):
        self.write_record(source_tree_sha='0' * 40)
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.result()['error'], 'same_run_installed_record_mismatch')
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())

    def test_password_requires_root_root_0600_regular_single_link_parent_0700(self):
        source = self.base / 'secret-source'
        source.write_text('file-secret')
        source.chmod(0o600)
        deploy.E05_SCHEMA_PASSWORD_FILE.unlink()
        deploy.E05_SCHEMA_PASSWORD_FILE.symlink_to(source)
        missing, password = deploy.e05_schema_prerequisites()
        self.assertIn('e05_schema_password_metadata_unsafe', missing)
        self.assertIsNone(password)
        deploy.E05_SCHEMA_PASSWORD_FILE.unlink()
        os.link(str(source), str(deploy.E05_SCHEMA_PASSWORD_FILE))
        missing, _ = deploy.e05_schema_prerequisites()
        self.assertIn('e05_schema_password_metadata_unsafe', missing)
        deploy.E05_SCHEMA_PASSWORD_FILE.unlink()
        deploy.E05_SCHEMA_PASSWORD_FILE.write_text('file-secret')
        deploy.E05_SCHEMA_PASSWORD_FILE.chmod(0o644)
        missing, _ = deploy.e05_schema_prerequisites()
        self.assertIn('e05_schema_password_metadata_unsafe', missing)
        deploy.E05_SCHEMA_PASSWORD_FILE.chmod(0o600)
        self.state.chmod(0o755)
        missing, _ = deploy.e05_schema_prerequisites()
        self.assertIn('e05_state_root_unsafe', missing)

    def test_results_directory_requires_root_root_0700(self):
        deploy.E05_SCHEMA_RESULTS.mkdir(mode=0o700)
        os.chown(deploy.E05_SCHEMA_RESULTS, 0, grp.getgrnam('isp').gr_gid)
        with self.assertRaises(deploy.SchemaIntegrationError) as caught:
            deploy.apply_e05_schema_after_install(self.context, self.admitted())
        self.assertEqual(caught.exception.code, 'e05_schema_result_directory_unsafe')
        self.assertFalse(self.calls.exists())

    def test_runner_digest_mismatch_is_actionable_and_never_executes(self):
        deploy.E05_SCHEMA_RUNNER_SHA256 = '0' * 64
        self.write_activation(runner_sha256='0' * 64)
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())
        result = self.result()
        self.assertEqual(result['status'], 'blocked_precondition')
        self.assertIn('e05_schema_runner_digest_mismatch', result['prerequisites'])

    def test_missing_fixed_resource_candidate_cannot_be_reported_as_success(self):
        self.write_runner(self.report('pass', candidate=False), 0)
        deploy.E05_SCHEMA_RUNNER_SHA256 = hashlib.sha256(self.runner.read_bytes()).hexdigest()
        self.write_activation()
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertEqual(self.result()['error'], 'e05_schema_runner_false_success')
        self.assertEqual(self.calls.read_text(), '1')
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertEqual(self.calls.read_text(), '1')

    def test_runner_binding_mismatch_is_fail_closed_and_preserved(self):
        report = self.report('pass')
        report['binding']['source_commit'] = '0' * 40
        self.write_runner(report, 0)
        deploy.E05_SCHEMA_RUNNER_SHA256 = hashlib.sha256(self.runner.read_bytes()).hexdigest()
        self.write_activation()
        self.assertEqual(deploy.maybe_apply_e05_schema_after_install(self.context), 1)
        self.assertEqual(self.result()['error'], 'e05_schema_runner_binding_mismatch')
        self.assertEqual(self.calls.read_text(), '1')

    def test_changed_activation_after_admission_stops_before_apply_and_is_not_retried(self):
        admission = self.admitted()
        self.write_activation(authorization='revoked_after_admission')
        self.assertEqual(deploy.apply_e05_schema_after_install(self.context, admission), 1)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.result()['error'], 'e05_activation_changed')
        self.assertEqual(deploy.apply_e05_schema_after_install(self.context, admission), 1)
        self.assertFalse(self.calls.exists())

    def test_installer_and_its_jvm_descendants_receive_neither_schema_secret(self):
        old_f06 = os.environ.get(deploy.SCHEMA_PASSWORD_ENV)
        os.environ[deploy.SCHEMA_PASSWORD_ENV] = 'f06-secret'
        observed = self.base / 'installer-environment.json'
        installer = self.bin / 'failed-installer'
        installer.write_text(
            '#!/usr/bin/python3\nimport json, os\nfrom pathlib import Path\n'
            + 'Path(%r).write_text(json.dumps(sorted(os.environ)))\nraise SystemExit(7)\n'
            % str(observed))
        installer.chmod(0o755)
        try:
            self.assertEqual(deploy.invoke_installer(str(installer)), 7)
        finally:
            if old_f06 is None:
                os.environ.pop(deploy.SCHEMA_PASSWORD_ENV, None)
            else:
                os.environ[deploy.SCHEMA_PASSWORD_ENV] = old_f06
        self.assertFalse(self.calls.exists())
        self.assertFalse(deploy.E05_SCHEMA_RESULTS.exists())
        keys = json.loads(observed.read_text())
        self.assertNotIn(deploy.SCHEMA_PASSWORD_ENV, keys)
        self.assertNotIn(deploy.E05_SCHEMA_PASSWORD_ENV, keys)

    def test_post_install_order_keeps_f06_authoritative_before_e05(self):
        source = inspect.getsource(deploy.invoke_installer)
        f06_call = source.index('apply_schema_after_install(_SCHEMA_CONTEXT)')
        f06_stop = source.index('if f06_return_code != 0:')
        e05_call = source.index('maybe_apply_e05_schema_after_install(_SCHEMA_CONTEXT)')
        installer_stop = source.index('if return_code != 0 or _SCHEMA_CONTEXT is None:')
        self.assertLess(installer_stop, f06_call)
        self.assertLess(f06_call, f06_stop)
        self.assertLess(f06_stop, e05_call)
        self.assertNotIn('shell=True', source)

    def test_same_run_build_receipt_and_jar_checks_still_precede_install(self):
        source = inspect.getsource(deploy.main)
        install = source.index('return_code = invoke_installer(INSTALLER)')
        for check in (
                "receipt.get('status') != 'success'",
                "receipt.get('gradle_exit_code') != 0",
                "receipt.get('bridge_exit_code') != 0",
                "flow.get('run_id') != run_id",
                "source.get('commit_sha') != source_commit",
                "GIT_SHA.fullmatch(str(source.get('tree_sha', '')))",
                "digest_fileobj(jar_handle) != jar_record['sha256']",
                "digest_fileobj(handle) != artifact_sha256"):
            self.assertLess(source.index(check), install)
        self.assertEqual(source.count('invoke_installer(INSTALLER)'), 1)
        self.assertLess(install, source.index("version_record.update(status='verified' if return_code == 0 else 'failed'"))
        self.assertLess(install, source.index('raise SystemExit(return_code)'))

    def test_preservation_final_e05_runner_bytes_match_parent_production_pin(self):
        # Read source bytes only: no production runner or MySQL invocation.
        fresh = importlib.machinery.SourceFileLoader(
            'cyf_api_preservation_e05_parent_pin', str(DEPLOY)).load_module()
        runner = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-e05-additive-schema'
        self.assertEqual(fresh.E05_SCHEMA_RUNNER_SHA256,
                         hashlib.sha256(runner.read_bytes()).hexdigest())
        self.assertEqual(fresh.E05_SCHEMA_SQL_SHA256,
                         '3c287315e1d6126c652b219e6b4f14ebf02546ee7458c5d6abc3bf46e46b048c')
        self.assertIn('runner_digest_mismatch', inspect.getsource(fresh.e05_schema_prerequisites))

    def test_preservation_versioned_call_shape_still_requires_every_receipt_and_jar_check(self):
        source = inspect.getsource(deploy.main)
        install = source.index('return_code = invoke_installer(INSTALLER)')
        for check in ("receipt.get('status') != 'success'",
                      "receipt.get('gradle_exit_code') != 0",
                      "receipt.get('bridge_exit_code') != 0",
                      "flow.get('run_id') != run_id",
                      "source.get('commit_sha') != source_commit",
                      "GIT_SHA.fullmatch(str(source.get('tree_sha', '')))",
                      "digest_fileobj(jar_handle) != jar_record['sha256']"):
            self.assertLess(source.index(check), install)


if __name__ == '__main__':
    unittest.main()
