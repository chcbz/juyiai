# Typed INSPECT v1：受权资料查阅与同会话续办合同

状态：**领域合同 v1 已定；引擎隔离 profile、源码和真实运行尚未就绪**。这是新 sibling 合同，不修改既有 typed CHAT v1 的含义，也不是功能上线声明。

依据：API `a6e3e06cb4fa29ed6c01d80e8d8f0ae9372a1de9`、Client `607d25145efe3d13f996e5fbb5e33a01d7bf2195`、Web `ebb664fc8a443845577f356d0823bd6368634dfa`。API 相关220项源码回归已通过；本合同用例仍NOT_RUN。源码依据见既有[接线准备](integration-evidence-20260928/inspect-authority-prep-20261001/prepared.md)，该准备的历史API a213引用不冒充新基线。

设计样例与12项待执行用例：[typed-inspection-authority-v1.json](fixtures/typed-inspection-authority-v1.json)。fixture仅验证字段/摘要一致性，profile明确NOT_ENABLED/NOT_MEASURED，不是能力声明或测试通过记录。

## 1. 不可混淆的边界

- CHAT v1 `referenceMode=NONE|AVAILABLE`、route=CHAT、outcomeContractVersion=1保持原样。AVAILABLE只是目录，不能先下载再声称“没加载资料”。
- INSPECT是用户在同一议事中明确提供资料供本轮查阅；无生成、修改、付费工具、EXECUTE START、工作空间写入或正式交付权限。
- 已明确且已授权的“参考此图画鸟”仍可直接走EXECUTE，不强制先进行一次INSPECT或固定三次模型调用。
- 选入资料时界面说明“本轮将交给所选Agent查阅”；仅浏览目录不授予机器读取。实际发送使用专用inspection入口，不让模型正文签发读授权。
- 复用现有request、turn、snapshot、outbox、事件、typed admission/outcome/pending/proposal和Client inbox/binding。不增加第二套问题状态机或文件根。
- `TypedDeliberationFinalValidator`当前明确只接受CHAT。实现不得直接把它的route条件放宽为CHAT/INSPECT；新版本绑定与旧版本绑定分别校验，再复用纯内容校验原语。

## 2. HTTP边界

### 2.1 用户受理

`POST /chat/conversations/{conversationId}/interactions/inspection`

身份：现有human登录身份；服务端解析tenant/owner/client，禁止浏览器指定这些身份或target/profile。携带既有`Idempotency-Key`。

body沿用讨论命令的精确字段：`schemaVersion:1`、`intent:DISCUSSION|CLARIFICATION_REPLY`、`taskId`、`expectedAssignmentRevision`、`content`、`parentOutcomeId`、`expectedParentStateVersion`、`pendingQuestionId`、`expectedPendingQuestionStateVersion`、`sourceSelectors`。selector仍为既有六键的两种精确来源，不收URL、本机路径、裸hash、producer或grant。没有资料可查阅时返回422，不能假装inspection完成；普通无资料讨论走CHAT。

明确sourceSelectors优先；澄清回复的sourceSelectors为空数组时可继承父问题精确目录，但必须重新授权和签发本轮快照。至少一个来源是INSPECT语义要求，不是任意性能门槛；其余已有字段域、长度限制沿源合同，不新设count/byte/时间预算阈值。

受理事务与typed CHAT共用锁顺序：task root → bounty binding → conversation → scoped pending/admission。核对当前assignment、conversation generation、唯一目标及目标当前唯一就绪inspection声明。新入口bodyDigest加入contract=`juyiting-typed-inspection-v1`、purpose=INSPECT；同键跨CHAT/INSPECT或变更payload为409，不返回另一路由的成功回执。

返回仍为固定Admission回执ADMITTED/0与既有request/turn IDs、statusUrl、eventCursor；本回执不表示资料已经读取。恢复新增下面明确的原key只读入口，不把现有仅known-request GET误称为已有按key查询；不因404推导原POST未受理。新请求/快照/outbox/typed admission及pending CAS同事务提交；失败整体回滚。

### 2.2 用户只读恢复

`GET /chat/conversations/{conversationId}/interactions/inspection/request`，human身份＋原`Idempotency-Key`、无body/query。当前授权scope内只读查原typed admission；存在且inspection marker匹配时返回原固定Admission回执（replay=true），不存在404，属于同一身份的跨合同key冲突409。GET绝不创建request、outbox或Provider调用；404仍不证明在途POST未受理。自动恢复仅GET，只有用户显式重试才允许原key＋原body POST，不生成新key。

