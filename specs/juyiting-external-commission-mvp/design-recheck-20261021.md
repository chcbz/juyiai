# 外单详设：代码与生产实页复核（2026-10-21，D2.1）

> 历史复核：代码观察与当时生产证据保留；D2.1范围及修订结论已被 [D3](design.md) 替代，尤其自动首轮应复用，不再要求待指令、独立撤回或外单专用资料协议。

## 1. 结论与证据边界

D2业务规则已明确，但不能仅凭原文直接按“加开关＋放开canOperate”开发。复核发现**首轮自动发送、本人名册守卫、双client域、撤回/取消、ACK归属、资料默认授权**等落地缺口。D2.1已补充约束和工作项；安全与数据库验证仍须实施阶段完成，不能称为已实现或全链验收通过。

唯一Owner仍为当前聊天；本次只读生产实操、定向源码阅读和设计修订，没有派发任务、修改业务源码、DDL、构建、部署、真实派单、修改线上Agent开关或调用模型。使用已有授权测试账号，独立临时浏览器；不读取/控制用户或其他聊天的浏览器。请求拦截允许GET及已审查的列表/推荐POST，阻止业务写入；OAuth登录是认证例外。凭据不写证据。

基线：`evidence/design-recheck/baseline.json`；最新读回/源码文件摘要另见同目录 `source-readback.json` 与 `online-readback.json`。原 `baseline.json` 保留历史，不回写为新一轮测试证据。公共接口规范仍1.2，SHA未变。

首次固定API为`510b2937696495b54a9203729784660e62c65082`；Web为`19a322a4b3b51856f8c1235a73d3aac4d848b022`。复核期间其他任务正常推进Web至`68552ea79a033e62159f4ee99fae6c724adb243c`；两者src差异只有`src/composables/useOutputs.js`的6行差异，本次名册/承办/议事守卫文件未变。随后重新加载生产并复查当前页面。Runtime本地与本次查询远端develop均为`5e8742aac6b9261a8d6cc94f77da1175e8ae74e2`，D2的“本地与远端不同”不再作为当前阻塞。

## 2. 生产实际操作结果

| 页面/操作 | 本次看到什么 | 对外单设计的意义 |
|---|---|---|
| 真实OAuth登录→办事首页 | 首页先填需求，创建提示不调用Agent | 保留现有主线；未点击开始办事写入 |
| 打开提出需求→返回 | 需求与资料可选，尚未选择承办 | 不在首页/创建页增加选Agent步骤 |
| 打开点将册→吴用详情 | PC和390×844移动均有技能、本领、刷新、密议，无接外单开关 | 原型是新增设计，不能称生产已有开关；仅详情加开关行 |
| 打开现存待点将事项492 | 任务详情、固定资料v1、推荐承办与确认按钮 | 未新建或改变任务；任务号只作本轮观察证据 |
| 展开“另选承办Agent” | 当前可见吴用、扈三娘、李逵、林冲；没有全部/我的/其他用户筛选、提供方归属和外单确认 | 不能凭名称推断他人Agent；这是当前账号的既有候选逻辑 |
| PC/移动待点将详情 | 提示“已有授权与费用规则保持不变”，取消仅“未实际开始” | 新外单文案不能照搬旧费用含义；取消范围与D2承诺不一致 |
| 任务资料与成果入口 | 可见固定版本资料、当前暂无正式成果 | 仅看引用元数据，不发送附件、不预览客户图片内容、不验收 |

证据：`live-agent-detail.json/png`、`live-agent-mobile.json/png`、`current-page-actions.json`、`current-live-*.png`、`live-candidates-expanded-*.json/png`、`readonly-network*.json`。早期 `live-assignee-options` 是折叠状态，不作为候选展开证据；展开结果以上述expanded及current批次为准。无业务写入不等于跨用户链路成功：新接口尚未实现，本轮没有第二/第三个独立授权账号，因此A/B/C真实越权、运行取消、模型和成果交付均未测。

## 3. 缺漏及修订

### R01 高：详情/议事仍把“承办方”限定为“本人可管理Agent”

- `web/src/components/juyiting/BountyPanel.vue:665–680` 的 `assignedAgentForTask`、`matterCandidates`取`operableAgents`并过滤canAssign。
- `web/src/components/world/JuyiHall.vue:2014–2027,2341,2370–2373` 的 `discussTask`、attach和点将回调均重新查本人名册。`resolvePermittedConversationAgent`在2892附近仅允许boundToMe/canOperate，适用于私人密议，不能全局放开。
- **修订**：候选、当前任务授权目标、私人管理名册三个读模型分开。任务详情、恢复、继续办理、workspace actor均使用本任务权威target摘要/actions；普通密议/安装/刷新完整技能目录保持本人权限。不能通过传入外部DTO或设置canOperate=true绕守卫。

### R02 高：自己的Agent也被在线状态/eligible硬拦截

- `useHallData.js:95–101`需eligible不为false、canOperate且status=online；BountyPanel二次过滤。`AgentServiceImpl:1984–2011`旧assign路径按allowQueue拒绝busy/offline并validateAbility；当前普通单目标实际入口是`point-and-deliberate`，不能误以为只改旧assign就覆盖。
- **修订**：新的普通单目标承办资格OWNED/EXTERNAL统一遵守“能力仅推荐、离线可先委派”，并分别回归实际调用入口。已有funded/team路径不借此扩大范围；真实身份/安装服务有效性仍校验。展示故障与不具备身份资格分开。

### R03 高：D2“入单不发送”与现有grant/首轮bootstrap耦合

