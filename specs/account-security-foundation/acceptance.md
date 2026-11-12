# Account security foundation and global session revocation acceptance

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：账号认证、安全会话与撤销。**

### 必须验证的业务结果
登录/过期/退出与撤销后的新请求、跨账号资源访问、Web身份切换迟到响应；凭据不得出现在日志。

### 不回归边界
Cookie局部修复不等于全局撤销验收；不把显示名作为身份，不在每层重解JWT。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## Acceptance criteria

### Account and token gate

- [ ] fresh/upgrade migration 后 `account_state` 列为 ASCII/`ascii_bin`，每个现有用户精确为 `ACTIVE/0`；repeat 不改已有值。
- [ ] ACTIVE 用户新 access token 含 exact `token_kind=user`、canonical `uid`、byte-exact `jiacn` 和数值 `auth_epoch`；非 ACTIVE/缺身份用户不能登录或签发 token。
- [ ] 有效用户 JWT 仅在 uid/jiacn 对应同一 DB 行、state ACTIVE 且 epoch 相等时进入 Controller。
- [ ] 旧 token 缺 epoch 仅在 DB ACTIVE/0 时有效；首次 revoke 后永远失效。
- [ ] 非法 uid/epoch/token_kind 或空白 jiacn fail closed；显式 machine token及严格结构的 legacy machine token保持兼容，普通缺 jiacn token失败。
- [ ] stale authorization-code/refresh/HttpSession principal 不能自动升级到当前 epoch；生产 Web client 不支持 refresh grant。

### Global revocation and API Key

- [ ] `POST /user/me/sessions/revoke-all` 不接受客户端指定用户或 epoch，只使用 Bearer JWT 主体。
- [ ] form session、CTX、API Key、machine token、匿名、错误方法均不能执行撤销。
- [ ] 单次成功只把 epoch 加 1；两个并发相同 token 最多一次加 1，失败请求不重试到新 epoch。
- [ ] 成功提交后原 token 对 `/resource`、`/user/my` 和另一受保护 URI 均为 401。
- [ ] 账户非 ACTIVE 时已有 API Key 为 401；账户 ACTIVE 时 revoke-all 不直接禁用 API Key。
- [ ] Long.MAX epoch 不回绕；`active`/`Active`/未知 state 的 CAS 均零写入。

### Context and browser

- [ ] 同一 servlet 线程的连续请求不会继承前一请求 EsContext。
- [ ] JWT claims 覆盖/清空旧 CTX 身份，旧 Cookie 不能冒充 Bearer 主体。
- [ ] CTX Cookie 在生产为 HttpOnly/Secure/SameSite=Lax/Path=/。
- [ ] prod/grey CORS 仅接受 `https://kit.chaoyoufan.cn`，带 credentials 时无 wildcard origin。
- [ ] “退出当前设备”仅清理当前浏览器身份并回首页，不调用 revoke endpoint。
- [ ] “退出所有设备”有确认和影响说明；204/401/SESSION_EPOCH_CONFLICT 清理身份，网络/5xx/耗尽错误保留身份并显示可重试错误。
- [ ] 身份清理不删除主题、游客体验或其他无关 localStorage。

### Production OAuth client and release

- [ ] `jiafewnnv58ec2379c` 仅 `none + authorization_code + openid + PKCE`，生产 callback 精确，localhost/Postman/secret/client_credentials/refresh 均不可用。
- [ ] access token TTL 为 `PT10M`，authorization code TTL 为 `PT5M`。
- [ ] 迁移前备份权限 600，包含原 DDL/统计/client 行和可执行的精确 rollback SQL。
- [ ] 独立安全 Review 为 ACCEPT，focused API/Web tests、Gradle layering、lint/build 和线上 smoke 全部通过。
- [ ] API/Web commit 已推送，root integration pin 可复现，部署证据已记录。

## Verification evidence

- Architect verdict: ACCEPTABLE on 2026-08-24 after uid/token_kind/legacy/rollback and ascii_bin state revisions
- Independent security review: pending
- API revision: pending
- Web revision: pending
- Root integration revision: pending
- Migration backup/checksum: pending
- Commands/tests: pending
- Production deployment/smoke: pending
- Result: pending
