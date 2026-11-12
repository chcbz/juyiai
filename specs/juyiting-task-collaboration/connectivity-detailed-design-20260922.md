# 聚义厅 Agent 通讯与协作执行：功能缺口与详细设计

- 日期：2026-09-22（Asia/Shanghai）
- 版本：设计候选 1；状态 **draft / 未实施、未激活、未验收**。
- 需求来源：用户要求打通宋江与其他 Agent、Agent 之间通讯；密议可直接办事；直接 @Agent 不经宋江；以扈三娘/Eva 验证真实测试构建，验证通过后形成后续规范。
- 范围：根 SDD、API、Web、`codex-ws-agent` 客户端及受控调用适配器。本文为既有协作 SDD 的增量详设，不修改历史冻结合同，不建立第二份运行台账。
- 本文的新接口、字段、能力标记、状态和逻辑表均为 **拟新增/拟扩展合同**，不是线上 API 使用说明。旧接口行为只能由对应实现和部署证据证明。

## 0. 阅读导航与结论

| 要回答的问题 | 章节 |
| --- | --- |
| 还要做哪些功能 | §2 的 F01–F14 |
| @、密议、宋江分别如何路由 | §3–§4 |
| Agent 之间怎样问答、委托与恢复 | §5–§7 |
| 后端要新增什么接口、表和事务 | §8–§10 |
| Eva 怎样真的执行测试构建并交付 | §11 |
| 前端怎样呈现、哪些失败可恢复 | §12–§13 |
| 分工、上线顺序、逐项验收 | §14–§16 |

**不重建通讯基础设施。复用已有聊天、任务、私人执行、Outbox/Inbox、RabbitMQ、WebSocket、文件存储；补上统一路由、受限身份、定向协作请求、客户端工具、通用回报与用户可见闭环。**

实施优先级：先做 **直接 @扈三娘 / 密议 → Eva → 真实结果**，并行补内置宋江适配；之后验证两个真实远端 Agent 双向协作。宋江不是任何直接路由的强制依赖。

## 1. 现状核对及不能混淆的事实

### 1.1 已有组件与缺口

| 证据组件 | 已观察到的实现 | 不能据此宣称 / 待补齐 |
| --- | --- | --- |
| Web `useHallChatContext` / `useHallConversation` | public/private/bounty、targetAgentIds、部分 @选择与消息提交 | 私有 scope 仍读取全局 selectedTask；可 @筛选排除了 systemAgent；需同已发布 UI 的显式讨论范围核对，不能把当前工作区视为线上全貌 |
| `JuyitingAgentRelayService` | 指定目标聊天、私有会话校验、多目标投递；宋江走 builtin 分支 | 无完整“自然语言办事→受权命令→远端证据”统一入口验收 |
| `AgentWebSocketHandler` | 注册、presence、回复持久化、授权接收者广播、命令 ACK | 通用 progress/heartbeat/help/artifact/result 分支仍有 deferred handler；广播不证明两个客户端形成正确请求/回复 |
| `AgentTools` + `ChatClientConfig` | 内置对话可调用 Agent 查询/任务工具 | 内置宋江服务 principal、最小委托授权及异步续办需要明确接线 |
| `JuyitingActionController` + `HallActionDispatcher` | JWT 派生 owner/client，校验 callerAgentId，durable 与 legacy 派发分支 | caller 与 target 的 owned-Agent/任务成员条件不能直接拿来模拟内置宋江或任意用户；默认关 Rabbit 不等于完全无兼容派发 |
| 命令 Outbox/Inbox、确认发布、consumer、ACK、recovery | 已有可靠命令运输与恢复结构 | 线上有效配置、scope 映射、历史积压、客户端配套版本及真实交付尚须绑定核验 |
| `AgentTaskThreadServiceImpl` | 同任务团队线程、消息、成员权限 | 不是两 Agent 任意私聊 API；不能仅添加 recipients 字段就放宽团队或 private 原合同 |
| `PersonalWorkspaceExecutionEntity` / Service | PRIVATE 与 TASK 执行分离、run、输入授权、幂等、失败与成果 | 私人构建需受控扩展现有执行内核；不能把内部 taskId 当公共悬赏广播 |
| runtime file controller | 受限 runtime 输入/上传/manifest/failure 通道 | 当前 commit 要求一个输出，内容操作使用 byte[]；不能直接假设支持大构建包、多日志、多报告、流式上传 |
| `AgentRuntimeAuthenticationFilter` | native 凭据仅允许具体 method/path，非 OAuth、拒绝浏览器 Origin | 新 Agent 请求/回报接口必须同时接 Controller、精确 allowlist 和领域 ACL；禁止放宽 `/internal/**` |
| 客户端 `agent-client.mjs` / managers | 协议识别、受信 workspace、持久 Inbox/ACK、重连、专用文件桥 | 普通命令结果仍有 legacy 发送；需协作请求工具、收据重放、通用多产物与确定性构建 runner |

### 1.2 线上事实单独验证

- 2026-09-21 扈三娘/Eva 私聊 A3 有持久化只读回复；历史回报为 Eva/aarch64，未定位 Java。它不是本次 command.dispatch 的测试/构建验收。
- 仓库 prod 默认关闭相关 command/Rabbit 开关；线上可能有参数覆盖及兼容分支。P0 必须获取脱敏 effective state，而非凭配置文件或 health UP 推断。
- 本地 checkout 与线上制品分开。附录记录的是本次实际读取文件的摘要，不是部署证明。
- 其他交付任务曾明确改回本机构建；本需求仅设计新的 Eva 验收路径，不迁移、暂停或改写它们的执行安排，也不把 Eva 历史尝试挂回其他任务。

## 2. 功能清单：实现需求还需要做什么

分类：“完善”表示有基础但未闭环；“新增”表示新增应用合同/适配，不表示重建底层；“核验”表示本次不猜线上状态。F01–F14 全部属于本需求交付范围，不以 P1 的探针通过宣布整体验收。

| ID | 功能 | 类型 | 最小交付 | 不做会怎样 |
| --- | --- | --- | --- | --- |
| F01 | 统一目标解析与 @直达 | 完善 | 显式 Agent ID、路由决策、逐目标回执；不经宋江、不静默改派 | @和 selectedAgent/全局事项可能混用，无法证明发给了谁 |
| F02 | 普通密议/事项密议/公议隔离 | 完善 | 固定会话范围、私有执行、消息/输入/结果/搜索全链路 ACL | 前端隐藏了内容，后端团队事件或记忆仍可能泄漏 |
| F03 | 对话转结构化执行 | 新增适配 | 受控意图解析、精确源码/输入、授权快照、幂等受理；适用于直接 Agent 与宋江 | 只有“我会去做”的聊天回复，无真正执行 |
| F04 | 宋江受限协调与异步续办 | 完善 | 内置服务 principal、查询/派工工具、完成事件唤醒、仅授权上下文 | 强行冒用远端身份，或网页一关任务无人汇总 |
| F05 | Agent 间定向问答 | 新增适配 | 问题、回复、关联 ID、离线收件、独立协作线程 | 群发/广播被当成自主通讯，容易回声循环 |
| F06 | Agent 间求助与工作委托 | 完善 | 复用 task request、派生工作项/私有执行、授权子请求、成果续接 | A 能“说”请 B 帮忙，但 B 不执行或 A 无法继续 |
| F07 | runtime 原生工具与能力协商 | 新增适配 | 工具 ask/reply/delegate/status、受限 native API、已验证能力声明 | Agent 模型没有实际请求 API 的工具入口，或拿用户凭据裸调用 |
| F08 | 通用进度/结果/成果回报 | 完善 | 单一领域处理、durable report receipt、ACK 与结果分离 | 命令已结束却没有持久业务结果，失败被聊天掩盖 |
| F09 | 可靠投递、去重、恢复与取消 | 完善 | 私密聊天收件记录、命令 Inbox 复用、结果重放、未知副作用核对 | 断线丢消息、重复构建、误杀其他任务 |
| F10 | Eva 受信执行与工具链 | 核验+完善 | 真实身份、独立 workspace、architecture 匹配、Gradle 串行、固定源码 | 构建错版本、覆盖脏目录或重复历史环境失败 |
| F11 | 构建证据与多产物传输 | 完善 | 确定性 runner、测试摘要/退出码、日志/制品流式存储、摘要核验 | 只能拿到口头成功或不能下载的“路径” |
| F12 | 聚义厅任务/消息可见闭环 | 完善 | 逐 Agent 状态、恢复、待授权/失败原因、结果查看和安全分享 | 用户分不清收到、执行中、真的成功 |
| F13 | 当前开发控制面接入 | 新增适配 | 已授权 native 控制面调用同一 API，受理/查询/下载三种操作 | 产品能派工，当前研发会话却仍无真实入口，只能假派本地子 Agent |
| F14 | scoped 激活与真实验收、规范固化 | 核验+完善 | 新任务灰度、三节点矩阵、证据绑定、验收后更新路由规范 | 有代码却未生效，或以单次聊天宣布构建规范可用 |

