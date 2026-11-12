# CYF Juyi Hall bounded health monitor

`cyf-juyiting-health.py` is a Python 3.6 stdlib cron monitor. It checks the
public Juyi Hall HTML entry, the unauthenticated public API/auth boundary (including
the fixed endpoint's production empty-401 contract), the canonical local API status,
MySQL/Redis reachability, and the Codex Agent unit.
Only the API can be recovered, through the exact accepted canonical command.

It does **not** prove authenticated map/roster/business behavior, SMTP inbox
delivery, or whole-host availability. Whole-host failure needs an external
monitor. Redis `-NOAUTH`/`-NOPERM` proves reachability only.

## Fixed safety behavior

- `/usr/local/sbin/cyf-api-kit` must be root-owned 0755 with SHA-256
  `56537824cd33f6333f199ea1cebda90b127b39c079e08daad6d164607f788ef5`.
- State is root-only, atomic 0600 under `/home/isp/state/cyf-juyiting-health`, protected
  by a nonblocking singleton flock held through the full synchronous canonical
  recovery (cold start is normally 9-13 minutes and can wait up to 1200s).
- Recovery needs 3 consecutive local API failures, healthy MySQL/Redis, no
  maintenance marker and a 60-second cooldown. Memory/disk observations are
  warnings rather than blockers. Recovery alone invokes the trusted canonical with
  fixed `CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0` and
  `CYF_API_MIN_DISK_AVAILABLE_BYTES=0`; status and other commands do not receive
  those overrides or inherited environment values.
- At most 3 actual attempts are persisted per incident. The count/in-flight fence is
  durable immediately before invocation, including an invocation exception. The
  third failed attempt persists a circuit latch and a prioritized single Chinese
  `恢复失败，已停止自动重试（3/3）` alert; no fourth attempt occurs. A third-attempt
  success does not send that alert or latch the circuit.
- STOPPED may start. NOT_READY may restart only after 25 minutes when canonical
  output explicitly includes matching artifact, owned listener, PID/age and
  `RUNTIME_IDENTITY=cyf-api(987:1000)`. The canonical rc4 no-listener branch
  lacks a complete runtime-identity assertion and is deliberately alert-only.
- Three trusted API-UP observations reset the circuit. `--reset-circuit` is an
  explicit alternative. Public web/API, dependencies, and Agent are alert-only.
- Incident/recovery mail is queued durably. The current recovery-attempt notice is
  tried ahead of old mail, then canonical status is read again: restart requires the
  same trusted PID to remain MATCH/LISTENING/NOT_READY and at least 25 minutes old.
  Healthy/PID-changed/identity-changed results cancel recovery without consuming an
  attempt. Mail failure remains queued with bounded retry/dedup.
- New incident, recovery, resolution, reminder, digest and test mail is concise
  Chinese with the action first and bounded metadata after it. The final exhausted
  alert includes Asia/Shanghai time, impact, confirmed classifications versus unknown
  cause, attempt/action/return code/fresh health, manual next action and the resource
  override explanation. Recovery-result time is captured after the lifecycle call and
  fresh health check. Every stored probe has its own observation time; the snapshot
  timestamp is the window start. After attempt mail, maintenance, MySQL, Redis and
  canonical identity are all rechecked before the attempt is counted or invoked.
  A persisted interrupted third attempt becomes an explicit UNKNOWN terminal latch
  with one durable urgent notice and no fourth invocation. Interrupted attempts one
  or two retain their fence until three trusted UP checks, which then clear the old
  incident budget without guessing the missing native result. A later reminder or
  priority insertion cannot evict an exhausted alert from a full outbox. The fixed
  mail-helper child alone uses `LC_ALL=C.UTF-8` and `LANG=C.UTF-8` so sanitized Chinese
  argv can be encoded by Python 3.6; canonical status/recovery and other children stay
  on the fixed `C` locale. Mail contains no raw logs, secrets or inbox-delivery claim.
- `/usr/bin/python3` symlinks are accepted only through a root-owned, non-writable
  lstat chain ending at a trusted executable. Credential file content is never read.
- Cron suppresses ordinary output mail. Exceptional `fail_closed` guards alone write
  a fixed sanitized event through root-trusted `/usr/bin/logger`; no response body,
  argv, environment or credential is logged.

## CLI

```text
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --init
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --check-once
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --status
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --pause
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --resume
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --reset-circuit
/usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --notify-test
```

`--status` reads the stored snapshot only: no repair, probe, mail retry, or
recovery. `--notify-test` is an explicit real mail action and must not be used by
automated tests.

Maintenance pauses only actions selected by a later tick; it never signals or
cancels an already-running canonical recovery. If `--pause` returns lock-busy
while recovery is in flight, a root operator may create the marker for the next
tick without touching the monitor/canonical processes:

```sh
/usr/bin/install -o root -g root -m 0600 /dev/null /home/isp/state/cyf-juyiting-health/maintenance
```

The next normal tick validates that marker and reports checks while suppressing
recovery. Remove it with `--resume` after the singleton lock is available.

Manual and automatic recovery share one three-attempt incident budget. There is no
general manual-import CLI. A separately authorized exact monitor Owner may, while
maintenance is active and under the monitor lock, reconcile a trusted manual receipt
monotonically into the existing schema-v1 recovery fields as specified in
`CONTRACT.md`. Installation, reconciliation, mail execution and resume each require
their own runtime authorization.

## Staged installation (not executed by this task)

Never execute repository scripts as root below `/home/isp`. First copy this
bundle to a root-owned staging directory, review it, then run:

```sh
/root/cyf-juyiting-health-stage/install.sh install
# Separately, only after acceptance and runtime authorization:
/root/cyf-juyiting-health-stage/install.sh install-cron
```

`install` atomically replaces the monitor from a fully written, fsynced same-directory
temporary file, so an active cron reader sees either the old or new complete bytes.
It copies config and explicitly initializes absent state. It does
not install cron, probe services, send mail, or recover API. The installer validates
the complete root-owned/non-writable staging parent chain and every payload.
`install-cron` requires the installed monitor's owner/mode/link count and SHA-256 to
match the reviewed candidate embedded in the installer, then byte-verifies the cron
copy. It does not restart `crond` or run an immediate check. Existing config/state
are never overwritten or repaired.

## Tests

```sh
/usr/bin/python3 -m unittest discover -s ops/health/tests -p 'test_*.py' -v
/usr/bin/python3 -m py_compile ops/health/cyf-juyiting-health.py
/bin/sh -n ops/health/install.sh
```

All behavior tests inject side effects; they do not access network, mail,
canonical lifecycle, systemd, or production state.

## Elasticsearch 案卷检索依赖（2026-10-20）

在现有每分钟 cron 内增加独立 `elasticsearch` 探针，沿用连续3次异常告警、恢复通知与去重；**只告警，不启动/重启ES，不因ES单独异常重启API**。检查固定本机HTTP端点的认证、`/_cluster/health` 和 `chat_memory/_search?size=0&terminate_after=1`，不读取业务正文。集群red/超时、认证失败、索引不存在、搜索超时或分片失败均不算成功；green或yellow且所有目标主分片检索成功才健康，yellow保留在分类中（不代表副本冗余正常）。本探针不覆盖Embedding供应商、语义相关性、页面或入库写入验收。

专用固定凭据文件 `/etc/cyf-elasticsearch-health-auth.json` 为root:root 0600普通单链接JSON（仅username/password），本次受控复制既有生产ES认证，不输出到日志、邮件、仓库或进程参数。禁止代理与重定向，凭据异常失败关闭；生产ES凭据轮换时需同步更新此文件。没有凭据时不把401当作健康。

现存六组件监控状态在安装锁下备份，显式补充 `component_streaks.elasticsearch=0`；旧snapshot补未观测失败标记，下一次真实探测覆盖。不重置事故、API恢复计数、熔断、邮件队列或其他组件状态。未来升级旧六组件实例也须先完成此受控状态迁移，不能直接覆盖后假定cron正常。原实例现有canonical预检、恢复carrier摘要、生产实体目录与SMTP错误分类修复需保留，不能用较旧仓库整文件覆盖。

## Agent通道与API内存故障观测（2026-10-21，已安装核验）

- Agent探针先核对精确unified unit/MainPID，再读root-owned0600的`/home/isp/state/cyf-agent-runtime-v1/unified/host/runtime-health.json`。所有已挂载Agent必须连接、注册、ready，且快照与有效presence回执不超过三个配置心跳周期；缺失、旧PID、隔离或回执过期均不能报健康。该时效仅用于告警，不中断请求/流、不触发Agent自动重启。注册启动期允许如实显示未就绪，原连续三轮告警去抖保留。
- 本机API的原canonical status仍负责安装摘要、PID、监听和health。UP时附加只读当前日志末1MiB检查；只匹配当前PID的ERROR/WARN OutOfMemoryError/Metaspace，历史PID不影响新进程。发现故障或无法读取观测时告警，`recovery_safe=false`，不把这条观察直接升级为自动重启授权。日志tail不是堆/类加载诊断，不能声称解决Metaspace根因。
- 不新增状态schema、业务接口或凭据；原恢复锁、预算、备份、鉴权、邮件与熔断策略不变。安装状态和实测证据另见当前handoff。

### 2026-10-21 恢复工具信任摘要维护

本轮对比了线上monitor/carrier与仓库，保留线上已有的canonical只读预检、生产实体目录、SMTP脱敏分类修复。当前canonical脚本的已审阅差异为继承FD9的inode/flock验证和启动Java时关闭FD10；未覆盖或降级该脚本。`CANONICAL_SHA256`绑定核验后的现行实体，monitor再次绑定carrier摘要，installer绑定两者摘要。`--check`只验证文件身份/摘要，不启动Java；不通过时不占用自动恢复次数。未来canonical变更必须同步审阅和更新精确摘要，不能改成“任意当前hash自动通过”。本次8项canonical路径检查、93项monitor定向测试通过；生产故障恢复演练未执行。

## API堆配置与恢复摘要（2026-11-02核对）

仅覆盖当前主机API容量维护与恢复工具摘要闭包；生产应用仍为Flow5260799/426、commit `8100b7910df973374828c717dd885577528f929f` / tree `0dd124c6473fc4bbc01ba14de096a59bc648026d`，不是新应用发布。

- 现行启动helper使用 `-Xms256m -Xmx768m`；Metaspace256m、direct64m及其他运行参数不变。此前384m堆在自然负载观察中存在大对象分配与Evacuation Failure，不能据主机MemAvailable充足便判断JVM堆无压力。
- `CYF_API_STARTUP_DIAGNOSTICS=1` 不仅输出控制面时间，还会加入Spring DEBUG/TRACE及startup tracing参数。纯容量对照/正常维护不要开启；如需测量冷启动应独立注明这些参数，不能宣称仅改变堆。
- helper变更须连同recovery carrier的canonical SHA、monitor的carrier SHA及install.sh候选SHA核对；不得绕过摘要校验或覆盖原有继承锁修复。恢复时同批恢复摘要闭包，不修改任务/会话/ACK事实。
- 本轮配置和读回已生效；性能结论按固定观察窗口解释，不将health UP当业务或端到端性能验收。证据和恢复入口：`docs/implementation/handoffs/JUYITING-PERFORMANCE-20261102.md`、`/home/isp/state/cyf-diagnostics/juyiting-performance-20261102/REPORT.md`。
