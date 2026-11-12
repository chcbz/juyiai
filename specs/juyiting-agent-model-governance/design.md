# 聚义厅 Agent 模型、接单与可交付技能治理 R1 — 详细设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：好汉实际模型与能力治理。**

### 最小责任链
模型路由/配置提供模型事实；API投影来源和观察；Web好汉详情展示；定价由费用模块负责。

读取实际配置/可信运行观察→区分配置值和实际使用值→展示模型及来源→推荐/执行按各自合同使用。

### 实施约束
用户模型偏好不是可用性证明；不写死旧模型名单、价格或用品牌替代能力，不把声明技能当执行成功。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


更新日期：2026-09-18；契约版本：`juyiting-agent-governance-v1`。本文件是待实施的 API/产品合同，不表示下列接口、表或事件已经上线。

## 1. 术语、事实源与信任等级

| 术语 | 定义 | 可用于 |
| --- | --- | --- |
| canonical owner / binding | 当前持久绑定到 Agent 的 owner、tenant、client 与 binding version；不能由展示昵称推断 | 策略修改、外单资格、技能确认 |
| 模型观测 | 一个 Agent 在特定 binding 下使用/声明某模型与路由的版本化记录 | 模型展示、历史解释 |
| 模型路由 | 服务端为特定任务解析出的模型及 route version | 任务费用预估；可作为可信展示来源 |
| 参考价格簿 | 平台管理、不可变版本的模型单位费率与标准工作负载 | 估算、计费智力值；不是 Provider 账单 |
| 计费智力值 | 按模型标准工作负载费用归一化的 1–100 展示分 | 仅展示/排序辅助 |
| runtime ability | Agent runtime 上报的建议标签 | 调度/推荐/展示 |
| deliverable skill | 由目录定义且由当前 owner 确认，可对外展示的交付能力 | 可交付档案 |
| skill candidate | 从可信任务结果按规则生成、尚待 owner 决策的建议 | 审阅队列 |

### 1.1 模型来源优先级

服务端生成 `trustSource`，客户端不可自行指定：

1. `VERIFIED_RUNTIME`：受管、签名或服务端认证的运行时观测；可用于展示、分数和历史解释。
2. `TASK_ROUTE`：服务器为可访问任务实际解析出的路由；可用于该任务估算，也可作为展示事实。
3. `SELF_REPORTED`：Agent owner 的声明；只用于展示，不能计算权威预估或计费智力值。
4. `UNKNOWN`：没有可用的可信来源或模型不在有效价格簿中。

同一用途优先选择当前 binding 下的 `VERIFIED_RUNTIME`；无该记录时可选择尚有效的 `TASK_ROUTE`；再无则显示最近 `SELF_REPORTED`；不得把历史 binding、过期/撤销观测或另一 tenant/client 的记录拼接为当前模型。每个展示值必须附 `observedAt` 和来源。

### 1.2 价格簿与精度

- R1 使用平台管理的**参考**价格簿，字段 `priceBookVersion` 不可变；费率 provenance 固定为 `REFERENCE_PRICE_BOOK_NOT_PROVIDER_BILLING`，除非将来独立的经济合同定义了更严格来源。
- 金额为 decimal-string 的最小单位 `referenceCostMicro`，服务端用精确整数/十进制计算；前端不得以浮点重算权威结果。
- 价格簿记录每模型的 `input/cachedInput/output/reasoning` 单位费率、适用模型 ID、状态和 `standardWorkloadProfile`。价格簿更新只新增版本，绝不就地覆盖历史费率。
- R1 不提供面向普通用户的价格簿编辑接口；价目表发布属于受控平台配置/迁移，须有审计和回滚版本。

## 2. 角色、可见性与权限矩阵

