# 2026-09-30 fast v1→v2 旧库迁移融合（研发证据）

API 特性分支合入原迁移分支 `d761da80`，融合提交 `a4f6501fbf7362ba0dc148ee7bf1386e05784817`，tree `5a466953750656fd6e35366b470b72e835e003f2`，已推送远端。变更修复 `chat_dispatch_outbox.available_at` 在终态消息上允许 NULL 的 schema/Initializer/SQL 一致性；SQL 迁移 SHA-256 为 `4093d2c020767dde0476acc54696d83c0011e11158e3aad62c87c714e3804df2`。保留新鲜空库与旧库两条路径，不更改生产数据库或开启默认业务开关。

针对融合 exact tree，使用串行 `/home/isp/wsps/cyf/ops/orchestration/cyf_orchestrator.py gradle` 执行 `:chat:jia-chat-service:chatDeliberation --tests cn.jia.chat.config.ChatDeliberationSchemaContractTest`：JUnit XML **3 tests / 0 failed / 0 skipped**，证据缓存 key `8644c70afaffceba66f06bddc2da3643b81248ae1c10f49b134d7f0a9b486fdf`。另外仅向本线程独立 MySQL 8.0.21 socket 中**不存在**的 synthetic schema `mmd_legacy_v2_20260930_01a0dde8_integrated01` 导入固定旧版 `1b5fa4ce` schema，再执行与融合树字节摘要相同的迁移 SQL：初态 V1 → APPLIED，重复执行不增加事件；两条正常待发消息与 final 可恢复，两条孤儿事件进入 DEAD 并携带准确原因；owner 范围字段和 final 消息 ID 检查通过。fixture 未写入/触碰生产数据库。

**边界**：只验证固定 fast v1 两条 synthetic 消息及 SQL、静态 Java 合同，不证明任意真实旧库、生产迁移、机器 JWT、Provider、浏览器或正式发布；目前 Chat 持久资产独立 Owner 仍有未提交的 schema/Initializer 修改，后续融合必须三方代码对照后实测 combined tree，不能把这次旧库 SQL 通过冒充媒体资产表迁移已经通过。
