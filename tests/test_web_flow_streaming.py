import contextlib
import fcntl
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / 'ops/ci/aliyun-flow/host/cyf-web-flow-deploy'
COMMIT = 'a' * 40


def load_helper(label):
    return importlib.machinery.SourceFileLoader('web_flow_stream_' + label, str(SCRIPT)).load_module()


def deterministic_bytes(label, size):
    result = bytearray()
    counter = 0
    seed = label.encode('ascii')
    while len(result) < size:
        result.extend(hashlib.sha256(seed + str(counter).encode('ascii')).digest())
        counter += 1
    return bytes(result[:size])


class HttpResponse(io.BytesIO):
    def __init__(self, value, status=200):
        io.BytesIO.__init__(self, value)
        self.status = status

    def getcode(self):
        return self.status


class StrictForwardReader(io.BytesIO):
    def __init__(self, value):
        io.BytesIO.__init__(self, value)
        self.bytes_read = 0
        self.seek_calls = 0

    def read(self, size=-1):
        value = io.BytesIO.read(self, size)
        self.bytes_read += len(value)
        return value

    def seek(self, offset, whence=0):
        self.seek_calls += 1
        raise AssertionError('compressed archive sought instead of streaming forward')


class CountingSeekReader(io.BytesIO):
    def __init__(self, value):
        io.BytesIO.__init__(self, value)
        self.bytes_read = 0
        self.backward_seeks = 0

    def read(self, size=-1):
        value = io.BytesIO.read(self, size)
        self.bytes_read += len(value)
        return value

    def seek(self, offset, whence=0):
        before = self.tell()
        position = io.BytesIO.seek(self, offset, whence)
        if position < before:
            self.backward_seeks += 1
        return position


class WebFlowStreamingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-web-stream-test-')
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def environment(self, label, run='92'):
        helper = load_helper(label)
        root = self.base / label / 'state'
        site = self.base / label / 'site'
        root.mkdir(parents=True, mode=0o700)
        site.mkdir(mode=0o755)
        downloads = root / 'downloads' / run
        downloads.mkdir(parents=True, mode=0o755)
        (site / 'assets').mkdir(mode=0o755)
        (site / 'index.html').write_bytes(b'old index')
        (site / 'assets/old.js').write_bytes(b'old asset')
        helper.ROOT = root
        helper.SITE = site
        helper.SITE_URL = 'https://fixture.invalid/'
        return helper, root, site, downloads / 'package.tgz'

    def manifest(self, content, commit=COMMIT, run='92', bad_path=None, bad_digest=False):
        files = []
        for name, value in content.items():
            files.append(dict(
                path=bad_path if bad_path is not None and name == 'index.html' else name,
                size=len(value),
                sha256='0' * 64 if bad_digest and name == 'index.html'
                else hashlib.sha256(value).hexdigest()))
        return dict(schema_version=1, pipeline_id='4403172', run_id=run, branch='develop',
                    commit=commit, files=files, package_version="1.14.0-consolidated.20261009")

    def archive_bytes(self, entries):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode='w:gz') as archive:
            for entry in entries:
                kind = entry[0]
                name = entry[1]
                if kind == 'file':
                    value = entry[2]
                    member = tarfile.TarInfo(name)
                    member.size = len(value)
                    archive.addfile(member, io.BytesIO(value))
                elif kind in ('dir', 'dir-sized'):
                    member = tarfile.TarInfo(name)
                    member.type = tarfile.DIRTYPE
                    member.mode = 0o755
                    if kind == 'dir-sized':
                        member.size = len(entry[2])
                        archive.addfile(member, io.BytesIO(entry[2]))
                    else:
                        archive.addfile(member)
                elif kind == 'symlink':
                    member = tarfile.TarInfo(name)
                    member.type = tarfile.SYMTYPE
                    member.linkname = entry[2]
                    archive.addfile(member)
                elif kind == 'hardlink':
                    member = tarfile.TarInfo(name)
                    member.type = tarfile.LNKTYPE
                    member.linkname = entry[2]
                    archive.addfile(member)
                else:
                    raise AssertionError('unknown fixture entry')
        return output.getvalue()

    def write_archive(self, package, entries):
        package.write_bytes(self.archive_bytes(entries))
        package.chmod(0o600)

    def snapshot(self, site):
        values = {}
        for path in sorted(site.rglob('*')):
            relative = str(path.relative_to(site))
            st = path.lstat()
            if stat.S_ISREG(st.st_mode):
                values[relative] = ('file', stat.S_IMODE(st.st_mode), path.read_bytes())
            elif stat.S_ISDIR(st.st_mode):
                values[relative] = ('dir', stat.S_IMODE(st.st_mode))
            elif stat.S_ISLNK(st.st_mode):
                values[relative] = ('symlink', os.readlink(str(path)))
            else:
                values[relative] = ('other', st.st_mode)
        return values

    def invoke(self, helper, pipeline='4403172', run='92'):
        package = helper.ROOT / 'downloads' / run / 'package.tgz'
        helper.deploy(pipeline, run, COMMIT, '1.14.0-consolidated.20261009',
                      hashlib.sha256(package.read_bytes()).hexdigest())

    def deploy(self, helper, content, run='92'):
        with mock.patch.object(helper.urllib.request, 'urlopen',
                               return_value=HttpResponse(content['index.html'])), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.invoke(helper, run=run)

    def test_reverse_tar_manifest_at_tail_stages_then_publishes_index_last(self):
        helper, root, site, package = self.environment('tail')
        content = {
            'index.html': b'<html>new tail</html>',
            'assets/a.js': b'new javascript',
            'assets/z.css': b'new css',
        }
        manifest = json.dumps(self.manifest(content), sort_keys=True).encode('utf-8')
        self.write_archive(package, [
            ('file', 'dist/index.html', content['index.html']),
            ('file', 'private-report/results.json', b'not public'),
            ('file', 'dist/assets/z.css', content['assets/z.css']),
            ('file', 'dist/assets/a.js', content['assets/a.js']),
            ('file', 'release.json', manifest),
        ])
        replacements = []
        stage_modes = []
        real_atomic_file = helper.atomic_file
        real_mkdtemp = helper.tempfile.mkdtemp

        def record_replace(path, source, mode):
            replacements.append(str(path.relative_to(site)))
            return real_atomic_file(path, source, mode)

        def record_stage(*args, **kwargs):
            name = real_mkdtemp(*args, **kwargs)
            stage_modes.append(stat.S_IMODE(os.lstat(name).st_mode))
            return name

        with mock.patch.object(helper, 'atomic_file', side_effect=record_replace), \
                mock.patch.object(helper.tempfile, 'mkdtemp', side_effect=record_stage):
            self.deploy(helper, content)

        self.assertEqual(replacements[-1], 'index.html')
        self.assertEqual(set(replacements[:-1]), {'assets/a.js', 'assets/z.css'})
        self.assertEqual(stage_modes, [0o700])
        for name, value in content.items():
            self.assertEqual((site / name).read_bytes(), value)
        self.assertFalse((site / 'private-report').exists())
        record = json.loads((root / 'record.json').read_text())
        self.assertEqual(record['status'], 'online_verified')
        self.assertEqual(record['phase'], 'online_verified')
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_manifest_at_head_and_archive_directories_after_files(self):
        helper, root, site, package = self.environment('head')
        content = {'index.html': b'head index', 'assets/app.js': b'head app'}
        manifest = json.dumps(self.manifest(content)).encode('utf-8')
        self.write_archive(package, [
            ('file', 'release.json', manifest),
            ('file', 'dist/index.html', content['index.html']),
            ('file', 'dist/assets/app.js', content['assets/app.js']),
            ('dir', 'dist/assets/'),
            ('dir', 'dist/'),
        ])
        self.deploy(helper, content)
        self.assertEqual((site / 'index.html').read_bytes(), content['index.html'])
        self.assertEqual((site / 'assets/app.js').read_bytes(), content['assets/app.js'])
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_gnu_tar_c_root_marker_package_installs_successfully(self):
        helper, root, site, package = self.environment('gnu-root')
        content = {'index.html': b'gnu root index', 'assets/app.js': b'gnu root app'}
        export = self.base / 'gnu-root' / 'export'
        (export / 'dist/assets').mkdir(parents=True)
        (export / 'release.json').write_text(json.dumps(self.manifest(content)))
        for name, value in content.items():
            (export / 'dist' / name).write_bytes(value)
        subprocess.check_call(['tar', '-C', str(export), '-czf', str(package), '.'])
        package.chmod(0o600)
        with tarfile.open(str(package), 'r:gz') as archive:
            first = archive.next()
            self.assertIn(first.name, ('.', './'))
            self.assertTrue(first.isdir())
            self.assertEqual(first.size, 0)
        self.deploy(helper, content)
        self.assertEqual((site / 'index.html').read_bytes(), content['index.html'])
        self.assertEqual((site / 'assets/app.js').read_bytes(), content['assets/app.js'])
        record = json.loads((root / 'record.json').read_text())
        self.assertEqual((record['status'], record['phase']), ('online_verified', 'online_verified'))
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_root_marker_file_link_duplicate_nonzero_and_traversal_are_rejected(self):
        content = {'index.html': b'new'}
        manifest = json.dumps(self.manifest(content)).encode('utf-8')
        attacks = {
            'root-file': [('file', '.', b'')],
            'root-symlink': [('symlink', '.', 'dist')],
            'root-hardlink': [('hardlink', '.', 'dist')],
            'root-nonzero-dir': [('dir-sized', '.', b'x')],
            'root-duplicate': [('dir', '.'), ('dir', './')],
            'root-no-bypass': [('dir', '.'), ('file', './dist/../escape', b'x')],
        }
        for label, attack in attacks.items():
            with self.subTest(label=label):
                helper, root, site, package = self.environment(label)
                self.write_archive(package, attack + [
                    ('file', './dist/index.html', content['index.html']),
                    ('file', './release.json', manifest),
                ])
                before = self.snapshot(site)
                with self.assertRaisesRegex(SystemExit, 'unsafe archive entry'):
                    self.deploy(helper, content)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])
                self.assertFalse((root / 'record.json').exists())

    def test_hash_and_commit_failures_leave_public_tree_unchanged_and_clean_stage(self):
        cases = [('hash', self.manifest({'index.html': b'new'}, bad_digest=True), 'digest mismatch'),
                 ('commit', self.manifest({'index.html': b'new'}, commit='b' * 40), 'does not match')]
        for label, manifest, message in cases:
            with self.subTest(label=label):
                helper, root, site, package = self.environment(label)
                content = {'index.html': b'new'}
                self.write_archive(package, [
                    ('file', 'dist/index.html', content['index.html']),
                    ('file', 'release.json', json.dumps(manifest).encode('utf-8')),
                ])
                before = self.snapshot(site)
                with self.assertRaisesRegex(SystemExit, message):
                    self.deploy(helper, content)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])
                self.assertFalse((root / 'record.json').exists())

    def test_malicious_entries_are_rejected_without_public_mutation(self):
        content = {'index.html': b'new'}
        manifest = json.dumps(self.manifest(content)).encode('utf-8')
        attacks = {
            'traversal': [('file', 'dist/../escape', b'x')],
            'symlink': [('symlink', 'dist/link', '../../outside')],
            'hardlink': [('hardlink', 'dist/link', 'dist/index.html')],
            'duplicate': [('file', 'dist/index.html', b'new'), ('file', './dist/index.html', b'new')],
            'noncanonical': [('file', 'dist//index.html', b'new')],
        }
        for label, attack in attacks.items():
            with self.subTest(label=label):
                helper, root, site, package = self.environment('attack-' + label)
                entries = attack + [('file', 'release.json', manifest)]
                if label not in ('duplicate', 'noncanonical'):
                    entries.insert(0, ('file', 'dist/index.html', content['index.html']))
                self.write_archive(package, entries)
                before = self.snapshot(site)
                with self.assertRaisesRegex(SystemExit, 'unsafe archive entry'):
                    self.deploy(helper, content)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])
                self.assertFalse((root / 'record.json').exists())

    def test_manifest_coverage_size_and_path_remain_fail_closed(self):
        cases = []
        base = {'index.html': b'new index', 'assets/app.js': b'app'}
        missing = self.manifest(base)
        missing['files'] = missing['files'][:1]
        cases.append(('coverage', base, missing, 'dist differs'))
        wrong_size = self.manifest(base)
        wrong_size['files'][0]['size'] += 1
        cases.append(('size', base, wrong_size, 'digest mismatch'))
        bad_path = self.manifest(base, bad_path='../index.html')
        cases.append(('path', base, bad_path, 'invalid manifest path'))
        for label, content, manifest, message in cases:
            with self.subTest(label=label):
                helper, root, site, package = self.environment('manifest-' + label)
                self.write_archive(package,
                                   [('file', 'dist/' + name, value) for name, value in content.items()] +
                                   [('file', 'release.json', json.dumps(manifest).encode('utf-8'))])
                before = self.snapshot(site)
                with self.assertRaisesRegex(SystemExit, message):
                    self.deploy(helper, content)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def online_fixture(self, label):
        helper, root, site, package = self.environment('online-' + label)
        content = {'index.html': b'new online index'}
        self.write_archive(package, [
            ('file', 'release.json', json.dumps(self.manifest(content)).encode('utf-8')),
            ('file', 'dist/index.html', content['index.html']),
        ])
        return helper, root, site, content

    def parse_online_logs(self, value):
        prefix = 'CYF_WEB_FLOW_ONLINE_VERIFY '
        return [json.loads(line[len(prefix):]) for line in value.splitlines() if line.startswith(prefix)]

    def assert_request_contract(self, request, attempt):
        headers = dict((key.lower(), value) for key, value in request.header_items())
        self.assertEqual(headers['accept-encoding'], 'identity')
        self.assertEqual(headers['cache-control'], 'no-cache, no-store, max-age=0')
        self.assertEqual(headers['pragma'], 'no-cache')
        self.assertIn('pipeline/4403172 run/92 commit/' + COMMIT, headers['user-agent'])
        self.assertEqual(headers['x-cyf-flow-identity'], '4403172/92/' + COMMIT)
        self.assertIn('flow_pipeline=4403172', request.full_url)
        self.assertIn('flow_run=92', request.full_url)
        self.assertIn('flow_commit=' + COMMIT, request.full_url)
        self.assertIn('flow_verify_attempt=' + str(attempt), request.full_url)

    def test_online_transient_mismatch_then_match_retries_read_only_and_marks_verified(self):
        helper, root, site, content = self.online_fixture('transient')
        requests = []
        responses = [HttpResponse(b'x' * len(content['index.html'])), HttpResponse(content['index.html'])]

        def respond(request, timeout):
            requests.append((request, timeout))
            return responses[len(requests) - 1]

        stderr = io.StringIO()
        with mock.patch.object(helper.urllib.request, 'urlopen', side_effect=respond), \
                mock.patch.object(helper.time, 'sleep') as sleep, \
                mock.patch.object(helper, 'atomic_file', wraps=helper.atomic_file) as publish, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            self.invoke(helper)
        self.assertEqual(len(requests), 2)
        self.assertEqual(publish.call_count, 1)
        sleep.assert_called_once_with(2)
        for number, (request, timeout) in enumerate(requests, 1):
            self.assertEqual(timeout, 30)
            self.assert_request_contract(request, number)
        events = self.parse_online_logs(stderr.getvalue())
        self.assertEqual([event['match'] for event in events], [False, True])
        self.assertEqual([event['status'] for event in events], [200, 200])
        self.assertEqual([event['length'] for event in events], [len(content['index.html'])] * 2)
        self.assertTrue(all(event['request_identity'] == '4403172/92/' + COMMIT for event in events))
        self.assertTrue(all(event['accept_encoding'] == 'identity' for event in events))
        self.assertTrue(all(event['cache_control'] == 'no-cache, no-store, max-age=0' for event in events))
        self.assertTrue(all('pipeline/4403172 run/92 commit/' + COMMIT in event['user_agent'] for event in events))
        self.assertNotEqual(events[0]['actual_sha256'], events[0]['expected_sha256'])
        self.assertEqual(events[1]['actual_sha256'], events[1]['expected_sha256'])
        record = json.loads((root / 'record.json').read_text())
        self.assertEqual((record['status'], record['phase']), ('online_verified', 'online_verified'))
        self.assertEqual((site / 'index.html').read_bytes(), content['index.html'])
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_online_mismatch_waits_beyond_three_attempts_until_external_cancellation(self):
        helper, root, site, content = self.online_fixture('permanent')
        wrong = b'y' * len(content['index.html'])
        stderr = io.StringIO()
        with mock.patch.object(helper.urllib.request, 'urlopen', side_effect=[HttpResponse(wrong) for _ in range(4)]) as urlopen, \
                mock.patch.object(helper.time, 'sleep', side_effect=[None, None, None, KeyboardInterrupt()]) as sleep, \
                contextlib.redirect_stderr(stderr):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke(helper)
        self.assertEqual(urlopen.call_count, 4)
        self.assertEqual(sleep.call_args_list, [mock.call(2)] * 4)
        events = self.parse_online_logs(stderr.getvalue())
        self.assertEqual(len(events), 4)
        self.assertTrue(all(event['status'] == 200 and not event['match'] for event in events))
        self.assertTrue(all(event['actual_sha256'] != event['expected_sha256'] for event in events))
        record = json.loads((root / 'record.json').read_text())
        self.assertEqual((record['status'], record['phase']), ('installed', 'installed'))
        self.assertEqual((site / 'index.html').read_bytes(), content['index.html'])
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_online_exceptions_are_logged_until_external_cancellation(self):
        helper, root, site, content = self.online_fixture('exception')
        stderr = io.StringIO()
        with mock.patch.object(helper.urllib.request, 'urlopen', side_effect=OSError('fixture failure')) as urlopen, \
                mock.patch.object(helper.time, 'sleep', side_effect=[None, None, None, KeyboardInterrupt()]) as sleep, \
                contextlib.redirect_stderr(stderr):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke(helper)
        self.assertEqual(urlopen.call_count, 4)
        self.assertEqual(sleep.call_args_list, [mock.call(2)] * 4)
        events = self.parse_online_logs(stderr.getvalue())
        self.assertEqual(len(events), 4)
        self.assertTrue(all(event['error_type'] == 'OSError' for event in events))
        self.assertTrue(all(event['status'] is None and event['length'] == 0 for event in events))
        empty_digest = hashlib.sha256(b'').hexdigest()
        self.assertTrue(all(event['actual_sha256'] == empty_digest and not event['match'] for event in events))
        record = json.loads((root / 'record.json').read_text())
        self.assertEqual((record['status'], record['phase']), ('installed', 'installed'))
        self.assertEqual((site / 'index.html').read_bytes(), content['index.html'])
        self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_old_run_and_unsafe_public_target_are_rejected_before_publish(self):
        for label, unsafe_target in [('old-run', False), ('target', True)]:
            with self.subTest(label=label):
                helper, root, site, package = self.environment(label)
                content = {'index.html': b'new', 'assets/app.js': b'app'}
                self.write_archive(package, [
                    ('file', 'release.json', json.dumps(self.manifest(content)).encode('utf-8')),
                    ('file', 'dist/index.html', content['index.html']),
                    ('file', 'dist/assets/app.js', content['assets/app.js']),
                ])
                if unsafe_target:
                    (site / 'assets/app.js').symlink_to('/tmp/not-used')
                    message = 'unsafe site target'
                else:
                    (root / 'record.json').write_text('{"run_id":"93"}')
                    (root / 'record.json').chmod(0o600)
                    message = 'older'
                before = self.snapshot(site)
                with self.assertRaisesRegex(SystemExit, message):
                    self.deploy(helper, content)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])

    def test_identity_failure_and_lock_cancellation_leave_publication_unchanged(self):
        content = {'index.html': b'new'}
        entries = [
            ('file', 'release.json', json.dumps(self.manifest(content)).encode('utf-8')),
            ('file', 'dist/index.html', content['index.html']),
            ('file', 'private-report/result.json', b'x'),
        ]
        for label in ('identity', 'lock'):
            with self.subTest(label=label):
                helper, root, site, package = self.environment('guard-' + label)
                self.write_archive(package, entries)
                before = self.snapshot(site)
                held = None
                try:
                    if label == 'identity':
                        with self.assertRaisesRegex(SystemExit, 'invalid execution identity'):
                            self.invoke(helper, pipeline='4403173')
                    elif label == 'lock':
                        # The production lock waits rather than rejecting contention.
                        # Simulate caller cancellation at that wait, never deadlock the test.
                        with mock.patch.object(helper.fcntl, 'flock', side_effect=KeyboardInterrupt()) as flock:
                            with self.assertRaises(KeyboardInterrupt):
                                self.deploy(helper, content)
                        self.assertEqual(flock.call_args[0][1], fcntl.LOCK_EX)
                finally:
                    if held is not None:
                        os.close(held)
                self.assertEqual(self.snapshot(site), before)
                self.assertEqual(list(root.glob('.cyf-web-stage-*')), [])
                self.assertFalse((root / 'record.json').exists())

    def test_single_pass_small_archive_reads_each_file_once_without_backward_seek(self):
        helper = load_helper('single-pass')
        content = {
            'index.html': deterministic_bytes('index', 1024 * 1024),
            'assets/a.js': deterministic_bytes('a', 1024 * 1024),
            'assets/b.js': deterministic_bytes('b', 1024 * 1024),
        }
        manifest = json.dumps(self.manifest(content), sort_keys=True).encode('utf-8')
        entries = [('file', 'dist/index.html', content['index.html']),
                   ('file', 'dist/assets/b.js', content['assets/b.js']),
                   ('file', 'release.json', manifest),
                   ('file', 'dist/assets/a.js', content['assets/a.js'])]
        blob = self.archive_bytes(entries)
        self.assertLessEqual(sum(len(value) for value in content.values()) + len(manifest), 8 * 1024 * 1024)
        stage = self.base / 'stream-stage'
        stage.mkdir(mode=0o700)
        stream = StrictForwardReader(blob)
        extract_counts = {}
        original_extractfile = tarfile.TarFile.extractfile

        def counted_extractfile(archive, member):
            extract_counts[member.name] = extract_counts.get(member.name, 0) + 1
            return original_extractfile(archive, member)

        with mock.patch.object(tarfile.TarFile, 'extractfile', counted_extractfile):
            manifest_bytes, staged = helper.scan_archive(stream, stage)
        helper.validate_manifest(manifest_bytes, staged, '4403172', '92', COMMIT)
        self.assertEqual(stream.seek_calls, 0)
        self.assertLessEqual(stream.bytes_read, len(blob))
        self.assertTrue(extract_counts)
        self.assertEqual(set(extract_counts.values()), {1})

        # Reproduce the former getmembers + validation read + install read pattern only
        # on this <=8 MiB synthetic archive; it must re-read compressed bytes and seek back.
        old = CountingSeekReader(blob)
        with tarfile.open(fileobj=old, mode='r:gz') as archive:
            members = archive.getmembers()
            for member in members:
                if member.isfile() and (member.name == 'release.json' or member.name.startswith('dist/')):
                    archive.extractfile(member).read()
            for member in members:
                if member.isfile() and member.name.startswith('dist/'):
                    archive.extractfile(member).read()
        self.assertGreater(old.backward_seeks, 0)
        self.assertGreater(old.bytes_read, stream.bytes_read)
        print('STREAMING_IO_EVIDENCE ' + json.dumps(dict(
            archive_bytes=len(blob), forward_compressed_bytes=stream.bytes_read,
            forward_seek_calls=stream.seek_calls, member_extract_calls=sum(extract_counts.values()),
            legacy_compressed_bytes=old.bytes_read, legacy_backward_seeks=old.backward_seeks), sort_keys=True))

    def test_source_forbids_member_catalogs_and_uses_stream_mode(self):
        source = SCRIPT.read_text()
        self.assertIn("mode='r|gz'", source)
        self.assertNotIn('.getmembers(', source)
        self.assertNotIn('.getmember(', source)
        self.assertNotIn('extractall(', source)
        self.assertNotIn('.read_bytes()', source)


if __name__ == '__main__':
    unittest.main()
