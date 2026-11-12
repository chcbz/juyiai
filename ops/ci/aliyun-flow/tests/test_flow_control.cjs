'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const control = require('../flow-control.cjs');

const ORG = '5fb7d76ee6f9d07f148529c7';
const PIPELINE = '5263690';
const COMMIT = 'b8b30fbe1f95a34ff3d6eb99b8c9881b23894847';
const REPO = 'https://github.com/chcbz/juyiai-api.git';
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const response = body => Promise.resolve({ body: { success: true, ...body } });

function files({ flow = 'name: demo\n', create = false } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cyf-flow-control-test-'));
  const candidate = path.join(dir, 'candidate.yaml');
  fs.writeFileSync(candidate, flow);
  const candidateSha256 = hash(Buffer.from(flow));
  const allowlist = path.join(dir, 'allowlist.json');
  fs.writeFileSync(allowlist, JSON.stringify({
    organizations: [ORG],
    pipelines: [{ org: ORG, pipeline: PIPELINE }],
    creates: create ? [{ org: ORG, name: 'demo', candidateSha256 }] : [],
  }));
  return { dir, candidate, candidateSha256, allowlist };
}

function pipeline(flow, name = 'demo') {
  return { name, pipelineConfig: { flow, sources: [{ type: 'git' }] } };
}
function run(id = 1) {
  return {
    pipelineRunId: id,
    status: 'RUNNING',
    startTime: 1,
    sources: [{ data: { repo: REPO, branch: 'develop', commint: JSON.stringify([{ commitId: COMMIT }]) } }],
  };
}
function contextFile(dir, flow, existingRunIds = []) {
  const value = {
    schemaVersion: 1,
    kind: 'cyf.flow.start-context.v1',
    org: ORG,
    pipeline: PIPELINE,
    pipelineName: 'demo',
    canonicalConfigSha256: hash(Buffer.from(control.canonicalFlowText(flow))),
    existingRunIds,
    requestStartedAt: new Date().toISOString(),
    expectedSources: [{ repo: REPO, branch: 'develop', commit: COMMIT }],
    params: { runningBranchs: { [REPO]: 'develop' }, envs: {} },
  };
  const file = path.join(dir, 'context.json');
  const bytes = Buffer.from(JSON.stringify(value));
  fs.writeFileSync(file, bytes);
  return { file, sha256: hash(bytes) };
}

test('write operations require an explicit allowlist', () => {
  assert.throws(() => control.checkedScope({ org: ORG, pipeline: PIPELINE }, 'start', true, null), error => error.code === 'WRITE_ALLOWLIST_REQUIRED');
});

test('start refuses config drift before sending a write', async () => {
  const f = files();
  const frozen = contextFile(f.dir, 'name: expected\n');
  let writes = 0;
  const client = {
    getPipeline: () => response({ pipeline: pipeline('name: changed\n') }),
    startPipelineRun: () => { writes += 1; return response({ pipelineRunId: 1 }); },
  };
  await assert.rejects(control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 }), error => error.code === 'START_CONTEXT_STALE');
  assert.equal(writes, 0);
});

test('start writes once, requires a run id, and reads the run back', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  let writes = 0, runReads = 0;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => response({ pipelineRuns: [], nextToken: null }),
    startPipelineRun: () => { writes += 1; return response({ pipelineRunId: 1 }); },
    getPipelineRun: () => { runReads += 1; return response({ pipelineRun: run(1) }); },
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'APPLIED');
  assert.equal(result.run.id, '1');
  assert.equal(writes, 1);
  assert.equal(runReads, 1);
});


test('manual pipeline start accepts an explicitly source-free run only when readback is source-free', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  const value = JSON.parse(fs.readFileSync(frozen.file));
  value.expectedSources = [];
  fs.writeFileSync(frozen.file, JSON.stringify(value));
  frozen.sha256 = hash(fs.readFileSync(frozen.file));
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => response({ pipelineRuns: [], nextToken: null }),
    startPipelineRun: () => response({ pipelineRunId: 1 }),
    getPipelineRun: () => response({ pipelineRun: { pipelineRunId: 1, status: 'RUNNING', startTime: 1, sources: [] } }),
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'APPLIED');
});

test('start rejects an expected ancestor when the actual source head moved', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  const movedHead = 'a9d3e7417447a9f5f59a12523e582a8e8f1818f6';
  const moved = run(2);
  moved.sources[0].data.commint = JSON.stringify([{ commitId: movedHead }, { commitId: COMMIT }]);
  let writes = 0;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => response({ pipelineRuns: [], nextToken: null }),
    startPipelineRun: () => { writes += 1; return response({ pipelineRunId: 2 }); },
    getPipelineRun: () => response({ pipelineRun: moved }),
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.equal(result.returnedRunId, '2');
  assert.equal(result.run.sources[0].headCommit, movedHead);
  assert.equal(writes, 1);
});

test('ambiguous create reconciles one exact new pipeline without another write', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow, create: true });
  let lists = 0, writes = 0;
  const client = {
    listPipelines: () => response({ pipelines: lists++ === 0 ? [] : [{ pipelineId: 9, pipelineName: 'demo' }], nextToken: null }),
    createPipeline: () => { writes += 1; const error = new Error('socket timeout'); error.code = 'ETIMEDOUT'; throw error; },
    getPipeline: () => response({ pipeline: pipeline(flow) }),
  };
  const result = await control.commandCreate(client, { org: ORG, name: 'demo', allowlist: f.allowlist, candidate: f.candidate, 'candidate-sha256': f.candidateSha256 });
  assert.equal(result.state, 'APPLIED');
  assert.equal(result.pipeline, '9');
  assert.equal(result.ambiguousResponse, true);
  assert.equal(writes, 1);
});

