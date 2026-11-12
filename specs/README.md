# CYF规格入口

导航核对：2026-11-10。维护35个现行责任专题，另有4个退役专题和1个历史来源目录；文档有效范围以责任合同及证据为准，不代表全部功能已实现或上线。

Agent统一从[文档总入口](../docs/README.md)按任务分流；业务回归见[聚义厅全局119项](juyiting-unified-experience/global-regression.md)。原日期验收和冻结合同保持来源，不以本次导航核对刷新实现状态。

## 从这里开始

1. [现行责任与退役索引](INDEX.md)：找到唯一责任专题，不并行维护第二套同义规格。
2. [统一开发约束](architecture-convergence/development-principles.md)：性能、事实归属、必要校验、兼容边界、DFX与验证口径。
3. 专题 `spec.md` → `design.md` → 实际受影响的 `tasks.md` / `acceptance.md`；专项合同以主spec明确指向为准，不默认读全部历史。术语一名一义、冲突优先级见[规格维护规则](AGENTS.md)。
4. [当前实现知识](../docs/knowledge-base/README.md)与固定源码用于确认实现；原handoff/receipt用于确认测试、安装及业务验收，不能互相替代。

## 文档角色

| 文档 | 负责什么 | 不能当什么 |
| --- | --- | --- |
| spec/design | 当前目标、责任、流程、协议与数据细则 | 全部实现/上线证明 |
| tasks/acceptance | 实际改动范围、可观察验收及历史结果 | 自动重开所有旧待办、历史发布授权 |
| integration.yaml | 对应批次的精确候选关联 | 当前checkout/线上版本的自动跟踪器 |
| schema/fixture/冻结bundle | 具体版本协议及测试输入 | 可以静默覆盖的“旧文档” |
| 报告/日志/receipt/历史会话 | 当时输入与事实 | 今日实施步骤或新的用户授权 |

默认本地固定源码验证/构建；按真实授权安装。单Owner自检，契约变化才联动实际消费者。文档维护要求见[本目录规则](AGENTS.md)，操作流程见[SDD工作流](../docs/sdd-workflow.md)。

`./sddw check-docs`仅检查文档导航。不要为通过检查运行pin重写历史SHA；不要以批量改日期冒充全仓源码和业务复验。
