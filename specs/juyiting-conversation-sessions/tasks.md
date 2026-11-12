# 工作分解（计划，不是第二台账）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：业务会话与原生thread的适用映射。**

**实施目标：** 首次发送创建→同一Agent在允许边界续接→显式切换隔离→历史分页继续。
**责任落点：** API定义业务会话身份与范围；bridge持有按Agent/隔离边界的原生thread映射；Web切换业务会话。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：同一业务会话可涉及多个Agent的原生thread，不作全局严格1:1承诺；材料/工具合同变化不机械新建thread，必要更换必须说明具体隔离/能力原因。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：同会话两轮原文记忆、不同会话/身份无串线、重启后映射恢复、材料输入不丢历史、20条历史分页。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


唯一运行状态在 `docs/implementation/TASKS.yaml#runtime_ledger_json`。

- JY-SESSION-AGENT-20260910：critical_worker，isp-install 独立 worktree 的 conf/codex-ws-agent/**；session 路由、事件捕获、聚焦测试及 README。
- JY-SESSION-WEB-20260910：balanced_worker，web 独立 worktree 的会话 composable/相关助手、ChatPanel/历史控件/JuyiHall 与测试；无 API 源码写入。
- 主控：SDD、台账、资源与发布协调；只读独立 sol_reviewer；验证通过自动晋级。
