# 详细设计 v1

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：复用同一地图状态的只读预览。**

### 最小责任链
地图数据/运动由原地图模块维护；竖屏预览只投影视图。

地图事实→共享状态→只读缩略预览→需要交互时进入现行全景入口。

### 实施约束
不以roster替代map，不建立第二动画/轮询/会话状态；不恢复已取消方向控制。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 1. 代码事实与限制
读取设计基线 `101ac4c6`：
- `HallPortraitHome.vue` 的 `scene-sky/scene-hall/scene-courtyard` 是装饰；`sceneAgents` 取 `mapAgents.slice(0, 4)`。
- `JuyiHall.vue` 以 `v-if/v-else` 切换竖屏首页与 `HallStage`；后者管理单例 `juyitingGame` 的挂载、销毁、就绪回调与模拟接入。
- `JuyitingGame.js` 管理地图资源/场景/运动运行态；`HallScene.js` 完成人物与地图图层绘制，并驱动已有运动更新。
- `HallStage` 的 `simulation-ready/reset/phase-events` 会连到页面命令队列和状态转发；“只屏蔽鼠标”不足以证明只读。
- `fitToViewport()` 当前等同主厅 reset，不能直接当全地图 contain 使用；必须以实际地图边界计算镜头。
- 横屏生命周期已有新整改，接入必须基于其被接受候选，不能在旧实现上并行重写。

## 2. 展示与交互契约
- 预览标题“厅中实景”，辅助说明“只读预览 · 横屏可探索”。实际加载成功之前不得标为实时/已就绪。
- 卡片横向占满竖屏内容区，按地图宽高比保留尺寸（基线画布 1664×928 仅为加载前占位比例）；完整容纳地图，允许上下/左右留边，不裁掉建筑以填满卡片。
- 保留地图图层顺序、遮挡、角色精灵、朝向和行走动画；不另取前四人，不接入 roster 过滤。是否显示原有演示角色与横屏保持一致。
- 首版不增加人物名称常驻标签或选择热点，避免全景缩小后遮挡；不在预览改变人物世界坐标或碰撞体积。
- 预览画面没有点击/拖动/缩放/键盘地图动作，不获取焦点、不捕获指针、不 preventDefault 页面滚动；横屏按钮在画面外独立可聚焦，继续调用现有 `requestPortraitLandscape`。
- pending 时按钮禁用并显示已有方向提示；失败不自动反复请求横屏。预览重试只重试地图资源，不重启业务连接。
- 保留原竖屏快捷入口、状态统计、待办与弹框；原场景内人物按钮由纯预览替代，点将操作仍由点将册提供。

## 3. 组件边界和单运行态
建议结构（实施时可按已接受 SCREEN 契约微调，但不得改变不变量）：

```text
JuyiHall（既有业务数据/选择/方向状态）
 ├─ HallPortraitHome
 │   └─ HallLiveMapPreview（纯视图外壳 + 稳定 mount target/slot + 状态）
 └─ 页面级唯一场景宿主（在预览目标或横屏目标展示同一 Canvas）
     └─ juyitingGame → HallScene → 现有角色运动
```

- 页面级场景宿主只有一个；优先复用 SCREEN 已接受的保留/恢复能力。可用 Vue 管理的稳定宿主/Teleport 完成换容器；不得直接复制 canvas DOM 作为新引擎。
- 若采用 Teleport，设计要求目标容器先存在；保留两个稳定目标而不是把承载 Canvas 的目标随 v-if 删除。不假设第三方引擎能自动重绑尺寸，必须执行宿主 adapter 与浏览器验证；异步目标时序由本任务显式管理。
- UI 外壳不导入 `juyitingGame`、API store、movementEngine 或命令队列，不自行挂载引擎。
- 准备阶段只新增 `HallLiveMapPreview.vue`、`liveMapPreviewPolicy.js` 和对应新测试；不修改共享入口/场景文件。
- 只因横竖屏切换，不重建场景/人物/模拟；最终离开路由才彻底销毁。后台恢复是否保留 Canvas 由 SCREEN 生命周期契约决定，不能覆盖其受审修复。
- 交接后接入前必须完成 adapter 对照表：SCREEN 暴露的保留/恢复、容器重绑定、尺寸稳定提交、输入锁、最终销毁接口逐项对应。若缺能力，由本任务原 Terra Owner 在已交接文件中最小扩展，独立审核。

