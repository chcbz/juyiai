#!/usr/bin/env node
'use strict';

/* Narrow, versioned Alibaba Cloud Flow control plane.
 * Every invocation performs at most one write. Candidate/config hashes and
 * start context are frozen, credentials and raw service errors are never output.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const SDK = require('/root/.codex/skills/aliyun-pipeline/node_modules/@alicloud/devops20210625');

const CLI_VERSION = '1.1.0';
const ENDPOINT = 'devops.cn-hangzhou.aliyuncs.com';
const REGION = 'cn-hangzhou';
const SHA256 = /^[a-f0-9]{64}$/;
const FULL_SHA = /^[a-f0-9]{40}$/;
const IDENTIFIER = /^[A-Za-z0-9._:-]{1,160}$/;
const RUN_ID = /^[1-9][0-9]*$/;
const WRITE_COMMANDS = new Set(['create', 'update', 'start']);
const COMMANDS = new Set(['config', 'list', 'create', 'update', 'start', 'status']);
const OPTION_NAMES = {
  config: new Set(['org', 'pipeline', 'allowlist', 'credentials-file']),
  list: new Set(['org', 'pipeline', 'allowlist', 'credentials-file']),
  status: new Set(['org', 'pipeline', 'run', 'allowlist', 'credentials-file']),
  create: new Set(['org', 'name', 'candidate', 'candidate-sha256', 'allowlist', 'credentials-file']),
  update: new Set(['org', 'pipeline', 'name', 'candidate', 'candidate-sha256', 'allowlist', 'credentials-file']),
  start: new Set(['org', 'pipeline', 'context', 'context-sha256', 'allowlist', 'credentials-file']),
};

class ControlError extends Error {
  constructor(code) { super(code); this.code = code; }
}
function fail(code) { throw new ControlError(code); }
function sha256(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function canonicalFlowText(text) { return text.replace(/\r\n/g, '\n').replace(/\n*$/, '\n'); }
function now() { return new Date().toISOString(); }
function requireValue(value, code) { if (!value) fail(code); return value; }
function requireIdentifier(value, code) {
  if (!IDENTIFIER.test(String(value || ''))) fail(code);
  return String(value);
}
function requireSha256(value, code) {
  if (!SHA256.test(String(value || ''))) fail(code);
  return String(value);
}
function isRecord(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }

function parseArgs(argv) {
  if (argv.length === 1 && argv[0] === '--version') return { command: 'version', options: {} };
  const command = argv.shift();
  if (!COMMANDS.has(command)) fail('UNSUPPORTED_COMMAND');
  const options = {};
  while (argv.length) {
    const token = argv.shift();
    if (!token.startsWith('--')) fail('INVALID_ARGUMENT');
    const key = token.slice(2);
    if (!key || !OPTION_NAMES[command].has(key) || Object.prototype.hasOwnProperty.call(options, key)) fail('INVALID_ARGUMENT');
    const value = argv.shift();
    if (!value || value.startsWith('--')) fail('MISSING_ARGUMENT_VALUE');
    options[key] = value;
  }
  return { command, options };
}

function readJsonFile(file, code) {
  try {
    const parsed = JSON.parse(fs.readFileSync(path.resolve(file), 'utf8'));
    if (!isRecord(parsed)) fail(code);
    return parsed;
  } catch (error) {
    if (error instanceof ControlError) throw error;
    fail(code);
  }
}

function credentials(options) {
  const source = options['credentials-file'] ? readJsonFile(options['credentials-file'], 'INVALID_CREDENTIALS_FILE') : process.env;
  const accessKeyId = source.ALIBABA_CLOUD_ACCESS_KEY_ID || source.accessKeyId || source.access_key_id;
  const accessKeySecret = source.ALIBABA_CLOUD_ACCESS_KEY_SECRET || source.accessKeySecret || source.access_key_secret;
  const securityToken = source.ALIBABA_CLOUD_SECURITY_TOKEN || source.securityToken || source.security_token;
  if (typeof accessKeyId !== 'string' || !accessKeyId.trim() || typeof accessKeySecret !== 'string' || !accessKeySecret.trim() ||
      (securityToken !== undefined && (typeof securityToken !== 'string' || !securityToken.trim()))) fail('CREDENTIALS_UNAVAILABLE');
  const config = { accessKeyId, accessKeySecret, endpoint: ENDPOINT, regionId: REGION, connectTimeout: 10000, readTimeout: 25000 };
  if (securityToken) config.securityToken = securityToken;
  return new SDK.default(config);
}

function loadAllowlist(options, command) {
  if (!options.allowlist) {
    if (WRITE_COMMANDS.has(command)) fail('WRITE_ALLOWLIST_REQUIRED');
    return null;
  }
  const value = readJsonFile(options.allowlist, 'INVALID_ALLOWLIST');
  const organizations = Array.isArray(value.organizations) ? value.organizations : [];
  const pipelines = Array.isArray(value.pipelines) ? value.pipelines : [];
  const creates = Array.isArray(value.creates) ? value.creates : [];
  if (!organizations.every(item => typeof item === 'string') ||
      !pipelines.every(item => isRecord(item) && typeof item.org === 'string' && typeof item.pipeline === 'string') ||
      !creates.every(item => isRecord(item) && typeof item.org === 'string' && typeof item.name === 'string' && SHA256.test(item.candidateSha256 || ''))) {
    fail('INVALID_ALLOWLIST');
  }
  return { organizations, pipelines, creates };
}

function checkedScope(options, command, requiresPipeline, createCandidate) {
  const org = requireIdentifier(options.org, 'INVALID_ORG');
  const pipeline = requiresPipeline ? requireIdentifier(options.pipeline, 'INVALID_PIPELINE') : null;
  const allowlist = loadAllowlist(options, command);
  if (allowlist && !allowlist.organizations.includes(org)) fail('ORG_NOT_ALLOWLISTED');
  if (allowlist && pipeline !== null && !allowlist.pipelines.some(item => item.org === org && item.pipeline === pipeline)) fail('PIPELINE_NOT_ALLOWLISTED');
  if (command === 'create' && (!allowlist || !allowlist.creates.some(item => item.org === org && item.name === createCandidate.name && item.candidateSha256 === createCandidate.sha256))) {
    fail('CREATE_NOT_ALLOWLISTED');
  }
  return { org, pipeline };
}

function candidate(options) {
  const expected = requireSha256(options['candidate-sha256'], 'INVALID_CANDIDATE_SHA256');
  let content;
  try { content = fs.readFileSync(path.resolve(requireValue(options.candidate, 'MISSING_CANDIDATE_FILE'))); }
  catch (_) { fail('CANDIDATE_UNREADABLE'); }
  if (sha256(content) !== expected) fail('CANDIDATE_SHA256_MISMATCH');
  const text = content.toString('utf8');
  return { content: text, sha256: expected, canonicalSha256: sha256(Buffer.from(canonicalFlowText(text), 'utf8')) };
}

function pipelineConfig(pipeline) {
  const config = pipeline && pipeline.pipelineConfig;
  if (!isRecord(config) || typeof config.flow !== 'string') fail('PIPELINE_CONFIGURATION_UNAVAILABLE');
  return config;
}
function configSummary(pipeline) {
  const config = pipelineConfig(pipeline);
  const sources = Array.isArray(config.sources) ? config.sources : [];
  return {
    name: typeof pipeline.name === 'string' ? pipeline.name : null,
    configSha256: sha256(Buffer.from(config.flow, 'utf8')),
    canonicalConfigSha256: sha256(Buffer.from(canonicalFlowText(config.flow), 'utf8')),
    configBytes: Buffer.byteLength(config.flow, 'utf8'),
    sourceCount: sources.length,
    sourceKinds: sources.map(source => isRecord(source) && typeof source.type === 'string' ? source.type : 'unknown'),
  };
}
function sourceSummary(source) {
  let commits = [];
  try {
    const parsed = JSON.parse(source && source.data && source.data.commint);
    if (Array.isArray(parsed)) commits = parsed.map(item => item && item.commitId).filter(item => FULL_SHA.test(item || ''));
  } catch (_) { /* unknown source commit stays empty */ }
  return {
    repo: source && source.data && source.data.repo || null,
    branch: source && source.data && source.data.branch || null,
    headCommit: commits.length ? commits[0] : null,
    commits,
  };
}
function runSummary(run) {
  return {
    id: run.pipelineRunId === undefined ? null : String(run.pipelineRunId),
    status: typeof run.status === 'string' ? run.status : 'UNKNOWN',
    startTime: run.startTime === undefined ? null : run.startTime,
    sources: Array.isArray(run.sources) ? run.sources.map(sourceSummary) : [],
  };
}

