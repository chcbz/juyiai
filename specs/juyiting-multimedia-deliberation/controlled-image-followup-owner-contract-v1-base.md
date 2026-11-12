# Schema 3 per-intent controlled-image follow-up — API Owner contract preparation

Date: 2026-10-01. Status: **L0 source-backed proposal for the next freeze; no API/SDD source change and no capability claim**.

Source baseline: API merge candidate `8121e8d89ad0be13ddb79012b61955bac5ae8caa`, tree `e106bfa99b78c97ac2e6a765a7032a1db20dc9bf`. Runtime wire remains the frozen controlled-image v3 source wire. This proposal only closes the owner HTTP and durable per-intent authority gap.

## 1. Non-negotiable boundaries

1. Keep schema 2 at `POST /chat/conversations/{conversationId}/interactions` byte/semantic compatible. Add a strict `schemaVersion == 3` branch; never silently reinterpret a v2 body.
2. Never mutate the initial task grant's `grantVersion`, `permittedOperationsJson`, `inputScopeJson`, `allowOwnTaskDerivedAssets`, or single `costAuthorizationRef`. The initial `mmd-ci-v1:<consentId>` locator remains initial assign-and-start authority only.
3. Every schema 3 `EXECUTE` intent gets a new interaction key, request/step/intent identity, owner-issued operation grant, Provider consent, execution/run, command and START fence. A `CONSUMED` initial or prior follow-up consent is never callable authority for another intent.
4. Consent is cost/account authority only. It cannot grant `EDIT_IMAGE`, choose a source, expand task scope, or repair a stale/revoked/reassigned baseline grant.
5. Existing `AgentTaskExecutionGrantServiceImpl.verifyAdmission(...)` keeps its ordinary rule `allowed.contains(operation)`. The follow-up aggregate uses a newly named baseline-currentness check plus the independent operation grant; it must not pass `GENERATE_IMAGE` to that old method while executing `EDIT_IMAGE`.
6. Agent code must not depend on Chat. The owner HTTP issue/admit orchestration therefore belongs in Chat and calls new Agent APIs; Chat resolves and later locks/revalidates conversation assets. All writes participate in the existing shared Spring transaction and roll back together.

## 2. Exact owner HTTP candidate

All endpoints require authenticated owner JWT plus exact tenant/client/owner context, `Cache-Control: private, no-store`, no query parameters, strict duplicate-key/trailing-token JSON rejection, and exactly one `Idempotency-Key` where stated. Unknown or extra JSON fields are invalid.

All long-valued schema 3 wire fields below are **canonical decimal strings** (no sign, no leading zero except `"0"`) to avoid JavaScript precision loss. Values exposed to existing number-only v2 code remain v2-only.

### 2.1 Read-only preview

`POST /chat/conversations/{conversationId}/interactions/preview`

Header `Idempotency-Key` is the final interaction key that will also be used for admit.

Exact request body:

```json
{
  "schemaVersion": 3,
  "interactionKind": "EXECUTE",
  "taskId": "task_1",
  "expectedConversationGeneration": "7",
  "expectedTaskVersion": "0",
  "expectedAssignmentRevision": "0",
  "expectedGrantVersion": "1",
  "requirementRevision": "1",
  "targetAgentId": "agent_1",
  "content": "把上一稿中的天空调整为黄昏",
  "actionProposal": {"kind": "edit_image"},
  "inputRefs": [
    {"kind": "CURRENT_CONVERSATION_ASSET", "assetId": "ast_previous", "revision": "1"}
  ],
  "replyTo": null,
  "continuationOf": {"requestId": "request_previous", "stepId": "step_previous"}
}
```

Strict operation/source union:

- `generate_image` → `GENERATE_IMAGE`; `inputRefs` contains 0–16 exact `{"kind":"TASK_LINKED_WORKSPACE_VERSION","fileId":"...","version":"1","purpose":"REFERENCE"}` entries.
- `edit_image` → `EDIT_IMAGE`; `inputRefs` contains exactly one exact `{"kind":"CURRENT_CONVERSATION_ASSET","assetId":"...","revision":"1"}` entry.
- `replyTo` is exactly `null` in this EXECUTE package. Clarification replies require a later separately frozen state/revision wire.
- `continuationOf` is `null` or exactly `{requestId,stepId}`. It is lineage only, never authority.
- The browser never sends asset producer lineage, MIME, hash, byte length, storage URI, grant ID, model ID, request ID, step ID or execution-intent ID.

