#!/usr/bin/python3
"""Retire only historical Runtime recovery payloads; never live state/programs.
Keep newest two payload-bearing batches AND current release's pinned backup.
Run on every host cleanup, independent of disk pressure. No tree retirement.
"""
import argparse
import fcntl
import json
import os
import pwd
from pathlib import Path
import re
import stat
import sys
import time
import importlib.util
import subprocess
import tarfile


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


safe = module('runtime_cache_safety', '/usr/local/libexec/cyf/rebuildable_cache_cleanup.py')
Unsafe = safe.Unsafe
PAYLOADS = ('state.tar', 'state.tar.gz', 'old-program.tar.gz')
MAX_FILES = 100000


class Paths(safe.Paths):
    def __init__(self):
        super().__init__()
        self.base = Path('/home/isp/baks/cyf-agent-runtime-v1')
        self.current = Path('/home/isp/apps/cyf-agent-runtime-v1/release-records/current.json')
        self.release_lock = Path('/run/lock/cyf-wuyong-versioned-release.lock')
        self.audit = Path('/home/isp/baks/host-cleanup/runtime-backups/audit.jsonl')


def directory(paths, p, runtime_record=False):
    # Check every physical ancestor, not just the final component.
    for d in reversed((p,) + tuple(p.parents)):
        st = d.lstat()
        legacy_apps = runtime_record and str(d) == '/home/isp/apps' and st.st_uid == pwd.getpwnam('isp').pw_uid
        if not stat.S_ISDIR(st.st_mode) or (st.st_uid != 0 and not legacy_apps) or st.st_mode & 0o022:
            raise Unsafe('unsafe directory: ' + str(d))
        if os.path.lexists(d / '.keep'):
            raise Unsafe('keep marker: ' + str(d))
    if p.stat().st_dev != paths.root_device or safe.mounted(paths, p):
        raise Unsafe('mounted/wrong device: ' + str(p))
    return p.stat()


def read_current(paths):
    directory(paths, paths.current.parent, runtime_record=True)
    ancestors = [(d, d.lstat().st_dev, d.lstat().st_ino) for d in paths.current.parents]
    st = safe.regular(paths.current)
    if st.st_size > 1024 * 1024:
        raise Unsafe('oversized release record')
    fd = os.open(paths.current, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as f:
        if safe.signature(os.fstat(f.fileno())) != safe.signature(st):
            raise Unsafe('release record replaced')
        data = json.load(f)
        if safe.signature(os.fstat(f.fileno())) != safe.signature(st):
            raise Unsafe('release record changed')
    if safe.signature(paths.current.lstat()) != safe.signature(st):
        raise Unsafe('release record replaced')
    for d, dev, ino in ancestors:
        current = d.lstat()
        if not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != (dev, ino):
            raise Unsafe('release record ancestor replaced')
    # Unknown/unverified activation fails closed. No inferred success from idle.
    if data.get('status') != 'verified-active':
        raise Unsafe('current Runtime release is not verified-active')
    pin = Path(data.get('backup', ''))
    if pin.parent != paths.base or not re.fullmatch(r'20\d{6}-[A-Za-z0-9_.-]+', pin.name):
        raise Unsafe('missing/invalid pinned Runtime recovery batch')
    directory(paths, pin)
    return pin, safe.signature(st)


def leaf(paths, p, shared=False):
    directory(paths, p.parent)
    st = p.lstat()
    if not (stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode)):
        raise Unsafe('non-payload file type')
    if st.st_uid != 0 or (st.st_nlink != 1 and not (shared and stat.S_ISREG(st.st_mode))) or (not stat.S_ISLNK(st.st_mode) and st.st_mode & 0o022):
        raise Unsafe('unsafe payload ownership/links/mode')
    if st.st_dev != paths.root_device or safe.mounted(paths, p):
        raise Unsafe('mounted payload')
    return st


