# 聚义厅移动竖屏正式事项冒烟测试用例

日期：2026-09-25（Asia/Shanghai）  
适用 SDD：`juyiting-lightweight-workbench`，并覆盖 `juyiting-conversation-first-v4-20260924` 定义的一句话渐进式主流程。  
当前基线：Web `release/1.13.32` / `2f528d5280ca41b0dfde81d8e83178f0bce97e0c`；Agent runtime `1.13.24-f1807bb-20260925` / `f1807bbddf62b897a6eb82ff44c901392f59ac3c`。

## 1. 目的与边界

本用例集用于每次聚义厅 UI、正式执行、正式交付或 Agent runtime 发布后的最小线上闭环验证。成功必须以服务端权威回执、可读取正式交付及最终案卷状态为准，不能用本地生成文件、聊天回复、上传成功或客户端乐观状态替代。

日常发布后执行 **20 分钟快速冒烟**：沿同一条业务链合并观察 JYT-SMK-01～14，不逐项重复进入页面。JYT-SMK-R01～R05 改为扩展回归，不再默认塞入每次发布后的快速冒烟。

测试边界：

- 使用 Chromium 移动设备仿真，基准视口 `390×844`；不得称为实体手机测试或真实系统软键盘测试。
- 测试 Agent 只能选择最新 `codex-ws-agent` 配置的**吴用或林冲**，不得使用扈三娘。
- 资料为可选项；无资料路径必须能够完成办理。
- 创建事项不能自动调用 Agent 或 Provider；实际办理和返工必须有独立的明确确认。
- 若调用外部 Provider，测试执行前必须已有费用授权；费用未知时不得宣称零费用。
- 不以性能目标超时中断真实可用流程，但保留真实网络错误、传输超时、身份切换取消、鉴权、幂等、租约和事务边界。

## 2. 20 分钟快速冒烟编排

### 2.1 固定测试输入

- 使用一句话需求：`请生成一页《聚义厅冒烟测试结果》PDF，写明任务标题、执行 Agent、生成时间和“冒烟通过”结论。`
- 资料固定为 0 份，不上传附件，不要求返工，不主动制造失败。
- Agent 只选吴用或林冲；优先选当前在线且已注册的一名，不做双 Agent 重复执行。
- 复用有效登录会话；登录失效时完成一次正常 OAuth 登录，不用预造 token 绕过登录。

### 2.2 时间预算

| 阶段 | 累计时间目标 | 合并执行内容 |
| --- | ---: | --- |
| 并行预检 | 0～2 分钟 | 同时核验 Web/API/runtime 健康、版本绑定、目标 Agent 注册和 PDF 存储；打开 390×844 页面 |
| 创建与开工 | 2～6 分钟 | 一句话创建、确认资料 0 份、点将、进入榜文议事、发送确认并明确开工 |
| Agent 执行 | 6～14 分钟 | 轮询同一 execution/run；页面等待期间同步记录请求、布局和遮挡证据 |
| 交付闭环 | 14～18 分钟 | 打开正式交付、预览单页 PDF、下载并校验摘要、验收、收入案卷、归档后重开 |
| 证据收口 | 18～20 分钟 | 写入任务、Agent、execution/run/delivery、PDF 摘要、终态和关键截图 |

### 2.3 缩时规则

1. JYT-SMK-01～14 仍全部保留，但在同一次自然页面流转中顺带观察，禁止为了“逐用例留图”重复导航或重复请求。
2. 健康、版本、Agent 注册和存储预检并行执行；等待 Provider 时同步完成网络回执、视口宽度和按钮无遮挡记录。
3. 日常快速冒烟只要求一页 PDF；多页逐页内容审阅、返工、失败撤销和跨身份隔离改到扩展回归。
4. 证据使用结构化回执、两张关键截图（正式成果、归档）和一个下载文件即可；只有异常时追加日志和截图。
5. 不重复未知结果的 POST，不为赶时间跳过正式验收、归档或权威状态核对。
6. 20 分钟是正常链路完成目标，不是传输超时或取消阈值。到第 20 分钟仍在执行时，记录超时阶段并继续等待真实终态；不得撤销正常请求、伪报成功或绕过锁。

### 2.4 扩展回归触发条件

以下情况另行执行 JYT-SMK-R01～R05 或相关专项测试，不计入日常 20 分钟快速冒烟：

