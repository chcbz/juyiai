# 接外单最小闭环详设 D3.1

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：同平台外部Agent承办与正式成果验收。**

### 最小责任链
API管理公开接单范围、任务授权与验收；外部Runtime执行合同；Web明确用户选择。

公开候选→用户确认委派→原流程自动办理→固定成果选择→显式验收。

### 实施约束
不绑定某个好汉/Owner；外部私有技能/资料不泄露；不新增确认后再开始步骤，查看/下载不等于验收。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 2026-10-21。以本版替代D3及D2.1，不在旧文末尾继续叠加例外。接口统一遵循 `/home/isp/wsps/cyf/api/docs/interface-standard.md` 1.2，SHA-256 `7dc50a51b5c3faa2d5311dd0f749ed2000365c34febc3c3714ba2a945180548f`。本版记录当时的目标契约；后续限定范围实现/发布见acceptance.md，不再把早期“拟实现”当作今日状态。

## 1. 架构决策：扩大可承办范围，不新增外单流程

```text
原任务 → 统一候选 → 原确认委派入口
                   ↓
          统一解析任务主体和执行主体
                   ↓
       原assignment / grant / bootstrap outbox
                   ↓
       原议事 / Runtime执行 / 成果 / 验收
```

本人和他人Agent都走同一入口、同一编排、同一执行/结果协议。仅在选择资格的授权边界区分：本人目标按既有归属授权；他人目标额外检查同平台与接外单开关。下游只接收已验证的执行上下文，不各自按OWNED/EXTERNAL复制逻辑。

删除D2.1的外单专属提交接口、`initiationMode`、`EXPLICIT_INSTRUCTION`、`PREPARE_CONVERSATION`、独立delegation状态机和“先接单待指令”。复用现有bootstrap自动发送首轮，不另造一个延后启动编排。

## 2. 用户交互

1. 在本人Agent详情开启“允许其他用户委派任务”。说明：面向同平台所有用户；关闭不影响已接任务。切换不调用模型、不要求在线。
2. 沿原流程创建任务，在任务详情选择承办Agent。列表合并自己的和其他用户已开放的Agent；显示名称、所属用户、运行状态及现有推荐信息。首版不强制新增“我的/其他用户”筛选标签。
3. 在原确认区展示需求、当前任务资料范围、目标及所属用户；对所有目标使用统一说明：“确认后将任务内容和所列资料发送给该Agent开始办理；资料由该Agent运行环境及所使用的模型服务处理。”不新增独立确认页。
4. 点击确认后自动进入原办理链路；准备中、等待运行、执行中、失败等沿用原投影。离线/忙碌不拒绝委派，待可执行时恢复。提交成功不等于模型已运行。
5. 继续交流、成果、验收沿原任务页面。无需服务方手动接单，也不新增服务方查看客户任务正文的权限。

## 3. 最小数据变化

### 3.1 逐Agent接外单开关
新增一张按真实Agent绑定保存开关修订与原请求回执的轻量政策表，字段和唯一键固定见§9。每个绑定的最大revision是当前开关值：包含绑定身份键、`enabled`、`revision`及更新时间/操作者。无记录即关闭；重新绑定不继承旧绑定的开放状态。身份键包含现有注册表要求的tenant/client/owner/agent/binding，不以显示名作为键。

写入沿用项目幂等语义，回执直接保存在同一政策修订行，不另建回执表、政策状态机或通用操作平台。明确设置布尔值而不是“取反”；同key同payload返回原结果，同key异payload拒绝。超时保持结果未知，沿原key恢复；不能以随后读到的当前值冒充原写入回执。首次读取失败显示不可用，不当作默认关闭。

### 3.2 扩展既有assignment/grant，不新增外单订单或delegation表
保留任务owner；在既有承办授权事实中固定执行主体完整身份（tenant/client/owner/agent/binding）及接单时政策版本（本人目标为空）。已有字段能表达就复用，只补缺失字段。本人目标同样写完整执行主体，不让下游猜测owner。

既有assignment/grant版本就是授权代际，不再引入独立delegationId/revision。执行、outbox与成果通过既有稳定引用解析该授权事实；只有恢复或索引必须时才补充执行主体字段，不把完整上下文无条件复制到所有表。

