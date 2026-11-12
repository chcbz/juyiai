import contextlib
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[4]
OPS = ROOT / 'ops/ci/aliyun-flow'


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(path)).load_module()


class AutoReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-auto-test-')
        self.root = Path(self.tmp.name)
        self.api = load('api_deploy', OPS/'host/cyf-api-flow-deploy')
        self.web = load('web_deploy', OPS/'host/cyf-web-flow-deploy')
        self.commit = 'a'*40

    def tearDown(self):
        self.tmp.cleanup()

    def web_package(self, bad_hash=False, wrong_source=False, package_version=None):
        self.web.ROOT = self.root/'web-state'
        self.web.ROOT.mkdir(mode=0o700)
        self.web.SITE = self.root/'site'
        self.web.SITE.mkdir()
        (self.web.SITE/'index.html').write_bytes(b'old')
        download = self.web.ROOT/'downloads/92'
        download.mkdir(parents=True)
        content = {'index.html':b'<html>new</html>', 'assets/a.js':b'new javascript'}
        manifest = dict(schema_version=1, pipeline_id='4403172', run_id='92', branch='develop',
                        commit='b'*40 if wrong_source else self.commit,
                        files=[dict(path=p,size=len(v),sha256='0'*64 if bad_hash else hashlib.sha256(v).hexdigest()) for p,v in content.items()])
        package_version = package_version or '1.0.0'
        manifest['package_version'] = package_version
        self.web_release_version = package_version
        with tarfile.open(str(download/'package.tgz'), 'w:gz') as archive:
            for p,v in [('release.json',json.dumps(manifest).encode())]+[('dist/'+p,v) for p,v in content.items()]+[('mochawesome-report/mochawesome.html',b'private test report')]:
                member=tarfile.TarInfo(p); member.size=len(v);archive.addfile(member,io.BytesIO(v))
        self.web_release_digest = hashlib.sha256((download/'package.tgz').read_bytes()).hexdigest()
        return content

    def test_web_same_run_installs_only_dist(self):
        files = self.web_package()
        with mock.patch.object(self.web.urllib.request,'urlopen',return_value=io.BytesIO(files['index.html'])):
            self.web.deploy('4403172','92',self.commit,self.web_release_version,self.web_release_digest)
        for p,v in files.items(): self.assertEqual((self.web.SITE/p).read_bytes(),v)
        self.assertFalse((self.web.SITE/'mochawesome-report').exists())

    def test_web_hash_failure_does_not_publish(self):
        self.web_package(bad_hash=True)
        with self.assertRaisesRegex(SystemExit,'digest mismatch'):
            self.web.deploy('4403172','92',self.commit,self.web_release_version,self.web_release_digest)
        self.assertEqual((self.web.SITE/'index.html').read_bytes(),b'old')

    def test_web_wrong_source_does_not_publish(self):
        self.web_package(wrong_source=True)
        with self.assertRaisesRegex(SystemExit,'does not match'):
            self.web.deploy('4403172','92',self.commit,self.web_release_version,self.web_release_digest)
        self.assertEqual((self.web.SITE/'index.html').read_bytes(),b'old')

    def test_web_old_run_does_not_publish(self):
        self.web_package()
        (self.web.ROOT/'record.json').write_text('{"run_id":"93"}')
        with self.assertRaisesRegex(SystemExit,'older'):
            self.web.deploy('4403172','92',self.commit,self.web_release_version,self.web_release_digest)

    def test_web_major_release_no_longer_needs_nightly_intent(self):
        files = self.web_package(package_version='1.2.0')
        (self.web.ROOT/'record.json').write_text(json.dumps({
            'run_id': '91', 'package_version': '1.0.7', 'files': []}))
        with mock.patch.object(self.web.urllib.request, 'urlopen', return_value=io.BytesIO(files['index.html'])):
            self.web.deploy('4403172', '92', self.commit,self.web_release_version,self.web_release_digest)
        self.assertEqual((self.web.SITE/'index.html').read_bytes(), files['index.html'])

    def make_bootjar(self, path, omitted=(), test_only=False):
        packager = load('api_packager', OPS/'auto/package-api.py')
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, 'w') as dependency:
            for name in packager.REQUIRED_MAIL_RUNTIME_CLASSES - set(omitted):
                dependency.writestr(name, b'offline class fixture')
        with zipfile.ZipFile(str(path), 'w') as boot:
            boot.writestr(('test-libs/' if test_only else 'BOOT-INF/lib/') + 'mail.jar', nested.getvalue())
        return packager

    def test_bootjar_mail_runtime_all_present(self):
        jar = self.root/'good.jar'
        packager = self.make_bootjar(jar)
        self.assertEqual(set(packager.verify_mail_runtime(jar)), packager.REQUIRED_MAIL_RUNTIME_CLASSES)

    def test_bootjar_missing_mail_or_activation_fails(self):
        for missing in ('javax/mail/MessagingException.class', 'javax/activation/DataHandler.class'):
            jar = self.root/'missing.jar'
            packager = self.make_bootjar(jar, omitted=(missing,))
            with self.assertRaisesRegex(SystemExit, 'missing required mail runtime'):
                packager.verify_mail_runtime(jar)

    def test_test_only_mail_dependency_cannot_pass_bootjar(self):
        jar = self.root/'test-only.jar'
        packager = self.make_bootjar(jar, test_only=True)
        with self.assertRaisesRegex(SystemExit, 'missing required mail runtime'):
            packager.verify_mail_runtime(jar)

    def test_invalid_bootjar_fails(self):
        jar = self.root/'invalid.jar'
        jar.write_bytes(b'not a bootJar')
        packager = load('api_packager', OPS/'auto/package-api.py')
        with self.assertRaisesRegex(SystemExit, 'invalid bootJar runtime archive'):
            packager.verify_mail_runtime(jar)

    def test_flow_embeds_exact_packager_before_upload(self):
        import textwrap
        pipeline = (OPS/'templates/backend-develop-release.yaml').read_text()
        marker = "                python3 - <<'PYARTIFACT'\n"
        embedded = pipeline.split(marker, 1)[1].split('                PYARTIFACT', 1)[0]
        self.assertEqual(textwrap.dedent(embedded), (OPS/'auto/package-api.py').read_text())
        source = (OPS/'auto/package-api.py').read_text()
        self.assertLess(source.index('mail_runtime = verify_mail_runtime(jars[0])'), source.index('out.mkdir('))

    def api_package(self):
        repo = self.root/'repo';repo.mkdir()
        for cmd in [['git','init','-q'],['git','config','user.email','fixture@example.invalid'],['git','config','user.name','fixture']]:
            subprocess.check_call(cmd,cwd=str(repo))
        (repo/'README').write_text('source')
        subprocess.check_call(['git','add','README'],cwd=str(repo))
        subprocess.check_call(['git','commit','-qm','fixture'],cwd=str(repo))
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=str(repo)).decode().strip()
        build=repo/'_cyf_flow_build';(build/'jia/starter/libs').mkdir(parents=True)
        self.make_bootjar(build/'jia/starter/libs/fixture.jar')
        (build/'opencv-resolved.json').write_text(json.dumps(dict(jar_sha256='323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4',jar_size=722802)))
        env=dict(os.environ,PIPELINE_ID='5260799',BUILD_NUMBER='20',CI_COMMIT_REF_NAME='develop',CI_COMMIT_SHA=commit,CYF_SOURCE_CLEAN_BEFORE='1')
        subprocess.check_call(['python3',str(OPS/'auto/package-api.py')],cwd=str(repo),env=env,stdout=subprocess.DEVNULL)
        out=repo/'_cyf_api_flow_export'
        return repo,out,commit,env

    def test_api_package_binds_exact_metadata(self):
        _,out,commit,_=self.api_package()
        receipt=json.loads((out/'receipt.json').read_text())
        self.assertEqual(receipt['source']['commit_sha'],commit)
        self.assertEqual(len(list(out.iterdir())),5)
        digest=hashlib.sha256((out/'receipt.json').read_bytes()).hexdigest()
        for name in ['application.metadata.json','application.sidecar.json']:
            self.assertEqual(json.loads((out/name).read_text())['receipt_sha256'],digest)

    def test_api_dirty_source_fails_before_export(self):
        repo,out,commit,env=self.api_package()
        (repo/'README').write_text('dirty')
        result=subprocess.run(['python3',str(OPS/'auto/package-api.py')],cwd=str(repo),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'CalledProcessError',result.stderr)

    def test_api_auto_identity_and_reject_wrong_source(self):
        _,out,commit,_=self.api_package()
        state=self.root/'api-state';state.mkdir(mode=0o700)
        incoming=state/'incoming';incoming.mkdir(mode=0o700)
        download=state/'downloads/20';download.mkdir(parents=True)
        self.api.ROOT=state;self.api.PACKAGE=incoming/'package.tgz';self.api.APPROVAL=state/'approval.json'
        self.api.BACKUPS=state/'backups';self.api.LOCK=str(state/'lock')
        self.api.INSTALLER=str(OPS/'host/cyf-api-flow-deploy')
        with tarfile.open(str(download/'package.tgz'),'w:gz') as archive:
            for p in out.iterdir():archive.add(str(p),arcname=p.name)
        # Run in a child: mock exec prevents any service action, all filesystem checks run.
        script="""
import importlib.machinery, sys
from pathlib import Path
m=importlib.machinery.SourceFileLoader('fixture',sys.argv[1]).load_module()
s=Path(sys.argv[2]);m.ROOT=s;m.PACKAGE=s/'incoming/package.tgz';m.APPROVAL=s/'approval.json';m.BACKUPS=s/'backups';m.LOCK=str(s/'lock');m.INSTALLER=sys.argv[1]
commit=sys.argv[3]
digest=__import__('hashlib').sha256((s/'downloads/20/package.tgz').read_bytes()).hexdigest()
sys.argv=['fixture','5260799','20',commit,'1.2.0',digest]
def done(installer):
    return 0
m.invoke_installer=done
m.main()
"""
        result=subprocess.run(['python3','-c',script,str(OPS/'host/cyf-api-flow-deploy'),str(state),commit],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertEqual(result.returncode,0,result.stderr.decode())
        self.assertFalse((download/'package.tgz').exists())
        self.assertTrue((incoming/'package.tgz').is_file())
        approval=json.loads((state/'approval.json').read_text())
        self.assertEqual(approval['source_commit_sha'],commit)
        # A retrying Flow deployment downloads again; retain fail-closed source mismatch coverage.
        import shutil
        shutil.copyfile(str(incoming/'package.tgz'), str(download/'package.tgz'))
        result=subprocess.run(['python3','-c',script,str(OPS/'host/cyf-api-flow-deploy'),str(state),'b'*40],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'source identity mismatch',result.stderr)

    def test_duplicate_cleanup_rejects_mismatch_without_deleting(self):
        source = self.root/'download.tgz'; source.write_bytes(b'original')
        copy = self.root/'incoming.tgz'; copy.write_bytes(b'different'); copy.chmod(0o600)
        with self.assertRaisesRegex(SystemExit, 'digest mismatch before cleanup'):
            self.api.discard_verified_download_copy(source, copy, source.stat())
        self.assertEqual(source.read_bytes(), b'original')
        self.assertEqual(copy.read_bytes(), b'different')

    def test_duplicate_cleanup_rejects_changed_download(self):
        source = self.root/'download.tgz'; source.write_bytes(b'original')
        old = source.stat()
        source.write_bytes(b'changed bytes')
        copy = self.root/'incoming.tgz'; copy.write_bytes(b'changed bytes'); copy.chmod(0o600)
        with self.assertRaisesRegex(SystemExit, 'download changed before'):
            self.api.discard_verified_download_copy(source, copy, old)
        self.assertTrue(source.exists())

    def test_installer_child_does_not_inherit_coordinator_lock(self):
        import fcntl
        lock = self.root/'coordinator.lock'
        fd = os.open(str(lock), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.set_inheritable(fd, True)  # exercise close_fds even against an unsafe caller
        child = self.root/'installer-fixture'
        child.write_text("#!/usr/bin/python3\nimport os,fcntl\np=" + repr(str(lock)) + "\n"
                         "target=os.stat(p)\n"
                         "for name in os.listdir('/proc/self/fd'):\n"
                         " try: st=os.stat('/proc/self/fd/'+name)\n"
                         " except OSError: continue\n"
                         " assert (st.st_dev,st.st_ino)!=(target.st_dev,target.st_ino)\n"
                         "fd=os.open(p,os.O_RDWR)\n"
                         "try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                         "except BlockingIOError: pass\n"
                         "else: raise SystemExit('parent lost mutex while child running')\n")
        child.chmod(0o755)
        try:
            self.assertEqual(self.api.invoke_installer(str(child)), 0)
        finally:
            os.close(fd)

    def test_installer_native_failure_is_preserved(self):
        child = self.root/'failed-installer'
        child.write_text('#!/bin/sh\nexit 7\n'); child.chmod(0o755)
        self.assertEqual(self.api.invoke_installer(str(child)), 7)

    def test_develop_templates_verify_without_deployment(self):
        for name in ['backend-develop-release.yaml','frontend-develop-release.yaml']:
            text=(OPS/'templates'/name).read_text()
            self.assertIn('branch: develop',text)
            self.assertIn('branchesFilter: ^develop$',text)
            self.assertIn('- push',text)
            self.assertNotIn('component: VMDeploy',text)
            self.assertNotIn('  deploy:',text)
            self.assertIn('step: ArtifactUpload',text)
            self.assertNotIn('TICKET_ZLIB_B64',text)
            self.assertNotIn('release_guard',text)
            self.assertNotIn('FirstBatchPause',text)
            self.assertNotIn('cyf-api-flow-deploy',text)
            self.assertNotIn('cyf-web-flow-deploy',text)
        api=(OPS/'templates/backend-develop-release.yaml').read_text()
        # Required regression selectors matter; an arbitrary total must not reject new tests.
        for selector in (
            'cn.jia.agent.api.AgentCommandOperationsControllerTest',
            'cn.jia.agent.dao.AgentCommandOperationsMapperContractTest',
            'cn.jia.agent.service.impl.AgentCommandOperationV1ProjectorTest',
            'cn.jia.agent.service.impl.AgentCommandOperationsServiceImplTest',
            'cn.jia.agent.service.impl.AgentSceneServiceImplTest',
            'cn.jia.agent.dao.AgentSceneScopedDaoTest',
            'cn.jia.core.amqp.RabbitMqBudgetConfigurationTest',
            'cn.jia.config.ApiPerformanceMetricsConfigTest',
            'cn.jia.config.SmsEmailRuntimeClasspathTest',
            'cn.jia.chat.ai.BudgetedChatModelTest',
            'cn.jia.user.service.impl.UserServiceImplTest',
        ):
            self.assertIn('--tests ' + selector + ' ', api)
        self.assertLess(api.index(':starter:bootJar'),api.index("python3 - <<'PYARTIFACT'"))


if __name__=='__main__':unittest.main()
