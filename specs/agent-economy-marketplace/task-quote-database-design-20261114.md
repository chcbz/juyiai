# 事项报价修复：Runtime上报模型与数据库价目详设

- 日期：2026-11-14（Asia/Shanghai）；版本：1.3（技术细节冻结；2026-11-14补充实际交付状态）。
- 状态：**API已实现、测试、迁移并受控安装；生产健康及只读报价冒烟通过**。精确源码、隔离资金/调价验收与生产验证边界见§13；本文不授予后续生产改价或收费测试权限。
- Owner：`quote_database_owner`；任务：`TASK-QUOTE-DATABASE-20261114`。开发前调查基线与实际交付候选分别记录，不把旧基线冒充安装身份。
- 主合同：[文钱包与成本账](beta-wen-billing.md)；本详设只替代其中逐Agent静态计费路由及启动时价目读取的同范围规则，不改变固定报价资金合同。
- 公共约束：[根AGENTS](../../AGENTS.md)、[接口规范v1.4](../../api/docs/interface-standard.md)、[RB-1](../juyiting-skill-execution/responsibility-boundaries.md)、[全局回归手册](../juyiting-unified-experience/global-regression.md)。

## 1. 用户最终决定与范围

### 1.1 已确认决定

1. 信任经现有身份认证的Runtime上报模型；复用已有`executionModel`字段、注册、存储及实例归属，不追加模型可信认证。
2. 本次**不修改Runtime源码、协议、配置或部署**；不下发模型、不增加应用确认、远程探测、任务级模型锁定或渠道上报。
3. 报价不再要求每个Agent、每种任务类型登记独立路由；必须覆盖全部现有有效用户绑定，不能缩小验收范围。平台现有可供后续绑定的模型全部预置价目，新绑定正常注册后无需逐Agent配置即可查价。
4. 模型／工具单价及模型的事项报价选择在数据库维护；更新后新读取生效，不依赖重建或重启服务。
5. 已有报价、资金预占、结算与成本快照保持不变；后续模型上报或价目变化不使原报价失效，不补扣或重算。
6. 复用已有能力；只补持久化与必要读取衔接，不建设通用配置中心、管理后台、价格平台或模型网关。
7. 开源通用性：Git/JAR只维护通用默认值、结构迁移、说明和合成示例；生产价格、渠道标识、租户、主机、地址和凭据不进入公开仓库或通用JAR。
8. 2026-11-14用户明确：从GitHub查最新模型API单价，在开发前确定，不将价格调研推迟到开发或部署末尾。公开API价作为事项报价基准，不冒充实际采购账单；沿原已确认一次性人民币换算口径，无运行时汇率。

### 1.2 本次目标

- 消除“新Agent可被推荐，但必须人工补逐Agent路由才可报价”的结构性问题。
- 同模型共享平台明确选定的事项报价价目；多渠道／档位不猜选。
- 全部有效用户绑定及平台当前支持模型的未来绑定均纳入覆盖；平台引入新模型时先维护模型级价目，不因新用户绑定新增Agent级路由。
- 模型、工具价格数据库化，并保持实际成本消费者的精确渠道和历史版本语义。
- 推荐HTTP契约及用户资金流程不变；Web原则上无需发布。

### 1.3 非目标

- 活动、租费、自部署套餐、主机登记、语音或全量外置配置迁移；这些属于相邻整改，不捆绑本次修复。
- Provider连接地址／密钥热切换、模型下发、自动选模、降级、模型网关、收费试调用。
- 实际执行模型与上报值的额外验证；不把目标模型或展示名称替换成执行事实。
- 新价格算法、按角色倍率、任务复杂度系数、报价TTL、续费策略、钱包重构。
- 字典扩建、自动抓价、汇率、预约调价、Redis缓存／广播、通用配置审核或审批框架。
- 默认选中候选等UI体验调整、推荐排序改变、扩大模型输入和增加推荐调用。

## 2. 源码基线与问题归因

### 2.1 开发前只读调查基线（历史输入）

| 仓库 | 本地HEAD | tree |
| --- | --- | --- |
| API | `80618640d6dd48f23ae668b59ea88778d9e57bdf` | `8d6d5104eefe4e41f0523d3b19e0298e85accb19` |
| Web | `6ce64429e5c75477d5f10d358759da9caa8692f8` | `f9833306a53fe89ee338b8cced00f512a2e56356` |
| Runtime | `978d44268d8d79b0361831e23a9dff1f51020a11` | `b9a8e485471b6cfd3d024702d44de66d6d1a09dd` |

根文档工作区存在其他任务修改，不能以根HEAD代表所有已读文档字节；本次不覆盖其他任务内容。未fetch或查询远端最新。后续实现开工须重新固定实际候选，不把本表当未来测试或线上身份。

### 2.2 修复前调用链（问题归因）

- `AssigneeRecommendationService`：原候选授权、单次模型推荐和整事项Token估计。
- `AssigneeRecommendationQuotes.prepare`：在原事项根事务内按`agentId + workload.kind`调用`AssigneeQuoteRoutes.find`。
- `AssigneeQuoteRoutes`：从`jia.agent.task-pricing.routes`在启动时建立Map；未命中返回`BILLING_ROUTE_MISSING`。
- `ConfiguredTaskPricingService`：从`economy.pricing.models/tools`在启动时建立Map。
- `TaskBillingServiceImpl.quote`：先查已存绑定报价，再查价、计算并保存快照。
- Web的`hallAssigneeRecommendation.js`将`BILLING_ROUTE_MISSING`映射成“计费配置尚未就绪”。

根因是**已存在的模型上报没有成为报价查价输入，逐Agent路由及价目又是独立启动配置**。不是余额不足，也不能从该错误反推模型本身不可用。

### 2.3 已有能力，不重建

| 能力 | 复用位置 | 约束 |
| --- | --- | --- |
| 模型上报 | Runtime `buildAgentRegistrationPayload` | 优先profile.codexModel，其次现有引擎配置readback；不是chatModel覆盖值 |
| 认证注册与持久化 | `AgentWebSocketHandler`、`AgentServiceImpl.register`、`AgentRuntimeDao.updateRegistration` | 原身份/会话fence保留；presence不覆盖模型 |
| 模型读取 | `agent_runtime.execution_model`、`AgentRuntimeDao.findByAgentIds` | 对授权候选批量读；保留现有环境分区，不增加逐层tenant校验 |
| 价格模型与计算 | `ModelTokenPrice`、`TaskQuoteCalculator`、`CnyAmounts` | 原BigDecimal精度、Token类别、长上下文与最终取整 |
| 价格边界 | `TaskPricingService`、`ModelPriceCatalog` | 扩展既有契约，不另造平行服务 |
| 固定报价／资金 | `TaskBillingServiceImpl`及原mapper/posting | 先重放后查价，原任务锁、预占、扣款、释放不变 |
| 成本历史 | `UsageCostService`及`economy_usage_revision.price_snapshot_json` | 原调用身份、revision、摘要及快照不变 |
| 好汉目标与租费 | `agent_persona_model`、`economy_hosting_model_plan`、`economy_hosting_rent_plan` | 保留但不用于推断上报模型或Token单价 |

### 2.4 本次配置盘点的边界

11月14日只读盘点指定API部署配置：存在20条旧承办路由，其20个工具列表均为空；未发现`economy.pricing.tools[*]`独立工具价格项。本次仅将数量和空列表结论写入公开文档，不复制任何生产价格、渠道、Agent或凭据值。

这不是所有部署环境的保证。迁移入口必须盘点目标环境真实输入；若发现非空工具估算，按第7节处理，不能静默丢弃。

## 3. 责任边界和目标链路

```text
原候选授权／单次推荐与Token估计
  → agent：批量读取候选已保存的executionModel
  → economy：按模型选择事项报价渠道／档位
  → economy：读取该计价键当前版本及必要工具价
  → 原计算器 → 原报价快照
  → 原确认预占／验收扣款／取消释放
```

| 层 | 本次负责 | 不负责 |
| --- | --- | --- |
| agent | 授权候选、读取上报模型、传递已有事项和用量事实 | 不选价格、不查Provider、不维护逐Agent价目 |
| economy | 模型报价选择、价目、计算、报价与成本快照 | 不读Agent表、不认证Runtime、不切换模型 |
| chat | 原推荐调用与成本证据；给价目查询传原可信scope | 不复制价目、不改推荐连接或模型配置 |
| Runtime | 原上报与执行 | 无本次改动 |
| Web | 原报价显示及显式确认 | 不计算金额、不重排推荐、不承担资金判断 |

模块仍按core/api/mapper/service分层：领域结构和计算留core，查询契约留api，SQL留mapper，配置选择与事务留service。agent和chat通过economy-api消费，不把费用逻辑塞入base/common。

## 4. 权威事实和价格语义

### 4.1 模型事实

