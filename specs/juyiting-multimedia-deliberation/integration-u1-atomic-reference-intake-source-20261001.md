# 可选参考图原子创建：真实 MySQL 修复与源码整合

适用当前日期为2026-09-30；本补充文件名保留宿主日志原始时间标识（2026-10-01），不用于推断当前日期或发布日期。长期目标与冻结合同不变。仅源码验收，整套产品34项仍 NOT_RUN。

## 1. 当前精确研发基线

- API：`083f9846ee26835e6db79892e4f7186accff467a`，tree `fbc21df09279e7924d997b11b56ed59039bfa475`。
- 两个父提交：已推送能力基线 `74b4b44e` + 原子创建/约束修复 `2a1364dc`。Main组合无手工冲突修补；feature从74b4精确fast-forward，推送并远端readback一致。
- Web：`7821209c874995621d139da9047983f3b586d0b0`；Client：`1812e5b5d090013338265d16ca34b0b9c257da49`，本包不变。
- 来源：[便携manifest](integration-evidence-20260928/atomic-reference-intake-source-20261001/manifest.json)。SDD gitlink与integration.yaml同时提升，不用主工作区脏checkout重新pin。

## 2. 缺陷、修复及实测

旧59ed候选真实MySQL2失败：catalog CHECK_CLAUSE与CLI展示转义不是同一层。原关键词匹配还可能接受弱CHECK。修复精确校验约束集合、ENFORCED及表达式，保留运算符/括号/字面值大小写；只规范化实际catalog的一层引号转义，拒绝歧义多层反斜杠。新增实际Spring CGLIB事务回归，避免新服务final造成代理失败。

Main合并树的正常源码/依赖图任务 `:agent:jia-agent-service:mmdU1ReferenceIntake` 已通过：

| 类别 | tests | failures/errors/skipped |
| --- | ---: | --- |
| Controller | 4 | 0/0/0 |
| schema initializer | 7 | 0/0/0 |
| mapper contract | 1 | 0/0/0 |
| 实际隔离MySQL8.0.21 | 2 | 0/0/0 |
| 实际Spring事务组合 | 2 | 0/0/0 |
| service | 4 | 0/0/0 |
| 合计 | 20 | 0/0/0 |

真实MySQL测试未跳过；运行后本线程前缀数据库余数0。自有loopback transport已按自身stop-file协作关闭，无代理错误，未操作MySQL服务或其他任务进程。证据含全部6份XML、Gradle日志、fixture、accepted-cache原记录、cleanup readback和transport终态及SHA-256。

accepted key：`66255835db4ce425b70e66eb4351c93463a7ae489d55ffe9bf4809be8d00afec`；fixture：`ee02435d1d0de6064fe13aff2140566863a2881dfc6ed9a4ad3db03e6dd6d135`。这是合并fbc树证据，**不是声称Standalone2a曾成功运行**；原Owner daemon消失记录保留。

最初组合运行在测试前发生kernel证实的全局OOM。归因后R2使用同Java21、正常图及真实MySQL，关闭实际GraalVM JVMCI编译器并调整自有JVM，未删断言/禁真实测试。仍fork single-use daemon，**未实现单JVM，不宣传单JVM优化**。原始MySQL失败及kernel归因均保留；`build_origin=local_user_authorized`，没有Flow Run。

## 3. 业务含义与边界

原子创建将真实task与精确REFERENCE版本放在同一事务，以owner/client/tenant和原幂等键隔离；刷新仍只读恢复，明确继续才复用原key/body。资料不因目录出现就被模型读取，task-link capability仍默认关闭，费用仍UNAVAILABLE。

本20项只证明新增原子创建及约束/事务组合，不累加旧74b4的66或Web108为当前整套回归；不证明完整启动、生产迁移、真实双客户端、工具前扣费门禁、画鸟浏览器交付、验收或发布。

## 4. 下一步

1. 将真实Provider凭据来源、平台operator delegation、task owner同意与Provider调用前门禁分别建模；不凭非空costRef、提示词或事后事件计数开放费用权限。
2. 补同会话澄清续办、精确上一稿EDIT/派生输入授权、原意图权威拒绝/放弃语义。
3. 收敛最新develop（保留voice/Redis4修复），完整启动及相关交叉回归；重新核实版本占用后构建同源制品。
4. 依既有授权边界完成双接应、真实媒体保存/交付/验收与34产品用例后，才发布并通知“可以验收”。
