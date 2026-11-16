# Web/API 构建迁移到203.32.84.239

2026-11-16，Owner `build_migration_owner` / developer，任务 `REMOTE-BUILD-MIGRATION-20261116`。

## 范围与授权

用户授权“开始迁移构建任务并进行一次构建和发布”。迁移Web/API测试、构建、打包到已安装工具的服务器，生产机仍用原LOCAL受控安装事务。无功能代码变更，以当前已部署源码重建验证新链路。Runtime存在其他活动任务和未提交变更，本次不发布；不变更生产数据/模型/身份、不开付费Flow。

- 根控制器开发基线：`2b2abf4ec02ae050ad9f1fdc8dc9f05ab049a87f`，工具候选最终commit在执行证据中固定。
- API：`d6f03755ac524b7604495ed162943a5b30ec580f` / tree `2a24067cf6d9161ee1b9a347132928392d54b3e8`，版本 `1.1.56-SNAPSHOT`，工作区干净，等于当前生产源码。2026-11-16约09:48只读远端查询develop为 `377132f786c6a38b1cb9d2cb90bda7dc3a96ff0b`；不把本地候选宣称为远端最新，不自动取旧远端发布。
- Web：`2ee2349a1f727c1c712dd54b36e268075977300e` / tree `6d0474c094b073ecf699d11420e5b425b83b0733`，版本 `1.16.150`，干净，等于生产及当时远端develop。
- 生产API发布前JAR SHA-256：`f6c8fa110f2bc23acf1b8d39d4d6e59de8455a28a92f0d3f2ab7627268f8e840`；生产Web原buildId `runtime-lease-web-k2-toolbar-01-20261115`。执行前重新核对，不以此段替代前代摘要并发保护。

## 责任与最小联动

本次责任在既有编排/传输边界：local_release委托原Web/API builder，SSH传输不复制API业务权限/状态机。无接口、持久化或执行合同变化，不要求Web/API/Runtime业务代码联动。统一接口规范路径 `/home/isp/wsps/cyf/api/docs/interface-standard.md`，固定版本为上述API commit；RB-1职责与根AGENTS显式随controller快照携带。

## 实施与验证

- 现有 `local_release.py` 添加显式SSH worker参数，远端systemd控制构建deadline，原生产安装保持独立；`remote_build.py`仅传输/源固定，不另造发布runner。
- 固定host key、浅Git快照排除脏字节、禁止覆盖接收目录、安全归档解包及deadline职责的隔离工具测试通过；原构建、安全/分层/fresh JAR与时限测试保留。完整日志在 `/home/isp/state/cyf-remote-build-migration-20261116/transport-tests.log`。
- 初次工具/缓存准备、真实构建批次、测试XML、制品SHA、安装及验收分别保留于同任务证据和构建批次目录。准备成功不代表应用构建通过。
- 未执行全局119项、真实Provider收费调用或故障注入；发布后验收限定原安装器全资源核对、API健康/签名/认证边界，以及明确记录的只读冒烟。

## 执行批次与故障归因

- controller 固定 `19c59363bc5ca211a02ebc18acada1a109db164d` / tree `eef01b0ddc03e2d886b6be4fbe53d6bb404b686d`；45项工具定向测试通过，日志 `/home/isp/state/cyf-remote-build-migration-20261116/final-transport-tests.log`。
- worker已安装 Node24.22.1/npm11.19.1、Dragonwell21.0.11、Gradle9.3.1，均在`/home/isp/apps`；Gradle迁移6688项缓存逐hash核验，通过原API plan-only与orchestrator preflight。缓存迁移不是应用验证。
- 首批 `remote-20261116-01`：源码准备197.675秒，单独记录；Web构建阶段414.446秒后Owner受控停止，`FAIL` / exit143，API未开始，生产未安装。Canvas GNU原生tarball从npm官方源持续低速下载，六分多钟仍未完成；预计余下必要构建/打包超600秒，未续时。不是单元测试失败，也不重标为成功。
- 首批证据 `/home/isp/state/cyf-remote-build-migration-20261116/release-01/release.json`，网络/停止现场和npm原日志在同根 `failure-01/`。修复选择迁入本机已有、逐blob匹配锁文件SRI的npm内容缓存，不改锁文件/依赖版本/测试要求。准备脚本曾因控制机默认Python3.6及残留准备目录失败，原日志另存；控制器正式执行必须用现有 `/root/.local/bin/python3.11`。

