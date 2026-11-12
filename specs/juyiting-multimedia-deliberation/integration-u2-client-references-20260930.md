# U2 参考图输入与真实生图接应组合证据（2026-09-30）

Agent Client `isp-install` 四仓融合分支现为 `a2519deed5e79b306b1e52157d528e46f5af147d`（tree `ca3fc394dd85e051ee8208ce921e113ef745f23d`），由独立参考图候选 `faac342fdc4e8a821878017e2f0b222d5991bf8d` 与原生 imagegen/Provider START 候选合并、自检后快进并推送。组合树的 `conf/codex-ws-agent/test/*.test.mjs` **420/420 PASS，0 FAIL、0 SKIP**，日志 `evidence/u2-references/client-combined-exact-20260930.log`。运行使用未跟踪的既有依赖软链接，提交中不含依赖副本。所有生成事件均为测试桩；**无生产 Agent 安装、无付费 Provider 调用。**

- 原生会话只有在任务/Agent/运行实例租约通过、API 返回 exact `executionId + leaseVersion` 且输入清单字段/顺序合法时，才在私有、单次运行目录读取参考图；仅用 fenced `POST /inputs/{inputRef}/content` 获取当前授权字节，禁止使用旧 `/inputs` 或用户文件名拼路径。
- 逐份核对 MIME、字节数与 SHA-256，目标固定为 `inputs/input_N.png|jpg`。读响应未知、短读、重复或跨执行输入不调用 Provider；中途撤权会被服务端逐次读取校验与 Provider START 边界重新拒绝。
- 仅当所有已授权输入均已物化、当前租约有效并取得服务端单次 `/conversation/provider-start` 的精确成功回执，才调用独立 imagegen；ACK 未知不执行也不自动重试费用。无输入需求继续支持原生无参考图路径。
- 环境变量 `CYF_CONVERSATION_IMAGEGEN_ENABLED` 默认未开启；服务端点将的 `costAuthorizationRef` 当前仍为 null，没有收费授权时 `GRANT_REVOKED`（或等价拒绝）不能用客户端开关绕过。此处 420 个通过只证明模拟边界，不证明在线画鸟、音频或正式成果可验收。

后续：把明确费用授权/预算事实与点将 grant 关联；真实 Agent 能力与目标选择/开关回读；会话 `part.ready` 与可预览下载媒体、保存工作空间、正式晋升验收；逐版本 develop/测试构建/发布与浏览器实测。遵循 [分版本发布计划](versioned-delivery-plan-20260928.md)，不可用本定向测试替代产品验收。