- 修改 execution 状态机、幂等、租约、输入授权或恢复逻辑；
- 修改身份、ACL、账号切换、task/conversation/Agent 隔离；
- 真实冒烟出现失败、未知 POST 结果、陈旧连接或重复执行迹象；
- 发布前专项验收明确要求返工、多页内容审阅或异常恢复演练。

## 3. 前置条件

| 编号 | 前置条件 | 核验方式 |
| --- | --- | --- |
| PRE-01 | Web、API 和 Agent runtime 健康，且发布版本与待验 commit/tree 一致 | HTTP 健康检查、线上 JS、release/current 指向和进程归属 |
| PRE-02 | 测试账号能够完成 OAuth 登录并进入 `/juyiting` | 页面显示当前账号的办事概览；API 请求为认证态 |
| PRE-03 | 吴用或林冲在 `/agent/roster` 中可操作且 runtime 注册成功 | roster 状态与 Agent `registration stage=registered` |
| PRE-04 | 正式 PDF 存储能力已启用 | `agent.personal-workspace-storage` 与 `agent.task-artifact-storage` 可用 |
| PRE-05 | 无重复未知写请求 | 开始前核对任务、execution、work item 和正式交付历史 |

## 4. 主流程用例

| 用例 | 操作 | 必须观察的结果 | 失败判定/禁止替代 |
| --- | --- | --- | --- |
| JYT-SMK-01 登录与竖屏基线 | 以认证账号进入 `/juyiting`，设置 390×844 移动仿真 | 页面可用；`innerWidth=390`；根页面 `scrollWidth=390`；底部导航可见 | 登录页、桌面尺寸或页面级横向溢出均不通过 |
| JYT-SMK-02 一句话创建事项 | 在“办事”首页只填写一句需求并提交 | 建立正式事项并进入事项详情；文案明确“创建不执行” | 提交即调用 Agent/Provider、要求先填完整表单或先选资料均不通过 |
| JYT-SMK-03 资料可选 | 不选择资料，进入资料区域后返回或直接继续 | 显示资料 0 份；开始办理仍可继续；资料按钮不被底栏、键盘适配区或浮层遮挡 | 将资料设为必选、无资料时报阻断错误或按钮不可达均不通过 |
| JYT-SMK-04 明确点将 | 在吴用、林冲中选择一名并点将 | `/agent/tasks/{taskId}/assign` 成功；任务只关联显式选择的目标 Agent | 使用隐藏 selected state、错派其他 Agent 或选择扈三娘均不通过 |
| JYT-SMK-05 榜文议事 | 从该事项进入正式议事并发送确认消息 | 议事绑定当前 task、唯一 conversation 和已指派 Agent；刷新后可恢复 | 借用私人会话、其他榜文会话或仅显示本地假回复均不通过 |
| JYT-SMK-06 明确开工确认 | 在确认卡核对 Agent、资料数量、PDF 和未知费用说明，点击一次“确认并开始办理” | 只创建一个 TASK execution；返回 executionId、runId、workItemId；初始状态为 `QUEUED`/工作项 `running` | 创建事项时自动执行、按钮重复产生多个 execution 或 PRIVATE 回退均不通过 |
| JYT-SMK-07 Agent 实际执行 | 等待目标 Agent 领取命令并执行 | 本地 ledger 依次出现 RECEIVED/STARTED/终态；服务端 execution 最终为 `OUTPUT_COMMITTED` | 客户端 inbox completed、本地 PDF 存在、上传 201 或聊天“已完成”不能单独算成功 |
| JYT-SMK-08 正式交付出现 | 打开“查看正式成果与验收”并刷新 | `/agent/tasks/{taskId}/formal-deliveries` 返回当前 run 的 `submitted` 批次；producerAgentId 为所选 Agent | items 为空、仅 conversation output、artifact 与 run 不匹配均不通过 |
| JYT-SMK-09 PDF 预览 | 点击正式 deliverable 的“预览”，查看本次单页结果 | 预览可打开；页数符合一页需求；正文与本次需求相符；单页时上一页/下一页正确禁用 | manifest、本地路径、聊天摘要或空白预览不能替代 PDF 正文 |
| JYT-SMK-10 PDF 下载与摘要 | 点击“下载”，保存正式 artifact 精确版本 | HTTP 200、MIME `application/pdf`；下载大小非零；本地 SHA-256 与正式 artifact contentHash 一致 | 下载私人文件、最新非固定版本或摘要不一致均不通过 |
| JYT-SMK-11 用户验收 | 对 `submitted` 正式交付点击一次“验收通过” | decision HTTP 200；delivery=`accepted`、deliveryVersion 增长；work item=`completed`；task 自动=`completed` | 客户端直接改状态、无正式交付先完成或重复 decision 均不通过 |
| JYT-SMK-12 收入案卷 | 从已完成事项点击“收入案卷” | `/agent/tasks/{taskId}/archive` HTTP 200；task=`archived`；“办事→案卷”可找到该事项 | 只隐藏卡片、私人归档标记或归档后丢失正式成果均不通过 |
| JYT-SMK-13 归档后成果保持 | 从案卷重新进入并打开正式成果 | 已验收 PDF 仍可预览、下载，固定版本和摘要不变 | 归档后成果 404、版本漂移或验收状态丢失均不通过 |
| JYT-SMK-14 移动无遮挡 | 在首页、资料区、议事、开工确认、正式成果、案卷分别检查视口 | 主动作、输入区、预览翻页、下载、验收、归档按钮均可达；底栏不遮挡内容；根页面无横向溢出 | 仅检查 DOM 存在而按钮实际被遮挡不算通过 |

