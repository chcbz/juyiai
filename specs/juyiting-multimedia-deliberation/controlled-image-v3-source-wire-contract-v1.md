# 受控图像 v3：精确来源、上一稿修改与运行 wire 合同 v1

日期：2026-10-01。状态：**本文件冻结新增 runtime wire，供 API/Client 实施；不是能力就绪、Provider授权或产品验收证明**。它落实[多轮详设准备](multiround-followup-design-notes-v1.md)的实际来源/编辑缺口，不替代待落地的 owner interactions/每意图费用同意/pending clarification 业务合同。完整目标仍包括图片、音频、文本、文件、保存、交付、验收与双接应。

基准 Client `5548052`；已有 v2 [桥接合同](controlled-image-bridge-contract-v1.md)及其 fixture 保持字节不变。API当前桥候选须先完成实际验证。共同样例见 [wire fixture](fixtures/controlled-image-v3-source-wire-v1.json) 和旁置 SHA；均为虚构离线输入、状态NOT_RUN，不含真实账户或调用许可。

## 1. 长期决策与旧协议边界

- 新 EXECUTE 意图使用新 execution/run、commandId、独立 consent/authority 映射；同一 task/assignment/conversation 不重新点将，不覆写首轮 grant 单locator，不复用旧CONSUMED请求。
- EDIT读取精确当前会话asset，不要求先保存个人空间，不将asset伪装成workspace文件。不变更或覆盖原稿；新稿有自己的producer lineage。
- 澄清在execution/RESERVED前完成。Client不新增聊天模型前置。回复澄清可推进同一持久规划，但只能在补齐本轮精确授权之后形成可执行意图；不是任意文本自动获得收费权。
- 普通讨论、只读状态与实际执行占用分开。不得用一个busy状态封死WAITING_USER回复，也不得依据性能SLO跳过操作。
- v1/native 32输入，v2/controlled 16输入及既有command/START/declaration保持原合同。新v3为独立sibling和严格parser，不给旧record增加nullable字段或做跨lane降级。

## 2. Capability sibling与真实组合

新增注册键 `controlledImageBountyExecutionV3`，schemaVersion=1，transport=`PERSONAL_WORKSPACE_CONTROLLED_IMAGE_HTTP_V3`；commandSchemaVersions=[3]、leaseProtocolVersions=[1]、providerStartFenceVersions=[3]、resultCommitProtocolVersions=[1]。共同fixture固定disabled形状：enabled=false、operations=[]。其余既有credential-binding九字段不变。

真正就绪时operations包含GENERATE_IMAGE、EDIT_IMAGE，分别声明以下精确矩阵（新增字段不能偷偷放进旧sibling）：

| operation | 唯一source种类 | 数量 | 实际MIME |
| --- | --- | --- | --- |
| GENERATE_IMAGE | TASK_LINKED_WORKSPACE_VERSION | 0–16 | image/jpeg或image/png |
| EDIT_IMAGE | CURRENT_CONVERSATION_ASSET | 恰好1 | image/jpeg或image/png |

**本次Client实现slice必须注册disabled**：只有API的source resolver/intent authority/START、Client真实poll/lane/adapter及组合验证齐备，才能另行启用声明。单独adapter或mock通过不是READY证明；默认关闭不等于完整产品完成。

enabled的精确完整形状也固定在fixture，只作后续组合完成后的预期：每个operation恰operation/inputManifest/resultManifest；inputManifest恰schemaVersion=3、minItems、maxItems、mimeTypes、sourceKinds；resultManifest与旧schema-v1 PNG单输出同形状。注册始终以disabled实例实施，本slice不得用预期enabled样例冒充实际READY。

独立inbox：`GET /internal/agent/tasks/conversation-executions/controlled-image-v3-commands`，响应为原生wire恰`{"items":[...v3 command...]}`，不套owner接口的JsonResult；batch上限沿用已有controlled lane 16，列表条目仅本合同v3。认证、唯一live session、runtime instance及same-session credential binding按现有控制链重验；旧共享inbox仍只投递原支持版本。unknown/v2混入v3列表直接拒绝，不回退旧lane。

