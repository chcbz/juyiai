# 原点将操作只读投影合同 v1

日期：2026-09-30。状态：**冻结施工合同；尚未实现/部署**。补充[入口详设](point-and-start-entry-design-v1.md)。复用已有 grant/bootstrap outbox，不新增消息/文件系统/执行，不把内部 worker discovery 当浏览器接口。

## 1. 接口与身份

`GET /agent/tasks/{taskId}/assignment-operation`，header `Idempotency-Key` 为原点将键。开关 `agent.task-deliberation-operation.read-enabled` 默认 false。

身份/参数规则与 current requirement 读入口相同：有效人类 owner JWT → 服务器 tenant `0` / client / owner；拒绝空、padding/control/unpaired surrogate、超长度 ID/key；taskId/key 不 trim、不转换成其他键。key 最多 100 个 code points。不得接受 owner/client/tenant query 参数，全部 error 和成功响应 `Cache-Control: private, no-store`。

scope + `ASSIGN_AND_START:` + 原键定位业务 action；同 scope 但另一个 task 的键不能返回该 task 的资料。GET 不 claim/reconcile outbox，不写表，不新建消息/grant/execution，不调 Provider。

## 2. Response

`JsonResult.success` data 仅含以下字段：

```json
{
  "schemaVersion": 1,
  "taskId": "task-123",
  "targetAgentId": "agent-123",
  "requirementRevision": "1",
  "assignmentRevision": "1",
  "taskVersion": "2",
  "grantId": "grant_123",
  "grantVersion": "1",
  "grantState": "ACTIVE",
  "permittedOperations": ["GENERATE_IMAGE"],
  "inputs": [],
  "bootstrapId": "bootstrap_123",
  "bootstrapState": "ADMITTED",
  "stateVersion": "2",
  "initialOperation": "GENERATE_IMAGE",
  "conversationId": "77",
  "initialRequestId": "initial-request-123",
  "currentAssignment": true
}
```

- 所有 long 字段以规范十进制字符串表示；requirementRevision/grantVersion > 0，assignmentRevision/taskVersion/stateVersion ≥ 0。schemaVersion 固定 JSON 整数 1。
- input summary 仅 `{fileId, version, purpose, contentMimeType, byteLength, contentHash}`；version 为正 JSON int，byteLength 为非负规范十进制字符串，hash 为 64位小写hex。不返回任何路径/lease/工具轨迹/token/费用凭据。
- permittedOperations 是持久 grant 的明确集合；initialOperation 是持久 bootstrap 的单次初始操作，并必须属于集合，不能从任意文本重新分类或制造。
- grantState：`ACTIVE/REVOKED/SUPERSEDED`。bootstrapState：`PENDING/CLAIMED/RETRY/ADMITTED/DEAD`，与原始事实一致，不把回执包装成生成完成。
- ADMITTED 必须有已记录的 conversationId/initialRequestId；其他状态两者必须 null。ADMITTED 只证明 Chat 受理，不证明 Runtime START/字节/交付。
- currentAssignment 仅在原 grant 仍 ACTIVE、root 当前目标匹配、持久最新 TASK_ASSIGNED 的真实 assignment epoch 对应原 grant 时为 true；不得拿 taskVersion 等于 assignmentRevision 作替代。root taskVersion 可因其他事件前进。
- 原操作被撤回/重新点将时仍可按原键只读核对历史 facts，但 currentAssignment=false，客户端不自动把原操作作为当前新任务办理。这个字段**不是执行授权**；dispatch/START/input/output 仍重新准入。

## 3. 数据与一致性

锁顺序与任务写入口保持 root 首先：认证 owner-scoped task root → 原 grant action → 原 bootstrap action；只读元数据/不可变 snapshot 可在 root 锁内读取。沿用现有 DAO 的精确 binary scope/action 条件；校验返回记录的 exact scope/task/action/grant/revision/target 关联，不因为 SQL 返回非空就信任。

核对：grant requestHash 合法、输入/操作 JSON 结构有效，bootstrap 现有 canonical payload/reference hash 校验通过，outbox 所记录 grantVersion 在 1..当前 grantVersion 范围，需求 snapshot exact revision/摘要归属有效。stateVersion 是 outbox version，grantVersion/taskVersion 是独立 fence，不能用一个 version 代替三者。持久字段不完整/漂移时失败，不伪造待办来掩盖缺失。

| 状况 | HTTP/业务码 |
| --- | --- |
| 没有 owner JWT | 401 / `ASSIGNMENT_OPERATION_UNAUTHENTICATED` |
| 非法参数或身份-looking query | 400 / `ASSIGNMENT_OPERATION_BAD_REQUEST` |
| 缺/foreign task，或原 action 在该 owner task 下不存在 | 404 / `ASSIGNMENT_OPERATION_UNAVAILABLE`（相同通用信息） |
| 记录完整性/关联/epoch 损坏 | 500 / `ASSIGNMENT_OPERATION_INTEGRITY_ERROR` |
| 实际数据库/事务/依赖不可用 | 503 / `ASSIGNMENT_OPERATION_SOURCE_UNAVAILABLE` |

## 4. Web 恢复与会话接入

Web 在首个 POST 前持久/readback原键+body，查询永不写。GET 暂时404不证明原POST没被受理；刷新不自动POST。用户明确恢复时可在404后复用原键/body POST；401/403/500/503/坏回执不触发写入，既有PENDING/CLAIMED/RETRY/ADMITTED只继续只读核对。

核对投影与原task/目标/revision/精确 operations/inputs；outbox、grant、root的各自 fence 不回退。同 fence 的不可变事实改变或已确认ADMITTED回退必须拒绝；独立root/grant推进不能错误地当作同outbox版本冲突。

ADMITTED + currentAssignment=true 后仍先GET canonical task，再以确切会话与首轮 request ID 读取Chat。校验request的conversationId、steps中的task/assignment/target，再装载同一会话历史/事件；不从列表取第一条当证明，不补发首轮、不读本机文件、不仅本地标assigned。

## 5. 最小验证

Owner 自检：JWT/header/query spoof；owner/client/tenant case/padding exact；同key另task；缺根/缺action/缺grant-or-outbox一致性；真实输入/payload hash；当前assignment与其他taskVersion事件区分；撤权/重派历史可核对但不自动开启；版本精度；ADMITTED IDs/非ADMITTED null；no-store、无写/claim/Provider。测试selector复用既有bootstrap套件并明确折中，不替代真实MySQL/安全链/浏览器。
