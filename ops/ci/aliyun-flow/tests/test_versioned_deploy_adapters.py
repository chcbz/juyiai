"""Bounded offline adapter tests. No app, provider, DB, or service operations."""
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[4] if 'CYF_ADAPTER_TEST_ROOT' not in os.environ else None
HOST = Path(os.environ['CYF_ADAPTER_TEST_ROOT']) if ROOT is None else ROOT / 'ops/ci/aliyun-flow/host'


class VersionedAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cyf-versioned-fixture-')
        self.root = Path(self.temp.name)
        self.api = importlib.machinery.SourceFileLoader('version_api', str(HOST/'cyf-api-flow-deploy')).load_module()
        self.web = importlib.machinery.SourceFileLoader('version_web', str(HOST/'cyf-web-flow-deploy')).load_module()
        self.commit = 'a'*40
        self.version = '1.2.0'

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, path, values):
        with tarfile.open(str(path), 'w:gz') as archive:
            for name, value in values.items():
                member = tarfile.TarInfo(name);member.size=len(value)
                archive.addfile(member, io.BytesIO(value))
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def web_fixture(self, run='92', commit=None, version=None, bad_file=False, branch='develop'):
        self.web.ROOT=self.root/'web';self.web.ROOT.mkdir(mode=0o700)
        self.web.SITE=self.root/'site';self.web.SITE.mkdir(mode=0o700)
        (self.web.SITE/'index.html').write_bytes(b'old')
        package=self.web.ROOT/'downloads'/'92'/'package.tgz';package.parent.mkdir(parents=True)
        content=b'<html>new</html>'
        manifest=dict(schema_version=1,pipeline_id='4403172',run_id=run,branch=branch,
                      commit=commit or self.commit,package_version=version or self.version,
                      files=[dict(path='index.html',size=len(content),sha256='0'*64 if bad_file else hashlib.sha256(content).hexdigest())])
        digest=self.archive(package,{'release.json':json.dumps(manifest).encode(),'dist/index.html':content})
        return digest,content

    def api_fixture(self, run='20', commit=None):
        state=self.root/'api';state.mkdir(mode=0o700)
        (state/'incoming').mkdir(mode=0o700)
        package=state/'downloads'/'20'/'package.tgz';package.parent.mkdir(parents=True)
        jar=b'synthetic-jar-not-executable';provenance=b'{}'
        source=dict(branch='develop',commit_sha=commit or self.commit,tree_sha='b'*40,clean_before=True,clean_after=True)
        flow=dict(organization_id=self.api.EXPECTED_ORG,pipeline_id='5260799',run_id=run,job_id=self.api.EXPECTED_JOB,source_tip_sha=source['commit_sha'])
        identity=hashlib.sha256((json.dumps(dict(flow=flow,source=source),sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
        receipt=dict(schema_version=1,status='success',gradle_exit_code=0,bridge_exit_code=0,ticket_sha256=identity,flow=flow,source=source,
                     files=[dict(kind='application_jar',path='application.jar',sha256=hashlib.sha256(jar).hexdigest(),size=len(jar)),
                            dict(kind='dependency_provenance',path='dependency.provenance.json',sha256=hashlib.sha256(provenance).hexdigest(),size=len(provenance))])
        digest=self.archive(package,{'application.jar':jar,'dependency.provenance.json':provenance,
                    'receipt.json':json.dumps(receipt).encode(),'application.metadata.json':b'{}','application.sidecar.json':b'{}'})
        self.api.ROOT=state;self.api.PACKAGE=state/'incoming/package.tgz';self.api.APPROVAL=state/'approval.json'
        self.api.BACKUPS=state/'backups';self.api.LOCK=str(state/'deploy.lock')
        self.api.INSTALLER=str(HOST/'cyf-api-flow-deploy')
        return digest

    def api_call(self, digest, code=0, version=None):
        with mock.patch.object(sys,'argv',['fixture','5260799','20',self.commit,version or self.version,digest]), \
             mock.patch.object(self.api,'invoke_installer',return_value=code) as installer:
            with self.assertRaises(SystemExit) as raised:self.api.main()
        return raised.exception.code,installer

    def test_requires_explicit_version_and_digest(self):
        for module in [self.api,self.web]:
            for version,digest in [('', 'a'*64),(' x','a'*64),('x\n','a'*64),('x',''),('x','b'*63)]:
                with self.assertRaises(SystemExit):module.validate_versioned_release(version,digest)
            self.assertEqual('1.2.0-rc.1',module.validate_versioned_release('1.2.0-rc.1','a'*64))

    def test_legacy_three_argument_cli_cannot_deploy(self):
        for module in [self.api,self.web]:
            source=Path(module.__file__).read_text()
            self.assertIn('len(sys.argv) != 6',source)
            self.assertNotIn('nightly_intent',source)
            self.assertNotIn('SCHEDULE_INTENTS',source)

    def test_web_major_version_needs_no_midnight_intent(self):
        digest,content=self.web_fixture()
        (self.web.ROOT/'record.json').write_text(json.dumps({'run_id':'91','package_version':'1.0.0','files':[]}))
        with mock.patch.object(self.web,'verify_online_index') as health:
            self.web.deploy('4403172','92',self.commit,self.version,digest)
        health.assert_called_once();self.assertEqual(content,(self.web.SITE/'index.html').read_bytes())
        record=json.loads((self.web.ROOT/'record.json').read_text())
        self.assertEqual(self.version,record['release_version']);self.assertEqual(digest,record['artifact_sha256'])
        self.assertEqual('online_verified',record['status'])

    def test_web_source_branch_is_provenance_not_allowlist(self):
        branch = 'codex/new-unlisted-release'
        digest, content = self.web_fixture(branch=branch)
        with mock.patch.object(self.web, 'verify_online_index'):
            self.web.deploy('4403172', '92', self.commit, self.version, digest)
        record = json.loads((self.web.ROOT/'record.json').read_text())
        self.assertEqual(branch, record['branch'])
        self.assertEqual(content, (self.web.SITE/'index.html').read_bytes())

    def test_web_wrong_version_never_publishes(self):
        digest,_=self.web_fixture()
        with self.assertRaisesRegex(SystemExit,'release version differs'):
            self.web.deploy('4403172','92',self.commit,'1.3.0',digest)
        self.assertEqual(b'old',(self.web.SITE/'index.html').read_bytes())

    def test_web_wrong_archive_digest_never_publishes(self):
        self.web_fixture()
        with self.assertRaisesRegex(SystemExit,'artifact digest mismatch'):
            self.web.deploy('4403172','92',self.commit,self.version,'0'*64)
        self.assertEqual(b'old',(self.web.SITE/'index.html').read_bytes())

    def test_web_wrong_run_never_publishes(self):
        digest,_=self.web_fixture(run='93')
        with self.assertRaisesRegex(SystemExit,'does not match'):
            self.web.deploy('4403172','92',self.commit,self.version,digest)

    def test_web_wrong_commit_never_publishes(self):
        digest,_=self.web_fixture(commit='c'*40)
        with self.assertRaisesRegex(SystemExit,'does not match'):
            self.web.deploy('4403172','92',self.commit,self.version,digest)

    def test_web_file_digest_still_checked(self):
        digest,_=self.web_fixture(bad_file=True)
        with self.assertRaisesRegex(SystemExit,'dist digest mismatch'):
            self.web.deploy('4403172','92',self.commit,self.version,digest)

    def test_web_old_run_still_rejected(self):
        digest,_=self.web_fixture();(self.web.ROOT/'record.json').write_text('{"run_id":"93"}')
        with self.assertRaisesRegex(SystemExit,'older'):
            self.web.deploy('4403172','92',self.commit,self.version,digest)

    def test_api_version_run_commit_archive_bound_without_midnight(self):
        digest=self.api_fixture();code,installer=self.api_call(digest)
        self.assertEqual(0,code);installer.assert_called_once()
        record=json.loads((self.api.ROOT/'versioned-release-20.json').read_text())
        self.assertEqual(self.version,record['version']);self.assertEqual(self.commit,record['commit'])
        self.assertEqual('20',record['run_id']);self.assertEqual(digest,record['artifact_sha256'])
        self.assertEqual('verified',record['status'])

    def test_api_failed_installer_not_reported_verified(self):
        digest=self.api_fixture();code,installer=self.api_call(digest,code=7)
        self.assertEqual(7,code)
        self.assertEqual('failed',json.loads((self.api.ROOT/'versioned-release-20.json').read_text())['status'])

    def test_api_wrong_archive_digest_no_installer(self):
        self.api_fixture();code,installer=self.api_call('0'*64)
        self.assertIn('artifact digest mismatch',code);installer.assert_not_called()
        self.assertFalse(self.api.APPROVAL.exists())

    def test_api_wrong_run_no_installer(self):
        digest=self.api_fixture(run='21');code,installer=self.api_call(digest)
        self.assertIn('Flow identity mismatch',code);installer.assert_not_called()

    def test_api_wrong_commit_no_installer(self):
        digest=self.api_fixture(commit='c'*40);code,installer=self.api_call(digest)
        self.assertIn('source identity mismatch',code);installer.assert_not_called()

    def test_web_mutex_waits_instead_of_preempting(self):
        source=Path(self.web.__file__).read_text()
        self.assertIn('fcntl.flock(lock, fcntl.LOCK_EX)',source)
        self.assertNotIn('fcntl.LOCK_EX | fcntl.LOCK_NB',source)


if __name__=='__main__':unittest.main()
