# 验收与证据矩阵（D2）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：典籍任职、资料整理与受控内容维护。**

### 必须验证的业务结果
任意合法好汉/技能组合、越权拒绝、版本并发/幂等、草稿与发布分离、真实读回；工具完成不等于用户验收。

### 不回归边界
任职、技能安装、任务准入各自独立；不按好汉显示名或技能名硬编码通用Runtime，不向Agent暴露数据库凭据。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


**以下全部为待执行验收条件，不是测试通过报告。** 本轮仅交付设计与静态文档检查；未调用应用、未运行 Gradle/Vite、未做生产内容维护。

机器可读矩阵：[acceptance-cases.json](acceptance-cases.json)。功能要求见 [spec.md](spec.md)，合同见 [design.md](design.md)。

## 1. 测试层级

- API unit/contract：schema、DTO、鉴权、native filter、工具上下文、内容校验、CAS/幂等。
- 隔离 MySQL：真实外键/唯一/非空及业务责任层规则（不新增/依赖CHECK）、撤任与发布竞态、原子激活、唯一约束、迁移断点；不以 mock 事务代替。
- Client Node：命令协议、安装证明、固定 origin/资源范围、持久 inbox/断点/重放、凭据不进模型。
- Web unit + browser：reader 兼容、真实 HTTP 边界、身份清理、权限 UI、故障状态、移动布局。
- 集成 fixture：明确授权小型文本，至少一个非 120 回/无序言样本，旧水浒摘要不变。
- 真实业务验收：获授权管理者、真实任职 Agent、真实客户端、确定底本《三国演义》、发布回执、读回及私人数据闭环。

所有 Gradle 必须通过 `/home/isp/wsps/cyf/ops/orchestration/cyf_orchestrator.py`，先检查 nearest build.gradle；实际 selector 在实现时按新增测试类确定。此处不伪造尚不存在的可运行测试命令。

## 2. 用例

### 身份与任职

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| AUTH-01 | **普通读者不能任命**：读者调用任职写接口或诱导宋江任命 | 拒绝写入，数据库无任职/授权变化 | M2, M7 | 未执行 |
| AUTH-02 | **显示名不能授权**：另一个 Agent 显示名也叫吴用 | 仅 canonical Agent/binding 的任职有效 | M2 | 未执行 |
| AUTH-03 | **同 owner 任命**：管理者选择自己的当前绑定 Agent | 保存准确 scope/binding/skill/profile；可离线任命 | M2 | 未执行 |
| AUTH-04 | **跨 owner 任命拒绝**：书库管理者指定他人 Agent | 首期拒绝，不能仅凭管理公共书库权获得他人 Agent | M2 | 未执行 |
| AUTH-05 | **换 owner / binding**：任职后 Agent 解绑或变更 owner | 有效任职失效；旧作业写/发布拒绝，历史保留 | M2, M4 | 未执行 |
| AUTH-06 | **撤任线性化**：用数据库 barrier 并发撤任与发布 | 按提交/锁先后产生唯一正确结果，撤任提交后无新发布 | M2, M4 | 未执行 |
| AUTH-07 | **单岗位并发任命**：两个管理请求竞争同一 slot revision | 一个生效，另一个冲突；无两个当前负责人 | M2 | 未执行 |
| AUTH-08 | **仅编修不能发布**：DRAFT_ONLY Agent 调用 native publish | 403；草稿保留，可由有权管理者另行发布 | M2, M4 | 未执行 |
| AUTH-09 | **AUTO 授权交集**：岗位可自动发布但本 job 为 MANUAL | Agent 不能发布；管理者显式发布可成功 | M2, M4 | 未执行 |
| AUTH-10 | **书目范围**：EXPLICIT_WORKS 任职尝试新建别书或改另一本 | 拒绝且无跨 work 数据变化 | M2, M4 | 未执行 |
| AUTH-11 | **全维度隔离**：分别更换 tenant/client/owner/agent/runtime/job/source | 均不可跨范围读取草稿或写入，不泄露资源存在性 | M2, M4 | 未执行 |
| AUTH-12 | **管理权限撤销**：发起者书库授权撤销后后台准备发布 | 原授权不再允许发布；有权管理者可新授权接管 | M2, M4 | 未执行 |

