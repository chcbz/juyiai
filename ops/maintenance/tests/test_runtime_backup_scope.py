import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'runtime_backup_scope.py'
spec = importlib.util.spec_from_file_location('runtime_scope', str(SCRIPT))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-state-scope-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'state'; self.root.mkdir()
        self.home = self.root / 'unified/agents/owner/codex-home'; self.home.mkdir(parents=True)
        self.inspect = self.home.parent / 'inspection-state/abcdef'
        self.inspect.mkdir(parents=True)

    def put(self, p, text='recovery'):
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text); return p

    def log(self, path=None):
        path = path or self.home / 'logs_2.sqlite'
        path.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(str(path))
        c.execute('CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, ts_nanos INTEGER, level TEXT, target TEXT, feedback_log_body TEXT, module_path TEXT, file TEXT, line INTEGER, thread_id TEXT, process_uuid TEXT, estimated_bytes INTEGER)')
        c.execute('CREATE TABLE _sqlx_migrations (version INTEGER)'); c.commit(); c.close()
        return path

    def test_omit_schema_confirmed_diagnostics_and_companions(self):
        self.log(); self.put(self.home / 'logs_2.sqlite-wal'); self.put(self.home / 'logs_2.sqlite-shm')
        result = m.plan([self.root])
        self.assertEqual(len(result['excluded']), 3)
        self.assertTrue(all(x['reason'] == 'schema-confirmed-diagnostic-log' for x in result['excluded']))

    def test_never_infer_unknown_sqlite_is_disposable(self):
        db = self.log(); c = sqlite3.connect(str(db)); c.execute('CREATE TABLE recovery (id TEXT)'); c.commit(); c.close()
        self.assertFalse(m.diagnostic_database(db))
        self.assertFalse(m.plan([self.root])['excluded'])

    def test_same_name_outside_codex_home_is_retained(self):
        self.log(self.root / 'logs_2.sqlite')
        self.assertFalse(m.plan([self.root])['excluded'])

    def test_preserves_auth_state_ack_sessions_requests_conversations_and_tmp(self):
        for name in ('auth.json','state_5.sqlite','queue_1.sqlite-wal','sessions/history.jsonl','tmp/unknown.data','logs_9.sqlite'):
            self.put(self.home / name)
        for name in ('requests/deadbeef/binding.json','conversations/deadbeef/codex-home/state_5.sqlite','measurement/unknown/binding.json'):
            self.put(self.inspect / name)
        result = m.plan([self.root]); self.assertFalse(result['excluded'])
        self.assertEqual(sum(not os.path.isdir(x['path']) for x in result['included']), 9)

    def test_omit_only_known_ephemeral_probe_subdirectories(self):
        for label in ('.isolated-Ab1234','.execution-Qw321z'):
            self.put(self.inspect / 'measurement' / label / 'codex-home/state_5.sqlite')
        self.put(self.inspect / 'measurement/unknown/identity.json')
        self.put(self.root / 'measurement/.isolated-Ab1234/business')
        result = m.plan([self.root]); self.assertEqual(len(result['excluded']), 2)
        self.assertTrue(any(x['path'].endswith('/unknown/identity.json') for x in result['included']))

    def test_symlinks_not_followed_and_diagnostic_symlink_not_omitted(self):
        db = self.log(self.base / 'logs_2.sqlite')
        (self.home / 'logs_2.sqlite').symlink_to(db)
        (self.root / 'outside').symlink_to(self.base)
        result = m.plan([self.root]); self.assertFalse(result['excluded'])
        self.assertEqual(len([x for x in result['included'] if os.path.islink(x['path'])]), 2)

    def cache(self, path=None):
        path = path or self.home / '.tmp/plugins'
        path.mkdir(parents=True)
        def git(*args):
            return subprocess.check_output(['git', '-C', str(path)] + list(args), stderr=subprocess.DEVNULL)
        git('init'); git('config', 'user.name', 'fixture'); git('config', 'user.email', 'fixture@example.invalid')
        self.put(path / 'plugins/example/data', 'public-package')
        self.put(path / '.gitignore', '*.ignored\n')
        git('add', '.'); git('commit', '-m', 'fixture')
        return path, git

    def test_clean_cache_omits_worktree_but_retains_all_git(self):
        path, git = self.cache()
        result = m.plan([self.root])
        omitted = [r for r in result['excluded'] if r['reason'] == 'rebuildable-plugin-cache-worktree']
        self.assertEqual(len(omitted), 2)
        self.assertTrue(all(r['commit'] == git('rev-parse', 'HEAD').decode().strip() for r in omitted))
        self.assertTrue(any(r['path'] == str(path / '.git/HEAD') for r in result['included']))
        self.assertTrue((path / 'plugins/example/data').exists())

    def test_dirty_untracked_ignored_or_hidden_changes_keep_entire_cache(self):
        path, git = self.cache()
        for name in ('plugins/example/data', 'private', 'private.ignored'):
            f = self.put(path / name, 'local-data')
            self.assertFalse(m.plan([self.root])['excluded'])
            if name == 'plugins/example/data': git('checkout', '--', name)
            else: f.unlink()
        git('update-index', '--assume-unchanged', 'plugins/example/data')
        self.put(path / 'plugins/example/data', 'hidden-local-data')
        self.assertFalse(m.plan([self.root])['excluded'])

    def test_same_name_public_repository_outside_cache_is_kept(self):
        self.cache(self.root / 'workspace/.tmp/plugins')
        self.assertFalse(m.plan([self.root])['excluded'])

    def test_managed_home_cache_and_unknown_tmp(self):
        self.cache(self.root / ('unified/' + 'a' * 64 + '/home/.tmp/plugins'))
        self.put(self.home / '.tmp/private.data')
        result = m.plan([self.root])
        self.assertEqual(len(result['excluded']), 2)
        self.assertTrue(any(r['path'].endswith('/.tmp/private.data') for r in result['included']))

    def test_cache_symlink_kept_not_followed(self):
        path, git = self.cache(self.base / 'external')
        (self.home / '.tmp').mkdir()
        (self.home / '.tmp/plugins').symlink_to(path)
        self.assertFalse(m.plan([self.root])['excluded'])

    def test_archive_restores_cache_offline_from_preserved_git_and_keeps_business_state(self):
        path, git = self.cache()
        self.put(self.home / 'sessions/private.jsonl', 'session-fixture')
        self.put(self.home / '.cyf-skill-view-staging/cmd/data', 'recovery-fixture')
        self.put(self.root / 'private-runs/output', 'user-output')
        archive = self.base / 'state.tar.gz'
        with (self.base / 'log').open('wb') as log: result = m.write_state_archive(archive, [self.root], log)
        dest = self.base / 'restore'; dest.mkdir()
        subprocess.check_call(['tar', '-xzf', str(archive), '-C', str(dest)])
        restored = dest / str(path).lstrip('/')
        self.assertFalse((restored / 'plugins').exists())
        subprocess.check_call(['git', '-C', str(restored), 'restore', '--source=HEAD', '--worktree', '--', '.'])
        self.assertEqual((restored / 'plugins/example/data').read_text(), 'public-package')
        restored_home = dest / str(self.home).lstrip('/')
        self.assertEqual((restored_home / 'sessions/private.jsonl').read_text(), 'session-fixture')
        self.assertEqual((restored_home / '.cyf-skill-view-staging/cmd/data').read_text(), 'recovery-fixture')
        self.assertEqual((dest / str(self.root).lstrip('/') / 'private-runs/output').read_text(), 'user-output')
        self.assertEqual(result['policy'], 'runtime-essential-state-v2')


    def test_roots_must_not_overlap_or_alias(self):
        for roots in ([self.root,self.home],[self.root,self.root]):
            with self.assertRaises(ValueError): m.plan(roots)
        alias = self.base / 'alias'; alias.symlink_to(self.root)
        with self.assertRaises(ValueError): m.plan([alias])

    def test_socket_fails_closed(self):
        import socket
        s = socket.socket(socket.AF_UNIX); self.addCleanup(s.close)
        cwd = os.getcwd()
        try:
            os.chdir(str(self.root)); s.bind('writer.sock')
        finally: os.chdir(cwd)
        with self.assertRaisesRegex(ValueError,'SOCKET'): m.plan([self.root])

    def test_real_uncompressed_archive_roundtrip_excludes_only_diagnostics(self):
        self.log(); self.put(self.home / 'auth.json','secret-fixture')
        self.put(self.inspect / 'requests/aa/binding.json')
        source = self.put(self.home / 'state_5.sqlite','state-fixture'); source.chmod(0o600)
        os.link(str(source), str(self.home / 'state-alias'))
        (self.home / 'state-link').symlink_to('state_5.sqlite')
        archive = self.base / 'state.tar'
        with (self.base / 'log').open('wb') as log: result = m.write_state_archive(archive,[self.root],log)
        self.assertTrue(result['archiveSha256']); self.assertEqual(archive.stat().st_mode & 0o777,0o600)
        with tarfile.open(str(archive),'r:') as tar:
            names = tar.getnames()
            self.assertFalse(any(x.endswith('logs_2.sqlite') for x in names))
        dest = self.base / 'restore'; dest.mkdir()
        subprocess.check_call(['tar','--acls','--xattrs','-xf',str(archive),'-C',str(dest)])
        restored = dest / str(self.home).lstrip('/')
        self.assertEqual((restored/'auth.json').read_text(),'secret-fixture')
        self.assertEqual((restored/'state_5.sqlite').stat().st_mode & 0o777,0o600)
        self.assertEqual((restored/'state_5.sqlite').stat().st_ino,(restored/'state-alias').stat().st_ino)
        self.assertEqual(os.readlink(str(restored/'state-link')),'state_5.sqlite')
        self.assertTrue((self.home/'logs_2.sqlite').exists())  # no source deletion
        with self.assertRaises(ValueError): m.write_state_archive(archive,[self.root],io.BytesIO())

    def test_changed_source_preserves_original_and_stops(self):
        self.put(self.home / 'auth.json')
        old = m.plan; calls = [0]
        def changed(roots):
            calls[0] += 1
            result = old(roots)
            if calls[0] > 1: result['policy'] = 'changed'
            return result
        with patch.object(m,'plan',side_effect=changed):
            with (self.base/'log').open('wb') as log:
                with self.assertRaisesRegex(ValueError,'CHANGED'): m.write_state_archive(self.base/'state.tar',[self.root],log)
        self.assertFalse((self.base/'state-scope.json').exists())
        self.assertTrue((self.home/'auth.json').exists())

    def test_backup_cannot_live_inside_source(self):
        with self.assertRaisesRegex(ValueError,'INSIDE_SOURCE'):
            m.write_state_archive(self.root/'state.tar',[self.root],io.BytesIO())





class StateEntryTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('scope_entry', str(SCRIPT.with_name('runtime_backup_cleanup.py')))
        self.entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.entry)
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-state-entry-'); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.paths = SimpleNamespace(base=self.base/'baks', lock=self.base/'host.lock', release_lock=self.base/'release.lock', current=self.base/'current.json', proc=Path('/proc'))
        self.paths.root_device=self.base.stat().st_dev
        self.paths.mountinfo=Path('/proc/self/mountinfo'); self.paths._mount_text=None; self.paths._mounts=[]
        self.paths.base.mkdir()
        self.batch = self.paths.base/'20261109-new'; self.batch.mkdir()
        for path in (self.paths.lock,self.paths.release_lock,self.paths.current): path.write_text('{}'); path.chmod(0o600)
        self.root = self.base/'state'; self.root.mkdir(); (self.root/'auth.json').write_text('fixture')
        self.signature = self.entry.safe.signature(self.paths.current.lstat())
        self.states = {'ActiveState':b'inactive','MainPID':b'0','LoadState':b'loaded','ControlGroup':b''}
        self.used = False
        self.patchers = [patch.object(self.entry,'read_current',return_value=(self.paths.base/'20261108-pin',self.signature)),
                         patch.object(self.entry,'state_roots',return_value=[self.root]),
                         patch.object(self.entry.subprocess,'check_output',side_effect=self.command),
                         patch.object(self.entry.safe.proc,'snapshot',side_effect=self.usage)]
        for p in self.patchers:p.start(); self.addCleanup(p.stop)

    def command(self,cmd,**kw):
        if cmd[0]=='systemctl':return self.states[cmd[-2]]
        # The scope module shares subprocess; permit its read-only disk checks.
        if cmd[0]=='stat':return b'ext2/ext3\n'
        raise AssertionError(cmd)

    def usage(self,*args):
        from types import SimpleNamespace
        return SimpleNamespace(used=lambda path:self.used)

    def test_active_service_refused_without_backup(self):
        self.states['ActiveState']=b'active'; self.states['MainPID']=b'123'
        with self.assertRaisesRegex(self.entry.Unsafe,'already be stopped'):
            self.entry.run_state(self.paths,'backup-state',self.batch)
        self.assertFalse(list(self.batch.iterdir()))

    def test_state_open_by_any_process_refused(self):
        self.used=True
        with self.assertRaisesRegex(self.entry.Unsafe,'still in use'):
            self.entry.run_state(self.paths,'backup-state',self.batch)
        self.assertFalse(list(self.batch.iterdir()))

    def test_existing_backup_never_overwritten(self):
        (self.batch/'state.tar.gz').write_bytes(b'original')
        with self.assertRaisesRegex(self.entry.Unsafe,'immutable'):
            self.entry.run_state(self.paths,'backup-state',self.batch)
        self.assertEqual((self.batch/'state.tar.gz').read_bytes(),b'original')

    def test_busy_lock_not_bypassed(self):
        import fcntl
        with self.paths.lock.open('r+') as f:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(OSError):self.entry.run_state(self.paths,'backup-state',self.batch)
        self.assertFalse(list(self.batch.iterdir()))

    def test_new_selected_backup_when_stopped_and_unused(self):
        result=self.entry.run_state(self.paths,'backup-state',self.batch)
        self.assertEqual(result['status'],'essential-state-backed-up-not-restored')
        self.assertTrue((self.batch/'state.tar.gz').exists())
        receipt=json.loads((self.batch/'state-scope.json').read_text())
        self.assertIn('currentRecordSha256',receipt['releaseBinding'])
        with tarfile.open(str(self.batch/'state.tar.gz'),'r:gz') as archive:
            self.assertTrue(any(x.name.endswith('/auth.json') for x in archive))


if __name__ == '__main__': unittest.main()