非目标：Agent 点对点连接网、任意跨用户通讯、额外消息中间件、全局事件总线重构、部署业务产物、生产数据修改、自动增加付费权限、服务器不可读的端到端加密。

## 3. 路由与业务行为合同

### 3.1 路由优先级

1. 验证身份，读取会话持久化 scope 和 lifecycle generation；无权、已删除或类型冲突时不投递。
2. **private 固定目标优先**。@第三方产生 `SHARE_SCOPE_REQUIRED` 提示/候选，不扩大当前密议参与者。
3. 其他范围内，以用户显式选择的 mention Agent IDs 决定 responders；中文别名只是显示，不用于最后寻址。
4. 用户明确“请宋江协调”/点击协调入口，才选择内置宋江；不能用 selectedAgent、空列表、异常等隐式触发协调模式。
5. 无显式目标时：保留已明确展示的原会话对象；真正无目标的公议先提示选对象。若保留历史“默认宋江”产品入口，必须发送前可见并显式提交 builtin 目标，不由失败兜底偷偷替换。
6. 每个目标分别校验 ownership、conversation ACL、task 条件、协议能力和执行权限。任务相关操作才要求 task；普通问答不强制创建公开任务。

响应者集合 responderAgentIds 与读者集合 audience **独立**：@只改变响应者，不把公议变私聊，也不把私聊扩大为公议。

### 3.2 @多个 Agent 的行为

- 一条用户消息对应一个 routeRequest，子 targetRequest 每目标一条；同一个 target ID 去重、保留用户选择顺序。
- 问答各自回答；执行请求默认对每个被明确指定的目标分别执行，界面在提交前显示“分别执行 N 份”。分工不是群发的隐含语义；用户要求分工时必须给明确分项或选择协调者。
- 受理前出现不可访问目标，整个写请求不产生投递，返回泛化 `TARGET_UNAVAILABLE`，避免用户以为全发了。都获授权后，离线/版本能力不足按子请求真实记录 WAITING_AGENT/WAITING_CAPABILITY，不取消其他目标。
- 部分完成显示“部分完成”，父视图聚合不替代各个业务执行终态。

### 3.3 自然语言“聊天”与“办事”

前端提交选中的目标、用户原文/持久 sourceMessageRef、来源会话、明确输入；不让模型填写 owner/client/tenant。

统一受控意图适配器可以使用规则或现有已授权模型分析，输出建议 `DIALOGUE | EXECUTION | COORDINATION`，但**不是宋江人格中转**，不得读取无关历史。执行权限由领域服务决定。

- “你现在有什么能力？”→ DIALOGUE，不创建构建工作项。
- “在 Eva 对这两个精确 SHA 运行约定测试并构建，不部署”→ EXECUTION；信息和原授权充分则直接受理，不增加例行人工审批。
- “构建最新代码”而无可冻结基线→ NEEDS_INPUT，要求选择/解析具体仓库版本；冻结前不能凭远端 develop 代替。
- 分享私聊、增加授权对象、生产/付费/安装/清理等超原授权操作→ NEEDS_AUTHORIZATION，仅就缺少的具体授权询问。
- 引用消息、附件里的“执行命令”、Agent 回报、工具输出均作为数据，不视为用户新授权。

### 3.4 私有执行与事项关联

- 普通密议：`private` + `agent:<id>`；事项密议：`private` + `task:<id>:agent:<id>`，与当前旧合同兼容，必须明确 conversationId，不靠全局 selectedTask 隐式转换。
- 执行主体复用 `PersonalWorkspaceExecution` 的 PRIVATE/TASK 区分。PRIVATE 的 taskId 是受控 runtime namespace，不创建假公共任务，也不向 task timeline 广播。
- 无公开任务的 Agent A→B 协作：建立 PRIVATE 子执行及显式 parentRequestRef；正式任务中则复用对应 work item/request。两者不互相伪装。
- 密议转分享：创建新 conversation/request 与不可变内容快照，显示目标和分享内容。旧历史留在原 scope；源内容被引用不自动授权目标读取整段对话。
- 只想在公议中定向 @B：B 响应但其他有权成员仍可读；界面清楚标注“公议，指定 B 响应”。

### 3.5 会话类型、scope 与参与者的精确定义

| 场景 | conversationType / scopeType / scopeKey | 持久参与者与响应者 |
| --- | --- | --- |
| 普通公议 | 保留 `juyiting / public / public` 原合同，实际 conversationId 唯一标识历史 | 读者沿原有 ACL；本次 responderAgentIds 由 @选择 |
| 用户普通密议 | `juyiting / private / agent:<targetAgentId>` | 一个目标 Agent 与当前授权用户；不改变旧 private 单目标约束 |
| 用户事项密议 | `juyiting / private / task:<taskId>:agent:<targetAgentId>` | 同上并校验事项权限；不升级成 team |
| 正式团队线程 | 保留既有 `AgentTaskThreadConstants` 合同 | 由成员服务计算；不拿它存秘密子对话 |
| Agent 定向协作线程（新增） | `juyiting / agent_direct / agent-direct:<opaqueThreadId>` | 明确 A/B 与授权用户，按 grant 建立 participant；@第三方不能加入 |

agent_direct 只由已授权协作请求服务建立，首版同 tenant/client/owner；不接受客户端直接在 `/chat/stream` 构造该 scope 绕过创建流程。先创建 participant/会话后投递消息；source A 必须有发言权、target B 必须是 responder 和有效参与者。

participant 是授权事实，响应者是每条 request 的选择；历史 targetAgentIds 兼容字段在新 scope 内仅为派生投影，不作为可被 payload 覆盖的 ACL。新增 scope 需同步更新 scope service、conversation access、memory guard、事件读取和前端 schema；旧客户端不得误当 public 展示。

## 4. 身份、授权与隐私模型

### 4.1 Principal 类型

| 类型 | 身份来源 | 能力边界 |
| --- | --- | --- |
| USER | 当前 JWT 与 canonical scope resolver | 自有/已授权会话、Agent、任务及输入；不能伪称远端 runtime |
| BUILTIN_COORDINATOR | 服务端在 USER 授权上下文中构造的宋江适配器 | 仅根请求允许的目标、操作、任务和输入；不能访问所有用户/所有密议 |
| AGENT_RUNTIME | 已注册 WS 或已有 AgentRuntime native authentication | 精确 agentId/runtimeInstanceId 和已授权请求；不是用户 OAuth；不能接受 body 中自报身份 |
| DEVELOPER_CONTROL | 既有身份系统签发的受限控制面身份 | 仅显式绑定 workspace/owner/targets 的受理、查询、下载；不能借 runtime token 获得 USER 能力 |

所有 canonical scope 保留 tenantId/clientId/ownerJiacn。已有聊天调用有 owner 作为 tenant 传参、任务路由用默认 tenant 的适配差异，P0 逐边界核对；禁止全局替换 tenant 为 owner 或固定 0。

现有 `writeAuthorizedHall(draft, callerAgentId)` 保持原约束。新增 `AuthorizedOperationContext` 服务内部类型与 PRIVATE/builtin 专用授权适配后调用同一底层事务写入；不增加“跳过成员检查”的公共 boolean。

### 4.2 授权快照 Grant

拟新增不可变 grant revision，字段：`grantId`、issuerPrincipalRef、parentGrantRef、rootRequestId、scope、audienceRef、targetPrincipalRefs、allowedOperations、sourceSnapshotRefs、fileVersionRefs、delegationPolicy、revision、revokedAt。

- 根 grant 来自用户明确意图或既有授权。子 grant 的目标、操作和输入必须是父授权允许的子集；private 子请求仅能带父授权明确允许转交的内容。
- `delegationPolicy=NONE | NAMED_TARGETS`，不添加“所有 Agent”默认值。需要其他目标时创建待授权候选，不发送敏感 payload。
- Grant 不携带密钥、任意 API URL、磁盘路径或生产授权。源文件引用固定版本与摘要，输出引用也固定版本。
- 每次投递、输入读取、消息重放、成果查询/下载都重校验当前撤权状态。已下载至执行节点的字节无法凭服务器撤权收回；停止新访问并按受控取消流程结束工作，不承诺抹除对方已知信息。
- 现有授权足够时无需用户重复点击。授权变更、新增分享对象、风险范围变化才产生可见确认动作。

### 4.3 可见性与审计

| 对象 | 读权限 |
| --- | --- |
| 公议原文 | 原 conversation audience，不由 @扩展 |
| 用户密议 | 授权用户与唯一目标；宋江不是默认读者 |
| task-private | 密议参与者 ∩ 当前有效任务权限；其他成员无权 |
| Agent-directed thread | 同 owner/scope 下显式授权的 A/B 及授权用户；不继承整队读权限 |
| PRIVATE 执行/产物 | 对应执行 grant 的读者；“所属同一 task”不是读权限 |
| TASK 工作项成果 | 原任务合同与新增 audience 限制的交集；有意公开需用户确认 |
| 系统运维审计 | 授权运维的最小元数据，正文不进入宋江/其他 Agent 模型上下文 |

