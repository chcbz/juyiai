# 技能管理多端合同 SM-C1

## 2026-10-28 职责边界补充（目标约束，不改变已发布wire）

本管理体系接入原生执行遵循[RB-1](responsibility-boundaries.md)和[核心详设v3.1](native-execution-technical-design-20261027.md)：API保留来源/版本/权益/安装管理权，Runtime负责包实体与真实能力，Web只呈现权威状态，技能包不授予任务执行权限。普通说明/脚本包不因原生使用而强制新增runner；私有来源及真实所需包元信息在既有管理合同中做最小扩展，不造商品/订单绕过权限，不新建第二套市场。

本节不改写已发布DTO/schema或固定摘要，安装即授权/费用规则不变；历史执行恢复按本文末节2026-10-28单轨决定退役，不沿用此前兼容续跑要求。新合同必须同步实际生产者消费者与回归；未实现不能凭文档宣称可安装或READY。

2026-10-23 · Owner：本聊天 · **状态：目标合同已确定，应用尚未实现/验收。**

范围以[现有原型落地方案](management-mvp.md)为准：同列表查看、安装、升级、启停、离线安装等待、重试/核对和折叠记录。不增加页面或通用操作平台。本文件是三端的唯一业务约定，取代旧SM-1接口草案；公共规则仍是[统一接口规范v1.2](../../api/docs/interface-standard.md)，不另造公共协议。

给各端的共同决定：**Web不猜状态，API决定权限/资金/新任务准入，Runtime报告精确安装事实；一个操作始终能查回，重试不变成第二笔购买。**

## 1. 合同包与分工

| 文件 | 用途 |
| --- | --- |
| 本文 | 路由、身份、状态、副作用、费用、互斥、恢复、切换规则 |
| [Schema](fixtures/management-contract-v1.schema.json) | `definitions`中的封闭DTO；必填/可空、字段类型与枚举以此为唯一字典 |
| [报文与摘要样例](fixtures/management-contract-v1.examples.json) | 完整HTTP/命令/回执正反例、原始非法JSON、固定摘要向量；全为合成值，不是真实商品 |
| [业务用例](fixtures/management-contract-v1.behavior.json) | 三端共同消费的跨请求/状态/权限/恢复验收场景，不冒充已执行测试 |
| [来源基线](evidence/management-contract-20261023/source-baseline.json) | 本地HEAD/tree、远端查询时刻、公共规范及相关文件摘要 |

Web实现请求和状态展示；API实现HTTP、事务、命令生产/回执消费、任务准入；Runtime实现命令消费、安装/恢复/目录生产。现有接线落点为Web的useSkillMarket/useHttp与AgentPanel，API的SkillMarketplaceController/Http/Service、SkillInstallCommandWriter/Dispatch/Ack/Result/Recovery、InstalledSkillDescriptorService及任务准入，Runtime的skill-install-manager/skill-registry/skill-executor和agent-client能力刷新。新增管理路由仍进入这些既有领域服务，不新建独立购买系统。三端引用同一份合同与文件SHA，不复制样例后各自修改。开工时绑定本合同及根AGENTS；外部Runtime仓库必须显式收到这些路径。

字段/语义变更先更新这份合同和同源fixture，并同步全部受影响端；不得临时加别名或猜测解析。本文决定的是接口行为，不强制新增某张表或某个框架。需要持久化的操作标识/状态可在现有安装、策略和记录存储中实现，但不能只放内存。

## 2. 公共约束与标识

- HTTP请求/响应、WS事件/回复分别引用Schema内唯一的`HttpRequest/HttpSuccess/AsyncEvent/AsyncReply`信封定义，业务只在`data`内；公共`protocolVersion=1`。技能管理命令/结果及能力子对象的业务`schemaVersion=2`，与文档SM-C1、技能包manifest版本、应用版本不同。
- 请求/响应`X-Request-Id`与body一致；写接口必须有`Idempotency-Key`，两者语法使用`Id`定义。同一逻辑请求重传保留原requestId/key/body，不因查询超时换键。HTTP响应`Cache-Control: private, no-store`。
- `skillChangeId`是**一次技能动作**的稳定标识，动作仅INSTALL/UPGRADE/ENABLE/DISABLE；不是商城orderId、commandId或任务ID。`skillInstallationId`是技能安装；`runtimeInstallationId`是Runtime安装身份，绝不互换。`orderId`只用于真实购买，权益覆盖升级/启停为null。
- `skillRevision`是scope+Agent+skill的单调变更代际，无记录为`"0"`；创建写动作时CAS并加一，状态进度不改它。`changeRevision`是操作记录版本，状态/回执变化时增加。重试取得新的skillRevision以拒绝旧消息，但保留skillChangeId、原/目标版本及购买关系。
- Long/金额/代际用规范十进制字符串，最大值来自Java Long；attempt是1～2147483647的JSON整数（存储类型范围，不是业务重试次数门槛）。时间是非负安全整数毫秒，摘要是64位小写hex，不带`sha256:`。
- 所有声明字段必填；可空字段必须显式null。拒绝未知/重复key、错误类型、数字字符串冒充attempt、浮点/指数表示小整数、未配对Unicode surrogate。Schema验证不能代替原始JSON重复key/数字token检查。
- API身份来自当前认证，path中的Agent须属当前Owner；tenant/client必须一致。外单任务使用权限不授予Agent管理权限。管理body禁止自报owner/tenant；Runtime命令中的这些字段只是待核对声明，与受信通道绑定逐项匹配。路径参数解码一次后必须是单一资源段，拒绝`/`、反斜杠、`?`、`#`及控制字符；不大小写折叠或再次URL解码。

## 3. Web ↔ API：七类业务接口

以下是**目标路由与DTO**，不声称现存全部可调用。`{agentId}`均核对当前归属；查询无副作用。

| 方法/路径 | 请求definition | 成功definition / HTTP | 职责 |
| --- | --- | --- | --- |
| GET `/agent/{agentId}/skills` | 无body/query | SkillListResponse / 200 | 同一列表，含详情、当前安装、批准候选、权限/依赖、真实运行状态、允许动作和最近操作 |
| POST `/agent/skill-orders/quotes` | QuoteRequest | QuoteResponse / 200 | 复用现有报价路径；支持INSTALL/UPGRADE，仅准备报价，不扣费/安装 |
| POST `/agent/{agentId}/skill-changes` | CreateChangeRequest | ChangeResponse / 202 | 接纳四种动作，返回可查询的skillChangeId；202不是安装成功 |
| GET `/agent/{agentId}/skill-changes` | 无body/query | ChangeListResponse / 200 | 当前Agent可见记录，按createdAt降序、同时间skillChangeId降序；首期完整数组，不隐藏分页/擅截历史 |
| GET `/agent/{agentId}/skill-changes/{skillChangeId}` | 无body/query | ChangeResponse / 200 | 查询原操作，关闭/刷新后恢复使用 |
| POST `/agent/{agentId}/skill-changes/{skillChangeId}/retry` | RetryRequest | ChangeResponse / 202 | 已确定可恢复失败的新尝试，保留原操作/原支付关系 |
| POST `/agent/{agentId}/skill-changes/{skillChangeId}/reconcile` | ReconcileRequest | ChangeResponse / 202 | 安排核对原记录/回执，不重新安装、切换或执行Provider |

下载仍用GET `/internal/agent/skill-installations/{skillInstallationId}/package`，响应200、Content-Type为application/octet-stream、Cache-Control为private, no-store，原始包字节，不包JSON；必须认证当前Runtime并核对原操作/包/绑定，不接受客户端任意URL。已有包下载的媒体/权限保护保留。权益覆盖升级下载按原权益+当前skillChange+精确安装授权，不要求伪造orderId来通过旧下载检查。

### 3.1 请求决定

- QuoteRequest明确`action,agentId,skillKey,sourceSkillInstallationId,targetProductVersionId,expectedAgentVersion,expectedSkillRevision,approvedPermissions`。首次安装source=null；升级必须指定当前精确source。权限为目标版本完整授权集合，按UTF-8字节序排序且去重；修改Agent/目标/权限/原安装立即使未提交报价失效。
- CreateChangeRequest的四分支已在Schema封闭：INSTALL/UPGRADE带quoteId、固定目标、完整批准权限、expectedPrice；ENABLE/DISABLE只带当前source安装、Agent版本和skillRevision，不带报价或目标包。path Agent必须等于quote Agent。
- INSTALL默认启用；UPGRADE保留原启用期望，不把已停用技能偷偷启用。ENABLE/DISABLE的期望由动作确定，客户端不另传开关值。
- 已覆盖的旧权限可复用已有明确授权；新增权限必须由用户批准。Quote与提交都核对目标包所需权限，不信任“无新增”的原型示例，不允许权限集合混入未授权扩张。
- Retry/Reconcile只接受expectedChangeRevision；用户不能改attempt、原/目标、订单、金额或Runtime身份。API分配attempt：网络重放不加，已确认未生效且可恢复的重试加一并分配新commandId；INSTALL/UPGRADE准备失败重试另分配新候选skillInstallationId，ENABLE策略重试仍绑定原精确安装，不生成新安装或重新下载。DISABLE已在API关闭准入即成功，Runtime同步沿原命令恢复，不把它重新标为失败。旧尝试记录不覆盖。target中的productVersionId/版本/包/manifest/权限固定；只有INSTALL/UPGRADE的target.skillInstallationId可随已授权新attempt分配，不能把新尝试冒充原安装ID的网络重放。