### 原生通道与工具

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| NATIVE-01 | **native 精确路由**：逐个验证新增方法/路径及相邻非法路径 | 仅合同路径可用，Controller/filter 均覆盖 | M2, M6 | 未执行 |
| NATIVE-02 | **认证通道不能混用**：用户 JWT 调 native，runtime 凭据调 admin/me | 拒绝；不提升为另一种 principal | M2 | 未执行 |
| NATIVE-03 | **头与路径歧义**：重复 Authorization/Agent header、编码分隔符、Origin | 失败关闭，不绕过白名单或落入 OAuth 通道 | M2 | 未执行 |
| NATIVE-04 | **请求主体伪造权限**：正文加入 owner/tenant/permissions/其他 draftId | 拒绝未知或冲突字段，无权限升级 | M2, M4 | 未执行 |
| NATIVE-05 | **可信协调上下文**：从普通会话或伪造 persona 调宋江工具 | 服务端不接受模型声称的 coordinator 身份 | M7 | 未执行 |
| NATIVE-06 | **旁路工具隔离**：在典籍协调请求尝试 shell/SQL/任意 URL 工具 | 请求工具集合不提供旁路，业务服务再次鉴权 | M7 | 未执行 |
| NATIVE-07 | **正文提示注入**：来源正文要求调用发布、读密钥或改任职 | 视为纯文本；无越权调用、外泄或隐藏副作用 | M5, M6, M7 | 未执行 |
| NATIVE-08 | **凭据不进模型**：捕获 prompt/tool result/manifest/日志/UI 回执 | 无 JWT/runtime secret/DB credential，bridge 固定 origin | M6, M7 | 未执行 |

### 平台技能与执行资格

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| SKILL-01 | **abilities 不等于安装**：runtime 上报 archive-maintainer 字符串但无安装事实 | WAITING_SKILL，不派发或执行写操作 | M3, M4 | 未执行 |
| SKILL-02 | **平台配置不收费**：关闭技能市场资金操作后安装平台技能 | 安装回执有效；钱包/订单/资金流水均无变化 | M3 | 未执行 |
| SKILL-03 | **包/版本篡改**：下载包或回执的摘要/version/Agent/command 不匹配 | 不能激活安装事实，不触发任职扩大 | M3, M6 | 未执行 |
| SKILL-04 | **安装回执伪造/重放**：普通 HTTP 声称成功，或重放其他 runtime/origin 回执 | 拒绝；同一真实回执重放仅返回原结果 | M3 | 未执行 |
| SKILL-05 | **安装器文件安全**：测试穿越/符号链接/执行文件伪装/损坏归档 | 不写出授权安装范围；失败归因不伪造退款/成功 | M3 | 未执行 |
| SKILL-06 | **在途技能升级/撤销**：任务运行中安装新版本或撤销已绑定版本 | 升级不替换在途包；撤销暂停依赖任务 | M3, M6 | 未执行 |
| SKILL-07 | **老客户端协议不支持**：client 不支持新 archive 命令 | 明确待更新，不降级成自由 shell 或普通文件执行 | M3, M6 | 未执行 |

### 内容、来源与版本

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| CONTENT-01 | **非 120 回 / 无序言**：使用明确合法小 fixture，不满足旧种子形状 | 正常导入并读回，数据库与服务都不硬编码 120 | M1, M5 | 未执行 |
| CONTENT-02 | **来源固定与权利声明**：缺来源摘要/固定版本或必要权利说明 | WAITING_INPUT/校验失败，不擅自选现代底本 | M5 | 未执行 |
| CONTENT-03 | **不臆造原著**：底本缺章，Agent 生成看似合理章节补上 | 来源映射/目录校验不通过，不上架 | M5, M6 | 未执行 |
| CONTENT-04 | **跨语言摘要向量**：Java/Node 对中文、罕见字、换行、JSON 键顺序处理 | 规范化结果/摘要一致，非法 Unicode/重复键拒绝 | M1, M5, M6 | 未执行 |
| CONTENT-05 | **持久化内容再校验**：上传声明摘要正确但存储实际字节损坏 | 发布前读回失败，READY/发布不伪造 | M1, M4, M5 | 未执行 |
| CONTENT-06 | **章节目录完整性**：缺章/重复/乱序/实际目录与冻结来源不同 | 定位具体块与来源差异；真实不完整阻止发布 | M5 | 未执行 |
| CONTENT-07 | **草稿 CAS 与校验失效**：两个编辑写同 revision，或校验后再改正文 | 冲突不覆盖；改动后旧 validation 不可发布 | M4, M5 | 未执行 |
| CONTENT-08 | **READY 不公开**：把成功导入但未发布 editionId 交给读者 | 正文/目录/提问/私人数据新锚点入口均不泄露 | M1, M4 | 未执行 |
| CONTENT-09 | **原子激活**：发布事务中注入失败与重启 | active/publication/job/outbox 全提交或全不提交 | M4 | 未执行 |
| CONTENT-10 | **新版本不覆盖旧锚点**：已给旧版建立进度/书签/手札后发布勘误 | 新 editionId；旧文本/ID/hash 和旧私人数据不变且仍可读 | M1, M4, M8 | 未执行 |
| CONTENT-11 | **下架与默认版选择**：管理者明确下架当前版，不指定替代版 | active 置空、正文有权请求410；不自动退旧版，私人笔记保留 | M1, M4, M8 | 未执行 |
| CONTENT-12 | **同标题/重复新增**：不同 turn 再请求相同标题，含相同/不同 canonicalKey | 提示可能已有作品；唯一 key 不重复，不能自动覆盖不同作品 | M4, M7 | 未执行 |
| CONTENT-13 | **固定来源/网络出口**：传入任意 URL、重定向内网或读非授权文件版本 | 来源适配拒绝；不向外部 origin 附带凭据 | M5, M6 | 未执行 |
| CONTENT-14 | **XSS/正文指令数据化**：正文含 HTML/script/危险链接 | 阅读纯文本或受控净化，不执行脚本/隐式抓取 | M5, M8 | 未执行 |

