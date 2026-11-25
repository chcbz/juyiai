"""Read-only verification for the unified Runtime's pre-start phase.

The expected values come from an independent operator-controlled activation pin,
never from current.json. The release owner must keep program paths stable through
start; this function does not acquire its caller's release lock or publish permits.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def verify(app, records, *, commit, tree, archive_sha, manifest_sha):
    app, records = Path(app), Path(records)
    for value, size in ((commit, 40), (tree, 40), (archive_sha, 64), (manifest_sha, 64)):
        require(re.fullmatch('[0-9a-f]{%d}' % size, value), 'invalid activation pin')
    for root in (app, records):
        require(root.is_absolute() and root.resolve(strict=True) == root, 'aliased release path')
        for directory in (root, *root.parents):
            st = directory.stat()
            require(stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022,
                    'untrusted release directory: ' + str(directory))
    def read_record(path):
        st = path.lstat()
        require(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022,
                'untrusted release metadata')
        return path.read_bytes()
    record = json.loads(read_record(records / 'current.json'))
    expected = dict(unit='cyf-agent-runtime-v1@unified.service', sourceKind='LOCAL',
                    rollbackPolicy='forward-only', sourceCommit=commit, sourceTree=tree,
                    artifactSha256=archive_sha, artifactManifestSha256=manifest_sha, artifactPath=str(app))
    require(all(record.get(k) == v for k, v in expected.items()), 'release binding mismatch')
    require(record.get('status') in ('installed-channel-verification-pending', 'verified-active'), 'not installed')
    mp = Path(record['artifactManifestPath']); require(mp.parent == records, 'foreign release manifest')
    raw = read_record(mp); require(hashlib.sha256(raw).hexdigest() == manifest_sha, 'manifest binding mismatch')
    rows = json.loads(raw); require(isinstance(rows, list) and rows, 'empty installation manifest')
    pending = {r['path']: r for r in rows}; require(len(pending) == len(rows), 'duplicate installation entry')
    stack = [app]; count = 0
    while stack:
        for p in stack.pop().iterdir():
            rel = str(p.relative_to(app)); st = p.lstat(); mode = st.st_mode
            row = dict(path=rel, mode=oct(stat.S_IMODE(mode)), uid=st.st_uid, gid=st.st_gid)
            require(st.st_uid == 0 and (stat.S_ISLNK(mode) or not mode & 0o022),
                    'mutable program entry: ' + rel)
            if stat.S_ISDIR(mode):
                row.update(type='directory'); stack.append(p)
            elif stat.S_ISREG(mode):
                with p.open('rb') as stream:
                    row.update(type='file', sha256=hashlib.file_digest(stream, 'sha256').hexdigest())
            elif stat.S_ISLNK(mode):
                require(p.resolve(strict=True).is_relative_to(app), 'external program link')
                row.update(type='symlink', target=os.readlink(p))
            else:
                raise ValueError('unsupported program entry')
            require(row == pending.pop(rel, None), 'installation entry mismatch: ' + rel); count += 1
    require(not pending, 'missing installation entry'); return count
