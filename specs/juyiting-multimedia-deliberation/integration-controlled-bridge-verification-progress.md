# 受控图像桥：实际验证进展与未关闭缺口

文档日期：2026-09-30。只读状态补充，不改冻结 wire、详设或运行台账。原始日志/快照按采集主机时钟保存（部分为 2026-10-01），不作为当前日期或发布日期。

## 分支与详设交付

本次独立 `ls-remote` + `merge-base --is-ancestor` 重新确认 SDD/API/Web/Client 四仓 `codex/juyiting-multimedia-deliberation` 与当前远端 feature HEAD 一致，且都包含当前 fast HEAD；无需重复建分支/合并。SDD及Client没有develop独有提交，API/Web分别仍有4个；发布前须收敛，不能将fast合入当作develop融合。

当前远端源码核验点：SDD `493b1187`、API `083f9846`、Web `1ceb48d`、Client `5548052`。SDD为本文提交前核验点；原始 SHA/tree/readback 见[证据快照](integration-evidence-20260928/controlled-bridge-verification-progress/latest-branch-and-design-readback.json)。研发 pins 不因候选编译或文档提交而提前提升。

长期方案继续是[统一议事与受控执行](long-term-fusion-plan-20260928.md)：fast 为 CHAT 轻量策略，按需 INSPECT/EXECUTE，不预加载全部资料/工具。主合同为[融合详设v2](fusion-detailed-design-v2.md)，[媒体/存储详设](design.md)和[实施计划](fusion-implementation-plan-v2.md)继续有效。

## API：已越过编译内存问题，但真实测试失败

- 候选 `d3baf9b0` / tree `bdf04ddb` **未合入API feature**。
- v9：正常图中 javac worker成功，Gradle daemon增量classpath snapshot耗尽heap，0测试/0XML。历史失败不改PASS。
- v10：仅两个bounded fixture JavaCompile设 `options.incremental=false`，所有11个测试源、正常依赖图、AP、production/default-full-test配置与heap不变；实际完整javac已通过并进入agent测试。
- 实际38项：30通过、5失败、3跳过，5份JUnit XML；45 actionable tasks（17 executed/28 up-to-date）。4个Controller失败缺JsonPath运行类，1个真实CGLIB事务夹具缺H2 JDBC driver。chat selector尚未执行。MySQL3为真实跳过，继续NOT_RUN，不当通过。
- 下一步由原API Owner提交最小scoped runtime依赖修复；固定新commit/tree/matrix/input后串行重测。禁止原输入盲重跑、禁AP/排测试或借baseline class覆盖。普通通过后再执行当前线程自有隔离MySQL3。

原stdout artifact未生成，不伪造stdout；保留实际daemon日志及XML。完整摘要/压缩原始日志摘要见[manifest](integration-evidence-20260928/controlled-bridge-verification-progress/manifest.json)。

## Web：组件成功不等于原会话已采用

候选 `cb65ebfa` / tree `4ed8dadf` **未提升Web feature**。Owner6项动态和69项已有回归不覆盖全部页面组合。Main从该commit导出12个精确Git blob，真实Vue + 两个composable、假HTTP实际重现：

1. issue与bridge POST成功，但页面委托旧core `checkOriginal` 被费用意图拒绝：自动采用计数0、投影GET0；不能以BOUND或 `onBound++` 代替进入原议事。
2. 显式恢复GET延迟404，在context失效后仍发出bridge POST1；应为0。
3. issuer响应丢失且尚无wrapper时，两个恢复动作HTTP0；须接原issuerkey只读核对及显式精确继续，不能改新key或转legacy。

另须补新offer/需求修订/modal关闭的同意checkbox重置、实际页面采用与恢复动态证据。原Web Owner在原写集修复；Main不修改Owner源文件。初次在途工作树探针不属于immutable证据，仅精确Git blob结果列入本补充。[重现结果](integration-evidence-20260928/controlled-bridge-verification-progress/findings-cb65-immutable.json)和[源码manifest](integration-evidence-20260928/controlled-bridge-verification-progress/immutable-cb65-source-manifest.json)可复核。

## 交付边界

分支创建、fast代码合入、长期方案及详设已交付；上述是实际验证与原Owner修复，不是产品完成。Client v2已有源码证据，API/Web桥仍未完整联通。澄清/上一稿EDIT、完整多媒体、正式验收/完成、develop语音收敛、双接应浏览器34项及精确版本发布仍要完成。

本次未调用真实Provider/付费、未选真实账户、未部署/启用或迁移生产数据库。34产品用例仍NOT_RUN，29共同桥fixture也不据这些局部测试改PASS。唯一运行台账仍是 `docs/implementation/TASKS.yaml#runtime_ledger_json`。


## 最新实际验证补充（2026-10-01）

此节更新上述旧候选状态，保留原失败历史；不修改长期详设、冻结wire、验收标准或运行台账。

