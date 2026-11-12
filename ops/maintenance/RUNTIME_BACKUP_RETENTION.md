# Runtime recovery payload retention (2026-10-26)

User-authorized host policy: existing `/etc/crontab` invokes `/home/isp/bin/clear_disk.sh clean` every 30 minutes. Runtime retention runs before the low-space early return, even when free space exceeds 5 GiB; it is not a new app automation or Flow release. The clean entry uses a fast df before retention, not a recursive diagnostic du that could delay recovery while holding the lock. Detailed du remains in check/plan and the post-low-space diagnostic path.

- Only `/home/isp/baks/cyf-agent-runtime-v1/YYYYMMDD-<batch>/` known layouts: `state.tar`, `state.tar.gz`, `old-program.tar.gz`, files/symlink entries inside `old-program/`. Keep all directories, RECOVERY, version/manifest records and other evidence. Archived symlinks are unlinked, never followed.
- Keep newest **two payload-bearing batches**, plus `current.json`'s explicit `backup` pin, all newer-than-pin attempts, batches changed within one hour, `.keep` ancestors, active batches/inodes and unsafe batches. Unsafe batches reserve newest slots rather than evict valid recoveries. Missing pin/payload, unknown activation status or incomplete process scans fail closed.
- Current record must say `verified-active`; this is historical release verification, not an assertion of continuous health. Read only safe root-owned records. Legacy `/home/isp/apps` is isp-owned 0755: allow this exact ancestor only for reading the release record, verify all ancestor identities before/after; deletion ancestry remains root-owned and non-writable by others.
- Hold existing host cleanup and `/run/lock/cyf-wuyong-versioned-release.lock` locks, nonblocking. Busy is a no-op, not an excuse to unlink locks or cancel deployment. New releases must keep using the same release lock. Reboot recreation uses tmpfiles `f`, never `f+`.
- Resnapshot `/proc` before every 100-file mutation chunk; validate complete batch before any deletion and each file signature/anchored parent before unlink. Mounts, hardlinks, insecure ownership/modes, nested `.keep`, depth >20, >100000 entries per batch or >512 unretired batches or >10000 metadata entries are not deleted. Unknown formats are not guessed.
- Completed `PAYLOAD_RETIRED.json` tombstones are not rescanned or counted against the active-batch budget; do not reuse retired batch roots. Later files under a retired root are preserved rather than inferred disposable. Small historical records can therefore accumulate without exhausting the active 512-batch bound.
- Durable pre-delete audit and `PAYLOAD_RETIRED.json` mark partial/full retirement; these recovery points are no longer complete. Audit `/home/isp/baks/host-cleanup/runtime-backups/audit.jsonl` rotates at 8 MiB (5 rotations); ordinary status/syslog remains existing host logger. No external notification configured.
- Source mirrors: `clear_disk.host.sh` is the full host entry; `clear_disk.sh` remains the minimal existing repository compatibility entry with an independent Runtime stage. Runtime helper reuses shipped `rebuildable_cache_cleanup.py`, `host_cleanup_log.py`, `host_cleanup_processes.py`; deploy together under `/usr/local/libexec/cyf/`. No builds or service restarts needed for this maintenance change.

Read-only plan: `/usr/bin/python3 -I -B /usr/local/libexec/cyf/runtime_backup_cleanup.py plan`.
Isolated fixtures: `/usr/bin/python3 -I -B /home/isp/bin/tests/test_runtime_backup_cleanup.py`.
This policy does not guarantee sufficient disk for arbitrary future workloads; non-Runtime backups, databases, current program/state, task worktrees and Flow pins remain protected.

## 必要状态备份与程序瘦身（2026-11-09用户后续决定）

优先**减少重复程序文件及不必要的备份成员**，不以旧程序重压缩作为优化主线。下面的`compact-program`保持显式手工兼容，不加入cron或未来安装的默认链路；原保留数量、current pin、锁、身份与可恢复安装边界不变。

