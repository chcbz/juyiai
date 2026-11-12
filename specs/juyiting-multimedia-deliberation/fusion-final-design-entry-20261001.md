# 聚义厅统一多媒体议事：长期融合详设与施工总入口

> **2026-10-03 用户纠偏（当前优先）**：[通用资料详设增量v3](unified-materials-correction-20261003.md)取代独立参考图入口及图片限定业务流程。唯一“添加资料（可选）”须支持图片/文档/音频等；Agent判断用途，通用会话、输出、保存与交付保持完整范围。不是文案改名；旧冻结绘图wire仅作执行适配与兼容，原34项需补UM01–UM10。当前尚未实现/验收本纠偏。

日期：2026-10-01。特性：`juyiting-multimedia-deliberation`；SDD/API/Web/Agent Client 共用分支 `codex/juyiting-multimedia-deliberation`。

本文收敛已有详设的阅读和实施顺序，**不是第二份 wire、DDL 或运行台账**；不改任何冻结合同/fixture。分支和文档已经交付，完整功能仍在实施，尚未按本特性发布或验收。

## 1. 长期决策：一个会话，按需启用能力

fast-deliberation 是轻量 CHAT 运行策略，不是另一套聊天产品；multimedia-deliberation 是同一悬赏会话的资料、创作、修改及交付能力。合入 fast 后复用其 request/turn/snapshot/outbox/event，不新建第二套聊天消息、队列或问题状态机。

| 用户当前意图 | 本轮所需上下文/能力 | 不能据此推导的权限 |
| --- | --- | --- |
| 普通讨论、查询进度 | 必要对话事实；进度可直接读服务端状态 | 不能调用生成工具 |
| 补充参考资料 | ACL 校验后的精确版本目录（AVAILABLE） | 可选择/可见不代表 Agent 已读内容 |
| 问图片或文件里是什么 | 显式受权查阅（INSPECT），本轮精确输入 | 不授予写文件、生成或付费权限 |
| 生成/修改 | 当前任务、目标能力、操作授权、精确来源、有效费用许可（如涉及） | 点将/模型提议不是无限授权 |

明确且已授权的“画一只鸟”可直接执行，不强制先跑 CHAT，也不强制每轮固定三次模型调用。需要必要信息才澄清。没有真实查阅能力时如实说明，不能用目录元数据编造“我看过图片”。

这是一套长期领域架构；旧端点/runtime 适配是阶段性兼容层。停止兼容须有客户端迁移、在途请求完成和回放恢复证据，不设任意日期/性能阈值。

## 2. 用户流程与状态事实

```text
提交需求“画一只鸟” + 可选工作空间精确参考版本
  → 显式目标点将，固定需求/assignment/目标和首轮办理意图
  → 自动建立或复用该任务唯一“悬赏议事”，可靠投递需求与资料目录
  → 同一输入框：直接生成 / 自然讨论 / 澄清回复 / 补充资料 / 修改上一稿
  → 同一会话展示文字、图片、音频、文件，新旧稿都可发现
  → 受权预览和下载；可选保存到工作空间
  → 选择精确最终成果 → 正式提交 → 用户验收 → 任务完成
```

- 重新点将更新 assignmentRevision，不能复制一套新议事；旧目标迟到结果不得污染新办理。
- Agent 收到需求、文字回复完成、执行完成、媒体就绪、保存、正式提交、验收、任务完成分别记录。
- 实时展示指文字增量、真实执行状态、完整媒体经验证后原位出现；不承诺逐像素生成或未提交音频自动播放。
- 用户不满意可继续输入、补充资料、引用旧稿。自然澄清不强制固定表单；有歧义才问清引用哪一稿。
- 保存是可选归档，不是继续修改、预览下载或验收的前置条件。最终成果集合由用户确认，旧稿不自动全部交付。

## 3. 分层职责与唯一协议入口

```text
Web：单输入框、会话内容块、精确引用、选择成果、恢复
  → Chat：身份/幂等受理、持久 request/turn、上下文、typed 结果和问题 CAS、事件
  → Agent/执行域：当前目标能力、操作授权、START、隔离 run、输出提交
  → 资产/空间/交付域：持久字节及来源、各用途 ACL、归档、正式提交与验收
```

