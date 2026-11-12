# 受控图像合法点将 / START：跨仓桥接合同 v1

状态：**wire 与共同 fixture 冻结，供 BRIDGE-A/C/W 实施；不是实现、测试通过或费用启用证明**。对应上一份[详设](controlled-image-grant-start-bridge-design-v1.md)，本文件覆盖其中“拟议 wire”字段；其长期业务范围不缩减。API core `acab3411` 仍是验证候选，实施可在其独立 worktree 准备，整合必须等待实际 core 与组合树验证。Client 基线 `69765549`，Web `1ceb48d`。

共同 fixture：[controlled-image-bridge-v1.json](fixtures/controlled-image-bridge-v1.json)。其中所有主体、模型、policy、密钥标识均为离线虚构值，无真实账户或调用授权。五组 cases 是**预期验收输入/不变量**，不是通过记录；共同 fixture 的字节 SHA-256 绑定在同目录 `.sha256` 文件。不可各仓悄悄改 wire。

## 1. 不变量与兼容

- 一个悬赏议事，多种有权限边界的处理动作；明确且受权的画鸟直接 EXECUTE，不额外强制 fast 模型。快速聊天仍不得加载工具/资料原文或获得执行权限。
- 旧 fast-v1、nativeBountyExecution-v1（32 inputs）、credential-binding-v1、PRIVATE/TASK 及普通/funded/auto 点将不改授权语义。旧非空 costRef 不能再构成 paid admission。
- 受控图像仅 GENERATE_IMAGE；0–16 个 canonical task-linked JPEG/PNG 输入，固定一个 PNG `output_1`，一个 HTTP attempt。第17项在 ISSUED/RESERVED/START 前拒绝，不截断；后续 EDIT/澄清另有合同，不能假装已支持。
- operator delegation + owner exact consent + server grant + exact execution/run + live runtime/lease，缺一不得外发。能力 GET 与任何原操作 GET 均不签发/绑定/预留/消费。
- 成果、归档、正式交付、验收、需求完成仍是不同事实。CONSUMED/START 不代表有鸟图，也不代表实际扣费金额已知。

## 2. owner HTTP

JWT owner/client/tenant 与 core 一致，不能浏览器自报身份；runtime principal 不能调用 owner 接口。响应沿用 `JsonResult.success(data)`，private,no-store,nosniff。

### 2.1 capability：独立 GET，不放宽 v1

```text
GET /agent/tasks/{taskId}/point-and-start-controlled-image-capability?targetAgentId=<explicit>
```

仅此一个 query 参数，目标显式；不接受 consentId/hash/owner。`data` 的完整精确形状见 fixture `wire.capability`：schemaVersion=2，lane=`ORDINARY_SINGLE_AGENT_CONTROLLED_IMAGE_ASSIGN_AND_START`，serverLane、controlledExecution、providerBinding、authorization、newStart、requestedOperations、initialOperation、inputRefsPolicy、maxInputItems、originalIntentRecovery。

- `authorization.state=CONSENT_REQUIRED` / paidExecutionAuthorized=false，是当前服务、operator、唯一 live binding 与协议均具备、但**尚未同意本次**的观察。newStart=false，不能直接点将。
- controlledExecution READY 要求新 sibling 与现有 credential binding 两个事实来自同一当前认证 session 且完全吻合；联合lookup一次读取WS session/current auth binding，并在 runtime入口精确绑定 RuntimeScope.runtimeInstanceId；不得拼接两个各自唯一但不同session的lookup。不能只凭技能名或 binding-v1 READY。
- unavailable 状态使用 `UNAVAILABLE`，newStart=false，blockingReasons 有真实来源；providerBinding=null，requestedOperations=[]，initialOperation=null。inputRefsPolicy/maxInputItems 恒为 TASK_LINKED_REFERENCE/16，是协议边界，不表示可读整个空间。源故障503，不伪装成功。
- originalIntentRecovery 固定 legacyFallbackAllowed=false、unknownOrNotFoundMeans=RECOVERY_REQUIRED、replayPolicy=EXPLICIT_USER_EXACT_ORIGINAL_KEY_AND_BODY_ONLY。
- 旧 `/point-and-start-capability` 仍 v1/UNAVAILABLE。Web 只显式选择新受控 lane，不能未知版本/坏状态退回旧 assign。

### 2.2 issue / exact wrapper / readback

