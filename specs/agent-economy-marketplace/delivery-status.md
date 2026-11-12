> 2026-11-08：内测文钱包固定报价闭环已上线并完成真实验收；当前范围及剩余计费证据边界见 `beta-wen-billing.md`。下文9月SILVER交付仅供历史取证。

# 银两交易、技能市场与托管租金 — 交付状态补充

## 2026-09-09 18:51 增量交付补充（优先于下方9月6日快照）

- V0经济实现已随API `97ae8ef12c0a0306a40a04017f44139e1ca27823` / tree `9ffcf29061c56eb8135f50c548a8373a0317155c` **实际部署**，包含已审已测6267全部差额与SSE修复。2026-09-09 18:23:21 COMMITTED；实际JAR SHA-256 `587a2ffd1d220cc60cee0cbd5a5163f26df68d490cd527189c922a71d9c688d6`，PID3910271，18:28交回监控。Main18:47独核实际制品/进程及25终态引用。
- 终态证据：`/var/tmp/cyf-jy-sse-runtime-prep-knuth-20260909-j0t31t3s/runtime-combined97ae8-final-receipt.json`，SHA-256 `baea77697f34ef77582440e13048305d89e3f7a65b234799e1d142f803e36a14`。单次通知邮件AUTH526失败另案处理，不能声称邮件送达，也不推翻部署成功。
- Web生产经济UI此前已发布；223981→e346仅两测试文件，生产制品无差额，不重复发布。客户端current关键四模块实际匹配isp-install a100a500，磁盘安装映射不代替真实技能安装/结果验收。
- 定向经济36方法真实PASS证据按原tree复用；W05/W06/W09/W11处于待业务验收，**整个功能不归档**。R01租金15+catalog4方法于18:48实际启动但尚无结论，R03隔离MySQL9初始化失败未闭环；原117PASS/32FAIL历史不得改写为新149PASS。
- 尚缺合法受控身份下的发银/钱包读回/报价显式认领/结算退款、六技能真实Agent安装ACK/结果与激活退款、完整租金业务等。未授权真实收费/生产DML，不把部署视为付费业务上线批准。生产完整SDD、PoP/Broker/KMS和后续范围未完成；`integration.yaml`及冻结合同/bundle保持不变。

## 2026-09-06 历史快照（下列未部署描述仅代表当时）

> 文档任务 SDD-ARCHIVE-20260906；截至 2026-09-06T09:21:00.295553+08:00。这是审计投影，不可用于 claim/调度。当前状态以唯一运行台账为准。

- 生命周期：`implementing_preview`。归档：未归档。
- 结论：V0 正在实施，W01/W02/W03/R00 已 accepted；余项依次处于实现、审查、验证或依赖/根因阻断。生产完整 SDD 与 V0 预览验收严格区分，未部署/未启用收费。
- 下一步：完成剩余 W04–W12 与 R01/R02，验收 R03/W13 后执行 W14 开发预览发布；原 9月8日目标不是交付承诺。

## 需求 / 设计同步

SILVER 独立于旧 point；整数 micro-silver、GROSS_INCLUSIVE、显式 Agent、托管/幂等/原子结算保留。租金仅 server，local 不收费；生产 PoP/Broker/KMS 等不能被 V0 验收替代。五份生产核心文档及 bundle.sha256、V0 合同均保持字节不变。

## 任务 / 验收映射

