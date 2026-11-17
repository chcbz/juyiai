# CYF Agent 模型文件认证统一详设

核对日期：2026-11-15（Asia/Shanghai）。状态：**已按用户授权实施；Runtime1.3.114（4fd0951）已部署；773通过/0失败/10跳过，花荣/张清真实流程、吴用普通与正式议事通过；仅本次定向范围，生产新主体enrollment全流程未运行**。

任务：`RUNTIME-LEASE-SEPARATION-20261112`；Owner：`main_orchestrator`。本设计取代该任务此前“独立 credentials 目录/引用”以及“文件优先、环境回退”的同范围建议；不改其他身份、技能及业务合同。

## 1. 决策与验收目标

所有 CYF Agent 的**执行期模型认证来源只有本主体 `codexHome/auth.json`**。新建托管 Agent 由受信模板生成文件；静态 Agent 使用明确配置的自身 HOME 文件。普通 app-server 直接读取；隔离执行只从同一文件生成自身临时副本。两者不是两套凭据来源，隔离策略仍各司其职。

- 不新增服务、credentials 目录、后端接口、数据库字段或每请求密钥下发。
- 不按 Agent 名字、静态/托管类型或旧版本切换认证方式；无环境变量回退，无功能开关。
- 存量配置由**一次性离线迁移**转换，正常启动不承担旧格式升级。
- 保留现阶段模板、journal、target、public baseline 中的受控凭据副本；不是集中密钥管理、自动轮换或更强同UID安全边界方案。
- 模型凭据与图片/知识整理/语音、Runtime enrollment/安装授权、API基础设施凭据用途分开；值相同也不意味着可合并授权。
- 完成标准：新托管完整接入、重启恢复、清理后重新接入都能使用文件认证；花荣、张清真实正式议事通过；已有静态 Agent 不回归。不能用启动成功或离线单测代替业务验收。

## 2. 已核事实与基线

| 项目 | 分析基线 |
| --- | --- |
| 根仓 | `2b2abf4ec02ae050ad9f1fdc8dc9f05ab049a87f` |
| Runtime | `af9f10ab84fef01def1083ac7da817a504abc617`，1.3.113 / bridge 1.1.75；分析时源码干净 |
| API | `d6f03755ac524b7604495ed162943a5b30ec580f`，1.1.56；已有真实 native READY 承办检查 |
| Web | `2ee2349a1f727c1c712dd54b36e268075977300e`，1.16.150；本方案不修改 |
| 边界 | [RB-1](responsibility-boundaries.md)、[接口标准 v1.4](../../api/docs/interface-standard.md) |

这是已核本地/上轮安装基线，不是本轮重新核验的远端最新或线上健康。实施前复查实际 HEAD、工作区、安装记录和进程；不覆盖其他修改。

已核根因：吴用、林冲、卢俊义 HOME 有 API-key auth.json；花荣、张清无该文件，托管模板通过 `providerEnvironment` + `env_key` 向普通 app-server 注入模型 key。隔离议事主动清理环境，只复制本主体 auth.json，因而报 `TYPED_INSPECTION_AUTH_SOURCE_REQUIRED`。**没有证据证明这是外部 Agent 引擎升级导致；确定的是内部创建与执行路径不一致。**

另外三个真实缺口：托管 `publicFiles` 只有 config，清理后会丢 auth；冻结 journal/target 继续按旧模板恢复；target-only 预创建主体不一定进入已接入 subject 列表。只给两名 Agent 手工写文件不能解决新接入。

## 3. 精确数据合同

### 3.1 模板

托管 template 非 null 时，精确字段由 `profile,codexConfig,providerEnvironment` 改为：

```json
{
  "profile": { "chatEngine": "app-server" },
  "codexConfig": "由下述合同约束的完整 TOML",
  "modelAuth": { "auth_mode": "apikey", "OPENAI_API_KEY": "<仅示意，不可用占位值上线>" }
}
```

例中 profile 是片段，实际仍满足现有 profile 字段及二进制、工作区、native Provider配置要求。

