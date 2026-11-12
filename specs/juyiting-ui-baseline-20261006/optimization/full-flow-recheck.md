# 生产完整主链路与最新 develop 核对

日期：2026-10-17（Asia/Shanghai）。Owner：当前线程。**结论：正式文本事项主链路通过；顶部私人交办未闭环；目标四阶段流程尚未实现。不是全产品或所有异常分支通过。**

用户本轮授权创建测试数据并进行完整流程核对。仅对本轮自建记录操作；未部署、未修改产品代码、未充值/招募/扩大付费权限。普通文本Agent已真实执行，实际费用未另行审计，不声称零费用。

## 1. 两条真实路径的结果

### A. 首页“开始办事”：已完成真实人工验收

测试标记 `CYF-FLOW-AUDIT-20261017`，正式事项 **466**，原议事 **1760458006507**。

| 步骤 / 时间 | 实际操作与权威结果 | 证据 |
|---|---|---|
| 17:56 创建 | 输入三行会议准备清单需求并点击开始办事；创建一次正式事项。随后列表可读到466、待点将；未指派时已持久化 | `01-created`、`02-persisted-detail` |
| 创建后的导航 | 自动打开点将册；返回事项详情才看到建议承办及交给某Agent操作。不是原型预期的同一详情内推荐确认 | `01-created`、`03-recommendation` |
| 17:58 指定承办 | 实际点击“交给吴用”，`point-and-deliberate`成功后自动建立议事并产生首轮答复，无额外手动开始执行 | `04-point-result`、`05-first-reply` |
| 18:00 多轮修改 | 原议事发送“第二行明确提前10分钟”；Agent真实返回修改后的三行内容，历史保留，无另建事项 | `06-revision-sent`、`07-revised-reply` |
| 18:01 明确交付 | 在同一议事请求将修改版正式交付等待验收；typed-outcome回读`deliverable=true`，带固定messageSource和REPLACE关联 | `08-delivery-request`、`09-delivery-response`、`11-delivery-intent-outcome.json` |
| 交付前实际根状态 | 此时任务仍`assigned`、taskVersion=1、startedAt/completedAt为空，未稳定进入`reviewing`。议事“已完成”是request/turn完成，**不是事项已验收** | `10-task-and-requests.json` |
| 查看与继续修改 | 从事项详情打开“查看正式成果与验收”，展示最后三行文本、确认验收、继续修改；继续修改回原议事，返回后可继续验收。仅跳转没有发起拒收 | `12-after-chat-detail`、`13-formal-results`、`14-mobile-acceptance`、`15-continue-modification` |
| 18:03 人工验收 | 点击一次“确认验收”，调用`POST /agent/tasks/466/finalizations`；回执`COMPLETED / TASK_COMPLETED / deliveryState=ACCEPTED / taskVersion=4`，选择的是最后一轮固定文本 | `16-acceptance-result`、`17-completed-readback.json`、`18-finalization-receipt.json` |
| 刷新后持久化 | 页面重载后首页及事项列表显示已完成；再次打开原议事可读三轮历史，输入和发送均禁用。18:11服务端仍`completed` | `19-reloaded-home`、`26-completed-chat-mobile`、`27-completed-controls.json`、`29/30-completed-chat-*`、`31-final-readback.json` |

正式交付ID：`finalization_delivery_ca85e563cd1be595d5bb0274775bd751148d8700aa8c7f2b586e3f098bd9c0f7`。该记录保留用于复查，未删除或归档。

**重要区分**：本轮完成了“修改普通成果后验收”，没有把它冒充“已提交待验收→要求修改→重新交付→再次验收”。后者需要稳定submitted批次；当前这条一键finalization链在用户点击后连续提交并验收，没有独立待用户决定的正常停留点。不能通过直接改数据库或伪造交付补出通过结果。

### B. 顶部“提出需求”：创建了另一种私人事项，未获得完整结果

