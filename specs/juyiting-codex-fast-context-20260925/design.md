# 聚义厅 Codex 快速议事与上下文一致性详设

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：议事上下文连续性与执行热路径。**

### 最小责任链
API请求/回合/完成事实；bridge原生会话映射和执行隔离；Web流预览/最终展示。

持久请求→复用适用原生thread→增量流预览→完整最终回复事务→事件更新页面。

### 实施约束
不恢复每消息新进程/全历史重发、不每片查库/重验输入、不把相同thread ID当正文记忆证明；不新建第二聊天引擎。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

2026-09-25快速议事提案与阶段记录，不恢复旧codex exec/新引擎/全历史推送方案；当前原生会话和页级展示遵循现行合同。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



日期：2026-09-25
状态：Ready；架构、合同与实施排序已通过全面复核，可按 `tasks.md` 进入开发与测试；尚未实现、A/B、发布或用户验收。
权威范围：本目录 `spec.md`、本文件、`tasks.md`、`acceptance.md`、`integration.yaml`。

## 1. 决策摘要

本方案不把“持久 app-server”作为第一优先级。现有证据表明，单独去掉 CLI 启动实测只能节省约 1–3 秒，无法解释或消除 18 秒中位数和分钟级长尾。优先顺序为：

1. **先建立端到端观测和基线**，防止把推算当作实测。
2. **先补权威 Context Snapshot 与 CHAT/INSPECT/EXECUTE 路由边界**，否则快速模型只会更快地产生缺上下文答案。
3. **先用 spike 决定 Fast CHAT 引擎，再上线受验证的快速 CHAT 与轻重 lane 分离**；不能把 read-only sandbox 误写成“工具已禁用”。
4. **随后接入精确只读 INSPECT**，解决不同工作目录和代码内容不可见问题。
5. **最后把成熟路径迁入长期 app-server 并接真实 delta**；其主要价值是流式、预热和稳定 thread，不是单纯省启动时间。
6. **在业务数据库成为唯一上下文事实源后再启用 thread 滚动、压缩和回收**，避免因清理 Codex 缓存造成业务历史丢失。

任何聊天文本、关键词或模型判断都不能授权执行。实际执行仅接受现有正式执行链路产生的持久 `command.dispatch`/execution/work item 事实；CHAT 最多生成办理建议或执行草稿。

## 2. 证据等级与当前结论

### 2.1 已由代码或现场确认

| 事实 | 当前证据 |
| --- | --- |
| 普通聊天走 `codex exec --json`，并按会话映射 `resume` | `agent-client.mjs` 的 `buildCodexArgs`、`runCodex` |
| UI 已发送 selected Agent、参与者、selected task 等 metadata | `web/src/composables/juyiting/useHallConversation.js` |
| API 会重建可信 scope metadata | `JuyitingAgentRelayService.trustedConversationMetadata` |
| Agent runtime 最终 prompt 主要只取 `message.content/prompt/instruction` | `agent-client.mjs:resolvePrompt` |
| 输出完成后才按 72 字符切片 | `agent-client.mjs:buildReplyChunks` |
| CHAT 与 COMMAND 共用 `isBusy=chatActive \|\| commandActive` | `AgentMessageProcessor` |
| managed host 只执行 `initialize → account/read → thread/start`，没有 `turn/start` | `managed-host.mjs` 注释与实现 |
| 当前 managed host 预热 thread 使用 `approvalPolicy=never` 与 `sandbox=workspace-write`；虽然尚未发起 turn，但该配置不能直接复用于 CHAT | `managed-host.mjs:initializeHostingEngine` |
| 主机 2 CPU、内存紧张、Swap 在用、根盘 93% | 2026-09-25 现场只读复核 |

### 2.2 历史观测，不是控制变量实验

| 指标 | 约 35 条既有会话样本 |
| --- | ---: |
| 有效答复完成 P50 | 17.9s |
| 有效答复完成 P90 | 128s |
| 最大值 | 248s |
| Codex 内部 TTFT P50 | 7.5s |
| Codex 内部 TTFT P90 | 14s |
| CLI/会话启动到首任务事件 P50 | 0.95s |
| CLI/会话启动到首任务事件 P90 | 2.9s |

这些数字证明当前存在长尾、上下文膨胀和宿主资源压力，但不能直接证明某项改造的因果收益。

### 2.3 仍属估算

- 持久 app-server 单独节省约 1–3 秒。
- 快速 CHAT 首个有效内容约 6–12 秒。
- 快速 CHAT + app-server + 真流式约 4–8 秒。

以上只用于排优先级，不写入发布验收门槛。实施后必须用同输入、同模型、同 Agent、同资源窗口的 A/B 替换估算。

### 2.4 2026-09-25 官方协议与本机 schema 复核

- 官方 app-server 文档确认 `thread/start`、`thread/resume`、`turn/start`、`turn/interrupt`、`thread/unsubscribe`、`thread/compact/start`、`thread/archive` 及 `item/agentMessage/delta` 等能力，并明确存在命令、文件修改、权限、动态工具和用户输入等服务端请求。
- 本机 `codex-cli 0.156.0` 已用 `codex app-server generate-json-schema` 生成临时 schema 并核对：`ThreadStartParams` 支持 cwd/model/approval/sandbox/config/instructions，`TurnStartParams` 支持 `clientUserMessageId`、cwd/model/effort/approval/sandboxPolicy 等。
- 该 schema 的 `readOnly` sandbox 可配 `networkAccess=false` 并阻止文件写入，但没有发现一个已证明能关闭 shell/读取等全部内建工具的统一 `chatToolsEnabled=false` 字段。`tools` 配置主要覆盖 web search 或 connector/app 工具，不能据此推导内建工具完全不可见。
- 本次临时生成的合并 v2 schema SHA-256 为 `995fc3b8f8c469f6787e8fc5be4038c4f31359025edd8480b862e83355f3bf3b`；它用于本次设计证据，实施仍需对实际部署 binary 重新生成并绑定 digest。
- 因此原设计中的“无工具 Fast CHAT”是未证实假设，现改为独立选型门禁。schema 只证明本机版本字段形状，不替代部署版本锁定、运行时 tool catalog 和负向行为测试。

## 3. 成效、成本、风险优先级

评分为 1–5 的相对排序，不是运行时硬门槛；Owner-day 是设计阶段粗估，不含排队、发布等待和未知迁移返工。

| 工作包 | 用户成效 | 直接性能收益 | 工程成本 | 主要风险 | 优先级 | 粗估成本 |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| M0 端到端时间戳与可重复基线 | 3 | 1 | 1 | 指标高基数/泄露正文 | P0 | 1–2 owner-day |
| M0.5 Fast CHAT 引擎/工具暴露 spike | 5 | 4 | 2 | 错把 read-only 当 no-tools、选型返工 | P0 | 2–4 owner-day |
| M1 权威路由 + Context Snapshot V1 | 5 | 2 | 4 | ACL、过期上下文、prompt 变大、群聊串线 | P0 | 5–8 owner-day |
| M2 受验证的 Fast CHAT | 5 | 5 | 3 | 误路由、低推理质量、额度/成本漂移 | P1 | 3–6 owner-day |
| M3 chat/inspect/command lane、持久 turn 与公平排队 | 4 | 4 | 4 | 竞态、资源争用、未知受理、重复执行 | P1 | 4–6 owner-day |
| M4 精确只读 INSPECT 快照 | 4 | 3 | 4 | 路径越权、指令注入、SHA/manifest 漂移 | P1 | 5–8 owner-day |
| M5 长期 app-server + 真 delta | 4 | 2（完成时间）/5（首屏体验） | 5 | 协议适配、服务端请求、进程恢复、重复 final | P2 | 6–10 owner-day |
| M6 摘要、保留、thread 滚动/压缩/归档 | 4 | 3（长尾） | 4 | 摘要遗漏、隐私删除不完整、误删缓存 | P2 | 4–6 owner-day |
| M7 三 Profile 扩量与容量/成本调优 | 3 | 2 | 2 | 2 核宿主过载、额度争用 | P3 | 2–4 owner-day |

