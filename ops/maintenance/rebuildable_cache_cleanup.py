#!/usr/bin/python3
"""Bounded inactive caches and explicitly completed task dependencies/final packages.
No inferred completion or recursive source/database/release scanning.
"""
import argparse, fcntl, hashlib, importlib.util, json, os, re, stat, sys, time, uuid
from pathlib import Path

def module(name, file):
 s=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
proc=module('cache_processes',str(Path(__file__).with_name('host_cleanup_processes.py')))
logger=module('cache_audit_logger',str(Path(__file__).with_name('host_cleanup_log.py')))
MAX_ENTRIES=200000
class Unsafe(RuntimeError):pass
class Paths:
 def __init__(self):
  self.cache=Path('/root/.gradle/caches')
  self.state=Path('/home/isp/state/cyf-host-cleanup')
  self.registry=self.state/'completed-tasks.json'
  self.audit=Path('/home/isp/baks/host-cleanup/rebuildable-cache/audit.jsonl')
  self.lock=Path('/run/lock/cyf-host-cleanup.lock')
  self.mountinfo=Path('/proc/self/mountinfo')
  self.proc=Path('/proc')
  # Packages/build state follow the host layout; old shared worktrees are legacy-only.
  self.task_bases=[Path(x) for x in ['/tmp','/var/tmp','/home/isp/pkgs/cyf','/home/isp/state/cyf-local-build/tasks','/home/isp/wsps/cyf/.worktrees','/home/isp/wsps/worktrees']]
  self.runtime_backup_base=Path('/home/isp/baks/cyf-agent-runtime-v1')
  self.artifact_records={
   'api':Path('/home/isp/state/cyf-api-flow/record.json'),
   'web':Path('/home/isp/state/cyf-web-flow/record.json'),
   'runtime':Path('/home/isp/apps/cyf-agent-runtime-v1/release-records/current.json')}
  self.artifact_locks={
   'api':[(Path('/tmp/cyf-api-flow-auto-approval-v2.lock'),0o600),(Path('/tmp/cyf-release-api.lock'),0o660)],
   'web':[(Path('/home/isp/state/cyf-web-flow/deploy.lock'),0o600)],
   'runtime':[(Path('/run/lock/cyf-wuyong-versioned-release.lock'),0o600)]}
  self.root_device=os.stat('/').st_dev
  self._mount_text=None;self._mounts=[]
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def physical(p, write=False):
 s=p.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or s.st_mode&0o002 or (s.st_mode&0o020 and s.st_gid!=0):raise Unsafe('unsafe directory: '+str(p))
 return s
def regular(p):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022 or s.st_nlink!=1:raise Unsafe('unsafe regular file: '+str(p))
 return s
def digest(p,expected,directory=None):
 fd=os.open(str(p) if directory is None else p.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
 with os.fdopen(fd,'rb') as f:
  if signature(os.fstat(f.fileno()))!=tuple(expected):raise Unsafe('file changed before content verification')
  h=hashlib.sha256();remaining=expected[6]
  while remaining:
   b=f.read(min(1024*1024,remaining))
   if not b:raise Unsafe('file shortened while hashing')
   h.update(b);remaining-=len(b)
  if f.read(1) or signature(os.fstat(f.fileno()))!=tuple(expected):raise Unsafe('file changed while hashing')
  return h.hexdigest()
def read_registry(paths):
 if not os.path.lexists(str(paths.registry)):return []
 physical(paths.state);s=regular(paths.registry)
 if s.st_size>1024*1024:raise Unsafe('oversized completion registry')
 fd=os.open(str(paths.registry),os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd) as f:
  if signature(os.fstat(f.fileno()))!=signature(s):raise Unsafe('registry replaced')
  v=json.load(f)
  if signature(os.fstat(f.fileno()))!=signature(s) or signature(paths.registry.lstat())!=signature(s):raise Unsafe('registry changed')
 if not isinstance(v,dict) or v.get('version')!=1 or not isinstance(v.get('tasks'),list) or len(v['tasks'])>256:raise Unsafe('invalid completion registry')
 if any(not isinstance(e,dict) for e in v['tasks']):raise Unsafe('invalid registry entry')
 return v['tasks']
def atomic_json(p,v):
 d=logger.open_parent(p);temp='.'+p.name+'.'+uuid.uuid4().hex
 try:
  try:before=os.stat(p.name,dir_fd=d,follow_symlinks=False);logger.safe_log_stat(before);identity=(before.st_dev,before.st_ino)
  except FileNotFoundError:identity=None
  fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=d)
  with os.fdopen(fd,'w') as f:json.dump(v,f);f.flush();os.fsync(f.fileno())
  try:s=os.stat(p.name,dir_fd=d,follow_symlinks=False);logger.safe_log_stat(s);now=(s.st_dev,s.st_ino)
  except FileNotFoundError:now=None
  if now!=identity:raise Unsafe('registry/status replaced')
  os.replace(temp,p.name,src_dir_fd=d,dst_dir_fd=d);os.fsync(d)
 finally:
  try:os.unlink(temp,dir_fd=d)
  except FileNotFoundError:pass
  os.close(d)