ACL 覆盖 list/count/search/context-pack/memory、SSE/live/replay、下载/预览、错误信息、推送标题和文件名；不可见资源统一 404，查询不得暴露私有对象存在。拒绝只靠前端过滤。

不把密议同步到共享模型记忆。Agent 模型会话缓存以 scope+conversation+grant revision 隔离；撤权/身份切换清理本客户端可控缓存。采用服务端访问隔离，不宣称端到端加密。

## 5. Agent 间通讯与客户端工具

### 5.1 两种协作，不混为一类

**问答**：A 提问 → B 回答 → A 获取回复。对话回复可以使用已授权模型，但不能通过对话队列获得 workspace 管理/构建权限。

**工作委托**：A 请求 B 测试、生成或处理输入 → 后端校验 → 创建具体 execution/work item → command.dispatch → B 执行 → 提交结果 → A 继续。A 不能直接下发服务器专属的 command.dispatch。

### 5.2 Agent 原生工具合同（拟新增）

| 工具 | 输入 | 输出 |
| --- | --- | --- |
| `collaboration.ask` | 当前请求内的 targetAgentId、question、允许转交的 inputRefs | requestId、state |
| `collaboration.reply` | replyToRequestId、content、已授权 outputRefs | replyId、持久收据 |
| `collaboration.delegate` | targetAgentId、operation、source/inputs、parentRequestId | 子 request/execution refs 或待授权候选 |
| `collaboration.status` | requestId | 仅有权读取的子状态、回复/成果固定引用 |
| `execution.report` | runner 产生的 progress/result/reportId | 服务端提交收据 |

工具由客户端 runtime 的 native adapter 提供，模型只能提出结构化工具参数。adapter 从当前运行上下文推导身份和 command/task/grant，携带仅内存保存的 runtime credential 调用精确 API。

不把 bearer token 放进 prompt、shell argv、文件 manifest、聊天历史或通用环境；不让模型自己 curl 任意 API。已有工具注册方式按客户端实际机制接线，工具可调用性需实际验收，不能只在 system prompt 描述这些名字。

native 请求失败将原 request/report ID 留在本地 outbox，查询/补交原请求；未经确认不得生成第二份工作。正在处理的命令仍遵守已有 Inbox 的 recovery-required 语义。

### 5.3 回声与重复响应防护

新增对话交互元数据（§6），明确 `QUESTION | REPLY | NOTICE`：

- QUESTION + 指定 responder 才创建一次回复处理任务，去重键为 scope/requestId/targetAgentId。
- REPLY 必须关联已有问题，幂等落库；不被广播转换成新 QUESTION。
- NOTICE 只更新观察状态，不唤醒模型、不产生构建命令。
- 已识别原发送者的广播不触发自回复；source 由服务器填，不能让客户端伪造以规避检查。
- A 的明确后续问题生成新 requestId，并保留 root/parent 关系；因果图拒绝自引用和循环引用，不设置无依据对话轮数或性能 deadline。

### 5.4 A 等待 B 时如何继续

- A 的 native 工具获得子 requestId，父工作项记录 WAITING_DEPENDENCY 与所需结果引用；不持有 Gradle、DB 事务或发布锁等待 B。
- B 完成后，结果事件在提交后唤醒 A；服务端按 parentRequestId + resultEventId 记录一次性继续意图。
- A 原运行仍活跃时，通过客户端 native tool 通知返回结果；不能把续办命令排到被 A 自己占住的同一队列后造成自锁。
- 若 A 已在安全检查点挂起，只有已有执行状态证明确实结束/让出资源，才用新的 continuation commandId + 固定原结果引用恢复；旧命令不得重新执行。未知崩溃先核对，不自动并发起第二个 A。
- 无法满足本机资源依赖时显示等待原因；不抢占其他任务、不用固定超时取消依赖。

## 6. 协议详细合同与兼容

### 6.1 版本和能力

保留顶层 `schemaVersion=1` 及现有 command/ACK 语义。拟新增能力标记：`jia.collaboration.v1`、`jia.execution-report.v1`、`jia.build-verify.v1`、`jia.output-stream.v1`。

能力由经过验证的客户端实现声明，服务端校验允许集并与注册身份绑定；不是角色 abilities 的营销标签。hello/registration 的可选能力字段须在两端 normalizer/schema 中显式支持。

未协商能力不发送其扩展帧；新要求显示 WAITING_CAPABILITY 或功能不可用，不转换成普通 chat 冒充执行。服务端已完成持久受理的请求等待原目标，不静默换节点。

### 6.2 基础 Envelope

| 字段 | 合同 |
| --- | --- |
| schemaVersion | 整数 1；拒绝类型错误、缺失的新协议请求 |
| messageType | canonical 类型；不以 legacy outer type 决定可执行性 |
| messageId | 传输消息 ID；ACK/report 自己有新 ID |
| commandId / commandType | command.dispatch 必填；业务幂等由 commandId+canonical payload fingerprint 保证 |
| sourceAgentId / targetAgentId | 发送者由连接推导；command 目标必填、精确匹配注册 Agent |
| correlationId / causationId | 关联请求/前序事件；ACK correlationId 指向原 dispatch messageId |
| conversationId / taskId / workItemId | 按消息域必填；PRIVATE namespace 不冒充正式任务；同 envelope/nested 声明冲突拒绝 |
| runtimeInstanceId | 当前运行实例；不能拿它代替任务/所有者 ID |
| payload | 版本化业务对象；禁止未知执行字段、任意身份覆盖、URL/路径注入 |

所有 ID 对外不透明字符串；数据库 BIGINT 和新增 revision/sequence/字节长度采用十进制字符串，避免 JS 精度损失。旧接口按自身冻结编码，不全局改 wire 类型。

### 6.3 定向聊天扩展示例（候选，不是当前可直接发送的请求）

下面 payload.collaboration 由服务器构造，source/target/grant 不能由未鉴权调用者自报。chat.message 内容不代表可执行工作。

```json
{
  "schemaVersion": 1,
  "messageType": "chat.message",
  "messageId": "msg-example-01",
  "sourceAgentId": "agent-a",
  "targetAgentId": "agent-b",
  "conversationId": "conversation-example-01",
  "correlationId": "request-example-01",
  "payload": {
    "content": "请说明这个测试失败的原因。",
    "collaboration": {
      "version": 1,
      "requestId": "request-example-01",
      "rootRequestId": "request-example-01",
      "replyToRequestId": null,
      "kind": "QUESTION",
      "requiresResponse": true,
      "grantId": "grant-example-01",
      "grantRevision": "1"
    }
  }
}
```

REPLY 必须有 replyToRequestId，requiresResponse=false。无扩展的旧 chat 保持原行为，但不得在新 Agent-directed 流程中自动降级使用。新接收者仍从持久 audience 计算，payload 不是 ACL。

### 6.4 构建执行与结果扩展

拟新增 `commandType=BUILD_VERIFY`，仍包在 command.dispatch 中。需要同时扩展常量、canonical codec、schema、writer authorization、consumer、Inbox fingerprint、客户端 allowlist/runner 和测试；不能只在字符串里写一个新 commandType。

其 payload 为 BuildVerificationSpec（§11），包含 PRIVATE/TASK executionRef、grant、固定源码、runnerPlanRef、输入引用。**不得把它混入现有精确 workspace file bridge payload**，也不依赖 prompt 指示执行哪个 shell。

通用回报采用 `work.progress` / `work.heartbeat` / `work.result` / `artifact.publish` 的受版本约束 payload。报告必须绑定 reportId、commandId、dispatch messageId、executionRef、grant revision、执行 attempt/fencing、runtimeInstanceId；全部由 native adapter 补齐/核验。

新增协商后的 `work.report.receipt`：只在数据库提交后返回 reportId、resultRef、committedVersion。复用现有专用 result receipt 的服务模式，但不改变技能结果既有 wire。

### 6.5 兼容与迁移规则

- 新协作请求只走已验证的 durable 路径；不走 Hall legacy 内存 mailbox 兜底。旧调用可保持原行为，界面不得将旧 delivered 当可靠交付。
- 同一 commandId 固定结果协议；客户端不能同时用 work.result 与 legacy task.report 双重推进业务终态。legacy 由受限 adapter 归一化，不创建另一套 outcome。
- 个人文件桥、技能安装、正式 task work item 原合同不变；新接口调用共用领域服务而非复刻状态机。
- 已保留的 `PRIVATE + WORKSPACE_FILE_EXECUTE` 是明确例外：D03 以声明输出的 manifest commit 表示成功，不发送通用 `work.result`。验收必须核对 owner 的 `OUTPUT_COMMITTED`、results manifest、受控文件版本和摘要；不得补造 legacy receipt。
- protocol.error 只记录失败，不能被处理为新工作。未知扩展返回能力/协议错误，不反复重发相同不兼容消息。

