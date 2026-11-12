# API 3 秒性能治理 tasks

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：可用性优先的API性能观测与热点治理。**

**实施目标：** 固定场景基线→定位CPU/内存/磁盘/SQL/网络与排队→最小责任层修改→同输入复测→记录剩余长尾。
**责任落点：** 各责任模块减少查询/序列化/IO；现有观测入口记录耗时；主机工具负责发布资源。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：3秒与分位目标只作观测，不拒绝请求、下传deadline或强杀流。不是授权全接口改异步/建operation框架；本地构建发布另按根AGENTS执行600秒默认上限，保留工具限时行为，超限须向用户申请例外；不是业务请求deadline。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：按真实路由和同一请求观测首字/完成、SQL次数、字节与GC；失败不计性能成功；保留ACL/事务/幂等与原保护。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 2026-09-13 用户最新修订：可用性优先

**“不要直接拒绝请求，可以记录下来作为后续优化点，优先保证可用性。”**

本节覆盖下面历史的硬 deadline/超时结束描述：1s/2.5s/3s/5s 仅作为观测与优化目标，不得仅因超标拒绝、取消请求、跳过依赖或截断 SSE/AI。全局和依赖层均为观测，不向下游传播可执行的性能 deadline。不得用更大的任意阈值替换旧限制。

保留真实网络错误处理、明确配置的传输超时、用户/身份生命周期取消、账户和授权校验、事务、幂等与互斥；没有获得锁不得继续写或伪报成功。慢请求以安全日志、request ID 和延迟指标记录，作为后续优化点；不记录凭证或用户正文。普通发布仍保留本地必要功能/安全回归、同批次制品及健康核验，不靠快速失败满足性能数字。不恢复历史独立 Reviewer/release_guard 前置。


任务执行状态只进入 `docs/implementation/TASKS.yaml#runtime_ledger_json`；本文件定义工作分解和依赖，不构成第二份运行台账。

## Phase 0：合同与基线

- [ ] `PERF-00`（main_orchestrator，root docs）：冻结 SLO、route 分类、固定负载、数据夹具、异常口径和证据格式。
- [ ] `PERF-01`（routine_worker，root tooling）：生成 Controller 展开清单 + 声明式 framework/management/error surface manifest，并在 grey/prod-like exact candidate 上采集运行时 HandlerMapping/management mappings；双向比对、校验 registry，输出 profile/count/hash。
- [ ] `PERF-02`（gpt_test_runner，只读）：在隔离环境建立未优化基线；禁止生产压测，记录 exact API tree、fixture digest、JDK/DB/CPU/内存和缓存冷热。
- [ ] `PERF-03`（sol_reviewer，只读）：独立审查 SLO 是否可测、例外是否被滥用、样本数与分位数是否足够。

## API (`api/`)

### Phase 1：观测与预算

- [ ] `PERF-A01`（Owner负责；旧角色已退役）：加入低基数 Micrometer route histogram、inflight、deadline/slow counters 和 Hikari/Tomcat/JVM 暴露；owned paths 预计为 common starter/service 与 starter 配置。
- [ ] `PERF-A02`（Owner负责；旧角色已退役）：安全 request ID/trace ID filter 和慢请求结构化日志；替换默认参数 INFO 日志，不记录敏感值。
- [ ] `PERF-A02B`（Owner负责；旧角色已退役）：将同步访问审计写库从普通请求关键路径移出，冻结 after-commit/outbox/失败降级与审计不丢失边界。
- [ ] `PERF-A03`（Owner负责；旧角色已退役）：实现 deadline 仅观测且不向下游传播，保留真实 timeout/error contract；Owner 自检写事务、幂等和取消边界并补本地定向回归。
- [ ] `PERF-A04`（Owner负责；旧角色已退役）：为 DB、Redis、LDAP、Elasticsearch、Rabbit、外部 HTTP/AI/SMS/微信建立分层耗时观测；不裁剪既有传输超时、不添加基于 SLO 的默认短超时或调用前拒绝。

### Phase 2：聚义厅热点