- `modelAuth` 必填且仅含这两个字段；`auth_mode` 固定字符串 `apikey`；key 非空、无首尾空白及控制字符，不猜供应商品牌前缀，不改变值。
- 不接收 null、数组、OAuth tokens、其他认证模式、任意额外密钥字段。当前盘点的五名 Agent 均为此模式；未来 OAuth 是另行明确的合同变更，不在本轮暗加兼容。
- `template:null` 仍允许静态-only host；adopted static subject 的 template 必须保持 null。
- `providerEnvironment` 在托管模板中彻底退役；出现时明确拒绝，不静默忽略、不转换。外层 configVersion=1、journal formatVersion=2、target formatVersion=1 保留：本次替换部署合同，不引入并行版本解析。
- 凭据不进入 profile、manifest、API注册/报价/READY载荷、错误正文或公共回执。
- 文件序列化为固定字段顺序的 `JSON.stringify({auth_mode:'apikey',OPENAI_API_KEY:key}) + '\n'`。新托管/迁移/cleanup 使用同一序列化函数；静态既有合法JSON不因缩进不同必须重写。

### 3.2 TOML 与 Provider 绑定

托管 parser 保留现有小型严格 TOML 子集，不引入第二套完整 TOML 库。**不增加 `preferred_auth_method`**：复核发现组件示例明确标其在曾审计0.153.4中无效，而隔离生成器仍写该字段，不能把内部旧输出当成引擎有效合同。统一删除该旧输出并以实际执行binary的配置readback验证。top增加 `cli_auth_credentials_store="file"`，要求明确文件存储，不允许keyring/auto；该字段在本机实际执行binary上的支持与生效必须在最早探针核实，不因当前在线文档或其他安装版本支持就当已验证。Provider 移除 `env_key`，要求 `requires_openai_auth=true`、`wire_api="responses"`。保留单 Provider、HTTPS、无 URL userinfo/query/fragment、无 headers/include/外部认证命令的边界。

```toml
model = "<保留原授权模型>"
model_provider = "managed"
cli_auth_credentials_store = "file"
[model_providers.managed]
name = "managed"
base_url = "https://provider.example/v1"
wire_api = "responses"
requires_openai_auth = true
```

此 URL 仅示例，迁移不得改变真实目的地。`model_reasoning_effort`、`disable_response_storage` 按既有配置保留。模板普通 Provider id/base_url/wire 必须与 nativeExecutionProviderId/BaseUrl/WireApi 一致，避免同一 key 被送往未授权的另一目的地；比较配置中的明确值，不通过网络猜测。沿现有 `requireHostingDeliberationTemplate` 完成该配置责任，不在API复制。

静态配置沿既有合法解析/`canShareChatProvider`核对选中的 Provider，不把托管精简 parser 强加到含其他正常设置的静态完整 config。必须满足相同文件认证语义，不含选中 Provider 的 env_key/认证替代通道。原 native→typedInspection 字段适配非凭据回退，不在本轮重构；已有静态显式绑定不得改目的地。

### 3.3 文件与失败语义

复用 bridge 文件处理边界，提取一个小型 `model-auth.mjs` 纯合同/安全读取 helper（不是新服务或框架），由托管模板、普通启动、隔离stage和cleanup调用：

- 源文件位于已绑定主体 HOME；父目录继承现有私有根校验；最终文件 `open(O_RDONLY|O_NOFOLLOW|O_NONBLOCK)` 后 fstat，要求 regular、同运行UID、无group/world权限。不以 existsSync 判定安全，dangling symlink 也失败。
- 同一打开的fd完成读取/JSON验证；隔离复制使用所验证的字节，不在验证后重新按路径读取。不能从其他 Agent HOME、宿主登录HOME、环境或模板临时取值救场。
- 新文件0600，目录0700；原子写、fsync文件及父目录，拒绝覆盖不匹配的已有文件。所有错误只含类型和非秘密上下文，不拼 key、JSON正文或env dump。
- 内部统一错误码：`MODEL_AUTH_REQUIRED`（缺失）、`MODEL_AUTH_UNSAFE`（链接/属主/权限/类型）、`MODEL_AUTH_INVALID`（JSON/字段/模式）。模板形状错沿 `HOSTING_TEMPLATE_INVALID`；已存在材料与冻结模板冲突沿 `HOSTING_STATE_UNCONFIRMED`。
- 原生边界可保留既有对外 readiness 分类和稳定失败载荷，内部cause采用统一码；不是恢复旧认证路径。无效源不得伪报READY；错误限制到现有主体/能力失败域，不另造全主机业务阻断。
- 普通每次新建引擎和隔离每次stage校验，warm复用不逐消息重写auth、不新增模型调用探针。删除/改动源文件后的新引擎必须失败；已初始化进程的凭据驻留不等于支持热轮换。

