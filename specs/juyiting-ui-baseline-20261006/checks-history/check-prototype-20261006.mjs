import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
const dir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../prototype')
const require=createRequire(path.resolve(process.argv[2]||'web/package.json'))
const {JSDOM}=require('jsdom')
const pages=['home','tasks','create','agents','detail','chat','private','public','workspace','mine','library','messages','catalog','map','file','reader','help','account']
const scenarios=['ready','empty','waiting','streaming','error','recording','voice-review','results','completed']
const results=[]
function create(page,width=390,scenario='ready') {
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8')
 const dom=new JSDOM(html,{url:`http://localhost/?scenario=${scenario}#${page}`,runScripts:'outside-only',pretendToBeVisual:true})
 dom.window.structuredClone=structuredClone;
 dom.window.innerWidth=width;dom.window.innerHeight=width===390?844:1000
 const proto=dom.window.HTMLDialogElement.prototype
 proto.showModal=function(){this.setAttribute('open','')}
 proto.close=function(){this.removeAttribute('open');this.dispatchEvent(new dom.window.Event('close'))}
 const sources=[...dom.window.document.querySelectorAll('script[src]')].map(script=>fs.readFileSync(path.join(dir,script.getAttribute('src')),'utf8'));
 dom.window.eval(sources.join('\n')+'\nwindow.__baselineTest = {go,accept};')
 return dom
}
function click(dom,selector){const node=dom.window.document.querySelector(selector);assert.ok(node,selector);node.click();return node}
for(const width of [390,1440])for(const page of pages){const dom=create(page,width);assert.ok(dom.window.document.body.children.length);assert.ok(dom.window.document.title.includes('界面基准'));assert.equal(dom.window.document.querySelectorAll('.discussion-brief').length,0);for(const el of dom.window.document.querySelectorAll('[src]')){const src=el.getAttribute('src');if(!src||/^(data:|blob:|https?:)/.test(src))continue;assert.ok(fs.existsSync(path.join(dir,src)),`${page}: missing ${src}`)}results.push({page,width,result:'PASS'});dom.window.close()}
for(const scenario of scenarios){const dom=create('chat',390,scenario),d=dom.window.document;
 assert.ok(d.querySelector('.composer-input-area .composer-more'))
 assert.ok(d.querySelector('.composer-input-area .voice-start'))
 assert.ok(d.querySelector('.composer-input-area .composer-send'))
 for(const label of ['重取回话','话头记录','另起话头'])assert.ok(d.querySelector(`.panel-toolbar [aria-label="${label}"]`))
 assert.ok(!d.querySelector('.composer-more-panel'))
 assert.ok(![...d.querySelectorAll('button')].some(e=>e.textContent.trim()==='工作空间'))
 results.push({page:'chat',scenario,width:390,result:'PASS'});dom.window.close()
}
{
 const dom=create('chat'),d=dom.window.document
 click(dom,'.composer-more');assert.ok(d.querySelector('.composer-more-panel .composer-add-materials'));assert.ok(d.querySelector('.composer-more-panel .voice-settings-trigger'))
 click(dom,'[data-action=ui-settings]');assert.ok(d.querySelector('.voice-disclosure').textContent.includes('AI 生成语音'));assert.ok(!d.querySelector('.voice-settings').textContent.includes('识别语言'))
 click(dom,'[data-action=ui-materials]');const checks=d.querySelectorAll('dialog[open] input[type=checkbox]');assert.equal(checks.length,4);checks[0].click();click(dom,'[data-action=confirm-materials]');assert.ok(d.querySelector('.composer-body').textContent.includes('小鸟图片'))
 click(dom,'[data-action=ui-history]');assert.ok(d.querySelector('.baseline-history'));click(dom,'[data-action=ui-delete-history]');assert.ok(d.querySelector('dialog[open]'));click(dom,'[data-action=ui-delete-confirm]');assert.ok(!d.querySelector('.baseline-history'))
 click(dom,'[data-action=ui-voice]');click(dom,'[data-action=ui-voice-stop]');const text=d.querySelector('.baseline-voice-status textarea');text.value='测试转写';click(dom,'[data-action=ui-voice-append]');assert.ok(d.querySelector('.composer-textarea').value.includes('测试转写'))
 results.push({interaction:'plus/materials/history/voice-draft',result:'PASS'});dom.window.close()
}
{
 const dom=create('chat',390,'results'),d=dom.window.document
 assert.equal(d.querySelectorAll('.mmd-result').length,4)
 dom.window.__baselineTest.go('detail');dom.window.__baselineTest.accept()
 assert.equal(d.querySelectorAll('dialog[open] input[type=checkbox]').length,0)
 click(dom,'[data-action=finish]');assert.ok(d.body.textContent.includes('已完成'))
 results.push({interaction:'media/delivery/acceptance',result:'PASS'});dom.window.close()
}
{
 const dom=create('mine'),d=dom.window.document
 click(dom,'[data-prototype-page=library]');click(dom,'[data-action=ui-library-search]');click(dom,'[data-action=ui-search]');assert.ok(d.querySelector('[data-search-results]').textContent.includes('案卷'))
 dom.window.__baselineTest.go('workspace');click(dom,'[data-action=ui-file]');click(dom,'[data-action=ui-rename]');d.querySelector('dialog[open] input').value='改名示例.md';click(dom,'[data-action=ui-rename-save]');assert.ok(d.body.textContent.includes('改名示例.md'));click(dom,'[data-action=ui-recycle]');assert.ok(d.body.textContent.includes('恢复'))
 results.push({interaction:'mine/library/file-management',result:'PASS'});dom.window.close()
}
{
 const css=fs.readFileSync(path.join(dir,'hall-view-tabs.css'),'utf8')
 for(const group of ['.hall-overview .overview-tabs','.library-panel .library-tabs','.hall-draft-editor .case-tabs','.personal-workspace.is-hall-treasure .treasure-tabs'])assert.ok(css.includes(group))
 assert.ok(css.includes('background: #f7eae6 !important'))
 assert.ok(css.includes('border: 0 !important'))
 assert.ok(css.includes('button:focus-visible'))
 const dom=create('workspace'),d=dom.window.document
 assert.ok(d.querySelector('link[href="hall-view-tabs.css"]'))
 assert.ok(d.querySelector('.personal-workspace.is-hall-treasure .treasure-tabs button[aria-pressed="true"]'))
 results.push({style:'shared capsule tabs/resource and workspace selected state; not pixel acceptance',result:'PASS'});dom.window.close()
}
for(const source of ['prototype.js','baseline-ui.js'])assert.ok(!/\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(|getUserMedia\s*\(/.test(fs.readFileSync(path.join(dir,source),'utf8')))
const report={checkedOn:'2026-10-06',method:'JSDOM DOM/interaction/resource checks; not Chromium or visual screenshot acceptance',status:'PASS',count:results.length,results}
fs.writeFileSync(path.join(dir,'prototype-checks.json'),JSON.stringify(report,null,2)+'\n')
console.log(`${results.length} documentation-prototype checks passed`)