- 同账号、同Agent、类似三行纯文本测试，标记 `CYF-FLOW-AUDIT-20261017-入口B`。
- 现页面步骤为保存草稿→确认交办→选择执行好汉→保存更改→确认私人授权→交办。确认页明确“私人交办”，不是正式任务。
- 草稿：`hdr_bc318365fe28439d8b49f56d3390f2b6`；私人事项：`hpc_2904ed1fbb994cbbbc74e65605be0f9b`；执行：`pwe_2b4067a66d9d4bd0a3db35bff4d7ccc7`。
- 18:07:17提交，18:11:10最终回读：`executionMode=PRIVATE`、`state=QUEUED`、`conversationId=null`、`businessTaskId=null`，成果接口`items=[]`。UI“等待执行”，可核对进展/个人整理；收入案卷明确不是验收。证据`21-private-confirmation`、`22-private-submitted`、`23-private-rechecked`、`24-private-case-readback.json`、`25-private-mobile`、`31-final-readback.json`。
- **本轮私人执行→成果→验收未走通**。仅凭这一观察窗口，不能断言永远不会执行，也不能断言Runtime完全没取到命令；最新源码PRIVATE start本身不会持久化RUNNING，QUEUED不能独立证明未开始。未进入Runtime取件/执行日志定位根因，未伪装Agent身份推进。
- 该测试记录仍保留，可能被后续消费者处理。本轮不修改后台状态、不隐藏/归档待处理事实、不取消其他业务事项。

## 2. 最新 develop 对照（不是旧工作区推测）

本轮执行了三个仓库的`git fetch origin develop`，固定结果：

| 仓库 | 新拉取的远端develop commit | 与当前本地HEAD |
|---|---|---|
| 根仓 | `aae93c074960580942112707e9518d831a0ff0af` | 相同 |
| Web | `6fbdb6618b1132316a95db87cca9402de83138e8` | 相同 |
| API | `b76a1d0aeda572767a6d4734d050121d985bd9c9` | 相同 |

通过`git show <固定commit>:<path>`读取21个相关文件并固定SHA-256，均与定向核对的工作区文件一致。未切换分支、未覆盖脏文件、未查询或启动正式Flow验证。下面是**固定源码静态核对 + 当前生产实测相互印证**，不是宣称最新develop已启动完整运行环境，也不以本地HEAD冒充生产部署commit。接口基线为`api/docs/interface-standard.md` v1.2（2026-10-14）。

| 发现 | develop落点（仓库内路径） | 对变更方案的影响 |
|---|---|---|
| 首页已经原子创建TASK | Web `useHallRequirementCreate.js:52–57`及`JuyiHall.vue`首页接线 | 保留现有创建幂等/恢复，不从零重建 |
| 顶部仍是私人CREATE | Web `JuyiHall.vue:542–555`未指定TASK_CREATE；`HallDraftEditor.vue`默认种类和私人授权；API `HallRequestDraftServiceImpl.java:419–433`创建PRIVATE_CASE | B01必须改新需求入口接线和合同，不能只换文案；旧私人记录不自动公开迁移 |
| 点将自动首轮已存在 | Web `useHallPointAndStart.js:84`；API `AgentTaskDeliberationOperationController.java:76` | B02复用point-and-deliberate，不另加指派后再点开始 |
| 修改稿有固定关联 | Web `useHallTypedDeliberation.js`与`bountyOutputCatalog.js:142–196`；生产deliverable/messageSource/REPLACE | 保留当前文字成果链，不将每条答复或任意新消息当拒收 |
| 议事无内联验收、详情另开验收 | Web `BountyDiscussionPanel.vue:43–58`未传acceptance；`BountyAcceptancePanel.vue:8–23`传acceptance；`BountyExecutionOutputs.vue:56–60`条件显示按钮 | A07/B06新增的是议事内固定批次入口；独立验收能力已存在，不重做系统 |
| 一键完成“提交+验收” | API `ChatSelectedOutputFinalizationService.java:101–109`连续submit→ACCEPTING→accept；Web `useHallBountyFinalization.js:172–184` | B05需调整编排合同，明确系统提交与人工决定两个事实；不是简单新增待验收标签 |
| 四状态还未贯通 | Web constants、`BountyPanel.vue:607`仍分散映射且漏reviewing；生产request完成/根assigned同时存在 | B03统一用户主阶段，但保留内部请求状态；“本轮答复完成”不能当事项完成 |
| 完成态混合提示 | `BountyExecutionOutputs.vue:13`空结果提示与finalize成功提示可同时出现；本轮重开议事可见“结果完成后…”和“验收完成”并存 | A07补已验收空集合/历史呈现，不能据此认定交付丢失；服务端已固定交付仍存在 |
| 私人队列独立机制 | API `PersonalWorkspaceExecutionServiceImpl.java:910–925`PRIVATE start仅校验；`:1856–1874`runtimeQueuedCommands按Agent/身份过滤；Runtime控制器提供取件入口 | 不以“等待执行”改“进行中”掩盖缺口；旧链需单独查取件/执行/回执，新主线先收敛 |

