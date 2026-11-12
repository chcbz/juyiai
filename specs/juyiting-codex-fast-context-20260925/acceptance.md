# 聚义厅 Codex 快速议事与上下文一致性验收

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：议事上下文连续性与执行热路径。**

### 必须验证的业务结果
新会话不串历史、同会话多轮引用原文、重启续接、取消/失败正确结束、首字与完整回复分段测量。

### 不回归边界
不恢复每消息新进程/全历史重发、不每片查库/重验输入、不把相同thread ID当正文记忆证明；不新建第二聊天引擎。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

2026-09-25快速议事提案与阶段记录，不恢复旧codex exec/新引擎/全历史推送方案；当前原生会话和页级展示遵循现行合同。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



日期：2026-09-25
状态：Pending。以下是可观察验收合同，不代表当前已经通过。

## 1. 证据真实性

- [ ] 报告明确区分代码确认、历史观测、控制变量 A/B、工程估算和用户验收。
- [ ] 不再把“预计 4–8 秒”等估算写成已经达到的线上结果。
- [ ] 所有结论绑定 exact API/Web/Agent Runtime commit/tree、配置和 CLI 版本。

## 2. 路由与执行边界

- [ ] 普通问答进入 CHAT，不读取项目仓库、不写文件、不执行命令；如果候选引擎无法证明完全不暴露工具，产品、日志和验收均标记为 `read-only-constrained`，不宣称“无工具”。
- [ ] Fast CHAT 引擎选择有 direct model/Responses、受限 app-server、后端 ChatModel 的同夹具对比和明确取舍证据。
- [ ] tool catalog/readback 与负向 prompt 证明 CHAT 不能 shell、读 cwd 外文件、联网、写文件、调用 MCP/plugin/skill/dynamic tool 或申请权限。
- [ ] `approvalPolicy=never` 未被当作 deny-all；即使动作不触发审批，CHAT/INSPECT 仍由 tool catalog 与 OS sandbox 实际阻断越界。
- [ ] 任务状态问题使用后端注入的权威状态，不通过仓库猜测。
- [ ] 查看授权代码/日志/附件进入 INSPECT，结果包含精确 source ref/tree SHA。
- [ ] 用户在聊天中说“执行、修改、部署、继续”不会直接产生 command。
- [ ] 只有现有正式 execution/work item/command.dispatch 事实进入 EXECUTE。
- [ ] 已有执行运行中时，“继续”不会产生第二个执行。
- [ ] 默认 CHAT/显式 input refs INSPECT 不串行调用额外 LLM 分类器；若启用模型 proposal，其失败/超时回到确定性规则且单独报告时延成本。

## 3. Context Snapshot

- [ ] 每轮 dispatch 有 `contextSnapshotId/contextHash/sourceVector`。
- [ ] canonical JSON/hash 在 API 与 Agent golden fixture 完全一致；模型上下文预算来自实际 capability，裁剪项和原因可审计。
- [ ] Web/低信任日志不暴露可枚举的敏感事实裸 hash；使用版本化 HMAC 或 opaque ID，digest 不被当作授权凭证且 key 轮换可演练。
- [ ] Snapshot Builder 无按消息/参与者/附件 N+1；任何缓存以 source vector 为键并在 ACL/generation/revision 变化时失效。
- [ ] Agent final echo 完全相同的 snapshot ID/hash；不匹配回复不写入其他会话。
- [ ] 新 thread、Agent 重启、页面刷新、SSE 重连后可从业务 DB 恢复上下文。
- [ ] selected Agent、task、participant、input ref 均由后端重新校验，前端伪造不能扩大范围。
- [ ] conversation 删除/generation 变化后，迟到回复不能重新写入。
- [ ] 工作目录变化创建新 thread generation，但业务摘要、决定和任务状态不丢失。
- [ ] 摘要错误/缺失时系统明确降级，不把不完整上下文伪装为完整。
- [ ] 多 Agent 群聊为每个目标 Agent 生成独立 dispatch/snapshot/turn/thread；回复含 targetAgentId/replyToMessageId，其他 Agent 私有检查或执行结果不会隐式共享。
- [ ] 一个群聊发送只有一条共享 user message 和一个父 request；每个目标 Agent 有独立子 turn，父状态正确表示 partial/completed/failed/cancelled。
- [ ] 最终事件的 routeUsed/toolUseObserved/inspectedRefs/grounding 由 Runtime 根据真实事件生成，模型正文不能伪造。

## 4. 身份、ACL 与隐私

