# 聚义厅遮挡系统 V0 GPT 视觉审核报告

**日期：** 2026-08-03  
**状态：** `ACCEPT-V0-CLOSED`（2026-08-09 延迟证据复核）；已解锁 E8A，但不代表遮挡缺陷已修复，也不批准 E8B  
**审核模型：** GPT-5.6 Sol，高推理，只读多模态审核  
**Agent：** `019fc7c5-5155-7393-8902-bfece2d6a3ee`（本轮以只读 `architect` profile 启动；后续使用已注册的 `vision_reviewer` profile）  
**设计依据：** `docs/juyiting-occlusion-system-design.md`  
**执行依据：** `docs/juyiting-occlusion-system-execution-plan.md`

## 1. 总结

当前历史截图足以冻结以下产品事实：

1. 卢俊义曾在右上桌子区域发生头部/上身被可见桌子像素错误覆盖；
2. 扈三娘在对应历史截图中没有被桌子错误遮挡，该表现必须作为正向基线保留；
3. 现有截图不是严格同坐标、同动画帧、同 camera/zoom 的 A/B，因此不能证明问题由角色身份本身引起；
4. 桌子 prop、TMX mask geometry、可绘制 occluder 像素是三种不同对象，禁止再使用“桌子 mask 挡人”这种混合表述；
5. 当前证据不足以把历史问题唯一归因到 mask 命中、prop depth、重复 occluder、脚点或动画 anchor。

因此本轮结论是：**视觉回归已确认，但根因仍为 `UNCERTAIN`；必须补齐标准化 contact sheet 和 debug manifest。**

## 2. 已冻结回归用例

| 用例 | 预期 |
| --- | --- |
| `REG-TABLE-LUJUNYI-HISTORICAL` | 在历史问题坐标/动画帧复现卢俊义；修复后头部和上身不得被前方桌子像素错误覆盖。 |
| `REG-TABLE-HUSANNIANG-POSITIVE` | 扈三娘对应位置继续保持不被桌子错误遮挡，禁止修复卢俊义时破坏正向基线。 |
| `REG-TABLE-ROLE-INVARIANCE` | 两个角色使用相同脚点、floor、elevation 和关系条件时，排序不得因角色身份变化。 |
| `REG-TABLE-TARGET-RELATION` | 桌前目标关系固定为 `桌子 < 人物 < 前方栏杆`。 |

## 3. 逐项视觉判定

| 附件 | 判定 | 可确认事实 | 不能据此确认 |
| --- | --- | --- | --- |
| A1 卢俊义近景 | `FAIL / P1` | 历史上存在头部被桌子覆盖的问题，纳入冻结回归。 | 具体由哪个 mask、prop depth 或 image layer 导致。 |
| A2 扈三娘近景 | `PASS / 正向基线` | 人物头部和上身仍可见，没有被桌面吞没。 | 不能仅凭画面推导完整排序链。 |
| A3 双人截图 | `UNCERTAIN / P2` | 同一区域人物可见性存在差异。 | 人物身份、相同世界坐标、相同动画帧。 |
| A4 历史附件 | `UNCERTAIN / P1` | 当前附件路径已缺失。 | 不能用文字描述替代像素证据。 |
| A5 全景 | `UNCERTAIN / P2` | 桌子、栏杆和人物同时可见。 | 对话框遮挡关键边界，无法精确判断桌面/人物关系。 |
| A6 同区域截图 | `UNCERTAIN / P1` | 相邻实体存在明显可见性差异。 | 身份、坐标和具体 depth 原因。 |
| A7 路线/障碍叠加图 | `UNCERTAIN / P1` | 多类 polygon、节点、路线在中央和右侧汇聚。 | 未分离 mask/collision/nav/routes，不能建立 37 mask 视觉映射。 |
| A8 地图底图 | `PASS / 参考` | 提供空间和美术基线。 | 不证明运行时最终绘制顺序。 |
| A9 canonical occluder | `PASS / P1 系统风险` | 是带 alpha 的可绘制 occluder 像素，不是 TMX mask geometry。 | 不能把透明背景或资源本身称为 mask。 |

## 4. 已核实资源身份

| 资源 | SHA-256 |
| --- | --- |
| `web/public/juyiting/images/liangshan-hall-base-clean-v3.webp` | `72d5ca5ff3d5c71ec66018d65bbe6a9636e6bbab10338e2a07989b0be1efd9aa` |
| `web/public/juyiting/images/liangshan-hall-mid-occluders-v3.webp` | `3e4f3f90b4d84411a844978237a7d3530bd481c37a62bcd73b9d694a7d2dd432` |
| `web/public/juyiting/images/liangshan-hall-foreground-occluders-v3.webp` | `3e4f3f90b4d84411a844978237a7d3530bd481c37a62bcd73b9d694a7d2dd432` |
| `web/public/juyiting/images/props/liangshan-hall-prop-bounty-board-cropped.png` | `2e4c3e749119392b01a7301aaa8f40986a09e5cc731ab61105ed600a755b6252` |

