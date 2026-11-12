# 宋江与远端 Agent 通讯、协作执行打通方案

日期：2026-09-22（Asia/Shanghai）
状态：方案草案；仅新增设计文档，未派发实现、未修改运行配置、未启动测试/构建/部署。
归属：既有 `juyiting-task-collaboration` SDD 的补充方案，不重写冻结合同，不建立第二份运行台账。

## 1. 目标与验收边界

让用户在聚义厅交给宋江的工作，能由后端可靠派给明确的远端 Agent；同一授权任务内的 Agent 能提问、协商、请求帮助、委托工作和回传成果。首个真实执行节点为 Eva 上的扈三娘 `jyt-jiafewnnv58ec2379c-husanniang`。

最终示例：用户要求测试/构建 → 宋江创建任务并选择扈三娘 → Eva 在受信隔离工作区执行精确源码 → 上传日志/测试报告/制品 → 服务端核验并落库 → 宋江汇总真实结果。第二个真实 Agent 必须另外验证双向通讯；不能把给多个 Agent 群发一条消息当作 Agent 间协作。

首轮不部署业务产物、不调用付费 Provider、不操作生产数据、不重启其他任务进程。环境安装、清理、身份迁移等另列精确目标与授权，不从“打通通讯”推导无限运维权限。

## 2. 已知事实与待核事项

本次读取的是本地工作区，不是线上制品；工作区有既存改动。读取时 HEAD：API `fd47b1086ee5466571c2f810948f1541ae452fdf`、Web `c567e0593bd0334a4f6d47536e235fc1c3af7bb5`、isp-install `c5b1ea43f8a54599d38b08d377d1f6f53f76b18b`。这些 SHA 不能替代后续冻结候选 tree/部署证据。

| 现有能力/证据 | 本次结论 |
| --- | --- |
| `BuiltinHallAgentSupport`、`ChatClientConfig`、`AgentTools` | 宋江是后端内置角色，已有 Agent 查询/任务工具接线；不需要额外 WS runtime 才能协调。内置“online”不等于远端执行可用。 |
| `JuyitingAgentRelayService`、`AgentWebSocketHandler` | 有用户到指定 Agent 的聊天、授权会话内回复广播；需核对客户端实际消费、持久化及断线补收，不能直接宣称双向自主协作已完成。 |
| `JuyitingActionController`、`HallActionDispatcher` | 已有动作派发入口与旧链路兼容分支；OFF/非派发 scope 不一定完全不能投递，故“默认关闭=没有任何执行通路”不成立。 |
| Outbox/Inbox、Rabbit consumer、ACK、租约和恢复服务 | 已有实现，优先复用；需核对部署版本、有效开关、schema、真实作用域及最后一公里。 |
| 通用 WS `work.result/progress/heartbeat/help.request/artifact.publish` | 当前通用分支仍有 `PROTOCOL_HANDLER_NOT_AVAILABLE`；技能/个人工作空间等专用途径另有处理，不能混为通用闭环已完成或完全不存在。 |
| 生产 properties 的 command/Rabbit 默认 false | 仅证明仓库默认值；未核验启动参数、环境覆盖或线上实际状态。 |
| 2026-09-21 Eva A3 | 私聊回复持久化，Agent 自报 Eva/aarch64 与只读命令结果；没有 command.dispatch 构建、可信 workspace、Java 或制品回传验收。 |

特别核查：现有 Hall 派发要求 caller/target 是可写任务成员且满足 owner 下 Agent 身份校验。宋江内置身份如何合法代表用户、命令路径与聊天路径如何映射 tenant/owner，必须明确；不能直接传 `callerAgentId=songjiang` 或伪造 runtime 绕过校验。

## 3. 目标架构：后端中转，不建设 Agent 间直连网

```text
用户 / 聚义厅（以及后续已鉴权的开发控制面）
           ↓ 同一任务服务、同一身份校验
宋江：后端协调适配器（代表当前用户，受 task/操作授权约束）
           ↓ 结构化意图 / 任务工作项
协作领域服务 → MySQL（任务、消息、事件、结果、Outbox/Inbox）
           ↓ 已提交的命令
Outbox → RabbitMQ → WS Gateway → 扈三娘/Eva 或其他 Agent
           ↑ ACK / 进度 / 求助 / 结果 / 可核验的产物引用
           └──── 持久化、去重、状态推进 → SSE/消息通知 → 宋江/用户
```

