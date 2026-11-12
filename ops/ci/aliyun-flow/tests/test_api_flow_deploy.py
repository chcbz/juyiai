"""Offline F06 deploy integration tests; never touch production helpers or MySQL."""
import fcntl
import grp
import importlib.machinery
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
DEPLOY = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-flow-deploy'
loader = importlib.machinery.SourceFileLoader('cyf_api_flow_deploy_f06_test', str(DEPLOY))
deploy = loader.load_module()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


class ApiFlowDeployF06Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-api-flow-deploy-f06-', dir='/tmp')
        self.base = Path(self.tmp.name)
        self.base.chmod(0o700)
        self.state = self.base / 'state'
        self.state.mkdir(mode=0o700)
        self.release_lock = self.base / 'cyf-release-api.lock'
        self.release_lock.touch(mode=0o660)
        os.chown(self.release_lock, 0, grp.getgrnam('isp').gr_gid)
        self.release_lock.chmod(0o660)
        self.runner = self.base / 'cyf-api-additive-schema'
        self.calls = self.base / 'runner-calls'
        self.observed = self.base / 'runner-observed.json'
        self.context = {
            'pipeline_id': '5260799',
            'run_id': '40',
            'source_commit_sha': 'a' * 40,
            'source_tree_sha': 'b' * 40,
            'receipt_sha256': 'c' * 64,
            'jar_sha256': 'd' * 64,
        }
        self.previous = {
            'ROOT': deploy.ROOT,
            'SCHEMA_RESULTS': deploy.SCHEMA_RESULTS,
            'RELEASE_LOCK': deploy.RELEASE_LOCK,
            'SCHEMA_RUNNER': deploy.SCHEMA_RUNNER,
            'SCHEMA_PASSWORD_FILE': deploy.SCHEMA_PASSWORD_FILE,
            '_SCHEMA_CONTEXT': deploy._SCHEMA_CONTEXT,
        }
        deploy.ROOT = self.state
        deploy.SCHEMA_RESULTS = self.state / 'schema-results'
        deploy.RELEASE_LOCK = self.release_lock
        deploy.SCHEMA_RUNNER = self.runner
        deploy.SCHEMA_PASSWORD_FILE = self.state / 'f06-schema-password'
        deploy._SCHEMA_CONTEXT = self.context
        self.old_password = os.environ.get(deploy.SCHEMA_PASSWORD_ENV)
        self.old_attacker = os.environ.get('CYF_F06_SCHEMA_OFFLINE_TEST')
        os.environ[deploy.SCHEMA_PASSWORD_ENV] = 'offline-secret-never-persist'
        os.environ['CYF_F06_SCHEMA_OFFLINE_TEST'] = 'YES'
        self.write_record()
        self.write_runner(self.report('pass'), 0)

    def tearDown(self):
        for name, value in self.previous.items():
            setattr(deploy, name, value)
        if self.old_password is None:
            os.environ.pop(deploy.SCHEMA_PASSWORD_ENV, None)
        else:
            os.environ[deploy.SCHEMA_PASSWORD_ENV] = self.old_password
        if self.old_attacker is None:
            os.environ.pop('CYF_F06_SCHEMA_OFFLINE_TEST', None)
        else:
            os.environ['CYF_F06_SCHEMA_OFFLINE_TEST'] = self.old_attacker
        self.tmp.cleanup()

    def report(self, status, error=None, partial=False):
        tables = {
            'agent_task_artifact_outcome': {'status': 'created_equivalent'},
            'agent_task_artifact_outcome_decision': {'status': 'created_equivalent'},
        }
        value = {
            'schema_version': 1,
            'operation': 'apply',
            'status': status,
            'transaction_model': 'mysql_ddl_autocommit_per_create_no_rollback_or_drop',
            'lock_order': ['f06_runner_file_lock', 'f06_mysql_named_lock'],
            'tables': tables,
        }
        if partial:
            tables['agent_task_artifact_outcome_decision'] = {
                'status': 'create_backend_error_absent'}
            value['failed_table'] = 'agent_task_artifact_outcome_decision'
        if error is not None:
            value['error'] = error
        return value

    def write_record(self, **changes):
        value = {
            'schema_version': 2,
            'status': 'installed',
            'phase': 'installed',
            'recovery': 'not_required',
            'ticket_sha256': 'e' * 64,
            'source_commit_sha': self.context['source_commit_sha'],
            'source_tree_sha': self.context['source_tree_sha'],
            'run_id': self.context['run_id'],
            'receipt_sha256': self.context['receipt_sha256'],
            'candidate_sha256': self.context['jar_sha256'],
            'previous_sha256': 'f' * 64,
            'backup': str(self.state / 'backups/fixture.jar'),
            'candidate_stop_rc': 0,
            'timestamp': '20260913T000000Z',
        }
        value.update(changes)
        path = self.state / 'record.json'
        path.write_bytes(encoded(value))
        path.chmod(0o600)

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
    'env_keys': sorted(os.environ),
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
        return json.loads((deploy.SCHEMA_RESULTS / 'run-40.json').read_text())

    def test_success_runs_once_under_release_lock_and_does_not_claim_feature_activation(self):
        self.assertEqual(deploy.apply_schema_after_install(self.context), 0)
        result = self.result()
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['activation_claim'], 'schema_only_not_feature_activation')
        self.assertEqual(result['sql_sha256'], deploy.SCHEMA_SQL_SHA256)
        self.assertEqual(self.calls.read_text(), '1')
        observed = json.loads(self.observed.read_text())
        self.assertTrue(observed['release_lock_held'])
        self.assertEqual(observed['argv'], ['--apply'])
        self.assertEqual(
            observed['env_keys'], ['CYF_F06_MYSQL_PASSWORD', 'LC_ALL', 'PATH'])
        evidence = ''.join(path.read_text(errors='replace')
                           for path in deploy.SCHEMA_RESULTS.iterdir())
        self.assertNotIn('offline-secret-never-persist', evidence)
        for path in deploy.SCHEMA_RESULTS.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_same_run_pass_is_reused_without_rerunning_runner(self):
        self.assertEqual(deploy.apply_schema_after_install(self.context), 0)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 0)
        self.assertEqual(self.calls.read_text(), '1')

    def test_partial_ddl_failure_is_preserved_and_same_run_is_not_retried(self):
        self.write_runner(self.report('failed', 'create_statement_failed', partial=True), 1,
                          stderr='fixture backend error')
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        first = self.result()
        self.assertEqual(first['error'], 'create_statement_failed')
        self.assertEqual(first['runner_report']['failed_table'],
                         'agent_task_artifact_outcome_decision')
        self.assertEqual(first['runner_report']['tables']['agent_task_artifact_outcome']['status'],
                         'created_equivalent')
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        self.assertEqual(self.calls.read_text(), '1')
        self.assertEqual(self.result(), first)
        self.assertEqual((deploy.SCHEMA_RESULTS / 'run-40.stderr').read_text().strip(),
                         'fixture backend error')

    def test_interrupted_running_state_requires_manual_recovery_without_rerun(self):
        deploy.ensure_private_directory(deploy.SCHEMA_RESULTS)
        running = deploy.schema_state(
            self.context, 'running', '2026-09-13T00:00:00.000000Z',
            action='inspect durable metadata; do not rerun')
        deploy.write_schema_state(deploy.schema_paths('40')['state'], running, create=True)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.result()['status'], 'running')

    def test_installer_failure_is_returned_without_schema_attempt_or_password_leak(self):
        installer = self.base / 'failed-installer'
        installer_observed = self.base / 'installer-observed'
        installer.write_text(
            '#!/usr/bin/python3\nimport os\nfrom pathlib import Path\n'
            + 'Path(%r).write_text(str(%r in os.environ))\nraise SystemExit(7)\n'
            % (str(installer_observed), deploy.SCHEMA_PASSWORD_ENV))
        installer.chmod(0o755)
        self.assertEqual(deploy.invoke_installer(str(installer)), 7)
        self.assertEqual(installer_observed.read_text(), 'False')
        self.assertFalse(deploy.SCHEMA_RESULTS.exists())
        self.assertFalse(self.calls.exists())

    def test_already_installed_recovery_path_still_invokes_schema(self):
        installer = self.base / 'already-installed'
        installer.write_text('#!/bin/sh\necho CYF_API_FLOW_INSTALL=PASS_ALREADY_INSTALLED\nexit 0\n')
        installer.chmod(0o755)
        self.assertEqual(deploy.invoke_installer(str(installer)), 0)
        self.assertEqual(self.calls.read_text(), '1')
        self.assertEqual(self.result()['status'], 'pass')

    def test_wrong_installed_record_fails_before_runner_and_is_durable(self):
        self.write_record(run_id='41')
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        self.assertFalse(self.calls.exists())
        result = self.result()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'same_run_installed_record_mismatch')

    def test_root_only_file_secret_is_used_without_persisting_it(self):
        os.environ.pop(deploy.SCHEMA_PASSWORD_ENV)
        deploy.SCHEMA_PASSWORD_FILE.write_text('offline-file-secret')
        deploy.SCHEMA_PASSWORD_FILE.chmod(0o600)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 0)
        self.assertNotIn('offline-file-secret', json.dumps(self.result()))
        self.assertNotIn(deploy.SCHEMA_PASSWORD_ENV, os.environ)

    def test_file_secret_rejects_symlink_world_readable_and_hard_link(self):
        os.environ.pop(deploy.SCHEMA_PASSWORD_ENV)
        source = self.base / 'secret'
        source.write_text('never-persist')
        source.chmod(0o600)
        deploy.SCHEMA_PASSWORD_FILE.symlink_to(source)
        self.assertIsNone(deploy.schema_prerequisites()[1])
        deploy.SCHEMA_PASSWORD_FILE.unlink()
        os.link(str(source), str(deploy.SCHEMA_PASSWORD_FILE))
        self.assertIsNone(deploy.schema_prerequisites()[1])
        deploy.SCHEMA_PASSWORD_FILE.unlink()
        deploy.SCHEMA_PASSWORD_FILE.write_text('never-persist')
        deploy.SCHEMA_PASSWORD_FILE.chmod(0o644)
        self.assertIsNone(deploy.schema_prerequisites()[1])

    def test_file_secret_requires_root_only_parent_and_single_line(self):
        os.environ.pop(deploy.SCHEMA_PASSWORD_ENV)
        deploy.SCHEMA_PASSWORD_FILE.write_text('never-persist')
        deploy.SCHEMA_PASSWORD_FILE.chmod(0o600)
        self.state.chmod(0o755)
        self.assertIsNone(deploy.schema_prerequisites()[1])
        self.state.chmod(0o700)
        deploy.SCHEMA_PASSWORD_FILE.write_text('bad\nsecret')
        self.assertIn('db_principal_or_protected_password_not_configured',
                      deploy.schema_prerequisites()[0])

    def test_missing_runner_and_db_principal_are_both_actionable(self):
        self.runner.unlink()
        os.environ.pop(deploy.SCHEMA_PASSWORD_ENV)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        result = self.result()
        self.assertEqual(result['status'], 'blocked_precondition')
        self.assertEqual(result['error'], 'schema_activation_prerequisites_missing')
        self.assertEqual(result['prerequisites'], [
            'schema_runner_not_installed',
            'db_principal_or_protected_password_not_configured',
        ])
        self.assertIn('cyf_f06_schema_runner', result['action'])
        self.assertIn('new Flow run', result['action'])

    def test_malformed_runner_output_is_preserved_and_not_treated_as_success(self):
        self.write_runner('not-a-runner-report', 0)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        result = self.result()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'schema_runner_report_contract_mismatch')
        self.assertIsNone(result['runner_report'])
        self.assertTrue((deploy.SCHEMA_RESULTS / 'run-40.stdout').is_file())
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        self.assertEqual(self.calls.read_text(), '1')

    def test_runner_cannot_report_pass_with_an_unverified_table(self):
        report = self.report('pass')
        report['tables']['agent_task_artifact_outcome_decision']['status'] = 'not_attempted'
        self.write_runner(report, 0)
        self.assertEqual(deploy.apply_schema_after_install(self.context), 1)
        result = self.result()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'schema_runner_false_success')
        self.assertEqual(self.calls.read_text(), '1')

    def test_runner_native_failure_code_and_report_are_retained(self):
        self.write_runner(self.report('failed', 'mysql_session_ended'), 9,
                          stderr='access denied fixture')
        self.assertEqual(deploy.apply_schema_after_install(self.context), 9)
        result = self.result()
        self.assertEqual(result['runner_exit_code'], 9)
        self.assertEqual(result['error'], 'mysql_session_ended')
        self.assertEqual(result['runner_report']['error'], 'mysql_session_ended')
        self.assertNotEqual(result['stderr_sha256'], '0' * 64)


    def test_preservation_explicit_version_and_external_artifact_digest_are_required(self):
        self.assertEqual(deploy.validate_versioned_release('fixture-version', '1' * 64), 'fixture-version')
        for version, digest in (('', '1' * 64), (' v', '1' * 64), ('v\n', '1' * 64), ('v', 'unknown')):
            with self.subTest(version=version, digest=digest):
                with self.assertRaises(SystemExit):
                    deploy.validate_versioned_release(version, digest)

    def test_preservation_version_record_keeps_all_byte_checks_before_installer(self):
        import inspect
        source = inspect.getsource(deploy.main)
        install = source.index('return_code = invoke_installer(INSTALLER)')
        for check in ("digest_fileobj(handle) != artifact_sha256",
                      "source.get('commit_sha') != source_commit",
                      "digest_fileobj(jar_handle) != jar_record['sha256']",
                      "version_record_path = ROOT / ('versioned-release-' + run_id + '.json')"):
            self.assertLess(source.index(check), install)
        self.assertIn("status='verified' if return_code == 0 else 'failed'", source)

    def test_preservation_physical_backup_directory_and_arbitrary_alias_rejection(self):
        physical = self.base / 'physical-backups'
        physical.mkdir(mode=0o700)
        deploy.validate_backup_directory(physical)
        alias = self.base / 'unapproved-alias'
        alias.symlink_to(physical, target_is_directory=True)
        with self.assertRaises(SystemExit):
            deploy.validate_backup_directory(alias)
        physical.chmod(0o755)
        with self.assertRaises(SystemExit):
            deploy.validate_backup_directory(physical)

    def test_preservation_tar_validation_accepts_safe_historical_reports_not_extra_payload(self):
        import io, tarfile
        def opened(names):
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w') as tar:
                for name in names:
                    entry = tarfile.TarInfo(name)
                    entry.size = 1
                    tar.addfile(entry, io.BytesIO(b'x'))
            buffer.seek(0)
            return tarfile.open(fileobj=buffer, mode='r:')
        names = sorted(deploy.EXPECTED_MEMBERS)
        with opened(names + ['test-results/summary.json', 'test-results/suite.xml']) as archive:
            self.assertEqual(set(deploy.validated_release_members(archive)), deploy.EXPECTED_MEMBERS)
        for extra in ('test-results/../escape.xml', 'test-results//suite.xml',
                      'test-results/unapproved.bin', 'test-results\\suite.xml', '/escape'):
            with self.subTest(extra=extra), opened(names + [extra]) as archive:
                with self.assertRaises(SystemExit):
                    deploy.validated_release_members(archive)
        with opened(names + ['test-results/suite.xml', 'test-results/suite.xml']) as archive:
            with self.assertRaises(SystemExit):
                deploy.validated_release_members(archive)


