# Agent Economy Marketplace V0 Preview Contract

> Frozen for the 2026-09-08 development preview. This file intentionally narrows the production SDD. Full signatures, PoP, mTLS download sessions, capability leases, provider broker/KMS, reconciliation, and production authorities remain deferred.

## Shared rules

- Feature gates default false:
  - API: `economy.preview.enabled=false`
  - Agent Client: `AGENT_SKILL_INSTALL_ENABLED=false`
  - Web only renders preview actions when the API capability response enables them.
- Scope is derived from authenticated JWT/runtime context. Money endpoints must not use fallback tenant/client/user identities.
- Currency is always `SILVER`.
- Monetary persistence uses signed 64-bit integer micro-silver; HTTP uses canonical non-negative decimal strings.
- `1 SILVER = 1,000,000 micro-silver`; display reference is `100 SILVER = 1 CNY`.
- Every money mutation requires `Idempotency-Key`. Same actor/key/body returns the original response; same actor/key/different body returns `409 IDEMPOTENCY_CONFLICT`.
- Funded task and skill purchase payloads always carry explicit `agentId`/`targetAgentId`; the server does not infer selected Agent state.

## Preview capability and owned Agent projection (2026-09-05 integration freeze)

These additions are required for W09/W13 integration; documentation does not imply the endpoints are already deployed. Use the existing `JsonResult` envelope (`code: "E0"`, payload in `data`).

`GET /economy/capabilities` is authenticated with the same exact JWT principal as wallet:

```json
{
  "economyPreviewEnabled": true,
  "skillMarketplaceEnabled": true,
  "principalScopeFingerprint": "opaque-server-derived-scope-fingerprint"
}
```

- Flags are server-derived booleans, false unless the corresponding configured preview scope and implemented feature are available. Missing/malformed responses disable Web actions; wallet HTTP 200 and `/agent/capabilities` (an Agent capability list) are not substitutes.
- Fingerprint is nonsecret, stable for the exact tenant/client/actor tuple and changes whenever any member changes. It binds browser recovery storage only, never authorizes a server mutation. Responses are private/no-store; do not include JWTs, API credentials, or signing secrets.
- Existing **POST `/agent/roster`** with JSON `{ "pageNum":1, "pageSize":50 }` remains authoritative. Add canonical decimal-string `version` to purchasable owned-Agent items; Web requires explicit selection plus `boundToMe === true` and `canOperate === true`. No GET-roster replacement, map-based selection, constant/fabricated version or numeric coercion.
- W09 must project a persisted Agent/binding concurrency token and validate it together with current ownership/readiness in quote/purchase transactions. The projection flags are not a substitute for server ACL. Until that token exists, purchase remains disabled rather than inventing version `"1"`.

## Economy foundation and wallet

### `GET /economy/wallet`

Response:

```json
{
  "currency": "SILVER",
  "availableMicro": "1200000000",
  "heldMicro": "300000000",
  "version": "17"
}
```

### `GET /economy/ledger?cursor=&limit=50`

Response items expose no internal counterparty:

```json
{
  "items": [{
    "transactionId": "etx_...",
    "entryId": "een_...",
    "businessType": "ISSUE_SILVER",
    "businessRef": "preview-welcome",
    "direction": "CREDIT",
    "amountMicro": "100000000",
    "status": "POSTED",
    "postedAt": "1788320000000"
  }],
  "nextCursor": null
}
```

### `POST /economy/preview/issuances`

Development preview only; disabled in production profile. Header `Idempotency-Key` required.

```json
{ "amountMicro": "1000000000", "campaignRef": "preview-welcome" }
```

Issues from `SYSTEM:SILVER_ISSUANCE` to the authenticated user wallet.

W03 response is the immutable receipt `{ "transactionId": "etx_...", "status": "POSTED", "amountMicro": "1000000000" }`. Idempotent replay returns that original receipt, not a newly read wallet balance. Wallet GET returns available, held and version from one consistent database snapshot; a missing wallet reads as zero without creating accounts.

## Funded bounty

### `POST /agent/tasks`

Legacy body remains unfunded. Adding the following fields creates a funded single-Agent task and reserves the full amount atomically:

```json
{
  "grossBountyAmountMicro": "1000000000",
  "settlementPolicy": "GROSS_INCLUSIVE",
  "requiredSkillRequirements": [{"skillKey":"repo-test","versionRange":">=1.0.0"}]
}
```

Response adds:

```json
{
  "funding": {
    "mode": "FUNDED_SINGLE_AGENT",
    "status": "FUNDS_HELD",
    "escrowId": "esc_...",
    "grossBountyAmountMicro": "1000000000",
    "remainingMicro": "1000000000"
  }
}
```

Stable failures include `INSUFFICIENT_SILVER`, `IDEMPOTENCY_CONFLICT`, and `FUNDED_TEAM_NOT_SUPPORTED`.