- npm缓存迁入554个锁定SRI内容blob，远端553项已有、1项新增（Canvas GNU）；完整锁文件不在本机cache的82项为其它平台等未缓存包，不伪称全部依赖已迁入。新批Web依赖11.568秒、53通过/2pending、构建12.464秒，worker全程41.431秒。
- 第二批 `remote-20261116-02`：Web（含回传）207.789秒通过；API 8.028秒失败，Gradle在测试前报告Groovy DSL不可变workspace缺失 `cp_init`/report输出。根因是迁移快照只归档文件而漏掉有语义的空目录，不是代码/测试失败；总构建215.817秒，生产未安装。已按原缓存目录清单补齐1224个目录并核验9752目录、6688原文件，未清空缓存。证据同根 `release-02/`、`gradle-cache-directories*.{json,log}`。
- 同期观察到回传约5Mbps，API原JAR约241MiB，不能仅靠热缓存承诺600秒。传输适配为SSH固定密钥的rsync块差量：旧程序/包仅作字节basis，接收完整归档SHA/大小必须匹配worker原归档后才解包；不复用测试结果、不改变原包。传输受本阶段剩余预算约束，不给生产进程下传deadline。9项transport及32项local工具测试通过，日志同根 `delta-{transport,local}-tests.log`。

## 已完成发布（2026-11-16，约10:49 CST）

- 成功批次 `remote-20261116-03`，controller `c8e91ee5`（完整身份见SSH transport.json）。与前两批独立执行、独立计时，不重标原FAIL。
- 真实构建与回传 **316.679秒**：Web208.608秒，API108.071秒；worker API99.121秒、Gradle95.018秒，**202任务/75 FROM-CACHE**。源码准备200.768秒单独记录；原API安装101.234秒、Web安装16.661秒、健康/签名/匿名拒绝检查单独记录。控制器总墙钟646.569秒不是构建计时，也未把生产JVM放入deadline单元。
- **Web1.16.150**：55项定向基线中53 PASS、2 pending、0失败；**API1.1.56-SNAPSHOT**：7份本批XML、96测试、0失败/错误/跳过，保留validateLayering及fresh bootJar。不是沿用历史95测试数量。
- API包SHA-256 `63103f191d83cbc2a99ffe358350b9ea6f4f20cd3997b885250dfbcf2a047a14`；生产JAR `7c552971f7ecd69cb17a5fcdae2db414fe166bd86854422f0be712dc2adb8745`。Web包 `71c2f52413a3af22a4de307bcb762c0c5c8f9792d747f3e438306941741f2205`。完整commit/tree沿本文件固定候选；无业务源码变化。
- API安装record `installed` / LOCAL，PID1092219、HEALTH=UP、ARTIFACT_ATTESTATION=MATCH；Web `online_verified` / LOCAL，原安装器核对全资源线上摘要。原API前代JAR备份摘要匹配构建前记录，Web前代备份由原事务记录；没有绕锁/改恢复入口。
- `/actuator/health`200且UP、`/oauth2/jwks`200且有keys、聚义厅真实scene snapshot匿名请求401。这里只证明健康/签名/认证边界及资源上线，不是已认证业务闭环或全局119项/UI回归通过；无收费Provider/资金写操作。
- rsync API归档252,641,280字节中251,872,768字节由basis匹配，仅768,512字节literal；接收完整归档摘要仍匹配worker。Web匹配17,449,344字节，literal93,582,976字节；如实记录网络仍占主要耗时，不承诺任意版本都能高命中。
- 现有10个NewAPI/StarAI容器的ID、启动时间、重启次数、健康状态对比工具安装前均不变。Runtime未发布、其活动工作区与状态未改；其它任务脏修改保留。
- 构建包路径 `/home/isp/state/cyf-local-build/tasks/cyf-remote-20261116-03/{api/package/api.tar,web/package/web.tgz}`，已按既有保留策略登记。原缓存保留；worker未安装生产主机清理定时任务，不能在没有跨机当前/回退绑定保护时盲目照搬清理。

