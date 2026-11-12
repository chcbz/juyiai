# 源码推演复核与详设修正（2026-10-18）

## 边界与结论

本轮Owner为当前线程；仅源码只读、详设与执行计划修订。根/API/Web重新fetch origin/develop成功，HEAD与远端一致，完整commit/tree/命中源码字节见`source-design-review.json`。Runtime仅核对本地`/home/isp/wsps/chcbz/isp-install`源码，未fetch其远端，不代表最新或安装版本。未登录生产、未改产品/原型运行代码、未运行应用测试/Flow/部署。

**上一版“可以直接照着开发”的判断过早。发现10项设计缺口，其中R01–R03会直接阻断主链或破坏修改边界。本文修正已同步代码级详设；这是设计闭合，不是运行验证通过。** 产品交互和四主状态不变；不新增用户审批、独立Reviewer或重复框架。

## 1. 逐项事实、后果与修正

| ID/级别 | 已核实的源码事实 | 上版遗漏/后果 | 冻结修正 |
|---|---|---|---|
| R01 P0 | `ChatDeliberationService.persistFinal`对turn/finalDigest不可变；`chat-typed-deliberation-schema-v1.sql`限制request_revision=1且request/revision outcome唯一；Web `actionProgressAdvances`禁止终态回退 | B4.1写“同request恢复生成”会冲突、覆写历史或被前端丢弃 | 原USER消息复用，父request/turn终态不改；创建确定性**子request/turn**，由review operation关联父子。复用`admitInspectionContinuation`/`admitTrusted`已有复用USER能力，不假冒INSPECT。新增受信CHAT continuation，禁止普通HTTP传existingUser |
| R02 P0 | `ChatActionOutcomeContract`当前v4只允许ANSWER/CLARIFY/ACTION_REQUEST；capability只支持EXECUTE/EXECUTE_SKILL；declaration carrier、final摘要、Runtime parser/model schema、Web parser均严格校验 | 新增`proposeRevision`没有任何合法上游调用载体，写出来也跑不通；仅改prompt会被codec拒绝 | 活动协议统一升级v5，新增专属REVISION_REQUEST union及受信reviewBasis；三端codec/声明/摘要/模型输出schema/fixtures一起改。不可伪装普通技能或复用v4摘要；旧协议仅历史只读 |
| R03 P0 | `ChatActionDispatchService.consume`校验任务归属/指派，但当前无“待验收修改决定”前置；执行器仍可接ACTION_REQUEST | 只拦自动提交不够：Agent可能先执行工具产出修改，再来拒收，造成并发覆盖/重复费用 | 待验收输入快照在原admission固定。生成/修改型ACTION_REQUEST在新入口必须有已COMMITTED的review lineage，否则拒绝执行；此阶段只允许问答、澄清、经明确能力分类的只读检查。不能仅凭prompt区分只读 |
| R04 P1 | typed admission现行record没有delivery/version/targetArtifactIds字段；原review表只有命令JSON，B7摘要无消息来源/目标集合 | 批次定位与多成果部分修改只能靠临时内存，重复提议可能改目标却被当重放 | 增加独立typed review-context快照表与review来源/父子关联字段；内部消息来源修改使用新独立摘要域，包含来源与完整目标集合，不能复用B7人工ACCEPT摘要 |
| R05 P1 | `ChatActionFinalService.persist`的ACTION事件与final同事务；relay默认异常重投，未知event直接DEAD | B4写“PROCESSING留待恢复”但没有worker；B3永久冲突会无限重投 | 自然语言REVISION_REQUEST同final事务入REVIEW_REQUESTED；复用已有fenced outbox。自动提交区分永久拒绝和暂态故障。浏览器ACCEPT同key POST可恢复PROCESSING，GET仅查；不能把关闭浏览器后悬挂解释成成功 |
| R06 P1 | `ChatActionOutcomeContract`来源只认workspace/current conversation/execution；B3.1新增FORMAL_ARTIFACT，B5 source union却没有对应分支 | 文字/跨话头保留项能提交但无法正确读取、预览或继续编辑 | 受信批次为独立reviewBasis，不伪造现有sourceSelector；读模型增加FORMAL_ARTIFACT固定引用，沿正式artifact ACL读字节。保留旧来源链与新批次artifact，不能把全部来源强塞当前话头 |
| R07 P1 | `useHallData.loadTasks`将selectedTask不在当前30条或列表失败时清空；ChatPanel只读依赖selectedTask.status | 验收后任务离开筛选页，原议事丢失上下文；筛选/分页/网络异常可影响发送和只读 | 列表选择与活动任务上下文分离；活动任务按ID刷新及scope隔离，列表缺席不证明删除。pending操作绑定task，不以整个列表刷新取消当前任务 |
| R08 P1 | `useHallTypedDeliberation`/`hallTypedDeliberation`按request、turn、outcome及单调版本合并；当前actionProgress v4只允许EXECUTE子路由 | 父request结束会被当作修改完成；新CHAT子请求不被接受 | 增加reviewProgress/父子关联投影及严格parser；父意图结束≠事项完成，跟踪子请求catalog/SSE及任务交付读模型，reload从持久事实恢复 |
| R09 P1 | 原正式决定服务changes_requested会将work item重置READY、清租约并把root改RUNNING；promotion重新claim，要求exactly one required work item且非paid授权 | 若沿用拒收前taskVersion/旧lease，新提交必冲突；误推广到付费/多工作项链会越界 | 子执行与新提交使用决定后的固定版本、有效grant和新租约；旧提交仅reconcile不续租。仅普通单承办/单必需工作项进入本链；资金榜/多工作项保持原能力，不假装可验收 |
| R10 P1 | 新状态计数设计原先一处按raw CASE，一处按交付覆盖；原HTTP同时允许ACCEPT/REQUEST_CHANGES但自然语言设计要求受信来源 | 列表/计数不一致；浏览器可绕过消息来源链直接返工；文档出现两条开发路线 | 同scope root/current-delivery关联谓词同时用于phase过滤/计数/展示；新review POST仅ACCEPT，REQUEST_CHANGES只来自受信内部final。原专用工作空间返工保留但不是新UI通路 |

