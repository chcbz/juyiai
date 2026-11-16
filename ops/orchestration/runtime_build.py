# Adapted from cyf-tutorial-unblock-20261112/build-runtime.py: portable code only.
# Target-host dependencies are retained and validated separately; never ship x86 dependencies to Eva ARM.
from pathlib import Path
import os,subprocess,json,time,hashlib,stat,sys,re,shutil
import argparse
parser=argparse.ArgumentParser(description='Portable Runtime LOCAL builder, promoted from the existing Runtime114 builder. Never installs.')
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--node',type=Path,required=True)
parser.add_argument('--dependencies',type=Path,required=True)
parser.add_argument('--codex-bin',type=Path,required=True)
parser.add_argument('--commit',required=True)
parser.add_argument('--tree',required=True)
parser.add_argument('--build-id',required=True)
parser.add_argument('--plan-only',action='store_true')
a=parser.parse_args()
repo=a.source;B=a.output;src=B/'build/source';out=B/'package';start=time.monotonic()
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_storage import require_disk,build_environment
os.umask(0o077);[require_disk(p) for p in (B,repo,a.dependencies)];
if a.plan_only:
 print(json.dumps({'source':str(repo),'output':str(B),'node':str(a.node),'dependencies':str(a.dependencies),'codexBin':str(a.codex_bin),'commit':a.commit,'tree':a.tree,'limitSeconds':600}));sys.exit(0)
B.mkdir(mode=0o700,parents=True);src.mkdir(parents=True);out.mkdir();env=build_environment(B/'t',os.environ.copy());env['PYTHONDONTWRITEBYTECODE']='1';env['CYF_NATIVE_EXECUTION_ISOLATION_PROBE']='1';env['CYF_CODEX_BIN']=str(a.codex_bin)
git=lambda *a:subprocess.check_output(['git','-C',repo,*a],text=True).strip()
assert not git('status','--porcelain')
commit=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');assert commit==a.commit and tree==a.tree
assert (repo/'conf/codex-bridge/package-lock.json').read_bytes()==(a.dependencies/'package-lock.json').read_bytes(), 'dependency lock mismatch'
runtime_version=json.loads((repo/'conf/cyf-agent-runtime-v1/package.json').read_text())['version']
r={'sourceKind':'LOCAL','buildId':a.build_id,'commit':commit,'tree':tree,'status':'RUNNING','startedAt':time.time(),'limitSeconds':600,'artifactScope':'portable runtime and bridge code; target-host dependency validation required'}
def save():(B/'build-result.json').write_text(json.dumps(r,indent=2)+'\n')
def run(args,**kw):return subprocess.run(list(map(str,args)),env=env,check=True,timeout=max(1,600-(time.monotonic()-start)),**kw)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def manifest(root):
 rows=[]
 for p in sorted(root.rglob('*')):
  st=p.lstat();e={'path':str(p.relative_to(root)),'mode':oct(stat.S_IMODE(st.st_mode))}
  if p.is_symlink():raise RuntimeError('unexpected code symlink')
  elif p.is_dir():e['type']='directory'
  elif p.is_file():e.update(type='file',sha256=sha(p))
  else:raise RuntimeError('unsupported code entry')
  rows.append(e)
 return rows