初始输入继续冻结当前任务关联资料的fileId/version及原完整性摘要。用户确认即授权提交时当前任务关联资料；确认区的资料列表用于说明范围，不构成额外的客户端快照合同；本期不新增外单专用inputRefs协议或子集勾选器。以服务端接受确认委派时、原任务事务读取的关联资料为准，复用allTaskMaterials和原grant快照；后续重试读取原快照。无需新增资料摘要字段、校验步骤或重新确认弹窗。后续增删资料按现有任务授权流程处理，不改变已提交操作的初始快照。

## 4. 统一服务端授权和提交

统一解析结果包含任务域A、执行主体B和assignment/grant引用。它由服务端认证身份、任务归属及注册表生成，浏览器不能指定owner、tenant或执行身份。

提交使用现有 `POST /agent/tasks/{taskId}/point-and-deliberate` 及原请求恢复入口。不新增 `/external-commissions`。沿用target、任务版本、需求版本、幂等键和现有响应投影；资料直接复用原快照逻辑，不扩展请求DTO。

事务逻辑：
1. 按当前用户验证任务操作权限；先按原key恢复已有操作，成功重放不因之后关单被拒绝。
2. 解析目标真实绑定；本人目标合法即可，他人目标检查可信平台范围和开关。能力匹配、在线、忙碌及成本未知不作委派门槛。
3. 在既有task-root事务及共享锁顺序中复核任务/需求/资料版本、目标绑定与政策；统一写assignment、grant和原bootstrap outbox。
4. 沿原outbox确保会话并自动受理首轮；提交失败按原事务回滚，已提交但后续失败按原操作恢复，不重新派一单。

开关更新与新委派对同一政策记录串行裁决；政策不存在按关闭处理。先完成关单则拒绝新外单；先提交委派则视为存量继续。政策锁位置固定在目标identity锁之后、输入文件锁之前（见§9）；关单路径不得反向锁任务，不另造一套锁框架。

已接任务后续执行检查持久assignment/grant，不再检查“当前是否开放接外单”。真正撤销绑定、任务授权失效和旧会话fence仍按原安全规则处理，不能把开关关闭与身份失效混为一谈。

## 5. 接口与读模型

| 入口 | 最小变化 |
|---|---|
| Agent详情开关GET/PUT（新增 `/agent/{agentId}/external-service-policy`） | 本人管理权限；返回enabled/revision，PUT明确目标值、expectedRevision和原幂等机制；仅修改该Agent |
| 任务候选（新增 `/agent/tasks/{taskId}/assignee-candidates`） | 任务有权用户读取，合并本人与同平台开放目标；复用项目分页约定，所有合法目标可达，不以推荐TopN代替候选全集 |
| 原recommend | 复用同一候选资格查询；只排序/建议，推荐失败仍可手选 |
| 原point-and-deliberate与request恢复 | 接受两类目标，共用编排和响应；不返回外单专属下一步指令 |
| 原任务详情/操作投影 | 返回权威assignedTarget及既有actions，不依赖目标仍在当前候选中 |
| 原Runtime/议事/成果接口 | 沿既有协议传递、校验稳定授权引用，正确解析任务域与执行主体 |

候选最小摘要：agentId、displayName、providerDisplayName、isMine、availability及现有推荐摘要。不并列设计canCommission与canAssign两套资格；推荐信息不授权，服务端提交再次校验。不公开宿主地址、凭据、私有安装目录或其他客户数据。

本人管理名册与任务候选职责不同：名册仍只管理自己的Agent；任务详情按任务授权加载承办摘要。继续办理不能再依赖operableAgents；私人密议、刷新技能与安装配置仍保持本人权限。

## 6. 共用执行链的必要修正

- 数据、任务会话、输入和成果始终归A；模型连接、技能安装、Runtime会话属于B。本人任务是A=B的同一模型，不是另一条执行路径。
- 出站按授权目标B路由；ACK、receipt、delta/final、invalid outcome、停止回执等，均从认证B和持久执行/outbox引用解析回A，再核对agent/binding/session fence。不能直接信任请求中指定的A，也不能只修改成功回报。
- 队列、领取、输入、effect、结果提交和恢复使用同一主体解析结果；保留既有幂等、授权版本和旧回报隔离。
- Runtime线程/缓存按完整任务域、会话与既有授权代际隔离。若原键已经充分隔离则不改；仅补实证缺失的上下文，不新建外单runner或协议。
- 他人Agent开放不赋予其所属用户浏览A任务的应用权限。但其宿主管理员可能接触处理中的资料；前端不承诺对宿主的密码学隔离。

