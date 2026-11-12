# 典籍阁 Agent 任职与内容维护：总体方案与详细设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：典籍任职、资料整理与受控内容维护。**

### 最小责任链
API管理任职/版本/发布权限和事实；模型按技能编排；工具实现内容协议；bridge只执行隔离。

明确任务与任职授权→模型调用获准通用内容工具→草稿/版本→受控发布→读取发布事实。

### 实施约束
任职、技能安装、任务准入各自独立；不按好汉显示名或技能名硬编码通用Runtime，不向Agent暴露数据库凭据。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


**版本：D2；日期：2026-09-28；状态：ready / 可交接实施，从 M0 基线映射开始。下文是目标合同，不是已实现能力；未派发、未测试、未部署。**

> D2 已吸收兼容性复核：不扩旧 ItemRef、不建第二套调度/文件系统、保留直达吴用、区分 Runtime 协议、隔离私人来源与公开发布。实施入口见[Agent 交接](handoff.md)，共享边界见 §18；D1 风险记录保留在[影响评估](impact-assessment.md)。

## 0. 阅读导航与决策摘要

- §1 源码差距；§2 产品与架构；§3 身份/任职/授权；§4 技能与客户端；§5 内容与状态机。
- §6 数据模型；§7 API；§8 宋江工具；§9 异步协议；§10 事务和恢复。
- §11 来源与内容安全；§12 前端；§13 阅读兼容与迁移；§14 运维；§15 实施与验收；§16 待冻结事项。

关键选择：

| 问题 | 推荐决策 | 不采用的方式 |
| --- | --- | --- |
| 谁对话、谁执行 | 宋江受理协调或直接交办，任职 Agent 执行 | 所有业务都塞进宋江提示词 |
| 怎么维护 | 受控 HTTP API / 同一应用服务 | Agent 直连 DB、执行生产 SQL |
| 技能是否等于权限 | 不等于；安装证明、任职、作业授权同时检查 | abilities 字符串即管理员 |
| 是否每次人工发布 | 默认仅编修，可一次显式预授权自动发布 | 每本书强制新增审批流，或默认全自动越权 |
| 内容发布 | 固定来源 → 草稿 → 校验 → 不可变版本 → 原子激活 | 直接覆盖线上章节 |
| 是否微服务化 | 留在已有 archive 域，复用既有 Agent 传输 | 为首期新增独立 CMS 服务/消息系统 |
| 是否依赖技能交易 | 首期平台配置技能，无资金动作 | 为安装维护技能伪造订单或开启收费市场 |
| 第一版规模 | 一个编修岗位、一个技能、一部新增书端到端 | 全站官职/多人会签/交易平台 |

## 1. 经源码核对的现状与必要改动

精确来源、commit、blob/hash 见 [源码基线](source-baseline.md) 与 [审计清单](source-audit.json)。远程跟踪 refs 本轮未 fetch，不代表线上；Web 本地 checkout 不完整代表现行 reader，实现前须另冻结集成基线。

| 位置 | 当前观察 | 本功能的必要改动 |
| --- | --- | --- |
| `ArchiveManifestLoader` | 固定水浒书名、work/edition、哈希、120 回等 | 保留旧种子校验器；新增通用 manifest 校验器，不修改种子摘要来冒充新书 |
| `archive-schema.sql` / `ArchiveSchemaCatalog` | 历史审计：DB CHECK固定120回、旧启动精确比对schema | 当前不新增/依赖CHECK；业务规则由服务层落实，同步DDL/catalog/启动器，不自动恢复旧CHECK；已有生产约束仅授权迁移 |
| `ArchiveBootstrap` / importer | 启动导入且可能重新激活种子版本 | 种子只在空书目初始化；重启不能覆盖已发布的新 active 指针 |
| `ArchiveReaderServiceImpl` | 单书 catalog；READY 与固定摘要/计数绑定；只允许当前 active | 新书架/单书目录；按发布记录读取历史版本；不把 READY 等同公开 |
| `JdbcArchivePersonalDataStore` | `lockActiveEdition` SQL 写死 shuihuzhuan | 统一“可读已发布版本”解析，保留 owner 隔离、锚点和 CAS |
| `ArchiveTextSelectionValidator` | 固定 editionId 和 c001…c120 形状 | 由路径指定 edition，按真实目录/段落验证；不从文本推断版本 |
| `ChatClientConfig` / `AgentTools` | 默认工具包含 Agent 工具和通用 shell 等 | 为典籍协调路径构造受限请求级工具集合；服务端权限不能依赖工具可见性 |
| `AgentRuntimeAuthenticationFilter` | native method/path allowlist，无典籍写入口 | 精确新增方法/路径；仍禁止转入用户 OAuth 通道 |
| `InstalledSkillEntitlementLookup` | 已安装技能查询依赖市场有效订单/授权 | 新平台配置安装事实适配，不复用或伪造 ACTIVE 订单 |
| Web 跟踪分支 reader | 单 catalog、进度/手札/提问已有处理 | 书架、管理入口与按书/版本缓存；保留旧 reader 的身份清理与恢复行为 |

**范围因此不是“一个 @Tool + 一本 JSON”，而是内容域通用化、最小职责授权和可靠执行三个闭环。**

## 2. 产品结构与模块边界

### 2.1 业务链路

```text
书库管理者 ── 任命/授权 ──> 典籍阁编修（真实 Agent ID，例如吴用）
       │                         │ 安装 archive-maintainer
       └─ 宋江/直达 ──> 维护单 ─> 任职与技能校验 ─> 既有命令传输
                                               │
                                吴用：取授权来源、整理、提交草稿
                                               │
                                       受控内容管理 API
                                               │
                             草稿校验 → 封存 → 持久化 READY
                                               │
                              有权发布 → 原子激活 + 审计/事件
                                               │
                          读回核验 → 宋江回报 → 典籍阁阅读
```

### 2.2 后端归属

- 内容、书库任职和维护单放在现有 archive 域：`/home/isp/wsps/cyf/api/chat/jia-chat-{core,api,mapper,service}/` 对应 archive 包；不新起 CMS 服务。
- `ArchiveMaintenanceService` 负责用例；`ArchiveAppointmentService` 负责书库职责；`ArchivePublicationService` 负责封存/发布；`ArchiveContentValidator` 负责确定性校验；`ArchiveReadableEditionResolver` 供正文/私人数据/选文共用。
- Agent 域提供 `ArchiveAgentExecutionPort` 所需的身份、绑定版本、runtime、安装事实、命令发送能力。接口归属 `agent-api`，适配归属 `agent-service`；archive 依赖接口，不让 `agent-service` 反向依赖 `chat-service`。
- archive native Controller 可在 `chat-service`，复用已存在的 runtime principal；filter 仍在 `agent-service`。验证模块依赖图，禁止新增 service 循环。
- Agent 客户端版本化源码继续在 `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/`，不直接修改部署副本冒充源码交付。
- 管理表单与宋江工具调用同一应用服务。后端同进程无需绕一圈 HTTP；吴用外部进程通过 native HTTP API 调用。

### 2.3 维护单与既有任务的关系

- `archive_maintenance_job` 是本业务权威事实，负责章节校验、待发布和已发布状态。
- 默认不创建收费悬赏、不动钱包。首期独立典籍管理面板 + 原会话维护卡深链，**不扩展现有 ItemRef/OVERVIEW-v1 的 sourceType、kind、nextAction、mark 或计数合同**。维护单不伪装 TASK/PRIVATE；未来关联正式任务用显式 linkedTaskId，列表扩展另行版本化设计，不属于本期。
- 会话维护卡由业务 outbox 幂等通知更新；卡片丢失不影响内容事实，不新增独立聊天事件日志。聊天、客户端 inbox completed、work.result 均不能直接置为 PUBLISHED。
- 第一版无任职时提示管理者完成任命；不默认由宋江越过岗位执行。管理者始终可从管理 UI 完成修订/发布作为正常操作入口，不是 Agent 越权后门。

## 3. 身份、任职与权限详设

### 3.1 三种身份与两种资源范围

