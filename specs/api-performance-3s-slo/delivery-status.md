# API 3 秒性能治理 delivery status

更新：2026-09-11。本文件是状态投影，当前 owner/gate 仅取 `docs/implementation/TASKS.yaml#runtime_ledger_json`。

## 已交付的有界切片

- 生命周期：`implementing`，整体验收尚未完成。SDD 合同独立 R4 审查 ACCEPT0/0/0。
- `PERF-A02-LOG`：安全慢日志/单调计时，独立 source + 6 项定向单测 ACCEPT。
- `PERF-A01-HIST`：HTTP histogram/1s、2.5s、3s buckets/URI 上限，独立 source + 5 项定向测试 ACCEPT。
- 两项 API 切片已推送 `codex/perf-api-integration-20260911`：`5571d183fe7c612f2d5ebb272548aa5bfad77e90` / tree `b993a925464701b5a17c93461cf3f558036f5d13`，未发布。
- `PERF-BUILD-01`：上述合并 API 的日志 selector 经真实 offline Gradle 6/6PASS、零跳过，独立证据审查 ACCEPT0/0/0。非敏感占位属性绕过历史 publishing 配置缺失；不是完整模块、starter/metrics测试或启动证明。
- `PERF-01-TOOLS`：离线扫描/严格对账工具最终 R4 ACCEPT0/0/0，`43e0e46f8d9a07797713adb432c3bcab770dd8b0` / tree `e0a9c30fa385c1ff0ae42d2f70f97dd5d87bc3b9`。修复自定义注解漏检、外部可信工件绑定和哈希/解析竞态；26 项实际单测、真实 CLI 合成正反例通过。已推送工具分支，并 byte-exact 合入 `codex/perf-sdd-20260911`。
- R4 验证包装器及元数据脚本各有一次失败；原始命令结果/源码身份/工件 hash 经 main 与独立 reviewer 复核，足以支持有界源码验收。未伪造成功 wrapper 或 verifier-cache HIT；失败历史保留。

- `PERF-BUILD-02`：同一 exact API 的完整应用主源码图经真实 offline `:starter:classes` 编译通过，34m14s、80 actionable（75 executed /5 up-to-date），独立 R2 ACCEPT0/0/0；测试 **NOT_RUN**，不是 bootJar/启动/性能验收。
- `PERF-CAPTURE-PREP`：隔离采集前置分析完成并经过只读复核；现有 Actuator 可用于严格 namespace 内采集，但不可在宿主机/生产暴露 mappings。配置、夹具、运行工件和隔离预检仍待实施。

## 尚未完成

- 真实 grey/prod-profile 框架/管理面清单、受保护运行时采集、registry 全覆盖对账。
- 完整测试、可运行安全工件、应用启动、跨链路 trace/inflight/依赖预算、隔离性能基线、热点查询优化、逐接口 3 秒达标及发布。
- 旧 checkout 的42 Controller/约401 mapping，及后续 exact API `014fb7e` 的440条 supported mapping，均只是历史/非零诊断，不是 accepted 全量接口清单。

## 下一步

用户已明确改为低资源直接发布：不新建隔离环境、不本地重构建或压测，先将已验收日志/指标切片交由现有发布 Owner 做云端制品核验和发布，上线仅轻量 smoke/被动观测。当前等待同一 API 发布任务协调，尚未发布；完整清单、热点优化及3秒 SLO 仍未验收。

证据与失败矩阵：`../../docs/implementation/handoffs/PERF-CONTINUE-R3-20260911.md`；此前证据见 `PERF-FIRST-BATCH-20260911.md` 和 `PERF-VERIFY-R2-ROOT-CAUSE-20260911.md`。

本轮构建证据、元数据补证和保留失败历史：`../../docs/implementation/handoffs/PERF-RUNTIME-PREP-20260911.md`。仅补证、未重复构建；后采集的 orchestrator hash 不冒充执行前证明。

最新发布授权与协调入口：`../../docs/implementation/handoffs/PERF-DIRECT-RELEASE-20260911.md`；此前隔离预检执行计划暂停，不再作为本轮实现任务。
