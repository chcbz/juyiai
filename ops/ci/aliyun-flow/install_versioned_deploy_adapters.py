#!/usr/bin/env python3
"""Flow-only, fixed-target deployment-adapter verification and reversible install."""
import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

TARGETS = {'api': Path('/usr/local/sbin/cyf-api-flow-deploy'),
           'web': Path('/usr/local/sbin/cyf-web-flow-deploy')}
LOCKS = [Path('/tmp/cyf-api-flow-auto-approval-v2.lock'),
         Path('/home/isp/state/cyf-web-flow/deploy.lock')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
        raise RuntimeError('unsafe private adapter work directory')


def read_target(path):
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0
                or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o755):
            raise RuntimeError('unsafe adapter target: '+str(path))
        with os.fdopen(fd,'rb') as handle:
            fd=None;data=handle.read()
        return data
    finally:
        if fd is not None:os.close(fd)


def atomic(path,data,mode):
    fd,name=tempfile.mkstemp(prefix='.adapter-',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as handle:
            os.fchmod(handle.fileno(),mode);handle.write(data);handle.flush();os.fsync(handle.fileno())
        os.replace(name,str(path))
        directory=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--payload',required=True);parser.add_argument('--payload-sha256',required=True)
    parser.add_argument('--root',required=True);parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    if os.geteuid()!=0 or os.environ.get('PIPELINE_ID')!='5264702':
        raise RuntimeError('authorized ops Flow identity required')
    run=os.environ.get('BUILD_NUMBER','')
    if not run.isdigit() or int(run)<=0:raise RuntimeError('invalid ops Run')
    raw=Path(args.payload).read_bytes()
    if digest(raw)!=args.payload_sha256:raise RuntimeError('payload digest mismatch')
    payload=json.loads(raw.decode())
    if {r['component'] for r in payload['records']}!=set(TARGETS) or len(payload['records'])!=2:
        raise RuntimeError('expected exactly two fixed-target adapters')
    work=Path(args.root);safe_directory(work)
    fixtures=Path(tempfile.mkdtemp(prefix='verify-run-'+run+'-',dir=str(work)))
    candidates=[]
    for record in payload['records']:
        target=TARGETS[record['component']]
        if record['path']!=str(target):raise RuntimeError('foreign install target')
        content=base64.b64decode(record['content_base64'],validate=True)
        if digest(content)!=record['candidate_sha256']:raise RuntimeError('candidate digest mismatch')
        compile(content.decode(),str(target),'exec')
        candidate=fixtures/target.name;candidate.write_bytes(content);candidate.chmod(0o755)
        candidates.append((record,target,content))
    tests=base64.b64decode(payload['test_base64'],validate=True)
    if digest(tests)!=payload['test_sha256']:raise RuntimeError('test digest mismatch')
    test_path=fixtures/'test_versioned_deploy_adapters.py';test_path.write_bytes(tests)
    environment=dict(os.environ,CYF_ADAPTER_TEST_ROOT=str(fixtures))
    subprocess.check_call([sys.executable,str(test_path)],env=environment)
    if not args.install:
        print('CYF_VERSIONED_ADAPTERS=VERIFIED_ONLY',flush=True);return
    state={'pipeline_id':'5264702','run_id':run,'payload_sha256':args.payload_sha256,
           'status':'installing','targets':[]}
    report=work/('installation-run-'+run+'.json')
    with contextlib.ExitStack() as stack:
        for path in LOCKS:
            fd=os.open(str(path),os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
            stack.callback(os.close,fd)
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o077:
                raise RuntimeError('unsafe deployment mutex')
            fcntl.flock(fd,fcntl.LOCK_EX)  # wait, never preempt another owner
        # Validate both predecessors before the first write; save byte-exact backups.
        for record,target,content in candidates:
            old=read_target(target)
            if digest(old)!=record['previous_sha256']:raise RuntimeError('adapter changed; coordinate before install')
            backup=work/(target.name+'.before-run-'+run)
            if backup.exists():raise RuntimeError('preserve existing Run backup; no blind retry')
            backup.write_bytes(old);backup.chmod(0o600)
            with backup.open('rb') as handle:os.fsync(handle.fileno())
            state['targets'].append(dict(path=str(target),previous_sha256=digest(old),
                candidate_sha256=record['candidate_sha256'],backup=str(backup),status='backed_up'))
        atomic(report,(json.dumps(state,sort_keys=True)+'\n').encode(),0o600)
        for (record,target,content),item in zip(candidates,state['targets']):
            if digest(read_target(target))!=record['previous_sha256']:
                raise RuntimeError('adapter changed before atomic replacement')
            atomic(target,content,0o755)
            if digest(read_target(target))!=record['candidate_sha256']:raise RuntimeError('installed digest mismatch')
            item['status']='installed_verified'
            atomic(report,(json.dumps(state,sort_keys=True)+'\n').encode(),0o600)
        state['status']='installed_verified'
        atomic(report,(json.dumps(state,sort_keys=True)+'\n').encode(),0o600)
    print('CYF_VERSIONED_ADAPTERS=INSTALLED_VERIFIED '+json.dumps(state,sort_keys=True),flush=True)


if __name__=='__main__':main()
