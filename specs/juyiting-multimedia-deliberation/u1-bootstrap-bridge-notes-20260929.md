# U1 点将 → 悬赏议事可靠桥接：实现边界与待验事实

日期：2026-09-29。状态：特性分支增量设计，**未完成自动投递/执行/浏览器验收**；不替换 `fusion-detailed-design-v2.md` 的业务合同。

## 已有候选和证明范围

- Agent 候选 `c9c54e5e31ed08191cae11b659434d4b4c81f156`：在任务根事务里记录 assignment、grant 与 owner-scoped `agent_task_bounty_bootstrap_outbox`；事件键为 `(tenant,client,owner,sourceBusinessActionId)`。`claimNext(scope,consumerId,now)` 与 fenced `reconcile(scope,command,now)` 只对**已知确切 owner scope** 工作；`ADMITTED` 只证明 Chat 持久受理，不证明模型/执行/媒体成果。
- Chat 候选 `414612780f057d40961e406e080f6b782da151b3`：`ChatBountyConversationService.ensure` 经服务端 grant 校验、唯一绑定、尝试安全收养旧会话并处理重复点将/重派；`ChatBountyConversationServiceTest` 4/4 在 exact tree `3528ccb1adfe19a3c3a46643b1b55bed57905077` 通过（本地定向，非 Flow、非 MySQL 迁移/浏览器）。
- **二者均未合入 API 主特性树/develop**；不能把上述两段代码视为已经实现初始需求消息自动投递。

## 必须补齐的桥接合同

1. **后台发现**：Chat 后台消费不能依赖用户保持页面打开。当前 owner-scoped `claimNext` 缺可信待办 scope 发现机制；应在 Agent 服务内提供私有的、行锁/租约保护的待办发现或最小的 internal claim-any（仅受信服务、受控调度），由已持久 outbox 行确定 `tenant/client/owner`，不可让浏览器传任意 owner。不要枚举用户、扫描所有任务或凭消息标题猜归属。队列中还需可观测的 PENDING/RETRY/DEAD 对账；尤其 discovery SQL 排除空白/异常 owner 的行后，该行会留在 PENDING 而非自动 DEAD，须告警并单独按 scope 修复/隔离，不能静默失联或让坏行挡住其他 scope。
2. **Chat 入站幂等**：claim 的 `sourceBusinessActionId` 固定初次受理键；每次重领先查同键请求+conversation，再根据 grant 当前版本和 task/assignment/scope 复核。会话绑定、唯一初始用户消息、request/turn/快照/dispatch 意图与可恢复回执按事务边界定义；断线、lease 超时不得重复发起有费用的 run。`ADMITTED` 在 Chat 上述事实提交后才能 `reconcile`。
3. **需求与资料**：Agent outbox 只有 `taskId + requirementRevision` 锚和精确素材摘要，绝不存正文；Chat 从可信 owner/task 读当时版本的原文和允许资料内容/目录，版本不匹配 fail closed（等待修订对账，不把最新标题冒充旧需求）。**当前代码核查**：`AgentTaskExecutionGrantServiceImpl.validateAssign` 只校验客户端 `requirementRevision>0` 并持久该数字；Agent 侧尚未定位对应正文的不可变版本/owner-scoped 历史。仅凭 outbox 锚无法重建早先原文，自动消费前必须在 task-root 事务冻结需求正文+摘要（或证明已有权威版本源并逐字节读取），并使 revision 服务端产生/校验，而不是信任客户端自报。读取素材仍要逐条 ACL、版本、摘要验证，聊天轻量 profile 不因附件存在自动加载字节。
4. **旧入口并发**：`/chat/stream` 经通用 `ChatConversationServiceImpl.create` 仍可能创建 bounty 会话。仅有新 `chat_bounty_binding` 唯一键**不能**证明历史/并发入口全局一个会话；迁移/并发测试须覆盖旧会话与新点将交错、重复/重派、软删除后恢复。上线 v2 前要么旧创建路径与 binding 共用事务锁/唯一键，要么收敛为受控旧语义并提供兼容迁移，不能静默产生两套聊天。
5. **删除/重派**：旧会话软删除后绑定不可指向不可读行又另建同 task 会话。重派旧 grant 与旧目标后续 dispatch 必须重新准入并隔离；用户已经保存/正式交付的内容不可因撤销 grant 或删会话丢失。
6. **路由与成果真实性**：初次“画一只鸟”需经 v2 interaction admission/受控 execution，不能调用原 `/chat/stream` 的 CHAT/INSPECT 当作生成成功。明确交互的 clarify/answer/execute/status、真实 bytes-backed 图片 part、可预览/下载、用户手动归档、正式提交和验收仍各有独立事实。

## 验证出口

在合入主特性分支前补：Agent selector、Chat selector 和 schema；MySQL8 空库/旧库迁移两次及 owner/client/tenant/软删唯一性；相同意图并发/claim 过期/崩溃重领/旧入口并发；两种接应的 profile/实际产物；真实用户授权的浏览器“画鸟→预览/下载→保存→交付→验收”。本地结果不构成发布证据；按当前授权的版本发布链记录 exact SHA/tree、测试、制品摘要和实际健康。无这些证据不得提示用户验收。
