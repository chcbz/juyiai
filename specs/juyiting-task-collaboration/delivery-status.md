# 聚义厅悬赏榜与可靠多 Agent 协作 — 任务证据快照

截至 2026-09-06T09:21:00.295553+08:00；源文件 SHA-256 `e90988c19a0b2ec0aa24834d9e143fa3e17ac63b89648fbe8f7aba160db66705`。只读历史投影，不是调度台账。

| 任务 | 截止时点记录 | commit / tree | 证据摘要与剩余动作（历史快照） |
| --- | --- | --- | --- |
| `A01` | accepted（历史定义） | 未从运行台账绑定 | 首轮 Review 驳回后完成 8 项修订；Lagrange 第二轮独立 Review 已 ACCEPT。 |
| `A02` | integrated（历史定义） | 未从运行台账绑定 | Erdos 第三轮独立 Review ACCEPT；三项 commit 已集成并推送 api/develop，联合模块测试通过；未执行生产迁移。 |
| `A03` | integrated（历史定义） | 未从运行台账绑定 | Lorentz 独立 Review ACCEPT；alias 修复与最终 WebSocket JSON 测试已集成并推送 api/develop，联合模块测试通过。 |
| `A04` | integrated（历史定义） | 未从运行台账绑定 | Locke 第三轮独立 Review ACCEPT；三项 commit 已集成 api/develop，低内存单 worker 联合测试通过并推送。 |
| `A05` | integrated（历史定义） | 未从运行台账绑定 | Mill 独立 Review ACCEPT；两项 commit 已集成并推送 isp-install/master，npm ci 后 17 tests 与 Node 20 validate 通过；未部署在线副本。 |
| `A06` | integrated（历史定义） | 未从运行台账绑定 | Mill 第七轮独立 Review ACCEPT；七项 commit 已集成并推送 isp-install/master，npm ci、54 tests、validate 通过；未部署在线副本。 |
| `A07` | accepted（历史定义） | 未从运行台账绑定 | 2026-07-29 adversarial_reviewer / DeepSeek V4 Pro High 最终 ACCEPT；七个提交关闭 archive TOCTOU、旧 policy fail-stop、Git 配置注入和迟到 dirty/unpushed commit 风险。M1 isp-install 集成保留每个 profile 的 codexModel，92/92 回归通过，未部署。 |
| `A08` | accepted（历史定义） | 未从运行台账绑定 | 2026-07-29 adversarial_reviewer / DeepSeek V4 Pro High 最终 ACCEPT；稳定身份签发、byte-exact 解析、legacy manifest/apply、binding/runtime 投影与事务锁闭环完成。M1 集成同时保留 A08 与 B09 initializer validation，未执行生产身份迁移或部署。 |
| `B01` | integrated（历史定义） | 未从运行台账绑定 | Lagrange Review ACCEPT；commit 已 cherry-pick 到 api/develop，联合模块测试通过。 |
| `B02` | integrated（历史定义） | 未从运行台账绑定 | Feynman 独立 Review ACCEPT；已 cherry-pick 到 api/develop，联合模块测试通过。 |
| `B03` | integrated（历史定义） | 未从运行台账绑定 | 主控第二轮独立 Review ACCEPT：真实 H2/Spring 事务回滚与提交均验证，assignee 和持久状态 fail closed；已集成并推送 api/develop。 |
| `B04` | integrated（历史定义） | 未从运行台账绑定 | Erdos 独立 Review ACCEPT；commit 已 cherry-pick 到 api/develop，联合模块测试通过并推送。 |
| `B05` | integrated（历史定义） | 未从运行台账绑定 | Erdos 第五轮独立 Review ACCEPT；parent gate 并发、byte-exact scope/status、索引与无关任务锁隔离均通过；已集成 api/develop 并推送。 |
| `B06` | integrated（历史定义） | 未从运行台账绑定 | Locke 第三轮独立 Review ACCEPT；ACL 过滤下推、501+ 行可达、UTF-8 边界及 duplicate 异常分类均通过；已在 B05 后集成 api/develop 并推送。 |
| `B07` | accepted（历史定义） | 未从运行台账绑定 | 2026-07-29 DeepSeek V4 Pro High 最终 ACCEPT；首轮六项 P0/P1 与两项遗留 P2 已关闭，317 tests 全绿。MySQL byte-exact 消息查询实库 probe 留待集成门禁。 |
| `B08` | accepted（历史定义） | 未从运行台账绑定 | 2026-07-29 DeepSeek V4 Pro High 最终 ACCEPT；P1 suspended/retired 聚合阻塞及 4 项 P2 已关闭，mapper 55 + service 311 回归与隔离 MySQL 11 项通过。生产 agent_task_meta scoped UNIQUE 漂移登记为集成强制门禁。 |
| `B09` | accepted（历史定义） | 未从运行台账绑定 | 2026-07-29 adversarial_reviewer / DeepSeek V4 Pro High 最终 ACCEPT；四轮提交关闭审计伪造、SQL 归一化碰撞、旧三表升级和 GROUP_CONCAT 截断风险。M1 release_guard 随后发现 initializer bootstrap 计数引用两个旧名，已由 c49d148 修复并用隔离 MySQL 8.0.21 回归关闭。未执行生产回填或部署。 |
| `C01` | integrated（历史定义） | 未从运行台账绑定 | 2026-08-08 C01 已 integrated：Sol integration Writer 以 no-ff merge `76c857ea5f6c9cbf4fbe59d24d695cf75d0a0f4e` 合入 `feat/m2-api-base-20260803`，集成 tree 与 accepted C01 byte-exact；DeepSeek V4 Pro 独立复核 ACCEPT。未推送、未合 develop、未部署。 |
| `C01B` | integrated（历史定义） | 未从运行台账绑定 | 2026-08-15：C01B 已 integrated。R3 源 6cb8a805 / tree bbc727d1 经独立 module-wide 662 与隔离 MySQL 29/29 验证、Sol High fallback 终审 ACCEPT（0 P0/P1/P2），随后以 byte-exact no-ff merge 7a199341 合入 feat/m2-api-base-20260803；未推送、未合 develop、未部署或迁移。 |
| `C01H` | integrated（历史定义） | 未从运行台账绑定 | 2026-08-15：C01H 已 integrated。R2 source 1e374621/tree 1e0b7818 经独立 module-wide 586、initializer MySQL 11/11、完整与补充 probe 验证和 Sol High终审ACCEPT（0 P0/P1/P2），byte-exact no-ff merge 71e243df 合入累计API基线；未推送、未合develop、未部署或迁移。 |
| `C02` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-16：C02-R3 final commit 1f6a27e/tree 50c87ab ACCEPT。Lazy 单 synchronization、rollback-safe savepoint A′、异步有界 wakeup、subscription lease cancellation 与 lifecycle race 已关闭；独立 mapper 95、agent service 524（44 conditional skips）、chat 105、隔离 MySQL 8.0.21 2/2 PASS；Sol High Review 0 P0/P1。C03 ACCEPT 后已随 BE1 merge 21a55db 一次性集成至累计 API 基线，result tree 81533ca。 |
| `C03` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-16：C03-R5 final commit 4d404a3/tree 81533ca ACCEPT。Live-first、周期 durable high-water、bounded paging/continuity/resync、隔离 delivery 与 start/close lifecycle 已关闭；replay 41、DAO 4、独立综合 110、隔离 MySQL 3/3 PASS。BE1 已以 merge 21a55db byte-exact 集成累计 API 基线。 |
| `C04` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C04-R6 final commit f1cb375/tree 7a84a3c ACCEPT。显式 canonical Agent ACL、runtime 投影解耦、单一 RR 只读快照、连续/脱敏 timeline、精确版本字符串、Unicode/padding byte-exact 合同均闭合；独立 mapper 105、service 628（52 skip）、隔离 MySQL 8/8 PASS。已以 merge f8707b2 byte-exact 集成累计 API 基线。 |
| `C05` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C05 final commit 361c3a3/tree 9f8a7fa ACCEPT。Spark 连续三次 clean-worktree stream disconnect 后切换 Sol High；BIGINT wire、partial-write EOF、内部 ACL transaction、matrix-path no-store 三轮独立 Review 闭合。当前树 module-wide PASS、focused 117/117、隔离 MySQL 8/8；C05F ACCEPT 后已以 merge e45ba39 byte-exact 集成累计 API 基线。 |
| `C05F` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C05F commit de9332c/tree 8b80bf3 ACCEPT。workspace/events 共用 immutable exact-scope gate，默认关闭，启动非法配置 fail-fast，请求顺序与 disabled 零分配闭合；module-wide、focused/M1/chat 与独立 binder/wiring probes PASS。已以 merge e45ba39 byte-exact 集成累计 API 基线。 |
| `C06` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C06 final e76b51e/tree e1e3530 ACCEPT。严格 decimal-string/BigInt reducer、snapshot/SSE generation fencing、bounded parser/retry/poll/timeout、Vue whole-state replacement 与 fail-safe cleanup 闭合；34 focused、531 full tests、build、targeted ESLint 和独立 Sol High Review PASS。 |
| `C07A` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C07A final commit 3f92a694/tree 7c47db07 ACCEPT；TaskWorkspace wiring 保持显式 task/actor 输入与 M1 数据流不变，移除 coordinator/assignee/roster/last-selected fallback，并明确 assignment 前清 provenance、完成后不自动授权 workspace、conversation 仅 association-only。 |
| `C07B` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C07B source cdc1b31/tree c4ac81e ACCEPT；TaskWorkspace/Timeline 纯展示 UI 完成。FE2 final HEAD 429d7f4/tree dfc6286。 |
| `C07C` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C07C source caa6cb8/tree c0e6821 ACCEPT；repair 429d7f4 后 FE2 final HEAD/tree dfc6286。nested-reference P1 与 test-global P2 已修复。 |
| `C07` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C07 source e96d4ba/tree 29b1706 ACCEPT；repair b72354c 后 FE2 final HEAD/tree dfc6286。Juyi Hall 集成、显式 actor/link/state/error/retry 回归通过。 |
| `C07F` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：C07F source 45ac8c2/tree 58148f2 ACCEPT；FE2 final HEAD 429d7f4/tree dfc6286。默认关闭 production scan 与 runtime/build 门禁通过。 |
| `C08A` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-21：累计 API base e45ba39/tree 8b80bf3 通过 ancestry/tree/frozen-hash/profile/startup/schema/chat/隔离 MySQL 门禁；两次 broad Gradle aggregate 由宿主 OOM 终止且无断言失败，独立 Sol High Review 评定证据充分并 ACCEPT。 |
| `C08W` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-22：C08W accepted。FE2/C08W follow-up commits 44f5c8e/tree f775657..., fa54ea4/tree dab7ae5..., 8cca8d0/tree ba7ed4f...；requiredAbilities 对齐 C04 JSON String、有界解析、accessible full label、components.d.ts 收敛。最终 merge HEAD 266583f2e59d5f1362ed4d653f58d02b78a0e6b5，tree ba7ed4f167c43b3af8a7f07d34d626308496cd36，parents 6c2f514... + 8cca8d0...，byte-exact。C08 仍保持 draft，不提前 GO。 |
| `C08` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-22：既有旧生产 API 已保持 PID 3382302/start-ticks 2897184880/JAR 8b8f2e7d.../health UP。API drill v3 最终 runner ec88c51c...、MANIFEST 08123fec...、241/241 PASS，覆盖 normal deploy/rollback、failed deploy auto-restore、failed rollback candidate rescue 和 final rollback；schema transitions 6/8、launches 4/5。Combined smoke v3 最终 runner 4b394bf0...、MANIFEST 90bb93f1...、56/56 PASS，覆盖 Chromium/Nginx/backend、snapshot、SSE replay/resync/restart、旧 JWT 和 ACL。DeepSeek 对最终 runner 均 ACCEPT(0/0/0)，Sol High release_guard 最终 GO(0/0/0)。生产 DB/RabbitMQ/candidate deployment、dirty develop/master merge 均 NOT_PERFORMED。 |
| `C09A` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：原 C09A 3450055 ACCEPT 后，合入 agent-skill develop 形成 b99ec209（295 targeted PASS），再合入最新 OAuth develop 50dc8535。OAuth 初审与 Web 合并为 REJECT 0/4/0；critical_worker 在 successor 上关闭 identity trim 与 scope absent 两项 API P1，最终 HEAD cbd4716/tree 6863d7a，OAuth focused 10/10 PASS，sol_reviewer ACCEPT 0/0/0。未部署、未执行生产 DDL/DML/RabbitMQ。 |
| `C09W` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：accepted M2+E13 successor cafcad8 合入最新 OAuth develop 78c8309，形成 74dc245；EOF mechanical follow-up ff7ecb6。OAuth 初审 REJECT 0/4/0 后，critical_worker 关闭 transaction 未绑定配置与 Chat/Hall SSE 匿名 fetch 两项 Web P1，最终 HEAD 549fbd0/tree 7e354b9。修复后 OAuth/SSE/Hall/PWA 32/32、M2 impacted 27/27、默认与 flag-on build PASS；sol_reviewer ACCEPT 0/0/0。未部署、未触碰 dirty web/develop。 |
| `C09` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：最新 API cbd4716/tree 6863d7a 与 Web 549fbd0/tree 7e354b9 已 clean、包含当前 develop parents，并经 OAuth 修复后独立 Review ACCEPT 0/0/0。旧 synthetic tree ded803a 已因修复失效；基于 root HEAD 6d5dfce 两次独立临时 index 均生成 tree 57a7dfb，真实 root index gitlinks 未变化；release_guard GO 0/0/2，仅接受 preparation 并解锁 M3-00 离线安全门禁。 |
| `D01` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：GPT-only D01 accepted。权威表名 agent_command_delivery/agent_outbox_event/agent_consumer_inbox；scoped unique、MEDIUMBLOB+BINARY(32)、retry/lease/CAS/expiry/fence、confirm/return、WAITING_AGENT、replay审计已冻结。独立 conditional initializer 实现 flags-off 零访问、0/3 create+validate、3/3 validate-only、partial/drift fail-closed、无DML/backfill，并拒绝同/跨 schema 任意入向或出向 FK。最终 HEAD 5dcdbcd3/tree e623b9b1，sol_reviewer ACCEPT 0/0/0。 |
| `D02` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：GPT-only D02 accepted。changed legacy assignment 是首批唯一 producer，每个 target 写一条 TASK_INVITE；真实 TASK_ASSIGNED eventId 作为 causationId，deterministic commandId 与 random message/outbox eventId 分离。canonical business/wire bytes+SHA-256、exact duplicate 幂等、conflict fail-closed、DB_SHADOW DEAD marker、flags-off 零访问及 enabled missing-writer fail-closed 已冻结。最终 HEAD 2645ed13/tree 624e3f3a；agent module 831/831、chat normalizer 17/17、隔离 MySQL 8.0.21 原子性矩阵 7/7；sol_reviewer ACCEPT 0/0/0。 |
| `D03` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-24：GPT-only D03 accepted。Relay 采用 unlocked bounded discovery + delivery→outbox 短事务 claim、事务外 persistent/mandatory Rabbit publish、correlated confirm/return 后 fenced settle；四态 admission、exact scope、D04 canonical topology digest、13 个 typed AMQP headers、eventId/deliveryId/raw hash provenance 已冻结。corruption lane 可终态化 poison head；MAX/MAX-1 饱和 quarantine，MAX-2 双 claimant 仅一个 winner，败者零 mutation，ACK 可安全结算到 PUBLISHED/MAX。最终 HEAD 8d822996/tree 098bf948；独立 targeted 46/46、mapper 126/126、service 967（80 environment-gated skipped）、隔离 MySQL 8.0.21 19/19；sol_reviewer ACCEPT 0/0/0。真实隔离 Rabbit smoke 因无安全本地镜像而跳过，禁止宿主 5672 fallback；源码未部署、未开 flag。 |
| `D04` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：ACCEPT。实现 canonical 2 exchanges/5 queues/8 bindings topology、dedicated non-default Rabbit infrastructure、显式 provision、有限 passive existence readiness 与 manual-ACK listener factory；独立验证 57/57 PASS，manifest SHA-256=96fd7d32aba468eacbcf96dfa5d441fd938f0d0cb5c6dafcdcae9e797fb4110e，宿主 Rabbit PID/listeners 前后不变；Sol Review ACCEPT 0/0/0。 |
| `D05` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-24：ACCEPT。实现 strict Rabbit decoder、D04 manual-ACK consumer、D07 Inbox claim/complete、exact ACL/presence、byte-exact WS dispatch、offline WAITING_AGENT、confirmed bounded transient parking及canonical D03 CLAIMED source race；五轮独立对抗审查关闭 publish-before-settle、orphan retry、ACL transient、poison validation/provenance与mapper projection风险。最终 HEAD f50b7062/tree 7688c6e6；targeted 126/126、starter compile PASS、module-wide 1251（1170 pass/81 skip/0 fail）、隔离MySQL13/13；sol_reviewer ACCEPT 0/0/0。生产dispatch仍false，未部署。 |
| `D06` | accepted | `f02bb1167fd0` / `3b5b519c2010` | D06 R8 authoritative ACCEPT 0/0/0 on exact API f02bb1167fd09825b02ec399c077699933b144a6/tree 3b5b519c201047d71eaf212c61fb53deb743ffb3 paired with A06 test-only 4db501816abf/tree 527c02ce9e13. Source Writer released. D08 stale candidate remains non-promotable and must be rebuilt later; no deployment is authorized. |
| `D07` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23：GPT-only D07 accepted。固定 consumer agent-command-dispatch-v1；delivery→outbox→inbox 锁序、raw bytes自算SHA-256、来源证明、exact duplicate prior/in-flight、identity/hash conflict fail-closed、PROCESSING lease/reclaim/fence、expired/stale/terminal stored-shape、DB_SHADOW/flags zero-access 已冻结。claim 将 Inbox+delivery PUBLISHED→CONSUMED 原子提交，complete 将 fenced Inbox+delivery disposition 原子提交；SENT 不等于 RECEIVED。最终 HEAD 8be1e16f/tree 67dcc66b；service878、mapper119、隔离MySQL8.0.21 12/12；sol_reviewer ACCEPT 0/0/0。 |
| `D08` | accepted | `cc5e03205d78` / `0efc5a51dca6` | D08 remains accepted on exact cc5e03205d7842768892c0c962d103a5e6f90022/tree 0efc5a51dca6085936306764d6d302a607e1ba64 with focused ownership-denial evidence 5ae746d20350a332f271cf5809ce3f16a0d1dc45aeea468289d614cdb8099c6e and isolated MySQL restart/concurrency evidence 0af7529498cbc1a806c1e7dd6d999e487cc067aa96458f5ee7d5a6536da36ca3. Cleanup removed only an unregistered stale fixture; no source/test/production action. |
| `D09` | accepted | `2d935f64ccaf` / `f4ff2d9a444b` | Authoritative sol_reviewer 01a03f09-9b7f-7921-baef-3d16d78742e0 ACCEPT P0/P1/P2=0/0/0 on exact 2d935f64/tree f4ff2d9a with fresh isolated MySQL evidence fixture 1737656840f1 and XML 5/0/0/0; R8-2 accepted, R8-3/4 remain forbidden. Dependencies D06/D08/D09 are now accepted, so M3-RG may run read-only. |
| `E01` | draft（历史定义） | 未从运行台账绑定 | null |
| `E02` | draft（历史定义） | 未从运行台账绑定 | null |
| `E03` | draft（历史定义） | 未从运行台账绑定 | null |
| `E04` | draft（历史定义） | 未从运行台账绑定 | null |
| `E05` | draft（历史定义） | 未从运行台账绑定 | null |
| `E06` | draft（历史定义） | 未从运行台账绑定 | null |
| `E07` | draft（历史定义） | 未从运行台账绑定 | null |
| `E08` | draft（历史定义） | 未从运行台账绑定 | null |
| `F01` | draft（历史定义） | 未从运行台账绑定 | null |
| `F02` | draft（历史定义） | 未从运行台账绑定 | null |
| `F03` | draft（历史定义） | 未从运行台账绑定 | null |
| `F04` | draft（历史定义） | 未从运行台账绑定 | null |
| `F05` | draft（历史定义） | 未从运行台账绑定 | null |
| `F06` | draft（历史定义） | 未从运行台账绑定 | null |
| `G01` | draft（历史定义） | 未从运行台账绑定 | null |
| `G02` | draft（历史定义） | 未从运行台账绑定 | null |
| `G03` | draft（历史定义） | 未从运行台账绑定 | null |
| `G04` | draft（历史定义） | 未从运行台账绑定 | null |
| `G05` | draft（历史定义） | 未从运行台账绑定 | null |
| `G06` | draft（历史定义） | 未从运行台账绑定 | null |
| `G07` | draft（历史定义） | 未从运行台账绑定 | null |
| `G08` | draft（历史定义） | 未从运行台账绑定 | null |
| `M3-IR` | accepted | `828ef2e2f35c` / `f7e53c955734` | Authoritative sol_reviewer 01a03f8f-a8df-75a3-a108-ff76f9a95fe2 ACCEPT P0/P1/P2=0/0/0 on exact 828ef2e2/tree f7e53c95 with immutable addendum fc393688, fixture=N/A evidence f1c42469, XML 82/0/0/0, 50 executed tasks and BUILD SUCCESSFUL. M3-RG is now unblocked for one fresh release_guard; no deployment/activation is authorized. |
| `M3-RG` | done | `7f7360e3f65a` / `1bce97d41705` | 已按用户发布优先指令上线：API 运行包 SHA-256 c70a1e348bed6a4293a90fa6ca27cad1c1b6d1a9a77e7f1ac6b2cac93bab1271，127.0.0.1:10018/actuator/health 已返回 UP。后续仅按上线后缺陷处理，不再阻塞已发布功能。 |
