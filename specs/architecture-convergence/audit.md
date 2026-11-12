# 全仓架构核对与根因分析

## 1. 基线与方法

2026-10-25只读查询四仓develop；以下是本次分析输入，不表示重新核验了当前生产。源码使用Git对象读取，未将共享工作树当成远端源码。

| 仓库 | 固定commit | 本地HEAD（核对时） |
|---|---|---|
| jia-sdd | `472a256c90ef19675b57c28c0c2dbc6be88ca4e4` | `5e6ab2b6f1a156c320189f17d76941fbe623738a` |
| jia/API | `e7e6f7e3b90bbe8f7d00abc85f5dcaec3bc33de3` | `94b4c8a5e5b1402ef44097b5a337a75431a0ec1b` |
| Web | `075c0c28a7cf7410d915dc15ca5eb5ff50ace01d` | `9dbd132e8bc25119c0532cbed672ab7fa4a214b3` |
| isp-install | `c4688cf792a2a24668b601fab6e5cea624df7e0c` | 同左 |

根commit的api/web gitlink与表中一致。前三仓有未提交修改；Runtime仓库还包含其他项目通用安装脚本，不因纳入盘点取得修改它们的授权。

### 全量覆盖到什么程度

| 仓库 | 全部tracked条目 | 读取的源码扩展文件 |
|---|---:|---:|
| Root | 3883 | 172 |
| API | 4416 | 2953 |
| Web | 1464 | 670 |
| Runtime/安装仓 | 465 | 237 |
| 合计 | 10228 | 4032 |

- 对全部Git树条目记录路径、blob、字节数和类别；读取全部`.java/.js/.mjs/.cjs/.ts/.vue/.py/.sh/.gradle`文件作词法盘点。API自定义非main sourceSet归测试；随包第三方静态文件单列，不当作应拆业务源码。
- 全部Java main源文件2021份。Gradle字面项目依赖305条；非test依赖图**未发现强连通环**。不包括插件动态生成依赖，也不等于Spring Bean没有循环。
- 原始跨包import候选不等于违规：排除了material→mat包名别名和测试，仍含合理common/core依赖。实际源码解析到其他域service文件的import198条，大量是公共基础设施；详表供复核，不能宣称198个缺陷。
- 深度分析针对任务→议事→资料→技能→结果→验收、异步恢复、身份边界、模块装配、测试/部署入口。其他模块完成树/依赖/入口盘点，**没有逐方法业务验收或生产流量覆盖**。
- 本轮不构建、不跑应用业务测试、不查询生产数据库、不做故障注入；反射、动态Bean装配、外部部署配置与真实性能不是静态扫描结论。

证据：[全文件清单](evidence/inventory.tsv)、[统计/依赖](evidence/static-audit.json)、[可解析service引用](evidence/service-imports.json)、[JS引用](evidence/js-imports.json)、[schema入口](evidence/schema-entrypoints.json)。

复核方式：`git -C api show e7e6f7e3:<下列路径>`；Web/Runtime分别用表中commit。行号是该固定版本的定位辅助，实施以符号为准。

## 2. 全项目模块处置矩阵

| 范围 | 已检查的边界 | 本次决策 |
|---|---|---|
| common/base、plugin、starter | 依赖、分层任务、基础接口、装配入口 | 保持基础设施；扩现有分层检查，不把业务搬入common |
| agent：任务/指派/租约/成果/工作空间 | 状态服务、grant、执行、跨域读写、恢复 | 一期收敛policy与资料读取；复杂执行器按后续队列处理 |
| chat：议事/WS/SSE/历史/验收 | outbox、Action、source、结果选择、连接注册 | 保留持久outbox和锁序；停止重复解释Agent数据 |
| economy：账本/技能购买/托管 | 暴露接口、Agent mapper耦合、事务入口 | 保留本地资金原子事务；跨域归属设计单独闭合，不删mapper依赖了事 |
| oauth/user | 公共身份接口、service上下文读取、消费入口 | 身份抽取不得顺手取消；需要逐调用点迁移 |
| task/workflow | 声明依赖、入口与聚义厅域关系 | 不将历史通用task模块误认Agent任务唯一实现，不合并状态机 |
| material/kefu/point/wx | 模块/跨域引用，KefuMsgTypeCode位于service | 值类型泄漏属结构债，未证实当前故障；一期不搬包 |
| isp/dwz/sms | 主源码、模块依赖、接口目录 | 未发现本次必须改造的依赖环；不等于功能/安全全验 |
| 知识库/记忆/ES/Embedding | MemoryRepositoryImpl读写、失败及清理调用点 | 写入/查询非空假成功已保护；清理空实现及count失败返回0另列，不开启清库 |
| Web业务、游戏渲染、原型 | import图、巨型组合组件、会话状态、测试profile | 一期只提取读回调度；游戏/地图/视觉不改 |
| Runtime lane/provider/安装 | poll、effect持久化、session、调用者和安装入口 | 一期仅结果分类/观测；固定app目录、身份、版本追溯不变 |
| Root SDD/Flow/健康检查 | 导航、规则优先级、测试选择及发布入口 | 合同必须进版本；不将doc check当作行为验收，不另建平台 |

