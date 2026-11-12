# Provider core 普通验证、真实 MySQL 与页面恢复增量

文档日期：2026-09-30。原始宿主日志部分显示2026-10-01，按原字节/时钟保留，**不作为当前日期或发布日期**。这是源码施工证据补充，不修改冻结业务/wire，不新增运行台账。

## API：v13–v15普通验证与真实 MySQL 历史问题

候选 `b443be0001cf2f1d3bfdbe833c9a6adf023fbeda` / tree `fb8ad1baacc8f2de310fb021858cbd97a6259cc5` 仅在pure9ad之后增加scoped chat mapper依赖、修复测试List泛型推断；BRIDGE-A在途源码未混入。在v13–v14核验点，API feature保持`083f9846`、未提升研发pin；本轮最终v16整合结论见末节。

| 执行 | 实际结果 | 证据含义 |
| --- | --- | --- |
| v11 | Agent35通过、3MySQL跳过；Chat主javac之后daemon增量分析OOM | 不当成Chat测试通过 |
| v12 | 正常production Chat full javac通过；Chat fixture编译3项mapper缺失、1项List泛型错误 | 0Chat测试，不是完整验证 |
| v13 | exit0；Chat17测试/6XML全部通过；Agent任务UP_TO_DATE | Agent明确复用v11实际35通过+3跳过，不声称本次重跑 |
| v14独立MySQL3 | 3测试、3失败、0跳过 | 三例均在setUp抛`chk_atpcc_identity` CHECK definition drift；业务体/CAS并发断言尚未执行 |

v13正常完整source/dependency graph、AP和所有11个fixture源仍保留。private init仅关闭既有两个bounded fixture及production Chat compileJava的增量优化，不跳任务/借baseline类/弱化断言；heap未增长。v14使用同一精确源码、distinct class selector和显式opt-in五项env，真实JDBC连本线程隔离MySQL8.0.21。Main实际socket和loopback TCP身份均核对相同datadir/skip-networking实例；执行后只读核验prefix库为空，未控制mysqld/proxy或操作生产。

普通验证通过不能掩盖真实schema初始化错误；原Owner先补真实CHECK_CLAUSE证据及最小scoped修复，再固定新immutable/matrix重测。不去掉定义检查、不放行同名弱CHECK。此前v9/v10及本补充v11–v14失败保持原结果。

## Web：恢复与自动采用已实证，候选仍待整合

原`0eb99d0`候选正向自动接入已通过，但真实Page目标watch在旧GET等待时切换Agent仍adopt1：stop timer不等于fence in-flight响应。Main使用精确Git blobs、实际Page onBound/attach/clear/watch表达式及真实Vue/native/controlled composables重现，交原Owner修复。

候选`02a116cc24c85f008fb30d7c3cbfd29f3cb651fd` / tree `064c1606fa121467c7ade25befb8184dac2f52b2`已加入Page context generation、native in-flight fencing，并识别合法自身canonical任务更新，避免正向采用被自己取消。Main精确组合证据：

- issuer-only ACK-loss：实际Page check读取原费用同意；显式resume使用原bridge读回/原键POST，无native capability/legacy降级。
- 实际Page onBound自动观察：PREPARING持续到ADMITTED后ATTACHED，adopt1；一次bridge POST，无`/assign` POST。
- Agent、authorization generation、task/requirement revision失效：释放迟到原GET后均adopt0；不补发写操作。
- revision watch的**新只读恢复**与**旧迟到GET**分别记录，不能把只调用composable或错误传task对象的stub当作完整Page恢复证据。

以上是fake HTTP的真实实现组合，不是整页SFC/browser/实际API联调。中间native-only探针因简化watch恢复入口而出现revision额外读取；它不属于完整Page证据、不归因产品失败。Owner仍须完成持久回归/最小selector及scoped lint自检后，Main才精确FF/push。

## 便携证据与下一动作

[manifest](integration-evidence-20260928/provider-core-normal-mysql-web-recovery-progress/manifest.json)包括v11–v14原始stdout压缩摘要、真实normal/MySQL XML、固定matrix/inputs/init/runner、隔离资源前后读回、Page精确探针/完整Git blob源码闭包，以及只读历史失败快照。压缩日志固定mtime，原始/压缩摘要均保留。snapshot不是第二份Owner/gate台账，运行仍仅在主根TASKS.yaml。

下一执行步骤：原API Owner修复pristine CHECK误拒绝；Curie对新exact source按新matrix串行验证。Web Owner补真实Page恢复回归后整合其确切源码。随后继续BRIDGE-A三段事务及共同29 fixtures、同会话澄清/旧稿EDIT、全部媒体/归档/正式验收、develop语音收敛与双接应浏览器。

未选真实账户、未调用Provider/付费、未构建发布/部署/启用/迁移生产。**完整34项产品用例仍NOT_RUN，29共同桥fixture不据局部测试改PASS；尚不可通知可验收。**

## 本轮后续精确状态

- Web`8244f5a`/tree`a9e7910`已source_accepted，83项实际通过与Main真实Page闭包证据保留；SDD研发pin/gitlink更新，不是发布/验收。
- API纯`041bd061`只修provider-specific严格13项catalog比较及回归，实际MySQL raw catalog13/13匹配且诊断finally清理；v15 Agent39项中38通过1fixture失败，零skip。两个MySQL生命周期/CAS用例实际通过；第三例DDL`CHECK(1)`被MySQL8.0.21以3812非布尔表达式拒绝，故尚未进入“弱CHECK应拒绝”断言。Chat本轮未到达，不冒用旧v13 XML。
- 原Owner独立test-only`99ff1a43`将弱约束改为合法布尔永真`CHECK(1=1)`，完整拒绝断言保留。Main固定新v16 matrix/input、live socket/TCP资源并启动新候选的一次验证（不是重跑旧输入）；此补充写入时仍在验证，API pin保持083f。
- cache登记先被旧task SHA、重复Main活跃Owner及错误gate/mode拒绝；检查orchestrator实际验证规则后，使用原Owner self-verifier在verification gate登记精确证据并释放。没有绕过检查、虚构新Reviewer或修改外部OAuth任务；这些控制面错误不当作业务测试失败/成功。

## v16最终源码整合（不改历史失败）

新immutable`99ff1a43` / tree`d44fb594`的完整两个scoped selector在同一次normal graph运行中成功：Agent实际39项（包含真实MySQL3）、Chat实际17项，合计11XML/56项，0失败/错误/跳过。两项Test任务实际执行，不是UP_TO_DATE复用旧XML；63tasks中3executed/60up-to-date是正常生产依赖输出复用，不当作只有3个测试。stdout摘要`1fa37be056209ac29f6b2a5653f0fec4012c09cdadc8f1de3d6860e72fba5aef`。Main确认live进程终止、全部XML/摘要及socket/TCP实际身份和空prefix清理后，API feature已byte-exact FF/push/readback到99ff；SDD研发pin与api gitlink同步。

上文“API不提升/仍在验证”只属于对应v13–v15/v16准备时点；失败XML/原始日志不改PASS。本次关闭的是Provider core源码验证及Web恢复源码包，不关闭API受控Grant/execution/START三段桥、共同29fixture、澄清/旧稿EDIT、真实Provider/双接应/浏览器/正式验收、develop语音收敛或版本发布。34产品用例继续NOT_RUN。下一步由原API Owner提交完整BRIDGE-A immutable候选，再固定实际Spring/MySQL/跨仓验证。
