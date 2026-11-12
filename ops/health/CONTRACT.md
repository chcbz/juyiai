# OPS-HEALTHMON-AVAILABILITY-20260906 frozen implementation contract

Frozen on 2026-09-06 before the availability-policy source change. This file is
implementation input and review material, not installation, resume, mail, or API
lifecycle authorization.

## Event and API catalog

Only these read-only observations exist:

1. `GET https://kit.chaoyoufan.cn/juyiting`: HTTP 200, `text/html`, configured
   bounded HTML marker present.
2. `GET https://api.chaoyoufan.cn/agent/map`: either the production contract's exact
   HTTP 401 with empty Content-Type and zero-byte body, or HTTP 401/403 with a JSON
   authentication-denial object. This proves only that the fixed public API/auth
   boundary responds; HTML 403/502 and HTML 200 SPA responses fail, and authenticated
   map or roster semantics are not proved.
3. `/usr/local/sbin/cyf-api-kit status`: exact canonical status authority. Exit 0 is
   trusted UP only with the required identity/artifact/listener fields; exit 3 is
   stopped only with an unowned-port-free stopped result; exit 4 can be recovery-safe
   only when runtime identity, artifact, listener ownership, PID and age are all
   explicit. Exit 1 is busy/error and exit 5 is unsafe. Unknown/truncated output is
   unsafe.
4. Read-only TCP checks: MySQL handshake on 127.0.0.1:3306; Redis unauthenticated
   `PING` on 127.0.0.1:6379 where `+PONG`, `-NOAUTH`, or `-NOPERM` proves reachability
   only.
5. `/usr/bin/systemctl is-active cyf-agent-runtime-v1@unified.service`: alert-only.
6. Bounded MemAvailable and API-filesystem availability observations: warning-only,
   never recovery admission blockers under this availability policy.

Only these mutations exist:

- Atomic monitor state/maintenance updates below `/home/isp/state/cyf-juyiting-health`.
- Exact API recovery command `/usr/local/sbin/cyf-api-kit start` for trusted STOPPED,
  or `restart` for the fully trusted LISTENING/NOT_READY branch after 25 minutes.
  Recovery alone receives the exact fixed environment additions
  `CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0` and
  `CYF_API_MIN_DISK_AVAILABLE_BYTES=0`; canonical `status`, mail, systemctl and every
  other child retain the original fixed environment without those additions.
- Exact mail command `/usr/bin/python3 -I /root/.local/bin/cyf-task-email SUBJECT BODY`.
  Only this exact mail-helper child receives fixed `LC_ALL=C.UTF-8` and `LANG=C.UTF-8`
  so sanitized Chinese argv remains encodable on Python 3.6. Canonical status/recovery
  and every other child retain the fixed `C` locale; no inherited environment is added.
- Explicit CLI administration: `--init`, `--pause`, `--resume`, `--reset-circuit`, and
  `--notify-test`.

No URL, executable, argv, shell fragment, credential, token, PID, signal, build,
deploy, pull, DML, Gradle, business write, arbitrary inherited environment, or Agent
recovery is configurable.

## Lock order and singleton boundary

1. Validate fixed config path, ownership, mode, parent chain, bounded JSON and schema.
2. Validate fixed state directory and lock inode.
3. Acquire the monitor lock with nonblocking `flock`.
4. Validate/read state; corrupt, missing (except explicit `--init`), insecure, or
   unknown-schema state fails closed.
5. Validate maintenance marker.
6. Run bounded read-only probes.
7. Persist the current snapshot, including warning-only resource classification.
8. Persist the selected recovery-attempt notice and deliver that current notice ahead
   of older queued mail. Before counting or invoking, read the maintenance marker,
   MySQL, Redis and canonical status again. Restart proceeds only when the same trusted
   PID is still MATCH/LISTENING/NOT_READY and at least 1500 seconds old; maintenance,
   dependency loss, a healthy result, PID change, identity change or another
   precondition skip never consumes an attempt.
9. Persist actual attempt count, timestamp and in-flight fence immediately before the
   canonical lifecycle invocation. Invocation exceptions consume that already-durable
   attempt.
10. Invoke only the exact canonical action with the two fixed recovery-only resource
    threshold overrides. Keep the same monitor flock for the complete wait; the
    monitor does not impose a timeout or signal that subprocess.
11. Run a fresh canonical status and persist the result with the actual completion
    time after the potentially long lifecycle call, not the pre-invocation time. A third failure persists the
    circuit and the single urgent Chinese exhausted notice before delivery is tried.
    Mail failure leaves both circuit and notice durable. Third-attempt success persists
    success without the exhausted notice or circuit latch.

