# 长期融合方案：统一议事与受控执行

日期：2026-09-28。目标分支：四仓 `codex/juyiting-multimedia-deliberation`。状态：长期设计 v2 + 研发整合基线；**不是多媒体业务开发完成、可上线或已验收声明**。本次只授权创建分支、整合已有代码、必要冲突修复及相关验证、编写设计，不合入 develop、不部署、不执行付费生成。

## 1. 决策摘要

长期统一为一个能力：**统一议事会话、权威业务上下文、按需能力加载、授权执行、统一产物与用户验收**。

- fast-deliberation 不成为一套独立产品/聊天系统，而是普通讨论、澄清、进度查询的轻量运行策略。
- multimedia-deliberation 是同一会话上的创作/修改/交付体验；它不意味着每轮默认挂载所有附件和工具。
- CHAT / INSPECT / EXECUTE 表示权限与能力边界，不强制拆成三个微服务或三次模型调用。进度查询是只读投影，可不调用模型。
- 明确生成/修改需求可经业务授权检查直接进入 execution；不要求先调用快速聊天模型“批准”。判定不充分才进行受限规划/澄清。
- 共享 conversation 和消息/资产事实，不等于共享模型线程、工具配置、执行目录、lease 或凭据。
- 复用一套 durable request/turn/snapshot/outbox/event。文件 execution 保留自己的持久运行状态；通过唯一关联连接两者，不能用聊天 final 代替执行完成。

本方案不是短期为两个分支接线。长期保留领域边界，临时保留协议适配；退出旧协议以可验证的迁移事实为条件，不以任意日期或时延阈值为条件。

## 2. 解决当前两份设计的真实差异

| 原有差异 | 长期决策 |
| --- | --- |
| fast 禁止 `/chat/stream` 通过 execute hint 获得执行权限；多媒体要求点将后自动办理 | 保留原禁止。任务发起/点将业务事务可以记录明确且有范围的办理授权，由独立服务端协调器生成 execution 事实；聊天文本/分类结果不能授权 |
| v1 多媒体示意图容易被解读为“每轮先 CHAT 再执行” | 改为统一 admission → 授权解析 → 路由/规划。明确操作直接执行，CHAT 只是可选步骤 |
| fast 的资料隔离与多媒体的图片读取似乎矛盾 | 区分轻量业务上下文、素材目录元数据、原始字节和工具目录；CHAT 不挂载文件，读取/执行只物化本轮允许的精确引用 |
| 同会话是否等于同一 Codex thread | 不等于。模型线程只是按 Agent/scope/profile 分区的推理缓存，业务事实持久于平台 |
| 点将是否给予无限执行权限 | 否。记录 task/assignment/Agent/操作/资料/现有费用授权范围；新的资料外发、工具、费用边界须重新授权 |
| INSPECT 已有枚举但未接通 | 不广告可用能力；先实现受控读取或返回能力不可用，不把明确的文件理解问题降级成猜测回答 |
| “无工具”是否已经得到保证 | 当前原候选只证明到 read-only-constrained；严格无工具必须有实际引擎工具目录/负向证据，不能把 sandbox 或 never approval 当证明 |

## 3. 长期模块边界

```text
Web / 其他客户端：同一会话与媒体内容块
             │ 一次用户意图 / 幂等键
             ▼
InteractionAdmission（身份、作用域、固定输入、持久受理）
             ▼
ConversationOrchestrator（上下文选择、路由/规划、澄清、恢复）
     ┌───────┼──────────────────┐
     ▼       ▼                  ▼
CHAT profile 受控资料读取       ExecutionCoordinator
轻量上下文   精确内容授权       Grant + 能力 + run/producer
     │       │                  │
     └───────┴─────结果/状态─────┘
                       ▼
既有 message + parts / asset 引用 + durable event journal
                       │
              个人归档 / 正式交付 / 用户验收
```

建议放在既有 chat 与 agent 模块，不先拆新微服务：chat 管会话/admission/context/event；agent 管目标能力、授权执行、runtime 和产物；workspace 管个人资产；正式交付领域保留其 producer/版本/验收规则。跨模块调用以应用服务和 outbox 协调，不让 Web 串行调多个写接口承担可靠性。

## 4. 长期上下文与能力策略

| 层次 | 内容 | 加载规则 |
| --- | --- | --- |
| C0 对话事实 | 当前输入、角色身份、必要历史摘要、任务状态 | 轻量 CHAT 可用；按 scope 授权和源版本冻结 |
| C1 素材目录 | 文件/资产 ID、精确版本、名称、MIME、可见状态 | 供判断引用；目录不代表已经看过内容，不暴露私有路径/token |
| C2 内容 | 本轮图片、音频、文本/文件字节或受控提取片段 | 仅在明确需要且授权后读取；不默认把全部历史媒体塞入上下文 |
| C3 能力 | 本轮允许工具、输入输出声明、执行策略 | 仅在相应读取/执行 profile 中启用；不是把平台全部工具交给模型 |