## 4. 预览外壳接口（可先行实施）
`HallLiveMapPreview.vue`：
- props：`state`（loading/ready/paused/error）、`errorMessage`（受控简短文本）、`mapWidth/mapHeight`（正有限数；未知使用占位比例）、`orientationRequestPending`、`orientationHint`。
- emits：`request-landscape`、`retry`、`visibility-change(boolean)`；无 select-agent、command 或 orientation side effects。
- 默认 slot 提供稳定画面容器；状态浮层不得替换或销毁 slot。visibility 由 IntersectionObserver 观测，缺 API 时按可见降级；通知去重，卸载清理。此信号仅供宿主合成策略，不直接暂停引擎。
- error/paused 状态文案与恢复按钮语义准确；状态播报只在离散转换发生，不随帧/人物位置触发 aria-live。
- 无 API 调用、截图复制、RAF 动画或全局 document 事件写入。

纯函数 `liveMapPreviewPolicy.js`：
- contain 几何：输入 world bounds（含非零 x/y）和正 viewport 尺寸，输出 scale 与 offset；scale=min(viewW/worldW,viewH/worldH)，offset 将 world bounds 中心对齐。非法/零尺寸返回未就绪，不提交 NaN/Infinity 镜头。
- activation 合成：区分未就绪、documentHidden、portraitOffscreen、overlayCovered、landscapeActive；竖屏离屏不能暂停正在显示的横屏。
- 状态/目标帧率作为纯策略输出，而不是组件启动第二个 timer。预览可见目标 20fps；横屏沿用既有帧率，不更改其全局默认。

## 5. 模式切换与镜头
模式转换顺序：
1. 提升转换 generation，取消旧手势并锁输入；保存横屏专属镜头（进入预览时才保存）。
2. 更新单场景宿主的展示容器；等待 Vue DOM 完成及有效非零尺寸稳定提交。
3. 预览采用 actual world bounds 的 contain 镜头；横屏恢复专属镜头，若存在显式 agent/task/hotspot 入口目标则仍按原优先级处理。
4. 接受当前 generation 的 ready/resize 回调；过期异步资源/RAF/observer 回调不得覆盖当前模式。
5. 预览保持独立 `preview` 输入锁原因；横屏仅释放 preview 锁，不释放 modal/voice/loading 锁。

预览镜头不写回原横屏 resume snapshot，不重置地图 generation；横屏与预览不能同时占用两套 canvas/runloop。快速切换中最终状态以方向协调器最新有效请求为准，不用容器宽高反推新的用户方向意图。

## 6. 数据、业务只读与权限
- 地图仍用 `GET /agent/map` → `mapAgents` → 原 `sceneAgents`；名单仍用 `/agent/roster`，禁止 `/agent/active`。
- 不新增 API/path/schema/event。已有认证、主体变化、版本和回放语义不变，不提升权限或修改 feature flag。
- 冷启动竖屏仅为展示，不因 preview ready 启动额外业务命令消费者、任务派发或状态写入；本地巡逻可沿用已存在的纯表现运行态。
- 横屏已经建立的业务驱动由原页面 Owner 统一管理；切换 UI 不再建第二套队列/订阅，也不能把已接纳命令假完成、重排或吞 terminal。预览组件完全不持有这些能力。
- 接入前必须明确“本地巡逻渲染”与“后端命令驱动”的独立生命周期：如现有二者耦合，先做有界 adapter 隔离再接入，不能以关闭全部 simulation 达成只读而导致画面无人移动。
- 路由离开/主体变化仍清理原主体场景数据和订阅。不同主体不得复用角色运行态或镜头目标中的敏感上下文。

## 7. 性能、失败与恢复
- 惰性加载场景，但卡片和按钮首屏立即可用；地图资源按同一版本复用，不每次切换 fetch 新 URL。
- 预览渲染预算目标 20fps，是否可独立降低绘制须在引擎 adapter 验证，禁止仅给叠层限帧而实际全场景持续全速运行。
- 离屏或弹框完全遮挡时停止无意义绘制；document hidden 遵循 SCREEN 后台契约。可见性优化不得暂停后台已接纳业务命令的必要处理，需将业务与绘制策略分离。
- 恢复时丢弃隐藏时间导致的超大动画 dt 或按既有安全时钟恢复；无瞬移追赶、累计巨量 RAF/定时器、额外命令 replay。
- 资源失败显示错误和明确重试入口，不无限重试；拒绝空白但伪装 ready。低性能可保留末帧并标注“预览已暂停”，不得把失败变成截图式成功。
- 构建前记录资源快照并协调唯一重型构建；不因预览重启后端、不读取他人证据目录、不抢锁/终止进程。

## 8. 接入前需关闭的契约项
- SCREEN 独立 ACCEPT exact SHA/tree 与正式路径交接。
- 单宿主换容器能否保留 runloop/角色以及非零尺寸提交（mock 不能替代真实浏览器）。
- 冷竖屏预览与既有 backend simulation 命令驱动隔离方案具备测试。
- 限帧/离屏策略不会改变既有业务回调语义。
上述项未关闭可实现纯组件与策略，不可将准备阶段成果描述为动态地图已上线。