## 证据与后续使用

- 完整成功回执、阶段日志、XML、测试摘要、工具及制品摘要：`/home/isp/state/cyf-remote-build-migration-20261116/release-03/`；控制器日志同根 `release-controller-03.log`。失败原证据分别为 `release-01/` 和 `release-02/`。
- 工具测试9 transport +32 local +7 storage，48项通过；同根`delta-{transport,local,storage}-tests.log`。不将工具测试当作应用业务回归。
- 根AGENTS收口Web/API后续默认worker位置；CLI仍须显式传入固定SSH主机、全新remote-root、公开runtime-config等参数，不是将默认无参数入口偷偷重定向，也不允许自动回落生产机重构建。
- 后续有新业务候选时固定新的完整commit/tree，按变更加入必要回归。Runtime及远端自动清理适配不在本轮完成范围。根提交仅本任务文件、未push（保留无关未发布历史），工具源码、安装与业务验收边界分别记录。

收尾补记：最终独立摘要/源码/测试/备份/容器审计为 `/home/isp/state/cyf-remote-build-migration-20261116/completion-audit.json`（PASS）。仅本任务的三批远端临时源码/裸快照、本机重复source/output传输归档及缓存seed归档已清理，原批次输出、包、原始日志/XML、完整传输摘要、缓存和备份保留；worker生成的ledger/evidence变更另存后再删源码暂存。清理回执同根 `temporary-cleanup.json/.log`，未清他人工作区。

文档检查：Git空白检查通过；本次引用的既有工具说明与handoff路径存在。`./sddw check-docs --all-docs` 返回2，原因是开源导出既有缺失 `docs/sdd-document-map.json`，日志同根 `docs-check.log`；不宣称全库文档检查通过，也不为本次构建迁移生成替代全库索引。

## Runtime补齐（2026-11-16，执行中）

用户“继续完成”授权扩展原任务到Runtime；原Web/API成功记录不变。只读核实另一任务已在2026-11-15发布Runtime1.3.114/bridge1.1.76，源码4fd0951fec5d5a89c05985b96465169ff7e39e39/tree c6e7f6e0b5713e738fa5153115d13ec1a4a84566，当前PID873209、record verified-active。此前“Runtime未发布”仅指本迁移批次，不能当作全机最新状态。认证迁移和原业务验收按原handoff独立保留，不重复迁移/收费。

沿唯一Owner build_migration_owner，使用原orchestrator将同任务从done重新转claimed（claim命令不接受done，安全拒绝后走transition，未手改ledger）。将原Runtime114完整34组selector构建脚本提升为参数化`ops/orchestration/runtime_build.py`，复用`remote_build.py`固定源及SSH回传，不新造生产安装事务。目标是同源完整测试、远端代码包与已安装内容精确匹配时受原发布锁作幂等确认，不重启、不覆盖身份/状态或重放迁移；如不匹配须停下归因，不能宣称已经发布。

首批`runtime-remote-20261116-01`在测试前0.415秒FAIL：worker首次没有`/home/isp/state/cyf-build`父目录，旧脚本只mkdir末级。原日志和result保留于`/home/isp/state/cyf-remote-build-migration-20261116/runtime-01/`；失败证据收集因没有生成输出另安全拒绝，未打包/未安装。修正为普通盘父目录递归创建，并让传输临时包按输出批次命名，避免不同批次相互冲突；独立第二批重新计600秒，不改写原FAIL。

