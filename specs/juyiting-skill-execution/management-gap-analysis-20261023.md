# 技能管理补齐：三端缺口与实施方案

> 当前范围（2026-10-23）：用户明确以现有原型为准，现行入口为[按原型落地方案](management-mvp.md)。安装、升级、启停、失败重试、未知核对、离线安装等待及折叠记录均保留。本文及SM-1保留审计/方案演进用途，不恢复整套管理框架，也不沿用后来文档的功能裁剪；真实发布/价格未知不得补造。

核对日期：2026-10-23（Asia/Shanghai）。任务/唯一Owner：SKILL-MANAGEMENT-20261023 / 本聊天。
状态：**源码审计与实施方案，不是管理功能已交付或已上线**。承接现有技能执行模块，不新建技能市场/调度平台。接口以`api/docs/interface-standard.md`的2026-10-14冻结规范（文档1.2）为准。

## 1. 结论与事实边界

当前具备“包发布 → 购买/首次安装 → 安装回执 → 能力发现 → 任务执行”的基础，但**没有完整的技能生命周期管理**。特别是升级不是缺一个按钮，而是前端入口、后端准入/状态模型及Runtime安装切换均不完整。

### 本次图片问题已经证明的事实

- 10月22日Runtime提交`0e96676`已将image-edit源码包1.0.0升级为1.1.0，声明PNG/JPEG/WebP/GIF/BMP/TIFF/HEIC/HEIF/AVIF；image-provider引入统一图片规范化。并非只放开上传或原生读图。
- 10月23日只读核对吴用实际安装清单，仍为image-edit1.0.0，仅PNG/JPEG。事项516的原请求能力快照绑定这个旧版本与包摘要；模型选择GIF触发ACTION_SELECTION_INVALID。
- **未查询**当前平台1.1.0商品发布状态及相关安装操作历史，不能断言它已经上架、安装失败或只是未刷新。升级Runtime不自动升级独立安装的技能。
- 后端现行源码在quote/purchase通过`lockSkillKey(...agent, skillKey).isEmpty()`拒绝再次购买，错误SKILL_ALREADY_ORDERED；SQL包含该技能的全部历史权益，包括FAILED。
- Runtime `_assertNoRegistryConflict`拒绝另一个installationId持有同一skillKey，固定目标为`CODEX_HOME/skills/<skillKey>`。当前是首次安装与同一操作重放，不是新版本替换接口。

### 固定来源

Web远端638084d、API远端b0735f57、Runtime远端297272f；完整commit/tree、读取时间、关键源码SHA见`evidence/management-gap-20261023/source-audit.json`。对比确认本地关键market/install源码与远端一致；Web AgentPanel远端另含接外单设置，未覆盖。生产Runtime程序1.2.6与源码候选1.2.7分开；本轮没有线上API/Web版本闭包或完整业务测试，不把源码审计冒充线上验收。

## 2. 已有能力——复用，不重写

| 层 | 已有源码能力 | 证据入口（组件仓路径） |
|---|---|---|
| Web | 技能集市、选择已拥有Agent、固定商品版本报价/购买、权限确认、订单轮询、未知购买操作原键恢复 | web/src/components/economy/SkillMarket{Route,}.vue；web/src/composables/useSkillMarket.js |
| Web | Agent详情安装核验/运行状态/原因码；任务级可用技能展示；身份切换与迟到响应守卫 | web/src/components/juyiting/AgentPanel.vue；web/src/composables/juyiting/useHallAgentProfileCapabilities.js |
| API | 管理员包发布、不可变包存储、product/version发布指针、摘要核验、并发版本检查 | api/agent/jia-agent-service/src/main/java/cn/jia/agent/{api/SkillPackagePublicationController.java,skill/SkillPackagePublicationService.java,skill/SkillPackages.java} |
| API | 购买权益与首次安装、命令/outbox、Runtime下载身份、ACK、安装回执及可确定失败退款 | 同模块skill/SkillMarketplaceService、SkillInstallCommandWriter、SkillInstallDispatchService、SkillInstallAckService、SkillInstallResultService |
| API | 原安装投递恢复、可信安装证据、当前Runtime会话目录、任务授权 | SkillInstallRecoveryService、InstalledSkillDescriptorService；chat模块ChatActionCapabilityService |
| Runtime | 包下载/hash、路径及解压保护、暂存安装、持久PREPARED/ACTIVE登记、marker与回执重投、崩溃恢复 | conf/codex-ws-agent/skill-install-manager.mjs |
| Runtime | 安装变化时失效/重测；当前会话、runner、工具及Provider binding核验；精确版本执行 | skill-registry.mjs；agent-client.mjs的onSkillInstallChanged；skill-executor.mjs |