### 6.6 命令有效期与长任务等待

取材发现现有 canonical codec 对 TASK_INVITE/Hall command 使用固定一小时 TTL；这是当前实现约束，不是本需求长期离线/构建等待的授权依据。

新 BUILD_VERIFY 合同增加 `expiryPolicy=NO_BUSINESS_EXPIRY|EXPLICIT`：默认不设置业务过期；只有用户/既有授权明确指定有效期时，才携带 expiresAt。issuedAt 始终记录；不传播性能 SLO deadline、不把默认 TTL 改成另一个任意大数字。

实现要同步扩展该命令类型的 codec、DB expires_at 可空语义、outbox discovery/claim/consumer/recovery 与客户端最终执行检查：NO_BUSINESS_EXPIRY 的记录不走过期判定，旧类型继续原合同；已撤权/取消/身份失效仍不得开始。不得以“字段可空”让旧命令无意绕过到期检查。

命令的明确业务到期只约束尚未开始的授权启动；已开始的任务是否停止由原授权、用户取消、实际传输错误及任务状态决定，不能仅因投递 TTL 到点杀掉执行。若既有业务合同要求执行中到期停止，须明确展示并按该独立授权执行。

独立测试覆盖：离线等待超过旧默认 TTL 仍保留新请求、显式到期尚未开始不执行、长构建不因投递计时终止、旧命令到期语义不回归。

## 7. 关键时序

### 7.1 用户直接 @扈三娘执行

```text
1 用户选择扈三娘、会话和固定源码/输入，提交幂等请求。
2 API 解析当前用户和范围；固化 target/grant/执行规格。
3 事务写入 request + PRIVATE execution 或 TASK work item 绑定 + command/outbox。
4 返回 202 与稳定 requestId；未等待测试完成，不表示成功。
5 relay/consumer 将 command.dispatch 送至 Eva 精确注册连接。
6 Eva 持久 Inbox → RECEIVED → workspace/源码/工具核验 → STARTED。
7 runner 执行相关测试与构建，持久化日志/退出码与结果报告。
8 上传输出，提交 manifest/work.result；API 校验、提交、回 durable receipt。
9 原会话/请求事件更新，用户可读报告/下载制品；没有宋江推理或审批调用。
```

事务提交后响应丢失，用原 Idempotency-Key 查询；GET 暂时 404 不证明提交未发生，不换 key 再派。

### 7.2 用户密议宋江，由宋江委托

用户 → 宋江受限适配器；若原授权足够则建立子请求，只分享授权快照 → 同一服务派给 Eva → 子结果持久事件 → 受限唤醒宋江 → 在原密议汇总。

委托对象新增或需额外私密资料时，先保存待授权候选；确认前不向目标发送正文。宋江总结引用真实 resultRef，不把模型生成的“成功”当作报告。

### 7.3 Agent A 请求 Agent B

A native tool → 受限 internal request API → 验证 parent/grant/目标 → DIALOGUE 定向问题或 EXECUTION 命令 → B 回复/结果 → 原 parent 绑定事件 → A 续办。

两条路径均不需要宋江。A/B 不共享 token、不读取彼此工作树、不用聊天文本传 shell 命令冒充 server command。

## 8. API 详细合同（拟新增；旧 API 作为适配入口保留）

### 8.1 通用规则

- 浏览器/受权控制面前缀 `/agent/collaboration/v1`；仅 USER 或明确定义的受限控制面 principal。
- native 前缀 `/internal/agent/collaboration/v1`；仅当前注册的 AgentRuntime principal，拒绝 Origin、用户 JWT、重复/冲突身份头和不在 allowlist 的路径。
- 写操作携带 Idempotency-Key；同 scope+principal+操作+key+同 canonical 请求重放原资源；同 key 不同内容 409。所有隐私响应 `Cache-Control: private, no-store`。
- 校验 unknown fields、重复 JSON keys、标识规范、路径/body 绑定；大小和传输配置使用实际 schema/服务器能力，不复制历史任意阈值做发布门禁。
- 202 仅表示已持久受理，201 表示对象/上传阶段已创建，200 为查询/幂等回放；业务未成功不得返回“成功完成”。

### 8.2 用户/控制面接口

| Method / path（加用户前缀） | 请求 | 响应 / 行为 |
| --- | --- | --- |
| GET `/capabilities?conversationId=...` | 当前有权会话 | `{schemaVersion,targets:[{agentId,runtimeKind,connectionState,protocolFeatures,operationAvailability}],allowedActions}`；不暴露密钥/宿主路径 |
| POST `/requests` | RequestCreate + Idempotency-Key | 202 RequestView；NEEDS_INPUT/AUTHORIZATION 不产生下行命令 |
| GET `/requests/by-key` | 原 Idempotency-Key；无 body/query | 200 原 RequestView；404 不能作为重发依据 |
| GET `/requests/{requestId}` | 精确 ID | 200 RequestView，仅当前授权字段 |
| POST `/requests/{requestId}/authorizations` | `{expectedRevision,grantProposalId,confirmedSnapshotDigest}` + key | 200 新 revision；确认的是服务器保存的精确候选，不接受扩大范围字段 |
| POST `/requests/{requestId}/cancel` | `{expectedRevision,reason}` + key | 202 当前取消处理状态；不立即伪报 CANCELLED |
| GET `/requests/{requestId}/events` | Last-Event-ID 或 cursor，不能冲突 | SSE snapshot/live/replay；访问变化时停止输出旧范围事件 |
| GET `/requests/{requestId}/artifacts/{artifactId}/versions/{version}/content` | 固定版本 | 流式字节、长度和摘要；先校验结果归属和 ACL，再调用既有文件内容服务 |

RequestCreate（字段级候选）：

- `conversationId` 必填；`sourceMessageId` 可选，仅可引用当前用户在此会话的固定消息；`instruction` 为本次明确提交正文。两者同给时正文必须匹配选定快照，避免引用正文与执行正文分叉。
- `mode=DIALOGUE|EXECUTION|COORDINATION`；`targetAgentIds` 必填，去重后不能空；`taskRef` 可选且必须与会话关联规则匹配。
- `executionSpec`：EXECUTION 时为 §11 的固定规格或其他已支持的版本化任务规格；DIALOGUE 不接受执行字段。
- `inputRefs`：每项 `{fileId,fileVersion,sha256}`，服务端检查字节元数据和权限；不接受任意 URL/本地路径。
- `delegation`：`{policy:NONE|NAMED_TARGETS,targetAgentIds,operations,shareSnapshotRefs}`；默认 NONE，用户显式提交才可向子请求授权。
- 不接受 tenant/owner/sourceAgentId/runtimeId/callerRole/approvalBypass 等身份提升字段。

RequestView：`{schemaVersion,requestId,revision,mode,conversationId,state,targets:[{targetRequestId,agentId,state,deliveryRef,executionRef,resultRef,errorCode}],requiredAction,allowedActions,createdAt,updatedAt}`。state 是只读聚合，权威 execution/delivery 不从父视图写回；无权 target 信息不回传。

旧 `/chat/stream` 的消息历史继续复用；新版 Web 对办事请求调用新 request 入口。后端共同适配器维护 `sourceMessageId → requestId` 唯一关联，防止一条原文既走 stream 再走 request 被执行两次。原文未先持久化时，POST requests 在同事务写入一次聊天消息。

### 8.3 Agent native 接口

| Method / path（加 native 前缀） | 请求 | 响应 / 行为 |
| --- | --- | --- |
| POST `/requests` | `{parentRequestId,kind:QUESTION|DELEGATION,targetAgentId,content,executionSpec?,inputRefs}` + key | 202 子 RequestView；runtime 自身份和 grant 从 parent 派生；无权委托仅返回缺授权，不发送 |
| GET `/requests/{requestId}` | ID | 仅本人参与且被 grant 允许的状态/回复/结果引用 |
| POST `/requests/{requestId}/replies` | `{replyId,content,outputRefs}` + key | 201/200 持久 reply receipt；引用原请求且仅允许实际 responder |
| GET `/inbox?cursor=...` | 不透明绑定游标 | `{items,nextCursor,hasMore}`；定向对话/授权通知补收，不建立第二个 command claim 队列 |
| POST `/inbox/receipts` | `{deliveryId,messageId,status:RECEIVED|PROCESSED}` + key | 200 持久收据；PROCESSED 不等于执行成功 |
| POST `/commands/{commandId}/reports` | RuntimeReport + key | 200 ReportReceipt；与 WS report 共用领域处理 |
| GET `/commands/{commandId}/inputs/{inputRef}/content` | 已授权别名 | 流式固定版本输入；客户端看不到可替换下载 URL |
| POST `/commands/{commandId}/outputs/stages` | `{outputId,filename,mime,byteLength,sha256}` + key | 201 StageView，绑定当前执行/command/runtime 授权 |
| PUT `/commands/{commandId}/outputs/stages/{stageId}/content` | 原始文件流；声明长度/摘要与 stage 一致 | 200 verified StageView；重复相同字节幂等，不同字节409 |

