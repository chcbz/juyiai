#!/usr/bin/env node
/** Offline-only invariant check; it does not attach to CDP or launch anything. */
import { readFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
const here = dirname(fileURLToPath(import.meta.url))
const plan = JSON.parse(await readFile(join(here, 'acceptance-plan.json'), 'utf8'))
const harness = await readFile(join(here, 'run-browser-acceptance.mjs'), 'utf8')
const catalog = JSON.parse(await readFile(join(here, 'selector-catalog.json'), 'utf8'))
const expected = [...Array(22)].map((_, i) => `AC${String(i + 1).padStart(2, '0')}`).concat([...Array(12)].map((_, i) => `FD${String(i + 1).padStart(2, '0')}`))
const failures = []
const check = (ok, message) => { if (!ok) failures.push(message) }
check(plan.cases.length === 34, 'expected exactly 34 cases')
check(new Set(plan.cases.map(item => item.id)).size === 34, 'case IDs must be unique')
check(expected.every(id => plan.cases.some(item => item.id === id)), 'AC01–22 and FD01–12 must be complete')
check(plan.cases.every(item => item.status === 'NOT_RUN'), 'all planned cases must remain NOT_RUN')
check(plan.primaryJourney.includes('AC01') && plan.primaryJourney.includes('AC07') && plan.primaryJourney.includes('AC10') && plan.primaryJourney.includes('AC14') && plan.primaryJourney.includes('AC17'), 'primary journey checkpoints missing')
for (const phrase of ['no-reference', 'explicit target', 'automatic deliberation', 'naturalWidth', 'SHA-256', 'original', 'selected set', 'task completion']) check(plan.primaryProofRequirements?.some(item => item.toLowerCase().includes(phrase.toLowerCase())), `required primary proof absent: ${phrase}`)
for (const forbidden of ["from 'node:child_process'", 'spawn(', 'launchChrome(', 'puppeteer', 'playwright']) check(!harness.includes(forbidden), `forbidden browser-launch/dependency fragment: ${forbidden}`)
for (const required of ["args.has('--execute')", 'JYT_BROWSER_ACCEPTANCE_ALLOW_LIVE', 'JYT_BROWSER_CDP_URL', 'JYT_CDP_HARNESS_MODULE', 'PARTIAL_COMPLETED', 'NOT_RUN', 'BLOCKED_DEPLOYED_SOURCE_PIN_MISMATCH', 'BLOCKED_REQUIRED_UI_FLAGS_NOT_PROVEN', 'BLOCKED_UNRESOLVED_OPERATOR_ACTION_TEMPLATE', 'sanitizeEvidence', 'readyCheckpoint', 'BLOCKED_ACTION_']) check(harness.includes(required), `required execution boundary missing: ${required}`)
for (const credential of ['CYF_TEST_PASSWORD', 'CYF_TEST_USERNAME', 'Bearer ey', 'password=']) check(!harness.includes(credential), `credential-like literal present: ${credential}`)
check(catalog.status === 'SOURCE_DERIVED_NOT_LIVE_VERIFIED', 'selector catalog must not claim live verification')
check(JSON.stringify(catalog).includes('naturalWidth'), 'catalog must include decoded image selector evidence')
if (failures.length) { console.error(JSON.stringify({ status: 'FAIL', failures }, null, 2)); process.exitCode = 1 } else console.log(JSON.stringify({ status: 'PASS', checks: 15, cases: 34, browserAttached: false, browserLaunched: false }, null, 2))
