#!/usr/bin/env node
import { spawn } from 'node:child_process'
import { createHash, X509Certificate } from 'node:crypto'
import { access, lstat, mkdir, mkdtemp, readFile, realpath, rm, stat, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { basename, join, resolve } from 'node:path'
import { lookup } from 'node:dns/promises'
import { isIP } from 'node:net'
import { setTimeout as delay } from 'node:timers/promises'

const FRONTEND_URL = process.env.H06_FRONTEND_URL || ''
const BACKEND_URL = process.env.H06_BACKEND_URL || ''
const CA_FILE = resolve(process.env.H06_BROWSER_CA_FILE || '')
const CERT_SPKI = process.env.H06_BROWSER_CERT_SPKI || ''
const EVIDENCE_DIR = resolve(process.env.H06_BROWSER_EVIDENCE_DIR || '')
const TOKEN_FILE = resolve(process.env.H06_BROWSER_TOKEN_FILE || '')
const CHROME_LAUNCHER_SHA256 = process.env.H06_CHROME_LAUNCHER_SHA256 || ''
const CHROME_EXECUTABLE_SHA256 = process.env.H06_CHROME_EXECUTABLE_SHA256 || ''
const ISOLATED_HOSTS_FILE = resolve(process.env.H06_ISOLATED_HOSTS_FILE || '')
const CHROME_CANDIDATES = process.env.H06_CHROME_PATH
  ? [process.env.H06_CHROME_PATH]
  : ['/usr/local/bin/chromium-headless-smoke', '/usr/bin/chromium-browser', '/usr/bin/chromium']
const TIMEOUT_MS = Number(process.env.H06_BROWSER_TIMEOUT_MS || 90000)
const CDP_TIMEOUT_MS = Number(process.env.H06_CDP_TIMEOUT_MS || 45000)
const REQUIRED_RESPONDER = { id: 'archive-clerk-v1', displayName: '案卷书吏', mode: 'fallback' }
const QUESTION_PATH = /\/archive\/v1\/me\/questions\/[0-9a-f-]+$/
const FORBIDDEN_ROUTING_KEYS = new Set(['agentId', 'agent_id', 'model', 'provider', 'route', 'routing', 'responder', 'responderId'])
const TOKEN_MARKERS = ['authorization', 'cookie', 'set-cookie', 'proxy-authorization']

if (!FRONTEND_URL || !BACKEND_URL || !process.env.H06_BROWSER_EVIDENCE_DIR || !process.env.H06_BROWSER_TOKEN_FILE || !process.env.H06_BROWSER_CA_FILE || !CERT_SPKI || !CHROME_LAUNCHER_SHA256 || !CHROME_EXECUTABLE_SHA256 || !process.env.H06_ISOLATED_HOSTS_FILE) {
  throw new Error('explicit isolated URLs, CA/SPKI, token, Chromium digests and isolated hosts file are required')
}

const assertPhysical = async (path, label) => {
  let info
  try { info = await lstat(path) } catch (error) { throw new Error(`${label} is unavailable: ${path}: ${error.message}`) }
  if (info.isSymbolicLink() || !info.isFile()) throw new Error(`${label} must be one physical regular file: ${path}`)
}
const sha256 = value => createHash('sha256').update(value).digest('hex')
const isLoopbackLiteral = host => {
  const kind = isIP(host)
  if (kind === 6) return host === '::1'
  if (kind !== 4) return false
  const octets = host.split('.').map(value => Number.parseInt(value, 10))
  return octets.length === 4 && octets.every(value => Number.isInteger(value) && value >= 0 && value <= 255) && octets[0] === 127
}
const isolatedHosts = new Map()
for (const rawLine of (await readFile(ISOLATED_HOSTS_FILE, 'utf8')).split(/\r?\n/)) {
  const line = rawLine.replace(/#.*/, '').trim()
  if (!line) continue
  const [address, ...names] = line.split(/\s+/)
  if (!isLoopbackLiteral(address)) throw new Error(`isolated hosts file contains non-loopback address: ${address}`)
  for (const name of names) {
    if (!name.endsWith('.h06.invalid')) continue
    const values = isolatedHosts.get(name) || new Set(); values.add(address); isolatedHosts.set(name, values)
  }
}
const assertIsolatedUrl = async (raw, label) => {
  const url = new URL(raw)
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error(`${label} must be a credential-free isolated origin with root path only`)
  if (url.protocol !== 'https:' || !url.port || url.port === '443') throw new Error(`${label} must be explicit isolated HTTPS on a non-443 port`)
  const normalizedHost = url.hostname.startsWith('[') && url.hostname.endsWith(']') ? url.hostname.slice(1, -1) : url.hostname
  const hostKind = isIP(normalizedHost)
  if (hostKind) {
    if (!isLoopbackLiteral(normalizedHost)) throw new Error(`${label} literal IP is not in 127/8 or ::1`)
  } else {
    if (!normalizedHost.endsWith('.h06.invalid') || !isolatedHosts.has(normalizedHost)) throw new Error(`${label} hostname is not fixed by the isolated hosts file`)
    const expected = isolatedHosts.get(normalizedHost)
    const addresses = await lookup(normalizedHost, { all: true })
    if (!addresses.length || addresses.some(({ address }) => !isLoopbackLiteral(address) || !expected.has(address))) throw new Error(`${label} resolution differs from the fixed isolated hosts mapping`)
  }
  return url.origin
}

if (typeof globalThis.WebSocket !== 'function') throw new Error('candidate-pinned Node runtime lacks a native WebSocket implementation')
const WebSocket = globalThis.WebSocket

const json = value => `${JSON.stringify(value, null, 2)}\n`
const exists = async path => { try { await access(path); return true } catch { return false } }
const findChrome = async () => {
  for (const path of CHROME_CANDIDATES) if (await exists(path)) return resolve(path)
  throw new Error('Chromium unavailable; set H06_CHROME_PATH to an isolated browser binary')
}
const requestJson = async (url, options = {}) => {
  const response = await fetch(url, { ...options, signal: options.signal || AbortSignal.timeout(15000) })
  if (!response.ok) throw new Error(`${url} returned ${response.status}: ${(await response.text()).slice(0, 500)}`)
  return response.json()
}
const waitForJson = async (url) => {
  const deadline = Date.now() + 20000
  let error
  while (Date.now() < deadline) {
    try { return await requestJson(url) } catch (caught) { error = caught; await delay(200) }
  }
  throw error || new Error(`timed out waiting for ${url}`)
}
const sanitizeHeaders = headers => Object.fromEntries(Object.entries(headers || {}).map(([key, value]) => [
  key,
  TOKEN_MARKERS.includes(key.toLowerCase()) ? '[REDACTED]' : String(value).slice(0, 2000)
]))

class CdpSession {
  constructor (url) {
    this.ws = new WebSocket(url)
    this.nextId = 1
    this.pending = new Map()
    this.handlers = new Map()
    this.handlerErrors = []
  }

  async open () {
    await new Promise((resolve, reject) => {
      this.ws.addEventListener('open', resolve, { once: true })
      this.ws.addEventListener('error', reject, { once: true })
    })
    this.ws.addEventListener('message', event => {
      const message = JSON.parse(event.data)
      if (message.id && this.pending.has(message.id)) {
        const pending = this.pending.get(message.id)
        this.pending.delete(message.id)
        clearTimeout(pending.timer)
        if (message.error) pending.reject(new Error(message.error.message))
        else pending.resolve(message.result || {})
      } else if (message.method && this.handlers.has(message.method)) {
        Promise.resolve(this.handlers.get(message.method)(message.params || {})).catch(error => this.handlerErrors.push(error))
      }
    })
  }

  on (method, handler) { this.handlers.set(method, handler) }
  throwHandlerErrors () { if (this.handlerErrors.length) throw this.handlerErrors.shift() }
  send (method, params = {}) {
    const id = this.nextId++
    this.ws.send(JSON.stringify({ id, method, params }))
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        if (this.pending.delete(id)) reject(new Error(`${method} timed out`))
      }, CDP_TIMEOUT_MS)
      this.pending.set(id, { resolve, reject, timer })
    })
  }
  close () { this.ws.close() }
}