| 身份 | 身份来源 | 可做什么 |
| --- | --- | --- |
| 普通读者 | 服务端认证用户 scope | 已公开典籍阅读、自己的进度/手札；可在聊天中提出建议，不形成执行单 |
| 书库管理者 | 认证用户 + 持久书库管理授权 | 同 owner 任命/撤任、创建维护单、修订、发布、下架、查询审计 |
| 宋江协调器 | 服务端解析的用户会话 + canonical coordinator | 在当前用户可授权范围内创建/查询维护单；没有独立管理员特权 |
| 任职 Agent | 受信 runtime principal + 当前 binding + 任职 | 仅当前作业授权的来源、草稿和操作；不能任命或扩权 |
| 后台导入 worker | 内部工作身份 + 持久作业授权 | 执行该作业确定性校验/导入；发布时复核原授权或新的管理者授权 |

内容读取范围和私人数据 owner 范围分开：公共书库可对已有允许访问的用户开放；私人手札仍按 `(tenantId, clientId, ownerJiacn)` 隔离。当前单租户值不能成为跳过 owner/client 校验的理由。

首期书库 `platform-classics` 可包含现有水浒；它是显式配置的公共内容集合。创建书库管理授权必须由已授权管理入口或受控配置完成，**不把任意普通 owner、角色名或首位登录者自动升级为书库管理员**。具体首任管理者是激活时待确认的真实身份，不写入本设计。

### 3.2 任职模型

岗位编码 `ARCHIVE_EDITOR`，显示“典籍阁编修”，每书库首期一个有效 slot。任职记录保留历史：

```json
{
  "appointmentId": "apt_example",
  "collectionId": "platform-classics",
  "roleCode": "ARCHIVE_EDITOR",
  "agentId": "agent_example",
  "bindingVersion": "17",
  "ownerScope": "derived-server-side-not-client-input",
  "workScope": {"mode": "COLLECTION"},
  "permissionProfile": "DRAFT_ONLY",
  "requiredSkill": {"key": "archive-maintainer", "version": "1.0.0", "packageSha256": "frozen-at-release"},
  "status": "ACTIVE",
  "revision": "1"
}
```

示例仅说明字段；SHA 必须是真实 64 位摘要，真实请求不接收 ownerScope。`workScope` 支持 `COLLECTION` / `EXPLICIT_WORKS`；后者不得新建未列明书目。任职权限变化形成新授权版本，不能复用旧 revision 悄悄扩大权限。

任职持久状态只有 `ACTIVE / REVOKED`；`待装技能 / 离线 / 就绪 / 换绑待重任` 是根据安装和当前身份计算的 readiness，不把在线状态当作权限事实。离线可任命，保持待就绪。

### 3.3 权限矩阵

| 操作 | 读者 | 协调器（用户有权时） | 编修 DRAFT_ONLY | 编修 PUBLISH_VALIDATED | 书库管理者 |
| --- | --- | --- | --- | --- | --- |
| 读公开版本 / 自己的阅读数据 | 是 | 按用户 | 无额外私人数据权 | 同左 | 按自己的 owner |
| 聊天中提出建议（不创建维护单） | 是 | 是 | 非岗位权限 | 非岗位权限 | 是 |
| 任命/撤任/更改岗位权限 | 否 | 首期不暴露写工具 | 否 | 否 | 是 |
| 创建维护单 | 否 | 是 | 仅执行已分配作业 | 同左 | 是 |
| 导入/改草稿/请求校验 | 否 | 不直接处理正文 | 作业范围内 | 作业范围内 | 是 |
| 发布指定已校验版本 | 否 | 首期不提供直接发布工具 | 否 | 作业允许 AUTO 时 | 是 |
| 下架 / 移交 / 恢复旧版本为默认 | 否 | 否 | 否 | 否 | 是 |
| 任意 SQL / DB 凭据 / 全量私人手札 | 否 | 否 | 否 | 否 | 此功能也不提供 |

有效权限为：**书库授权 ∩ 当前身份绑定 ∩ 有效任职 ∩ 本次作业授权 ∩ 操作允许状态**。技能安装是执行资格，不是上述权限的替代物。

### 3.4 Runtime 与作业授权

首期使用 legacy codex-ws-agent 的现有命令传输及 native AgentRuntime 认证适配。独立 Runtime v1 的 Bearer/session/heartbeat/ACK 不是同一协议；在其拥有已验证 command-channel adapter 前，本功能不向它投递执行命令，不把技术发布当 Agent 激活。凭据、profile、state 不跨协议复制。

- 原生通道复用 `AgentRuntimeAuthentication.Scope(tenantId, clientId, ownerJiacn, agentId, runtimeInstanceId)`，所有 scope 由服务端凭据解析。
- 创建作业时保存发起者、任职 id/revision、bindingVersion、实际 Agent、固定技能包、来源快照、书目范围和可执行动作；签发持久 `executionGrant` 记录，不把任意 scope 字符串当授权。
- native 请求至少同时验证 runtime、jobId、runId、commandId、attempt/epoch、grant、任职/管理授权版本和资源归属。URL 中的 ID 只能定位，不能授权。
- 首次成功 start 将在途执行绑定到 runtimeInstanceId；同实例重连可恢复。新实例/新绑定必须由服务端显式恢复流程生成新执行 epoch，旧实例请求被拒绝，不靠离线时长自动抢占。
- 原生凭据由受控 bridge 持有，不置入正文、模型提示词、manifest、工具返回值或普通日志。bridge 只接受固定操作和已绑定 job/run，不允许模型提供 origin/Authorization。
- 这不声称同 OS 用户下任意 shell 与凭据完全隔离；托管运行建议隔离执行身份/IPC，外部客户端视为不可信。即使客户端被控制，服务端仍限制其为该作业范围。
- 本功能不能向 Agent 发用户 JWT，也不能让 runtime 凭据访问任职、管理员或私人阅读接口。重复 header、路径编码歧义、Origin 请求继续按现有 native 策略拒绝。

### 3.5 撤销的线性化语义

撤任、管理授权撤销、换绑、取消与写入/发布共享授权行/作业行的事务序列化边界：先完成的事务生效。撤销提交前已提交的发布不伪称可撤回；撤销提交后所有后续写入/发布失败。队列通知用于加速 UI 收敛，不是撤销正确性的依赖。要移除已发布内容必须另执行有权下架操作。

## 4. 技能、安装与客户端

### 4.1 技能包内容（候选）

```text
archive-maintainer/
  SKILL.md                 # 流程、来源边界、工具用法、成功证据
  manifest.json            # key/version/协议版本/包摘要/受控操作声明
  scripts/parse-text.mjs    # 固定来源适配与章节/段落切分
  scripts/check-content.mjs # 本地诊断，不替代服务端校验
  schemas/content.json     # manifest、章节、来源 schema
  fixtures/                # 小型合法测试底本及确定性预期
```

- 主要操作为确定性脚本。模型可协助识别目录、解释异常、整理书目；不得生成缺失原文或自动改写原著。
- 本地检查只是提前反馈；服务端重新计算持久化内容摘要与章节完整性。
- skill permissions 只声明所需操作（如 `archive.draft.write`），不是授予这些操作。任职和作业授权单独生效。
- 运行绑定 exact skill version/package digest。升级包不能改变在途任务所用版本；新任务选择已验证包，撤销受损包使依赖任务暂停，而不是自动换版本继续。

### 4.2 不与收费市场绑定的安装路径

现有安装器的下载、摘要检查、目录安全、原子激活和持久回执机制可复用；但现有服务的市场订单、托管结算和退款状态不能照搬。

推荐新增平台配置安装源 `PLATFORM_PROVISIONED`，只允许受控平台技能目录；独立 `agent_platform_skill_installation` 记录。命令类型新增 `PLATFORM_SKILL_INSTALL` v1，保留现有 `SKILL_INSTALL` 合同原样，不把新字段塞进冻结 payload。