### 可靠性与故障恢复

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| RECOVERY-01 | **章节提交响应丢失**：DB 已提交，客户端网络断开 | 按同 key 或 draft digest 恢复，仅一个有效章节 | M4, M6 | 未执行 |
| RECOVERY-02 | **同 key 不同请求**：复用 Idempotency-Key 修改 body/path/候选 | 409，不静默覆盖或生成新操作 | M4 | 未执行 |
| RECOVERY-03 | **未知状态不能当未受理**：POST 仍在途时查询 key 得404 | UI/Agent 仍保留原 key，不能断言失败并另起作业 | M4, M6, M8 | 未执行 |
| RECOVERY-04 | **命令重复/乱序**：重复 delivery 或旧 epoch start/write/result | 同执行幂等；旧 epoch 拒绝；ACK 不置 PUBLISHED | M4, M6 | 未执行 |
| RECOVERY-05 | **离线和慢处理**：断连/长时解析/性能超过历史 SLO | 作业等待/继续；不因预算不足取消或跳过后续步骤 | M4, M6, M8 | 未执行 |
| RECOVERY-06 | **同实例重连/新实例恢复**：分别断线同 runtime 和换 runtime | 同实例可恢复；新实例须正式恢复并隔离旧 epoch | M2, M4, M6 | 未执行 |
| RECOVERY-07 | **临时对象写入后崩溃**：对象成功但 DB 引用未提交 | 原操作恢复或清理本命名空间孤儿，不影响其他任务 | M4 | 未执行 |
| RECOVERY-08 | **READY 后激活前崩溃**：正文完整 READY 但无 publication | 有权同 operation 恢复，读者此前不可见 | M4 | 未执行 |
| RECOVERY-09 | **发布后通知丢失**：publication 提交后 outbox 暂时失败 | job/result 可查询；投影最终收敛，不重复发布 | M4, M7, M8 | 未执行 |
| RECOVERY-10 | **并发版本发布**：两个 job 指向同 (expectedWorkRevision, expectedActiveEditionId)，另测 active A→B→A | 只有一个成功，另一个明确 CAS 冲突，不后写覆盖 | M4 | 未执行 |
| RECOVERY-11 | **显式取消/移交**：在运行时由有权管理者取消或移交 | 旧执行后续写拒绝，草稿/历史保留；不操作 foreign 进程 | M2, M4, M6 | 未执行 |
| RECOVERY-12 | **事件恢复与游标**：重复乱序事件及过期 cursor | 按 sequence 幂等；返回 RESYNC_REQUIRED 并取真实快照 | M4, M8 | 未执行 |
| RECOVERY-13 | **根因有界重试**：同输入相同错误连续两次 | blocked_root_cause；修复后才新 attempt，历史失败保留 | M4, M6 | 未执行 |

