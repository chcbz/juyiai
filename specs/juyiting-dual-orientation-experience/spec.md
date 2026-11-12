# 聚义厅横竖屏双形态体验

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：横竖屏展示壳与资源生命周期。**

### 责任与业务流程
JuyiHall保有业务状态；横竖展示壳复用同一状态；Web管理订阅/运动/视口生命周期。

进入页面→按视口展示→方向切换保留上下文→离开释放资源。

### 明确边界
不为每个布局建立会话/数据/选中状态副本；布局按现行原型，不复活旧方向控件。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
切换不重复请求/订阅、软键盘/安全区/焦点、后台/退出释放资源；真实设备未测则明确未测。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留方向/资源生命周期和真实设备回归；旧布局目标不覆盖最新原型。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


<!-- SDD delivery reconciliation 2026-09-06 -->
## Problem

当前移动端横竖屏都以 melonJS 地图为页面主体。竖屏下地图可视面积狭窄，高频操作需要经过地图或浮层；横屏适合探索，但当前互动深度不足以要求用户长期停留。继续压缩同一套地图布局，会同时损害竖屏效率和横屏沉浸感。

## Goals

1. 竖屏提供单手可用的轻应用首页：状态概览、轻量实景窗口、快捷功能、待办和当前上下文。
2. 横屏保留完整地图、拖动缩放、人物/热点探索和右侧业务抽屉。
3. 横竖屏共享 Agent、任务、会话、草稿、筛选和选中上下文；物理旋转不重新加载顶层业务状态。
4. 首次竖屏不创建 melonJS；进入横屏才创建地图，回竖屏后不让隐藏 canvas 在后台运行。
5. 普通 H5 只使用真实视口方向；不恢复 CSS 旋转、交换宽高或触摸坐标补偿。
6. 横屏互动使用严格、一次性的 landscape entry target（严格目标聚焦，见 O03；不做未来功能预留）。

## Non-goals

- 本期不新增后端接口、数据表或事件协议。
- 本期不实现完整游戏化任务路线、多 Agent 集结、随机事件或区域解锁。
- 不通过削弱竖屏核心操作强迫用户横屏。
- 不保证普通微信 H5 可以强制锁定设备方向。
- 不在本期实现或验收小程序跨页 `redirectTo`；宿主页面方向配置和 WebView handoff 另立宿主任务。
- 不使用 `transform: rotate(...)`、交换宽高或坐标补偿模拟横屏。
- 不改变 `/agent/map` 与 `/agent/roster` 的数据边界，不重新引入 `/agent/active`。

## Scope

- O00：把最新 Web `origin/develop`、C09W 和 H05W 收敛为 clean、独立审核通过的 Web 基线。
- O01：新增唯一方向/体验模式 composable；`useHallPanels` 不再监听方向。
- O02：新增竖屏轻应用首页；首次竖屏地图 mount 次数为 0。
- O03：实现地图 snapshot + destroy/remount 生命周期、相机恢复和严格目标聚焦。
- O04：完成 panel、键盘、可访问性、OAuth/SSE、ArchiveReader、TaskWorkspace、E13 回归门禁。

## Constraints and risks

- O00 必须先完成；不得从本地 dirty `web/develop` 开工。
- 允许独立任务在独立 worktree 按不重叠 owned paths 并行使用 Writer；D06 未 accepted、无 handoff、worktree 不 clean 时仍不得 claim O00。
- H06 重型 Gradle/浏览器门禁运行期间，O00/O04 build 与全量验证必须错峰。
- `JuyiHall.vue` 是业务状态唯一编排层；两个展示壳不得创建第二份数据、会话或选中状态。
- 地图采用确定性的 snapshot + destroy/remount 主路径，不依赖当前缺失的 melonJS resume 契约。
- 任务指派 API 必须要求显式目标 Agent；缺 Agent 时不得发请求。
- E13 脚本和 fixture 为禁止路径；不得覆盖或重生成。
