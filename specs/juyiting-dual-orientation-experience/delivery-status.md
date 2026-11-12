# 聚义厅横竖屏体验 — 交付状态补充

> 文档任务 SDD-ARCHIVE-20260906；截至 2026-09-06T09:21:00.295553+08:00。这是审计投影，不可用于 claim/调度。当前状态以唯一运行台账为准。

- 生命周期：`implementing`。归档：仅 AR-20260906-04 历史发布记录。
- 结论：O00–O04 已源码接受；高度修复已发布但台账仍有 integration 缺口，旧屏幕修复已发布；新循环/屏幕 follow-up 尚未验收。
- 下一步：沿当前 Owner 完成 screen 修复及真实三次横竖屏循环、canvas 清理/重建验证，并核对高度修复合入记录。

## 需求 / 设计同步

保留真实 viewport 方向、竖屏轻应用/横屏地图、snapshot destroy/remount、同一业务状态及显式 Agent。新修复需覆盖重复进出、延迟资源加载、重复注册/残留 canvas；不得借模拟测试宣称微信真机通过。

## 任务 / 验收映射

| 任务 | 截止时点记录 | commit / tree | 证据摘要与剩余动作（历史快照） |
| --- | --- | --- | --- |
| `O00` | accepted | `d289f120cbdc` / `afa783a95015` | O00 remains authoritative ACCEPT 0/0/0 on exact d289f120/tree afa783a9. Its clean registered worktree was safely removed non-force, freeing 256266240 bytes while preserving branch refs/heads/codex/o00-juyiting-web-convergence and commit/tree. No source/test/process/deploy action. |
| `O01` | accepted | `832dc9fd5c80` / `27b5c44904a2` | O01-R5 authoritative ACCEPT 0/0/0 by Godel the 3rd 01a03a64-b677-7093-9418-d6f100ab512f on exact 832dc9fd/tree 27b5c449. Dependency-free R4/R5 probes passed; one missing-timestamp legacy probe is obsolete under the accepted R4 fail-closed contract. Official Mocha remains pre-load infra-blocked with 0 executions. O02 may be claimed from this exact base. |
| `O02` | accepted | `fd515acf22d6` / `78779a6fc8a1` | O02 remains authoritative ACCEPT 0/0/0 on exact fd515acf/tree 78779a6f. Two fail-closed cleanup probes removed nothing; /tmp/o02-verifier-ad33b112b3f1e6a5664b0dde66eea5088d2abd31 is intentionally preserved. O03 progression remains independent; no source/test/deploy action. |
| `O03` | accepted | `0f8c243a7e32` / `ada2b911ff85` | O03 R5 authoritative ACCEPT 0/0/0 by unique sol_reviewer 01a04065-60c8-7821-a10f-e6faa58a27ac on exact 0f8c243a/tree ada2b911. Accepted evidence: V1 9/9 selectors, 144 identities, imports13 and zero resources; V2 16/0; V3 COW bundle build GO with donor/O03 identity and cleanup PASS. Owner released; O04 dependency is now satisfied and may enter read-only preparation. |
| `O04` | accepted | `965d60393fcc` / `f31118c5b522` | Fresh independent sol_reviewer 01a0467e-ecd5-7d20-a776-cbb39c6d5a32 ALLOW P0/P1/P2=0/0/0 on exact O04 commit 965d60393fcc589f691dfa1533e4855b5c13ff20/tree f31118c5b522ddbf3c4355abc466323030d7fd0f. Accepted R5 COPY_PASS key 3a75e513c20a9ad424fb3bbb68d1a14c408d57a3dada2f2d67980e6f6c388756 (23458 entries, digest c33a60be47b3a234669de2f4706ba0cf7d1a920dcff695b5283c83969cd6917d) and Gate 12.2 key 5c8bf63e8c4432e807d33b7771dcb8ea58edda784b3eb69eb8a0f6b0972558a9/artifact SHA 89d35d12c7cf60baedbdc5ef8d3638cf4daeb5377c77fde0fdec0ed209a34e8b/result 56/0/0. Durable contract ends at fresh Gate 12.2 review; no speculative Gate 12.3 is authorized. Owner released; no production action. |
| `O01-LANDSCAPE-HEIGHT` | accepted | `7872fc68a340` / `d89936e967ae` | Fresh authority Godel ACCEPT0/0/0 on7872fc68/d89936e9; focused2/2, build6m19s, CDP20/20 PASS. /tmp/o01-r3-authoritative-accept.txt. Source complete; exact artifact activation authorized separately. |
| `O01-LANDSCAPE-HEIGHT-RELEASE` | done | `7872fc68a340` / `d89936e967ae` | Production release evidence unchanged: manifest827f5fc7, focused2/2, CDP20/20, HTTPS42/42. On 2026-09-10, remote `develop` `24e5e5d` was independently confirmed to contain both `7872fc68` and former baseline `1488e844` as ancestors; the stated divergent-merge wait was stale. No rebuild, redeploy, backend, or voice change. |
| `JY-BUG-RELEASE-20260905` | done | `101ac4c6a2b4` / `93c561b90b8d` | DEPLOYED and pushedorigin/develop101ac4c: authentic57screen+55readerPASS, productionbuildPASS, independentsourceACCEPT0/0/0, all403deployedfilesexactdigest63f535b7, publicindex+JuyichunkHTTPS200byteexact. NoAPI/foreignprocess/main-dirtycheckoutchanges. Nextaction: refresh/reenterWeChat and manuallycycle3times+close/reopenreading; realdevice/browsercyclesunverified, no falsePASS. |
| `JY-FOLLOWUP-SCREEN-20260906` | remediating | `21a44c79c873` / `ad1c596a6443` | Run one known30sec tsx baseline selector + changed component file with logs/sourceSHA/exit; source review continues independent; no source edits without reviewer handoff |
| `JY-FOLLOWUP-VERIFY-20260906` | remediating | `101ac4c6a2b4` / `93c561b90b8d` | Bounded new attempt authorized: local exact baseline dist preview + pre-start fake auth/intercepted API, sequential CDP no recursive queue; 3 real canvas cycles. Then integrated build only when notified. |

## 集成与未验证边界

未运行 `sddw pin`、未改变 root gitlinks 或本地 checkout。候选 SHA、源码审查、构建产物、生产激活分别记账；未勾选条目表示尚无逐项验收映射，不能据历史 checkbox 推翻较新的任务证据，也不能无依据批量打勾。

审计快照：`docs/implementation/archive/2026-09-06/execution-snapshot.json`；归档登记：`docs/implementation/archive/2026-09-06/release-records.json`。
