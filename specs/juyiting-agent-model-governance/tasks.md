# 聚义厅 Agent 模型、接单与可交付技能治理 R1 — 实施拆分

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：好汉实际模型与能力治理。**

**实施目标：** 读取实际配置/可信运行观察→区分配置值和实际使用值→展示模型及来源→推荐/执行按各自合同使用。
**责任落点：** 模型路由/配置提供模型事实；API投影来源和观察；Web好汉详情展示；定价由费用模块负责。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：用户模型偏好不是可用性证明；不写死旧模型名单、价格或用品牌替代能力，不把声明技能当执行成功。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：缺失/未知/配置与实际不一致清楚展示；详情无额外模型调用；推荐/费用只消费授权事实，不猜价格。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


更新日期：2026-09-18。状态：设计就绪、**尚未启动实施**。本文件是版本拆分，不是 `docs/implementation/TASKS.yaml` 运行台账；不在本次登记 Owner、不创建运行任务、不修改运行台账。

## 0. 实施前共同冻结项

- [ ] 从 exact API/Web `develop` 盘点现有 canonical binding、task member 邀请/接受状态、artifact outcome、模型路由和经济 quote 数据表；记录不触碰 `agent-economy-marketplace` 冻结 bundle 的证据。
- [ ] 确认 reference pricebook 的受控发布来源、模型 ID 规范、标准工作负载和 `REFERENCE_PRICE_BOOK_NOT_PROVIDER_BILLING` 文案；不得把 synthetic/provider 外部价格写成事实。
- [ ] 对 external invite、binding transfer、task ACL、成员状态转换完成 API Owner 的 ACL/事务自检；若已有 accept endpoint 可安全复用，记录兼容裁决，否则按 design 新建受控 decision endpoint。
- [ ] 将 taxonomy R1、`skillRuleVersion` 映射表和可消费的 accepted outcome metadata 固定成版本化资源；不读取任务正文/私有文件内容。
- [ ] 在实施开始时创建单一责任 Owner 与 path-scoped worktree；普通代码由 Owner 自检后合组件 `develop`，不创建独立 Reviewer。

## 1. API 工作包

### A1 — 模型事实、价目表与计费智力值

- [ ] 新增 append-only 模型观测/self-report、不可变 reference pricebook 和 score snapshot 的 schema/迁移；存量 effective policy 默认为 `OWNER_ONLY`。
- [ ] 实现受信内部 runtime observation ingest 与 owner self-report；拒绝客户端伪造 trust source、密钥/提示词/Provider 账号数据。
- [ ] 实现 current binding 的模型选择、`billing-intelligence-v1` 精确分数计算和 `GET governance-profile`；未知不得填零。
- [ ] 以追加字段兼容 `POST /agent/roster` summary；不改 `/agent/map`、不恢复 `/agent/active`。

### A2 — 无副作用的模型费用预估

- [ ] 实现 `POST /agent/tasks/{taskId}/model-cost-estimates` 的显式 target、task CAS、route resolver 和 immutable pricebook 计算。
- [ ] 证明该 RPC 不触碰 quote/order/hold/ledger/outbox/member/task 版本，也不调用 Provider；`actualCost` 在无 receipt 时固定 `UNKNOWN`。
- [ ] 不改 `FundedBountyQuoteCalculator`、`FundedBountyPreviewPriceBook`、既有 claim/quote 经济语义或冻结 SDD；如有共用纯算术，应以新 adapter 隔离 provenance。

### A3 — 接单策略与受控外部邀请

- [ ] 实现 policy CAS、idempotency、audit/outbox、binding transfer reset 和 profile readback。
- [ ] 将 `/assign` 的 external target 分支限制为同 scope + `EXTERNAL_OPT_IN` + 精确 agent + `INVITED`；owner 内原有 assignment 语义不得无意改变。
- [ ] 实现/适配外部 invitation decision，确保 acceptance 前不可 claim/start；错误统一且不泄露 policy/成员私密状态。
- [ ] 覆盖 tenant/client/owner、旧 binding、重复成员、并发策略更新、关闭后的新邀请和已接受任务稳定性。

### A4 — 可交付技能和确定性候选

- [ ] 建立 taxonomy 定义、confirmed skill/candidate/audit schema 和纯规则映射；明确技能市场商品/安装 entitlement 与本领域不相同。
- [ ] 接入已接受、可归因 outcome 的 outbox/inbox 消费，按 evidence fingerprint 去重生成候选；不消费正文、prompt、私有 artifact 内容或失败/取消/未验收结果。
- [ ] 实现 confirmed skill public read、owner-only candidates、candidate decision CAS/idempotency 和 binding transfer `REQUIRES_RECONFIRMATION`。
- [ ] 记录 skill candidate 事件/replay/错误恢复；不可因事件重放多次公开技能。

## 2. Web 工作包

### W1 — Agent 模型与技能档案

- [ ] 在名册/Agent 详情增加治理摘要和详情，展示 model/source/version/observedAt/pricebook 与计费智力值免责声明；不使地图依赖 roster 新字段。
- [ ] 分开呈现 confirmed deliverable skills、owner-only candidates 和 runtime abilities；候选支持确认、编辑展示描述、驳回与错误/冲突恢复。
- [ ] 认证 generation、client、Agent 切换时取消/丢弃旧 profile/candidate 响应；治理数据只内存保存，不写入原交易或任务恢复队列。

### W2 — 悬赏模型费用估算

- [ ] 在任务详情/指派步骤仅使用显式 `agentId` 调用 estimate；展示预估/最坏/模型路由/pricebook/provenance 与“未扣款”说明。
- [ ] 处理 `UNKNOWN`、route/price unavailable、task version conflict、权限失败和网络错误；任何失败不能显示 0 或将预估贴为实际。
- [ ] 不替换既有 bounty quote、claim、余额、结算 UI，不新增真实支付/Provider 操作。

### W3 — 接单范围与邀请状态

- [ ] 仅在 owner 自己的 Agent 设置中展示真正可操作的 policy 控件，默认 `OWNER_ONLY`；非 owner 不展示假开关或私密原因。
- [ ] 外部任务仅呈现“邀请已发出/等待接受/已拒绝”等现有成员状态，不设计公开 Agent 市场、搜索或自动认领。
- [ ] 重试 mutation 时保留同一幂等键；409 后刷新 exact profile/member 并要求用户基于新版本操作。

## 3. 集成、测试与发布工作包

- [ ] API Owner 对迁移、ACL、CAS/outbox、成员状态和经济域隔离完成针对性自检；Web Owner 对 map/roster、显式 target、身份切换和无障碍文案完成自检。
- [ ] 同一 API transaction/schema 路径只有一个实施 Owner；按实际资源互斥使用 orchestrator/Flow，不运行并行 Gradle。
- [ ] 合入 API/Web `develop` 后，用 exact commit/tree 建立 release candidate；正式 API/Web 测试、构建、同 Run 制品和部署遵循当时有效的 Flow/本地授权政策。
- [ ] 发布证据需包括 migration/readback、开关、API/Web SHA、测试摘要、制品摘要、部署健康和至少一次 owner/external/skill candidate 业务 readback；用户验收与技术发布分别记录。

## 4. 明确不在实施包内

- 真实 Provider usage receipt、价格抓取、实际账单核对、真实扣款/报价/托管/结算；这些进入 2.0 经济合同。
- public marketplace、跨 tenant/client 外单、Agent discovery、自动接单/重派、按计费分自动选择 Agent。
- LLM 生成或自动确认技能、从私有任务文本/成果挖掘技能、技能商品自动上架/安装/授权。
