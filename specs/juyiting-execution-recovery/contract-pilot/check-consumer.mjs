// Cheap isolated consumer diagnostic. Not a Java/HTTP/DB or Flow test.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { execFileSync } from 'node:child_process'

const webRoot = process.argv[2]
assert.ok(webRoot, 'usage: node check-consumer.mjs <isolated-pinned-web-worktree>')
const fixture = JSON.parse(readFileSync(new URL('./execution-history.json', import.meta.url)))
const git = (...args) => execFileSync('git', ['-C', resolve(webRoot), ...args], {
  encoding: 'utf8', env: { ...process.env, GIT_OPTIONAL_LOCKS: '0', GIT_NO_LAZY_FETCH: '1' }
}).trim()
assert.equal(git('rev-parse', 'HEAD'), fixture.source.webCommit, 'wrong source commit')
assert.equal(git('status', '--porcelain', '--untracked-files=normal'), '', 'use a clean isolated source worktree')
const moduleUrl = pathToFileURL(join(resolve(webRoot), 'src/composables/usePersonalWorkspaceExecution.js'))
const originalFetch = globalThis.fetch
// An accidental real request is a test failure, never a silent fixture success.
globalThis.fetch = async () => { throw new Error('network forbidden in fixture diagnostic') }
let assertions = 0
try {
  const { usePersonalWorkspaceExecution } = await import(moduleUrl.href)
  for (const example of fixture.cases) {
    const calls = []
    const adapter = usePersonalWorkspaceExecution({
      identityEpoch: 'contract-owner', identityScope: 'contract-owner',
      storage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
      api: { execute: async options => {
        calls.push(options)
        if (example.response.status !== 200) throw new Error(example.response.body.code)
        return { data: structuredClone(example.response.body) }
      } }
    })
    try {
      await adapter.loadHistory({ adopt: false })
      assert.equal(adapter.historyState.value, example.consumerState)
      assert.equal(calls.length, 1)
      assert.equal(calls[0].method, 'GET')
      assert.equal(calls[0].url, '/personal-workspace/executions')
      if (example.response.status === 200) assert.deepEqual(adapter.history.value, example.response.body.items)
      else assert.equal(adapter.history.value.length, 0)
      assertions += 5
    } finally { adapter.dispose() }
  }
  // One real consumer instance follows the cursor from the shared first/last pages.
  const pages = ['first-page', 'last-page'].map(id => fixture.cases.find(c => c.id === id))
  const calls = []
  const adapter = usePersonalWorkspaceExecution({
    identityEpoch: 'contract-owner', identityScope: 'contract-owner',
    storage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    api: { execute: async options => {
      calls.push(options)
      assert.ok(calls.length <= 2, 'unexpected extra request')
      return { data: structuredClone(pages[calls.length - 1].response.body) }
    } }
  })
  try {
    await adapter.loadHistory({ adopt: false })
    await adapter.loadHistory({ ...pages[1].request, append: true, adopt: false })
    assert.equal(calls.length, 2)
    assert.equal(calls[1].params.beforeCreatedAt, pages[1].request.beforeCreatedAt)
    assert.equal(calls[1].params.beforeExecutionId, pages[1].request.beforeExecutionId)
    assert.deepEqual(adapter.history.value.map(x => x.executionId), pages.flatMap(page => page.response.body.items.map(x => x.executionId)))
    assert.equal(adapter.historyNextCursor.value, null)
    assertions += 5
  } finally { adapter.dispose() }
  console.log(JSON.stringify({ status: 'PASS', layer: 'real_frontend_consumer_with_injected_api',
    assertions, webCommit: fixture.source.webCommit, javaHttpDatabase: 'NOT_RUN', formalFlow: 'NOT_RUN' }))
} finally { globalThis.fetch = originalFetch }
