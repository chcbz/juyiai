# 主机目录职责与本地发布目录（2026-11-07）

主机权威说明：`/home/isp/docs/SERVER_ARCHITECTURE.md`。以下同步当前本任务目录整理事实；历史证据不做路径字符串回写。

## 2026-11-07：本地构建与开发目录职责归位

- `apps`放工具链：构建JDK为`/home/isp/apps/dragonwell-21.0.11.0.11+10-GA`，生产Temurin不变。
- `pkgs`放安装包归档：API当前/回退及Web当前镜像已移至`/home/isp/pkgs/cyf/cyf-local-archive-20261107-{api-current,api-rollback,web-current}/package/`。不把包或备份放入开发目录。
- `state`放构建状态及缓存：`/home/isp/state/cyf-local-build/gradle-home`；后续临时构建任务使用`/home/isp/state/cyf-local-build/tasks/cyf-BATCH`，最终归档放pkgs，不将构建目录当永久备份。
- `baks`放历史维护备份及证据：旧`/home/isp/wsps/private-maintenance`剩余13个历史任务已原子迁至`/home/isp/baks/private-maintenance`；2094项原文件/目录的字节、权限、所有者及inode完整核对，无载荷复制、删除或服务重启。旧wsps入口不留软链接。
- `wsps`只放项目源码和开发工作副本。后续新增工作树按所属项目放在`<项目>/.worktrees/`，不再创建共享的顶层`worktrees`、`cyf-worktrees`或用于运维归档的`private-maintenance`。工作树用于隔离分支、不是独立服务，也不需要两个不同名称的顶层目录。
- `/home/isp/wsps/cyf-worktrees`为空且无占用、挂载，已删除。`/home/isp/wsps/worktrees`仍有15个任务目录（12个Git工作树，另3个任务目录），涉及CYF根/API/Web及isp-install，不属于同一个仓库。现有任务未移动、删除或重登记；后续由各Owner确认任务状态后通过Git机制逐项收口，不以目录年龄批量清理。旧共享路径仅保留兼容，禁止继续扩张。
- 完成包登记的3条镜像路径已迁到pkgs，保留原完成时间、源码、摘要和inode；原4条台账记录数不变。现有清理器增加精确pkgs/build-task bases并移除旧private-maintenance base；当前/回退、最近两批、24h、锁和进程使用保护不变。baks下的维护档案不进入最终包清理范围。
- 历史安装record与历史archive.json路径原文保留，不伪造重绑定；原当前/回退内存盘包仍保留。迁移映射、摘要与验证见`/home/isp/wsps/cyf/docs/implementation/evidence/local-release-closure-20261107/directory-layout-migration.json`。不把目录整理当成新的构建或发布。

## 2026-11-13：自动清理执行入口与CPU预算

- 主机cron每天北京时间03:15、13:15调用 `systemctl start --no-block cyf-host-cleanup.service`，不直接执行清理脚本。service仍运行原 `/home/isp/bin/clear_disk.sh clean`，保留所有锁、范围、保护及日志；同一service不并行重入。
- 同目录的 `cyf-host-cleanup.service` 与 `system-cyfcleanup.slice` 是主机 `/etc/systemd/system/` 安装单元的精确镜像。独立slice的 `CPUQuota=50%` 为整个清理树最多0.5vCPU，不是整机50%；`CPUShares=128`，service设nice19及idle IO。无需enable service，仍由既有cron触发。
- 本轮未将构建、测试、cron整体、root用户组或生产服务放入该资源组；直接手工调用脚本也不保证受此限额。既有在途清理经scope无中断纳管，不终止/重跑删除。
- 安装核验、回退与备份路径以主机架构文档同日章节为准。配额执行与业务提速分别验收，不以短时采样承诺延迟改善。

- 同日用户将频率从每30分钟调整为每天两次，cron表达式为 `15 3,13 * * *`，以主机Asia/Shanghai时区解释。时段按用户指定，不是实时空闲检测；半核预算、nice/idle IO、现有锁和保留策略不变。在途清理不被本次调整终止或重跑。
