# 通用点将 → 自动议事：新主路径合同（2026-10-03）

## 决策与边界

遵循用户“无需做太多兼容补丁，一切都按新方案实施”：普通需求统一添加资料、显式点将、自动悬赏议事。新点将不要求选择生成图片/编辑图片/资料用途，不以原生绘图能力或独立 Images API 配置作为进入议事的前提。旧操作只保留未完成请求与已有内容保护，不再为旧生图入口增加产品分支。

本合同落实**点将与自动首轮议事源码**，不等同于完整多媒体交付已完成。API、Web、Client 候选仅推送特性分支；截至2026-10-04，Web新点将和CHAT会话接线、32项统一资料查阅协议已完成源码自检。自动查阅/执行编排、真实媒体与正式验收仍待完成，没有此次发布或线上成功证据。

## HTTP

- `POST /agent/tasks/{taskId}/point-and-deliberate`
- `GET /agent/tasks/{taskId}/point-and-deliberate/request`
- 两者均要求 owner JWT、tenant=0、唯一 `Idempotency-Key`，禁止 query 覆盖身份/意图；响应 `Cache-Control: private, no-store`。
- POST JSON **只允许**下面三个字段；版本为 canonical decimal string，不允许数字强制转换、重复字段、尾随 JSON、客户端资料目录/权限/绘图参数。

```json
{"targetAgentId":"agent-id","expectedTaskVersion":"0","requirementRevision":"1"}
```

POST 成功返回 HTTP 200 + 现有 `JsonResult.data` 内的 `AssignmentOperationView`；含原 task/target、字符串版本、grant/bootstrap 状态、冻结 inputs 目录、`initialOperation=DELIBERATE`。PENDING/CLAIMED/RETRY 不是 Agent 已收到或需求完成；ADMITTED 才具有 conversationId/initialRequestId，依然不是执行成功。GET 只读，不重新创建、补发首轮或调用 Provider。

POST 事务提交后若投影读取失败，浏览器须保留原键与原正文并核对原请求；不能因此生成新键或回退 `/assign`。400 格式错误，401 身份不成立，404 请求/目标/资料不在授权范围，409 原键异意图或版本冲突；持久态/来源故障维持真实 5xx。错误不返回数据库、私有路径或密钥。旧 image 操作不能被新 GET 解释为 DELIBERATE。

## 服务端点将事务

1. owner-scoped task-root 锁下核对服务端不可变需求修订。
2. 首次请求读取该任务全部 ACTIVE INPUT/REFERENCE 关联，固定 fileId/version；从真实版本读取 MIME/字节数/SHA-256。输出不是输入资料；同文件不同版本不合并。相同版本若有两历史关系只保留一次，内部优先 INPUT。
3. 全目录按既有32版本存储容量核对；非输入关联造成分页时继续读取，不把第一页误当全集。超限明确失败，不丢弃第33项。scope、失效文件、关联、版本均必须重新验证。
4. 复用原任务指派/grant/bootstrap outbox 同一事务。新初始操作为 DELIBERATE；基础操作集合为 DELIBERATE + INSPECT_INPUTS，**没有 GENERATE_IMAGE、paidExecutionAuthorized 或 costAuthorizationRef**。
5. 原键重放从原 grant 输入快照重建意图，不混入后来补充的资料；原目标/版本/正文哈希仍核对。下游 admission 仍检查当前 assignment/grant，不把历史重放当当前执行权。

没有新增文件系统、历史回填、表或 DDL；资料用途字段仅为内部精确 ACL 关系，不变成 UI 入口。

## 自动首轮

- Bootstrap 消费前复核完整需求修订及资料摘要；通过现有 grant admission 和 task/binding/conversation 锁序建立唯一 bounty 会话。
- DELIBERATE 复用 `ChatTypedDiscussionAdmissionService`，把完整 `title + description` 和全部精确选择器送入 DISCUSSION。稳定首轮 key 由原 sourceBusinessActionId 及作用域派生。
- typed admission 持久化源目录及 durable CHAT request/turn/outbox；Agent 可以 ANSWER、CLARIFY 或提出后续执行建议。重复消费复用原 typed receipt。
- 初始 CHAT **没有执行 step/executionId**；不插入 WAITING_ADMISSION image link，不伪造正在生图。
- typed 目录支持 INPUT/REFERENCE 精确关系与32项；SQL 保留 owner/client/tenant/task/file/version，并对 link_role 精确匹配。提供目录不等于已读取文件字节。
- Client 同步接收32项混合媒体目录，仍验证来源唯一、媒体类型、会话与目标绑定；不扩大操作或付费授权。

## Web新主路径（2026-10-04）

- 普通单目标点将只调用新POST；没有绘图capability前置、独立图像确认框、客户端inputRefs或旧assign fallback。资金榜与多Agent流程不借此扩大授权。
- 原存储槽的新记录为schema2，三字段正文/原键不可变；既有意图只能按原合同核对，不转换为新的议事请求。坏记录、身份/任务/目标变化不发新POST。
- ADMITTED后用精确task/assignment/target/request/conversation绑定读取首轮并接入会话；DELIBERATE为一个CHAT turn、零execution step，不伪造正在执行。首轮turn状态/序列防回退。
- 已确认PENDING的POST即使后续GET暂时失败，仍可只读观察原操作；不重发POST，不设任意性能取消门槛。
- Hall详情不再另建PDF/绘图产品入口；资料摘要显示中性文件/版本，无资料同样可点将。

## 统一资料查阅协议（2026-10-04）

创建目录、CHAT选择器、INSPECT清单、Agent输入与最终回执统一支持既有32项资料容量，不再在16项处截断/拒绝。`INPUT`与`REFERENCE`是服务端精确关系：保持原role/version，不能为了进入查阅而把INPUT改写REFERENCE；OUTPUT、大小写别名和无效版本仍拒绝。

查阅上下文、内容领取和最终提交复核都按owner/client/tenant/task/file/version及二进制精确role读取有效关联。领取/最终复核仍在既有task锁、assignment/conversation/runtime授权下，摘要/MIME/长度不放松。当前会话资产使用assetId/revision及null purpose，不强行套工作空间引用。Client保持固定API origin、manifest绑定及私有临时目录；无新的文件系统或兼容产品支路。

此项仅打通数据合同，**不代表Agent已自动选择何时查阅或跨类型执行**。当前typed执行建议仍含图片限定，需要继续改为实际能力驱动；不把协议容量自检冒充音频/文档真实处理能力。

## 源码自检与剩余工作

最新精确候选与日志摘要：`integration-evidence-20260928/unified-materials-correction-20261003/generic-point-inspection-source-progress-20261004.json`。历史点将59PASS、Chat51PASS/3条件MySQL未运行保留在原`generic-point-source-progress.json`，不改写历史结果。

本轮：Web287定向PASS + 14组件PASS；API64PASS/0skip；Client32PASS；Web原有lint 201项→200项，新增rule/message实例0。API新SQL是mock JDBC及合同验证，不冒充真实MySQL；Web正式测试/生产构建/制品发布仍须Flow4403172。没有本轮Provider调用、生产DML或发布。

必须继续：

1. Agent按需选择查阅并自动续议；执行建议按实际能力及既有授权协调，不强迫通用点将先走图像确认或额外重复确认，不推导未授权扣费。
2. 失败终态投影、仅本地spool未STAGED上传恢复、双接应、会话继续补资料、真实多媒体预览/下载、归档与正式交付验收。
3. 新路径MySQL及完整浏览器用例，统一候选达到上线条件后按既定版本/Flow政策发布；禁止重放418/419/420或删除paid claim。
