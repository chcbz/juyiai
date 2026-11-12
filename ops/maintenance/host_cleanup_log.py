#!/usr/bin/python3
"""Persistent private cleanup logging; refuse unsafe sinks before starting work."""
import fcntl
import json
import syslog
import uuid
import os
from pathlib import Path
import signal
import select
import stat
import subprocess
import sys
import time

LOG = Path('/home/isp/logs/clear_disk.log')
LOCK = Path('/run/lock/cyf-cleanup-log.lock')
CLEANUP_STARTED = False

class CleanupInterrupted(Exception):
    def __init__(self, signum):
        self.signum = signum
        super().__init__('cleanup logger interrupted by signal %d' % signum)

def open_parent(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts or len(path.parts) < 2:
        raise ValueError('invalid absolute cleanup log path')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        return directory
    except Exception:
        os.close(directory)
        raise

def safe_log_stat(s):
    if (not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_nlink != 1
            or s.st_mode & 0o022):
        raise ValueError('unsafe cleanup log')

def open_log(path, directory=None):
    # Anchor the entire parent walk, not just the leaf; reject FIFO without wait.
    own_directory = directory is None
    if own_directory:
        directory = open_parent(path)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=directory)
        try:
            s = os.fstat(fd)
            safe_log_stat(s)
            current = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            if (s.st_dev, s.st_ino) != (current.st_dev, current.st_ino):
                raise ValueError('cleanup log changed while opening')
            os.fchmod(fd, 0o600)
            return fd
        except Exception:
            os.close(fd)
            raise
    finally:
        if own_directory:
            os.close(directory)

def validate_log(fd):
    directory = open_parent(LOG)
    try:
        opened = os.fstat(fd)
        current = os.stat(LOG.name, dir_fd=directory, follow_symlinks=False)
        safe_log_stat(current)
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError('cleanup log path changed during execution')
    finally:
        os.close(directory)

def rotate_log(fd):
    if os.fstat(fd).st_size < 8 * 1024 * 1024:
        return fd
    directory = open_parent(LOG)
    try:
        # Snapshot the ENTIRE chain before any rename, all relative to one FD.
        chain = {}
        for i in range(6):
            name = LOG.name if i == 0 else LOG.name + '.' + str(i)
            try:
                s = os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            safe_log_stat(s)
            chain[name] = (s.st_dev, s.st_ino)
        if chain.get(LOG.name) != (os.fstat(fd).st_dev, os.fstat(fd).st_ino):
            raise ValueError('cleanup log changed before rotation')
        for i in range(5, 0, -1):
            old = LOG.name if i == 1 else LOG.name + '.' + str(i - 1)
            new = LOG.name + '.' + str(i)
            # Revalidate both ends against preflight immediately before rename.
            for name in (old, new):
                try:
                    s = os.stat(name, dir_fd=directory, follow_symlinks=False)
                    safe_log_stat(s)
                    actual = (s.st_dev, s.st_ino)
                except FileNotFoundError:
                    actual = None
                if actual != chain.get(name):
                    raise ValueError('rotation path changed after preflight')
            if old in chain:
                os.replace(old, new, src_dir_fd=directory, dst_dir_fd=directory)
                chain[new] = chain.pop(old)
        newfd = open_log(LOG, directory)
        try:
            os.fsync(directory)
        except Exception:
            os.close(newfd)
            raise
        os.close(fd)
        return newfd
    finally:
        os.close(directory)

def stop_group(child):
    # Cleanup owns its own session. Do not leave Flow/cache subprocesses alive
    # after a logging failure or interruption; no service processes join it.
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()

def interrupted(signum, frame):
    raise CleanupInterrupted(signum)

