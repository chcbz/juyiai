'use strict';
// Standalone, offline prototype only. No production runtime, API, Provider, or account access.
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={home:'办事',tasks:'事项',create:'提出需求',agents:'点将册',detail:'事项详情',chat:'悬赏议事',private:'密议',workspace:'资料',mine:'我的'};
const catalog=[
 {id:'ref-bird',name:'小鸟图片.svg',type:'image',url:'assets/bird-v1.svg',note:'图片 · 示意插画'},
 {id:'ref-brief',name:'活动说明.md',type:'document',url:'assets/brief.md',text:'# 活动说明\n主题：自然观察\n对象：亲子家庭\n需要：一张配图、一段介绍、一份活动方案。',note:'文档'},
 {id:'ref-audio',name:'音频示例.wav',type:'audio',url:'assets/sample.wav',note:'音频 · 2 秒示意音'},
 {id:'ref-text',name:'小鸟介绍.txt',type:'text',text:'小鸟停在枝头，观察四周。保持距离，安静欣赏。',note:'文本'}
];
const state={draft:'',title:'',draftFiles:[],chatDraft:'',chatFiles:[],quote:null,task:null,agent:null,messages:[],outputs:[],archive:[],saved:[],final:[],pending:false,selectedAgent:null,privateChats:{},privateAgentId:null,delivery:[]};
let page=labels[location.hash.slice(1)]?location.hash.slice(1):'home',view='',toastTimer,picker=null,lastFocus=null,workspaceFrom=null,serial=0,finalDraft=[];
const scenario=new URLSearchParams(location.search).get('scenario')||'normal';
const storageKey='cyf-offline-prototype-complete-20261007:'+scenario;
state.localFiles=[];state.operation=null;state.simulation={create:scenario==='create-failure'?'failed':scenario==='create-unknown'?'unknown':'ok',reply:scenario==='reply-failure'?'failed':'ok',accept:scenario==='accept-unknown'?'unknown':scenario==='accept-failure'?'failed':'ok'};
try{const stored=JSON.parse(sessionStorage.getItem(storageKey)||'null');if(stored?.state){Object.assign(state,stored.state);serial=stored.serial||0;}}catch{/* Browser storage may be unavailable. */}
const conversation=()=>page==='private'?(state.privateChats[state.privateAgentId]||state):state;
function persist(){try{sessionStorage.setItem(storageKey,JSON.stringify({state,serial}));}catch{/* No business storage is used. */}}
function openPrivate(){const a=state.selectedAgent;if(!a)return;state.privateAgentId=a.id;if(!state.privateChats[a.id])state.privateChats[a.id]={agent:{...a},messages:[],outputs:[],chatDraft:'',chatFiles:[],quote:null,pending:false,delivery:[]};go('private');}
const taskTitle=()=>state.task?.title||state.draft||'画一只鸟';
const status=()=>state.task?.complete?'已完成':state.operation?.stage==='pending'?'验收中':state.operation?.stage==='unknown'?'验收待核对':state.operation?.stage==='failed'?'验收未完成':state.pending?'办理中':state.error?'回复失败':state.outputs.length?'待验收':state.agent?'议事中':'待点将';
const asset=id=>[...catalog,...state.localFiles,...state.archive,...state.outputs,...Object.values(state.privateChats).flatMap(c=>c.outputs)].find(a=>a.id===id);
function scoped(root,key){root?.setAttribute(key,'');$$('*',root).forEach(e=>e.setAttribute(key,''));return root;}
function insert(parent,html,scope){const wrap=document.createElement('div');wrap.innerHTML=html;if(scope)scoped(wrap,scope);parent.append(...wrap.childNodes);}
function feedback(message){$('#prototype-feedback')?.remove();const n=document.createElement('div');n.id='prototype-feedback';n.role='status';n.textContent=message;document.body.append(n);clearTimeout(toastTimer);toastTimer=setTimeout(()=>n.remove(),2600);}
function syncViewport(){$$('.juyi-page').forEach(e=>e.style.setProperty('--hall-visual-height',innerHeight+'px'));}
function button(label,action,extra=''){return `<button type="button" data-action="${action}" ${extra}>${label}</button>`;}
function files(ids,context,removable=true){return `<div class="mmd mmd-attachments">${ids.map(id=>{const a=asset(id);return a?`<div class="mmd-chip"><span>${esc(a.name)}</span>${button('预览','preview',`data-id="${id}"`)}${removable?button('移除','remove',`data-id="${id}" data-context="${context}"`):''}</div>`:''}).join('')}</div>`;}
function media(a,full=false){if(a.type==='image')return `<img src="${a.url}" alt="${esc(a.name)}（原型示意插画）" data-action="preview" data-id="${a.id}">`;if(a.type==='audio')return `<audio controls preload="metadata" src="${a.url}" aria-label="${esc(a.name)}"></audio><small class="mmd-muted">${a.id.startsWith('local-')?'本机音频（未上传）':'2 秒示意音，非真实配音'}</small>`;return `<pre>${esc(full?a.text:(a.text||'可预览、下载此文件。').slice(0,220))}</pre>`;}
function result(a){return `<section class="mmd-result" data-result="${a.id}"><strong>${esc(a.name)}</strong>${media(a)}<div class="mmd-row">${button('预览','preview',`data-id="${a.id}"`)}${button('下载','download',`data-id="${a.id}"`)}${button(state.saved.includes(a.id)?'已保存':'保存到工作空间','save',`data-id="${a.id}" ${state.saved.includes(a.id)?'disabled':''}`)}${!conversation().task?.complete?button('引用修改','quote',`data-id="${a.id}"`):''}</div></section>`;}
function common(){
 $$('.quick-reference-open,.hall-reference-picker,.formal-task-execution').forEach(e=>e.remove());
 $$('.overview-start-copy>p').forEach(e=>e.textContent='说清想办的事，选一位好汉一起完成。也可以添加已有资料。');
 $$('.quick-material-open').forEach(e=>{delete e.dataset.prototypePage;e.textContent='添加资料（可选）';e.dataset.action='materials';e.dataset.context='draft';});
 const input=$('.overview-quick-request textarea');if(input){input.value=state.draft;input.placeholder='例如：画一只鸟，或整理一份活动方案。';const submit=$('.overview-quick-request button.primary');submit.disabled=!state.draft.trim()&&!state.draftFiles.length;$('.quick-request-input small').textContent=state.draft.length+'/200';$('.quick-request-actions').insertAdjacentHTML('afterend',files(state.draftFiles,'draft'));}
 // Preserve existing sample lists. Only the first item is the interactive task.
 $$('.overview-item,.task-card').forEach((e,i)=>{if(e.matches('.overview-item')&&i!==0)return;if(e.matches('.task-card')&&e!==$('.task-card'))return;const title=$('strong,h3,h4',e);if(title)title.textContent=taskTitle();const badge=$('[class*=state],.status-badge,.overview-status',e);if(badge)badge.textContent=status();if(e.matches('.overview-item')){const desc=$('.overview-item-copy>p',e);if(desc)desc.textContent='正式事项 · '+(state.agent?.name||'待安排');}else if($(':scope>p',e))$(':scope>p',e).textContent=state.task?.description||taskTitle();});
 $$('.task-create-actions').forEach(group=>{const first=$('button',group);if(!first)return;$$('button',group).slice(1).forEach(e=>e.remove());first.textContent='提出需求';first.dataset.prototypePage='create';});
 $$('.task-data-state').forEach(e=>e.remove());
 $$('.task-status-tabs button').forEach(e=>{if(e.textContent.includes('待开工'))e.firstChild.textContent='议事中 ';});
 $$('form').forEach(f=>f.addEventListener('submit',onSubmit));
}
function render(){
 view=innerWidth<=900?'mobile':'desktop';const snap=window.BASELINE_SNAPSHOTS[view+'-'+(page==='private'?'chat':page)]||window.BASELINE_SNAPSHOTS[view+'-home'];
 document.body.innerHTML=snap.html.replaceAll('./juyiting-portraits/','../current/juyiting-portraits/').replaceAll('./static/','../current/static/');
 document.body.className=snap.bodyClass;document.documentElement.className=snap.htmlClass;document.title=labels[page]+' · 完整交互原型（离线示例）';syncViewport();common();const badge=document.createElement('div');badge.className='prototype-simulation-label';badge.textContent='离线交互原型 · 非线上功能';document.body.append(badge);
 if(page==='tasks'||page==='home')renderTaskList();if(page==='create')renderCreate();if(page==='agents')renderAgents();if(page==='detail'||page==='chat')renderDetail();if(page==='chat'||page==='private')renderChat();if(page==='workspace')renderWorkspace();persist();
}
function go(next){if(!labels[next])return;page=next;history.replaceState(null,'','#'+page);render();}
function renderCreate(){const form=$('.task-create-form');if(!form)return;$('[name=taskTitle]',form).value=state.title;$('[name=taskTitle]',form).placeholder='需求名称（可选）';$('[name=taskDescription]',form).value=state.draft;const desc=$('[name=taskDescription]',form);desc.placeholder='想完成什么？';$('button[type=submit]',form).textContent='提交需求';desc.insertAdjacentHTML('afterend',`<div class="mmd">${button('添加资料（可选）','materials','data-context="draft"')}${files(state.draftFiles,'draft')}</div>`);$('button[type=submit]',form).disabled=!state.draft.trim()&&!state.draftFiles.length;}
function renderAgents(){const panel=$('.agent-panel');if(!panel)return;$$('.agent-row',panel).forEach((row,i)=>{row.dataset.action='choose-agent';row.dataset.agent=String(i);row.setAttribute('aria-pressed',state.selectedAgent?.id===String(i));});const detail=$('.detail-card',panel);detail.classList.add('mmd','mmd-agent-detail');const selected=state.selectedAgent;const row=selected?$('.agent-row[data-agent="'+selected.id+'"]',panel):null;detail.innerHTML=selected?`<h3>${esc(selected.name)}</h3><p>${esc($('small',row)?.textContent||'')}</p><p class="mmd-muted">${esc($('em',row)?.textContent||'')}</p><div class="mmd-row">${button('与这位好汉密议','private-chat')}${state.task&&!state.agent&&!state.task.complete?button('点将并议事','assign','class="mmd-primary"'):''}</div>`:'<p>点一位好汉，查看本领并选择承办人。</p>';}
function renderDetail(){const card=$('.matter-advice-card');if(card){$('.matter-advice-heading span',card).textContent='事项进展';$('.matter-advice-heading strong',card).textContent=status();$('.matter-request',card).textContent=state.task?.description||taskTitle();$('dl',card).innerHTML=`<div><dt>承办好汉</dt><dd>${esc(state.agent?.name||'尚未点将')}</dd></div><div><dt>资料</dt><dd>${state.task?.files.length||0} 份</dd></div>`;scoped($('dl',card),'data-v-9209fea5');$('.matter-fee-note',card)?.remove();const b=$('.matter-primary-action',card);b.textContent=state.task?.complete?'查看议事记录':state.agent?'继续议事':'去点将';b.dataset.prototypePage=state.agent?'chat':'agents';}
 const materials=$('.task-material-links');if(materials){materials.innerHTML=`<div class="mmd"><h4>资料与成果</h4>${files(state.task?.files||[],'task',false)}<p class="mmd-muted">${state.outputs.length?`已有 ${state.outputs.length} 份成果，可在议事中查看。`:'尚无成果，可在议事中继续补充需求和资料。'}</p></div>`;}
 const b=$('.matter-results-action');if(b){b.textContent=state.task?.complete?'查看验收结果':'查看正式成果与验收';b.dataset.action='accept';}
}
function renderChat(){
 const ctx=conversation(),isPrivate=page==='private';
 const panel=$('.chat-panel');if(!panel)return;$$('.mmd-composer-extra',panel).forEach(e=>e.remove());
 $$('.context-summary strong,.discussion-brief strong').forEach(e=>e.textContent=isPrivate?'密议':'悬赏议事');$$('.context-summary small,.discussion-brief small').forEach(e=>e.textContent=isPrivate?(ctx.agent?.name||'请选择好汉'):taskTitle()+' / '+(ctx.agent?.name||'尚未点将'));const em=$('.context-summary em');if(em)em.textContent=isPrivate?(ctx.pending?'正在回复':'与好汉单独聊聊'):status();if(!isPrivate){const back=$('.panel-return');if(back)back.dataset.prototypePage='detail';}if(isPrivate){const back=$('.panel-return');if(back)back.dataset.prototypePage='agents';const heading=$('#juyiting-floating-panel-title');if(heading)heading.textContent='密议';}
 $('.toolbar-actions',panel)?.remove();
 const messages=$('.hall-messages');messages.setAttribute('aria-live','polite');messages.innerHTML=ctx.messages.map((m,index)=>`<div class="hall-message ${m.role}"><div class="message-head"><strong>${m.role==='USER'?'你':esc(ctx.agent?.name||'好汉')}</strong></div><div class="message-content"><p>${esc(m.text)}</p></div>${m.quote?`<div class="mmd mmd-quote">引用：${esc(asset(m.quote)?.name)}</div>`:''}${files(m.files||[],'message',false)}<details data-v-4c0df501 class="text-selection-archive"><summary data-v-4c0df501>保存文字片段</summary><label data-v-4c0df501>要保存的文字<textarea data-v-4c0df501 data-message-text="${index}" rows="3">${esc(m.text)}</textarea></label><button data-v-4c0df501 type="button" data-action="save-text" data-message="${index}">保存到工作空间</button></details>${m.outputs?.length?`<div class="mmd mmd-results">${m.outputs.map(id=>result(asset(id))).join('')}</div>`:''}</div>`).join('')+(ctx.error?`<div class="mmd mmd-error" role="alert">${esc(ctx.error)} ${button('核对回复状态','reply-status')}</div>`:'')+(ctx.pending?'<p class="mmd-pending" role="status">正在回复…</p>':'');scoped(messages,'data-v-8f1da78a');
 if(!ctx.messages.length)insert(messages,`<p class="mmd-pending">${isPrivate?'想聊什么，直接说吧。密议不会创建或更改事项。':'请先提出需求并点将，需求和资料将自动带入这里。'}</p>`);
 const input=$('.composer-textarea');input.disabled=!!ctx.task?.complete;input.value=ctx.chatDraft;input.placeholder=ctx.task?.complete?'事项已完成':'补充需求，或告诉好汉哪里需要调整…';
 $$('.composer-context,.composer-meta,.hall-voice-controls',panel).forEach(e=>e.remove());input.rows=2;input.style.height='';
 $('.composer-execute')?.remove();const send=$('.composer-send');send.innerHTML='发送';send.ariaLabel='发送';send.title='发送';send.disabled=ctx.pending||!!ctx.task?.complete||(!ctx.chatDraft.trim()&&!ctx.chatFiles.length)||!ctx.agent;
 const form=$('.composer-submit'),body=$('.composer-body');$$('.composer-more',panel).forEach(e=>e.remove());
 const extra=document.createElement('div');extra.className='mmd mmd-composer-extra';extra.innerHTML=`${ctx.quote?`<div class="mmd-quote">引用：${esc(asset(ctx.quote)?.name)} ${button('取消引用','unquote')}</div>`:''}${files(ctx.chatFiles,'chat')}`;if(ctx.quote||ctx.chatFiles.length)body.prepend(extra);
 const more=document.createElement('button');more.type='button';more.className='composer-more';more.dataset.action='composer-more';more.textContent='＋';more.ariaLabel='添加资料、语音输入与设置';more.title='添加资料、语音输入与设置';more.disabled=!!ctx.task?.complete;$('.composer-actions').prepend(more);
 const scrollEnd=()=>{if(messages.isConnected)messages.scrollTop=messages.scrollHeight;};requestAnimationFrame(scrollEnd);$$('img',messages).forEach(img=>img.addEventListener('load',scrollEnd,{once:true}));
}
function renderWorkspace(){const list=$('.treasure-file-list');if(!list)return;const items=[...catalog,...state.saved.map(asset)];list.innerHTML=items.map(a=>`<div class="treasure-file-row"><div><strong>${esc(a.name)}</strong><p>${catalog.includes(a)?'已有资料':'从议事保存的成果'} · ${esc(a.note||({image:'图片',audio:'音频',document:'文档',text:'文本'}[a.type]))}</p></div><button type="button" data-action="preview" data-id="${a.id}">查看</button></div>`).join('');scoped(list,'data-v-a1bd66a6');if(workspaceFrom)list.insertAdjacentHTML('beforebegin',`<div class="mmd mmd-workspace-back">${button('← 返回议事','back-chat')}</div>`);}
function submitRequest(){if(!state.draft.trim()&&!state.draftFiles.length)return;if(state.simulation.create!=='ok'){createProblem();return;}state.task={title:state.title.trim()||state.draft.trim().slice(0,36)||'附件需求',description:state.draft.trim(),files:[...state.draftFiles],complete:false};state.agent=null;state.messages=[];state.outputs=[];state.delivery=[];state.final=[];state.pending=false;state.selectedAgent=null;state.chatDraft='';state.chatFiles=[];state.quote=null;state.error=null;state.operation=null;state.draft='';state.title='';state.draftFiles=[];go('agents');}
function assign(){if(!state.selectedAgent||!state.task||state.agent||state.task.complete)return;state.agent={...state.selectedAgent};state.messages=[{role:'USER',text:state.task.description,files:[...state.task.files]}];go('chat');reply(state.task.description||'请先确认这些资料的用途。',true,state);}
function output(type,text,revision,ctx=conversation()){const id='result-'+(++serial);const a={id,type,name:'',text,note:'第 '+revision+' 稿'};if(type==='image'){a.name=`小鸟-第${revision}稿.svg`;a.url=revision===1?'assets/bird-v1.svg':'assets/bird-v2.svg';}else if(type==='audio'){a.name=`音频-第${revision}稿.wav`;a.url='assets/sample.wav';}else if(type==='document'){a.name=`活动方案-第${revision}稿.md`;a.url='assets/plan.md';a.text='# 自然观察活动方案\n\n目标：认识身边的鸟类，记录观察结果。\n\n1. 介绍观察方法。\n2. 分组观察并记录。\n3. 分享发现，整理成果。\n\n保持距离，不打扰动物。';}else a.name=`文字成果-第${revision}稿.txt`;ctx.outputs.push(a);return id;}
function reply(text,first=false,ctx=conversation()){
 ctx.pending=true;if(conversation()===ctx&&(page==='chat'||page==='private'))renderChat();persist();const task=ctx.task;
 setTimeout(()=>{if(ctx.task!==task)return;const revision=ctx.messages.filter(m=>m.outputs?.length).length+1;let ids=[],answer;
 if(ctx!==state&&!/画|图片|照片|音频|配音|方案|文档|文件|介绍/.test(text)){answer='我是'+ctx.agent.name+'，可以直接和我聊，也可以补充资料。你想先聊哪件事？';}
 else if(first&&(!ctx.task?.description||/^(帮我|做一下|处理一下|优化一下|改一下|看看)[。！!\s]*$/.test(text.trim())||text.trim().length<3)){answer='你希望完成什么内容？可以补充用途或想要的结果，也可以添加一份资料。';}
 else {const history=ctx.messages.filter(m=>m.role==='USER').map(m=>m.text).join(' ');const image=asset(ctx.messages.at(-1)?.quote)?.type==='image'||/画|图片|小鸟|照片|配图|插画/.test(text)||(!/音频|配音|文档|方案|文字|介绍/.test(text)&&/画|图片|小鸟|照片/.test(history));const audio=/音频|配音|声音/.test(text),doc=/方案|文档|文件|纪要/.test(text);if(image)ids.push(output('image','',revision,ctx));if(audio)ids.push(output('audio','',revision,ctx));if(doc)ids.push(output('document','',revision,ctx));if(!ids.length||/文字|介绍|说明/.test(text))ids.push(output('text','小鸟停在枝头，轻轻侧头，望向远处。愿你在忙碌中，也留意身边这些小小的美好。\n\n（原型示例文字，可作为独立成果验收。）',revision,ctx));answer=first?'先给你这一版，看看是否符合你的想法。':'已按补充内容整理了新一稿，上一稿仍保留在会话中。';}
 ctx.error=null;ctx.messages.push({role:'AGENT',text:answer,outputs:ids});
 // Explicit demo deliverable slots: a revision replaces its slot, not unrelated files.
 for(const id of ids){const a=asset(id);ctx.delivery=(ctx.delivery||[]).filter(old=>asset(old)?.type!==a.type);ctx.delivery.push(id);}
 ctx.pending=false;persist();if(conversation()===ctx&&(page==='chat'||page==='private'))renderChat();else if(ctx===state&&page==='detail')renderDetail();
 },650);
}
function send(){const ctx=conversation();if(state.simulation.reply==='failed'){ctx.error='示例：发送未明确受理。草稿与资料已保留，不自动重发。';renderChat();persist();return;}if(ctx.pending||ctx.task?.complete||!ctx.agent||(!ctx.chatDraft.trim()&&!ctx.chatFiles.length))return;const text=ctx.chatDraft.trim();ctx.messages.push({role:'USER',text:text||'请结合这些资料继续。',files:[...ctx.chatFiles],quote:ctx.quote});if(ctx===state&&ctx.task)ctx.task.files=[...new Set([...ctx.task.files,...ctx.chatFiles])];ctx.chatFiles=[];ctx.chatDraft='';ctx.quote=null;reply(text||'请结合这些资料继续。',false,ctx);}
function dialog(title,html,footer=''){const d=document.createElement('dialog');d.className='mmd mmd-dialog';d.setAttribute('aria-label',title);d.innerHTML=`<header><h3>${esc(title)}</h3>${button('关闭','close-dialog','aria-label="关闭窗口"')}</header>${html}${footer?'<footer>'+footer+'</footer>':''}`;document.body.append(d);lastFocus=document.activeElement;d.addEventListener('close',()=>{d.remove();if(lastFocus?.isConnected)lastFocus.focus();});d.showModal();return d;}
function openMaterials(context,selection=null){const ids=selection||(context==='chat'?conversation().chatFiles:state.draftFiles);picker={context,conversation:conversation(),ids:[...ids]};const all=[...catalog,...state.localFiles,...state.saved.map(asset)];dialog('添加资料（可选）',`<p class="mmd-muted">从工作空间选择资料，也可从本机添加示例附件。</p><label class="mmd-local-file">本机添加（仅此标签）<input type="file" multiple data-local-files></label><div class="mmd-files">${all.map(a=>`<div class="mmd-file-option"><input type="checkbox" id="pick-${a.id}" data-pick="${a.id}" ${ids.includes(a.id)?'checked':''}><label for="pick-${a.id}"><strong>${esc(a.name)}</strong><br><small>${esc(a.note||a.type)}</small></label>${button('预览','preview',`data-id="${a.id}"`)}</div>`).join('')}</div>`,button('取消','close-dialog')+button('确定（'+ids.length+'）','confirm-materials','class="mmd-primary"'));}
function preview(id){const a=asset(id);if(!a)return;dialog(a.name,`<div class="mmd-preview">${media(a,true)}<p class="mmd-muted">${a.type==='image'?'原型示意插画，非真实 Agent 生成照片。':'离线示例内容。'}</p></div>`,button('下载','download',`data-id="${id}"`));}
function download(id){const a=asset(id);if(!a)return;let url=a.url,blob=false;if(!url){url=URL.createObjectURL(new Blob([a.text||''],{type:'text/plain;charset=utf-8'}));blob=true;}const link=document.createElement('a');link.href=url;link.download=a.name;document.body.append(link);link.click();link.remove();if(blob)setTimeout(()=>URL.revokeObjectURL(url),2000);}
function deliveryList(){return finalDraft.map(id=>{const a=asset(id);return a?`<div class="mmd-chip"><span><strong>${esc(a.name)}</strong><br><small>${esc(a.note)}</small></span>${button('预览','preview',`data-id="${id}"`)}</div>`:''}).join('')||'<p class="mmd-muted">尚无可验收成果；可返回原议事继续补充。</p>';}
function accept(){if(!state.task)return;const done=state.task.complete;if(state.operation&&!done){operationDialog();return;}if(scenario==='independent-roots'){dialog('来源尚未关联','<p>图片与文字来自两个独立请求，暂不能作为同次交付验收。</p><p>保留原成果，不自动合并、不重新生成。来源关联恢复入口待实现（R01）。</p>',button('回原议事查看','continue-chat'));return;}finalDraft=done?[...state.final]:[...(state.delivery?.length?state.delivery:([...state.messages].reverse().find(m=>m.role==='AGENT'&&m.outputs?.length)?.outputs||[]))];dialog(done?'验收结果':'验收成果',`<p>${done?'事项已完成，最终成果如下。':'请查看本次成果，满意后确认验收；需要修改就返回议事。'}</p><div class="mmd-attachments" data-delivery-list>${deliveryList()}</div>`,done?button('关闭','close-dialog'):button('继续修改','continue-chat')+button('确认验收','finish',`class="mmd-primary" ${finalDraft.length&&!state.pending?'':'disabled'}`));}
function onSubmit(e){e.preventDefault();if(e.target.matches('.overview-quick-request,.task-create-form'))submitRequest();else if(e.target.matches('.composer-submit'))send();else feedback('原型保留原有入口，本次只演示需求协作流程。');}
document.addEventListener('input',e=>{const t=e.target;if(t.matches('.overview-quick-request textarea')){state.draft=t.value;$('.quick-request-input small').textContent=t.value.length+'/200';$('.overview-quick-request button.primary').disabled=!t.value.trim()&&!state.draftFiles.length;}if(t.name==='taskDescription'){state.draft=t.value;$('.task-create-form button[type=submit]').disabled=!t.value.trim()&&!state.draftFiles.length;}if(t.name==='taskTitle')state.title=t.value;if(t.matches('.composer-textarea')){const ctx=conversation();ctx.chatDraft=t.value;$('.composer-send').disabled=ctx.pending||!!ctx.task?.complete||(!t.value.trim()&&!ctx.chatFiles.length)||!ctx.agent;}});
document.addEventListener('change',e=>{const t=e.target;if(t.matches('[data-local-files]')){addLocalFiles(t.files);return;}if(t.dataset.pick){picker.ids=t.checked?[...new Set([...picker.ids,t.dataset.pick])]:picker.ids.filter(id=>id!==t.dataset.pick);$('[data-action=confirm-materials]').textContent='确定（'+picker.ids.length+'）';}});
document.addEventListener('click',e=>{
 const t=e.target.closest('[data-action],button,a,[data-prototype-page]');if(!t||t.disabled||t.matches('a[download]'))return;
 if(t.type==='submit'&&t.closest('form'))return;e.preventDefault();const action=t.dataset.action,id=t.dataset.id;
 if(action==='composer-more'){dialog('更多',`<div class="mmd-more-menu">${button('添加资料','composer-materials')}${button('语音输入','voice-record')}${button('语音设置','voice-settings')}</div>`);return;}
 if(action==='composer-materials'){t.closest('dialog').close();openMaterials('chat');return;}
 if(action==='voice-record'){t.closest('dialog').close();dialog('语音输入','<p role="status">正在录音…</p><p class="mmd-muted">交互演示，不会启用麦克风。</p>',button('取消','close-dialog')+button('结束录音','voice-stop','class="mmd-primary"'));return;}
 if(action==='voice-stop'){t.closest('dialog').close();dialog('确认语音文字','<label class="mmd-voice-transcript">识别内容（可修改）<textarea rows="3" aria-label="识别内容">请把画面调整得明亮一些。</textarea></label><p class="mmd-muted">以上为示例转写，不是真实录音识别。</p>',button('取消','close-dialog')+button('放入输入框','voice-use','class="mmd-primary"'));return;}
 if(action==='voice-use'){const text=$('.mmd-voice-transcript textarea').value.trim();if(!text){feedback('请输入要使用的文字');return;}const ctx=conversation();ctx.chatDraft=[ctx.chatDraft,text].filter(Boolean).join('\n');t.closest('dialog').close();renderChat();$('.composer-textarea').focus();return;}
 if(action==='voice-settings'){t.closest('dialog').close();dialog('语音设置',`<label>识别语言 <select class="mmd-voice-language" aria-label="识别语言"><option value="zh-CN">中文</option><option value="en-US">English</option></select></label><p class="mmd-muted">设置只保留在本原型，不连接语音服务。</p>`,button('取消','close-dialog')+button('保存','voice-settings-save','class="mmd-primary"'));$('.mmd-voice-language').value=state.voiceLanguage||'zh-CN';return;}
 if(action==='voice-settings-save'){state.voiceLanguage=$('.mmd-voice-language').value;t.closest('dialog').close();feedback('已保存原型语音设置');return;}
 if(action==='materials'){openMaterials(t.dataset.context);return;}
 if(action==='confirm-materials'){if(picker.context==='chat')picker.conversation.chatFiles=[...picker.ids];else state.draftFiles=[...picker.ids];t.closest('dialog').close();render();return;}
 if(action==='close-dialog'){t.closest('dialog').close();return;}
 if(action==='preview'){if(!t.closest('.mmd-preview'))preview(id);return;}
 if(action==='download'){download(id);return;}
 if(action==='remove'){const key=t.dataset.context==='chat'?'chatFiles':'draftFiles';const ctx=t.dataset.context==='chat'?conversation():state;ctx[key]=ctx[key].filter(x=>x!==id);render();return;}
 if(action==='choose-agent'){state.selectedAgent={id:t.dataset.agent,name:$('strong',t).textContent};renderAgents();return;}
 if(action==='private-chat'){openPrivate();return;}
 if(action==='assign'){assign();return;}
 if(action==='save-text'){const text=$('[data-message-text="'+t.dataset.message+'"]').value.trim();if(!text){feedback('先选好要保存的文字');return;}const a={id:'saved-text-'+(++serial),name:'议事文字片段-'+serial+'.txt',type:'text',text,note:'议事文字'};state.archive.push(a);state.saved.push(a.id);feedback('文字片段已保存到工作空间');return;}
 if(action==='save'){if(!state.saved.includes(id)){state.saved.push(id);state.archive.push({...asset(id)});}t.disabled=true;t.textContent='已保存';feedback('已保存到工作空间');return;}
 if(action==='quote'){const ctx=conversation();ctx.quote=id;ctx.chatDraft='请把这一稿';renderChat();$('.composer-textarea').focus();return;}
 if(action==='unquote'){conversation().quote=null;renderChat();return;}
 if(action==='workspace'){workspaceFrom='chat';go('workspace');return;}
 if(action==='back-chat'){go('chat');return;}
 if(action==='task-files'){dialog('事项资料',state.task?.files.length?files(state.task.files,'task',false):'<p>暂无资料，可以继续议事，无需添加。</p>');return;}
 if(action==='accept'){accept();return;}
 if(action==='continue-chat'){if(state.task?.complete){feedback('已完成事项为只读，不再修改或重复验收。');return;}go(state.agent?'chat':'agents');return;}
 if(action==='finish'){beginAcceptance();return;}
 if(action==='operation-status'){resolveOperation();return;}
 if(action==='operation-detail'){t.closest('dialog')?.close();go('detail');return;}
 if(action==='create-status'){state.simulation.create='ok';t.closest('dialog').close();feedback('示例核对：未受理。草稿保留，可显式提交。');return;}
 if(action==='reply-status'){state.simulation.reply='ok';conversation().error=null;renderChat();feedback('示例核对：未受理。请核对草稿后显式发送。');return;}
 if(t.dataset.prototypePage){if(t.dataset.prototypePage==='detail'&&!state.task){feedback('请先提出需求，原型不会自动建立事项。');return;}if(t.dataset.prototypePage==='materials')openMaterials('draft');else if(t.dataset.prototypePage==='workspace'){workspaceFrom=page==='chat'?'chat':null;go('workspace');}else go(t.dataset.prototypePage);return;}
 if(t.matches('.workbench-mobile-more')){dialog('更多',`<div class="mmd-row">${button('点将册','go-agents')}${button('提出需求','go-create')}</div>`);return;}
 if(action==='go-agents'){go('agents');return;}if(action==='go-create'){go('create');return;}
 if(t.matches('.voice-start,.voice-settings-trigger')){feedback('此原型不启用麦克风，语音入口保持原样。');return;}
 feedback('保留现有入口；本次原型只演示需求、资料、议事与验收。');
});
window.addEventListener('hashchange',()=>{if(labels[location.hash.slice(1)]){page=location.hash.slice(1);render();}});
window.addEventListener('resize',()=>{if(view!==(innerWidth<=900?'mobile':'desktop'))render();else syncViewport();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('dialog[open]')){if(page==='chat')go('detail');else if(page==='private')go('agents');}});
for(const event of ['input','change','click'])document.addEventListener(event,()=>queueMicrotask(persist));
window.addEventListener('pagehide',persist);
render();
for(const ctx of [state,...Object.values(state.privateChats)])if(ctx.pending){ctx.pending=false;ctx.error='示例：刷新时回复状态待核对；不会自动重发。';persist();if(page==='chat'||page==='private')renderChat();}
if(state.operation?.stage==='pending')setTimeout(resolveOperation,350);