### `POST /agent/tasks/{taskId}/quotes`

Body and response follow the frozen production design section 7.3. V0 uses a seeded versioned fixed price book and integer arithmetic. Required response fields are `quoteId`, explicit `agentId`, `taskVersion`, `priceBookVersion`, four token categories, estimated/worst compute, platform fee, estimated/worst Agent payout, recommendation, reason codes, and `expiresAt`.

### `POST /agent/tasks/{taskId}/claim`

Body:

```json
{ "agentId":"canonical-agent-id", "quoteId":"q_...", "taskVersion":"8", "allowQueue":false }
```

Funded `/assign` returns `QUOTE_REQUIRED`; funded group/auto paths return `FUNDED_TEAM_NOT_SUPPORTED`.

Successful claim returns an immutable receipt (not a complete task snapshot):

```json
{
  "taskId":"task-id", "agentId":"canonical-agent-id", "quoteId":"q_...",
  "status":"assigned", "taskVersion":"9", "claimedAt":"1788320000000"
}
```

Same-key replay returns that receipt unchanged. Web must refresh the canonical task snapshot after confirmed success rather than treating this receipt as a full `AgentTaskDTO`. Task versions/timestamps remain canonical strings. W05 uses an explicitly labelled synthetic development-preview price book until an actual provider price-book version is configured; it is not a claim about current provider token prices. Required skill checks use `FundedBountySkillEntitlementLookup`: empty requirements are allowed, nonempty requirements fail closed until W09 provides exact scoped installed-and-active entitlement facts.

### Settlement preview endpoints

- `GET /agent/tasks/{taskId}/settlement`
- `POST /agent/tasks/{taskId}/funding/cancel` with `{ "expectedTaskVersion":"..." }` for pre-start cancellation/refund.
- `POST /agent/tasks/{taskId}/funding/complete` with `{ "expectedTaskVersion":"...", "actualComputeMicro":"..." }` is preview-only test orchestration. Amounts are server-capped by the accepted quote; the server calculates fee, payout, and refund and never accepts caller-supplied payout/fee.

## Skill market HTTP

- `GET /agent/skill-products`
- `GET /agent/skill-products/{productId}`
- `POST /agent/skill-orders/quotes` with `{productVersionId,targetAgentId,expectedAgentVersion}`
- `POST /agent/skill-orders` with `{quoteId,productVersionId,targetAgentId,expectedPriceMicro,expectedAgentVersion,approvedPermissions}`
- `GET /agent/skill-orders/{orderId}`
- `GET /agent/{agentId}/skill-entitlements`

Minimum quote response payload (the exact product/Agent tuple is echoed for recovery fencing):

```json
{
  "quoteId":"sq_...", "productVersionId":"spv_...",
  "targetAgentId":"canonical-agent-id", "expectedAgentVersion":"17",
  "priceMicro":"30000000", "expiresAt":"1788320000000"
}
```

Minimum order-create immutable receipt and order-GET payload share:

```json
{
  "orderId":"so_...", "productVersionId":"spv_...",
  "targetAgentId":"canonical-agent-id", "expectedAgentVersion":"17",
  "status":"FUNDS_HELD"
}
```

Create replay retains its original status/receipt; GET reports the current state. Catalog detail must supply explicit `productVersionId`, `skillKey`, `skillVersion`, canonical `priceMicro`, permission strings in `permissions`, and server-computed `canPurchase`/denial reason (including admin restriction). Backend must validate the approved permission subset again at purchase. Do not advertise a product as purchasable solely because its price exists.

Seeded products and exact whole-SILVER prices:

| skillKey | priceMicro | restriction |
| --- | ---: | --- |
| repo-inspector | 0 | none |
| code-reviewer | 20000000 | none |
| repo-test | 30000000 | none |
| code-editor | 50000000 | none |
| web-builder | 60000000 | none |
| deploy-runner | 100000000 | admin authority required |

Purchase states: `FUNDS_HELD → INSTALLING → ACTIVE`; installation failure before activation produces `REFUNDED`.

## Exact-Agent delivery credential setup (2026-09-06 integration freeze)

This supports non-rental managed clients as well as hosted Agents; buying a skill must not require paying hosting rent. A legacy owner/client-shared API key is not proof of one exact Agent. This is a narrow existing-API-key association, not production PoP/KMS or a new identity platform. Source contract only, not a deployed endpoint.

`POST /agent/{agentId}/skill-install-credentials`, exact JWT owner/current canonical binding, canonical UUID `Idempotency-Key`:

```json
{ "expectedAgentVersion": "17" }
```

First successful HTTP 201 payload:

```json
{
  "credentialId": "opaque-credential-id",
  "targetAgentId": "canonical-agent-id",
  "version": "18",
  "status": "CREATED",
  "apiKey": "<one-time-secret>",
  "recovery": "ROTATE_WITH_NEW_KEY"
}
```

