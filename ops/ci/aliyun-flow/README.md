> 2026-10-29 用户更新：Flow 只在 worker 上测试/构建/打包/上传后结束，不调用或等待生产主机；主机主动拉取固定 Run 制品后独立受控安装/核验。目标是卸载本机内存并减少计费，不重复构建已核验的精确制品；锁/身份/备份/完整性保留。此条覆盖下方旧 Flow 部署口径，详见根 AGENTS 同日规则及 docs/aliyun-flow-cicd-strategy.md。

# CYF 阿里云 Flow 工具

## 当前规则（2026-10-22）

- Flow卸载本机高内存Node.js/Gradle测试、构建和打包，并执行授权部署；轻量检查、API查询、发布协调、上线核验可本机执行。不是禁止Flow测试，也不是禁止本机使用Node.js/Gradle控制面。按实际负载分工，本机不生产打包/源码直发。
- 复用API5260799/Web4403172；develop不自动部署。版本发布提前固定授权、版本、完整源码、配对条件与恢复路径。Run完成本轮工作即结束，不添加外部等待、人工确认、ready文件轮询或上线验收阶段。
- 身份/权限、同Run制品摘要、发布锁、备份和可恢复安装仍保留；本机协调不绕锁，不新增无依据门槛。Flow终态、安装完成、健康/业务验收分开记录。
- 写配置复用flow-control.cjs：确认无活动Run/归属冲突，保存前值、固定候选哈希、单次写入并readback；不重复启动、不取消他人任务。云端当前内容必须实时查询，不能由本README或旧模板推断。
- 同Run版本化适配器接口仍为 `PIPELINE RUN COMMIT VERSION ARTIFACT_SHA256`；正式部署仅消费固定制品，不能以取消等待为由伪造Run或任取历史制品。若要分离构建部署，先验证来源契约和工具支持。
- 2026-10-22后续已更新默认CI模板并应用两端云端配置；Web294/API234均SUCCESS（177秒/337秒）。本任务未改backend-ci-run.sh、policy或主机helper，未部署/取消他人Run；两端均无外部等待作业。精确输入与核验见docs/implementation/handoffs/FLOW-RESOURCE-SPLIT-20261022.md；这不是部署适配器全部改造完成的证明。

### 2026-10-22耗时维护增量

前端默认`cloneDepth: 1`，release保持原测试；assets/all恢复完整历史再执行历史来源校验。Web296同源码实测127秒（原294为177秒），不可当长期耗时保证。后端只新增准备阶段持久化数值计时，summary中的`flowPreparationPhases`/`jdkBootstrap`用于区分JDK、字体、MySQL；API235实测293秒，字体准备37.76秒，执行策略未改。两端成功且同Run制品已核验，未部署。当前配置摘要/收益边界见docs/aliyun-flow-cicd-strategy.md与duration-optimization-results.json，不盲试缓存/JVM旧方案。

## 历史：FLOW-CI-01 后端手动云端冷测试/构建桥

日期：2026-09-09。以下记录说明一次性、ticket 绑定的后端测试/构建桥演进过程；它不是当前通用发布操作手册。

## 冻结执行范围

首轮 API 源码固定为：

- repo：`https://github.com/chcbz/juyiai-api.git`
- branch provenance：`develop`
- 实际构建 commit：`6267f3b16fe7b672a3c8479f058a662d9c75216c`
- 实际构建 tree：`936d6e4bcf3d7a4cc23cde62fa0e697be93d659b`
- 单测：`:common:jia-common-core:test --tests cn.jia.core.security.SensitiveDataSanitizerTest`
- 静态门禁：`validateLayering`
- 制品构建：`:starter:bootJar`

`:starter:bootJar` 自身依赖的 `PublicArtifactVerifier` 保持启用。桥拒绝 `-x`、`clean/build/check` 聚合、publish/upload/install/deploy/release、Gradle 属性注入和自定义任务图。

Flow 取源 tip 与实际构建 commit 是两个字段。例如 Flow 取到后续 `develop` tip `97ae8ef12c0a0306a40a04017f44139e1ca27823` 后，仍须显式 detached checkout 到 ticket 的 `6267f3b...`。receipt 分别记录 `flow.source_tip_sha` 和 `source.commit_sha`，不得宣称二者相等。

