# 持久会话资产整合与验证

日期：2026-09-30。API `05575ae39d31476f08b1ec8ad1f1c824cb3a8e69` / tree `04ef4e3422d0b37e74e2c8230a41f19d2efc3956` 已 fast-forward 合入并推送 `codex/juyiting-multimedia-deliberation`。Web 保持 `4e321ea6303d3523f9a181cab61474da69162f81`。这是源码切片，不是产品验收或发布证据。

## 实现范围

- `ChatBountyAssetProjector` 从已提交的 CONVERSATION execution 读取可信输出目录，核对 owner/client/tenant、request/step/task/Agent/run 及当前会话 generation；不读取模型给出的媒体路径或摘要，不调用 Provider。
- 根任务/grant 检查在前，会话锁在后；事务内创建真实助手消息、`chat_conversation_asset`、媒体 part 与 durable `agent_message` 事件，提交后才通知在线订阅者。历史 GET 从持久关系读取 parts，不采信消息 metadata 伪造媒体。
- `step/output` 唯一约束、当前锁定读及 step stateVersion CAS 防止重复投影。MySQL REPEATABLE READ 下不能只依赖先前快照；会话锁后用 `FOR UPDATE` 读取既有资产。
- `ChatConversationAssetController` 提供精确资产详情与私有 GET/HEAD/Range；每次仍经过现有受权输出读取重新核对真实 MIME/长度/摘要，保留合法 416。不公开 Agent 工作目录、内部凭据或裸存储路径。
- `ChatBountyAssetRelay` 默认关闭；后台补齐已提交成果，不产生新的生成意图。撤权/源不存在不会阻塞其他 owner 的投影；其他未变失败连续出现时停止并记录，不能吞错伪报成功。
- 新 DDL 及 initializer 验证 `chat_conversation_asset` 的 scope FK、来源唯一性及列/索引。启动前须一起核对 `chat.bounty-asset.enabled`、受权媒体组件、依赖 schema 与私有存储配置；本切片未开启生产配置。

## 真实证据及局限

1. exact API/tree 经串行 orchestrator 验证：`chatDeliberation` **30 类 / 157 项 PASS**，0 failure/error/skip；`bf08FormalFlow` **60 项**使用未变测试输入的 UP-TO-DATE 结果，并非声称重复执行。构建终态成功。详见[XML摘要与校验和](integration-evidence-20260928/u3-durable-assets-local-verification-20260930.json)。
2. 本线程独立 MySQL 8.0.21：DDL 重入保留记录，step/output 唯一性和 scope FK，owner/generation 隔离，实际 archive 源查询及 RR 旧快照后的当前锁定读通过。详见[MySQL回执](integration-evidence-20260928/u3-durable-assets-isolated-mysql-20260930.json)与[固定目标夹具](fixtures/verify-durable-assets-mysql.py)。夹具不连接生产，不复用已有 schema；已有 fixture 不应盲目重跑。
3. `git diff --check` 通过；原不完整候选工作树保留不动，只整合已验证的完成候选。源码自检，无独立 Reviewer。

MySQL 证据为 synthetic SQL，不替代真实 Spring 并发事务、Provider 和浏览器。没有生产迁移、正式构建或部署；产品 AC/FD 仍 NOT_RUN。

## 尚未闭合的合同

- 成果区保存仍发 `mode=CREATE/outputRef`，Chat 归档只接受 `mode=create/items[].assetRef`。应由服务端提供 output → persisted assetRef 的只读、owner-scoped 精确映射，前端复用既有 `useHallConversationArchive.js`；尚未投影时等待真实资产，不伪造引用或摘要。
- 正式 `finalizations` 编排尚未实现。正式成果晋升、用户验收和任务完成不能由一个前端成功按钮替代。
- 有参考图/上一稿修改、澄清续办、双接应、真实多媒体及全流程浏览器验收仍需逐项核验。只有全部目标功能、exact 版本发布和真实验收证据满足后才通知用户可验收。
