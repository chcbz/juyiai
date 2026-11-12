#!/usr/bin/env python3
"""Static wire/expectation validation only; not implementation or product acceptance."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
path = ROOT / 'controlled-image-bridge-v1.json'
digest = hashlib.sha256(path.read_bytes()).hexdigest()
assert (ROOT / 'controlled-image-bridge-v1.sha256').read_text().strip() == digest + '  ' + path.name
value = json.loads(path.read_text())
assert value['status'] == 'FROZEN_EXPECTATIONS_NOT_EXECUTED'
assert value['real_provider_authority'] is False
wire = value['wire']
assert set(wire['wrapper']) == {'schemaVersion', 'assignment', 'providerConsent'}
assert set(wire['wrapper']['providerConsent']) == {'consentId', 'expectedVersion'}
assert set(wire['wrapper_receipt']) == {'schemaVersion', 'grant', 'providerConsent'}
assert wire['consent_issue_body']['assignment'] == wire['wrapper']['assignment']
assert wire['consent_issue_body']['assignmentIdempotencyKey'] == wire['assignment_key']
assert wire['consent_issue_key'] != wire['assignment_key']
command = wire['command']
assert set(command) == {'schemaVersion', 'taskId', 'runId', 'conversationId', 'commandId', 'messageId',
                        'instruction', 'outputContentMimeType', 'outputId', 'providerExecution'}
assert command['schemaVersion'] == 2 and command['outputContentMimeType'] == 'image/png'
assert command['outputId'] == 'output_1'
descriptor = command['providerExecution']
assert set(descriptor) == {'providerLane', 'consentId', 'bindingId', 'bindingEpoch', 'modelId',
                           'maxInputItems', 'maxOutboundRequestAttempts', 'precallFenceVersion'}
assert re.fullmatch(r'consent_[a-f0-9]{32}', descriptor['consentId'])
assert descriptor['providerLane'] == 'CONTROLLED_IMAGE_HTTP_V1'
assert descriptor['maxInputItems'] == 16 and descriptor['maxOutboundRequestAttempts'] == 1
assert descriptor['precallFenceVersion'] == 1 and descriptor['bindingEpoch'] == '1'
assert wire['provider_start_request']['providerExecution'] == descriptor
assert wire['provider_start_receipt']['providerExecution'] == descriptor
assert set(wire['provider_start_request']) == {'schemaVersion', 'commandId', 'messageId', 'executionId', 'providerExecution', 'fence'}
assert set(wire['provider_start_receipt']) == {'schemaVersion', 'started', 'taskId', 'runId', 'executionId', 'commandId', 'messageId', 'providerExecution', 'leaseVersion'}
assert wire['provider_start_receipt']['started'] is True
assert wire['provider_start_receipt']['leaseVersion'] == wire['provider_start_request']['fence']['version']
for key in ('commandId', 'messageId'):
    assert wire['provider_start_receipt'][key] == wire['provider_start_request'][key] == command[key]
for key in ('taskId', 'runId'):
    assert wire['provider_start_receipt'][key] == command[key]
assert wire['authority_locator'] == 'mmd-ci-v1:' + descriptor['consentId']
assert len(wire['authority_locator']) <= 100
consent = wire['wrapper_receipt']['providerConsent']
assert consent['consentId'] == wire['wrapper']['providerConsent']['consentId'] == descriptor['consentId']
seed = value['fixture_seed']
assert hashlib.sha256(seed['assignment_base_hash_source_payload'].encode('utf-8')).hexdigest() == seed['assignment_base_hash_sha256'] == consent['assignmentBaseHash']
assert hashlib.sha256(('TASK_LINKED_INPUT_SNAPSHOT_V1\n' + seed['input_snapshot_json']).encode('utf-8')).hexdigest() == seed['input_snapshot_digest_sha256'] == consent['inputSnapshotDigest']
assert command['instruction'] == seed['requirement_title'] + '\n\n' + seed['requirement_description']
cap = wire['capability']
assert cap['schemaVersion'] == 2 and cap['maxInputItems'] == 16
assert cap['authorization'] == {'state': 'CONSENT_REQUIRED', 'paidExecutionAuthorized': False}
assert cap['newStart']['eligible'] is False
assert cap['originalIntentRecovery']['legacyFallbackAllowed'] is False
sibling = wire['controlledImageBountyExecution']
assert sibling['commandSchemaVersions'] == [2] and sibling['providerStartFenceVersions'] == [2]
assert sibling['operations'][0]['inputManifest']['maxItems'] == 16
assert set(value['case_groups']) == {'wrapper_replay', 'authority_tuple', 'three_atomic_segments', 'races_and_leases', 'input_boundaries'}
ids = []
for group in value['case_groups'].values():
    for case in group:
        assert set(case) == {'id', 'input', 'expect', 'result'} and case['result'] == 'NOT_RUN'
        ids.append(case['id'])
assert len(ids) == len(set(ids)) == 29
print('STATIC_CONTRACT_OK fixture_sha256={} expected_cases=29 implementation_executed=0 product_acceptance=false'.format(digest))