## 最小 CLI

所有可能执行 Gradle 的入口必须经过 orchestrator：

```text
cyf_orchestrator.py flow-remote issue   # 控制机签发不可变 ticket
cyf_orchestrator.py flow-remote run     # 云端校验并执行精确 argv
cyf_orchestrator.py flow-remote inspect # 控制机校验下载包，输出待审核导入字段
```

`flow_remote.py` 不能被直接用于 `issue` 或 `run`。`inspect` 只做本地完整性检查，不接受证据。

### 1. 控制机签发 ticket

签发必须在唯一主控 checkout 调用。它在现有 `/tmp/cyf-orchestrator.lock` 下读取唯一 `docs/implementation/TASKS.yaml` ledger，并要求：

- 指定 task 当前 owner 是该 task 的 writer/verifier；
- gate 是 `targeted_verification` 或 `verifying`；
- task 的 `exact_sha_tree` 精确等于本次 API source commit/tree；
- 本地 API Git 对象存在、tree 匹配，且 commit 位于 `origin/develop` 历史中。

它**不要求主控整仓 clean**，也不复制 ledger。ticket 只保留 owner/gate 与 ledger API tuple，不包含 blocker、next_action 或完整任务对象。orchestrator、bridge、runner、init script 以实际文件 SHA-256 组成 tool bundle；控制仓 Git HEAD/tree 不是构建工具版本。

示例（只有主控将目标 task 放入上述 gate 并绑定 API tuple 后才能执行）：

```bash
python3 ops/orchestration/cyf_orchestrator.py flow-remote -- issue \
  --task-id FLOW-CI-01 \
  --ticket /tmp/cyf-flow-tickets/FLOW-CI-01.json \
  --api-git-repo /home/isp/wsps/cyf/api \
  --repo-url https://github.com/chcbz/juyiai-api.git \
  --branch develop \
  --commit-sha 6267f3b16fe7b672a3c8479f058a662d9c75216c \
  --tree-sha 936d6e4bcf3d7a4cc23cde62fa0e697be93d659b \
  --selector backend-cold-smoke-v1 \
  --flow-organization 5fb7d76ee6f9d07f148529c7 \
  --flow-pipeline 5256653 \
  --remote-cwd /flow/workspace/api \
  --remote-tool-root /flow/workspace/flow-tools \
  --remote-run-base /flow/workspace/flow-output \
  --ttl-seconds 3600
```

命令输出 ticket SHA-256、receipt 绝对路径、selector 和 fixture digest。ticket 使用不可覆盖创建并设为只读。预期 ticket SHA-256 必须作为字面量写入受信 Flow YAML/Command，不能从 ticket 自身读取。

fixture digest 绑定：API tree、selector、完整 argv、tool bundle、Java major、wrapper properties SHA 和 Gradle distribution URL。完整 DB/Rabbit 集成及其它 selector 不在首轮范围内。

### 2. Flow 作业准备

新流水线 `5256653` 当前应保持手动、零 triggerEvents、零 deploy。主控负责 Flow YAML、API 操作和 Run 核验。建议让 API checkout、工具目录和输出目录成为 Flow workspace 下三个互不包含的兄弟目录：

```text
workspace/
  api/          # clean detached 6267 checkout
  flow-tools/   # 已审 tool bundle
  flow-output/  # receipt、日志和唯一 JAR；ArtifactUpload 使用此相对路径
```

generic Git source 可公开无凭证取 `develop` tip，但执行前必须：

1. 保留 Flow Run 记录的实际 tip，并映射为 `CYF_FLOW_SOURCE_TIP_SHA`；
2. 获取并显式 `git checkout --detach 6267f3b...`；
3. 保留 `refs/remotes/origin/develop`，使桥能证明固定 commit 属于 `develop`；
4. 确认 API checkout clean，origin URL 与 ticket 完全一致；
5. 把已审工具字节放在 ticket 的 `tool_root`，不能依赖控制机 `/root/.gradle` 或私钥；私仓消费认证只使用主控绑定的专用加密变量组，不复制本机配置。

