# Account security foundation and global session revocation design

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：账号认证、安全会话与撤销。**

### 最小责任链
认证入口维护会话/撤销事实；业务服务使用可信主体完成资源授权；Web清理本身份的状态。

登录认证→建立会话→业务授权→退出/撤销后拒绝新未授权请求。既有已接收执行的生命周期由对应业务合同决定，不为所有流式片段新增撤权查库。

### 实施约束
Cookie局部修复不等于全局撤销验收；不把显示名作为身份，不在每层重解JWT。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## User flow

1. 用户完成密码、短信或第三方登录时，服务端只允许 `account_state=ACTIVE`，并把稳定 user ID、byte-exact `jiacn` 和当时 `auth_epoch` 固化到认证 principal。
2. authorization code 换取用户 access token 时，JWT 明确标记 `token_kind=user`，并包含 `uid`、`jiacn`、`username` 与数值型 `auth_epoch`。
3. 每个用户 JWT 在进入业务 Controller 前读取当前 `user_info`：稳定 ID 与 `jiacn` 必须匹配同一行，账户必须 ACTIVE，token epoch 必须等于数据库 epoch。
4. 用户选择“退出当前设备”时，浏览器只清理本地 token、身份和实时连接状态，然后返回公开首页；其他设备不受影响。
5. 用户选择“退出所有设备”时先确认影响；浏览器用当前 Bearer token 调用撤销接口。CAS 成功后当前 token 立即失效；并发请求已完成撤销时也清理本地身份。
6. 再使用旧 token、旧授权会话 principal、非 ACTIVE 账户 API Key，或不能明确分类的 JWT 时，统一失败且不进入业务逻辑。

## Data model

`user_info` 新增：

- `account_state VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'ACTIVE'`；本阶段合法值仅 `ACTIVE`、`SUSPENDED`、`DISABLED`，未知值 fail closed。
- `auth_epoch BIGINT NOT NULL DEFAULT 0`；范围 `0..Long.MAX_VALUE`，只允许单调递增。

不变量：

- 只有 byte-exact `ACTIVE` 可认证。
- 任何离开 ACTIVE 或重新进入 ACTIVE 的状态转换都必须在同一事务增加 `auth_epoch`，防止恢复账户时旧 token 复活。
- 本阶段不提供状态管理 API/UI；上述不变量必须由后续账号注销/后台管理 SDD 继承。

迁移要求：

- upgrade SQL 可重复执行或有明确 precondition；现有行回填为 `ACTIVE/0`，并验证 `account_state` 列精确使用 `ascii_bin`，不得继承表级大小写不敏感 collation。
- repeat 不得改变已有 epoch/state。
- 回滚代码时保留两列；自动发布不得执行 destructive down migration。
- 生产迁移前保存 `SHOW CREATE TABLE user_info`、行数、NULL/空白/byte-exact duplicate/collation-collision 审计及目标 OAuth client 原始行；备份权限 600。
- 2026-08-24 只读预审：生产 `jia.user_info` 共 289 行、1 行 `jiacn IS NULL`、未发现 byte-exact duplicate 或大小写折叠碰撞；该 NULL 用户不能被签发新 user token，发布前需再次复核。

## JWT identity and classification contract

### New token claims

新用户 access token：

| Claim | Wire type | Contract |
| --- | --- | --- |
| `token_kind` | JSON string | byte-exact `user` |
| `uid` | JSON string | `user_info.id` 的 canonical positive decimal ASCII；稳定、不可变 |
| `jiacn` | JSON string | 非空业务主体，byte-exact；禁止 trim/lowercase |
| `auth_epoch` | JSON integer | `0..Long.MAX_VALUE`，不能是 string/float |
| `sub` | JSON string | 暂时保持现有登录标识以兼容 OIDC；不得用于账户查询或 CAS |

新 machine access token 必须显式 `token_kind=machine`，且不得携带 `uid`、`jiacn` 或 `auth_epoch`。`client_id` 与 `sub` 继续按授权服务器既有 machine 语义签发。

### Legacy compatibility

