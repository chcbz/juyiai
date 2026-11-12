# 真实 CHECK catalog 与原生引擎兼容推进（2026-10-01）

本记录继续完整用户目标，不替代工作空间/多媒体/双接应/正式验收与版本发布。最新源码 pin 仍以 `integration.yaml` 为准；未验证候选不得提升。运行状态只在主工作区 TASKS.yaml 的 runtime_ledger_json。

## 1. 真实数据库观察已取得，原失败保留

API 组合基线 `642e73238edde3354a8b23654e561a496a2691f3` / tree `b529963ae8ece8f916917e998cd25db9c7fd77f6` 的原 V3 测试仍是34通过/3真实MySQL失败，后续未运行，不因诊断取得资料改成通过。

同一真实 Source Owner 的隔离诊断，先后出现 Python3.6 subprocess 关键字、MySQL列头及函数切片错误；这些停止记录保留，未盲目重试相同输入。Stage5改为完整控制流 mock 自检后执行新的单次候选：

- 实际 MySQL8.0.21、UUID/datadir身份匹配；事前 schema 不存在；CREATE成功后才取得 ownership。
- 来源精确抽取的25条SQL全部实际 exit0，包含原23条及两张后续表的精确CREATE；没有手抄或弱化原CHECK。
- 四张表的 SHOW CREATE 与 tables/checks/columns/indexes 原始catalog已经捕获。
- 原Stage5 receipt **仍是FAILED**：最后汇总以小写 `table_name` 读取真实大写列头 `TABLE_NAME`，产生KeyError。这是汇总脚本错误，不是25条DDL执行失败。
- cleanup实际PASS：只删除本次已ACK的私有schema，前后identity匹配并确认该schema消失。

Main随后仅对冻结raw TSV/JSON做离线读回：按真实header构造小写键别名、保持所有值/谓词不变；逐行raw与JSON相符，四种catalog都覆盖四表，得到 **4表、27个ENFORCED=YES CHECK、136列、89索引行**。没有再次执行DDL，没有把原FAILED receipt覆盖为PASS。

该观察允许 Source Owner 基于真实CHECK rendering修复限定initializer及测试两条路径；不能去掉所有括号、放宽predicate、接受same-name弱CHECK或重写共享canonicalizer。Source Owner 已提交精确 child `354f736a09b0e89d52306616245ba86e16897d85` / tree `15b9015a5734d7d46899788c904659c73535852b`，parent 为原 `642e732`。只改 `ControlledImageFollowupV3SchemaInitializer.java` 及对应测试；三条 catalog literal 与真实观察逐字匹配，原SQL、legacy修复和共享canonicalizer保持不变。新增测试覆盖14个owned CHECK及弱化/TRUE/extra/missing/unenforced拒绝。

Owner静态自检和Main独立路径/摘要/literal核对通过，**仅接受为新的验证输入**，不是正式JUnit通过或产品接受。新验证Owner已经实际READY、绑定唯一ledger并获GO，按完整正常图V3→V2→typed 11类/真实MySQL串行验证；最终fresh XML结果尚待返回。原34通过/3MySQL失败不改写；feature及integration pin仍保持已接受 `87c0acc`。

## 2. Client原生协议兼容是实际阻断项

当前已接受Client `2f6907274ea5395980df0643c6b3898fa522a54f` 的适配器固定CLI0.153.4/schema `b06f77062369d481a59cc70720c12b89cb9dd49c385863923262102d3ad6c978`。

本机全局launcher的优先嵌套native实际为CLI **0.159.2**，binary SHA-256 `1748767b230ebfc3d4ab7e4e254920d0c0ad9691fd8c11f190e7d44511a4a92e`。在清空环境、独立HOME/CODEX_HOME下生成的完整schema bundle SHA-256为 `7243ba241962af92ca60581f1a81808ebda4212a800f8b205f54703bcfd508c5`；这不是兄弟包0.156.0的结果。

对**未修改的真实Client public measurement方法**使用显式私有snapshot/schema根实测，得到 `APP_SERVER_BINARY_UNTRUSTED / CODEX_APP_SERVER_SNAPSHOT_FAILED:APP_SERVER_BINARY_UNTRUSTED`，childCalls=0、私有snapshot清理完成，未启动app-server/模型/Provider。旧包装先取error.code，掩盖具体内部错误；不能把该结果误写成已经隔离证明的 VERSION_MISMATCH。