第二批`runtime-remote-20261116-02`完整测试135.501秒FAIL：783项766PASS/7FAIL/10SKIP，无包。7项分别来自构建机缺/usr/bin/bwrap（5项）及Ubuntu26 uutils多调用二进制按新文件名复制后退出（cat进程身份及sleep存活清理2项）；均为真实失败，不忽略或补绿。安装系统依赖bubblewrap0.11.1；GNU coreutils9.7已随主机存在，下一次Runtime任务仅用systemd BindReadOnlyPaths将gnucat/gnusleep映射到私有mount namespace内原路径，主机默认命令及其它服务不变。源代码/测试selector不变，先跑原失败用例诊断，独立新完整构建仍600秒。工具12项测试通过，日志同证据根runtime-transport-tests-03.log。

原失败用例诊断逐步暴露完整原生工具闭包：先补同版本Codex0.167.0原生二进制（SHA cdcb45aaa01d0f14e298985e09465aebccd47f64ecd298aea44814af7b62bbda），再补slirp4netns及同发行版codex-resources/codex-path（40文件逐hash验证），均在worker专用apps目录，不复制任何HOME/auth或使用Provider。各次原诊断日志保留，不是新完整构建或PASS。

Ubuntu26内核审计明确拒绝隔离视图`/runtime/codex-resources/bwrap`的嵌套userns。仅为该确切沙箱helper安装AppArmor attachment，位于`/home/isp/conf/cyf-build/runtime-bwrap.apparmor`，系统入口为`/etc/apparmor.d/cyf-runtime-build-bwrap`链接；授予userns以运行真实嵌套bwrap，不关闭sandbox/实际只读或网络探针，两个全局AppArmor限制sysctl均未更改。没有为其它程序/全局userns解除限制。原生测试必须真实通过后才启动完整第三批。

原失败用例最终诊断05为8PASS/0FAIL/0SKIP（包含另一spawn负例，独立诊断不冒充完整套件）。第三完整尝试`runtime-remote-20261116-03`在测试前0.515秒因源码断言安全FAIL：另一Owner已将Runtime HEAD提交为4d763777/1.3.115，传输层原只克隆当时HEAD，builder正确拒绝与本次固定4fd0951候选不一致。未跟随发布、未复位/覆盖他人工作区。传输新增可选完整commit固定快照，以浅fetch准确对象构造snapshot，不改变本地HEAD或脏字节；新增回归13项通过（含并发Owner新HEAD保持不变/仍输出原候选）。下一完整批固定原线上4fd0951及精确lock，不顺带发布1.3.115或另一任务新API。

第四批`runtime-remote-20261116-04`**BUILT_NOT_PUBLISHED**：固定4fd0951，完整783项773PASS/0FAIL/10原skip，worker138.124秒、含回传144.823秒；包SHA96b6f8b1487e5fb6ffa4119625ba9bb2e9f471833ac6cff327bd9f728c8625e1。实际portable manifest为152项、与原114包逐项完全相同。生产幂等确认在原发布锁处1.022秒安全拒绝：另一Owner正受控部署115（MATERIAL任务，PID1110067持锁），本任务没有抢锁/停进程/覆盖新版本。原BUILT及publication FAIL分别保留；经原conflict-alert告警，不向另一聊天发消息或改变归属。为与该任务即将发布的实际候选一致，接续仅远程构建同固定115/bridge77源码4d763777/treef51cce51，并在原完整34文件上额外加入image-input及typed-inspection-input-carriers；不减少测试、不替另一Owner进行部署/数据恢复。115的生产发布/业务验收仍由原任务负责；本任务后续只在其完成且源/清单一致时作幂等核验，绝不降回114。

第五批`runtime-remote-20261116-05`**BUILT_NOT_PUBLISHED**：精确115/bridge77（4d763777 / f51cce51），36文件807项：**797PASS/0FAIL/10原SKIP**；worker138.258秒、含回传143.939秒，准备46.071秒另计。包SHA `cda994cb32e5e92aa07e065c3b141897e7dc03c9a795cbbc93a290f49c1b07b6`，controller固定94d3cf0d（完整SHA/tree见transport.json）。新增两个载体selector不替换原34文件；完整工具/锁/binary/resources摘要、TAP、manifest及原包在 `/home/isp/state/cyf-build/rt-r05/`，包外证据另存本任务`runtime-05/package-evidence/`。未伪称由本任务安装：原MATERIAL Owner正将同源115受控安装，2026-11-16 11:42只读回执为INSTALLED_CHANNEL_PENDING/PID1116103，804.118秒是其独立安装阶段，不计入本次远程构建143.939秒。