function definitiveApiCode(error) {
  const status = Number(error && (error.statusCode || error.status));
  const serviceCode = error && typeof error.code === 'string' ? error.code : (error && typeof error.name === 'string' ? error.name : '');
  const message = error && typeof error.message === 'string' ? error.message : '';
  if (status === 401 || status === 403 || /Forbidden|Unauthorized|NoPermission/i.test(serviceCode + ' ' + message)) return 'FLOW_API_FORBIDDEN';
  if (status === 429 || /Throttl|RateLimit/i.test(serviceCode + ' ' + message)) return null;
  if (status === 404 || /NotFound/i.test(serviceCode)) return 'FLOW_API_NOT_FOUND';
  if (serviceCode === '1209300' || /yaml/i.test(message)) return 'FLOW_API_INVALID_YAML';
  if (status >= 400 && status < 500 && status !== 408) return 'FLOW_API_REJECTED';
  return null;
}
async function readBody(request) {
  try {
    const response = await request;
    const result = response && response.body;
    if (!result || result.success === false || result.errorCode) fail('FLOW_API_REJECTED');
    return result;
  } catch (error) {
    if (error instanceof ControlError) throw error;
    fail(definitiveApiCode(error) || 'FLOW_API_UNAVAILABLE');
  }
}
async function writeOnce(factory) {
  try {
    const response = await factory();
    const result = response && response.body;
    if (!result || result.success === false || result.errorCode) return { state: 'DEFINITE_FAILURE', code: 'FLOW_API_REJECTED' };
    return { state: 'RESPONDED', body: result };
  } catch (error) {
    const code = definitiveApiCode(error);
    return code ? { state: 'DEFINITE_FAILURE', code } : { state: 'AMBIGUOUS' };
  }
}