| 操作 | 任务发布者 | 当前 Agent owner | 被邀请 Agent 执行身份 | 无关同 scope 用户 | 跨 tenant/client |
| --- | --- | --- | --- | --- | --- |
| 查看公开 confirmed skills | 可（按现有 Agent 可见性） | 可 | 可 | 仅现有 profile ACL 允许时 | 不可 |
| 查看模型/计费分说明 | 可（按现有 Agent 可见性） | 可 | 可 | 仅现有 profile ACL 允许时 | 不可 |
| 读取候选技能/完整证据摘要 | 不可 | 可 | owner 授权的管理身份可 | 不可 | 不可 |
| 修改模型 self-report | 不可 | 可 | 不可，除非已是 owner 授权身份 | 不可 | 不可 |
| 写入 verified runtime 观测 | 不可 | 不可 | 不可 | 不可 | 不可；仅受信内部运行时 |
| 修改接单策略 | 不可 | 可 | 不可，除非 owner 授权身份 | 不可 | 不可 |
| 请求任务模型估算 | 可，且对任务有读/派单权限 | 可，若对任务有权 | 不可（除非同具任务权限） | 不可 | 不可 |
| 发起外部精准邀请 | 可，且任务 owner/ACL 允许 | 不能替代任务 owner | 不可 | 不可 | 不可 |
| 接受/拒绝外部邀请 | 不可 | 可 | 仅具当前 binding 授权的 Agent 身份 | 不可 | 不可 |
| 确认/驳回候选技能 | 不可 | 可 | 不可，除非 owner 授权身份 | 不可 | 不可 |

所有 Agent 私有读取先核验 trusted principal 中的 tenant、client、owner 与 current canonical binding。不存在和越权统一返回不泄露细节的 404/`AGENT_NOT_ELIGIBLE`；不能由 `agentId`、昵称、旧 binding 或默认 tenant 推导所有权。

## 3. 用户体验与业务流程

### 3.1 名册与角色详情：模型、分数和技能

1. 名册卡保留既有角色信息；在不破坏卡片密度的前提下显示“模型”摘要和“计费智力值”。未知显示 `未记录`，不是 `0`。
2. 点开详情显示：模型名称、`routeVersion`、`trustSource`、`observedAt`、`priceBookVersion`、标准工作负载说明和固定提示：**“计费智力值按参考模型费用计算，不表示效果、可靠性、权限或可接单资格。”**
3. 技能分为三个区：`已确认可交付`、`候选待确认`（仅 owner 自己可见）、`运行时能力`。候选只显示 taxonomy 名、建议交付物类型、规则版本、任务数量/时间，不复制任务正文或私有 artifact 内容。
4. 地图仍只使用 `/agent/map`；名册仍使用 `/agent/roster`。新详情请求失败不影响地图实体或 roster 的主体加载。

### 3.2 张榜/揭榜：费用估算

1. 任务发布者先在原任务流程中**显式选择 `agentId`**；不得根据 UI 当前选中状态或地图位置隐式带入。
2. 输入预计及最坏 token 分项，或接受由前端根据任务类型提供的可编辑预填。点击“估算”调用独立无副作用接口。
3. 结果展示模型/路由、价格簿版本、来源、估算费用、最坏费用和免责声明：`仅供估算；未扣款、未创建报价、未锁定模型或价格。`
4. 若 route/pricebook 不能可信解析，显示不可估算并阻止把该结果粘贴为“实际费用”。用户仍可按现有任务能力继续编辑/保存；R1 不改变已有报价或认领链路。
5. 未来若有权威 usage receipt，历史任务可展示 `ACTUAL_VERIFIED`；R1 没有 receipt 时只能为 `UNKNOWN`，不得以预估替代。

### 3.3 接单范围与外部精准邀请

#### 策略

| 枚举 | 含义 | 默认 |
| --- | --- | --- |
| `OWNER_ONLY` | 仅接受当前 canonical owner 发起、且现有 task ACL/binding/scope 都允许的任务 | 是；缺失记录也按此处理 |
| `EXTERNAL_OPT_IN` | owner 明确允许外部 owner 在同 tenant/client 内对已知精确 Agent 发起邀请；仍需逐单接受 | 否 |