### 3.2 查询与界面决定

`SkillRow`包含installed与candidate两种事实；安装证据存在但商品下架仍返回该行。candidate只来自平台批准版本，不按版本字符串/本地源码猜测“最新”。详情直接使用行内VersionDetails，无第二详情状态源。

`allowedActions`决定按钮，`deniedActions`给可解释原因；后端执行仍重新检查。VIEW不代替管理ACL。`runtime.state=READY`不等于任务准入：还需admissionEnabled、合法权益/权限及具体任务授权。说明型包使用NOT_EXECUTABLE，不伪造任务动作；其启用仅影响受管说明发现。

Web按schema解析，不按msg中文分支。关闭不取消操作；同窗口草稿与展开态分离，身份切换清理敏感草稿/迟到响应。仅保存原请求指纹、key和操作标识用于恢复，不保存“自动批准”。刷新先查原操作；尚未收到ID时只能显式重放原键原请求，不猜404意味着可以新买。

待核对是客户端观察：HTTP超时不把服务器状态改成FAILED。列表、详情、折叠记录都从同一服务事实投影；原型的计时动画、模拟连接、固定0积分不移植到产品。

### 3.3 既有接口的处置

复用`SkillMarketplaceService`、订单/权益、安装器与outbox，不新建交易系统。原`POST /agent/skill-orders`写入口在该链路切换时返回410 `ENDPOINT_RETIRED`，原市场调用方一并改用唯一的skill-changes入口；不保留两个购买状态机。商品、订单、权益历史GET仍按ACL保留，不用于推断新管理终态。quote路径保留但DTO按本合同同步变更，不做双解析。

这不是现在退役接口的操作授权。未完成三端及已有调用方改造前不切换；历史原订单/安装结果不改写。

## 4. 费用、幂等和事务

### 4.1 收费规则（API决定，Web/Runtime不猜）

2026-11-09准入补漏：新的INSTALL/UPGRADE报价及确认在同库业务事务中锁租约并检查有效租期；LOCKED拒绝，FINISHING拒绝所有新技能变更（包括ENABLE/DISABLE/UNINSTALL）。已接受的相同请求先幂等重放，旧操作结果、重试/恢复不重验租期，继续原预占/扣款/释放事实。集中由HostingRentWorkAdmission负责，不加到Runtime派发或通用所有权查询中。无租期schema时不查询租约；正式切换/存量过渡另依费用合同，不以此候选宣称已覆盖生产。测试入口为HostingRentWorkAdmissionTest和SkillManagementTransactionTest，实际通过状态见统一调度handoff。


- 现行费用合同以[内测文钱包](../agent-economy-marketplace/beta-wen-billing.md)为准（2026-11-09）：Money.currency=WEN，amountMinor为整数文，1元=100文；不使用银两／微银两，不浮点计算。
- 新INSTALL固定50文，包括卸载后重装；UPGRADE固定20文。均coverage=PURCHASE，entitlementId=null，确认创建真实订单并预占，成功按原订单结算；商品包登记价或历史已有权益不豁免本次操作费。零价历史订单与已接纳操作仍保留原事实，不补收费。
- 升级仍要求来源安装、目标包及平台政策有效；COVERED/PAID表示允许对应升级，均收20文操作费，NOT_ALLOWED拒绝，缺政策报SKILL_UPGRADE_POLICY_UNSET。不额外抵扣旧购买款、不计算差价、不新增发布维护界面。
- 尚未接纳的旧免费报价不能创建新操作，需重新报价；已经接纳的重复请求先按原事实幂等返回，不因当前价格改变重新扣费。首次请回的保留技能费用另由租约报价固定，不伪造成技能重装操作。
- quote固化原安装、目标摘要、权限、归属版本、skillRevision与金额，expiresAt由服务器给出。到期仅阻止新提交，不取消已接纳操作。已接纳后普通下架不改目标；安全撤销仍拒绝危险操作，不能按“已报价”越权。
- 可恢复准备失败保留原订单资金关系供用户重试；明确终结且证明未切换才释放/退款一次。已退款历史单不能重开重试。切换/回执未知绝不自动退款。
- 收到可信APPLIED并提交精确安装事实时，按原交易合同结算一次；当前目录未确认仍VERIFYING，不因已结算就宣称可运行。后续离线不自动撤销安装/退款。

### 4.2 原子边界

创建时在同一事务内完成：归属/版本、当前skill状态与quote校验 → 合法权益或真实订单/资金关系 → 持久skillChange及候选安装 → outbox。网络下载/Runtime执行不在DB事务内。同scope/Agent/skill只有一个活动写动作；防重与资金锁复用现有服务，GET无派单副作用。

所有写/回执/恢复入口采用一致锁序：已有actor经济锁 → Agent归属/skill互斥 → 商品/quote/订单/权益 → 账户/账本 → 安装/命令记录。实施时消除既有路径反序，不能只保护新Controller而旧写入口绕过。

2026-10-29 锁序补充（API `ab7b8b647e8b2a8980308b27c187bcc13cb3d269`，Flow5260799/365回归通过、主机1.17.13安装完成；通道稳定性验收仍未通过）：Agent归属锁内部必须遵循 **binding → identity → runtime**。Runtime会话围栏与技能管理外层事务在取得runtime行锁之前获取binding/identity锁；不得等到回调的归属校验才反向获取。已有installation会话锁、actor锁、代际/摘要校验及事务范围保持；PROVISIONED身份可校验但非注册请求不得激活。依据为2026-10-29生产状态扫描与请求事务反序死锁，风险是状态刷新失败与请求事务回滚。回归入口：`AgentRuntimePersistentSessionFenceTest`、`AgentIdentityServiceImplTest`、`AgentStatusMonitorTest`及隔离MySQL的`SkillManagementRuntimeMonitorLockOrderTest`。不以捕获异常后自动重放代替修复；不据此宣称所有重连均由该死锁造成。


skillRevision负责防旧意图，changeRevision负责进度CAS。原任务准入与安装切换/停用共享该skill的锁；准入事务同时保存精确安装引用和任务授权，不能先检查旧版、锁外才登记。

FAILED_RETRYABLE的已证实未切换尝试允许旧版继续使用并释放活动执行锁。重试须确认当前skillRevision及source仍对应原意图；如果期间发生新的同技能操作，旧重试返回409、不再覆盖新策略。新的写动作在确认旧尝试未切换后按同事务终结其资金/重试资格；不能留下仍可再次扣款的旧授权。RECOVERY_REQUIRED则不开放冲突写。

### 4.3 幂等与摘要

每个HTTP写按`可信actor+tenant/client+method+规范path+Idempotency-Key`唯一；输入摘要见§8。同key异参409，同key同参返回同一资源（当前权威状态可已前进，身份/版本/支付关系不变）。先查已受理幂等记录，再对新意图检查quote到期/CAS；不能让成功重放因过期quote失去恢复能力。重放仍校验当前ACL。

retry是一个新的显式尝试动作，有自己的key，但仍属原skillChange；重复retry请求只增加一次attempt。reconcile多次/并发合并对同一未决命令的查询，不增加安装或Provider副作用。同根因/同输入失败不自动盲重试，保留真实失败记录。

## 5. API ↔ Runtime：命令、回执及就绪

沿现有已认证通道、command/outbox/ACK/result恢复，不建新通道。完整信封和字段见Schema的Command、CommandAck、Result、ResultReceipt，完整正反例在共享examples。

| commandType / phase | Runtime行为 | 结果证据 |
| --- | --- | --- |
| SKILL_INSTALL / PREPARE | 核对持久Runtime绑定、原安装与授权；下载精确目标，验证包/manifest/依赖，独立暂存，不换active | PREPARED及preparedSha256；确定失败FAILED；无法证明UNKNOWN |
| SKILL_INSTALL / ACTIVATE | 只接受对应PREPARED证据与API授权意图；受控切换当前发现视图，持久结果 | APPLIED，actual精确目标；结果不明UNKNOWN，不能假装已回退 |
| SKILL_SET_ENABLED / POLICY | 不安装包；对精确active应用ENABLE/DISABLE策略，按新代际忽略迟到旧策略 | APPLIED及当前actual/appliedRevision |
| SKILL_RECONCILE / READ | 查observedCommandId的原journal/marker/结果；不下载、切换、重跑任务 | 原阶段的PREPARED/APPLIED/FAILED等事实；不能证实则UNKNOWN |

