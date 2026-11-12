# 统一议事与受控执行详细设计 v2

> **2026-10-03 最新实施指令**：用户明确“无需做太多兼容补丁，一切都按新方案实施”。新入口、新请求统一走通用资料与按需议事；不新增旧生图入口、双轨产品流程或回退适配工程。只保留身份隔离、幂等、未完成请求及既有内容保护，不以历史兼容覆盖率阻塞新方案。

> **2026-10-03 用户纠偏（当前优先）**：[通用资料详设增量v3](unified-materials-correction-20261003.md)取代独立参考图入口及图片限定业务流程。唯一“添加资料（可选）”须支持图片/文档/音频等；Agent判断用途，通用会话、输出、保存与交付保持完整范围。不是文案改名；绘图专用wire仅作为执行适配，不扩展旧产品入口，原34项需补UM01–UM10。当前已完成创建/资料基础源码自检，通用点将会话链路与整体验收仍待完成。

日期：2026-09-28。状态：**长期目标合同；基础设施已部分实现，业务闭环尚未实现**。本文件为长期融合决策的详设，对 v1 `design.md` 中“必须先 CHAT 再执行”等不明确之处进行优先澄清。v1 的多媒体 UI、私有存储、归档及验收要求继续有效。具体数据库 DDL/DTO 映射须在 U1 实施前冻结，不能把本文件的新增接口当线上可用接口。


**实施前现有表/端点映射**：参见 [M0 源码对照与合同](m0-source-mapping-and-contract.md)，其中明确现有 PRIVATE/TASK 与新 CONVERSATION 模式的数据库约束冲突及身份/幂等边界；仍须代码和实际MySQL验证。

## 1. 必须保持的不变量

1. 同一任务对应稳定悬赏 conversation，重新点将提高 assignmentRevision，不复制另一个聊天系统。
2. 只有服务器认证身份决定 owner/client/tenant/sender；请求、模型和附件不能覆盖。
3. conversation 可共享，model thread、execution run、producer lease 按对应作用域隔离。
4. 分类/意图只是建议，不能创建执行权限；明确用户业务授权经服务端持久化并校验后才能准入执行。
5. 目标 capability、grant、精确资料 ACL、任务/assignment 版本均通过，才允许真实工具调用。
6. 未归档媒体由平台持久存储；asset ready 必须有已校验字节，Agent 路径/外链不是成果。
7. 文本 final、执行完成、媒体 ready、正式提交、验收、任务完成是不同事实。
8. 网络重试、replay、恢复、看进度不会创建新的收费生成；用户明确新意图才可创建新执行。
9. 保存到空间、正式交付与验收独立；不能因用户未归档而阻止读取上一稿或验收。
10. 不把“一次点将”解释为无限工具/资料/消费授权；不因模型回复“我已获得批准”而提升权限。

## 2. 统一入口与职责

### 2.1 接入层

新增 orchestration 入口负责受理用户意图，复用 fast 的持久 request/message 及事件日志。旧 `/chat/stream` 保留 CHAT/INSPECT 语义和 execute hint 禁止；新增入口不得直接下发未经校验的 runtime command。

组件职责候选：
- `InteractionAdmissionService`：认证范围、conversation/task 关系、幂等/输入快照/用户消息入库；不调用 Provider。
- `ConversationOrchestrator`：选择步骤（answer/clarify/inspect/execute/status）、持久关联、恢复/聚合，不承担字节存储。
- `ExecutionAdmissionPolicy`：读取 task grant、用户/Agent 权限、能力及现有费用授权，返回允许/需授权/拒绝。
- `ContextResolver`：将业务事实、资料目录和内容分层组装，记录版本/摘要，不开放任意搜索。
- `ExecutionCoordinator`：通过现有执行服务创建 run/输入清单/输出用途，保持 native START 语义。
- `ConversationAssetService`：验证输出关联、创建 asset/part、发布媒体事件；独立于个人归档。

名字是职责合同，不要求机械新增六张表或六个服务进程；API Owner 在现有模块内实现最小分层，避免重复封装同一状态机。

### 2.2 路由顺序（不强制 LLM 前置）

```text
认证/幂等受理 → 固定任务和输入快照
  1. 明确状态查询 → 读服务端执行投影；无需再生成
  2. 明确绑定产物的编辑或结构化生成意图 → 校验grant/能力 → execution
  3. 仅需读指定内容 → 受控INSPECT / 内容解析
  4. 信息不足 → 基于允许上下文澄清
  5. 普通讨论 → CHAT轻量profile
```