## 7. 状态、取消与范围收敛

不新增外单业务状态。任务状态、bootstrap提交/恢复、执行状态、成果和验收沿原模型；同一原操作重试不产生第二个首轮执行。

取消沿现有任务actions和后端规则：当前不支持运行中整单取消，本期不因外单扩建。服务方关闭开关只禁新单；不提供服务方逐单撤回/转单。原通用能力已有的继续、停止某次执行等保留原含义和授权，不能换名充当撤单。

不新增换承办流程；如原页面允许换承办，必须沿现有assignment/grant代际保证旧执行不能写新目标，不能默认把旧私聊交给新目标。若现有能力不满足，该操作按既有状态约束处理，不用本需求扩大其可用范围。

## 8. 迁移、验证与未核实项

实施在原表补必要字段/索引；历史本人授权按注册表可核实身份回填执行主体，不能推测跨域映射。活动授权迁移和旧回报需专项验证。内测按最新契约同步升级，不留owner缺省回退或双轨兼容实现。

同平台身份已由用户冻结为：`tenant_id`与`client_id`同时精确相等。值来自认证scope和注册表，不需要额外平台注册映射；任一不同都不可见、不可委派。沿现行tenant约束，不借本功能扩展多租户能力。

业务、接口与实现选择在§9冻结，不再留“平台映射/资料版本策略待定”。代码测试仍须证明实现符合合同，文档冻结不等于迁移或并发测试通过。

## 9. D3.1编码合同（2026-10-21冻结）

### 9.1 固定范围与授权解析
- 范围仅普通单Agent任务的原point-and-deliberate链路；不扩funded/team/PRIVATE桥接能力，不为外单另设协议版本。
- 统一服务命名 `TaskAssigneeAuthorityService`，位于现有agent-service；提供 `resolveForAssignment(taskScope, canonicalAgentId)` 和 `resolveForExecution(authenticatedRuntime, persistedGrantReference)`。返回不可变taskScope、executorOwnerJiacn、targetAgentId、executorBindingId及grant/assignment版本；平台tenant/client共用taskScope，无需新增executorTenant/Client字段。
- 新派单目标必须为同tenant/client的ACTIVE非SYSTEM注册身份且binding有效；本人无需开关，他人须开关开启。只在此处做归属/开放判断，下游不传播isExternal执行分支。
- `targetAgentId`使用候选返回的canonical ID，不接受浏览器传owner/client/tenant/binding。保留原本人alias解析的地方不得用于猜测他人身份；新UI只提交canonical ID。
- 执行解析以持久grant固定的B为准，身份变更/绑定不符/旧session拒绝。本人执行也是完整B=A，不做缺字段时回退任务owner。

### 9.2 数据字段、索引和回执
新增 `agent_external_service_policy`（MySQL字符/时间类型与现有grant一致）：

| 字段 | 类型/约束 |
|---|---|
| id | BIGINT自增主键 |
| tenant_id/client_id/provider_owner_jiacn | VARCHAR(50)，NOT NULL，二进制比较 |
| agent_id | VARCHAR(100)，NOT NULL，canonical ID |
| binding_id | BIGINT NOT NULL，与注册表bindingId一致 |
| revision/expected_revision | BIGINT NOT NULL；revision=expected_revision+1，初始expected=0 |
| enabled | BOOLEAN NOT NULL |
| idempotency_key | VARCHAR(100) NOT NULL |
| request_hash | CHAR(64) ascii_bin NOT NULL |
| created_at | BIGINT NOT NULL，毫秒时间 |

唯一键 `(tenant_id,client_id,agent_id,binding_id,revision)` 和 `(tenant_id,client_id,provider_owner_jiacn,idempotency_key)`。查询当前开关取该绑定最高revision；同一身份锁下串行追加修订，不更新历史行，不需要单独回执表。成功回执可由该行确定重建；request hash包含目标、binding、expectedRevision、enabled和认证scope，不包含追踪requestId。每次新key成功写入均revision+1，即便布尔值未变；同key重放不增加revision。首次无行返回false/0。查询当前与查询原操作不能混淆。

