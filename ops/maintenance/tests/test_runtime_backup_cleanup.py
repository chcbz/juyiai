#!/usr/bin/python3
"""Isolated Runtime recovery-retention fixtures. No production deletion."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('runtime_retention', str(Path(__file__).resolve().parents[1] / 'runtime_backup_cleanup.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Tests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='runtime-retention-test.', dir='/root'))
        self.p = m.Paths()
        self.p.base = self.root / 'backups'
        self.p.base.mkdir()
        self.p.current = self.root / 'records/current.json'
        self.p.current.parent.mkdir()
        self.p.audit = self.root / 'audit/audit.jsonl'
        self.p.lock = self.root / 'host.lock'
        self.p.release_lock = self.root / 'release.lock'
        for p in (self.p.lock, self.p.release_lock):
            p.write_text(''); p.chmod(0o600)
        self.p.mountinfo = self.root / 'mounts'
        self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n')
        self.p.proc = self.root / 'proc'
        (self.p.proc / '123/fd').mkdir(parents=True)
        (self.p.proc / '123/maps').write_text('')
        self.bs = [self.batch(i) for i in range(4)]
        self.pin(self.bs[2])
        self.now = time.time() + 7200

    def tearDown(self):
        shutil.rmtree(self.root)

    def batch(self, i):
        p = self.p.base / ('20261026-fixture%d' % i)
        p.mkdir(mode=0o700)
        for n in ('RECOVERY.md', 'current.json'):
            (p / n).write_text('{}')
        (p / 'state.tar').write_text('state')
        (p / 'old-program/lib').mkdir(parents=True)
        (p / 'old-program/lib/code.py').write_text('program')
        time.sleep(.005)
        return p

    def pin(self, batch, status='verified-active'):
        self.p.current.write_text(json.dumps({'status': status, 'backup': str(batch)}))

    def collect(self):
        return m.collect(self.p, m.safe.proc.snapshot(self.p.proc), self.now)

    def clean(self):
        with mock.patch.object(m.time, 'time', return_value=self.now):
            return m.run(self.p, 'clean')

    def test_newest_two_and_current_pin(self):
        batches, protected, _, _ = self.collect()
        self.assertEqual({b['batch'] for b in batches}, {str(p) for p in self.bs[:2]})
        self.assertEqual(set(protected), {str(p) for p in self.bs[2:]})

    def test_current_pin_survives_outside_newest_two(self):
        self.pin(self.bs[0]); self.assertFalse(self.collect()[0])

    def test_grace_period(self):
        self.now = time.time(); self.assertFalse(self.collect()[0])

    def test_unknown_status_fails_closed(self):
        self.pin(self.bs[2], 'pending'); self.assertRaises(m.Unsafe, self.collect)

    def test_external_pin_rejected(self):
        self.pin(self.root); self.assertRaises(m.Unsafe, self.collect)

    def test_missing_pin_payload_fails_closed(self):
        p = self.bs[2]; (p/'state.tar').unlink(); (p/'old-program/lib/code.py').unlink()
        self.assertRaises(m.Unsafe, self.collect)

    def test_keep_ancestor_protects_all(self):
        (self.p.base/'.keep').symlink_to('missing'); self.assertRaises(m.Unsafe, self.collect)

    def test_batch_keep_protects(self):
        (self.bs[0]/'.keep').write_text(''); self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_nested_keep_skips_whole_batch(self):
        (self.bs[0]/'old-program/lib/.keep').write_text('')
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_hardlink_skips_whole_batch(self):
        os.link(self.bs[0]/'state.tar', self.root/'alias')
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def shared_program(self):
        source = self.bs[0]/'old-program/lib/code.py'
        alias = self.bs[0]/'old-program/image/tool'
        alias.parent.mkdir()
        os.link(source, alias)
        return source, alias

    def test_internal_program_links_collected_once_for_space(self):
        source, alias = self.shared_program()
        rows = m.collect_batch(self.p, self.bs[0])
        shared = [r for r in rows if r.get('shared')]
        self.assertEqual(len(shared), 2)
        self.assertEqual(sum(r['allocated'] for r in shared), source.stat().st_blocks*512)

    def test_internal_links_can_be_retired_without_touching_other_releases(self):
        source, alias = self.shared_program()
        # Test collect/clean independent of timestamps changed by creating links.
        rows = m.collect_batch(self.p, self.bs[0])
        remaining = {}
        for row in rows:
            if row.get('shared'):
                remaining.setdefault(tuple(row['signature'][:2]), []).append(row)
        for row in rows:
            m.unlink(self.p, row, remaining)
        self.assertFalse(source.exists()); self.assertFalse(alias.exists())
        self.assertEqual((self.bs[2]/'old-program/lib/code.py').read_text(), 'program')

    def test_clean_shared_links_across_chunks_counts_storage_once(self):
        source, alias = self.shared_program()
        for i in range(101):
            os.link(source, alias.parent/('tool%d' % i))
        for batch in self.bs[1:]:
            time.sleep(.005)
            os.utime(batch/'state.tar', None)
        expected = sum(r['allocated'] for b in self.collect()[0] for r in b['rows'])
        result = self.clean()
        self.assertEqual(result['removed_files'], 106)
        self.assertEqual(result['reclaimed_allocated_bytes'], expected)
        self.assertEqual(self.clean()['removed_files'], 0)
        self.assertFalse(source.exists()); self.assertFalse(alias.exists())

    def test_interrupted_clean_does_not_make_shared_survivor_newer_than_pin(self):
        self.shared_program()
        for batch in self.bs[1:]:
            time.sleep(.005); os.utime(batch/'state.tar', None)
        original = m.unlink
        seen = []
        def interrupt(paths, row, remaining=None):
            original(paths, row, remaining)
            if row.get('shared') and not seen:
                seen.append(row['path'])
                raise OSError('interrupted after unlink')
        with mock.patch.object(m, 'unlink', side_effect=interrupt):
            self.assertRaises(OSError, self.clean)
        result = self.clean()
        self.assertIn(str(self.bs[0]), result['retired_batches'])
        self.assertFalse((self.bs[0]/'old-program/lib/code.py').exists())

    def test_recent_new_content_in_partial_retirement_is_not_aged_by_intent(self):
        source, alias = self.shared_program()
        for batch in self.bs[1:]:
            time.sleep(.005); os.utime(batch/'state.tar', None)
        b = next(b for b in self.collect()[0] if b['batch'] == str(self.bs[0]))
        m.safe.atomic_json(self.bs[0]/'PAYLOAD_RETIRED.json', {
            'status': 'retiring-not-a-complete-recovery',
            'policy': 'newest-two-plus-current-pin',
            'payloadStamp': b['stamp'], 'batchIdentity': list(b['identity'])})
        source.write_text('new content after interrupted cleanup')
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])
        self.assertTrue(alias.exists())

    def test_active_shared_inode_protects_whole_batch(self):
        source, alias = self.shared_program()
        (self.p.proc/'123/fd/3').symlink_to(alias)
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])
        self.assertTrue(source.exists())

    def test_external_program_alias_rejected(self):
        source, alias = self.shared_program()
        os.link(source, self.root/'outside')
        self.assertRaises(m.Unsafe, m.collect_batch, self.p, self.bs[0])
        self.assertTrue(alias.exists())

    def test_new_external_alias_after_plan_rejected(self):
        source, alias = self.shared_program()
        rows = [r for r in m.collect_batch(self.p, self.bs[0]) if r.get('shared')]
        remaining = {tuple(rows[0]['signature'][:2]): rows}
        os.link(source, self.root/'outside')
        self.assertRaises(m.Unsafe, m.unlink, self.p, rows[0], remaining)
        self.assertTrue(source.exists()); self.assertTrue(alias.exists())

    def test_shared_source_write_between_unlinks_rejected(self):
        source, alias = self.shared_program()
        rows = [r for r in m.collect_batch(self.p, self.bs[0]) if r.get('shared')]
        remaining = {tuple(rows[0]['signature'][:2]): list(rows)}
        m.unlink(self.p, rows[0], remaining)
        Path(rows[1]['path']).write_text('modified')
        self.assertRaises(m.Unsafe, m.unlink, self.p, rows[1], remaining)

    def test_interrupted_shared_cleanup_can_be_replanned(self):
        self.shared_program()
        rows = [r for r in m.collect_batch(self.p, self.bs[0]) if r.get('shared')]
        remaining = {tuple(rows[0]['signature'][:2]): list(rows)}
        m.unlink(self.p, rows[0], remaining)
        fresh = m.collect_batch(self.p, self.bs[0])
        survivor = next(r for r in fresh if r['path'] == rows[1]['path'])
        self.assertFalse(survivor.get('shared'))
        m.unlink(self.p, survivor)

    def test_unsafe_mode_skips_whole_batch(self):
        (self.bs[0]/'state.tar').chmod(0o666)
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_symlink_batch_never_followed(self):
        self.bs[0].rename(self.root/'original'); self.bs[0].symlink_to(self.root/'original')
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_symlink_old_program_never_followed(self):
        shutil.rmtree(self.bs[0]/'old-program'); (self.bs[0]/'old-program').symlink_to(self.root)
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_active_fd_batch_protected(self):
        (self.p.proc/'123/fd/3').symlink_to(self.bs[0]/'state.tar')
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_active_cwd_batch_protected(self):
        (self.p.proc/'123/cwd').symlink_to(self.bs[0])
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_incomplete_proc_scan_aborts(self):
        (self.p.proc/'123/maps').write_text('bad')
        self.assertRaises(ValueError, self.collect)

    def test_mount_protects(self):
        self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n2 1 0:0 / %s rw - ext4 /dev/y rw\n' % self.bs[0])
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])

    def test_scan_limit_no_partial_batch(self):
        with mock.patch.object(m, 'MAX_FILES', 1):
            self.assertFalse(self.collect()[0])

    def test_plan_no_mutation(self):
        with mock.patch.object(m.time, 'time', return_value=self.now):
            r = m.run(self.p, 'plan')
        self.assertEqual(r['removed_files'], 0); self.assertTrue((self.bs[0]/'state.tar').exists())
        self.assertFalse(self.p.audit.exists())

    def test_clean_only_payloads_preserves_records(self):
        (self.bs[0]/'evidence.txt').write_text('evidence')
        r = self.clean(); self.assertEqual(r['removed_files'], 4)
        for p in self.bs[:2]:
            self.assertFalse((p/'state.tar').exists()); self.assertTrue((p/'RECOVERY.md').exists())
            self.assertTrue((p/'old-program/lib').is_dir())
            self.assertEqual(json.loads((p/'PAYLOAD_RETIRED.json').read_text())['status'], 'retired-not-a-complete-recovery')
        self.assertTrue((self.bs[0]/'evidence.txt').exists())
        self.assertTrue((self.bs[2]/'state.tar').exists()); self.assertTrue((self.bs[3]/'state.tar').exists())

    def test_symlink_leaf_unlinked_not_target(self):
        target = self.root/'outside'; target.write_text('retain')
        (self.bs[0]/'old-program/link').symlink_to(target)
        self.now += 7200
        # Mutation makes batch newest: force it old via a signature-only test.
        rows = m.collect_batch(self.p, self.bs[0])
        row = next(r for r in rows if r['path'].endswith('/link'))
        m.unlink(self.p, row); self.assertEqual(target.read_text(), 'retain')

    def test_payload_replacement_rejected(self):
        row = m.collect_batch(self.p, self.bs[0])[0]
        Path(row['path']).unlink(); Path(row['path']).write_text('changed')
        self.assertRaises(m.Unsafe, m.unlink, self.p, row)

    def test_release_busy_skips(self):
        with open(self.p.release_lock, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.clean()['removed_files'], 0)
        self.assertTrue((self.bs[0]/'state.tar').exists())

    def test_host_busy_skips(self):
        with open(self.p.lock, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.clean()['removed_files'], 0)

    def test_inherited_host_lock(self):
        with open(self.p.lock, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with mock.patch.object(m.time, 'time', return_value=self.now):
                self.assertEqual(m.run(self.p, 'clean', f.fileno())['removed_files'], 4)

    def test_audit_failure_before_delete(self):
        with mock.patch.object(m.safe.logger, 'open_log', side_effect=OSError('fixture')):
            self.assertRaises(OSError, self.clean)
        self.assertTrue((self.bs[0]/'state.tar').exists())

    def test_clean_idempotent(self):
        self.clean(); self.assertEqual(self.clean()['removed_files'], 0)

    def test_no_space_threshold_retention(self):
        with mock.patch.object(m.safe, 'free_bytes', return_value=100*1024**3):
            self.assertEqual(self.clean()['removed_files'], 4)


    def test_retired_metadata_does_not_consume_active_batch_limit(self):
        for i in range(513):
            p = self.p.base / ('20261026-retired%d' % i)
            p.mkdir()
            (p / 'PAYLOAD_RETIRED.json').write_text(json.dumps({
                'status': 'retired-not-a-complete-recovery',
                'policy': 'newest-two-plus-current-pin'}))
        self.assertEqual(len(self.collect()[0]), 2)

    def test_retired_batch_root_never_reused_for_new_deletion(self):
        self.clean()
        (self.bs[0] / 'state.tar').write_text('new data must be preserved')
        self.assertEqual(self.clean()['removed_files'], 0)
        self.assertTrue((self.bs[0] / 'state.tar').exists())

    def test_retirement_marker_symlink_never_followed(self):
        target = self.root / 'external-marker'
        target.write_text(json.dumps({'status': 'retired-not-a-complete-recovery',
                                      'policy': 'newest-two-plus-current-pin'}))
        (self.bs[0] / 'PAYLOAD_RETIRED.json').symlink_to(target)
        self.assertNotIn(str(self.bs[0]), [b['batch'] for b in self.collect()[0]])


if __name__ == '__main__':
    unittest.main()