- 旧 user token：无 `token_kind` 但有非空 `jiacn` 时，按 byte-exact `jiacn` 查询；必须恰好匹配一行。缺 `auth_epoch` 只按 0 处理，且仅 DB 为 ACTIVE/0 时通过。存在但非法的 epoch 绝不降级为 0。
- 旧 machine token：仅在同时满足“无 `token_kind/uid/jiacn/username/auth_epoch`、`sub` 与 `client_id` 都是非空 string 且 byte-exact 相等”时兼容；否则 401。绝不使用“缺 jiacn 即 machine”的 fail-open 规则。
- 新 token 若 `token_kind` 缺失、未知或与 claims 组合矛盾，必须 401。
- legacy fallback 在生产 Web client 收敛后的最大旧 access-token TTL（当前 30 天）内保留并建立移除任务；任何用户 epoch 增至 1 后，其所有旧无-epoch token 永久失效。

## API and security contract

### Account security service and validator

- `AccountSecurityService` 通过稳定 ID 或 byte-exact legacy `jiacn` 返回窄 `AccountSecuritySnapshot(userId, jiacn, accountState, authEpoch)`；legacy 查询必须拒绝 0 行或多行，不能依赖 `utf8mb4_0900_ai_ci` 的普通等值比较。
- resource validator 保留现有签名、时间等标准 validator，并在其成功后组合账户 validator；不得替换默认 validator。
- `token_kind=user`：按 `uid` 查询，同一行的 `jiacn` 必须与 token byte-exact 一致，state 为 ACTIVE，epoch 相等。
- legacy user：按 exact `jiacn` 唯一解析，再校验 ACTIVE/0。
- `token_kind=machine` 或严格兼容的 legacy machine：跳过用户表；其他模糊 token fail closed。
- claim 类型错误、负数、小数、非 canonical UID、溢出、空白身份均 401。
- DB 查询异常 fail closed；Controller 不得执行。错误响应不得透露账户存在性、state、当前 epoch 或匹配数量。
- `/resource` 与 `oauth.resource.uris` 下全部 Bearer JWT 路径使用同一组合 validator。

### Login, issuance and refresh

- `UserDetailsService` 对不存在、非 ACTIVE、无稳定 ID 或无非空 `jiacn` 用户统一认证失败，不泄露原因。
- 第三方自动登录在创建 Authentication 前重新读取并校验账户，不能使用之前第三方回调中的陈旧对象。
- `CustomUserDetails` 增加不可变 `userId`、byte-exact `jiacn`、`loginAuthEpoch`；所有构造点必须显式传值，禁止默认使用“当前 DB epoch”。
- JWT customizer 对用户 principal 写入 `token_kind=user`、`uid`、`jiacn`、`username`、`auth_epoch=loginAuthEpoch`；machine grant 写入 `token_kind=machine`。
- 每次 authorization-code、refresh-token 或既有 HttpSession 尝试签发用户 JWT 时，都重新按 user ID 读取 DB，要求 ACTIVE、exact jiacn 且 `db.auth_epoch == principal.loginAuthEpoch`。不匹配时必须重新认证，禁止把旧 principal 自动升级为最新 epoch。
- 必须用真实 authorization-code 与 refresh grant focused test 证明 Spring Authorization Server 各路径能恢复原始用户 principal；不能只假设 `JwtEncodingContext.getPrincipal()` 永远直接包装 `CustomUserDetails`。
- 生产 Web client 本阶段移除 refresh grant，浏览器不得依赖或保存 refresh token；其他仍支持 refresh 的 client 也必须受上述 issuance guard。

### `POST /user/me/sessions/revoke-all`

- Authentication: 仅通过组合 validator 的 Bearer `JwtAuthenticationToken` user token；form-login session、CTX Cookie、API Key、machine token 或匿名均为 401/403，零写入。
- Request: 无 body；不接受 `id`、`userId`、`uid`、`jiacn`、`authEpoch` query/body 参数作为主体或 CAS 值。
- Subject: 新 token 使用 JWT `uid` 和 `auth_epoch`；legacy user token 仅由服务端 exact `jiacn` 解析 user ID，expected epoch 固定为 0。不得使用 `sub`、username 或 CTX。
- Mutation 是单条原子 SQL，不得先读后写或失败后以新 epoch 重试：

