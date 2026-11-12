# 聚义厅 melonJS 沉浸舞台优化设计

日期：2026-06-29

## 目标

把聚义厅首屏从“Vue DOM 舞台 + melonJS 叠加层”升级为“melonJS 主舞台 + Vue 业务面板”。本轮重点是让 melonJS、Tiled 地图、精灵表和动画真正参与用户体验：地图结构来自 Tiled，人物来自 spritesheet，业务反馈驱动角色动画、热点高亮和短气泡。

本轮不替换 Vue 3.5、Vite 6、Varlet UI 和现有业务 composable，不改变后端接口。

## 现状判断

现有代码已经引入 melonJS，但还没有完全用起来：

- `HallStage.vue` 会挂载 `.melon-layer`，调用 `juyitingGame.mount()`、`start()`、`syncAgents()`。
- `JuyitingGame.js` 会动态加载 `melonjs`、初始化 canvas、加载图片资源并注册 `HallScene`。
- `HallScene.js` 会绘制背景、前景、热点 marker 和 melonJS 版 `HallAgent`。
- 但 DOM 版 `AgentToken` 仍是主要可见/可点击人物层。
- `.melon-layer` 当前 `pointer-events: none`，melonJS 注册的热点点击不是主要交互来源。
- `hall.tmx` 存在，但运行时代码使用手写 `HALL_HOTSPOTS`，没有以 Tiled 为地图真源。
- `liangshan-character-atlas-v2.png` 当前只取单帧 idle，没有按动画状态播放 spritesheet。

## 范围

本轮做 melonJS 主舞台化：

- 让 `HallStage.vue` 使用 melonJS canvas 作为主舞台层。
- 使用 Tiled `web/public/juyiting/hall.tmx` 作为场景配置真源，读取背景、前景、热点、障碍和出生点。
- 使用 spritesheet 定义角色视觉和动画帧，支持 `idle`、`walk`、`talk`、`busy`、`selected`、`error` 状态。
- 把 `useHallScene` 的 `sceneAgents`、`sceneHotspots` 和业务反馈同步到 melonJS。
- Vue 保留面板、toast、选中上下文、业务数据加载和降级 DOM 层。
- 修复或规避 TMX 坐标与背景图片尺寸不一致的问题。

本轮不做：

- 不改 `/agent/map` 和 `/agent/roster` 的数据边界。
- 不重新引入 `/agent/active`。
- 不改变任务指派必须传显式目标 Agent 的约束。
- 不重构好汉簿、悬赏榜、议事面板内部业务流程。
- 不新增大型渲染框架，不用 Three.js 替代 melonJS。

## Tiled 地图设计

`hall.tmx` 当前包含：

- `imagelayer background`：背景图片 `images/liangshan-hall-bg-v2.png`。
- `objectgroup hotspots`：`mainSeat`、`agentRoster`、`bountyBoard`、`personaCatalog`、`libraryShelf`。
- `objectgroup obstacles`：桌案、书架、柱子、鼓、武器架等碰撞或避让区。
- `objectgroup spawns`：宋江、林冲、吴用、李逵、扈三娘、卢俊义以及通用出生点。
- `imagelayer foreground`：前景遮挡图片 `images/liangshan-hall-foreground-v1.png`。

实现原则：

- 新增一个轻量 TMX 解析层，读取 imagelayer 和 objectgroup，不依赖手写 `HALL_HOTSPOTS` 作为真源。
- 坐标统一为背景图片空间，再归一化到当前 canvas 尺寸。
- 当前 `hall.tmx` 的 map tile 尺寸是 `960x640`，但背景图片是 `1672x941`，且部分对象 y 坐标超过 640。实现时以 image layer 的 `width/height` 或对象最大边界作为坐标空间，避免底部热点被裁掉。
- 保留 object properties，例如 hotspot 的 `panel`。

## Spritesheet 与动画设计

现有资源：

- `web/public/juyiting/liangshan-character-atlas-v2.png`：角色外观图集，当前按 4 列 x 3 行使用。
- `web/public/juyiting/liangshan-character-body-atlas-v1.png`：身体部件图集，可作为后续细分动画资源。

