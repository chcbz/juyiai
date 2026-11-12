# 聚义厅横竖屏双形态 design

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：横竖屏展示壳与资源生命周期。**

### 最小责任链
JuyiHall保有业务状态；横竖展示壳复用同一状态；Web管理订阅/运动/视口生命周期。

进入页面→按视口展示→方向切换保留上下文→离开释放资源。

### 实施约束
不为每个布局建立会话/数据/选中状态副本；布局按现行原型，不复活旧方向控件。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## Experience model

### Portrait command mode

真实移动端竖屏进入 `portrait-command`：

- 顶部状态概览：候命、办事中、异常和待处理榜文。
- 聚义厅实景窗口：静态/轻量场景背景、少量 Agent 状态和“厅中动静”；不挂载可拖动 canvas。
- 快捷入口：点将册、悬赏榜、厅前议事、招贤令、案卷阁、点验刷新。
- 待办与当前上下文：当前 Agent、当前任务、最近状态和显式操作入口。
- “横屏看全景”可以携带 Agent、任务或热点 target，但只请求方向，不提前换壳。

### Landscape immersive mode

真实移动端横屏及桌面进入 `landscape-map`：

- 完整 `HallStage` 占满可用区域。
- 地图人物、建筑热点、拖动、缩放和回主厅继续作为主要交互。
- 顶部只保留紧凑刷新、声音和方向入口；业务内容使用右侧抽屉。
- target 可聚焦 Agent、任务已显式关联的 Agent 或热点；未知/失效 target 回主厅。

## Single source of truth

`JuyiHall.vue` 继续唯一持有 `mapAgents`、roster `agents`、`tasks`、selected Agent/task、panel/focus、conversation/draft/stream、filters、toast 和 sound。

`useHallExperienceMode` 是方向和体验模式的唯一监听者，只持有：

- `isMobileCoarse`、`isPhysicalLandscape`
- `experienceMode: portrait-command | landscape-map`
- best-effort H5 方向请求状态、提示和本页获得的 fullscreen/lock ownership
- `landscapeEntryTarget` 与 generation

`HallPortraitHome`、`HallStage` 只通过 props/emits 消费顶层状态。

## Orientation formula and listener ownership

唯一公式：

```text
experienceMode = !isMobileCoarse
  ? landscape-map
  : (isPhysicalLandscape ? landscape-map : portrait-command)
```

规则：

1. `useHallExperienceMode` 是唯一 `matchMedia('(orientation: landscape)')`、`matchMedia('(pointer: coarse)')` 和 layout `resize` 监听者。
2. `useHallPanels` 改为纯输入：`useHallPanels({ experienceMode, isMobileCoarse })`；不得再注册 orientation/resize listener。
3. 桌面恒为 `landscape-map`，无论窗口宽高关系。
4. 移动端只接受真实 orientation media 状态；仅在 API 不存在时用稳定的 `innerWidth > innerHeight` 初始化/回退。
5. `visualViewport.height`、软键盘高度变化和单纯 layout resize 不参与模式判定。
6. 点击按钮只发起 fullscreen + `screen.orientation.lock('landscape')`；真实方向变化前 UI 不切换。
7. 本期 Web 禁止直接调用 `wx.miniProgram.redirectTo`。可选 host adapter 仅返回 capability/ack；跨页 handoff 不属于本期验收。
8. 请求失败保持竖屏并提示物理旋转；unmount 只释放本页实际获得的 fullscreen/lock。
9. 禁止 CSS rotate/virtual landscape。

## Map lifecycle: snapshot + destroy/remount

主路径固定为 **snapshot + destroy/remount**，不使用不完整的 `pause()` 作为隐藏后台运行方案。

状态机（`destroying` 只可到 `unmounted`）：

```text
unmounted → mounting
mounting → running | suspending | destroying
running → suspending | destroying
suspending → suspended | destroying
suspended → resuming | destroying
resuming → running | suspending | destroying
destroying → unmounted
```

反向事件规则：

- `mounting/resuming` 尚未 ready 就转竖屏：进入 `suspending`，作废 generation，完成当前幂等 destroy 后进入 `suspended`。
- `suspending` 期间又转回横屏：只设置 `resumeRequested=true`；必须先完成 destroy 并进入 `suspended`，再立即 `suspended → resuming`，禁止交叉 mount/destroy。
- 任意非 `unmounted/destroying` 状态发生页面 unmount：进入 `destroying`；后续方向/ready/observer callback 全部忽略，最终只能到 `unmounted`。
- fatal mount/restore error：进入 `destroying → unmounted`，由显式重试重新开始 `unmounted → mounting`。

事务边界：

