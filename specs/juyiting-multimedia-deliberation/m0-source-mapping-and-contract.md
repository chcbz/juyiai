# M0：现有表/入口映射与可实施合同

状态：基于本分支 API `5c31ad48` 的实现前映射；下列 **新** grant、interaction、asset、CONVERSATION 用途均未上线。此文补充 [融合详设 v2](fusion-detailed-design-v2.md)，不替代既有 PRIVATE/TASK 正式交付或 `design.md` 的22项验收；只有各项实际源码、MySQL与联调完成才能从 proposed 改为 implemented。

## 1. 已存在且必须复用的权威事实

| 业务事实 | 源码位置 / 现有库表 | 新需求处理 |
| --- | --- | --- |
| 任务归属/版本/点将 | `agent/.../AgentServiceImpl.assignTaskInternal`；`agent_task_meta.task_version`、成员/work-item | 旧 `/agent/tasks/{taskId}/assign` 没有业务 grant/幂等办理含义；新 v2 办理必须从 JWT 身份重新校验 owner/client、版本和精确目标，在任务锁内保存有范围的授权。不得凭旧点将或 `allowQueue` 推导授权。 |
| 资料选择 | `agent_personal_workspace_task_file_link` 与 `agent_personal_workspace_conversation_file_link` | 参考图片使用 `fileId + fileVersion + role=REFERENCE`，同时校验最新操作主体、指定版本的可读性及任务/会话归属；只看文件名/展示卡不等于运行时已读取字节。 |
| 持久会话 | `chat_request/turn/context_snapshot/dispatch_outbox/conversation_event` | 新 interaction 复用唯一请求、用户消息和事件序列；`/chat/stream` 永不执行。既有 `chat_turn` 的 `uk_chat_turn_request_target` 在同请求同目标多步骤时不能重复建 turn；用关联的 step/executionIntent 记录后续办理，不制造第二套消息。 |
| Agent 运行/成果 | `agent_personal_workspace_execution{,_input,_output}` | `PRIVATE` commit 自动入个人文件，`TASK` commit 自动制作正式成果；两者都不是未归档会话试稿。引入明确 `CONVERSATION` 用途并保留 native START、run/lease/fencing；首先受 task grant 校验，commit 只登记会话资产/part，不静默创建个人文件或正式交付。 |
| 正式成果与用户决定 | `agent_task_artifact`、`AgentTaskFormalDeliveryController` / decision service | 在用户**选定最终成果**后，由受信业务适配器产生正式成果/提交并维持原 producer 校验；仅用户 JWT 能决定验收。text_final、asset.ready、提交、验收、任务完成各自独立。 |

## 2. 最小增量表与数据关系（DDL 必须以实施提交和真实MySQL核验冻结）

1. `agent_task_execution_grant`：`grant_id`，`tenant_id/client_id/owner_jiacn`，`task_id`，`requirement_revision`，`assignment_revision`，`target_agent_id`，`permitted_operations_json`，`input_scope_json`，`cost_authorization_ref`（可空=不得收费），`source_business_action_id`，`policy_revision`，`grant_version`，`state`，`created_at/revoked_at`。强制 scope+action 唯一/幂等；原任务重派/撤销在相同 task-root 锁内 CAS 变更为失效。任何浏览器/模型传入 `grantId`、`costAuthorizationRef` 均不是授予证据：服务端关联已经核准的授权。
2. `chat_interaction_step` 与 `chat_step_execution_link`：沿用 `chat_request` 身份/消息/seq；step 绑定 `request_id/turn_id`、task+assignment+grant+inputSnapshot、类型/状态/修订；link 唯一 `(scope,execution_intent_id)`、`(scope,execution_id)`，重投递先读旧 link，不能再次调用付费 Provider。跨 agent/chat 模块如果共数据库，用本业务事务/outbox；若跨库，显式可靠 outbox，绝不伪称原子。
3. `chat_conversation_asset` + `chat_message_part`：按 `(scope,conversation_id,generation,asset_id)` 及 `(message_id,part_id,revision)` 限定；指向已上传校验的 output/storage 引用与 byteLength/MIME/hash。`processing → ready` 只能在字节可读及身份/执行关联确认后发布；断线补拉沿用现有 conversation event 序列。
4. `agent_personal_workspace_execution` 当前 `chk_pwex_mode` **只允许 PRIVATE/TASK**，`agent_personal_workspace_execution_output.chk_pwexo_commit` 当前 **要求已COMMITTED就有workspaceFileId/version=1**，`chk_pwexo_publication_mapping` PUBLISHED 当前要求 artifact/formalDelivery。新用途必须显式迁移并更新这些约束与 mapper/service 的多处模式分支，CONVERSATION commit 不应假填 `workspaceFileId` 或复用 TASK 自动提交路径。
5. 个人保存创建自己的工作空间文件版本引用，会话资产保留其独立来源/保留引用；正式成果必要时复制到既有 task-artifacts-private 并核对同 hash。复用 workspace-private 与 task-artifacts-private，**没有第三个数据根**。

## 3. 调用顺序与失败原则

```
浏览器提交需求/点将（有或无参考图）
  → 服务端认证与 task/assignment CAS → 有范围 grant + bootstrap outbox
  → 同一悬赏议事只写一条原始用户消息 / 唯一 request
  → 有足够资料及授权且目标有真实生成能力：直接启动绑定 intent 的 execution
    或资料/意图不足：同议事提问，等待用户补充（不占生成 lease）
  → 精确版本只读领取 / native START / 提交真实输出 → 校验 asset.ready + part/event
  → 预览/下载/再编辑；用户可以选择保存到个人空间
  → 用户选定最终成果 → 原正式生产者校验与正式提交 → 用户身份验收
```

- 任何步骤只凭网络断线/返回404都不得再建执行。用户明确要求“重新生成”才产生新 intent；断线/刷新仅恢复原 request/run/asset。
- 读取、生产、commit、下载和重新点将竞争：统一按 scope + taskVersion + assignmentRevision + grantVersion 核对。旧 Agent 的晚到字节不能污染新 assignment；取消走真实协议，不凭前端按钮制造“已停止”结论。
- CHAT/状态查询不物化原始参考图片，也不启用执行工具；INSPECT 只能读已授权精确输入；EXECUTE 必须有 grant、capability 和实际费用/外发授权。两类 Agent 接应均如实声明能力，不将 legacy PRIVATE/TASK 能力冒充新办理能力。

## 4. 模块交接与未冻结项

- U1-A Agent 模块先实现 JWT/ACL + 任务锁/幂等/授权版本及撤销；不得在 `/chat/stream` 放开 `EXECUTE`。之后 Chat 模块实现一个 request 的互动 admission/step/状态投影，引用 grant 而不自行造权限。
- U2-A 改 output 模式/表约束、运行路径与 asset read，必须以真实 MySQL 8 测空/存量/重入/半途失败。音频 Range、保存、受信正式晋升及浏览器回归由后续工作包完成，不因为参考图选择器成功就标为完成。
- 尚须在 U1/U2 实施前以对应真实代码/DB测试冻结：task assignmentRevision 的权威持久字段、grant 唯一键的重派语义、旧机器 JWT tenant 兼容、Provider 费用授权的既有引用方式、正式 producer 的受信适配路径。这里列的是待实现的合同，不是运行中 endpoint 或已核准扣费。
