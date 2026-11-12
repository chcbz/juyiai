# Web 外部图片请求同意：core 实施合同 v1

状态：冻结本 Web 源码包；基于 Web7821209 与受控图像 core HTTP 合同。此包接 issue/query/revoke，不接点将费用桥、不开放 paid/newStart，不调用 Provider。真实点将、START、续办与产品验收仍为后续完整范围，不据 core 自检标可验收。

## 1. 复用一个持久原点将意图

复用 `hallPointAndStartIntent` 的 tenant/client/owner + task 存储键和原 `schemaVersion=1` 外壳，不建立另一个能绕开原意图仲裁的存储。原 key/body 含 canonical assignment，保持精确不变；可加可选扩展 `providerConsent`，无扩展的原记录兼容不变。

扩展严格为：`schemaVersion:1`、`issueKey`、`issueBody`、`receipt:null|coreReceipt`、`revoke:null|{key,expectedVersion}`。issueBody 必须与 core 合同完全相同，嵌入原 key/body；绑定ID/epoch/ack严格校验，operations仅GENERATE_IMAGE，精确 refs最多16，不静默裁剪。四项原assignment key/body与consent key/body必须作为一个intent在issue POST之前持久并readback。

所有 key/body/binding/ack immutable，receipt仅按服务端合法单调状态与version更新，已知receipt身份/hash/model/operator信息不可替换。revoke key/expectedVersion一旦持久也不可替换；同键不同正文拒绝。扩展损坏/未知字段/不可读存储为CORRUPT/UNAVAILABLE，不认为无原操作。普通点将flow对带该扩展的intent，绝不调用旧 `/assign`，明确提示使用费用意图恢复；其原key不能变更/清除。

本core不定义放弃/删除记录的接口；撤销后仍保留原receipt和意图，不伪称可以新建。后续真正重新办理须有领域终态处置合同。

## 2. Composable 与 HTTP

新增 `useHallPointAndStartCostConsent`，输入 agentApi/actorScopeKey/storage/keys，输出 state、busy、prepareAndIssue、checkOriginal、resumeOriginal、revokeOriginal、dispose。可另有纯 receipt/intent helper，命名由Owner决定。

prepareAndIssue仅接受已固定的canonical assignment与显式binding/ack，current身份scope、任务、target一致，普通原intent或已有扩展优先恢复，不新建/覆盖。在POST前将完整immutable record存入同一个原点将store。issue调用：`POST /tasks/{taskId}/point-and-start-cost-consents`，原issue key；读取原请求：`GET .../request`带原issue key；revoke使用独立持久key和expectedVersion。仅使用已冻结四个core端点，不发 `/assign`、不发legacy chat、不创建会话、不产生paid capability。

未知POST/GET错误保留原键/正文。刷新/checkOriginal只GET；GET404不证明原POST未受理，不自动POST。resumeOriginal须由用户明确调用，先GET，只有core原请求404允许在本次显式恢复中重放原issue key/body；网络/503/冲突不偷偷新建请求。revoke UNKNOWN也先GET核对：REVOKED回执不再POST；未撤销状态的明确继续只重放已持久revoke key/expectedVersion。

actorScope变化、dispose、换task/target或新operation generation后，旧响应不得持久或覆盖UI；同时只能一个active写操作。身份切换不清除另一身份持久记录。业务等待无性能deadline。

## 3. Receipt 验证

沿用 core DTO，顶层恰为 schemaVersion,consentId,taskId,targetAgentId,state,version,assignmentIdempotencyKey,assignmentBaseHash,inputSnapshotDigest,providerBinding,modelId,custody,operatorPolicyRevision,pricingMode,maxOutboundRequestAttempts,expiresAt；binding恰为bindingId,bindingEpoch。值为 core 已冻结类型，不容忍 extra authority 字段。

schemaVersion=1，version/epoch/expiresAt为正canonical Java-long十进制字符串；state仅ISSUED/BOUND/RESERVED/CONSUMED/REVOKED；assignment key/task/target/binding匹配本地intent，hash为SHA-256，pricingMode=UNPRICED_EXTERNAL_ACCOUNT，attempts=1。custody枚举以API operator policy实码为准；不从字符串判断用户余额/费用权限。首次issue成功要求ISSUED；原GET可以投影后续合法状态，但core Web不会促成BOUND/RESERVED/CONSUMED。

同version异state/其他内容拒绝，version不回退；hash、binding/model/custody/operator/expiry不更新。不将expired改写server state，不将ISSUED或GET READY转成费用已授权。

## 4. 写集与最小自检

Web Owner独占：新增consent intent/receipt helper、composable、focused tests；修改现有 hallPointAndStartIntent 的可选扩展验证/immutability 和 useHallPointAndStart 的安全恢复guard。此包不改页面/选择器/能力v1 parser/API/Client，不启用真实账户。后续stage2合同才接按钮与正式点将。

测试覆盖：POST前单intent持久；普通原intent优先；同key异body/binding/ack；receipt错target/key/hash/epoch/额外authority及version回退；大long精度；16/17 inputs；所有core状态；跨身份/task迟到fence；存储坏/缺失；UNKNOWN→GET404无自动POST→明确原键重放；撤销UNKNOWN恢复；普通point flow不能绕过费用扩展发assign；原point tests回归。测试用现有离线依赖，不装全套、不跑production build。提交exact SHA/tree和实际selector/计数/日志，Owner自检，无Reviewer。

## 5. 与真实 API 过期投影的合同修正（core v1.1）

API候选 `view` 明确对未消费/未撤销且过期的ISSUED/BOUND/RESERVED行返回state=EXPIRED而不写入状态或递增version。初稿第3节仅五种wire状态不足以接收该真实投影。本节覆盖初稿该点；数据库生命周期仍五状态，Web wire还接受第六种EXPIRED，不用客户端时钟授予/撤销权限。

- 首次issue成功要求ISSUED；query可以返回EXPIRED。相同version的ISSUED/BOUND/RESERVED→EXPIRED是唯一允许的非完全相同回执；其他不可变字段必须完全一致。不因GET过期回执递增server version。
- EXPIRED不可在相同或更高version回到ISSUED/BOUND/RESERVED；GET发现真实REVOKED/CONSUMED且version更高可投影，代表真实终态，不是新授权。已REVOKED/CONSUMED不能被EXPIRED覆盖。EXPIRED→EXPIRED仍按原version单调及facts不变规则。
- EXPIRED可用原撤销接口按原version显式撤销；任何query/resume不重新同意/延期/换key，过期receipt不能开启paid/newStart。
- prepareAndIssue的acknowledgement必须由明确调用提供，不设默认值；缺失/错误ack不能持久新intent或POST。函数参数不是用户费用权限，真正UI后续须先明确展示并取得本次同意。
- 公共composable提供纯UI上下文切换入口（如selectTask），或显式可观察task/target上下文参数；切到另一task/target应使旧pending响应失效、不得污染新UI/新身份。该动作不取消服务端操作，不删除原持久intent。后续页面必须调用/传入实际选择；本core尚不接页面，不声称已验证真实页面导航。
- 新回归证明：expired相同version真实投影、终态/immutable保护、过期撤销/恢复无assign、显式ack缺失零写入、同身份换task/target迟到响应fence。