先按 [core v1](controlled-image-provider-core-contract-v1.md) + [Web v1.1](web-provider-consent-core-contract-v1.md) 签发；issueKey 和 assignmentKey 不同，四项 key/body 同一原 intent 持久并 readback。ack 必须来自明确用户动作，不能设默认。

```text
POST /agent/tasks/{taskId}/point-and-start-controlled-image
Idempotency-Key: <原 assignment key>
GET /agent/tasks/{taskId}/point-and-start-controlled-image/request
Idempotency-Key: <同一原 assignment key>
```

POST body 顶层**仅** schemaVersion=1、assignment、providerConsent；后者仅 consentId、expectedVersion（canonical Java-long decimal string）。assignment 原 canonical v2 正文完全不变；不能追加 costRef、hash、binding、金额、endpoint、token。具体字段与值见 fixture。wrapper 在 POST **之前**作为同一原 intent 的 immutable 扩展持久/readback；刷新不能重新从目录构建。

响应 `data` 顶层仅 schemaVersion=1、grant（既有 owner-safe DTO）、providerConsent（core 当前只读 DTO）。首次201，原键/原 wrapper 重放200，GET200；replay 先核对持久原操作，不能拿已经被点将推进的 taskVersion 重新拒绝原成功操作。core consent version 后续推进时回读允许当前 monotone receipt，不能因此得到新调用。

持久记录必须固定 scope/task/原键、完整 wrapper digest、原 expectedConsentVersion、原 consentId、实际 grant/version/assignment、server locator；物理存储可复用已有 action metadata 或独立桥接操作表，但必须在同一事务写入，不能只保存在浏览器。wrapper hash 域与旧 assignmentBaseHash 分开，旧 grant hash 不被改变。同键不同 wrapper/consent/expectedVersion 409。

GET 只观察已提交 mapping 和当前 consent，不补写、不 claim outbox、不发首轮。404 仍是 UNKNOWN，不能推断在途 POST 未受理或自动换key。用户明确继续仅允许原 key/原 wrapper，网络/503/409保留原意图。撤销/过期不是删除原点将意图的许可。

统一新桥接错误：400 CONTROLLED_IMAGE_BRIDGE_BAD_REQUEST；404 CONTROLLED_IMAGE_BRIDGE_NOT_FOUND（owner-safe）；409 CONTROLLED_IMAGE_BRIDGE_CONFLICT；503 CONTROLLED_IMAGE_BRIDGE_SOURCE_UNAVAILABLE。未登录401；旧接口错误合同不改。错误中不披露 secret/locator/其他owner，异常不能转换为成功。桥接默认关闭；真实关闭/依赖未可用不调用 Provider。

## 3. authority 与三段事务

### 3.1 单向依赖与锁序

应用 aggregate 依赖 Grant、Consent 与独立 CostAuthority 查证层。Grant **不注入 Consent service**（Consent core 已依赖 Grant）；Authority 只依赖 scoped DAO / operator / 当前binding等下层，不反向调用 Grant/Execution/Chat。不使用 lazy 循环引用遮盖结构错误。

每个段 REQUIRED 同一 task-root transaction：

```text
root → grant action/bootstrap → canonical target/files（确定排序）
     → grant → consent → execution/run/inputs → START marker → Chat write rows
```

无需某类行时跳过，但不得反序新增锁。core 公开 transition 现在先 consent 再重新 admit grant，**不能直接嵌到 execution锁之后**；桥接须提供“aggregate 已持root与grant”的内部原语/authority上下文，先取得当前grant/target/files，再锁consent，再execution；不能凭浏览器或提示词构造该上下文。root重入不是REQUIRES_NEW。

Chat coordinator 现在 root/grant 后先锁 Chat 再 createConversation，是实码待改处。新组合必须先 creation+RESERVED，再锁/验证/绑定 Chat；Chat link/step/request 的任何失败全部回滚 execution/inputs/RESERVED。必须验证 Agent 与 Chat 使用同一有效 transaction manager + DataSource；如果实际不是同一个，不能以注解相同宣称原子，要先闭合同库边界，禁止假原子双写。

### 3.2 点将 + BOUND

