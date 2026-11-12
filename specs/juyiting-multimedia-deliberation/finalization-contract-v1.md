# MMD finalization v1 joint contract, 2026-09-30

Purpose: actual selected byte-backed conversation outputs -> trusted formal artifacts -> existing formal delivery submission -> real owner acceptance -> domain task completion. No generation/provider execution. This is NOT a reviewer task, and not permission to deploy/migrate production.

HTTP:
- POST /agent/tasks/{taskId}/finalizations, required Idempotency-Key, existing JsonResult wrapping; synchronous 200 completed or 202 genuinely pending, precise existing error status/code.
- GET /agent/tasks/{taskId}/finalizations/{operationId}: read-only receipt.
- GET /agent/tasks/{taskId}/finalizations/request: read-only original Idempotency-Key lookup; 404 is not proof a POST was not accepted. Specific request path must not be captured by operationId mapping.

POST body (exact keys): expectedTaskVersion (safe integer >=0), expectedAssignmentRevision (safe integer >=0), conversationId (exact string), summary (nonempty <=4000), selectedOutputs (ordered array 1..99 unique sources). Each selection has exact requestId,stepId,outputId,sha256,title,purpose. The sha256 is an expected pin, NEVER ownership authority. 99 derives from existing formal submission max100 including manifest. Model/browser cannot supply producer,lease,run,scope,storage URL/path or authorization fields.

Receipt fields (no secrets):
operationId, taskId, conversationId, state [pending,completed,failed], stateVersion (positive decimal string), stage [PROMOTING,READY_TO_SUBMIT,SUBMITTED,ACCEPTING,TASK_COMPLETED], expectedTaskVersion (nonnegative decimal string matching original intent), expectedAssignmentRevision (same), selectedOutputs (exact frozen six-field array), deliveryId (nullable exact string), deliveryState (nullable/submitted/accepted), taskState (exact persisted domain state), taskVersion (nonnegative decimal string), errorCode (nullable owner-safe string), retryable(boolean).

TASK_COMPLETED only when real domain task completed AND formal accepted, with actual deliveryId; other stages are progress, not success. Versions in receipt are strings to avoid precision loss. Reads never submit/accept/promote. POST same key/body reconciles exact stages, not new generation. Same key different immutable body ->409.

Admission binds authenticated owner/client/tenant, actual task/conversation/generation, exact persisted request/step/execution/output, original assignment and target, present grant/ACL, bytes hash/MIME/length, current root version. New decisions are user's explicit selected-set acceptance. Reassignment/revocation races must not accept another assignment. Replay of known committed operation is before obsolete lease/task versions.

Trusted promotion lives in Agent service and may be called by Chat orchestration through agent-api contract; no agent-service -> chat-service cycle. Preserve real producer/work-item/run/lease semantics via explicit server-owned promotion authority and actual lease claim/start, not forged runtime receipts or deleting lease checks. Reuse artifact storage/publish, formal submit and real owner decision services. No creation of a Provider execution just to obtain a lease. Scope this adapter to verified conversation outputs and current task/assignment.

Persist immutable selected set and per-phase facts. Source bytes store/validated before formal records; producer secrets private only. Do not hold Chat/archive locks across Agent task root/storage calls. Prepare recovery after promotion/submission/acceptance ACK loss; never claim distributed atomicity. User acceptance and optional workspace archival remain independent.

Web stores original body/key before POST, locks original selections while outcome unknown, restores intent across remount, reads known operation/original key before explicit original POST replay. Identity change aborts and fences late receipts. No automatic writes on polling/replay/remount. A bare stage label is insufficient for completion; validate exact scope, frozen selections, original versions and real delivery/task facts. API implementation must match this contract or report exact necessary change before integration.
