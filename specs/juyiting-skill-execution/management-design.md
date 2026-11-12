> **历史方案（导航核对：2026-11-10）：** 已按2026-10-23用户决定由[原型范围](management-mvp.md)和[管理合同](management-contract.md)取代；本文件保留来源，不是当前实施/验收入口。后文“当前/待实施”只指原日期，不恢复旧框架或新表/端点。

# 技能管理详细设计（SM-1）

> 已取代（2026-10-23）：用户明确以现有原型为准。本文件仅保留为旧方案，不再作为实施范围或验收清单；当前只看[按原型落地方案](management-mvp.md)，不恢复本文件整套框架，也不删减原型已有功能。

日期：2026-10-23；任务：`SKILL-MANAGEMENT-20261023`。关联：[需求清单](management-requirements.md) · [实施计划/验收](management-plan.md)。

**本文是目标设计，不是现存API说明。** 新接口/表/消息需按下述合同实施并通过实际序列化→消费端验证后才可使用。原型数据不是批准商品或真实价格。接口公共规则固定为 `api/docs/interface-standard.md` v1.2（2026-10-14）；不另造通用工作流或兼容协议。

## D1. 架构与权威边界

```text
Agent详情 → SkillManager（同一列表、每行原位展开）
                    ↓ 管理查询 / 报价 / 精确动作 / 原操作恢复
        Agent技能管理应用服务（Owner ACL、CAS、互斥、审计）
          ├─ 现有商品版本/包发布与不可变包存储
          ├─ 现有报价、订单、权益、钱包/账本
          ├─ 技能激活关系 + 管理操作 + 既有installation/attempt
          └─ 既有command/outbox与认证下载、回执、恢复
                    ↓
        Runtime既有安装器/registry/executor
          暂存 → 校验 → 准备回执 → 授权切换 → 激活回执
          不可变包/在途引用 → 精确版本执行与恢复
                    ↓ 当前会话能力目录
        API新准入核验 → 管理投影/任务目录 → Web原行更新
```

不把DB事务说成能原子覆盖Runtime文件系统；准备、激活、API提交、运行目录就绪是可恢复的不同事实。后台管理授权、Runtime物理安装、任务执行授权各自有权威来源。

| 事实 | 权威来源 | 不能用什么替代 |
| --- | --- | --- |
| 可安装/升级候选 | 批准的productVersion、发布指针、权限/兼容性规则 | 本地源码包、版本号排序、网页硬编码 |
| 购买权益及费用 | 当前合法权益、服务器quote、现有订单账本 | 示例价格、Runtime自报、运行费用说明 |
| 当前激活版本 | API激活关系 + 精确Runtime激活证据 | 安装中目标、文件存在、单独订单ACTIVE |
| 当前可运行 | 合法启用关系 + 当前Runtime session目录 + runner/依赖/binding核验 | 已购买、旧session缓存、普通SKILL.md |
| 本次任务可执行 | 现有任务scope/Owner或委托授权 + 固定技能快照 | 管理权限、外单可见性、名称相同 |

普通升级保留**新合同内部**在途执行的精确旧技能包，不是恢复被统一接口切换淘汰的历史wire兼容层。历史协议的隔离按v1.2规范执行，不由本功能重新激活。

## D2. 界面与交互规格

### D2.1 入口、列表与动作

- 继续使用Agent详情“技能”标题行的“管理技能”；管理窗口标题“{Agent名称}的技能”，不另增安装总入口、市场/已安装Tab或仪表盘。
- 每行：名称 + 状态；一行用途；当前版本/候选提示；右侧同列主动作，详情为弱操作。已安装项优先、其余按现有商品稳定顺序，异步更新不把正在操作的行突然换位。
- 显示集合为“合法现有安装/在途操作 ∪ 当前作用域可安装商品”。下架但已合法安装的技能不能因目录删除而消失；缺失候选不伪造“最新”。不在首期增加无数据依据的搜索/筛选区域；后续大量真实数据需要时在现有列表头补紧凑控件。
- 只展开一行，切换展开不丢当前窗口各技能的草稿；展开行仍属于原列表。操作记录在末尾折叠，不展示协议/主机实现细节为默认内容。
- 每行主动作由后端`allowedActions`产生；不能只凭ONLINE或版本字符串推导。隐藏越权动作，暂不可用但用户有资格的动作显示明确原因。

| 当前事实 | 行摘要与主动作 | 行内次操作 |
| --- | --- | --- |
| 未安装、批准商品可用 | 未安装 / 安装 | 能力、权限、费用说明 |
| 已启用、批准新版本可用 | 当前版本→候选 / 升级 | 详情内停用 |
| 已启用、无升级候选 | 已启用 / 详情 | 停用 |
| 已停用 | 已停用 / 启用 | 详情；无新安装入口 |
| 在途/等待连接 | 真实阶段 / 查看进度 | 收起；无第二安装/升级 |
| UNKNOWN或恢复待处理 | 待核对 / 核对结果 | 关联原操作，不新建订单 |
| 确定可恢复失败 | 失败原因 / 重试原操作 | 查看本次attempt |
| 退款等最终失败 | 未安装或旧版仍在 / 查看结果 | 新报价只能显式另起授权，不伪装原重试 |
| 已安装未就绪 | 已安装 · 缺依赖/待连接/待核验 | 具体原因，依权限提供受控处理 |

