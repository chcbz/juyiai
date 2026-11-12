# 聚义厅可扩展地图遮挡系统方案

**状态：** 实施前设计基线（Explorer、Adversarial Reviewer、Architect 三方意见已合并）  
**日期：** 2026-08-03  
**范围：** `web/` 聚义厅地图渲染、TMX 遮挡元数据、遮挡资源、人物/道具层级排序、调试与验证；不改后端接口，不改变 `/agent/map` 与 `/agent/roster` 数据边界。  
**关联文档：**

- `docs/juyiting-runbook.md`
- `docs/juyiting-occlusion-system-execution-plan.md`
- `docs/juyiting-feature-guide.md`
- `docs/juyiting-immersive-fullscreen-map-design.md`
- `docs/superpowers/specs/2026-07-11-juyiting-unified-map-and-agent-simulation-design.md`

---

## 1. 决策摘要

当前聚义厅遮挡实现不是严格的遮罩系统，而是“任意 mask 命中后把整个人物切换到低 depth 区间”。该模型无法表达“人物在桌子前、同时在栏杆后”，也无法随地图扩展稳定维护。

本方案冻结为：

```text
renderSchemaVersion=2 + TMX 单一静态事实源
+ 统一规范化 SceneObject IR
+ 六个分区的无损遮挡图集
+ 可独立排序的 occluder-fragment
+ 人物、prop、fragment 统一稳定世界排序
+ floor/elevation/renderBand 首版即生效
+ 少量 target-specific OcclusionConstraintZone 处理不规则例外
+ 均匀网格空间索引和按需重排
```

不继续修补现有全局 `behindMask` 公式；不再依赖 prop 声明顺序；不构建全对象两两关系，也不在 idle 帧重复排序。普通关系使用显式地面接触点；复杂视觉结构优先继续拆片；只有分片仍无法表达时才增加目标明确的 polygon 约束。排序事务对全部 active `world` 对象执行确定性的稀疏约束排序，但 mandatory edge 只来自空间网格发现的有效 OcclusionConstraintZone。

首版固定六个 render band，顺序从后到前为：

```text
background → world → overhead → lighting → world-ui → screen-ui
```

v2 以整张场景为原子切换单位。迁移期只允许 v1 adapter 和 shadow renderer 做对照，禁止同一活动场景中的对象混用 v1/v2 排序语义。

## 2. 已核实的当前事实

### 2.1 地图和对象规模

`web/public/juyiting/hall.tmx` 当前设计空间为：

```text
104 × 58 tiles × 16 px = 1664 × 928
```

当前对象数量：

| 类别 | 数量 | 当前用途 |
| --- | ---: | --- |
| `mask` | 37 | 触发人物低 depth 公式 |
| `collision` | 38 | 视觉解析副本；实际移动主要使用 `nav_obstacles` |
| `nav_obstacles` | 38 | 移动和路径约束 |
| hotspot polygon | 5 | 地图业务入口 |
| prop tile object | 5 | 主座、点将名册、悬赏桌、书架、名册书 |
| regions | 8 | 人物活动区域 |
| patrol routes | 6 | 当前主要人物路线 |

### 2.2 当前 mask 实际只使用外接矩形

`web/src/game/tiledMap.js` 已保存 polygon 点和 origin，但 `web/src/game/scenes/HallScene.js` 的 `_sortByDepth()` 仅判断：

```js
agent.pos.x >= occ.x && agent.pos.x <= occ.x + occ.width
agent.pos.y >= occ.y && agent.pos.y <= occ.y + occ.height
```

因此当前所谓“进入 mask”实际上是进入 polygon 的 AABB。复杂 mask 的矩形空白区域也可能误触发。

### 2.3 当前人物使用两套不连续 depth 公式

```js
if (behindMask) {
  agent.depth = 1.5 + normY * 1.0
} else {
  agent.depth = 2.0 + normY * 3.5
}
```

以 `y=420`、场景高度 `928` 为例：

```text
mask 外：3.584
mask 内：1.953
```

这不是 depth 除以 2，而是切换到另一套低层级公式。人物跨越 mask 边界时会发生非连续跳变。

### 2.4 当前 prop 按 TMX 声明顺序固定 depth

`HallScene.js` 当前从 `3` 开始，每个 prop 增加 `0.5`：

```text
主座       3.0
点将名册   3.5
悬赏桌     4.0
书架       4.5
名册书     5.0
```

该顺序与物体实际地面基线无关。

### 2.5 两张遮挡图完全相同

以下两个文件 SHA256 完全相同：

```text
web/public/juyiting/images/liangshan-hall-mid-occluders-v3.webp
web/public/juyiting/images/liangshan-hall-foreground-occluders-v3.webp
```

已核实摘要：

```text
3e4f3f90b4d84411a844978237a7d3530bd481c37a62bcd73b9d694a7d2dd432
```

同一批非透明像素当前分别在 depth `2` 和 `5` 被绘制。mid/foreground 的概念没有对应不同的视觉内容，不能作为后续扩展基础。

---

## 3. 问题定义

当前系统存在以下系统性问题：

1. 任意 mask 只产生一个全局 `behindMask` 布尔值，没有目标遮挡物。
2. mask polygon 被降级为 AABB，产生误判。
3. 人物一旦进入 mask，会同时落到桌子、栏杆、前景图等多个无关对象后面。
4. prop 使用声明顺序而不是空间关系排序。
5. 整张遮挡图只能有一个固定 depth，无法让不同建筑片段分别参与排序。
6. 同一张遮挡图被重复绘制到两个 depth。
7. 当前测试只覆盖资源和固定 layer，缺少真实 polygon、人物/prop 排序和全图视觉回归。
8. 现有模型依赖当前单张地图尺寸和固定图层名，后续扩展会继续增加硬编码。

右上悬赏桌只是最明显的实例，不是独立问题。全地图的柱子、栏杆、桌子、书架、墙沿和前门结构都受同一缺陷影响。

---

## 4. 目标与非目标

### 4.1 目标

- 人物、prop 和遮挡结构使用同一套世界排序规则。
- 能表达“桌子在人物后、栏杆在人物前”等局部关系。
- 37 个现有 mask 全部被审计、命名和迁移，不遗漏区域。
- 新增普通单层地图区域时，只编辑 TMX 和资源，不修改排序核心代码。
- 保持地图移动、路线、热点、相机和业务数据流不变。
- 新系统在 108 人压力场景下无明显帧率退化。
- 遮挡资源不显著增加现有页面网络加载体积。

