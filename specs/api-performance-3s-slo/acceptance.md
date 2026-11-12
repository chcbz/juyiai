# API 3 秒性能治理 acceptance

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：可用性优先的API性能观测与热点治理。**

### 必须验证的业务结果
按真实路由和同一请求观测首字/完成、SQL次数、字节与GC；失败不计性能成功；保留ACL/事务/幂等与原保护。

### 不回归边界
3秒与分位目标只作观测，不拒绝请求、下传deadline或强杀流。不是授权全接口改异步/建operation框架；本地构建发布另按根AGENTS执行600秒默认上限，保留工具限时行为，超限须向用户申请例外；不是业务请求deadline。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 2026-09-13 用户最新修订：可用性优先

**“不要直接拒绝请求，可以记录下来作为后续优化点，优先保证可用性。”**

本节覆盖下面历史的硬 deadline/超时结束描述：1s/2.5s/3s/5s 仅作为观测与优化目标，不得仅因超标拒绝、取消请求、跳过依赖或截断 SSE/AI。全局和依赖层均为观测，不向下游传播可执行的性能 deadline。不得用更大的任意阈值替换旧限制。

保留真实网络错误处理、明确配置的传输超时、用户/身份生命周期取消、账户和授权校验、事务、幂等与互斥；没有获得锁不得继续写或伪报成功。慢请求以安全日志、request ID 和延迟指标记录，作为后续优化点；不记录凭证或用户正文。普通发布仍保留本地必要功能/安全回归、同批次制品及健康核验，不靠快速失败满足性能数字。不恢复历史独立 Reviewer/release_guard 前置。


## Acceptance criteria

### A. 覆盖与分类

- [ ] 当前 API checkout 的全部 Controller mapping 被展开，并生成声明式 framework/management/error surface manifest；每个可发布 profile 的运行时 HandlerMapping 与 management/Actuator mappings 被采集，声明 surface 与运行时清单双向一致并有 exact tree SHA、依赖/profile 配置摘要和内容 hash。
- [ ] 多 method、多 path、继承、条件 Bean、框架/management endpoint 均被分类；Swagger/静态资源/CORS OPTIONS 即使不进业务 SLO 也必须出现在 surface inventory。
- [ ] registry 覆盖率 100%；默认 `SYNC_STANDARD`，显式例外只允许 `ASYNC_ACK`、`STREAM_FIRST_EVENT`、`TRANSFER_TTFB`、`EXTERNAL_REDIRECT`、`OPERATIONAL`。
- [ ] 新增/受影响route补分类和必要回归；未测明确列出，不新增全量性能CI硬门禁。

### B. 观测

- [ ] 每个规范化 route 可查看 count、p50、p95、p99、max、status/outcome、inflight；标签无 ID/URI 高基数。
- [ ] 每条慢请求可用 request/trace ID 关联网关、Spring、SQL/连接池、缓存和外部依赖主要耗时。
- [ ] 日志不记录 Authorization、Cookie、token、query、请求正文或用户敏感参数；现有逐请求参数 INFO 默认关闭；访问审计写库不再无界阻塞普通请求。
- [ ] Hikari pending/acquire、Tomcat busy、JVM GC pause、process CPU/memory、数据库慢查询/锁等待有可观测证据。

### C. 性能观测与优化目标（非运行时拒绝条件）