def collect_batch(paths, batch):
    directory(paths, batch)
    # Known recovery layout only. Preserve RECOVERY, manifests, records, evidence.
    for n in ('RECOVERY.md', 'current.json'):
        safe.regular(batch / n)
    selected = [batch / n for n in PAYLOADS if os.path.lexists(batch / n)]
    old = batch / 'old-program'
    if os.path.lexists(old):
        directory(paths, old)
        def fail(error):
            raise error
        for d, dirs, files in os.walk(old, followlinks=False, onerror=fail):
            d = Path(d)
            directory(paths, d)
            if len(d.relative_to(old).parts) > 20:
                raise Unsafe('payload depth limit')
            links = [n for n in dirs if (d / n).is_symlink()]
            dirs[:] = [n for n in dirs if n not in links]
            selected.extend(d / n for n in files + links)
            if len(selected) > MAX_FILES:
                raise Unsafe('payload entry limit; no partial batch')
    rows, groups = [], {}
    for p in selected:
        # Sharing is only supported inside one retired installation, never for
        # state archives or aliases into another release/live program.
        st = leaf(paths, p, old in p.parents)
        row = {'path': str(p), 'signature': safe.signature(st), 'allocated': st.st_blocks * 512}
        rows.append(row)
        if stat.S_ISREG(st.st_mode):
            groups.setdefault((st.st_dev, st.st_ino), []).append(row)
    for aliases in groups.values():
        if len(aliases) != aliases[0]['signature'][5]:
            raise Unsafe('payload hardlink escapes old-program')
        if len(aliases) > 1:
            for row in aliases:
                if old not in Path(row['path']).parents or row['signature'] != aliases[0]['signature']:
                    raise Unsafe('payload hardlink changed/outside old-program')
                row['shared'] = True
                row['allocated'] = 0
            # Space is reclaimed only when the last directory entry is removed.
            aliases[-1]['allocated'] = Path(aliases[-1]['path']).lstat().st_blocks * 512
    return rows


def retirement_record(batch):
    """Completed retirement records are immutable tombstones, never reused roots.
    Ignore any later additions to such roots (preserve, do not auto-delete them).
    """
    marker = batch / 'PAYLOAD_RETIRED.json'
    if not os.path.lexists(marker):
        return {}
    st = safe.regular(marker)
    if st.st_size > 4096:
        raise Unsafe('oversized retirement marker')
    fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as f:
        if safe.signature(os.fstat(f.fileno())) != safe.signature(st):
            raise Unsafe('retirement marker replaced')
        value = json.load(f)
        if safe.signature(os.fstat(f.fileno())) != safe.signature(st):
            raise Unsafe('retirement marker changed')
    if safe.signature(marker.lstat()) != safe.signature(st):
        raise Unsafe('retirement marker replaced')
    return value


def retired_batch(batch):
    value = retirement_record(batch)
    return (value.get('status') == 'retired-not-a-complete-recovery'
            and value.get('policy') == 'newest-two-plus-current-pin')


def collect(paths, usage, now=None):
    now = time.time() if now is None else now
    directory(paths, paths.base)
    pin, current_sig = read_current(paths)
    batches = []
    skips = []
    entries = list(paths.base.iterdir())
    if len(entries) > 10000:
        raise Unsafe('metadata entry limit exceeded')
    unretired = 0
    for batch in entries:
        if not re.fullmatch(r'20\d{6}-[A-Za-z0-9_.-]+', batch.name):
            continue
        try:
            directory(paths, batch)
            retirement = retirement_record(batch)
            if (retirement.get('status') == 'retired-not-a-complete-recovery'
                    and retirement.get('policy') == 'newest-two-plus-current-pin'):
                continue
            unretired += 1
            if unretired > 512:
                raise Unsafe('unretired batch limit exceeded')
            rows = collect_batch(paths, batch)
            if rows:
                # File times, never directory mtime (deletion changes directory mtime).
                stamp = max(r['signature'][8] / 1e9 for r in rows)
                # Our own hardlink unlinks change survivor ctime. An interrupted
                # retirement must not become a newer-than-pin recovery forever.
                # Reuse only this directory's original, protected intent stamp.
                if (retirement.get('status') == 'retiring-not-a-complete-recovery'
                        and retirement.get('policy') == 'newest-two-plus-current-pin'
                        and retirement.get('batchIdentity') == list(safe.signature(batch.lstat())[:2])
                        and isinstance(retirement.get('payloadStamp'), (int, float))
                        and 0 < retirement['payloadStamp'] <= stamp
                        and all(r['signature'][7] / 1e9 <= retirement['payloadStamp'] for r in rows)):
                    stamp = retirement['payloadStamp']
                batches.append({'batch': str(batch), 'stamp': stamp, 'rows': rows,
                                'identity': safe.signature(batch.lstat())[:2]})
        except (OSError, Unsafe) as e:
            if unretired > 512:
                raise Unsafe('unretired batch limit exceeded')
            # Unsafe batches still reserve a newest slot, so failures cannot evict
            # the real newest recoveries. Use top-level metadata conservatively.
            skips.append({'batch': str(batch), 'reason': str(e)})
            stamp = max(batch.lstat().st_ctime, batch.lstat().st_mtime)
            batches.append({'batch': str(batch), 'stamp': stamp, 'rows': [], 'unsafe': True})
    batches.sort(key=lambda x: (x['stamp'], x['batch']), reverse=True)
    protected = {b['batch'] for b in batches[:2]} | {str(pin)}
    # Never prune newer-than-current backup attempts, even beyond newest two.
    pin_stamp = next((b['stamp'] for b in batches if b['batch'] == str(pin)), None)
    if pin_stamp is None:
        raise Unsafe('pinned recovery payload is missing')
    eligible = []
    for b in batches:
        if b.get('unsafe') or b['batch'] in protected:
            continue
        if b['stamp'] > pin_stamp or now - b['stamp'] < 3600:
            skips.append({'batch': b['batch'], 'reason': 'recent/newer-than-current recovery'})
            continue
        if usage.used(Path(b['batch'])) or any(tuple(r['signature'][:2]) in usage.inodes for r in b['rows']):
            skips.append({'batch': b['batch'], 'reason': 'active recovery'})
            continue
        eligible.append(b)
    return eligible, sorted(protected), skips, current_sig


