"""Worker integration: original installer manifest shape, D179 code and real node."""
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_start_admission import verify


class Admission(unittest.TestCase):
    @unittest.skipUnless('CYF_TEST_RUNTIME_ARCHIVE' in os.environ, 'requires explicit worker fixture')
    def test_full_candidate(self):
        package = Path(os.environ['CYF_TEST_RUNTIME_ARCHIVE']); sha = 'e58c644e175086671a81884fed9020ec360d7ca9f6fc0711a3292cfebb4ab911'
        self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(), sha)
        with tempfile.TemporaryDirectory(dir=os.environ['CYF_TEST_SCRATCH']) as d:
            app = Path(d) / 'app'; records = app.parent / 'records'; app.mkdir(); records.mkdir()
            subprocess.run(['tar', '-xzpf', package, '-C', app], check=True)
            node = app / 'node/bin/node'; node.parent.mkdir(parents=True)
            shutil.copy2(os.environ['CYF_TEST_NODE'], node); link = app / 'node/current'; link.symlink_to('bin/node')
            rows = []
            for p in sorted(app.rglob('*')):
                s = p.lstat(); row = dict(path=str(p.relative_to(app)), uid=s.st_uid, gid=s.st_gid, mode=oct(stat.S_IMODE(s.st_mode)))
                if p.is_symlink(): row.update(type='symlink', target=os.readlink(p))
                elif p.is_dir(): row.update(type='directory')
                else:
                    with p.open('rb') as f: row.update(type='file', sha256=hashlib.file_digest(f, 'sha256').hexdigest())
                rows.append(row)
            mp = records / 'candidate.manifest.json'; mp.write_text(json.dumps(rows)); m = hashlib.sha256(mp.read_bytes()).hexdigest()
            args = dict(commit='6d152d8697c82b93f542e9e5cdbc30b5198db034', tree='568e897569b482e782fba2bb953c160904241d67', archive_sha=sha, manifest_sha=m)
            record = dict(sourceCommit=args['commit'], sourceTree=args['tree'], sourceKind='LOCAL', rollbackPolicy='forward-only', unit='cyf-agent-runtime-v1@unified.service', artifactPath=str(app), artifactSha256=sha, artifactManifestSha256=m, artifactManifestPath=str(mp), status='installed-channel-verification-pending'); current = records / 'current.json'; current.write_text(json.dumps(record))
            t = time.monotonic(); self.assertEqual(verify(app, records, **args), len(rows)); print('entries', len(rows), 'nodeBytes', node.stat().st_size, 'verifySeconds', round(time.monotonic()-t, 3))
            Path(d).chmod(0o772)
            with self.assertRaisesRegex(ValueError, 'untrusted release directory'): verify(app, records, **args)
            Path(d).chmod(0o700)
            with node.open('ab') as f: f.write(b'x')
            with self.assertRaisesRegex(ValueError, 'entry mismatch'): verify(app, records, **args)
            with node.open('r+b') as f: f.truncate(node.stat().st_size - 1)
            link.unlink(); link.symlink_to(mp)
            with self.assertRaisesRegex(ValueError, 'external program link'): verify(app, records, **args)
            link.unlink(); link.symlink_to('bin/node'); current.write_text(json.dumps(dict(record, sourceTree='0'*40)))
            with self.assertRaisesRegex(ValueError, 'release binding'): verify(app, records, **args)
            current.write_text(json.dumps(record)); self.assertEqual(verify(app, records, **args), len(rows))

            if os.environ.get('CYF_TEST_PROGRAM_VIEW'):
                exercise_view(Path(d), app, records, args, record, current)


def exercise_view(base, app, records, pins, record, current):
    apps = base / 'apps'; apps.mkdir(mode=0o755); instance = apps / 'runtime'
    instance.mkdir(); app.rename(instance / 'app'); records.rename(instance / 'records')
    app = instance / 'app'; records = instance / 'records'
    record.update(artifactPath=str(app), artifactManifestPath=str(records / 'candidate.manifest.json'))
    (records / current.name).write_text(json.dumps(record))
    skeleton = base / 'view'; (skeleton / 'runtime').mkdir(parents=True)
    apps.chmod(0o777); original = instance.stat(); ns = os.stat('/proc/self/ns/mnt')
    data = json.dumps([str(instance), str(skeleton), original.st_dev, original.st_ino, ns.st_dev, ns.st_ino, pins])
    # Parent acts only after child has admitted the complete installation. Its old path is then replaced.
    with subprocess.Popen(['unshare', '--mount', '--propagation', 'private', sys.executable, __file__, 'child', data],
                          text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as child:
        if not select.select([child.stdout], [], [], 20)[0]:
            child.kill(); raise RuntimeError('no admission response')
        if child.stdout.readline().strip() != 'admitted': raise RuntimeError('child did not admit candidate')
        parked = apps / 'parked'; instance.rename(parked); instance.mkdir()
        child.stdin.write('continue\n'); child.stdin.flush()
        output, _ = child.communicate(timeout=30)
        if child.returncode or 'ENOENT' not in output or 'node_modules/@imagemagick/magick-wasm/package.json' not in output: raise RuntimeError('private validator probe: ' + output)
        if not (parked / 'state-proof').is_file() or (instance / 'state-proof').exists():
            raise RuntimeError('wrong instance state')
        print('canonical paths survived outer rename; original validator refused incomplete fixture', flush=True)


def child_view(raw):
    from runtime_program_view import protect_instance
    inst, skeleton, dev, ino, nsdev, nsino, pins = json.loads(raw); inst = Path(inst)
    try:
        protect_instance(inst, skeleton, device=dev, inode=ino + 1, parent_ns=(nsdev, nsino))
    except ValueError as exc:
        if str(exc) != 'instance identity changed': raise
    else:
        raise ValueError('wrong instance was accepted')
    protect_instance(inst, skeleton, device=dev, inode=ino, parent_ns=(nsdev, nsino))
    app = inst / 'app'; verify(app, inst / 'records', **pins)
    os.chdir(app)
    print('admitted', flush=True)
    if input() != 'continue': raise ValueError('unexpected sync')
    verify(app, inst / 'records', **pins)
    (inst / 'state-proof').touch(exist_ok=False)
    v = subprocess.run(['/bin/bash', app / 'runtime/validate.sh', '--root', app], capture_output=True, text=True)
    if not v.returncode or 'Runtime Node version:' not in v.stdout:
        raise ValueError('expected real validator to stop on missing host closure')
    print(v.stderr, flush=True)


if __name__ == '__main__':
    if sys.argv[1:2] == ['child']: child_view(sys.argv[2])
    else: unittest.main()
