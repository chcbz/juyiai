# typed final 服务端严格校验与摘要合同 v1

冻结日期：2026-10-01。API 基线 `97989512351b6a409ac629e4546ce9fe698670e0`；Client `2f6907274ea5395980df0643c6b3898fa522a54f`。本包是自然多轮闭包的独立叶子实现，尚未实现/联调，不替代原子落库、pending question/CAS/resume、真实INSPECT、完整媒体、双接应、浏览器与分版本发布。

## 1. 目标与写集

新增三个路径，不改现75路径Owner的 Handler/Interactions/StepStore，不另建聊天引擎：

- `chat/jia-chat-service/src/main/java/cn/jia/chat/service/TypedDeliberationFinalValidator.java`
- `chat/jia-chat-service/src/chatDeliberationTest/java/cn/jia/chat/service/TypedDeliberationFinalValidatorTest.java`
- `chat/jia-chat-service/src/chatDeliberationTest/resources/contracts/typed-deliberation-api-final-validator-v1.json`

纯函数：严格校验服务端本轮facts/结果和完整binding、canonical typed final摘要、不可变深拷贝；无Bean/DB/网络/Provider/许可/START/文件读写/生成ID。继承[Client typed合同](typed-deliberation-client-result-contract-v1.md)第2–5节，普通正文永不当JSON语义结果解析。公开Java函数/record命名由Owner在自检中固定，不自行改变本合同。

## 2. 输入与严格语义

服务端调用者先从数据库锁定的exact turn/snapshot加载并验证上下文hash与callback binding；本helper只接受该可信marker内facts，不接受Agent/浏览器声称已requested。无marker的plain final沿用既有text-only路径；出现sidecar必须拒绝，typed请求缺sidecar也必须拒绝，不能降级；这些业务接线在后续原子持久化包完成。

`dispatchFacts`四键与`interactionOutcome`五键精确复用Client合同。Object输入允许普通Java JSON Map/List/String/Number/null/Boolean，不通过toString/number/string coercion。Map仅String keys，unknown/missing/duplicate字段拒绝。JSON文本入口使用严格原始JSON parser，重复key（任何层）、多根/尾随值、损坏Unicode、Markdown fence不修复；不能先用忽略重复的Map parser丢失证据。

- JSON numeric版本值数学意义恰为1可接受（1、1.0、1e0），不得Boolean/string coerce；经验证输出统一Integer1，与Client的JSON Number==1一致。Canonical writer不接float，所以必须先规范为语义整数1，不按raw词法计算摘要。
- ANSWER、CLARIFY、EXECUTION_PROPOSAL的互斥/null、requiredFacts、操作/源规则与Client完全一致。text/question为非blank有效Unicode scalar，允许正常正文LF，不能把instruction控制字符规则错误加到正文。content须String、非blank、与text exact相等，保留已有CHAT的200000 UTF-16长度域。
- instruction必须非blank、有效scalar、最多4000 Unicode codepoint、拒ISOControl，不trim/normalize；4000鸟emoji合法。
- sourceRefId沿用Client现boundedIdentifier：nonblank、最多512 UTF-16、无ISOControl、合法scalar；不根据“像路径”猜测权限，真正权限来自本轮已授权目录成员。
- facts referenceMode仅NONE/AVAILABLE；NONE无sources，AVAILABLE可空；catalog原输入manifest最多16项不变，唯一opaque source。GEN可零图源；EDIT恰一CURRENT_CONVERSATION_ASSET/image，操作属于supportedOperations。目录不代表已阅读字节，INSPECT不启用。

Binding是固定14字段record/对象：tenantId、ownerJiacn、clientId、conversationId、conversationGeneration、requestId、requestRevision、turnId、dispatchId、snapshotId、contextDigest、targetAgentId、route、taskId。全部String、不缺失；本悬赏现支持tenantId=0、route=CHAT。generation/revision为signed BIGINT范围canonical正decimal string；conversationId沿用现正decimal ID。其他ID保留源schema现域（tenant/owner/client50、snapshot64、request/turn/dispatch/target/task100），nonblank、无首尾strip差异、无ISOControl/损坏Unicode。contextDigest为sha256:加64 lowercase hex。不得String(undefined)/null或numeric→string匹配。

## 3. 唯一 canonical digest

`finalDigest = "sha256:" + SHA256(UTF8(CanonicalContextJson.write(digestInput)))`。使用现`CanonicalContextJson` v1：对象键按现Java lexical序排序、数组原序、null原样、无额外空白、string不normalize、数字仅规范后的整数；不要另建JCS/数字序列化器。

精确digestInput四层：

```json
{
  "domain":"juyiting.typed-final",
  "digestSchemaVersion":1,
  "outcomeContractVersion":1,
  "binding":{"上述14字段":"exact original values"},
  "content":"exact text",
  "interactionOutcome":{"完整5键union":"validated immutable values"}
}
```

contextDigest已绑定原snapshot/facts；digest再绑定完整callback/任务来源与typed union。不使用只有content的旧摘要作为typed重复判断，不把Agent传入的摘要当可信事实。`CanonicalContextJson.write`前必须消除不符合协议的Java对象、float/null语义漂移，所有结果深度不可变（null合法不能用拒null的Map.copyOf直接构造union）。

[黄金夹具](fixtures/typed-deliberation-api-final-validator-v1.json)固定中文CLARIFY的canonical UTF-8及sha256；对象key重排保持摘要，数组重排按完整语义变更摘要。同text但clarification/proposal/source/dispatch/context任一不同必须不同digest。后续persistFinal依此返回原重复fact或409，不能重新分配question/proposal。

## 4. 错误与权限

校验异常固定Reason为INVALID_FACTS、INVALID_OUTCOME、INVALID_JSON、INVALID_BINDING、INVALID_CONTENT、CONTENT_MISMATCH；code为TYPED_FINAL_加Reason，无content/文件路径/token/其他scope泄漏。这里不是HTTP endpoint，不伪造401/409/4xx已实测。validated proposal不是grant、consent、execution、pendingQuestion或START，helper不创建authority。

## 5. 实施验证与完整闭包

Owner原写集source-only+轻量静态自检，提交clean child/exacttree、所有fixture/source hash、实际/未运行状态。Java正常源图编译和JUnit仅在Main后续冻结矩阵、授予验证后经orchestrator串行，不能用手工javac/class-copy/跳依赖替代。30条fixture expectation当前均NOT_RUN。

下一协调包必须接入：snapshot可信typed marker与逐目标协商；raw final sidecar/正文同事务验证与digest；outcome/pending/proposal持久投影、CAS及查询恢复；DISCUSSION/CLARIFICATION_REPLY准入；唯一Hall composer问题/提议展示和明确确认后新v3意图。Handler/Interactions等原75路径Owner结束前不交叉写。本包源码通过仅关闭纯校验子项，不能宣称自然多轮/产品/发布完成。