### 4.2 非目标

- 本次不替换 melonJS。
- 不为未来楼层、高台、楼梯、桥、动态门和大地图分区预留结构；新增区域按当前单层地图结构增量扩展，portal/多楼层状态机不在本次范围（见第11章）。
- 本次不重构 `/agent/map`、roster、任务和聊天数据流。
- 本次不合并或重画全部导航数据。
- 本次不把 `collision` 和 `nav_obstacles` 合并为新的运行时体系；只增加一致性校验，避免遮挡改造影响路线。
- 本次不默认实现支持任意 3D 交叉关系的完整场景图。
- 不为当前 37 个 mask 编写 `if (maskId === ...)` 的代码特例。

---

## 5. 总体架构

### 5.1 固定渲染层级

render band 只表达大层级，不表达对象的局部前后关系。顺序固定为：

| `renderBand` | `renderBandOrder` | 用途 |
| --- | ---: | --- |
| `background` | 0 | 地板、不可交互底图 |
| `world` | 100 | agent、prop、occluder-fragment、动态世界对象 |
| `overhead` | 200 | 永远位于普通世界对象上方的屋顶、顶棚等结构 |
| `lighting` | 300 | 光照、色彩覆盖层 |
| `world-ui` | 400 | 跟随世界坐标的名称、气泡、hotspot 反馈 |
| `screen-ui` | 500 | 固定屏幕坐标的 HUD、面板 |

不得再增加 `world-back`、`roof`、`always-back`、`always-front` 等重叠表达。需要普通空间排序的对象进入 `world`；确实必须覆盖整个世界层的静态结构进入 `overhead`。

### 5.2 唯一排序契约

所有可排序 SceneObject 使用同一个全序键：

```text
renderBandOrder
→ floorOrder
→ elevation
→ fixedPoint(sortAnchor.y)
→ bounded tieBias
→ stableId ASCII byte order
```

冻结定义：

- `floorOrder` 来自地图级 floor registry，当前只有 `floor-1 → 0`；未知 floorId 为 fatal。
- `elevation` 是相对当前 floor 基准面的**有符号整数世界像素**；当前对象全部为 `0`。
- `fixedPoint(sortAnchor.y) = round(sortAnchor.y × 256)`，避免浮点微差造成跨平台不稳定。
- `tieBias` 是 `[-32, 32]` 的整数，默认 `0`，只在前四项完全相同、即 fixed-point Y 相等时参与比较；超界为 fatal。
- `stableId` 按 ASCII 字节升序比较，作为最终确定性 tie-break。
- 排序完成后，renderer 按顺序分配连续整数 depth；业务语义不再依赖 `1.5～5.5` 之类浮点区间。
- `chunkId` 仅用于资源、裁剪和空间索引，绝不参与视觉排序。

```ts
type WorldSortKey = {
  renderBandOrder: 0 | 100 | 200 | 300 | 400 | 500
  floorOrder: number
  elevation: number
  fixedPointY: number
  tieBias: number
  stableId: string
}
```

### 5.3 `sortMode` 的单一职责

`sortMode` 只描述 `sortAnchor` 的更新算法：

- `fixed`：接触点来自 TMX/IR，运行期间不随对象位置变化；用于静态 prop、fragment 和结构。
- `y`：接触点随对象运行时位置更新；用于 agent 和可移动世界对象。

render band、polygon 约束与 `sortMode` 相互独立。polygon 约束是独立的 `OcclusionConstraintZone`，不会把 fragment 改成另一种 sort mode。

### 5.4 为什么不构建全对象关系图

当前聚义厅是单层静态地图，绝大部分遮挡关系可由独立视觉片段和地面接触点解决。系统不为任意对象对建立前后边，也不每帧重建关系。

冻结流程是：

```text
空间网格发现当前有效 zone
→ 为全部 active world 对象计算基础全序键
→ 仅添加稀疏 mandatory edge
→ 事件触发时执行确定性 Kahn 排序
```

Kahn 的**节点作用域固定为全部 active `world` 对象**，不是局部子图；这样不需要定义存在歧义的“局部结果如何合并回全局”。空间网格只负责缩小 zone/fragment 的发现范围，避免 `agents × all-map fragments/zones` 扫描；基础全序不展开成两两边。

只有人物移动、跨 cell、约束 membership 变化、动态对象移动、chunk 状态或场景配置变化时才启动排序事务。

## 6. 通用 Scene Object 模型

parser/runtime adapter 输出统一对象：

```ts
type SceneRender =
  | {
      type: 'asset'
      assetRef: string
      sourceRect?: Rect
      destinationRect: Rect
      anchor?: Point
    }
  | {
      type: 'procedural'
      rendererKey: string
      destinationRect: Rect
      styleRef?: string
    }

type SceneObject = {
  stableId: string
  sourceEntityId?: string
  sceneId: string
  chunkId: string
  kind: 'agent' | 'prop' | 'occluder-fragment' | 'structure' | 'hotspot'

  renderBand: 'background' | 'world' | 'overhead' | 'lighting' | 'world-ui' | 'screen-ui'
  floorId: string
  elevation: number
  sortMode: 'fixed' | 'y'
  sortAnchor: { x: number, y: number }
  tieBias: number

  render?: SceneRender

  geometry?: {
    footprint?: Point[]
    hitArea?: Point[]
    visualClip?: Point[]
  }

  navigation?: {
    blocksMovement: boolean
  }

  interaction?: {
    hotspotId: string
    panel: string
  }
}
```

### 6.1 必填与命名规则

