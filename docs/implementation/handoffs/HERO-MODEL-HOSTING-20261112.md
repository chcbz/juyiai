# 108好汉固定模型与成本比例托管定价

**当前状态（2026-11-13上线验收）：数据库目标模型绑定与托管定价已上线；API1.1.49-SNAPSHOT/f3fd61a848，本地167项测试0失败0跳过、分层及制品检查通过。生产108人/8模型配置和线上目录逐项一致，健康/摘要通过，旧套餐及历史租约价格不改。公开参考价已核对；私有渠道账单、Runtime实际模型切换及推荐承办费不在本次完成范围。**

任务：`HERO-MODEL-HOSTING-20261112`。Owner：当前会话（hero-model-owner/developer）。日期2026-11-12。

## 范围与输入

- 用户要求：把已定义108人模型写入好汉配置；以gpt-6.1-terra=500文为平台托管基准，尽量按模型成本比例、可适度四舍五入。
- 开始复用根/API develop工作区；后因另一任务并发修改API，最小隔离到 `/root/.codex/worktrees/hero-model-hosting/api`，仅转移本任务路径并恢复共享工作区内本任务差异，保留其他修改。根基线c0cfe2a9926fdddc18ba28b5227cb1d33715c4e1；本轮API基线57b6d5f423122ce1f14a18402c1ccc7724236ea5；API工作区开工干净。根/Runtime存在其他任务修改，未覆盖；未查询远端最新、未推断线上版本。
- 规则：根AGENTS、api/AGENTS、接口规范api/docs/interface-standard.md v1.4；默认本地验证，经编排器串行，不调用付费模型/Flow，不部署。参考成本源与公式在责任合同 `specs/juyiting-agent-model-governance/hero-model-assignments.md` §6，临时产品价档已弃用。
- 非目标：事项承办报价、人民币实际成本账、自部署/技能费、已有租约迁移、Runtime真实调用配置、生产改价/扣款/部署。

## 历史责任链及已撤回候选

- API agent-core WaterMarginPersonaCatalog固定108个modelId，独立于运行时真实executionModel；API DTO投影5个配置字段，保持系统宋江不可租用及原ACL。
- economy-core HostingModelPriceBook唯一持有成本参考价与30天托管价：相同4∶1非缓存输入/输出参考，基准500文，最终HALF_UP到10文。官方标准短上下文公开标价，不冒充实际渠道采购/用量。
- 新邀请server按personaCode选择模型planId；经济域原immutable plan/quote/lease/ledger负责资金，local仍50文。旧确认重放和原租约续期继续原planId及金额，不重写历史。移除/交接识别精确模型套餐，保留managed清理和身份边界。
- Web已有报价面板直接展示服务端金额，无新价格算法；本轮无Web源码修改。字段无害新增，Runtime控制wire不变。
- 必须区分：目标配置、候选报价与Runtime实际模型。**Runtime模型下发/一致性尚未接通，不是本轮配置成功的证明；不得以此候选直接宣称可按目标模型交付或已完成线上差异化收费。**

## 历史验证与状态（以下待执行描述已由接续结果取代）

- 静态108行模型/姓名/稳定键与责任文档逐项一致：通过；代码新增测试覆盖全表价格、107可租角色新报价、未知/错价、旧报价/续租、自部署、managed移除与公共目录不伪造执行模型。
- Gradle定向验证、layering待执行；精确候选及包外日志写入 `/home/isp/state/cyf-hero-model-hosting-20261112/`。
- 未构建生产包、未修改线上/Runtime、未改生产数据；全库文档入口依赖缺失，仅做定向校验。
- 定位/实现/验证/等待耗时：未知不补填；本轮无生产发布等待计入开发统计。

验证候选commit `e3c7886b1badc6b6acde9b526cbf9aaae78fcd42`，tree `f8a626fdb10f153ad9ac9b31f583466818dcc8b6`；本地隔离worktree。

## 2026-11-13 纠正与撤回

- verify-01：并发SETUP片段误带导致编译失败，70.052秒；ac76d0a9f1仅移除误带片段，另一任务worktree原修改完整保留。
- verify-02：Mockito循环重设when触发旧answer空参数，107.506秒；5a342cae79改为doAnswer。
- verify-03：启动Python版本及编排gate问题，未执行Gradle；原回执保留。
- verify-04：109.538秒通过，测试汇总 {'tests': 75, 'failures': 0, 'errors': 0, 'skipped': 0}，validateLayering通过。仅为已撤回候选的历史结果，不代表正确配置方案获验收。
- 用户随后明确否决模型/价格硬编码，要求继续撤回；撤回commit `71ac8a3c4725ed4c94d6cc06779932166b10d873`，tree与基线57b6d5f423完全一致；13个候选文件净差异归零。共享API仍在原基线且干净，未合入、未推送、未部署。
- 根文档仅修正本任务段落；恢复统一租费现行口径，保留其他任务对首次技能/自部署规则的修改；108行分配和8档价格作为草案保留。
- 核查既有配置发现：economy.pricing.models/tools为启动时人民币价目索引；agent.hosting-rent提供统一托管金额；租费表为不可变套餐快照；agent_persona无固定模型字段。不能只改现有套餐表就完成模型差异化，也不能宣称现有配置支持热更新。详见分配表§7。
- 本次撤回交付不包括重设计/实现新的动态配置管理，不以Java换成内置JSON/YAML常量替代。后续须复用真实配置能力，仅补模型绑定与价格读取缺口；未完成生效配置目标。
- 证据：`/home/isp/state/cyf-hero-model-hosting-20261112/withdrawal.json`、verify-01至04原日志、root-cause-matrix.md；无生产最终包、无制品发布回执。

## 2026-11-13 外置配置接续

- 用户在撤回完成后要求继续，复用原隔离worktree，不新增worktree/框架/表或后台。基线仍为57b6d5f423，原硬编码已归零，恢复任务ledger用于本次外置配置验证。
- 外置模型绑定和托管价Map扩展既有AgentHostingRentProperties；具体108人/8档价格仅在docs/examples/hero-hosting.properties运维候选文件，不打入应用默认资源。配置由已有Spring机制导入，需受控重启，不支持热更新。
- 平台类型仍用原planId，模型价按唯一版本选不可变套餐，故移除/交接不必复制模型白名单；手动续期改为读原租约版本/金额/周期，避免调价重写历史。自部署、技能、承办及Runtime合同不变。
- DTO新增4个可空string目标/参考价字段，executionModel仍为真实观察，不用目标覆盖。
- config-verify-01在测试编译失败（81.132秒）：提取构造helper引用setup局部变量；修为fixture field/JdbcTemplate持有的数据源，原日志保留。新候选3d82f76302进入config-verify-02。
- config-parity.json验证108个稳定键/模型/金额与草案一致、8个唯一版本、Java实现不含模型名单；不代表价格来源已核验或线上已加载。
- 并发任务RUNTIME-LEASE-SEPARATION在独立worktree增加quoteSetup/建链路径；其方案合入时须将新平台报价同样接到本次通用plan(actor, planId, personaCode)选择，并保留其非收费建链边界。当前未编辑/合入该任务worktree，不能声称未合入路径已覆盖。