- 使用当前授权候选的已存`executionModel`；精确字符串匹配，不大小写折叠、不按品牌／相似名称映射。
- null／空值表示未上报；不取`configuredModel`、108人目标表、旧静态路由或推荐模型补齐。
- Runtime模型变更在原注册刷新写入后，对后续报价可见；不承诺任意本地文件修改能立即自动上报。
- 新报价使用本次短事务读到的上报值。并发更新允许本次读旧值、下次读新值；不加跨进程锁或远程确认。
- 已授权跨Owner候选的模型可供服务端计价，不因此向推荐LLM或浏览器暴露新增私有字段；不新增owner-only过滤误伤原有外部承办。

### 4.2 平台报价与真实成本分离

- 模型名并不唯一确定采购渠道。因此每个scope、每个模型显式选择一个事项报价渠道与档位。
- 该选择只说明平台如何给用户报固定价，不证明Runtime真实采购渠道，不切换其实际模型。
- 即使某模型只有一条价目，也必须有明确事项报价选择；不得用查询顺序、最低价、最新时间或默认渠道猜选。
- 实际成本使用原回执／调用适配器提供的精确channel/model/tier；不得回退到事项报价选择。
- 推荐模型的调用成本与承办候选的事项报价不同；此次只替换共用价目来源，不改变推荐模型或加收推荐服务费。

### 4.3 价格与历史

- 原公式不变：整事项预估人民币费用＝模型估计的输入/输出Token分别乘登记单价＋已有明确收费工具估算；最终一次`ceil(人民币元×100)`得到整数文。
- 不新增最低价、附加费、缓存优惠假设；显式零价与缺价不同，沿原价格结构和计算器语义。
- 当前价目变化、报价选择变化、模型上报变化，只影响新报价。`Binding`不增加模型revision，不增加报价过期校验。
- 原报价查询／重放必须先于新模型可用性和新价目解析；即使当前选择已删除或模型未上报，原有效报价及资金重放仍按原事实处理。
- 实际成本缺usage／价格时仍为PENDING；不填0、不用报价反推用量、不自动重发Provider调用。

## 5. 数据设计

### 5.1 最小持久化集合

新增表均归economy-mapper，表名为本设计的实施目标，不表示已经存在。使用现有MySQL、InnoDB、二进制标识比较及可信`EconomyScope`约定，不新增通用配置表。

| 表 | 主键／唯一性 | 用途 |
| --- | --- | --- |
| `economy_model_price` | tenant_id, client_id, channel, model, tier, price_version | 不可变模型价格版本 |
| `economy_model_price_current` | tenant_id, client_id, channel, model, tier | 当前价格版本指针 |
| `economy_task_model_tariff` | tenant_id, client_id, model | 该模型唯一事项报价选择及已有工具估算配置 |
| `economy_tool_price` | tenant_id, client_id, channel, tool, unit, price_version | 不可变工具价格版本 |
| `economy_tool_price_current` | tenant_id, client_id, channel, tool, unit | 当前工具价格版本指针 |

这五个窄表分别解决历史版本、当前选择和模型报价选择，不是五套服务。工具两表承接现有工具价格能力，空环境保持空，不自动启用收费工具。没有当前指针表示该计价键不供新查价，不再新增ACTIVE/DISABLED状态机或预约生效任务。

### 5.2 列合同

公共标识为精确非空字符串，schema沿既有scope列采用`tenant_id/client_id VARCHAR(50)`；channel/tier/version/tool/unit采用`VARCHAR(100)`；model采用`VARCHAR(200)`与现有executionModel接收上限一致。二进制collation；迁移发现超出实际列容量时显式报告，不截断、改名或哈希替换原身份。这是存储约束，不是模型名单限制。

**`economy_model_price`**

- 主键列如上；`price_data_json LONGTEXT NOT NULL`；`created_at BIGINT NOT NULL`（Unix毫秒）。
- price_data_json只保存价格内容：`basis`、`yuanPerMillionTokens`、`shortContextMaxInputTokens`、`longContextYuanPerMillionTokens`。
- basis非空；rates对象键沿`ModelTokenPrice.Category`，值为非负BigDecimal的十进制字符串；缺类别不补零。JSON数字不得先经过double。
- threshold可null；longContext可空对象；约束沿原ModelTokenPrice构造及计算规则，不重复写SQL CHECK。
- 读取用表键及内容构造原ModelTokenPrice；不会改现有报价快照中的序列化结构。

**`economy_model_price_current`**

- 主键列如上；`price_version VARCHAR(100) NOT NULL`；`updated_at BIGINT NOT NULL`。
- 同scope复合外键指向模型版本表完整主键，无级联删除。

**`economy_task_model_tariff`**

- 主键列如上；`channel VARCHAR(100) NOT NULL`、`tier VARCHAR(100) NOT NULL`、`tools_json LONGTEXT NOT NULL`、`updated_at BIGINT NOT NULL`。
- tools_json为原工具估算项列表：`[{channel,tool,unit,unitsPerDeliverable}]`，最后一项为非负十进制字符串；明确无工具为`[]`，不允许null。
- 同一tool key不得重复，沿原Route.Tool的含义。这里只迁现有确定的估算配置，不新增模型自动推断工具收费能力。
- 无指向current表的强制外键：有报价选择但尚未登记价格是明确的候选缺价状态，不用数据库约束把运营维护变成必须一次发布全部能力。
- 工具价格缺失同样在原报价责任层报候选不可报价，不自动登记免费价。

**`economy_tool_price`**

- 主键列如上；`price_data_json LONGTEXT NOT NULL`保存`basis`和`yuanPerUnit`（非负十进制字符串）；`created_at BIGINT NOT NULL`。
- 读取组装原`TaskQuoteCalculator.ToolPrice(version,basis,yuanPerUnit)`。

**`economy_tool_price_current`**

- 主键列如上；`price_version VARCHAR(100) NOT NULL`；`updated_at BIGINT NOT NULL`。
- 同scope复合外键指向工具版本表；无级联删除。

JSON用于存原有变长Token分类和工具列表，不把整个通用应用配置序列化到数据库。版本行只插入，不更新或删除；指针和报价选择可更新。已有资金/报价/成本表不改结构，不新增审计事件总线、触发器或全量配置台账。

### 5.3 scope和访问

- 本设计选择按tenant/client隔离价目及报价选择，不把owner放入价目键：同scope的Agent共享价目。
- 现有ModelPriceCatalog没有scope参数；新持久化边界显式接收调用方已持有的EconomyScope，禁止以进程client默认值代替真实调用client。
- 原HTTP／Runtime入口负责认证准入；费用存储查询绑定原scope，不再次认证，也不向所有DAO机械加tenant参数。
- 普通用户／Runtime不能指定价格、价目版本、报价渠道或写数据库；首版不开放价格管理HTTP接口。

### 5.4 维护及并发更新

复用现有受控SQL维护方式；运维脚本属于现有维护入口扩展，不新增常驻runner。

1. 新价：同事务插入新版本，再插入／更新对应current指针，提交后新事务读取生效。
2. 更新已有指针时带操作者刚读到的旧版本条件；影响行数不符合预期则整笔回滚，避免覆盖另一人调价。此条件只用于实际并发写入口。
3. 切换事项报价渠道／档位：更新该模型唯一tariff行；不改实际成本身份，不改已存报价。
4. 停止新报价：删除tariff选择；停止某计价键的新价格读取：删除current指针。版本和历史快照保留。
5. 撤销一次错误调价：切回原版本指针；不回滚已经发生的用户资金与业务事实。
6. 指针／内容在同一事务查询或JOIN获取，不在查询间读取半套配置。已开始事务可见旧一致版本；“立即生效”指提交后新事务，不强制改变在途请求。

不增加时间生效调度、任意价差上限、模型白名单、缓存失效系统。价格数值来源仍须由获授权维护者明确登记；不从公开模型名称推导官方报价。

## 6. 服务契约与逐文件改动

### 6.1 agent报价入口

`AssigneeRecommendationQuotes`移除AssigneeQuoteRoutes依赖，复用AgentRuntimeDao批量读取本次已授权候选的executionModel。本次固定使用该批量DAO，不扩展公共推荐DTO、不新增网络请求。

- 非空候选集最多新增一次批量模型读取，不每个候选查Runtime详情。
- 原候选授权与事项根事务、需求／资料快照不变。
- 传给费用域的是原Task、Binding、payer、原工作量及可空reportedModel。
- 用量原`TaskWorkload`的kind/inputTokens/outputTokens/deliverables；agent不再填渠道／模型价，工具估算由费用域的模型报价选择承接。
- 未上报模型的结果也进入费用域原先重放分支；新报价才产生候选不可报价错误。
- `AssigneeQuoteRoutes`及其ConfigurationProperties退出生产；对应测试改测新查询，不保留文件fallback。

### 6.2 费用API的目标签名

以下为本次内部Java契约目标，不是新HTTP端点：