- 所有生产对象必须有唯一且不可变的 `stableId`。
- `stableId` 必须匹配 `^[a-z0-9][a-z0-9._-]{2,95}$`，禁止使用 Tiled 数字 ID、数组下标或声明顺序生成。
- 推荐命名：`jyt.<kind>.<chunk>.<semantic-name>.v<schema-revision>`。
- 示例：`jyt.occ.east-upper.railing-01.v1`、`jyt.zone.east-upper.railing-01.behind.v1`、`jyt.prop.bounty-board.v1`。
- `fixed` 和 `y` 对象都必须有显式 `sortAnchor`；它表示脚底或地面接触点，不能由图片底边、AABB 中心或数组位置隐式推断。
- `tieBias` 只能解决完全相同 fixed-point Y 的视觉并列，不得拿来修补错误接触点。
- `render.type='asset'` 时 `assetRef` 必填且 sourceRect 不得越界；`render.type='procedural'` 时 `rendererKey` 必填；纯交互对象可不提供 render。
- polygon 必须至少三个有效点，并转换为统一世界坐标。
- 所有坐标基于 TMX 的 coordinateWidth/coordinateHeight，不得将 `1664×928` 写死到通用排序模块。
- v2 缺少其对象类型所要求的 stableId、assetRef/rendererKey、floor registry 项或对象引用时，返回结构化 fatal，不允许只告警后继续。

### 6.2 Runtime Agent Adapter

地图 Agent 继续只来自 `/agent/map`，不引入 `/agent/active`，也不与 roster 数据流合并。runtime adapter 规则冻结为：

- `sourceEntityId` 原样保存 API 返回的 agent ID 字符串，不 trim、不改大小写、不做 Unicode normalization；排序身份生成时按其 UTF-8 字节处理。
- `stableId = 'jyt.agent.' + base32lower(sha256(UTF8(sourceEntityId))) + '.v1'`。
- adapter 必须维护 stableId→sourceEntityId 反查表；重复 sourceEntityId、stableId 冲突或缺失 ID 均为 fatal。
- 初始 floorId/elevation 由可信 spawn resolver 给出；当前固定为 `floor-1/0`。
- 初始 chunkId 由世界坐标和 TMX chunk registry 解析，不能信任 API 任意覆盖。
- 普通 Agent 位置更新可修改 sortAnchor 和由可信 chunk resolver 推导出的 chunkId。
- floorId/elevation 只能由未来可信 portal/movement resolver 原子修改；普通 Agent 快照不得直接覆盖。
- stableId、sourceEntityId、kind、renderBand、sortMode、tieBias 和静态资源身份在对象生命周期内不可变。

## 7. Occluder Fragment 与 OcclusionConstraintZone

### 7.1 可绘制遮挡片段

```ts
type OccluderFragment = {
  stableId: string
  sceneId: string
  chunkId: string
  floorId: string
  elevation: number
  renderBand: 'world' | 'overhead'
  sortMode: 'fixed'
  sortAnchor: { x: number, y: number }
  tieBias: number
  assetRef: string
  sourceRect: Rect
  destinationRect: Rect
  visualClip?: Point[]
}
```

每个 `occluder-fragment` 是可独立排序的视觉表面和独立 Renderable，可以与人物、prop 一起排序。若同一图片区域需要同时位于不同人物前后，必须继续拆片或使用针对该 fragment 的局部约束，不能给共享 fragment 设置全局前/后状态。

`overhead` fragment 不进入 `world` Kahn 图，也不能成为 OcclusionConstraintZone 的 target；只有 `renderBand='world'` 的 fragment 可被约束。

### 7.2 OcclusionConstraintZone 模型

```ts
type OcclusionConstraintZone = {
  stableId: string
  sceneId: string
  chunkId: string
  floorId: string
  targetFragmentId: string
  relation: 'behind' | 'front'
  priority: number
  polygon: Point[]
  bounds: Rect
  hysteresisPx: 3
}
```

约束只改变**当前 agent 与 targetFragment**的相对顺序：

```text
relation=behind  → agent < targetFragment
relation=front   → targetFragment < agent
```

不得修改共享 fragment 的全局 depth 或状态。因此两个 agent 位于同一 fragment 两侧时，可以同时得到：

```text
agent-A < targetFragment < agent-B
```

scope 规则：

- zone 必须显式给出 sceneId、floorId、chunkId，或在 parser 中从其对象组继承后固化到规范化 IR。
- targetFragment 必须满足 `renderBand='world'`，并与 zone 处于同一 sceneId、floorId；指向 overhead、跨 scene 或跨 floor 均为 structured fatal。
- runtime 只为与 zone 同 sceneId、floorId 的 agent 计算 membership 和生成边；任何跨 scene/floor 的 edge 生成尝试均为运行时不变量 fatal。
- 跨 chunk 引用仅在 manifest 明确声明 fragment 跨边界且仍只有一个权威 stableId 时允许。
- `priority` 是有符号整数。多个同向有效约束先按 priority 降序、再按 stableId ASCII 字节升序确定权威来源，便于确定性调试。
- 同一 agent/target 在同一空间可能同时得到 `behind` 与 `front` 时，属于配置冲突，必须在静态几何验证中报 fatal；不得运行时任选一条。

### 7.3 Polygon 判断、有效性与固定迟滞

parser 先把 polygon 转换为 1/256 世界像素定点坐标：

```js
worldPoints = localPoints.map(point => ({
  x: round((originX + point.x) * 256),
  y: round((originY + point.y) * 256)
}))
```

canonicalization 可移除一个与首点完全相同的尾点；之后 validator 必须拒绝：

- 少于三个唯一点；
- 相邻重复点或零长度边；
- 自相交 polygon；
- 绝对面积小于 1 平方世界像素；
- 以欧氏半径 3px 做 Minkowski erosion 后没有非空内部面积的过窄 zone。

运行时先做 AABB broad phase，再做固定点 even-odd point-in-polygon 和边界判断。对脚点 `p` 计算到全部非退化边线段的最小**欧氏距离** `dMin`；凹角和顶点自然取所有线段距离的最小值。定义有符号距离：

```text
signedDistance(p, polygon) =
  +dMin   p 在内部
   0      p 在边界
  -dMin   p 在外部
```

迟滞固定为 **3 个世界像素**：

- 初次采样：signedDistance≥0 按 inside，<0 按 outside；因此边界初始按 inside。
- previous=outside：只有 signedDistance≥+3 才切到 inside，否则保持 outside。
- previous=inside：只有 signedDistance≤-3 才切到 outside，否则保持 inside。
- 等于 ±3 时执行切换。

距离在世界坐标中计算，不受相机缩放、设备像素比或画布分辨率影响。

### 7.4 稀疏约束排序与无环硬门禁