### 3.1 自然讨论和澄清：typed v1

以[原子续办合同 v1](typed-deliberation-atomic-followup-contract-v1.md)为唯一具体 HTTP/事务合同：

- `POST /chat/conversations/{conversationId}/interactions/discussion`，schemaVersion=1；intent 为 DISCUSSION 或 CLARIFICATION_REPLY。
- 复用 CHAT request；可信原生 final 只有 ANSWER、CLARIFY、EXECUTION_PROPOSAL。正文、JSON 代码块、中文句子都不能重新解析成执行许可。
- 正文、typed outcome、pending/proposal、turn/request 更新及 event/outbox 在同一事务持久化；问题按精确 pending ID/版本 CAS，回复创建新的 CHAT request。
- `GET /chat/conversations/{conversationId}/requests/{requestId}/typed-outcome` 为只读恢复，不发起模型或执行。
- 按[回执补充 v1.1](typed-deliberation-receipt-adoption-contract-v1.1.md)区分固定 Admission `ADMITTED/0` 与实时 RequestView `RUNNING/COMPLETED` 等状态；重放回执不能拷贝或重置运行投影。

**早期详设中的“schema-3 讨论入口”只是被后续冻结合同替代的候选，不实施第二套讨论路由或问题状态机。**

### 3.2 生成和修改：独立 EXECUTE v3

按[owner HTTP 授权合同](controlled-image-followup-owner-contract-v1.md)、[当前上下文补充](controlled-image-followup-owner-context-v1.1.md)及[Client v3 来源合同](controlled-image-v3-source-wire-contract-v1.md)实现。

用户确认本轮执行意图后走权威 context/preview/明确确认/issue/admit；初始点将的自动首轮办理继续沿其已冻结合同。模型 proposal 只提供建议，不签发 grant、consent 或 START。旧 GENERATE-only 授权不能借来 EDIT；修改使用独立 per-intent 操作授权、精确会话来源及有效独立消费许可。

上述 v1/v3 属于不同协议域，不是要求全平台升到 schema3。旧 `/chat/stream` 禁止 execute hint 获取执行权限的边界继续保留。

### 3.3 真实资料查阅：INSPECT sibling v1

[受权查阅领域合同v1](typed-inspection-authority-contract-v1.md)固定独立inspection admission/原key只读恢复、purpose-scoped machine GET、manifest无自引用摘要、每次读取的当前授权重核，以及新的typed终态v2。复用已有snapshot/request/inbox/typed pending，不新增文件根或第二状态机；旧CHAT v1的NONE/AVAILABLE与route=CHAT不改。领域合同不等于引擎就绪：实际工具/文件系统隔离profile、四种carrier、授权实现和真实双接应仍待完成。设计fixture的12项运行用例均NOT_RUN。

## 4. 一份内容、三种用途；Agent 工作目录不统一挂载

```text
受信不可变内容（存储引用、精确版本、SHA-256、MIME、长度）
 ├─ 会话 asset / message part：历史、预览、继续引用
 ├─ WorkspaceFileVersion：用户主动保存、个人目录组织
 └─ 正式 artifact / delivery manifest：所选成果快照、验收证据
```

三种用途各有 ACL 和保留关系，不能相互授予权限；不要求三套文件系统，也不承诺所有用途永远零字节复制。按[媒体/存储详设](design.md)复用配置化的现有私有根：会话/个人内容使用 workspace-private，正式交付使用 task-artifacts-private；设计参考路径为 `/opt/cyf/service/workspace-private` 和 `/opt/cyf/service/task-artifacts-private`，**不是本轮对线上配置的实测声明**。不新增第三根，不硬编码上述路径，不按裸 hash 认领他人内容。

山寨安顿和自家接应各自保留工作目录；它们是缓存/执行沙箱，不是平台用户空间的事实源：

