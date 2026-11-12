# C1：个人工作空间与文件交付合同 v1（候选）

> 2026-10-22 范围变更（REMOVE-PPT-PREVIEW-20261022）：按用户要求取消 PPT/PPTX 在线预览、逐页 PNG 与文本回退，保留上传、原文件下载、生成/修改交付和权限校验；下文历史预览要求不再适用于 PPT。源码候选及验证见同名 handoff，非上线证明。

2026-09-18。**文档候选，不是已上线 API，不是 ready/实施授权。** 本文把已明确的业务方向落为接口、数据和并发规则；真实运行时工具、客户端范围和实施源码尚有待核项。上位需求为 `spec.md`，用户流程为 `workspace-design.md`。

## 1. 本轮确定的设计原则

1. 上传无需悬赏；文件属于认证用户，不属于某个 Agent 或其服务器目录。
2. 同一文件可以用于多条本人任务；每次执行固定输入版本，后续上传不替换运行中的材料。
3. 原件默认不改写。由原件生成的修改版是派生成果；继续修改同一成果才追加其版本。重命名与内容版本分离。
4. 同一生成物在工作空间、任务页、对话中引用同一个 artifact/version；不复制成三份文件。
5. 任务关联是组织关系，不自动授予 Agent 读取权；授权在明确的执行请求中生成，只包含被选择的版本。
6. 移入回收站不是撤销执行，也不是永久清除。影响提示与撤销动作分开，避免正在执行的任务静默丢材料。
7. 首版不建团队盘、在线编辑器或自动同步盘，不要求物理上为每个用户挂载一个磁盘目录。

## 2. 从现有代码得到的约束

基线 API `e15f7020bf77153912aafce15fc11c67b2f06e11`；证据见 `docs/implementation/evidence/creative-workspace-c1-20260918/source-inventory.json`，不混用当前 checkout。

| 事实 | 对合同的影响 |
| --- | --- |
| `AgentTaskWorkspaceController` 的 `GET /agent/tasks/{taskId}/workspace` 是 task + actor 的协作快照 | 个人文件 API 使用新前缀 `/agent/personal-workspace`，不改旧接口含义 |
| `AgentTaskArtifactStorage.Scope` 有必填 taskId，文件系统 scope hash 也含 taskId | 无任务上传不能传空 taskId、虚构悬赏或放宽旧 scope 校验；新增 owner-scoped 输入存储适配，复用安全 IO 能力而不是篡改旧存储语义 |
| artifact 有 owner/task/producer/version，现有 owner 下载可读确切版本 | 生成文件仍引用现有 artifact 事实源；空间索引不独立决定“已生成/已验收” |
| `AgentRuntimeAuthentication` 与用户 OAuth 不同，principal 含 owner/client/Agent/runtimeInstance | 用户文件库与 runtime 文件领取分开鉴权；不把用户 JWT 交给 Agent |
| native filter 当前只放行 context-pack 和 E05 reassignment lease 路径 | 新 runtime 文件方法/路径必须逐项扩展并回归；不能放宽为 `/agent/**`，也不能认为现有身份自动允许文件上传 |
| 普通 `createTask` 初始化 OPEN 等悬赏字段，未发现独立的个人文件执行可见性字段 | 对话执行不能直接调用普通创建后只在前端隐藏；须明确内部执行来源和服务端所有列表/推荐/事件的可见性合同 |

认证 scope 沿既有单租户模式：tenant=`0`，client/owner 由服务器验证后的 principal 推导；不接受 body/query 中的任意 owner/tenant/client/producer。`client_id` 不是用户 ID；首版沿现有 client 隔离，不擅自合并不同 OAuth 客户端的数据。跨端是否同一 client 须在接线时核实。

## 3. 数据模型与版本含义

以下为拟新增/复用的逻辑记录，不是直接执行的 DDL。