RuntimeReport：`{reportId,dispatchMessageId,executionRef,grantRevision,attempt,fencingToken,sequence,kind,occurredAt,payload}`，kind 为 PROGRESS/HEARTBEAT/RESULT/ARTIFACT；runtime principal 不在 body 传入。RESULT payload 为 `{outcome,exitCode,testSummary,sourceEvidence,toolchainEvidence,outputStageRefs,manifestDigest,failureCode}`；§11 规定真实性校验。

ReportReceipt：`{reportId,committedVersion,resultRef,duplicate}`。HTTP 回执丢失可以用相同 key/报告重放；同 ID 不同语义拒绝。WS 新 receipt 指向同一个 resultRef。

输入/输出新流式通道在私有与任务模式下都调用既有文件/成果领域服务，物理 blob 不复制第二份；现有单输出文件桥保持原 API 不变。

### 8.4 错误、等待与恢复动作

| HTTP / 代码 | 意义 | 客户端动作 |
| --- | --- | --- |
| 400 INVALID_REQUEST / SCOPE_CONFLICT | 字段、类型、范围冲突 | 保留草稿并修正，不原样重试 |
| 401 AUTHENTICATION_REQUIRED | 凭据失效/无身份 | 走原登录/注册恢复，不从磁盘抓取其他凭据 |
| 403 OPERATION_NOT_ALLOWED | 已知本人资源但该操作不允许 | 展示边界；不得换 caller ID 绕过 |
| 404 RESOURCE_NOT_FOUND | 不存在或当前身份不可见 | 不泄露对象/成员存在 |
| 409 IDEMPOTENCY_CONFLICT / RESULT_CONFLICT | 同 key/报告内容冲突 | 原请求核对，不覆盖 |
| 412 REVISION_MISMATCH | 候选授权/取消 revision 过期 | 刷新当前状态，不能覆盖并发变更 |
| 422 CAPABILITY_UNSUPPORTED / EXECUTION_SPEC_INVALID | 合同/工具不支持 | 明确缺项；不降级聊天冒充执行 |
| 503 STORAGE_UNAVAILABLE / TRANSPORT_UNAVAILABLE | 真实基础设施错误 | 用原 ID/键核对并按原因恢复 |

WAITING_AGENT、WAITING_CAPABILITY、WAITING_DEPENDENCY、NEEDS_INPUT、NEEDS_AUTHORIZATION 是已受理对象的状态，不伪造 HTTP 成功业务结果。不可访问目标在受理前返回泛化错误；已授权目标离线可持久排队。

## 9. 状态机、幂等和恢复

### 9.1 三层状态不得混用

| 层 | 权威来源 | UI 含义 |
| --- | --- | --- |
| 投递 | 既有 command delivery/outbox/inbox/ACK | 已受理、待连接、已接收；只证明运输 |
| 执行 | PRIVATE execution 或 TASK work item/run | 执行中、等待依赖、失败、取消中、待核对 |
| 业务结果 | 持久结果与可验证 manifest/报告 | 测试/构建通过或失败；产物可用/不可用 |

新增 request 聚合候选状态：NEEDS_INPUT、NEEDS_AUTHORIZATION、ACCEPTED、WAITING_AGENT、WAITING_CAPABILITY、RUNNING、WAITING_DEPENDENCY、PARTIAL、COMPLETED、FAILED、CANCEL_REQUESTED、CANCELLED、RECONCILIATION_REQUIRED。这些是明确映射的视图/交互状态；实现不得将它们另存一份独立 execution 终态。Request revision 在其授权/响应/目标投影变化时单调增长，事件中的版本与读取快照同源。

### 9.2 原子受理

校验 scope 与幂等键 → 获取原任务/私有执行必要锁 → 固化 grant 与 request/目标绑定 → 写 execution 或 work item、command delivery/outbox → 写带 audience 的事件 → 提交 → 返回 202/发实时通知。

不能先发 WS 再补数据库。请求构造失败不得残留可投递命令；相同 sourceMessage/操作只关联一个根 request。遵守既有 task/member/runtime/delivery/outbox 锁顺序，新表锁顺序在下述事务合同中固定，避免反向锁。

### 9.3 原子完成

1. 上传阶段只保存 staging，不更新业务成功。
2. report handler 验证 canonical scope、原命令、current attempt/fence、实际 target、输入/输出绑定及 grant。
3. 同一事务记录 report Inbox、结果、manifest 精确引用、execution/work item 状态、私有/任务事件及续办意图。
4. 提交后发送 ReportReceipt。客户端 receipt 到达前保留原报告/结果 outbox；不能因为 ACK 已 SUCCEEDED 删除未提交结果。
5. RESULT 早于 ACK 可先接受合法结果，迟到 STARTED/ACK 不使终态倒退；同报告重复重放原 receipt。

### 9.4 断线、崩溃与取消

- WS 断线不取消工作；已有报告/通知补收独立恢复。当前 runtime credential 依注册流程更新，旧凭据不持久化重用。
- 重启后已持久完成但未回执的报告可对原 execution 核对补交；新 runtime 只有经服务端恢复绑定授权后才能提交旧结果，不把旧 runtimeId 字段改成新的冒充原进程。
- 执行中崩溃且副作用未知：沿用 recovery-required；同命令不自动重跑。新的 attempt 必须有恢复依据，保持来源和 fencing。
- 取消：owner/授权协调者发请求，客户端仅取消该任务拥有且允许控制的进程，保留证据；真正停止后提交取消结果。目标离线时显示 CANCEL_REQUESTED。完成与取消竞态按服务端版本/既有状态机核对，不伪造胜负或删除已提交产物。
- 传输重复投递可按原合同恢复；实际业务相同根因连续第二次失败且输入未变，记录 blocked_root_cause 并暂停本项，其他独立任务继续。
- 慢响应只记录，不传播会被强制执行的性能 deadline；保留明确传输超时、真实网络错误、用户取消与租约归属。没有证据不新增固定等待、磁盘、内存、包大小发布门禁。

### 9.5 SSE 与收件游标

新请求 SSE 复用已有 snapshot/live/replay/resync 服务模式：快照携带当前 revision 和本 scope 高水位，客户端先缓冲 live、再补持久事件、按事件 ID 去重；断线带最后提交游标恢复，身份/请求不同不接受复用游标。

原 task/scene 流各自保留原序列；请求流通过带 audience 的持久关联事件排序，不把多个无关流的数字 ID 直接混作全序。native inbox cursor 绑定 scope/agent/audience 与序列，只能补本人收件。前端用十进制字符串/BigInt 比较版本。

游标过期或历史不连续返回明确 resync，重新获取授权快照，不静默跳过事件。撤权后不再输出正文或私有元数据；如果已无请求读取权，以泛化不可见终止流。慢流采用已有可恢复背压机制，不以任意性能等待上限取消实际工作。

## 10. 数据、事务与迁移设计

### 10.1 复用优先

复用现有 ChatConversation/ChatMessage、task thread/request/work item、PersonalWorkspaceExecution、file/version/output、command delivery/outbox/inbox、既有 task/scene 事件和恢复机制。根 request 仅是跨聊天/私人执行/任务执行的关联与授权入口，不是第二个任务系统。

以下表名为逻辑候选，实施前按实际 schema 复核；只在对应字段/索引确实不存在时追加 migration。

| 对象/逻辑表 | 核心字段与约束 | 为什么需要 |
| --- | --- | --- |
| `agent_collaboration_request`（新增） | scope、requestId、root/parent、sourceMessageRef、conversationId、mode、callerPrincipalRef、grantRef、idempotencyKey/hash、revision、createdAt；scope+principal+key唯一，sourceMessage+operation 唯一 | 关联直达/协调/问答及原意图，不复制 execution 结果 |
| `agent_collaboration_target`（新增） | scope、requestId、targetRequestId、targetAgentId、deliveryRef、executionRef、taskRequestRef；request+target唯一 | 多 @逐目标绑定和恢复；状态从权威对象投影 |
| `agent_collaboration_grant`（新增） | scope、grantId、revision、issuer、parentGrant、操作/目标白名单、快照与固定版本 refs、revokedAt；grant+revision唯一 | 私聊分享与有限委托；不可变快照，撤销独立标记 |
| `chat_conversation_participant`（补充 ACL） | scope、conversationId、principalType/id、role、grantRef、revokedAt、version；conversation+principal唯一 | Agent-directed 显式参与者；不直接改 private 单目标语义 |
| `agent_conversation_delivery`（新增或复用合适的持久通知表） | scope、messageId、requestId、targetAgentId、cursor、receiptState；message+target唯一 | 聊天/问答离线补收；command 不在此重复排队 |
| `agent_execution_report_inbox`（新增或扩展现有 report Inbox） | scope、reportId、commandId、attempt、runtimeBindingRef、semanticHash、sequence、resultRef；scope+reportId唯一 | 结果/进度幂等和统一 HTTP/WS receipt |
| 原事件记录（扩展） | audienceKind/ref、sourceRequestRef、causationId、grantRevision | 阻断私密事件泄漏并支持恢复；不另开一个全局事件库 |
| 原 file/output/execution（扩展） | streaming stage refs、多输出 manifest、executionSpecVersion、runnerPlanRef、sourceEvidenceRef | 真实构建产物复用存储和 PRIVATE/TASK 状态 |