def mounted(paths,p):
 text=paths.mountinfo.read_text()
 if text!=paths._mount_text:
  paths._mount_text=text;paths._mounts=[]
  for line in text.splitlines():
   fields=line.split()
   if len(fields)<6:raise Unsafe('invalid mount metadata')
   paths._mounts.append(re.sub(r'\\([0-7]{3})',lambda m:chr(int(m.group(1),8)),fields[4]))
 name=str(p)
 return any(m!='/' and (name==m or name.startswith(m.rstrip('/')+'/')) for m in paths._mounts)
def guard(paths,p,root):
 if root not in p.parents:raise Unsafe('outside artifact root')
 if mounted(paths,p):raise Unsafe('mounted artifact')
 for d in p.parents:
  s=d.lstat()
  if not stat.S_ISDIR(s.st_mode):raise Unsafe('symlink/non-directory ancestor')
  if os.path.lexists(str(d/'.keep')):raise Unsafe('keep marker')
  if d==root or root in d.parents:physical(d)
 s=regular(p)
 if s.st_dev!=paths.root_device:raise Unsafe('wrong device')
 return s
def used(u,p):
 s=p.stat()
 if not hasattr(u,'ancestor_names'):
  u.ancestor_names=set(u.paths)
  for n in u.paths:u.ancestor_names.update(str(parent) for parent in Path(n).parents)
 return (s.st_dev,s.st_ino) in u.inodes or str(p) in u.ancestor_names

def task_root(paths,p):
 direct=p.parent in paths.task_bases
 # The existing combined controller emits <batch>/api/package and /web/package.
 # Admit only these exact component children, not arbitrary nested task trees.
 combined=(p.name in ('api','web','runtime') and p.parent.parent in paths.task_bases
           and re.fullmatch(r'cyf-[A-Za-z0-9_.-]+',p.parent.name))
 if not p.is_absolute() or '..' in p.parts or not (direct or combined):raise Unsafe('task outside explicit bases')
 if direct and p.parent in paths.task_bases[:2] and not re.fullmatch(r'cyf-[A-Za-z0-9_.-]+',p.name):raise Unsafe('unrecognized temporary task')
 if str(p.resolve())!=str(p):raise Unsafe('symlink task path')
 for root in ([p.parent,p] if combined else [p]):
  physical(root)
  if mounted(paths,root):raise Unsafe('mounted task')
  if os.path.lexists(str(root/'.keep')):raise Unsafe('task keep marker')
 return p

def dependency_root(task,rel):
 if not isinstance(rel,str):raise Unsafe('invalid dependency declaration')
 p=Path(rel)
 if p.is_absolute() or any(x in ('..','.','') for x in rel.split('/')) or len(p.parts)>3 or p.name!='node_modules' or any(x=='node_modules' or x.startswith('.') for x in p.parts[:-1]):raise Unsafe('only explicit node_modules roots supported')
 root=task/p;physical(root)
 # Require reproducible NPM project evidence, never infer completion from inactivity.
 regular(root.parent/'package-lock.json');regular(root.parent/'package.json')
 return root