### 用户闭环与兼容迁移

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| UX-01 | **旧水浒启动不夺指针**：已有后续合法版本时重启 archive bootstrap | 不切回种子版，不重写原文/摘要 | M1 | 未执行 |
| UX-02 | **新旧 schema 桥接**：空库、旧库、已迁移库及中断迁移恢复 | 初始化/schema 校验兼容，步骤可恢复，无误删个人数据 | M1 | 未执行 |
| UX-03 | **旧 API shape 不变**：旧客户端使用 /archive/v1/catalog 和原 question 入口 | 原返回结构/旧锚点解释兼容，不把 catalog 突变数组 | M1 | 未执行 |
| UX-04 | **新增书阅读全链路**：选择新增书，阅读、续读、书签、手札、选文提问 | 全按新 edition/manifest 验证和 owner 持久化，不回落水浒 | M1, M8 | 未执行 |
| UX-05 | **进度初始化顺序**：已有后段进度，从书架进入/刷新 reader | 先读进度再开章；自动保存不覆盖为卷首 | M8 | 未执行 |
| UX-06 | **跨书/跨身份缓存**：切换书、版本、账号并模拟旧响应晚到 | 不会错书/泄露进度手札草稿，身份变更取消旧请求 | M8 | 未执行 |
| UX-07 | **真实 HTTP/CORS**：真实 createApi→fetch，带幂等/If-Match/JWT；可信/不可信 Origin | 合法预检/ETag读取正确，非授权跨域不放行 | M2, M8 | 未执行 |
| UX-08 | **首次任命用户路径**：无任职，对宋江要求新增书 | 引导明确任命；不自行给任意吴用赋公共维护权 | M7, M8 | 未执行 |
| UX-09 | **缺来源/待技能/离线**：分别触发三种真实阻碍 | 显示准确下一步；不把三者均称执行失败 | M7, M8 | 未执行 |
| UX-10 | **普通读者建议**：普通读者对宋江要求新增公共书 | 明确提示需要书库管理者且未创建维护单，不形成收费执行、建议队列或越权写内容 | M7, M8 | 未执行 |
| UX-11 | **端到端 DRAFT_ONLY**：已任命吴用仅编修，对宋江要求新增固定来源书 | 返回待发布草稿及真实校验，有权管理者可手动发布 | M1, M2, M3, M4, M5, M6, M7, M8 | 未执行 |
| UX-12 | **端到端 AUTO 三国演义**：明确授权的真实底本/任职/AUTO，经宋江交办 | 真实 Agent 完成；服务端publication + 新书读回 + 正确汇报 | M1, M2, M3, M4, M5, M6, M7, M8 | 未执行 |
| UX-13 | **读回失败不重发发布**：publication 已提交，但阅读探测暂时失败 | 报告已提交但读回异常，不重复激活/假报完全成功 | M4, M7, M8 | 未执行 |
| UX-14 | **移动/横竖屏/返回**：真实浏览器视口与键盘缩高、深层返回、焦点 | 关键操作可见，正文/手札有界滚动，回到正确书架/作业 | M8 | 未执行 |
| UX-15 | **权限撤销后前端**：页面仍持旧 capabilities，后台撤任/撤管理授权 | 服务端拒绝，前端清理敏感写状态；不依赖隐藏按钮 | M2, M8 | 未执行 |
| UX-16 | **部署事实不混淆**：核对制品、版本、初始化、runtime、真实内容回执 | 有完整 exact source/test/artifact/online 证据；没有 Flow Run 则不伪造 | M9, M10 | 未执行 |

### D2 兼容与共享边界