全面复核后的整体粗估：**32–54 owner-day**。M1–M4 可由 API/Web/Agent Runtime 分仓并行，但同一工作包只有一个实现 Owner；正式发布以 exact SHA、测试、制品和健康证据为准。

### 3.1 为什么不是先做 app-server

- 已观测启动中位开销约 0.95 秒，低于模型 TTFT 和完整生成时间。
- 当前没有真实 delta；即使常驻进程，若仍等待 final 后切片，用户体感改善有限。
- app-server 引入长期进程、thread 生命周期、协议版本和恢复复杂度，成本高于快速 CHAT。
- 因此 app-server 应建立在路由、上下文和 lane 已稳定的基础上。

### 3.2 为什么 Context Snapshot 必须早于快速 CHAT

当前 UI metadata 虽已到达 Agent，但没有形成完整模型输入。若直接改低推理/无工具模型：

- 任务状态、参与者、决定和资料版本可能不可见；
- 新 thread 或进程重启后只能看到当前一句话；
- 模型可能从工作目录或旧 thread 猜测事实。

快速路径必须以“后端提供权威事实、模型不得自行猜测”为前置。

## 4. 目标架构

```text
Web 聚义厅事项/议事界面
  │  content + conversationId + selected refs + clientSeenVector
  ▼
Chat API
  ├─ 身份、owner/client/tenant、conversation generation 校验
  ├─ Interaction Router
  ├─ Context Snapshot Builder
  ├─ 消息持久化 + source vector/high-watermark
  └─ Agent Relay
        │
        ▼
Codex Agent Runtime（每 Profile 独立 CODEX_HOME）
  ├─ CHAT lane    → 已验证引擎、小 workdir、低推理、无副作用
  ├─ INSPECT lane → 精确只读 snapshot/manifest
  └─ COMMAND lane → 既有持久 inbox、幂等、隔离 worktree
        │
        ▼
Codex app-server adapter（M5 后启用）
  ├─ thread start/resume
  ├─ turn/start
  ├─ agent message delta
  ├─ final/interrupt/unsubscribe
  └─ compact/archive lifecycle
```

业务数据库保存消息、任务、执行和正式成果；Agent runtime 的 thread 只保存推理缓存。任何 thread 丢失都不得导致业务事实丢失或错误恢复到其他会话。

## 5. 权威路由

### 5.1 路由类型

| 模式 | 用途 | 工具/文件 | 写入能力 |
| --- | --- | --- | --- |
| `CHAT` | 普通问答、任务状态解释、方案讨论、澄清 | 首选经证明无模型工具的引擎；否则仅允许无副作用/只读受限且必须标注 | 无 |
| `INSPECT` | 查看授权文件、日志、附件、测试输出、精确 Git 快照 | 只读 manifest 范围 | 无 |
| `EXECUTE` | 修改、构建、测试、部署或产生正式成果 | 既有完整工具与隔离工作树 | 仅现有正式授权范围 |
| `CHAT_STATUS` | 执行中查询状态或补充非冲突说明 | 后端结构化状态 | 无；不启动第二次执行 |

### 5.2 决策顺序

```text
1. 收到现有正式执行链路的有效 command.dispatch / execution fact
   => EXECUTE

2. 同一任务已有执行运行中
   => CHAT_STATUS 或记录补充说明
   => 不重复 dispatch

3. 请求需要读取已授权文件、日志、附件或 Git 内容
   => INSPECT

4. 其他情况
   => CHAT
```

以下内容不能授权 EXECUTE：

- 用户文本中的“执行、修改、部署、继续”；
- 前端 `interactionMode=execute`；
- 选择 Agent、任务或上传文件；
- 模型判断“需要工具”；
- 同一会话之前执行过工作。

用户在聊天中提出写入请求时，CHAT 返回办理建议或已有 Hall Draft；真正执行继续复用 `/agent/hall/drafts/{id}/submit`、个人工作空间 execution 或其他现有权威入口，不在 `/chat/stream` 新造旁路。

### 5.3 分类器边界

- 规则和模型分类器只能产生 `routeProposal`。
- 后端验证授权资源后才能将 proposal 提升为 INSPECT。
- 分类器永远不能将聊天提升为 EXECUTE。
- 分类不确定时默认 CHAT；CHAT 必须明确“需要只读检查/确认办理”，不得假装读过文件或完成执行。
- 默认 CHAT 和带已授权 input refs 的 INSPECT 优先用确定性规则，不在每条消息前串行增加一次 LLM 分类调用。若引入模型分类器，必须证明其额外时延/成本，并且超时或失败回到规则结果。

### 5.4 多 Agent 群聊与回复归属

一个业务 conversation 可以有多个目标 Agent，但不能因此共享推理线程：

- 一个用户发送动作产生稳定 `requestId` 和一条共享 user message；API 为每个 `targetAgentId` 创建独立的子 `turnId/dispatchId/contextSnapshotId`。各快照包含同一消息高水位，但 `agent`、capability、可见 input refs 和 thread key 分别计算。
- 目标列表由已持久化 conversation scope 与服务端 roster/任务关系重建；前端 mention 只作为候选。
- 每个 Agent 只能看到该业务会话中允许共享的已提交消息。其他 Agent 的私有 INSPECT 结果、执行工作区、内部 trace 和未发布草稿默认不可见；若需共享，必须先形成 owner 可见的正式消息或显式引用。
- 各 Agent final 独立持久化并携带 `replyToMessageId/targetAgentId/dispatchId`。展示顺序按服务端提交序列，不按客户端到达时间重排；迟到回复仍标注所依据的 snapshot 版本。
- 父 request 状态由子 turn 聚合为 `RUNNING/PARTIAL/COMPLETED/FAILED/CANCELLED`；一个 Agent 失败不回滚其他 Agent 已持久化回复，也不把部分完成伪报为全部完成。
- 同一 Agent/同一 conversation 维持单 turn；不同 Agent 可在资源允许时并行，但公平调度不能让一个群聊耗尽全部 chat lane。
- thread key 必须包含 Agent ID，禁止多个角色共用一个 Codex thread，以免 persona、历史或工具结果串线。

## 6. Context Snapshot V1

### 6.1 权威来源

| 上下文 | 权威来源 | 前端作用 |
| --- | --- | --- |
| 当前用户和租户/客户端 | 服务端认证上下文 | 不可覆盖 |
| 会话范围、参与者、目标 Agent | owned conversation + scope service | 仅发送选择提示 |
| 消息历史 | chat_message 已提交记录 | 只报告最后可见 high-watermark |
| selected task | owner-scoped task 查询 | 仅提交 task ref |
| 执行状态 | execution/work item authoritative state | 仅展示与查询 |
| 附件/文件版本 | owner-safe link + version/hash | 仅提交 file/version ref |
| Git/工作区 | server-issued manifest/tree SHA | 不接受任意客户端路径 |
| 已形成决定 | 结构化 decision/summary 记录 | 可建议新增，不能覆盖旧事实 |

### 6.2 Source Vector

不依赖单一前端 revision。每个快照记录：

```json
{
  "conversationGeneration": 3,
  "messageHighWatermark": "9223372036854001001",
  "taskRevision": 17,
  "executionRevision": 5,
  "bindingVersion": 9,
  "summaryRevision": 12,
  "workspaceTreeSha": null
}
```

不存在的维度为 `null`。所有 Long ID 通过字符串传输，避免 JavaScript 精度损失。可信内部边界可对 canonical JSON 计算 SHA-256；若 digest 需要发送到 Web、跨服务日志或其他较低信任边界，使用带版本的 HMAC-SHA-256 或仅暴露不透明 snapshotId，避免低熵事实被字典枚举。任何 hash/HMAC 都不是授权凭证。

