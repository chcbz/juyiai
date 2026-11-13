> **2026-11-06 现行规则：** 用户告知云效额度用完，CYF 默认改为本地测试、构建、打包和受控部署；不自动启动 Flow。正式证据绑定真实本地构建批次、完整 commit/tree、必要测试与制品 SHA-256，不伪造 Run/CI 身份。保留发布授权、身份/ACL、锁、备份、可恢复安装与线上验收；develop 不自动部署。Gradle 仍先读构建文件并经现有编排器串行执行。下文冲突的 Flow-only/禁止本地构建说明仅作历史，完整规则见根 `AGENTS.md`“本地构建与部署（2026-11-06 用户最新决定）”。2026-11-07已完成Web/API原安装器LOCAL适配与同批实测；默认快速路径见本文末节，长期策略见 docs/aliyun-flow-cicd-strategy.md 的2026-11-07节。

## 本地构建存储（2026-11-08）

- Web/API本地入口 `local_web_build.py`、`local_build.py` 与组合入口 `local_release.py` 共用 `build_storage.py`：启动前按实际文件系统拒绝 tmpfs/ramfs 上的源码/输出及对应缓存、组合入口证据目录；包含符号链接、挂载别名及尚未创建的目录，不只匹配 `/dev/shm` 字符串。Web额外检查 npm 当前有效缓存目录。
- 调用方仍传入磁盘上的批次路径（惯用 `/home/isp/state/cyf-local-build/tasks/<batch>/`），不能为省磁盘改用内存盘。不存在的目录检查最近已存在祖先；不能读取文件系统类型时停止，不静默放行。
- 构建子进程的 TMPDIR/TMP/TEMP 与 JAVA_TOOL_OPTIONS 中 java.io.tmpdir 固定到批次输出下 `tmp/`，保留其他 Java 参数；不修改全局环境、生产服务或安装环境。临时文件沿既有任务收尾清理，不自动删除历史目录或他人文件。
- 风险依据：本次已发生旧内存盘构建产物与编译/生产进程争用物理内存并触发 OOM。此规则只阻止文件落入内存盘，不承诺阻止所有进程内存耗尽，不新增任意内存阈值。Runtime外部打包入口不在本次代码改动范围。
- 定向验证：Python3.11 执行 `ops/orchestration/tests/test_build_storage.py` 及 `test_local*.py`；不启动应用构建或生产安装。

## Web共享安装依赖（2026-11-09）

- 现有 `local_web_build.py` 默认经 `web_dependencies.py` 复用 `/home/isp/state/cyf-local-build/web-dependencies/<key>/node_modules`，可用 `--dependency-store` 指定普通磁盘实体路径。共享的是**同输入的完整安装集合**，不是把所有版本强塞进同一个目录，也不直接借用主工作区的旧node_modules。
- key包括package.json及package-lock.json摘要、Node版本/ABI/平台/架构/二进制摘要、npm版本、有效npm配置摘要及固定ci参数（包含dev/optional/peer，运行依赖自身安装脚本）。仅存配置摘要，不把认证配置明文写入共享receipt；下载仍复用npm自身的完整性缓存。不同版本号若改变manifest/lock也产生新集合。
- 首次按key互斥，在私有暂存目录执行npm ci和npm ls；安装/校验失败不发布。成功后依赖目录置为权限只读并原子发布；复用前和构建后核对全部文件/模式/内部链接摘要。只读是防误写约束，不是对同属主/root的安全沙箱；损坏集合报错留证，不覆盖修补或静默复用。key锁等待、首次安装和复用核验计入当次构建发布耗时；异常重试按根AGENTS最新规则重新计时。
- 只给未存在node_modules的源码目录建立链接；已有同集合链接可复用，已有真实目录或其他链接直接报告、不改动。**不要对该共享链接运行npm install/ci/update。** 老工作区不自动迁移，不改生产目录。现阶段不接入自动回收；不能把共享依赖集合当作普通任务临时目录删除。
- Vite仍读取原源码配置，但使用runner配置加载器以避免默认bundle加载器写共享node_modules/.vite-temp；Vite cacheDir在批次输出旁。TMPDIR仍沿用批次磁盘tmp。共享方案仅适用于当前Web的registry+integrity锁定依赖；根安装生命周期脚本、workspace、本地链接依赖不猜测共享，需按真实使用另行适配。
- 定向入口：`python3 -B -m unittest discover -s ops/orchestration/tests -p test_web_dependencies.py -v`。含完整性/失败/并发/目录保护、真实小型loopback包npm ci/ls及跨源码目录复用；可用本机现存Vite时另做极小真实bundle的配置/输出隔离冒烟，不等于CYF全量构建。2026-11-09已完成真实Web锁完整安装、第二次reuse及生产构建；Web038a571显式取得ESM配置目录以兼容runner（alias/LESS语义不变），见 `docs/implementation/handoffs/WEB-DEPENDENCY-SETS-20261109.md`。

