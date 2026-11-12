# 长期融合方案交付与实际合同缺口（2026-10-01）

本文件为精确源码/文档交接补充，不是新 HTTP/wire 合同，不替代执行台账。长期详设已交付，功能继续实施；未选择真实账户、未付费、未部署本特性、未做浏览器产品验收。

## 1. 分支和权威文档

SDD、API、Web、Agent Client 均使用 `codex/juyiting-multimedia-deliberation`。本轮独立查询远端 feature/fast/develop，并验证精确 fast SHA 是对应 feature 的祖先；本地 feature 与远端一致。保留既有成果，不重建分支或伪造重复 merge。

| 仓库 | 复核时已推送 feature SHA | 当前 fast 全部包含 |
| --- | --- | --- |
| SDD | `357ddc0b03320c97eaf65c5bd29266e5163ad482` | 是 |
| API | `8121e8d89ad0be13ddb79012b61955bac5ae8caa` | 是 |
| Web | `8b8c951d4902a5927c85a43a3fcede525154509b` | 是 |
| Agent Client | `71b26ce69d25a59f223499854b692e597b57d911` | 是 |

SDD 行为本次文档提交前观测点。完整 tree、fast/develop SHA、采集时间和文档摘要见[独立远端回执](integration-evidence-20260928/fusion-branch-design-current-readback-20261001.json)。fast ancestry 不是最新 develop 已全部融合的证明；API 当前最新 develop `49a93135` 的五路径语音增量仍在候选验证。

开发 Agent 阅读顺序：
1. [需求](spec.md)与[长期融合方案](long-term-fusion-plan-20260928.md)。
2. [融合详设 v2](fusion-detailed-design-v2.md)与[媒体/文件/双接应详设](design.md)。
3. [多轮与每意图授权详设](long-term-followup-authority-design-20261001.md)，再读[owner 冻结合同](controlled-image-followup-owner-contract-v1.md)、[只读当前 context v1.1](controlled-image-followup-owner-context-v1.1.md)及其优先级文件。
4. [实施计划](fusion-implementation-plan-v2.md)、[验收矩阵](acceptance.md)与[当前精确 pin](integration.yaml)。

## 2. 长期决策与完整产品边界

统一一个悬赏会话、一套持久 request/turn/step/event 和权威资产。fast 是轻量 CHAT 策略，不是并存的第二个产品；multimedia 也不是“每一轮加载全部工具和资料”。

- **CHAT/NONE**：讨论、状态及必要历史，不预读附件字节、不挂执行目录。具体引擎只有只读受限证据时必须诚实声明，不能宣称已严格无工具。
- **AVAILABLE**：精确资料目录/版本/来源，不把目录当成已理解图片或已读文件。
- **INSPECT**：本轮 ACL、固定输入 manifest 与真实读取能力；能力未实现就不可广告，不偷偷降级猜测。
- **EXECUTE**：明确本轮意图，服务端独立授权、资料快照、真实能力及费用/外发校验。明确且信息充分的首轮需求可直接执行；信息不足才持久澄清，不强制 LLM 规划前置。
- 自然“再鲜艳一点/换成黄鹂”应生成可信来源的 typed proposal 或必要澄清；proposal 不是权限。新编辑/再生成按冻结的 preview→明确同意→issue→admit 获得新每意图授权；初始 GENERATE grant 不能借权 EDIT。
- 同会话不等于同模型线程、同目录或同 lease。山寨安顿/自家接应均通过受权 manifest/API 领取本轮输入、在各自 run 隔离目录工作、提交校验过的输出；提示词只是目录说明，不是权限控制。
- 一份内容的三种用途为会话展示、个人保存、正式交付。共享内容身份/来源，分别校验用途权限；不新建三套文件系统，不要求物理去重先完成，也不强制先保存空间才能修改上一稿或验收。

完整范围不缩减：可选工作空间参考图→显式点将→自动同会话议事→直接生成/必要澄清→自然多轮补充修改→文本/图片/音频/文件实时展示、预览、下载→主动保存→正式交付、验收及真实需求完成。两个接应模式均须实际验证。