## 4. 生命周期与并发

### 4.1 新建/预创建托管

受信operator模板验证 → 现有锁内冻结target/journal → 创建独立HOME → 生成 config.toml + auth.json → 两文件检查通过 → 后续prepare/materialize/enroll/执行。请求不得提供 key、HOME或模板覆盖。

两文件不能假称跨文件原子：在既有主体门闩内完成，二者完成前禁止启动/返回配置就绪。中途崩溃后，只能从同一冻结模板补齐缺失文件；存在且字节相同则成功，冲突失败不覆盖。文件创建避免半写暴露（私有同目录临时文件完整写入后，以不覆盖现有目标的发布方式安装，清理本次临时文件）；不可用rename无条件覆盖来替代冲突检查。

`subjectAgent` 不再带模型 `providerEnvironment`；同时产生可信 `publicFiles={config.toml,auth.json}`，auth由冻结modelAuth序列化。target、INITIAL、重启materialize、readmission共用同一实现。

### 4.2 普通执行

本主体HOME文件 → 统一验证 → app-server；`HOME`/`CODEX_HOME`仍明确绑定本主体。`buildRuntimeExecutionEnvironment` 删除 `CYF_MANAGED_PROVIDER_*` 注入，不继承宿主 OPENAI_API_KEY 等模型秘密。binary probe、CLI、tool adapter、普通app-server及warm restore的环境构造调用都沿原白名单，不能留旁路。

`makeEntry` 去掉 `agent.providerEnvironment` 回退，但保留 `providerEnvironments` 中图片等技能配置及其现有授权消费者。不能删除整张map。普通源auth文件持久保留，不在initialize后删除。

### 4.3 隔离执行

同主体源auth → request/conversation私有HOME副本0600 → 生成file-auth配置 → 既有沙箱spawn → initialize/既有测量 → seal只删除临时副本 → 多轮复用。初始化失败也清理临时凭据；不得删除主体源文件。保留沙箱网络、CA、身份及进程可见性检查。

typed inspection、无LOCAL_FILE warm chat及native execution均采用该复制合同。恢复新进程重新从主体源生成私有副本；不中途从环境补齐。初始化后凭据能否持续支持真实多轮及恢复必须实测，不以 account/read 或一次initialize当证明。

### 4.4 移除、清理与重新接入

保持既有停止、成果/知识整理、费用flush、state退役、materials清理、HOME清理顺序。cleanup在任何删除前验证可信baseline同时含合法config/auth；缺auth不能再解释为“环境提供凭据”。

清除旧owner会话/缓存/身份状态后，由可信operator baseline重建config/auth。这里“publicFiles”是可保留的operator配置，不是匿名公开或跨owner个人凭据。**不得从旧owner可写HOME提取secret作为新baseline。**静态publicFilesPath仍核对tenant/client/agent精确身份；无授权baseline时阻止该清理流程并报告，不从其他Agent补齐。

不改变enrollment、installation、租约或会话代际规则；不自动接管历史主体，不因模型认证修复重新收费。

## 5. 文件级实施清单

源码路径相对 `/home/isp/wsps/cyf/runtime/`；实际实施遵守该仓AGENTS和根规则。