## 2. 修正后的内部主链（用户仍只发一条消息）

```text
用户发送 → typed admission持久USER + 父request + 批次快照
  → Agent v5 final
    ANSWER(deliverable=false)：解释；待验收不变
    CLARIFY：在原议事提问；待验收不变
    REVISION_REQUEST：父final不可变落库 + REVIEW_REQUESTED outbox（同事务）
      → worker事务外准备受信包（不运行生成工具）
      → root锁 → review operation → binding/conversation → delivery/work item → outbox claim
      → 再验身份、原USER、generation、指派、批次版本、明确目标集合
      → decide(changes_requested) + 创建CHAT子request/turn/dispatch（复用USER）
      → COMMITTED receipt(parentRequestId, childRequestId) + fenced outbox SENT（同事务）
      → 原议事显示进行中，Agent执行子请求（失败保留可恢复原因）
      → 子final有效正式交付 + DELIVERY_REQUESTED → 晋升/提交 → 待验收
      → 用户点击确认ACCEPT → 原子正式决定 → 已完成
```

不存在“重新打开父final”“再插一条用户消息”“直接让模型写状态”。普通讨论不执行修改工具；自然语言理解本身仍有误判风险，后端只能验证受信来源/授权/版本，不能声称完全识别真实语义。

## 3. 修正后的合同与数据落点

### 3.1 活动v5协议（目标，不是现行API）

- 新final union字段固定：`schemaVersion=5, kind, text, clarification, action, deliverable, deliveryRelation, revision`。原有字段语义不重命名；无对应union字段为null。新增kind=`REVISION_REQUEST`，此时`clarification/action/deliveryRelation=null, deliverable=false`，`revision={instruction, targetArtifactIds}`；目标非空、去重、属于受信快照RESULT项，不能选MANIFEST，instruction非空合法Unicode。其他kind要求revision=null。没有批次快照不得输出该kind。
- 服务端dispatch加入`reviewBasis`：null或`{taskId,taskVersion,deliveryId,deliveryVersion,batchSha256,assignmentRevision,sourceMessageId,sourceRequestId,items}`；item固定artifactId/version/hash/purpose/displayRole。快照并不是用户授权，只用来定位，明确修改仍来自原USER及Agent解释。模型不得改owner/租约，也不接受模型自由传deliveryId。
- `ChatActionOutcomeContract`/`ChatActionFinalValidator`/`TypedDeliberationDeclaration`/session registry与实际dispatch/final handler全部改v5；carrier新写`CHAT_MESSAGE_FINAL_SIDECAR_V5`，final摘要中outcomeContractVersion=5且包含revision；旧摘要永不重算。同步SQL outcome kind CHECK、schema initializer、Web hallTypedDeliberation、Runtime `juyiting-action-outcome.mjs`及声明/model schema生成调用点。v5协商未就绪不派发该新链，返回明确能力不足，不静默按v4走另一条实现。
- 内部修改摘要：`SHA256(UTF8(JSON.stringify(["hall-message-review-v1",taskId,sourceRequestId,sourceMessageId,parentOutcomeId,parentFinalDigest,deliveryId,deliveryVersion,batchSha256,sortedTargetArtifactIds,instruction])))`。target按UTF-8字节序；数字十进制string。需Java↔Runtime/Web独立向量验证，本文定义不是已测试向量。scope绑定DB唯一键，不由模型填写。
- `ChatTaskDeliveryReviewService.proposeRevision`只接收已验证的BoundRevision（scope来自持久源），不暴露任意HTTP/模型直调接口；新公共review操作仅ACCEPT。REQUEST_CHANGES是内部领域决定，不能由浏览器绕过父final和原消息快照。

