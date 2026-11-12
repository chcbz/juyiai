# API 3 秒性能治理

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：可用性优先的API性能观测与热点治理。**

### 责任与业务流程
各责任模块减少查询/序列化/IO；现有观测入口记录耗时；主机工具负责发布资源。

固定场景基线→定位CPU/内存/磁盘/SQL/网络与排队→最小责任层修改→同输入复测→记录剩余长尾。

### 明确边界
3秒与分位目标只作观测，不拒绝请求、下传deadline或强杀流。不是授权全接口改异步/建operation框架；本地构建发布另按根AGENTS执行600秒默认上限，保留工具限时行为，超限须向用户申请例外；不是业务请求deadline。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
按真实路由和同一请求观测首字/完成、SQL次数、字节与GC；失败不计性能成功；保留ACL/事务/幂等与原保护。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留性能观测/热点治理和证据；不把3秒目标恢复成拒绝/截流门禁。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


## 2026-09-13 用户最新修订：可用性优先

**“不要直接拒绝请求，可以记录下来作为后续优化点，优先保证可用性。”**

本节覆盖下面历史的硬 deadline/超时结束描述：1s/2.5s/3s/5s 仅作为观测与优化目标，不得仅因超标拒绝、取消请求、跳过依赖或截断 SSE/AI。全局和依赖层均为观测，不向下游传播可执行的性能 deadline。不得用更大的任意阈值替换旧限制。

保留真实网络错误处理、明确配置的传输超时、用户/身份生命周期取消、账户和授权校验、事务、幂等与互斥；没有获得锁不得继续写或伪报成功。慢请求以安全日志、request ID 和延迟指标记录，作为后续优化点；不记录凭证或用户正文。普通发布仍保留本地必要功能/安全回归、同批次制品及健康核验，不靠快速失败满足性能数字。不恢复历史独立 Reviewer/release_guard 前置。


## Problem

CYF 当前后端是单体 Spring Boot 多模块工作区，当前 checkout 静态扫描覆盖 42 个 Controller、约 401 条方法级 mapping。历史接口审计只覆盖 381 个文档端点，知识库基线覆盖 38 个 Controller / 393 条 mapping，因此性能专题必须先建立“全部现役路由可枚举、可分类、可度量”的统一清单，不能只优化聚义厅的几个热点接口。

2026-09-08 的只读生产诊断已观测到聚义厅普通接口存在秒级至数十秒长尾，例如 `/agent/map`、`/agent/roster`、`/agent/tasks/search`、`/agent/tasks/status-counts`、`/agent/personas/catalog`、`/agent/scenes/{sceneId}/snapshot`。当前代码同时存在 60 秒 RestTemplate/Ribbon/Elasticsearch/MCP 等依赖超时、30 秒数据库连接获取超时、默认 `Integer.MAX_VALUE` 的分页大小，以及按请求打印参数和 JVM 内存信息的日志拦截器。另有 `UriAccessLogFilter` 在业务处理前同步写访问审计库；这些机制可能放大排队、日志 I/O、无界列表和依赖故障，却不能形成按规范化路由统计的 P95/P99 闭环。

## Goals

1. **普通同步 API 全部进入 3 秒 SLO：** 固定验收环境和负载下，每个规范化路由 `p95 <= 1s`、`p99 <= 2.5s`，`99%` 的合格请求在 `3s` 内得到完整成功响应；超标请求继续处理并记录耗时；性能目标不再作为运行时拒绝条件，快速失败不能计作性能成功。
2. **所有现役 API 100% 分类：** 声明 surface（Controller 展开 + framework/management/error manifest）与每个可发布 profile 的运行时 HandlerMapping/management mappings 双向核对；新增路由默认进入普通同步3秒观测分类。SSE、AI 流式、文件传输、异步任务和外部授权回调必须以精确 method + route 显式登记，不能通过条件 Bean、框架端点、通配例外或漏记规避观测。
3. **端到端可观测：** Nginx、Spring、SQL/连接池、缓存和外部依赖使用同一 request/trace 标识，可按 route、status、outcome、依赖类型查看直方图、并发和错误。
4. **优先消除根因而非加长超时：** 批量查询替代 N+1，数据库分页/聚合替代内存分页，缓存具有授权边界和失效策略，长任务改为 3 秒内 ACK 后异步执行。
5. **性能回归成为优化依据：** 新增或修改 API 保留分类、固定数据集和可重复的性能证据；超标形成优化待办，不为凑数字拒绝业务，未达标不得宣称性能目标已完成。

