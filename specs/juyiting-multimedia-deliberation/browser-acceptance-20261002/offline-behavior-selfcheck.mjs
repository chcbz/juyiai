#!/usr/bin/env node
/** Dummy-CDP behavior check only: no browser endpoint, live action, or process launch. */
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { runActions, safeUrl, sanitizeEvidence } from './run-browser-acceptance.mjs'

const signed = 'https://media.example.test/object.png?Signature=secret-value&X-Amz-Credential=credential-value'
assert.equal(safeUrl(signed), 'https://media.example.test/object.png')
const sanitized = sanitizeEvidence({ url: signed, nested: { src: signed, href: signed }, text: `download ${signed}` })
assert.equal(sanitized.url, 'https://media.example.test/object.png')
assert.equal(sanitized.nested.src, 'https://media.example.test/object.png')
assert.equal(sanitized.nested.href, 'https://media.example.test/object.png')
assert.ok(!JSON.stringify(sanitized).includes('secret-value'))
assert.ok(!JSON.stringify(sanitized).includes('?Signature='))
const root = await mkdtemp(join(tmpdir(), 'jyt-browser-acceptance-selfcheck-'))
const evaluated = []; let cdpSends = 0
try {
  await assert.rejects(() => runActions({
    actions: [
      { name: 'missing-assignment', type: 'clickSelector', selector: '#missing' },
      { name: 'must-not-run-fill', type: 'fill', selector: '#would-mutate', value: '画一只鸟' }
    ],
    cdp: { send: async () => { cdpSends++; return {} }, __capture: async () => Buffer.from('unused') },
    evaluate: async expression => { evaluated.push(expression); return { ok: false, reason: 'selector-not-visible', url: signed } },
    evidenceRoot: root,
    downloads: join(root, 'downloads'),
    baseUrl: 'https://media.example.test'
  }), /BLOCKED_ACTION_MISSING_ASSIGNMENT_SELECTOR_NOT_VISIBLE/)
  assert.equal(evaluated.length, 1, 'a failed selector must block every later action')
  assert.equal(cdpSends, 0, 'no later CDP mutation may be sent after selector failure')
  const blockedEvidence = await readFile(join(root, 'actions', '01-missing-assignment.json'), 'utf8')
  assert.ok(!blockedEvidence.includes('secret-value'))
  assert.ok(!blockedEvidence.includes('?Signature='))
  console.log(JSON.stringify({ status: 'PASS', dummyCdp: true, browserAttached: false, browserLaunched: false, selectorFailureStoppedLaterMutation: true, signedUrlRedacted: true }, null, 2))
} finally { await rm(root, { recursive: true, force: true }) }