- 管理者同时是该 Agent owner 才能发起安装；显式目标 agentId/bindingVersion/skillVersion，不从 UI 选中态隐式取值。
- 无购买、银两扣减或退款；记录“平台配置”。安装确需额外收费资源时停留说明，不能从本方案推导付费授权。
- 安装回执必须来自当前受信 runtime/已注册传输身份，绑定 commandId、installationId、Agent、binding/runtime、包摘要、attempt/epoch 和服务端挑战；重放、跨源订单混用、摘要不符均拒绝。
- 平台发布的包必须有可验证发布者与完整性证明；安装证明记录认证来源与服务端确认。不能把“客户端说已安装”或目录存在当成证明，也不夸大安装证明为远程执行代码的绝对证明。
- 统一 InstalledSkillResolver 按 MARKET / PLATFORM_PROVISIONED 分派；`PlatformInstalledSkillResolver` 是新增来源适配器，不是另一套 registry/installer。deliverable skill 标签不等于安装事实、商业权益或岗位权限；维护成功不自动产生正式成果验收证据。适配器在服务端输出 `VERIFIED / PENDING / REVOKED / UNAVAILABLE`；与商业安装授权保持可插拔适配，不改资金表。
- 原始 SKILL_INSTALL 的签名/认证和安装安全要求不能降低。新 origin 的 proof canonicalization 和 challenge/密钥验证方案在 M0 合同阶段按现有注册安全实现冻结，不能用未认证普通 HTTP 回调替代。

### 4.3 独立业务执行命令

新增 `ARCHIVE_MAINTENANCE_EXECUTE` v1，属于统一执行入口的类型扩展，不建 archive 专用 scheduler/command polling。复用既有 `command.dispatch`、durable inbox、outbox、fencing 和 reconnect 机制。客户端必须声明协议支持；老客户端显示“需要更新典籍维护能力”，不能降级为自由 shell 或通用 WORKSPACE_FILE_EXECUTE 来绕过合同。

## 5. 内容模型与状态机

### 5.1 五种不同的事实

1. `Work`：作品书目；《三国演义》是一部作品，不同来源可以有多个版本。
2. `SourceSnapshot`：不可变原始文件、来源版本/获取方式、权利依据、SHA-256 与归一化规则。
3. `Draft`：可修改的编辑版本，带 revision 与来源快照；普通读者不可见。
4. `Edition`：已封存正文；editionId、段落字节、ID、manifest 不可修改。
5. `Publication`：该版本是否已经获授权发布、何时发布、谁操作；active 指针只是默认推荐版本，不代表其他已发布版本消失。

标题不作为数据库唯一身份。新 workId/editionId 由服务端分配；`canonicalKey` 在书库内唯一，用于来源明确后的作品去重。标题相同只产生相似项提示，不自动覆盖已有书。

### 5.2 草稿与作业状态

```text
草稿：EDITABLE → VALIDATING → VALIDATED → SEALED
                       └→ CHANGES_REQUIRED → EDITABLE
       VALIDATED --修改--> EDITABLE（旧校验结果失效）
       未发布草稿可 CANCELLED；SEALED 不再改，只能派生新草稿

维护单：WAITING_INPUT / WAITING_ASSIGNEE / WAITING_SKILL → QUEUED → RUNNING
       RUNNING → NEEDS_CHANGES → RUNNING
       RUNNING → AWAITING_PUBLISH → PUBLISHING → PUBLISHED
       有权 AUTO 跳过人工等待，但不跳过校验/封存/事务检查
       非终态 → SUSPENDED_AUTH / FAILED / CANCELLED
```

- Agent 离线表现为 QUEUED + `waitReason=AGENT_OFFLINE`；没有任职则 WAITING_ASSIGNEE，不自动挑一个有类似名字的 Agent。
- `AWAITING_PUBLISH` 表示草稿交付完成，**不等于上架完成**。
- `FAILED` 记录阶段、根因、可否重试；修复/新输入后显式 resume 创建新 attempt，不改旧失败事实。
- `SUSPENDED_AUTH` 必须由有权管理者重新授权恢复/移交；给旧任务换一个任职 ID 直接继续是不允许的。
- `PUBLISHING` 必须可查询 durable operation；超时显示状态待确认，不能标成发布失败再重发一个全新请求。

### 5.3 不可变版本与可见性

保留底层 `archive_edition.import_state=STAGING/READY`；新增 publication 状态 `PUBLISHED/WITHDRAWN`，无 publication 的 READY 版本仅内部可见。默认阅读依据 `archive_work.active_edition_id`；历史已发布且未下架版本通过 editionId 可读。

- 新版本激活：一次短事务把出版记录、active 指针、作业终态、审计/outbox 一起提交。
- 旧版本仍为 PUBLISHED，不重写私人数据。用户自愿切换新版，不能自动按段号迁移。
- 下架：管理者显式操作。已下架正文返回 410（先通过可见性检查）；私人笔记保留并提示引用内容已下架。选择新 active 或置空必须显式且原子，不默认退回旧版。
- 误发布纠正优先新版本向前修复；恢复旧版为默认是独立授权操作，不能作为自动保守回退。

### 5.4 正文与来源规范

`source.rawSha256` 针对原始字节；`normalizedSha256` 针对确定性变换结果；`manifestSha256` 针对规范化 manifest；block/paragraph 哈希针对最终 UTF-8 字节。规范算法须有版本和测试向量，不能依赖 Java/Node 默认对象 key 顺序碰巧相同。

第一版可采用 `canonical-json-v1`：递归按 Unicode 码点排序对象键、数组保序、UTF-8、无额外空白；无浮点数；schemaVersion、章节 ordinal 等有界整数按十进制 JSON 整数编码，64 位 revision/epoch/sequence 用规范十进制字符串；拒绝重复 JSON 键与非法 Unicode。后端和客户端用相同测试向量验证；旧种子原有摘要算法及数据保持不动。

只允许已声明的换行/编码处理，不默默繁简转换、删标点或改字。每个段落保留来源字节区间/适配器映射；映射无法建立时显示需人工校订。源文本中的目录、版权说明、页眉等被排除内容必须单独记录规则与实际区间，不能以“清洗”名义静默丢原文。

## 6. 数据模型与约束

下表是逻辑模型；DDL 在实现准备阶段按实际 schema/version 固定，不能将本表直接当生产迁移脚本。

| 表/实体 | 关键字段 | 约束与作用 |
| --- | --- | --- |
| `archive_collection` | collection_id, code, reader_scope_policy, revision | 书库可见性；首期一个公共经典库 |
| `archive_collection_manager` | collection_id, tenant_id, client_id, owner_jiacn, permissions, revision, revoked_at | 显式管理授权；不以 tenant 代替 owner |
| `archive_collection_work` | collection_id, work_id, canonical_key, revision | work 首期仅属一个 collection；collection+canonical_key 唯一 |
| `archive_appointment_slot` | collection_id, role_code, current_appointment_id, revision | collection+role 唯一；锁 slot 原子换任 |
| `archive_appointment` | id, slot, agent_id, owner scope, binding_version, profile, work_scope, skill ref, revision, state | 历史不可覆盖；同 slot 一有效任职由指针约束 |
| `agent_platform_skill_installation` | install_id, origin, target scope/binding/runtime, package digest, command/epoch, proof ref, state | 与市场 order 分离；安装重复/冲突幂等处理 |
| `archive_maintenance_job` | job_id, requester scope, collection/work, source refs, appointment snapshot, state, run/epoch, grant revision, revision | 权威业务事实；job 带完整精确范围 |
| `archive_job_run` | run_id, job_id, execution_ref, command_id, actor/runtime, package digest, attempt, execution_epoch, outcome | 业务关联与审计，不拥有独立队列/lease；execution_ref/command_id 绑定唯一；每次合法恢复保留历史 |
| `archive_source_snapshot` | source_id, collection, authorized_by, private object ref, raw digest/length, source metadata, rights basis, normalization version | 原始对象不可变；来源文件 ACL 不公开扩散 |
| `archive_draft` | draft_id, job_id, work_id, base_edition_id, source_id, revision, state, validated_revision, validation_digest | 修改 revision 必须失效旧校验 |
| `archive_draft_block` | draft_id, block_key, ordinal, title, immutable payload ref/digest, revision | draft+block_key/ordinal 唯一；按章提交，重复正文不静默覆盖 |
| `archive_validation` | validation_id, draft_id/revision, ruleset_version, source/manifest digest, findings, outcome | 不把 warning 伪成 error；固定候选可复用 |
| `archive_publication` | publication_id, work/edition, draft revision, manifest digest, actor, authorization snapshot, state, previous_active, published_at | edition 唯一出版记录；不可变正文引用 |
| `archive_operation` | scope+operation_key, method/path, request_hash, target, status, response snapshot | 幂等与未知结果查询 |
| `archive_event` | aggregate_id, sequence, schema_version, type, scoped payload, outbox state | aggregate+sequence 唯一；审计与投影/恢复事件 |