- `runtime_backup_scope.py`供现有维护helper及未来Owner受控安装事务复用。未知文件默认保留，原有两类排除保持：精确`unified/agents/<subject>/inspection-state/<hex>/measurement/.isolated-*|.execution-*`启动探测临时目录；`codex-home/logs_2.sqlite`经只读SQLite检查确认为仅含`logs/_sqlx_migrations/sqlite_sequence`及既有诊断列时，排除该库与其`-wal/-shm`。库无法读取、列/表有变化、名字相同但语义不符均保留。程序不删除任何源状态。
- **2026-11-12范围收窄（v2）**：另排除精确静态布局`unified/agents/<subject>/codex-home/.tmp/plugins`、托管布局`unified/<64hex>/home/.tmp/plugins`中可从本地Git恢复的干净工作副本。仅在该目录确为独立Git工作树、无已跟踪修改/未跟踪/忽略文件、无submodule和隐藏修改的index标志时生效；未知/脏目录整体保留。**完整`.git`目录、历史和版本仍打包**，排除记录绑定commit。恢复后在该缓存目录执行`git restore --source=<state-scope.json记录的commit> --worktree -- .`即可离线重建；不需拉取、不清源目录、不改已有备份。普通项目仓库以及其他`.tmp`内容不受影响。
- 技能`.cyf-skill-view-staging`含原子切换恢复意图，`inbox/.../skill-install`含journal及不可变技能包，不能仅以“暂存”命名排除；与`private-runs`一并保留。v2定向测试含干净/脏/忽略/隐藏文件、静态及托管布局、公共仓库和符号链接保护，以及压缩包真实恢复后离线重建缓存与业务状态保留。
- `inspection-state`的`requests/conversations`和`private-runs`不是通用垃圾。保留完整会话、请求绑定、身份/授权、队列、ACK、幂等、用户成果、HOME中的其他SQLite及未知临时文件。不按空闲/年龄推断任务完成；不恢复旧状态覆盖新事实。
- 依据：Runtime1.3.68/source92df9eb8，`isolated-engine-profile.mjs`的`_prepareEphemeralState`逐次mkdtemp生成启动探测状态；`_prepareRequestState`及`typed-inspection-profile.mjs`的持久请求/会话恢复仍依赖原目录。诊断库已核对真实表/列而未读取日志内容。变化后需核实对应生产者，不能把本清单扩成通配删除规则。
- 新备份显式枚举成员，tar使用`--no-recursion --null --verbatim-files-from`避免重新纳入排除子树；保留ACL/xattr、权限、链接与稀疏文件，tar compare及前后清单复核成功后写该批`state-scope.json`，绑定归档SHA和发布记录摘要。归档沿用既有tar/tar.gz格式，收益来自范围缩小，不转换/重压缩旧备份。API也支持普通`state.tar`，但不能把它的大小和历史gzip包直接比较。
- 主机已安装的显式入口：`runtime_backup_cleanup.py plan-state`只读清单；`backup-state --batch <NEW_BATCH>`只写新批次，取得host→release锁并要求指定Runtime单元已由Owner停止、LoadState正常、MainPID为0、cgroup无残留及状态根无其他进程占用。工具不会停服务、启动、激活或恢复数据。原pin/既有载荷不能覆盖，失败保留源状态及诊断。
- **已接入与复用边界（2026-11-09）：** Runtime1.3.69/source`fb9aafbd4c334efe7633f147d5b986de084f45df`已通过本批前瞻本地安装器真实启用，备份`20261109-runtime-footprint-local/state-scope.json`绑定必要状态选择；新安装器及prepared证据见`docs/implementation/evidence/runtime-footprint-20261109/release/install/`。历史prepared/一次性安装器继续保留原摘要，不原地改写，也不宣称所有未来发布自动接线。下一Owner在停止写入、原子切换前直接复用`runtime_backup_scope.write_state_archive(...)`，传同批`release_binding`与log，持host→release锁且确认状态无占用；不要调用CLI重抢自己的release锁，也不必重复实现函数内已有的tar compare。保留pre-start原程序rename恢复和后启动状态兼容判断。
- Python源入口：外仓`conf/cyf-agent-runtime-v1/lib/freeze-python.py`已在新私有stage冻结后、sandbox image/manifest之前合并字节/模式/uid/gid/xattr相同的Python别名。显式磁盘`CYF_PYTHON_DEBUG_OUTPUT`用于包外保存符号并对带`.debug_info`的Python ELF执行`strip --strip-debug`，不剥离动态符号、不删pip或功能包。无该变量时只去重。原`python-artifact.py`已适配内部硬链接的安全提取，旧普通文件包仍兼容；新硬链接包须配套新提取器，不能交给旧消费者猜测恢复。不能在sandbox链接已建立后或生产app内原地执行。

- **当前Python模式：** 1.3.69仅去重，保持Python/sandbox字节摘要及现有材料能力认证，实际app约837→686MiB。strip改变认证输入，不能默认开启或重标旧认证；约626MiB仅是前期隔离strip探测，不是本版实占。
- **回收实况：** 08:48后plan保留最近两批/current，无eligible批次，未额外删除。新归档old-program继承原基线runtime目录0775，被安全清理器保留；未来回收须单独对账原manifest/存储兼容，不改权限绕过保护。

