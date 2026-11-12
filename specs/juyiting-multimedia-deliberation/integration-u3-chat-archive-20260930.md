# Chat 会话资产归档集成：定向验证记录（2026-09-30）

研发分支 `codex/juyiting-mmd-chat-archive` 在隔离 API 工作树最初提交了 `5e5f97574f3db70316935dab3ae8f1c20ec896b1` / tree `ed43b109ace744f73d20ba3b9ed6f34caa4f8a9e`，新增 owner-scoped Chat 归档 POST/GET 操作、源资产关联/精确摘要、持久幂等键、恢复账本及单测。最终补丁 `b7655d0eb10e6501481091ec52e19283e8e6a5f4` / tree `09df1520cbb65e9f237d8ed57189087ad01219a5` 已推送并快进 API 特性分支。**仍依赖尚未合入的会话持久资产表**，默认 off，不代表线上服务可用。

## 根因矩阵（Gradle，仅此 exact tree）

1. 首次定向测试未进入编译：`build.gradle:109` 发布配置读取 `repoUsername` 失败。改测试调用参数 `-PrepoUsername=unused -PrepoPassword=unused`；这两个值仅为本机非机密配置占位，不执行 publish。
2. 调整后依赖/生产 Java 源码编译经过 Chat service；尚未产出测试 XML。2026-09-30 09:41:58+08 内核日志确认全局 OOM 杀死 Gradle daemon pid 1695849（RSS ~943 MiB），故不能宣称单测通过。现场 `MemAvailable` 约 1.4 GiB。下一候选保留串行锁及单 worker，仅为此定向测试显式限制 daemon heap（`-Dorg.gradle.jvmargs=-Xmx384m -XX:MaxMetaspaceSize=256m -Dfile.encoding=UTF-8`）；不要杀其他 Owner 进程；若限制后仍 OOM 则重新记录证据/调整构建资源，不重复盲试。

现存功能差距：个人工作空间目前的 MIME 白名单只支持 PNG/JPEG/text/PDF/Office，现有运行时输出也未启用音频；因此当前 Chat 归档源码 **不能**声称支持音频归档或 WebP/GIF。图片优先纵切不等于完整多媒体验收，后续单独扩展安全 MIME/字节校验与相应测试。

## 定向验证结果

针对上表根因更改 Gradle 参数后，首次实际测试进入 19 个用例，18 通过、1 个失败：`ChatConversationArchiveControllerTest.java:84`，HTTP adapter 未预先校验短幂等键，Mockito 服务返回 null 导致 NPE。补丁 `b7655d0e` 在调用服务前用与服务端同一格式校验；在其干净 exact tree `09df1520` 用 orchestrator 串行运行 `:chat:jia-chat-service:chatDeliberation` 及 3 个 Chat 归档测试类，JUnit XML 回读 **6+9+4=19 / 19，通过 0 失败、0 错误、0 跳过**。命令包含 `--offline --max-workers=1 -PrepoUsername=unused -PrepoPassword=unused` 和仅作用于测试的限堆参数；证据缓存 key `51e1b483b1b8e222c7a82dc0ebf582dd3e2e735258aba4dd41ab2f23825847a4`。尚无真实 MySQL 8 建表/重入、持久 asset 与 archive API 的整合测试、真实浏览器或发布构建，**不能据此开启默认特性或通知验收**。