## 3. 发现及可执行处置

### F01 · P1：资料事实归属分散（已确认结构问题）

Chat的四个服务直接查询`agent_personal_workspace_task_file_link/file/file_version`：

- `chat/.../service/ChatTypedDeliberationContextService.java`：effectiveSelectors约55、workspace约206。
- `chat/.../service/ChatSkillSourceAccessService.java`：workspace约74；read先验权、读取、后验权。
- `chat/.../service/ChatTypedInspectionContextService.java`：workspace约301。
- `chat/.../service/ChatInspectionAuthorityService.java`：workspaceRow约370，**FOR UPDATE**。

这些不是完全等价SQL：有普通读与锁定读、元数据与内容定位差异。其问题是数据所有者改授权/关联规则时需要跨域同步多个实现；不能简单文本去重，更不能把锁读改为无锁读。

**一期B2**只收敛前两处普通读到Agent窄端口；后两处及默认选择查询明确保留精确旧债。新同类实现不得继续查表。后续锁定读取必须另给事务合同。避免为“全清理”牺牲并发授权保护。

### F02 · P1：可恢复性作为字符串约定（已确认结构问题；历史误判已修）

`TaskSkillPolicyService.Snapshot(boolean allowed,String reasonCode,...)`；`TaskSkillPolicyServiceImpl.read`（约36–82）；`ChatActionExecutionService.requireAvailablePolicy`（约178）；`ChatDeliberationOutboxRelay.deliverClaim`。

当前已经把`RUNTIME_UNAVAILABLE`从永久Rejected中排除，不能再称线上仍存在相同BUG。但同一布尔拒绝承载授权拒绝与临时断线，消费者又按字符串分流，未来很容易重犯。**B1**在既有契约内增加内部类型化分类，保持wire和持久事实不变。

### F03 · P1：执行与装配边界过重（已确认风险，不按行数定罪）

- `PersonalWorkspaceExecutionServiceImpl`3274行：私人/任务/议事文件执行、受控图片、技能effect/result以及授权/存储恢复，末段又实现`SkillExecutionService`。
- `AgentWebSocketHandler`3453行：会话注册、连接能力、多个协议处理与发送；实现多个lookup接口。
- Runtime `agent-client.mjs`6769行：配置、registry、多个lane、连接生命周期与装配。
- Web `JuyiHall.vue`5087行，但约1965行是style；组件本来就应组合页面，不能把全部行数算业务复杂度。`useHallConversation.js`2331行才是异步状态重点。

真正风险：新增功能必须同时理解多个职责和隐含初始化顺序，`required=false`依赖缺失常到实际请求才暴露。**B3/B4先抽取窄职责**；不新增第二套引擎。大规模SkillService/WS拆分列后续，必须先列完整private调用闭包与事务边界，禁止先制造一个包含所有旧方法的Support类。

### F04 · P1：前端对历史做全量业务推导（确认实现，是否放宽需产品/合同决定）

`useHallTypedDeliberation.js:207–252`组合catalog、READY、failedReads、ordinaryChatRequests、emptyCancellation决定是否能发送及修改哪份成果；还deep watch目录恢复。历史不完整会影响当前操作，这是代码事实；所有这些限制是否该取消，不由“体验优化”推断。

**B3只提取已有读回调度，不改此决策**。后续若下沉服务端，须定义显式选中成果/澄清/普通聊天三种意图、失效版本与提交重验，并先改原型。禁止未经确认引入新context接口或自动选“最新图片”。

### F05 · P1：现有分层检查覆盖不足（已确认）

`api/build.gradle:127–189 validateLayering`检查api/mapper不依赖service、DAO位置及common特例，没有限制业务域间impl/mapper泄漏，也不检查service读取SecurityContext。

例：Chat控制器捕获`AgentServiceImpl.AgentBizException`；`HallActionDispatcher`依赖`AgentCommandCanonicalCodec`实现包。进一步解析还发现安全适配器、HostingHttp、SkillManagementCodec等实际service跨域依赖，不止两个import。

**B0**添加有具体风险的增量边界检查；现存例外逐路径/符号登记，不能全目录豁免。不要求一期全部消债，不把这些198条候选机械判错。

### F06 · P1：业务服务依赖线程登录环境（已确认违反既有分层意图）

API main service中5个文件直接读取`SecurityContextHolder`：
`AgentServiceImpl:938`、`AgentTaskCreationOperationServiceImpl:528`、`AgentTaskRequirementSnapshotServiceImpl:52`、`HallTaskCreationServiceImpl:125`、`PersonalWorkspaceExecutionServiceImpl:162`。

这是隐藏输入，HTTP、异步和测试重用成本高。**不是授权检查应删除**：必须先将已验证身份映射为框架无关上下文，并列全调用者；普通字符串scope不能冒充可信身份。本轮冻结新增此用法，现有迁移放后续安全专项。`reconfirm`本轮主源码搜索未见调用，不拿未接通路径解释全部现象。

