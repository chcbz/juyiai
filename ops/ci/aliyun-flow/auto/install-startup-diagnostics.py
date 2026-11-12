#!/usr/bin/env python3
"""Flow-only tooling installation: no application start, stop, build or SQL.

The caller supplies a fixed candidate manifest in its private bundle. Existing
coordinator/release/lifecycle locks serialize this change with normal releases.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

NAMES = ('cyf-api-kit', 'cyf-api-flow-install')
LOCKS = ('/tmp/cyf-api-flow-auto-approval-v2.lock', '/tmp/cyf-release-api.lock',
         '/tmp/cyf-api-lifecycle.lock')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fsync_directory(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_regular(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or info.st_mode & 0o022:
            raise RuntimeError('unsafe tooling file: ' + path.name)
        with os.fdopen(fd, 'rb') as source:
            fd = None
            return source.read(), info
    finally:
        if fd is not None:
            os.close(fd)


def atomic_write(path, data, mode):
    fd, temporary = tempfile.mkstemp(prefix='.startup-diagnostics-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as target:
            os.fchmod(target.fileno(), mode)
            os.fchown(target.fileno(), 0, 0)
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, str(path))
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def owned_private_directory(path):
    path.mkdir(mode=0o700, exist_ok=True)
    s = path.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or s.st_gid != 0 or stat.S_IMODE(s.st_mode) != 0o700:
        raise RuntimeError('unsafe backup directory')


def main():
    if os.geteuid() != 0 or os.environ.get('PIPELINE_ID') != '5264702':
        raise RuntimeError('requires the existing Flow manual operations pipeline')
    if len(sys.argv) != 2:
        raise RuntimeError('requires private bundle root')
    bundle = Path(sys.argv[1]).resolve(strict=True)
    manifest = json.loads((bundle / 'diagnostic-manifest.json').read_text())
    if set(manifest) != {'schemaVersion', 'helpers'} or manifest['schemaVersion'] != 1 or set(manifest['helpers']) != set(NAMES):
        raise RuntimeError('unexpected candidate manifest')
    candidates, before, handles = {}, {}, []
    destination = Path('/usr/local/sbin')
    for parent in (Path('/usr'), Path('/usr/local'), destination):
        s = parent.lstat()
        if not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o022:
            raise RuntimeError('unsafe tooling parent')
    for name in NAMES:
        data, _ = read_regular(bundle / 'ops/ci/aliyun-flow/host' / name)
        spec = manifest['helpers'][name]
        if set(spec) != {'beforeSha256', 'candidateSha256'} or digest(data) != spec['candidateSha256']:
            raise RuntimeError('candidate digest mismatch')
        subprocess.run(['/bin/bash', '-n', str(bundle / 'ops/ci/aliyun-flow/host' / name)], check=True)
        candidates[name] = data
    try:
        for lock in LOCKS:
            fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
            handles.append(fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1:
                raise RuntimeError('unsafe existing lock')
            fcntl.flock(fd, fcntl.LOCK_EX)
            current = os.stat(lock, follow_symlinks=False)
            if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
                raise RuntimeError('lock inode changed')
        for name in NAMES:
            data, info = read_regular(destination / name)
            if stat.S_IMODE(info.st_mode) != 0o755 or info.st_gid != 0:
                raise RuntimeError('unexpected installed helper metadata')
            if digest(data) not in (manifest['helpers'][name]['beforeSha256'], manifest['helpers'][name]['candidateSha256']):
                raise RuntimeError('helper changed by another owner; preserve it')
            before[name] = data
        identity = digest(json.dumps(manifest, sort_keys=True).encode())
        backup_root = Path('/home/isp/state/cyf-api-flow/diagnostic-tooling')
        owned_private_directory(backup_root)
        backup = backup_root / identity
        owned_private_directory(backup)
        # Save exact originals before any replacement; existing backups are immutable.
        for name in NAMES:
            path = backup / (name + '.before')
            if not path.exists():
                if digest(before[name]) != manifest['helpers'][name]['beforeSha256']:
                    raise RuntimeError('already changed helper has no original backup')
                atomic_write(path, before[name], 0o600)
            else:
                old, _ = read_regular(path)
                if digest(old) != manifest['helpers'][name]['beforeSha256']:
                    raise RuntimeError('backup identity mismatch')
        changed = []
        try:
            for name in NAMES:
                if before[name] != candidates[name]:
                    # Record before replace, so a post-replace fsync error also restores.
                    changed.append(name)
                    atomic_write(destination / name, candidates[name], 0o755)
                actual, _ = read_regular(destination / name)
                if digest(actual) != manifest['helpers'][name]['candidateSha256']:
                    raise RuntimeError('installed readback mismatch')
        except BaseException:
            for name in reversed(changed):
                atomic_write(destination / name, before[name], 0o755)
            raise
        result = {'status': 'installed', 'applicationRestarted': False, 'sqlExecuted': False,
                  'pipeline': '5264702', 'run': os.environ.get('BUILD_NUMBER'),
                  'diagnosticsDefault': 'off', 'helpers': manifest['helpers']}
        atomic_write(backup / 'result.json', (json.dumps(result, sort_keys=True) + '\n').encode(), 0o600)
        print('CYF_STARTUP_DIAGNOSTICS_TOOLING=' + json.dumps(result, sort_keys=True))
    finally:
        for fd in reversed(handles):
            os.close(fd)


if __name__ == '__main__':
    main()