| 任务 | 截止时点记录 | commit / tree | 证据摘要与剩余动作（历史快照） |
| --- | --- | --- | --- |
| `ECO-V0-W01` | accepted | `未绑定` / `未绑定` | V0 preview contract frozen at specs/agent-economy-marketplace/v0-plan.md sha256=fafa497c307a48df94d81e00eb912053bc9ed58ca9fe66a11af78c3002a5d37f; frozen production bundle manifest remains c5c5a715d027c87e74617b07c0a2ee3cb33c9d71cd69db7f95b80775f74a735c. Proceed with W02. |
| `ECO-V0-W02` | accepted | `70ec1dfb1fb7` / `354f06b70be2` | Independent sol_reviewer 01a07051-2528-7c23-9a12-e64ea94365c6 ACCEPT P0/P1/P2=0/0/0 on 70ec1dfb/tree 354f06b7. No-DB 8ad6088f and MySQL c75ef1fc PASS; MySQL 11/0/0/0 including 100 requests; temporary users/databases zero. Promote W03 wallet/ledger/preview issuance implementation; no deployment yet. |
| `ECO-V0-W03` | accepted | `97df61a13616` / `1ec7d890b0dc` | W03 ACCEPT on97df61a1/tree1ec7d890: independent source0/0/0 plus34 tests PASS incl dev/grey/prod JWT chains; evidence538f3342. Unlock W04 and requested R01 paid rent. No deployment or live charging. |
| `ECO-V0-W04` | awaiting_verifier | `ea1eb579a532` / `fb32f4592b17` | R3 exactea1eb579/treefb32f459 independent sourceACCEPT0/0/0; prior source/provider exceptions resolved, historical matrices retained in W04 handoffs. Runtime gate pending. W05 owner now integrates corrected source parent in separate claim-r2 worktree; plan focused combined verification after its review, no duplicate full suite or deploy. |
| `ECO-V0-W05` | waiting_dependency | `fbee63956118` / `dcef936f4c8a` | OriginalW05owner nowW06 has expanded combinedsource scope for4fullreviewfindings in eco-v0-bounty-settlement; originalfbee6395 frozen/rejected. Await cleancombinedcandidate then separate W05/W06reviewpromotion. Preparedrun-w05-r2-nodb.shNOTGO; W09mustnotrepairsharedfunding concurrently. |
| `ECO-V0-W06` | implementing | `fbee63956118` / `dcef936f4c8a` | W06sourceowner continues isolatedsettlement plus4inheritedW05fullreview corrections perW05R3matrix, oneactivelease. Minimal sharedposting CAPTURE_COMPUTE/FEE/PAY_AGENT and partialcapture continuation ownedW06, coordinate W09primitive needs/paths. No runtime/source promotion; cleancombinedcandidate then independentreviews. |
| `ECO-V0-W07` | verifying | `d56e205c558f` / `0a6b87991f20` | Bounded d56e205c independentSOURCEACCEPT0/0/0 recorded; GO only run-w07-r3-lifecycle-nodb.sh six new mock lifecycle cases on exacttree0a6b8799. No MySQL GO: old wrapper unsafe, main preparing retention/session-zero cleanup gate. No repair/blindretry/processcontrol, preserve prior evidence scopes. |
| `ECO-V0-W08` | review | `086a9ddea30c` / `1426b81cccb0` | Independent W08 source review on086a9dde/tree1426b81c,14additive seed/package paths vs production-source-acceptedW07b4614bd. Exact6prices/admin/defaultoff/scope/deterministicZIP/digest/drift checks; noDB/runtime/seeding/repairs. Unblock W09 promotion source dependency without duplicate schema review. |
| `ECO-V0-W09` | claimed | `086a9ddea30c` / `1426b81cccb0` | Original rental critical owner handed offR01, now exclusive W09 source owner in NEW eco-v0-skill-purchase. Merge immutableR01aa81221b to preserve shared guards; implement exact-scope capabilities, durable Agent CAS, purchase/package/install-result/activation/refund with tests. Frozen W05 integration later; no runtime/DB/other-tree writes. |
| `ECO-V0-W10` | blocked_root_cause | `3b337d22ee4e` / `3302bf9f6bbb` | Stop second-failure loop; original installer owner bounded fixture mode correction and R01 managed-host staging integration in new tree after admission, independentreview then target retry. Reuse exact installer47PASS honestly. |
| `ECO-V0-W11` | waiting_dependency | `c6945cff137f` / `8a096b870bd5` | W11 source defects join W12-owned combined Web remediation packet WEB-R2 in new worktree; no second active lease for same Agent. Preserve original candidate. After combined clean corrected commit, independent review/test evidence promotes W11 and W12 separately; W12 owner includes minimal W11 integration paths. |
| `ECO-V0-W12` | source_review | `06875878bd21` / `b6f892934d96` | Clean R4 Web candidate06875878/treeb6f89293: explicit quote confirm/cancel and immutable claim receipt+canonical readback/retry fencing, static-only. Entire combined R2-R4 independent review and focused tests/build pending. Original combined worktree now immutable; no deployment. |
| `ECO-V0-W13` | blocked_dependency | `未绑定` / `未绑定` | Wait for accepted API/Web/Agent candidates plus requested hosting-rent R01/R02/R03 integration evidence, then run targeted combined verification and independent review. Rent scope is specs/agent-economy-marketplace/v0-hosting-rent.md; no automatic real charging before price/period configuration. |
| `ECO-V0-W14` | blocked_dependency | `未绑定` / `未绑定` | Wait for accepted candidates, then deploy development preview and smoke test. |
| `ECO-V0-R01` | source_review | `aa81221be06e` / `5d4d87fe8864` | R4 clean APIaa81221b/tree5d4d87fe and companion Agentaf40adbe/tree21aaef68 committed: concrete private readiness adapter and durable free reprovision. Full R3-R4 independent review/compile/runtime pending; packaging must add managed-host.mjs on integration. No sockets/services/rent activated. |
| `ECO-V0-R02` | source_review | `53e12c87c03b` / `9b4c58d40863` | Terra capacity recovered once; clean53e12c87 parentWebR406875878: explicit rent quote/confirmation, immutable receipts and canonical lease recovery, paid manual renewal/free reprovision, no server fallback. Static-only. Independent full corrected Web+rental review and focused tests/build pending; no deployment. |
| `ECO-V0-R03` | blocked_dependency | `未绑定` / `未绑定` | After R01/R02 accepted, run targeted rent API/MySQL/Web verification and independent review before combined W13/W14 preview delivery. |
| `ECO-V0-R00` | accepted | `6623e4c3eebb` / `9db6898cdf0f` | Admission-only R00 ACCEPT: independent source0/0/0 and88 tests PASS on6623e4c3/tree9db6898c; evidence d4e6ba49. Preserve local/no-charge behavior and closed server path. R01 full paid lease remains blocked on W03; no deployment. |

## 集成与未验证边界

未运行 `sddw pin`、未改变 root gitlinks 或本地 checkout。候选 SHA、源码审查、构建产物、生产激活分别记账；未勾选条目表示尚无逐项验收映射，不能据历史 checkbox 推翻较新的任务证据，也不能无依据批量打勾。

审计快照：`docs/implementation/archive/2026-09-06/execution-snapshot.json`；归档登记：`docs/implementation/archive/2026-09-06/release-records.json`。