### D2.2 原位准备、报价与确认

1. 点安装/升级后展开能力差异、权限与购买费用范围，未提交不创建订单。
2. 必需权限全部批准后，后台获取报价；无新增权限且已有合法授权覆盖时可直接准备报价。**不自动勾选新增权限，不自动最终提交**。
3. 报价请求绑定Agent、技能、原/目标版本、状态版本与权限摘要；响应必须匹配当前准备快照。改变任一绑定输入即失效；晚到报价不能覆盖新选择。
4. 报价失败原位显示“重新获取报价”，不跳页；服务端`expiresAt`决定有效性，不新设客户端业务等待门槛。
5. 确认区以紧凑一行保留“技能名 · 目标版本 · 购买价/权益覆盖”，按钮为“确认安装”或“确认升级”。滚动到**整个确认区**而非仅按钮；低高度下仍能同时识别对象与动作。
6. 安装费和运行费用分开展示。金额复用`Money`与`formatSilverMoney`，`amountMinor`十进制字符串、`currency:SILVER`；不把原型“0积分”直接移入真实商品，不用浮点换算。未知运行费用只说明，不进入执行准入。
7. 升级只保留一份“1.0.0 → 1.1.0”与关键差异；保留权限扩张、购买费用、在途影响，折叠工具链解释，去掉重复标题/版本卡与多余留白。

### D2.3 暂存和关闭

组件内`drafts[scopeFingerprint, agentId, skillKey, targetProductVersionId]`保存权限选择、说明展开态、滚动锚点和当前quote。不是新的业务事实库。

| 事件 | 未提交草稿 | 已提交操作 |
| --- | --- | --- |
| 收起/切另一技能行 | 同窗口保留，重开复验quote | 继续后台处理，重开查同operation |
| 改权限/目标/原版本 | 保留仍适用选择但quote失效；新增权限未批准 | 不允许把在途操作改目标 |
| 关闭管理窗口 | 结束本次准备，丢弃未提交quote/勾选；不冒充取消服务器操作 | 本地仅保存安全恢复索引，后台不取消 |
| 刷新 | 不持久化预批准权限；重新准备报价 | 从恢复索引查询服务器，绝不自动新提交 |
| Owner/tenant/client切换 | 清空敏感草稿，终止旧scope请求 | 旧结果不渲染；无权查询原操作 |
| Agent切换 | 不把草稿转给另一Agent | 按Agent隔离索引与响应 |

不在localStorage保存token、原始授权资料或“自动同意”。恢复索引复用现有purchase journal模式，保存scope标识、原requestId/idempotencyKey、操作/订单标识与必要请求指纹；它不能替代服务器ACL或从中恢复可执行授权。

### D2.4 五项UX修正与响应式

- UX1（SM-11）：确认区自带对象摘要；390×480不得只见泛称按钮与下一技能行。
- UX2（SM-10）：`expandedRow`与业务草稿分离；勾选只改对应字段，不重建整块DOM导致details关闭。quote失效要明确说明，不把收起当取消。
- UX3（SM-12）：窗口初始焦点入内；行标题`tabindex=-1`可聚焦，随后Tab按DOM前进。focus trap只在首/末边界循环，不能把“当前不是可Tab控件”一律跳到关闭。过滤真正不可见及闭合details子控件；可见focus ring保留。
- UX4（SM-13）：技能行本身就是唯一标题；版本变化与差异紧凑排布。低高度正文滚动，页头/关闭可达；不通过再加大卡片补救。
- UX5（SM-14）：复用`--hall-text-muted:#68716b`等现有token；离线示例提示采用已有12px辅助字号，不再用难辨的11px浅灰弱化重要限定。不声称据此全站无障碍合规。
- 首轮精确回归视口：1440×1000、390×844、320×844、844×390、390×480。检查滚动、对象上下文、触控目标、焦点、长名称/错误，而非只检查无横向溢出。
- Esc先收起当前行再关窗，退出回原行/管理入口焦点；遮罩关闭与既有一致，点击正文不关闭。关窗不取消已接纳后台操作；显式取消服务器操作不在首期承诺范围。
- 保留加载、读失败原位重试、真实空态、无候选、无管理权限、等待连接、执行中、未知、确定失败及完成状态。不得用空列表掩盖接口错误或自动造数据。

## D3. 管理读模型与事实投影

新增`SkillManagementQueryService`，复用商品、权益、安装证据、Runtime session目录及操作记录；GET没有安装、重新注册或派单副作用。

列表行DTO目标字段（封闭集合；nullable必须显式声明）：

