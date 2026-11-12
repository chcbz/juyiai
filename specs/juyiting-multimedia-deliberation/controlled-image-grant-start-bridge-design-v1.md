# 受控图像：Grant / execution / START 融合详设 v1

状态：**下一完整桥接包的详细设计，尚未冻结实施 wire、尚无源码/联调通过**。本文件不修改已冻结 core/native-v1 合同，不启用真实账户。实施前 Owner 必须基于验证后的 API core 精确树核对下面的事务与协议，然后冻结跨仓共同 fixture；不得只给 costAuthorizationRef 填字符串就开放收费。

后续合同补充：[桥接合同 v1](controlled-image-bridge-contract-v1.md)已冻结跨仓wire及共同预期fixture；本文原“拟议/尚未冻结”保留初稿历史含义。wire以补充合同为准，源码、真实测试、费用启用和产品验收仍须分别证明。

## 1. 与长期融合方案的关系

一个悬赏议事承载 CHAT / INSPECT / EXECUTE；受控 HTTP 是 EXECUTE 的 adapter，不新增聊天系统。明确“画一只鸟”且已受权可直达执行，不强制先调用 fast 模型。资料仍复用 owner 工作空间及精确 task-linked version，输出仍经现有 lease → stage/commit → 持久会话 asset → 可选归档 / 正式交付。

费用分为 operator 账户许可和 owner exact 操作同意。两种接应只改变凭据保管来源与各自 workdir，不改变 scope/摘要/事务规则。一次外部 HTTP 尝试不代表一笔已知金额；金额未知必须明确展示，测试不得擅自选择真实账户。

## 2. 实码确认的桥接缺口

API core 候选 `acab3411` 已提供 readonly assignment preview 和 ISSUED→BOUND→RESERVED→CONSUMED 原语，但尚未与以下写入共同提交：

- `AgentTaskExecutionGrantServiceImpl.assignLocked` 仍写 costAuthorizationRef=null 并创建唯一 bootstrap；付费 admission 仍只把非空 costRef 当作条件。
- `PersonalWorkspaceExecutionServiceImpl.createConversationExecution` 写 execution / inputs 后尚未预留 consent；`beginConversationProviderStart` 仅写旧 START 时间与 lease version，尚未原子消费 owner consent。
- native-v1 命令严格 schemaVersion=1 / 32 inputs，与受控 adapter 的16输入上限不等价；Client受控adapter不广告旧native-v1执行能力。
- `PointAndStartCapabilityService` 的 v1 始终费用UNAVAILABLE / newStart=false；Web core只issue/query/revoke，页面尚未接合法收费点将。

以上是 actual source gap，不是新增保守发布门槛。最终必须同时关闭，不发布“只有 core 默认关闭”的产品版本。

## 3. 拟议 owner 点将 wire

新增独立 owner 入口（待共同 fixture 冻结）：

```text
POST /agent/tasks/{taskId}/point-and-start-controlled-image
Idempotency-Key: <原 assignmentIdempotencyKey>
```

```json
{
  "schemaVersion": 1,
  "assignment": {
    "agentId": "<显式目标>", "workflowVersion": 2,
    "businessAction": "assign_and_start", "expectedTaskVersion": 6,
    "requirementRevision": 3, "requestedOperations": ["GENERATE_IMAGE"],
    "initialOperation": "GENERATE_IMAGE", "inputRefs": []
  },
  "providerConsent": {"consentId": "<真实签发记录>", "expectedVersion": "1"}
}
```