自然语言“画一只鸟”没有结构化 operation 时，可以由已授权任务类型/受限规则生成 proposal；歧义才使用受限模型规划。规则或模型都不能替代第 2 步授权。识别失败不硬塞错误执行；能够进行普通讨论则回答，确需材料/工具但不可用则明确告知，而不是假装已读/已完成。

附件存在也不强制 INSPECT：用户问“多久能完成”只读状态；用户问“图上是什么”才需要内容。已经进入授权执行的生成任务可自行判断合理默认值或提出澄清，不必先通过 fast 模型再调用执行模型。

## 3. 办理授权 TaskExecutionGrant

### 3.1 授权来源与用户体验

用户通过明确的需求办理动作（提交/点将并启动该任务）表达本任务办理意图。后端基于用户实际权限及已有账户/费用授权，生成或引用有范围的 grant；授权信息需在正常任务交互中可见，不额外强制每轮点击“开始生成”。

旧的“只选择 Agent”“上传文件”“普通聊天中出现执行词”仍不等于授权。前端字段只是申请；创建 grant 的服务端必须验证该业务动作真实、幂等且有权限，不能以客户端 `authorized=true` 为凭据。

一次用户意图固定允许的操作及输出规格；模型不能以“继续优化”为由自行派生无限生成轮次。用户后续修改构成新的明确意图，但仍可沿用未越界的任务授权。

无已有费用授权/资料外发许可时进入 needs_authorization；不得从本设计或本次分支整合推导可调用付费 Provider。

### 3.2 逻辑字段

```text
grantId, scope(tenant/client/owner), taskId, requirementRevision, assignmentRevision,
targetAgentId, permittedOperations[], permittedToolPolicyRef,
inputScopeRefs[], allowOwnTaskDerivedAssets,
costAuthorizationRef, policyRevision,
state(ACTIVE/REVOKED/SUPERSEDED), version,
issuedBy, sourceBusinessActionId, createdAt, revokedAt?
```

- `allowOwnTaskDerivedAssets` 只允许本任务由已授权执行产生且用户可读的资产，不能据此读取其他会话/私有工具结果。
- 后续用户明确附加新资料须独立 ACL 校验并固定快照，可在既有操作/外发边界内扩展该次 execution 输入；越界需要新授权。
- `costAuthorizationRef` 引用现有收费/预算机制，不另造钱包或任意额度。额度耗尽/权限撤销是授权事实；性能慢或剩余时延预算不足不是拒绝理由。
- 需求修订若改变授权操作/用途/资料外发边界，原grant不能自动沿用；普通同任务改色等操作在原边界内可创建新意图并固定新输入，不强制重复授权。
- grant 不暴露 runtime lease/token，不接受模型自行填写，不挂在公开媒体 URL。
- 不需要额外全局过期数字：生命周期跟随授权撤回、任务终态、assignment 变更及已有明确的凭据有效期。

### 3.3 并发与撤销

同一 grant/version 与 assignmentRevision 在 execution 准入事务校验并固定。真正 dispatch/START/受控输入领取/输出提交再校验必要归属与授权状态，防排队期间撤销仍运行。

重新点将使旧 grant superseded，旧 Agent 不得取得新资料/提交到新 assignment；已产生费用/字节不可伪装回滚。取消在途执行走真实取消协议，晚到结果按版本/运行事实处理，不污染新任务。grant 撤销不会自动删除用户已经保存的文件或正式交付证据。

## 4. request / turn / step / execution 关联

复用 fast 的 `chat_request`、`chat_turn` 和事件日志；不新增第二套 request。一个用户发送动作一个 request、一条用户消息；多 Agent 时沿用各自子 turn。一个 turn 可包含多个规划/读取/执行步骤，不强制每个步骤都调用模型。

候选最小关联模型：

| 逻辑记录 | 字段 | 约束 |
| --- | --- | --- |
| InteractionContext（可扩展 request） | requestId、conversationId、taskId、assignmentRevision、intentRevision、authorizationRef、inputSnapshotId、payloadHash | scope/idempotencyKey 唯一；同键异正文或资料快照 409 |
| InteractionStep | stepId、turnId、type、parentStepId、state、revision、inputSnapshotId、resultRef、errorCode | turn/stepId 唯一；数据按 actor/Agent scope 隔离 |
| StepExecutionLink | stepId、executionIntentId、executionId、runId、partIds | step/executionIntentId 唯一；重投递不得另建计费执行 |
| PendingClarification | stepId、questionMessageId、resumeContextRef、expectedGrantVersion、status | 用户回复需绑定待澄清步骤；多处不明确时询问而不是随意续跑 |