云端只需 Python 3、JDK 21、Git 和源码自带 Gradle Wrapper。`cold-init.gradle` 使用：

- `beforeSettings` + `pluginManagement.includeBuild(api/plugin)` 从同一 API SHA 编译 settings 插件；
- 原组织固定 release/snapshot 消费仓库，加阿里云公共 Maven 镜像、Maven Central、Gradle Plugin Portal；
- 外置 `GRADLE_USER_HOME`、project cache、TMP/HOME 和所有 project build directories；
- task graph 中嵌套 Gradle `Exec` 拒绝规则。

### 3. 云端执行

Flow YAML 必须把受信平台字段显式映射到以下 allowlist 环境变量：

```text
CYF_FLOW_ORGANIZATION_ID
CYF_FLOW_PIPELINE_ID
CYF_FLOW_RUN_ID
CYF_FLOW_JOB_ID
CYF_FLOW_SOURCE_TIP_SHA
```

另需主控为新流水线绑定专用加密变量组，提供 `CYF_MAVEN_USERNAME` 和 `CYF_MAVEN_PASSWORD`。桥不复制完整环境；仅增加这两个消费凭证环境项，不传 AK、发布属性或其它 secret。两项缺失、空白、部分配置或无效控制字符在 Gradle/nonce 前拒绝，错误不含实际值。执行命令仍只有四个参数：

```bash
/flow/workspace/flow-tools/ops/ci/aliyun-flow/run-cloud.sh \
  /flow/input/FLOW-CI-01.json \
  HARD_CODED_EXPECTED_TICKET_SHA256 \
  /flow/workspace/api \
  /flow/workspace/flow-output/FLOW-CI-01/NONCE/receipt.json
```

`run-cloud.sh` 只分发到 orchestrator；Gradle 由 Python `subprocess.Popen(argv, shell=False)` 启动。native Gradle 非零退出码原样返回。

## 拒绝与并发边界

### 固定校验顺序

1. ticket 文件 SHA-256 与 Flow 字面量相等；
2. ticket schema/字段、期限、fixture/tool bundle 自洽；
3. Flow org/pipeline 环境匹配，Run/Job/tip 格式有效；
4. tool 文件逐字节匹配；
5. cwd、origin、HEAD、tree、wrapper、`origin/develop` ancestry、clean 状态匹配；
6. 对 `HEAD` 中不可变 `*.gradle`/`*.gradle.kts` blobs 做 Python 正则扫描，拒绝嵌套 Gradle；
7. 消费凭证预检通过后，原子占用本机 nonce；
8. 获取 `/tmp/cyf-gradle.lock`；
9. 锁内再次验证源码，然后执行唯一 argv；
10. 导出脱敏测试 XML、复核源码仍 clean、复核 OpenCV provenance、检查并包装制品；清理本 run 私有 scratch，最后写 receipt。

锁顺序固定为：签发只持 control lock；远端为 `nonce O_EXCL -> /tmp/cyf-gradle.lock`，不获取 ledger/evidence lock。远端不修改任何控制账本。

### 文件事务边界

- ticket、receipt、metadata 使用不可覆盖的同目录临时文件 + 原子 hard-link；
- nonce 一旦占用，即使 Gradle 失败也不可在同一 runner 复用；
- run root 必须是全新目录且与 checkout/tool root 不相交；
- receipt 最后写入，包含 stdout/stderr SHA、测试 XML 汇总、唯一 JAR、sidecar 和 metadata SHA；
- Gradle 成功但制品不唯一、XML 缺失/异常或 checkout 变脏时，bridge 返回失败，不能视为构建成功。

## 制品与 receipt

成功导出包含一个 SHA 命名 JAR及：

```text
artifacts/<jar-name>-<sha256>.jar
artifacts/<jar-name>-<sha256>.jar.sha256
artifacts/metadata.json
dependency-provenance.json
test-results/TEST-<relative-path-hash>.xml
gradle.stdout.log
gradle.stderr.log
receipt.json
```

receipt 记录 API source commit/tree、完整 argv、ticket/tool/fixture digest、Flow org/pipeline/run/job/source tip、native/bridge exit、起止时间、JUnit XML 汇总和文件 SHA。它不含认证密钥。

