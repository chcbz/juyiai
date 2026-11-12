// Runs after npm test/build. Publish only dist; keep test reports in Flow artifacts.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root='_cyf_web_develop_ci_export', files=[];
function walk(dir){for(const e of fs.readdirSync(path.join(root,'dist',dir),{withFileTypes:true})){
 const relative=path.posix.join(dir,e.name), p=path.join(root,'dist',relative);
 if(e.isDirectory())walk(relative);
 else if(e.isFile()){const data=fs.readFileSync(p);files.push({path:relative,size:data.length,sha256:crypto.createHash('sha256').update(data).digest('hex')});}
 else throw Error('Unsupported dist entry: '+relative);
}}
walk('');
if(!files.some(x=>x.path==='index.html'))throw Error('Missing site entry');
const packageVersion=JSON.parse(fs.readFileSync('package.json','utf8')).version;
const m={schema_version:1,pipeline_id:process.env.PIPELINE_ID,run_id:process.env.BUILD_NUMBER,branch:process.env.CI_COMMIT_REF_NAME,commit:process.env.CI_COMMIT_SHA,package_version:packageVersion,files};
if(m.pipeline_id!=='4403172'||m.branch!=='develop'||!/^[1-9][0-9]*$/.test(m.run_id)||!/^[0-9a-f]{40,64}$/.test(m.commit))throw Error('Wrong Flow identity');
fs.writeFileSync(path.join(root,'release.json'),JSON.stringify(m)+'\n');
console.log('CYF_WEB_ARTIFACT '+JSON.stringify({pipeline:m.pipeline_id,run:m.run_id,commit:m.commit,files:files.length}));