排序算法冻结为：

1. 为活动对象计算基础全序键；
2. 只从当前有效且 agent/zone/targetFragment 同 scene、同 floor、target 位于 world band 的 OcclusionConstraintZone 生成 mandatory edge，不把基础全序展开成两两边；
3. 合并重复同向边，直接相反边立即 fatal；
4. 对**全部 active `world` 对象**执行 Kahn 拓扑排序，所有当前入度为 0 的对象使用基础全序键作为优先队列顺序；
5. 无局部约束时结果与基础全序完全一致；存在约束时，只保证 mandatory edge 和确定性优先队列，不修改共享 fragment 状态；
6. 输出数量少于输入对象数即表示存在环，整个事务失败。

该算法的节点覆盖全部 active `world` 对象，但边仅来自当前有效约束，因此是全活动集、稀疏边的 constraint resolver，不是任意对象两两关系图。zone 候选仍必须来自空间网格，禁止 agent 扫描全地图 zone/fragment。

以下均为 fatal：

- 静态约束分析发现环；
- 重叠 polygon 产生相反关系；
- 激活前组合场景验证发现环；
- 运行时事务发现未被静态验证覆盖的环。

验证失败时不得使用 stableId 或旧 depth 公式静默打破环。激活前失败则拒绝新场景；运行时不变量失败则拒绝该帧事务、保留上一完整帧并进入明确错误状态，同时阻止该地图版本发布。

## 8. 遮挡资源方案

### 8.1 当前地图与 canonical source

不再同时绘制两张内容相同的全场景遮挡图。六个 atlas 的唯一权威输入冻结为：

```text
assetRef: jyt.occlusion-source.hall-v3
path: web/public/juyiting/images/liangshan-hall-mid-occluders-v3.webp
fileSha256: 3e4f3f90b4d84411a844978237a7d3530bd481c37a62bcd73b9d694a7d2dd432
```

该三元组必须写入生成 manifest 和发布校验。`liangshan-hall-foreground-occluders-v3.webp` 只是当前重复 legacy 资源，不是 canonical source，v2 切换后删除。

若未来确需修改源图，必须显式创建新的 assetRef/version、记录新 SHA-256、重新生成全部 atlas 并重新走 RGBA/截图评审；禁止只同时替换“源图+atlas”来绕过金线。

首版固定：

```text
六个分区的 lossless WebP/PNG atlas
+ sourceRect/destinationRect
```

### 8.2 面向地图扩展的推荐方案

既然后续地图会扩大，不建议长期维持一张无限增长的全图 atlas。建议按区域拆分：

```text
web/public/juyiting/images/occluders/
├── center-v1.webp
├── west-upper-v1.webp
├── west-lower-v1.webp
├── east-upper-v1.webp
├── east-lower-v1.webp
└── entrance-v1.webp
```

对应 `chunkId`：

```text
center
west-upper
west-lower
east-upper
east-lower
entrance
```

扩建后新增 chunk，而不是重做整个大厅遮挡图。

### 8.3 切片规则

- 单根柱子是一个 fragment。
- 水平栏杆按视觉前沿分为一个或多个 fragment。
- 斜墙、楼梯和斜栏杆拆成多个短片段，每片具有稳定基线。
- 每个非透明像素应只归属一个 fragment，避免重复加深。
- sourceRect 周围保留 1～2 像素透明 padding，防止纹理采样接缝。
- 运行时复用已加载 atlas，不为每个 fragment 发起独立请求。
- 图集离线生成必须将全部 fragment 重建为完整遮挡平面，并与 canonical source 解码后的 RGBA 逐像素、逐通道完全一致；任一像素差异均阻断发布。生成图集只允许使用 lossless WebP 或 PNG。
- 跨 chunk 的同一个 fragment 只能有一个权威 stableId，可以登记到多个空间索引 cell，但不能复制成多个 SceneObject。

---

## 9. 当前 37 个 mask 的迁移范围

所有旧 mask 都必须进入审计清单：

| 地图区域 | mask IDs | 数量 |
| --- | --- | ---: |
| 西北 | 48、70 | 2 |
| 北中 | 54、71 | 2 |
| 东北 | 57、72、73 | 3 |
| 西中 | 49、52、53、69、83、84 | 6 |
| 中央 | 55 | 1 |
| 东中 | 56、58、59、74、76～80 | 9 |
| 西南 | 50、51、67、68 | 4 |
| 南中 | 61～66 | 6 |
| 东南 | 60、75、81、82 | 4 |
| **总计** |  | **37** |

每个 mask 必须完成：

1. 添加语义名称和唯一 `stableId`；
2. 对照遮挡图确定对应视觉结构；
3. 判断是否可完全转换为普通 fragment `sortAnchor.y`；
4. 若不能，设置明确 `targetFragmentId`；
5. 使用真实 polygon，而不是外接矩形；
6. 记录 behind、boundary、front 三个验收点；
7. 纳入自动化几何测试和浏览器截图审计。

现有 polygon 是迁移素材，不自动视为正确答案。大型不规则区域必须对照实际非透明像素重新校准。

---

## 10. 五个 Prop 的迁移

当前 prop 初始基线候选：

| Prop | TMX rect | 初始 `sortAnchor.y` 候选 |
| --- | --- | ---: |
| `main-seat-rect` | y=175, h=93 | 268 |
| `agent-roster-rect` | y=601, h=136 | 737 |
| `bounty-board-rect` | y=255, h=124 | 379 |
| `library-shelf-rect` | y=578, h=141 | 719 |
| `roster-book-rect` | y=192, h=192 | 384 |

最终 `sortAnchor.y` 必须以物体实际接触地面的前沿为准，不能直接信任图片矩形底边。每个 prop 必须验证人物从上、下、左、右经过时的排序。

右上悬赏桌的目标关系为：

```text
桌子基线约 379
人物脚点约 420
栏杆前沿约 458

桌子 < 人物 < 栏杆
```

---

## 11. 楼层、平台和未来地图扩展

### 11.1 单层横向扩建

新增普通房间、柱子、桌子和栏杆时，仅增加：

- chunk 资源；
- TMX SceneObject；
- fragment 的 `sortAnchor`；
- 必要的 `OcclusionConstraintZone`。