## 本地包收口与耗时（2026-11-06）

- 2026-11-09用户最新决定：10分钟仅限定单次构建发布，异常重试重新计算。每次执行独立600秒，随构建执行的单元测试、构建、打包和发布在本次内计时，不按内部阶段重置，不跨源码候选／开发过程／重试累计。回归验证与业务验收单独记录、不受此限；不把单元测试改名豁免。重试前归因、保留原失败和耗时；同根因同输入连续失败两次不盲重试。单次超限仍按根AGENTS申请例外，历史累计不构成扩时理由。保留身份、锁、完整性及恢复保护，不下传应用或生产服务deadline。下方旧工具实现说明是历史事实，不代表已按本条适配。
- 完成/终止时只将已明确可回收的最终包登记到既有 completed-tasks 清理入口，见 `ops/maintenance/LOCAL_ARTIFACT_RETENTION.md`；不是旧准入、生产发布授权或全目录清理。主机适配状态须看该说明及任务handoff。

> 2026-10-29 用户更新：Flow 只在 worker 上测试/构建/打包/上传后结束，不调用或等待生产主机；主机主动拉取固定 Run 制品后独立受控安装/核验。目标是卸载本机内存并减少计费，不重复构建已核验的精确制品；锁/身份/备份/完整性保留。此条覆盖下方旧 Flow 部署口径，详见根 AGENTS 同日规则及 docs/aliyun-flow-cicd-strategy.md。

# 当前交付入口（2026-10-22）

Flow用于卸载本机高内存任务：前端 `4403172`、后端 `5260799` 执行重型测试、构建、打包及授权部署。文档/静态检查、低开销定向验证、状态查询、发布协调和上线核验可本机执行；按实际负载判断，不按Node.js/Gradle工具名一刀切，不设无依据内存门槛。本机不生产打包/源码直发。develop不自动部署；版本绑定固定源码、真实Run与同Run制品。

Run本轮执行完成即结束，不轮询配对ready文件、不等其他Flow/人工确认或上线检查。条件在本机协调；部署安全保护仍保留，结束后由本机核验健康/业务。规则见根AGENTS与部署策略。2026-10-22默认CI模板及两端云端配置已切换，并各实跑一次（Web294/API234）；本任务未部署或改安装器，详情见docs/implementation/handoffs/FLOW-RESOURCE-SPLIT-20261022.md。下方旧实现说明不能作为继续挂等待的依据。

**2026-10-24 执行时限补充：CYF 每次 Flow Run 总耗时不得超过 10 分钟（600 秒）**，覆盖 Web/API/临时运维与 Runtime；计时覆盖准备到终态的全部作业，不能按作业重置。达限须受控结束并保留真实超时/恢复证据，不删必要回归、不绕部署保护、不搬回本机重型任务。规则优先级与安全边界见根 `AGENTS.md`“Flow 执行时限”及 `docs/aliyun-flow-gate-policy.md`；本次规则更新不代表已修改云端超时或在途 Run。

## 历史后端默认 Flow CI（2026-10-20；非当前默认入口）