def artifact_path(paths,task,rel):
 # Only explicitly named final outputs, never source trees, databases or backups.
 if not isinstance(rel,str):raise Unsafe('invalid artifact declaration')
 parts=rel.split('/')
 if (not parts or any(x in ('..','.','') or x.startswith('.') for x in parts)
     or len(parts)>3 or len(parts)>1 and parts[0] not in ('package','packages','artifacts')
     or not rel.endswith(('.jar','.tgz','.tar.gz','.zip'))
     or any(x in rel.lower() for x in ('backup','rollback','evidence','source','state'))):
  raise Unsafe('only explicitly declared final package/JAR outputs supported')
 p=task/rel;guard(paths,p,task)
 return p

def mark_complete(paths,task,rels,artifacts=(),component=None,commit=None,tree=None,payload_sha256=None):
 task=task_root(paths,task);u=proc.snapshot(paths.proc)
 if used(u,task):raise Unsafe('task still active')
 if not isinstance(rels,(list,tuple)) or len(rels)>8 or not rels and not artifacts:raise Unsafe('declare dependencies or final artifacts')
 roots=[dependency_root(task,r) for r in sorted(set(rels))]
 for root in roots:
  if os.path.lexists(str(root/'.keep')):raise Unsafe('dependency keep marker')
 declared=[]
 if artifacts:
  if (component not in paths.artifact_records or len(artifacts)>8
      or not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit)
      or not isinstance(tree,str) or not re.fullmatch('[0-9a-f]{40}',tree)
      or component=='api' and (not isinstance(payload_sha256,str) or not re.fullmatch('[0-9a-f]{64}',payload_sha256))):
   raise Unsafe('artifacts require component, full commit/tree and API payload SHA-256')
  for rel in sorted(set(artifacts)):
   p=artifact_path(paths,task,rel);st=regular(p)
   declared.append({'relative_path':rel,'signature':signature(st),'sha256':digest(p,signature(st))})
  # Parent path and task identity remain the authority, even during registration.
  if used(proc.snapshot(paths.proc),task):raise Unsafe('task became active')
  for item in declared:
   p=artifact_path(paths,task,item['relative_path'])
   if signature(regular(p))!=tuple(item['signature']):raise Unsafe('artifact changed while registering')
 st=task.lstat();entries=read_registry(paths)
 entries=[e for e in entries if e.get('task_root')!=str(task)]
 if len(entries)>=256:raise Unsafe('completion registry full')
 entry={'task_root':str(task),'device':st.st_dev,'inode':st.st_ino,'completed_at':time.time(),'dependencies':[str(r.relative_to(task)) for r in roots]}
 if declared:
  entry['artifacts']={'component':component,'commit':commit,'tree':tree,'payload_sha256':payload_sha256,'files':declared}
 entries.append(entry)
 if not paths.state.exists():paths.state.mkdir(mode=0o700)
 physical(paths.state);atomic_json(paths.registry,{'version':1,'tasks':entries})
 return {'registered':str(task),'dependency_roots':[str(r) for r in roots],'artifacts':[str(task/d['relative_path']) for d in declared]}

def artifact_document(p):
 physical(p.parent);st=regular(p)
 if st.st_size>1024*1024:raise Unsafe('oversized current release record')
 parents=[(d,d.lstat().st_dev,d.lstat().st_ino) for d in p.parents]
 directory=logger.open_parent(p)
 try:
  fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
  with os.fdopen(fd) as f:
   if signature(os.fstat(f.fileno()))!=signature(st):raise Unsafe('current record replaced')
   data=json.load(f)
   if signature(os.fstat(f.fileno()))!=signature(st):raise Unsafe('current record changed')
 finally:os.close(directory)
 if signature(regular(p))!=signature(st):raise Unsafe('current record changed')
 for d,dev,ino in parents:
  now=d.lstat()
  if not stat.S_ISDIR(now.st_mode) or (now.st_dev,now.st_ino)!=(dev,ino):raise Unsafe('current record ancestor changed')
 return data,signature(st)