function createProblem(){const unknown=state.simulation.create==='unknown';dialog(unknown?'提交状态待核对':'提交失败（示例）',`<p>${unknown?'不能确认是否已受理。先核对状态，不重复创建。':'明确未受理，需求和附件保留。'}</p>`,button(unknown?'核对创建状态':'返回修改','create-status'));}
function beginAcceptance(){if(state.operation||!finalDraft.length||!state.task||state.pending)return;state.operation={id:'demo-operation-'+(++serial),taskTitle:state.task.title,outputs:[...finalDraft],stage:'pending',writes:1};if(page==='detail')renderDetail();persist();$('dialog[open]')?.close();operationDialog();setTimeout(resolveOperation,650);}
function operationDialog(){const op=state.operation;if(!op)return;finalDraft=[...op.outputs];dialog('验收进度',`<p role="status">${op.stage==='pending'?'正在核对验收状态…':op.stage==='failed'?'验收未完成。原操作和成果保留。':'验收状态未知。不会重新提交验收。'}</p><small>原操作：${esc(op.id)} · 同一事项 · 冻结 ${op.outputs.length} 项成果</small><div class="mmd-attachments">${deliveryList()}</div>`,button('返回详情','operation-detail')+button('查询原操作状态','operation-status'));}
function resolveOperation(){const op=state.operation;if(!op||state.task?.complete)return;if(state.simulation.accept==='unknown'){op.stage='unknown';}else if(state.simulation.accept==='failed'){op.stage='failed';}else{op.stage='completed';state.final=[...op.outputs];state.task.complete=true;persist();const d=$('dialog[open]');if(d?.getAttribute('aria-label')==='验收进度'){d.close();go('detail');feedback('示例验收完成，事项已完成');}else{render();}return;}if(page==='detail')renderDetail();persist();const d=$('dialog[open]');if(d?.getAttribute('aria-label')==='验收进度'){d.close();operationDialog();}}

