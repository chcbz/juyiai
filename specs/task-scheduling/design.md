# 统一调度设计候选

## 租约调度职责（2026-11-12现行）

租约绑定用户与Agent，不绑定Runtime主进程；30天续费任务只依赖租约、自动续费开关及可用余额，不读取心跳/在线状态，也不等待主机adopt、stop或cleanup。永久失联与主动离线按相同规则继续续费。

存量登记由正式维护事务同时写TRANSITION与首次到期待办，明确planId，不根据控制路由猜套餐。FINISHING按套餐分支：自行部署只处理平台任务/资金及精确旧授权撤销，不做主机清理；托管保留自身资产隔离后再释放。历史命令与原收费事实不重写。候选状态见[handoff](../../docs/implementation/handoffs/RUNTIME-LEASE-SEPARATION-20261112.md)，以下旧批次实现说明不作为本次整链通过证据。

2026-11-11核对API ed5010e882。当前沿用同库业务事实、单一调度入口及事务外Runtime交接，不假设跨库原子事务。下文说明设计职责；源码、分批验证与线上验收分别见[验收](acceptance.md)，不把历史“尚未实现”描述当当前状态。

## 责任与依赖
业务模块依赖task-api/core，提供处理器及可信业务键；task-service实现调度，不能反向依赖agent/chat/economy-service。保留现有JobService消费者，补齐明确失败结果，不能以字符串错误包装成功代表执行成功。业务处理器明确是否允许手动触发；收费任务不能从任意HTTP params构造付款权限。

## 持久待办
新增task模块专属表`task_scheduled_work`，与task_plan/item隔离；DDL候选位于API `task/jia-task-mapper/src/main/resources/db/task-scheduled-work-v1.sql`，尚未迁移生产。
- 复合主键：tenant_id/client_id/handler/business_key/target_node；空target_node表示集群任务，非空表示指定节点。业务引用不落用户正文或凭据。字符串使用utf8mb4_0900_bin，大小写和尾空格不合并。
- 字段：version、requested_revision、due_at、claim_token、claim_revision、claim_until、next_wake_at。时间统一epoch毫秒；有在途claim时next_wake_at为claim_until，否则为due_at。没有额外完成状态枚举、completedRevision或并行的第二份状态机；空闲行保留版本，不在每轮完成时删建。
- 索引`(tenant_id,target_node,next_wake_at)`；范围查询在排序/LIMIT/锁定前限定可信进程tenant、节点归属及已配置client。全局任意client进程与固定client进程均不依赖HTTP上下文。表字段长度是SQL键存储界限，不向业务新增数量/时间门槛。
- `ScheduledWorkStore`从FixedTenantAdmissionPolicy取得tenant；内部业务键只带client/handler/business/node，调用方不能覆盖tenant。TaskTenantConfiguration仍仅处理旧表；新Mapper的每条存储SQL自行完整分区，以`@InterceptorIgnore(tenantLine="true")`跳过重复解析。实际回归发现JSqlParser会把FOR UPDATE SKIP LOCKED放到ORDER/LIMIT前；这里只避免新Mapper的重复改写，不取消其他Mapper的公共隔离。
- 登记加入调用方同库事务：确保行存在→锁定该键→状态转换→版本条件更新。不自动重试业务事务。取消不存在的键不插入空行。
- worker读取数据库当前时间，按到期索引`FOR UPDATE SKIP LOCKED`批量锁定并更新领取；提交后返回业务引用和claim。完成/重试/续租各自短事务读取最新状态，校验token/revision/租期并更新；执行中登记的新revision不被旧完成覆盖。版本CAS额外阻止陈旧快照写回。
- store已有条件装配，未在生产启用或执行DDL；真实持久化/协调测试不等于收费消费者已经完成。
- 单次到期、cron、合并事件分别定义触发身份；同一cron发生点不能因重复通知生成另一轮任务。
- 回调只传最小业务引用，不落用户正文或凭据。

## 事务与唤醒
1. 业务事务内登记可靠待办；提交后本地唤醒/Redis通知仅加速。通知失败不撤回已提交资金，也不丢待办；待办首次写入失败不能假报可靠登记成功。
2. 余额增加入口已定位EconomyPostingServiceImpl.postInTransaction：账号更新、分录及POSTED终态同事务。唯一updateAccountBalance生产调用在该类。
3. 在该事务识别USER/AVAILABLE账号的实际正向净变更，登记该用户的余额变化待办；重复posting直接replay，不制造第二个余额变化。统一posting仅报告余额事实，不查Agent表，不遍历租约，不现场调用续费。
4. 无欠费Agent的用户收到余额事件时，允许一次索引空结果，消费后不周期反复检查；这是事件驱动必要查询，不保证绝对零空查询。
5. 单个用户连续变化合并revision。处理时固定领取revision，执行中新事件增加requestedRevision；完成只确认已领取revision，剩余变化继续待办。
6. 定时改期/取消与旧claim并发使用版本核对；过期闹钟不能复活已移除关系。业务再次检查真实租期/资格是状态转换责任，不把调度消息当付款授权。