模型线程绑定使用 scope/conversation/Agent/profile/policyRevision/context lineage。CHAT 与执行线程默认不复用有工具权限的缓存；具体 adapter 可用隔离的 turn 配置优化，但必须证明权限边界不会遗留。DB 快照是事实源，不只保存不可解析的 threadId 或消息 ID。

## 5. 分层上下文与受控输入

### 5.1 本轮快照

快照来源包括：当前需求修订、已授权参与者、任务/执行真实状态、必要历史窗口/摘要及 sourceVector、本轮用户消息、素材目录与本轮内容清单。两者分别记录 `availableRefs`（目录）和 `materializedRefs`（实际提供内容），防把“看到附件名”误报为“读取图片”。

每个内容引用必须明确 kind、源 ID、version/revision、scope、contentHash。至少支持 workspace_version、conversation_asset、message_snapshot；旧 conversation/task/message 引用通过受控 resolver 解析，不交给 runtime 任意读取接口。

### 5.2 三种执行准备

| Profile | 加载业务内容 | 工具/文件策略 |
| --- | --- | --- |
| CHAT | C0 + 必要C1，不预加载原始附件 | 专用轻量环境；不挂载执行目录，不注入通用工具；如只能只读受限必须诚实广告 |
| INSPECT | C0 + 指定C2 | 固定 manifest/只读输入，可使用所需解析或视觉能力，禁止任意文件系统/网络扩展 |
| EXECUTE | C0 + 本次精确C2 + 需要的C3 | run隔离 inputs/outputs/scratch，工具按授权操作启用；其他资料仍不可读 |

直接向支持视觉输入的模型提供授权图片可视为受控内容输入，不必人为增加 shell 工具。音频播放/图片展示属于 UI，不因此给 Agent 音频理解/生成能力。

builtin 宋江与远端 runtime 均使用同一权威上下文合同；builtin 路径不能绕回默认带全部工具的 ChatClient。实现时冻结独立 builder/profile 或采用合规 adapter，不能把传入同一快照误称工具已经隔离。

## 6. 接口与协议增量（拟议，不是现有 endpoint）

### 6.1 统一请求

`POST /chat/conversations/{conversationId}/interactions`

认证：现有用户认证/CSRF；scope/sender 仅服务端推导。必须 `Idempotency-Key`。请求候选：

```json
{
  "schemaVersion":2,
  "taskId":"task-1",
  "expectedAssignmentRevision":3,
  "content":"把这只鸟的羽毛改成蓝色",
  "inputRefs":[{"kind":"conversation_asset","assetId":"asset-1","revision":1}],
  "replyTo":{"messageId":"message-1","partId":"image-1"},
  "actionProposal":{"kind":"edit_image"},
  "continuationOf":null
}
```

`actionProposal` 可省略，仅提示；客户端不得提交 owner、grant 权威字段、任意工具列表/命令。服务端按 task 关联选择 grant，而非接受用户伪造 grant 权限。`continuationOf` 用于准确回复澄清/失败恢复，不等于重新执行；源 request/step 必须同授权范围。

新受理返回 202：`requestId,userMessageId,turnIds[],state,stateVersion,eventCursor,statusUrl`。同键同 payload 返回同 request 当前状态；旧未知响应不会生成第二个 request。复用 `GET /chat/requests/{requestId}` 查询，新增 steps/挂接 execution 投影，保持旧字段兼容。

错误：400 结构/引用非法；401 未认证；404 无权或不存在；409 同键异payload、assignment/版本冲突、取消/状态冲突；422 实际能力/格式不支持。可等待的离线目标保留 waiting_target；缺必要授权持久为 needs_authorization，不标执行已开始。错误只提供 owner-safe 代码、stage、retryable、requestId，不暴露本机路径或凭据。

### 6.2 授权动作

新多媒体点将请求拟在既有 `/agent/tasks/{taskId}/assign` 携带 `workflowVersion=2`、`businessAction=assign_and_start`，界面仍只有一次“点将并办理”的正常动作。两字段表达用户请求，不是权限证明；服务端仍校验认证用户、任务版本、目标归属、操作与已有费用/资料授权，再在同事务记录assignment/grant意图/outbox。旧客户端不携带版本时保持原点将语义，不因上线新功能自动授予或启动历史任务。重试使用原幂等键，不重复创建grant/执行。

