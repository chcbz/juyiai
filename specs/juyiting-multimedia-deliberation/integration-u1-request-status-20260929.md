# U1 会话请求状态/回放增量（2026-09-29）

API 多媒体特性分支 `codex/juyiting-multimedia-deliberation` 推送并从远端读回 `9670756adda18b98cc38046dc33ed497eade595f`，tree `4f43e2beca2b26f16c46af74bb7b7f6e46b5ba7f`。SDD API gitlink 固定同 SHA；Web/Client pin 不变。

- 在**既有** `GET /chat/requests/{requestId}` 的 `RequestView` 中新增 `steps[]` 只读投影（请求 scope + 会话存活/代际校验、step/link 的 tenant/owner/client/conversation 逐项校验）。执行意图未绑定运行时返回 `executionId=null`、`executionState=WAITING_ADMISSION`，`state=PLANNING`；绝不从文本结束或一条入站事件推断生成成功。既有 CHAT 请求返回原字段和空 `steps[]`，不把旧 CHAT 重新解释为执行。
- v2 planning 请求缺少 step、EXECUTE 缺少 link 或 scope 不符时 fail closed，不返回虚假完成状态；同幂等键 replay 对 requestRevision/step/link 校验，历史授权撤销后的重领不产生第二次意图。人类身份解析失败返回受控不可见，不泄露身份细节。
- `chat.bounty-interactions.enabled` 和 bootstrap worker 仍**默认关闭**。无自动协调、native START、Provider 回复、字节媒体/预览下载、精确归档/交付/验收；`/chat/stream` 的 CHAT/INSPECT/执行禁止边界保留。另有 Agent/** 隔离候选未通过测试，未整合于此 pin。
- API exact tree 经全局串行 orchestrator 定向 `:chat:jia-chat-service:chatDeliberation`：**21 classes / 102 tests、0 failures/errors/skips**；原日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-chat/request-projection-9670756a-attempt1.log`，evidence key `d525740de22f99506b070bdf9a48259f22d73a1abee27e76e8f6a17a57e69061`。这不是 Java/MySQL 并发、生产构建/版本发布或浏览器验收。

**后续**：接入可自动处理无 proposal 的讨论/澄清、精确材料 resolver、授权的执行分发和事件/字节媒体，再完善归档/正式交付/验收及真实浏览器两种接应验证。AC/FD 产品用例保持 NOT_RUN。
