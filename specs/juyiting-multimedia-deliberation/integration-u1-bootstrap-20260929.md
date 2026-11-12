# U1 悬赏议事 bootstrap 基础集成回执（2026-09-29）

**状态：特性分支研发源码已整合；非自动议事、非真实图片交付、非版本发布/产品验收。** 相对 [此前 U1 授权/step 基础](integration-u1-20260929.md) 的增量，业务合同继续遵循 [融合详设 v2](fusion-detailed-design-v2.md) 和 [桥接缺口](u1-bootstrap-bridge-notes-20260929.md)。

- API 特性分支 `codex/juyiting-multimedia-deliberation` exact commit `a6d2bf67065a86425bed4049377950967592aba4`、tree `94792737479f4f789f9d5314115a154360faef5a`，已推送并从远端 ref readback；整合 Agent assignment/grant/bootstrap outbox (`c29a0a11` + 负向测试修正 `a6d2bf67`) 与 Chat owner-scoped bounty binding (`3e69a255`)。根特性分支的 API gitlink 同步到此版本，Web/Client pin 不变。
- 独立 Agent exact tree `7bc07a50935590b3b09e13bf757ba04626eb13af` / `99894ce355ddb3533a8782c3b4f7fa8795167486` 定向 `:agent:jia-agent-service:mmdU1BootstrapOutbox`：19/19、0 failed/skipped；原始日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-outbox/targeted-02.log`。首轮 18/19 失败是负向测试给 0 触发参数校验而非 stale-fence，已保留失败证据 `targeted-01.log`，未把失败写成成功。
- 独立 Chat exact tree `414612780f057d40961e406e080f6b782da151b3` / `3528ccb1adfe19a3c3a46643b1b55bed57905077`：bounty binding 4/4，schema contract 3/3；首轮 JVM OOM 被内核杀死，改为单 worker + 512m heap 后通过；原始日志 `evidence/u1-chat/gradle-bounty-binding-1worker.log`、`gradle-bounty-schema-1worker.log`。
- **同一整合 API tree** 串行 orchestrator 跑 `:chat:jia-chat-service:chatDeliberation :agent:jia-agent-service:mmdU1BootstrapOutbox`：Chat 16 classes / 76 tests、Agent 4 classes / 19 tests，共 95，0 failures/errors/skips；原始日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-outbox/integrated-a6d2bf67.log`，evidence key `70655d241c695582293633868509e2064bdee2cecd69195fce6231c5646feb65`。本地定向验证只用于特性源码自检，不等于生产构建/发布。
- **缺口未消除**：`claimNext(scope)` 缺服务端待办 scope 发现/启动调度；Chat binding 不等于首条需求入库或 Agent 已接单；`/chat/stream` 旧 bounty 新建路径仍可能产生竞争；新表 MySQL8 空/旧库迁移与真实唯一性未测；`interactions`、真实授权执行、bytes-backed 媒体与验收仍待实现。按 [桥接缺口](u1-bootstrap-bridge-notes-20260929.md) 分包推进，任何单项通过不得称“可验收”。

## 本地隔离 MySQL 8 补验（同一 API exact tree）

在本任务已有、仅本线程持有的 Unix socket 私有 MySQL 8.0.21 内新建 `mmd_bootstrap_u1_20260929`，分别对 Chat 和 Agent outbox 新表的仓库原版 DDL 执行两次。11 个 CRUD/约束观察覆盖 binding 同 scope task 唯一、同 scope conversation 唯一、跨 owner 分离、非负 assignment、outbox 同 scope action 唯一、非法提前 ADMITTED 拒绝、CLAIMED→ADMITTED 有效转换。结果及 DDL SHA-256：`/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-outbox/mysql-integrated-a6d2bf67.json`。**未测旧库迁移、与旧 `/chat/stream` 并发、真实 service SQL 的事务隔离、生产 MySQL，故不得声称全局会话唯一或发布就绪。**

## 可信后台发现增量（仍未开启消费者）

API 特性分支随后整合 `bb395a8549cc9c20a6cbc07543180caa688d1c1a` / tree `ef010dd9450061d70a6b0497d219e417992c91fe`，远端同 SHA。Agent 内部 `claimNextAvailable(consumerId,now)` 从数据库行派生 owner/client，MySQL8 `FOR UPDATE SKIP LOCKED`、版本与租约 fence；**没有 HTTP 端点，也尚无后台 worker 或 Chat 自动投递。** 新装 v1 DDL 增加发现索引，既有 v1 表需显式执行 `agent-task-bounty-bootstrap-outbox-discovery-v2.sql` 一次；缺索引时初始化 fail closed。

