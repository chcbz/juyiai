# 聚义厅统一技能执行详设（SE-2）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：原生技能执行与管理的职责收敛。**

### 最小责任链
API权限/完成事实；bridge目录进程会话隔离；模型编排；工具具体协议；技能经验；Web展示。

普通技能安装/配置→任务授权→原生执行→工具产物适配→API提交成果→Web显示权威结果。

### 实施约束
RB-1和原生详设优先于旧runner协议；旧执行/恢复单轨退役，历史只读；不按技能名/Provider硬编码通用层，不缓存全部技能包。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

SE-2旧runner/协议设计与实施记录，保留来源但不作为新的执行/恢复入口；当前以RB-1及原生详设为准。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



## 2026-10-28 原生执行目标入口

新原生执行按[RB-1职责规格](responsibility-boundaries.md)、[核心详设v3.1](native-execution-technical-design-20261027.md)、[扩展详设v3.1](native-execution-extensions-20261028.md)实施。下文SE-2保留为既有合同/历史实现来源；其固定ACTION_REQUEST/单技能runner/宿主生成文件规则不得扩为新原生路径的通用前提。单轨切换不保留历史执行恢复，也不自动转换旧执行；旧已提交成果只读，不重算旧摘要。

已有越界实现不是永久兼容项，须执行v3.1§16的删除与退出条件；专业工具算法及正确职责的保护继续复用。此导航更新不是源码删除或上线声明。

