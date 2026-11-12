# 环境租户灰度：会话决策、交付边界与冻结剩余项

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：环境租户隔离与冻结剩余项。**

### 责任与业务流程
API配置提供业务tenant；公共持久化负责SQL隔离；独立存储和后台入口补真实绕过点。

环境配置→入口一致性准入→可信业务上下文→公共隔离查询/领取→业务权限。

### 明确边界
不写死tenant0/1，不让请求覆盖配置；全局账号与业务租户分开；用户已冻结未实施范围，本次规格整理不重新授权。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
切换配置、跨租户查询/领取/写入隔离、全局身份不复制、主键访问不绕业务权限；现有已交付与冻结列表分开。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


记录日期：2026-10-31（Asia/Shanghai）。Owner：FULL-TENANT-GRAY-20261029。

**状态：已开发 API 批次已合入 develop、构建并部署核验通过；全业务灰度未完成，未实施部分冻结。** 本文件是本次会话的接续规格，不是新的开发、迁移或发布授权。用户最终要求“没改的就不要改了”；后续授权只闭环已开发候选。2026-10-31仅整理文档，没有重新查询远端/生产，不把下述历史核验称作今天的最新状态。

## 1. 目标与已确定规则

- 业务租户用于环境数据隔离，支持本地功能验证。`tenant_id=1`是灰度示例，生产`0`是已部署配置值，不能成为业务语义常量。目标是任意合法配置值，不是写死两个环境；**目标不等于所有残留已清理**。
- 业务 tenant 的权威来源是后端环境配置`cyf.security.fixed-tenant.tenant-id`，不是 OAuth 客户端或用户的永久属性。外部 scope 仅做一致性准入，不能覆盖环境；认证身份仍承担用户/client识别和授权。
- `user_info`与`oauth_client`属于全局身份；不以业务租户复制账号。删除`user_info.client_id/tenant_id`、`oauth_client.tenant_id`的方向已落实到本次核验基线；积分使用 point 模块的`point_account`，业务成员关系独立保存。不能再把这些删除列列为本轮未完成项。
- 公共定义按来源、版本及公开语义确定，不借用生产tenant0作为所有环境公共目录。公共persona定义与租户私有覆盖分开；运行实体、用户数据不因标为SYSTEM就跨租户共享。其他目录须依实际用途分类，不能把全部SYSTEM对象一刀切为公共数据。
- 历史数据不做全量迁移；遵循“没有jiacn就不迁”，不猜测owner/tenant、不自动重放任务，不把旧迁移授权沿用到新环境。
- 用户不要求本线程验收灰度环境；本批交付重点为已开发代码合入、固定制品发布及生产核验，不等于承诺全业务灰度开放。

### 单一责任层与性能

| 责任层 | 本次固定约束 |
| --- | --- |
| 认证/入口 | 一次生成可信上下文；校验协议和scope一致性，不在Controller逐个重复JWT/tenant解析 |
| 业务服务 | 保留权限、资源关系、状态机、事务、幂等；不重复公共持久化已承担的租户过滤 |
| 持久化/存储 | 复用公共SQL隔离；明确排除全局身份和公共定义；原生SQL、文件/索引各适配器承担实际绕过点 |
| 后台/消息 | 从配置或认证消息取得可信上下文；排序、LIMIT、领取和锁定前分区，不跨域领取后内存过滤 |
| Runtime/bridge | 执行合同及目录、进程、身份、会话、文件、状态隔离；不复制API业务权限/状态机 |
| Web | 展示权威结果；契约不变不改前端，不给用户提供覆盖环境tenant的入口 |

`selectById/updateById/deleteById`及批量接口在公共隔离或可靠授权已覆盖时保留，不逐个加tenant参数。规则在责任层集中测试，业务测试保留业务风险，不每层堆同一防御矩阵。不新增框架、Reviewer、审批或门禁。避免逐行过滤、N+1预查询及无依据索引；MySQL执行计划/索引效果须有真实证据，不用H2或单测冒充。

规范依赖：[项目规则](../../AGENTS.md)“分层职责与最小联动”、[接口规范](../../api/docs/interface-standard.md)、[RB-1](../juyiting-skill-execution/responsibility-boundaries.md)。旧[单租户规格](../single-tenant-role-isolation/spec.md)的字面0/JWT租户/tenant0公共目录/全库归零是历史迁移口径，不再作为新灰度开发指令；owner授权和原证据仍保留。

## 2. 已交付批次（历史事实，不是今日重新观测）

