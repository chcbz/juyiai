"""Isolated full-program startup using independently fixed source and archive pins. Requires worker-prepared, digest-bound public dependencies.

Run only in a dedicated worker mount namespace and new ordinary-disk batch; never
point this at an operator instance. Real API and credentials are not inputs.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_activation_pin import ActivationPin
from runtime_program_view import activate_unified


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def need(ok, why):
    if not ok: raise RuntimeError(why)


def run(base, tools, pkg, src, deps, node, expected):
    need(os.stat('/proc/self/ns/mnt').st_ino != os.stat('/proc/1/ns/mnt').st_ino, 'private worker mount namespace required')
    base.mkdir(mode=0o700); apps = base/'apps'; apps.mkdir(); instance = apps/'unified'; instance.mkdir(); app = instance/'app'; app.mkdir()
    records = instance/'release-records'; records.mkdir(); ctl = base/'control'; ctl.mkdir(); skeleton = base/'view'; (skeleton/'unified').mkdir(parents=True)
    build = json.loads((pkg.parent/'build-result.json').read_bytes()); archive = pkg/'runtime-code-1.3.118.tgz'
    need(build['status']=='PACKAGED_NOT_INSTALLED' and
         (build['commit'],build['tree'],build['artifactSha256']) == expected and sha(archive)==expected[2], 'wrong fixed build')
    subprocess.run(['tar','-xzpf',archive,'-C',app],check=True); bridge = app/'codex-bridge'
    need(sha(bridge/'package-lock.json') == deps.name and (bridge/'package-lock.json').read_bytes()==(deps/'package-lock.json').read_bytes(), 'JS lock mismatch')
    (app/'node/bin').mkdir(parents=True); localnode = app/'node/bin/node'
    for source, dest in ((node,localnode),(deps/'node_modules',bridge/'node_modules'),(tools/'python-stage/codex-bridge/.toolchain',bridge/'.toolchain'),(tools/'browser',bridge/'.browser-toolchain')):
        subprocess.run(['cp','-a','--reflink=auto',source,dest],check=True)
    sources = json.loads((bridge/'toolchain/browser/sources.json').read_bytes())
    for key in ('font','fontLicense'):
        name = sources[key]['name']; public = tools/'public-fonts'/name; need(sha(public)==sources[key]['sha256'],'public font hash')
        subprocess.run(['cp','--remove-destination',public,bridge/'.browser-toolchain/fonts'/name],check=True)
    env = dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', TMPDIR=str(base), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([localnode,app/'runtime/lib/prepare-toolchain-image.mjs','--root',app],env=env,check=True)
    # Fixed repository host fixture produces an independent identity; no access to real conf or issuer.
    fixture_rel = Path('conf/cyf-agent-runtime-v1/test/channel-fixture.mjs')
    fixture = pkg.parent/'build/source'/fixture_rel
    need(sha(fixture) == sha(src/fixture_rel) and subprocess.check_output(['git','-C',src,'rev-parse','HEAD'],text=True).strip()==build['commit'], 'fixture source mismatch')
    config = Path(subprocess.check_output([localnode,'--input-type=module','-e',
        'const {fixture}=await import(process.argv[1]); console.log((await fixture({after(){}},{count:1})).path)',
        fixture.as_uri()],env=env,text=True).strip())
    need(config.is_relative_to(base), 'fixture outside batch'); host = Path(json.loads(config.read_bytes())['stateRoot'])
    entries = []
    for p in sorted(app.rglob('*')):
        s=p.lstat(); row=dict(path=str(p.relative_to(app)),mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,gid=s.st_gid)
        if p.is_symlink(): row.update(type='symlink',target=os.readlink(p))
        elif p.is_dir(): row.update(type='directory')
        else: row.update(type='file',sha256=sha(p))
        entries.append(row)
    manifest=records/'candidate.json'; manifest.write_text(json.dumps(entries)); pins=dict(commit=build['commit'],tree=build['tree'],archive_sha=sha(archive),manifest_sha=sha(manifest))
    (records/'current.json').write_text(json.dumps(dict(sourceCommit=pins['commit'],sourceTree=pins['tree'],sourceKind='LOCAL',rollbackPolicy='forward-only',unit='cyf-agent-runtime-v1@unified.service',artifactPath=str(app),artifactSha256=pins['archive_sha'],artifactManifestSha256=pins['manifest_sha'],artifactManifestPath=str(manifest),status='installed-channel-verification-pending')))
    ns=os.stat('/proc/self/ns/mnt'); lock=ctl/'release.lock'; ownerfile=host/'.runtime-writer.lock/owner.json'
    with lock.open('xb') as owner:
        fcntl.flock(owner,fcntl.LOCK_EX); auth=ActivationPin(ctl,lock); gen=auth.deny(owner.fileno(),previous=None)
        auth.allow(owner.fileno(),previous=gen,instance=instance,records=records,pins=pins); apps.chmod(0o777)
        child_env=dict(env,CYF_RUNTIME_V1_API_BASE_URL='http://127.0.0.1:1')
        starts=[]; instances=set()
        for attempt in (1,2):
            started=time.monotonic()
            with (base/f'start-{attempt}.log').open('w') as log, subprocess.Popen(['unshare','--mount','--net','--propagation','private',sys.executable,__file__,'child',str(base),str(config),str(ns.st_dev),str(ns.st_ino)],env=child_env,stdout=log,stderr=subprocess.STDOUT) as child:
                try:
                    deadline=time.monotonic()+90
                    while time.monotonic()<deadline and child.poll() is None:
                        if ownerfile.is_file() and ownerfile.stat().st_size: break
                        time.sleep(.05)
                    need(ownerfile.exists() and json.loads(ownerfile.read_bytes())['pid']==child.pid, 'Runtime did not acquire fixture writer; inspect start.log')
                    need(os.path.samefile(f'/proc/{child.pid}/exe',localnode), 'not candidate node PID')
                    receipt=json.loads(ownerfile.read_bytes()); need(receipt['instanceId'] not in instances,'reused Runtime instance id')
                    instances.add(receipt['instanceId']); starts.append(round(time.monotonic()-started,3))
                    child.send_signal(signal.SIGTERM); need(child.wait(20)==0 and not ownerfile.exists(),'writer shutdown')
                finally:
                    if child.poll() is None: child.kill(); child.wait()
    print(json.dumps(dict(status='FIXTURE_STARTED_AND_STOPPED',entries=len(entries),startToWriterSeconds=starts,manifestSha=pins['manifest_sha'],archiveSha=pins['archive_sha'])))


if __name__=='__main__':
    if sys.argv[1]=='child':
        base, config=map(Path,sys.argv[2:4]); ctl=base/'control'
        activate_unified(base/'apps/unified',base/'view',authority=ActivationPin(ctl,ctl/'release.lock'),config=config,parent_ns=tuple(map(int,sys.argv[4:])))
    else:
        # Do not derive the expected values from the worker package or build-result.json.
        import argparse, re
        parser=argparse.ArgumentParser()
        for arg in ('base','tools','pkg','src','deps','node'): parser.add_argument(arg,type=Path)
        parser.add_argument('--expected',nargs=3,metavar=('COMMIT','TREE','ARCHIVE_SHA'),required=True)
        args=parser.parse_args(); expected=tuple(args.expected)
        need(all(re.fullmatch('[a-f0-9]{%d}'%size,value) for size,value in zip((40,40,64),expected)),'invalid fixture pins')
        run(args.base,args.tools,args.pkg,args.src,args.deps,args.node,expected)
