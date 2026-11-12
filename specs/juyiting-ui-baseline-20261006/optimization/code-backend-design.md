# 代码级详设：后端、合同与持久化

> 2026-10-23整理：本文保留原日期源码/设计定位，不按旧排期执行、不从“待实现”文字推断当前代码。当前范围与交互见 [spec.md](spec.md)，剩余工作见 [tasks.md](tasks.md)，后续成果多选及历史稿验收见 [最新详设](../../juyiting-external-commission-mvp/design.md#selected-output-acceptance)。发布/验收独立查证。

2026-10-18；**目标实现设计，不是现有接口说明或上线记录**。基线为 `code-baseline.json` 中本轮fetch固定的develop。Owner及范围沿原handoff。项目接口标准：`api/docs/interface-standard.md` v1.2；旧生产结论仍是10月17日，不因本轮读源码重标。

本文件将原详设E01中的主链选择收口到目标方案。2026-10-18源码二次推演发现并修正10项缺口，详见[source-design-review.md](source-design-review.md)；其中v5跨端合同/真实DB探针必须先通过，不能把文档当可运行证据。标“新增”的类/路由/字段现在不存在；按本文件建立，不需要实施者重新选择业务架构。编译、真实数据库事务及真实Agent回归仍是实施验收，不以文档替代。

路径约定：`chatSvc`=`api/chat/jia-chat-service/src/main/java/cn/jia/chat/`；`agentSvc`=`api/agent/jia-agent-service/src/main/java/cn/jia/agent/`；API/mapper/core路径在表中写明。行号随修改变化，以类/方法名定位。

## B0. 本轮发现与固定决策

| 代码事实 | 本次决定 |
|---|---|
| `ChatSelectedOutputFinalizationService.submit()`依次prepare/submit/accept | finalization仅准备并提交；人工决定独立，自动链不得调用accept |
| `ChatFinalizationWire.receipt()`和SQL `chk_csof_terminal`强制COMPLETED=TASK_COMPLETED | 明确区分“提交操作完成”和“事项完成”；改wire、约束、消费者与测试，不能只删一行accept |
| `AgentTaskReworkExecutionServiceImpl.createLocked()`要求PUBLISHED工作空间输出 | 不将文本伪装为workspace file；新增Chat侧统一review operation，要求修改和原议事接续在同一事务中完成，复用Agent决定服务 |
| `useFormalDeliveries`只在内存生成决定key；控制器校验key但未将其传入决定服务 | 新UI统一走有持久幂等记录的review operation；原决定CAS仍是领域权威，不误称现有key已有完整日志 |
| `ChatActionFinalService.persist()`已有明确deliverable与事务；现有outbox有fence/重投 | 使用同一outbox新增内部事件，不从浏览器watch自动POST、不新增轮询框架 |
| TASK执行已有正式提交；CONVERSATION结果是候选，不自动等于正式交付 | TASK沿已有正式服务；聊天只有明确交付意图才提升。普通RESULT_COMMITTED不直接待验收 |
| 顶部已有`TASK_CREATE`草稿分支，默认入口却是私人CREATE | 新入口接到现有正式草稿；后端共用原子创建服务，避免重复造创建API |

## B1. 创建：两种编辑形态，一个正式保存事实

改动：`agentSvc/service/impl/HallRequestDraftServiceImpl.java` 的TASK_CREATE提交分支、`agentSvc/service/impl/HallTaskCreationServiceImpl.java`、`api/agent/jia-agent-api/src/main/java/cn/jia/agent/service/HallTaskCreationService.java`，复用`AgentTaskCreationOperationController`与`AgentTaskCreationOperationServiceImpl.create`的v2命令；Web接线见前端详设F1。

1. 保留首页即时创建与顶部账号草稿两种**存草稿方式**，但创建正式事项均委托已有v2原子创建服务。不要强求二者共用同一个HTTP路径而删除持久草稿。
2. TASK_CREATE提交原事务中：锁定owner域草稿/revision → 校验未提交/当前内容 → 从title/instruction/inputs映射创建命令 → 调用原子创建服务 → 保存submissionRef和TASK回执。不得另一次独立POST再标草稿已提交。
3. 字段映射：`editableFields.title→title`，`instruction→description`，每个固定`inputs.fileId/version→attachments`的现行v2输入结构；targetAgentId/outputMime不得成为TASK_CREATE预指派/执行授权。materialScope等严格沿`hallRequirementCreateIntent.requirementMaterialsBody`和服务端v2 DTO，不能复制原型样例字段。
4. 幂等：正式草稿提交key继续绑定草稿ID、revision和冻结命令；草稿提交操作已有受理记录时先重放原回执。首页`useHallRequirementCreate`沿原key/body恢复，不能又调用draft.submit。两入口全局未决互斥只防当前账号并发操作，不能将一个入口未知转成另一个入口新任务。
5. 旧CREATE/REVISION草稿仍属PRIVATE_CASE；打开旧草稿不改kind，原样保留独立权限和提交语义。新正式入口不自动克隆旧私人资料；资金榜保持既有费用/资金资格，排除于普通创建改造。
6. 开始办事成功返回同一taskId后即待点将；指派仍复用`point-and-deliberate`及bootstrap outbox。不新建“确认承办后保存”接口。

具体修复现有拦截：`requireTaskCreate()`目前拒绝非空inputs、title>30和instruction>200；`HallTaskCreationServiceImpl.create()`重复该限制并直接调用agents.createTask。不是改入口就自动支持完整需求。

- 将HallTaskCreationService.create签名改为`create(OwnerScope scope, String creationKey, String title, String description, List<InputSelection> inputs)`（目标签名，get不变）；调用方只此TASK_CREATE支路及测试同步更新。
- adapter改注入`AgentTaskCreationOperationService`，构造`CreateCommand(2,title,true,description,true,List.of(),true,null,refs)`；refs每项`InputReference(fileId,version,"INPUT")`，版本按现有固定int范围。creationKey=`hall-task-`+SHA256(长度前缀scope/draftId/submissionKey/revision)，短于100；不拿用户原key跨命名域复用。
- `requireTaskCreate`移除源于旧task_plan截断的30/200硬拒绝和inputs为空限制；仍保留草稿现行title≤200/instruction≤20000等真实字段限制及Agent/outputMime必须null、sourceRef/conversationId禁止。v2完整requirement snapshot是原始需求权威，task_plan摘要不是完整需求。回读同时断言requirement snapshot与资料链接精确一致，不再强求task_plan短摘要等于长正文。
- 资料授权/固定版本验证和链接写入由原子创建服务执行，任一失败连同草稿提交标记一起回滚。测试补200字标题、超过200字正文、多资料及撤权回滚；不扩大为旧私人草稿迁移。

## B2. 提交操作：方法级改造

### 文件与函数清单

| 既有文件/符号 | 改动 |
|---|---|
| `chatSvc/service/ChatSelectedOutputFinalizationService.java` `submit/apply/validateView/stageRank/receipt` | submit在正式submitted后终止；删除推进ACCEPTING和调用agent.accept的分支；apply可将SUBMITTED映射为操作completed，不能触发任务完成；保留源校验、reconcile先于过期版本校验、CAS、失败恢复 |
| `chatSvc/api/ChatFinalizationWire.java` `receipt` | 新操作成功为`state=COMPLETED, stage=SUBMITTED`，含固定deliveryId；taskState是提交时事实，不表示已完成。新写只允许PROMOTING/READY_TO_SUBMIT/SUBMITTED；现有promotion的MAX_SAFE_INTEGER/SQL范围本次不顺手扩大；以十进制string解析并显式校验该域现有上界，不先转JS Number再比较，review Long与promotion域边界分别验证 |
| `chatSvc/api/AgentTaskSelectedOutputFinalizationController.java` `submit/byRequest/byOperation` | POST成为“正式提交”，成功200、受理未完202；GET只查，不执行编排；更新接口目录和错误说明，不保留旧submit+accept写路径 |
| `chatSvc/service/ChatSelectedOutputFinalizationStore.java` `create/advance` | 仍用原operation/item表及stateVersion CAS；新增按scope+task+delivery查操作的只读方法，支持来源闭包 |
| `api/agent/jia-agent-api/.../AgentSelectedOutputFinalizationService.java` `accept` | 删除活动调用入口与实现的accept/acceptLocked自动决定职责；prepare/submit/reconcile继续复用；领域人工决定只走正式决定服务 |
| `agentSvc/service/impl/AgentSelectedOutputFinalizationServiceImpl.java` `committedView` | 已有提交重放不重新索取过期lease；读取已accepted/changes_requested的历史事实不再次决定；返回交付ID及现状供恢复，不转新操作 |
| `chatSvc/config/ChatSelectedOutputFinalizationSchemaInitializer.java` | 核验新约束/索引；不能只改CREATE IF NOT EXISTS而漏掉已安装表 |

**操作完成回执不可当动态事项快照。** 新finalization一旦COMPLETED即保持提交成功快照；后来人工验收/返工由正式交付读模型呈现。提交已经成功但Chat保存回执失败时，重放先查Agent正式交付，再补操作完成，不把“已经被验收/要求修改”误判为未提交。

### 持久化约束变更

文件：`api/chat/jia-chat-mapper/src/main/resources/db/chat-selected-output-finalization-v1.sql`；新增独立升级资源`chat-selected-output-finalization-submission-v2.sql`（新增设计）。

- 保留原state、stage、固定来源、摘要等列，不批改历史成果；B3.1的contract_version/正式artifact来源是额外增量列与约束。新写成功允许`state=completed, stage=SUBMITTED`。
- `chk_csof_progress`对SUBMITTED允许delivery_state为submitted/accepted/changes_requested：仅用于崩溃后核对到提交已存在、决定已发生的真实事实。
- `chk_csof_terminal`改为：completed时必须delivery_id非空、无error且retryable=0；stage=SUBMITTED且delivery_state属于上述三值，或历史stage=TASK_COMPLETED且accepted+task_state=completed。其他stage不得completed。
- `chk_csof_outcome`继续校验failed必须有error；不得放开空delivery成功。TASK_COMPLETED/ACCEPTING保留**历史数据可读**，新操作不再写这两个stage，不提供旧协议续跑分支。
- 增加普通索引`idx_csof_delivery(tenant_id,owner_jiacn,client_id,task_id,delivery_id)`；不要用更新阶段前查全表来替代索引。
- 升级器先information_schema读前值并比较目标定义；有同名异构约束直接报告，不静默跳过。升级/降级方案见B8；本轮不执行DDL。

## B3. 系统自动提交：可靠事件，而非前端推断

新增`chatSvc/service/ChatDeliverySubmissionService.java`，方法：

```java
void enqueue(PreparedDeliveryCandidate candidate, long now); // MANDATORY，同final持久化事务
void consume(ChatDeliberationOutboxService.Claim claim);     // 事务外编排，短事务落各阶段
SubmissionProjection read(Scope scope, String taskId, String operationId); // 只读
```

`PreparedDeliveryCandidate`是服务内不可变记录：scope、taskId、assignmentRevision、conversationId/generation、requestId、turnId、outcomeId、finalDigest。没有浏览器提供的owner/lease/存储URI。

1. 在`ChatActionFinalService.persist()`成功插入ANSWER outcome且`deliverable=true`后，**同一事务**插入事件`DELIVERY_REQUESTED`。已有重放返回分支不重复插入，消息/final回滚则事件一起回滚。
2. 事件ID=`delivery-submit-`+SHA256(长度前缀UTF-8编码的tenant/client/owner/turnId/finalDigest)的前48位小写十六进制；总长64，匹配既有outbox.event_id VARCHAR(64)。消息修改事件ID=`review_`+其域隔离SHA256的前57位；同样总长64，不扩DDL、不截断入库。新增eventType长度在已有varchar(30)内。payload只含固定引用，读取时重验scope、binding、消息正文摘要和明确标记，不信payload自带授权。
3. `ChatDeliberationOutboxRelay.deliverClaim()`新增DELIVERY_REQUESTED分支；复用claim/续租/fencing/sent/retry/dead。不能让现有default判死；消费方就绪后才打开事件生产。耗时源读取期间按既有续租模式，失锁后不得ACK。
4. `consume`重新读取`ChatActionFinalService`权威outcome/来源目录；借`ChatCompletedMessageSourceService.resolve`、execution source校验构造固定selectedOutputs。完整集合由有效deliveryRelation及已验证deliveryTargets确定：保留未被REPLACE的项、替换明确指向项、增加明确APPEND项；来源唯一且同任务/指派，禁止只取最后一文件或扫描所有历史附件。
5. 纯文本ANSWER有deliverable且无关系时，作为该轮单项候选；存在当前submitted批次时，**不自动替换/拒收**。返回`DELIVERY_REVIEW_REQUIRED`并保留候选供原议事说明；用户明确要求修改后新轮次才可提交。
6. TASK模式`PersonalWorkspaceExecutionServiceImpl`已有`submitFormalDelivery`等正式发布链，沿用其deliveryId；禁止再生成第二批次。CONVERSATION模式媒体的OUTPUT_COMMITTED/RESULT_COMMITTED仅候选：通过同一议事后续明确交付ANSWER及deliveryTargets提交，没有交付标记就不待验收。
7. 消费时仅对活跃当前指派且无未决修改的事项生成新操作；key用事件ID稳定派生，第一次固化expectedTaskVersion，恢复读已有operation命令，**不能随重试换版本/摘要**。
8. 调用finalization新提交语义，不调用accept。成功提交并读回后sent；临时存储/网络失败原事件retry；scope/来源撤销、事项终态或当前批次冲突明确记录失败原因，不伪成功。允许人工“核对提交”读取原操作；恢复只发送同一事件/意图，不扩大权限。
9. 用户关闭浏览器后仍可提交，页面刷新只能GET。已完成历史消息不批量补扫生成新事件；切换仅处理新合同下新产生事件。

### B3读投影的实施合同补充（2026-10-19）
原议事typed-outcome的公共**展示DTO**升为schemaVersion=6（不是模型outcome v5，也不改写历史final摘要）；在原有全部字段外增加必填`submissionProgress`，非明确交付ANSWER/历史无事件/开关未开启时为null。没有v5/v6活动双轨；Java wire、Web严格parser和测试一起切换。
非null字段恰为`eventId,operationId,state,dispatchVersion,operationStateVersion,deliveryId,errorCode,retryable`。state仅PENDING/COMPLETED/FAILED；eventId为原稳定事件，operationId在操作尚未创建时null，两个版本为各自持久CAS十进制string（操作尚未创建则operationStateVersion=null）。COMPLETED必须有operation/delivery且无error、retryable=false；FAILED必须明确error、retryable=false，不允许因读取超时/DB错误合成失败。
读取必须核对原final/binding、exact事件payload/身份、当前事项owner、原key/operationId/冻结命令摘要；只读，不claim、不consume、不POST、不改变final。已落COMPLETED操作可先于outbox ACK展示提交成功；SENT没有提交回执、跨域事件或身份矛盾均报告持久化错误，不能拼假成功。未知/内部错误原因归一为公开`DELIVERY_SUBMISSION_REJECTED`，不把存储异常正文暴露给页面。
Web同一final合并独立校验dispatch/operation单调版本、稳定operation/delivery及终态不可倒退；静态消息final不变。错误文本显示在原答复下方而非输入框，现有刷新只GET，绝不在watch中重新提交。

### B3.1 部分替换/跨话头的固定来源闭包

不能把旧话头文件重新贴成新请求的outputId绕过`resolve()`同话头/代际检查。对已正式交付的未修改项，复用其**正式artifact**作为新批次来源；明确新增如下内部合同：

- `AgentSelectedOutputFinalizationService.SourceOutput`增加服务内union分支`FORMAL_ARTIFACT`：`sourceDeliveryId/sourceArtifactId/sourceArtifactVersion/contentHash`，其余Chat消息/执行定位字段为null；公共finalization请求仍只接受当前既有两种选择，不能提交这个受信分支。
- 新`ChatDeliverySubmissionService.resolveCandidate`读取前一批已要求修改的正式manifest，将保留项映射为FORMAL_ARTIFACT，新生成项仍走COMPLETED_MESSAGE/OUTPUT。旧来源的同task/scope/固定版本、父决定changes_requested以及新请求VerifiedDeliveryBasis都必须吻合；旧成果可读不等于可任意作为其他任务输入。
- `AgentSelectedOutputFinalizationServiceImpl`增加受信来源解析：沿现有artifact读服务读固定字节/摘要/MIME，再经新操作正常publish/submit；不复用原work-item租约，不覆盖旧artifact。新manifest同时记录父delivery和各项原固定来源，保留REPLACE/APPEND链。
- `ChatSelectedOutputFinalizationStore.Selection`与item表增加nullable `source_delivery_id/source_artifact_id` varchar(100)、`source_artifact_version` int>0；source_kind新增FORMAL_ARTIFACT。该分支只有上述三列＋sha256/title/purpose必填，request/step/output/turn/message/snapshot/final_digest均null；已有两个分支必须新列全null。更新nullable request_id及其CHECK；主键item_order仍固定序列，新增源唯一性由提交规范化集合校验并加`(scope,operation_id,source_delivery_id,source_artifact_id,source_artifact_version)`唯一索引，不删除原两种源唯一索引。
- `SelectedOutputFinalizationDigest`新增明确v2规范化计算（按source_kind标记、固定字段顺序、长度前缀UTF-8，不排序用户可见成果序列），operation表增加`contract_version` smallint NOT NULL，旧记录值1、新写仅2；manifest schemaVersion新写2。v2精确顺序：put字符串`MMD_SELECTED_OUTPUT_FINALIZATION_V2`→taskId→putLong(expectedTaskVersion)→putLong(expectedAssignmentRevision)→conversationId→summary→putLong(items.size)；每项依次put(sourceKind)、requestId、stepId、outputId、sha256、title、purpose、turnId、messageId、snapshotId、finalDigest、sourceDeliveryId、sourceArtifactId，再putLong(sourceArtifactVersion或-1)。put沿现有实现：null编码有符号big-endian int64 -1，非null为UTF-8字节长的big-endian int64＋原字节；数值big-endian int64。非本分支字段必须null，元素不能null。v2计算不得用旧摘要函数忽略新增来源。原v1只读审计，不重新解释或续跑；迁移须更新两个服务的schema initializer与真实DB测试。
- Agent侧`agent_selected_output_finalization`也增加contract_version（旧1、新2）并更新`AgentSelectedOutputFinalizationSchemaInitializer`/`agent-selected-output-finalization-v1.sql`及新增升级资源；冻结命令摘要/源摘要与manifest生成同步支持新source union；不把B4的batchSha256当promotion digest混用。权限、版本、字节验证失败整批不提交，不默默丢掉保留项。
- 如果新结果完全替换旧批，只有新来源，不强行引入FORMAL_ARTIFACT。一个父批次只能对应已成功修改决定后的明确新轮次；新话头只看历史不创建新轮次。

替换关系由每个新RESULT实际producer admission的固定catalog及其parentOutcomeId/持久lineage证明：必须回到同一COMMITTED修改操作；每个新结果恰有一个被选中的正式目标输入，目标去重且全集覆盖。纯文本替换还要求原目标为text/*。单个输出引用多个目标、同一目标对应多个输出、漏目标、跨修改操作或无固定来源均整批拒绝，不通过按顺序或按数量猜测替换关系；多目标可由逐项目标明确的独立生成结果构成。该规则不要求浏览器增加选择分支。

新增测试必须覆盖三项只替换一项、跨话头保留旧固定项、源被撤权、同artifact不同version，以及新摘要缺字段/顺序变化。该内部union和迁移是C01/C03的一部分，不留给UI临时保存文件绕过。

## B4. 统一人工决定：文本与文件同一事务接续议事

新增（Chat依赖Agent API，不反向依赖Chat service）：

- `chatSvc/api/AgentTaskDeliveryReviewController.java`
- `chatSvc/service/ChatTaskDeliveryReviewService.java`
- `chatSvc/service/ChatTaskDeliveryReviewStore.java`
- `chatSvc/config/ChatTaskDeliveryReviewSchemaInitializer.java`
- `api/chat/jia-chat-mapper/src/main/resources/db/chat-task-delivery-review-v1.sql`

### 目标HTTP合同（新增）

| 路由 | 含义 |
|---|---|
| `POST /agent/tasks/{taskId}/delivery-review-operations` | 仅用户显式ACCEPT；REQUEST_CHANGES只从内部受信v5 final产生 |
| `GET /agent/tasks/{taskId}/delivery-review-operations/request` + Idempotency-Key | 查原操作；404不证明未受理，不自动换键 |
| `GET /agent/tasks/{taskId}/delivery-review-operations/{operationId}` | 查原操作及原回执，GET绝不推进执行 |

2026-10-19实施核对补充：两条操作GET在读取持久记录前都必须以当前可信scope重新核对实际事项根的owner；终态原回执不豁免当前授权。保留原回执不变，不以查询触发决定；根不可读时返回不可见，数据库失败不可伪装成404或重建操作。

请求data**全部字段必填，允许空的字段显式null**：

```text
schemaVersion: 1 (number)
deliveryId: string 1..100
expectedTaskVersion: canonical decimal string >=0 (Java Long范围)
expectedDeliveryVersion: canonical decimal string >=0
expectedAssignmentRevision: canonical decimal string >=0
batchSha256: lowercase 64 hex
decision: ACCEPT  // HTTP只接受此值；内部operation另有REQUEST_CHANGES
conversationId: string 1..100 | null
conversationGeneration: positive decimal string | null
instruction: string | null
sourceSelectors: array
```

- ACCEPT：conversationId/generation/instruction=null，sourceSelectors=[]；不要求验收者打开原话头，必须有事项验收权和当前批次。
- REQUEST_CHANGES的来源、正文、话头和目标全部来自内部BoundRevision及持久快照，详见B4.1；公共HTTP收到该decision返回400，不允许客户端模拟Agent提议。
- 长整数全程string/Java long/BigInt；不调用现有safeFinalizationVersion转换造成截断。交付物artifactVersion/workItemVersion等在新增投影也用decimal string，现行内部Integer仍做范围检查；不得改变历史摘要字节。
- `batchSha256`只校验冻结集合，不作授权。算法固定：`SHA256(UTF8(JSON.stringify(["hall-delivery-batch-v1",taskId,deliveryId,deliveryVersion,items])))`，items为按artifactId UTF-8字节升序、再按artifactVersion数值排序的`[artifactId,artifactVersion,lowercaseContentHash,purpose]`数组，版本均十进制string；purpose保留原Unicode/null规则（本合同必为string）。Java用无额外空格、非ASCII不转义的数组序列化；用同一fixture证明与JS逐字节一致。items包含该正式交付的完整items，不能因界面隐藏manifest而少验收一项。
- Idempotency-Key沿现有合法字符长度8..100；scope来自认证。公共请求/响应使用标准Q/R信封，useHttp只解包一次。

成功data固定字段：`schemaVersion, operationId, taskId, deliveryId, decision, state, stateVersion, taskState, taskVersion, deliveryState, deliveryVersion, requestId, sourceRequestId, conversationId, errorCode, retryable`。

`state=COMMITTED`时：ACCEPT对应taskState=COMPLETED/deliveryState=ACCEPTED/requestId=null；REQUEST_CHANGES对应taskState=RUNNING/deliveryState=CHANGES_REQUESTED/requestId非空，requestId为子请求、sourceRequestId为原请求，表示子执行可靠受理而不是Agent已产出。状态版本正string，task/delivery版本非负string，requestId/conversationId按上述决定允许null。持久业务失败为`REJECTED`并有errorCode/retryable=false；事务外失联没有假FAILED回执，由客户端UNKNOWN核对。活动进行中操作`PROCESSING`返回202；已提交200；失败HTTP与标准错误一致，失败响应不夹成功receipt，GET可查持久REJECTED事实。

### 持久化结构（新增表，目标DDL规格）

表`chat_task_delivery_review_operation`：

| 列 | 类型/约束 |
|---|---|
| tenant_id, owner_jiacn, client_id | varchar(50)，binary collation，NOT NULL |
| operation_id, task_id, delivery_id, idempotency_key | varchar(100)，binary collation，NOT NULL |
| request_sha256, batch_sha256 | char(64) ascii_bin，NOT NULL |
| request_json | mediumtext，NOT NULL且JSON_VALID，冻结规范化data，不放token/lease |
| decision | varchar(24)，ACCEPT/REQUEST_CHANGES |
| state | varchar(16)，PROCESSING/COMMITTED/REJECTED |
| state_version | bigint非负，初始1，CAS增长 |
| receipt_json | mediumtext nullable，COMMITTED/REJECTED必须有效JSON |
| created_at, updated_at | bigint毫秒非负 |

本表还必须增加B4.1/source-design-review.md §3.2规定的origin/source/target/child列与条件CHECK，不可只照本基础列清单建表。

主键`(tenant_id,owner_jiacn,client_id,operation_id)`；唯一`(tenant_id,owner_jiacn,client_id,task_id,idempotency_key)`；普通索引`(tenant_id,owner_jiacn,client_id,task_id,delivery_id,updated_at)`。FK遵循现有同域策略，不添加跨库级联删除。不同key重复决定仍由领域delivery version CAS拒绝；同key异body返回409。

### 事务/锁及函数顺序

```text
accept(scope, taskId, key, command):
  validate ACCEPT-only wire; freeze digest; replay same key/body
  persist PROCESSING admission
  independent-bean REQUIRED transaction:
    lock root → operation → delivery/work item
    validate current scope/versions/exact batch
    decide(accepted) + COMMITTED receipt atomically
  transient failure: rollback decision, retain recoverable original operation
  same-key same-body POST resumes PROCESSING; GET only reads
  deterministic rejection: persist REJECTED after rollback
```

自然语言修改不走此HTTP流程，走B4.1的outbox消费者；新增`admitDeliveryRevisionContinuation`代替旧设计`admitPreparedRevision/resumePreparedRevision`。原工作空间文件返工服务仅保留其独立TASK用途，新议事UI不另发decide/createRework。

**普通输入的明确性（2026-10-18更新）**：无引用也可明确要求修改；引用仅定位，不能授权返工。正文统一受理一次；Agent解释语义，后端控制状态，前端只展示。具体入口与事务差异见下节B4.1。

### B4.1 自然语言修改：不可变父请求＋复用USER的子执行

本节经源码复核重写，废止“恢复原request/REVISION_READY后继续生成”的旧设计。`ChatDeliberationService`的final与typed outcome不可变，不能重新打开父请求。

1. typed admission同事务冻结当前交付快照；Agent活动v5输出`REVISION_REQUEST`，不是自由调用后端方法，更不是EXECUTE_SKILL。结构、摘要、来源表及三端落点见[source-design-review.md §3](source-design-review.md)。普通问答/澄清保持待验收；有批次待验收时无COMMITTED修改lineage不得先执行生成/修改工具。
2. `ChatActionFinalService.persist`将父final与`REVIEW_REQUESTED`写入同一事务。新增`ChatTaskDeliveryReviewService.proposeRevision(BoundRevision)`只接受已验证持久源；浏览器不得直接调用REQUEST_CHANGES。
3. outbox消费在事务外准备固定包，再按root→operation→binding/conversation→delivery/work item→outbox顺序重新校验。决定、子CHAT admission、dispatch、COMMITTED回执和fenced SENT同事务。永久冲突明确拒绝，暂态错误复用原事件重试。
4. 新增`ChatDeliberationService.admitDeliveryRevisionContinuation`（MANDATORY），复用`admitInspectionContinuation`的真实USER复用能力，但route为CHAT、独立新request/turn，lineage为DELIVERY_REVISION。父request/turn/final/摘要不变；子ID由scope+operation确定，不再插用户消息。
5. 回执`requestId`为子请求，新增`sourceRequestId`为父请求（ACCEPT两者null）；前端通过独立reviewProgress跟踪子请求及交付，不把父完成当事项完成。后续新成果使用决定后版本、新lease和有效grant；旧批次不覆盖。
6. 新DDL需加入typed review-context快照表和review origin/source/target/child字段；内部摘要冻结来源和目标，不复用B7 ACCEPT摘要。v5 declaration、Runtime parser/model schema、Java validator/SQL、Web strict parser及跨端fixtures是C01必需范围。
7. 明确修改仍来自用户消息；Agent解释可能出错，后端只保证合法来源、权限、版本和执行一致性，不宣称语义绝对正确。歧义通过原议事澄清；验收永远显式点击。


## B5. 交付读模型：同批次、可预览、可恢复

新增`chatSvc/service/ChatTaskDeliveryReviewReadService.java`与上述Controller GET：
`GET /agent/tasks/{taskId}/delivery-review-context`（scope与task验权，仅读）。

data字段：`schemaVersion=1, taskId, taskVersion, taskState, assignmentRevision, currentDelivery, history, pendingOperation`。currentDelivery无当前批次为null；历史分页沿服务端已有正式交付读取边界，不无界扫描。currentDelivery结构：
`deliveryId, deliveryVersion, state, batchSha256, summary, submittedAt, items, allowedActions`。

所有version/revision/generation均canonical decimal string，submittedAt为非负安全整数毫秒；taskState/交付state采用大写枚举。history每项与currentDelivery结构相同，history不含当前批次。pendingOperation=null或`{operationId,kind:SUBMISSION|REVIEW,state,stateVersion,errorCode,retryable}`；SUBMISSION state使用PENDING/COMPLETED/FAILED，REVIEW使用PROCESSING/COMMITTED/REJECTED，以kind分派，不混同事项状态。

item固定字段：`artifactId, artifactVersion, contentHash, purpose, displayRole(RESULT|MANIFEST), source, unavailableReason`；unavailableReason正常为null。source是严格union（FORMAL_ARTIFACT为内部保留项的新增读来源）：`{kind:COMPLETED_MESSAGE,requestId,messageSource:{turnId,messageId,snapshotId,finalSha256}}`、`{kind:CONVERSATION_OUTPUT,requestId,stepId,outputId}`、`{kind:WORKSPACE_FILE,fileId,version}`、`{kind:FORMAL_ARTIFACT,sourceDeliveryId,sourceArtifactId,sourceArtifactVersion}`；MANIFEST可以source=null且unavailableReason=null（通过正式artifact授权预览）；RESULT未能解析来源则source=null且unavailableReason=`SOURCE_UNAVAILABLE`，只读显示不可预览原因，不造URL。正式artifact的预览仍沿已有身份/权限检查后的读取服务，不能凭来源映射放宽ACL。

- 来源从Agent不可变manifest/已存操作items映射并逐项比对，不从`allItems.at(-1)`或当前话头推导；manifest也是正式items时计入完整摘要，但RESULT数量只算真实成果。
- 读取root/交付/操作关联应为同一数据库一致读快照；无法证明一致时返回冲突/核对提示，不拼接不同版本生成allowedActions。history与current不重标旧submitted为当前。history为与currentDelivery同结构的数组（不重复currentDelivery），沿现有正式读取最多100项的已知边界；超过现有服务可读取范围返回明确不可用，不截断为假完整。分页扩展不隐式承诺。根completed时currentDelivery可为最后accepted批次，allowedActions仅VIEW。
- `allowedActions`限定`VIEW, ACCEPT, REQUEST_CHANGES, CHECK_OPERATION`；任何终态/未决冲突/来源不完整不得开新写；按钮隐藏不是服务端授权替代。
- pendingOperation按scope/task返回原operationId/state及查询入口，不泄露幂等key或instruction。GET不恢复操作，浏览器恢复需显式动作及原冻结意图。

## B6. 四状态的查询和计数，不在30条前端分页中凑总数

改动路径：`AgentController.searchTasks`/status-counts，`AgentServiceImpl.searchTasks`及计数方法，`api/agent/jia-agent-core/.../AgentTaskSearchDTO.java`，`AgentTaskMetaDao`/Impl、`AgentTaskMetaMapper`当前搜索条件。

- 新增查询字段`phase`，取`PENDING_ASSIGNMENT|IN_PROGRESS|PENDING_ACCEPTANCE|COMPLETED|HISTORY|UNKNOWN`，可不传；与旧raw status不能同时传，冲突400。旧status供内部诊断，不是新增用户状态。
- SQL共用owner域root与current delivery关联谓词，然后归一化CASE；不是只按raw status：open→PENDING_ASSIGNMENT；planning/assigned/running/blocked→IN_PROGRESS；reviewing→PENDING_ACCEPTANCE；completed→COMPLETED；failed/cancelled/archived→HISTORY；其他→UNKNOWN。不把后端没有的claimed/queued当根枚举补入。
- 根reviewing却无当前submitted/关联矛盾：读模型覆盖为UNKNOWN并给核对原因；这类异常的phase查询/计数使用同一关联条件，不允许列表显示未知而待验收计数照加。completed交付缺失同理保留根完成事实但验收数据标未核对，禁写，不伪造未完成。
- 原计数响应扩展为明确`phaseCounts`与`rawStatusCounts`，两者scope/keyword/ability相同；数值是合法计数，接口标准定义为十进制string以避免SQL COUNT bigint精度损失。所有消费者同时改，不兼容猜字段。
- root status仍保留，phase是读模型；历史分类保留raw status/结束原因。PRIVATE来源不加入正式TASK合计，不泄露他人事项。

### B6.1 概览来源与事项列表一致（2026-10-19实施收口）

- `HallReadService.ItemSummary` / `HallReadWire` 对 `TASK` 明确返回 `phase`，取值与 B6 相同；私人及其他来源不借用正式事项phase。`HallReadSql` 复用 `AgentTaskPhaseSql.PHASE`，列表、计数及概览不各自从 raw status 猜测。
- 当前交付批次不唯一、关联矛盾等保留 `UNKNOWN`；即使 latest-only join 找到一个 submitted，也不能给UNKNOWN附上可验收 `review`。只有 `PENDING_ACCEPTANCE` 且真实reviewReady才能返回review。
- 正式schema关闭时不能查询不存在的正式表；只保留根COMPLETED/HISTORY事实，其余UNKNOWN。Web缺失/非法/与状态矛盾phase时隔离TASK来源错误，不影响其他来源，不回退猜字段。UNKNOWN入口“核对事项”，只读，禁止验收/续写。
- 验证要求：真实MyBatis/MySQL对同一owner域的逐页事项、phase筛选、分组总计及概览逐项相等；另测并存两个submitted不可被latest-only join洗成待验收。此要求不等于当前正式测试已通过，精确提交与Run见任务证据。

## B7. HTTP、摘要与失败合同

新增目标错误码：`DELIVERY_REVIEW_BAD_REQUEST`400、`DELIVERY_REVIEW_FORBIDDEN`403（或资源防枚举404）、`DELIVERY_REVIEW_NOT_FOUND`404、`DELIVERY_REVIEW_CONFLICT`409、`DELIVERY_REVIEW_IDEMPOTENCY_CONFLICT`409、`DELIVERY_SOURCE_UNAVAILABLE`409、`DELIVERY_REVIEW_STORAGE_UNAVAILABLE`503；未认证401由现有安全层。错误无成功data，无stack/资料内容。

完整成功/失败信封及batch摘要字节样例见`code-contract-fixtures.json`。通用Q/R由既有拦截器/JsonResult/ApiJsonResponses负责；Controller不再包一层data，Web移除useFormalDeliveries的循环解包，统一useHttp后仅一次业务解包。`requestId`与Idempotency-Key不混同。

请求摘要使用`SHA256(UTF8(JSON.stringify(["hall-delivery-review-v1",schemaVersion,deliveryId,expectedTaskVersion,expectedDeliveryVersion,expectedAssignmentRevision,batchSha256,decision,conversationId,conversationGeneration,instruction,canonicalSelectors])))`，含所有null、完整instruction和sourceSelectors（selector先经现有codec验证，字段按键名UTF-8顺序递归转为`[[key,value],...]`，数组保持原顺序），不含认证token、requestId；scope/key在唯一键域绑定。同key另一个delivery/版本/正文必须409。fixture不是生产ID或真实用户内容。三个摘要各有用途：batchSha256冻结验收集合、review request摘要冻结人工操作、promotion v2摘要冻结受信晋升来源；严禁相互代替。

## B8. 迁移与切换清单（实施项，不是本轮操作）

1. 固定当前schema和所有消费者，更新`api/docs/interface-catalog/http-chat.md`、`http-agent.md`及对应schema/完整wire fixture；现有规范未授权的全局重构不借本任务扩展。
2. 新建review operation表，升级finalization约束/索引；更新initializer的已安装检查和新建检查。Flow干净MySQL验证fresh install、旧真实结构升级、重复升级、同名异构失败；DDL会隐式提交，不能承诺事务回滚。
3. 旧ACCEPTING/未决submit+accept记录按统一规范v1.2的切换规则备份并隔离，禁止新代码自动续跑；历史已完成只读。不为旧协议建立续跑兼容层、不删除业务成果/账本。正式停止/切换要走实际发布授权，不把规范历史授权当本轮可操作许可。
4. 同批API/Web消费者就绪后切换；事件消费分支先具备，再生产DELIVERY_REQUESTED；旧页面资产不得调用新语义后仍提示“已验收”。缓存/资源版本由版本发布处理，不能长期运行两套合同。
5. 回退先关新增入口/事件生产并保留所有原始记录；只在代码能读新schema和新submitted事实时允许恢复旧候选。否则修复前进，不把新submitted删掉来适配旧代码。操作表与已发生人工决定不得回滚为未执行。

自动提交的永久失效必须记录可查询拒绝并fenced结算，不得被relay通用catch无限重投；暂态故障才重试。自然语言新提交的批次、版本、lease、scope和来源冻结规则见源码推演R05/R09。


### 2026-10-19 发布后异常修正进度
WebSocket增量内容校验必须区分空串与纯空白：publishAgentMessageDelta改isBlank→isEmpty，空格/换行/制表符保留原文及序号；ACL、回调绑定、版本和连续性检查不变。参数化认证身份测试补4类空白，候选c59311a1d8；Flow157未取得执行证据，尚未上线。生产318片段原文未留存，不把推导当作该片段实证。
证据与源码基线：`../evidence/reply-followup-diagnosis-20261019/verification.md`。


### 2026-10-19 最新正式验证状态（13:01 CST）
Web59ba8a8 / Flow4403172/232 SUCCESS（3054通过、2pending，构建/扫描成功）。API cd2146f408e692fc58424390e89a40d2f10eb7d2 / tree b757d4cf1b4d3c1b864a2be47106ba0e0b734d56 / Flow5260799/161 SUCCESS（2420项中2325通过、95跳过、0失败/错误；分层检查及fresh bootJar成功）。此前Run159的5项失败已由Run160错误回执定位：旧normalizer误要求requestId/messageId相等，注册被拒绝；已修正两种身份的混用，并覆盖17项normalizer、1项command wire和5组分片回归。不改ACL、运行时证明或序号连续性，不通过改相同ID回避问题。
源码已集成develop，未部署；制品仅有Flow元数据，尚未独立下载验包。Runtime重复回复“收到。”及完整生产议事/验收闭环仍待解决，不标整体方案完成。本次不改变页面/交互，无需另改原型。完整证据：specs/juyiting-ui-baseline-20261006/evidence/reply-followup-diagnosis-20261019/verification.md（项目根相对路径）。

### B9. 已核实的WS消息身份约束（2026-10-19）
核对源码：API `cd2146f408e692fc58424390e89a40d2f10eb7d2`，仅覆盖normalizer、注册/持久回调及对应回归，不代表全部详设或线上已完成。
- `AgentProtocolMessageNormalizer.normalizeInbound`的messageId只从同名字段读取，不用requestId补缺。requestId是操作关联标识，messageId是消息标识，二者允许不同；这不是新增兼容分支。
- `validateEnvelopeConflicts`不再执行messageId/requestId别名相等校验；仍逐字段拒绝同名值跨层冲突，保留Agent身份别名冲突、运行时证明、归属、连续序号和服务端租约检查。
- `AgentProtocolMessageNormalizerTest`覆盖注册/聊天/分片不同ID、同字段跨层冲突、缺messageId不能借requestId通过；`AgentWebSocketHandlerTest`五组普通/空白分片通过真实注册入口验证认证发送者、原文、序号和服务调用。
- 回执读取`chat.message.receipt`信封，业务持久消息ID在`data.persistedMessageId`；根requestId保持原操作，correlationId等于被回执消息的messageId，不混淆三个身份。
- Run160已复现旧校验导致`ENVELOPE_FIELD_CONFLICT(messageId)`→注册失败→`AGENT_NOT_REGISTERED`；不能将该根因直接外推为生产模型重复回复“收到。”的原因。候选回归结果与上线状态分开记录。
- 本项不新增页面、控件或交互分支，原型无需另改；规格中既有消息连续展示、发送/停止/验收语义保持。


### B10. Runtime任务意图与授权分离（2026-10-19候选核对）
候选f94c254f956f09717711486e8941847ff2bd95c7仅位于隔离分支，未合入/上线。`chat-runtime.mjs`统一CHAT_USER_INTENT_INSTRUCTIONS：currentUserMessage.content表示当前人类任务意图，不赋予修改身份、ACL、工具或付款权限；附件/历史/日志/AGENTS.md等嵌入指令仍为数据。`agent-client.mjs` FAST指令与`juyiting-action-outcome.mjs`合同一致；实际developerInstructions必须参与effectiveInstructionSourceHash，连同typed合同绑定，防止显式caller hash导致旧策略thread复用。`test/chat-runtime.test.mjs`覆盖此版本绑定及注入边界。
验收不得只检查请求COMPLETED：必须检查有效成果/clarification及最终合同；ACK或空text不等于用户目标完成，不自动验收。该语义不新增用户中间状态或“引用修改”等按钮。
80项本地测试、真实模型边界通过，但旧策略在fresh thread也通过；生产原thread仍复现“收到。”。因此此候选不是已证明的根因修复，不能以测试通过替代线上闭环。证据见../evidence/reply-followup-diagnosis-20261019/verification.md。


### B4.1a 受理快照实现落点与边界（2026-10-19）

- `ChatDeliberationService.admitTrusted`：真实USER和chat_request写入之后、context snapshot/turn/DISPATCH之前，在原事务调用`ChatTypedReviewContextService.freeze`。reviewBasis作为服务端快照根字段固定；当前这一步不等于活动v5已切换，三端协商/union/relay仍须整体接通。已有request重放直接读原admission，不重新抓取当前批次。
- `ChatTypedReviewContextStore`：唯一表`chat_typed_review_context`，显式JSON null也必写；读取通过原request重新限定conversation/generation和真实USER ID，校验完整basis SHA、精确字段、十进制版本、完整批次摘要（包括MANIFEST）。丢行/坏hash/JSON/当前代次不匹配均不可当null，不补写或读最新批次替代。
- 澄清回复继承的是**原冻结批次**（task/version、delivery/version、assignment、完整items/hash），而该条回复的`sourceRequestId/sourceMessageId`必须绑定本次实际受理的USER和request，不能沿用父消息冒充本次来源。旧批次无/有与当前不一致、版本/摘要变化即冲突，不静默rebase。
- pending操作、暂不可预览不会把现有SUBMITTED批次变为null；普通问题可固定原批次并继续等待验收。basis只是定位不是执行/拒收资格，最终领域决定仍重新验权及校验allowedActions/源与版本。
- `ChatActionDispatchService.consume`：包准备前核对原冻结basis，根/绑定/话头/outbox锁内再次核对；无正式修改lineage时，受理于待验收批次的EXECUTE_SKILL一律拒绝，Agent自称只读无效。当前根reviewing或完成/失败/取消/归档/未知状态也不受理新工具子执行。后续v5修改子执行须经COMMITTED决定后独立受理，不能通过放宽此检查复用父请求。
- store/service/schema共同沿`chat.delivery-review.enabled=false`默认关闭，不新增用户开关或另一套活动协议。新增快照表仅在`cyf.chat.delivery-review-schema.allow-additive-migration=true`且已确认fresh缺表时可加建，已有异构表、弱CHECK/索引/FK/非InnoDB直接报错；本次不在生产开启或执行DDL。
- 新增轻量codec/受理/guard/schema测试在现有`src/test/java`普通test任务执行；已有selected-output专项继续mmdU3Finalization，不另建runner或测试框架。真实MySQL原子/竞争与三端v5闭环仍是独立未完成验收，mock顺序不能替代。

### 2026-10-19 编码收口补充（当前候选，待统一Flow）
- MESSAGE_REVISION拒绝不伪造权威状态：根不存在/已撤权时只落原来源操作的REJECTED审计与fenced SENT，不修改业务根。内部拒绝receipt的taskState/taskVersion、deliveryState/deliveryVersion允许成对null表示不可读；公共ACCEPT回执不放宽。根可读但原批次消失，只交付投影成对null。终态重放仍校验原摘要，不创建child。
- typed child admission两个摘要字段沿既有表合同使用`sha256:`前缀，review操作摘要仍为64位hex，两域不能混用。Outbox event_id固定不超过64字符，不靠DDL放宽。
- 替换关系由同一COMMITTED修改操作和每个实际producer冻结输入证明：精确delivery/artifact/version/hash/parent final；不按数量或顺序推测。每个输出对应一个目标，全部目标恰好覆盖；多目标单输出无法证明时整批拒绝。EXECUTE子admission沿已选sourceRefIds只保存实际选中catalog；公共FORMAL_ARTIFACT selector仍禁止。
- 统一MySQL回归复用JuyitingWorkflowMySqlTest：真实领域决定、Chat续请求/DAO、原USER复用、typed admission、receipt和fenced ACK共同事务；receipt写失败、失去fence、并发ACCEPT、根缺失均覆盖。测试仅冻结模型final与外部能力输入，不把这些替身当真实Provider端到端。

### 上线启动依赖补充（2026-10-20，API f0eb7e1bb9，待本轮Flow验收）

- 实际开启`chat.delivery-review.enabled`后，提交链必须避免`Deliberation → ActionFinal → DeliverySubmission → SelectedOutputFinalization → Deliberation`的启动注入环。`ChatDeliverySubmissionService`经`ObjectProvider<ChatSelectedOutputFinalizationService>`在outbox消费的提交阶段获取服务；入站final事务只持久化提交意图，不提前解析/调用提交器。
- 不允许设置`spring.main.allow-circular-references=true`规避。`ChatWorkflowBeanGraphTest`在review及selected-output门同时开启、循环依赖关闭时组装真实8个workflow服务，正/反初始化顺序都应通过；数据库/外部服务边界mock只用于装配测试，不替代原28项真实MySQL事务回归和上线启动健康检查。
- 发布源及嵌入编排ledger都必须绑定同一commit/tree；生成配置后应从**落盘YAML重新解码**验证工具包SHA及ledger，而不是只验证生成前变量。云端拒绝早期基线/摘要不一致不算执行过测试，不允许放宽校验重试。
- Flow启动失败时核验真实旧JAR摘要、配置恢复、实际进程和健康；旧版恢复不代表新版本上线成功。详情保留原handoff及release证据，不重标整体方案完成。

### 2026-10-20 发布复验补充
API `a7b7270b5e6bbce80acfb1f037f75977af96d9aa` 已通过 Flow189 并安装；前述启动循环修复的正式 bean 图双序测试均通过。API1.16.12/Web1.16.12/Runtime新payload已上线，不代表端到端验收完成。
PC真实事项468暴露前端导航/上下文收口问题：创建完成回调打开详情后，快捷入口又打开点将册；选将确认后进入议事须消费临时选将层而非叠加。另真实 `enterBountyDiscussion` 会同步清空 `selectedAgent`，原通用watch将内部切换误判为外部目标变更而失效当前bootstrap。修复只豁免受控调用中的同步“原候选→空”转换，身份/授权代次和后续用户选人仍失效旧回执，禁止放宽全局fence。前端跟进1.16.13，原测试事项沿原request继续，不重复点将。

### 2026-10-20 实际上线复验限制
已部署不等于详设全链路已实现。当前生产API189/Web246/Runtime8a9742a，真实流程发现交付提示更新、待验收上下文409、事项容器空白和重复只读重同步四项OPEN；详见 `../evidence/implementation-20261019/production-release-20261020.md`。修复需沿既有事件/作用域/幂等机制，不用新增全局轮询、放宽grant执行资格或移除身份fence掩盖问题。自然修改与最终用户验收尚未完成真实验证，保持未验收状态。

#### 2026-10-20 主流程缺口修复（候选03901c3385，未标线上验收）
- LIVE02只在currentFollowupContext只读元数据投影允许reviewing。调用方唯一为议事上下文GET；不修改admit/resolveFollowupBaseline/付费或图片授权，不新增执行权限。保持owner/target/assignment/requirement/active grant核验。
- LIVE01在原提交完成后，任务根事务内持久化delivery_submission_completed并settle原outbox SENT；任一步失败同事务回滚，重试仍是原提交key。事件绑定原final digest、request、conversation/generation及deliveryId，只作为重取提示。ObjectProvider延迟解析Deliberation避免重引入启动注入环。无DDL、无Runtime协议变更、无全局轮询。
- 正式候选包含原完整回归及AgentTaskExecutionGrantServiceImplTest；真实PC/mobile流程未完成前不标交付。

- 补充提交 `0afd50f70ebd839dc1ac9be1ee71d50e525baf8f`：仅持久化事件不足以通知当前 SSE 连接。`ChatDeliverySubmissionService.consume`须返回事务已提交的事件；`ChatDeliberationOutboxRelay`通过既有`publishPersistedEvent`发布。不得在根事务提交前发布，不重新生成事件身份；断线仍走原持久事件重放。正式候选 API1.16.15/Flow191，结果待核验。

#### 2026-10-20 主流程Runtime真实回报缺口（f30cb5a）
- 实测澄清后模型将CLARIFY结果错误当作可关联交付父节点；无合法deliveryParent时，模型输出schema必须将deliveryRelation限定为null，不允许事后放宽服务端关联校验。Runtime `buildActionOutcomeContract`新增显式deliveryParent输入，由已冻结的typedDeliberationAdmission提供；无父节点不能从话头或history推断。
- 自然修改模型返回REVISION_REQUEST但text为空；schema此前允许空串、Runtime语义校验却拒绝。text schema添加minLength=1，并明确各kind都要有非空用户可见说明；不修改成果或审核权限，不伪造说明补全模型回报。
- 源码`/home/isp/wsps/chcbz/isp-install` f30cb5a18219308393bd175939bc5f56cc89db9d，38项定向Runtime回归通过，既有安装器生成独立制品并验证66个payload文件、配置闭包后切换，未改Runtime身份/配置/数据库。真实重新发送及验收仍待收口。

### 2026-10-20 剩余验收：停止与流式delta并发
生产474实际点击停止返回409，原因是delta持续递增stateVersion。取消接口增加可选十进制字符串expectedLastDeltaSeq，与expectedStateVersion配对；仅current=STREAMING、expectedVersion<currentVersion、0<=expectedDelta<currentDelta且version差=delta差时允许原用户停止意图，其他冲突保留。仅有delta字段、非法/溢出/未来值拒绝；旧版本单字段仍严格CAS。取消仍在原身份/会话代次/turn锁内，持久取消和outbox同事务，终态不覆盖。新增服务和HTTP回归；前端成对取同一turn快照，无自动重试。

剩余异常收口：Runtime已发送recovery_required/errorCode，但既有ACK接收只确认dispatch而丢弃业务失败。限定ACTION_OUTCOME_INVALID/UNION/KIND、DELIVERY_PARENT/TARGET_INVALID、SELECTION/PARAMETERS_INVALID这七类确定的模型契约拒绝，经可信session fence和原dispatch/message/turn/Agent/owner/会话代次核对后写FAILED与持久resync_required事件，事务后实时发布，刷新原request聚合；不伪造final，不把TURN_ACCEPTANCE_UNKNOWN或任意网络错误当失败，不覆盖终态。
Audit：实测typed-outcome/review路径115字符而生产core_log.uri=VARCHAR(100)，导致丢失整条访问遥测。仅超长已脱敏URI以28字符前缀+#sha256:+64位摘要记录（总100），普通URI原样；明确这是有标记的摘要不是完整URI，不改权限或交易审计、不扩大数据库字段、不做DDL。

### 2026-10-20 剩余验收：资料队列消息的响应脱敏边界

线上已证实 Runtime 收到八字段事件，`correlationId/code/msg` 均为 null；不是业务命令或授权错误。`SensitiveResponseBodyAdvice` 调用反射型 `SensitiveDataSanitizer`，忽略 `ProtocolMessage` 的 NON_NULL 序列化声明。限定修复：仅 ProtocolMessage 的这三个 null 回复字段省略，事件仍五字段、回复仍八字段、data:null 保留；嵌套敏感数据继续脱敏，不给路径添加 AllowSensitiveOutput，不放宽 Runtime 严格解析。回归须包含 Advice 后的序列化及原对象不变；真实队列恢复、文件执行本身分别验收，不能用解码通过代替文件成果完成。

### 2026-10-20 11:06 CST：历史执行阻塞的实际归因（未修复）
核对源码API0620837a97、Runtime2f0518de38；只读证据留在`/var/tmp/cyf-remaining-implementation-20261020/`，不修改生产记录。

1. 材料恢复：任务459两条冻结记录的typedDeliberation.schemaVersion=4、admission.schemaVersion=2；当前`juyiting-action-outcome.mjs:resolveActionChatRequest`只接受schemaVersion=5，`agent-client.mjs:recoverMaterialsChat`因此缺失action绑定而拒绝。原失败原因分别为ACTION_SOURCES_INVALID、TURN_FAILED。不是所有普通CHAT误路由，也不是本次模型超时。不得把冻结v4改标v5或增加旧版兼容；以新v5正式测试验证当前路径，历史记录处置须通过有授权的原取消/撤销入口，保留原失败证据，不直接删文件/改DB。当前未证明重连调度外的无限定时重试。
2. PRIVATE队列：两条protocol1 QUEUED执行的`queuedCommand()`生成pwe_cmd_命令，但RuntimeQueuedCommand缺correlationId/expiresAt/D06原始绑定；只读精确commandId查询，`agent_command_delivery`均0行。仅补字段仍会被`AgentCommandAckServiceImpl.lockDeliveryByCommand`以ACK_DELIVERY_NOT_FOUND拒绝。完整修复须在PRIVATE命令生产事务接入既有D06 delivery/outbox/inbox及session/身份/到期绑定，queued wire消费同一原始命令；不在Runtime伪造授权，不用新TASK成功掩盖PRIVATE失败。
3. PRIVATE修复验收必须包括：新执行durable admission→wire→当前session ACK→原执行状态→文件成果；重复ACK、过期session、跨身份、未知投递结果及取消竞争保持既有门禁。历史QUEUED不能直接补伪delivery；需先明确原记录安全撤销/重新提交路径，保持用户意图与幂等。此项跨服务事务工作未完成，不列入前端候选的已修复范围。

### 2026-10-20 SSE持久回放溢出修正（本批限定范围）
- 核对基线：API `0620837a97f48e01a613a436f33b06ea862f043e`；生产474原会话1760458006513，11:54:11/11:54:41服务日志明确bounded queue overflow，随后已提交的SSE响应无法再编码JSON错误；浏览器原生fetch报HTTP2协议错误。不是仅凭模型耗时推断。
- 根因：认证的`ChatController.conversationEvents`将持久历史`Flux.fromIterable(replay)`、ready及durableCatchUp整体包进`ChatStreamPolicy.bounded`；其`onBackpressureBuffer(64, ERROR)`向上游无限请求，MVC慢消费时历史事件先灌满队列，导致流异常结束。
- 修复：该认证入口直接`ChatStreamPolicy.firstFrame(stream)`，让持久回放/补齐遵循下游需求；保留broker既有有界live hint缓冲、持久序列补齐、500分页、租户/主体/世代校验、cursor和doFinally关闭订阅。不得调大64、改全局legacy policy、增加定时轮询或自动重发。首帧仅观测，不强制超时。
- 回归：真实controller的128历史帧零初始需求→逐条request，128帧live缺口补齐→逐条request，零需求取消释放，以及MVC实际编码完整128帧后ready；原跨身份/非法cursor/大整数/媒体与取消回归保留。测试状态以本批Flow报告为准，源码新增不代表通过。

### 2026-10-21 统一已有成果提交（开发中，未发布）
基线API c09fd09e86ef775c91b21acf63847079c9186c79；公共接口规范固定v1.2。
- 扩展现行v5 interactionOutcome union：`SUBMISSION_REQUEST`。不新增任务状态、HTTP接口、数据表或按MIME分支。消费者必须先支持新union，Runtime最后激活；严格旧消费者不允许接收新kind，不设双解析。
- 字段：非空text为操作说明，不是RESULT；deliverable=false；clarification/action/revision=null；deliveryRelation={mode:SUBMIT,parentOutcomeId,parentFinalDigest}，禁止target字段。仅引用冻结deliveryParent；没有parent或已有reviewBasis时禁止生成此意图，缺信息用CLARIFY。禁止关键词直改状态。
- ChatActionOutcomeContract/Runtime双端校验联合类型；ChatActionFinalService验证冻结parent+全量retained targets，SUBMIT不增加、重置、替换任何成果。提交说明不创建文字成果。deliveryTargets沿精确因果链重建原有text或EXECUTE结果，格式无关。
- 沿原final事务写DELIVERY_REQUESTED outbox；ChatDeliverySubmissionService消费ANSWER的真实文字交付或SUBMISSION_REQUEST的已有成果引用，复用同一finalization、ACL、根锁、assignment/generation、摘要、幂等、失败回执。禁止直接写REVIEWING/COMPLETED；验收仍由用户通过现有review operation执行。
- 新增格式仅修改生成/预览适配，普通文件无预览不能阻断交付。一次选择是一条已核实成果链，不默认合并独立根、不选最新；事项480须用户明确选择。
- 验证：纯文字、单媒体、多独立根、混合成果、精确修改后重交；错误parent/digest/跨身份/未完成/待验收重复提交；断线幂等恢复；SUBMIT自身不增加文字artifact、不调用生成技能；正式Flow及生产PC/移动端实链未完成不得标完成。
- 源码核查补正：存在DB `chk_chat_typed_outcome_kind`枚举CHECK，必须在原schema initializer锁内扩展SUBMISSION_REQUEST；fresh SQL同步。无新增表/列，但不是“无DDL”。升级须校验旧精确约束和其余catalog，DDL前保存SHOW CREATE TABLE；有新kind记录后不可盲目回退旧约束。Runtime声明outcomeKinds须同步；API先切换会暂时将旧Runtime标UNSUPPORTED，必须安排短暂协调切换，不能谎称零影响。

#### 发布前核验与切换边界（2026-10-21 17:45，尚未上线）
- 候选 API `21c32034b4b60cad497db5640966fdd7635d44b8` / Flow213：2749 tests、122 skipped、0 failures/errors；新增真实 MySQL 旧v5 CHECK迁移回归通过（原30项suite）。验证包含关闭迁移不改表、显式允许后保留记录、重复执行幂等、其余catalog漂移时DDL前失败。该测试不代表生产已迁移。
- Web `6c350fbaa81263aff90f23027fe2250a62f1df83` / Flow277：3186 passed、2 pending、0 failures；PC1440/移动390原型选择器在工具栏后，无横向溢出，无默认批次；未选阻止发送、显式选择及三种提交回执展示已本地核对，非线上端到端证明。
- 生产配置当前关闭 `cyf.chat.typed-deliberation-schema.allow-additive-migration`。现有F06/E05专用运维工具不能冒用于typed CHECK迁移，不绕过其摘要/权限检查。实际生产完整catalog和DDL快照、恢复点尚须核实，不能因测试通过直接开启所有schema迁移。
- 切换前：固定前后端发布版本、源码与同Run制品；准备Runtime1.2.2独立制品（不覆盖1.2.1）；盘点共用实例各subject在途任务/ACK/未知结果。不得清队列或重提消除阻塞，不自动选事项480的成果。
- 协调步骤：保存实际数据库完整catalog/SHOW CREATE及应用配置和Runtime一致状态恢复点；仅通过经过验证且持有共享schema锁的typed initializer变更精确kind CHECK，维持其余schema迁移开关关闭。若以短时启动配置授权该initializer，必须绑定本批固定候选、只允许预检确认的差异，并在启动核验后恢复配置原值/readback；具体生产执行载体未核实前不执行。API与Runtime严格声明同步切换，前端随后开放新入口；旧Runtime短暂UNSUPPORTED不能报为零中断。
- 切换后分别验证：实际JAR/网页/Runtime源码摘要；typed readiness与新声明注册；吴用独立测试事项已有成果提交→真实deliveryId→用户验收、自然修改后重交、断线重复回执，PC/移动端同一闭环。纯媒体/混合/修改链仍需真实链路证据，不用原型、单测或服务active冒充。
- 恢复边界：新kind写入后不得恢复旧CHECK或让旧消费者读取新union；保留新业务事实并前向修复，禁止旧DB快照覆盖新提交/验收。没有新业务写入时亦须核对旧二进制、catalog与状态相容性后才能恢复。

#### 2026-10-21 18:31发布状态补充（非全量业务验收结论）
API1.16.21/21c32034已由Flow5260799/214部署；Runtime1.2.2/5e8742a已协调激活并重新注册。Flow214部署前精确调用原initializer完成typed kind CHECK迁移，完整catalog前后校验；迁移开关仍false、无业务DML，备份保存在`/home/isp/baks/cyf-submission-kind-flow-214/`。这更新上节“尚未上线”历史状态，恢复边界不变。API正式2749执行/122skip/0fail，MySQL30pass。业务真实测试495已点将，PDF能力不匹配返回CLARIFY后改用授权独立图片测试；尚未证明真实SUBMISSION_REQUEST到人工验收闭环，不把CI与健康替代业务证据。版本/制品/切换证据详见原handoff18:31节和`/var/tmp/cyf-media-delivery-20261021/`。

#### 2026-10-21 18:40真实提交暴露的事务边界缺口（修复中）
独立495已产生真实图片EXECUTE RESULT_COMMITTED；自然提交得到SUBMISSION_REQUEST（无action、无新成果），但DELIVERY_REQUESTED消费在`ChatActionFinalService.readActionIfPresent → verifyDeliveryRelation → listConversationOutputs → task root FOR UPDATE`报MySQL1792/25006 READ ONLY。根因是直接outbox调用没有HTTP读接口已有的读写事务，final读取方法开启readOnly；已有mock单测未覆盖Spring代理+MySQL锁组合。
修复限定：`readActionIfPresent`与同样重建媒体父链的`loadAction`改为原REQUIRED读写事务；混合文字读取的外层`ChatCompletedMessageSourceService.resolve`同步，避免外层只读覆盖内层声明。不移除FOR UPDATE/ACL、不改REQUIRES_NEW/NOT_SUPPORTED、不清outbox或更换key、不补造文字成果。补现有MySQL suite的实际事务代理/锁/回滚与只读反例；此回归验证事务边界，不冒充完整媒体内容集成。发布后由原事件自然重试，同一图片无需重生成；当前仍未完成验收。

#### 2026-10-21 19:01补漏验证结论
事务修复53a29aca08a804f08a1012294c9130b209b33cbc已随API1.16.22/Flow215正式发布；MySQL33项通过、总2752执行/122skip/0fail。真实495原outbox无需人工重提即恢复SENT，submissionProgress COMPLETED，正式唯一RESULT与原图片hash相同；测试人员通过原UI确认后ACCEPTED/COMPLETED。此前18:40“修复中”更新为主链路通过。混合文媒/自然媒体修改重交尚未做本批生产实链，不用事务代理回归冒充。详见production-parity-release-20261021.md的19:01节及最终release-receipt.json。

### 2026-10-21 19:32 原生资料修改回执重放补漏（修复候选，未上线）
496混合文媒正式提交已成功；自然修改生成合法REVISION_REQUEST且精确只指向图片RESULT，但后台loadRevision重验final时硬编码rawReceipt=null，丢失该CHAT实际持久化的inspectionInputReceipt，原生资料authority非空导致TYPED_FINAL_INVALID_JSON。普通页面读final传递原receipt，故页面可正常显示修改意图而后台不能续办；不是模型格式错误。
- 修复仅ChatActionFinalService.loadRevision：按其他final读入口重放持久化receipt，继续验证来源、binding、finalDigest、reviewBasis、catalog及event；增加同一v5存储封包键集/版本检查，不跳过证明或补造receipt。
- 在原ChatActionOutcomeV5Test增加真实loadRevision/真实validator嵌套回归：带原生图片、无资料、缺失/篡改receipt、合法但不同engineTurn导致摘要变化、错误封包、错误事件payload。仅storage mock，不能冒充真实完整事务验收。
- 不改wire/Runtime/前端/DB；纯后端校验补漏无需改交互原型。新Flow精确候选验证通过后原REVIEW_REQUESTED事件自然恢复，不重发/清队列/重生成。剩余自然媒体修改及验收仍待生产闭环。

### 2026-10-21 续核结果：修改回放与保留项闭包

上述receipt修复510b2937已随API1.16.23/Flow216发布，新增7项真实reader回归通过（存储替身，不冒充端到端）；生产496原REVISION_REQUEST事件恢复SENT，固定旧正式图片输入→新修订图→SUBMISSION_REQUEST→保留旧文字FORMAL_ARTIFACT→新批→人工验收的实链通过。新批只含新图和原文，原文hash不变，2次EXECUTE总数为初始+修改；结果与B3.1一致，不因Agent多问一次澄清而重生成文字。正式验收证据/版本/剩余忙态恢复问题以production-parity-release-20261021.md的20:25节为准，后端成功不代替前端所有恢复路径验收。