优先扩展既有任务发起/点将事务形成 grant，不新增“每轮授权”按钮。需要补授权时拟议 `POST /agent/tasks/{taskId}/execution-authorizations`，输入 `expectedTaskVersion,expectedAssignmentRevision,requestedOperations,inputRefs,existingCostAuthorizationRef`；由服务端验证后返回非敏感 `authorizationId,version,state,scopeSummary`。客户端不能自己设置金额或把 ref 当已授权证明。

撤销拟议 `POST /agent/tasks/{taskId}/execution-authorizations/{authorizationId}/revoke`，携 expectedVersion/idempotencyKey；只撤销当前用户有权管理的授权，返回撤销事实及相关运行的取消进度，不谎称已经终止所有 Provider。

### 6.3 状态、取消与执行创建

- `GET /chat/requests/{requestId}`：复用并扩展 aggregateState/steps/outputs/requiredAction；不是另一套状态服务。
- `POST /chat/requests/{requestId}/cancel`：旧语义不静默扩大。新 v2 请求须显式 `scope=interaction` 和 expectedStateVersion，服务端编排取消其已授权运行；不取消同会话其他请求/他人工作。旧客户端没有 scope 时保持取消聊天推理原语义。
- `POST /chat/turns/{turnId}/cancel`：仍仅取消对应推理；与真实执行取消分清，UI 显示“停止回复”和“取消办理”的实际目标。
- 新执行由服务端应用服务调用既有 execution 入口/持久 command 机制，绑定 grant、step 和 intent；**不允许 `/chat/stream` 通过 execute 字段绕过**。
- CONVERSATION 使用独立 native fence 的 inbox/lease/inputs/stage/commit/failure 路径，不复用 PRIVATE/TASK 无 fence 输入接口，不用浏览器代持 producer 凭据。当前服务端 `POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/inputs` 仅在当前 Agent Runtime 租约、任务根、grant 和执行归属一致且输入行**真实为空**时返回 `{executionId,leaseVersion,noReferencedMaterials:true,inputs:[]}`；输入行不为空则拒绝，绝不把有参考资料说成“无资料”。后续参考图版本与来源 ACL 接入时扩展为精确 input manifest 和受 fence 的字节读取，不能把目前的无参考桥接当作完整参考素材实现。

### 6.4 能力协商

逐目标声明协议、context snapshot、事件、读取格式、执行操作、输出用途、工具策略及实际版本。能力注册须绑定当前 Agent owner/connection，不能信任前端宣称支持。

交互受理固定路由及协议决策，但发送前重新核对当前连接 capability，变化时等待/明确不兼容，不偷偷切到另一执行协议重复收费。老 Agent 原有文本能力可保留；需要新媒体而不支持时如实报告，不能虚假 fallback 成“生成成功”。

## 7. 状态机与恢复语义

### 7.1 两类状态不能混为一谈

- 推理 turn：admitted → responding → text_final / failed / cancelled。
- 办理聚合（request 投影）：accepted → planning / waiting_user / waiting_authorization / waiting_target / running → succeeded / partially_failed / failed / cancelled。

其中 request.succeeded 仅表示本次请求预期步骤完成，不表示任务验收/需求完成。多媒体请求的 text_final 之后可以仍 running；media ready 需上传与manifest已提交。现有 durable terminal event 保留文本含义，新 UI 用 request projection 展示办理状态，不能改旧事件定义造成客户端提前停止媒体订阅。

### 7.2 澄清与续办

已授权执行可产生 clarification artifact，平台在同会话提问，保存原步骤/资料快照/授权版本。释放长运行 lease 后，下次回复通过 continuationOf 产生新的受控 continuation execution，关联同请求链和前次检查点，而不是盲目重跑已发生副作用。

仅对工具支持安全恢复且已有检查点的阶段自动续办。无可恢复检查点、费用/输出未知时先对账，不伪造exactly-once Provider保障；用户要求重新生成时建立新意图并明确已有结果状态。

### 7.3 事务与去重