function readFailureCode(error) {
  return error instanceof ControlError ? error.code : (definitiveApiCode(error) || 'FLOW_API_UNAVAILABLE');
}
async function reconcileRead(factory) {
  try { return { ok: true, value: await factory() }; }
  catch (error) { return { ok: false, code: readFailureCode(error) }; }
}
async function getPipeline(client, org, pipeline) {
  const result = await readBody(client.getPipeline(org, pipeline));
  if (!isRecord(result.pipeline)) fail('PIPELINE_NOT_FOUND');
  return result.pipeline;
}
async function getRun(client, org, pipeline, run) {
  const result = await readBody(client.getPipelineRun(org, pipeline, run));
  if (!isRecord(result.pipelineRun)) fail('RUN_NOT_FOUND');
  return result.pipelineRun;
}
async function listRuns(client, org, pipeline, maxResults) {
  const result = await readBody(client.listPipelineRuns(org, pipeline, new SDK.ListPipelineRunsRequest({ maxResults })));
  if (!Array.isArray(result.pipelineRuns)) fail('RUN_LIST_UNAVAILABLE');
  return { runs: result.pipelineRuns, nextToken: result.nextToken || null };
}
async function listAllPipelines(client, org) {
  let nextToken = null;
  const pipelines = [];
  for (let page = 0; page < 20; page += 1) {
    const result = await readBody(client.listPipelines(org, new SDK.ListPipelinesRequest({ maxResults: 100, nextToken: nextToken || undefined })));
    if (!Array.isArray(result.pipelines)) fail('PIPELINE_LIST_UNAVAILABLE');
    pipelines.push(...result.pipelines);
    nextToken = result.nextToken || null;
    if (!nextToken) return pipelines;
  }
  fail('PIPELINE_LIST_REQUIRES_RECONCILIATION');
}

function frozenStartContext(options, org, pipeline) {
  const expected = requireSha256(options['context-sha256'], 'INVALID_CONTEXT_SHA256');
  let bytes;
  try { bytes = fs.readFileSync(path.resolve(requireValue(options.context, 'MISSING_CONTEXT_FILE'))); }
  catch (_) { fail('CONTEXT_UNREADABLE'); }
  if (sha256(bytes) !== expected) fail('CONTEXT_SHA256_MISMATCH');
  let context;
  try { context = JSON.parse(bytes.toString('utf8')); } catch (_) { fail('INVALID_CONTEXT'); }
  if (!isRecord(context) || context.schemaVersion !== 1 || context.kind !== 'cyf.flow.start-context.v1' || context.org !== org ||
      context.pipeline !== pipeline || !IDENTIFIER.test(context.pipelineName || '') || !SHA256.test(context.canonicalConfigSha256 || '') ||
      !Array.isArray(context.existingRunIds) || !context.existingRunIds.every(id => RUN_ID.test(String(id))) ||
      typeof context.requestStartedAt !== 'string' || Number.isNaN(Date.parse(context.requestStartedAt)) || !isRecord(context.params) ||
      !Array.isArray(context.expectedSources) ||
      !context.expectedSources.every(item => isRecord(item) && typeof item.repo === 'string' && typeof item.branch === 'string' && FULL_SHA.test(item.commit || ''))) {
    fail('INVALID_CONTEXT');
  }
  return { context, sha256: expected };
}
function sourcesMatch(run, expected) {
  const actual = runSummary(run).sources;
  if (expected.length === 0) return actual.length === 0;
  return expected.every(wanted => actual.some(item => item.repo === wanted.repo && item.branch === wanted.branch && item.headCommit === wanted.commit));
}

