# 自然讨论的 typed result：Client/API 追加合同 v1

日期：2026-10-01。Main 冻结的首个自然语义执行包，**尚未实现/未联调/未激活/未验收**。Client基线 `71b26ce69d25a59f223499854b692e597b57d911` / tree `9675a2d85bf08a8e1af45d7c8e76106352db55a3`。不覆盖既有fast hosted wire黄金字节、初始点将、schema3 EXECUTE、受控START/费用和成果合同。

## 1. 长期选择：一个原子final，不增加并行结果事件

采用既有 `chat.message` final 的严格追加sidecar，而不是准备稿候选的独立 `chat.interaction.outcome` 事件。原因是正文与ANSWER/CLARIFY/proposal必须在一个绑定dispatch的final中校验、去重和持久化，不能发生正文先完成、澄清后丢失或两个终态各自竞争。原text final仍是原text final；**绝不把普通聊天正文、代码块、用户JSON或Markdown重新解析成proposal**。

typed planner只用本轮服务端固定snapshot中的文本历史/资料目录；SOURCE引用不等于读过文件。模型可以提出建议，不能创建ID、许可、consent、operation grant、execution、command或START。自然后续编辑依然通过新意图独立preview/ack/issue/admit；初始GENERATE grant不借权EDIT。本包保持INSPECT真实不可用，后续固定manifest/授权/引擎能力另闭环，不把NONE/AVAILABLE称为INSPECT。

## 2. 服务端可信dispatch request

只对modern durable、route=CHAT、juyiting bounty的exact目标Agent启用。profile显式 `typedDeliberationEnabled=true`，且已测量匹配本仓native app-server schema、引擎已初始化且未关闭；否则声明UNAVAILABLE并在engine开始前拒绝typed请求，无legacy/CLI execution fallback、无未授权资料读取。

服务端在已验hash的 `contextSnapshot.facts.typedDeliberation` 写入以下**精确且唯一**对象（不是浏览器可写字段）：

```json
{
  "schemaVersion": 1,
  "referenceMode": "AVAILABLE",
  "supportedOperations": ["GENERATE_IMAGE", "EDIT_IMAGE"],
  "availableSources": [
    {"sourceRefId":"source_1","kind":"CURRENT_CONVERSATION_ASSET","mediaType":"image"}
  ]
}
```

referenceMode仅NONE/AVAILABLE。NONE必须sources=[]；AVAILABLE可以无可选源（例如用户没有选图），不得伪称看图。supportedOperations是去重的已实现目标操作子集，仅GENERATE_IMAGE/EDIT_IMAGE；它表示可提出的运行时能力，不是授权许可。GEN proposal可无sources；EDIT必须唯一合法CURRENT_CONVERSATION_ASSET/image。availableSources每项仅三个字段，kind为TASK_WORKSPACE_FILE或CURRENT_CONVERSATION_ASSET，mediaType为text/image/audio/file；sourceRefId沿用已有exact bounded identifier，不接受路径/URL/模型提供的摘要、版本、producer tuple。目录项唯一，资料上限沿用已有受控input manifest，而不新增性能/总会话门槛；最终仍受现snapshot/facts实际wire域约束，不静默截断。

Client必须用既有validateChatDispatch/validateContextSnapshot验tenant/client/owner/request/revision/turn/dispatch/target/conversation/generation/hash；facts.conversation.id/generation/scopeType=bounty与message一致，facts.task.id=message.taskId，snapshot target=profile.agentId=message.targetAgentId。不能因profile标签或任意用户同名JSON就启用。无该facts字段：原CHAT输出/黄金wire/行为保持不变；字段存在但无效：明确拒绝，不降级plain CHAT伪报已理解。

## 3. 原生结构化模型输出和严格union

仓内实际测量的CLI为0.153.4，TurnStartParams.json SHA `b36fb37326b1cf69f75c8b306f1f886d53a57c4b1b985e08e298e2407ea2ad02`，bundle SHA `b06f77062369d481a59cc70720c12b89cb9dd49c385863923262102d3ad6c978`；其中存在 `outputSchema`（约束本轮final assistant message的JSON Schema）。这是本地版本证据，不是“最新CLI/所有模型均支持”断言。adapter只在本包显式policy中传此schema，plain CHAT的turn/start参数不增字段；不通过prompt解析或命令工具代替机器结果通道。真实模型支持与双接应仍须实际验收。

root是object、additionalProperties=false、以下五字段全部required（避免root anyOf与不同引擎兼容猜测）：

```json
{
  "schemaVersion": 1,
  "kind": "EXECUTION_PROPOSAL",
  "text": "我可以基于上一稿把羽毛颜色调得更鲜艳，请确认这个修改。",
  "clarification": null,
  "proposal": {
    "operation": "EDIT_IMAGE",
    "instruction": "把羽毛颜色调得更鲜艳，保持原有鸟的姿态",
    "sourceRefIds": ["source_1"]
  }
}
```

严格语义（Client与未来API独立验证）：

- ANSWER：text为非空可读string，clarification=null、proposal=null。
- CLARIFY：text为非空string；proposal=null；clarification仅question（非空string）和requiredFacts（非空、去重数组），允许值SOURCE_SELECTION/REFERENCE_REQUIRED/REQUIREMENT_DETAILS/OPERATION_CHOICE。模型不能指定pending question ID、CAS/version、resume authority或任意对象路径。
- EXECUTION_PROPOSAL：text非空；clarification=null；proposal仅operation/instruction/sourceRefIds。operation必须属于本轮supportedOperations；instruction沿用冻结v3的4000Unicode codepoint、非blank、ISOControl拒绝且不trim/normalize；sourceRefIds唯一且逐项属于snapshot availableSources，GEN只可引用image，EDIT精确一个current-conversation image。API将sourceRefId映射成自己冻结的真正源版本和producer lineage，模型不提供parent/grant。

