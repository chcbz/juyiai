"""Local build storage policy: keep generated files off memory filesystems."""
import os
from pathlib import Path
import shlex
import subprocess


def require_disk(path):
    """Check the actual filesystem, including symlinks/bind mounts and new paths."""
    ancestor = Path(path).resolve()
    while not ancestor.exists():
        ancestor = ancestor.parent
    kind = subprocess.check_output(
        ['stat', '-f', '-c', '%T', '--', str(ancestor)],
        universal_newlines=True).strip()
    if kind in ('tmpfs', 'ramfs'):
        raise ValueError('local build storage must not use {}: {}'.format(kind, path))


def build_environment(output, inherited=None):
    """Use batch-owned disk scratch instead of inherited /tmp or TMPDIR."""
    scratch = Path(output) / 'tmp'
    require_disk(scratch)
    scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
    env = dict(os.environ if inherited is None else inherited)
    for key in ('TMPDIR', 'TMP', 'TEMP'):
        env[key] = str(scratch)
    # Java does not use TMPDIR on Linux; retain unrelated caller options.
    options = shlex.split(env.get('JAVA_TOOL_OPTIONS', ''))
    options = [v for v in options if not v.startswith('-Djava.io.tmpdir=')]
    options.append('-Djava.io.tmpdir=' + str(scratch))
    env['JAVA_TOOL_OPTIONS'] = ' '.join(shlex.quote(v) for v in options)
    return env
