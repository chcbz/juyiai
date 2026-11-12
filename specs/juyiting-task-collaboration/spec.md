# 聚义厅悬赏榜与可靠多 Agent 协作

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：任务/请求/回合扩展性与协作事实。**

### 责任与业务流程
任务模块管理事项/成员/工作项；议事模块管理请求/回合；执行端接收具体合同；费用独立。

用户明确目标→按不同指令建立请求→绑定目标回合/执行→回报各自成果→事项侧按合同聚合。

### 明确边界
保留多回合扩展不等于每请求广播所有好汉；单承办UI验收不代表M4/M5高级协同完成；旧SILVER规则由文钱包覆盖。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
请求/回合/消息关联清楚、不同目标隔离、重复回报幂等、局部失败不污染无关执行、任务完成与成果验收分离。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留通讯协作详设与M4/M5未交付目标，单承办UI不是多Agent整体完成。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


## 目标与范围

稳定 Agent 身份、多成员/work item、显式指派、共享会话、snapshot/SSE 恢复以及 outbox/inbox/离线补投。E/F/G 高级协同/知识检索/生产加固仍是规划范围；SILVER 交易由独立 economy SDD 承担。

## 非目标

本次文档更新不创建新功能实现、不允许跳过现有安全合同、不宣布未验证的生产交付。

## 权威输入

- `docs/juyiting-multi-agent-collaboration-design.md`
- `docs/implementation/M2_EXECUTION_PLAN.md`
- `docs/implementation/M3_EXECUTION_PLAN.md`
