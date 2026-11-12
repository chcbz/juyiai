# 公共公测发布与安全整合 — 设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：公测范围与真实交付验收。**

### 最小责任链
Owner按特性范围核对安全/功能/运维证据；既有发布工具负责安装事务。

固定候选和公测范围→必要测试→本地不可变制品→获授权安装→健康与真实用户主流程验收。

### 实施约束
不是所有规划功能的自动启用许可；开发、安装、健康、业务验收不能合并为一个PASS；资金/生产迁移须已有实际授权。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


Hosted 使用精确身份 scope 隔离且 fail closed；任务搜索/计数 scope 下推 DAO/SQL，拒绝 legacy tenant=0 自动归属；preflight 无默认凭证、非 loopback 要 SHA-bound 批准、TLS fail closed、统一 deadline/清理。具体 API 路由/错误合同引用原任务与 handoff，不放宽凭证或访问边界。

## 契约来源及兼容

以下原始合同为细节权威，本入口为全量盘点时补录，不替代已冻结请求/响应、ACL、事件、错误及版本合同。

- `docs/implementation/handoffs/PWA-PREFLIGHT-SAFETY-P1.md`
- `specs/account-security-foundation/design.md`
- `specs/oauth-public-client-hardening/spec.md`

无本次代码/Schema/迁移改动；后续实现必须沿现有任务 Owner 与 scoped worktree。
