> **现行适用范围（2026-11-07）：** 本文是[所属专题](spec.md)的细则，不独立定义发布/角色/DFX规则；共用[统一开发约束](../architecture-convergence/development-principles.md)。旧日期候选/测试/安装仅代表当时范围，未核实部分不改成今日完成。业务协议/冻结输入不因文档整理改写。

# 技能与经济职责分离 v2

日期：2026-11-04。当前状态：源码职责分离、18张生命周期表更名、两端部署及定向生产验收完成；当前结论见§9–10，§1–8保留首版历史基线。

## 1. 范围与基线

用户要求现在划清技能职责，后续统一考虑economy与其他功能融合。本版只定义技能生命周期、岗位授权、技能购买与资金的责任边界；不设计通用商品中心、统一订单平台、事件总线或分布式事务。遵循RB-1及根AGENTS分层职责。

核对源码：API origin/develop `234d98febc3cc66ceade7f4709cee43d3172c9c1`，tree `9694b93442f7885b46011708c0348a3e595e0493`；线上已验证候选仍为本任务上一批 `fe0c693939c3a29694ca43dc59fb6346337c3110`（Flow481），不能将远端源码当作线上版本。主API工作区存在其他任务脏改，本版不改动其源码。

生产表只读盘点：`/home/isp/state/cyf-position-skill-install-20261104/skill-table-inventory.json`，21张economy_skill_*、3张岗位表、1张执行表；不含通用身份、资金、任务与文件表。典籍维护两张源码DDL表不在该生产库。

## 2. 唯一职责

| 责任域 | 拥有的事实与决策 | 不承担 |
| --- | --- | --- |
| 技能管理（现有agent模块的skill包） | 技能定义、包版本、发布审核；安装、启停、升级、卸载；安装授权、版本/摘要绑定；执行能力的业务准入；Runtime回执与幂等；技能列表聚合 | 余额、扣款、退款、记账；不能用支付成功替代安装成功 |
| 岗位管理（现有agent.position） | 岗位定义、任职与撤职、权限资源范围；绑定共享目录的技能类型/版本；触发岗位技能的安装/移除需求 | 不另建技能安装状态机、不直接操作Runtime文件、不因为安装包就授予任职 |
| economy | 当前技能购买报价/订单/交易回执；资金冻结、结算、退款、账本及资金幂等 | 技能包内容/审核、Agent安装状态、岗位权限、Runtime目录与协议 |
| Runtime/bridge | 根据已授权合同安装和发现技能、隔离文件/进程、执行和上报真实结果 | 不认定支付、岗位任职或业务完成事实 |
| Web | 展示权威列表与allowedActions，提交用户意图 | 不独立计算岗位授权、交易或安装状态 |

商品是技能的发布与分发信息，不因有价格就把技能目录归economy。技能版本可以保留现有售价作为发布信息；交易层在报价/订单中冻结金额，不另造第二套技能目录。后续统一定价或商品模型不在本版内。

## 3. 表归属（现有21张明确分为18+3）

下表统一省略当前物理前缀`economy_skill_`。

| 技能管理拥有（18张） | 职责 |
| --- | --- |
| product、product_version | 发布目录与不可变包版本 |
| installation、entitlement | 安装与使用权益；权益可以来自购买或岗位，不等同付款 |
| managed_state、change | 当前安装指针/启停状态及操作生命周期 |
| management_quote、upgrade_policy | 管理操作意图、版本修订与升级资格；含钱部分使用交易结果，不自行记账 |
| installation_authorization、change_command | 安装合同及Runtime命令 |
| management_request、management_result | 请求幂等、回执去重 |
| delivery_binding、result_receipt | Runtime绑定及既有安装回执 |
| managed_credential、credential_operation | 安装相关托管凭据及其幂等，不代表通用凭据平台 |
| actor_root、agent_version | 现有并发锁根与状态版本 |

| economy拥有（3张） | 职责 |
| --- | --- |
| purchase_quote | 既有购买报价，金额/报价有效性/交易输入 |
| order | 技能购买订单及其资金关联；商品/Agent引用是交易快照，不是目录或安装权威 |
| order_receipt | 交易回执及交易幂等 |

`agent_position_state/authority/operation`继续由岗位管理拥有；`agent_skill_execution`继续由Agent执行域拥有。典籍维护job/action属于典籍业务，不因名字含skill而搬进通用技能管理。

**物理表名不等于职责。首版源码分离不改生产表名、不复制表、不双写，不新增视图或别名兼容层。** 18张历史前缀通过实体映射保留，所有新写入只由新归属代码执行。物理更名需要另行固定DDL及跨表外键/维护脚本的完整切换范围；不是用户本轮已执行的生产迁移，也不阻塞职责设计。不能只改前缀宣称职责分离完成。

