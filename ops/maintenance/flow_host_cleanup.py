#!/usr/bin/python3
"""Flow host cleanup with bounded, deployment-state-guarded Flow payload retention.

It never scans worktrees, caches, databases, Codex history, or cloud credentials.
API cleanup requires a confirmed installed record; Web download cleanup requires a
confirmed online-verified record.  Both deployment locks are held for mutations.
Python 3.6+; tests use isolated Paths, never the production CLI.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

BACKUP_NAME = re.compile(r'[0-9]{8}T[0-9]{6}Z-[0-9a-f]{64}-[0-9]+\.jar')
CHUNK = 1024 * 1024  # streaming buffer, not an artifact-size admission limit
# Total rollback payload limit, INCLUDING the record-pinned rollback JAR.
API_BACKUP_KEEP = 2
# Keep the newest completed download for quick investigation and one predecessor.
API_DOWNLOAD_KEEP = 2
WEB_DOWNLOAD_KEEP = 2


class Unsafe(RuntimeError):
    pass


class Paths:
    def __init__(self):
        self.api = Path('/home/isp/state/cyf-api-flow')
        self.validator = Path('/usr/local/sbin/cyf-api-flow-deploy')
        self.web_validator = Path('/usr/local/sbin/cyf-web-flow-deploy')
        # Rollback JARs are centralized; Flow state remains under /var/lib.
        self.api_backups = Path('/home/isp/baks/flow-api')
        self.web = Path('/home/isp/state/cyf-web-flow')
        self.audit = Path('/home/isp/state/cyf-flow-cleanup/audit.jsonl')
        self.mountinfo = Path('/proc/self/mountinfo')
        # Same order as existing auto deploy -> installer; never change lock metadata.
        self.locks = [(Path('/run/lock/cyf-clear-disk.lock'), (0o600, 0o644)),
                      (Path('/tmp/cyf-api-flow-auto-approval-v2.lock'), (0o600,)),
                      (Path('/tmp/cyf-release-api.lock'), (0o660,)),
                      (Path('/home/isp/state/cyf-web-flow/deploy.lock'), (0o600,))]


def physical_dir(path):
    path = Path(path)
    st = path.lstat()
    if (not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid()
            or st.st_mode & 0o022 or str(path.resolve()) != str(path)):
        raise Unsafe('unsafe directory: ' + str(path))
    if (path / '.keep').exists() or (path / '.keep').is_symlink():
        raise Unsafe('.keep protects directory: ' + str(path))
    return st


def signature(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid,
            st.st_nlink, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def regular(path, modes=(0o600,)):
    st = Path(path).lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid()
            or st.st_nlink != 1 or stat.S_IMODE(st.st_mode) not in modes):
        raise Unsafe('unsafe file: ' + str(path))
    return st


@contextmanager
def locked(paths):
    descriptors = []
    try:
        for path, modes in paths.locks:
            before = regular(path, modes)
            fd = os.open(str(path), os.O_RDWR | os.O_NOFOLLOW)
            descriptors.append(fd)
            if signature(os.fstat(fd)) != signature(before):
                raise Unsafe('lock changed while opening')
            fcntl.flock(fd, fcntl.LOCK_EX)  # wait; no timeout or preemption
            if signature(path.lstat()) != signature(os.fstat(fd)):
                raise Unsafe('lock path was replaced')
        yield
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def read_v3_validator(paths, path=None):
    """Reuse the installer's trusted contract, without executing its CLI."""
    path = paths.validator if path is None else path
    for parent in reversed(path.parents):
        physical_dir(parent)
    before = regular(path, modes=(0o755,))
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        if signature(os.fstat(stream.fileno())) != signature(before):
            raise Unsafe('validator changed while opening')
        code = stream.read()
        if (signature(os.fstat(stream.fileno())) != signature(before)
                or signature(path.lstat()) != signature(before)):
            raise Unsafe('validator changed while reading')
    namespace = {'__name__': '_cyf_cleanup_validator', '__file__': str(path)}
    exec(compile(code, str(path), 'exec'), namespace)
    return namespace


def validate_v3(paths, state):
    validator = read_v3_validator(paths)
    try:
        validator['local_install_record'](state, Path(state['backup']).parent)
    except (validator['LocalRejected'], KeyError, TypeError, ValueError) as exc:
        raise Unsafe('invalid v3 installation record: ' + str(exc))


