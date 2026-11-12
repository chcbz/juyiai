# 点将输入：任务已关联参考图合同 v1

日期：2026-09-30。追加冻结合同；以Web `84b14a5` / API `5668c747` / Client `1812e5b` 实码为基础。此包实现需求前选择图片后的真实关联回读，不代替合法费用授权、澄清/EDIT、产品验收或发布。

## 1. 复用现有领域与HTTP，不新增文件系统

需求创建依照 `requirement-reference-intake-contract-v1.md` 原子生成task和REFERENCE链接。**创建草稿、创建回执、latest指针不作为随后点将的输入权威**。新点将必须读取当前任务关联和owner-readable精确文件版本；原点将恢复始终使用原key/body/refs，不重新选择资料。

复用JWT owner-scoped只读入口：

- `GET /agent/tasks/{taskId}/file-links`；后续页唯一 `cursor` 参数。
- `GET /agent/personal-workspace/files/{fileId}`；同文件不同引用版本可共用本次有效详情，但必须逐一核验明确版本。
- 既有需求/current、canonical task、assign、assignment-operation及bootstrap合同保持不变，不另建资料目录或第二套request。

file-links raw JSON：`{items:[{relationId,taskId,fileId,version,role,state,relationRevision,createdAt}],nextCursor}`。详情以现有 `{file,latestVersion,versions,relations,derivation}` 为准。身份来自JWT和实际API auth generation，不能通过query/body指定owner。私有内容不使用公开URL；本包只读取元数据，不需要preview、Blob或把平台绝对路径交给浏览器。

## 2. 能力政策增量与分阶段上线

原 `point-and-start-capability` schemaVersion=1/root字段集不扩展；唯一枚举增量为 `inputRefsPolicy="TASK_LINKED_REFERENCE"`。Web必须同时识别旧 `EMPTY_ONLY` 和该新值，仍严格拒绝未知值、矛盾授权/能力/动作与错误身份回执，不把新策略当执行/费用许可。

API新增明确开关 `agent.task-reference-inputs.enabled`，默认false；关闭仍返回EMPTY_ONLY。仅在开关打开、已有storage/普通native链路真实就绪，且当前目标声明的GENERATE_IMAGE输入确实支持0–32 JPEG/PNG时，才可宣告TASK_LINKED_REFERENCE。声明存在或配置=true不替代实际源验证；read/admit/start继续原有实时校验。

本包不改变 `authorization=UNAVAILABLE`、paid=false或newStart=false的真实费用缺口。后续合法费用桥才能使newStart可用。不可为跑通本包在生产合成costRef、UI强制READY或放开fast-v1 EXECUTE。

对EMPTY_ONLY的新意图也要完整只读核对任务REFERENCE目录：有实际有效参考图时阻止新写，不能静默丢图发送[]。完整空目录可按原EMPTY_ONLY政策继续；失败、未知或不完整目录不等于空。已有原操作的恢复不受当前输入政策改动影响，不转legacy。

## 3. 浏览器可确定输入与失败行为

每个新意图固定显式task/target、身份scope、authorizationGeneration及本地resolver generation。原intent检查必须发生在capability、file-links和文件详情读取前；PRESENT/CORRUPT/UNAVAILABLE不进入新输入解析或另一写入路径。

1. 完整读取关联分页，直到nextCursor=null；不能只读第一页。沿用实际每页50，不另设最大页数/时延门槛。重复cursor、跨页重复relation、错task、非法字段/版本/revision均拒绝，不用去重掩盖不完整返回。
2. 仅ACTIVE+REFERENCE进入该图片政策；DETACHED/INPUT/OUTPUT不加入。重复fileId/version的REFERENCE拒绝；第33个不同引用拒绝，不截断前32。32沿用既有grant/native输入上限，不是新增性能门禁。
3. 每个选中文件必须在本人当前可读详情中ACTIVE；详情fileId与所有版本归属一致，version恰好匹配一次，1..2147483647。MIME取该版本，不取latest或body：只接受image/jpeg/image/png。最新v3不能替换关联v2。TRASHED、不可读/缺失、重复版本或不支持MIME阻止新写；不得跳过坏图。
4. 结果为固定规范排序的 `{fileId,version,purpose:"REFERENCE"}` 数组，交给原point-and-start持久化链路。只有所有分页/必要详情成功且没有ACTIVE/REFERENCE时才是[]。空页仍有nextCursor则继续，不提前判空。
5. 每次await后检查显式task/target、scope、auth generation及resolver generation。身份/选择/请求替代/unmount后，迟到结果不更新新界面，不发native或legacy写入。无按时延SLO取消或拒绝。
6. 输入读取失败显示“参考资料未能核对，未办理”，保留原需求，不自动另走legacy或另建intent。一旦原key/body已持久化，后续刷新/恢复只查询或明确重放原body，不按当前链接改写refs，不重发首轮聊天。

