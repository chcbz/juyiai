import pathlib,json,hashlib,concurrent.futures,urllib.request,urllib.parse,datetime
P=pathlib.Path(__file__).resolve().parents[1]/'evidence/release-1.0.6-20261008';a=json.loads((P/'artifact-verification.json').read_text());m=json.loads((P/'release-manifest.json').read_text());rp=pathlib.Path('/var/lib/cyf-web-flow/record.json');raw=rp.read_bytes();r=json.loads(raw)
assert (r['run_id'],r['commit'],r['package_version'],r['release_version'],r['status'],r['phase'],r['artifact_sha256'])==('180',m['commit'],'1.0.6','1.0.6','online_verified','online_verified',a['artifactSha256']);assert r['files']==m['files'];site=pathlib.Path('/home/isp/hosts/cyf/web/kit')
def verify(f):
 rel=f['path'];b=(site/rel).read_bytes();assert len(b)==f['size'] and hashlib.sha256(b).hexdigest()==f['sha256']
 url='https://kit.chaoyoufan.cn/'+urllib.parse.quote(rel,safe='/')+'?flow_verify=4403172-180'
 req=urllib.request.Request(url,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache, no-store, max-age=0','Pragma':'no-cache','User-Agent':'cyf-ui-release-online-verification/180'})
 h=hashlib.sha256();size=0
 with urllib.request.urlopen(req,timeout=30) as response:
  assert response.status==200
  for block in iter(lambda:response.read(1048576),b''):h.update(block);size+=len(block);assert size<=f['size']
 assert size==f['size'] and h.hexdigest()==f['sha256'],('PUBLIC_BYTES_MISMATCH',rel)
 return {'path':rel,'size':size,'sha256':h.hexdigest(),'installedBytesMatch':True,'publicHttpsBytesMatch':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(verify,m['files']))
assert raw==rp.read_bytes()
result={'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pipeline':4403172,'run':180,'version':'1.0.6','commit':r['commit'],'tree':a['tree'],'recordStatus':r['status'],'artifactSha256':a['artifactSha256'],'files':len(files),'fullManifestPublicCoverage':True,'installedBytesVerified':True,'publicHttpsBytesVerified':True,'entryAndJuyiHallJSAndCSSVerified':True,'recordUnchanged':True,'overallBusinessAcceptance':'NOT_COMPLETE'}
(P/'online-files.json').write_text(json.dumps(files,indent=2)+'\n');(P/'online-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
