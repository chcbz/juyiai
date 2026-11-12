# 受控图像账户与单次请求：core 合同 v1

适用日期：2026-09-30。状态：**本core工作包冻结合同**；不是整个费用链路或产品已可用声明。基线API083f9846、Client1812e5b、Web7821209c。server START/原生v1/PRIVATE/TASK原合同不放宽；后续接线另补版本化合同。

## 1. 边界与权限来源

真实operator许可与taskOwner exact操作同意缺一不可。不得从余额/悬赏/托管租赁/技能订单或非空字符串推导许可。所有账户，包括本地profile，先有受信server-side operator delegation；不能凭客户端自报custody绕过此层。

operator配置源默认关闭/空：逐条绑定tenant/client/owner/target、bindingId/epoch、modelId、providerLane、custody/issuer/policyRevision、expiresAt、是否允许UNPRICED_EXTERNAL_ACCOUNT，以及本次maxOutboundRequestAttempts=1。期限、主体、model/endpoint/account由operator显式设置，无默认账户、模型、金额或自动延期。custody来自operator记录，不来自名为managedApiKeyId的会话属性——该属性也用于普通API key，不足以区别山寨/本地。

这是operator attestation/delegation，不宣称Provider已验证账户所有权。真实部署配置及付费调用仍需具体授权，不在本包偷偷配置。

## 2. 注册 sibling（不修改fast-v1或nativeBountyExecution-v1）

注册字段`nativeProviderCredentialBinding`：disabled形态恰为schemaVersion=1,enabled=false；enabled形态恰为下述9字段。

```json
{"schemaVersion":1,"enabled":true,"providerLane":"CONTROLLED_IMAGE_HTTP_V1",
 "bindingId":"operator_configured_binding","bindingEpoch":"1","modelId":"operator-configured",
 "maxInputItems":16,"maxOutboundRequestAttempts":1,"precallFenceVersion":1}
```

epoch是正十进制字符串，范围Java long；不接受秘密、URL、auth.json/hash、额外authority字段。服务器仅用当前成功注册且实际认证绑定的唯一live session作观察源；offline/undeclared/unsupported/ambiguous不能READY。正常API token换代、注册失败、断连及binding epoch变化清除旧事实；客户端声明不是扣费授权。

client侧仅真实受控HTTP executor/凭据配置/HTTP-poll协议均可用时声明enabled，不能将通用codex/imagegen executor当此能力。此次不广告native-v1的32输入能力；受控executor最多16（实际Provider协议限制），不静默裁剪。

## 3. owner consent HTTP

默认关闭的issuer接口：

```text
POST /agent/tasks/{taskId}/point-and-start-cost-consents
GET  /agent/tasks/{taskId}/point-and-start-cost-consents/{consentId}
GET  /agent/tasks/{taskId}/point-and-start-cost-consents/request
POST /agent/tasks/{taskId}/point-and-start-cost-consents/{consentId}/revoke
```

POST/原键request GET使用Idempotency-Key，revoke使用独立键及expectedVersion。JWT owner/client/tenant=0，不允许Runtime principal/浏览器自报owner。owner-safe不存在/越权404，坏正文400，同key异正文/版本409，真实源不可读503。GET private,no-store，绝不创建或推进记录、Agent或Provider。

issue严格body：schemaVersion=1、assignmentIdempotencyKey、assignment（现有v2 assign_and_start正文；不含任何授权/工具/费用字段）、providerBinding {bindingId,bindingEpoch}、acknowledgement=`UNPRICED_EXTERNAL_ACCOUNT_ONE_IMAGE_REQUEST_ATTEMPT`。首轮和requestedOperations本core仅GENERATE_IMAGE。服务器复用真实v2 validator，对当前confirmed requirement、canonical target、精确task-linked refs/owner bytes事实形成readonly Preview；不能写assignment/grant/bootstrap/消息。root锁内固定server assignmentBaseHash、inputSnapshotDigest和requirement内容身份。不接受浏览器hash。

receipt字段：schemaVersion、consentId、taskId、targetAgentId、state、version、assignmentIdempotencyKey、assignmentBaseHash、inputSnapshotDigest、providerBinding、modelId、custody、operatorPolicyRevision、pricingMode、maxOutboundRequestAttempts、expiresAt。version/epoch/时间使用十进制字符串，金额不提供；expiry取operator许可期限，没有任意默认TTL。

重复issue原key原body返回原receipt，不因查询或重放重新授权/延期；原key异body409。request GET的404不证明在途POST未受理，浏览器不得自动换key。

## 4. 持久事实和内部生命周期

