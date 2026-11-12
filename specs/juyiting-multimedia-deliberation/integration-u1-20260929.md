# U1 授权与议事步骤源码整合回执（2026-09-29）

状态：**研发特性分支，未上线、未做产品验收**。本回执仅记录相对 [2026-09-28 基线](integration-baseline-20260928.md) 的增量，不替代冻结的 [融合详设 v2](fusion-detailed-design-v2.md)。

- API 特性分支 `codex/juyiting-multimedia-deliberation` 已快进并推送至 `beb45e6aef2780aeb43e6a92597b47049495cc29`，tree `78a120cb0da277f357ed314fa09c4bdb7c86277e`；远端读取同 SHA。
- Agent U1：将带 owner/client/tenant、任务和 assignment revision 的 grant 及输入版本摘要落库，新增授权/撤销/准入、同 scope 幂等和 active-task 唯一性；已修复 Jackson 3、实体 setter 和 controller 认证夹具。原来仅按索引名字校验的漏洞，在隔离 MySQL 8 中可插入两条 ACTIVE grant；现读取 `information_schema.statistics` 核验 ordered key/unique/prefix/expression，增加同名非唯一索引的负向测试。旧证据：`integration-evidence-20260928/u1-grant-drift-negative.json`。
- Chat U1：新增 `chat_interaction_step` 和 `chat_step_execution_link` 的带 scope 外键、唯一执行意图与递增版本，映射 store 的 scope/CAS 定向测试；这是编排的持久化前提，**尚未实现统一 interactions endpoint、自动议事或真实 Provider 执行**。
- exact API tree 在 orchestrator 序列化 Gradle 同一调用下完成 `:agent:jia-agent-service:mmdU1Grant` 11/11 与 `:chat:jia-chat-service:chatDeliberation` 72/72，0 failures/errors/skips。原始日志在 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u1-chat/gradle-u1-combined.log`；reuse evidence key `e2de2ea36294026f3e06fc3130d0bf402f33428f16cb2fee9e2ba0714773fc11`。测试结果 XML 在该 tree 的两个模块 `build/test-results/{mmdU1Grant,chatDeliberation}`。
- Web 保持 `e9f00f5be51389e1660e0cc53a9463edc8a3a33d`；Client 保持 `7b13329793095b71ff751d4833cc910ae979dfcf`。当前研发 pin 不代表已同步上线版本。真实迁移旧库、machine JWT、server/local 双模式、浏览器画鸟→图片预览/下载→交付/验收尚未验证；图片归档 API、受控执行与会话媒体字节仍缺实现。

下一步按 v2 实施计划继续 U1 admission/outbox → U2 CONVERSATION 输出/asset 归档 → U3 前端与真实接应 → 云端或明确授权的本地测试/版本发布 → 实际浏览器及权限验收。旧 `/chat/stream` 的 fast CHAT/INSPECT 工具隔离不得为了兼容多媒体而退化；不能将源码定向绿灯写成完整产品通过。
