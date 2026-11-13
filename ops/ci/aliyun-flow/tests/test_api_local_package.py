#!/usr/bin/env python3
"""Private synthetic ZIP/log/proof only: NOT Gradle/test/build/release evidence."""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / 'auto/package-api-local.py'
INIT = ROOT / 'local-release-metadata.init.gradle'
SPEC = importlib.util.spec_from_file_location('ur05_local_producer', PRODUCER)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
MAIL_CLASSES = ('javax/mail/MessagingException.class', 'javax/mail/Session.class',
                'javax/mail/Transport.class', 'com/sun/mail/smtp/SMTPTransport.class',
                'javax/activation/DataHandler.class')


class Fixture:
    """Synthetic non-secret test corpus; never usable as actual build evidence."""
    def __init__(self, root):
        self.root = root
        self.source = root / 'api'
        self.build = root / 'build'
        self.output = root / 'output'
        for path in (self.source, self.build, self.output):
            path.mkdir(mode=0o700)
        (self.source / 'starter').mkdir()
        (self.source / 'settings.gradle').write_text("rootProject.name='jia'\n")
        (self.source / 'starter/build.gradle').write_text('// synthetic only\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@invalid', 'commit', '-qm', 'synthetic')
        self.identity = {'version': '0.1.0-synthetic', 'buildId': 'private-unit-1',
                         'commit': self.git('rev-parse', 'HEAD'), 'tree': self.git('rev-parse', 'HEAD^{tree}')}
        self.init = root / INIT.name
        self.init.write_bytes(INIT.read_bytes())
        self.dependency = self.build / 'synthetic-opencv.jar'
        self.dependency.write_bytes(b'synthetic dependency NOT the production OpenCV artifact')
        self.jar = self.build / 'application-original.jar'
        self.write_jar()
        self.clean = {'commit': self.identity['commit'], 'tree': self.identity['tree'], 'clean': True}
        self.proof_path = self.build / 'local-bootjar-proof.json'
        self.proof = {'format': 'cyf-api-local-bootjar-proof-v1', 'identity': self.identity,
                      'sourceRoot': str(self.source), 'buildRoot': str(self.build),
                      'sourceBefore': self.clean, 'sourceAfter': self.clean, 'task': ':starter:bootJar',
                      'metadata': self.metadata(), 'moduleVersion': '1.1.2-SNAPSHOT', 'implementationVersion': None,
                      'jar': m.record(self.jar), 'publicArtifactVerifier': 'bootJar-original-doLast-completed'}
        self.prov_path = self.build / 'opencv-resolved.json'
        self.prov_path.write_bytes(m.canonical({'coordinate': 'org.opencv:opencv:4.5.5',
            'jar_sha256': m.sha(self.dependency.read_bytes()), 'jar_size': self.dependency.stat().st_size,
            'resolved_file': str(self.dependency)}))
        self.tasks = (':starter:publicArtifactVerifierTest', ':starter:poiProductionRuntimeClasspathTest', ':agent:test')
        self.reports = []
        for i in range(len(self.tasks)):
            report = self.build / ('TEST-synthetic%d.xml' % i)
            report.write_bytes(b'<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="Synthetic" name="only"/></testsuite>')
            self.reports.append(report)
        self.log_path = self.build / 'actual-command-synthetic.log'
        self.ev = {'format': 'cyf-api-local-build-evidence-v1', 'identity': self.identity,
            'sourceRoot': str(self.source), 'buildRoot': str(self.build),
            'sourceBefore': self.clean, 'sourceAfter': self.clean,
            'invocation': {'argv': ['./gradlew', '--console=plain', '--no-daemon', '--no-build-cache',
                '-I', str(self.init), *self.tasks, ':validateLayering', ':starter:bootJar'],
                'exitCode': 0, 'cacheHit': False, 'log': {}, 'selector': 'synthetic-unit', 'fixtureSha256': 'a'*64,
                'inputs': [m.record(self.source / 'settings.gradle'), m.record(self.source / 'starter/build.gradle'), m.record(self.init)]},
            'tests': [{'task': task, 'selector': 'synthetic', 'fixtureSha256': 'a'*64, 'reports': [m.record(report)]}
                for task, report in zip(self.tasks, self.reports)],
            'validateLayering': {'task': ':validateLayering'}, 'bootJar': {'task': ':starter:bootJar', 'proof': {}},
            'opencv': m.record(self.prov_path)}
        self.evidence_path = self.build / 'build-evidence.json'
        self.refresh_proof()
        self.refresh_log()
        self.save_evidence()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], stderr=subprocess.DEVNULL).decode().strip()

    def metadata(self):
        return dict(zip(m.METADATA_KEYS, [self.identity[k] for k in ('version', 'commit', 'tree', 'buildId')]))

    def write_jar(self, mail=True, changes=None, implementation=None):
        values = {'Manifest-Version': '1.0', 'Main-Class': 'org.springframework.boot.loader.launch.JarLauncher',
                  'Start-Class': 'cn.jia.JiaApplication', **self.metadata()}
        values.update(changes or {})
        if implementation is not None:
            values['Implementation-Version'] = implementation
        manifest = ''.join('%s: %s\r\n' % item for item in values.items()) + '\r\n'
        with zipfile.ZipFile(self.jar, 'w') as boot:
            boot.writestr('META-INF/MANIFEST.MF', manifest)
            if mail:
                inner = io.BytesIO()
                with zipfile.ZipFile(inner, 'w') as lib:
                    for name in MAIL_CLASSES:
                        lib.writestr(name, b'synthetic class')
                boot.writestr('BOOT-INF/lib/synthetic-mail.jar', inner.getvalue())

    def refresh_proof(self):
        self.proof_path.write_bytes(m.canonical(self.proof))
        self.ev['bootJar']['proof'] = m.record(self.proof_path)

    def refresh_log(self, extra='', task_suffix='', omit=None):
        lines = ['GRADLE_LOCK_ACQUIRED task=synthetic pid=1']
        lines += ['> Task ' + t + task_suffix for t in (*self.tasks, ':validateLayering', ':starter:bootJar') if t != omit]
        lines += ['CYF_LOCAL_BOOTJAR_BEGIN ' + self.identity['buildId'],
                  'CYF_LOCAL_BOOTJAR_END ' + m.sha(self.proof_path.read_bytes()), 'BUILD SUCCESSFUL in 1s', extra]
        self.log_path.write_text('\n'.join(lines) + '\n')
        self.ev['invocation']['log'] = m.record(self.log_path)

    def save_evidence(self):
        self.evidence_path.write_bytes(m.canonical(self.ev))

    def args(self):
        return argparse.Namespace(opt_in=True, version=self.identity['version'], build_id=self.identity['buildId'],
            commit=self.identity['commit'], tree=self.identity['tree'], source_root=str(self.source), build_root=str(self.build),
            evidence=str(self.evidence_path), evidence_sha256=m.sha(self.evidence_path.read_bytes()),
            output=str(self.output / 'synthetic-only.tar'))

    def pins(self):
        # Explicit test-only replacement for full-path consistency checks. Production
        # constant pin/digest are tested separately and NEVER changed in source.
        return mock.patch.multiple(m, OPENCV_SHA=m.sha(self.dependency.read_bytes()), OPENCV_SIZE=self.dependency.stat().st_size)


class LocalPackageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ur05-private-unit-')
        self.root = Path(self.tmp.name)
        self.f = Fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def rejected(self, action, code=None):
        with self.assertRaises(m.Rejected) as caught:
            action()
        if code:
            self.assertEqual(caught.exception.code, code)
        self.assertFalse((self.f.output / 'synthetic-only.tar').exists())

    def run_fixture(self):
        self.f.save_evidence()
        with self.f.pins():
            return m.produce(self.f.args())

    def test_exact_five_payloads_bind_actual_bytes_no_self_reference(self):
        result = self.run_fixture()
        self.assertFalse(result['productionAuthorized'])
        archive = Path(result['package']['path'])
        self.assertEqual(m.sha(archive.read_bytes()), result['package']['sha256'])
        self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
        self.assertEqual(archive.stat().st_nlink, 1)
        with tarfile.open(archive) as handle:
            self.assertEqual(handle.getnames(), list(m.MEMBERS))
            self.assertTrue(all(member.isfile() for member in handle.getmembers()))
            data = {name: handle.extractfile(name).read() for name in handle.getnames()}
        receipt = m.strict_json(data['receipt.json'])
        self.assertEqual(receipt['status'], 'packaged')
        self.assertEqual(receipt['identity'], self.f.identity)
        for name in ('application.metadata.json', 'application.sidecar.json'):
            item = m.strict_json(data[name])
            self.assertEqual(item['receiptSha256'], m.sha(data['receipt.json']))
            self.assertEqual(item['applicationJar']['sha256'], m.sha(data['application.jar']))
            self.assertEqual(item['dependencyProvenance']['sha256'], m.sha(data['dependency.provenance.json']))
        self.assertNotIn(result['package']['sha256'].encode(), b''.join(data.values()))
        self.assertFalse(list(self.f.output.glob('.cyf-local-package-*')))

    def test_real_pin_and_helper_unchanged(self):
        self.assertEqual(m.OPENCV_SHA, '323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4')
        self.assertEqual(m.OPENCV_SIZE, 722802)
        self.assertEqual(m.sha((ROOT / 'auto/package-api.py').read_bytes()),
            '165887c1e50d6db286359e7c6de9a04098440634ff542267ba84edf5bc21d84a')
        self.rejected(lambda: m.produce(self.f.args()), 'PROVENANCE_INVALID')

    def test_source_dirty_tracked_and_untracked(self):
        for name in ('settings.gradle', 'untracked'):
            with self.subTest(name=name):
                path = self.f.source / name
                old = path.read_bytes() if path.exists() else None
                path.write_text('changed')
                self.rejected(lambda: m.produce(self.f.args()), 'SOURCE_DIRTY')
                if old is None:
                    path.unlink()
                else:
                    path.write_bytes(old)

    def test_wrong_commit_and_tree(self):
        for field in ('commit', 'tree'):
            args = self.f.args()
            setattr(args, field, 'f'*40)
            self.rejected(lambda: m.produce(args), 'SOURCE_MISMATCH')

    def test_missing_opt_in_and_noncanonical_tokens(self):
        for field, value in (('opt_in', False), ('version', 'bad\nsecret'), ('commit', 'a'*39), ('build_id', '../bad')):
            args = self.f.args()
            setattr(args, field, value)
            self.rejected(lambda: m.produce(args), 'INPUT_INVALID')

    def test_wrong_evidence_digest(self):
        args = self.f.args()
        args.evidence_sha256 = 'f'*64
        self.rejected(lambda: m.produce(args), 'EVIDENCE_TAMPERED')

    def test_wrong_identity_or_unknown_secret_flow_fields(self):
        original = copy.deepcopy(self.f.ev)
        for mutate in (lambda e: e.update(flow={'run': 1}), lambda e: e.update(password='synthetic-secret'),
                       lambda e: e['identity'].update(buildId='foreign'), lambda e: e.update(format='flow-receipt')):
            self.f.ev = copy.deepcopy(original)
            mutate(self.f.ev)
            self.rejected(self.run_fixture, 'EVIDENCE_INVALID')

    def test_failed_exit_and_cached_or_missing_task(self):
        self.f.ev['invocation']['exitCode'] = 1
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        self.f.ev['invocation']['exitCode'] = 0
        self.f.ev['invocation']['cacheHit'] = True
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        self.f.ev['invocation']['cacheHit'] = False
        for suffix in (' UP-TO-DATE', ' FROM-CACHE', ' SKIPPED', ' NO-SOURCE'):
            self.f.refresh_log(task_suffix=suffix)
            self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        for task in (*self.f.tasks, ':validateLayering', ':starter:bootJar'):
            self.f.refresh_log(omit=task)
            self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        self.f.refresh_log(extra='EVIDENCE_HIT key=synthetic; Gradle skipped')
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')

    def test_compile_cache_flag_allows_only_fresh_required_tasks(self):
        self.f.ev['invocation']['argv'][2] = '--build-cache'
        self.f.refresh_log(extra='> Task :agent:compileJava FROM-CACHE')
        package = Path(self.run_fixture()['package']['path'])
        self.assertTrue(package.is_file())
        package.unlink()
        self.f.refresh_log(extra='> Task :agent:test FROM-CACHE')
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')

    def test_exact_task_execution_allows_testclasses_siblings(self):
        siblings = '\n'.join('> Task ' + task + 'Classes' for task in self.f.tasks)
        self.f.refresh_log(extra=siblings)
        self.assertTrue(Path(self.run_fixture()['package']['path']).is_file())

    def test_exact_task_token_rejects_prefix_only_status_and_duplicates(self):
        task = self.f.tasks[0]
        for extra in ('> Task ' + task + 'Classes', '> Task ' + task + 'Extra',
                      '> Task ' + task + ':child', '> Task ' + task + '-sibling',
                      '> Task ' + task + ' UP-TO-DATE', '> Task ' + task + ' FROM-CACHE',
                      '> Task ' + task + ' SKIPPED', '> Task ' + task + ' NO-SOURCE'):
            with self.subTest(extra=extra):
                self.f.refresh_log(omit=task, extra=extra)
                self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        self.f.refresh_log(extra='> Task ' + task)
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')

    def test_proof_stale_foreign_or_wrong_metadata(self):
        original = copy.deepcopy(self.f.proof)
        for mutate in (lambda p: p.update(identity={**p['identity'], 'buildId': 'foreign'}),
                       lambda p: p['metadata'].update({'CYF-Release-Version': 'wrong'}),
                       lambda p: p.update(publicArtifactVerifier='skipped'),
                       lambda p: p.update(sourceAfter={**p['sourceAfter'], 'clean': 1})):
            self.f.proof = copy.deepcopy(original)
            mutate(self.f.proof)
            self.f.refresh_proof()
            self.f.refresh_log()
            self.rejected(self.run_fixture, 'EVIDENCE_INVALID')

    def test_proof_or_log_byte_tamper(self):
        for path in (self.f.proof_path, self.f.log_path, self.f.jar, self.f.prov_path):
            original = path.read_bytes()
            path.write_bytes(original + b'x')
            self.rejected(self.run_fixture, 'EVIDENCE_TAMPERED')
            path.write_bytes(original)

    def test_jar_missing_mail_or_wrong_release(self):
        for kwargs, expected in (({'mail': False}, 'MAIL_RUNTIME_INVALID'),
                                 ({'changes': {'CYF-Release-Version': 'foreign'}}, 'JAR_INVALID'),
                                 ({'implementation': 'actual-different'}, 'JAR_INVALID')):
            self.f.write_jar(**kwargs)
            self.f.proof['jar'] = m.record(self.f.jar)
            self.f.refresh_proof()
            self.f.refresh_log()
            self.rejected(self.run_fixture, expected)

    def test_implementation_version_preserved_if_present(self):
        self.f.write_jar(implementation='module-real-1')
        self.f.proof['implementationVersion'] = 'module-real-1'
        self.f.proof['jar'] = m.record(self.f.jar)
        self.f.refresh_proof()
        self.f.refresh_log()
        result = self.run_fixture()
        with tarfile.open(result['package']['path']) as archive:
            metadata = m.strict_json(archive.extractfile('application.metadata.json').read())
        self.assertEqual(metadata['implementationVersion'], 'module-real-1')
        self.assertEqual(metadata['moduleVersion'], '1.1.2-SNAPSHOT')

    def test_provenance_actual_resolved_bytes_not_json_claim(self):
        self.f.dependency.write_bytes(b'foreign dependency')
        with mock.patch.multiple(m, OPENCV_SHA=self.f.ev['opencv']['sha256'], OPENCV_SIZE=722802):
            self.rejected(lambda: m.produce(self.f.args()), 'PROVENANCE_INVALID')

    def test_bad_xml_counts_failures_and_entities(self):
        examples = (b'<testsuite tests="2"><testcase classname="a" name="b"/></testsuite>',
                    b'<testsuite tests="1" failures="1"><testcase classname="a" name="b"><failure/></testcase></testsuite>',
                    b'<testsuite tests="1" skipped="1"><testcase classname="a" name="b"><skipped/></testcase></testsuite>',
                    b'<!DOCTYPE testsuite []><testsuite/>', b'<broken')
        for data in examples:
            self.f.reports[0].write_bytes(data)
            self.f.ev['tests'][0]['reports'] = [m.record(self.f.reports[0])]
            self.rejected(self.run_fixture, 'TEST_EVIDENCE_INVALID')

    def test_honest_skipped_xml_does_not_discard_passed_task_reports(self):
        skipped = self.f.build / 'TEST-honest-skipped.xml'
        skipped.write_bytes(b'<testsuite tests="1" skipped="1"><testcase classname="SyntheticSkipped" name="optional"><skipped/></testcase></testsuite>')
        self.f.ev['tests'][0]['reports'].append(m.record(skipped))
        result = self.run_fixture()
        with tarfile.open(result['package']['path']) as archive:
            receipt = m.strict_json(archive.extractfile('receipt.json').read())
        reports = receipt['evidence']['tests'][0]['reports']
        self.assertEqual(sum(r['skipped'] for r in reports), 1)
        self.assertEqual(sum(r['tests'] for r in reports), 2)

    def test_missing_required_security_task_and_duplicate_report(self):
        original = copy.deepcopy(self.f.ev['tests'])
        self.f.ev['tests'] = original[1:]
        self.rejected(self.run_fixture, 'TEST_EVIDENCE_INVALID')
        self.f.ev['tests'] = original
        self.f.ev['tests'][1]['reports'] = self.f.ev['tests'][0]['reports']
        self.rejected(self.run_fixture, 'TEST_EVIDENCE_INVALID')

    def test_alias_symlink_hardlink_and_unsafe_output(self):
        symlink = self.root / 'alias'
        symlink.symlink_to(self.f.source, target_is_directory=True)
        args = self.f.args()
        args.source_root = str(symlink)
        self.rejected(lambda: m.produce(args), 'PATH_UNSAFE')
        os.link(str(self.f.jar), str(self.root / 'hardlink'))
        self.rejected(self.run_fixture, 'PATH_UNSAFE')
        (self.root / 'hardlink').unlink()
        self.f.output.chmod(0o755)
        self.rejected(self.run_fixture, 'PATH_UNSAFE')

    def test_output_existing_never_overwritten(self):
        output = Path(self.f.args().output)
        output.write_bytes(b'prior')
        with self.f.pins(), self.assertRaises(m.Rejected) as caught:
            m.produce(self.f.args())
        self.assertEqual(caught.exception.code, 'OUTPUT_EXISTS')
        self.assertEqual(output.read_bytes(), b'prior')

    def test_publish_uncompressed_tar_retains_exact_members(self):
        output = Path(self.f.args().output)
        data = {name: (name.encode() + b'\0') * 50 for name in m.MEMBERS}
        with mock.patch.object(m.tarfile, 'open', wraps=tarfile.open) as opening:
            m.publish(output, data, lambda: None)
        self.assertEqual(opening.call_args.kwargs['mode'], 'w')
        self.assertNotIn('compresslevel', opening.call_args.kwargs)
        self.assertNotEqual(output.read_bytes()[:2], b'\x1f\x8b')
        with tarfile.open(output, 'r:') as archive:
            self.assertEqual({row.name: archive.extractfile(row).read() for row in archive}, data)

    def test_older_tgz_caller_keeps_gzip_compatibility(self):
        output = self.f.output / 'older-caller.tgz'
        data = {name: name.encode() for name in m.MEMBERS}
        m.publish(output, data, lambda: None)
        self.assertEqual(output.read_bytes()[:2], b'\x1f\x8b')
        with tarfile.open(output, 'r:gz') as archive:
            self.assertEqual({row.name: archive.extractfile(row).read() for row in archive}, data)

    def test_atomic_publish_rechecks_before_publication_and_cleans_stage(self):
        def fail():
            raise m.Rejected('SOURCE_DIRTY')
        self.rejected(lambda: m.publish(Path(self.f.args().output), {name: b'x' for name in m.MEMBERS}, fail), 'SOURCE_DIRTY')
        self.assertEqual(list(self.f.output.iterdir()), [])

    def test_atomic_output_race_preserves_other_writer(self):
        output = Path(self.f.args().output)
        def race():
            output.write_bytes(b'other-writer')
        with self.assertRaises(m.Rejected) as caught:
            m.publish(output, {name: b'x' for name in m.MEMBERS}, race)
        self.assertEqual(caught.exception.code, 'OUTPUT_EXISTS')
        self.assertEqual(output.read_bytes(), b'other-writer')
        self.assertFalse(list(self.f.output.glob('.cyf-local-package-*')))

    def test_strict_json_duplicate_nan_unknown_fields(self):
        for value in (b'{"a":1,"a":2}', b'{"a":NaN}', b'not-json'):
            self.rejected(lambda: m.strict_json(value), 'EVIDENCE_INVALID')

    def test_cli_secret_argument_safe_error(self):
        secret = 'synthetic-secret-do-not-print'
        result = subprocess.run(['python3', '-I', '-B', str(PRODUCER), '--password', secret],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(secret.encode(), result.stdout + result.stderr)
        self.assertEqual(m.strict_json(result.stdout)['code'], 'INPUT_INVALID')

    def test_argv_disallows_exclusions_credentials_and_fake_flow(self):
        original = copy.deepcopy(self.f.ev['invocation']['argv'])
        for args in (['-x', 'test'], ['-PCYF_FLOW_GRADLE_ACTIVE=1'], ['-Dpassword=synthetic'], ['--refresh-dependencies']):
            self.f.ev['invocation']['argv'] = original + args
            self.rejected(self.run_fixture, 'EVIDENCE_INVALID')

    def test_parallel_headers_require_one_fresh_root_completion(self):
        task = ':starter:bootJar'
        completion = 'CYF_TASK_TIMING ' + json.dumps(dict(task=task, rootBuild=True,
            skipped=False, failed=False, skipMessage=None)) + '\n'
        headers = '> Task ' + task + '\n> Task ' + task + '\n'
        m.task_executed(headers + completion, task)
        for log in (headers, headers + completion + completion,
                    headers + completion.replace('"failed": false', '"failed": true'),
                    headers + '> Task ' + task + ' FROM-CACHE\n' + completion):
            with self.assertRaises(m.Rejected): m.task_executed(log, task)

    def test_fixed_fast_build_options_do_not_allow_arbitrary_jvm_arguments(self):
        argv = ['./gradlew', '--parallel', '--offline', '--max-workers=2',
            '--project-cache-dir', '/private/cache',
            '-Dorg.gradle.jvmargs=-Xmx768m -XX:MaxMetaspaceSize=384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1',
            '--console=plain', '-I', '/safe/local-release-metadata.init.gradle', ':starter:bootJar']
        m.validate_argv(argv, {':starter:bootJar'}, [{'path': '/safe/local-release-metadata.init.gradle'}])
        for extra in ('--exclude-task', '-x', '-Dorg.gradle.jvmargs=-javaagent:/unsafe'):
            with self.assertRaises(m.Rejected):
                m.validate_argv(argv + [extra], {':starter:bootJar'}, [{'path': '/safe/local-release-metadata.init.gradle'}])

    def test_serial_low_memory_build_keeps_exact_argv_and_rejects_unsafe_jvm_options(self):
        argv = ['./gradlew', '--console=plain', '--no-daemon', '--parallel', '--no-parallel',
                '--max-workers=2',
                '-Dorg.gradle.jvmargs=-Xmx512m -XX:+UseSerialGC -XX:MaxMetaspaceSize=384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1',
                '-I', '/safe/local-release-metadata.init.gradle', ':starter:bootJar']
        original = list(argv)
        m.validate_argv(argv, {':starter:bootJar'}, [{'path': '/safe/local-release-metadata.init.gradle'}])
        self.assertEqual(original, argv)
        with self.assertRaises(m.Rejected):
            m.validate_argv(argv + ['-Dorg.gradle.jvmargs=-javaagent:/unsafe'],
                            {':starter:bootJar'}, [{'path': '/safe/local-release-metadata.init.gradle'}])

    def test_actual_test_filter_argv_is_preserved_not_executed(self):
        argv = self.f.ev['invocation']['argv']
        i = argv.index(':agent:test')
        argv[i + 1:i + 1] = ['--tests', 'cn.jia.SyntheticFixture.realMethod']
        self.run_fixture()

    def test_unpaired_init_and_tests_flags_rejected(self):
        original = list(self.f.ev['invocation']['argv'])
        for suffix in (['-I'], ['--tests'], ['--tests', 'synthetic-secret with spaces']):
            self.f.ev['invocation']['argv'] = original + suffix
            self.rejected(self.run_fixture, 'EVIDENCE_INVALID')

    def test_flow_environment_not_used_as_local_evidence(self):
        with mock.patch.dict(os.environ, {'BUILD_NUMBER': '999', 'CYF_FLOW_GRADLE_ACTIVE': '1', 'PIPELINE_ID': '5260799'}):
            # Explicitly reject mixed Flow identity, even if local evidence is valid.
            self.rejected(self.run_fixture, 'INPUT_INVALID')

    def test_source_changes_during_export_fail_before_publication(self):
        original = m.payloads
        def mutate(*args):
            result = original(*args)
            (self.f.source / 'settings.gradle').write_text('changed during export')
            return result
        with mock.patch.object(m, 'payloads', mutate):
            self.rejected(self.run_fixture, 'SOURCE_DIRTY')

    def test_missing_or_aliased_evidence_no_output(self):
        args = self.f.args()
        args.evidence = str(self.f.build / 'absent.json')
        with self.assertRaises(OSError):
            m.produce(args)
        alias = self.f.build / 'alias.json'
        alias.symlink_to(self.f.evidence_path)
        args.evidence = str(alias)
        self.rejected(lambda: m.produce(args), 'PATH_UNSAFE')

    def test_missing_proof_boundary_markers_and_reversed_order(self):
        original = self.f.log_path.read_text()
        for text in (original.replace('CYF_LOCAL_BOOTJAR_BEGIN', 'WRONG_BEGIN'),
                     original.replace('CYF_LOCAL_BOOTJAR_END', 'WRONG_END'),
                     original.replace('BUILD SUCCESSFUL', 'BUILD FAILED')):
            self.f.log_path.write_text(text)
            self.f.ev['invocation']['log'] = m.record(self.f.log_path)
            self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')
        lines = original.splitlines()
        begin = next(i for i, line in enumerate(lines) if line.startswith('CYF_LOCAL_BOOTJAR_BEGIN'))
        end = next(i for i, line in enumerate(lines) if line.startswith('CYF_LOCAL_BOOTJAR_END'))
        lines[begin], lines[end] = lines[end], lines[begin]
        self.f.log_path.write_text('\n'.join(lines) + '\n')
        self.f.ev['invocation']['log'] = m.record(self.f.log_path)
        self.rejected(self.run_fixture, 'BUILD_NOT_FRESH')

    def test_no_output_when_required_fixed_inputs_tampered(self):
        self.f.init.write_text('different init')
        self.rejected(self.run_fixture, 'EVIDENCE_TAMPERED')

    def test_output_cannot_live_under_source_or_build(self):
        for root in (self.f.source, self.f.build):
            args = self.f.args()
            args.output = str(root / 'unsafe.tgz')
            self.rejected(lambda: m.produce(args), 'PATH_UNSAFE')

    def test_malformed_evidence_cli_never_prints_original_values(self):
        original = copy.deepcopy(self.f.ev)
        for key, value in (('invocation', []), ('tests', 'synthetic-secret'), ('bootJar', None), ('sourceBefore', [])):
            self.f.ev = copy.deepcopy(original)
            self.f.ev[key] = value
            self.f.save_evidence()
            args = self.f.args()
            argv = ['python3', '-I', '-B', str(PRODUCER), '--opt-in']
            for name in ('source_root', 'commit', 'tree', 'version', 'build_id', 'build_root', 'evidence', 'evidence_sha256', 'output'):
                argv.extend(['--' + name.replace('_', '-'), str(getattr(args, name))])
            result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr, b'')
            self.assertNotIn(b'synthetic-secret', result.stdout)
            self.assertIn(m.strict_json(result.stdout)['code'], m.SAFE_CODES)

    def test_init_static_scope_and_original_security_order(self):
        text = INIT.read_text()
        self.assertIn("System.getenv('CYF_LOCAL_RELEASE_OPT_IN') != '1'", text)
        self.assertNotIn('CYF_FLOW_GRADLE_ACTIVE', text)
        self.assertIn("settings.settingsDir.canonicalFile != sourceRoot", text)
        self.assertIn("gradle.rootProject.projectDir.canonicalFile != sourceRoot", text)
        self.assertIn("org.springframework.boot.gradle.tasks.bundling.BootJar", text)
        self.assertIn("task.path != ':starter:bootJar'", text)
        self.assertIn("task.mustRunAfter(project.tasks.withType(org.gradle.api.tasks.testing.Test))", text)
        self.assertIn("task.mustRunAfter(gradle.rootProject.tasks.named('validateLayering'))", text)
        self.assertIn('task.inputs.properties(metadata)', text)
        self.assertIn('task.manifest.attributes(metadata)', text)
        self.assertNotIn("'Implementation-Version':", text)
        self.assertIn('gradle.projectsEvaluated', text)
        self.assertIn('StandardOpenOption.CREATE_NEW', text)
        self.assertEqual(1, text.count('tasks.withType'))  # enumeration only, not blanket task mutation
        self.assertIn('candidate instanceof org.gradle.api.tasks.compile.JavaCompile', text)
        self.assertIn('candidate.outputs.cacheIf { false }', text)
        self.assertIn('candidate instanceof org.gradle.api.tasks.testing.Test', text)
        self.assertIn('candidate.outputs.upToDateWhen { false }', text)
        self.assertNotIn('includeBuild(', text)
        self.assertNotIn('defaultTasks', text)
        self.assertNotIn('setActions', text)


if __name__ == '__main__':
    unittest.main()