| 项目 | 2026-10-30最终证据 |
| --- | --- |
| API develop commit | `5c2a2e45d4def3a1e90de98fc0166627d0fc21fd` |
| API tree | `7ece4263737f4185aba33bfaa564ee1b4d05c2bd` |
| Flow | `5260799/409 SUCCESS`；4446项：4260通过、186跳过、0失败/错误；validateLayering、fresh bootJar、打包上传通过 |
| 制品SHA-256 | `9496c87afa217e23e5e5790a9ca1bb120d3f31e9f17710c2e86d880520b00c0a` |
| JAR SHA-256 | `8f4d3b7b227199d04700810ef3cc9b583d8f8d0defc02095518f98d27ab83909` |
| 安装/核验 | 23:04 +08:00最终核验；`/home/isp/hosts/cyf/api/cyf-api-kit.jar`，PID415368，摘要MATCH、HEALTH=UP，安装记录installed、发布记录verified |
| 生产抽验 | PKCE登录、`/user/my`、生产环境scope、积分与DB一致、Agent persona目录/map/capabilities/list通过；不是生产全部写流程验收 |
| 配置/数据 | 仅补显式tenant配置`0`；保留MIME/OAuth allowlist。无灰度DDL、历史回填、业务迁移；安装器检查既有表等价未改表 |
| 主机修复 | 根仓develop `2072aac3`：中断已恢复健康时，精确失败记录摘要绑定的一次性授权重试；6项新回归+5项锁回归通过；复用409制品安装成功 |

已改scope链路及直接验证修复包括：统一进程policy、Chat发现/relay收口、技能版本owner误作tenant修正、恢复发现先分区、persona公共定义/私有覆盖及binding旧联接收口；最终修复Runtime统计tenant取值和WebSocket报告使用已认证会话scope，支持正确的requestId/occurredAt投影。旧测试fixture和错误码断言失败已在409闭环，不能把407/408的失败再列为待修；历史失败Run不改标成功。

**生产不是全程零中断**：首次安装143/TERM后，原流程恢复旧JAR健康，再按原锁和备份链复用相同制品完成。TERM来源未查明，见下方运维遗留。无Web/Runtime本批源码修改或Runtime重启，无付费Provider调用，无重复改图/文件生成请求。

