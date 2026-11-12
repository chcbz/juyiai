# V0 hosting HTTP contract

Frozen by main from R01 application checkpoint `3bb9b762` on 2026-09-05. This is a source contract, not runtime acceptance. Full rent rules/pricing remain `v0-hosting-rent.md`. REPROVISION success below is the accepted next-slice contract, not implemented in that checkpoint.

## Common

Exact JWT `sub` payer / `jiacn` tenant / `client_id` client; backend independently proves canonical ownership. No client identity override. Existing JsonResult envelope; `Cache-Control: private, no-store`. Every POST requires a lowercase canonical UUID `Idempotency-Key`; preserve for unknown-outcome retry. No query params/unknown body fields. All money, periods, versions and epoch-ms timestamps are canonical decimal strings; `managed` is boolean. Mutation replay is the immutable original receipt, not current state.

## Requests

| Method/path | Body |
| --- | --- |
| POST `/agent/personas/{personaCode}/hosting-rent/quotes` | `{purpose:"INITIAL",agentId?:string|null}` |
| POST `/agent/personas/{personaCode}/bind` | `{mode:"server",hostingAction:"INITIAL",agentId,quoteId,expectedPlanVersion,expectedAmountMicro,expectedPeriodSeconds}` |
| Same bind route, free reprovision | `{mode:"server",hostingAction:"REPROVISION",agentId,leaseId,expectedLeaseVersion}` |
| GET `/agent/{agentId}/hosting-lease` | none |
| POST `/agent/hosting-leases/{leaseId}/renewal-quotes` | `{agentId,expectedLeaseVersion}` |
| POST `/agent/hosting-leases/{leaseId}/renewals` | `{agentId,quoteId,expectedLeaseVersion,expectedPlanVersion,expectedAmountMicro,expectedPeriodSeconds}` |

For INITIAL without binding, quote allocates only proposed opaque Agent ID; confirmation echoes it and reserve transaction creates identity/binding. Existing binding requires its explicit canonical Agent ID. Local/default bind remains existing behavior, no rent charge.

## Response data

`?` below denotes nullable/inapplicable.

Quote HTTP200:
```text
{quoteId,purpose,personaCode,agentId,leaseId?,expectedLeaseVersion?,planId,planVersion,
 currency,amountMicro,periodSeconds,expiresAt}
```
INITIAL confirmation HTTP202 / renewal confirmation HTTP200:
```text
{agentId,intentId,leaseId,quoteId,transactionId,status,currency,amountMicro,periodSeconds,occurredAt}
```
Original INITIAL status `FUNDS_RESERVED`; renewal `ACTIVE`. Accepted initial reservation is not service readiness. Display actual server plan/price/period; configured preview v1 is `"1" / "1000000000" / "2592000"` (1000 SILVER/30 fixed days), not a UI-side charging constant. Token/skill/task charges separate; no implicit renewal or historical backcharge.

Lease lookup HTTP200:
```text
{managed,
 lease?:{leaseId,agentId,personaCode,bindingId,version,status,planVersion,amountMicro,
         periodSeconds,paidFrom?,paidThrough?},
 intent?:{intentId,version,status,serviceReadyAt?,reserveTransactionId,
          captureTransactionId?,refundTransactionId?},
 admission,
 reprovision?:{requestId,version,status,requestedAt,serviceReadyAt?}}
```
Lease: `PROVISIONING|ACTIVE|REFUNDED`. Intent: `FUNDS_RESERVED|PROVISIONING_UNKNOWN|SERVICE_READY|FAILED_NO_EFFECT|ACTIVE|REFUNDED`. Admission: `NOT_MANAGED|PENDING|ALLOWED|RENEWAL_REQUIRED|INITIAL_REQUIRED`.

Free REPROVISION HTTP202 (next slice):
```text
{requestId,agentId,leaseId,operation:"REPROVISION",status:"ACCEPTED",currency:"SILVER",
 amountMicro:"0",leaseVersion,paidThrough,occurredAt}
```
Evolving reprovision lookup status: `ACCEPTED|PROVISIONING_UNKNOWN|SERVICE_READY|FAILED_NO_EFFECT`. Acceptance receipt never changes. Exact ACTIVE/unexpired lease + expected version; increment lease version once, preserve paid dates/price/history, zero ledger mutation/refund. Same-key replay before evaluating subsequent lease evolution. No duplicate generation creation while prior outcome unknown. Success is not advertised until adapter exists.

## Errors / UI behavior

- HTTP400: `BAD_REQUEST`, `HOSTING_RENT_INVALID_COMMAND`.
- 401: `HOSTING_RENT_UNAUTHENTICATED`.
- 403: `HOSTING_RENT_FORBIDDEN`, `HOSTING_RENT_OWNER_UNPROVEN`, `ECONOMY_PREVIEW_DISABLED`.
- 404: `HOSTING_RENT_NOT_FOUND_OR_FORBIDDEN`.
- 409: `INSUFFICIENT_SILVER`, `IDEMPOTENCY_CONFLICT`, `HOSTING_RENT_QUOTE_EXPIRED`, `HOSTING_RENT_QUOTE_ALREADY_CONSUMED`, `HOSTING_RENT_LEASE_CONFLICT`, `HOSTING_RENT_INTENT_CONFLICT`, `HOSTING_RENT_CONCURRENCY_CONFLICT`, `HOSTING_RENT_PLAN_VERSION_CONFLICT`, `HOSTING_RENT_AGENT_CONFIRMATION_REQUIRED`, `HOSTING_RENT_CONFLICT`.
- 503: `HOSTING_RENT_NOT_CONFIGURED`, `HOSTING_RENT_NOT_READY`, `HOSTING_RENT_REPROVISION_NOT_READY`, `HOSTING_RENT_UNAVAILABLE`.
- New-work guards: 409 `HOSTING_RENT_NOT_ACTIVE`, `HOSTING_RENT_RENEWAL_REQUIRED`.

Show quote, wallet availability, expiry and token-fees-separate before explicit confirm. Failure/unknown/disabled cannot fall back to the legacy server provisioning endpoint. Refetch latest lease after mutation with monotonic identity/version fencing; failed readback must not turn a confirmed reservation into failed payment. Pending reconciliation is not an invitation to repeat charging. Free reprovision and manual renewal are distinct actions.
