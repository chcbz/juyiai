# Fast deliberation 分支合入与多媒体议事方案影响评估

日期：2026-09-27。范围：`codex/juyiting-codex-fast-deliberation-context` 与各仓远端 `develop`。结论：**当前不是 merge-ready，不执行直接合入；建议修复/整合后作为多媒体议事基础能力复用。**

本轮仅取远端 refs、读取精确提交、生成不改索引/工作树的 merge-tree、在本线程临时快照执行定向测试与无模型调用探针。未 checkout/merge/push、未创建 Reviewer、未运行 Gradle/生产构建、未执行 SQL/模型调用或部署。现有脏工作树不作为评估基线，也未回退。

## 1. 精确基线

开始及结束两次 `ls-remote` 结果一致：

| 仓库 | develop | candidate | develop-only / candidate-only | 合并模拟 |
| --- | --- | --- | --- | --- |
| sdd | `02d66c044a379c5b602ee854b92a56bdb1a12496` | `1d7090f91ac55e57ce0000d520572f9204a02d11` | 100 / 32 | 2 个 gitlink 冲突；另有缺失历史子模块对象提示，不据此认定候选损坏 |
| api | `e15e1a9d947e86e5f81a3288948087466a8a879c` | `caee54fc27a08146f9cc57219cf86c763e41c531` | 17 / 5 | 6 个文件内容冲突 |
| web | `9854173f7f409ca2f1c862eb153b0e3574ee58ff` | `96838f17fc24fbf21781be39476aa9723dee3a2c` | 20 / 6 | 2 个文件内容冲突 |
| client | `29fda32acca7a4c4f7a66a4188946853086e6dcb` | `68dbe8992a56c8e1041056a9123b1156d1d2b35e` | 5 / 8 | 1 个测试文件内容冲突；主程序自动合并后语法检查通过 |

API 主要冲突：ChatController、JuyitingAgentRelayService、AgentWebSocketHandler、对应测试与 chat-service build.gradle。Web 冲突：hallConversationMessages.js、useHallConversation.js。客户端冲突：agent-client.test.mjs。

最新 develop 包含候选基线之后的服务器权威发送者身份、可信任务材料注入、多 owner 托管隔离与注册、文件执行 native start receipt 等修复。不能采用整文件 `ours/theirs` 或用候选 gitlink 覆盖最新组件。根仓还含非本 feature 的历史文档提交；应只整理本需求文档，并在组件整合后重新固定 gitlink。

## 2. 需要修正的代码问题

以下定位均是精确候选快照，不是当前主工作区行号。

### F1 / P1：新 durable admission 绕回客户端提供的发送者身份

`ChatDeliberationService.admit()` 第 120–121 行直接采用 `input.getSenderType()/getSenderName()`。候选的 final 持久化也接受调用方传入的 senderName。最新 develop 已新增 HumanSenderIdentityResolver/AgentSenderIdentityResolver，将人类和 Agent 展示身份固定到服务端权威身份。

因此即使解开 ChatController 的文本冲突，仅在 Controller 保留 resolver 仍不够：新 durable service 的入库也必须接收已解析的身份，不能继续信任请求中的 senderType/name。否则旧的身份混淆问题从新路径重现。

修复：将服务端身份结果贯穿 admission、持久消息、事件和最终回执；补带伪造 senderType/name 的 v2 请求及 Agent final 回归，不以新前端不发送这些字段代替服务端校验。

### F2 / P1：后台无逐目标能力协商，默认客户端无法接收新 durable CHAT

`ChatDeliberationOutboxRelay` 第 192–199 行直接构造 hostedWire 并发送，未按目标 Agent 的 fastChat/appServer/dispatch-ack 能力选择协议。候选 env 默认 fastChat/appServer 关闭；`runFastChat()` 第 4031–4032 行对 modern durable 请求直接报 `FAST_CHAT_FEATURE_DISABLED`。

本轮用仓内 API wire fixture 和默认 Profile 做无网络探针，得到 `FAST_CHAT_FEATURE_DISABLED`，兼容 fallback 调用次数为 0。客户端这样 fail closed 本身正确，问题是服务端发送了目标尚未支持的协议。仅升级 API 或升级但未开启 Fast CHAT 的客户端，会破坏原本能聊天的接入；“自家接应”尤其不能假定同步升级。

修复：服务端读取并校验逐 Agent capability，在受理/分发时选定与能力匹配的路径；旧协议支持明确保留，现代受理之后不能偷偷重跑旧执行。版本混用、群聊混合目标和开关关闭要测试。