```sql
UPDATE user_info
SET auth_epoch = auth_epoch + 1
WHERE id = :userId
  AND auth_epoch = :expectedEpoch
  AND account_state = _ascii'ACTIVE' COLLATE ascii_bin
  AND auth_epoch < 9223372036854775807;
```

- Success: 恰好更新 1 行并提交，HTTP 204、无 body；该 token 随即 stale。
- CAS race/stale: 更新 0 行且 expected epoch 非 Long.MAX 时，HTTP 409 `SESSION_EPOCH_CONFLICT`；不读取并泄漏失败原因，不再次 increment。两个并发相同 token 最多一个成功。
- Exhaustion: token expected epoch 为 Long.MAX 时直接 HTTP 409 `AUTH_EPOCH_EXHAUSTED`，零写入且不回绕。
- Invalid/stale/inactive token 若在 validator 阶段发现，HTTP 401 `invalid_token`。
- GET/PUT/DELETE 或路径近似匹配不得产生写入。

### API Key account gate

- API Key 自身存在、启用且未过期后，再按其 nonblank `jiacn` 做 byte-exact 唯一用户查询；账户 state 比较依赖列级 `ascii_bin` 并保持 byte-exact。
- 0 行、多行、NULL/空白 jiacn、未知/非 ACTIVE state 统一认证失败；API Key 链不得信任 CTX。
- API Key 认证成功后显式覆盖 context 身份字段。
- `revoke-all` 只撤销用户 JWT/旧登录 principal，不改 API Key 行；账户仍 ACTIVE 时 API Key 继续有效，因此 UI 不得称其为“撤销所有凭证”。

### Module dependency rule

```text
user-core: UserEntity + CustomUserDetails + snapshot value types
user-api: AccountSecurityService narrow interface
user-mapper: exact identity read + auth_epoch CAS
user-service: AccountSecurityService implementation
oauth-service: login/issuance/refresh/API-key gates (already depends user-api)
oauth-resource: composed JWT validator + revoke controller; add user-api only
starter: assembles user-service and oauth modules
```

- revoke controller 放在 `oauth-resource`，避免 `user-service` 依赖 resource-server 类型。
- 禁止 `oauth-resource -> user-service/user-mapper`、`user-* -> oauth-*`、`common-service -> user-*`。
- `oauth-resource` 仅允许新增 `implementation project(':user:jia-user-api')`；主 starter 缺少 `AccountSecurityService` 实现时，对配置了用户资源 URI 的应用启动 fail fast，不能静默跳过账户 gate。

## Identity context, Cookie and CORS

- `EsContext` 是非权威兼容上下文；身份/ACL 永远只读 Spring Security 与 DB snapshot。
- `EsContextHolder` 增加 `clearContext()` 调用 `ThreadLocal.remove()`。
- `EsContextFilter` 每个 servlet 请求开始先清旧值并建立全新 context，最外层 `try/finally` 无条件 remove；无 Cookie、解密失败、解析失败都不得保留线程旧值。
- `EsSecurityContextFilter` 不得因 Cookie 已有 `jiacn` 提前返回。Bearer JWT 对 `jiacn/appcn/client_id/username` 逐字段覆盖，token 缺失字段即清空对应 Cookie 值；machine token 必须清空 Cookie 用户身份。
- API Key 成功认证也要覆盖/清空相应字段。
- CTX Cookie：`HttpOnly; Secure; SameSite=Lax; Path=/`。如果未来确认必须跨站，只能显式改为 `SameSite=None; Secure`。Web 不假设能删除 HttpOnly Cookie。
- `CorsConfig` 实际读取 `cors.allowed.origin.patterns`；prod/grey 改为该键且只允许 `https://kit.chaoyoufan.cn`，dev 可保留 localhost pattern。
- `allowCredentials=true` 时禁止 wildcard origin；授权服务器/API Key 错误处理不得手写 `Access-Control-Allow-Origin: *`。预检、正常响应、401 与 409 使用同一 CORS policy。
- allowed headers 至少覆盖 `Authorization, Content-Type, X-API-Key`，methods 至少覆盖 `POST, OPTIONS` 及现有业务方法。

