# Flow 主机资源与磁盘清理

更新：2026-09-13。默认正式构建、测试在云效，本机仅安装制品；不恢复本地 Gradle/Vite 构建。

## 已发现的问题与调整依据

- 云端读取确认：后端 `5260799 / cyf-api-release`、前端 `4403172 / cyf-web-release` 的构建任务均为 `public/cn-beijing`。
- 10:10–10:13 CST 本机约 3.64 GiB 内存，可用约 1.5–1.6 GiB；没有 Gradle 进程。根盘约 50 GiB，空闲约 5.5 GiB。没有同条件迁移前监控，不能量化整机降幅或硬盘寿命。
- 旧 `/home/isp/bin/clear_disk.sh` 为凑足固定 10/11 GiB 空闲，扫描所有工作树、临时目录、历史发布和归档会话。10:05:26–10:06:41 一轮约 75 秒，Gradle 阶段约 64 秒，几乎未回收空间。
- 新 Flow 数据不在旧清理范围：检查时后端备份约 1.44 GiB、incoming 约 190 MiB、前端下载约 298 MiB。
- 实际发现两个后端备份字节完全相同。**备份文件名包含的是候选 JAR 摘要，不是备份内容摘要**，不能按文件名去重。流式逐字节比对和 SHA-256 才是本次去重依据。

## 已启用的最小清理范围

只去重 `/var/lib/cyf-api-flow/backups` 中符合安装器命名格式、owner/权限正确、无符号链接且单硬链接的普通 JAR：

1. 按清理锁 → 后端 Flow 协调锁 → 后端发布锁的既有顺序等待；不超时判败、不抢占、不操作其他任务进程。
2. 读取当前部署状态，必须为 `installed / not_required`；缺失、不完整或恢复中的状态保留全部文件。
3. 永久排除当前 `record.json.backup` 引用文件；每种不同内容至少保留一份。年龄、文件名摘要和空闲容量不是删除依据。
4. 同大小文件先流式比较实际字节；删除前重新核对状态、文件身份、内容和打开的文件描述符。只检查 `/proc` 链接，不读取其他任务数据。
5. 先持久化删除意图，再删除一个精确文件、fsync，并记录保留副本路径和摘要。审计不可写则不执行该次删除。

不清理：不同版本备份、API incoming/downloads、任何前端下载/线上资源、工作树、构建/依赖缓存、`/tmp`、`/var/tmp`、证据、数据库、Codex 历史。一般日志轮转另行管理。

没有空闲磁盘目标、按年龄扩大扫描、包大小限额或硬编码保留版本数。历史不同版本如需淘汰，应另行确定恢复需求及云端制品可取回证据；本次不凭日期推断可删。

## 入口与部署

- 维护源：`/home/isp/wsps/cyf/ops/maintenance/flow_host_cleanup.py`、`/home/isp/wsps/cyf/ops/maintenance/clear_disk.sh`。
- 安装：`/usr/local/libexec/cyf/flow_host_cleanup.py`，兼容入口 `/home/isp/bin/clear_disk.sh`。
- `/etc/crontab` 原每 30 分钟的调用保持不变；新脚本已经替换入口，不再运行旧扫描逻辑。
- 前值备份：`/var/lib/cyf-flow-cleanup/clear_disk.before-20260913.sh`；安装校验：同目录 `installation.json`。
- 删除意图/结果以及清理失败：`/var/lib/cyf-flow-cleanup/audit.jsonl`。无候选不追加日志。

```bash
# 只读容量元数据，不递归扫描工作树
/home/isp/bin/clear_disk.sh check
# 只读待删清单及预计回收字节；会等待发布锁
/home/isp/bin/clear_disk.sh plan
# 持锁重新生成计划、核对后仅删除字节相同的冗余备份
/home/isp/bin/clear_disk.sh clean
```

`check-deep` 保留为兼容别名，现在与 `check` 一样只看固定 Flow 目录。旧 `MIN_FREE_GB`、`RECOVERY_FREE_GB`、年龄等环境参数不再控制删除。

## 本次验证与执行

- 26 项隔离临时目录单测通过，覆盖 pin 保留、同大小不同内容、链接/权限、锁顺序、状态变更、打开文件、审计失败、未知证据和 Web 文件保留。
- shell 静态检查和安装源/readback SHA-256 一致；未运行本地 Gradle/Vite、未触发 Flow 或重启服务。
- 本机首次 dry-run：14.90 秒、最大 RSS 17,920 KiB；确认一个可删除重复文件。
- 按同一规则执行：删除一份逻辑大小 `220206485` 字节、占用 `220213248` 字节（约 210 MiB）的重复 JAR；保留副本 SHA-256 `aa64ddf1be41147156236aa3d4f70121e2b95918d8dd2024d0cd3d0fec4df090`。不是当前 Run36 恢复副本。
- 清理后复查：0 候选，0.06 秒，最大 RSS 14,064 KiB；这次是无重复的元数据检查，不能承诺所有未来清理都同样耗时。
- 空闲约 5.7 GiB（全盘读数还受其他进程写入影响）；后端 loopback `/actuator/health` 返回 `UP`。

复验：

```bash
python3 -B -m unittest discover -s /home/isp/wsps/cyf/ops/maintenance/tests -v
bash -n /home/isp/wsps/cyf/ops/maintenance/clear_disk.sh
```

这些是控制面隔离测试，不替代应用发布所需的云端测试。

## 工作树专项核对

2026-09-13 首轮只读核对见 `docs/aliyun-flow-worktree-cleanup-audit-20260913.md`：103 个工作树中首批筛出 8 项约 854 MiB。经用户确认，12:36 CST 实际移除 7 项，目录原占用 869773312 字节（约 829.48 MiB）；保留分支、提交和真实共享依赖。`h06-r48-api-concurrency` 仍被 12 个 systemd 服务配置引用，已跳过且未操作服务。

12:38 CST 根盘复查可用约 5.2 GiB、使用率 90%，全盘读数包含其他任务并发写入。后端 loopback 12:38 为 `UP`，随后连接被拒绝；12:41:26 的只读核对显示 10018 无监听，部署记录为 `activating / activation / ready`，需发布责任方核验激活结果，不能沿用先前 `UP` 作为当前健康结论。本任务没有执行发布或操作服务。

实际执行记录见 `/home/isp/wsps/cyf/docs/aliyun-flow-worktree-cleanup-execution-20260913.json`。工作树删除仍不纳入定时清理。


## 2026-09-17 用户授权的一次性深度清理

本次用户明确扩大范围后，另执行一次人工清理：29个已完成worktree、10个旧Flow备份JAR与2个旧下载包，合计约5.68GiB分配块。保留当前记录引用的恢复副本、源码分支、脏/未合/共享工作树及线上文件。详见`docs/implementation/DISK_DEEP_CLEANUP_20260917.md`。未变更上述定时入口和默认去重规则，未删除云端源制品。
