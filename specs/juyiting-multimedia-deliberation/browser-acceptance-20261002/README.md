# Juyi multimedia real-platform browser acceptance — prepared 2026-10-02

**Status: `PREPARED_NOT_EXECUTED`.** This is an Owner-run execution harness and matrix, not a mock test and not product acceptance evidence. All **AC01–AC22 + FD01–FD12 remain `NOT_RUN`** until a deployed platform session produces the listed browser, event, ID, screenshot, and artifact evidence.

## Scope and source binding

The source-derived selector catalog is pinned to Web commit `7aaca8916bc2cad2d053328af0780913fff64bca`, tree `71c0536a8b3eeb9cbc7db9028b92ccfc05cd127c`. The future deployed build must prove all three flags effective:

- `VITE_JUYITING_MULTIMEDIA_DELIBERATION_V2_UI=true`
- `VITE_JUYITING_TYPED_DELIBERATION_UI=true`
- `VITE_JUYITING_FOLLOWUP_EXECUTE_V3_UI=true`

The harness deliberately reuses the existing Web CDP mechanics by runtime injection (`JYT_CDP_HARNESS_MODULE`, normally the Web checkout’s `scripts/juyiting/e13/lib/cdp-harness.mjs`). It adds **no** Playwright/Puppeteer dependency and contains no Chromium launcher, process spawn, Vite startup, model call, Flow action, deployment, or service control.

## Required future run inputs

All inputs are supplied at runtime and are never written here:

```bash
export JYT_BROWSER_ACCEPTANCE_ALLOW_LIVE=1
export JYT_BROWSER_CDP_URL='http://127.0.0.1:OPERATOR_OWNED_CDP_PORT'
export JYT_CDP_HARNESS_MODULE='/absolute/path/to/web/scripts/juyiting/e13/lib/cdp-harness.mjs'
export JYT_ACCEPTANCE_BASE_URL='https://deployed-host'
export JYT_ACCEPTANCE_METADATA_JSON='/secure/operator/run-metadata.json'
export JYT_ACCEPTANCE_ACTIONS_JSON='/secure/operator/actions.json'
export JYT_ACCEPTANCE_EVIDENCE_DIR='/secure/operator/evidence/juyiting-browser-acceptance-YYYYMMDD'
```

`run-metadata.json` must contain `deployedCommit`, `deployedTree`, `flowRun`, `artifactSha256`, `identityLabel`, `effectiveUiFlags` (all three exact required strings), and the deployed base URL. The prepared harness refuses a source pin or UI-flag mismatch rather than attributing another deployment to this candidate. Credentials are supplied only through a pre-authenticated operator-owned browser profile or secure runtime injection outside this repository; do not print, save, or add them to the action JSON.

The browser must already be running and owned by the operator. The harness **attaches only**; it neither starts nor closes that browser. It closes only its own CDP socket. Existing CDP transport timeouts remain transport error reporting, not a product performance gate; the harness never cancels a model/task because an observation window elapsed.

## Offline self-check / future execution

```bash
node specs/juyiting-multimedia-deliberation/browser-acceptance-20261002/offline-selfcheck.mjs
node specs/juyiting-multimedia-deliberation/browser-acceptance-20261002/run-browser-acceptance.mjs --plan
node specs/juyiting-multimedia-deliberation/browser-acceptance-20261002/run-browser-acceptance.mjs --execute --primary
```

The first two commands neither connect to CDP nor start a browser. The last command is rejected unless both `--execute` and `JYT_BROWSER_ACCEPTANCE_ALLOW_LIVE=1` are present. Each mutation is preceded by an explicit `readyCheckpoint` (a concrete visible selector or text condition). A missing selector/condition is recorded and stops every later action; it never sleeps blindly or times out and continues. The operator may inspect the captured checkpoint and resume only from a safe, non-replaying action list. It runs only a declared primary slice and writes `PARTIAL_COMPLETED`; it intentionally leaves all 34 matrix statuses `NOT_RUN` until the Owner correlates real evidence. `operator-actions.primary.example.json` is a non-runnable template: copy it outside Git and replace its explicit `OPERATOR_REPLACE_*` placeholders only after a real DOM discovery snapshot.

## Primary vertical journey (not a claim that all 34 pass)

1. Start with no reference material; enter **“画一只鸟”** and use an explicit target Agent assignment.
2. Record exactly one assignment/conversation/first request and observe automatic deliberation/direct execution under real authorization.
3. Require a real decoded image (`naturalWidth` and `naturalHeight` > 0), capture the preview screenshot, download through product UI, and compute SHA-256 over the actual downloaded bytes; compare any product/server digest.
4. In the same conversation request **“改成蓝色”** with the first actual asset as the input. Capture distinct execution/asset IDs and prove the original remains visible/unmodified.
5. Select only the new image plus intended text in finalization. Record selected output IDs, delivery ID/state, decision/acceptance fact, and actual task-completed state separately.
6. Run the image journey independently against both **server** and **local** target Agents for AC17. Different browser roots/profiles and distinct task/run evidence are mandatory; a shared process/profile is not a substitute.

The primary slice maps AC01/03/05/07/10/14/17 and FD02/07/08/10. It does **not** prove all 34 cases. Audio, reference-version, ACL, offline/recovery, concurrency, negative authorization, old-client, and other matrix cases retain their individual planned actions in `acceptance-plan.json`.

## Evidence / outcome discipline

The future run records sanitized URL paths, status/MIME events, screenshots, DOM discovery, browser-downloaded filename/byte count/SHA-256, and any actual IDs observable from legitimate browser responses. Authorization headers, cookies, token/password/signature-like values, and URL query strings are redacted; structured `url`/`src`/`href` evidence retains origin and path only. HTTP 200, a toast, an image URL, static demo, mock event, local generated file, or a model result outside the product does **not** make a case pass.

If prerequisites, deployed flags, capability, consent, provider, local/server separation, or selector discovery are absent, record the exact real state as `BLOCKED`/`NOT_RUN`; do not simulate success. A real product contradiction is `FAIL`. No arbitrary resource or performance threshold is introduced.

## 22:25 candidate rebind

The execution plan and selector catalog now target Web `7aaca891` / tree `71c0536`. Git comparison against the original c74 preparation proves only CI bootstrap and its test changed; UI selector source is byte-identical. `preparation-receipt.json` and earlier offline logs remain historical c74 evidence. Run152 checkout is confirmed, but test/build/deploy/artifact and all34 product cases are still unproven. The rebind is not a deployment claim.
