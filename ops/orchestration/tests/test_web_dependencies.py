"""Dependency store regressions. Synthetic packages only; no Web build/deploy."""
import ast
import base64
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import socketserver
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import web_dependencies as deps
from build_storage import build_environment


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=str(SCRIPTS)))
        self.source = self.tmp / 'source'
        self.source.mkdir()
        (self.source / 'package.json').write_text('{"name":"fixture","version":"1.0.0"}')
        (self.source / 'package-lock.json').write_text('{}')
        self.store = self.tmp / 'store'
        self.inputs = {'lock': 'fixture', 'node': 'fixture', 'npm': 'fixture'}
        self.log = (self.tmp / 'install.log').open('w')
        self.calls = []

    def tearDown(self):
        self.log.close()
        deps.discard_owned_staging(self.tmp)

    def install(self, argv, cwd, **kwargs):
        self.calls.append(argv)
        if argv[1] == 'ci':
            modules = Path(cwd) / 'node_modules'
            (modules / 'tiny').mkdir(parents=True)
            (modules / 'tiny' / 'package.json').write_text('{"version":"1.0.0"}')
            (modules / 'tiny' / 'cli.js').write_text('console.log("fixture")')
            (modules / 'tiny' / 'cli.js').chmod(0o755)
            (modules / '.bin').mkdir()
            (modules / '.bin' / 'tiny').symlink_to('../tiny/cli.js')

    def ensure(self, source=None, inputs=None):
        with patch.object(deps, 'identity', return_value=inputs or self.inputs), \
             patch.object(deps.subprocess, 'check_output', return_value=str(self.tmp)+'\n'), \
             patch.object(deps.subprocess, 'check_call', side_effect=self.install):
            return deps.ensure(source or self.source, self.store, {}, self.log)

    def test_same_inputs_share_without_reinstall(self):
        first = self.ensure()
        second_source = self.tmp / 'other'
        second_source.mkdir()
        second = self.ensure(second_source)
        self.assertFalse(first['reused'])
        self.assertTrue(second['reused'])
        self.assertEqual(first['path'], second['path'])
        self.assertEqual(2, len(self.calls))  # ci + ls, only once
        self.assertEqual((self.source / 'node_modules').resolve(), (second_source / 'node_modules').resolve())
        self.assertEqual(0o555, (self.source / 'node_modules/tiny/cli.js').stat().st_mode & 0o777)

    def test_different_lock_or_toolchain_separates(self):
        base = deps.key_for(self.inputs)
        for key in ('lock', 'node', 'npm'):
            changed = dict(self.inputs, **{key: 'different'})
            self.assertNotEqual(base, deps.key_for(changed))
        first = self.ensure()
        other = self.tmp / 'other'
        other.mkdir()
        second = self.ensure(other, dict(self.inputs, lock='new'))
        self.assertNotEqual(first['path'], second['path'])

    def test_existing_dependency_directory_is_not_modified(self):
        modules = self.source / 'node_modules'
        modules.mkdir()
        (modules / 'owned-by-other').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'leave it untouched'):
            self.ensure()
        self.assertEqual('keep', (modules / 'owned-by-other').read_text())
        self.assertEqual([], self.calls)

    def test_wrong_link_is_not_replaced(self):
        (self.source / 'node_modules').symlink_to(self.tmp / 'somebody-else')
        with self.assertRaisesRegex(ValueError, 'leave it untouched'):
            self.ensure()
        self.assertEqual(str(self.tmp / 'somebody-else'), os.readlink(str(self.source / 'node_modules')))

    def test_missing_changed_and_writable_files_rejected(self):
        result = self.ensure()
        root = Path(result['path'])
        file = root / 'node_modules/tiny/package.json'
        file.chmod(0o644)
        with self.assertRaises(ValueError):
            self.ensure()
        file.write_text('{"version":"bad"}')
        file.chmod(0o444)
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            self.ensure()
        file.parent.chmod(0o755)
        file.unlink()
        file.parent.chmod(0o555)
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            self.ensure()
        self.assertEqual(2, len(self.calls))  # never silently repair a published set

    def test_failed_install_never_publishes_or_attaches(self):
        def fail(*a, **kw):
            raise subprocess.CalledProcessError(1, ['npm', 'ci'])
        self.install = fail
        with self.assertRaises(subprocess.CalledProcessError):
            self.ensure()
        self.assertFalse((self.source / 'node_modules').exists())
        self.assertFalse((self.store / deps.key_for(self.inputs)).exists())
        self.assertEqual([], list(self.store.glob('.*')))

    def test_failed_completeness_check_never_publishes(self):
        install = self.install
        def incomplete(argv, **kwargs):
            if argv[1] == 'ls':
                raise subprocess.CalledProcessError(1, argv)
            return install(argv, **kwargs)
        self.install = incomplete
        with self.assertRaises(subprocess.CalledProcessError):
            self.ensure()
        self.assertFalse((self.store / deps.key_for(self.inputs)).exists())

    def test_external_link_rejected(self):
        modules = self.tmp / 'modules'
        modules.mkdir()
        (modules / 'escape').symlink_to(self.source / 'package.json')
        with self.assertRaisesRegex(ValueError, 'external or broken'):
            deps.inventory(modules)

    def test_incomplete_publication_rejected(self):
        (self.store / deps.key_for(self.inputs)).mkdir(parents=True)
        with self.assertRaises(FileNotFoundError):
            self.ensure()
        self.assertFalse((self.source / 'node_modules').exists())

    def test_tmpfs_store_rejected(self):
        with self.assertRaisesRegex(ValueError, 'tmpfs'):
            deps.ensure(self.source, Path('/dev/shm/cyf-never-create'), {}, self.log)

    def test_identity_keys_config_without_recording_secrets(self):
        (self.source / 'package-lock.json').write_text('{"lockfileVersion":3,"packages":{"":{}}}')
        config = {'registry': 'https://example.invalid', 'secret-token': 'private'}
        def output(argv, **kwargs):
            if argv[0] == 'node':
                return json.dumps(dict(version='v1', abi='1', platform='linux', arch='x64', execPath=sys.executable))
            if argv[1:3] == ['config', 'list']:
                return json.dumps(config)
            return '1.0.0'
        with patch.object(deps.subprocess, 'check_output', side_effect=output):
            first = deps.identity(self.source, {})
            config['registry'] = 'https://other.invalid'
            second = deps.identity(self.source, {})
        self.assertNotEqual(deps.key_for(first), deps.key_for(second))
        self.assertNotIn('private', json.dumps(first))

    def test_source_dependent_installs_not_silently_shared(self):
        (self.source / 'package.json').write_text('{"scripts":{"postinstall":"node local.js"}}')
        with self.assertRaisesRegex(ValueError, 'root lifecycle'):
            deps.identity(self.source, {})

    def test_per_key_lock_serializes_publication(self):
        # Two callers, no one observes the private incomplete staging directory.
        events = []
        install = self.install
        def slow(argv, **kwargs):
            if argv[1] == 'ci':
                events.append('install')
                entered.set()
                proceed.wait(3)
            return install(argv, **kwargs)
        entered, proceed = threading.Event(), threading.Event()
        other = self.tmp / 'other'
        other.mkdir()
        results, errors = [], []
        def worker(source):
            try:
                results.append(deps.ensure(source, self.store, {}, self.log))
            except Exception as exc:
                errors.append(exc)
        with patch.object(deps, 'identity', return_value=self.inputs), \
             patch.object(deps.subprocess, 'check_output', return_value=str(self.tmp)+'\n'), \
             patch.object(deps.subprocess, 'check_call', side_effect=slow):
            a = threading.Thread(target=worker, args=(self.source,))
            b = threading.Thread(target=worker, args=(other,))
            a.start()
            self.assertTrue(entered.wait(3))
            self.assertFalse((self.store / deps.key_for(self.inputs)).exists())
            b.start()
            proceed.set()
            a.join(5)
            b.join(5)
        self.assertEqual([], errors)
        self.assertEqual(['install'], events)
        self.assertEqual([False, True], sorted(r['reused'] for r in results))

    def test_staging_config_difference_stops_before_install(self):
        with patch.object(deps, 'identity', side_effect=[self.inputs, dict(self.inputs, config='changed')]), \
             patch.object(deps.subprocess, 'check_output', return_value=str(self.tmp)+'\n'), \
             patch.object(deps.subprocess, 'check_call') as install:
            with self.assertRaisesRegex(ValueError, 'staging npm configuration'):
                deps.ensure(self.source, self.store, {}, self.log)
            install.assert_not_called()
        self.assertFalse((self.store/deps.key_for(self.inputs)).exists())

    def test_existing_web_builder_wires_reuse_evidence_and_post_build_verification(self):
        text = (SCRIPTS/'local_web_build.py').read_text()
        ast.parse(text)
        self.assertIn('ensure_dependencies(S,args.dependency_store,env,log)', text)
        self.assertIn("verify_dependencies(P(R['dependencies']['path']),R['dependencies']['inputs'])", text)
        self.assertLess(text.index("run('build'"), text.index('  verify_dependencies('))
        self.assertIn("D/'web_dependencies.py'", text)
        self.assertIn("'receiptSha256'", text)
        self.assertNotIn("['npm','ci'", text)

    @unittest.skipUnless(Path('/home/isp/wsps/cyf/web/node_modules/vite/dist/node/index.js').exists(),
                         'existing Vite installation not available')
    def test_real_vite_adapter_uses_batch_output_not_shared_temp(self):
        # Tiny real Vite build, not the CYF production bundle. Never chmod or
        # install into the existing dependency tree used for this smoke test.
        modules = Path('/home/isp/wsps/cyf/web/node_modules')
        temp = modules / '.vite-temp'
        def state():
            return deps.inventory(temp) if temp.exists() else None
        before = state()
        (self.source / 'node_modules').symlink_to(modules)
        (self.source / 'package.json').write_text('{"type":"module"}')
        (self.source / 'vite.config.js').write_text(
            "import {defineConfig} from 'vite'; import path from 'node:path'; "
            "import {fileURLToPath} from 'node:url'; "
            "const root=path.dirname(fileURLToPath(import.meta.url)); "
            "export default defineConfig({resolve:{alias:{'@':path.resolve(root,'src')}},build:{minify:false}})")
        (self.source / 'index.html').write_text('<script type="module" src="/main.js"></script>')
        (self.source / 'src').mkdir()
        (self.source / 'src/feature.js').write_text('export const value=42')
        (self.source / 'main.js').write_text("import {value} from '@/feature.js'; console.log(value)")
        env = build_environment(self.tmp)
        env['PATH'] = '/home/isp/apps/node/bin:' + env.get('PATH', '')
        subprocess.check_call(['node', str(SCRIPTS/'local-web-build.mjs'), str(self.source), str(self.tmp/'dist')],
                              env=env, stdout=self.log, stderr=subprocess.STDOUT)
        self.assertTrue((self.tmp/'dist/index.html').is_file())
        self.assertEqual(before, state())
        self.assertFalse((self.source/'.vite').exists())

    @unittest.skipUnless(Path('/home/isp/apps/node/bin/npm').exists(), 'local Node/npm not available')
    def test_real_npm_ci_integrity_and_cross_source_reuse(self):
        # Real npm ci/ls, loopback tarball only, no external registry/model/service.
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:gz') as archive:
            payload = b'{"name":"cyf-tiny-fixture","version":"1.0.0","main":"index.js"}'
            for name, payload in [('package/package.json', payload), ('package/index.js', b'module.exports=42;')]:
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        blob = data.getvalue()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', str(len(blob)))
                self.end_headers()
                self.wfile.write(blob)
            def log_message(self, *args):
                pass
        server = socketserver.TCPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        try:
            package = dict(name='fixture', version='1.0.0', dependencies={'cyf-tiny-fixture':'1.0.0'})
            lock = dict(name='fixture', version='1.0.0', lockfileVersion=3, packages={
                '': package, 'node_modules/cyf-tiny-fixture': dict(version='1.0.0',
                resolved='http://127.0.0.1:{}/tiny.tgz'.format(server.server_address[1]),
                integrity='sha512-'+base64.b64encode(hashlib.sha512(blob).digest()).decode())})
            (self.source / 'package.json').write_text(json.dumps(package))
            (self.source / 'package-lock.json').write_text(json.dumps(lock))
            other = self.tmp / 'other'
            shutil.copytree(str(self.source), str(other))
            env = build_environment(self.tmp)
            env['PATH'] = '/home/isp/apps/node/bin:' + env.get('PATH', '')
            env['npm_config_cache'] = str(self.tmp / 'npm-cache')
            first = deps.ensure(self.source, self.store, env, self.log)
            second = deps.ensure(other, self.store, env, self.log)
            self.assertFalse(first['reused'])
            self.assertTrue(second['reused'])
            self.assertEqual(first['key'], second['key'])
            got = subprocess.check_output(['node', '-p', 'require("cyf-tiny-fixture")'], cwd=str(other), env=env)
            self.assertEqual(b'42', got.strip())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
