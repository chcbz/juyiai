# 工程详细设计 v1

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：最小清晰办事体验与事实展示。**

### 最小责任链
API业务状态；Web按原型展示明确意图；成果服务提供正式交付事实。

需求→承办→原议事→成果→显式验收；返工与新需求分开。

### 实施约束
DRAFT/SUBMISSION/RESULTS历史合同不冒充新业务完成；不重建并行页面/重复确认/重复正文，不把预览当成果或自动验收。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> **2026-09-22收尾更新：** 当前已发布 `1.13.10-uxfix4`，用户确认本轮UI并授权收尾；最新实现、精确SHA、302/39/6/37测试分层与尚未验证项见 `session-closeout-20260922.md`。横屏保留沉浸地图；竖屏仅地图“横屏看全景”，不显示其他方向／地图控制按钮。本补充覆盖下文旧方向入口设计；不改写历史失败或宣称整套业务／真机验收完成。

状态：设计候选，**新增合同均未实现**。既有合同以 `source-audit.json` 绑定的release SHA为准。本文不覆盖既有身份、正式交付、账本或地图引擎冻结合同。

## 1. 复用与差距

| 领域 | 已有源码/实测能力 | 本次改造 |
|---|---|---|
| 地图/方向 | HallStage、useHallExperienceMode、miniProgramOrientation；原生/虚拟路径已有 | 保留引擎与方向控制，解耦homeMode与orientation；去半宽抽屉，复核晚到回调/等待行为 |
| 弹窗 | useHallPanels已有聚焦/捕获/回焦；PersonalWorkspace已有分层 | 统一根窗口导航栈、来源、草稿/层级/滚动恢复；不再嵌一个完整应用 |
| 文件库 | 上传、版本、预览、内容、回收/恢复、任务/会话关联 | 取材模式与浏览模式共用组件；版本固定与返回统一 |
| 执行 | POST create、只读历史、按原key核对、GET详情、输入撤权 | 复用请求幂等与权限；新增私人事项/草稿持久关联和成果查询投影 |
| 正式任务 | 已有workspace、formal-deliveries、decision、rework-executions | 独立适配，保留租约、根锁、输入关联及验收语义；不拿私人接口绕过 |
| 聊天 | 范围隔离、历史、流式会话 | 显式conversationId+scope；选择内容转草稿，不引入另一套聊天服务 |
| 阅读 | 典籍、阅读位置、手札及进度接口 | 只接来源/引用/返回，不重建阅读器 |
| 结果回传 | 已补failure精确鉴权路径；已有持久收件箱 | 还需持久化终态待报、确认后清理；临时文件和声明成果隔离 |

**关键缺口不能只用localStorage填补。** Demo将草稿和所有样例存浏览器，不满足生产身份隔离、跨设备恢复、可靠执行和费用确认。

## 2. 前端组件与状态归属

既有根：`/home/isp/wsps/cyf/web/src/components/world/JuyiHall.vue`，在实施worktree对应相对路径改造；根checkout较旧，不在其上直接覆盖。

建议新增至 `web/src/components/juyiting/`（完整路径根同上）：

| 组件 | 责任 |
|---|---|
| HallWorkWindow.vue | 唯一活动窗口、标题/方向/返回/关闭、焦点与可用区域 |
| HallOverview.vue | 独立overview投影，部分失败/最近/需处理 |
| HallRequestEditor.vue、HallRequestConfirm.vue | 草稿编辑、显式对象/固定版本/范围/费用授权 |
| HallCaseDetail.vue | source-aware详情壳；进展/资料/成果，不实现第二套执行状态机 |
| HallMaterialPicker.vue | 临时选择事务、上传/预览复用；确认才写草稿 |
| HallFileDetail.vue、HallResultList.vue | 版本、预览/下载、来源/修改；正式动作交由现有模块 |
| HallOrientationControl.vue | 地图与窗口共用方向入口 |