- `commandId`由API分配，每个阶段/尝试独立；`fencingToken=skillRevision`在本链中作为单调策略栅栏。首次deliveryEpoch为1；普通网络重投保持messageId/body。合法重连需要新投递代际时API增加deliveryEpoch并分配新messageId，commandId和业务摘要不变，记录每次授权投递。
- Runtime收到后验证命令/身份再持久收件，才发`command.ack` RECEIVED；收到不等于安装。当前通道实例证明与不可变执行实例分开；结果里的executionRuntimeInstanceId保留实际执行启动实例，不能在重连时改成新boot。
- work.result是事实事件；外层无code，业务evidence.outcome表示阶段结果。API验证并提交后发work.result.receipt E0/ACCEPTED；旧尝试/旧策略的合法迟到结果可回IGNORED_STALE并留审计，不倒退新状态。相同messageId不同摘要拒绝SKILL_RESULT_CONFLICT。
- 回执匹配skillChangeId、commandId、attempt、fence、已授权deliveryEpoch、原/目标包和Runtime持久身份。重连后的旧deliveryEpoch证据可在其确实被授权且仍对应当前未决命令时接受，不能仅因网络重连丢掉已发生安装的事实；绝不接受另一尝试/身份的成功覆盖当前状态。
- READ回执里的evidence.observedCommandId必须等于请求指定的原命令。NOT_STARTED仅在持久收件/intent/marker检查足以证明未开始时返回；缺文件或等得久不能单独证明未执行。
- 下载路径必须等于目标skillInstallationId对应的受控路径。包长度、SHA、来源、解压/路径保护、manifest与平台批准内容必须一致。EXECUTABLE包必须有manifest摘要；INSTRUCTION明确null，不生成虚假可执行动作。
- 没有任务taskId/workItemId，不把orderId塞进任务字段；命令中批准权限摘要用于绑定原授权记录，不单凭一个hash自行授予执行权限；管理fence只控制管理命令先后，不能拿新管理代际拒绝原本合法的已准入旧任务；安装命令无任务邀请expiresAt。真实认证有效期仍校验，重连重新取得合法投递资格，不改历史消息的TTL来“恢复”。

### 5.1 安装与升级顺序

接纳 → 离线等待或PREPARE → PREPARED → API锁内复验原状态/授权，关闭该技能不确定的新准入并持久ACTIVATE意图/outbox → Runtime切换并回执 → API提交active/资金 → 当前会话能力核验 → SUCCEEDED。

准备期间旧版正常服务。升级成功后新任务使用新版；在途/已准入未送达/结果未明的旧任务继续绑定原安装、包与权限，不自动换包或重放外部效果。API发激活后若结果不明，该技能新准入保持关闭，其他技能不受影响。

### 5.2 能力目录与任务版本（不能只定安装接口）

`SkillExecutionDeclaration`冻结注册/能力刷新中的`skillExecution`子对象：schemaVersion2、catalogRevision，以及每项精确skillInstallationId/productVersionId/版本/包/manifest、policyRevision、enabled、runner、readiness、依赖摘要、bindingRevision、observedAt。它复用现有能力生产与接受链，不新建消息类型或第二份目录。其余注册字段仍按现有统一注册合同，本功能不重定义整个注册接口。

`CapabilityAdapterInput`是**已通过注册认证后**的边界测试输入，不是新HTTP接口或可以直接信任的网络报文。包含当前runtimeInstallationId、runtimeInstanceId、sessionGeneration和上述子对象；Schema例子只覆盖受影响边界，实际注册完整wire→consumer测试仍须实现阶段运行。状态广播不能代替注册接受；连接变化/安装变化/策略变化触发既有refreshCapabilities。

API只接受当前认证会话的目录，核对安装、摘要、policyRevision、enabled及可信绑定；catalogRevision只在同一会话比较。API持久APPLIED与目录先后到达均可暂存核对，不因早到目录或旧session缓存直接开准入。真正READY的可执行技能才允许新任务授权；说明包可在精确发现视图核验后启用，但不成为EXECUTE_SKILL能力。

`TaskSkillBinding`是已有任务授权/执行快照在安装边界上的类型化投影，不新增Web请求或第二授权。准入原子固定executionId、taskGrant及其版本、Agent、技能安装与包/manifest/权限摘要；Runtime执行与恢复按它找包，不再只查当前active。既有内部快照的字段/摘要按原合同保留，适配只做明确字段映射，不能改写已准入快照：snapshot.skill.key/version/installationId分别映射skillKey/skillVersion/skillInstallationId，taskGrant.id/version映射taskGrantId/taskGrantVersion；productVersionId及批准权限摘要来自该精确安装的不可变授权记录，而不是当前active/当前商品。executionId取原执行记录，包/manifest取原快照。这个类型化投影不替代或另签任务授权；若所需旧记录无法证明，则恢复待核对，不借新版重跑。

程序目录仍为固定`app/`。技能包在受管stateRoot中按摘要保留，current发现视图复用受管CODEX_HOME/skills；升级不能覆盖旧任务引用的内容。本期不自动清理旧技能包，不新增GC协议；回收必须另核对API持久准入、Runtime在途及未知结果引用，不能仅看Runtime进程数为零。

### 5.3 启停与离线

- DISABLE：API事务关闭新准入并持久策略/投递后，此动作即可SUCCEEDED；runtimeSynced=false时说明Runtime尚待同步。这是“停止新调用”，不是取消在途。后续ENABLE使用更高skillRevision，迟到DISABLE不得覆盖它。
- ENABLE：记录期望true，但admissionEnabled保持false；精确安装、权益、当前Runtime策略和目录核验后才SUCCEEDED并开放。普通启停不删除包/权益/成果；安全撤销仍按现有专门权限合同执行。
- 当前原型明示离线提交的是INSTALL：合法Owner、持久Runtime安装映射仍可信才能接纳WAITING_AGENT；无映射或归属变更拒绝。重连复验映射、Owner与当前会话后续同一操作，不新建订单。
- 为不自行扩大原型，UPGRADE/ENABLE在新提交时要求当前连接，离线返回SKILL_AGENT_OFFLINE；DISABLE是API新准入控制，离线仍可立即生效。已受理的任一操作断线后都保留并恢复原操作，不因此退款或失败。

## 6. 状态、失败和展示

| 服务端状态 | 条件/下一步 | 原型显示 |
| --- | --- | --- |
| ACCEPTED | 操作及必要outbox已提交 | 已接纳 |
| WAITING_AGENT | 持久绑定合法，无当前连接；重连后续原阶段 | 等待连接 |
| PREPARING | 处理候选准备 | 下载与校验 |
| PREPARED | 精确准备证据已接受；复验后发送ACTIVATE | 准备完成 |
| ACTIVATING | API已持久切换意图，禁止不确定新准入 | 安全切换 |
| VERIFYING | 已确认安装/启用应用，等待当前目录匹配 | 已安装/已应用，待运行核验 |
| SUCCEEDED | 动作条件满足；DISABLE例外见§5.3 | 完成（运行状态另显示） |
| FAILED_RETRYABLE | 证实尝试未切换/未生效，且原授权/资金允许重试 | 失败原因、重试原操作 |
| FAILED_FINAL | 原意图终结或权限/资金已终结；不可重试 | 结果与适用退款信息 |
| RECOVERY_REQUIRED | 切换/策略结果未知或证据冲突 | 待核对、核对原操作 |

允许转换：ACCEPTED→WAITING_AGENT/PREPARING/VERIFYING/SUCCEEDED(DISABLE)；WAITING_AGENT恢复到已持久的原阶段；PREPARING→PREPARED/已证实失败；PREPARED→ACTIVATING；ACTIVATING→VERIFYING或RECOVERY_REQUIRED；VERIFYING→SUCCEEDED或RECOVERY_REQUIRED。任何阶段身份撤销不能绕过未知副作用直接退款：已证实未执行才FAILED_FINAL，否则RECOVERY_REQUIRED。普通断线不使状态倒退；WAITING_AGENT不能掩盖“已切换但未知”，后者用RECOVERY_REQUIRED。

FAILED_RETRYABLE仅在重试资格有效时开始新attempt；INSTALL/UPGRADE的新候选安装ID不改变目标productVersion/包/权限/支付关系，ENABLE仍引用原安装。换目标必须新明确报价与意图。恢复核对读回可信证据后可恢复原阶段/终态，不自动重复ACTIVATE。SUCCEEDED/FAILED_FINAL不回到执行态；后续离线、依赖变化放在runtime维度。

