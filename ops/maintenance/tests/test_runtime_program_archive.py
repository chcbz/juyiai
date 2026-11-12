#!/usr/bin/python3
"""Real GNU tar/gzip fixtures only; never change production backups or services."""
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('program_archive', str(Path(__file__).resolve().parents[1] / 'runtime_backup_cleanup.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ProgramArchiveTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='runtime-program-archive-test.', dir='/root'))
        self.p = m.Paths()
        self.p.base = self.root / 'backups'; self.p.base.mkdir()
        self.p.current = self.root / 'records/current.json'; self.p.current.parent.mkdir()
        self.p.audit = self.root / 'audit/audit.jsonl'
        self.p.lock = self.root / 'host.lock'; self.p.release_lock = self.root / 'release.lock'
        for lock in (self.p.lock, self.p.release_lock):
            lock.write_text(''); lock.chmod(0o600)
        self.p.mountinfo = self.root / 'mounts'
        self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n')
        self.p.proc = self.root / 'proc'
        (self.p.proc / '123/fd').mkdir(parents=True)
        (self.p.proc / '123/maps').write_text('')
        self.p.restore_bases = [self.root]
        self.batch = self.p.base / '20261109-fixture'; self.batch.mkdir(mode=0o700)
        self.source = self.batch / 'old-program'; self.source.mkdir(mode=0o700)
        (self.source / 'lib').mkdir()
        (self.source / 'lib/code.py').write_text('print("recovery")\n' * 100)
        (self.source / 'lib/code.py').chmod(0o750)
        (self.source / 'internal').symlink_to('lib/code.py')
        # Final-path venv links are leaves, not archive extraction destinations.
        (self.source / 'external-python').symlink_to('/usr/bin/python3')
        os.link(str(self.source / 'lib/code.py'), str(self.source / 'alias.py'))
        with (self.source / 'sparse').open('wb') as f:
            f.seek(512 * 1024); f.write(b'end')
        (self.batch / 'current.json').write_text('{}')
        (self.batch / 'RECOVERY.md').write_text('Preserve current facts; no automatic state rollback.')
        (self.batch / 'state.tar.gz').write_bytes(b'untouched-state-fixture')
        self.p.current.write_text(json.dumps({'status': 'verified-active', 'backup': str(self.batch)}))
        self.repin()

    def tearDown(self):
        shutil.rmtree(str(self.root))

    def repin(self):
        self.tree = m.program_tree(self.source)
        rows = []
        for name, e in self.tree['entries'].items():
            row = dict(path=name, **{k: e[k] for k in ('type', 'mode', 'uid', 'gid')})
            for k in ('sha256', 'target'):
                if k in e: row[k] = e[k]
            rows.append(row)
        self.manifest = self.batch / 'current.manifest.json'
        self.manifest.write_text(json.dumps(rows))
        self.sha = m.program_digest(self.manifest)
        self.original_record = self.p.current.read_bytes()

    def compact(self):
        return m.run_program(self.p, 'compact-program', self.batch, self.sha)

    def restore(self, dest=None):
        dest = dest or self.root / 'cyf-runtime-restore-fixture'
        result = m.run_program(self.p, 'restore-program', self.batch, self.sha, dest)
        self.assertEqual(result['status'], 'restored-to-staging-not-activated')
        self.assertEqual(m.program_tree(dest), self.tree)
        return dest

    def test_roundtrip_keeps_links_metadata_and_state(self):
        before = (self.batch / 'state.tar.gz').read_bytes()
        self.assertEqual(self.compact()['status'], 'compacted')
        self.assertFalse(self.source.exists())
        dest = self.restore()
        self.assertEqual((dest / 'alias.py').stat().st_ino, (dest / 'lib/code.py').stat().st_ino)
        self.assertEqual(os.readlink(str(dest / 'external-python')), '/usr/bin/python3')
        self.assertEqual((self.batch / 'state.tar.gz').read_bytes(), before)
        self.assertEqual(self.p.current.read_bytes(), self.original_record)
        self.assertTrue(self.compact()['alreadyComplete'])

    def test_real_process_snapshot(self):
        self.p.proc = Path('/proc')
        self.compact(); self.restore()

    def test_acl_xattr_and_group_survive(self):
        file = self.source / 'lib/code.py'
        os.chown(str(file), 0, 65534)
        os.setxattr(str(file), 'user.cyf-fixture', b'preserve-attributes')
        subprocess.run(['setfacl', '-m', 'u:65534:r--', str(file)], check=True)
        self.repin(); self.compact(); dest = self.restore()
        self.assertEqual(os.getxattr(str(dest / 'lib/code.py'), 'user.cyf-fixture'), b'preserve-attributes')
        self.assertEqual((dest / 'lib/code.py').stat().st_gid, 65534)

    def test_wrong_pinned_digest_no_mutation(self):
        with self.assertRaises(m.Unsafe):
            m.run_program(self.p, 'compact-program', self.batch, '0' * 64)
        self.assertTrue(self.source.exists())
        self.assertFalse((self.batch / 'old-program.tar.gz').exists())

    def test_external_hardlink_rejected(self):
        os.link(str(self.source / 'lib/code.py'), str(self.root / 'outside'))
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())

    def test_manifest_drift_rejected(self):
        (self.source / 'lib/code.py').write_text('changed')
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())

    def test_existing_archive_not_adopted(self):
        (self.batch / 'old-program.tar.gz').write_bytes(b'unknown')
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())

    def test_source_keep_protects(self):
        (self.source / '.keep').write_text('')
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())

    def test_mounted_source_protects(self):
        self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n2 1 0:1 / '+str(self.source)+' rw - ext4 /dev/y rw\n')
        with self.assertRaises(m.Unsafe): self.compact()

    def test_busy_host_or_release_lock(self):
        for lock in (self.p.lock, self.p.release_lock):
            with lock.open('r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError): self.compact()
        self.assertTrue(self.source.exists())

    def test_active_program_protects(self):
        (self.p.proc / '123/fd/3').symlink_to(self.source / 'lib/code.py')
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())

    def test_compression_failure_keeps_source(self):
        with mock.patch.object(subprocess, 'run', side_effect=subprocess.CalledProcessError(2, 'tar')):
            with self.assertRaises(subprocess.CalledProcessError): self.compact()
        self.assertTrue(self.source.exists())
        self.assertFalse((self.batch / 'old-program.tar.gz').exists())
        self.assertFalse(list(self.batch.glob('.program-archive-*.tmp')))

    def test_independent_verification_failure_keeps_source(self):
        with mock.patch.object(m, 'extract_program', side_effect=m.Unsafe('restore check failed')):
            with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())
        self.assertFalse((self.batch / 'old-program.tar.gz').exists())

    def test_interrupted_directory_retirement_can_resume(self):
        original = m.unlink; calls = []
        def interrupt(*args):
            if calls: raise OSError('fixture interruption')
            calls.append(True); return original(*args)
        with mock.patch.object(m, 'unlink', side_effect=interrupt):
            with self.assertRaises(OSError): self.compact()
        self.assertTrue(self.source.exists())
        self.restore()  # Complete recovery remains available despite partial unlink.
        self.assertEqual(self.compact()['status'], 'compacted')
        self.assertFalse(self.source.exists())

    def test_resume_rejects_extra_file(self):
        with mock.patch.object(m, 'unlink', side_effect=OSError('fixture interruption')):
            with self.assertRaises(OSError): self.compact()
        (self.source / 'unknown').write_text('do not delete')
        with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue((self.source / 'unknown').exists())

    def test_tampered_archive_rejected(self):
        self.compact()
        with (self.batch / 'old-program.tar.gz').open('ab') as f: f.write(b'changed')
        with self.assertRaises(m.Unsafe): self.restore()

    def test_existing_destination_never_overwritten(self):
        self.compact(); destination = self.root / 'cyf-runtime-restore-existing'; destination.mkdir()
        (destination / 'keep').write_text('old')
        with self.assertRaises(FileExistsError): self.restore(destination)
        self.assertEqual((destination / 'keep').read_text(), 'old')

    def test_live_or_nonstaging_destination_refused(self):
        self.compact()
        for dest in (self.root / 'app', Path('/home/isp/apps/cyf-agent-runtime-v1/app')):
            with self.assertRaises(m.Unsafe): self.restore(dest)

    def test_malicious_archive_members_rejected(self):
        bads = [('path', '../outside'), ('absolute', '/outside'), ('fifo', 'fifo'), ('duplicate', 'x'),
                ('symlink-parent', 'x/y'), ('hardlink-outside', 'x')]
        for kind, name in bads:
            p = self.root / (kind + '.tgz')
            with tarfile.open(str(p), 'w:gz') as t:
                root = tarfile.TarInfo('.'); root.type = tarfile.DIRTYPE; t.addfile(root)
                if kind == 'symlink-parent':
                    link = tarfile.TarInfo('x'); link.type = tarfile.SYMTYPE; link.linkname = '/tmp'; t.addfile(link)
                v = tarfile.TarInfo(name)
                if kind == 'fifo': v.type = tarfile.FIFOTYPE
                if kind == 'hardlink-outside': v.type = tarfile.LNKTYPE; v.linkname = '../outside'
                t.addfile(v)
                if kind == 'duplicate': t.addfile(v)
            with self.assertRaises(m.Unsafe): m.program_tar_members(p)

    def test_receipt_write_failure_never_deletes_original(self):
        with mock.patch.object(m.safe, 'atomic_json', side_effect=OSError('fixture disk full')):
            with self.assertRaises(OSError): self.compact()
        self.assertEqual(m.program_tree(self.source), self.tree)
        self.assertTrue((self.batch / 'old-program.tar.gz').exists())
        # Unknown archive is preserved for explicit reconciliation, never adopted.
        with self.assertRaises(m.Unsafe): self.compact()

    def test_source_changed_after_compression_never_deleted(self):
        original = subprocess.run
        def changed(argv, **kwargs):
            result = original(argv, **kwargs)
            if '--create' in argv:
                (self.source / 'lib/code.py').write_text('source drift')
            return result
        with mock.patch.object(subprocess, 'run', side_effect=changed):
            with self.assertRaises(subprocess.CalledProcessError): self.compact()
        self.assertEqual((self.source / 'lib/code.py').read_text(), 'source drift')

    def test_archive_changed_during_directory_retirement_stops(self):
        original = m.unlink; changed = []
        def drift(*args):
            result = original(*args)
            if not changed:
                with (self.batch / 'old-program.tar.gz').open('ab') as f: f.write(b'drift')
                changed.append(True)
            return result
        with mock.patch.object(m, 'unlink', side_effect=drift):
            with self.assertRaises(m.Unsafe): self.compact()
        self.assertTrue(self.source.exists())
        self.assertNotEqual(json.loads((self.batch / 'program-archive.json').read_text())['status'], 'compacted')

    def test_compressed_payload_is_compatible_with_existing_retention(self):
        self.compact()
        rows = m.collect_batch(self.p, self.batch)
        self.assertIn(str(self.batch / 'old-program.tar.gz'), [r['path'] for r in rows])
        self.assertNotIn(str(self.batch / 'program-archive.json'), [r['path'] for r in rows])


if __name__ == '__main__': unittest.main(verbosity=2)