另按现源码同序枚举实际资源：40个regular文件共78101808 bytes，明确超过旧64MiB硬上限；这是确定存在的拒绝条件。长期修复不回退全局CLI，也不把上限随意调大：按实测登记版本化schema，移除无依据count/size硬拒绝，保留资源清单/摘要/身份/私有复制/符号链接及真实错误处理，且保留具体cause。旧0.153.4合同及所有既有wire保持不变；新合同由本地profile显式选择，未知版本/schema仍拒绝，不自动换Provider或模型。

准备工作树与源包合同已存在，但本轮真实spawn被thread limit拒绝，**没有新Client Owner、没有开始实现**。唯一ledger新增等待条目准确记录此事实；不修改max_threads、不抢占其他Agent。完成当前已拥有的verification工作、关闭其已完成Owner后再领取。

只读进一步发现 `juyiting-typed-outcome.mjs` 的 readiness 仍硬匹配旧CLI/schema；仅修adapter测量会使新原生版本永远UNAVAILABLE。已新增不可变源包补充v1.1（原合同保留），最小写集增加该模块及其runtime测试：readiness、声明和runFastChat必须核对**本地profile显式选定**的registered exact合同与真实已测量、已初始化且未关闭adapter，不允许“任一已登记版本/仅measured=true”通过。typed schema1、输出union、sidecar、既有golden wires均不变。新版本兼容仍未开始实施。

## 3. INSPECT及严格无工具能力不能伪报

0.159.2本地schema包含text/localImage/localAudio输入，不包含通用本地文件输入；schema可用不证明模型理解或source物化已经实现。当前Client `runReadOnlyInspection`仍明确NOT_ENABLED，typed v1仅NONE/AVAILABLE。后续须实现独立受权input-only materializer、精确来源/字节摘要和真正输入adapter；普通文件按实际解析器能力处理，不能靠文件名回答。

本轮离线features实测shell_tool默认true；显式关闭该项确实变为false，但其它工具相关feature仍存在。该结果不是“严格无工具”证明。现有read-only-constrained声明继续如实保留；不能用空dynamicTools、只读sandbox、approval=never或单个feature关闭推导strictNoToolsVerified=true。

讨论仍以冻结 `interactions/discussion` typed v1及回执v1.1为准，EXECUTE保持独立v3；不实现早期schema-3讨论候选，不增加第二套问题状态机。

## 4. 发布前仍须完成

新API精确child相关正常图测试通过后才提升feature/pin；Client原生引擎兼容与真实INSPECT、多轮来源和完整媒体、双接应、真实登录/正式交付/验收/完成仍按原范围推进。当前loopback10018实际连接拒绝，已向canonical Runtime协调入口发alert-only，Main未重启foreign服务；旧健康记录不作为当前UP证据。

尚无本特性develop合入、冻结release、生产制品/部署或产品验收。不能发送“可以验收”的通知。所有上述原始回执与离线派生见[便携manifest](integration-evidence-20260928/catalog-and-native-runtime-progress-20261001/portable-manifest.json)。

## 2026-10-01 后续源码与真实环境收口（本节优先于上文同日历史状态）

完整正常图对 `354f736` 实际执行到Agent V3：**38项、37通过、1真实MySQL重启失败，0error/skip，9份fresh XML**。此前V3直接catalog问题已经收口；剩余失败是旧provider-consent initializer 的两处V3期待仍用原DDL表达式，而非实际MySQL catalog rendering。Chat V3、V2和typed阶段未运行；原失败与owned schema清理PASS均保留。

新Source Owner提交 `7abcd58ad74d4deb23e9b4c0a572168004b05ebb` / tree `7dae5070aa1c5bb45e90419f415c83b07708048a`，仅三路径：新增catalog-only accessor、替换旧initializer两处期待、补实际catalog正向与弱化/TRUE/OR/缺失/额外/未执行CHECK负向测试。Main独立核对生产diff只含该accessor和两处调用替换；DDL、共享normalizer及第四允许路径不变。仅静态接受为新验证输入，尚未晋升feature/pin。

同一Owner自检首次 `7abc` 在read-only MySQL TCP前置检查失败，**未运行任何Gradle/数据库写入**。Main进一步按精确自有Unix socket只读核验，MySQL8.0.21、UUID/datadir、PID/start_ticks仍匹配且服务存活；故障是旧TCP代理已消失，不是数据库死亡。已授权该Owner在新验证runner生命周期内创建自己的TCP→此唯一Unix socket适配，不重启/操作mysqld或其他进程。新的输入、前置身份/私有prefix检查及完整正常图V3→V2→typed 11类回归继续；旧NOT_RUN/失败不改写。旧source回执错误未来时间已由单独actual-clock correction补正，原字节与摘要保留，不把错误时间用作事件发生证据。