Agent A → API → Agent B 复用同一条链路；不共享 Agent 凭据、不要求 SSH 互通、不让 Agent 向另一个 Agent 直接发送可执行 `command.dispatch`。Agent 提交协作请求，服务器校验后产生下行命令。

### 3.1 三类消息必须分清

1. **对话**：提问、回复、讨论，持久化后通知指定收件人；收到通知不自动变成工作执行，也不因广播让所有 Agent 自动回复。私聊不泄漏到团队。
2. **命令**：结构化派工，由服务器产生 `command.dispatch`，显式 target/task/work item；只有该类型进入受信执行队列。
3. **事件/结果**：接收、开始、进度、阻塞、结束、成果，是已发生事实；不把事件重新当成命令。ACK 成功不替代测试/成果验收。

协作消息在已有协议上增加必要的版本化语义：消息 ID、关联/因果 ID、发送者、目标、task、thread、消息种类与 replyTo。字段名称和存储复用在合同冻结时确认；不在此宣布新接口已经实现。发言身份从受信连接或服务端授权推导，模型提交的 source/owner 字段不是身份凭证。

### 3.2 宋江的协调身份

- 保留内置宋江，增加受限的服务端协调适配器：身份来源为已鉴权用户，记录实际 operator、代表角色、task 和目标 Agent。
- 内置协调者与远端 runtime 使用不同 principal 类型；不创建假 API Key、不放宽所有 Agent 的成员校验。必要的任务协调者授权变更单独自检和回归。
- 复用/补齐 AgentTools：查能力、创建任务与工作项、指定目标派发、查看进展、读取成果、发送协作请求。异步完成以持久事件唤醒，不依赖用户浏览器一直连接。
- 同一完成事件重复投递不能重复汇总、重复派工。模型建议先经领域服务验证，不能靠提示词保证权限或幂等。
- 宋江展示“内置协调服务可用”；远端展示已连接/忙碌/离线、实际执行能力及阻塞原因，不用一个 online 状态替代所有能力。

### 3.3 通用回报与可靠性

- 补齐通用进度、心跳、求助、结果、成果处理，复用既有租约、工作项、文件/产物服务；WS 与受控 runtime HTTP 入口调用同一领域服务，不维护两份终态。
- 若复用个人工作空间文件桥，必须满足它现有的精确 manifest payload 合同；不能随意混入字段使其落入普通执行分支。编码 workspace 与文件桥如何衔接需形成显式版本合同。
- 接收方先持久化再 ACK；服务端结果提交后返回可重放收据。断线按 cursor/Inbox/结果 outbox 恢复；结果先于 ACK、重复/迟到回报不能倒退状态。
- 投递状态、执行状态、业务验收状态分开。界面语义至少区分：已受理、待连接、已接收、执行中、待核对、成功、失败、已取消；具体枚举映射既有状态机，不另造平行事实源。
- 断线或执行崩溃后先核对原命令与实际副作用，不自动重跑未知结果命令。重复 commandId 不重复执行；同 ID 不同业务内容拒绝覆盖。
- 同根因、输入未变的第二次连续失败停止盲目重试，记录 blocked_root_cause；只暂停该工作项，其他独立工作可推进。
- 性能慢只记录与优化，不因任意 1s/3s/5s 门槛拒绝协作。保持实际传输错误、明确配置的传输超时、用户取消和租约/fencing；租约失效不授权抢占或杀掉其他任务进程。

### 3.4 Agent 间协作

- 同一授权 task 内支持 A 向 B 发出指定收件人的问题或工作请求；B 可回复 A，结果仅对该消息/成果的授权接收者可见；宋江和任务成员身份本身不授予密议读取权限。
- 普通成员可提交求助；只有获得相应委托授权的 principal 可派生执行命令。默认不开放跨租户/跨 owner 任意通讯；外部邀请沿用既有明确邀请合同。
- 根请求、因果链和已处理事件 ID 用于去重、防止消息环路；通知不自动触发再次派工。用户可取消对应请求，不以任意轮数/耗时限制代替正确的事件语义。
- 第二个 Agent 的结果可被第一个 Agent 作为显式输入继续处理，固定产物版本与授权，不读取对方整个工作目录。