| 字段 | 类型/来源 |
| --- | --- |
| `skillKey,name,description` | string；真实商品/安装元数据，已下架安装仍有安全可读名称 |
| `stateVersion` | decimal string；该scope/Agent/skill管理关系CAS版本；尚无关系为`"0"` |
| `installed` | null或`{installationId,productVersionId,skillVersion,packageSha256,manifestSha256}`，后者摘要可null（说明包） |
| `candidate` | null或`{productVersionId,skillVersion,packageSha256,publicationState,upgradeEligibility}`；只含批准可见候选 |
| `desiredEnabled,admissionEnabled` | boolean；用户期望与API新准入实际开关不同 |
| `runtime` | `{state,reasonCode,observedAt,catalogRevision}`；无可信观察时时间/revision为null，不填当前时间伪造最近核验 |
| `operation` | null或当前操作摘要`{operationId,type,status,stage,attempt,reasonCode,recoveryAction,updatedAt}` |
| `allowedActions` | 动作数组，服务器按身份/状态/发布/财务关系计算 |
| `deniedActions` | `{action,reasonCode}`数组；不附敏感内部信息 |

`runtime.state`目标集合：`UNKNOWN/OFFLINE/VERIFYING/READY/DEPENDENCY_MISSING/PROVIDER_UNBOUND/VERSION_MISMATCH/NOT_EXECUTABLE`。启用、停用和未安装由管理关系表达，不把所有维度压成一个大枚举。

`READY`本身不代表任务可执行：还需`admissionEnabled=true`、合法权益/权限及该任务授权。候选ready与当前版本ready不得混用；离线旧观测可保留时间但标“上次观测”，不能画当前在线绿点。

列表排序冻结在本次视图；仅在用户刷新/明确结束动作后重排。轮询复用既有请求与重试机制，窗口不可见减少无谓查询，但不得因等待长就把业务标失败。不加新的常驻全目录扫描。

## D4. 最小数据增量、索引与迁移

以下实体名为拟新增逻辑模型，物理DDL沿既有表命名/迁移机制落地；不会在文档阶段执行SQL。

| 实体 | 字段与职责 | 约束 |
| --- | --- | --- |
| `AgentSkillBinding`（新增） | tenant/client/agent/skill；activeInstallationId；activeProductVersionId；activePackageSha256；desiredEnabled/admissionEnabled；stateVersion；activationEpoch；pendingOperationId；lastObservation | scope+agent+skill唯一；版本/epoch单调；一个非空pending操作；没有可信安装不能填active |
| `SkillManagementOperation`（新增） | operationId；scope/actor/owner/agent/skill；type；原installation/版本/摘要；目标productVersion/版本/摘要；expectedAgentVersion/sourceStateVersion；quote/entitlement/fundingOrder关联；权限摘要；status/stage；attempt；command关联；requestId/idempotencyKey/requestHash；时间/安全错误 | actor+scope+mutationKind+idempotencyKey唯一；同键不同hash409；原/目标快照创建后不可改写 |
| `SkillManagementOperationEvent`（新增或复用现有等价审计存储） | operationId+eventSequence、attempt、前后状态、来源/操作者、原因、command/message/installation、发生时间与证据摘要 | 追加写、sequence唯一；不是第二套可写“成功状态”或新消息总线 |
| 现有`SkillInstallation`（扩展） | 关联operationId/attempt/activationEpoch，保留每次包安装证据与现有消息fence；升级不覆盖旧成功安装 | 首次安装仍关联真实order；原权益覆盖的升级允许无新order，必须关联合法entitlement+operation；不得伪造购买订单凑外键 |
| 现有quote/order/entitlement（定向扩展） | quote绑定操作类型、原激活关系/目标、权限/费用政策；新付费仍沿真实交易；旧权益安装快照保留，新激活关系引用覆盖权益 | 不把旧ACTIVE/FAILED权益改成新版本安装中；历史金额/摘要不重写；升级覆盖有权威政策而非前端猜测 |

数值型ID、stateVersion/operationVersion、epoch、revision、sequence及可能超出JavaScript安全整数的Long出wire用十进制字符串；attempt沿v1.2用有界正整数JSON number，具体合法范围在SM-T02按现有字段定义固定，不设性能型次数门槛。数据库二进制摘要按既有存储保留，wire为64位小写hex；不是把已有历史摘要重新计算覆盖。

**提交事务**：身份/Owner版本 → 串行化同Agent/skill关系 → 校验目标/quote/权限/CAS → 绑定合法权益或创建真实资金订单 → 插入operation和installation/command/outbox → 设置pending → 提交。网络下载、Runtime通信、Provider调用不在DB事务内。

锁顺序统一接入既有经济事务：actor经济锁 → Agent身份版本/skill binding → 商品、报价与订单 → 钱包/账本 → installation/outbox；实现前枚举现有quote/purchase/result/recovery路径，在同一合同切换中消除反序。不能只锁新管理入口却让旧购买入口绕过互斥；唯一索引是并发底线，异常须回滚整事务。

### 迁移规则

