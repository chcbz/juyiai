# 本地最终包的受控保留（2026-11-06）

> 当前状态（2026-11-07）：已安装并回读现有清理器、LOCAL记录适配及artifact登记；4个已完成任务已登记，原30分钟cron入口已真实消费。维护回归253项通过。实际入口退出3仅因根盘约1GiB仍低于5GiB，无可合法继续删除候选；未改写安装record或强删受保护数据。详细证据见 `docs/implementation/evidence/local-release-closure-20261107/`。

## 责任与范围

- 根 AGENTS 本地执行新规则下，清理仍由主机存储适配器执行。扩展现有 `rebuildable_cache_cleanup.py` 的 `mark-complete` / `mark-active`、现有 `/home/isp/state/cyf-host-cleanup/completed-tasks.json`，不是新台账、审批或发布通道。
- 只清理 Owner 已确认任务完成/终止、无需继续持有的**明确最终输出**。任务根沿用 `/tmp/cyf-*`、`/var/tmp/cyf-*` 及原显式 worktree bases，也支持同一显式base下`cyf-BATCH/{api,web,runtime}`的精确组件子根（逐级身份/挂载/.keep检查，不允许任意嵌套）；路径只能是任务根直接文件或 `package/`、`packages/`、`artifacts/` 下最多两层的 `.jar/.tar/.tgz/.tar.gz/.zip`。不递归猜测 source/build/state/backups/recovery/evidence，不扫描未知历史目录；deliverables/releases 仍不做通用兜底删除。
- 完成声明复用既有 root Owner 控制面，不是包内字段自动授予清理权限。登记绑定组件、完整 commit/tree、文件签名/SHA-256；API 还须声明**实际 application JAR SHA-256**，用于匹配 current record 的 candidate/previous 回退摘要。Owner 从同批生产者证据取得该值，不能填压缩包摘要冒充 JAR 摘要。工具不重做构建真实性/发布审批。
- Owner 登记前须把同批日志、测试、receipt/metadata/manifest 等追溯材料保存在包外；若包内仍有唯一证据副本，先按原格式受控保存并核对摘要，否则不登记。工具信任已有 Owner 完成声明，不另建证据准入框架。
- 最新两个已登记构建批次**按组件分别保留**；沿用24小时完成保留期。当前记录绑定的 commit/tree、包摘要、API payload/回退摘要、Runtime 当前 backup/current.json 中前一版本源码/包绑定、显式路径引用额外保留；`.keep`（含悬空链接）、挂载、符号链接、外部硬链接、文件/任务替换、当前状态不明和进程使用均保护。只 unlink 精确登记文件，全部目录、日志、测试/receipt/manifest证据保持。
- 重新使用已完成目录前 `mark-active --task-root <真实目录>`；不复用已被回收的包/目录或靠 mtime 重新认领新文件。缺失旧文件为幂等跳过，替换的同名文件不会被自动采纳。

## 自动触发与发布互斥

- 继续现有 `/etc/crontab` 每30分钟 `/home/isp/bin/clear_disk.sh clean`，不新增计划任务。该阶段沿用可用空间低于5GiB触发、回收到8GiB停止；空间充足只保留/观测，并不保证固定年龄就删除。
- 复用 host cleanup lock；涉及登记包时还按现有次序非阻塞获取 API coordinator→release、Web deploy 或 Runtime release lock，不创建/改写锁。任一缺失/忙/元数据不符时保护**全部登记包**，独立缓存清理仍可执行；不取消别人的发布。
- 只读读取各组件现行权威发布记录；API 必须 installed/not_required，Web online_verified，Runtime verified-active，且有已知源码字段。未知新记录格式先保护包，等责任层明确适配，不猜测语义。此读取不代表重新验证持续线上健康。
- 每次 unlink 前复核登记/当前记录、完整进程扫描、路径/文件身份及 SHA-256。复用现有预删除审计 `/home/isp/baks/host-cleanup/rebuildable-cache/audit.jsonl` 和全局清理日志。错误停止/跳过，不递归删除目录、不碰数据库、生产程序或备份。

