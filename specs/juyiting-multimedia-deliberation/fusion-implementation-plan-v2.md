# 长期融合实施计划 v2

> **2026-10-03 最新实施指令**：用户明确“无需做太多兼容补丁，一切都按新方案实施”。新入口、新请求统一走通用资料与按需议事；不新增旧生图入口、双轨产品流程或回退适配工程。只保留身份隔离、幂等、未完成请求及既有内容保护，不以历史兼容覆盖率阻塞新方案。

> **2026-10-03 用户纠偏（当前优先）**：[通用资料详设增量v3](unified-materials-correction-20261003.md)取代独立参考图入口及图片限定业务流程。唯一“添加资料（可选）”须支持图片/文档/音频等；Agent判断用途，通用会话、输出、保存与交付保持完整范围。不是文案改名；绘图专用wire仅作为执行适配，不扩展旧产品入口，原34项需补UM01–UM10。当前已完成创建/资料基础源码自检，通用点将会话链路与整体验收仍待完成。

日期：2026-09-28。本轮已授权的是 feature 整合与设计；后续业务包仍是计划。运行状态只在主工作区 `/home/isp/wsps/cyf/docs/implementation/TASKS.yaml#runtime_ledger_json` 登记，本文件不是第二套运行 ledger。

## 2026-10-01 回执领域修复：当前最小施工顺序

本节是工作包依赖，不是运行台账；不存在/失效Agent句柄不能当作正在施工或验证。复领任务须先核验实际Owner与路径归属，不创建独立Reviewer。

1. API以干净typed组合`8fc61c4`为候选基线，仅修typed Admission持久回执为`ADMITTED/0`及对应新受理/原键replay测试；原RequestView/TurnView状态不改。保留原final事务、pending CAS、真实session能力及全部历史协议边界。
2. Web以干净`891a1ec`为候选基线，仅修新typed适配的合法RequestView状态采用，保留原身份/目标/会话/唯一turn绑定和低版本防回退。原七边界、同版本OPEN、UNKNOWN原键恢复、content失败不重复POST继续回归。
3. Main只读核验本轮193项套件通过但两项合法状态失败，故两候选不晋升。[回执v1.1合同](typed-deliberation-receipt-adoption-contract-v1.1.md)/TRA01–06跨端共同用例仍NOT_RUN；不得为了过probe修改旧fixture或全局legacy reducer。
4. API最小CHECK-catalog child`3351bf3`已经在8fc组合中，但V6未启动；须由有实际归属的Verifier经orchestrator正常图完整62V3（包括隔离MySQL3），通过后82V2，并完成typed60/16共同事务/真实数据库核验。沿用精确selector，失败归因不盲重跑。
5. 通过后才更新组件feature/pin，继续真实INSPECT、双接应、多媒体/保存/正式交付验收及版本发布。193项源码套件不代表34项产品验收；旧计划版本号发布前重新分配。

具体HTTP以已冻结原子typed v1的`interactions/discussion`为准，独立EXECUTE v3继续沿用；早期设计中schema-3讨论候选不另行实现。[证据与精确SHA](integration-evidence-20260928/typed-receipt-adoption-20261001/manifest.json)。

## 1. 分支与实施策略

四仓统一分支 `codex/juyiting-multimedia-deliberation`，以各自精确远端 develop 为第一亲合入 fast 的精确提交。保留 develop 修复和 fast 基础，不强制覆盖任何一边，不更新 develop/release，不触发部署。

组件的真实 merge commit 保留两个父提交。SDD 仅引入 fast feature 文档目录，保留 develop 的其他文档与新多媒体规格；历史无关文档变化不顺带传播，api/web gitlink 在组件已推送后固定。原 fast 分支不改写、不删除，后续工作集中在新分支。

[M0 源码表/端点映射与待冻结项](m0-source-mapping-and-contract.md)是U1/U2实现的施工对照，尚不是迁移通过或新接口上线证明。

## 2. 后续工作包与依赖

