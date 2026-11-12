# JuyiAI GitHub source migration — 2026-11-12

## Scope

The root integration repository and API/Web/Runtime snapshots start from each GitHub repository's original MIT-license initialization commit. Old repository history is not merged or uploaded. Private operational receipts, user/session data, certificate containers and secrets are excluded. Original source/history remains outside these public branches.

Runtime includes its engine, required runtime payload descriptor, skills, installation wrappers and current tests; unrelated shared installers are not included. The historical fixed-source installer acceptance harness and its nine dedicated tests remain in the original repository. The current dependency-pinning assertion and PPTX predicate regression are retained without requiring the private old commit.

## Source pins

- api: commit `6e57eead938c6cb1c5d26736b53a82999ac30ca0`, tree `c94ab5ee666abd1ff35ffbbfd086bd3319f7c746`.
- web: commit `f5f7114ac9083be14e97538ea775fb46a0af957c`, tree `1278209edb9313a8e1e12fd06b22e9e8e598ee08`.
- runtime: commit `fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63`, tree `d220e1fdc63d8d8518b4ff5d261f38cb2531cbcd`.

## Verification

- Gitleaks 8.30.1 directory scan: 52 findings manually reviewed as SHA references, synthetic fixtures, idempotency/cache IDs or variable names; no unreviewed findings at snapshot preparation. This is not a claim that automated scanning proves all content safe.
- Runtime current Node suite: 354 passed, one existing cross-end integration test explicitly skipped. The first broad run exposed a missing payload descriptor and overlong Unix-socket temporary path; both corrected before the final run.
- Runtime standalone entry and enrollment tests: 17 passed. The old shared dispatcher normalized failure status; standalone entry correctly preserves the child exit status.
- Runtime Python utility suite: 29 passed, one skipped.
- Web local TLS configuration: one passed; self-host onboarding: seven passed.
- Sanitized test JSON/XML: 13 parsed successfully; new root task ledger validated.
- API full compilation, full application regression, production packaging and deployment were NOT performed by this migration. Public clean-machine dependency availability remains a separate task.

## Operational boundary

No production installation directory, database, service, account, wallet or runtime identity is changed. Source remote migration does not migrate cloud pipeline settings or authorize automatic deployment. Legacy technical names and installation paths remain contractual identifiers.

## Security correction

A supplementary review found a potentially sensitive literal in an old API encryption test that automated scanning missed. The test now uses synthetic round-trip data; this migration’s public API snapshot and root component reference were rewritten. Remote branch verification does not establish removal from GitHub caches or revoke a credential. The owner must revoke/rotate the old credential if still active; its validity was not tested.

Local workspace verification found a test-only `node_modules` symlink accidentally tracked in Web; it is removed and both directory and symlink forms are ignored. Existing workspace dependencies are retained, not overwritten.
