// Development-only, offline component fixture. No production build or API auth.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root=process.env.CYF_WEB_UI_WORKTREE || '/home/isp/wsps/private-maintenance/ui-only-20261007/web';
const require=createRequire(path.join(root,'package.json'));
const {parse,compileStyle}=require('@vue/compiler-sfc');
const {createServer}=await import(pathToFileURL(require.resolve('vite')).href);
const {default:vue}=await import(pathToFileURL(require.resolve('@vitejs/plugin-vue')).href);
const fixture=fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)),'../evidence/ui-only-20261007/dev-fixture.html'),'utf8');
const hall=parse(fs.readFileSync(path.join(root,'src/components/world/JuyiHall.vue'),'utf8')).descriptor;
const css=hall.styles.map(style=>compileStyle({source:style.content,filename:'JuyiHall.vue',id:'data-v-ui-fixture',scoped:style.scoped}).code).join('\n');
const server=await createServer({configFile:false,root,plugins:[vue(),{name:'ui-only-offline-fixture',configureServer(server){server.middlewares.use(async(req,res,next)=>{const url=req.url?.split('?')[0];if(url==='/.ui-preview.html'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(await server.transformIndexHtml(url,fixture));return}if(url==='/.ui-preview.css'){res.setHeader('Content-Type','text/css; charset=utf-8');res.end(css);return}next()})}}],resolve:{alias:{'@':path.join(root,'src')}},server:{host:'127.0.0.1',port:18767,strictPort:true},optimizeDeps:{include:['vue']}});
await server.listen();console.log('Offline dev fixture http://127.0.0.1:18767/.ui-preview.html');
for(const signal of ['SIGTERM','SIGINT'])process.once(signal,async()=>{await server.close();process.exit(0)});