Canonical 规则固定为：UTF-8、对象 key 字典序、数组保持业务顺序、数字不得用浮点承载 ID、时间统一 epoch millis 或 RFC3339（同一字段只选一种）、缺失字段与显式 `null` 不混用。API 与 Agent 使用同一 golden fixture 验证 digest；HMAC 记录 `digestVersion/keyId`，轮换期间允许双读但只写新版本。

### 6.3 Context Envelope

```json
{
  "schemaVersion": "1",
  "contextSnapshotId": "ctx_...",
  "contextHash": "sha256:...",
  "sourceVector": {},
  "interactionMode": "CHAT",
  "conversation": {
    "id": "401",
    "scopeType": "task",
    "scopeKey": "399",
    "summary": "...",
    "decisions": []
  },
  "actor": {
    "displayName": "寨中来客"
  },
  "agent": {
    "agentId": "...-wuyong",
    "personaName": "智多星",
    "capabilities": []
  },
  "task": {
    "id": "399",
    "title": "...",
    "status": "IN_PROGRESS",
    "assignedAgentId": "...",
    "progress": "...",
    "blockers": []
  },
  "execution": {
    "executionId": null,
    "state": null,
    "lastAuthoritativeEvent": null
  },
  "recentMessages": [
    {"id": "...", "role": "user", "content": "..."}
  ],
  "inputRefs": [],
  "workspace": null,
  "userMessage": "现在进展怎么样？",
  "responsePolicy": {
    "mustNotClaimToolUse": true,
    "mustStateMissingFacts": true
  }
}
```

### 6.4 构建和持久化顺序

1. 在服务端事务内验证 owned conversation 与 lifecycle generation。
2. 幂等地写入本轮 user message，取得 `messageHighWatermark`。
3. 读取任务、执行、binding、附件版本等权威事实。
4. 生成 canonical source manifest、最小结构化 facts 和 `contextHash`。
5. 保存 Context Snapshot 元数据，再下发 Agent。
6. Agent 回报必须携带同一 `contextSnapshotId/contextHash`。
7. 最终回复保存时再次验证 conversation generation；身份切换、会话删除或 generation 改变时不得写入旧会话。

快照表不重复保存文件正文、API Key、凭证或推理 trace。消息正文仍由 chat_message 保存；快照只保存消息 ID 列表、必要结构化事实、版本向量、hash 和授权范围。

### 6.5 摘要和裁剪原则

按以下不可丢失顺序组织输入：

1. 身份/范围/权限和模式；
2. 当前用户消息；
3. 当前任务、执行和工作区精确事实；
4. 已确认决定和未解决问题；
5. 摘要之后的最近原始消息；
6. 低优先级历史说明。

达到模型上下文压力时先裁剪低优先级历史，不得裁掉授权边界、当前消息或精确任务状态。没有可信摘要时，新建 thread 或回退完整安全路径，不允许用缺失摘要伪装上下文完整。

输入预算从实际 `model/list`/provider capability 的上下文窗口和输出预留推导，不写死跨模型 token 数。Builder 在 dispatch 前产出 `includedRefs/omittedRefs/truncationReason`；超大附件不直接嵌入，必须转 INSPECT、摘要或分段读取。裁剪结果进入 context hash，Agent 不得在本地再次无记录地裁剪。

### 6.6 回答依据与可验证引用

最终事件由 Runtime 生成不可由模型伪造的 `grounding` 元数据：

```json
{
  "contextSnapshotId": "ctx_...",
  "sourceVector": {},
  "inspectedRefs": [
    {"logicalRef": "api/chat/.../Foo.java", "treeSha": "abc...", "sha256": "..."}
  ],
  "toolUseObserved": false
}
```

- CHAT 的任务状态结论绑定 snapshot fact ref；INSPECT 的文件结论绑定 manifest ref/hash/tree SHA。
- `routeUsed/toolUseObserved/inspectedRefs` 由适配器根据真实事件生成，模型正文不能自行声明“我已检查/已执行”来改变这些字段。
- 来源缺失、版本冲突或读取失败时，回复必须说明缺口并保持 CHAT/INSPECT 失败状态，不能用旧 thread 记忆补成当前事实。
- 前端可显示简化的“依据版本”，审计端保留精确 ref；不得把内部绝对路径、密钥或不可见资源名称泄露给无权用户。

### 6.7 持久化模型与一致性

实施时优先复用现有 message/outbox/audit 基础设施；若不能满足约束，新增逻辑实体如下，具体表名由 API Owner 在 migration 设计中冻结：

| 实体 | 最小字段 | 关键约束 |
| --- | --- | --- |
| Context Snapshot | snapshotId、owner/client/tenant scope HMAC、conversation/generation、sourceVector、contextDigest/version、facts manifest、createdAt | snapshotId 高熵唯一；不保存 secret/文件正文；scope/generation 不可变；digest 不作授权 |
| Chat Request | requestId、userMessageId、conversation/generation、requestRevision、aggregateState、timestamps | `(scope, requestId, requestRevision)` 唯一；群聊父状态从子 turn 聚合 |
| Chat Turn | turnId、requestId、targetAgentId、snapshotId/hash、route、state、finalDigest、timestamps | `(requestId,targetAgentId)` 唯一；finalDigest 单次确定 |
| Agent Dispatch | dispatchId、turnId、protocolVersion、attempt/state、acceptedAt | turnId 逻辑唯一；同 dispatchId 重投幂等 |
| Thread Binding | profile/agent/conversation/mode/workspace/policy/instruction/model hashes、generation、threadId、state | 完整 thread key 唯一；tombstone 后不可 resume |
| Summary/Decision | conversation/generation、revision、message range、sourceVector、generatorVersion、status、supersedes | revision CAS；correction/supersession append-only |

事务与一致性规则：

1. user message、Chat Request、每个目标 Agent 的 Chat Turn 和首个 outbox 记录在同一 API 事务中提交；提交后才可向 Agent 发送。
2. task/execution/binding 可能跨模块读取，不能假装处于同一数据库事务。Builder 读取各自 revision，形成 source vector，并在 dispatch 前复核关键 revision；变化则重建 snapshot。
3. Agent ACK、engine accepted、final generated 等通过 CAS 推进状态，旧 attempt 不能覆盖新 generation。
4. final message 与 `FINAL_PERSISTED` 在同一事务中写入，并以 turnId/targetAgentId/finalDigest 唯一约束防重。
5. 事件发布使用 transactional outbox 或等价机制；“DB 成功、SSE/WS 失败”由 outbox 重投，不重新调用模型。
6. DDL 若新增表/索引，必须包含在线迁移、回填、回退和旧版本兼容；若复用现有表，需记录唯一键、索引和隔离级别如何满足上述约束。

Snapshot Builder 应使用批量/并行的 owner-scoped 查询避免按消息、参与者或附件产生 N+1；任何缓存都必须以 source vector 为键并在 ACL、generation 或 revision 变化时失效。快照构建耗时单独观测，但不能因性能目标跳过权威读取。

## 7. 工作目录与内容可见性

### 7.1 CHAT workdir

每个 Profile 使用独立小目录，例如：

```text
/home/isp/apps/codex-ws-agent/chat-workdirs/<profileId>/
├── AGENTS.md          # persona、回答边界、禁止执行
└── README.md          # 无项目源码说明
```

CHAT 不扫描 `/home/isp/wsps/cyf`，也不依赖工作目录获取业务状态。所需内容由 Context Envelope 注入。因此不同执行工作目录不会让普通议事丢失任务状态。

### 7.2 INSPECT snapshot

两种授权来源：

1. 文件/附件：物化只读输入目录，带 `manifest.json`、owner、版本、hash、允许路径。
2. 代码：绑定 exact Git tree SHA 的只读 checkout/snapshot。

manifest 示例：