ISSUED、exact version、原 assignment key/hash/input/confirmed requirement/canonical target/当前operator+binding+model+expiry 全部一致后，在 root内完成原 assignment/event/grant/唯一bootstrap、桥接映射、consent BOUND、grant locator，一并提交。任一写失败全回滚。locator 固定 server-only `mmd-ci-v1:<consentId>`，仅是查证位置，不是 bearer permit，不在 owner grant DTO 暴露。其consentId须为实际server签发的 `consent_` + 32 lowercase hex，不能把任意非空ID拼入locator；scope-safe lookup及execution/run唯一关联必须防两个consent并发占同一execution。

查证 tuple 必须包含 tenant/client/owner/task/target/grant/version/assignment/baseHash/inputDigest/consent/binding/epoch/model/operatorPolicyRevision。陌生、伪造、错owner、旧grant、空或非空未知ref都不能通过 paid admission。grant.paidExecutionAuthorized 是此持久授权事实的 owner-safe摘要，不表示“还剩一次可用调用”。不能用该布尔发起第二execution。

### 3.3 execution + RESERVED

当前合法 BOUND 下同一事务创建唯一 execution/run/精确 inputs 并 reserve；input snapshot 与真实 grant/consent一致。第二 execution/run 拒绝。原 execution意图回放只核对同一mapping，不能换run，也不能因为query显示BOUND就创建新execution。第17项先拒绝，部分inputs/RESERVED不得提交。

### 3.4 START + CONSUMED

root/grant/consent/execution/当前 runtime/fence/实际输入bytes与摘要全部核对后，在一次事务内写 RESERVED→CONSUMED + execution START时间/lease版本。首次成功才有第5节 callable receipt；重复 START409，即便相同lease。ACK-loss重放或GET不能返回第二份 started:true；Client 收不到首次精确receipt就零外发。

revoke-first拒绝 START；START-first保留consume事实，之后 revoke409，不宣称撤销/退款。任何START标记或消费写失败都回滚双方。

费用用途明确分为 NEW_EXECUTION / PROVIDER_START / EXISTING_RUN：CONSUMED只允许同一run审计、原结果提交/读取（仍验证实时任务/资产ACL与runtime lease），不允许新调用。已消费后operator到期/撤销不能让已提交私有asset凭空不可读。EXISTING_RUN不重新获得新调用权限，也不绕过显式execution取消、会话/资料撤回或当前asset ACL；源输入继续读取要有当前受权事实。同run补交仍需有效runtime/lease与未被取消的execution。不能依靠宽松EXISTING_RUN处理忽略用户明确撤销。现有所有流程一律 `admit(...paid=true)` 的实现须在相关调用点拆分用途，不可把已有成果读取当新收费准入，也不可把非付费读取检查当新调用准入。

## 4. 独立能力 sibling 与 v2 command

新增 `controlledImageBountyExecution`（不是重命名旧声明），schemaVersion=1、transport=`PERSONAL_WORKSPACE_CONTROLLED_IMAGE_HTTP_V2`；commandSchemaVersions=[2]、leaseProtocolVersions=[1]、providerStartFenceVersions=[2]、resultCommitProtocolVersions=[1]；enabled时唯一GENERATE_IMAGE操作、0..16 JPEG/PNG inputs、一个PNG output_1。disabled时同形状、operations=[]。完整字段见 fixture。

`nativeProviderCredentialBinding` v1 保持原9字段，其中precallFenceVersion=1指受控adapter/持久claim协议；与新增 START envelope schemaVersion=2 不是同一概念。不能把已有binding-v1当新START-v2具备。

共享 GET `/internal/agent/tasks/conversation-executions/commands`，仅向真正认证的唯一live当前受控声明session投递该authority下v2；原native session仍仅v1。跨版本/跨lane不混投。Java当前v1 record保持原九字段，用共同view接口和单独v2 record作异构投影，不给v1增加nullable providerExecution；持久controlled locator未知/暂离线只能不投递，不能降级v1。v2 command 在旧9字段上仅增 `providerExecution`，完整形状见 fixture，后者仅 lane/consentId/bindingId/epoch/model/16/1/precallFenceVersion，来源是server BOUND/RESERVED事实，不是model输出或浏览器metadata。epoch十进制字符串；descriptor精确字段名为 providerLane、consentId、bindingId、bindingEpoch、modelId、maxInputItems、maxOutboundRequestAttempts、precallFenceVersion，不采用缩写。IDs沿用runtime安全ID约束；未知/额外字段拒绝。

