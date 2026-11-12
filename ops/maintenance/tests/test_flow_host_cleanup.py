#!/usr/bin/python3
"""Flow retention regression: isolated fixture files only, no production mutations."""
import importlib.util, json, os, shutil, sys, tempfile, unittest, subprocess
from pathlib import Path
HELPER=sys.argv[1] if len(sys.argv)>1 else '/usr/local/libexec/cyf/flow_host_cleanup.py'
sys.argv=[sys.argv[0]]
spec=importlib.util.spec_from_file_location('flow_test',HELPER); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class FlowTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(prefix='host-cleanup-flow-test.',dir='/tmp'))
  self.p=m.Paths(); self.p.api=self.root/'api'; self.p.api_backups=self.root/'backups'; self.p.web=self.root/'web'; self.p.audit=self.root/'audit/events.jsonl'
  for d in [self.p.api,self.p.api_backups,self.p.web,self.p.api/'downloads',self.p.web/'downloads',self.p.audit.parent]: d.mkdir(parents=True,exist_ok=True)
  self.pin=self.jar(99,b'pinned',1)
  self.state={'schema_version':2,'status':'installed','phase':'installed','recovery':'not_required','run_id':'1','backup':str(self.pin)}
  self.write_state(self.p.api/'record.json',self.state)
  self.write_state(self.p.web/'record.json',{'schema_version':1,'status':'online_verified','phase':'online_verified','run_id':'1'})
 def v3(self):
  import hashlib
  v=m.read_v3_validator(self.p)
  h='a'*64
  ref={'path':'/fixture/evidence.json','sha256':h,'size':1}
  source={'kind':'local-build-v1','batchId':'fixture','identity':{'version':'1.0.0','buildId':'fixture','commit':'b'*40,'tree':'c'*40}}
  pre={'canonicalJarSha256':h,'installedRecord':dict(ref),'approval':dict(ref),
       'runtimeGeneration':{'pid':1,'startTicks':'1','jarSha256':h},
       'identityInventory':dict(ref),'inflightInventory':dict(ref),'schemaInventory':dict(ref)}
  release={'source':source,'precondition':pre,'rollbackPolicy':'forward-only',
           'package':{'sha256':h,'size':1},
           'payloads':{name:{'sha256':h,'size':1} for name in v['LOCAL_MEMBERS']}}
  for key in ['decision','admission','maintenanceAuthority','buildEvidence','controllerVerification','schemaPlan','helperCatalog']:
   release[key]=dict(ref)
  old=self.pin
  self.pin=self.p.api_backups/('20260101T000000Z-'+h+'-99.jar')
  old.rename(self.pin)
  self.state={'schema_version':3,'status':'installed','phase':'installed','recovery':'not_required',
    'release':release,'binding_sha256':v['local_binding_sha'](release),
    'candidate_sha256':h,'previous_sha256':hashlib.sha256(b'pinned').hexdigest(),
    'backup':str(self.pin),'candidate_stop_rc':0,'timestamp':'20260101T000000Z'}
  self.write_state(self.p.api/'record.json',self.state)
 def test_v3_plan_without_fabricated_run(self):
  self.v3();self.history(); p=m.plan(self.p)
  self.assertTrue(p['actions']);self.assertTrue(all(a['run_id'] is None for a in p['actions']))
 def test_v3_apply_retains_pin(self):
  self.v3();self.history();self.apply();self.assertTrue(self.pin.exists());self.assertEqual(len(self.remaining()),1)
 def test_v3_binding_tamper_rejected(self):
  self.v3();self.state['binding_sha256']='0'*64;self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_candidate_mismatch_rejected(self):
  self.v3();self.state['candidate_sha256']='0'*64;self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_pin_content_mismatch_rejected(self):
  self.v3();self.pin.write_bytes(b'changed')
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_unknown_fields_rejected(self):
  self.v3();self.state['run_id']='123';self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_recovery_required_rejected(self):
  self.v3();self.state['recovery']='required';self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_inflight_rejected(self):
  self.v3();self.state['phase']='activating';self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_pin_outside_root_rejected(self):
  self.v3();outside=self.root/self.pin.name;self.pin.rename(outside);self.state['backup']=str(outside)
  self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_changed_record_stops_apply(self):
  self.v3();self.history();proposal=m.plan(self.p);self.state['candidate_stop_rc']=1
  self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):self.apply(proposal)
 def test_v3_missing_release_rejected(self):
  self.v3();del self.state['release'];self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_v3_unsafe_validator_rejected(self):
  self.v3();self.p.validator=self.root/'validator';self.p.validator.write_text('raise RuntimeError()');self.p.validator.chmod(0o777)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_unknown_schema_rejected(self):
  self.state['schema_version']=4;self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def v2_history(self, target=None):
  import hashlib
  target=target or self.jar(7,b'old-v2',10)
  root=self.p.api/'local-inputs/task/precondition';root.mkdir(parents=True)
  record=root/'installedRecord.json'
  old={'schema_version':2,'status':'installed','phase':'installed','recovery':'not_required',
       'run_id':'120','backup':str(target),'previous_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
  self.write_state(record,old)
  self.state['release']['precondition']['installedRecord']={'path':str(record),
    'sha256':hashlib.sha256(record.read_bytes()).hexdigest(),'size':record.stat().st_size}
  self.state['binding_sha256']=m.read_v3_validator(self.p)['local_binding_sha'](self.state['release'])
  self.write_state(self.p.api/'record.json',self.state)
  return target,record
 def test_retire_v2_proven_backup(self):
  self.v3();target,record=self.v2_history()
  self.assertFalse(any(a['remove']==str(target) for a in m.plan(self.p)['actions']))
  proposal=m.plan(self.p,retire_v2=True)
  self.assertTrue(any(a.get('retired_schema_version')==2 for a in proposal['actions']))
  self.apply(proposal);self.assertFalse(target.exists());self.assertTrue(self.pin.exists());self.assertTrue(record.exists())
 def test_retire_v2_active_pin_protected(self):
  self.v3();self.v2_history(self.pin)
  self.assertFalse(m.plan(self.p,retire_v2=True)['actions'])
 def test_retire_v2_tampered_evidence_rejected(self):
  self.v3();target,record=self.v2_history();record.write_text('{}')
  with self.assertRaises(m.Unsafe):m.plan(self.p,retire_v2=True)
 def test_retire_v2_wrong_backup_bytes_rejected(self):
  self.v3();target,record=self.v2_history();target.write_bytes(b'changed')
  with self.assertRaises(m.Unsafe):m.plan(self.p,retire_v2=True)
 def test_retire_v2_is_idempotent(self):
  self.v3();target,record=self.v2_history();self.apply(m.plan(self.p,retire_v2=True))
  self.assertFalse(m.plan(self.p,retire_v2=True)['actions'])
 def test_retire_v2_requires_v3(self):
  with self.assertRaises(m.Unsafe):m.plan(self.p,retire_v2=True)
 def test_retire_v2_busy_backup_retained(self):
  self.v3();target,record=self.v2_history();self.apply(m.plan(self.p,retire_v2=True),busy=lambda p:p==target)
  self.assertTrue(target.exists())
 def test_retire_v2_keep_marker_blocks(self):
  self.v3();target,record=self.v2_history();(record.parent/'.keep').touch()
  with self.assertRaises(m.Unsafe):m.plan(self.p,retire_v2=True)
 def test_retire_v2_symlink_evidence_rejected(self):
  self.v3();target,record=self.v2_history();original=record.parent/'original.json';record.rename(original);record.symlink_to(original)
  with self.assertRaises(m.Unsafe):m.plan(self.p,retire_v2=True)
 def tearDown(self): shutil.rmtree(str(self.root))
 def write_state(self,p,data): p.write_text(json.dumps(data)); p.chmod(0o600)
 def jar(self,n,data,t):
  p=self.p.api_backups/('20260101T000000Z-'+('%064x'%n)+'-'+str(n)+'.jar'); p.write_bytes(data); p.chmod(0o600); os.utime(str(p),(t,t)); return p
 def downloaded(self,root,n):
  d=root/str(n); d.mkdir(); p=d/'package.tgz'; p.write_bytes(b'package'); p.chmod(0o644); os.utime(str(p),(n,n)); return p
 def apply(self,proposal=None,busy=lambda p:False): return m.apply(self.p,proposal or m.plan(self.p),busy)
 def remaining(self): return {f.read_bytes() for f in self.p.api_backups.iterdir() if f!=self.pin}
 def history(self):
  old=self.jar(1,b'newest-content',2); new=self.jar(2,b'newest-content',99)
  for n in range(3,13): self.jar(n,('unique %d'%n).encode(),n+10)
  return old,new
 def test_newest_representative_not_alphabetical(self):
  old,new=self.history(); proposal=m.plan(self.p)
  action=next(a for a in proposal['actions'] if a['remove']==str(old))
  self.assertEqual(action['keep'],str(new)); self.assertFalse(any(a['remove']==str(new) for a in proposal['actions']))
 def test_one_distinct_history_after_dedup(self):
  self.history(); self.apply(); self.assertEqual(len(self.remaining()),1)
 def test_newest_distinct_content_retained(self):
  old,new=self.history(); self.apply(); self.assertTrue(new.exists()); self.assertFalse(old.exists())
 def test_pin_survives_identical_newer_copies(self):
  for n in range(1,14): self.jar(n,b'pinned',n+10)
  self.apply(); self.assertEqual(list(self.p.api_backups.iterdir()),[self.pin])
 def test_two_total_including_old_pin_retained(self):
  for n in range(1,16): self.jar(n,('unique %d'%n).encode(),n)
  self.apply(); self.assertEqual(len(self.remaining()),1); self.assertTrue(self.pin.exists())
 def test_oldest_group_can_be_expired_intentionally(self):
  self.jar(1,b'old',1); self.jar(2,b'old',2)
  for n in range(3,14): self.jar(n,('unique %d'%n).encode(),n)
  self.apply(); self.assertNotIn(b'old',self.remaining()); self.assertEqual(len(self.remaining()),1)
 def test_plan_is_readonly(self):
  self.history(); before={str(f):f.read_bytes() for f in self.p.api_backups.iterdir()}; m.plan(self.p)
  self.assertEqual(before,{str(f):f.read_bytes() for f in self.p.api_backups.iterdir()}); self.assertFalse(self.p.audit.exists())
 def test_download_keep_two_each(self):
  for root in [self.p.api/'downloads',self.p.web/'downloads']:
   for n in range(1,6): self.downloaded(root,n)
  self.apply()
  for root in [self.p.api/'downloads',self.p.web/'downloads']: self.assertEqual(sorted(f.parent.name for f in root.glob('*/package.tgz')),['4','5'])
 def test_private_downloads_keep_two_each(self):
  for root in [self.p.api/'downloads',self.p.web/'downloads']:
   for n in range(1,6): self.downloaded(root,n).chmod(0o600)
  self.apply()
  for root in [self.p.api/'downloads',self.p.web/'downloads']: self.assertEqual(sorted(f.parent.name for f in root.glob('*/package.tgz')),['4','5'])
 def test_mixed_download_modes_keep_two_each(self):
  for root in [self.p.api/'downloads',self.p.web/'downloads']:
   for n in range(1,6): self.downloaded(root,n).chmod(0o600 if n<4 else 0o644)
  self.apply()
  for root in [self.p.api/'downloads',self.p.web/'downloads']: self.assertEqual(sorted(f.parent.name for f in root.glob('*/package.tgz')),['4','5'])
 def test_writable_download_is_protected(self):
  root=self.p.web/'downloads'
  old=self.downloaded(root,1);old.chmod(0o666)
  for n in range(2,6): self.downloaded(root,n)
  self.apply();self.assertTrue(old.exists())
 def test_busy_duplicate_not_removed(self):
  old=self.jar(1,b'x',1); new=self.jar(2,b'x',2); self.apply(busy=lambda p:p==old)
  self.assertTrue(old.exists()); self.assertTrue(new.exists())
 def test_changed_state_blocks_apply(self):
  self.history(); proposal=m.plan(self.p); self.state['run_id']='2'; self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe): self.apply(proposal)
 def test_unconfirmed_state_blocks_plan(self):
  self.state['status']='installing'; self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe): m.plan(self.p)
 def test_unsafe_hardlinks_and_unknown_files_retained(self):
  p=self.jar(1,b'x',2); os.link(str(p),str(self.root/'external.jar')); unknown=self.p.api_backups/'evidence.tgz'; unknown.write_bytes(b'protected')
  self.apply(); self.assertTrue(p.exists()); self.assertTrue(unknown.exists())
 def test_root_keep_stops_plan(self):
  self.history(); (self.p.api_backups/'.keep').touch()
  with self.assertRaises(m.Unsafe): m.plan(self.p)
 def test_keep_appearing_after_plan_stops_apply(self):
  self.history(); proposal=m.plan(self.p); (self.p.api_backups/'.keep').symlink_to('missing')
  with self.assertRaises(m.Unsafe): self.apply(proposal)
 def test_download_subtree_keep_retained(self):
  root=self.p.api/'downloads'
  for n in range(1,5): self.downloaded(root,n)
  (root/'1'/'.keep').touch(); self.apply(); self.assertTrue((root/'1/package.tgz').exists())
 def test_same_device_mount_blocks_backup(self):
  old,new=self.history(); self.p.mountinfo=self.root/'mountinfo'
  self.p.mountinfo.write_text('1 0 1:1 / '+str(old)+' rw - ext4 /dev/mock rw\n')
  proposal=m.plan(self.p); self.assertFalse(any(a['remove']==str(old) for a in proposal['actions']))
  self.assertIn(str(old),proposal['skipped_unsafe'])
 def test_mount_appearing_after_plan_blocks_apply(self):
  old,new=self.history(); proposal=m.plan(self.p); self.p.mountinfo=self.root/'mountinfo'
  self.p.mountinfo.write_text('1 0 1:1 / '+str(self.p.api_backups)+' rw - ext4 /dev/mock rw\n')
  with self.assertRaises(m.Unsafe): self.apply(proposal)
  self.assertTrue(old.exists()); self.assertTrue(new.exists())
 def test_keep_during_audit_blocks_unlink(self):
  old,new=self.history(); proposal=m.plan(self.p); original=m.audit
  def mark(paths,event):
   original(paths,event)
   if event['event']=='remove_intent': (self.p.api_backups/'.keep').touch()
  m.audit=mark
  try:
   with self.assertRaises(m.Unsafe): self.apply(proposal)
  finally: m.audit=original
  self.assertTrue(old.exists())
 def test_symlink_parent_during_audit_blocks_unlink(self):
  old,new=self.history(); proposal=m.plan(self.p); original=m.audit; moved=self.root/'retired-backups'
  def swap(paths,event):
   original(paths,event)
   if event['event']=='remove_intent':
    self.p.api_backups.rename(moved); self.p.api_backups.symlink_to(moved)
  m.audit=swap
  try:
   with self.assertRaises(m.Unsafe): self.apply(proposal)
  finally: m.audit=original
  self.assertTrue((moved/old.name).exists())
 def test_fd_unlink_rejects_replaced_inode(self):
  old,new=self.history(); signature=m.signature(old.stat()); old.rename(old.with_suffix('.saved')); old.write_bytes(b'replaced'); old.chmod(0o600)
  with self.assertRaises(m.Unsafe): m.unlink_payload(self.p,old,signature,self.p.api_backups)
  self.assertTrue(old.exists())
 def test_closed_fd_mapping_protects_payload(self):
  p=self.jar(1,b'x'*4096,2)
  program='import os,sys,ctypes,time; f=os.open(sys.argv[1],os.O_RDONLY); c=ctypes.CDLL(None); c.mmap.restype=ctypes.c_void_p; c.mmap(None,4096,1,2,f,0); os.close(f); print("ready",flush=True); time.sleep(30)'
  child=subprocess.Popen([sys.executable,'-I','-B','-c',program,str(p)],stdout=subprocess.PIPE)
  try:
   self.assertEqual(child.stdout.readline(),b'ready\n'); self.assertTrue(m.open_elsewhere(p))
  finally: child.terminate(); child.wait(); child.stdout.close()
 def test_process_cwd_protects_payload_parent(self):
  p=self.jar(1,b'x',2)
  child=subprocess.Popen([sys.executable,'-I','-B','-c','import time; print("ready",flush=True); time.sleep(30)'],cwd=str(self.p.api_backups),stdout=subprocess.PIPE)
  try:
   self.assertEqual(child.stdout.readline(),b'ready\n'); self.assertTrue(m.open_elsewhere(p))
  finally: child.terminate(); child.wait(); child.stdout.close()
 def test_failed_process_scan_not_treated_as_idle(self):
  p=self.jar(1,b'x',2); fake=self.root/'fake-proc/123'; fake.mkdir(parents=True); (fake/'fd').mkdir(); (fake/'maps').write_text('malformed data\n')
  with self.assertRaises(ValueError): m.open_elsewhere(p,fake.parent)
 def test_missing_process_helper_stops_check(self):
  p=self.jar(1,b'x',2); original=m.__file__; m.__file__=str(self.root/'no-helper/flow.py')
  try:
   with self.assertRaises(FileNotFoundError): m.open_elsewhere(p)
  finally: m.__file__=original
 def test_policy_limit_is_two_including_pin(self):
  self.assertEqual(m.API_BACKUP_KEEP,2)
  self.history(); self.apply()
  self.assertEqual(len(list(self.p.api_backups.iterdir())),2)
 def test_pin_only_not_padded(self):
  self.apply(); self.assertEqual(list(self.p.api_backups.iterdir()),[self.pin])
 def test_pin_and_one_history_not_removed(self):
  p=self.jar(1,b'unique',2); self.apply()
  self.assertTrue(self.pin.exists()); self.assertTrue(p.exists())
 def test_newest_pin_still_counts_towards_limit(self):
  os.utime(str(self.pin),(1000,1000))
  for n in range(1,6): self.jar(n,('content %d'%n).encode(),n)
  self.apply(); self.assertEqual(self.remaining(),{b'content 5'})
  self.assertTrue(self.pin.exists())
 def test_plan_reports_total_limit(self):
  proposal=m.plan(self.p)
  self.assertIn('at most 2 API JAR backups total: pinned rollback plus newest 1 distinct history',proposal['protected'])
 def native_api(self):
  import hashlib
  v=m.read_v3_validator(self.p);h='a'*64;previous=hashlib.sha256(b'pinned').hexdigest()
  a={'schema_version':4,'source_kind':'LOCAL','source':{'version':'1.0.0','buildId':'fixture','commit':'b'*40,'tree':'c'*40},'package':{'path':'/fixture/api.tgz','sha256':h,'size':1},'receipt_sha256':h,'jar_sha256':h,'expected_previous_sha256':previous,'consumed':False}
  self.state={k:a[k] for k in ('schema_version','source_kind','source','package','receipt_sha256','expected_previous_sha256')}
  self.state.update(binding_sha256=v['native_binding'](a),candidate_sha256=h,previous_sha256=previous,status='installed',phase='installed',recovery='not_required',backup=str(self.pin),candidate_stop_rc=0,timestamp='20260101T000000Z')
  self.write_state(self.p.api/'record.json',self.state)
 def native_web(self):
  import hashlib
  v=m.read_v3_validator(self.p,self.p.web_validator)
  d={'schema_version':1,'source_kind':'LOCAL','source':{'version':'1.0.0','buildId':'fixture-web','commit':'b'*40,'tree':'c'*40},'package':{'path':'/fixture/web.tgz','sha256':'a'*64,'size':1},'previousIndexSha256':'d'*64,'previousRecordSha256':'e'*64}
  binding=hashlib.sha256(v['local_json_bytes'](d)).hexdigest();backup=self.p.web/'backups'/binding;backup.mkdir(parents=True)
  self.write_state(backup/'descriptor.json',d)
  self.webstate={'schema_version':2,'source_kind':'LOCAL','status':'online_verified','phase':'online_verified','source':d['source'],'package':d['package'],'artifact_sha256':d['package']['sha256'],'binding_sha256':binding,'backup':str(backup)}
  self.write_state(self.p.web/'record.json',self.webstate)
 def test_native_local_plan_preserves_pin_and_has_no_fake_run(self):
  self.native_api();self.native_web();self.history();proposal=m.plan(self.p)
  self.assertTrue(proposal['actions']);self.assertTrue(all(a['run_id'] is None for a in proposal['actions']))
  self.apply(proposal);self.assertTrue(self.pin.exists())
 def test_native_local_api_binding_tamper_blocks(self):
  self.native_api();self.state['binding_sha256']='0'*64;self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_native_local_api_rollback_digest_tamper_blocks(self):
  self.native_api();self.pin.write_bytes(b'changed')
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_native_local_api_predecessor_mismatch_blocks(self):
  self.native_api();self.state['previous_sha256']='0'*64;self.write_state(self.p.api/'record.json',self.state)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_native_local_web_package_tamper_blocks(self):
  self.native_api();self.native_web();self.webstate['package']=dict(self.webstate['package'],size=2);self.write_state(self.p.web/'record.json',self.webstate)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_native_local_web_unknown_source_blocks(self):
  self.native_api();self.native_web();self.webstate['source_kind']='OTHER';self.write_state(self.p.web/'record.json',self.webstate)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
 def test_native_local_web_inflight_blocks(self):
  self.native_api();self.native_web();self.webstate['status']='installed';self.write_state(self.p.web/'record.json',self.webstate)
  with self.assertRaises(m.Unsafe):m.plan(self.p)
if __name__=='__main__': unittest.main(verbosity=2)