def artifact_record(paths,component):
 # Read authoritative records as-is, never fabricate CI identity or re-authorize a release.
 data,record_sig=artifact_document(paths.artifact_records[component])
 expected={'api':('installed','source_commit_sha'),'web':('online_verified','commit'),'runtime':('verified-active','sourceCommit')}
 status,key=expected[component]
 native=(component=='api' and data.get('schema_version')==4 or component=='web' and data.get('schema_version')==2) if isinstance(data,dict) else False
 if native:
  identity=data.get('source')
  if (data.get('source_kind')!='LOCAL' or not isinstance(identity,dict)
      or any(not re.fullmatch('[0-9a-f]{40}',str(identity.get(k,''))) for k in ('commit','tree'))
      or not isinstance(identity.get('buildId'),str) or not identity['buildId']):raise Unsafe('unknown LOCAL source; artifacts protected')
  commit=identity['commit']
 else:commit=data.get(key,'') if isinstance(data,dict) else ''
 if not isinstance(data,dict) or data.get('status')!=status or not re.fullmatch('[0-9a-f]{40}',str(commit)):raise Unsafe('unknown/unconfirmed current release; artifacts protected')
 if component in ('api','web') and data.get('phase')!=status:raise Unsafe('current release is incomplete')
 if component=='api' and (data.get('recovery')!='not_required' or not re.fullmatch('[0-9a-f]{64}',str(data.get('previous_sha256','')))):raise Unsafe('unknown API recovery pin')
 tokens=set()
 def strings(v):
  if isinstance(v,str):tokens.add(v)
  elif isinstance(v,dict):
   for x in v.values():strings(x)
  elif isinstance(v,list):
   for x in v:strings(x)
 strings(data)
 if component=='runtime':
  pin=Path(data.get('backup',''))
  if pin.parent!=paths.runtime_backup_base or not re.fullmatch(r'20[0-9]{6}-[A-Za-z0-9_.-]+',pin.name):raise Unsafe('unknown Runtime rollback pin')
  old,old_sig=artifact_document(pin/'current.json')
  if not isinstance(old,dict) or old.get('status')!='verified-active' or not re.fullmatch('[0-9a-f]{40}',str(old.get('sourceCommit',''))):raise Unsafe('unknown Runtime rollback source')
  strings(old);record_sig=record_sig+(str(pin),)+old_sig
 return tokens,record_sig

def artifact_pinned(meta,item,path,task,tokens):
 values={meta['commit'],meta['tree'],meta.get('payload_sha256'),item['sha256'],str(path),str(task)}-{None}
 return bool(values & tokens) or any(t.startswith(str(task)+'/') for t in tokens)

def collect_artifacts(paths,u,now,task_hours):
 entries=read_registry(paths);rows=[];skips=[]
 registry_sig=signature(regular(paths.registry)) if entries else None
 for component in paths.artifact_records:
  batches=[e for e in entries if isinstance(e.get('artifacts'),dict) and e['artifacts'].get('component')==component]
  if not batches:continue
  # Malformed declarations cannot evict newer protected batches.
  if any(not isinstance(e.get('completed_at'),(int,float)) or not 0<e['completed_at']<=now for e in batches):
   skips.append({'component':component,'reason':'invalid artifact completion time'});continue
  batches.sort(key=lambda e:(e['completed_at'],e.get('task_root','')),reverse=True)
  try:tokens,record_sig=artifact_record(paths,component)
  except (OSError,Unsafe,ValueError,TypeError) as exc:
   skips.append({'component':component,'reason':str(exc)});continue
  for entry in batches[2:]:
   try:
    task=task_root(paths,Path(entry['task_root']));st=task.lstat();meta=entry['artifacts']
    if (st.st_dev,st.st_ino)!=(entry['device'],entry['inode']):raise Unsafe('task identity changed')
    if now-entry['completed_at']<task_hours*3600:continue
    if used(u,task):raise Unsafe('artifact task active')
    if (not re.fullmatch('[0-9a-f]{40}',str(meta.get('commit','')))
        or not re.fullmatch('[0-9a-f]{40}',str(meta.get('tree','')))
        or component=='api' and not re.fullmatch('[0-9a-f]{64}',str(meta.get('payload_sha256','')))
        or not isinstance(meta.get('files'),list) or not 1<=len(meta['files'])<=8):raise Unsafe('invalid artifact source declaration')
    pending=[]
    for item in meta['files']:
     p=task/item['relative_path']
     # Missing retired files are harmless. A recreated/replaced path is never adopted.
     if not os.path.lexists(p):continue
     p=artifact_path(paths,task,item['relative_path']);st=regular(p)
     if signature(st)!=tuple(item['signature']):raise Unsafe('registered artifact changed')
     if not re.fullmatch('[0-9a-f]{64}',str(item.get('sha256',''))):raise Unsafe('invalid registered artifact digest')
     if used(u,p) or artifact_pinned(meta,item,p,task,tokens):raise Unsafe('active/current/rollback-bound artifact')
     pending.append({'artifact':True,'path':str(p),'root':str(task),'task':str(task),'signature':signature(st),'sha256':item['sha256'],'allocated':st.st_blocks*512,'cutoff':entry['completed_at'],'completed_at':entry['completed_at'],'root_identity':(task.stat().st_dev,task.stat().st_ino),'task_identity':(task.stat().st_dev,task.stat().st_ino),'component':component,'record_signature':record_sig,'registry_signature':registry_sig,'artifact_metadata':meta,'artifact_item':item})
    rows.extend(pending)
   except (OSError,Unsafe,KeyError,TypeError,ValueError) as exc:skips.append({'path':entry.get('task_root'),'reason':str(exc)})
 return rows,skips