### 3.2 持久化与恢复

- 新表`chat_typed_review_context`，主键`(tenant_id,owner_jiacn,client_id,request_id,request_revision)`，域ID长度/排序沿typed admission；存`basis_json`（合法JSON，显式null代表当时无交付）、`basis_sha256`、`created_at`，FK引用同scope request。与USER/admission同事务写；不可在Agent返回后再读取最新批次冒充原快照。父requestId/messageId/generation由请求/快照关联读，不接受客户端指定。
- review operation增加`origin=USER_ACCEPT|MESSAGE_REVISION`、nullable `source_request_id/source_message_id/parent_outcome_id/parent_final_digest/child_request_id`、`target_artifact_ids_json`。MESSAGE_REVISION来源完整且目标非空；USER_ACCEPT所有来源字段null、目标[]；state=COMMITTED时MESSAGE_REVISION必须child_request_id非空。增加`(scope,task_id,source_request_id,decision)`唯一键；同源重复回调复用操作，不换key。新目标DDL及fixture必须按此修改后方能实施。
- 子requestId确定性派生自scope+review operationId，revision=1，新turn/dispatch ID各自派生；USER ID沿父原消息，lineage固定`origin=DELIVERY_REVISION,parentRequestId,parentOutcomeId,parentFinalDigest,reviewOperationId,originalUserMessageId`。内部`admitDeliveryRevisionContinuation`为MANDATORY，在根锁下调用现有受信admission能力；外部typed endpoint不接existingUser/lineage，不伪造INSPECT或EXECUTE技能。
- 保留原request终态和final摘要；**review回执requestId表示子请求**，增加sourceRequestId（ACCEPT时两者均null）。父结果投影新增独立`reviewProgress`，不是强塞旧actionProgress。字段为`operationId,state,stateVersion,sourceRequestId,childRequestId,childState,childStateVersion`；仅REVISION_REQUEST有值，QUEUED时子字段null，COMMITTED后子ID稳定，后续子状态只随持久事实单调推进。
- REVIEW_REQUESTED同父final事务写入已有outbox；消费者可在任务根锁内直接创建/重放操作并决定，不先留下一个没有job的PROCESSING。事务外包准备失败由原outbox重试；操作/决定/子admission/dispatch/SENT同事务回滚。ACCEPT同步操作若PROCESSING且未决定，用同key同body POST恢复；GET与页面mount绝不执行决定。
- 永久冲突（批次已被验收、代际失效、来源不合法）落可查询的REJECTED/拒绝事件并fenced结算；暂态数据库/网络失败重试，不设无证据重试次数硬门槛。丢失claim不能宣告SENT，也不能回滚另一worker已提交的决定。

### 3.3 部分修改与读模型

- 新RESULT来源union增加`FORMAL_ARTIFACT={kind,sourceDeliveryId,sourceArtifactId,sourceArtifactVersion}`；外层item仍是新批次artifactId/version/hash。读取和预览逐项校验scope/task/固定内容，不将source当下载URL。新一轮固定集合为“旧RESULT减去被替换项＋新RESULT＋新manifest”，拒绝重复artifact、目标不在旧批次及无法证明替换关系；不能自动把多项新结果合并到所有目标。
- 子上下文带VerifiedDeliveryBasis和target集合；普通用户资料selectors仍使用现行严格格式，正式历史成果经服务端包准备读取，不扩成客户端可写的FORMAL_ARTIFACT selector。跨话头要求当前有效binding/generation，旧话头仅提供已授权固定历史源。
- phase查询/计数从同一owner域根与有效交付关系计算。只有current SUBMITTED且无已提交修改决定才待验收；根终态优先。根reviewing关联缺失UNKNOWN；completed保留已完成事实但单列资料核对提示。未决操作只是提示/写互斥，不将一条普通消息pending显示为事项进行中。

## 4. 最早验证顺序与反例

先做小闭环，而不是先改完19个页面再联调：