普通SKILL.md说明包不自动等于平台可执行插件；可执行manifest也不自行授予权限。Runtime登记只报告事实，权限仍来自后端合法安装及任务授权。

## 3. Web缺口

### F1. Agent级管理入口（首期）

在现有Agent详情“技能”区增加“管理技能”，复用技能市场，不复制第二套购买页面。管理页按所选Agent展示：技能名称、当前启用版本、平台可升级的已发布版本、安装/运行状态、最近核验时间、具体不可用原因、可执行操作。

现有market的权益/运行时快照是分散文本；SkillMarketRoute未向SkillMarket传入installedSkills/runtimeAbilities，不能作为可靠的已安装管理总览。现有profile DTO也没有候选版本、升级差异、操作进度/动作权限，不能前端猜测。

### F2. 版本与升级交互（首期）

- 明确“当前1.0.0 → 候选1.1.0”，展示输入格式、参数、权限/依赖变化及费用变化；目标绑定批准的商品版本及摘要，不实时追踪所谓latest。
- 升级、重试已确定失败、核对原未知操作分别呈现；有在途操作时禁重复写，刷新/断线/换身份不丢恢复关联。
- 页面区分后台已接纳、下载/校验、切换、回执待确认、Runtime就绪，不把购买ACTIVE或文件存在直接画成“可调用”。
- 安装完成后刷新管理投影与任务目录；仍使用旧能力的会话快照应由既有授权路径重新建立新请求，不能静默替换旧请求。

### F3. 停用、卸载、恢复与历史（后续同一体系）

先提供“停用新调用”；卸载不等于删除历史成果/权益/配置。恢复指定已批准版本须显示影响，不默认支持任意降级。操作历史展示操作者、原/目标版本、时间、结果及安全错误，不暴露token/主机私有路径。

### F4. 平台维护视图

维护者需要包上传/校验、版本列表/差异、发布状态与Agent采用情况；现有发布API没有对应完整Web管理界面。普通Agent Owner只能管理自己的安装，不能发布平台包或修改别人的Agent。首期可复用受控发布入口，后续补维护页，不为此次图片修复再造商城。

所有页面先改唯一原型`web/prototypes/juyiting/`，覆盖PC/移动/空态/离线/失败/未知；原型通过不等于上线。

## 4. API缺口

### B1. 管理聚合读模型（首期）

当前catalog只给当前商品、entitlements给权益、profile给安装/运行事实，缺少统一Owner管理读模型及版本历史。需要按可信主体聚合：

`agent + skillKey → publishedCandidate + desiredVersion + activeInstallation + runtimeObserved + operation + allowedActions + observedAt`

各项是不同事实，缺失显示未知/未发布/未安装，不能互相补值。候选以批准发布指针和兼容性为依据，不按字符串或目录名猜最新；原版本/依赖/权限差异由服务器产生。该读接口无安装、刷新注册、派单副作用。

### B2. 独立升级准入（首期关键）

当前报价/购买是首次安装语义。不能删除SKILL_ALREADY_ORDERED检查、伪造新skillKey或清旧权益后再次购买来升级。

在既有管理服务内补有类型的升级操作，绑定Agent/skill、原installation与摘要/版本、目标批准productVersion与摘要、Owner范围、expectedStateVersion、requestId/幂等键；新命令复用既有outbox、认证下载、回执与恢复，不另造消息通道。

- 旧权益覆盖的升级不重复创建购买订单；收费或新增权限若超出原授权，需要明确的新授权，不假设免费、不把运行费用审批重新引入。
- 同Agent/skill的并发升级、停用、卸载互斥；旧回执不得将新一代状态倒退。
- 失败重试保留历史证据，但要有新的受控准入；未知只核对原操作，不另起安装。
- 离线可显示真实等待；是否允许离线提交必须由冻结契约明定，不用当前ONLINE取代Owner授权，也不把未送达当成功。

### B3. 数据状态与激活提交（首期）

当前installation状态REQUESTED/INSTALLING/SUCCEEDED/FAILED，entitlement状态PENDING_INSTALLATION/ACTIVE/FAILED且终态不再转换；不足以承载新候选、旧启用版本、升级/停用和保留的在途版本。

实施前冻结“权益、安装事实、当前激活关系、管理操作”的职责及最小增量DDL，优先扩展已有记录，不把成功旧安装改回安装中，不将新版本覆盖旧回执；不为页面复制第二套成功状态。切换期间先禁止不确定的新准入，收到精确回执/当前目录后才可宣告新版本可调用。Runtime本地激活和后端授权提交是跨进程两阶段事实，必须可恢复，不伪称一次数据库事务覆盖两端。