### F3 / P1：业务快照不足以重建新模型线程的多轮上下文，内置路径也未消费快照

`ChatDeliberationService.factsManifest()` 第 677–694 行仅存会话、任务概要、inputRefs 和 userMessage ID，无历史正文或摘要；`summaryRevision` 仍为 null。客户端 envelope 只包含上述事实与当前消息，无按引用取回历史内容的实现。Thread binding 不存在/因配置变化新建线程时，模型不能从这些 ID 重建前几轮要求。

此外 `ChatDeliberationOutboxRelay.runBuiltin()` 第 324–326 行构造 Prompt 时只显式加入本轮 `content`，没有传入 factsManifest、可信 taskMaterials 或正确的会话上下文。这与最新 develop 内置宋江的可信资料注入路径发生实质重叠。

此结论是缺少上下文输入路径，不声称已做真实模型质量实验，也不声称所有可 resume 的已有线程都会丢记忆。

修复：从业务 DB 形成有权限、精确版本的历史窗口/摘要/选定素材上下文，恢复新线程时可消费；内置和远端路径采用一致上下文合同。测试新线程、模型策略变化、缓存丢失以及“引用上一稿继续修改”。

### F4 / P2：INSPECT 的能力声明与可执行范围不一致

API capabilities 声明 `chat/inspect`，客户端注册也包含 INSPECT；但 `runReadOnlyInspection()` 第 4102–4103 行直接抛 `INSPECT_NOT_ENABLED`，真实聊天路径并未调用该检查实现。inputRefs 只接受 `{type,id}`，类型仅 conversation/task/message，不能表达用户空间 `fileId + version` 或会话产物引用。

探针确认该 inspection 函数不可用。不能把 `interactionHint=inspect` 或有 inputRefs 当作“图片已读取”的证明。

修复选择：如暂只提供只读问答，应收窄能力声明并明确未接通的能力；接多媒体方案时扩展精确素材引用及受控领取，不能简单放开任意路径/工具。完整生图不是此只读分支本来就该完成的功能，不能通过移除 EXECUTE 禁止来实现。

## 3. 数据和发布风险（区别于上述代码问题）

- 候选引入 chat_context_snapshot、chat_request、chat_turn、chat_dispatch_outbox、chat_conversation_event 及 schema-version/migration 逻辑；初始化器在非 H2 数据库启动时运行，不是一个纯前端开关。缺少字段/索引与 additive migration 配置必须按实际库核对。
- 修改 OAuth 签发和通用资源过滤器：无 tenant 声明的旧 machine JWT 会被拒绝；影响不限聚义厅。需按实际机器客户端和 token 生命周期进行兼容切换，不能假设 Web/Agent 同时更新即可。
- 候选 acceptance 明确未执行真实 MySQL 8 migration/恢复演练、真实部署 Profile 负向工具验证、线上验证。已有单测不能替代这些风险相关证据。
- branch readiness 文档包含历史独立 Reviewer、未测算宿主资源门槛和逐次发布授权表述：**不能把这些旧规定当本轮合并阻断依据**。沿用用户最新 Owner 自检、观测优先和真实授权边界；本轮阻断依据是实际冲突、上述代码问题及必要兼容/数据验证缺口，不是历史磁盘/swap 数值或性能目标。
- 性能 A/B 没跑意味着不能声称已加速；这不单独构成性能发布硬门禁。涉及真实付费 Provider 的验证需留在已授权范围，不由本轮读分支推导付费许可。

## 4. 本轮验证

| 检查 | 结果 | 能证明什么 |
| --- | --- | --- |
| 四仓精确远端 SHA 开始/结束核对 | 一致 | 评估提交没有在本轮观察窗口变化 |
| Git merge-tree | 四仓均 exit 1 | 当前不能直接无冲突合并；未修改真实索引/工作树 |
| API/Web/client diff --check | 全部通过 | 无 Git whitespace 报错，不等于编译/业务通过 |
| 候选 Web 定向测试 | 79 passing | fast-deliberation + hall-conversation 两个测试文件 |
| 候选客户端定向测试 | 141 tests passing | chat-runtime + agent-client 两个测试文件，含嵌套用例 |
| 默认 Profile durable 请求、INSPECT 探针 | 复现 F2/F4 | 无真实模型/服务请求 |
| 自动合并预览中的客户端主程序 node --check | 通过 | 只证明该文件语法，测试冲突仍未处理 |
| API Java/SQL 正式集成测试 | 本轮未运行 | 不宣称合并后编译或数据库已通过 |
| 浏览器端到端与付费模型验证 | 本轮未运行 | 不宣称线上可用、生成成功或性能达标 |

