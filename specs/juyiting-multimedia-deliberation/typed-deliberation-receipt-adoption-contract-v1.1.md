# Typed受理回执与当前请求投影的领域分离补充 v1.1

冻结：2026-10-01。继承[原子续办合同v1](typed-deliberation-atomic-followup-contract-v1.md)与其不变golden fixture；本补充**不改schemaVersion、不增删wire字段、不改变原合同/fixture hash**。来源是实际Main Web边界失败与现有API请求状态源码，不是新增没有证据的检查。

## 1. 实际问题与决策

Web child `891a1ec`修复了原6种不匹配回执，但将`RequestView.state/stateVersion`强制等于原receipt的`ADMITTED/0`。现有ChatDeliberationService真实admit创建request聚合态`RUNNING/0`、turn态`RECEIVED/0`；final后聚合态可为`COMPLETED`，状态版本随事实前进。Main真实production composable对合法RUNNING初态及COMPLETED终态均拒绝采用。API当前typed候选又直接把request聚合state复制进Admission，违反v1 golden的ADMITTED领域语义。两处必须同时修正；不得为了过测试改写旧RequestView或要求Agent等待GET后才处理。

**持久受理回执、请求聚合状态、turn推理状态是三个不同事实。**

## 2. 不变受理回执

现有v1受理字段与golden保持不变。成功typed Admission记录并返回：`state="ADMITTED"`、`stateVersion="0"`；这是本原操作已持久受理的事实，不是RUNNING/COMPLETED状态投影。`eventCursor`固定原受理事实的日志高水位；同键同正文replay返回同一原receipt，只有原合同允许的`replay`标志改变。

不得复制当前RequestView.state作为Admission.state，不借此新增执行状态或收费事实。无需为此给旧chat_request/chat_turn添加字段。RequestView继续由原GET返回当前领域状态，不要求匹配ADMITTED。

## 3. 新typed前端采用闭包

新typed适配器保持严格受理receipt结构、ID、单turn与回执URLs校验。读取GET后，先在不修改任何UI状态的条件下验证：

- requestId、userMessageId、唯一turnId与原receipt一致；requestRevision必须为新typed request的规范`"1"`，turn revision与request一致。
- request/turn都属于相同conversationId、conversationGeneration和显式目标Agent；当前身份/会话/任务/assignment guard仍有效。旧历史成果只读不受影响。
- 当前request.state属于原CHAT聚合态`RUNNING|PARTIAL|COMPLETED|FAILED|CANCELLED`，stateVersion为canonical decimal string；不要求等于原receipt的ADMITTED/0，不把合法版本前进判作回执不匹配。
- turn状态和version/lastDeltaSeq/finalMessageId按现有durable turn域校验。已有较新同request投影不得被迟到低版本或非终态回读降级；采用前后的current guard继续阻止目标/身份漂移。

验证成功采用权威request/turn，再只读同一conversation content；不伪造本地user ID，不再POST，不将content读失败变成未受理UNKNOWN。失败回执零状态污染、零content二读、零POST。仅修改新typed入口，不改变旧`applyRequestView`的全局兼容语义。

## 4. 必须补的真实测试

- API新受理返回ADMITTED/0，同时原GET真实返回RUNNING/0；final之后原receipt原键replay仍ADMITTED/0，GET可COMPLETED/更高版本。
- Web合法RUNNING request/RECEIVED turn可采用；快速final导致GET已COMPLETED/FINAL_PERSISTED同样可采用。
- 原不匹配userMessage/turn/generation/target/conversation/revision负向继续拒绝，迟到target及content失败/UNKNOWN保护不退步。
- 迟到较低request version不得覆盖同request较新的终态；测试使用真实composable与明确反例，而非只验证helper。

Main固定probe `receipt-progress-probe-v1.1.mjs`本轮再次实测891：两合法采用失败、一错误receipt拒绝通过；同一精确候选13文件193通过/0失败，原六边界、UNKNOWN恢复、同版本OPEN及七项回执probe继续通过。七项probe的正向RequestView为合成ADMITTED，不能据此证明真实RUNNING/COMPLETED兼容；真实状态反例具有独立证据。见[本轮便携证据](integration-evidence-20260928/typed-receipt-adoption-20261001/manifest.json)。补充fixture记录跨端共同预期NOT_RUN，不能把部分mock probe结果冒充API/产品通过。

## 5. 源码范围与交付边界

API原26path Owner修正其ChatTypedDiscussionAdmissionService及对应测试，不侵入独立V3 source/schema范围；Web原Owner修改其新typed采用及测试，保留原voice harness修复。保持原16项原子闭包、62V3及82V2验证要求，组合后再做真实服务端/浏览器。未运行生产迁移/Provider/发布；不改变完整多媒体、真实INSPECT和双接应目标。
