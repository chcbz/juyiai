# 聚义厅 Codex 快速议事与上下文一致性实施任务

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：议事上下文连续性与执行热路径。**

**实施目标：** 持久请求→复用适用原生thread→增量流预览→完整最终回复事务→事件更新页面。
**责任落点：** API请求/回合/完成事实；bridge原生会话映射和执行隔离；Web流预览/最终展示。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不恢复每消息新进程/全历史重发、不每片查库/重验输入、不把相同thread ID当正文记忆证明；不新建第二聊天引擎。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：新会话不串历史、同会话多轮引用原文、重启续接、取消/失败正确结束、首字与完整回复分段测量。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

2026-09-25快速议事提案与阶段记录，不恢复旧codex exec/新引擎/全历史推送方案；当前原生会话和页级展示遵循现行合同。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



日期：2026-09-25
状态：Ready backlog；可分配 Owner 并进入开发与测试，当前尚未进入 `TASKS.yaml` 运行台账。
原则：不创建独立 Reviewer；每个实现 Owner 对其身份、ACL、事务、幂等、并发和恢复边界自检。

## 0. 依赖关系

```text
T00 合同/基线
 ├─ T05 Fast CHAT 引擎/工具暴露 spike
 ├─ T10 API Router
 ├─ T11 API Context Snapshot/durable turn
 ├─ T12 Agent Context Envelope
 ├─ T13 Web request/vector
 └─ T14 correctness + T15 unknown/cancel
       ↓
T20 Fast CHAT（依赖 T05） ── T21 Lane separation
       ↓              ↓
T30 INSPECT exact snapshot
       ↓
T40 app-server turns ── T41 true delta
       ↓
T50 summary/thread lifecycle
       ↓
T60 one-profile pilot → T61 three-profile rollout
```

T10/T11/T12/T13 可在契约冻结后按非重叠路径并行。T20 必须等待 T05 给出可证据化引擎结论；T40 不得先于 T10/T11/T12/T15；T41 不得先于 turn/final 归属和幂等合同通过。

## 1. Phase 0：合同、可观测与基线

### T00 — 冻结协议与证据分级（Root Owner，L0）

- [ ] 冻结本 SDD 的 request/event/context schema v1。
- [ ] 明确现有 Hall Draft/Personal Workspace execution/command.dispatch 中哪个事实是 EXECUTE 唯一授权入口。
- [ ] 记录当前 API/Web/Agent Runtime/Root SHA、tree、CLI 版本、配置和 Profile capability。
- [ ] 将“代码确认、历史观测、官方能力、工程估算”分开写入基线报告。

产出：冻结设计补充、baseline manifest。

### T01 — API/WS/SSE 时间戳（API Owner，约 1 owner-day）

建议路径：

- `api/chat/jia-chat-service/.../ChatController.java`
- `api/chat/jia-chat-service/.../JuyitingAgentRelayService.java`
- `api/chat/jia-chat-service/.../AgentWebSocketHandler.java`

- [ ] 增加 request/turn 关联 ID 和阶段时间戳。
- [ ] 指标标签限制为 route/mode/profile/outcome。
- [ ] 日志不记录正文、token、Cookie、文件内容或高基数业务 ID 标签。
- [ ] 慢请求仅记录，不设置性能取消。

### T02 — Agent Runtime 时间戳和资源采样（Agent Runtime Owner，约 1 owner-day）

- [ ] 记录 receive、queue、engine start、first event、final、publish 时间。
- [ ] 采样每 Profile/engine RSS、CPU、FD、session/log 磁盘。
- [ ] 标记 `routeUsed/fallbackReason/threadGeneration`。
- [ ] 不记录完整 prompt 或私有绝对路径。

### T03 — Web 首可见时间（Web Owner，约 0.5–1 owner-day）

- [ ] 记录发送、首状态、首 delta、final render。
- [ ] 身份切换和会话切换取消旧页面更新，不取消已受理后台工作。
- [ ] 不上报正文和敏感 ID。

### T04 — 可重复基线夹具（GPT test runner/责任 Owner）

- [ ] 固定普通问答、任务状态、连续指代、长历史、工作目录变化、执行中查询、文件检查七类用例。
- [ ] 保存输入事实和期望事实，不保存生产私密正文。
- [ ] 采集现有 A 组分布和宿主资源窗口。

### T05 — Fast CHAT 引擎与工具暴露 spike（Agent Runtime + API Owner，约 2–4 owner-day）