建议composables：`useHallNavigationSession`、`useHallDraft`、`useHallOverview`、`useHallCaseAdapter`；改造既有useHallExperienceMode/useHallPanels；复用usePersonalWorkspace、usePersonalWorkspaceExecution与任务/会话链接composable。

数据层三类严格分开：
1. 服务端事实：草稿revision、执行状态/输入快照、文件版本、任务动作权限。
2. UI会话：navigation frames、活动tab、临时选择、焦点/滚动、地图镜头。
3. 设备状态：homeMode、用户方向偏好、物理方向、键盘可用区域、资源归属。

```ts
type ItemRef =
  | { sourceType: 'PRIVATE_CASE'; caseId: string }
  | { sourceType: 'TASK'; taskId: string }
  | { sourceType: 'LEGACY_EXECUTION'; executionId: string }
  | { sourceType: 'DRAFT'; draftId: string };
type Frame = {
  key: string; view: string; origin: 'map'|'overview'|'tasks'|'chat'|'files'|'books';
  ref?: ItemRef; conversationId?: string; draftId?: string;
  tab?: 'progress'|'materials'|'results'; selectedVersions?: {fileId:string;version:number}[];
  focusAnchor?: string; scrollAnchor?: string;
};
```

每条来源键为`sourceType + 该类型ID`；不从标题、Agent或时间近似合并。Frame不持Token/Provider凭据，不把敏感正文序列化URL。选人提交必须显式targetAgentId。mapAgents来自`/agent/map`、roster来自`/agent/roster`；不引入`/agent/active`。

身份epoch变更：清空内存/本地最小恢复索引，取消旧身份读取并忽略晚到响应，关掉旧窗口/下载句柄；已受理执行不撤销、不重放。方向切换不改变epoch或业务请求generation。

## 3. 导航与异步规则

- 根入口replaceRoot；选材/预览push；返回pop；确认选材commitSelectionAndPop；关闭saveAndDismiss。同层tab变化replace而非push。
- 系统返回先消费一层有效history状态；到根后交由路由/宿主。浏览器历史只保存无敏感内容的引用。
- 路由/宿主重建通过服务端draftId、caseId、executionId恢复；未提交的临时选择若要跨页保留，保存为草稿中的`uiCheckpoint`，但不改变已确认inputs，恢复后仍需点“使用”。
- 一个活动业务面；子层隐藏后inert，不保留多个可操作dialog。预览内文滚动不与外层同方向重复套滚动。
- 轮询同一executionId：请求完成后再按配置安排下一次，只读；页面隐藏可暂停观测、回来立即核对，不取消运行。网络失败显示“更新中断/最后核对时间”。
- 不以1s/3s/5s耗时将QUEUED改FAILED；不因剩余预算不足跳过下一步。网络配置超时/用户取消/身份取消依既有策略，未知提交不等于未受理。
- 既有任务事件流继续复用；事件按现有事件ID/版本去重。重连缺事件时读快照，不根据socket断开创建新运行。新增私人读模型本期用读取/轮询，不再加一条SSE链路。

## 4. 领域对象：不再造Task系统

`caseId`只用于私人委托聚合，和已有TASK的`taskId/workItemId`不同；**已有ExecutionView.workItemId是正式工作项，不可借作UI事项ID**。

候选新增表（真实迁移名称在B01冻结）：

| 表 | 关键字段/约束 | 责任 |
|---|---|---|
| hall_request_draft | draft_id PK；tenant/client/owner；kind CREATE/REVISION/TASK_CREATE/TASK_ACTION；source_ref；case_id/task_id/conversation_id；title/instruction；target_agent_id；output_mime；inputs_json；source_output_ref；ui_checkpoint_json；revision；state EDITING/SUBMITTED/DISCARDED；submitted_execution_id/submission_ref；create_key/create_hash；submit_key/submit_hash；discard_key/discard_hash；updated_at | 可恢复的账号草稿，非运行队列 |
| hall_private_case | case_id PK；tenant/client/owner；title；origin_ref；revision；created_at/updated_at | 私人事项元数据，不复制执行状态为事实 |
| hall_case_execution | case_id/execution_id关联；scope；revision_no；parent_execution_id；source_output_ref；created_at；scope+execution_id唯一、case+revision_no唯一 | 确认时绑定；不可变成果谱系 |
| hall_user_item_mark | scope+source_type+source_id唯一；viewed_result_ref；archived_at；revision；last_operation_key/hash/result_revision | 私人“已查看/收入案卷”；不是任务验收 |

