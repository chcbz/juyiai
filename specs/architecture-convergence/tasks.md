# 单Owner实施计划与范围控制

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：统一事实归属、性能与DFX职责。**

**实施目标：** 先定位事实所有者和真实绕过点→只改责任层→契约变化时联动实际消费者→删除被替代临时路径→定向回归。
**责任落点：** 入口认证；API业务规则；公共持久化隔离；Runtime执行隔离；工具具体协议；Web展示。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：一条规则一个责任层；不是全链复制scope、统一兜底框架或重启2026-10-26历史排程。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：身份/ACL不弱化、重复决策与无依据校验被移除、错误只影响所属失败域、真实消费者用例覆盖；不为局部修复强制全仓重测。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

## 原有材料的适用范围

2026-10-26 B0–B5的固定候选排程/发布记录，不重启旧截止与旧Flow步骤；当前新增改动按上方现行方式执行。 后文所有旧“当前/最新/待实施”仅指其原时间，不是2026-11-07状态。



状态：**B0–B4已编码；API321/Web321/Runtime62本次同Run测试、制品与安装已核验；B5线上会话准备受阻，整体未完成**。单Owner，沿用唯一Web隔离worktree；不分派子Agent、不增加Reviewer。07:28用户“确认”授权本轮固定候选发布及既定业务回归。

## 1. 09:00硬截止计划（2026-10-26用户实施授权）

用户最新指令“开始实施，9点前完成”覆盖上一版07:37截止，现已开始B0。单Owner串行B0→B1→B2→B3→B4→B5，不分派子Agent，不增加Reviewer，保留AC-01至AC-06及必要验收。

- 实际开始核对：**北京时间2026-10-26 00:18:52**；排程按00:19起算。
- 硬截止：**北京时间2026-10-26 09:00**；剩余约8小时41分钟，不再从任意续接点重置本次时限。
- 等待、冲突处理和返修均计入；原16–29小时估算仍提示超时风险，不能删除必要测试换速度。
- 已获实施授权；07:28用户明确确认生产发布，授权只覆盖本次固定候选和既定回归。

| 批次 | 北京时间窗口（10月26日） | 分钟预算 | 交付/退出条件 |
|---|---|---|---|
| B0 | 00:19–01:00 | 41 | 固定源码/规范，保留他人修改，落实边界检查，核对测试和环境 |
| B1 | 01:00–02:10 | 70 | policy分类和指定消费者迁移，旧wire/幂等不变 |
| B2 | 02:10–04:00 | 110 | 两处资料读取迁移，旧SQL退役，关键权限/摘要回归 |
| B3 | 04:00–05:05 | 65 | Web调度提取，原生命周期和业务投影不变 |
| B4 | 05:05–05:45 | 40 | Runtime局部/整体失败分层，UNKNOWN不重放 |
| B5 | 05:45–08:00 | 135 | 固定候选、正式Flow/兼容回归、集成及获授权发布/业务验收 |
| 返修收口 | 08:00–09:00 | 60 | 仅本期缺陷重验和证据收口 |

各批可以提前推进，不为等待排程窗口空转。B1/B2合为API正式候选；Web/Runtime分别绑定候选。编码中只做必要定向反馈，不逐小改正式构建。Flow每Run≤600秒，不删必要回归、不搬本机重型构建。

### 检查点与失败处理

