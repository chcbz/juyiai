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



### 同日一次性在线整理（17:26—17:28，北京时间）

- 经用户明确授权，对本机 `jia.core_log` 执行 `ALTER TABLE jia.core_log FORCE, ALGORITHM=INPLACE, LOCK=NONE`；显式限定在线算法，避免静默退回阻塞写入的COPY方式。取得本表维护锁，元数据锁等待限定5秒（不限制整个维护耗时），不重启服务、不关闭binlog、不清空表、不删除数据库文件。重建83.102秒，含备份及验证全程156.954秒；执行源码基线 `2b2abf4ec02ae050ad9f1fdc8dc9f05ab049a87f`。
- 执行前为当前保留的整张表建立single-transaction备份 `retained-core-log.sql.gz`（55,607,945字节），gzip完整性及SHA-256验证通过；未宣称已做隔离恢复演练。备份及恢复说明、SQL、前后数据指纹和实际空间回执保存在 `/home/isp/state/cyf-git-cleanup-20261115/core-log-rebuild-172532/`，私有权限保存，暂不自动删除。恢复必须先隔离核验，禁止直接覆盖生产。
- 固定 `id <= 7834232` 的952,915条原有记录，重建前后有序逐行SHA-256聚合完全一致；NULL时间记录仍68,465条，期间及完成后新记录继续增长。维护连接退出后两把命名锁均已释放，七天保留事件仍ENABLED、首次运行仍未到期。未执行业务全链回归。
- 表文件从4,777,312,256字节降到767,557,632字节（约732MiB），按实际分配块释放4,009,951,232字节（约3.73GiB）。扣除备份及同期磁盘活动，根盘净增可用约3.68GiB，已用约47.15GiB，尚未达到45GiB。此次仅一次性整理，不新增定期缩表；七天自动删行策略不变。上节“未重建/未回收”为首次删行时的历史状态，不代表此次整理后的状态。

## 2026-11-15后续：按用户授权删除教学录屏

用户明确“录屏可以不要了”后，只清理本次教学任务的原始WebM、剪辑/成品MP4、下载补录及失败尝试视频，不删除整批目录。范围为 `/home/isp/state/` 下三个 `cyf-tutorial-recording-20261112{,-batch02,-batch03}`、`cyf-tutorial-download-completion-20261112` 和 `cyf-tutorial-review-20261113`。补录与交付目录的全部关联硬链接已在范围内核齐，无外部硬链接、`.keep`、挂载或视频FD占用；未触碰 `cyf-tutorial-unblock-20261112` 的Runtime包、源码及安装状态。

- 删除122个视频路径（88个唯一inode），按唯一inode回收1,372,782,592字节，约1.278GiB；删除后五个限定目录内无上述视频。没有另存视频备份，否则无法兑现丢弃录屏及回收空间的要求。
- 其余1,241个普通文件逐项SHA-256及身份核验不变：脚本、说明、验收/日志、输入图片、PDF/PPTX/Excel等交付资料和依赖缓存保留。没有删除其他业务数据或改变后续录屏的自动保留策略。
- 私有删除清单、删除前摘要和验收在 `/home/isp/state/cyf-git-cleanup-20261115/tutorial-video-removal/{plan.json,deleted.jsonl,FINAL.json}`。根盘可用实测增加约1.277GiB（差额含同期系统写入）；当次已用约48.92GiB、可用9.95GiB，仍未达到45GiB目标。

## 2026-11-15后续：优先清理项（用户授权）

