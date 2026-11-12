> **2026-10-07 原型入口纠正**：后续新需求统一基于[最近优化的UI原型](../../juyiting-ui-baseline-20261006/prototype/index.html)及其页面/状态索引。本页的 `complete-20261007` / `adjusted` 是历史中间成果，不是当前界面基准；历史证据保留，真实业务仍 NOT_COMPLETE。

> **2026-10-07 最新完整交互入口**：[浏览器走查后补齐版](complete-20261007/index.html) · [分支场景](complete-20261007/scenarios.html) · [范围与检查](complete-20261007/README.md)。下方current/adjusted保留历史对照，生产缺口仍未修复。

# 页面原型

> **最新评审与实施入口：[局部调整版交互原型](adjusted/index.html) · [交互说明与截图](adjusted/README.md) · [变化红框与编号说明](adjusted/annotations/index.html)。** [实际页面基线](current/index.html)仅用于对照。下方均为旧独立原型的历史说明（包括旧验收选择行为），不是当前需求；当前验收无多选、无“调整交付内容”。

> **范围纠正：不做大改。** 以下为旧版独立流程示意，不是页面重做依据。实际实施保留现有聚义厅页面、布局、导航及样式，仅局部补齐资料、多媒体、保存和验收。页面划分、侧栏、配色与四步进度条均不要求落地；以 [详设第0节](../design.md) 为准。

对应 [详细设计](../design.md)。这是**可点击的文档原型**，不是现有产品截图，也不证明功能已开发或上线。

## 使用

用浏览器打开 [index.html](index.html)。无安装、无网络依赖、无 API / Provider 调用。

- 按顺序体验：提需求 → 选择 Agent → 开始议事 → 继续补充 → 验收 → 完成。
- “添加资料”统一多选图片、文档、音频、普通文件；可预览、取消或移除，也可以不选任何资料。
- 会话中可引用图片、补充附件、查看新一版示意；可预览、下载示例字节，保存后在工作空间看到内容。
- 验收可调整所选成果，不要求先保存；可以只选择文字成果。
- 按最新反馈，已删除顶部切页菜单和四步流程导航。保留底部“办事 / 事项 / 资料 / 我的”；“我的”只说明沿用现有功能，不扩展个人中心。顶部仅保留原型示意说明。

## 范围与限制

Agent 名称、能力、在线状态、对话和验收均为内存演示，不查询真实平台。小鸟是手绘 SVG 示意，不冒充实际生成照片；音频为两秒合成示意音，不冒充鸟鸣、语音或 Agent 输出。文本与 CSV 是原型文件。保存/验收仅修改原型内存，刷新后重置；正式产品必须持久化。下载仅下载明确标记的示意文件。

原型展示多媒体组件形态，**不是要求每次任务都返回图片、音频和文档**。本期详设不要求重做已有语音录制和全站工作空间管理；原型不模拟麦克风、权限、后端重连、模型、事务或数据库。

## 原型图

| 场景 | 桌面图 |
|---|---|
| 四步总览 | [总览](screenshots/overview.png) |
| P1 提需求 | [页面](screenshots/01-request.png) |
| D1 统一添加资料 | [弹层](screenshots/02-materials.png) |
| P2 选择 Agent | [页面](screenshots/03-agents.png) |
| P3 会话与多媒体结果 | [页面](screenshots/04-chat.png) |
| D2 大图预览 | [弹层](screenshots/05-preview.png) |
| P4 验收成果 | [页面](screenshots/06-accept.png) |
| P5 已完成 | [页面](screenshots/07-done.png) |
| P6 工作空间 | [页面](screenshots/08-workspace.png) |
| 移动端提需求 | [390px](screenshots/09-mobile-request.png) |
| 移动端会话 | [390px](screenshots/10-mobile-chat.png) |
| 移动端验收 | [390px](screenshots/11-mobile-accept.png) |

截图由本原型在真实 Chromium 渲染生成，非生产构建。交互及布局自检见 [prototype-checks.json](prototype-checks.json)。