已有 `archive_work/edition/chapter/paragraph` 继续保存封存正文；进度/书签/手札/提问原表不搬移、不删除。表名前缀与 DAO 分层在 M0 检查现有命名避免冲突。后台任务可复用已有 durable job/outbox 基础设施，但不得把同一事实另存第二套不一致状态机。

主要数据库变化：

- `chapter_count = 120` 改为 `chapter_count >= 1`；chapter reader_ordinal 为正整数，与 chapter_number 相符，不再硬编码上界 120。
- 序言可缺省：preface count/bytes 均可为 0，存在时必须一致大于 0；reader 总数/字节仍等于各部分之和。
- 连续章节/段落、声明目录与实际目录相符等跨行条件由服务端验证，不伪装成单行 CHECK 可保证。
- 保留现有 PK/唯一索引/FK、二进制身份比较和不可变版本 ID；新增 collection 关联与权限查询必须一起联表验证，不能先按 edition 查正文再事后筛选。
- source 原始文件和草稿 payload 放已有受控对象/文件存储；DB 存摘要与引用。不可直接从 HTTP 提交绝对文件路径。草稿达到发布后复制/落入既有正文存储；不在 DB 事务内下载大文件。

## 7. API 合同

### 7.1 通用约定

- 用户管理入口 `/archive/admin/v1`，现有阅读入口 `/archive/v1`，原生执行入口 `/internal/archive/v1`。认证通道严格分开。
- 所有有副作用操作必须携带 `Idempotency-Key`；用户/内容编辑对已存在目标的更新同时带 `If-Match`。原生命令 start/failure 按精确 command/attempt/executionEpoch 与作业状态 CAS，不能把普通 UI ETag 代替执行归属；native 草稿/发布更新仍需 If-Match。ETag 由目标 ID+revision 生成；新建返回目标 ETag。
- 服务端先检查当前权限，再按 actor scope、方法/规范路径、key 查原操作；同 key 同请求重放原结果，同 key 异请求 409；第一次请求再检查 If-Match。这样已成功请求的重放不被自己的旧 ETag 错误拦住。
- HTTP 201 表示同步创建记录，不等于内容发布；202 必有 operationId/jobId 与可查询地址；JSON 不返回秘密。Job/operation 状态才是异步真相。
- 内部 64 位版本/序号/epoch 使用十进制字符串，避免 JS 精度损失。
- 请求字段显式白名单，拒绝未知权限/owner/tenant 字段、重复键和非法身份编码。UI 的隐藏按钮不是权限控制。

### 7.2 管理端接口（均为新增）

| 方法与 `/archive/admin/v1` 路径 | 权限/主要请求 | 返回 |
| --- | --- | --- |
| GET `/collections/{cid}/capabilities` | 当前用户可见性 | allowedActions、任职摘要、可用技能，不暴露他人秘密 |
| GET `/collections/{cid}/appointments` | 书库管理者 | 当前任职和历史分页 |
| POST `/collections/{cid}/appointments` | appoint；agentId, expectedBindingVersion, workScope, permissionProfile, exact skill ref；If-Match 为 slot ETag | 201 appointment + readiness |
| POST `/appointments/{id}/revoke` | appoint；reason；If-Match appointment | 200 revoked + affected job refs |
| POST `/collections/{cid}/source-snapshots` | source.prepare；fixedFileVersionRef 或 approvedProviderRef，rightsDeclaration | 202 source operation；冻结完成后返回 sourceId/digest |
| GET `/source-snapshots/{sid}` | 来源所属书库管理 + 已授权来源可见性 | provenance、digest、rights、processingStatus |
| POST `/collections/{cid}/jobs` | job.create；operation, existingWorkId 或 newWork, sourceId（允许缺失，此时仅待输入）, publicationMode, requestIntentId | 201 job；来源/任职未就绪时返回真实等待状态 |
| GET `/collections/{cid}/jobs` | management；state/cursor | 有权范围的分页列表 |
| GET `/jobs/{jid}` | job.read | 作业快照、阶段、revision、真实进度、draft/edition/result |
| POST `/jobs/{jid}/resolve-input` | job.manage；sourceId/newWork 等缺失输入；If-Match | 200 job；有效内容更新创建新候选，不改已封存来源 |
| POST `/jobs/{jid}/resume` | job.manage；reason, expected appointment/skill snapshot；If-Match | 202 新 run/epoch；不默默换 Agent |
| POST `/jobs/{jid}/reassign` | job.manage；newAppointmentId/revision；If-Match | 202；撤销旧执行授权、产生新 run，保留草稿 |
| POST `/jobs/{jid}/cancel` | job.manage；reason；If-Match | 200 cancelled 或已发布 409 |
| GET `/jobs/{jid}/draft` | job.read | 当前草稿及校验摘要 |
| GET `/drafts/{did}/blocks/{bid}` | draft.read | 管理预览，不进入公共阅读 API |
| PUT `/drafts/{did}/blocks/{bid}` | draft.write；chapter payload；If-Match draft | 200 新 draft revision |
| PATCH `/drafts/{did}` | draft.write；书目/目录允许字段；If-Match | 200；使旧校验失效 |
| POST `/drafts/{did}/validate` | draft.validate；If-Match | 202 validation operation |
| GET `/drafts/{did}/validation` | draft.read | 固定 revision 的检查结果、规则版本 |
| POST `/drafts/{did}/publish` | edition.publish；expectedDraftRevision, validationId/digest, expectedWorkRevision, expectedActiveEditionId（可 null）；If-Match draft | 202 publication operation |
| POST `/works/{wid}/editions/{eid}/withdraw` | edition.withdraw；reason, replacementActiveEditionId（可 null）；If-Match work | 200 可见性/默认指针结果 |
| GET `/jobs/{jid}/events?after={seq}` | job.read | 有序事件页，恢复用；非 SSE |
| GET `/operations/by-key` | key 通过 Idempotency-Key header；当前 actor 与资源权限 | 原请求 accepted/committed/failed；不存在返回 404，不等于在途 POST 未受理 |
| GET `/operations/{oid}` | 当前 actor/书库权限 | 操作快照与真实结果 |

首期 source 可先由管理者固定文件生成快照；来源缺失的自然语言需求只建 WAITING_INPUT 意图，不默认抓网络。管理员直接改草稿与 Agent 修改遵循同一个 ETag；不能覆盖在途操作。

### 7.3 原生执行接口（新增精确 allowlist）

以 `B=/internal/archive/v1/jobs/{jid}/runs/{rid}` 表示下表路径前缀；这是文档缩写，实际 filter 逐一匹配明确方法与规范 ID。

| 方法与路径 | 请求/行为 |
| --- | --- |
| POST `B/start` | commandId,messageId,attempt,executionEpoch；原子领取或重放 |
| GET `B/context` | 授权来源/书目/草稿/权限/固定包引用；不含用户 JWT |
| GET `B/sources/{sid}/content` | 只读已授权不可变来源；摘要及长度响应 |
| GET `B/draft` | 当前 revision、已导入章列表、摘要；用于断点恢复 |
| PUT `B/blocks/{bid}` | 内容批次 + Idempotency-Key + If-Match；仅当前 draft |
| POST `B/validate` | 校验当前 revision；202，服务端确定性检查 |
| GET `B/validation` | 当前/指定候选的校验结果 |
| POST `B/publish` | 仅 PUBLISH_VALIDATED 且 job=AUTO；绑定当前校验、expectedWorkRevision 和 expectedActive |
| POST `B/failure` | 结构化错误与诊断引用，不接受凭据/全量日志 |
| GET `B/result` | 当前执行对应 publication/validation 的权威结果 |

任何 native 请求都不能用 payload 指向别的 draft/collection/source 来越权。路径自身绑定目标，正文若冗余携带目标必须完全一致。Receipt 查询若 runtime/任职已撤销，仍拒绝旧身份；管理者通过管理 API 查询历史，不靠旧凭据读回。

平台安装另增用户 `POST /agent/platform-skills/installations`、`GET /agent/platform-skills/installations/{id}`，native 精确 `GET /internal/agent/platform-skills/installations/{id}/package`、`POST .../{id}/result`。其 scope/receipt 合同由平台安装包 M0 冻结，不能使用裸包 URL 或任意包路径。

