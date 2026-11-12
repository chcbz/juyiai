// Real frontend state -> production createApi/useHttp -> loopback Java -> MySQL.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import { resolve, join } from 'node:path'
import { execFileSync } from 'node:child_process'
const fixtureBytes = readFileSync(process.env.CYF_HISTORY_CONTRACT)
const fixture = JSON.parse(fixtureBytes)
const web = resolve(process.env.CYF_HISTORY_WEB)
const origin = process.env.CYF_HISTORY_ORIGIN
const url = new URL(origin)
assert.equal(url.protocol, 'http:'); assert.equal(url.hostname, '127.0.0.1')
assert.equal(url.pathname, '/'); assert.ok(!url.username && !url.password)
const git = (...args) => execFileSync('git', ['-C', web, ...args], { encoding: 'utf8', env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' } }).trim()
assert.equal(git('rev-parse', 'HEAD'), fixture.source.webCommit)
assert.equal(git('status', '--porcelain'), '')
const requireWeb = createRequire(join(web, 'package.json'))
const { ref } = requireWeb('vue')
const { usePersonalWorkspaceExecution } = await import(pathToFileURL(join(web, 'src/composables/usePersonalWorkspaceExecution.js')))
const { createApi } = await import(pathToFileURL(join(web, 'src/composables/useHttp.js')))
const tokens = JSON.parse(process.env.CYF_HISTORY_TOKENS)
const actualFetch = globalThis.fetch
const observations = []
// Restrict transport; never synthesize a response or suppress an actual network failure.
globalThis.fetch = async (input, options = {}) => {
  const target = new URL(input)
  assert.equal(target.origin, origin)
  assert.equal(options.method || 'GET', 'GET')
  assert.ok(target.pathname.startsWith('/agent/personal-workspace/executions'))
  const response = await actualFetch(input, { ...options, redirect: 'error' })
  observations.push({ path: target.pathname, status: response.status, cache: response.headers.get('cache-control') })
  return response
}
const storage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
let assertions = 0
function adapterFor(identity) {
  const epoch = ref(identity)
  const authStore = { authorizationGeneration: 0, token: async () => tokens[epoch.value] }
  const api = createApi(`${origin}/agent`)
  const adapter = usePersonalWorkspaceExecution({ identityEpoch: epoch, identityScope: epoch, storage,
    api: { execute: options => api.execute({ ...options, authStore, rum: false }) } })
  return { adapter, epoch, authStore }
}
try {
  const first = fixture.cases.find(c => c.id === 'first-page')
  const last = fixture.cases.find(c => c.id === 'last-page')
  const { adapter, epoch, authStore } = adapterFor('ownerA')
  try {
    await adapter.loadHistory({ adopt: false })
    assert.equal(adapter.historyState.value, 'ready'); assertions++
    assert.deepEqual(adapter.history.value, first.response.body.items); assertions++
    assert.deepEqual(adapter.historyNextCursor.value, first.response.body.nextCursor); assertions++
    await adapter.loadHistory({ ...last.request, append: true, adopt: false })
    assert.deepEqual(adapter.history.value, [...first.response.body.items, ...last.response.body.items]); assertions++
    assert.equal(adapter.historyNextCursor.value, null); assertions++
    epoch.value = 'ownerB'; authStore.authorizationGeneration++
    assert.deepEqual(adapter.history.value, []); assertions++
    await adapter.loadHistory()
    assert.equal(adapter.historyState.value, 'empty'); assertions++
    assert.deepEqual(adapter.history.value, []); assertions++
  } finally { adapter.dispose() }
  for (const identity of ['ownerCase', 'clientOther', 'clientCase']) {
    const { adapter } = adapterFor(identity)
    try { await adapter.loadHistory(); assert.equal(adapter.historyState.value, 'empty'); assertions++ }
    finally { adapter.dispose() }
  }
  const { adapter: brokenAdapter } = adapterFor('broken')
  try {
    await brokenAdapter.loadHistory()
    assert.equal(brokenAdapter.historyState.value, 'error'); assertions++
    assert.deepEqual(brokenAdapter.history.value, []); assertions++
    assert.ok(brokenAdapter.historyError.value); assertions++
  } finally { brokenAdapter.dispose() }
  // Raw wire checks also traverse production createApi/useHttp; request errors not fabricated.
  const wire = createApi(`${origin}/agent`)
  const wireAuthStore = { authorizationGeneration: 0, token: async () => tokens.ownerA }
  const malformed = fixture.cases.find(c => c.id === 'unpaired-cursor')
  await assert.rejects(wire.execute({ url: '/personal-workspace/executions', method: 'GET',
    params: malformed.request, authStore: wireAuthStore, rum: false }), error => error.status === 400 && error.code === 'BAD_REQUEST'); assertions++
  assert.ok(observations.some(x => x.status === 503)); assertions++
  assert.ok(observations.every(x => x.cache?.includes('private') && x.cache?.includes('no-store'))); assertions++
  globalThis.fetch = actualFetch
  const browser = process.env.CYF_HISTORY_BROWSER === '1' ? await (await import('./check-browser.mjs')).checkBrowser() : null
  console.log(JSON.stringify({ browser, status: 'PASS', layer: 'Vue-consumer_createApi_useHttp_fetch_JavaJWT_Controller_Service_MyBatis_MySQL',
    assertions, requests: observations.length, statuses: observations.map(x => x.status),
    fixtureSha256: createHash('sha256').update(fixtureBytes).digest('hex'), webCommit: fixture.source.webCommit,
    limitations: ['Synthetic signed identities, not production OAuth login', 'Vue state exercised in Node, not rendered browser UI', 'No deployment or formal frontend Flow'] }))
} finally { globalThis.fetch = actualFetch }
