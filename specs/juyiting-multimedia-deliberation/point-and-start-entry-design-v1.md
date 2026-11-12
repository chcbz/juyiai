# 点将即办理：真实入口闭环详设 v1

日期：2026-09-30。状态：**施工合同；当前入口尚未接通，不是上线或验收证据**。补充[长期融合详设 v2](fusion-detailed-design-v2.md)，不改写已冻结的[最终验收合同](finalization-contract-v1.md)。

## 1. 当前源码证据与缺口

核对基线：API `194ec91a596c28f9575a64aef47a5bf7b9fb6778`、Web `02af2d062cf6f87969f42901948059a1d95624ea`。

- Web `useHallTaskActions.js::assignTask` 普通榜仅发 `{agentId, agentIds}`；`JuyiHall.vue::assignTask` 成功后标记点将，不自动进入议事。
- API `AgentController.assignTask` 只有出现 v2 字段才调用 `assignAndGrant`；旧请求继续调用 legacy `assignTask`。v2 回执是 `AgentTaskExecutionGrantDTO`，**不是任务 DTO**。
- `AgentTaskDTO` 当前只有 taskVersion，没有 requirementRevision；不可从展示正文、计划或默认值 1 推导权威需求修订。
- 内部 `AgentTaskRequirementSnapshotService` 已有 `captureOnCreate/read/requireCurrent/reconfirm`，没有供浏览器读取当前修订的接口。新建普通榜已持久化不可变原文；历史榜可能没有可信快照。
- 已有 Chat bootstrap/outbox/稳定会话基础；但不能把内部 discovery/reconcile 服务当成已存在的浏览器 owner-scoped binding/initial-request 读接口。需要核对现有会话列表投影是否能精确对应 assignment，否则新增纯读投影。前端成果区和完成刷新单测通过，不证明页面会实际走到这条执行链路。

因此：必须补齐**权威当前修订读取 → 原键 v2 点将 → canonical task/binding 读取 → 自动进入已有悬赏议事**。不得用旧点将成功、mock 媒体或本地 `completed` 标签替代。

## 2. 权威当前需求只读接口（新增，尚未实现）

`GET /agent/tasks/{taskId}/requirements/current`

认证：受认证的人类 owner JWT；tenant 固定为现有受支持的 `0`，client/owner 仅取服务器认证 claims。请求不得指定另一个 owner/client/tenant。Task ID 仅是定位符，查询必须包含精确 owner/client/tenant，禁止大小写或尾空格等价匹配。

`JsonResult.success` 的 data：

```json
{
  "taskId": "task-123",
  "taskVersion": "0",
  "requirementRevision": "1",
  "title": "画一只鸟",
  "description": null,
  "contentSha256": "64位小写十六进制摘要",
  "source": "CREATE"
}
```

- taskVersion 是当前真实 task root 版本，不是创建版本；允许 0。requirementRevision 必须大于 0。两者以规范十进制**字符串**输出，不丢失 Java long 精度。
- source 仅 `CREATE` / `RECONFIRM`；title/description 是已校验摘要的不可变原文，不从截断的 task plan 重建。
- 在既有 owner-scoped task-root 事务/锁边界中读取当前 root 和最新 snapshot，锁顺序 `task root → requirement snapshot`，保证同一观察。不写表、不更新任务版本、不 reconfirm、不建 grant/消息/outbox、不调用 Provider。
- GET 仅返回浏览器所需字段，不返回 scope、私有目录、工具、费用凭据或租约。响应 `Cache-Control: private, no-store`。
- 特性开关 `agent.task-requirement-snapshot.read-enabled` 默认 false。未启用不广告此能力；启用之前验证真实 schema readiness。此开关只控制读取入口，不授予任何执行权限。

| 状况 | HTTP / 业务语义 |
| --- | --- |
| 无有效 owner JWT | 401；不查询数据库 |
| 参数格式非法 | 400；不规范化为另一个 ID |
| task 不存在或属于其他 scope | 404；同样通用信息，不泄漏存在性 |
| 当前 owner task 没有可信需求快照 | 409 / `REQUIREMENT_RECONFIRM_REQUIRED`；不得假造 revision=1 |
| root/snapshot 摘要或归属损坏 | 500 / `REQUIREMENT_INTEGRITY_ERROR`；不可回退到展示正文 |
| 实际数据库/依赖不可用 | 503 / `REQUIREMENT_SOURCE_UNAVAILABLE`；保留原因证据但不泄漏 SQL/凭据 |

历史榜重新确认属于单独显式 owner 写动作；本读接口不能自动补录。尚无确认 UI/API 时明确说明不能使用新办理流程，保持已支持的旧路径，不偷偷将其视为已授权 v2。

## 3. 浏览器 v2 点将协议

仅对已协商支持此流程的普通**单 Agent**榜启用；资金榜、旧多 Agent 点将和旧接口语义保持不变。纯展示开关 `isMultimediaDeliberationUiEnabled` 不是执行授权或能力证明。