### 外置配置最终自检与合入

- config-verify-02：3d82f76302，47.916秒；74项所选回归通过。公共develop随后推进到d0cdf6a03a，第一次条件式合入安全拒绝，未覆盖任何修改。
- 在原隔离worktree合入d0cdf6a03a，保留其SETUP建链/新观测/禁用激活边界；quoteSetup与原quote都使用同一外置模型套餐选择。补同一应用回归覆盖两路径各自更换模型价格。未触碰另一任务worktree。
- 最终候选 `fd9a5ff3b7dc69c827d0d236eac6af8582b5ca59`，tree `9ebe68f70518a3dd61533655b1182400fa243958`；config-verify-03耗时50.832秒，74测试0失败0跳过，validateLayering实际执行通过。这是应用配置/报价责任层回归，未运行无改动的SETUP MySQL集成或线上业务验收，不继承他人通过证据。
- 共享API develop已安全fast-forward到该受测commit，工作区干净；未push、未部署、未重启、未写数据库或生产配置。根文档更新与其他任务脏修改并存，未混合提交根ledger/Runtime/gitlink。
- 最终回执 `/home/isp/state/cyf-hero-model-hosting-20261112/configuration-delivery.json`。复用输出目录还留有旧economy/core XML，明确排除，不能计作本轮测试；本轮只计5个选中suite共74项。
- 无生产最终包，无需登记包清理回执；包外证据保留。任务专属build中间目录可在证据留存后清理，已合入worktree可归档。
- 使用入口：`/home/isp/wsps/cyf/api/docs/examples/hero-hosting.properties`、同docs的hero-model-hosting-configuration.md。上线前仍须核对实际渠道成本、补Runtime模型下发及交付一致性，不因配置投影成功自动启用差异化收费。
- 收尾实际执行：仅删除本任务`verify-01/build`中间产物，所有日志/XML/input/result/receipt保留；归档worktree工具拒绝（`The task's primary checkout cannot be removed.`），因此保留当前worktree，未绕过工具手工删除。


## 2026-11-13 数据库配置接续（取代外置文件方案）

- 唯一配置源改为`agent_persona_model`好汉→模型、`economy_hosting_model_plan`模型→当前价格版本；复用既有不可变`economy_hosting_rent_plan`。无Java模型/金额名单，无properties Map消费路径，无进程缓存；提交后下一次读取生效。
- 两张新表显式DDL，同scope复合外键，无CHECK/新触发器/启动迁移；`docs/examples/hero-hosting.sql`完整108绑定/8模型/8价档，默认不执行，不覆盖既有scope。价格仍为待渠道证据核验的草案，不能称已对齐实际采购成本。
- 原邀请与SETUP报价共用数据库选择；缺价不回退统一价格；金额/周期/币种/状态等资金规则由原报价应用服务校验。旧报价重放/原租约续期仍使用原价，自部署、技能、承办/推荐费不变。
- 目录/批量DTO按scope一次数据库读取，单实例按可信scope查询；configuredModel不覆盖executionModel。宋江辅助投影使用已有调用方client，不回读请求上下文。无管理后台及Runtime下发改动。
- 候选c4f521fb5b、efab8f9cc1及后续ae5a96d19b；最新完整commit/tree以db-verify-02/input.json为准。共享develop仍保留前一已测外置文件基线，待本轮验证后安全集成。
- db-verify-01：真实隔离MySQL端口33855，启动约73秒，冷依赖编译在总批次590秒处按600秒上限受控SIGTERM；总耗时593.935秒，未到测试，不记通过。inner result的timedOut=false只是收到SIGTERM，超时事实见deadline-guard.json及本段；原日志/回执不改写。own server已关闭且只删除其独占datadir，生产3306未访问。
- db-verify-02：保留本任务已完成编译输出复用；把余下批次预算传给内层runner避免外层超时遗留编译。复用原Gradle编排器串行锁，不绕门禁、不调用Flow。完整DDL/seed/FK/无缓存/历史价格真实MySQL验证与应用/目录/SETUP等定向回归并行职责分测，实际结果待回执。
- 验证边界：原续期应用回归覆盖旧价格；HostingRentRenewalMySqlTest夹具同步数据库价源，但完整跨Runtime生命周期套件未执行；不冒充全站/线上/付费模型验收。
- 包外证据目录`/home/isp/state/cyf-hero-model-hosting-20261112/db-verify-01/`、`db-verify-02/`；无生产包、无部署、无生产数据库写入。原worktree作为当前聊天主checkout不能归档，保留、不强删。


### 数据库候选本轮停止点

- 最终代码候选`ae5a96d19bddfa8f8c7cfb8c9359065831538aba`，tree`e63d06d711f5e930c182bb73f9952cc6f78acbe8`，工作区干净。共享API develop仍是`fd9a5ff3b7dc69c827d0d236eac6af8582b5ca59`的历史外置文件实现，本轮未合入、未push。
- db-parity.json：108角色→模型→金额逐项与分配表一致，8模型/8版本，锚点500；此项为静态一致性，不是渠道成本核验。
- db-verify-02/sql-smoke.json：显式核对独占MySQL datadir后，在另建hero_config_sql_smoke库实际执行原租费DDL、新表DDL、完整初始化SQL；读回108人/8模型、terra=500、quote=0、lease=0，测试库已DROP。它只证明SQL结构/数据初始化，不冒充Java报价/FK拒绝/历史不可变等尚未执行的JUnit测试。
- db-verify-02总耗时594.985秒（Gradle子执行492.026秒），应用service编译期间内层deadline触发SIGTERM；timedOut=true。Gradle/java/隔离MySQL均已退出，fixture datadir清理完成；不杀其他任务/生产进程。编译未报源码错误，但未完成测试和validateLayering，不能计通过。
- 本次观测到主机另有非本任务清理进程占CPU，未干预；复用已完成依赖编译仍未在预算内完成。停止自动重试，请用户允许下一次验证单次上限20分钟，未获准前不再启动。保留本任务编译输出供授权后的增量验证，包外证据不清理。
- 无生产数据库数据变更，无生产包/部署/Runtime模型切换。数据库配置功能完成实现候选，不是完整验收/上线完成。


### 用户授权20分钟验证接续

用户明确“允许，不要问了，赶紧完成”，本次db-verify-03单次上限1200秒；原失败回执保留，复用同一候选和已完成编译输出，经原编排器执行，不扩成生产迁移/部署授权。


- db-verify-03按1200秒上限受控结束，总1197.105秒；agent-service编译340.067秒、chat-service162.082秒、common-test80.011秒及其余主要依赖均完成；停止在compileManagedHostingRegressionJava，不能计作测试通过。精确候选仍ae5a96d19b，无源码变更。
- db-verify-04在启动MySQL夹具时触发继承的90秒子超时，尚未启动Gradle；保留原日志/回执，独占初始化进程已由subprocess清理，datadir清理。与冷编译超时是不同原因。
- 完成既有root-cause-matrix后，经原authorize-remediation恢复同一Owner；db-verify-05仅把初始化子限时调至300秒，仍从总1200秒扣除，不放宽总限时。不改生产MySQL或其他任务进程。
- db-verify-05先等待已有Gradle串行锁（另一任务正常持锁），随后实际取得锁。等待计入本次预算，未绕锁/抢占/停止他人任务，未与其他聊天发消息。复用本任务已完成的固定源码输出，不重标前几轮失败为成功。