`5260799` 默认配置的源码为 `ops/ci/aliyun-flow/backend-ci-run.sh` 和 `backend-ci-policy.json`；离线渲染使用 `prepare-backend-ci.py --output /absolute/candidate.yaml`，仍通过既有 flow-control 固化，不在本机运行Gradle。细节见 `docs/aliyun-flow-cicd-strategy.md` 的默认提速维护节。

云端仍用本编排器的 `gradle --flow-ci`：精确Flow身份/策略argv/当前干净commit/tree、新输出和原Gradle锁；不读写人类任务ledger、不复用整轮结果、不授权部署。普通任务不要使用此模式，原task guard保持不变。

2026-10-20续调查（诊断源码63ed6b21）只增加可核验数值计时：同Run制品的既有`test-results/summary.json`含`gradlePhases`与`taskTimings`；用`rootBuild`区分主/嵌套build，各自offset不混算，JVM uptime另列。Flow日志可能省略开头，优先查同Run summary/XML。Gradle JVM C1和重任务优先实验均无明确净收益，已撤回，原policy/顺序及Test-only C1不变；没有新增缩时保证，不部署。

# 开工诊断（DEV-FEEDBACK-PILOT-20261008）

在现有 `cyf_orchestrator.py` 增加 `preflight`，不另建台账或准入门禁：

```bash
python3 -B ops/orchestration/cyf_orchestrator.py preflight TASK_ID \
  --cwd /absolute/path/to/task-worktree --component api \
  --baseline origin/develop --selector ':module:test --tests ExampleTest' \
  --fixture path/to/synthetic-fixture.json
```

- TASK_ID 必须存在；cwd 必须是仓库/worktree 根。baseline 显式指定，只读取本地引用，不 fetch，也不宣称远端最新。跨仓任务逐仓核对，台账 SHA 不匹配时先确认它绑定的是哪个组件，不自动改台账。
- JSON 输出 HEAD/tree、分支、是否脏、任务 SHA 是否匹配、基线双方独有提交数、工具是否在 PATH、根构建文件和指定 fixture 是否存在。
- 不执行 java/node/gradle/npm、候选 selector 或 shell；不读取 fixture/凭据内容，不下载依赖、不连接数据库、不修改任务或发通知。文件存在不等于内容/schema/依赖就绪。
- 当前 ledger 不含 owned_paths/worktree 映射，路径冲突明确 UNKNOWN；仅列其他 Writer 作为人工协调线索，不能声称无冲突。锁可用性、数据库和工具版本也未验收。
- Findings 仅建议，正常观察退出0；未知任务、非仓库或无法读取退出2。这不是测试成功、正式构建或发布批准。
- 前后端重型正式验证走Flow4403172/5260799，轻量验证可在本机；后端先读build.gradle，再经原gradle串行入口，保留validateLayering。preflight不绕过锁、授权或失败处理，不把生产构建带回本机。

隔离测试（只创建并清理自己的临时 Git 仓库）：

```bash
python3 -B -m unittest discover -s ops/orchestration/tests -p 'test_preflight.py' -v
```

共享契约试点见 `specs/juyiting-execution-recovery/contract-pilot/README.md`。它复用实际前端消费者，但完整 Java HTTP/数据库层必须单独验证，不能以替身响应 PASS 替代。

## 执行历史：单命令定向验证

`execution_history_check.py --task-id TASK_ID --api /absolute/clean-api --web /absolute/pinned-web`

- 加 `--check-only` 仅预检；不自动创建/接管任务或改基线。cache miss运行要求该任务已在现有验证阶段。
- 先语法/合同检查和廉价消费者回归，再经原编排入口运行真实HTTP/MySQL测试及分层检查。无自动重试、安装、发布或前端本机生产打包。
- 命中精确输入并核验完整证据时返回 `REUSED`，不启动Gradle/MySQL；缺失或损坏的证据不能复用。根目录普通文档变化不触发重建。
- 一次性环境准备、凭据来源、完整命令、证据边界仍以 `specs/juyiting-execution-recovery/contract-pilot/README.md` 为唯一详细说明。
- 工具本身的隔离测试：`python3 -B -m unittest discover -s ops/orchestration/tests -p 'test_execution_history_check.py' -v`。这些工具测试不是实际跨端验收证据。