Grant 的目标/操作/文件集合第一版可用经严格 schema 校验的 canonical JSON 固化；主键/作用域/状态索引保持关系型。若授权查询实际需要成员逐行锁，则规范化为子表，不为未来假设先增加通用 ACL 平台。

### 10.2 索引与锁

- 所有唯一性和查询先带 canonical scope；ID byte-exact 比较，沿用现有 binary/长度校验，不让大小写/尾空格碰撞绕过身份。
- Request 查询索引 `(scope,principal,idempotency_key)`；子目标 `(scope,request_id,target_agent_id)`；收件 `(scope,target_agent_id,cursor)`；report `(scope,command_id,attempt,sequence)`；participant `(scope,conversation_id,principal)`。
- 输入只读元数据先解析，授权写入时重新确认 grant revision。正式任务路径保持既有 task→member→runtime→delivery→outbox 顺序；PRIVATE 保持 execution/grant→runtime→delivery→outbox。
- 新 request/grant 的争用在调用任务/执行事务前解析幂等身份；不得一处先锁 request 再 task、另一处先 task 再同一 request。实施合同统一为域根→request/grant→成员/运行态→消息/command/outbox；如现有域内固定顺序不允许插入，采用单一 owner transaction adapter 并以并发测试验证，不随意修改既有多处锁顺序。
- 文件流和网络发送不在数据库事务内；stage 封存后短事务挂接 manifest。报告并发/撤权并发须执行真实数据库事务回归。

### 10.3 迁移策略

1. 只读核验实际 schema 和现有表/索引，生成增量 DDL 候选；未经授权不执行生产迁移。
2. 新字段/table additive，旧读写保持原有合同；新类型 conversation 不会进入旧 team/private 不识别的查询。
3. 新功能 scope 内执行新事务路径；不双写两套权威 execution/result。旧记录通过兼容只读 adapter 展示，无法安全推导 ACL 的记录不公开。
4. 已有队列/DEAD/shadow 记录不会因开启新功能自动 reissue。新 request 有明确协议/激活标识，只放行本次新任务。
5. 安装保留可恢复产物与配置前值。新表数据保留，不通过删表/删 Inbox/替换 commandId 处理失败；遇到问题按精确证据修复。

## 11. Eva 测试/构建执行详细设计

### 11.1 环境准入是证据，不是固定资源门槛

实际核验：绑定 agentId/runtime、真实 hostname/architecture、客户端 source/deployed digest、受信 workspace policy、Git 来源、项目工具链、已用工作区与资源归属、相关测试依赖。

Eva 历史为 aarch64；JDK21 等版本依项目构建声明核实，缺少则提出精确安装清单，不直接复用本机 x86_64 native 依赖。保护 `/home/chc/wsps/cyf` 的既有脏文件，受信独立工作区由客户端 workspace manager 创建。

容量按实际源码、依赖、临时输出与保留产物计算；已有缓存去重计入。真实 ENOSPC/权限错误报告为环境阻塞，不能通过清理别的任务目录或假报成功推进。

### 11.2 BuildVerificationSpec（候选）

```json
{
  "specVersion": 1,
  "executionMode": "PRIVATE",
  "executionRef": "execution-example-01",
  "grantId": "grant-example-01",
  "grantRevision": "1",
  "components": [
    {
      "repositoryPolicyId": "cyf-api-trusted",
      "commitSha": "1111111111111111111111111111111111111111",
      "treeSha": "2222222222222222222222222222222222222222",
      "runnerPlanRef": "api-targeted-test-and-build-v1",
      "runnerPlanDigest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "testSelectors": ["selector-resolved-from-approved-plan"],
      "fixtureDigest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
  ],
  "inputRefs": [],
  "allowDeployment": false
}
```

样例 SHA/选择器仅示意，不是可执行候选。实际多个仓库分别固定 commit/tree；无 fixture 时为 null 并声明无需 fixture 的理由，不能伪造摘要。

repositoryPolicyId 由 Eva 本地受信策略解析 URL/root/baseline；消息不能替换这些路径。若固定基线尚未被受信仓库获取，先报告 NEEDS_SOURCE，不在其他目录构建“相近版本”。

### 11.3 确定性 runner

- 构建/测试不靠模型自主拼接 shell。新增客户端 build runner 从已核验版本的 runnerPlan 解析具体 argv、工作目录、环境白名单、选择器和产物位置；runnerPlan 的版本/摘要加入证据。
- 文本 instruction 仅解释目标，不能覆盖 argv 或注入 shell。允许选择器只能属于计划声明的可选项，未知项返回明确错误。
- Java/Gradle 先读项目最近 build.gradle，全部经该宿主项目 orchestrator 串行；Web 按项目声明执行相关测试及生产构建。保留测试失败，不为产出包而略过失败测试。
- 冻结 worktree 不接受并发代码写入；测试/build 的代码与脚本包括未跟踪输入都在输入 manifest 中。记录运行前后 tracked tree/差异，意外源变动使证据不匹配，不覆盖别人改动。
- 测试 DB/Rabbit 等使用本任务隔离 fixture，禁止默认连生产。现有授权模型调用与外部付费工具不同；本确定性构建 runner 不需要额外模型/付费 Provider 调用。
- 每阶段输出 `{stage,startedAt,finishedAt,exitCode,tests,logRef}`。是否通过由退出码、报告解析、必要产物和 exact source 共同判定；跳过和未运行分别报告。

### 11.4 多输出与传输

输出集合可以包括 stdout/stderr、JUnit/测试报告、构建包、source/toolchain manifest。复用现有 blob/file version 存储；新流式 stage 从受权路径写入受控临时文件或既有对象存储适配器，边读边计算长度/SHA-256，不把整包放 byte[] 或 JSON/base64。

- stage 绑定 scope/command/execution/output；不同 runtime 不能抢用上传位置。服务端生成受控存储名，客户端 filename 仅安全展示。
- 上传中断不封存产物；相同 stage 可重传，只有完全验证的字节原子替换 incomplete stage。不同摘要/长度拒绝，不覆盖已绑定成果。
- manifest 包含固定 outputId、sha256、byteLength、file/version refs 和执行身份；按既有规范排序/摘要算法处理已支持 manifest，新多输出扩展明确 version，不悄悄改变旧单输出算法。
- 结果提交事务绑定全部必要 verified outputs；下载实际再校验摘要/长度，界面只给已提交且可用的版本。
- 原产物损坏/缺失时，保留原执行成功历史和产物 UNAVAILABLE 状态，告知证据不完整；不能伪造可下载，更不能偷偷重建并替换原版本。
- 禁止任意外部 artifact URL/重定向下载和本地任意文件读取；输入、输出均用服务器派生的精确引用。

### 11.5 必须记录的证据

`requestId / commandId / executionId / runtimeInstanceId`、真实执行主机与 architecture、各组件 commit/tree、输入/fixture/runnerPlan digest、工具版本、各阶段退出码与测试统计、失败/跳过、产物 manifest 和 SHA-256、API 提交收据、下载核验、开始结束时间。

临时云效不可用且用户授权远端测试构建时记录 `build_origin=local_user_authorized`、`execution_host=Eva`；不产生虚构 Flow Run。正式发布与该构建验收分开；云效恢复后的权威证据按届时用户政策执行，不自动把 Eva 成功当发布许可。

## 12. 前端与控制面交互

### 12.1 聚义厅

- 发消息前展示范围徽标：公议/与 X 密议/事项 T 下密议；展示实际 responder chips 和独立“协调者”选择。
- @候选来自当前授权 roster；内置宋江使用单独 builtin 能力投影，不用放宽 `boundToMe` 假装远端；所有选中最后提交精确 ID。
- 发送后每个 target 卡片显示受理、待连接、执行中、等待输入/授权、失败、待核对、结果可用；不只显示总“已发送”。
- 私密分享确认只展示本次快照、文件版本和目标，默认不勾选整段历史；转事项/转草稿保留原会话。
- 结果页展示 source SHA、测试摘要、运行主机、可下载报告/制品及摘要；PARTIAL、SKIPPED、NOT_RUN、UNAVAILABLE 明确区分。
- browser 刷新/断线只读恢复原 requestId/key；取消只发对应取消请求。不同 owner/client/会话的草稿与 request refs 隔离，敏感正文不写全局 localStorage。
- 保留 map=/agent/map、roster=/agent/roster；不使用 /agent/active 作为聚义厅在线/权限事实。