```java
// TaskBillingService：替换旧ModelKey输入；其余资金方法和Binding不变。
Quote quote(Task task, Binding binding, String payerUserId,
            TaskWorkload workload, String reportedModel);

// TaskPricingService：由费用域解析本模型的事项报价选择。
PreparedQuote prepare(EconomyScope scope, TaskWorkload workload,
                      String reportedModel);

// ModelPriceCatalog：实际成本用精确计价键；原价格对象不变。
Optional<ModelTokenPrice> find(EconomyScope scope,
                              String channel, String model, String tier);
Optional<ModelTokenPrice> findVersion(EconomyScope scope,
                                     String channel, String model,
                                     String tier, String version);
```

- `reportedModel`是可空内部输入；null／空值的新报价返回`Unavailable(BILLING_ROUTE_MISSING)`，不是强行构造默认ModelKey。
- `scope`来自已有业务上下文，不从浏览器新增字段取得。
- `find`无current返回Optional.empty；`findVersion`不存在返回empty；数据库错误和损坏价格数据不能转成empty。
- 不保留没有scope的生产查询重载，以免一个入口悄悄查错环境；改真实调用方和fixture即可，不扩大全项目接口。
- TaskPricingService.Unavailable.Reason增补`BILLING_ROUTE_MISSING`作为现有wire原因的内部表达；其他原因和HTTP契约不变。
- PreparedQuote保留原模型／工具快照和有效TaskWorkload；工具数量由tariff原估算项乘deliverables后形成。agent无需知道此计算细节。

`TaskBillingServiceImpl.quote`顺序必须保持：

```text
检查原绑定报价／付款身份
  有历史 → 直接返回，不查当前tariff和价格
  无历史 → prepare(scope,workload,reportedModel)
           → 原TaskQuoteCalculator
           → 原QuoteSnapshot落库
```

旧报价的Binding摘要算法、付款身份、snapshotJson、预占/结算和LEGACY_FREE读取完全不变。

### 6.3 价格实现与存储

- 替换ConfiguredTaskPricingService为明确的数据库实现（`DatabaseTaskPricingService`）；保留TaskPricingService和ModelPriceCatalog为同一责任实现，不再维护启动Map。
- economy-mapper增加上述五表的窄查询／维护SQL。通用连接、事务和异常处理复用原基础能力。
- economy配置装配移除EconomyPricingProperties作为生产价源的注册。本次已检索到旧Properties的生产消费者为该实现与配置注册，二者替换后删除该类型；测试fixture直接构造原价格对象，不保留影子生产实现。
- 首版无跨请求缓存。查一个模型仅读对应tariff/current/version；工具只读明确需要且非零数量的价格，不扫描全价目。
- 同一报价内通过原事务获得一致读取；实际成本的单次精确查询JOIN current/version取得一份快照。
- 不为尚无实测瓶颈增加批量报价API、预加载框架或请求线程缓存；候选模型批读与数据库精确索引已足够形成最小实现。

### 6.4 真实消费者的联动清单

| 消费者 | 必须变化 | 保持不变 |
| --- | --- | --- |
| `TaskBillingServiceImpl` | 新prepare输入，仍先重放 | 快照、资金事务、Binding、计算公式 |
| `RecommendationCostRecorder` | `find(binding.scope(), channel, requestedModel, tier)` | 调用前选价、响应沿原快照；推荐模型/连接不改 |
| `NativeProviderUsageCostRecorder` | 原started快照优先；首次无started且有明确priceVersion时改用findVersion | 原执行归属、摘要冲突、原usage normalizer |
| `PlatformKnowledgeUsageRecorder` | starting按原binding.scope查当前价；responded复用原started快照 | 平台成本归属与私有交接授权 |
| `NativeExecutionUsageCostRecorder` | 无需改价目读取：本来没有调用目录 | 总计数证据仍PENDING |
| `ChatUsageCostRecorder` | 同上，无需改 | 原CHAT归属和未知成本语义 |

旧版回执缺精确版本不猜填：沿现有缺价/PENDING规则。已有started记录的price为null时仍沿原null，不用新价悄悄追补。查历史版本只解决“有原渠道/模型/档位/版本证据，却因当前指针变化查不到”的缺口，不自动信任未知时间或重算历史。

### 6.5 Web与Runtime

- 推荐请求、结果、金额、quoteId、recommendationId等wire字段不变。
- 缺上报模型／缺报价选择沿`BILLING_ROUTE_MISSING`；缺模型价沿`MODEL_PRICE_MISSING`；既有前端文案可直接展示。
- 无需增加executionModel、渠道、价格版本到浏览器或推荐LLM输入。
- 本次不修改前端默认选中逻辑、不新增轮询／自动推荐重试；缺价候选仍保留原能力评价。
- Runtime零代码／协议改动，注册与配置刷新能力照旧；不重新部署Runtime来修API查价。

## 7. 工具、工作量及版本兼容

1. 五类kind继续保留在工作量和报价快照中，不再作为模型价目选择键；无按kind换模能力。
2. 当前受查部署20个工具列表均为空，迁移后各模型tariff写`tools_json=[]`，不是推断工具免费。
3. 既有非空工具估算如在某目标环境出现：相同模型各旧路由的工具清单完全一致时，可原样迁入该模型tariff；数量、unit和单价语义不变。
4. 若同模型不同Agent／kind旧工具配置冲突，迁移报告精确差异并停止该模型转换；不任选、合并或丢弃。当前已盘点环境没有此冲突，因此不为假设场景新建kind策略引擎。后续若实际遇到，由原费用合同明确唯一选择后继续。
5. 当前及历史Token类别、缓存写入、图像Token、长上下文规则完整保留；不得迁移时仅保留INPUT/OUTPUT。
6. 普通技能运行成本元数据、模型建议和技能名不自动变成独立收费工具。现有技能授权／执行及预算边界不变。
7. 不变更原报价Snapshot schema。新数据库price_data_json是目录存储格式，不要求历史snapshot重写或统一格式。

## 8. 错误与必要校验

| 风险／条件 | 责任层 | 失败范围及结果 | 回归 |
| --- | --- | --- | --- |
| 非授权候选或错误身份 | 原agent准入 | 原401/404/既有业务错误；不读跨权限候选 | 原候选ACL与跨Owner用例 |
| 模型未上报／无tariff | 费用prepare（历史重放之后） | 单候选UNAVAILABLE/BILLING_ROUTE_MISSING | 新Agent／缺模型／删选择 |
| 无当前模型价格 | 费用prepare | 单候选MODEL_PRICE_MISSING | 多渠道精确选价 |
| 使用了缺单价Token类别 | 原价格准备／计算 | 单候选TOKEN_PRICE_MISSING | 原类别回归 |
| 非零工具数量缺价 | 原价格准备 | 单候选TOOL_PRICE_MISSING | 工具价格回归 |
| 金额无法表示 | 原计算器 | 单候选QUOTE_AMOUNT_OVERFLOW | 原溢出测试 |
| SQL失败、缺表、损坏JSON／负价 | 存储／配置责任层 | 沿现有异常边界报服务失败并回滚本次事务；不能伪装缺配置 | 数据库错误与回滚 |
| 并发维护覆盖 | 同一次配置写事务 | 条件更新冲突回滚该次维护；无通用审批 | 两连接更新 |
| 改价期间重放旧报价／成本 | 原费用服务 | 读原快照／原版本，不新增扣款 | 价格变更与ACK重投 |

协议输入、资金合法性、schema唯一键/版本引用各在原责任层实现一次。无新增模型在线探测、价格新鲜度TTL、最低余额预检、每层tenant重验或任意金额门槛。显式零单价按原计算器允许；历史金额不得因维护者修改current而重写。

## 9. 配置归属与开源交付

| 项目 | 本次处理 |
| --- | --- |
| `economy.pricing.models/tools` | 显式迁入数据库，移除生产配置消费与旧覆盖项 |
| `jia.agent.task-pricing.routes` | 删除逐Agent价源；不迁为另一张逐Agent路由表 |
| `jia.chat.recommendation.usage-channel/usage-tier` | 原推荐真实成本来源，仍由部署侧明确提供；不是逐Agent报价路由，不强行合并进平台报价选择 |
| 通用框架／算法参数 | 保留通用Git/JAR默认；不夹带生产值 |
| 数据源／部署scope／主机／地址／私有路径 | 原部署侧配置，不为消灭外置文件写入公共JAR |
| 密钥、ENC密文、TLS私钥、解密密码 | 原安全注入，均不纳入公开Git/JAR |
| 活动、租费、控制主机、语音配置 | 本次不迁移；后续按各自责任整改 |
| `CORE_DICT` | 本次不使用、不增加价格字典 |

结构迁移SQL可入Git；合成fixture以`example-model`、`example-channel`、`example-client`和明确合成价格标识，不使用真实渠道/账号值。生产初始化数据在受限部署目录生成，日志只列键名、数量、摘要及脱敏差异。示例不由启动自动seed。

价格操作说明沿既有费用文档维护，首次可使用受控事务SQL，不建设管理后台或公开价格写API；将来需要管理功能再由economy同一责任层提供，不改变本期交付范围。

