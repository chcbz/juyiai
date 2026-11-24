> **2026-11-16 现行统一策略：** Web/API/Runtime默认在自有SSH worker `203.32.84.239` 测试、构建和打包；控制机固定输入、回传核验并执行已授权的原LOCAL安装事务。不自动启动付费Flow、不自动回退控制机重型构建。完整规则见[根AGENTS](../../AGENTS.md#juyiting-build-release-policy)，具体执行见本文[SSH入口](#ssh-构建服务器2026-11-16迁移入口)。Web/API必须显式选择SSH参数，Runtime使用原参数化builder与同一传输，不宣称三端一键发布。下文冲突的Flow-only或控制机默认构建说明只作历史；身份/ACL、锁、摘要、备份恢复与独立验收不变。

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

- 2026-11-16统一口径：单次必要单元测试、构建、打包、构建锁/排队等待及制品回传共用600秒，不按内部阶段重置，不跨源码候选／开发过程／重试累计；源码/工具/缓存准备单独留证，构建入口内实际依赖安装/核验不移出计时。生产安装/备份恢复/启动/健康另计，异常重试归因后重新计算。回归验证与业务验收单独记录、不受此限；不把单元测试改名豁免。重试前归因、保留原失败和耗时；同根因同输入连续失败两次不盲重试。单次超限仍按根AGENTS申请例外，历史累计不构成扩时理由。保留身份、锁、完整性及恢复保护，不下传应用或生产服务deadline。下方旧工具实现说明是历史事实，不代表已按本条适配。
- 2026-11-15用户更新：可复用构建缓存保留；限定构建基目录中的未登记历史包/API生成class/JAR也由既有自动入口按24小时、最近两批及当前/回退/并发保护发现回收，删除包前保留唯一证据，不要求补登记或声明任务结束。完成登记仍兼容；不是旧准入、生产发布授权或全目录清理。精确范围与主机安装状态见 `ops/maintenance/LOCAL_ARTIFACT_RETENTION.md`。

> 历史（已被2026-11-16统一策略覆盖）：2026-10-29 用户更新：Flow 只在 worker 上测试/构建/打包/上传后结束，不调用或等待生产主机；主机主动拉取固定 Run 制品后独立受控安装/核验。目标是卸载本机内存并减少计费，不重复构建已核验的精确制品；锁/身份/备份/完整性保留。此条覆盖下方旧 Flow 部署口径，详见根 AGENTS 同日规则及 docs/aliyun-flow-cicd-strategy.md。

# 历史交付入口（2026-10-22；非当前默认）

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
- Web/API/Runtime必要测试与构建默认在指定SSH worker，轻量诊断可在控制机；后端先读build.gradle，再经原gradle串行入口，保留validateLayering。preflight不绕过锁、授权或失败处理，不自动回退控制机重型构建。

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

文档整理后复用 `./sddw check-docs [feature-id]`，全目录默认覆盖规则、当前索引和特性主文档，检查范围及历史例外见 [SDD说明](../../docs/sdd-workflow.md#sdd-document-check)。该命令不执行应用测试/构建、不修改pin/台账、不比较历史SHA与当前checkout；不能作为发布验收。 2026-11-16已恢复原导航映射并适配公开导出：只有 `sdd-document-map.json` 的 `export_profile.omitted` 精确列出的内部集成清单/历史来源/附件缺失可报告为 `unavailable_exported_references`（未包含、未验证）；不能豁免现行文档/源码或目录通配。已存在文件仍检查，未列出的断链仍失败，不以导航PASS宣称缺失证据有效。既有 `sddw verify` 保留模板候选核验语义。工具自身定向回归：`python3 -B -m unittest discover -s ops/orchestration/tests -p test_sdd_docs.py -v`。

## 本地快速构建与受控发布（2026-11-07）

<a id="api-local-build-baseline"></a>
### 后端本地构建默认执行基线（2026-11-13）

执行要求见[根规范](../../AGENTS.md#api-local-build-policy)。本节维护可执行参数；后续API任务默认沿用，不复制新的构建runner。目标为同批必要测试、构建、打包及锁等待≤300秒，既有单次600秒受控停止不变。Web/Runtime不机械继承本节参数。

| 项目 | 默认执行方式 | 不得退回/混淆 |
| --- | --- | --- |
| 入口与状态 | worker系统Python3.14运行 `local_build.py --package`（控制器用已验证Python3.11），委托原编排器和Gradle锁；任务为本Owner可用的 `targeted_verification` 或 `verifying` 状态，commit/tree与干净源码一致 | 裸跑Gradle、绕锁、手改任务登记、从生产目录编译 |
| 工具链 | 现行入口的Gradle9.3.1、Dragonwell21.0.11；构建JVM为C1-only、堆768m/Metaspace384m/ActiveProcessorCount2；`--no-daemon --parallel --max-workers=2 --build-cache` | 为凑时限增加worker/堆、默认恢复完整分层JIT、修改生产JVM；新参数先定向验证和完整实测 |
| 输出与缓存 | 新批次独立普通磁盘buildDir，显式传入已核验的持久cache-home；仅JavaCompile复用标准内容寻址结果 | 清缓存作为常规步骤、复用旧测试/分层/JAR、无输入绑定借用class文件 |
| 编译分析 | 仅本地init设置 `JavaCompile.options.incremental=false`，cache miss仍正常javac/注解处理 | 把关闭一次性增量分析误当关闭build-cache；改普通项目开发构建 |
| 状态快照 | Test及最终bootJar使用 `doNotTrackState`，保留原依赖连线及动作，均当批新执行 | 仅设 `upToDateWhen(false)` 后继续维护不可复用快照；跳过真实测试/原制品安全扫描 |
| 依赖完整性 | OpenCV用artifactView/componentFilter只取目标模块；仍校验4.5.5、SHA-256、大小、来源、消费前拒绝和回执 | 为单个pin物化全图、按期望版本过滤导致漏检、lenient或跳过校验 |
| 最小必要验证 | 原 `local-fast-baseline-v3-critical`：Agent认证/权限、Auth表单、生产邮件、制品安全及POI检查，另执行validateLayering和fresh bootJar；业务相关用例显式追加 | 将95项当永恒固定数量；删必要测试、默认编译无关诊断或整个历史test树 |
| 包与检查 | 普通 `api.tar`；结构验证一次，发布前再核对源/证据及外部输入SHA/大小；流式摘要；正式包/证据fsync和原子发布保留 | 外层重复gzip、反复ZIP/XML/邮件扫描、对可丢弃扫描副本逐个fsync；删除正式完整性检查 |

#### 执行前与失败处理

1. 从根规范进入当前任务，核对Owner、源码完整commit/tree、允许验证的任务状态、相关build.gradle及缓存来源。`--plan-only`只检查输入和生成计划，不是构建成功；不要等进入Gradle后才修正任务状态。
2. 先观察普通磁盘可用空间、已有构建、CPU负载与缓存完整性，沿现有串行锁安排；不得停生产/他人进程、开付费Flow、升配或改积分模式。空间不足时只按原保留规则处理本任务明确失效临时副本，先保存唯一证据，不清全局缓存。
3. 选择已有且已核验的 `--cache-home`；**不要盲用历史示例的 `gradle-home` 目录**。本机2026-11-13原home曾损坏，成功批次使用独立恢复home；当前选择以实际目录、同版输入及完整性核验为准，不以目录名/mtime判断。依赖齐全时用 `--offline`，缺依赖明确失败；新依赖另按真实解析需要处理，不静默退回联网或伪造命中。
4. 用同一入口完成必要测试→分层→fresh JAR→打包，按实际依赖允许内部并行，**整体只计时一次**。保留inputs/result/log、XML、proof和包内证据原字节，核对外部/包内JAR及包SHA。不同源码或缓存/CPU条件不能当受控A/B；全编译命中必须如实说明，不能外推冷构建保证。
5. 总时长超过300秒记录目标未达；超过600秒按原受控停止及例外规则处理。保留失败结果并分段归因；同根因同输入连续失败两次按原编排器停止盲重试，有真实修复再继续。不拆单测/打包改名规避计时。
6. 构建通过后不自动安装；只有精确输入及有效证据匹配才复用包执行另获授权的受控部署。结束时保存包外证据并按下方现有 `mark-complete` 登记，不重新压缩或为安装重试重建同一包。

#### API单组件调用模板（替换所有占位符，不直接照抄旧批次）

```bash
set -euo pipefail
cd /home/isp/wsps/cyf
PYTHON=/root/.local/bin/python3.11
TASK=EXISTING_TASK_ID
BATCH=NEW_BATCH_ID
SOURCE=/ABS/CLEAN/API
CACHE_HOME=/ABS/VERIFIED/GRADLE_HOME
BATCH_ROOT="/home/isp/state/cyf-local-build/tasks/cyf-${BATCH}"
mkdir -m700 "$BATCH_ROOT"
args=(--task-id "$TASK" --source "$SOURCE" --output "$BATCH_ROOT/api"
  --cache-home "$CACHE_HOME" --jdk /home/isp/apps/dragonwell-21.0.11.0.11+10-GA
  --version ACTUAL_API_VERSION --batch-id "$BATCH" --package --offline
  --regression-arg=--info)
# 按真实变更在args追加 --regression-arg=:模块:任务、--regression-arg=--tests 等。
"$PYTHON" ops/orchestration/local_build.py "${args[@]}" --plan-only > "$BATCH_ROOT/plan.json"
systemd-run --unit="cyf-${BATCH}" --wait --pipe --collect \
  --property=RuntimeMaxSec=600 --property=KillMode=control-group \
  --property=WorkingDirectory=/home/isp/wsps/cyf \
  "$PYTHON" /home/isp/wsps/cyf/ops/orchestration/local_build.py "${args[@]}" \
  2>&1 | tee "$BATCH_ROOT/build-unit.log"
```

本模板不会自动创建授权或任务Owner。执行前通过现有 `cyf_orchestrator.py transition` 核对/更新本任务验证状态及完整commit/tree；不能强占他人任务。冷缓存或缺依赖时不要直接承诺300秒。正常复用编译缓存的实测：工具候选`6fae56721ee1378b73fd102126a3055dd57c31f8`、API `80618640d6dd48f23ae668b59ea88778d9e57bdf`；批次`api-build-5min-20261113-02`总141.108秒，95测试0失败/0错误/0跳过，75项编译缓存复用。原始证据在 `/home/isp/state/cyf-local-build/tasks/cyf-api-build-5min-20261113-02/measurement.json`，这是历史固定输入实测，不是未来批次的成功回执。


- API候选验证与打包均使用下方现有 `local_build.py`；通过 `--regression-arg` 原样追加业务任务和 `--tests`，不要为每次重试复制 `run.py` 再手拼Gradle参数。该入口保留 `--parallel --max-workers=2 --build-cache`、compile-only缓存政策、当批测试/分层检查/fresh JAR；只设置依赖缓存目录不等于启用编译产物缓存。
- 包含真实Unix socket的测试应选短的普通磁盘批次路径（如`/home/isp/state/cyf-build/<批次>`）；临时目录仍是该批次的`tmp/`。路径过长会导致socket绑定失败，不是构建超时，不能通过删除测试或放宽身份检查处理。
- 单独构建仍在任务专属 `systemd-run --wait --pipe --collect --property=RuntimeMaxSec=600 --property=KillMode=control-group` 内运行；不是生产服务的执行容器。`local_build.py` 不安装，不因构建成功自动发布。
- 定向测试筛选不缩小生产依赖图；维护测试引用starter主输出时确实需要编译应用图，不能靠去掉任务/必要检查凑600秒。内容匹配的JavaCompile结果可复用，测试结果和最终JAR不能借缓存跳过。
- orchestrator输出 `GRADLE_LOCK_WAIT`、含`wait_seconds`的 `GRADLE_LOCK_ACQUIRED`，结束输出`GRADLE_EXECUTION_TIMING`的 `lock_wait_seconds`、`elapsed_seconds`（Gradle执行）、`invocation_seconds`（含前置和等待）。锁等待仍计入原600秒；超时保留原结果，不移动计时起点。任务阶段看现有 `CYF_GRADLE_PHASE` / `CYF_TASK_TIMING`，归因时加`--regression-arg=--info`可区分FROM-CACHE、重编原因和实际测试。
- 按实际主机负载安排重型任务；不停止生产/其他任务，不扩大超时，不承诺共享主机任意竞争或全冷缓存必定600秒。异常必须有实质变化（源码修复、已证实缓存/负载/工具修复）才重试，不以循环重试代替归因。


- API 构建入口 `local_build.py` 委托现有 orchestrator、跨任务锁和 Gradle；Web 构建入口 `local_web_build.py` 按锁与工具链复用完整依赖（首次 npm ci）、定向基线、原源码 Vite 配置与完整 public 打包。两个 builder **不安装**；新输出必须在干净源码和生产目录之外。
- 完整同批入口 `local_release.py --install`：显式固定任务、两端完整 commit、版本、工具链、缓存、全新输出与包外 evidence-dir。串行 Web/API 构建，再由已安装的原 helper 执行 LOCAL 受控事务，核对前代摘要、备份、健康、签名、安全边界和全部线上入口/JS/CSS 摘要。没有伪造 Flow Run，未恢复旧准入。
- **2026-11-08时限实现：** `local_release.py`按Web/API测试、构建、打包单元累计`buildSeconds`计算600秒预算，保留剩余预算RuntimeMaxSec及失败/超时证据。安装、启动、健康、业务验收和前置检查不消耗构建预算，不向Web安装器下传剩余构建时限；安装器既有网络/恢复限制不变。`wallSeconds`仍记录完整交付墙钟，`under600Seconds`明确仅表示构建阶段。5项定向工具回归通过，尚未执行改动后完整双端发布；本任务沿原独立LOCAL安装器复用固定包。
- API 热缓存仅复用已验证工具/依赖及 JavaCompile 产物；测试、validateLayering、fresh bootJar 均当批新执行。构建采用 Dragonwell21、C1-only与 workers2/内部 parallel（2026-11-13：完整tiered JIT试验未达标且观察到大量C2启动CPU消耗，恢复原构建参数回测；不能把恢复参数本身当作达标），不改生产 Temurin/JVM 参数，不带 `CYF_API_STARTUP_DIAGNOSTICS`。公共 artifact/POI 与认证/生产邮件类路径检查保留；2026-11-13默认不再编译/运行启动计时、性能指标及Elasticsearch健康隔离三组测试（上次批次共10项），不沿用旧105项作为当前数量。相关功能变更时通过现有 `--regression-arg=:starter:test --regression-arg=--tests --regression-arg=完整测试类名` 加入；默认选择器为 `local-fast-baseline-v3-critical`。去掉逐任务依赖图打印，保留阶段/任务耗时、凭据移除和禁止嵌套Gradle。不是全功能回归。`--plan-only` 可查完整输入/实际命令而不构建。
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
  --cache-home /ABS/VERIFIED/GRADLE_HOME \
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

组合发布入口通过 `--api-rollback-policy forward-only` 将不可回退决策固化进该次 API 安装描述并核对安装回执；不是给启动脚本设置临时环境变量。若旧reader不能识别已写入的 usage/报价格式，须明确选用该参数，由兼容新格式的版本前修。未选参数保持已有兼容发布语义，并不推定具体业务候选可回退；该参数不执行迁移，不改变 Web/Runtime 的回退策略。

原API schema4 LOCAL descriptor可选`rollback_policy`，省略或`compatible`沿用原程序回退；显式`forward-only`用于已执行不兼容数据迁移的候选。该字段参与不可变binding并写入安装record，故障恢复从同一descriptor读取，不依赖一次性环境变量。启动失败保留候选和证据，不自动启动旧schema不兼容JAR；只有完成明确的数据恢复/兼容评估后才可另行回退。此能力不执行或授权迁移，也不恢复旧schema3准入框架。来源/摘要/备份/锁/健康保护不变；定向回归`ops/ci/aliyun-flow/tests/test_native_local_api.py`覆盖旧descriptor、forward-only失败及同源恢复。CYF当前主机已适配，源码与现行安装目录差异按任务handoff保留，不整文件覆盖旧修复。

### 2026-11-13 本地OpenCV解析范围

`local-build.init.gradle` 的 afterResolve 校验只通过 artifactView/componentFilter 读取 org.opencv:opencv 的实际 artifact，不为校验单一模块而强制物化整套第三方/项目 artifact。版本不参与过滤，仍拒绝非4.5.5版本及 SHA-256/size 漂移；原始来源仓库限制、消费前检查与来源回执保持。不启用 lenient，不缓存/跳过校验结果。此变更本身不证明完整构建达标，耗时以固定批次实测为准。

### 2026-11-13 全新批次不维护增量编译分析

本地入口强制全新buildDir，未命中标准JavaCompile缓存时本来就需要全量javac。专用init将JavaCompile.options.incremental设为false，避免生成后续批次无法复用的增量依赖/类路径分析；不改项目开发构建、不关闭标准内容寻址build-cache，不改javac/注解处理器输入及必要测试/分层/fresh JAR。真实隔离fixture已验证原模式与新模式缓存键相同、跨新输出命中、无缓存重新编译的生成源码/class摘要及运行结果一致；这不是完整应用构建达标证明，完整批次另计。

## SSH 构建服务器（2026-11-16：迁移入口）

根AGENTS已将 Web/API/Runtime 今后默认构建位置统一为用户指定的 `203.32.84.239`；该主机只测试、构建、打包，不接收生产安装权限、不启动 Flow。生产机继续执行原 LOCAL 安装器，版本、身份/ACL、锁、备份、恢复、健康及线上资源摘要检查不变。Web/API显式参数见下文，Runtime参数化builder与原生闭包见下方专节；不是三端一键发布器，生产发布仍由既有受控事务负责。

Web/API复用 `local_release.py`，每次在原固定源码参数上显式追加（无参不自动选择worker）：

```bash
--build-host 203.32.84.239 \
--web-runtime-config /ABS/PINNED/PUBLIC/runtime-config.json \
--remote-root /home/isp/wsps/cyf-build/NEW_BATCH \
--ssh-known-hosts /home/isp/conf/cyf-build/known_hosts
```

- `remote_build.py` 只提供 SSH 传输，不能独立发布；只接受授权配置 `JYT_BUILD_SERVER` 的主机，并使用已固定的 SSH host key，拒绝自动信任新密钥。登录凭据由控制机 `/root/.codex/auth.json` 读取，不进入 argv、Git、源快照或回执；askpass 私有脚本只引用凭据文件，正常结束删除。
- 每个候选只有一套远端干净源码快照：controller/API/Web 使用原始完整 commit/tree 的浅 Git 克隆，**不复制脏工作区**。远端任务台账显式携带实际 Owner、任务ID、源码身份和允许验证状态；远端写入不能覆盖控制机其他任务状态。
- 执行前远端原 API builder 的 `--plan-only` 核对工具/命令/输出；Gradle 仍经现有编排器串行执行。API 使用已核验、私有的持久 cache-home，仅复用依赖/脚本/JavaCompile缓存，不复制项目buildDir、测试结果或最终JAR当作新批次成功。初次迁移缓存的输入、摘要、日志独立保存，不算应用构建通过。
- SSH worker 使用 `/home/isp/apps` 中固定 Node/JDK/Gradle，`/home/isp/state` 放缓存与每批输出、临时目录；`/tmp`为tmpfs，不用于构建。Web仅加载单独的 `conf/cyf-build/web.env` 公开VITE配置，并与控制机显式固定的 `--web-runtime-config` 内容比较后才允许安装；Maven消费凭据只在worker私有 `conf/cyf-build/maven.env` 中提供；不复制整个 Codex auth、全局 Gradle init 或生产凭据。
- Web/API测试、构建、打包各在**远端** task-owned systemd单元执行，第二阶段只拿到同一次执行的剩余600秒；不会因SSH断线让构建无限继续。SSH/归档回传耗时也计入该次构建阶段记录，归档与rsync只使用该阶段剩余预算；不把worker安装、缓存迁移或回归验收伪装成应用构建成功。不向生产安装/服务下传构建deadline，不本机自动回退构建。
- 原始包（内含fresh JAR）、构建输入、日志、XML及proof回传到控制机同名批次输出路径；SSH固定host key的rsync块差量只减少网络字节，可用当前API JAR/Web包作字节basis，但不复用测试或产物成功事实。worker原归档与接收端完整SHA-256/大小必须一致，之后才安全解包；不重新压缩/改写待发布包。SSH传输、原制品SHA和安装器原验证共同保证来源。`evidence/ssh/transport.json` 记录构建主机、控制器/API/Web完整commit/tree、传输摘要及大小；source_kind仍为真实LOCAL，不虚构CI/Flow Run。
- 本入口不自动配置SSH、安装工具、恢复缓存或取得发布授权。worker连接/构建失败停止该次交付、保存真实失败；归因后才以新批次重试。不复用正在运行的一次执行来续时，不抢他人锁。

本次实际安装、固定候选、测试、尝试和发布状态见 `docs/implementation/handoffs/REMOTE-BUILD-MIGRATION-20261116.md`；2026-11-16批次remote-20261116-03已实测构建与回传316.679秒并完成原受控安装，前两批FAIL原样保留；不代表全冷/任意负载均保证此耗时。后续Web/API任务继续显式选择SSH参数，不自动回落生产机重型构建。

缓存准备注意：Gradle不可变Groovy DSL缓存的空目录也是输入，快照必须保留并核验目录清单；只校验文件不代表缓存结构完整。控制机使用已验证的Python3.11（当前 `/root/.local/bin/python3.11`），不以系统默认Python3.6执行控制器；worker使用已验证系统Python3.14。

### Runtime 远程构建（2026-11-16补齐）

`runtime_build.py` 是原 Runtime114 LOCAL 代码包脚本的参数化提升，不是新的生产安装器。保留原34个测试文件与 `collateExecutionPayload`；`--regression-test` 可追加本次变更的源内 `.test.mjs`，不能替换/减少基线。代码包不携带生产 HOME、auth、身份、会话或目标 ABI 依赖；实际安装主机继续验证既有依赖及固定实体 app。

1. 沿原任务登记唯一 Owner、固定完整 commit/tree、版本及实际发布授权；不要跟随其他任务的新 HEAD。`RemoteBuild.prepare(..., revisions={'controller': controller_commit, 'runtime': runtime_commit})` 可浅传输精确提交，不复位/覆盖活动工作区。
2. worker 在 `/home/isp/state/cyf-local-build/runtime-dependencies/<精确锁SHA>/` 准备同候选 `package.json`/`package-lock.json`，用既有 npm 缓存运行 `npm ci`；不用生产 node_modules，不读取 Maven/Web 配置。原生测试工具闭包为 Node、bwrap、slirp4netns、nft、nsenter/unshare，以及已核验的 Runtime 专用 Codex0.167.0 原生 binary **和同发行版 codex-resources**。
3. 先在 worker 用下列参数加 `--plan-only` 核对路径及追加selector（计划不构成构建成功），再经原 `RemoteBuild.build_command` 调用 task-owned systemd 单元。示意路径须换为本次干净快照和全新输出：

   ```sh
   /usr/bin/python3 /ABS/CONTROLLER/ops/orchestration/runtime_build.py \
     --source /ABS/RUNTIME --commit FULL_COMMIT --tree FULL_TREE \
     --output /home/isp/state/cyf-build/NEW_BATCH --build-id REAL_BUILD_ID \
     --node /home/isp/apps/node/bin/node \
     --codex-bin /home/isp/apps/cyf-runtime-build-codex-0.167.0/bin/codex \
     --dependencies /home/isp/state/cyf-local-build/runtime-dependencies/EXACT_LOCK_SHA \
     --regression-test conf/codex-bridge/test/image-input.test.mjs \
     --regression-test conf/codex-bridge/test/typed-inspection-input-carriers.test.mjs
   ```

   上例两项追加selector仅是材料输入变更的示例，后续按实际影响集选择；不可替换/减少原基线，也不将这两项强加给所有任务。

4. 本 worker 是 Ubuntu26/uutils，原测试会把 cat/sleep 复制成不同名称后验证原生 inode；用 `build_command(..., runtime_source=..., native_fixtures=[('/usr/bin/gnucat','/usr/lib/cargo/bin/coreutils/cat'),('/usr/bin/gnusleep','/usr/lib/cargo/bin/coreutils/sleep')])`，只在该 systemd mount namespace 绑定 GNU 工具，不改系统命令。原生沙箱需要的 AppArmor profile 仅匹配隔离视图 `/runtime/codex-resources/bwrap` 并授予 userns；配置 `/home/isp/conf/cyf-build/runtime-bwrap.apparmor`，系统链接 `/etc/apparmor.d/cyf-runtime-build-bwrap`。**不关闭全局 AppArmor/userns 限制，不以跳过真实隔离用例替代依赖准备。** 其它主机按实际工具/内核决定，不机械安装该兼容绑定。
5. `build_command` 的远端期限与 `collect('runtime', ..., timeout=remaining)` 共用600秒。源码/依赖准备另计，不能拆测试与打包续时；`build-result.json`、原 TAP、package manifest、原 tgz、工具/binary/resources SHA均回传，重复源码/payload及 scratch 不回传。包仍是 LOCAL 来源，不伪造 Flow Run。
6. 构建不是安装授权。按既有 Runtime 发布锁、前代 CAS、固定目录/备份/forward-only 边界发布；若另一 Owner 正发布，告警并等待，不抢锁/降级。已验证上线的**同一源码及全部 portable 字节/模式、原安装清单/依赖和实时通道**均一致时可锁内幂等确认，不重复搬文件、重启、认证迁移或收费回归；保留原安装来源，只新增精确远程验证回执，不把包 SHA 不同但代码相等伪称为同一原包。

实测及失败原始回执见[迁移handoff](../../docs/implementation/handoffs/REMOTE-BUILD-MIGRATION-20261116.md)。本入口不编译 Runtime 专用 Codex 源码补丁，不修改全机 Codex，也不自动部署其他任务最新候选。

生产 Runtime 走公网 API 时，还须核对既有 `ops/ci/aliyun-flow/host/nginx/cyf-runtime-native-locations.conf` 的精确协议路由。2026-11-17已补齐 protocol6 `/internal/agent/executions/commands`（GET）及执行 run 的指定 POST 操作，复用原代理鉴权，不能以 blanket `/internal` 放行代替；WebSocket在线/READY不等于原生HTTP执行可达。定向入口 `python3 -B -m unittest discover -s ops/ci/aliyun-flow/tests -p test_runtime_native_nginx.py -v`；实际公网401/405负例及 Eva两轮私聊见[升级handoff](../../docs/implementation/handoffs/EVA-RUNTIME-UPGRADE-20261117.md)。
