# API 最新语音增量融合：源码接受（2026-10-01）

API `codex/juyiting-multimedia-deliberation` 已精确 FF/push/readback 为 `42d6e7e4196cbde7e0a8fe5a41d3e909d954fc3d` / tree `b9da418a149398f5ddfe551593056b88de465711`。父提交为原 feature `8121e8d8` 和 develop `49a93135`；仅五个语音路径为原 feature 的增量，字节精确等于 develop，不涉及 API followup Owner 的 74 路径。

## 实际证据，而非静态计数

| 阶段 | 实际 XML / 测试 | 使用方式 | 结果 |
| --- | --- | --- | --- |
| Agent bridge | 8 / 57 | 同 exact42d v1 实际结果复用，不是 v3 重跑 | 0 fail/error/skip |
| Chat bridge | 9 / 25 | v3 独立串行执行，exit0 | 0 fail/error/skip |
| Voice | 16 / 129 | v3 独立串行执行，exit0 | 0 fail/error/skip |
| 合计 | 33 / 211 | 分阶段组合，不是一次完整应用测试 | 0 fail/error/skip |

Voice raw 文件沿用 `voice-delta-v2-voice.actual-stdout-stderr.log` 名称：v2 runner 在创建 raw/启动 Gradle 前失败，v3 首次创建该文件。不能因文件名误读为 v2 通过，也不得因此重跑。Voice 实际 63 tasks：6 executed / 57 UP-TO-DATE；Chat 实际 60 tasks：1 executed / 59 UP-TO-DATE。过期 Voice16XML/120 永不计入42d证据。

真实 Redis4 binary 由测试 executor 系统属性传入，contract10/10含 `exactExternalRedis406ExecutesAllServerTimeWritePaths` 与 `realRedisExecutesAtomicTerminalReplayAndTokenMismatchContracts`；使用 owned child，短生命周期 Redis child PID 未输出，不虚报 PID。Main 确认 launcher/orchestrator/daemon 已退出，自有 MySQL Unix/TCP socket/datadir/version/skip-networking/UUID一致、精确 fixture 前缀为空，33测试源及 build/delta hash、候选 clean SHA/tree 均核对。

## 保留失败与边界

v1 combined exit1/daemon registry expiration OOM（Agent57实际通过、Chat/Voice未跑）仍为失败；v2 Chat runner `KeyError: logs` 在 Gradle 前失败仍为失败。v3 仅修顶层 logs alias 并使用已批准独立阶段，没有替换源码、init、AP、heap 或测试范围。分阶段通过不证明宿主OOM长期风险消除。

[便携原件与摘要](integration-evidence-20260928/api-voice-delta-42d-source-accepted/portable-manifest.json)包含33XML、raw/daemon、矩阵/输入/argv、授权、MySQL读回与push回执。`build_origin=local_user_authorized`；无虚构Flow Run，无Provider调用、生产数据修改或部署本特性。

下一步：完成 API followup 包并实际验证，再闭合同会话多 request 发现/旧稿保留、自然讨论与澄清、真实INSPECT、双接应、34产品/29共同桥用例及浏览器验收。当前只接受源码融合，不宣称产品完成或已发布。