Exact successful preview projection:

```json
{
  "schemaVersion": 3,
  "requestId": "...",
  "stepId": "...",
  "executionIntentId": "...",
  "ownerPayloadSha256": "...",
  "instructionSha256": "...",
  "sourceSnapshotSha256": "...",
  "conversationGeneration": "7",
  "taskVersion": "0",
  "assignmentRevision": "0",
  "grantVersion": "1",
  "requirementRevision": "1",
  "targetAgentId": "agent_1",
  "operation": "EDIT_IMAGE",
  "sources": [],
  "providerBinding": {"bindingId": "...", "bindingEpoch": "1"},
  "modelId": "...",
  "custody": "...",
  "operatorPolicyRevision": "...",
  "pricingMode": "UNPRICED_EXTERNAL_ACCOUNT",
  "maxOutboundRequestAttempts": 1
}
```

`sources` is the server-resolved immutable descriptor array, including exact MIME/hash/positive byte length and either workspace identity or the full asset producer tuple from the frozen v3 runtime wire. Preview is `@Transactional(readOnly=true)` and must perform zero inserts, updates, outbox writes, assignment/grant mutations, execution creation or Provider work.

### 2.2 Owner issue: one consent plus one operation grant

Minimal dependency-safe path (Chat-owned, because Agent must not call a Chat asset resolver):

`POST /chat/conversations/{conversationId}/interactions/provider-consents`

Header `Idempotency-Key` is a distinct **consent-issue key**. Body repeats the complete preview intent rather than accepting client-provided digests or proposed IDs:

```json
{
  "schemaVersion": 2,
  "interactionIdempotencyKey": "final-interaction-key",
  "intent": { "schemaVersion": 3, "interactionKind": "EXECUTE", "...": "the exact preview body" },
  "providerBinding": {"bindingId": "...", "bindingEpoch": "1"},
  "acknowledgement": "the exact frozen unpriced-external-account acknowledgement"
}
```

The issue service re-derives all IDs and all digests, resolves current server binding/policy/model facts, and rejects any mismatch with the body or current source. It atomically inserts:

- a fresh Provider consent with purpose `FOLLOWUP_EXECUTE`, state `ISSUED`, version 1; and
- a fresh owner operation grant with state `AUTHORIZED`, version 1, exact operation/source/intent tuple.

Exact successful/replay projection:

```json
{
  "schemaVersion": 2,
  "consentId": "consent_32lowerhex",
  "consentState": "ISSUED",
  "consentVersion": "1",
  "operationGrantId": "opgrant_32lowerhex",
  "operationGrantState": "AUTHORIZED",
  "operationGrantVersion": "1",
  "taskId": "task_1",
  "conversationId": "conversation_1",
  "conversationGeneration": "7",
  "requestId": "...",
  "stepId": "...",
  "executionIntentId": "...",
  "targetAgentId": "agent_1",
  "operation": "EDIT_IMAGE",
  "ownerPayloadSha256": "...",
  "instructionSha256": "...",
  "sourceSnapshotSha256": "...",
  "providerBinding": {"bindingId": "...", "bindingEpoch": "1"},
  "modelId": "...",
  "custody": "...",
  "operatorPolicyRevision": "...",
  "pricingMode": "UNPRICED_EXTERNAL_ACCOUNT",
  "maxOutboundRequestAttempts": 1,
  "expiresAt": "server-policy value"
}
```

Read-only ACK-loss recovery:

`GET /chat/conversations/{conversationId}/interactions/provider-consents/request`

It requires exactly one consent-issue `Idempotency-Key`, no query and no body. It returns the persisted projection only and never refreshes expiry, binding, model, state or policy.

Required revocation closure (pre-START authority only):

`POST /chat/conversations/{conversationId}/interactions/provider-consents/{consentId}/revoke`