Agent owner 在“接单范围”设置中明确看到默认和边界。更新使用 CAS、幂等键和审计。关闭外单只阻止**新的**外部邀请；已产生的邀请、已接受成员和已开始任务按既有任务状态机取消/重派，不静默终止。

#### 外部邀请流程

1. 外部任务发布者必须已经有权看到该 Agent 或持有合法精确 `agentId`，创建任务时将目标作为显式 `agentId` 传到现有 assignment API。
2. 服务端在同一事务内验证：任务版本、任务 owner、caller 权限、目标 Agent current canonical binding、同 tenant/client、策略为 `EXTERNAL_OPT_IN`、当前未存在可执行同类成员，并执行既有幂等/成员约束。
3. 通过后创建 `INVITED` 成员而非直接 claim/run；返回“已发送邀请”。不得因 opt-in 自动开始、自动报价或自动冻结资金。
4. 当前 Agent owner/被授权 Agent 身份可接受或拒绝。接受后才进入既有可分配/可 claim 的成员状态；拒绝或策略变化后的新请求均不泄露具体拒绝原因。
5. `OWNER_ONLY`、跨 scope、binding 已变、任务版本冲突或无权限时，外部调用获得泛化 `AGENT_NOT_ELIGIBLE` 或既有版本/ACL 错误；前端不要据此显示“该 Agent 拒绝外单”的私密状态。

不提供 public browse、外单搜索、模糊推荐、自动认领、跨 scope 直接 DM/任务内容暴露。绑定/owner 转移会将策略重置为 `OWNER_ONLY`，新 owner 必须重新明确开启。

### 3.4 可交付技能与任务自动总结

#### taxonomy R1

每个 canonical `skillKey` 由平台目录维护，包含显示名、分类、允许的交付物类型、限制/所需授权和目录版本：

| 分类 | R1 技能示例 | 典型交付物 |
| --- | --- | --- |
| 产品与策略 | 需求澄清、方案设计、调研分析、技术文档 | brief、方案、调研报告、说明文档 |
| 工程实现 | 前端实现、后端实现、接口集成、数据处理 | 源码变更、接口定义、数据脚本 |
| 质量保障 | 测试设计、自动化测试、回归验证、故障分析 | 测试计划、测试代码、回归报告、故障报告 |
| 平台运维 | CI/CD 配置、可观测性、发布支持、运行排障 | 流水线配置、仪表盘、发布记录、排障报告 |
| 内容与知识 | 结构化整理、知识库维护、文案与翻译 | 知识条目、结构化数据、文案、译文 |
| 协作交付 | 任务拆解、上下文整理、成果打包、验收协作 | 工作项、context pack、交付清单、验收记录 |

`deliverable skill` 不等同技能市场商品、可执行包、安装 entitlement、许可证或收费权限。目录中标注的限制只作交付说明，不自动授予权限。

#### 确定性候选规则 R1

- 只消费已接受且可归因的 `artifact outcome` / 任务完成裁决、`requiredAbilities`、work item type 和已脱敏的结构化 artifact metadata。
- 不读取自由任务正文、聊天内容、prompt、文件正文、密钥、运行日志；不调用 LLM 或外部 Provider。
- `skillRuleVersion` 将上述结构化类型映射到一个或多个 `skillKey`。候选携带 opaque task/outcome reference、Agent/binding、规则版本、生成时间、证据摘要和 evidence fingerprint。
- 处理幂等键为 `(agentId, bindingVersion, skillKey, evidenceFingerprint, skillRuleVersion)`；同一 outcome 重放不可重复生成。失败、取消、仅分享、未验收、归因不明、旧 binding 不匹配的任务不生成候选。
- 候选状态为 `PENDING` → `CONFIRMED` / `DISMISSED` / `SUPERSEDED`。owner 可确认、调整非安全展示描述或驳回；驳回理由为私有可选备注。新证据不能静默推翻驳回，须新 fingerprint 或由 owner 手动重新打开。
- 对外 profile 仅返回 `CONFIRMED`；候选和其私有证据只对 current owner 可见。任务发布者未来可以提供 endorsement，但 R1 没有修改 Agent 技能档案的权力。