1. 先盘点当前表约束、重复skill权益、实际可信安装和未决操作，产生只读清单；不以“历史FAILED”全部删除解决唯一性。
2. 为每个合法精确激活证据生成binding；证据冲突或缺失标`RECOVERY_REQUIRED`且禁止新冲突写，不猜最新版本。
3. 增加operation关联及必要nullable约束；旧记录保持原字节/结果，不能把历史发布切换前的消息重入执行。
4. 升级新代码与数据变更按同一跨端合同准备；产品<2.0不留长期双解析/旧写入口。停机和迁移须另有本次授权，不能借用以前的授权。
5. 回退核验新增数据是否已产生；已运行新操作时不能只回滚二进制到不认识新状态的旧程序。优先受控前向修复；确需数据恢复须保留新事实并重新验证兼容性。

## D5. HTTP接口目标合同

现有可复用入口：`GET /agent/skill-products`、商品详情、`POST /agent/skill-orders/quotes`、`POST /agent/skill-orders`、订单与权益查询；现有首次购买会要求readyProof，并对全部同skill历史权益执行`SKILL_ALREADY_ORDERED`。**不能删除检查后拿重复购买冒充升级**。

新管理入口调用相同交易/安装领域服务，不建立第二套钱包。产品界面最终只使用一个Agent管理数据源；既有市场路由可以继续浏览，但选定Agent后的安装交互复用同一组件/命令入口，不并存独立状态机。

### D5.1 路由与副作用

以下为待实现路径，所有资源访问均校验tenant/client/当前Actor与Agent归属，外单委托权限不算管理权限。

| 方法/路径 | 请求 | 响应data/副作用 |
| --- | --- | --- |
| `GET /agent/{agentId}/skills` | 无body；首期沿现有完整catalog列表，无臆测容量上限 | `{agentId,agentVersion,items,observedAt}`；无写副作用 |
| `GET /agent/{agentId}/skills/{skillKey}` | 无body | 行DTO + 指定批准候选差异、权限/费用说明；无副作用 |
| `POST /agent/{agentId}/skill-operation-quotes` | `QuoteRequest`；Idempotency-Key | `Quote`；持久报价，不冻结/扣款/创建安装 |
| `POST /agent/{agentId}/skill-operations` | `CreateOperationRequest`；Idempotency-Key | `Operation`；原子受理与outbox，返回202不表示成功安装 |
| `GET /agent/{agentId}/skill-operations/{operationId}` | 无body | 当前Operation，主体范围复验，无新命令 |
| `GET /agent/{agentId}/skill-operation-requests/{requestId}` | 无body；关联原创建requestId | 原操作或404；requestId不是授权/幂等凭证，不枚举他人请求 |
| `GET /agent/{agentId}/skill-operations` | `skillKey,cursor,pageSize` | `{items,nextCursor,hasMore}`；游标按实际event顺序，pageSize复用已核验约定，SM-T02固定fixture |
| `POST /agent/{agentId}/skill-operations/{operationId}/retries` | `{expectedOperationVersion}`；新的动作Idempotency-Key | 原operation的新attempt；只接受可恢复失败，不新建购买 |
| `POST /agent/{agentId}/skill-operations/{operationId}/reconciliation` | `{expectedOperationVersion}`；Idempotency-Key | 原操作核对状态；可安排现有恢复器查原证据，不新建安装/激活/Provider执行 |

版本详情/差异由商品版本服务支撑；首期无需另做发布维护页。启停用CreateOperation中的`ENABLE/DISABLE`类型，不为每个按钮另造一套协议。

### D5.2 DTO与前置条件

`QuoteRequest`必填：`type`（INSTALL/UPGRADE）、`skillKey`、`targetProductVersionId`、`expectedAgentVersion`、`expectedStateVersion`、`approvedPermissions`（规范化string数组）；UPGRADE还必填`sourceInstallationId`。scope/actor/owner只能来自认证上下文，不信任body。

`Quote`必填：`quoteId,type,skillKey,targetProductVersionId,targetSkillVersion,targetPackageSha256,expectedAgentVersion,expectedStateVersion,approvedPermissionsSha256,price,coverage,expiresAt`。`price={amountMinor,currency}`；`coverage=EXISTING_ENTITLEMENT/NEW_PURCHASE/UPGRADE_CHARGE`；必要时包含`entitlementId`。无权威费用政策不能编造quote。

`CreateOperationRequest`公共必填：`type,skillKey,expectedAgentVersion,expectedStateVersion`。INSTALL/UPGRADE另必填`quoteId,targetProductVersionId,approvedPermissions`，UPGRADE必填`sourceInstallationId`；ENABLE/DISABLE仅另含`sourceInstallationId`，不得带目标包或伪造quote。`additionalProperties=false`，不得用空字段兼容全部动作。

`Operation`必填：`operationId,type,skillKey,status,stage,attempt,operationVersion,originalRequestId,createdAt,updatedAt,recoveryAction`；`sourceInstallationId,targetProductVersionId,installationId,fundingOrderId,reasonCode,observedAt`按类型/阶段可null。目标对象与授权快照不可通过更新接口更改。

JSON成功示例（合成值，省略业务未定义字段不是允许生产DTO随意扩展）：