### 数据库方案最终验证与合入

- 最终源码`ae5a96d19bddfa8f8c7cfb8c9359065831538aba`，tree`e63d06d711f5e930c182bb73f9952cc6f78acbe8`。db-verify-05执行成功；总批次1188.935秒（含独占MySQL初始化/串行锁等待），Gradle编排执行676.066秒，未超过用户允许的1200秒。此前失败/超时回执全部保留，未重标成功。
- 7个实际suite共78测试，0失败/0错误/0跳过：真实数据库配置3、应用报价38、交接16、迁移7、目录投影9、配置3、真实SETUP报价2。验证DDL+108绑定+8模型、500文锚点、同一reader改价/换模可见、跨scope/FK拒绝及旧套餐不可变；原邀请/SETUP报价共用数据库、缺价/错价失败、旧租约价保护、自部署不变。
- validateLayering实际执行94.993秒，通过（未跳过）；无生产fresh JAR构建或发布。测试XML/日志/输入/fixture回执与SHA-256在db-verify-05/summary.json，最终交付回执`/home/isp/state/cyf-hero-model-hosting-20261112/database-configuration-delivery.json`。不计旧XML，也不把本轮选中2项SETUP测试当其整套测试通过。
- 合入前核对共享develop为fd9a5ff3b7且干净，git merge --ff-only后等于上述受测commit/tree且干净；无额外API源码改动，不需要重跑同一输入。未混合提交根规格/handoff/其他任务脏修改，未写其他worktree。
- SQL入口`/home/isp/wsps/cyf/api/docs/examples/hero-hosting.sql`；维护说明`/home/isp/wsps/cyf/api/docs/hero-model-hosting-configuration.md`；DDL在同API的agent/jia-agent-mapper/src/main/resources/db/agent-persona-model-hosting.sql。初始化需明确目标scope，不能默认执行生产迁移。
- MySQL57173独占实例已关闭，独占datadir清除；原生产3306未访问。保留本任务固定源码编译输出供后续增量验证，避免再次冷编译；没有生产最终包待登记。当前worktree是聊天主checkout，之前归档工具已明确拒绝，不强制删除。
- 数据库配置实现/本地集成切片完成；尚未执行生产迁移/部署、Runtime实际模型下发及实际渠道成本核验，未更改推荐/承办费用或伪造模型交付事实。完整跨Runtime续期MySQL套件、全站浏览器与线上验收未运行，不继承历史通过结果。


### 2026-11-13 接续：生产只读核验（未启用）

本轮不重跑同一源码的78项测试、不改变已完成实现切片，不把用户继续指令当成允许编造成本数据。

- 实际通过本机MySQL socket执行`START TRANSACTION READ ONLY`：`jia`中只有既有`economy_hosting_rent_plan`，两个新配置表尚不存在。scope与既有套餐一致（tenant 0 / client jiafewnnv58ec2379c），固定环境tenant也为0；未宣称已审计全部有效datasource环境覆盖。
- 读回现行平台套餐version=1、500文/2592000秒；自部署version=1、50文。两条不可变UPDATE/DELETE保护触发器存在。未执行DDL、INSERT、UPDATE、DELETE或生产备份恢复。
- 只读检查生产JAR内部agent-mapper/service两包，均未包含`PersonaModelHosting`新配置读取类；不能宣称数据库方案已经线上生效。JAR摘要及受检包名固定在本轮receipt。
- 生产成本配置只覆盖请求8模型中的`gpt-6-luna`：人民币/百万Token INPUT=0.668790、OUTPUT=3.343950、CACHED_INPUT=0.066879，来源标记为用户确认渠道价。其余7项（包括500文锚点模型）的实际成本缺失。孤立的luna单价不能证明八模型成本比例；本轮官方检索/打开也未返回可用价格证据，不沿用草案数值冒充核实结果。
- 数据库目录/现价快照、只读SQL、生产包摘要、成本来源及迁移/恢复顺序保存在`/home/isp/state/cyf-hero-model-hosting-20261112/activation-preflight-01/`。这是只读预检，不是可恢复数据备份或发布证据。最初查询误用`version/amount`列名失败，随后按SHOW CREATE TABLE的真实`plan_version/amount_wen`重查成功；两次均只读。
- 后续真实前置：取得其余7模型渠道成本或明确采用非成本核实的暂定价政策；按现有迁移/发布锁保存备份，应用增量DDL与最终配置；受控安装已验证源码的构建包；收费启用前核实实际模型交付。DDL不能通过DML回滚撤销；失败初始化ROLLBACK，不覆盖旧套餐/历史报价/租约。现阶段不自动启用草案差异化收费。


### 2026-11-13 上线请求与GitHub定价核验接续

- 用户要求“完成上线”后发现开发候选和线上c7c0f2d78d无共同历史（开源导出），同时含其他任务未上线SETUP/outbound/交接改造。为避免连带发布，在原主worktree创建`codex/hero-model-hosting-release`，以真实线上commit为基线，仅移植本功能13文件；提交`5c6d6ddf57bf925380c7b0de78966f2bd7b1d9ba`、tree`c8440186bc87aad6802a1f73a55767cfc89f8af2`，版本1.1.49-SNAPSHOT。共享develop及其他任务未改写；原78项结果仍只证明ae5a候选，不冒充新候选验收。
- release-verify-01使用既有LOCAL builder及Gradle锁，附加本功能应用/目录/真实MySQL/旧交接测试，隔离夹具与构建整体600秒。初始化/依赖编译消耗预算，wrapper在590秒前后超时，systemd清理本任务子进程；builder记录STOPPED_BEFORE_COMPLETION、publishable=false。未完成新候选测试/bootJar，未部署、未迁移。自有MySQL已停止，保留日志及编译输出；此前成功测试未被重标。本轮失败需按冷输出与fixture占时归因后才能续建，不盲重试。
- 用户随后明确先核实成本，并指定GitHub来源；停止生产写入/发布。实际下载两个仓库的JSON：llmrates/llm-pricing-dataset与simonw/llm-prices，经jsDelivr取得（直连GitHub超时）。逐项筛选OpenAI Standard短上下文/当前price_history，8项输入、输出、缓存读单价均一致，Decimal按500*(4I+O)/9、HALF_UP到10文计算，结果为5000/1000/1000/500/50/2000/1110/110，与现有SQL一致。
- 原始JSON、真实SHA-256、抽取字段、计算公式及SQL一致性在`/home/isp/state/cyf-hero-model-hosting-20261112/channel-cost-20261113/`。这是GitHub公开参考价核验，不是私有采购成本；网关只读模型目录确认8项存在但无价格字段，不虚构折扣/账单。未进行收费推理调用。
- 来源身份与内容固定通过下载文件摘要，未取得上游commit不编造Git SHA。此前未能返回有效内容的检索不计证据，实际核验仅以成功下载/解析的两个JSON及浏览到的GitHub文件为准。规格§6已由“缺公开价格证据”更新为“公开参考价已交叉核验、私有结算未核实”。