- 执行历史可追加 `--browser`：在同一Java/MySQL存活窗口驱动生产组件Chromium页面；非整站、非正式前端Flow。源码/辅助桩/浏览器指纹/截图证据边界见同一contract-pilot README。

## 历史后端本地构建：受控持久依赖缓存（2026-10-09）

> 2026-10-17起此节仅记录历史实现，不是当前发布入口。保留工具与证据供追溯，不授权本地生产构建或部署，不把本地 metadata init 直接移入 Flow。

**2026-10-09当时的正式本地发布默认启用**：既有 `gradle` 入口识别 `CYF_LOCAL_RELEASE_OPT_IN=1` + `CYF_LOCAL_GRADLE_ACTIVE=1`，核验显式metadata init的内容与固定compile-only策略一致后，无home参数默认 `/var/cache/cyf-gradle-local`（委托身份使用UID后缀），无cache flag默认加入 `--build-cache`。无需每次手传缓存参数；源码与build输出仍逐批隔离。Flow和普通专项诊断不受影响，显式 `--no-build-cache`、显式 `--dependency-cache-home` 保留诊断/隔离用途。与默认home冲突的旧 `GRADLE_USER_HOME` 需在调用端移除或明确绑定匹配home，不静默降级。

- 参数设置子进程 `GRADLE_USER_HOME` 并输出路径readback；目录必须canonical、无符号链接、由实际Gradle身份持有且0700。首次仅创建该目录，不自动创建父路径、不复制历史配置/daemon、不清缓存或他人目录。
- home不得有隐式 `gradle.properties`、`init.gradle(.kts)` 或非空 `init.d`；仓库/消费凭据仍由固定显式init配置管理，不将凭据写入home。冲突的环境/CLI user-home拒绝，不能悄悄落到另一个目录。
- 第一组对照仅复用依赖/解析/脚本缓存，`--no-build-cache`下仍重新执行207任务。正式本地候选默认 `--build-cache`（可保留 `--no-daemon`），配合本仓固定 `local-release-metadata.init.gradle` 的compile-only策略：只允许JavaCompile按Gradle输入指纹复用（包括测试类编译），所有非JavaCompile禁用输出缓存，Test额外禁止up-to-date；不复用测试报告或旧JAR。原定向测试、`validateLayering`、OpenCV来源/SHA、PublicArtifactVerifier、POI运行类路径和fresh bootJar仍执行。
- 默认策略不改基础证据键、源码核验、串行锁、身份或发布授权；接受旧整轮证据还须策略对象匹配。工具新增 `GRADLE_EXECUTION_TIMING` 实测子进程耗时，计时不含获取互斥锁的等待；没有deadline/资源门禁。
- 完整调用仍须固定任务、commit/tree、selector、fixture和工具链，逐批记录新输出/日志/制品SHA；不要直接套其它任务的示例选择器。构造fixture前可调用 `local_release_cache_defaults(args, requested_argv)`取得实际参数和策略，绑定effective argv及policy。原证据记录保存 `effective_argv`/`release_cache_policy`；producer证据必须写实际argv，不能把未补默认flag的requested argv冒充实际命令。正式发布只消费同批核验的制品。

本轮测量及边界见 `/home/isp/wsps/cyf/docs/implementation/handoffs/BACKEND-RELEASE-10M-20261009.md`；不是生产安装入口，不因此重启服务。