## 租费消费者（2026-11-11核对，未生产启用）
- 到期和余额增加合并到同一用户键`hosting-rent.reconcile-user`，避免两个事件入口分别竞争该用户余额。租约首次启用/手动续期也通过同事务`HostingLeaseChangeListener`登记，不把task依赖放进economy。
- 用户处理按`paid_through,lease_id`稳定排序，100行keyset分页，在限定tenant/client/user后加锁。到期ACTIVE与LOCKED同一条责任链处理；某项付不起仍继续后项。新变更只signal更早期限，每页资金事务提交前补读并登记该用户下一真实期限，避免较晚续费覆盖更早的其他Agent租期；后继期限在同一资金事务内登记，不能只在回调返回后补闹钟。无租约用户消费余额事件后不继续周期查询。
- `HostingRentRenewalServiceImpl`以数据库时间核实租期/连续锁定时长。AVAILABLE足够则内部`RENEW_HOSTING_RENT`直接从本USER/AVAILABLE记入系统租金收入；无外部部署不增加无意义预占步骤。现有posting承担借贷平衡、余额CAS和流水幂等，新模板只允许自身可用余额到指定租金收入，不允许代扣他人或动用预占。
- 扣款+租期+后继调度登记同库事务；幂等身份是scope/lease/旧paidThrough，不是调度revision。新期从成功扣款后的数据库时间开始固定30天，欠费时间不补收。
- 余额不足转LOCKED（欠费收尾、仍可续费恢复），起点固定为原到期时间，不因调度延迟重置。到达15天时转FINISHING（最终收尾），此时余额足够也不再扣费；登记`hosting-rent.finish`可靠待办。处理器负责旧事项终结、原执行停止、费用/技能回执收妥、私有清理及解除关系；保留公共实例/技能/仓库。分阶段源于数据库事务与外部I/O职责，不是双轨兼容；仍需实际部署验收才可启用。
- 整页先锁业务根，再处理钱款，最后发同事务租约变更；不能首条FINISHING先取得调度锁、后条付款再取得钱包锁。首期技能清单冻结、首费与基础周期价分离已有实现/定向证据；存量过渡和自行部署接入仍待完成，当前没有迁移生产数据。
- 当前结构还包含收尾证据、原安装关联与调度索引；以现有DDL/维护catalog及受控升级SQL为准。不新增CHECK、启动自动迁移或兼容旧列双轨。金额仍使用当前文整数账本，实际模型成本人民币6位精度不变。

## 锁顺序（已发现的真实风险）
现有posting锁序为调用方业务根→排序账户→escrow；追加调度待办登记后不能让调度worker持该待办行锁再进入钱包。
- 领取和结果写回分别使用短事务；claim事务提交后才调用业务。worker存储入口拒绝已有业务事务，避免误加入外部事务延长持锁；不采用REQUIRES_NEW挂起仍持有钱包锁的外层事务。
- 业务处理保留现有业务根/账户顺序，不持调度行锁等待扣款或网络。
- 同一待办的业务处理再次触发余额事件时也不得存在调度锁嵌套反转。
- 租期扣款幂等与调度claim不同：执行租约过期不证明旧进程已经停止，旧执行者写回受token约束；业务钱款仍由期次唯一事实防重复。

## 多容器与低空查
已实现RedisScheduleCoordinator与RedisScheduleWakeup候选，协调分区所有者并跨节点通知，数据库保存待办及claim事实。已核对common现有RedissonDistributedLock：未指定租期时采用watchdog锁，指定租期时固定到期；ILock仅包装释放，没有失锁通知/所有权查询契约。不能将拿锁成功视为永久所有者，不能跨线程转交解锁，也不能仅凭isLocked（可能属于其他节点）继续领取。协调实现需在task适配层明确同线程获取/释放及领取前所有权确认，数据库claim/CAS与费用幂等仍负责失锁并发安全；不为调度修改所有公共锁消费者。本机独占Redis双客户端所有权、通知、交接已验证；Redis不可用无降级用例为故障注入，不冒充真实集群故障演练。
- 所有者在启动/接管时读最近dueAt，设置一次性闹钟；到点按索引分批领取，执行后重新安排。
- 新的更早任务/余额事件通知所有者重新安排；收到无关通知不扫描全部业务表。
- 保留集中低频索引补查恢复提交后通知丢失，不允许各业务各自增加周期空扫。
- Redis故障不能无锁退化为所有容器自由调度。待办保留、到期入口按真实租期判断；既有事项执行不因调度故障强停。
- 只读核对主机PID4136为 `/home/isp/apps/redis/bin/redis-server`，位于root会话cgroup而非redis/redis-server同名systemd服务；未读取凭据或改进程。不能据此认定其高可用拓扑或将本机测试视为线上故障验收。

## 执行与迁移
- 定时线程只安排唤醒；慢业务不能挤占费用执行。线程池/队列容量沿实际配置确定，不发明资源门槛。
- 业务失败/等待外部事实/可重试异常区分；不自动重放结果未知的付费Provider调用。
- Memory旧@Scheduled和统一cron同时切换；TaskAlert虽有cron但旧executor未真实触发，不能随升级偷偷启用生产提醒。
- 派发队列只迁移唤醒，不复制其ACK/领取状态机。文件回执恢复在所属节点执行；SSE/语音心跳保留连接归属。
- fixed-tenant灰度/非执行节点继续禁用后台领取。不能以注册存在判定当前部署可执行。
- 旧业务定时器在该项正式切换时移除；不长期双跑，也不一次性删除未迁移任务。

## 必要保护的依据与验证边界
- 身份/分区：同名业务键可能属于不同租户、client或节点；固定进程scope与SQL分区限制错误领取，真实MySQL覆盖排序/LIMIT前隔离及节点归属。不是每层复制JWT解析。
- claim token/revision/到期与version：领取可因崩溃重新分配，迟到执行者不得覆盖现行状态。仅拒绝该次陈旧写回，不中断旧业务线程；资金期次幂等仍由业务负责。
- 正batch/lease和时间加法溢出：防止无效LIMIT、立即过期或溢出生成错误闹钟；不设业务SLO强制deadline。
- worker外部事务保护：防止钱包→调度→钱包锁序反转及回调时领取锁尚未提交。回归检查事务嵌套拒绝和另一连接在回调前可登记；真实钱包消费者并发切片已由HostingRentRenewalMySqlTest覆盖，生产多容器验收另计。
- 原型回归入口：API `ScheduledWorkStoreMySqlTest`，真实MySQL、生产DDL/Mapper/TaskTenantConfiguration/Spring事务；core `ScheduledWorkTest`与`JobRegistryTest`覆盖纯状态转换和注册。真实钱包扣款切片另见HostingRentRenewalMySqlTest，部署与真实Redis失锁尚未验证。