1. 任务分配、grant 意图与 bootstrap outbox 同一业务事务；跨库不假装原子。
2. admission 的幂等记录、用户消息、request/turn 与 outbox 采用事务写入或现有等价机制。
3. executionIntentId 稳定映射到唯一 execution；dispatch 重试重用同标识。
4. 字节上传是可恢复阶段；校验完成后同事务登记 output/asset/part 及发布outbox，不先发布 ready 再写字节。
5. 归档/正式提交分别持久幂等键。formal晋升和用户验收不能一起假装分布式原子动作。

Provider调用后的ACK丢失属于 outcome_unknown，优先查运行/已上传输出；不能只因查询暂404或SSE断开就新开执行。Native START 必须先于真实 Provider 调用，重指派/撤权后不能绕过。

## 8. 事件、媒体和成果

沿用 durable 单会话 event journal：统一 eventId/seq/cursor，新增 `interaction.state_changed,step.state_changed,part.processing,part.ready,part.failed,authorization.required`。稳定关联 request/turn/step/execution/run/message/part；按消息/part revision 防旧事件回退，按 scope 分发。

断线后补拉；游标过期返回 resync_required，读取授权快照+watermark后续订阅。快照与后续事件边界可复核；不在Web另造只驻内存的成果真相。回放/消息保存不能触发执行。

媒体/产物/归档/验收沿用 v1：
- 会话字节先持久到现有 workspace-private，创建 asset 而非必然创建个人文件。
- 个人归档创建文件版本引用；最终交付按精确选中集合晋升至既有正式成果协议，必要时复制字节核对hash。
- 正式producer授权由受信适配器办理，用户以自己的身份验收；不删除lease/权限条件。
- 文本快照、图像、音频、文件均可归档/引用；音频Range和私有认证必须覆盖，不能把工具执行stdout当最终文件。
- 已保存或正式交付持有自己的保留引用，会话删除/Agent离线不导致其丢失；本期不增加任意TTL自动GC。

## 9. 最小数据迁移计划

优先扩展现有 request/turn/snapshot/outbox/执行输出关系：新增可空关联列，保持旧读写；仅确无可复用结构时引入 grant、step、execution link、conversation asset、archive/finalization 关系。

DDL冻结项：scope组合唯一键、幂等键payload hash、grant/assignment CAS、step/run唯一映射、asset版本、事件seq索引、关键外键/逻辑一致性检查；具体表名与已有MyBatis实体映射由U1提交，不在此编造已落地SQL。

迁移验证：实际MySQL空库/存量/重入/部分失败恢复；旧记录无grant时不得自动补无限授权；历史Markdown路径不回填假资产；旧machine JWT tenant影响由既有通用认证迁移单独核验。新schema未准备好不启动新功能入口，但保留原业务可用性，不吞实际数据库错误。

## 10. 安全与资源边界

按tenant/client/owner、task/conversation、Agent、assignment、run层层绑定。当前storage的tenant=0限制继续如实保留，不借此推广多租户。

不把资料文件里的指令提升为系统策略；路径/MIME/魔数/hash/符号链接检查延续原runtime；只返回本轮声明输出。前端预览使用已授权内容API、安全Markdown/文档转换，不接受模型自造URL/hash当可信交付。

轻/重工作互不占同一粗粒度busy标志；共享并发资源按实际容量/排队策略调度，不能为了TTFT阈值拒绝或取消下一步。资源不足真实报错可处理，性能慢只观测；不加未经推导的磁盘/swap硬门槛。观察值不构成新的凭空预算。

## 11. 融合验收补充（FD01–FD12，全部NOT_RUN）

| ID | 验证目标 | 可观察通过条件 |
| --- | --- | --- |
| FD01 | 普通聊天保持轻量 | 无附件内容物化/无执行工具启用/无execution创建；有必要对话上下文 |
| FD02 | 明确生成直接执行 | 授权充分的画鸟意图可直接进入execution；不是先强制CHAT模型调用；只有一次执行 |
| FD03 | 带资料按需加载 | 精确指定版本被读取；其他空间资料未读取；元数据和真实内容读取证据区分 |
| FD04 | 模型/前端不能授权 | forged execute/grant/tool/cost 字段不能触发未授权执行，旧stream禁止仍成立 |
| FD05 | 同会话不同权限环境 | CHAT无法读取前次执行目录/私有轨迹；已发布资产可经授权再次引用 |
| FD06 | 澄清释放并安全续办 | 等待用户无长执行lease；恢复重新校验grant，已完成副作用不重复 |
| FD07 | 文本结束不结束办理 | text_final后媒体仍更新；request办理完成不自动完成任务 |
| FD08 | 重试/回放不重复计费 | 同意图只对应一个execution；unknown结果对账，明确新生成才新intent |
| FD09 | 撤权/重指派竞态 | 旧Agent不能领取新资料/向新assignment提交；晚到结果不会覆盖新状态 |
| FD10 | 状态查询不走重执行 | 查进度只读投影，不额外触发生成/资料扫描 |
| FD11 | 新旧混用与能力真实 | 每个目标协议匹配；不支持INSPECT不广告；无工具标签有实际引擎证据 |
| FD12 | 冷恢复与多模态 | thread缓存丢失时恢复授权事实/上稿，builtin和远端一致；image/audio/file历史可读 |