### 12.2 当前开发控制面（F13）

提供三个受权操作的薄适配器：`submit_verification`、`get_request`、`fetch_artifact`，映射同一 USER/DEVELOPER_CONTROL API。输入包含明确 target、固定源码与计划，输出原 request/receipt/制品引用。

接入前验证已有身份系统能否签发并限制所需权限；若不能则列为实现缺口，不借用浏览器 cookie、从配置抓取用户 token 或伪装 AgentRuntime。密钥只在既有受控凭据存储内，不进入 prompt、代码仓库、工具参数回显或报告。

控制面没有工具/授权时，产品已登录入口仍可验收；但 F13 保持未完成。不能把本地 spawn_agent 命名为 Eva 就报告远端派发成功。先验产品和真实节点，再验证研发控制面的一次实际提交与回收。

## 13. 可观测性与用户通知

- 关联链：rootRequest → targetRequest → task/work item 或 PRIVATE execution → command → dispatch → report → output manifest。
- 记录持久化受理、消息投递、ACK、runner阶段、结果提交、下载验证各自时间；延迟用于排障，不把慢请求当业务失败。
- 脱敏日志包含稳定错误码与 scope 的受控标识，不含聊天正文、文件内容、授权头和密钥。任务/会话标题本身可能敏感，默认不进公共日志。
- 用户通知触发：有结果、真实失败、需要补输入/授权/环境措施、状态从等待变可执行。状态不变不反复通知；通知只给该 audience。
- 无关运维/任务冲突 alert-only，交由确切 Owner 处理；协调线程不操作他人进程或证据目录。

## 14. 实施分包与路径所有权

以下是计划，不是运行 ledger；未创建实际 Owner、worktree 或任务。执行时唯一 ledger 仍由 `/home/isp/wsps/cyf/docs/implementation/TASKS.yaml#runtime_ledger_json` 管理，字段按既有政策，不在本文件滚动维护运行状态。

| 包 | 覆盖功能 | Owner 配置/范围 | 依赖 | 交付 |
| --- | --- | --- | --- | --- |
| D00 现场基线与合同核对 | F10/F14 | 集成协调只读 | 无 | actual API/client/schema/scope/capabilities，差异清单 |
| D01 路由、scope、授权与入口事务 | F01–F03 | critical_worker；API/chat/agent 指定路径 | D00 | Request/grant/私有执行适配、接口与数据库回归 |
| D02 通用回报与可靠运输接线 | F08/F09 | critical_worker；同 API Owner 统筹，避免与 D01 同文件并写 | D01 合同 | report/receipt、durable聊天、replay/fencing/取消 |
| D03 runtime 工具与协议 | F05/F07/F09 | 客户端 Owner；isp-install 独立 worktree | D01/D02 冻结合同 | native工具、能力协商、持久请求/结果恢复 |
| D04 宋江协调 | F04 | API Owner；Builtin/AgentTools 范围 | D01/D02 | 受限 principal、授权委托、异步汇总 |
| D05 Agent 双向协作 | F05/F06 | API/客户端各自 Owner | D01–D03 | 问答、委托、依赖续办、两真实 runtime 验收 |
| D06 Eva runner/多输出 | F10/F11 | 客户端 Owner + API 输出适配 | D01–D03 与环境授权 | 确定性执行、多产物 stream/manifest、真实构建证据 |
| D07 聚义厅交互 | F01/F02/F12 | balanced_worker；Web 独立 worktree | D01 的 UI/API 状态合同 | @/密议/执行卡片/结果恢复、UI 测试 |
| D08 开发控制面 | F13 | 集成工具 Owner | D01/D02、身份授权方案 | 三个受限操作、真实提交与下载 |
| D09 组合验收与规范 | F14 | gpt_test_runner 协调验证 + 原 Owner 自检 | 所有相关包 | §16 全量证据及规范更新 |

研发 Owner 与远端业务 Agent 是两套身份：研发分工用本地 Worker 不证明 Eva 执行。无独立 Reviewer，不因旧审查队列阻断；身份/ACL/事务/迁移风险由责任 Owner 明确自检并补相关回归。

可并行：D03、D07 在 D01 合同后分别写客户端与 Web；D04/D05/D06 避免共享 API 文件并写。依赖表达工作前置，不是全局源码单队列；Gradle 在每个宿主经 orchestrator 串行，不抢占其他任务资源。

不承诺无证据固定工期。D00 后按实际差异调整实现范围，D01 完成后根据真实吞吐更新剩余排期；现有可复用源码不是“零成本已上线”。

## 15. 激活与验收推进顺序

1. **仅基线核验**：脱敏版本、身份、协议、有效开关、DB/Rabbit 结构及历史积压；只读操作不创建 Reviewer。
2. **兼容能力部署准备**：三仓候选自检、冻结 exact SHA/tree；先发布能理解协议而未派新工作的服务/客户端，实际运行变更另按授权执行。
3. **精确新请求激活**：只允许当前 owner/client/tenant 与指定目标的新 root request；不更改全局默认、不释放历史命令；配置保存前值、固定哈希、readback。
4. **直达和密议探针**：先 @扈三娘，再密议扈三娘；证明确实无宋江中转、有 command/receipt/结果和 ACL。
5. **宋江与双 Agent**：内置宋江到 Eva、到第二真实 Agent；Eva 与第二 Agent 双向问答/委托；期间可并行准备 Eva 构建工具链。
6. **真实相关测试与构建**：前端、后端分别绑定 exact source/fixture；每一项均有真实退出码、报告、产物校验。无 Java/空间/网络按精确原因处理，不假报通过。
7. **恢复、失败、隐私验收**：故障注入先在隔离环境；线上不停止其他任务、不得以固定 SLO 拒绝下一步。
8. **控制面验证与规范固化**：当前研发入口一次真实派发/回收后，按证据更新 runbook/MODEL_ROUTING/AGENTS 必要条款；失败不静默回本机。

发布基础仍沿用户最新授权：Flow 不可用的临时例外下自检合 develop、验证 exact SHA 后冻结 release 分支；保留版本发布时间、进程归属、互斥、健康与可恢复安装。通讯验收不自动部署所生成的业务包，不新建重复流水线，不推导付费/生产数据权限。

停止某项推进的依据仅限真实错误、必要授权缺失、目标/制品/身份不匹配、资源归属冲突及明确业务依赖；修复和有证据的新候选可继续，不把历史失败变永久门槛。

## 16. 验收矩阵与完成定义

全部为待执行用例；“现有单测通过”“文档校验通过”与本表真实业务验收分开记录。