class ApiLocalClosedContractTest(unittest.TestCase):
    """Pure synthetic type/binding units; no real authority/build/install claim.

    FileRefs intentionally do not name existing files. Runtime acceptance must
    independently verify protected descriptors/publication/proofs before calling
    these comparison helpers. This is not the production inspector or installer.
    """
    def setUp(self):
        import copy
        self.copy = copy.deepcopy
        self.ref = lambda label: {'path': '/home/isp/state/cyf-api-flow/local-fixture/' + label,
            'sha256': 'a' * 64, 'size': 100}
        ident = {'version': '1.0.2-unit', 'buildId': 'opaque-build.20261009',
                 'commit': 'a' * 40, 'tree': 'b' * 40}
        self.precondition = {
            'canonicalJarSha256': 'c' * 64, 'installedRecord': None, 'approval': None,
            'runtimeGeneration': {'pid': 123, 'startTicks': '456', 'jarSha256': 'c' * 64},
            'identityInventory': self.ref('identities.json'),
            'inflightInventory': self.ref('inflight.json'),
            'schemaInventory': self.ref('schema-inventory.json'),
        }
        self.decision = {
            'format': 'cyf-api-local-install-decision-v1', 'status': 'approved',
            'scope': deploy.LOCAL_SCOPE, 'source': {'kind': 'local-build-v1',
                'identity': ident, 'batchId': 'explicit-unit-batch'},
            'admission': self.ref('admission.json'), 'package': {'sha256': 'd' * 64, 'size': 1000},
            'payloads': {name: {'sha256': 'e' * 64, 'size': 100} for name in deploy.LOCAL_MEMBERS},
            'buildEvidence': self.ref('build-evidence.json'),
            'controllerVerification': self.ref('controller-verification.json'),
            'maintenanceAuthority': self.ref('maintenance-authority.json'),
            'precondition': self.copy(self.precondition),
            'schemaPlan': self.ref('schema-plan.json'), 'helperCatalog': self.ref('helpers.json'),
            'rollbackPolicy': 'forward-only', 'productionAuthorized': True,
        }
        self.authority = {
            'format': 'cyf-api-local-maintenance-authority-v1', 'authorityId': deploy.LOCAL_AUTHORITY_ID,
            'scope': deploy.LOCAL_SCOPE, 'authorizationId': 'explicit-unit-permission',
            'authorizationEvidence': self.ref('separate-permission.json'),
            'release': {k: self.copy(self.decision[k]) for k in ('source', 'admission', 'package', 'payloads')},
            'schemaPlan': self.copy(self.decision['schemaPlan']),
            'helperCatalog': self.copy(self.decision['helperCatalog']),
            'precondition': self.copy(self.precondition),
            'operations': {'apiInstall': True, 'apiStopStart': True, 'schemaApply': True, 'helperInstall': False},
            'rollbackPolicy': 'forward-only', 'recoveryScope': deploy.LOCAL_RECOVERY_SCOPE,
            'productionAuthorized': True,
        }
        self.schema = {
            'format': 'cyf-api-local-schema-plan-v1',
            'partialDdlPolicy': 'introspect-equivalent-skip-missing-only-no-drop-no-ddl-rollback',
            'entries': [], 'resourcePreconditions': [],
        }
        for name in deploy.LOCAL_PROOF_REFS:
            self.schema[name] = self.ref(name + '.json')
        for feature, runner, inner, sql_sha in (
            ('F06', deploy.SCHEMA_RUNNER, 'db/agent-task-artifact-outcome-f06.sql', deploy.SCHEMA_SQL_SHA256),
            ('E05', deploy.E05_SCHEMA_RUNNER, 'db/agent-work-item-reassignment-e05.sql', deploy.E05_SCHEMA_SQL_SHA256),
        ):
            runner_ref = self.ref(feature)
            runner_ref['path'] = str(runner)
            self.schema['entries'].append({'feature': feature, 'runner': runner_ref,
                'resourceOuter': deploy.LOCAL_AGENT_MAPPER, 'resourceInner': inner,
                'sqlSha256': sql_sha, 'statementPolicy': 'exact_create_table_if_not_exists_only',
                'expectedCatalogSha256': 'f' * 64})
        for name, outer, inner in deploy.LOCAL_RESOURCES:
            self.schema['resourcePreconditions'].append({'name': name, 'resourceOuter': outer,
                'resourceInner': inner, 'sqlSha256': 'a' * 64, 'expectedCatalogSha256': 'f' * 64,
                'actualSchemaProof': self.ref(name + '-proof.json')})
        self.catalog = {'format': 'cyf-api-local-helper-catalog-v1', 'sourceCommit': 'a' * 40,
            'sourceTree': 'b' * 40, 'helpers': {}, 'kitRole': 'reuse-installed-no-local-record-change'}
        for name, path in deploy.LOCAL_HELPER_PATHS.items():
            ref = self.ref(name)
            ref['path'] = path
            self.catalog['helpers'][name] = ref
        self.binding = deploy.local_binding_from_decision(self.decision, self.ref('decision.json'))
        self.approval = {'schema_version': 3, 'release': self.copy(self.binding),
            'binding_sha256': deploy.local_binding_sha(self.binding), 'consumed': False, 'consumed_at': None}
        self.record = {'schema_version': 3, 'status': 'prepared', 'phase': 'pre_cutover',
            'recovery': 'not_started', 'release': self.copy(self.binding),
            'binding_sha256': deploy.local_binding_sha(self.binding),
            'candidate_sha256': 'e' * 64, 'previous_sha256': 'c' * 64,
            'backup': str(deploy.BACKUPS / ('20261009T120000Z-' + 'e' * 64 + '-123.jar')),
            'candidate_stop_rc': 255, 'timestamp': '20261009T120000Z'}

    def reject(self, function, value, code=None):
        with self.assertRaises(deploy.LocalRejected) as caught:
            function(value)
        self.assertIn(caught.exception.code, deploy.LOCAL_SAFE_CODES)
        self.assertEqual(str(caught.exception), caught.exception.code)
        if code is not None:
            self.assertEqual(caught.exception.code, code)

    def test_closed_json_rejects_duplicate_nan_float_exponent_and_bad_encoding(self):
        for raw in (b'{"key":1,"key":2}', b'{"nested":{"k":1,"k":2}}', b'{"key":NaN}',
                    b'{"key":Infinity}', b'{"key":1.0}', b'{"key":1e999}', b'\xff'):
            with self.subTest(raw=repr(raw)):
                self.reject(deploy.local_json, raw)
        self.assertEqual(deploy.local_json(b'{"n":1,"absent":null,"flag":false}'),
                         {'n': 1, 'absent': None, 'flag': False})

    def test_file_ref_grammar_and_integer_types_are_exact_not_presence(self):
        self.assertEqual(deploy.local_ref(self.ref('proof.json')), self.ref('proof.json'))
        for size in (True, False, -1, 1.0, '100', None):
            item = self.ref('proof.json'); item['size'] = size
            self.reject(deploy.local_ref, item)
        for path in ('relative', '//var/lib/proof', '/var//lib/proof', '/var/lib/../proof',
                     '/var/lib/./proof', '/var/lib/proof/', '/var/lib/proof\n', '/var/lib/a\\b'):
            item = self.ref('proof.json'); item['path'] = path
            self.reject(deploy.local_ref, item, 'PATH_UNSAFE')
        for digest in ('A' * 64, 'a' * 63, 'a' * 65, True, None):
            item = self.ref('proof.json'); item['sha256'] = digest
            self.reject(deploy.local_ref, item)
        item = self.ref('proof.json'); item['extra'] = 'unreviewed'
        self.reject(deploy.local_ref, item)

    def test_local_source_is_opaque_and_never_flow_run_or_legacy_alias(self):
        self.assertEqual(deploy.local_source(self.decision['source']), self.decision['source'])
        for obj in ({**self.decision['source'], 'run_id': '120'},
                    {**self.decision['source'], 'kind': 'flow-run-v1'},
                    {**self.decision['source'], 'batchId': 'bad\nidentity'}):
            self.reject(deploy.local_source, obj, 'SOURCE_IDENTITY_MISMATCH')
        for field in ('version', 'buildId', 'commit', 'tree'):
            for value in (None, True, '', 'bad\nvalue'):
                obj = self.copy(self.decision['source']); obj['identity'][field] = value
                self.reject(deploy.local_source, obj, 'SOURCE_IDENTITY_MISMATCH')

    def test_precondition_requires_explicit_absence_generation_and_all_inventories(self):
        self.assertEqual(deploy.local_precondition(self.precondition), self.precondition)
        for key in self.precondition:
            value = self.copy(self.precondition); del value[key]
            self.reject(deploy.local_precondition, value)
        for field, bad in (('pid', True), ('pid', 0), ('pid', '123'), ('startTicks', '0'),
                           ('startTicks', 456), ('jarSha256', 'f' * 64)):
            value = self.copy(self.precondition); value['runtimeGeneration'][field] = bad
            self.reject(deploy.local_precondition, value, 'CANONICAL_GENERATION_CHANGED')
        for key in ('installedRecord', 'approval'):
            value = self.copy(self.precondition); value[key] = False
            self.reject(deploy.local_precondition, value)

    def test_schema_plan_requires_exact_ten_ordered_resources_and_four_proofs(self):
        self.assertIs(deploy.local_schema_plan(self.schema), self.schema)
        for name in deploy.LOCAL_PROOF_REFS:
            value = self.copy(self.schema); del value[name]
            self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')
            value = self.copy(self.schema); value[name] = None
            self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')
        for index in range(len(deploy.LOCAL_RESOURCES)):
            value = self.copy(self.schema); value['resourcePreconditions'].pop(index)
            self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')
            value = self.copy(self.schema); del value['resourcePreconditions'][index]['actualSchemaProof']
            self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')
            value = self.copy(self.schema); value['resourcePreconditions'][index]['expectedCatalogSha256'] = None
            self.reject(deploy.local_schema_plan, value, 'SCHEMA_CATALOG_DRIFT')
        value = self.copy(self.schema); value['resourcePreconditions'].reverse()
        self.reject(deploy.local_schema_plan, value, 'SCHEMA_RESOURCE_MISMATCH')
        value = self.copy(self.schema); value['resourcePreconditions'] += value['resourcePreconditions'][:1]
        self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')
        value = self.copy(self.schema); value['resourcePreconditions'] = value['resourcePreconditions'][3:4] + value['resourcePreconditions'][6:7]
        self.reject(deploy.local_schema_plan, value, 'SCHEMA_PREREQUISITE_MISSING')

    def test_schema_entries_must_bind_same_batch_resources_and_exact_create_only(self):
        for field, value in (('feature', 'F06'), ('sqlSha256', '0' * 64),
                             ('resourceOuter', 'BOOT-INF/lib/wrong.jar'),
                             ('resourceInner', 'db/unknown.sql'), ('statementPolicy', 'allow-alter')):
            plan = self.copy(self.schema); plan['entries'][1][field] = value
            self.reject(deploy.local_schema_plan, plan, 'SCHEMA_RESOURCE_MISMATCH')
        plan = self.copy(self.schema); plan['entries'].reverse()
        self.reject(deploy.local_schema_plan, plan, 'SCHEMA_RESOURCE_MISMATCH')
        plan = self.copy(self.schema); plan['entries'][1]['runner']['path'] = '/tmp/unreviewed-runner'
        self.reject(deploy.local_schema_plan, plan, 'SCHEMA_RESOURCE_MISMATCH')
        plan = self.copy(self.schema); plan['resourcePreconditions'][1]['resourceInner'] = 'db/old-identity.sql'
        self.reject(deploy.local_schema_plan, plan, 'SCHEMA_RESOURCE_MISMATCH')

    def test_helper_catalog_is_exact_installed_paths_and_no_kit_reimplementation(self):
        self.assertIs(deploy.local_helper_catalog(self.catalog), self.catalog)
        for helper in deploy.LOCAL_HELPER_PATHS:
            cat = self.copy(self.catalog); del cat['helpers'][helper]
            self.reject(deploy.local_helper_catalog, cat, 'HELPER_CATALOG_MISMATCH')
            cat = self.copy(self.catalog); cat['helpers'][helper]['path'] = '/tmp/' + helper
            self.reject(deploy.local_helper_catalog, cat, 'HELPER_CATALOG_MISMATCH')
        cat = self.copy(self.catalog); cat['kitRole'] = 'replace-kit'
        self.reject(deploy.local_helper_catalog, cat, 'HELPER_CATALOG_MISMATCH')
        cat = self.copy(self.catalog); cat['helpers']['second-installer'] = self.ref('second-installer')
        self.reject(deploy.local_helper_catalog, cat, 'HELPER_CATALOG_MISMATCH')

    def test_install_decision_requires_exact_permission_and_every_bound_field(self):
        self.assertIs(deploy.local_install_decision(self.decision), self.decision)
        for key in self.decision:
            value = self.copy(self.decision); del value[key]
            self.reject(deploy.local_install_decision, value)
        for key, bad in (('productionAuthorized', 1), ('productionAuthorized', False),
                         ('status', 'admitted'), ('scope', 'artifact-admission-only'),
                         ('rollbackPolicy', 'env-inferred'), ('package', {'sha256': 'd' * 64, 'size': True})):
            value = self.copy(self.decision); value[key] = bad
            self.reject(deploy.local_install_decision, value)
        value = self.copy(self.decision); value['run_id'] = '123'
        self.reject(deploy.local_install_decision, value)

    def test_independent_maintenance_has_exact_operations_no_cli_or_artifact_escalation(self):
        checked = deploy.local_authority_matches(self.decision, self.authority, ('apiInstall', 'apiStopStart', 'schemaApply'))
        self.assertIs(checked, self.authority)
        for operation in ('apiInstall', 'apiStopStart', 'schemaApply'):
            value = self.copy(self.authority); value['operations'][operation] = False
            with self.assertRaises(deploy.LocalRejected) as caught:
                deploy.local_authority_matches(self.decision, value, (operation,))
            self.assertEqual(caught.exception.code, 'MAINTENANCE_SCOPE_MISSING')
        for bad in (1, 'true', None):
            value = self.copy(self.authority); value['operations']['helperInstall'] = bad
            self.reject(deploy.local_maintenance_authority, value, 'MAINTENANCE_SCOPE_MISSING')
        for field in ('schemaPlan', 'helperCatalog', 'precondition', 'rollbackPolicy', 'release'):
            value = self.copy(self.authority)
            if field == 'rollbackPolicy': value[field] = 'rollback-compatible'
            elif field == 'precondition': value[field]['identityInventory']['sha256'] = 'f' * 64
            elif field == 'release': value[field]['source']['batchId'] = 'foreign-batch'
            else: value[field]['sha256'] = 'f' * 64
            with self.assertRaises(deploy.LocalRejected) as caught:
                deploy.local_authority_matches(self.decision, value)
            self.assertEqual(caught.exception.code, 'AUTHORITY_INVALID')
        value = self.copy(self.authority); value['authorizationEvidence'] = None
        self.reject(deploy.local_maintenance_authority, value, 'AUTHORITY_INVALID')

    def test_release_binding_excludes_mutable_envelope_and_is_canonical_not_self_hashed(self):
        original = self.copy(self.binding)
        digest = deploy.local_binding_sha(self.binding)
        reversed_keys = dict(reversed(list(self.binding.items())))
        self.assertEqual(deploy.local_binding_sha(reversed_keys), digest)
        self.assertEqual(self.binding, original)
        for field in ('source', 'decision', 'admission', 'maintenanceAuthority', 'schemaPlan', 'helperCatalog'):
            value = self.copy(self.binding)
            if field == 'source': value[field]['batchId'] = 'different-batch'
            else: value[field]['sha256'] = 'f' * 64
            self.assertNotEqual(deploy.local_binding_sha(value), digest)
        for key in ('binding_sha256', 'run_id', 'status', 'phase'):
            value = self.copy(self.binding); value[key] = 'unreviewed'
            self.reject(deploy.local_binding_sha, value, 'RECOVERY_BINDING_MISMATCH')

    def test_approval_v3_never_infers_consumption_or_accepts_boolean_version(self):
        self.assertIs(deploy.local_approval(self.approval), self.approval)
        consumed = self.copy(self.approval); consumed.update(consumed=True, consumed_at='20261009T120000Z')
        self.assertIs(deploy.local_approval(consumed), consumed)
        for field, bad in (('schema_version', True), ('schema_version', 2), ('consumed', 1),
                           ('consumed_at', '20261009T120000Z'), ('binding_sha256', 'f' * 64)):
            value = self.copy(self.approval); value[field] = bad
            self.reject(deploy.local_approval, value)
        value = self.copy(consumed); value['consumed_at'] = None
        self.reject(deploy.local_approval, value)
        value = self.copy(self.approval); del value['consumed_at']
        self.reject(deploy.local_approval, value)

    def test_install_record_retains_original_phases_exact_candidate_and_backup(self):
        for status in ('prepared', 'activating', 'active_pending', 'rolling_back', 'installed', 'failed'):
            value = self.copy(self.record); value['status'] = status
            self.assertIs(deploy.local_install_record(value), value)
        for field, bad in (('status', 'healthy-inferred-installed'), ('phase', 'bad phase'),
                           ('recovery', 'unknown\nvalue'), ('candidate_stop_rc', True),
                           ('candidate_stop_rc', -1), ('candidate_stop_rc', 256),
                           ('timestamp', '2026-10-09'), ('backup', '/tmp/unreviewed.jar'),
                           ('candidate_sha256', 'a' * 64), ('binding_sha256', 'a' * 64)):
            value = self.copy(self.record); value[field] = bad
            self.reject(deploy.local_install_record, value)
        for field in self.record:
            value = self.copy(self.record); del value[field]
            self.reject(deploy.local_install_record, value)
        value = self.copy(self.record); value['run_id'] = '120'
        self.reject(deploy.local_install_record, value)

    def publication(self):
        admitted = {'format': 'cyf-api-local-admitted-input-v1', 'status': 'admitted',
            'source': {k: self.copy(self.decision['source'][k]) for k in ('kind', 'identity')},
            'authority': {'authorityId': deploy.LOCAL_AUTHORITY_ID,
                'batchId': self.decision['source']['batchId'], 'batchAuthority': self.ref('batch.json'),
                'trustedRecord': self.ref('trusted.json'),
                'verificationRecord': self.copy(self.decision['controllerVerification'])},
            'package': {**self.decision['package'], 'path': self.ref('package.tgz')['path']},
            'payloads': {name: {**self.decision['payloads'][name], 'path': self.ref(name)['path']}
                         for name in deploy.LOCAL_MEMBERS},
            'evidence': {'buildEvidence': self.copy(self.decision['buildEvidence']),
                'snapshots': [{'role': 'build-evidence', 'originalPath': '/original/source/build.json',
                               'file': self.copy(self.decision['buildEvidence'])}]},
            'installPrecondition': {'canonicalJarSha256': self.precondition['canonicalJarSha256']},
            'scope': 'artifact-admission-only', 'productionAuthorized': False}
        verified = {'format': 'cyf-api-local-published-verification-v1', 'status': 'verified',
            'scope': 'artifact-admission-only', 'productionAuthorized': False,
            'admission': self.copy(self.decision['admission']), 'source': self.copy(admitted['source'])}
        return admitted, verified

    def test_publication_projection_must_stay_artifact_only_and_match_copied_proofs(self):
        admitted, verified = self.publication()
        original = self.copy((admitted, verified, self.decision))
        self.assertIs(deploy.local_publication_matches(self.decision, admitted, verified), self.decision)
        self.assertEqual((admitted, verified, self.decision), original)
        for field in ('productionAuthorized', 'scope', 'status'):
            changed = self.copy(admitted)
            changed[field] = True if field == 'productionAuthorized' else 'wrong'
            with self.assertRaises(deploy.LocalRejected):
                deploy.local_publication_matches(self.decision, changed, verified)
        changed = self.copy(verified); changed['productionAuthorized'] = True
        with self.assertRaises(deploy.LocalRejected):
            deploy.local_publication_matches(self.decision, admitted, changed)
        for field in ('package', 'payloads', 'buildEvidence', 'controllerVerification', 'precondition'):
            changed = self.copy(self.decision)
            if field == 'payloads': changed[field]['application.jar']['sha256'] = 'f' * 64
            elif field == 'precondition':
                changed[field]['canonicalJarSha256'] = 'f' * 64
                changed[field]['runtimeGeneration']['jarSha256'] = 'f' * 64
            else: changed[field]['sha256'] = 'f' * 64
            with self.assertRaises(deploy.LocalRejected):
                deploy.local_publication_matches(changed, admitted, verified)

    def test_schema_recovery_requires_separate_exact_installed_release_and_prior_proofs(self):
        value = {'format': 'cyf-api-local-schema-recovery-authority-v1',
            'authorityId': deploy.LOCAL_AUTHORITY_ID,
            'scope': 'exact-installed-release-partial-schema-reconcile',
            'authorizationEvidence': self.ref('recovery-permission.json'),
            'bindingSha256': deploy.local_binding_sha(self.binding),
            'installDecision': self.copy(self.binding['decision']),
            'priorResults': [self.ref('prior-result.json'), self.ref('prior-stdout.json')],
            'actualMetadataProof': self.ref('actual-metadata.json'), 'allowedFeatures': ['F06', 'E05'],
            'schemaPlan': self.copy(self.binding['schemaPlan']), 'canonicalJarSha256': 'e' * 64,
            'productionAuthorized': True}
        self.assertIs(deploy.local_schema_recovery_authority(value, self.binding), value)
        for field, bad in (('productionAuthorized', False), ('scope', 'new-release'),
                           ('bindingSha256', 'f' * 64), ('canonicalJarSha256', 'f' * 64),
                           ('priorResults', []), ('allowedFeatures', ['E05', 'F06']),
                           ('allowedFeatures', ['F06', 'F06']), ('actualMetadataProof', None)):
            changed = self.copy(value); changed[field] = bad
            with self.assertRaises(deploy.LocalRejected):
                deploy.local_schema_recovery_authority(changed, self.binding)
        changed = self.copy(value); changed['priorResults'] *= 2
        with self.assertRaises(deploy.LocalRejected):
            deploy.local_schema_recovery_authority(changed, self.binding)

    def test_closed_type_helpers_do_not_read_write_or_spawn_and_emit_only_fixed_codes(self):
        from unittest.mock import patch
        with patch('os.open', side_effect=AssertionError('unexpected filesystem operation')), \
             patch('subprocess.run', side_effect=AssertionError('unexpected process operation')):
            deploy.local_install_decision(self.decision)
            deploy.local_authority_matches(self.decision, self.authority)
            deploy.local_schema_plan(self.schema)
            deploy.local_helper_catalog(self.catalog)
            deploy.local_approval(self.approval)
            deploy.local_install_record(self.record)
            admitted, verified = self.publication()
            deploy.local_publication_matches(self.decision, admitted, verified)
        error = deploy.LocalRejected('raw-secret-or-exception-body')
        self.assertEqual(error.code, 'INPUT_INVALID')
        self.assertEqual(str(error), 'INPUT_INVALID')


if __name__ == '__main__':
    unittest.main()