坏摘要/暂时下载失败只有证实未激活且原资金可继续才可恢复；包身份/权限撤销等终结原因不能统统标“重试”。result.reasonCode是诊断，不能单凭一个failureCode绕过阶段/证据检查决定退款。evidence.UNKNOWN必须使retryAllowed=false。

## 7. 错误与幂等HTTP状态

成功查询/报价200；动作接纳202；错误统一HttpError，data=null。即使已有操作失败，GET成功读取仍200，业务失败在SkillChange内；不能把查询失败伪装为空列表。

| HTTP | code | 调用方动作 |
| --- | --- | --- |
| 400 | BAD_REQUEST / PROTOCOL_VERSION_UNSUPPORTED | 修正字段/协议，不自动兼容旧报文 |
| 401 | UNAUTHENTICATED | 重新认证，不重放为新购买 |
| 403 | AGENT_FORBIDDEN / SKILL_DOWNLOAD_FORBIDDEN | 停止越权动作；普通资源查询防枚举用404 |
| 404 | RESOURCE_NOT_FOUND | 无权/不存在；不据此换key重买 |
| 409 | IDEMPOTENCY_CONFLICT / SKILL_STATE_CONFLICT | 原键异参或状态已变，读回后由用户决定 |
| 409 | SKILL_CHANGE_PENDING / SKILL_ALREADY_ORDERED | 查原操作/已有安装，不重复提交 |
| 409 | SKILL_VERSION_NOT_PUBLISHED / SKILL_UPGRADE_POLICY_UNSET / SKILL_UPGRADE_NOT_ALLOWED | 刷新候选/说明原因，不猜价格或资格 |
| 409 | SKILL_QUOTE_EXPIRED / SKILL_QUOTE_MISMATCH / SKILL_PERMISSIONS_MISMATCH | 未提交准备失效，重新明确确认 |
| 409 | SKILL_RUNTIME_MAPPING_REQUIRED / SKILL_AGENT_OFFLINE | 先补合法绑定/连接；离线安装的合法等待不返回这个错误 |
| 409 | SKILL_RETRY_NOT_ALLOWED / SKILL_RESULT_CONFLICT / SKILL_DELIVERY_FENCED | 原操作查询/核对，禁止另起副作用 |
| 422 | INSUFFICIENT_FUNDS | 报价有效但资金不足，整事务无安装副作用 |
| 503 | SKILL_STATE_UNAVAILABLE | 原位重试查询；写结果不明按原key恢复 |
| 500 | INTERNAL_ERROR | 记录关联ID，不伪报确定未执行 |
| 410 | ENDPOINT_RETIRED | 该链切换后旧写入口不可再调用 |

不把所有经济/系统异常硬映射409；未分类内部异常500、依赖不可用503。真实405/415等传输错误仍按公共规范处理。WS拒绝沿AsyncError使用相同code，无HTTP status字段；成功结果存储回执必须在事务提交后发。安全msg不含token、主机路径、SQL或其他Owner信息。

## 8. 规范化摘要与跨端固定向量

不改写历史hash。新管理消息使用独立域；沿现有codec实现以下确定性JSON规则，不依赖Map插入顺序，不用日志脱敏对象算hash：

1. 只允许本Schema字段与类型，拒绝重复key、孤立surrogate、非有限数及非整数number；整数用最短十进制，-0/小数/指数token拒绝。
2. 对象key按UTF-8无符号字节序排序；数组保持顺序（Permissions在生成前按同序排序、重复拒绝）；null保留，不删空值。
3. 无空白UTF-8 JSON，无BOM/末尾换行；`"`和反斜杠转义，控制字符按下述唯一规则编码，其他Unicode原样，不做NFC/大小写归一。五个JSON短转义固定为`\b/\f/\n/\r/\t`，其他U+0000～U+001F固定用小写`\u00xx`；正斜杠不转义，U+2028/U+2029原样输出。
4. SHA-256输入为`UTF8(domain) + 0x00 + canonicalJson`，输出裸小写hex。schema/examples中的digestVectors同时提供canonicalUtf8和SHA，含非BMP字符检验，不能用JS默认UTF-16排序替代。

| 摘要 | domain / 覆盖对象 |
| --- | --- |
| HTTP输入 | `cyf.skill.request.v1` / `{method,path,data}`，path为解码并按本合同规范化的资源路径，身份scope和key在唯一约束中绑定；requestId不参与业务摘要 |
| approvedPermissionsSha256 | `cyf.skill.permissions.v1` / 已按规定排序的完整权限数组 |
| commandSha256 | `cyf.skill.command.v2` / 整个CommandData去掉commandSha256、deliveryEpoch；其他所有字段包含，因此同command不同授权/目标必冲突 |
| preparedSha256 | `cyf.skill.prepared.v1` / `{skillChangeId,attempt,source,target,approvedPermissionsSha256}`，仅在实际包/manifest/依赖核验且准备journal持久化后产生 |
| resultSha256 | `cyf.skill.result.v2` / 完整ResultData去掉resultSha256，包含原执行实例与原投递代际 |

command业务摘要排除deliveryEpoch仅用于同一逻辑命令合法重投；不代表可任意改epoch，必须匹配API投递记录和当前身份。result消息/原始字节重发保持不变，不能因重连改原执行事实。旧命令摘要、旧订单hash和归档证据原样保留，不能批量重算后伪装新协议。

## 9. 一致性与上线边界

- 新DTO、生产者、消费者、同源fixture一起改。首先做实际Java serializer→完整wire→Web/Runtime parser及反向回执的定向测试，再做HTTP/WS/DB和故障链。Schema/例子静态通过不等于真实接口可用。
- 当前本地与remote develop并不一致，完整值见来源基线；本文核对的是所列本地源码及现有原型，不宣称远端全部差异已审计。开工固定候选并将变更差异映射到本合同，不反向偷偷改协议。
- 原型里的1.1.0、0积分、平台发布/升级覆盖不当作真实数据；真实发布政策/包审批/测试身份是实施输入，协议对缺失输入的拒绝方式已固定，不留三端各自猜测。
- 当前成功安装只有精确可信证据才映射为新管理来源；冲突/缺证据显示待核对，不猜最新。历史记录不覆盖、不伪造新购买订单补外键。物理存储增量/迁移脚本由API实现Owner完成并测试，不以本合同授权执行迁移。
- 内测不保留旧wire双解析。本链协调切换时隔离旧协议待投递/恢复输入，保留历史订单/账本/身份/证据；本合同内已准入旧技能版本继续运行，**不等于恢复旧协议任务**。停机/迁移/生产安装需本次实际授权，不复用历史授权。
- Runtime程序固定app目录，不新增程序releases/current。四小时是目标排期，不因时间不足取消旧任务保护、权限或回归；规范收口、本机静态检查、开发完成、Flow通过、安装、业务验收分别记录。


## 2026-10-24 执行命令兼容与恢复分类（最新授权）

覆盖此前“一律拒绝未知字段/不兼容旧输入”在下述执行命令范围的解释；管理DTO和TaskSkillBinding仍按原封闭Schema。公共规范为v1.3，公共协议版本未改变。

| 校验/场景 | 规则与实现 |
| --- | --- |
| 执行命令顶层、skill、outputs新增字段 | 不再按字段总数拒绝；保留原对象参与摘要，runner只接收已声明字段；输出合同比较已定义4个语义字段 |
| 必需字段、身份、ACL、绑定、输入授权、包/文件摘要、租约及幂等 | 保留；不以“兼容”默认缺失授权或改写原证据 |
| 已完成旧记录缺新字段 | readSkillRecoveryCheckpoint先核验原identity/摘要/receipt，只跳过本地已完成调度；不重跑、不发布新的成功 |
| 旧未完成记录缺taskSkillBinding | SKILL_RECOVERY_BINDING_REQUIRED，保留原记录并隔离本execution；同ID新报文不得替换，其他任务继续 |
| 已有UNKNOWN副作用 | 原防重放及恢复规则不变，不重新调用模型/Provider |
| 单记录坏JSON/缺字段/无效回执、带可信ID的坏inbox项 | 收集executionErrors，继续独立合法任务；处理后仍报告错误与processed，不伪报整轮成功 |
| 目录权限、软链/硬链、主体或命令摘要身份冲突 | 仍fail-closed，终止本轮；不能作为普通版本不兼容吞掉 |
| 未知执行协议 | 不猜测执行，隔离可识别单条记录；本轮只支持现行协议4执行，不恢复旧写接口 |

恢复扫描顺序：私有目录及原identity → 原command摘要 → 已提交receipt → 未完成attempt → 当前执行DTO。扫描不得调用会创建目录/identity的构造器；只读分类不能迁移/删除数据。新任务通过原服务端claim/授权再执行。

实现落点：Runtime `skill-execution-store.mjs::readSkillRecoveryCheckpoint`、`skill-conversation.mjs::pendingCommands/poll`、`skill-executor.mjs::parseSkillCommand/executionView`。不改Web交互或API管理权限。

