# U1 后续会话交互入站增量（2026-09-29）

**特性分支源码自检，非聊天/澄清/真实图片执行或产品验收。** API `codex/juyiting-multimedia-deliberation` 已推送并从远端读回 `3e707504a9dc564931f91aa062ffe5cff8f4b7b5`，tree `8ae5005427f4b1f67f2047c1990abe262c8e83f7`；SDD 的 API gitlink 固定到同一提交，Web/Client pin 不变。

- 独立 `POST /chat/conversations/{conversationId}/interactions` 控制器，**默认关闭**（`chat.bounty-interactions.enabled` 未设置时无路由）。只有 v2 明确的 `generate_image/edit_image/generate_audio/edit_audio/inspect_inputs` proposal 准入；无 proposal 的对话/澄清路由尚未实现，不能称为完整统一入口。`/chat/stream` 原 CHAT/INSPECT、禁止 EXECUTE 的边界不变。
- 以认证主体解析 tenant/owner/client/sender，后端验证 owner-scoped、live bounty conversation 与 task，先在任务锁下核验当前 grant/assignment/Agent/操作，再核对绑定行和会话行锁；同一 Idempotency-Key 固定一条 USER 消息、一条 request、step、无 executionId 的 intent 与持久状态事件。重领返回原状态，不创建第二次执行。拒绝未受控 `inputRefs`、replyTo、continuationOf，直到精确资料/会话 asset resolver 落地；不能将浏览器引用视作已读素材。
- 请求返回 `PLANNING` 仅表示入站已提交；本增量**不**运行执行 coordinator/native START/Provider，不产出图片/音频、不实现空间归档和验收。自动 bootstrap worker 依旧默认关闭。后续必须对付费 Provider 再核对已有明确付费授权；本次 grant 准入使用 `paidExecution=false` 绝不是付费权限。
- API exact tree 经 `/home/isp/wsps/cyf/ops/orchestration/cyf_orchestrator.py gradle` 串行 `:chat:jia-chat-service:chatDeliberation`：**20 classes / 96 tests、0 failure/error/skip**。原日志：`/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-chat/followup-3e707504-attempt3.log`；key `cdc76c04ffd9c986d78849bf2d1b824b3a9887709b7fcc3794c7d36f3e76e9cf`。前两次失败：首次未提供 build.gradle 读取的非敏感 publishing 占位变量、未编译；第二次 96 项有 1 项测试夹具 Mockito restub NPE（不是服务），已修测试夹具后复测通过；原失败日志 `followup-099c0507-attempt1.log` / `followup-099c0507-attempt2.log`，不得改写为通过。

**继续施工**：可信资料/上一稿精确 resolver、无 actionProposal 的服务端讨论/澄清、受控执行分发与成本授权、字节支持的会话媒体/预览下载、选择性归档/正式成果/验收、实际 MySQL 事务与存量迁移、双接应模式、版本发布及真实浏览器画鸟。功能开关不得在缺失后端执行与恢复能力时开启；现阶段所有产品 AC/FD 用例仍未执行。