1. B0结束必须说明候选、规范、测试环境及发布授权是否齐备；发现影响期限的阻塞立即报告，不留到最后一小时。发布授权未取得不得操作生产，等待仍计入本次时限。
2. 每批报告完成范围、剩余项和截止风险；阶段通知不要求重复人工批准。05:45检查全部编码是否完成；未完成立即报告，只能使用现有总预算，不能挤掉必要验收后宣称成功。
3. 08:00明确实际回归结果及未验项；剩余一小时只处理本期缺陷与收口。无法在截止前满足退出条件时如实说明，不静默延期。
4. 截止时AC-01至AC-06、指定正式验证和业务验收仍有未完成/失败/跳过项，**本次优化整体标记abandoned，不按部分完成交付，不自动另起优化续做**。缺少发布授权或线上验收同样不能宣称全部完成。
5. 全部编码及必要发布前回归通过前，不分批把半成品合入共享develop或部署。候选保留可追溯差异；不强推、不reset共享分支，不以目录整体还原清除其他任务修改。
6. 废弃时停止新增开发、合入和发布，保存本任务必要补丁/证据及失败原因，收回本任务未交付改动。若已合入或已安装，仅对本任务提交/程序按既有锁、备份与恢复流程安全撤回；保护他人提交、身份、授权、资金、业务数据和checkpoint。若恢复存在冲突立即报告，不盲目覆盖。
7. 到点尚有本任务Run或安装步骤时按受控取消/恢复流程处理，不强杀无关任务或遗留半安装。安全恢复若超过截止仍记本次优化失败，不以恢复为由延长开发期限。仅保留审计记录，不删除失败证据；本次规则不会自动安装后台计时器。

### Agent分配与完成定义

唯一执行者为当前会话Agent：承担B0设计核对、B1/B2后端、B3前端、B4 Runtime、B5测试协调/浏览器验收/收口。Flow只是执行重型作业的工具，不是额外Agent。本次更新仅调整计划，不把未运行的检查改成通过。

“完成”必须同时满足：全部指定实现与旧逻辑退役、约束检查有效、必要测试真实执行通过、精确候选及制品证据齐全、集成及获授权发布、PC/移动端与图片多轮业务验收通过。PDF沿用暂不验边界。不能以编译成功、部分批次完成或线上健康代替整体完成。

## 2. B0 — 基线与防新增债

**目标/条款：** AC-05/06，design §2。Owner：当前单Agent。

- [ ] 创建/复用当前任务handoff，记录四仓commit/tree、规则版本和“未发布”。不更改其他ledger条目。
- [ ] 对比本包固定版本与实际候选相关符号；处理未入Git的validation-policy/已批准校验清理，留差异证据。不能checkout覆盖脏树。
- [ ] 在API既有validateLayering增加G1–G4，生成并人工分类精确旧债baseline。
- [ ] 当前5处SecurityContext与G1已存在依赖允许暂留但禁止新增；不是批准旧代码为必要。
- [ ] 把本包导航加入specs/INDEX，API baseline说明引用本包；若维护既有文件，必须保留他人修改，独立审查自己的增量。
- [ ] 核对关键测试实际归属：文件→sourceSet→task/filter→Flow argv→报告，不能只检查文件存在。

**允许代码位置：** `api/build.gradle`、`api/docs/architecture-boundary-baseline.json`（新增）、相应既有规范的明确增量。本包及INDEX是文档范围。不得同时改root Flow适配器、任务ledger协议、应用配置或公共skill。

**退出证据：** 基线版本可重现；新增跨域impl/新增隐式身份访问能报告精确位置；旧允许引用不误报；规则实现差异与测试报告明确。允许用最小合成import/注释夹具验证解析，不新增一套架构测试项目。

## 3. B1 — 明确可恢复性

**目标/条款：** AC-01，design §3。

**生产allowlist：**
- `api/agent/jia-agent-api/src/main/java/cn/jia/agent/service/TaskSkillPolicyService.java`
- `api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/TaskSkillPolicyServiceImpl.java`
- `api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`（仅policy消费方法）
- `api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatActionExecutionService.java`
- 同目录`ChatActionCapabilityService.java`、`ChatActionDispatchService.java`、`ChatDeliberationOutboxRelay.java`