```json
{
  "protocolVersion": 1,
  "requestId": "req-skill-install-demo",
  "data": {
    "type": "INSTALL",
    "skillKey": "pdf-extract",
    "expectedAgentVersion": "12",
    "expectedStateVersion": "0",
    "quoteId": "sq_demo",
    "targetProductVersionId": "spv_demo",
    "approvedPermissions": ["READ_AUTHORIZED_INPUT", "WRITE_TASK_RESULT"]
  }
}
```

上例请求为`POST .../skill-operations`，必须另带独立`Idempotency-Key`。HTTP202响应：

```json
{
  "protocolVersion": 1,
  "requestId": "req-skill-install-demo",
  "code": "E0",
  "msg": "操作已接纳",
  "data": {
    "operationId": "smo_demo",
    "type": "INSTALL",
    "skillKey": "pdf-extract",
    "status": "WAITING_AGENT",
    "stage": "WAITING_CONNECTION",
    "attempt": 1,
    "operationVersion": "1",
    "originalRequestId": "req-skill-install-demo",
    "sourceInstallationId": null,
    "targetProductVersionId": "spv_demo",
    "installationId": "si_demo",
    "fundingOrderId": "so_demo",
    "reasonCode": "AGENT_OFFLINE",
    "recoveryAction": "QUERY_ORIGINAL",
    "observedAt": null,
    "createdAt": 1792713600000,
    "updatedAt": 1792713600000
  }
}
```

### D5.3 幂等、权限与错误

- 原逻辑创建保存requestId与独立Idempotency-Key；规范化请求hash覆盖动作类型、资源、原/目标、版本和权限，不把展示文案作为业务输入。
- 同键同输入返回同一operation/quote结果；同键不同输入409。UI双击/跨标签不是安全边界，服务器锁/CAS/唯一约束仍生效。
- 刷新后先GET原operation；尚无operationId则按原requestId查询。404不代表“可以换新键再买”：可能原请求尚未完成。没有受理证据时只能在用户明确操作下重放**原键原请求**，仍经过同一幂等路径；报价已失效则返回明确错误，由用户重新确认，不自动续费或重新授权。
- quote变更/过期只使未提交确认失效，不因已受理操作超过quote时刻就取消/退款。
- 普通查询200；受理202；资源不可见404；身份401/403；冲突409；业务字段合法但条件不满足422；依赖不可用503。完整错误信封`{protocolVersion,requestId,code,msg,data:null}`，禁止HTTP200包装业务失败。

| 目标错误码 | HTTP | 前端处理 |
| --- | --- | --- |
| `AGENT_FORBIDDEN` | 403/防枚举时404 | 关闭管理敏感数据，不展示其他Owner事实 |
| `SKILL_VERSION_NOT_PUBLISHED` | 409 | 清理失效候选与quote，重新读目录 |
| `SKILL_STATE_CONFLICT` | 409 | 重新读取精确关系，不自动改目标提交 |
| `SKILL_OPERATION_IN_PROGRESS` | 409 | 展示当前有权访问的原操作恢复入口 |
| `IDEMPOTENCY_CONFLICT` | 409 | 阻止重用错误键，不随机换键掩盖冲突 |
| `SKILL_QUOTE_EXPIRED` / `SKILL_QUOTE_MISMATCH` | 409 | 原行提示重新准备并确认 |
| `SKILL_PERMISSIONS_MISMATCH` | 409 | quote失效，重新展示实际权限 |
| `SKILL_RUNTIME_MAPPING_REQUIRED` | 409 | 先完成真实身份绑定；不可显示已排队成功 |
| `SKILL_RETRY_REQUIRES_NEW_QUOTE` | 409 | 说明原财务已终结，只有显式新授权可安装 |
| `SKILL_RECOVERY_REQUIRED` | 409 | 只核对原操作，不开放重复写 |
| `SKILL_STATE_UNAVAILABLE` | 503 | 原位查询重试，不推断安装终态 |

沿用已有等价错误码时以冻结fixture为准，不创建同义码分叉。失败stage和安全原因写操作记录，响应不泄露下载凭据或主机绝对路径。

## D6. 操作状态机与资金语义

| 状态 | 准入/业务含义 | 允许后续 |
| --- | --- | --- |
| ACCEPTED | 已持久受理，不等于下载或成功 | WAITING_AGENT/PREPARING；启停可到VERIFYING/完成 |
| WAITING_AGENT | 合法身份绑定存在，但无当前连接 | 同操作待连接，不自动新购买；重连重新验证会话fence |
| PREPARING | 独立下载/校验/依赖准备 | PREPARED，或证实未激活后的失败 |
| PREPARED | 候选具备完整准备证据 | API再次CAS/授权后ACTIVATING |
| ACTIVATING | API已关闭本skill不确定的新准入，已持久化切换意图 | VERIFYING；结果不明进入RECOVERY_REQUIRED |
| VERIFYING | 精确激活/策略回执已收到，待当前目录/准入读回 | SUCCEEDED或RECOVERY_REQUIRED；不能凭时间成功 |
| SUCCEEDED | 本动作成功条件已满足 | 本operation不再转回运行态；观察到后续离线另更新runtime维度 |
| FAILED_RETRYABLE | 证实本attempt未激活，且权益/资金允许原操作重试 | 显式重试增加attempt，原目标不变 |
| FAILED_FINAL | 已终结退款、授权失效或不可继续 | 查看历史；新请求须新报价/明确授权 |
| RECOVERY_REQUIRED | 是否已激活/应用不能证明 | 原操作核对，禁止新冲突写/自动退款 |

