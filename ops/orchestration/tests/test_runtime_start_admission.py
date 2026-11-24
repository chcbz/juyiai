"""Worker integration: original installer manifest shape, D179 code and real node."""
import hashlib
import json
import os
from pathlib import Path
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


if __name__ == '__main__': unittest.main()