所有查询和唯一键包括服务端有效tenant/client/owner（即使当前tenant为默认值也不省略隔离维度）。JWT/既有scope resolver确定归属，不信任请求体owner。正文不进日志或埋点，存储/备份沿用既有私有数据策略。

幂等存储：草稿建立(scope,create_key)唯一和(scope,submit_key)非空唯一约束，固定保存请求hash与原submissionRef；discard是一次性生命周期命令，记录自己的key/hash。标记是可逆的CAS设值操作，以scope+ref+expectedRevision防覆盖，最近相同key/hash重放返回原结果；更早已被后续标记替代的重放返回412而不重施旧状态。

索引：草稿(scope,state,updated_at,draft_id)，私人事项(scope,updated_at,case_id)，执行关联(scope,execution_id)、(scope,case_id,revision_no)。不先建通用搜索/画像/全量复制表。

历史兼容：旧执行以LEGACY_EXECUTION可见，零数据迁移也可读；用户明确从旧成果发起修改时，校验归属并在同一事务创建case、绑定旧执行、新执行。冲突时重读唯一绑定，不能让同一旧运行被并发挂到两个case。不批量改旧execution状态，不推断标题/父子关系。

## 5. 已有API复用清单

以下按release源码核对；请求DTO细节不在本次改写，实施直接导入既有类型/测试。

| 方法/路径 | 复用目的 |
|---|---|
| GET `/agent/map`；POST `/agent/roster` | 地图和可操作名册独立 |
| POST `/agent/tasks/search`；既有任务详情/指派/工作区接口 | 协作事项列表、执行动作与权限 |
| GET/POST `/agent/personal-workspace/files` | 文件列表/上传 |
| GET/PATCH `/agent/personal-workspace/files/{id}` | 详情/元数据 |
| GET/POST `/agent/personal-workspace/files/{id}/versions` | 历史/新版本 |
| GET `/agent/personal-workspace/files/{id}/versions/{version}/preview`、`/content` | 固定版本预览/下载 |
| POST `/agent/personal-workspace/files/{id}/trash`、`/restore` | 回收与恢复；不是永久清理 |
| GET/POST/DELETE 既有 `/agent/tasks/{taskId}/file-links...` 与 `/agent/conversations/{conversationId}/file-links...` | 原作用域链接；链接不自动扩权 |
| GET `/agent/personal-workspace/executions/capabilities` | 真实输入/输出及generationEnabled |
| POST `/agent/personal-workspace/executions` | 既有显式执行创建；保留旧客户端 |
| GET `/agent/personal-workspace/executions` | 私人历史，使用现有createdAt+executionId游标 |
| GET `/agent/personal-workspace/executions/request` + Idempotency-Key | 原意图只读核对；404不能证明从未受理 |
| GET `/agent/personal-workspace/executions/{id}` | 执行详情；保留failure/模式/业务任务字段 |
| GET/POST `/agent/tasks/{taskId}/formal-deliveries` | 正式成果及提交 |
| POST `/agent/tasks/{taskId}/formal-deliveries/{deliveryId}/decision`、`/rework-executions` | 原正式验收和返工；不能绕开decisionVersion/sourceOutputRef |

文件二进制下载沿用鉴权链/受控地址。不能在浏览器无认证新开tab导致偶发403后就公开文件；临时URL不进入分析日志。

## 6. 新增API候选合同