Exact body: `{"schemaVersion":2,"operationGrantId":"...","expectedConsentVersion":"1","expectedOperationGrantVersion":"1"}` plus a distinct revoke `Idempotency-Key`. Consent and operation grant revoke atomically. A consumed authority cannot be made callable again and revocation does not hide already committed assets; current asset ACL still governs reads.

### 2.3 Final admit on the existing interactions path

`POST /chat/conversations/{conversationId}/interactions`

Header is the same final interaction key used by preview. Body is the exact preview body plus exactly one field:

```json
"authority": {
  "consentId": "consent_32lowerhex",
  "expectedConsentVersion": "1",
  "operationGrantId": "opgrant_32lowerhex",
  "expectedOperationGrantVersion": "1"
}
```

Schema 3 response is exact and versioned rather than silently reusing the unversioned v2 record:

```json
{
  "schemaVersion": 3,
  "requestId": "...",
  "userMessageId": "...",
  "stepId": "...",
  "executionIntentId": "...",
  "consentId": "...",
  "operationGrantId": "...",
  "state": "PLANNING",
  "stateVersion": "0",
  "eventCursor": "...",
  "statusUrl": "/chat/requests/...",
  "replay": false
}
```

Read-only original-key recovery:

`GET /chat/conversations/{conversationId}/interactions/request`

It requires exactly one interaction `Idempotency-Key`, no query and no body. It returns the same persisted schema 3 projection. It cannot create missing rows, reserve consent, re-resolve source, advance state, emit an event or touch `updated_at`.

## 3. Identity and digest timing

The existing stable domains remain the basis:

- `requestId = stable("mmd-interaction-request", tenantId, clientId, owner, interactionKey)`
- `stepId = stable("mmd-interaction-step", requestId)`
- `executionIntentId = stable("mmd-interaction-execution", stepId)`

Timing is explicit:

1. Preview derives the three IDs after authenticated scope/key validation. They are provisional and nothing is persisted.
2. Issue re-derives them and reserves the tuple durably in the consent/operation-grant rows. It does **not** insert a Chat request/message/step/execution or create an Agent execution.
3. Admit re-derives them and inserts the exact Chat request/step/link plus Agent execution. A mismatch with the reserved tuple is 409.
4. A different consent-issue key cannot create a second authority for the same `executionIntentId`; the unique constraint rejects it. Recovery uses the original issue key.

Canonical SHA-256 domains use `CanonicalContextJson` v1 (recursive lexical object keys, array order preserved, compact UTF-8, exact JSON escaping):

- `ownerPayloadSha256`: schema 3 intent body excluding `authority`, with every version already represented as canonical decimal text.
- `instructionSha256`: `{"instruction":<exact content>,"schemaVersion":1}`; no trim, Unicode normalization or model rewrite.
- `sourceSnapshotSha256`: server-resolved exact scope/operation/source descriptors including MIME/hash/byte length and complete workspace or asset lineage; never browser-provided lineage.
- `interactionRequestDigest`: full schema 3 admit body including the authority IDs/expected versions. This is the Chat idempotency digest.
- `consentIssueRequestDigest`: full schema 2 issue body. This is the consent-issue idempotency digest.
- Runtime `inputSnapshotDigest` remains the separately frozen domain containing real execution/run IDs and materialized inputs. Admit must persist both owner/source digests and the later runtime digest; it must not claim they are interchangeable.

Same key behavior:

- same issue key + same issue digest → persisted receipt replay;
- same issue key + different body/binding/acknowledgement/intent → 409;
- same interaction key + same full admit digest → persisted interaction replay **before** current revoke/reassignment checks;
- same interaction key + any changed schema/content/operation/ref/revision/parent/authority/version → 409;
- GET by original key is read-only and 404/unknown never authorizes a fresh key or legacy fallback.

## 4. Exact lower bounds from current storage/code