## 5. 扩展恢复与幂等用例

| 用例 | 触发条件与操作 | 必须观察的结果 |
| --- | --- | --- |
| JYT-SMK-R01 撤销失败执行输入 | execution 长时间停留或客户端已失败而服务端仍 `QUEUED`；勾选确认并调用 `revoke-inputs` | 原 execution=`INPUTS_REVOKED`、grantRevision 增长、原 work item 恢复 `ready`；不会自动重跑 |
| JYT-SMK-R02 原请求恢复 | R01 后从同一事项重新确认办理一次 | 生成新的 execution/run；仍绑定原 task、conversation、Agent、work item 和资料范围 |
| JYT-SMK-R03 未知结果只读核对 | POST 回执丢失、网络中断或页面刷新 | 先按 idempotency key/execution 历史核对；不得直接重新 POST；终态事实不被其他记录清除 |
| JYT-SMK-R04 输出传输陈旧连接 | 上传或 manifest commit 首次出现 `UND_ERR_SOCKET` | runtime 仅对安全的上传/commit 最多重试一次，上传重建 FormData；相同幂等键和内容；HTTP 错误与其他传输错误不盲重试 |
| JYT-SMK-R05 身份与任务隔离 | 切换账号、client、task、conversation 或目标 Agent | 旧身份在途 UI 更新被取消；不得读取、验收、归档或恢复其他作用域的数据 |

## 6. 2026-09-25 实际执行记录

| 项目 | 实际值 |
| --- | --- |
| 任务 | `403` / `1.13.32移动竖屏全流程复测-林冲-2026092510` |
| Agent | 林冲 `jyt-jiafewnnv58ec2379c-linchong` |
| 资料 | 0 份 |
| 成功 execution | `pwe_fbfa23aeabe245bebac00daa6a975816` |
| 成功 run | `pwe_run_d5a69b71a91648e89801fe70422665ef` |
| work item | `wi_legacy_34576cd169532e58cc60c33d9b888ff1`，最终 `completed` |
| 正式交付 | `pwe_delivery_7f0b7f9f99dc0453141452eda1ec3730e9cbd2b2255ab213003fa3c0f3761bf8`，最终 `accepted` |
| PDF | 4 页，65,345 bytes，SHA-256 `74c3dec88ee59c1d6a66634bdc84a14a70bf45f09723d19a3cd762cfe828fe9b` |
| 任务终态 | `archived`，taskVersion `4` |
| 视口 | Chromium 390×844 移动仿真；`innerWidth=scrollWidth=390` |
| 结果 | JYT-SMK-01～14 PASS；R01、R02、R04 实际覆盖；R03/R05 由既有合同与定向测试覆盖，本轮未主动制造跨身份破坏场景 |

本次先对旧 execution `pwe_d7ac4108983345e786ff1f42e6927bd4` 执行 R01，服务端返回 `INPUTS_REVOKED` 且工作项恢复 `ready`；随后执行 R02，新 execution 完成正式输出、验收与归档。该恢复操作通过用户作用域公开 API 和页面确认完成，没有生产 DML。

## 7. 证据