| 文件/入口 | 必改内容 |
| --- | --- |
| `conf/codex-bridge/model-auth.mjs`（新增小helper） | JSON合同、确定性序列化、安全读取；不含业务状态机 |
| `conf/cyf-agent-runtime-v1/lib/hosting-config.mjs` | template新schema、file-auth TOML、Provider一致性；移除旧模型env validator |
| `conf/cyf-agent-runtime-v1/lib/hosting-control.mjs` | subjectAgent/publicFiles、两文件materialize、target与journal共同验证；移除无auth旧注释 |
| `conf/cyf-agent-runtime-v1/lib/private-home-cleanup.mjs` | 删除前要求合法config/auth baseline；不改费用/退役顺序 |
| `conf/codex-bridge/agent-client.mjs` | 去模型env注入及agent fallback；普通启动使用共同auth验证；保留技能map |
| `conf/codex-bridge/isolated-engine-profile.mjs` | stage复制复用共同读取；保留隔离与seal |
| `typed-inspection-profile.mjs`、`native-execution-runtime.mjs`、`app-server-adapter.mjs`（bridge目录） | 核对所有spawn/restore调用；有共同入口覆盖则不机械重写；验证仍通过真实initialize/测量；退役无效preferred_auth_method输出，核验file存储readback |
| `conf/codex-bridge/skill-inventory.mjs` | 补核独立catalogOnly spawn：原HOME=dirname(codexHome)，不能当普通host wrapper已覆盖；明确HOME/CODEX_HOME，不额外要求无模型调用的目录发现通过付费认证 |
| `conf/cyf-agent-runtime-v1/agent-runtime.mjs`、`lib/security.mjs` | 文件key及动态新托管key脱敏覆盖；现有knownSecrets只来自技能map/knowledge配置，不能依赖它们恰好与模型key同值 |
| `conf/cyf-agent-runtime-v1/lib/security.mjs`、`execution-adapter.mjs` | 核对静态baseline读取与cleanup传递；仅补实际绕过点 |
| `conf/cyf-agent-runtime-v1/hosting-control.example.json`、该组件`HOSTING-CONTROL.md`、Runtime/bridge README | 改为文件认证、明确模板含secret及权限；同步所有有执行意义的fixture |
| Runtime/bridge package版本及lock自身版本 | 固定新候选，预计1.3.114/1.1.76；实施时先核对无其他候选占用 |

模型密钥读取不能新增未脱敏日志；检查新helper的异常、hosting错误转发及引擎stderr处理，模拟哨兵secret断言所有捕获日志/注册/回执不含原值。仅mask首尾不够，禁止输出secret摘要作为公开标识。

## 6. 一次性迁移（随同版本受控安装）

### 6.1 全集合与转换规则

不只循环活动Agent。离线列举并绑定：

1. `/home/isp/conf/cyf-agent-runtime-v1/unified.hosting.json` 的future模板。
2. `/home/isp/state/cyf-agent-runtime-v1-managed/unified/hosting-journal.json` 所有非null subject.template。
3. 同目录全部符合target身份规则的 `target-*.json`，包括target-only记录。
4. 上述主体已物化HOME/config、auth，以及受影响operator public baselines；静态五名范围中实际三名静态文件只核验，合法的不重写。
5. journal里未知/历史subject只转换冻结配置以满足整体解析；不创建原来不存在的运行目录、不启动/重新enroll。发现不能解释的文件关系先停止迁移，不猜活跃身份。

每份旧template根据其自身选中Provider.env_key取自身providerEnvironment值，生成modelAuth；去env_key、设置file-auth属性。**不因为盘点K01相同就从某个全局key覆盖所有主体。**多余未被消费的env字段须查清用途：不能证明属于本次模型旧通路则阻止自动转换、保留原值待定向处理，不默默删除技能secret。

新schema已存在且语义正确：幂等验证并跳过；两种字段混用、HOME不同key、目标冲突、链接/权限异常均失败，不能用“迁移”覆盖冲突。静态及其他服务密钥、Provider地址/模型/native超时不变。

基线代码的opKey来自tenant/client/operationId，manifest摘要来自manifest；operation.candidate不含template。迁移只改上述认证字段及对应config，不重算operation/manifest/enrollment摘要，不改generation、activeOperationKey、readmission、费用、ACK、outbox或完成事实。以结构化allowlist比对证明其余值相等；若实际候选结构变化，重新分析而非套用旧脚本。

### 6.2 顺序、CAS与恢复

沿原安装器增加本批迁移步骤，不新建常驻runner或第二套任务ledger。迁移提供plan/apply/verify行为，旧schema只存在于该一次性工具，运行时代码不读取旧格式。