`agent_task_execution_grant`新增：
- `executor_owner_jiacn VARCHAR(50)`：执行主体B；tenant/client复用grant原字段。
- `executor_binding_id BIGINT`：真实绑定；target_agent_id复用原字段。
- `external_policy_revision BIGINT NULL`：他人入单时冻结的政策版本；本人为NULL，不参与后续运行资格。
- 索引 `(tenant_id,client_id,executor_owner_jiacn,target_agent_id,state)`；binding在授权验证中精确比较。

既有PWE `taskGrantId/taskGrantVersion/assignmentRevision`和bootstrap `grantId`继续复用。按这些引用join grant取B，不再新增第二份委派事实。Chat出站/回报从已存的任务会话/dispatch→grant关系解析；若某个dispatch缺可持久恢复的grant引用，只给该记录补 `task_grant_id/task_grant_version`，不得只缓存于内存或用当前active grant替代历史授权。补引用的分支必须有断线恢复用例。

所有grant创建、换版、撤销、skill baseline复制路径都携带executor字段；不仅修改assignLocked首次insert。历史回填从grant.target_agent_id精确join注册表，并验证原tenant/client/owner；能证明的本人授权写B=A。无法证明的行输出具体诊断，禁止猜测或以默认owner继续执行。新写入强制字段完整；迁移先加列/回填/核验，再施加活跃授权非空约束。历史异常不得被伪造为已迁移成功。

### 9.3 HTTP固定输入输出
沿公共信封；以下字段均为data内容，64位整数使用十进制字符串。

**开关**
- `GET /agent/{agentId}/external-service-policy`：仅本人；返回 `{agentId, enabled, revision}`。
- `PUT`同路径，Idempotency-Key必填；输入 `{enabled: boolean, expectedRevision: "0"}`；200返回 `{agentId, enabled, revision}`。拒绝多余授权字段，不调用模型。
- `GET /agent/{agentId}/external-service-policy/request` + 原Idempotency-Key：返回该原操作的固定成功回执；未找到返回404。404不等于原PUT不会迟到，恢复时仍只重发同key同payload，不新建操作。
- 版本冲突/同key异payload为409；无权或目标不在认证scope按现有不可枚举边界404；未登录401、格式错误400。复用项目异常分类和信封code，不另建错误协议。

**候选**
- `GET /agent/tasks/{taskId}/assignee-candidates?afterAgentId=...&pageSize=...`；本人任务权限；pageSize默认50、最大100，仅控制分页批量，不限制总候选或执行容量。
- 在同tenant/client下以canonical ID二进制升序keyset分页，取ACTIVE且binding有效的本人或开放目标；返回 `{items, nextAfterAgentId}`。首版不按动态推荐分分页，推荐独立沿原recommend展示，避免游标稳定性框架。
- item固定 `{agentId,displayName,providerDisplayName,isMine,availability}`；availability沿既有枚举。公开昵称缺失返回null，UI显示“其他用户”，不回退内部登录账号；分页不返回私有安装配置。
- 推荐器与手选共用资格查询；在线/能力只影响推荐，不删候选。跨页期间开关变化允许候选刷新，提交处权威校验，不建立候选快照存储。

**委派和任务继续**
- 原POST `point-and-deliberate`输入保持 `{targetAgentId,expectedTaskVersion,requirementRevision}`＋原Idempotency-Key；成功仍200及原AssignmentOperationView。GET原request恢复不变。
- 目标关闭/政策并发导致新外单不可接受返回409，刷新候选；不存在/异平台目标404；任务版本冲突沿原409。本人不受政策影响。
- 原任务详情增加或复用 `assignedTarget`，字段同候选摘要；与既有actions一起决定继续办理。读取基于该任务grant，不过滤已关闭的承办Agent。不可用绑定显示不可用原因，不转交另一Agent或伪装运行成功。

### 9.4 事务与锁顺序
固定新增派单路径：task-root → 原requirement读 → grant-action → bootstrap-action → target identity → 最新policy行（仅新外单）→ 原文件/link/version锁。保留既有文件内部顺序。通过现有legacy assignment的target锁入口传入已解析B并在同锁区校验政策，不在调用前后两头重复加新锁。

开关PUT：先认证本人 → 锁target identity → 按key查原修订 → 原回执优先 → 读最新policy并校验expectedRevision → insert修订 → commit。不锁任务/grant/outbox，所以不引入identity→task的反向等待。无policy行时以已存在identity行串行首次写入，不依赖锁不存在行。