不修改核心排序代码。当前六个 chunk 全部常驻；扩建时可增加 chunk，但 stableId、floor registry 和排序契约不变。

### 11.2 多楼层、高台、桥和楼梯

`floorId` 和 `elevation` 从 v2 第一版就参与排序，不是只解析不生效：

```text
renderBandOrder
→ floorOrder
→ elevation（有符号整数世界像素）
→ fixedPoint(sortAnchor.y)
→ tieBias
→ stableId
```

当前 floor registry 冻结为：

```text
floor-1 → floorOrder 0
```

当前所有对象 `elevation=0`。未来增加楼层时必须在 TMX 地图级 registry 声明唯一 floorOrder；重复 order 或未知 floorId 均为 fatal。

楼梯和入口未来负责人物 floor/elevation 状态切换：

```text
ON_FLOOR_A → IN_PORTAL(A,B,progress) → ON_FLOOR_B
```

禁止瞬时修改 floorId 造成层级跳变。portal 状态机不在本次实现范围内，但 schema 已保留扩展点。

### 11.3 动态门和移动物体

动态世界对象使用 `sortMode='y'`。只在位置变化、跨越空间格或关系变化时重新计算排序，不要求静态对象每帧重排。未来移动门或家具必须让 render、collision、navigation 和空间索引在同一帧事务中提交，避免“看得见但撞不到”。

### 11.4 大地图资源加载

当前版本冻结六个 chunk 资源结构并全部常驻，不提前引入流式加载。未来地图显著扩大时，保持同一 manifest 接口再启用：

- 当前 chunk 常驻；
- 相邻 chunk 预加载；
- 远处 chunk 延迟加载或释放；
- interaction、occlusion 和 navigation 使用同一 chunkId；
- 跨 chunk fragment 仍只有一个权威 SceneObject，不复制视觉或排序身份。

## 12. 解析、激活与帧事务

### 12.1 单一规范化 IR

TMX 是静态场景唯一事实源，并新增独立的：

```text
renderSchemaVersion=2
```

不得复用 `movementSchemaVersion`。XML parser 与 melonJS/预解析输入必须归一到同一个规范化 SceneObject IR。两条输入路径产生的 canonical serialized IR 必须**字节完全一致**，包括字段顺序、数字格式、默认值展开和对象排序；仅“语义相近”不算通过。

动态 Agent 快照只允许更新位置、可见性、动画等白名单字段。chunkId 只能由可信 chunk resolver 根据位置推导；floorId/elevation 只能由可信 portal/movement resolver 原子更新；stableId、sourceEntityId、renderBand、sortMode、tieBias 和静态资源身份不可由快照覆盖。渲染元数据不能成为热点、任务或 Agent 操作的权限依据。

### 12.2 v1/v2 边界

迁移期允许：

```text
legacy TMX → v1 adapter → normalized IR → shadow renderer comparison
```

但活动场景只能整体使用 v1 或整体使用 v2。禁止五个 prop 已用 v2、fragment 仍用 v1 公式之类混合对象语义。atomic v2 switch 之前，v2 只在 shadow/测试路径运行。

### 12.3 地图激活状态

```text
parsed → canonicalized → validated → assetsReady → instantiated → active
```

v2 缺少 stableId、floor registry 项、targetFragment 或任一必需引用时必须 structured fatal；仅当 `render.type='asset'` 时缺少 assetRef 为 fatal，仅当 `render.type='procedural'` 时缺少 rendererKey 为 fatal。错误必须包含 sceneId、objectId、field、errorCode。

任何验证失败都不得实例化或展示部分场景：

- 已有 active scene：保留上一完整场景，不切换；
- 没有 active scene：显示完整、可诊断的错误状态，不显示半张地图；
- 资产加载或实例化失败：销毁 staging scene，不污染 active scene。

### 12.4 帧事务

单帧按以下边界提交：

```text
冻结位置快照
→ 更新空间索引和 zone membership
→ 生成基础全序键与局部约束边
→ 无环校验并计算完整稳定顺序
→ 一次性提交连续整数 depth
→ draw
```

不得在一帧绘制过程中逐个对象改变关系。事务失败时保留上一完整帧并进入明确错误状态，不能部分提交。

## 13. 性能模型

### 13.1 空间索引

使用均匀网格，初始 cell 尺寸由基准测试在 128×128 与 256×256 世界像素中选择并写入常量。每个 cell 记录：

- occluder-fragment；
- OcclusionConstraintZone；
- prop；
- hotspot。

人物只查询当前和相邻 cell。fragment 可登记到多个 cell，但仍只有一个 SceneObject 和 stableId。

### 13.2 更新策略

重新计算候选与顺序的触发条件：

- 人物位置变化；
- 人物跨越空间 cell；
- dynamic object 移动；
- chunk 加载或卸载；
- scene object 配置变化。

idle 人物不重复运行全部 polygon 检测。生产 instrumentation 必须能证明不存在 `agents × all-map fragments/zones` 扫描。

### 13.3 固定性能门禁

基准环境和负载冻结为：

```text
构建：production build
主机：当前测试/部署主机
浏览器：Chromium 自动化测试 harness
视口/世界基线：1664×928
负载：108 agents、50 fragments、37 zones
预热：10 秒
采样：60 秒
```

只统计 world ordering + spatial-index update：

```text
p95 ≤ 2.0 ms
p99 ≤ 4.0 ms
```

同时要求：

- instrumentation 证明没有全图笛卡尔扫描；
- 无持续 GC 抖动；
- draw call、JS heap、texture memory 与网络体积均有迁移前后基线；
- 不得因重复遮挡图增加网络资源；
- debug overlay 默认关闭且不进入生产热路径。

## 14. 名称、气泡和选中效果

产品规则在本方案中直接冻结：

| 内容 | renderBand | 参与物理遮挡 |
| --- | --- | --- |
| 人物身体 | `world` | 是 |
| 脚下选中圈 | `world` | 是，与人物身体保持绑定顺序 |
| 人物名称 | `world-ui` | 否，始终可见 |
| 对话气泡 | `world-ui` | 否，始终可见 |
| Hotspot 反馈文字 | `world-ui` | 否，始终可见 |
| HUD/面板 | `screen-ui` | 否 |