- 限定删除197份API历史压缩日志、2份MySQL历史压缩日志、2份2026-10-27堆转储、废弃录屏专用FFmpeg二进制，以及已停用JUnit/4套测试fixture的数据库载荷。只删除已核验的819个普通文件及空数据目录；保留未压缩/活动日志、测试mysql.log、脚本及其他证据，不清空整个state/tmp/log目录。复用现有完整FD/cwd/exe/mmap快照，逐文件核验身份、摘要及占用，并检查.keep、挂载、链接与进程引用。
- 系统包缓存经 `dnf --cacheonly clean all` 成功清理（63项），不连接仓库、不卸载软件；不包含Gradle/NPM/node_modules/Node编译缓存。以上合计按分配块回收981,770,240字节，根盘净增可用976,707,584字节（约0.91GiB），当次已用约46.24GiB；未达到45GiB。
- 删除清单与摘要、系统缓存回执及空间/保护验证在 `/home/isp/state/cyf-git-cleanup-20261115/priority-cleanup-173534/`。819个删除路径复核均已不存在；两个审计回滚/整理备份SHA-256与原回执一致，clear_disk清理审计压缩日志全部保留，数据库新日志继续产生且七天事件仍ENABLED。
- 历史构建中间输出另外调用已安装 `rebuildable_cache_cleanup.py clean --artifacts-only`，沿原host/build/release锁、当前/回退及24h/最近两批保护执行；本节上述回收量**未计入该后台阶段**。最终输出见同证据目录 `build-output-clean.json`，空文件表示仍未收尾，应查询进程/退出日志而非宣称已完成。其他备份、诊断证据、其他项目和可复用构建缓存未扩清；未新增自动保留规则。

## 剩余清理候选（2026-11-15 17:47北京时间盘点）

本轮仅记录，不新增删除授权。根盘当次已用约46.24GiB，距45GiB尚约1.24GiB；活动任务会继续写入。下表是目录占用/候选上限，**不是全部可以回收，不能把父子目录重复相加**。原始盘点在 `state/cyf-git-cleanup-20261115/priority-cleanup-173534/remaining-inventory.json`（该相对路径基于 `/home/isp/`）。

### 可优先继续筛选（保留必要证据）

| 项目与完整路径 | 当前占用 | 可处理范围/条件 |
| --- | ---: | --- |
| `/home/isp/state/cyf-diagnostics` | 647MiB | 筛旧日志、trace、重复诊断输出；含依赖和唯一证据，不能整删 |
| `/home/isp/state/cyf-host-cleanup` | 240MiB | 压缩大JSON计划、去重复/失败预案；保留必要删除审计，不承诺释放240MiB |
| `/var/log/journal` | 192MiB | 可另行授权缩短保留/限容量，仅回收可退役的历史journal，活动部分保留 |
| `/var/tmp` | 135MiB | 逐任务核对旧fixture/临时文件；不整删源码或证据 |
| `/home/isp/state/cyf-native-skills-20261028` | 506MiB | 筛下载镜像和旧临时工具（此前发现Python源码压缩包约44MiB）；可复用依赖、源码/证据不动 |
| `/home/isp/state/juyiting-root-cause-20261109` | 149MiB | 筛临时Arthas等诊断工具，保留必要根因证据 |
| `/home/isp/state/cyf-git-cleanup-20261115` | 351MiB | 含下列两份备份共约248MiB，非备份材料约103MiB亦含清理追溯；只压缩/去重，不整删 |

### 需要先确认绑定、用途或Owner

| 项目 | 当前占用 | 处理前提 |
| --- | ---: | --- |
| `/home/isp/state/cyf-tutorial-unblock-20261112/attempt04/package/runtime-1.3.103.tgz` | 280MiB | 核对当前/回退绑定、占用和发布锁，必要证据先保存；所在批次目录共383MiB，不整删 |
| `/root/.codex` | 约1.01GiB | 历史库约715MiB、日志库约79MiB；含当前/其他会话，须专门核对归属、保留追溯及数据库安全整理，禁止直接rm SQLite/整个目录 |
| `/home/isp/apps/jdk8` | 357MiB | 排查全部服务与构建引用后再判断，当前不是已确认无用软件 |
| `/home/isp/pkgs/xray` | 16MiB | 确认旧安装包不再作为恢复输入；不是卸载在用代理 |
| `/tmp/banyishu-*` | 三个主要目录合计约440MiB，另有小文件 | 属其他项目，由对应Owner确认；CYF清理规则不授权删除 |
| 两份审计维护备份 | 约195MiB+53MiB | 分别在 `audit-retention-7d/expired-before-20261108T141444975.sql.gz`、`core-log-rebuild-172532/retained-core-log.sql.gz`（均位于上列cyf-git-cleanup目录）；删除会失去恢复副本，目前继续保护，已包含于351MiB不另加 |

