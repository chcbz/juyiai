# U2 轻量议事与会话输出基础整合（2026-09-29）

特性分支 `codex/juyiting-multimedia-deliberation` API exact commit `9180da1710142cbe1dc3bdef6fc45035f35018ae`，tree `e6d1008b096c9177e0a12dbe98e1348289763ef8`，已推送远端并读回相同 SHA。该基线在 Chat/** 合入无 `actionProposal` 的普通议事接入，在 Agent/** 合入 conversation-only 输出的关闭态基础；不是完整多媒体交付，也未合入组件 `develop`。

- v2 `/chat/conversations/{conversationId}/interactions` 在默认关闭的开关下分流：无 proposal 且无未经校验资料的普通讨论 → fast CHAT 持久 request/turn/outbox，禁止借用执行工具；明确 proposal → 原有待执行 step/link，仅表示 `PLANNING`。返回共同的 requestId/statusUrl/状态，不把“聊天回复”解释为图像已生成。议事受理按 owner 任务根 → bounty binding → 会话加锁，对当前目标和 assignmentRevision 做检查；普通任务版本增长不误判重新点将。浏览器传入的未知 inputRefs/replyTo/continuationOf 仍拒绝，不宣称可传图。
- Agent/** 的 conversation output 仅为基础存储/受控读取候选，执行仍默认关闭；由独立 Owner 验证了 `scopeType=bounty`、`scopeKey=task:<taskId>` 的作用域，拒绝其它 scope。MySQL 8.0.21 隔离实例只验证增量 DDL/CHECK/部分 SQL 回滚，**未**证明 Java 服务真实并发事务/生产迁移。
- 本次 exact 集成 tree 经全局串行 orchestrator 执行 `:agent:jia-agent-service:mmdU2ConversationOutput` **2 classes / 10 tests**，`:chat:jia-chat-service:chatDeliberation` **22 classes / 107 tests**，两者均 0 failures/errors/skips；日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u2-integration/gradle-9180da17-attempt1.log`，evidence key `507e10a8e47f60471e9faf5887180cd0564641e5babc5d2409372ac04d0d2d21`。两个配置失败尝试在 `evidence/u1-chat-discussion/` 留痕，成功运行使用本地非发布 init（不是 Flow 运行）。

**仍须完成**：自然语言意图判断/澄清、精确资料与前稿 ACL resolver、grant/付费授权与执行协调、Agent native START 的持久 lease/fence 与续期/过期重领、真实字节媒体及受权预览下载、空间保存、正式交付/验收、客户端两种接应、DB 服务级事务和真实浏览器画鸟验收。不得在这些缺口消除前开启执行/声称上线；Web/Client pin 暂不变。测试账号凭据不进入日志或提交。