| 包 | 责任建议/路径边界 | 交付内容 | 依赖 | 通过证据 |
| --- | --- | --- | --- | --- |
| U0-A | API Owner；chat admission/relay、身份、上下文 | 收口F1–F3：可信身份、逐目标协商、可重建历史/宋江快照；兼容machine JWT/迁移 | 本轮整合基线 | final tree的相关Java回归、实际schema/认证夹具；未测不标通过 |
| U0-R | Client Owner；chat-runtime/app-server/agent-client | 真实能力声明、read-only-constrained隔离、INSPECT固定manifest；保留START/恢复 | 冻结wire，与U0-A并行 | 默认/新版Profile、双接应、隔离/能力负向、冷恢复 |
| U1-A | API Owner；task授权/交互准入/执行协调 | grant、steps/link、统一入口、direct execute、澄清/撤权、事务outbox/CAS | U0合同确定 | FD01–FD10的服务级夹具；DDL和source mapping固定 |
| U1-W | Web Owner；会话交互/状态/reducer | 同一UI提交意图、授权状态、明确取消目标、请求聚合，不强制第二次开始 | U1合同，可mock并行 | 主状态、旧消息、晚到媒体、身份切换回归 |
| U2-A | API Owner；会话asset/workspace/delivery | CONVERSATION用途、未归档可读、精确输入、媒体读取、选定成果晋升/验收 | U1-A | ACL/摘要/保存与交付分阶段、producer身份/幂等 |
| U2-R | Client Owner；workspace-file-bridge | 精确参考/上一稿输入、outputs提交、execution-part关联 | U2合同，与API并行 | 真实字节/input digest/START/output commit；旧PRIVATE/TASK |
| U2-W | Web Owner；需求资料/图片卡/归档/验收 | 无参考/有参考画鸟、直接修改、放大/下载/保存与最终清单 | U1-W、U2合同 | 浏览器图片纵切，不能用mock图代替最终验收 |
| U3 | 各组件格式Owner | 音频播放/Range/保存，文本选区，普通文件和混排，双接应/断线恢复 | U2 | AC全部范围 + FD11/FD12；不冒充音频生成能力 |
| U4 | 集成Owner/gpt_test_runner | exact pair联调、实际MySQL、迁移/旧新协议、Provider已授权端到端；兼容退出评估 | U0–U3 | AC01–AC22 与 FD01–FD12 共34项实际状态，构建/部署/业务验收分开 |

U0不是新的独立Reviewer队列；Owner自检后按真实证据推进。

## 3. 与 v1 工作包的映射

- F0 拆为本轮 merge conflict 整理与后续 U0 能力/上下文/隔离收口；不把冲突已解决等同缺陷全部关闭。
- M0 由长期方案、详设v2建立决策基线；具体DDL、DTO和wire夹具仍须U1冻结。
- B1/B2/B3 对应 U1-A/U2-A；R1 对应 U0-R/U2-R；W1/W2/W3 对应 U1-W/U2-W/U3。
- I1 是图片纵切，不代表整体完成；I2 扩展为 AC01–AC22 + FD01–FD12。
- 原R0发布包只在真实上线条件和授权成立后执行，本轮没有release/deploy授权。

## 4. 变更边界与退出要求

每个Owner只写自己的worktree和已分配路径；相邻API grant/asset/delivery由同Owner或显式交接处理，不能多人争用一文件。不同仓/模块可并行，不设置无依据的全局串行源代码队列。

每包交付：exact commit/tree、冲突/合同变化说明、最小selector、实际结果及日志、DB fixture digest（涉及数据库时）、未完风险。不在SDD中用未经测试的源码pin冒充accepted基线；开发pin明确标研发基线。

兼容adapter退出需有目标客户端迁移与在途请求处理证据；默认目标不可假定已升级。收窄能力声明可以作为安全过渡，不能按此标“功能已完成”。存储复制字节可长期保留，不为去重做无关大迁移。

## 5. 核心风险专项

- 撤权/重新点将与START/下载/上传竞态：检查grant/assignment/run版本，不能仅前端按钮禁用。
- 用户资料注入：C1元数据不冒充C2真实读取，附件不能授予工具/费用权限。
- 多Agent与多owner：目标能力和上下文独立，不能广播私有结果或共享模型线程。
- 部分完成：text_final、asset.ready、archive.saved、delivery.submitted、decision.accepted、task.completed分开恢复。
- Provider结果未知：承认未知并对账；不能宣称网络级exactly-once，也不能自动重跑导致重复收费。
- 功能开关不代替数据库/认证风险检查；新schema与machine JWT变更需实际夹具证据。

## 6. 本轮验证范围

按实际整合树进行冲突标记/whitespace/语法、Web与Client相关定向测试；API检查最近build.gradle后通过orchestrator进行必要验证，实际执行范围和失败归因以 `integration-baseline-20260928.md` 为准。

本轮不会为了文档中的未来功能跑付费模型、浏览器生成、真实库迁移或生产构建。没有实测的事项保持NOT_RUN；性能慢只记观测，不新增任意数值硬门槛。无Reviewer，未修改其他任务进程/服务。

## 2026-09-30 入口闭环增量