## 运行时与业务扩展（候选已实现，未启用）
- `TaskSchedulingConfiguration`只在`cyf.task.scheduling.enabled=true`装配。DDL由受控迁移执行，不由启动器自动建表；生产值未改。固定租户灰度进程可写自身分区待办，但现有`cyf.security.fixed-tenant.enabled=true`使运行时Bean不创建、不领取。
- `TaskSchedulingRuntime`在ApplicationReadyEvent后启动，避免早于JobRegistry初始化。集群与配置的node-id拥有各自协调器，共享同一有界worker容量；关闭停止领取，已接受业务不shutdownNow。各协调器使用单一线程获取、检查、释放Redisson watchdog锁。
- 运维显式提供`node-id/workers/batch-size/lease-ms/retry-ms/recovery-ms/owner-retry-ms`，没有新增吞吐、延迟或资源硬门槛。node-id须与本机资料归属一致、重启稳定，节点恢复任务迁移时核对。lease只约束调度claim与迟到写回，不中断业务请求。
- 空闲tick一次最近期限索引查询，不再做领取查询；未到期直接返回相对等待，时间来自数据库。满容量不查库，worker结束唤醒；SKIP LOCKED未领到任务按配置退避，不在过期索引上空转。恢复仅集中到期索引，不查询全部Agent。
- `ScheduledJobHandler`显式接入既有JobRegistry；旧handler/旧cron不会因升级自动启用。业务在worker线程执行、领取事务已提交；本机执行续租独立于集群owner，不把连接/执行心跳变成集群全局任务。普通通用执行接口拒绝此类handler，不能凭job-execute权限伪造付费执行上下文；原execute错误改为失败信封，status响应不变。当前Web源码未发现该执行接口消费者。
- 运行中通知以修订号保留，唤醒提示只带client分区，不带用户正文。重复键通知在同一Spring事务同步中合并；提交后异步发送Redis，发送失败不撤回已提交业务，集中恢复读取可靠待办。嵌套REQUIRES_NEW与外层回滚各自维护同步，不新增线程本地资源管理。
- `EconomyPostingServiceImpl`在POSTED写入后、事务提交前，仅对USER/AVAILABLE净增加发`EconomyAvailableBalanceListener.Increase`，重放不发；观察者只能同库登记，不做网络、查Agent或扣费，失败向外传播以回滚钱包/流水/待办。无观察者时不新增查询。
- `HostingRentBalanceWakeup`候选由`agent.hosting-rent.auto-renew-enabled=true`显式注册，订阅余额事实并登记`hosting-rent.reconcile-user`用户键，0表示立即待办，避免混用主机时间。启用必须有ScheduleService，不能默默丢掉通知；实际续费、关系收尾及私有交接已有实现和分批验证；完整组合结果见验收页，生产配置/迁移与线上验收未完成，不提前启用这两个开关。
- 当前已实现cron发生点/错过执行策略、已列消费者迁移、首期/技能费用与迟到回执处理；CONTROL/GENERAL容量分离已有定向验证。仍缺自行部署收费、存量迁移、生产配置及真实混合业务验收；本地有界线程池用例不冒充生产容量证明。

## 原生技能恢复的节点归属（2026-11-10候选，未发布）

`SkillInstallCommandWriter.writeManagement`在原技能订单/命令事务内登记`skill.native-delivery`，业务键为原delivery ID；不新增命令、尝试或退款。该任务使用实际配置的`cyf.task.scheduling.node-id`作为targetNode，因为原生WebSocket只存在于接入节点，不能交给任意集群owner发送。

`AgentSessionReadyListener`仅在后端已认证、注册回执已交付、本机执行目录就绪后调用，按该Agent分页补登记仍未完成的原命令；失败撤销注册并关闭连接供正常重连恢复，不依赖有损旧reconnect队列。回调若已无本机当前会话，则结束旧节点待办；新接入节点通过上述边界登记。原delivery/outbox的独立租约与CAS继续保护节点迁移，延期取原next_retry_at/lease_until/更新间隔，包含outbox独立租约，不做立即空转。

因此不保留每5秒业务扫描或每节点全Agent启动扫描；持久键恢复与真实连接注册承担这两个明确职责。费用/ACL/状态授权仍在原技能服务，调度只定位并唤醒。候选源码、验证及未完成事项以统一调度handoff为准，不能将此段当作生产启用证明。

## 显式cron与持久发生点（2026-11-10候选，基础已验证、未启用）

不能把`requestedRevision`当计划发生时间，不能应用启动即执行所有`JobHandler.getCron()`。候选新增`CronScheduleService.register`内部入口：一个可信client/handler/node对应一份明确表达式、时区及错过策略。仅接受已注册的`ScheduledJobHandler`，无HTTP注册接口；未登记的旧TaskAlert等不会自动启动。

`task_cron_schedule`仅保存表达式/时区/策略、启用状态及下一发生点，不承担执行租约；现有`task_scheduled_work`仍是唯一执行队列。原子事务锁定确切游标→登记目标handler的`cron:<epochMillis>`发生点→推进游标→登记下一闹钟。停机恢复或两个旧/新owner重叠回调不能重复生成同一发生点；无需按每个错过分钟循环，也无第二个轮询器。两个表的写入失败共同回滚。

- 相同定义重启保留原游标；显式配置改变只影响未来，已接受发生点保留。显式取消关闭未来闹钟，不中断已接受业务。
- `COALESCE`：错过多个时点时仅登记最早未处理发生点一次，然后转到当前数据库时间之后的下一时点；并非重放全部历史业务。
- `SKIP`：只有另一个后继发生点也已到期才跳过旧点；普通队列延迟几毫秒不算错过。时区/DST以各发生点的真实epoch区分。
- 计划时间/队列领取均基于DB时钟；回调只登记业务工作，不在持久事务内执行模型/网络。业务重试仍须核对原事实，通用cron不能提供外部付费调用的exactly-once保证。

