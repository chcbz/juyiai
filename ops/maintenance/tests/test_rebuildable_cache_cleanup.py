#!/usr/bin/python3
"""Isolated metadata/deletion fixtures only; never production clean."""
import importlib.util,json,os,shutil,tempfile,time,unittest
from pathlib import Path
from unittest import mock
s=importlib.util.spec_from_file_location('rebuildable',str(Path(__file__).resolve().parents[1]/'rebuildable_cache_cleanup.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.base=Path(tempfile.mkdtemp(prefix='rebuildable-test.',dir='/tmp'));self.p=m.Paths()
  self.p.cache=self.base/'cache';self.p.cache.mkdir()
  self.p.state=self.base/'state';self.p.registry=self.p.state/'completed-tasks.json'
  self.p.audit=self.base/'audit/audit.jsonl';self.p.lock=self.base/'cleanup.lock';self.p.lock.write_text('');self.p.lock.chmod(0o600)
  self.p.mountinfo=self.base/'mounts';self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n')
  self.p.proc=self.base/'proc';(self.p.proc/'123/fd').mkdir(parents=True);(self.p.proc/'123/maps').write_text('')
  self.temp=self.base/'tasks';self.temp.mkdir();self.p.task_bases=[self.temp,self.base/'var-tasks']
  self.now=time.time()+5*86400
 def tearDown(self):shutil.rmtree(str(self.base))
 def file(self,name='old.bin'):
  p=self.p.cache/name;p.write_text('fixture');p.chmod(0o600);return p
 def rows(self):return m.collect(self.p,m.proc.snapshot(self.p.proc),self.now)[0]
 def task(self):
  task=self.temp/'cyf-fixture';(task/'web/node_modules').mkdir(parents=True)
  (task/'web/package-lock.json').write_text('{}');(task/'web/package.json').write_text('{}')
  for n in ('a.js','b.js'):(task/'web/node_modules'/n).write_text('dependency')
  return task
 def complete(self,task):m.mark_complete(self.p,task,['web/node_modules'])
 def test_host_layout_has_explicit_package_and_build_bases_not_private_maintenance(self):
  bases=m.Paths().task_bases
  self.assertIn(Path('/home/isp/pkgs/cyf'),bases)
  self.assertIn(Path('/home/isp/state/cyf-local-build/tasks'),bases)
  self.assertIn(Path('/home/isp/wsps/cyf/.worktrees'),bases)
  self.assertNotIn(Path('/home/isp/wsps/private-maintenance'),bases)
  self.assertNotIn(Path('/home/isp/baks/private-maintenance'),bases)
 def test_explicit_package_and_build_component_roots_remain_bounded(self):
  for name in ('pkgs','build-tasks'):
   base=self.base/name;base.mkdir();self.p.task_bases.append(base)
   task=base/'cyf-new-batch/api';task.mkdir(parents=True)
   self.assertEqual(m.task_root(self.p,task),task)
   nested=task/'nested';nested.mkdir()
   with self.assertRaises(m.Unsafe):m.task_root(self.p,nested)
 def test_old_global_cache_eligible(self):p=self.file();self.assertEqual([r['path'] for r in self.rows()],[str(p)])
 def test_recent_ctime_protects_even_if_mtime_old(self):p=self.file();os.utime(str(p),(0,0));self.assertFalse(m.collect(self.p,m.proc.snapshot(self.p.proc),time.time())[0])
 def test_keep_dangling_symlink_protects(self):self.file();(self.p.cache/'.keep').symlink_to('missing');self.assertFalse(self.rows())
 def test_hardlinks_protected(self):p=self.file();os.link(str(p),str(self.base/'external'));self.assertFalse(self.rows())
 def test_symlink_and_group_write_protected(self):p=self.file();p.chmod(0o660);(self.p.cache/'link').symlink_to(p);self.assertFalse(self.rows())
 def test_ancestor_mount_protected(self):self.file();self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n2 1 0:0 / %s rw - ext4 /dev/x rw\n'%self.base);self.assertFalse(self.rows())
 def test_fd_scope_protected(self):p=self.file();(self.p.proc/'123/fd/4').symlink_to(p);self.assertFalse(self.rows())
 def test_mmap_without_fd_protected(self):p=self.file();st=p.stat();(self.p.proc/'123/maps').write_text('1000-2000 r--p 00000000 %02x:%02x %d %s\n'%(os.major(st.st_dev),os.minor(st.st_dev),st.st_ino,p));self.assertFalse(self.rows())
 def test_incomplete_process_scan_fails_closed(self):self.file();(self.p.proc/'123/maps').write_text('malformed');self.assertRaises(ValueError,self.rows)
 def test_unregistered_task_never_scanned(self):self.task();self.assertFalse(self.rows())
 def test_register_requires_inactive_task(self):task=self.task();(self.p.proc/'123/cwd').symlink_to(task);self.assertRaises(m.Unsafe,self.complete,task)
 def test_only_declared_dependencies_no_source_or_database(self):
  task=self.task();(task/'source.py').write_text('source');(task/'mysql-data').mkdir();(task/'mysql-data/data.bin').write_text('database');self.complete(task)
  self.assertEqual(len(self.rows()),2);self.assertTrue(all('node_modules' in r['path'] for r in self.rows()))
 def test_fresh_completion_waits_24_hours(self):task=self.task();self.complete(task);self.assertFalse(m.collect(self.p,m.proc.snapshot(self.p.proc),time.time())[0])
 def test_invalid_dependency_scope_rejected(self):task=self.task();self.assertRaises(m.Unsafe,m.mark_complete,self.p,task,['mysql-data']);self.assertRaises(m.Unsafe,m.mark_complete,self.p,task,['../node_modules'])
 def test_package_lock_required(self):task=self.task();(task/'web/package-lock.json').unlink();self.assertRaises(FileNotFoundError,self.complete,task)
 def test_changed_project_after_completion_protected(self):task=self.task();self.complete(task);time.sleep(.01);(task/'web/package.json').write_text('{"changed":true}');self.assertFalse(self.rows())
 def test_changed_task_identity_protected(self):task=self.task();self.complete(task);task.rename(self.temp/'old');task.mkdir();self.assertFalse(self.rows())
 def test_new_file_after_completion_retained(self):task=self.task();self.complete(task);time.sleep(.01);(task/'web/node_modules/new.js').write_text('new');self.assertEqual(len(self.rows()),2)
 def test_malformed_registry_aborts(self):task=self.task();self.complete(task);self.p.registry.write_text('{');self.assertRaises(ValueError,self.rows)
 def test_changed_file_before_unlink_retained(self):p=self.file();r=self.rows()[0];p.write_text('changed');self.assertRaises(m.Unsafe,m.unlink_row,self.p,r,m.proc.snapshot(self.p.proc));self.assertTrue(p.exists())
 def test_parent_symlink_before_unlink_rejected(self):p=self.file();r=self.rows()[0];self.p.cache.rename(self.base/'original');self.p.cache.symlink_to(self.base/'original');self.assertRaises((m.Unsafe,OSError),m.unlink_row,self.p,r,m.proc.snapshot(self.p.proc));self.assertTrue(p.exists())
 def test_plan_has_no_mutation_or_audit(self):p=self.file();result=m.run(self.p,'plan');self.assertTrue(p.exists());self.assertFalse(self.p.audit.exists());self.assertEqual(result['removed_files'],0)
 def test_clean_removes_registered_dependencies_only(self):
  task=self.task();self.complete(task);(task/'source.py').write_text('keep')
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):result=m.run(self.p,'clean')
  self.assertEqual(result['removed_files'],2);self.assertTrue((task/'source.py').exists());self.assertTrue(task.exists());self.assertIn('intent',self.p.audit.read_text())
 def test_clean_high_space_is_noop(self):
  p=self.file()
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=10*1024**3):result=m.run(self.p,'clean')
  self.assertTrue(p.exists());self.assertEqual(result['removed_files'],0)
 def test_audit_symlink_blocks_all_mutations(self):
  p=self.file();self.p.audit.parent.mkdir();self.p.audit.symlink_to(self.base/'outside')
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):self.assertRaises(OSError,m.run,self.p,'clean')
  self.assertTrue(p.exists())
 def test_missing_lock_fails_closed(self):self.file();self.p.lock.unlink();self.assertRaises(FileNotFoundError,m.run,self.p,'clean')
 def test_task_cannot_escape_explicit_bases(self):self.assertRaises(m.Unsafe,m.task_root,self.p,self.base)
 def test_content_changed_with_same_metadata_refused(self):
  p=self.file();r=self.rows()[0];p.write_text('changed')
  with mock.patch.object(m,'signature',return_value=tuple(r['signature'])):self.assertRaises(m.Unsafe,m.unlink_row,self.p,r,m.proc.snapshot(self.p.proc))
  self.assertTrue(p.exists())
 def test_scan_limit_aborts_no_partial_delete(self):
  a=self.file('a.bin');b=self.file('b.bin')
  with mock.patch.object(m,'MAX_ENTRIES',1),mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):self.assertRaises(m.Unsafe,m.run,self.p,'clean')
  self.assertTrue(a.exists());self.assertTrue(b.exists())
 def test_snapshot_failure_after_plan_stops_deletion(self):
  p=self.file();u=m.proc.snapshot(self.p.proc)
  with mock.patch.object(m.proc,'snapshot',side_effect=[u,PermissionError('fixture incomplete')]),mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):self.assertRaises(PermissionError,m.run,self.p,'clean')
  self.assertTrue(p.exists())
 def test_wrong_inherited_lock_refused(self):
  self.file();other=self.base/'other.lock';other.write_text('');fd=os.open(str(other),os.O_RDWR)
  try:self.assertRaises(m.Unsafe,m.run,self.p,'plan',inherited=fd)
  finally:os.close(fd)
 def test_custom_free_space_trigger_respected(self):
  p=self.file()
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=7*1024**3):result=m.run(self.p,'clean',min_free_gib=10,target_gib=12)
  self.assertFalse(p.exists());self.assertEqual(result['removed_files'],1)