### 2026-11-13 发布接续（进行中）

- 接续时发现release-verify-02仍运行，未并发重启构建。最终总596.951秒停止；新候选主agent编译完成310.896秒，未完成所有测试和bootJar，仍不可发布。
- 核对原始两个GitHub JSON的SHA-256及8档Decimal公式，仍与初始化SQL一致。公开参考价格不是私有渠道结算；4:1输入输出为规划假设，不冒充实测负载。
- release-verify-03利用本轮刚完成的主模块Gradle编译缓存作为实质重试条件，原源码commit/tree不变； fresh批次仍执行必要回归、validateLayering、最终bootJar和包摘要，不复用旧测试成功。保持600秒总限时、原编排锁、独占MySQL，若编译缓存未复用或再次超时则停止盲重试。
- `production-release/migrate.py`、`install.py`、`online-readback.py`已准备但尚未执行生产写入：必须BUILT/精确源码/摘要通过后才备份并增量迁移、安装及在线108行逐项核对。原套餐、报价、租约和钱包不更新；既有Runtime实际模型不伪造为配置模型。
- release-verify-03最终594.114秒停止；主模块确已FROM-CACHE（4.987秒，前批310.896秒），但配置/依赖图和必要验证仍未在默认600秒内完成。原失败证据保留，未写生产。
- release-verify-04接续沿用用户此前对本任务明确批准的20分钟验证例外（“允许，不要问了，赶紧完成”），1200秒独立限时，不变更全局默认、不向生产安装/服务下传截止时间；这是限时参数的明确变更，不再同输入盲重试。成功与否以04实际回执为准。
- release-verify-04：Gradle595.195秒完成，15个suite共167测试0失败0跳过，validateLayering和fresh bootJar通过；整批643.087秒，打包失败`TEST_EVIDENCE_INVALID`。根因为AgentPersonaPublicScopeTest两个参数化方法生成重复(classname,name)，不是业务测试失败。未修改XML或放宽producer。
- release-verify-05：只修复这两个参数化测试的显示名称为`{displayName} [{index}] tenant={0}`；候选`f3fd61a84833266ee68a7ce06ad61c77f72d7077`/tree`cea03a51924f11b3cd5ac50cf46f47ae2563a215`，业务字节来源不变，版本仍1.1.49-SNAPSHOT。完整fresh测试/包绑定新候选，旧04失败回执保留。不以04 JAR替代05身份；仍未写生产库。


### 2026-11-13 最终生产交付

- release05在执行Gradle前被旧task tree pin拒绝（未绕门禁）；通过既有Owner transition更新到新候选，再执行release06。
- release06最终源码f3fd61a848/cea03a5192，167测试0失败0跳过，validateLayering及fresh bootJar通过；Gradle820.024秒，总批次1131.816秒，未超过本任务已获准1200秒。测试报告名称唯一性已核验，所有旧失败回执保持原状。包/JAR/源码及测试证据在build-verification.json。
- 增量迁移先经历一次全局发布锁冲突，等待锁自然释放后重新核对原生产摘要，未抢锁/换锁/停他人任务。原租费表与schema备份到/home/isp/baks/hero-model-hosting-20261113，108绑定/8模型/8新套餐事务提交；旧套餐快照读回不变。
- 原LOCAL安装器第一次在切换前因既有backup别名目标/home/isp/baks/flow-api缺失而拒绝；保留失败log及旧record，按原固定路径恢复root:root0700目录、不改安装器/锁、不伪造旧历史备份。第二次受控安装成功，新的原运行JAR备份摘要与原生产9edc1650...一致；曾缺失的历史备份在repair回执中明确记录。
- 新API JAR SHA256 `054f4e819472274a426295342ec8820ee4b7383529de23562680489debec706e`；应用PID3787147，HEALTH=UP、ARTIFACT_ATTESTATION=MATCH，标准启动参数未加入DEBUG/TRACE诊断。8项canonical-path检查通过。
- 2026-11-13 09:47（Asia/Shanghai）通过既有专用测试用户PKCE登录，只读GET目录HTTP200/E0；108项persona/model/amount/version/period全部与已提交数据库一致、8模型、terra500文/2592000秒、宋江系统角色不变。无收费模型调用或业务写入验收。
- 总交付回执 `/home/isp/state/cyf-hero-model-hosting-20261112/production-release/delivery.json`；同目录保存数据库/线上全108行、构建校验、受控安装、恢复及备份记录。当前主worktree保留，不删除其他工作区或合入未上线SETUP改造。
- 本次上线为数据库目标配置及托管报价读取；Runtime实际切模、私有采购价/折扣、推荐承办费与真实扣费链路验收未实现/未执行，不把公开参考价称为渠道结算价。后续调价通过插入不可变新套餐及更新数据库指针，无需修改Java或重启。
- API文档事实收口为独立docs-only提交fcebdeb2fb，不冒充生产源码f3fd61a848。根共享文档/ledger只改本任务记录，未混合提交其他任务修改。
- 已两次调用既有包mark-complete登记入口，均因维护锁忙安全拒绝；未绕锁、未清理包/日志/备份，未宣称登记成功。当前已安装包保持完整保留，待维护锁空闲再登记；此项仅影响后续缓存回收登记，不影响已完成安装、恢复备份和线上验收。当前主worktree保留。


## 2026-11-13 后续UI：模型名称并入好汉信息（仅本地实现，未发布）

- Owner：当前Codex任务；范围只含详情模型位置与招贤令模型名称，不改模型绑定/定价/API/Runtime。Web复用 `/home/isp/wsps/cyf/web`，develop基线 `113c6e69938387dd10439b30a1be22245f3544cc` / tree `7a373751aa067f81933a3b03c7cc773d53b4965d`。
- 已提交Web `d244cada762c8ea60b1cf25401a495bff03ef39c` / tree `c03b97c46e53a85b96e9358b114d866556fe7a19`，未push、未生产打包、未安装。保留同工作区并发的HostingRentPanel/hostingRentContract/useHostingRent修改，未纳入本提交。
- 原型先行：唯一原型 `web/prototypes/juyiting/` 的agents/catalog及规格更新，复用现有18786服务；HTTP与Chromium 1440/390/320离线验证。没有启动或停止他人预览进程。
- 产品：AgentPanel把executionModel及无权限/加载/错误/未上报状态并入头像旁身份信息，移除独立section；PersonaCatalogPanel在名号/星号下展示configuredModel，缺失为暂未配置，不用配置值冒充已上报模型。
- 本地定向83项及邻近43项测试通过（不是全套）；两文件lint原有55 errors/21 warnings，逐条规则/消息/源码行指纹与基线相同，无新增。正常/长名称、文本转义、切换/刷新/无权限及目录字段覆盖。
- 产品Chromium使用真实Vue组件配离线fixture，1440/761/760/601/600以及独立完成的390/320检查通过，模型位置及长名称无页面横溢；不是认证生产实页或真机。首轮测试fixture漏传filteredAgents导致手机选择器超时，已修fixture；后续长运行预览被终止/连接拒绝的记录保留，手机改用domcontentloaded和独立短批次完成，未将中断批次重标全量成功。
- 证据与测试、截图、源码摘要：`/home/isp/state/cyf-hero-model-ui-20261113/delivery.json`及同目录。临时产品预览已结束、临时HTML已移出源码，自动生成components.d.ts已单独保存差异并恢复；既有原型预览仍保留。

