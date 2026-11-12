# 前后端构建迁移至云效 Flow：只读评估

> **历史记录说明（2026-09-11）：** 本文主体保留 2026-09-09 的迁移过程和失败分析。当前权威策略与最新状态已迁移到 [`docs/aliyun-flow-cicd-strategy.md`](aliyun-flow-cicd-strategy.md)：后端现使用 `5260799 / cyf-api-kit-ci`，Run 13 已完成云端测试、`bootJar` 和生产部署；前端 `4403172 / cyf-web-kit` Run 86 发布成功。不要再把本文早期的旧后端流水线或 R3 失败当作当前状态。

核查日期：2026-09-09；实时 API 查询始于 16:36 Asia/Shanghai。组织：`5fb7d76ee6f9d07f148529c7`。

## 结论

可行，且前后端均已有流水线。复用云端构建集群，生产主机只接收不可变制品、安装、启动和健康检查；不要把本机构建脚本包一层远程调用，也不要把本机注册成构建执行机。

本次仅查询配置、运行和部署单、检查本地代码；未修改云效配置、推送代码、触发流水线、运行构建/测试或控制任何服务。仅为只读查询安装了技能自身的固定 SDK 依赖。

## 实时 API 证据

通过本机已有阿里云 CLI 凭证在内存中调用只读 DevOps API。未保存凭证、webhook、完整流水线 YAML、签名下载 URL。

| 项目 | 前端 | 后端 |
| --- | --- | --- |
| 流水线 | `cyf-web-kit` / `4403172` | `cyf-api-kit` / `1466118` |
| 查询时最新运行 | `85`，`SUCCESS` | `167`，`SUCCESS` |
| 运行开始时间 | 2026-09-09 00:03:35 +08:00 | 2026-06-21 23:45:19 +08:00 |
| 实际来源分支 | `master` | `master` |
| 实际来源提交 | `77666e8fc1b2060ff3db8374b5de4539a5e5e53d` | `982259abfe333439c062f46d047e1e04276d7cdc` |
| 作业 | 扫描、单测、构建、主机部署均 SUCCESS | 扫描、构建上传、主机部署均 SUCCESS；无独立测试作业 |
| 部署单 | `69254729` | `64335028` |
| 部署单结果 | 一批一台 Success，clientStatus healthy | 一批一台 Success，clientStatus healthy（历史运行） |

组织流水线列表已遍历至无下一页；运行列表第一页用于确定最新运行，未将历史成功运行当作本次新发布。两条流水线当前 sources 均配置 `master`、`push`，触发过滤 `.*`；不能默认推送 `develop` 就会运行，修改或推送前还需核对完整触发设置。

证据来源：`ListPipelines`、`ListPipelineRuns`、`GetPipeline`、`GetPipelineRun`、`GetVMDeployOrder`。本次没有下载制品、比较线上资源字节或核验后端当前运行 JAR，故不声明当前线上版本已核验。

## 当前配置与迁移缺口

### 前端：复用并规范化

- 测试/构建使用 `K8S-4`、Alinux3 容器；命令分别为 `npm install && npm run test`、`npm install && npm run build`；打包 `dist`。
- Node 安装步骤当前配置 `23.5`，不等于项目脚本最终实际运行版本；技能历史记录曾说明脚本固定 Node 20.20.2，需要在目标提交上核对，而非盲改版本。
- 部署到主机组 `28833`，当前直接向 `/home/isp/hosts/cyf/web/kit` 下载并解包。建议增加 SHA-256、版本清单和暂存目录校验后切换，保留原扫描/测试/性能门禁。
- 本机 `web` HEAD 为 `42b6d804abdb3888c01277b892326af3186d6a2c`，且有未提交修改；技能提及的 `web/scripts/ci/README.md` 在本 checkout 不存在。云端成功不代表此工作区未提交改动已发布。先确定发布提交，不能覆盖或自动重置现有改动。

### 后端：必须先适配，不能直接点发布

