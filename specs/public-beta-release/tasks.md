# 公共公测发布与安全整合 — 任务

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：公测范围与真实交付验收。**

**实施目标：** 固定候选和公测范围→必要测试→本地不可变制品→获授权安装→健康与真实用户主流程验收。
**责任落点：** Owner按特性范围核对安全/功能/运维证据；既有发布工具负责安装事务。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不是所有规划功能的自动启用许可；开发、安装、健康、业务验收不能合并为一个PASS；资金/生产迁移须已有实际授权。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：身份/ACL、真实onboarding、关键用户旅程、已知限制、制品摘要与恢复边界；600秒只作整批墙钟目标。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


任务级实施/审核/验证由 `docs/implementation/TASKS.yaml#runtime_ledger_json` 唯一管理；不在此派发第二份 Owner。

## 剩余交付

- [ ] 关联 exact API/Web 安全修复与实际部署 artifact
- [ ] 账号/迁移及 credentialed 浏览器安全验收
- [ ] 实际用户 onboarding 可用性与隔离验证
- [ ] 记录公测 release baseline 后才关闭整体需求

完整快照映射见 [delivery-status.md](delivery-status.md)。历史定义中未进入当前运行台账的任务仍是规划，不擅自启动。

## 仓库分工（角色，不是第二份执行认领）

| 仓库/职责 | 路由 | 边界 |
| --- | --- | --- |
| API | critical_worker | 身份/ACL/事务/后端核心；exact task owner 读取运行台账 |
| Web | balanced_worker | 冻结合同下交互与前端集成；不得修改 API owned paths |
| 集成/归档 | main_orchestrator | 不重置脏主树，不覆盖其他任务认领 |
| 验证 | gpt_test_runner | exact tree/selector/fixture；重型资源串行 |
| 独立审查 | sol_reviewer | 只读，不预实现或修复 |