## 2026-11-13 用户授权发布模型信息UI

用户明确“上线”。线上实际Web为b35cdbd/1.16.136，不包含develop中的接应目标准备改造；本次以该线上源码为基线，仅移入d244cad模型信息改动，原型冲突按线上既有行为+本次模型行解决。发布候选469ad526185a98ef15c1e0512e83b595b8b59806 / tree 0c9eaf2685acf73cf8376033292172405843d087 / 1.16.139，隔离worktree `/root/.codex/worktrees/hero-model-ui-release/web`。目标仅Web两处展示；保留当前brand/demo/下载限制，不发布API/Runtime/未授权接应改动。原始开发提交d244cad保留，不回退共享develop。既有本地builder+受控LOCAL安装器，单次600秒，证据根 `/home/isp/state/cyf-local-build/tasks/hero-model-ui-20261113`；授权、前代record/index摘要已保存，未实施生产数据写入。

### UI发布未执行：资源争用阻塞（2026-11-13）

- 发布分支codex/hero-model-ui-release已推送469ad526185a98ef15c1e0512e83b595b8b59806，未回退/合入共享develop中的接应改动。
- R1：178通过/2可选pending，冷依赖283.18秒、测试50.893秒、Vite构建191.906秒、打包52.029秒；完整归档验证未在600秒内结束，STOPPED_BEFORE_COMPLETION，未安装。
- R2：177通过/2pending/1失败；原有配置加载smoke10秒超时（11979ms，R1同测试6956ms）。未构建/未安装。
- R3：仅本任务builder及子进程nice -5；前置排队锁154.933秒，依赖核验221.996秒，测试194.028秒；配置加载及SelectedAgentCard交互出现原有10秒超时。FAIL，未构建/未安装。周期清理持续运行，另一次构建曾占用串行锁；未停止他人任务或生产服务，未绕锁、删测试、修改断言或放宽测试/600秒上限。
- 同根因重复后停止盲重试，等待真实负载改善或用户明确允许协调维护任务。release-status.json记录各尝试及前代摘要复核。生产record/index仍与发布前完全相同，线上保持1.16.136/b35cdbd，不得称1.16.139已上线。
- 私有浏览器前置诊断曾遇PWA导航、只读roster使用POST、引导异步浮层；仅修正验证脚本的真实入口、只读POST准入和浮层关闭，不改产品。没有把前置失败冒充新UI线上验收。源码worktree保持干净、单一隔离以待恢复；日志和首轮未放行包均保留，不清理未知或生产绑定资料。

### 2026-11-13 本次UI已受控上线（复用R1现成包）
- 用户要求构建完成即直接用包部署；未再次构建。R1原STOPPED_BEFORE_COMPLETION原件保留；独立恢复校验通过，逐项验证614个归档成员、全部文件大小/摘要、嵌入manifest、gzip完整性、178通过/2pending/0失败测试报告及固定源码/工具。
- 上线版本1.16.139；commit `469ad526185a98ef15c1e0512e83b595b8b59806`，tree `0c9eaf2685acf73cf8376033292172405843d087`；真实批次HERO-MODEL-UI-20261113-R1；包SHA-256 `34ece330cf8785521252d8baf20f4fbdcd3270f9d6bf9d7aff97a7955a387f7d`。
- 原deploy_local受控安装成功（113.934秒），613文件、30文件变化，线上256个index/JS/CSS摘要通过；生产record为online_verified。保留身份/ACL/发布锁/前代比较/备份/失败恢复。未发布共享develop其他改动。
- 证据根 `/home/isp/state/cyf-local-build/tasks/hero-model-ui-20261113/`：r1-recovery-validation.json、install-descriptor.json、install.log、record-after.json。
- 认证浏览器验收未完成：专用测试用户名册/目录条目未出现，保留attempt03/04超时证据，不冒充UI验收通过；前期精确组件fixture和响应式验证仅为本地证据。部署及线上资源核验已通过，不与浏览器验收混同。
- 最终包mark-complete登记因既有cleanup锁忙安全退出，保留包及全部证据，不停止维护进程、不绕锁；后续可按原保留入口登记。

### 2026-11-13 后端本地包取消外层压缩
- 用户“不要多此一举”：根工具提交13829d52，当前builder默认package/api.tar，不压缩，保留JAR、版本/来源/校验材料。兼容在途旧builder .tgz调用和历史gzip包。不改Web，不重新构建/发布应用。
- 原安装器两处读取改内容识别，保留成员/摘要/ACL/锁/恢复；持原coordinator→release锁备份并原子适配现有主机脚本，仅替换两处读取，不覆盖其独有内容。原维护器在host锁下补.tar登记。备份/home/isp/baks/cyf-api-no-compression-20261113/。
- producer41、retention70、builder9、source安装边界8、已安装helper离线冒烟3项通过。完整native套件31项有4个15秒超时、2个现有forward-only失败（未修改HEAD测试源复现后两者）；不标全套通过、不改超时/断言。
- 证据：/home/isp/state/cyf-hero-model-hosting-20261112/backend-build-analysis-20261113/no-compression-delivery.json及同目录日志。没有Gradle构建、应用安装或服务重启；下一次整批缩时待实测。

### 2026-11-13 默认后端发布链路精简
- 用户要求删非关键步骤/测试；本轮仅调整根本地工具，见commit 10006120e49ee618fb5b609324badb549348ff05。启动计时/性能指标/Elasticsearch健康隔离三组（历史10项/44.355秒）从默认执行筛选与编译slice一并移出，保留源码，相关改动显式运行。新selector local-fast-baseline-v3-critical，避免旧默认数量/历史证据混用。
- 删除仅用于输出的逐任务依赖图打印；保留阶段/任务耗时、凭据移除、禁止嵌套Gradle、缓存与串行锁。身份/认证/邮件runtime、生产包安全/POI、分层检查、fresh JAR、业务实际受影响回归、安装校验及恢复未删。
- builder11/cache默认12/release runner5，共28项控制器回归通过。未启动Gradle/应用打包/生产安装，不宣称新链路实际缩时或应用验收完成。证据在backend-build-analysis-20261113/critical-release-delivery.json及critical-release-*-tests.log。

### 2026-11-13 19:30 CPU定位与持续优化