### 3.5 密议：可直接办事，不强制经过宋江

密议是同一协作基础设施上的独立访问范围，不是公议的显示过滤。复用传输不等于共享上下文。

| 场景 | 路由 | 默认业务可见范围 |
| --- | --- | --- |
| 用户与扈三娘密议 | 用户 → API 私人会话 → Eva → 原会话 | 当前用户、指定扈三娘；不抄送宋江或其他 Agent |
| 用户与宋江密议 | 用户 → 内置协调适配器 → 原会话 | 当前用户、宋江；不自动分发给其他 Agent |
| 关联事项的密议 | 用户 → task 下独立 private thread → 指定 Agent | 密议参与者且仍有相应任务权限；其他任务成员不能凭成员身份阅读 |
| Agent A 与 B 定向私下协作 | A → API 校验授权 → 独立定向线程 → B | 授权参与者；不得由 A 私自把用户密议历史加入此线程 |

- 普通密议不要求公开悬赏或团队任务。用户明确要求执行时，由后端创建/关联私有执行记录与必要内部 task/work item，再产生 command.dispatch；私有执行必须有独立 ACL，不能借用默认对整队可见的 task 容器。
- 现有 private 会话限定一个目标 Agent。A/B 的协作线程属于需要冻结的新参与者合同，不直接把 private 的 targetAgentIds 放宽为多个。跨用户场景另走明确邀请与授权。
- 与扈三娘密议时可以直接说“在 Eva 测试这一版本”，无需先找宋江；继承执行授权边界、受信 workspace、exact SHA 和证据要求。聊天消息本身仍不直接触发构建；受控意图转换产生结构化命令。
- 与宋江密议时，宋江可规划，但要委托其他 Agent，必须明确目标、指令和允许分享的输入。用户已明确要求“交给扈三娘测试”可作为该范围授权；若要分享额外私聊历史或资料，则需再确认，不把既有授权扩大。
- 普通密议和事项密议使用不同 conversationId/scopeKey；界面切换事项不迁移旧历史或未发送内容。转公议/团队任务/草稿需选择并确认内容快照和分享范围，不复制整个密议。
- 执行结果、日志、报告、制品下载、通知、SSE/replay、搜索和记忆检索都继承私有范围；公共时间线不得泄露密议正文、标题、文件名或私有任务存在。必要运维审计仅向有权运维者暴露最小元数据，不自动进入宋江的模型上下文。
- 收件范围从持久化 ACL 推导，不能信任消息 payload 的 participants；撤权、历史补收和文件下载均重新校验。不能只靠前端隐藏按钮或消息卡片。
- 本方案的“密议”指应用层访问隔离，不承诺服务器不可读或端到端加密；若需要后者，另行设计密钥与模型处理边界。

密议专项验收：直接私派 Eva 并回收结果；宋江/其他成员无法列出或读取其正文与产物；切换普通/事项密议不串上下文；委托仅分享授权快照；撤权后订阅、重放与下载均受限。以上纳入 P1/P2 的 API/客户端测试及 P4 的 UI 验收，不待后续再补隐私边界。

### 3.6 显式 @Agent：定向路由，不强制经过宋江

- 用户明确 @某 Agent 时，后端把经当前会话权限校验的目标作为收件人，直接路由到该 Agent；宋江不是默认中转、审批者或兜底代答者。只有 @宋江、明确委托宋江或用户主动使用协调入口，才进入宋江协调路径。
- @是收件人选择，不是授权扩展或任意执行指令。普通问题走 chat.message；明确的办事请求经同一受控意图转换、任务权限与 workspace 校验后走 command.dispatch，无需宋江批准。
- @多个 Agent 时，对每个获授权目标独立投递、报告送达/执行结果；不因群发自动建立主从调度，不假设一个回复代表所有目标完成。需要分工协调时由用户明确委托。
- 私有会话的固定收件范围优先于文本 @：密议中 @第三方不能直接把历史或附件发出去，应提供新建定向会话/确认分享快照的明确操作；已明确授权的委托仅携带必要输入。
- 公议中的 @只选择被请求响应的 Agent，不改变该公议本身的可见范围。宋江若原本是授权参与者，可按既有 ACL 阅读公议，但不会因此成为执行中转；想私密沟通需进入密议。
- 未绑定、无权限、目标不明确或离线须返回真实状态；仅对合法且支持持久投递的请求排队。不静默换成宋江、其他 Agent 或本机子 Agent。