- 已有 Java 构建上传作业，构建集群 `K8S-9`，`CI_RUNTIME_VERSION=jdk21`，制品目录 `starter/build/libs/`。
- 当前构建命令含 `./gradlew build -x test`，并配置 init.gradle / Maven 本地仓库相关步骤。历史绿灯不能作为当前完整测试证据。
- 仓库使用 Gradle Wrapper 9.3.1、自定义 settings 插件 `cn.jia.jia-dependency-management:1.1.2-SNAPSHOT`。本机 `/root/.gradle/init.gradle` 注入 pluginManagement、repositories、mavenLocal。云端冷启动需显式配置插件、仓库、凭证和版本来源，不能依赖本机缓存；发布证据需记录可变 SNAPSHOT 的确切制品摘要。
- 测试有 H2、Redis 及隔离 RabbitMQ/Testcontainers 等依赖。按测试 selector 划分纯单测与集成测试，在云端使用隔离服务/容器；不能连接生产数据库跑测试，也不能以 `-x test` 代替既有质量门禁。云端执行机的容器能力/网络可达性需首轮验证。
- 旧流水线下载到 `/home/isp/hosts/cyf/api/package.tgz`，以 root 执行 `/home/isp/bin/cyf_api_kit_start.sh`。该脚本现为生命周期入口的兼容转发，不能视为制品安装；`/home/isp/bin` 为 isp 可写路径，不能作为 root 自动化信任边界。
- 当前安全运行位置是 `/opt/cyf/service/api`，运行用户 `cyf-api`，运行记录 `/run/cyf-api`，root-owned 生命周期命令 `/usr/local/sbin/cyf-api-kit` 只负责 start/restart/stop/status。需要独立的受限、可信制品安装入口，不能只把旧命令替换成 restart。
- `ops/release/build-api.sh` 已有 clean HEAD/tree 和不可变制品证据，但仍直接 flock 调 Gradle；应改为项目要求的 `ops/orchestration/cyf_orchestrator.py` 路径。`deploy-api.sh` 还假设 PID/log 位于 JAR workDir，不能原样套用 `/run/cyf-api` 新布局。
- `verify-release.sh` 同时绑定 API/Web checkout 和 release-input/tool 摘要。云端构建与主机部署分离时，需要明确多仓 SHA 清单、工具版本、路径映射和制品导入验证，避免要求生产主机重建源码。每台构建宿主串行 Gradle；跨主机结果按 tree SHA + selector + fixture digest 导回唯一执行账本，不另建并行账本。

## 建议执行顺序

1. 固定前后端目标提交及流水线来源，保护本机未提交改动；只读核对自动触发规则，避免推送与手动触发重复运行。
2. 先准备后端“仅云端测试和构建、不可部署”的配置，独立审查后，在明确授权下运行一次冷缓存验证。Gradle、浏览器和隔离测试依赖都放云端；先保持每台执行机一个 Gradle。
3. 产出精确提交/tree、工具与依赖摘要、测试 selector/fixture、JAR SHA-256 和运行号绑定的制品及证据。
4. 适配 root-owned 制品安装、release 锁、运行身份、健康和业务 smoke；迁移/数据库审批与部署分开，不绕过现有门禁。先 dry-run / 隔离验收，生产执行另需明确授权。
5. 验收后调整项目构建约定：本机只做轻量静态检查与编排，正式测试/构建以云效同一提交证据为准；不在云端成功后又本地全量重建。

## 独立只读复核：当前部署方案不予放行

独立 Reviewer 确认技术路线可继续评估，但现有脚本不能作为安全迁移完成证据；实施时须补齐以下门禁，完成后重新独立验收：