| Fact | Lower bound | Wire form | Actual source basis |
|---|---:|---|---|
| `conversationGeneration` | 1 | decimal string | `chat_conversation.lifecycle_generation` defaults/repairs to 1; interaction admission rejects `<1`; archive CHECK permits null only before save and otherwise `>=1`. |
| `taskVersion` / `expectedTaskVersion` | 0 | decimal string, max 9007199254740991 | Root task version 0 is valid; current consent parser and task mutation validation accept `>=0`. |
| `assignmentRevision` / `expectedAssignmentRevision` | 0 | decimal string, max 9007199254740991 | Grant and bounty-binding CHECKs are `>=0`; current interaction admission accepts 0. |
| `requirementRevision` | 1 | decimal string | Grant/consent CHECKs require positive revision. |
| baseline `grantVersion` | 1 | decimal string | Grant CHECK and admission require `>=1`. |
| `workspaceVersion` | 1 | decimal string on schema 3 wire; Java/SQL INT internally | Workspace/version/link/execution-input CHECKs require `>=1`. |
| `assetRevision` | 1 | decimal string | Archive and conversation-asset access require exact revision; archive CHECK is `>=1`. |
| consent/operation-grant version | 1 | decimal string | New authority state starts at version 1 and every CAS increments. |
| request/step revision | 1 | internal BIGINT | Current interaction inserts request revision 1 and step request/step number 1. |
| request/step/link `stateVersion` | 0 | decimal string | Existing Chat tables default/insert 0; do not incorrectly require positive. |
| binding epoch | 1 | decimal string | Existing provider consent requires a canonical positive long. |

The v3 image source additionally requires positive byte length even though generic workspace storage permits zero-byte rows; JPEG/PNG validation and the frozen v3 runtime input wire require actual positive bytes.

## 5. Authority checks and transaction sequence

### Preview (read-only)

1. Authenticate exact owner scope and validate path/key/body.
2. Derive provisional IDs and owner payload/instruction digests.
3. Read exact live bounty conversation/generation/task relation and one target.
4. Read current task root, active baseline grant, assignment epoch, target identity and current requirement. Check supplied versions exactly.
5. Resolve sources: workspace version + active task link + bytes facts, or exact current-conversation asset via persisted producer lineage and current ACL.
6. Check the registered same-session v3 declaration, binding epoch, operator policy and model facts. No consent/grant/execution write.

### Issue (one transaction)

1. Parse/re-derive all IDs/digests. Lookup prior consent-issue key first; exact replay returns, changed digest 409.
2. Pre-read the Chat conversation/source snapshot without locks.
3. Lock Agent owner task root, then active baseline grant/target/workspace rows. Verify exact task/assignment/grant/requirement/target and baseline state is `ACTIVE`, current and not revoked/superseded.
4. Verify target's current registered v3 capability supports the requested operation and exact source kind; verify current provider binding/operator policy. This is not inferred from enum syntax.
5. Insert the per-intent operation grant and `FOLLOWUP_EXECUTE` consent, linked one-to-one by intent and consent IDs.
6. Lock Chat bounty binding, conversation and (for EDIT) exact producer request/step/link/asset rows; re-resolve bytes/ACL and compare source digest. Any drift throws and rolls back Agent inserts.
7. Commit; there is no execution, run, lease, command, START, outbox or Provider call.

### Admit (one root-first transaction)

1. Parse/re-derive IDs/digests. Read prior Chat request first. Exact replay returns before stale/revoked authority checks; changed digest 409.
2. Pre-read current Chat source snapshot.
3. Lock Agent task root and revalidate current baseline assignment/grant/target/requirement. The new baseline method validates currentness only and does not pretend that a GENERATE-only baseline grants EDIT.
4. Lock the exact operation grant; require `AUTHORIZED`, matching owner/task/conversation/generation/intent/operation/instruction/source/payload/baseline tuple and expected version.
5. Lock the exact consent; require `ISSUED`, purpose `FOLLOWUP_EXECUTE`, same operation-grant/intent/digests/provider binding/account policy and expected version. A non-empty consent ID is not authority.
6. Lock/revalidate workspace source rows where applicable. Create one v3 execution/run and immutable v3 execution-source rows. Atomically move operation grant `AUTHORIZED→RESERVED` and consent `ISSUED→BOUND→RESERVED`; persist execution/run on both.
7. Only after Agent execution creation, lock Chat bounty binding, conversation and exact asset lineage/source rows. Revalidate generation, task, assignment, current ACL and source digest.
8. Insert Chat user message/request/step/execution link using the reserved IDs, bind link to the new execution, and emit one state event.
9. Any Chat/source failure rolls back execution, source rows, both authority transitions and Chat rows. No lock may be held across a Provider or external storage/network call.