| ID | 关联功能 | 场景 / 验收要求 | 必需证据 |
| --- | --- | --- | --- |
| AT01 | F01 | 公议 @扈三娘直接到 Eva，无宋江推理/派工调用 | 路由决策、target、runtime、回复 |
| AT02 | F01 | 同名角色/多个实例按精确 ID 选择；不按昵称误发 | 两实例夹具、错误与选择记录 |
| AT03 | F01/F12 | @多个目标独立投递/部分完成；无自动协调 | 各 targetRequest 状态 |
| AT04 | F02 | 与 Eva 密议执行，结果只回原私有范围 | 会话/执行/结果 ACL、实际返回 |
| AT05 | F02 | 普通密议和事项密议切换不串历史/草稿 | API scope 与浏览器恢复用例 |
| AT06 | F02 | 密议 @第三方需分享候选；未确认零正文投递 | server outbox/目标收件为空 |
| AT07 | F02/F04 | 宋江非授权时不能读取密议、标题、产物、SSE、检索 | API/list/search/context/memory/download 负例 |
| AT08 | F03 | 聊天不触发 build；明确执行进入 command 队列 | chat/command 类型与进程证据 |
| AT09 | F03/F09 | 原消息 stream/request 双入口不重复办事 | sourceMessage 唯一绑定、执行次数 |
| AT10 | F04 | 宋江有限委托与异步汇总，浏览器关闭仍完成 | grant、子请求、持久唤醒、resultRef |
| AT11 | F05/F07 | 两真实 Agent A→B 提问并收到关联回复，反向也成功 | 双端 runtime、request/reply IDs |
| AT12 | F05/F09 | NOTICE/自广播/重复回复不触发回声或额外模型工作 | 消息去重与工具调用计数 |
| AT13 | F06 | A 委托 B，B 交付后 A 消费固定结果继续 | parent/child、输出版本、续办事件 |
| AT14 | F06 | 未授权目标/额外资料/跨 owner 委托拒绝且不泄漏 | grant 子集负例、双用户双 client 夹具 |
| AT15 | F07 | runtime 不能访问 USER API/任意 internal 路径；伪身份失败 | filter/controller/领域联合测试 |
| AT16 | F07/F14 | 旧客户端能力不足真实展示，不降级假执行 | 握手能力和拒绝/等待证据 |
| AT17 | F08 | 进度、结果/失败在 API 持久，HTTP/WS 统一同一结果 | reportId/resultRef、事务记录 |
| AT18 | F08/F09 | RESULT 早于 ACK、乱序进度不倒退终态 | 状态版本、重复响应 |
| AT19 | F09 | 同 key/command 同内容重放；不同内容冲突不覆盖 | 唯一约束、运行次数 |
| AT20 | F09 | 完成后回执丢失、重连只补结果不重跑 | durable outbox、receipt、进程次数 |
| AT21 | F09 | 执行中崩溃进入待核对，旧 runtime/fence 不能抢报 | recovery 状态、恢复授权 |
| AT22 | F09 | 取消与完成竞态、离线取消，不误杀其他任务 | 进程归属和结果版本 |
| AT23 | F10 | Eva 工具链/受信 worktree/架构/源码准确且不污染脏树 | before/after、policy、source SHA |
| AT24 | F10/F11 | 真实前端相关测试+构建 | 命令、退出码、报告、制品 digest |
| AT25 | F10/F11 | 真实后端相关测试+构建，Gradle 经 orchestrator | 同上及串行/fixture 证据 |
| AT26 | F11 | 多报告/制品上传中断恢复，下载字节摘要一致 | stage/manifest/下载 hash |
| AT27 | F11 | 测试失败/跳过、产物丢失/不匹配不能显示完整成功 | 失败夹具、状态/报告 |
| AT28 | F02/F09 | 撤权后输入/事件重放/下载受限，已下载边界如实说明 | revoke revision、负例 |
| AT29 | F12 | 刷新/登录身份切换恢复正确私有请求，不串结果 | 前端+真实 HTTP/SSE 集成 |
| AT30 | F13 | 当前开发控制面真实派给 Eva 并下载校验结果 | 工具调用、API receipt、runtime、hash |
| AT31 | F14 | 新 scope 激活不派出历史 shadow/dead/积压旧命令 | 激活前后队列核对 |
| AT32 | F09/F14 | 慢请求继续等待、新命令不套旧固定 TTL；同根因二次失败不盲重跑 | 时间观测、有效期兼容、错误归因、下一动作 |

单元测试覆盖路由/意图/schema/状态机；集成测试覆盖 MySQL 事务、Rabbit/WS、native filter 与产物存储；浏览器测试使用真实 HTTP→SSE 边界；双 Agent/Eva 实测单独保存证据。不得用 mock 替代第二真实 Agent 或 Eva 构建。

证据目录在实际 Owner 执行时创建，按 task/worktree 隔离；索引包含 source commit/tree、客户端 deployed hash、选择器、fixture digest、报告、产物、激活 scope、在线核验与未验收项。不读取/覆盖其他线程的私有证据。

**完成定义**：F01–F14 均有对应 AT 证据；直接路由、密议、宋江委托、双 Agent 协作、Eva 前后端相关测试构建、结果恢复、开发控制面全部实测通过，才能宣布本需求打通并将 Eva 路由定义为后续规范。仅部分通过则逐项报告，不标整个 feature accepted/released。

## 17. 实施前决策清单（不得用猜测填成“已就绪”）

| 编号 | 尚需现场确认 | 已选设计 / 缺少时动作 |
| --- | --- | --- |
| Q01 | 线上 API/客户端与本地源码差异、effective scope 开关 | D00 只读核验，不凭默认值推断 |
| Q02 | 第二个真实 Agent 的 ID、绑定与可用能力 | 使用用户已有授权节点，不创建假节点；缺少则 AT11/13 未验收 |
| Q03 | Eva Java/工具链、受信 policy、实际容量与输入来源 | 按 §11 核实；必要安装/清理精确授权后实施 |
| Q04 | 当前身份系统可用的开发控制面授权 | 用既有身份签发/权限扩展，不复用他人凭据 |
| Q05 | 新表与现有 schema 能否复用、数据迁移实际范围 | 按 §10 差异化最小 DDL，测试后按授权安装 |
| Q06 | 实际 artifact 存储流式接口、manifest 算法和文件桥兼容 | 复用物理存储，版本化扩展多输出；不打破旧单输出合同 |
| Q07 | builtin actor/PRIVATE execution 在 canonical writer 的授权适配点 | 专门 principal/域适配，不放宽通用 owned-Agent 校验 |

这些决定不影响确认用户行为目标；只有涉及真实实现/环境差异的条目在 D00 收敛后，本文才可与对应 spec/tasks/acceptance 的增量一起进入 ready。没有上线时间或环境安装的隐含承诺。

## 附录 A. 相关文档与当前代码入口

- 原方案：`/home/isp/wsps/cyf/specs/juyiting-task-collaboration/connectivity-plan-20260922.md`
- SDD 源入口：`/home/isp/wsps/cyf/specs/juyiting-task-collaboration/design.md`
- 原协作架构：`/home/isp/wsps/cyf/docs/juyiting-multi-agent-collaboration-design.md`
- 聚义厅运行指南：`/home/isp/wsps/cyf/docs/juyiting-runbook.md`
- 新版体验合同：`/home/isp/wsps/cyf/specs/juyiting-unified-experience/design.md`
- 客户端规范：`/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/README.md`
- Eva 历史证据说明：`/home/isp/wsps/cyf/docs/implementation/handoffs/JYT-UX-EVA-PREFLIGHT-20260921.md`

附录 B 仅记录这次设计取材文件，使用绝对路径与实际字节摘要。目录下可能有既存未提交改动，因此 HEAD/tree 是仓库提交参照，不代表本次整个工作区洁净、实现已验证或线上已部署。

## 附录 B. 设计取材快照

| 仓库 | HEAD | 提交 tree |
| --- | --- | --- |
| `/home/isp/wsps/cyf/api` | `fd47b1086ee5466571c2f810948f1541ae452fdf` | `419d0da055539278fe9d495677acb4e84798f285` |
| `/home/isp/wsps/cyf/web` | `c567e0593bd0334a4f6d47536e235fc1c3af7bb5` | `cf2745557e8c9a3152d9db744cc2917b965b76d2` |
| `/home/isp/wsps/chcbz/isp-install` | `c5b1ea43f8a54599d38b08d377d1f6f53f76b18b` | `36e27d3fab582dc8617780e364cedfdbbd4af527` |

| 已读取源文件 | SHA-256 |
| --- | --- |
| `/home/isp/wsps/cyf/web/src/composables/juyiting/useHallChatContext.js` | `1128921a780474fc6425332c2054c4d13e16a705b32af5394cdd65d64a4a7904` |
| `/home/isp/wsps/cyf/web/src/composables/juyiting/useHallConversation.js` | `485b3d80a47b0d36012bfdd8b15f1e44c62717d357a6b871f989b2f5cd0031a2` |
| `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/JuyitingAgentRelayService.java` | `485016acbcaaa982b8713daabe03cf919c553f04a2443697a04787695035df4f` |
| `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/JuyitingConversationScopeService.java` | `9d3ac0e19fdc721ddcef05cb534bb3b64492dfaad236911d40a06c23246fb8bb` |
| `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/HallActionDispatcher.java` | `f629f58a0835eeb9125840d70ca2dd546e365fa986dad03f6e600d91d3603220` |
| `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/handler/AgentWebSocketHandler.java` | `e498d266858636faef33b32c2bd0bb51c6f93f1f52da50ec83158fa766c1c04b` |
| `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/impl/AgentTaskThreadServiceImpl.java` | `33768b0555136a9f28d7231b709aa66b8a65cc79c81cb7c58b5b14f6f549af95` |
| `/home/isp/wsps/cyf/api/agent/jia-agent-core/src/main/java/cn/jia/agent/entity/PersonalWorkspaceExecutionEntity.java` | `01cf0fa7ffb3f3cb1c5642a938611d996e1b80d25fabf39bd9f776cf02e0a998` |
| `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceRuntimeFileController.java` | `9d749634d8446b65790709eebc25c7c5c3fe840486fe1ed96935d6ab84c1ac41` |
| `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/security/AgentRuntimeAuthenticationFilter.java` | `6032b917dff653d5a95781c11edbfa9edc0cc3b7f8c0275144939b83d77ef9d5` |
| `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/agent-client.mjs` | `2c481210ff317ff80b670d42e6781e9ded7879a4e60da97e58a437ee8f3dcd16` |
| `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/README.md` | `e97e753dbe07ae286cac7d1ae1a4c483720a35c92a568a3669a401cb457ca820` |

本次仅执行文档结构、引用存在性、JSON 示例语法与需求/验收对应检查；未编译 API/Web/客户端、未启动 Agent 或构建、未修改 DB/配置/运行台账。
