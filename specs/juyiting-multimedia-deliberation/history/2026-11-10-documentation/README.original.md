> **2026-10-07 原型入口纠正**：后续新需求统一基于[最近优化的UI原型](../juyiting-ui-baseline-20261006/prototype/index.html)及其页面/状态索引。本页的 `complete-20261007` / `adjusted` 是历史中间成果，不是当前界面基准；历史证据保留，真实业务仍 NOT_COMPLETE。

> **2026-10-07 浏览器走查与原型补齐**：[页面交互矩阵](page-interaction-prototype-20261007.md) · [完整可点击原型](prototypes/complete-20261007/index.html) · [异常与恢复场景](prototypes/complete-20261007/scenarios.html)。仅离线设计交付，线上缺口未修复；SF05已确认可见重复，整体NOT_COMPLETE。

> **2026-10-07 当前状态补录**：[已实现/发布/业务证据](delivery-status.md) · [剩余任务](remaining-tasks-20261007.md) · [新最短流程实测](shortest-flow-test-20261007.md)。下方2026-10-04及更早记录保持历史，旧“暂停/未执行”不覆盖已实际发布的API117/Web177。整体验收仍NOT_COMPLETE；不重做已实现功能、不因文档构建或部署。

# 当前开发进度（2026-10-04）

> 文档收口（2026-10-23）：当前页面交互读 ../juyiting-ui-baseline-20261006/optimization/spec.md 与Web原型；技能执行读 ../juyiting-skill-execution/design.md；跨账号及成果选择读 ../juyiting-external-commission-mvp/design.md。本文后续时间线及current-state/delivery-status仅证明标注日期的观察；旧v1/v1.1中基础+补充关系保留，不能按文件名删除或当今日wire版本。


用户已恢复按版本开发。入口/点将册/＋菜单与转写入草稿已形成 Web 候选 `58d631d`，229项定向与本地研发构建通过，已推送独立开发分支。第一增量尚缺附件-only的配套准入/续办，成果与验收、真实联调和正式发布仍待完成；**未更新集成pin、未上线、不可据此宣称完整产品可验收**。见[分版本开发回执](implementation-progress-20261004.md)。

以下保留历史时点记录；其中线上版本只代表各次核验时点。

---

# 当前实施进展（2026-10-03 21:54）

