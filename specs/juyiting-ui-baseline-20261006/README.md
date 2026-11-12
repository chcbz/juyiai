> 当前唯一交互原型已迁至 `/home/isp/wsps/cyf/web/prototypes/juyiting/`，入口 `index.html`；启动脚本为该目录的 `serve-preview.py`。本目录的 `optimization/` 维护本次完整优化方案，历史验证证据保留原处，`prototype` 仅为兼容链接，不维护第二份原型。

# 聚义厅 UI 基准：当前知识与历史来源

文档收口：2026-10-08。**仅收口已发布的议事输入区 UI 切片，不归档整个 feature，不改变任务状态。**

## 日常开发入口

- [组件职责与依赖](../../docs/knowledge-base/05-frontend-architecture.md#hall-discussion-composition)：哪些行为属于页面、ChatPanel、Composer 和语音控件接线。
- [议事 UI 行为与回归边界](../../docs/knowledge-base/06-juyiting-end-to-end.md#hall-discussion-ui)：资料入口、菜单/语音反馈、可访问性、完成态锁定及定向验证。
- 当前开发和发布规则以根 AGENTS.md 与现行发布策略为准；不要从旧发布步骤推导本次操作授权。

## 本次优化完整方案（当前入口）

优先阅读 [优化SDD导航](optimization/README.md)，当前待办见 [tasks.md](optimization/tasks.md)；下方2026-10-08/16记录仅为历史来源。

- `optimization/spec.md`：本次界面样式与办事流程的完整变更方案，包含前后端差异、实施顺序、验收与风险。
- `optimization/production-recheck.md`、`optimization/full-flow-recheck.md`：只读页面及授权完整流程/最新develop核对；不是最新原型规格。
- 最新原型规格仍在 `/home/isp/wsps/cyf/web/prototypes/juyiting/specs/prototype-spec.md`；任务方案不放原型目录。

## 早期方案的收口

2026-10-16样式与办事临时方案已被统一规格取代并删除，关键约束见 [当前规格](optimization/spec.md)。原 [逐页审计](style-audit-20261016.md) 及evidence仍保留，不改变当时未验证边界。旧路径恢复见 `../../docs/sdd-document-map.json`。

## 2026-10-16 原型增量修订

现有原型已更新资料选择层级、删除话头确认与账户入口边界；见[原型说明](prototype/README.md)及 `evidence/prototype-corrections-20261016/`。这不是产品发布，不宣称全量生产一致。手机与PC共用同一原型。

## 历史资料（原文件保持不变）

| 材料 | 用途与边界 |
| --- | --- |
| [spec.md](spec.md)、[design.md](design.md) | 原型/设计时的目标与非目标；其中“仅原型/不改产品”是当时范围，不覆盖后续实现事实 |
| [原型说明](prototype/README.md)、[coverage.md](coverage.md) | 固定 UI 对照与模拟覆盖，不能证明后台或生产功能 |
| [UI 实施记录](ui-implementation-20261007.md) | 2026-10-07 模板/样式调整过程、自检及候选验证 |
| [1.0.6 发布记录](release-1.0.6.md) | 精确版本、Flow Run180、制品、在线及浏览器历史核验 |
| [机器可读发布回执](evidence/release-1.0.6-20261008/release.json) | 历史发布绑定；不是当前线上查询结果 |

## 本轮核对与未完成边界

- 已读取上述发布回执及 artifact/online/browser JSON，版本 1.0.6、Run180、commit 与发布说明对应。历史源码为 `ee6ca1b6beba562e0c7fa13d422857f554644471`；在线字节核验时间为 **2026-10-08 00:33:38 +08:00**。
- 为避免把旧 UI 说明当作当前契约，又核对本地 Web 集成引用 `75766a3b78c2e552ef448e924a813ed2dfc7ecd4` 中 ChatPanel/Composer。后续新增完成态禁用逻辑已明确区分，不能沿用当次 UI patch 的“脚本不变”描述。
- 没有重新运行历史测试、Flow、登录或在线检查；未宣称上述任一版本是现在的生产版本。全库生成基线不变。
- 原发布回执的整体业务验收为 `NOT_COMPLETE`；R01、重复正文、完成态恢复等原待办保持原证据边界，不在本次重判完成或未完成。原型与其余 UI 范围也未整体归档。