### 已纳管待执行 / 明确保留

- 历史API中间输出：上轮计划约79.3MiB，既有后台 `rebuildable_cache_cleanup.py clean --artifacts-only` 仍在执行，未拿到最终结果；最终删除量只认 `priority-cleanup-173534/build-output-clean.json`，不把计划量当回收量。不再启动重复清理、不绕锁。`lease-int5`源码身份缺失等保护仍保留。
- MySQL binlog：当次约5.89GiB，现有259200秒（3天）自动保留；等待自动到期。提前清理需核对恢复/复制依赖并另授权，不直接rm。
- `/home/isp/state/cyf-runtime-lease-separation-20261112`约527MiB：活动任务，暂不清。Runtime历史备份、API回退JAR、当前/回退包及生产状态受保护，不能为凑45GiB直接删。
- Gradle/NPM/Web共享依赖/node_modules/Node编译缓存继续保留；运行中的云效Runner、生产应用、数据库和Git可达历史不当垃圾。
- 原优先项的旧压缩日志、历史堆转储、废弃录屏FFmpeg和停用测试数据库载荷已清，不重复列为收益。`cyf-test-tmp`余约2.5MiB主要是日志/证据，`clear_disk.log.*.gz`为清理审计，继续保留。


## 2026-11-15后续：旧证据压缩与journal回收

- 本次授权继续处理可筛选目录，未扩到Codex活动会话、其他项目、JDK/Xray、Runtime包及维护备份。上一轮构建中间产物已完成：8,410文件、83,189,760字节（79.3MiB），最终回执为 `priority-cleanup-173534/build-output-clean.json`；此前“仍在执行”为当时盘点状态。
- 对至少48小时未变化、至少512KiB、无占用的旧JSON/JSONL/log/txt文本证据执行相邻gzip归档，共140份，按实际分配块节省474411008字节（452.4MiB）。逐文件验证解压SHA-256与原内容一致后才移除原路径；全部压缩文件再次核验通过。保留源代码、测试输入、可复用构建缓存、权威manifest/receipt/state等控制记录，未知用途工具/包未删。
- 一次性执行 `journalctl --vacuum-size=100M`，只回收可退役的历史journal，不直接删除活动文件、不改永久保留配置。执行返回码0；前后占用及回收详情见证据目录的journal日志，不承诺含活动文件的总量低于100MiB。
- 本批净增可用141099008字节（0.131GiB）；完成核验时根盘已用46.528GiB、可用12.338GiB，尚未达到45GiB。实际净值含同期系统写入，不与上一轮回收重复累计。
- 私有证据路径 `/home/isp/state/cyf-git-cleanup-20261115/evidence-compression-204918/`：`compressed.jsonl`映射旧路径→gzip及原内容SHA-256，`plan.json`保留原身份/权限/时间，`verification.json`是逐文件复核结果，恢复说明为`RECOVERY.md`。历史证据原路径若已压缩，按映射用 `gzip -dc -- 原路径.gz`读取；不把原路径缺失误当成证据字节已丢失。

本次journal回执实际释放128MiB（216MiB→88MiB），与文本压缩合计约580MiB。清理结束的净增可用回执与随后复核不是同一时点：期间其他写入使根盘回升；20:55后的二秒只读观测发现其他gzip进程及MySQL/Codex仍写盘，观测时已用约46.79GiB。该gzip不属于本次Python压缩进程，未对其控制或清理。详见同证据目录`concurrent-write-observation.json`；不把本次文件回收量冒充整盘净下降。