- [ ] `PERF-A10`（Owner负责；旧角色已退役）：`/agent/map`、`/agent/roster` 的 persona/task/status 批量读取，保持 map/roster 分流、byte-exact identity 与 tenant/client/owner ACL，SQL 次数固定上界。
- [ ] `PERF-A11`（Owner负责；旧角色已退役）：`/agent/tasks/search` 过滤、授权、分页下推 SQL；保持请求/响应、排序、显式目标 Agent 和 ACL 兼容。
- [ ] `PERF-A12`（Owner负责；旧角色已退役）：`/agent/tasks/status-counts` 数据库聚合；与 search 使用同一 byte-exact 授权范围。
- [ ] `PERF-A13`（Owner负责；旧角色已退役）：persona catalog 版本化缓存；缓存 scope/失效 after-commit，用户绑定态不进入共享缓存。
- [ ] `PERF-A14`（Owner负责；旧角色已退役）：scene snapshot 一致性和查询降本，不破坏十进制版本、单调 generation、snapshot/SSE fencing。
- [ ] `PERF-A15`（Owner负责；旧角色已退役）：Chat/Agent SSE 有界缓冲、首帧耗时观测（不取消）、断线/慢消费者清理、live-before-replay、gap/resync 和授权语义。
- [ ] `PERF-A16`（Owner负责；旧角色已退役）：统一 operation v1、幂等、ACL、原子 outbox、状态查询和保留期；逐 endpoint 审计后才允许 `ASYNC_ACK` compliance=pass。

### Phase 3：全模块批次

- [ ] `PERF-A20`（explorer，只读）：按 p99 × 流量 × 错误预算生成 user/material/isp/task/chat/wx/sms 等模块的优化排序；输出 acceptance -> paths -> tests -> dependencies 矩阵。
- [ ] `PERF-A21-USER`（Owner负责；依赖 A01-A04）：owned paths 限 `common` 分页合同与 `user` list/service/mapper/test；统一 page size 上限，消除 `/user/list` 3N 查询并保持全部 ACL/排序兼容。
- [ ] `PERF-A22-EXTERNAL`（Owner负责；依赖 A03-A04）：owned paths 限 `sms`、`oauth` 外部回调/client/test；统一慢调用观测、幂等和真实失败语义，禁止事务内网络调用。
- [ ] `PERF-A23-LONGOPS`（Owner负责；依赖 A16）：owned paths 限 `task/job`、`material/news`、`wx` 长同步操作及 operation/outbox adapter/test；逐 route 版本化迁移为 `ASYNC_ACK`，不得静默改变旧接口。
- [ ] `PERF-A24-<MODULE>-<SEQ>`（默认 critical_worker）：后续每批必须在唯一运行台账展开为独立 ID、exact base、依赖和不重叠 owned paths；仅当只涉及冻结合同下的机械投影/mapper 修改且无 ACL/事务/缓存/异步风险时，才可由 main_orchestrator 经 sol_reviewer 预审后改派 balanced_worker。

## Web (`web/`)

- [ ] `PERF-W01`（Owner负责；旧角色已退役）：普通 JSON 请求 5 秒仅观测，保留显式传输超时、用户/身份取消和真实错误分类；移除隐式计时取消。
- [ ] `PERF-W02`（Owner负责；旧角色已退役）：聚义厅 map/snapshot 优先，roster/catalog/tasks/counts 按需加载和独立 loading/error。
- [ ] `PERF-W03`（balanced_worker，冻结合同）：SSE/AI 流式指数退避、jitter、连接去重、隐藏页暂停、认证失败停止重连；reducer 保持 generation fencing、去重、gap/resync 和幂等。
- [ ] `PERF-W04`（Owner负责；旧角色已退役）：安全 RUM request timing 与 request ID 关联，默认采样且不含敏感数据。

## Operations / deployment

- [ ] `PERF-O01`（runtime Owner）：Nginx 增加安全 upstream connect/header/response timing、request ID 和规范化 URI；保留配置语法和回滚证据。
- [ ] `PERF-O02`（runtime Owner）：生产运行与构建/测试/Agent 资源隔离；不跨线程终止进程。
- [ ] `PERF-O03`（release_guard）：建立 SLO dashboard、慢路由榜、错误预算和告警；低流量使用最小样本门槛。
- [ ] `PERF-O04`（release_guard）：每批发布前 exact SHA/fixture/selector gate，发布后只读 smoke；生产压测另行授权。

## Integration and verification

- [ ] 声明 surface（Controller + framework/management/error manifest）与每个发布 profile 的运行时 HandlerMapping/management mappings 双向一致；全部 surface 均已分类，未知、动态未展开或 profile 差异 = 0。
- [ ] 聚义厅六个热点 route 在固定数据集下 p95 <= 1s、p99 <= 2.5s、3s 内完整响应/明确失败。
- [ ] 全部 `SYNC_*` route 逐模块具备足量样本；不能用总体平均值替代逐 route 证据。
- [ ] SSE/AI首帧、异步ACK、文件TTFB按各自观测口径记录，并验证真实错误/取消场景；不因性能目标拒绝或截流。
- [ ] 数据库查询次数、连接等待、GC、外部依赖耗时和错误可通过 request/trace ID 关联。
- [ ] gpt_test_runner 验证后由 sol_reviewer 独立审查；最终 release_guard 只读放行。
