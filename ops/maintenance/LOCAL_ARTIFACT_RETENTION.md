# 本地构建包与产物自动保留（核对：2026-11-15）

## 当前策略（2026-11-15用户更新）

**可复用构建缓存保留；未登记的历史构建输出也自动清理，需要时重新构建。** 本节覆盖此前“只清理完成登记包”及低磁盘时清理构建缓存的口径。不从产物年龄推定任务完成，不改写任务ledger或发布回执。

### 自动触发与保留

- 复用每天北京时间 **03:15、13:15** 的 `cyf-host-cleanup.service` → `/home/isp/bin/clear_disk.sh clean`，不新增cron或收费Flow。构建包及明确中间输出清理独立于磁盘空闲量。
- 已登记包沿原 `completed-tasks.json`：完成满24小时、每组件最近两批、当前/回退/占用保护；明确退役声明仍只豁免时间与最近两批，不豁免安全保护。
- **未登记输出无需补登记或等待Owner宣告任务结束**。只在下述明确构建基目录发现；按同组件输出阶段最近修改时间保留最近两批，其余最后修改/状态变化满24小时才可回收。新文件、替换文件及新批次重新计时。此时间仅判断产物保留，不是任务完成事实。已登记路径不被重新解释成未登记输出，不绕过其既有保护。
- 两种来源的最近两批分别保守保留，当前/回退绑定额外保留；不会为了凑数量删除恢复输入。需要暂时保留某批可放置 `.keep`（含悬空链接）；开始复用已登记批次仍先 `mark-active`，正在运行的批次由构建/发布锁与进程占用保护，不能把撤销登记理解为未登记产物永久豁免。

### 未登记发现范围

- 仅 `/home/isp/state/cyf-build`、`/home/isp/state/cyf-local-build/tasks`、`/home/isp/state/cyf-local-build/artifacts`，最多 `<batch>/<attempt或component>` 两层阶段根。不扫描整个state、worktree、生产安装、备份或任意tmp目录。
- 阶段根必须有现有生产者文档 `result.json`、`manifest.json`、`release.json` 或 `build-evidence.json`；不要求其宣告任务完成。缺失/无法读取时保留，不把未知目录或测试fixture当构建输出。
- 最终包只识别阶段根或其 `package/`、`packages/`、`artifacts/` 下的 `api`、`web`、`runtime`（可带数字版本后缀）的 `.tar/.tgz/.tar.gz`。API包还须能识别 `application.jar`；未知命名、未知格式、坏包保留并报告，不对任意压缩包兜底删除。
- API中间输出只处理该阶段 `build/jia/**` 下 `classes`、`libs` 路径内的 `.class/.jar`，且须有可读取的源码身份。源码、报告、测试XML、依赖目录和其他输出不随之删除；不递归删除阶段目录。

### 缓存与证据

- **无论空闲空间多少，都不删除可复用Gradle缓存、NPM缓存、Web共享依赖、已登记node_modules以及Node/TSX编译缓存。** 旧参数保持CLI兼容，不再授权缓存回收；包清理不调用旧缓存候选逻辑，底层unlink也拒绝缓存行。
- 未登记包删除前，把包顶层JSON/XML/log/Markdown及 `test-results/`、`evidence/`、`reports/` 文档按原字节保存到 `/home/isp/state/cyf-host-cleanup/retained-artifact-evidence/<package-sha256>/`，索引绑定原包路径、摘要、内部文档名与摘要。只流式读取，不按压缩包路径解压。单文档16MiB/总64MiB的读取保护沿本次受控证据保存约束，超限保留原包、不丢弃证据。
- 原有包外日志、测试、receipt/metadata/manifest、源码、状态和备份全部保留。已登记包仍由Owner在登记前保存唯一证据。未登记包解析/证据保存/核验失败就保留。

### 当前/回退与并发保护

- 原host清理锁、API coordinator/release、Web deploy、Runtime release锁不变；增加获取已有Gradle与orchestrator构建锁，全部非阻塞，不创建替代锁、不终止别人的任务。缺失/忙/不安全则跳过本轮构建输出。沿用既有50文件审计批次，每批结束释放构建锁并让出调度；若构建接手，不等待或抢回，余下产物留给下一次定时清理。逐文件占用/摘要/身份核验不减，避免成千class的小额回收长期阻塞后续构建。
- 只读读取权威发布记录及Runtime前一批记录；源码commit/tree、外层包摘要、API实际application JAR摘要、显式路径引用与当前/回退绑定匹配时保护。未知/未确认发布状态保护相应组件，不伪造验收状态。
- 删除前复核文件/阶段身份、SHA-256、源码文档身份及完整进程快照；`.keep`、挂载、符号链接、外部硬链接、在用文件/阶段均保护。预删除审计仍用 `/home/isp/baks/host-cleanup/rebuildable-cache/audit.jsonl`。
- 数据库、生产程序、运行身份/会话、备份、源码、证据不是“可以重新构建”的输出，不在新增发现范围。

