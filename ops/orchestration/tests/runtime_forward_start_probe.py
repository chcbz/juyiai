"""Offline D179 activation rehearsal. Run ONLY on a build worker, never install a unit.

Pin the portable build manifest outside the app; host dependencies and installation
CAS are NOT represented by this fixture. ExecStartPre uses the trusted interpreter,
not the candidate's node, shell or validate.sh.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

ARCHIVE = 'e58c644e175086671a81884fed9020ec360d7ca9f6fc0711a3292cfebb4ab911'
MANIFEST = '9612f4a154c77ddbed127653dbdfce76d93079cf95d5c7c9ef35a72123695101'


def check(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root, manifest):
    data = manifest.read_bytes()
    check(hashlib.sha256(data).hexdigest() == MANIFEST, 'manifest binding')
    check(stat.S_ISDIR(root.lstat().st_mode), 'physical program root required')
    entries = []
    for p in sorted(root.rglob('*')):
        mode = p.lstat().st_mode
        row = dict(path=str(p.relative_to(root)), mode=oct(stat.S_IMODE(mode)))
        if stat.S_ISREG(mode):
            row.update(type='file', sha256=digest(p))
        else:
            check(stat.S_ISDIR(mode), 'unexpected link or special entry')
            row.update(type='directory')
        entries.append(row)
    check(entries == json.loads(data), 'program manifest mismatch')


def exercise(pkg, scratch):
    archive = pkg / 'runtime-code-1.3.118.tgz'
    manifest = pkg / 'artifact.manifest.json'
    check(digest(archive) == ARCHIVE, 'archive binding')
    with tempfile.TemporaryDirectory(dir=scratch, prefix='rb-start-') as tmp:
        base = Path(tmp); app = base / 'app'; app.mkdir()
        subprocess.run(['tar', '-xzpf', archive, '-C', app], check=True)
        verify(app, manifest)
        permit = base / ('allowed-' + ARCHIVE); events = base / 'started'
        def attempt(label, expected):
            unit = f'cyf-{base.name}-{label}'
            cmd = ['systemd-run', '--quiet', '--wait', '--collect', '--unit', unit,
                   '-p', 'Type=oneshot', '-p', f'ConditionPathExists={permit}',
                   '-p', f'ExecStartPre=/usr/bin/python3 {Path(__file__).resolve()} check {app} {manifest}',
                   '/usr/bin/touch', str(events)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            check(events.exists() == (expected == 'started'), (label, result.stderr))
            if expected == 'rejected':
                journal = subprocess.check_output(['journalctl', '-u', unit, '--no-pager', '-o', 'cat'], text=True)
                check(result.returncode != 0 and 'ValueError:' in journal, (label, journal))
            elif expected == 'started':
                check(result.returncode == 0, result.stderr); events.unlink()
            else:
                journal = subprocess.check_output(['journalctl', '-u', unit, '--no-pager', '-o', 'cat'], text=True)
                check('condition' in journal.lower(), (label, journal))
            print(label, expected, flush=True)
        attempt('no-permit', 'skipped'); permit.touch(); attempt('authorized', 'started')
        program = app / 'runtime/agent-runtime.mjs'; original = program.read_bytes()
        program.write_bytes(original + b'\n// incompatible reader fixture\n'); attempt('donor', 'rejected')
        program.write_bytes(original); mode = program.stat().st_mode; program.chmod(mode ^ 0o100)
        attempt('wrong-mode', 'rejected'); program.chmod(mode)
        saved = base / 'saved'; app.rename(saved); app.symlink_to(saved, target_is_directory=True)
        attempt('linked-root', 'rejected'); app.unlink(); saved.rename(app)
        attempt('forward-repair', 'started')


if __name__ == '__main__':
    op, first, second = sys.argv[1:]
    if op == 'check':
        verify(Path(first), Path(second))
    elif op == 'exercise' and os.geteuid() == 0:
        exercise(Path(first), Path(second))
    else:
        raise SystemExit('expected check or root worker exercise')
