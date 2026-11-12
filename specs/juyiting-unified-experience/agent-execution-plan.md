# Agent执行分包（2026-09-21用户指令补充）

> 文档收口（2026-10-23）：仅保留本文件内DRAFT-v1/SUBMISSION-v1/RESULTS-v1/OVERVIEW-v1的原源码契约及历史来源。旧Owner分包、Flow关闭/本机生产构建、旧主机与版本发布命令均不作为当前执行指令；当前任务按根AGENTS，不恢复独立Reviewer或自动部署。


本次用户已授权开始开发并允许并行。旧估算的人日分解保留作范围参考，**7–10工作周不再作为当前Agent实施排期**。不按Agent数量机械除人日，也不承诺无证据的小时级全量上线；从第一波源码/自检实际耗时校准后续。

## 2026-09-22 执行主机变更（覆盖下文旧远端限制）

用户明确“就用本机吧，不要用eva了”。不再联系或等待Eva；本机测试、构建、发布继续，经orchestrator串行Gradle。先核对实际负载及工具链，复用已成功的低内存JVM设置，并将本任务置于独立资源范围；不暂停生产、不抢占他人进程，不把历史OOM当永久拒绝理由，也不原样重试失败。Flow继续关闭，本地证据标记local_user_authorized。

## 发布目标（用户最新确认）

完整需求落实并验证后发布 **1.13.10**，发布健康及线上核验完成再通知用户验收；不能把第一波窗口壳当作整套完成。保留地图、手动方向切换、分层单活动窗和连续业务流程。当前两条Writer线继续推进；既有业务主机构建两次OOM的限制不因版本指令被解除。真实目标用户试点与需额外付费/生产数据变更的验证独立披露，不冒充已经通过。

## 协调与并行

主Agent仅维护合同/台账/集成和用户通知，不写应用实现；最多两名源码Owner并行。每人独立worktree，Web与API/Runtime路径不重叠。所有包Owner自检，无独立Reviewer。任务状态唯一来源仍是TASKS.yaml，下面是分包与依赖合同，不是动态执行台账。

| 批次 | Web线（balanced_worker） | API/Runtime线（critical_worker） | 收口 |
|---|---|---|---|
| 1 | UX-W01：统一主窗口、方向控制、地图/模式保留、低高度布局、焦点/返回 | UX-B01A：有身份隔离的持久草稿CRUD、CAS/幂等、schema及API测试源码 | 先交exact源码与可运行定向测试；不等待全部页面再报告 |
| 2 | UX-W02：共享编辑器、选材/预览/确认、接草稿接口 | UX-B01B：私人case/执行关联、原子submit与原key核对；正式任务适配不绕权限 | 冻结submit DTO后联调 |
| 3 | UX-W03：事项进展/成果/恢复 | UX-R01：终态持久待报、ACK后清理、scratch隔离 | 不用mock成功代替结果可靠 |
| 4 | UX-W05：概览/消息与空错态 | UX-B02：独立首页读模型；UX-B03：真实成果索引/修改谱系 | 开放能力按实际合同显示 |
| 5 | UX-W04：百宝箱/议事/点将/阅读来源与返回整合 | 对前述真实联调缺口继续修正 | Q01/Q02按包到达开始；不一开始重建全平台 |
| 6 | P01目标用户试点 | L01受控交付/观测 | 源码、测试、制品/版本、真实闭环分别报告 |

任务ID落库前缀`JYT-UX-`，后缀`-20260921`。以上UX短名是WBS简称。B01拆A/B，避免一个Agent先等待所有事务/正式交付合同才开始可独立落地的草稿基础。

## 第一波Web合同

基于Web `76c16ab68de605689201d491f25bee68eae0f0ac`。可写JuyiHall、juyiting窗口/方向/布局相关组件与composables、对应定向tests；不改API/Runtime/根docs。

- 保留真实HallStage/melonJS、地图/名册分流和所有功能入口。
- 根办理窗口统一近全幅低高度布局，不右半宽；个人中心不恢复工作空间。
- 地图与活动面板均有方向控制；保留真实/虚拟/小程序分支，不能以CSS旋转宣称系统键盘方向通过。
- homeMode与orientation解耦的壳/状态可先落地；不要为实现默认地图把原引擎替换成Demo静态图片。任何未完成的概览数据接线留给W05，禁止注入虚构业务数据。
- 现有草稿/选材/讨论状态不因方向变化卸载丢失；单活动层focus/return契约明确。
- 删除无依据的强制3秒方向取消逻辑时保留实际API拒绝、用户撤回、资源归属与晚到回调防护，不增大数字假装修复。
- 最小测试：方向请求拒绝/晚到、软键盘缩高不换业务模式、活动面板跨方向不丢对象、横屏几何/焦点；允许轻量定向Web测试，禁止Vite生产构建。

