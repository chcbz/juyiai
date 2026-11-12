'use strict';
const records=window.CHANGE_ANNOTATIONS;
const pages=records.filter(x=>x.device==='desktop');
const scene=document.querySelector('#scene'),screen=document.querySelector('#screen'),stage=document.querySelector('#stage'),overlay=document.querySelector('#overlay'),notes=document.querySelector('#notes');
let device=innerWidth<700?'mobile':'desktop';
for(const p of pages){const o=document.createElement('option');o.value=p.id;o.textContent=p.title;scene.append(o);}
scene.value=pages.some(x=>x.id===location.hash.slice(1))?location.hash.slice(1):'chat-result';
function render(){
 const record=records.find(x=>x.id===scene.value&&x.device===device);if(!record)return;
 document.querySelector('#scene-title').textContent=record.title;
 screen.src=record.image;screen.alt=record.title+'（'+(device==='desktop'?'桌面':'手机')+'原型，红框见编号说明）';screen.width=record.width;screen.height=record.height;
 stage.classList.toggle('mobile',device==='mobile');overlay.replaceChildren();notes.replaceChildren();
 for(const [index,box] of record.boxes.entries()){
  const mark=document.createElement('div');mark.className='mark';mark.style.left=box.x/record.width*100+'%';mark.style.top=box.y/record.height*100+'%';mark.style.width=box.w/record.width*100+'%';mark.style.height=box.h/record.height*100+'%';
  const badge=document.createElement('button');badge.type='button';badge.textContent=index+1;badge.setAttribute('aria-label','变化 '+(index+1)+'：'+box.title);badge.setAttribute('aria-controls','note-'+index);mark.append(badge);overlay.append(mark);
  const li=document.createElement('li');li.id='note-'+index;const number=document.createElement('span');number.className='number';number.textContent=index+1;const text=document.createElement('div'),title=document.createElement('strong'),note=document.createElement('p');title.textContent=box.title;note.textContent=box.note;text.append(title,note);li.append(number,text);notes.append(li);
  badge.addEventListener('click',()=>{document.querySelectorAll('.selected').forEach(e=>e.classList.remove('selected'));mark.classList.add('selected');li.classList.add('selected');if(innerWidth<900)li.scrollIntoView({block:'nearest',behavior:'smooth'});});
 }
 for(const d of ['desktop','mobile'])document.getElementById(d).setAttribute('aria-pressed',d===device);
 history.replaceState(null,'','#'+record.id);
}
scene.addEventListener('change',render);
for(const d of ['desktop','mobile'])document.getElementById(d).addEventListener('click',()=>{device=d;render();});
document.querySelector('#marks').addEventListener('change',e=>overlay.hidden=!e.target.checked);
for(const [id,delta] of [['prev',-1],['next',1]])document.getElementById(id).addEventListener('click',()=>{scene.selectedIndex=(scene.selectedIndex+delta+pages.length)%pages.length;render();});
window.addEventListener('hashchange',()=>{if(pages.some(p=>p.id===location.hash.slice(1))){scene.value=location.hash.slice(1);render();}});
render();