## 4. 数据模型、版本与历史语义

表名是实现建议，须在 API migration 盘点后避免与现有表冲突；所有 ID、金额、版本和时间在 API 中使用字符串。

| 建议实体 | 核心字段 | 不变量 |
| --- | --- | --- |
| `agent_model_observation` | `observation_id, agent_id, binding_version, model_id, display_name, route_version, trust_source, observed_at, revoked_at, version` | append-only；client 不能写 trust source；旧 binding 不能成为当前事实 |
| `agent_model_declaration` | `agent_id, binding_version, model_id/display_name, route_version, declared_by, declared_at, version` | 仅 owner；只能产生 `SELF_REPORTED` |
| `agent_reference_price_book` / `rate` | `price_book_version, model_id, token_rates, standard_workload_profile, provenance, active_from` | 已发布版本不可更新/删除；R1 不等于真实账单 |
| `agent_engagement_policy` | `agent_id, binding_version, policy, version, updated_by, updated_at` | 无记录=`OWNER_ONLY`；binding 变化必须重置 |
| `agent_engagement_policy_audit` | `audit_id, old/new policy, binding_version, actor, idempotency_key, occurred_at` | 每次有效写入可追溯 |
| `agent_deliverable_skill` | `agent_id, binding_version, skill_key, taxonomy_version, state, public_description, evidence_summary, version` | 只有 confirmed 可公开；不承载安装/授权事实 |
| `agent_skill_candidate` | `candidate_id, agent_id, binding_version, skill_key, state, rule_version, evidence_fingerprint, evidence_refs, version` | 证据私有、去重、状态 CAS |

### 4.1 计费智力值公式

对一个当前可信模型，取其所在 active `priceBookVersion` 的标准工作负载 `W`，按四类 token 费率计算成本 `C(model, W)`。令 `Cmax` 为该价格簿内所有可计价 active 模型在同一 `W` 下的最大成本：

```text
intelligenceScore = ceil(100 * C(model, W) / Cmax)
```

- 成本和中间结果均为精确整数/十进制；结果限制在 `1..100`。
- 模型没有可信来源、未在 active pricebook、`Cmax <= 0`、或工作负载缺失时，返回 `UNKNOWN`，不回退到 self-report、不显示 0。
- 输出包含 `scoreFormulaVersion`、`priceBookVersion`、`modelId`、`trustSource` 和 `computedAt`。历史估算/历史 profile 可保存 score snapshot，之后价格簿更新不能重写其解释。
- UI 名称固定为“计费智力值”，并显示提示语，避免将费用高低伪装为质量判断。

### 4.2 Owner/binding 变化

binding/owner 变化不得继承新 owner 未确认的接单开放状态：新 binding 的 effective engagement policy 为 `OWNER_ONLY`。模型观测、声明、候选和已确认技能保留为历史审计记录，但当前 profile 只选择 current binding 证据；既有已确认 skill 进入 `REQUIRES_RECONFIRMATION`（对外隐藏），直到新 owner 确认或显式撤销。历史任务、历史估算和已接受的外单不被改写。

## 5. API 合同

统一使用现有 `JsonResult`；成功 `{"code":"E0","data":...}`，失败保留真实 HTTP 状态与稳定 `code`。响应 `Cache-Control: private, no-store`。未知字段、重复 JSON key、非法 decimal-string、负数、溢出和不支持 enum 均为 400；所有 version 采用规范正整数字符串。

### 5.1 Agent 治理 profile（读取）

`GET /agent/{agentId}/governance-profile`

成功数据（示例字段，`null` 不代表 0）：

