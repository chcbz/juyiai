# 个人工作空间与会话资产：音频/新图片格式保存与预览（2026-09-30）

API 特性分支 `codex/juyiting-multimedia-deliberation` 已快进推送到 `f95d470bdaeeb1074f3f38daa061dd3d7fa3c08d`，tree `47e70750fafc03be469915310e0e0a51b4f4e85d`。研发子分支 `codex/juyiting-mmd-workspace-multimedia` 亦已推送、回读。

- 原有 owner/client/tenant 限定、归档摘要校验和源 revision/幂等规则保留。个人工作空间可接受由部署存储配置明确允许的 `audio/mpeg, audio/ogg, audio/wav, audio/mp4, audio/webm` 与 `image/webp, image/gif`，按 MIME/扩展名对应生成持久版本。列表新增 AUDIO 分类；私有预览 part 返回原始字节供浏览器解码，下载依然走原有认证、`nosniff` 和附件接口；HTML 仍不支持。
- Chat 归档服务对同一批 MIME 输出选择固定安全扩展名，拒绝其余类型。不在新目录复制文件，也不把模型返回路径/MIME 作为可信内容。现有工作空间物理存储仍以配置中的 `allowedMimeTypes` 为最终边界；**源码许可不意味着生产配置已启用**。
- 本地串行 orchestrator 在该 exact tree 验证 `:agent:jia-agent-service:v1131Acceptance` 两类用例 **11+9=20/20**，`:chat:jia-chat-service:chatDeliberation` 三类归档用例 **10+6+4=20/20**，XML 0 失败/0 错误/0 跳过。证据缓存分别为 `af47e4716cec651b4a96ba8335e7366285a4ccb92a5b93f49f2cc1ab68c3730a`、`2733f3559ffd772abb8826eec6cfb328b6a09f28966cf08f1f717e24533f66d4`。Gradle 使用有限本地堆，仅作为定向开发证据，非云端或本地正式发布构建。

**仍不完整**：Agent runtime 的 execution output MIME 白名单、现有数据库 CHECK 与客户端能力未扩展到音频/WebP/GIF；故不能声称 Agent 已能生成这些格式的会话产物。会话持久资产 Owner 代码、真实 MySQL 8 建表/旧库迁移、最终选稿正式提交与验收、线上浏览器音频 Range/画鸟流程均未验。不得启用默认标志、合入 develop 或通知用户验收。