- 本地producer/admission的argv白名单允许 `--build-cache`，但不放宽所需测试/分层/bootJar任务的fresh日志要求，`FROM-CACHE`/`UP-TO-DATE`仍拒绝。`invocation.cacheHit=false`指整个验证未被EVIDENCE_HIT跳过，不表示JavaCompile未命中；实际命中以逐任务日志为准。
- 2026-10-09用户授权收尾已同步安装 `/usr/local/libexec/cyf-api-local/admit-api-local.py`；回读SHA `49ff62e470beadf5c5c570b007d1d30a6dd18b1f32df217274d89121ff77728b`，新flag可用且cached required tasks仍拒绝。原值备份 `/home/isp/baks/cyf-backend-cache-closeout-20261009/admit-api-local.py.before`。安装使用既有coordinator→release→lifecycle锁和原子替换，应用PID/start/JAR/health未变，无应用发布或DDL。
- 工具更新不改写历史批次的helper catalog/authority/receipt。下一次发布按当前固定工具重新生成对应批次的helper catalog；若恢复旧的精确批次且其catalog绑定旧工具，按同锁顺序先验证/恢复原helper（before SHA `a5d4f89693e02903001f148c5fdac1613d2756c26d334fd78702df054a16c32b`），不得绕过工具摘要或把旧回执重标新批次。


## SDD文档链路（轻量只读）