## 3. 本轮实际发现与 Owner 下一步

### 3.1 Web 多轮候选四项合同遗漏

Main 实际加载 immutable `4ce7a02e` 的 JS primitive/Vue composable，以 mock HTTP 复现；不是浏览器或 Provider 测试：

1. 4000 个 Unicode codepoint 的鸟 emoji（8000 UTF-16 code unit）被误拒。
2. 内容中的 LF 控制字符被误接受。
3. 内容中的 C1 NEL 控制字符被误接受。
4. 无安全 crypto 熵时，两次不同意图向 preview 发出同一个常量幂等键。

[原始 probe/stdout/source manifest](integration-evidence-20260928/web-followup-4ce7-main-contract-failures/manifest.json)固定实际证据。该候选未 FF/push 到 feature。已交原 Web Owner 在同 18 允许路径内提交 child：按 Unicode codepoint 计数、严格拒绝 ISOControl、使用安全唯一键或无安全熵零写，并新增边界回归保留原相关测试。不能用常量或 `Math.random` 替代安全熵。

**后续实际修复已收口**：原 Owner child `4f21fa42` / tree `543c5112` 仅修三路径；Owner85相关测试/lint/SFC摘要核对，Main29定向实际通过及上述四个原失败probe复测全部通过。该 default-off EXECUTE 源码切片已精确 FF/push/readback；[原始便携证据](integration-evidence-20260928/web-followup-4f21-source-accepted/portable-manifest.json)记录新源码，当前 Web pin/gitlink 已同步。历史 `4ce7a02e` 失败证据不改写成通过。

此包完成也不等于全多轮媒体闭包：新的受理 request 必须进入同会话成果发现/事件恢复，不能只 toast“已受理”、仍仅订阅首轮 activeRequest。

### 3.2 API 最新语音融合候选的真实终态

候选 `42d6e7e` / tree `b9da418a` 无冲突合入 API 最新 develop 的五个语音路径，未提升 feature。原组合 v1 的正常源图执行 exit 1：62 tasks 全 executed，15m26s 后 Gradle daemon registry expiration listener OOM；另有 worker signal 9 记录。没有业务 Java 编译诊断或测试断言失败，不能记成业务通过。

- Agent：本轮实际 8 XML / 57 项，零失败/错误/跳过。
- Chat：本轮 0 XML，NOT_RUN。
- Voice：未到达，NOT_RUN；旧 16 XML / 120 项明确排除，当前源码静态 129 个 `@Test` 不是已通过 129 项。
- Main 核对原 launcher/orchestrator/daemon 均终态，自有 MySQL Unix/TCP 身份一致、fixture schema 前缀为空。

[便携原始证据](integration-evidence-20260928/api-voice-delta-v1-failure/portable-manifest.json)保留 XML、原 stdout/daemon gzip 和源/环境摘要。原输入不盲重跑；新分阶段矩阵复用同候选实际 Agent57，分别串行执行原 Chat9 与 Voice16，保持正常源图、init、AP、heap 与全部测试范围。每阶段独立授权、真实新 XML 验证；拆分或缓存变暖本身不是 PASS/OOM 风险消除证明。

分阶段 v2 Chat 的 runner 在启动 Gradle 前实际因 `KeyError: logs` 退出：新 input 只有 `phase.logs`，固定 runner 需要顶层 `logs`。无 Gradle/PID/新 XML，仍 NOT_RUN。已归因停止；下一次只修控制面 schema、重新冻结 input/matrix/argv 并完整核对 runner 消费字段，不修改源码/init/测试或原失败记录。

### 3.3 API schema v1/v3 重启兼容

原 consent initializer 对 v1 catalog 的精确列顺序、16 index 行、13 CHECK 名与谓词有严格验证；完整 v3 扩展后重启必须兼容，不能删检查或接受任意 drift。经源码证据，批准原 API Owner 在原 72 路径外仅增加旧 initializer 和对应测试两条路径，共 74 路径：只接受完整 pristine-v1 或完整 v3 catalog，保留原 13 enforced CHECK，严格校验新增 purpose/execution protocol union、列与索引。

