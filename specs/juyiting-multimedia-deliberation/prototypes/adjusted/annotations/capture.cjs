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
(async()=>{let port;for(let i=0;i<150;i++){if(fs.existsSync(path.join(profile,'DevToolsActivePort'))){port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];break;}await delay(100);}const targets=await fetch('http://127.0.0.1:'+port+'/json').then(r=>r.json());ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.once('open',r));ws.on('message',data=>{const x=JSON.parse(data);if(x.id&&pending.has(x.id)){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(Error(JSON.stringify(x.error))):p.resolve(x.result);}if(x.method==='Runtime.exceptionThrown')errors.push(x.params.exceptionDetails.text);});await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://*']});await viewport(1440,1000);await call('Page.navigate',{url:(process.env.PROTOTYPE_ORIGIN||'http://127.0.0.1:35111')+'/adjusted/index.html'});await delay(700);


const scenes=[
 {id:'request',title:'提需求 · 办事首页',page:'home',marks:[['.quick-request-actions','入口合并','取消独立“参考图”，统一为“添加资料（可选）”；不加资料也能开始。'],['.overview-quick-request .mmd-attachments','资料随需求带入','已选资料统一展示，可预览、移除，不区分专门的参考图入口。']]},
 {id:'tasks',title:'事项 · 一个提出需求入口',page:'tasks',marks:[['.task-create-actions','三个入口合一','张榜、起草正式任务、起草交办统一为“提出需求”，不用先理解内部任务类别。']]},
 {id:'create',title:'提需求 · 统一表单',page:'create',marks:[['.task-create-form .mmd','同样统一资料','合并后的需求表单使用同一资料选择方式，不再出现专门的参考图片面板。']]},
 {id:'materials',title:'选择资料',page:'home',setup:"openMaterials('draft')",marks:[['.mmd-files','不只选图片','从工作空间选择图片、文档、音频或文本；参考图只是图片在任务中的用途。'],['dialog footer','选择可取消','确认才更新已选资料；取消保留原选择，没有资料也能继续。']]},
 {id:'agents',title:'点将册',page:'agents',setup:'state.agent=null;renderAgents()',marks:[['.mmd-agent-detail','只显示好汉信息','保留“与这位好汉密议”，不展示需求和资料；有待点将事项时才显示点将动作，密议不创建事项。']]},
 {id:'private',title:'密议 · 保留已有独立会话',page:'agents',setup:"openPrivate();conversation().messages=[{role:'USER',text:'你好，我们先聊聊想法。'},{role:'AGENT',text:'可以。这里是我们单独的会话，不会创建或更改事项。'}];renderChat()",marks:[['.discussion-brief','与指定好汉单独聊天','密议与悬赏议事分开保存；返回点将册、更换好汉，都不会把会话内容混入事项。'],['.composer-body','同样使用简洁输入区','文字、资料、引用和语音演示都在同一个输入区完成。']]},
 {id:'chat-start',title:'悬赏议事 · 自动带入需求',page:'chat',setup:"document.querySelector('.hall-messages').scrollTop=0",marks:[['.hall-message.USER','自动首条消息','这里的需求与资料由点将自动带入。Agent 可以直接执行，也可以在会话中自然澄清。'],['.composer-body','只用普通发送','取消“生成图片”“受控请求”及重复批准，不需要选择工具或办理模式。']]},
 {id:'chat-result',title:'悬赏议事 · 图片与继续修改',page:'chat',marks:[['.mmd-result img','在消息中看成果','统一在会话内显示图片，点击放大；不另开一套绘图流程。'],['.mmd-result .mmd-row','预览、下载、保存、引用','保存到工作空间是可选操作；引用当前稿继续改，旧稿仍保留。'],['.composer-body','融合为一个输入区','只保留“＋”和发送；资料、语音输入与设置收进“＋”。'],['.chat-panel .panel-toolbar','不加额外功能按钮','已移除事项资料、百宝箱、验收；资料和成果仍在消息中，验收回事项详情。']]},
 {id:'chat-media',title:'悬赏议事 · 音频与文档',page:'chat',setup:"state.messages=[state.messages[0],{role:'AGENT',text:'音频和文档也在这次议事中。',outputs:['result-2','result-3']}];renderChat();requestAnimationFrame(()=>{const m=document.querySelector('.hall-messages'),r=document.querySelector('.mmd-result');m.scrollTop+=r.getBoundingClientRect().top-m.getBoundingClientRect().top-10})",marks:[['.mmd-result audio','音频原位播放','语音、音频类成果可直接播放，也可下载或保存。这里使用示意音。'],['.mmd-result[data-result=result-3]','文档也是成果','文档与文字和图片一样，可在会话中预览、下载并用于验收。']]},
 {id:'workspace',title:'资料 · 现有工作空间',page:'workspace',setup:"document.querySelector('.treasure-file-row:last-child').scrollIntoView({block:'center'})",marks:[['.treasure-file-row:last-child','保存后在这里找到','继续使用现有工作空间，不新增一套文件系统；保存的成果可以再次作为资料使用。']]},
 {id:'detail',title:'事项详情',page:'detail',marks:[['.matter-advice-card','进展与继续议事','去掉“明确开始正式办理”等重复执行说明，保留进展和继续议事动作。'],['.task-material-links','需求资料与成果','在同一事项查看关联资料和成果数量；不再限定为正式 PDF 办理。'],['.matter-results-action','保留原验收入口','验收只保留在事项详情。议事中通过原有返回按钮回到这里，不增加验收快捷按钮。']]},
 {id:'accept',title:'验收成果 · 默认直接看交付清单',page:'detail',setup:"state.messages.at(-1).outputs=['result-1','result-2','result-3','result-4'];accept()",marks:[['[data-delivery-list]','只看本次成果','不再有多选框或调整交付内容功能；当前成果直接列出供预览，旧稿留在会话中。'],['dialog footer','满意后完成','不满意就继续修改；满意后确认验收，无需先保存到工作空间。']]}

];
const seed=`state.draft='画一只鸟';state.title='画一只鸟';state.draftFiles=['ref-bird','ref-brief'];state.task={title:'画一只鸟',description:'画一只鸟',files:['ref-bird','ref-brief'],complete:false};state.selectedAgent={id:'0',name:'公孙胜'};state.agent={...state.selectedAgent};state.outputs=[];state.delivery=[];state.privateChats={};state.privateAgentId=null;state.archive=[];state.saved=[];state.pending=false;state.chatDraft='';state.chatFiles=[];state.quote=null;serial=0;output('image','',1);output('audio','',1);output('document','',1);output('text','小鸟停在枝头，观察四周。',1);state.saved=['result-1'];state.archive=[{...state.outputs[0]}];state.messages=[{role:'USER',text:'画一只鸟',files:['ref-bird','ref-brief']},{role:'AGENT',text:'先给你这一版，看看是否符合你的想法。',outputs:['result-1']}];`;
const report=[];
for(const width of [1440,390]){
 await viewport(width,width===1440?1000:844);
 for(const scene of scenes){
  await evalJS(seed);await navigate(scene.page);if(scene.setup)await evalJS(scene.setup);await delay(220);
  const boxes=[];
  for(const [selector,title,note] of scene.marks){
   const rect=await evalJS(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;let r=e.getBoundingClientRect(),l=Math.max(0,r.left),t=Math.max(0,r.top),right=Math.min(innerWidth,r.right),bottom=Math.min(innerHeight,r.bottom);for(let p=e.parentElement;p;p=p.parentElement){const s=getComputedStyle(p),b=p.getBoundingClientRect();if(/auto|scroll|hidden|clip/.test(s.overflowY)){t=Math.max(t,b.top);bottom=Math.min(bottom,b.bottom);}if(/auto|scroll|hidden|clip/.test(s.overflowX)){l=Math.max(l,b.left);right=Math.min(right,b.right);}}return right-l>6&&bottom-t>6?{x:l,y:t,w:right-l,h:bottom-t}:null})()`);
   if(rect)boxes.push({selector,title,note,...rect});else throw Error('mark not visible: '+width+' '+scene.id+' '+selector);
  }
  const name=(width===1440?'desktop':'mobile')+'-'+scene.id;await capture(name);report.push({id:scene.id,title:scene.title,device:width===1440?'desktop':'mobile',width,height:width===1440?1000:844,image:'screenshots/'+name+'.png',boxes});
 }
}
fs.writeFileSync(path.join(root,'annotations.js'),'window.CHANGE_ANNOTATIONS = '+JSON.stringify(report,null,2)+';\n');
assert.equal(errors.length,0,errors.join('\n'));console.log(JSON.stringify({screens:report.length,markedRegions:report.reduce((n,s)=>n+s.boxes.length,0),errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{if(ws?.readyState===WebSocket.OPEN){try{await call('Browser.close');}catch{}ws.close();}if(child.exitCode===null)child.kill('SIGTERM');await delay(400);if(child.exitCode!==null)fs.rmSync(profile,{recursive:true,force:true});});