| 记录 | 核心字段 / 约束 |
| --- | --- |
| 空间文件条目 | owner scope、`fileId`、`sourceKind=UPLOAD/ARTIFACT`、显示名称、`metadataRevision`、`ACTIVE/TRASHED`、创建时间；ARTIFACT 必须唯一绑定 sourceTaskId + artifactId |
| 上传版本 | owner scope、fileId、`version`、实际 MIME、原始文件名、hash、长度、私有存储引用；只用于 UPLOAD；版本内容不可变 |
| 任务文件关系 | owner scope、taskId、linkId、fileId、精确 version、`INPUT/REFERENCE/OUTPUT`、关系 revision；OUTPUT 来源关联由服务端生成，用户不可伪造 |
| 执行输入快照/授权 | 复用的 execution/run 绑定、明确 Agent、已选文件版本、grant 状态/revision、来源关系；不依赖“当前最新版本” |
| 预览派生记录 | 精确源引用/版本/hash、renderer 标识、`PENDING/READY/FAILED/UNSUPPORTED`、页/工作表索引、受控内容引用；预览不是源文件版本 |
| 幂等操作回执 | owner scope、操作类型、key、请求摘要、结果引用与状态；避免重复创建文件、任务、版本或派发模型 |

**两类版本统一显示但不重复建事实源：**
- UPLOAD 的 version 来自上传版本记录；ARTIFACT 的 version 直接采用 artifactVersion，不再存另一套输出版本号。
- `metadataRevision` 只用于显示名/回收站等管理并发；不得冒充文件内容版本或 taskVersion。
- 上传原件 U/v1 经 Agent 修改，得到新成果 A/v1，记录 `derivedFrom=U/v1`；再次修改 A 得到 A/v2。UI 显示“原件 → 修改版 → 后续版本”，不伪造连续的跨文件版本号。
- 另一任务从 U/v1 派生 B/v1，不能覆盖 A；明确修改现有 A 时才校验 expected artifactVersion。
- 用户重命名、回收站状态属于持久的管理元数据，不是可随意丢弃的缓存。可重建的是 artifact 目录/状态投影；重建不能恢复被用户移入回收站的项目或抹掉显示名。
- 文件名相同不覆盖；哈希相同不合并用户业务条目。内部内容去重即使采用，也不能跨 owner 泄露存在性或混用授权。

## 4. 通用 HTTP 合同

下文路径全为**新增候选**，既有接口除单列适配点外不变。响应 JSON 使用 `{data: ...}`；错误 `{code, message, requestId}`，不得含外部存储路径、凭据或他人文件信息。

- 用户端只接受现有用户 JWT，runtime 凭据调用用户目录返回拒绝；native 端只接受匹配的 AgentRuntime 身份及既有要求的 headers，不提供浏览器 native 凭据入口。
- ID 与版本都是明确值，不接受 `latest` 作为执行输入；版本/revision 用规范正整数字符串表示，避免 JS 精度与格式歧义。实际长度/计数限制沿已验证合同或依据另列，不在本设计随意发明数值。
- 新建/写入要求 `Idempotency-Key`；作用域为 owner + 操作类型 + 目标标识。摘要包含规范化请求与实际上传内容哈希；同 key 同请求重放原回执，同 key 不同请求返回 `409 IDEMPOTENCY_CONFLICT`，不得再执行。
- 已完成回执重放先复核当前身份和对象访问权。并发同 key 正在处理时返回 `202` 与同一 operationId；不执行第二次。超时/断线不代表失败，先查询操作回执。
- 文件元数据更新使用 `If-Match`（服务端返回的 metadata ETag）；缺失 `428 PRECONDITION_REQUIRED`，过期 `412 METADATA_CHANGED`。版本追加按 expectedPreviousVersion CAS，冲突 `409 FILE_VERSION_CONFLICT`。
- 用户读取：`Cache-Control: private, no-store`，二进制 `nosniff` 和安全文件名/实际扩展名；只读预览经过受控渲染，不执行 Office 宏、脚本或不可信 HTML。
- 查询与修改中的对象先核对 owner scope；外国对象或不存在统一 `404 FILE_NOT_FOUND`，不能先返回版本/类型错误暴露存在性。
- 不对列表缓存或预览索引默认信任，每次领取都核对当前权限；不以临时 URL 或任意路径作为文件身份。

## 5. 用户文件 API（C1-A）

前缀：`/agent/personal-workspace`。