## Non-goals

- 不承诺所有 AI 回答、SSE 连接、文件完整上传/下载或长任务在 3 秒内完成；这些接口以ACK、响应头或首个应用帧3秒内到达为观测目标，不作为强制超时承诺。
- 不以统一强杀 3 秒代替事务、幂等、补偿和取消设计；已开始的写事务不得因客户端断开而产生未知提交状态。
- 不在生产环境直接做未经授权的压测，也不通过盲目增大 JVM、Tomcat、Hikari 或代理超时掩盖排队。
- 不在本专题中重写所有业务模块；按观测到的长尾和用户旅程分批优化。
- 不把一次 curl、少量样本、HTTP 200 或健康检查等同于全部 API 已达标。

## Scope

### API

- 路由清单与 SLO 分类注册表，默认普通同步 API 适用 3 秒观测目标。
- Spring Boot / Actuator / Micrometer 请求指标、慢请求结构化日志、request-id/trace-id 透传。
- Hikari、Tomcat、JVM、SQL、Redis、RabbitMQ、LDAP、Elasticsearch、AI/SMS/微信等外部依赖的耗时观测及既有传输超时配置。
- 聚义厅首批热点链路：map、roster、persona catalog、task search/counts、scene snapshot。
- 列表批量查询、数据库分页/聚合、缓存、索引、事务缩短、长任务异步 ACK。
- 统一性能测试夹具、分位数计算、路由覆盖和优化记录。

### Web

- 普通请求耗时观测、显式 AbortController 取消；不设置隐式性能取消总预算，不自动重试写操作。
- 聚义厅地图必要数据优先，roster/catalog/counts 按需加载，分模块 loading/error。
- SSE/AI 流式单独计算连接、首帧、重连，不套用完整响应 3 秒规则。
- RUM 上报用户侧请求耗时，并与后端 route/request-id 关联；不得上报 token、Cookie、正文或用户敏感数据。

### Operations

- Nginx 记录安全的 upstream connect/header/response 时间和规范化 URI。
- 在隔离预发环境执行 1、5、10、20 并发阶梯和持续测试；生产只运行低频、受控、只读合成探针。
- 建立 SLO 看板、慢路由清单和优化待办，不以无依据的耗时阈值阻断发布或运行请求。

## Constraints and risks

- 当前 root、api、web checkout 都存在大量其他任务状态；实施必须使用任务/worktree/path 级 Owner，不能覆盖现有改动。
- 每次 Gradle 调用必须通过 `python3 ops/orchestration/cyf_orchestrator.py gradle`，并复用 exact tree/selector/fixture evidence。
- 生产与开发/构建资源争用会污染基线；容量结论只能来自资源隔离、数据固定的环境。
- Micrometer route 标签必须使用 Spring 模板路径，禁止原始 URI、用户 ID、task ID 等高基数标签。
- 缓存必须包含租户/用户/ACL 边界并有版本或失效策略，不能为性能牺牲权限正确性。
- 真实网络失败必须保留可重试性、幂等和明确错误语义；不能让超时变成重复扣款、重复任务或未知事务结果。

## Existing evidence

- `docs/implementation/handoffs/JY-PERF-SLA-20260908.md`：2026-09-08 生产只读诊断、聚义厅长尾样本和资源边界。
- `docs/project-api-endpoint-audit.md`：2026-07-18 的 381 个文档端点审计。
- `docs/knowledge-base/04-backend-api-inventory.md`：2026-08-15 的 38 Controller / 393 mapping 静态基线。
- 本专题 2026-09-11 当前 checkout 只读复核：42 Controller / 401 方法 mapping；最终数字以 PERF-01 exact-tree inventory 为准。