> **2026-10-26局部修订**：源码组件目录现为 `conf/codex-bridge/`，仍耦合Codex app-server；下文2026-10-13基线不是现行安装路径。媒体批次精确REPLACE、失败规划终态投影及代码入口以 [management-contract补充](management-contract.md#2026-10-26-媒体替换与失败规划读取补充已发布本次业务验收通过) 为准，实施与正式验证见 [本次handoff](../../docs/implementation/handoffs/CODEX-BRIDGE-REPAIR-20261026.md)。旧基线保留，不将源码变更等同上线。

**核对：2026-10-13；状态：实现合同，不是已上线说明。**

本版承接2026-10-13的SE-2合同，2026-10-23收敛到稳定design.md；已取代SE-1，澄清决定合并在文末。原字节在项目外备份保留，实际实现/验收看handoff与acceptance。

本文固定代码职责、协议、数据增量、事务、恢复和切换方式。后续直接实现与验证，不再安排“制定方案”任务。生产迁移时读回实际 schema/源码是安全核验，不是重新设计。

## 当前授权边界修订（2026-10-14）

用户明确要求Agent允许接外单。**任务下单人和Agent归属不必同Owner**；下文历史Owner scope表述不得解释为同Owner接单门禁。

- 任务范围：由已验证登录主体、订单委派、当前task assignment/grant和资料授权确定；任务、会话、结果继续按各自的数据授权范围隔离。
- Agent运行范围：由安装及已认证当前Runtime proof确定。任务Owner不能代填Runtime owner；安装、host、runtime instance、session generation和包摘要继续精确匹配。
- 能力计算：先验证任务委派及操作授权，再用真实Agent runtime scope读取该Agent的合法技能安装和实时目录；不比较task owner与runtime owner相等。无委派/授权不枚举他人的安装清单。
- 配置和技能安装：接外单不授予下单人修改Agent归属、配置、安装或购买技能的管理权。不为通过图片验收迁移/伪造Agent身份。
- 费用：仅登记展示，不参与运行就绪或执行授权；既有技能包购买事务独立保留。

实现状态以handoff和精确源码验证为准；本条是当前合同，不是已上线或完整外单执行验收声明。任务目录、执行接纳、Runtime领取/输入/回执均须显式区分上述两个范围，禁止只删除Owner字段而扩大资料访问。

## 0. 固定源码与已查明事实

精确 HEAD/tree 与已读文件摘要见 `baseline.json`。API/Web 本地受跟踪工作区干净；根仓库已有大量他人修改，只新增本特性目录。未查询远端 develop，也未核验当前线上 API/Web 制品，不把本地 HEAD 称作最新线上版本。

Runtime 源仓库：`/home/isp/wsps/chcbz/isp-install`，模块在 `conf/codex-ws-agent/`；实际安装位于 `/home/isp/apps/cyf-agent-runtime-v1/unified/codex-ws-agent`。已比较六个关键模块，其中 installed `agent-client.mjs` 与源 HEAD 不同：线上文件没有源中的 text-file 接线。其余五个抽查模块字节相同。实施必须保留源 HEAD 的已有 text-file 增量，不能拿 installed 整文件覆盖源码；这不是全 Runtime 同源证明。

已确认耦合点：

- Web `hallPointAndStartIntent.js` 同时硬编码媒体操作白名单和普通议事操作集合。
- `ChatActionCapabilityService.available/appendImageAdapter` 硬编码图片 Provider lane 与文本零资料条件。
- `ChatActionExecutionService.admit` 在图片和文本执行器之间分支。
- `ChatActionFinalService.actionProgress` 按文本/图片重新推导 childRequestId。
- `ChatActionOutcomeContract`、Runtime `juyiting-action-outcome.mjs` 均严格校验旧动作结构，必须同批更新。
- `ChatTypedDiscussionAdmissionService.admit`/`ChatTypedDeliberationContextService.resolve` 只处理本条 selectors；普通后续消息不会自动带入任务资料。
- `ChatConversationAssetSourceResolver.resolveAction` 已有真实来源校验，但受图片 operation 限制。
- `PersonalWorkspaceExecutionServiceImpl` 混合了通用文件、图片 consent、Provider 和固定 MIME。
- `ChatBountyAssetProjector` 才是执行输出→会话资产/消息的关键路径；`AgentTaskArtifactOutcomeServiceImpl` 是成果验收，**不改它的验收状态机**。
- 当前吴用 profile 含 typedInspection 与 controlledImageHttp；林冲、卢俊义没有相应键。装技能本身不会使识图就绪。

## 1. 决策与轻量边界

1. 沿用现有 `CHAT → ACTION_REQUEST → outbox → EXECUTE_SKILL → result` 调度骨架；result 可以是数据、文件或两者。仅文件产物进入文件归档，不增加第二个调度器。
2. 不保留 INSPECT_INPUTS 顶层业务操作。资料解析/受权读取是基础接口；当前模型具备视觉/文档输入时直接在原回合使用真实输入载体，专用OCR/解析则调用普通分析技能。不是每次识别都必须生成一个技能执行，也不强制先识别后编辑。
3. 沿用现有 `skillKey`/`skillVersion` 命名，不额外引入与安装不一致的 skillId。
4. SKILL.md 说明如何工作；只有要注册为平台可调用动作的技能才需要执行 manifest。普通说明型技能无需被强制改造成可执行插件，安装规则不能因缺少执行manifest拒绝它。两者都不是权限来源。
5. 一个新附属表保存技能执行快照和效果记录；主执行表、输出表、chat outbox/step/link/asset 继续复用；必须补足无文件结果的真正终态，不能为了复用而伪造空文件。
6. 不引入新守护进程、消息队列、DAG 引擎、插件热部署平台。复用当前轮询/outbox、Runtime 租约与锁。
7. 费用仅 `costInfo` 展示/登记。核心执行路径不能读取费用字段作判定，也不能创建 consent/冻结/预扣记录。
8. 原包购买和悬赏经济业务不变。Provider 帐号余额不足是外部工具真实错误，不转换为平台费用审批。
9. 新技能若采用现有 runner，只新增技能包与安装记录；新 Provider 协议可新增 runner 适配器；新安全边界/预览方式可能需要核心扩展，不承诺永远零代码改动。
10. 已有包大小、消息资料数量、租约等协议边界本次不随意扩大或新设。等待没有性能强制 deadline；保留真实传输超时和身份/用户取消。

## 2. 模块与改动清单

下文目录缩写：

- AS=`api/agent/jia-agent-service/src/main/java/cn/jia/agent`
- AI=`api/agent/jia-agent-api/src/main/java/cn/jia/agent`
- AC=`api/agent/jia-agent-core/src/main/java/cn/jia/agent`
- AM=`api/agent/jia-agent-mapper/src/main/java/cn/jia/agent`
- CS=`api/chat/jia-chat-service/src/main/java/cn/jia/chat`
- RT=`/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent`
- WEB=`web/src/composables/juyiting`

### 2.1 后端

| 文件/类型 | 固定修改 |
|---|---|
| AS/skill/SkillPackages.java | 从已批准产品版本/包存储读取不可变包，执行manifest存在时才校验声明；按摘要缓存，不按角色复制 |
| economy/.../skillseed/PlatformSkillPackageCatalog.java | 只负责内置包引导；一般新包采用已有市场版本记录+本地不可变包存储，不再仅认classpath/启动全量缓存；复用发布/安装ACL，不建立第二市场 |
| AS/skill/SkillInstallResultService.java | 可执行包才匹配manifest摘要；普通说明型包不伪造执行能力；Runtime就绪不冒充安装授权 |
| AS/skill/SkillInstallDispatchService.java | 保留安装身份/事务/outbox，不承载执行策略 |
| AS/skill/SkillManifestCodec.java（新增） | 解析执行声明并封装标准JSON Schema库；不自写方言/递归校验引擎；无网络ref加载 |
| AI/service/SkillCapabilityLookup.java（新增） | agent 模块定义能力查询接口，chat 实现实时 session 适配，避免 agent 反向依赖 chat |
| CS/handler/SkillExecutionSessionRegistry.java（新增） | 注册可信 Runtime 的当前技能目录；断线/代际变化失效 |
| CS/service/ChatActionCapabilityService.java | 只投影可调用技能目录；模型原生输入支持另作运行事实，不伪装成INSPECT动作；移除图片/零资料文本特例 |
| CS/service/ChatActionOutcomeContract.java、ChatActionFinalValidator.java | action-v4 描述/参数/摘要验证，与 JS 共用正反 fixture |
| CS/service/ChatTypedDiscussionAdmissionService.java、ChatTypedDeliberationContextService.java | 确定本次有效资料上下文、冻结目录与能力快照 |
| CS/service/ChatConversationAssetSourceResolver.java | 提取 resolveAuthorizedSources，按来源类型校验 ACL/lineage，不按 GENERATE/EDIT 分支 |
| CS/service/ChatActionExecutionService.java | 唯一 EXECUTE adapter；按 descriptor 调用通用 createSkillConversation，不再分图片/文本 |
| CS/service/ChatActionDispatchService.java | 保留outbox claim和锁序，所有显式技能动作走EXECUTE；删除独立inspect分发分支 |
| CS/service/ChatBountyExecutionTerminationService.java | 接入protocol4撤销/取消，UNKNOWN不假装安全取消，保持Owner和在途副作用事实 |
| CS/service/ChatActionFinalService.java | 从已持久化 admission/step/link 读 childId，不按技能重新计算；投影执行与归档状态 |
| AS/service/impl/AgentTaskExecutionGrantServiceImpl.java、AgentTaskDeliberationOperationReadServiceImpl.java | 新议事 baseline 为 DELIBERATE/EXECUTE_SKILL；具体技能权限在已安装 entitlement+任务 scope 决定 |
| AI/service/PersonalWorkspaceExecutionService.java、AS/.../PersonalWorkspaceExecutionServiceImpl.java | 增加createSkillConversation/skillCommand/skillInput/commitSkillResult；统一数据与文件结果，复用lease/stage/recovery；不访问图片consent |
| AC/entity/SkillExecutionEntity.java、AM/{dao,mapper}/...（新增） | §7 的附属快照与 CAS 数据访问 |
| AS/api/PersonalWorkspaceConversationRuntimeController.java | 保留既有 conversation endpoints；增加 effect/resume 的通用端点；无图片端点新增 |
| AS/skill/SkillExecutionService.java（新增） | 快照、lease/effect 状态、复验与恢复；不另起调度器 |
| CS/service/ChatBountyAssetProjector.java | 增加executionId定向结果投影，分派数据/文件展示但不按技能分支；保留文件原事务；pending仅补偿 |
| CS/archive/conversation/ChatConversationArchiveService.java | 复用素材索引/读权限，只读目录不触发全内容读取/生成 |
| AS/service/impl/PersonalWorkspaceOutputFormatValidator.java | 结构校验器按 MIME 注册；未知安全文件走 opaque 下载，禁止自动 inline/执行 |

不改 `AgentTaskArtifactOutcomeServiceImpl` 的接受/替换/验收语义，不把生成完毕当作正式交付被接受。

### 2.2 Runtime

新增 RT `skill-manifest.mjs`、`skill-registry.mjs`、`skill-executor.mjs`；Provider adapter 从既有图片模块提取，不重写传输实现。

- `skill-install-manager.mjs`：执行 manifest 校验、可执行包安装标记绑定摘要、普通包仅绑定包摘要；保留 zip 防穿越/包摘要/Owner 锁。
- `agent-client.mjs`：注册 `skillExecution` 声明；接收统一 executionProtocolVersion=4；同一 poll 循环按 descriptor.runner 调用，不为每技能起 lane。
- `chat-runtime.mjs`、`juyiting-action-outcome.mjs`：action-v4 输出与验证；规划回合仍不允许直接运行生成脚本。
- `workspace-file-bridge.mjs`：复用受权输入下载、staged upload/commit，输出不直接写进业务文件表。
- `typed-inspection-runtime.mjs`：将真实内容载体/隔离/证据提取为公共materials-input adapter，原生对话和分析技能共享；旧顶层INSPECT路由退出；交付证据不代表模型理解正确。
- `controlled-image-http-executor-v3.mjs`：提取 HTTP 编解码/格式校验到 `skill-runners/image-provider.mjs`，去掉 consent/图片专用上层 command；留 Provider 特有限制在适配器。
- `conversation-text-file.mjs`：其已有实现迁为 `skill-runners/native-model.mjs`；不覆盖源 HEAD 增量。
- `report-outbox.mjs`、既有恢复留存：记录 manifest/结果回执，服务端确认后才清理本执行临时目录。
- `conf/cyf-agent-runtime-v1/lib/runtime-client.mjs`对应 exact-route 白名单同步新 effect/resume 路由；不得开放 `/internal/**` 全通。

### 2.3 Web

- `hallPointAndStartIntent.js`：投影 schemaVersion=2；校验平台权限结构/基本操作和任务/主体/版本，不要求精确等于两项；不枚举技能名称。未知平台操作仍协议报错，已知 EXECUTE_SKILL 下新 skillKey 可扩展。
- `hallTypedDeliberation.js`、`useHallTypedDeliberation.js`：discussion schemaVersion=2、action-v4、执行状态和技能参数消费。
- `useTaskWorkspaceBinding.js`：TASK_DEFAULT/EXPLICIT/NONE 选择；UI 显示“本任务资料”和“仅本条消息”。
- `bountyOutputCatalog.js`、`bountyOutputRecovery.js`、`useHallBountyRequestCatalog.js`：优先按执行 ID 读取结果，保留成果关联语义，不等全历史页面才能展示新成果。
- `useHallArtifactTransfer.js`：通用下载；`useHallArtifactOutcomes.js` 验收操作不改，只对新数据作回归。
- 删除新流量对 `hallPointAndStartProviderConsent.js`、`useHallPointAndStartCostConsent.js`、`hallControlledImagePointAndStartBridge.js`、`useHallPointAndStartControlledBridge.js` 的依赖；迁完其身份/幂等检查后才删死代码。
- `web/src/components/economy/SkillProductCard.vue`：显示运行费用说明，独立于包购买价；未知费用不显示为 0。

## 3. 技能包声明与参数算法

说明型包：`SKILL.md + 可选 scripts/references`；可执行包额外带 `manifest.json`。例见 `examples/image-edit-se2.manifest.json`。本方案不把所有普通技能都变成平台动作；执行声明仅为产品执行能力的扩展。

manifest 必需字段：`schemaVersion=1, skillKey, skillVersion, title, description, runner, entrypoint, parametersSchema, inputs, outputs, requirements`；`costInfo` 可省略，读取时规范为 UNKNOWN。

- runner 仅为已登记执行类型：首期 `provider-operation`、`local-script`、`native-model`。每种 runner 内按 adapter 注册表查找，不将脚本、URL、CLI argv 放入模型输出。
- entrypoint 是包内相对路径或维护方登记的 adapter 名；禁止绝对路径、`..`、符号链接逃逸。
- inputs 声明 `minItems/maxItems/acceptedMimeTypes`；min/max 有真实工具依据，平台沿用当前请求最多32来源边界，不凭未来视频推测新限额。
- outputs 声明 `dataSchema`（可空）、`mimeTypes`、`multiple`、`artifactsRequired`；分析技能可零文件，文件生成技能按合同必须有文件。结果必须满足声明，但不是模型自报成功即算真实有效。
- requirements 为工具/Provider alias，凭据不入包。
- costInfo 不参与执行结构校验失败：缺失或费用说明格式错误只显示 UNKNOWN 并记录元数据警告，不让费用数据阻塞合法技能。其可用格式为 `mode=FREE|FIXED|METERED|UNKNOWN`、可空十进制字符串 amount、currency/unit/description/source/updatedAt。未知不等于免费。包中只有默认说明，部署的费用说明可独立更新；不必为价格变化重打包或重发应用。快照记录执行时的说明及来源/版本，不把说明当作实扣。见§11。

`parametersSchema` 和 `outputs.dataSchema` 统一采用 JSON Schema Draft 2020-12，声明 `$schema`，取消私有 `cyf-params-v1`。Java用 networknt/json-schema-validator，Runtime用 Ajv 的2020专用入口；依赖精确版本随首个候选的Gradle/npm锁定文件固定，不在这里猜“最新版本”。两者兼容性由相同语料验证，不自写两套递归校验器。

部署安全策略：schema只从可信包及随制品提供的meta-schema读取，`$ref`只允许当前文档/已验证包内资源；禁HTTP/文件系统任意加载、类型自动转换、默认值注入和静默删字段。不支持的schema要在安装/声明就绪检查明确报错，不运行时假装接受。可信包并不解除JSON消息/归档包既有解析边界。参数、结果仍接受严格JSON解析（重复key/trailing token拒绝）。业务金额/ID用字符串，不能依赖JS浮点精确表示大整数；跨端数值格式以shared fixtures核验。

库只校验结构，身份/执行权限/网络出口/工具依赖仍由平台控制；Web不重复实现第三套权威校验。格式、字体、单元格等专属业务校验属于技能或格式验证器，不扩展核心方言。

标准参考资料（2026-10-13，页面获取状态见references.json；不是本项目跨语言兼容性已验证）：JSON Schema官方2020-12规范；Ajv官方JSON Schema版本说明；networknt官方README支持列表。机器可追溯地址见 `references.json`。

元数据与 SKILL.md 是受安装完整性保护的能力描述；资料、图片中的文字、历史聊天仍是不可信内容，不得改变工具权限、runner、凭据或文件范围。

## 4. 能力发现、版本和费用

复用 Runtime 注册消息增加：

```json
{"skillExecution":{"schemaVersion":1,"catalogRevision":"7","skills":[
  {"skillKey":"image-edit","skillVersion":"1.0.0","packageSha256":"<64hex>",
   "manifestSha256":"<64hex>","runner":"provider-operation","readiness":"READY",
   "reasonCode":null,"toolchainDigest":"<64hex>","bindingRevision":"4"}
]}}
```

Runtime 报告只能提供运行事实，不能授予安装 entitlement。服务端对照真实安装结果、包摘要、身份 proof、当前 session generation；同一 scope 存在多个不唯一就绪主体则明确不可用，不能任挑一个。

```text
installedDescriptor = package verified by installation receipt
runtimeReady = current session report matches descriptor and available runner/dependency
taskAllowed = actor/task/assignment + installation entitlement + data/network policy
callable = installedDescriptor && runtimeReady && taskAllowed
# 这里没有 costInfo、balance、consent，也不调用计价服务
```

连接建立/包安装/配置重新加载时重新检查，heartbeat 使用缓存；断线、安装变更或 session generation 变化立即失效。调用时重新验证同一绑定。缓存键含完整主体、安装摘要、toolchainDigest、bindingRevision；不永久按“吴用/林冲”缓存。

只向模型提供当前任务可用技能摘要与参数 schema，选中后 Runtime 才加载完整 SKILL.md/资源；不把所有包、全部历史文件塞入上下文。暂不可用技能给 UI 原因，不谎报 READY。

为 UI 增加只读 `GET /agent/tasks/{taskId}/skill-capabilities?targetAgentId=...`，复用 Owner/task ACL，返回 `catalogRevision, items[{skillKey,skillVersion,title,state,reasonCode,costInfo}]`。无任务访问权404，真实目录依赖故障503。价格缺失永远不是503/403原因。API 响应 no-store，不包含 Provider 地址、凭据或内部路径。

## 5. action-v4 与任务资料

### 5.1 动作快照

在 facts.availableActions 中将旧 operation 特例改为：

```json
{"actionId":"act_<digest>","kind":"EXECUTE","operation":"EXECUTE_SKILL",
 "skill":{"skillKey":"image-edit","skillVersion":"1.0.0","packageSha256":"<64hex>","manifestSha256":"<64hex>"},
 "parametersSchema":{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","properties":{},"required":[],"additionalProperties":false},
 "inputMimeTypes":["image/png","image/jpeg"],"minSources":1,"maxSources":1,
 "outputMimeTypes":["image/png"]}
```

发现/结果中的粗粒度 mediaType 继续使用现有 text/image/audio/file；video 等新媒体在没有专用展示时归 file，保留真实 MIME，不为新增格式扩核心枚举。

所有显式技能动作的kind=EXECUTE、operation=EXECUTE_SKILL。原生模型直接看图属于本回合输入准备，不生成一个假的skill动作或额外分析回合。需要OCR/特定分析工具时按普通技能目录选中；缺依赖明确不可用。

模型只返回 `action:{actionId,instruction,sourceRefIds,parameters}`。skill/version/binding 由服务端从已冻结 facts 解析，不从模型或浏览器接受。请求非法参数直接校验失败；缺必要资料则 CLARIFY；资料已授权但模型未取得实际输入时，使用公共资料载体或分析技能，不让模型凭文件名臆测。能直接编辑的工具不强制先执行分析技能。

actionId 取安装描述的稳定摘要；在请求 facts 内唯一。重试读取原 facts，不重新跑当前目录来重建旧 action。packageSha256 是归档包原始字节摘要，manifestSha256 是包内 manifest 原始字节摘要；缺省费用的展示规范化不改变这些摘要。使用现有 canonical JSON 编码与 sha256，数字/字符串规格在 Java/JS fixtures 中固定。

chat action facts/final schemaVersion=4；Runtime 执行协议 executionProtocolVersion=4；manifest 自己的版本=1，三个版本不混用。升级不保留两种新执行生产入口，历史原始回执仍可审计读取。

### 5.2 资料上下文

`POST /chat/conversations/{id}/interactions/discussion` 沿原认证与 Idempotency-Key，body 升级 schemaVersion=2，增加 `materialScope=TASK_DEFAULT|EXPLICIT|NONE`，保留 sourceSelectors。

- TASK_DEFAULT（UI 默认）：当前任务有效资料版本 + 本消息显式选中资料。只自动纳入 TASK 可见且对当前 Agent 合法的 link，不扩展整个个人 workspace。
- EXPLICIT：仅本消息所选，适合“仅本条消息”。
- NONE：不带资料；sourceSelectors 必须空。
- CLARIFICATION_REPLY：父问题资料在其原 MESSAGE/TASK scope 内继续有效，除非用户显式替换/排除。普通下一条消息不继承无关 MESSAGE 临时资料。
- 自动来源上限沿现行32；超出不静默截断、不读取全部正文，保持普通对话可用，返回资料选择提示与分页选择入口。本次执行等待用户缩小范围。

服务端在原 task-root/binding/conversation 锁序内：

```text
先按完整 scope + key 查旧 admission；同 bodyDigest 直接回放
  → 校验当前 task/assignment
  → resolveEffectiveSelectors(command, currentTaskLinks, clarificationParent)
  → 去重：sourceKind + 精确版本身份；保持 deterministic 顺序
  → 逐项查 Owner/ACL/版本/来源关系
  → 冻结 catalog 的 MIME/大小/hash/来源（不信任客户端提供）
  → 生成事实和技能目录快照
  → 请求、快照、admission、outbox 同事务提交
```

明确：bodyDigest 绑定原始用户命令（含 materialScope），requestDigest 绑定解析后的有效资料快照；相同 key 重放不因任务后来添加资料而改变请求。源已撤销不允许新读取，但已持久结果可按当前读权限回放。

`resolveAuthorizedSources` 对 TASK_LINKED_WORKSPACE_VERSION 校验任务 link/版本/当前成员权限，对 CURRENT_CONVERSATION_ASSET 校验 scope/generation/producer step/output 已提交与保留状态。之后才按 skill.inputs 做 MIME/数量校验。

**图片编辑可接受任务上传图或当前会话成果；前者没有虚构 producer。** 只有显式编辑已有成果，才建立 replaces 精确引用；普通上传图编辑产生新成果，不伪造“替换某个已交付成果”。

## 6. 执行接纳：唯一事务入口

`ChatActionExecutionService.admit(BoundAction)` 的具体逻辑：

```java
// 调用方仍为 ChatActionDispatchService.consume 的 MANDATORY 事务
var action = requireActionFromFrozenFacts(bound);
require(action.kind == EXECUTE && action.operation == EXECUTE_SKILL);
var prior = typed.findAdmissionByKey(scope, actionEventId, true);
if (prior != null) return verifyReplayAndReadChild(prior, bound); // 不调用 live runtime/provider
var grant = grants.resolveAndAdmit(scope, task, assignment, agent, "EXECUTE_SKILL", false);
var descriptor = installedSkills.requireExact(action.skill);
var sources = sourceResolver.resolveAuthorizedSources(...);
validateParameters(descriptor.parametersSchema, action.parameters);
validateInputs(descriptor.inputs, sources);
var ready = capabilities.requireExactCurrent(scope, agent, descriptor);
// 不调用费用/consent，不在事务中访问 Provider/存储/启动进程
var snapshot = freeze(descriptor, params, sources, grant, ready.bindingRevision);
var execution = executions.createSkillConversation(scope, stableIds(actionEventId), snapshot);
insertChildRequestAndStepAndLinkAndAdmission(execution, bound);
persistActionStarted(bound, execution.requestId, "EXECUTE");
return execution.requestId;
```

snapshot_json 必含：`schemaVersion=1,skill{key,version,installationId,packageSha256,manifestSha256,runner,entrypoint},taskId,conversationId,conversationGeneration,targetAgentId,originalUserMessageId,originalUserContentSha256,parentOutcomeId,parentFinalDigest,actionEventId,instruction,parameters,taskGrant{id,version,assignmentRevision},providerBinding{alias,revision},inputs[],sourceSnapshotDigest,outputs,deliveryRelation,costInfo`。本地技能 providerBinding=null；costInfo 是不影响权限的登记快照。inputs 各项为 `inputRef,sourceKind,sourceIdentity,contentMimeType,byteLength,sha256`；sourceIdentity 保留工作区 file/version/purpose 或会话 generation/asset revision/producer output lineage；不要保存可由其他租户访问的裸URL。初始Runtime session放在lease/效果记录中，不把旧session永久锁死在不可变业务快照以致合法恢复不了。

新 ID 一律按 `sha256(canonical(scope,actionEventId,label))` 派生；request/step 用现有字段可容纳格式，executionId=`pwe_`+前60 hex（64字符，符合既有 chat link），runId=`pwe_run_`+完整64 hex。同 key 不同语义 digest 返回409，不追加任务。

锁序：接纳保持原 task root→binding→conversation→outbox→执行/附属行。注册/目录读取不在此获取反向 Runtime 安装锁；Runtime proof 验证复用既有 fencing API。实际 start/effect/commit 路径沿已有 runtime installation/session→task root→execution 的锁序；跨两域协调采用现有准备/短事务复验，不新增倒序持锁调用。

所有网络/Provider/文件大块读取在短事务外。准备后的 opaque 文件描述只能由服务端产生，提交事务重新检验身份、lease、输入版本及摘要，不从客户端 metadata 推断成功。

## 7. 数据库增量（明确选择：一个附属表）

**不创建第二张任务表或费用表。** 新增 `agent_skill_execution`，与现有 `agent_personal_workspace_execution` 一对一，承载旧通用执行表缺失的技能语义。主表仅存接纳/撤销/结果提交等宏观事实；附属phase是细粒度处理阶段，不是第二套独立成功真相：所有终态必须同事务更新主/附属并满足约束，读取时遇到不一致报告恢复问题，不以任一行猜成功。

| 字段 | 类型/约束 | 用途 |
|---|---|---|
| id | BIGINT AUTO_INCREMENT PK | 延续现有主键风格 |
| tenant_id/client_id/owner_jiacn | VARCHAR(50)，现有 binary scope 语义 | 隔离 |
| execution_id | VARCHAR(100) | 唯一关联 PWE |
| skill_key/skill_version | VARCHAR(64) | 与现有安装标识长度一致 |
| package_sha256/manifest_sha256 | CHAR(64) ascii_bin | 不可变包身份 |
| snapshot_json | JSON NOT NULL | 参数、源描述、来源 lineage、grant/binding/输出要求、skill描述/费用快照；无凭据和绝对存储路径 |
| snapshot_sha256 | CHAR(64) ascii_bin | canonical snapshot 完整性 |
| phase | VARCHAR(24) | READY、RUNNING、WAITING_PROVIDER、RESULT_UNKNOWN、RESULT_READY、ARCHIVING、COMPLETE、FAILED、CANCELLED |
| effects_json | JSON NOT NULL，初值 `{}` | 每个逻辑副作用的持久记录，见§9 |
| result_manifest_json | JSON NULL | 通用result含结构化data及artifact引用，不嵌入二进制/临时下载密钥 |
| last_error_code | VARCHAR(64) NULL | 非成功原因；不复用价格不足概念 |
| version | BIGINT NOT NULL DEFAULT 0 | CAS 状态版本 |
| created_at/updated_at | BIGINT NOT NULL | 与项目时间约定一致 |

唯一键 `(tenant_id,client_id,owner_jiacn,execution_id)`；不再创建 idempotency unique，沿 PWE 既有 `uk_pwex_idempotency_scope`。事务同时插入主行/附属行，不留下半条接纳。

DDL 资源新增 `agent-skill-execution-v1.sql`；mapper/DAO 必须保持 exact binary scope 检查。新增 `SkillExecutionSchemaInitializer` 只做已安装 schema 检测/就绪报告，生产 DDL 走既有显式迁移入口，不允许启动时偷偷迁移。

PWE 增量：

- 保留execution_mode=CONVERSATION；旧四态继续描述历史行，protocol4统一新增RESULT_COMMITTED终态，涵盖数据/文件/混合结果。新执行写 permitted_operation=EXECUTE_SKILL、execution_protocol_version=4、controlled_consent_id=NULL、operation_grant_id=NULL；原 grant/assignment/lease 完整保留。
- `output_content_mime_type` 允许 NULL；protocol=4 时从 snapshot.outputs 取允许集合，旧非4行保持原非空/原校验。移除对新协议的单一 MIME 枚举限制，SQL CHECK 必须显式 `(execution_protocol_version IS NOT NULL AND execution_protocol_version=4) OR (output_content_mime_type IS NOT NULL AND ...旧约束...)`，不能利用 SQL NULL 三值逻辑意外放行旧行。
- service 新协议不使用旧 image source/consent 表；通用源快照就在附属行 JSON，按 execution 加载，有现有最多32源边界，不新建每格式 source 表。
- PWE终态负责宏观事实：protocol4结果提交为RESULT_COMMITTED（不是必须有文件），撤销为INPUTS_REVOKED，确定失败为FAILED；未知外部结果保留 QUEUED 宏观行，由附属 phase=RESULT_UNKNOWN 阻止执行重发。
- `PersonalWorkspaceExecutionMapper.listQueuedConversationsByTarget` 的新协议分支必须 JOIN 附属行，只有 READY 才入新执行队列；RUNNING/WAITING_PROVIDER/RESULT_UNKNOWN/RESULT_READY/ARCHIVING 只进入各自恢复动作，CANCELLED/FAILED/COMPLETE 不再分发。不能仅凭主行 QUEUED 重发。
- phase COMPLETE 在通用result已持久化且所需消息/文件投影完成后设置；RESULT_COMMITTED与ARCHIVING可共存。零文件走数据结果投影，不插入虚构output/asset。
- 原 failure_code 固定 AGENT_DELIVERY_FAILED 的 CHECK 不放宽；具体技能错误存附属 last_error_code，并投影到技能状态。

`chk_pwex_execution_protocol` 当前只允许1/2/3，必须显式扩展第四个分支：protocol=4、CONVERSATION、permitted_operation=EXECUTE_SKILL、controlled_consent_id IS NULL、operation_grant_id IS NULL、runtime_input_snapshot_digest IS NOT NULL 且64位hash。`runtime_input_snapshot_digest` 写冻结 source vector 的摘要；完整 snapshot_sha256 另存附属行，二者不混用。保留旧三个分支的历史约束。同步 `ControlledImageFollowupV3SchemaInitializer` 中 execution CHECK 的期望定义和 schema detector，不让旧初始化器恢复旧 CHECK 或把正确新 schema 判为漂移；取消费用链路不能导致通用 schema 检测随图片开关一起关闭。

同步扩展主表state/failure CHECK：RESULT_COMMITTED只允许protocol4；成功行failure字段仍为空。所有显式列举主执行状态的队列、历史、终止、结果projection及测试同步更新；不能只在附属表标完成让主表永久QUEUED。

现有 output STAGED/COMMITTED、文件 storage/manifest、会话 asset 表全部复用。对新 MIME 移除 source 中写死的媒体分类作为存储准入条件，改为格式策略：有可信验证器就验证，无预览器走 application/octet-stream 附件下载（保留声明与检出 MIME），不信任扩展名，不 inline 执行 HTML/SVG。

不批量更改历史费用回执、旧执行摘要、typedInspection 原始证据。新代码与旧数据的审计读取不等于继续保留旧写入入口。

## 8. Runtime HTTP 与命令协议

以已存在 `/internal/agent/tasks` conversation 路由扩展，不另开公网技能执行接口。

| method/path（前缀略） | 行为 |
|---|---|
| GET `/conversation-executions/commands` | 返回 protocol4 命令；分页、只读；排除未知外部结果自动执行 |
| POST `/{task}/runs/{run}/conversation/lease`、`lease/renew` | 复用当前租约；支持 protocol4 身份 |
| POST `/{task}/runs/{run}/conversation/inputs` | 返回附属快照内已授权输入 |
| POST `/{task}/runs/{run}/conversation/inputs/{ref}/content` | 读前复验 lease/ACL，按已固定版本供字节 |
| POST `/{task}/runs/{run}/conversation/effects/{effectId}/start`（新增） | 短事务登记逻辑副作用，返回 NEW/RECORDED/KNOWN/UNKNOWN；不是费用许可 |
| POST `/{task}/runs/{run}/conversation/effects/{effectId}/result`（新增） | 持久化 Provider requestId/状态/不可变请求摘要，幂等 |
| POST `/{task}/runs/{run}/conversation/resume`（新增） | 新 session 同 Owner 同执行恢复 claim；仅返回允许的查询/上传/归档工作，不自动重新生成 |
| POST `/{task}/runs/{run}/conversation/outputs/{output}/content` | 复用分离上传与最终提交 |
| POST `/{task}/runs/{run}/conversation/output-commits/{manifest}` | 仅历史文件语义；新protocol4统一经result-commits提交完整结果，不保留第二个新执行成功入口 |
| POST `/{task}/runs/{run}/conversation/result-commits/{manifest}` | protocol4唯一新结果提交入口，接收data+artifact引用，验证后原子提交RESULT_COMMITTED；恢复重放相同结果，无效session不可绕过 |
| POST `/{task}/runs/{run}/conversation/failure` | 仅确定失败/取消，未知副作用走专门 phase，不伪报失败 |

命令 body：`executionProtocolVersion=4,executionId,taskId,runId,conversationId,conversationGeneration,skill{key,version,packageSha256,manifestSha256},snapshotDigest,parameters,instruction,inputRefs,outputs`；授权 scope 和当前 session proof 走已有原生鉴权，不由 body 自报。

effect start body：`executionId,snapshotDigest,leaseFence,effectDigest,providerBindingRevision`；effectId 路径稳定。effectDigest 绑定 adapter、操作、参数、精确 input hashes 和绑定；不含 token。

所有 mutating endpoint 保留当前五个 X-Agent 证明头及租约规则。客户端无权供应 URL/账号/输出路径作为权限。400结构错误、401/403按现有原生认证、404隐藏对象、409状态/摘要/版本/lease冲突、503真实依赖不可用。未登记费用、金额未知不产生拒绝。已有 key 同输入返回原记录；改变输入409。

## 9. 执行、幂等与恢复算法

### 9.1 Runtime 执行伪代码

```js
async function executeSkill(command, ctx) {
  const installed = registry.requireExact(command.skill)
  validateSnapshotAndParams(command, installed)
  const resume = await ctx.claimOrResume(command)
  if (resume.resultManifest) return recoverResultCommit(resume)
  const inputs = await ctx.materializeAuthorizedInputs(command.inputRefs)
  // 精确文件hash；资料不作为shell/配置执行，临时目录仅本execution可见
  const result = await runners.get(installed.runner).run({
    instruction: command.instruction, parameters: command.parameters,
    inputs, descriptor: installed,
    effects: ctx.effects, outputDirectory: ctx.outputDirectory
  })
  const manifest = await validateAndPersistResultEnvelope(result)
  if (manifest.artifacts.length) await ctx.stageOutputs(manifest.artifacts)
  const receipt = await ctx.commitResult(manifest) // data-only也有真实完成回执
  await ctx.persistReceipt(receipt)
  // 收到真实持久提交回执后才按现有留存规则清理；不是进程退出即清
  return receipt
}
```

2026-10-25 用户授权更新（Runtime候选 `60ed1881cb6c5d2c22a547af61126d09a471137b`，仅 local-script）：用 argv 数组、shell=false 直接启动 Node；entrypoint 包内校验，输入使用真实路径，输出及 HOME/cwd 使用执行级私有目录；环境只传必要值，不继承 Provider token、宿主 HOME 或数据库凭据。不再依赖 bwrap/namespace，不承诺输入只读挂载、宿主文件/网络隔离。脚本拥有 Runtime 服务账号权限，故只允许已授权审核包。READY 仍实测解释器、输入读/输出写；身份、包/输入摘要、幂等、输出路径/结果验证保留。源码与云端/安装验收分别记录；其他 runner 的隔离不变。详见 `../archive-agent-maintenance/position-skills-contract-20261024.md` 最新授权节。

Provider runner 在受控宿主 broker 内持有凭据；包脚本不能获得原始 token。broker 验证 binding 属于当前主体，网络目的地固定于部署配置，拒绝重定向到未批准目标。脚本请求外部副作用必须经 `ctx.effects.invoke`，不能自行放开网络。

### 9.2 effects_json：避免“通用”破坏副作用恢复

每个 execution 的逻辑 effectId 稳定，例如 `generate`、`upload-reference-1`、`submit-video`。不做通用工作流，多个步骤顺序由技能 adapter 实现；平台只登记与去重。

每项：`effectDigest,bindingRevision,status(START_RECORDED|ACCEPTED|SUCCEEDED|FAILED|UNKNOWN),providerRequestId,providerIdempotencyKey,ownerRuntimeFence,resultDigest`。Provider URL/signed URL/凭据不入公共投影。

1. 准备输入/参数；在 effect start 的短事务内核对最新 scope、lease、撤销、snapshot、binding revision。
2. 不存在 effect：CAS 插入 START_RECORDED，返回仅此 claimant 的 NEW；先 fsync 本地记录再实际发请求。
3. 同 effect 重放已存在：返回 RECORDED/KNOWN/UNKNOWN，不把它重新当 NEW。进程在登记后、发出前崩溃也按“不确定是否发出”处理。
4. 支持 Provider 幂等键且语义经 adapter 证实：恢复可用同一 key/同摘要查询或幂等重发；不支持时不能重发生成，只能查询既有 providerRequestId，无法核实则 RESULT_UNKNOWN。
5. 视频类异步返回任务 ID：记 ACCEPTED，phase WAITING_PROVIDER；后续轮询属于读取，不创建第二个任务。轮询沿实际退避/网络超时，不加业务 deadline。
6. 有结果：先持久化data及实际文件manifest；有文件才上传登记。上传失败只重传相同 outputId/hash。
7. commit 成功但响应丢失：读回相同 manifest；payload 不同409；从不重复调用生成。
8. 并发两个 claimant：一个 CAS 胜出；另一个只读已有状态。后台恢复也走同一规则。

这里保证的是“本系统不盲目重复发副作用”；对不支持幂等/查询的外部 Provider **不宣称 exactly-once**。

租约到期不能让第二个 Runtime 自动重做有 START_RECORDED 的效果；恢复必须通过 current-session 的 resume 核实原执行归属。撤销后禁止新的资料读取和新副作用；已经发出的 Provider 请求不一定可取消，如实报告，不能声称退款。结果可按服务端隔离留存，但不越权发布。

### 9.3 phase 转移

```text
READY → RUNNING
RUNNING → WAITING_PROVIDER | RESULT_UNKNOWN | RESULT_READY | FAILED
WAITING_PROVIDER → RESULT_READY | RESULT_UNKNOWN | FAILED
RESULT_UNKNOWN → WAITING_PROVIDER | RESULT_READY | FAILED（仅真实查证）
RESULT_READY → ARCHIVING（通用result已提交；零文件同样成立）
ARCHIVING → COMPLETE（所需数据消息/文件索引投影完成）
READY/RUNNING/WAITING_PROVIDER → CANCELLED（确认取消；无法确认外部副作用则保留UNKNOWN）
```

输出和外部效果可以已经存在而用户不再授权发布；不得把取消投影成“什么都没发生”。所有 CAS 递增 version；终态重放只返回同结果，不退回 READY。

## 10. 通用结果、输入证据、索引与验收

### 10.1 统一结果合同

```json
{"schemaVersion":1,"executionId":"pwe_...","snapshotDigest":"<64hex>",
 "result":{"data":{"summary":"识别结果"},"artifacts":[],
   "inputReceipts":[{"inputRef":"input_1","sha256":"<64hex>","carrier":"native-image","delivery":"DELIVERED"}]}}
```

- data可以为空、字符串或schema规定的结构；artifacts总是数组。至少满足包声明的结果约束，文件技能不能用空数组假报成功。
- data不是凭证和授权，不执行其中指令。输入回执由资料桥接/执行适配器生成并绑定实际载体，不信任模型自报。DELIVERED只能证明提供给本次模型/工具，不能证明正确理解；正确性需要样例和用户结果验证。
- 大块内容按现有传输边界放文件并引用，不将视频/图片base64塞入JSON/DB。分析结果可以是中间结果，也可以直接答复用户，不强制产生文件。
- 完成/失败由服务端校验与持久状态决定；Runtime提交的是结果候选，不是任意status即可改变终态。

### 10.2 commitSkillResult具体逻辑

```text
事务外：解析严格JSON、校验输出dataSchema；有文件则复核已stage的真实字节/hash/格式
短事务：校验当前身份/lease或合法resume、task/assignment、snapshot及现有result
  同manifest同digest已提交 → 回放；同ID异payload → 409
  确认每个artifact恰好对应本execution的一条stage记录
  原子写result_manifest_json；把实际output标COMMITTED（零文件不造行）
  PWE=RESULT_COMMITTED；phase=ARCHIVING；插入既有outbox的结果投影事件
提交后：projectResultByExecutionId
  data → 持久数据结果/对应消息parts
  artifacts → 原ChatBountyAssetProjector的文件资产逻辑
  满足全部预期投影 → phase=COMPLETE
```

`ChatActionFinalService.actionProgress`、`ChatBountyAssetProjector.pending`、恢复/取消/历史读取以及Web都按protocol4的RESULT_COMMITTED读取，不把旧OUTPUT_COMMITTED作为唯一成功证据。数据-only投影可以与结果提交同事务完成时直接置COMPLETE；需要outbox时如实ARCHIVING。单一结果digest和事件键保证恢复不重复追加消息。

### 10.3 技能组合不变成新工作流引擎

分析→生成等组合由现有Agent顺序选择下一动作，不另建DAG。上一技能结果是带provenance的数据。

资料selector采用v2带tag的联合类型：现有两类文件引用加通用`EXECUTION_RESULT`，字段为`executionId,resultDigest`；服务端核对同任务/当前可访问会话、producer已提交、未撤销及精确digest。冻结快照绑定这个引用，不复制成无来源可信提示词。文件结果仍用原文件/asset引用；新来源类型按读取方式区分，不按图片/PDF/Excel格式增长。EXECUTION_RESULT读取时将已提交data以规范JSON和application/json提供，hash按冻结结果内容定义，不把JSON转换成未标来源的系统指令。拒绝自引用、未完成结果和跨Owner访问。引用失权时阻止新读取；旧结果按当前读权限展示。

默认当前任务内顺序执行组合，不自动生成并行DAG或跨Agent调度。每步单独执行记录和幂等键，整体交付沿原关联机制聚合。

### 10.4 文件交付与验收

文件真实路径containment、symlink拒绝、hash/size/格式校验保留；预览不阻塞下载，无预览器为安全附件。索引按执行定向处理，pending扫描仅补偿。界面区分处理中/结果待核实/已生成登记中/可用/失败，不等全历史索引才能展示新结果。

中间分析结果只进入对话/后续上下文，不自动算作正式成果；用户要求分析报告时可作为文本/数据交付，但是否接受成果继续走原验收状态机。`AgentTaskArtifactOutcomeServiceImpl`不因技能化改语义。

记录能力发现、资料解析、工具执行、结果提交、投影分段耗时，不设没有证据的拒绝阈值。

## 11. 配置确定方案

继续现行 `/home/isp/conf/cyf-agent-runtime-v1/`，不迁移目录，不恢复旧 apps 链接。

新增**一个**共享 `skill-bindings.json`（schemaVersion=1），保存：

```json
{"schemaVersion":1,"providers":{"image-default":{"adapter":"image-http","endpoint":"<existing-endpoint>","model":"<existing-model>","credentialEnv":"<existing-env-name>","revision":"1"}},
 "subjects":{"<existing-agent-id>":{"providerAliases":{"image":"image-default"}}},
 "costInfoOverrides":{}}
```

- profile 只新增 `skillBindingsFile` 路径引用；无 `skillsEnabled/imageEnabled/pdfEnabled/...` 一串开关。安装成功且 runner 就绪才可发现。
- 费用说明独立放共享文件costInfoOverrides，键含skillKey/skillVersion和可选binding ID，字段带informationRevision/source/updatedAt；优先级为精确binding覆盖→技能版本覆盖→包默认→UNKNOWN。信息更新不变更包/安装摘要、不递增安全bindingRevision、不使运行中的执行失效。每次执行记录当时展示的费用快照；Provider实返用量/费用分开标注为reportedUsage/reportedCost，不伪称估算为实扣。
- provider binding revision 只在端点/模型/凭据引用等有效绑定变化时递增。原始 secret 不写此文件/技能包/日志。
- 安装清单来自既有 receipt/marker，不写第二份 enabledSkills 配置。
- 当前 `controlledImageHttpEndpoint/ModelId/ApiKeyEnv/BindingId/BindingEpoch` 映射到共享 provider；新执行启用后删除 profile 的旧 image enabled/ledger 配置引用，保留旧执行日志/证据，不删历史。
- `workspace-policies.json` 保持 ACL/隔离/输出根职责，不含费用；可共用 workspace policy，但不同身份不能共用可写运行目录。
- 原typedInspection*中的实际视觉输入/工具链/网络隔离/证据映射为公共inputCarriers配置，原证据字节保留；新执行不依赖旧INSPECT业务开关；原生CHAT提供资料仍校验该请求已冻结的task/assignment/source范围和当前可读权限，不能因为取消独立操作就跳过资料ACL。相同验证元组可复用证据，不按角色名复制，不因装图片技能就宣告模型能看图。
- `SKILL.md` 不绑定 codexHome 绝对路径。Runtime 根据当前 profile 注入相对执行根；缓存/技能包升级不破坏原 typedInspection evidence。
- 运行目录复用当前每角色 HOME 与受控工作目录；临时产物在既有 workspace 根的 executionId 子目录。恢复账本含执行身份，不跨 Owner 扫描目录。
- 原 `ControlledImageProviderOperatorPolicy` 中混合的身份/binding/网络范围迁入通用策略；consent/定价/费用确认条件移除。不能通过跳过整份 policy 实现取消费用审批。

配置工具只生成候选+diff/readback，不修改当前生效 profile、不自动重启共享 Runtime。实际切换随版本化发布窗口执行。

### 11.1 包发布不能绑定应用重发

已核实当前SkillPackages仅启动时读取classpath，SkillMarketplaceService.verifyPackage又与该内存catalog比较。只把Java数组挪到classpath JSON仍要求重发后端，不能算实现“加包即扩展”。

决定：内置包继续由PlatformSkillPackageCatalog/EconomyPlatformSkillSeeder引导；一般新增技能复用既有economy_skill_product/version表、SkillPackageController下载与安装授权，包字节放API可读的不可变包存储，通过实际已有storage适配或本地受控存储实现，不由Runtime任意URL声明来获得信任。应用只配置一个packageStoreRoot（主机默认 `/home/isp/state/cyf-skill-packages`，只是设计值，本轮不建目录），目录由API实际身份读取；新技能不增加配置文件。

维护方发布逻辑为：准备并校验包/声明→以hash内容寻址写入临时对象→完整性readback→原子提升为不可变对象→短事务写既有product version并发布指针。数据库失败只留下不可见孤立对象，不产生可下载未授权包；后续按引用保留/清理，不粗暴全目录删除。新发布入口为同模块维护接口，不是新服务；限定部署维护身份/显式发布操作，普通用户和Agent不能调用。它是需要实现的受控发布路径，不冒称当前已有任意包发布能力。

SkillPackages.get按已批准版本找到实际包摘要/大小并读取store，缓存只按摘要；不在购买/安装持锁事务内读取大文件，采用事务外prepare+事务内复验现有身份/version。verifyPackage验证DB批准的不可变包事实和实际bytes，不再以“出现在启动时内置列表”作为唯一真实性依据。包购买价及权限manifest仍按既有经济合同核对，运行费用不混入。

还须修改EconomyPlatformSkillSeeder.seedProduct：仅引导缺失的内置记录；已存在原seed版本仍校验不可变内容，但合法新发布版本的current指针不能被强行改回seed，也不能因不是原version=2就启动失败。

更新某技能发布新版本，安装以版本/hash独立保存，current指针切换不能覆盖运行目录；快照绑定installationId与精确包摘要，运行中保留原版本和已授予范围，不中途替换入口。已入执行的正常版本退役与显式安全撤销分开处理。正常升级不终止任务；明确安全撤销可以阻止继续执行且给出真实原因。新增工具依赖/新runner仍需Runtime制品升级，不能承诺所有新增能力都无需发布。

### 11.2 默认自动化边界（不是费用审批）

- 用户在办事任务提出具体要求后，Agent可自动选择并调用当前已安装、已授权、真实就绪的技能；不必每步点名、不重复弹费用确认。
- 默认不自动购买、安装、升级技能；仍走既有安装/管理操作。缺技能给出真实原因，不能偷偷下载代码。
- 默认不切换Agent、不切换凭据主体、不擅改Provider绑定；若当前能力缺失，不能借另一个角色账号继续跑。
- 模型能直接读图就直接使用真实载体；工具能直接编辑就不强制增加分析步骤。以任务所需的最少步骤执行，不为每次文件读取建业务子任务。
- “自动选择技能”不等于可扩大任务目的、联网范围或读取全部历史。资料中的指令不能授权后续副作用。
- 将来若用户要求自动安装、跨Agent调度或第三方可执行包，属于明确产品范围变更；本期不用为这些未要求的功能搭系统，也不因此阻塞当前实现。

## 12. 历史与切换（无永久双轨）

1. 源代码与 protocol4、前端 action-v4、技能包及配置作为同一发布批次固定；本次不编造版本号/Flow Run。
2. 先做显式增量 DDL；旧列/数据保留，新附属表空，不批量重写历史。
3. 按现有锁协调切换窗口；禁止旧协议新接纳，已有运行自然完成或进入明确可恢复状态；RESULT_UNKNOWN 不强制标成功/失败。窗口尚未满足就不切换，不抢停。
4. 在新写入口开放前，使指定 Runtime 版本、安装技能摘要、API、Web 三端协商全部达到新协议；不为配合新页面伪造 READY。
5. 旧点名任务不需重新点名：仍 ACTIVE 的原 grant 在首次新请求时，在 task-root 下依据当前 assignment/owner 创建新版本 EXECUTE_SKILL baseline 并 supersede 旧 baseline，旧快照只读保留；旧请求 key 仍按原 admission 读回，不重新接纳。新请求来自旧页面返回明确客户端升级错误，不静默翻译旧执行语义。
6. 历史审计读取保留原摘要校验或原有持久投影；历史原始记录不改成 v4。关闭旧写路由（410/明确协议错误），删除新流量不再使用的执行分支；只读历史解析不作为旧版本执行兼容层。
7. 回退：新流量开放前可恢复同批旧制品/配置，增量表保留；开放后不可直接用旧代码消费新执行。先冻结新接纳、处理新执行和效果不确定项，再按恢复批次协调。优先前向修复，绝不恢复 Provider START 来重发。
8. 前端正式验证/制品/部署走 Flow4403172；后端固定干净源码、先读 build.gradle、经现有 orchestrator gradle 串行验证/build/validateLayering；Runtime 走其版本化安装入口。develop push 不自动发布。

### 12.1 协议错误与费用旧路由收口

旧费用 issue/consume/revoke 新请求不再作为技能调用接口；旧账本只读审计，不伪造一个永远通过的 consent。旧费用/图片桥接 UI 入口删除；用户仍可正常撤销执行/资料授权，动作落在通用执行接口。无费用授权不代表执行全部不需用户任务意图：不得凭一张图片中的指令开启与用户任务无关的副作用。

## 13. 首批技能与扩展证明

- `image-generate`：现有图片 HTTP adapter，允许0..工具支持数量的参考图；费用信息 provider-priced 以 METERED/UNKNOWN 描述。
- `image-edit`：同 adapter、不新增核心分支；接受一张任务上传图或精确会话成果。
- `text-file`：将源中已有 native text-file 执行接入，修正“有资料就不提供文本生成”的发现条件。
- `pdf-export`：维护方 local-script 包，复用源中 `toolchain/requirements.txt` 的 reportlab/PyPDF2；依赖锁定在运行环境制品；不在每次请求临时 pip install；输出 PDF 走现有格式校验。
- `xlsx-export`：第三类输出验证（图片/PDF/表格），同 local-script runner，复用现有 openpyxl，不改任务/授权/成果核心。
- 视频本期不做付费实跑；统一协议支持提交 jobId→查询→取结果。接入新视频 Provider 需要实现对应 adapter、依赖及隔离配置，而不是新建视频专用业务流程。

### 13.1 PDF/XLSX 不是重新发明工具链

已查到 RT/toolchain/delivery_tool.py 与 requirements.txt 包含 PDF、XLSX 生成/解析库。首期复用其制品依赖，不另加一套 Python 环境。不过现有 create_pdf 会把内容转 ASCII replacement，不能把这个占位行为作为中文文档验收。

- pdf-export 参数固定为 `title:string, paragraphs:string[]`。脚本用已锁定 reportlab 在包内指定 CJK 字体（`assets/fonts/NotoSansSC-Regular.ttf`，入制品时带实际许可与SHA）绘制真实Unicode文本并分页；字体未就绪则依赖不可用，不能静默替换为问号。默认不执行HTML/JS、不获取外链字体；原始用户“生成要求”不是交付正文。实际正文由Agent参数提供、用户可复核。生成后用已有解析工具检查页数/文本，人工查看中文render fixture。
- xlsx-export 参数固定为 `sheets:[{name:string, rows:[{cells:[{type:'text'|'number'|'boolean'|'formula', value:<对应类型>}]}]}]`；type/value联动用标准schema和脚本业务校验。openpyxl 写入真实值，text 以文字单元格存储，不能让 `=...` 自动变成公式。formula 仅在明确任务意图下采用，拒绝外部工作簿/外部连接；不生成宏。重新加载核验 sheet/cell/value，不以文件存在判通过。
- 这两个技能只是首批受支持的内容范围，不声称覆盖任意复杂排版/财务模型。新技能以独立包提供自己的参数与脚本并升包版本，不改变平台接口。

每个包本身的业务生成逻辑与最小 fixture 由实施任务完成；核心接口、费用边界、状态和交付方式已经固定。依赖缺失明确安装/构建，不在运行时擅自下载或回退到高权限环境。

## 14. 实施与证据边界

详见 tasks.md 的直接代码任务及 acceptance.md。每包预计20～30分钟主动工作，非硬超时/完工承诺；超范围拆剩余实现，不再新增规划阶段。首次定向失败先定位；同输入同根因两次后停止盲重试。

本轮只修订设计并执行本地文档结构校验，没有新增技能、跑 Provider、改生产配置、执行 DDL、构建、发布或停机。Runtime 源/线上差异、远端/线上版本未核验的事实保留在 handoff，不能用设计完成冒充系统已修复。


## 澄清决定收口

原核对2026-10-13；不是新的实现/发布结果。跨账号承办由本设计授权边界修订和外单合同控制，“不自动跨账号”不等于拒绝用户已授权外单。

### 已确定，不再让用户选择技术细节

| 问题 | SE-1的不足/歧义 | SE-2确定的处理 |
|---|---|---|
| 读取 vs 理解 | INSPECT_INPUTS固化顶层路由 | 读取是公共资料接口；模型原生理解无需额外业务动作；专用分析是普通技能 |
| 技能 vs 工具 | 所有技能被要求执行manifest；native-file仍按产物命名 | 普通SKILL.md保留；可调用技能才有执行manifest；runner按运行方式而非文件类型划分 |
| 无文件结果 | 执行成功仅认OUTPUT_COMMITTED | 统一data/artifacts结果，protocol4采用RESULT_COMMITTED；零文件不造空文件、不等待文件索引 |
| 自动步骤 | 可能默认先识别后编辑 | 根据任务与真实能力走最少必要步骤，可直接读图、直接编辑；专用分析按需执行 |
| 扩展时发布 | classpath JSON还是要求后端重发 | 内置包保留seed，新增普通包走已有市场记录+不可变包存储；需实现受控发布，不宣称现有链路已支持 |
| 参数协议 | 私有cyf-params-v1、Java/JS双手写校验 | 标准JSON Schema固定方言、库校验+共同fixtures；禁远程ref/隐式转换，避免新增一套方言 |
| 费用变动 | 描述随不可变包变动就要升级包 | 独立描述覆盖与信息版本；不影响安装/安全binding版本，不审批、不预扣；报价/未知/Provider实返费用分开 |
| 版本与升级 | 当前指针升级可能毁掉在途旧版本 | 包按版本/hash不可变存放，运行中固定旧版本；正常升级不改旧执行，安全撤销另行处理 |
| 组合执行 | 分析结果如何成为下一步输入不清楚 | 精确引用上一执行的resultDigest，校验来源/ACL；已有Agent顺序组织，不新增DAG平台 |
| 输入证据 | 提供给模型容易被表述为理解正确 | 交付记录只证明本次输入提供，正确识别/正确修改必须用结果验收 |
| 数据/文件/验收 | 生成、登记、被用户接受可能混淆 | 分开状态；中间结果不自动正式交付；生成不等于验收 |
| 恢复与费用 | 防重可能被误认为继续做费用控制 | 防重是执行正确性；取消费用审批不删除恢复账本。未知外部副作用如实保留，不盲重发 |

## 产品侧默认边界（可按用户后续明确要求改变）

1. **自动调用已安装技能：允许。** 用户下达任务后，Agent自动选择已授权/就绪技能，不必用户点名技能，不增加逐次费用确认。
2. **自动购买、安装、升级：默认不做。** 使用已有管理/安装入口；缺技能明确说明，不能下载任意代码补能力。
3. **跨Agent、跨账号、自动换Provider：默认不做。** 在当前任务角色和批准绑定范围内执行；不能借其他角色凭据偷偷完成。
4. **第三方任意可执行包：本期不开放。** 先维护方受控包，避免为未要求场景建设审核/沙箱市场。
5. **复杂并行工作流：本期不建设。** 顺序技能组合和异步Provider任务恢复已覆盖当前需求。

这些默认值不阻塞实现。若用户希望改变自动安装或跨角色边界，需明确变更；不是要求用户再审批整份架构。

## 2026-10-23 管理生命周期增量（待实施）

[管理缺口与实施方案](management-gap-analysis-20261023.md)补充现行设计：源码已允许image-edit1.1.0多格式，但实际吴用仍装1.0.0；后端同skillKey重复购买保护与Runtime同名安装保护均不是升级实现。复用现有市场/不可变包/命令outbox/安装回执/Runtime registry，新增明确的升级准入及原版本保护，不删除防重复保护或手改安装清单。具体跨端字段、DDL与迁移在M2冻结后实现，不把目标设计当现行线上合同。


## 2026-10-24 恢复兼容修正

旧命令先按当前DTO解析会使已完成历史记录因缺TaskSkillBinding阻塞新任务。现改为只读历史分类后执行准入、单execution异常隔离；新增字段保留摘要但不传入runner权限。详细规则和代码落点统一见[管理合同兼容章节](management-contract.md#2026-10-24-执行命令兼容与恢复分类最新授权)，覆盖本设计中与本次兼容范围冲突的旧切换说明。基线ec9ac757，候选未上线；不重放旧UNKNOWN，不拓展其他模块兼容。