FD用例补充而非替代原AC01–AC22。**总数为34项（22 AC + 12 FD）**，不得把本轮源码合并定向测试计入这些未执行的产品用例。

## 12. 实施边界与交付定义

U0/U1→U2→U3→U4 的切片见长期方案；各项明确 commit/tree、selector、DB fixture digest、真实浏览器证据。当前合并分支是研发起点，不是产品实现完成。

明确不做：新建第二套会话数据库、把所有工具塞进fast、无授权自动收费、共享Agent挂载、全盘同步、在线Office编辑器、强制更换Provider、用开发助手直接生图替代平台验收。工程实施继续Owner自检，不创建独立Reviewer。本轮不执行数据库迁移/部署/模型调用。


## 13. 2026-09-30 实施状态补充（不改写目标合同）

本节是源码状态说明；长期权限、存储、幂等与验收合同不变。精确开发 pin 以 `integration.yaml` 为准，不以本文件日期或旧测试数量作为发布证据。

- **已整合基础**：fast 的持久 request/turn/outbox/snapshot/event；多媒体准入/执行与私有输出读取切片；Web 媒体展示、真实字节校验与下载合同；本次持久会话资产/历史 parts 切片。[资产整合与实测](integration-u3-durable-assets-20260930.md)包含默认关闭配置与证据限制。
- **保存对接合同**：成果区须从服务端读取真实 `assetRef={assetId,revision}`，使用 `mode=create` 和 `items[].assetRef`；`outputId` 是输出定位，不是资产保存凭据。后台投影未完成时可继续预览输出、显示保存待就绪，不错误宣告已归档。既有归档客户端持久原幂等意图并隔离身份；不再实现第三套保存客户端。
- **正式交付合同**：`finalizations` 仍须实现受信 producer 晋升、精确选中集合、用户验收和任务完成的分阶段恢复。会话资产 ready、个人保存、任务完成分别成立；不能用其一推导另一项。
- **未完成验证**：真实模型/两类客户端的无工具/精确读取边界，有/无参考资料、上一稿修改、澄清续办和多媒体端到端，以及 exact 版本发布。没有真实证据时维持 NOT_RUN，不用本地开发助手生成鸟图替代平台交付。


## 14. 2026-09-30 保存合同实施补充（晚于第13节）

[output→assetRef→工作空间归档对接](integration-u3-output-asset-archive-20260930.md)已整合至研发分支，覆盖第13节“保存对接合同”的源码缺口。目录 GET 的可选 assetRef 必须指向已持久且完整来源核对的资产；未投影时等待，不触发生成/投影/归档写操作。Web 保存统一委托已有归档 composable，保留原幂等意图、只读查询、明确原键重放和身份隔离。

这是源码和定向测试事实，不是线上保存或完整验收事实。正式晋升/验收/任务完成仍待实现；schema初始化顺序、真实双接应、完整多媒体/澄清/引用修改、exact版本发布和浏览器证据仍须收口。34项产品验收不得用本轮160/28项单元测试代替。

## 15. 2026-09-30 正式验收与分阶段恢复合同补充

正式验收HTTP合同冻结为 [finalization v1](finalization-contract-v1.md)：POST按原Idempotency-Key持久受理精确成果集合，两个GET分别按operationId/原键只读核对。阶段为PROMOTING→READY_TO_SUBMIT→SUBMITTED→ACCEPTING→TASK_COMPLETED；最终完成须同时具备真实正式交付accepted、领域task completed及实际deliveryId，不以UI标签或模型回复作证。版本使用十进制字符串回执，原请求保留可安全表示的整数。