## 4. 源码落实范围与依赖方向

复用现有agent/economy core、api、mapper、service结构，不新建独立微服务或通用框架。

1. 技能实体、枚举迁入agent-core；18张表的Mapper、DDL资源及相关schema维护入口归agent-mapper/service。已接受的物理表名、包摘要、配置值不因Java包移动而改变。
2. `EconomySkillMarketplaceMapper`与`EconomySkillApplicationMapper`是混合接口，必须按方法拆开：产品/版本/安装/权益/绑定进技能Mapper；报价/订单/交易回执留交易Mapper。`EconomySkillManagementMapper`与`EconomySkillCredentialMapper`按其技能职责迁移。不能通过extends保留一整个跨域Mapper，否则只是换包名。
3. 技能包种子、目录校验和发布配置（现`EconomyPlatformSkillSeeder`、`PlatformSkillPackageCatalog`等）归技能域。对应测试/资源一起移动；不为模块移动重发包或修改SHA。
4. 技能服务通过economy-api的窄交易入口使用既有报价、资金与订单操作，不再直接持有`EconomyLedgerMapper`或交易Mapper。economy-service实现交易入口，复用既有`EconomyPostingService`。接口只覆盖真实调用，不预建通用交易平台。
5. 当前`SkillMarketplaceService.reserve/settle`含账户初始化与资金操作，应移至交易责任层。技能服务提交可信作用域、业务操作ID、冻结报价/订单引用和成功/失败事实；交易层验证订单归属、金额、幂等与交易转换，不再重验安装包和岗位权限。
6. economy的core/api/mapper/service不得反向依赖agent的安装实体、Mapper或服务。交易输入输出采用所属API的明确DTO，不跨域传Entity，不把JSONObject当通用命令平台。技能目录聚合仍由agent服务执行。
7. 当前`SkillManagementService.enabled()`依赖`marketplace.available()`，后者又依赖`EconomyPreviewGate`，是实际耦合点。目录读取/非交易管理能力不得以经济预览开关作为自身就绪条件；有资金效果的操作继续由economy既有开关与权限控制。调整须覆盖免费与收费分支，不能直接删除资金保护或默认开放未授权交易。
8. HTTP/WS契约、reason code、岗位只读动作、Runtime合同不因内部搬迁变化。没有真实契约变化，不要求Web/Runtime联动发布。

## 5. 事务与调用链

### 普通安装/升级

技能服务：认证上下文 → Agent/技能权限与POSITION准入 → 固定版本与安装意图。

需要购买时：调用交易入口取得/核验报价及订单、执行原有资金冻结。

同一既有数据库事务：交易事实 + 安装变更/授权 + 命令意图提交；提交后由原派发器发送Runtime命令。Runtime结果回到技能服务；技能层确认安装结果，再由交易入口按原规则结算或退款。

**保留现有事务管理器和REQUIRED传播，不使用REQUIRES_NEW，不提前提交资金，不在事务中进行Runtime网络调用。** 方法移动不能改变既有身份fence、actor/skill/position/product/money锁顺序，也不能增加服务间往返造成反向锁序。具体方法逐项沿当前回归确认，不用一条臆造“统一锁顺序”覆盖不同入口。

### 岗位技能

岗位服务确定真实任职及技能关联 → 复用技能管理专用协调路径 → 安装授权与Runtime命令 → 真实回执。岗位链保持无付款人、无报价、无订单；普通手动安装仍拒绝POSITION。撤职复用既有移除/保留其他合法来源规则，不直接删文件或复制新状态机。

### 免费技能

不发生扣款/冻结/结算。既有是否保留零金额订单是兼容事实，首版不顺手清除或改写；不能为拆模块生成新的虚假交易。目录、安装授权和文件隔离仍必需。

## 6. 实施与验收顺序

1. 固定一个干净候选；按上面真实引用一次迁移实体、Mapper、维护入口、测试及资源，保留旧SQL物理名称。
2. 拆出交易入口，移除技能域直接访问交易持久化和账本的路径；同步混合schema维护入口，不允许重复扫描/执行。
3. 在现有分层检查中覆盖真实依赖：economy不引用agent；技能非交易持久化不再位于economy；技能资金操作不直接调用账本Mapper。不新建审批或台账系统。
4. 正式Flow验证：受影响core/mapper/schema/seed回归，SkillMarketplaceRealTransactionTest、SkillManagementTransactionTest、PositionSkillTransactionTest及相关HTTP/codec回归；真实数据库验证付款+安装意图原子回滚、幂等、失败结算、零金额与岗位无订单分支、岗位手动安装403、已安装技能列表及目录不丢失。保留validateLayering/fresh JAR；按实际改动补selectors，不机械全站重跑。
5. 测试与源码精确匹配后集成；部署仍需绑定固定Run制品并按既有授权独立安装。没有DDL时不执行写库迁移；若后续要求物理更名，先单列实际迁移与恢复范围。

