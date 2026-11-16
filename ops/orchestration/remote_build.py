"""SSH transport for the existing LOCAL builders; never installs production.

Only the configured build host is contacted. Sources are exact shallow Git
snapshots, not working-directory copies. Build deadlines live on the worker,
not around SSH or a production transaction. No synthetic CI/Flow identity.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import time
import subprocess
import sys
import tarfile
import tempfile

from build_storage import require_disk


def canonical_directory(path):
    path = Path(path)
    if not path.is_absolute() or path != path.resolve():
        raise ValueError('remote build paths must be physical absolute paths')
    require_disk(path)
    return path


def safe_extract(archive, target):
    """Receive only a build-owned tree; Python's data filter checks link escapes."""
    with tarfile.open(archive) as bundle:
        bundle.extractall(target, filter='data')


class RemoteBuild:
    def __init__(self, host, root, local_root, evidence, known_hosts, auth_file):
        self.host = host
        self.root = Path(root)
        if (not self.root.is_absolute() or '..' in self.root.parts or
                not str(self.root).startswith('/home/isp/wsps/cyf-build/')):
            raise ValueError('remote source root must be below /home/isp/wsps/cyf-build')
        self.local_root = Path(local_root)
        self.evidence = canonical_directory(evidence)
        self.evidence.mkdir(mode=0o700, parents=True)
        self.auth_file = Path(auth_file)
        auth = json.loads(self.auth_file.read_text())
        if host != auth['JYT_BUILD_SERVER'] or not re.fullmatch(r'[A-Za-z0-9.-]+', host):
            raise ValueError('build host must match the explicitly configured server')
        login = auth['JYT_BUILD_LOGIN']
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', login):
            raise ValueError('invalid build login')
        known_hosts = Path(known_hosts)
        if not known_hosts.is_file():
            raise ValueError('verify and provision the worker SSH host key first')
        self.ssh = ['ssh', '-o', 'ConnectTimeout=20', '-o', 'StrictHostKeyChecking=yes',
                    '-o', 'UserKnownHostsFile=' + str(known_hosts), '-o', 'NumberOfPasswordPrompts=1',
                    login + '@' + host]
        self.receipt = {'format': 'cyf-local-remote-build-transport-v1', 'host': host,
                        'root': str(self.root), 'sourceKind': 'LOCAL', 'sources': {}, 'transfers': []}
        self.askpass = self.evidence / 'askpass.py'
        with self.askpass.open('x') as stream:
            stream.write('#!' + sys.executable + '\nimport json\nprint(json.load(open(' +
                         repr(str(self.auth_file)) + '))["JYT_BUILD_PASSWORD"])\n')
        self.askpass.chmod(0o700)

    def close(self):
        self.askpass.unlink(missing_ok=True)

    def save(self):
        target = self.evidence / 'transport.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.receipt, indent=2) + '\n')
        os.replace(temporary, target)

    def environment(self):
        return dict(os.environ, SSH_ASKPASS=str(self.askpass), SSH_ASKPASS_REQUIRE='force', DISPLAY=':0')

    def command(self, argv):
        return self.ssh + [shlex.join(list(map(str, argv)))]

    def call(self, argv, **kwargs):
        return subprocess.run(self.command(argv), env=self.environment(), check=True, **kwargs)

    def output(self, argv):
        return self.call(argv, stdout=subprocess.PIPE, text=True).stdout.strip()

    def upload(self, archive, directory):
        # Receiver extracts only after transport bytes match; no stdout secrets.
        digest = hashlib.sha256()
        with Path(archive).open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        digest = digest.hexdigest()
        code = '''import hashlib,pathlib,sys,tarfile,os
p=pathlib.Path(sys.argv[1]); p.mkdir(mode=0o700,parents=True,exist_ok=False)
a=p/'.transfer.tar'
with a.open('xb') as out:
 h=hashlib.sha256()
 while b:=sys.stdin.buffer.read(1048576):out.write(b);h.update(b)
assert h.hexdigest()==sys.argv[2], 'transfer digest mismatch'
with tarfile.open(a) as tf:tf.extractall(p,filter='data')
a.unlink()
'''
        with Path(archive).open('rb') as stream:
            self.call(['python3', '-c', code, str(directory), digest], stdin=stream)
        self.receipt['transfers'].append({'direction': 'upload', 'destination': str(directory),
            'sha256': digest, 'size': Path(archive).stat().st_size})
        self.save()

    def prepare(self, sources, ledger_path):
        """Stage one snapshot per candidate; never include dirty working bytes."""
        for name, source in sources.items():
            source = Path(source)
            expected = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            bare = self.evidence / (name + '.git')
            subprocess.run(['git', 'clone', '--quiet', '--bare', '--depth=1', '--no-local',
                            str(source), str(bare)], check=True)
            actual = subprocess.check_output(['git', '--git-dir=' + str(bare), 'rev-parse', 'HEAD'], text=True).strip()
            if actual != expected:
                raise ValueError('source HEAD changed while staging ' + name)
            archive = self.evidence / (name + '-source.tar')
            with tarfile.open(archive, 'w') as bundle:
                bundle.add(bare, arcname='repository.git')
            remote_stage = self.root / (name + '-snapshot')
            self.upload(archive, remote_stage)
            destination = self.root / name
            self.call(['git', 'clone', '--quiet', '--no-hardlinks', str(remote_stage / 'repository.git'), str(destination)])
            identity = json.loads(self.output(['python3', '-c',
                'import subprocess,json,sys; p=sys.argv[1]; g=lambda *a:subprocess.check_output(["git","-C",p,*a],text=True).strip(); '
                'assert not g("status","--porcelain");print(json.dumps({"commit":g("rev-parse","HEAD"),"tree":g("rev-parse","HEAD^{tree}")}))', str(destination)]))
            if identity['commit'] != expected:
                raise ValueError('remote source mismatch')
            self.receipt['sources'][name] = dict(identity, path=str(destination))
            self.save()
        # Copy the real current task ledger (including its Owner/state), not an
        # invented CI context. Worker writes never replace the controller ledger.
        with Path(ledger_path).open('rb') as stream:
            self.call(['python3', '-c',
                'import pathlib,sys; p=pathlib.Path(sys.argv[1]); p.write_bytes(sys.stdin.buffer.read());p.chmod(0o600)',
                str(self.root / 'controller/docs/implementation/TASKS.yaml')], stdin=stream)
        code = ('import pathlib,sys; ps=list(map(pathlib.Path,sys.argv[1:])); '
                'assert all(p.is_absolute() and p.resolve()==p for p in ps); '
                'import subprocess; '
                'assert all(subprocess.check_output(["stat","-f","-c","%T",str(p)],text=True).strip() not in ("tmpfs","ramfs") for p in ps)')
        self.call(['python3', '-c', code, str(self.root), '/home/isp/state/cyf-local-build'])
        self.save()

    def build_command(self, command, unit, budget, api_source, web_source, runtime_source=None):
        mapped = []
        for value in command:
            if runtime_source is not None and str(value) == str(runtime_source):
                value = str(self.root / 'runtime')
            elif str(value) == str(api_source):
                value = str(self.root / 'api')
            elif str(value) == str(web_source):
                value = str(self.root / 'web')
            elif str(value).startswith(str(self.local_root) + '/ops/'):
                value = str(self.root / 'controller') + str(value)[len(str(self.local_root)):]
            mapped.append(str(value))
        mapped[0] = '/usr/bin/python3'
        # Credentials are read only by the remote build process, never in argv,
        # controller logs, source snapshots, receipts or archive transfers.
        environment_file = 'maven.env' if any(v.endswith('/local_build.py') for v in mapped) else 'web.env'
        credentials = '' if any(v.endswith('/runtime_build.py') for v in mapped) else 'set -a; source /home/isp/conf/cyf-build/' + environment_file + '; set +a; '
        script = ('set -euo pipefail; ' + credentials + 'exec ' +
                  shlex.join(['/home/isp/bin/cyf-build-env'] + mapped))
        return self.command(['systemd-run', '--quiet', '--wait', '--pipe', '--collect',
            '--unit=' + unit, '--property=RuntimeMaxSec=' + str(int(budget)),
            '--property=KillMode=control-group', '/bin/bash', '-c', script])

    def transfer_basis(self, component):
        """An optional byte-only rsync basis, never build/test evidence."""
        if component == 'api':
            path = Path('/home/isp/hosts/cyf/api/cyf-api-kit.jar')
        elif component == 'web':
            try:
                record = json.loads(Path('/home/isp/state/cyf-web-flow/record.json').read_text())
                path = Path(record['package']['path'])
            except (OSError, KeyError, ValueError):
                return None
        elif component == 'runtime':
            return None  # Portable code is small; no production identity/dependency bytes.
        else:
            raise ValueError('unknown build component')
        return path if path.is_absolute() and path.is_file() and not path.is_symlink() else None

    def download(self, source, archive, timeout):
        """SSH-pinned block delta; receiver reconstructs the original tar bytes."""
        command = ['rsync', '--archive', '--no-whole-file', '--stats',
                   '--rsh=' + shlex.join(self.ssh[:-1]),
                   self.ssh[-1] + ':' + str(source), str(archive)]
        completed = subprocess.run(command, env=self.environment(), check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, timeout=timeout)
        (self.evidence / (archive.stem + '-rsync.log')).write_text(completed.stdout)

    def collect(self, component, output, timeout=600):
        """Original package/XML/logs only; budget includes archive and transfer."""
        output = Path(output)
        if output.exists():
            raise ValueError('do not overwrite an existing received build')
        started = time.monotonic()
        def remaining():
            value = timeout - (time.monotonic() - started)
            if value <= 0:
                raise TimeoutError('build transfer budget exhausted')
            return value
        archive = self.evidence / (component + '-output.tar')
        if archive.exists():
            raise ValueError('do not overwrite an existing transport archive')
        remote_archive = output.parent / ('.' + output.name + '-' + component + '-transport.tar')
        code = '''import pathlib,tarfile,sys,hashlib,json
p=pathlib.Path(sys.argv[1]); a=pathlib.Path(sys.argv[2]); assert p.is_dir()
with a.open('xb') as raw, tarfile.open(fileobj=raw,mode='w|') as tf:
 for f in sorted(p.rglob('*')):
  if sys.argv[3]=='runtime' and str(f.relative_to(p)).startswith('build/'):continue
  if f.is_file() and not f.is_symlink() and (not str(f.relative_to(p)).startswith('build/') or f.suffix in ('.json','.xml','.log')):
   tf.add(f,arcname=str(f.relative_to(p)),recursive=False)
h=hashlib.sha256()
with a.open('rb') as stream:
 while b:=stream.read(1048576):h.update(b)
print(json.dumps({'sha256':h.hexdigest(),'size':a.stat().st_size}))
'''
        expected = json.loads(self.call(['python3', '-c', code, str(output), str(remote_archive), component],
                              stdout=subprocess.PIPE, text=True, timeout=remaining()).stdout)
        basis = self.transfer_basis(component)
        if basis is not None:
            shutil.copyfile(basis, archive)
        self.download(remote_archive, archive, remaining())
        digest = hashlib.sha256()
        with archive.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        if digest.hexdigest() != expected['sha256'] or archive.stat().st_size != expected['size']:
            raise ValueError('received archive digest/size mismatch')
        remaining()
        output.mkdir(mode=0o700, parents=True)
        safe_extract(archive, output)
        remaining()
        self.receipt['transfers'].append({'direction': 'download', 'component': component,
            'sha256': digest.hexdigest(), 'size': archive.stat().st_size,
            'algorithm': 'rsync-block-delta', 'basis': str(basis) if basis else None})
        self.save()
        self.call(['python3', '-c', 'import pathlib,sys;pathlib.Path(sys.argv[1]).unlink()',
                   str(remote_archive)], timeout=remaining())
