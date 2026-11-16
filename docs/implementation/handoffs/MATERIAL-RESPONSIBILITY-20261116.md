# MATERIAL-RESPONSIBILITY-20261116

## Owner / scope / fixed input
- Owner: current chat `material_boundary_owner` / developer. User: trace whether image capability validation was restored, audit and remove redundant/out-of-responsibility checks in the material/discussion execution chain. Implementation and verification authorized; no production restart/deployment/data rewrite authorized.
- Reuse `/home/isp/wsps/cyf/api`, branch develop, clean base `d6f03755ac524b7604495ed162943a5b30ec580f`, tree `2a24067cf6d9161ee1b9a347132928392d54b3e8`. Web and other root task changes are not owned by this task. Runtime scope subsequently extended only to selected-carrier validation, from clean develop base 4fd0951fec5d5a89c05985b96465169ff7e39e39; existing release of that base is not modified.
- Rules read: root/API AGENTS; docs entry, KB entry, global regression; RB-1 and API interface standard v1.4 (no wire/schema migration planned). Build follows current root 2026-11-16 SSH worker policy, not obsolete shared skill Flow defaults.
- Scope: attachment candidate projection, authenticated discussion readiness, bootstrap failure isolation, and actual input/skill/output consumers. No blanket removal of authorization, lease/fence, hashes, schema parsing, real adapter restrictions or frozen execution contracts; no old INSPECT/legacy execution reactivation.

## History (verified local Git history)
- `29bd0b302a2fef33b4a573c2b16d90e61354f0c9` 2026-10-22 added image-only admission rejection to avoid silent omission.
- `0ab9e72a54d1710be4c25c2a49988f354802f53c` 2026-10-31 removed file storage/transfer/native format gates but did not modify ChatMaterialsInputContract.
- `5b96cd8d6ed0127e130c569b31b133d129e57a65` 2026-11-04 added measured LOCAL_FILE wildcard transport and retained image rejection.
- `6e57eead938` 2026-11-12 sanitized import retained the method. Not evidence of a newly reintroduced guard after removal: confirmed missed cleanup, not a recent re-add.
- `66a83160d9457c92e7e50231d599a475495b314e` 2026-11-15 added assignment preflight via native readiness. Keep authenticated live discussion readiness before reservation; remove dependency of ordinary discussion on file-generation output formats.

## Responsibility audit / implementation decisions
| Check | Decision and responsibility |
|---|---|
| API image MIME not in native input declaration => INVALID_REQUEST | Remove semantic rejection. Carrier selection remains optional transport projection; full authorized source catalog remains in typed context and native action selection. No fabricated file carrier/read receipt. |
| API silently treats projected native inputs as all materials | Verify full catalog remains for unmatched image/audio/custom inputs; model may choose authorized native execution or explain limits. No prewritten content or omission of source identities. |
| Ordinary discussion requires non-empty nativeExecution.outputMimeTypes | Remove from readiness/assignment/admission; READY authenticated discussion may answer without file execution. Actual native script capability still needs its authenticated declaration and task authorization. |
| API读取原回合资料时重新要求今日载体能力与原声明一致 | 删除能力重准入；原持久化profile+权威目录复核manifest，HTTP身份fence与当前任务/资料ACL仍保留。 |
| materials declaration exact top-level/item key equality | Accept harmless additional metadata and project only known fields. Preserve actual schema version, carrier semantic, MIME syntax, digest and duplicate protections. |
| Task INVALID_REQUEST/INVALID_ROUTE interpreted as shared worker failure | Reconcile only the immutable intent through existing TERMINAL_FAILURE/DEAD and continue; verify durable terminal acknowledgment. Infrastructure/unknown/integrity failures remain fail-closed, not blindly retried as success. |
| Source ACL/version/hash; live runtime identity; task grant/lease; source selection membership | Keep at actual responsibility boundaries. Catalogue visibility is not permission for model to select another task's source. |
| Runtime adapter MIME/decoder/receipt checks | Keep at concrete carrier boundary; generic native file execution already carries all selected authorized bytes, independent of native preview adapters. |
| Fixed skill schema/input/output constraints | Keep for explicitly selected executable package contract, not as a prerequisite for ordinary chat. Instruction-only packages do not gain legacy manifest gates. |
| Web JPEG/PNG reference filter | Bound to legacy image-specific point-and-start contract, not ordinary point-and-deliberate/material upload. Do not change an unrelated lane or reactivate retired endpoints. |
| Runtime output format checks | Validate selected execution output contract and actual bytes before stage/commit, not comprehension of an input. Retain scoped checks; no speculative all-project deletion. |