发布前必须用旧已完成、旧UNKNOWN、坏单记录、新合法命令的混合fixture验证升级/重启，验证原字节与摘要不变、新任务继续、模型调用不重复；允许对真实存量只读盘点，但不重放历史数据。记录源码、正式测试、安装、线上业务验收四种独立状态。

核对日期2026-10-24；修复基线Runtime ec9ac757c40466670f0627a1e5486d8df5a4fce3，本轮候选1.3.2/engine1.1.2。50项本机定向测试通过，仅诊断；正式Flow与候选上线尚未完成，不能据此重标旧业务验收。


### 2026-10-24 校验必要性补充

用户要求扩展到全源码扫描；当前公共规范v1.4及[必要性规格](../../api/docs/interface-catalog/validation-policy.md)为最新规则。HTTP/M外层、列明的只读投影和收件箱批次上限按该规格简化；具体授权、输入/结果摘要和副作用恢复不删。未裁定项仍列待核实，不因“扫描完成”认定全量修复/上线。

### Native 技能在线判定（2026-10-25 回归修正）

- 当前 Runtime 的技能管理走已认证 HTTP pull，不在 `readyCommandTypes` 声明旧 `SKILL_INSTALL`。在线判断不得把“没有旧 WS 安装适配器”解释为 Agent 离线。
- Native 在线事实必须同时满足：当前已注册且持久状态健康的连接、精确 tenant/client/owner/agent、唯一 AVAILABLE 技能目录与当前 installation/host/runtimeInstance/sessionGeneration fence。目录在线只证明通道，不能替代单技能 READY、安装权益、任务授权或摘要核验。
- 风险与失败范围：跨身份、旧连接、错 host/代次、重复连接或目录不可用仍拒绝此次准入；不猜测权限、不重放历史任务。旧 WS `dispatchManagedSkill` 仍要求真正声明 `SKILL_INSTALL`，不得因 native 在线而下发旧命令。
- 实现入口：API `AgentWebSocketHandler.isManagedSkillSessionReady`；复用 `AgentWebSocketRawCommandDispatchTest.skillDispatchRequiresRealAdapterReadinessAndExactCurrentTransportFence` 验证 native 在线、旧命令未启用、错 fence、目录挂起和旧适配器兼容。生产任务523已复现：原图实际附载、ACTION_REQUEST持久化后被旧在线判断报 `SKILL_AGENT_OFFLINE`；修复后的正式Flow/业务结果另见本次handoff，本文不预报通过。

### 历史本地命令不能阻塞当前任务（2026-10-25）

- 已实测旧技能执行记录缺少 `taskSkillBinding`，包括已完成、有回执的历史记录；旧记录不能按当前执行合同重新准入，更不能补造绑定。Runtime扫描历史记录时的命令级 `SKILL_COMMAND_INVALID` 只隔离对应execution，保留全部原始命令、效果与回执，继续当前合法命令。
- 本轮不清理数据、不把未知旧任务标记完成、不自动恢复或重放。最终轮询仍报告原错误、executionErrors和真实processed数量。共享私有目录、文件身份/权限、会话/锁归属和完整性错误仍中止，避免跨身份处理。
- 实现 `skill-conversation.mjs` 的 `pendingCommands/poll`，复用既有历史UNKNOWN不饿死后续任务回归加入旧无绑定记录分支；不新增非关键测试套件。候选Runtime1.3.4/ed2855e，正式验证/安装状态见handoff。

### 当前技能与历史安装的展示边界（2026-10-25）

- 升级是原技能替换当前安装，不是新增一个并列技能。点将册技能详情、已安装数量及新任务技能候选只读取 `SkillManagedState.activeInstallationId` 指向的安装；准备中/失败/回执未知不根据目标版本或semver提前切换。
- 历史安装描述符继续用于已绑定任务的精确版本读取/恢复；不删除旧包、旧权益或任务绑定，也不把它们计入当前安装数量。启停不改变版本指针，运行就绪仍由当前Runtime事实单独判定。
- 未建立管理状态的历史来源沿原读取语义兼容，不猜最高版本、不伪造当前指针；有管理状态而没有active指针时不把历史安装展示为当前。
- 实现候选API `3aae986cb4f3efa3d8ddcc0ce62e7077a1c863a2`：`InstalledSkillDescriptorLookup.readCurrent` / `InstalledSkillDescriptorService` / `ChatActionCapabilityService.observeInstalledSkills`；`read`历史语义不变，不新增wire字段/数据库结构。回归入口为同名服务单测及既有 `SkillManagementTransactionTest.coveredUpgradePreservesExactOldTaskReferenceAndClosesAdmissionOnlyAtActivation`。正式验证/发布状态见原handoff，不由本段认定上线。

### 2026-10-25 技能管理不再依赖隐藏功能开关（实现候选，发布另验）

- 安装/升级/启停管理是Runtime内置能力，不要求profile声明`skillInstallEnabled`；旧值为false/true或缺失均忽略。岗位技能和归档同步不再共用此开关；仍要求当前认证会话ready、命令授权、持久状态健康。
- API不再以`economy.skill.marketplace.enabled`、`agent.position-skills.enabled`或`economy.skill.marketplace.adopt-hosting-credentials`作为技能功能/唯一托管凭证识别门控。历史字段可无害保留，不改变身份与凭证归属验证。
- 保留用户单技能启停、身份ACL、租户财务授权范围、包摘要、任务绑定、幂等/事务/锁与恢复保护。数据库schema-maintenance profile、schema/seed开关与测试发币控制具有真实写入副作用，不随本次功能开关删除自动启用。
- 前端能力DTO字段`skillMarketplaceEnabled`继续表达当前主体实际可用性，不是新增人工开关；缺授权或服务不可用不得伪造为true。
- 验证入口：Runtime skill-install-manager/runtime-host缺字段及历史false/true三组真实安装；API SkillManagementBuiltinConfigurationTest、技能事务/凭证/岗位回归。源码候选、正式测试、安装和业务验收分别记录在既有handoff。

## 2026-10-26 媒体替换与失败规划读取补充（已发布，本次业务验收通过）

固定基线与验证状态见 `../../docs/implementation/handoffs/CODEX-BRIDGE-REPAIR-20261026.md`。本节合同已由Web326/API325/Runtime65发布并完成task530定向验收；不代表全站或401专项闭环。

- ACTION_REQUEST 的 `deliveryRelation.mode=REPLACE` 仅用于精确冻结的媒体成果批次；必须同时指定 `targetOutcomeId/targetFinalDigest`，对应deliveryTargets中的outputSource项。ANSWER的REPLACE仍只替换text项。父链及目标必须属于同一授权任务、指派与成果摘要；不允许凭文件名、最新时间或聊天文字推断目标。
- 执行完成且真实输出校验通过后，在保留集合中替换目标outcome全部输出（保持其他项和原位置）；执行未完成、失败、未知不修改旧成果。规划文字不是输出，模型不能提供存储权限或伪造outputSource/replaces。
- 必要校验：父/目标摘要与冻结集合用于防串任务、错替换及并发旧上下文；仅拒绝该请求，不删已有成果。实现入口为bridge `validateActionOutcome`、API `verifyDeliveryRelation`/`deliveryTargets`，回归为既有action-outcome/retained-output测试。
- 已失败或取消且无已提交成果的规划turn读取投影使用FAILED/CANCELLED，所有outcome和progress为null；PENDING仅代表尚未完成。存在finalDigest而缺少成果行仍为不完整事务，不按普通失败忽略。前端只放行已验证空终态，不把UNKNOWN/PARTIAL、读取失败当成无成果。终态不接受迟到PENDING降级。
- 组件现定名codex-bridge，仍依赖Codex app-server，不宣称完成通用引擎解耦。历史报文、日志及摘要不改名重写。

## 2026-10-26 用户修订：安装即授权（实施中）
本节覆盖此前逐项批准权限/逐Agent配置确认的交互要求。选择安装或升级即批准固定候选的requiredPermissions；仍通过既有approvedPermissions及摘要传递，不新增API、不跳过ACL/版本绑定/幂等。权限仅在折叠详情展示，不再勾选或提醒；真实报价与费用确认保留。Runtime的skill-bindings.json可增加scopes[{tenantId,clientId,providerAliases}]，providers.json可增加scopes[{tenantId,clientId,environment}]，相同manifest所属范围的Agent自动取值，主体显式配置优先；不能从process.env或另一个主体隐式借用。scope重复、跨身份、非法环境字段拒绝；依赖缺失仍真实失败，不伪造READY。本次不采纳“缺依赖也算安装成功”方案，PREPARE/ACTIVATE及preparedSha256语义不变。旧配置继续兼容；新配置须随兼容Runtime受控启用，不能先写入旧程序。安装不触发模型调用，不自动重放UNKNOWN。

