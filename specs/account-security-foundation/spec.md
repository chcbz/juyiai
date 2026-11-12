# Account security foundation and global session revocation

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：账号认证、安全会话与撤销。**

### 责任与业务流程
认证入口维护会话/撤销事实；业务服务使用可信主体完成资源授权；Web清理本身份的状态。

登录认证→建立会话→业务授权→退出/撤销后拒绝新未授权请求。既有已接收执行的生命周期由对应业务合同决定，不为所有流式片段新增撤权查库。

### 明确边界
Cookie局部修复不等于全局撤销验收；不把显示名作为身份，不在每层重解JWT。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
登录/过期/退出与撤销后的新请求、跨账号资源访问、Web身份切换迟到响应；凭据不得出现在日志。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留独立安全合同及撤销/迁移未完成验收；不因Cookie修复收口整项。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


<!-- SDD delivery reconciliation 2026-09-06 -->
## Problem

聚义厅准备面向公众公测，但当前用户 access token 是不可即时撤销的自包含 JWT；`user_info` 没有账户生命周期或会话版本；现有 `DELETE /user/delete?id=...` 只是通用按 ID 删除，既不适合自助注销，也不能撤销 token、API Key 或关联数据。请求身份还可能受未清理的 `ThreadLocal` 和旧 `CTX` Cookie 影响。生产 Web OAuth client 仍允许 secret、refresh token、client credentials、Postman callback，并使用 30 天 access token。

在这些问题解决前，不得把现有删除接口包装成“注销账号”，也不得宣称账号可以安全停用或全局退出。

## Goals

- 为用户账户建立明确的 `account_state` 与单调递增 `auth_epoch`。
- 用户 JWT 使用稳定 `uid` 与显式 `token_kind`；每次受保护请求都校验 uid/jiacn 对应同一 ACTIVE 账户且 token epoch 与数据库一致。
- 提供只作用于当前 Bearer 主体的“退出所有设备”，并用 CAS 保证并发安全。
- 阻止撤销前的登录会话或 refresh principal 再签发可用 token。
- 非 ACTIVE 用户不能使用交互登录、第三方登录、用户 JWT 或已有 API Key。
- 修复 `EsContextHolder` 请求间身份泄漏、JWT/CTX 优先级与 CTX Cookie 基础属性。
- Web 个人中心提供清晰的“退出当前设备”和“退出所有设备”。
- 将生产 Web OAuth client 收敛为无 secret、PKCE、authorization-code-only、无 refresh/client-credentials 的短时 access token 客户端。

## Non-goals

- 本阶段不实现账号注销、数据导出、冷静期、恢复、PII 擦除、LDAP/ES/文件清理或法务留存。
- 不删除或改变管理员 `DELETE /user/delete?id=...` 的既有授权语义；自助注销必须另立 `account-self-service-closure` SDD。
- `revoke-all` 不撤销 Agent API Key；API Key 仅在账户非 ACTIVE 时拒绝认证，后续重新激活策略不在本阶段定义。
- 不建立设备列表、单设备服务端会话表、refresh-token family 或 JWT denylist。
- 不在浏览器保存或使用 refresh token。
- 不修复与本功能无关的现有依赖漏洞或重构整个认证栈。

## Scope

- API:
  - `user_info` schema、用户实体、DAO/service CAS。
  - 交互登录、第三方登录、JWT 签发、resource-server 用户状态验证、API Key 状态验证。
  - `POST /user/me/sessions/revoke-all`。
  - `EsContextFilter`、`EsSecurityContextFilter`、`EsContextHolder` Cookie 与 CORS 配置。
  - 定向单元/集成测试和可重复、可回滚的生产迁移材料。
- Web:
  - API store 的身份清理和全局撤销调用。
  - 个人中心的当前设备/所有设备退出操作、确认、忙碌态、失败态和导航。
  - 定向测试、lint 与 production build。
- Release:
  - 生产数据库迁移与字节级备份。
  - 生产 Web OAuth client 配置收敛及显式 rollback SQL。
  - API/Web 部署和线上认证 smoke。

## Constraints and risks

- 这是身份/ACL/并发/迁移变更，由本任务Owner对实际风险自检并完成必要回归；不指定已退役角色或创建独立Reviewer。
- 全局只允许一个源码 Writer；Gradle 命令必须持有 `/tmp/cyf-gradle.lock`。
- 安全敏感主体只从 Spring Security 的 `JwtAuthenticationToken` 获取；不得依赖 `EsContextHolder`、Cookie、query 或 body。
- `uid` 只能是 canonical positive decimal string；token kind 必须正向分类；epoch 必须按 JSON integer 严格解析，拒绝负数、浮点、字符串和溢出，不得静默降级。
- 发布顺序必须避免新代码查询不存在列；先备份并迁移 schema，再部署 API。回滚旧 API 时新增列保留，且必须显式失效已签发 token/登录 Session，禁止安全语义倒退。
- Web 主工作区和根仓库存在无关脏改动，只能精确暂存本功能文件，禁止回退用户改动。