### B4. 发布管理与升级覆盖（首期读接口，后续写管理）

发布服务已存在，不重写。补版本列表/详情/差异、哪些Agent仍用旧版、发布候选是否完成实装验证。商品下架、正常退役、安全撤销分别建模：下架不自动删除合法旧安装；安全撤销才可阻止已授权执行继续，不与普通升级混用。

### B5. 审计、错误和任务投影

操作记录串联requestId → 管理操作 → command/message → installation/epoch → Runtime目录revision。详情应能说明“新版未发布/尚未升级/安装未知/缺依赖/版本不一致”，而不只回话失败。为确定性模型结果不合法与不确定的外部执行结果分别处理；不能为消除等待把所有UNKNOWN强行标失败或自动重发。管理修复不替代这项原议事错误收敛。

## 5. Runtime缺口

### R1. 真正的升级状态机（首期关键）

当前manager只允许同一安装命令重放，拒绝同skillKey的新installation。须新增经服务器授权的升级路径：核对当前激活身份/摘要 → 独立暂存候选 → 包/manifest/依赖核验 → 安全切换 → 持久回执 → 重测目录。不能直接覆盖运行中的`skills/<key>`或只手改manifest。

### R2. 在途执行版本固定（首期关键）

现有executor按精确skill/version/hash找registry；registry来自ACTIVE目录。简单替换会使旧执行恢复找不到原包。需让新的调用使用新激活版本，旧执行/结果UNKNOWN仍可按原授权取回精确旧包；目录保留与GC依据在途引用/恢复记录，而非只按“不是最新”删除。

本设计不改变CYF Runtime程序固定`app/`，不恢复`releases/<版本>`或current程序链接。技能包是独立受管内容，其存储/引用结构另按不可变摘要及精确执行绑定设计，不能用“应用根只留一套程序”误删在途技能包。

### R3. 切换失败与崩溃恢复（首期）

下载/解压/依赖失败保持旧版本；已切换但ACK丢失时读回同一操作；重启根据真实文件/登记证据协调，不重下载重执行。回退通过新的受控激活操作复核当前状态，绝不恢复旧会话/授权/业务状态快照。无法证明切换结果时明确RECOVERY_REQUIRED。

### R4. 就绪与刷新（已有基础，补升级接线）

不能将“能力刷新完全缺失”列为缺口：onSkillInstallChanged已经失效并重测，断线/session变更也会失效。缺的是升级/停用/卸载事件接入同一路径，以及后端接收新目录前的安全过渡、UI readback及失败诊断。心跳仍复用缓存，不新增每轮全目录扫描。

### R5. 停用与卸载

停用先停止新准入；卸载先检查在途引用/结果恢复，再按受控操作移出激活区。保留身份、凭证、历史回执和业务状态；未注册的HOME技能不能因扫描到文件就获得平台权限。

## 6. 最小实施顺序

| 切片 | 内容 | 完成判据 |
|---|---|---|
| M1 | 真实状态盘点、Owner管理读模型、Agent管理原型 | 能明确显示吴用“实际1.0.0/源码候选1.1.0”，候选发布状态未经平台核验时不显示可升级；版本/权限/原因有权威来源 |
| M2 | 升级跨端固定契约及共享fixture、最小状态/迁移设计 | API/Runtime对身份、原目标、版本摘要、幂等、未知及旧回执拒绝集合一致 |
| M3 | Runtime暂存/切换/保留旧执行；API升级准入、操作查询、回执激活 | 合成fixture完成1.0→1.1；坏包不影响旧版；崩溃及ACK丢失可恢复；旧执行能继续/核对 |
| M4 | Web管理/升级/进度/原操作核对接线，版本差异与错误展示 | 不重复购买，不自动发送业务消息；换身份/Agent后旧响应不污染；PC/移动可用 |
| M5 | Flow固定源码验证及已授权在线升级验收 | 三端版本闭包、真实技能包/安装记录/目录一致；GIF/AVIF编辑实测另按授权调用Provider；旧失败请求不自动重放 |
| M6 | 同一管理体系补停用/启用、受控卸载/回退、维护发布页与批量采用视图 | 每动作有明确Owner/影响/恢复与证据；不增加无人授权的自动升级或新常驻服务 |

首期优先做M1–M5，解决“有新版却无法可靠升级”的实际问题；不是一次扩建所有市场运营功能。M6保留在同一方案，不能把首期交付称为完整卸载/回退管理已经实现。

## 7. 必须保留的回归