1. 先实现和测过转换、故障恢复；固定候选commit/tree，生成本地包及SHA/测试证据。plan读取不输出secret；只报告身份、字段名、权限、将改变的文件。
2. 安装前重新核对当前版本、配置输入、授权、锁及在途操作。复用原发布锁，停止本任务目标Runtime及其精确所属writer；等待/协调未知外部副作用，不杀其他任务。
3. 停写后形成最终输入CAS与完整私有备份（含权限/属主/旧程序恢复信息），记录本次新增文件清单。秘密文件摘要若为CAS所需，仅存私有恢复材料，不进入公开日志/报告。
4. 在非生产安装目录生成完整新配置集，使用新validator校验future/journal/targets及相互关系；先校验全部，再执行受控逐文件原子替换，记录已替换集合；进程仍保持停止，避免半新半旧被读取。
5. 安装新固定app程序与全部配置，readback校验白名单差异、权限、身份和摘要后才启动；不在生产app编译。之前安装脚本里的 `amend-managed-config.py` 不可再次盲用，它不是本次迁移工具。
6. 启动核对实际release record、PID、命令、通道、native readiness；然后执行业务验收。不重新提交684，不把准备中的685当已收费事项。

**失败恢复：**启动前任一步失败，在停止状态恢复本次已改文件、程序并删除仅本批新建的auth/临时文件，验证前值后启动旧候选。进程已启动但无新业务时先停目标writer，再按相同规则恢复。发生新的业务/会话事实后不得恢复整个state备份：先核对事实兼容，优先前向修复；需要回退时仅恢复程序及认证配置，不能回滚费用、租约、ACK、会话和完成记录。无法证明兼容则保持不可用并报告，不自动重放。

本次恢复旧候选是受控整批回退，不是新版本运行时双轨认证。备份受原保留策略保护，不自行删除。

## 7. 回归矩阵与可观察结果

全部初始状态为**待执行**，每项绑定新commit/tree、fixture、selector、日志；原593测试不自动继承为新候选通过。

| ID | 场景/入口 | 必须观察到 |
| --- | --- | --- |
| A01 | helper/hosting-config | 新schema正例；缺key、tokens、旧providerEnvironment/env_key、冲突Provider拒绝；错误无secret |
| A02 | 真实文件helper | 缺失、dangling symlink、目录、错误UID/权限、损坏JSON拒绝；合法源只读不改 |
| A03 | hosting-control完整prepareTarget→prepare→materialize | 新主体自动有两文件；没有测试手工补auth；并发重复/中断恢复无覆盖、只原一次enroll |
| A04 | hosting-lifecycle/restart | 冻结模板恢复正确；future模板变化不覆盖已有主体；target-only也能继续 |
| A05 | private-home-cleanup/readmission | 清理前baseline检查，旧会话删掉而operator auth恢复；重新接入无环境依赖；静态adoption保持null模板 |
| A06 | runtime-host/agent-client | 普通/CLI/tool/warm实际spawn环境不含模型key；图片等技能map仍按原授权可用 |
| A07 | isolated/typed/native profile | 同一主体源复制；源不删、临时seal；初始化失败也清临时；不同主体不串key/HOME |
| A08 | migration | future+journal+全部target+物化HOME；历史不激活；幂等、CAS冲突、部分写失败恢复、权限、身份/operation零漂移 |
| A09 | 固定真实binary隔离探针 | 真实initialize/沙箱/seal，不用mock冒充；无模型调用探针与真实Provider回合证据分开 |
| A10 | 新托管完整集成 | 使用实际模板物化后真实引擎认证，随后两轮及重启恢复；不能只用预置auth fixture |
| A11 | 花荣UI | 685先核对归属/未预占→明确选择→确认一次→自动进原议事→A/B两轮→刷新/恢复→取消释放 |
| A12 | 张清UI | 新自有事项，同样两轮及恢复→明确选版验收→只结算一次，检查余额/预占/账本 |
| A13 | 吴用/林冲/卢俊义影响 | 三者文件/Provider/native测量；吴用真实普通密议与正式议事代表回归；其余若未跑真实回合明确NOT_RUN |
| A14 | 日志/负向业务 | 哨兵secret不出日志/注册/回执；无auth主体不可承办，无扣费后失败；不能用通道ready替代native READY |

优先扩展现有测试：Runtime的 `hosting-config.test.mjs`、`hosting-control.test.mjs`、`hosting-lifecycle.test.mjs`、`hosting-readmission-integration.test.mjs`、`hosting-adoption.test.mjs`、`private-home-cleanup.test.mjs`、`runtime-host.test.mjs`、`provider-environments.test.mjs`；bridge的 `native-execution-profile.test.mjs`、`typed-inspection-profile.test.mjs`、`native-readiness.test.mjs`、`managed-chat-scope-config.test.mjs`、`agent-client.test.mjs`、`materials-chat.test.mjs`。新增helper测试仅测集中责任；公共fixture `hosting-fixture.mjs` 同步新schema。所有受同一fixture影响的hosting suites列入最终selector；不存在的文件名在计划阶段纠正，不能以不存在selector记通过。