## 3. Command与身份

命令顶层**恰13字段**，样例全部见fixture：schemaVersion=3、executionId、taskId、runId、conversationId、commandId、messageId、operation、instruction、inputSnapshotDigest、outputContentMimeType、outputId、providerExecution。

- operation仅GENERATE_IMAGE或EDIT_IMAGE；outputContentMimeType=image/png、outputId=output_1，沿用既有instruction长度/标识文法，不新增任意阈值。
- executionId与task/run/conversation稳定绑定。领取/续租继续原POST lease/lease-renew端点及冻结正文/响应，不增旧parser字段；新command.executionId必须与领取lease.executionId一致。
- commandId/messageId由本轮持久意图稳定派生，不使用临时runDir、随机epoch或重启随机ID。
- providerExecution仍恰原8字段，不塞operation/source：providerLane、consentId、bindingId、bindingEpoch、modelId、maxInputItems=16、maxOutboundRequestAttempts=1、precallFenceVersion=1。
- bindingEpoch等新增业务long字段为canonical decimal string，范围为Java-long；版本/长度不得转为不安全Number。已有lease-v1 fence.version/leaseVersion继续保持原safe整数。
- consentId为真实server签发的`consent_`加32小写hex，不能用任意非空定位字符串；样例账户/模型不构成配置默认值。

## 4. 来源快照与摘要

新增受权只读调用：`POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/inputs-v3`，正文为原lease-v1 fence；每项字节继续既有`POST /conversation/inputs/{inputRef}/content`及同fence正文，不改为GET或另造lease headers。服务端按持久execution schema选择来源解析，不能由owner或runtime query参数改变版本/来源。身份/runtime lease/request fence沿用原链；具体lease headers与原query规则不扩宽。

snapshot恰7字段：schemaVersion=3、executionId、leaseVersion、operation、inputSnapshotDigest、noReferencedMaterials、inputs；每个input恰5字段：inputRef、source、contentMimeType、byteLength、sha256。inputRef严格input_1..input_n、顺序持久固定，不排序、不截断、拒绝重复精确来源。byteLength为正canonical decimal string，比较实际Buffer长度时使用BigInt，不根据未验证长度分配Buffer；sha256为64小写hex。

source严格联合类型：

- workspace：恰kind=TASK_LINKED_WORKSPACE_VERSION、fileId、version（正decimal string）、purpose=REFERENCE。
- asset：恰kind=CURRENT_CONVERSATION_ASSET、conversationId、conversationGeneration（正decimal string）、assetId、assetRevision（正decimal string）、producerRequestId、producerStepId、producerExecutionId、producerRunId、producerOutputId。

asset的完整producer tuple由服务端scope/live-generation/asset-revision/source store查证生成，不接收浏览器自报lineage/hash作为授权。必须重验owner/client/tenant、task/assignment/target/grant、OUTPUT_COMMITTED、真实MIME/hash/长度及当前源ACL。URL、客户端路径、latest或第一张图推断都不可替代精确引用。消费后原已提交成果的可读性不依赖operator当前许可，新的EDIT外发仍须本轮明确授权。

摘要域恰schemaVersion=1、executionId、taskId、runId、conversationId、operation、noReferencedMaterials、inputs。采用项目CanonicalContextJson v1：对象key按词典序递归排序、数组保序、compact UTF-8、字符串JSON转义、整数不含浮点。排除leaseVersion/临时路径；fixture保存完整canonical UTF-8文本与SHA-256。Client重算并与command/snapshot一致，不只相信两个收到的hash相等。

本域是runtime输入身份；owner consent预览的payload/source摘要是另一个域，不能在execution尚未创建时伪造本域已持久运行的事实。后续API intent-authority映射须同时绑定精确payload/source及真正runtime input digest。

## 5. 首次START与回执

新增且仅用于v3：`POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/provider-start-controlled-image-v3`。

