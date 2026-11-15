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

## 2026-11-15：构建包自动回收补齐

`state`保存构建状态、证据及工作缓存，构建输出包出现在任务批次目录是正常的，但不是永久归档/备份。已完成/明确退役的精确最终包通过同一 `completed-tasks.json` 登记；现有每天两次服务入口对登记包执行独立于空闲空间的保留清理。只扩展明确构建基目录及一个批次子层，不扫描整个state。详细规则、退役例外和保护见 [本地包保留说明](LOCAL_ARTIFACT_RETENTION.md)。源码、日志、测试/回执、生产数据及当前/回退绑定不随之删除；未知任务仍待Owner确认。

## 2026-11-15后续：未登记输出发现与缓存保留

用户要求已落实到本次候选：可复用构建/依赖/Node编译缓存不参与自动清理，即使低磁盘；既有每天两次入口发现三个明确构建base的未登记最终包与API class/JAR，按24小时及每组件最近两批阶段保留，当前/回退/锁/占用与证据保存不变。不从年龄推断任务完成，不自动登记或删除整个目录。本文前一节“未知历史目录不扫描”改为责任范围内按精确模式发现，范围和实施回执见 [现行保留策略](LOCAL_ARTIFACT_RETENTION.md)。

## 2026-11-15：本实例MySQL错误日志自动轮转

核对范围：本机 `/home/isp/apps/mysql` 实例，修改前源码基线 `f3d0364e7062f1b0338bb8b4b86e397cf95787c8`。不覆盖其他主机或数据库；安装字节摘要、实际执行及恢复信息保存在 `/home/isp/state/cyf-git-cleanup-20261115/mysql-logrotate-fix/`，不把规则文本当安装证明。

- 原厂 `/etc/logrotate.d/mysqld` 只管理 `/var/log/mysql/mysqld.log`，不覆盖本实例实际 `/home/isp/logs/mysql.log`；旧路径仍有空文件，保留原厂规则不改。新增本实例 `/etc/logrotate.d/cyf-mysql`，仓库模板为 `mysql-error-log.logrotate`，沿既有 cron.daily/anacron 自动入口执行，不新增cron。每天轮转、保留5份（沿原规则数量）、gzip并延迟一个周期压缩，创建文件保持mysql:mysql、0640；不用copytruncate，不丢失轮转中的写入。
- `/usr/local/libexec/cyf/mysql_error_log_reopen.py` 对应本目录同名源码。轮转前核对PID文件、实际mysqld可执行文件/身份/配置、mysql.service进程组及当前日志FD。主机服务MainPID是mysqld_safe包装进程，**不能向它发送信号**。仅向已核实的实际MySQL 8.0.19+服务进程发送SIGUSR1，重开文本日志，不使用SIGHUP或会同时轮转binlog的flush-logs。无需SQL凭据、服务重启或更改数据库保留策略。
- 重开后最多等待5秒核对同一进程/starttime已经打开新日志；这只是logrotate操作回执等待，不是数据库请求deadline。未知版本、进程变化、日志身份/FD异常即失败；延迟压缩使本次原件仍可恢复，下一次prerotate未确认写入当前文件则拒绝继续轮转/压缩。
- 本机已安装回读并通过全局logrotate debug；实际定向轮转及最终helper重开均成功，服务PID/starttime不变，无重启。首次原件在确认无进程占用后单独无损压缩，解压SHA-256一致；后续自动执行沿delaycompress，不将这次人工验证压缩宣称为额外常驻策略。
- 回归：`python3 -B ops/maintenance/tests/test_mysql_error_log_reopen.py`（8项隔离单测）；真实logrotate隔离fixture分别覆盖成功轮转、prerotate失败保留当前文件、postrotate失败保留未压缩原件（3种场景）。本轮未执行应用构建、部署、SQL记录清理或binlog purge。
- 配置恢复：如需停用新增轮转，移除本任务新增的 `/etc/logrotate.d/cyf-mysql` 即可，原厂规则与数据库配置未改。已轮转文件保留原字节，当前新日志继续写入；不要用旧日志覆盖当前文件或重置共享logrotate状态。恢复/暂停配置不意味着已撤销历史轮转事实。

## 2026-11-15：数据库审计日志7天保留

范围仅本机 `jia.core_log`，源码基线 `678c3d45fc8b80321f8bd3ef3f146fb3cf16c264`；不清理其他业务表。安装模板为 [mysql-audit-retention.sql](mysql-audit-retention.sql)，验证入口为 `python3 -B ops/maintenance/tests/test_mysql_audit_retention.py`（真实隔离MySQL、私有socket，9项通过，不接触生产表）。