```json
{
  "snapshotId": "ins_...",
  "ownerScopeHash": "...",
  "treeSha": "abc...",
  "files": [
    {"logicalRef": "api/chat/.../Foo.java", "sha256": "...", "size": 1234}
  ],
  "allowedOperations": ["read", "search"],
  "expiresAt": null
}
```

不使用未经校验的任意绝对路径。快照失效时明确重新物化，不自动扩大路径。

`cwd` 和 manifest 不是操作系统安全边界。若候选引擎仍有文件/命令工具，必须在独立低权限进程或外部 sandbox/filesystem namespace 中运行，只把 manifest 声明的只读文件和必要运行时 bind-mount 进去，关闭网络并隔离宿主其他 CODEX_HOME、工作区、`/proc` 敏感信息和 secrets。无法证明该隔离时，INSPECT 不能上线。

### 7.3 EXECUTE workspace

继续使用现有隔离任务工作树：

```text
agent-workspaces/<taskId>/<agentId>
```

绑定 task/work item、exact SHA、允许路径、输入版本、锁和输出 manifest。thread 不允许跨 cwd 或跨 workspace scope 复用；工作目录、tree SHA、sandbox 或授权变化时必须开启新的 thread generation。

### 7.4 指令来源与 Prompt Injection 边界

指令按以下信任级别处理，并将有效来源路径/类型/hash 写入 `instructionSourceVector` 与 thread binding：

1. **平台托管指令**：运行时版本化的 `baseInstructions/developerInstructions`，最高可信，但仍不能扩大业务 ACL。
2. **CHAT Profile 指令**：CHAT 小 workdir 中由发布制品生成的 `AGENTS.md`/配置；目录归服务用户、不可被业务用户写入。
3. **仓库指令**：INSPECT exact tree 中的仓库 `AGENTS.md` 等，只在该仓库 scope 内生效，必须记录 SHA；它们可约束分析方式但不能扩大 manifest、网络、写入或执行权限。
4. **用户消息、附件、日志、代码内容**：始终是数据，即使内容声称“忽略之前指令”也不提升优先级。物化附件时不得使用会被 Codex 自动发现为指令/配置的保留文件名和目录结构。

CHAT workdir 必须同时避免继承未审计的项目 `.codex`、skills、plugins、MCP 配置。若 CODEX_HOME 的全局配置无法对 CHAT 建立可证明的最小 tool/instruction catalog，则该候选不能作为 Fast CHAT 引擎。

## 8. Agent thread 与进程模型

### 8.1 进程数量

- 不按用户、会话或消息创建 app-server。
- 每个隔离 Profile/CODEX_HOME 最多维护一个受管 app-server 候选进程；是否同时启用三个 Profile 必须先测量单 Profile RSS/CPU/Swap。
- 现有 2 核宿主全局只运行一个重 EXECUTE；该限制是初始调度策略，可依据容量实测调整，不是业务失败门槛。

### 8.2 Thread key

```text
tenantId + clientId + ownerSubjectHash + profileId + agentId + conversationId
+ interactionMode + workspaceScopeHash
+ enginePolicyHash + instructionSourceHash + modelConfigHash + generation
```

禁止跨用户、跨 Agent、跨业务会话、跨模式、跨工作目录复用。模型、reasoning、sandbox/tool policy、有效指令、身份或授权范围改变时都必须开启新 generation；不能把旧 thread 的隐藏历史带入新策略。

### 8.3 生命周期

```text
NEW → HOT → IDLE → UNSUBSCRIBED → ARCHIVED
          └────────→ COMPACTED → HOT(new generation)
```

- HOT：有活动 turn 或订阅。
- IDLE：无 turn；可主动 unsubscribe 停止向当前连接推送事件。官方文档说明 thread 在空闲一段时间后才卸载，不能把 unsubscribe 当作立即释放内存。
- COMPACTED：保留业务摘要和 source vector，旧 thread 不再作为唯一上下文。
- ARCHIVED：业务会话关闭、thread 已无恢复需要。
- DELETE：仅在业务保留政策允许、无活跃映射、快照和摘要可重建且 readback 通过时执行。

磁盘压力不能触发无证据的全目录年龄删除。先记录每 Profile session/log 占用，再按可证明已归档的业务引用清理。

### 8.4 身份、认证与进程边界

- 每个 Profile 的 CODEX_HOME、auth/config/session 目录由专用服务身份持有，目录默认 `0700`、凭证文件默认 `0600`，不与其他 Profile、Web 用户或执行 worktree 共享。
- app-server 默认只以父子进程 stdio 通信；若未来改为 socket/远程服务，必须另立认证、传输加密、peer identity 和重放防护设计，不能暴露未认证端口。
- 启动环境采用显式 allowlist，清除与本轮无关的云凭证、数据库口令和部署 token；Context Snapshot 与日志不得包含 auth 内容。
- 登录失效、token 轮换、账户切换或 Profile 解绑时，停止新 turn、使 binding generation 失效、重建进程并完成 readback。不得将一个 Profile 的登录态热切给另一个 Profile。
- 运行时 Profile 使用独立于 Codex Desktop 用户目录的 CODEX_HOME，内部 thread 不创建用户拥有的 Codex Desktop task，也不依赖桌面侧会话列表作为生命周期控制面。

## 9. 调度与并发

### 9.1 Lane

```text
chatLane     每 Profile 串行；可与一个重执行并存
inspectLane  只读、有界排队；避免与重执行争抢大量 I/O
commandLane  持久 FIFO，维持既有 ledger/inbox/ACK/recovery 语义
```

全局资源调度器观察 CPU、RSS、Swap、I/O wait 和活跃执行，不用性能目标取消已受理工作。

### 9.2 行为规则

- COMMAND 已运行时，新 CHAT 进入 chatLane，而不是返回“忙碌”或重复执行。
- 同一会话同一 Agent 同时只允许一个生成 turn；后续消息排队或由用户显式取消上一轮。
- CHAT 不持久化为 command，不进入 command dedupe ledger。
- EXECUTE 保留现有持久 inbox、fingerprint、STARTED ACK、terminal/recovery_required 处理。
- app-server 或 CHAT 失败可回退到现有 full Codex chat 路径；回退事件必须记录 `fallbackReason`，不得伪报 fast path 成功。
- handshake、WS/SSE、RPC 等传输边界保留明确超时和重连退避；模型生成慢只记录，不把性能 SLO 当 turn 自动中断条件。

### 9.3 公平、背压与重启语义

- CHAT/INSPECT 使用按 tenant/client/owner/Agent/conversation 组合键的公平队列，避免单一群聊或长会话长期占用 Profile；具体权重和并发值由容量试点推导，不在设计阶段硬编码。
- 用户消息一旦提交并返回 accepted，就必须同时存在可查询的 durable chat turn/outbox 记录。CHAT 不进入 command ledger，但也不能仅存在于内存队列。
- 队列有界时不得静默丢弃已受理项；达到真实容量上限可保持持久排队或返回明确未受理错误。不能为达到时延 SLO 把 accepted 请求改成取消/成功。
- Runtime 重启后重放的是未完成 dispatch 记录，不是重新写 user message；同一 `dispatchId` 在 Agent 侧去重。
- COMMAND 保持现有持久 FIFO 与互斥，不被 CHAT 公平策略抢占、取消或降级。

## 10. API 与事件合同

### 10.1 `POST /chat/stream`

保持现有路径，新增字段均可选：

```json
{
  "requestId": "req_...",
  "content": "...",
  "conversationId": "...",
  "conversationType": "juyiting",
  "targetAgentId": "...",
  "taskId": "...",
  "interactionHint": "chat|inspect",
  "clientSeenVector": {
    "conversationGeneration": 3,
    "messageHighWatermark": "..."
  },
  "inputRefs": [
    {"type": "workspace-file", "id": "...", "version": 2}
  ],
  "requestRevision": 4
}
```

规则：