本版验收分清三件事：职责设计已确定；源码分离需正式回归；上线需安装和业务证据。设计冻结时只完成第一件；后续实施状态见§7与handoff。

## 7. v1 实施细化（2026-11-04）

API 候选 `ba391c6ed9fe767a4b1dd2efa30cce70d2f288ee`，tree `7cddd0785c20a555577b71d9903171b07b16cb9b`，版本1.1.28-SNAPSHOT。生命周期实体/Mapper/配置/种子/测试及六个包资源已迁入agent；报价/订单/回执及资金通过economy-api访问，非交易安装链去除经济开关依赖。正式测试与集成结果以handoff为准。

维护资源有一处明确的联合职责：原七表 `economy-v0-skill-marketplace.sql` 含四张生命周期表与三张交易表，其相互引用及单次维护合同保留，整体随唯一schema-maintenance协调入口迁入agent。没有复制资源或在economy再注册一个initializer。交易表运行期写入仍只归economy交易实现；联合建表资源的位置不等于把交易业务搬回agent。其余旧配置键、物理表名及资源名保持，避免无必要部署配置变更。

消费者核对补充：实际Web `isSkillMarketplaceCapability`、技能路由及个人主页入口仍将技能可用性与经济预览AND绑定。因此本版包含最小Web适配（按技能能力字段展示/导航，保留钱包经济开关、scope检查与身份切换清理），不是HTTP/WS字段变化，也不修改Runtime。原型规格同步的是PC/移动端可用性状态，不新增页面或布局。此前“无需Web改动”的预判以此实际依赖核对为准。

## 8. 实施验收（2026-11-04）

- API develop `c70fe5df5d317f440f08567b585786c0445faeb3` / tree `44a500abd1718db3bfbffc34e2aa05cf9f337fb0`，1.1.28-SNAPSHOT；Flow5260799/489 SUCCESS，347项、0失败/错误/跳过，分层检查、真实事务及fresh JAR通过。
- Web develop `b9fd324f59785e0a758bb98eb5be8c412d62232b` / tree `7dced76dae330c483f48f1dd044a178411f2dd7a`，1.16.106；Flow4403172/436 SUCCESS，139项通过、Vite构建及代码扫描成功。
- 两端均非强制快进并readback，原Flow配置CAS恢复。本轮没有生产部署/DDL/服务重启、Runtime变更或付费模型调用。完整典籍外部Runtime场景未重放，只编译该测试调用方；本轮岗位安装与资金事务由真实DB回归覆盖。
- 证据：`/home/isp/state/cyf-skill-economy-separation-20261104/final-verification.json`。云端制品已生成/上传，本轮没有下载或安装；后续发布应复用上述固定Run，不为安装重建。

## 9. 用户追加物理表更名（2026-11-04，覆盖首版保留旧名的范围）
18张生命周期表由economy_skill_*改为agent_skill_*；3张交易表原名不变。API源码、DDL/catalog、外键引用及测试同步，保留既有字段/唯一键/事务/权限，不增加CHECK或兼容层。固定正反向单条RENAME脚本只由停写后的受控迁移执行，禁止启动自动迁移或旧JAR访问新表名。备份及回读覆盖真实行摘要、外键与触发器；恢复反向更名配套旧JAR，不恢复业务数据快照。Web复用436，Runtime不变。具体实施与线上状态见同一handoff，原489制品不能配新表发布。

## 10. 物理名称与上线验收（2026-11-04）
第9节已实施并上线：18张生命周期表统一agent_skill_*，3张交易表保留economy_skill_*；21表数据摘要及外键/触发器保持，无复制/双写/别名兼容。API494（df4b5e8bc6/1.1.30-SNAPSHOT，454tests全过）、Web442（421283b/1.16.108，329tests全过）固定制品主机独立安装。API develop集成28a076098c与494同tree，制品仍记真实受测commit；Web已集成develop。当前生产管理链及既有岗位/图片技能状态验收通过，未重新调用收费模型或重放外部工具E2E，Runtime未变。具体版本、备份/恢复、并发合入、失败Run及覆盖边界见既有handoff末节，主证据/home/isp/state/cyf-skill-table-rename-20261104/final-verification.json。此前§1–8是首版源码分离历史基线，不能作为当前仍使用旧物理表名或尚未部署的依据。