def file_digest(path):
    before = regular(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    with os.fdopen(fd, 'rb') as stream:
        if signature(os.fstat(stream.fileno())) != signature(before):
            raise Unsafe('rollback changed while opening')
        while True:
            data = stream.read(CHUNK)
            if not data:
                break
            digest.update(data)
        if (signature(os.fstat(stream.fileno())) != signature(before)
                or signature(path.lstat()) != signature(before)):
            raise Unsafe('rollback changed while hashing')
    return digest.hexdigest()


def read_state(paths):
    physical_dir(paths.api)
    physical_dir(paths.api_backups)
    path = paths.api / 'record.json'
    before = regular(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as f:
        if signature(os.fstat(f.fileno())) != signature(before):
            raise Unsafe('record changed while opening')
        state = json.load(f)
        if signature(os.fstat(f.fileno())) != signature(before):
            raise Unsafe('record changed while reading')
    if (not isinstance(state, dict) or type(state.get('schema_version')) is not int
            or state.get('schema_version') not in (2, 3, 4)
            or state.get('status') != 'installed' or state.get('phase') != 'installed'
            or state.get('recovery') != 'not_required'):
        raise Unsafe('installation not in a confirmed installed state; preserve all backups')
    version = state['schema_version']
    if version == 2 and not re.fullmatch('[1-9][0-9]*', str(state.get('run_id', ''))):
        raise Unsafe('invalid v2 Flow run identity')
    if version == 3:
        validate_v3(paths, state)
    if version == 4:
        validator = read_v3_validator(paths)
        try:
            validator['native_record'](state, Path(state['backup']).parent)
        except (SystemExit, KeyError, TypeError, ValueError) as exc:
            raise Unsafe('invalid native LOCAL installation record: ' + str(exc))
        if state['previous_sha256'] != state['expected_previous_sha256']:
            raise Unsafe('LOCAL predecessor digest mismatch')
    if not isinstance(state.get('backup'), str):
        raise Unsafe('invalid pinned rollback path')
    # Flow may still persist the legacy /var/lib alias.  Resolve it once and
    # operate only on the canonical centralized directory thereafter.
    try:
        backup = Path(state['backup']).resolve()
    except (OSError, RuntimeError):
        raise Unsafe('invalid pinned rollback path')
    if backup.parent != paths.api_backups or not BACKUP_NAME.fullmatch(backup.name):
        raise Unsafe('invalid pinned rollback path')
    regular(backup)  # Missing/unsafe pin must not silently make everything deletable.
    if version in (3, 4):
        if file_digest(backup) != state['previous_sha256']:
            raise Unsafe('v3 pinned rollback digest mismatch')
        # Null audit Run means LOCAL; never invent a numeric Flow identity.
        state['run_id'] = None
    state['backup'] = str(backup)
    if signature(path.lstat()) != signature(before):
        raise Unsafe('record changed during validation')
    return state, signature(before)


def read_web_state(paths):
    """Require completed public verification before retaining Web download payloads."""
    physical_dir(paths.web)
    physical_dir(paths.web / 'downloads')
    path = paths.web / 'record.json'
    before = regular(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as f:
        if signature(os.fstat(f.fileno())) != signature(before):
            raise Unsafe('web record changed while opening')
        state = json.load(f)
        if signature(os.fstat(f.fileno())) != signature(before):
            raise Unsafe('web record changed while reading')
    if (not isinstance(state, dict) or type(state.get('schema_version')) is not int
            or state.get('schema_version') not in (1, 2)
            or state.get('status') != 'online_verified' or state.get('phase') != 'online_verified'):
        raise Unsafe('web installation is not online verified; preserve all Web downloads')
    if state['schema_version'] == 1:
        if not re.fullmatch('[1-9][0-9]*', str(state.get('run_id', ''))):
            raise Unsafe('invalid Web Flow run')
    else:
        binding = state.get('binding_sha256')
        if state.get('source_kind') != 'LOCAL' or not re.fullmatch('[0-9a-f]{64}', str(binding)):
            raise Unsafe('invalid Web LOCAL binding')
        # Reuse the installed producer/installer contract and original private
        # descriptor. Never fabricate a Flow Run for audit or rewrite records.
        backup = paths.web / 'backups' / binding
        physical_dir(backup)
        try:
            if not os.path.samefile(str(backup), state['backup']):
                raise Unsafe('Web LOCAL backup mismatch')
            validator = read_v3_validator(paths, paths.web_validator)
            descriptor = validator['local_descriptor'](backup / 'descriptor.json')
            actual = hashlib.sha256(validator['local_json_bytes'](descriptor)).hexdigest()
            if (actual != binding or descriptor['source'] != state['source']
                    or descriptor['package'] != state['package']
                    or state['artifact_sha256'] != descriptor['package']['sha256']):
                raise Unsafe('Web LOCAL source/package binding mismatch')
        except (SystemExit, KeyError, TypeError, ValueError) as exc:
            raise Unsafe('invalid Web LOCAL record: ' + str(exc))
        state['run_id'] = None
    if signature(path.lstat()) != signature(before):
        raise Unsafe('Web record changed during validation')
    return state, signature(before)


def guard_payload(paths, path, root):
    """Respect keep markers and mounted storage before planning or unlinking."""
    if root not in path.parents:
        raise Unsafe('payload outside retention root')
    parent = path.parent
    while True:
        physical_dir(parent)
        if parent == root:
            break
        parent = parent.parent
    # st_dev and -xdev miss same-device bind mounts, including a mounted file.
    for line in paths.mountinfo.read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            raise Unsafe('invalid mountinfo')
        target = Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), fields[4]))
        if target != Path('/') and (target == path or target in path.parents):
            raise Unsafe('mounted retention payload: ' + str(path))