- 复用当前登录鉴权；服务端从认证上下文取得 owner/client/tenant，不接受 body/metadata 覆盖。无权访问统一返回非泄露错误。
- `interactionHint` 只是提示，不支持通过该接口请求 execute。
- `clientSeenVector` 用于发现页面陈旧，不决定服务端事实。
- `inputRefs` 必须逐项 owner/client/tenant 校验并固定版本。
- `requestRevision` 是同一客户端 requestId 的单调修订号，只用于去重/识别陈旧提交，不代表业务实体 revision；重试必须复用 requestId 和 revision。
- 老前端不发送新字段时默认 CHAT，仍可走旧 Agent 兼容路径。

成功受理返回或首个流事件必须包含稳定 `requestId/conversationId`；单 Agent 同时返回 `turnId`，多 Agent 返回每个 `targetAgentId → turnId` 映射。格式错误为 400，未认证为 401，scope 不可见统一为非泄露 403/404 策略，版本冲突为 409，真实容量/上游不可用可返回明确 429/503 且不得写成 accepted。已写入 user message 的请求不能再用普通 HTTP 失败掩盖，必须返回可查询 request/turn 状态。

### 10.2 查询、事件与取消端点

新增端点均复用当前认证上下文并做 owner/client/tenant + conversation generation 校验：

| Method/path | 用途 | 关键返回/语义 |
| --- | --- | --- |
| `GET /chat/capabilities?conversationType=juyiting` | Web 协商可发送字段和可展示能力 | API schema/event versions、interaction hints、flags；不暴露 Profile secret 或内部模型凭证 |
| `GET /chat/requests/{requestId}` | 网络结果未知、刷新或群聊聚合恢复 | 父状态、userMessageId、每个 targetAgentId 对应 turnId/state/finalMessageId |
| `GET /chat/turns/{turnId}` | 精确恢复单 Agent turn | state/stateVersion、snapshot basis、route、timestamps、final/error；无权访问采用非泄露错误 |
| `POST /chat/turns/{turnId}/cancel` | 取消一个 CHAT/INSPECT 子 turn | body 含 `expectedStateVersion/reason`；幂等；终态返回当前终态，不影响 COMMAND |
| `POST /chat/requests/{requestId}/cancel` | 群聊取消 pending 子 turn | body 必须显式 `allPending=true` 或 target turnIds；已完成项不回滚 |
| `GET /chat/conversation/events` | 既有 SSE | 支持 `Last-Event-ID` 或 cursor；重放持久状态/final，delta 只 best-effort |

新 Web 发送 `Idempotency-Key: <requestId>`；可选 body `requestId` 必须与 header 一致。旧 Web 无该字段时由服务端生成并在首事件返回。cancel 的业务幂等键与原发送 requestId 分离，避免取消重试被误判成发送重试。

兼容：这些查询/取消端点是 additive；旧 Web 可继续依赖 conversation event/polling。若 capabilities 不可用，新 Web 必须降级到旧 payload，不能乐观发送 v2。

### 10.3 Server → Agent `chat.message` 扩展

```json
{
  "schemaVersion": "2",
  "messageType": "chat.message",
  "messageId": "...",
  "requestId": "req_...",
  "turnId": "turn_...",
  "dispatchId": "dsp_...",
  "conversationId": "...",
  "targetAgentId": "...",
  "content": "用户原话",
  "routing": {
    "interactionMode": "CHAT",
    "routeReason": "DEFAULT_CHAT",
    "requestRevision": 4
  },
  "contextSnapshot": {
    "id": "ctx_...",
    "hash": "sha256:...",
    "sourceVector": {},
    "envelope": {}
  }
}
```

兼容：schema v1 Agent 继续读取 `content`；API 仅在 Agent 注册 capability 包含 `context.snapshot.v1` 时依赖新字段。

Agent 注册 capability 至少声明：`protocolVersions`、`contextSnapshotVersions`、`deltaVersions`、`interactionModes`、`engineKinds`、`toolPolicyKinds` 和运行时版本。API 对群聊逐 Agent 协商，未知 capability 一律走 v1 兼容路径。

### 10.4 Agent → Server 事件

```json
{
  "type": "agent_message_delta",
  "requestId": "req_...",
  "dispatchId": "dsp_...",
  "conversationId": "...",
  "turnId": "turn_...",
  "agentId": "...",
  "contextSnapshotId": "ctx_...",
  "contextHash": "sha256:...",
  "deltaSeq": 12,
  "content": "增量"
}
```

```json
{
  "type": "agent_message",
  "requestId": "req_...",
  "dispatchId": "dsp_...",
  "conversationId": "...",
  "turnId": "turn_...",
  "agentId": "...",
  "contextSnapshotId": "ctx_...",
  "contextHash": "sha256:...",
  "finalSeq": 37,
  "content": "最终答复",
  "finishReason": "completed",
  "routeUsed": "CHAT_FAST"
}
```

- `deltaSeq` 在 turn 内从 1 单调递增；重复序号幂等忽略，跳号触发 UI 等待最终消息而不是拼错文本。
- Runtime 只把用户可见的 Agent message delta/final 转发到聚义厅；reasoning text/summary、tool stdout/stderr、审批详情和内部 trace 默认不进入聊天消息或业务日志。
- 每个对 Web 发布的事件另带服务端 `eventId/eventVersion/occurredAt`；`deltaSeq` 只在单 turn 内排序，不能替代跨连接 event ID。
- delta 为瞬时体验数据；最终 `agent_message` 和关键 turn 状态只持久化一次。服务端可以不重放已过期 delta，但必须重放最新 turn 状态和 final。
- SSE 重连使用 `Last-Event-ID` 或显式 cursor 获取已持久状态/final，不自动重发用户请求；cursor 过旧时返回 snapshot/current-state，而不是猜测缺失 delta。
- final 必须与 dispatch 的 snapshot ID/hash 匹配；不匹配按协议错误处理并记录，不写入其他会话。
- final 超过当前传输/存储能力时不得被 `trimReply` 一类逻辑静默截断；按实测能力选择分块、正文对象引用或显式 `truncated=true + fullContentRef`，且 full ref 继续受 owner/client/tenant ACL。具体容量值由通道和数据库证据推导。

### 10.5 错误语义

| 错误 | HTTP/事件 | 行为 |
| --- | --- | --- |
| `CONTEXT_SCOPE_MISMATCH` | 403/协议错误 | 不下发 Agent，不泄露存在性 |
| `CONTEXT_STALE` | 409 或状态事件 | 服务端重建最新快照；写请求不自动重试 |
| `INSPECT_REF_NOT_FOUND` | 404 | 不扩大搜索路径 |
| `INSPECT_SNAPSHOT_CHANGED` | 409 | 重新固定版本后再检查 |
| `AGENT_FAST_PATH_UNAVAILABLE` | 状态事件 | 安全回退旧路径或继续排队 |
| `AGENT_PROTOCOL_UNSUPPORTED` | 状态事件 | capability 回退，不取消已受理 command |
| `TURN_CONTEXT_MISMATCH` | 协议错误 | 丢弃错误归属回复，保留审计 |
| `REQUEST_IDEMPOTENCY_CONFLICT` | 409 | 同 requestId/revision 的内容或 scope 不同；拒绝覆盖原请求 |
| `TURN_ACCEPTANCE_UNKNOWN` | 202/状态事件 | 保持可查询 unknown，先对账，不自动重放 |
| `TURN_ALREADY_TERMINAL` | 200/409 | cancel/read 返回当前终态，不回滚 final |
| `FAST_CHAT_TOOL_POLICY_VIOLATION` | 状态事件 | 拒绝请求/中断 turn，不能提升权限继续 |
| `ENGINE_RATE_LIMITED` / `ENGINE_QUOTA_EXHAUSTED` | 429/状态事件 | 按策略排队或显式失败/安全 fallback，不伪报成功 |
| `OUTPUT_REFERENCE_REQUIRED` | 状态事件 | 正文过大时返回受 ACL 的 fullContentRef，不静默截断 |