- 当前目标：必要critical基线测试/validateLayering/fresh bootJar/原producer打包，在单次600秒内实际完成；不部署，不将只跑热缓存或只改配置当达标。保留16:14超时批次与全部历史失败。
- 原批次无完整连续CPU监控，不能倒推唯一瓶颈。旁观其他runtime任务Gradle112506（不同源码/缓存且非offline）：短窗整机忙64.5%，另窗idle76.7%；Agent编译期间60秒整机idle28.17%、iowait5.66%，Gradle105.11%（1.05核），最热线程54.86%，并发GC线程也有占用。此任务Agent compileJava184.827秒，不是本任务受控对照。未见CFS配额/节流，不支持“全程CPU跑满”；短时争用与阶段差异同时存在。
- 根工具提交5569fe03：只移除构建Gradle JVM的TieredStopAtLevel=1，恢复默认分层JIT；测试JVM仍C1，heap768m/workers2/原串行锁/安全及完整性/必要测试范围不变。11项builder单测通过。尚未证明实际缩时，未改生产服务或其他任务。
- 接续批次目录 `/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-03/`，plan绑定API80618640d6dd48f23ae668b59ea88778d9e57bdf/tree8d6d5104eefe4e41f0523d3b19e0298e85accb19；同原依赖/编译缓存、offline、新输出、600秒上限，准备同步CPU/线程/IO/GC采样。当前其他构建仍活跃并持/tmp/cyf-gradle.lock，未叠加或终止其工作。自己的任务ledger经transition恢复targeted_verification；deferred不可claim的拒绝记录不冒充构建失败或绕过根因锁。
- 后续边界自检发现producer仅接受旧C1 JVM精确参数：提交d8410678新增当前tiered参数的精确白名单及完整打包fixture回归；旧参数仍兼容，未接受任意JVM参数/agent或排除任务。builder11+producer46+release runner5=62通过（误用test_local_release.py时发现0项，未计入通过数，已用实际test_local_release_runner.py执行5项）。
- 本任务待执行句柄57556，驱动 `/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-03/run-when-idle.py` 正在等待已确认活跃的其他Gradle112506。驱动只在该PID/starttime退出后、原Gradle锁空闲、API完整commit与干净状态/工具commit均未漂移时启动一次systemd600秒构建；漂移或锁竞争安全退出，不自动重跑。同期监控只读、不控制生产或其他任务。当前没有03的result.json/包，不宣称构建开始、通过或达标。初版等待驱动的state比较已在实际构建前停止本任务驱动并修复为starttime比较，不涉及Gradle重试或他人进程。
- **19:51 新证据更正CPU判定**：本机元数据/ECS只读API确认`ecs.t5-lc1m4.large`、2 vCPU/8GiB、`CreditSpecification=Standard`。官方规格基线20%（约0.4 vCPU持续算力）；CloudMonitor原16:14–16:24共11点CPU均值21.1813%、积分均值0.0782且最低0.01，19:30后积分降至连续0、CPU均值约20.48%。确认云平台积分基线限制，Linux quota=-1并不能排除它。原始响应/精确窗口/规格抓取在03的cloud-cpu-diagnosis.md/json，不公开账号元数据。未修改云模式/计费/实例、未停生产/他人任务；继续等原活跃构建自然结束，再验证tiered候选，不以环境原因冒充600秒达标。
- 20:03:35原外部Gradle自然退出，待执行驱动在20:03:39启动03；systemd RuntimeMaxSec=600已核实，未抢锁。03于20:05:19结束：97.578秒，FAIL、sourceUnchanged=true，尚未评估任何项目/业务编译/测试。根因原缓存groovy-dsl/2bda...无metadata.bin。后续清点原home：438个缺metadata且没有任何文件的空脚本workspace；modules-2/files-2.1为0文件；JavaCompile build-cache-1只剩lock/gc.properties，无缓存对象。目录时间显示18:44–18:48发生过变化，但未找到删除者，不能归罪既有标准清理器（其/root/.gradle/caches与此路径不是同一inode）。原缓存保留不动；03失败和GC/CPU日志保留，不计缩时或达标。
- 两次失败均已按原编排器归因，04/root-cause-matrix.json列CPU基线/真实Agent源码变化和独立缓存损坏；既有authorize-remediation恢复本Owner，不盲重试。04准备使用独立新缓存home，从同版可信本地缓存只复制caches数据，逐文件双端SHA-256和源FD身份复核；不复制源码、build输出、测试结果、凭据/init/config，原compile-only政策仍由当前入口执行。相同Gradle内容指纹决定是否命中，不手工放置class或复用测试成功；本次缓存条件已变化，不称原条件受控A/B。
- 04恢复/验证驱动句柄65918（recover-cache-and-run.py）已确认活跃，目前等待随后另起的外部Gradle135062自然结束。恢复时取得原/tmp/cyf-gradle.lock，源home只读、独立目标、保留原损坏home；恢复后调用原local_build.py做一次600秒完整critical build/package和原监控，无自动重试/部署/计费模式调整。03执行过的原等待驱动另存driver-executed-03.py及摘要，公共实验外壳只参数化输出/cache/观察PID；没有另造Gradle或测试runner。

## 2026-11-13 20:42 接续CPU实验04结果（未达标）
04由原编排入口执行，20:29:29—20:39:27，builder 600.767秒后SIGTERM，systemd结果timeout（含终止清理606.916秒）；publishable=false，无最终包、无部署。源commit80618640d6dd48f23ae668b59ea88778d9e57bdf/tree8d6d5104eefe4e41f0523d3b19e0298e85accb19。

与本次窗口对齐的只读CloudMonitor：20:29—20:40 CPU平均20.2817%（11点，20.009—22.018%）；累积积分9个已返回点全部0，消耗积分每点0.4，预支0。与Standard/t5/20%基线吻合，确认平台CPU算力限制，而非Linux CFS计数可排除的问题。没有修改实例、计费模式或生产进程。

主图就绪JVM uptime533.917秒（原02为163.801秒，条件不同不能归为单一JIT回归）；included plugin compileJava命中FROM-CACHE仍耗112.925秒。约408秒线程快照Daemon worker正在Groovy Verifier/compileScript，不是javac；C2累计168.577 CPU秒、C1累计31.446 CPU秒，表明正常tiered在此轮有明显启动编译成本，但不可据此推算物理算力或宣称C1必然更快。GC末次GCT18.316秒、FullGC0，不能解释全部600秒。

本轮恢复5506文件/672220584字节的同版可信缓存，逐文件双端SHA及源FD校验，原损坏缓存未改；未复制fileHashes/fileContent/javaCompile分析缓存，配置脚本也有新输入。恢复等待及维护单独记录，不混入本次600秒；缓存条件改变，不作受控A/B、不把FROM-CACHE当完整达标。恢复后offline，因此此次不涉及依赖下载等待。当前JIT参数候选尚未证实收益，不能标为已验证优化。

原始证据及measurement.json：/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-04/。CPU限制、脚本/分析缓存冷启动及源文件真实变化分别记录；不盲重跑同输入、不增加workers来抢积分。后续先改善本地构建缓存复用及评估JIT启动成本；若改用已有非突发构建机，须先核实主机/工具/安全边界；涉及Unlimited、升配等费用变更须明确授权。尚未满足完整构建打包600秒目标。

## 2026-11-13 21:08 解析范围优化及05结果；06参数回测进行中

