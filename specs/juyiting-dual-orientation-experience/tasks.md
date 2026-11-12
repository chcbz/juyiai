# 聚义厅横竖屏双形态 tasks

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：横竖屏展示壳与资源生命周期。**

**实施目标：** 进入页面→按视口展示→方向切换保留上下文→离开释放资源。
**责任落点：** JuyiHall保有业务状态；横竖展示壳复用同一状态；Web管理订阅/运动/视口生命周期。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不为每个布局建立会话/数据/选中状态副本；布局按现行原型，不复活旧方向控件。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：切换不重复请求/订阅、软键盘/安全区/焦点、后台/退出释放资源；真实设备未测则明确未测。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## Global preconditions

- [x] D06 `accepted`、`handoffs/D06.md` 存在、独立 Reviewer ACCEPT 已记录、D06 worktree clean。
- [ ] O00 使用独立 clean Web worktree，并与其他 active Writer 冻结不重叠 owned paths。
- [ ] Gradle、隔离 DB/Rabbit、browser gate 与 Web production build 等共享重型资源明确串行/错峰。
- [x] O00–O04 已登记到 `docs/implementation/TASKS.yaml` 和 `MODEL_ROUTING.yaml`。

## O00 — Web 高风险收敛基线

所有 O00/O01–O04 路径均相对独立 `web` repository root；控制面登记时写为 `web/<path>`。

- Owner：`critical_worker`
- Reviewer：`sol_reviewer`
- Source order：固定 `origin/develop` → C09W → H05W。若执行时 `origin/develop` 不再 byte-exact 等于 `7bc80de75f83d4cb7ca288380c3ed9eab1bc111a`，O00 自动失效，必须重新生成 manifests/merge-tree 并重新架构审查。
- Pinned inputs：
  - parent `7bc80de75f83d4cb7ca288380c3ed9eab1bc111a`, tree `182572ba74399f4feb714706b1310785ed83668e`
  - C09W `549fbd0fc8a3c40b5524a49e4f48d19369672cc8`, tree `7e354b98a231c862bea22c0e8f12240e11c7001f`
  - H05W `0b3d93041faaf6c3212a8a9f45a1ba64acd2108f`, tree `2ba166c2771175ef658e442b782a28992c81c8c3`
  - C09W/H05W shared relevant ancestor `42220937bdad154c20c3b9a95330440520635ef9`, tree `ee1fda38cdc9bfdbce229d6122a7b43fc7425502`
  - E13 accepted ancestor `c1d97096a196b843ca4a9fb5d126686dca9aa28b`, tree `0c0bf6fa8853f0b9dc5f2453503af7467bd46c59`
  - H04 accepted ancestor `59325d48bed5724de4a92b11e0b873f6d6443fd7`, tree `2464cc3a29439d082d15efbe4ded103417ced30b`
  - exact pre-resolution command（Git `2.43.7`）：`git merge-tree --write-tree --messages 7bc80de75f83d4cb7ca288380c3ed9eab1bc111a 549fbd0fc8a3c40b5524a49e4f48d19369672cc8`；预期 conflicted tree `46ed74444529001df23db02e89fc6009731f3b55`。命令参数必须使用上述完整 commit 拼写；conflict blob 含 label，短 ref 会产生不同 tree，禁止使用。
- O00 allowed paths：机械合入仅限 `o00-c09w-source-delta.txt` 与 `o00-h05w-source-delta.txt` 中的 path union；人工语义编辑仅限 `o00-semantic-conflicts.txt`。任何额外 path 立即 fail closed。
- Protected-parent resolution：C09W delta 中的 E13 scripts/fixtures 不进入 O00 结果。先按 merge 解决其他路径，再执行 `git restore --source=7bc80de75f83d4cb7ca288380c3ed9eab1bc111a --staged --worktree -- scripts/juyiting/e13 tests/fixtures/juyiting/occlusion-e13 tests/fixtures/juyiting/occlusion-v2-constraint`；验证三个 tree byte-exact 等于 parent ledger。受保护差异清单 `o00-protected-parent-resolution.txt` SHA-256 `59865b017ec15fc749457049f15e6b882467f1cb96a569520291bb6140449936`（50 entries）。
- Manifest identity：C09W delta SHA-256 `961128bcc4d9af215f36d0e8a1975bd4ce3df039a9894f7e21f02e98eba315a8`（90 entries）；H05W delta SHA-256 `c05a9fc50a710853bc3f8b2ac990a5a93384e73c8918e882a570289cbda1b502`（5 entries）；semantic conflicts SHA-256 `3a8d80d088ad0b60a49157819dadfec8d913881f10d8340aef25c2554d64fce1`（13 paths）。
- Conflict rule：不得整边覆盖；每个 semantic conflict 必须记录 parent/source/result blob 和选择理由。
- Required output evidence：Git version、完整命令、first-parent/source SHAs、pre/post-resolution tree、每步 merge-tree SHA、最终 commit/tree、`git status --porcelain` empty、Reviewer ACCEPT。
- Acceptance：最终三个禁止路径 tree 必须 byte-exact 等于 parent `619119a...` / `e38f91e...` / `cac2cc9...`；同时保留 account-security identity lifecycle、C09W TaskWorkspace/OAuth/SSE fail-closed、H04/H05W ArchiveReader、E13；匿名 token 缺失时 Chat/Hall/Archive/Task stream fetch=0。
- O00 ACCEPT 前不得 claim O01。