## 2026-10-26 增补：受控卸载（实现目标，尚未发布）

本节覆盖历史“卸载后续再做”的范围。共用接口规范 `api/docs/interface-standard.md` v1.4；不改变岗位功能。

1. **请求**：复用 `POST /agent/{agentId}/skill-changes`，新增 `action=UNINSTALL`，其余字段同启停：`skillKey/sourceSkillInstallationId/expectedAgentVersion/expectedSkillRevision`，保留原 Idempotency-Key。无报价、订单、退款、权限扩大；target 保留精确 source 包引用用于追溯，desiredEnabled=false。
2. **接纳**：身份/ACL、完整Runtime映射、精确source和版本CAS、同技能在途互斥仍校验。在线与离线均可接纳；事务内关闭新准入并保留 pendingChangeId，离线显示 WAITING_AGENT；不能仅因API已关闭准入就返回卸载成功。
3. **Runtime**：复用 POLICY 阶段、SKILL_SET_ENABLED 命令与结果摘要/锁/幂等/恢复机制，新增 UNINSTALL 执行语义。移出发现入口和当前安装投影，保留不可变包、历史任务引用、权益、成果、身份和服务配置，不创建GC框架。已停用技能也能卸载；不要求模型服务/执行依赖就绪。
4. **完成证据**：卸载 APPLIED 的 `actual=null`、`appliedRevision=skillRevision`；目标包仍在 command/change.target 中。API只接受绑定当前change/attempt/command/fence的证据，随后核对当前已认证会话的技能目录不再暴露该技能；两者匹配才清 activeInstallationId/pendingChangeId，返回 SUCCEEDED/runtimeSynced=true。旧目录、目录读取失败或未知回执不得伪造成功。
5. **恢复**：确定未生效可 FAILED_RETRYABLE，沿原change推进新attempt；UNKNOWN仅READ核对，不重复卸载、不转退款。失败/等待/未知均保持新准入关闭，保留最后确认的安装信息和原操作。
6. **重新安装**：成功卸载后允许INSTALL；对历史ACTIVE权益仅在确认对应受控卸载已完成时解除“已安装”阻挡，购买权益仍保留。相同产品版本的有效历史权益覆盖重新安装报价（0费用），仍创建新的安装身份和命令，不复用旧任务的安装ID。
7. **版本兼容**：UNINSTALL是新的执行语义，不把旧Runtime识别成支持；部署先Runtime及Web消费者，后API生产者；Web入口仍由服务端allowedActions决定，API切换前不提前显示。旧Web严格枚举不能读取新增动作，旧缓存页面需刷新，不能把仅后端部署视为兼容发布。旧历史动作与结果继续读取。校验依据：防越权、精确引用误删、并发覆盖、重复收费及错误成功；回归覆盖边界如下。

验收：启用/停用状态卸载；取消；重复点击与原键重放；离线等待/重连；已知失败重试；未知READ与重启恢复；跨Agent/越权和旧回执拒绝；在途精确包执行仍可读取；历史/成果/权益保留；同版本权益再安装；390px/PC键盘与关闭刷新。正式跨端、Flow发布和真实页面结果独立留证，不用原型示例替代。

#### 2026-10-26 发布前历史迁入兼容补充
历史迁入（explicit adoption）是现有管理变更之前的已核验安装基线，不要求伪造原管理change。卸载成功后，同一主体/Agent/技能的历史权益仍可用于重新安装；读取既有origin校验原始成功回执、包/权限摘要与归属，再核对其后的真实UNINSTALL已完成且runtimeSynced。缺失或被篡改的历史证明仍拒绝本次重新安装，不产生新订单或资金变化。此规则也防止较早迁入权益阻挡已升级技能的重新安装；不修改历史记录、不自动重放。实现`SkillManagementService.uninstalledAfter`，回归`SkillManagementTransactionTest.uninstallHistoricalAdoptionReusesRightsOnlyWithIntactOriginalEvidence`。

#### 2026-10-26 验收修正：后台刷新不得吞掉确认操作
技能列表已有有效快照和用户已确认的操作时，周期性只读刷新不禁用确认按钮，也不在获取跨标签操作锁后仅因loading而静默丢弃点击。仍保留身份/ACL、跨标签锁、幂等、报价有效期、权限摘要、当前候选与expectedAgentVersion/expectedSkillRevision；实际快照变化继续使旧草稿失效，由服务端拒绝过期版本。不新增开关、入口或确认弹层。实现useSkillMarket.submit及SkillManagement确认按钮，回归skill-market.test.js锁等待/刷新竞争与skill-market-ui-lifecycle.test.js真实组件轮询中确认。

### 目录刷新期间的运行态（2026-10-26）

安装、升级、启停或卸载完成后重新上报技能目录，等待精确匹配的注册 ACK 不等同于 Agent 离线。Runtime 健康且未暂停、有可用执行器时，不在该等待窗口发送会撤销服务端绑定的 offline presence；ACK 到达前不提前恢复业务准入。持久状态损坏或主动暂停仍报告 offline，既有身份、会话代次和结果回执校验保持。风险是出现“安装已成功但目录刷新使会话失效”的假离线；影响范围限当前通道，不修改安装事实或重放 UNKNOWN。实现/回归：Runtime `execution-adapter.mjs` 与 `runtime-host.test.mjs` 的 `catalog re-registration heartbeat`，固定候选19eac2f/1.3.16；线上验证与源码实现分别记录在技能管理handoff。

## 2026-10-26 性能实现约束：local-script解释器测量（1.3.18候选）

- 范围仅Runtime local-script的Node解释器摘要读取；不更改API/报文、工具链摘要字段或身份/权限，不以此扩大成全项目缓存。每次probe/probeTool以及执行前仍完整读取并SHA-256，既有probe结果缓存仍只有同摘要才能使用；无文件大小拒绝阈值。
- 将整文件同步分配改为异步固定缓冲读取，避免约127MB的解释器每次整块进入事件循环内存；1MiB仅是内部缓冲尺寸，不是业务准入上限。不宣称底层磁盘吞吐因此变快，不以测试耗时阈值拒绝请求。
- 必要校验依据：异步读取期间文件、别名或父目录被替换会令摘要与最终启动目标不一致。保留属主/权限约束，用同一O_NOFOLLOW文件描述符读取，检查文件dev/ino/size/mtime/ctime/uid/gid/mode/nlink前后一致及实际读取长度，路径/别名仍指向同一实体；父目录只比较inode/属主/权限，不因无关兄弟文件变化而失败。
- 失败范围仅当前工具测量：probe保持DEPENDENCY_MISSING语义，执行前测量失败不启动技能脚本；不清理历史结果、不重放UNKNOWN。回归入口：`conf/codex-bridge/test/local-tool-measurement.test.mjs`及既有`skill-local-script.test.mjs`；实现`skill-runners/local-tool-measurement.mjs`与`local-script.mjs`。本段描述候选约束，尚不代表发布/性能收益验收。

## 2026-10-26 性能实现：同字节 journal 验证复用（1.3.19已发布）

- 仅作用于单个 `SkillInstallManager` 的最后一份已完整验证 journal，不新增接口、开关、持久缓存或权限。依据：实装 `_load` 对未变化的约299KB/28命令记录反复做严格解析、摘要及全部历史关联校验，单次只读测量80–890ms；这不是端到端根因或收益证明。
- 每次仍安全打开并完整读取文件，保留真实路径、同FD、属主/权限、硬链接和读取前后身份/内容变化校验。只有路径、scope以及完整字节与上一份验证成功的快照全部相同才复用；不凭mtime、大小或TTL信任内容。不同字节执行原有全部严格JSON、摘要、schema及command/result/receipt关联检查。
- 返回独立深拷贝，防调用方修改污染下一次读取；每manager最多保留一份私有快照，重启不保留。保存不会把未验证对象直接加入快照；失败不产生可复用的新事实。不改变刷盘、ACK顺序、恢复、幂等或锁。
- 风险/失败范围：内容损坏或scope/路径漂移不能命中旧验证；权限/别名变化即使内容相同也必须拒绝当前读取，不清理旧事实或重放操作。回归入口为Runtime `skill-journal-validation.test.mjs`（同字节复用、返回对象隔离、同长损坏、合法摘要下坏关联、权限/硬链/符号链接、scope/路径/实例隔离及保存后全验）及既有完整管理器恢复测试。实现和发布/性能验收分别记录，不将此候选写成线上生效。

- 发布核对：Runtime1.3.19/bridge1.1.11，源码04b1129455c3c472a3db3b5ed6a1f1ca7547704e，Flow5264702/81 SUCCESS，583项回归通过。真实UI启停通过并恢复启用；单组耗时下降但仍19.1/33.9秒，不视为稳定性能验收完成。证据见技能管理handoff及 `evidence/management-performance-20261026.json`。

## 2026-10-27 回执调度实现（1.3.20已发布）

