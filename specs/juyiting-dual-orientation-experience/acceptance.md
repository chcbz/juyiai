# 聚义厅横竖屏双形态 acceptance

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：横竖屏展示壳与资源生命周期。**

### 必须验证的业务结果
切换不重复请求/订阅、软键盘/安全区/焦点、后台/退出释放资源；真实设备未测则明确未测。

### 不回归边界
不为每个布局建立会话/数据/选中状态副本；布局按现行原型，不复活旧方向控件。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## O00 convergence

- [ ] parent/C09W/H05W/E13/H04 commit+tree 与任务包一致。
- [ ] Git 2.43.7 下用文档完整 SHA 命令得到 pre-resolution tree `46ed74444529001df23db02e89fc6009731f3b55`；每步 parent/source/merge-tree/final tree 可复现，worktree clean。
- [ ] protected-parent resolution manifest SHA-256 为 `59865b017ec15fc749457049f15e6b882467f1cb96a569520291bb6140449936`，O00 最终 E13 scripts/fixtures 三个 tree byte-exact 等于 parent。
- [ ] account security、OAuth transaction、Chat/Hall/Archive/Task SSE fail-closed、TaskWorkspace、ArchiveReader 和 E13 回归通过。

## Mode and orientation

- [ ] 移动端真实竖屏为轻应用、真实横屏为地图；桌面恒地图。
- [ ] 只有 `useHallExperienceMode` 监听方向；`useHallPanels` 为纯输入。
- [ ] 点击请求后，物理方向未变化时布局不切换。
- [ ] 键盘、`visualViewport` 高度和普通 resize 不切体验模式。
- [ ] 重复点击、请求拒绝、请求迟到、旋转竞态和 unmount 均不泄漏 ownership/listener。
- [ ] 无 CSS rotate、交换宽高、坐标补偿和 Web 内 `wx.miniProgram.redirectTo`。

## Portrait command mode

- [ ] 首屏有状态、实景窗口、六入口、待办和上下文。
- [ ] 首次竖屏 `juyitingGame.mount` 调用次数为 0。
- [ ] 竖屏核心操作不被横屏能力锁定。
- [ ] 所有派单显式 Agent；缺 Agent 时 assign request 次数为 0。

## Map lifecycle and target

- [ ] 状态机覆盖 mounting/resuming 反向旋转、suspending 反向请求和任意状态 unmount；destroying 只到 unmounted；stale mount/ready/RAF/observer/simulation callback 被 generation fence 拒绝。
- [ ] `suspended` 后 game update、stage/engine ResizeObserver callback、return RAF、viewport commit 和输入处理均为 0。
- [ ] resume 等非零容器连续两个 RAF 稳定后只提交一次最终 viewport。
- [ ] camera snapshot 由 JuyiHall 跨 HallStage remount 持有；camera restore 保持 world center/zoom 并重新 clamp；selected Agent 恢复。
- [ ] `{agentId|taskId+agentId|hotspotId}` 仅 byte-exact 解析；latest wins、取消、settled 后一次消费通过。
- [ ] 未知/stale target 回主厅并清空，不按名称/persona/title 猜测。

## Shared state and protected regressions

- [ ] 旋转不 remount panel、ArchiveReader、TaskWorkspace；selected task/Agent、conversation、draft、filters、reader/workspace state 不丢。
- [ ] portrait bottom drawer、mobile landscape right drawer、desktop center modal。
- [ ] `/agent/map` 与 `/agent/roster` 独立，无 `/agent/active`。
- [ ] OAuth/SSE 缺 token 时 Chat/Hall/Archive/Task stream 的网络 fetch 总数为 0。
- [ ] E13 camera/input transform selectors 通过，且禁止路径 blob 未变化。

## Required evidence

- Root/API unchanged commit+tree：
- O00 parent/source/merge-tree/final commit+tree：
- O01/O02/O03/O04 commits/trees：
- Evidence key：`web tree SHA + exact selector/command + fixture digest + device/host version`。
- Exact automated commands（在 clean O04 Web worktree 执行）：
  - `TSX_TSCONFIG_PATH=jsconfig.json node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec tests/composables/accountSecuritySession.spec.js tests/composables/confirmationDialog.spec.js tests/composables/apiStoreOauth.spec.js tests/composables/oauthCallback.spec.js tests/composables/oauthHttpAuth.spec.js tests/composables/oauthRoutes.spec.js tests/composables/oauthSseAuth.spec.js tests/composables/oauthTransaction.spec.js tests/composables/useHttp.spec.js tests/composables/userProfileAccountSecurity.spec.js`
  - `TSX_TSCONFIG_PATH=jsconfig.json node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec tests/juyiting-experience-mode.test.js tests/juyiting-portrait-home.test.js tests/juyiting-component-behavior.test.js tests/juyiting-collaboration-flow.test.js tests/juyiting-hall-task-actions.test.js tests/juyiting-hall-conversation.test.js tests/juyiting-hall-backend-scene-state.test.js tests/juyiting-selected-agent-card.test.js`
  - `TSX_TSCONFIG_PATH=jsconfig.json node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec tests/juyiting-task-workspace-a11y.test.js tests/juyiting-task-workspace-feature-flag.test.js tests/juyiting-task-workspace-integration.test.js tests/juyiting-task-workspace-panel.test.js tests/juyiting-task-workspace-state.test.js tests/juyiting-task-workspace-wiring.test.js tests/archive-reader.test.js`
  - `node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec tests/game/camera/camera-controller.test.ts tests/game/camera/camera-transform.test.ts tests/game/camera/resize-policy.test.ts tests/game/input/input-controller.test.ts tests/game/input/pointer-gesture.test.ts tests/juyiting-hall-scene-runtime.test.js tests/juyiting-melon-hall-scene.test.js`
  - `npm run typecheck:game`
  - `npx eslint src/composables/juyiting/useHallExperienceMode.js src/composables/juyiting/useHallPanels.js src/composables/juyiting/useHallTaskActions.js src/components/world/JuyiHall.vue src/components/juyiting/HallStage.vue src/components/juyiting/HallPortraitHome.vue src/game/JuyitingGame.js src/game/scenes/HallScene.js src/game/camera/cameraController.ts tests/juyiting-experience-mode.test.js tests/juyiting-portrait-home.test.js tests/juyiting-hall-task-actions.test.js`
  - `npm run build`
  - `VITE_JUYITING_TASK_WORKSPACE_ENABLED=true npm run build`
- Required behavioral selectors：orientation request races；portrait mount=0；suspended callback/update/resize=0；resume final viewport；target latest/cancel/once/unknown；panel instance identity；explicit Agent API=0；OAuth/SSE anonymous fetch=0；ArchiveReader/TaskWorkspace regression；E13 camera/input regression。
- iOS WeChat H5：device model、iOS、WeChat version、普通 H5（Mini Program=N/A）、portrait→landscape→portrait repeated 5 cycles。
- Android WeChat H5：device model、Android、WeChat version、普通 H5（Mini Program=N/A）、same 5-cycle scenario。
- Independent Review：
- Result：pending