发布证据目录：`/home/isp/state/cyf-full-tenant-gray-20261029/verify-release-20261030/`，关键文件为`production-verification-final.json`、`test-summary-409.json`、`artifact-integrity-409.json`、`production-record-after.json`、`versioned-release-after.json`、`production-columns.json`、`schema-postinstall-no-change.json`。具体过程及恢复见[主handoff §24](../../docs/implementation/handoffs/FULL-TENANT-GRAY-20261030-ANALYSIS.md#24-本批交付闭环2026-10-30-2304生产核验通过)。

## 3. 未完成开发：冻结保留，不自动继续实施

下列按责任边界归并，不是剩余文件数/工期承诺。API入口均相对`/home/isp/wsps/cyf/api/`，以§2固定提交为准，不以当前其他Owner脏工作区代替发布源码。2026-10-31重新静态核对了该提交的Task插件及UserController；其余项沿用明确标注的历史分析边界。

| 项目/状态 | 代码或调查入口 | 最小后续方案与验收（重新授权后） |
| --- | --- | --- |
| 全业务SQL公共隔离：**未完成** | `task/jia-task-service/src/main/java/cn/jia/task/config/TaskTenantConfiguration.java`；`common/jia-common-mapper/src/main/java/cn/jia/common/dao/BaseDaoImpl.java`；原生mapper | 发布插件只覆盖`cn.jia.task.mapper`及`task_plan/task_item/v_task_item`。先对实际表/语句分类，复用一个公共装配；集中覆盖显式INSERT tenant、UPDATE改变分区、分页/JOIN、真实生产插件顺序；全局身份删除清理成员关系不得机械限为当前tenant。不要改遍继承DAO |
| `/user/my`双响应及legacy属性：**未完成** | `user/jia-user-service/src/main/java/cn/jia/user/api/UserController.java#userInfo`，`UserOwnIdentityRealMapperTest`、`UserLegacyIdentityCompatibilityTest` | 固定提交仍有`legacy-single-tenant-id:0`和UserEntity/CurrentUserIdentityDTO分支。以后统一完整业务投影、积分取point模块，保留脱敏与授权；真实契约不变不改Web |
| 其他固定0/历史兼容/SYSTEM运行实体：**尚未全量清理** | 既有[代码库存](../../docs/implementation/handoffs/FULL-TENANT-GRAY-20261030-CODE-REMAINDER.md)及API `docs/minimal-tenant-grey.md`；相关业务SQL/CHECK | 对固定提交区分真实硬编码、配置示例、测试数字、owner哨兵及历史只读事实，修实际边界。已有policy/恢复/WS修复不重列；旧minimal-grey说明含过期兼容口径，不能照抄启动参数或据此宣称开放全部路由 |
| 非SQL/独立入口：**覆盖证据未闭合，不能全部判定为未编码** | Memory/Archive适配器、JdbcTemplate stores、文件/索引/缓存、队列vhost与剩余后台入口；主handoff §20 | 复用各存储适配器分区；只补确证绕过点，后台先分区再排序/LIMIT/锁。已有显式安全SQL不重写；测试实际跨环境读写和领取，不机械透传全链scope |
| Runtime独立灰度安装：**本批未交付** | Runtime仓库`shell/cyf_agent_runtime_v1_install.sh`及两份`cyf-agent-runtime-v1@.service`（历史分析基线`d0c35270cf9164a1aa7e1247365e716d6e0be43f`，本次未重查Runtime源码） | 复用同一程序与已有target参数，独立app根/unit/配置/state/HOME/身份/会话/ACK及监听资源；生产默认根不动。`/home/isp/apps/cyf-agent-runtime-v1-grey`仅约定示例，不代表已安装；不复制生产授权与运行事实，不另造一套业务Runtime |

**源码存在但尚未执行的维护候选**：API `agent/jia-agent-mapper/src/main/resources/db/`下的`agent-identity-business-tenant-20261030.sql`、`agent-task-execution-grant-tenant-20261030.sql`、`agent-execution-report-tenant-20261030.sql`、`agent-personal-workspace-execution-tenant-20261030.sql`、`agent-task-creation-tenant-20261030.sql`，以及`agent/jia-agent-service/src/main/resources/db/agent-personal-workspace-tenant-links-20261029.sql`等。脚本写好不等于目标数据库已应用；未来须对固定目标检查CHECK、唯一键、索引和授权/备份范围，不能全量执行旧脚本或回填。生产0此次没有执行这些灰度迁移。

## 4. 未验证与运维遗留（不混作代码未完成）

- 灰度全业务E2E、独立Runtime灰度并行运行未验证：用户明确不要求本线程追加验收；minimal-grey既有限制不能因本批生产抽验通过而解除。
- 186项skip不是186个缺陷，也不是通过；详细条件见固定Run测试报告。测试客户端未签发refresh token，所以refresh未验；不能算refresh故障。
- MySQL实际collation/EXPLAIN、索引和主要后台查询性能证据未全闭环；既有测试不替代生产数据库性能证明，不新增无依据时限或资源门禁。
- 首次安装143/TERM信号来源未归因。恢复及同制品重试已经完成，信号来源调查独立冻结，不作为再次发布/全链治理理由。
- 反向锁序死锁是用户已明确排除的问题，不重开为灰度必改项；不动其他Owner任务、锁或安装。生产抽验通过不代表排除了所有未观测风险。

## 5. 接续与成本约束

1. **先读本文件，再看历史handoff**。旧93文件、353历史表、130实体及80 DAO统计是调查库存，不是当前剩余量；旧“未编译/失败/待发布”由§2精确证据覆盖，但未实施功能没有因此完成。
2. 当前只记录，不触发Flow/安装/重启/DDL，不修改业务代码。后续若重新授权，只选明确冻结项；先固定实际源码/目标，核对责任层与最小依赖，不重启无限全量整改。
3. Flow只在worker做必要重型测试、构建、打包、上传即结束；不SSH/VMDeploy调用主机，不监听主机安装或验收。每Run准备到上传终态总上限600秒，不拆Run规避、不抢他人配置/任务。
4. 本地固定源码生成不可变制品，按coordinator→release→lifecycle锁、身份/ACL、摘要、备份及恢复流程安装。精确源码/测试/制品一致时复用；下载/安装重试、文档、重启不重复构建。此规则不重新开放已冻结灰度范围。
5. develop合入不自动授权部署。源码、测试、安装、健康、业务抽验分别报告。恢复重试规则见[发布策略](../../docs/aliyun-flow-cicd-strategy.md)，原失败保留，不能伪报新Run或删掉失败记录。
6. 本任务隔离worktree已清理；当前根仓/API有其他任务修改，不能reset、全量stage或覆盖。证据继续使用原路径，不新建并行任务台账。

## 旧单租户专题承接

个人owner与角色资源授权仍独立于环境租户：不能用同tenant代替个人授权；角色活跃绑定及唯一约束按本专题实际合同维护。旧[单租户迁移](../single-tenant-role-isolation/spec.md)退役为历史，禁止重跑全库归零、旧两任务迁移或按旧指令删除不明归属数据。原快照、审计、冻结剩余和未知项仍按原范围保留。
