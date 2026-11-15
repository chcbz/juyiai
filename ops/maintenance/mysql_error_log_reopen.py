#!/usr/bin/python3
"""Reopen only this host's MySQL text logs; never flush binlogs or restart it."""
import argparse
import os
from pathlib import Path
import pwd
import re
import signal
import subprocess
import sys
import time

PID_FILE = Path('/home/isp/apps/mysql/mysql.pid')
EXE = '/home/isp/apps/mysql/bin/mysqld'
CONFIG_ARG = b'--defaults-file=/home/isp/apps/mysql/my.cnf'
LOG = Path('/home/isp/logs/mysql.log')
PROC = Path('/proc')


def identity():
    if PID_FILE.is_symlink():
        raise ValueError('symlink PID file')
    pid = int(PID_FILE.read_text().strip())
    if pid <= 1:
        raise ValueError('invalid server PID')
    process = PROC / str(pid)
    if os.readlink(str(process / 'exe')) != EXE:
        raise ValueError('PID is not the configured mysqld server')
    if process.stat().st_uid != pwd.getpwnam('mysql').pw_uid:
        raise ValueError('unexpected server identity')
    if CONFIG_ARG not in (process / 'cmdline').read_bytes().split(b'\0'):
        raise ValueError('wrong server configuration')
    groups = (process / 'cgroup').read_text().splitlines()
    if not any(g.endswith(':/system.slice/mysql.service') for g in groups):
        raise ValueError('server is not in mysql.service')
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return pid, fields[19]  # kernel starttime, not the wrapper's MainPID


def log_open(pid):
    if LOG.is_symlink() or not LOG.is_file():
        raise ValueError('missing or unsafe active error log')
    target = LOG.stat()
    if target.st_nlink != 1 or target.st_uid != pwd.getpwnam('mysql').pw_uid:
        raise ValueError('unexpected active log owner or hardlink')
    for fd in (PROC / str(pid) / 'fd').iterdir():
        try:
            st = fd.stat()
        except FileNotFoundError:
            continue
        if (st.st_dev, st.st_ino) == (target.st_dev, target.st_ino):
            return True
    return False


def run(mode):
    server = identity()
    # SIGUSR1 gained text-log-only semantics in MySQL 8.0.19. SIG HUP and
    # mysqladmin flush-logs are intentionally NOT used (they also rotate binlogs).
    version = subprocess.check_output([str(PROC / str(server[0]) / 'exe'), '--version'])
    match = re.search(rb'\bVer (\d+)\.(\d+)\.(\d+)\b', version)
    if not match or tuple(int(n) for n in match.groups()) < (8, 0, 19):
        raise ValueError('text-log-only signal is not supported by this server')
    if mode == 'check':
        if not log_open(server[0]):
            raise ValueError('server is not writing the current log; preserve previous logs')
        return server[0]
    if identity() != server:
        raise ValueError('server changed before signal')
    os.kill(server[0], signal.SIGUSR1)
    # This bounds only the logrotate acknowledgement wait, never DB requests.
    # delaycompress leaves the rotated original intact if acknowledgement fails.
    until = time.monotonic() + 5
    while True:
        if identity() != server:
            raise ValueError('server changed while reopening logs')
        if log_open(server[0]):
            return server[0]
        if time.monotonic() >= until:
            raise ValueError('reopen not acknowledged; preserve uncompressed original')
        time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['check', 'reopen'])
    args = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise ValueError('root required')
        print('MySQL text-log %s verified; server PID %s' % (args.mode, run(args.mode)))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print('MySQL log rotation stopped safely: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
