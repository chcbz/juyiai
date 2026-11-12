"""Local control-plane regression only; never deploy or touch production state."""
import contextlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
HOST = ROOT / 'ops/ci/aliyun-flow/host'
deploy = importlib.machinery.SourceFileLoader('retired_local_control', str(HOST/'cyf-api-flow-deploy')).load_module()

class LocalAdmissionRetiredTest(unittest.TestCase):
    def test_all_old_cli_modes_fail_closed(self):
        for mode in ('--local-inspect','--local-install','--local-offline-maintenance','--local-offline-recover-maintenance'):
            out=io.StringIO()
            with contextlib.redirect_stdout(out): rc=deploy.local_main([mode])
            self.assertEqual(rc,1)
            self.assertEqual(json.loads(out.getvalue())['error'],'LOCAL_ADMISSION_RETIRED')

    def test_local_publication_and_mutators_removed(self):
        for name in ('LocalReadSet','local_read_install_inputs','local_verify_publication','local_install','local_offline_session'):
            self.assertFalse(hasattr(deploy,name), name)
        self.assertFalse((HOST/'cyf-api-local-admit').exists())
        self.assertFalse((ROOT/'ops/ci/aliyun-flow/auto/admit-api-local.py').exists())

    def test_historical_record_parser_still_available(self):
        self.assertTrue(callable(deploy.local_install_record))
        self.assertTrue(callable(deploy.local_json))

    def installer_fixture(self, base):
        base.chmod(0o700)
        for p in ['state/incoming','service','bin']: (base/p).mkdir(parents=True,mode=0o700)
        lock=base/'cyf-release-api.lock'; lock.touch(mode=0o600)
        target=base/'service/cyf-api-kit.jar'; target.write_bytes(b'unchanged-production-fixture')
        kit=base/'bin/cyf-api-kit'; kit.write_text('#!/bin/sh\ntouch "'+str(base/'lifecycle-called')+'"\nexit 0\n'); kit.chmod(0o700)
        package=base/'state/incoming/package.tgz'
        with tarfile.open(str(package),'w:gz') as tar:
            for name in ['application.jar','application.metadata.json','application.sidecar.json','dependency.provenance.json','receipt.json']:
                data=b'{}'; info=tarfile.TarInfo(name); info.size=len(data); tar.addfile(info,io.BytesIO(data))
        package.chmod(0o600)
        approval=base/'state/approval.json'; approval.write_text('{"schema_version":3}'); approval.chmod(0o600)
        env=dict(os.environ,CYF_RELEASE_OFFLINE_TEST='YES',CYF_API_FLOW_INSTALL_TEST_ROOT=str(base))
        env.pop('CYF_API_LOCAL_OFFLINE_RECEIPT',None)
        return env,target

    def test_installer_rejects_local_approval_before_lifecycle_or_record(self):
        with tempfile.TemporaryDirectory(prefix='cyf-retired-unit-',dir='/tmp') as t:
            base=Path(t);env,target=self.installer_fixture(base)
            result=subprocess.run([str(HOST/'cyf-api-flow-install')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('LOCAL_ADMISSION_RETIRED',result.stderr)
            self.assertFalse((base/'lifecycle-called').exists())
            self.assertFalse((base/'state/record.json').exists())
            self.assertEqual(target.read_bytes(),b'unchanged-production-fixture')

    def test_installer_rejects_old_offline_maintenance_marker(self):
        with tempfile.TemporaryDirectory(prefix='cyf-retired-unit-',dir='/tmp') as t:
            base=Path(t);env,target=self.installer_fixture(base)
            env['CYF_API_LOCAL_OFFLINE_RECEIPT']='/not-used'
            result=subprocess.run([str(HOST/'cyf-api-flow-install')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('LOCAL_ADMISSION_RETIRED',result.stderr)
            self.assertFalse((base/'lifecycle-called').exists())
            self.assertFalse((base/'state/record.json').exists())

if __name__=='__main__': unittest.main()
