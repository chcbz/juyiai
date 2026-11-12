#!/usr/bin/env python3
import argparse,datetime,fcntl,gzip,hashlib,json,os,pathlib,signal,subprocess,tarfile,time,shutil
from build_storage import require_disk, build_environment
from web_dependencies import ensure as ensure_dependencies, verify as verify_dependencies
P=pathlib.Path; D=P(__file__).resolve().parent;T=time.monotonic()
parser=argparse.ArgumentParser(description='Fixed-source LOCAL Web release baseline/build/package; never installs.')
parser.add_argument('--source',type=P,required=True)
parser.add_argument('--output',type=P,required=True)
parser.add_argument('--batch-id',required=True)
parser.add_argument('--expected-commit',required=True)
parser.add_argument('--dependency-store',type=P,default=P('/home/isp/state/cyf-local-build/web-dependencies'))
parser.add_argument('--regression-test',action='append',default=[])
args=parser.parse_args();S=args.source;B=args.output
for p in (S,B):
 if not p.is_absolute() or p!=p.resolve():raise ValueError('source/output must be absolute physical paths')
if B==S or S in B.parents:raise ValueError('output must be outside source')
for forbidden in [P('/home/isp/hosts'),P('/opt/cyf/service'),P('/home/isp/apps/cyf-agent-runtime-v1')]:
 if B==forbidden or forbidden in B.parents:raise ValueError('never build inside production')
if not __import__('re').fullmatch('[A-Za-z][A-Za-z0-9_.-]*',args.batch_id):raise ValueError('invalid LOCAL build ID')
for p in (S,B):require_disk(p)
os.umask(0o077);B.mkdir(parents=True);R={'status':'RUNNING','publishable':False,'scope':'selected release baseline; NOT full suite, installer or deployment','stages':[]}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save():
 R['wallSeconds']=round(time.monotonic()-T,3);p=B/'result.tmp';p.write_text(json.dumps(R,indent=2));os.replace(p,B/'result.json')
def stop(n,f):R.update(status='STOPPED_BEFORE_COMPLETION',signal=n);save();raise SystemExit(128+n)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def git(*args):return subprocess.check_output(['git','-C',str(S),*args]).decode().strip()
def run(name,args):
 t=time.monotonic();r={'name':name,'argv':list(map(str,args))};R['stages'].append(r);save()
 with (B/(name+'.log')).open('w') as log:rc=subprocess.call(list(map(str,args)),cwd=S,env=env,stdout=log,stderr=subprocess.STDOUT)
 r.update(seconds=round(time.monotonic()-t,3),exitCode=rc);save()
 if rc:raise RuntimeError(name+' failed: '+str(rc))
