#!/usr/bin/env node
'use strict'
// Documentation-only validation. No application build, runtime call or production mutation.
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const cp = require('node:child_process')
const dir = __dirname
const root = path.resolve(dir, '../..')
const yaml = require(require.resolve('js-yaml', { paths: [root, path.join(root, 'web')] }))
const read = name => fs.readFileSync(path.join(dir, name), 'utf8')
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const checks = []
function check(name, condition) {
  checks.push({ name, passed: !!condition })
  if (!condition) throw new Error(`Documentation validation failed: ${name}`)
}
const required = ['spec.md', 'design.md', 'tasks.md', 'acceptance.md', 'integration.yaml']
check('sdd_five_required_files_present', required.every(name => fs.statSync(path.join(dir, name)).isFile()))
const integration = yaml.load(read('integration.yaml'), { json: false })
check('yaml_parsed_and_feature_ready_D2', integration.feature_id === 'archive-agent-maintenance' && integration.status === 'ready' && integration.contract.revision === 'D2')
check('no_release_or_integration_pins_claimed', Object.values(integration.pinned_revisions).every(value => value === null)
  && integration.release.status === 'not_started' && integration.release.flow_run === null
  && integration.release.build_origin === null && integration.source_observation.production_verified === false)
check('no_application_test_success_claimed', ['api', 'web', 'client', 'integration'].every(name => integration.verification[name] === 'not_run')
  && integration.acceptance.status === 'not_run')
const suite = JSON.parse(read('acceptance-cases.json'))
const cases = suite.cases
check('D2_acceptance_and_handoff_consistent', suite.revision === 'D2' && integration.implementation_handoff.status === 'ready_for_M0_not_dispatched' && cases.filter(c => c.id.startsWith('D2-')).length === 14)
const design = read('design.md')
check('D2_removes_legacy_hall_projection_proposal', !design.includes('新增 `sourceType=archive-maintenance`') && design.includes('不扩展现有 ItemRef/OVERVIEW-v1'))
check('D2_no_parallel_command_polling', !design.includes('| GET `/internal/archive/v1/commands` |') && design.includes('不新增 `/internal/archive/v1/commands`'))
check('D2_shared_auth_transport_publication_boundaries', ['PUBLICATION_USE', 'legacy codex-ws-agent', 'Runtime v1', 'ArchiveAgentExecutionPort', 'dispatchKey', '直达', 'juyiting-multimedia-deliberation'].every(x => design.includes(x)))
check('handoff_present', fs.statSync(path.join(dir, 'handoff.md')).isFile())
check('all_acceptance_cases_unexecuted', cases.length > 0 && cases.every(c => c.status === 'not_run' && c.evidence === null))
check('unique_acceptance_case_ids', new Set(cases.map(c => c.id)).size === cases.length)
const stories = new Set(cases.flatMap(c => c.user_stories))
check('user_stories_U1_to_U9_covered', Array.from({ length: 9 }, (_, i) => `U${i + 1}`).every(x => stories.has(x)) && stories.size === 9)
const workPackages = new Set(cases.flatMap(c => c.work_packages))
check('implementation_packages_M1_to_M10_covered', Array.from({ length: 10 }, (_, i) => `M${i + 1}`).every(x => workPackages.has(x)) && workPackages.size === 10)
const acceptance = read('acceptance.md')
check('machine_cases_match_human_matrix', cases.every(c => acceptance.includes(`| ${c.id} |`) && acceptance.includes(c.expected))
  && acceptance.includes(`**${cases.length} 项**`))
const tasks = read('tasks.md')
const estimates = [...tasks.matchAll(/\| (\d+)–(\d+) \|$/gm)].map(m => [Number(m[1]), Number(m[2])])
check('estimate_derived_from_work_packages', estimates.length === 11 && estimates.reduce((s, x) => s + x[0], 0) === 27
  && estimates.reduce((s, x) => s + x[1], 0) === 46)
const audit = JSON.parse(read('source-audit.json'))
check('source_audit_is_observation_not_release', audit.remote_refs_fetched_for_this_audit === false && audit.deployed_version_verified === false)
for (const item of audit.files) {
  const repo = audit.repositories[item.repository].path
  const bytes = cp.execFileSync('git', ['-C', repo, 'show', `${item.revision}:${item.path}`], { maxBuffer: 16 * 1024 * 1024 })
  const blob = cp.execFileSync('git', ['-C', repo, 'rev-parse', `${item.revision}:${item.path}`], { encoding: 'utf8' }).trim()
  check(`frozen_source:${item.repository}:${item.path}`, hash(bytes) === item.sha256 && bytes.length === item.bytes && blob === item.git_blob)
}
let linkCount = 0
let jsonExampleCount = 0
for (const name of fs.readdirSync(dir).filter(n => n.endsWith('.md'))) {
  const text = read(name)
  check(`no_trailing_whitespace:${name}`, !/[\t ]+$/m.test(text))
  check(`balanced_code_fences:${name}`, (text.match(/^```/gm) || []).length % 2 === 0)
  for (const match of text.matchAll(/\[[^\]\n]+\]\(([^)]+)\)/g)) {
    const target = match[1].split('#')[0]
    if (!target || /^(?:https?:|mailto:)/.test(target)) continue
    linkCount++
    const destination = path.isAbsolute(target) ? target : path.resolve(dir, target)
    check(`local_link:${name}:${target}`, fs.existsSync(destination) || destination === path.join(dir, 'documentation-check.json'))
  }
  for (const match of text.matchAll(/```json\n([\s\S]*?)\n```/g)) {
    JSON.parse(match[1]); jsonExampleCount++
  }
}
check('json_examples_parse', jsonExampleCount > 0)
check('index_contains_scoped_design_entry', fs.readFileSync(path.join(root, 'specs/INDEX.md'), 'utf8').includes('## 典籍阁 Agent 任职与内容维护方案'))
cp.execFileSync('git', ['-C', root, 'diff', '--check', '--', 'specs/INDEX.md'], { encoding: 'utf8' })
check('index_diff_whitespace_check', true)
const documentDigests = Object.fromEntries(fs.readdirSync(dir).filter(n => n !== 'documentation-check.json')
  .sort().map(name => [name, hash(fs.readFileSync(path.join(dir, name)))]))
const result = {
  feature_id: 'archive-agent-maintenance',
  kind: 'documentation_static_self_check_only',
  command: `node ${path.join(dir, 'validate-design.cjs')}`,
  status: 'passed',
  checks_count: checks.length,
  source_files_verified: audit.files.length,
  acceptance_cases: cases.length,
  acceptance_status: 'not_run',
  local_links_checked: linkCount,
  json_examples_parsed: jsonExampleCount,
  application_tests_run: false,
  production_operations_run: false,
  release_evidence: false,
  checks,
  document_sha256: documentDigests
}
fs.writeFileSync(path.join(dir, 'documentation-check.json'), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify({ status: result.status, checks: checks.length, source_files: audit.files.length,
  acceptance_cases: cases.length, local_links: linkCount, application_tests_run: false }, null, 2))