- [ ] owner/client/tenant 交叉测试均 fail closed，响应不泄露资源存在性。
- [ ] INSPECT 阻止任意绝对路径、`..`、软链逃逸、未声明文件和变更后的版本。
- [ ] `cwd`/manifest 不被当作安全边界；文件/命令工具存在时，低权限 OS/external sandbox 证明子进程看不到宿主其他工作区、CODEX_HOME、secrets 或网络。
- [ ] CHAT/INSPECT 均不能访问执行工作树之外的未授权内容。
- [ ] 日志和指标不记录正文、Cookie、token、API Key、文件内容或私有路径。
- [ ] 不同 Profile 使用独立 CODEX_HOME，后台 thread 不映射到其他 Profile。
- [ ] CHAT 只加载发布制品托管指令；仓库 AGENTS.md 记录 exact SHA 且不能扩大权限；用户附件/日志/代码即使使用保留文件名也不会被提升为系统/开发者指令。
- [ ] CODEX_HOME/auth/config/session 的 owner/mode、进程身份和 env allowlist 通过 readback；token 轮换/撤销/账户切换使旧 binding 失效。
- [ ] app-server 仅使用本地 stdio，或另有已验收的认证/TLS/peer identity 设计；不存在未认证监听端口。
- [ ] conversation/用户数据删除或授权撤销先阻止 resume，再 archive/delete 缓存；失败状态可重试且不能继续使用旧 thread。

## 5. 幂等、并发与恢复

- [ ] 同一 request/turn 重放不会重复保存 user message 或 final reply。
- [ ] `Idempotency-Key`、body requestId、requestRevision 语义一致；旧 Web 无 requestId 时服务端生成并回传。
- [ ] user message + turn + outbox 同事务；final + FINAL_PERSISTED 同事务；DB 成功而 WS/SSE 失败只重投事件，不重新调用模型。
- [ ] delta 按 `turnId + deltaSeq` 去重；乱序/跳号不会拼接错误文本。
- [ ] SSE 重连不自动重发用户请求。
- [ ] Web 以 eventId/Last-Event-ID 或 cursor 恢复关键状态/final；过期 cursor 不拼接残缺 delta。
- [ ] command durable inbox、ledger、STARTED ACK、terminal/recovery_required 行为保持。
- [ ] CHAT 失败或 app-server 崩溃可安全回退旧路径，不重复 EXECUTE。
- [ ] 一重执行期间轻量 CHAT 可排队或并行；性能慢不会取消已受理工作。
- [ ] accepted CHAT 存在 durable turn/outbox；Runtime/API 重启不丢请求、不重复写 user message，公平队列不会让单一群聊长期占满 Profile。
- [ ] `turn/start` 请求结果未知时进入明确 unknown/recovery 状态并先对账，不盲目重放；EXECUTE 不使用 CHAT 的重新生成策略。
- [ ] capability、request/turn 查询、单 turn cancel、群聊 pending cancel 端点均执行 owner/client/tenant/generation 校验和幂等语义。
- [ ] final 已生成但 DB 失败时按 digest 幂等保存；final 已保存但 SSE 失败时由 DB 重放，不重新生成。

## 6. 真实 streaming

- [ ] 新路径首个可见字符来自真实 engine delta，不是 final 后人工切片。
- [ ] final 只持久化一次并替换前端临时流式消息。
- [ ] 无 delta 的兼容 Agent 仍能以 final 完成，不伪造“正在输出”文本。
- [ ] 流式 delta 与 final 使用相同安全渲染，模型 HTML/Markdown、文件名和链接不能执行脚本、危险 scheme 或暴露未授权本地路径。
- [ ] reasoning、tool stdout/stderr、审批详情和内部 trace 不被当作用户聊天 delta/final 发布。
- [ ] 超大 final 不被静默截断；若使用 `truncated/fullContentRef`，UI 明示且全文引用继续执行 ACL。
- [ ] 取消仅响应用户取消、身份切换或真实传输/协议边界，不因性能目标自动中断。
- [ ] 页面/SSE 断开默认不取消已受理 CHAT；用户取消只停止对应推理并保留 user message/cancel 状态，不影响正式 COMMAND。
- [ ] 群聊取消可定向单个子 turn 或所有 pending turn；已完成回复不回滚，未选中的 Agent 不被取消。
- [ ] app-server 发起 command/file/permission/network/MCP/dynamic-tool 请求时 CHAT 明确拒绝并中断；user-input 请求仅转为澄清，不能成为执行确认。

## 7. 工作目录与快照

- [ ] CHAT 使用专用小 workdir，无项目源码；effective `.codex`/skills/plugins/MCP/instruction sources 均有 hash/readback，工具能力与选型结论一致。
- [ ] INSPECT manifest 的每个文件均有固定版本/hash；结果可追溯。
- [ ] EXECUTE 继续使用任务隔离 worktree、锁、exact SHA 和输出 manifest。
- [ ] thread 不跨 mode/workspaceScopeHash/cwd 复用。
- [ ] thread key 同时包含 tenant/client/owner、Profile、Agent、conversation、mode、workspace、engine/tool/instruction/model policy 和 generation；任一安全相关维度变化均不复用旧 thread。

