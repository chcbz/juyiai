# JuyiAI visible brand and Web release — 2026-11-12

Owner: current task. User explicitly authorizes renaming visible frontend “聚义厅” to “聚义” and deploying the frontend, including the previously completed new public demo. No API/Runtime deployment, private session changes, charges or database migration.

Base: root eb3942f157405166c5de260c4e2565f7c2c362ff; Web 6f31c4251eb67c04ab01a0986e20c50f159b4bbf; existing develop. Unrelated Runtime modifications and JUYITING-TUTORIAL-UNBLOCK handoff belong to another task and are untouched.

Prototype first: existing web/prototypes/juyiting/index.html and active scripts updated; historical shared snapshots preserved. Desktop 1440 and mobile 390 previews checked before product edits, screenshots in private evidence root /home/isp/state/cyf-local-build/tasks/juyiai-brand-release-20261112/.

Scope: visible Vue/JS/i18n labels, browser/product/share metadata, manifest app name and cache-reset page. Matching test fixtures/expectations updated. Keep juyiting paths, internal identifiers, persistence keys and interfaces unchanged. Candidate Web1.16.136.

Release: preserve current production frontend endpoint/OAuth-public-client/UI configuration from exact installed source (c453e0898642b0aec80677df71c088f74563a349); only title changes. Private build inputs stay outside Git with source/digest evidence. Original LOCAL installer provides lock, predecessor digest check, changed-file backup, assets-first/index-last install and automatic restoration on failure. Root/API/Runtime are not installed.

Tests, exact source, artifact, deployment and online acceptance are recorded separately below after execution.

## Diagnostics and regression

Attempt 1: failed in 88.36 seconds, 260 passing / 1 failing / 2 optional pending. Failure was a stale recruit fixture expecting local mode to emit direct bind-persona. Current source already routes both hosting modes through HostingRentPanel; corrected only its stub/expectation, asserting requestedMode=local, no premature binding and confirmed receipt propagation. Production recruitment behavior unchanged.

Sharing cover was a raster screenshot with the old brand; replaced it with a fresh 1200×630 browser capture of the current landing page, not a generated illustration. Historical filenames remain stable. Prototype snapshot archives and non-UTF8 game config comments left untouched.

Diagnostic preview initially used the wrong CLI argument, then created its own Vite cache in the installed dependency set. The preview was stopped; only that newly created cache was moved to the task directory, the original full dependency inventory was reverified, and subsequent preview used task-local cacheDir with the correct working directory. No unrelated caches changed. All such diagnostics are separate from the release attempt.

Attempt 2: selected tests 261 passed, 2 optional Mini Program pending. Existing test harness Vue stub/TMX warnings are not production-browser results. Build/install/online results follow below.

## Current result — deployment pending

Web source b35cdbd734583276a8bc5462125ffa8ac6a7a3a0 is committed and GitHub main/develop verified. Publication key revoked. Candidate version 1.16.136. No production frontend writes occurred; current Web record/index digests still equal the pinned predecessor (`production-unchanged.json`).

Attempt 2: tests passed 261 / pending 2, Vite compiled successfully; original 600-second timer stopped the builder at 599.907 seconds during packaging. Result is STOPPED_BEFORE_COMPLETION, not a releasable artifact. Launcher itself ended with signal 15 while its original timeout-owned builder continued; this was not relabeled as a new attempt. Partial package must not be deployed.

After read-only waiting for the observed competing Runtime packaging process to finish, attempt 3 reused the exact clean source in a fresh output and retained the original 600-second rule. It failed before compilation: 260 passed / 1 failed / 2 pending; Vite config-loading test exceeded its existing 10000ms timeout. Meanwhile a separate Runtime installation was active. Dependency verification took 149.893 seconds versus 19.032 seconds in attempt 2. This supports resource contention as a likely cause, not proof of a code defect; no test timeout or production resource policy was weakened. No further blind same-input retries. Failed logs/results are preserved separately.

The original LOCAL installer watcher exited on the failed build and performed no installation. No deploy descriptor was consumed, no backup/cutover ran. User has been asked whether this one frontend release may exceed the single-attempt 10-minute limit; next execution also needs the concurrent host work to settle. Code changes and the previously verified demo remain available in GitHub; online still uses the original Web version. No claims of online brand acceptance or full-suite success.