验证、实测、实际1.3.69发布及历史未发布阶段边界见`docs/implementation/handoffs/RUNTIME-FOOTPRINT-20261109.md`。

## 程序无损压缩与隔离恢复（2026-11-09）

### 现行边界

- 保持最近两批＋current pin的保留数量和现行锁/状态保护；`clean`、cron不自动压缩或转换任何恢复点。状态包 `state.tar[.gz]`、身份/授权/会话/ACK、日志及历史RECOVERY/安装记录不改写。
- 显式 `compact-program` 只把指定备份内的 `old-program/` 转为该批的 `old-program.tar.gz`。**归档不排除工具链或任何程序文件**，保留程序字节、内部硬链接、软链接、uid/gid/mode、纳秒mtime及扩展属性/ACL；没有跨批依赖，因此每批仍可独立恢复。GNU tar gzip1用于控制成本，不承诺固定压缩率。
- 责任入口仍是 `runtime_backup_cleanup.py`，复用host→Runtime release锁、进程扫描和原逐文件删除；不新增发布runner/守护程序/台账。此操作不改current发布记录，不代表应用发布或状态回退。
- 必须绑定该批原始 `current.manifest.json` 的真实SHA-256；完整源程序须匹配现有安装manifest，外部硬链接、占用、挂载、`.keep`和源漂移均停止。先完成tar compare和**全新磁盘目录独立恢复**，对元数据/内容/链接闭包复核，再发布归档及 `program-archive.json`，最后移除已验证原目录；不先删除腾空间。
- 临时归档和隔离恢复位于该批普通磁盘，需要容纳压缩包＋一次完整展开的实际峰值；不使用内存盘、不设置无依据大小门槛。旧程序已停用后的备份压缩/恢复属于安装维护，不向应用下传600秒deadline；隔离测试仍遵循CYF测试构建批次预算。
- `program-archive.json`是该批载荷的存储/恢复事实，不是新全局台账。部分目录移除失败仍保留已验证完整归档，重入只接纳原事实的剩余子集，额外文件/篡改不自动采纳；未知预存归档或发布receipt失败后须Owner明确对账，不猜测补全。

### 调用与恢复

以下命令仅是入口说明，使用真实批次和原始manifest摘要；本次未转换任何既有实际备份：

```bash
/usr/bin/python3 -I -B /usr/local/libexec/cyf/runtime_backup_cleanup.py compact-program \
  --batch /home/isp/baks/cyf-agent-runtime-v1/REAL_BATCH \
  --manifest-sha256 FULL_ORIGINAL_MANIFEST_SHA256

/usr/bin/python3 -I -B /usr/local/libexec/cyf/runtime_backup_cleanup.py restore-program \
  --batch /home/isp/baks/cyf-agent-runtime-v1/REAL_BATCH \
  --manifest-sha256 FULL_ORIGINAL_MANIFEST_SHA256 \
  --destination /home/isp/state/cyf-local-build/tasks/cyf-runtime-restore-REAL_TASK
```

- `restore-program`只创建全新暂存根；允许普通磁盘`/var/tmp`或现行本地tasks下`cyf-runtime-restore-*`，已有目录/链接一律不覆盖。归档成员检查拒绝路径逃逸、特殊文件、重复成员、软链接子路径及外部硬链接；合法绝对venv软链接仅保留为叶子，不跟随写入。
- 恢复到暂存不激活程序，不启动备份，不恢复状态。Owner仍须沿原流程检查状态兼容、停写/锁/身份、把程序安装到固定实体app并验证，之后才启动；不得直接运行暂存或备份目录。原历史RECOVERY.md若仍描述old-program目录，以本批新增存储receipt识别压缩形式，不把历史说明改写成新交付证据。
- **未来安装接续点：** pre-start失败仍用原old-program原子rename恢复；只在新进程/通道验证完成、current为verified-active、该批不在使用时，退出原安装事务并释放原锁后，由Owner调用显式压缩命令，由维护helper重新取得host→release锁。不要在新服务启动前移除原程序目录，不延长停机窗口去压缩。受测并安装该维护helper不代表历史一次性安装脚本已自动接线：image-usage任务的prepared.json绑定原安装器摘要，不能原地修改。

验证与实际安装状态统一见 `docs/implementation/handoffs/RUNTIME-BACKUP-OPTIMIZATION-20261109.md`。该早期任务只解决程序压缩，不作为必要状态分类的当前实现说明；当前范围及1.3.69真实接入以上节和RUNTIME-FOOTPRINT handoff为准。完整HOME仍不能整体排除；跨批工具链共享未实现。