Flow `ArtifactUpload` 的 `flowPublic.filePath` 使用 workspace 相对路径，但目标必须是主控从 **receipt.files + receipt.json** 建立的干净导出目录；不得上传整个 run root、API checkout、Gradle 缓存或原始 build 目录。

## R3 私仓、依赖摘要与秘密边界（导出契约变更）

固定消费端点（调用者不可覆盖；有效 HTTPS 端口显式设为 443）：

```text
https://packages.aliyun.com/5fb7d76ee6f9d07f148529c7/maven/2049636-release-r6d3t8
https://packages.aliyun.com/5fb7d76ee6f9d07f148529c7/maven/2049636-snapshot-tdmfld
```

三个 repository 层（pluginManagement/settings/project）使用相同配置。只在这两个仓库配置 PasswordCredentials/BasicAuthentication，不注入 Authorization header、不允许 HTTP 降级、不使用任意 endpoint/proxy 环境变量。使用固定 wrapper 9.3.1 的原生 host/port-scoped HTTP authentication；显式 443 避免 ANY_PORT scope，跨 host/port 不提供消费凭证。HTTP GET 重定向由 Gradle 原生传输处理，不增加自建代理/下载器。该约束的真实网络行为仍属后续云端验收，不是本轮 Python 测试证明。

发布 DSL 所需的 `repoUsername`/`repoPassword` 仍为空，发布 URL 不指向私仓；ticket 仍禁止发布任务。现有凭证服务端权限**未声称是 read-only**，主控负责变量组/授权边界。已通知的组 44254 仅是主控配置输入，不硬编码进桥，也不由桥关联。

`org.opencv:opencv:4.5.5` 只允许 release 仓库供应（其它仓库排除此 module），固定实际 JAR **722802 bytes** / SHA-256：

```text
323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4
```

`configuration.incoming.afterResolve` 对实际解析 artifact 的字节校验，抛错先于该 file collection 交给编译/测试/打包；不是任务完成后的补验。桥成功打包前再校验同一缓存文件的路径、大小和 SHA。`dependency-provenance.json` 记录该 pin、controller provenance 文档名及 controller POM SHA `786de45db6266b338faf603d0555bdb491357aeece0f9608c3a08d78700dc203`；**POM 字段是主控认证获取的摘要，不宣称云端复核了 POM**。固定摘要与 init/bridge 实际文件字节经 tool bundle 进入 fixture digest；不把主控 Git HEAD 当工具版本。

stdout/stderr 在控制台和日志写盘之前做有状态跨块脱敏，覆盖原值、用户名:密码、UTF-8/Latin-1 Basic Base64 及常见 XML/JSON/URL 转义。Test/JavaExec/Exec 任务环境移除两项消费凭证；这不是针对恶意构建源码的进程沙箱，仍依赖固定、已审的 API/tool 源码。原生 Gradle 非零 rc 即使后处理失败也保留；日志传输异常不能成为成功证据。

**主控 cloud-command.py 模板必须同步修改（不由本 worker 改）：**

1. 在全新导出目录中只复制 `receipt.json` 与 `receipt.files` 引用、SHA/size 匹配的普通文件；禁止 glob 整个 run root。
2. **删除原先另行复制 `build/**/TEST-*.xml` 的逻辑。** `kind=test_xml` 已指向桥流式脱敏的 `test-results/TEST-<hash>.xml`；receipt 汇总也只解析这些脱敏 XML。
3. 新增 `kind=dependency_provenance`，路径 `dependency-provenance.json`；成功候选必须有此文件。它是待主控通过认证 Flow API 核实的声明，不是签名或自动 accepted evidence。
4. 私有 `home/gradle-user-home/build/tmp/project-cache` 在结束时清理（包括失败路径）；原始 XML/缓存不是导出证据。即使清理失败，也只能复制 receipt 引用文件，不能兜底上传原始目录。
5. 唯一 JAR 导出前检查原始 ZIP、解压成员及嵌套 JAR/ZIP 中的消费凭证；发现秘密、坏 ZIP 或超界即拒绝导出，**不改写 JAR**，保留 PublicArtifactVerifier。扫描上限：总解压 1 GiB/150000 entries、嵌套 3 层、单嵌套 ZIP 128 MiB，超界 fail-closed。