class ArtifactTests(unittest.TestCase):
 setUp=Tests.setUp
 tearDown=Tests.tearDown
 def setUp(self):
  Tests.setUp(self)
  self.p.artifact_records={};self.p.artifact_locks={};self.p.runtime_backup_base=self.base/'runtime-backups';self.p.runtime_backup_base.mkdir()
  for component in ('api','web','runtime'):
   record=self.base/(component+'-record.json');lock=self.base/(component+'-release.lock')
   lock.write_text('');lock.chmod(0o600)
   self.p.artifact_records[component]=record;self.p.artifact_locks[component]=[(lock,0o600)]
   self.pin(component)
 def pin(self,component='api',**kw):
  status={'api':'installed','web':'online_verified','runtime':'verified-active'}[component]
  key={'api':'source_commit_sha','web':'commit','runtime':'sourceCommit'}[component]
  data={'status':status,'phase':status,key:'f'*40,'previous_sha256':'f'*64,'recovery':'not_required'};data.update(kw)
  if component=='runtime':
   pin=self.p.runtime_backup_base/'20261106-fixture';pin.mkdir(exist_ok=True)
   (pin/'current.json').write_text(json.dumps({'status':'verified-active','sourceCommit':'e'*40}))
   data['backup']=str(pin)
  self.p.artifact_records[component].write_text(json.dumps(data))
 def batch(self,i,component='api',artifact='package/final.tgz',dependencies=False):
  task=self.temp/('cyf-'+component+str(i));(task/'package').mkdir(parents=True)
  file=task/artifact;file.write_text('unique package '+str(i));file.chmod(0o600)
  rels=[]
  if dependencies:
   (task/'web/node_modules').mkdir(parents=True)
   (task/'web/package.json').write_text('{}');(task/'web/package-lock.json').write_text('{}')
   (task/'web/node_modules/a.js').write_text('dependency');rels=['web/node_modules']
  m.mark_complete(self.p,task,rels,[artifact],component,('%040x'%i),('%040x'%(i+100)),('%064x'%(i+200)))
  return task,file
 def four(self,component='api'):
  return [self.batch(i,component) for i in range(1,5)]
 def rows(self):
  return m.collect(self.p,m.proc.snapshot(self.p.proc),self.now)[0]
 def clean(self):
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):
   return m.run(self.p,'clean')
 def test_newest_two_per_component_preserved(self):
  batches=self.four();self.assertEqual({r['path'] for r in self.rows()},{str(f) for t,f in batches[:2]})
 def test_current_source_preserved(self):
  batches=self.four();self.pin(source_commit_sha='%040x'%1)
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_rollback_payload_digest_preserved(self):
  batches=self.four();self.pin(previous_sha256='%064x'%201)
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_current_archive_digest_preserved(self):
  batches=self.four();digest=m.digest(batches[0][1],m.signature(batches[0][1].stat()))
  self.pin(artifact_sha256=digest)
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_current_record_path_references_protected(self):
  batches=self.four();self.pin(package_path=str(batches[0][1]))
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_archive_grace_24h(self):
  self.four();self.assertFalse(m.collect(self.p,m.proc.snapshot(self.p.proc),time.time())[0])
 def test_archive_keep_and_active_task_protected(self):
  batches=self.four();(batches[0][0]/'.keep').symlink_to('missing')
  (self.p.proc/'123/fd/3').symlink_to(batches[1][1]);self.assertFalse(self.rows())
 def test_archive_changed_after_registration_protected(self):
  batches=self.four();batches[0][1].write_text('new data')
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_archive_symlink_replacement_protected(self):
  batches=self.four();batches[0][1].unlink();batches[0][1].symlink_to(batches[1][1])
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_archive_hardlink_protected(self):
  batches=self.four();os.link(batches[0][1],self.base/'alias')
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_only_declared_artifacts_no_metadata_or_sources_removed(self):
  batches=self.four()
  for task,file in batches:
   (task/'source.java').write_text('source');(task/'receipt.json').write_text('{}');(task/'other.tgz').write_text('unregistered')
  result=self.clean();self.assertEqual(result['removed_files'],2)
  self.assertEqual(result['artifact_eligible_files'],2)
  for task,file in batches:
   self.assertTrue(task.is_dir());self.assertTrue((task/'receipt.json').exists());self.assertTrue((task/'other.tgz').exists())
  self.assertTrue(batches[2][1].exists());self.assertTrue(batches[3][1].exists())
 def test_archive_clean_idempotent(self):
  self.four();self.assertEqual(self.clean()['removed_files'],2);self.assertEqual(self.clean()['removed_files'],0)
 def test_unknown_release_state_preserves_all_artifacts(self):
  self.four();self.pin(status='installing');self.assertFalse(self.rows())
 def test_missing_current_record_preserves_all_artifacts(self):
  self.four();self.p.artifact_records['api'].unlink();self.assertFalse(self.rows())
 def test_current_record_changed_after_plan_rejected(self):
  self.four();row=self.rows()[0];self.pin(source_commit_sha='%040x'%1)
  self.assertRaises(m.Unsafe,m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc));self.assertTrue(Path(row['path']).exists())
 def test_registry_changed_after_plan_rejected(self):
  self.four();row=self.rows()[0];self.p.registry.write_text(self.p.registry.read_text()+' ')
  self.assertRaises(m.Unsafe,m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc))
 def test_busy_release_lock_skips_artifacts_not_cache(self):
  self.four();cache=self.p.cache/'a.bin';cache.write_text('cache');lock=self.p.artifact_locks['api'][0][0]
  import fcntl
  fd=os.open(lock,os.O_RDWR);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   result=self.clean();self.assertEqual(result['artifact_eligible_files'],0);self.assertEqual(result['removed_files'],1)
  finally:os.close(fd)
 def test_missing_release_lock_skips_artifacts(self):
  self.four();self.p.artifact_locks['api'][0][0].unlink();self.assertEqual(self.clean()['removed_files'],0)
 def test_plan_has_no_mutation(self):
  self.four()
  with mock.patch.object(m.time,'time',return_value=self.now):result=m.run(self.p,'plan')
  self.assertEqual(result['artifact_eligible_files'],2);self.assertEqual(result['removed_files'],0);self.assertFalse(self.p.audit.exists())
 def test_high_space_is_noop(self):
  self.four()
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=10*1024**3):result=m.run(self.p,'clean')
  self.assertEqual(result['removed_files'],0)
 def test_web_runtime_have_separate_retention_slots(self):
  a=self.four('web');b=self.four('runtime');self.assertEqual(len(self.rows()),4)
  self.assertEqual(self.clean()['removed_files'],4)
 def test_runtime_rollback_source_preserved(self):
  batches=self.four('runtime');pin=self.p.runtime_backup_base/'20261106-fixture'
  (pin/'current.json').write_text(json.dumps({'status':'verified-active','sourceCommit':'%040x'%1}))
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_runtime_missing_rollback_record_protects_all(self):
  self.four('runtime');(self.p.runtime_backup_base/'20261106-fixture/current.json').unlink()
  self.assertFalse(self.rows())
 def test_dependencies_and_artifacts_together(self):
  self.four();task,f=self.batch(5,dependencies=True);self.assertEqual(len(self.rows()),4)
  self.assertEqual(self.clean()['removed_files'],4);self.assertTrue(f.exists());self.assertTrue((task/'web/package.json').exists())
 def test_invalid_artifact_scope_or_api_missing_payload_digest_rejected(self):
  task=self.temp/'cyf-invalid';task.mkdir();(task/'data.jar').write_text('payload')
  for rel in ('../escape.jar','source/data.jar','backup.tgz','package/state.tar.gz','receipt.json'):
   self.assertRaises(m.Unsafe,m.mark_complete,self.p,task,[],[rel],'api','a'*40,'b'*40,'c'*64)
  self.assertRaises(m.Unsafe,m.mark_complete,self.p,task,[],['data.jar'],'api','a'*40,'b'*40)
 def test_mark_active_removes_completion_so_artifacts_not_inferred(self):
  batches=self.four();m.atomic_json(self.p.registry,{'version':1,'tasks':[]});self.assertFalse(self.rows())
 def test_process_scan_failure_blocks_mutation(self):
  batches=self.four()
  with mock.patch.object(m.proc,'snapshot',side_effect=PermissionError('incomplete scan')):self.assertRaises(PermissionError,self.clean)
  self.assertTrue(all(f.exists() for t,f in batches))

 def native_pin(self,component,commit):
  self.pin(component,schema_version={'api':4,'web':2}[component],source_kind='LOCAL',source={'commit':commit,'tree':'d'*40,'buildId':'local-fixture'})
  p=self.p.artifact_records[component];d=json.loads(p.read_text());d.pop({'api':'source_commit_sha','web':'commit'}[component]);p.write_text(json.dumps(d))
 def test_native_api_source_and_rollback_remain_protected(self):
  batches=self.four();self.native_pin('api','%040x'%1)
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_native_web_source_remains_protected(self):
  batches=self.four('web');self.native_pin('web','%040x'%1)
  self.assertEqual([r['path'] for r in self.rows()],[str(batches[1][1])])
 def test_native_unknown_identity_preserves_all(self):
  self.four();self.native_pin('api','bad')
  self.assertFalse(self.rows())
 def test_native_unfinished_preserves_all(self):
  self.four();self.native_pin('api','b'*40);p=self.p.artifact_records['api'];d=json.loads(p.read_text());d['phase']='installing';p.write_text(json.dumps(d))
  self.assertFalse(self.rows())

 def test_combined_component_can_register_exact_final_package(self):
  task=self.temp/'cyf-combined-batch/api';(task/'package').mkdir(parents=True);(task/'package/api.tgz').write_bytes(b'package')
  result=m.mark_complete(self.p,task,[],['package/api.tgz'],'api','a'*40,'b'*40,'c'*64)
  self.assertEqual(m.read_registry(self.p)[0]['task_root'],str(task))
 def test_combined_unknown_nested_child_rejected(self):
  task=self.temp/'cyf-combined-batch/source';task.mkdir(parents=True)
  with self.assertRaises(m.Unsafe):m.task_root(self.p,task)
 def test_combined_parent_keep_protects(self):
  task=self.temp/'cyf-combined-batch/api';task.mkdir(parents=True);(task.parent/'.keep').touch()
  with self.assertRaises(m.Unsafe):m.task_root(self.p,task)
 def test_combined_parent_mount_protects(self):
  task=self.temp/'cyf-combined-batch/api';task.mkdir(parents=True)
  self.p.mountinfo.write_text('1 0 0:0 / / rw - ext4 /dev/x rw\n2 1 0:0 / %s rw - ext4 /dev/x rw\n'%task.parent)
  with self.assertRaises(m.Unsafe):m.task_root(self.p,task)

if __name__=='__main__':unittest.main(verbosity=2)