仅已确认当前会话且与持久结果精确匹配的技能 `work.result.receipt` 可不等待Runtime外层业务帧队列中的目录刷新。它仍进入 `SkillInstallManager.handle` 原有串行tail/事务锁并完整校验关联、保存回执；不是任意业务帧并发，不绕过下载/切换期间的写锁。普通命令和聊天回执仍走原ingress，目录测量、注册ACK与实际READY判定不变，不提前宣告运行就绪。

必要校验及风险：跨主体/错关联回执会错误退休结果重发；因此解析、当前socket/session/授权、持久结果关联在调度前保留，异步执行前再次核对会话。断线前未接纳的不补执行；已接纳在途回执在close时等待完成，不在写入中释放执行器。影响范围限该主体该回执，失败不回滚已完成技能事实。验证入口 `conf/cyf-agent-runtime-v1/test/runtime-host.test.mjs` 的受阻catalog/回执及时落盘、普通命令顺序、断线、close drain，以及原真实manager串行/恢复/回执绑定回归。实现 `lib/execution-adapter.mjs`；源码与线上状态仍分别核对。

发布核对（2026-10-27）：Runtime1.3.20/bridge1.1.11，源码 `15483d554a0fd6b01c3413d68c80e5367654a942`，tree `d138342b73f384402e7f46138385fe6e7b50bc68`；Flow5264702/84 SUCCESS、597项通过，真实页面两轮PDF启停及最终READY通过。四个命令的首次回执均在catalog结束前处理，外层queueWait约0.027–0.042ms；回执实际处理仍149–1678ms，不能混为同一指标。页面可比样本停用17.007秒、启用30.005/27.616秒，稳定端到端性能未验收。首停用3.844秒仅出现早期“完成”且策略待同步，保留但排除性能比较；计时须等明确Runtime同步完成提示，再单独核对READY。历史Run82磁盘满及83受控中断不重标成功；证据沿用 `evidence/management-performance-20261026.json` 与技能管理handoff。


## 2026-10-28 用户最新决定：原生执行单轨切换