At Provider START, the existing root-first controlled START aggregate is extended for schema 3 and atomically verifies the same baseline + operation grant + consent + execution/source/runtime lease tuple, then moves both authorities to `CONSUMED` and records first-only START. `CONSUMED` allows same-run read/stage/commit under live lease/current ACL; it never authorizes another Provider call.

## 6. Durable schema closure

### 6.1 New `agent_controlled_image_intent_operation_grant`

Required columns:

`id`, `operation_grant_id`, scope (`tenant_id`,`client_id`,`owner_jiacn`), `task_id`, `target_agent_id`, `conversation_id`, `conversation_generation`, `interaction_idempotency_key`, `request_id`, `step_id`, `execution_intent_id`, baseline tuple (`baseline_grant_id`,`baseline_grant_version`,`task_version`,`assignment_revision`,`requirement_revision`,`requirement_sha256`), `operation`, `instruction_sha256`, `source_snapshot_sha256`, `source_snapshot_json`, `owner_payload_sha256`, `consent_id`, issue idempotency (`issue_idempotency_key`,`issue_request_digest`), `state`, `version`, `reserved_execution_id`, `reserved_run_id`, `consumed_lease_id`, revoke key/digest/time, `created_at`, `update_time`.

Constraints/indexes:

- IDs are exact `opgrant_[0-9a-f]{32}` and `consent_[0-9a-f]{32}`; hashes are 64 lowercase hex.
- Versions: conversation/requirement/baseline grant/authority version `>=1`; task/assignment `>=0`.
- state is `AUTHORIZED|RESERVED|CONSUMED|REVOKED` with strict nullability/lifecycle predicates.
- unique scoped operationGrantId, issue key, interaction key, executionIntentId and consentId; reserved execution/run unique when non-null.
- operation is only `GENERATE_IMAGE|EDIT_IMAGE`; source JSON is an array of 0–16; EDIT has exactly one asset source, GENERATE only workspace sources.

### 6.2 Additive columns on `agent_task_provider_cost_consent`

Keep all v1 columns and semantics. Add purpose-specific nullable columns with a strict union CHECK:

`consent_purpose` (existing rows default `INITIAL_ASSIGN_AND_START`; new value `FOLLOWUP_EXECUTE`), `operation_grant_id`, `execution_intent_id`, `conversation_id`, `conversation_generation`, `operation`, `instruction_sha256`, `source_snapshot_sha256`, `owner_payload_sha256`, `runtime_input_snapshot_sha256`.

For `FOLLOWUP_EXECUTE`, all fields except runtime digest before reservation are required and must match the operation-grant row. The existing `assignment_idempotency_key` is populated from the current baseline grant's real persisted assignment key; it is not overwritten with the follow-up key. Old bind/reserve/consume methods remain initial-purpose-only; new purpose-specific methods reject cross-purpose use.

### 6.3 New `agent_controlled_image_execution_source_v3`

Required columns:

`id`, scope, `execution_id`, `input_ref`, `input_ordinal`, `source_kind`, `content_mime_type`, `byte_length`, `content_sha256`, `source_json`, workspace union (`file_id`,`file_version`,`purpose`), asset union (`conversation_id`,`conversation_generation`,`asset_id`,`asset_revision`,`producer_request_id`,`producer_request_revision`,`producer_step_id`,`producer_execution_id`,`producer_run_id`,`producer_output_id`), `created_at`.

Strict union:

- workspace source: version `>=1`, purpose `REFERENCE`, all asset columns null;
- asset source: generation/revision/request revision `>=1`, complete producer tuple, all workspace columns null;
- MIME only `image/jpeg|image/png`, byte length `>0`, hash 64 lowercase hex, ordinal 1–16, unique execution/inputRef and execution/ordinal.

### 6.4 Additive v3 execution facts

Add to `agent_personal_workspace_execution`: `execution_protocol_version` (legacy/current rows retain their real version; v3 is 3), `operation_grant_id`, and `runtime_input_snapshot_digest`. The existing `controlled_consent_id` remains. A strict CHECK requires the full v3 tuple only for protocol 3 and permits no schema-3 operation-grant fields on v1/v2 rows. Do not weaken the existing v2 `GENERATE_IMAGE` controlled-consent CHECK.