真实探针沿已有 `CYF_NATIVE_EXECUTION_ISOLATION_PROBE=1` 入口核对其具体覆盖，未调用Provider不得报“模型对话通过”。新托管真实租费/回合计入原100文预算，当前摘要已用22文，实施前重查账本；不自行提高预算或创建他人主体。若需额外主体才能覆盖A10且现有授权不含该操作，先用隔离集成完成技术验证并明确真实接入未验，不假造生产验收。

真实UI沿[全局手册](../juyiting-unified-experience/global-regression.md)记录原用例结果；目前活动37PASS/2FAIL/80NOT_RUN仅历史活动状态，必须有新证据才更新对应项，不宣称119项全部通过。原684只按原意图自然恢复，不代取消/验收/重新交办。

## 8. 构建、发布与交付顺序

1. 先最小红灯测试暴露新建、清理及恢复缺口，再共同helper/schema/materialization/env收口；同一候选补完fixture、迁移、文档。
2. 定向测试通过后锁定Runtime commit/tree、版本、工具链、依赖；复用本任务原本地Runtime构建入口，扩充credential/hosting selectors，不只复跑原15组。记录fresh结果、skip理由、构建输出与制品SHA。
3. 单次必要测试/构建/打包及锁等待≤600秒；异常保留日志、归因后重试从零计时；不通过拆批重置同一次构建时钟。不用tmpfs、不启动Flow、不修改生产JVM；安装/备份和业务回归另记实际时间。
4. 本轮仅发布Runtime；API/Web合同无变化，不为凑全链重建部署。既有API readiness逻辑保留；若真实验证发现另一个契约缺陷，先记录再决定实际最小联动，不假设必须修改三端。
5. 按§6迁移/安装，逐个确认五名Agent能力，再做A10–A14。失败项归因修复，不标为通过；不能用部署成功替代业务完成。
6. 最终回执包含：新版本与完整commit/tree、测试selector/计数、制品/安装摘要、迁移文件数与身份不变量、恢复点、实际健康、事项/会话/资金证据、真实未测项、全局用例更新。原失败保留。

部署工具复用位置（实施前重新读取）：
`/home/isp/state/cyf-runtime-lease-separation-20261112/task-ui-20261113-224052/cup-deploy-20261115/` 下 `build-runtime.py`、`prepare-local-runtime.py`、`install-runtime.py`。新批固定自己的版本/源/输出/前代及迁移步骤，不能改写旧证据。程序目标保持 `/home/isp/apps/cyf-agent-runtime-v1/app/`。

## 9. 风险、未验证点与结束条件

- 当前最小方案仍在私有模板/快照/HOME保留secret副本，普通app-server仍可读取自身持久文件；不声称具有集中轮换、不同Linux UID级秘密隔离能力。
- 当前盘点模型key与若干技能/语音实际值相同，但供应商账户授权未核。迁移保留原用途/目的地，不顺便轮换或取消其他消费者。
- seal后真实多轮、重启恢复、实际引擎对file-auth配置的表现，以固定本机binary实测为准；这是必须执行的验收，不是已被文档证明。
- 新模板合同替换与磁盘迁移必须同批，错配会使journal整体解析失败；离线全集合校验和失败恢复测试是必要条件，不以“主角两名成功”豁免。
- 不承诺“一小时必完”或“一次开发绝无返工”。本设计的作用是把已知调用链、数据、迁移、失败域、测试和验收一次明确，避免遗漏导致反复补丁。**只有实现、迁移、安装及上述必要验证全部有证据后，才可报告完成。**

证据/实现状态沿[原任务handoff](../../docs/implementation/handoffs/RUNTIME-LEASE-SEPARATION-20261112.md)维护；不另建任务或审批系统。


## 10. 二次复核修订与未关闭风险（2026-11-15）

**本节纠正初版详设的完整性判断；以下发现已写入实施范围，但未通过修改与实测关闭。**