1. **V01 合同探针**：同一v5 JSON经Runtime schema/validator → Java final validator/摘要 → Web parser；合法修改、普通问答、含糊澄清和伪造来源各一组。拒绝旧v4冒充v5及未知字段。未通过不接自动执行。
2. **V02 真DB事务探针**：单用户消息、父final→outbox→决定→子request；逐点注入失败，验证一条USER、父final不变、最多一个子执行、无半拒收。检查Spring实际代理与REQUIRED/MANDATORY加入同事务；不能用Mockito代替。
3. **V03 真实文本闭环**：提交→问答仍待验收→明确修改→新提交→人工验收；浏览器关闭/重启relay也能完成自动步骤。
4. **V04 并发与恢复**：验收先赢/修改先赢、相同事件双worker、不同消息同时改同批次、响应丢失、PROCESSING同key恢复、持久决定成功但通知失败。拒绝未知时自动换键。
5. **V05 成果边界**：三项改一项、纯文本、文件、跨话头历史源、旧版本撤权、manifest不能作为修改目标、租约失效/新claim、付费或多必需工作项明确不误入。
6. **V06 前端状态**：过滤掉当前事项、列表只回30项、列表网络失败、换账号/切任务、父final先到子执行后到、reload追踪子请求、普通消息pending仍待验收。
7. 再推进其余共享布局/19页回归，最后按项目规则以固定候选Flow正式验证；Runtime按其仓库现行流程并与同一v5合同对照。开发完成不代表部署，deploy需版本化发布及在线回读。

## 5. 已确认可复用、不应重做的部分

- 原子创建服务`create`已是REQUIRED；正式草稿提交事务可以加入。完整需求snapshot保持权威，不能删掉现有create结果/权限核对来“解决”长正文。需实际DB测试确认回滚。
- 正式要求修改决定已经重置工作项READY、清旧租约、root RUNNING，无需另写第二套事项状态机。
- 现有outbox具有claim/fencing/retry；现有受信continuation能够复用USER消息，复用而不是再建队列/Runner。
- 租约、资金/授权、身份隔离、只读历史不因简化用户状态而放宽。

## 6. 尚不能声称已解决的验证项

真实安装schema/索引与迁移耗时、MySQL锁次序在全部调用路径上的行为、跨三端codec实际字节一致、Runtime真实语义判断、真实媒体/设备适配、生产端到端返工均待实施验证。本文不是“零返修保证”；将最易暴露的问题前移至V01–V03，能尽早验证架构是否真正可运行。

- 澄清回答必须继承原pendingQuestion关联的冻结reviewBasis并核对当前版本；不以新消息时的最新批次静默替换原问题对象。快照失效则明确告知并重新澄清。新目标摘要样例在code-contract-fixtures.json，仍需V01跨端真实codec验证。

- 待验收只读检查的能力分类必须来自已核验、固定摘要的技能manifest/服务端白名单，不能采信Agent自称readOnly；现有EXECUTE_SKILL不能证明只读时不放行。普通ANSWER若错误标deliverable=true而没有有效修改lineage，自动提交必须明确拒绝，不替换当前批次。

## 7. 2026-10-18 界面方案收敛复核（本地源码，非新增生产验证）

本轮固定读取Web HEAD `6fbdb6618b1132316a95db87cca9402de83138e8`、API HEAD `b76a1d0aeda572767a6d4734d050121d985bd9c9`；未fetch，不宣称远端最新。本轮仅定向读取Web组件，未新增后端行为验证。

| 发现 | 证据位置 | 本轮处置/剩余验证 |
| --- | --- | --- |
| 文档正文仍要求末张卡验收、卡片验收、引用修改，与后补图标方案冲突 | 原F3、详设5.3、方案A07/B04、执行计划T04、原型C07 | 已直接修改正文及原型规格，不靠“最新附录”覆盖冲突；禁止旧文本重新作为开发指令 |
| 父scoped CSS不保证覆盖slot里的验收图标 | ChatPanel toolbar-actions、BountyDiscussionPanel包装组件 | F8明确matter-actions slot、共享class/限定deep与父壳事件转发；四图标同尺寸测试保留 |
| 第五取消按钮未在原型覆盖 | ChatPanel `v-if=durableCancelTarget` | 真实功能必须保留；C00新增条件样例与窄屏可达回归，目前未验证该样例 |
| 正式输入上下文不全是装饰文字 | HallChatComposer targetChips的removeTarget、mention-agent、clear-target | 固定对象可去重复；多Agent可操作对象不得删，先补原型样例再实施 |
| 固定44px与现有自动高度冲突 | HallChatComposer resizeTextarea写入Math.min(scrollHeight,132) | F8新增compact prop及JS高度分支；非正式模式保持原行为，避免CSS/JS争用 |
| 终态只读条件不全，CSS隐藏不等于停止资源 | ChatPanel serverTaskCompleted、materialPickerOpen watcher | 使用任务投影覆盖完成/取消/归档；保留未决非终态，收尾录音/选择器但不删草稿；切换事项恢复 |

以上未修改产品源码；后端V01–V03、P08真实入口/P18边界、真机软键盘及真实录音限制仍沿既有结论，不能以离线页面测试替代。