`UNKNOWN`是UI对“不知道是否受理或无法得到权威状态”的观察，不是成功/确定失败，也不靠时间写成一个永久终态。已有operation出现激活证据冲突时使用`RECOVERY_REQUIRED`；查询HTTP失败不能把服务器状态强行改成它。

**重试的三种不同动作**：

1. 网络重放：同一request/幂等键、同一command/installation/attempt，不新增副作用。
2. 准备阶段已证实失败后的用户重试：同一operation、新attempt/installation/command标识，保留旧失败记录；不重复创建购买或资金预留。
3. 财务/权益已终结后的重新购买：新的quote、显式确认、新operation/订单，关联旧操作仅供历史解释；不能贴“重试”标签隐藏第二次授权。

首次安装成功与资金结算沿现有交易不变量；需核对当前合法entitlement与明确激活成功后才提交对应结算。新增付费升级也使用真实order；原权益覆盖的升级没有第二笔假订单。确定失败如何释放/退款沿现有合同；只要切换可能已发生或外部结果未知，就不能按网络超时自行退款。

## D7. 安装、升级、启停的跨端时序

### D7.1 安装与升级

1. API受理事务固定Owner/Agent/原激活/目标版本/权限/quote/资金关系，唯一pending操作；通过现有outbox发准备命令。
2. Runtime核验当前合法绑定、消息与command fingerprint、原包/epoch，下载批准包到独立暂存；执行包/manifest/依赖检查，不能覆盖运行目录。
3. Runtime持久化`PREPARED`与准确结果后回执；API校验其对应operation/attempt/原目标与当前会话证据。
4. API持有同binding锁复核权限/目标/CAS，将新准入关停并分配单调`activationEpoch`，与激活命令outbox同事务提交。
5. Runtime验证精确准备状态后执行原子切换并持久化激活事实/结果outbox，重新发布当前session目录。
6. API接受匹配attempt/epoch/摘要的激活证据，提交active关系及相关权益/财务；仅在当前目录确认后开放`admissionEnabled`。目录未到则显示“已安装，待核验”，不假装可调用。
7. Web查询operation和binding读回，更新该行、Agent详情与后续任务能力。旧已准入任务继续原包；旧未准入消息的过期目录被明确拒绝/要求新请求，不自动重发。

准备阶段允许旧版新调用；切换阶段只关闭该skill的不确定新准入，不停整个Agent或其他技能。API新准入和切换CAS共用binding版本栅栏，防止“检查旧版后刚好切换”的竞态；切换前已准入任务在提交授权时就登记精确引用。

### D7.2 离线准入

目标行为允许**已合法拥有且持久Runtime映射可信**的Agent离线接纳操作；接纳与投递/激活分开。没有映射、Owner已变更、Runtime身份失效时拒绝，不能仅删`requireReady`绕过身份保护。

现有`quote/purchase`依赖当前readyProof，因此离线支持是实质性API/Runtime合同变更，不是前端开按钮。报价仍检查归属/版本/政策；操作绑定持久Runtime installation/host身份，重连投递需当前session证明。host或installation迁移不自动继承旧投递资格，转入受控核对。

### D7.3 停用与启用

- DISABLE：API事务先置`desiredEnabled=false,admissionEnabled=false`并记录成功的“停止新准入”事实；向Runtime投递策略变化并失效目录。离线时如实显示Runtime尚未同步，但API新任务已不能准入。用户语义是停用新调用，不把它误说成包已卸载或所有执行已停止。
- DISABLE的终态例外：API停止新准入的事务提交即为该动作SUCCEEDED并释放普通pending；Runtime策略同步状态单独保留，不等待离线Runtime才确认停用。策略epoch仍单调推进，后续ENABLE必须验证更新epoch；迟到停用命令/回执不得覆盖更新策略。这里的SUCCEEDED不适用安装/启用必须经VERIFYING的完成条件。
- ENABLE：仅有合法安装/权益才接纳；期望设true但新准入保持false，待精确包/权限/当前目录证明后开启并完成。离线等待不会伪装启用成功。
- 在途已准入授权保留原包/权限；安全撤销不是普通停用/升级，仍沿既有专门撤销合同拒绝后续危险副作用。
- 同skill普通升级、启停互斥；操作未知时不靠新启停覆盖旧状态。紧急安全撤销使用独立既有安全路径，不被普通管理操作屏蔽。

## D8. Runtime存储、消息与恢复

### D8.1 存储与引用

程序仍固定在 `/home/isp/apps/cyf-agent-runtime-v1/app/`，不新增程序版本目录或`current`链接。本设计的技能内容存储位于**现有受管stateRoot之下**，具体路径由安装配置传入，不另硬编码用户HOME。