文档整理后复用 `./sddw check-docs [feature-id]`，全目录默认覆盖规则、当前索引和特性主文档，检查范围及历史例外见 [SDD说明](../../docs/sdd-workflow.md#sdd-document-check)。该命令不执行应用测试/构建、不修改pin/台账、不比较历史SHA与当前checkout；不能作为发布验收。既有 `sddw verify` 保留模板候选核验语义。工具自身定向回归：`python3 -B -m unittest discover -s ops/orchestration/tests -p test_sdd_docs.py -v`。

## 本地快速构建与受控发布（2026-11-07）

### 固定源码验证沿用构建入口（2026-11-13）

- API候选验证与打包均使用下方现有 `local_build.py`；通过 `--regression-arg` 原样追加业务任务和 `--tests`，不要为每次重试复制 `run.py` 再手拼Gradle参数。该入口保留 `--parallel --max-workers=2 --build-cache`、compile-only缓存政策、当批测试/分层检查/fresh JAR；只设置依赖缓存目录不等于启用编译产物缓存。
- 包含真实Unix socket的测试应选短的普通磁盘批次路径（如`/home/isp/state/cyf-build/<批次>`）；临时目录仍是该批次的`tmp/`。路径过长会导致socket绑定失败，不是构建超时，不能通过删除测试或放宽身份检查处理。
- 单独构建仍在任务专属 `systemd-run --wait --pipe --collect --property=RuntimeMaxSec=600 --property=KillMode=control-group` 内运行；不是生产服务的执行容器。`local_build.py` 不安装，不因构建成功自动发布。
- 定向测试筛选不缩小生产依赖图；维护测试引用starter主输出时确实需要编译应用图，不能靠去掉任务/必要检查凑600秒。内容匹配的JavaCompile结果可复用，测试结果和最终JAR不能借缓存跳过。
- orchestrator输出 `GRADLE_LOCK_WAIT`、含`wait_seconds`的 `GRADLE_LOCK_ACQUIRED`，结束输出`GRADLE_EXECUTION_TIMING`的 `lock_wait_seconds`、`elapsed_seconds`（Gradle执行）、`invocation_seconds`（含前置和等待）。锁等待仍计入原600秒；超时保留原结果，不移动计时起点。任务阶段看现有 `CYF_GRADLE_PHASE` / `CYF_TASK_TIMING`，归因时加`--regression-arg=--info`可区分FROM-CACHE、重编原因和实际测试。
- 按实际主机负载安排重型任务；不停止生产/其他任务，不扩大超时，不承诺共享主机任意竞争或全冷缓存必定600秒。异常必须有实质变化（源码修复、已证实缓存/负载/工具修复）才重试，不以循环重试代替归因。


- API 构建入口 `local_build.py` 委托现有 orchestrator、跨任务锁和 Gradle；Web 构建入口 `local_web_build.py` 按锁与工具链复用完整依赖（首次 npm ci）、定向基线、原源码 Vite 配置与完整 public 打包。两个 builder **不安装**；新输出必须在干净源码和生产目录之外。
- 完整同批入口 `local_release.py --install`：显式固定任务、两端完整 commit、版本、工具链、缓存、全新输出与包外 evidence-dir。串行 Web/API 构建，再由已安装的原 helper 执行 LOCAL 受控事务，核对前代摘要、备份、健康、签名、安全边界和全部线上入口/JS/CSS 摘要。没有伪造 Flow Run，未恢复旧准入。
- **2026-11-08时限实现：** `local_release.py`按Web/API测试、构建、打包单元累计`buildSeconds`计算600秒预算，保留剩余预算RuntimeMaxSec及失败/超时证据。安装、启动、健康、业务验收和前置检查不消耗构建预算，不向Web安装器下传剩余构建时限；安装器既有网络/恢复限制不变。`wallSeconds`仍记录完整交付墙钟，`under600Seconds`明确仅表示构建阶段。5项定向工具回归通过，尚未执行改动后完整双端发布；本任务沿原独立LOCAL安装器复用固定包。
- API 热缓存仅复用已验证工具/依赖及 JavaCompile 产物；测试、validateLayering、fresh bootJar 均当批新执行。构建采用 Dragonwell21、默认分层JIT与 workers2/内部 parallel（2026-11-13：移除构建JVM的C1-only限制，保留短测试JVM的C1；实际收益以新批次实测为准），不改生产 Temurin/JVM 参数，不带 `CYF_API_STARTUP_DIAGNOSTICS`。公共 artifact/POI 与认证/生产邮件类路径检查保留；2026-11-13默认不再编译/运行启动计时、性能指标及Elasticsearch健康隔离三组测试（上次批次共10项），不沿用旧105项作为当前数量。相关功能变更时通过现有 `--regression-arg=:starter:test --regression-arg=--tests --regression-arg=完整测试类名` 加入；默认选择器为 `local-fast-baseline-v3-critical`。去掉逐任务依赖图打印，保留阶段/任务耗时、凭据移除和禁止嵌套Gradle。不是全功能回归。`--plan-only` 可查完整输入/实际命令而不构建。
- Web 保留生产 Vite 配置，public 原样流式打包而非复制两份；gzip1 和归档后释放自有 dist 控制峰值，逐文件验证完整包。基线47通过、2 pending，不能说全量测试通过。两端改业务仍须通过 `--api-regression-arg` / `--web-regression-test` 加入实际受影响回归；已知失败候选不能仅凭快速基线发布。
- **2026-11-13：API 本地部署包取消外层压缩。** `local_build.py` 默认生成 `package/api.tar`（普通 USTAR），仅归档原应用 JAR、版本、来源和校验材料；不再额外 gzip。安装器按内容识别，兼容历史 gzip 包；原签名/摘要、ACL、锁、备份及恢复不变。内部 incoming/package.tgz 为历史固定暂存文件名，不代表新包仍经 gzip。本条不改变 Web 的压缩方式。
- API 打包只执行一次完整 ZIP/XML/邮件类路径验证；发布前仍检查源码/证据未变，并对日志、输入、报告、JAR、来源记录和固定依赖重新计算 SHA-256。摘要采用分块读取，保留同一文件描述符及路径身份/修改检测。公共制品扫描的临时嵌套 JAR 随扫随删，不做逐文件强制落盘；正式包及目录 fsync、原子发布和安装保护不变。此优化不取消 Gradle 配置或分层检查。
- API 正式 LOCAL producer/receipt 与 Web LOCAL v2 manifest 绑定来源、工具、测试报告和逐文件摘要；原 API/Web helper 已适配 LOCAL，保留旧 Flow 来源兼容、锁、原件备份与恢复。安装路径仍是固定实体目录。原始失败、取消和历史诊断均保留，不重标成功。
- 实测与可复用命令见 `docs/implementation/handoffs/LOCAL-BUILD-TIMING-20261106.md`；包外证据在 `docs/implementation/evidence/local-release-fast-20261106/`。热缓存实测不是冷构建或未来每次的时间保证。`/dev/shm` 输出是临时内存盘，不是持久归档；当前/回退绑定制品不能为腾空间直接删除。

完整入口参数（用真实任务/新批次替换占位符，`--install` 有实际生产副作用）：

```bash
/root/.local/bin/python3.11 -u /home/isp/wsps/cyf/ops/orchestration/local_release.py \
  --task-id TASK --batch-id NEW_BATCH \
  --api-source /ABS/CLEAN/API --web-source /ABS/CLEAN/WEB \
  --expected-api-commit FULL_API_COMMIT --expected-web-commit FULL_WEB_COMMIT \
  --api-version VERSION \
  --jdk /home/isp/apps/dragonwell-21.0.11.0.11+10-GA \
  --cache-home /home/isp/state/cyf-local-build/gradle-home \
  --output /home/isp/state/cyf-local-build/tasks/cyf-NEW_BATCH --evidence-dir /ABS/NEW/EVIDENCE --install
```

### 持久化与完成后保留（2026-11-07落地）

- 上述JDK和缓存已从临时路径迁入持久目录并核验；当前API/回退/Web包另有持久、摘要一致的镜像，历史安装record未改写。不要清理仍绑定的内存盘原件。干净源码须重新准备，历史计时worktree已删除。
- 完整批次结束并保存包外证据后，由Owner显式登记，不能仅凭构建成功推断任务结束；统一输出的组件子目录已受控支持：

```bash
/usr/bin/python3 -I -B /usr/local/libexec/cyf/rebuildable_cache_cleanup.py mark-complete \
  --task-root /home/isp/state/cyf-local-build/tasks/cyf-NEW_BATCH/api \
  --artifact package/api.tar --component api \
  --source-commit FULL_API_COMMIT --source-tree FULL_API_TREE \
  --payload-sha256 ACTUAL_APPLICATION_JAR_SHA256
# Web：使用同批 /web、package/web.tgz、component web及真实Web commit/tree，不传API payload参数。
```

- 最近两批/组件、24h及当前/回退引用均保护，沿用原30分钟cron和锁；重新使用任务目录前先mark-active。详见`ops/maintenance/LOCAL_ARTIFACT_RETENTION.md`。根盘约1GiB仍偏紧，不能据此保证冷构建/新增回归或后续任意批次达600秒。

构建JDK目录已于2026-11-07按用户要求统一到`/home/isp/apps/dragonwell-21.0.11.0.11+10-GA`；此为目录原子迁移，不重下载、不另存一份、不改生产JRE。API包包含应用JAR及来源/测试/依赖证明，Web包包含静态资源及逐文件manifest；均为原安装事务输入，不是常驻运行依赖。历史安装记录和当前/回退绑定包本次不改动。

主机目录职责：构建任务及缓存归state、最终包归档归`/home/isp/pkgs/cyf`、历史维护备份归baks，源码/worktree归各项目。当前三个镜像已迁至pkgs，旧wsps/private-maintenance和空cyf-worktrees入口已移除；不通过搬动未完成工作树整理目录。见`ops/maintenance/HOST_DIRECTORY_LAYOUT.md`。

### LOCAL 发布涉及不兼容数据迁移（2026-11-07核验补充）

原API schema4 LOCAL descriptor可选`rollback_policy`，省略或`compatible`沿用原程序回退；显式`forward-only`用于已执行不兼容数据迁移的候选。该字段参与不可变binding并写入安装record，故障恢复从同一descriptor读取，不依赖一次性环境变量。启动失败保留候选和证据，不自动启动旧schema不兼容JAR；只有完成明确的数据恢复/兼容评估后才可另行回退。此能力不执行或授权迁移，也不恢复旧schema3准入框架。来源/摘要/备份/锁/健康保护不变；定向回归`ops/ci/aliyun-flow/tests/test_native_local_api.py`覆盖旧descriptor、forward-only失败及同源恢复。CYF当前主机已适配，源码与现行安装目录差异按任务handoff保留，不整文件覆盖旧修复。