async function commandConfig(client, options) {
  const { org, pipeline } = checkedScope(options, 'config', true, null);
  return { operation: 'config', org, pipeline, configuration: configSummary(await getPipeline(client, org, pipeline)) };
}
async function commandList(client, options) {
  const { org, pipeline } = checkedScope(options, 'list', true, null);
  const listed = await listRuns(client, org, pipeline, 100);
  return { operation: 'list', org, pipeline, runs: listed.runs.map(runSummary), nextToken: listed.nextToken };
}
async function commandStatus(client, options) {
  const { org, pipeline } = checkedScope(options, 'status', true, null);
  const run = requireIdentifier(options.run, 'INVALID_RUN');
  return { operation: 'status', org, pipeline, run: runSummary(await getRun(client, org, pipeline, run)) };
}

async function commandCreate(client, options) {
  const name = requireIdentifier(options.name, 'INVALID_PIPELINE_NAME');
  const reviewed = candidate(options);
  const { org } = checkedScope(options, 'create', false, { name, sha256: reviewed.sha256 });
  const before = await listAllPipelines(client, org);
  if (before.some(item => item.pipelineName === name)) fail('CREATE_NAME_EXISTS');
  const existingIds = new Set(before.map(item => String(item.pipelineId)));
  const requestStartedAt = now();
  const write = await writeOnce(() => client.createPipeline(org, new SDK.CreatePipelineRequest({ name, content: reviewed.content })));
  if (write.state === 'DEFINITE_FAILURE') fail(write.code);
  const intent = { operation: 'create', org, candidateSha256: reviewed.sha256, requestStartedAt };
  const returnedId = write.state === 'RESPONDED' && write.body.pipelinId !== undefined ? String(write.body.pipelinId) : null;
  if (returnedId && RUN_ID.test(returnedId)) {
    const checked = await reconcileRead(async () => configSummary(await getPipeline(client, org, returnedId)));
    if (!checked.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: false, returnedPipelineId: returnedId, reconciliationError: checked.code };
    if (checked.value.name === name && checked.value.canonicalConfigSha256 === reviewed.canonicalSha256) {
      return { ...intent, state: 'APPLIED', pipeline: returnedId, ambiguousResponse: false, readback: checked.value };
    }
    return { ...intent, state: 'UNKNOWN', ambiguousResponse: false, returnedPipelineId: returnedId, readback: checked.value };
  }
  const after = await reconcileRead(() => listAllPipelines(client, org));
  if (!after.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, reconciliationError: after.code };
  const candidates = after.value.filter(item => item.pipelineName === name && !existingIds.has(String(item.pipelineId))).map(item => String(item.pipelineId));
  const exact = [];
  for (const pipeline of candidates) {
    const checked = await reconcileRead(async () => configSummary(await getPipeline(client, org, pipeline)));
    if (!checked.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, candidatePipelineIds: candidates, reconciliationError: checked.code };
    if (checked.value.name === name && checked.value.canonicalConfigSha256 === reviewed.canonicalSha256) exact.push({ pipeline, readback: checked.value });
  }
  if (exact.length === 1) return { ...intent, state: 'APPLIED', pipeline: exact[0].pipeline, ambiguousResponse: true, readback: exact[0].readback };
  return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, candidatePipelineIds: candidates };
}

async function commandUpdate(client, options) {
  const name = requireIdentifier(options.name, 'INVALID_PIPELINE_NAME');
  const reviewed = candidate(options);
  const { org, pipeline } = checkedScope(options, 'update', true, null);
  const before = configSummary(await getPipeline(client, org, pipeline));
  const requestStartedAt = now();
  const write = await writeOnce(() => client.updatePipeline(org, new SDK.UpdatePipelineRequest({ pipelineId: pipeline, name, content: reviewed.content })));
  if (write.state === 'DEFINITE_FAILURE') fail(write.code);
  const intent = { operation: 'update', org, pipeline, candidateSha256: reviewed.sha256, requestStartedAt, before };
  const checked = await reconcileRead(async () => configSummary(await getPipeline(client, org, pipeline)));
  if (!checked.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: write.state === 'AMBIGUOUS', reconciliationError: checked.code };
  if (checked.value.name === name && checked.value.canonicalConfigSha256 === reviewed.canonicalSha256) {
    return { ...intent, state: 'APPLIED', ambiguousResponse: write.state === 'AMBIGUOUS', readback: checked.value };
  }
  return { ...intent, state: 'UNKNOWN', ambiguousResponse: write.state === 'AMBIGUOUS', readback: checked.value };
}

