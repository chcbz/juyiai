# 议事临时预览与持久完成分离

核对日期：2026-11-04。Owner：本聊天；沿用 JUYITING-POLLING-20261102 handoff。
状态：前后端与Runtime源码已实现，固定候选回归中；未合入整套候选、未发布。
适用：根AGENTS、API统一接口规范v1.4、RB-1；不改第三方模型流协议，不改工具执行/成果权威。

## 2026-11-04 用户最终确认（覆盖下文早期撤权/缓存讨论）

- 保留bridge提交完整最终正文及业务sidecar，API事务保存并确认；不实施“缓存流式正文后落库”。中间文字仅临时展示，不积累后端全文。
- 已准入流允许走完，不为中途账户删除、installation撤权或旧boot替换新增通知/失效框架。这些先前列为必做的撤权竞态研究退出本次范围；首次身份/任务归属和最终持久写入保护仍保留。正常断连/结束/取消的资源生命周期清理不是新的撤权框架。
- 已有ACK或首个有效回复均可证明送达；不新增确认协议，不逐帧重复outbox确认。一次准入及终态以外的预览帧不得查库、持数据库事务/锁。
- 缺帧只放弃临时预览，不重放模型/工具、不触发补帧或业务恢复。正式final保持原权威链路。
- 前端采用简单的完整起点规则：仅deltaSeq=1开始显示当前turn的首个streamId；重复忽略、缺号后放弃该turn预览、异streamId不能抢占。重连清除旧临时预览，晚加入可等待完整final。不新增开流控制事件、历史预览快照或换流协商。
- SSE data增加既有requestId/agentId/senderName/streamOutcomeKind语义；只有ANSWER/CLARIFY可用于用户预览。生产者与消费者均按下方实现接线；上线状态另记。

## 目标与非目标

中间文字是可丢失的展示过程，不是每token业务事务。开流准入、取消及最终结果是业务事实；后端热路径每个预览帧的SQL/数据库事务/业务行锁为零，SSE发送端也必须为零。正式最终结果仍权限校验、事务提交、幂等及持久通知。允许重启/断线丢预览，不允许以预览或socket成功宣称完成，不自动重跑模型/有副作用工具。

不新增表、MQ服务、全量文字缓存、轮询/补扫、TTL授权替代撤权、每帧摘要、补帧接口或跨所有业务的权限框架。流上的结构/连接/归属判断仍由网络边界实现。

## 补查发现及责任层

1. `AgentWebSocketHandler.handlePrivateMessage`在业务分派前调用`runtimeAuthentication.validateCurrent`；该方法读取installation/runtime/account。只修改`publishAgentMessageDelta`不能达成零SQL。
2. `withSessionMutationFence`持installation/runtime数据库锁；`isCurrentBinding`也间接调用validateCurrent。不能用现有方法名字猜测它是纯内存。预览应使用明确的当前活动通道绑定；持久副作用继续走数据库fence。
3. `requireCallbackConversation`、`requireConversationAgentScope`、`resolveAgentSender`以及`acceptDelta`重复读取派发/会话/执行关系。一次开流准入建立可信上下文，后续字段只做与该上下文的一致性核对。未授权key不能通过任意delta反复触发数据库准入。
4. `ChatController.durableCatchUp`把实时事件当日志序号提示，再`loadReplayThrough`查询正文。临时预览必须绕过该路径；最终持久事件保留原可靠补齐。
5. `ChatConversationEventBroker`的每订阅者replay buffer为持久提示设计，缺失提示能从数据库恢复。预览不能污染/挤掉最终提示，也不能按回复长度无限增长。使用明确有界的临时展示交付；慢客户端停止补齐该次预览，最终持久正文收敛，不取消模型/业务执行。
6. Web `hallConversationSse`原要求每帧SSE id并推进eventSequence游标；临时帧必须无SSE id、无数据库cursor。浏览器重连只使用持久游标，不将临时序号冒充日志序号。
7. Web `hallConversationMessages`缺帧触发resync，`hallDeliberationState`把delta升级为业务STREAMING/版本，`useHallConversation`会触发权威刷新且取消要求expectedLastDeltaSeq。这些必须解耦：预览缺失只改变预览展示，不触发业务失败/恢复/网络补查；取消依据业务版本，不依赖字符序号。
8. final已经传完整正文，API持久final并不以finalSeq为落库条件。保留最终正文/typed outcome/成果事实保护，不为“等预览齐全”延迟最终显示。迟到预览不能覆盖final/cancel终态。