专项验收：@扈三娘直接到 Eva，调用链无额外宋江推理/审批；多目标分别显示结果；同名角色按明确 Agent ID 路由；密议 @第三方不泄露历史；公议 @不被误标私密；离线不静默改派。

## 4. 实施顺序与交付包

以下为待派发工作包，不是当前运行状态。启动实施后通过 orchestrator 登记唯一台账，Owner 自检，无独立 Reviewer。

| 包 | 范围/责任 | 依赖 | 完成判据 |
| --- | --- | --- | --- |
| P0 基线核验 | 集成 Owner，只读 | 无 | 对齐线上 API/客户端版本、有效配置、scope、schema/队列状态、Eva 注册身份与能力；冻结协议差异清单。 |
| P1 纵向最小闭环 | API Owner + 客户端 Owner，各自路径 | P0 | 宋江受限 principal → 工作项 → 持久 command.dispatch → Eva 接收/执行只读探针 → 通用结果落库 → 宋江汇总。 |
| P2 双 Agent 通讯 | API/客户端 Owner | P1 合同 | 宋江↔Eva、宋江↔第二真实 Agent、Eva↔第二 Agent 的定向问答/求助/委托；验证断线补收与不重复执行。 |
| P3 Eva 测试构建 | 客户端/验证 Owner | P1、环境准备授权 | 受信独立 workspace、exact SHA/tree、相关测试和真实构建、结果与制品可下载校验；不部署。可与 P2 并行。 |
| P4 产品与规范 | Web Owner + 集成 Owner | P1 状态合同；验收依赖 P2/P3 | 聚义厅显示真实派工/执行/验收状态；刷新可恢复。全部通过后更新持久路由与运行规范。 |

实现可以在不重叠路径/worktree 内并行；身份/ACL/事务由 critical_worker 负责，冻结合同后的前端由 balanced_worker 负责，验证协调用 gpt_test_runner。这里的 Owner 是研发分工，不是用本地子 Agent 冒充 Eva。所有 Eva 执行证据必须来自扈三娘的真实 runtime。

### P0 核验输出

记录 API 制品版本、客户端源/部署副本版本、受控 endpoint、runtimeInstanceId、绑定身份、有效开关、实际 tenant/client/owner 映射、最后注册及受支持协议。输出脱敏，不读取或复制用户凭据来绕过 401。

若当前开发会话没有已鉴权调用入口，明确“产品链路验收”与“开发控制面接入”是两件事。产品先通过登录态入口验证；后续开发控制面也调用同一业务 API，获取最小授权，不另建直接 SSH/跨线程派工旁路。

### P3 Eva 的精确执行合同

- 固定项目各组件 commit/tree、任务 ID、work item ID、commandId、测试选择器、输入 manifest 和工具链要求。源码分支名不是执行证据。
- 使用 Eva 本地受信 workspace policy，仓库、根目录和基线不由聊天载荷覆盖。保护 `/home/chc/wsps/cyf` 既有脏改动，创建本任务独立工作区。
- Eva 历史回报为 aarch64，Java 尚未找到；重新核验，不直接复制 x86_64 的 JDK、node_modules 或 native 依赖。缺少工具链时形成必要安装方案再执行。
- 根据实际源码、依赖、构建临时文件与产物估算容量，不增加无依据磁盘/内存硬门槛。没有清理其他任务文件的默认权限。
- 后端 Gradle 一律经 Eva 上项目 orchestrator 串行；不使用生产数据库或未知共享 fixture。
- 输出源码 commit/tree、主机/runtime、工具版本、开始/结束时间、退出码、测试通过/失败/跳过、日志和产物 SHA-256；服务端保存可授权读取的文件引用，下载后校验字节。
- 最小只读探针通过仅算 P1 通过；必须真实相关测试及构建通过，才可把 Eva 纳入构建执行规范。构建脚本失败必须报失败，不靠 LLM 文字结论改成成功。

