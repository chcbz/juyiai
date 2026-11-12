# 分工与依赖

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：既有执行回执只读核对与新方案恢复。**

**实施目标：** 通过原请求/执行标识读取→核对已有回执→显示权威状态；仅沿获准新方案恢复入口处理可恢复事实。
**责任落点：** API保有执行/成果事实；Runtime恢复自身新方案状态；Web展示已知/未知与可操作范围。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不把UNKNOWN变失败重跑；旧协议已退役执行/恢复不恢复；完成回执不等于用户验收，不凭缺字段猜执行成功。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：重复回执幂等、跨身份拒绝、历史读取无执行副作用、未知明确展示、新方案自身崩溃恢复不重复外部副作用。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

- API Owner Turing / critical_worker：独立 worktree `/var/tmp/cyf-api-execution-history-20260921`，执行历史/请求核对与runtime failure路径及作用域测试。
- Web Owner Curie / balanced_worker：独立 worktree `/var/tmp/cyf-web-execution-recovery-20260921`，交付同窗回执/恢复/幂等保护/相关文件入口与回归。
- 主 Owner：本条执行精确只读诊断、契约、集成、orchestrator串行验证、授权范围内发布核验。无独立Reviewer。

API/Web可按冻结合同并行；正式集成依赖各自自检。现有脏主工作区不动。不创建额外生成进行验证；组件测试使用隔离fixture，线上仅查询既有运行和文件。

运行状态唯一登记于 `docs/implementation/TASKS.yaml#runtime_ledger_json` 的 JYT-EXEC-RECOVERY-API-20260921 / JYT-EXEC-RECOVERY-WEB-20260921，不在此复制动态队列。
