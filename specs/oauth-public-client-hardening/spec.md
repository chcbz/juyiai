# OAuth public client hardening

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：OAuth公共客户端与回调边界。**

### 责任与业务流程
OAuth认证适配器执行协议/状态绑定；业务入口使用认证结果。

发起授权→合法回调校验→换取认证结果→建立本站会话→授权读取业务。

### 明确边界
第三方回调保持提供方协议，不能机械套本站JWT/Q-R信封；合法重定向、状态绑定与凭据保护不因优化删除。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
合法/错误state和重定向、重复/过期回调、公共客户端无私钥假设、令牌不出现在日志、UTF-8解码不污染身份。

**状态：** 已闭环（released；OAuth 公共客户端加固已生产发布）。最终规格以本文为准；发布/验收证据见 [integration.yaml](integration.yaml)。过程文档已删除。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留OAuth独立安全合同和原发布证据，不扩大到全部账号/公测安全完成。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


<!-- SDD delivery reconciliation 2026-09-06 -->
## Problem

The browser OAuth2 authorization-code flow uses the callback `state` value as a navigation path without validating a locally bound transaction. PKCE verifier material is stored in localStorage and logged, callback failures silently return home, authenticated request retries can continue without a token, and the OAuth resource module exposes `GET /resource` with a null body and no exact JWT-only security boundary.

## Goals

- Bind every browser authorization callback to one unpredictable, short-lived, same-tab transaction.
- Keep post-login navigation separate from provider-controlled callback parameters.
- Consume PKCE material once, remove secret logging, and fail closed on malformed token responses.
- Provide a recoverable callback status/error page without rendering raw provider errors.
- Prevent missing-token and 401 paths from issuing or replaying unauthenticated requests.
- Make `GET /resource` a stateless Bearer-JWT identity projection with an allowlisted response.

## Non-goals

- Refresh-token issuance, storage, rotation, revocation, or logout.
- Account deletion, provider unlinking, or tenant deletion.
- General redesign of every OAuth resource matcher or user profile endpoint.
- Migration away from the existing `api_token` access-token storage key.

## Scope

- API: `api/oauth/jia-oauth-resource` controller, identity DTO, exact security chain, and focused tests.
- Web: OAuth transaction utility, API store, callback page/route, authenticated HTTP retry behavior, and focused tests.

## Constraints and risks

- One implementation Owner per task; independent tasks may write concurrently in separate worktrees with non-overlapping owned paths. API/Web commits remain independent.
- All Gradle commands hold `/tmp/cyf-gradle.lock`.
- Existing unrelated dirty changes in `api/`, `web/`, and root must not be staged or reverted.
- Production refresh-token behavior is unverified and remains disabled.
- Existing localStorage access-token exposure to same-origin XSS is a residual risk outside this packet.