持久晋升适配器须核验会话输出完整来源、授权/assignment、字节/MIME/hash/length；hash只是预期pin而非所有权凭据。通过Agent应用服务取得真实producer/work-item/run/lease，再复用正式submit和owner decision；不建立Agent→Chat实现模块循环依赖，不为获lease调用Provider，不删除原权限条件。固定成果/晋升/提交/验收事实分阶段恢复，GET、回放和查询绝不触发新执行。

[Web实作证据](integration-u3-finalization-web-20260930.md)已覆盖原操作恢复、完整回执校验、纯读查询和身份隔离；API正式闭环仍在开发，尚未获得exact候选测试/隔离MySQL/浏览器证据。本节冻结目标合同并记录切片进展，不将34项产品验收从NOT_RUN改为通过。

## 16. 2026-09-30 真实点将入口施工补充

[点将即办理入口详设 v1](point-and-start-entry-design-v1.md)补充权威当前需求读取、v2点将body/原幂等键、grant与task分离、自动进入已有bootstrap会话及unknown恢复。当前Web点将仍是legacy，当前需求revision读接口待实现；成果展示/最终验收UI测试不关闭此入口缺口。原CHAT/INSPECT/EXECUTE授权边界、统一会话/存储和finalization冻结合同不变；34项产品用例维持未验收。


## 17. 2026-09-30 原点将只读恢复合同补充

详见[原点将操作只读投影合同 v1](assignment-operation-read-contract-v1.md)。这是第16节入口施工的恢复补充，不改写已冻结的finalization合同，不宣称新接口已实现或已部署。

浏览器需在点将写入前固定原键和正文；状态恢复只读查询原业务action，分别核对 root/task、grant、bootstrap 的版本事实。`ADMITTED` 表示首轮Chat请求受理；只有当前assignment仍匹配时才自动采用其确切会话/首轮request，采用前还须验证服务端RequestView的任务/assignment/目标及会话关联。不以 `taskVersion == assignmentRevision` 猜当前归属，不自动重发首轮生成。

原操作404、网络响应未知、历史读取失败都不表示执行从未受理；用户明确恢复时才允许按原键/原正文重试对应写入。已确认的受理事实不得因媒体或历史读取失败被抹除。权限切换、重新点将、晚到响应须隔离，已撤销/替换的原操作仅可显示真实历史事实。

首轮初始动作与grant允许动作集合是不同维度。当前bootstrap只接受单个非INSPECT动作的实现限制须由代码包改为显式首轮动作，不能缩窄长期授权集合或让Web猜选首轮；补齐前不以同时允许GENERATE_IMAGE/EDIT_IMAGE的grant宣称入口闭环。


## 18. 2026-09-30 首轮采用与初始动作合同施工补充

[首轮采用源码证据](integration-u1-web-bootstrap-adoption-20260930.md)已整合Web，验证actual RequestView/fence再挂接确切会话。`OUTPUT_COMMITTED` 是本次原生创作请求终态，不是需求完成；SSE成果只触发权威只读readback，不代替真实字节/交付/验收事实。此切片尚未接页面v2点将，API新GET/finalization候选未正式验证。

[首轮动作与完整授权集合冻结合同](initial-operation-contract-v1.md)为第17节初始动作缺口固定新字段与hash兼容：grant可允许生成和修改，显式首轮只选择一项，已有outbox保存唯一初始动作；原投影不再由完整集合反向推导。兼容仅限旧请求原本可确定的单动作，不把缺字段/歧义转成默认收费执行。未实现的上一稿/费用授权/修改resolver不得以这一合同声明已可用。


## 19. 2026-09-30 原点将恢复组件与页面接线边界

[原点将恢复源码切片](integration-u1-web-point-and-start-20260930.md)固定原body/key，真实需求修订与canonical task先读，原grant/assignment/outbox独立fence后读；采用会话只交接确切已有bootstrap，禁止补发需求。首次明确动作、纯读核对、显式继续原操作是三个不同入口，不做刷新自动POST。

持久意图不是授权；服务端能力协商尚未定义/接通，新组件默认不支持。后续页面接线必须提供权威支持事实、当前身份/目标隔离回调、实际任务资料关联和精确首轮采用，不能用UI开关或测试注入证明执行许可。前端完成事实仍分别是本轮成果、个人归档、正式提交、owner验收和真实task.completed。