- `mapResumeSnapshot` 由不会随方向 remount 的 `JuyiHall.vue` 顶层持有，只包含 camera/runtime generation；`HallStage` suspend 时 emit，resuming 时以 prop 读取，restore 成功后 emit 清除。不得把 snapshot 只放在会被销毁的 `HallStage` 本地。
- 每次 mount/resume 递增 `mapGeneration`；所有 loader、ready、observer、RAF、simulation callback 必须核对 generation。
- `mounting`：输入以 `loading` reason 锁住；建立 stage ResizeObserver 与现有 canvas/engine observer；异步 mount 过期时不得发布 ready 或状态。
- `running`：只有此状态允许输入、simulation update、return-button RAF 和 viewport commit。
- `suspending` 顺序：
  1. 原子切换状态并锁输入；
  2. 记录 `{cameraSnapshot, mapGeneration}`；业务 selected Agent 不进入地图快照；
  3. 取消 stage RAF、return RAF、pending viewport commit；
  4. disconnect stage ResizeObserver，并让 engine/canvas observer 在 destroy 中清理；
  5. 停止 simulation phase/update 并作废 callback generation；
  6. 幂等调用 `destroy()`；
  7. destroy 完成后进入 `suspended`。
- `resuming`：创建新 generation，重新 mount；等待容器 `ResizeObserver` 报告非零尺寸并连续两个 RAF 稳定后，只提交一次最终 orientation viewport；随后调用 camera restore API，并从当下 `JuyiHall.selectedAgent` prop 同步选中态，再进入 `running` 并解锁输入；禁止历史快照回写业务选中态。
- `destroying`：页面真正 unmount 或 mount 失败时可从任意状态进入；重复调用必须幂等，且不得留下 observer、RAF、timer、listener、simulation callback 或 melon state。
- 首次竖屏保持 `unmounted`，所以 melonJS mount=0。

`cameraController.ts` 新增受检验的 `restore(snapshot, viewport)`；只接受有限数值并重新 clamp，不能直接信任旧 viewport。`JuyitingGame` 暴露 capture/restore/focus facade；测试覆盖 stale generation、最终 viewport 和 destroy 幂等。

## Landscape entry target

冻结 payload：

```ts
type LandscapeEntryTarget =
  | { kind: 'agent'; agentId: string }
  | { kind: 'task'; taskId: string; agentId: string }
  | { kind: 'hotspot'; hotspotId: string }
```

语义：

- ID 必须是非空字符串，按 byte-exact ID 解析；不得按姓名、persona、标题或模糊匹配猜测。
- 新 target 覆盖旧 target并递增 target generation；显式取消写入 `null`。
- Agent：只在 `mapAgents.agentId` byte-exact 命中时聚焦。
- Hotspot：只在 authoritative `sceneHotspots.id` byte-exact 命中时聚焦。
- Task：`taskId` 先 byte-exact 命中 authoritative task；payload 的 `agentId` 必须同时 byte-exact 属于该任务显式 `assignedAgentIds`/`assignees[].agentId` 集合，并命中 `mapAgents.agentId`。不得隐式取数组首项；任一条件不满足即回主厅。
- 仅在地图 `running` 且最终 viewport settled 后消费一次；消费前被覆盖/取消的 generation 不得生效。
- 未知、失效或不可见目标执行 `resetToMainHall()`，清空 target，并给出非阻断提示。

## Shared panel behavior

浮层位于两个展示壳之外，实例 key 不随方向变化：

- 竖屏：`bottom-drawer`
- 粗指针横屏：`right-drawer`
- 桌面：`center-modal`

旋转不得 remount panel 内容、ArchiveReader 或 TaskWorkspace；active panel、focus return target、聊天草稿、reader state 和 workspace reducer state 均留在 `JuyiHall.vue`/既有 composable。

## Assignment invariant

`assignTask(task, agent)` 与 `canAssign(task, agent)` 不允许默认 `agent = selectedAgent`。缺失 Agent 时立即返回/报可读错误，且 `agentApi.assignTask` 调用次数必须为 0。所有 UI emit 必须显式带 Agent。

## Protected semantics

- `/agent/map` 与 `/agent/roster` 双流不变，无 `/agent/active`。
- H04/H05W ArchiveReader 的 selection、恢复、private state 和 SSE reducer 不变。
- C09W TaskWorkspace decimal-string、recovery 和 OAuth/SSE fail-closed 不变。
- E13 camera/input/occlusion 坐标真源不变；本期不改证据脚本/fixture。

## Compatibility and rollout

- 无后端 feature flag。
- O04 真实设备 smoke 未通过前不部署。
- 回滚可恢复单一 `HallStage` 编排，但不得恢复 CSS rotate。
- 小程序固定 orientation page、WebView query/state handoff 和 return route 另立宿主任务后再启用。
