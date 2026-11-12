# Public demo aligned with the workbench — 2026-11-12

Owner: current task. Scope: public demo, landing-page wording, navigation label alignment, prototype, targeted tests and product documentation. No API/Runtime contract changes, no production data or paid calls. Deployment is separate from source completion.

Base: root 9d9cfc25d19e3bc7a090f500f4abe20b8423df1a; Web f5f7114ac9083be14e97538ea775fb46a0af957c; existing develop checkouts, initially clean.

Observed source mismatch: GuestDemo presents three fictional workers in four explanatory cards; JuyiHall uses 办事/事项/资料/我的 navigation, explicit assignee confirmation, discussion and deliverable acceptance. Public guest flow must remain local and clearly synthetic. Reuse pure presentation and navigation definitions, not network-owning business panels or the authenticated hall.

Prototype: web/prototypes/juyiting/index.html?guestDemo=1#home, existing unique prototype; preserve normal prototype behavior without the guestDemo query. Target: warm-white workbench, selected single assignee, synthetic Wen quote/reservation, conversation, deliverable and explicit acceptance; compact bottom navigation on mobile. Unsupported authenticated features point to sign-in, never pretend to execute.

Acceptance: three template paths; empty demand guard; no automatic acceptance; cancel/restart clears synthetic reservations; tabs preserve in-memory work; refresh resets; no business requests/storage writes; safe native-context handoff; desktop/mobile overflow and keyboard focus; actual hall navigation unchanged. Tests/build/remote/installation results recorded separately below.

## Implementation and diagnostics

The public page reuses BountyActionIcon, BountyTypedOutcomeCard and HallMinePage; demo navigation is checked against the actual hall navigation in a targeted contract test. The authenticated JuyiHall remains unchanged. No API/Runtime changes. Templates retain their stable IDs. No timers, mock backend, account persistence or paid model calls. Explicit confirmation reserves the selected synthetic quote; cancellation releases it; acceptance settles it. Unsupported features explain the sign-in boundary.

Public defaults and live archive components were missing from the open-source export. Clean-build attempt 1 failed in 31.174 seconds because app-title reads the missing `.env`. Attempt 2 passed 63 baseline tests (2 optional Mini Program cases pending), then failed in 28.533 seconds because LibraryPanel imports missing ArchiveReader. Both failures are retained, not relabeled. Added only public title/UI defaults (no private hosts, identities or secrets), and restored ArchiveReader/ArchivePositions from the exact pre-export Web source 60ddd8acfa75bb07db2d7b362072fb398c4f5e77. Reviewed restored components for embedded secrets/host paths; neither contains these. Added their existing targeted tests to attempt 3. No archived operations data was restored.

## Verification evidence

Private evidence root: `/home/isp/state/cyf-local-build/tasks/juyiai-demo-workbench-20261112/` (not bundled into the public repository).

- Prototype desktop/mobile checks preceded product changes; `prototype-desktop.png` and `prototype-mobile.png`.
- Initial targeted tests: 27 passed, 2 optional Mini Program cases pending. Onboarding suite: 25 passed. ESLint: no errors; existing Browserslist advisory only.
- Browser regression: desktop 1440×1000 and mobile 390×844; all three templates, explicit acceptance, cancellation, reset, navigation, safe sign-in context, no overflow or page errors, zero business calls. See `browser-regression.json` and script. These initial checks used the local Vite candidate, not deployed production.
- Product screenshots and PWA screenshots are local-candidate captures, explicitly labeled in README/guide; `screenshot-source.json` records source. No real user data.
- Scoped Markdown path validation: 40 local references checked, none missing (`docs-links.json`). The full document-map checker remains unavailable because the open-source export omits its map; this is not a full-library pass.

Attempt 3 exposed an integration-test loader dependency on the authenticated hall’s inline navigation array. Rather than changing many unrelated test harnesses for a demo-only task, the navigation extraction from JuyiHall was reverted. The demo keeps its small presentation constant and a targeted equality check against actual hall labels, panels and icons. This avoids changing authenticated business setup or unrelated mocks. Attempt 3 remains recorded as failed (172 passed, 1 failed, 2 pending); attempt 4 re-runs all selected tests.

## Final candidate

- Web 1.16.135 commit `6f31c4251eb67c04ab01a0986e20c50f159b4bbf`, tree `c68936103e1bb285e298a57f90a41f3173586007`. GitHub main/develop verified equal to this commit; temporary publication key revoked and read back.
- Clean local build `JUYIAI-DEMO-20261112-R4`: **BUILT**, 91.909 seconds (under 600). Selected tests: **173 passed, 2 optional Mini Program pending**. Vite build and package integrity checks passed. Existing large-chunk/Browserslist warnings remain; no claim of a full-suite pass.
- Package SHA-256 `c6f93d638179ee9a7e07ce61fcc4c2283df14ff94a612846d749517219947371`. Retained at the private evidence root `package/web.tgz`; original producer result unchanged, relocation recorded in `artifact-location.json`.
- Repeated desktop/mobile browser regression against the **extracted production package**, not Vite: all three templates, acceptance/cancel/reset, tabs, overflow, safe handoff and zero business calls passed; no page errors. Evidence: `production-browser/browser-regression.json`.
- Task preview processes stopped; task-owned clean clone and extracted preview removed, tests/logs/screenshots/manifest retained. Shared dependencies and other tasks untouched.
- **Not installed or deployed.** No online product URL/redirect changes, API migration, Runtime update or actual financial operation. README and product guide distinguish the locally verified new demo from the deployed site.