TMX 相关对象：

- prop tile object：`id=92`、`name=bounty-board-rect`；
- hotspot：`id=87`、`name=bounty-board`；
- 东北候选 mask：`id=57`、`72`、`73`，但实际历史帧命中对象仍必须由 debug 数据确认。

## 5. E1/V0 必须补齐的 contact sheet

| 编号 | 内容 | 最小证据 |
| --- | --- | --- |
| `V0-CS01` | 历史截图索引 | A1～A6 时间顺序、全图 crop 位置；缺失图明确标记。 |
| `V0-CS02` | 同坐标角色 A/B | 卢俊义、扈三娘同脚点、同朝向、同动画帧，关闭标签和气泡。 |
| `V0-CS03` | 桌子三点矩阵 | 两角色分别位于 behind、boundary、front，共 6 张 clean frame。 |
| `V0-CS04` | 双人同时出现 | UI 关闭和 world-ui 开启各一张。 |
| `V0-CS05` | Debug 对照 | 脚点、prop bbox、真实 mask polygon、mask AABB、命中 ID、全部相关 depth。 |
| `V0-CS06` | 资产组合 | base、桌子 prop、A9 均以棋盘格/组合方式展示，避免误读 alpha。 |
| `V0-CS07` | 几何分层 | mask-only、collision/nav-only、routes/nodes-only、combined，均带 ID/图例。 |
| `V0-CS08` | 九宫基线 | 九个区域 production-equivalent clean screenshot。 |
| `V0-CS09` | UI/相机回归 | desktop、mobile、zoom、pan，labels/bubbles 单独开启。 |

每张截图必须附带：commit/TMX/资产 hash、人物运行时 ID、世界坐标和脚点、动画帧和 anchor、camera/zoom/DPR、agent/prop/image-layer depth、命中 mask ID。关键 crop 必须保留 1:1 原始 PNG。

## 6. 当前复查边界

桌前问题首轮只复查：

1. `bounty-board-rect` prop；
2. canonical occluder 右上桌面状像素和相邻栏杆；
3. mask 57、72、73 以及 debug 证明实际命中的其他 mask；
4. `mid=2`、prop、`foreground=5` 与人物 depth 的关系；
5. 卢俊义/扈三娘精灵脚点、anchor 和同坐标表现；
6. labels/bubbles 是否稳定留在 `world-ui`。

E1 仍需补齐全地图九宫基线，但本问题不得扩散到导航、后端、roster 或任务数据流。


## 7. 2026-08-09 延迟证据闭合签字

**最终判定：** `ACCEPT-V0-CLOSED`。历史附件恢复后，GPT `vision_reviewer` 独立复核了卢俊义、扈三娘、双人、全景、几何 overlay 和五 prop inventory。V0 基线事实、对象边界与后续必测矩阵已足以启动 E8A。

冻结结论：

- 卢俊义右上桌区域为历史 `FAIL / P1`；扈三娘为 `PASS` 正向基线。
- 历史截图并非同脚点、同朝向、同动画帧，不能据此认定排序读取了角色身份。
- 可绘制桌子 prop、canonical occluder 像素、TMX mask geometry、hotspot 必须继续分离。
- 五个 prop 已 5/5 盘点，但最终 `sortAnchor` 不能直接等同 rect 底边，必须由 E8A 视觉规格签字。
- 37/37 mask geometry 已盘点，但视觉结构映射仍为 0/37，归 E10A；右上桌前除 57/72/73 外必须强制复核 mask 58。
- E8A 必须提供五 prop 的 stableId/floor/elevation/renderBand/sortMode/sortAnchor，以及上、下、左、右探针。右上桌必须提供 `N/S/W/E × 卢俊义/扈三娘` 八格和 `behind/boundary/front × 两角色` 六格，同脚点、同方向、同动画帧。
- 目标关系保持：`table anchor≈379 < agent foot≈420 < front railing anchor≈458`。
- fragment ownership、37 mask 映射、UI band、六角色白边、camera/mobile 等证据按计划分别延期到 E9A/E9B、E10A、E13，不再阻塞 E8A。

**门禁：** E8A 可开始；E8A 的 V1 视觉签字和技术签字未完成前不得进入 E8B。