def unlink(paths, row, remaining=None):
    p = Path(row['path'])
    shared = row.get('shared', False)
    aliases = (remaining or {}).get(tuple(row['signature'][:2]), []) if shared else []
    if shared and (len(aliases) != row['signature'][5] or row not in aliases):
        raise Unsafe('missing payload hardlink closure')
    if safe.signature(leaf(paths, p, shared)) != tuple(row['signature']):
        raise Unsafe('payload changed before unlink')
    # Anchor every parent with O_NOFOLLOW. Never follow archived symlinks.
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    chain = []
    try:
        parent = Path('/')
        for name in p.parent.parts[1:]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            parent /= name
            st = os.fstat(fd)
            chain.append((parent, st.st_dev, st.st_ino))
        for parent, dev, ino in chain:
            st = parent.lstat()
            if not stat.S_ISDIR(st.st_mode) or (st.st_dev, st.st_ino) != (dev, ino):
                raise Unsafe('parent replaced')
        if safe.signature(os.stat(p.name, dir_fd=fd, follow_symlinks=False)) != tuple(row['signature']):
            raise Unsafe('anchored payload changed')
        if shared:
            # Hold the inode while unlink changes nlink/ctime. Advance only
            # those expected fields on our remaining aliases, not arbitrary
            # replacement metadata. External links/writes still fail closed.
            held = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                before = tuple(row['signature'])
                if safe.signature(os.fstat(held)) != before:
                    raise Unsafe('shared payload changed')
                os.unlink(p.name, dir_fd=fd)
                after = safe.signature(os.fstat(held))
                if after[5] != before[5] - 1 or after[:5] != before[:5] or after[6:8] != before[6:8]:
                    raise Unsafe('shared payload changed while unlinking')
                aliases.remove(row)
                for alias in aliases:
                    alias['signature'] = after
            finally:
                os.close(held)
        else:
            os.unlink(p.name, dir_fd=fd)
    finally:
        os.close(fd)


