# 案卷阁典籍阅读 — 交付状态补充

> 文档任务 SDD-ARCHIVE-20260906；截至 2026-09-06T09:21:00.295553+08:00。这是审计投影，不可用于 claim/调度。当前状态以唯一运行台账为准。

- 生命周期：`implementing`。归档：仅 AR-20260906-05 / AR-20260906-04 历史发布记录。
- 结论：H01–H05W 已接受，H06 已发布；旧 reader 修复随 Web101ac4c 发布，CORS 补丁也已部署并通过可信/非可信预检，剩余 authenticated adapter/真实阅读闭环未完成，整体不归档。
- 下一步：CORS 五行补丁已独立 ACCEPT 并应用生产，可信 OPTIONS200/非可信来源403 已记录；不重复修补。由现有阅读 Owner 完成 authenticated save/read adapter 回归及读取、进度、书签/手札、关闭重开的业务闭环。

## 需求 / 设计同步

增补用户 UX 要求：点击阅读先进入典籍列表，选择典籍后进入占满可用视口的沉浸阅读；目录默认收起、允许按需展开。浏览器原生全屏受宿主权限约束，不保证微信强制横屏。保留 /archive/v1、exact-scope、CAS/幂等与账户切换 generation fencing。CORS 放行应精确匹配受信 origin/合法 headers，不用通配或移除幂等键绕过。UX 列表/全屏/目录默认收起及 authenticated save/read 闭环仍是待核实要求；CORS 五行补丁则已有独立 ACCEPT 与生产预检证据（可信 OPTIONS200 含幂等键、非可信403无 AllowOrigin），两者不能混称未验证，也不重复修补。

## 任务 / 验收映射

| 任务 | 截止时点记录 | commit / tree | 证据摘要与剩余动作（历史快照） |
| --- | --- | --- | --- |
| `H01` | accepted（历史定义） | 未从运行台账绑定 | R7 independent Review ACCEPT，0 P0/P1/P2；8/8 focused tests、artifact byte equality、HTTP ETag grammar exhaustive probe及feature tree SHA均通过。H01已接受，可进入H02。 |
| `H02` | accepted（历史定义） | 未从运行台账绑定 | R4独立Review ACCEPT且独立MySQL 8.0.21 PASS；120/11/3666/3677、ACTIVE版、并发重入、篡改拒绝和schema drift证据闭合。H02已接受，放行H03。 |
| `H03` | accepted（历史定义） | 未从运行台账绑定 | R7 final commit b4158f7/tree 3839154 ACCEPT。非ASCII progress path在Controller/service幂等前统一404且MySQL零残留；fresh MySQL 8.0.21 exact 1/1、module-wide 161 tests（2 guarded skips）及独立Review 0 P0/P1/P2闭合。H03已接受，放行H04。 |
| `H04` | accepted（历史定义） | 未从运行台账绑定 | R7 final commit 59325d4/tree 2464cc3 ACCEPT。目录/引首/120回阅读、精确继续/滚动、进度串行CAS、书签、私人手札、幂等重放/冲突草稿、responsive/a11y及生命周期闭合；100项定向测试、五文件ESLint、SFC compile、最终production build与独立Review 0 P0/P1/P2通过。 |
| `H05A` | accepted（历史定义） | 未从运行台账绑定 | 2026-08-23 R11 exact tree 完成 final service/mapper、隔离 MySQL 8.0.21 和独立 Review；Raman the 5th ACCEPT，0 P0/P1/P2。R11 用 ASCII-only UTF-8 CHECK 关闭 MySQL 8.0.21 中文 literal metadata 双重编码，同时保持 R9 transaction/SSE/worker blob 不变。 |
| `H05W` | accepted（历史定义） | 未从运行台账绑定 | R3 final commit 0b3d930/tree 2ba166c ACCEPT. Stale same-question stream callbacks, duplicate SSE fields, retry-409 UX, split CRLF parsing and exact 16-segment/8192-byte boundaries are closed; independent 116-test/lint/build verification and Sol High Review 0 P0/P1/P2 passed. H05W accepted and H06 dependency released. |
| `H06` | done | `66f30bc530f9` / `56cc82235e51` | 案卷阁 H06 已随当前 API 发布并通过线上 API 可用性复核。旧离线 ArchiveContentImporterTest gate 需 >=5368709120 字节可用磁盘，当前主机不足；该发布前门禁由用户发布优先决策以实际线上可用性验收替代，根因记录保留，不重跑重型 Gradle。 |
| `JY-BUG-RELEASE-20260905` | done | `101ac4c6a2b4` / `93c561b90b8d` | DEPLOYED and pushedorigin/develop101ac4c: authentic57screen+55readerPASS, productionbuildPASS, independentsourceACCEPT0/0/0, all403deployedfilesexactdigest63f535b7, publicindex+JuyichunkHTTPS200byteexact. NoAPI/foreignprocess/main-dirtycheckoutchanges. Nextaction: refresh/reenterWeChat and manuallycycle3times+close/reopenreading; realdevice/browsercyclesunverified, no falsePASS. |
| `JY-FOLLOWUP-READER-20260906` | implementing | `101ac4c6a2b4` / `93c561b90b8d` | CORS exact5line patch independently ACCEPT and production applied: nginx-t/reloadPASS, legitimate OPTIONS200 includeskey singleallowheaders; untrusted403noAllowOrigin. Main evidence0whiSH. NoAPIrestart/authenticatedsaveclaim. Owner complete realadaptertest. |
| `JY-FOLLOWUP-VERIFY-20260906` | remediating | `101ac4c6a2b4` / `93c561b90b8d` | Bounded new attempt authorized: local exact baseline dist preview + pre-start fake auth/intercepted API, sequential CDP no recursive queue; 3 real canvas cycles. Then integrated build only when notified. |

## 集成与未验证边界

未运行 `sddw pin`、未改变 root gitlinks 或本地 checkout。候选 SHA、源码审查、构建产物、生产激活分别记账；未勾选条目表示尚无逐项验收映射，不能据历史 checkbox 推翻较新的任务证据，也不能无依据批量打勾。

审计快照：`docs/implementation/archive/2026-09-06/execution-snapshot.json`；归档登记：`docs/implementation/archive/2026-09-06/release-records.json`。