```json
{
  "agentId":"a-123",
  "bindingVersion":"42",
  "model":{
    "status":"KNOWN",
    "modelId":"managed-model-x",
    "displayName":"Managed Model X",
    "routeVersion":"route-2026-09-a",
    "trustSource":"VERIFIED_RUNTIME",
    "observedAt":"1780000000000",
    "priceBookVersion":"reference-2026-09-r1"
  },
  "billingIntelligence":{
    "status":"KNOWN",
    "score":"67",
    "scoreFormulaVersion":"billing-intelligence-v1",
    "priceBookVersion":"reference-2026-09-r1",
    "disclaimer":"REFERENCE_COST_NOT_CAPABILITY"
  },
  "engagementPolicy":{"effective":"OWNER_ONLY","version":"3","editable":true},
  "deliverableSkills":[{"skillKey":"engineering.frontend","state":"CONFIRMED","taxonomyVersion":"r1","deliverableTypes":["SOURCE_CHANGE"]}],
  "runtimeAbilities":["ui","testing"]
}
```

若无可信模型，`model.status`/`billingIntelligence.status` 为 `UNKNOWN`，不返回伪造 ID、版本或分数。公开 profile 不返回候选、任务/产物证据、内部 rate 和 self-report 修改人。

`POST /agent/roster` 可在后续兼容扩展中增加只读 `governanceSummary`（模型展示名、分数状态/分数、confirmed skill keys）；旧客户端忽略新字段。`/agent/map` 无需为本版本新增字段。

### 5.2 自报与受信运行时模型观测

`PUT /agent/{agentId}/model-declaration`

- 仅 current owner；请求：`{expectedVersion, modelId, displayName, routeVersion}`；`Idempotency-Key` 必填。
- 数据经白名单/长度/敏感词检查，不允许 provider key、endpoint secret、prompt 或账户标识。
- 成功创建/更新 `SELF_REPORTED` 声明。响应仅说明 `usableForCostOrScore:false`。
- 409：`MODEL_DECLARATION_VERSION_CONFLICT`；404：`AGENT_NOT_ELIGIBLE`。

`POST /internal/agent-model-observations`

- 仅受信运行时服务身份，可写 `VERIFIED_RUNTIME`；服务端从认证主体推导 tenant/client/binding 与 source，拒绝普通 JWT/浏览器请求。
- 请求含 `agentId, modelId, displayName, routeVersion, observedAt, observationNonce`；nonce+binding 去重。
- 不接受 Provider token、请求正文、模型 output 或账单明细。该接口不对普通前端开放。

### 5.3 模型费用估算

`POST /agent/tasks/{taskId}/model-cost-estimates`

请求：

```json
{
  "agentId":"a-123",
  "expectedTaskVersion":"19",
  "routePreference":"DEFAULT",
  "estimatedTokens":{"input":"18000","cachedInput":"4000","output":"6000","reasoning":"3000"},
  "worstTokens":{"input":"36000","cachedInput":"8000","output":"12000","reasoning":"6000"}
}
```

- `agentId` 必填且明确；`estimated` 每类不得大于 `worst`。
- 服务端以 task ACL、任务 owner、current target binding、同 tenant/client 和 route resolver 验证；`SELF_REPORTED` 不得作为成本来源。
- 成功：

```json
{
  "estimateKind":"ESTIMATE_ONLY",
  "charged":false,
  "persisted":false,
  "currency":"REFERENCE_COST_MICRO",
  "agentId":"a-123",
  "taskVersion":"19",
  "modelId":"managed-model-x",
  "routeVersion":"route-2026-09-a",
  "routeSource":"TASK_ROUTE",
  "priceBookVersion":"reference-2026-09-r1",
  "rateProvenance":"REFERENCE_PRICE_BOOK_NOT_PROVIDER_BILLING",
  "estimatedTokens":{"input":"18000","cachedInput":"4000","output":"6000","reasoning":"3000"},
  "worstTokens":{"input":"36000","cachedInput":"8000","output":"12000","reasoning":"6000"},
  "estimatedCostMicro":"12345",
  "worstCostMicro":"24690",
  "actualCost":{"status":"UNKNOWN"}
}
```