| 方法与路径 | 请求 | 成功响应 / 语义 |
| --- | --- | --- |
| `GET /files` | q、sourceKind、mediaFamily、taskId、state、cursor；均可选 | `200 {items,nextCursor}`；默认 ACTIVE，本 owner 内按创建时间+fileId 降序。q 仅文件名，不宣称全文检索 |
| `POST /files` | multipart：一个 file、JSON metadata `{displayName?}`；幂等头；**无 taskId 要求** | `201 {operationId,file,version}`，原件 v1；只有字节校验/持久化和元数据提交完成才返回可领取 |
| `GET /files/{fileId}` | 无额外身份参数 | `200 {file,latestVersion,relations,derivation}` + ETag；已有输出版本/状态从 artifact/正式交付读取 |
| `PATCH /files/{fileId}` | `{displayName}`，If-Match + 幂等头 | `200 {file}` + 新 ETag；不改变源字节、原始文件名或 artifact.title 历史 |
| `GET /files/{fileId}/versions` | cursor | `200 {items,nextCursor}`；ARTIFACT 路由现有版本数据，不复制内容 |
| `POST /files/{fileId}/versions` | multipart file、metadata `{expectedPreviousVersion}`，幂等头 | 仅 UPLOAD 允许 owner 追加；`201 {operationId,version}`。ARTIFACT 返回 `409 OUTPUT_VERSION_MANAGED_BY_EXECUTION` |
| `GET /files/{fileId}/versions/{version}/content` | 精确版本 | `200` 私有文件流；上传走新输入适配，成果委托现有 owner 成果读取，不能只按 hash 取内容 |
| `GET /files/{fileId}/versions/{version}/preview` | 无 | `200 {state,parts,partial,reason?}`；不支持/失败有明确状态，不返回伪预览 |
| `GET /files/{fileId}/versions/{version}/preview/parts/{partId}` | 无 | `200` 受控预览内容；再次校验 owner 和源版本，不能以知道 partId 就读取 |
| `GET /files/{fileId}/usage` | 无 | `200 {impactRevision,taskReferences,activeExecutions}`；只返回当前 owner 有权查看的关系 |
| `POST /files/{fileId}/trash` | `{impactRevision,acknowledgeExistingReferences}`，If-Match + 幂等头 | `200 {file,effects}`；见删除语义；状态 ACTIVE→TRASHED，不删源字节 |
| `POST /files/{fileId}/restore` | 空 JSON，If-Match + 幂等头 | `200 {file}`；恢复条目，不自动恢复被撤销的执行授权 |
| `GET /operations/{operationId}` | 无 | `200 {state,result?,error?}`，状态 PROCESSING/COMMITTED/FAILED/RECONCILIATION_REQUIRED；只是操作回执，不是新任务状态机 |

列表 cursor 绑定 owner、筛选条件和最后排序键，跨用户/改筛选重用无效；不是授权凭证。第一版允许并发重命名等导致列表变化，客户端按 fileId 去重并可刷新，不虚称历史快照。翻页不读取文件全文。

`FileView` 最少字段：`fileId,sourceKind,displayName,mediaFamily,state,metadataRevision,latestVersion,createdAt,capabilities,source,links`。capabilities 分开 upload/read/edit/preview/download，含 AVAILABLE/UNSUPPORTED/UNVERIFIED，不因文件上传成功就标记可修改。

`VersionView`：`fileId,version,originalFilename,contentMimeType,byteLength,sha256,createdAt,derivedFrom,previewState`；`derivedFrom` 为精确文件版本数组，允许一个 PPT 来源于多个资料。

### 上传落库与恢复

字节先写私有暂存并计算 hash、类型/安全检查 → 写入不可变对象 → 同一 DB 事务提交条目/版本/操作回执和投影事件 → 返回成功。失败不得出现“READY 但文件不存在”；暂存孤儿单列恢复，不自动清除其他任务目录。传输重试复用 operationId/key，成功对象优先补元数据，不让用户重复产生逻辑文件。

现有存储接口是 byte[]/task scope；这里描述目标合同，不宣称当前已经支持流式 owner 上传。C1-A 须确定新适配器及实现资源依据，禁止用假 taskId 套旧接口。

## 6. 任务关联与输入授权（C1-B）

| 方法与路径 | 请求 | 返回与权限 |
| --- | --- | --- |
| `GET /agent/tasks/{taskId}/file-links` | cursor | `200 {items,nextCursor}`，owner task 权限；INPUT/REFERENCE/OUTPUT 分组，明确版本 |
| `POST /agent/tasks/{taskId}/file-links` | `{fileId,version,role:INPUT/REFERENCE}` + 幂等头 | `201 {link}`；本人 ACTIVE 文件及本人 task；同 task/file/version/role 不重复创建。只是选材，不派发 Agent |
| `DELETE /agent/tasks/{taskId}/file-links/{linkId}` | If-Match + 幂等头 | `200 {link,state:DETACHED,executionSnapshotsPreserved:true}`；取消未来选材关系，不抹除已经执行的快照。OUTPUT 来源关系不可用户删除 |