## 10. 迁移、安装与恢复

### 10.1 输入盘点

- 固定获授权的目标环境、scope、实际部署JAR与配置摘要；区分当前有效配置、备份和源码示例。
- 读取价目、旧路由的键及既有已上报模型。无需读取用户任务正文、附件、密钥或调用Provider。
- 对每个模型输出：是否有价格、有哪些channel/tier、旧路由是否一致、工具是否为空、哪些模型缺价。
- 多渠道选择由维护者明确给出；禁止从“第一条”推导。不能因急于修复而用相似模型、旧路由模型或目标模型代替上报模型。
- 盘点中发现旧路由模型与上报值不同，保留差异：新报价按上报值；为该模型补价须有真实授权依据，不能迁移出虚假免费或借用价格。

### 10.2 执行次序

1. 在隔离MySQL验证显式DDL、迁移输入及应用候选；没有启动自动DDL／初始化器。
2. 保存目标旧配置、必要schema／新增配置数据备份及原部署回执；不为本次改价备份后再覆盖用户钱包。
3. 显式建立五表。MySQL DDL独立执行并留结果，不把它误称可与数据插入一起事务回滚。
4. 在一个DML事务中导入不可变价格、current指针和模型tariff；重复输入同版本同内容可报告已存在，不同内容冲突则停止，不UPSERT覆写历史。
5. 按新程序解析规则只读核对全部行和原输入摘要；全部有效绑定及平台当前8模型必须齐备。缺价是未完成，不允许缩小本批覆盖或伪造成功。
6. 使用原LOCAL安装器安装固定API制品，安装及自动恢复期间暂保留旧外置键。新程序已删除其消费、仅读数据库，不存在文件覆盖或fallback。原安装器没有外置配置联合切换能力，不为本次扩建。
7. 健康及业务验收通过后，在既有锁保护下原子清除精确旧键，其他字节保持不变，无需再次重启；清理后回退须先恢复旧配置再恢复旧JAR。完整固定顺序见§12.6G。
8. 分别记录安装、健康与报价／资金业务验收。对外发布只包含通用结构和代码，不含私有seed。

迁移和切换期间避免并行维护两份价目：原配置作为切换前固定输入，新数据库在切换前不对外承诺生效。不在请求中双写、读双源或恢复旧路由。

### 10.3 恢复边界

- 发布前数据导入失败：回滚本次DML，保留独立DDL结果，不影响旧报价和资金。
- 新程序价目配置错误：优先修复／切回数据库指针；保留原错误维护记录，不重算已发报价。
- 应用回退只在实际授权和已核对兼容性下进行，不自动回退。旧程序只认静态配置，不能宣称切回旧JAR自然兼容所有新Agent和动态价目。
- 若必须恢复旧程序，先评估切换以来新增模型、价目和报价；保存新事实，明确配置转换与新请求影响。不得恢复旧数据库快照覆盖新报价、预占、钱包、ACK或业务状态。
- 正常定价失败只影响候选；配置迁移不能成为停所有Agent或Runtime的理由。

## 11. 测试与验收

本节为冻结验收定义；本批实际执行及范围见§13，不将历史测试数量当当前通过。入口从全局回归手册的ASSIGN/ECON及真实影响项选取；若声明CORE17或CHANGE_IMPACT，则遵守其完整范围，不能把本表的定向测试冒充全局通过。

### 11.1 数据库和费用责任层

| ID | 场景 | 必须观察到的结果 |
| --- | --- | --- |
| QDB-01 | 新schema、合成价目、current与tariff | 实际MySQL可读且还原原价格对象 |
| QDB-02 | 更新价目并提交，API进程不重启 | 新事务新报价用新版本；PID保持不变 |
| QDB-03 | 同模型两个渠道／档位 | 事项报价严格按tariff；成本严格按精确计价键 |
| QDB-04 | 同模型不同tenant/client | 只读各自价目；缺配置不借其他scope |
| QDB-05 | 新版本发布与并发读取／维护 | 只能读完整旧版或新版；条件更新冲突不覆写 |
| QDB-06 | 输入／输出／缓存／图像／长上下文 | 迁移前后原计算结果一致，缺类别不补零 |
| QDB-07 | 非空工具、零数量、缺工具价 | 原数量及费用语义保持，缺价仅对应候选 |
| QDB-08 | 旧报价重放时删tariff／价目指针／模型缺失 | 原quoteId及金额不变；不查当前选择 |
| QDB-09 | 无started的迟到精确版本回执 | 能按原版本查价，不换当前价；不存在则PENDING |
| QDB-10 | started.price=null及ACK重投 | 保留原null／快照和幂等，不自动追补或重发调用 |
| QDB-11 | 缺表、SQL异常、损坏JSON、非法价格 | 报服务／配置错误，事务回滚，不伪装BILLING_ROUTE_MISSING |
| QDB-12 | 显式零价、舍入、溢出 | 沿原CnyAmounts及计算器，零不等于缺价 |

### 11.2 agent与公共契约

| ID | 场景 | 必须观察到的结果 |
| --- | --- | --- |
| QAG-01 | 新Agent上报已有价目模型，无旧路由 | 推荐返回AVAILABLE，未新增任何逐Agent价目行 |
| QAG-02 | 原五种任务类型 | 同一模型无需五条路由，Token计算按原用量 |
| QAG-03 | null模型、缺tariff、缺模型价格，混合候选 | 对应旧unavailableReason正确，其他候选仍可报价 |
| QAG-04 | 多候选、不同owner | 只处理原授权候选；模型批量读，无新增远程请求 |
| QAG-05 | Runtime再次注册更新模型 | 新报价使用已保存新值；旧报价仍可按原合同确认 |
| QAG-06 | 静态路由与DB冲突 | DB是唯一来源；无DB数据不读旧文件兜底 |
| QAG-07 | 原HTTP请求／响应fixture | wire、金额格式、quoteId与原Web消费者兼容 |
| QAG-08 | 模型服务失败／无候选／资料变更 | 原错误和快照规则保留，没有新增模型调用 |

### 11.3 资金、成本与真实UI

- 复用`TaskBillingServiceMySqlTest`及原真实HTTP资金用例：确认预占、验收扣款、取消释放、余额不足、付款身份、并发及幂等。
- 复用`RecommendationCostRecorderTest`、`NativeProviderUsageCostRecorderTest`、公共知识成本相关用例：新数据源不改变原调用／账务归属。
- 扩展`AssigneeRecommendationQuotesTest`、`AssigneeRecommendationServiceTest`及Controller测试；旧路由配置测试改为上述模型/数据库读取测试。
- Web复用现有`juyiting-assignee-recommendation.test.js`及相关组件测试，证明无需改wire；不要求全前端重建来验证API内部改动。
- 在获授权环境，以一个无旧静态路由的新实例验证报价，再验证调价前后新旧报价和必要资金闭环；真实收费调用须另有实际预算与授权，不用测试账户耗尽钱包。
- Runtime只核对既有上报与API保存事实，不部署、不运行无关完整Runtime回归。接口未改不能宣称所有Runtime业务都重新验收。

### 11.4 构建与性能

按根AGENTS使用`local_build.py --package`并经原Gradle串行入口，先读build.gradle并plan-only；保留必要基线、上述业务定向、validateLayering及fresh JAR。正常缓存目标300秒、单次硬上限600秒及例外按根规则执行；独立集成／UI验收另记。无新runner、无付费Flow、无本地内存盘、无重复构建伪证据。

性能验收记录模型批量读取数、价目查询数、推荐模型调用数和实际耗时；不设无依据性能门禁，不因成本库访问给生产请求下传强制deadline。

## 12. 实施顺序及完成定义

1. **数据层**：五表DDL、模型／工具存储、current与历史版本查询、合成迁移fixture。
2. **费用层**：原接口内替换价源；tariff解析；原快照及成本消费者联动。
3. **agent层**：批量读取上报模型；删除逐Agent路由；保持先重放后解析当前配置。
4. **验证与迁移准备**：定向MySQL／HTTP／成本与前端消费者回归，私有环境差异清单。
5. **获授权发布与验收**：固定候选、显式DDL/DML、受控API安装，健康与业务分别验证。
6. **收尾**：原文档回写实际源码／测试／安装状态；旧配置消费删除；按原制品保留策略登记最终包，保留证据。

完成必须同时满足：新Agent不需要静态路由；价格在线更新；历史报价与成本版本不变；原资金回归通过；Runtime零改动；Git/JAR无私有配置；实际上线范围有真实证据。只写文档、只建表、只单测通过或只健康UP均不能标为报价问题完整修复。

### 12.1 一次开发的固定落点（v1.1补充）

以下是同一个API候选必须一起完成的改动，不拆成多次生产试投：

