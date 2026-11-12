# Agent Economy Marketplace V0 — Development Preview Plan

> Status: implementation authorized on 2026-09-02. This is a development preview only and does not satisfy the full production SDD acceptance bundle.

## Delivery target

- Preview deployment: 2026-09-08
- UAT and bounded fixes: 2026-09-09
- Feature flags: disabled by default; enabled only in the development preview environment after smoke checks.

## Frozen V0 scope

1. Independent `SILVER` wallet with immutable balanced journal entries.
2. Test issuance, wallet balance, and ledger history.
3. Funded bounty creation with full escrow and insufficient-balance rejection.
4. Versioned fixed price book, token estimate, explicit quote and explicit `agentId` claim.
5. Basic completion settlement and pre-start cancellation refund.
6. Platform-operated skill catalog with six seeded products:
   - `repo-inspector`: 0 SILVER
   - `code-reviewer`: 20 SILVER
   - `repo-test`: 30 SILVER
   - `code-editor`: 50 SILVER
   - `web-builder`: 60 SILVER
   - `deploy-runner`: 100 SILVER, admin-only
7. Skill purchase with explicit `targetAgentId`, escrow, `command.dispatch/SKILL_INSTALL`, SHA-256 package verification, result handling, activation, and failure refund.
8. Wallet, funded bounty quote/settlement, and skill-market Web UI.
9. Managed Agent Client implementation in the existing ADR-004 source repository, followed by controlled sync to the deployment copy without replacing runtime `data/` or `logs/`.
10. Added 2026-09-05: 招贤令 `server`（山寨安顿）hosting rent; `local`（自家接应）has no hosting rent. Versioned price/period configuration, explicit confirmation, lease state and manual renewal, idempotent payment and provisioning-failure compensation. See `v0-hosting-rent.md`; user delegated pricing on 2026-09-05, and preview plan v1 is 1,000 SILVER per Agent per fixed 30 days. Charging remains disabled until verified preview release.

## Unit and conversion

- `1 SILVER = 1,000,000 micro-silver`.
- Preview display reference: `100 SILVER = 1 CNY`.
- SILVER is not equal to provider tokens. Token usage is converted through a versioned price book; model/input/output/cache/reasoning categories can have different rates.
- API monetary amounts are decimal strings; persistence and arithmetic use integer micro-silver.

## Deferred to V1 / production hardening

- Full Provider Egress Broker and KMS lifecycle.
- Binding rotation and PoP challenge.
- Capability leases and complete isolation attestations.
- Automated UNKNOWN reconciliation.
- Historical funded-task migration.
- Third-party sellers.
- Production approval gates and exhaustive adversarial suites.

## Work packages and estimates

| ID | Deliverable | Estimate |
| --- | --- | ---: |
| ECO-V0-W01 | Contract constants, feature flags, preview fixtures | 2h |
| ECO-V0-W02 | Economy schema, balanced ledger, escrow foundation | 8h |
| ECO-V0-W03 | Test issuance, wallet and ledger APIs | 6h |
| ECO-V0-W04 | Funded bounty create/cancel/refund | 8h |
| ECO-V0-W05 | Price book, token quote and explicit claim | 8h |
| ECO-V0-W06 | Basic completion settlement | 6h |
| ECO-V0-W07 | Skill product/order/installation schema | 8h |
| ECO-V0-W08 | Seed six platform-operated skills | 4h |
| ECO-V0-W09 | Purchase/install-result/activation/refund APIs | 8h |
| ECO-V0-W10 | Managed Agent Client basic skill installation | 14h |
| ECO-V0-W11 | Wallet and funded-bounty Web UI | 12h |
| ECO-V0-W12 | Skill-market Web UI | 10h |
| ECO-V0-W13 | Targeted API/Web/Agent verification and review | 8h |
| ECO-V0-W14 | Development deployment and smoke | 4h |

Aggregate estimate: about 106 engineering hours. With API/Web/Agent work overlapped after the DTO contract freezes, expected critical path is 45–55 hours.

The original estimate excludes the 2026-09-05 rental addition. Its backend/UI/verification work is tracked as `ECO-V0-R00` (admission prerequisite) and `ECO-V0-R01/R02/R03` in the canonical runtime ledger and must join W13/W14 integration; the original preview dates remain targets, not verified delivery promises.

## Preview acceptance checklist

- Feature flags are off by default.
- A test user can receive SILVER and see balance plus immutable ledger history.
- Creating a funded bounty reserves the exact amount; insufficient funds returns a stable error and creates neither task nor partial journal.
- Quote shows token categories, price-book version, expected/worst model cost, platform fee, and expected/worst Agent income.
- Claim always carries explicit `agentId`; no selected-state fallback is accepted.
- Completion balances escrow into model cost, platform fee, Agent income, and user refund; pre-start cancellation fully refunds the remaining escrow.
- The six seeded skills render with the frozen prices and `deploy-runner` is admin-only.
- Purchase always carries explicit `targetAgentId`; successful verified installation activates the entitlement and failed installation refunds before activation.
- Juyi Hall continues to use `/agent/map` and `/agent/roster`; `/agent/active` is not introduced.
- Hosting rent applies only to server mode; quote/confirmation, insufficient-balance rejection, no double charging, lease/renewal, failure refund and old-endpoint enforcement meet `v0-hosting-rent.md`. Local mode is unchanged and existing Agents incur no retrospective rent.
- Targeted tests, production builds, independent review, deployment script, and development smoke evidence are recorded against exact commits.