- 根938df7d9将本地afterResolve的全artifact读取收窄为OpenCV component-filtered artifactView；不按版本过滤、不lenient，保持原SHA/size/版本/来源/消费前校验/回执。builder12、static contract7通过；真实Gradle隔离fixture于39.471秒通过六项实际断言：正确包可消费且有回执；同大小篡改/版本漂移均拒绝；拒绝不替换合法回执；只看无关依赖图不强制物化缺失JAR；真正读取缺失JAR仍失败。fixture独立home、无网络依赖，不污染应用缓存，完整源码Git身份/命令/回执在05/pin-fixture/。临时将原任务绑定真实fixture commit/tree以经原编排器验证，结束后已恢复API806186/tree8d6d，无伪造应用通过。
- 05完整构建599.969秒触及600秒上限，未完成Agent compileJava，无最终JAR/包、无完整测试回执，不达标、不部署。主图就绪128.851秒，04为533.917秒；配置缓存变热与hook修改同时存在，不能将405秒差异全归于hook。63个compileJava缓存命中，多项真实未命中：Agent mapper111.868秒，economy api60.052秒、mapper4.954秒、service75.912秒；Agent service编译到依赖分析仍未完成/未存cache。结束GC累计28.839秒、FullGC0，非全部600秒主因。
- 05云监控对齐20:48—20:59：CPU平均23.051%，积分0.04—0.56、均值0.2018。不是全程零积分，但储备极小，与受限突发基线相符；04零积分结论不覆盖05每个点。所有原始响应和measurement.json保留05/。
- 另试分层扫描包索引：原/新扫描器逐字提取，独立Groovy/JDK运行，合成用例正反顺序与所有2110生产Java的42项发现完全一致；全量19.7455对19.1455秒，非受控A/B且收益小，已撤回本任务全部scanner修改。API仍干净806186，不为小收益扩大变更。证据06/scanner-identity.json、scanner-equivalence-results.json、scanner-regression.log。
- 根7fa7626c恢复原构建JVM C1-only（内存/worker保持）；完整tiered在04快照408秒时C2累计168.577CPU秒、C1累计31.446CPU秒，启动开销大且两次未达标，但不凭此宣称C1必更快。producer保留两种已用参数的精确白名单以解释历史回执。builder12+producer46通过；错误test_package_api_local.py发现0项未计数，已用正确test_api_local_package.py实际46项验证。
- 05第二次失败后已归因停在blocked_root_cause，06/root-cause-matrix.json完整列04/05根因与不同候选，才通过既有authorize-remediation恢复原Owner并执行06；未绕过原根因锁。06在21:07:24启动一次完整critical build/package，原编排器/全新输出/同owned恢复缓存/ordinary disk/offline/600秒保持。开始前Agent key934ca008b02266e5a6734e04a30fda0e不存在，必须实际编译，不以纯热缓存当达标。当前句柄70350、unit cyf-api-build-perf-20261113-06，计划21:17达到上限；未完成即不能宣称成功。

证据根：/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-05/ 和 -06/。没有升级实例、修改积分计费模式、停止生产/他人任务或部署。

## 2026-11-13 21:31 06/07结果及新增增量分析线索（仍未达标）

- 06原C1参数：主图78.070秒；Agent实际cache miss编译235.148秒完成并产生合法key934ca008b02266e5a6734e04a30fda0e（2536218字节），分层检查64.820秒、公共制品64测试17.115秒当批通过；随后Chat实际miss未完成，600.762秒停止，无包。
- 07仅根据新增Agent编译cache复用做一次有归因验证（retry-attribution.json），没有删缓存或伪造miss：Agent FROM-CACHE3.059秒，Chat仍实际miss编译275.049秒完成；主图89.868秒，分层78.097秒、公共制品64测试21.904秒当批通过。后续starter compileJava和Agent compileLocalReleaseBaselineJava都已完成javac依赖分析，但停在编译任务收尾，600.083秒触限，无最终JAR/包、认证/Agent/邮件等critical测试未完成，不达标。
- 07约395秒仅对本unitJVM抓取线程：included builds在Gradle ExclusiveCacheAccessingWorker/ArrayBlockingQueue等待；Execution worker在模块JAR Deflater。单快照不证明长期磁盘瓶颈或死锁，不归为下载慢；保留threads-chat-postcompile.txt。无C2线程，C1累计约22.864 CPU秒。
- 新线索：外部每批fresh buildDir使JavaCompile在cache miss时总是全量javac，但仍走incremental编译收尾/分析缓存。直接检查当前安装Gradle9.3.1主类字节码：CompileOptions.isIncremental为@Internal；JavaCompile的false分支performFullCompilation不经过performIncrementalCompilation。javap输出保留07/compile-options-javap.txt、java-compile-javap.txt。这可能允许只关闭一次性输出的增量分析、保留标准内容寻址JavaCompile build-cache（而不是关闭编译缓存），但尚未实施或验证，不作缩时/安全承诺。
- 下一步必须先用真实javac/注解处理器/跨全新输出缓存fixture验证开关不改变所需结果及原标准cache hit，再改本地专用init并完成根因矩阵。06/07连续失败后停止当前相同配置重试；不延长单次时限，不切付费模式。API仍806186、根7fa7626c，未部署。

证据：/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-06/measurement.json 与 -07/measurement.json。目标仍active；有新的可验证代码路径，不能标成达标或资源阻塞终局。

## 2026-11-13 21:56 最终完成：08完整流程459.918秒，实测达标

**达标范围**：同一固定API源码/工具输入的一次完整必要critical测试、validateLayering、fresh bootJar及实际五件套打包，600秒内完成；并非仅热缓存/仅编译或仅改代码。不部署、不承诺所有模块全部冷缓存都在600秒。

### 已核验的最终证据

- 批次api-build-perf-20261113-08；API commit80618640d6dd48f23ae668b59ea88778d9e57bdf/tree8d6d5104eefe4e41f0523d3b19e0298e85accb19；工具commit a6d1595415f612fb845d0eb17bf5bec0ff88263b。源码前后clean且身份一致，inputs全部工具SHA及fixtureDigest重新核对通过。
- builder总**459.918秒（7分39.918秒）**；systemd单位460.026秒；Gradle407.819秒；打包46.875秒。均为真实本地计时，不冒充Flow/生产部署。
- 当批**95测试，0失败/0错误/0跳过**。AgentRuntimeSecurityIntegrationTest、AuthFormTransportTest、SmsEmailRuntimeClasspathTest、PublicArtifactVerifier三套安全测试、POI production runtime测试均有本批全新XML；四个Test任务实际执行，不复用测试缓存。validateLayering51.840秒真实执行、bootJar86.026秒实际新建并完成原PublicArtifactVerifier。
- Agent/Chat主代码编译缓存正常复用；Starter主代码真实未命中，compileJava19.004秒完成；Agent baseline fixture compile16.128秒真实执行。本轮不是纯热编译缓存跑分，但不是所有模块冷构建基准。202任务：130执行、72缓存。
- 最终包/api/package/api.tar，251566080字节，SHA-256 **82183956552b630efc53b23b6fc2648b1734888dda70797c14f7ca12ce42d4ff**；应用JAR SHA-256 **d645a411abeb94308090dfaebc86b397dc3541cc3fcd4dcb616418b377c51832**。重新流式核对包内application.jar及外部JAR、完整包摘要均匹配；五个成员合法。四个小型包证据已按原字节存到08/final-evidence，源码/测试/bootJar proof/构建证据/日志均在包外。productionAuthorized=false、无部署。