用户体验须展示本次精确参考版本或明确资料核对状态；不能让元数据目录被误认为Agent已经读取了图片内容。

## 4. 服务端TOCTOU和实际执行输入

浏览器读取不是锁/授权，不声称分页是全局数据库快照。它产生用户本次选择的精确引用集合；选择后新附加的链接不悄悄加入该原意图。

真正assign_and_start依旧复用 `AgentTaskExecutionGrantServiceImpl`：任务root/目标归属与版本锁内，对每个引用锁本人workspace file及该task/file/version/purpose关联，要求ACTIVE/精确版本，固定实际MIME/长度/摘要。读取之后解除关联/回收/权限变化会使写入失败或按真实事务事实恢复，不能只信Web。重新附加同一内容不会修改已持久化的原输入快照；不要求新增目录token或修改原assign请求hash。

真正native EXECUTE复用 `ChatBountyExecutionCoordinator` 的references解析、`PersonalWorkspaceExecutionServiceImpl` 的conversation输入合同和已有客户端受权manifest领取/摘要校验：JPEG/PNG限制在执行准入再次验证，START和output commit继续复核grant/assignment/runtime归属。此包不能将普通grant支持的其他资料/操作整体收窄，也不能靠提示词补ACL。

输出仍是持久conversation asset；客户端run inputs/outputs/scratch只是临时加工目录。READ元数据、grant固定快照、实际物化和Provider成功分别报告。

## 5. 最小验证与写集

### Web Owner

最小路径：新 `hallTaskLinkedReferenceInputs.js` 与对应单测/集成测试；只读扩展 `usePersonalWorkspaceTaskLinks.js`；`hallNativeBountyCapability.js`、`JuyiHall.vue`和对应native/point测试。可抽出可复用的页面编排函数以便实际调用链组合测试，但不为测试复制业务流程。普通/funded/原恢复不变量保留，不改API/Client或原选择器已验树。

验证：多页含第二页图、完整空、v2/latestv3、MIME/归属/缺失重复版本、DETACHED/INPUT/OUTPUT、33/重复refs、cursor重复/重复relation/错误task、任一GET401/403/404/503不可降级空、身份/授权/选择/unmount迟到、既有original零目录读取、恢复原refs、EMPTY_ONLY有图不丢弃、TASK_LINKED_REFERENCE精确body持久化及单次assign。须用真实resolver/HTTP adapter与真实point/start hook，且证明实际Hall调用同一编排；fixture HTTP不是浏览器业务验收。

### API Owner

不触碰原子需求创建Owner写集。最小为chat的 `PointAndStartCapabilityService` 及对应constructor/context/HTTP测试。复用已有grant/reference/coordinator/native输入验证，不另建表/重复parser/绕过事务。若发现既有执行重验缺陷，先归因并在此Owner明确补充写集后修复，不擅自修改另一Owner文件。

验证：开关关闭/目标不ready/链路未启用不可广告TASK_LINKED_REFERENCE；真实支持范围正向、现有EMPTY_ONLY/费用unready不变；scope、元数据GET零写；既有grant固定引用/解除关联拒绝、coordinator MIME/内容摘要/精确输入回归。正常依赖图下Gradle经orchestrator串行，Owner自检，不创建Reviewer。

Client当前已实现0–32 JPEG/PNG受权引用路径，byte-exact协议不变；此包无需为测试修改native声明。后续新Client行为必须单独精确验证，不能从API/Web源码通过推断两种接应已升级。

本合同及代码仅支持研发源交付；必须再完成原子创建API整合、合法费用、澄清/EDIT/派生输入、双接应、所有34项浏览器产品用例和exact版本制品部署后，才能通知可验收。
