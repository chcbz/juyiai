#!/usr/bin/python3
"""Isolated automatic unregistered output retention, no live filesystem cleanup."""
import hashlib,io,json,os,tarfile,time,unittest
from pathlib import Path
from unittest import mock
import test_rebuildable_cache_cleanup as fixtures
m=fixtures.m

class DiscoveredTests(unittest.TestCase):
 setUp=fixtures.ArtifactTests.setUp
 tearDown=fixtures.ArtifactTests.tearDown
 pin=fixtures.ArtifactTests.pin
 def batch(self,i,component='api',evidence=b'{"test":"original receipt"}'):
  self.p.discovery_bases=[self.temp]
  task=self.temp/('cyf-auto'+str(i));(task/'package').mkdir(parents=True)
  (task/'result.json').write_text(json.dumps({'status':'RUNNING','source':{'commit':'%040x'%i,'tree':'%040x'%(i+100)}}))
  p=task/'package'/(component+'.tgz')
  with tarfile.open(str(p),'w:gz') as t:
   for name,data in [('application.jar' if component=='api' else 'payload/app.js',('payload'+str(i)).encode()),('receipt.json',evidence),('test-results/TEST-original.xml',b'<testsuite/>')]:
    info=tarfile.TarInfo(name);info.size=len(data);t.addfile(info,io.BytesIO(data))
  return task,p
 def four(self,component='api'):return [self.batch(i,component) for i in range(1,5)]
 def perform(self,mode='clean',now=None):
  with mock.patch.object(m.time,'time',return_value=self.now if now is None else now),mock.patch.object(m,'free_bytes',return_value=100*1024**3):return m.run(self.p,mode,artifacts_only=True)
 def rows(self):return m.collect_discovered(self.p,m.proc.snapshot(self.p.proc),self.now,24)[0]
 def test_unregistered_old_outputs_removed_without_claiming_task_completion(self):
  batches=self.four();result=self.perform()
  self.assertEqual(result['removed_files'],2);self.assertEqual(result['discovered_eligible_files'],2)
  self.assertFalse(self.p.registry.exists());self.assertTrue(all(p.exists() for t,p in batches[2:]));self.assertTrue(all(t.exists() and (t/'result.json').exists() for t,p in batches))
 def test_recent_and_two_latest_stages_retained(self):
  batches=self.four();self.assertEqual(self.perform(now=time.time())['removed_files'],0)
  self.assertEqual(len(self.rows()),2);self.assertTrue(all(p.exists() for t,p in batches))
 def test_plan_is_read_only_even_for_embedded_evidence(self):
  batches=self.four();r=self.perform('plan');self.assertEqual(r['eligible_files'],2)
  self.assertFalse(self.p.state.exists());self.assertFalse(self.p.audit.exists());self.assertTrue(all(p.exists() for t,p in batches))
 def test_embedded_evidence_preserved_exactly_before_unlink(self):
  batches=self.four();sha=hashlib.sha256(batches[0][1].read_bytes()).hexdigest();self.perform()
  dest=self.p.state/'retained-artifact-evidence'/sha;index=json.loads((dest/'index.json').read_text())
  self.assertEqual(index['documents']['receipt.json'],hashlib.sha256(b'{"test":"original receipt"}').hexdigest())
  self.assertEqual((dest/(hashlib.sha256(b'receipt.json').hexdigest()+'.document')).read_bytes(),b'{"test":"original receipt"}')
  self.assertIn('test-results/TEST-original.xml',index['documents'])
 def test_current_source_pins_entire_stage(self):
  batches=self.four();self.pin(source_commit_sha='%040x'%1);self.perform()
  self.assertTrue(batches[0][1].exists());self.assertFalse(batches[1][1].exists())
 def test_rollback_payload_pins_even_without_registered_metadata(self):
  batches=self.four();self.pin(previous_sha256=hashlib.sha256(b'payload1').hexdigest());self.perform()
  self.assertTrue(batches[0][1].exists());self.assertFalse(batches[1][1].exists())
 def test_archive_hash_and_path_pins(self):
  batches=self.four();self.pin(artifact_sha256=hashlib.sha256(batches[0][1].read_bytes()).hexdigest(),package_path=str(batches[1][1]));self.assertFalse(self.rows())
 def test_unknown_or_missing_release_state_preserves_component(self):
  batches=self.four();self.pin(status='installing');self.assertFalse(self.rows());self.p.artifact_records['api'].unlink();self.assertFalse(self.rows())
 def test_keep_marker_active_task_and_hardlinks_protected(self):
  batches=self.four();(batches[0][0]/'.keep').symlink_to('missing');(self.p.proc/'123/cwd').symlink_to(batches[1][0]);self.perform();self.assertTrue(all(p.exists() for t,p in batches))
 def test_hardlinked_and_symlinked_packages_are_never_deleted(self):
  batches=self.four();os.link(str(batches[0][1]),str(self.base/'external'));batches[1][1].unlink();batches[1][1].symlink_to(batches[2][1]);self.perform();self.assertTrue(all(p.exists() for t,p in batches))
 def test_build_lock_busy_or_missing_protects_all_outputs(self):
  import fcntl
  batches=self.four();lock=self.base/'build.lock';lock.write_text('');lock.chmod(0o644);self.p.build_locks=[(lock,0o644)]
  fd=os.open(str(lock),os.O_RDWR)
  try:
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);self.assertEqual(self.perform()['removed_files'],0)
  finally:os.close(fd)
  lock.unlink();self.assertEqual(self.perform()['removed_files'],0);self.assertTrue(all(p.exists() for t,p in batches))
 def test_corrupt_archive_not_deleted(self):
  batches=self.four();batches[0][1].write_bytes(b'not an archive');self.perform();self.assertTrue(batches[0][1].exists())
 def test_embedded_path_traversal_refused(self):
  batches=self.four()
  with tarfile.open(str(batches[0][1]),'w:gz') as t:
   info=tarfile.TarInfo('../receipt.json');info.size=1;t.addfile(info,io.BytesIO(b'x'))
  self.perform();self.assertTrue(batches[0][1].exists())
 def test_evidence_symlink_sink_preserves_original_package(self):
  batches=self.four();self.p.state.mkdir();(self.p.state/'retained-artifact-evidence').symlink_to(self.base)
  self.assertEqual(self.perform()['removed_files'],0);self.assertTrue(all(p.exists() for t,p in batches))
 def test_package_replaced_after_plan_refused(self):
  self.four();row=self.rows()[0];p=Path(row['path']);p.write_bytes(b'replaced');self.assertRaises(m.Unsafe,m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc));self.assertTrue(p.exists())
 def test_stage_identity_changed_after_plan_refused(self):
  self.four();row=self.rows()[0];(Path(row['task'])/'result.json').write_text('{}');self.assertRaises(m.Unsafe,m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc))
 def test_generated_api_classes_and_jars_removed_not_source_logs_or_caches(self):
  batches=self.four()
  for task,p in batches:
   for rel in ('build/jia/agent/classes/java/main/A.class','build/jia/starter/libs/old.jar','build/jia/agent/test-results/TEST.xml','source.java','gradle.log','node_modules/a.js'):
    f=task/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'generated fixture')
  self.assertEqual(self.perform()['removed_files'],6)
  for task,p in batches:
   for rel in ('build/jia/agent/test-results/TEST.xml','source.java','gradle.log','node_modules/a.js'):self.assertTrue((task/rel).exists())
 def test_all_reusable_caches_survive_low_disk_and_completion_registration(self):
  task=self.temp/'cyf-deps';(task/'web/node_modules').mkdir(parents=True)
  for name in ('package.json','package-lock.json'):(task/'web'/name).write_text('{}')
  dep=task/'web/node_modules/a.js';dep.write_text('cache');m.mark_complete(self.p,task,['web/node_modules'])
  cache=self.p.cache/'old.bin';cache.write_text('cache')
  with mock.patch.object(m.time,'time',return_value=self.now),mock.patch.object(m,'free_bytes',return_value=0):r=m.run(self.p,'clean')
  self.assertTrue(dep.exists());self.assertTrue(cache.exists());self.assertTrue(r['caches_preserved']);self.assertEqual(r['removed_files'],0)
 def test_outside_explicit_bases_and_unknown_filenames_not_scanned(self):
  self.four();outside=self.base/'other';outside.mkdir();(outside/'api.tgz').write_bytes(b'keep')
  t=self.temp/'cyf-unknown';t.mkdir();(t/'result.json').write_text('{}');(t/'backup.tgz').write_bytes(b'keep');self.perform();self.assertTrue((outside/'api.tgz').exists());self.assertTrue((t/'backup.tgz').exists())
 def test_missing_producer_metadata_preserves_unknown_directory(self):
  batches=self.four();(batches[0][0]/'result.json').unlink();self.perform();self.assertTrue(batches[0][1].exists())
 def test_process_scan_incomplete_blocks_all_mutation(self):
  batches=self.four();(self.p.proc/'123/maps').write_text('malformed')
  self.assertRaises(ValueError,self.perform);self.assertTrue(all(p.exists() for t,p in batches))
 def test_registered_path_not_reinterpreted_as_unregistered(self):
  batches=self.four();task,p=batches[0];m.mark_complete(self.p,task,[],['package/api.tgz'],'api','1'*40,'2'*40,'3'*64)
  self.assertNotIn(str(p),[r['path'] for r in self.rows()])
 def test_audit_symlink_blocks_all_mutations(self):
  batches=self.four();self.p.audit.parent.mkdir();self.p.audit.symlink_to(self.base/'outside')
  self.assertRaises(OSError,self.perform);self.assertTrue(all(p.exists() for t,p in batches))
 def test_parent_symlink_or_new_mount_after_plan_refused(self):
  self.four();row=self.rows()[0];task=Path(row['task']);task.rename(task.with_name(task.name+'-original'));task.symlink_to(task.with_name(task.name+'-original'))
  self.assertRaises((m.Unsafe,OSError),m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc))
 def test_registered_and_readonly_legacy_cache_rows_cannot_delete_cache(self):
  cache=self.p.cache/'old';cache.write_text('reusable')
  row=m.collect(self.p,m.proc.snapshot(self.p.proc),self.now)[0][0]
  self.assertRaises(m.Unsafe,m.unlink_row,self.p,row,m.proc.snapshot(self.p.proc));self.assertTrue(cache.exists())
 def test_queued_builder_takes_lock_at_existing_audit_batch_boundary(self):
  import fcntl
  batches=self.four();task=batches[0][0]
  for i in range(60):
   p=task/('build/jia/agent/classes/java/main/A%d.class'%i);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'class')
  for other,package in batches[1:]:os.utime(str(package),None)
  lock=self.base/'build.lock';lock.write_text('');lock.chmod(0o644);self.p.build_locks=[(lock,0o644)]
  contender=os.open(str(lock),os.O_RDWR)
  try:
   with mock.patch.object(m.time,'sleep',side_effect=lambda _:fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)):
    result=self.perform()
   self.assertEqual(result['removed_files'],50);self.assertEqual(result['deferred_files'],12)
   self.assertIn('build took priority',result['scope_skips'][-1]['reason'])
  finally:os.close(contender)
 def test_idempotence(self):
  self.four();self.assertEqual(self.perform()['removed_files'],2);self.assertEqual(self.perform()['removed_files'],0)

if __name__=='__main__':unittest.main(verbosity=2)