1. **root 信任边界**：root 不仅不能执行 `/home/isp/bin` 脚本，也不能直接执行可写 workspace 下的 release 脚本或解包后的脚本。安装器及祖先目录需 root-owned；预期 SHA/Run/审批信息来自可信渠道，下载制品作为不可信数据，在 root-owned staging 拒绝链接/路径逃逸并校验后安装。
2. **生命周期与锁**：现有 deploy/rollback 保存 argv 后直接启动 Java，会绕过 canonical 工具的降权、环境装载和运行记录。两条路径都要改造；与 `/usr/local/sbin/cyf-api-kit` 对接还须遵守 release lock 的 FD8 继承协议，不能持锁后盲目调用 restart。
3. **联合 promotion**：保留 API/Web 联合 release tuple，明确聚合两个流水线的固定 Run/commit/tree/制品 SHA 的阶段；若改为组件级契约须另行审查。生产推进必须满足当前审批策略并绑定精确制品，不能重新拉移动中的 master。不得未经授权修改现有 push 自动部署规则。
4. **制品契约**：不能仅上传整个 libs 目录；需要唯一 SHA 命名 JAR、metadata、sidecar、可信 release record，显式附加 Flow Run ID 和测试 fixture digest，并通过 orchestrator 记录结果。
5. **Schema 门禁**：建立 exact-SHA migration inventory；获准访问生产后，只读预检 schema/digest，需 DDL 时独立审批并按先迁移后应用顺序执行。隔离测试通过但生产 schema 不兼容时禁止安装 JAR。

## 内存收益与边界

16:32 本机快照约 3724 MiB RAM、975 MiB available，swap 已用 958 MiB。这不是构建峰值测量。迁移后可避免本机承担 npm/Vite、Gradle/Javac、测试 JVM、Chrome 和隔离测试服务的构建测试开销；线上 Java/MySQL/Redis/Agent 的运行内存不会因此消失。具体节省量应比较迁移前后相同提交/测试负载的峰值 RSS 和 swap，当前不承诺固定 GB 数值。

相关入口：`docs/DEPLOYMENT.md`、`ops/release/build-api.sh`、`ops/release/deploy-api.sh`、`ops/release/verify-release.sh`、`ops/orchestration/cyf_orchestrator.py`。本记录是评估，不是部署批准或已完成迁移声明。

## 授权后执行进度（2026-09-09 19:08 +08）

已新建手动、无部署流水线5256653并实现受审ticket执行桥；两次真实Gradle均在云效北京云端执行，无本地构建或生产变更。Run1冷启动API参数问题已修复，Run2停在org.opencv:opencv:4.5.5依赖解析，业务测试及应用JAR未完成。按两次失败门禁停止，不能视为迁移验收通过。执行证据见`docs/implementation/handoffs/FLOW-CI-20260909-PHASE1.md`，当前阻塞及整改矩阵见`docs/implementation/handoffs/FLOW-CI-COLD-01-R2-ROOT-CAUSE.md`。

## 私仓线索修正与目标调整（2026-09-09）

认证核查确认原流水线1466118的release私仓可读取OpenCV4.5.5 POM（200）及JAR元数据（HEAD200）。新CI遗漏私仓与认证才导致Run2失败，不需要重新寻找/替换OpenCV。用户随后明确选择新流水线，当前复用5256653、不创建第三条且旧1466118/4403172不变。23:29认证流式GET完整OpenCV JAR（722802bytes）已取得SHA256；23:32创建专用加密变量组44254，两项均isEncrypted=true，尚未关联/触发。原Owner正在实施受审私仓认证整改；工具和精确新payload仍需独立复核。详见`docs/implementation/plans/FLOW-CI-20260909-R3-REMEDIATION.md`与同目录脱敏provenance/variable-group记录。

## R3 最终结果

用户提供控制台变量组ID `q37x7n8snxqq744z` 后，受审R3b配置更新及关联成功（API数值组44254）。Run3在云端完成Gradle构建（4分13秒、201任务）、bootJar和72项定向/必需verifier测试，OpenCV私仓实际JAR摘要核验通过；无本地真实构建。

流水线最终仍FAIL：构建后的新增制品秘密扫描触发递归资源上限，bridge70，未导出可交付JAR、未部署。尚不能区分累计1GiB与100000entries哪项触发，不能直接提高阈值或绕过。下一步仅有界非敏感诊断设计，另审修改/运行。完整证据及根因边界见`docs/implementation/handoffs/FLOW-CI-COLD-01-R3-RESULT.md`；历史失败记录保留。