def report_status(code):
    """Local syslog + private machine-readable status; no external delivery implied."""
    space = os.statvfs('/')
    available = space.f_bavail * space.f_frsize
    state = 'critical' if available < 1024**3 else 'warning' if code or available < 5*1024**3 else 'ok'
    priority = syslog.LOG_CRIT if state == 'critical' else syslog.LOG_ERR if state == 'warning' else syslog.LOG_INFO
    syslog.openlog('cyf-host-cleanup', syslog.LOG_PID, syslog.LOG_DAEMON)
    syslog.syslog(priority, 'cleanup state=%s exit=%d free_MiB=%d; inspect private cleanup log' % (state, code, available//1024**2))
    path = LOG.with_name('clear_disk.status.json')
    directory = open_parent(path)
    temporary = '.' + path.name + '.' + uuid.uuid4().hex
    def existing():
        try:
            st = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            safe_log_stat(st)
            return st.st_dev, st.st_ino
        except FileNotFoundError:
            return None
    try:
        identity = existing()
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        with os.fdopen(fd, 'w') as f:
            json.dump({'finished_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'state':state, 'exit_code':code, 'available_bytes':available, 'cleanup_started':CLEANUP_STARTED}, f)
            f.flush(); os.fsync(f.fileno())
        if existing() != identity:
            raise ValueError('cleanup status changed before publication')
        os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try: os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError: pass
        os.close(directory)

def main():
    global CLEANUP_STARTED
    CLEANUP_STARTED = False
    if len(sys.argv) != 3 or sys.argv[2] != 'clean' or os.geteuid() != 0:
        raise ValueError('expected root: logger SCRIPT clean')
    lock = os.open(str(LOCK), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        s = os.fstat(lock)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_nlink != 1 or s.st_mode & 0o077:
            raise ValueError('unsafe cleanup logging lock')
        current = LOCK.lstat()
        if (s.st_dev, s.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError('cleanup logging lock changed')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another logged cleanup is running; exit')
            return 0
        fd = open_log(LOG)
        try:
            fd = rotate_log(fd)
            def emit(data):
                validate_log(fd)
                view = memoryview(data)
                while view:
                    n = os.write(fd, view)
                    if n <= 0:
                        raise OSError('cleanup log write made no progress')
                    view = view[n:]
                os.fsync(fd)
                try:
                    sys.stdout.buffer.write(data); sys.stdout.buffer.flush()
                except BrokenPipeError:
                    pass
            emit(('[%s] BEGIN cleanup\n' % time.strftime('%Y-%m-%d %H:%M:%S %z')).encode())
            env = os.environ.copy(); env['CYF_CLEANUP_LOGGED'] = '1'
            # Install handler before spawning to close the startup signal gap.
            previous = signal.signal(signal.SIGTERM, interrupted)
            child = None; completed = False
            try:
                child = subprocess.Popen(['/bin/bash', sys.argv[1], 'clean'], env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
                CLEANUP_STARTED = True
                workers_stopped = False
                while True:
                    status = child.poll()
                    if status is not None and status != 0 and not workers_stopped:
                        # Do not wait for inherited pipes to reach EOF while an
                        # orphaned Flow/cache child keeps mutating after Bash died.
                        stop_group(child)
                        workers_stopped = True
                    ready, _, _ = select.select([child.stdout], [], [], 0.2)
                    if not ready:
                        continue
                    data = os.read(child.stdout.fileno(), 4096)
                    if not data:
                        break
                    emit(data)
                code = child.wait()
                if code < 0:
                    code = 128 - code  # wait() -SIGTERM -> shell-compatible 143
                emit(('[%s] END cleanup exit=%d\n' % (time.strftime('%Y-%m-%d %H:%M:%S %z'), code)).encode())
                os.fsync(fd)
                completed = True
                report_status(code)
                return code
            finally:
                # Prevent another TERM from interrupting descriptor/group cleanup.
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                try:
                    if child is not None:
                        if not completed:
                            stop_group(child)
                        child.stdout.close()
                finally:
                    signal.signal(signal.SIGTERM, previous)
        finally:
            os.close(fd)
    finally:
        os.close(lock)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, CleanupInterrupted) as exc:
        try:
            report_status(128 + exc.signum if isinstance(exc, CleanupInterrupted) else 1)
        except (OSError, ValueError):
            syslog.openlog('cyf-host-cleanup', syslog.LOG_PID, syslog.LOG_DAEMON)
            syslog.syslog(syslog.LOG_CRIT, 'cleanup failed and private status unavailable; inspect cleanup log')
        phase = 'cleanup started; workers stopped; inspect audit records' if CLEANUP_STARTED else 'no cleanup run'
        print('ERROR: persistent cleanup logging unavailable; %s: %s' % (phase, exc), file=sys.stderr)
        sys.exit(128 + exc.signum if isinstance(exc, CleanupInterrupted) else 1)
