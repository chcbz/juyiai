# 旧弱CHECK识别与真实Java/MySQL生命周期证据（2026-09-30）

API研发候选：`b1e7b06817f041804f1e1d613ff4aa280641e904`；tree `ec0d645cd310517cf836218f285332a402c8228f`。父系包括已整合的`f93febe9`，fast ancestry保留。Owner自检、精确树验证后fast-forward到`codex/juyiting-multimedia-deliberation`；无develop/release/生产/付费变更，不表示用户可验收。

## 实际修复

1. Agent/Chat finalization initializer读取实际CHECK_CLAUSE，拒绝同名且ENFORCED但弱定义；只对已有真实穿透证据的`chk_asof_lease`、`chk_csof_progress`、`chk_csof_terminal`检查规范化精确表达式。不自动ALTER/DROP/DML。
2. 修复真实MySQL新表启动阻塞：TEXT/MEDIUMTEXT的CHARACTER_MAXIMUM_LENGTH分别为65535/16777215，而原描述错误预期null。仍严格检查类型、容量、nullable/default、collation、index和scope；这些数字是MySQL类型元数据，不是新设文件大小或性能门禁。
3. 单测保留错误/null长度、旧弱CHECK、缺失定义、always-TRUE追加、literal case变化与未ENFORCED拒绝。

## 验证与复用

| 验证 | 实际结果 | 边界 |
| --- | --- | --- |
| 正常源/模块图 | 84项报告，0失败/错误/跳过；本次42执行，42Agent未变测试由GradleUP-TO-DATE沿用 | chat32 finalization+5schema+5readiness本次执行；agent42沿用同源/selector/fixture，不声称84项均重跑 |
| 真实JDBC + Spring InitializingBean graph | **6/6 PASS**，MySQL8.0.21、Java21.0.8 | 精确候选真实类加载；不是整套SpringBoot应用/生产构建 |
| 两次上下文启动/重复callback | PASS | core→deliberation→finalization/archive在runners前就绪；runners不重复source初始化 |
| 旧弱CHECK与raw legacy fence | 只读拒绝PASS | 表/列/定义不变；未自动修复旧库 |
| 修正后的既有CHECK | 只读接受PASS | 独立旧/修正fixture，不能由此宣称生产已迁移 |
| 本次Java创建DDL的3种NULL | MySQL3819全部拒绝，0记录 | LEASED null lease version、SUBMITTED/TASK_COMPLETED null delivery state；不依赖重叠CHECK报告顺序 |
| named锁/代理归属 | PASS | 锁释放；本线程loopback代理已正常关闭，无错误，mysqld未操作 |
| Provider/完整浏览器/上线 | NOT_PROVEN | 不生成替代图片、不通知可验收 |

实际新库采用**源派生的pre-fence测试表**：从chat mapper测试DDL只去除3个core fence列和相关索引，使真正core initializer建立canonical DDL。不是未修改的生产建表DDL，也不证明任意旧生产库升级成功。原始chat测试表指定DEFAULT CHARSET=utf8mb4，MySQL默认得到0900_ai_ci，即使数据库默认0900_bin；原始失败库保留，后续测试只读证明其被拒绝。

真实测试的旧弱CHECK库、修正库及raw拒绝库固定为当前线程独立fixture；新建库独立命名、socket/datadir/版本/skip_networking校验，未使用生产或其他线程库。所有Gradle经orchestrator串行，无抢占/任意性能拒绝门槛。

## 原失败保留与精确归因

- v1：Groovy变量shadow source DSL，编译/JDBC前失败。
- v2：harness配置Java25，而实际Java21；编译/JDBC前失败。
- v3：3PASS/2FAIL，原始seed排序规则被core正确拒绝；finalization未创建是依赖失败。
- v4：旧plan路径未切换，读到旧2表库，BeforeAll失败；intended fresh库未修改。v3同样读取v2 plan，源码同字节，证据不冒充计划绑定。
- v5：4PASS/2FAIL，真实TEXT/MEDIUMTEXT元数据预期错误；以b1e7源码修复。
- v6：5PASS/1FAIL，3819/HY000被Spring映射为UncategorizedSQLException，harness错误假定另一个异常子类。
- v7：5PASS/1FAIL，TASK_COMPLETED被重叠progress CHECK先拒绝，harness错误假定必须terminal标签。
- v8：**6PASS/0FAIL**；vendor3819及相关CHECK标签、精确SQL状态仍验证，不给CHECK顺序加无依据门禁。

证据根`/home/isp/wsps/cyf/evidence/u3-finalization-schema-check-truth-v1/`；[便携摘要](integration-evidence-20260928/schema-check-truth-20260930/schema-check-verification-v1.json)、[真实结果](integration-evidence-20260928/schema-check-truth-20260930/actual-java-mysql-result-v8.json)、[正常回归执行/复用](integration-evidence-20260928/schema-check-truth-20260930/normal-schema-reuse-v2.json)。日志和各版失败原样保留，摘要携带SHA-256。

## 后续出厂依赖

实际旧库若有弱CHECK/fence drift，需明确授权、恢复方案与独立迁移验证；本修复只安全识别，不偷做迁移。后续继续[原生能力合同](native-bounty-capability-contract-v1.md)、真实页面/客户端注册接线、task-linked参考图、澄清/修改/派生资产与合法costAuthorizationRef桥；两种接应真实Provider/34项产品用例和版本制品发布仍单独验证。
