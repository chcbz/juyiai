"""LOCAL Web archive/manifest boundary only; never writes the production site."""
import hashlib,io,json,tarfile,tempfile,unittest
from pathlib import Path
from test_web_flow_cache_verifier import load


class NativeWebManifestTest(unittest.TestCase):
    def setUp(self):
        self.web=load();self.tmp=tempfile.TemporaryDirectory(prefix='cyf-web-local-unit-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data={'index.html':b'<html>local</html>', 'assets/main.js':b'console.log(1)'}
        self.manifest=dict(format='cyf-local-web-build-v2',buildId='local-fixture',source=dict(commit='a'*40,tree='b'*40),version='1.2.3',scope='selected fixture tests',tests=dict(reportSha256='c'*64,selector=['unit'],stats=dict(tests=3,passes=2,pending=1,failures=0)),files={n:dict(size=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in self.data.items()})

    def validate(self, extra=()):
        out=io.BytesIO()
        with tarfile.open(fileobj=out,mode='w:gz') as tar:
            for n,b in list(self.data.items())+[('cyf-local-build.json',json.dumps(self.manifest).encode())]+list(extra):
                m=tarfile.TarInfo(n);m.size=len(b);tar.addfile(m,io.BytesIO(b))
        out.seek(0);manifest,staged=self.web.scan_archive(out,self.root,local=True)
        return self.web.validate_local_manifest(manifest,staged)

    def test_real_local_identity_has_no_fake_flow_fields(self):
        r,e=self.validate();self.assertEqual(r['source_kind'],'LOCAL');self.assertNotIn('run_id',r);self.assertNotIn('pipeline_id',r);self.assertEqual(set(e),set(self.data))
    def test_optional_shared_dependency_provenance_is_compatible(self):
        self.manifest['dependencies']=dict(key='d'*64,receiptSha256='e'*64)
        r,_=self.validate();self.assertEqual(r['dependencies'],self.manifest['dependencies'])
    def test_optional_dependency_metadata_cannot_override_source(self):
        self.manifest['dependencies']=dict(source=dict(commit='f'*40),run='fake informational label')
        r,_=self.validate();self.assertEqual(r['source']['commit'],'a'*40);self.assertNotIn('run_id',r)
    def test_failed_tests_rejected(self):
        self.manifest['tests']['stats']['failures']=1
        with self.assertRaises(SystemExit):self.validate()
    def test_unexecuted_tests_rejected(self):
        self.manifest['tests']['stats'].update(tests=1,passes=0,pending=1)
        with self.assertRaises(SystemExit):self.validate()
    def test_boolean_count_rejected(self):
        self.manifest['tests']['stats']['failures']=False
        with self.assertRaises(SystemExit):self.validate()
    def test_source_tree_missing_rejected(self):
        del self.manifest['source']['tree']
        with self.assertRaises(SystemExit):self.validate()
    def test_numeric_fake_run_rejected(self):
        self.manifest['buildId']='123'
        with self.assertRaises(SystemExit):self.validate()
    def test_file_tampering_rejected(self):
        self.data['assets/main.js']=b'tampered'
        with self.assertRaises(SystemExit):self.validate()
    def test_unlisted_file_rejected(self):
        with self.assertRaises(SystemExit):self.validate([('extra.js',b'extra')])
    def test_duplicate_archive_entry_rejected(self):
        with self.assertRaises(SystemExit):self.validate([('index.html',self.data['index.html'])])
    def test_archive_traversal_rejected(self):
        with self.assertRaises(SystemExit):self.validate([('../outside',b'bad')])
    def test_missing_index_rejected(self):
        del self.data['index.html'];del self.manifest['files']['index.html']
        with self.assertRaises(SystemExit):self.validate()
    def test_flow_fields_in_local_manifest_rejected(self):
        self.manifest['run_id']='99'
        with self.assertRaises(SystemExit):self.validate()


# All transaction tests use synthetic bytes, private /tmp directories and a
# mocked public network boundary. They never address the production root.
class NativeWebTransactionTest(NativeWebManifestTest):
    def setUp(self):
        super().setUp()
        from unittest import mock
        self.mock=mock
        self.state=self.root/'state';self.state.mkdir(mode=0o700)
        self.site=self.root/'site';self.site.mkdir(mode=0o755)
        (self.site/'assets').mkdir()
        self.old_index=b'<html>previous</html>';self.old_js=b'previous-js'
        (self.site/'index.html').write_bytes(self.old_index);(self.site/'assets/main.js').write_bytes(self.old_js)
        (self.site/'unrelated-old.js').write_bytes(b'keep cached clients')
        self.old_record=json.dumps(dict(status='online_verified',run_id='123',commit='d'*40)).encode()
        (self.state/'record.json').write_bytes(self.old_record);(self.state/'record.json').chmod(0o600)
        self.web.ROOT=self.state;self.web.SITE=self.site
        self.online=self.mock.patch.object(self.web,'local_online',return_value=2).start();self.addCleanup(self.mock.patch.stopall)
        self.data['assets/lazy.js']=b'lazy source';self.manifest['files']['assets/lazy.js']=dict(size=len(self.data['assets/lazy.js']),sha256=hashlib.sha256(self.data['assets/lazy.js']).hexdigest())
        self.seal()

    def seal(self):
        self.package=self.root/'package.tgz'
        with tarfile.open(self.package,'w:gz') as tar:
            for n,b in list(self.data.items())+[('cyf-local-build.json',json.dumps(self.manifest).encode())]:
                member=tarfile.TarInfo(n);member.size=len(b);tar.addfile(member,io.BytesIO(b))
        self.package.chmod(0o600)
        self.descriptor=dict(schema_version=1,source_kind='LOCAL',source=dict(self.manifest['source'],version=self.manifest['version'],buildId=self.manifest['buildId']),package=dict(path=str(self.package),size=self.package.stat().st_size,sha256=hashlib.sha256(self.package.read_bytes()).hexdigest()),previousIndexSha256=hashlib.sha256(self.old_index).hexdigest(),previousRecordSha256=hashlib.sha256(self.old_record).hexdigest())
        self.descriptor_path=self.root/'descriptor.json';self.write_descriptor()

    def write_descriptor(self):
        self.descriptor_path.write_text(json.dumps(self.descriptor));self.descriptor_path.chmod(0o600)

    def install(self):return self.web.deploy_local(self.descriptor_path)
    def assert_old(self):
        self.assertEqual((self.site/'index.html').read_bytes(),self.old_index)
        self.assertEqual((self.site/'assets/main.js').read_bytes(),self.old_js)
        self.assertEqual((self.state/'record.json').read_bytes(),self.old_record)
        self.assertEqual((self.site/'unrelated-old.js').read_bytes(),b'keep cached clients')

    def test_transaction_backups_source_and_index_last(self):
        calls=[];original=self.web.atomic_file
        def capture(path,source,mode):
            if self.site in path.parents:calls.append(str(path.relative_to(self.site)))
            return original(path,source,mode)
        with self.mock.patch.object(self.web,'atomic_file',side_effect=capture):r=self.install()
        self.assertEqual(calls[-1],'index.html');self.assertEqual(r['status'],'online_verified');self.assertNotIn('run_id',r)
        self.assertEqual((Path(r['backup'])/'files/index.html').read_bytes(),self.old_index)
        self.assertEqual((self.site/'assets/lazy.js').read_bytes(),self.data['assets/lazy.js'])
        self.assertEqual((self.site/'unrelated-old.js').read_bytes(),b'keep cached clients')

    def test_same_binding_is_idempotent(self):
        self.install()
        with self.mock.patch.object(self.web,'publish_staged') as publish:self.install()
        publish.assert_not_called()

    def test_bad_package_digest_cannot_publish(self):
        self.package.write_bytes(self.package.read_bytes()+b'tampered')
        with self.assertRaises(SystemExit):self.install()
        self.assert_old()

    def test_changed_previous_index_cannot_publish(self):
        self.descriptor['previousIndexSha256']='e'*64;self.write_descriptor()
        with self.assertRaises(SystemExit):self.install()
        self.assert_old()

    def test_changed_previous_record_cannot_publish(self):
        self.descriptor['previousRecordSha256']='e'*64;self.write_descriptor()
        with self.assertRaises(SystemExit):self.install()
        self.assert_old()

    def test_source_mismatch_cannot_publish(self):
        self.descriptor['source']['tree']='e'*40;self.write_descriptor()
        with self.assertRaises(SystemExit):self.install()
        self.assert_old()

    def test_online_failure_restores_exact_original_and_record(self):
        self.online.side_effect=SystemExit('public bytes mismatch')
        with self.assertRaises(SystemExit):self.install()
        self.assert_old();self.assertFalse((self.site/'assets/lazy.js').exists())

    def interrupted(self):
        original=self.web.atomic_file
        def partial(staged,expected):
            original(self.site/'assets/main.js',staged['assets/main.js']['path'],0o644)
            raise KeyboardInterrupt('simulate killed publisher before exception cleanup')
        with self.mock.patch.object(self.web,'publish_staged',side_effect=partial),self.mock.patch.object(self.web,'local_restore'):
            with self.assertRaises(KeyboardInterrupt):self.install()
        self.assertEqual(json.loads((self.state/'record.json').read_text())['status'],'publishing')

    def test_interrupted_same_binding_rolls_back_before_new_attempt(self):
        self.interrupted()
        original=self.web.local_restore;events=[]
        def restore(*args):
            original(*args);self.assert_old();events.append('restored')
        with self.mock.patch.object(self.web,'local_restore',side_effect=restore):r=self.install()
        self.assertEqual(events,['restored']);self.assertEqual(r['status'],'online_verified')

    def test_foreign_binding_cannot_adopt_unfinished_transaction(self):
        self.interrupted();self.manifest['buildId']='local-other';self.seal()
        before=(self.state/'record.json').read_bytes()
        with self.assertRaises(SystemExit):self.install()
        self.assertEqual((self.state/'record.json').read_bytes(),before)

    def test_symlink_package_cannot_publish(self):
        real=self.root/'real.tgz';self.package.rename(real);self.package.symlink_to(real)
        with self.assertRaises(SystemExit):self.install()
        self.assert_old()

    def test_unchanged_public_bytes_are_not_rewritten(self):
        self.data['assets/main.js']=self.old_js;self.manifest['files']['assets/main.js']=dict(size=len(self.old_js),sha256=hashlib.sha256(self.old_js).hexdigest());self.seal()
        original=self.web.atomic_file;calls=[]
        def capture(path,source,mode):
            if path==self.site/'assets/main.js':calls.append(path)
            return original(path,source,mode)
        with self.mock.patch.object(self.web,'atomic_file',side_effect=capture):self.install()
        self.assertEqual(calls,[])

class NativeWebOnlineTest(unittest.TestCase):
    def test_verifies_index_entry_and_lazy_chunks_without_flow_identity(self):
        from unittest import mock
        from test_web_flow_cache_verifier import Response
        web=load();payloads={'index.html':b'index','assets/main.js':b'main','assets/lazy.js':b'lazy'}
        expected={n:dict(size=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in payloads.items()}
        requests=[];index_calls=[]
        def response(request,timeout):
            requests.append(request)
            name=request.full_url.split('?')[0].replace(web.SITE_URL,'')
            if name=='index.html' and not index_calls:
                index_calls.append(1);return Response(b'old')
            return Response(payloads[name])
        with mock.patch.object(web.urllib.request,'urlopen',side_effect=response),mock.patch.object(web.time,'sleep'):
            count=web.local_online(dict(buildId='local-unit',commit='a'*40),expected,web.time.monotonic()+10)
        self.assertEqual(count,3);self.assertEqual(len(requests),4)
        self.assertTrue(any('/assets/lazy.js?' in r.full_url for r in requests))
        self.assertTrue(all('flow_' not in r.full_url and 'Flow' not in str(r.headers) for r in requests))
    def test_expired_local_budget_never_accepts_unverified_bytes(self):
        from unittest import mock
        web=load()
        with mock.patch.object(web.urllib.request,'urlopen') as network:
            with self.assertRaises(SystemExit):web.local_online(dict(buildId='local-unit',commit='a'*40),{'index.html':dict(size=1,sha256='a'*64)},web.time.monotonic()-1)
        network.assert_not_called()

if __name__=='__main__':unittest.main()
