"""Worker transport regressions; isolated Git/files only, no SSH or production."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from remote_build import RemoteBuild, safe_extract


class RemoteBuildTest(unittest.TestCase):
    def make(self, folder):
        auth = folder / 'auth.json'
        auth.write_text(json.dumps({'JYT_BUILD_SERVER': '203.32.84.239',
                                   'JYT_BUILD_LOGIN': 'root', 'JYT_BUILD_PASSWORD': 'fixture-secret'}))
        known = folder / 'known_hosts'
        known.write_text('fixture-host-key\n')
        return RemoteBuild('203.32.84.239', Path('/home/isp/wsps/cyf-build/test-candidate'),
                           Path('/controller'), folder / 'evidence', known, auth)

    def test_strict_host_pin_no_secret_in_argv_environment_or_askpass(self):
        with tempfile.TemporaryDirectory() as d:
            worker = self.make(Path(d))
            self.assertIn('StrictHostKeyChecking=yes', worker.ssh)
            self.assertNotIn('fixture-secret', repr(worker.command(['echo', 'x; rm -rf /'])))
            self.assertNotIn('fixture-secret', repr(worker.environment()))
            self.assertNotIn('fixture-secret', worker.askpass.read_text())
            self.assertEqual(0o700, worker.askpass.stat().st_mode & 0o777)
            self.assertEqual(['echo', 'x; rm -rf /'], shlex.split(worker.command(['echo', 'x; rm -rf /'])[-1]))
            worker.close()
            self.assertFalse(worker.askpass.exists())

    def test_wrong_host_and_source_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            worker = self.make(Path(d)); worker.close()
            for host, root in [('other-host', '/home/isp/wsps/cyf-build/new'),
                               ('203.32.84.239', '/home/isp/hosts/cyf'),
                               ('203.32.84.239', '/home/isp/wsps/cyf-build/../escape')]:
                with self.assertRaises(ValueError):
                    RemoteBuild(host, Path(root), Path('/controller'), Path(d) / host.replace('.', '-') / 'evidence',
                                Path(d) / 'known_hosts', Path(d) / 'auth.json')

    def test_deadline_belongs_to_remote_build_not_ssh_or_installer(self):
        with tempfile.TemporaryDirectory() as d:
            worker = self.make(Path(d))
            command = worker.build_command(['/python', '-u', '/controller/ops/orchestration/local_build.py',
                '--source', '/source/api', '--output', '/home/isp/state/batch/api'], 'own-api-build', 487.9,
                Path('/source/api'), Path('/source/web'))
            remote = shlex.split(command[-1])
            self.assertEqual('systemd-run', remote[0])
            self.assertIn('--property=RuntimeMaxSec=487', remote)
            self.assertIn('--property=KillMode=control-group', remote)
            script = remote[-1]
            self.assertIn('/usr/bin/python3', script)
            self.assertIn(str(worker.root / 'controller/ops/orchestration/local_build.py'), script)
            self.assertIn(str(worker.root / 'api'), script)
            self.assertIn('/home/isp/state/batch/api', script)
            self.assertNotIn('fixture-secret', script)
            self.assertNotIn('flow-ci', script)
            self.assertNotIn('deploy', script)
            worker.close()

    def test_archive_filter_rejects_path_and_link_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name, link in [('../escape', None), ('link', '/etc/passwd')]:
                a = root / 'bad.tar'
                with tarfile.open(a, 'w') as tf:
                    info = tarfile.TarInfo(name)
                    if link:
                        info.type = tarfile.SYMTYPE; info.linkname = link; tf.addfile(info)
                    else:
                        info.size = 1; tf.addfile(info, io.BytesIO(b'x'))
                with self.assertRaises(tarfile.FilterError):
                    safe_extract(a, root / 'out')
            self.assertFalse((root / 'escape').exists())

    def test_source_snapshot_is_exact_commit_and_excludes_dirty_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root / 'source'; source.mkdir()
            def git(*argv):
                return subprocess.check_output(['git', '-C', str(source), *argv], text=True).strip()
            git('init', '-q'); git('config', 'user.name', 'fixture'); git('config', 'user.email', 'fixture@example.invalid')
            (source / 'docs/implementation').mkdir(parents=True)
            ledger = source / 'docs/implementation/TASKS.yaml'; ledger.write_text('old-ledger')
            (source / 'tracked').write_text('committed')
            git('add', '.'); git('commit', '-qm', 'fixture')
            expected = git('rev-parse', 'HEAD')
            (source / 'tracked').write_text('dirty')
            (source / 'secret.env').write_text('must-not-transfer')
            ledger.write_text('real-current-owner-ledger')
            worker = self.make(root)
            worker.root = root / 'remote'; worker.root.mkdir()
            def local_call(argv, **kw):
                argv = list(map(str, argv))
                if argv[0] == 'python3':
                    argv[0] = sys.executable
                return subprocess.run(argv, check=True, **kw)
            worker.call = local_call
            worker.prepare({'controller': source}, ledger)
            self.assertEqual(expected, worker.receipt['sources']['controller']['commit'])
            checkout = worker.root / 'controller'
            self.assertEqual('committed', (checkout / 'tracked').read_text())
            self.assertFalse((checkout / 'secret.env').exists())
            self.assertEqual('real-current-owner-ledger', (checkout / 'docs/implementation/TASKS.yaml').read_text())
            self.assertEqual('dirty', (source / 'tracked').read_text())
            worker.close()

    def test_collection_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            worker = self.make(Path(d)); existing = Path(d) / 'existing'; existing.mkdir()
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                worker.collect('api', existing)
            worker.close()


if __name__ == '__main__':
    unittest.main()