## 准入与资源生命周期（2026-11-04当前方案）

- Runtime首个有效帧（deltaSeq=1）在现有认证与业务事务边界准入，绑定连接、tenant/client、turn、dispatch、conversation generation、snapshot、agent及可信sender；仅保存元数据，不保存正文。已存在的ACK或该首帧按现有机制确认派发送达，不新增确认协议。
- 后续帧只做内存连接/绑定/序号判断并转发；不查库、不进入持久事务、不推进业务版本。正常断连与终态提交后释放元数据；回滚不错误释放仍有效流。
- API重启或连接重建后，未知流的中段帧直接放弃预览，等待可靠final；不重跑模型/工具，也不从中段反复准入查库。
- 不新增中途账户删除/installation撤权传播框架，按用户决定允许已准入流走完；最终写入沿用原保护。会话broker generation fence仍有效。此处不承诺多实例临时广播。

## 临时SSE数据帧（源码已接通，未上线）

复用统一protocolVersion/requestId/messageType/messageId/data信封；messageType=`conversation.preview`。
SSE仅`event`和`data`，**不发送id字段**。data包含type=`agent_message_delta`、conversationId、conversationGeneration、turnId、streamId、deltaSeq、content、occurredAt；messageId=`preview:<streamId>:<deltaSeq>`，用于这条临时消息标识，不是日志游标。普通用户文字沿用ANSWER/CLARIFY分类，内部动作说明不作为用户预览。

禁止携带会推进业务状态或断点的eventSequence/eventVersion/state/stateVersion/lastDeltaSeq/cursor/nextCursor。解析后只调用独立onPreview，不进onEvent/onCommitted、不更新Last-Event-ID。

streamId由API一次准入生成；Web仅接纳当前turn首个从1开始的流，迟到新streamId不替换已选预览。无额外开流事件；断线放弃预览，final仍权威。

最终回复仍`conversation.event`，按现有持久游标交付；无需所有预览帧都到达。历史持久delta只作历史只读重放，新实现不继续写入；历史字段不为本批性能优化执行生产删列/清库。

## 临时方案撤销范围

- 删除Runtime200ms coalescer模块、timer、flush接线、打包清单及对应测试；恢复模型用户delta直接转发。
- 删除WS accepted final固定30秒等待特判，恢复原有有界指数退避；保留“重复ready不能绕过已有timer”“排队期间final已确认不重放”的正确性修复。是否进一步调整最终可靠交付，需基于新路径失败语义，不靠新的固定等待掩盖积压。
- 保留egress绑定分段计时、typed user-reply分类/thread identity和已有安全/持久机制。不是对fa8e2cd整提交git revert。
- 回退与长期方案配套发布；不先把撤销合并单独部署到仍逐帧落库的旧API，造成压力反弹。

## 验收及删除完成条件

- API开流准入单独计数；连续10/1000帧通过完整WS入口和SSE出口时，DAO/SQL/事务调用数不随帧数增加。测试包括上游认证与下游catchUp，不能只mock acceptDelta。
- 正常断连/取消/终态后不复活预览；错误绑定不进入已准入流，最终写入继续按现有权限与任务绑定保护。中途撤权传播不在本次范围。
- 预览不带SSE id；混合持久/临时帧只让持久帧推进cursor。丢帧、重复、迟到、重连、新开页不触发补帧轮询或执行重放。
- 慢订阅者、无订阅者、大量并发流无全文积累；final仍可通过持久重放恢复。最终保存失败不误报完成，final重复送达幂等。
- 删除新业务路径的acceptDelta持久写入及其DAO/状态补偿依赖；取消expectedLastDeltaSeq依赖；规范、生产者、消费者与回归同步。不因保留历史只读列而保留新旧双写执行路径。
- 本机仅轻量定向测试；正式跨端回归Flow固定源码，生产安装/业务实测另记。未完成项不能因文档或局部测试通过标成完成。