### O00-R1 — 权威 Review 显式 Agent 有界整改

- 触发：O00 candidate `4ab34b5673bc5f76c3d728ecef63d835cac451d9` / tree `10f5d5bfd8a2b0b3de958da4bc07d045e6c071c7` 权威 Review `REJECT 0/1/0`。
- 唯一 finding：派单在缺失显式 Agent 时仍回退 `selectedAgent` 并发出请求，且 wrapper 可能不更新 workspace。
- 允许新增路径仅限 `o00-r1-explicit-agent-remediation.txt`，SHA-256 `ea87d64cb2a540e92897d846fc0cc974622aa904c0042f105741d2a1b49054e5`（5 paths）。除此之外 O00 原 manifest/protected 规则保持不变。
- 修复合同：`assignTask(task, agent)` 与 `canAssign(task, agent)` 均不得默认读取 `selectedAgent`；缺 task/Agent/agentId 时 assign API=0，wrapper 不清理/写入 actor 或 workspace assignment；显式单 Agent/Agent 数组行为保持。
- 必须补真实 composable 负向回归与 wrapper wiring 约束；形成新 clean commit/tree 后由独立 `gpt_test_runner` 跑 targeted selectors，再启动一个 fresh `sol_reviewer`。旧 O00 Review 不得复用。

## O01 — 唯一体验模式与方向请求

- Dependencies：O00 accepted
- Owner：`balanced_worker`
- Reviewer：`sol_reviewer`
- allowed paths：
  - `src/composables/juyiting/useHallExperienceMode.js`
  - `src/composables/juyiting/useHallPanels.js`
  - `src/components/world/JuyiHall.vue`
  - `src/components/juyiting/HallStage.vue`
  - `tests/juyiting-experience-mode.test.js`
  - `tests/juyiting-component-behavior.test.js`
- Acceptance：唯一方向监听者、桌面恒 landscape、移动端只按真实方向、键盘不切模式、请求失败不提前换壳、无直接 Mini Program redirect、无 CSS rotate、竞态/unmount ownership 清理通过。

## O02 — 竖屏轻应用首页

- Dependencies：O01 accepted
- Owner：同一 `balanced_worker`
- Reviewer：`sol_reviewer`
- allowed paths：
  - `src/components/juyiting/HallPortraitHome.vue`
  - `src/components/world/JuyiHall.vue`
  - `src/composables/juyiting/useHallTaskActions.js`
  - `tests/juyiting-portrait-home.test.js`
  - `tests/juyiting-hall-task-actions.test.js`
  - `tests/juyiting-collaboration-flow.test.js`
- Acceptance：状态概览、轻量地图窗口、六个快捷入口、待办与当前上下文可单手操作；首次竖屏 melon mount=0；地图/名册双流不变；页面 wrapper 与 `useHallTaskActions` 两层派单均要求显式 Agent，缺 Agent 时 request=0；核心功能不被横屏能力锁定。

## O03 — 地图 destroy/remount 恢复与目标聚焦

- Dependencies：O02 accepted
- Owner：同一 `balanced_worker`
- Reviewer：`sol_reviewer`
- allowed paths：
  - `src/components/juyiting/HallStage.vue`
  - `src/components/world/JuyiHall.vue`
  - `src/game/JuyitingGame.js`
  - `src/game/scenes/HallScene.js`
  - `src/game/camera/cameraController.ts`
  - `tests/juyiting-component-behavior.test.js`
  - `tests/juyiting-hall-scene-runtime.test.js`
  - `tests/juyiting-melon-hall-scene.test.js`
  - `tests/game/camera/camera-controller.test.ts`