DDL为受控迁移候选，不自动建表，不加CHECK。该基础候选未将Memory/Wx等消费者迁移完成，不能当完整统一调度上线证据；全局/固定client和慢任务容量仍需随实际消费者接线验收。

基础验证：API `6cd01771f1c3aea76ba75a052cb834a091904b2b` 已通过39项（12纯单测、3装配、24真实MySQL）及分层检查，详见统一调度handoff的cron-scheduling-1证据；业务消费者尚未接入，未生产迁移。

### 2026-11-10 内部租户维护调度范围

内部 ScheduleKey/CronSchedule 的 clientId 空串专用于租户级维护，不代表虚构客户身份；null/空白非该标记。只有进程 FixedTenantAdmissionPolicy 未限制 client 时可登记、执行、结算此类任务。固定 client 进程按既有 SQL 分区在 ORDER/LIMIT/锁前排除维护行；租户、节点、claim 所有权规则不变。准入仅在 task 的内部责任层实现，不放宽外部身份策略或业务 ACL，不新增轮询器。真实消费者必须另行核对业务 SQL 的租户/用户范围，基础支持不代表 Memory 等已迁移。

### 推荐费用磁盘回执恢复

`RecommendationUsageRecovery`显式登记节点绑定cron，默认UTC每分钟一次，配置`jia.chat.recommendation.usage-recovery-cron`；旧`usage-recovery-delay-ms`定时入口退役。仅统一调度启用时装配，不保留双定时器。节点标识须稳定绑定原节点持久磁盘，部署不得把其他节点身份指向空目录。启动时在JobRegistry初始化后登记，保留既有持久cron游标；SQL登记失败不伪报启动成功。周期游标独立于前台回执写入，因此SQL不可用期间留下的原始成本凭据可在恢复后重新入账，无需再次发模型请求。前台落盘/原价表/usage/ACL/账本幂等与ACK后删除不变。未启用统一调度的候选不应单独发布此切换。

### 原生会话/工作区待办提示恢复

本节点`NativeConversationWorkRecovery`统一cron默认UTC每30秒（`jia.chat.native-work.recovery-cron`），一次补查覆盖两个lane；只把本机当前订阅传给原发现服务，无订阅时不查业务库。原`NativeConversationWorkNotifier`保留事件提示合并和本地串行执行器，但不再创建定时器。数据库扫描失败交给统一调度的持久重试；单个提示发送失败不阻挡其他订阅，下轮恢复。停止的notifier不再补查，事件回调仍核对原执行器归属。该通知仅为hint，不改变原队列认领、身份围栏、执行费用或租约。

### 事项启动队列Bootstrap

Bootstrap保留原业务outbox认领/租约/CAS、就绪判断、Runtime-awaiting回写与1s～300s暂态退避；只把独立ScheduledExecutor/取消timer换成task的节点绑定固定恢复键。节点绑定保持每个Chat节点有机会处理本机就绪Runtime，不将本机能力误当集群唯一能力。原5秒漏通知恢复尺度保持，成功认领后即时继续；仍每次只认领一条，事件风暴在本节点合并后才写SQL。启动在ApplicationReady登记，停止不删业务队列、不打断已认领工作。

原进程内通知为afterCommit hint。该listener若需要提前统一调度期限，使用责任边界内REQUIRES_NEW短事务；失败仍由原publisher留日志，旧持久恢复键/业务outbox保留。不能让REQUIRED调度写入落在原已提交仍绑定的资源上。扫描回调自身无外层事务，用task正常同库写入。该切换不新增业务派发门禁、收费、人工审批或第二套timer；完整上线须同时启用统一task及Bootstrap原功能开关。

### Memory显式发生点与付费尝试边界（2026-11-10实施候选，未上线）

保留普通`memory_sync`手动处理器，移除其独立`@Scheduled`/异步定时入口，单独`chat.memory-sync`适配器显式注册原sync-cron、配置时区（默认Asia/Shanghai）、集群作用域和COALESCE。原手动/周期共享业务锁及pending重试语义保留，不把普通handler改为禁止手动调用的ScheduledJobHandler。

业务拥有同库`chat_memory_job_run`发生点回执：配置tenant/client和原cron epoch为唯一键，调用业务前在独立短事务提交STARTED，调用结束后在另一短事务写SUCCEEDED/FAILED/SKIPPED；模型/ES不在这两个事务内，也不在定时器线程。业务失败记FAILED只说明该批处理抛错，不证明外部调用没有发生。STARTED没有最终回执表示运行中或结果未确认，重派同一发生点不重做模型调用、不改写成成功，不通过异步入队返回值冒充完成；完成写入失败仍保留STARTED。下一计划发生点可重试原pending会话，与原周期行为一致，不声称跨不同计划发生点或手动调用的exactly-once。

该表不是第二条执行队列，没有独立扫描/过期接管timer，DDL只为受控迁移候选且不加CHECK。`task_scheduled_work`完成只说明调度回调结束，记忆业务结果以该回执为准。请求或付款人不能提供scope；mapper使用进程配置，结果写入以原start_token限定。需验证唯一发生点并发、已提交开始事实对独立连接可见、结束事务回滚、未知结果不重复模型、正常后续周期重试与原手动能力。生产启用前仍须完成记忆源SQL/ES实际分区与混合worker容量验证；本适配器源码不能单独当作Memory全功能验收。

### Memory源数据与向量分区（2026-11-10候选，未发布）

