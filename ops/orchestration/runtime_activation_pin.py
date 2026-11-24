"""Persistent admission for one forward-only unified Runtime, not a release installer.

All writers use the original install transaction's open lock descriptor. The pin
lives outside the replaceable program/records; missing or denied never means
fall back. Readers do not take that lock (installer holds it through start).
"""
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid

from runtime_start_admission import require, verify


class ActivationPin:
    def __init__(self, directory, lock_path):
        self.directory = Path(directory)
        self.path = self.directory / 'unified.activation.json'
        self.lock = Path(lock_path)
        for root in (self.directory, self.lock.parent):
            require(root.is_absolute() and root.resolve(strict=True) == root, 'noncanonical control path')
            for p in (root, *root.parents):
                s = p.lstat()
                require(stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022,
                        'untrusted control directory')

    def _read(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, 'rb') as f:
            s = os.fstat(fd)
            require(stat.S_ISREG(s.st_mode) and s.st_uid == 0 and s.st_nlink == 1 and
                    stat.S_IMODE(s.st_mode) == 0o600, 'untrusted activation pin')
            obj = json.load(f)
        require(obj['schema'] == 1 and obj['unit'] == 'cyf-agent-runtime-v1@unified.service' and
                uuid.UUID(obj['generation']).hex == obj['generation'] and obj['state'] in ('DENIED', 'ALLOWED'),
                'invalid activation pin')
        return obj

    def read_allowed(self):
        obj = self._read()
        require(obj is not None and obj['state'] == 'ALLOWED', 'activation not permitted')
        return obj

    def _writer(self, fd, previous):
        lock = os.fstat(fd); path = self.lock.lstat()
        require(os.path.samestat(lock, path) and stat.S_ISREG(lock.st_mode) and lock.st_uid == 0 and
                lock.st_nlink == 1 and not lock.st_mode & 0o022, 'wrong release lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # same open description; never unlock it here
        obj = self._read()
        require((obj['generation'] if obj else None) == previous, 'activation generation changed')
        return obj

    def _write(self, state, **fields):
        obj = dict(schema=1, unit='cyf-agent-runtime-v1@unified.service', generation=uuid.uuid4().hex,
                   state=state, **fields)
        fd, tmp = tempfile.mkstemp(dir=self.directory, prefix='.activation-')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(obj, f); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, self.path)
            directory_fd = os.open(self.directory, os.O_DIRECTORY)
            try: os.fsync(directory_fd)
            finally: os.close(directory_fd)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return obj['generation']

    def deny(self, lock_fd, *, previous):
        self._writer(lock_fd, previous)
        return self._write('DENIED')

    def allow(self, lock_fd, *, previous, instance, records, pins):
        obj = self._writer(lock_fd, previous)
        require(obj is not None and obj['state'] == 'DENIED', 'must fence before activation')
        instance = Path(instance)
        require(Path(records).parent == instance and self.directory != instance and
                instance not in self.directory.parents, 'invalid activation layout')
        verify(instance / 'app', records, **pins)
        s = instance.stat()
        return self._write('ALLOWED', device=s.st_dev, inode=s.st_ino, pins=pins)