`GET /chat/conversations/{conversationId}/requests/{requestId}/inspection-outcome`返回`schemaVersion:2,contract,conversationId,conversationGeneration,requestId,requestRevision,turnId,state,outcome,inspection`。state沿PENDING/READY；outcome业务字段沿typed projection但由v2明确解析。inspection为`authorizationId,manifestDigest,sourceRefIds,inputSummary`；inputSummary未持久final前为null，之后仅为`inputDigest,sources`，不暴露engine线程ID或本机路径。receipt的typedOutcomeUrl指向此入口；旧typed-outcome入口不能把INSPECT当v1成功投影。

现有request状态/目录仍是办理进度事实源；新projection不新增第二状态机。未收到已绑定receipt时只显示“处理中（查阅）”，不谎报字节已读或模型已理解。

### 2.3 Agent读取

`GET /internal/agent/chat/requests/{requestId}/turns/{turnId}/inspection/inputs/{sourceRefId}/content`

- 仅现有runtime authentication。认证filter精确允许此路径和GET；浏览器JWT、匿名、错误Agent、跨tenant/owner/client均不能走此入口。
- 不接受query或任意远端URL；request/turn/manifest/snapshot均从持久记录解析。请求头`X-Inspection-Manifest-Digest`必须精确等于该snapshot中的manifestDigest。
- 每次GET重核：当前runtime身份及绑定、目标/profile、request/turn归属、INSPECT route、当前assignment/generation、仍可办理的request状态、精确sourceRef及来源版本、资料当前ACTIVE/REFERENCE链接或有效会话资产、撤权/删除。
- 按同一权威锁顺序线性化本次读取许可，再打开受信不可变版本。只读manifest不是授权票据；浏览器下载权限和EXECUTE grant不可代用。
- 返回实际内容，Content-Type/Length与快照一致，`Cache-Control: no-store`、`X-Content-Type-Options: nosniff`；不重定向、不返平台绝对路径、不走公开CDN。
- 初版仅完整GET，不承诺Range/HEAD；其他方法405。浏览器媒体的Range/HEAD继续由已有owner端点处理，不与此机器端点混同。
- 401：未认证；403：认证类型不是runtime或不具该端点调用权限；404：不属于当前身份的request/turn/source；409：已归属请求的manifest/assignment/generation或当前授权冲突；422：已归属来源格式不支持；503：当前目标或资料服务不可用。不得将慢请求作为这些错误原因。

撤权阻止后续新读取、重试和新轮次；已经合法传出的字节不能被追溯收回。源链接撤销或重新点将发生在读取之后时，终态提交还须重核本轮权威归属，旧目标不能污染新分配。不得声称仅靠删除客户端临时目录就能让Provider遗忘既传内容。

## 3. 快照、摘要与持久化

在既有不可变`ChatContextSnapshotEntity.factsManifestJson`新增独立顶层`typedInspection`，不改写旧`typedDeliberation`。同时使用既有`typedDeliberationAdmission`续办字段与typed admission/outcome存储；双方从contract marker判定各自版本，不能仅凭正文或route猜版本。

`typedInspection`精确键：

| 字段 | 约束 |
| --- | --- |
| schemaVersion / contract / purpose | 1 / `juyiting-typed-inspection-v1` / INSPECT |
| discussionFacts | 原目录事实schema1（NONE/AVAILABLE规则不改）；本入口来源非空，因而为AVAILABLE，不用它表示已读 |
| manifest | 下列不可变授权输入对象 |
| manifestDigest | `sha256:`＋canonical manifest的UTF-8 SHA-256 |
| authorizationId | 服务端stable(`inspection`,requestId,manifestDigest)，无独立可转移授权 |

manifest精确键：`schemaVersion:1`、`purpose:INSPECT`、`scope`、`profile`、`sources`。