- [ ] `SYNC_CRITICAL`：逐 route p95 <= 500ms、p99 <= 1s，超出 1s 记录慢请求并继续。
- [ ] `SYNC_STANDARD`：逐 route p95 <= 1s、p99 <= 2.5s、`SLI_3s >= 99%`，有效已授权请求语义成功率 >=99.9%；超出 3s 继续处理，快速失败不计性能成功。
- [ ] `ASYNC_ACK`：p95 <= 1s、p99 <= 2.5s、99% ACK <=3s，超出 3s 记录而不取消受理；符合 operation v1 的提交/查询 method+path、完整 status view、单调 version/state、result/error、404 防存在性侧信道、ACL、幂等、原子性和保留期合同。
- [ ] `STREAM_FIRST_EVENT`：握手 p95 <= 1s，99% 握手及首个应用帧 <=3s；首帧慢不得强制结束；真实断线、认证失败和用户取消仍清理/退避。
- [ ] `TRANSFER_TTFB`：请求 body 接收完成后 99% ACK/响应头 <=3s，超出 3s 不主动终止传输；完整传输另有按大小分桶吞吐证据。
- [ ] `EXTERNAL_REDIRECT`：本系统 99% 本地处理 <=3s，超出 3s 继续处理，保留真实第三方失败与 state 安全校验。
- [ ] 固定场景、源码、负载与冷/热条件，报告真实样本数/时长和统计方法；不足以支持结论标insufficient，不以固定30分钟/10000样本/3轮作为统一门槛。

### D. 正确性与安全

- [ ] 性能优化不改变 ACL、租户/用户隔离、事务原子性、幂等、snapshot/SSE fencing 和现有兼容 contract。
- [ ] 聚义厅 map/roster 继续分别使用 `/agent/map` 与 `/agent/roster`；不重新引入 `/agent/active`；任务分配继续传显式目标 Agent。
- [ ] tenant/client/task/owner 与 identity 按 byte-exact 语义校验；版本为十进制字符串且单调；SSE 保持 live-before-replay、去重、gap/resync、授权重放、有界缓冲和断线清理。
- [ ] Web reducer 幂等并拒绝旧 generation/重复事件覆盖新状态，不引入第二状态源。
- [ ] 缓存键/失效覆盖该缓存实际依赖的租户、主体、资源及权限/数据版本，使用无歧义编码，不机械给公共定义缓存复制全部scope。由所属边界验证无越权泄漏，不逐帧重新鉴权或完整hash历史。
- [ ] 性能目标耗尽不触发取消；真实依赖断开、连接池耗尽、慢SQL和客户端取消按既有事务/幂等处理，不引入重复写。提交结果未知沿已有权威状态查询恢复，不仅为优化新建operation框架。
- [ ] 普通读保留已有显式重试策略，不按剩余性能预算拒绝；写接口不做无条件自动重试；分页窗口遵循业务合同；批量、上传和解码约束须有真实容量/安全依据并由对应责任层落实，不设任意统一上限。

### E. 首批热点

固定 100 Agent、1000 Task、约定 persona/scene 数据夹具：

- [ ] `GET /agent/map`
- [ ] `POST /agent/roster`
- [ ] `POST /agent/tasks/search`
- [ ] `POST /agent/tasks/status-counts`
- [ ] `GET /agent/personas/catalog`
- [ ] `GET /agent/scenes/{sceneId}/snapshot`

以上 route 均达到 `SYNC_STANDARD`，且 SQL 次数不随 Agent/Task 返回数量线性增长。

### F. 发布

- [ ] API/Web exact commit、tree SHA、route inventory hash、fixture digest、测试 selector 和结果已记录。
- [ ] API Gradle 通过 `cyf_orchestrator.py gradle` 串行执行；未对 unchanged tree 重复全套验证。
- [ ] 独立 `sol_reviewer` ACCEPT，最终 `release_guard` 放行。
- [ ] 生产发布后低频只读 smoke 和 24 小时 SLO 观察通过；无未经授权的生产压测。
- [ ] 每个例外含精确 method+route、justification、owner、contract reference、compliance 和 review_by；通配例外、pending compliance 或过期 review 一律阻止 accepted。
- [ ] 全部 registry route 达标后才将专题标记 accepted；滚动 28 天观察窗口达标后再讨论对外 SLA。

## Verification evidence

- API revision: pending
- Web revision: pending
- Root revision: pending
- Route inventory count/hash: pending
- Fixture digest: pending
- Environment: pending
- Commands/tests: pending
- Result: pending
- Contract reviewer: sol_reviewer R4 delta ACCEPT P0/P1/P2=0/0/0（R3 两项 P2 已收敛）
- Implementation reviewer: pending
- Release guard: pending