- assignment 是 Web 既有持久正文与 core issueBody.assignment，不能追加/更换费用字段、hash、owner、endpoint 或 token；头中的原键必须等于 consent.assignmentIdempotencyKey。允许0–16个 canonical JPEG/PNG task-linked refs，不静默截断32项或丢参考图。
- wrapper 在正式 POST 前与同一个原 intent 整体持久/readback。恢复不能从当前参考目录重建正文；旧 assign flow 对带 providerConsent 的意图仍不得绕过走旧接口。
- JWT owner/client/tenant 及原 task/target ACL 与 core 相同；坏正文400、越权/不存在404、同键异正文/版本/摘要漂移409、真实依赖不可读503。未配置完整 bridge 返回明确 unavailable，不调用 Provider。
- 首次只在 ISSUED、exact version、当前 operator / binding / model / expiry 与 preview 全部一致时办理。server 重算原 assignmentBaseHash / inputSnapshotDigest，不信浏览器 hash。
- 返回 wrapper 的 owner-safe grant 与 bound consent；receipt 是受理事实，不是成果/验收。grant.paidExecutionAuthorized 的含义必须在共同 fixture 中限定为“持久受权事实”，不能等于还有一次可用新调用。
- 既有 original-key assignment-operation GET 继续纯读。应追加 versioned controlled receipt 投影用于刷新恢复，但不得通过GET补绑定、预留或START。404仍不能证明在途POST未受理。
- 旧普通/funded/auto-assign接口不改变正文或权限，不能给合法桥造一个 costRef fallback。

## 4. 服务端 aggregate 与锁/事务

### 4.1 点将及绑定

建立应用编排服务同时依赖 Grant service 与 consent service，**不要让二者相互构造器注入造成环**。外层采用现有 REQUIRED owner-scoped task-root transaction；同事务中完成：

1. 校验原键、正文、最新 requirement、canonical target 与精确参考文件；锁现有 grant action/bootstrap、target/input rows。
2. 执行原受控点将、grant与唯一 bootstrap 写入，使用原 assignment hash 规则，不重算一个不兼容 hash 域。
3. 对同一个真实 grant/version/assignment 绑定 exact consent；持久服务器签发的 cost authority reference（如果沿用现有列，它仅是查证记录的定位符）。绑定冲突/写入失败必须回滚 assignment/event/grant/bootstrap，不能补偿式“先成功点将再绑”。
4. 同键重放读取并比对已绑定事实，返回原 grant/consent，不再签发、不延期、不重复 bootstrap。已消费的历史回执可观察，不因此获得第二次调用。

root 永远先锁；同一aggregate重入已经持有的锁，不另起 REQUIRES_NEW。上线前固定 grant/outbox/target/files/consent 的具体顺序，并用真实事务测试验证跨任务共有target/file、revoke/assign/start竞态。现有 core 的内部 grant 验证不得在 execution 锁之后引入新的、顺序相反的 root/target锁。

### 4.2 创建 execution 并预留

复用既有 durable interaction / intent / execution，不从浏览器媒体卡直接启动。创建执行时在同一个root aggregate中重验当前 grant、assignment、confirmed requirement、输入bytes，以及绑定许可，写唯一execution/run/input snapshot，并将 BOUND→RESERVED 绑定该 execution/run。

任一写入失败全部回滚；同一execution原意图重放仅核对既有 RESERVED/CONSUMED mapping，不换run。第二execution不能占用已reserved/consumed consent，即便同一grant或同一Agent。不能用“查询原grant成功”替代预留。

### 4.3 实际 START 原子消费

先执行既有真实 runtime/root/grant/execution/fence/lease 与实际输入摘要校验；再在**同一次事务**完成：

```text
RESERVED(exact execution/run) → CONSUMED(exact lease identity)
+ execution.conversationProviderStartedAt / provider lease version
```

任一步失败都不提交START或消费；两个caller只有一个首次成功。operator、binding epoch/model/expiry变化或撤销先提交，则旧START拒绝；START先提交则 permit 已消费，不伪装撤销或退款。ACK丢失时Client不得调用Provider，也不得根据GET或第二次START“已消费”投影获得新的外发许可。

scope/target/输入/grant事实验证必须替换“costRef非空”准入。generic paid admission 对未知/伪造 reference 拒绝，不存在兼容旁路。费用的“新调用准入”与“读取/提交既有run、浏览器读取/归档已产生asset”分开：许可过期/消费不让已有私有产物无故消失，仍按当前任务或asset ACL处理；也不能通过既有结果读取接口再获新调用。