## 8. 性能和资源证据

以下是观测要求，不是未经测算的发布硬门槛：

- [ ] A/B 同输入、同模型、同 Agent、同资源窗口报告 TTFT、first-visible、final 分布。
- [ ] 报告样本量、异常值、置信区间、fallback 比例和质量结果。
- [ ] 关键身份/ACL/执行声称/状态/来源使用确定性断言；persona 与帮助度采用盲评/成对比较，严重安全错误不被平均质量分抵消。
- [ ] 分别报告 app-server 单项、Fast CHAT 单项和组合效果。
- [ ] 报告每 Profile app-server RSS/CPU/Swap/FD/磁盘增量。
- [ ] 性能未达估算时记录优化待办，不通过取消、拒绝或快速失败美化结果。
- [ ] 报告 route/profile/model/reasoning/service tier 的 token、调用、重试、rate-limit、额度和成本；fallback 不静默切到成本显著更高或权限更宽的路径。

## 9. Thread 生命周期

- [ ] 业务数据库是唯一会话事实源；删除 Codex 缓存后仍可重建新 thread。
- [ ] unsubscribe/archive/compact 不删除业务消息和正式执行事实。
- [ ] delete 仅针对无活跃引用、已形成可靠快照/摘要并通过 dry-run/readback 的缓存。
- [ ] 不使用宽泛年龄规则清理其他任务、其他 Profile 或未知状态文件。
- [ ] unsubscribe 仅被视为取消当前连接订阅；是否卸载/释放内存由实际 thread 状态和资源 readback 证明。
- [ ] 摘要记录生成器版本、输入 message range/source vector；用户纠正使用 supersession，摘要不能覆盖权威业务事实。

## 10. 兼容与回退

- [ ] 旧 Web 不发送新字段时仍可聊天。
- [ ] 新 Web 在 capability 端点不可用时降级旧 payload，不乐观发送 v2；网络未知时用 request/turn 查询恢复。
- [ ] 旧 Agent 不声明 capability 时 API 使用旧 payload/路径。
- [ ] 可分别关闭 true delta、app-server、Fast CHAT、INSPECT flag。
- [ ] 性能功能回退不撤销 Context Snapshot 的身份/权限校验和 EXECUTE 授权边界。
- [ ] API old/new × Agent old/new × Web old/new 全矩阵通过；新 Web 仅在服务端 capability 支持时发送新字段。
- [ ] 群聊中部分 Agent 升级时逐 Agent 协商，旧 Agent 不收到不兼容 payload，新 Agent 不替其他 Agent 共享 thread。

## 11. app-server 版本、服务端请求与失败注入

- [ ] 证据包含 Codex binary 版本/SHA、生成 schema digest、initialize capability、model/list、config/tool catalog 和事件方法集合。
- [ ] 无效 model/reasoning/sandbox/config 整份拒绝并保留上一有效配置；不发生半加载。
- [ ] command/file-change/permission/MCP/dynamic-tool/user-input 等 server request 均有模式化处理、关联 ID、超时和默认拒绝测试。
- [ ] 注入并验证：API DB 已提交但 WS 发送失败、Agent ACK 丢失、turn 应答丢失、delta 后 app-server 崩溃、final DB 失败、SSE 发布失败、mapping 损坏、quota/rate-limit、缓存删除失败。
- [ ] 每个失败点都能查询到真实状态和一个安全恢复动作，不伪报完成、不重复 EXECUTE。

## 12. 数据保留与可验证回答

- [ ] Context Snapshot、chat message、summary、Codex session/log 的保留和删除关系有配置/readback，缓存不保存业务库之外的唯一事实。
- [ ] 用户数据导出以业务 DB 为准；日志、指标和删除审计不包含正文或 secrets。
- [ ] CHAT 状态回答绑定 sourceVector/fact ref；INSPECT 结论绑定 manifest ref/hash/tree SHA；来源缺失或冲突时明确说明而不猜测。

## 13. 验证证据待填写

- API revision/tree：
- Web revision/tree：
- Agent Runtime revision/tree：
- Root integration revision：
- CLI/app-server version：
- App-server schema digest/capability/tool catalog：
- Selected Fast CHAT engine and policy：
- API tests：
- Web tests：
- Agent runtime tests：
- Controlled A/B report：
- Usage/cost/rate-limit report：
- Mixed-version/failure-injection report：
- Retention/deletion readback：
- Artifact SHA-256：
- Deployment/run evidence：
- Online verification：
- Known residual risks：