本次API只静态候选，不更新pin。初始动作字段须参与Controller v2识别，selector-only不完整请求也不能落入legacy；此缺口独立补测。schema readiness fixture纠正只解决测试条件，不替代正常模块/真实库启动。长期直接执行/澄清/多轮修改与费用授权仍按第17–18节和各冻结合同推进。

## 20. 2026-09-30 ENTRY/finalization组合源码证据

[组合源码与验证记录](integration-u1u3-entry-finalization-20260930.md)：API研发pin提升到 `f93febe9`/tree`8289c1a3`。正常模块357次测试执行、bounded99项、独立MySQL26项与锁归属实测通过；保留已归因失败，不意味着整套构建/Provider/UI或产品验收完成。真实NULL约束问题已修正；旧实验schema不能据CREATE IF NOT EXISTS视为已迁移。下一步权威目标能力协商、实际页面与task引用、多轮澄清/EDIT/费用授权；仍维持一条会话与平台权威资产，不添加第三套文件系统或强制三轮模型调用。

## 21. 2026-09-30 旧弱约束与实际生命周期补充

[精确源码与证据](integration-u3-schema-check-truth-20260930.md)：`b1e7b068`安全识别旧弱CHECK，不自动迁移；真实MySQL揭示的TEXT/MEDIUMTEXT元数据预期错误已修正。84项正常报告（42本次/42复用），6项真正JDBC/Spring初始化图通过。pre-fence源派生fixture不是生产原始DDL，不将此声明为完整应用启动/旧库迁移。原失败与绑定问题保留。

## 22. 2026-09-30 原生执行能力与费用来源补充

[原生能力施工合同v1](native-bounty-capability-contract-v1.md)冻结agent.register sibling `nativeBountyExecution`、成功当前session/持久身份校验，以及owner只读点将协商。fast-v1 EXECUTE=false保持不可变；原生HTTP执行与fast路由分别证明、服务端准入共享平台会话/资产事实。

能力就绪不等于费用授权。现有reward escrow/hosting/skill/wallet用途不能挪为costAuthorizationRef，当前费用签发桥缺失须真实补齐。原v2点将意图存在时永不legacy降级，404/UNKNOWN仅恢复未知，不能自动重发/生成。本文不因增加声明而缩窄画鸟、参考图、修改与验收目标。

## 23. Provider权限与调用前计数的源证据补充

见[长期费用/调用前详设补充 v1](provider-authority-and-precall-enforcement-design-v1.md)。当前START只防整次executor重启，通用Codex进程内部仍缺pre-call门禁；不能把单结果或提示词当单次费用保证。账户operator许可与taskOwner操作同意分别建模；独立受控executor/gateway须有真实适配和明确账户授权，未冻结或启用。此补充不改现有冻结native-v1，不缩窄完整多媒体/双接应/34产品验收目标。


## 自然交互与多稿发现的长期合同补充（2026-10-01）

本节追加而不改写已冻结协议。[typed result v1](typed-deliberation-client-result-contract-v1.md)明确模型结果通道：只有服务端校验过的snapshot启用native outputSchema，模型返回ANSWER、必要CLARIFY或EXECUTION_PROPOSAL。流式界面仅展示顶层text，原子final同时绑定正文与严格union；plain CHAT黄金wire不变，禁止对普通聊天正文做关键词/JSON解析来授予执行权。

API后续必须同事务保存finalDigest、message/event/outbox和typed事实：相同正文但不同proposal/问题不是幂等重复；来源、目标、dispatch和context hash由服务端重验。CLARIFY保存版本化pending question并进入WAITING_USER，不占长期生成lease；精确回复以问题版本CAS消费并形成唯一续办事实。回复/提议均不能直接生成command或consent，续办重新校验目标、任务、资料与本轮授权。未知回执按原键只读恢复，不再调用模型/生成第二次副作用。API pending/续办wire与DDL仍需责任Owner冻结并实测，本合同不冒充其实现。

[conversation request index v1](bounty-conversation-request-index-contract-v1.md)提供独立权威目录：activeRequest只负责正在处理/取消焦点，成果与历史由多request目录发现。固定through分页只是keyset扫描，不是假称跨页MVCC；晚提交低ordinal由下一轮从0重扫发现，单轮缺失不删除旧稿。历史旧assignment可预览/下载，不借用当前目标/许可供选择、编辑或验收。

这两份追加合同消除的是长期状态/来源边界，不是临时把fast与multimedia互相切换的兼容开关。真实INSPECT、自然输入闭环、API持久续办、双接应和全产品验收仍需完成。
