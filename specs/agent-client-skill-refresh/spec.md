# Agent client skill refresh

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：Agent技能事实刷新。**

### 责任与业务流程
Runtime发现并报告本机能力；API保存权威观察；Web只读展示。

安装或能力真实变化→上报→服务端更新观察→前端按事件/显式刷新读取。

### 明确边界
能力刷新不等于购买授权、安装成功或任务准入；不在详情GET触发全盘扫描或重注册。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
能力变化与重复报告、单Agent刷新、离线事实与未知状态、无变化时不额外扫描。

**状态：** 已闭环（released；2026-08-23 生产部署并核验 Agent 运行时技能刷新）。最终规格以本文为准；发布/验收证据见 [integration.yaml](integration.yaml)。过程文档已删除。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留技能刷新契约和既有发布证据；不是安装/交易或技能执行的替代文档。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


<!-- SDD delivery reconciliation 2026-09-06 -->
## Problem

聚义厅运行时把 `agent_persona.abilities` 当成 Agent 能力事实，覆盖接入客户端上报值，导致宋江推荐和自动分配无法反映客户端当前已安装技能。

## Goal

- Persona 能力仅作旧客户端/首次注册默认值。
- 已认证并绑定的客户端在注册和心跳中上报当前能力快照。
- 宋江推荐、自动分配和手动能力校验直接使用最新 `agent_runtime.abilities`。
- Codex WebSocket 客户端自动发现 profile 对应 `CODEX_HOME` 与工作区内的 `SKILL.md`。

## Non-goals

- 能力标签不作为 ACL 或高风险操作授权。
- 不修改 Agent canonical identity、persona binding 或任务事务模型。
- 不新增数据库表或字段。
