# 任务安排与路径所有权

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：复用同一地图状态的只读预览。**

**实施目标：** 地图事实→共享状态→只读缩略预览→需要交互时进入现行全景入口。
**责任落点：** 地图数据/运动由原地图模块维护；竖屏预览只投影视图。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不以roster替代map，不建立第二动画/轮询/会话状态；不恢复已取消方向控制。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：角色/位置与主地图一致、预览只读、视口切换释放资源、地图与名册筛选不相互污染。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


运行 owner、exact SHA/tree、门禁及阻断仅由主控写入 `TASKS.yaml#runtime_ledger_json`。以下是依赖与计划分工，不是第二 ledger。

| 阶段 | 计划角色 | 交付 | 依赖/门禁 |
|---|---|---|---|
| P0 设计 | 本线程协调者 | spec/design/tasks/acceptance/integration 五件套；告警共享路径 | 用户授权；新目录不覆盖既有横竖屏冻结规范 |
| P1 预览基础 | balanced_worker / Terra | 纯预览外壳、contain/activation 策略、新定向测试 | 仅下列新文件，可与 SCREEN 并行；不接入生产入口 |
| P2 真实地图接入 | 同一 Terra Owner | 单宿主双容器、真实地图/人物连续运动、只读与镜头隔离 | SCREEN exact-tree ACCEPT + 路径交接 + design §8 关闭；不得另开第二 Writer |
| P3 验证 | gpt_test_runner | 定向回归、真实 Canvas 浏览器验收、production build、产物清单 | 最终候选 tree；重型资源串行；不修改源码 |
| P4 独立审查 | 唯一 fresh sol_reviewer | exact-tree ACCEPT/REJECT、P0/P1/P2、证据匹配 | 禁止作者自审、旧 Reviewer ACCEPT 复用、择优接受 |
| P5 集成与发布 | 主控指定 release Owner | 精确提交合入、静态产物发布、HTTP/资源与页面烟测 | ACCEPT + tests/build；不改生产后端/voice 开关；共享部署窗口交接 |
| P6 用户设备验收 | 用户 + 协调者 | 微信真机模式切换与手势验收 | 如无法取得真机证据明确保留待验收，不凭单测标已验收 |

## P1 专有路径
- `web/src/components/juyiting/HallLiveMapPreview.vue`（新增）
- `web/src/composables/juyiting/liveMapPreviewPolicy.js`（新增纯函数）
- `web/tests/unit/juyiting/live-map-preview-policy.test.js`（新增）
- `web/tests/unit/juyiting/hall-live-map-preview.test.js`（新增；按当前测试加载模式编写）

Web task worktree：`.worktrees/juyiting-live-map-preview-20260906`；建议 branch `codex/juyiting-live-map-preview-20260906`，初始基线 `101ac4c6`。
禁止改 `package*.json`、部署脚本、现有 SCREEN 测试、API 和主 checkout；确需新路径先报协调者。

## P2 需正式交接的共享路径
`src/components/world/JuyiHall.vue`、`src/components/juyiting/{HallPortraitHome,HallStage}.vue`、`src/game/JuyitingGame.js`、`src/game/scenes/HallScene.js`；必要的 camera/input adapter 路径须在接入前补充到主控路径分配。
不得提前修改这些文件；采用已接受 SCREEN 后继为父基线，保护其修复及 reader/voice/ACL 等不相关代码。相同 tree 证据按 selector 复用，语义集成修改必须重新定向测试并独立审查。

## 明确禁止
重复 Writer/Reviewer、以旧白屏构建证明新地图预览、重跑全量替代失败归因、单测冒充浏览器/微信验收、未 ACCEPT 自动部署、强行更新 dirty 主工作区。

## 验证命令边界
P1 在任务 worktree 用本地依赖执行显式两文件 selector（最终以 Writer 验证可运行命令为准）：

```sh
node --import tsx ./node_modules/mocha/bin/mocha.js --no-config \
  --require ./tests/setup.js --timeout 30000 --reporter spec \
  tests/unit/juyiting/live-map-preview-policy.test.js \
  tests/unit/juyiting/hall-live-map-preview.test.js
```

不得用 `npm test -- <path>` 代替显式 selector 而意外保留 `.mocharc` 的全量 glob。P1 不单独跑 production build；P2 完成后的最终应用候选必须 `npm run build` 并独立审查，不能将不被应用 import 的基础组件测试当作完整上线验证。