async function commandStart(client, options) {
  const { org, pipeline } = checkedScope(options, 'start', true, null);
  const frozen = frozenStartContext(options, org, pipeline);
  const config = configSummary(await getPipeline(client, org, pipeline));
  if (config.name !== frozen.context.pipelineName || config.canonicalConfigSha256 !== frozen.context.canonicalConfigSha256) fail('START_CONTEXT_STALE');
  const before = await listRuns(client, org, pipeline, 100);
  if (before.nextToken !== null) fail('RUN_HISTORY_REQUIRES_RECONCILIATION');
  const existingRunIds = before.runs.map(run => String(run.pipelineRunId)).sort();
  const frozenRunIds = frozen.context.existingRunIds.map(String).sort();
  if (JSON.stringify(existingRunIds) !== JSON.stringify(frozenRunIds)) fail('START_CONTEXT_STALE');
  const requestStartedAt = now();
  const write = await writeOnce(() => client.startPipelineRun(org, pipeline, new SDK.StartPipelineRunRequest({ params: JSON.stringify(frozen.context.params) })));
  if (write.state === 'DEFINITE_FAILURE') fail(write.code);
  const intent = { operation: 'start', org, pipeline, contextSha256: frozen.sha256, requestStartedAt };
  const returnedId = write.state === 'RESPONDED' && write.body.pipelineRunId !== undefined ? String(write.body.pipelineRunId) : null;
  if (returnedId && RUN_ID.test(returnedId)) {
    const checked = await reconcileRead(() => getRun(client, org, pipeline, returnedId));
    if (!checked.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: false, returnedRunId: returnedId, reconciliationError: checked.code };
    if (!sourcesMatch(checked.value, frozen.context.expectedSources)) return { ...intent, state: 'UNKNOWN', ambiguousResponse: false, returnedRunId: returnedId, run: runSummary(checked.value) };
    return { ...intent, state: 'APPLIED', ambiguousResponse: false, run: runSummary(checked.value) };
  }
  // A transport-ambiguous start cannot be uniquely attributed from source/time
  // alone: another operator may have launched the same commit concurrently.
  // Reconciliation is evidence only and always remains UNKNOWN.
  const after = await reconcileRead(() => listRuns(client, org, pipeline, 100));
  if (!after.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, reconciliationError: after.code };
  const startedAtMs = Date.parse(requestStartedAt);
  const candidateRunIds = [];
  for (const item of after.value.runs) {
    const id = String(item.pipelineRunId);
    if (existingRunIds.includes(id) || Number(item.startTime) < startedAtMs) continue;
    const checked = await reconcileRead(() => getRun(client, org, pipeline, id));
    if (!checked.ok) return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, candidateRunIds, reconciliationError: checked.code };
    if (sourcesMatch(checked.value, frozen.context.expectedSources)) candidateRunIds.push(id);
  }
  return { ...intent, state: 'UNKNOWN', ambiguousResponse: true, candidateRunIds };
}

async function main() {
  const parsed = parseArgs(process.argv.slice(2));
  if (parsed.command === 'version') { process.stdout.write(JSON.stringify({ version: CLI_VERSION }) + '\n'); return; }
  const client = credentials(parsed.options);
  const handlers = { config: commandConfig, list: commandList, create: commandCreate, update: commandUpdate, start: commandStart, status: commandStatus };
  const result = await handlers[parsed.command](client, parsed.options);
  process.stdout.write(JSON.stringify({ version: CLI_VERSION, at: now(), ...result }) + '\n');
  if (result.state === 'UNKNOWN') process.exitCode = 3;
}

module.exports = { ControlError, canonicalFlowText, checkedScope, configSummary, frozenStartContext, commandCreate, commandUpdate, commandStart };
if (require.main === module) main().catch(error => {
  const code = error instanceof ControlError ? error.code : 'CONTROL_FAILURE';
  process.stderr.write(JSON.stringify({ version: CLI_VERSION, error: code, action: 'reconcile read-only; do not repeat a write' }) + '\n');
  process.exitCode = 2;
});
