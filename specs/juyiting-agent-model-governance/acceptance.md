# 聚义厅 Agent 模型、接单与可交付技能治理 R1 — 验收标准

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：好汉实际模型与能力治理。**

### 必须验证的业务结果
缺失/未知/配置与实际不一致清楚展示；详情无额外模型调用；推荐/费用只消费授权事实，不猜价格。

### 不回归边界
用户模型偏好不是可用性证明；不写死旧模型名单、价格或用品牌替代能力，不把声明技能当执行成功。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


更新日期：2026-09-18。状态：`ready`，尚未实施/验证/发布。本文件定义未来可观察的验收证据，不能以文档完成替代测试或用户验收。

## A. 模型、价格簿与计费智力值

- [ ] 授权用户能在 Agent 详情看到模型名称、route version、来源、观察时间、价目表版本与“计费智力值不代表能力/权限”的固定说明。
- [ ] `VERIFIED_RUNTIME`/`TASK_ROUTE` 可按 current binding 产生解释性展示；`SELF_REPORTED` 可显示来源但不能产生权威分数或费用预估。
- [ ] 同一 immutable pricebook 与标准工作负载下，服务端用精确计算得到 `ceil(100*C/Cmax)` 的 1–100 分；缺模型、缺价目表、零/非法最大成本均为 `UNKNOWN`，绝不显示 0 或猜测值。
- [ ] 更新价格簿后，历史分数/估算仍带原 `priceBookVersion`/snapshot，历史解释不被重算篡改。
- [ ] 模型观测/自报 API 不接受 Provider credential、prompt、账户标识或客户端伪造 trust source。

## B. 悬赏模型费用估算

- [ ] 估算请求必须含显式 `agentId` 和 `expectedTaskVersion`；隐式 UI selected state、跨 tenant/client、越权任务、self-reported-only route、版本冲突均不能得到可信估算。
- [ ] 合法调用返回模型/路由、不可变 pricebook、四类 token、estimated/worst 精确金额、`ESTIMATE_ONLY`、`charged=false`、`persisted=false` 和真实 provenance。
- [ ] API/SQL/事件断言证明 estimate 不新增或修改 quote/order/hold/ledger/outbox/task member/task version，不调用 Provider；同版本同输入可重算。
- [ ] 无权威 usage receipt 时 `actualCost.status=UNKNOWN`；UI 不把预估显示为实际费用、扣款或锁价。

## C. 默认 owner-only 与外部精准邀请

- [ ] 没有 policy 记录的 Agent 等效 `OWNER_ONLY`；owner 内、原有 ACL 允许的任务保持既有行为。
- [ ] 外部 owner 对 `OWNER_ONLY` Agent 发起 assign 被服务端拒绝；仅隐藏 UI 不能构成通过。
- [ ] 在同 tenant/client、task ACL 合法、current binding 正确、目标 `agentId` 精确且 policy 为 `EXTERNAL_OPT_IN` 时，外部 assign 只产生 `INVITED`，不自动 claim/start/报价/扣费。
- [ ] 被邀请 Agent 的当前 owner/授权身份接受后才进入现有可执行成员路径；未经邀请、过期/旧 binding、越权或跨 scope 均不能接受。
- [ ] policy 更新具有 CAS、`Idempotency-Key`、审计和 readback；关闭外单阻断新邀请但不静默终止已接受/运行任务；binding/owner 转移后 effective policy 重置为 `OWNER_ONLY`。
- [ ] 调用方不能由错误码、profile 列表或搜索接口枚举其他 Agent 的外单开关、成员私密状态或任务内容。

## D. 可交付技能与自动总结

- [ ] UI/API 明确区分 runtime abilities、confirmed deliverable skills 和 owner-only skill candidates；confirmed skill 不被解释成市场商品、安装、ACL 或付款资格。
- [ ] taxonomy R1 可表达六类技能、canonical `skillKey`、交付物类型、限制及 taxonomy version。
- [ ] 只有已接受、可归因、结构化的 outcome/任务元数据能生成候选；失败、取消、未验收、仅分享、无法归因和私有正文/文件内容均不能生成或泄露为公开技能。
- [ ] 同一 outcome 重放按 evidence fingerprint/rule version 去重；候选从 `PENDING` 经过 owner 的 CAS/幂等决策才会 `CONFIRMED` 或 `DISMISSED`。
- [ ] 非 current owner 无法读取候选/完整证据或确认、编辑、驳回；binding 转移后旧 confirmed skill 对外隐藏为待重新确认，历史审计保留。

## E. 回归、兼容和发布证据

- [ ] `/agent/map` 与 `/agent/roster` 继续独立；不出现 `/agent/active` 回流；任务分配继续显式传递目标 Agent。
- [ ] 新 profile/estimate/settings/skill 请求在登录、logout、client/Agent 切换、网络失败和未知字段时丢弃旧响应，不污染原任务、经济或聊天状态。
- [ ] 新 schema/migration、feature flag 默认/启用、API/Web exact SHA、定向测试、构建制品、部署健康和线上业务 readback 被记录在 release manifest；技术发布不写成用户验收。

## Verification evidence

- API revision: 未开始。
- Web revision: 未开始。
- Commands/tests: 本轮只完成设计文档结构、内部链接与 YAML 语法检查；不运行应用构建、部署或 Flow Run。
- Result: 需求已完成业务设计并进入版本计划，等待后续按唯一运行台账启动实施。