| 位置 | 确定交付 |
| --- | --- |
| economy-mapper `resources/db/migration-task-pricing-20261114.sql` | 五表显式DDL，空库和已有库迁移测试；不加入启动自动建表 |
| economy-mapper `EconomyPriceCatalogMapper` | 单一窄mapper，当前模型价JOIN、精确历史版本、tariff及所需当前工具价查询；每个关联含完整scope和计价键 |
| economy-service `DatabaseTaskPricingService` | 同时实现既有两接口，负责价格JSON编解码、tariff选择和有效工作量；不增加平行目录服务或缓存 |
| economy-api `TaskPricingService`、`ModelPriceCatalog`、`TaskBillingService` | 按§6.2替换签名；删除无生产用途的旧ModelKey输入，不留静态来源兼容重载 |
| economy-service `TaskBillingServiceImpl`、`EconomyConfiguration` | 接入数据库实现与原快照；删除旧Properties注册及旧价源实现 |
| agent `AssigneeRecommendationQuotes` | 构造器注入既有AgentRuntimeDao替代routes，授权候选ID去重后批读；删除AssigneeQuoteRoutes |
| 三个实际成本消费者 | RecommendationCostRecorder、NativeProviderUsageCostRecorder、PlatformKnowledgeUsageRecorder同候选改完scope和历史版本查询 |
| 对应测试及运维探针 | 同步构造器、mock、fixture和断言；不能保留依赖已删除类的独立Java探针 |

mapper遵循现有MyBatis注解SQL风格；价目存储行使用economy内部数据结构，不向agent/chat泄露持久化类型。公开仓库只交付DDL及合成数据；生产DML、连接信息和价目清单置于受限部署侧。

**工作量唯一来源固定如下：**

1. agent构造`TaskWorkload(kind,inputTokens,outputTokens,deliverables,Map.of())`，不再从旧路由填工具。
2. 费用prepare从tariff取得工具列表，逐项以BigDecimal计算`unitsPerDeliverable × deliverables`，生成有效toolUnits；不与调用方toolUnits叠加、不读技能元数据补数。
3. effectiveWorkload保留原kind和三个数量字段，以tariff计算结果替换toolUnits；`estimate`必须由effectiveWorkload生成，PreparedQuote同时携带二者。
4. TaskBillingServiceImpl以prepared.workload构造WorkloadSnapshot，以prepared.estimate生成工具快照；不要一边用新工具计算、一边保存旧工具。现有snapshot结构不变。
5. 零数量沿原计算语义保留且无需工具价；非零数量缺价仍为原候选错误。复用原类别检查和金额计算，不复制算法。

**重放与异常的边界：**原billing.quote先读旧绑定，再进入prepare。当前推荐调用每次新建recommendationId，因此批读模型属于生成新推荐，不是历史报价查询；不能据此承诺模型DAO故障时新推荐也可成功。DAO真实失败回滚，不转换为模型未上报；reserve/capture/release不得新增模型或价目查询。单候选Unavailable继续保留原noRollbackFor，其他数据库异常不得吞掉后提交部分候选。

**价格一致性已固定：**本轮只读核实部署MySQL 8.0.21为REPEATABLE-READ，原事项事务未覆盖隔离级别。固定在原事务内普通一致性读，current/version单条JOIN；不增加单条大SQL备选、全局隔离改动或新事务。证据及方法见§12.6A—B，测试验证确定合同而非重新选方案。

### 12.2 测试及维护消费者不能遗漏

除§11列出的业务用例，还必须一起适配：

- `EconomyPricingPropertiesTest`改为数据库实现测试；`AssigneeQuoteRoutesTest`的工具、重复项和缺配置覆盖迁入对应责任层测试，不只是删除测试。
- `TaskBillingServiceMySqlTest`、`EconomyWalletHttpMySqlTest`使用合成数据库价目，不实例化已删除ConfiguredTaskPricingService。
- `AssigneeRecommendationQuotesTest`替换旧routes构造器和ModelKey断言；现有推荐服务／Controller fixture维持wire合同。
- `RecommendationCostRecorderTest`、`NativeProviderUsageCostRecorderTest`、`PlatformKnowledgeUsageRecorderTest`、`PlatformKnowledgeUsageHttpMySqlTest`同步有scope的查询；有精确历史版本的STARTED和无STARTED的TERMINAL都覆盖findVersion，不能只改迟到终态。
- `ops/release/tests/AssigneeQuoteCoverageProbe.java`当前直接加载旧properties和旧实现，属于真实受影响消费者。本次改为受限连接下的只读数据库覆盖核对，复用新目录读取与计算，禁止写入报价／钱包或触发Provider。生产私有输入不放命令行或日志；原离线配置探针不再作为新候选验收入口。
- 测试注册固定为§12.6E的三个有限taskQuoteRegression切片，复用原测试和fixture（包括原managedHostingRegression覆盖的公共知识HTTP用例），不整跑无关托管测试；选择器通过原`--regression-arg`加入。
- 测试报告必须逐项映射§11；MySQL用例复用EconomyMySqlTestFixture隔离库，缺fixture或被skip不算通过。构建计划要显示实际任务和选择器；仅默认快速基线通过不足以发布本次候选。

### 12.3 开发前已固定的数据输入与安装前漂移复核

**代码能消除逐Agent路由依赖，但不能创造尚未登记的模型价格。** 2026-11-14用户将范围明确为全部有效用户绑定，本轮进一步只读盘点了部署数据源：固定环境tenant下status=1的绑定按tenant/client/agentId/bindingId精确关联Runtime，合计7条、4种上报模型，未发现缺失上报；只输出聚合数，不读取用户任务或正文。平台当前8种模型的GitHub价格已逐项核对，见§12.5。此时点盘点不替代安装前对新增绑定的差异复核。

部署侧覆盖清单现已固定，下列字段是执行时按摘要复核的输入，不是开发时再选择的方案：

- 目标scope内全部有效用户绑定的实际已上报模型集合；不能只取当前在线或已出现于推荐结果的子集。108人模型配置仅用于补齐未来可绑定模型目录，不能取代执行事实。
- 每个目标模型的明确报价channel/tier、价格版本和真实定价依据；多渠道由维护者明确选择。
- 推荐调用及另外两个实际成本消费者使用的精确计价键也须覆盖，不能只盘点承办模型。
- 旧配置所有价格类别／长上下文／工具项迁移前后的内容比对，以及旧路由与上报模型差异。
- 已有成本快照不重写；尚未入库、可能迟到的历史版本只有取得原权威价格内容才可补入，不能用当前价冒充。未找到仍PENDING并如实列明，不宣称全历史覆盖。

本批开发前须完成全部已绑定模型及平台当前支持模型的价格基线，缺价／渠道选择未明不能留到部署才确定；不得缩小恢复范围，也不得用默认价、免费价、相似模型价消除告警。安装前新出现的模型或绑定差异须补齐后再验收；原有离线、授权或用量估计失败仍按原业务合同处理，不能将“计价就绪”误称任意请求必成功。

### 12.4 一套候选、一次统一切换、分项验收

交付单位固定为：**API完整候选 + 五表DDL + 私有DML及覆盖结果 + 精确旧配置键删除清单 + 原恢复说明 + 本批测试证据**。不发布Web或Runtime，不先上线只改推荐入口的半套实现。

统一切换前已完成必要测试和隔离迁移演练；获得实际发布授权后，按§10先建表和导入核对，再受控安装API；统一验收通过后清理旧配置键，不假定安装器支持联合配置切换，详见§12.6G。统一核验：

1. 实际安装版本／摘要、进程及健康；旧路由和静态价格消费已退出。
2. 对全部有效绑定按已上报模型核对计价，并用合法合成工作量覆盖；平台当前全部8模型完成未来新绑定报价回归。真实推荐另外按原在线／授权条件验证，不把离线绑定从价格覆盖清单中删除；无逐Agent价目记录。
3. 同一API进程中提交一次获授权调价，新报价使用新价，旧quoteId及金额不变；复原时仅切回指针，不删除已产生事实。
4. 原确认预占、验收扣款、取消释放及重投幂等按获授权测试账户闭环；费用不得超出实际测试授权。
5. 推荐成本／原生Provider成本／公共知识成本的价目与快照路径验证完成，缺证据保持原PENDING。
6. Runtime无本次变更／部署、Web契约未改、开源包无私有seed或凭据。

“一次性完成”表示同一范围一次改齐、验证后统一安装，不是保证测试不会发现缺陷或强行只允许一次构建。失败须归因修复并重新固定候选；不能把开发验证推迟到生产，更不能为凑一次发布省略必要测试。

### 12.5 开发前价格来源与未来绑定闭环（2026-11-14）

**本次来源已查询，不再是“开发时再查”。** 通过GitHub REST API获取各文件当次检索的最新提交，再按固定commit/blob读取内容，保存原始字节与SHA-256：