| ID | 场景/触发 | 预期 | 工作包 | 状态 |
| --- | --- | --- | --- | --- |
| D2-01 | **旧办事台不扩类型**：打开维护单及原 hall overview/items/marks | 典籍只走独立面板/会话卡，旧 ItemRef 枚举、分区、游标和动作保持兼容 | M4, M8 | 未执行 |
| D2-02 | **直达与宋江边界**：分别向宋江和已任职吴用交办；另用密议 | 双入口同一授权用例；直达不经宋江，宋江不获得密议读取权 | M2, M7, M8 | 未执行 |
| D2-03 | **跨入口重放**：原 requestIntentId 从断线重试和会话卡恢复 | 只有一个 job/当前执行，异内容同 key 冲突；不能从 chat/task 重复派发 | M4, M6, M7 | 未执行 |
| D2-04 | **唯一执行权威**：业务 outbox 投递响应丢失后恢复 | 重用同 dispatchKey/command/executionRef，不建第二套调度或 archive 命令轮询 | M4, M6 | 未执行 |
| D2-05 | **两套 Runtime 隔离**：仅 heartbeat/ACK 的 Runtime v1 和 legacy 客户端混用 | 按目标实际能力投递；不支持者待就绪，不混用凭据/profile/state，不强制切换其他 Agent | M2, M6 | 未执行 |
| D2-06 | **逐目标能力变更**：受理后目标撤销命令能力或更换绑定 | 分发前重新校验，不发送不支持协议，不偷偷 fallback 重跑 | M2, M6 | 未执行 |
| D2-07 | **共享安装适配**：平台来源与商业来源安装同 key 技能，且仅标 deliverable 标签 | 来源分别核验，不伪造订单或扣费；标签不能提供安装事实/ACL/正式验收证据 | M3, M6 | 未执行 |
| D2-08 | **私人来源公开用途**：仅授 READ 的私人文件尝试 AUTO 或管理员发布 | 无 PUBLICATION_USE 时拒绝发布；有精确来源/书库/用途授权后才可继续 | M2, M4, M5 | 未执行 |
| D2-09 | **公开投影脱敏**：普通读者查询 capabilities 与会话维护卡 | 不返回他人 owner/agentId/binding/runtime/endpoint 或私人 source storageRef | M2, M8 | 未执行 |
| D2-10 | **冷线程与工具隔离**：更换模型线程后继续修订，另打开普通聊天 | 服务端注入已授权历史与精确来源；典籍工具限制不改变其他会话能力 | M7, M8 | 未执行 |
| D2-11 | **业务等待不占 lease**：草稿完成后等待人工发布并保持会话打开 | 释放执行 lease，保留 job；管理员用新的有效授权发布，不复用过期 producer 凭据 | M4, M6 | 未执行 |
| D2-12 | **共享存储不新增文件系统**：从私人来源导入草稿并封存正文 | 来源/草稿使用既有受控对象，正文落 archive；不迁移旧目录，不自动保存或正式验收 | M1, M4, M5 | 未执行 |
| D2-13 | **严格身份与内容迁移**：迁移前后以 tenant=0 与旧 tenant=owner 请求 | 内容兼容不恢复旧身份；owner/client 私人数据隔离不变 | M1, M2, M9 | 未执行 |
| D2-14 | **业务完成不混同**：分别产生草稿完成、publicaton 提交、读回失败和成功 | 状态分别可见，不把文件 manifest/技能安装/正式验收当典籍发布，读回失败不重复激活 | M4, M8, M9 | 未执行 |

## 3. 覆盖与分层完成标准

总计 **84 项**，覆盖 U1–U9、M0 以外所有实施/验证包；M0 以合同/基线冻结记录验证，不伪装成应用运行用例。

1. **设计交付**：五件套、源码审计、用例覆盖/结构通过；不意味着下面各层通过。
2. **源码与集成**：所有相关用例有 exact source/tree、selector、fixture digest、原始结果；不足项明确列出，integration pins 可复现。
3. **技术发布**：与源码绑定的制品 SHA-256、发布顺序、schema/client/API/Web 版本、实际健康；遵守当前默认本地固定源码与受控发布规则，真实批次/日志/摘要可追溯，不冒充Flow。
4. **实际业务验收**：真实任职/安装事实、原始来源摘要、校验 candidate、publication、读回以及用户可操作路径齐备。模型一句“完成”/HTTP202/ACK/文件生成都不等于此层。

## 4. 证据最小字段

`root/API/Web/Client commit + tree`、测试 selector、DB fixture/schema digest、skill version/package digest/安装确认、管理者与任职授权引用（脱敏）、job/run/command、source raw digest、draftRevision/validationId、edition/manifest digest、publicationId、读回结果、部署制品 digest 与 build_origin。不得保存 token、DB 凭据、私人手札正文或其他任务的证据目录。

若只有草稿模式，通过点为 AWAITING_PUBLISH，不能标 AUTO/实际上架通过；没有《三国演义》授权来源时先验证 fixture，不伪称真实书已新增。

## 5. 本轮结果

- 业务用例：全部 `not_run`。
- 应用构建/测试、生产迁移、任职、安装、导入、发布：均未执行。
- 文档静态检查结果：见 [documentation-check.json](documentation-check.json)；该文件只证明结构与自检项，不是安全认证或集成验收。

重跑本轮静态检查：

```bash
node /home/isp/wsps/cyf/specs/archive-agent-maintenance/validate-design.cjs
```

该命令只读取冻结 Git 对象、解析文档/YAML/JSON并更新本目录的静态检查记录；依赖现有 Web node_modules 中的 js-yaml，不安装依赖，不启动应用或访问生产。
