// Local document checks only; Chromium report is separate and authoritative for layout.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
const dir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../prototype')
const evidence=process.env.PROTOTYPE_EVIDENCE_DIR||path.resolve(dir,'../evidence/ui-sync-20261013');fs.mkdirSync(evidence,{recursive:true})
const require=createRequire(path.resolve(process.argv[2]||'/home/isp/wsps/cyf/web/package.json'))
const {JSDOM}=require('jsdom'),results=[]
const pages=['home','tasks','create','agents','detail','chat','private','public','workspace','mine','library','messages','catalog','map','file','reader','help','account','results']
const scenarios=['ready','empty','waiting','streaming','error','recording','voice-review','results','completed','create-failure','create-unknown','reply-failure','accept-unknown','accept-failure','independent-roots','cancel-ready','cancel-unknown','cancelled','history-error','runtime-ready','runtime-existing','runtime-unknown','runtime-invalid']
function create(page,width=390,scenario='ready') {
 const dom=new JSDOM(fs.readFileSync(dir+'/index.html','utf8'),{url:`http://localhost/?scenario=${scenario}#${page}`,runScripts:'outside-only',pretendToBeVisual:true})
 Object.defineProperty(dom.window.HTMLElement.prototype,'innerText',{get(){return this.textContent},set(v){this.textContent=v}});
 dom.window.HTMLElement.prototype.scrollTo=function(){};
 dom.window.structuredClone=structuredClone;dom.window.innerWidth=width;dom.window.innerHeight=844
 dom.window.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
 dom.window.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');this.dispatchEvent(new dom.window.Event('close'))}
 dom.window.eval([...dom.window.document.querySelectorAll('script[src]')].map(s=>fs.readFileSync(path.join(dir,s.getAttribute('src').split('?')[0]),'utf8')).join('\n')+'\nwindow.test={go,accept,state,conversation,submitRequest,visibleMatterStatuses};')
 return dom
}
function click(d,s){const n=d.window.document.querySelector(s);assert(n,s);assert(!n.disabled,s);n.click()}
for(const width of [320,390,1440])for(const p of pages){const d=create(p,width);assert(d.window.document.title.includes('界面优化基准'));assert.equal(d.window.document.querySelectorAll('.discussion-brief').length,0);for(const el of d.window.document.querySelectorAll('[src]')){const src=el.getAttribute('src').split('?')[0];if(!/^(data:|blob:|https?:)/.test(src))assert(fs.existsSync(path.join(dir,src)),p+': '+src)}results.push({page:p,width,pass:true});d.window.close()}
for (const width of [320,390,1440]) {
 const d=create('chat',width,'submission-failure'),q=s=>d.window.document.querySelector(s),st=d.window.test.state;
 const notice=q('.submission-notice');assert(notice);assert.equal(notice.getAttribute('role'),'status');
 assert(notice.closest('.hall-message.AGENT'));assert(!notice.closest('.composer-submit'));
 assert(notice.textContent.includes('原答复和文件已保留'));assert.equal(st.delivery.length,0);
 assert.equal(st.task.phase,'进行中');assert.equal(st.agent.name,'吴用');
 assert(q('.unified-message-result'));assert(!q('.submission-notice button'));assert(!q('.composer-textarea').disabled);
 assert(!q('[data-action=complete-acceptance-review]'));assert(!q('[data-action=finish]'));
 results.push({interaction:'submission failure preserves original answer and fixed candidate, no acceptance or retry write',width,pass:true});d.window.close();
}
for(const s of scenarios){const d=create(s==='completed'?'detail':'chat',390,s);if(s!=='completed'){for(const cls of ['composer-more','voice-start','composer-send'])assert(d.window.document.querySelector('.composer-input-area .'+cls));for(const title of ['重取回话','话头记录','另起话头'])assert(d.window.document.querySelector(`[aria-label="${title}"]`))}results.push({scenario:s,pass:true});d.window.close()}
{
 const d=create('chat'),q=s=>d.window.document.querySelector(s);assert(q('.composer-more + .composer-attach'));assert(q('.composer-inline-voice + .composer-send'));click(d,'.composer-more');assert(!q('.composer-more-panel .composer-add-materials'));click(d,'[data-action=ui-settings]');assert(q('.voice-disclosure').textContent.includes('AI'));assert(!q('.voice-settings').textContent.includes('识别语言'));click(d,'[data-action=complete-materials]');click(d,'[data-action=picker-select][data-id=ref-brief]');click(d,'[data-action=picker-stage]');click(d,'[data-action=confirm-materials]');assert(q('.composer-submit').textContent.includes('活动说明'));
 click(d,'[data-action=complete-history]');assert(q('.baseline-history'));click(d,'[data-action=complete-history]');click(d,'[data-action=complete-voice]');click(d,'[data-action=complete-voice-stop]');q('.baseline-voice-status textarea').value='测试转写';click(d,'[data-action=complete-voice-append]');assert(q('.composer-textarea').value.includes('测试转写'));results.push({interaction:'optimized settings/materials/history/voice',pass:true});d.window.close()
}
{
 const d=create('chat',390,'results');assert.equal(d.window.document.querySelectorAll('.mmd-result').length,4);d.window.test.go('detail');d.window.test.accept();click(d,'[data-action=complete-acceptance-review]');assert.equal(d.window.document.querySelectorAll('dialog input[type=checkbox]').length,0);click(d,'[data-action=finish]');await new Promise(r=>setTimeout(r,750));assert(d.window.test.state.task.complete);assert.equal(d.window.test.state.operation.writes,1);results.push({interaction:'single acceptance and read-only state',pass:true});d.window.close()
}
const idx=new JSDOM(fs.readFileSync(dir+'/pages.html','utf8'));const links=[...idx.window.document.querySelectorAll('a')];assert.equal(links.filter(l=>l.textContent.includes('打开页面')).length,19);assert.equal(links.filter(l=>l.textContent.includes('体验分支')).length,27);for(const l of links){const p=l.getAttribute('href').split(/[?#]/)[0];assert(fs.existsSync(path.resolve(dir,p)),p)}idx.window.close();results.push({index:'19 pages, 27 states, links resolve',pass:true})
for(const f of ['prototype.js','baseline-ui.js','interaction-completion.js'])assert(!/\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(|getUserMedia\s*\(/.test(fs.readFileSync(dir+'/'+f,'utf8')))

for(const scenario of ['cancel-ready','cancel-unknown']){
 const d=create('detail',390,scenario),q=s=>d.window.document.querySelector(s),st=d.window.test.state;
 const before=JSON.stringify(st.task);click(d,'[data-action=complete-cancel]');click(d,'dialog footer [data-action=close-dialog]');assert.equal(JSON.stringify(st.task),before);
 click(d,'[data-action=complete-cancel]');click(d,'[data-action=complete-cancel-confirm]');assert.equal(st.cancellation.writes,1);
 if(scenario==='cancel-unknown'){assert(!st.task.cancelled);click(d,'[data-action=complete-cancel]');assert.equal(st.cancellation.writes,1);assert.equal(st.cancellation.queries,1);}else{assert(st.task.cancelled);click(d,'.matter-results-action');assert(q('.terminal-history-actions'));assert(!q('[data-action=finish]'));assert(!q('[data-action=workspace]'));}
 results.push({interaction:scenario,pass:true});d.window.close();
}
for(const scenario of ['runtime-ready','runtime-existing','runtime-unknown','runtime-invalid']){
 const d=create('catalog',390,scenario),q=s=>d.window.document.querySelector(s),st=d.window.test.state;
 assert(q('[data-action=complete-runtime-register]').disabled);
 if(scenario!=='runtime-existing')click(d,'[data-action=complete-runtime-import]');
 if(scenario==='runtime-invalid')assert(q('[data-action=complete-runtime-register]').disabled);
 else {if(scenario!=='runtime-existing')click(d,'[data-action=complete-runtime-register]');click(d,'[data-action=complete-runtime-query]');assert(q('[data-action=complete-runtime-register]').disabled);assert.equal(st.runtimeDemo.status,scenario==='runtime-unknown'?'UNKNOWN':scenario==='runtime-existing'?'ACTIVE':'PENDING');}
 click(d,'[data-action=complete-runtime-close]');assert(!q('.runtime-setup'));
 results.push({interaction:scenario,pass:true});d.window.close();
}

{
 const d=create('detail',390,'cancel-ready'),q=s=>d.window.document.querySelector(s),st=d.window.test.state;
 click(d,'[data-action=complete-cancel]');click(d,'[data-action=complete-cancel-confirm]');
 d.window.test.go('chat');assert(q('.composer-textarea').placeholder.includes('已取消'));click(d,'[data-action=complete-history]');assert(q('[data-action=complete-delete-current]').disabled);
 st.agent=null;d.window.test.go('agents');click(d,'.agent-row');assert(!q('[data-action=assign]'));
 st.draft='新需求保留原取消事项';d.window.test.submitRequest();click(d,'[data-action=complete-agent-confirm]');assert(st.task.unified);assert.equal(st.cancellation.writes,0);assert(Object.values(st.matterLibrary).some(ctx=>ctx.task.cancelled));assert(q('.chat-panel'));
 results.push({interaction:'terminal wording, no assign/delete and new-task cancellation isolation',pass:true});d.window.close();
}

{
 const d=create('home'),st=d.window.test.state,q=s=>d.window.document.querySelector(s);
 st.draft='把活动说明整理成一页简报';st.draftFiles=['ref-brief'];d.window.test.submitRequest();click(d,'[data-action=complete-agent-confirm]');assert(st.task.unified);assert(q('.chat-panel'));assert(st.pending);const id=st.task.id;
 assert.equal(st.messages.length,1);assert(!q('[data-mode]'));assert(!q('[data-action=complete-draft-submit]'));
 await new Promise(r=>setTimeout(r,750));assert.equal(st.task.phase,'已有结果');assert.equal(st.outputs.length,1);assert(q('.unified-message-result'));const first=JSON.stringify(st.task.executions[0]);
 click(d,'.unified-message-result [data-action=preview]');assert(q('dialog[open]'));click(d,'dialog [data-action=close-dialog]');
 assert(!q('.unified-message-result [data-action=quote]')); q('.composer-textarea').value='把时间改成明天，重新生成';q('.composer-textarea').dispatchEvent(new d.window.Event('input',{bubbles:true}));q('.composer-submit').dispatchEvent(new d.window.Event('submit',{bubbles:true,cancelable:true}));
 await new Promise(r=>setTimeout(r,750));assert.equal(st.task.id,id);assert.equal(st.task.executions.length,2);assert.equal(st.outputs.length,2);assert.equal(JSON.stringify(st.task.executions[0]),first);assert.equal(st.messages[2].quote,null);assert.equal(q('.hall-messages').querySelectorAll('.unified-message-result').length,2);assert(!q('.composer-textarea').disabled);
 results.push({interaction:'single conversation quick entry/result/preview/natural-language revision retains same matter and old version',pass:true});d.window.close();
}
{
 const d=create('create'),st=d.window.test.state,q=s=>d.window.document.querySelector(s);
 st.draft='帮我';d.window.test.go('create');assert(!q('[data-mode]'));click(d,'[data-action=complete-draft-next]');assert.equal(st.task.phase,'待点将');assert.equal(st.agent,null);assert.equal(st.messages.length,0);click(d,'[data-action=complete-agent-confirm]');const id=st.task.id;
 await new Promise(r=>setTimeout(r,750));assert.equal(st.task.phase,'待你补充');assert.equal(st.outputs.length,0);assert(q('.hall-messages').textContent.includes('最后得到什么结果'));
 q('.composer-textarea').value='整理一份亲子活动方案';q('.composer-textarea').dispatchEvent(new d.window.Event('input',{bubbles:true}));q('.composer-submit').dispatchEvent(new d.window.Event('submit',{bubbles:true,cancelable:true}));await new Promise(r=>setTimeout(r,750));
 assert.equal(st.task.id,id);assert.equal(st.outputs.length,1);assert(q('.unified-message-result'));assert.equal(st.messages.length,4);assert(!q('[data-action=complete-draft-confirm]'));
 d.window.test.go('home');assert(q('.overview-item [data-prototype-page=chat]'));click(d,'.overview-item [data-prototype-page=chat]');assert(q('.chat-panel'));assert.equal(st.task.id,id);
 results.push({interaction:'clarification and supplement yield result in same chat; home continues original conversation',pass:true});d.window.close();
}

{
 const d=create('tasks'),q=s=>d.window.document.querySelector(s);assert(!q('.bounty-panel .task-create-actions'));assert(!q('.bounty-panel .task-create-form'));assert(q('[aria-label="搜索事项"]'));assert(q('[aria-label="刷新事项"]'));click(d,'[data-action=complete-task-refresh]');results.push({interaction:'compact task toolbar without duplicate create form',pass:true});d.window.close();
}
const hashes=Object.fromEntries(['prototype.js','baseline-ui.js','interaction-completion.js','interaction-completion.css','production-ui.css','index.html','pages.html','prototype.css','baseline-ui.css','shared/snapshots.js','assets/hall-base-v3.webp'].map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(dir+'/'+f)).digest('hex')]))
// Four business stages; clarification/failure/unknown stay contextual, not new lifecycle states.
{
 const d=create('chat',390,'ready');
 const checks=d.window.eval(`(()=>{
  const ctx=blankMatterContext();ctx.task={id:'status-matrix',phase:''};
  const rows=[];const record=expected=>rows.push([listedMatterStatus(ctx),expected]);
  record('待点将');ctx.agent={id:'0',name:'宋江'};record('进行中');
  for(const phase of ['待你补充','需核对','失败','受阻','正在处理']){ctx.task.phase=phase;record('进行中');}
  ctx.task.phase='已有结果';ctx.outputs=[{id:'version-1'}];record('进行中');
  ctx.delivery=['missing-version'];record('进行中');ctx.delivery=['version-1'];record('待验收');
  ctx.pending=true;record('进行中');ctx.pending=false;ctx.error='结果未知';record('进行中');ctx.error=null;
  ctx.operation={stage:'unknown'};record('待验收');ctx.task.complete=true;record('已完成');
  ctx.task.cancelled=true;record('已取消');return rows;
 })()`);
 for(const [actual,expected] of checks)assert.equal(actual,expected);
 assert.deepEqual(Array.from(d.window.test.visibleMatterStatuses),['待点将','进行中','待验收','已完成']);
 results.push({interaction:'four stages and fixed delivery readiness, 15 cases',pass:true});d.window.close()
}
const report={checkedOn:'2026-10-19',method:'JSDOM local document/interaction checks, not visual acceptance',status:'PASS',count:results.length,results,sourceHashes:hashes,productAcceptance:false}
fs.writeFileSync(evidence+'/prototype-checks.json',JSON.stringify(report,null,2)+'\n');console.log('PASS '+results.length+' document checks')