- 本机已安装存储过程和同名事件 `jia.cyf_core_log_retention_7d`。事件每天执行一次，按执行时刻减7天清理 Unix 毫秒 `create_time`；首次定时计划为北京时间 **2026-11-16 14:24:17**，不是主机03:15/13:15构建清理任务。日周期意味着记录到期后可能等待下次执行，不承诺精确到期即删。调度器运行时ON，来源为编译默认值（COMPILED），不修改全局配置或重启数据库；首次人工调用不等于已经验证未来定时触发。
- 按主键每5000个实际ID分窗口、独立autocommit连接执行，固定本轮最大ID；使用非阻塞命名锁，冲突报错且不抢锁，异常释放自己的锁。保持binlog和原复制设置，不加索引、不重建表。调用可传更早阈值/更小ID上限以绑定备份，不能缩短7天保留。
- `create_time IS NULL`、非正时间无法判断年龄，不从ID猜时间，继续保留。本次盘点有 **68,465条NULL时间记录**；因此不能宣称表中每条记录都能证明不超过7天。其他业务数据不随审计日志清理。
- 首次人工清理限定 `id <= 7787012 AND create_time > 0 AND create_time < 1794118484975`（北京时间2026-11-08 14:14:44.975以前）。首次已删除 **6,443,799条**，耗时937.79秒（数据库维护，不是应用构建发布）；同一备份范围内过期记录为0，保留837,230条近期记录及68,465条NULL时间记录，新审计继续产生、维护锁已释放。执行回执、安装对象、校验及测试在 `/home/isp/state/cyf-git-cleanup-20261115/audit-retention-7d/`（`FINAL.json`、`verification.tsv`）。首次删除前已用一致性快照备份该精确范围，gzip完整性及SHA-256通过。
- 首次回滚备份 `expired-before-20261108T141444975.sql.gz` 约195MiB，目录0700、文件0600，SHA-256为 `e89bbc7c9c93abb9d862397735703e78a873d7462d2df035f8dc38e825a0d2f5`。**此备份含7天以前审计内容，暂不自动删除**；不是日常清理每次再备份。需恢复时先校验摘要并在隔离库恢复、核验列和ID，再经授权受控合并，不将SQL直接导回生产覆盖当前记录。暂停未来清理可 `ALTER EVENT jia.cyf_core_log_retention_7d DISABLE`，不关闭全局调度器、不影响其他事件；暂停不会撤销已发生删除。
- InnoDB删除仅提供表内可复用空间，不保证`.ibd`立即缩小；本次未执行OPTIMIZE/重建/删除数据库文件，表文件仍为4,777,312,256字节。实际删除过程中恢复日志增长，根盘已用从约46.78GiB升至50.18GiB、可用约8.68GiB，未达到45GiB目标，不将逻辑删除说成磁盘已回收。binlog当前自动保留3天（259200秒），与审计表7天不同；备份、binlog等恢复副本不承诺同步物理抹除。

### 非业务内容的自动清理边界（同日定向盘点）

以下是未纳入普通过期清理的内容，不等于全部获准删除：

| 内容 | 当次占用 | 边界 |
| --- | ---: | --- |
| 教学录屏（原始及剪辑成品） | 本次已清理，见下节 | 2026-11-15用户确认不再需要；后续新录屏仍未设自动过期，不因本次授权全局扫描删除 |
| `state/cyf-diagnostics`日志、trace及诊断证据 | 648MiB | 无统一自动过期策略，不能整目录当垃圾删除 |
| `/var/log/cyf-api-flow`历史API启动日志 | 165MiB | 现有logrotate及主机日志清理未覆盖，是日志轮转盲区，本次未扩改 |
| `state/cyf-test-tmp`测试fixture | 8.9MiB | 不在通用临时目录扫描范围，按任务归属确认 |
| 各任务日志、receipt、测试XML、清理追溯、非Runtime维护备份 | 未汇总 | 保留验收与恢复凭据，不实行全state/baks按年龄删除 |
| 本次审计首次回滚备份 | 约195MiB | 私有恢复副本，暂不自动删除 |
| Gradle/NPM/Web依赖、node_modules、Node编译缓存 | 本次不重复汇总 | 用户明确保留可复用缓存，属于有意排除而非漏管 |

不要混淆三类：①上述确实范围外或明确保留；②已纳管但因当前/回退绑定、最近两批、24小时、占用/锁、身份/证据不全而保护跳过（例如`state/cyf-build/lease-int5`）；③通用临时及轮转日志已有规则，但仅空闲低于5GiB才触发、清到8GiB，当前不触发。MySQL错误日志、3天binlog与每天两次历史构建输出均已有各自自动策略，不列为无规则盲区。生产身份、授权、会话及运行状态不能因为位于state而视作非业务垃圾。


## 2026-11-15后续：按用户授权删除教学录屏

用户明确“录屏可以不要了”后，只清理本次教学任务的原始WebM、剪辑/成品MP4、下载补录及失败尝试视频，不删除整批目录。范围为 `/home/isp/state/` 下三个 `cyf-tutorial-recording-20261112{,-batch02,-batch03}`、`cyf-tutorial-download-completion-20261112` 和 `cyf-tutorial-review-20261113`。补录与交付目录的全部关联硬链接已在范围内核齐，无外部硬链接、`.keep`、挂载或视频FD占用；未触碰 `cyf-tutorial-unblock-20261112` 的Runtime包、源码及安装状态。

- 删除122个视频路径（88个唯一inode），按唯一inode回收1,372,782,592字节，约1.278GiB；删除后五个限定目录内无上述视频。没有另存视频备份，否则无法兑现丢弃录屏及回收空间的要求。
- 其余1,241个普通文件逐项SHA-256及身份核验不变：脚本、说明、验收/日志、输入图片、PDF/PPTX/Excel等交付资料和依赖缓存保留。没有删除其他业务数据或改变后续录屏的自动保留策略。
- 私有删除清单、删除前摘要和验收在 `/home/isp/state/cyf-git-cleanup-20261115/tutorial-video-removal/{plan.json,deleted.jsonl,FINAL.json}`。根盘可用实测增加约1.277GiB（差额含同期系统写入）；当次已用约48.92GiB、可用9.95GiB，仍未达到45GiB目标。