### 关键落地与边界

- root938df7d9：OpenCV消费前pin只解析该模块artifact，不物化全图；保留版本/SHA/size/来源/回执，不lenient。真实隔离Gradle六断言通过，源码和摘要保留05/pin-fixture。
- root7fa7626c：恢复短生命周期构建的原C1-only JVM；没有扩大worker/heap，没有修改生产JVM。完整tiered试验历史保留，未把C1收益归为受控A/B。
- roota6d15954：仅本地专用init对每批fresh输出关闭JavaCompile增量分析；标准内容寻址build-cache继续用，不改项目开发构建/javac/AP输入。真实隔离三阶段fixture：原增量模式全编译42.184秒，新模式跨新输出命中39.046秒，新模式禁用缓存真实编译38.885秒；两种模式标准key一致，5个生成源码/class摘要及生成类运行结果完全一致。builder13单测通过。新API主构建日志无增量依赖分析/classpath snapshot收尾，必要fixture/javac/AP/全部基线已实际通过。
- 扫描器包索引试验对2110源码42发现完全一致但收益小，已全部撤回，未增加API改动。早先去外层gzip/一次producer结构验证/临时扫描副本去fsync的改动保留且本次完整流程已消费；正式完整性/正式产物fsync/锁不动。
- 云端T5标准模式积分基线CPU限制已由只读ECS/CMS证实；无CPU/计费/生产资源调整。较早批次缓存状态/源码/云负载不同，不将全部耗时差异归为单一代码变更。
- 依既有清理器mark-complete登记最终api.tar及真实JAR摘要，最新两批/24小时/当前和回退保护保持；没有运行全局clean。为收尾释放本任务02/04/05/06/07失败的已核验无最终制品的build临时目录，移除前所有测试/reports及小型证据已复制并SHA核对；原始日志、源码身份、回执、原缓存和其他任务不动。failed-output-cleanup.json逐批映射可追溯，最终08制品未删。

主验收清单和所有核验值：/home/isp/state/cyf-local-build/tasks/cyf-api-build-perf-20261113-08/measurement.json。目标完成，不继续相同配置重跑，不作部署或全功能业务验收声明。

## 2026-11-13 22:45 用户新增5分钟优化目标（进行中）
- 复用任务API-BUILD-PERF-20261113，Owner main_orchestrator/developer；API固定80618640/tree8d6d5104干净，现有root脏文件保持。目标完整critical测试/分层/fresh JAR/包<=300秒；原600秒单次硬上限不扩大，不部署或变更付费资源。
- 先用历史08证据诊断重打包，13.208秒（cProfile），明确不是新构建或300秒验收。逐函数计时在five-minute批次01/producer-profile.txt；原先46.875秒与本次条件不同，不直接算代码收益。
- 首个候选仅本地init：Test及最终bootJar采用doNotTrackState，减少每批不能复用的输入/输出状态快照；编译仍使用标准内容寻址缓存，测试/分层/原security action/源身份/正式摘要和刷盘不删。Groovy摘要循环改JDK DigestInputStream.transferTo，摘要算法不变。先过控制器14/producer46再真实完整构建验收，不先宣称提速。

## 2026-11-13 22:53 五分钟目标完成：完整批次141.108秒

- 新工具候选根提交`6fae56721ee1378b73fd102126a3055dd57c31f8`；API仍为干净`80618640d6dd48f23ae668b59ea88778d9e57bdf`/tree`8d6d5104eefe4e41f0523d3b19e0298e85accb19`，未改业务源码或生产JVM。
- 本次新增：仅本地release Test/bootJar `doNotTrackState`，不再为必须fresh执行的任务维护不可复用的输入/输出状态快照；保留原依赖连线、测试任务、分层检查、原bootJar archive/security动作及源身份/完整性/正式刷盘。JavaCompile仍受标准build-cache管理，不变为untracked。Groovy摘要逐块动态循环改JDK DigestInputStream.transferTo，SHA-256与原文件按Python重新核对一致。
- 实测批次`api-build-5min-20261113-02`：builder总**141.108秒**（2分21.108秒），原编排器Gradle121.519秒、lock wait0秒、打包17.391秒。95项测试0失败/0错误/0跳过；四个Test、validateLayering及bootJar均当批真实执行。日志明确Test/bootJar untracked；不是UP-TO-DATE/FROM-CACHE测试或旧JAR。
- 本次75项JavaCompile使用既有缓存，没有真实编译miss；必须标为正常复用编译缓存的完整构建，不代表全模块冷构建<=300秒。与旧459.918秒的缓存与CPU负载条件不同，不能把全部差额当成单一改动的受控A/B收益。分层25.182秒、bootJar32.823秒；不把可并行任务耗时直接求和。
- 新包251566080字节，SHA-256`9b61781d856672b7ce0d4f90deef90c2a47d601f3767e9fca02c18f03e5161ac`；新JAR SHA-256`a0c38605bc4fd121b05ae028a50e5b721cc9d8d7b125f9bca2c92ac2196df2b3`。包内5成员、外部/包内JAR摘要、工具输入SHA、95测试XML、原security proof及sourceUnchanged已全部复核。包内四JSON按原字节留在02/final-evidence，详细measurement/inputs/result/logs保留。
- 01批次0.824秒在Gradle启动前被implementing gate拒绝；通过原transition改targeted_verification后02才执行，没有绕身份/任务锁。01诊断性重打历史08包的cProfile13.208秒不算新构建。本轮仅删除已保存并SHA核对报告的本任务旧hosting01—04失败编译临时输出，以及新诊断包，原正式包、生产、备份、缓存和他人目录不动；清理635943354逻辑字节，记录01/cleanup-own-failed.json。
- 不部署、不升配、不改积分收费模式，不延长单次600秒硬上限；目标达成后不再盲重跑。工具控制器14、producer46项通过（Python3.11）；必要应用95项为本批全新结果。

证据：`/home/isp/state/cyf-local-build/tasks/cyf-api-build-5min-20261113-02/measurement.json`。

收尾：最终包已通过原清理器mark-complete登记（首次因既有锁忙安全退出，稍后原入口成功，未抢锁）；沿用24小时/最近两批/当前及回退保护。工具60项最终回执已存02/tool-tests.txt，运行说明提交81e8bddc，任务ledger已done。未改动任何无关脏文件。

## 2026-11-13 后续默认执行规范已固化
用户要求将五分钟方案纳入长期规范：根提交abe28f51358b07feeee6d0824960d24ea355b9d5，仅改根AGENTS、ops/orchestration/README、docs部署/构建策略/导航5份现有文档。规范明确300秒性能目标与600秒既有硬上限、原入口/任务验证状态、可靠缓存、fresh测试/分层/JAR、已验证优化、必要回归追加与失败归因及保留策略；不承诺冷缓存任意负载300秒。新增13链接及锚点、bash -n命令模板、源码工具与原实测SHA一致性检查通过；全局sddw检查因既有docs/sdd-document-map.json缺失退出2，未伪报全量通过。证据02/documentation-validation-20261113.json；本次纯文档，不重新构建、部署、改资源或改写历史构建成功证据。
