# 聚义厅悬赏榜与可靠多 Agent 协作 — 设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：任务/请求/回合扩展性与协作事实。**

### 最小责任链
任务模块管理事项/成员/工作项；议事模块管理请求/回合；执行端接收具体合同；费用独立。

用户明确目标→按不同指令建立请求→绑定目标回合/执行→回报各自成果→事项侧按合同聚合。

### 实施约束
保留多回合扩展不等于每请求广播所有好汉；单承办UI验收不代表M4/M5高级协同完成；旧SILVER规则由文钱包覆盖。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


已有详细架构合同继续有效：canonical scope/Agent、状态机/CAS/lease、decimal-string 版本、live/replay/resync、DB outbox/inbox、Rabbit confirm/manual ACK 与幂等。地图 /agent/map、名册 /agent/roster 分流，派单必须显式 Agent，禁止 /agent/active 回流。生产 Rabbit 激活不从 API 健康推断。

## 契约来源及兼容

以下原始合同为细节权威，本入口为全量盘点时补录，不替代已冻结请求/响应、ACL、事件、错误及版本合同。

- `docs/juyiting-multi-agent-collaboration-design.md`
- `docs/implementation/M2_EXECUTION_PLAN.md`
- `docs/implementation/M3_EXECUTION_PLAN.md`

无本次代码/Schema/迁移改动；后续实现必须沿现有任务 Owner 与 scoped worktree。