Client新版兼容已从“没有Owner”推进为**真实Owner READY并绑定唯一ledger/获GO**，开始冻结v1.1七路径施工及相关Node/离线native测量；最终源码与实际测试结果仍待返回。没有启动真实app-server模型、Provider或生产安装，不据此宣称INSPECT或严格无工具可用。

当前版本占用见[分版本最新补充](versioned-delivery-plan-20260928.md#2026-10-01-当前版本重新核验优先于历史候选号)：1.13.45/46/47均不可再当本特性新候选号；三个出厂范围不缩减，达到条件后选当时空闲版本。本特性仍未合develop、发布或完整验收。


## 2026-10-01 21:36 实测补充：OOM归因与Client边界修复

`7abc`第二轮已通过自己的TCP→Unix桥身份及prefix前置核验，但**kernel global OOM明确杀死自有Gradle daemon PID 2844792**，发生于production依赖编译、JUnit尚未开始；fresh XML为0，V2/typed均NOT_RUN，不能分类成JUnit失败。此前argv额外包含全局`--rerun-tasks`，导致全部production/AP/compiler依赖强制重编译。原始raw/argv/kernel/PID及清理证据已保存，owned schema cleanup通过，桥关闭且原mysqld未操作。cleanup回执另有先close后读取socket的EBADF，原异常不掩盖。

已通过唯一ledger的`authorize-remediation`冻结第三轮输入：源码、normal init、堆、依赖/AP与全部selectors不变，仅去掉全局`--rerun-tasks`，每个目标Test task使用自己的`--rerun`产生fresh XML；内置选项由本地Gradle9.3.1 primary bytecode确认。Owner在新runner中保持桥到三个阶段终态，关闭前捕获socket元数据。此为受证据支持的新输入，不是同输入盲重试；当前尚无第三轮结果。

Client `ff594c6b7e38293501326cf980c34ffa9921a614` / tree `6ecfd9d2e2e4500a50164c7fad5e3a671c7b61c2`已完成七路径源码及Owner **161/161 Node PASS**，清环境的真实native version/schema离线测量也通过：CLI0.159.2、bundle `7243ba24…`、binary `1748767b…`，40资源/78101808bytes，private copy。保留默认0.153.4及旧wire，资源量只观测；该测量没有启动会话、模型或Provider。

Main对真实模块的纯负向probe另发现：registry为plain object，`__proto__`、`constructor`、`toString`等未登记继承键被当作合同；当synthetic measured readback缺少三个合同字段时，undefined比较可错误得到READY。普通未知字符串正常拒绝。**这是实测合同校验失败，不是已证明远程利用或真实engine启动**；161项原PASS保留，`ff594`尚未晋升feature/pin。已交回同一Owner限定own-key最小child及resolver/声明/runtime零启动负向回归，不再重复重资源native测量，不改INSPECT/wire/默认合同。

证据均收进[便携manifest](integration-evidence-20260928/catalog-and-native-runtime-progress-20261001/portable-manifest.json)：`api-7abc-v2-oom/`、`client-ff594/`及`main/client-ff594-own-key-negative/`；两个Main限定修复/验证矩阵也同目录保存。当前范围仍为完整产品，不以源码/离线测量代替真实INSPECT、双接应、多媒体、正式交付、验收或发布。


## 2026-10-01 21:44 Client最小child已接受并推送

同一Source Owner完成`607d25145efe3d13f996e5fbb5e33a01d7bf2195` / tree `c1fb2ccac220d588d341999ea4adbd6f3757fb3c`，parent为原`ff594`，四路径child只有central resolver own-key判断和三份测试增量。Owner **162/162 Node PASS、0fail/error/skip/cancel**；Main在新不可变模块副本上不改原断言，重跑原继承键7项和typed事实/绑定4项，全部PASS。原ff594负向失败和161PASS仍保存，不改写为通过。

默认/两份登记合同、旧CODEX_APP_SERVER_SCHEMA与wire/fixture未变；own-key修复不改资源测量逻辑，复用ff594真实离线native测量，不重复重资源运行。Main核对exact source/path/log hash及clean tree后，以FF-only、普通非force push晋升Client feature，远端直接回读为607d；SDD Client研发pin同步。证据见同一[便携manifest](integration-evidence-20260928/catalog-and-native-runtime-progress-20261001/portable-manifest.json)的`client-607d/`、`main/client-607d-probes/`及push readback。

这是原生版本兼容的**源码接受**，不是启动或生产安装；INSPECT仍NOT_ENABLED，strictNoToolsVerified仍false。API7abc新第三轮完整验证未返回，不晋升API；完整浏览器/双接应/多媒体正式交付/用户验收及本特性发布仍待实际完成。


## 2026-10-01 第三轮API结果：Agent39通过，Chat测试source-set编译失败

`7abc`第三轮实际argv正确移除全局`--rerun-tasks`、各目标Test单独`--rerun`。Agent V3 **39项、9份fresh XML、0fail/error/skip**，Main独立解析原始XML确认；新增legacy-catalog测试已实际运行。其后Chat V3 `compileMmdControlledImageFollowupV3Java`报3处同一未解析fixture引用，JUnit没有开始；**整个V3阶段FAIL、V2和typed11均NOT_RUN，API不晋升**。不是本轮OOM，也不能将39项部分通过当完整后端通过。

实际依赖闭包为V3 `AgentWebSocketControlledImageV3ExecutionTest`→已有`NativeProviderCredentialBindingDeclarationTest`→已有`AgentRuntimeCapabilitiesTest.candidate()`；V3 source-set漏了这两个fixture，V1/V2已经包含。已冻结单路径source-only child：只准`chat/jia-chat-service/build.gradle`补入上述两个已有源，保留全部现有selectors/依赖/AP/resources，不改断言、不借旧class；fixture自身测试自然增加实际数量。Main尚未收到child；新源码exact SHA/tree及后续验证需重新绑定，不能直接重跑旧输入。

第三轮owned schema清理PASS、桥关闭`connect_ex=111`、mysqld PID/start_ticks未变且未操作；关闭前捕获元数据后已没有第二轮EBADF。原始argv/raw、fresh XML、source/class provenance、精准归因和cleanup收进[便携manifest](integration-evidence-20260928/catalog-and-native-runtime-progress-20261001/portable-manifest.json)的`api-7abc-v3-compile-closure-failure/`，Main实际XML核对和最小child矩阵保存于`main/`。

当前接受的组件研发pin仍为API87c0、Webebb、Client607d；源码失败没有覆盖已接受基线。完整功能、INSPECT/双接应/真实浏览器和版本发布继续保持未完成，不发送“可以验收”通知。


## 2026-10-01 21:58 依赖闭包child已提交，下一轮验证输入已绑定

`30632a9754ace8e03cdc1f7561ba12237c0f377e` / tree `04d2fddd83a4e86adc21d6aaf2e866de5fa913dc`，parent7abc，clean；仅上述build.gradle增加两行include。Main独立移除新增两行后逐字节等于parent，原production/fixture/assertion与其他构建配置不变。这只是静态接受为验证输入，尚未晋升API feature/pin。

新v4矩阵和唯一ledger绑定3063精确源码，保留正常依赖/AP、目标Test单独`--rerun`、全部V3/V2/typed11；新加入两份fixture必须真实运行并计入fresh XML。已向同一实际Owner投递GO。首次message工具返回owner未找到，没有据此宣称执行开始；恢复同一ID后再投递已受理，保留控制面恢复回执。**当前未收到v4结果**。原第三轮39部分通过/Chat编译失败及历史OOM/前置失败保持原样。


## 2026-10-01 22:07 验证路由故障与真实Owner重新绑定

v4原Owner实际报`Selected model is at capacity`，没有v4测试/runner结果，不能宣称已执行或通过。Main保留原始控制面错误并关闭自己的errored Agent，不重试同一路由、不改全局模型配置。新Terra验证-only Owner已实际READY，核对3063 clean/source及完整normal graph，无真实阻塞；经唯一ledger`authorize-remediation`和精确owner/SHA/tree绑定后获v5 GO，使用新的独立证据目录。原Sol/Mini失败保留，不调用DeepSeek，不新建独立Reviewer。

v5保留所有源/依赖/AP、V3新增两份真实fixture、V2和typed11，以及owned桥生命周期/身份/prefix/provenance/fresh XML；模型路由变化不能缩减测试范围。当前仍待真实结果，API feature/pin未提升；本特性未发布、不可通知可验收。两份故障归因/实际Owner矩阵已入上述便携manifest。