1. 两个Agent/两个Owner/不同tenant-client不能交叉安装或查询敏感管理详情；接外单权限不等于管理权限。
2. 相同幂等键相同输入重放只有一次操作；相同键不同目标/摘要冲突；两次并发升级只有一个通过CAS。
3. 旧版仍有效、新版准备失败不影响旧版；权限扩张未经授权不能生效；有购买费用时沿原交易保护。
4. 下载/hash/manifest/工具依赖/Provider binding异常如实报错，不改写技能声明伪造支持。
5. 每个激活崩溃点、重启、ACK丢失、晚回执、Runtime session变化均有定向用例，不错误退款/伪成功/重复购买。
6. 旧执行固定旧包；普通升级不取消任务；UNKNOWN结果仅恢复不重新调用Provider；安全撤销单独测。
7. 能力缓存/任务快照切换正确：旧消息仍核对原版本，新请求才使用新目录；旧响应不覆盖新状态。
8. Web刷新、跨标签、切Owner/Agent、关闭/取消、离线与未知保留正确恢复入口，不使用后端未授权操作。
9. 无可执行manifest的普通说明包可按原规则安装，但不会进入任务可调用目录；未登记本地文件不能自授能力。
10. 上线须区分源码候选、技能市场发布、安装激活、Runtime就绪与真实业务验收；发布Runtime1.2.x不代表技能1.1.0已安装。

## 8. 验证与本轮交付边界

本轮只做只读源码/安装清单审计和方案落盘，未跑应用测试、未调用模型、未写数据库/订单、未发布包、未升级Agent或部署。已有首次安装测试不能直接复用为新升级链路验收。

后续轻量共享fixture/DOM/合成Runtime目录测试可本机；高内存Node/Gradle测试、应用构建/打包在原Flow4403172/5260799。Gradle先读最新build.gradle并经现有串行编排入口；生产安装遵守固定源码、制品摘要、发布锁、备份和恢复。新数据迁移先校验既有约束/升级回滚策略，不在分析时直接执行。

详细授权、固定源码、前任务未完成改动和下一动作见`../../docs/implementation/handoffs/SKILL-MANAGEMENT-20261023.md`。

## 10. 用户查看用原型增量（2026-10-23）

用户要求先更新并查看原型，因此本阶段不进入产品实现。唯一原型新增Agent详情“管理技能”，包含列表、版本差异、升级进度/成功/准备失败/未知核对、启用停用确认、操作记录及离线空态；入口 `web/prototypes/juyiting/index.html?scenario=skill-management#agents`。首期设计仍复用现有市场，不增加购买页；平台维护端、受控卸载/回退、实际三端升级合同与数据模型仍未实现。权限和费用差异为明确标记的合成假设，不将1.1.0源码存在当作平台已发布或当前实装事实。

原型组件是 `skill-management.js/css`，在现有原型目录增量加载，正文规格已同步。轻量浏览器诊断复用已有 `check-browser.cjs` 定向分支；截图与最终检查结果由 `docs/implementation/handoffs/SKILL-MANAGEMENT-20261023.md` 索引。仅待用户看交互，不触发真实购买、升级、迁移或发布。

2026-10-23用户看原型后要求保持简约：管理入口收进现有技能标题行，去掉重复升级横幅/统计/说明块；默认一行技能记录，详情、差异、进度按需显示，弹窗按内容自适应高度。此要求纳入后续产品实现，不以新增信息块作为默认方案。


2026-10-23继续按用户要求补“安装技能”原型：管理列表工具行增加单一入口，同一窗口按需展示技能集市示例、逐项权限、报价/安装确认、进度与失败/未知/离线恢复。成功后回到多技能紧凑列表；失败沿原安装恢复、未知只核对，不重复购买、不把安装中计为已安装。示例商品/价格/发布状态不是实际事实。复用现有market的确认语义，不新建产品市场；失败重试/离线准入为后续待冻结合同，本轮不修改API/Runtime或实际安装。文字规格见唯一原型同日“安装技能”章节，验证与状态见SKILL-MANAGEMENT-20261023 handoff。


**2026-10-23现行原型以本段为准**：用户否定继续增加安装入口/选择页，要求从UI设计与体验整体规划。已安装与可安装统一为一张技能列表，不再有“安装技能”总入口、已安装/市场页切换；每行以名称/用途识别技能，以版本/状态辅助判断，只突出当前安装/升级操作，详情弱化。权限、报价、确认、进度原位展开，历史折叠；完成不离开列表。前文分层安装入口仅为同日已被替代的交互草案，不作为后续产品开发要求。三端安全/权限/幂等合同与实现边界不变。