## 5. 版本化 Client 协议

不能把受控16输入能力伪装成native-v1的32输入。下一共同 fixture 采用独立 controlled capability sibling 和 command schemaVersion=2，旧fast-v1/native-v1保持不变。

v2 command 保留既有task/run/conversation/command/message/instruction/output identity，增加精确非秘密 provider execution descriptor：providerLane、consentId、bindingId/epoch、modelId、maxInputItems=16、maxOutboundRequestAttempts=1、precallFenceVersion。其来源是server bound/reserved事实，不是浏览器提示词。

Client在读取输入和START之前严格验证descriptor与当前受控配置完全一致；无法理解v2、binding/模型不匹配、17项资料等明确拒绝，不能退回generic codex/imagegen。命令只投递给真实认证且唯一live当前受控声明的session。

START v2成功回执应带schema、execution/run/consent及binding/model/lease identity，Client精确比对；旧`{started:true}`不足以在v2开启外发。只有收到首次实际成功v2 receipt后，现有私有持久claim→单次fetch→stage/commit adapter可运行。失败/未知保留claim，无retry/fallback，不宣称未扣费。具体field/type/错误及响应字节要在fixture冻结，不靠本文拟议字段直接各仓自行发明。

## 6. Web体验及状态

真实capability v2区分“受控执行链已具备、需本次同意”和“已有exact consent可办理”，不把native技能名、配置或非空记录当READY。v1费用仍UNAVAILABLE；未知版本不能静默降级legacy。capability GET不签发或消费费用。

用户点将流程：读取权威requirement/完整task refs/当前binding → 展示来源与金额未知/一次HTTP尝试范围 → 用户明确同意 → 原四项key/body持久 → core issue → 合法点将wrapper原键POST → original-operation GET → 精确采用同一首轮议事。任何未知都保留原意图并只读核对，只有用户显式继续可原键/原正文重放。切换身份/task/target使迟到回执失效，不删服务端操作。

刷新、生成中、未知、可预览、已归档、已正式提交、已验收、领域任务完成分别显示；不将BOUND/CONSUMED/START或客户端inbox completed当画鸟交付。允许用户继续补充文本/图片，下一轮动作必须有自己的exact授权，不无限复用首轮一次请求同意。

## 7. 工作包与验证闭环

| 包 | 写集/责任 | 依赖与最小证据 |
| --- | --- | --- |
| BRIDGE-A | API应用aggregate、Grant权威reference查证、execution预留/START事务、versioned投影/command、tests | 已验证core树；真实Spring/JDBC回滚、并发消费与revoke race；fake计数不做真实收费 |
| BRIDGE-C | Client controlled sibling、v2 command/receipt、descriptor/config比对、tests | 同一冻结fixture；旧native/fast回归、丢ACK及17项拒绝、稳定ledger重复0外发 |
| BRIDGE-W | capability v2、同一个原intent扩展、显式同意和页面采用、tests | 相同fixture；原键恢复、404未知、绑定/身份/navigation栅栏，无legacy旁路 |
| BRIDGE-I | 跨仓真实服务/双接应浏览器与后续多轮 | 上述exact源码及schema；先fake跨链，再取得具体真实账户/调用授权才做Provider验收 |

每个包Owner自检，不设Reviewer；同文件不交给多个Writer。正式测试构建遵循当前用户授权与orchestrator串行规则。tiny源码验证只作定向证据，不冒充正常模块/整套启动/产品验收；不要因已有tiny通过省掉真实事务/fixture。

此外仍要冻结并完成[澄清/续办/上一稿EDIT](multiround-followup-design-notes-v1.md)、文本/图片/音频/文件混排与归档/正式验收、最新develop语音融合及精确版本发布。34项产品用例不因BRIDGE-A完成变PASS；整个需求达到可验收后才通知用户。