## Frontend behavior

- `useApiStore` 提供：
  - `clearIdentity()`：精确删除 `api_token/userId/jiacn/openid`，重置 global user、`authorizationStarted` 以及认证派生的 SSE/WebSocket/消息状态；不得 `localStorage.clear()` 误删偏好或游客数据。
  - `revokeAllSessions()`：直接读取当前 token，不触发新的 OAuth 跳转；POST 撤销接口；204 成功；401 表示 token 已失效；409 仅 `SESSION_EPOCH_CONFLICT` 可视为并发撤销完成，其他错误交给 UI。
- “退出当前设备”：不调用 revoke endpoint，精确清理后 `router.replace('/')`。
- “退出所有设备”：二次确认，说明“不停用 Agent/API Key、不是注销账号”；请求期间禁用重复操作。204/401/`SESSION_EPOCH_CONFLICT` 后清理并回首页。
- 网络、5xx、`AUTH_EPOCH_EXHAUSTED` 或未知响应默认保留 token，显示可重试且不含服务端原文的错误，不虚假宣称已全局退出。
- 操作支持键盘、明确 focus、`aria-live` 状态；不得记录 token、claims 或原始敏感错误。

## Production Web OAuth client

Client ID `jiafewnnv58ec2379c` 目标状态：

- authentication methods：仅 `none`，client secret 为空/不可用。
- grants：仅 `authorization_code`。
- redirect URIs：仅 `https://kit.chaoyoufan.cn/oauth2/callback`；移除 localhost 与 Postman callback。开发回调使用独立非生产 client。
- scopes：仅 `openid`。
- `require-proof-key=true`；`require-authorization-consent` 保持现状，除非浏览器 smoke 证明需另立产品决策。
- access-token TTL `PT10M`；authorization-code TTL `PT5M`。
- refresh grant 禁用，Web 不接收或使用 refresh token。

应用前保存原字段字节值并生成精确 rollback SQL；应用后逐字段验证，并确认 `client_credentials`、secret token exchange、refresh、localhost/Postman callback 均被拒绝。

## Compatibility and rollout

1. 在 production-shaped MySQL 验证 fresh/upgrade/repeat、legacy exact lookup、非法 claims/state、并发 CAS 与 rollback prerequisite。
2. 生产先备份并复核 jiacn 审计，应用 additive schema migration；验证所有 289 个历史行 state/epoch，单独记录 1 个 NULL jiacn 用户。
3. 部署 API；当前生产是单 JVM、非滚动多实例，因此随机 JWK 不构成本次混合版本阻断，但仍是后续“持久签名密钥与轮换”发布缺口。
4. 部署 Web，验证两种退出、实时连接清理与错误 UX。
5. 收敛生产 Web OAuth client，做 PKCE 登录、claim/TTL、拒绝 grant/callback 和 `/user/my` smoke。
6. 回滚 Web/API 时保留 additive columns。若回滚到无 epoch validator 的旧 API，必须显式使已签发 token 和授权服务器 HttpSession 全部失效；禁止仅回退 JAR 后继续服务。当前重启随机 JWK 的副作用不能替代长期密钥轮换契约。
7. legacy token fallback 最迟在生产 client 收敛后 31 天复审移除。

## Decisions

- 使用稳定 `user_info.id` 的 `uid` 做新 token 定位与 CAS；`sub`/username 不承担账户身份。
- 保留 byte-exact `jiacn` 作为业务身份和 legacy 过渡校验，但不假设当前非唯一索引提供安全唯一性。
- 使用显式 `token_kind` 正向分类；仅严格结构的旧 machine token 获得临时兼容。
- 选择 per-user `auth_epoch`，不使用 JWT denylist；撤销是单行 CAS，资源请求执行权威账户读取。
- 自助注销延后为独立 `account-self-service-closure`，必须覆盖 immediate deactivation、epoch increment、API Key/Agent 停用、幂等请求、PII/outbox/外部清理与留存。
- 公共 Web client 不使用 refresh token；短 access token + auth epoch 是公测基线。