读取旧版与追加新版不互相替代；同一任务可先关联多个文件，但执行请求必须明确选择本次所用版本。不能因为是任务参与者就读到 owner 个人空间内未授权的其他资料。

### 回收站的明确选择

- 移入回收站只停止常规列表展示及新任务授权，不立即撤销已有 ACTIVE 执行快照。用户须确认“已有任务仍可能使用这些文件”；没有引用也必须提交最新 impactRevision，防止检查后又产生新授权的竞态。
- impactRevision 为服务端对关联/活跃授权集合的版本标识；变化返回 `409 FILE_USAGE_CHANGED`，返回本人的最新影响摘要，不修改任何状态。
- 取消关联不等于撤销已开始的执行。需要停止既有任务时用显式取消/撤销输入授权动作；服务端拒绝后续领取，不承诺瞬时收回已经下载的字节。
- owner 可从回收站查看/下载历史版本；任务历史仍能读取原已保存成果。永久删除与保留期限首版不提供，界面必须明确这不是“彻底删除”。

## 7. 对话执行与 runtime 文件桥接（C1-C/D，接线待决）

### 7.1 用户发起执行

候选 `POST /agent/personal-workspace/executions`：

```json
{
  "conversationId": "conv-example",
  "targetAgentId": "agent-example",
  "taskId": null,
  "instruction": "精简第二章，保留报价表",
  "inputs": [{"fileId": "file-example", "version": "1"}],
  "revisionOf": null
}
```

- 幂等头必需。先校验当前用户会话/Agent/文件权限、工具能力和付费/外发授权；缺授权返回可操作错误，不先收费或派发。
- 新生成无输入允许 `inputs=[]`；文件修改必须有实际输入。继续修改时 `revisionOf={fileId,version}`，需显式列为本次 inputs 并检查确切源版本。
- `taskId=null` 表示无需用户悬赏。服务器创建内部 task/work item/run、不可公开的执行来源记录；不能用普通 OPEN 悬赏创建后仅前端过滤。已有 taskId 则核对 owner 与执行目标，复用原任务。
- `202 {executionId,taskId,runId,state}` 仅表示持久受理和授权快照已提交，不表示执行完成。`GET /agent/personal-workspace/executions/{executionId}` 返回现有 task/run/成果事实的视图，不另建状态机。
- 对话前端将执行请求与同一 user message 关联，不能同时调用新执行入口和普通 chat 路径各派发一次；回复/进度继续通过既有会话事件投影。
- `POST /agent/personal-workspace/executions/{executionId}/revoke-inputs`：`{expectedGrantRevision}` + 幂等头，返回新 grant 状态和执行取消的真实状态；禁止伪报工具已停止。

**待决**：具体 conversation/message 幂等绑定、内部 task 来源标记/服务端列表隔离、初始工作项 lease 建立。E05 reassign lease 不能伪造为普通初始执行 lease；完成该适配前不得宣称上述受理路由 ready。

### 7.2 native 端候选方法

| 方法与路径 | 用途与边界 |
| --- | --- |
| `GET /agent/tasks/{taskId}/runs/{runId}/file-inputs` | 返回本 runtime 获授的 inputRef、精确版本/hash/类型，不返回 owner 全库或任意 URL |
| `GET /agent/tasks/{taskId}/runs/{runId}/file-inputs/{inputRef}/content` | 逐请求验证 Agent/runtime、assignment、run、输入 grant、当前授权/lease；输出实际私有文件流 |
| `POST /agent/tasks/{taskId}/runs/{runId}/file-output-staging` | 单个输出 multipart，含 clientOutputId、源输入引用和元数据，幂等头；只暂存，不算正式 artifact/交付 |
| `POST /agent/tasks/{taskId}/runs/{runId}/file-output-commits` | `{manifestId,outputs:[stagingRef...],revisionOf?}` + 幂等头；校验同 run、持有者、lease、hash/格式与源版本；事务发布 artifact、来源、回执及投影事件 |
| `GET /agent/tasks/{taskId}/runs/{runId}/file-output-commits/{manifestId}` | 查询精确持久回执，结果未知先查询；不能重新生成模型输出来“重试上传” |

