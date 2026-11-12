# 需求创建与可选参考图：原子受理合同 v1

日期：2026-09-30。本合同追加长期详设的需求前参考图入口，不改变旧 `/agent/tasks` 或已冻结的点将合同。**施工合同，不代表已部署。** 新入口只创建普通需求及资料关联，不点将、不创建 grant、不启动 Agent、不收费。

## 1. 用户与接口

在尚无 taskId 的需求草稿中，可从本人工作空间选择 0–32 个 JPEG/PNG 精确版本，也可空选。32 与 INT 版本沿用现有 point-and-start/input manifest 合同，不另设性能门槛。草稿 refs 精确为 `{fileId,version,purpose:"REFERENCE"}`，不能传 URL、本机路径、owner、任意 MIME 或 latest 指针。

```http
POST /agent/tasks/creation-operations
Idempotency-Key: <原操作键>
Content-Type: application/json
```

正文允许且仅允许：`title,description,requiredAbilities,reward,inputRefs`；title 必填，其余按既有普通 task 原始需求验证规则，inputRefs 缺省/空列表均代表无参考。不接受 funding、cost、grant、target、身份、执行字段。title/description 保存完整原文，不按 task_plan 的30/200投影限制拒绝原文，也不悄悄截断原需求。

```json
{"title":"画一只鸟","description":"照片风格","requiredAbilities":[],"reward":null,"inputRefs":[{"fileId":"pwf_x","version":2,"purpose":"REFERENCE"}]}
```

成功 201（同键同正文 replay 200 亦可；Web 接受两者），raw JSON、`Cache-Control: private, no-store`：

```json
{"schemaVersion":1,"operationId":"atco_x","taskId":"42","requirementRevision":1,"state":"COMMITTED","inputRefs":[{"fileId":"pwf_x","version":2,"purpose":"REFERENCE"}],"task":{"id":"42"}}
```

`task` 是真实普通 AgentTaskDTO，绝不是 grant DTO。task.id 与 taskId 必须相同；requirementRevision 是同事务 captureOnCreate 验证的1，不由 Web 猜值。Receipt refs 是当时固定的选择，不因 latest 更新改写；文件后来不可读不伪装当前仍可读。重放/查询可返回当前授权 task 投影，但不可重建任务、复活已解除链接、替换资料或启动执行。

```http
GET /agent/tasks/creation-operations/request
Idempotency-Key: <同原键>
```

只读同身份原操作投影，同一响应结构。未知键404不证明原POST没有受理；刷新/remount仅GET，用户明确“继续原张榜”才复用原key+原body POST。不自动新键、不提交当前编辑稿代替原稿。GET不claim、不补写或发事件。

错误 raw `{code,message}`：400 `BAD_REQUEST`，401 `UNAUTHENTICATED`，403身份范围无效，404 `TASK_CREATION_NOT_FOUND`（任务/原操作/参考版本不存在或不可读），409 `IDEMPOTENCY_CONFLICT`，503 `TASK_CREATION_UNAVAILABLE`（实际存储/事务依赖不可用）。不能暴露私有路径、输入正文、凭据。所有错误 no-store；未知500亦按未知结果处理。

## 2. 服务端事实与原子性

认证 scope 仅当前 JWT + EsContext 一致的 tenant=0/client_id/jiacn；body/key/resource 不是授权。旧普通与 funded 入口保持原语义，不把资金榜恢复/扣费凭据挪给本流程。

新增一张小型 `agent_task_creation_operation` 元数据表（不是新的文件存储）：身份/原键唯一、opaque operationId、requestHash、state、taskId、requirementRevision、inputRefsJson、createdAt/completedAt。它只记录创建意图与确切回执；不另建 workspace/assets/grant/run 表。DDL为可重入 additive CREATE，不迁移或写现有任务。

单个 REQUIRED 事务内按序：
1. 严格解析/验证scope、原键、完整原文和 refs；固定排序与 payload hash。title/description 保持 null/空字符串等原始语义；同正文refs排序不制造不同任务，重复tuple拒绝。
2. 插入或等待原键唯一行，`SELECT ... FOR UPDATE` 得到当前归属；同键异hash409。同键已COMMITTED只读现有task回执，不调用 createTask/link。
3. 复用现有代理 `AgentService.createTask`：保留任务root预留/rekey、完整original snapshot、event/outbox及after-commit机制，不直接写task_plan或用伪造taskId。
4. 验证创建的任务当前owner、原始requirement snapshot及revision；对每个 refs 使用既有task/file row锁、ACTIVE/精确版本/本人scope校验。JPEG/PNG MIME取真实version metadata，不信body；创建既有 REFERENCE task-file link并核对精确返回。
5. 记录COMMITTED任务/refs回执并提交；任一引用、领域或operation CAS失败，任务/plan/snapshot/links/事件与operation一起回滚，不留部分榜文、不有“成功但没有资料”。

禁止 REQUIRES_NEW claim/链接提交造成跨事务孤儿；Provider、上传等长操作完全不进入该事务。未提交reservation对GET不可见，网络未知必须显式按原意图恢复。读/重放仍校验当前任务归属；identity切换不得展示旧响应。

## 3. Web

- 候选选择器只读 list/detail/version/authorized Blob，不写 task/link；确切选择提交给实际创建流程。
- 同身份 durable creation intent 包含原 key 和完全固定正文/refs，持久失败/损坏不按空记录处理。认证scope由现有实际 auth generation 派生，换身份清屏/fence迟到写回。
- 新张榜点击若存在未决原操作，显示原正文/refs恢复入口，不自动重复提交。remount/刷新不POST；查询失败/404保留意图。一次在途操作互斥；只读核对或明确原键重放，不允许两次点击分配新key。
- 回执必须验证精确taskId/revision/refs/identity，才可更新任务列表/选中和清除原意图；未知/错误回执不本地伪报成功，不清空当前草稿。
- 创建成功后的点将采用refs须读取既有真实task-file目录和capability政策，不能仅凭draft放开当前 EMPTY_ONLY。该点将接入另包验证；本包不宣称画鸟完成。

## 4. 最小实际验证

空参考、一个/多个精确版本、long Unicode原文、同键重放零第二task、同键异正文/版本409、不同owner/client同key隔离、文件TRASHED/他人/不存在/错误MIME拒绝、第二ref失败全事务回滚、并发原key等待、commit失败回滚、GET零写及当前task归属。真实MySQL DDL重入、唯一键/精确大小写及代理事务回滚夹具；不能以mock调用顺序替代实际事务。Web覆盖 remount纯GET、404不清、显式原key/body、快速双击、损坏storage、identity/async fence、真实Bounty页面草稿与回执绑定。

Owner按exact commit/tree/selector/fixture自检；Gradle由orchestrator串行。不做生产迁移、付费调用或独立Reviewer；source PASS与产品验收分开。