Client在 lease/inputs/content/START之前精确匹配当前operator显式config的lane、binding、epoch、model、limits与协议；受控配置不接受v1命令，不 fallback通用codex/imagegen。输入manifest沿用v1 exact shape与bytes校验，但controlled lane **在下载和START前**拒绝>16；old native32不改。此包不改变已有PNG output/stage/commit wire。

## 5. v2 START端点与回执

```text
POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/provider-start-controlled-image
```

请求仅 schemaVersion=2、commandId、messageId、executionId、providerExecution、fence；fence仍现有 {version:number,token:string}。runtime filter须精确允许此路径/POST，不放开任意internal路径。旧 `/provider-start` 对controlled execution拒绝，不能返回旧 `{started:true}` 获得兼容旁路。

首次成功200 JSON（不用 owner JsonResult外壳）：schemaVersion=2、started=true、taskId、runId、executionId、commandId、messageId、providerExecution、leaseVersion。完整固定字段见 fixture；leaseVersion正safe integer，与当前lease完全一致，不重复暴露lease token。GET无此回执，重复/漂移409，坏正文400，scope不存在404，源故障503。失败错误沿用原runtime JsonResult error封装与状态，不因请求返回 started:false 伪装成功。

Client严格验证字段集合和全部identity/config/lease，只有首次真正成功回执才调用已有受控adapter。丢ACK/坏回执/重放/换epoch/未知均零外发；即使曾拿到回执，稳定ledger还要独占fsync claim，使第二executor/重启零次新HTTP。首次fetch失败/429/redirect/坏base64不retry/fallback，不宣称未扣费；claim不得删后再生。一次HTTP attempt不等于网络exactly-once或账单金额。

## 6. 五组共同 fixture 与实测要求

| 组 | 最小输入/故障 | 必须证明 |
| --- | --- | --- |
| wrapper_replay | 原请求、同键异consent/expectedVersion、issue/assign ACK-loss、GET404 | 原wrapper持久与201/200/409；唯一bootstrap；404无自动POST/legacy |
| authority_tuple | 全tuple各字段漂移、任意非空ref、自声明能力、换session/epoch | 无付费execution/consume/HTTP；跨owner404；未知ref拒绝 |
| three_atomic_segments | bind/reserve/start各段中间故障、Chat link失败、各ACK-loss | 全部rollback或exact只读恢复；START未知0外发；无半成功 |
| races_and_leases | revoke/START双方先提交、两个START、第二execution、错lease、重启 | 单次consume事实；只有一份callable receipt；最多一个fetch |
| input_boundaries | 0/16/17项、错MIME/hash/version/order、v1/v2混投 | 16完整物化；17不裁剪且reserve/download/START/HTTP=0；旧native32回归 |

各Owner必须用fixture真实跑自己边界，不只 assert fixture自相等。API用真实Spring事务/隔离MySQL验证回滚、DDL与并发；Client fake fetch计数/稳定ledger重启；Web真实composable+原intent+页面事件验证显式同意与恢复。保存exact commit/tree、selector、fixture字节digest、原stdout/XML/counts，保留环境/源码失败，不用测试个数替代34项产品用例。

## 7. 写集、依赖、退出条件

- BRIDGE-A（critical Owner）：API controlled aggregate/controller/readback、authority与consent内部顺序、grant/执行/START/command/当前声明、Chat coordinator/capability、necessary schema、事务/并发tests。**不改**Client/Web/SDD wire；不真实迁移生产，不选择账户/启用费用。
- BRIDGE-C（balanced Owner）：Client新sibling、v2 parser/配置匹配/START、poll runtime、focused tests；**不改**API/Web/旧fast权限或core HTTP账本防重。可独立按fixture先实施，不等待API正式启用。
- BRIDGE-W（balanced Owner）：Web新capability/同意UI/原intent wrapper+readback+页面采用/恢复tests，原v1仍安全。Client/API合同冻结后可平行施工，整合时验证对应服务。
- BRIDGE-I：先离线fake跨仓全链/双接应，再在具体真实费用授权内做真实Provider和浏览器验证。与多轮/所有媒体/保存/正式验收/完成共同满足产品34项后，按exact SHA版本发布并通知可验收。

性能只观测，资源/等待预算不作未经证据的拒绝门限；真实锁归属、鉴权、事务、幂等、明确传输超时与用户取消仍保留。没有新的独立Reviewer，Owner自检。未ready不合develop/启用/发布；不能停留在“core默认关闭”声称长期融合已落实。
