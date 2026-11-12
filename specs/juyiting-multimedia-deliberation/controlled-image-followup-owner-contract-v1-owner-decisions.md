# Schema 3 per-intent follow-up — final L0 Owner supplement

Date: 2026-10-01. Baseline API `8121e8d89ad0be13ddb79012b61955bac5ae8caa`, tree `e106bfa99b78c97ac2e6a765a7032a1db20dc9bf`. This file incorporates Main's owner-HTTP decisions and the preview→issue drift self-check. It is not implementation or product acceptance.

## 1. Preview drift self-check

**Decision: `bindingId` + `bindingEpoch` alone are not sufficient to prove that issue authorizes exactly what the owner saw in preview. Add an exact `expectedPreview` echo to the issue body.**

Source reasons:

1. `NativeProviderCredentialBindingDeclaration` parses `bindingId`, `bindingEpoch` and `modelId` as independent declaration fields. It enforces each field's shape, but contains no invariant requiring `bindingEpoch` to change when `modelId` changes.
2. `ControlledImageProviderOperatorPolicy.requireCurrent(...)` first matches the current binding ID/epoch, then independently selects server operator policy using model ID and returns `custody` and `policyRevision` from server configuration. Neither custody nor policy revision is part of the native binding snapshot or cryptographically/structurally derived from the epoch.
3. Existing consent issue request digest contains assignment, binding ID/epoch and acknowledgement, but does not contain previewed model/custody/operator-policy revision or a source digest.
4. The exact source/ACL/bytes digest is independent of Provider binding identity. Asset generation/revision/ACL or task-linked source facts can drift without any binding epoch change.

Therefore schema-2 follow-up issue body has these exact top-level fields:

```json
{
  "schemaVersion": 2,
  "interactionIdempotencyKey": "final-interaction-key",
  "intent": {"schemaVersion": 3},
  "providerBinding": {"bindingId": "binding_1", "bindingEpoch": "1"},
  "expectedPreview": {
    "ownerPayloadSha256": "64lowerhex",
    "instructionSha256": "64lowerhex",
    "sourceSnapshotSha256": "64lowerhex",
    "modelId": "model_1",
    "custody": "OPERATOR_TEMPLATE",
    "operatorPolicyRevision": "policy-r1"
  },
  "acknowledgement": "UNPRICED_EXTERNAL_ACCOUNT_ONE_IMAGE_REQUEST_ATTEMPT"
}
```

`expectedPreview` is not authority and is not trusted as source truth. Issue must re-resolve the current server source, same-session binding and operator policy, recompute all three digests, and compare every field exactly. Any difference is HTTP 409 `BOUNTY_FOLLOWUP_V3_CONFLICT`, with zero consent/operation-grant/execution/Chat writes. Hash comparison is constant-time; text facts use exact binary equality. The final persisted consent and operation grant store the re-derived server values.

No extra echo is required for pricing mode or attempt count because this contract fixes them to `UNPRICED_EXTERNAL_ACCOUNT` and `1`, and the existing policy rejects any other value. No timestamp/TTL tolerance or arbitrary drift window is introduced.

## 2. Main-decided owner wire corrections

- Endpoints are Chat-owned:
  - `POST /chat/conversations/{conversationId}/interactions/preview`
  - `POST /chat/conversations/{conversationId}/interactions/provider-consents`
  - `GET /chat/conversations/{conversationId}/interactions/provider-consents/request`
  - `POST /chat/conversations/{conversationId}/interactions/provider-consents/{consentId}/revoke`
  - existing `POST /chat/conversations/{conversationId}/interactions` with strict schema-3 branch
  - `GET /chat/conversations/{conversationId}/interactions/request`