test('ambiguous update reconciles exact readback without another write', async () => {
  const flow = 'name: demo\nstages: {}\n';
  const f = files({ flow });
  let reads = 0, writes = 0;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(reads++ === 0 ? 'name: old\n' : flow) }),
    updatePipeline: () => { writes += 1; const error = new Error('socket timeout'); error.code = 'ETIMEDOUT'; throw error; },
  };
  const result = await control.commandUpdate(client, { org: ORG, pipeline: PIPELINE, name: 'demo', allowlist: f.allowlist, candidate: f.candidate, 'candidate-sha256': f.candidateSha256 });
  assert.equal(result.state, 'APPLIED');
  assert.equal(result.ambiguousResponse, true);
  assert.equal(writes, 1);
});

test('definitive create rejection stops after one write', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow, create: true });
  let writes = 0;
  const client = {
    listPipelines: () => response({ pipelines: [], nextToken: null }),
    createPipeline: () => { writes += 1; const error = new Error('yaml invalid'); error.code = '1209300'; error.statusCode = 400; throw error; },
  };
  await assert.rejects(control.commandCreate(client, { org: ORG, name: 'demo', allowlist: f.allowlist, candidate: f.candidate, 'candidate-sha256': f.candidateSha256 }), error => error.code === 'FLOW_API_INVALID_YAML');
  assert.equal(writes, 1);
});

test('ambiguous start with one concurrent same-source run remains UNKNOWN', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  let lists = 0, writes = 0;
  const concurrent = run(7);
  concurrent.startTime = Date.now() + 1000;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => response({ pipelineRuns: lists++ === 0 ? [] : [concurrent], nextToken: null }),
    startPipelineRun: () => { writes += 1; const error = new Error('socket timeout'); error.code = 'ETIMEDOUT'; throw error; },
    getPipelineRun: () => response({ pipelineRun: concurrent }),
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.deepEqual(result.candidateRunIds, ['7']);
  assert.equal(writes, 1);
});

test('ambiguous start with multiple same-source runs remains UNKNOWN', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  let lists = 0;
  const runs = [run(8), run(9)];
  for (const item of runs) item.startTime = Date.now() + 1000;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => response({ pipelineRuns: lists++ === 0 ? [] : runs, nextToken: null }),
    startPipelineRun: () => { const error = new Error('socket timeout'); error.code = 'ETIMEDOUT'; throw error; },
    getPipelineRun: (_org, _pipeline, id) => response({ pipelineRun: runs.find(item => String(item.pipelineRunId) === String(id)) }),
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.deepEqual(result.candidateRunIds.sort(), ['8', '9']);
});

test('ambiguous create plus reconciliation read failure returns structured UNKNOWN', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow, create: true });
  let lists = 0, writes = 0;
  const client = {
    listPipelines: () => {
      if (lists++ === 0) return response({ pipelines: [], nextToken: null });
      const error = new Error('read timeout'); error.code = 'ETIMEDOUT'; throw error;
    },
    createPipeline: () => { writes += 1; const error = new Error('write timeout'); error.code = 'ETIMEDOUT'; throw error; },
  };
  const result = await control.commandCreate(client, { org: ORG, name: 'demo', allowlist: f.allowlist, candidate: f.candidate, 'candidate-sha256': f.candidateSha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.equal(result.reconciliationError, 'FLOW_API_UNAVAILABLE');
  assert.equal(writes, 1);
});

test('ambiguous update plus reconciliation read failure returns structured UNKNOWN', async () => {
  const flow = 'name: demo\nstages: {}\n';
  const f = files({ flow });
  let reads = 0, writes = 0;
  const client = {
    getPipeline: () => {
      if (reads++ === 0) return response({ pipeline: pipeline('name: old\n') });
      const error = new Error('read timeout'); error.code = 'ETIMEDOUT'; throw error;
    },
    updatePipeline: () => { writes += 1; const error = new Error('write timeout'); error.code = 'ETIMEDOUT'; throw error; },
  };
  const result = await control.commandUpdate(client, { org: ORG, pipeline: PIPELINE, name: 'demo', allowlist: f.allowlist, candidate: f.candidate, 'candidate-sha256': f.candidateSha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.equal(result.reconciliationError, 'FLOW_API_UNAVAILABLE');
  assert.equal(writes, 1);
});

test('ambiguous start plus reconciliation read failure returns structured UNKNOWN', async () => {
  const flow = 'name: demo\n';
  const f = files({ flow });
  const frozen = contextFile(f.dir, flow);
  let lists = 0, writes = 0;
  const client = {
    getPipeline: () => response({ pipeline: pipeline(flow) }),
    listPipelineRuns: () => {
      if (lists++ === 0) return response({ pipelineRuns: [], nextToken: null });
      const error = new Error('read timeout'); error.code = 'ETIMEDOUT'; throw error;
    },
    startPipelineRun: () => { writes += 1; const error = new Error('write timeout'); error.code = 'ETIMEDOUT'; throw error; },
  };
  const result = await control.commandStart(client, { org: ORG, pipeline: PIPELINE, allowlist: f.allowlist, context: frozen.file, 'context-sha256': frozen.sha256 });
  assert.equal(result.state, 'UNKNOWN');
  assert.equal(result.reconciliationError, 'FLOW_API_UNAVAILABLE');
  assert.equal(writes, 1);
});
