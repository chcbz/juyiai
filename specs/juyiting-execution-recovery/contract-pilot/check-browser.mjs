import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import { join, dirname } from 'node:path'
import { readFileSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import net from 'node:net'

export async function checkBrowser() {
  const web = process.env.CYF_HISTORY_WEB
  const output = dirname(process.env.CYF_HISTORY_RESULT)
  const req = createRequire(join(web, 'package.json'))
  const { createServer } = await import(pathToFileURL(req.resolve('vite')))
  const { default: vue } = await import(pathToFileURL(req.resolve('@vitejs/plugin-vue')))
  // Existing root-only headless runtime needs an owned no-sandbox launcher.
  const chromeBinary = process.env.CHROME_PATH
  assert.ok(chromeBinary && !chromeBinary.includes("'") && !chromeBinary.includes('\n'))
  const launcher = join(output, 'browser-launcher.sh')
  const chromeLog = join(output, 'browser-stderr.log')
  assert.ok(!chromeLog.includes("'") && !chromeLog.includes('\n'))
  // The shared CDP helper discards stderr; preserve startup failures in this run.
  writeFileSync(launcher, `#!/bin/sh\nexec '${chromeBinary}' --no-sandbox "$@" 2>'${chromeLog}'\n`, {mode: 0o700})
  process.env.CHROME_PATH = launcher
  const { launchChrome, stopChrome, evaluate, waitForExpression } = await import(pathToFileURL(join(web, 'scripts/juyiting/e13/lib/cdp-harness.mjs')))
  const origin = new URL(process.env.CYF_HISTORY_ORIGIN)
  assert.equal(origin.hostname, '127.0.0.1')
  const fixture = JSON.parse(readFileSync(process.env.CYF_HISTORY_CONTRACT))
  const expected = fixture.cases.filter(x => ['first-page', 'last-page'].includes(x.id)).flatMap(x => x.response.body.items.map(i => i.executionId))
  const entry = readFileSync(new URL('./browser-entry.js', import.meta.url), 'utf8').replaceAll('__WEB__', web)
  const virtual = {
    'history-entry': entry,
    'history-api-store': `export { auth as useStoreValue } from 'history-entry'; import {auth} from 'history-entry'; export const useApiStore = () => auth;`,
    'history-global-store': `import {globalStore} from 'history-entry'; export const useGlobalStore = () => globalStore;`,
    'history-execution': `import {usePersonalWorkspaceExecution as real} from '/@fs/${web}/src/composables/usePersonalWorkspaceExecution.js'; import {api} from 'history-entry'; export function usePersonalWorkspaceExecution(options) { const value = real({...options, api}); window.__historyExecution = value; /* mount history, not exact-execution recovery */ value.recover = () => value.loadHistory({adopt:false}); return value; }`,
    'history-workspace': `import {usePersonalWorkspace as real} from '/@fs/${web}/src/composables/usePersonalWorkspace.js'; export {savePersonalWorkspaceBlob} from '/@fs/${web}/src/composables/usePersonalWorkspace.js'; import {api} from 'history-entry'; export const usePersonalWorkspace = options => real({...options, api});`
  }
  const requests = [], checks = [], screenshots = {}
  let chrome, server
  const check = (name, value) => { assert.ok(value, name); checks.push(name) }
  try {
    server = await createServer({ configFile: false, envFile: false, root: web, logLevel: 'silent',
      cacheDir: join(output, 'vite-cache'), optimizeDeps: { noDiscovery: true, include: [] },
      resolve: { alias: [
        { find: '@/stores/api', replacement: 'history-api-store' },
        { find: '@/stores/global', replacement: 'history-global-store' },
        { find: '@/composables/usePersonalWorkspaceExecution', replacement: 'history-execution' },
        { find: '@/composables/usePersonalWorkspace', replacement: 'history-workspace' },
        { find: '@', replacement: join(web, 'src') }
      ] },
      plugins: [vue(), { name: 'history-fixture-mount', resolveId: id => Object.hasOwn(virtual, id) ? '\0' + id : null,
        load: id => virtual[id.slice(1)], configureServer(s) {
          s.middlewares.use((request, response, next) => {
            if (request.url !== '/') return next()
            response.setHeader('Content-Type', 'text/html; charset=utf-8')
            response.end('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}*{box-sizing:border-box}</style><div id="app"></div><script type="module" src="/@id/__x00__history-entry"></script>')
          })
        } }],
      server: { host: '127.0.0.1', port: 0, fs: { allow: [web] }, proxy: {
        '/agent': { target: origin.origin, configure(proxy) {
          proxy.on('proxyRes', (res, request) => requests.push({ path: request.url, method: request.method, status: res.statusCode, cache: res.headers['cache-control'] }))
        } }
      } }
    })
    await server.listen()
    const port = server.httpServer.address().port
    // Reserve an ephemeral discovery port; launch helper owns only its child/profile.
    const reservation = net.createServer(); await new Promise(r => reservation.listen(0, '127.0.0.1', r))
    const debugPort = reservation.address().port; await new Promise(r => reservation.close(r))
    chrome = await launchChrome({ debugPort })
    const { cdp } = chrome
    await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: `window.__historyTokens = ${process.env.CYF_HISTORY_TOKENS}` })
    const click = async selector => {
      const point = await evaluate(cdp, `(() => {const e=document.querySelector(${JSON.stringify(selector)}); if(!e||e.disabled) throw Error('Missing/disabled control'); e.scrollIntoView({block:'center'}); const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2; if(x<0||y<0||x>=innerWidth||y>=innerHeight||!e.contains(document.elementFromPoint(x,y))) throw Error('Control clipped/covered: '+${JSON.stringify(selector)}); return {x,y} })()`)
      await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 })
      await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 })
    }
    const openHistory = async () => { await click('.box-actions button:nth-child(2)'); await click('.execution-history summary') }
    const rows = n => waitForExpression(cdp, `document.querySelectorAll('.history-row').length === ${n}`)
    for (const [name, width, height] of [['desktop',1440,900], ['mobile',390,844], ['landscape',844,390]]) {
      await cdp.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: name === 'mobile' })
      await cdp.send('Page.navigate', { url: `http://127.0.0.1:${port}/` })
      await waitForExpression(cdp, 'window.__historyExecution?.historyState.value === "ready"')
      await openHistory(); await rows(20)
      check(name + ':first-page-20', await evaluate(cdp, 'window.__historyExecution.history.value.length === 20'))
      await click('.execution-history .load-more'); await rows(21)
      check(name + ':append-21-no-duplicates', JSON.stringify(await evaluate(cdp, 'window.__historyExecution.history.value.map(x=>x.executionId)')) === JSON.stringify(expected))
      check(name + ':last-page-hides-load-more', await evaluate(cdp, '!document.querySelector(".execution-history .load-more")'))
      await click('.history-heading button'); await rows(20)
      check(name + ':refresh-operable', true)
      const image = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
      const bytes = Buffer.from(image.data, 'base64'), file = `browser-${name}.png`
      writeFileSync(join(output, file), bytes); screenshots[file] = createHash('sha256').update(bytes).digest('hex')
      check(name + ':identity-clears-synchronously', await evaluate(cdp, 'window.__switchHistoryIdentity("ownerB")'))
      await openHistory()
      check(name + ':previous-rows-cleared', await evaluate(cdp, 'document.querySelectorAll(".history-row").length === 0'))
      await click('.history-heading button')
      await waitForExpression(cdp, 'window.__historyExecution.historyState.value === "empty"')
      check(name + ':empty-not-error', await evaluate(cdp, 'document.querySelector(".execution-history").textContent.includes("服务端暂无最近执行记录") && !document.querySelector(".execution-history [role=alert]")'))
      await evaluate(cdp, 'window.__switchHistoryIdentity("broken")'); await openHistory(); await click('.history-heading button')
      await waitForExpression(cdp, 'window.__historyExecution.historyState.value === "error"')
      check(name + ':503-not-empty', await evaluate(cdp, '!!document.querySelector(".execution-history [role=alert]") && !document.querySelector(".execution-history").textContent.includes("服务端暂无最近执行记录")'))
      check(name + ':no-unexpected-operation', await evaluate(cdp, 'window.__unexpected.length === 0'))
    }
    check('real-history-transport-only', requests.length >= 15 && requests.every(x => x.method === 'GET' && x.path.startsWith('/agent/personal-workspace/executions?') && x.cache?.includes('no-store')))
    check('real-503-observed', requests.filter(x => x.status === 503).length === 3)
    return { status: 'PASS', checks, requests, screenshots,
      limitations: ['Synthetic auth and standalone production component, not full Hall/OAuth', 'Ancillary files/roster/capabilities injected; initial exact-execution recovery excluded', 'No frontend formal Flow or deployment'] }
  } finally {
    if (chrome) { chrome.cdp.close(); await stopChrome(chrome.chrome, chrome.userDataDir) }
    if (server) await server.close()
  }
}