## 兼容入口与只读预案

`rebuildable_cache_cleanup.py plan --artifacts-only` 输出精确候选，无删除、无证据写入。`clean` 与 `clean --artifacts-only` 均只消费登记包及上述发现输出，不清缓存、不等待低磁盘。

既有 `mark-complete` / `mark-active` / `--retirement-reason` 保留兼容；完成登记不再是上述未登记发现范围的回收前置条件，不另建完成台账。`--node-modules` 的历史声明可读取，但不再触发依赖删除。

## 本轮实施与验收

已通过108项独立Python用例与88项Shell用例，并将候选安装到现有主机入口、逐文件回读摘要一致；原03:15/13:15计划不变。规则、源码、隔离测试、主机安装回读和真实执行分别记录。本轮私有证据目录为 `/home/isp/state/cyf-git-cleanup-20261115/automatic-output-retention/`；最终安装回执为其中 `lock-yield/installation.json`；后台实跑状态及回收量独立记录，不将启动或中止的执行重标为完整成功。此前回收41包、6.614GiB是上一轮结果，不冒充新增发现的收益。旧Flow缺失回退JAR及Runtime备份待验收可能仍令整个service报警；不绕过这些独立阶段的保护。

## 历史验证与目录变更（不覆盖上述当前策略）

## 回归与实施状态

隔离回归入口 `python3 -B ops/maintenance/tests/test_rebuildable_cache_cleanup.py`，覆盖旧依赖清理、本地最终包、每组件最近两批、当前/回退绑定、24h、busy/missing lock、未知记录、复用/身份变化、完整进程扫描、plan零删除、幂等和仅登记文件删除。只用临时 fixture，不删历史包。

源码基线：根 `136e0682c6436f7ad3122dfd9a5fffee7698c82e`；本次实际修改以 handoff 的文件 SHA-256 为准，不把未提交维护工具冒充该 commit 内的字节。主机安装/回读、自动任务是否实际消费及下一次真实发布600秒结果分别记在 `docs/implementation/handoffs/LOCAL-BUILD-RETENTION-10M-20261106.md`。旧本地准入仍已退役，见同目录 `ADMISSION_RETENTION.md`，本功能不恢复它。

2026-11-07补记：现行API schema4 LOCAL由原coordinator原生校验器确认，Web schema2 LOCAL由原Web helper及私有备份descriptor确认；保留旧Flow支持，未知schema仍fail-closed。安装文件摘要、注册与真实入口记录已保存。上述“源码基线”是历史起点，不代表本轮工具字节已存在于该旧commit。

## 2026-11-07目录归位更新

完成包显式基目录增加`/home/isp/pkgs/cyf`、`/home/isp/state/cyf-local-build/tasks`，移除`/home/isp/wsps/private-maintenance`；现有共享worktrees仅作历史兼容，不作为新工作树默认根。三个镜像的登记路径已随原子迁移更新，完成时间/摘要/身份不变。baks/private-maintenance是历史维护档案，不纳入最终包扫描。此为目录整理，不改变24h/最近两批/当前回退/进程/锁保护。详见`HOST_DIRECTORY_LAYOUT.md`。

## 后台调度优先级（2026-11-13）

完整主机入口 `clear_disk.host.sh` 在取得原cleanup锁后、启动任何清理阶段前，仅降低自身及后续子进程的CPU优先级（nice19）和I/O优先级（idle）。原因是两核主机低于既有5GiB触发线时，半小时清理会与构建及服务争用CPU。设置失败返回4，不伪报成功或继续高优先级扫描。目录/保留期限/身份/状态/摘要/全部锁及5→8GiB回收规则均不变，不扫描或修改其他进程优先级，不中止在途清理。繁忙主机上的回收会更慢；这是后台维护让出资源，不是磁盘空间充足或任意构建必在600秒内结束的保证。最小兼容入口与cron计划本次不变。

验证：`bash ops/maintenance/tests/test_clear_disk.sh ops/maintenance/clear_disk.host.sh`（仅隔离fixture）。主机安装与单独子进程优先级回读见 `RUNTIME-LEASE-SEPARATION-20261112` handoff；不能把对新入口的验证当作已改变旧进程。

本轮实测（2026-11-15）：现有service入口回收41份包、7,101,808,640字节（6.614GiB），根盘已用44.746GiB；1份API包因回退绑定保留，294份包外证据/当前文件摘要一致。定向及相邻维护回归245项Python、87项Shell通过，主机Python3.6兼容回归81项通过。包阶段再次执行为0删除；旧回退缺失及Runtime备份待验收保护令整项service仍返回4，不将其报告为全阶段成功。实际回读和日志见上述私有证据目录。