- scope：`tenantId,ownerJiacn,clientId,conversationId,conversationGeneration,taskId,assignmentRevision,requestId,requestRevision,targetAgentId`；版本数使用与现wire一致的规范十进制字符串，不能有浮点、前导零或精度截断。
- profile：`profileId,engineContractId,enginePolicyDigest,toolPolicyDigest,inputPolicyDigest`，来自当前live session的服务端冻结声明，不接收用户覆盖。
- sources：按sourceRefId排序；每项精确为`sourceRefId,selector,mediaKind,mimeType,byteLength,sha256,carrier,carrierContractDigest`。selector是服务端已解析的精确原selector；hash/长度来自持久内容，byteLength为规范非负十进制字符串。carrier来自已协商profile，不由用户或模型任意选择。
- 不包含下载URL、host本机路径、token、运行临时路径、snapshotId或contextDigest。后二者由现有快照流程在manifest固定后计算，防止“快照摘要含自身”的循环绑定。
- 外层dispatch沿原链绑定turnId/dispatchId/snapshotId/contextDigest；sourceRef不能脱离其snapshot/manifest重用。sources.sha256是64位小写hex，manifestDigest及三个policyDigest/ carrierContractDigest为带`sha256:`前缀的64位小写hex；不混用两种域。

新内部受理必须接收服务器构造的可信inspection上下文，统一写入snapshot/requestDigest/outbox。不得为了通过legacy INSPECT守卫而伪造`materializedRefs`，也不得把新入口的授权检查变成允许任意HTTP inputRefs的通行证。原generic/legacy入口规则保持不变。

原则上不新增schema表：受权范围已能由immutable snapshot＋现有request/turn及当前业务权威恢复。源码Owner若发现无法保证幂等/撤权/事务闭合，先报告精确缺口再修订合同，不能默默加表或修改既有schema version。

## 4. Client物化与原生输入

- 使用当前本地profile私有目录下的inspection请求目录；与CHAT空工作目录和EXECUTE run分开，平台根不共享挂载。
- 仅由manifest派生请求路径，固定已信任平台origin和认证header。每个响应验证长度、SHA、MIME、常规文件/符号链接边界，原子发布只读输入；不跟随重定向、任意URL、设备或符号链接。
- 本地资料身份至少绑定authorizationId、manifestDigest、sourceRefId及精确bytes。文件名只是本地opaque命名，不能携带源平台绝对路径。
- 复用既有inbox认领、native turn acceptance unknown和thread/read恢复；将manifest/input receipt作为该inbox附属字段，不另建业务状态机。发turn/start前持久记录准备好的canonical输入摘要；未知结果不得再次start或降级到legacy/EXECUTE。
- thread key在现有身份、会话generation、mode、cwd、引擎/tool策略外，再绑定authorizationId/manifestDigest/inputPolicyDigest。不能沿用已包含被撤权资料的旧INSPECT线程作为新请求上下文；需要的历史从当前授权业务快照重建。
- 收到本机缓存不等于当前仍授权：新轮次必需重新受理，旧授权不能因缓存存在跨request重用。内容不能先进入模型再校验摘要。

carrier：

| carrier | 接入及证据 |
| --- | --- |
| DIRECT_TEXT | 明确支持的text MIME，严格解码；作为标记为不可信资料的text输入；记录原bytes与实际文本输入各自摘要 |
| LOCAL_IMAGE | 支持且实际可解码的image MIME → 原生localImage，路径必须是本轮已验证私有文件 |
| LOCAL_AUDIO | 支持的audio MIME → 实测可用原生localAudio，不把schema字段存在当模型已理解 |
| PARSED_TEXT | 对具体文件MIME绑定实测确定性parser binary/config摘要、原bytes摘要及提取文本摘要；未知/加密/解析失败不冒充文本 |

同一source只使用一个carrier，不在正文与另一隐式上下文重复注入。无generic local-file协议保证；未实测格式诚实不可用，不能默默转application/octet-stream。四类媒体仍为完整目标，不能以图片单项通过宣布全部完成。

## 5. 能力、隔离与真实就绪

新增独立`typedInspection`声明，精确键为`schemaVersion,contract,enabled,profileId,engineContractId,enginePolicyDigest,toolPolicyDigest,inputPolicyDigest,toolPolicy,recovery,supportedInputs`。schemaVersion=1、contract固定上述ID，recovery=`durable-inbox-turn-readback-v1`；supportedInputs每项为`mediaKind,mimeType,carrier,carrierContractDigest`。toolPolicy仅`STRICT_NO_TOOLS|MANIFEST_READ_ONLY`。不改旧声明中INSPECT不可用的事实，不因存在新字段自动启用旧profile。