### 7.4 读者接口与兼容

| 路径 | 设计 |
| --- | --- |
| GET `/archive/v1/catalog` | 保持旧单书返回结构；兼容映射原水浒默认入口，不直接改成数组 |
| GET `/archive/v1/works?cursor=...` | 新书架列表，items 含 workId/title/activeEdition；不含草稿 |
| GET `/archive/v1/works/{wid}/catalog` | 单书当前默认版本目录，结构沿用原 catalog |
| GET `/archive/v1/editions/{eid}/catalog` | 指定已发布版本目录，便于旧书签续读 |
| GET `/archive/v1/editions/{eid}/preface`、`/chapters/{bid}` | 沿用原路由；通用化版本可读校验；无序言返回可辨识 404，UI 不请求 |
| `/archive/v1/me/progress/{eid}`、bookmarks、notes | 原路径/body/CAS/幂等保持；底层验证器支持所有可读已发布版本 |
| POST `/archive/v1/editions/{eid}/questions` | 新版选文提问创建，editionId 在路径显式给定；body 复用原锚点语义 |
| `/archive/v1/me/questions` 原创建 | 兼容适配到旧水浒 edition；不把旧客户端锚点解释为别书 |
| `/archive/v1/me/questions/{qid}`、events、retry | 保留 owner 规则；新记录固定 edition/manifest，不随 active 更新 |

读请求在返正文前校验 collection reader scope + publication。404 隐藏无权资源；对已确认有可见权且被明确下架的版本返回 410。即使猜到 editionId，READY 但未发布的内容也不可读。

### 7.5 请求/响应示例

以下 POST `/archive/admin/v1/collections/platform-classics/jobs` 示例不含真实生产 ID：

```json
{
  "operation": "ADD_WORK",
  "newWork": {"canonicalKey": "sanguo-yanyi", "title": "三国演义", "language": "zh"},
  "sourceId": "src_example",
  "publicationMode": "MANUAL",
  "requestIntentId": "intent_example"
}
```

服务端查当前任职者，返回实际 agentId，不依赖宋江模型填写 owner。新书 ID 由服务端生成。

```json
{
  "jobId": "aj_example",
  "state": "QUEUED",
  "revision": "1",
  "assignedAgent": {"agentId": "agent_example", "displayName": "吴用"},
  "appointmentId": "apt_example",
  "publicationMode": "MANUAL",
  "result": null
}
```

PUT 章节的概念请求：`{blockType, blockKey, ordinal, title, paragraphs:[{ordinal,text,sourceRanges}], declaredDigest}`。段落 ID 由服务端按封存 edition/ordinal 生成；服务端计算字节/摘要，客户端 declaredDigest 只用于相互校验。

发布回执至少含：`publicationId, jobId, workId, editionId, manifestSha256, sourceSha256, chapterCount, paragraphCount, previousActiveEditionId, actorType, actorId, authorizationRevision, publishedAt, readbackState`。文本、完整原始文件、凭据不进入回执。阅读链接按前端实际路由构造，不能硬编码未实现 URL。

### 7.6 错误合同

| HTTP / code | 语义及下一步 |
| --- | --- |
| 400 `INVALID_REQUEST` | 结构/未知字段/非法编码；修正请求，不盲重试 |
| 401 `RUNTIME_UNAUTHENTICATED` | 凭据失效或不匹配；走正式重新认证流程 |
| 403 `ARCHIVE_ACTION_FORBIDDEN` | 已知范围内缺操作权；不能通过换工具绕过 |
| 404 `ARCHIVE_RESOURCE_NOT_FOUND` | 不存在或无权；不泄露归属 |
| 409 `IDEMPOTENCY_CONFLICT` | 同 key 不同意图；核对原意图，不能自动换 key 复制操作 |
| 409 `ASSIGNMENT_CHANGED` / `EXECUTION_FENCED` | 已换绑/移交/旧执行；由有权者恢复 |
| 409 `ACTIVE_EDITION_CHANGED` | 发布 CAS 冲突；展示新默认版，重新决定，不静默覆盖 |
| 412 `REVISION_MISMATCH` | 草稿/任职版本变化；加载差异合并 |
| 422 `CONTENT_VALIDATION_FAILED` | 返回固定 revision 检查项，修内容后再校验 |
| 428 `PRECONDITION_REQUIRED` | 缺失必要 If-Match/候选引用 |
| 503 `DEPENDENCY_UNAVAILABLE` | 实际存储/依赖失败；保留作业和已提交步骤，查操作后恢复 |

权限检查必须先于解释私有资源的细粒度错误。性能慢不是上述任何失败码的理由。

## 8. 宋江 @Tool 设计

首期仅增加三项协调工具：

| 拟议工具 | 模型可传参数 | 服务端注入/检查 | 结果 |
| --- | --- | --- | --- |
| `getArchiveMaintenanceContext` | collectionId | 当前用户、可信 coordinator 会话、collection 可见性 | 岗位/权限/来源缺口/可执行动作 |
| `requestArchiveMaintenance` | collectionId, operation, title/workId, sourceId, requestedPublicationMode | 用户权限、requestIntentId/幂等、真实任职、技能与来源 | jobId、真实状态、明确下一步 |
| `getArchiveMaintenanceJob` | jobId | 当前用户对 job 的可见性 | 进度、待办、权威结果 |

- 首期不给模型任命、授权升级、下架或直接编辑正文工具；相应操作通过明确管理 UI。以后自然语言授权可用结构化确认卡承载，但不得只从一句含糊回复推断。
- 发布模式上限来自服务端保存的用户确认意图或已明确授权的默认办理策略，并再与任职权限取交集。模型的 requestedPublicationMode 只能请求或收窄，不能把已固定的 MANUAL 改成 AUTO；授权 sourceId 也必须与意图/作业来源范围相符。
- `requestIntentId` 在 UI/服务端固定一次确认意图时生成。相同 conversation turn/tool-call 重试映射相同 intent，网络恢复不得重建 key。不同 turn 的相似请求展示已有维护单建议，不靠相似度强行合并。
- 可信用户/会话/协调器上下文从服务端传入，不出现在模型可生成参数中。可使用项目 Spring AI 版本支持的 ToolContext 或显式应用层上下文；按项目依赖实测，不借本功能默认升级框架。
- 只为该次典籍协调请求构造工具集合，不修改其他会话的默认能力。典籍协调路径不得携带默认 ShellTools、任意 URL 请求、SQL 等旁路工具；需要按请求实际构造工具集合，而非仅在 prompt 写“不要使用”。同一服务端授权仍覆盖工具、UI、native 三个入口。
- 宋江可解释等待、转交和结果，但只有读到 publication 回执及成功读回后才能说“已上架”。404/未知操作状态只能说“尚未确认”。

## 9. 命令、事件与断线恢复

### 9.1 命令 payload（新增类型，不改既有冻结类型）

不新增 `/internal/archive/v1/commands` 轮询端点。发现、投递、ACK、取消和 reconnect 由现有通道负责；下列 native 接口仅处理已绑定的内容作业。逐目标能力缺失时保留 QUEUED，`waitReason=CAPABILITY_UNSUPPORTED`，不转自由 shell。

`ARCHIVE_MAINTENANCE_EXECUTE` 的传输 envelope 沿用已验证的 commandId/messageId/targetAgentId/attempt/fencing/delivery epoch；业务 payload：

```json
{
  "schemaVersion": 1,
  "jobId": "aj_example",
  "runId": "ar_example",
  "executionEpoch": "1",
  "appointmentId": "apt_example",
  "appointmentRevision": "1",
  "bindingVersion": "17",
  "skillInstallationId": "psi_example",
  "skillPackageSha256": "actual-64-hex-required",
  "contextRef": "/internal/archive/v1/jobs/aj_example/runs/ar_example/context"
}
```

这是形状示例，不能直接投递。contextRef 必须由 client 固定 origin 与 job/run 重建并比较，不信任任意 URL。不得新增强制执行的性能 deadline；现有安全 credential/lease 生命周期与可续期机制继续按身份安全处理，不把它当成任务总耗时预算。

### 9.2 事件 envelope