- 该 RPC 不创建 `quoteId/orderId/holdId`，不写 bounty quote、账本、outbox、成员或 task 版本；同输入、同任务版本、同 pricebook 应得到相同结果，不需 `Idempotency-Key`。
- 400：`MODEL_COST_ESTIMATE_BAD_REQUEST`；401：`UNAUTHENTICATED`；403：既有 task ACL；404：`TASK_OR_AGENT_NOT_FOUND`（不可枚举）；409：`TASK_VERSION_CONFLICT`；422：`MODEL_ROUTE_OR_PRICE_UNAVAILABLE`；503：`MODEL_COST_ESTIMATE_UNAVAILABLE`。

### 5.4 接单策略、邀请和接受

`PUT /agent/{agentId}/engagement-policy`

```json
{"expectedVersion":"3","policy":"EXTERNAL_OPT_IN"}
```

- current owner、`Idempotency-Key` 必填；有效更新写 policy + audit + outbox（同一事务）。
- 返回 `agentId,bindingVersion,effectivePolicy,version,updatedAt`；409 `ENGAGEMENT_POLICY_VERSION_CONFLICT`。
- binding 变化处理写一条 reset audit，不复用前 owner 的 idempotency result。

现有 `POST /agent/tasks/{taskId}/assign` 的 payload 保持显式 `agentId`/`agentIds`。实现须增加外部目标校验：外部 target 通过时创建 `INVITED` 而非跳过成员状态机；owner 内任务保留既有语义。响应为每个 target 的 `memberId,status,assignmentKind`，不暴露私密拒绝理由。

`POST /agent/tasks/{taskId}/members/{memberId}/external-invitation-decision`

```json
{"expectedMemberVersion":"4","decision":"ACCEPT"}
```

- 仅目标 Agent 的 current owner/被授权当前 binding 身份，`Idempotency-Key` 必填。
- `ACCEPT` 只将 `INVITED` 转入既有接受状态；不自动 claim/start/计费。`DECLINE` 进入既有不可执行终态。
- 409：成员/task version 冲突或不在 invited；404/403：不泄露 member 是否属于该 Agent。

### 5.5 技能读取、候选审阅与决策

`GET /agent/{agentId}/deliverable-skills`：按 profile ACL 只返回 `CONFIRMED`，字段为 `skillKey, displayName, category, taxonomyVersion, deliverableTypes, limitations, confirmedAt`。

`GET /agent/{agentId}/deliverable-skill-candidates?cursor=&limit=50`：仅 current owner；返回 `PENDING/DISMISSED/SUPERSEDED` 候选和脱敏 evidence summary。cursor 不授予权限。

`POST /agent/{agentId}/deliverable-skill-candidates/{candidateId}/decision`

```json
{
  "expectedCandidateVersion":"2",
  "decision":"CONFIRM",
  "publicDescription":"可交付前端页面与自动化回归材料"
}
```

- current owner、`Idempotency-Key` 必填；`CONFIRM` 创建/更新该 binding 的 confirmed skill，`DISMISS` 仅更新候选状态，均写审计/outbox。
- `publicDescription` 是可选短展示文字，按输出限制过滤；不允许塞入任务正文、凭据、客户数据或授权声明。
- 409：`SKILL_CANDIDATE_VERSION_CONFLICT`；404：`SKILL_CANDIDATE_NOT_FOUND`（含越权）；422：`SKILL_CANDIDATE_NOT_CONFIRMABLE`。

## 6. 事件、事务与一致性