- 不可变技能包内容按`packageSha256`寻址，包含manifest摘要/校验清单；技能内容不等同Runtime程序版本。
- staging按operation/attempt独立；registry保留精确installation、来源、command fingerprint、active关系与阶段journal。
- 既有`CODEX_HOME/skills/<skillKey>`作为当前受管发现视图，复用已验证的目录交换/防篡改原语；不是随意切换程序`current`链接，也不覆盖运行中的文件。
- executor/resume通过授权快照读取精确摘要包，不再仅靠当前ACTIVE目录查找。在API任务准入与Runtime本地start登记引用；未知外部副作用和未确认结果也保留引用。
- 内容GC只在确认无激活、无已准入/在途/结果恢复引用且历史证据可追溯后执行；不能按“非最新版”或无根据保留天数删除。GC自动化不作为本期新常驻服务。
- 普通说明型包可没有执行manifest；只能影响受管技能说明发现，不凭此进入任务可执行目录。

### D8.2 消息合同

复用现有`command.dispatch`、ACK、结果回执、租约与outbox。目标增加显式命令类型`SKILL_PREPARE / SKILL_ACTIVATE / SKILL_SET_ENABLED / SKILL_RECONCILE`，同一链路同步实际Java producer、Runtime codec与回执consumer，不另开通道。

公共信封沿v1.2，保留`requestId/messageId/correlationId`、真实认证与已有command/attempt/fencingToken/deliveryEpoch语义。业务`data`按命令类型封闭：

| 命令 | 必须绑定的业务信息 |
| --- | --- |
| PREPARE | operationId/type/attempt、agentId/skillKey、source精确installation/version/hash（首次为null）、target productVersion/version/packageSha256/manifestSha256、权限摘要、既有认证下载路径、Runtime持久绑定、expectedStateVersion |
| ACTIVATE | 原PREPARED operation/attempt/installation与准备证据摘要、原/目标摘要、单调activationEpoch、desiredEnabled、当前合法投递fence |
| SET_ENABLED | operation/type、精确activeInstallation/package、策略版本/epoch、desiredEnabled；不能携带任意新包 |
| RECONCILE | 原operation/attempt/command/installation、目标证据标识；只查原journal/marker/回执，无重新执行授权 |

结果必须包含原operation/attempt/installation、命令关联、阶段、真实包/manifest摘要、激活epoch、成功证据或安全failureCode。可执行包缺manifest摘要拒绝；说明包明确null。命令fingerprint与摘要canonical规则在SM-T02冻结同源fixture，不能用日志脱敏后的对象计算业务摘要。

Runtime重连后：当前通道身份需有效；历史操作证据按原command/attempt识别，重新投递采用既有明确delivery epoch规则，不把旧session消息直接当当前权威。迟到旧attempt/旧epoch回执只留审计、不倒退当前绑定；结果恢复不能变成创建另一安装。

### D8.3 崩溃与失败矩阵

| 断点 | 恢复依据 | 禁止行为 |
| --- | --- | --- |
| 下载/校验未完成 | 暂存与原attempt，确认未激活 | 覆盖旧包，伪造ACTIVE |
| PREPARED落盘、回执丢失 | 同command fingerprint+准备journal读回 | 新建购买或用新installation冒充同attempt |
| API已记录切换意图、命令未送达 | 原outbox/epoch恢复投递 | 放开不确定的新准入 |
| 目录交换完成、ACTIVE journal未完成 | 原intent+双方marker/摘要判断提交或未提交 | 仅按目录名猜结果、恢复旧业务状态快照 |
| Runtime已ACTIVE、结果未达API | 持久结果outbox，当前认证核对原证据 | 以超时退款、重复执行切换 |
| API已active、当前目录尚未确认 | exact安装与session目录重新对账 | 显示READY或重做购买 |
| 旧回执/旧session在新epoch后到达 | 原attempt/epoch/绑定校验，忽略状态写入 | 回退新active关系或把旧目录当新目录 |
| 已调用Provider但结果未知的旧任务 | 原执行快照、原包、现有effect恢复协议 | 为验证升级自动再调用Provider |

无法证明文件/journal一致时保留证据并进入RECOVERY_REQUIRED；不能用“自动回滚”一词掩盖未知。安装准备失败后可安全废弃本attempt暂存，但包/身份/授权/历史回执/业务状态的清理边界仍分别核对。

## D9. 前端落点与接线