就绪需要：实际binary/schema绑定、本地operator profile配置、真实原生启动与恢复、carrier正向理解、越界文件/工具/网络负向证据。仅read-only sandbox、空MCP、approval=never、localImage字段存在或Model名称均不足。

允许两种经实证策略：严格无工具且直接输入，或仅manifest范围内受控读取。不能把后一种声明为严格无工具。Client和API均默认不启用未验证profile；未就绪不偷用CHAT猜资料内容。

**尚需单独固定的引擎实施项**：实际可用profile的完整工具目录/OS隔离配置、文件parser与支持MIME清单、真实出站参数快照。此处不虚构这些证据；它们是Client source enable/广告的前提，而非延迟API接口设计的借口。

### 5.1 UI 意图与能力就绪不能混同

本合同中的 `typedInspection` 声明属于已认证目标runtime的服务端协商事实，不约定将它直接附加到全局 `/chat/capabilities`。后者未绑定task/assignment/target，不能用全局布尔值证明当前目标查阅就绪，也不能凭空解析未约定字段。

Web可让用户明确选择本轮“查阅所选资料”，这是用户意图而非能力广告。未取得目标就绪事实时说明“将所选资料交给当前Agent查阅，实际可用性在发送时校验”或“能力待确认”；提交由inspection admission实时校验唯一目标、profile、来源及当前授权。受理成功仍不等于已读。422/503等真实失败需展示，不可静默转换为CHAT猜资料、EXECUTE或另造新意图。

本轮不新增第二个Web能力事实源或凭build flag伪造ready。未来若需发送前目标就绪预览，必须单独约定task/assignment绑定的只读投影；该预览不能替代受理时重新校验。用户意图选择、服务端能力声明、授权受理和实际输入回执保持分离。

## 6. 结构化终态与用户交互

INSPECT final使用新的`outcomeContractVersion:2`，`interactionOutcome.schemaVersion:2`；其ANSWER/CLARIFY/EXECUTION_PROPOSAL联合的业务字段与限制沿原typed结构，但版本2只能与typedInspection marker和route=INSPECT匹配。旧CHAT v1拒绝v2，INSPECT拒绝v1；正文不解析为命令。

必需Client生成的`inspectionInputReceipt`：`schemaVersion:1,authorizationId,manifestDigest,inputDigest,engineThreadId,engineTurnId,sources`；sources记录每个sourceRef的`sha256,byteLength,carrier,contributionDigest`，不得多项/漏项/换序后改变canonical含义。路径和认证header不进入API或浏览器。receipt不是新增授权，仅为可信Client边界的输入记录；模型不能自己填receipt。

v2 outcome_json持久对象为`schemaVersion:2,interactionOutcome,inspectionInputReceipt`；kind/text等查询列仍从union取，既有pending/proposal继续复用。v1 outcome_json布局不变，按可信snapshot marker分派解析；不得对两个marker同时存在的snapshot猜版本。

finalDigest同时覆盖contract版本、完整binding、原始规范化union和receipt；body、outcome、pending/proposal、request/turn及事件仍一个事务。重放同digest返回原结果；变更receipt/union冲突。当前身份/assignment/generation及授权变化按2.3处理，不让旧Agent迟到结果推进新分配。

继续使用同一个typed pending问题记录与CAS，不添加inspection_pending；资料澄清可继承父目录但重新授权。用户只是补充文本时可继续CHAT，不能因此声称本轮重新看过资料；用户继续查阅则新INSPECT请求。旧成果、图片/音频/文件展示、保存、正式提交和验收不因本合同改为强制先保存。

Web显示阶段区分：资料目录AVAILABLE → 查阅受理 → 正在查阅 → Agent答复/澄清/提议。前端不凭选中资料宣称已读；byte receipt只证明输入边界，不替代“理解正确”的真实模型验收。新版结果需显式支持版本2，不把未知版本按v1降级展示为已完成。

### 6.1 输入摘要算法（v1 精确补充，2026-10-02）

本节为 IA/IC 共享算法；fixture见 `fixtures/typed-inspection-input-digests-v1.json`。沿既有canonical JSON：对象键按字典序，UTF-8，无额外空白；数组顺序不重排。来源必须已经按 `sourceRefId` 严格升序，重复/乱序拒绝，不默默改变manifest或native输入顺序。字段名统一 `sourceRefId`，不得使用 `sourceRef` 别名。

