# 代码级详设：Web、页面与交互

> 2026-10-23整理：本文保留原日期源码/设计定位，不按旧排期执行、不从“待实现”文字推断当前代码。当前范围与交互见 [spec.md](spec.md)，剩余工作见 [tasks.md](tasks.md)，后续成果多选及历史稿验收见 [最新详设](../../juyiting-external-commission-mvp/design.md#selected-output-acceptance)。发布/验收独立查证。

2026-10-18；状态：**待开发**。既有文件基线见`code-baseline.json`；新增文件均为设计路径。依赖[后端合同](code-backend-design.md)，唯一原型为`web/prototypes/juyiting/`。先改对应原型与最新规格再改下列产品组件；不使用会话附件中的历史“先聊一聊”页面作为实施入口。

路径约定：下文`src/`均相对`web/`。新增组件沿JavaScript、Composition API、已有useHttp与身份生命周期，不新建状态管理框架。

> 2026-10-19编码前收口见 [权威上下文约束](detailed-design.md)：权威指派context的同步reset亦须处理；D01规定完整修复边界；旧dialog.revise事件移除，修改仅从原议事输入。此补充不表示源码已修改。

## 2026-10-20 UI补差快速实施核对

本节只针对 [本轮8组差异](ui-parity-recheck-20261020.md)，不重启下文历史全量开发。固定Web `50107f38a757a5ce58d298965a953a353d7b48b1`；只读核对，不代表编码完成。历史“待开发/新增模块”以本节基线源码是否已存在为准，严禁重复创建review、状态投影、停止回复或重做Runtime。

**开发就绪结论：已有设计可指导大部分补差，但尚不足以保证8组差异全部在30分钟内完成。** 30分钟为用户要求的编码窗口，非已验证工时；正式Flow/部署/双端验收另列，不能缩范围冒称全部完成。

|补差|既有落点与明确约束|就绪程度|
|---|---|---|
|UI-01需求表单|`HallDraftEditor.vue`只改TASK_CREATE分支布局/校验/资料渲染。原型interaction-completion.js的既有规则：显式名称，否则需求trim前36字符，否则“资料处理”；正文完整保留。服务端requireTaskCreate仍要求非空title，因此在现有persist前派生有效title并随当前保存revision固定，不删后端校验，不调用模型。空白无资料不能开始；只附资料可用兜底名称。保存快照/needsSave应比较同一规范化有效字段，不能生成标题后造成永远未保存。私人分支不变|命名规则已找到；资料模板可见性根因仍须DOM定向确认|
|UI-02待点将|`BountyPanel.vue`复用候选和现有start事件。选择只存当前task的本地候选ID；确认时重核资格，再调用原指派链；换task/身份清选择。不能改成点候选直接请求|F1已明确，需补候选切换/确认单次触发测试|
|UI-03进行中|同组件按现有phase/actions渲染事项进展、承办、资料成果；继续议事沿用原事件。保留待验收、终态、取消权限及未决操作提示，不改状态机|F1/F2/C04足够，不重新实现状态投影|
|UI-04输入区|`HallChatComposer.vue`compact分支输入独占100%一行、工具另起行，不再只在≤360px换行。保持44px输入高度与内部滚动、44px触控/20px图标；不删除目标选择、录音、停止回复、附件与IME逻辑|补齐F8仅规定高度、未明确全宽的缺口；320/390/1440定向回归|
|UI-05筛选|原型5入口，当前常量和接口分别HISTORY/UNKNOWN，useHallData查询单phase。不能仅删UNKNOWN、只查询HISTORY或把当前页数组混合假装完整聚合。需先确定合并入口的查询/分页/计数实现，再对照唯一原型|未就绪：旧详设缺合并聚合的代码级合同，影响30分钟全量承诺|
|UI-06顺序与配色|只调整JuyiHall/ChatPanel现有正式议事技能条展示位置与输入区局部样式；不迁移技能调用/生命周期，不全局影响私聊/公议权限|目标明确；采用现有token，不扩建设计系统|
|UI-07导航|沿用navigationPresentation和原return handler，不为显示返回按钮重写路由栈。原型对应根面板需返回，无返回独立弹窗保留close，不能只换图标却仍走错误层级；保留焦点和录音锁|F5可用；还须定向核对各入口根层返回目的地|
|UI-08帮助|HallMinePage复用既有open-onboarding接线；不添加原型页面索引到生产，不重做向导|目标明确，补一条入口事件测试|

实施顺序：先在编码窗口前解决UI-05合同与UI-01渲染根因；主链路表单/点将/详情/输入→筛选/工具栏/导航/帮助→必要定向检查。若未解决，不将8项标记“全部ready”，也不默认为用户接受只修CSS。新发现的不相关问题仅记录，不扩范围。

最少定向检查：标题派生与草稿revision一致；选人不发请求、确认单次指派；身份/事项切换不串候选；四主状态CTA正确；HISTORY与UNKNOWN均可完整查询且未知计数不当0；移动输入宽度与按钮可达；返回无双出口。复用现有测试，不新建runner、不碎片化正式构建。

### 2026-10-21 本轮实施收口（取代上表“尚待确定”项）

- 集成源码基线已前进至 `8ece5a25a850ca5bf85a6ce91a0e6be30ab20edd`（包含独立TMX解析优化，不修改该功能）。当前生产仍为1.16.24；本节是编码事实，不是上线证明。
- UI-01 已确认裸`<template>`使资料区不可见，改真实div；标题派生仅TASK_CREATE分支，36字/资料处理规则在保存前生效，正文完整保存；DOM和保存回执定向测试已通过。
- UI-05 已冻结为四主阶段＋异常/历史入口。次级明确分“历史”“待核对”，分别沿用HISTORY/UNKNOWN查询、分页、独立服务端计数；不新增合并phase、不拼接分页、不制造总数。原型和规格已先行修正。
- UI-03 实际承办名优先现有名册对象、其次任务assignedAgentName；有指派ID但名册不可读时标“承办信息待核对”，不假称未点将。资料只展示真实附件数或原议事查看提示，正式成果复用原入口/权威批次，不新增写资料功能。
- UI-07 工作台PC/手机二级根面板统一单返回；原handler、self/hall detail归属和录音锁不变。非工作台独立桌面弹窗仍可关闭。
- UI-08 我的→使用帮助复用既有onboarding事件，传入触发元素以恢复焦点；不另造帮助系统。
- 此次不改API、Runtime、支付/多Agent合同、流式监听、取消/验收状态机。不以这些历史实现重启一轮开发。

## F0. 新增/修改模块的唯一职责

| 文件 | 方法/接口 | 实施内容 |
|---|---|---|
| 新增`src/composables/juyiting/hallTaskPresentation.js` | `projectHallTask({task, reviewContext, pendingOperation})` | 纯函数，输出phase/label/reason/tone/readOnly/actions；无网络/存储副作用 |
| 新增`src/composables/juyiting/useHallDeliveryReview.js` | `refresh/openConfirmation/confirmAcceptance/observeRevision/checkOriginal/resumeOriginal/dispose` | 唯一任务级验收/修改意图，复用API和身份清理；详情、议事、正式页共享实例 |
| 新增`src/composables/juyiting/hallDeliveryReviewIntent.js` | `validateContext/freezeReviewIntent/reviewBody/batchDigest/validateReceipt/read/write/settle` | 精确schema、版本、大整数、存储readback与同意图核对；不包含UI文案 |
| 新增`src/components/juyiting/HallDeliveryReviewDialog.vue` | props`context, frozenBatch, pending, error`；emits`confirm, preview, back` | 只展示固定批次与确认动作，不能自己发请求 |
| 修改`src/composables/juyiting/useHallBountyFinalization.js` | `validFinalizationReceipt/applyReceipt/resume` | 提交操作，不再等同任务完成；界面自动链只读查询，禁止mount/watch提交 |
| 修改`src/composables/useFormalDeliveries.js`与`src/components/deliveries/FormalDeliveryList.vue` | list/决定入口 | 保留既有正式历史读取；新UI验收/修改转共享review，不继续各自产生key+先decide后createRework |

实例归属：在`JuyiHall.vue`任务上下文创建review composable，通过props/emits向`BountyPanel`、`BountyDiscussionPanel`、`BountyAcceptancePanel`传递。切换当前task或身份销毁旧观察；不得让三个页面各持一个未决验收意图。弹层开关留组件内，不保存到全局业务Store。

## F1. 两入口与待点将（P01/P03/P04/P05）

### `src/components/world/JuyiHall.vue`

- 现有首页`createTask → runRequirementCreate(schemaVersion:2) → onCommitted`保留。`onCommitted`更新tasks/selectedTask后打开对应事项详情并开始只读推荐，不再另建保存页/默认先开点将册。必须在fence.isCurrent后跳转；return true前确保回执已被任务视图采用。
- 顶部“提出需求”改打开现有`formalDraft` frame（已经设置`initial-kind="TASK_CREATE"`）；`draft` frame保留供旧PRIVATE记录/历史入口，不改所有draft默认类型。
- `HallDraftEditor @open-task`与首页onCommitted共用具名`openPendingTaskDetail(task)`（新增本地函数）：校验task.id、更新选中、进入tasks详情；不自动指派/发送。
- `createTask`现有funded/原草稿未决/普通创建未决互斥继续保留；程序跳转只用真实taskId，禁止“当前最后一项”索引。
- 确认承办继续调用既有`useHallPointAndStart.start({task,agent})`，保留显式ID/requirementRevision/taskVersion、costConsent、controlled bridge；不得改成首页选Agent。

### `src/components/juyiting/HallDraftEditor.vue`

- `isTaskCreate`时不显示承办Agent和outputMime授权控件；按钮“保存草稿 / 开始办事”。保留form标题/正文/资料固定版本、编辑后保存、错误与原操作核对。
- 新增`startFormalTask()`：先persist当前编辑稿并等待revision回读，再提交TASK_CREATE；不走私人授权确认页；仅当该分支的实际契约允许以“开始办事”确认创建时传创建确认，不把它用于付费执行授权。
- 回执必须`ref.sourceType=TASK`、execution=null、task存在，随后`loadFormalTask→emit('open-task',task)`；读取失败显示“已保存，正在核对”并查询原TASK，不重复submit。
- 保存草稿不提交；关闭不丢已保存事实。私人CREATE/REVISION/TASK_ACTION原逻辑单独保留，不因移除新正式确认页而扩大旧分支授权。

### `src/components/juyiting/BountyPanel.vue`

- 删除`simpleMatterStatus`字面量表与“有assignee就已受理”的兜底，使用F2投影；`modalTask/selectedAssigneeIds/openTask/back`等已有状态继续使用。
- `preferredAgents/assignableRecommendedAgents/selectedOperableAgent`复用；待点将详情展示推荐理由、候选卡、“另选承办Agent”展开同区列表，选择不发请求；主按钮“确认承办，进入议事”。
- 进行中只保留主要“继续议事”；待验收“查看成果并验收 / 继续议事”；完成“查看成果 / 查看议事记录”；终态取消资格仍由实际allowedActions/已有资格函数决定。
- 推荐失败只重试推荐；确认失败留同任务；版本改变重读候选，不重新创建。手机名册详情返回名册保留过滤/滚动，再返回事项。

## F2. 状态与计数（P01/P02/P04/P06/P14）

`projectHallTask`返回结构固定：

```js
{ phase: 'PENDING_ASSIGNMENT', label: '待点将', tone: 'neutral',
  reason: null, readOnly: false, actions: [], rawStatus: 'open', needsReconcile: false }
```

- root有效状态按后端B6映射；不存在`claimed/queued`根枚举的兼容猜测。队列和pendingQuestion只是reason。
- 没有reviewContext时可以显示根reviewing→待验收的只读标签，但accept不可用；context读取失败标明成果未核对。根/交付同快照矛盾时phase=UNKNOWN并冻结写入。
- 未决operation覆盖冲突操作能力而非改根阶段；401/403清除受限事实，未知status显示核对原因。completed/cancelled/failed/archived不允许发送/修改；个人mark不覆盖root。
- 修改`src/constants/juyiting.js`：主筛选四项，历史及异常次级入口；旧taskStatusText/taskStateClass委托统一投影或明确只作raw技术状态，不再独立维护用户文案。
- 修改`src/composables/juyiting/useHallData.js`：`taskStatusFilter`切为phase语义；`loadTasks/searchTasks`传phase；`loadTaskStatusCounts/taskStatusCount`读取新phaseCounts与rawStatusCounts，禁止从当前30条求总数。查询keyword/ability与计数完全相同，identity/筛选变更时epoch隔离旧响应。
- 修改`HallOverview.vue`及`JuyiHall.vue`首页卡片、`BountyPanel`列表/详情和消息聚合显示处，共用同一投影。后端phase计数未切换前不能把两个raw状态拼成不完整总数。

### F2.1 概览 TASK phase 接纳（2026-10-19候选）

`HallReadWire.ItemSummary.phase`由服务端显式给出，TASK六阶段与事项搜索/计数共用分类器。`useHallOverview.validItem`必须确认字段合法且与共享投影一致；缺失、未知取值、状态矛盾只隔离TASK partition，不把其他来源一起清空。不按字符串reviewing自行拼一个待验收权限。UNKNOWN即使返回了旧review标记也不得接纳验收；操作文案为“核对事项”。只有明确PENDING_ACCEPTANCE且完整reviewReady才允许review元数据；具体写权限仍以用户打开后读回的review-context为准。正式schema关闭时非终态可显示UNKNOWN，不因此查询不存在的表。对应真实MySQL/正式Flow证据见本次verification；不是生产已部署声明。

## F3. 提交、展示和验收（P06/P19）

### `src/components/juyiting/BountyExecutionOutputs.vue`

删除`finalizationCompleted = state==='COMPLETED'`推导事项完成的逻辑；`@task-completed`只能来自review COMMITTED/ACCEPT且核对根completed。`finalizeSelected`不再绑定“确认验收”。

组件接收新增props：`reviewContext, reviewState, canRevise`；事件：`preview-artifact, reconcile-review`；议事顶部`review-delivery`由BountyDiscussionPanel负责，不从成果卡发出。`acceptance`可逐步在本次切换内统一为真实context能力，不再以独立成果页面boolean决定授权；切换完成移除旧双语义。

- `allItems`仍用于普通消息/附件预览，`deliveryProjection`以reviewContext.currentDelivery与固定source映射生成；`bountyOutputCatalog`原REPLACE/来源校验继续保留，不前端编造正式交付。
- 议事顶部只有一个“查看并验收”图标，消息区与RESULT卡均无验收按钮。确认弹窗展示本批RESULT数、冻结整个batch；隐藏manifest卡不缩小验收集合。
- 未出现对应消息的当前话头插入一张引用该权威批次的紧凑卡，不复制消息，不另设固定待验收横条。普通卡不附验收。
- 成果卡去下载/保存到工作空间；媒体预览内部下载、资料详情下载、文字片段保存仍保留。移除“引用修改”入口；修改统一通过原议事输入，多成果目标不明确时在对话中澄清。
- 完成态优先最终成果；读取失败显示error，空态只在确认无数据后显示。不同时输出“验收完成/结果完成后显示”。

### `BountyDiscussionPanel.vue` / `BountyAcceptancePanel.vue`

正式议事和独立页均接任务级reviewContext，保留`TaskSkillCapabilities`、typed outcome和请求恢复。独立页`useHallBountyAcceptance`只负责定位/读取原来源，不唯一化为“最新话头”。正式历史不需要聊天索引存在才可展示；无唯一话头时仍可验收固定交付，不能随便选择最新会话。

`src/components/juyiting/discussionPanelContract.js`添加新props/events并在父壳接收；私聊/公共组件不传正式reviewContext，不出现验收按钮。

### `useHallDeliveryReview`状态流程

```text
refresh(context GET) → ready
openConfirmation(delivery) → freeze完整batch → dialogOpen       [无POST]
confirmAcceptance → persist intent/readback → POST review ACCEPT
  COMMITTED → GET root+context → 刷新列表/首页/详情 → 完成只读
  409/403 → 显示真实冲突/撤权；不换批次继续
  网络/5xx/回执校验失败 → UNKNOWN → checkOriginal(GET)
继续议事 → 聚焦原输入，用户直接描述修改对象和要求         [无POST]
sendDiscussion(content, selectors, optionalReference) → 原typed POST一次
  Agent提出修改意图 → 后端持久review operation → 既有request接续（前端不二次POST）
  COMMITTED(requestId) → attach确定性子request/SSE，不再send一遍正文
```

不能在watch(state)或mount执行POST。原intent字段：`scopeFingerprint, taskId, key, body, operationId, receiptVersion`；key不进入URL。存储prefix`cyf.hall.delivery-review.v1`，scope+task隔离；生成key前校验旧槽，写后readback失败不POST。刷新恢复先GET；显式resume才允许同key/body重送，服务器同key异体409。

任务切换/销毁AbortController＋epoch；仅取消客户端观察，保留原账号原操作恢复槽。当前confirmed批次被别设备修改时关闭确认并提示重新核对，不能偷偷替换弹窗内集合。

## F4. 输入发送与正式返工

改动`src/composables/juyiting/useHallTypedDeliberation.js`发送入口及父`JuyiHall.vue`发送分派：

1. 所有议事正文发送一次现有DISCUSSION/CLARIFICATION_REPLY，保留parentOutcome/pendingQuestion和generation；前端不得按关键词分类或自行POST REQUEST_CHANGES。
2. 成果卡移除“引用修改”及其创建chip的入口；发送不依赖chip。用户直接说明修改对象和要求，Agent基于当前批次理解；多成果指代不清时在同议事澄清。
3. 后端从已持久用户消息构造意图上下文，Agent输出结构化提议；普通提问维持待验收，含糊表达在原议事澄清。前端只呈现服务端返回的阶段/操作回执，不提前置进行中。
4. 后端正式受理修改后显示内联消息“已开始按你的要求修改”；沿reviewProgress关联的子request/SSE接续（原父request不重开），不重复send正文。失败/UNKNOWN核对原请求及关联review operation，禁止换key重发。
5. 自然语言“可以/不错”不代表验收；ACCEPT只能来自用户显式验收按钮及确认。引用和澄清均不新增弹窗或主状态。
6. 原正式文件返工入口进入同一原议事并可预填成果名称，不再要求“按此修改”按钮。独立工作空间TASK专用执行能力保持不变。

## F5. 全屏、导航、主题（19页）

| 文件/区域 | 精确改法 | 禁止做法 |
|---|---|---|
| `JuyiHall.vue` floating-panel/panel-overlay与`ChatPanel.vue` | 仅chat/private的容器加语义class，全可视区域grid三行：auto minmax(0,1fr) auto；`min-height:0`、`min-width:0`，消息区overflow:auto，外层禁止双滚动 | 把所有二级弹层全屏；直接全局覆盖floating-panel |
| `ChatPanel.vue`/`AgentPanel.vue`/`BountyPanel.vue`及各二级页头 | `hasBack`时仅返回，无返回独立弹窗才标准close；复用现有SVG图标、aria-label/title，焦点返回触发者 | 用字符X/×拼新图标；删除附件移除或子区关闭 |
| `src/styles/theme.less`及工作台作用域 | 使用现有--hall-*；主#923f30/hover#793326、暖白#fffefa、正文#242e2b；同义旧--work-*不再扩第三套 | 覆盖地图/阅读主题；把历史snapshot CSS整体复制 |
| `HallConversationHistory.vue` | 当前话头列表选中/加载/分页/删除中统一token，失败不显示旧成功；删除确认含标题 | 假空态代替生产记录；删除话头连带删交付 |
| `HallVoiceControls.vue`/`HallChatComposer.vue` | 文字/录音/转写占同输入主体，取消还原原草稿；转写可编辑但不自动发；附件条独立限高 | 录音区追加在输入框下面无限撑高；把示例波形当真实权限/识别成功 |
| `HallMessageMedia.vue` | 公共媒体卡操作布局class，次操作左/主右，gap4/8、14px字、44px触控，320允许换行 | 挤小触控区域；移除资料详情的下载 |

全屏使用现有可视视口/安全区机制并以100dvh为布局基准，不另造全站键盘hook；消息底部滚动只在用户近底部时跟随，翻历史时新流不强制跳底。弹窗焦点限制/Escape最上层退回，不能误关整个议事。

## F6. 资料选择与预览（C08/C09、P09/P10）

改`src/components/juyiting/HallMaterialPicker.vue`的`pickerFileId/pickerVersion/materialPreview/draftMaterials`及`previewQuickMaterial/confirmQuickMaterials`，并将`HallDraftEditor`内重复选材呈现收敛到同一组件（保留接口映射，不复制第二套CSS）。

- 新本地state`mobilePreviewOpen=false`；视口为PC时选择并固定version后自动preview，按钮不渲染；手机同一按钮`预览/收起预览`始终可见、aria-expanded及aria-controls对应预览区域。
- 选择区正文grid：PC列表+预览，各自min-height:0/overflow:auto；footer为auto，暂选清单为可展开限高区。移动显示列表或预览而非上下各占无限高度；20项/长文件名样例不会挤掉列表。
- 手机顶部返回：预览开→收起并恢复文件行焦点；预览关→取消弹层。取消丢弃temporary selection，不改父model；完成一次emit固定版本集合。
- 图片object-fit:contain/max-inline-size:100%；文字/PDF/音频按现有播放器/文档组件，不用图片标签假展示PDF；保留页码/上一页/下一页/返回选材/选取当前资料。
- 选中文件后网络预览失败不清空已选，允许重读；file/version变更旧响应不回填；切PC/手机不清选择。独立预览关闭仍可用，下载为明确品牌按钮。
- P10新版本上传/版本下拉、回收/恢复沿既有workspace操作，不因示例禁用被删；已引用旧版本不随上传更新。

## F7. 逐页改动对照和允许保留

| 页面 | 文件定位（均复用现有） | 执行内容 |
|---|---|---|
| P01 home | HallOverview / JuyiHall | F1入口、F2最近事项 |
| P02 tasks | BountyPanel / useHallData | F2筛选计数、历史异常 |
| P03 create | HallDraftEditor / useHallDrafts | F1正式草稿 |
| P04 detail | BountyPanel | F1推荐、F3双入口 |
| P05 agents | AgentPanel | 现有PC分栏/手机详情、返回及固定主操作 |
| P06 chat | BountyDiscussionPanel / ChatPanel | F3–F6完整主线 |
| P07 private | ChatPanel及其私聊接线 | 共用样式，不共享TASK数据/验收 |
| P08 public | 既有公议入口/ChatPanel | 实际入口仍需实页证据，禁止新造入口 |
| P09 workspace | JuyiHall引入的PersonalWorkspace | 共用预览/返回、管理能力保留 |
| P10 file | `src/components/workspace/PersonalWorkspace.vue`内详情/preview区域 | F6版本/下载；不另建详情页 |
| P11 mine | JuyiHall我的视图 | 导航/反馈，无调试索引 |
| P12 library | `src/components/juyiting/LibraryPanel.vue` | 返回/控件，阅读主题保留 |
| P13 reader | `src/components/juyiting/archive/ArchiveReader.vue`及LibraryPanel内阅读入口 | 页头去重、目录/手札/书签/引用不删 |
| P14 messages | JuyiHall的HallOverview messages-only聚合视图 | F2状态和合法跳转，无隐式已读 |
| P15 catalog | `src/components/juyiting/PersonaCatalogPanel.vue` | 页头/按钮，不做无Agent引导 |
| P16 map | JuyiHall地图壳 | 仅导航语义，不改地图引擎 |
| P17 help | HallOnboarding | 文案四步，末步明确“查看成果、确认验收”；不漏验收 |
| P18 account | 当前入口边界 | 只保留真实禁用，不编造账户表单 |
| P19 results | BountyAcceptancePanel / FormalDeliveryList | F3同源批次、历史和异常恢复 |

对共享复核页不发明产品新路径；现有真实import落点清单见`code-baseline.json`。没有证据的页面不以“全19页已统一”结项。源码级方案不声称当前原型已经补齐这些行为。


## F8. 源码推演补齐：活动任务与v5子执行

- `useHallData.loadTasks`当前会因任务不在30条列表或请求失败清空selectedTask。改为列表选择与activeTaskById独立；筛选/计数刷新不能撤销正在议事的任务，权限撤销按任务GET真实403/404处理，账号切换清理。
- `hallTypedDeliberation.js` strict parser/`useHallTypedDeliberation.js`同步v5 REVISION_REQUEST和独立reviewProgress，字段见source-design-review.md §3；不能塞入只支持EXECUTE的v4 actionProgress。父final完成后仍观察子catalog/SSE；同用户消息只显示一次，内部子请求不渲染为新用户消息。
- 接收原始typed POST回执不显示“已开始修改”，后端COMMITTED修改决定才切进行中。普通问答pending/澄清不改变任务待验收；验收按钮依据服务端资格，不能被父request completed误驱动。
- 测试列表不含当前任务、网络失败、批次被其他设备决定、子事件先后乱序、reload、撤权和跨账号，不只测理想点击流。

## F9. 实页/原型对照增补（2026-10-18，待实施）

[page-prototype-recheck.md](page-prototype-recheck.md) U01–U10是C00前置清单。独立成果页的`renderFormalResults`不能直连`finish`，应共用`reviewAcceptance`；产品`BountyAcceptancePanel`与议事`FormalDeliveryList`使用同一批次ID/版本/资格及操作回执，而非分别缓存一份finalDraft。`renderChat`的验收按钮置顶部现有事项操作栏，不放消息区、不新增固定操作行；弹窗标明总项数并展示全批成果，文件内只保留预览。每次渲染先清理旧入口，资格不满足时不留残余按钮。

`BountyDiscussionPanel`任务技能条保留；`BountyPanel`/`useHallData`保留异常和归档入口；`HallMaterialPicker`保留PDF分页；`PersonalWorkspace`新版本前置选择/失败不丢旧引用；`HallOverview`消息聚合不得退化成当前选中事项；`PersonaCatalogPanel`不硬编码两个人；`HallOnboarding`明确最后验收步骤。源原型落点及状态样例详见U01–U10。

先用同一fixture对照六个事项相关页，覆盖待验收/已完成/异常和多成果；加载与失败不混为无数据。未核实的公议/账户不能填造实现或通过记录。

## 2026-10-18 原型补缺已落地

[原型修正与复查](prototype-fix-recheck.md)记录U01–U10在现原型中的实现及精确输入检查。前节“待补原型”是实页核对时结论，本轮已补离线表达；产品前后端/Runtime实现、生产状态不一致及V01–V03仍未完成，不把原型通过作为C01–C09完成证据。


### 2026-10-18 顶部验收图标样式（最新）

顶部“查看并验收”采用与刷新/话头操作一致的线性清单勾选图标，替代红底文字按钮：44×44px触控区域、20px图标、透明背景、正文色，hover浅底、键盘focus可见轮廓，title及aria-label为“查看并验收”。替代此前88px文字按钮规格；仅更换入口样式，原资格、全批查看、确认验收及异常核对不变，不能点击图标就直接完成事项。产品尚未实施。

## F8. 2026-10-18 布局收敛：逐文件接线与风险控制

本节及已修正F3为当前实施规格，不执行历史“末卡验收/引用修改/统计行”。本轮读取本地Web `6fbdb6618b1132316a95db87cca9402de83138e8`；未fetch、未重新登录生产，实际部署结论仍沿原证据。

| 既有文件/落点 | 目标实现（尚未编码） | 回归要求 |
| --- | --- | --- |
| `BountyPanel.vue` `task-status-tabs` | 保留原overflow-x:auto；显式nowrap，按钮flex-shrink:0、44px触控，四阶段及异常/历史同排；不新增统计行；计数读取失败/加载提示不可当统计行删除 | 键盘焦点能滚入视口，320/390/520/523/1440，所有筛选可达，未知计数不伪装0 |
| `ChatPanel.vue` `toolbar-actions` | 新增具名`matter-actions` slot，放在现有操作之后；统一含slot按钮的44px盒/20pxSVG/1.8线宽。scoped样式用限定slot作用域的`:deep()`或共享class契约，不能假设父scoped选择器能命中slot内部。取消能力由durableCancelTarget派生后传入输入区，不再渲染工具栏取消× | 四常规操作等尺寸；停止与发送同位切换，见下文2026-10-19补充；极窄屏不另起固定状态行 |
| `BountyDiscussionPanel.vue` | 从任务级review实例取得只读展示上下文，经`#matter-actions`提供唯一验收图标，`review-delivery`事件向JuyiHall传递；ChatPanel不读取交付/执行网络请求。显式声明review相关props，chatProps解构时排除，避免传成DOM属性 | `discussionPanelContract.js`声明review事件/props，父壳显式连接；private/public不传slot；录音锁、操作未决及服务端资格统一决定可用性，点击和确认阶段再次核验 |
| `BountyExecutionOutputs.vue` | 只展示消息/成果/预览，不放验收或quote-revision操作；当前话头无交付消息时保留权威批次引用展示 | 不能依赖最后消息或当前话头决定批次；P19独立页共用同一冻结批次确认 |
| `ChatPanel.vue` `HallChatComposer` | 新增显式`matterReadOnly`展示prop，仅bounty采用投影后的完成/取消/归档只读；普通pending/unknown不是终态。隐藏composer而不清空父级draft。关闭已打开选材/录音面板须走既有voice取消/资源清理，不只CSS隐藏 | 终态→活动事项恢复；语音流与定时器结束；草稿按身份/事项/话头隔离。现有serverTaskCompleted仅判completed，需扩展，不能直接以任意readonly禁用私聊 |
| `HallChatComposer.vue` `resizeTextarea` | 正式紧凑模式新增`compact` prop（默认false，仅正式议事传入）；该分支height=44px并内部滚动，非compact保留现有Math.min(scrollHeight,132)。不能仅CSS强压而保留JS反复写132px | IME组合输入、Shift+Enter、多行粘贴、1200字、软键盘；字数并入工具栏；语音状态仍在输入区；不清空已选附件 |
| `HallChatComposer.vue` `targetChips` | 仅在单一固定承办对象且已有页头上下文时去掉重复标签；可移除/可选择的多Agent chip是功能，不能全局隐藏。多对象控制需先在原型补验证，再确定放入现有更多操作的位置 | 保留mention-agent/clear-target事件、既有权限和传话目标；不得因“视觉精简”扩大或改变接收人 |

顶部验收图标为清单勾选（不是已经验收成功标记），透明底/正文色，hover浅底，focus轮廓，title/aria-label“查看并验收”。只打开复核弹窗，不触发accept；结果数量、文件名和版本在弹窗完整呈现。ESC/取消返还触发点焦点；若因状态变化入口消失，焦点落回事项工具栏的可用操作，不聚焦已移除DOM。

### 原型/产品资源边界

离线原型四项联动资源使用内容摘要参数，修改后更新index.html；验证SVG path实际非空且可绘制，不只断言存在svg。产品走既有Vite/Flow哈希资源机制，不照搬原型脚本、手动?v=或HTML快照；资源更新不得以清空localStorage来修图标。


### 2026-10-19 停止本轮回复接线补充（目标设计，产品未实现）

- `ChatPanel.vue`删除旧工具栏取消按钮；保留`cancel-deliberation`事件和durableCancelTarget资格判断，将目标、提交中/未知/错误以显式props传给`HallChatComposer.vue`。不要以isLoading单独推断可取消，也不能用普通发送disabled逻辑禁用有效停止按钮。
- `HallChatComposer.vue`在发送位置切换发送/停止/核对按钮。停止和核对均type=button，通过独立事件上抛，不能触发form submit；Enter发送需排除busy/IME，不把textarea Enter解释成取消。样式、尺寸及文案遵循最新原型规格。
- `useHallConversation.js`保留既有turn版本校验/请求域allPending与生命周期guard。新增按requestId绑定的cancel操作状态与inflight去重；提交成功不直接展示停止成功，读回CANCELLED才恢复。FAILED/已完成竞态如实呈现；409读取权威版本后再决定，不盲重试；网络未知只读原请求。取消失败不得仅log.warn，需要向输入区返回可见错误。多目标结果未全终态时继续等待，不能把一条取消当作全轮成功。
- 取消回执只更新对应轮；旧SSE/计时器不得把已取消轮复活或覆盖新一轮。保留既有身份/ACL、锁、事务和请求恢复契约，接口标准仍为api/docs/interface-standard.md v1.2。
- 回归：三个议事入口、单/多turn、受理未明、停止成功/明确失败/未知读回、完成竞态、双击/键盘/切换身份话头、刷新后恢复、迟到消息与继续发送；保留草稿、资料与已完成成果。无新增事项状态。
- 原型离线演示不替代生产取消链路，真实吴用取消仍待实测。纯原型/规格更新不触发产品构建或部署。

### 2026-10-19 生产复核：停止入口不能只换图标（阻断项）

真实吴用事项459/会话1760458006504两次单turn取消均返回409 `CHAT_REQUEST_CONFLICT / Turn state version changed`，随后自然完成；不是取消成功。详见evidence/reply-stop-live-20261019。两次同类失败后停止发送测试请求，不以完成态冒充CANCELLED。

本地源码核对Web `6fbdb6618b1132316a95db87cca9402de83138e8`、API `3a960261ffad6e12d6e412df62eeac953b0d8f64`（非生产安装版本证明）：
1. `ChatDeliberationMapper.acceptDelta`每个delta递增state_version；`ChatDeliberationService.acceptDelta/persistEvent`构建事件时未在通用wire中带turn state/stateVersion。需沿发布/重放封装再核对最终wire，不能假设通用eventVersion就是turn版本。
2. `hallDeliberationState.reduceDeliberationEvent`仅在事件携带stateVersion时更新版本；缺少版本的STREAMING patch不能保证满足单turn取消前置。必须验证完整POST/GET/SSE版本一致，而不是仅修按钮文案。
3. `useHallConversation.cancelDeliberation`捕获错误后仅log.warn/false，缺少可见错误及409读回路径；同/较旧版本的终态回执提前return false也须按幂等终态处理。绝不删ACL/版本校验或默认扩大allPending来让测试通过。

补充开发动作/验收：
- 先保留原请求/turn及取消意图；409只读权威原请求。若已完成，保留回复并提示无需停止；若CANCELLED，展示真实停止；若仍pending，刷新正确版本，允许用户显式重试；网络未知亦只读，不自动循环POST。
- 对持续delta期间stateVersion频繁变化的竞态，不承诺“读回再POST必成功”。接口Owner须核定取消命令并发语义与SSE版本闭包；沿最新统一契约收敛，不增加兼容双轨。尚未核定前列为停止成功验收阻断项。
- 定向集成回归：DISPATCHED→STREAMING途中取消、多个delta期间取消、409后完成/仍pending、终态幂等、跨请求迟到回执、多turn部分完成。最终须生产真实观察CANCELLED并成功发送下一轮，不能只验202/按钮消失。

### 2026-10-19 修复候选落实（未部署）

已在useHallConversation落地请求级取消去重、会话/身份/请求结果隔离、409权威读回与可见提示、未知结果后续只读核对、终态幂等回执，以及有活动发送会话时读回请求终态释放发送锁。后端回话delta/final/recovery/cancel事件携带精确turn state/stateVersion，取消/最终回复先更新内存投影再生成事件，避免事件引用旧版本；保留严格expectedStateVersion校验。并发窗口仍可合法409，由明确读回/人工重试收口，不无限重发。此候选只修链路与错误反馈，发送位置停止图标接线仍按已确认原型另行实施，不把本轮代码当作全部界面改造。

### 2026-10-19 停止链路修复验证进度（非上线）

后端`5aa8efc2462cd0dc1dce531bdbfccaa5cae390c6`（Flow5260799/155）、前端`7b0d2be8feb34a366403d7d728a91be625a42166`（Flow4403172/227）正式验证通过并以受测提交集成develop。后端2397次执行：2302通过、95跳过；前端3049通过、2pending。修复权威turn版本传播、409/未知只读核对、重复取消及终态发送锁恢复，不改变事项状态、不降低并发版本校验。

详细证据与失败归因见[停止链路修复核验](../evidence/reply-stop-fix-20261019/verification.md)。临时流水线配置已恢复并readback；**未部署生产**。此处只更新已核验实现范围：生产仍待吴用真实停止→CANCELLED→下一轮发送回归；停止图标输入区接线、其他页面优化与整体验收未完成。制品上传成功不等于独立下载校验或上线完成。

### 输入区停止接线与刷新恢复（2026-10-19）

- `HallChatComposer`接收`durableCancelTarget`和只读`replyCancellationState`，停止入口独立`type=button`，不走表单发送；`ChatPanel`移除工具栏取消×并转发精确target，三个议事wrapper共用契约，`JuyiHall`三个入口均接线。不得复用事项撤销的`cancellationState`（不同功能）。
- 停止/发送均44×44，SVG20×20/1.8线宽；停止暖灰底。inFlight禁用；unknown保留原target并显示“核对停止结果”，不会因后来的多turn目标扩大原操作。停止失败为alert；同话头确认结束后恢复textarea焦点，不跨话头/身份夺焦点。
- `useHallConversation`使用响应式请求级job；浏览器sessionStorage记录按已水合identityScope+conversationId+generation+requestId+revision隔离。标记在取消POST前写入；未知/切换中断后保留；确认终态或明确拒绝清除。刷新标记只能令UI进入只读核对路径，不能触发POST。只存target，不存认证信息/回复/服务端版本；存储不可用退化到当前页内存，不宣称跨刷新保证。
- 当前候选Web`f9e04cbcd70d2678dd3097ffe9cdea3d7b10fbd9`；正式结果见本轮核验记录，原先“输入区尚未接线”仅为前一阶段基线，不能继续作为此候选源码结论；生产是否上线单独核验。


### 2026-10-19 停止回复专项线上核验补充
API1.16.9（5aa8efc246，Flow5260799/156）与Web1.16.10（bca42d2ea6，Flow4403172/230）已版本化发布并核验同Run制品/安装摘要；浏览器16个已加载资源匹配。吴用密议停止（409权威读回→显式重试→CANCELLED）及下一轮发送通过。此结论仅覆盖停止专项，不覆盖全部原型优化。
正式事项467的两个后续问题均返回“收到。”且界面未展示对应用户消息，根因未定位；正式议事停止/完整验收仍未闭环。另记录长流DELTA_GAP_EXPECTED_318_GOT_319独立问题，停止成功不表示序列问题已修。不得将整体方案标记全部验收通过。
完整证据及下一条源码核对入口：`specs/juyiting-ui-baseline-20261006/evidence/reply-stop-release-20261019/verification.md`（项目根目录相对路径）。此前未发布说明为历史基线，本节仅更新上述专项状态。


### 2026-10-19 发布后异常修正进度
正式议事回执接入改以chatContext的事项和唯一承办目标为准，不再使用selectedAgent/selectedTask作为议事主体。真实入口会清空selectedAgent，原先会提前拒绝回执导致用户消息不刷新。保持scope/身份/代次/receipt校验和目标漂移拒绝；已补无选中好汉、浏览其他事项及迟到响应回归。候选59ba8a8，175项定向诊断通过；Flow231未取得执行证据，尚未上线。
证据与源码基线：`../evidence/reply-followup-diagnosis-20261019/verification.md`。


### 2026-10-19 最新正式验证状态（13:01 CST）
Web59ba8a8 / Flow4403172/232 SUCCESS（3054通过、2pending，构建/扫描成功）。API cd2146f408e692fc58424390e89a40d2f10eb7d2 / tree b757d4cf1b4d3c1b864a2be47106ba0e0b734d56 / Flow5260799/161 SUCCESS（2420项中2325通过、95跳过、0失败/错误；分层检查及fresh bootJar成功）。此前Run159的5项失败已由Run160错误回执定位：旧normalizer误要求requestId/messageId相等，注册被拒绝；已修正两种身份的混用，并覆盖17项normalizer、1项command wire和5组分片回归。不改ACL、运行时证明或序号连续性，不通过改相同ID回避问题。
源码已集成develop，未部署；制品仅有Flow元数据，尚未独立下载验包。Runtime重复回复“收到。”及完整生产议事/验收闭环仍待解决，不标整体方案完成。本次不改变页面/交互，无需另改原型。完整证据：specs/juyiting-ui-baseline-20261006/evidence/reply-followup-diagnosis-20261019/verification.md（项目根相对路径）。

## 2026-10-19 发布后补核：同代接纳不能自失效（待实现）

核对源码Web `f112b0b2044032d34d0f5a39251f40bbb1b5cbee`（Flow4403172/233已上线）。本节修正前述“已接纳回执即可刷新USER”的实现假设，不改变原型交互：同一议事自然发送，服务端保存后显示本人消息，不新增按钮/分支。原型规格及页面已要求这一行为；不伪造本地已持久化消息。

**已发现缺口**：JuyiHall.vue的followupContextGeneration同步watch直接取activeRequest.conversationGeneration。历史会话的generation已由权威指派投影/目录给出，但activeRequest为空；接纳同generation request时applyRequestView触发undefined→1，invalidateFollowupContext使onAccepted的isCurrent失效，useHallConversation不再加载正文。生产task467复现消息已保存不显示；真实composable+真实页面watch的本地诊断同样失败。证据见`../evidence/followup-release-20261019/verification.md`（相对本优化目录）。

实施要求：
1. 在`tests/juyiting-typed-deliberation-page-routing.test.js`补真实同步watch参与的红绿回归，不能只传固定`isCurrent:()=>true`；覆盖activeRequest初始为空、已存在同代请求、首轮快速完成和历史浏览时selectedAgent为空。
2. 在`JuyiHall.vue`区分“安全主体/真实会话代次改变”与“同一代次的request投影补齐”。明确以已校验的当前会话权威generation比较；unknown→已在本次context确认的同值不是新主体。先获得权威代次再发送；真实不同代次、用户/授权、任务/指派、目标Agent或会话切换仍须立即失效。不直接删除watch或关闭isCurrent检查。
3. 两个同步watch需一起处理：一个失效followup，一个重置目录并recover。禁止简单改成依赖会被reset清空的catalog计算值，造成重置→代次空→再次重置的循环；不可用缓存的旧身份代次填补新会话。对权威代次来源、作用域及reset顺序写出单一职责，再实现。
4. `useHallConversation.js`继续严格校验receipt/request/task/target/generation和版本单调性，仅当仍为当前作用域时读取服务端正文。若读取失败明确保留已接纳状态及可恢复提示，不再次POST，不把发送成功伪装成未保存，也不插入假USER持久化记录。
5. 回归：同代接纳只产生一次后续正文加载；GET等待中切身份/任务/目标/代次不得显示旧消息；迟到低版本不回退；目录reset不递归；多个轮次不会重复/漏USER；断网恢复不重复发送。真实浏览器再核对USER、ASSISTANT同时保留及停止/重载，正式验证覆盖精确候选Flow。

当前仅补设计与失败复现，尚未修正产品源码；本次上线不以单测数量充当该闭环验收。模型重复回复问题按用户要求暂停，但不是这一前端缺口的豁免依据。

## F-GUARD. 响应式监听与异步回执安全规则

规则日期：2026-10-19。核对基线：Web `f112b0b2044032d34d0f5a39251f40bbb1b5cbee`；覆盖聚义厅页面组合、请求目录、会话内容、流式事件与回执接纳。**以下为必须落实的设计/测试约束，不表示现有实现已符合。** 同代接纳自失效的失败证据见前节。本节是规则唯一正文；执行清单引用本节，不复制第二套定义。

### G01. 明确每个监听器的输入、职责和写入范围

新增/修改业务watch前，在对应模块详设列明：监听源、权威来源、触发条件、允许写入的状态、网络副作用、清理方式、受影响用例。检查所有会读到这些写入的watch/computed，而不是只测试新增函数。不是限制watch数量；不得用删除安全监听、改成定时刷新或把flush改成延迟来掩盖错误判定。

本次两个watch共同监听7类输入，一处失效操作、一处重置目录并恢复请求。二者属于同一上下文切换流程，应由一处统一判定“是否真正切换”并按顺序协调，不各自以投影字段变化决定切换；可保留职责不同的下游监听，但不得重复判定、相互重置。

### G02. 区分权威身份与展示投影

- 安全作用域：已认证用户/授权版本、当前实际会话ID与服务端generation、该会话绑定的事项和指派版本、实际目标Agent、影响路由的模式。按当前接口合同获取；这不是新增业务状态。
- 展示投影：当前request、消息列表、列表中浏览/选中的事项或Agent、加载标志、请求目录。展示对象补齐/替换、浏览其他事项不能独立充当真实会话切换信号；只有实际改变交互绑定的操作才能切换作用域。
- `conversationGeneration`是服务端会话代次，`followupContextGeneration`是前端操作失效计数，两者不可混用；request stateVersion/revision也不等于会话代次。确实影响本次请求前置条件的事项版本变化仍须重新核对，不把所有版本更新一概忽略。
- generation须通过既有规范化/校验函数比较，不做宽松字符串/数值强转；冲突不“选一个可用值”继续发送。

### G03. 明确初始化、补齐、切换与失去上下文的判定

| 事件 | 判定 | 处理 |
| --- | --- | --- |
| 尚未取得可信身份/会话代次 | 未就绪 | 只读恢复；不得以空值通配开始有副作用请求 |
| 当前request为空，权威上下文已确认generation=1；同作用域回执补齐1 | 同代投影补齐 | 不失效当前操作、不重置目录；继续正文同步 |
| 同作用域换成另一request，generation不变 | 同代新轮次 | 允许接纳新轮次；仍按各request/turn版本处理，不混合两个请求 |
| 权威generation从1变2，或真实身份/授权/会话/指派目标改变 | 真正切换 | 立即使旧操作失效，清理旧投影/订阅，再恢复新作用域 |
| 当前可信上下文被撤销、退出登录或离开会话 | 失去作用域 | 立即隔离旧异步结果，不用历史缓存补齐新作用域 |
| 同一次目录刷新暂时清空entries，但权威绑定未改变 | 加载过程 | 不把暂空当新代次；loading与身份分离，不清除仍有效的权威绑定 |
| 多个权威响应代次/目标冲突 | 待核对 | 阻止写入/接纳，按现有只读恢复路径核对；不自动降级或重复POST |

“空→有值”不是统一允许规则：只有同作用域、已确认的相同权威值补齐才可继续。真实切换后即使代次数值相同，也不能接纳旧作用域响应。

### G04. 接纳顺序与异步安全

每次操作固定其作用域快照及操作标识；每个await返回和提交可见投影前均检查仍有效。回执接纳顺序为：校验回执 → 只读权威request → 核对作用域/目标/版本 → 更新同代投影 → 读取/合并服务端消息。投影更新不得自行增加上下文失效计数。严格保留现有ACL、身份、请求归属及单调版本校验；同代不意味着任意request都可信。

加载和流事件可能交错；合并按服务端消息/请求/turn身份及版本去重，不以旧列表整体覆盖新流式消息。旧请求的异步清理不得解除新请求发送锁或删除新草稿。不要只在发送前检查一次身份，也不要移除提交后的安全检查。

### G05. 避免循环与重复副作用

不得让“监听目录派生generation→reset目录→派生generation变化”形成循环。明确作用域权威数据的持有者和失效入口；目录refresh/reset是消费者，不反向决定身份。真正切换时先失效旧操作，再清理、恢复新作用域；同一有效触发不重复启动相同恢复。不能依赖回调注册顺序、任意延时或无限重试得到正确性。

### G06. 流式事件、消息保存与只读恢复分工

Agent流式答复、用户消息保存回执、断线/刷新恢复是不同路径，共享同一作用域与版本规则。watch是状态响应，不是轮询；本次修复不新增定时刷新。确需网络重连/状态核对时沿用既有机制，记明启动/停止条件，组件卸载、退出登录或切会话时释放自身订阅/定时器；不停止其他页面/任务的连接。

服务端已接纳不等于页面已同步；正文读取失败保留原request身份并显示可恢复状态，只读核对，不重新发送同一业务请求。若有本地待发送展示，必须明确区分未确认/已确认，不能伪造已保存messageId。普通回答、流结束或请求COMPLETED不等于正式成果已提交或已验收。

### G07. 验证必须覆盖真实组合

纯函数/composable测试不足以验收此类修改。扩展既有page-routing测试，让真实页面watch参与、使用真实可变化的isCurrent；覆盖副作用顺序及网络调用计数。增加实际组件挂载/浏览器发送验证，保证模板所见USER与ASSISTANT都更新；测试替身不得屏蔽导致事故的状态变化。原型fixture、定向本地诊断、精确候选Flow和生产冒烟分别记录，不互相替代。

### G08. 可定位而不泄露数据

失效/忽略迟到回执时，在既有诊断机制记录明确原因（如身份切换、代次变化、目标变化、版本陈旧），以及必要的请求关联标识、前后代次和操作阶段。仅保留最小必要信息；不记录token、完整消息、附件或模型推理。区分“服务端未保存”“已保存未显示”“流未收到”“模型内容不符”，禁止以一次HTTP成功或测试总数替代业务断言。不为此扩建监控框架或新增无依据的性能门禁。

执行与证据要求见code-execution-checklist.md的G-REG矩阵。规则与测试必须随真实修改一起落实；当前只补规范，不代表已修复或再次上线。

### 2026-10-19 自然修改反馈接线
BountyTypedOutcomeCard在原消息内显示reviewProgress受理/拒绝/子请求进展，无新增操作按钮或主状态；BountyExecutionOutputs将修改QUEUED/子请求非终态纳入原有刷新条件。useHallTypedDeliberation在每轮只读刷新跟随已受理child，即使其旧投影为PENDING也再次读取；同轮visited去重并阻断循环，不新增watch/timer/POST。子请求完成不意味着已提交或已验收。原型场景revision-queued/revision-rejected/revision-running及规格同批更新。

### 2026-10-20 实际上线复验限制
已部署不等于详设全链路已实现。当前生产API189/Web246/Runtime8a9742a，真实流程发现交付提示更新、待验收上下文409、事项容器空白和重复只读重同步四项OPEN；详见 `../evidence/implementation-20261019/production-release-20261020.md`。修复需沿既有事件/作用域/幂等机制，不用新增全局轮询、放宽grant执行资格或移除身份fence掩盖问题。自然修改与最终用户验收尚未完成真实验证，保持未验收状态。

#### 2026-10-20 主流程缺口修复（候选38667d01，未标线上验收）
- LIVE03已实际复现：BountyPanel传完整task给taskStateClass/taskStatusText，而JuyiHall仍以字符串toLowerCase。改用既有projectHallTask统一投影，不改布局；挂载回归必须使用非空真实状态元数据，不能空数组掩盖类型错误。
- LIVE04实际断点记录：事件2629 typed_question_answered返回false，被SSE解析器判event_rejected，无游标推进而不断重放。该同会话合法投影提示即使不是activeRequest也须确认游标并只读重取，不修改活动执行授权；未知/跨会话事件仍不放宽。
- LIVE01增加同会话delivery_submission_completed持久提示→typed-outcome权威GET→submissionProgress状态/版本变化→既有delivery-review-context GET→原工具栏图标。不得以消息正文或提示事件本身作为验收权限。原型行为不变，规格已同步。
- 定向诊断173+87项通过；正式测试/业务验收单独记证据，不用本机结果替代Flow。

### 2026-10-20 剩余验收修复的源码约束
- `useHallConversation.syncDurablePresentation`仅以同turn权威CANCELLED/FAILED清理对应半截消息的streaming标志，保留内容，不把取消伪装为正常最终结果。
- `hallDeliberationState`同步推进stateVersion与lastDeltaSeq；取消提交二者配对快照。旧版本/冲突事件不得覆盖；后端仅允许纯delta推进的取消竞态，不取消其他轮次。
- `BountyDiscussionPanel.taskCompleted`由当前事项状态或**taskId精确匹配**的delivery-review-context COMPLETED派生；确认验收后即刻只读，不等列表副本刷新，不锁住切换后的其他事项。
- 刷新恢复历史时，`useHallConversation.appendHallEventMessage`拒绝非activeRequest的历史delta建立实时气泡；历史最终消息仍正常接纳。此为现有请求隔离的补齐，不新增订阅、轮询或写入。
- 上述停止/readonly已分别在Web250/251正式验证；历史delta补丁f184d9d的Flow252尚需回读，不以候选代码代替上线证据。精确结果收口在remaining-20261020/verification.md。

### 2026-10-20 11:06 CST：剩余项实施候选（基线f184d9d，未发布）
- `ChatPanel`正式事项复用`HallMaterialPicker`；从空目录也能选择固定版本，以REFERENCE逐项调用原`usePersonalWorkspaceTaskLinks.attach`，成功项移出待选，失败/未知项保留并走原写意图恢复。选择资料不发送消息、不启动执行；切换身份/事项/话头、事项终态或卸载时generation失效，禁止继续下一项或回填新作用域。
- `BountyDiscussionPanel`以同task权威COMPLETED收口旧回话状态、终止/恢复区和验收入口；`ChatPanel`收口另起话头、历史回答入口、待回复提示。历史问题保持“保留历史问题”，不得伪称已回答。`HallConversationHistory.readOnly`仅限制删除，不限制浏览/切换；确认弹窗期间转终态也拒绝删除事件。
- `useHallDeliveryReview.recoveryNeeded`仅在原intent、COMMITTED回执及同task同delivery的权威ACCEPTED版本全部闭合时隐藏恢复操作；不清除持久意图、不自动重放写入。UNKNOWN/冲突/缺少上下文继续显示。存储损坏而无intent时只显示错误，不显示无效“查询原验收”。
- 原型先更新；修复了历史停止场景初始化早于conversation声明的问题，恢复归一化移至renderChat。此为离线原型问题，不冒称生产问题。
- 定向结果：组件集成146项通过（含终态确认期间禁止删除、资料选择作用域与失败保留）；早先资料/写意图等8套94项通过，两组有重叠，不相加。原型97项文档检查通过；布局/生产功能和正式Flow尚待验证。

### 2026-10-20 11:32 CST：精确原会话当前轮恢复候选
- 修正只读历史导航：`continueBountyModification`允许completed回原会话，不放开cancelled继续办理；source.taskId与身份/分页/会话范围校验保留。只是导航，不调用点将、发送或执行。
- `useHallConversation.loadHallConversationContent`仅在正式议事且尚无权威activeRequest时，先读该精确conversation的完整`/requests`快照。使用既有catalogPage/mergeCatalogEntries验证taskId、conversationId、generation、after/through及重复request，最后ordinal才是本会话当前轮；不改变会话选择，不依靠第一条SSE事件选择回话。
- 快照读完前保持loading；失败不开放发送/停止或启动SSE。切换身份/事项/会话、卸载、并发新受理均作废旧读回。已受理bootstrap/typed receipt已固定exact request，跳过恢复读取，不改变首轮冻结合同。
- 仅快照内已知历史request的interaction.state_changed/chat_request_replay确认游标且不修改活动轮；旧delta不重建实时气泡，历史持久final照常展示。未知状态事件不扩大准入；无新增定时轮询。
- 224项定向回归通过，含分页、范围/边界冲突、切换期间晚到读回、真实SSE帧旧状态/旧delta隔离及取消精确checkpoint；正式Flow/实页仍待核对。receipt-adoption测试原先将GET一概mock成RequestView，现为新增的初始恢复路径提供真实空catalog fixture，不修改生产契约。

### 2026-10-20 11:56 CST 生产复核补充：传输失败与终态恢复

受测Web d349f0b3e77078def8e0f344d74d4ae8fff261ad / Flow254，仅以下范围已实测：完成事项回原议事只读、原会话恢复最新轮次并取消、正式资料固定版本绑定。新发现原生SSE HTTP2协议中断时，权威request读取已FINAL_PERSISTED而UI仍为已受理；刷新后恢复。此处为**未完成修复的验收缺口**，不是新功能授权：
- 现有原request只读恢复结果必须在同身份、task、conversation/generation、request/revision和turn约束下同步状态；旧轮/晚响应不能覆盖当前轮，版本不回退。
- 网络失败不等于执行失败；不能重发用户消息、重启执行或伪造成果。已知终态需要取得同会话持久最终消息，不能只消除spinner而遗失答复。
- 复用现有single-flight恢复/读取调度，不另开并行轮询或监听；HTTP2具体根因另需实际协议证据，不以增加定时器掩盖。
- 定向回归必须包含：恢复旧会话→新自然议事→SSE真实断流→原请求GET终态→最终消息恢复，以及并发切换身份/事项拒绝迟到读回。正式Flow与真实PC/移动确认之后才能关闭此项。
- 材料选择成功不等于所选Agent具备对应原生输入能力；本次吴用声明仅PNG，text/plain得到真实澄清，不通过扩展能力范围来冒充本次交付完成。

### 2026-10-20 Web255已发布实现：沿现有重连恢复持久终态
- 实现commit `f08e427f56f9172068b697eae13dcdbfd0076f9c`，tree `9ba5c9cc7e45828f3e251699c5d16b3acebd4d97`，版本1.16.23，正式Flow255：3125通过/2pending；366安装文件及公网入口、议事JS/CSS与同Run制品一致。生产业务验收仍独立核对。
- `scheduleHallEventReconnect`仍唯一重连计时器；重开流前复用`recoverUnknownRequest`单飞读取。真正终态（含子turn状态）且finalMessageId尚未渲染时读取原会话持久消息；历史加载使用`resumeEvents:false`，不竞争打开第二条流。原有`onRequestCatalogHint`读回typed-outcome，不新增观察者。
- `recoverUnknownRequest`校验已知requestId/revision/conversationId/generation及turn归属，拒绝版本倒退或将真正终态复活；UNKNOWN/RECOVERY_REQUIRED/PARTIAL仍按子turn判断，不能因聚合名误判已结束。未完成时保留半截输出。
- 异步所有阶段保留当前身份/作用域/活动request fence，旧回调只清理自身句柄；最终正文读取失败用“回话已结束，正文加载待重试”，不显示假成功、不重发POST、不新增请求。已渲染final避免后续重连重复读历史。
- 新增12项终态恢复/错误/竞争回归，定向218通过；原型97文档检查通过，均与正式Flow证据分开保存。

### F-DFX-PROJECTION（2026-10-20，本轮已实现并定向上线核验）
源码基线Web f08e427f56f9172068b697eae13dcdbfd0076f9c；只修当前快照、失败读恢复、精确成果缓存三项，不兼容历史协议。
1. useHallChatContext提供原会话TaskDTO刷新，单飞、同身份/话头/subject隔离、合法版本不倒退。JuyiHall继续发送与恢复先调用，再刷新assignment/catalog/typed；不以selectedTask替代conversationTask，不重置用户点名/草稿。
2. useHallConversation复用既有重连timer承接失败投影读取；只读失败保持dirty，成功且作用域/读取代次不变才清除；健康SSE不重建，既有focus/visibility恢复dirty。typed-outcome网络/格式失败必须返回真实失败，404普通CHAT不误判；无新监听、无自动POST。
3. previewReviewOutput精确匹配失败后最多刷新一次原outputs并重新校验scope/hash/version；预览操作序号隔离迟到点击，读取失败不回退旧成果。
回归：版本3→7恢复发送、慢读后身份/事项/话头切换、健康SSE+目录/typed读失败恢复、404、失败/成功竞争、旧非空成果缓存、刷新失败、预览切换。先定向检查，合为一次Web正式Flow及PC/移动实页验收；未有证据不标完成。

核验补充（2026-10-20 13:30 CST）：Web1.16.24 / 50107f38a757a5ce58d298965a953a353d7b48b1 / Flow257，3142通过2pending；三项定向修复上线。原474连续修订10月22→23→24日，事项版本7→9→11后仍可发送；受控GET传输失败解除后无刷新自动读取，旧非空缓存预览在点击时只刷新一次deliverables并精确打开23/24日成果。474、PC新477、移动新478均通过UI显式验收，服务端COMMITTED/COMPLETED/ACCEPTED。手机为390×844浏览器视口，不是物理设备；只覆盖纯文字主流程，不冒充媒体/多Agent/付费/所有页面验收。精确证据见remaining-20261020/web257-projection-dfx-verification.json。

## UI-03线上验收返回补漏（2026-10-21）

基线`0bda314`/Flow261/1.16.25。PC事项481、移动事项482的ACCEPT均COMMITTED/COMPLETED，手机多轮修改也提交成功；但返回详情仍可见reviewing旧快照。原因是loadTasks只从当前筛选页更新selectedTask，而完成事项已经离开筛选页；验收watch仅刷新列表，未刷新首页。修复只沿用同一loadTasks：当前选中ID不在列表或快照版本落后时GET原/tasks/{id}一次，用查询epoch/身份/选中ID/版本单调性隔离；验收调用附原taskId及最低taskVersion，拒收落后回执的详情。失败保留事项并显式提示，不以不在列表视为删除，不修改列表筛选、不新增轮询/写请求。验收成功同时递增已有hallReadRevision刷新首页。4条定向回归：过滤页之外完成同步、选项切换晚到响应、旧版本拒收、账号切换隔离。该补漏超出初次30分钟编码窗口，不能再称全部修复在00:18前完成。

### 2026-10-21 返回导航实测补漏

`useHallPointAndStart.checkOriginal(taskId, { attach: false })`用于选中事项快照监听的被动核对；保留精确原操作/TaskDTO、版本/身份校验，但不调用`onAdmitted`、不打开议事、不补写。默认显式核对、显式恢复、初次点将及准备观察仍可attach。`JuyiHall`选中事项version监听仅调用被动模式，避免验收后刷新或重新查看已完成事项时抢回议事。覆盖assigned/submitted/completed三种快照，验证0导航/0写及随后显式进入仍可用。原型`completed-background-read#detail`保持详情，不新增页面或业务状态。

线上TaskDTO/AgentTaskStatus确认待验收为`reviewing`，前述测试与校验的submitted应改为reviewing，不保留错拼状态兼容。原点将恢复提示仍保留，但ADMITTED只说明可由事项操作进入原议事，不声称正在自动导航。

### F-NAV：办事直达详情返回列表（2026-10-21 修正）

基线 Web `3fe5125e3c40eeeadf89e0b15e78e3902389a761`。生产只读复现：办事待点将卡片→事项详情→返回，列表0行且各计数为“—”；并非真实空数据。`openOverviewTask` 的 restore 路径刻意跳过 `loadPanelData`，而 `selectTask(null)` 原来只清理选中项。

修复限于 JuyiHall `selectTask`：清空前记录“有选中任务且当前为tasks”，关闭详情后调用已有 `loadTasks()`；重复清空、其他面板清空不发起额外查询。打开精准详情仍不刷新列表，返回时保留关键词/状态/能力条件，不新增watch或轮询。原useHallData负责加载、查询/计数错误、空态、迟到请求及身份代际保护，详情关闭前先清空选择，避免列表回执重开详情。PC和移动共用同一逻辑。

回归：实际挂载JuyiHall+BountyPanel，从未经加载的首页直达待点将详情，真实返回按钮触发一次查询并渲染卡片；保留筛选，重复清空不再请求。配套现有hall-data反例覆盖错误/计数/旧响应。本地定向证据不替代Flow及上线验收，发布结果单独记录。

### 2026-10-21 已有成果上下文与提交回执（开发中）
- 复用catalog/typed-outcome读取，不新增计时监听；EXECUTE子请求不调用CHAT typed-outcome。
- 当前契约v5完成值RESULT_COMMITTED；匹配父动作、精确子请求/step、assignment、target、scope与版本。多个独立成果显式选择；自然语言发送仅冻结parent引用，不自行生成outputs或提交状态。
- SUBMISSION_REQUEST投影展示“提交已有成果”；text仅操作说明；submissionProgress仍显示服务端PENDING/COMPLETED/FAILED，不以生成完成代替正式提交。SUBMIT关系作为同一成果链的无新增节点，不是文字成果。

#### 2026-10-21 18:31发布状态补充
上述已有成果关联/选择/提交回执实现已随Web1.16.34（19a322a4b3b51856f8c1235a73d3aac4d848b022）由Flow4403172/278发布；3186pass/2pending/0fail，同Run366安装文件及公网入口/JS/CSS一致。原型PC/390检查与正式组件测试通过；真实生产媒体业务闭环尚在独立测试495验证，不能据此声称所有场景验收完成。原事项480两个独立根不得默认选择最新或代用户确认。发布证据`/var/tmp/cyf-media-delivery-20261021/web-release/`；真实网络/截图位于同根production-browser目录。

#### 2026-10-21 19:01真实页面收口
Web仍1.16.34/19a322a（未因后端事务修复重复发布）；配合API1.16.22，独立495的已生成图片→自然提交→待验收→原UI确认→已完成已实际走通。PC/390均核对正式预览，真实验收POST仅移动模拟视口一次；原480只读3个独立根默认未选，未替用户选择。混合文媒、自然媒体修改重交和真机未做生产实链。非阻塞遗留：历史提交卡在已完成页面仍沿用“请查看并验收”提示，主状态与只读权限正确，留项不扩本轮发布。详见既有生产对齐发布文档19:01节。

### 2026-10-21 重入EXECUTE终态收敛（已发布Web1.16.36 / 9dbd132）

范围仅`useHallConversation`；不增加监听、轮询、业务事件或POST。496生产事件留证：`agent_message`携带requestId/parts，不携带CHAT turnId或turn stateVersion；`ChatBountyAssetProjector`同步落终态后发该事件。此前事件仅触发独立成果catalog更新，已恢复的activeRequest仍RUNNING；`retryHallConversation`仅重载历史且activeRequest存在时不重取catalog，故手动重取也不解忙。

- 已有bootstrap媒体提示分支统一覆盖从catalog恢复的EXECUTE：仅同conversation且requestId精确等于activeRequest、并有EXECUTE step的有效`agent_message/part.ready`，复用原single-flight `scheduleAuthoritativeRequestReadback`。首次执行与恢复路径共用一次调度；其他请求仍仅刷新独立投影，不接管当前回话。消息本身不能判完成。
- 原重取入口先`recoverUnknownRequest`核对已有当前请求，再重载历史；等待前捕获身份/范围guard与requestId，等待后核对二者，切换后的迟到操作不继续刷新。网络错误保留未核实状态；原GET不得触发重发/取消/生成。
- 继续使用原代际、修订、单调版本与终态不回退校验；原CHAT回执/流/停止不重写。
- 原`juyiting-restored-request.test.js`新增7项实际composable回归：当前媒体事件、历史事件隔离、手动重取、错代际、旧版本、网络错误、任务切换迟到。最初两条故障在修改前均因缺少GET失败；修正共享调度后与原bootstrap/SSE/会话回归合计140项定向通过。正式Flow与线上检查以发布记录为准，不用组件替身网络测试冒充新一轮生产模型执行。
- 原型沿用`projection-recovery`和“重取回话”，规格新增终态恢复约束，不改布局或文案；外部委托原型脏变更未纳入本候选。

- 发布收口（2026-10-21 20:58 +08:00）：首候选Flow280被原bootstrap重复GET回归阻断，未部署；共享原分支修正后Flow281 SUCCESS，3198pass/2pending/0fail。部署71553147 healthy，同Run366文件及公网入口/议事JS/CSS一致，恢复CI-only APPLIED。线上496完成态PC/移动模拟视口历史/重取/返回只读通过，未新增EXECUTE；终态进行中→完成的精确修复回归证据在正式测试，不冒充新一轮付费线上执行。回执：`/var/tmp/cyf-media-delivery-20261021/busy-recovery-release-r2/release-receipt.json`。