以上Web组件位于`web/src/components/juyiting/`，composable位于`web/src/composables/juyiting/`；API服务路径完整清单见受限证据`develop-source-audit.json`。

## 3. 应优先修正的方案

1. **P0：统一新需求入口**。首页和顶部都进入同一正式事项创建合同，保存后推荐/确认Agent→原议事；旧PRIVATE记录继续独立读取，保留ACL及资料范围。
2. **P1：统一用户状态**。主线四阶段，request完成表述为“本轮答复完成”；事项完成必须以验收事实为准。保留失败/取消/归档的次级可查入口。
3. **P1：拆开正式提交与验收决定**。可交付文本不等于正式submitted；服务端成功创建固定交付后才待验收，用户确认后才已完成。复用既有固定版本/幂等/事务/原操作恢复。
4. **P1：议事内唯一批次验收入口**。当前独立验收页保留为历史/补充入口，和议事使用同一交付决定；不保留重复长提示条。同时修正完成后的混合空态提示。
5. **P1：补真正的返工分支验收**。普通修改已实测可用；待验收拒收、修改后新交付、过期批次冲突等须在新提交合同接通后正式验证，不能用普通多轮聊天代替。
6. **旧私人执行缺口另跟踪**。本轮未完成该链，不扩大为无证据的Runtime全重构；先查所属Agent队列取件、开始/输出/提交回执及UI状态读取，不能人工改状态“走通”。

这些项已回写`change-plan.md`与`/home/isp/wsps/cyf/web/prototypes/juyiting/specs/prototype-spec.md`。仍遵循先补唯一交互原型，再改产品实现；本轮没有改原型运行代码。

## 4. 覆盖边界、测试数据与诊断说明

- 正式主链是**真实生产、普通单Agent、纯文本**路径；观察了PC/手机关键页面。未测试图片/语音/附件执行、付费工具、多Agent、网络UNKNOWN恢复、权限切换、并发验收，也未故意制造已提交拒收。
- 两轮新需求均未读取私人资料或操作旧事项。普通文本真实Agent调用已发生；不声明成本账单已审计。
- 写入保护按精确路由单次放行：正式创建1、推荐1、点将1、追加议事2、finalization1；私人草稿创建1、更新2、提交1，共10次。登录与明确只读POST另计。
- 4次推荐POST在未持有当次许可时被拦截（包括开页附带推荐）；一次已明确放行的推荐核验有效。其余阻断不判产品故障，也没有解除全局写保护。
- 测试脚本初次使用错误input选择器，曾保存一个空草稿，已在**同一草稿**补全标记/正文再提交，没有额外残留第二个空草稿；错误快照归入diagnostic，不计真实用户流程缺陷。
- 请求目录三个已发布turn记录DELTA_GAP终止原因，但最终答复存在、请求COMPLETED且后续验收成功。此为附带传输诊断线索，未定位根因，不混同于业务验收失败。
- 完成态只检查输入与发送禁用，未尝试绕过终态发送。私人记录截至18:11仍QUEUED且无成果；不承诺该时刻之后状态不变。
- 生产资源重新读取SHA见`production-loaded-assets.json`，未新查服务器安装版本；不将上午部署版本或本次develop当作当前生产安装证明。

原始证据目录：`/home/isp/wsps/cyf/specs/juyiting-ui-baseline-20261006/evidence/production-full-flow-20261017/`，受限存放，避免公开账号数据。固定源码与阶段检查见该目录`baseline.json`、`develop-source-audit.json`、`verification.json`。正式测试/构建/发布仍须按项目规则使用Flow，本轮不构建、不部署。
