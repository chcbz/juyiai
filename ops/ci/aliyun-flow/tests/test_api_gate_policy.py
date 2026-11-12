"""Small offline control-plane fixtures; never invoke a production process or Gradle."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[4]
HOST = ROOT / 'ops/ci/aliyun-flow/host'


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


class ApiGatePolicyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-gate-policy-', dir='/tmp')
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        for name in ('state/incoming', 'state/backups', 'service', 'bin'):
            (self.root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.old = b'old-fixture-artifact'
        self.target = self.root / 'service/cyf-api-kit.jar'
        self.target.write_bytes(self.old)
        lock = self.root / 'cyf-release-api.lock'
        lock.touch(mode=0o600)
        lifecycle = self.root / 'bin/cyf-api-kit'
        lifecycle.write_text('''#!/bin/sh
root="$(dirname "$0")/.."
echo "$1" >> "$root/calls"
case "$1" in
stop) touch "$root/stopped" ;;
start) rm -f "$root/stopped" ;;
status) if [ -e "$root/stopped" ]; then echo STATUS=STOPPED; exit 3; fi; echo HEALTH=UP ;;
esac
''')
        lifecycle.chmod(0o700)
        jar = io.BytesIO()
        with zipfile.ZipFile(jar, 'w') as archive:
            archive.writestr('META-INF/MANIFEST.MF', 'Spring-Boot-Classes: BOOT-INF/classes/\nStart-Class: fixture.Main\n')
            archive.writestr('BOOT-INF/lib/fixture.jar', b'fixture')
        self.jar = jar.getvalue()
        provenance = encoded({'fixture': True})
        flow = dict(organization_id='5fb7d76ee6f9d07f148529c7', pipeline_id='5260799',
                    job_id='cloud_ci.api_ci', run_id='34', source_tip_sha='a' * 40)
        source = dict(branch='develop', commit_sha='a' * 40, tree_sha='b' * 40,
                      clean_before=True, clean_after=True)
        records = [dict(kind='application_jar', path='application.jar', sha256=digest(self.jar), size=len(self.jar)),
                   dict(kind='dependency_provenance', path='dependency.provenance.json', sha256=digest(provenance), size=len(provenance))]
        receipt = dict(schema_version=1, status='success', gradle_exit_code=0, bridge_exit_code=0,
                       ticket_sha256='c' * 64, flow=flow, source=source, files=records)
        receipt_bytes = encoded(receipt)
        metadata = dict(schema_version=1, receipt_sha256=digest(receipt_bytes), flow=flow, source=source,
                        application_jar=records[0], dependency_provenance=records[1])
        sidecar = dict(schema_version=1, receipt_sha256=digest(receipt_bytes), flow=flow,
                       sha256=digest(self.jar), size=len(self.jar))
        self.members = {'application.jar': self.jar, 'application.metadata.json': encoded(metadata),
                        'application.sidecar.json': encoded(sidecar), 'dependency.provenance.json': provenance,
                        'receipt.json': receipt_bytes}
        self.write_package()
        approval = dict(schema_version=2, ticket_sha256='c' * 64, source_commit_sha='a' * 40,
                        source_tree_sha='b' * 40, run_id='34', receipt_sha256=digest(receipt_bytes),
                        jar_sha256=digest(self.jar), consumed=False)
        path = self.root / 'state/approval.json'
        path.write_bytes(encoded(approval))
        path.chmod(0o600)
        self.env = dict(os.environ, CYF_RELEASE_OFFLINE_TEST='YES',
                        CYF_API_FLOW_INSTALL_TEST_ROOT=str(self.root),
                        CYF_API_FLOW_TEST_TARGET_AVAILABLE_BYTES=str(2 * 1024 * 1024),
                        CYF_API_FLOW_TEST_BACKUP_AVAILABLE_BYTES=str(2 * 1024 * 1024))

    def tearDown(self):
        self.tmp.cleanup()

    def write_package(self):
        with tarfile.open(str(self.root / 'state/incoming/package.tgz'), 'w:gz') as archive:
            for name, content in self.members.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))

    def install(self):
        return subprocess.run([str(HOST / 'cyf-api-flow-install')], env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=15)

    def assert_untouched(self):
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertFalse((self.root / 'calls').exists())

    def test_actual_artifact_space_succeeds_far_below_five_gib(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.target.read_bytes(), self.jar)
        record = json.loads((self.root / 'state/record.json').read_text())
        self.assertEqual(record['status'], 'installed')
        self.assertEqual(Path(record['backup']).read_bytes(), self.old)

    def test_insufficient_actual_space_stops_before_lifecycle(self):
        self.env['CYF_API_FLOW_TEST_TARGET_AVAILABLE_BYTES'] = '1'
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('capacity before unpacking', result.stderr)
        self.assert_untouched()

    def test_separate_backup_filesystem_requires_actual_backup_bytes(self):
        self.env.update(CYF_API_FLOW_TEST_TARGET_DEVICE='1', CYF_API_FLOW_TEST_BACKUP_DEVICE='2',
                        CYF_API_FLOW_TEST_BACKUP_AVAILABLE_BYTES='1')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('backup capacity', result.stderr)
        self.assert_untouched()

    def test_tampered_artifact_is_rejected(self):
        self.members['application.jar'] += b'tamper'
        self.write_package()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('JAR does not match receipt', result.stderr)
        self.assert_untouched()

    def test_wrong_source_approval_is_rejected(self):
        p = self.root / 'state/approval.json'
        data = json.loads(p.read_text())
        data['source_commit_sha'] = 'd' * 40
        p.write_bytes(encoded(data))
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does not match exact root approval', result.stderr)
        self.assert_untouched()

    def test_path_traversal_is_rejected(self):
        self.members['../outside'] = b'forbidden'
        self.write_package()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('package member', result.stderr)
        self.assertFalse((self.root / 'outside').exists())
        self.assert_untouched()

    def test_embedded_python_compiles(self):
        for name in ('cyf-api-flow-install', 'cyf-api-kit'):
            text = (HOST / name).read_text()
            for index, body in enumerate(re.findall(r"<<'PY'\n(.*?)\nPY", text, re.S)):
                compile(body, '%s:embedded:%s' % (name, index), 'exec')

    def test_unmeasured_limits_and_timeout_kill_are_absent(self):
        installer = (HOST / 'cyf-api-flow-install').read_text()
        lifecycle = (HOST / 'cyf-api-kit').read_text()
        deploy = (HOST / 'cyf-api-flow-deploy').read_text()
        for name in ('MIN_LIFECYCLE_BYTES', 'MAX_PACKAGE_BYTES', 'MAX_EXTRACT_BYTES'):
            self.assertNotIn(name, installer)
        for name in ('MIN_DISK_AVAILABLE_BYTES', 'MIN_MEMORY_AVAILABLE_BYTES', 'TIMEOUT_SECONDS', '"$ticks" KILL'):
            self.assertNotIn(name, lifecycle)
        self.assertNotIn('LOCK_NB', deploy)
        self.assertNotIn('flock -w', installer)
        self.assertIn('healthy_endpoint_owned_by', lifecycle)
        self.assertIn('runtime_record_matches', lifecycle)
        self.assertIn('verify_lock_fd', lifecycle)


    def test_preservation_safe_flow_reports_are_not_extracted_into_privileged_workspace(self):
        self.members['test-results/summary.json'] = b'{"synthetic":true}'
        self.members['test-results/only-private-fixture.xml'] = b'<testsuite/>'
        self.write_package()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_bytes(), self.jar)
        self.assertFalse(any(self.root.rglob('only-private-fixture.xml')))
        self.assertFalse(any((self.root / 'service').glob('.cyf-api-flow-install.*')))

    def test_preservation_unsafe_historical_report_path_is_rejected_before_lifecycle(self):
        self.members['test-results/../outside.xml'] = b'forbidden'
        self.write_package()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unsafe or duplicate test report member', result.stderr)
        self.assert_untouched()

    def test_preservation_offline_backup_alias_is_not_the_only_production_allowlisted_alias(self):
        backups = self.root / 'state/backups'
        backups.rmdir()
        other = self.root / 'other-backups'
        other.mkdir(mode=0o700)
        backups.symlink_to(other, target_is_directory=True)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('backup alias is unsafe', result.stderr)
        self.assert_untouched()

    def test_preservation_forward_only_failure_retains_candidate_and_exact_retry_finalizes(self):
        # Existing offline-only fake lifecycle; no service/real JAR/process control.
        lifecycle = self.root / 'bin/cyf-api-kit'
        original = lifecycle.read_text()
        lifecycle.write_text(original.replace('start) rm -f "$root/stopped" ;;',
                                              'start) exit 1 ;;'))
        self.env['CYF_API_FLOW_FORWARD_ONLY'] = '1'
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.target.read_bytes(), self.jar)
        record = json.loads((self.root / 'state/record.json').read_text())
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['recovery'], 'forward_only_candidate_retained')
        self.assertEqual(Path(record['backup']).read_bytes(), self.old)
        self.assertFalse(json.loads((self.root / 'state/approval.json').read_text())['consumed'])
        calls = (self.root / 'calls').read_text().splitlines()
        self.assertEqual(calls, ['stop', 'status', 'start'])
        lifecycle.write_text(original)
        recovered = self.install()
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(self.target.read_bytes(), self.jar)
        self.assertEqual(json.loads((self.root / 'state/record.json').read_text())['status'], 'installed')
        self.assertTrue(json.loads((self.root / 'state/approval.json').read_text())['consumed'])
        self.assertEqual((self.root / 'calls').read_text().splitlines().count('stop'), 1)

    def test_preservation_forward_only_foreign_receipt_cannot_resume_or_restore(self):
        lifecycle = self.root / 'bin/cyf-api-kit'
        lifecycle.write_text(lifecycle.read_text().replace('start) rm -f "$root/stopped" ;;',
                                                         'start) exit 1 ;;'))
        self.env['CYF_API_FLOW_FORWARD_ONLY'] = '1'
        first = self.install()
        self.assertNotEqual(first.returncode, 0)
        prior_calls = (self.root / 'calls').read_bytes()
        approval = self.root / 'state/approval.json'
        value = json.loads(approval.read_text())
        value['receipt_sha256'] = '9' * 64
        approval.write_bytes(encoded(value))
        second = self.install()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('does not match exact root approval', second.stderr)
        self.assertEqual((self.root / 'calls').read_bytes(), prior_calls)
        self.assertEqual(self.target.read_bytes(), self.jar)



@unittest.skip('Historical schema3 publication is retired; native LOCAL schema4 is covered by test_native_local_api')
class ApiLocalSharedInstallerSourceTest(unittest.TestCase):
    """Real original shell transaction with SYNTHETIC verifier/kit and no MySQL.

    This is source regression, not isolated business acceptance, package admission,
    real service deployment, production authorization or Runtime readiness.
    """
    def setUp(self):
        from test_api_flow_deploy import ApiLocalReadonlyInspectTest, deploy
        self.deploy = deploy
        self.inputs = ApiLocalReadonlyInspectTest(); self.inputs.setUp()
        self.fixture = ApiGatePolicyTest(); self.fixture.setUp()
        f, i = self.fixture, self.inputs
        self.child = subprocess.Popen(['/bin/sh', '-c', 'read fixture_line', '-jar', str(f.target)],
            cwd=str(f.target.parent), stdin=subprocess.PIPE)
        proc = Path('/proc') / str(self.child.pid)
        raw = (proc / 'stat').read_bytes()
        ticks = raw[raw.rfind(b')') + 2:].split()[19].decode('ascii')
        i.decision['precondition'].update(canonicalJarSha256=digest(f.old), installedRecord=None, approval=None,
            runtimeGeneration={'pid': self.child.pid, 'startTicks': ticks, 'jarSha256': digest(f.old)})
        self.runtime_ref = i.write(i.root / 'runtime.record',
            ('pid=%s\nstart_ticks=%s\njar_sha256=%s\n' % (self.child.pid, ticks, digest(f.old))).encode(), 0o644)
        lifecycle = f.root / 'bin/cyf-api-kit'
        lifecycle.write_text(lifecycle.read_text().replace('start) rm -f',
            'start) if [ -f "$root/fail-start" ]; then exit 1; fi; rm -f'))
        for name in ('cyf-api-flow-deploy', 'cyf-api-flow-install'):
            i.catalog['helpers'][name] = i.write(Path(i.paths[name]), (HOST / name).read_bytes(), 0o755)
        i.catalog['helpers']['cyf-api-kit'] = i.write(Path(i.paths['cyf-api-kit']), lifecycle.read_bytes(), 0o755)
        i.authority['operations'].update(apiInstall=True, apiStopStart=True, schemaApply=True)
        i.admitted['installPrecondition']['canonicalJarSha256'] = digest(f.old)
        i.seal()
        f.env['CYF_API_FLOW_INSTALL_TEST_INPUT_ROOT'] = str(i.root)
        self.stage()

    def tearDown(self):
        self.child.stdin.close(); self.child.wait(timeout=5)
        self.fixture.tearDown(); self.inputs.tearDown()

    def stage(self):
        d, i, f = self.deploy, self.inputs, self.fixture
        self.binding = d.local_binding_from_decision(i.decision, i.decision_ref)
        approval = {'schema_version': 3, 'release': self.binding,
                    'binding_sha256': d.local_binding_sha(self.binding), 'consumed': False, 'consumed_at': None}
        (f.root / 'state/incoming/package.tgz').write_bytes(Path(i.admitted['package']['path']).read_bytes())
        (f.root / 'state/incoming/package.tgz').chmod(0o600)
        (f.root / 'state/approval.json').write_bytes(d.local_canonical(approval))
        (f.root / 'state/approval.json').chmod(0o600)

    def install(self):
        return self.fixture.install()

    def record(self):
        return json.loads((self.fixture.root / 'state/record.json').read_text())

    def test_local_same_original_transaction_consumes_v3_without_numeric_flow_identity(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = self.record()
        self.deploy.local_install_record(record, self.fixture.root / 'state/backups')
        self.assertEqual(record['release'], self.binding)
        self.assertEqual(record['status'], 'installed')
        self.assertNotIn('run_id', record)
        self.assertEqual(self.fixture.target.read_bytes(), self.inputs.payload_bytes['application.jar'])
        self.assertEqual(Path(record['backup']).read_bytes(), self.fixture.old)
        approval = self.deploy.local_approval(json.loads((self.fixture.root / 'state/approval.json').read_text()))
        self.assertTrue(approval['consumed'])

    def test_local_installed_same_binding_is_idempotent_no_second_stop_or_start(self):
        first = self.install(); self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.fixture.root / 'calls').read_text().splitlines()
        second = self.install(); self.assertEqual(second.returncode, 0, second.stderr)
        after = (self.fixture.root / 'calls').read_text().splitlines()
        self.assertEqual(before.count('start'), after.count('start'))
        self.assertEqual(before.count('stop'), after.count('stop'))
        self.assertIn('PASS_ALREADY_INSTALLED', second.stdout)

    def test_local_changed_generation_rejects_before_durable_record_or_lifecycle(self):
        (self.inputs.root / 'runtime.record').write_text('pid=1\nstart_ticks=1\njar_sha256=' + 'a' * 64 + '\n')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CANONICAL_GENERATION_CHANGED', result.stderr)
        self.fixture.assert_untouched()
        self.assertFalse((self.fixture.root / 'state/record.json').exists())

    def test_local_foreign_decision_binding_cannot_adopt_incoming(self):
        path = self.fixture.root / 'state/approval.json'
        approval = json.loads(path.read_text()); approval['release']['decision']['sha256'] = 'f' * 64
        approval['binding_sha256'] = self.deploy.local_binding_sha(approval['release'])
        path.write_bytes(self.deploy.local_canonical(approval))
        result = self.install(); self.assertNotEqual(result.returncode, 0)
        self.fixture.assert_untouched()

    def test_local_consumed_approval_active_pending_same_record_recovers_only_commit(self):
        self.fixture.env['CYF_API_FLOW_TEST_FAULT'] = 'record:installed:replace'
        first = self.install(); self.assertNotEqual(first.returncode, 0)
        self.assertEqual(self.record()['status'], 'active_pending')
        calls = (self.fixture.root / 'calls').read_text().splitlines()
        second = self.install(); self.assertEqual(second.returncode, 0, second.stderr)
        after = (self.fixture.root / 'calls').read_text().splitlines()
        self.assertEqual(calls.count('stop'), after.count('stop'))
        self.assertEqual(calls.count('start'), after.count('start'))
        self.assertEqual(self.record()['status'], 'installed')

    def test_local_forward_only_is_from_authority_not_caller_toggle(self):
        (self.fixture.root / 'fail-start').touch()
        self.fixture.env['CYF_API_FLOW_FORWARD_ONLY'] = '0'
        first = self.install(); self.assertNotEqual(first.returncode, 0, first.stdout)
        record = self.record()
        self.assertEqual(record['recovery'], 'forward_only_candidate_retained')
        self.assertEqual(self.fixture.target.read_bytes(), self.inputs.payload_bytes['application.jar'])
        (self.fixture.root / 'fail-start').unlink()
        second = self.install(); self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.record()['status'], 'installed')

    def test_local_rollback_compatible_ignores_caller_forward_only_and_restores_old(self):
        self.inputs.decision['rollbackPolicy'] = 'rollback-compatible'
        self.inputs.authority['rollbackPolicy'] = 'rollback-compatible'
        self.inputs.seal(); self.stage()
        (self.fixture.root / 'fail-start').touch()
        self.fixture.env['CYF_API_FLOW_FORWARD_ONLY'] = '1'
        result = self.install(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.record()['status'], 'rolling_back')
        self.assertEqual(self.fixture.target.read_bytes(), self.fixture.old)
        self.assertNotEqual(self.record()['recovery'], 'forward_only_candidate_retained')

if __name__ == '__main__':
    unittest.main()
