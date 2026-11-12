import pathlib,json,hashlib,tarfile,posixpath,datetime
P=pathlib.Path(__file__).resolve().parents[1]/'evidence/release-1.0.6-20261008';candidate=json.loads((P/'candidate.json').read_text());archive=pathlib.Path(json.loads((P/'artifact.tgz.receipt.json').read_text())['localPath']);assert archive.is_file()
h=hashlib.sha256()
with archive.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
seen=set();dist={};retained={}
with tarfile.open(archive,mode='r|gz') as t:
 for m in t:
  name=m.name[2:] if m.name.startswith('./') else m.name
  if name in ('','.'):assert m.isdir();continue
  name=name.rstrip('/') if m.isdir() else name
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and str(p)==name and (m.isfile() or m.isdir()) and name not in seen
  seen.add(name)
  if m.isdir():continue
  size=0;dg=hashlib.sha256();keep=name in ('release.json','source-commit.txt','source-tree.txt','installer/helper-release.json','mochawesome-report/mochawesome.json');out=[]
  f=t.extractfile(m)
  for b in iter(lambda:f.read(1048576),b''):
   dg.update(b);size+=len(b)
   if keep:out.append(b)
  assert size==m.size
  if name.startswith('dist/'):dist[name[5:]]={'size':size,'sha256':dg.hexdigest()}
  if name=='installer/cyf-web-flow-deploy':assert dg.hexdigest()==candidate['helperSha256']
  if keep:retained[name]=b''.join(out)
m=json.loads(retained['release.json']);assert (str(m['pipeline_id']),str(m['run_id']),m['branch'],m['commit'],m['package_version'])==('4403172','180','develop',candidate['commit'],'1.0.6');assert m['release']=={'version':'1.0.6','commit':candidate['commit']}
assert retained['source-commit.txt'].decode().strip()==candidate['commit'];assert retained['source-tree.txt'].decode().strip()==candidate['tree'];expected={f['path']:{'size':f['size'],'sha256':f['sha256']} for f in m['files']};assert len(expected)==len(m['files']) and dist==expected and 'index.html' in dist
stats=json.loads(retained['mochawesome-report/mochawesome.json'])['stats'];assert stats['failures']==0 and stats['passes']>=3181 and stats['pending']==2
helper=json.loads(retained['installer/helper-release.json']);assert helper['commit']==candidate['commit'] and str(helper['run_id'])=='180' and helper['helper']['sha256']==candidate['helperSha256']
installed=pathlib.Path('/var/lib/cyf-web-flow/downloads/180/package.tgz');dg=hashlib.sha256()
with installed.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):dg.update(b)
assert dg.hexdigest()==h.hexdigest()
result={'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pipeline':4403172,'run':180,'version':'1.0.6','commit':candidate['commit'],'tree':candidate['tree'],'artifactBytes':archive.stat().st_size,'artifactSha256':h.hexdigest(),'archiveSafety':'PASS; no source build or extraction','distFilesVerified':len(dist),'distCoverageExact':True,'testStats':stats,'embeddedHelperSha256':candidate['helperSha256'],'installedFlowDownloadMatchesOriginal':True,'overallBusinessAcceptance':'NOT_COMPLETE'}
(P/'artifact-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(P/'release-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