Cron overlap therefore defers immediately and cannot overlap a cold start that may
last 9-13 minutes (canonical maximum 1200 seconds). The 60-second cooldown aligns with
the next one-minute cron opportunity and never creates an internal busy loop.

## State transaction boundaries and compatibility

State is a root-owned 0600 regular file, one link, atomically replaced from a 0600
same-directory temporary file and followed by file and directory `fsync`. Attempt and
`last_attempt_at` are durable before lifecycle execution. An interrupted `in_flight`
attempt consumes its attempt slot and is fenced by cooldown/max-attempt controls. If
persisted attempt three has no trustworthy terminal receipt, the next tick clears the
in-flight marker into an explicit UNKNOWN terminal result, latches the circuit and
durably queues one deduplicated urgent notice without claiming a confirmed command
failure or success; no fourth invocation is permitted. For interrupted attempt one or
two, three later trusted canonical-UP observations clear the stale in-flight fence and
old incident budget without guessing the missing native terminal, so a later incident
starts with its own three-attempt budget.
Recovery success requires both command exit 0 and a fresh fully trusted canonical UP
status. A healthy observation never depends on lifecycle command exit alone.

Schema version remains `1`; the strict outer state keys and existing recovery fields
are unchanged. Existing `resource_preflight` snapshots remain valid, while new
snapshots may use optional `resource_observation`. New check results carry their own
integer `observed_at`; `last_snapshot.at` is the observation-window start and never
pretends that earlier component checks occurred after a long recovery call. Existing incidents, attempts,
circuit state, outbox and notice IDs are loaded without reset during upgrade. Default
absence is accepted only by explicit `--init` (or an installer action that explicitly
calls it). `--status` is read-only and never creates, repairs, retries mail, probes
services, or receives recovery-only environment overrides.

## Recovery state machine

- Only local canonical API STOPPED or fully trusted LISTENING/NOT_READY failures count
  toward API auto-recovery eligibility.
- Three consecutive API failures are required. STOPPED -> `start`.
- NOT_READY -> `restart` only with `ARTIFACT_ATTESTATION=MATCH`, exact PID,
  `RUNTIME_IDENTITY=cyf-api(987:1000)`, `PORT_10018=LISTENING_BY_PID`, and trusted
  elapsed age >=1500 seconds. The rc4 no-listener branch is alert-only.
- MySQL and Redis must be reachable; maintenance must be absent. Resource observations
  are retained as warnings but do not block the exact recovery action.
- Cooldown is >=60 seconds. Maximum is three persisted actual attempts per incident.
  The third failed attempt latches the circuit; no fourth automatic attempt exists.
  Third-attempt success does not send the exhausted alert and does not latch.
- Three observed fully trusted API-UP checks reset the attempt/circuit fence. Explicit
  `--reset-circuit` remains an authorized-only alternative.
- Public web, public API/auth, dependencies, and Agent service are alert-only. An
  external-only failure can never restart a locally healthy API.
- rc1, rc5, unknown identity, malformed output, missing identity, foreign listener,
  and insecure/corrupt files are fail-closed and never recover.

## Manual/automatic shared-attempt reconciliation contract

There is no broad manual-import CLI. While maintenance remains active, a separately
authorized exact monitor Owner may reconcile an independently persisted manual
lifecycle receipt under the monitor's own lock. The reconciliation must verify the
same incident ID, trusted receipt digest, exact action/time/result, `in_flight=null`,
and a monotonic combined attempt number equal to current attempts or current attempts
plus one; it must never decrement, skip, reset, or grant three manual plus three
automatic attempts. An exact duplicate is idempotent; conflicting or gapped input
fails closed. Existing schema-v1 recovery fields are updated atomically. Manual
failure number three persists the same circuit and single urgent notice; manual
success number three does not latch. Resume/install/mail execution requires a later
separate authorization.

## Sensitive-payload and mail allowlist

Durable snapshots, stdout and mail may contain only: UTC/Asia-Shanghai timestamps,
component names, boolean health, bounded classification labels, HTTP status/content
type, trusted PID, trusted elapsed seconds, recovery action/attempt/result/return code,
incident ID, queue counts, the two public fixed override names/zero values, and fixed
operational guidance. They must never contain response bodies, canonical stdout/stderr
or argv rows, process command lines, arbitrary environment values, credentials,
tokens, email recipient/config contents, passwords, cookies, authorization headers,
raw logs, or arbitrary exception text. Error details are reduced to fixed exception
class labels.