本任务此时只等待原Owner完成实时通道核验，随后作原锁/CAS下同源幂等确认，不回放认证迁移、不改变当前安装来源或业务事实、不重启服务。远程原10容器身份/启动时间/重启计数/健康不变，主机cat仍uutils、AppArmor全局限制均1；证据`runtime-worker-supplement-verification.json`。worker架构/工具说明已先备份后追加Runtime实际闭包与构建结果，备份在worker`/home/isp/baks/cyf-build-migration/20261116-runtime/`，修改摘要回执`runtime-remote-documentation-update.json`。文档不是生产健康通过证据。

工具定向验证13 transport +32 local +7 storage +2 CLI计划/路径用例，54项通过；实际应用测试单独见807项结果。`./sddw check-docs --all-docs`仍因导出缺`docs/sdd-document-map.json`返回2，未伪称全库检查通过。包114完成登记；包115先登记后在后续核验复用前用原mark-active撤回，完成后须重新登记。原失败和锁冲突均保留。

## Runtime迁移与发布核验完成（2026-11-16 11:50 CST）

- 原MATERIAL Owner已将Runtime1.3.115/bridge1.1.77、4d763777/f51cce51受控安装并标verified-active；其原制品SHA `973b8edc3c33b1574178ab4e29c0ae6906629995a8622c9307a7b9b5ed37529a`及安装来源保持原样，不伪改成远程包。
- 本任务最终在原发布锁内做 **IDEMPOTENT_NO_REINSTALL / PASS**：远程第五批807项797PASS/0FAIL/10SKIP、143.939秒的代码包与原115候选及实际安装程序**全部152项文件/目录、字节与模式匹配**，安装baseline（含原派生缓存证明）、目标依赖及原validate.sh通过。当前PID1116103、5/5主体connected/registered/ready，健康文件新鲜；前后PID及程序清单不变。未重复安装/重启/认证迁移、未改当前安装record或恢复state。
- 当前新增发布验证回执 `/home/isp/apps/cyf-agent-runtime-v1/release-records/remote-build-20261116.json`；完整结果 `/home/isp/state/cyf-remote-build-migration-20261116/runtime-05/publication/publication-result.json`。独立发布核验148.151秒；等待另一Owner安装/通道核验及本次验证共720.920秒，**不计入已完成的远程构建143.939秒，不续600秒构建期限、不给生产进程下传deadline**。原114包构建成功及原锁冲突仍各保留，前三批真实失败不重标。
- 真实115安装、备份与业务验收由原任务留证；本任务仅声明远程完整必要selector、代码/依赖、发布幂等及5通道健康，不声明FULL119全过、原用户事项689恢复或新增付费Provider调用。API/Web及其后续业务发布归各原任务，本次不重建/重发它们。
- Runtime默认worker位置、参数化原builder、固定revision浅快照、追加回归及Ubuntu原生闭包/私有GNU挂载已收口根AGENTS与既有编排README；代码/工具定向54项通过，与应用807项结果分开。根提交仅本任务文件、本地develop，不自动push混合历史。
- 两个成功Runtime包均按原保留入口mark-complete登记，115在核验复用前mark-active、核验后重新登记，未清共享缓存。仅本任务五批远端源码/重复build及scratch、本机重复Git/传输/engine seed归档已清理；worker原controller ledger在清理前另存，原包、TAP、metadata、完整测试/失败/锁冲突证据、安装状态、缓存和备份全部保留。清理回执 `/home/isp/state/cyf-remote-build-migration-20261116/runtime-cleanup/receipt.json`，13项worker临时目录及26个本机重复副本，不包含生产app/状态。
- 文档全库检查仍因已知导出缺map返回2，空白与本次直接链接检查单独通过；不把这个既有文档阻塞称为应用发布失败或全库文档PASS。