### 10.6 Chat Turn 状态、未知受理与取消

持久状态至少区分：

```text
RECEIVED → USER_COMMITTED → SNAPSHOT_READY → DISPATCH_PENDING
→ AGENT_ACCEPTED → ENGINE_ACCEPTED → RUNNING → FINAL_GENERATED
→ FINAL_PERSISTED → PUBLISHED
                         ↘ CANCEL_REQUESTED / CANCELLED
                         ↘ ACCEPTANCE_UNKNOWN / RECOVERY_REQUIRED / FAILED
```

- `requestId`、`dispatchId`、app-server `clientUserMessageId`、`threadId/turnId` 的映射先于对外发布 final 持久化；各层重试都复用原稳定 ID。
- 区分“尚未发送”“Agent 已接受”“`turn/start` 已发送但应答丢失”“final 已生成但数据库未保存”等状态。未知受理时先通过本地 journal、app-server thread/read/turn 事件和业务 DB 对账，禁止盲目再次 `turn/start`。
- CHAT/INSPECT 是无副作用推理时，若最终无法对账，可把旧尝试标记 abandoned/unknown 后由明确策略或用户动作生成新 dispatch；必须避免重复落屏并记录重复 token/cost 风险。EXECUTE 永不沿用该推理重试规则。
- 用户取消只中断对应 CHAT/INSPECT 推理并保留已提交 user message 与取消状态；不会回滚业务事实。身份切换使旧页面停止接收并尝试 interrupt 其非执行 turn，但不得取消已经进入正式 COMMAND 状态机的工作。
- 群聊取消必须显式指定子 turn 或 `allPending=true`；已完成子 turn 不回滚，未指定时不得误取消同 request 的其他 Agent。
- SSE/页面断开默认不取消已受理 CHAT；服务端继续完成并持久化 final，重连后按状态恢复。

## 11. app-server 适配

### 11.1 接入顺序

1. `initialize` / `initialized`。
2. `account/read` 与能力确认。
3. 按 Thread key `thread/start` 或 `thread/resume`。
4. `turn/start`，输入为静态 persona 约束、Context Envelope 和本轮 user message。
5. 消费真实 Agent message delta 与 final。
6. turn 完成后更新本地 thread binding 的 `lastAppliedContextHash`。
7. 空闲时 unsubscribe；需要滚动时 compact/archive 并新建 generation。

Codex 官方 app-server 文档是协议能力依据；实现仍必须锁定部署 CLI 版本并以集成测试确认实际字段，不能只依据文档假设。

### 11.2 版本和能力锁定

- 发布证据记录 Codex binary SHA/版本、生成的 JSON schema digest、初始化 capability、`model/list`、有效 config readback 和事件方法集合。
- `chatReasoningEffort`、sandbox、service tier、experimental 字段只能从该版本 schema/capability 选择；无效配置整份拒绝并保留上一个有效配置。
- 升级 CLI 先在单 Profile 新 generation 演练，再切换；不在活动 thread 上假设 session-static model/reasoning 设置能热更新。

### 11.3 服务端请求处理

app-server 可能向客户端发出命令审批、文件修改审批、权限申请、动态/MCP 工具调用和用户输入请求。适配器必须按 `(threadId, turnId, itemId, requestId)` 关联并执行显式策略：

`approvalPolicy=never` 不是“拒绝全部工具”，而是不会为策略内动作询问用户；因此不能依靠它阻止 CHAT 读文件或执行只读命令。工具目录和 OS sandbox 才是安全门禁。

| 模式 | 请求 | 策略 |
| --- | --- | --- |
| CHAT | command/file change/permission/network/MCP/dynamic tool | 拒绝并中断该 turn，记录 `FAST_CHAT_TOOL_POLICY_VIOLATION`；不得自动批准 |
| CHAT | user input | 可转成普通澄清事件或结束当前 turn；不得把它当执行确认 |
| INSPECT | manifest 内只读读取/搜索 | 仅在选定引擎能证明请求仍受 manifest 和 sandbox 约束时允许 |
| INSPECT | 写入、网络、扩大路径、权限升级 | 拒绝并中断 |
| EXECUTE | 审批/工具请求 | 继续服从现有 durable command 权限和工作区策略；app-server 请求本身不是新增授权 |

未识别的服务端请求默认拒绝；超时、断连或 handler 崩溃不能转成批准。所有响应和 `serverRequest/resolved` 都保留低敏审计。

### 11.4 Fast CHAT 引擎决策门禁

在 T20 前对三类候选做同一套正确性、安全、时延、成本测试：

1. **直接轻量模型/Responses 路径**：最容易做到真正不传 tools，但需要自行维护 persona、流式、额度与模型调用。
2. **Codex app-server 受限路径**：复用登录、thread 和 delta；必须证明 effective tool catalog、网络、cwd、skills/plugins/MCP 和 server requests 均满足 CHAT 边界。
3. **现有后端内置模型路径**：复用 Spring AI/ChatModel 基础设施；需确认是否能承载外部 Agent persona、独立 profile 认证和真实流式。

选型门禁：

- 负向 prompt 无法触发 shell、文件读取、网络、MCP、plugin、dynamic tool 或权限升级；
- 若 app-server 仍暴露文件/命令能力，仅有 cwd/read-only 不合格；必须证明低权限 OS 进程/外部 sandbox 只可见小 workdir，或淘汰该候选；
- Context Envelope、persona、群聊隔离、流式、取消、usage 和 rate-limit 可观察；
- 认证方式、供应商数据处理/保留配置、区域与账户费用归属符合现有授权边界；
- 同输入 A/B 质量与资源证据齐全；
- 未证明 strict no-tools 时，名称、UI、指标和验收一律使用 `read-only-constrained`，不能声称“工具已关闭”。

### 11.5 Runtime 接口

```js
runFastChat(message, contextSnapshot)
runReadOnlyInspection(message, contextSnapshot, inspectManifest)
runConfirmedCommand(message, durableCommandRecord)
```

禁止继续由一个 `runCodex(mode)` 隐式承担三种不同安全语义。

### 11.6 Profile 配置候选

```ini
chatEngine=<validated-direct-responses|validated-app-server|validated-backend-model>
chatModel=<model/list 与账户 capability 验证后的模型>
chatReasoningEffort=<模型实际支持的低档位>
chatSandbox=read-only
chatToolPolicy=<verified-none|read-only-constrained>
chatNetworkAccess=false
chatWorkdir=/home/isp/apps/codex-ws-agent/chat-workdirs/<profileId>

inspectReasoningEffort=medium
inspectSandbox=read-only

commandReasoningEffort=medium
commandSandbox=workspace-write
```

模型与 reasoning 参数必须经 Profile capability/readback 确认。配置无效时保留上一份有效配置，不半加载。

## 12. 前端行为

### 12.1 请求

- 保持当前 selected Agent、task、participant metadata。
- 新增 `interactionHint/clientSeenVector/requestRevision/inputRefs`。
- 不发送完整 `messages[]` 作为可信上下文。
- 用户点击发送后生成稳定 request ID；网络结果未知时先读取会话/turn 状态，不自动再次发送。

### 12.2 展示状态

```text
已送达 → 排队中 → 正在理解上下文 → 正在检查（INSPECT）
      → 正在生成 → 回话已毕
```

状态必须来自真实服务端/Agent 事件，不使用定时器伪造。

群聊按 Agent 显示独立排队/生成/完成/失败状态，并展示父 request 的部分完成；不能用第一个 Agent final 提前结束整次发送，也不能因一个 Agent 失败隐藏其他已完成回复。

模型输出、文件名和引用均按不可信内容处理：前端 Markdown/HTML 必须使用既有安全渲染和 URL allowlist，禁止事件属性、脚本、危险 scheme 或未授权本地路径链接。流式增量与 final 使用同一 sanitization 规则，不能只清洗最终文本。

