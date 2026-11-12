import argparse
from contextlib import redirect_stdout, contextmanager
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

MODULE = Path(__file__).resolve().parents[1] / 'execution_history_check.py'
SPEC = importlib.util.spec_from_file_location('history_check', str(MODULE))
H = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(H)


class HistoryCheckTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cyf-history-wrapper-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.o = Mock()
        self.o.EVIDENCE_PATH = self.base / 'cache.json'
        self.o.atomic_write.side_effect = lambda path, value, **kwargs: path.write_text(json.dumps(value))
        self.o.load_json.side_effect = lambda path, default: json.loads(path.read_text()) if path.exists() else default
        self.prepared = {'api': {'commit': 'a'*40, 'tree': 'b'*40}, 'web': {'commit': 'c'*40, 'tree': 'd'*40},
            'identity': {'fixtures': {'execution-history.json': 'e'*64}}, 'fixtureDigest': 'f'*64}

    def bundle(self):
        p = self.prepared
        frontend = {'status': 'PASS', 'assertions': 17, 'requests': 8,
                    'webCommit': p['web']['commit'], 'fixtureSha256': 'e'*64}
        result = {'status': 'PASS', 'fixtureSha256': 'e'*64, 'productionTouched': False,
                  'forbiddenCalls': 0, 'rowSnapshotUnchanged': True, 'realMapperQueries': 11,
                  'frontendOutput': json.dumps(frontend)}
        (self.base / 'result.json').write_text(json.dumps(result))
        (self.base / 'junit.xml').write_text('<testsuite name="' + H.TEST_NAME + '" tests="1" failures="0" errors="0" skipped="0"/>')
        (self.base / 'manifest.json').write_text('{}')
        (self.base / 'consumer.log').write_text('PASS')
        (self.base / 'gradle.log').write_text('> Task :validateLayering\nBUILD SUCCESSFUL\n')
        summary = dict(p, status='PASS', evidence=str(self.base / 'summary.json'),
            artifacts={name: H.digest_file(self.base / name) for name in
                       ('result.json', 'junit.xml', 'gradle.log', 'consumer.log', 'manifest.json')})
        (self.base / 'summary.json').write_text(json.dumps(summary))
        record = {'result': 'accepted', 'artifact': str(self.base / 'summary.json'), 'selector': H.SELECTOR,
                  'tree_sha': p['api']['tree'], 'fixture_digest': p['fixtureDigest']}
        self.o.EVIDENCE_PATH.write_text(json.dumps({'records': {'key': record}}))
        return result, summary

    def browser_bundle(self):
        self.prepared['identity']['browser'] = {'executable': '1'*64}
        result, _ = self.bundle()
        frontend = json.loads(result['frontendOutput'])
        frontend['browser'] = {'status': 'PASS', 'checks': ['check'] * 29,
            'requests': [{}] * 15, 'screenshots': {}}
        for name in ('browser-desktop.png', 'browser-mobile.png', 'browser-landscape.png'):
            (self.base / name).write_bytes(b'png-fixture')
            frontend['browser']['screenshots'][name] = H.digest_file(self.base / name)
        result['frontendOutput'] = frontend
        return result

    def test_browser_rejects_node_only_pass(self):
        self.prepared['identity']['browser'] = {'executable': '1'*64}
        result, _ = self.bundle()
        with self.assertRaisesRegex(H.CheckError, 'rendered browser'):
            H.validate_result(result, self.base / 'junit.xml', self.prepared)

    def test_browser_accepts_complete_receipt(self):
        result = self.browser_bundle()
        self.assertEqual('PASS', H.validate_result(result, self.base / 'junit.xml', self.prepared)['browser']['status'])

    def test_browser_rejects_tampered_screenshot(self):
        result = self.browser_bundle()
        (self.base / 'browser-mobile.png').write_bytes(b'changed')
        with self.assertRaisesRegex(H.CheckError, 'digest mismatch'):
            H.validate_result(result, self.base / 'junit.xml', self.prepared)

    def test_browser_rejects_missing_viewport(self):
        result = self.browser_bundle()
        del result['frontendOutput']['browser']['screenshots']['browser-landscape.png']
        with self.assertRaisesRegex(H.CheckError, 'viewport evidence'):
            H.validate_result(result, self.base / 'junit.xml', self.prepared)

    def test_valid_bundle_reused_without_credentials_or_gradle(self):
        self.bundle()
        self.assertEqual('REUSED', H.cached_summary(self.o, 'key', self.prepared)['status'])
        self.o.cmd_gradle.assert_not_called()

    def test_no_record_is_cache_miss(self):
        self.assertIsNone(H.cached_summary(self.o, 'key', self.prepared))

    def test_failed_record_is_cache_miss(self):
        self.o.EVIDENCE_PATH.write_text('{"records":{"key":{"result":"failed"}}}')
        self.assertIsNone(H.cached_summary(self.o, 'key', self.prepared))

    def test_missing_artifact_fails_closed(self):
        self.bundle(); (self.base / 'junit.xml').unlink()
        with self.assertRaisesRegex(H.CheckError, 'missing/tampered'):
            H.cached_summary(self.o, 'key', self.prepared)

    def test_tampered_artifact_fails_closed(self):
        self.bundle(); (self.base / 'gradle.log').write_text('fake')
        with self.assertRaises(H.CheckError):
            H.cached_summary(self.o, 'key', self.prepared)

    def test_missing_summary_cannot_use_gradle_exit_zero(self):
        self.bundle(); (self.base / 'summary.json').unlink()
        with self.assertRaises(H.CheckError):
            H.cached_summary(self.o, 'key', self.prepared)

    def test_wrong_selector_cannot_reuse(self):
        self.bundle(); value=json.loads(self.o.EVIDENCE_PATH.read_text());value['records']['key']['selector']='other'
        self.o.EVIDENCE_PATH.write_text(json.dumps(value))
        with self.assertRaises(H.CheckError):
            H.cached_summary(self.o, 'key', self.prepared)

    def test_legacy_log_receipt_cannot_be_misreported_as_complete(self):
        self.bundle(); value=json.loads(self.o.EVIDENCE_PATH.read_text());value['records']['key']['artifact']=str(self.base/'gradle.log')
        self.o.EVIDENCE_PATH.write_text(json.dumps(value))
        with self.assertRaises(H.CheckError):
            H.cached_summary(self.o, 'key', self.prepared)

    def test_result_rejects_wrong_fixture_or_web(self):
        result,_=self.bundle()
        result['fixtureSha256']='wrong'
        with self.assertRaises(H.CheckError): H.validate_result(result,self.base/'junit.xml',self.prepared)
        result,_=self.bundle();f=json.loads(result['frontendOutput']);f['webCommit']='wrong';result['frontendOutput']=f
        with self.assertRaises(H.CheckError): H.validate_result(result,self.base/'junit.xml',self.prepared)

    def test_result_rejects_writes_no_sql_or_incomplete_frontend(self):
        for field,value in [('productionTouched',True),('forbiddenCalls',1),('rowSnapshotUnchanged',False),('realMapperQueries',0),('status','FAIL')]:
            result,_=self.bundle();result[field]=value
            with self.assertRaises(H.CheckError): H.validate_result(result,self.base/'junit.xml',self.prepared)
        result,_=self.bundle();result['frontendOutput']={'status':'PASS'}
        with self.assertRaises(H.CheckError): H.validate_result(result,self.base/'junit.xml',self.prepared)

    def test_skipped_or_failed_junit_is_not_pass(self):
        result,_=self.bundle()
        for field in ('skipped','failures','errors'):
            text='<testsuite name="'+H.TEST_NAME+'" tests="1" failures="0" errors="0" skipped="0"/>'
            (self.base/'junit.xml').write_text(text.replace(field+'="0"',field+'="1"'))
            with self.assertRaises(H.CheckError): H.validate_result(result,self.base/'junit.xml',self.prepared)

    def test_environment_drops_injected_tool_flags_and_stale_tokens(self):
        with patch.dict(os.environ, {'CYF_HISTORY_TOKENS':'secret','CYF_FLOW_GRADLE_ACTIVE':'1','NODE_OPTIONS':'bad',
                                    'JAVA_TOOL_OPTIONS':'bad','CYF_MAVEN_PASSWORD':'secret'}):
            env=H.clean_env()
        for key in ('CYF_HISTORY_TOKENS','CYF_FLOW_GRADLE_ACTIVE','NODE_OPTIONS','JAVA_TOOL_OPTIONS','CYF_MAVEN_PASSWORD'):
            self.assertNotIn(key,env)

    def test_credentials_only_read_explicit_source(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(H.CheckError,'explicitly select'):
                H.credentials(argparse.Namespace(credentials_init=None))

    def test_credential_values_are_not_in_parse_error(self):
        path=self.base/'credentials.gradle';path.write_text("username 'secret-a'\nusername 'secret-b'\npassword 'secret-c'")
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(H.CheckError) as caught: H.credentials(argparse.Namespace(credentials_init=path))
        self.assertNotIn('secret-',str(caught.exception))

    def test_environment_credentials_do_not_open_init(self):
        with patch.dict(os.environ,{'CYF_MAVEN_USERNAME':'u','CYF_MAVEN_PASSWORD':'p'}):
            self.assertEqual('p',H.credentials(argparse.Namespace(credentials_init=self.base/'absent'))['CYF_MAVEN_PASSWORD'])

    def test_local_init_preserves_dependency_integrity_and_removes_flow_identity(self):
        root=self.base/'ops/ci/aliyun-flow';root.mkdir(parents=True)
        source="CYF_FLOW_GRADLE_ACTIVE CYF_FLOW_BUILD_ROOT must be set by flow_remote\npinnedOpenCvSha256=abc\nchildEnvironment.remove('CYF_MAVEN_PASSWORD')"
        (root/'cold-init.gradle').write_text(source)
        derived=H.local_init(self.base)
        self.assertIn('pinnedOpenCvSha256=abc',derived)
        self.assertIn("childEnvironment.remove('CYF_MAVEN_PASSWORD')",derived)
        self.assertNotIn('CYF_FLOW_',derived)
        self.assertIn("test.outputs.file(System.getenv('CYF_HISTORY_RESULT'))",derived)

    def test_init_drift_requires_explicit_review(self):
        root=self.base/'ops/ci/aliyun-flow';root.mkdir(parents=True);(root/'cold-init.gradle').write_text('changed')
        with self.assertRaises(H.CheckError):H.local_init(self.base)

    def test_first_failure_not_entire_log(self):
        text='100 lines of task output\nfile.java:4: error: missing class\nBUILD FAILED\nmore details'
        self.assertEqual('file.java:4: error: missing class',H.first_failure(text))
        self.assertEqual('SyntaxError: duplicate',H.first_failure('prefix\nSyntaxError: duplicate\nNode20'))

    def test_tree_digest_ignores_location_not_bytes(self):
        a=self.base/'a';b=self.base/'b';a.mkdir();b.mkdir();(a/'x').write_text('same');(b/'x').write_text('same')
        self.assertEqual(H.tree_digest(a),H.tree_digest(b))
        (b/'x').write_text('changed');self.assertNotEqual(H.tree_digest(a),H.tree_digest(b))

    def test_package_closure_content_change_invalidates_identity(self):
        for name,deps in [('vue',{'dep':'1'}),('dep',{}),('consola',{})]:
            p=self.base/'node_modules'/name;p.mkdir(parents=True)
            (p/'package.json').write_text(json.dumps({'name':name,'version':'1','dependencies':deps}))
            (p/'index.js').write_text('code')
        before=H.installed_packages(self.base);self.assertEqual(3,len(before))
        (self.base/'node_modules/dep/index.js').write_text('changed')
        self.assertNotEqual(before,H.installed_packages(self.base))

    def test_no_auto_install_for_missing_dependency(self):
        with self.assertRaisesRegex(H.CheckError,'no auto-install'):H.installed_packages(self.base)

    def test_source_requires_clean_root(self):
        subprocess.check_call(['git','init','-q',str(self.base)])
        subprocess.check_call(['git','-C',str(self.base),'config','user.email','test@example.invalid'])
        subprocess.check_call(['git','-C',str(self.base),'config','user.name','test'])
        (self.base/'file').write_text('data');subprocess.check_call(['git','-C',str(self.base),'add','file'])
        subprocess.check_call(['git','-C',str(self.base),'commit','-qm','fixture'])
        self.assertEqual(40,len(H.source_identity(self.base)['tree']))
        (self.base/'new').write_text('preserve')
        with self.assertRaisesRegex(H.CheckError,'Dirty source'): H.source_identity(self.base)
        self.assertEqual('preserve',(self.base/'new').read_text())

    def test_check_only_never_executes_or_loads_credentials(self):
        prepared=dict(self.prepared,baseline={})
        with patch.object(H,'load_orchestrator',return_value=self.o),patch.object(H,'precheck',return_value=prepared),\
             patch.object(H,'execute') as execute,patch.object(H,'credentials') as credentials,redirect_stdout(StringIO()) as out:
            self.assertEqual(0,H.main(['--task-id','T','--api',str(self.base),'--web',str(self.base),'--check-only']))
        execute.assert_not_called();credentials.assert_not_called()
        self.assertEqual('NOT_RUN',json.loads(out.getvalue())['verification'])

    def test_changed_owner_does_not_get_failure_attributed(self):
        self.o.task.return_value={'owner':'another'};p=dict(self.prepared,taskAtStart={'owner':'ours'})
        H.attribute_failure(argparse.Namespace(task_id='T'),self.o,p,self.base/'log','failure')
        self.o.cmd_fail.assert_not_called()


    @contextmanager
    def unlocked(self, path):
        yield

    def test_reuse_does_not_need_active_owner_credentials_or_build(self):
        self.o.exclusive_lock.side_effect=self.unlocked
        self.o.evidence_key.return_value='key'
        cached={'status':'REUSED'}
        args=argparse.Namespace(task_id='T',api=Path('/api'),web=Path('/web'))
        with patch.object(H,'source_identity',side_effect=[self.prepared['api'],self.prepared['web']]),patch.object(H,'cached_summary',return_value=cached),patch.object(H,'guard') as guard,\
             patch.object(H,'credentials') as creds,patch.object(H.subprocess,'run') as run:
            result=H.execute(args,self.o,self.prepared,time.monotonic())
        self.assertEqual('REUSED',result['status']);guard.assert_not_called();creds.assert_not_called();run.assert_not_called()

    def test_cheap_failure_never_starts_gradle_and_has_no_retry(self):
        self.o.exclusive_lock.side_effect=self.unlocked
        self.o.evidence_key.return_value='key'
        self.o.task.return_value={'owner':'ours'}
        prepared=dict(self.prepared,baseline={},files={'check-consumer.mjs':b'code'},init='init')
        args=argparse.Namespace(task_id='T',evidence_root=self.base,node=Path('/node'),api=Path('/api'),web=Path('/web'))
        def run_once(command,**kwargs):
            kwargs['stdout'].write('SyntaxError: duplicate binding')
            return argparse.Namespace(returncode=1)
        with patch.object(H,'source_identity',side_effect=[self.prepared['api'],self.prepared['web']]),patch.object(H,'cached_summary',return_value=None),patch.object(H,'guard',return_value={'owner':'ours'}),\
             patch.object(H,'credentials',return_value={'CYF_MAVEN_PASSWORD':'secret'}),\
             patch.object(H.subprocess,'run',side_effect=run_once) as run:
            with self.assertRaisesRegex(H.CheckError,'SyntaxError'):
                H.execute(args,self.o,prepared,time.monotonic())
        self.assertEqual(1,run.call_count)
        self.o.cmd_fail.assert_called_once();self.o.cmd_evidence_put.assert_called_once()
        failure=json.loads(next(self.base.glob('run-*/failure.json')).read_text())
        self.assertEqual('FAILED',failure['status']);self.assertNotIn('secret',str(failure))

    def test_invalid_cache_does_not_silently_start_build(self):
        self.o.exclusive_lock.side_effect=self.unlocked
        self.o.evidence_key.return_value='key'
        with patch.object(H,'source_identity',side_effect=[self.prepared['api'],self.prepared['web']]),patch.object(H,'cached_summary',side_effect=H.CheckError('tampered')),\
             patch.object(H.subprocess,'run') as run,patch.object(H,'credentials') as creds:
            with self.assertRaises(H.CheckError):
                H.execute(argparse.Namespace(task_id='T',api=Path('/api'),web=Path('/web')),self.o,self.prepared,time.monotonic())
        run.assert_not_called();creds.assert_not_called()


    def test_changed_source_after_precheck_cannot_reuse_or_build(self):
        with patch.object(H,'source_identity',return_value={'commit':'changed','tree':'changed'}), \
             patch.object(H,'cached_summary') as cached,patch.object(H.subprocess,'run') as run:
            with self.assertRaisesRegex(H.CheckError,'Source changed'):
                H.execute(argparse.Namespace(api=Path('/api'),web=Path('/web')),self.o,self.prepared,time.monotonic())
        cached.assert_not_called();run.assert_not_called()

    def test_fingerprints_are_taken_after_lock_and_baseline_is_rechecked(self):
        events=[]
        @contextmanager
        def lock(path):
            events.append('lock');yield;events.append('unlock')
        self.o.exclusive_lock.side_effect=lock
        def precheck(args,orchestrator):
            events.append('precheck');return self.prepared
        with patch.object(H,'load_orchestrator',return_value=self.o), \
             patch.object(H,'source_identity',return_value={'commit':'old','tree':'old'}), \
             patch.object(H,'precheck',side_effect=precheck),patch.object(H,'execute') as execute, \
             redirect_stdout(StringIO()):
            self.assertEqual(2,H.main(['--task-id','T','--api',str(self.base),'--web',str(self.base)]))
        self.assertEqual(['lock','precheck'],events);execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