拒绝unknown key/kind、重复JSON属性、非object/null/array顶层、伪prototype、损坏Unicode/JSON、不符合互斥、非法operation/source。JSON Schema约束不能取代实际parser/语义验证。无Markdown fence剥离、无前后文提取、无“修复JSON”第二模型调用；不合规本轮失败，不能回退执行或把无效union包装成成功ANSWER。所有字段沿用实际existing CHAT/context/v3域，不新增SLO或任意响应总时限。

## 4. 流式文本与thread隔离

app-server delta为结构化JSON时，不把raw JSON、schema、sourceRefIds或proposal局部字段当聊天文本广播。专用incremental decoder只识别**顶层text string**，正常处理字段任意顺序、chunk split、escaped quote/backslash、新行escape、Unicode/surrogate split，输出新增已完整解码的Unicode scalar前缀。不把嵌套text冒充顶层；prefix不删除/重写用户已收到的delta。结构未完整时可保持处理中，不能因首帧慢取消。final通过严格union验证后，content精确等于text、与已广播前缀一致；无效JSON不产生成功sidecar。

原sendChatDelta的seq、cancel、turn绑定和持久outbox保留。完整typed union只在原子final发布，streaming prose不是执行建议已批准。typed静态指令/format/schema/本轮可信结果合同digest纳入现thread key的instruction/model/tool policy绑定，typed与普通CHAT不复用不兼容引擎thread；同用户会话仍一条。User files/logs/代码/AGENTS/资料名和模型历史正文仍是DATA，不升格工具/开发指令。

## 5. final wire：只在显式协商后添加两字段

保持既有chat.message callback Trace/正文/schemaVersion/finalSeq/status，完成typed本轮时追加：

```json
{
  "outcomeContractVersion": 1,
  "interactionOutcome": {
    "schemaVersion": 1, "kind": "ANSWER", "text": "这是一只鸟的创作需求。",
    "clarification": null, "proposal": null
  }
}
```

content===interactionOutcome.text。原finalSeq是实际已发text delta seq，不能为JSON raw delta编造seq；profile sender、Trace、conversation generation、context hash都从原消息与runtime绑定生成，不来自模型。失败/取消走现明确失败/取消路径，不补发成功union；同final outbox重发保持exact union/content，不能再运行模型。

**API后续必需原子持久化（本包尚未实现）**：只有snapshot明确请求且当前绑定target/dispatch/turn/hash完全一致，才接受sidecar；无请求的sidecar或请求但成功final无sidecar不得偷降级。finalDigest必须包含contractVersion+完整canonical union+正文+原final binding，重复文本但different proposal/clarification为冲突而非duplicate；同exactfinal返回原fact。以request/step/currentness CAS持久化typed outcome，CLARIFY生成server pending question和WAITING_USER，proposal生成server ID/源快照/parent但不发执行authority。plain text不经semantic parser。API与Web的pending CAS/回复/resume/typed展示必须后续完整施工，不能以Client切片替代。

## 6. 真实能力声明、默认关闭和接应模式

新的registration/presence sibling `typedDeliberation`（profile默认off时不输出该key，原默认声明保持）：schemaVersion=1，state=READY或UNAVAILABLE，carrier=CHAT_MESSAGE_FINAL_SIDECAR_V1，referenceModes=[NONE,AVAILABLE]，outcomeKinds=[ANSWER,CLARIFY,EXECUTION_PROPOSAL]，engine=CODEX_APP_SERVER_NATIVE_OUTPUT_SCHEMA，strictNoToolsVerified=false，toolPolicy=read-only-constrained。READY只能显式flag+现fastCHAT配置+实际初始化且matching measuredschema的live adapter；不可只按flag/山寨安顿/自家接应标签声明。adapter退出后立即不READY，未知model是否兼容不能等同实测成功。

既有RuntimeCapabilities v1 CHAT/INSPECT/EXECUTE 与controlled V2/V3声明不改语义：INSPECT仍supported=false；typed提议EDIT不意味着controlledImageV3Ready或已安装/生产调度。初始点将清晰需求仍可直接EXECUTE，不强制模型planner先跑；语义planner只在本轮确实需要时选择，且无生成permission消费。两个接应都通过同native contract，但必须分别真实验证，不因mock双标签断言通过。

## 7. Client自检与全产品边界

Owner实现原生outputSchema adapter传递、strict union/stream decoder、runFastChat选择/绑定/原子callback/defaultoff声明及actual mock-runtime测试（不是只造fixture/parser）。回归普通CHAT/PRIVATE/TASK/既有native/controlimage黄金wire、unknownturn不重跑、cancel/latecallback、schema/adapter不可信与无flag、prompt injection不改mode，输出所有源码/fixturehash、实际命令/stdout/测试计数。不得调用真实Provider/账户、安装、push或Gradle。

本切片只向完整自然多轮闭包推进：API typed persistence/pending question CAS/resume、Web输入proposal/澄清、真实INSPECT、全媒体生成/输入、双接应、34产品/29桥、浏览器与版本发布均仍需完成；不宣称产品已可验收。