命名空间：`/agent/hall`。全部浏览器JWT，scope server-derived；私有响应`Cache-Control: private, no-store`。所有ID为不透明字符串，revision为非负安全整数/既有一致编码。集合采用受校验游标，不接客户端任意SQL排序。

### 6.1 只读投影

| 方法/路径 | 输入 | 输出/行为 |
|---|---|---|
| GET `/overview?cursor=...` | 可选游标 | `{schemaVersion:1,sections:{recent,needsAction},sourceStatus,asOf,nextCursor}`；各section含items与complete/partial/error；未知计数为null而非0 |
| GET `/items?kind=...&view=...&q=...&cursor=...` | kind=all/private/task/draft，view=recent/needsAction/archive；q为有界名称查询 | 与overview同一种ItemSummary；任务列表筛选不修改首页缓存 |
| GET `/submissions/request` | Idempotency-Key | 新草稿提交的只读核对，返回`{ref,execution?,task?,submittedAt}`；可恢复TASK_CREATE；未找到404仍不能证明在途请求未受理 |
| GET `/cases/{caseId}` | ID | `{caseId,title,revision,executions:[...],allowedActions,sourceRef}`；无可见范围不泄露是否存在 |
| GET `/executions/{executionId}/results` | ID | `{executionId,state,manifestId,items:[{outputId,fileId,fileVersion,mime,filename,byteLength,sha256,availability}],allowedActions}`；只返回已提交且调用者可读输出 |

ItemSummary = `{ref,title,status:{code,evidenceSource,observedAt},targetAgent?,nextAction?,allowedActions,updatedAt}`。私人仅基于case关联；正式任务基于原任务ACL和状态。分页以稳定`updatedAt,sourceType,id`顺序；不同源失败不把缺项报空。第一版允许各section独立游标与明确分区，不为了“统一”在前端把两页随意拼成一个正确总数。

数据一致性：overview非事务性全局快照，`asOf`只表示本次采样时间；action需在服务端执行时重验版本/ACL，不相信过期allowedActions。已归档私人事项若产生新执行/新成果，应按新变化重新进入最近与需查看，不丢事件。

### 6.2 草稿CRUD

| 方法/路径 | 输入/并发 | 响应 |
|---|---|---|
| POST `/drafts` | Idempotency-Key；`{kind,originRef,sourceRef?,caseId?,taskId?,conversationId?,instruction,title,targetAgentId?,outputMime?,inputs:[{fileId,version}],sourceOutputRef?}` | 201 Draft；同key同payload返回同对象，不重复草稿 |
| GET `/drafts/{id}` | 身份校验 | 200 Draft；无权限统一404 |
| PUT `/drafts/{id}` | `If-Match`为revision；整体可编辑字段；source/引用均复核 | 200新revision；冲突412，保留用户文本并可比较/另存，不last-write-wins |
| POST `/drafts/{id}/discard` | Idempotency-Key+expectedRevision | 200已放弃；不影响任何已受理执行 |
| POST `/drafts/{id}/submit` | Idempotency-Key；`{expectedRevision,authorizationAcknowledgement}` | 202 `{ref,execution:ExecutionView}`，或TASK_CREATE返回新task ref；本事务完成后才显示已受理 |

Draft包含`draftId,revision,state,savedAt,editableFields,sourceSummary,submissionRef?`。authorizationAcknowledgement用于记录明确知情，不创造计费凭据；真实费用授权若已有token/revision引用则按既有服务核验，不接受前端自报“已付”。费用未知不得编造报价/上限保障；Provider受控授权不足则不能执行。

TASK_CREATE仅创建原业务任务而非私人execution；TASK_ACTION调既有任务应用服务，保留关联/租约前置；正式返工必须调现有rework服务，不通过私人修改字段模拟。类型对应的提交实现独立适配，合同冻结时用真实DTO逐项验明。

### 6.3 只影响私人整理的标记

