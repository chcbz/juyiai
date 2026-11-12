# 聚义厅 Codex 快速议事与上下文一致性

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：议事上下文连续性与执行热路径。**

### 责任与业务流程
API请求/回合/完成事实；bridge原生会话映射和执行隔离；Web流预览/最终展示。

持久请求→复用适用原生thread→增量流预览→完整最终回复事务→事件更新页面。

### 明确边界
不恢复每消息新进程/全历史重发、不每片查库/重验输入、不把相同thread ID当正文记忆证明；不新建第二聊天引擎。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
新会话不串历史、同会话多轮引用原文、重启续接、取消/失败正确结束、首字与完整回复分段测量。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md) · [当前专项细则](../juyiting-ui-baseline-20261006/optimization/detailed-design.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

2026-09-25快速议事提案与阶段记录，不恢复旧codex exec/新引擎/全历史推送方案；当前原生会话和页级展示遵循现行合同。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



> 文档收口（2026-10-23）：保留上下文/恢复/性能约束与未证实范围；普通议事与执行融合入口看多媒体及技能执行，不重建第二聊天引擎。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


日期：2026-09-25
状态：Ready（详设已完成并通过全面复核，可进入开发与测试；尚未实施、A/B、发布或验收）
范围：`api/chat`、`web` 聚义厅会话、版本化 `codex-ws-agent` 运行时源码与其部署配置。

## Problem

聚义厅普通议事与实际执行目前都进入完整 Codex coding Agent 路径。现有只读审计和历史会话样本表明：

1. 普通聊天会为每条消息启动新的 `codex exec --json` 进程；CLI 启动本身不是主要耗时，但会增加抖动。
2. CHAT 与 COMMAND 共享忙碌状态，执行工作时普通议事会被拒绝或等待，无法形成轻重任务隔离。
3. Agent 收到的 UI metadata 已包含会话范围、目标 Agent 和任务引用，但当前 `resolvePrompt()` 主要只取消息正文；上下文准确性依赖 Codex session 恢复，线程丢失、上下文膨胀、切换工作目录后容易缺少权威业务事实。
4. 当前所谓流式输出是在最终结果产生后按 72 字符切片，不是模型真实增量，用户首屏等待接近完整生成时间。
5. `resume` 长期累积工具历史和输入上下文，历史样本出现明显长尾；业务会话与 Codex 推理线程尚未形成可恢复、可压缩、可验证的上下文快照边界。
6. 当前主机仅 2 CPU、约 3.6 GiB 内存，2026-09-25 复核时根盘使用率 93%、Swap 已使用约 1.5 GiB；不能用无限并发或无限保留线程换取表面速度。

已有约 35 条历史会话的观测样本显示：有效答复完成 P50 约 17.9 秒、P90 约 128 秒、最大约 248 秒；Codex 内部首 Token P50 约 7.5 秒、P90 约 14 秒；CLI/会话启动到首任务事件 P50 约 0.95 秒、P90 约 2.9 秒。这些是历史观测，不是控制变量 A/B，不能作为改造后的承诺值。

## Goals

1. 将普通议事、只读检查和已授权执行分为 `CHAT`、`INSPECT`、`EXECUTE` 三条权威路由；文字分类不得授权执行。
2. 后端从业务数据库和授权资源生成版本化 `Context Snapshot`，Codex thread 只是可丢弃推理缓存；线程丢失后仍可恢复完整、授权且可追溯的上下文。
3. 先完成 Fast CHAT 引擎选型验证，再落地低推理、独立小工作目录的快速 CHAT 路径；只有候选引擎证明模型侧确实不暴露工具时才能称为“无工具”，否则必须标记为“无副作用工具/只读受限”。
4. 将聊天与重执行分离调度；性能慢只记录和排队，不因任意 SLO 取消真实工作。
5. 在收益验证后接通长期 app-server `turn/start` 与真实增量事件，移除最终文本伪切片。
6. 对需要代码、日志、文件或精确 Git 状态的问题使用只读精确快照；对写入和部署继续复用现有正式执行授权、幂等、工作树和回执链路。
7. 用端到端时间戳、资源指标和上下文正确性夹具形成可重复 A/B；区分事实、观测、估算和验收结果。

## Non-goals

- 不承诺模型回答百分之百正确；本专题保证上下文完整性、授权边界、版本一致性和可追溯性。
- 不允许 `/chat/stream`、关键词、模型分类或前端按钮字段直接产生代码修改、部署、付费调用或生产数据写入。
- 不重写现有个人工作空间、任务执行、正式交付、返工和验收状态机。
- 不把业务聊天历史存储迁移到 Codex thread；不把 Codex JSONL 当作业务事实源。
- 不以 1 秒、3 秒或其他未经实测推导的阈值拒绝、取消或截断请求。
- 不在本专题中扩大 Agent 文件权限、跨 owner/tenant/client 读取范围或共享 CODEX_HOME。
- 不直接修改 `/home/isp/apps/codex-ws-agent/` 部署副本作为源码；运行时变更必须来自 `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/`。

## Scope

### API (`api/chat` 为主；`api/agent` 仅用于能力/版本协商的只读调用)

- 权威路由器和 capability/version 协商。
- Context Snapshot 聚合、版本向量、哈希和最小审计记录。
- 会话消息、任务状态、执行状态、参与者和输入引用的 owner/client/tenant 级校验。
- 新增可选请求字段与 Agent 下行协议字段，保持旧客户端兼容。
- `turnId`、`deltaSeq`、最终消息单次持久化、重放和去重。
- 端到端阶段时间戳和慢请求观测。

### Web

- 继续只提交用户输入、选择引用和最后可见版本，不上传前端缓存作为权威历史。
- 展示真实阶段：排队、正在理解、只读检查、执行状态、生成中、完成、上下文已更新。
- 对 delta 按 `turnId + deltaSeq` 去重；最终消息替换临时增量，不重复落屏。
- CHAT 中出现写入意图时展示办理建议/执行确认入口，不直接执行。

### Agent runtime

- `runFastChat`、`runReadOnlyInspection`、`runConfirmedCommand` 三个明确入口。
- 快速聊天引擎对比与 capability/schema readback：直接轻量模型/Responses 路径、受限 Codex app-server、现有后端内置模型路径。
- 快速聊天独立模型参数、受验证的工具暴露策略、只读小 workdir。
- 分离 chat/inspect/command lane 和全局资源限制器。
- 长期 app-server 的 `thread/start/resume`、`turn/start`、delta、final、interrupt、unsubscribe 与恢复适配。
- Codex thread 映射、滚动、压缩、归档和磁盘回收；不得删除仍被业务状态引用或尚未形成可靠摘要的记录。
- app-server 服务端请求（审批、权限、工具、用户输入）的显式拒绝/转译策略，禁止静默批准写入或网络访问。
- CODEX_HOME、认证令牌、进程身份、配置版本、模型额度和调用成本的运行治理。

## Constraints and risks

- root、api、web 当前均有大量其他任务改动；实施必须使用独立 worktree、精确路径所有权和 exact SHA，不覆盖现有工作。
- `chcbz/isp-install` 是独立版本仓库，必须作为第三个实施仓记录源码、测试和发布哈希。
- 当前 2 核主机先进行单 Profile 小流量试点；并发量和常驻进程数量依据 RSS/CPU/Swap 实测扩大，不凭空设置容量承诺。
- CHAT/INSPECT 的降级只能回到现有安全路径或明确提示；不能为了速度绕过权限、幂等、锁、事务、执行授权或工作区隔离。
- 上下文摘要可能遗漏事实，必须保留 source vector、近期原始消息和可重建路径；摘要不能成为唯一授权依据。
- app-server 协议和 CLI 版本必须通过 capability 检测适配，不能假设所有部署版本行为一致。
- 2026-09-25 本机 `codex-cli 0.156.0` 生成的 app-server schema 提供 `sandboxPolicy`、`approvalPolicy`、`model`、`effort` 等字段，但未证明存在关闭全部内建工具的统一开关；Fast CHAT 的“无工具”结论必须由独立 spike 和实际 tool catalog/readback 证明。
- Codex 会从 cwd/CODEX_HOME/项目层读取指令和配置。CHAT 只能加载运行时托管指令；INSPECT 中仓库指令与用户资料必须分级，任何资料内容都不能因文件名或目录位置被提升为系统/开发者指令。
- 接受、运行、最终生成、最终持久化和发布是不同状态；`turn/start` 结果未知时不得盲目重放，EXECUTE 尤其不能因网络重试重复执行。
- 群聊中每个目标 Agent 使用独立 snapshot、turn 和 thread binding；不得共享 Codex thread 或把其他 Agent 的私有工具结果隐式注入。
- 数据删除、保留期、身份切换和授权撤销必须使 thread binding 与快照缓存失效；Codex session/log 不能成为绕过业务删除的副本。
