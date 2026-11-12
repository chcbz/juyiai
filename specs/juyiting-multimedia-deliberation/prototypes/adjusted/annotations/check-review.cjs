// Lightweight offline-prototype browser check; no product build or Provider calls.
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process'),assert=require('assert'),WebSocket=require('/home/isp/wsps/cyf/web/node_modules/ws');
const root=__dirname;
const profile=fs.mkdtempSync('/var/tmp/cyf-prototype-chromium-');const downloads=path.join(profile,'downloads');fs.mkdirSync(downloads);
const child=cp.spawn('/usr/bin/chromium-browser',['--headless','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let ws,id=0;const pending=new Map(),errors=[],checks=[],layouts=[];const mark=(name,details)=>checks.push({name,pass:true,details});
async function call(method,params={}){const n=++id;return new Promise((resolve,reject)=>{pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});}
async function evalJS(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function click(selector){await evalJS(`(()=>{const x=document.querySelector(${JSON.stringify(selector)});if(!x)throw Error('missing '+${JSON.stringify(selector)});x.click();return true})()`);await delay(65);}
async function viewport(w,h){await call('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:1,mobile:w<721});}
async function navigate(page){await evalJS(`go(${JSON.stringify(page)})`);await delay(100);}
async function capture(name){await delay(100);const shot=await call('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(path.join(root,'screenshots',name+'.png'),Buffer.from(shot.data,'base64'));}
(async()=>{let port;for(let i=0;i<150;i++){if(fs.existsSync(path.join(profile,'DevToolsActivePort'))){port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];break;}await delay(100);}const targets=await fetch('http://127.0.0.1:'+port+'/json').then(r=>r.json());ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.once('open',r));ws.on('message',data=>{const x=JSON.parse(data);if(x.id&&pending.has(x.id)){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(Error(JSON.stringify(x.error))):p.resolve(x.result);}if(x.method==='Runtime.exceptionThrown')errors.push(x.params.exceptionDetails.text);});await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://*']});await viewport(1440,1000);await call('Page.navigate',{url:(process.env.PROTOTYPE_ORIGIN||'http://127.0.0.1:35111')+'/adjusted/annotations/index.html#chat-result'});await delay(700);



const results=[];
for(const width of [1440,390,320]){
 await viewport(width,width===1440?1000:900);
 for(const device of ['desktop','mobile']){
  await click('#'+device);
  const ids=await evalJS('pages.map(p=>p.id)');
  for(const id of ids){
   await evalJS(`scene.value=${JSON.stringify(id)};render()`);await delay(70);
   const r=await evalJS(`({id:scene.value,device,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,imageReady:screen.complete&&screen.naturalWidth>0,marks:document.querySelectorAll('.mark').length,notes:notes.children.length,contained:[...document.querySelectorAll('.mark')].every(e=>{const b=e.getBoundingClientRect(),p=stage.getBoundingClientRect();return b.left>=p.left-1&&b.right<=p.right+1&&b.top>=p.top-1&&b.bottom<=p.bottom+1})})`);
   assert(r.imageReady,JSON.stringify(r));assert.equal(r.marks,r.notes);assert(r.contained,JSON.stringify(r));assert(r.scrollWidth<=width+1,JSON.stringify(r));results.push(r);
  }
 }
 await evalJS("scene.value='chat-result';render()");await click(width===1440?'#desktop':'#mobile');await capture('review-'+width);
}
await click('.mark button');assert.equal(await evalJS('document.querySelectorAll(".selected").length'),2);await click('#marks');assert(await evalJS('overlay.hidden'));await click('#marks');assert(!await evalJS('overlay.hidden'));const before=await evalJS('scene.value');await click('#next');assert.notEqual(await evalJS('scene.value'),before);await click('#prev');assert.equal(await evalJS('scene.value'),before);assert.equal(errors.length,0);
fs.writeFileSync(path.join(root,'review-checks.json'),JSON.stringify({kind:'read-only-prototype-annotations',screens:24,views:results.length,results,errors,productSourceChanged:false},null,2)+'\n');console.log(JSON.stringify({views:results.length,errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{if(ws?.readyState===WebSocket.OPEN){try{await call('Browser.close');}catch{}ws.close();}if(child.exitCode===null)child.kill('SIGTERM');await delay(400);if(child.exitCode!==null)fs.rmSync(profile,{recursive:true,force:true});});