```json
{
  "schemaVersion": 1,
  "eventId": "ae_example",
  "aggregateType": "ARCHIVE_MAINTENANCE_JOB",
  "aggregateId": "aj_example",
  "sequence": "12",
  "type": "ARCHIVE_VALIDATION_FINISHED",
  "jobRevision": "9",
  "data": {"validationId": "av_example", "draftRevision": "7", "outcome": "PASS"}
}
```

事件类型至少包括 `APPOINTMENT_CHANGED, JOB_CREATED, EXECUTION_STARTED, CHAPTER_IMPORTED, VALIDATION_FINISHED, PUBLICATION_COMMITTED, JOB_FAILED, JOB_CANCELLED, AUTHORIZATION_SUSPENDED`。事件不包含来源全文、私人手札、token；序号来自服务端事务，不信任客户端时间排序。

第一版 UI 采用 GET job 快照 + cursor 事件分页，复用现有聚义厅事件仅发“有变化”通知，不引入第二条必须存在的 SSE 通道。断线重连先取快照，再按 sequence 补事件；重复/乱序事件幂等。游标超过保留区间时返回 `RESYNC_REQUIRED` 和快照入口，不能伪造连续历史。

### 9.3 投递与恢复规则

- 至少一次投递；业务效果靠幂等键、唯一约束、草稿 revision、发布 CAS 保证，绝不宣称传输 exactly-once。
- 命令 ACK 只代表接收/开始；服务端 publication 才代表上架。
- 客户端在固定目录保留本 run 的章节处理断点与 digest；重连先 GET draft/result，对已提交同 digest 章节跳过重写。
- 用户离开页面、关闭 SSE/轮询不取消后台工作；显式取消才撤销执行授权。
- 已知 transient 错误按既有策略退避，先查询原操作；同输入同根因连续第二次失败进入 `blocked_root_cause` 诊断，不无限循环。修改候选/完成实际修复后新 bounded attempt。
- 互斥争用等待，不抢占、不 signal 其他进程。授权撤销或新的合法执行 epoch 拒绝旧写入是正确性控制，不是超时抢占。

## 10. 事务、幂等与失败恢复

### 10.1 外部 I/O 与 DB 事务分离

下载来源、模型调用、解析、对象上传在事务外完成。每章先写不可变临时对象并验证实际字节，再在短事务登记引用和 revision。DB 提交前对象已持久；进程崩溃最多留下未引用临时对象，不留下指向尚未成功上传对象的草稿条目。未引用对象清理只能按本功能对象命名空间和引用事实执行，不能按任意磁盘阈值删其他任务数据。

### 10.2 封存与发布

1. 以 draftRevision 冻结 candidate manifest 与来源/解析规则；VALIDATING 只检该快照。
2. 校验成功仅标记 VALIDATED；并发修改产生新 revision，使旧 validation 失效。
3. 发布请求核对候选后封存为 SEALED，服务端给 editionId；复制/导入段落分批进入 STAGING，每批持久化断点，重新读回校验后 READY。
4. READY 不公开；最后短事务重新核对当前授权、任职/绑定/包撤销状态（Agent 自动发布）或新的管理者授权（手动发布）、expectedWorkRevision + expectedActiveEditionId 和验证摘要。
5. 原子写 publication、switch active 并递增 workRevision、job=PUBLISHED、operation=COMMITTED、audit/outbox。workRevision 使用 collection_work 的版本字段，所有默认版/下架变更均递增，防止 active 指针 A→B→A 的 ABA 漏检。
6. publication/operation 保存独立 `readbackState=PENDING/PASSED/FAILED`、检查项和核验时间；读回目录和章内容做服务验收。PUBLISHED 是数据库发布事实，readbackState 是可读性证据，不合并成一个不透明成功标记。提交后读回失败显示“发布已提交，阅读核验异常”，不得标记“发布失败”并重复激活。

管理者可接管已撤任 Agent 留下的合法草稿。此时保存新的 human actor/authorization，不冒充原 Agent 发布，不复用其已撤销 grant；正文校验仍须匹配 exact candidate。

### 10.3 锁顺序与撤任竞态

首期单数据源事务方案优先；集成前验证实际 transaction manager 和数据源一致。新域统一顺序为：现有 Agent 身份根锁（按 Agent 域已冻结顺序）→ 书库管理授权/岗位 slot → appointment/平台安装 → job/run → draft → work → edition/publication。只读取不可变快照的步骤不持长锁。

跨域方法若既有顺序冲突，不得强行混用上述顺序；在 M0 调整为统一接口与明确锁次序后才能实现。不能拿到 work 锁后再回头调用会锁 runtime 的权限查询。事务外校验之后必须在提交前重新锁定授权版本，不能只做“先查一次权限”。

若实测跨数据源，本候选的单事务激活方案必须修订，不以跨服务异步事件宣称原子撤权；这是必要架构验证，不是可跳过的假设。

### 10.4 典型故障矩阵

| 故障点 | 持久事实 | 恢复动作 |
| --- | --- | --- |
| 来源下载中断 | source PREPARING，未成为可用来源 | 同 operation 查询后断点重试，不造新 source 内容 |
| 临时对象已写、DB 未提交 | 未引用对象 | 原 key 查询，再提交或有范围地清理 |
| 某章提交成功、响应丢失 | block revision/digest 已存在 | 同 key 重放/GET draft，不能再加一章 |
| 校验期间有人改草稿 | 旧 validation 指向旧 revision | 当前草稿回到 EDITABLE，旧结果不允许发布 |
| READY 后发布前宕机 | 版本未公开 | 有权恢复同 publication operation，不重复导入 |
| 发布事务提交、通知丢失 | publication/job 已 committed | outbox 重投、UI 快照收敛 |
| 两版本并发发布 | 只有一个 (expectedWorkRevision, expectedActive) CAS 成功 | 另一项 409 明确冲突，由管理者决定，不静默覆盖 |
| 撤任与发布并发 | 按授权/工作行锁线性化 | 撤任先则发布失败；发布先则保留事实，另行下架 |
| 书库 DB/对象存储真故障 | 保留精确阶段与已提交内容 | 归因后恢复；不绕过校验或锁伪报成功 |

## 11. 来源、版权声明与内容安全

### 11.1 《三国演义》来源冻结

按实际选择的底本记录：书名、署名、版本说明、语言/字形、提供者、来源定位与固定版本、实际目录、原始字节/摘要、权利声明及其依据、取得者和时间、处理规则。作品古老不自动证明任意现代校注/排版/译本可再发布；模型不能裁决来源权利。

首期推荐用户明确提供可用的纯文本底本，或平台已确认的固定来源适配器。来源身份/权利不清先 WAITING_INPUT，不抓取任意网站“补齐”。实际章回数来自底本；测试另含非 120 回小样本，证明真正通用化。

### 11.2 输入处理

私人文件 READ/执行输入授权与公共书库 PUBLICATION_USE 分开。创建 source snapshot 必须记录 sourceVersion + rawSha256 + 目标 collection + 用途授权引用；仅有读取权只能用于授权预览/草稿，不得发布。发布服务校验当前用途授权、固定来源及 exact candidate；来源正文、会话或技能不得扩大该授权。人工发布也不跳过来源用途校验。公开 API 不返回原始私人 source storageRef、owner、会话或任职 runtime。


- 第一版只接收声明支持的文本/结构化内容，使用确定性解码；拒绝不支持的压缩包/可执行格式，不把上传文件交给 shell 执行。
- 外部正文视为数据，段落中的“忽略规则/调用发布/读取密钥”等指令不得获得控制权。
- API 参数使用 allowlist 与结构化 schema，SQL 参数化；前端正文纯文本渲染，禁止未经净化的 v-html、任意远程脚本/图片加载。
- 若启用来源 URL 适配器，origin/provider 固定配置，逐跳重验证重定向与解析地址，禁止 loopback/private/link-local/云元数据访问；不允许正文携带 URL 触发附带凭据的请求。首期不支持的来源不给代理出口。
- 文件存储采用随机对象 ID、实际类型/字节校验、路径/符号链接隔离；任务仅获显式授权来源版本，不能扫描整个用户工作区。

### 11.3 校验分层（不加无依据门禁）

**必须阻止发布的真实正确性条件**：来源未固定/未获授权、内容或包摘要不符、章节/段落缺失或重复/乱序、目录与已确认底本不符、来源映射不完整且未经明确校订、引用不可访问、校验候选过期、无当前发布权、执行/锁归属失效。