All new incident, recovery, resolved, reminder, digest and test notices use concise
Chinese: actionable summary first, bounded metadata after it. Subject CR/LF/control
characters and body controls are sanitized. Schema-v1 loading continues to accept a
legacy stored subject of at most 160 characters and a body of at most 2000 characters,
so upgrades do not invalidate the existing outbox. Every newly queued subject and every
subject immediately before helper delivery is re-sanitized to at most 40 UTF-8 bytes;
all current templates fit that byte bound without Python 3.6 encoded-word folding, and
the urgent failure/unknown titles retain `3/3`. Bodies remain bounded to 2000 characters.
The durable outbox is bounded and deduplicated. Delivery failure remains pending with
bounded retry backoff. Current attempt and exhausted notices are prioritized. A small
bounded priority reserve permits critical insertion without evicting an existing
exhausted alert; if even that reserve is full of protected alerts, a new attempted
notice fails closed rather than invoking without durable notice. Other full-queue
events are coalesced into a bounded Chinese digest; reminders and later priority
insertion cannot evict an exhausted alert. Helper acceptance is stated only as local helper acceptance, never as inbox
delivery. `/usr/bin/python3` may be a symlink only when every lstat hop and parent is
root-trusted and the final target is a safe executable. Exceptional `fail_closed`
guards emit only a fixed sanitized message through a root-trusted `/usr/bin/logger`;
normal ticks are not sent to syslog.

## Acceptance-to-test mapping

| Acceptance | Test coverage |
| --- | --- |
| three-failure threshold and exact start | `test_stopped_threshold_starts_on_third_failure` |
| three actual failures -> persistent latch -> no fourth | `test_three_failures_latch_and_never_invoke_a_fourth_recovery` |
| third success has no failure alert/latch | `test_third_success_does_not_latch_or_send_exhausted_failure` |
| attempt persisted immediately; invocation exception counted | `test_stopped_threshold_starts_on_third_failure`, `test_recovery_exception_consumes_third_actual_attempt_and_latches` |
| post-mail maintenance/dependency/identity revalidation skips not counted | `test_post_mail_maintenance_change_rechecks_dependencies_and_skips_without_count`, `test_post_mail_dependency_change_skips_without_count`, `test_precondition_and_revalidation_skips_do_not_consume_attempts`, identity revalidation tests |
| warning-only resources and recovery env overrides | `test_resource_warning_does_not_block_recovery`, `test_recovery_env_has_only_fixed_threshold_overrides_and_status_has_none` |
| old schema-v1 incident/attempt/circuit retained | `test_schema_v1_old_state_load_preserves_attempts_incident_and_circuit` |
| urgent Chinese mail content/priority/dedup/send failure | `test_third_failure_alert_is_durable_prioritized_deduped_and_survives_mail_failure` |
| interrupted third attempt -> UNKNOWN latch/urgent/no fourth | `test_interrupted_third_attempt_latches_unknown_alert_and_never_invokes_fourth` |
| three trusted UP checks isolate early interrupted attempt from next incident | `test_three_trusted_up_checks_clear_early_interruption_before_new_incident` |
| per-probe timestamps in mixed observation window | `test_each_mixed_window_probe_has_its_actual_observation_time` |
| completion timestamp and exhausted-alert outbox protection | `test_recovery_result_mail_uses_actual_completion_time`, `test_full_outbox_reminder_never_evicts_exhausted_alert`, `test_new_priority_never_evicts_existing_exhausted_alerts`, `test_new_exhausted_alert_evicts_only_noncritical_items` |
| concise Chinese templates, urgent `3/3`, injection controls, new 40-byte subjects and legacy 160-character state acceptance | `test_mail_fields_are_sanitized_and_bounded`, `test_subject_templates_are_short_utf8_and_keep_urgent_attempt_count`, `test_legacy_long_subject_is_bounded_again_at_delivery_time`, `test_schema_v1_old_state_load_preserves_attempts_incident_and_circuit` |
| exact old long subject after send-time sanitization plus every current title flattens with ASCII From/To, CRLF and no encoded-word continuation under isolated Python 3.6; mail-only UTF-8 locale | `test_real_isolated_python36_flattens_all_bounded_subjects_without_folding`, `test_recovery_env_has_only_fixed_threshold_overrides_and_status_has_none` |
| rc1 busy and rc5/foreign fail closed | `test_rc1_busy_never_recovers`, `test_rc5_foreign_identity_never_recovers` |
| external-only failure no restart | `test_external_only_failure_never_recovers_healthy_api` |
| maintenance pause | `test_maintenance_reports_but_pauses_recovery` |
| corrupt/missing/insecure state/config | `StateStoreSecurityTests`, `ConfigSecurityTests` |
| 60-second cooldown and interrupted fencing | `test_cooldown_blocks_second_attempt`, `test_interrupted_attempt_is_fenced`, `test_cooldown_is_one_cron_interval_without_busy_loop` |
| dependency gate | `test_dependency_down_blocks_recovery` |
| startup grace/full rc4 identity | `test_not_ready_requires_grace_and_full_identity`, `test_rc4_without_runtime_identity_is_alert_only` |
| command exit is not success | `test_exit_zero_without_fresh_up_is_failure` |
| mail retry/dedup/bounds/current-attempt priority | `MailQueueTests`, `test_current_attempt_mail_is_durable_and_prioritized` |
| web marker, empty 401, JSON denial and HTML rejection | `ProbeContractTests` |
| safe Python symlink chain | `TrustedExecutableTests` |
| post-mail same-PID restart fencing | `test_post_mail_restart_revalidation_*` |
| exceptional guard syslog only | `test_guard_logging_uses_fixed_sanitized_syslog_command`, `test_cron_syntax_contract` |
| installer staging/activation trust | `test_installer_trust_and_activation_contract` |
| maintenance directory durability | `test_pause_resume_marker_and_directory_fsync` |
| fixed config/command/security and no real side effects | `ConfigSecurityTests`, `StaticContractTests`, injected `FakeEffects` tests |

