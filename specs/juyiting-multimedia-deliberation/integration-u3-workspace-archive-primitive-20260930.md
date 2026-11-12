# 会话成果归档的个人工作空间原语（2026-09-30）

API `codex/juyiting-multimedia-deliberation` 已快进并远端回读 `39a7aa4539572f180eb2c4a344b0dd0dc1597ff6` / tree `8eeec7e91cc6d5684d8b9f0d5650d82ecc242ee4`。本切片在既有 `PersonalWorkspaceService` 中新增**仅供可信服务端调用**的 `archiveConversationAsset`：先核实传入的不可变 asset ID、revision、内容 SHA-256 与实际字节一致，按 owner/client/tenant 作用域写入已有私有对象存储，写入个人文件版本与可查询操作回执，来源标记为当前 schema 允许的 `AGENT_DELIVERY`；幂等操作将 asset/revision/hash 和目标文件元数据一起固定，相同键的其他稿返回冲突。复用现有存储根，不新增第三套文件系统；不修改个人空间的浏览器上传入口。

Owner 范围内验证：经 `/home/isp/wsps/cyf/ops/orchestration/cyf_orchestrator.py gradle` 串行执行 `:agent:jia-agent-service:v1131Regression --tests cn.jia.agent.service.impl.PersonalWorkspaceServiceImplTest`，JUnit XML **8 tests / 0 failures / 0 errors / 0 skipped**，包括本次新增来源哈希/幂等重放/跨身份拒绝/实字节读取用例。首次缺发布仓库*非敏感*构建占位参数、第二次冷编译进程被内核 OOM 杀死（pid 1676611），归因后在同一源码树以 512m Gradle heap、单 worker 完整通过；无生产构建、MySQL/浏览器或付费调用。运行任务 `MMD-U3-WORKSPACE-ARCHIVE-20260930`，证据缓存 key `4b1cd5c130370c010ae84a33c8b570ea08cc64ed15eda313572bc5e29a36c61b`。

**尚未完成**：Chat 端仍需在同身份会话上以受信关联核验 asset/part/原 run → 读取原字节 → `POST /chat/conversations/{id}/archive-operations` 接入本原语并持久关联 operation/asset，支持刷新后 `GET` 归档状态和同资产不同键防重复、失联恢复。当前只有低层原语，不对浏览器开放新路由，不能显示“保存成功”或通知产品验收。现有存储白名单还未覆盖所有音频格式，后续扩展需经存储格式与预览能力核验，不得把未支持格式标已归档。