def scopes(paths,now,cache_days,task_hours):
 out=[];skips=[]
 if paths.cache.exists():
  try:physical(paths.cache);out.append((paths.cache,paths.cache,now-(cache_days+1)*86400,None))
  except (OSError,Unsafe) as e:skips.append({'path':str(paths.cache),'reason':str(e)})
 for e in read_registry(paths):
  try:
   if not isinstance(e,dict):raise Unsafe('invalid task entry')
   task=task_root(paths,Path(e['task_root']));st=task.lstat()
   if (st.st_dev,st.st_ino)!=(e['device'],e['inode']):raise Unsafe('task identity changed')
   completed=e['completed_at']
   if not isinstance(completed,(int,float)) or not 0<completed<=now:raise Unsafe('invalid completion time')
   if now-completed<task_hours*3600:continue
   rels=e['dependencies']
   if not isinstance(rels,list) or len(rels)>8 or not rels and not e.get('artifacts'):raise Unsafe('invalid dependency roots')
   for rel in rels:
    root=dependency_root(task,rel)
    if any((root.parent/n).lstat().st_ctime>completed for n in ('package-lock.json','package.json')):raise Unsafe('project changed after completion')
    out.append((root,task,completed,completed))
  except (OSError,Unsafe,KeyError,TypeError,ValueError) as exc:skips.append({'path':e.get('task_root','invalid') if isinstance(e,dict) else 'invalid','reason':str(exc)})
 return out,skips

def collect(paths,u,now,cache_days=2,task_hours=24,include_artifacts=True):
 rows=[];roots,skips=scopes(paths,now,cache_days,task_hours);scanned=0
 for root,task,cutoff,completed in roots:
  if used(u,task):skips.append({'path':str(root),'reason':'scope active'});continue
  for d,ds,fs in os.walk(str(root),followlinks=False):
   depth=len(Path(d).relative_to(root).parts)
   ds[:]=[n for n in ds if depth<16 and not os.path.islink(os.path.join(d,n)) and not os.path.lexists(os.path.join(d,n,'.keep'))]
   for name in fs:
    scanned+=1
    if scanned>MAX_ENTRIES:raise Unsafe('bounded scan limit exceeded; no partial plan')
    if name.endswith('.lock') or name in ('.keep','gc.properties'):continue
    p=Path(d)/name
    try:
     s=guard(paths,p,root)
     if max(s.st_mtime,s.st_ctime)>cutoff or used(u,p):continue
     rows.append({'path':str(p),'root':str(root),'task':str(task),'signature':signature(s),'sha256':digest(p,signature(s)),'allocated':s.st_blocks*512,'cutoff':cutoff,'completed_at':completed,'root_identity':(root.stat().st_dev,root.stat().st_ino),'task_identity':(task.stat().st_dev,task.stat().st_ino)})
    except (OSError,Unsafe) as exc:skips.append({'path':str(p),'reason':str(exc)})
 if include_artifacts:
  artifacts,artifact_skips=collect_artifacts(paths,u,now,task_hours);rows.extend(artifacts);skips.extend(artifact_skips)
 return rows,skips

