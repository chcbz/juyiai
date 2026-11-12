# Account security foundation and global session revocation tasks

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：账号认证、安全会话与撤销。**

**实施目标：** 登录认证→建立会话→业务授权→退出/撤销后拒绝新未授权请求。既有已接收执行的生命周期由对应业务合同决定，不为所有流式片段新增撤权查库。
**责任落点：** 认证入口维护会话/撤销事实；业务服务使用可信主体完成资源授权；Web清理本身份的状态。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：Cookie局部修复不等于全局撤销验收；不把显示名作为身份，不在每层重解JWT。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：登录/过期/退出与撤销后的新请求、跨账号资源访问、Web身份切换迟到响应；凭据不得出现在日志。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## API (`api/`)

- [ ] 新增 ASCII/`ascii_bin` `account_state` 与 `auth_epoch` 实体映射、枚举/安全快照、按 uid 与 byte-exact jiacn 的 DAO 查询及 CAS，并提供 additive/repeat-safe migration、preflight 和 rollback 材料。
- [ ] 用窄 `user-api` 接口实现账户状态读取和 `revoke-all` CAS，保持 Gradle layering 无环。
- [ ] 扩展 `CustomUserDetails(userId, jiacn, loginAuthEpoch)`，更新密码/短信/第三方登录构造点，拒绝非 ACTIVE 或缺稳定身份账户。
- [ ] JWT 签发显式 `token_kind`、`uid`、`auth_epoch`，严格兼容 legacy machine/user token，并阻断 stale authorization-code/refresh/HttpSession principal。
- [ ] 为 `/resource` 和 `oauth.resource.uris` 安装组合 JWT validator，严格处理旧/非法 epoch 和数据库失败。
- [ ] 在 `oauth-resource` 实现 Bearer-user-only `POST /user/me/sessions/revoke-all`，主体只来自 `JwtAuthenticationToken`，成功 204、CAS 冲突 409。
- [ ] API Key 认证增加 ACTIVE 用户 gate，验证 revoke-all 不直接禁用 API Key。
- [ ] 修复 `EsContextHolder` 生命周期、JWT/API Key 覆盖 CTX、CTX Cookie 属性、prod/grey CORS 键和错误响应 wildcard header。
- [ ] 增加 focused tests：登录/签发、validator、endpoint ACL/CAS/concurrency、API Key、CTX/CORS、migration。

## Web (`web/`)

- [ ] 在 API/global store 增加精确身份清理和 `revokeAllSessions()`，不得清空无关 localStorage。
- [ ] 个人中心增加“退出当前设备”“退出所有设备”、影响说明、确认、忙碌、错误与无障碍状态。
- [ ] 成功/已失效后 `router.replace('/')`；网络/5xx 保留身份并允许重试。
- [ ] 增加 store 与 `UserProfile` 定向测试，运行 ESLint 和 production build。

## Integration and verification

- [ ] 独立 `sol_reviewer`/`adversarial_reviewer` 审查身份来源、依赖环、JWT validator、refresh、CAS race、migration 和数据泄漏。
- [ ] 所有 Gradle 命令使用 `flock /tmp/cyf-gradle.lock`；记录 tree SHA、test selector 与 DB fixture digest。
- [ ] 在 production-shaped MySQL 验证 fresh/upgrade/repeat、rollback prerequisite、Long.MAX、未知 state 和双并发 CAS。
- [ ] 对生产 OAuth client 原行做权限 600 字节级备份，生成精确 rollback SQL，并完成目标字段迁移。
- [ ] 验证 PKCE authorization-code 登录、10 分钟 token、5 分钟 code、`client_credentials`/refresh/secret/Postman callback 拒绝。
- [ ] API/Web 分别提交并推送；执行 `./sddw pin account-security-foundation` 与 `./sddw verify account-security-foundation`。
- [ ] 精确提交根 SDD 与 api/web gitlinks，不包含并行 control-plane 或 E13 改动。
- [ ] 按 schema → API → Web → OAuth client/smoke 顺序部署，记录备份、部署和线上 revoke 证据。
- [ ] 创建下一阶段 `account-self-service-closure` SDD，不复用危险的通用 delete endpoint。