- 发布闭环：`deliverables/releases/v1.13.32-ui-optimization-local-20260925/closure-summary.md`
- 结构化结论：`deliverables/releases/v1.13.32-ui-optimization-local-20260925/release-outcome.json`
- 全流程证据：`deliverables/releases/v1.13.32-ui-optimization-local-20260925/evidence/final-flow-task403/`
- 下载 PDF：`deliverables/releases/v1.13.32-ui-optimization-local-20260925/evidence/final-flow-task403/result.pdf`
- 正式交付验收：`evidence/final-flow-task403/formal-delivery-accepted.json`
- 最终归档：`evidence/final-flow-task403/task-archived.json`
- 390×844 截图：`evidence/final-flow-task403/formal-preview-390x844.png`、`evidence/final-flow-task403/archive-390x844.png`

## 8. 已记录但不阻断本轮闭环的问题

1. 正式成果面板额外读取 conversation deliverables 失败时会显示英文兜底 `Conversation deliverables are unavailable`；task-scoped 正式成果仍可预览、下载和验收。后续应改为中文且不弱化正式成果成功状态。
2. 已完成/已归档事项重新进入时，执行摘要可能先显示“尚未确认”，需显式读取执行历史；不得因此否定已验收正式交付或已归档任务事实。
3. 协作工作台读取曾出现一次 503；本轮 work item、正式交付、验收与归档的权威接口均成功。后续需独立追踪 503，不用 UI 文案掩盖。

以上三项为后续 bugfix 输入，不改变本次主流程 PASS，也不得在未来 smoke 中静默忽略。

## 9. 2026-09-25 Web 1.13.33 快速冒烟追加记录

| 项目 | 实际值 |
| --- | --- |
| 发布 | Web `release/1.13.33` / `d79af65ed0c493b31a82f8d26206b949ea662bf4` |
| 任务 | `404` / `请生成一页《聚义厅冒烟测试结果》PDF，写明任务标题、执行 Agent、生成时间和“冒烟通过”结论。` |
| Agent | 林冲 `jyt-jiafewnnv58ec2379c-linchong` |
| 资料 | 0 份 |
| conversation | `1760458004747` |
| execution | `pwe_2798de29c56a412080779f8578c47547`，终态 `OUTPUT_COMMITTED` |
| run | `pwe_run_2abe42eb40674c04b6c679cd03ef9e19` |
| work item | `wi_legacy_e49ffb82576e12e107c09407fefa0976`，最终 `completed` |
| 正式交付 | `pwe_delivery_5a3ee0906994150a8d386abe688dfca7a1d3deda80839273995248c20a1bb415`，最终 `accepted` |
| PDF | 1 页，14,729 bytes，SHA-256 `42bf72a78ab78c98eb05bbdfde0e1d3e7c7623ebd229df4c83c3a60afdcd1d5f` |
| 任务终态 | `archived`，taskVersion `4` |
| 视口 | Chromium 390×844 移动仿真；`innerWidth=scrollWidth=390` |
| 用时 | 约 13 分 23 秒（事项创建至归档） |
| 结果 | JYT-SMK-01～14 PASS；未主动执行扩展恢复/跨身份破坏场景 |

本轮所有业务写操作均通过真实 UI 完成；只读终态核对使用认证 GET。正式 PDF 在验收前及归档后均通过 UI 预览和下载，归档前后 SHA-256 一致。证据见 `deliverables/releases/v1.13.33-ui-optimization-r2-local-20260925/evidence/fast-smoke-20260925142825/`。

新增非阻断观察：协作工作台首次回读可短暂不可用但一次只读刷新恢复；完成/归档详情的 execution 摘要仍可能需手动重读；PDF 中角色 Agent 与底层模型名称口径不统一；部分二级面板返回后多一步导航。以上已作为后续 bugfix 输入记录在本次 `closure-summary.md`。

## 10. 2026-09-26 Web 1.13.37 / 当前 1.13.38 快速冒烟追加记录

本轮验证对象为已合入 `feature/ui-optimization` 最新提交 `050f658413c1ff583a2b2912c1c134f4c4bdf64a` 的 Web 1.13.37：合入提交 `328e9b6`，发布提交 `95ce14d54c19f4a7d6aa64d1fb547eb8c03d72fb`，tree `5d6d7a92092d9cd94a6ae0c5428f7c34971bc807`。1.13.37 完成精确发布后，另一项已授权任务发布了其后代 Web 1.13.38 `21e71dfdd9a5c20856ac02b689d4045db3bc6273`；最终业务冒烟运行于包含本次 UI 优化的当前 1.13.38。