- Acceptance：状态机与 generation fence 完整；回竖屏 observer/RAF/update/resize=0；再横屏仅一次最终 viewport commit，恢复 camera/selected；target payload/覆盖/取消/一次消费/unknown fallback 全部通过。

## O04 — Panel、可访问性与集成门禁

- Dependencies：O03 accepted
- Owner：同一 `balanced_worker`
- Reviewer：`sol_reviewer`
- Test runner：`gpt_test_runner`
- allowed paths：
  - `src/composables/juyiting/useHallPanels.js`
  - `src/components/world/JuyiHall.vue`
  - `tests/juyiting-experience-mode.test.js`
  - `tests/juyiting-portrait-home.test.js`
  - `tests/juyiting-component-behavior.test.js`
  - `tests/juyiting-collaboration-flow.test.js`
  - `tests/juyiting-selected-agent-card.test.js`
  - `tests/archive-reader.test.js`
  - `tests/juyiting-task-workspace-integration.test.js`
  - `tests/composables/oauthSseAuth.spec.js`
- Acceptance：panel/ArchiveReader/TaskWorkspace 在旋转时不 remount；焦点/草稿/reader/workspace state 不丢；显式 Agent 缺失时 API=0；OAuth/SSE 匿名 fetch=0；targeted tests、typecheck、lint、生产 build、真实 iOS/Android 微信 smoke 通过。

## Protected source/blob ledger

O00 必须在 handoff 中给出最终对应 blob；以下 accepted 输入不能被无说明降级：

- account security `7bc80de`：`useAccountSecuritySession.js` `45948eb4b918db4df220806e57776e6ec3fc1b5c`、`identityLifecycle.js` `d8bb74de963c0c1949f28b6c0f1802d72590c644`、`authenticatedSse.js` `58cf32a991e06cb83cd2bf80c5e63f9bca899f7a`
- C09W：`TaskWorkspacePanel.vue` `1b9ba158a7015c0f8c69652ab9add5720cb1ff85`、`useTaskWorkspace.js` `4b0316e2e00cf8702dc521798beea80e77e95fc8`、`useTaskEventStream.js` `5254b55512ca4481d4176f1fa6dbc36d63e068b6`、`oauthTransaction.js` `117e601e96281facdf3dd2d54544ad4c82dcfd18`、`oauthCallback.js` `5bc1b7377aaef090a2c872133d4edfa7fd6acd80`
- H05W：`ArchiveReader.vue` `53f55af8d7f212c3fd8880691de7805f620d4bf3`、`useArchiveReader.js` `c39b2a801cffbe6af016932d7746c49b965c0865`、`archive-reader.test.js` `5a63594e6928e984412e2983fae7852d53ef62c7`
- E13 runtime：`JuyitingGame.js` `085bdf3c56e96c2abd29a68c306b7084a8a44917`、`HallScene.js` `b14adfb1ae980f13a4c087882f880a4e2e3b8173`、`cameraController.ts` `614f71762253327b93e742ab166b96025e9ac24c`

## Forbidden path identity

O01–O04 的禁止路径以 O00 最终 tree 为准；O00 必须记录并解释 parent/source 差异。当前固定 parent tree identity：

- `scripts/juyiting/e13` tree `619119a02466e59e8ac5841130385ef26e85abc5`
- `tests/fixtures/juyiting/occlusion-e13` tree `e38f91edce5f282cb3c9e92a25840b5e6f2ef104`
- `tests/fixtures/juyiting/occlusion-v2-constraint` tree `cac2cc99a1e5fb1d069e3f62fa7fbf7d13a0890c`

## Forbidden paths

- `scripts/juyiting/e13/**`
- `tests/fixtures/juyiting/occlusion-e13/**`
- `tests/fixtures/juyiting/occlusion-v2-constraint/**`
- root `api/**`
- root `deliverables/**`

## Promotion

O00 → O01 → O02 → O03 → O04。每项独立 commit/tree、handoff、gpt_test_runner evidence 和 Reviewer ACCEPT 后自动推进；REJECT 由原 Writer 在原 worktree 修复。O04 后才允许集成/部署门禁。