**仅观测/提示**：与其他底本章数不同、文字风格、罕见字、相似章节、耗时、包/文件大小、资源占用。不会仅因 3 秒耗时、任意包大小、磁盘预留或“模型觉得不像原著”拒绝。

传输/解析的安全限制只使用实际支持格式、现存基础设施边界和有证据的资源条件；需要新增数值硬限制时必须另记实际问题、测量与最小推导，不能在本设计凭空指定 MB/秒上限。

## 12. 前端交互详设

### 12.1 典籍阁

读者保留“典籍阅读 / 案卷检索”分离；新增书架先列作品，进入后读指定 edition。管理者增加“内容维护”，只有服务端 capabilities 允许才显示写操作。

内容维护分三个页签：

1. **任职**：负责人、真实 Agent 标识、owner/binding 状态、技能 exact 版本、在线 readiness、授权范围；“任命/换任/撤任”。任命表单清楚区分“仅编修”与“校验后可自动发布”，后者不是默认勾选。
2. **维护单**：标题、负责人、阶段、实际完成章数/总数、阻碍、来源、发布模式；缺来源、离线、待装技能、待发布分别展示。
3. **版本与记录**：版本/来源/校验/发布者/摘要、修订差异、待发布预览；管理者可发布/下架；Agent 输出文字不是状态徽标来源。

### 12.2 宋江对话卡

“新增《三国演义》”返回结构化办理卡：`目标书库 / 来源底本 / 承办者 / 已有权限 / 本次发布模式 / 维护单状态`。缺项只问缺项，已有明确预授权和来源时直接建单执行，不重复请求无意义确认。

需要首次任命、扩大权限、确定来源时跳相应管理表单。普通读者看到“这需要书库管理者授权，当前未创建维护单”，不能看到伪造“吴用正在导入”。建议可留在原聊天中，但首期不新增建议队列，不承诺已进入管理者待办。卡片包含“查看维护单”“打开典籍”（仅已发布且读回正常）。

### 12.3 Reader 与个人数据

- store/cache key 至少包含 identity generation + collection/work + edition；不能共享上一身份的目录/进度或草稿。
- 切书/版本先安全处理当前进度队列，再获取目标版本的服务端进度后打开章节；不并行打开卷首并自动保存覆盖断点。
- 历史书签点击固定 editionId；提示“此为旧版”，可自愿打开新版首页，但不自动迁移锚点。
- 书架/目录 ETag 与 publication/active revision 关联；正文按 edition/manifest/block digest 缓存。权限更改及身份切换清理敏感缓存，不依赖缓存 TTL 撤权。
- 处理已有真实 CORS 边界：新增请求所用 Authorization、If-Match、Idempotency-Key 与 Content-Type；expose ETag 等实际所需响应头，不开放 wildcard 凭据。
- 移动竖屏、横屏、键盘缩高、返回路径、焦点恢复与已有布局规则保持；慢请求保留“处理中”，用户取消与身份切换取消单独处理。

建议新增（路径待按冻结 Web 基线核对）：
`/home/isp/wsps/cyf/web/src/components/juyiting/archive/ArchiveShelf.vue`、`ArchiveMaintenancePanel.vue`、`ArchiveAppointmentPanel.vue`、`ArchiveJobDetail.vue`、`ArchiveDraftPreview.vue`；composable `useArchiveShelf.js/useArchiveMaintenance.js`。已有 `LibraryPanel.vue/useArchiveReader.js` 定向扩展，不重建整套聚义厅。

## 13. 兼容、迁移与启用顺序

### 13.1 兼容目标

单租户严格沿用环境业务租户（当前为 tenant=0）及 owner/client 隔离，不增加旧 tenant=owner 兼容分支；环境租户口径见[环境租户规格](../full-tenant-gray/spec.md)，此处不另定义租户规则。下述 schema 桥接仅限典籍内容结构。

旧水浒 work/edition/block/paragraph ID、正文、摘要、个人数据不变；旧 `/catalog` 返回 shape 不变；新书使用新入口。已有选文问题的 edition/anchor 不重解释。只读权限、个人 owner 隔离、map/roster 分流和显式 task 目标保持。

### 13.2 分阶段迁移

1. **观察/冻结**：核对实际组件/source/client SHA、DB schema 版本和样本数据；当前文档 HEAD 不能直接作为发布基线。
2. **桥接版本**：按实际切换依赖准备不新增/依赖CHECK的候选，同步DDL/catalog/启动器和责任层回归；种子bootstrap存在时不夺回active。历史旧程序精确比对CHECK的风险须在迁移前核实，不为兼容恢复已退役约束。
3. **扩展迁移**：添加管理/草稿/发布旁表，登记旧书库关联与旧版 publication，业务层落实章回/序言规则；若目标库仍存在旧CHECK，按授权迁移删除，不启动清库。DDL 不假设跨语句事务原子；记录每步 schema 版本/校验摘要，可从实际状态恢复。
4. **原数据保护验证**：迁移前后固定段落/正文/私人数据样本的 ID/摘要和数量一致；不重算旧 manifest。使用 fixture 全量验证与生产授权的最小只读核验，不复制私人正文进日志。
5. **服务/客户端能力**：部署 native allowlist、平台安装、执行命令支持；未升级客户端清晰不可执行，不误报技能就绪。
6. **前端**：启用多书 reader 和管理功能可见性；旧客户端仍可读旧默认入口。
7. **小范围激活**：指定真实管理者、任职 Agent、来源快照和权限；按实际测试结果执行《三国演义》首个维护单。
8. **实际验收**：新增与旧书阅读、私人数据、选文、撤权、重放/宕机恢复全部通过后才宣称功能闭环。

任职、来源授权和首本公共上架均需要明确业务授权。本次“提供方案”不是激活授权。关闭新写入口是可恢复保护措施，不自动删除草稿/发布记录，不还原其他任务代码；默认向前修复。旧二进制回滚必须确认它支持新 schema，禁止直接回装导致启动失败。

## 14. 可观测性、费用与运维

- trace 链：conversation intent → job → run → command → source/draft/validation → edition/publication；存在平台安装记录时关联其安装身份。日志只记 ID/阶段/摘要/错误码，不记 token 或全文。
- 指标：待输入/待技能/离线等待数、实际来源处理耗时、每章导入耗时、校验耗时、发布事务耗时、失败根因、重放次数、权限拒绝、active CAS 冲突。性能目标与成功率/可用性分开。
- 超时只作为明确传输配置/实际故障信息；后台作业不因前端连接断开或剩余 SLO 预算不足取消。
- 第一版不收费安装、不设岗位工资、不创建 funded bounty。模型执行仍可能有既有模型成本；开始真实运行前核对已有额度/调用授权，超出范围需用户明确授权，不能用安装免费推导推理免费。
- 普通内容上架不需要每本重建/部署应用；只需受控内容发布事务。技能/协议/程序更新仍按组件正常发布。
- 开发验证遵循项目当前政策：默认本地固定干净源码、独立输出测试/构建/打包，按实际授权受控安装；使用现有适配器真实LOCAL来源，保留exact SHA/tree、测试与制品SHA-256，Gradle经orchestrator串行。不自动恢复Flow，不伪造Run。
- 不新增独立 Reviewer，不增未知固定资源/耗时硬门槛；部署互斥、实际健康、进程归属、可恢复安装保留。

## 15. 交付包与验收重点

实施拆分见 [tasks.md](tasks.md)，全部测试条件见 [acceptance.md](acceptance.md)。核心顺序：

`基线/授权合同 → 通用内容及可读版本 → 任职与 native ACL → 平台技能安装 → 作业/内容发布 → 客户端执行 → 宋江/前端 → 集成 → 授权激活`。

前端在 API DTO/错误/状态冻结后可并行，不能把 UI mock 通过当真实执行通过。P0 任职/ACL/事务/迁移由 critical_worker Owner 实施并自检；普通前端/集成由 balanced_worker；验证由 gpt_test_runner。角色是计划建议，不代表本轮创建或派发子任务。

## 16. 必须在实施/激活前冻结的事项

