"""Integration fixture only: replace the stopped donor, then exec the delivery peer
from a verified installed program. The session and usage body stay on stdin.
Never import the historical install script or use its production paths.
"""
import ast
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_activation_pin import ActivationPin
from runtime_start_admission import verify


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def need(ok, message):
    if not ok: raise RuntimeError(message)


def resume(root, peer, tmp):
    app=root/'instance/app'; stage=root/'candidate'; records=app.parent/'release-records'; backup=root/'backup'; task=root/'tx'
    need(root.resolve()==root and root.parent==Path('/home/isp/state/cyf-local-build') and root.name.startswith('rb-joint-'), 'expected isolated worker batch')
    need(sha(peer)=='6f332d640569cd3aa7872c54c91d18425046eca2e6843e733375a941927a5ce6','fixture source changed')
    ctl=root/'control'; ctl.mkdir(mode=0o700); app.mkdir(parents=True); records.mkdir(); backup.mkdir(); task.mkdir()
    (app/'donor-fixture').write_text('not admitted'); (records/'current.json').write_text('{}'); lock=ctl/'release.lock'
    manifest=root/'candidate.manifest.json'; pins=dict(commit='6d152d8697c82b93f542e9e5cdbc30b5198db034',tree='568e897569b482e782fba2bb953c160904241d67',archive_sha='e58c644e175086671a81884fed9020ec360d7ca9f6fc0711a3292cfebb4ab911',manifest_sha='8b014ec9b90850da016b239084b38cf3ad6e81a50725487708ea5fc4c2b02560')
    need(sha(manifest)==pins['manifest_sha'], 'candidate manifest changed')
    inbox=tmp/'cutover-inbox'
    def retained(): return {str(p.relative_to(inbox)):sha(p) for p in inbox.rglob('*') if p.is_file()}
    before=retained(); need(any('/response-' in k for k in before),'no pending response')
    source=root/'install.py'; need(sha(source)=='384d0ab31a1b311057d9a47794e540e92d0fedfc37cb350ac2a9a38816859fde','wrong transaction')
    copy=task/'install.py'; shutil.copyfile(source,copy)
    subprocess.run(['git','apply',str(Path(__file__).resolve().parents[1]/'runtime-forward-only.patch')],cwd=task,check=True)
    need(sha(copy)=='31daffdd43906abacaa2039d8a58ef7119f3caf78c8e27a35071481abe8ce933','wrong repair policy')
    tree=ast.parse(copy.read_bytes()); tx,=[n for n in tree.body if isinstance(n,ast.Try)]; i,=[i for i,n in enumerate(tx.body) if isinstance(n,ast.Assert) and isinstance(n.msg,ast.Constant) and n.msg.value=='DONOR_CHANGED']; tx.body=tx.body[i:]
    helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('sha','manifest','atomic')]
    def forbidden(*args): raise AssertionError('no donor start or external operation allowed')
    with lock.open('xb') as fd:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB); authority=ActivationPin(ctl,lock); g=authority.deny(fd.fileno(),previous=None)
        # Real ENOENT between the two historical renames. Candidate remains in its intact staging directory.
        missing=root/'missing-stage'; ns=dict(os=os,hashlib=hashlib,stat=stat,json=json,time=time,shutil=shutil,
            APP=app,STAGE=missing,BACK=backup,RECORDS=records,TASK=task,started=time.monotonic(),stopped=True,start_attempted=False,old_saved=False,
            report={'rollbackPolicy':'forward-only'},admin=forbidden,prop=forbidden)
        exec(compile(ast.Module(body=helpers,type_ignores=[]),'<transaction-helpers>','exec'),ns); ns['baseline']=ns['manifest'](app)
        try:
            with contextlib.redirect_stdout(sys.stderr):exec(compile(ast.Module(body=[tx],type_ignores=[]),'<stopped-transaction>','exec'),ns)
        except FileNotFoundError as e:
            need(Path(e.filename)==missing,'unexpected missing path')
        else: raise AssertionError('missing-stage operation succeeded')
        failure=json.loads((task/'installation-result.json').read_bytes()); need(failure['status']=='FAIL' and failure['predecessorMoved'] and failure['recovery']=='forward_only_repair_required' and not failure['candidateStartAttempted'] and not app.exists(),'unexpected failure recovery')
        try: authority.read_allowed()
        except ValueError as e: need(str(e)=='activation not permitted','unexpected admission error')
        else: raise AssertionError('donor was allowed')
        need(retained()==before,'pending bytes changed while stopped'); stage.rename(app)
        dest=records/'candidate.json'; shutil.copyfile(manifest,dest)
        record=dict(sourceCommit=pins['commit'],sourceTree=pins['tree'],sourceKind='LOCAL',rollbackPolicy='forward-only',unit='cyf-agent-runtime-v1@unified.service',artifactPath=str(app),artifactSha256=pins['archive_sha'],artifactManifestSha256=pins['manifest_sha'],artifactManifestPath=str(dest),status='installed-channel-verification-pending')
        ns['atomic'](records/'current.json',record); generation=authority.allow(fd.fileno(),previous=g,instance=app.parent,records=records,pins=pins)
        permit=authority.read_allowed(); need(permit['generation']==generation and permit['inode']==app.parent.stat().st_ino,'not repaired')
        verify(app,records,**permit['pins']); env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'); subprocess.run(['/bin/bash',app/'runtime/validate.sh','--root',app],stdout=sys.stderr,env=env,check=True)
        # Test driver lives outside the program manifest. ESM realpath resolution loads all actual implementations from app.
        harness=root/'harness'; base=harness/'codex-bridge'; dst=base/'test/fixtures'/peer.name; dst.parent.mkdir(parents=True); shutil.copyfile(peer,dst)
        (harness/'cyf-agent-runtime-v1').symlink_to(app/'runtime',target_is_directory=True)
        for f in (app/'codex-bridge').glob('*.mjs'): (base/f.name).symlink_to(f)
        need(retained()==before and authority.read_allowed()==permit,'repair changed pending source or authority')
        (tmp/'runtime-repair-proof.json').write_text(json.dumps(dict(failure=failure['recovery'],pendingUnchanged=True,manifestSha=pins['manifest_sha'],donorStarted=False)))
        os.execve(app/'node/bin/node',[app/'node/bin/node',dst],env)


if __name__=='__main__': resume(*map(Path,sys.argv[1:]))