### 12.3 过期上下文

若回复生成期间 task/execution 发生关键变化：

- 回复仍可展示为“基于版本 X”；
- 同时显示“事项状态已更新”，请求后端生成结构化补充；
- 不把旧状态回答伪装成当前事实；
- 身份或会话 generation 变化属于安全边界，旧回复不得写入新上下文。

### 12.4 写入意图

用户说“把问题修好”时：

1. CHAT 解释理解的目标、范围、资料和风险；
2. 在答复中返回不具执行效力的结构化办理建议，不在 CHAT 路径写 Hall Draft；
3. 用户点击现有明确入口，由该已鉴权接口创建/更新 Hall Draft；
4. 用户在现有流程确认提交；
5. 正式执行服务生成持久 execution/command；
6. Agent Runtime 收到 `command.dispatch` 后进入 EXECUTE。

## 13. 可观测性与 A/B

### 13.1 时间戳

统一 request/turn ID，记录：

- `request_received_at`
- `user_message_committed_at`
- `context_snapshot_ready_at`
- `agent_ws_dispatched_at`
- `agent_received_at`
- `lane_queued_at` / `lane_started_at`
- `engine_thread_ready_at`
- `engine_turn_started_at`
- `first_model_event_at`
- `first_visible_delta_published_at`
- `final_generated_at`
- `final_persisted_at`
- `final_published_at`
- Web `first_visible_rendered_at`

日志不得记录用户正文、认证 token、Cookie、API Key、文件内容或绝对私有路径。标签使用 route/mode/profile/outcome，不使用用户 ID、conversationId 等高基数值作为指标标签。

### 13.2 指标

- route 分布和 fallback 原因；
- queue wait、TTFT、first-visible、final latency；
- input/output token 与 context envelope 大小；
- thread resume/new/compact/archive 数量；
- delta duplicate/gap/final mismatch；
- context stale 与 scope rejection；
- 每 Profile app-server RSS、CPU、Swap、FD、session/log 磁盘；
- command 不重复执行、未知结果和 recovery_required 数量。

### 13.3 A/B 设计

对同一组固定问题和授权夹具比较：

| 组 | 路径 |
| --- | --- |
| A | 当前 `codex exec + resume + final 切片` |
| B | Context Snapshot + 当前 full Codex |
| C | T05 选定的 Fast CHAT 引擎，关闭持久 thread/连接优化 |
| D | 同一 Fast CHAT 引擎启用可用的持久 thread/连接与真实 delta；另单列 app-server 候选对比 |

测试覆盖普通闲聊、任务状态、连续指代、长会话、新 thread 恢复、工作目录变化、执行中状态查询和需要 INSPECT 的问题。按分布和置信区间报告，不用单次最好值；性能超标只进入优化清单，不取消可用请求。

质量评估分两层：身份/ACL/执行声称/任务状态/来源版本等关键事实使用确定性断言，任何严重越权或虚假执行声称都不能用平均分抵消；表达完整性、persona 一致性和一般帮助度使用盲评/成对比较并报告分布，不预设无依据单一总分门槛。

### 13.4 用量、成本和限流

- 按 route/profile/model/reasoning/service tier 记录 input/output/cache token、调用数、重试、reroute、rate-limit 与账户额度事件，不把用户/会话 ID 做指标标签。
- Fast CHAT 使用明确 allowlist 的模型与 reasoning；fallback 不得静默切换到成本显著更高或权限更宽的模型/供应商。需要跨成本档时记录原因并遵守产品费用策略。
- 账户额度耗尽、限流和认证恢复是可见状态：可持久排队或安全回退，但不能伪报成功；重试尊重服务端 backoff，并按稳定 request/dispatch ID 对账。
- “性能回退”不等于获得外部付费工具、部署或生产操作授权。

## 14. 风险与控制

| 风险 | 概率/影响 | 控制 |
| --- | --- | --- |
| CHAT 把需要文件的问题当普通聊天 | 中/高 | 明确 route proposal；无证据不猜；一键转 INSPECT |
| INSPECT 路径越权 | 低/严重 | 服务端 manifest、owner scope、exact SHA、read-only sandbox |
| 文本触发执行 | 中/严重 | `/chat/stream` 不接受 execute；仅持久 command path 授权 |
| Context Snapshot 过期 | 中/中 | source vector/hash；关键变化显示版本并补充 |
| 摘要遗漏关键决定 | 中/高 | 决定结构化；保留摘要后原始消息；可重建 |
| app-server 崩溃或协议变化 | 中/中 | capability/version adapter、进程监管、旧路径回退 |
| 真 delta 重复/乱序 | 中/中 | turnId + deltaSeq；final 单次持久化 |
| 轻重 lane 并发压垮 2 核宿主 | 中/高 | 单 Profile 试点、全局一重执行、RSS/Swap 实测扩量 |
| thread/session 占满磁盘 | 高/高 | 业务 DB SSOT、引用感知归档、占用观测、无盲删 |
| 低 reasoning 降低回答质量 | 中/中 | 固定正确性夹具、按场景回退 medium/full path |
| 多仓脏工作区相互覆盖 | 高/高 | 独立 worktree、path ownership、exact SHA、禁止改部署副本 |
| Fast CHAT 实际仍可调用工具 | 中/严重 | 引擎 spike、tool catalog/readback、负向行为测试、未知请求默认拒绝 |
| 指令文件/附件提升为高优先级指令 | 中/严重 | 指令来源分级、保留名隔离、source hash、最小 CODEX_HOME |
| `turn/start` 受理未知导致重复推理/执行 | 中/高 | 持久状态、clientUserMessageId、journal/readback、禁止盲重放 |
| 群聊跨 Agent 上下文泄露 | 中/严重 | 每 Agent 独立 snapshot/thread、可见性投影、正式消息后才共享 |
| token/认证/session 泄露 | 低/严重 | 服务身份权限、env allowlist、stdio、轮换与删除 fence |
| 额度/限流导致静默高价回退 | 中/中 | 模型 allowlist、usage/limit 事件、显式 fallback policy |
| 数据删除后 Codex 缓存仍可恢复 | 中/严重 | retention ledger、binding tombstone、archive/delete retry/readback |

## 15. 分阶段实施计划

### Phase 0：冻结合同与基线（P0）

范围：M0、M0.5。除隔离 spike 外无线上业务行为改变。

- 建立时间戳、route/profile/outcome 指标和资源采样。
- 保存当前 A 组固定问题、上下文夹具和历史观测脚本。
- 记录 Agent Runtime、API、Web、root exact SHA/tree 和 CLI 版本。
- 验证日志脱敏与指标低基数。

退出条件：同一请求可关联 API、WS、Agent、engine、SSE、Web；现有行为和执行授权未改变。

### Phase 1：上下文正确性与权威路由（P0）

范围：M1。

- API 实现 Interaction Router、Context Snapshot Builder 和 source vector/hash。
- Agent 实现 `buildContextEnvelope()`，不再只把 `content` 当完整 prompt。
- Web 增加 clientSeenVector、requestRevision 和可选 inputRefs。
- CHAT 文字写入意图只返回办理建议；EXECUTE 仍只走现有正式执行路径。
- 先继续使用当前 full Codex 引擎，隔离“上下文正确性”与“性能优化”变量。

退出条件：新 thread、Agent 重启、页面刷新、任务切换后仍能基于同一权威快照回答；跨身份/范围负向测试通过。

### Phase 2：快速 CHAT 与 lane 分离（P1）

范围：M2、M3。

- 先完成引擎/工具暴露 spike；仅在 tool catalog、负向请求和运行 readback 证明后使用 `verified-none`，否则采用 `read-only-constrained` 并如实展示。
- 拆分 chatLane 和 commandLane；命令运行时聊天排队/并行，不返回伪忙碌成功。
- 单 Profile feature flag 试点，保留旧 full path fallback。
- 运行 A/B，报告 TTFT、first-visible、final、质量和资源变化。