| 事项 | 本设计默认 | 冻结时机 |
| --- | --- | --- |
| 首任书库管理者和吴用真实 ID | 不猜，不从显示名推断 | 激活前，验证当前 owner/binding |
| 《三国演义》具体底本/来源/权利 | 用户提供文本或已批准来源快照；不默认 120 回 | 首本 source snapshot 创建前 |
| 任职发布权限 | DRAFT_ONLY，可显式 PUBLISH_VALIDATED | 任命时 |
| 技能安装证明的新 source 合同 | 平台配置、不碰资金表，复用安装安全机制 | M0，Client/API 同步冻结 |
| 原生认证/注册模式匹配 | 复用项目精确 runtime 认证，不造用户 token | M0，用实际部署 client 验证 |
| 模块事务与锁顺序 | 单数据源、授权/内容同事务检查 | M0，代码实现前确认 |
| API/Web/Client 集成基线 | source-audit 是观察，不是发布 pin | M0，从当前可复现 develop 冻结 |
| 既有工具调用框架能力 | 沿用项目依赖，验证上下文传播及工具隔离 | 宋江工具实现前 |

这些是具体目标和授权/集成条件，不是为了等待而增加 Reviewer、人工票据或性能门禁。设计可以继续推进，未提供具体生产目标时不执行真实任命和上架。

## 17. 第一版边界与门禁依据自检

- 固定来源/章节完整性检查来自“新增可阅读原著而非模型生成故事”的业务目标；hash/授权/事务检查沿用既有安全与版本不变性要求。
- schema 兼容、reader/私人数据/选文解耦来自 source-audit 中实际固定书目和 CHECK 的证据；不是为了通用化做全站重构。
- 新 `expectedWorkRevision` 是为消除默认版 A→B→A 后仅比较 ID 无法发现的并发修改；权限/锁/幂等都用精确事务版本，不添加性能 deadline。
- 不设置无来源的全文长度、包大小、磁盘/内存预留或总执行秒数门槛。已有真实传输安全边界保持，新增数值必须有实测问题与推导。
- 第一版只有一个岗位和一个技能；商业市场、全站任职、跨 owner 雇佣、建议队列、OCR 等不混入验收范围。平台安装和维护执行是安全边界所需的小型协议增量，而非另建 Agent 平台。


## 18. D2 共享边界与接入合同

### 18.1 三个入口、一个业务用例

- 管理 UI、宋江协调、直接 @任职 Agent/密议都调用同一 `ArchiveMaintenanceService.request`。直达路径不调用宋江，不把私人会话加入宋江上下文。
- 用户级请求必须由服务端构造 `ArchiveRequestContext={actorScope,requestIntentId,entryPoint,conversationRef?,targetAgentId?,confirmedPolicyRef}`；模型只能提供 §8 的业务参数。直达 targetAgentId 必须与当前任职匹配，不匹配只提示，不自动改派。
- 显式确认意图由受信业务层建立；聊天入口取 canonical request/turn 关联，UI 入口持久保存原 key。`(actorScope,requestIntentId)` 唯一，同意图跨重试/入口只返回原 job；异内容同 key 为 409。不同轮次的真实新意图不按文本相似度自动合并。
- 先校验当前权限再查幂等。创建 job、保存意图映射、业务 outbox 同事务；outbox 的 dispatchKey=`jobId/runId` 稳定。发送响应丢失后查原 command，不新建平行执行。
- 直接聊天中的普通答复不自动授予执行权。远端模型不能伪造用户上下文调用管理 API；结构化维护意图必须通过已验证的服务端受理入口。旧客户端不支持结构化意图时展示管理入口，不隐式换另一种执行路径。

### 18.2 唯一执行权威与模块端口

`ArchiveAgentExecutionPort` 位于 agent-api，archive 只依赖接口；agent-service 适配既有身份、安装、命令机制。逻辑方法如下，Java DTO 按 M0 对齐，不引入循环 service 依赖：

| 方法 | 输入 | 输出/责任 |
| --- | --- | --- |
| resolveTarget | 受信 actor、显式 Agent、bindingVersion、requiredCapabilities | 当前 canonical identity、可用协议和 readiness；不可见目标不返回内部信息 |
| resolveInstalledSkill | 同 scope/target + exact key/version/digest | 安装来源、安装记录 revision、有效状态；标签不能替代证明 |
| ensureExecution | 已授权 job/run、稳定 dispatchKey、grantRef、精确包/来源引用 | 唯一 executionRef/commandId/transportProfile；幂等调用不重复执行 |
| inspectExecution | 已授权 job/run 与绑定 executionRef | 真实 ACK/start/运行状态，不能推导 publication |
| fenceExecution | 有权取消/换绑、expectedEpoch、reason | 撤销旧执行写权；通知失败不影响事务授权检查 |

这些是接入既有能力的端口，不是必须新建的五套服务。通用传输只有一份 command/inbox/lease 真相；archive run 仅引用它。业务 job 可以跨多次 run 长期存在，AWAITING_PUBLISH/等待用户不长期持有 Agent lease。草稿执行完成和内容发布是不同阶段，人工发布使用新的管理员授权，不复用过期生产者凭据。

保留既有 PRIVATE WORKSPACE_FILE_EXECUTE 的 OUTPUT_COMMITTED + manifest + owner-safe 文件校验，不改变其 payload/回执或用它伪装典籍维护。本功能专用命令不自动创建正式悬赏、文件任务验收或钱包结算。

### 18.3 平台安装与协议协商

- 注册能力是精确版本集合：支持 PLATFORM_SKILL_INSTALL/v1、ARCHIVE_MAINTENANCE_EXECUTE/v1 及其 native adapter。服务端在受理和实际投递前均读取目标能力；出现变化不向不兼容客户端发送新命令。
- 新安装命令的业务字段为 schemaVersion、installationId、bindingVersion、skillKey/version/packageSha256、challengeId、packageRef；目标/runtime/command/attempt/epoch 由已认证 envelope 绑定。packageRef 仅是 §7.3 固定路径，bridge 不接受任意 origin。
- 平台包来自服务端批准目录及已验证发布者来源；客户端重算包摘要、进行既有目录/符号链接/原子激活检查。结果字段为 installationId、commandId、attempt、executionEpoch、challengeId、packageSha256、outcome、errorCode（可空）。认证 scope 不从 body 获取。
- 一次性 challenge 绑定完整安装请求及当前 runtime；同已验证结果重放幂等，换 digest/目标/epoch 拒绝。客户端回执须走现有受信 native 认证，不引入自制 HMAC 密钥或裸回调。安装证明不宣称能证明被攻陷宿主实际执行了正确代码。
- 服务端校验当前绑定、包发布/撤销状态、挑战和传输事实后保存安装结果。商店订单状态/退款协议保持原样，失败不伪造商业权益。

### 18.4 前端与公开投影

首期管理入口属于典籍阁，不注入统一办事列表。原会话维护卡只存受权 jobRef 和显示元数据，打开时按当前用户 GET job；不能靠卡片存在授权。普通读者可见“当前是否有人负责/能否提交管理请求”等脱敏能力，不得到他人 agentId、owner、binding、runtime 或 endpoint。仅管理者在自己的授权管理范围看到目标身份。

若共用会话消息 parts，按现有版本化扩展点接入；没有该扩展点则先返回受控文字链接/按钮，不能修改旧 ItemRef 让它接受未知类型。新轮次继续编辑使用固定 source/edition/draftRevision，不能只依靠模型 thread 记忆。

### 18.5 多媒体依赖和合同交接

已提交的相邻特性为 `juyiting-multimedia-deliberation`（根 develop 基线 ccd6cbabe0c9f737ae61237c0d01c4df821e8a5c）。它仍是设计，不代表可直接调用的新 API。遵守其“共享会话执行/既有私有存储/个人保存与正式验收分离”边界；典籍源文件和草稿复用受控存储对象，封存正文继续使用已有 archive 正文表，不新增第三存储根。

M0 需要从实施时最新组件 SHA 核对 fast-deliberation 的权威身份、逐目标 capability、冷线程上下文与真实 INSPECT 能力，不直接复用 9 月 27 日未就绪候选。缺口只影响相应聊天集成，不阻止独立内容域与 UI 合同开发。

共享热点包括 ChatController、JuyitingAgentRelayService、AgentWebSocketHandler、native filter、useHallConversation、hallConversationMessages、agent-client。由当前 Owner 约定字段/方法与精确 tree 后交接，不整文件覆盖；不创建 Reviewer，不修改别的任务台账/证据。