新增[ENTRY-A/ENTRY-W/ENTRY-I施工包](point-and-start-entry-design-v1.md#5-最小开发包与验证)：从权威当前requirement snapshot读接口接通真实v2点将和自动议事。可以与独立finalization/schema-readiness路径并行，但组件pin须基于已测试候选。此处仅任务定义，不是第二套运行ledger，不改变现有Owner写集或产品验收状态。


### 入口恢复合同施工补充

[原点将操作只读投影 v1](assignment-operation-read-contract-v1.md)为ENTRY-A/ENTRY-W固定追加合同：服务端按原键提供owner-safe的grant/bootstrap/current-assignment事实，Web按确切首轮request采用同一议事历史与事件。API写集与finalization/schema-readiness隔离；读取投影、会话采用以及真实页面v2点将是不同切片，不因其中一项完成即关闭入口包。验证须覆盖无写入/无Provider、404未知、撤权/重派、版本精度、身份切换、错误回执与首轮不重复。

首轮动作与grant操作集合的拆分仍需独立实现，不在只读投影或Web中绕过服务端准入。当前进行中的API候选未验证前不更新跨仓gitlink；实际Java测试阻塞归因与下一步诊断保留在Owner证据中，不把文档静态检查冒充运行测试。


### ENTRY首轮采用源码进展（2026-09-30）

[Web采用切片](integration-u1-web-bootstrap-adoption-20260930.md)已推送并通过130定向，页面真实点将/完整ENTRY-W尚未完成。下一步接权威当前revision、原key/body持久readback、原操作投影与canonical任务，调用该采用函数；不能补发首轮或据媒体事件本地完成任务。

[初始动作合同 v1](initial-operation-contract-v1.md)为grant/DTO和只读projection分配不重叠写集，旧hash兼容和单outbox为共同fixture。仍需完整服务编译/测试、真实DB及跨仓页面验收；source acceptance与产品验收分开。


## 2026-09-30 原点将恢复组件增量

- ENTRY-W恢复组件已源码合入Web `7ac3bbc`：182定向通过，其中45新增；[证据](integration-u1-web-point-and-start-20260930.md)。原key/body、grant!=TaskDTO、纯读/显式恢复、独立fence与身份隔离已补；不代表实际页面已启用。
- 下一依赖顺序：API readiness修正验证 → finalization/current requirement/projection/initialOperation及selector-only Controller路由整合/回归 → 权威能力协商与页面接线/实际引用关联 → 真实澄清、上一稿/修改和费用授权 → 双接应/Provider/浏览器全范围 → exact版本制品发布及线上验收。
- 不对未完整业务分支提前合develop/启用/发布；未实测状态不改PASS。实际阶段推进继续使用唯一runtime ledger，不设Reviewer队列。

## 2026-09-30 组合源码验证增量

[ENTRY/finalization/readiness组合候选](integration-u1u3-entry-finalization-20260930.md)已推送API `f93febe9` 并提升研发pin；正常模块357次执行、bounded99项、独立MySQL26项和归属锁验证通过。后续不重复把未变的组合树全部重测当作进展；按exact tree/selector/fixture复用证据，对实际新改动补相关验证。旧弱CHECK识别/授权迁移、真实Java/MySQL生命周期、目标能力协商/页面接线、真实引用/澄清/EDIT/合法费用授权与最终全范围发布验收仍单独施工。无develop/release/生产激活或可验收声明；运行状态仍只在runtime ledger。

## 2026-09-30 schema修复完成与native能力施工

[本次证据](integration-u3-schema-check-truth-20260930.md)关闭精确候选的旧弱CHECK识别及隔离Java/MySQL初始化验证缺口；整套启动、实际旧库授权迁移不合并关闭。

[冻结native合同](native-bounty-capability-contract-v1.md)下一包按仓库隔离并行：API Owner实现声明解析/当前session身份源/只读协商；Web Owner接真实页面点将与原意图恢复；Client Owner由真正启用的执行器/配置生成注册声明。三个写集不涉及schema initializer，遵循Owner自检无Reviewer；精确验证后再提升pin，不把施工任务当第二ledger。

此包是必要前置，不代替合法费用授权、task-file引用入榜与回读、同会话澄清/EDIT和派生产物；当前费用ref为空时禁止付费准入。最后仍必须完整两种接应/Provider/浏览器/版本发布再通知可验收。


## 2026-09-30 native源码整合及当前实施授权补充

[四仓 native 源码基线](integration-u1-native-capability-source-20260930.md)现已通过精确源码验证并更新pin，页面原键恢复与能力协商已接线；真实引用/费用/澄清/EDIT/产品全流程仍按依赖继续，不重复改写旧切片结果。当前用户持续目标是实施后按版本发布、可验收时通知；早期“仅设计/无发布授权”限于当时动作，不阻止达到上线条件后的普通已授权发布。付费调用、生产数据和迁移授权不据此扩展；本次无发布或产品通过。下一包优先需求前可选精确参考图、任务创建/引用关联与合法费用授权桥。


## Provider权限与调用前控制的真实依赖

[调用前详设补充v1](provider-authority-and-precall-enforcement-design-v1.md)把实际native源码缺口单独列清：普通executor START只防整次重启，不保证内部只生图一次/只扣费一次。下一费用工作包须先冻结真实operator delegation + owner exact consent + 可执行pre-call adapter合同，再分配Client/API/Web非重叠写集。无真实适配器不开放费用lane，不擅自切换Provider；mock计数回归与实际付费验收分别报告。

原子参考图创建已源码晋升API083f（20通过，含实际MySQL2及事务2）；此处不建立第二份任务台账。[整合证据](integration-u1-atomic-reference-intake-source-20261001.md)保留原缺陷、失败及exact合并树证明。原始宿主时间戳不代表当前日期或发布日期。

[多轮follow-up源码准备](multiround-followup-design-notes-v1.md)是下一合同冻结入口：先落持久澄清/parent lineage与精确conversation-asset resolver，再统一成果卡/composer发送恢复。当前EDIT确定被拒绝，且无真实EDIT-capable bridge；不要只改Web或新造会话规避。

## 受控费用 Grant / START 的下一完整桥接包

[桥接详设 v1](controlled-image-grant-start-bridge-design-v1.md)将core之后的缺口收敛为BRIDGE-A/C/W/I：原点将与consent绑定、唯一execution预留、同事务consume+START、受控16项v2命令/回执与显式页面同意，不能只写非空costRef。这是待Owner核对并冻结共同wire fixture的详设，不是源码完成；真实费用账户仍未选择/授权，不推导付费许可。运行状态只记录在主工作区唯一ledger。


## 自然讨论与多稿发现的当前实施顺序（2026-10-01）

此处是工作包依赖，不是第二执行ledger；实际Owner/gate只在主工作空间runtime_ledger_json。

1. **互不重叠的源码包**：API 74路径owner/source/per-intent包；API六leaf只读请求目录；Web独立多request catalog；Client原生typed union/stream/atomic final。各包完整自检后交干净child，未完候选不能晋升；不设置Reviewer。
2. **精确组合验证**：按tree/selector/fixture复用已核验42d的Agent57、Chat25、Voice129，不为未改树全套盲重跑。新API包补正常源图/隔离MySQL、default-off旧schema与v1/v3重启、并发/ACL；Web补实际Vue/Page多稿同名output、read-hint、刷新/晚低ID重扫和迟到fence。Gradle经orchestrator串行、等待不抢占。
3. **API自然交互闭包**：依据[已冻结Client结果合同](typed-deliberation-client-result-contract-v1.md)冻结服务端可信snapshot/typed final原子持久化及pending question/CAS/原键恢复/resume合同；完整实现并验证，不能将Client-only结果当业务完成。Web再接唯一Hall composer与问题/提议显示，EXECUTE仍走独立owner明确同意/issue/admit，不复制第二套会话。
4. **真实查阅与全媒体**：固定本轮资料manifest及能力后实现INSPECT，不支持就诚实不可用；验证文本/图片/音频/文件展示、预览/下载/保存，以及正式交付、验收、实际需求完成。历史读和当前写权限分开。
5. **发布与通知**：全部34产品/29桥用例、山寨安顿/自家接应实际验证和浏览器闭环完成后，自检合组件develop，从未占用的实际exact版本发布并核验制品/线上健康与产品。真实费用账户、付费和生产数据授权不从实施授权推导；本特性未发布前不通知“可验收”。

当前typed fixture的24 runtime expectations与request-index的22 expectations保持NOT_RUN，执行后另记exact evidence，不篡改冻结fixture为PASS。1.13.45–1.13.47只是旧候选示例且已有其他发布占用，后续必须重新读取真实版本，不覆盖release分支。


## typed final 校验叶子包（2026-10-01）

[服务端严格校验/摘要合同v1](typed-deliberation-api-final-validator-contract-v1.md)和中文黄金fixture已冻结，30 runtime预期尚未运行。新三个叶子路径与现75路径每意图授权Owner互不重叠，可并行实现；只处理exactfacts/union/binding和canonical完整摘要，不碰Handler/Interactions/StepStore。随后完整原子落库/pending question CAS/resume包接线，不能拿纯validator通过代替澄清/自然多轮完成。新版发布按各里程碑适用范围实测，不要求基础版冒充34项完整产品通过；任何“画鸟可验收”通知仍须实际目标版本在线和对应浏览器闭环。


## 2026-10-01 回执修复施工补充

按[最新领域实施优先级](integration-typed-receipt-source-adoption-20261001.md)执行：Web ebb 源码已接受；API642e仅候选、V3真实MySQL CHECK失败须新源码修复，完整正常图验证继续作为前置。自然讨论与澄清仍仅 typed schema1 入口，独立执行v3不变；不追加早期schema-3讨论或第二套问题状态机。真实INSPECT、双接应、全部媒体及浏览器正式交付验收仍在完整范围内。Owner/gate只用主工作区唯一台账；此节不记录独立运行状态。