const evaluate = async (cdp, expression) => {
  cdp.throwHandlerErrors()
  const result = await cdp.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text)
  return result.result?.value
}
const waitFor = async (cdp, expression, timeout = TIMEOUT_MS) => {
  const deadline = Date.now() + timeout
  let last
  while (Date.now() < deadline) {
    try { last = await evaluate(cdp, expression) } catch (error) { last = error.message }
    if (last) return last
    await delay(250)
  }
  throw new Error(`timed out waiting for ${expression}; last=${JSON.stringify(last)}`)
}
const click = (cdp, selector) => evaluate(cdp, `(() => { const e=document.querySelector(${JSON.stringify(selector)}); if(!e) return false; e.click(); return true })()`)
const fill = (cdp, selector, value) => evaluate(cdp, `(() => { const e=document.querySelector(${JSON.stringify(selector)}); if(!e) return false; const setter=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e),'value')?.set; setter.call(e,${JSON.stringify(value)}); e.dispatchEvent(new Event('input',{bubbles:true})); return true })()`)
const screenshot = async (cdp, name) => {
  const result = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
  await writeFile(join(EVIDENCE_DIR, 'screenshots', `${name}.png`), Buffer.from(result.data, 'base64'))
}
const run = (command, args) => new Promise((resolve, reject) => {
  const child = spawn(command, args, { stdio: ['ignore', 'pipe', 'pipe'] }); let output = ''
  child.stdout.on('data', chunk => { output += chunk }); child.stderr.on('data', chunk => { output += chunk })
  child.on('error', reject); child.on('exit', code => code === 0 ? resolve(output) : reject(new Error(`${command} exited ${code}: ${output.slice(-2000)}`)))
})