def run(paths, mode, inherited=None):
    fds = []
    auditfd = None
    result = {'stage': 'runtime_backups', 'mode': mode, 'removed_files': 0,
              'reclaimed_allocated_bytes': 0, 'retired_batches': []}
    try:
        for lock, inherit in ((paths.lock, inherited), (paths.release_lock, None)):
            before = safe.regular(lock)
            fd = os.dup(inherit) if inherit is not None else os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
            fds.append(fd)
            if safe.signature(os.fstat(fd)) != safe.signature(before):
                raise Unsafe('lock identity changed')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return dict(result, skipped='cleanup/release in progress')
            if safe.signature(lock.lstat()) != safe.signature(before):
                raise Unsafe('lock replaced')
        batches, protected, skips, current_sig = collect(paths, safe.proc.snapshot(paths.proc))
        result.update(protected=protected, skipped=skips, eligible_batches=[b['batch'] for b in batches],
                      estimated_reclaim_bytes=sum(r['allocated'] for b in batches for r in b['rows']))
        if mode == 'plan' or not batches:
            return result
        if not paths.audit.parent.exists():
            paths.audit.parent.mkdir(mode=0o700)
        directory(paths, paths.audit.parent)
        safe.logger.LOG = paths.audit
        auditfd = safe.logger.rotate_log(safe.logger.open_log(paths.audit))
        def audit(value):
            nonlocal auditfd
            auditfd = safe.logger.rotate_log(auditfd)
            safe.logger.validate_log(auditfd)
            data = memoryview((json.dumps(value) + '\n').encode())
            while data:
                n = os.write(auditfd, data)
                if n <= 0:
                    raise OSError('audit write failed')
                data = data[n:]
            os.fsync(auditfd)
        for b in batches:
            batch = Path(b['batch'])
            directory(paths, batch)
            if safe.signature(batch.lstat())[:2] != tuple(b['identity']):
                raise Unsafe('backup batch replaced')
            # Durable marker BEFORE first deletion: interrupted runs must not
            # advertise a partially retired archive as a usable recovery point.
            audit({'retirement_intent': str(batch), 'time': time.time()})
            safe.atomic_json(batch / 'PAYLOAD_RETIRED.json', {
                'status': 'retiring-not-a-complete-recovery', 'time': time.time(),
                'payloadStamp': b['stamp'], 'batchIdentity': list(b['identity']),
                'policy': 'newest-two-plus-current-pin', 'audit': str(paths.audit)})
            remaining = {}
            for row in b['rows']:
                if row.get('shared'):
                    remaining.setdefault(tuple(row['signature'][:2]), []).append(row)
            for i in range(0, len(b['rows']), 100):
                fresh = safe.proc.snapshot(paths.proc)
                if fresh.used(batch):
                    raise Unsafe('backup became active')
                if read_current(paths)[1] != current_sig:
                    raise Unsafe('current release changed')
                chunk = b['rows'][i:i + 100]
                if any(tuple(r['signature'][:2]) in fresh.inodes for r in chunk):
                    raise Unsafe('payload inode became active')
                audit({'intent': chunk})
                done = []
                try:
                    for row in chunk:
                        unlink(paths, row, remaining)
                        result['removed_files'] += 1
                        result['reclaimed_allocated_bytes'] += row['allocated']
                        done.append(row['path'])
                finally:
                    audit({'removed': done})
            safe.atomic_json(batch / 'PAYLOAD_RETIRED.json', {
                'status': 'retired-not-a-complete-recovery', 'time': time.time(),
                'policy': 'newest-two-plus-current-pin', 'audit': str(paths.audit)})
            result['retired_batches'].append(str(batch))
            audit({'batch_complete': str(batch)})
        return result
    finally:
        if auditfd is not None:
            os.close(auditfd)
        for fd in reversed(fds):
            os.close(fd)


# Program compaction is explicit, never part of automatic retention. The archive
# remains a complete recovery payload; identity/state and service control stay
# with the original installer/Owner.
def program_digest(path):
    import hashlib
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def program_tree(root):
    """Portable recovery facts plus internal hardlink closure, not live inode IDs."""
    def entry(p):
        s = p.lstat()
        e = dict(mode=oct(stat.S_IMODE(s.st_mode)), uid=s.st_uid, gid=s.st_gid,
                 mtime_ns=s.st_mtime_ns)
        if stat.S_ISLNK(s.st_mode):
            e.update(type='symlink', target=os.readlink(p))
        elif stat.S_ISDIR(s.st_mode):
            e['type'] = 'directory'
        elif stat.S_ISREG(s.st_mode):
            e.update(type='file', sha256=program_digest(p))
        else:
            raise Unsafe('special program entry: ' + str(p))
        e['xattrs'] = {name: os.getxattr(str(p), name, follow_symlinks=False).hex()
                      for name in os.listxattr(str(p), follow_symlinks=False)}
        if safe.signature(p.lstat()) != safe.signature(s):
            raise Unsafe('program changed during measurement')
        return e, s
    facts, groups = {}, {}
    root_fact, _ = entry(root)
    if root_fact['type'] != 'directory':
        raise Unsafe('program root is not a physical directory')
    def failed(e):
        raise e
    for d, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        d = Path(d)
        for name in sorted(dirs + files):
            p = d / name
            if name == '.keep' or (p.is_dir() and not p.is_symlink() and os.path.lexists(p / '.keep')):
                raise Unsafe('keep marker in program')
            e, s = entry(p)
            rel = str(p.relative_to(root))
            facts[rel] = e
            if e['type'] == 'file':
                groups.setdefault((s.st_dev, s.st_ino), []).append((rel, s.st_nlink))
    links = []
    for group in groups.values():
        if any(n != len(group) for _, n in group):
            raise Unsafe('program hardlink escapes recovery root')
        if len(group) > 1:
            links.append(sorted(n for n, _ in group))
    return dict(root=root_fact, entries=facts, hardlinks=sorted(links))


