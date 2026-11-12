"""CYF local Web installed-dependency sets; no production installation.

Published sets are mode-read-only, not a security sandbox against their owner/root.
Every reuse and completed build verifies the full installed tree. Never run npm in
an attached set. Dependency downloads still use npm's integrity-checked cache.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from build_storage import require_disk

FORMAT = 'cyf-web-dependencies-v1'
CI = ['ci', '--no-audit', '--no-fund', '--include=dev', '--include=optional',
      '--include=peer', '--ignore-scripts=false']
LIFECYCLE = {'preinstall', 'install', 'postinstall', 'prepare', 'prepublish',
             'preprepare', 'postprepare', 'dependencies'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def identity(source, env):
    source = Path(source)
    package = json.loads((source / 'package.json').read_text())
    lock = json.loads((source / 'package-lock.json').read_text())
    # Shared install must not depend on unkeyed source files or workspace links.
    if package.get('workspaces') or LIFECYCLE.intersection(package.get('scripts', {})):
        raise ValueError('shared Web dependencies do not support root lifecycle scripts/workspaces')
    if lock.get('lockfileVersion') not in (2, 3) or 'packages' not in lock:
        raise ValueError('shared Web dependencies require npm lockfile v2/v3')
    for name, entry in lock['packages'].items():
        if not name:
            continue
        resolved = entry.get('resolved', '')
        if entry.get('link') or not resolved.startswith(('https://', 'http://')) or not entry.get('integrity'):
            raise ValueError('shared Web dependencies require integrity-locked registry packages: ' + name)
    def out(argv):
        return subprocess.check_output(argv, cwd=str(source), env=env,
                                       universal_newlines=True).strip()
    runtime = json.loads(out(['node', '-p', 'JSON.stringify({version:process.version,abi:process.versions.modules,platform:process.platform,arch:process.arch,execPath:process.execPath})']))
    runtime['binarySha256'] = digest(runtime.pop('execPath'))
    config = json.loads(out(['npm', 'config', 'list', '--json']))
    # Storage/log destinations do not change the installed graph. All semantic
    # options (registry, peer/links/script/architecture policy, etc.) remain keyed.
    for field in ('cache', 'logs-dir', 'userconfig', 'globalconfig'):
        config.pop(field, None)
    return {
        'format': FORMAT, 'manifestSha256': digest(source / 'package.json'),
        'lockSha256': digest(source / 'package-lock.json'), 'node': runtime,
        'npmVersion': out(['npm', '--version']), 'install': CI,
        'npmConfigSha256': hashlib.sha256(encoded(config)).hexdigest(),
        'npmrcSha256': digest(source / '.npmrc') if (source / '.npmrc').exists() else None,
    }


def key_for(inputs):
    return hashlib.sha256(encoded(inputs)).hexdigest()


def inventory(root):
    """Include paths/content/modes; reject links escaping the installed set."""
    root = Path(root).resolve()
    result = {}
    def visit(folder):
        for p in sorted(folder.iterdir()):
            name = str(p.relative_to(root))
            mode = stat.S_IMODE(p.lstat().st_mode)
            if p.is_symlink():
                target = p.resolve()
                if root not in target.parents or not target.exists():
                    raise ValueError('external or broken dependency symlink: ' + name)
                result[name] = {'link': os.readlink(str(p))}
            elif p.is_dir():
                result[name] = {'directory': True, 'mode': mode}
                visit(p)
            elif p.is_file():
                result[name] = {'sha256': digest(p), 'size': p.stat().st_size, 'mode': mode}
            else:
                raise ValueError('unsupported dependency file: ' + name)
    visit(root)
    return result


def freeze(folder):
    for root, dirs, files in os.walk(str(folder), followlinks=False):
        for name in files:
            p = Path(root) / name
            if not p.is_symlink():
                p.chmod(0o555 if p.stat().st_mode & 0o111 else 0o444)
        for name in dirs:
            p = Path(root) / name
            if not p.is_symlink():
                p.chmod(0o555)
    Path(folder).chmod(0o555)


def verify(published, inputs):
    published = Path(published)
    if published.is_symlink():
        raise ValueError('published dependency set must be a physical directory')
    receipt = json.loads((published / 'receipt.json').read_text())
    if receipt['inputs'] != inputs or receipt['key'] != key_for(inputs):
        raise ValueError('dependency identity mismatch')
    modules = published / 'node_modules'
    if modules.is_symlink() or modules.stat().st_mode & 0o222:
        raise ValueError('dependency root is not read-only')
    actual = inventory(modules)
    if actual != receipt['files']:
        raise ValueError('dependency tree missing or changed; refuse reuse')
    if any(v.get('mode', 0) & 0o222 for v in actual.values()):
        raise ValueError('writable file in published dependency set')
    return receipt


def check_attachment(source, target):
    link = Path(source) / 'node_modules'
    if os.path.lexists(str(link)):
        if not link.is_symlink() or link.resolve() != target.resolve():
            raise ValueError('existing node_modules is not this dependency set; leave it untouched')


def attach(source, target):
    check_attachment(source, target)
    link = Path(source) / 'node_modules'
    if not os.path.lexists(str(link)):
        link.symlink_to(target, target_is_directory=True)


def discard_owned_staging(staging):
    # Only the unique directory returned by our own mkdtemp, never other batches.
    for root, dirs, files in os.walk(str(staging), followlinks=False):
        Path(root).chmod(0o700)
        for name in files:
            p = Path(root) / name
            if not p.is_symlink():
                p.chmod(0o600)
    shutil.rmtree(str(staging))


def ensure(source, store, env, log):
    source, store = Path(source).resolve(), Path(store)
    if not store.is_absolute() or store != store.resolve():
        raise ValueError('dependency store must be an absolute physical path')
    if source == store or source in store.parents or store in source.parents:
        raise ValueError('dependency store must be outside source')
    for forbidden in ('/home/isp/hosts', '/opt/cyf/service', '/home/isp/apps/cyf-agent-runtime-v1'):
        base = Path(forbidden).resolve()
        if store == base or base in store.parents:
            raise ValueError('dependency store must not be in production')
    require_disk(source)
    require_disk(store)
    cache = subprocess.check_output(['npm', 'config', 'get', 'cache'],
                                   cwd=str(source), env=env, universal_newlines=True).strip()
    require_disk(cache)
    inputs = identity(source, env)
    key = key_for(inputs)
    published = store / key
    check_attachment(source, published / 'node_modules')
    store.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (store / (key + '.lock')).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        reused = published.exists()
        if reused:
            verify(published, inputs)
        else:
            staging = Path(tempfile.mkdtemp(prefix='.' + key + '-', dir=str(store)))
            try:
                for name in ('package.json', 'package-lock.json', '.npmrc'):
                    if (source / name).exists():
                        shutil.copyfile(str(source / name), str(staging / name))
                if identity(staging, env) != inputs:
                    raise ValueError('staging npm configuration differs from keyed source configuration')
                subprocess.check_call(['npm'] + CI, cwd=str(staging), env=env,
                                      stdout=log, stderr=subprocess.STDOUT)
                # npm ci enforces manifest/lock consistency and registry integrity;
                # npm ls validates non-optional installed dependency relationships.
                subprocess.check_call(['npm', 'ls', '--all', '--include=dev', '--include=optional', '--include=peer', '--json'],
                                      cwd=str(staging), env=env, stdout=log, stderr=subprocess.STDOUT)
                if identity(source, env) != inputs:
                    raise ValueError('dependency inputs changed during install')
                for name in ('package.json', 'package-lock.json', '.npmrc'):
                    if (staging / name).exists():
                        (staging / name).unlink()
                freeze(staging / 'node_modules')
                receipt = {'key': key, 'inputs': inputs, 'files': inventory(staging / 'node_modules')}
                (staging / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True))
                freeze(staging)
                verify(staging, inputs)
                os.rename(str(staging), str(published))
            finally:
                if staging.exists():
                    discard_owned_staging(staging)
        attach(source, published / 'node_modules')
        return {'key': key, 'path': str(published), 'reused': reused,
                'receiptSha256': digest(published / 'receipt.json'), 'inputs': inputs}