- [ ] 对比直接轻量模型/Responses、受限 Codex app-server、现有后端 ChatModel 三类候选。
- [ ] 锁定本机及候选部署 Codex CLI 版本，保存 `generate-json-schema` digest、`model/list`、config/capability readback。
- [ ] 验证模型侧实际 tool catalog、built-in shell/file read、web、MCP、plugin、skill、dynamic tool 和 server request 行为。
- [ ] 负向 prompt 尝试命令、读取 CHAT cwd 外文件、联网、写文件、申请权限和调用工具；记录真实事件，不只检查配置名。
- [ ] 证明 `approvalPolicy=never` 未被误当 deny-all；策略内工具即使不触发审批也必须受 tool catalog/OS sandbox 限制。
- [ ] 验证 persona、Context Envelope、群聊隔离、delta、取消、usage、rate-limit 和成本可观测性。
- [ ] 记录候选引擎认证方式、供应商数据处理/保留配置、区域和费用归属，不推导未授权外部付费调用。
- [ ] 给出 `verified-none` 或 `read-only-constrained` 结论；未通过 strict no-tools 证明不得使用“无工具”名称。
- [ ] 失败候选不回退到权限更宽或成本显著更高的路径；输出选择依据和剩余风险。

## 2. Phase 1：权威路由与 Context Snapshot

### T10 — Interaction Router（API Owner，约 1–2 owner-day）

- [ ] 新增 `CHAT/CHAT_STATUS/INSPECT/EXECUTE` 内部枚举和决策顺序。
- [ ] `/chat/stream` 只接受 `interactionHint=chat|inspect`，不接受 execute 授权。
- [ ] EXECUTE 仅从现有持久 execution/command path 进入。
- [ ] 正在运行的执行收到“继续”时返回状态/补充说明，不产生重复 command。
- [ ] capability 不支持时安全回退旧 chat 路径。
- [ ] 默认 CHAT/显式 refs INSPECT 采用确定性规则；不得为每条消息串行增加 LLM 分类调用，模型 proposal 失败回到规则结果。

### T11 — Context Snapshot Builder（API Owner，约 3–4 owner-day）

- [ ] 以 owner/client/tenant + conversation generation 锁定会话。
- [ ] 用户消息提交后取得 message high-watermark。
- [ ] 聚合可信 task、execution、binding、participant、input refs。
- [ ] 生成 canonical source vector、facts manifest、context hash。
- [ ] 固定 canonical JSON 规则并建立 API/Agent golden hash fixture。
- [ ] 跨较低信任边界的 digest 使用版本化 HMAC 或仅暴露 opaque snapshotId；hash/HMAC 不参与 ACL，支持 key 轮换双读单写。
- [ ] 从实际模型 capability 推导输入预算，记录 included/omitted refs 与裁剪原因；超大附件转 INSPECT/摘要，不在 Agent 端静默裁剪。
- [ ] 保存最小快照记录；不重复存文件正文和凭证。
- [ ] 建立 durable chat turn/outbox：requestId、dispatchId、targetAgentId、snapshot、状态与重试归属可查询。
- [ ] 建立父 Chat Request + 每目标 Agent 子 Chat Turn/dispatch；群聊独立 snapshot，其他 Agent 私有 INSPECT/执行结果不自动共享。
- [ ] 父 request 聚合 partial/completed/failed/cancelled，不因首个 final 提前结束，也不因单 Agent 失败回滚其他回复。
- [ ] final 写入时校验 generation 和 snapshot 归属。
- [ ] user message + turn + outbox 同事务，final + FINAL_PERSISTED 同事务；事件发布使用 transactional outbox 或等价机制。
- [ ] 补 schema migration、唯一键/索引、事务隔离、CAS、跨模块 revision 复核、并发和删除 fence 测试；如可复用现有表则记录无需 DDL 的依据。
- [ ] 聚合查询避免 N+1；缓存以 source vector 为键并在 ACL/generation/revision 变化时失效。

### T12 — Agent Context Envelope（Agent Runtime Owner，约 1–2 owner-day）

建议源路径：

- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/agent-client.mjs`

- [ ] 新增严格 schema 验证与大小边界。
- [ ] `buildContextEnvelope()` 替代“仅 current content 作为完整 prompt”。
- [ ] prompt 明确 authoritative facts、missing facts、禁止工具声称和当前模式。
- [ ] 指令来源分级并记录 `instructionSourceVector`；用户附件/日志/代码永远作为数据，不能因文件名被自动提升为指令。
- [ ] Runtime 根据真实事件生成 grounding/tool-use/source refs，禁止模型正文伪造“已检查/已执行”。
- [ ] Agent 回报 echo snapshot ID/hash。
- [ ] schema v1 旧消息保持兼容。

### T13 — Web Context Hints（Web Owner，约 1 owner-day）

建议路径：

- `web/src/composables/juyiting/useHallConversation.js`
- `web/src/composables/juyiting/hallConversationMessages.js`

- [ ] 发送 `interactionHint/clientSeenVector/requestRevision/inputRefs`。
- [ ] 生成并复用稳定 requestId；仅在 API capability 支持时发送新字段。
- [ ] 使用 `Idempotency-Key`；header/body requestId 一致，未知结果查询 request/turn，不生成新 ID 重发。
- [ ] 不上传完整 `messages[]` 作为权威事实。
- [ ] 页面刷新后从服务端重新建立 vector。
- [ ] 网络结果未知时查询原 conversation/turn，不自动重复发送。

### T14 — Context correctness fixture（API/Web/Agent Runtime Owners）

- [ ] 新 thread 恢复。
- [ ] app/Agent 重启恢复。
- [ ] 页面刷新与 SSE 重连。
- [ ] selected task/Agent 切换。
- [ ] 跨 owner/client/tenant、伪造 task/participant/input ref。
- [ ] conversation 删除 generation fence。
- [ ] Long ID 字符串传输。
- [ ] 多 Agent 同 conversation 独立 thread/snapshot、回复归属、提交顺序和不可见私有结果。
- [ ] repository `AGENTS.md` 与恶意附件同名指令文件的信任边界。

### T15 — Turn 状态、未知受理与取消（API + Agent Runtime Owner，约 2–3 owner-day）

- [ ] 实现 capabilities、request/turn 查询、单 turn 取消和群聊 pending 取消端点，复用非泄露 scope 校验。
- [ ] 实现从 `RECEIVED` 到 `PUBLISHED` 的持久 chat turn 状态及 unknown/recovery/cancel 分支。
- [ ] 稳定映射 requestId/dispatchId/clientUserMessageId/threadId/turnId/final digest。
- [ ] 区分未发送、Agent ACK 丢失、`turn/start` 应答丢失、final 持久化失败、SSE 发布失败。
- [ ] 未知受理先 journal/readback，对账失败不得盲目重放；EXECUTE 绝不复用 CHAT 推理重试规则。
- [ ] 用户取消、身份切换、页面断开和传输失败分别测试；页面断开默认继续并持久化 final。
- [ ] 群聊取消可精确指定子 turn 或 allPending；已完成子 turn 不回滚，未指定不误伤其他 Agent。

## 3. Phase 2：Fast CHAT 与 lane

### T20 — Fast CHAT profile（Agent Runtime Owner，约 2–3 owner-day）

- [ ] 仅实现 T05 选中的引擎，增加 chatEngine/chatModel/chatReasoningEffort/chatSandbox/chatToolPolicy/chatWorkdir 配置。
- [ ] Profile 热加载采用整份有效配置，错误配置保留旧值。
- [ ] `runFastChat()` 达到 `verified-none`，或被明确标为 `read-only-constrained`；不得将 sandbox 等同于禁用全部工具。
- [ ] 若候选仍有文件/命令能力，使用低权限 OS/external sandbox 只暴露 CHAT 小目录；仅有 cwd/read-only 不通过门禁。
- [ ] CHAT 小目录不继承未审计的 `.codex`、skills、plugins、MCP；有效指令与配置 hash 纳入 thread key/readback。
- [ ] Context 不足时明确请求 INSPECT/更多信息，不能猜测。
- [ ] 保留 full Codex fallback 并记录原因。

### T21 — Lane 分离与资源调度（Agent Runtime Owner，约 2–3 owner-day）

- [ ] 拆分 `chatLane/inspectLane/commandLane`。
- [ ] command durable inbox/ledger/ACK/recovery 语义保持不变。
- [ ] 一重执行期间允许轻量 CHAT，但不无限并发。
- [ ] 同一 conversation/Agent 单 turn，后续消息排队或用户显式取消。
- [ ] 按 tenant/client/owner/Agent/conversation 做公平排队；具体权重和并发由试点证据推导。
- [ ] 已 accepted 的 CHAT 有持久 outbox，不因队列上限、重启或慢请求静默丢弃。
- [ ] 性能慢不触发取消；真实网络超时、用户取消和身份切换取消保持。
- [ ] 区分 handshake/WS/SSE/RPC 传输超时与模型生成耗时；只有真实传输/配置超时触发相应失败。

### T22 — Fast CHAT UI 状态（Web Owner，约 0.5–1 owner-day）

- [ ] 展示排队、理解上下文、生成中、回退旧路径等真实状态。
- [ ] 群聊逐 Agent 展示子 turn 状态和父 request 部分完成，不以第一个 final 结束整次发送。
- [ ] 写入意图展示办理建议/确认入口，不显示“已经执行”。

### T23 — 单 Profile A/B（Integration Owner）

- [ ] 选择低业务风险且有代表性流量的一个 Profile，不按角色名称先验指定。
- [ ] A/B 比较 TTFT、first-visible、final、质量、RSS/CPU/Swap。
- [ ] 关键事实用确定性断言；persona/帮助度用盲评或成对比较，严重越权/虚假执行声称不能被平均分抵消。
- [ ] 记录置信区间和异常归因，不只报告最好值。
- [ ] 不因性能不达估算值取消可用请求。

## 4. Phase 3：INSPECT

### T30 — Read-only manifest service（API/Agent Owners，约 3–4 owner-day）

- [ ] owner-safe 文件/附件版本固定和 manifest。
- [ ] exact Git tree SHA snapshot。
- [ ] 路径规范化、软链、防穿越和允许路径校验。
- [ ] snapshot 变化/失效有明确错误，不扩大扫描。
- [ ] 区分平台指令、仓库指令和用户资料；附件使用非保留名物化，仓库指令记录 exact SHA 且不能扩大权限。

### T31 — `runReadOnlyInspection()`（Agent Runtime Owner，约 1–2 owner-day）

- [ ] read-only sandbox 和 snapshot cwd。
- [ ] cwd/manifest 之外再使用低权限 OS 进程或外部 filesystem sandbox，只挂载声明文件并关闭网络；无法证明隔离则不启用 INSPECT。
- [ ] thread key 包含 workspaceScopeHash。
- [ ] 输出携带 source refs/tree SHA。
- [ ] 真实事件生成 `toolUseObserved/inspectedRefs`；模型文字不能伪造来源。
- [ ] 禁止 build/deploy/write，即使用户文本要求执行。

### T32 — INSPECT UX（Web Owner，约 0.5–1 owner-day）

- [ ] 显示正在检查的授权来源和版本。
- [ ] 缺少授权引用时提示选择资料/工作区。
- [ ] 结果显示基于哪个 SHA/文件版本。
- [ ] delta/final/引用/文件名统一安全渲染，阻止 script、事件属性、危险 URL scheme 和未授权本地路径链接。

## 5. Phase 4：app-server 与 true streaming

### T40 — App-server adapter（Agent Runtime Owner，约 3–5 owner-day）

建议源路径：

- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/managed-host.mjs`
- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/agent-client.mjs`

- [ ] 进程监管、initialize/account/capability。
- [ ] thread start/resume 与精确本地 binding。
- [ ] `turn/start`、interrupt、unsubscribe、进程退出恢复。
- [ ] 处理 command/file-change/permission/MCP/dynamic-tool/user-input 等 server-initiated request；未知请求默认拒绝，CHAT/INSPECT 不静默批准。
- [ ] `turn/start` 接受未知时用 thread/turn/journal/clientUserMessageId 对账，不盲重放。
- [ ] 明确 unsubscribe 只取消当前连接订阅，不能把它当立即释放 thread 内存的证据。
- [ ] thread 不跨 Profile Home、mode、conversation、workspace。
- [ ] 失败回退不触碰 command durable state。

### T41 — Delta protocol（API + Agent + Web Owners，约 2–3 owner-day）

- [ ] `turnId/deltaSeq/contextSnapshotId/hash`。
- [ ] Agent payload/event 贯穿 requestId/turnId/dispatchId/targetAgentId；API 校验精确归属。
- [ ] 删除新路径的 72 字符伪切片。
- [ ] 只转发 Agent message delta/final；reasoning、tool stdout/stderr、审批详情和内部 trace 不进入用户聊天或业务日志。
- [ ] delta 去重/跳号处理，final 单次持久化。
- [ ] 服务端事件包含 eventId/eventVersion/occurredAt；关键状态/final 持久化，delta 可不持久化。
- [ ] SSE 用 Last-Event-ID/cursor 恢复；cursor 过旧返回当前状态/final，不自动重发用户请求。
- [ ] 旧 Agent/旧 Web 兼容。
- [ ] 删除/替代静默 `trimReply`：超大 final 使用显式 truncated/fullContentRef 或受 ACL 的正文对象，容量值按实测推导。

### T42 — App-server 单 Profile 容量试点

- [ ] 记录冷/热 thread、一个 CHAT、CHAT+EXECUTE 时 RSS/CPU/Swap/I/O。
- [ ] 进程崩溃、CLI 升级、协议不兼容和 WS 断连演练。
- [ ] 认证失效、token 轮换、rate-limit/额度不足、服务端请求 handler 崩溃演练。
- [ ] 有实际证据后决定是否扩展到三个 Profile。

### T43 — CODEX_HOME 与 secret 生命周期（Agent Runtime/运维 Owner，约 1–2 owner-day）

- [ ] 每 Profile service identity、目录/文件权限、env allowlist 和 stdio 边界 readback。
- [ ] auth token 轮换、撤销、账户切换、Profile 解绑使旧 binding generation 失效。
- [ ] snapshots/logs/metrics 不含 token、Cookie、API Key、云凭证和私有绝对路径。
- [ ] 若未来使用 socket/远程 app-server，另立认证/TLS/peer identity 设计；本任务不开放未认证监听端口。

## 6. Phase 5：摘要与生命周期

### T50 — Structured summary/decision ledger（API Owner，约 2–3 owner-day）

- [ ] 摘要关联 message high-watermark 和 summary revision。
- [ ] 决定、约束、未决问题结构化，不只保留自由文本。
- [ ] 摘要更新不能覆盖身份、ACL、任务和执行权威事实。
- [ ] 摘要失败时仍可用近期原始消息恢复。
- [ ] 记录生成器版本、输入 message range/source vector；失败不覆盖旧摘要，更新采用 revision/CAS。
- [ ] 用户纠正和决定变更使用 append-only correction/supersession，不原地改写历史。

### T51 — Thread rolling/compact/archive（Agent Runtime Owner，约 1–2 owner-day）

- [ ] 依据实际 token/latency/resource 观测触发，不预设无依据硬阈值。
- [ ] 滚动前保存 summary/source vector/readback。
- [ ] 业务会话关闭后 unsubscribe/archive。
- [ ] delete 仅处理无引用、可重建缓存，并有 dry-run/readback。
- [ ] conversation/用户数据删除、身份解绑先写 tombstone 禁止 resume，再异步 archive/delete；失败可重试且不泄露正文。

### T52 — 三 Profile rollout（Integration Owner，约 2–4 owner-day）

- [ ] 逐 Profile 开 flag，记录每一步资源增量。
- [ ] 验证身份隔离、CODEX_HOME 隔离和 thread list。
- [ ] 达到宿主资源压力时保持排队/旧路径，不盲目增加并发。

## 7. 验证与发布任务

### T60 — 静态和组件验证

- [ ] API：router、snapshot transaction、ACL、generation fence、事件幂等。
- [ ] Web：请求字段、delta reducer、Last-Event-ID/cursor、身份切换、未知请求恢复、安全渲染。
- [ ] Agent：schema、thread key、lane、fallback、app-server fixture。
- [ ] 所有 Gradle 调用经 `python3 ops/orchestration/cyf_orchestrator.py gradle ...`。

### T61 — 集成验证

- [ ] exact API/Web/Agent Runtime commits/trees。
- [ ] 同版本协议 capability readback。
- [ ] mixed-version 矩阵：API old/new × Agent old/new × Web old/new，以及群聊中部分 Agent 升级。
- [ ] app-server schema digest、model/config/tool catalog、instruction source 与 CODEX_HOME 权限 readback。
- [ ] A/B 报告和正确性矩阵。
- [ ] command 重复执行为零的夹具证据。
- [ ] 资源、磁盘和进程归属 readback。
- [ ] failure matrix 注入：WS send、ACK、turn response、app-server crash、DB final、SSE publish、binding corruption、quota、delete failure。
- [ ] usage/cost/rate-limit 报告；fallback 不发生未授权高价或高权限跃迁。

### T62 — 发布与回退

- [ ] 依据实施时有效的 Flow 或本地用户授权政策。
- [ ] 先 API 兼容字段，再 Agent capability，再 Web UI，按 flag 开启。
- [ ] Web 发送新字段前读取 API capability；每个目标 Agent 独立协商 payload 版本。
- [ ] 每阶段保留关闭 flag 和旧路径回退。
- [ ] 发布记录测试、制品 SHA-256、部署顺序、健康和线上低风险只读核验。