所有contribution preimage精确公共键：`schemaVersion:1,sourceRefId,sha256,byteLength,mimeType,carrier,carrierContractDigest`；各carrier只追加以下字段：

- DIRECT_TEXT：`sourceByteDigest,textDigest`。sourceByteDigest为`sha256:`加原bytes的hex摘要。严格UTF-8解码，保留BOM、Unicode和换行，不做归一化；非法序列拒绝。实际native text精确为 `UNTRUSTED INSPECTION MATERIAL (` + sourceRefId + `):\n` + 解码文本。textDigest为该完整native text的UTF-8摘要。
- PARSED_TEXT：`sourceByteDigest,parserConfigDigest,extractedTextDigest,textDigest`。parserConfigDigest绑定已登记的parser binary/config合同；提取文本须为合法Unicode scalar序列，拒绝孤立surrogate，不在编码时替换。extractedTextDigest为原提取文本UTF-8摘要；实际native text使用与DIRECT_TEXT完全相同的包装，textDigest覆盖包装后文本。不得将文件正文当系统指令。
- LOCAL_IMAGE/LOCAL_AUDIO：不追加字段。路径、adapter函数、engine IDs均不进入preimage；实际bytes/载体及carrier合同已由公共字段和manifest绑定。仅允许对应native类型及经验证的当前私有path，拒绝adapter替换为text、URL或其他来源。此检查不替代上游decode/profile验证。

`contributionDigest = sha256: + SHA256(canonical(preimage))`。

receipt的每项精确键为`sourceRefId,sha256,byteLength,carrier,contributionDigest`。`inputDigest = sha256: + SHA256(canonical({schemaVersion:1,authorizationId,manifestDigest,sources:receiptSources}))`；API重算该摘要并对照manifest验证来源顺序/字段。contributionDigest记录可信Client的实际转换，不能伪称API仅凭摘要已独立理解内容。

准备输入函数必须在原生turn/start前可运行，不要求engineThreadId/engineTurnId。它返回nativeInputs、inputDigest及不含engine IDs的receipt草稿；原生受理后独立finalizer附加真实engineThreadId/engineTurnId，形成第6节完整receipt。禁止用占位IDs提前制作final receipt，禁止为计算摘要触发第二次turn/start。输入数组中每个source恰有一项；关联说明包含在文本项内，不重复注入文件正文。

## 7. 最小施工包与验证

| 包 | 责任与范围 | 验证 |
| --- | --- | --- |
| IA | 高风险API Owner：sibling admission、可信snapshot、machine GET/authfilter、current authority、typed v2原子终态与既有pending复用；不做生产迁移 | 实际Spring事务/隔离MySQL、MVC＋runtime过滤器、所有下列负向 |
| IC | Client Owner：profile与安全物化、载体、inbox receipt、独立thread binding、未知恢复；无EXECUTE START | 实际模块Node测试、四类实物、真native输入/工具/文件隔离；未实证profile不enable |
| IW | Web Owner：同输入框选择资料/查阅意图、v2回执和恢复、真实阶段展示 | 实际composable→API wire、跨身份/断线/多请求恢复，之后真浏览器 |

IA/IC必须有明确身份/ACL/快照责任Owner与冻结owned paths；不创建Reviewer。仅完成文档不算已分配或开工。主执行台账唯一记录Owner/进度。

最低合同用例（本合同全部NOT_RUN）：
1. 同key同body返回同request；跨路由同key或不同manifest冲突；中断后只读恢复不重复模型。
2. 人类JWT不能机器GET；跨owner/client/tenant/agent/profile、猜ID均拒绝；filter不开放泛化internal路径。
3. workspace固定版本、conversation asset固定revision；后续新版本不替换输入。
4. 撤销资料链接、重新点将、会话generation变化、取消分别使新读取失效；已合法传出的字节不谎称可撤回。
5. digest/MIME/长度不符、redirect/symlink/traversal/设备、未知parser均不得调用模型。
6. manifest/context摘要无自引用；request/turn/snapshot/outbox/pending CAS原子回滚；不新增第二state machine。
7. CHAT v1/INSPECT v2版本交叉、缺receipt、伪造额外source、改digest/final重放冲突都拒绝。
8. 同一pending并发回复只有一个成功；新一轮重新授权，不拿旧cache或old thread偷读。
9. 每种carrier的真实已知内容理解；不只验证wire或mock传参；未知接受状态不再次start。
10. 恶意素材要求shell/网络/其他目录/执行授权时，真实引擎隔离与服务端边界均有效。
11. server/local双接应各自通过；纯文本讨论和既有EXECUTE v3不退化。
12. 真浏览器完成参考图→询问→自然补充→生成/修改→预览下载→可选保存→精确提交→验收完成。此项仍与原34项产品用例合并验收，不缩成接口测试。