| 文件/模块（拟新增项已标注） | 责任 |
| --- | --- |
| `web/src/components/juyiting/AgentPanel.vue` | 复用技能标题行入口、Owner可见性、管理返回后的详情刷新 |
| `web/src/components/economy/SkillManagerDialog.vue`（新增） | 同列表/行内展开/焦点/滚动，组件内无第二份安装事实 |
| `web/src/components/economy/SkillManagementRow.vue`（新增） | 名称/版本/状态/主动作；控制展示而不拥有交易真相 |
| `web/src/composables/useSkillManagement.js`（新增） | 聚合查询、scope指纹、草稿/quote失效、操作恢复、状态读回 |
| `web/src/composables/useSkillMarket.js` | 抽复用既有金额、权限规范化、journal/请求守卫；交易行为单一入口，避免复制整个composable |
| `web/src/components/economy/SkillMarketRoute.vue` / `SkillMarket.vue` | 选定Agent后复用同一管理入口与安装组件；历史市场用途不扩成第二管理系统 |
| `web/src/composables/juyiting/useHallAgentProfileCapabilities.js` | 管理完成后的真实能力刷新，身份/代际迟到守卫保留 |
| `web/src/composables/useHttp.js`及现有API封装 | 新路径、标准信封/错误边界，不在UI二次解码旧信封 |

这些是建议的最小模块职责，不要求为形式把所有行内内容拆成大量文件；实现前依据最新分支组件结构核对。桌面与移动复用同一状态源，不维护两套管理页。

## D10. API与Runtime源码落点

| 层 | 复用/增量 |
| --- | --- |
| agent service/api | 新`SkillManagementController`/查询与动作服务；现有`SkillMarketplaceService`交易/权限、`SkillPackagePublicationService`发布、`SkillPackages`包存储复用 |
| economy core/mapper | 现有quote/order/entitlement/installation的必要字段/关系、索引与事务；不重写钱包 |
| agent core/mapper | 新binding/operation/event实体与CAS查询；层次检查继续`validateLayering` |
| install chain | `SkillInstallCommandWriter/DispatchService/AckService/ResultService/RecoveryService`接入阶段/attempt/epoch，不破坏原确切回执与资金一致性 |
| capability/admission | `InstalledSkillDescriptorService`、chat `ChatActionCapabilityService`及实际准入路径读取active/admission状态；不让管理投影成为授权源 |
| Runtime `conf/codex-ws-agent/skill-install-manager.mjs` | 替换只允许首次安装的冲突处理为显式受控准备/激活；无授权仍拒绝冲突 |
| Runtime `skill-registry.mjs`、`skill-executor.mjs` | active投影与精确历史引用分离，执行/恢复固定摘要 |
| Runtime `agent-client.mjs`、现有codec/report-outbox | 同源消息合同，安装/启停变化复用`onSkillInstallChanged`失效重测 |
| Runtime宿主路由/安装入口 | 新内部路径若涉及既有白名单需定向同步；程序固定app布局不变，不授权本次部署 |

外部Runtime仓库为 `/home/isp/wsps/chcbz/isp-install`；指派任务必须显式携带CYF根规则和接口v1.2，不能假定自动继承。管理设计不应再次硬编码image-edit/pdf/text分支决定通用能力。

## D11. 后续功能设计边界

- 卸载：同一操作框架新增UNINSTALL，先停止新准入、确认在途/未知引用，保留权益/输出/回执；无引用后才移出active投影。首期无伪可用卸载按钮。
- 受控回退：新增ROLLBACK作为新的精确目标激活操作，复验包授权、权限/状态兼容性；不恢复旧身份/授权/业务数据库快照，不默认任意降级。
- 发布维护：沿现有管理员发布服务补版本详情、diff和采用视图；下架仅影响新购买/候选，普通退役不抹除旧合法安装，安全撤销按安全执行合同单独处理。
- 三项均需先扩展当前唯一原型、冻结新增合同与验收；本文件只是边界设计，不把首期表字段存在当后续功能已完成。

## D12. 可观测性、验证与待核验事实

日志/事件关联`requestId → operationId → attempt → command/message → installation/activationEpoch → catalogRevision`，记录阶段耗时与真实错误；不输出权限秘密/下载token，不设无依据请求、包大小或等待时间硬门槛。

验证以[实施计划](management-plan.md)A01–A28为准：UX不是只测截图尺寸；合同不是只测自造mock；安装成功不是Provider业务成功；Flow完成不是线上验收。精确候选/同源fixture优先，小反馈→影响回归→获授权版本化发布。

实施前事实核验清单：①API最新remote develop对quote/安装/统一协议的差异；②真实版本发布与升级权益政策；③当前DB唯一约束及历史证据质量；④Runtime包内容缓存与执行引用路径；⑤发布时实际API/Web/Runtime/技能包版本；⑥分页默认/上限沿现有契约取值并固定测试，不凭文档新设门槛。未知范围如实保留，不能以文档的目标字段伪造当前事实。


### 2026-10-26 卸载最小实现增补
用户已将卸载纳入本期，覆盖前文“首期无卸载按钮”。复用既有change/outbox/POLICY/READ与行内详情，不新增接口控制器、数据库表、权限开关或GC服务。Runtime以removed投影退出当前发现，保留精确不可变包；API接纳时关闭新准入，精确APPLIED(actual=null)+当前目录核验后清active指针。保留历史权益，重新安装引用新的installation身份，同版本有效权益报价为0；保留原零金额订单审计，不重复扣费。冻结业务字段及恢复边界见management-contract.md末节，发布状态以handoff证据为准。