独立agent_task_provider_cost_consent表，与旧intake/schema分开拥有。严格scope/key及consentId唯一约束，persist requestDigest、原assignment key/baseHash、当前requirement/task/精确inputs、binding/epoch/model/operator政策、expiry、状态/version、bind grant/assignment、reserve execution/run、consume lease、revoke key/digest。实际bytes留已有私有存储，不另建文件系统。

状态：ISSUED→BOUND→RESERVED→CONSUMED；在未消费前可REVOKED。expired为按可信时钟/政策投影，不靠GET写状态。每次变迁验活跃operator政策、真实当前binding、scope/assignment/grant/input摘要；消费后的同一execution仍可读/补交/对账，但不能获得第二次外部请求。

core提供内部bind/reserve/consume校验原语，无HTTP开放这些方法：

- bind：当前server assignment/grant下，exact baseHash/input匹配后绑定实际grant/version/assignment；不信任client costRef。
- reserve：当前grant重验、绑定唯一execution/run/input snapshot；不同execution拒绝，同一事实可只读重放。
- consume：实际START调用点先完成既有runtime/root/grant/execution/fence校验，再在**同事务**原子RESERVED→CONSUMED并写START；丢ACK不得重新外发。

**本core包还不接旧grant.costAuthorizationRef或Provider START，因此生产paid/newStart继续false/UNAVAILABLE。** 后续接线必须加真实transaction组合回归，不能把core方法模拟通过宣称整个START已获得这项保证。禁止“非空即授权”回退。

## 5. Client受控HTTP adapter

本包实现一个独立adapter，不把现有账户自动转换成API凭据。不选择/创建/切换实际Provider；operator显式配置enabled、binding/epoch、HTTPS base URL、API key环境变量名、modelId、稳定持久ledger根。缺失任一项不可用，绝不从CODEX_HOME/auth.json提取token。模型没有latest/default/fallback。

官方OpenAI Images参考已核实JSON图片生成和编辑、base64输入/输出；本adapter只覆盖其GPT image-style契约。资料来源：`https://developers.openai.com/api/reference/resources/images/methods/generate` 和 `https://developers.openai.com/api/reference/resources/images/methods/edit`。无参考输入用/v1/images/generations，有0<refs<=16用/v1/images/edits，data URL由本次已物化且验摘要的JPEG/PNG字节构造，不发送外部file_id/URL。n=1、output_format=png；不用GPT image不支持的response_format参数。

稳定ledger以scope/Agent和commandId（不以临时runDirectory、binding epoch或重启生成的随机id）标识同一调用意图。前置校验后，在本线程/profile私有ledger内用不跟随symlink的独占创建及持久化写入claim，再只发一次HTTP请求；第二个并发executor、重启/断连及已存在/损坏claim都不能再次调用。目录权限/ownership按实际受权根核验；不操作别的profile目录。失败/未知保留claim，不能删除后自动重试；run scratch清理不能删除账本。

单次fetch，redirect:error，无自动retry/备用账户/备用模型/URL下载。请求失败/响应未知不退款、不重跑、不声称未扣费。响应仅接受一项canonical base64 PNG真实bytes，仍经既有stage/commit验证。一次HTTP attempt不等于一笔已知金额/单次Provider账单，不宣传网络exactly-once。

adapter只在既有NativeLane已经收到成功START之后调用；本包无合法费用桥，不能在生产启用来绕过API。与normal codex executor隔离，无聊天模型前置、shell或外部工具调用。

## 6. source工作包与自检

API Owner：新current-binding declaration/lookup、operator policy、server preview、consent service/controller/DAO/entity/DDL及独立initializer、tests；窄增Grant接口/impl只读preview，不改assign付费/现有START/oldNative-v1或intake。Client Owner：独立受控executor/config/declaration/ledger及tests、最小profile和注册/调用接线；不改server/API、fast adapter或恢复旧费用回退。Web此包只读准备，不写未冻结跨仓UI wire。

必须有真实测试：负向自声明提权、旧会话/换代/多session、跨owner/client/target、refs版本/摘要、同key异body、撤销/expiry/epoch drift、并发同一claim/second executor/重启、redirect/network/429/invalid base64/multiple结果无第二次调用。Owner self-check，无Reviewer；所有Gradle经orchestrator。隔离MySQL验证DDL约束和并发core原语，不操作生产服务或数据。

后续仍需：旧grant/START同事务接线、native协议容量协商、Web exact consent/点将、同会话澄清/EDIT、多媒体/归档/交付验收、双接应及34产品用例、develop语音融合、exact版本发布。当前不冻结/选择真实账户、不启用费用或发布，不把core source通过当可验收。