### 10.1 引擎配置与实际执行版本（必须先验）

- 已确认源码存在冲突：`codex-home.example.toml`说明旧审计版不支持preferred_auth_method，`isolated-engine-profile.mjs`却仍生成它。初版详设沿用该字段不严谨，§3.2现已纠正；这不证明它是花荣缺auth的根因。
- 本轮只读 `/usr/local/bin/codex --version` 返回0.167.0，静态profile指向该路径；现有契约fixture名却为0.153.4。**CLI路径当前版本、contract fixture版本、已运行app-server的测量快照可能不同。**未核实实际进程可执行文件摘要前不得声称引擎已升级或任一版本已完整兼容。
- 最早验证先绑定wrapper、实际二进制、schema测量、运行snapshot完整摘要与版本；核实config/read的有效值及配置警告，不能只看解析不报错（未知字段可能被忽略）。禁止为绕过不兼容临时自动更新引擎或重命名fixture。
- 在独立私有测试HOME、假key和不可达的本机测试Provider下验证文件认证选择，不使用/root登录HOME、不调用真实模型、不启动生产会话。真实Provider多轮另按预算验证。若file存储配置不支持或不能证明无外部凭据回退，先修正设计并说明证据，不继续部署猜测方案。

### 10.2 额外启动入口及配置优先级（代码边界已确认，行为待测）

- `observeInstalledSkillInventory`独立调用AppServerAdapter并覆盖HOME为主体HOME的父目录；初版只列普通/CLI/tool/warm不足。应显式绑定主体HOME/CODEX_HOME，加入catalogOnly实际spawn断言。目录发现不等于执行模型请求，不应因为统一认证给纯目录读取新增收费或不相关认证阻断。
- 普通默认AppServerAdapter会引用宿主HOME，CYF已包装路径和未包装路径必须分别断言。修复放在CYF责任入口或适配器中明确的CYF上下文，不修改其他项目的Codex全局行为。
- 需覆盖工作目录项目配置、命令行覆盖、系统凭据存储对有效Provider/认证设置的影响：以引擎实际config/read为准。不得因主体config.toml正确就断言所有最终设置正确；也不为此禁用所有合法项目设置。普通与隔离分别验证file存储、Provider绑定、无env_key及无认证替代渠道。

### 10.3 脱敏与凭据摘要（代码边界已确认）

- `agent-runtime.mjs`当前knownSecrets列表来自providerEnvironments与knowledgeConfig；新modelAuth/静态auth的独立key未必包含其中。`security.mjs`的字段名脱敏不能保护任意message字符串里的key。真实K01共享值可能掩盖问题，所以测试必须使用互不相同的模型/图片/知识整理哨兵key，并覆盖运行后新增托管主体。
- 实施在现有logger/凭据读取边界加入内存脱敏值登记，不落盘、不写摘要、不另建密钥管理服务；动态创建在任何可能转发异常前登记。异常优先输出稳定代码，不原样传播Provider正文。不得在整个进程环境搜集所有秘密来凑覆盖。
- `typed-inspection-profile.mjs`的nativeProbe目前含authSourceDigest。尚未证明它已外泄，但不能宣称“代码完全没有凭据摘要”。新方案移除不承担授权/隔离职责的凭据内容摘要及其测量输出，保留非秘密配置/可执行文件/隔离证据摘要。检查实际消费者及序列化边界，不盲改冻结attestation/历史记录。

### 10.4 普通持久HOME的威胁边界（明确接受，不伪称修复）

fd校验可以保证本次读取的是已验证文件，但普通引擎随后自行按路径读取仍有时间窗口；同UID可写HOME不能靠一次检查变成强隔离。本轮不承诺抵御同UID恶意替换、不承诺源key对普通工具绝对不可见。保留已有工具/目录访问限制；如果业务要求达到隔离议事同等“模型阶段文件不可见”，这将改变最小方案，须重新设计，不能用现有方案冒称满足。

### 10.5 补充必执行测试