旧操作重放沿现有task-root/grant-action回执路径直接恢复，不要求当前开放。后续执行沿原task-root下的锁序，只把identity的owner替换成grant中的B，不新增policy锁，不全局重排旧锁体系。共享task-root的旧路径不得绕过根锁；并发测试验证关单/派单和重放，不以书面顺序代替实测。

### 9.5 精确修改入口与验证落点
| 代码入口 | 编码要求 |
|---|---|
| AgentTaskDeliberationOperationController / AgentTaskExecutionGrantServiceImpl.assignForDeliberation、assignLocked | 原DTO不变；去除“按A resolve目标”的假设，使用统一authority；保留allTaskMaterials与原bootstrap；所有grant复制带B |
| AgentIdentityRegistryMapper / identity服务 / legacy assignment目标锁 | 增加同tenant/client精确目标查询和锁定；不修改原本人管理权限方法的含义 |
| PersonalWorkspaceExecutionServiceImpl及mapper | 队列与执行查grant的B，文件/任务仍A；覆盖claim/input/startEffect/recordEffect/result/resume |
| ChatDeliberationOutboxRelay、OutboxService、AgentWebSocketHandler | send选B；ACK/receipt/所有回报从持久关联回A，保留B会话fence，禁止仅用B作为outbox owner |
| AgentWorkItemLeaseServiceImpl / AgentTaskAggregationServiceImpl / TaskAssigneeAuthorityService | 租约claim/start/result及成果聚合保留任务A scope；canonical身份经task-scoped统一authority读取grant冻结B。live须当前ACTIVE grant及原binding，历史canonical不能授权live；无grant只允许原本人多Agent身份校验，已有grant缺字段直接拒绝。不得放宽私域Workspace/本人团队Plan权限 |
| Web useHallData、BountyPanel、JuyiHall | 候选不再依赖operableAgents；继续办理用assignedTarget；开关只加详情行，保留私人密议/管理guard |
| Runtime chat-runtime.mjs、agent-client.mjs | 不加外单判断；按现有授权引用完整隔离线程和ACK恢复，只有实证缺失才补协议字段 |

复用 `AgentTaskExecutionGrantSchemaContractTest`、`AgentTaskBountyBootstrapOutboxServiceImplTest`、`ChatDeliberationOutboxCommitTest`、`AgentWebSocketTypedDeliberationTest`以及PWE mapper/HTTP现有测试入口，补政策与authority专项用例。首个反馈证明：A/B同平台可派，异tenant/client各自拒绝；确认一次产生原首轮；关单不影响存量；重试不重复；C/另一绑定/旧session不可读写；本人原路径不回归。其他D3-AC按受影响路径执行，不删除权限/事务回归以凑工期。

## 10. 三小时开发目标与完成口径

三小时是用户要求的实施时间盒，不是已有实测工期保证。按连续推进安排：0–20分钟固定任务/源码与合同测试；20–90分钟政策、authority、grant/路由实现（Web可非重叠并行）；90–140分钟接通页面、Runtime和失败恢复；140–180分钟定向回归、集成及固定候选提交正式Flow。该分配为计划，不是承诺Flow排队和全部修复能在剩余窗口内完成。

不新增Reviewer、独立框架或阶段审批；同Owner范围内连续完成。三小时内以可验证闭环为目标，届时分别报告代码、定向诊断、正式Flow状态，未通过不标完成。发布仍按授权与不可变制品流程执行，不把“开发完成”冒充“生产上线”。本次用户要求先补详设，本轮仅完成合同冻结，不声称已启动或完成三小时编码。


<a id="selected-output-acceptance"></a>
## 成果选择与明确验收（2026-10-23收口）

合并已完成的 design.md，原核对2026-10-22。本节是该增量契约；发布/结果移至 acceptance.md，不另留临时方案作为第二入口。