save()
try:
 tool_paths=[a.node,Path('/bin/cat'),Path('/bin/sleep'),Path('/usr/bin/bwrap')]
 tool_paths += [a.codex_bin,Path('/usr/bin/slirp4netns'),Path('/usr/sbin/nft'),Path('/usr/bin/nsenter'),Path('/usr/bin/unshare')]
 tool_inputs=[{'path':str(p),'realpath':str(p.resolve()),'sha256':sha(p)} for p in tool_paths]
 resources=a.codex_bin.parent.parent/'codex-resources'
 assert resources.is_dir(), 'native engine resource closure missing'
 resource_inputs=[{'path':str(p),'sha256':sha(p)} for p in sorted(resources.rglob('*')) if p.is_file()]
 assert resource_inputs, 'empty native engine resource closure'
 r['externalTools']=tool_inputs;r['codexResources']=resource_inputs;save()
 with (B/'source.tar').open('wb') as f:run(['git','-c','tar.umask=0077','-C',repo,'archive',commit],stdout=f)
 run(['tar','-xf',B/'source.tar','-C',src]);(B/'source.tar').unlink()
 run(['cp','--archive','--link',a.dependencies/'node_modules',src/'conf/codex-bridge/node_modules'])
 tests=['hosting-control', 'runtime-host', 'hosting-lifecycle', 'hosting-readmission-integration', 'unified-runtime-acceptance', 'hosting-config', 'hosting-adoption', 'hosting-outbound-host', 'hosting-outbound', 'hosting-setup-cli', 'hosting-tls', 'private-home-cleanup', 'private-data-cleanup', 'private-state-cleanup', 'provider-environments', 'model-auth-migration']
 node=a.node
 with (B/'test.log').open('w') as log:run([node,'--test','--test-concurrency=1','--test-reporter=tap',*[src/'conf/cyf-agent-runtime-v1/test'/(t+'.test.mjs') for t in tests],*[src/'conf/codex-bridge/test'/(t+'.test.mjs') for t in ['native-readiness', 'managed-chat-scope-config', 'juyiting-typed-outcome', 'juyiting-action-outcome', 'juyiting-typed-runtime', 'chat-runtime', 'agent-client', 'materials-chat', 'chat-context-retry', 'registration-footprint', 'model-auth', 'typed-inspection-profile', 'native-execution-profile', 'native-image-execution-profile', 'native-browser-execution-profile', 'skill-inventory', 'app-server-native-handshake', 'config-runtime']]],stdout=log,stderr=subprocess.STDOUT)
 counts={k:int(v) for k,v in re.findall(r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$',(B/'test.log').read_text(),re.M)}
 assert counts.get('tests',0)>0 and not any(counts.get(k,0) for k in ['fail','cancelled','todo'])
 r['toolchain']={'python':sys.version,'nodeVersion':subprocess.check_output([str(node),'--version'],text=True).strip(),'builderSha256':sha(Path(__file__)),'lockSha256':sha(a.dependencies/'package-lock.json')}
 r['tests']={'counts':counts,'files':tests+['native-readiness', 'managed-chat-scope-config', 'juyiting-typed-outcome', 'juyiting-action-outcome', 'juyiting-typed-runtime', 'chat-runtime', 'agent-client', 'materials-chat', 'chat-context-retry', 'registration-footprint', 'model-auth', 'typed-inspection-profile', 'native-execution-profile', 'native-image-execution-profile', 'native-browser-execution-profile', 'skill-inventory', 'app-server-native-handshake', 'config-runtime'],'logSha256':sha(B/'test.log'),'nodeSha256':sha(node)};save()
 payload=B/'build/payload';payload.mkdir()
 shutil.copytree(src/'conf/cyf-agent-runtime-v1',payload/'runtime',ignore=shutil.ignore_patterns('test','.gitignore'))
 run([node,'--input-type=module','-e',"import{pathToFileURL}from'node:url';let m=await import(pathToFileURL(process.argv[1]));await m.collateExecutionPayload(process.argv[2],process.argv[3])",src/'conf/cyf-agent-runtime-v1/lib/execution-adapter.mjs',src/'conf/codex-bridge',payload/'codex-bridge'])
 entries=manifest(payload);(out/'artifact.manifest.json').write_text(json.dumps(entries,indent=2)+'\n')
 archive=out/('runtime-code-'+runtime_version+'.tgz');run(['tar','--numeric-owner','-I','gzip -1','-cf',archive,'-C',payload,'.'])
 assert all(sha(Path(row['path']))==row['sha256'] for row in tool_inputs+resource_inputs), 'external build tool changed'
 assert manifest(payload)==entries and not git('status','--porcelain') and git('rev-parse','HEAD')==commit
 r.update(status='PACKAGED_NOT_INSTALLED',artifactPath=str(archive),artifactSha256=sha(archive),artifactBytes=archive.stat().st_size,manifestSha256=sha(out/'artifact.manifest.json'),runtimeVersion=runtime_version,bridgeVersion=json.loads((payload/'codex-bridge/package.json').read_text())['version'],payloadPath=str(payload))
except BaseException as e:r.update(status='FAIL',error=type(e).__name__+': '+str(e));raise
finally:r['seconds']=round(time.monotonic()-start,3);save();print(json.dumps(r))