**单一资料入口与音频基础已改源码，尚未整体上线。** Web候选`6a2b71e`已独立推送，66项定向回归通过：Overview统一选择图片/PDF/音频/文本，固定版本预览、下载、移除；workspace音频白名单与两种界面已接通。不是只改文案，但也不是完整后端闭环：悬赏榜/通用原子创建、Agent按需分派、FAILED终态投影仍需接续。详见[纠偏详设第8节](unified-materials-correction-20261003.md#8-2026-10-03-2154-实施增量源码候选不是上线)。

没有合develop、没有新增正式Run或部署，原34项+UM子例仍NOT_COMPLETE；API bb52候选保留。以下为此前时点记录。

---

# 当前产品方向与交付状态（2026-10-03 21:20）

**用户已要求纠偏：取消独立“参考图”入口，统一“添加资料（可选）”，支持图片、文档、音频与普通文件的完整协作闭环。** 不是换文案，也不是仅生图产品。方案、详设、工作包与验收以[通用资料增量v3](unified-materials-correction-20261003.md)为当前优先；完整34项保留并补UM01–UM10，尚未验收。

线上仍API1.13.67/Web1.13.64 Run164（含语音SVG）/Client1.13.62。420虽自动进入议事，仍在Provider START前FAILED且界面等待；本轮找到全局响应脱敏器破坏source精确字段的缺陷，修复候选bb52cd7b已12项回归通过、独立feature推送，**未合develop/构建/发布**。底层修复保留，不能代表通用资料已完成；无新增Provider/Flow/生产DML，未重放原任务。

以下为历史时点记录；包括此前“DTO修复”在内，不能取代以上更完整的HTTP链路事实。

---

# 当前交付状态（2026-10-03 20:30）

**API1.13.67已发布：419查询已从500恢复200；完整多媒体34项尚未完成。** 同时修复参考/改图source多余null字段被Agent严格拒收的问题：真实HTTP回归10绿，原版红测与部署Client离线校验俱全。Web1.13.64/Run164及语音SVG不变；原419保持FAILED，不重放。下一步是新正常业务意图的实际参考图生成、同会话改图等验收。详见[本轮发布与边界](release-1.13.67-reference-wire-progress-20261003.md)。

以下按原时点保留历史，不替代以上最新运行状态。

---

# 历史：参考图查询修复尚未发布（2026-10-03 19:58）

**语音SVG已上线；完整多媒体验收仍未完成。** 新419已实测参考v2在源变v3后仍精确授权，但点将结果查询遭MySQL JSON格式误判；最小修复API `8359ec5` 已29项通过并合入develop，**尚未发布**。另有local执行在Provider START前FAILED，需单独定位，未重放。线上仍API66/Web64；原418已验收交付保持不变。详见[本轮实际进展](reference-v2-read-integrity-progress-20261003.md)。

---

# 当前交付状态（2026-10-03 17:50）

**鸟图已完成真实预览、下载、工作空间保存和正式验收；完整多媒体34项尚未完成。** 当前线上API1.13.66、Web1.13.64（Flow4403172/164 SUCCESS，含e586语音SVG）。API实时事件修复28项通过，已实际发布并完成监控交接；真实浏览器原会话单层SSE/已有图片回放/游标续读通过，正式与工作空间原图摘要不变。详见[发布结果](integration-evidence-20260928/release-1.13.66/release-result.json)与[验收增量](acceptance.md)。

以下保留历史记录；其中旧日期“最新”不替代以上状态。

---

**2026-10-01 真实验证最新补充**：[API多轮/澄清验证](integration-api-strict-wire-runtime-verification-20261001.md)记录a213的Chat V3 33通过、V2 82通过，typed64项中13失败；另明确复用同树Agent39通过。128m daemon堆耗尽、collector/provenance纠正及全部原始失败保留。限定修复继续，失败候选不提升；真实INSPECT/完整多媒体/双接应/浏览器/发布仍未完成。

# 最新交付入口（2026-10-01）

**完整实施最新推进**：[真实catalog与原生引擎兼容](integration-catalog-and-native-runtime-progress-20261001.md)：API7abc第三轮Agent V3实际39项全部通过，但Chat V3 source-set漏fixture导致3编译错误、JUnit未开始；V2/typed未运行，单路径两行child3063已提交并静态核对，v4原Owner容量不足未执行，实际Terra READY并绑定v5完整验证GO、结果未返回，API未晋升。前轮真实OOM/原失败均保留。Client own-key child607d已接受并推送，Owner162 Node及Main原11项probe通过；真实离线native测量只证明版本/schema兼容。INSPECT/双接应/完整浏览器/本特性版本发布仍未完成。

**统一详设总入口**：[长期融合详设与施工入口](fusion-final-design-entry-20261001.md)汇总单会话/按需能力、双接应输入输出、三用途存储、恢复和开发分工；讨论以冻结 typed v1 为准，执行保持独立 v3，不另实现早期 schema-3 讨论候选。四仓当前 fast 合入有[21:39直接远端证据](integration-evidence-20260928/fusion-feature-fast-remote-readback-20261001-2139.json)，无需重复建分支/merge。

**最新进度**：[回执领域修复与实施优先级](integration-typed-receipt-source-adoption-20261001.md)：Web `ebb664f` 已推送，Main 196 项及合法状态/绑定 probe 通过（基线 lint 两错误与旧合成正向失败保留）；API `642e732` V3实测34通过/3真实MySQL CHECK失败，后续NOT_RUN、未晋升。浏览器启动前置已实测，不等于业务验收。

**前轮详设收口与真实核验**：[受理回执/请求投影领域分离 v1.1](typed-deliberation-receipt-adoption-contract-v1.1.md)补齐当前API/Web状态混用问题；[本轮证据](integration-evidence-20260928/typed-receipt-adoption-20261001/manifest.json)记录891精确候选13文件193通过/0失败，但合法RUNNING/COMPLETED采用仍2失败，候选未晋升。API8fc为干净无冲突组合，测试NOT_RUN；V6未启动。完整产品未发布/验收。

**本次要求已落实：四仓分支已建立并推送、当前 fast 已包含、长期方案与详细设计已交付。完整功能仍在实施，不表示已发布或可验收。**

- 统一开发分支：SDD / API / Web / Agent Client 的 `codex/juyiting-multimedia-deliberation`；[本次直接远端核验](integration-evidence-20260928/typed-receipt-adoption-20261001/branch-readback.json)证明四仓当前 fast HEAD 都是 feature HEAD 的祖先，无需重复合并。
- 最新已推送组件基线：API `87c0acc`、Web `ebb664f`、Client `607d251`；完整 commit/tree 以 `integration.yaml` 为准，历史段落不代表最新 pin。
- **先读**：[本次详设交付与施工入口](fusion-delivery-handoff-20260930.md#本次请求的最终交付2026-10-01)，然后读[长期融合方案](long-term-fusion-plan-20260928.md)、[整体详设 v2](fusion-detailed-design-v2.md)、[多轮及每意图授权详设](long-term-followup-authority-design-20261001.md)、[媒体/存储/验收详设](design.md)。具体讨论按[原子typed合同v1](typed-deliberation-atomic-followup-contract-v1.md)与[回执补充v1.1](typed-deliberation-receipt-adoption-contract-v1.1.md)，执行按独立v3合同；版本号不是全局升级。
- 长期统一一个会话、一套 request/turn/event 和权威内容引用；fast 是 CHAT 策略，多媒体按需查阅或执行，不默认全量加载工具/资料、不要求固定三次模型调用。模型提议不能授予执行权限。
- 实施顺序和逐版出厂条件见[开发计划](fusion-implementation-plan-v2.md)与[分版本计划](acceptance.md)。自然澄清的 API 原子续办、真实 INSPECT、双接应和完整浏览器闭环仍需完成；旧示例版本号 1.13.45–1.13.47 不得直接用于本特性发布。

**2026-10-01 原子续办完整实施启动**：[业务冻结合同](typed-deliberation-atomic-followup-contract-v1.md)固定自然DISCUSSION、原子final、问题CAS/新CHAT续办和独立执行确认；16共同预期保持NOT_RUN。API26路径（Handler已明确交接）与Web12路径由各自Owner实际施工；每意图授权包d995已交付，094精确组合正在正常图验证，尚未提升。

**2026-10-01 typed final严格校验源码已收口**：[正常图实际38项接受](integration-u2-api-typed-final-validator-source-20261001.md)记录87c0编译及JUnit通过，未关闭原子落库/pending CAS/自然多轮或产品验收。

以下为各历史时点的增量记录，保留原始失败和限制；最新状态以以上入口及集成 pin 为准。

---

**2026-10-01 请求目录API已收口**：[API目录接受](integration-u2-api-request-index-source-20261001.md)记录9798正常编译及62实际测试（MySQL2）；与Web1993的实时联调/浏览器/产品发布仍待验证。

**2026-10-01 原生自然答复源码已收口**：[Client结果接受](integration-u2-client-typed-result-source-20261001.md)记录2f69/199实际Node及原边界修复；API原子持久化/澄清续办和Web自然输入仍待闭合，INSPECT未启用。

**2026-10-01 多稿目录源码已收口**：[Web目录接受](integration-u2-web-request-catalog-source-20261001.md)记录1993/105定向及原四wire失败修复；API索引真实验证仍待完成，不表示产品/发布通过。

**多轮执行下一包（2026-10-01）**：[owner HTTP/每意图授权合同 v1](controlled-image-followup-owner-contract-v1.md)已冻结，含 source-backed preview→issue 漂移校验及独立EDIT授权；仍需实际实现/验证，澄清/资料讨论和完整产品范围不缩减。

# 聚义厅多媒体悬赏议事：融合开发入口

## 2026-10-01 最新融合设计增量

API `42d6e7e` 已完成正常源图的33XML/211项实际组合核验并推送；此前OOM/runner失败保留历史记录，不表示宿主风险消除。Web已接受基线仍为 `4f21fa42`，多请求目录新候选尚未完成自检，未提升。

长期交互继续是一条会话、按需路由、权威资产多用途，而不是每轮全量加载。[原子 typed result 合同 v1](typed-deliberation-client-result-contract-v1.md)已冻结：原生结构化结果只有ANSWER/CLARIFY/EXECUTION_PROPOSAL，正文与结果在同一final落库；普通正文绝不解析成执行许可。Client源码施工、API问题CAS/续办和Web自然输入尚未完成，INSPECT未就绪。多稿发现按[请求目录合同 v1](bounty-conversation-request-index-contract-v1.md)实现，不再把activeRequest等同全会话成果。

下一阶段按[融合实施计划](fusion-implementation-plan-v2.md#自然讨论与多稿发现的当前实施顺序2026-10-01)推进。文档离线fixture校验不是运行时或产品验收；完整34项、29桥、双接应、浏览器及本特性发布均仍待完成。

## 2026-10-01 当前交付与实施边界（本轮只读复核）

四仓 `codex/juyiting-multimedia-deliberation` 已建立、推送并包含当前 fast 代码；[精确远端回执](integration-evidence-20260928/fusion-branch-design-current-readback-20261001.json)记录 API `8121e8d8`、Web `8b8c951d`、Client `71b26ce6`。其后 Web 多轮 EXECUTE 切片已接受并推送 `4f21fa42`，见[实际修复证据](integration-evidence-20260928/web-followup-4f21-source-accepted/portable-manifest.json)。长期方案、详设 v2、媒体/存储详设和开发计划已交付，继续使用下文“阅读顺序”，不另建第二套架构合同。

最新实现风险：[本轮整合与待办](integration-current-design-and-contract-findings-20261001.md)明确 Web 多轮候选的四项实际合同遗漏、API 最新语音组合的真实 OOM/NOT_RUN、schema v1/v3 重启兼容写集，以及自然澄清/INSPECT/多请求媒体的未关闭范围。失败候选未提升；**分支与文档完成，不等于完整产品已发布或可验收**。下文旧 SHA/限制均保留各自历史时点；源码当前 pin 以 `integration.yaml` 为准。


当前研发分支：SDD / API / Web / Agent Client 四仓 `codex/juyiting-multimedia-deliberation`。

**本轮进展（2026-10-01）**：[Client v3精确来源/EDIT源码](integration-u2-client-v3-source-edit-20261001.md)已43离线定向通过并精确FF/push到`71b26ce6`，声明强制disabled、不调度生产；[API桥](integration-controlled-bridge-verification-progress.md#api桥源码已验证并推送2026-10-01)`f89d4de3`已推送，Chat25本轮实际通过、Agent57/真实MySQL3复用实际证据；Web`8b8c951`已融合develop、120定向通过。API当前develop语音融合施工中，完整多轮/费用/双接应与34项产品验收未完成。

**2026-10-01 最新执行进展**：[完整桥与develop融合的实际验证](integration-controlled-bridge-verification-progress.md#最新实际验证补充2026-10-01)已保存API桥57项9失败及Web语音组合3失败/lint19项原始便携证据，交回原Owner限定修复；未提升失败候选。分支与长期详设交付不变，完整产品仍未发布/验收。

**最新请求交付核验（2026-10-01）**：[交付说明](fusion-delivery-handoff-20260930.md#最新分支与详设交付核验2026-10-01)及[远端/文档回执](integration-evidence-20260928/fusion-current-branch-design-readback.json)确认四仓分支已推送且包含当前fast，长期方案/详设/计划已齐备。源码pin为API `99ff1a43`、Web `8244f5a`、Client `5548052`；分支与文档交付已完成，完整多媒体产品仍在实施，未发布、未验收。

**本次请求交付复核**：四仓远端 feature 与本地 HEAD 一致，且当前 fast HEAD 均为 feature 祖先，已有合入无需重复 merge。详见[交接最新复核](fusion-delivery-handoff-20260930.md#本次分支与详设交付复核)及[精确分支证据](integration-evidence-20260928/branch-design-reverification.json)。本次仅补交接与核验，不变更源代码、不合 develop、不发布；完整产品仍未验收。

**2026-09-30 本次交付入口**：[长期融合详设交接](fusion-delivery-handoff-20260930.md)汇总精确远端分支核验、完整详设合同导航与开发顺序。fast已合入不等于最新develop已合入，更不等于产品已验收；下文旧切片限制保留对应日期的历史含义。

**本分支合入 fast-deliberation 作为开发基础，不表示完整多媒体业务已完成或可以直接部署。** 精确源码、实际测试、未关闭风险见 [整合回执](integration-baseline-20260928.md) 与 [U1增量证据](integration-u1-20260929.md)。

## 最新源码整合补充（2026-09-30）

[原生能力协商四仓源码整合](integration-u1-native-capability-source-20260930.md)已同步 API `5668c747` / Web `ab317fa` / Client `1812e5b` 的研发 pin 与远端证明：API 83、Web 144、Client Owner 172 项定向通过。旧交接/切片中的“协商施工中、页面未接线”保留其历史含义，最新状态以此补充和 `integration.yaml` 为准。引用入口仍 EMPTY_ONLY，合法费用授权及完整澄清/EDIT、双接应/Provider/浏览器/版本发布未完成，**不表示可验收**。

## 任务参考图源码融合补充

[本次源码与缺口](integration-u1-task-linked-reference-source-20260930.md)：API `74b4b44e` Owner66定向、Web `7821209` Owner108定向通过并精确FF/push；参考图策略默认关闭，费用仍未授权。原子创建候选的实际MySQL2失败已定位并交回原Owner，未提升该候选；新develop语音修复仍需收敛。源码交付不是发布或完整34项产品验收。

## 本次精确验证补充

[受控图像桥实际验证进展](integration-controlled-bridge-verification-progress.md)：四仓远端fast ancestry重新核验；API实际38项中5失败/3跳过，Web精确组合重现会话采用/迟到恢复/issuer阶段缺口。候选均未提升，原Owner继续修复；分支和详设已交付不等于产品可验收。

## Provider core 与页面恢复：最新实际验证

[普通验证/MySQL/页面恢复补充](integration-provider-core-normal-mysql-web-recovery-progress.md)：API `99ff1a43`已以实际56项通过（Agent39含真实MySQL3、Chat17，0fail/skip）精确FF/push/readback；Web `8244f5a`以83项实际回归/scoped lint及Main真实Page闭包证据整合，覆盖issuer-only恢复、自动PREPARING→ATTACHED及目标/授权/修订迟到fence。SDD研发pins/gitlinks同步，历史失败保留。API Grant/execution/START桥、多轮及34项产品验收/Provider/发布仍未完成，不通知可验收。

## 阅读顺序

1. [需求方案](spec.md)：用户流程及不做什么。
2. [长期融合方案](long-term-fusion-plan-20260928.md)：统一议事，不保留两个独立聊天系统。
3. [融合详细设计 v2](fusion-detailed-design-v2.md)：统一入口、授权、路由、上下文、状态机、兼容。
   - [2026-10-01 多轮与每意图授权详设补充](long-term-followup-authority-design-20261001.md)：资料可用/查阅分层、首轮GEN不能借权EDIT、统一follow-up与实施依赖；具体HTTP/DDL待Owner冻结。
4. [原 UI / 媒体 / 归档与验收详设](design.md)：未被v2覆盖的合同继续有效。
5. [融合实施计划 v2](fusion-implementation-plan-v2.md)：U0–U4工作包及Owner/依赖/验证。
6. [分版本交付与验收计划](acceptance.md)：候选 1.13.45–1.13.47 的出厂条件与通知标准。
7. [验收](acceptance.md)：AC01–AC22，另加详设v2的FD01–FD12；共34项产品用例。
8. [集成状态](integration.yaml) 与 [便携证据](integration-evidence-20260928/README.md)。
9. [2026-09-29 轻量议事与 Agent 基础整合](integration-u2-chat-agent-convergence-20260929.md)、[受权媒体读取候选](integration-u2-media-read-20260929.md)、[U2会话执行lease集成](integration-u2-lease-20260929.md)、[U2受权输出清单](integration-u2-output-catalog-20260929.md)：均默认关闭，不等同上线。

- [受权媒体 HEAD / 音频 Range 验证](integration-u3-media-range.md)：API 单段字节范围、无正文 HEAD、416/If-Range；仍需浏览器和正式发布。
- [回复流内多媒体片段回归](integration-u2-web-reply-stream-parts.md)：`part.ready` 不再被请求状态处理吞掉；仅验证 Web 接收端，不是后端生成 `part.ready` 的证明。
- [待确认保存操作的恢复](integration-u3-archive-pending-reconcile-20260930.md)：服务端仍 pending 时用户显式复用原键 POST；后端归档接口仍未联通。
- [工作空间归档服务端原语](integration-u3-workspace-archive-primitive-20260930.md)：可信会话字节及来源校验后可创建 owner-scoped 文件版本；Chat 资产绑定/归档接口尚未接通。
- [会话成果归档的刷新恢复](integration-u3-archive-resume-20260930.md)：Web 同身份会话内保留原保存幂等键与操作ID；服务端归档仍未实现，不能将本切片视为归档验收。
- [议事会话内成果展示证据](integration-u2-web-inline-transcript.md)：受权成果组件进入同一聊天滚动区；仍未持久化 `part.ready`，未做浏览器验证。
- [2026-09-30 多轮媒体成果持续展示证据](integration-u2-web-live-gallery-20260930.md)：首稿后继续发现后续 EXECUTE 的已提交成果，尚无浏览器验收。
- [2026-09-30 客户端参考图+生图单次接应组合证据](integration-u2-client-references-20260930.md)：开发分支已整合，仍默认关闭、未付费/未部署。

## 2026-09-30 当前增量状态

[持久会话资产整合证据](integration-u3-durable-assets-20260930.md)：已提交输出可投影为持久消息/parts/事件，刷新历史可恢复；私有资产读取复用受权内容接口。默认关闭，未部署。

长期合同仍以详设 v2 为准；上述旧切片中的“未持久化/归档接口未实现”是对应切片当时的限制，不是本次最新状态。[成果区保存合同映射](integration-u3-output-asset-archive-20260930.md)现已源码接通，复用已有归档客户端及服务端 assetRef；**仍缺正式验收/完成编排及真实全流程验收，不能宣布可验收。**

[正式验收界面与原操作恢复](integration-u3-finalization-web-20260930.md)已完成Web源码切片，57项定向通过；[finalization冻结合同](finalization-contract-v1.md)是跨仓实现合同，API尚未整合/验证。UI完成不代表正式提交、领域验收或需求完成已真实联通。

[验收完成后的任务投影刷新](integration-u3-finalization-completion-refresh-20260930.md)已补齐Web联动，61项定向通过；只读刷新，不本地伪造任务完成。后端正式验收与schema启动依赖仍在开发，不通知可验收。

[原点将意图与只读恢复组件](integration-u1-web-point-and-start-20260930.md)已推送Web `7ac3bbc`，182项定向回归通过；实际页面/服务端能力协商仍未接通，不把恢复组件当点将全流程完成。

## 开发注意

- 先处理U0残留与U1合同，不直接启用所有能力开关。
- 明确生成请求可直接进入已授权execution，不强制先调用快速聊天模型。
- CHAT、资料读取、EXECUTE是权限边界，不是三套会话/三次固定模型调用。
- 老 `/chat/stream` 不开放execute hint；新编排器经任务授权调用既有执行链路。
- 未保存到个人空间的会话产物仍持久；试稿、归档、正式交付/验收分开。
- 新API/表逻辑名是拟议设计，不能把接口目录当已经部署的实现。
- 按最新AGENTS/Owner自检政策，使用独立worktree；不覆盖他人脏改、不创建Reviewer、不擅自部署/付费调用。

## 点将入口的真实闭环补充（2026-09-30）

[四仓远端分支与fast ancestry重新核验](integration-evidence-20260928/branch-reverification-20260930.json)已通过，且均与远端feature readback一致；这不是当前develop融合、构建或发布证明。[点将即办理入口详设 v1](point-and-start-entry-design-v1.md)记录实码缺口：页面普通点将仍走legacy，权威当前requirementRevision没有浏览器读接口。下一包按ENTRY-A/ENTRY-W/ENTRY-I接通原键v2点将、canonical投影及自动进入同一悬赏议事；不得猜revision=1、将grant当task、重发首轮或据UI单测宣称业务闭环。

## 原点将操作的只读恢复合同（2026-09-30）

[原点将操作只读投影合同 v1](assignment-operation-read-contract-v1.md)固定浏览器以**原幂等键**核对 grant / bootstrap / 当前 assignment 的响应、权限和恢复语义。该接口仍是施工合同，不能将文档链接或 `ADMITTED` 回执当作已生成媒体、已交付或已验收。

- `GET` 不 claim outbox、不创建消息或执行、不调用 Provider；404 不证明原 POST 没有被受理。
- 自动进入议事必须读取确切 conversation / initial request，验证 task、assignment、显式目标 Agent，再加载历史/事件；不从列表猜测、不补发首轮。
- grant 的允许操作集合与首轮 `initialOperation` 必须区分；“允许生成并修改”不等于首轮同时执行两次。当前接口实现缺口仍需独立代码包处理。
- [本次远端复核](integration-evidence-20260928/branch-followup-verification-20260930.json)只证明四仓分支与 fast ancestry；API 本地 schema-readiness 候选尚未验证/推送，不替换已记录的远端研发 pin。

## 真实首轮会话采用切片（2026-09-30）

[首轮采用与native成果终态源码证据](integration-u1-web-bootstrap-adoption-20260930.md)：Web `0e9be06`，130定向通过（新增35）。已受理首轮可精确挂入同一议事，原生媒体本轮终态只读核对后解除忙碌，领域任务完成不被混淆。**页面点将连接、后端候选验证及真实画鸟流程仍未闭环。**

[首轮动作与完整授权集合合同 v1](initial-operation-contract-v1.md)固定可选selector、旧请求hash兼容、单bootstrap与原键只读恢复；两个独立Owner正在按不重叠写集实现，不把允许操作集合当同时执行的动作清单。

## 当前schema验证与原生能力施工补充（2026-09-30）

[旧弱CHECK识别与真实Java/MySQL证据](integration-u3-schema-check-truth-20260930.md)已验证API `b1e7b068`：正常84项报告（42本次、42复用）及真实6项JDBC/Spring全部通过；不是整套启动、迁移或产品验收。

[原生悬赏能力/点将协商冻结合同](native-bounty-capability-contract-v1.md)新增独立native声明，保留fast-v1 EXECUTE=false；API、Web页面与Client分别施工。task引用/澄清/EDIT/合法费用桥、双接应与真实浏览器仍必须完成。候选版本号按版本计划末尾的远端占用补充重新核实。


## 需求前可选参考图施工（2026-09-30）

[需求创建与可选参考图原子受理合同 v1](requirement-reference-intake-contract-v1.md)已冻结：普通榜文由一个持久原操作创建真实task和精确REFERENCE关联，刷新只读查询，明确继续才原键/原正文重放；旧普通/funded接口不扩大权限。Web候选已接真实Bounty草稿、原请求恢复及页面路由，组件选择器与API事务实现分别独立施工；候选尚未成为跨仓生产基线。选择参考图不会放开当前native EMPTY_ONLY或费用授权；后续必须接真实task-file回读与执行输入、合法费用桥、澄清/EDIT及最终浏览器发布验收。


本次参考图施工期间再次核实[四仓当前远端分支](integration-evidence-20260928/branch-reference-intake-verification-20260930.json)，均已包含当前fast；[交接第8节](fusion-delivery-handoff-20260930.md#8-需求参考图施工期间的远端复核2026-09-30)保留候选与产品验收区别，以及确定拒绝原意图的安全处置待办。Web候选仍需修复选择器异步替换竞态并验证组合树，不将两项夹具组合测试视为真实画鸟通过。


## 2026-10-01 参考图入口Web整合

[Web精确组合源码证据](integration-u1-reference-intake-web-20261001.md)：远端`84b14a5`，213定向通过，scoped ESLint通过；真实需求表单、真实选择器和真实创建composable已组合验证，选择器异步替换竞态已修复。上文旧候选/施工限制保留对应日期含义。API仍独立验证，不把此Web研发pin当成跨仓联调、资料执行或可验收；native仍EMPTY_ONLY、费用未授权，完整34产品用例NOT_RUN。


[任务已关联参考图点将合同 v1](task-linked-reference-point-and-start-contract-v1.md)冻结下一包：完整任务目录与精确版本回读、TASK_LINKED_REFERENCE真实能力政策、原意图优先、执行事务重验；不放开费用或提前通知可验收。

## 原子参考图创建缺陷已修复（采集时间2026-10-01）

[原子创建真实MySQL与源码整合证据](integration-u1-atomic-reference-intake-source-20261001.md)：API研发pin提升到`083f9846`，20项通过（含实际MySQL2、Spring事务2），零失败/错误/跳过；原catalog失败已修复，历史失败保留。上文“API候选尚未整合”属于旧时点；当前仍默认关闭/无合法费用桥、无真实34产品用例、无发布。

## Provider权限与真实调用前控制

[费用来源与pre-call长期详设补充 v1](provider-authority-and-precall-enforcement-design-v1.md)明确：现有单次executor START不保证单次imagegen调用/扣费；平台template账户需要operator delegation与taskOwner同意，不能只写非空costRef。受控图像adapter及费用wire尚未冻结/实现，不切换Provider或开放费用入口。

[同会话澄清/续办/上一稿修改详设准备](multiround-followup-design-notes-v1.md)列出源码确定的拒绝路径、可复用assetRef与恢复链，以及下一份合同的最小写集；这不是已接通EDIT或已冻结wire。

[受控图像账户与单次请求core合同 v1](controlled-image-provider-core-contract-v1.md)冻结下一源码包：真实operator policy + owner exact consent、当前binding声明、持久一次HTTP调用adapter。core阶段不接旧grant/START费用权限，不选真实账户或执行付费；全产品目标保持不变。

## 受控图像与费用同意 core：最新源码补充

[源码融合与证据](integration-provider-core-source-progress.md)：Client `69765549`（193项定向通过）与 Web `1ceb48d`（69项定向通过）已精确FF、推送并readback；[Web core 合同 v1.1](web-provider-consent-core-contract-v1.md)规定 EXPIRED 只读投影、显式同意和 task/target 迟到响应隔离。API `acab3411` 是尚在验证的候选，不提升API研发 pin。上文“受控adapter尚未实现”的旧记录保留其历史时点含义。

core **不等于合法点将/START费用桥或页面闭环**：未选择真实账户/模型，未启用付费，未做34项产品用例、双接应浏览器或版本发布；不通知可验收。

[受控图像Grant/execution/START桥接详设 v1](controlled-image-grant-start-bridge-design-v1.md)补充下一完整桥接的入口wire、aggregate/回滚、一次消费与版本化16输入协议、Web显式同意及三仓写集；拟议wire须先冻结共同fixture，不当作已实现或可收费的接口。

## 合法费用桥：共同 wire 与五组 fixture

[桥接冻结合同 v1](controlled-image-bridge-contract-v1.md)将上一详设的拟议wire固定为独立受控capability/点将/原键读回、同session能力协商、v2 command及仅首次成功START回执，并闭合root-first三段事务、authority查证及16输入边界。[29项共同预期fixture](fixtures/controlled-image-bridge-v1.json)全部NOT_RUN；静态字段/摘要检查及现有Web core issue/BOUND receipt兼容检查通过，**不是桥接实现或34项产品验收通过**。

后端验证环境曾有argparse错误、stale baseline ABI、正常图javac堆不足；保留失败，改为exact-source正常图输出，不以环境错误归因业务或用静态兼容替代真实事务。API core仍须实际验证后整合，Client/API/Web下一包按冻结wire实施；未启用账户/Provider，未发布或通知可验收。

### develop文档收敛与实施启动（精确SHA补充）

SDD融合提交 `6c347c444d91d783885cbfc77b31e7f2c99dbd36` 已推送/readback；父提交为本合同 `69a2a420` 与 develop `01f7599e`。只解决 INDEX 冲突：保留本功能 implementing/34项范围，并保留 develop D2典籍任职入口；D2整目录与develop字节一致，组件gitlink未变。此只证明SDD文档收敛，不证明API/Web最新develop语音已融合。

BRIDGE-A/C 已由两个Owner在独立API/Client worktree按冻结合同施工，不创建Reviewer。API原core `acab3411` 保持未验证候选：正常源图已编过agent主类，但无测试/XML；common-test的Testable AP在384MiB仍堆不足。下一修正基于实际11个standalone测试的imports，由原Owner提交仅定向sourceSet依赖修复，保留全部测试/真实production源码图和标准full-test配置，不再盲增堆、不disable AP、不复制baseline类或假overlay。新候选实际通过后才能提升API pin；真实MySQL、跨仓桥接、34产品用例和发布仍未完成。

## 受控 v2 Client 源码整合补充

[Client精确源码及真实修复证据](integration-u2-controlled-image-v2-client-source.md)：研发pin提升到5548052/tree59af3，Owner157定向通过、Main12项纯parser断言及hash核对后精确FF/push/readback。原初稿154通过未覆盖的grammar/epoch/UNKNOWN和类型强制转换缺陷均由原Owner修复；没有真实Provider或产品验收。API核心实际编译缺失Hamcrest仍修复，API/Web合法费用桥和多轮完整范围继续施工，不通知可验收。