实施顺序：
1. Snapshot分类方法及表驱动关键断言；保留record字段、constructor、equals。
2. Action先迁移，能力目录及workspace技能消费随后；逐项搜索所有`TaskSkillPolicyService`/`policy.allowed()`，不能只修报错处。
3. 局部Unavailable与Rejected区分；只改错误表达，原outbox控制流不重构。
4. 删除迁移后的reason字符串业务判断，不删除reason日志/wire；零新DDL/HTTP字段。

**关键回归：**既有`TaskSkillPolicyServiceTest`、`SkillExecutionServiceTest`、`ChatActionCapabilityServiceTest`、`ChatActionDispatchReviewGuardTest`。已核实`ChatActionDispatchReviewGuardTest.transientRuntimeLossRetriesPreparationButRevokedGrantStillRejects`覆盖瞬断及撤权，直接扩此用例/同类测试验证类型分类；**不再新增ChatActionAvailabilityTest**，不补数量阈值测试。

**退出：** 原grant错误仍拒绝；Runtime短断线只重试；同action只一个child；未授权仍不能列出他人技能；无新reason比较旁路。

## 4. B2 — 资料读取端口

**目标/条款：** AC-02，design §4；B1完成后实施，避免在同类并发改动。

**生产allowlist：**
- 新增`api/agent/jia-agent-api/src/main/java/cn/jia/agent/service/TaskLinkedMaterialReader.java`
- 新增`api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/TaskLinkedMaterialReaderImpl.java`
- `api/agent/jia-agent-mapper/src/main/java/cn/jia/agent/dao/PersonalWorkspaceTaskLinkDao.java`
- 同mapper模块`dao/impl/PersonalWorkspaceTaskLinkDaoImpl.java`、`mapper/PersonalWorkspaceTaskFileLinkMapper.java`
- `api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatTypedDeliberationContextService.java`（仅workspace普通读及依赖）
- 同目录`ChatSkillSourceAccessService.java`（仅workspace分支及依赖）
- B0 baseline删除已清理例外。

实施顺序：
1. Mapper新增exact查询，DAO内部record；不删旧表/列/SQL资源，不改其他消费者。
2. Reader元数据、内容、I/O后重验；无HTTP、无DB写入、无长事务包裹I/O。
3. 两个Chat调用者迁移且保留原source JSON/摘要与错误映射。
4. 删除两处已迁移SQL；确认effectiveSelectors和inspection锁读未被误删。
5. 关键旧用例复用；缺口仅增加`TaskLinkedMaterialReaderTest`与必要的`TaskLinkedMaterialReaderMySqlTest`，使用项目已有CYF_REVIEW_MYSQLD自有进程隔离MySQL fixture，不引新数据库框架或sourceSet。若真实MySQL无法启动，记阻塞，不用mock替代并发验权通过。

**关键回归：**补充既有`ChatRetainedOutputSourcesTest`中的两处端口消费者绑定/错误映射回归（只增加本次迁移关键断言）；既有`PersonalWorkspaceTaskFileLinkMapperContractTest`、`PersonalWorkspaceTaskLinkServiceImplTest`、typed/skill源消费，新增reader tests只覆盖scope、固定版本、摘要、撤销和异常映射这几个风险。

**退出：** 两个指定方法不再访问Agent表/内部storageUri；两份相同文件名、不同版本/owner不会串用；链接读取中撤销不得把内容交给下一步Provider。旧JSON和snapshot hash匹配。

## 5. B3 — Web调度模块

**目标/条款：** AC-03，design §5。

**allowlist：**
- 新增`web/src/composables/juyiting/hallRequestReadbackScheduler.js`
- `web/src/composables/juyiting/useHallConversation.js`，仅设计列出的Map/调度/生命周期调用者
- `web/tests/juyiting-hall-conversation.test.js`
- `web/eslint.config.js`（仅新模块依赖限制，若现有规则可满足则不改）

实施顺序：原行为断言→抽取纯调度→迁移所有inflight查询→reset/dispose→删除旧Map和函数实现。原GET绑定/版本校验仍留原业务模块；不要把复杂代码换个名字全部搬过去。