### 分支与长期详设交付

四仓独立 `ls-remote` 再次读回并验证当前fast为feature祖先：SDD `308e7166`、API `99ff1a43`、Web `8244f5a`、Client `5548052`，均与本地feature一致。SDD为此补充提交前观测点。长期方案、融合详设v2及媒体/存储详设、实施计划已交付；无需重复建分支或重复merge fast。最新远端develop分别为SDD `01f7599e`、API `b2986836`、Web `33a73aa0`、Client `29fda32a`；fast ancestry不是组件最新develop已融合的证明。

### API：core已通过，完整Grant/START桥仍失败

已推送core `99ff1a43` 的正常56项（含真实MySQL3）通过证据继续有效，与下面新桥候选分开。桥候选父 `7346003f`，一行Mockito编译修复后候选 `b16848aa` / tree `cadcbc9f` 尚未提升feature。

- v1：production Agent javac完成，daemon增量分析OOM；0测试/0XML。
- v2：仅禁用production Agent增量分析，完整production编译通过；bounded fixture的Mockito wildcard编译失败；0测试/0XML。
- v3：一行`doReturn`类型捕获修复；Agent实际8 XML、57项中48通过/9失败/0error/0skip。Chat因前序失败未启动；MySQL3实际启动但全部setUp失败，业务体NOT_RUN。
- 九项失败分四类：security fixture缺jsonassert运行依赖1；完整CHECK catalog rendering drift导致MySQL3；Conversation fixture matcher/能力投影/EXISTING_RUN与ACL诊断4；authority null policy产生NPE而非typed fail-closed1。

Main已核对终态PID缺席及实际XML，按独立修复矩阵交回原API Owner生成新immutable child；不重跑旧输入、不删17fixture、不放松6bridgeCHECK/权限/一次消费断言。新的exact SHA/tree与matrix固定后才由原Verifier经orchestrator串行执行Agent+Chat；未提前宣称这些失败已修复。

### Web：无冲突develop融合不等于测试通过

原Web Owner已形成候选 `335948d4` / tree `fd0493c4`，父为feature `8244f5a`和develop `33a73aa0`；merge无冲突且树与预期相同，严格7个voice/PCM路径，原多媒体闭包字节不变。候选尚未推送/提升feature。

实际bridge83、PCM6通过；voice28通过/3失败，scoped lint19 errors。两项Page mock缺新多媒体flag，一项错误期待任意metadata.frozen绕过已有sanitize；lint为模板排版、AudioWorklet global声明、cleanup catch说明和测试规则。已授权原Owner在原7路径生成新child，修夹具/支持字段断言与lint，不放开未知metadata、不改多媒体闭包、不禁全局规则。须重测bridge+PCM+voice+scoped lint。

[便携manifest](integration-evidence-20260928/controlled-bridge-and-develop-fusion-20261001/manifest.json)保存3轮API原stdout、matrix/input/argv/preflight、v3全部8XML及Web全部stdout、两Owner修复矩阵，共33个原件；gzip解压后与原件SHA逐一一致。Web第一次ledger失败回执手工抄错self-check全hash，修复矩阵已明确纠正为`947cfaf8913c6470f38ef44afa60465ec4470e35f91418d8ba8d6bc8adfca34d`，原文件及历史均保留；不是新增源码失败。

本节只是源候选验证与修复进展。29共同预期fixture与34产品用例仍NOT_RUN；完整澄清/上一稿EDIT、全部多媒体、正式验收/完成、双接应真实浏览器与按版本发布仍须实现验证。未选择真实账户、未调用Provider/付费、未发布或通知可验收。唯一运行台账仍是`docs/implementation/TASKS.yaml#runtime_ledger_json`。


### 本轮源码推进与新实际诊断（2026-10-01）

Web候选`8b8c951d`/tree`386d1e00`已由Owner实际bridge83+PCM6+voice31共120项及scoped lint通过；Main核对实际stdout摘要/hash、原7路径及受保护多媒体闭包字节一致后，精确FF/push/readback到feature。原335失败和修夹具过程的真实stdout均保留在[便携Web证据](integration-evidence-20260928/web-develop-fusion-8b8c951/manifest.json)。旧feature checkout实际缺失但Git ref/source保留，Main新建`web-fusion-main-20261001`独占checkout继续，不操作主develop或推断是谁删除。

API桥v4`dbcd4da1`实际8XML、Agent57中54通过/3失败/0error/0skip：v3的6个非MySQL诊断已通过，bridge6CHECK已越过；3个MySQL用例仍在setUp新遇到execution表CHECK catalog drift，Chat未开始。这不是Provider/OOM失败。完整stdout/XML、实际后prefix空readback及Main两个freeze-checker的控制面错误（未启动测试时发生）均保存[本轮便携证据](integration-evidence-20260928/controlled-bridge-v4-execution-check/manifest.json)。