一切以新方案为准，不保留旧协议/旧runner的历史执行恢复。适用范围、切换与未完成任务处置以[RB-1单轨切换补充](responsibility-boundaries.md#2026-10-28-单轨切换补充用户最新决定)及核心详设v3.1为准；覆盖本文此前涉及旧执行续跑、补传、补提交的兼容要求。不改写历史摘要、删除已提交成果或自动重放；新方案自身恢复及正确职责的安装/交易事务保护保留。此处是目标合同更新，产品代码与生产尚未切换。

### 历史：2026-10-29 原生包权益迁移补充（RB-02/08）

以下免费迁移为当时专项授权与历史事实；不覆盖§4.1的2026-11-09新操作收费规则，不改写已接纳迁移的原订单/安装事实。

用户已批准图片技能迁移沿用现有权益、不新增收费。复用管理员受管包发布入口 `POST /agent/skill-maintenance/product-versions`，multipart `metadata` 增加可省略/为null的 `coveredUpgradeFromProductVersionId`；非空时明确批准该来源版本到本次目标版本的 `COVERED` 政策。未提供不自动生成政策，不改变商品售价或任何既有权益/订单。响应回显该字段。

只有同tenant/client、同SYSTEM商品、同skillKey、APPROVED且版本序号小于目标的来源可以覆盖；目标是本次实际发布的不可变包。包发布与政策写入同事务，已存在同值政策幂等，已存在PAID/NOT_ALLOWED拒绝且不覆盖。不得以更换key冒充升级；本轮image-generate/image-edit分别发布自身新INSTRUCTION包，继续使用同商品和真实source installation。升级quote必须返回coverage=ENTITLEMENT、price=0；create必须无新订单，沿现有权益安装与回执闭环。不新增管理UI、跨商品权益转换或直接数据库维护入口。

必要校验及风险：管理员身份/租户与商品归属防止越权授权；来源/目标同商品同key及递增序号防止错误覆盖；既有政策不覆写防止改变已报价执行语义；事务保护避免只发布包或只改政策。失败范围仅本次发布，历史成果/权益不变。实现及回归：SkillPackagePublicationController/Service、EconomySkillMarketplaceMapper（沿用发布持久层，不新增分层例外）、SkillPackagePublicationControllerTest/SkillPackagePublicationServiceTest及SkillManagementTransactionTest；正式验证仍走固定源码Flow。此规格新增不表示已上线。

### 2026-10-29 已提交结果后的ACK重发退休（Runtime候选33d78ac）

技能安装命令收到已认证且关联完整的`work.result.receipt`并持久化后，该命令的主动`command.ack`重发必须退休：结果回执已证明API接收完成事实，继续在每次heartbeat/resume重发旧ACK只会占用同一WebSocket业务队列。仅跳过已有有效receipt的命令；未确认命令仍保留原字节、当前会话约束和发送失败停止语义。历史journal、结果/ACK完整性、直接收到合法重复投递时的幂等响应不删除、不改写，不自动重放业务。职责RB-03执行适配、RB-08持久回执，不增加通用编排或新状态机。必要校验与失败范围：仍由现有journal及receipt关联校验防止错回执退休；异常仅影响本主体重发，不能凭内存发送成功推定接收完成。回归为`conf/codex-bridge/test/skill-install-manager.test.mjs`的cross-boot receipt退休/历史不改/合法重投，以及混合已确认与未确认ACK、发送失败、断会话。生产吴用38/38已receipt仍进入旧ACK重发集合为问题证据；候选测试与上线效果分别记录，不据此断言所有重连根因已解决。

### 2026-10-29 Agent WS接收容量与既有持久边界对齐（API候选ffc5f52）

生产直接观测到API以1009/text_buffer_overflow关闭连接，合法大小的完整Agent消息可能在进入现有codec/业务校验前被容器默认小文本缓冲拒绝。Agent端点接收容量必须能容纳既有inbox MEDIUMBLOB边界16,777,215；将已有值提取为`AgentProtocolConstants.MAX_WIRE_BYTES`并复用于inbox与Agent WebSocket session，不新增业务包体配额、不扩展普通聊天端点，不裁剪/重写完整JSON、授权或签名事实。现行AMQP差异另记，不能借传输修复扩大无关执行语义。

必要性/失败范围：容器过早关闭会使该Agent注册、presence和持久回执持续重连；超出既有可持久化边界仍由传输/原持久校验拒绝，合法消息继续原身份、schema、摘要、幂等校验。回归：`AgentWebSocketHandlerTest`端点设置及真实Tomcat超过默认8KiB的网络用例，要求非法envelope到codec后拒绝且不以1009提前断线；正式Flow与上线后新鲜ACK/关闭码/实际内存分别记录。职责RB-02/API传输适配，无新业务编排/生产DDL，不自动重放旧任务。


## 2026-10-29 注册声明清理与增长边界（源码候选，未上线）

适用：`agent.register`、其注册回执及`agent.presence`；遵循公共接口规范1.2、RB-03/08。保留身份/租户/会话fencing、消息关联、包/权限完整性和原生能力；不改DDL、旧任务恢复/重放、文件下载协议，不新建注册服务、差量同步或分片协议。

### 清理决定

1. Runtime删除注册中的`inputCarriers`；其supportedInputs与`typedDeliberation.materialsInput`重复，API Java注册/能力消费路径没有该字段消费者。API实际消费的materialsInput/nativeExecution不删，本地隔离测量/摘要验证也不删。
2. `runtimeCapabilities.capabilityContractVersion=1`语义不变。新生产者及现代注册回执只发送`capabilityContractVersion/runtimeVersion/profiles/fastChatEnabled/appServerEnabled/trueDeltaEnabled`。固定`protocolVersions/chatProtocolVersions/contextSnapshotVersions/contextEnvelopeVersions/deltaVersions/dispatchAckTypes/deliverySemantics`、从CHAT派生的`interactionModes`和不参与现代路由决策的`legacyCompatibility`不再重复发送。API对旧生产者已经发送的这些描述字段仍按同一v1固定值校验后丢弃，不因删除描述字段猜测新执行能力、不新增旧执行入口；先API后Runtime切换，旧API不承诺接受精简形态。
3. 普通状态构造函数只发送status/currentTaskId/currentTaskTitle/errorMessage；身份公共字段由现有传输适配器附加。当前Runtime周期presence本就只发status/durableStateHealthy与身份，不改其就绪判定。能力变化沿既有注册刷新及相关ACK激活，不混进普通心跳。
4. 取消未上线ffc5f52中把MEDIUMBLOB字节上限用作WebSocket字符容量的改动。数据库上限回到inbox内部，不能用存储容量证明传输内存合理。已有真实默认字符缓冲仍为8192；本轮去重不代表已解决任意规模技能目录传输。
5. 保留的typedDeliberation协议常量参与当前解析/能力授权，非本轮确认的无消费者分支；保留profiles与运行开关一致性校验，防止清理把不可执行路径声明为ready。技能目录16字段有解析/索引/安装一致性消费者，本轮不以“API也有一份”为理由删除权威交叉核验。

### 每类字段的增长风险

|字段|来源/增长方式|结论与处理|
|---|---|---|
|公共信封ID/版本|每条覆盖，固定形状；ID受既有合同约束|不累计消息历史，保留关联/去重|
|tenant/client/agent/host/installation/runtime/sessionGeneration|当前身份会话，代次为现有int64十进制|不随技能/文件增长；不可为瘦身绕过fence|
|name/personaName/senderName/endpoint|当前配置，非历史列表|不会因请求积累，但不是所有发送端字符串都有长度上界；不宣称全报文绝对有界；重复展示字段本轮不改变通用信封和API展示契约|
|abilities|`WORKSPACE_BUSINESS_ABILITY_ORDER`白名单筛选，目前17项|目录/文件增加不自动追加任意字符串；不是技能全文|
|runtimeCapabilities|本轮精简后6个根字段、3个固定profile|当前枚举固定，不随任务/技能增长；新增协议能力需显式修改合同/测试|
|typedDeliberation基本字段|固定结构/枚举与当前状态|固定规模；不能把声明当业务操作授权|
|materialsInput.supportedInputs|已测量载体列表，每种MIME一项、摘要固定长度|不会随上传文件数量增加；但类型集合无maxItems，扩展载体会O(m)增长，未来需重新测量报文容量；不是无限有界保证|
|nativeExecution|当前schema/protocol/policy/输出MIME枚举|现API只接受5种输出MIME和1种脚本策略，无重复；新类型需要合同变更，不随输出文件数增加|
|skillExecution.skills|仅当前、未卸载安装记录，含启用/禁用状态|O(n)线性增长，schema无技能数上限，是主要真实膨胀风险；不截断、不偷偷丢禁用/未就绪技能，不臆造数量门槛|
|每项技能元数据|当前安装ID、产品版本、包/manifest摘要、策略、状态/原因、工具链摘要、观察时间|不传SKILL.md/脚本/凭据/文件内容；大多固定/有界，runner由安装manifest语义限制；避免今后夹带正文或完整执行历史|
|catalogRevision/observedAt|当前值覆盖；现有revision整数合同|不是变更历史数组；重复测量observedAt不应推动catalogRevision|
|历史安装、ACK/result journal、历史产物|保留在本地状态，由专用恢复/查询处理|不进入当前注册目录；升级/卸载后的保留包不自动累加到skills。其磁盘增长是另一运维问题，不借本轮删除历史业务证据|
|状态消息|status/currentTaskId/title/error，以及现有周期健康字段|无能力目录，技能数不影响其长度；title/error是当前文本，不能扩成历史日志|

### 回归与风险结论

- Runtime真实构造/序列化 + 实际SkillRegistry：0/1/4/10/100/1000技能样本；9与90种输入；100次相同目录刷新；缩减目录；真实升级/卸载保留历史但只声明当前版本。样本规模是测量点，不是新业务上限。共享完整公共信封fixture由实际Node生产者生成，两端读取同字节JSON。
- API验证精简/原有扩展形态的相同路由决策、相同精简回执；缺失关键profile、冲突协议值仍拒绝。不是只删测试追求变绿。
- 当前模拟（固定ASCII指令技能样本）4技能约5045 bytes，10技能7553，100技能45173，1000技能421373；每增加一项约418 bytes。此数不是生产全部技能上界，EXECUTABLE/更长ID会更大。90种输入相对9种额外14660 bytes。
- **无最大技能数合同的全量注册列表，没有有限缓冲能证明永久足够。** 本轮只清理确认冗余，不把8192/16MiB/任意新值作为无限扩展方案。增长链路未消除；要支持更大目录，需后续明确容量及正常超限处理，或将目录同步从注册剥离并复用现有管理链路，涉及范围/契约须单独列明，不偷加平台。不能把去重/测试通过宣称全部生产验收完成。

正式验证更新：2026-10-29，Runtime a4940cb/Flow5264702-96（737/730pass/7skip/0fail）；API 7c4fb10624/Flow5260799-367（3280/3121pass/159skip/0fail）。两端同字节registration-compact-v1.json已消费通过。已合develop、未部署；上述目录增长风险未消除，不能据此声称生产验收通过。

### 2026-10-29 用户确认：Agent文本接收容量64K

- 用户明确选择64K，实施为Agent WebSocket session独立的`setTextMessageSizeLimit(64 * 1024)`；当前Tomcat以UTF-16 code unit计数，非UTF-8字节/压缩帧大小，不联动MEDIUMBLOB或普通聊天/二进制通道。
- 注册精简保持；超过65,536文本单位仍由容器1009拒绝，不截断技能声明、不重放任务。64K不代表无界技能目录增长已解决。
- 风险/回归：现网8,330单位注册触发默认8,192溢出；真实Tomcat回归10,000、65,536、65,537，含中文/补充平面字符，界内仍须过协议校验，界外1009。仅影响Agent文本接收；正式证据另记。

上线核对（2026-10-29）：API de6776fb/Flow5260799-371（3286项、3127通过、159跳过、0失败错误），真实Tomcat六项容量边界通过；先API1.17.14、后Runtime a4940cb/Flow5264702-96的1.3.23安装完成，注册精简已启用。三个Agent连续11次30s采样ready/ACK新鲜，17:30再次健康；这是本次通道验收，不覆盖付费业务E2E或历史任务告警，不消除上述O(n)/O(m)风险。证据`/home/isp/state/cyf-native-skills-20261028/agent-ws-64k-20261029/verification.json`。后续其他Owner API发布已开始，当前版本/维护恢复应按该记录的时间与handoff核对，不能把历史验收当实时状态。

### 岗位技能与普通手动安装边界（2026-11-08修订）

责任层API：`agent_skill_product.skill_type`是同一tenant/client所有Owner共享的技能分类（GENERAL/POSITION），不依赖中文标题/skillKey硬编码，也不把安装包当作任职。Owner岗位state只保存岗位关联的版本绑定、任职/撤职、资源权限及安装需求，不作为商品分类或普通安装资格来源。生命周期使用共享分类解析绑定；旧JSON的type字段只读兼容，不作为第二份权威事实，普通读取不重写历史JSON。同一技能不得因浏览账号不同而变成普通技能。GENERAL即便作为岗位附带技能也不按POSITION限制。

普通管理目录保留VIEW/必要RECONCILE，不提供INSTALL/UPGRADE/ENABLE/DISABLE/UNINSTALL/RETRY，deniedActions原因`POSITION_MANAGED_SKILL`；Web复用既有“岗位技能由任职管理，不提供手动安装”和allowedActions展示，不自行推导分类/权限，Runtime不复制API规则。

风险：跨Owner查看、绕过按钮直调新旧报价、购买、变更、重试或报价后分类改变，会绕过岗位生命周期。API写入保留Owner根→商品行的既有锁序（Owner根协调任职授权，不提供分类），在同一事务读取共享商品当前分类后拒绝403 `POSITION_MANAGED_SKILL`；管理员不豁免；新写入不扣款、不建立命令/授权。目录一次读取共享分类集合，不扫描/复制其他Owner数据。已接受幂等回执仍可读取，不取消已有操作。任职/撤职继续原专用路径，包安装不授岗位/资源权限。

既有岗位技能绑定接口保持wire：绑定已审核商品；首次将GENERAL提升为POSITION必须具有`skills:platform`的SKILL_REVIEW/SKILL_PUBLISH，和Owner绑定原子提交。其他Owner可绑定相同已确认分类，不允许借GENERAL绑定降级共享POSITION，也不授予其其他Owner任职。升级沿用商品分类。

已有库迁移使用`api/agent/jia-agent-mapper/src/main/resources/db/migrations/20261108-shared-skill-type.sql`，获授权后在实际库身份、固定快照、停写和发布锁范围显式执行。历史Owner分类冲突/无法解析的POSITION绑定先拒绝并报告，不猜测或启动自动修复；无冲突后回填商品列，不改任职/权限/历史JSON或回执。仅源码/隔离测试，不等于线上迁移/发布。无新DB表、CHECK或Runtime逻辑。

回归：SkillManagementTransactionTest（跨Owner目录/管理员/普通与旧购买准入/报价后分类改变、无分类修改权限、GENERAL附带技能、任职撤职隔离），SkillManagementCatalogTypeMigrationTest（真实MySQL回填/幂等/冲突/范围隔离），PositionSkillPolicyTest。既有Web wire无变化，不要求重复Web/Runtime构建。准确源码、测试及发布状态沿`REUSABLE-SKILLS-20261102` handoff记录；2026-11-04历史验收仍只证明原Owner范围。