def program_manifest_matches(tree, manifest):
    # The existing installed manifest remains authoritative; no new schema for it.
    actual = []
    for name, e in tree['entries'].items():
        v = dict(path=name, **{k: e[k] for k in ('mode', 'uid', 'gid', 'type')})
        for key in ('sha256', 'target'):
            if key in e:
                v[key] = e[key]
        actual.append(v)
    if sorted(actual, key=lambda v: v['path']) != sorted(manifest, key=lambda v: v['path']):
        raise Unsafe('old program does not match pinned installed manifest')


def program_tar_members(archive):
    import tarfile
    import posixpath
    members = {}
    with tarfile.open(str(archive), 'r:gz') as t:
        for m in t:
            name = posixpath.normpath(m.name)
            if (m.name.startswith('/') or '..' in m.name.split('/') or
                    name in members or name == '..' or name.startswith('../') or
                    not (m.isfile() or m.isdir() or m.issym() or m.islnk())):
                raise Unsafe('unsafe/duplicate program archive member')
            if name == '.' and not m.isdir():
                raise Unsafe('archive root is not a directory')
            members[name] = m
    if '.' not in members:
        raise Unsafe('missing archive root metadata')
    for name, m in members.items():
        parent = posixpath.dirname(name)
        while parent:
            if parent not in members or not members[parent].isdir():
                raise Unsafe('archive member beneath a link/non-directory')
            parent = posixpath.dirname(parent)
        if m.islnk():
            target = posixpath.normpath(m.linkname)
            if (m.linkname.startswith('/') or '..' in m.linkname.split('/') or
                    target not in members or not members[target].isfile()):
                raise Unsafe('unsafe archive hardlink')
    return members


def extract_program(archive, destination):
    import subprocess
    program_tar_members(archive)
    # Absolute symlinks can be required by the final-path venv. They are retained
    # as leaves, never followed; tar hardlinks and all written paths stay inside.
    subprocess.run(['tar', '--extract', '--gzip', '--acls', '--xattrs',
                    '--xattrs-include=*', '--numeric-owner', '--same-owner', '--same-permissions',
                    '--delay-directory-restore',
                    '-f', str(archive), '-C', str(destination)], check=True)


def program_subset(actual, expected):
    """Allow only our already-retired names on resume, never adopt new contents."""
    for name, fact in dict(actual['entries'], **{'.': actual['root']}).items():
        wanted = expected['root'] if name == '.' else expected['entries'].get(name)
        a, b = dict(fact), dict(wanted or {})
        if a.get('type') == 'directory':
            a.pop('mtime_ns', None); b.pop('mtime_ns', None)
        if a != b:
            raise Unsafe('remaining old program changed: ' + name)
    names = set(actual['entries'])
    groups = sorted(sorted(set(g) & names) for g in expected['hardlinks'] if len(set(g) & names) > 1)
    if actual['hardlinks'] != groups:
        raise Unsafe('remaining program hardlink topology changed')


