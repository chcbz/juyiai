# 自然议事、typed final 原子落库与澄清续办合同 v1

冻结：2026-10-01；API基线87c0/tree35fd，Web1993，Client2f69。继承typed Client v1、API validator v1/v1.1和长期详设；本合同覆盖业务接线，不标实现/验收已完成。原38项源码证据不代替本合同验证。

## 1. 必须完整实现的闭包与兼容边界

同一会话自然DISCUSSION → 本轮可信typed snapshot → 原生结构化final → 正文/union/问题/提议/event/outbox同事务 → 同身份刷新恢复 → CLARIFICATION_REPLY按pending CAS创建新的普通CHAT request → 后续自然答复。执行提议只能成为独立v3 preview/ack/issue/admit的输入，不能授予grant/consent/START。明确已授权首轮生成仍可直接EXECUTE。

- 现有RequestView/TurnView、请求目录及旧 /chat/stream不增加必选字段，不改wire。
- 旧text-only admission/final按原语义工作。正文、用户JSON、代码块不能重解析成typed结果。
- 不复用grant-bound ChatInteractionStepStore/step_execution_link表示问题或提议。
- server属性 `chat.typed-deliberation.enabled=false` 为默认；不开启Provider、不改真实库。功能能力与schema准备就绪必须实际读取；不可只按flag/Agent接应标签声明READY。
- 本轮范围含语义讨论、选定资料目录、澄清、建议与恢复，不假称已经INSPECT；图片/音频/文件的真实读取在既定完整范围继续闭环。

## 2. 可信typed请求、资料目录和runtime能力

服务器锁定owner/client/tenant/task/assignment/conversation/generation后，查询同作用域、确切Agent当前唯一live已注册session的typedDeliberation声明。仅modern durable CHAT、bounty、READY及完整frozen声明可开启；不借旧session/profile/presence或legacy fallback。离线、歧义、UNAVAILABLE时新typed admission明确503（不能伪报完成）；plain兼容不变。声明解析及session注册/移除hook由同一个完整闭包Owner实现，Handler需等当前75path Owner明确交接后再写。

facts.typedDeliberation只由server写，四键精确继承Client合同（schemaVersion/referenceMode/supportedOperations/availableSources）。本輪supportedOperations必须来自当前目标真实声明及原实现operation子集；有目录≠已读内容，有能力≠授权。NONE需要sources=[]，AVAILABLE是经过ACL校验的目录而非物化。

可选sourceSelectors使用既有受控来源选择语义：每项恰六键 `kind,fileId,version,purpose,assetId,assetRevision`；TASK_LINKED_WORKSPACE_VERSION仅fileId/version/REFERENCE有值，CURRENT_CONVERSATION_ASSET仅assetId/assetRevision有值，其余null。引用上限沿既有16域，ID和版本沿已有精确域，不接受URL/path/hash/producer/grant。服务器按当前task绑定资料/会话已提交资产解析精确版本、MIME/hash/producer，与源目录opaque sourceRefId建立冻结映射；private lineage不能由模型或浏览器指定。映射随本轮snapshot持久，后续执行重新查证，不以只读目录授权。源sourceRefId可为scope+canonical源快照的server稳定hash；不得靠数组index在后续轮次重新解释。澄清回复默认继承父问题的本轮目录，但仍核验当前ACL/assignment，新增资料通过新的显式sourceSelectors。

admission的request digest需包括intent、parent/pending/CAS、内容和精确目录，不能只用content；metadata进入既有服务端snapshot通道而非CHAT用户正文。新fresh CHAT request revision恒1，不自行创造旧request的多revision语义。

## 3. final回调与同事务

仅在锁定exact turn/snapshot并重新验证contextDigest、target、owner/client/tenant/route之后接受optional pair `outcomeContractVersion:1` 与 `interactionOutcome`。typed marker存在则pair必需；marker不存在则pair禁止。Handler保留raw JSON重复key/尾随内容/损坏Unicode证据，不能先经宽松Map解析丢弃。须拒绝任意层重复键，不扩大旧plain callback字段语义。

完整binding、facts、content、union交给已接受TypedDeliberationFinalValidator；digest唯一继承其canonical算法，不另发明或只hash文本。同digest重复返回原message/outcome/question/proposal；同文本不同union/facts/binding报409。snapshot缺失/不一致不能downgrade。

扩展现有ChatDeliberationService.persistFinal事务：创建原ASSISTANT message、typed outcome、必要pending/proposal、turn final CAS、request aggregate、原FINAL_PERSISTED事件及outbox全体原子提交。任何一个失败全体回滚；无另一个竞争final事件。FINAL_PERSISTED outbox仍唯一，正文delta仍独立prose，不把部分JSON当建议。