- SQL发现层从进程配置取得tenant和可选固定client，在cursor/group/LIMIT之前精确分区。会话父记录是身份来源，消息必须与父记录的tenant/client/account精确一致；活跃用户发现保留client/account组合，不再把同账号不同client合并，排除删除、系统消息和已标记排除的事项会话内容。会话快照继续使用原显式tenant DAO重载、父锁和生命周期检查，不复制入口认证。
- 仅真实三个消费者联动：长记忆服务、ChatController案卷读写、LongTermMemoryAdvisor；入口复用原可信client/account上下文，无Anonymous/默认client兼容。ES适配器从进程配置取得tenant，按tenant_id/client_id/jiacn精确keyword在KNN候选和普通query排序/limit前过滤，不靠取回后过滤提供隔离。会话与周期summary确定ID包含tenant/client/account；普通请求不能传tenant覆盖配置。
- 只读实测chat_memory alias现指chat_memory_v2，jiacn为keyword、向量1024维，没有tenant_id/client_id。发布前须固定实际alias目标并应用候选`chat/jia-chat-mapper/src/main/resources/db/chat-memory-scope-mapping-v1.json`的两个keyword字段，再readback；不运行自动mapping创建/启动修复，不在每个请求查询mapping。旧doc缺身份字段不命中新分区查询，不猜client、不复制给所有client、不降级owner-only检索。历史源会话仍在数据库，既有ES文档和公共数据不因本改动删除。
- ES映射变更/实际KNN回归与源码定向测试分别记录。这里只是候选实现，不能把mock查询结构断言当成真实ES检索证明。原数据库会话清理并未接入调度，本次不启用它；完整上线仍需混合慢任务/费用worker容量及其余费用生命周期回归。

### Wx每日发送迁移边界（2026-11-11调查基线，后续实现见下节）

旧`WxSchedule`的07:30 cron、Redis15分钟防重复锁、当日随机DelayQueue和ThreadRequest等待属于同一个业务消费者；迁移必须全部收口，不能仅替换cron注解。计划与每个订阅的原到期时间应在同库事务内落盘并登记ScheduleService，唯一业务键按租户/客户端/订阅/日期/消息种类固定；重复发现不重新抽取随机时间。使用统一调度完成重启恢复，不另加业务轮询或长时间sleep线程，不修改公共ThreadRequest工具的其他使用者。

统一调度领取不代表微信已发成功。发送前需要独立提交业务尝试事实，发送后的结果另行提交；同一发送的开始事实存在但结果未知时，不自动再发，不把调度回调结束冒充送达。保留投票成功且用户活跃时原两小时答题关联语义。测试使用假微信端，真实外部发送和生产数据不随源码验证触发。

本次读取的公共机制不能证明这条业务已隔离：task拦截器仅覆盖task表；BaseDao只过滤实体显式tenant；订阅发现、MpUser.findByJiacn取首条、MatVote.selectNoTick及MatPhrase随机查询目前均有实际未分区路径。下一实现只修这些真实依赖边界，使用可信订阅身份/进程配置，不往通用worker复制HTTP上下文、不扩大成所有DAO改造。需覆盖重启后随机期限稳定、并发计划唯一、发送未知不重试、原答题关联、SQL排序/LIMIT前身份隔离，以及慢发送与资金任务混合容量；文档不是已通过证据。

### Wx每日发送候选接线（2026-11-11，1807de23d4，未发布）

- `wx.daily-plan`显式注册07:30 Asia/Shanghai、SKIP cron；计划与单订阅receipt在同库短事务内落盘并signal。每页100条是发现分页，不是业务数量上限；按cursor连续处理。重复发现沿原due，不重抽随机时间；宕机跨日不补发前一天日常内容，已计划未发且跨日的receipt变EXPIRED。没有独立扫描、DelayQueue、ThreadRequest或Redis TTL防重timer。
- `wx.daily-delivery`读取冻结接收人，发送前重验订阅与取当前素材，独立提交STARTED后才访问微信，完成另事务；已STARTED/UNKNOWN和终态不重发。调度完成不等于送达，明确false记FAILED、异常记UNKNOWN，投票已被接受而答题缓存失败仍保留SUCCEEDED事实。无外部发送超时或付费重放门槛。
- 实际查询范围在各自DAO落实，可信tenant来自环境；订阅、recipient、模板定义与素材都先分区再LIMIT/RAND。已授权问题的选项继续按questionId读取。模板实例主键读取后核对tenant/client/appid才使用；共用发送实现遇到文本发送异常不再追加模板发送，明确false仍可fallback。
- 定时及Webhook出题、读答案指针、条件删除、退订统一使用已有WxDailyVoteKeys的appid/account哈希身份，保留2小时有效期；不保留owner-only双读或迁移生产旧key。接口没有新的外部scope参数，Webhook认证不变。
- 当前候选59项验证在途；真实计划+task原子性/多实例恢复、混合慢发送与费用容量、生产索引/配置/迁移/启用另验收，不把以上源码说明当作已上线证明。

## 首期总额与周期租金分离（2026-11-11已定向验证，未发布）

资金责任层固定报价的`amount_wen`为本订单预占/实扣/退款总额，`recurring_amount_wen`为基础周期租金；租约`amount_wen`仅复制后者，首期意图仍复制完整总额。正常续租报价两者相同，自动续费继续消费租约金额，不能从首期意图或总报价继承一次性技能费。报价记录保存基础金额，避免在预占时额外反查/锁定价格计划或改变既有锁顺序。新字段非空，无旧值兜底/在线自动补列，也不新增CHECK。

规则与风险：资金服务在消费已冻结报价时要求0<周期额<=订单总额，续期报价要求二者相等，避免错误负数或把一次性费用带入续租；失败仅拒绝该订单，既有事项执行不受影响。验证入口为`HostingRentLedgerServiceRealTransactionTest`新增真实H2事务用例：首单全额预占/实扣/幂等后基础金额续租、首费不足不产生账务、失败全额退款；它不冒充Runtime库存采集或首费报价生成已完成。字段随fresh DDL与schema catalog同步，生产需在最终快照/迁移方案中处理，不能单独上线这一schema变化。

### 首次收费公共技能库存（2026-11-11，候选实现，未上线）