| ID | 输入 | 验收 |
| --- | --- | --- |
| A15 | 实际受测/部署binary及独立HOME | 明确file-store有效；旧preferred字段不再生成；config/read与固定摘要绑定，fixture不冒充运行版本 |
| A16 | catalogOnly、默认/包装spawn与冲突项目配置 | 不继承宿主HOME/凭据，不因项目覆盖绕过认证合同；纯目录发现不增加模型请求 |
| A17 | 不同哨兵key、动态创建主体、message错误、完整measurement序列化 | 日志/注册/对外回执无key及凭据内容摘要；图片等技能仍独立可用 |
| A18 | 迁移后真实两轮、主动结束测试进程后恢复原测试会话 | seal后第二轮成功；新进程从主体文件重新初始化；无重复业务意图/扣费，源auth保留 |

以上18项为测试设计，不是18项已通过。静态检查、未付费binary探针、真实Provider回合及生产UI验收分别记证据。官方在线认证资料本轮工具检索未返回可用正文，未作为字段生效证明；以固定本机引擎的测量和实测关闭，不凭记忆推断。


## 11. 固定本机引擎离线验证结果（2026-11-15 19:19–19:21）

本节更新§10的部分待验结论，**不代表生产执行快照或真实Provider回归通过**。

- 实际二进制：`/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`，0.167.0，SHA-256 `cdcb45aaa01d0f14e298985e09465aebccd47f64ecd298aea44814af7b62bbda`。
- 在独立0700 HOME、清理后的环境及 `unshare --net` 无外网namespace执行，不读真实密钥、不调用模型、不修改生产。严格配置探针：file-store配置exit0；preferred_auth_method明确报unknown configuration field、exit1。因此本机候选应删除该旧字段，不是仅凭旧示例推测。
- 独立app-server initialize后实际config/read返回 `cli_auth_credentials_store=file`，选中probe Provider的requires_openai_auth=true、env_key=null，其他认证替代字段为空。假key auth.json的account/read识别apiKey；删除该临时auth后，同一进程account/read仍识别apiKey。只证明该引擎的配置生效和已初始化认证状态保持，不证明真实第二轮请求成功。
- 测试进程已按精确子进程句柄退出，临时假key文件已删除。证据在 `/home/isp/state/cyf-runtime-lease-separation-20261112/task-ui-20261113-224052/model-auth-design-verification/` 的config-probe.py、result.json、readback-probe.py、readback.json。最初定位binary时使用旧目录结构导致StopIteration，改为实际bin/codex后执行；该定位错误不属于产品测试失败或通过。
- 当前安装record的rollbackPolicy为forward-only。§6恢复算法仅是待实现工具的能力设计，实际发布不得据此越过既有forward-only约束；未获允许时失败保持停机/前向修复，不自动恢复旧候选。启动前撤销尚未生效的文件写入也须由现有安装器明确支持，不能默认已具备。

**仍未关闭：**生产当前app-server快照与上述binary的对应、新实现后的全消费者集成、迁移故障恢复、真实seal后两轮/重启恢复、花荣张清及新接入UI与费用闭环。现在可以按本详设组织同一候选的完整开发与测试；这些是交付必须完成的验证，不得省略后直接部署或宣称一次必成。

### 安装验收补充（2026-11-15，4fd0951实测）

静态 inputCarriers 的真实认证必须绑定最终固定 app 路径。现有 toolchainDigest 包括 sourcePath/imageRoot；在暂存目录生成的证明不能直接随候选搬迁后充当有效证据。此次暂存证明在暂存路径自检通过，但上线后吴用正式议事687出现 TYPED_INSPECTION_CARRIER_EVIDENCE_INVALID；实际复测吴用、林冲的原生证明仅 toolchainDigest 变化，并连带 engine/toolPolicyDigest 改变。保留失败，不能改写摘要冒充认证。

收尾采用最终目录下分别重新执行9图+文件真实模型认证、完整证据读取与 contractReady 自检，持既有发布锁更新两 profile 的证据引用并受控重启，再跑正式议事；不修改产品源码、不重建、不降低完整性校验。不再把候选目录的载体认证当作最终线上认证。新建托管 synthetic materialization 技术探针不等于生产 enrollment/计费完整接入验证，后者仍明确未运行。

最终状态（2026-11-15 21:39）：正式路径载体证据更新后静态688复测成功，最终PID873209的5主体通道就绪；685取消、686只选B验收、688取消与资金唯一性均已核对。详见原任务handoff及其B/model-auth-implementation/verification-summary.json。此前687载体证据失败及其他构建超时保持原记录，不以本次成功抹除。
