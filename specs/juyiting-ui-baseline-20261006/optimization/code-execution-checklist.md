# 代码实施清单、测试落点与提交顺序

> 2026-10-23整理：本文保留原日期源码/设计定位，不按旧排期执行、不从“待实现”文字推断当前代码。当前范围与交互见 [spec.md](spec.md)，剩余工作见 [tasks.md](tasks.md)，后续成果多选及历史稿验收见 [最新详设](../../juyiting-external-commission-mvp/design.md#selected-output-acceptance)。发布/验收独立查证。

2026-10-18。本文把原执行计划E00–E09展开成可提交的代码包。**未运行应用测试、未实现功能、未发布。** 单Owner自检，不另设Reviewer或逐包审批；未知工期不估造。

## 1. 按顺序编码

| 包 | 对应E/A/B | 改动/产物 | 必须先有的输入 | 退出条件 |
|---|---|---|---|---|
| C00 原型补齐 | E00；全部A | 原型现有文件、规格C01–C15、P19、状态历史、自然语言修改，无引用修改按钮 | 本次Web/Backend代码详设 | 原型和规格一致，PC/手机可演示；无另一套页面 |
| C01 合同与结构 | E01；B03/B05/B06 | 后端B2/B4 SQL/initializer、B4/B5 DTO+codec、v5 Runtime/Java/Web联合契约、完整wire fixtures及接口目录 | code-contract-fixtures.json | serializer→consumer一致；fresh/upgrade/重复升级/异构schema都测；不是仅加表 |
| C02 创建收敛 | E03；B01/B02、A03 | HallTaskCreationService签名/实现、requireTaskCreate、顶部formalDraft、共用待点将详情 | C00、创建v2现行合同 | 长正文/资料同事务，失败无半建，成功待点将；明确目标确认一次首轮 |
| C03 自动正式提交 | E04；B05 | finalization终止SUBMITTED、ChatActionFinalService事件、outbox消费、新SubmissionService | C01 | 关闭浏览器也能提交；重复事件唯一批次；普通结果不待验收；accept从自动路径不可达 |
| C04 人工决定/原议事返工 | E04；B04/B06/B07/B08 | review controller/service/store/read model、v5 REVISION_REQUEST/outbox、admitDeliveryRevisionContinuation、固定manifest源构造 | C01/C03 | 同事务决定+复用USER的CHAT子执行+回执；文本/文件/多成果都不需伪workspace输出；UNKNOWN恢复、并发互斥 |
| C05 状态查询与共享UI | E05；B03、A03/A07 | phase查询/计数、hallTaskPresentation、useHallDeliveryReview/Dialog、三个入口接线 | C00/C01/C04 | 一种投影、同批次、无重复请求/验收条；完成由权威决定不是finalization.COMPLETED |
| C06 共享布局 | E02；A01/A02/A04/A05/A06/A08 | ChatPanel全屏、选材/预览、语音/附件、名册、页头与theme | C00；可与C02–C04非重叠并行 | 所有操作可见可关、焦点可用、多选不挤压；不改私聊权限 |
| C07 辅助页/整站复核 | E06；A09 | workspace/library/reader/messages/catalog/map/help及19页回归 | C05/C06 | 既有功能不裁剪，帮助包含验收；公共/账户证据边界明确 |
| C08 正式验证/集成/版本交付 | E07/E08 | Flow4403172/5260799固定候选、测试报告、制品、发布记录 | C01–C07；部署另需实际授权 | 精确源码证据；合develop不部署；版本发布后真实新数据回读 |
| C09 旧私人链 | E09；B07 | 原队列/Runtime/输出独立定位和必要修复范围 | 原生产证据，实际操作按授权 | 不用新TASK入口替代旧问题根因，不静默迁移旧PRIVATE |

每包可单独提交，但新合同/新入口须协调切换，不能在半成品状态启用。后端B2/B4是实质事务和schema改动；C06纯样式可独立推进。禁止为加快进度暂时前端伪造submitted或调用旧accept再改标签。

## 2. 既有测试按方法扩展

### API Agent

目录：`api/agent/jia-agent-service/src/test/java/cn/jia/agent/`。

| 既有测试类 | 新增/调整方法（目标名） | 核心断言 |
|---|---|---|
| `service/impl/HallTaskCreationServiceImplTest` | `createsDraftTaskThroughAtomicV2WithPinnedInputs` | adapter委托v2而非裸createTask；无指派/Provider副作用 |
| `service/impl/AgentTaskCreationOperationRealTransactionTest`、`AgentTaskCreationOperationMySqlTest` | `draftSubmitAndMaterialLinksRollbackTogether` | 第二资料撤权/写入失败时root、links、draft提交一起回滚 |
| `service/impl/AgentSelectedOutputFinalizationServiceImplTest` | `submittedReplayNeverAcceptsOrReleasesAnotherLease` | 当前交付存在先核对；旧lease不重新领取；无人为决定不completed |
| `service/impl/AgentTaskFormalDeliveryDecisionServiceImplTest` | 保留`acceptedDecisionCompletesTaskAndWorkItem`、`changesRequestedReturnsSubmittedWorkToReadyAndRequiresNewLeaseLater`；加`concurrentAcceptAndRevisionHasSingleWinner` | root/workItem/member/event同事务；两个决定只有一个生效 |
| `service/impl/AgentTaskReworkExecutionServiceImplTest` | `publishedWorkspaceReworkContractRemainsScoped` | 既有文件用途不回退；文本不硬传该接口 |
| 新增`service/impl/AgentTaskPhaseProjectionTest` | `searchAndCountsUseIdenticalScopedPredicates` | all状态、keyword/ability、跨owner、未知根枚举、reviewing不一致；不是只测试前端四标签 |

新增真实并发/回滚测试使用当前MySQL fixture/事务设施，不用mock计数代替真实唯一约束/CAS。

### API Chat

已核对`api/chat/jia-chat-service/build.gradle`存在**`mmdU3Finalization`任务**，sourceSet从`src/mmdRegressionTest/java`白名单包含5个类；只把新测试文件放该目录不会自动运行，必须更新include。

| 既有类/新增类 | 修改与断言 |
|---|---|
| `ChatSelectedOutputFinalizationServiceTest` | 将`actualHappyPathPreservesExactOrderedSelectionAcrossAllDurablePhases`改为止于SUBMITTED；`readySubmissionAndAcceptanceAckLossRecoverWithoutRepeatingEarlierAuthority`拆成提交回执丢失恢复与新review决定恢复；verify accept never。保留源越权/摘要/MIME/长度/只读GET/同键异体测试 |
| `ChatSelectedOutputFinalizationStoreTest` / SchemaInitializerTest | completed+SUBMITTED合法、空delivery非法；新增FORMAL_ARTIFACT union/contract_version与v2摘要；历史accepted只读；新schema upgrade/readback及丢回执场景 |
| `AgentTaskSelectedOutputFinalizationControllerTest` | POST200表示提交成功而非完成事项；202处理中；GET不写；失败HTTP不能带成功receipt |
| `ChatCompletedMessageSourceServiceTest` | 普通ANSWER/CLARIFY不晋升；deliverable及消息固定来源/替换校验继续通过 |
| 新增`ChatDeliverySubmissionServiceTest` | final事务回滚不留事件；同事件重投一次正式交付；三项仅替换一项/跨话头保留固定artifact源；消费失败重试同key；先提交已成功再丢ACK不重复；现submitted不被普通新答复替换 |
| 新增`ChatTaskDeliveryReviewServiceTest` | ACCEPT、文本REQUEST_CHANGES、多成果文件REQUEST_CHANGES；变更指派/撤权/旧generation/旧batch拒绝；没有keyword拒收；同键异体冲突 |
| 新增`ChatTaskDeliveryReviewTransactionTest` | 使用真实Spring代理/MySQL：决定成功后admission失败全部回滚；COMMITTED回执丢失GET可取；ACCEPT与REQUEST_CHANGES竞争唯一成功；跨scope相同key隔离 |
| 新增`ChatTaskDeliveryReviewControllerTest` / StoreTest / SchemaInitializerTest | 精确字段、版本字符串、重复/未知字段、错误HTTP、索引/唯一约束、只读GET、历史输入不续跑 |
| 新增`ChatTaskDeliveryReviewReadServiceTest` | 原话头消息删除/换话头仍能由正式manifest找回；source缺失只读；manifest不冒充结果数量；同批摘要两端完全一致 |

新Chat类放`src/mmdRegressionTest/java/cn/jia/chat/{service,api,config}/`，本次扩展既有mmdU3Finalization include及description覆盖，不新建另一个测试框架。关键relay测试新增在同sourceSet用实际Relay/Outbox service，不能只测试新增Service而漏default分派。

### Web

现有测试入口为Mocha+tests/setup.js，**不是Vitest/Jest**。默认`.mocharc.json`含`tests/*.test.js`；新增业务测试沿该目录。

| 既有测试文件（web/tests） | 修改/新增断言 |
|---|---|
| `juyiting-requirement-materials-intake.test.js`、`juyiting-hall-drafts.test.js`、`juyiting-hall-draft-editor-component.test.js` | 顶部正式草稿→提交、长正文/资料、执行回执必须null、历史私人不改kind、创建未知跨入口不重建 |
| `juyiting-point-and-start.test.js`、`juyiting-pending-requirement-roster.test.js` | 保存即待点将；选择不指派、取消保留、明确Agent/版本、一次首轮 |
| `juyiting-bounty-finalization.test.js`、`juyiting-finalization-task-refresh.test.js` | COMPLETED+SUBMITTED只提示提交完成，不触发task-completed；mount/watch只GET；新key与原意图隔离 |
| `juyiting-bounty-output-gallery.test.js`、`juyiting-bounty-output-catalog.test.js`、`juyiting-formal-review-component.test.js` | 三入口同批次；仅一入口；普通/历史无验收；RESULT计数与整批冻结区分；成果卡无下载/保存，预览仍可下载 |
| `formal-delivery-od10.test.js` | 历史正式读取保留，新决定改走review operation，不用循环data解包 |
| `juyiting-composer-more-menu.test.js`、`juyiting-voice-conversation.test.js` | 录音框内、取消/转写恢复、权限错误、无自动发送、引用chip未发送不拒收 |
| 新增`juyiting-task-presentation.test.js` | 全根枚举/当前交付/UNKNOWN/终态及五消费者一致；查询与计数输入一致 |
| 新增`juyiting-delivery-review.test.js` | 实际consumer解析目标serializer fixture；冻结版本/摘要；双击、404、5xx、同键异体、断网reload、迟到响应与身份切换 |
| 新增`juyiting-delivery-review-component.test.js` | open/close不POST、确认才POST、REQUEST_CHANGES回执只attach不二次send、已完成禁用 |

原型浏览器工具复用根spec `tools/check-browser.cjs`/`check-prototype.mjs`；增加场景到既有工具，不把原型mock回执当正式产品合同。

## 3. 可复制验证入口（执行时绑定候选，本文未执行）

先读最新根/命中模块build.gradle；以下为Flow后端候选的既有编排入口任务参数，`${API_CANDIDATE}`必须是**云端固定commit的干净API目录**，不是生产安装目录。正式测试不在本机运行：

```bash
python3 ops/orchestration/cyf_orchestrator.py gradle -- \
  -p "$API_CANDIDATE" :chat:jia-chat-service:mmdU3Finalization
python3 ops/orchestration/cyf_orchestrator.py gradle -- \
  -p "$API_CANDIDATE" :agent:jia-agent-service:test \
  --tests 'cn.jia.agent.service.impl.*FormalDelivery*Test' \
  --tests 'cn.jia.agent.service.impl.*SelectedOutputFinalization*Test' \
  --tests 'cn.jia.agent.service.impl.*TaskCreation*Test' \
  --tests 'cn.jia.agent.service.impl.AgentTaskPhaseProjectionTest'
python3 ops/orchestration/cyf_orchestrator.py gradle -- \
  -p "$API_CANDIDATE" validateLayering
```

三次按顺序串行，使用Flow任务的编排器路径/工作目录。已有全量CI任务、依赖完整性与fresh JAR仍执行，不能以上述定向命令替代正式发布任务。Agent现有MySQL测试fixture沿其已有测试配置，不使用生产数据库。新增类和include未落地前不能将这些命令标为通过。

前端定向诊断（仅本机开发反馈，非Flow正式证据；新增测试文件实现后才运行）：

```bash
cd web
node --import tsx ./node_modules/mocha/bin/mocha.js --no-config \
  --require ./tests/setup.js --timeout 10000 --exit --reporter spec \
  tests/juyiting-task-presentation.test.js \
  tests/juyiting-delivery-review.test.js \
  tests/juyiting-delivery-review-component.test.js \
  tests/juyiting-bounty-finalization.test.js \
  tests/juyiting-hall-draft-editor-component.test.js
```

前端正式仍由Flow4403172运行实际CI测试与生产构建；后端5260799。部署绑定应用版本/commit/tree/同Run制品SHA，不新增流水线，不自动发布develop。

## 4. 成对端到端用例（不得遗漏媒体与返工）

1. 首页纯文本→待点将→确认Agent→普通答复不待验收→明确交付→关闭浏览器→后台submitted→重新进入待验收→确认→completed。
2. 顶部保存草稿（长正文＋多资料）→开始办事→与首页相同后半链；不存在新PRIVATE_CASE、无资料丢失/重复创建。
3. submitted文本→普通提问仍submitted→不点引用直接发送明确修改→Agent提议→同事务changes_requested＋原议事关联子请求（复用原USER消息）→新固定版本→submitted→人工验收。另测有引用但仅提问不拒收、多成果/旧批次澄清、重复回调、并发验收、撤权及执行失败恢复。
4. 图/音频/多文件：普通输出不自动提交；明确交付固定整批；只一验收按钮；验收范围不受文件预览/切换影响。TASK已有交付不二次晋升。
5. 三入口并发验收/修改、过期批次、断网/响应丢失、刷新/身份切换、话头切换/删除、撤权；观察根/交付/操作/消息/事件唯一性而非只看Toast。
6. 1440/390/320、断点两侧、低高度/键盘：资料20项样例、长名字、PDF分页、返回/关闭/Escape、焦点、录音/转写、消息滚动与完成只读。

每例记录候选源码、真实请求关联、权威状态回读、浏览器截图/DOM、Flow Run与未覆盖项。历史事项466仅作定位证据，不重标为新合同成功。

## 5. 收口标准

开发前不再需要选择“是否拆提交与验收/文本返工怎么做/哪个页面负责决定”：上述方案已经明确。实际安装schema、当前部署产物、公共议事入口与真机权限仍属于现场验证输入，不编造成已知。若发现源码基线变化，先更新命中函数与fixture，不在未核对情况下照抄旧行号。

实施完成后将稳定知识回写既有模块/架构说明，原始需求和核对证据留本目录。最新原型规格只回写Web原型目录，本次变更方案/代码设计仍在optimization。


## 2026-10-18 已确认：议事自然语言修改与控制边界

直接说出明确修改要求即可；移除“引用修改”按钮，多成果通过名称/内容及对话澄清定位。普通提问/赞同保持待验收，含糊表达在原议事澄清。不得把引用、关键词或“可以”当作正式决定。验收仍须用户点击并确认。

职责：用户作决定；Agent理解并提出结构化修改请求；后端核验来源消息、ACL、批次/版本、幂等及事务并控制状态；前端呈现回执、不自行切换状态。后端不能消除全部语义误判，语义不确定时不执行返工。

流转：待验收 →（正式修改与续执行登记提交成功）进行中 →（新成果正式提交）待验收 →（用户明确验收）已完成。普通问答/澄清不改变待验收。历史成果保留，多成果指代不清时先问清目标。

实施以code-backend-design.md B4.1、code-frontend-design.md F4为准；自然语言发送一次，复用原USER消息并创建关联子request，不重开父request、不重复发送正文。验收与修改并发以固定批次版本校验，未知结果查询原操作。此为目标设计/离线演示，不表示产品或生产已实现。


## 2026-10-18 源码推演修正入口

详见[source-design-review.md](source-design-review.md)：10项缺口及R01–R10源码依据，v5三端协议、不可变父请求＋关联子执行、来源快照、待验收执行门控、恢复/版本/前端上下文等修正已并入代码级详设。此为目标设计，不是生产已实现。

执行顺序调整：C01先做V01 Runtime→Java→Web严格合同探针；C04先做V02真实DB事务和单消息子执行，再以V03文本“提交→修改→再提交→验收”打通垂直闭环；通过后再扩多成果/19页。新增Runtime为本链必需参与组件，不放到仅排查旧私人链的C09。V04–V06并发/恢复/成果/前端反例按复核文档补充。正式验证仍走项目Flow；Runtime源码/流程单独固定并遵循其仓库规则，不借本次审查授权发布。

## 2026-10-18 C00/C07退出条件增补

执行[page-prototype-recheck.md](page-prototype-recheck.md) U01–U10，当前均为待实现，不把本轮截图计作这些修复完成。C00须先补任务技能、异常归档、统一复核、批次操作归属、PDF分页、版本管理、多事项消息、长名册、验收帮助及六页同状态fixture。

C05验证两处验收入口均先复核同一固定批次、取消复核无副作用、返回议事不拒收；C07保留19页覆盖矩阵，P08真实入口和P18禁用边界单列；320/390/1440、20附件、长内容、焦点/关闭及真机软键盘分开记录。生产只读保护阻断不计缺陷，失败诊断不记PASS。正式Flow/写链验证沿原计划，不被本轮读页替代。

## 2026-10-18 原型补缺已落地

[原型修正与复查](prototype-fix-recheck.md)记录U01–U10在现原型中的实现及精确输入检查。前节“待补原型”是实页核对时结论，本轮已补离线表达；产品前后端/Runtime实现、生产状态不一致及V01–V03仍未完成，不把原型通过作为C01–C09完成证据。

## 2026-10-18 最新布局退出条件（C00/C05/C06）

1. 议事验收只出现在顶部slot；消息/文件卡无按钮；private/public无验收。点击只打开复核，取消/返回不写决定、不改草稿。状态变化使触发点消失时焦点有安全回落。
2. 四图标每项44×44、SVG20×20、线宽1.8、中心一致且无单独margin；title/aria-label准确；320/390/520/523/1440测量，不能只检查不横溢。
3. 补充源码`durableCancelTarget`第五图标及多Agent可操作targetChips原型样例，再测窄屏/键盘/取消与目标不丢；当前四图标测试不能替代。
4. `resizeTextarea`与44px紧凑样式一致；长文/IME/换行/软键盘不挤压消息；终态关闭录音与选择器而不删草稿；切回活动事项恢复。
5. 五筛选单行横滚无统计行；原计数加载失败状态不误删。刷新后SVG路径有效、bbox非零、资源版本匹配、草稿保持，不能通过清数据规避。


### 2026-10-19 发布后异常修正进度
补充必测：无selectedAgent进入正式议事后接入ADMITTED回执并读回用户消息；浏览对象变化不得中断本会话、真实target/身份变化必须隔离迟到响应；纯空白delta须保序；模型收到正确多轮内容后必须按当轮任务答复。当前前两项本地诊断通过，空白delta已有回归待Flow，模型行为对照尚待实施；禁止按历史成功标本轮通过。
证据与源码基线：`../evidence/reply-followup-diagnosis-20261019/verification.md`。


### 2026-10-19 最新正式验证状态（13:01 CST）
Web59ba8a8 / Flow4403172/232 SUCCESS（3054通过、2pending，构建/扫描成功）。API cd2146f408e692fc58424390e89a40d2f10eb7d2 / tree b757d4cf1b4d3c1b864a2be47106ba0e0b734d56 / Flow5260799/161 SUCCESS（2420项中2325通过、95跳过、0失败/错误；分层检查及fresh bootJar成功）。此前Run159的5项失败已由Run160错误回执定位：旧normalizer误要求requestId/messageId相等，注册被拒绝；已修正两种身份的混用，并覆盖17项normalizer、1项command wire和5组分片回归。不改ACL、运行时证明或序号连续性，不通过改相同ID回避问题。
源码已集成develop，未部署；制品仅有Flow元数据，尚未独立下载验包。Runtime重复回复“收到。”及完整生产议事/验收闭环仍待解决，不标整体方案完成。本次不改变页面/交互，无需另改原型。完整证据：specs/juyiting-ui-baseline-20261006/evidence/reply-followup-diagnosis-20261019/verification.md（项目根相对路径）。


### 2026-10-19 Runtime复测约束（未关闭项）
API cd2146f408/Flow161及Web59ba8a8/Flow232正式CI通过、未发布。Runtime隔离候选f94c254f956f09717711486e8941847ff2bd95c7未合入/安装；80项本地诊断与注入/缺图模型检查通过，但旧、新策略fresh-thread均能回答43。生产task467原thread再次仅回复“收到。”（USER1859218/ASSISTANT1859219），根因未闭环。带同文AGENTS的三轮对照第2轮出现空text合同失败，不标整组通过。
执行顺序：固定原thread与fresh-thread差异证据→针对性修正及重复验证→独立版本化发布→正式议事停止/继续发送/有效成果/人工验收回归。禁止清历史、盲重发、将COMPLETED当业务成功或自动验收。无需新增页面/按钮，原型保留当前简化流程。本轮详设补充见code-backend-design.md B10；完整证据见../evidence/reply-followup-diagnosis-20261019/verification.md。

## G-REG. 监听/回执回归矩阵（2026-10-19，待落地）

规则唯一正文：`code-frontend-design.md#f-guard-响应式监听与异步回执安全规则`。基线Web f112b0b；当前同代接纳失败已在独立诊断复现，以下不是已通过清单。此前“未发布/先查模型”的条目是历史；最新为API1.16.10/Flow162、Web1.16.11/Flow233已上线，模型专项暂停，USER即时显示仍待修复。

首要落点：扩展`web/tests/juyiting-typed-deliberation-page-routing.test.js`；composable、消息合并和取消相关回归复用各自既有测试，不新建独立runner。

| ID | 必测输入/交错 | 必须断言 |
| --- | --- | --- |
| G-REG-01 | activeRequest为空、已知权威代次1，ADMITTED读回同代request | 接纳成功；本人消息立即可见；不自失效；一次接纳只触发一次后续正文加载，无第二次POST |
| G-REG-02 | 已存在同代request，新轮次快速COMPLETED | 新USER/ASSISTANT均保留，不把前轮结果当本轮，不重复消息 |
| G-REG-03 | 相同绑定下更换对象引用、刷新目录、浏览另一事项/Agent | 不误判切会话；无reset递归、恢复请求风暴或重复POST |
| G-REG-04 | GET等待/投影提交时切用户、授权、会话、模式、真实指派/目标 | 参数化逐项覆盖；旧响应不污染新作用域，旧清理不释放新操作锁/清空新草稿 |
| G-REG-05 | 权威generation 1→2；切另一会话但代次同为1 | 均失效旧操作；不能仅比较代次数值放行 |
| G-REG-06 | 上下文未就绪、权威来源冲突、退出后旧缓存仍有值 | 不发送、不接受不可信投影；恢复只读；不以空值通配 |
| G-REG-07 | 迟到低版本、重复receipt/stream事件、不同request | 不回退、不串轮、不重复；保留现有严格归属校验 |
| G-REG-08 | 正文GET与新delta/final交错、网络返回乱序 | 旧列表不能覆盖新流内容；USER和ASSISTANT按稳定身份正确合并 |
| G-REG-09 | POST成功后正文GET失败、断线或重新打开页面 | 能只读恢复原请求；不重复POST、不把已接纳误报为未保存 |
| G-REG-10 | 真实切换触发两个原watch、卸载/重新挂载 | 统一切换判定、无循环/重复恢复，旧订阅清理，仅当前作用域可写 |
| G-REG-11 | 停止与最终事件竞争、停止后新轮次 | 保留终态/版本规则及可恢复错误，旧取消结果不破坏新轮次 |
| G-REG-12 | 吴用真实界面PC/移动端发送、多轮、重载 | 当前页USER即时显示、流回复保留、重载不丢/不重；未提交成果不显示可验收，验收须用户明确操作 |

执行顺序：固定基线/作用域与原型行为 → G-REG-01真实watch红测 → 最小修正及受影响矩阵 → 实际组件/浏览器 → 精确候选Flow正式测试 → 集成记录。发布另按实际授权；线上冒烟失败不能把已安装版本写成业务验收通过。Owner在现有handoff记录每项结果和证据；不新增Reviewer或人为逐阶段审批，不以模型专项暂停免除页面回归。


### G-REG-13：权威context的组合自失效（2026-10-19新增，待实现）

覆盖`useHallBountyAssignmentContext`真实fingerprint/reset和JuyiHall真实watch：同scope已有权威generation1、activeRequest空，接纳同代request后projection不清空、followup epoch不增加、正文同步成功。分别注入GET刷新开始、目录reset、任务版本变更、身份切换、generation冲突及GET失败；只有同代补齐可以继续，真实切换仍隔离，失败不以旧绑定继续写。不得只测试页面两个watch或恒真isCurrent。执行边界和改法见implementation-ready.md D01；全链仍保留G-REG-01至12及V01–V06。

### 2026-10-20 SSE断流验收增补（不扩业务范围）
- [x] Web255/f08e427正式测试3125通过、2pending，同Run制品/366安装文件/公网资源核验，配置恢复APPLIED。
- [x] API根因定位：持久回放进入64条急切缓冲导致溢出；只取消认证durable SSE的外层buffer，保留live限界/持久补齐/ACL/取消清理。
- [x] API9ca2776c27/1.16.18，Flow195正式4项新增回归、全部既定选择器（包含SensitiveResponseBodyAdviceTest）、分层检查、freshJAR、同Run部署及在线摘要核验；2606通过/122skip。
- [ ] PC/移动真实474吴用原会话：新消息仅发送一次，断开/重连不刷新即显示持久最终回复、不持续等待；区分浏览器注入断网与真实历史大回放。
- [ ] 后端发布后同会话大量历史事件完整回放且无队列溢出；删除/换身份/取消仍按既定合同。
- 本清单不关闭PRIVATE D06缺原始context、历史v4材料以及未覆盖媒体/多Agent/付费等OPEN项。

- 12:40复核修正：上述PC/移动“完整恢复”复选框保持未通过。CDP offline不可靠终止现存SSE；正文可见但失败的成果投影读回未自动补齐。12:37受控reader错误确认原重连→GET→SSE路径，但不能代替全部在途流程。下一批按序只收口：canonical TaskDTO恢复（保留版本/ACL fence）→目录与typed-outcome失败后的原恢复调度→精确成果缓存失效后一次刷新→PC/移动预览/继续修改/验收。无新监听、无自动重发、无猜选成果；详见verification.md12:40记录。

### G-REG-DFX-PROJECTION（2026-10-20）
- 编码候选Web1.16.24：50107f38a757a5ce58d298965a953a353d7b48b1 / tree2adbc30cdc5cdbd7db3f41375751113e22e448b8。
- 本机定向149项：canonical task单飞/作用域/版本不倒退；健康SSE下失败GET复用原timer；typed失败与404；精确预览旧非空缓存/一次刷新/权限切换/迟到点击。只作开发反馈。
- 真实页面组件及followup路由122项定向通过；补齐原测试替身新方法，不改生产行为/不放宽断言。Flow256原候选3137通过、5失败（替身缺依赖）、2pending，未部署；不能作为发布证据。修正后Flow257统一验证中。
- 待线上：自有474连续自然修改不刷新即可发送；预加载旧成果后生成新版本仍可预览；精确阻断GET且SSE存活，恢复读取后自动补齐；PC/移动新建→点将→议事→验收。注入故障与原生断流分开记证据，不将模型回复或页面截图等同正式交付/验收。
- 13:30收口：Flow257 SUCCESS，3142pass/2pending，366安装文件和公网入口/议事JS/CSS一致，配置恢复readback APPLIED。当前三项DFX生产复测通过；474/477/478三条显式ACCEPT均COMMITTED/COMPLETED/ACCEPTED，终态composer隐藏。PC477创建曾被测试runner错误许可路径拦截，在UI按原键确认继续成功；移动478新建无此拦截。不是业务接口失败，不掩盖初次测试步骤。原生断网/物理移动设备/媒体/多Agent/付费/全页面不在本轮完成结论内。