### F07 · P2：Runtime“部分失败”日志语义不准（已确认）

`skill-conversation.mjs:167–208 poll`已逐execution隔离，多条成功后仍将firstError throw并携带processed；`agent-client.mjs:5684–5688`统一记录“poll unavailable”。

它不等于所有任务失败。**B4**返回结构化批结果，错误留execution上；只有共享身份/会话/存储错误抛到lane层。保持UNKNOWN不自动重发Provider。

### F08 · P1：源码基线与规格可交付状态脱节（已确认）

核对时`api/docs/interface-catalog/validation-policy.md`存在于工作树但**不在e7e6f7e3中，git status为??**；API AGENTS及interface-standard也有未提交修改。根SDD流程还同时保留旧“后端本机构建”等段落，虽被根最新规则覆盖，接续者只读旧段落仍易误用。

因此“本聊天说过/本机有文档”不等于“另一个Agent从develop能取得”。**B0要求固定规范版本和差异处置**，不擅自提交他人草稿，也不对脏树reset。文档与候选不一致是实施阻塞，要明说，不补造已合入证据。

### F09 · P2：测试入口累积，存在未执行错觉（已确认结构风险）

Agent build.gradle有24个字面sourceSets.create入口（990行）；Chat有13个（565行）；还存在其他声明方式。Root CI selector显式枚举；Web有release/assets/all。

定向sourceSet是减少无关历史编译的合理措施，不是都应删除。风险是新增测试文件未进入实际Run却被声称通过，或迁移类名后旧selector遗漏。**B0/B5核对实际报告与selector绑定**，不增加第N个临时sourceSet，不以清理名义删除ACL/资金/幂等回归。

### F10 · P2：领域命名和实际数据归属不一致（确认耦合，迁移方案待专项）

Agent hosting/position/skill多处用Economy mapper；`SkillMarketplaceService`同时管理授权/购买意图与资金posting，本地REQUIRED事务是已有正确机制。`SkillMarketplaceConfiguration`还依赖Economy schema initializer；多个技能文件读取Economy中的PlatformSkillPackageCatalog。

不应“删掉economy-service依赖”后用反射绕过。长期按数据owner拆出稳定API和内部适配器；资金提交仍由Economy持有，权益/安装生命周期需先明确归属，不迁表、不分布式化。本期禁止新增跨域mapper，不搬当前资金事务。

### F11 · P2：未实现/失败被空值掩盖的残留（确认源码，不声称线上发生）

`chat/.../memory/MemoryRepositoryImpl.java:279–297 deleteOldDocuments`只构造SearchRequest并打日志，没有执行删除；全main搜索仅接口及实现命中，无已发现调用。`countByJiacn:301–317`异常返回0，无法区分不可用与零条。

这是接口表达不诚实的债务，不是当前知识库所有读写未通。真正embedding写入和检索已有失败抛出及维度检查。后续先核调用方，再删除未用空实现或明确unsupported；统计失败改显式不可用。**本包不执行清库、不改变保留期限、不增加自动清理功能**。

## 4. 已有正确机制，不得为了“优化”删除

- 42个`SchemaInitializer` main类均标注`schema-maintenance`。不能指控应用每次正常启动都跑这42个DDL；实际profile启用属于运维验证。
- 模块声明依赖没有检测到环；Bean装配是否有环另论。
- Outbox是持久扫描，WS/SSE只是交付/观察渠道；ChatActionDispatch明确不在锁事务内做包读取/Provider执行。
- Web已有inflight合并、generation/scope guard、250ms读回去抖、终态不退回运行态；B3是保留这些机制并收敛owner。
- Runtime已有effect持久记录和不确定结果隔离；不能用“自动重试更可靠”绕开未知副作用。
- 任务、会话、执行、交付各自的锁和摘要保护不是重复校验的同义词。

## 5. 为什么前面的局部修复不够

直接原因各不相同；共享架构原因是**契约没有一个可执行的事实边界**。单个Bug修了，旁路仍在复制规则；文档描述了目标，却未把目标转换成允许依赖、状态写入者、错误分类和实际测试选择。再加上规范未入固定源码，下一次开发无法完整复现约束。

对策不是加更多审批：单Owner完成一条纵向切片，把调用方一起改完、旧分支一起删掉、关键回归真实执行。验收以减少重复决策及保持行为为准，不以新增文件数或测试数为准。

## 6. 剩余未知和后续顺序

1. 一期B0–B4完成后再设计SkillExecutionService职责提取；必须附每个移动方法的调用者/事务/DAO列表，不能只有新类名。
2. 可信身份上下文迁移与Economy权益归属属于后续安全/事务专项，不在一期借道修改。
3. 前端操作投影下沉若改变可发送行为，需要独立业务合同与最新原型。
4. 并发负载、长断网、进程崩溃、Provider扣费次数、现行生产配置/所有业务路径，本次未重新实测。既有task526/529图片与短断连回归仅是历史证据，不覆盖这些未知。
5. 全局协议迁移、历史数据修复、校验删除任务有独立规格与脏工作区，先协调；不以本方案宣布这些任务已完成。