## 第一波API合同：DRAFT-v1（本波冻结）

基于API `bbf5b739c1bb14c69fde60ba7eb3be41be2377cf`，仅先实现草稿基础，不在此波启动任何execution或Provider。

- `POST /agent/hall/drafts`：Idempotency-Key，body含`kind=CREATE|REVISION|TASK_CREATE|TASK_ACTION`、`originRef`、可选source/case/task/conversation引用、title/instruction/targetAgentId/outputMime/inputs/sourceOutputRef。草稿允许尚未填写完成，但字段类型、作用域与来源必须校验。返回201 Draft；同scope/key同请求返回同draft，不同请求409。
- `GET /agent/hall/drafts/{id}`：200 Draft，不可见404。
- `PUT /agent/hall/drafts/{id}`：If-Match使用带引号revision如`"3"`；替换可编辑字段，200新revision，过期412，保留旧值；不能编辑已提交/放弃草稿。
- `POST /agent/hall/drafts/{id}/discard`：Idempotency-Key、expectedRevision；幂等放弃，不影响执行。不可见404，版本冲突412，错误不能写库。
- `GET /agent/hall/drafts?cursor=...`：仅当前scope的可恢复草稿摘要，稳定updatedAt+draftId游标；列表不返回全部instruction正文。该补充供W02恢复入口，后续overview复用同服务。
- Draft响应为`{draftId,revision,state,savedAt,kind,editableFields,sourceSummary,submissionRef}`；editableFields承载title/instruction/targetAgentId/outputMime/inputs等实际可编辑字段，submissionRef本波null；state只EDITING/DISCARDED。
- scope取既有JWT resolver/信任边界，不信任body中的owner/client/tenant。新增控制器显式处理401/403/私有对象404；private,no-store。
- 复用已有合法source与固定版本ACL查询；暂无法验证的来源不能用“先存字符串再说”绕过权限，可以返回可读422并标明未开放，向主Agent报告，不伪装全范围可用。
- schema/迁移脚本只写源码；禁止连接生产库、执行生产DDL。revision、create/discard key/hash、生命周期及scope索引按design.md，不存浏览器敏感正文到localStorage。
- 本波**不实现/不暴露假submit、case查询、正式Task创建、计费**；由B01B在真实应用服务合同核对后接通。草稿存在不等于新业务任务。
- 必须补Controller/service/mapper或事务夹具测试源码：身份隔离、同key同/异请求、并发CAS、无权来源、discard重放、旧执行API无副作用。
- 后端编译/Gradle本轮主机不跑；Owner做静态自检和提交，给出精确测试selector，交隔离验证环境。不是放弃测试，不允许据此标accepted/发布。

## 后续交付规则

每包报告开始/结束时间、commit/tree、修改路径、真实运行过的检查与未执行项。第一次同根失败先归因，第二次不变输入停盲重试。源码就绪与测试通过/合入/发布分开；没有收费/生产DML授权不做真实有副作用试验。

用户授权本地构建交付仍有效，但先有资源隔离；不是云效不可用就重复在已OOM业务主机上构建。正式Gradle只经orchestrator串行，不让两个Agent争抢内存/锁或操作对方进程。

## 1.13.10隔离验证与发布交接要求

- 2026-09-21只读核对：远端develop仍为上列发布基线，两组件尚无`release/1.13.10`；此为当时观测，真正冻结前重查，不抢占/覆盖他人分支。
- 当前业务主机约3.7GiB RAM且此前两次全局OOM。工具列出了独立eva的`/home/chc/wsps/cyf`项目，但尚未核对它的资源/权限/源码，不等同已有可用构建机；已向用户询问新建该主机测试打包任务的授权，不擅自创建跨主机任务。
- 隔离执行者先核对主机不是当前生产节点、已有任务/资源归属和实际工具链。用独立干净checkout获取固定候选，核对commit/tree；不能覆盖eva原工作区或清理其缓存/进程。无Provider、生产DB或部署权限。
- Gradle必须经orchestrator，传入task_id、cwd、tree-sha、实际selector和隔离fixture摘要。现有`ops/release/build-api.sh`直接flock调用Gradle且有历史锁超时，不可原样当本次入口；沿当前已授权orchestrator路径产出，再打包校验。不能抄旧源码树的测试PASS。
- 新hall表启动时会执行扩展式DDL；最终迁移表/SQL摘要、真实MySQL兼容性与旧应用恢复必须随最终候选核实，尚未操作生产DDL/DML。
- 最终相关验证成功、自检合入develop后冻结未占用release/1.13.10；记录`build_origin=local_user_authorized`、前后端及Runtime SHA/tree、实际测试、制品SHA-256。Flow保持不触发。业务主机只受控安装已验证制品与健康/线上核验，不源代码构建。
- 发布通知包含验收入口、地图/方向/草稿/选材/交办/成果/修改的可执行清单和真实未验证项。目标用户试点属于发布后的业务验收；未获授权的付费生成与真机测试不伪造PASS，也不临时添加为无依据发布门禁。

