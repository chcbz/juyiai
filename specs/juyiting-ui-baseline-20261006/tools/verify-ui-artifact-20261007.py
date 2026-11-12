"""Read-only same-run Flow artifact integrity and UI test report verification."""
import hashlib,json,os,posixpath,tarfile
from pathlib import Path
from datetime import datetime,timezone
E=Path(__file__).resolve().parents[1]/'evidence/ui-only-20261007'
download=json.loads((E/'flow179-artifact-download.json').read_text())
assert download['pipeline']==4403172 and download['run']==179
p=download['path'];expected_commit='726453950fe934c894be9e602ac72ee1151c9efb';expected_tree='d03c91801fa921027401d817022ff2b85a20929c'
h=hashlib.sha256()
with open(p,'rb') as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
assert h.hexdigest()==download['sha256']
with tarfile.open(p) as t:
    members=t.getmembers();names=[m.name for m in members]
    assert len(names)==len(set(names)),'duplicate entries'
    assert not any(m.name.startswith('/') or '..' in m.name.split('/') or '\\' in m.name or m.issym() or m.islnk() or m.isdev() for m in members),'unsafe archive'
    files=[m for m in members if m.isfile()]
    release=[m for m in files if posixpath.basename(m.name)=='release.json'];assert len(release)==1
    manifest=json.load(t.extractfile(release[0]))
    assert str(manifest['pipeline_id'])=='4403172' and str(manifest['run_id'])=='179' and manifest['branch']=='develop' and manifest['commit']==expected_commit
    commit_members=[m for m in files if posixpath.basename(m.name)=='source-commit.txt'];tree_members=[m for m in files if posixpath.basename(m.name)=='source-tree.txt']
    assert len(commit_members)==1 and len(tree_members)==1
    assert t.extractfile(commit_members[0]).read().decode().strip()==expected_commit
    assert t.extractfile(tree_members[0]).read().decode().strip()==expected_tree
    base=posixpath.dirname(release[0].name);prefix=base+'/dist/'
    actual={m.name[len(prefix):]:m for m in files if m.name.startswith(prefix)};expected={row['path']:row for row in manifest['files']}
    assert len(expected)==len(manifest['files']) and set(actual)==set(expected) and 'index.html' in actual
    for name,m in actual.items():
        fh=hashlib.sha256()
        stream=t.extractfile(m)
        for block in iter(lambda:stream.read(1024*1024),b''):fh.update(block)
        assert m.size==expected[name]['size'] and fh.hexdigest()==expected[name]['sha256'],'dist integrity mismatch'
    reports=[m for m in files if posixpath.basename(m.name)=='mochawesome.json'];assert len(reports)==1
    report=json.load(t.extractfile(reports[0]));stats=report['stats'];assert stats['failures']==0 and stats['passes']>0
    selected=[]
    def walk(node):
        if isinstance(node,dict):
            for case in node.get('tests',[]):
                title=case.get('fullTitle') or case.get('title','')
                if any(key in title for key in ('simple composer more menu','conversation material references','offers version-pinned workspace references inline','keeps conversation actions in the upper toolbar','explains that a material reference needs an established conversation')):
                    selected.append({key:case.get(key) for key in ('title','fullTitle','state','duration')})
            for key in ('results','suites'):
                for child in node.get(key,[]):walk(child)
    walk(report)
    assert selected and all(case['state']=='passed' for case in selected)
    assert any('renders the existing materials slot while plus is closed' in (case['title'] or '') for case in selected)
    assert any('offers version-pinned workspace references inline' in (case['title'] or '') for case in selected)
result={'verifiedAt':datetime.now(timezone.utc).isoformat(),'pipeline':4403172,'run':179,'commit':expected_commit,'tree':expected_tree,'archiveSafety':'PASS; no extraction/installation','artifactBytes':os.path.getsize(p),'artifactSha256':h.hexdigest(),'distFilesVerified':len(actual),'distCoverageExact':True,'testStats':stats,'uiRegressions':selected,'packageVersion':manifest.get('package_version'),'buildOrigin':'aliyun_flow','deployment':False,'onlineAcceptance':'NOT_RUN','overallBusinessAcceptance':'NOT_COMPLETE'}
(E/'flow179-artifact-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('run','commit','artifactSha256','distFilesVerified','testStats','deployment')},ensure_ascii=False))
