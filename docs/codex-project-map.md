# CYF 项目地图

导航核对：2026-11-10。先读[根规则](../AGENTS.md)与[文档总入口](README.md)。本页只定位仓库与责任，不复制发布规则或全部业务状态。

## 仓库与实现

| 位置 | 职责 | 从哪里继续 |
| --- | --- | --- |
| 根协调仓 | 跨仓合同、集成gitlinks、文档/工具 | [规格索引](../specs/INDEX.md)、[SDD流程](sdd-workflow.md) |
| `web/` | Vue页面、状态、交互、原型、Web测试 | [Web规则](../web/AGENTS.md)、[前端知识](knowledge-base/05-frontend-architecture.md) |
| `api/` | Java/Gradle业务、持久化、接口、后台任务 | [API规则](../api/AGENTS.md)、[后端知识](knowledge-base/03-backend-architecture.md) |
| `runtime/`（juyiai-runtime） | CYF Runtime/bridge源码和打包 | [技能执行合同](../specs/juyiting-skill-execution/spec.md)、[Runtime自托管](../specs/runtime-self-host-onboarding/spec.md) |

API/Web为独立Git仓/子模块，root gitlinks是某次集成候选，不等于本地HEAD、远端develop或当前线上；分别记录，不互相替代。Runtime独立开发任务须显式携带CYF规则和接口合同，不假设从工作区自动继承。

Runtime安装固定实体根为 `/home/isp/apps/cyf-agent-runtime-v1/app/`，内部组件名为 `codex-bridge`；状态、身份、授权和私有HOME不是可清理旧程序。精确源码路径按当前任务实际checkout核实，不把历史worktree作为固定开发入口。

## 按问题定位

| 问题 | 责任入口 |
| --- | --- |
| 聚义厅生命周期、议事/密议、选材/成果 | [Runbook](juyiting-runbook.md) · [功能地图](juyiting-feature-guide.md) |
| 全局业务测试与核心冒烟 | [全局回归](../specs/juyiting-unified-experience/global-regression.md) |
| WEN账本、报价、预占、验收/取消 | [文钱包合同](../specs/agent-economy-marketplace/beta-wen-billing.md) |
| 原生执行/技能/隔离 | [RB-1](../specs/juyiting-skill-execution/responsibility-boundaries.md) |
| 文档与源码如何核对 | [知识库入口](knowledge-base/README.md)；旧摘要不证明当前行为 |
| 构建/安装/恢复/存储 | [部署指南](DEPLOYMENT.md) → [已有工具](../ops/orchestration/README.md) |
| Agent角色/任务归属/交接 | [实施入口](implementation/README.md) |
| 地图/遮挡/视觉 | [遮挡设计](juyiting-occlusion-system-design.md) · [原型](../web/prototypes/juyiting/specs/prototype-spec.md) |

具体组件/Controller用相关知识条目的路径定位后检查实际源码；不把历史组件名、接口统计和“已发布”描述自动升级为今天事实。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__codex-project-map.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