def package_entries(root, paths=None):
    """Return verified numeric-run package payloads, newest first, without recursion."""
    physical_dir(root)
    entries = []
    for child in root.iterdir():
        if not child.name.isdigit():
            continue
        try:
            physical_dir(child)
            package = child / 'package.tgz'
            guard_payload(paths or Paths(), package, root)
            st = regular(package, modes=(0o600, 0o644))
        except (FileNotFoundError, Unsafe):
            continue
        entries.append((st.st_mtime_ns, package, st))
    return sorted(entries, key=lambda row: (row[0], row[1].name), reverse=True)


def retention_action(path, st, reason, run_id):
    return {'remove': str(path), 'remove_signature': signature(st),
            'allocated_bytes': st.st_blocks * 512, 'reason': reason,
            'run_id': run_id}


def api_backup_retention(paths, state, duplicates=()):
    """Keep at most two payloads: the pinned rollback and one newest distinct history."""
    pinned = Path(state['backup'])
    newest, actions = 0, []
    rows = []
    for entry in (paths.api_backups).iterdir():
        if not BACKUP_NAME.fullmatch(entry.name):
            continue
        try:
            guard_payload(paths, entry, paths.api_backups)
            st = regular(entry)
        except Unsafe:
            continue
        rows.append((st.st_mtime_ns, entry, st))
    for _, entry, st in sorted(rows, key=lambda row: (row[0], row[1].name), reverse=True):
        if entry == pinned or str(entry) in duplicates:
            continue
        if newest < API_BACKUP_KEEP - 1:
            newest += 1
            continue
        actions.append(retention_action(entry, st, 'api_backup_retention', state['run_id']))
    return actions


def download_retention(paths, api_state, web_state):
    actions = []
    for root, keep, reason, state in (
            (paths.api / 'downloads', API_DOWNLOAD_KEEP, 'api_download_retention', api_state),
            (paths.web / 'downloads', WEB_DOWNLOAD_KEEP, 'web_download_retention', web_state)):
        for index, (_, package, st) in enumerate(package_entries(root, paths)):
            if index >= keep:
                actions.append(retention_action(package, st, reason, state['run_id']))
    return actions