- Owner success/error bodies remain inside the existing `JsonResult` envelope. The previously listed success fields are the exact `data` object, not a replacement top-level wire.
- Public follow-up reasons are `BOUNTY_FOLLOWUP_V3_INVALID_REQUEST`, `BOUNTY_FOLLOWUP_V3_NOT_FOUND_OR_FORBIDDEN`, `BOUNTY_FOLLOWUP_V3_CONFLICT`, and `BOUNTY_FOLLOWUP_V3_UNAVAILABLE`. Authentication keeps the existing 401 behavior; owner-safe absence is 404, drift/idempotency conflict 409, real source/policy/storage unavailability 503.
- A schema-3 instruction is non-null, nonblank, at most 4000 Unicode code points, and contains no ISO control character, matching `PersonalWorkspaceExecutionServiceImpl.text(command.instruction(), "instruction", 4000)`. No new body-size limit is added.
- Scope IDs retain 50-code-point boundaries; ordinary IDs and idempotency keys retain 100-code-point boundaries, nonblank/no ISO controls, with existing strip rules where the current ID validator applies.

### Exact HTTP source shapes

GENERATE source item remains:

```json
{"kind":"TASK_LINKED_WORKSPACE_VERSION","fileId":"file_1","version":"3","purpose":"REFERENCE"}
```

EDIT owner source item is nested:

```json
{"kind":"CURRENT_CONVERSATION_ASSET","assetRef":{"assetId":"ast_previous","revision":"1"}}
```

The runtime v3 descriptor remains unchanged and contains the server-derived flat full producer lineage.

For `EDIT_IMAGE`, `continuationOf` is mandatory and exact `{requestId,stepId}`. The server-selected asset's producer request ID and producer step ID must equal it; another same-conversation parent is rejected. For `GENERATE_IMAGE`, `continuationOf` may be null or an exact existing compatible request/step in the current owner scope, conversation generation and task. It never grants operation/source authority.

## 3. Issue transaction equality gate

After same-key replay lookup and before any insert, issue must compare:

- exact schema-3 intent and derived request/step/execution-intent IDs;
- current conversation generation, task/assignment/grant/requirement/target tuple;
- current server source descriptor and `sourceSnapshotSha256`;
- exact instruction and `instructionSha256`;
- canonical owner intent and `ownerPayloadSha256`;
- current same-session `bindingId`, `bindingEpoch`, and `modelId`;
- current operator `custody` and `operatorPolicyRevision`;
- fixed pricing mode, one-attempt policy and exact acknowledgement.

Only then may the transaction insert one `FOLLOWUP_EXECUTE/ISSUED` consent and one `AUTHORIZED` operation grant. A replay with the same issue key first validates the persisted request digest and returns the persisted projection without consulting current policy; a changed issue body is 409.

## 4. Final exact implementation path allowlist

No directory wildcard, generated-file wildcard, or implied “corresponding” path is part of this list.

### Existing Agent files allowed to change

1. `agent/jia-agent-api/src/main/java/cn/jia/agent/service/AgentTaskExecutionGrantService.java`
2. `agent/jia-agent-api/src/main/java/cn/jia/agent/service/AgentTaskProviderCostConsentService.java`
3. `agent/jia-agent-api/src/main/java/cn/jia/agent/service/PersonalWorkspaceExecutionService.java`
4. `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/AgentTaskProviderCostConsentEntity.java`
5. `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/PersonalWorkspaceExecutionEntity.java`
6. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/AgentTaskProviderCostConsentDao.java`
7. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/PersonalWorkspaceExecutionDao.java`
8. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/AgentTaskProviderCostConsentDaoImpl.java`
9. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/PersonalWorkspaceExecutionDaoImpl.java`
10. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/AgentTaskProviderCostConsentMapper.java`
11. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/PersonalWorkspaceExecutionMapper.java`
12. `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/AgentTaskExecutionGrantServiceImpl.java`
13. `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/AgentTaskProviderCostConsentServiceImpl.java`
14. `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`
15. `agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceConversationRuntimeController.java`
16. `agent/jia-agent-service/build.gradle`

### New Agent files allowed