- `llmrates/llm-pricing-dataset`，文件`data/models.json`；commit `05a4f717cea700c6f150101e73ca5cff9a15f50d`（提交时间2026-11-13T19:55:23Z）。
- `BerriAI/litellm`，文件`model_prices_and_context_window.json`；commit `ccb7f753c9a73ddaea862b19871ce3a8ea354016`（提交时间2026-11-14T05:33:54Z）。
- 只对原厂OpenAI记录、standard档和精确模型名核对，不混入Azure区域价、聚合渠道、Batch/Flex/Priority/Ultrafast。8模型的输入、输出、缓存读在基础与长上下文两档共48个值一致。
- GitHub数据中的官方来源指向OpenAI API pricing；本轮直接访问官网HTTP403，因此证据措辞是“GitHub两目录固定版本一致”，不是“已独立官网核验”。两个目录一致也不证明采购账单金额。

本批部署侧明确采用`public-api-reference/standard`作为事项报价身份，8模型均有一条tariff，工具列表为空；此键表示公开API参考价，不是Runtime连接渠道。美元原值及对应人民币值在受限部署侧价格基线保存，**不把生产seed或当前价目硬编码进Git/JAR**。人民币沿原已确认6.6879一次性换算，不是本轮实时汇率，不新增换汇功能；价格内容保留BigDecimal精度，只在原最终文金额处取整。

基线含标准基础三类Token价及272000输入Token阈值对应的长上下文三类价，不将整事项累计Token假定为一次Provider调用；原estimateCost与实际cost的区别保留。缓存写入原始字段已留证，未额外猜测其TTL类别映射；原真实渠道已确认的缓存写入价随旧目录内容迁移，不能删去或被参考价覆盖。图片模型原成本价亦已查到对应GitHub参考记录，本期不把图片工具模型当承办默认模型。

**事项报价与实际成本分开迁移：** 新8模型参考价供tariff选择；原实际成本精确channel/model/tier/version行按原已确认内容保留。旧版本、已有成本快照不重写。参考价记录只说明定价依据，不允许拿它填未知Runtime采购渠道；不让本次价格研究引出Runtime协议改造。

**以后用户绑定的保障方式：**

1. 当前平台108好汉采用的8模型一次备齐价格；尚未被绑定的模型也不能漏。
2. 同scope新用户、新Agent、新绑定复用该模型价目，正常注册保存executionModel后即可报价，无逐Agent维护步骤、无重启。
3. 平台将来新增模型时，在其开放使用前通过同一数据库维护价目与tariff；这是模型目录维护，不增加新的绑定审批、运行时GitHub抓取或用户手工计费配置。
4. 自部署Agent若上报目录外模型，不能凭一个任意字符串保证有正确价格。该情况纳入新增模型补价责任，不偷偷映射其他模型、不假定免费，也不宣称当前8模型基线覆盖未来所有未知型号。若产品要允许任意未登记模型绑定后立即报价，需要另行明确这种型号的定价来源；本次不擅自增加默认收费或网络抓价能力。
5. QAG补充：全部有效绑定模型覆盖、8模型新绑定覆盖、新用户同模型复用、原绑定模型变更，以及安装前新增绑定差异复核。覆盖结果不得用删除缺价绑定或缩小候选集合取得。

开发前价目研究与只读盘点已完成；价格基线及原始源文件保存在受限部署侧。本段记录开发输入，实际生产写入回执及安装结果见§13；后续调价仍由数据库新版本承接，不修改已发报价。

### 12.6 技术细节冻结：事务、存储、迁移、测试与安装（2026-11-14）

本节将此前“开发时核实／择一”的技术点收敛成确定实现。后续测试用于验证实现符合本节，不承担重新选择业务方案的职责。未来批次号、候选commit、PID、测试端口等执行时产生的身份值不在设计阶段伪造。

#### A. 已核实的环境事实与事务选择

- API源码基线仍为§2.1的80618640；部署JAR自报版本1.1.52-SNAPSHOT、commit `9c8c38c3ade03747e833f107ae9d8696104c196a`、tree `caa70871aaf7ab524f35e65e118efaa2f95ea386`，不能混称本地HEAD已上线。
- 以部署数据源只读连接查得MySQL **8.0.21**、session/global均**REPEATABLE-READ**、InnoDB页大小16384。部署properties及当前进程相关环境／参数未发现价目、隔离级别或连接初始化覆盖。该结果不是对任意其他部署环境的保证。
- 原`AgentTaskMutationTransactionImpl`使用REQUIRED TransactionTemplate、不覆盖隔离级别；`TaskBillingServiceImpl.quote`为MANDATORY且对Unavailable不回滚。**固定复用该事务及一致性读，不增加新事务模板、不修改全局隔离级别、不加目录行锁，不再保留“换成单条大SQL”的备选方案。**
- 价目SELECT均为普通非锁定读；该报价事务里的tariff、current、version及工具读共享同一快照。数据库价目维护提交后，后续新报价事务可见；在途事务继续旧快照是合同允许行为。报价目录是同事务数据源，不启用读副本或动态数据源切换。
- 成本目录查询无需包住Provider调用：current与version单条JOIN取得一份价格后，沿原STARTED快照记录；后续响应不查新价。两个边界不合并成长事务。
- 只读核对五个新表当前均不存在。绑定、模型目录、已有成本attempt的scope并集为**1个tenant/client组合**；7个有效绑定都已上报模型。数据库现有108人模型定义实际覆盖8模型，与前轮文档清单一致。scope原值只在私有迁移输入保留。

#### B. 持久化实现及SQL固定

新增`EconomyPriceCatalogMapper`，复用现有`@MapperScan("cn.jia.*.mapper")`，不加第二套扫描／DataSource。service使用mapper，agent/chat仅用economy-api。内部行结构固定为三个无行为数据对象：`EconomyModelPriceRow`、`EconomyToolPriceRow`、`EconomyTaskModelTariffRow`（economy-core，沿既有Lombok数据对象和下划线映射）；不向HTTP暴露。

Mapper仅承担以下读方法，不新增价格写HTTP接口或通用Repository：

| 方法 | 输入／SQL结果 | 无结果 |
| --- | --- | --- |
| findTaskTariff | scope+model → channel/tier/tools_json | prepare产生BILLING_ROUTE_MISSING |
| findCurrentModel | scope+channel+model+tier → 当前完整版本行 | prepare产生MODEL_PRICE_MISSING；成本find返回empty |
| findModelVersion | 上项+version → 指定不可变版本行，不连接current | findVersion返回empty |
| findCurrentTool | scope+channel+tool+unit → 当前完整工具版本行 | 非零工具用量产生TOOL_PRICE_MISSING |

当前模型价的实际关联条件固定为：

```sql
SELECT p.*
FROM economy_model_price_current c
JOIN economy_model_price p
  ON p.tenant_id=c.tenant_id AND p.client_id=c.client_id
 AND p.channel=c.channel AND p.model=c.model AND p.tier=c.tier
 AND p.price_version=c.price_version
WHERE c.tenant_id=#{tenantId} AND c.client_id=#{clientId}
  AND c.channel=#{channel} AND c.model=#{model} AND c.tier=#{tier};
```

历史价直接查price表全部六列键；tariff查scope+model；工具JOIN按scope/channel/tool/unit/version等值关联。所有参数用MyBatis绑定，禁止字符串拼接。新表精确collation保证不借用大小写不同键，无需在各服务复制BINARY过滤；原Agent表仍用既有DAO分区。

新报价目录查询量固定为每候选**2+K次**（tariff、模型、K个非零工具键）；Agent模型最多一次批读。当前K=0。不增加批量报价API、跨候选缓存或全表加载。历史报价重放不进入这些查询。

DDL固定如下；完整迁移文件由本段直接实施，不能换为实体启动建表。所有标识列沿§5长度，时间为Unix毫秒，五表不继承通用业务实体附加owner/status列。

```sql
CREATE TABLE IF NOT EXISTS economy_model_price (
 tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL,
 channel VARCHAR(100) NOT NULL, model VARCHAR(200) NOT NULL,
 tier VARCHAR(100) NOT NULL, price_version VARCHAR(100) NOT NULL,
 price_data_json LONGTEXT NOT NULL, created_at BIGINT NOT NULL,
 PRIMARY KEY(tenant_id,client_id,channel,model,tier,price_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS economy_model_price_current (
 tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL,
 channel VARCHAR(100) NOT NULL, model VARCHAR(200) NOT NULL,
 tier VARCHAR(100) NOT NULL, price_version VARCHAR(100) NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY(tenant_id,client_id,channel,model,tier),
 CONSTRAINT fk_model_price_current_version
 FOREIGN KEY(tenant_id,client_id,channel,model,tier,price_version)
 REFERENCES economy_model_price(tenant_id,client_id,channel,model,tier,price_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS economy_task_model_tariff (
 tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL,
 model VARCHAR(200) NOT NULL, channel VARCHAR(100) NOT NULL,
 tier VARCHAR(100) NOT NULL, tools_json LONGTEXT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY(tenant_id,client_id,model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS economy_tool_price (
 tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL,
 channel VARCHAR(100) NOT NULL, tool VARCHAR(100) NOT NULL,
 unit VARCHAR(100) NOT NULL, price_version VARCHAR(100) NOT NULL,
 price_data_json LONGTEXT NOT NULL, created_at BIGINT NOT NULL,
 PRIMARY KEY(tenant_id,client_id,channel,tool,unit,price_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS economy_tool_price_current (
 tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL,
 channel VARCHAR(100) NOT NULL, tool VARCHAR(100) NOT NULL,
 unit VARCHAR(100) NOT NULL, price_version VARCHAR(100) NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY(tenant_id,client_id,channel,tool,unit),
 CONSTRAINT fk_tool_price_current_version
 FOREIGN KEY(tenant_id,client_id,channel,tool,unit,price_version)
 REFERENCES economy_tool_price(tenant_id,client_id,channel,tool,unit,price_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
```