const stopChrome = async (chrome, profile) => {
  let exited = chrome.exitCode !== null
  chrome.once('exit', () => { exited = true })
  if (!exited) chrome.kill('SIGTERM')
  await Promise.race([new Promise(resolve => chrome.once('exit', resolve)), delay(3000)])
  if (!exited) {
    chrome.kill('SIGKILL')
    await Promise.race([new Promise(resolve => chrome.once('exit', resolve)), delay(2000)])
  }
  await rm(profile, { recursive: true, force: true })
}

const openLibrary = async cdp => {
  await waitFor(cdp, 'Boolean(document.querySelector(".hall-board.is-melon-ready .melon-layer canvas"))')
  const point = await evaluate(cdp, `(() => {
    let game=window.__JYTING_GAME__; let component=document.querySelector('.hall-stage')?.__vueParentComponent;
    while(!game&&component){ game=component.setupState?.juyitingGame; component=component.parent }
    const canvas=document.querySelector('.melon-layer canvas'); const rect=canvas?.getBoundingClientRect();
    const viewport=game?.getSceneDebugSnapshot?.().camera?.viewport;
    const area=game?._hallScene?._hitProvider?.().hotspots?.find(item=>item.id==='library-shelf');
    if(!canvas||!rect?.width||!viewport?.width||!area?.bounds) return null;
    const target={x:area.bounds.x+area.bounds.width/2,y:area.bounds.y+area.bounds.height/2};
    game.panBy?.(viewport.width/2-target.x,viewport.height/2-target.y);
    const fresh=game?._hallScene?._hitProvider?.().hotspots?.find(item=>item.id==='library-shelf')?.bounds;
    if(!fresh) return null; const p={x:fresh.x+fresh.width/2,y:fresh.y+fresh.height/2};
    const scale=Math.max(rect.width/viewport.width,rect.height/viewport.height);
    return {x:rect.left+(rect.width-viewport.width*scale)/2+p.x*scale,y:rect.top+(rect.height-viewport.height*scale)/2+p.y*scale};
  })()`)
  if (!point) throw new Error('library-shelf hotspot unavailable')
  await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'left', buttons: 1, clickCount: 1 })
  await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'left', buttons: 0, clickCount: 1 })
  await waitFor(cdp, 'Boolean(document.querySelector(".panel-library"))')
}

const readDomState = cdp => evaluate(cdp, `(() => ({
  title:document.title,
  panel:Boolean(document.querySelector('.panel-library')),
  readerTab:document.querySelector('#library-reader-tab')?.getAttribute('aria-selected'),
  searchTab:document.querySelector('#library-search-tab')?.getAttribute('aria-selected'),
  heading:document.querySelector('.reader-content h4')?.textContent?.trim()||'',
  paragraphIds:[...document.querySelectorAll('.reader-paragraph[data-paragraph-id]')].map(e=>e.dataset.paragraphId),
  notes:[...document.querySelectorAll('.reader-notes li p')].map(e=>e.textContent.trim()),
  bookmarks:[...document.querySelectorAll('.reader-notes .bookmark-list li, .reader-notes li')].map(e=>e.textContent.trim()),
  question:document.querySelector('.archive-question-result')?.innerText||'',
  body:(document.body.innerText||'').slice(0,12000)
}))()`)