- `AgentTaskExecutionGrantServiceImpl.assignForDeliberation`读取allTaskMaterials，`assignLocked`始终要求bootstrap存在；`ChatBountyBootstrapAdmissionService:130–150`在ensure会话后立即admit首轮讨论/outbox。不能直接复用该公开入口而又承诺“待指令”。
- 该writer还先锁grant-action/bootstrap-action再进入身份/输入锁；原文task→identity→grant简写不是已验证的真实全序，D2.1已纠正，需共享锁序回归。
- **修订**：单独的外单接单编排方法复用底层task-root/assignment/grant writer，但不得调用auto-bootstrap admission。持久化`initiationMode`区分AUTO_BOOTSTRAP与EXPLICIT_INSTRUCTION；外单只准备任务会话，首条指令另经现行typed discussion提交。细节见详设§11.2。需同步原grant/readback不变量，不写伪SENT/伪requestId。

### R04 高：跨客户端模型仍只保存一个clientId

- 当前表和服务scope同时把client用于任务与认证Runtime；`TenantClaimPolicy`只解决tenant claim，不提供“多个OAuth client属于同平台”的映射。
- **修订**：任务域与执行域完整持久化（task tenant/client及executor tenant/client），平台归属从可信配置/身份源解析；政策按执行者域索引。已知代码不能证明全平台OAuth映射已存在，实际映射输入仍是实施阻塞项，不偷偷降级为“仅同client”也不去掉tenant校验。

### R05 高：只改delta/final会漏掉ACK、停止和receipt

- `AgentWebSocketHandler:1190–1235`将session B的owner传给`ChatDeliberationOutboxService`；后者按该owner锁outbox，而外单outbox数据应属于A。仅修出站会导致ACK拒绝/重投。
- **修订**：dispatch ACK、receipt、invalid-outcome、stop及停止ACK都经认证B→持久dispatch/turn关联→A；每一分支复验agent/binding/fence，旧代际不得写新任务。原typed session discovery仍保持B，不可全局替换owner。

### R06 高：运行中撤回不是已有取消服务的一次调用

- `AgentTaskCancellationServiceImpl:100–114`拒绝非初始work item及执行/指令事实。`ChatBountyExecutionTerminationController`只放弃指定execution，不是整单取消，更不是撤销Provider调用。
- **修订**：复用锁/状态writer和终止恢复能力，但明确新增委派撤销协调。A取消整单、A撤销委派、B撤回服务是三个语义；B不能把A任务直接标CANCELLED。运行中的撤回先禁止新工作，历史结果与未知效果保留；切换新承办先核清旧执行。详设§11.4，实施项及验收单列，不称“已有支持”。

### R07 高：输入空列表会被旧入口隐式扩成全部资料

- `assignForDeliberation:124–135`默认allTaskMaterials；与D2委托payload显式inputRefs的最小授权含义不同。
- **修订**：外单inputRefs为完整初始授权集合，空数组就是无授权文件，不能默默取allTaskMaterials。委托页逐项显示fileId/version对应名称与用途/摘要；新增资料必须显式授权并生成新grant版本。显式授权边界与本轮聊天引用范围分开，不把消息未引用等同于撤权。

### R08 中：B撤回/换人会话代际、可见历史和结果去向未固定

- 当前`ChatBountyConversationService.ensure`可以替换任务target，仍复用既有conversation。仅换target不足以证明旧回报不能写新承办。
- **修订**：换承办必推进assignment与任务会话授权代际；A保留原历史，新承办只获得当前需求和本次授权材料，不默认把前承办完整thread/上下文移交。旧回报归旧执行审计，不覆盖新turn；Unknown效果不能借换承办自动重做。

### R09 中：候选/详情DTO缺少实际UI所需的公开归属

- D2候选字段没有providerDisplayName，却要求展示归属；原profile-capabilities API仅boundToMe可读，不能直接给他人的详情复用。原型“外部Agent”也易误解为跨平台接入。
- **修订**：candidate/task target增加`providerDisplayName`（公开昵称，null有占位）和只读`externalServiceState`；界面用“所属用户：…”、“其他用户的Agent”，内部relation=EXTERNAL不变。管理名册保持原范围；只在本人详情内加开关，无独立卡片。他人摘要不请求私有安装目录。

### R10 中：恢复/分页/开关失败状态只有原则，没有完整前端处理表

- **修订**：固定关闭确认不取消存量；PUT未知时按原key查政策操作回执，不能GET最新开关代替原操作结果；加载失败不当默认关闭。候选空态、推荐失败、游标失效、目标关闭后的重新选择、选人/账号切换迟到响应均增加用例。已接任务的target展示不能依赖它仍存在于“新单候选列表”。

## 4. 当前开发就绪程度

业务规则无需重新让用户选择；D2.1已能指导按工作项拆解实现与失败回归。但**不能宣布所有实现前提已闭合**：平台域映射/双主体DDL与锁序、撤回协调及新grant/bootstrap不变量，须先完成EX-01/02的具体验证后冻结接口候选。真实跨用户、并发、Runtime隔离、恢复和最终交付必须实施后测试。原型通过、生产同账号页面正常、历史Flow成功均不是该功能验收。


## 5. 原型与最新详设的剩余差异

当前离线原型已经把开关放回本人详情，但仍是示例状态，不具备原操作回执、真实分页/CAS、跨用户授权。原型还使用“外部Agent”和合并的“待指令/待运行”演示；D2.1要求的公开归属文案、独立准备/待发送/已受理待运行状态、完整宿主信任提示及加载/冲突/未知恢复状态，须在产品UI实现前同步补原型。本轮不以更新详设冒充这些交互已完成。

最终生产读回：Web记录1.16.35/commit68552ea/Flow279，实际加载16份资源与安装文件及该记录摘要一致；API安装记录1.16.23/commit510b293/Flow216、实体JAR摘要一致。这里只读取已有发布证据，本聊天没有发起发布，也未证明Runtime当前安装版或该外单功能已上线。