- NEW key through existing `ApiKeyService`, unique keyId-to-Agent association and persisted Agent-version CAS commit together. Never adopt a reused generic key. Existing R01 fresh `hosting:<intentId>` keys may be associated only after exact scope/name/current binding verification and uniqueness checks.
- Private/no-store response; secret appears only on the first successful response, never in logs, browser persistence, GETs or replay. This setup endpoint is not a money mutation: its deliberate one-time-secret exception returns HTTP 409 `SKILL_CREDENTIAL_SECRET_NOT_REPLAYABLE` on exact same-key/body replay. Different-body reuse returns `IDEMPOTENCY_CONFLICT`.
- A lost response requires roster refresh followed by an **explicit** new-key rotation, never automatic retry with a new key. Rotation revokes the previous dedicated key, rejects pending/unknown installations, and does not kill ongoing work or infer a safe refund.
- Creation is not readiness. The supported client must use the dedicated key and establish exact authenticated canonical registration before purchase can charge; a stale old-key online runtime is insufficient.
- Installer download protocol remains existing `X-API-Key`. The frozen `/internal/agent/skill-installations/{installationId}/package` route has a narrowly scoped authenticated security chain. The WebSocket handshake retains only the authenticated API-key entity ID as a private session attribute; dedicated install-result processing compares that exact ID with the installation binding. No secret is carried in that attribute.

## Agent Client `SKILL_INSTALL` preview command

The existing canonical `command.dispatch` envelope remains authoritative. Required V0 fields:

```json
{
  "schemaVersion": 1,
  "messageType": "command.dispatch",
  "messageId": "msg_...",
  "requestId": "msg_...",
  "commandType": "SKILL_INSTALL",
  "commandId": "cmd_...",
  "attempt": 1,
  "fencingToken": "1",
  "deliveryEpoch": "1",
  "targetAgentId": "canonical-agent-id",
  "orderId": "so_...",
  "installationId": "si_...",
  "productVersionId": "spv_...",
  "skillKey": "repo-test",
  "skillVersion": "1.0.0",
  "packageSize": "123456",
  "packageDigest": "sha256:<64 lowercase hex>",
  "downloadPath": "/internal/agent/skill-installations/si_.../package"
}
```

Preview constraints:

- `downloadPath` must be an absolute same-origin API path beginning `/internal/agent/skill-installations/`; arbitrary URLs/hosts are rejected.
- Download uses the existing managed Agent API credential; no credential or package bytes are logged.
- Existing durable ACK order remains `RECEIVED → STARTED → SUCCEEDED|FAILED`.
- `SKILL_INSTALL` is handled by a dedicated installer, never by `runCodex` and never by the coding-worktree path.
- Staging is profile-local. Reject oversize/mismatched length, digest mismatch, path traversal, absolute paths, symlinks, duplicate entries, missing `SKILL.md`, and skill identity mismatch.
- Activation is atomic into `<CODEX_HOME>/skills/<skillKey>` with an installation marker and persistent installed-skill registry keyed by `installationId`.
- Same command fingerprint is idempotent; conflicting reuse of `installationId`, command fence, product version, or digest fails closed.
- A durable `work.result` outbox must be persisted before terminal `SUCCEEDED` so restart can replay activation evidence.

Terminal result payload:

```json
{
  "schemaVersion": 1,
  "messageType": "work.result",
  "resultType": "SKILL_INSTALL_RESULT",
  "commandId": "cmd_...",
  "attempt": 1,
  "fencingToken": "1",
  "deliveryEpoch": "1",
  "orderId": "so_...",
  "installationId": "si_...",
  "targetAgentId": "canonical-agent-id",
  "productVersionId": "spv_...",
  "status": "SUCCEEDED",
  "packageDigest": "sha256:...",
  "skillKey": "repo-test",
  "skillVersion": "1.0.0",
  "installedAt": "1788320000000",
  "failureCode": null
}
```

Stable failure codes: `SKILL_INSTALL_DISABLED`, `SKILL_INSTALL_COMMAND_INVALID`, `SKILL_DOWNLOAD_FORBIDDEN`, `SKILL_PACKAGE_TOO_LARGE`, `SKILL_PACKAGE_DIGEST_MISMATCH`, `SKILL_ARCHIVE_INVALID`, `SKILL_IDENTITY_MISMATCH`, `SKILL_INSTALL_CONFLICT`, `SKILL_INSTALL_IO_FAILED`.

## Explicit V0 security boundary

This preview verifies transport scope, same-origin download, exact SHA-256, archive safety, durable command fencing, and result replay. It does **not** claim package publisher-signature verification, binding PoP, mTLS download-session semantics, isolation attestation, capability leases, or production-grade refund reconciliation. Those remain governed by the full SDD and must not be advertised as complete.