PATCH `/items/{sourceType}/{sourceId}/mark`：`{expectedRevision,viewedResultRef?,archived:boolean}`，携带操作key。仅PRIVATE_CASE/LEGACY_EXECUTION支持私人整理；TASK要走原正式状态接口。无成果不能标“已查看成果”；标记不更改执行状态/验收/结算。可撤销归档。

### 6.4 统一错误与版本兼容

- 401：重新登录；403：当前动作禁止；私有对象不可见404；409：幂等冲突/已提交/运行状态冲突；412：草稿版本变化；422：能力/输入/格式不支持；503：实际存储或服务异常。正文`{code,message,traceId,retryable,details?}`，details只含允许对用户展示的字段。
- 发生明确提交前校验失败可改草稿；提交结果未知进入只读核对，不能把503/断网自动当未执行。
- 新增接口不替换旧executions/create；旧请求hash语义不变。新submit重用既有执行幂等key，并由草稿持久提交索引提供GET `/agent/hall/submissions/request`核对；它同时支持无execution的TASK_CREATE。旧私人执行仍可按既有GET原key核对后从关联索引找到ref。
- 新投影schemaVersion=1；增加可选字段兼容；移除/改变字段需新版本。使用实际响应契约测试，不能只mock happy path。

## 7. 原子提交、幂等与修改谱系

拟定事务顺序（实施前B01核对既有锁序，不可凭文档直接新加反序锁）：

1. 验证JWT与操作key，查本scope已提交意图；相同key/相同请求返回同回执，不同请求409；以草稿持久submit_key/hash/submission_ref为统一凭据。
2. 锁草稿、校验revision/EDITING；若已SUBMITTED且匹配本次意图直接返回原回执，不创建第二执行。
3. 私人：锁/创建case（正式：由原Task服务取得task-root等既有锁）；按既有排序校验文件、固定版本、来源范围、Agent和真实授权。
4. 在**同一数据库事务**内调用已有执行服务写运行/输入快照，再写case_execution及草稿SUBMITTED。禁止前端先POST execution再POST关联形成丢链窗口。
5. 提交后返回202；由既有持久队列领取执行，不把Provider调用塞进数据库事务。若现有服务传播行为不支持同一事务，先修应用服务边界/同库outbox，不伪称原子。
6. 事务回滚没有半个case已执行；丢响应但提交成功时原key可查。读取不到请求保持未知，记录最小意图key/账号作用域供恢复。

全局锁序禁止交叉反向：新适配器先锁draft，私人再锁case；正式随后沿既有task-root→file；case不能被正式Task路径锁后再回锁draft。既有客户端无需新表锁；所有新操作统一顺序，死锁与双标签页并发作为具体测试。

私人修改：选已提交且可访问的`sourceOutputRef={executionId,outputId,fileId,fileVersion}`，输入快照包含该版本，新执行与父执行/递增revision绑定。UI的“成果v2”是case修订序号，不等于将原物理fileVersion从1覆盖到2；输出也可能是新fileId。既有正式返工维持formalDeliveryId+decisionVersion授权，不接受普通用户伪造parent绕过验收。

## 8. 执行状态与业务状态分离

| 可信源 | 显示 | 主动作 |
|---|---|---|
| server Draft EDITING | 草稿 | 继续填写 |
| 本地intent发送中/响应不明 | 提交中/待核对 | 查询原key（无新POST） |
| execution QUEUED | 已受理 | 看进展/核对；不猜正在写文档 |
| 可信运行事件（存在时） | 执行中/具体阶段 | 看实际阶段；没有事件就不显示百分比 |
| OUTPUT_COMMITTED+可访问manifest | 成果可查看 | 预览/下载；不等于用户确认可用 |
| OUTPUT_COMMITTED但文件访问失败 | 成果已登记，暂不可领取 | 重读成果/报错，不自动重新生成 |
| FAILED+可信原因 | 执行失败 | 查原因；明确新执行另确认 |
| INPUTS_REVOKED | 输入授权已撤回 | 说明已知影响；不承诺Provider即时停止/费用自动退回 |
| 正式delivery decision | 待验收/需返工/已验收 | 原正式动作；私人标记不得写入这些状态 |