CLI/ticket/receipt 顶层 schema 不变；`receipt.files` 增加上述两种记录。旧工具的成功 receipt 不因本次工具更新自动成为 R3 候选。主控须在独立 delta review 后生成新 tool/fixture/ticket/nonce，另审精确 YAML、变量组与上传模板；本提交不授权新的云端 Run。

## 控制机审核与 evidence 导入

receipt 本身可由本地用户伪造，**绝不能直接自动成为 accepted evidence**。主控下载 ticket、receipt 及 receipt 引用文件后，先通过认证 Flow API 核对：

- organization/pipeline/run/job；
- Run 的取源 tip；
- 受信配置中的字面 ticket SHA；
- 实际命令、JDK 21、无部署阶段；
- 上传文件来自同一 Run/Job。

再执行本地完整性检查：

```bash
python3 ops/orchestration/cyf_orchestrator.py flow-remote -- inspect \
  --ticket /tmp/cyf-flow-tickets/FLOW-CI-01.json \
  --expected-ticket-sha256 HARD_CODED_EXPECTED_TICKET_SHA256 \
  --receipt /path/to/downloaded/receipt.json
```

输出中的 `automatically_accepted` 永远为 `false`，并提供 `evidence_put_fields`。只有主控完成上述认证核对后，才可按现有 verification gate 手工调用 `evidence-put`。本工具不实现 import，也不创建第二账本。

## 本地轻量验证

仅标准库和 shell/static 测试，不调用真实 Gradle：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s ops/ci/aliyun-flow/tests -p 'test_*.py' -v
```

新增测试使用 Python shebang fake-wrapper 和合成 ZIP/依赖 pin，不运行 Groovy/真实 Gradle，不把静态断言当成冷构建通过。覆盖跨 chunk 原值/Basic 脱敏、双 sink、缺失/部分认证、环境隔离、压缩嵌套制品泄密拒绝、解析文件 hash 漂移、清理与脱敏 XML、native rc，以及固定端点/消费前 hook/发布空凭证静态约束。

原有覆盖：ticket 篡改/过期/未知字段、ledger source mismatch、主控 unrelated dirty、工具篡改、源码 dirty、HEAD/tree/branch、危险 argv、Git blob nested-Gradle 扫描、nonce replay、native rc、XML 汇总、唯一 JAR、receipt 文件 SHA，以及“不自动 accepted”。

## 未覆盖门禁

首轮结果只证明指定纯单测、layering 和 bootJar/PublicArtifactVerifier。它不代表全量 API 测试、MySQL/Rabbit/Testcontainers 集成、生产 schema、部署、服务健康或业务验收通过。

### 2026-11-03 固定制品的分支溯源（轮询发布修复）

F06/E05主机schema runner不再要求receipt的branch等于develop。branch是必需的非空来源信息，不是发布授权名单；真实pipeline/run、完整commit/tree、clean标记、来源identity digest、receipt/JAR/依赖摘要及实际已安装记录继续逐项绑定，擅改branch而不重绑定identity仍拒绝。否则固定候选分支已通过Flow并合入develop后，会在应用安装成功才被后置hook拒绝。

核对/回归入口：`test_api_additive_schema.ApiAdditiveSchemaTest`、`test_api_e05_additive_schema.ApiE05AdditiveSchemaTest`及`test_api_e05_flow_deploy`。定向新增“固定feature branch可用且不重建既有表”和“branch篡改未重绑定identity必须拒绝”；E05 runner文件摘要须随该固定工具候选同步，不削弱制品或schema检查。源码、实际安装与Run447恢复证据见`docs/implementation/handoffs/JUYITING-POLLING-20261102.md`，旧失败记录不重标成功。

本机用临时systemd承载API安装时，必须显式保留安装器启动的生产JVM生命周期（既有scope，或经确认的RemainAfterExit/KillMode设置）；默认短命service会在后置hook失败退出时清理同cgroup JVM。不要用重建、重复安装或伪造Flow身份处理后置检查失败；保留原回执，核对实际已装字节和锁后只完成相应恢复。