## 2026-10-20 ES dependency extension

Add `elasticsearch` to the existing component set, probe timestamps, incident streaks and sanitized Chinese notifications. Only fixed `http://127.0.0.1:9200/_cluster/health` and `/chat_memory/_search?size=0&terminate_after=1` authenticated GETs are permitted. Use no proxy or redirects; do not return document content. Fixed root-only 0600 `/etc/cyf-elasticsearch-health-auth.json` is an explicit exception to the earlier no-credential-file-read rule, not a configurable URL or shell hook. No ES lifecycle, index writes/deletes, embedding calls or new API recovery triggers are added.

A non-timeout green/yellow cluster and complete successful search shards are required. Yellow remains visible as `es_search_ok_yellow`; red, missing index, bad credentials, transport/parse errors and partial search fail. Existing deployed schema-v1 six-component state requires an explicit locked, backed-up addition of the seventh streak and unobserved snapshot field before first validation; preserve all incident/recovery/outbox fields. This is host monitor maintenance, not an application build or application release.

### 2026-10-21 已安装核验补充：可用性而非进程存活
Agent snapshot只做观察，当前MainPID、0600可信文件、连接/注册/ready、三心跳周期内有效回执缺一不可。Agent异常仅告警，不自动重启。API当前PID近期OOM观察覆盖“health还UP但运行线程已异常”的窗口，仅告警、不得授权恢复；旧PID错误忽略。保留既有state schema与恢复决策，不改变业务deadline。

恢复carrier保留只读`--check`；monitor必须在预留恢复次数前检查canonical信任链。摘要过期、身份不可信、预检不可用均拒绝恢复且不消耗次数；不自动接受新hash。2026-10-21核验现行canonical SHA256为`878e2f91f2a557f2c10ca954c438b090cc370d90e99da851053e0190bc04be56`，本轮未修改该实体；后续升级需要重新审阅和固定。

2026-10-26局部核验：用户授权开启API OOM自动dump，保留192MiB Metaspace上限。Flow5264702/74安装仅新增dump参数的canonical，SHA为`1ea29310b2bbce2a4755869286886d529f55d85a5b6e3ae862562a3d0e39a081`；76同步carrier和monitor固定摘要，carrier `--check`通过，无重启、无监控状态/计数变更。上文2026-10-21摘要保留作历史基线，不代表当前值。当前carrier SHA为`00dd5d68e76b329e87ef1e678ac567f6108a1065622a598885e21e68090a61b4`，monitor SHA为`4136857418ab1fe8b2b8c552241306b02d1dadd6dd8e0fa24ddca717fb64978a`；仍禁止自动信任当前任意字节。证据`/home/isp/state/cyf-skill-management-recovery-20261026/uninstall/release/oom-dump/`，实际OOM生成dump及完整故障恢复未演练。