Runtime新增只读`hosting.inventory`，请求只带可信tenant/client/owner及canonical Agent ID，路径和执行参数不接受外部传入。原host按subject门串行读取已有Agent；新托管Agent的已验证model-only模板不复制技能或插件、HOME/work尚未创建，返回空库存而不提前创建实例/关系。API仍负责报价/付款权限，Runtime不计算价格或收钱。

已有Agent复用本机经完整性核验的原生App Server，仅initialize/initialized→skills/list(forceReload)，不调用account/model/MCP、thread/turn或Provider。发现由引擎解析普通/插件/项目技能的原生语法，不复用受限安装预览YAML解析器；补充SkillInstallManager当前安装记录，含禁用，不读取历史保留版本，不包含system scope内置工具。Discovery HOME限定Agent自身HOME父目录，不继承服务账号的私人HOME。读取结束等自有进程退出，不创建第二个业务Agent实例。

返回类型/数量和稳定摘要，不返回本机路径、正文、凭证。原生技能revision为SKILL.md定义摘要；托管技能revision绑定当前安装ID、包树摘要、版本、enabled。同名冲突/引擎发现错误/安装期间变化不能猜成零或部分报价。该摘要表示安装库存及定义版本，不把公共仓库任意文件变化当作技能安装费事件。API已将摘要/数量冻结到首单、确认时复核并将首次种类数×50文加到订单总额；正常续租只基础租金。2026-11-11已对API9650453056/Runtime456fe04定向验证prepare最终库存确认，真实退款链补充另见下节。完整迁移及发布仍未完成，不能据定向通过单独启用收费。

接线前实测发现：本机原生库存冷启动含完整性核验约33秒，不能沿用现有快速控制通道2秒deadline，否则会永久出现“不可报价”。API新增operator-only `agent.hosting-rent.managed.inventory-timeout-ms`（默认60000，正整数可配置），库存RPC与包含库存读取的INITIAL prepare采用此传输超时，capabilities/observe及不读取库存的其他控制请求维持原值；依据上述实测而非构建时限。不下传至业务执行/模型调用，不因超时猜零费，尚无付款。完整性核验仍复用原worker按二进制事实缓存，库存仍强制刷新，不用TTL缓存冒充确认时库存。该配置和真实冷启动UDS→API验收须在最终发布前核实。

### 首期报价到Runtime prepare的最终库存闭合（2026-11-11，定向验证通过，退款补充验证中）
- INITIAL prepare携带已冻结报价的`quotedInventory={hostId,inventorySha256}`；它只用于prepare，不扩散到ensure/current/收尾关联字段。API从原quote读取，不能临时重算费用或替换订单库存。正常REPROVISION不重复收首费或重新冻结库存。
- Runtime复用subject门，在已清理的同实例重邀／新建候选之前读取库存并比较；成功将报价引用与原operation同时落盘，重复prepare只返回该持久事实、不用后来安装变化重写原结论。
- 库存不一致时在原operation journal持久化无candidate的拒绝事实，再返回`FAILED_NO_EFFECT/HOSTING_INVENTORY_CHANGED`及绑定原关联和报价引用的证据摘要；此时不分配新installation/secret、不注册／启动新关系。原intent即使重试、进程重启、库存恢复也不能转成成功。新报价必须用新intent。
- 缺库存、读取失败、持久化失败或响应不完整均为UNKNOWN，不触发释放预占。API只接受完整回显且与报价host一致的确定失败，复用现有failed-no-effect→refund事务；不新增退款引擎或新授权入口。历史已准备操作不补造库存证明；历史关联只读和收尾不因新prepare字段重写。
- 退款凭据处置仍归ManagedHostingCredentials（2026-11-11 API2751453c8e候选）：`FAILED_NO_EFFECT`的同一INITIAL/USER关联在现有资金事务内，只要installation/manifest/key均未签发且generation=0，就无需撤销不存在的key；旧key存在时仍撤销精确关联。Runtime关联已签发/残缺时不可假定无副作用，拒绝并回滚该笔退款，其他事项不受影响。防止库存拒绝错误冻结资金，同时避免撤权未证实却退款；回归为ManagedHostingCredentialsTest及HostingRentRenewalMySqlTest三项真实协作者/数据库用例。实现和测试终态见原handoff，不把候选当上线结果。

### 混合任务容量（2026-11-11实施目标，未验证/上线）
- 真实缺口：慢Memory/Wx及Runtime收尾占满既有worker后，到期/余额续费回调无法领取。独立续租心跳不能解决业务容量饥饿。
- 继续一个注册器、一个持久待办表、一组分区所有者/唤醒/claim恢复。处理器显式声明CONTROL（仅短数据库控制事务、不调用外部服务）或默认GENERAL；续费及cron游标推进声明CONTROL，模型/网络/Runtime处理仍GENERAL。通用task不识别费用/品牌/技能名。
- 同一runner中两组有界执行容量：现有workers用于GENERAL，新增由部署明确配置control-workers；两者共享现有心跳，不另开定时器/队列/账本。容量耗尽不领取、不空查询，已接受工作不强制中断。每个有容量分组只按自己最近期限唤醒，GENERAL占满不阻止CONTROL。
- 分类来自当前注册元数据；claim和nextDelay在SQL排序/LIMIT前按同一CONTROL handler集合包含/排除，不先领取再过滤。不改持久任务键、业务版本、授权、事务或执行恢复语义。未注册任务保留在GENERAL按既有失败重试，不猜执行。
- 为含handler的期限查询增加对应索引（只作为受控迁移候选），无CHECK/触发器。验证需含实际MySQL大量更早GENERAL到期下CONTROL先领取、跨tenant/client/node、慢任务占满时资金回调完成、容量释放/失败/停机不丢已接受工作，以及空CONTROL集合不发查询。

### 2026-11-11 原安装维护记账边界（实施候选，非上线状态）

公共知识提取费用属于平台维护，不是原用户的新执行。`POST /internal/agent/hosting-leases/{leaseId}/knowledge-usage`沿用统一Q/R和原请求/回执字段，认证单轨改为原Runtime installation bearer；不接受AgentRuntime普通会话、用户JWT或API key，不申请新session。Runtime只从原私有安装状态读取凭据，只调用该固定路径，不注册/重启执行器。