typed final event在既有agent_message payload增加 `typedOutcome`（本合同view，首次提交态），旧客户端可忽略。消息metadata记录outcomeId/finalDigest，不泄露private source/token/path。用户回答问题时新增持久 `typed_question_answered` 事件，payload恰pendingQuestionId/state/stateVersion/replyRequestId/parentOutcomeId；这是问题状态，不是新final或执行。依既有event journal replay/version语义，不本地制造完成。

## 4. 只读投影：不改现RequestView

GET `/chat/conversations/{conversationId}/requests/{requestId}/typed-outcome`：认证同现identity/tenant解析；精确owner/client/tenant/conversation/generation和bounty当前可见性。历史源仍可读，不要求旧grant ACTIVE；删除/foreign范围opaque404。返回JsonResult.success(data)，data恰：

`schemaVersion(1),conversationId,conversationGeneration,requestId,requestRevision,turnId,state(PENDING|READY),outcome(null或下述view)`。

PENDING仅表示持久本轮尚无成功typed final，不触发Provider或生成；请求非typed则404，不伪造ANSWER。所有long/version/cursor以canonical decimal string出JSON；schemaVersion仍number1。

outcome view恰：`outcomeId,taskId,assignmentRevision,assistantMessageId,finalDigest,kind,text,clarification,proposal`。

- ANSWER：clarification=null、proposal=null。
- CLARIFY：clarification恰 `pendingQuestionId,state(OPEN|ANSWERED),stateVersion,question,requiredFacts,replyRequestId(null或原回复request)`，proposal=null。
- EXECUTION_PROPOSAL：proposal恰 `proposalId,state(PROPOSED),stateVersion("0"),operation,instruction,sourceRefIds,sourceSelectors,parent`，clarification=null。sourceSelectors是server冻结六键选择投影；parent为server从源资产解析的 `{requestId,stepId}` 或null。仅用于重新进入既有v3权威context/preview；不含grant/consent/execution/token/producerPath。普通生成无源时sourceRefIds/sourceSelectors=[]、parent=null。

原final event可持首次OPEN投影，读接口返回当前CAS态；event处理不能用迟到OPEN覆盖ANSWERED。状态不更新immutable union或finalDigest。

## 5. 自然讨论和澄清回复入口

新增同一interactions surface的清晰路由 POST `/chat/conversations/{conversationId}/interactions/discussion`，避免与既有v2/v3 EXECUTE路由混用；不是另建消息/会话系统。Idempotency-Key沿现100字符opaque域；认证及opaque404优先序沿既有讨论。

body恰十键：`schemaVersion:1,intent:DISCUSSION|CLARIFICATION_REPLY,taskId,expectedAssignmentRevision,content,parentOutcomeId,expectedParentStateVersion,pendingQuestionId,expectedPendingQuestionStateVersion,sourceSelectors`。版本及revision为canonical decimal string，nullable字段必须出现为null（不coerce）。DISCUSSION允许parentOutcomeId=null；若引用父outcome须属于本scope/同generation且expectedParentStateVersion与父pending/proposal当前版本一致（ANSWER版本0）；pending两键必须null。CLARIFICATION_REPLY父outcome及pending/CAS均必需并完全相互对应。空sourceSelectors不是资料读取证据。

锁顺序：task root → bounty binding → conversation → parent/pending/typed admission → request/turn。复用现AgentTaskMutationTransaction和ChatBountyBindingStore锁源，保持当前assignment fence及唯一目标Agent，不从body信任target/sender。任意裸replyTo/continuationOf/agent/authority字段拒绝。

持久typed admission按scope+Idempotency-Key唯一，digest覆盖完整语义body+server冻结源/lineage。先在锁定当前scope下查原操作：同键/body精确重复回原request/receipt，changedbody409；不是fresh admission，不再调用模型/收费。再新建CHAT request（revision1）及outbox，并对OPEN pending按expected版本CAS→ANSWERED，写唯一replyRequestId、原key/bodydigest；同事务成功。不同key抢同问题只有一次赢，失配409，不能自动重新答题。陈旧assignment/撤权/删除/换身份按实际scope拒绝，GET对历史已完成结果仍只读。回答不创建grant、step、preview、execution或START。

202 JsonResult.success(data)的data恰：`schemaVersion(1),intent,requestId,userMessageId,turnIds,state,stateVersion,eventCursor,statusUrl,typedOutcomeUrl,replay,pendingQuestionId`；除schemaVersion/replay/turnIds外long字段用字符串。statusUrl为原`/chat/requests/{requestId}`，typedOutcomeUrl为第4节路径。精确replay仍202同receipt，pendingQuestionId仅CLARIFICATION_REPLY有值。

