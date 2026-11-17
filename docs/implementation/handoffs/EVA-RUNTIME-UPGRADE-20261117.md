# Eva Runtime upgrade / 扈三娘上线（2026-11-17）

## Scope and fixed source

- Task `EVA-RUNTIME-UPGRADE-20261117`; sole Owner `eva_runtime_upgrade_owner`.
- User authorization: upgrade agent-runtime on **eva-chc** and verify 扈三娘 online. No API/Web deployment, reenrollment, billing, business data migration, or unrelated cleanup.
- Existing workspace `/home/isp/wsps/cyf/runtime`, clean `develop`; fixed commit `c184e26bc88aab6e21bb62322117a1a9152c6a41`, tree `3822c091c91ad35d0b521e0f9ef178f36c85fdb0`; Runtime 1.3.118 / bridge 1.1.80. Do not track concurrent HEAD changes.
- RB-1: Runtime owns local execution, authentication file adaptation and host writer isolation; API owns user authorization and completion facts. Interface standard `/home/isp/wsps/cyf/api/docs/interface-standard.md` v1.4; no wire-contract change in this operation.
- Root workspace has unrelated preexisting modifications, preserved. No new worktree or source modification required.

## Discovery and verification

- eva-chc is `Eva`, aarch64, login/service user `chc`; fixed app `/home/chc/apps/cyf-agent-runtime-v1/app`, service `cyf-agent-runtime-v1@unified.service`.
- Actual old Runtime 1.3.108 / bridge 1.1.72, source `3ddc90d13c88813f967dd9d2c8f3b03b42b07aff`. Old historical release record says verified-active, but live unit failed since **2026-11-14 16:00:40 +08**, exit78/MainPID0. Do not treat historical receipt as live health.
- Four writer locks retain dead PID107266 and instance `c49b7c07-a975-47a4-98d2-fad767976f11`, matching host `chc-223-6c3ee548-aab2-48a1-8ce1-e47d40cdab54`. `/proc/107266` absent; no live target unit writer. Locks are intentionally not auto-stolen by Runtime; operator stopped-writer repair is required.
- Root filesystem initially189MiB available; use existing `/mnt/Workspace/Backups` (340GiB available) for verified stopped-state/config backup. No cache/history deletion.
- Reuse original immutable SSH-worker build `native6-runtime-20261117-05`, worker203.32.84.239:1056tests,1045PASS,11SKIP,0FAIL; build+collection216.643seconds. Package `/home/isp/state/cyf-build/n6r05/package/runtime-code-1.3.118.tgz`, SHA256 `53c976cffc8ef4a625d67c46d4ed3abb949261ff551562a26fbca876131f448f`. Original evidence retained; no rebuild or fabricated Flow run.
- New portable bytes/modes and ARM64 donor dependency graph verified; only bridge package identity version differs. Existing Node22.22.0, Python/toolchain and native sandbox image pass target closure check. Candidate stage24.262seconds is target installation preparation, not a new source build.
- Adapt existing Eva prepare/install transaction from Runtime108 release; original release lock, source/artifact pin, predecessor manifest/CAS, target dependency validation, stopped-writer checks, fixed app rename, backup and forward-only recovery retained.
- New version requires shipped offline model-auth migration (5files planned). Preserve original static auth.json credential; migrate only template/target/config representation via shipped CAS tool, with private backup. Do not copy global platform credentials or re-enroll.
- First preparation failed safely before staging due old manifest parser expecting object versus actual list; retained `stage-result.attempt01.json`, corrected parser for actual versioned manifest. No production mutation in preparation.

## Evidence and next action

- Controller evidence `/home/isp/state/cyf-eva-upgrade-20261117/`; private target evidence `/home/chc/state/cyf-local-build/eva-upgrade-20261117/`.
- Read instructions and existing orchestration tools first; obsolete shared skill Flow-only defaults overridden by root2026-11-16 policy.
- Installation, authenticated presence and two-round private chat completed; exact final evidence below. No global119 regression claim.


## Final completion (2026-11-17 10:13 +08)