`IF NOT EXISTS`只方便已执行DDL的重试，不证明已有结构正确；维护时核对这五张表的列／主键／外键／collation，不检查无关表、不新增全库schema门禁。已有EconomySchemaInitializer仅负责原资金七表，**不修改其TABLES、不把新五表塞入原七表验证器**。测试显式执行本DDL。

#### C. 编解码、输入及异常固定

- `DatabaseTaskPricingService`使用现有`tools.jackson.databind.ObjectMapper`；目录JSON读写为该实现的私有转换方法，不新建公共序列化框架。模型身份从SQL键取，JSON不重复存身份。
- rates和工具单价使用十进制字符串→BigDecimal；写入也为字符串，不经double、不提前按6位小数舍入。basis非空，threshold为null或正整数Long；分类键沿现有Category。未知结构扩展字段不影响读取；未知收费类别、非法值或损坏JSON不能猜测、补零或吞掉，沿配置异常回滚。
- tariff.tools必须为列表；每项精确tool key唯一，unitsPerDeliverable非负。转换时调用原领域对象构造器，工具数量乘法仅在prepare一次完成，不复制成本算法。
- `find/findVersion`缺失身份字段或空白字段返回empty，保持现有缺成本依据语义；**不trim、不改大小写、不以其他渠道或版本替代**。合法身份命中但内容损坏报配置异常。reportedModel缺失只在新报价prepare映射BILLING_ROUTE_MISSING。
- billing旧绑定重放可接收null workload和null model；不能在重放前加Objects.requireNonNull(workload)。无旧报价才构造effectiveWorkload。
- NativeProvider recorder固定分支：同receipt重放→原STARTED快照（包括null）→无STARTED且精确channel/model/tier/version齐全时findVersion→否则null。STARTED与TERMINAL都按该分支，不把首次STARTED误改为查当前版本。
- 报价Unavailable保持单候选且不污染事务；配置／SQL异常由原服务失败边界处理并回滚整次报价事务。公开wire错误码及Web文案不变。

#### D. 私有迁移输入及行数已确定

现有外置配置中本次删除键**141个且无重名**：模型价20键、空工具配置1键、逐Agent路由120键。旧价目2个、工具价0个、20条路由工具列表全为空；原价字段无properties转义或续行。删除清单按实际键固定，不只写模糊前缀后全文件重排。

开发前已准备输入manifest及首次导入DML；本批已于2026-11-14执行并逐字段读回一致（见§13）。冻结的唯一scope导入结果：

| 表 | 首次导入行数 | 内容 |
| --- | ---: | --- |
| economy_model_price | 10 | 原真实渠道2版本逐字段保留 + 新公开API参考8版本 |
| economy_model_price_current | 10 | 各键明确指向上述版本 |
| economy_task_model_tariff | 8 | 全部模型明确选公开API参考standard，tools为空 |
| economy_tool_price | 0 | 不创造工具价 |
| economy_tool_price_current | 0 | 同上 |

原2版本的渠道、模型、档位、version、basis及全部缓存／图像类别保留，原未设长上下文的仍为null和空表；不能把公开价的新长上下文规则套回旧采购价。8新版本依据固定GitHub提交及原换算基准，完整内容／金额验收向量已在私有输入确定。没有使用托管套餐价格。

迁移操作固定：核对私有输入摘要和scope→显式五表DDL→一个DML事务插入版本、指针、tariff→按原对象解析及行内容读回→受控API发布。首次导入SQL要求目标目录空；SQL错误立即退出并回滚连接，不用`--force`。重试已成功导入的批次只读比对：同键同内容且current/tariff一致为已完成，不重插；发现差异停止并保留真实差异，不UPSERT覆盖不可变版本。这不增加新迁移服务。

后续调价固定为：INSERT新版本→`UPDATE current SET price_version=:new,updated_at=:now WHERE 完整键 AND price_version=:old`→影响行数为1才提交，否则回滚。tariff变更在同一维护事务锁定该模型tariff行后更新；版本行不UPDATE/DELETE。不加触发器、报价TTL或预约任务。

#### E. 测试注册与fixture固定

不通过`--tests`假装避免全历史test源码编译。本批固定在economy-service、agent-service、chat-service各增加一个范围有限的Gradle **taskQuoteRegression** Test/sourceSet，沿既有隔离切片模式，复用原testImplementation/testRuntimeOnly和原fixture，不创建runner或新的测试框架。三个切片不依赖sourceSets.test.output；继承现有应用依赖版本对齐，`maxParallelForks=1`，各Task按现有资源设置执行。

| 模块切片 | 精确编译／执行集合（类名） |
| --- | --- |
| economy-service | DatabaseTaskPricingServiceTest（替换EconomyPricingPropertiesTest的有效断言）、DatabaseTaskPricingMySqlTest（新DB矩阵）、TaskBillingServiceMySqlTest、EconomyWalletHttpMySqlTest、UsageCostServiceMySqlTest；辅助EconomyMySqlTestFixture、TaskPricingTestFixture（新合成数据帮助类） |
| agent-service | AssigneeRecommendationQuotesTest、AssigneeRecommendationServiceTest、AssigneeRecommendationControllerTest、NativeProviderUsageCostRecorderTest、PlatformKnowledgeUsageRecorderTest、PlatformKnowledgeUsageHttpMySqlTest、PlatformKnowledgeUsageControllerTest、AgentTaskBillingMySqlTransactionTest；辅助AgentRuntimePersistentSessionFenceTest、PlatformKnowledgeMaintenanceFixture、跨源码目录EconomyMySqlTestFixture和TaskPricingTestFixture |
| chat-service | RecommendationCostRecorderTest、RecommendationUsageJournalTest、RecommendationUsageRecoveryTest；沿原mock／合成回执，不发Provider请求 |

AgentTaskBillingMySqlTransactionTest本次查明也直接构造旧价源，必须一起改为新mapper及合成数据。两个旧配置测试退出时，工具、缺价和重复项有效断言迁入新责任层测试，不直接丢覆盖。其余原测试不整批迁移目录，切片只用include引用原文件。

构建传入的业务任务固定为：

```text
:economy:jia-economy-core:test --tests cn.jia.economy.pricing.* --tests cn.jia.economy.usage.TokenUsageCostTest
:economy:jia-economy-service:taskQuoteRegression
:agent:jia-agent-service:taskQuoteRegression
:chat:jia-chat-service:taskQuoteRegression
```

上述逐项经原`local_build.py --regression-arg`进入，不替换默认认证／权限／制品基线、validateLayering和fresh bootJar。producer已支持显式追加Test任务的fresh XML采集，无需改producer或另建证据系统。

fixture固定为任务自有的**独立MySQL 8.0.21进程／普通磁盘datadir／loopback空闲端口**，不使用生产3306数据库做测试。沿已有任务自有MySQL启停方式、EconomyMySqlTestFixture环境契约，Owner只管理自己的PID和目录；端口、数据库前缀及密码是本批执行身份，不预填历史值。不得照跑旧`verify_eco_v0_w02_mysql.sh`（它含旧任务、旧源码及3306）；不创建全局宽权限测试账号。MySQL fixture必须在受限构建批次前准备好，构建自身仍按原单批计时，不能把应用单测挪出计时。

公共知识HTTP用例必须设置`CYF_KNOWLEDGE_NODE`和`CYF_KNOWLEDGE_NODE_FIXTURE`，后者固定为Runtime仓库现有`conf/cyf-agent-runtime-v1/test/knowledge-java-fixture.mjs`（不是仅导出mock的knowledge-usage-fixture.mjs）。本轮Node为v24.22.1，driver SHA-256为`a29f9c9e421a8e88c3021bb2c1389cca2a41dc30a0ecce50fdf86a57874ad74a`；fixture及相对导入文件绑定Runtime固定tree，复制到本批普通磁盘测试输入，不修改或部署Runtime。

AgentTaskBillingMySqlTransactionTest的两个`browser*`方法明确从构建切片执行过滤中排除，属于独立真实浏览器集成验收，不伪报跳过为通过；其余需要的MySQL／Node用例未执行或skip都不能通过本批业务验收。浏览器阶段另用原方法及既有Web消费测试验证；不增加Web生产包。