按正式修复矩阵，原API Owner仅在本线程精确新诊断schema中运行原fixture CREATE与v1_17 ALTER，取得`chk_pwex_controlled_consent`真实catalog、ENFORCED=YES及前后prefix/exactschema均0。新候选`29b60fee`/tree`9b0bb114`仅修initializer和独立literal正/负断言，DDL资源/17fixture/AP/heaps不变；未提升API feature。Main固定v5 matrix/input/argv并交原Verifier一次运行，实际结果待核准，不把catalog自检当57项测试通过。

下一完整多轮包的[runtime来源/EDIT wire合同v1](controlled-image-v3-source-wire-contract-v1.md)已冻结：独立v3 sibling、精确asset来源、每轮新command/consent、保留旧v2，三组合法及13组负向共同样例仍NOT_RUN。此只锁定runtime增量，owner pendingClarification/每意图费用及统一Hall composer仍须落地，不把新native样例当完整多轮已接通。真实账户未选、Provider未调用、完整34项产品仍NOT_RUN；未发布或通知可验收。


### Agent桥实际通过、Chat诊断逐步推进（2026-10-01）

API桥v5候选`29b60fee`已实际执行Agent57项（含真实隔离MySQL3），全部零失败/错误/跳过；MySQL用例已进入业务体，不再只是catalog诊断。Chat production编译完成，但fixture在`ChatBountyExecutionCoordinatorTest.java:199`因多余闭合分隔符编译失败，Chat XML0、NOT_RUN。Main重新核对Unix/TCP同一测试库身份及本线程prefix空；完整stdout、8XML、冻结输入与最小语法修复矩阵保留在[实际v5便携证据](integration-evidence-20260928/controlled-bridge-v5-chat-syntax/manifest.json)。

新child`b3593501`仅删除该多余`)`，断言和17fixture保留。v6首次进入Chat业务测试：Chat实际25项/3失败/0error/0skip，其中coordinator7及Spring事务1通过；三项WebSocket测试在Mockito反射`AgentRuntimeAuthenticationService`时因`cn.jia.oauth.service.ApiKeyService`不在bounded runtime classpath而失败，尚未到业务断言。Agent为UP-TO-DATE，复用输入未变的v5实际57项/真实MySQL3 XML，不冒称v6重新执行了57项。原stdout与17XML、Main后prefix空读回及限定修复矩阵见[实际v6便携证据](integration-evidence-20260928/controlled-bridge-v6-chat-runtime/manifest.json)。

Main已按归因矩阵授权原API Owner仅修Chat bounded fixture runtime依赖；不改变生产依赖、17测试源、权限/CHECK/一次消费断言、AP、堆参数或selector。只有新immutable child及新freeze后才允许下一次验证；未提升失败候选，不将局部测试改写成完整Bridge、29共同样例或34产品验收通过。

[最新四仓独立远端读回](integration-evidence-20260928/fusion-current-remote-heads-20261001.json)再次确认feature均包含当前fast；Web`8b8c951`亦包含最新develop，API feature相对当前develop仍缺10个提交，后续集成须按真实差异收敛。Client新v3精确来源/EDIT源码包已派发，注册必须disabled、operations=[]，业务澄清/每意图费用合同及统一Hall follow-up仍须完成；不将runtime合同误当owner HTTP合同或真实能力就绪。

完整范围仍为可选参考图、点将进入同一悬赏议事、生成或澄清、多轮修改、多媒体实时展示/预览下载、主动保存、正式交付/验收/任务完成；未选择真实账户、未付费调用、未发布或通知可验收。


### API桥源码已验证并推送（2026-10-01）

最小Chat runtime修复child`f89d4de3`/tree`b54dee07`只新增bounded source set的OAuth API运行依赖；production/17fixture/AP/heap/selectors不变。v7真实exit0、`BUILD SUCCESSFUL`：Chat25项本轮实际执行全部通过；Agent57项（含真实MySQL3）为输入未变的v5实际XML复用，明确不是v7重跑。Main已核对17XML、实际stdout摘要、终态回执及Unix/TCP自有测试库prefix0。

已新建Main独占`api-fusion-main-20261001`checkout，精确FF/push/readback到feature`f89d4de3`；SDD API研发pin/gitlink随此次提交同步。原v5语法、v6runtime失败不删除/不改PASS；[本轮便携证据及推送回执](integration-evidence-20260928/controlled-bridge-v7-source-accepted/manifest.json)保存新冻结输入、原stdout、17XML与源tree/远端证明。

这是API bridge源码切片通过，不是API/Web/Client29共同样例或完整34项产品验收，更不是Provider/浏览器/版本发布。完整多轮澄清、精确上一稿EDIT、每新意图authority、统一Hall follow-up与API最新develop差异收敛仍是后续工作；v3 Client源码包继续默认关闭实施，真实账户未选择、未付费调用、未部署。
