# U2 会话执行 lease 与点将 epoch 集成（2026-09-29）

组件 API 特性分支 `codex/juyiting-multimedia-deliberation` merge commit `988f426f1117dddefe869562987377b69990eb5b`、tree `3b44038ec371475e1584f0aaa45bffc1a58bcc95`；将 Agent Owner 提交 `8c970264744124518895a7c20e4eef8bd0e8e795` 与 Chat/Agent 当前特性基线合并。经 push 和远端 readback 同一 commit。仅研发特性分支，未合 develop。

- 会话执行 native claim 建立基于 task root → grant → execution row 的受控 lease，携带 runtime 实例、版本、token 和实际到期时间；续期/分段输出/提交/失败要求匹配 fence，超期重领轮换 token。默认 `jia.agent.conversation-execution.enabled=false`，原 `/internal/agent/tasks/.../start/outputs/failure` 不得借无 fence 旧路由承接会话执行；这不是新的可用 runtime HTTP 入口，**当前客户端仍不能实际领取会话执行任务**。
- 点将 epoch 用当前最新 `TASK_ASSIGNED` 事件及 active grant 验证，不把会因普通任务状态更新而增长的 taskVersion 当作 assignmentRevision；重指派/撤权后重新检查，不能仅凭相同 Agent ID 判断。
- 合并冲突的取舍：保留新 lease 及拒绝旧路由，保留最新 Chat 受权图片意图/下载候选；新增“分配给其他 Agent 的 task root 不得生成执行”回归。MySQL v1.15 lease schema 增量原样保留，未在本集成树跑真实 Java/MySQL 事务。

本地用户授权的**非发布**定向测试均经 `python3 ops/orchestration/cyf_orchestrator.py gradle`、同一 exact tree 串行执行：`:agent:jia-agent-service:mmdU2ConversationOutput` 2 classes / 16 tests，`:agent:jia-agent-service:mmdU1Grant` 3 classes / 18 tests，`:chat:jia-chat-service:chatDeliberation` 23 classes / 112 tests；各 0 failure/error/skip。日志位于 `evidence/u2-integrated-lease-988f426f.log`（cache key `98ca860306323b68d68df1a6d8780f814a42f1191889ac357c92b6a0dd20eaab`）及 `evidence/u2-integrated-chat-grant-988f426f.log`（key `ffa399a97f7f47dc0dd58ed343d1816bb9d722a1339dc86120ebd30d6089e29d`），相对于 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/`。Agent Owner 的隔离 MySQL 8.0.21 lease/CHECK 实验在 `evidence/u2-conversation-output-agent/mysql8-v1_15-check-fixed.json`；不能代替本集成树的实际服务事务与升级迁移验证。

**未完成**：认证 native lease HTTP/WS 合同与 Client 适配、受权执行自动编排与澄清/资料解析、会话资产清单与 part.ready、真实图片、工作空间归档、正式交付、真实浏览器及发布。没有 Provider 调用/付费操作；本步骤不支持宣布“可验收”。
