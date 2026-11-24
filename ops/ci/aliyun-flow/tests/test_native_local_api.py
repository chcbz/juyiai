"""Synthetic source/ZIP/lifecycle fixtures only; no real release/DB/Gradle."""
import copy
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import unittest
import zipfile
from unittest import mock
import test_api_gate_policy as old

HOST = old.HOST
PIN = '323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4'
CV = b'SYNTHETIC OPENCV FIXTURE - NOT A REAL DEPENDENCY'
sha = old.digest
encoded = old.encoded


class NativeLocalApiTest(unittest.TestCase):
    def setUp(self):
        self.f = old.ApiGatePolicyTest(); self.f.setUp()
        self.root = self.f.root
        self.host = self.root / 'host'; self.host.mkdir(mode=0o700)
        coordinator = (HOST / 'cyf-api-flow-deploy').read_text()
        # Only the private synthetic coordinator copy uses a synthetic dependency
        # pin. Production source still enforces the original immutable OpenCV.
        coordinator = coordinator.replace(PIN, sha(CV)).replace('== 722802', '== ' + str(len(CV)))
        (self.host / 'cyf-api-flow-deploy').write_text(coordinator)
        (self.host / 'cyf-api-flow-deploy').chmod(0o755)
        self.installer = self.host / 'cyf-api-flow-install'
        self.installer.write_bytes((HOST / 'cyf-api-flow-install').read_bytes()); self.installer.chmod(0o755)
        self.m = importlib.machinery.SourceFileLoader('native_unit_' + self.root.name.replace('-', '_'), str(self.host / 'cyf-api-flow-deploy')).load_module()
        self.identity = dict(version='0.0.1-synthetic', buildId='local-synthetic-1', commit='a'*40, tree='b'*40)
        self.package = self.root / 'local-package.tar'
        self.archive_mode = 'w'
        self.approval_path = self.root / 'state/approval.json'
        self.jar = self.jar_bytes()
        self.provenance = dict(coordinate='org.opencv:opencv:4.5.5', jar_sha256=sha(CV), jar_size=len(CV), resolved_file='/synthetic/not-production')
        self.prov_ref = dict(path='dependency.provenance.json', sha256=sha(encoded(self.provenance)), size=len(encoded(self.provenance)))
        self.jar_ref = dict(path='application.jar', sha256=sha(self.jar), size=len(self.jar))
        self.receipt = dict(format='cyf-api-local-release-receipt-v1', status='packaged',
            producer={'kind':'local-build-v1'}, identity=self.identity,
            source=dict(commit=self.identity['commit'], tree=self.identity['tree'], cleanBefore=True, cleanAfter=True),
            applicationJar=self.jar_ref, dependencyProvenance=self.prov_ref,
            verification={'publicArtifactVerifier':'bootJar-original-doLast-completed'},
            evidence={'tests':[dict(task=t, reports=[dict(tests=1, failures=0, errors=0, skipped=0)]) for t in
                [':agent:jia-agent-service:localReleaseBaseline', ':starter:localReleaseBaseline',
                 ':starter:publicArtifactVerifierTest', ':starter:poiProductionRuntimeClasspathTest']]})
        self.extra_members = {}
        self.seal()

    def tearDown(self): self.f.tearDown()

    def jar_bytes(self, commit=None, include_opencv=True, opencv_bytes=CV, opencv_name='opencv-4.5.5.jar'):
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            identity = self.identity
            attrs = dict(**{'Manifest-Version':'1.0', 'Main-Class':'org.springframework.boot.loader.launch.JarLauncher',
                'Start-Class':'cn.jia.JiaApplication', 'Spring-Boot-Classes':'BOOT-INF/classes/',
                'CYF-Source-Commit':commit or identity['commit'], 'CYF-Source-Tree':identity['tree'],
                'CYF-Local-Build-Id':identity['buildId'], 'CYF-Release-Version':identity['version']})
            z.writestr('META-INF/MANIFEST.MF', ''.join(k+': '+v+'\r\n' for k,v in attrs.items())+'\r\n')
            if include_opencv:
                z.writestr('BOOT-INF/lib/' + opencv_name, opencv_bytes)
        return out.getvalue()

    def seal(self, sidecar_change=None):
        receipt = encoded(self.receipt)
        binding = dict(identity=self.identity, receiptSha256=sha(receipt), applicationJar=self.jar_ref, dependencyProvenance=self.prov_ref)
        metadata = dict(format='cyf-api-local-application-metadata-v1', moduleVersion='0.0.1-synthetic', implementationVersion=None, **binding)
        sidecar = dict(format='cyf-api-local-application-sidecar-v1', **binding)
        if sidecar_change: sidecar.update(sidecar_change)
        members = dict(self.extra_members, **{'application.jar':self.jar, 'receipt.json':receipt,
            'dependency.provenance.json':encoded(self.provenance), 'application.metadata.json':encoded(metadata),
            'application.sidecar.json':encoded(sidecar)})
        with tarfile.open(self.package, self.archive_mode) as tar:
            for name,data in members.items():
                info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
        self.package.chmod(0o600)
        self.approval = dict(schema_version=4, source_kind='LOCAL', source=self.identity,
            package=dict(path=str(self.package), sha256=sha(self.package.read_bytes()), size=self.package.stat().st_size),
            receipt_sha256=sha(receipt), jar_sha256=sha(self.jar), expected_previous_sha256=sha(self.f.old), consumed=False)
        self.write_approval()

    def write_approval(self):
        self.approval_path.write_bytes(encoded(self.approval));self.approval_path.chmod(0o600)

    def install(self):
        return subprocess.run([str(self.installer)], env=self.f.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=15)

    def record(self): return json.loads((self.root/'state/record.json').read_text())

    def untouched(self, result):
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.f.target.read_bytes(), self.f.old)
        self.assertFalse((self.root/'calls').exists())
        self.assertFalse((self.root/'state/record.json').exists())

    def test_retired_schema3_descriptor_rejected_before_lifecycle(self):
        self.approval['schema_version'] = 3
        self.write_approval()
        result = self.install()
        self.untouched(result)
        self.assertIn('LOCAL_ADMISSION_RETIRED', result.stderr)

    def test_exact_local_source_reuses_original_transaction_and_backup(self):
        result=self.install();self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        r=self.record();self.m.native_record(r,self.root/'state/backups')
        self.assertEqual(r['schema_version'],4);self.assertEqual(r['source_kind'],'LOCAL');self.assertEqual(r['source'],self.identity)
        self.assertNotIn('run_id',r);self.assertNotIn('flow',r)
        self.assertEqual(r['status'],'installed');self.assertEqual(Path(r['backup']).read_bytes(),self.f.old)
        self.assertEqual(self.f.target.read_bytes(),self.jar);self.assertTrue(json.loads(self.approval_path.read_text())['consumed'])
        self.assertEqual(sha(self.package.read_bytes()),self.approval['package']['sha256'])

    def replace_jar(self, **kwargs):
        self.jar = self.jar_bytes(**kwargs)
        self.jar_ref = dict(path='application.jar', sha256=sha(self.jar), size=len(self.jar))
        self.receipt['applicationJar'] = self.jar_ref
        self.seal()

    def test_legacy_gzip_package_remains_installable(self):
        self.archive_mode = 'w:gz'
        self.seal()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.f.target.read_bytes(), self.jar)

    def test_compile_only_opencv_need_not_be_in_production_jar(self):
        self.replace_jar(include_opencv=False)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.f.target.read_bytes(), self.jar)

    def test_runtime_opencv_copy_must_keep_pinned_bytes(self):
        self.replace_jar(opencv_bytes=b'not the pinned dependency')
        self.untouched(self.install())

    def test_runtime_opencv_copy_must_keep_pinned_coordinate(self):
        self.replace_jar(opencv_name='opencv-9.9.9.jar')
        self.untouched(self.install())

    def test_idempotent_same_binding_does_not_stop_or_start_twice(self):
        first=self.install();self.assertEqual(first.returncode,0,first.stderr)
        before=(self.root/'calls').read_text().splitlines()
        second=self.install();self.assertEqual(second.returncode,0,second.stderr)
        after=(self.root/'calls').read_text().splitlines()
        self.assertEqual(after.count('stop'),before.count('stop'));self.assertEqual(after.count('start'),before.count('start'))

    def test_tampered_package_is_rejected_before_lifecycle(self):
        with self.package.open('ab') as f:f.write(b'tampered')
        self.untouched(self.install())

    def test_wrong_jar_digest_is_rejected(self):
        self.approval['jar_sha256']='f'*64;self.write_approval();self.untouched(self.install())

    def test_wrong_previous_canonical_digest_is_rejected(self):
        self.approval['expected_previous_sha256']='f'*64;self.write_approval();self.untouched(self.install())

    def test_wrong_source_identity_is_rejected(self):
        self.receipt['source']['tree']='d'*40;self.seal();self.untouched(self.install())

    def test_missing_required_test_is_rejected(self):
        self.receipt['evidence']['tests'].pop();self.seal();self.untouched(self.install())

    def test_failed_test_is_rejected(self):
        self.receipt['evidence']['tests'][0]['reports'][0]['failures']=1;self.seal();self.untouched(self.install())

    def test_all_skipped_security_task_is_rejected(self):
        self.receipt['evidence']['tests'][0]['reports'][0]['skipped']=1;self.seal();self.untouched(self.install())

    def test_sidecar_mismatch_is_rejected(self):
        self.seal({'receiptSha256':'f'*64});self.untouched(self.install())

    def test_embedded_bootjar_identity_mismatch_is_rejected(self):
        self.jar=self.jar_bytes(commit='d'*40);self.jar_ref.update(sha256=sha(self.jar),size=len(self.jar));self.seal();self.untouched(self.install())

    def test_package_symlink_is_rejected(self):
        original=self.root/'original.tgz';self.package.rename(original);self.package.symlink_to(original);self.untouched(self.install())

    def test_writable_package_is_rejected(self):
        self.package.chmod(0o666);self.untouched(self.install())

    def test_fake_flow_projection_is_rejected(self):
        self.receipt['flow']={'run_id':'123'};self.seal();self.untouched(self.install())

    def test_numeric_local_build_id_is_rejected(self):
        self.approval['source']['buildId']='123';self.write_approval();self.untouched(self.install())

    def test_traversal_member_is_rejected_before_lifecycle(self):
        self.extra_members['../escape']=b'no';self.seal();self.untouched(self.install())

    def test_duplicate_descriptor_key_is_rejected(self):
        data=encoded(self.approval).replace(b'"schema_version":4',b'"schema_version":4,"schema_version":4')
        self.approval_path.write_bytes(data);self.untouched(self.install())

    def test_consumed_active_pending_recovers_only_commit(self):
        self.f.env['CYF_API_FLOW_TEST_FAULT']='record:installed:replace'
        first=self.install();self.assertNotEqual(first.returncode,0);self.assertEqual(self.record()['status'],'active_pending')
        before=(self.root/'calls').read_text().splitlines()
        second=self.install();self.assertEqual(second.returncode,0,second.stderr)
        after=(self.root/'calls').read_text().splitlines()
        self.assertEqual(after.count('stop'),before.count('stop'));self.assertEqual(after.count('start'),before.count('start'))
        self.assertEqual(self.record()['status'],'installed')

    def test_start_failure_restores_previous_bytes_and_healthy_service(self):
        lifecycle=self.root/'bin/cyf-api-kit'
        lifecycle.write_text(lifecycle.read_text().replace('start) rm -f',
            'start) if [ -f "$root/fail-next-start" ]; then rm "$root/fail-next-start"; exit 1; fi; rm -f'))
        (self.root/'fail-next-start').touch()
        result=self.install();self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.f.target.read_bytes(),self.f.old)
        self.assertEqual(self.record()['status'],'failed');self.assertEqual(self.record()['recovery'],'restored_healthy')
        self.assertFalse((self.root/'stopped').exists())

    def test_web_verification_failure_after_forward_only_api_install(self):
        import sys
        from test_web_native_local import NativeWebTransactionTest
        site = NativeWebTransactionTest(); self.addCleanup(site.doCleanups); site.setUp()
        with mock.patch.object(sys, 'path', [str(old.ROOT/'ops/orchestration')] + sys.path):
            from local_release import api_install_descriptor
        p = dict(identity=self.identity, package=self.approval['package'], receiptSha256=self.approval['receipt_sha256'],
                 applicationJarSha256=self.approval['jar_sha256'])
        self.approval = api_install_descriptor(p, self.approval['expected_previous_sha256'], 'forward-only')
        self.write_approval(); result = self.install(); self.assertEqual(result.returncode, 0, result.stderr)
        record = self.record(); self.assertEqual((record['status'], record['rollback_policy']), ('installed', 'forward-only'))
        calls = (self.root/'calls').read_bytes()
        def assert_api_unchanged():
            self.assertEqual(self.record(), record); self.assertEqual(self.f.target.read_bytes(), self.jar)
            self.assertEqual((self.root/'calls').read_bytes(), calls)
        def public_mismatch(*args):
            self.assertEqual((site.site/'index.html').read_bytes(), site.data['index.html'])
            assert_api_unchanged(); raise SystemExit('injected public index mismatch')
        site.online.side_effect = public_mismatch
        with self.assertRaisesRegex(SystemExit, 'injected public index mismatch'): site.install()
        site.assert_old(); self.assertFalse((site.site/'assets/lazy.js').exists()); assert_api_unchanged()
        site.online.side_effect = None
        repaired = site.install(); self.assertEqual(repaired['status'], 'online_verified')
        self.assertEqual((site.site/'index.html').read_bytes(), site.data['index.html']); assert_api_unchanged()

    def test_forward_only_start_failure_never_restores_incompatible_jar(self):
        # Exercise the release controller's real descriptor, not a manually patched installer fixture.
        import sys
        with mock.patch.object(sys,'path',[str(old.ROOT/'ops/orchestration')]+sys.path):
            from local_release import api_install_descriptor
        p=dict(identity=self.identity,package=self.approval['package'],receiptSha256=self.approval['receipt_sha256'],
               applicationJarSha256=self.approval['jar_sha256'])
        prev=self.approval['expected_previous_sha256'];self.assertEqual(self.approval,api_install_descriptor(p,prev,'compatible'))
        with self.assertRaises(ValueError):api_install_descriptor(p,prev,'guess')
        self.approval=api_install_descriptor(p,prev,'forward-only'); self.write_approval()
        lifecycle=self.root/'bin/cyf-api-kit'
        lifecycle.write_text(lifecycle.read_text().replace('start) rm -f',
            'start) if [ -f "$root/fail-next-start" ]; then rm "$root/fail-next-start"; exit 1; fi; rm -f'))
        (self.root/'fail-next-start').touch()
        result=self.install(); self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.f.target.read_bytes(),self.jar)
        record=self.record(); self.m.native_record(record,self.root/'state/backups')
        self.assertEqual(record['rollback_policy'],'forward-only')
        self.assertEqual(record['recovery'],'forward_only_candidate_retained')
        self.assertTrue((self.root/'stopped').exists())
        self.assertEqual((self.root/'calls').read_text().splitlines().count('start'),1)
        # Optional bounded rendezvous with the isolated Java receiver. The parent may not
        # repair until it verified the closed listener, the untouched inbox and MySQL counts.
        if os.environ.get('CYF_TEST_PENDING_RECEIPT_WINDOW')=='1':
            import sys, select
            print('API_FORWARD_ONLY_FAILED_STOPPED',flush=True)
            self.assertTrue(select.select([sys.stdin],[],[],30)[0], 'missing receiver outage observation')
            self.assertEqual(sys.stdin.readline(),'REPAIR\n')
        # Retrying derives policy from the same durable descriptor, not env.
        again=self.install(); self.assertEqual(again.returncode,0,again.stderr)
        self.assertEqual(self.f.target.read_bytes(),self.jar)
        self.assertEqual(self.record()['status'],'installed')

    @unittest.skipUnless(os.environ.get('CYF_CUTOVER_API_RESULT_SHA'), 'requires fixed LOCAL package and isolated worker')
    def test_fixed_api_bootjar_config_failure_retains_exact_candidate(self):
        # Real JAR/installer/JVM; one deliberate Spring config failure, NOT evidence of healthy boot.
        self.assertNotEqual(os.stat('/proc/self/ns/net').st_ino,os.stat('/proc/1/ns/net').st_ino)
        self.assertNotEqual(os.stat('/proc/self/ns/mnt').st_ino,os.stat('/proc/1/ns/mnt').st_ino)
        self._fixed_api_bootjar_failure()

    def _fixed_api_bootjar_failure(self):
        import shutil, sys
        self.assertNotIn(subprocess.check_output(['stat','-f','-c','%T',self.root],text=True).strip(),('tmpfs','ramfs'))
        result_path=Path(os.environ['CYF_CUTOVER_API_RESULT']); raw=result_path.read_bytes()
        self.assertEqual(sha(raw),os.environ['CYF_CUTOVER_API_RESULT_SHA']); result=json.loads(raw)
        self.assertEqual(result['status'],'BUILT'); pkg=result['package']; self.assertIs(pkg['productionAuthorized'],False)
        archive=result_path.parent/'package/api.tar'; self.assertEqual(archive,Path(pkg['package']['path']))
        shutil.copyfile(archive,self.package); self.package.chmod(0o600)
        # Use the unmodified pinned coordinator (including real OpenCV pin) for actual release bytes.
        shutil.copyfile(HOST/'cyf-api-flow-deploy',self.host/'cyf-api-flow-deploy')
        with mock.patch.object(sys,'path',[str(old.ROOT/'ops/orchestration')]+sys.path):
            from local_release import api_install_descriptor
        self.approval=api_install_descriptor(dict(pkg,package=dict(pkg['package'],path=str(self.package))),sha(self.f.old),'forward-only')
        self.write_approval(); env=dict(self.f.env)
        for k in ('CYF_API_FLOW_TEST_TARGET_AVAILABLE_BYTES','CYF_API_FLOW_TEST_BACKUP_AVAILABLE_BYTES'):env.pop(k,None)
        kit=self.root/'bin/cyf-api-kit'; entry='start) rm -f "$root/stopped" ;;'; source=kit.read_text(); self.assertEqual(source.count(entry),1)
        kit.write_text(source.replace(entry,'start) cd "$root/service" || exit 2; exec "$JAVA_HOME/bin/java" -Xmx256m -jar cyf-api-kit.jar --spring.config.location=file:./missing-cutover-required.properties > "$root/boot.log" 2>&1 ;;'))
        res=subprocess.run([str(self.installer)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
        self.assertNotEqual(res.returncode,0)
        self.assertTrue((self.root/'state/record.json').is_file(),res.stderr[-900:])
        record=self.record(); self.assertEqual(record['status'],'failed')
        self.assertEqual(record['recovery'],'forward_only_candidate_retained'); self.assertEqual(record['rollback_policy'],'forward-only')
        with self.f.target.open('rb') as f:self.assertEqual(hashlib.file_digest(f,'sha256').hexdigest(),pkg['applicationJarSha256'])
        self.assertEqual(record['receipt_sha256'],pkg['receiptSha256']); self.assertEqual(record['source'],pkg['identity'])
        boot=(self.root/'boot.log').read_text();self.assertIn('APPLICATION FAILED TO START',boot);self.assertIn('missing-cutover-required.properties',boot)
        self.assertEqual((self.root/'calls').read_text().splitlines().count('start'),1); self.assertTrue((self.root/'stopped').exists())

        return env,pkg

    @unittest.skipUnless(os.environ.get('CYF_CUTOVER_RECOVERY')=='isolated', 'requires offline full-service namespace and fixed LOCAL package')
    def test_fixed_api_repair_reaches_real_health_after_failure(self):
        # Parent binds only test inputs and private service dependencies, never a live install tree.
        import signal, socket, sys, urllib.request
        for ns in ('pid','mnt','net'):
            self.assertNotEqual(os.stat('/proc/self/ns/'+ns).st_ino, int(os.environ['CYF_FIXTURE_PARENT_'+ns.upper()]))
        self.assertFalse(Path('/home/isp/conf').exists()); self.assertFalse(Path('/home/isp/hosts').exists())
        self.assertEqual(subprocess.check_output(['ip','route','show','default']),b'')
        env,pkg=self._fixed_api_bootjar_failure()
        before=self.record(); approval=self.approval_path.read_bytes()
        with self.assertRaises(ConnectionRefusedError):socket.create_connection(('127.0.0.1',18442),1)
        # Changing the isolated service configuration is the repair. The package, descriptor,
        # target, durable failed record, database and test namespace are NOT replaced.
        kit=self.root/'bin/cyf-api-kit';src=kit.read_text();start=src.index('start)');end=src.index(';;',start)+2
        src=src[:start]+'''start) python3 "$root/fixture-jvm.py" start "$root" || exit 1; rm -f "$root/stopped" ;;
'''+src[end:];src=src.replace('echo HEALTH=UP','exec python3 "$root/fixture-jvm.py" health "$root"');kit.write_text(src)
        (self.root/'fixture-jvm.py').write_text('''import json, os, pathlib, subprocess, sys, time, urllib.request
root=pathlib.Path(sys.argv[2]); endpoint='http://127.0.0.1:18442/actuator/health'
def healthy():
    try:
        with urllib.request.urlopen(endpoint,timeout=2) as r:
            status=json.load(r)['status'];return r.status==200 and (status.get('code') if isinstance(status,dict) else status)=='UP'
    except (ValueError,KeyError,OSError):return False
if sys.argv[1]=='health':sys.exit(0 if healthy() else 1)
with (root/'repair-boot.log').open('wb') as log:
    p=subprocess.Popen([os.environ['JAVA_HOME']+'/bin/java','-Xmx512m','-Djava.io.tmpdir=/tmp','-jar','cyf-api-kit.jar','--spring.config.additional-location=file:/work/fixture.properties','--spring.profiles.active=rb-isolated'],cwd=root/'service',stdin=subprocess.DEVNULL,stdout=log,stderr=log,close_fds=True)
(root/'repair.pid').write_text(str(p.pid));deadline=time.monotonic()+75
while p.poll() is None and time.monotonic()<deadline:
    if healthy():sys.exit(0)
    time.sleep(.25)
if p.poll() is None:p.terminate();p.wait(timeout=10)
sys.exit(1)
''')
        try:
            again=subprocess.run([str(self.installer)],env=env,capture_output=True,text=True,timeout=110)
            self.assertEqual(again.returncode,0,again.stderr[-900:]); after=self.record()
            self.assertEqual(after['status'],'installed'); self.assertEqual(after['rollback_policy'],'forward-only')
            for key in ('source','binding_sha256','receipt_sha256','candidate_sha256','previous_sha256'):
                self.assertEqual(before[key],after[key],key)
            self.assertEqual(json.loads(approval)['expected_previous_sha256'],sha(self.f.old))
            with self.f.target.open('rb') as f:self.assertEqual(hashlib.file_digest(f,'sha256').hexdigest(),pkg['applicationJarSha256'])
            with urllib.request.urlopen('http://127.0.0.1:18442/actuator/health',timeout=3) as r:
                status=json.load(r)['status']; self.assertEqual(r.status,200);self.assertEqual(status.get('code') if isinstance(status,dict) else status,'UP')
            self.assertEqual((self.root/'calls').read_text().splitlines().count('start'),2)
        finally:
            pid=self.root/'repair.pid'
            if pid.exists():
                n=int(pid.read_text());proc=Path('/proc')/str(n)
                if (proc/'cwd').exists() and (proc/'cwd').samefile(self.root/'service') and (proc/'exe').samefile(Path(env['JAVA_HOME'])/'bin/java'):
                    os.kill(n,signal.SIGTERM)

    def test_forward_only_policy_is_part_of_immutable_binding(self):
        original=self.m.native_binding(self.approval)
        self.approval['rollback_policy']='forward-only'
        self.assertNotEqual(original,self.m.native_binding(self.approval))
        self.approval['rollback_policy']='guess'
        self.write_approval(); self.untouched(self.install())

    def test_activation_crash_recovery_rolls_back_never_promotes(self):
        self.f.env['CYF_API_FLOW_TEST_FAULT']='activation:dir_fsync'
        first=self.install();self.assertNotEqual(first.returncode,0);self.assertEqual(self.record()['status'],'activating')
        self.assertEqual(self.f.target.read_bytes(),self.jar)
        second=self.install();self.assertNotEqual(second.returncode,0)
        self.assertEqual(self.record()['status'],'failed');self.assertEqual(self.record()['phase'],'activating_candidate_recovery')
        self.assertEqual(self.f.target.read_bytes(),self.f.old);self.assertFalse((self.root/'stopped').exists())

    def test_foreign_source_cannot_adopt_pending_transaction(self):
        self.f.env['CYF_API_FLOW_TEST_FAULT']='record:installed:replace'
        first=self.install();self.assertNotEqual(first.returncode,0)
        before=(self.root/'state/record.json').read_bytes();calls=(self.root/'calls').read_bytes()
        self.approval['source']['buildId']='local-foreign';self.write_approval()
        result=self.install();self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.root/'state/record.json').read_bytes(),before);self.assertEqual((self.root/'calls').read_bytes(),calls)

    def test_coordinator_uses_same_mutex_and_installer_without_flow_schema_hooks(self):
        m=self.m;m.ROOT=self.root/'state';m.APPROVAL=self.approval_path;m.BACKUPS=self.root/'state/backups'
        m.LOCK=str(self.root/'coordinator.lock');m.INSTALLER=str(self.installer)
        descriptor=self.root/'descriptor.json';descriptor.write_bytes(encoded(self.approval));descriptor.chmod(0o600)
        with mock.patch.dict(os.environ,self.f.env), mock.patch.object(m,'apply_schema_after_install',side_effect=AssertionError('no LOCAL schema hook')):
            self.assertEqual(m.native_api_main([str(descriptor)]),0)
        self.assertEqual(self.record()['source_kind'],'LOCAL')

    def test_read_atime_is_not_mistaken_for_content_mutation(self):
        before=self.package.stat()
        os.utime(self.package, ns=(1, before.st_mtime_ns))
        self.m.native_package(self.approval)
        self.assertEqual(self.package.stat().st_mtime_ns,before.st_mtime_ns)
        before=self.approval_path.stat()
        os.utime(self.approval_path, ns=(1, before.st_mtime_ns))
        self.m.native_read_approval(self.approval_path)

    def test_source_keeps_real_opencv_pin_and_retired_modes_closed(self):
        text=(HOST/'cyf-api-flow-deploy').read_text()
        self.assertIn(PIN,text);self.assertIn("'--source-local'",text)
        self.assertIn("'LOCAL_ADMISSION_RETIRED'",text)
        self.assertNotIn('local_install_decision(',text[text.index('# BEGIN NATIVE_LOCAL_SOURCE_V1'):])

if __name__=='__main__':unittest.main()