定向测试运行于从候选 exact SHA 导出的本线程临时快照，借用现有依赖目录，不是 dirty 主工作区；也不是冲突解决后的 merged tree。候选文档里历史 377/85/147 等数字是原实现方记录，不能与本轮 141/79 混算。

## 5. 对当前多媒体工作空间方案的影响

**产品目标不变；技术实现应整合，不应并行建设第二套会话 request/turn/outbox/snapshot/event 体系。**

| 当前方案部分 | 该分支可提供 | 仍需补齐/调整 |
| --- | --- | --- |
| 点将后自动议事 | durable admission、request/turn/outbox 基础 | 点将意图到唯一会话/首次需求及资料投递的业务桥接 |
| 流式回复与刷新恢复 | delta 去重、event journal、cursor/replay、查询与取消 | 将消息 parts 与媒体就绪/失败纳入同一事实模型；不能把 turn 文本 final 当生成文件完成 |
| 上下文与连续修改 | snapshot/sourceVector/thread binding 的基础结构 | F3 修复、fileId/version/assetRef、源稿真实读取；未归档试稿可直接继续修改 |
| Agent 直接生成或澄清 | CHAT/INSPECT 与 EXECUTE 的边界 | 受服务端权限/费用/能力约束的生成编排，将请求转为真实 execution；不能在 read-only CHAT 内放开生图工具 |
| 保存到空间和验收 | 不提供完整实现 | 会话产物持久化、主动归档、最终成果选择及正式交付/验收衔接仍按原方案做 |
| 双接应方式 | 公共客户端 fast-chat 框架 | 保留最新 develop 多 owner 托管隔离、native start receipt；修复 F2 并覆盖旧/新自家接应 |
| 存储目录 | 不要求改变现有文件根 | 继续保留 workspace-private/task-artifacts-private 及客户端独立执行目录，无历史文件迁移 |

关键设计细化：聊天 turn、文件 execution、媒体 part 三者显式关联。文本已结束而图片仍生成属于正常中间状态；澄清不占用长时间生成 lease。用户继续修改会启动新 execution，但保持同一个悬赏会话与精确源成果引用。

## 6. 推荐推进顺序

1. 在独立、路径归属明确的整合工作树基于最新组件 develop 整理候选，不覆盖当前 dirty 工作树，不一键选择分支全文件。
2. 先解决 F1/F2/F3 和真实 capability 声明，保留 develop 身份保护、资料注入、多 owner 托管和执行 START 语义；再解决相应测试冲突。
3. 对最终 merged tree 执行身份/协议混用/上下文恢复/文件执行回归，核对 MySQL 迁移与 OAuth 兼容发布计划；按用户当前发布政策由 Owner 自检推进，不新增 Reviewer。
4. 组件达到合入条件后才合入 develop；根仓只更新目标 feature 文档与已验证组件 gitlink，避免带入无关历史文档。
5. 将修正后的 durable 会话机制作为多媒体方案基础；在其上实现媒体内容块、会话产物、自动受控执行、主动保存和验收。不能把这个分支合入本身标为“画鸟交付完成”。

## 7. 可复核证据位置

本轮独占证据根：`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d`。

- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/manifest.json`：四仓 exact SHA、merge base、模拟合并树与退出码。
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/api-merge.txt`、`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/web-merge.txt`、`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/client-merge.txt`、`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/sdd-merge.txt`：冲突原始输出。
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/web-targeted-tests.log`、`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/client-targeted-tests.log`、`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/behavior-probes.log`：本轮原始测试/探针日志。
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots`：候选精确提交导出的只读评估副本；`/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/merge-preview` 是带冲突标记的模拟结果，不是已解决候选。

主要候选源码快照：
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatDeliberationService.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatDeliberationOutboxRelay.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/InteractionRouter.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatController.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/chat/jia-chat-service/src/main/java/cn/jia/chat/config/ChatDeliberationSchemaInitializer.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/api/common/jia-common-core/src/main/java/cn/jia/core/security/TenantClaimPolicy.java`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/client/conf/codex-ws-agent/agent-client.mjs`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/client/conf/codex-ws-agent/chat-runtime.mjs`
- `/tmp/cyf-fast-delib-mergecheck-20260927-9lm5fi5d/snapshots/client/conf/codex-ws-agent/app-server-adapter.mjs`