1. `agent/jia-agent-api/src/main/java/cn/jia/agent/service/ControlledImageFollowupAuthorityService.java`
2. `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageFollowupAuthorityDTO.java`
3. `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageIntentOperationGrantEntity.java`
4. `agent/jia-agent-core/src/main/java/cn/jia/agent/entity/ControlledImageExecutionSourceV3Entity.java`
5. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/ControlledImageIntentOperationGrantDao.java`
6. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/ControlledImageExecutionSourceV3Dao.java`
7. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/ControlledImageIntentOperationGrantDaoImpl.java`
8. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/impl/ControlledImageExecutionSourceV3DaoImpl.java`
9. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/ControlledImageIntentOperationGrantMapper.java`
10. `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/ControlledImageExecutionSourceV3Mapper.java`
11. `agent/jia-agent-mapper/src/main/resources/db/agent-controlled-image-followup-v3.sql`
12. `agent/jia-agent-service/src/main/java/cn/jia/agent/config/ControlledImageFollowupV3SchemaInitializer.java`
13. `agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/ControlledImageFollowupAuthorityServiceImpl.java`

### Existing Chat files allowed to change

1. `chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatBountyInteractionController.java`
2. `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionAdmissionService.java`
3. `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyExecutionCoordinator.java`
4. `chat/jia-chat-service/src/main/java/cn/jia/chat/handler/AgentWebSocketHandler.java`
5. `chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/conversation/ChatConversationArchiveStore.java`
6. `chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/conversation/JdbcChatConversationArchiveStore.java`
7. `chat/jia-chat-mapper/src/main/java/cn/jia/chat/deliberation/ChatInteractionStepStore.java`
8. `chat/jia-chat-service/build.gradle`

### New Chat files allowed

1. `chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatBountyInteractionV3Controller.java`
2. `chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatBountyInteractionV3Wire.java`
3. `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionV3PreviewService.java`
4. `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyInteractionV3AuthorityService.java`
5. `chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatConversationAssetSourceResolver.java`

### Exact Agent test files allowed

1. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageIntentOperationGrantServiceTest.java`
2. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageIntentOperationGrantSpringTransactionTest.java`
3. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageIntentOperationGrantMySqlTest.java`
4. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/PersonalWorkspaceControlledImageV3ExecutionTest.java`
5. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/PersonalWorkspaceControlledImageV3StartTest.java`
6. `agent/jia-agent-service/src/test/java/cn/jia/agent/config/ControlledImageFollowupV3SchemaInitializerTest.java`
7. `agent/jia-agent-service/src/test/java/cn/jia/agent/security/AgentRuntimeControlledImageV3SecurityIntegrationTest.java`
8. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/AgentTaskProviderCostConsentServiceImplTest.java`
9. `agent/jia-agent-service/src/test/java/cn/jia/agent/api/AgentTaskProviderCostConsentControllerTest.java`
10. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageGrantAuthorityTest.java`
11. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageConversationStartTest.java`
12. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageBridgeAtomicitySpringTest.java`
13. `agent/jia-agent-service/src/test/java/cn/jia/agent/service/impl/ControlledImageBridgeMySqlTest.java`
14. `agent/jia-agent-service/src/test/java/cn/jia/agent/security/AgentRuntimeSecurityIntegrationTest.java`

### Exact Chat test files allowed

1. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/api/ChatBountyInteractionV3ControllerTest.java`
2. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyInteractionV3PreviewServiceTest.java`
3. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyInteractionV3AuthorityServiceTest.java`
4. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyInteractionV3AdmissionServiceTest.java`
5. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatConversationAssetSourceResolverTest.java`
6. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyExecutionCoordinatorV3Test.java`
7. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyExecutionCoordinatorV3SpringTransactionTest.java`
8. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/handler/AgentWebSocketControlledImageV3ExecutionTest.java`
9. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/handler/ControlledImageBountyExecutionV3DeclarationTest.java`
10. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyInteractionAdmissionServiceTest.java`
11. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyInteractionRequestStatusTest.java`
12. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyExecutionCoordinatorTest.java`
13. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/ChatBountyExecutionCoordinatorSpringTransactionTest.java`
14. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/handler/AgentWebSocketControlledImageExecutionTest.java`
15. `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/handler/ControlledImageBountyExecutionDeclarationTest.java`

The list intentionally excludes initial point-and-start/bridge-operation semantics, old v1/v2 wire DTOs, Web/Client/SDD, finalization/formal delivery, Provider account selection, production operations and unrelated develop files.
