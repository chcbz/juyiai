#!/usr/bin/python3
"""Read-only FD/cwd/exe/mapping metadata. Never read command arguments or file data.

Permission and malformed-map errors fail closed. Vanished processes/FDs are normal.
The CLI emits a complete NUL-framed snapshot, followed by a success marker, only
AFTER the entire scan succeeds; a shell process-substitution exit cannot hide errors.
"""
import argparse
import os
from pathlib import Path
import re
import stat
import sys

MARKER = '__CYF_PROCESS_SNAPSHOT_COMPLETE__'

def path_name(value):
    if value.endswith(' (deleted)'):
        value = value[:-10]
    return value if value.startswith('/') else None

class Usage:
    def __init__(self):
        self.paths = set()
        self.inodes = set()
        self.processes = 0
    def used(self, path):
        path = Path(path)
        st = path.stat()
        if (st.st_dev, st.st_ino) in self.inodes:
            return True
        name = str(path)
        return any(p == name or p.startswith(name.rstrip('/') + '/') for p in self.paths)

def snapshot(root=Path('/proc')):
    usage = Usage()
    for process in root.iterdir():
        if not process.name.isdigit():
            continue
        try:
            if not process.is_dir():
                continue
            usage.processes += 1
            for name in ('cwd', 'exe'):
                try:
                    target = path_name(os.readlink(str(process / name)))
                    if target:
                        usage.paths.add(target)
                except (FileNotFoundError, ProcessLookupError):
                    pass
            try:
                for fd in (process / 'fd').iterdir():
                    try:
                        target = path_name(os.readlink(str(fd)))
                        st = fd.stat()
                        if target:
                            usage.paths.add(target)
                        if stat.S_ISREG(st.st_mode):
                            usage.inodes.add((st.st_dev, st.st_ino))
                    except (FileNotFoundError, ProcessLookupError):
                        pass
            except (FileNotFoundError, ProcessLookupError):
                pass
            try:
                maps = (process / 'maps').read_text(errors='surrogateescape')
                for line in maps.splitlines():
                    fields = line.split(None, 5)
                    if len(fields) < 5:
                        raise ValueError('malformed process mapping metadata')
                    inode = int(fields[4])
                    if not inode:
                        continue  # anonymous mappings, vdso, etc.
                    major, minor = fields[3].split(':')
                    usage.inodes.add((os.makedev(int(major, 16), int(minor, 16)), inode))
                    if len(fields) == 6:
                        target = path_name(re.sub(r'\\([0-7]{3})',
                            lambda m: chr(int(m.group(1), 8)), fields[5]))
                        if target:
                            usage.paths.add(target)
            except (FileNotFoundError, ProcessLookupError):
                pass
        except (FileNotFoundError, ProcessLookupError):
            pass
    if not usage.processes:
        raise ValueError('no visible processes; refusing an empty usage snapshot')
    return usage

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proc-root', type=Path, default=Path('/proc'))
    args = parser.parse_args()
    try:
        usage = snapshot(args.proc_root)
        records = sorted(usage.paths) + ['@inode:%d:%d' % k for k in sorted(usage.inodes)] + [MARKER]
        sys.stdout.buffer.write(('\x00'.join(records) + '\x00').encode('utf-8', 'surrogateescape'))
        sys.stdout.buffer.flush()
        return 0
    except (OSError, ValueError) as exc:
        # No raw args, environment, map contents, or application data in errors.
        print('WARNING: incomplete process snapshot; preserve candidates: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