| 事件 | 触发 | 最小 payload | 处理要求 |
| --- | --- | --- | --- |
| `agent.model.observed.v1` | verified observation 被接受 | observationId, agentId, bindingVersion, modelId, routeVersion, observedAt | 不携带密钥/输入输出 |
| `agent.engagement-policy.changed.v1` | 策略有效变更或 binding reset | agentId, bindingVersion, old/new policy, version | 与 audit 同事务 outbox |
| `agent.skill-candidate.generated.v1` | accepted outcome 生成候选 | candidateId, agentId, bindingVersion, skillKey, ruleVersion, evidenceFingerprint | inbox 幂等 |
| `agent.deliverable-skill.changed.v1` | confirm/dismiss/reconfirm | agentId, bindingVersion, skillKey, state, version | profile 投影可重放 |

候选生成消费者必须使用 existing outbox/inbox/replay 模式；同一 outcome 重放只产生一条候选。估算 RPC 是同步纯计算，不发布事件、不增加任务 aggregate version。策略写入和邀请创建要各自遵从现有 transaction/CAS/member 状态机；不能把“持续等待”实现为越过锁或伪成功。

## 7. 迁移、兼容与回滚

1. 先盘点现有 Agent owner/binding、task member、artifact outcome、价格簿和路由来源；DDL 只新增治理域表/索引，禁止重写冻结经济表语义。
2. 所有存量 Agent 的 effective engagement policy 为 `OWNER_ONLY`，不做批量外单开放。没有模型数据/accepted outcome 的 Agent 维持空态。
3. `POST /agent/roster` 只追加可选 summary；旧 Web/API 继续可用。地图、聊天、既有 assign/claim、经济 quote 与 artifact 流程在开关关闭或新字段未知时保持原行为。
4. 新能力受独立 feature flags 管理：profile display、model estimate、external invite、skill candidates；默认关闭直到 API/Web 同版本发布并完成 ACL/readback。关闭 external invite 不取消已接受任务；关闭 display 仅隐藏新读取入口。
5. 回滚先关闭新入口/策略变更入口，保留审计与历史记录；不得通过删除技能/观测/估算历史恢复。已写 schema 采用向前兼容方式保留。

## 8. 验证与风险控制

### 最小测试矩阵

- 价格簿版本、decimal 精度、四类 token、分数公式/未知分支、历史 snapshot；self-report 绝不能用于权威分数或估算。
- 模型估算在 API/SQL 观察中不写 quote/order/ledger/outbox/task member；task version、route/price 缺失、越权和跨 scope 均按合同失败。
- `OWNER_ONLY` 外部 assign 拒绝；opt-in 后仅同 scope 精确 target 创建 `INVITED`；接受前不可 claim；关闭后只阻断新邀请；binding 变更重置策略。
- policy/candidate decision 的 CAS、重复 `Idempotency-Key`、重放、审计、并发更新和 owner/client/tenant 隔离。
- accepted 可归因 outcome 生成一次候选；失败/取消/未验收/仅分享不生成；候选不含任务正文或 artifact 内容；非 owner 无法读取或确认。
- Web 验证 roster/map 分流、显式 Agent estimate、身份/Agent 切换取消旧请求、UNKNOWN 文案、外单邀请状态、候选确认/驳回和旧任务 UI 不回归。

### 主要风险及控制

| 风险 | 控制 |
| --- | --- |
| 把参考成本误当真实 Provider 账单 | 固定 provenance、`ESTIMATE_ONLY`、不写经济表、actual=UNKNOWN |
| 把高费用分数理解为质量/权限 | 固定“计费智力值”名称、详情解释、拒绝作为 ACL/调度硬规则 |
| 外单绕过 owner 或跨 scope | 服务端 transaction 校验、精确 target、`INVITED` 后二次接受、binding reset |
| 用自由文本或私密成果自动宣称技能 | 只用 accepted structured metadata、确定性规则、候选需 owner 确认 |
| 价格簿更新篡改历史解释 | immutable version、历史 snapshot 和审计 |
| 新 UI 损坏聚义厅数据流 | map/roster 分流不变，详情失败隔离，不重引 `/agent/active` |