- 独立 Agent exact tree `1b26cec82550c1937652d81819958efa82f9d6ae` / `fe3fa06c9ff0fb26870a44470bce89644cf31788` 定向 26/26、0 failed/skipped，日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-discovery/targeted-01.log`。
- 整合后同一 API exact tree 串行 orchestrator `chatDeliberation` 76/76 + `mmdU1BootstrapOutbox` 26/26，共 102，0 failed/skipped；日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-outbox/integrated-bb395a85.log`、evidence key `9ba296414adae5d99f67565322d176a715cfa7bcd9fc8e240d66ef2522197656`。单测中模拟的锁竞争不冒充数据库行为。
- 本线程隔离 MySQL 8.0.21 在私有新库对已装 v1 表执行一次原版显式 v2 索引迁移，按列顺序核对两个新索引，并开启两条独立事务证实 `SKIP LOCKED` 在锁住 owner-b 行时能读取 owner-c 行；证据 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-bootstrap-outbox/mysql-discovery-index-before.txt`、`mysql-discovery-index-after.txt`、`mysql-discovery-concurrency.json`。这里只证明 SQL 和事务锁行为，不证明 Java Spring 真实并发、旧业务历史升级或生产数据库变更。

**当前关键阻断项**：服务端权威不可变 `requirementRevision` 正文快照及精确 owner-scoped 读取未实现；不能把客户端自报 revision 或 `TaskPlan` 的已截断描述传给 Agent。Chat 受理/消费者、旧会话同任务唯一性、真实执行及媒体交付仍缺；此增量绝非可发布或可验收证明。

## 旧入口 bounty 同任务绑定增量（2026-09-29）

API 特性分支已快进推送 `e64623cdb3b58eaba120e9685c9a54300fcae0c5` / tree `6663a389b4d91fee5a75e602a31354370ca952e0`，远端 readback 同 SHA。旧 `/chat/stream` 对 `juyiting/bounty` 的创建与 v2 `ensure` 共享 `(tenant,client,owner,task)` binding 行锁；拒绝非法 task/scope/目标组合、多个历史候选及删除稳定 bounty 会话，不让旧 CHAT 路径获取新执行 grant。owner 在 exact tree 自检：`chatDeliberation` **82/82**，旧通用会话 guard **11/11**，0 failures/skips；原始日志 `evidence/u1-chat/legacy-unique-full-e64623cd.log`、`legacy-guard-e64623cd.log`。这仅证明源码切片的定向行为；旧新入口并发、历史数据/迁移的真实 MySQL8 验证仍待完成，不能宣称数据库层全局唯一或端到端已可用。权威不可变需求快照与后台消费尚在研发中；不得将 `ADMITTED` 或普通文本回复视为生成图片成功。

同一旧入口 API exact SHA/tree 的独立 MySQL 8.0.21 SQL 级并发补验：本线程独占私有 socket 上创建隔离库 `mmd_chat_legacy_binding_20260929`，安装仓库原版 Chat U1 DDL，两条事务竞争同 `(tenant,owner,client,task)` binding 行：第二条 reserve 等锁后读得同一 conversation（约 793ms 阻塞；两条连接仅产生 1 个 live bounty）；两个 owner 的同 task 各自独立；唯一历史候选收养、两个历史候选拒绝并回滚。见 `evidence/u1-chat/mysql-legacy-binding-e64623cd.json`（含 DDL SHA-256）。**这是 SQL/约束/行锁证据，不是 Spring `create/ensure` 并发集成、真实旧库迁移或全局唯一性结论。**

## 权威需求快照及自动议事入站源码（2026-09-29）

Agent Owner 在独立 `Agent/**` 工作树提交 `1dd01d2d`（append-only `agent_task_requirement_snapshot`，任务根事务创建/认证 owner 重确认；`read(scope,taskId,revision)` 原文与 SHA-256 精确回读；grant 的当前 revision 校验），首轮 45 项有 10 项失败：9 项旧 H2 夹具缺 `owner_jiacn`/旧 tenant，1 项 Mockito restub 提前执行旧 answer；原日志 `evidence/u1-requirement-snapshot-agent/gradle-mmdU1BootstrapOutbox-1dd01d2d-attempt1.log`。Owner 改变**仅测试夹具**后提交 `f7d24bc5` / tree `c2c170cd`，经 orchestrator 复测 Agent 7 classes / **45/45** 通过、0 failures/errors/skips，日志 `evidence/u1-requirement-snapshot-agent/gradle-mmdU1BootstrapOutbox-f7d24bc5-attempt2.log`。历史任务不自动伪造 revision；旧已出资任务的重确认入口及 Java service 真 MySQL 事务尚未验证。

Chat 主特性树新增 `ChatBountyBootstrapAdmissionService` 和**默认关闭**的后台 `ChatBountyBootstrapRelay`：可信 claim 精确取需求原文、复核 grant/会话，按业务动作原子入一条 USER 消息、同一 `chat_request`、step、无执行 ID 的 intent 及 durable 状态事件；重领复用原记录。首次入站**不会偷跑** fast CHAT 推理、执行命令或 Provider。独立 Chat `b7ade3d9` / tree `9f0d4e54` 经 orchestrator `chatDeliberation` 19 classes / **89/89**，日志 `evidence/u1-chat/gradle-bootstrap-initial-b7ade3d9.log`。

Agent 修复与 Chat 入站组合在 API 特性分支 `8470e549525fb9f0c52a73380800f827dec4cfc8` / tree `3ab92940ed35747563c0fd1a704b04af74873f65`，已推送并从远端 readback。**同一整合 exact tree** 经串行 orchestrator 跑 Chat **89/89** + Agent **45/45**，共 134，0 failures/errors/skips，日志 `evidence/u1-bootstrap-outbox/integrated-8470e549.log`、evidence key `a540ba8f21b07e5908a8fd5e9ebcac8af427f858dc5831b740edb7ba6238e1c5`。

私有隔离 MySQL 8.0.21 新库安装原版快照 DDL 两次并验证历史任务不回填、Unicode 全量回读、跨 owner 隔离、唯一键/十余负向 CHECK；精确 JSON（含 DDL SHA-256）在 `evidence/u1-requirement-snapshot-agent/mysql-requirement-snapshot-sql-8470e549.json`。**此项只是 SQL/约束/原文 hash 夹具，不是 Java Spring 真实 transaction 或存量生产库迁移。**

**当前残余**：worker 开关默认 off，尚未有 `/chat/conversations/{id}/interactions` 公共入口及澄清/受控 execution 后台消费者；`ADMITTED` 只表示初始请求/step 已持久入站，不能声称 Agent 已答复或图片已生成。 bytes-backed 会话媒体/预览下载、空间保存、最终交付/验收和真实浏览器仍未完成；绝非可发布或可通知用户验收。
