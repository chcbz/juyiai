# 公共公测发布与安全整合

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：公测范围与真实交付验收。**

### 责任与业务流程
Owner按特性范围核对安全/功能/运维证据；既有发布工具负责安装事务。

固定候选和公测范围→必要测试→本地不可变制品→获授权安装→健康与真实用户主流程验收。

### 明确边界
不是所有规划功能的自动启用许可；开发、安装、健康、业务验收不能合并为一个PASS；资金/生产迁移须已有实际授权。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
身份/ACL、真实onboarding、关键用户旅程、已知限制、制品摘要与恢复边界；600秒只作整批墙钟目标。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留跨功能公测安全与实际onboarding未完成验收，不当作单次版本发布临时稿。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


## 目标与范围

按认证 tenant/client 隔离托管 Profile 与任务列表/计数，服务器运行密钥不出浏览器；公测 onboarding 与安全 preflight 集成。账号注销、交易、语音启用不随本包自动纳入。

## 非目标

本次文档更新不创建新功能实现、不允许跳过现有安全合同、不宣布未验证的生产交付。

## 权威输入

- `docs/implementation/handoffs/PWA-PREFLIGHT-SAFETY-P1.md`
- `specs/account-security-foundation/design.md`
- `specs/oauth-public-client-hardening/spec.md`