## 5. 验收用例（待执行，不代表已通过）

1. **宋江→Eva→宋江**：用户发起，只读探针由 command.dispatch 执行；接收/开始/结果能按同一任务、命令和 runtime 追踪。
2. **宋江→另一真实 Agent**：相同合同成功，不写死扈三娘身份；无第二节点时明确未验收，mock 不能替代。
3. **Agent A↔Agent B**：A 定向提问、B 回复；A 发起授权工作请求、B 交付、A 消费固定成果继续处理；宋江仅看到其被授权接收的进展。
4. **真实测试与构建**：分别核验相关前端、后端测试和构建；可先完成一个组件但不得宣称另一组件通过；报告可下载且摘要一致。
5. **失败真实可见**：测试失败、工具缺失、无受信 workspace、目标离线都给出精确状态；accepted/delivered/ACK 不能显示为业务成功。
6. **幂等与恢复**：重复提交、重复投递、ACK/结果乱序、执行后回执丢失、API/客户端重连；不重复构建，不丢已提交结果，未知副作用进入核对。
7. **身份隔离**：伪造 source/target/owner、跨任务取结果、非成员派工、撤销授权、旧 runtime 回报均按现有权限及 fencing 处理；宋江无全局越权。
8. **用户可见性**：关闭/刷新浏览器后恢复任务和结果；取消只作用于明确拥有的工作项；慢请求不伪报失败或成功。

重启/故障注入先在隔离环境执行；线上验收不得重启、取消或杀掉其他任务进程。证据按 tree、选择器、fixture digest 复用，不为未变树重复全套构建。

## 6. 激活、发布与规范形成

- 先按精确 scope 激活首个新任务，不重放历史 shadow/dead/outbox 命令；检查旧积压是否会被激活，不能让一次开关操作释放历史工作。
- 配置保存前值、固定候选哈希、readback；变更应用方式与原任务运行互斥。基于真实错误修复，不盲目开全量开关，也不默认回退到不可靠旧通路。
- 沿用现有云效/临时本地授权政策：2026-09-17 临时例外未被恢复指令覆盖时，授权远端主机执行须记录 `build_origin=local_user_authorized` 与 `execution_host=Eva`，不得伪造 Flow Run。云效恢复后正式 CI/CD 回归既有流水线；Eva 的开发验证/构建用途与发布证据要求分开。
- 源码自检合入组件 develop；正式部署按已验证 exact SHA 冻结 release 分支、既有版本发布时间与授权执行。不因验收通讯顺便发布业务产物。
- P1/P2/P3 的真实用例通过后，更新既有 runbook、`MODEL_ROUTING.yaml`、AGENTS 的必要条款：Eva 是指定远端扈三娘，不是本地子 Agent；构建测试走结构化派发，失败明确上报，不静默换宿主机；上线仍按发布政策。
- 当前只有方案，不预写“Eva 验收通过/后续默认启用”。第一个可执行动作是 P0 只读基线核验并冻结 P1 最小合同。

## 7. 代码与证据入口

所有路径均为当前绝对路径；历史设计中 Reviewer/本地构建限制等以用户最新政策为准。

- `/home/isp/wsps/cyf/docs/juyiting-runbook.md`
- `/home/isp/wsps/cyf/docs/juyiting-multi-agent-collaboration-design.md`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/JuyitingActionController.java`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/HallActionDispatcher.java`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/BuiltinHallAgentSupport.java`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/handler/AgentWebSocketHandler.java`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/AgentTaskThreadController.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/config/AgentRabbitSafetyGate.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceRuntimeFileController.java`
- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/README.md`
- `/home/isp/wsps/cyf/docs/implementation/handoffs/JYT-UX-EVA-PREFLIGHT-20260921.md`

## 2026-09-22 详细设计补充

功能缺口、路由/密议/身份、Agent原生工具、协议与接口、状态/事务/迁移、Eva构建证据和验收细化见 [通讯与协作执行详细设计](/home/isp/wsps/cyf/specs/juyiting-task-collaboration/connectivity-detailed-design-20260922.md)。该文为 draft，优先验证直接 @/密议到 Eva，不要求先完成宋江适配。新增接口/字段是设计候选，未实施或激活；未改运行台账。