1. 服务端固定本轮受权 input manifest：精确来源、版本、摘要及运行归属，不传任意平台绝对路径。
2. Client 从受权接口领取字节，物化到自己的隔离 run 中；职责为 inputs（只读）、scratch（临时）、outputs/staging（声明成果），实际位置由执行 command/manifest 决定。
3. 提示词告诉 Agent 本轮可读文件、输出位置及声明格式；授权、路径约束、符号链接检查和上传归属由 Client/服务端落实，不能只靠提示词。
4. 输出沿既有受权内容上传与 manifest commit 协议提交。校验 run/producer/assignment、摘要、长度、类型和来源后，才能登记持久 asset/part 并发布 ready 事件。
5. Agent 离线、临时目录清理或会话切换不能让已保存/正式交付内容丢失。正式存储必要复制时核对摘要；不做跨 owner 物理去重。

### 4.1 双接应的引擎合同与本地版本选择

平台统一的是领域协议和受权内容，不要求所有Agent同一工作目录或同一全局CLI。Client按本地operator profile显式选择已登记的exact引擎合同，测量真实binary/version/schema bundle、私有资源快照和启动identity；版本未登记或与选择不符时如实不可用，不自动更换模型、Provider或全局CLI。

能力声明、typed readiness、实际CHAT调用必须使用同一所选合同；不能在adapter支持新版本后仍硬匹配旧合同，也不能只看measured=true。默认旧合同及现有wire保持兼容。资源文件数量/字节记录为观测，不沿用无依据的大小门槛；路径、归属、符号链接、摘要和资源漂移的真实安全检查仍保留。原生协议兼容不等于INSPECT或严格无工具能力证明，[当前源码依据与验证边界](integration-catalog-and-native-runtime-progress-20261001.md)另行记录。

## 5. 实时媒体、断线及业务恢复

- 复用单会话持久事件日志和请求目录；不能把 activeRequest 当全会话唯一成果。同身份刷新可恢复多请求、新旧稿及 pending question。
- part.ready 必须指向已有受信字节；Agent 本机路径、模型自造 URL、假图片占位都不是交付件。
- 图片放大/下载，音频播放器及受权 Range，文本和文件按真实支持能力预览；不支持的格式明确可下载但暂不支持预览。
- 原幂等键固定完整输入/来源/父链/授权语义，同键异正文冲突；未知结果先原键只读对账，404 不证明在途 POST 未受理。不能因刷新、SSE 重连或 ACK 丢失新开收费执行。
- 保存、正式提交、验收分别幂等恢复。验收成功但可选归档失败只重试归档；正式提交成功不在 Web 本地伪造 task completed。
- owner/client/tenant、conversation generation、task、目标、assignment、run fence 全链路保留。性能慢只记录，不据 SLO 取消下一步；真实网络错误、配置传输超时、用户取消及锁归属仍保留。

## 6. 影响范围、实施依赖和 Agent 指导

影响 Web 聚义厅输入/资料选择/媒体展示/恢复/验收，API chat/agent/workspace/正式交付关联及其新增 schema，Agent Client 能力/受权输入输出/执行适配，以及 SDD。采用加法集成和受限 Owner 写集，不全盘重写、不新拆微服务、不迁移全部历史文件。身份/ACL、事务及迁移需真实专项回归和原授权边界。

| 顺序 | 工作包 | 交付判定 |
| --- | --- | --- |
| 1 | API 当前组合收口 | 真实 CHECK catalog/事务与 typed 闭包通过，不能放宽弱 CHECK 或把静态检查当数据库通过 |
| 2 | 真实 Client CHAT/INSPECT/EXECUTE | 精确引擎合同、当前 profile 能力、实际读取与权限隔离；不能用 read-only/空 dynamicTools 冒充严格无工具证明 |
| 3 | 跨仓多轮/来源/媒体闭环 | 可选参考、澄清、生成、上一稿修改、图音文文件展示下载、归档和正式交付恢复 |
| 4 | 双接应和真实浏览器 | 分别实测山寨安顿/自家接应及完整用户流程，不用 mock 标签或浏览器启动检查代替验收 |
| 5 | 按版本发布 | 重新核对版本与 exact SHA；相关测试/构建、制品摘要、实际部署健康及业务验收分别记录 |

