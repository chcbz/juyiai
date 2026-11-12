# 聚义厅功能与实现阅读地图

核对：2026-11-10。本文帮助定位业务责任，不另定义协议、当前线上版本或所有页面实现。完整合同见[specs索引](../specs/INDEX.md)，开发/排障见[Runbook](juyiting-runbook.md)。

## 用户主链

需求保存 → 推荐/手选 → 显式确认承办 → 正式议事与多轮修改 → 真实成果 → 选择明确版本验收，或合法取消。草稿保存、推荐、确认、执行、成果提交、验收是不同事实；以责任专题状态机和当前实现为准。

普通密议面向明确好汉/会话，不默认创建正式事项；与事项议事的输入、历史、资料scope和费用授权分开。新需求与返工也不能靠相同文本或旧终态自动合并。

## 业务与实现定位

| 领域 | 责任合同 | 找实现时关注 |
| --- | --- | --- |
| 地图、首页、返回与横竖屏 | [UI基准](../specs/juyiting-ui-baseline-20261006/spec.md)、[整体体验](../specs/juyiting-unified-experience/spec.md) | Web页面编排/面板与当前路由；地图不复制业务状态 |
| 需求与承办推荐 | [推荐合同](../specs/juyiting-assignee-recommendation/spec.md) | 需求版本、真实候选、手选与显式确认；推荐不等于授权执行 |
| 对话、多轮及恢复 | [议事](../specs/juyiting-multimedia-deliberation/spec.md)、[会话](../specs/juyiting-conversation-sessions/spec.md) | 消息页级投影、完整最终回复、流仅预览、身份/话头切换与迟到响应隔离 |
| 原生执行和技能 | [技能主spec](../specs/juyiting-skill-execution/spec.md) | selected授权、模型/工具/bridge职责、真实工具回执及正式成果 |
| 资料与交付 | [资料合同](../specs/juyiting-creative-delivery-mvp/spec.md) | 固定不可变版本、引用范围、预览与存储能力分开、历史成果仍可认证读取 |
| 钱包与费用 | [WEN专项合同](../specs/agent-economy-marketplace/beta-wen-billing.md) | 原子预占/释放/结算与幂等；人民币用量回执另记，不从UI推断账本 |
| 好汉/岗位/托管 | [技能管理](../specs/juyiting-skill-execution/management-contract.md)、[经济专题](../specs/agent-economy-marketplace/spec.md) | 安装、授权、默认模型、就绪分别是实际事实；新移除/交接合同不默认已实现 |
| 典籍与阅读 | [维护](../specs/archive-agent-maintenance/spec.md)、[阅读器](../specs/archive-pavilion-reader-mvp/spec.md) | 查询和写发布分验；章数、引首、版本与阅读进度按真实书籍数据 |
| 帮助、反馈与我的 | [UI现行规格](../specs/juyiting-ui-baseline-20261006/optimization/spec.md) | 帮助分类/搜索/业务跳转；原反馈身份隔离与未知结果不自动重发 |
| 语音/公共协作 | [语音](../specs/juyiting-voice-conversation/spec.md)、[Realtime](../specs/juyiting-voice-realtime/spec.md)、[协作](../specs/juyiting-task-collaboration/spec.md) | 实际开关、合同落地和真机/多账号证据；目标设计不是当前能力 |

## 从文档进入代码

前端从[Web规则](../web/AGENTS.md)和[前端知识](knowledge-base/05-frontend-architecture.md)定位，后端从[API规则](../api/AGENTS.md)和[后端架构](knowledge-base/03-backend-architecture.md)定位。组件重组、Controller路由和源码路径以本次固定checkout核实，不将旧指南的组件名/接口清单直接当现行事实。

界面先改[唯一原型](../web/prototypes/juyiting/specs/prototype-spec.md)，再落产品、对照回归。契约未变的责任层内部修复不机械改三端；契约变化才同步实际生产者和消费者。

## 测试及有效性

所有长期业务用例统一归[全局回归](../specs/juyiting-unified-experience/global-regression.md)，不在本页复制旧页面按钮清单。现行规则由根AGENTS/责任合同维护；旧UI快照、SILVER、无条件不兼容、Flow-only及早期客户端说明仅作历史，不恢复为默认行为。文档查阅不授权收费、发布、写典籍、改岗位或清理主机。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__juyiting-feature-guide.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