退出条件：无执行重复、无 scope 泄露；快速路径相对 A 组有可重复收益，回答正确性未出现不可接受回退。具体数值由实测记录，不预设硬门槛。

### Phase 3：只读 INSPECT（P1）

范围：M4。

- 文件输入生成 owner-safe manifest。
- 代码检查绑定 exact tree SHA 的只读 snapshot。
- 线程与 workspaceScopeHash 绑定，禁止跨 cwd 续接。
- CHAT 能明确升级为已授权 INSPECT；失败不扩大路径。

退出条件：代码/日志问题引用的来源和 SHA 可验证；路径穿越、软链、跨 owner、失效版本测试通过。

### Phase 4：长期 app-server 与真实 streaming（P2）

范围：M5。

- 扩展 `managed-host.mjs` 或独立 adapter，执行真实 `turn/start`。
- 处理 delta/final/interrupt/unsubscribe 和异常恢复。
- 移除 `buildReplyChunks` 伪流式路径，仅保留旧 Agent 兼容分支。
- 先一个 Profile，再按 RSS/CPU/Swap 和错误率扩展。

退出条件：首个可见字符来自真实模型事件；SSE 重连不重复 final；app-server 崩溃可安全回退且不影响 command ledger。

### Phase 5：上下文滚动、压缩和生命周期（P2/P3）

范围：M6、M7。

- 结构化摘要与 decision ledger。
- thread generation、compact/archive/unsubscribe。
- 引用感知磁盘回收和三 Profile 扩量。
- 对长会话重新测量尾延迟和资源曲线。

退出条件：业务会话不依赖 Codex JSONL；删除/归档演练可从业务 DB 和快照重建；磁盘回收不会触碰活跃/未知执行。

## 16. 兼容、灰度与回退

### 16.1 Feature flags

```text
juyiting.context-snapshot-v1
juyiting.interaction-router-v1
juyiting.fast-chat-v1
juyiting.inspect-snapshot-v1
juyiting.appserver-turns-v1
juyiting.true-delta-v1
```

按 tenant/client/profile 开启；不开启时保持现有行为。

### 16.2 混合版本矩阵与发布顺序

| API | Agent | Web | 预期行为 |
| --- | --- | --- | --- |
| old | old | old | 当前路径 |
| new | old | old/new | API 只发 v1，使用旧 Agent 路径；新 Web 字段必须由服务端 capability gate 后才发送 |
| new | new | old | 服务端可生成 snapshot，但默认保持兼容 UI/final；不要求旧 Web 处理 delta |
| new | new | new | capability 与 feature flag 同时满足后启用 snapshot/Fast CHAT/delta |
| old | new | any | Agent 不能假设收到 snapshot v2；按 v1 安全处理 |
| any | partially upgraded multi-Agent | new | 每个目标 Agent 独立协商；不能因一个新 Agent 让其他旧 Agent 收到不兼容 payload |

发布顺序：API additive schema 和 durable turn 先上线；Agent 新 capability 在 flag off 状态上线；Web capability-aware UI 再上线；最后按 tenant/client/profile 小流量开 flag。任何一层回滚都不撤销 EXECUTE 授权边界、generation fence 和身份校验。

### 16.3 回退顺序

1. 关闭 true delta，保留 final。
2. 关闭 app-server turns，回退 `codex exec`。
3. 关闭 fast chat，回退 full Codex CHAT。
4. 保留 Context Snapshot 和执行边界；除非其自身存在安全缺陷，不因性能回退而撤掉权限校验。
5. COMMAND lane、持久 inbox、幂等和 recovery 语义不得由性能回退覆盖。

### 16.4 发布

- API/Web 依届时有效 Flow 或用户授权本地发布政策执行。
- Agent Runtime 从 `/home/isp/wsps/chcbz/isp-install` 的 exact commit 构建/同步到新 release，不直接编辑 `/home/isp/apps/codex-ws-agent/current`。
- 每阶段记录 API/Web/Agent Runtime commit/tree、测试、制品 SHA-256、配置 readback、进程归属、健康和回退点。
- 不创建独立 Reviewer；各 Owner 自检后按项目政策合入和验证。

## 17. 数据保留、删除与摘要治理

- `chat_message` 与业务任务/执行记录遵循各自权威保留策略；Context Snapshot 仅保存最小元数据和引用，其保留不得长于对应业务会话所需期限。
- Codex thread/session/log 是可删除缓存。用户数据删除、conversation 删除、owner/client/tenant 解绑或授权撤销时，先写 binding tombstone 阻止 resume，再异步 unsubscribe/archive/delete，并对失败重试和 readback。
- 删除尚未完成时不能重新使用该 thread；审计仅保留不含正文的删除操作 ID、范围 hash、结果和时间。
- 摘要由版本化生成器产生，记录输入 message range、模型/规则版本和 source vector。生成失败不覆盖旧摘要；新摘要通过 CAS 提升 revision。
- 用户纠正或决定变更以 append-only correction/supersession 记录表达，不原地篡改历史。摘要可帮助回答，但永远不能覆盖 ACL、任务、执行、文件版本等权威事实。
- 数据导出以业务 DB 为准，不承诺导出模型内部 reasoning trace；Codex 缓存中不应存在业务库之外的唯一用户内容。

## 18. 失败模式与恢复矩阵

| 失败点 | 可观察状态 | 恢复原则 | 禁止行为 |
| --- | --- | --- | --- |
| user message 已提交，WS 未发送 | `DISPATCH_PENDING` | outbox 重投同一 dispatchId | 重写 user message |
| Agent 已收，ACK 丢失 | `ACCEPTANCE_UNKNOWN` | Agent journal/dedupe 对账 | 生成第二个 EXECUTE |
| `turn/start` 请求已发，应答丢失 | `ENGINE_ACCEPTANCE_UNKNOWN` | 用 thread/turn 事件、read API、clientUserMessageId 对账 | 立即再次 turn/start |
| app-server 在 delta 中崩溃 | `RUNNING`/`RECOVERY_REQUIRED` | 丢弃未持久 delta；恢复 final 或明确失败 | 把部分文本当 final |
| final 生成，DB 保存失败 | `FINAL_GENERATED` | 按 final digest 幂等重试持久化 | 再生成不同答案并覆盖 |
| final 已保存，SSE 发布失败 | `FINAL_PERSISTED` | 重连按 DB 重放 final | 重发用户请求 |
| generation/身份在运行中变化 | `CANCELLED_SCOPE_CHANGED` | interrupt 非执行 turn，拒绝写入旧 scope | 写入新会话/新身份 |
| mapping 缺失/损坏 | `THREAD_BINDING_INVALID` | 从业务快照新建 generation | 猜测或跨 cwd resume |
| rate limit/额度不足 | `QUEUED_RATE_LIMIT`/`FAILED_QUOTA` | 按 backoff 排队或显式安全 fallback | 静默换高价/高权限路径 |
| DB 已删除，Codex delete 失败 | `CACHE_DELETE_PENDING` | tombstone + 重试 + readback | 继续 resume 该 thread |

## 19. 关键决定

1. **预计最大收益来自 Fast CHAT，不是 app-server 单项；但具体引擎和收益必须先由 spike/A/B 证明。**
2. **上下文准确性先于速度。**
3. **业务数据库是上下文 SSOT，Codex thread 是缓存。**
4. **不同 workdir 使用不同 thread generation；业务上下文通过快照同步，不依赖 cwd。**
5. **聊天永远不能授权执行。**
6. **真实 streaming 只来自 engine delta，不再伪切片。**
7. **性能目标用于观察和排序，不用于取消、拒绝或伪报成功。**
8. **所有预计时延和 owner-day 在实施前都只是规划估算，A/B 后更新。**