详细工作包/路径分工以[实施计划](fusion-implementation-plan-v2.md)为准；验收覆盖[AC01–AC22](acceptance.md)及[FD01–FD12](fusion-detailed-design-v2.md#11-融合验收补充fd01fd12全部not_run)，不得缩减成只验一个 mock 画鸟结果。

给开发 Agent 的指令模板：

> 在 codex/juyiting-multimedia-deliberation 的独立 worktree 承接一个明确工作包，先读本文、对应冻结合同和当前精确组件 pin。复用已有会话/request/event，讨论实现 typed v1、执行实现独立 v3；只写分配路径，不改黄金 fixture 或其他 Owner 代码。提交 exact commit/tree、变更清单、真实测试及原始证据、未完事项；Owner 自检，不建独立 Reviewer。所有 Gradle 经 orchestrator。不得未经授权调用付费 Provider、迁移生产数据或操作其他任务进程。

运行责任及状态只在 `/home/isp/wsps/cyf/docs/implementation/TASKS.yaml#runtime_ledger_json` 管理；本文不记录第二份运行队列。云效不可用期间的已授权本地发布记录 local_user_authorized，不伪造 Flow Run；发布前不盲用已占用的历史示例版本号。

## 7. 本次分支与详设交付证据

[直接远端读回及精确 ancestry](integration-evidence-20260928/fusion-final-design-branch-readback-20261001.json)确认四仓 feature 已推送，当前 fast HEAD 均为其祖先；因此复用现有分支和合入记录，不重复创建或制造无意义 merge。

研发 pin：API `87c0acc`、Web `ebb664f`、Client `2f69072`；完整 SHA/tree 以 `integration.yaml` 为准，未通过的 API 组合候选不替换 pin。[最近实际验证记录](integration-typed-receipt-source-adoption-20261001.md)保存 Web 196 通过及基线 lint 问题、API 候选 34 通过/3 真实 MySQL 失败及其余未运行，不冒称完整通过。

本次详设交付不修改运行源码、不合 develop、不发布或触发付费生成。真实 INSPECT、双接应、完整多媒体和浏览器验收仍需闭合，**不能通知“可以验收”**。长期方案见[融合方案](long-term-fusion-plan-20260928.md)，领域详设见[整体 v2](fusion-detailed-design-v2.md)；本文仅收敛导航及后续冻结合同的优先顺序。


## 7.1 本次交付复核（2026-10-01 22:35，Asia/Shanghai）

上述第7节保留首次交付时点。本次以[直接远端读回](integration-evidence-20260928/fusion-design-delivery-current-readback-20261001.json)再次核对：SDD、API、Web、Agent Client 四仓均已建立并推送 `codex/juyiting-multimedia-deliberation`，各仓当前 `codex/juyiting-codex-fast-deliberation-context` HEAD 都是该 feature 的祖先，不重复创建分支或制造空 merge。

| 仓库 | 本次核验的远端 feature SHA | fast 合入结果 |
| --- | --- | --- |
| SDD（本文补充之前） | `68729a74819ca425e81ebd938e538d11a60dff02` | 已包含 |
| API | `87c0acc16bef37c35f96f0edbbc078b5ff860a46` | 已包含 |
| Web | `ebb664fc8a443845577f356d0823bd6368634dfa` | 已包含 |
| Agent Client | `607d25145efe3d13f996e5fbb5e33a01d7bf2195` | 已包含 |

本次仅补文档和分支核验；组件研发 pin 不变，以 `integration.yaml` 为准。阅读顺序：本文 → 长期融合方案 → 整体详设 v2 / 媒体与存储详设 → 对应后续冻结合同 → 实施计划与验收。整体详设中的候选 HTTP/状态模型若被后续版本化冻结合同替代，按本文第3节选择唯一实施合同，不另建并行协议或状态机。

**本次交付范围完成的是分支、fast 代码融合和长期详设，不是产品开发完成。** 真实 INSPECT、双接应、多媒体全流程和浏览器验收仍未关闭；未执行应用构建、develop 合入、发布、生产迁移或付费生成。下一步按第6节工作包落实，并保留真实测试/发布/用户验收三个独立判定。