1. 明确采用点击行/动作传入的 Agent ID，不使用隐藏的 selectedAgent 替代。
2. GET 当前需求与 canonical task，检查 task ID、真实 open 状态、owner 操作权限与目标能力。引用来自工作空间精确 fileId/version 的本次选择，可为空；**当前 grant 还要求本任务已有 ACTIVE、owner-scoped 的 task-file link（含用途）**，选择个人文件本身不满足此条件。引用入榜/关联应明确、幂等并回读成功，不能在 grant 中跳过该校验。不能默认读取整个 Agent 工作目录。
3. 固定原需求 revision、taskVersion、Agent、操作集合和 inputRefs，将**原 body + 原幂等键**持久化并 readback 后才 POST。
4. `POST /agent/tasks/{taskId}/assign`，携带 `Idempotency-Key`：

```json
{
  "agentId": "agent-123",
  "workflowVersion": 2,
  "businessAction": "assign_and_start",
  "expectedTaskVersion": 0,
  "requirementRevision": 1,
  "requestedOperations": ["GENERATE_IMAGE"],
  "inputRefs": [{"fileId": "file-123", "version": 2, "purpose": "REFERENCE"}]
}
```

此示例只展示已有 AgentTaskAssignDTO 合同，不证明有费用授权。前端把规范版本字符串转数字前必须证明其位于 JS safe integer 范围，不能截断、四舍五入或盲目 `Number(null)`。无法安全表示时明确停止该写操作，后续单独版本化数字合同，不改旧接口含义。

- 只申请需要的操作；**当前 `AgentTaskBountyBootstrapPayload.initialOperation` 只允许一个非 INSPECT 操作**，所以示例不能同时传 GENERATE_IMAGE/EDIT_IMAGE。长期授权操作集合与“本次初始操作”须分离，并通过兼容合同/持久 outbox 验证后支持同授权边界内的后续修改；未实现前不得把编辑视为默认已授权，也不应为编辑新建会话或绕过 grant。后续请求仍校验服务端 grant、Agent 能力、资料/外发及现有费用授权。
- 不传 `agentIds`、`allowQueue=true`、`authorized`、`tools`、`permittedToolPolicyRef`、`costAuthorizationRef` 或 `paidExecutionAuthorized` 等越权/旧多选字段。
- Idempotency-Key 必须符合当前服务器 exact 规则及最大 100 字符；不能借用 finalization 的另一个键范围。存储损坏/不可用不得绕过 readback 写入。
- 服务端通过原任务根事务创建 assignment、grant 与 bootstrap outbox；浏览器不再单独发送首轮“画一只鸟”，避免重复办理/收费。

## 4. 成功、未知与自动议事

- grant 回执必须核对 taskId、targetAgentId、requirementRevision、assignmentRevision、grantVersion、state 与精确 inputs/operations。ACTIVE grant 仅是授权事实，不等于 Provider 已执行或图片已生成。
- 不能 `Object.assign(task, grant)`；成功后只读 GET canonical task、稳定 bounty binding/initial request 的 owner-safe 投影，并从服务端事实刷新列表。此投影是必须补齐/核对的接口合同，不假定当前已有公开 binding endpoint；不得以“取列表第一条”匹配会话。
- 确认当前 assignment 对应的 conversation 后自动进入该会话，加载历史/游标并订阅。bootstrap 尚未投影时显示“已点将，议事准备中”，保留原操作，继续只读查询；不得新建另一个聊天、补发首轮或伪报失败。
- 网络中断、暂时 404、SSE 断开不证明原 POST 未受理。刷新/remount 不自动 POST；用户明确“继续原点将”才用**原 key/body**恢复，不换 Agent、版本、资料或键。要改选先核对原事实，再发独立新意图。
- 同 key/body 的已受理重复请求不得多建 bootstrap/execution。键冲突、真实任务版本变化、权限撤回应明确提示，不自动降级为 legacy 绕过。
- 身份切换取消本浏览器等待并 generation 隔离迟到回执；不取消其他身份已持久受理的操作，不跨身份读恢复记录。
- `conversationTask` 是独立于浏览任务的会话主题快照；进入时更新为 canonical 快照，不因用户浏览另一张榜把当前会话换题。验收仍重新读权威版本。

## 5. 最小开发包与验证

| 包 | 写入范围/责任 | 必须验证 |
| --- | --- | --- |
| ENTRY-A | API Owner；snapshot interface/impl、新独立 requirement controller、新测试；不碰 finalization/grant/Chat schema Writer 路径 | owner/client/tenant 大小写精确隔离、原文/摘要、当前 revision 而非默认 1、根锁一致读、无写/Provider、缺快照/漂移错误、no-store |
| ENTRY-A2 | API Owner；owner-safe assignment/binding/initial-request 纯读投影及显式初始操作合同，待grant Writer交接后分配 | 不把内部reconcile当公开查询；assignment/首轮精确对应；授权操作集合与本次初始操作分离；旧请求兼容及不多建execution |
| ENTRY-W | Web Owner；独立 point-and-start composable、TaskActions/JuyiHall 连接、定向测试 | 原键持久/readback、unknown/remount/显式恢复、精确 Agent/inputs、grant≠task、自动会话、身份/旧资金榜/多选回归 |
| ENTRY-I | 集成 Owner；exact candidate/source mapping 与浏览器证据 | 新点将真实进入 bootstrap、单首轮/单 execution、准备中恢复；有/无参考画鸟及34项产品用例逐项状态 |

并行写集须不重叠；Owner 自检，无独立 Reviewer。Java 验证经 orchestrator 串行；正式构建和发布遵循当前授权/版本策略。源码切片、真实启动、Provider 执行、部署、产品验收分别记录；达到完整出厂条件才通知用户“可验收”。
