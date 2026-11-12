// Read-only, task-owned CDP targets only; never closes the shared browser.
import WebSocket from '/home/isp/wsps/cyf/web/node_modules/ws/index.js';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const dir=process.env.PROTOTYPE_EVIDENCE_DIR||'/home/isp/wsps/cyf/specs/juyiting-ui-baseline-20261006/evidence/production-diff-20261007';
const base='http://127.0.0.1:'+(process.env.CDP_PORT||'39155');
const op=process.argv[2],arg=process.argv[3]||'';
let owned=JSON.parse(await fs.readFile(dir+'/owned-targets.json','utf8').catch(()=>'{"targets":[]}'));
if(op==='create'){
 const t=await(await fetch(base+'/json/new?about:blank',{method:'PUT'})).json();
 owned.targets.push({cdpPort:process.env.CDP_PORT||'39155',id:t.id,webSocketDebuggerUrl:t.webSocketDebuggerUrl,createdAt:new Date().toISOString(),scope:arg});
 await fs.writeFile(dir+'/owned-targets.json',JSON.stringify(owned,null,2));console.log(t.id);process.exit(0);
}
const t=owned.targets.find(x=>x.scope===(process.env.SCOPE||'production'));if(!t)throw Error('no owned target');
if(op==='close'){console.log(await(await fetch('http://127.0.0.1:'+(t.cdpPort||'39155')+'/json/close/'+t.id)).text());process.exit(0);}
const ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.once('open',r);ws.once('error',j)});
let seq=0;const pending=new Map(),network=[],responses=[],errors=[];
ws.on('message',b=>{const m=JSON.parse(b);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timer);m.error?p.j(Error(JSON.stringify(m.error))):p.r(m.result)}}
 if(m.method==='Network.requestWillBeSent'){try{const u=new URL(m.params.request.url);if(u.protocol==='https:'||u.protocol==='http:')network.push({method:m.params.request.method,url:u.origin+u.pathname})}catch{}}
 if(m.method==='Network.responseReceived'){try{const u=new URL(m.params.response.url);if(u.protocol==='https:'||u.protocol==='http:')responses.push({url:u.origin+u.pathname,status:m.params.response.status})}catch{}}
 if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);
});
const call=(method,params={})=>new Promise((r,j)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);j(Error('CDP diagnostic timeout '+method))},45000);pending.set(id,{r,j,timer});ws.send(JSON.stringify({id,method,params}))});
const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
await call('Runtime.enable');await call('Page.enable');await call('Network.enable');
try{
 if(op==='nav'){await call('Page.navigate',{url:arg});await delay(5500);}
 if(op==='eval')console.log(JSON.stringify(await ev(arg),null,2));
 if(op==='view'){const width=+arg;await call('Emulation.setDeviceMetricsOverride',{width,height:width<721?844:1000,deviceScaleFactor:1,mobile:width<721});await delay(400);}
 if(op==='click'||op==='text'){
  let selector=arg;
  if(op==='text'){await ev(`(()=>{const candidates=[...document.querySelectorAll('button,a,[role=button]')].filter(e=>e.innerText.trim()===${JSON.stringify(arg)}&&e.getBoundingClientRect().width>0&&!e.disabled);if(!candidates.length)throw Error('Button not found '+${JSON.stringify(arg)});document.querySelectorAll('[data-cyf-inspect-action]').forEach(e=>e.removeAttribute('data-cyf-inspect-action'));const e=candidates[candidates.length-1];e.setAttribute('data-cyf-inspect-action','current');})()`);selector='[data-cyf-inspect-action=current]';}
  const pos=await ev(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e||e.disabled)throw Error('Missing or disabled '+${JSON.stringify(arg)});e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);if(!r.width||!r.height||!e.contains(hit))throw Error('Not visible or obscured '+${JSON.stringify(arg)});return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  await call('Input.dispatchMouseEvent',{type:'mousePressed',...pos,button:'left',clickCount:1});await call('Input.dispatchMouseEvent',{type:'mouseReleased',...pos,button:'left',clickCount:1});await delay(1800);
 }
 if(op==='snap'){
 await call('Page.bringToFront');await delay(250);
 const result=await ev(`(()=>{const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};const box=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,w:r.width,h:r.height,color:s.color,background:s.backgroundColor,borderRadius:s.borderRadius,fontSize:s.fontSize,strokeWidth:s.strokeWidth}};return {url:location.origin+location.pathname+location.hash,title:document.title,width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,text:document.body.innerText,buttons:[...document.querySelectorAll('button,a,[role=button]')].filter(visible).map(e=>({tag:e.tagName,text:e.innerText,label:e.getAttribute('aria-label'),title:e.title,cls:e.className,disabled:!!e.disabled,href:e.getAttribute('href')?.split('?')[0],box:box(e),icons:[...e.querySelectorAll('svg,i')].map(i=>({tag:i.tagName,cls:i.className,box:box(i)}))})),inputs:[...document.querySelectorAll('textarea,input,select')].filter(visible).map(e=>({type:e.type,placeholder:e.placeholder,cls:e.className,disabled:e.disabled,box:box(e)})),tabs:[...document.querySelectorAll('.overview-tabs button,.library-tabs button,.case-tabs button,.treasure-tabs button')].map(e=>({text:e.innerText,cls:e.className,box:box(e)})),scripts:[...document.scripts].map(e=>e.src).filter(Boolean),styles:[...document.querySelectorAll('link[rel=stylesheet]')].map(e=>e.href)}})()`);
 await fs.writeFile(dir+'/'+arg+'.json',JSON.stringify({at:new Date().toISOString(),result},null,2));const shot=await call('Page.captureScreenshot',{format:'png',fromSurface:false,captureBeyondViewport:false});await fs.writeFile(dir+'/'+arg+'.png',Buffer.from(shot.data,'base64'));console.log(JSON.stringify({name:arg,text:result.text.slice(0,14000),buttons:result.buttons.map(b=>({text:b.text,label:b.label,cls:b.cls,disabled:b.disabled})),tabs:result.tabs,width:result.width,scrollWidth:result.scrollWidth},null,2));
 }
 if(op==='assets'){
 const assets=await ev(`(async()=>{const names=[...new Set([...document.scripts].map(e=>e.src).concat(performance.getEntriesByType('resource').map(e=>e.name)))].filter(x=>x.startsWith(location.origin)&&/\\.(js|css)(?:$|\\?)/.test(x));const out=[];for(const name of names){const r=await fetch(name,{cache:'no-cache'});const buf=await r.arrayBuffer();const sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',buf))].map(x=>x.toString(16).padStart(2,'0')).join('');out.push({path:new URL(name).pathname,status:r.status,bytes:buf.byteLength,sha256:sha})}return out})()`);await fs.writeFile(dir+'/production-loaded-assets.json',JSON.stringify({at:new Date().toISOString(),scope:'actually loaded asset URLs freshly read back; not deployment-control attestation',assets},null,2));console.log(JSON.stringify(assets,null,2));
 }
}catch(e){console.error(e.stack);process.exitCode=1;}finally{await fs.appendFile(dir+'/actions.jsonl',JSON.stringify({at:new Date().toISOString(),scope:process.env.SCOPE||'production',op,arg:op==='eval'?'diagnostic DOM evaluation':arg,network,responses,errors,success:!process.exitCode})+'\n');ws.close();}
