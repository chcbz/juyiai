# Client INSPECT runtime 实施交接（2026-10-02）

这是基于 Client `7a1756be0a1d33b9430880bdd8c1a610c8eb21d7` 的源码接点核对，不是运行通过证据。唯一领域合同仍为 [typed-inspection-authority-contract-v1.md](typed-inspection-authority-contract-v1.md)，不新增协议或执行状态机。运行 Owner/状态只在主工作空间 TASKS.yaml 管理。

## 已确认的接点及真实缺口

以下路径相对 Client 仓库的 `conf/codex-ws-agent/`：

| 源码接点 | 当前事实 | 实施要求 |
| --- | --- | --- |
| `typed-inspection-input-carriers.mjs` | 已有纯转换和 receipt draft/finalize；没有 I/O 或授权 | 复用已接受转换器及 repo-local digest fixture，不重复实现 canonical 算法 |
| `agent-client.mjs:4280` `runReadOnlyInspection` | 只抛出 INSPECT_NOT_ENABLED，未接 processor | 实现后必须接真实 dispatch，不能仅新增测试可调用函数 |
| `agent-client.mjs:5319` processor 初始化 | runChat 始终调用 runProfileChat | 按可信 snapshot marker/route 分派，保持 CHAT v1 原语义；不得把 INSPECT 发给普通 CHAT |
| `agent-client.mjs:2722` | inbox claim 后复用 runChat 和 controls | 在既有 claim/recovery 链附加 manifest/receipt，不另建第二个 inbox |
| `chat-runtime.mjs:565` markRunning | 将 engine 数据持久保存 | 准备阶段先持久化 inputDigest；start 回执未知只对账，不重复 start |
| `chat-runtime.mjs:619` buildThreadKey | 当前参数没有 inspection 的 authorizationId/manifestDigest/inputPolicyDigest | 新 mode 的绑定完整纳入这些输入；保留旧 CHAT key 的兼容行为 |
| `app-server-adapter.mjs:442` | runTurn 已接受 input 数组，并附只读 sandboxPolicy | 不需重造 turn 协议；数组支持不证明 localAudio/文件理解，更不证明宿主文件隔离 |
| `agent-client.mjs:3702` | INSPECT 明确 disabled | 只有实际 profile 测量与启动/readback 完成后才能宣告对应能力，不能永远关闭然后宣布完成 |

## 连续实施顺序

1. **受权输入**：固定平台 origin、精确内部内容路由与认证；禁止 redirect/任意 URL。校验 manifest 绑定、MIME、bytes、hash，私有目录原子发布只读常规文件，拒绝路径与 symlink 越界。撤权失败不得从旧缓存补读。
2. **真实运行链**：processor → typed INSPECT runtime → inputs prepare → inbox 持久化 → 原生 turn → finalize receipt → v2 final。对每一个跨层接点增加故障/恢复测试，而不只测试 helper。
3. **隔离 profile**：绑定 exact binary/schema/resources 和启动身份；仅可见必要运行资源、本轮输入及受限状态目录；明确 Provider 连接与任意工具网络的区别。不得挂载整个宿主根来修复资源遗漏。
4. **载体实证**：图像解码/原生输入、音频实际理解、具体文档 parser provenance、严格文本解码分别验证。schema 或 adapter mock 仅作源码测试；不以假支持绕过能力协商。
5. **完整闭环**：山寨安顿和自家接应分别核对真实版本、读取摘要、同会话澄清/执行/修改、预览下载、可选保存、正式交付和任务完成。AC01–AC22/FD01–FD12 原范围不变。

## 必须保留的失败测试

- 同一 request 重送、start 已受理但响应丢失、Client 重启：不二次调用 start，不转 legacy/EXECUTE。
- 来源撤权、重新点将、会话 generation 变化、manifest/inputPolicy 改变：旧输入/旧线程不得复用。
- 内容接口 3xx、MIME/长度/hash 不符、symlink、跨请求路径：输入未验证前不得进入模型。
- 真实原生 final 与 receipt 的 thread/turn 不符：拒绝；不能用模型正文填可信 receipt。
- 恶意资料请求工具或读取宿主 canary：验证实际隔离，不能只断言提示词包含禁止语句。

## 可复用证据与授权边界

已有 [本机隔离探查](integration-evidence-20260928/inspection-isolation-feasibility-20261002/README.md) 只证明最小 bwrap 文件视图可行，没有验证原生引擎、网络或模型理解。保留 v1 失败及 v2 成功，不重新将其计作产品通过。

本交接不授权付费 Provider、生产服务恢复或生产数据修改。线上 OAuth 502 与产品源码验证分开处理；未恢复登录前不得把浏览器启动成功记为用户旅程通过。最终以 exact 源码/制品、实际部署和真实业务结果证明可验收。