No Chat schema addition is necessary for the minimum if Chat readback obtains authority by the unique `executionIntentId` through the Agent API. `chat_request.request_digest`, `chat_interaction_step.input_snapshot_digest` and `chat_step_execution_link` remain the durable Chat identity/link; the link is bound to the created execution in the admit transaction.

## 7. Exact implementation closure/write allowlist for the future package

No file below was changed in this L0 task. The next frozen implementation should be limited to these paths plus tests/build selectors explicitly frozen with it.

### Agent existing paths to extend

- `agent/jia-agent-api/src/main/java/cn/jia/agent/service/AgentTaskExecutionGrantService.java`
- `agent/jia-agent-api/src/main/java/cn/jia/agent/service/AgentTaskProviderCostConsentService.java`
- `agent/jia-agent-api/src/main/java/cn/jia/agent/service/PersonalWorkspaceExecutionService.java`
- `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/AgentTaskProviderCostConsentEntity.java`
- `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/PersonalWorkspaceExecutionEntity.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/AgentTaskProviderCostConsentDao.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/AgentTaskProviderCostConsentDaoImpl.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/AgentTaskProviderCostConsentMapper.java`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/AgentTaskExecutionGrantServiceImpl.java`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/AgentTaskProviderCostConsentServiceImpl.java`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceConversationRuntimeController.java`

### Agent new paths

- `agent/jia-agent-api/src/main/java/cn/jia/agent/service/ControlledImageFollowupAuthorityService.java`
- `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageIntentOperationGrantEntity.java`
- `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageExecutionSourceV3Entity.java`
- `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageFollowupAuthorityDTO.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/ControlledImageIntentOperationGrantDao.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/ControlledImageExecutionSourceV3Dao.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/ControlledImageIntentOperationGrantDaoImpl.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/ControlledImageExecutionSourceV3DaoImpl.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/ControlledImageIntentOperationGrantMapper.java`
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/ControlledImageExecutionSourceV3Mapper.java`
- `agent/jia-agent-mapper/src/main/resources/db/agent-controlled-image-followup-v3.sql`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/config/ControlledImageFollowupV3SchemaInitializer.java`
- `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/ControlledImageFollowupAuthorityServiceImpl.java`

### Chat existing paths to extend

- `chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatBountyInteractionController.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionAdmissionService.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyExecutionCoordinator.java`
- `chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/conversation/ChatConversationArchiveStore.java`
- `chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/conversation/JdbcChatConversationArchiveStore.java`
- `chat/jia-chat-mapper/src/main/java/cn/jia/chat/deliberation/ChatInteractionStepStore.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/handler/AgentWebSocketHandler.java` for the already frozen v3 sibling declaration/current-session lookup only.

### Chat new paths

- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionV3PreviewService.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionV3AuthorityService.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatConversationAssetSourceResolver.java`
- `chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatBountyInteractionV3Controller.java`

Explicitly out of scope: initial point-and-start controller/service/bridge operation table, baseline grant locator mutation, old native v1/v2 DTO fields, Provider account selection, Client/Web/SDD, formal delivery/finalization, and production migration/deploy.

## 8. Focused verification selectors for the implementation freeze

New bounded Gradle tasks to add to the nearest existing build files (names are reserved by this proposal; they do not exist yet):

- `:agent:jia-agent-service:mmdControlledImageFollowupV3`
- `:chat:jia-chat-service:mmdControlledImageFollowupV3`

Required exact test classes:

Agent:

- `cn.jia.agent.service.impl.ControlledImageIntentOperationGrantServiceTest`
- `cn.jia.agent.service.impl.ControlledImageIntentOperationGrantSpringTransactionTest`
- `cn.jia.agent.service.impl.ControlledImageIntentOperationGrantMySqlTest`
- `cn.jia.agent.service.impl.PersonalWorkspaceControlledImageV3ExecutionTest`
- `cn.jia.agent.service.impl.PersonalWorkspaceControlledImageV3StartTest`
- `cn.jia.agent.config.ControlledImageFollowupV3SchemaInitializerTest`
- `cn.jia.agent.security.AgentRuntimeControlledImageV3SecurityIntegrationTest`