错误：invalid400；foreign/missing404；digest/CAS/assignment冲突409；持久化或真实能力不可用503。没有性能deadline/首帧取消阈值。UNKNOWN写结果仅原key GET/显式原POST恢复，不创建新收费操作。

## 6. 持久模型、迁移与事务来源

逻辑分离immutable outcome、pending question、proposal、typed admission四表：`chat_typed_outcome,chat_typed_pending_question,chat_typed_proposal,chat_typed_admission`。每表保留完整tenant/owner/client/conversation/generation及关联IDs；不可只按globalID读。outcome存完整canonical union/digest/binding/精确源目录、原assistantMessageId；pending及proposal的immutable payload关联outcome，mutable pending stateVersion CAS只增；admission保存完整bodydigest及既有request/userMessage/turn receipt。server稳定IDs从scope/turn/kind或scope/key生成，不接受modelID。

保持既有九表、v2 schema/repair与原CHECK字节语义；本包独立additive resource `db/chat-typed-deliberation-schema-v1.sql` 和严格 `ChatTypedDeliberationSchemaInitializer`，共用已有 `cyf:chat-deliberation:v2` migration lock避免并发DDL，version表新增3而不改version2历史。新initializer不得在default-off修改旧表/旧数据；启用后缺表且未明确allow-additive-migration则真实not-ready，不silent-create。迁移资格与identity/paid/生产DML授权分开，本轮仅源码/隔离测试，真实生产迁移另核授权。

DDL使用原MySQL8 InnoDB utf8mb4_0900_bin，完整NOT NULL/default/PK/UK/FK/index/CHECK实际catalog验证；scope+turn unique、scope+key unique、pending/proposal每outcome唯一。避免在旧chat_turn追加新scopeUK或放宽旧CHECK；新outcome通过原global turn_id FK并在应用事务核完整scope，其余pending/proposal FK可用outcome的scope复合唯一。完整DDL/ExpectedCatalog由责任Owner在受限source范围实现并提交，不凭空声称其已冻结；Main须绑定exact committed DDL/schema hash和隔离MySQL8 fixture后才准DB验证/提升。partial/weak/未知drift必须拒绝，失败保留；不以假H2代替MySQL FK/事务证据。

## 7. 前端完整接线与执行确认

唯一悬赏输入框发送自然DISCUSSION；正在答OPEN问题时以server pending ID/CAS发送CLARIFICATION_REPLY。刷新恢复请求目录→逐精确request read typed projection，不把activeRequest当全部历史；身份/会话generation fence、UNKNOWN原key恢复、迟到event/reply隔离沿现composables。

同一 transcript显示自然正文、问题及提议卡。问题不等于执行失败；提议卡的“确认办理/修改”必须由用户明确点击后走既有v3 context→preview→明确ack→issue→admit；EDIT独立per-intent操作授权及当前图源，不借GENERATE。用户仍可普通继续补充文本，不强制填固定表单，也不从中文字符串直接启动执行。UI支持材料目录选取，但确实未读取时不声明看过。

## 8. 实施ownership与实际验证

完整API Owner负责本合同原子闭包。当前75path Owner继续独占Handler/原Interactions/StepStore/执行authority/schema/build.gradle；本包先写disjoint Service/typed store/新controller/schema等。Handler注册/finalhook必须等明确移交再补；不在另一worktree提前编辑冲突path，不绕过旧controller。原Interactions无需改本新子路由，75包的execution改动完整保留。Web单独Owner写其composer/reducer/API adapter/实际page接线；不新增第二套聊天状态。

责任Owner源码自检后给exact child/tree/受限path列表/DDL及normalGraph测试清单。Main验证：plain回归、typed strict/Digest replay、完整Spring transaction原子rollback、pending同key/并发CAS/换身份/assignment/冷恢复、实际schema pristine→v3→restart/partial/weak、Handler真实callback和当前session钩子、MVC过滤身份、真实隔离MySQL；Web真实page/composable/API wire测试及后续live浏览器。测试fixture冻结NOT_RUN，实际结果另记录，不能把helper38通过算本合同通过。无Reviewer、Gradle只经orchestrator串行，保留真实transport/cancel/锁归属，Provider/生产激活需原授权。

完整34项/29桥、INSPECT、双接应、图片/音频/文本/文件、归档/正式验收/完成及本特性版本发布仍为目标，不缩减为本合同源码交付。