def run_program(paths, mode, batch, manifest_sha256, destination=None):
    """Explicit storage-only operation under the existing host→release locks."""
    import shutil
    import subprocess
    import tempfile
    import uuid
    fds = []
    auditfd = None
    temporary = None
    try:
        for lock in (paths.lock, paths.release_lock):
            before = safe.regular(lock)
            fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW); fds.append(fd)
            if safe.signature(os.fstat(fd)) != safe.signature(before):
                raise Unsafe('program archive lock changed')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if safe.signature(lock.lstat()) != safe.signature(before):
                raise Unsafe('program archive lock replaced')
        if batch.parent != paths.base or not re.fullmatch(r'20\d{6}-[A-Za-z0-9_.-]+', batch.name):
            raise Unsafe('outside explicit Runtime backup batch')
        directory(paths, batch)
        pin, current_sig = read_current(paths)
        if retired_batch(batch) or retirement_record(batch):
            raise Unsafe('retired/incomplete recovery point')
        manifest = batch / 'current.manifest.json'
        safe.regular(manifest); safe.regular(batch / 'current.json'); safe.regular(batch / 'RECOVERY.md')
        if program_digest(manifest) != manifest_sha256:
            raise Unsafe('pinned program manifest digest mismatch')
        baseline_manifest = json.loads(manifest.read_text())
        source = batch / 'old-program'
        archive = batch / 'old-program.tar.gz'
        receipt = batch / 'program-archive.json'
        if safe.proc.snapshot(paths.proc).used(batch):
            raise Unsafe('recovery batch in use')
        audit_path = paths.audit.with_name('program-archive-audit.jsonl')
        if not audit_path.parent.exists():
            audit_path.parent.mkdir(mode=0o700)
        directory(paths, audit_path.parent)
        safe.logger.LOG = audit_path
        auditfd = safe.logger.rotate_log(safe.logger.open_log(audit_path))
        def audit(value):
            safe.logger.validate_log(auditfd)
            data = (json.dumps(value) + '\n').encode()
            view = memoryview(data)
            while view:
                written = os.write(auditfd, view)
                if written <= 0:
                    raise OSError('program archive audit write failed')
                view = view[written:]
            os.fsync(auditfd)
        archive_signature = None
        def stable():
            if archive_signature is not None and safe.signature(safe.regular(archive)) != archive_signature:
                raise Unsafe('verified program archive changed')
            if (read_current(paths)[1] != current_sig or
                    program_digest(manifest) != manifest_sha256):
                raise Unsafe('release or pinned program manifest changed')
            if safe.proc.snapshot(paths.proc).used(batch):
                raise Unsafe('recovery batch became active')
        newly_verified = False
        if os.path.lexists(receipt):
            safe.regular(receipt); record = json.loads(receipt.read_text())
            if (record.get('schemaVersion') != 1 or
                    record.get('manifestSha256') != manifest_sha256 or
                    record.get('status') not in ('archive-verified-directory-retirement-pending', 'compacted')):
                raise Unsafe('unknown program archive receipt')
            safe.regular(archive)
            if program_digest(archive) != record['archiveSha256']:
                raise Unsafe('program archive digest mismatch')
        else:
            if mode != 'compact-program' or os.path.lexists(archive):
                raise Unsafe('missing archive receipt or unknown preexisting archive')
            directory(paths, source)
            # Existing batch scanner validates mounts/permissions/internal links.
            collect_batch(paths, batch)
            tree = program_tree(source); program_manifest_matches(tree, baseline_manifest)
            temporary = batch / ('.program-archive-' + uuid.uuid4().hex + '.tmp')
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            audit(dict(event='archive-start', batch=str(batch), manifestSha256=manifest_sha256))
            subprocess.run(['tar', '--create', '--format=pax', '--acls', '--xattrs',
                            '--xattrs-include=*', '--numeric-owner', '--sparse', '-I', 'gzip -1',
                            '-f', str(temporary), '-C', str(source), '.'], check=True)
            with temporary.open('rb') as f:
                os.fsync(f.fileno())
            # GNU tar compare plus independent restored-tree verification.
            subprocess.run(['tar', '--compare', '--gzip', '--acls', '--xattrs', '--xattrs-include=*',
                            '-f', str(temporary), '-C', str(source)], check=True)
            with tempfile.TemporaryDirectory(prefix='.program-verify-', dir=str(batch)) as td:
                extract_program(temporary, Path(td))
                if program_tree(Path(td)) != tree:
                    raise Unsafe('independent program restore verification failed')
            if program_tree(source) != tree:
                raise Unsafe('source changed while archiving')
            stable()
            record = dict(schemaVersion=1, status='archive-verified-directory-retirement-pending',
                          archiveSha256=program_digest(temporary), manifestSha256=manifest_sha256,
                          tree=tree, originalBatch=str(batch))
            # No pre-existing output is overwritten, even by a replacement file.
            os.link(str(temporary), str(archive)); temporary.unlink(); temporary = None
            safe.atomic_json(receipt, record)
            newly_verified = True
            audit(dict(event='archive-verified', batch=str(batch), archiveSha256=record['archiveSha256']))
        archive_signature = safe.signature(safe.regular(archive))
        program_manifest_matches(record['tree'], baseline_manifest)
        # Also verify receipt/manifest against actual archive on resume and restore.
        if not newly_verified:
            with tempfile.TemporaryDirectory(prefix='.program-verify-', dir=str(batch)) as td:
                extract_program(archive, Path(td))
                if program_tree(Path(td)) != record['tree']:
                    raise Unsafe('archive tree does not match verified recovery facts')
        stable()
        if mode == 'restore-program':
            bases = getattr(paths, 'restore_bases', [Path('/var/tmp'), Path('/home/isp/state/cyf-local-build/tasks')])
            if (destination is None or destination.parent not in bases or
                    not destination.name.startswith('cyf-runtime-restore-')):
                raise Unsafe('restore requires a new explicit disk staging directory')
            directory(paths, destination.parent)
            destination.mkdir(mode=0o700)  # fail on ANY existing path; never overwrite app/state
            try:
                extract_program(archive, destination)
                if program_tree(destination) != record['tree']:
                    raise Unsafe('staging restore verification failed')
                stable()
            except BaseException:
                # Own exclusively-created staging tree only; no backup/state deletion.
                shutil.rmtree(str(destination))
                raise
            audit(dict(event='restored-to-staging', batch=str(batch), destination=str(destination)))
            return dict(status='restored-to-staging-not-activated', destination=str(destination))
        if mode != 'compact-program':
            raise Unsafe('unknown explicit program archive operation')
        if not os.path.lexists(source):
            if record['status'] != 'compacted':
                stable()
                record['status'] = 'compacted'; safe.atomic_json(receipt, record)
            return dict(status='compacted', alreadyComplete=True, archive=str(archive))
        directory(paths, source)
        program_subset(program_tree(source), record['tree'])
        rows = [r for r in collect_batch(paths, batch) if source in Path(r['path']).parents]
        # Record only directory identities; our child removals change their times.
        dirs = []
        for d, children, _ in os.walk(source, followlinks=False):
            for p in [Path(d)]:
                s = p.lstat(); dirs.append((p, s.st_dev, s.st_ino))
        remaining = {}
        for row in rows:
            if row.get('shared'):
                remaining.setdefault(tuple(row['signature'][:2]), []).append(row)
        audit(dict(event='directory-retirement-intent', batch=str(batch), archiveSha256=record['archiveSha256']))
        for i in range(0, len(rows), 100):
            stable()
            chunk = rows[i:i + 100]
            fresh = safe.proc.snapshot(paths.proc)
            if any(tuple(r['signature'][:2]) in fresh.inodes for r in chunk):
                raise Unsafe('old program inode became active')
            for row in chunk:
                unlink(paths, row, remaining)
            audit(dict(event='directory-files-removed', paths=[r['path'] for r in chunk]))
        for i, (p, dev, ino) in enumerate(sorted(dirs, key=lambda x: len(x[0].parts), reverse=True)):
            if i % 100 == 0:
                stable()
            s = directory(paths, p)
            if (s.st_dev, s.st_ino) != (dev, ino):
                raise Unsafe('old program directory replaced')
            p.rmdir()  # never removes any unknown new file
        stable()
        record['status'] = 'compacted'; safe.atomic_json(receipt, record)
        audit(dict(event='compacted', batch=str(batch), archiveSha256=record['archiveSha256']))
        return dict(status='compacted', archive=str(archive), archiveBytes=archive.stat().st_size)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        if auditfd is not None:
            os.close(auditfd)
        for fd in reversed(fds):
            os.close(fd)