### eva入口尝试补充（2026-09-21）

用户已允许尝试。只读项目/任务记录查询成功，但当前没有可调用的跨主机创建/投递工具；业务机SSH别名eva一次探测因名称无法解析退出255。未创建eva任务、未开始测试构建。具体可粘贴预检任务见`/home/isp/wsps/cyf/docs/implementation/handoffs/JYT-UX-EVA-PREFLIGHT-20260921.md`。不能把用户授权或项目可见当作连通/构建成功。

## 第二波提交合同：SUBMISSION-v1（源码冻结，尚未完成隔离验证）

合同核对来源：API commit `4b285f0e1e2b0d26e0b28be51d64bca30ee2fdc1` / tree `9c175f80935eae2bed978ab1bc49268a441f58e9` 中的 HallRequestDraftService、HallRequestDraftController、HallSubmissionController。下面是候选源码合同，不是线上接口已发布的声明。

- `POST /agent/hall/drafts/{draftId}/submit`：`Idempotency-Key` header，body `{expectedRevision, authorizationAcknowledgement}`，202 receipt。这里不是 PUT 的 If-Match；两个字段必填。
- `GET /agent/hall/submissions/request`：同一原始 `Idempotency-Key` header，无 query/body，200 receipt；404 不证明在途 POST 未受理，不据此自动重新提交。
- `GET /agent/hall/cases/{caseId}`：200 私人 CaseView，无 query。三条接口使用既有 JWT owner/client/tenant 身份与 `private, no-store`。
- receipt=`{ref:{sourceType,sourceId},execution,task,submittedAt}`；execution 复用 PersonalWorkspaceExecutionService.ExecutionView，当前 task=null。
- CaseView=`{caseId,title,revision,executions,allowedActions,sourceRef:{originRef}}`；executions 的每项=`{revisionNo,parentExecutionId,sourceOutputRef,execution}`。sourceOutputRef=`{executionId,outputId,fileId,fileVersion}`，不可把 fileVersion 错映射成最新版本。
- Draft 在提交后允许 SUBMITTED；同 key 回放原 receipt，不再次创建执行；412 保留本地编辑后核对，不覆盖其他编辑。未知/断网保留 scope 隔离的非敏感 key/ref，不能在浏览器存敏感需求正文。
- CREATE/REVISION 为私人事项；TASK_ACTION 复用正式 execution 的任务/会话/文件/租约 ACL，不等于正式返工。TASK_CREATE 此候选明确返回422 `HALL_SUBMISSION_KIND_UNAVAILABLE`，界面继续保留既有正式“张榜”；不能把这项缺口计为新统一正式创建已完成。正式返工仍经原 formal-delivery rework 接口。
- 错误区分401/403、私有资源404、409（key/状态/执行冲突）、412 revision、422来源/类型不可用、503存储。GET与POST有不同错误码前缀，Web按实际响应读取，不硬猜同一码。
- B03若现有case/execution输出已满足需求就复用，不另造平行成果系统；新增最小读合同先协调再接线。

验证：B01B仅静态自检；已写隔离MySQL并发/回滚fixture，但未执行Java编译/Gradle/MySQL。精确 selector `:agent:jia-agent-service:jytUxB01b`，对应fixture digest `9f5fb80f8e106855cf1144fb5adc2035396dbe5e728bbd6af8b2e16f4fd82e88`。该digest不自动适用于后续B03源码。Q02实测浏览器启动SIGTRAP、未导航应用，不能声称四视口通过；详见W01浏览器证据。

## 第三波成果合同：RESULTS-v1（Owner已确认，源码候选待提交与隔离验证）