def identical(a, b):
    """Compare actual bytes, not names (installer names contain CANDIDATE digest)."""
    sa, sb = regular(a), regular(b)
    if sa.st_size != sb.st_size:
        return None
    fa = os.open(str(a), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fb = os.open(str(b), os.O_RDONLY | os.O_NOFOLLOW)
    except BaseException:
        os.close(fa)
        raise
    digest = hashlib.sha256()
    with os.fdopen(fa, 'rb') as left, os.fdopen(fb, 'rb') as right:
        if (signature(os.fstat(left.fileno())) != signature(sa)
                or signature(os.fstat(right.fileno())) != signature(sb)):
            raise Unsafe('backup changed while opening')
        while True:
            x, y = left.read(CHUNK), right.read(CHUNK)
            if x != y:
                return None
            if not x:
                break
            digest.update(x)
        if (signature(os.fstat(left.fileno())) != signature(sa)
                or signature(os.fstat(right.fileno())) != signature(sb)
                or signature(a.lstat()) != signature(sa)
                or signature(b.lstat()) != signature(sb)):
            raise Unsafe('backup changed during comparison')
    return {'sha256': digest.hexdigest(), 'size': sa.st_size,
            'remove_signature': signature(sa), 'keep_signature': signature(sb),
            'allocated_bytes': sa.st_blocks * 512}


def legacy_v2_retirement(paths, state):
    """Opt-in retirement of the v2 rollback named by v3's bound precondition."""
    if state['schema_version'] != 3:
        raise Unsafe('v2 retirement requires a confirmed v3 installation')
    ref = state['release']['precondition']['installedRecord']
    if ref is None:
        return []
    record = Path(ref['path'])
    guard_payload(paths, record, paths.api / 'local-inputs')
    before = regular(record)
    if before.st_size != ref['size'] or file_digest(record) != ref['sha256']:
        raise Unsafe('v2 history evidence digest mismatch')
    fd = os.open(str(record), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        if signature(os.fstat(stream.fileno())) != signature(before):
            raise Unsafe('v2 history evidence changed')
        old = json.load(stream)
        if (signature(os.fstat(stream.fileno())) != signature(before)
                or signature(record.lstat()) != signature(before)):
            raise Unsafe('v2 history evidence changed')
    if old.get('schema_version') != 2:
        return []
    if (old.get('status') != 'installed' or old.get('phase') != 'installed'
            or old.get('recovery') != 'not_required'
            or not re.fullmatch('[1-9][0-9]*', str(old.get('run_id', '')))
            or not isinstance(old.get('backup'), str)):
        raise Unsafe('unconfirmed v2 history evidence')
    target = Path(old['backup']).resolve()
    if target.parent != paths.api_backups or not BACKUP_NAME.fullmatch(target.name):
        raise Unsafe('v2 history backup outside scope')
    # The active record pin is unconditional, even if its bytes came from v2.
    if target == Path(state['backup']):
        return []
    if not target.exists() and not target.is_symlink():
        return []  # Already retired; repeated invocation is harmless.
    guard_payload(paths, target, paths.api_backups)
    st = regular(target)
    if file_digest(target) != old.get('previous_sha256'):
        raise Unsafe('v2 history backup digest mismatch')
    action = retention_action(target, st, 'api_backup_retention', None)
    action['retired_schema_version'] = 2
    action['evidence'] = str(record)
    return [action]


def plan(paths, retire_v2=False):
    state, record_signature = read_state(paths)
    web_state, web_record_signature = read_web_state(paths)
    pinned = Path(state['backup'])
    groups, skipped, actions = {}, [], []
    # Pinned first, then newest: duplicate keepers must be the most recent
    # representatives, not whichever name happens to sort first.
    entries = sorted(paths.api_backups.iterdir(),
                     key=lambda p: (p != pinned, -p.lstat().st_mtime_ns, p.name))
    for p in entries:
        if not BACKUP_NAME.fullmatch(p.name):
            continue  # do not inspect JSON approval/history/evidence contents
        try:
            guard_payload(paths, p, paths.api_backups)
            st = regular(p)
        except Unsafe:
            skipped.append(str(p))
            continue
        keepers = groups.setdefault(st.st_size, [])
        for keeper in keepers:
            proof = identical(p, keeper)
            if proof is not None:
                actions.append(dict(proof, remove=str(p), keep=str(keeper),
                                    reason='byte_identical_backup', run_id=state['run_id']))
                break
        else:
            keepers.append(p)

    legacy_actions = legacy_v2_retirement(paths, state) if retire_v2 else []
    # De-duplicate first, then retain bounded distinct history and completed downloads.
    seen = set(action['remove'] for action in actions)
    for action in legacy_actions + api_backup_retention(paths, state, seen) + download_retention(paths, state, web_state):
        if action['remove'] not in seen:
            actions.append(action)
            seen.add(action['remove'])
    return {'pinned_backup': str(pinned), 'record_signature': record_signature,
            'web_record_signature': web_record_signature, 'actions': actions,
            'estimated_reclaim_bytes': sum(a['allocated_bytes'] for a in actions),
            'skipped_unsafe': skipped,
            'protected': ['record.json referenced API rollback JAR',
                          'at most %d API JAR backups total: pinned rollback plus newest %d distinct history' %
                          (API_BACKUP_KEEP, API_BACKUP_KEEP - 1),
                          'newest %d API and %d Web downloaded packages' %
                          (API_DOWNLOAD_KEEP, WEB_DOWNLOAD_KEEP),
                          'API incoming payload, worktrees, caches, /tmp, evidence, databases, Codex history']}


def open_elsewhere(path, proc_root=Path('/proc')):
    # Fail closed on missing scanner/permission errors. Include inode-based FD
    # aliases and maps even when the mapping's original descriptor is closed.
    spec = importlib.util.spec_from_file_location('cleanup_process_usage',
        str(Path(__file__).with_name('host_cleanup_processes.py')))
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    usage = scanner.snapshot(proc_root)
    return usage.used(path) or usage.used(path.parent)


def audit(paths, event):
    physical_dir(paths.audit.parent)
    if paths.audit.exists() or paths.audit.is_symlink():
        regular(paths.audit)
    fd = os.open(str(paths.audit), os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as out:
        if (os.fstat(out.fileno()).st_nlink != 1
                or signature(os.fstat(out.fileno())) != signature(regular(paths.audit))):
            raise Unsafe('audit file changed')
        out.write(json.dumps(dict(event, time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                             sort_keys=True) + '\n')
        out.flush()
        os.fsync(out.fileno())


def retention_regular(paths, action):
    path = Path(action['remove'])
    reason = action['reason']
    if reason == 'api_backup_retention':
        if path.parent != paths.api_backups or not BACKUP_NAME.fullmatch(path.name):
            raise Unsafe('out-of-scope API backup retention candidate')
        guard_payload(paths, path, paths.api_backups)
        return path, regular(path)
    if reason == 'api_download_retention':
        if (path.name != 'package.tgz' or path.parent.parent != paths.api / 'downloads'
                or not path.parent.name.isdigit()):
            raise Unsafe('out-of-scope API download retention candidate')
        guard_payload(paths, path, path.parent.parent)
        return path, regular(path, modes=(0o600, 0o644))
    if reason == 'web_download_retention':
        if (path.name != 'package.tgz' or path.parent.parent != paths.web / 'downloads'
                or not path.parent.name.isdigit()):
            raise Unsafe('out-of-scope Web download retention candidate')
        guard_payload(paths, path, path.parent.parent)
        return path, regular(path, modes=(0o600, 0o644))
    raise Unsafe('unknown retention reason')


def unlink_payload(paths, path, expected, root):
    """Unlink only the revalidated original file through a no-symlink parent FD."""
    guard_payload(paths, path, root)
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        parent = physical_dir(path.parent)
        opened = os.fstat(directory)
        if (parent.st_dev, parent.st_ino) != (opened.st_dev, opened.st_ino):
            raise Unsafe('payload parent changed')
        try:
            os.stat('.keep', dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Unsafe('.keep appeared before payload unlink')
        current = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        if signature(current) != tuple(expected):
            raise Unsafe('payload changed before fd-based unlink')
        os.unlink(path.name, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)


def unlink_retained(paths, action, busy):
    remove, st = retention_regular(paths, action)
    if signature(st) != action['remove_signature']:
        raise Unsafe('retention candidate changed after plan')
    if busy(remove):
        return None
    event = {k: action[k] for k in ('remove', 'reason', 'allocated_bytes', 'run_id')}
    for key in ('retired_schema_version', 'evidence'):
        if key in action:
            event[key] = action[key]
    audit(paths, dict(event, event='remove_intent'))
    if signature(retention_regular(paths, action)[1]) != action['remove_signature']:
        raise Unsafe('retention candidate changed before unlink')
    unlink_payload(paths, remove, action['remove_signature'],
                   paths.api_backups if action['reason'] == 'api_backup_retention' else remove.parent.parent)
    audit(paths, dict(event, event='removed'))
    return event


def apply(paths, proposal, busy=open_elsewhere):
    removed, skipped = [], []
    # Caller holds API and Web deployment locks. Never accepts a caller-supplied plan.
    for action in proposal['actions']:
        state, current_record = read_state(paths)
        _, current_web_record = read_web_state(paths)
        if (current_record != proposal['record_signature']
                or current_web_record != proposal['web_record_signature']):
            raise Unsafe('deployment record changed')
        if action['reason'] != 'byte_identical_backup':
            event = unlink_retained(paths, action, busy)
            if event is None:
                skipped.append(action['remove'])
            else:
                removed.append(event)
            continue

        remove, keep = Path(action['remove']), Path(action['keep'])
        if (remove.parent != paths.api_backups or keep.parent != remove.parent
                or remove == Path(state['backup']) or remove == keep):
            raise Unsafe('out-of-scope or pinned duplicate candidate')
        guard_payload(paths, remove, paths.api_backups)
        guard_payload(paths, keep, paths.api_backups)
        if (signature(regular(remove)) != action['remove_signature']
                or signature(regular(keep)) != action['keep_signature']):
            raise Unsafe('duplicate candidate changed after plan')
        if busy(remove) or busy(keep):
            skipped.append(str(remove))
            continue
        proof = identical(remove, keep)
        if proof is None or proof['sha256'] != action['sha256']:
            raise Unsafe('duplicate proof changed')
        event = {k: action[k] for k in ('remove', 'keep', 'sha256', 'size',
                                        'allocated_bytes', 'run_id', 'reason')}
        audit(paths, dict(event, event='remove_intent'))
        if (signature(regular(remove)) != proof['remove_signature']
                or signature(regular(keep)) != proof['keep_signature']):
            raise Unsafe('duplicate candidate changed before unlink')
        guard_payload(paths, keep, paths.api_backups)
        unlink_payload(paths, remove, proof['remove_signature'], paths.api_backups)
        audit(paths, dict(event, event='removed'))
        removed.append(event)
    return {'removed': removed, 'skipped_open_files': skipped,
            'reclaimed_allocated_bytes': sum(e['allocated_bytes'] for e in removed)}


def inventory(paths):
    """Metadata only, fixed directories/depth; never recurse through task worktrees."""
    areas = {}
    for root in (paths.api_backups, paths.api / 'incoming',
                 paths.api / 'downloads', paths.web / 'downloads'):
        size, count = 0, 0
        if root.exists():
            physical_dir(root)
            for entry in root.iterdir():
                st = entry.lstat()
                if stat.S_ISREG(st.st_mode):
                    size += st.st_blocks * 512
                    count += 1
                elif stat.S_ISDIR(st.st_mode) and entry.name.isdigit() and root.name == 'downloads':
                    package = entry / 'package.tgz'
                    try:
                        st = package.lstat()
                        if stat.S_ISREG(st.st_mode):
                            size += st.st_blocks * 512
                            count += 1
                    except FileNotFoundError:
                        pass
        areas[str(root)] = {'allocated_bytes': size, 'files': count}
    disk = os.statvfs('/')
    return {'available_bytes': disk.f_bavail * disk.f_frsize, 'areas': areas,
            'space_target': None, 'scope': 'Flow payload metadata only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', default='check', choices=('check', 'check-deep', 'plan', 'clean'))
    parser.add_argument('--retire-v2-backups', action='store_true',
                        help='explicitly retire the old v2 rollback proven by v3 precondition evidence; never the active pin')
    args = parser.parse_args()
    if args.retire_v2_backups and args.mode not in ('plan', 'clean'):
        parser.error('v2 retirement is available only with plan or clean')
    paths = Paths()
    if os.geteuid() != 0:
        parser.error('root is required to inspect protected Flow deployment state')
    try:
        if args.mode in ('check', 'check-deep'):
            result = inventory(paths)
        else:
            with locked(paths):
                proposal = plan(paths, retire_v2=args.retire_v2_backups)
                result = proposal if args.mode == 'plan' else apply(paths, proposal)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, Unsafe) as exc:
        event = {'event': 'cleanup_stopped', 'error': str(exc), 'mode': args.mode}
        if args.mode == 'clean':
            try:
                audit(paths, event)
            except (OSError, Unsafe):
                pass
        print(json.dumps(event), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