def state_roots():
    roots = [Path('/home/isp/state/cyf-agent-runtime-v1'), Path('/home/isp/state/cyf-agent-runtime-v1-managed'),
             Path('/home/isp/conf/cyf-agent-runtime-v1')]
    roots += [Path('/home/isp/apps/cyf-agent-runtime-v1') / name for name in ('linchong', 'lujunyi', 'wuyong')]
    return [p for p in roots if p.exists()]


def run_state(paths, mode, batch=None):
    scope = module('runtime_backup_scope', Path(__file__).with_name('runtime_backup_scope.py'))
    if mode == 'plan-state':
        return scope.summary(scope.plan(state_roots()))  # live inventory, not a recovery claim
    fds = []
    try:
        for lock in (paths.lock, paths.release_lock):
            before = safe.regular(lock)
            fd = os.open(str(lock), os.O_RDWR | os.O_NOFOLLOW); fds.append(fd)
            if safe.signature(os.fstat(fd)) != safe.signature(before): raise Unsafe('state backup lock changed')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if safe.signature(lock.lstat()) != safe.signature(before): raise Unsafe('state backup lock replaced')
        if batch is None or batch.parent != paths.base or not re.fullmatch(r'20\d{6}-[A-Za-z0-9_.-]+', batch.name):
            raise Unsafe('explicit Runtime state backup batch required')
        directory(paths, batch)
        if any((batch / name).exists() for name in ('state.tar', 'state.tar.gz', 'state-scope.json', 'PAYLOAD_RETIRED.json')):
            raise Unsafe('existing state recovery payload is immutable')
        pin, current_sig = read_current(paths)
        if batch == pin: raise Unsafe('cannot rewrite pinned recovery point')
        unit = 'cyf-agent-runtime-v1@unified.service'
        def stopped():
            state = subprocess.check_output(['systemctl', 'show', unit, '-p', 'ActiveState', '--value']).strip()
            pid = subprocess.check_output(['systemctl', 'show', unit, '-p', 'MainPID', '--value']).strip()
            loaded = subprocess.check_output(['systemctl', 'show', unit, '-p', 'LoadState', '--value']).strip()
            if loaded != b'loaded' or state not in (b'inactive', b'failed') or pid != b'0': raise Unsafe('Runtime must already be stopped by release Owner')
            cgroup = subprocess.check_output(['systemctl', 'show', unit, '-p', 'ControlGroup', '--value']).decode().strip()
            if cgroup:
                for base in (Path('/sys/fs/cgroup'), Path('/sys/fs/cgroup/systemd')):
                    members = base / cgroup.lstrip('/') / 'cgroup.procs'
                    if members.exists() and members.read_text().strip(): raise Unsafe('Runtime cgroup still has children')
            usage = safe.proc.snapshot(paths.proc)
            if any(usage.used(root) for root in state_roots()): raise Unsafe('state roots still in use')
            if safe.signature(paths.current.lstat()) != current_sig: raise Unsafe('release record changed')
        stopped()
        with (batch / 'state-backup.log').open('xb') as log:
            os.chmod(str(batch / 'state-backup.log'), 0o600)
            result = scope.write_state_archive(batch / 'state.tar.gz', state_roots(), log,
                release_binding={'currentRecordSha256': program_digest(paths.current)})
        stopped()
        return dict(status='essential-state-backed-up-not-restored', archive=str(batch / 'state.tar.gz'),
                    archiveSha256=result['archiveSha256'], archiveBytes=result['archiveBytes'],
                    excludedCount=len(result['excluded']))
    finally:
        for fd in reversed(fds): os.close(fd)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['plan', 'clean', 'compact-program', 'restore-program', 'plan-state', 'backup-state'])
    p.add_argument('--batch', type=Path)
    p.add_argument('--manifest-sha256')
    p.add_argument('--destination', type=Path)
    p.add_argument('--host-lock-fd', type=int)
    args = p.parse_args()
    if os.geteuid() != 0 or (args.host_lock_fd is not None and args.host_lock_fd < 3):
        p.error('root and a valid inherited lock FD required')
    try:
        if args.mode in ('plan-state', 'backup-state'):
            if args.host_lock_fd is not None or args.manifest_sha256 or args.destination or (args.mode == 'plan-state' and args.batch) or (args.mode == 'backup-state' and not args.batch):
                p.error('plan-state has no write options; backup-state requires only a new explicit batch')
            result = run_state(Paths(), args.mode, args.batch)
        elif args.mode in ('compact-program', 'restore-program'):
            if not args.batch or not re.fullmatch(r'[0-9a-f]{64}', args.manifest_sha256 or '') or args.host_lock_fd is not None:
                p.error('explicit batch, full manifest SHA-256 and independently acquired locks required')
            if (args.mode == 'compact-program' and args.destination is not None) or (args.mode == 'restore-program' and args.destination is None):
                p.error('destination is required only for restore-program')
            result = run_program(Paths(), args.mode, args.batch, args.manifest_sha256, args.destination)
        else:
            if args.batch or args.manifest_sha256 or args.destination:
                p.error('program archive options do not apply to retention')
            result = run(Paths(), args.mode, args.host_lock_fd)
        print(json.dumps(result))
        return 0
    except (OSError, Unsafe, ValueError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError) as e:
        print('Runtime backup cleanup stopped safely: ' + str(e), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