### 冻结交互
1. 右上角清单勾选图标：title“验收”，aria-label“统一验收”；打开可验收成果清单，默认不选，支持多选。
2. 每个成果卡片按钮“验收此版”：进入同一弹窗，仅预选点击成果，允许调整选择。不以“最新版本”为准入条件。
3. 列表显示名称、版本/来源和预览，明确所选数量。零选择不可确认，不把历史稿全部隐式验收。
4. 只有点击“确认验收”才产生提交/验收写入。打开、选中、取消、关闭、继续修改均不产生验收写入。
5. 当前成果预览去掉下载按钮与空页脚；仅影响本次议事成果预览，不删除工作台等独立下载能力。
6. 确认后显示真实阶段：提交成果 → 验收；提交成功不等于任务完成，只有验收成功回执才显示完成。
7. 已完成事项仅提供验收记录，未选历史稿保留预览但不出现重复验收按钮。

## 3. 统一实现路径
- 成果候选从当前事项已有的持久化成果/完成消息来源构造，不从文件名、最后一条消息或图片 URL 推断身份。
- 技能成果携带 requestId/stepId/outputId/sha256，完成文本使用 messageSource 等既有契约。界面选择集合与最终发送集合必须同源。
- 显示当前任务授权范围内可正式提交的成果；历史版本不按时间排除。跨事项、跨账号或不符合当前 assignment revision 的记录不伪装为可验收项；若历史改派版本确需支持，须另核验服务端授权，不能绕过现有检查。
- 点击确认时冻结所选集合、摘要、任务版本和 assignment revision，保存原幂等键；不能处理过程中被新消息或选中项替换。
- 复用 useHallBountyFinalization 完成既有成果提交，检查返回 deliveryId/选中集合/任务版本；复用 useHallDeliveryReview 的正式验收操作。两处入口只负责初始选中项，不分两条业务路径。
- 一次用户确认允许顺序执行“提交 + 验收”，但两个接口不是原子事务。提交成功、验收失败时保留已提交状态，仅恢复验收，不重复提交。
- 已正式提交且与本次选择完全一致的当前交付复用；已有交付与新选历史稿不同，不能误验收当前交付。编码先用真实 API 合同验证既有替换/修订路径；若现有接口拒绝，补同一服务的最小能力和回归，不另建订单或状态机，不用模型代发提交。
- 超时或刷新只查询原操作；恢复需要继续写入时由用户明确操作，不因重新挂载自动验收。失败重试沿用原键/原集合。409 重新读取真实状态，不静默换稿；401/403 停止操作。

## 4. 影响范围
- Web：BountyDiscussionPanel.vue 的工具栏、BountyExecutionOutputs.vue 及实际消息成果卡片，调用方的选择集合与事件接线，HallDeliveryReviewDialog.vue/useHallDeliveryReview.js、useHallBountyFinalization.js，当前成果预览入口和相关测试。
- 优先复用已有组件/composable，不新增平行验收系统；移除这条路径上的过时自动验收语义，不保留兼容双轨。
- API：先回归 SelectedOutputFinalization 的技能/文本来源校验、历史同授权版本选择、多项提交、已有交付不同集合。必要修正限既有服务契约；不能在核验前声称必然零后端改动。
- Runtime：预计无需修改；不调用模型实现按钮动作。数据库：不计划增加表或业务状态。
- 风险：历史成果来源字段可能缺失、旧提交与新选择冲突、提交/验收部分成功、不同账号或重新委派后的来源权限。均须有明确失败提示，不降低保护来通过验收。

## 5. 验证与发布
- 最早反馈：从实际成果卡片追到选中对象及 finalization 请求，验证首稿/多次改稿/历史首稿/多选均携带正确来源；核查已有交付不同选择的 API 行为。
- 正式测试覆盖：顶部不默认全选、卡片仅预选本版、无下载按钮、关闭零写入、重复点击一次操作、提交失败、提交成功但验收失败、超时刷新原操作、409、身份切换、越权/跨事项、已完成只读、移动与桌面布局。
- 本人和跨用户外单各跑真实闭环；覆盖图片及文本。使用专用测试事项，不代用户验收现有503事项。
- 精确候选 commit/tree 固定后，Web4403172 / API5260799（仅有后端修改时）正式测试/构建；版本化发布消费同 Run 不可变制品，记录 SHA-256。develop push 不自动部署。
- 编码完统一部署验证；若两端有改动先发布所需 API，再发布 Web，按实际依赖核对。上线核对版本/制品/健康及真实账号闭环后通知用户。
- 原型多版本及文案诊断证据在 evidence/delivery-entry-prototype/multi-result.json，不替代产品 Flow 或线上验证。
