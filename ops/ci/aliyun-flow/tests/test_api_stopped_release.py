"""Synthetic stopped-release guards; no production reads/writes or processes."""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

PATH = pathlib.Path(__file__).resolve().parents[1]/'host/cyf-api-flow-deploy'
m = {'__name__':'stopped_release_test','__file__':str(PATH)}
exec(compile(PATH.read_text(),str(PATH),'exec'),m)

class StoppedReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.proc=self.root/'proc';self.proc.mkdir()
        (self.proc/'net').mkdir();(self.proc/'sys/kernel/random').mkdir(parents=True)
        (self.proc/'sys/kernel/random/boot_id').write_text('12345678-1234-1234-1234-123456789012\n')
        for name in ('tcp','tcp6'):(self.proc/'net'/name).write_text('header\n')
        self.jar=self.root/'api/app.jar';self.jar.parent.mkdir();self.jar.write_bytes(b'fixture')
        self.guard=patch.dict(m,LOCAL_STOPPED_PROC=self.proc,ROOT=self.root,local_read_slot=lambda *a,**k:None)
        self.guard.start();self.addCleanup(self.guard.stop)
        self.source={'kind':'local-build-v1','identity':{'version':'synthetic'}}
        self.ref={'path':'/synthetic/proof','sha256':'a'*64,'size':1}
        self.pre={'runtimeGeneration':None,'canonicalJarSha256':'b'*64,'installedRecord':self.ref,'stoppedRecovery':self.ref}
        self.proof={'format':'cyf-api-local-stopped-observation-v1','source':self.source,'canonicalJarSha256':'b'*64,'installedRecord':self.ref,'observation':m['local_stopped_observation'](self.jar)}
        self.auth={'source':self.source,'stoppedRecoveryAuthorized':True,'productionAuthorized':True}
    def check(self):
        class Reader:
            def checked(_,r):return json.dumps(self.auth if r=='auth' else self.proof).encode()
            def recheck(_):pass
        return m['local_assert_stopped_generation']({'decision':{'source':self.source,'precondition':self.pre},'authority':{'authorizationEvidence':'auth'},'reader':Reader()},self.jar)
    def rejected(self):
        with self.assertRaises(m['LocalRejected']):self.check()
    def test_explicit_stopped_proof_passes(self):self.check()
    def test_authorization_required(self):self.auth['stoppedRecoveryAuthorized']=False;self.rejected()
    def test_other_candidate_rejected(self):self.auth['source']={};self.rejected()
    def test_boot_change_rejected(self):self.proof['observation']['bootId']='different';self.rejected()
    def test_record_change_rejected(self):self.proof['installedRecord']=None;self.rejected()
    def test_live_generation_cannot_be_disguised(self):self.pre['runtimeGeneration']={'pid':42};self.rejected()
    def test_offline_session_cannot_be_combined(self):self.pre['offlineMaintenance']=self.ref;self.rejected()
    def test_runtime_record_blocks(self):
        with patch.dict(m,local_read_slot=lambda *a,**k:b'active'):self.rejected()
    def test_existing_maintenance_blocks(self):(self.root/'offline-maintenance-active.json').write_text('{}');self.rejected()
    def test_tcp_listeners_block_ipv4_and_ipv6(self):
        for name in ('tcp','tcp6'):
            with self.subTest(name=name):
                p=self.proc/'net'/name;p.write_text('header\n0: 00000000:2722 00000000:0000 0A\n');self.rejected();p.write_text('header\n')
    def test_relative_canonical_process_blocks(self):
        p=self.proc/'42';p.mkdir();(p/'cmdline').write_bytes(b'java\0-jar\0app.jar\0');(p/'cwd').symlink_to(self.jar.parent);self.rejected()
    def test_unrelated_process_allowed(self):
        p=self.proc/'42';p.mkdir();(p/'cmdline').write_bytes(b'java\0-jar\0/other/service.jar\0');(p/'cwd').symlink_to(self.root);self.check()
    def test_surviving_opaque_process_blocks(self):
        p=self.proc/'42';p.mkdir();self.rejected()
    def test_null_generation_without_explicit_mode_rejected(self):
        p=dict(self.pre,approval=None,identityInventory=self.ref,inflightInventory=self.ref,schemaInventory=self.ref);p.pop('stoppedRecovery')
        with self.assertRaises(m['LocalRejected']):m['local_precondition'](p)
    def test_default_live_guard_is_still_dispatch_target(self):
        import inspect
        source=PATH.read_text()
        self.assertIn("else:\n        local_assert_runtime_generation(precondition['runtimeGeneration'], jar_path)",source)

if __name__=='__main__':unittest.main()