function renderTaskList(){
 if(page==='home'){$$('.overview-item').slice(1).forEach(e=>e.remove());if(!state.task)$$('.overview-item').forEach(e=>e.remove());}
 if(page!=='tasks')return;const cards=$$('.task-card');cards.slice(1).forEach(e=>e.remove());const first=cards[0];
 const bucket=state.task?.complete?'已完成':!state.agent?'待点将':state.pending?'办理中':state.operation&&state.operation.stage!=='completed'?'受阻':state.outputs.length?'待验收':'议事中';
 const filter=state.taskFilter||bucket,match=!!state.task&&filter===bucket;
 const tabs=$$('.task-status-tabs button');for(const t of tabs){const label=t.innerText.trim().replace(/\s*\d+$/,'');t.dataset.action='demo-filter';t.dataset.filter=label;t.innerText=label+' '+(state.task&&bucket===label?'1':'0');t.classList.toggle('active',filter===label);}
 if(first){if(!state.task||!match){first.style.display='none';first.insertAdjacentHTML('afterend','<p class="mmd mmd-empty">该状态下暂无演示事项。</p>');}else{first.dataset.prototypePage='detail';const strong=$('strong',first);if(strong)strong.textContent=state.task.title;const badge=$('.status-badge',first);if(badge)badge.textContent=status();}}
}
document.addEventListener('click',e=>{const t=e.target.closest('[data-action="demo-filter"]');if(t){state.taskFilter=t.dataset.filter;go('tasks');}});
async function addLocalFiles(selected){
 const ids=[];for(const f of selected){const id='local-'+(++serial),type=f.type.startsWith('image/')?'image':f.type.startsWith('audio/')?'audio':/text|json/.test(f.type)||/\.(txt|md|csv)$/i.test(f.name)?'text':'document';
 const a={id,name:f.name,type,note:'本机示例附件 · 不上传'};
 if(type==='image'||type==='audio'){a.url=await new Promise((r,j)=>{const rd=new FileReader();rd.onload=()=>r(rd.result);rd.onerror=j;rd.readAsDataURL(f);});}
 else{a.text=type==='text'?await f.text():'此格式只演示文件选择，不支持内容解析。请在真实产品核对可用格式。';a.url=await new Promise((r,j)=>{const rd=new FileReader();rd.onload=()=>r(rd.result);rd.onerror=j;rd.readAsDataURL(f);});}
 state.localFiles.push(a);ids.push(id);}
 picker.ids=[...new Set([...picker.ids,...ids])];const ctx=picker.context,all=picker.ids;$('dialog[open]')?.close();persist();openMaterials(ctx,all);
}