所有上述 native 路径都需新增精确 method/path allowlist，用户 JWT 不可假扮 runtime；runtime 无个人文件库列表/删除/重命名权限。producer 从认证 principal 推导，凭据不写入模型 prompt 或工具日志。服务器可在已验证的精确输入授权下代理 owner 内容读取，但不把任意 owner read 方法暴露给 runtime。

输出提交默认创建派生 artifact；更新已有成果时验证本 run 的修改授权、source artifact/version 及 expectedPreviousVersion。一个 manifest 的文件、来源与回执在 DB 原子提交；外部字节已经暂存但 DB 失败时不能标交付。正式交付批次/验收继续走现有 formal delivery 规则，文件发布成功不自动判定用户已验收。

**待决**：现有 artifact service 的 actor/member 边界与 runtime run 权限适配、lease 的确切来源、原子多文件提交及正式交付桥接；必须在 exact 实施基线验证，不能仅增加 filter 白名单就算授权安全。

## 8. 并发、事务与事件恢复

- 不改变既有 task-root → artifact-version 锁顺序；涉及任务关联/授权时，先单个 task-root，再按稳定 fileId 顺序锁相关空间条目/输入版本，最后进入既有 artifact 事务。禁止持文件锁后逆向抢 task-root；跨多任务操作分成独立事务。
- 单文件重命名/回收站事务只锁空间条目及其 impact revision，不回头锁各 task-root。授予输入、关联/取消关联、grant 撤销等会影响 usage 的写入在同事务更新 impactRevision，因此可判定“新授权先提交”或“回收站先提交”，不能出现检查与授权脱节。
- 同时修改源内容与开始任务时：任务使用请求中的不可变 version，不追随最新指针；若源已被移入回收站则不签发新 grant。已开始任务有稳定快照。
- 同一 artifact 并发追加以 expectedPreviousVersion/CAS 解决冲突；不因为冲突自动重跑模型。元数据改名冲突与内容冲突分别报告。
- artifact 保存及状态继续由现有 domain/事务权威记录；工作空间归档事件携带 sourceTaskId/artifactId/version/hash，重放只 upsert 投影，不重新产出或验收。
- 候选事件：`workspace.file.created`、`workspace.file.version-added`、`workspace.file.metadata-changed`、`workspace.file.trashed/restored`、`workspace.task-link.changed`、`workspace.output-indexed`。信封包含 schemaVersion/eventId/owner scope/aggregateId/aggregateRevision/sourceRef；不得包含文件全文、凭据或外部链接。
- 事件必须在源事务提交后可见，采用可靠 outbox/既有持久事件适配，按 eventId 幂等消费；旧 revision 不覆盖新状态，丢失可由权威记录补投影。**管理元数据和回收站不从 artifact 自动重置。**
- 第一版不要求新建浏览器 SSE 流；上传/编辑后 readback、执行既有事件触发刷新、重新进入空间主动查询即可。避免为了文件目录再造一条消息总线。现有会话/任务事件仍遵循原 cursor/replay 规则。

## 9. 错误和用户可见状态

| HTTP / code | 用户含义 / 行为 |
| --- | --- |
| 401 UNAUTHENTICATED | 重新认证，不保留前身份的附件/预览缓存 |
| 403 CAPABILITY_FORBIDDEN | 当前主体不能执行此类操作；不得用返回内容推测他人对象 |
| 404 FILE_NOT_FOUND / TASK_NOT_FOUND | 不存在或不在当前 owner scope；响应不暴露外国对象 |
| 409 FILE_VERSION_CONFLICT / FILE_USAGE_CHANGED / IDEMPOTENCY_CONFLICT | 刷新本人的状态后明确选择；不隐式改用最新或重复派发 |
| 412 METADATA_CHANGED / 428 PRECONDITION_REQUIRED | 元数据并发条件失效/缺失；不覆盖别人的重命名或回收站动作 |
| 415 FILE_TYPE_UNSUPPORTED | 当前上传格式不支持；若只是编辑工具不支持则文件仍可保存，能力单独显示 |
| 422 CONTENT_INVALID / CAPABILITY_UNAVAILABLE / AUTHORIZATION_REQUIRED | 内容无效、工具无法完成或缺本次调用授权；给出明确补充动作，不虚报完成 |
| 503 STORAGE_UNAVAILABLE / OUTPUT_RECONCILIATION_REQUIRED | 文件或回执尚不能确认；查询/恢复已有操作，不重新收费生成 |