- `GET /agent/hall/executions/{executionId}/results`，无 query/body；仅 JWT owner/client/tenant 可见的 PRIVATE execution。正式 TASK 返回404，正式成果/返工继续使用既有 formal-deliveries。
- DTO=`{executionId,state,manifestId,items:[{outputId,fileId,fileVersion,mime,filename,byteLength,sha256,availability}],allowedActions}`。单execution固定输出集合不另加分页/任意上限。
- 非终态只给真实state，manifestId=null/items=[]，不泄漏staged output。提交后按已绑定output读取精确file/version，不追最新版。文件回收/缺失/元数据不一致保留已登记成果并标UNAVAILABLE，不伪造可下载；可读取为AVAILABLE，只有AVAILABLE成果可开放CREATE_REVISION。
- manifest重建必须与既有Runtime规范算法一致（taskId/runId及outputId排序后的output/hash/byteLength），不发明新摘要算法；以最终测试绑定。
- 身份不可见404、非法query/请求400、缺少身份401、存储/投影自相矛盾503；private,no-store。
- 谱系继续使用B01B CaseView；用户明确新建修改草稿才懒关联旧私人执行，新run不覆盖旧输出。复用既有execution/output/file/version/case，不新增表。

这是前后端实现合同，不是已上线/测试通过结论；最终源码与测试状态只以运行台账为准。

## OVERVIEW-v1（本机续接批次：接口结构冻结、未验证/未上线）

协调者按B02 Owner当前源码`HallReadService`/`HallReadController`冻结以下结构供W05并行；最终SHA和验证仍以台账为准。新私人mark/正式待验收投影仍须补齐，不以当前partial包装完整实现。

- `GET /agent/hall/overview`无query：`{schemaVersion:1,sections:{recent:Section,needsAction:Section},sourceStatus:{recent:{private/task/draft:SourceStatus},needsAction:同结构},asOf}`。
- `Section={status:complete|partial|error,partitions:{private/task/draft:Partition}}`；`Partition={items:[ItemSummary],status,nextCursor,count:null,errorCode}`；`SourceStatus={status,errorCode}`。complete代表成功读取该源，不代表没有下一页。
- `ItemSummary={ref:{sourceType:DRAFT|PRIVATE_CASE|LEGACY_EXECUTION|TASK,sourceId},title可null,status:{code,evidenceSource,observedAt},targetAgent:null|{agentId},nextAction,allowedActions,updatedAt}`。nextAction分别为EDIT_DRAFT/OPEN_CASE/OPEN_EXECUTION/OPEN_TASK；只有已接通动作可呈现。
- 分区续页用`GET /agent/hall/items?kind=private|task|draft|all&view=recent|needsAction&q=&cursor=`；有cursor时kind必须是单source。返回`{schemaVersion,kind,view,q,section:Section,sourceStatus,asOf}`。不合并异源页构造“正确总数”；query绑定游标，JWT scope服务端派生；private,no-store。
- UI必须区分loading、成功空集、partial、error，并可单源重试；独立于榜单筛选。消息入口使用真实needsAction，不伪造通知/已读等于验收。
- 当前实现明确披露VIEWED_RESULT_NOT_TRACKED/TASK_REVIEW_NOT_PROJECTED及archive422；这是待补范围，不是设计删除或可发布结论。私人mark/归档、新成果重现与原正式待验收需在后续提交补齐，保持DTO向后兼容。

### TASK_CREATE-v1 适配补充（9d5ec3f源码合同，未测试上线）

`TASK_CREATE`提交回执为`{ref:{sourceType:'TASK',sourceId},execution:null,task:{taskId,taskVersion:string},submittedAt}`，taskId与sourceId相同；TASK_ACTION仍为execution非空/task:null。未知状态依旧只用原key核对，不因GET错误换key。

当前适配只创建无悬赏金额、无指派的正式任务，不自动付费、执行或补附件。`title<=30`、`instruction<=200`来自既有task_plan真实持久宽度及taskPlanFor截断逻辑；其他targetAgentId/outputMime/sourceRef/conversationId须null，inputs为空。旧create响应曾回显完整说明，但持久只存截断字段，不能把响应回显当长文保存成功。UI明确“任务名目/简述”和后续正式办理，不展示无法提交字段，不静默清用户已有内容。私人需求编辑仍保留全文/格式/选材/明确Agent；付费张榜及正式验收沿原入口。这不代表资金/长正式说明/新能力已统一完成。
