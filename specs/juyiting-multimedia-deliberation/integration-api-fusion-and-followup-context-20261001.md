# API develop 融合与多轮上下文闭包：实际状态补充

日期：2026-10-01。只读状态/证据，不改冻结 v1、验收标准或唯一 runtime ledger。

## 已交付范围

重新独立读回 SDD/API/Web/Client 四仓的 `codex/juyiting-multimedia-deliberation`，分别为 `ecb041bb`、`f89d4de3`、`8b8c951d`、`71b26ce6`；均与本地 feature HEAD 一致，且当前 fast HEAD 为其祖先。这是本文件提交前的观测点，无需重复建分支/merge fast。

[长期融合方案](long-term-fusion-plan-20260928.md)、[融合详设 v2](fusion-detailed-design-v2.md)、[存储/媒体详设](design.md)、[实施计划](fusion-implementation-plan-v2.md)、[长期多轮/每意图权限补充](long-term-followup-authority-design-20261001.md)及[冻结 owner HTTP/权限合同 v1](controlled-image-followup-owner-contract-v1.md)均已交付。一个会话、request/turn/step/event 和资产体系，按本轮权限选择 CHAT/INSPECT/EXECUTE；不是双聊天系统，也不让普通聊天默认加载工具/附件字节。

## API develop 融合 v4：82 项桥通过，整次仍失败

候选 `8121e8d89ad0be13ddb79012b61955bac5ae8caa` / tree `e106bfa99b78c97ac2e6a765a7032a1db20dc9bf` 的 develop parent 是 `88da023bb0c7a4868f4c0ccdc5afd3a259c57f8a`；尚未提升 API feature pin。

- 本轮真实 Agent 8 XML/57 项、Chat 9 XML/25 项，全部零失败/错误/跳过；Agent 含真实隔离 MySQL 3 项。均为实际执行，不是 UP-TO-DATE 复用。
- 64 actionable tasks（54 executed、10 up-to-date），整次 exit 1。common-test 编译已出现 Testable processor initialization 与 dependency analysis（0.199s），随后 daemon Java heap 错误/99% heap，未出现 snapshot completion。此证据支持增量 snapshot 路径推断，**不足以宣称 AP 失败或业务断言失败**。
- Voice 0 XML、NOT_RUN；真实 Redis4 测试也 NOT_RUN。不能将 82 项通过写成完整融合或产品通过。
- v4 launcher/orchestrator/daemon 已真实终态；未因慢请求/SLO 人为取消。

[便携 manifest](integration-evidence-20260928/api-develop-fusion-v4-followup-context-20261001/manifest.json)保存 stdout、daemon、17 XML、冻结输入/矩阵/命令和授权读回，共 27 原件。gzip 解压后逐一与原 SHA-256 一致；原失败保留。

v5 只在已有私有 init 的 `incremental=false` 列表增加 `:common:jia-common-test:compileJava`；33 个源文件、16 个 Voice 类、17 个桥类、AP/依赖图/heaps/selector 和 fixture 形状不变。Main 已核对精确 hash/parser、Unix/TCP 同一 MySQL 身份与 prefix 空、Redis4 二进制，授权一次串行 orchestrator 组合。**此补充不预断 v5 成功**；实际运行结果仍需另行保存。

## 当前 develop 又前进：不覆盖原验证绑定

最新只读 API develop 是 `49a931357fe6b067c47a2dda425e31be8257193d`，相对候选 parent 新增 3 个语音提交、5 个路径：Realtime session client、VoiceDigests 及 3 个测试。既有冻结组合保持原输入继续，不取消、不替换为未验证树。后续必须对这 5 个路径收敛并补实际相关组合；本次结果只能证明其 exact parent/tree，不能证明最新 develop 已融合。

Web/SDD/Client 当前观测的 develop 均为对应 feature 祖先。各仓原始 `ls-remote`、tree/祖先结果保存在同一便携证据，不用历史 snapshot 推导最新状态。

## 多轮 Web 的真实缺口

API Owner 已在独占工作树实施 v1 72 精确路径包（源码施工，不是通过）。Web Owner 只读核对证明：刷新后缺少权威的完整 current tuple，不能从初始点将 pin、旧 request、成果 asset 或 hidden selectedAgent 拼出 generation/assignment/grant/requirement/target。

拟新增 Chat-owned `GET /chat/conversations/{conversationId}/interactions/context`，仅返回当前一致上下文，供构造 preview；不物化字节、不签发权限、不创建执行、绝不替代 preview→明确同意→issue→final。此时仍待 API Owner 核对并由 Main 冻结独立 v1.1 补充；Web 不把候选接口提前当成可用能力，也不猜版本 `"1"`。

## 验收与授权边界

29 桥共同 fixture、34 产品用例仍 NOT_RUN。普通有 refs 的讨论、AVAILABLE/INSPECT、持久澄清及 WAITING_USER 可回复、全媒体/多 lineage、双接应、实际 Provider/浏览器、保存/正式交付/验收/需求完成与 exact 版本发布仍必须闭合。未选择真实账户/模型、未付费调用、未发布/启用，不通知产品可验收。运行状态只在 `docs/implementation/TASKS.yaml#runtime_ledger_json`，本补充不是第二台账。


## 后续实际更新：v5 通过及 context v1.1 冻结

此前 v4 失败与缺口记录保留。本次 v5 真实 exit0/BUILD SUCCESSFUL，69 tasks（6 executed/63 UP-TO-DATE）：Voice16XML/120项本轮实际编译执行，全部零失败/错误/跳过；Redis contract 10项含真实 Redis4.0.6 owned-child 用例执行通过。Agent57/Chat25（含MySQL3）UP-TO-DATE，明确复用上节 v4 输入未变的实际 XML，不宣称 v5 重跑82项。

Main逐一核对33XML/源码hash/任务执行与复用标记，确认终态PID缺席，重新读回自有MySQL Unix/TCP同一身份且prefix空。API feature已精确 FF/push/remote readback到 `8121e8d89ad0be13ddb79012b61955bac5ae8caa`，SDD研发pin/gitlink同步；[便携v5/source提升证据](integration-evidence-20260928/api-develop-fusion-v5-source-accepted/manifest.json)保存41原件及逐selector复用边界。源证据只绑定develop parent88da；最新49a三commit/五path语音delta仍待单独收敛，不把旧组合视为最新develop全融合。

Main基于Web真实缺口冻结独立 [owner context v1.1追加合同](controlled-image-followup-owner-context-v1.1.md)：GET current context自己的schemaVersion1，精确九字段（全部ID/版本string，五个版本decimal）与typed错误/业务零写/一致读取/前端fence。已冻结v1原件/72允许路径不改。API Owner继续源码自检/实施，实际GET与Web测试仍NOT_RUN；Main合同决策不冒充Owner源码通过。完整34项产品/29共同fixture仍NOT_RUN，无Provider/付费/上线或可验收声明。