默认关闭/旧 schema 的 mapper 不得引用不存在的新列；部分迁移、同名弱 CHECK、未知额外列/index/CHECK 必须拒绝。当前仅批准 source-only，自检和实际隔离 MySQL/default-off/restart 验证仍须完成；不推导生产数据库迁移授权。

## 4. 尚未关闭的长期闭包

[自然中文多轮/全媒体设计准备](integration-evidence-20260928/discussion-inspect-design-preparation/Chinese-natural-multiround-design-supplement.md)及[源码事实/能力矩阵原件](integration-evidence-20260928/discussion-inspect-design-preparation/portable-manifest.json)已保存；它们是下一合同输入，不是已冻结接口、实现或权限。草案 HTTP 字段/JSON 语法须独立机器 fixture 校验后再冻结，不能照抄 draft 为上线 wire。

- DISCUSSION/CLARIFICATION_REPLY 的严格 HTTP 分支、持久 pending question/CAS/resume、typed outcome 的当前 dispatch 校验仍须冻结并实现；不把现有文本流解析成执行授权。
- Client 当前 INSPECT adapter 未启用；CHAT 严格无工具证明未完成。接应标签不等于能力就绪。
- 多 request/step 的全媒体持续发现、历史/断线事件恢复、自然输入 proposal/澄清和本轮 refs/draft/assignment/grant fence 仍须联调。
- 34 产品用例、29 共同桥 fixture、浏览器画鸟全流程、两个接应模式及本特性版本发布均未完成。正式构建/发布必须绑定实际版本、exact SHA/tree、测试和制品摘要；既有其他功能的 release 不能当本特性已发布。

下一可执行步骤：原 API Owner 完成授权源码包与自检，Web 已接受切片继续做跨仓组合，Verifier 完成候选分阶段实际组合验证；Main 再冻结讨论/澄清/INSPECT 下一合同并做跨仓闭包。Owner 自检，无独立 Reviewer；Gradle 经 orchestrator 串行，等待资源不抢占，性能慢仅观测。


## 4. 同日后续：语音融合验证已收口

上文 §3.2 是原 v1 失败观测点，保留不改。随后同 `42d6e7e` 获得 Main 实际核验的 33XML/211项：Agent57原v1复用，Chat25和Voice129为v3独立实际执行，零失败/错误/跳过；owned Redis4 contract10/10通过，PID终态与MySQL后读回一致。API feature 已精确 FF/push/readback42d，当前 pin/gitlink同步。详见[新源码接受回执](integration-api-voice-delta-source-accepted-20261001.md)；该通过不包含自然多轮、产品用例或发布，不覆盖历史OOM/runner失败。


## 5. 多稿发现施工合同已冻结

[bounty conversation request index v1](bounty-conversation-request-index-contract-v1.md)定义owner只读GET、scope隔离、已有RequestView复用、fixed-through keyset、晚提交低ordinal从0重扫和Web独立catalog；历史读不依赖ACTIVE grant，不把旧target/assignment稿借权为当前验收。22项预期fixture均NOT_RUN，离线检查只证明示例shape与坏输入拒绝，不证明API/Web业务。API新六叶子路径与既有74路径互不重叠，Web沿用明确多稿接口，不改activeRequest取消焦点。下一步责任Owner实现和实际验证该包，不停留在文档。


## 6. 自然答复Client执行包

[typed result v1](typed-deliberation-client-result-contract-v1.md)已冻结：原生outputSchema产出ANSWER/CLARIFY/proposal，以同一chat.message final sidecar原子绑定，不把普通正文解析成执行命令；只流式显示顶层text。sourceRefId仅可选本轮授权目录，不含模型造出的grant/版本/费用/parent。Client实现默认关闭且真实能力声明；API随后须将正文+union纳入finalDigest并持久化pending question/CAS/resume，Web再闭合自然交互。24预期runtime用例均NOT_RUN，离线shape自检不是Provider/用户验收；真实INSPECT未被广告或偷启。