## 2026-11-03 23:48 补查：已核实影响与实施前剩余项

核对API源码HEAD `516267bf7b19bfc03581ae580704af9246ffb622`，下列目标文件当时无工作区差异；不是远端develop或当前安装制品一致性证明。Web候选由`3470468`推进至`c7cf61ef566928798d7b84300e0d6b1fada1d240`，仅本任务分支本地提交，未合入/发布。

### 新核实的遗漏

- **账户删除也是撤权入口。** API `user/jia-user-service/.../api/UserController.java`的`/delete`调用`userService.delete`；`UserServiceImpl`继承`common/jia-common-service/.../BaseServiceImpl.delete(Serializable)`，直接`baseDao.deleteById`，没有本地活动通道通知。不能只接`AccountSecurityServiceImpl.revokeAllSessions`。应在用户业务责任层处理删除后的活动主体失效，而非修改所有通用DAO删除。
- **旧boot替换不是socket断连。** `AgentRuntimeAuthenticationService.issue`更新runtimeInstanceId/sessionGeneration/tokenHash；本地bindings以含runtimeInstanceId的Scope为键。只调用`bind`不能使不同runtimeInstanceId的旧key自动消失。需按稳定主体失效旧执行通道，不将逐帧DB校验替换成裸map查询。
- **已有解绑通知不是授权失效。** `AgentHostedBindingTransaction.publishOfflineAfterCommit`是可选UI状态发布，捕获异常且允许publisher不存在；不能当作可靠的本地撤权通知。`suspendForBinding`、installation revoke及账户epoch更新仍需各自责任层接线。
- **一般会话更新不会改参与人。** `ChatConversationServiceImpl.persistOwnedUpdate`只使用新title/status，owner/targetAgentIds/taskId/generation沿用锁定记录。因此不为改标题新增全流失效。删除已有stripe fence，afterCommit关闭订阅、afterCompletion释放；不能另起反向锁序的逐帧锁链。
- **delta还隐式确认派发。** `publishAgentMessageDelta`在acceptDelta后调用`acknowledgeHostedReceipt`，后者再次进入persistent session fence，并锁outbox。删除delta业务路径必须明确保留`chat.dispatch.ack`的独立持久确认及final确认；需验证Runtime接收持久化和ACK失败恢复，不可让“预览未送达”导致再执行。
- **实际SSE入口未使用64项outbound buffer。** `ChatController.conversationEvents`有意只用firstFrame观测，先将数据库replay载入List，再concatWith live；不能以`ChatStreamPolicy.bounded`存在宣称这条路径已端到端有界。broker每订阅者replay.limit(1024)也不能当作新预览通道的内存证明。新临时流不得复用历史全文replay或最终通知队列；持续慢消费、取消清理以及final抵达必须有真实订阅需求回归。
- **Web草稿曾将预览错误升级为业务恢复。** `createHallSseParser`的预览分支调用onInvalid，会停止后续解析；`useHallConversation`的onInvalid又触发authoritativeResync。本轮测试复现“8→坏预览→9”只能收到8。现已在草稿解析器将可识别预览拒绝限定为onPreviewInvalid，不推进游标、不调用通用onInvalid，后续持久帧继续交付。尚未接入UI；未知/不可解码协议错误仍沿原传输错误规则，未声称所有坏帧都可恢复。
- **预览展示需保留用户回复用途。** `hallDiscussionTurns`只展示ANSWER/CLARIFY流；草稿data只有正文还不足以完整接入。正式合同需带可信sender/agent及明确用户回复用途，或者由开流上下文提供；不能用默认ANSWER让内部动作文字进入用户界面。

### 本机拓扑证据及边界

23:48只读查询：运行nginx master命令为`/home/isp/apps/nginx/sbin/nginx`；当前磁盘`conf/vhost/api.chaoyoufan.cn.conf`及native proxy snippet指向`127.0.0.1:10018`；该地址有一个Java监听PID2964836。这支持本机单API目标设计，但**未核实nginx进程实际已加载该磁盘配置、外部DNS/LB其他节点及其它安全写入进程**，不能声称分布式撤权已解决。若实际存在多API写入口，不能无依据使用单进程失效作为完整授权保证；先明确实际部署边界，不为假设扩建MQ。