| 项目 | 实际值 |
| --- | --- |
| 移动基线 | Chromium `390×844` 移动竖屏仿真；`innerWidth=scrollWidth=390` |
| 任务 | `408` / `请生成一页《聚义厅冒烟测试结果》PDF，写明任务标题、执行 Agent、生成时间和“冒烟通过”结论。` |
| Agent | 林冲 `jyt-jiafewnnv58ec2379c-linchong`；未使用扈三娘 |
| 资料 | 首次办理 0 份；返工只固定输入第 1 版 PDF |
| conversation | `1760458004751` |
| 首次 execution/run | `pwe_f27461b622df4da59ad6b2d137d88ec1` / `pwe_run_b1e6c2601ce140ccbefd3bb58424d971`，终态 `OUTPUT_COMMITTED` |
| 首次交付 | `pwe_delivery_e8f2e0d9f498858d8202cee74727dc66cb140c49728f9a9879ab0504efd05a04`，第 1 版 `changes_requested` |
| 返工 execution/run | `pwe_05f8812a122a429d9dec13cbb5c7440d` / `pwe_run_d5b0e2765b764ceeb668b2ee8b4df63b`，终态 `OUTPUT_COMMITTED` |
| 最终正式交付 | `pwe_delivery_0a70d3f2ccf0fdb242328ba1f5cb97a9f46b5f62c9f5e68089bb3409abc328b3`，第 2 版 `accepted` |
| 最终 PDF | 1 页，4,512 bytes，SHA-256 `085e1ae94e7ef5d8668f599edcd68265ef8e768d6832161a9401543806919936` |
| PDF 正文 | 任务标题、执行 Agent“林冲”、生成时间和“冒烟通过”结论齐全 |
| 任务终态 | `archived`，taskVersion `6` |
| 用时 | 创建至归档 39 分 38 秒；首次正式 execution 创建至归档 24 分 53 秒 |
| 结果 | 主流程闭环 PASS；同时实际覆盖“要求修改 → 固定版本返工 → 第 2 版验收” |

第 1 版 PDF 将“执行 Agent”写为底层 Provider 模型 `GPT-5.6 Luna`，不符合业务 Agent“林冲”的验收口径。本轮未降低标准直接通过，而是经真实 UI 提交“要求修改”，以固定第 1 版 PDF 创建返工 execution；第 2 版改为“执行 Agent 林冲”后再验收、归档。所有业务写操作均通过真实 UI 完成，只读终态核验使用认证 GET；外部 Provider 未知费用已获用户授权。

20 分钟目标本轮未达成，主要耗时来自认证/API 并发切换后的恢复，以及发现语义错误后执行一次真实返工；未以性能门槛取消请求或伪报成功。正常链路本身可完成，且返工后的固定成果在归档前后通过 UI 预览、下载，SHA-256 完全一致。

证据目录：`deliverables/releases/v1.13.37-ui-optimization-r3-local-20260925/evidence/fast-smoke-20260925232937/`。关键证据包括：

- `14-start-formal-execution.log`：首次 TASK execution 202 回执；
- `20-open408-results-clean.json`：第 1 版正式 `submitted` 交付及 producerAgentId；
- `26-request-changes.json`、`28-create-rework-click.log`：要求修改和返工创建；
- `31-rework-delivery-ui.json`、`33-preview-revision2-ui.json`：第 2 版正式交付及正确正文；
- `34-ui-download-revision2.json`、`35-accept-revision2.json`：下载摘要与验收回执；
- `36-archive-task.log`、`39-reopen-archive-task408.json`：归档及案卷重开；
- `42-archive-ui-download.json`、`44-archive-download-sha256.txt`：归档后下载及摘要一致；
- `43-archive-preview-390x844.png`：归档后移动竖屏正式成果预览。

本轮新增非阻断 bugfix 输入：

1. `/agent/tasks/408/workspace` 在后半段持续返回 `TASK_WORKSPACE_UNAVAILABLE` 503，事项详情因而显示“协作工作台不可用”，但 task-scoped 正式交付、验收和归档接口正常。
2. 首页事项卡在任务已经 `completed` 时仍短暂显示“办理中”，重新打开详情才取得权威终态；概览摘要需要更及时失效或刷新。
3. 从案卷重开后，正式成果可读取、预览、下载且验收态正确，但返工上下文未自动恢复，面板仍提示“进入本榜文议事”；只读成果不受影响。
4. Provider 初次生成时把业务 Agent 写成模型名，正式执行提示词应明确区分“承办 Agent”和“底层 Provider”。