try:
 assert not git('status','--porcelain')
 R.update(startedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),source={'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}')},lockSha256=sha(S/'package-lock.json'),tools={str(p):sha(p) for p in [P(__file__),D/'local-web-build.mjs',D/'build_storage.py',D/'web_dependencies.py']},sparseCheckout='All production src/public/static and root config present; prototypes and unselected tests omitted; interface-wire mjs suites and fixtures present')
 assert R['source']['commit']==args.expected_commit
 assert git('rev-parse','--show-toplevel')==str(S)
 R['nodeVersion']=subprocess.check_output(['/home/isp/apps/node/bin/node','--version']).decode().strip()
 R['nodeBinarySha256']=sha(P('/home/isp/apps/node/bin/node').resolve())
 env=build_environment(B);env['PATH']='/home/isp/apps/node/bin:'+env.get('PATH','')
 for k in list(env):
  if k.startswith(('PIPELINE_','CI_COMMIT','CYF_FLOW_')) or k in ['CI','BUILD_NUMBER']:env.pop(k,None)
 # npm config may redirect the cache to tmpfs; inspect its effective value.
 cache=P(subprocess.check_output(['npm','config','get','cache'],cwd=S,env=env,universal_newlines=True).strip())
 require_disk(cache)
 with open('/tmp/cyf-gradle.lock','a+') as lock:
  t=time.monotonic();fcntl.flock(lock,fcntl.LOCK_EX);R['queueSeconds']=round(time.monotonic()-t,3)
  t=time.monotonic();stage={'name':'dependencies'};R['stages'].append(stage);save()
  try:
   with (B/'dependencies.log').open('w') as log:
    R['dependencies']=ensure_dependencies(S,args.dependency_store,env,log)
  finally:stage['seconds']=round(time.monotonic()-t,3);save()
  tests=['app-title','home-login-redirect','identity-scope','interface-wire','production-build-flags','public-entry-navigation','public-pwa-beta-entry','pwa-shell-freshness']
  tests+=args.regression_test
  run('tests',['node','--import','tsx','./node_modules/mocha/bin/mocha.js','--no-config','--require','./tests/setup.js','--timeout','10000','--exit','--reporter','mochawesome','--reporter-options','reportDir='+str(B/'test-reports')+',reportFilename=mochawesome.json,consoleReporter=dot',*[f'tests/{n}.test.js' for n in tests]])
  run('build',['node',D/'local-web-build.mjs',S,B/'dist'])
  verify_dependencies(P(R['dependencies']['path']),R['dependencies']['inputs'])
  changed=git('diff','--name-only').splitlines();assert set(changed)<=set(['src/components.d.ts','src/auto-imports.d.ts']),changed
  if changed:
   (B/'generated-declarations.patch').write_text(subprocess.check_output(['git','-C',str(S),'diff','--',*changed]).decode());subprocess.check_call(['git','-C',str(S),'restore','--source=HEAD','--',*changed])
  assert not git('status','--porcelain')
  files={}
  for folder in [S/'public',B/'dist']:
   for p in folder.rglob('*'):
    assert not p.is_symlink(),str(p)
    if p.is_file():files[str(p.relative_to(folder))]=p
  report=B/'test-reports/mochawesome.json'; stats=json.loads(report.read_text())['stats'];assert stats['failures']==0 and stats['passes']>0
  manifest={'format':'cyf-local-web-build-v2','buildId':args.batch_id,'tests':{'reportSha256':sha(report),'selector':tests,'stats':{k:stats[k] for k in ['tests','passes','failures','pending']}},'source':R['source'],'dependencies':{k:R['dependencies'][k] for k in ['key','receiptSha256']},'version':json.loads((S/'package.json').read_text())['version'],'files':{n:{'sha256':sha(p),'size':p.stat().st_size} for n,p in sorted(files.items())},'scope':R['scope']}
  (B/'manifest.json').write_text(json.dumps(manifest,indent=2)); t=time.monotonic();(B/'package').mkdir();pkg=B/'package/web.tgz'
  class SpaceGuard:
   def __init__(self, stream):self.stream=stream
   def write(self, data):
    if shutil.disk_usage(B).free < 32*1024*1024 + len(data):raise OSError('Stop before exhausting host disk; preserve 32MiB reserve')
    return self.stream.write(data)
   def flush(self):return self.stream.flush()
  with pkg.open('wb') as raw,gzip.GzipFile(fileobj=SpaceGuard(raw),mode='wb',compresslevel=1,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
   for n,p in sorted(files.items(), key=lambda item: (0 if B/'dist' in item[1].parents else 1, item[0])):
    tar.add(p,arcname=n,recursive=False)
    if B/'dist' in p.parents:p.unlink() # owned generated bytes already in stream; never unlink public source
   tar.add(B/'manifest.json',arcname='cyf-local-build.json',recursive=False)
  R['stages'].append({'name':'package','seconds':round(time.monotonic()-t,3)})
  t=time.monotonic()
  with tarfile.open(pkg,'r:gz') as tar:
   seen=set()
   for m in tar:
    assert m.isfile() and m.name not in seen;seen.add(m.name)
    data=tar.extractfile(m)
    h=hashlib.sha256();length=0
    for chunk in iter(lambda:data.read(1024*1024),b''):h.update(chunk);length+=len(chunk)
    if m.name!='cyf-local-build.json':assert {'sha256':h.hexdigest(),'size':length}==manifest['files'][m.name]
   assert seen==set(files)|{'cyf-local-build.json'}
  R['stages'].append({'name':'package-integrity','seconds':round(time.monotonic()-t,3)})
  R.update(status='BUILT',artifact={'path':str(pkg),'sha256':sha(pkg)},sourceUnchanged=not git('status','--porcelain'))
except Exception as e:
 R.update(status='FAIL',error=str(e));save();raise
finally:save()