## Owner 完成登记

以下占位符必须使用本任务真实值；并非要求每项任务都新建目录：

```bash
/usr/bin/python3 -I -B /usr/local/libexec/cyf/rebuildable_cache_cleanup.py mark-complete \
  --task-root /var/tmp/cyf-REAL_TASK_BATCH \
  --artifact package/REAL_PACKAGE.tgz --component api \
  --source-commit FULL_40_HEX_COMMIT --source-tree FULL_40_HEX_TREE \
  --payload-sha256 ACTUAL_APPLICATION_JAR_64_HEX_SHA256
```

Web/Runtime 使用对应 component，不需 API payload 参数；可同时用既有 `--node-modules web/node_modules` 登记依赖目录。只有有已知最终包且任务已结束才登记；不为无包任务添加步骤。未识别/待恢复任务保持不登记。

只读预案：`/usr/bin/python3 -I -B /usr/local/libexec/cyf/rebuildable_cache_cleanup.py plan`。不以 `clean` 作为探测。

## 回归与实施状态

隔离回归入口 `python3 -B ops/maintenance/tests/test_rebuildable_cache_cleanup.py`，覆盖旧依赖清理、本地最终包、每组件最近两批、当前/回退绑定、24h、busy/missing lock、未知记录、复用/身份变化、完整进程扫描、plan零删除、幂等和仅登记文件删除。只用临时 fixture，不删历史包。

源码基线：根 `136e0682c6436f7ad3122dfd9a5fffee7698c82e`；本次实际修改以 handoff 的文件 SHA-256 为准，不把未提交维护工具冒充该 commit 内的字节。主机安装/回读、自动任务是否实际消费及下一次真实发布600秒结果分别记在 `docs/implementation/handoffs/LOCAL-BUILD-RETENTION-10M-20261106.md`。旧本地准入仍已退役，见同目录 `ADMISSION_RETENTION.md`，本功能不恢复它。

2026-11-07补记：现行API schema4 LOCAL由原coordinator原生校验器确认，Web schema2 LOCAL由原Web helper及私有备份descriptor确认；保留旧Flow支持，未知schema仍fail-closed。安装文件摘要、注册与真实入口记录已保存。上述“源码基线”是历史起点，不代表本轮工具字节已存在于该旧commit。

## 2026-11-07目录归位更新

完成包显式基目录增加`/home/isp/pkgs/cyf`、`/home/isp/state/cyf-local-build/tasks`，移除`/home/isp/wsps/private-maintenance`；现有共享worktrees仅作历史兼容，不作为新工作树默认根。三个镜像的登记路径已随原子迁移更新，完成时间/摘要/身份不变。baks/private-maintenance是历史维护档案，不纳入最终包扫描。此为目录整理，不改变24h/最近两批/当前回退/进程/锁保护。详见`HOST_DIRECTORY_LAYOUT.md`。

## 后台调度优先级（2026-11-13）

完整主机入口 `clear_disk.host.sh` 在取得原cleanup锁后、启动任何清理阶段前，仅降低自身及后续子进程的CPU优先级（nice19）和I/O优先级（idle）。原因是两核主机低于既有5GiB触发线时，半小时清理会与构建及服务争用CPU。设置失败返回4，不伪报成功或继续高优先级扫描。目录/保留期限/身份/状态/摘要/全部锁及5→8GiB回收规则均不变，不扫描或修改其他进程优先级，不中止在途清理。繁忙主机上的回收会更慢；这是后台维护让出资源，不是磁盘空间充足或任意构建必在600秒内结束的保证。最小兼容入口与cron计划本次不变。

验证：`bash ops/maintenance/tests/test_clear_disk.sh ops/maintenance/clear_disk.host.sh`（仅隔离fixture）。主机安装与单独子进程优先级回读见 `RUNTIME-LEASE-SEPARATION-20261112` handoff；不能把对新入口的验证当作已改变旧进程。