def unlink_row(paths,r,u):
 p=Path(r['path']);root=Path(r['root']);task=Path(r['task'])
 if used(u,task) or used(u,p):raise Unsafe('active before unlink')
 if (root.stat().st_dev,root.stat().st_ino)!=tuple(r['root_identity']) or (task.stat().st_dev,task.stat().st_ino)!=tuple(r['task_identity']):raise Unsafe('scope identity changed')
 if r.get('artifact'):
  if signature(regular(paths.registry))!=tuple(r['registry_signature']):raise Unsafe('completion registry changed')
  tokens,record_sig=artifact_record(paths,r['component'])
  if record_sig!=tuple(r['record_signature']) or artifact_pinned(r['artifact_metadata'],r['artifact_item'],p,task,tokens):raise Unsafe('current release changed/pinned artifact')
 elif r['completed_at'] and any((root.parent/n).lstat().st_ctime>r['completed_at'] for n in ('package-lock.json','package.json')):raise Unsafe('project changed after completion')
 s=guard(paths,p,root)
 if signature(s)!=tuple(r['signature']) or max(s.st_mtime,s.st_ctime)>r['cutoff']:raise Unsafe('file identity/age changed')
 fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY);chain=[];part=Path('/')
 try:
  for name in p.parent.parts[1:]:
   child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child;part=part/name;st=os.fstat(fd);chain.append((part,st.st_dev,st.st_ino))
  for parent,dev,ino in chain:
   st=parent.lstat()
   if not stat.S_ISDIR(st.st_mode) or (st.st_dev,st.st_ino)!=(dev,ino):raise Unsafe('parent replaced')
  if signature(os.stat(p.name,dir_fd=fd,follow_symlinks=False))!=tuple(r['signature']):raise Unsafe('anchored file changed')
  if digest(p,r['signature'],fd)!=r['sha256']:raise Unsafe('cache content changed')
  if signature(os.stat(p.name,dir_fd=fd,follow_symlinks=False))!=tuple(r['signature']):raise Unsafe('file changed after content verification')
  guard(paths,p,root);os.unlink(p.name,dir_fd=fd)
 finally:os.close(fd)

def free_bytes():
 s=os.statvfs('/');return s.f_bavail*s.f_frsize