Chat:

- `cn.jia.chat.api.ChatBountyInteractionV3ControllerTest`
- `cn.jia.chat.service.ChatBountyInteractionV3PreviewServiceTest`
- `cn.jia.chat.service.ChatBountyInteractionV3AuthorityServiceTest`
- `cn.jia.chat.service.ChatBountyInteractionV3AdmissionServiceTest`
- `cn.jia.chat.service.ChatConversationAssetSourceResolverTest`
- `cn.jia.chat.service.ChatBountyExecutionCoordinatorV3Test`
- `cn.jia.chat.service.ChatBountyExecutionCoordinatorV3SpringTransactionTest`
- `cn.jia.chat.handler.AgentWebSocketControlledImageV3ExecutionTest`
- `cn.jia.chat.handler.ControlledImageBountyExecutionV3DeclarationTest`

The implementation matrix must also rerun the unchanged compatibility selectors:

- `:agent:jia-agent-service:mmdU1ProviderConsentCore`
- `:agent:jia-agent-service:mmdControlledImageBridge`
- `:chat:jia-chat-service:mmdU1ProviderCredentialBinding`
- `:chat:jia-chat-service:mmdControlledImageBridge`

Minimum adversarial cases: exact happy GENERATE/EDIT; initial locator unchanged; consent-only EDIT rejected; baseline-only EDIT rejected; wrong operation/source/digest rejected; baseline revoked/superseded/reassigned/current-requirement drift; source generation/revision/producer lineage/current ACL drift; issue/admit same-key changed-body 409; issue/admit ACK-loss original-key GET writes zero rows; duplicate intent cannot obtain a second consent; 17th input rejected without truncation; operation grant/consent/execution atomic rollback on late Chat lock failure; concurrent issue/admit/START single winner; consumed authority cannot start a second call; v1/v2 command/declaration/START fixtures byte-exact.

## 9. Source evidence and remaining freeze choices

Key actual sources inspected:

- `ChatBountyInteractionController.java`: current path/body and hard `schemaVersion == 2`.
- `ChatBountyInteractionAdmissionService.java`: deterministic IDs, replay-before-grant mutation, current root→binding→conversation lock order, generation `>=1`, and current absence of ref resolver.
- `AgentTaskExecutionGrantServiceImpl.java`: active/current/revoke/assignment epoch/current requirement and ordinary `allowed.contains(operation)` enforcement.
- `AgentTaskProviderCostConsentServiceImpl.java` and v1 consent DDL: ISSUED→BOUND→RESERVED→CONSUMED lifecycle, task `>=0`, requirement/grant positive, assignment `>=0`, exact operator binding/policy facts.
- `JdbcChatConversationArchiveStore.findAuthorizedSource`: exact owner/client/tenant/conversation/generation/asset/revision and producer request/step/execution/run/output lineage.
- workspace/archive DDL: workspace version `>=1`, asset revision `>=1`, conversation generation `>=1`, Chat state version starts at 0.

Main still must freeze these presentation choices before implementation, without weakening authority semantics:

1. Final endpoint spelling: this proposal chooses Chat-owned `/interactions/provider-consents` to preserve the existing Chat→Agent dependency direction. A task-scoped Agent HTTP endpoint would require an additional server-authenticated Chat source-preview handle and is not the minimal closure.
2. Exact acknowledgement text/version for a follow-up unpriced external account; it cannot be invented by implementation.
3. Exact maximum `content`/identifier/body sizes, derived from existing transport and field contracts rather than arbitrary new limits.
4. Whether `continuationOf` is mandatory for EDIT or merely optional lineage; source authority remains the exact asset ref either way.
5. Exact public error-code names. Required statuses are 400 malformed, 401/403 identity, 404 owner-safe absent, 409 stale/idempotency/authority conflict, and 503 source/policy/storage unavailable.

No unresolved choice permits implementation to expose EDIT before the independent owner operation grant, reuse a prior consent, overwrite the baseline locator, accept client source lineage/digests, or downgrade to legacy behavior.