本轮优先使用 `liangshan-character-atlas-v2.png` 做稳定动画：

- 定义每个角色的 sprite frame 起点和可用帧。
- `idle`：轻微上下浮动或单帧 breathing，不需要大量帧也能动。
- `walk`：目标点移动时播放步行动画；如果图集中缺少完整步态帧，用位置缓动 + squash/tilt 补足。
- `talk`：发言时播放头部/整体轻微摆动，并显示气泡。
- `busy`：任务执行中播放更明显的步态或高亮。
- `selected`：选中角色加描边、光圈或 tint。
- `error/offline`：降低饱和度或显示异常状态。

动画状态由 `sceneStatus`、`prominentMotion`、`selected`、`focused`、`bubble` 驱动。

## melonJS 与 Vue 分工

### melonJS 负责

- 背景、前景、热点 marker、人物精灵、角色动画、气泡、选中高亮。
- 热点点击命中和角色点击命中。
- 根据 `sceneAgents` 增删角色、移动角色、更新状态。
- 根据 `sceneHotspots` 显示热点状态和反馈文字。

### Vue 负责

- 页面编排、数据加载、面板打开关闭、任务指派、聊天、toast。
- 将 `sceneAgents` 和 `sceneHotspots` 传入 `HallStage`。
- 接收 melonJS 发出的 `select-agent` 和 `open-panel` 事件。
- 提供降级 DOM 舞台：当 melonJS 初始化失败时，仍可使用现有 DOM 热点和基础人物。

## 用户体验

进入聚义厅时，用户看到 melonJS canvas 主舞台：

- 背景和前景来自 Tiled image layer。
- 六位核心好汉从 Tiled spawn 点或 `useHallScene` anchor 入场。
- 点击人物会选中 Agent，底部显示选中上下文。
- 点击 Tiled hotspot 会打开对应 Vue 面板。
- 任务推荐后，推荐人物高亮，悬赏榜热点显示“荐单已出”。
- 点将后，目标人物向榜文区移动并播放 `busy/walk` 动画。
- 开议后，参与人物向议事区靠近并播放 `talk/discuss` 状态。
- 藏书阁搜索/引用后，藏书阁热点显示短反馈。

面板打开时，melonJS 主舞台保持背景可见但暂停或降低动画强度，避免遮挡和资源浪费。

## 错误与降级

- melonJS 初始化失败时，保留 Vue DOM 版本热点和人物作为降级体验。
- TMX 加载失败时，用当前静态资源和现有 `HALL_SCENE_HOTSPOTS` 派生 fallback。
- spritesheet 资源加载失败时，显示简化形状或跳过角色绘制，不阻断面板入口。
- 所有降级都要记录 console warn，不能让页面白屏。

## 数据边界

保持现有聚义厅不变量：

- 地图人物仍来自 `mapAgents` / `/agent/map`。
- 名册人物仍来自 `agents` / `/agent/roster`。
- `visibleAgents` 和 `sceneAgents` 继续从地图数据和 featured heroes 派生。
- 任务指派继续通过 `assignTask(task, agent)` 显式传入目标。
- 聊天上下文继续携带 `scene: 'juyiting'`、选中 Agent、提及 Agent 和选中任务。

## 验证

代码完成后运行：

- `cd web && npm run lint`
- `cd web && npm run test`
- `cd web && npm run build`
- 需要视觉确认时运行本地 dev server，用浏览器检查 canvas 非空、背景可见、角色可见、热点可点击、动画有状态变化。

重点检查：

- 页面不调用 `/agent/active`。
- `HallStage` 仍同步 `sceneAgents` 到 melonJS。
- TMX hotspots 能打开 `chat`、`agents`、`tasks`、`catalog`、`library` 面板。
- 角色点击能选中 Agent。
- `sceneHotspots` 的反馈能显示在 canvas 内。
- 桌面和移动端没有明显遮挡或文本溢出。

## 提交说明

根目录当前不是有效 Git 仓库：`/home/isp/wsps/cyf/.git` 是空目录，`git status` 无法运行。因此本设计文档写入根 `docs/`，但不能在根目录提交。后续前端代码变更将在 `web/` 仓库提交并推送。