新增数据库测试固定覆盖：DDL/FK/二进制键、字符串BigDecimal精度、实际两连接改价且同事务读旧／新事务读新、单候选Unavailable事务继续、损坏JSON整次回滚、旧报价零目录读取、历史版本无current仍可读、非零工具数量、旧模型更新后新旧报价分离。无依据的新增防御矩阵不扩展。

#### F. 维护探针及验收固定

原AssigneeQuoteCoverageProbe硬编码少数Agent及旧properties，改为**只读当前数据库覆盖探针**：读取固定scope全部status=1绑定，LEFT JOIN精确绑定的Runtime，缺Runtime/模型也计入失败总数；不能按在线状态或价格JOIN成功过滤。再读取该scope现有模型目录，补测未来可绑定8模型。凭据只从受限文件／既有安全注入取得，不放命令行、日志或Git。

探针不启动完整应用、不调用billing.quote、不生成quoteId或资金流水；在只读REPEATABLE-READ事务中通过新mapper+DatabaseTaskPricingService+原计算器，以五种kind和固定合成工作量校验。期望金额取私有冻结价目验收向量，不能拿刚算出的实际结果当期望。输出只列覆盖数、缺失类型、输入／结果摘要；敏感归属留受限证据。原命名入口复用，不新增常驻巡检或自动抓价。

隔离环境的真实报价／资金HTTP测试另覆盖持久化和幂等；生产界面验收按既有测试账户与实际授权执行，不为验证价格新建收费模型调用。数据覆盖、真实推荐可用性及资金流程分别出证，不把7条只读计价成功称作7个Agent均已完成真实承办。

#### G. 安装器能力与恢复顺序固定

本轮核对现有`cyf-api-flow-deploy --source-local`与原`cyf-api-flow-install`：LOCAL入口接受固定制品，复用JAR备份、安装、健康和自动恢复；**不提供外置application-prod.properties联合切换，也不自动执行本次五表DDL**。本期不扩建安装器，不新增配置发布框架，不伪造已有能力。

因此确定顺序为：

1. 必要测试、固定私有数据、隔离迁移演练均完成后，取得实际发布授权；保存原配置完整受限备份及摘要。
2. 显式完成五表和DML导入／读回，旧API继续原配置运行，不改旧价格，不并行维护两份价目。
3. 使用现有LOCAL入口安装唯一API制品；**安装期间保留原外置141键**。新JAR已删除其消费，忽略这些键，只读数据库，因此不是双源或fallback。自动恢复旧JAR时原配置仍在，可正常恢复原行为。
4. 安装、健康及报价／资金业务验收通过后，在原协调锁→API发布锁顺序下核对前值摘要，备份、原子清除精确141键并readback，其余配置逐字节保留。不重启API；旧键已无生产消费者。配置清理单独留回执，不冒称与JAR同一文件系统事务。
5. 清理之后若另获授权回退旧JAR，**先在同样锁保护下恢复原配置备份，再走原JAR安装／恢复入口**。新JAR忽略恢复的旧键，此中间状态安全；禁止先启动旧JAR再补配置。仍需明确旧版不支持新Agent的退化影响，不声称回退后继续满足新功能验收。
6. 所有恢复只涉及本次应用／配置和价目current指针，不回滚整个数据库；已发报价、资金、ACK和成本事实保留。

不另构建Web或Runtime；不调用要求Web/API一起构建的组合发布入口来做API单组件交付。未来执行前对源码、输入、绑定增量和锁状态的复核是防止目标漂移，不是尚未确定的设计分支。

## 13. 公开文档校验与当前交付状态

- 本文件为所选业务详设，由现有主spec、design及文钱包合同链接，不开第二个独立专题。
- 开源导出缺少`docs/sdd-document-map.json`；不伪造分类台账，不将定向链接检查称为全库文档检查通过。
- 本节为2026-11-14实际交付增量，前文开发前基线/冻结设计保留原身份；不将相邻托管、活动或全部配置治理标作本次完成。

### 13.1 固定候选与交付

- API `43feb23d914c2316dd6d7aa460e4a8599f4d67e4` / tree `aef93a448e1d7b307e27d20974b8ee1aece156c9`，版本1.1.53-SNAPSHOT，已合入并推送develop、受控安装。JAR SHA-256：`b5fad5996f2b024059b0854e80a2d35038b7899841194553e178ab0406d6c756`。
- 五表DDL及私有DML显式执行，逐字段读回为10模型版本、10模型current、8tariff、0工具；保留原真实渠道2版本。生产未改写历史报价或资金表。
- 原141个静态路由/价格键按冻结清单移除，其他配置字节及权限保留；新JAR安装后再清理，清理未重启API。数据库是唯一价源，无旧文件回退。
- Runtime源码、协议、配置及部署均无本次改动；Web契约及源码无本次修改/发布。浏览器验收消费固定已安装Web1.16.145（`9d6e1ddf71cfa96ec441c94da50e1e4ec376f9e1`），不把其他任务发布归于本次。

### 13.2 实际验证及证据边界

| 层/要求 | 本批证据与实际结果 |
| --- | --- |
| 固定候选构建与安全基线 | 原本地入口批次`cyf-quote-db-20261114-05`，318项测试0失败/错误/跳过、validateLayering、fresh bootJar及制品安全检查；367.134秒，含54.863秒锁等待，未达300秒目标但低于600秒；未隐藏前4批失败 |
| QDB-01/03/04/05/07/11 | DatabaseTaskPricingMySqlTest及DatabaseTaskPricingServiceTest：实际MySQL键/FK、scope、精确渠道/档位、RR双连接、工具数量、损坏数据；补充组合验证覆盖陈旧条件更新不覆盖新版 |
| QDB-02/08与§12.4.3 | 同一JVM/服务实例加载精确已安装JAR，在隔离MySQL连续10文→调价40文→指针恢复10文；原quoteId/金额/完整快照始终不变，3报价事实/2价格版本保留，钱包100文及零资金流水不变；未修改生产价格，非生产HTTP验收 |
| QDB-06/12 | 原价格计算器及TaskBillingServiceMySqlTest：类别、长上下文、BigDecimal、最终舍入、溢出、工具快照和显式零价；旧2价目与私有冻结输入逐字段相同 |
| QDB-09/10、成本消费者 | NativeProviderUsageCostRecorderTest、RecommendationCostRecorderTest、PlatformKnowledgeUsageRecorderTest及原journal/HTTP回归：精确历史版本、保留STARTED null、重投幂等、未知仍PENDING |
| QAG-01—08 | AssigneeRecommendationQuotes/Service/Controller回归：新绑定无逐Agent配置、更新已报模型、一次候选模型批读、授权/陈旧建议、wire与原错误；五kind及未来8模型另由覆盖探针验证 |
| 资金与真实UI | 原隔离MySQL资金/事务/HTTP用例验证预占、验收、取消、并发、身份及幂等；独立两浏览器用例验证实际页面承办预占和余额不足，真实JWT/Tomcat/MySQL，资料/目录为明确fixture，无Provider执行 |
| Web消费侧 | 原4个相关测试集共33项通过，无Web重建；最终浏览器输入613文件安装摘要前后一致 |
| 生产安装与冒烟 | 原安装器LOCAL安装成功、制品摘要匹配、服务健康UP；全部7有效绑定和8支持模型×5kind共75组只读计价与独立期望向量一致，无缺价/路由失败；清理配置后再次通过 |

模型批读一次由推荐责任层测试确认；无新增推荐模型调用。模型价current单条JOIN、tariff及工具查询归原费用层，没有缓存/远程探测。实际构建耗时与独立浏览器100.554秒分开记录，不把合成报价延迟当真实Provider响应性能。

完整JUnit XML、浏览器截图/SQL断言、安装及迁移读回、价目来源、配置备份与补充调价验证保留于受限部署证据，沿原任务handoff索引；开源仓库只公布源码身份、合成测试和范围，不公开价格seed、scope、用户归属或凭据。安装成功不等于所有Agent已实际完成付费任务；本批没有生产试扣费、付费模型调用或全量Runtime回归。

### 13.3 后续维护及恢复

- 新绑定已登记模型无需额外配置；全新模型上线前登记模型版本/current与tariff，不保证未知未来模型自动获价。新scope同样需要自己的价目，不能跨环境兜底。
- 后续改价沿§12.6D事务式INSERT版本＋完整键/原version条件更新；不重建/重启、不覆盖旧版本。指针回退只影响后续新报价，已有quote和成本事实保持。
- 应用回退须在原锁下先恢复旧外置配置备份，再调用原JAR安装/恢复入口；旧版缺新Agent路由的退化影响必须明确。不得恢复整库资金快照。
- 成功包按现有completed-tasks登记，当前/回退来源保护继续生效；失败及浏览器可丢弃编译输出在保存XML/日志后清理，本任务隔离数据库服务停用，不清他人工作区/缓存。