API复用Runtime-v1安装认证，在安装锁下验证ACTIVE与凭据摘要，再按installation→binding→initial intent→lease顺序校验原关系。只有原INITIAL已生效、安装/manifest匹配、租约FINISHING、executorStoppedAt已记录且handoverId匹配，才能记平台成本。身份来自原安装和绑定，不由请求指定；不依赖已停用原用户的登录状态/authEpoch。普通session、WS、事项执行及技能授权不变；该维护凭据不能当作新执行资格。

STARTED先落平台账再调用模型；RESPONDED使用原价快照和原attempt身份，重复/断线重投不重复记费。清理和关闭仍待平台费用回执交接完成；最后撤销原安装凭据，与记账共用安装锁避免关闭并发。需要同时验证账户停用、错误/撤销安装、错误租约/handover、未停机、已结束、普通session冒充和丢ACK重放；源码/测试/发布状态见现有handoff，不因本节写入视为通过。


### 存量静态实例关联（2026-11-11，候选实现，未切换生产）

- 新控制动作`hosting.adopt`复用protocolVersion=1消息封装及原hosting关联字段；`runtimeInstallationId`、裸`manifestSha256`、字符串`provisionGeneration="1"`必须对应已有运维配置中的同一tenant/client/canonical Agent。只接受INITIAL关联，operationId等于initialIntentId，不接受路径、profile、凭证、报价清单或命令。API必须先按原installation/identity/binding完成业务授权；Runtime只落实精确本机主体与writer所有权，不能据请求新建实例或导入安装身份。
- 回执为原字段完整回显加`outcome=ADOPTED`及hostId，只证明已有安装与该过渡租约的持久关联。**不是SERVICE_READY、预占/捕获或付费验收证据**。API须核对原hostId与全部关联字段；丢回执按原operation重试，不另建安装/重复收费。过渡登记由仅在schema-maintenance配置生效的HostingRentTransitionApplication显式调用：先锁原安装/关系取得快照，事务外adopt，再在同一锁序下复核并登记；不在启动时自动扫描。原输入固定cutoverAt和scope/binding派生的租约/意图ID，重放不得重置30天期限。运维批次入口位于starter的`cn.jia.maintenance.HostingRentCutover`（当前候选，验证与上线另记），生产切换仍待完成。
- 运维入口只装配明确列出的数据源/SSL/原有DAO、服务和同事务调度存储，不扫描全应用、不启动worker、HTTP或schema initializer。`--preview INPUT.json NEW-RECEIPT.jsonl`校验整批原身份/安装/关系与配置路由，不调用adopt、不建立钱包/租约；它不代表外部服务就绪或套餐DDL已准备。`--apply`在同样预检后逐项复用原register；需先按既有受控维护流程完成真实备份、必要DDL/套餐、可信控制配置和停止旧writer。没有新审批层或常驻迁移开关。
- 输入`cutoverAt`为固定真实切换毫秒时间，`subjects`逐项包含actorId/ownerJiacn/agentId/installationId；tenant/client只能来自维护进程配置，不能由文件覆盖。拒绝歧义JSON和同批重复Agent，防止资金主体或原始时间被悄然替换。输出新建JSONL回执（输入SHA、预检、逐条真实登记、最终完成）；发生异常不写最终完成项，已提交项保留，使用原输入和新回执文件幂等续跑。不得因重跑生成新cutoverAt来延长期限。
- 过渡原始意图使用`settlement_kind=TRANSITION`、amount=0，quote/reserve/capture/refund/serviceReady事实不伪造；租约本身保存正常套餐价，期满直接复用既有续费/欠费/收尾。关联起点只在该原始意图用createTime，付费意图继续使用reservedAt，不在金融记账路径增加猜测回退。四个原支付专属字段的nullable变更走显式DDL迁移，不在启动时自动执行。
- 免费接入不要求用户已经领取活动或拥有钱包。同一登记事务只幂等创建零余额AVAILABLE账户，保留既有余额、不赠款、不生成交易流水，再登记首次到期调度；调度失败整笔回滚。API78b1cb1c9b的65项及layering通过，含真实MySQL无钱包接入→到期LOCKED→15天FINISHING；仍不代表生产切换完成。
- 同一HostingControl journal保存静态profileId引用和关联，不复制HOME/配置/凭证；原运行实例、安装ID及既有会话保持不变。静态接入没有待消费注册密钥，其内部enrollment字段明确为null；不伪造过期时间或占位摘要。`template:null`表示宿主只管理既有静态实例，不提供新建托管能力；私有socket、scope、journal路径和所有权保护不变。
- 原`current/quiesce/evidence/cleanup`直接复用已有状态机。接入后重启不重注册、不自动将接入视为新执行；收尾已经停下的实例重启仍保持停止。最终清理仍要求原租约证据、私有清理和公共文件基线；公共技能/仓库保留，不新增收费引擎或清理分支。
- 静态实例清理后的重新邀请沿用原readmitAgent：保留同一公共实例、profile和HOME实体目录，只有安装/新关系身份更换；受控写回原manifestPath，复用原私有清理和关系准入。迟到旧关联不能停止或清理新关系。没有完成原交接不允许重新准入。
- 免费重整对任何现有安装统一使用安装责任层的`lockExistingInstallation`，不调用创建/确保待注册安装，不依赖注册密钥仍可取。初次新安装仍需完整enrollment信息；REPROVISION允许明确的两项null元数据，缺一项或初次省略均拒绝；后续绑定/租约/manifest/generation事务核对不减少，也不增加一次SQL读取。
- 定向证据：Runtime2488e71同源232项通过（含静态接入并发重放、重启、真实私有清理及同实例重邀；模型/原生注册明确fixture）。Java↔实际UDS↔Runtime的adopt/停止/证据/清理与安装锁回归已在固定API b49120979d通过62项及validateLayering（356.945秒），证据adoption-api-1；Runtime输入e54aa6c已核对581个Git blob及依赖摘要。远程宿主控制传输、实际存量租约迁移和生产上线仍未完成，不能单独打开收费开关。