- **PASS**: Eva fixed app Runtime1.3.118 / bridge1.1.80, source c184e26 / tree3822c091. Service active/enabled, PID288485, NRestarts0; one exact target connected/registered/ready, current health fresh. Target dependency/portable bytes/modes/validator pass; original host config, static profile, manifest and static auth credential unchanged. Shipped file-auth migration changed5files, subsequent plan0 (idempotent); no global platform credential copied.
- Controlled installation75.659seconds (not build). Original app retained at `/home/chc/baks/cyf-agent-runtime-v1/20261117-eva-runtime118/old-program`; original release records/config and4exact dead writer locks preserved. Verified stopped-state/config archive `/mnt/Workspace/Backups/cyf-eva-runtime118-20261117/stopped-state-config.tar.gz`, SHA256 `88aedfa316176f7e1d04feedce6b3b999f26c95d5a4f53fdaa5fd94945b048ea`. Forward-only; do not restore historical state over new business facts.
- Real private smoke exposed **missing public gateway protocol6 routes**: `/internal/agent/executions/commands` returned444 while WS was online. Updated only the two bounded new route/method blocks in the existing nginx snippet, preserving all other bytes and original session/installation/owner authorization. Original config backed up `/home/isp/baks/cyf-eva-runtime118-gateway-20261117/`; nginx `-t` PASS, graceful reload (no API/Web source build or service restart). Source counterpart/test and existing orchestration guide updated. Six narrow routing tests PASS; public no-auth GETcommands/POSTlease401, wrong-method POSTcommands405; actual authenticated commands/lease/inputs/result-commit/usage200. No blanket internal proxy.
- First obsolete smoke body omitted mandatory `materialRefs`, rejected400 **before admission**, retained original rejection. Corrected body with a new request key accepted200; its SSE timed out while gateway route was missing. Did **not repost**, cancel or replace the admitted request. After gateway repair, original request read back `RESULT_COMMITTED` / `FINAL_PERSISTED`, final2302587, exact expected answer matched.
- Second turn in the same conversation1760458009640: request `runtime-smoke-682ccbf3872c482b840b9e1e2672ab2d`, final2302645, exact expected answer matched, `RESULT_COMMITTED` / `FINAL_PERSISTED`; real SSE `chat.stream.completed`. No task/file/paid skill creation for smoke. Normal model invocation usage is not represented as a zero-cost guarantee.
- Authenticated agent GET reports **online**. Existing lease `hrl_transition_1ed745ba-4a69-3444-bd6a-a11c804c4109`, version1,50WEN/2592000seconds, exact paidFrom1794556917380/paidThrough1797148917380 unchanged; no reenrollment, lease mutation, reserve/capture/refund or renewal operation. Runtime original registration identity retained.
- Final target `/home/chc/state/cyf-local-build/eva-upgrade-20261117/completion-summary.json`; controller copy `/home/isp/state/cyf-eva-upgrade-20261117/completion-summary.json`. Installation record updated under original release lock to verified-active with separate two-round business acceptance reference. Original build/source evidence stays native6-runtime-20261117-05, not relabeled as a new build.
- No Runtime/API/Web source changes, no cleanup of other tasks/cache, no global119/file/image/billing acceptance claim. Runtime self-host reboot-lock automation is not changed; this was explicit stopped-writer repair, not automatic stale-lock takeover.
- Final documentation/navigation check `./sddw check-docs --all-docs` **FAIL on one preexisting unrelated link**: `specs/juyiting-ui-baseline-20261006/optimization/acceptance.md` points to `../../../../docs/implementation/handoffs/NATIVE-PROTOCOL-SINGLE-TRACK-20261116.md`. Not changed in this scope. Scanned39features/186Markdown/1201local targets; no unreachable default documents. Export omissions and2unverified references remain explicitly reported, not upgraded to source/online validation. `git diff --check` PASS. Installed nginx snippet and committed-source candidate SHA256 both `e507afca78fa35e5e4d5608edd5f4103a2792648802cde4dfd3ea17167f0ba0c`.

## 同日追加：chcbz.net

用户随后授权升级 `isp@chcbz.net`；该主机是 `li159-118`，不是控制机或 Eva。其 Runtime1.3.102 已升级到同一固定1.3.118候选，李逵实时通道及真实私聊验收通过；独立安装失败与恢复、状态备份、证据及磁盘余量见[目标升级记录](CHCBZ-RUNTIME-UPGRADE-20261117.md)。本条不改变上文 Eva 的来源、备份和验收事实。
