# U2 会话输出清单读取候选（2026-09-29）

API feature exact commit `678c326372daa8d1eee88f64dbfbe6d34f71ea57` / tree `7bfbcf6938c0839c60240c3971fd19bf467a9c4b`；从已测试的子工作树无冲突快进到 `codex/juyiting-multimedia-deliberation`，远端 push/readback 相同 SHA。仍默认关闭 `chat.bounty-media.enabled`，未合 develop/部署。

新增 `GET /chat/requests/{requestId}/steps/{stepId}/outputs`，在现有 owner-scoped request→step/link→CONVERSATION execution 闭环成立时获取会话输出列表，不接受来自浏览器的 execution/run/owner/storage URI。Agent 从 task root、活动授权、锁定执行及受限输出行逐项查验字节 SHA-256、长度，才返回 outputId/MIME/hash/长度；Chat 仅为可信 inline MIME 返回需用户认证的预览 URL，未知 MIME 只返回强制下载 URL。原字节接口仍在实际点击时重新校验，不以列表或 Agent 自报 URL 当完成事实。当前只补“发现 outputId 与受权预览/下载链接”，**还没有产物自动关联、part.ready、真实浏览器图片或工作空间归档**。

精确树本地定向 `:agent:jia-agent-service:mmdU2ConversationOutput` 2 classes / 17 tests 和 `:chat:jia-chat-service:chatDeliberation` 23 classes / 114 tests，均 0 failure/error/skip。首个冷构建于 2026-09-29 15:57:42 +08:00 被主机 OOM 结束，journal 中明确 pid=1345324 的 Gradle daemon（约 1.13 GB 匿名 RSS）；日志 `evidence/u2-output-catalog-678c3263.log`，不是测试通过。归因后同一树以单 worker 和有界本地 Gradle/Test JVM 重跑成功，日志 `evidence/u2-output-catalog-678c3263-lowmem.log`，orchestrator 证据 key `34d39f1b6ce58c08c9b0ea1bcb0b4cee36b1c47905ad72ecdcee0f16786dbdcb`，不将这个本地改动当线上门禁或 Flow 成功。

剩余关键路径：持久关联真实执行输出与议事 part、服务端自动执行协调、Agent/Client 受认证 native fence 传输、可选参考图/上一稿、保存空间和正式交付，真实 Provider 授权及浏览器端到端。尚不可通知产品验收。