### 远程宿主控制传输（2026-11-11，双端候选，生产未配置）

远程自行部署复用同一HostingControl和journal，仅增加运维配置的双向TLS入口；不是新增收费引擎、SSH业务调用或依赖Agent会话的控制入口。私有UDS继续使用原身份/权限合同；TLS在宿主进程持有，单Agent停止后仍可做证据确认及私有清理。应用消息保持protocolVersion=1及原scope/关系/代际，不让请求选择路径、地址或凭证。

Runtime hosting配置可选`remote`，完整字段为`listenHost`（IP字面量）、`port`（0..65535，0供测试）、`certificatePath/privateKeyPath/clientCaPath`（规范绝对普通文件）。TLS最低1.2、强制客户端证书校验；使用专用控制客户端CA，受该CA信任的客户端具有控制调用身份，后续仍按原scope和精确关系约束。证书/CA不能被组或其他用户写入，私钥不能被组或其他用户访问，属主只允许root或服务身份，且必须位于所有Agent可写根、host state、managedRoot之外。证书更新走受控宿主重启，无新轮询框架。省略remote保持本地行为。

两个传输共用16384字节请求帧上限。TLS配置/监听失败关闭已打开的UDS，不遗留半启动控制入口；正常关闭连同未完成TLS握手连接一起回收。本机临时证书的定向测试覆盖停止后继续控制、同journal重放、双向身份拒绝和凭证隔离；详见acceptance和Runtime `conf/cyf-agent-runtime-v1/HOSTING-CONTROL.md`。

API候选新增`HostingControlChannel`，复用Spring `SslBundles`读取客户端密钥与可信CA，不自行解析/存储另一份凭证。`agent.hosting-rent.control.local-host-id`明确原本地Runtime hostId；`remotes`按真实hostId索引`address/port/ssl-bundle/tenant-id/client-id/owner-jiacn`，`owner-jiacn="*"`仅是运维配置通配。TLS地址和端口只来自配置，不接受请求URL；客户端强制校验服务器DNS/IP SAN与TLS1.2以上，远程返回hostId必须匹配选中端点。控制请求和原协议解码共用，不改变账本或生命周期状态机。

路由优先使用已授权candidate.hostId；首次prepare用已持久化quote.inventoryHostId。没有这两种来源的库存/current/免费重整，单次按tenant/client/canonical Agent读取运行投影；已有投影缺hostId或host未配置时不回落本机。只有尚无运行投影的新托管主体走明确的本地host。这样重新邀请后投影暂时清空host字段也不会把远程实例误发本机；候选/报价已携带host时不额外查库，没有扫描或路由轮询。

已有静态实例的免费重整探测沿原已登记host发capabilities；它只需要该宿主管理现有实例，不要求提供新建模板。`template:null`返回的`available:false`继续表示不可新建，不再误拒绝已存在实例的管理。新建托管探测仍要求available=true，wire不增加兼容字段，后续关系/安装证明不放松。调度和业务服务使用同一个provider，remote不是第二套收费或重试逻辑。

本地只读核对hostId为`cyf-unified-065bb566a2d82210`，仍为UDS；李逵为`selfhost-li159-118-935f9597`，运行PID306359且尚无hostingControlPath。此为2026-11-11本轮观察，不代表已部署候选。最终安装须明确配置local-host-id及对应远程TLS端点，不能沿旧空配置发布后声称可用。双端固定源码测试结果见acceptance；生产证书/端口和实际李逵验收均未执行。

### 部署计价归属（2026-11-11，API 3fdfb9d724 / Web bf6d870，未发布）

- 复用同一租费应用服务、账本和调度；平台托管使用既有 `agent-hosting-preview` 套餐，自行部署使用 `agent-self-hosted` 套餐，默认50文/2592000秒。主机的计价类型由运维可信 `agent.hosting-rent.control.self-hosted-host-ids` 指定，不由HTTP的mode、网络地址或UDS/mTLS传输类型决定；远程主机也可属于平台托管。
- 初次报价在事务外取得真实库存和hostId，按可信主机类型冻结套餐、首次技能库存及周期价。确认时所选mode必须匹配冻结套餐；真实库存/host/部署类型变化只使尚未提交的报价失效，不预占、不创建关系。已经受理的资金操作仍按原key/报价重放，不因主机配置变化丢弃完成事实。
- 续租沿用原租约不可变planId，取该套餐当前明确版本及价格，不重新探测主机。为保留 plan→binding→lease 的加锁顺序，先按scope/lease主键做一次非锁定套餐发现，然后复用原业务锁及资金事务；无全表扫描、轮询或新增计费引擎。已有技能首费不进入周期租金。
- HTTP绑定入口两种mode统一委托收费应用服务，不再接受null/default/local直接创建免费关系；空值/缺少幂等键只拒绝该请求。原直接绑定Controller方法及其免费service依赖删除。租约只读投影新增原planId，资金记录和原操作hash不变。
- Web两种接应方式共用租约面板，确认请求使用冻结报价/租约planId；首次报价的实际部署类型和用户所选方式不一致时明确提示并禁止确认，不静默改收另一价格。旧版持久化免费重整操作没有planId时，保留其原来唯一的server请求语义，不清除未知操作或重换key；这只保留已提交事实，不新增免费入口。旧useHallData直接绑定不发请求，要求进入报价确认。
- cc72fe8362域服务/主机路由三个suite在`pricing-api-2`通过42项及layering（485.806秒），此前600秒超时保留FAIL。后继HTTP与Web候选的验证另见handoff；存量首次登记和最终发布仍未完成，不能仅凭控制/报价子链打开生产收费。
