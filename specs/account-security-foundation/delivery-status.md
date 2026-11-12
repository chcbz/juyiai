# 账号安全基础与全局撤销 — 交付状态补充

> 文档任务 SDD-ARCHIVE-20260906；截至 2026-09-06T09:21:00.295553+08:00。这是审计投影，不可用于 claim/调度。当前状态以唯一运行台账为准。

- 生命周期：`implementing`。归档：未归档。
- 结论：Cookie 修复包已在运行台账行政收口，但只记录 manifest 校验，缺 exact Git 绑定与 credentialed 生产验收；不能把整个账号安全需求标为完成。
- 下一步：补齐 auth_epoch/撤销、生产 OAuth client 与迁移的逐项验收及实际版本映射。

## 需求 / 设计同步

保持 uid/token_kind、ACTIVE/auth_epoch、Bearer 主体、CAS、Cookie/CORS 原合同；本次不放宽身份/事务/迁移条件。

## 任务 / 验收映射

| 任务 | 截止时点记录 | commit / tree | 证据摘要与剩余动作（历史快照） |
| --- | --- | --- | --- |
| `ASF-COOKIE-P1` | done | `未绑定` / `未绑定` | 按用户继续推进/发布优先指令收口：已核对发布目录候选 manifest SHA-256=017e147eadafda4f87b35b3b4fa6bbafaf27334614452adefcccef37124cfc39 及 manifest-root SHA-256=a6e085773b75a100230cf4a32b59353e18000e479bdf9dfa3e8b055990a58845，清单校验通过；不执行 credentialed/生产 smoke。 |

## 集成与未验证边界

未运行 `sddw pin`、未改变 root gitlinks 或本地 checkout。候选 SHA、源码审查、构建产物、生产激活分别记账；未勾选条目表示尚无逐项验收映射，不能据历史 checkbox 推翻较新的任务证据，也不能无依据批量打勾。

审计快照：`docs/implementation/archive/2026-09-06/execution-snapshot.json`；归档登记：`docs/implementation/archive/2026-09-06/release-records.json`。
