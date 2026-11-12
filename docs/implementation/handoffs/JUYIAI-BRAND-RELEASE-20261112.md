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

## Earlier result — deployment pending (attempts 1–4)

Web source b35cdbd734583276a8bc5462125ffa8ac6a7a3a0 is committed and GitHub main/develop verified. Publication key revoked. Candidate version 1.16.136. No production frontend writes occurred; current Web record/index digests still equal the pinned predecessor (`production-unchanged.json`).

Attempt 2: tests passed 261 / pending 2, Vite compiled successfully; original 600-second timer stopped the builder at 599.907 seconds during packaging. Result is STOPPED_BEFORE_COMPLETION, not a releasable artifact. Launcher itself ended with signal 15 while its original timeout-owned builder continued; this was not relabeled as a new attempt. Partial package must not be deployed.

After read-only waiting for the observed competing Runtime packaging process to finish, attempt 3 reused the exact clean source in a fresh output and retained the original 600-second rule. It failed before compilation: 260 passed / 1 failed / 2 pending; Vite config-loading test exceeded its existing 10000ms timeout. Meanwhile a separate Runtime installation was active. Dependency verification took 149.893 seconds versus 19.032 seconds in attempt 2. This supports resource contention as a likely cause, not proof of a code defect; no test timeout or production resource policy was weakened. No further blind same-input retries. Failed logs/results are preserved separately.

The original LOCAL installer watcher exited on the failed build and performed no installation. No deploy descriptor was consumed, no backup/cutover ran. User has been asked whether this one frontend release may exceed the single-attempt 10-minute limit; next execution also needs the concurrent host work to settle. Code changes and the previously verified demo remain available in GitHub; online still uses the original Web version. No claims of online brand acceptance or full-suite success.


## Authorized continuation — 2026-11-12

User renewed Web deployment authorization after the timing diagnosis; no extension of the 600-second attempt limit was granted. Recheck confirms production predecessor record/index and private environment remain unchanged. Runtime build/install has ended, but tutorial video encoding and the scheduled host cleanup are active; wait for materially reduced load before the next attempt, without stopping other owners' processes. Waiting is recorded separately from the build/install attempt.

Prepared attempt R4 reuses the same clean Web commit and selectors, preserves production configuration, and uses the original builder/installer. Corrected the unused task-local install wrapper: standalone local_web_build.py unconditionally leaves `publishable=false` because it does not install; existing local_release.py authorizes installation by BUILT/source/manifest/test/artifact verification instead. R4 follows those checks, adds exact candidate equality, and does not alter any producer result or production installer. This correction is not a relaxation of failed-test or partial-package restrictions.


Attempt R4 outcome: STOPPED_BEFORE_COMPLETION at 600.915 seconds (timeout launcher exit 124; scheduler delivery slightly beyond 600). Dependency reuse verification alone took 394.939 seconds; selected unit tests started but did not complete, so no build/package/install occurred. Runtime and scheduled cleanup were absent when this attempt started, but multiple tutorial video encoders/browser contexts remained and host CPU contention persisted. Read-only process samples showed only 20 builder CPU seconds over 309 wall seconds before tests. Temporarily adjusted only the owned R4 builder to nice -5, inherited by its children, without resetting the deadline or changing any production/other-owner process. All R4 build/test processes have exited. No further retry while the competing recording workload remains.

Production recheck (`production-unchanged-r4.json`) confirms record and index digests exactly match predecessor; online remains Web1.16.134 at c453e0898642b0aec80677df71c088f74563a349. No final artifact exists for retention registration, no failed artifact was installed, and public README/screenshots remain labeled as local candidates. Next attempt requires the recording workload to finish or explicit authorization to coordinate its pause; increasing the deadline is not treated as the default fix. Private timing/resource evidence remains in the existing task directory.


## Current result — deployed and publicly verified, 2026-11-12

User renewed deployment authorization. Before R5, tutorial ffmpeg encoders had ended; no competing Runtime builder or cleanup was observed, and vmstat sampled 88–91% CPU idle. Production predecessor and private configuration digests still matched. No task was interrupted, no timeout was raised, and no priority adjustment was used for R5.

R5 pins Web b35cdbd734583276a8bc5462125ffa8ac6a7a3a0 / tree 149869c64ff740b3443c55344c7887af01de0b33 / 1.16.136. Dependencies reused (24.052s); selected unit tests 261 passed / 2 optional pending (38.082s); build 49.333s (Vite 45.83s); packaging 18.105s; archive integrity 2.988s. Builder total 156.239s including metadata and post-build dependency verification. Original controlled installer completed in 22.634s, changing 38 files, checking 613 installed files and 256 online files. Combined build/install 180.089s, within the original 600s cap. Artifact SHA-256: 96a46c6acc31072c474ad64c4710e3db81f5fded2deaf47018b0d58e968709d5. Logs, source-bound test report, manifest, artifact relocation and installation receipt remain in the existing private evidence directory; prior failed attempts retain their original outcomes.

Installed record is online_verified and exact source/artifact matches. Restore uses the existing controlled installer and predecessor backup /var/lib/cyf-web-flow/backups/d3184e555ba244e4f7a81c24f0744a887e2654784edf26dd2af39e08795d49a3. API and Runtime were not deployed. Shared working Web HEAD has since advanced for another task; this release deliberately installs only the pinned brand/demo candidate, and does not reset those commits or the root gitlink.

Public-browser regression: desktop 1440 and mobile 390; all three templates, discussion, explicit acceptance, cancellation, refresh/reset, navigation, no horizontal overflow, no page errors and no business/model requests passed. Initial browser attempt encountered the existing PWA first-controller reload during mobile setup; the runner was corrected to await that actual reload, preserving service-worker behavior rather than disabling it. No production code changed. Runtime browser title is 聚义 · AI 协作工作台; raw SEO title is separately source-exact. Public PWA names use 聚义. Screenshot recapture uses fresh signed-out online contexts, without real tasks or charges; README/product guide now describe the deployed version. This is scoped brand/demo acceptance, not full signed-in business regression.