**禁止：** 不改JuyiHall模板/style、typed submit语义、源资料选择/成果parent、频率/超时、Provider，故本批无需原型修改；若出现上述改动需求，应作为范围变化重新写规格/原型，不混入本批。

**退出：** 同一请求并发GET合并、尾沿终态读回不丢、切账号/会话后的旧响应不落库、不残留定时器；PC/手机界面及业务行为一致。

## 6. B4 — Runtime结果报告

**目标/条款：** AC-04，design §6。Runtime任务必须显式携带根AGENTS及本包固定版本，不能只读isp-install局部旧release规则。

**allowlist：**
- `conf/codex-ws-agent/skill-conversation.mjs`（仅poll批结果）
- `conf/codex-ws-agent/agent-client.mjs`（仅native poll caller日志/返回消费）
- `conf/codex-ws-agent/test/skill-conversation.test.mjs`
- `conf/codex-ws-agent/test/agent-client.test.mjs`
- Runtime现行package版本/锁定及交付说明，只有真实制品准备时才改，不能借此升级依赖。

**禁止：** 不改effect key、provider request、执行manifest、安装目录、systemd、pause/kill策略、租约、重试时钟；不新增独立后台检查进程。

**退出：** 一个execution错误不掩盖另一条成功；未知副作用不增加执行次数；共享scope/store冲突仍中止；caller能分清PARTIAL与整体unavailable。

## 7. B5 — 一次统一验收与交付收口

- [ ] API B1/B2候选：定向测试＋validateLayering＋既有必要回归/打包在Flow5260799。测试selector增量只改已有policy中相关列表，不删其他任务必要测试。
- [ ] Web候选：Flow4403172实际release profile并记录报告；不以assets未跑宣称所有地图性能已验。
- [ ] Runtime：已授权时Flow5264702固定候选测试/打包/安装；单纯分析任务不触发。
- [ ] 核对任务、图片、跨账号、瞬断、验收完整流程，详见acceptance。
- [ ] 记录测试/构建、安装、Run终态、线上业务四种结果；用实际SHA，不写“latest”。
- [ ] 组件自检后合入develop；不自动部署。发布需明确范围/授权；各阶段失败即时报告，不静默延期。
- [ ] 稳定归属与错误语义回写既有知识主题；原冻结合同和历史失败不重标。原始证据就地保留，不再堆日期版方案。

## 8. 防发散的提交契约

每批handoff/提交说明必须含：`batch_id、spec条款、base/candidate commit+tree、改动文件/符号、删除旧入口、关键测试selector及实际结果、未验项、范围变化`。

出现新路由/新表/新依赖/新全局开关/重复facade/与本批无关格式化时，不得以“顺便优化”继续。先记录具体阻塞和最小必要变化并修订本包；业务范围改变须询问用户。Owner自检不需要独立Reviewer，不为每个普通提交新增审批。

结束标准是**新路径唯一、旧重复实现退役、关键行为证据齐全**；不是“编译过”“多写了测试”“代码看起来更整洁”。

### B5执行入口核实补充（2026-10-26 00:58）

API Run315在Gradle启动前失败：现有flow_ci_context同时硬编码三个旧分支，与本任务候选分支不匹配。为验证未集成候选，B5仅允许在既有backend-ci-policy.branches及flow_ci_context精确分支列表中加入codex/architecture-convergence-api；不伪装develop，不去掉源码/tree/命令/身份约束，不重构编排器。对应已有test_flow_ci原分支循环用例覆盖此增量。云端临时配置同样限定此分支，结束后按摘要核对恢复原配置。

Run318补充：Gradle全部执行成功、撤权真实DB回归通过；制品export仍有同一旧分支名单。仅对既有backend-ci-run.sh的checkout/export名单增加同一本任务分支，保持commit/tree/clean/run/制品摘要核验；不删除身份检查，不混用其他Run制品。