文件状态、previewState、executionState、formalDeliveryState 四者分离。预览失败不删除已保存文件；工具退出成功不等于成果已保存；已保存不等于用户验收。只有具备实际依据的传输限制才按实际错误报告；不添加任意秒数、文件大小或性能 deadline 硬门禁。

## 10. 迁移、兼容和实施顺序

### C1-A：个人上传与管理

新增空间条目/上传版本/操作回执及 owner 输入存储适配；文件格式支持与管理分离。先实现无悬赏上传、管理、精确下载和权限负例，不需要先改 Agent 客户端。输出目录最初只读引用已有 artifact。

### C1-B：已有成果投影与任务关联

新增关系/派生/预览元数据；以既有 artifact 为权威，原 owner 下载和 formal-deliveries 不改变含义。增量/受控回填仅记录空间引用，不复制旧字节、重编号或重放任务执行；保留管理 overlay。任务页面继续使用 `/agent/tasks/{taskId}/workspace` 原协作合同。

### C1-C/D：执行授权与 runtime 桥接

补内部执行可见性、输入授权、native 领取/回传、事务回执与对话接线。该段涉及客户端范围与初始 lease/producer 适配，不能用 A/B 的完成掩盖尚未打通。不得擅自改客户端部署副本。

### 实施前待核项

1. exact 实施基线和客户端源/部署差异归拢；运行时范围确认不影响继续 A/B 详细设计，但 C/D 实施必须明确。
2. 新表/索引/唯一键与既有迁移入口、outbox 能力；owner 存储独立 namespace 和写入恢复实现。所有 DDL 先在隔离环境验证，生产迁移另核目标与恢复。
3. 普通对话内部 task 的来源/可见性、初始 lease、artifact producer 适配与事件幂等键。此三项是 runtime 合同冻结前的明确缺口，不用虚构字段假装现成。
4. Office/PDF/图片工具的读取、编辑、预览和导出分别验证；外发/额度授权依原规则。

schema 采用增量兼容扩展，不修改旧 artifact URI、不批量搬文件、不直接更新生产任务。未核对前不能将整个 feature 标 ready；也不将所有基础文件库工作绑定到尚未授权的付费调用。新增身份/事务问题由责任 Owner 自检，不创建 Reviewer。

## 11. 验收样例索引

`workspace-contract-cases.json` 是设计用 Given/When/Then 清单，全部 `not_run`。包含无悬赏上传、身份隔离、双任务固定版本、元数据/内容并发、回收站竞态、输入撤销、native allowlist、可信 producer、恢复与投影重放等；它不是 mock 或自动化测试 PASS。


### 资料管理剩余修复（2026-10-16，源码及定向验证通过，未发布）

本节替代 usage 旧数组返回约定；统一接口规范仍为 `api/docs/interface-standard.md` v1.2。
`GET /personal-workspace/files/{fileId}/usage` 的业务 data 为
`{fileId, impactRevision, counts:{taskReferences, conversationReferences, activeInputGrants}}`。
修订和计数均为十进制字符串。三个计数分别统计当前身份范围内 ACTIVE 任务关联、ACTIVE 议事关联、ACTIVE 输入授权记录；不截断、不相加，不按执行状态过滤或执行 ID 去重。
后端同一 SELECT 读取修订与三个 COUNT，避免跨语句混合快照；增删关联/输入授权与文件修订在同一文件行锁和事务内提交。
回收确认使用本次 usage 的 impactRevision 同时生成 If-Match 和请求 data；412 后废弃旧确认，重新读取后由用户再次确认。回收保留旧版本、已有引用和授权，不等于撤销输入授权。
当前页面内的写入意图冻结原文件对象、请求内容、前提和 Idempotency-Key；双击共享请求，未知结果重试原操作，不生成新键。身份切换/销毁清除；不提供跨刷新恢复。关联重放回执是当前关联状态，可能已再次关联/解除，须区分原操作完成与当前状态。
固定源码 API `58b4b5f408257c6d5103d915e13c7927c1571e20`、Web `0bc9af441e10c714dca54dc2fca572dde477cbfe`；验证结果见 `docs/implementation/handoffs/WORKSPACE-MANAGEMENT-AUDIT-20261016.md`，不以本节代表线上已切换。