const main = async () => {
  const frontendOrigin = await assertIsolatedUrl(FRONTEND_URL, 'frontend URL')
  const backendOrigin = await assertIsolatedUrl(BACKEND_URL, 'backend URL')
  if (frontendOrigin === backendOrigin) throw new Error('frontend/backend isolated origins must be distinct')
  await assertPhysical(CA_FILE, 'browser CA certificate')
  const caCertificate = new X509Certificate(await readFile(CA_FILE))
  const actualSpki = createHash('sha256').update(caCertificate.publicKey.export({ type: 'spki', format: 'der' })).digest('base64')
  if (actualSpki !== CERT_SPKI) throw new Error('browser CA SPKI does not match the explicit isolated pin')
  await assertPhysical(TOKEN_FILE, 'browser token file')
  if (!/^[A-Za-z0-9+/]{43}=$/.test(CERT_SPKI)) throw new Error('isolated certificate SPKI pin is invalid')
  await mkdir(join(EVIDENCE_DIR, 'screenshots'), { recursive: true })
  const token = (await readFile(TOKEN_FILE, 'utf8')).trim()
  if (!token || token.split('.').length !== 3) throw new Error('browser token file does not contain a JWT')
  const tokenHash = sha256(token)
  const chromePath = await findChrome()
  await assertPhysical(chromePath, 'Chromium launcher')
  const launcherStat = await stat(chromePath)
  if (launcherStat.uid !== 0 || (launcherStat.mode & 0o022) !== 0) throw new Error('Chromium launcher must be root-owned and not writable by group/other')
  const launcherBytes = await readFile(chromePath)
  if (sha256(launcherBytes) !== CHROME_LAUNCHER_SHA256) throw new Error('Chromium launcher digest differs from trusted expected digest')
  let executablePath = await realpath(chromePath)
  const launcherText = launcherBytes.toString('utf8')
  const execMatch = launcherText.match(/^exec\s+(\/[^\s]+chromium[^\s]*)/m)
  if (execMatch) {
    let target
    try { await lstat(execMatch[1]); target = await realpath(execMatch[1]) } catch (error) { throw new Error(`Chromium wrapper target is broken: ${execMatch[1]}: ${error.message}`) }
    await assertPhysical(target, 'resolved Chromium wrapper target'); executablePath = target
  }
  const executableBytes = await readFile(executablePath)
  if (sha256(executableBytes) !== CHROME_EXECUTABLE_SHA256) throw new Error('Chromium executable digest differs from trusted expected digest')
  const versionText = await new Promise((resolve, reject) => {
    const child = spawn(chromePath, ['--version'], { stdio: ['ignore', 'pipe', 'pipe'] })
    let output = ''; child.stdout.on('data', chunk => { output += chunk }); child.stderr.on('data', chunk => { output += chunk })
    child.on('error', reject); child.on('exit', code => code === 0 ? resolve(output.trim()) : reject(new Error(`chromium --version exited ${code}`)))
  })
  await writeFile(join(EVIDENCE_DIR, 'browser-binary.json'), json({
    launcherPath: chromePath, launcherBasename: basename(chromePath), launcherSha256: sha256(launcherBytes), caCertificateSha256: sha256(await readFile(CA_FILE)), certificateSpkiSha256Base64: CERT_SPKI,
    executablePath, executableBasename: basename(executablePath), executableSha256: sha256(executableBytes), version: versionText
  }))

  const profile = await mkdtemp(join(tmpdir(), 'cyf-h06-browser-'))
  try {
    await run('/usr/bin/certutil', ['-N', '--empty-password', '-d', `sql:${profile}`])
    await run('/usr/bin/certutil', ['-A', '-d', `sql:${profile}`, '-n', 'CYF H06 isolated CA', '-t', 'C,,', '-i', CA_FILE])
  } catch (error) { await rm(profile, { recursive: true, force: true }); throw error }
  const debugPort = 52111
  const chrome = spawn(chromePath, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run',
    '--no-default-browser-check', '--disable-background-networking', '--disable-component-update',
    '--disable-default-apps', '--disable-sync', '--metrics-recording-only',
    '--window-size=1440,1000', `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, 'about:blank'
  ], { stdio: ['ignore', 'ignore', 'pipe'] })
  let stderr = ''
  chrome.stderr.on('data', chunk => { stderr += chunk.toString().slice(0, 10000) })
  let cdp
  const network = []
  const requests = new Map()
  let questionWire = null
  try {
    const version = await waitForJson(`http://127.0.0.1:${debugPort}/json/version`)
    const target = await requestJson(`http://127.0.0.1:${debugPort}/json/new?about:blank`, { method: 'PUT' })
    cdp = new CdpSession(target.webSocketDebuggerUrl || version.webSocketDebuggerUrl)
    await cdp.open()
    await Promise.all([cdp.send('Page.enable'), cdp.send('Runtime.enable'), cdp.send('Network.enable')])
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true })
    await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: `(() => {
      const original = window.fetch.bind(window)
      window.__H06_SSE__ = []
      window.__H06_SSE_META__ = { questionPutResolvedAt: null, streamOpenedAt: null }
      window.fetch = async (...args) => {
        const response = await original(...args)
        try {
          const method = String(args[1]?.method || args[0]?.method || 'GET').toUpperCase()
          const url = String(response.url || args[0]?.url || args[0] || '')
          if (method === 'PUT' && /\\/archive\\/v1\\/me\\/questions\\/[^/]+(?:\\?|$)/.test(url)) window.__H06_SSE_META__.questionPutResolvedAt = performance.now()
          if (/\\/archive\\/v1\\/me\\/questions\\/[^/]+\\/events(?:\\?|$)/.test(url) && response.ok && response.body) {
            window.__H06_SSE_META__.streamOpenedAt = performance.now()
            window.__H06_SSE_META__.streamStatus = response.status
            window.__H06_SSE_META__.streamContentType = response.headers.get('content-type') || ''
            const clone = response.clone(); const reader = clone.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
            ;(async () => { try { while (true) { const { done, value } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }).replace(/\\r\\n/g, '\\n'); let cut; while ((cut = buffer.indexOf('\\n\\n')) >= 0) { const block = buffer.slice(0, cut); buffer = buffer.slice(cut + 2); const frame = { event: '', id: '', data: null }; for (const line of block.split('\\n')) { if (line.startsWith('event:')) frame.event = line.slice(6).trim(); else if (line.startsWith('id:')) frame.id = line.slice(3).trim(); else if (line.startsWith('data:')) { try { frame.data = JSON.parse(line.slice(5).trim()) } catch {} } } if (frame.event) { frame.receivedAt = performance.now(); window.__H06_SSE__.push(frame) } } } } catch (error) { window.__H06_SSE__.push({ event: '__capture_error__', message: String(error) }) } })()
          }
        } catch (error) { window.__H06_SSE__.push({ event: '__instrument_error__', message: String(error) }) }
        return response
      }
    })()` })
    cdp.on('Network.requestWillBeSent', params => {
      const request = params.request || {}
      const entry = { requestId: params.requestId, method: request.method, url: request.url, headers: sanitizeHeaders(request.headers), timestamp: params.timestamp }
      if (request.postData && !QUESTION_PATH.test(new URL(request.url).pathname)) entry.postDataSha256 = sha256(request.postData)
      if (QUESTION_PATH.test(new URL(request.url).pathname) && request.method === 'PUT') {
        let body
        try { body = JSON.parse(request.postData || '') } catch { throw new Error('question request body is not JSON') }
        const keys = Object.keys(body).sort()
        if (keys.join(',') !== 'anchor,question') throw new Error(`question request keys are not exact: ${keys.join(',')}`)
        if (keys.some(key => FORBIDDEN_ROUTING_KEYS.has(key))) throw new Error('question request contains routing field')
        questionWire = { method: request.method, path: new URL(request.url).pathname, keys, body }
      }
      requests.set(params.requestId, entry); network.push(entry)
    })
    cdp.on('Network.webSocketCreated', params => {
      const origin = new URL(params.url).origin.replace(/^ws/, 'http')
      if (![frontendOrigin, backendOrigin].includes(origin)) cdp.handlerErrors.push(new Error(`browser attempted non-isolated WebSocket origin: ${origin}`))
      network.push({ type: 'websocket', url: params.url, requestId: params.requestId })
    })
    cdp.on('Network.responseReceived', params => {
      const entry = requests.get(params.requestId)
      if (entry) { entry.status = params.response?.status; entry.responseHeaders = sanitizeHeaders(params.response?.headers || {}); entry.mimeType = params.response?.mimeType }
    })
    await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: `localStorage.setItem('api_token', ${JSON.stringify(JSON.stringify({ data: token, expTime: Date.now() + 86400000 }))})` })
    await cdp.send('Page.navigate', { url: `${FRONTEND_URL}/juyiting?transition=none&scene-debug=1` })
    await waitFor(cdp, 'Boolean(document.querySelector(".juyi-page"))')
    await openLibrary(cdp)
    await waitFor(cdp, 'Boolean(document.querySelector("[aria-label=\\"典籍阅读\\"]")) && document.querySelectorAll(".reader-catalog button").length===121')
    const catalog = await evaluate(cdp, `(() => ({count:document.querySelectorAll('.reader-catalog button').length, labels:[...document.querySelectorAll('.reader-catalog button')].map(e=>e.textContent.trim())}))()`)
    if (catalog.count !== 121 || !catalog.labels.some(label => label.startsWith('第1回')) || !catalog.labels.some(label => label.startsWith('第120回'))) throw new Error(`catalog invariant failed: ${JSON.stringify(catalog)}`)

    await evaluate(cdp, `(() => { const e=[...document.querySelectorAll('.reader-catalog button')].find(e=>e.textContent.trim().startsWith('第1回')); e.click(); return true })()`)
    await waitFor(cdp, 'document.querySelector(".reader-content h4")?.textContent?.includes("第1回")')
    await waitFor(cdp, 'document.querySelectorAll(".reader-paragraph[data-paragraph-id]").length >= 2')
    const ch1 = await readDomState(cdp)
    await screenshot(cdp, 'chapter-001')

    await evaluate(cdp, `(() => { const p=document.querySelector('.reader-paragraph[data-paragraph-id]'); p.focus(); p.click(); return p.dataset.paragraphId })()`)
    await click(cdp, '.bookmark-create')
    await waitFor(cdp, 'document.querySelectorAll(".bookmark-delete").length >= 1')
    const noteText = `H06孤立手札-${Date.now()}`
    await fill(cdp, '[aria-label="当前段落私人手札"]', noteText)
    await click(cdp, '.note-save')
    await waitFor(cdp, `document.querySelector('.reader-notes')?.innerText.includes(${JSON.stringify(noteText)})`)
    await delay(1200)

    const selection = await evaluate(cdp, `(() => {
      const p=[...document.querySelectorAll('.reader-paragraph[data-paragraph-id]')].slice(0,2);
      if(p.length!==2||!p[0].firstChild||!p[1].firstChild) return null;
      const r=document.createRange(); r.setStart(p[0].firstChild,Math.min(1,p[0].firstChild.length-1)); r.setEnd(p[1].firstChild,Math.min(8,p[1].firstChild.length));
      const s=getSelection(); s.removeAllRanges(); s.addRange(r); return {text:s.toString(),ids:p.map(e=>e.dataset.paragraphId)};
    })()`)
    if (!selection?.text || !/[^\x00-\x7f]/.test(selection.text) || selection.ids.length !== 2) throw new Error(`cross-paragraph Chinese selection failed: ${JSON.stringify(selection)}`)
    await fill(cdp, '[aria-label="向案卷书吏提问"]', '请说明这两段之间的叙事联系。')
    await click(cdp, '.question-create')
    await waitFor(cdp, 'Boolean(document.querySelector(".archive-question-result"))')
    await waitFor(cdp, `(() => { const t=document.querySelector('.archive-question-result')?.innerText||''; return t.includes('SUCCEEDED') })()`, 120000)
    await waitFor(cdp, `(() => (window.__H06_SSE__||[]).some(e => e.event === 'QUESTION_SUCCEEDED' || e.data?.eventType === 'QUESTION_SUCCEEDED'))()`, 120000)
    const questionDom = await evaluate(cdp, `(() => ({text:document.querySelector('.archive-question-result')?.innerText||'',responder:(document.body.innerText||'').includes('archive-clerk-v1')&&(document.body.innerText||'').includes('案卷书吏')&&(document.body.innerText||'').includes('fallback')}))()`)
    if (!questionDom.responder || !questionDom.text.includes('SUCCEEDED')) throw new Error('successful fixed responder terminal is absent from DOM')
    if (!questionWire) throw new Error('question PUT wire was not captured')
    const sseFrames = await evaluate(cdp, 'window.__H06_SSE__ || []')
    const eventType = frame => frame.data?.eventType || frame.data?.type || frame.event || ''
    const terminalIndex = sseFrames.findIndex(frame => eventType(frame) === 'QUESTION_SUCCEEDED')
    const queuedIndex = sseFrames.findIndex(frame => eventType(frame) === 'QUESTION_QUEUED')
    const runningIndex = sseFrames.findIndex(frame => eventType(frame) === 'QUESTION_RUNNING')
    const sseMeta = await evaluate(cdp, 'window.__H06_SSE_META__ || {}')
    if (!(queuedIndex >= 0 && runningIndex > queuedIndex && terminalIndex > runningIndex)) throw new Error(`live successful SSE sequence missing/out of order: ${JSON.stringify(sseFrames)}`)
    const terminalFrame = sseFrames[terminalIndex]
    if (!(sseMeta.streamStatus === 200 && String(sseMeta.streamContentType || '').includes('text/event-stream') && Number.isFinite(sseMeta.questionPutResolvedAt) && Number.isFinite(sseMeta.streamOpenedAt) && Number.isFinite(terminalFrame.receivedAt) && sseMeta.questionPutResolvedAt <= sseMeta.streamOpenedAt && sseMeta.streamOpenedAt < terminalFrame.receivedAt)) throw new Error(`SSE terminal was not observed after a real successful stream open: ${JSON.stringify({ sseMeta, terminalFrame })}`)
    const terminalFrames = sseFrames.slice(queuedIndex, terminalIndex + 1)
    const canonicalDecimal = value => /^(0|[1-9][0-9]*)$/.test(value)
    const maxSequence = 9223372036854775807n
    const rawIds = terminalFrames.map(frame => String(frame.id ?? ''))
    if (rawIds.length < 3 || rawIds.some(value => !canonicalDecimal(value))) throw new Error(`SSE IDs are not canonical decimal strings: ${JSON.stringify(rawIds)}`)
    for (const frame of terminalFrames) {
      const dataSequence = String(frame.data?.sequence ?? '')
      if (!canonicalDecimal(dataSequence) || frame.id !== dataSequence) throw new Error(`SSE id/data.sequence mismatch: ${JSON.stringify(frame)}`)
      const sequence = BigInt(dataSequence)
      if (sequence < 0n || sequence > maxSequence) throw new Error(`SSE sequence outside signed BIGINT range: ${dataSequence}`)
    }
    const ids = rawIds.map(value => BigInt(value))
    if (ids.some((value, index) => index && value <= ids[index - 1])) throw new Error(`SSE sequence IDs are not strictly increasing: ${JSON.stringify(rawIds)}`)
    const questionId = questionWire.path.split('/').pop()
    const recovery = await evaluate(cdp, `(async () => {
      const token=${JSON.stringify(token)}; const base=${JSON.stringify(BACKEND_URL)}; const questionId=${JSON.stringify(questionId)};
      const firstFrame=async cursor=>{ const controller=new AbortController(); const response=await fetch(base+'/archive/v1/me/questions/'+questionId+'/events',{headers:{Authorization:'Bearer '+token,Accept:'text/event-stream','Last-Event-ID':cursor},signal:controller.signal}); const reader=response.body?.getReader(); const decoder=new TextDecoder(); let text=''; if(reader){ while(!text.includes('\\n\\n')){ const item=await reader.read(); if(item.done) break; text+=decoder.decode(item.value,{stream:true}).replace(/\\r\\n/g,'\\n') } } controller.abort(); return {status:response.status,contentType:response.headers.get('content-type')||'',firstFrame:text.split('\\n\\n')[0]||''} };
      const ahead=await firstFrame('9223372036854775807');
      const overflow=await fetch(base+'/archive/v1/me/questions/'+questionId+'/events',{headers:{Authorization:'Bearer '+token,'Last-Event-ID':'9223372036854775808'}});
      const noncanonical=await fetch(base+'/archive/v1/me/questions/'+questionId+'/events',{headers:{Authorization:'Bearer '+token,'Last-Event-ID':'00'}});
      const snapshotResponse=await fetch(base+'/archive/v1/me/questions/'+questionId,{headers:{Authorization:'Bearer '+token,Accept:'application/json'}}); const snapshot=await snapshotResponse.json();
      return {ahead,overflowStatus:overflow.status,noncanonicalStatus:noncanonical.status,snapshotStatus:snapshotResponse.status,snapshot:snapshot?.data||snapshot};
    })()`)
    if (recovery.ahead.status !== 200 || !/event:\s*resync_required/.test(recovery.ahead.firstFrame) || !/"type"\s*:\s*"resync_required"/.test(recovery.ahead.firstFrame)) throw new Error(`cursor-ahead did not produce resync_required: ${JSON.stringify(recovery)}`)
    if (recovery.overflowStatus !== 400 || recovery.noncanonicalStatus !== 400) throw new Error(`overflow/noncanonical cursor was not rejected: ${JSON.stringify(recovery)}`)
    if (recovery.snapshotStatus !== 200 || recovery.snapshot?.questionId !== questionId || !canonicalDecimal(String(recovery.snapshot?.currentSequence || ''))) throw new Error(`resync snapshot replacement unavailable: ${JSON.stringify(recovery)}`)
    const sseTerminal = { liveStreamOpenedBeforeTerminal: true, frames: terminalFrames, sequenceIds: rawIds, cursorAheadResyncRequired: true, overflowRejected: true, noncanonicalRejected: true, snapshotReplacement: recovery.snapshot, result: 'QUESTION_SUCCEEDED' }
    await screenshot(cdp, 'question-terminal')

    await cdp.send('Page.reload', { ignoreCache: true })
    await waitFor(cdp, 'Boolean(document.querySelector(".juyi-page"))')
    await openLibrary(cdp)
    await waitFor(cdp, `document.querySelector('.reader-notes')?.innerText.includes(${JSON.stringify(noteText)})`)
    const reloadState = await readDomState(cdp)
    if (!reloadState.body.includes(noteText)) throw new Error('note did not survive reload')
    const persisted = await evaluate(cdp, `(() => ({bookmarkCount:document.querySelectorAll('.bookmark-delete').length,heading:document.querySelector('.reader-content h4')?.textContent?.trim()||''}))()`)
    if (persisted.bookmarkCount < 1) throw new Error('bookmark did not survive reload')
    if (!persisted.heading.includes('第1回')) throw new Error(`progress did not restore chapter 1: ${persisted.heading}`)

    await evaluate(cdp, `(() => { const e=[...document.querySelectorAll('.reader-catalog button')].find(e=>e.textContent.trim().startsWith('第120回')); e.click(); return true })()`)
    await waitFor(cdp, 'document.querySelector(".reader-content h4")?.textContent?.includes("第120回")')
    const ch120 = await readDomState(cdp)
    await screenshot(cdp, 'chapter-120')
    if (!(await click(cdp, '[aria-label="上一回"]'))) throw new Error('previous button missing')
    await waitFor(cdp, '!document.querySelector(".reader-content h4")?.textContent?.includes("第120回")')
    if (!(await click(cdp, '[aria-label="下一回"]'))) throw new Error('next button missing')
    await waitFor(cdp, 'document.querySelector(".reader-content h4")?.textContent?.includes("第120回")')

    const legacyBeforeExplicitSearch = network.filter(item => item.url.includes('/chat/library/search')).length
    if (legacyBeforeExplicitSearch !== 0) throw new Error(`archive flow made ${legacyBeforeExplicitSearch} accidental legacy search requests`)
    await click(cdp, '#library-search-tab')
    await waitFor(cdp, 'document.querySelector("#library-search-tab")?.getAttribute("aria-selected")==="true"')
    await fill(cdp, '[aria-label="案卷检索关键词"]', 'H06不存在关键词')
    await evaluate(cdp, `(() => { const f=document.querySelector('.library-search'); f.requestSubmit(); return true })()`)
    await waitFor(cdp, `(() => { const t=document.querySelector('.library-search-tab')?.innerText||''; return t.includes('暂未查得案卷')||t.includes('得 0 条') })()`)
    await screenshot(cdp, 'legacy-search-empty')

    for (const item of network) {
      if (!/^https?:/.test(item.url)) continue
      const origin = new URL(item.url).origin
      if (![frontendOrigin, backendOrigin].includes(origin)) throw new Error(`browser attempted non-isolated network origin: ${origin}`)
    }

    const archiveQuestionRequests = network.filter(item => item.url.includes('/archive/v1/me/questions/'))
    const legacyRequests = network.filter(item => item.url.includes('/chat/library/search'))
    if (legacyBeforeExplicitSearch !== 0) throw new Error('archive question flow accidentally requested legacy search')
    if (legacyRequests.length !== 1) throw new Error(`expected exactly one deliberate legacy search request, observed ${legacyRequests.length}`)
    const sseObserved = archiveQuestionRequests.some(item => item.url.includes('/events'))
    const snapshotObserved = archiveQuestionRequests.some(item => item.method === 'GET' && !item.url.includes('/events'))
    if (!sseObserved) throw new Error('successful question SSE transport was not observed')
    if (!snapshotObserved) throw new Error('terminal question snapshot transport was not observed')

    await writeFile(join(EVIDENCE_DIR, 'browser-network.json'), json(network))
    await writeFile(join(EVIDENCE_DIR, 'question-wire.json'), json({ ...questionWire, bodySha256: sha256(JSON.stringify(questionWire.body)), body: questionWire.body }))
    await writeFile(join(EVIDENCE_DIR, 'browser-dom.json'), json({ catalog, ch1, ch120, reloadState, questionDom, selection }))
    await writeFile(join(EVIDENCE_DIR, 'question-sse-terminal.json'), json(sseTerminal))
    await writeFile(join(EVIDENCE_DIR, 'browser-result.json'), json({
      result: 'PASS', tokenSha256: tokenHash, catalog: true, chapter1: true, chapter120: true,
      progressReload: true, bookmarkReload: true, noteReload: true, crossParagraphQuestion: true,
      responder: REQUIRED_RESPONDER, questionWireExact: true, successfulSseTerminal: true, cursorAheadResyncRequired: true, overflowCursorRejected: true, snapshotReplacement: true, snapshotTerminal: true,
      legacySearchGracefulEmpty: true, archiveToLegacyAccidentalRequests: 0
    }))
    console.log(`H06_BROWSER=PASS EVIDENCE=${EVIDENCE_DIR}`)
  } catch (error) {
    await writeFile(join(EVIDENCE_DIR, 'browser-failure.json'), json({ result: 'FAIL', message: error.message, chromiumStderrTail: stderr.slice(-4000) }))
    throw error
  } finally {
    cdp?.close()
    await stopChrome(chrome, profile)
  }
}

await main()