### 尚未闭合，不能直接移除通用认证

1. 开流准入与撤权/新boot的并发顺序：先查库后放入map会产生“撤权完成后旧授权再入map”竞态；仅afterCommit remove不够。需要明确仅覆盖低频准入/撤权的同步机制及锁序，数据帧不持数据库锁。
2. Runtime独立dispatch ACK的接收持久化、重投和final恢复顺序仍需完成端到端核对；开流失败只允许少展示，不得自动重跑执行。
3. SSE新订阅开流快照与后续临时帧必须有确定顺序；旧stream不能靠迟到帧重新抢占，final/cancel后的排队预览不能复活。前端传输generation已有机制可复用，不新增定时补帧。
4. slow-consumer的排队边界与final独立交付尚未完成实现/回归，不能用固定条数口头替代内存验证。

轻量证据：`/home/isp/state/cyf-diagnostics/juyiting-polling-20261102/ephemeral-stream/web-preview-isolation-before.log`（新增回归失败）及`web-preview-isolation-after.log`（7项通过）。不是Flow集成回归/生产效果证明。现阶段继续补查，不宣称整体方案检查完成。


## 2026-11-04 实现与验证接续

- API候选 `81d9c1b1b6`（基线`3a5a8650a0`）：完整WS入口首次准入后直达临时broker；删除acceptDelta服务/DAO/Mapper写路径与逐帧outbox确认；内置模型流也改为一次准入后直接预览。最终正文/typed sidecar持久化不变。取消只依赖业务stateVersion；旧expectedLastDeltaSeq可读但不参与并发判断。
- Web候选 `ffb2e56`：预览只更新气泡，最终正文替换；缺帧/重连仅放弃预览。取消不发送字符checkpoint。补查发现首字观测逐帧增长，已改为每请求一次；实际composable接入1000帧的轻量测试确认无新增读取、无重连、仅一条首字观测。
- Runtime `3fbd562`：撤销200ms合并和accepted-final固定30秒等待，保留原可靠final、指数退避及ready/ACK正确性修复。Flow5264702/134成功：848项Node测试，838通过、10原有主机探针跳过；不是生产包或主机探针通过证明。
- API472/473失败均保留：第一次3项（取消旧预期2项、Spring测试注册1项）；修正后第二次普通测试通过，深入MySQL修订测试发现同一新增组件在独立harness未注册（8项）。已检索实际Spring手工注册入口并补齐，不把失败Run用于发布。474验证新候选；Web421成功后，422验证新增观测修正。
- 本节记录源码/验证范围，不代表上线；本次没有新表、新服务、全文缓存、预览重放或补扫机制。

### 2026-11-04 线上背压修正候选（覆盖无缓冲直传解释）

线上474的directBestEffort + merge预取1在正常MVC异步写出时发生大量序号跳变，故“不缓存全文”不能解释成“传输层不允许短队列”。API候选509325a971仅在每个实时预览订阅后使用Reactor默认小队列（256项，DROP_OLDEST）；不修改持久流预取，不存历史、不开定时器、不累计全文、不补帧、不产生数据库写入。真正持续慢端满队列只丢预览，Web缺帧丢弃草稿，final仍使用独立持久通道；取消订阅或会话删除主动清队列。buffer属于连接生命周期，晚订阅者不会收到此前字节。

此容量是传输资源边界而不是应用SLO或拒绝执行的门槛；线上跳号暴露短暂写出抖动，候选补热源突发128×10组/逐项需求，以及超容量慢端、快端/final隔离和关闭释放回归。尚需Flow和真实浏览器确认，不以规格更新宣称验收完成。

2026-11-04 08:31核验：上述509325a971经Flow475通过并已安装；真实新事项375帧连续、无预览清空、完整final匹配，刷新保留一条。实现/发布证据见handoff“预览背压修正发布及实测通过”；不把单次浏览器通过外推为负载上限或模型延迟改善。