“需本人处理”只由真实动作派生：可继续草稿、待指派且本人有权、明确待确认/待查看成果/失败有可操作补救；QUEUED不算需处理。未知状态单独“待核对”，不以大红失败代替事实。

## 9. 客户端结果可靠回传（独立R01）

基线源码在 `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/`，部署副本不得直接改。既有inbox/archive可复用，不另造调度器。

- 持久状态至少区分RUNNING、RESULT_READY、REPORT_PENDING、ACKNOWLEDGED；inbox completed不是业务已成功。
- Provider结束后先持久化终态、taskId/runId/agent/scope、manifest digest或稳定失败code，再尝试上报。原子落盘/崩溃恢复沿用现有durable文件机制。
- 服务端成功确认且精确身份/运行/内容一致后才能将唯一待报记录清理/归档。报送失败保留，不吞异常后无条件删除；网络恢复重试**上报同一结果**，绝不重跑Provider。
- 重复成功/失败上报按exact run幂等；与已有终态冲突不能覆盖，保留证据转待处理。
- 输出声明只来自受控deliverables目录；工具临时PDF/图片/cache在独立scratch目录。仍拒绝未声明成果、路径穿越、符号链接逃逸与其他run文件；不能通过放宽全目录校验解决临时文件问题。
- 对旧生产运行的纠错是另一个精确授权操作，不纳入自动回填。本包只保障后续运行和已保留可恢复记录的规范重报。
- 测试：断网/401/403/503、落盘后崩溃、上报成功回包丢失、重复消息、乱序终态、未声明临时文件、部分上传、重启恢复。确认Provider调用次数不增。

## 10. 安全与敏感信息

- 两用户/两client/不同tenant实际scope夹具，列表、draft、case、结果、下载、预览及动作都测不可越权；未接入真实第二账号的测试不能宣称生产ACL验收。
- 从私聊转草稿必须选择/确认内容，按目标执行范围重新校验；私人资料不能因关联公议或正式任务直接公开。
- server capabilities是展示输入，操作时再次校验；客户端传allowedActions/owner/费用数值不可信。
- 撤回资料、回收文件、更改Agent或任务权限：提交时重验；在途运行保留原输入授权语义，不能静默换最新版。
- 诊断只记录对象ID/错误码/耗时/脱敏trace；不收正文、原文件名、Token、下载地址与模型输入。导出诊断需用户主动。

## 11. 兼容、迁移与交付

- 扩展式DDL新增草稿/私人索引表，不drop/rename旧表；使用既有迁移机制，建立版本标记。预演重复执行迁移、旧应用兼容、备份/恢复与权限；不因资料设计而操作生产数据库。
- 旧执行和旧入口兼容打开：关联则到新case，无关联则旧执行视图；不对所有历史行强造case。个人中心旧路由可受控重定向百宝箱，但导航不再展示工作空间。
- 交付顺序：API兼容能力/表→客户端可靠回传（精确owner授权与发布路径）→Web新壳→真实联调；Web可用能力探测，不在后台缺合同情况下开放假按钮。
- 普通功能向前修复，不以保守回退作为默认；安装仍须可恢复、版本/进程归属明确，失败不操作他人进程。
- 当前本地发布例外可用，但本任务已有两次同机构建OOM证据；**正式构建安排资源隔离环境**，不重复在业务服务同机堆叠构建。Gradle仍经orchestrator串行。无隔离环境则记录等待，不伪造测试或发布。
- 测试、commit/tree、制品SHA256、部署顺序/健康按exact版本绑定。记录`build_origin=local_user_authorized`，Flow恢复前不触发自动Flow/不伪造Run。
- 本轮新API/表/组件只是详设；未标accepted、未pin脏仓库、未新增执行台账/Reviewer。