`world-ui` 内部按跟随对象的 `floorOrder/elevation/fixedPoint(sortAnchor.y)/stableId` 稳定排序，但不受 `world` 中桌子、栏杆、fragment 的局部约束影响。`lighting`、`world-ui`、`screen-ui` 的 band 顺序不得被 world sort 改写。

## 15. 调试能力

新增开发环境遮挡调试开关，至少显示：

- 人物脚点；
- 人物完整 sort key；
- fragment 边界、stableId 和 `sortAnchor.y`；
- OcclusionConstraintZone polygon、priority 和 targetFragmentId；
- 当前命中的空间 cell；
- 当前 agent 与目标 fragment 的 front/behind 边；
- 迟滞 membership 的前一状态和当前状态；
- structured fatal、冲突约束和循环路径。

建议支持：

```text
?jytOcclusionDebug=1
```

调试显示只在开发环境启用。生产环境保留低成本计数器用于证明不存在全图扫描，但不渲染 overlay。

## 16. 实施阶段

迁移顺序必须保持原子边界：

```text
normalized IR + shadow renderer
→ migrate 5 props
→ generate fragments/atlases
→ complete all required OcclusionConstraintZone objects
→ full-map calibration
→ atomic v2 switch
→ remove legacy formulas/resources
```

### Phase 0：测试、观测和生产等价基线

- 锁定已对齐的 production-equivalent TMX/资产作为截图基线；
- 记录 37 mask、5 prop、重复遮挡资源、网络、内存和 draw call 基线；
- 建立真实 polygon、固定迟滞、排序全序、无环和 stableId 测试；
- 建立 camera、hit-test、pointer routing、lighting/UI 回归；
- 增加 debug overlay 和性能 instrumentation。

### Phase 1：规范化 IR、validator 和 shadow renderer

- 冻结 renderSchemaVersion=2、floor registry、render band 和排序契约；
- 定义 SceneObject、SceneRender、Runtime Agent Adapter、OccluderFragment、OcclusionConstraintZone；
- XML 与预解析输入生成字节一致的 canonical IR；
- 完成 runtime Agent 身份、条件 assetRef/rendererKey、scope、sourceRect、polygon signed-distance/erosion、冲突和无环 fatal 校验；
- v1 adapter 和 v2 shadow renderer 只做对照，不接管活动场景。

### Phase 2：迁移五个 Prop

- 在 v2 shadow path 中为五个 prop 标注显式 sortAnchor；
- 验证人物从上、下、左、右经过时的关系；
- 验证对象声明顺序、插入顺序和输入路径不改变结果；
- 活动场景仍保持完整 v1，避免混合语义。

### Phase 3：生成 Fragment 和六个无损 Atlas

- 从冻结 assetRef+SHA-256 的 canonical source 按六个 chunk 生成 lossless WebP/PNG；
- 将遮挡视觉拆成可独立排序的 occluder-fragment；
- 为 37 个旧 mask 建立 stableId、视觉结构对应、sortAnchor 和验收探针；
- 执行 reconstructed plane 与 canonical source 的 RGBA 精确相等门禁。

### Phase 4：补齐全部必要 OcclusionConstraintZone

- 只为继续拆片仍无法表达的区域增加 target-specific OcclusionConstraintZone；
- 冻结 behind/front、scope、priority、stableId、3px 迟滞规则；
- 静态检查重叠冲突和循环；
- 验证多人位于同一目标 fragment 两侧时关系同时正确。

### Phase 5：全地图校准和固定性能基准

每个遮挡物验证 `behind/boundary/front`，覆盖九宫区域：

```text
西北、北中、东北
西中、中央、东中
西南、南中、东南
```

完成 108 agents、50 fragments、37 zones 的 10s 预热 + 60s Chromium 基准，并满足 p95/p99 门禁。

### Phase 6：原子 v2 切换

- staging scene 通过全部 schema、asset、RGBA、几何、视觉、性能和功能门禁后，整图一次性切换到 v2；
- 人物、prop、fragment 使用同一排序契约；
- 不允许逐对象灰度启用；
- 切换失败时保留上一完整 active scene。

### Phase 7：Legacy 清理、独立复核和发布

- 删除全局 `behindMask` 双 depth 公式；
- 删除 `propDepth += 0.5`；
- 删除重复全图遮挡资源和不再引用的 v1 runtime 分支；
- 保持 nav nodes、edges、slots、routes 和 movement 数据不变；
- 运行测试、生产构建、截图、性能和线上 smoke；
- 由只读 Reviewer 与 Release Guard 审查，通过后部署、提交和推送。

## 17. Agent 分工和执行策略

遵循 `docs/implementation/MODEL_ROUTING.yaml` 的串行执行、单写入 Owner 和写审分离原则。

| 顺序 | Agent 角色 | 职责 | 写入范围 |
| ---: | --- | --- | --- |
| 1 | `explorer` | 再确认代码入口、资产引用、测试缺口和无关改动边界 | 只读 |
| 2 | `critical_worker` | normalized IR、validator、atomic activation、排序与约束核心、核心测试 | JS/TS 和相关测试 |
| 3 | `routine_worker` | 按冻结 schema 处理 37 个 stableId、TMX 属性、fragment manifest 和机械性测试数据 | TMX、资产 manifest、定向测试 |
| 4 | `balanced_worker` | HallScene 集成、六 atlas 接入、全图视觉校准和性能优化 | 场景代码、TMX/资产定向调整 |
| 5 | `test_runner` | 测试、构建、RGBA 校验、截图、压力和 smoke | 只读验证 |
| 6 | `adversarial_reviewer` | 攻击排序错误、循环、AABB 假命中、遗漏区域、partial scene 和资源重复 | 只读审查 |
| 7 | 对应原 Writer | 修复 Reviewer 问题，不扩大写入范围 | 原允许范围 |
| 8 | `release_guard` | atomic migration、集成和生产发布门禁 | 只读门禁 |

执行必须串行，一次仅一个 active task。禁止两个写入 Agent 同时修改 `HallScene.js` 或 `hall.tmx`；每次 handoff 必须携带 commit、changed files、测试结果和残余风险。

---

## 18. 工作量估算

当前调查和根因定位已经完成。剩余估算：