请求恰8字段：schemaVersion=3、commandId、messageId、executionId、operation、inputSnapshotDigest、providerExecution、fence（原lease-v1恰version/token）。首次成功data恰12字段：schemaVersion=3、started=true、taskId、runId、conversationId、executionId、commandId、messageId、operation、inputSnapshotDigest、providerExecution、leaseVersion。

服务端在同一root-first事务重验本轮intent→consent→run、完整operation/source/digest、live scope/lease、真实输入字节和当前ACL，原子RESERVED→CONSUMED并写START。不能借首轮grant locator查另一许可，不能在锁Chat行后反序创建Agent execution；失败全部回滚。重复START409；ACK丢失、坏回执、403/404/409/503均零Provider外发，不自动重试、新建key或返回第二份started:true。源读取和结果提交仍保持取消、当前ACL及run fence检查，不拿EXISTING_RUN恢复新的调用资格。

Client对首次receipt的所有字段/descriptor/operation/digest/lease严格与原command及lease一致；未知字段拒绝。没有成功精确receipt，executor/claim/Provider都不得启动。

## 6. 输入物化、Adapter与成果

复用现有run隔离、私有inputs/outputs/scratch、无覆盖wx、nofollow、真实MIME/长度/hash校验、PNG输出验证/stage/commit。v3物化结果必须保留immutable source descriptor和decimal长度，不能调用现有workspace-only materializer而丢来源。

传入executor：`execute({command,runDirectory,inputs})`；operation/source/digest必须保留到真实HTTP payload及durable requestDigest。不再只按inputs.length猜业务动作：空GENERATE用既有generations分支；workspace参考GENERATE和单asset EDIT用既有edits分支。沿用当前受控HTTP body、n=1、PNG、一次fetch/redirect:error/无retry或备用账户；不切Provider或选择真实模型。图片只来自本次已受权物化的data URL，不外发file_id/URL。

pre-call claim key仍profileId+agentId+commandId；operation、inputSnapshotDigest、canonical source及最终body进入requestDigest，不能把epoch/runDir加进key逃过旧claim。exclusive create、file+directory fsync、损坏fail-closed、重启/并发不重发保持。一次HTTP attempt不宣传网络exactly-once或已知扣费金额。

新EDIT稿按现有output_1 PNG提交为独立conversation asset；新旧稿同时可预览下载。主动归档及正式交付是后续独立动作，不在Client创建第二套workspace或自动保存。

## 7. 实施包与验证

- Client（可与API桥修复并行）：独立v3 strict command/source/digest/START/lane；operation-aware adapter、注册disabled sibling及真实poll组合；保持旧v2 fixture/hash/parse/claim测试。API端点未实现时不得广告就绪。
- API（桥验证后由同Owner继续）：新sourceResolver/persisted inputs、每execute intent独立authority、v3 command/inbox/inputs/START、同库root-first事务；再闭合owner follow-up admission/pendingClarification和explicit permit。
- Web（业务HTTP合同冻结后）：composer和成果卡统一Hall follow-up；WAITING_USER可回复、原key恢复、上一稿精确引用；不直接调用native endpoint，不假造asset/workspace。

必须验证：3个合法样例canonical字节一致；严格字段/数字/来源/操作/数量mutation；foreign/旧revision/generation/lineage/取消拒绝；第17项零下载/START/fetch；digest/operation/receipt漂移零fetch；ACK丢失、旧consumed、同command变源/并发/重启/坏claim不得再次调用；原v1=32、v2=16及旧fixture字节不变；实际poll→lease→source bytes→START→adapter→PNG stage/commit组合。澄清等待时execution/reserve/command/START/claim/fetch全部不存在。

本文件只冻结新runtime增量，不把owner澄清/自动规划/费用同意的未落地接口当完成。完整34项产品与双接应/真实Provider/浏览器、正式交付验收及exact版本发布依然必需。Owner自检，无Reviewer；Gradle经orchestrator。性能只记录观测，不新增SLO拒绝门槛。