## 2026-11-04 CHAT本地文件交付扩展（候选，未上线）

范围为现行CHAT材料入口，不恢复旧独立INSPECT执行。遵守RB-03/05、API接口规范v1.4及根AGENTS分层职责。本节是本次候选合同；只读议事工具环境与正式回归未完成前不注册/启用该能力。

- 新增载体`LOCAL_FILE`：原始授权文件在本轮只读输入目录中可见，模型通过已有工具按需读取。不是`localFile` App Server原生输入（安装版0.166.0没有此输入），也不是已解析正文、阅读成功或理解证明。
- 能力声明复用`materialsInput.supportedInputs`，`mediaKind=file, mimeType=*/*, carrier=LOCAL_FILE`表示通用文件交付。只有LOCAL_FILE允许此通配MIME；它不宣称任意格式可解析。精确声明（例如image/png→LOCAL_IMAGE）优先，其余使用通用文件交付；避免按扩展名维护第二份白名单。
- 请求manifest保留文件真实mimeType、sourceRefId、原字节SHA-256/byteLength、固定下载URL和当前请求绑定，不以`*/*`替换真实类型。沿用原下载授权及隔离，API不解析Office/PDF，bridge不预解析全文。
- bridge生成一条明确标识为本地文件描述的文本输入，内容为sourceRefId、沙箱内path、真实mimeType、sha256、byteLength；正文不嵌入、不解码、不假造App Server文件类型。材料内容不成为可信指令。路径由现有材料根映射产生，不接受用户指定宿主路径。
- contributionDigest沿用规范canonical digest：`{...contributionBase, textDigest: SHA256(实际描述文本UTF8)}`；既有inputDigest及最终engineThreadId/engineTurnId关联保持。LOCAL_FILE回执只证明交付，不能当阅读成果。旧4种载体既有向量及hash不改变。
- 只读工具环境不借用正式nativeExecution的业务执行/提交权限，不挂技能凭据，不创建成果任务或outputs提交。图像直传保持；格式不支持/加密/内容不可读由实际工具结果说明，不将不存在的正文交给模型后要求用户重复上传。
- 必要回归：通配与精确优先级、原哈希/MIME保持、描述及回执绑定、未嵌入二进制、原4载体向量不变、同thread普通/文件/普通，以及真实沙箱读取和未授权目录不可见。文件已交付不等于模型调用了工具；不新增按文件强制调用步骤。

#### 2026-11-04 议事工具提示与启动依赖补充（LOCAL_FILE候选，未上线）

- 议事禁止执行业务动作，不再把已授权LOCAL_FILE的只读输入准备一并写成“禁止调用所有工具”。只有实际启用文件读取工具的adapter才向普通/材料消息提供同一份工具说明；无工具的旧profile不虚报能力。说明指出既有Python/docx/openpyxl/pypdf位置与只读边界，由模型选择读取方式，可合并读取，不新增按格式分派的bridge解析器。
- 启动测量必须先取得既有进程级single-flight工具链，再验证CHAT文件工具环境；不能依赖稍后的正式native execution阶段才初始化工具链。复用既有结果，不新增每Agent缓存或每消息探针。
- 普通文件写入仅限工具专用TMPDIR `/tmp/chat-files`，不是整个/tmp；会话Home即使位于/tmp下仍不得被模型命令写入。保留底层procfs兼容项，不放开业务目录。
- 真实候选测得四文件读取与前后普通消息同thread/Home；这只证明指定样本和候选adapter/provider，不等于Web/API上线验收，不宣称任意文件、扫描PDF或OCR均支持。交付回执仍不等于模型已读/已理解。