| 工作项 | 预计工作量 |
| --- | ---: |
| schema、runtime Agent adapter、测试和 debug 基线 | 1～1.5 agent-day |
| parser、激活事务、统一排序和 constraint resolver | 1.5～2 agent-day |
| 六区资源、37 个区域和五个 prop 数据迁移 | 2～3 agent-day |
| 全地图视觉与 polygon 距离校准 | 1～2 agent-day |
| 性能、回归、独立复核和发布 | 1～1.5 agent-day |
| **合计** | **6.5～10 agent-day** |

如果现有遮挡资源无法可靠分片、需要重新制作视觉资产，预留：

```text
8～12 agent-day
```

主要不确定性是美术片段边界和 37 个区域的逐个校准，不是排序代码本身。

---

## 19. 测试与验收门禁

### 19.1 Parser/schema/activation

- renderSchemaVersion=2 与 renderer 匹配；
- XML 与预解析输入的 canonical serialized IR 字节完全一致；
- stableId 匹配 `^[a-z0-9][a-z0-9._-]{2,95}$`，不可变且场景内唯一；
- floor registry 唯一，当前 `floor-1 → 0`；
- elevation 为有符号整数世界像素；
- tieBias 为 `[-32,32]` 整数；
- polygon 全部 canonicalize 为 1/256 世界像素定点坐标；
- OcclusionConstraintZone scope、targetFragment 和 priority 合法；target 必须在 world band，且 zone/target 同 scene、同 floor；
- `fixed`/`y` 对象都有显式 sortAnchor；
- runtime Agent adapter 保留 sourceEntityId 原值并生成确定、唯一、可反查的哈希 stableId；
- sourceRect 不越界，chunkId/floorId/renderBand 合法；
- 缺失 stableId/引用，或 asset render 缺 assetRef、procedural render 缺 rendererKey，产生 structured fatal；
- 任一失败均不实例化 partial scene，并保留上一 active scene或显示完整错误态。

### 19.2 几何和约束

每个 polygon 覆盖：

- 内部点；
- 边界点；
- AABB 内但 polygon 外部的点；
- 完全外部点；
- outside→inside 深入不足/达到 3px；
- inside→outside 离开不足/达到 3px；
- 初次采样边界按 inside；
- signed distance 使用世界坐标最小欧氏线段距离，±3px 临界值执行切换；
- 自相交、退化边、面积过小及 erosion(-3px) 后无内部面积的 zone 为 fatal；
- 重叠相反关系为 fatal；
- 静态、激活前和运行时候选图均无环。

### 19.3 排序

- agent-agent Y-sort；
- agent-prop 上方/下方；
- agent-fragment front/behind；只允许 agent/zone/target 同 scene、同 floor且 target 位于 world band；
- 完整键顺序严格为 renderBandOrder/floorOrder/elevation/fixed-point Y/tieBias/stableId；
- tieBias 只在 fixed-point Y 相同时生效；
- 右上区域满足 `table < agent < railing`；
- zone 边界无明显 depth 跳变和闪烁；
- 不存在全局 mask 副作用；
- 两个人同时位于同一 fragment 两侧时，双方顺序同时正确；
- 插入顺序、TMX 声明顺序和重复运行不改变最终排序。

### 19.4 遮挡资源硬门禁

- canonical source 必须是 `jyt.occlusion-source.hall-v3`，文件路径和 SHA-256 与 §8.1 完全匹配；
- atlas 仅允许 lossless WebP 或 PNG；
- 所有 fragment 按 destinationRect 重建后的完整遮挡平面，与 decoded canonical source RGBA 逐像素、逐通道完全一致；
- 每个非透明像素只有一个权威 fragment owner；
- 无漏像素、重叠加深、透明边缘污染或采样接缝；
- 不再加载内容相同的 mid/foreground 全图资源。

### 19.5 全地图视觉

- 37 个旧 mask 全部对应验收记录；
- 九宫区域全部截图；
- 每个目标遮挡物至少 behind/boundary/front；
- 六个现有人物在高风险区域验证不同精灵透明轮廓；
- 桌面、移动端、缩放、拖拽和 camera transform 后结果一致；
- 名称、气泡、选择效果符合 world-ui 冻结规则；
- lighting、world-ui、screen-ui 不受 world sort 干扰；
- 截图基线使用已对齐的 production-equivalent TMX 和资产。

### 19.6 功能与性能回归

- 路线、停车位、home/queue slots 正常；
- collision/nav_obstacles 行为无变化；
- 五个 hotspot 点击、agent hit-test、pointer routing 和反馈正常；
- map agents 与 roster agents 数据流保持分离；
- Chromium 固定基准 p95 ≤ 2.0ms、p99 ≤ 4.0ms；
- instrumentation 证明无 `agents × all-map fragments/zones` 扫描；
- production build 通过；
- 部署后线上资源、地图和交互 smoke 通过。

## 20. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 片段边界切错 | 黑边、缝隙、重复加深 | lossless atlas、exclusive ownership、RGBA 精确重建门禁 |
| sortAnchor 误用图片底边 | 人物前后关系错误 | 显式标注地面接触点，逐 prop/fragment 验证 |
| polygon 仍被当 AABB | 大范围误遮挡 | 单元测试强制覆盖 AABB 内 polygon 外点 |
| 不规则结构无法由固定接触点表达 | 个别位置排序错误 | 先拆片，再使用 target-specific OcclusionConstraintZone |
| 约束冲突或循环 | 激活失败或运行时错误态 | 静态+激活前+运行时 fatal，无静默降级，修正数据后才发布 |
| v1/v2 混用 | 行为不可预测、难以回滚 | 仅 adapter/shadow 对照，整图原子切换 |
| 大地图 atlas 膨胀 | 加载慢、显存高 | 六 chunk manifest；当前常驻，未来按同一接口流式化 |
| 每帧全量 polygon 运算 | 108 人掉帧 | 均匀网格、移动触发、固定 p95/p99 门禁和扫描计数器 |
| 标签与身体层级不一致 | 视觉穿帮 | 名称/气泡固定 world-ui，单独回归 |
| 遮挡改造影响移动/点击 | 路线或交互回归 | 不改 nav 数据，增加 camera/hit-test/pointer regression |
| staging 资产不完整 | 半张地图或黑块 | 原子激活，失败保留上一 active scene或完整错误态 |