## Acceptance / earliest verification
- Unmatched JPEG/PNG/MP3/custom files do not reject admission; exact/native and wildcard carriers still use matching hash/MIME; full source catalog survives and is selectable by native execution.
- Discussion READY without output formats may answer; missing/disconnected/ambiguous/foreign bindings remain rejected; no invented native execution capability.
- Two invalid task intents do not stop a following valid intent; DEAD acknowledgment verified; infrastructure/lease/reconcile failures preserve protection and uncertainty.
- Actual affected Java tests plus default auth/artifact/POI baseline, layering, fresh JAR via existing orchestration. Source/test/build/deployment/online results recorded separately.
- Evidence: `/home/isp/state/cyf-material-boundaries-20261116/`; original incident evidence stays `/home/isp/state/cyf-meeting-audio-20261116/task689-diagnosis/`.

## Status
Source changes and scoped verification completed. Not deployed; no production recovery or task689 completion claimed.

### Source discovery update
- Origin fetch on 2026-11-16 failed with Empty reply from server; local origin/develop remains `377132f786c6a38b1cb9d2cb90bda7dc3a96ff0b`, not asserted latest. Build uses fixed local baseline matching incident deployment.
- Additional confirmed issue: material read/final rebuilt the old manifest from today's live advertised MIME catalogue, conflating capability refresh with authorization revocation. Changed to persisted profile reconstruction; current HTTP identity, dispatch, task state, source ACL and digest verification stay intact.
- Verified old INSPECT POST returns `RetiredSkillWriteEndpoint.response()` and native runtime rejects independent INSPECT. Its historical parsing/adapter contract is not reactivated or used to reject current CHAT.

## Final source / verification (2026-11-16)
- API develop commit `bb4f89b7956abf0271376f957f448298101388ef`, tree `c8728cdd0da52b88c4b68673804960853f33b356`, version 1.1.57-SNAPSHOT.
- Runtime develop commit `4d7637771bf5a78c39eff9dbc115d83ef58b796b`, tree `f51cce515c650468047394af733398987cbec6de`, bridge 1.1.77 / runtime 1.3.115. Only carriers selected in manifest.sources are checked against measured adapters; an unused advertised format disappearing no longer blocks this turn. Selected carrier/digest changes still reject before fetching/model invocation.
- API worker batch `material-boundary-20261116-01`: 179 tests, zero failure/error/skip; validateLayering and fresh bootJar/package succeeded. Fixed controller `20630af9f618f71e01d2cf21b0bfc69d14c8dcb5`. Build+transfer 98.875s (source preparation separately 16.174s); under 300s target and 600s limit. Full command/fixtures/toolchain in inputs.json/result.json; no Flow or installation.
- API package SHA-256 `1c7c1fc8e3534e1b6839aef141454bf2d490d1ae1f0c64e2f6d731d9c77852c8`; JAR `8002f4b9f01c2297a332984335da79ec73b162a5d67684f12b7c2aa838f77a13`.
- Runtime committed-source Node tests: 47 total, 46 passed, 1 existing optional installed-document-toolchain test skipped, zero failures. Selectors: materials-chat.test.mjs, image-input.test.mjs, typed-inspection-input-carriers.test.mjs. Node from existing runtime app, ordinary-disk task TMPDIR, mock/fixture tests without paid model execution. Initial run failed because isolated image test omitted manifest.sources; corrected fixture to include actual source, retained initial failure log, added selected-digest-negative test, then reran successfully. No production code fallback for malformed fixtures.
- Evidence saved outside reclaimable package at `/home/isp/state/cyf-material-boundaries-20261116/`: api-evidence (XML/inputs/result/Gradle log), api-test-summary.json, verify-01.log, runtime-tests.log (initial failure), runtime-tests-02.log and runtime-tests-committed.log (successful fixed-source verification).
- Audit scope is material admission/read/final, discussion readiness, bootstrap isolation and related Runtime carriers/skill/output consumers—not a claim that every validation in the entire repository was audited. Security ACL, binding, hashes, immutable contracts and actual sandbox/decoder boundaries remain.
- Source-only closure: local component develop commits, no remote-push success asserted, no deployment/restart/production writes. Original meeting-audio task remains unverified pending separately authorized installation and business acceptance.