动态加载发生在平台可验证的准备阶段；模型可建议补读，但不能自行授权。已授权 execution 内可以多步读取/澄清/生成，不按每条自然语言句子强制重新路由。等待用户澄清时持久化待办，释放实际执行资源；恢复必须重新验证授权/assignment/版本。

快速聊天不接收 shell/stdout/内部 reasoning/全部工具轨迹。执行完成只发布用户可见成果、必要说明及来源引用；下一轮通过 context resolver 按需读取成果，而不是复用带所有工具权限的旧线程。

## 5. 与当前源码的映射

| 长期职责 | 当前基础 | 后续补齐 |
| --- | --- | --- |
| 持久受理/轮次 | ChatDeliberationService 与 request/turn | 多步骤 interaction 关联、可信身份全链路、幂等统一入口 |
| 事件与投递 | ChatDeliberationOutboxRelay/event journal | 逐目标能力、步骤状态与媒体事件，不能只发现代 wire |
| 权威上下文 | Context Snapshot / thread binding | 冷线程可重建正文/摘要、精确素材授权、宋江与外部 runtime 同合同 |
| 路由 | InteractionRouter CHAT/INSPECT，拒绝 execute hint | 新 orchestration admission 与结构化执行意图桥接，原 endpoint 边界不变 |
| 实际执行 | PersonalWorkspaceExecutionService、native file bridge | CONVERSATION 用途、不自动归档、run/part 关联 |
| 文件与交付 | workspace-private、task-artifacts-private、formal delivery | 资产引用、多项主动保存、选定成果受信晋升 |
| Web | 现有会话 composable/reducer | parts 混排、统一阶段、直接办理/澄清、引用修改/保存/验收 |

合并已有代码只建立上述“当前基础”，不是自动实现“后续补齐”。本轮实测和剩余 F1–F4 情况以 `integration-baseline-20260928.md` 为准，不用旧分支 acceptance 数字冒充新树验证。

## 6. 临时兼容措施与退出条件

| 临时措施 | 隔离位置 | 退出条件（不是自动删除命令） |
| --- | --- | --- |
| 旧 `/chat/stream` 文本协议 | legacy admission adapter | 所有受支持客户端迁移/明确停止支持，旧在途请求完成，回放/恢复覆盖；迁移期不偷偷改旧含义 |
| 老 runtime 没有新媒体/用途能力 | target capability adapter | 实际注册/readback 证明支持新合同；未升级自家接应仍能使用原已支持功能 |
| read-only-constrained 引擎 | CHAT engine adapter + honest capabilities | 同授权 Provider 下的确切引擎证明工具不暴露/不可调用，才升级为 no-tools 声明；不擅自增加付费 Provider |
| 正式成果复制字节 | formal promotion adapter | 存储/ACL 能安全共用不可变对象时再优化；物理去重不是本需求前置 |
| 图像先行实现 | 功能交付切片 | 音频/文本/通用文件及完整验收通过，才能标整个 feature 完成 |

不长期保留双套消息、双套事件日志或“一个聊天系统套另一个聊天系统”。不要求立刻重写现有 API/全盘迁移旧文件。

## 7. 本次交付与后续实施

本次交付：四仓新 feature 分支、真实代码整合提交、范围内自检、长期方案与详设。未授权事项：develop 合入、release 分支、服务/Agent 更新、迁移真实数据库、浏览器付费生成。

后续实施顺序：
1. **U0 基础收口**：完成能力协商、冷上下文、真实 INSPECT 声明、必要身份/迁移/机器 JWT 回归，记录最终树。
2. **U1 统一 admission/grant/关联合同**：落实下一份详设中的幂等、授权、执行准入和状态恢复。
3. **U2 图片纵切**：无/有参考图、直接生成、必要澄清、未归档继续修改、预览/下载、精确验收。
4. **U3 完整多媒体与归档**：音频、文本选区、文件、混排、保存失败恢复、双接应。
5. **U4 兼容收敛与发布准备**：迁移/隔离/恢复、实际部署与真实端到端；达到各自条件再停止旧适配。

任务可按独立工作树和路径并行；真实依赖才阻塞。Owner 自检，无独立 Reviewer；Gradle 经 orchestrator。性能只观测，真实权限、锁、幂等、传输错误与用户取消保留。