## 21. 专家评审意见汇总

### 21.1 Repository Explorer 意见

只读仓库盘点确认：

- 37 个 mask、38 个 collision、5 个 prop 当前缺少统一语义关联；
- mask、可见 image layer 和 prop 是彼此独立的数据流；
- prop 依赖 TMX 声明顺序；
- 当前测试没有覆盖真实遮挡结果；
- 后续应以 stable scene object 为中心，而不是继续维护匿名 mask。

本方案采纳了 stableId、明确对象关联、真实 polygon 和全地图覆盖矩阵。

### 21.2 Adversarial Reviewer 意见

独立对抗审查指出必须处理：

1. mid/foreground 两张资源完全相同；
2. 当前 polygon 被 AABB 替代；
3. 遮挡排序缺少直接测试；
4. 统一排序必须定义 tie-break 和边界稳定规则；
5. 五个 prop 迁移后必须逐个视觉验证；
6. polygon 检测必须有空间索引或更新节流；
7. labels 从人物 renderable 分离时必须冻结产品规则。

本方案已将以上内容列为实施和发布门禁。

### 21.3 Architect 意见

独立架构评审要求并已纳入本版：

- 冻结唯一排序契约和六个 render band，删除 band/sortMode 重叠表达；
- floor registry、elevation 单位、fixed-point 算法、tieBias 范围和 stableId 字节序必须可执行；
- XML 与预解析输入的 canonical serialized IR 必须字节一致；
- constraint 必须是 per-agent/targetFragment 边，不得修改共享 fragment；
- 3px 迟滞、冲突 fatal、无环 hard gate 不得留给实现自由发挥；
- v1/v2 只可通过 adapter/shadow 共存，活动场景必须原子切换；
- v2 资产和引用缺失不得产生 partial scene；
- fragment 资源必须通过 decoded RGBA 精确相等门禁；
- 性能基准需固定环境、负载、时长和 p95/p99；
- lighting、UI、camera、hit-test 和 pointer routing 必须纳入回归；
- 最终复核进一步冻结：全 active world 稀疏边 Kahn 作用域、Runtime Agent Adapter、条件 assetRef 契约、3px signed-distance 算法和 canonical source assetRef+SHA-256。

### 21.4 架构取舍意见

当前地图不默认上完整动态拓扑图。推荐顺序是：

```text
统一稳定全序键
→ 复杂视觉结构继续拆成独立 fragment
→ 仍无法表达时使用局部 target-specific OcclusionConstraintZone
```

只有未来出现大量动态遮挡物、跨层桥梁或无法通过 floor/elevation 和分片表达的交叉关系时，再评估把局部约束解析升级为更通用的渲染关系图。当前明确不引入 ECS、3D Z-buffer、逐像素 depth map、运行时图集打包、quadtree/R-tree 或任意规则语言。

## 22. 已冻结实施决策

以下不再作为实施期开放选项：

1. **名称和气泡：** 始终位于 `world-ui`，不参与物理遮挡。
2. **资源结构：** 直接采用 center、west-upper、west-lower、east-upper、east-lower、entrance 六个 chunk；当前全部常驻。
3. **floor/elevation：** 从 v2 第一版进入排序键；当前 `floor-1 → floorOrder 0`，所有对象 elevation=0。
4. **稳定 ID：** 匹配 `^[a-z0-9][a-z0-9._-]{2,95}$`，采用 `jyt.<kind>.<chunk>.<semantic-name>.v<revision>`。
5. **排序算法：** `fixedPoint(sortAnchor.y)=round(y×256)`，tieBias 为 `[-32,32]` 且只处理相同 fixed-point Y。
6. **Constraint：** 仅 per-agent/targetFragment，target 必须在 world band，agent/zone/target 必须同 scene、同 floor；priority 降序 + stableId 字节序；迟滞固定 3px；冲突和循环 fatal。
7. **Agent 身份：** `/agent/map` 原始 ID 保存在 sourceEntityId；stableId 使用原始 UTF-8 字节 SHA-256 的 lowercase base32；chunk/floor 只能由可信 resolver 更新。
8. **Polygon 距离：** 1/256 定点坐标、even-odd containment、到边线段最小欧氏 signed distance、±3px 切换；退化、自相交和 erosion(-3px) 为空均 fatal。
9. **Canonical source：** `jyt.occlusion-source.hall-v3` + 固定路径 + SHA-256 是六 atlas 唯一输入。
10. **性能基线：** production build、当前测试/部署主机、Chromium、1664×928、108 agents、50 fragments、37 zones、10s 预热、60s 采样，p95≤2.0ms、p99≤4.0ms。
11. **截图基线：** 使用 dev/prod 已对齐后的 production-equivalent TMX 与资产。
12. **激活策略：** staging 全门禁通过后整图 atomic v2 switch；失败保留上一 active scene，禁止 partial scene。
13. **资源保真：** atlas 仅使用 lossless WebP/PNG，重建平面与 canonical source decoded RGBA 精确相等。

## 23. 完成定义

只有同时满足以下条件，才能认为“整个地图遮挡问题已解决”：

- 37 个旧 mask 全部完成语义迁移和验收；
- 不再存在全局 `behindMask` 双公式；
- 不再使用 `propDepth += 0.5`；
- 不再同时绘制两张内容相同的全图遮挡图片；
- 所有普通世界对象使用冻结的统一稳定排序键；
- 复杂区域只影响明确的当前 agent 与 targetFragment；
- constraint 冲突和循环均为 fatal，无静默 fallback；
- 六个无损 atlas 通过 decoded RGBA 精确相等门禁；
- XML 与预解析路径生成字节一致的 canonical IR；
- runtime Agent 身份可确定生成、无碰撞且可反查 sourceEntityId；
- 3px signed-distance 迟滞和退化 polygon validator 通过；
- canonical source assetRef/path/SHA-256 门禁通过；
- 右上悬赏桌及九宫区域视觉验证通过；
- lighting/UI、camera、hit-test、pointer、路线、热点、缩放、移动端均回归通过；
- 108 人固定性能基准通过；
- v2 整图原子激活，失败时不出现 partial scene；
- 独立 Reviewer 和 Release Guard 均通过；
- 文档、TMX schema、测试和生产实现保持一致。