def run(paths,mode,cache_days=2,task_hours=24,target_gib=8,inherited=None,min_free_gib=5):
 before=regular(paths.lock)
 fd=os.dup(inherited) if inherited is not None else os.open(str(paths.lock),os.O_RDWR|os.O_NOFOLLOW)
 auditfd=None;artifact_fds=[]
 try:
  if signature(os.fstat(fd))!=signature(before):raise Unsafe('lock changed')
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if signature(paths.lock.lstat())!=signature(before):raise Unsafe('lock replaced')
  include_artifacts=True;artifact_lock_error=None
  components={e['artifacts'].get('component') for e in read_registry(paths) if isinstance(e.get('artifacts'),dict)}
  try:
   for component in sorted(c for c in components if c in paths.artifact_locks):
    for lock,lock_mode in paths.artifact_locks[component]:
     st=lock.lstat()
     if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_nlink!=1 or stat.S_IMODE(st.st_mode)!=lock_mode:raise Unsafe('unsafe artifact release lock')
     held=os.open(lock,os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK);artifact_fds.append(held)
     if signature(os.fstat(held))!=signature(st):raise Unsafe('artifact release lock changed')
     fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
     if signature(lock.lstat())!=signature(st):raise Unsafe('artifact release lock replaced')
  except (OSError,Unsafe) as exc:
   include_artifacts=False;artifact_lock_error=str(exc)
  u=proc.snapshot(paths.proc);rows,skips=collect(paths,u,time.time(),cache_days,task_hours,include_artifacts)
  if artifact_lock_error:skips.append({'path':'registered local artifacts','reason':artifact_lock_error})
  result={'stage':'rebuildable_caches','mode':mode,'eligible_files':len(rows),'estimated_reclaim_bytes':sum(r['allocated'] for r in rows),'skipped_count':len(skips),'artifact_eligible_files':sum(bool(r.get('artifact')) for r in rows),'scope_skips':[r for r in skips if 'component' in r or r.get('path')=='registered local artifacts' or r.get('reason') in ('scope active','task identity changed','dependencies changed after completion','artifact task active','active/current/rollback-bound artifact','registered artifact changed')],'removed_files':0,'reclaimed_allocated_bytes':0}
  if mode=='plan' or free_bytes()>=min_free_gib*1024**3 or not rows:return result
  if not paths.audit.parent.exists():paths.audit.parent.mkdir(mode=0o700)
  physical(paths.audit.parent);logger.LOG=paths.audit;auditfd=logger.rotate_log(logger.open_log(paths.audit))
  def audit(v):
   logger.validate_log(auditfd);b=(json.dumps(v)+'\n').encode();view=memoryview(b)
   while view:
    n=os.write(auditfd,view)
    if n<=0:raise OSError('audit write made no progress')
    view=view[n:]
   os.fsync(auditfd)
  for i in range(0,len(rows),50):
   if free_bytes()>=target_gib*1024**3:break
   batch=rows[i:i+50];auditfd=logger.rotate_log(auditfd);audit({'intent':batch})
   for r in batch:
    if free_bytes()>=target_gib*1024**3:break
    # Fresh FD/cwd/mmap snapshot for every mutation. Incomplete scans abort, not skip silently.
    fresh=proc.snapshot(paths.proc)
    try:unlink_row(paths,r,fresh)
    except (OSError,Unsafe):result['skipped_count']+=1;continue
    result['removed_files']+=1;result['reclaimed_allocated_bytes']+=r['allocated']
    audit({'removed':r['path']})
  return result
 finally:
  if auditfd is not None:os.close(auditfd)
  for held in reversed(artifact_fds):os.close(held)
  os.close(fd)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['plan','clean','mark-complete','mark-active']);p.add_argument('--host-lock-fd',type=int);p.add_argument('--cache-keep-days',type=int,default=2);p.add_argument('--task-keep-hours',type=int,default=24);p.add_argument('--target-gib',type=int,default=8);p.add_argument('--min-free-gib',type=int,default=5);p.add_argument('--task-root',type=Path);p.add_argument('--node-modules',action='append',default=[]);p.add_argument('--artifact',action='append',default=[]);p.add_argument('--component',choices=['api','web','runtime']);p.add_argument('--source-commit');p.add_argument('--source-tree');p.add_argument('--payload-sha256',help='API application JAR digest declared by the task Owner, for rollback pin protection');a=p.parse_args()
 if any(v<0 or v>999999999 for v in (a.cache_keep_days,a.task_keep_hours,a.target_gib,a.min_free_gib)) or a.host_lock_fd is not None and a.host_lock_fd<3:p.error('invalid bounded settings')
 if a.target_gib<a.min_free_gib:p.error('target must be at least trigger')
 paths=Paths()
 try:
  if a.mode in ('mark-complete','mark-active'):
   if os.geteuid()!=0 or a.task_root is None:p.error('task registration requires root and --task-root')
   fd=os.open(str(paths.lock),os.O_RDWR|os.O_NOFOLLOW)
   try:
    st=regular(paths.lock)
    if signature(os.fstat(fd))!=signature(st):raise Unsafe('lock changed')
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if signature(paths.lock.lstat())!=signature(st):raise Unsafe('lock replaced')
    if a.mode=='mark-complete':result=mark_complete(paths,a.task_root,a.node_modules,a.artifact,a.component,a.source_commit,a.source_tree,a.payload_sha256)
    else:
     task=task_root(paths,a.task_root);entries=read_registry(paths)
     if not paths.state.exists():paths.state.mkdir(mode=0o700)
     physical(paths.state);atomic_json(paths.registry,{'version':1,'tasks':[e for e in entries if e.get('task_root')!=str(task)]});result={'active':str(task)}
   finally:os.close(fd)
  else:
   if a.mode=='clean' and os.geteuid()!=0:p.error('clean requires root')
   result=run(paths,a.mode,a.cache_keep_days,a.task_keep_hours,a.target_gib,a.host_lock_fd,a.min_free_gib)
  print(json.dumps(result));return 0
 except (OSError,Unsafe,ValueError,TypeError) as e:print('WARNING: rebuildable cleanup stopped safely: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
