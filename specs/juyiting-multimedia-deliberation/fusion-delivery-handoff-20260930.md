# 多媒体议事长期融合详设：交接与实施入口

日期：2026-09-30。特性名称：**聚义厅统一多媒体议事与受控交付**；feature ID：`juyiting-multimedia-deliberation`。

本文件是本次分支/文档交付的只读状态补充，不改变冻结的 API、wire 或验收合同，不是运行台账。完整详设以[融合详设 v2](fusion-detailed-design-v2.md)为主，[UI/媒体/存储详设](design.md)补充，冲突时 v2 优先。**分支建立与 fast 代码融合已完成；完整产品尚未验收。**

## 2026-10-01 18:56 增量交接

最新状态及具体领域施工优先级见[回执领域修复与实施优先级](integration-typed-receipt-source-adoption-20261001.md)：Web ebb 已晋升源码并推送；API642e V3实测34通过/3真实MySQL失败，Chat/V2/typed未运行，不改API pin；以下前轮193项/合法状态2失败/API8fc记录保留为历史。最新远端证明及便携原始证据同页可达，不把浏览器启动或源码接受当业务验收。

## 本次请求的最终交付（2026-10-01）

本节更新交付入口和当前源码快照；下文各历史核验点原样保留，不是最新状态。**本次交付是分支、fast 合入与长期详设；没有把整个多媒体功能宣称为开发完成、发布或可验收。**

### 当前远端分支核验

直接 `git ls-remote --heads origin` 读取四仓 feature/fast HEAD，再以 `git merge-base --is-ancestor <remote-fast> <remote-feature>` 核对。四仓返回均为 0，且本地 feature 与远端一致；没有重复 merge、重建分支、改写 fast 或操作脏主 checkout。

| 仓库 | 本次文档提交前 feature HEAD | 当前远端 fast HEAD | 包含 fast / 已推送 |
| --- | --- | --- | --- |
| SDD | `0334c58a04adf5583d021527b0b430a653c9db2c` | `9f47e63e456a7965d954e6d1e645a083920d784e` | 是 / 是 |
| API | `87c0acc16bef37c35f96f0edbbc078b5ff860a46` | `caee54fc27a08146f9cc57219cf86c763e41c531` | 是 / 是 |
| Web | `1993b888391c2c7ce707dc60da743810f25f17df` | `96838f17fc24fbf21781be39476aa9723dee3a2c` | 是 / 是 |
| Agent Client | `2f6907274ea5395980df0643c6b3898fa522a54f` | `68dbe8992a56c8e1041056a9123b1156d1d2b35e` | 是 / 是 |

完整时间/tree/命令语义见[本次远端回执](integration-evidence-20260928/typed-receipt-adoption-20261001/branch-readback.json)。SDD 此后只追加本文档提交，组件 pin 不变。本次18:19北京时间远端快照中，四仓各自develop HEAD也都是feature祖先；此事实只绑定该快照，不推导之后新增提交已包含。本轮不另行合develop或发布。

### 长期设计与详设优先级

1. [长期方案](long-term-fusion-plan-20260928.md)：一个业务会话；fast 为轻量 CHAT 策略，多媒体为同入口的受权能力。CHAT/INSPECT/EXECUTE 是权限和上下文边界，不是三套系统或固定三次模型调用。
2. [整体详设 v2](fusion-detailed-design-v2.md)：受理、任务授权、路由、快照、状态机、幂等、协议兼容和故障恢复。
3. [多轮与每意图授权补充](long-term-followup-authority-design-20261001.md)：细化 v2 的当前实施决策。旧 GENERATE-only grant **不能借权 EDIT**；本轮明确操作/来源授权与费用同意分别核验，不改写原 grant。讨论、精确澄清回复、执行三类意图均留在同会话。
4. [媒体/存储/归档/验收详设](design.md)：text/image/audio/file 内容块、受权真实字节、预览/下载、可选保存、选定最终成果及正式验收/完成。UI 展示不等于 Agent 已理解附件；未保存成果仍须持久可读。
5. 具体实现按已冻结的领域 wire/HTTP/fixture 合同施工（包括[原子typed合同v1](typed-deliberation-atomic-followup-contract-v1.md)与[回执领域补充v1.1](typed-deliberation-receipt-adoption-contract-v1.1.md)）；**新架构决策不静默改变旧协议或已绑定 hash**。确需改变合同时另冻结版本。候选设计、源码接受、产品验收、实际发布四种状态分开。

“一份内容，三种用途”保留平台已有私有存储根，使用会话 asset、个人文件版本、正式交付 manifest 的精确引用和各自 ACL；不是让所有 Agent 共用一个物理目录。山寨安顿/自家接应均从受 fence 的 manifest 物化本轮 inputs，在各自 run 的 outputs 提交，由平台验证后发布媒体。提示词说明路径，但授权/上传/提交由协议执行。

### 当前具体合同与状态收口

| 领域 | 当前实施合同 | 与fast关系 |
| --- | --- | --- |
| 自然讨论/精确澄清回复 | typed schemaVersion=1；`POST /chat/conversations/{conversationId}/interactions/discussion`；原子typed合同v1 | 仍是原durable CHAT request/turn，正文与可信结果同事务；不新建聊天引擎 |
| 新生成/编辑 | 每意图授权、执行schema-3及Client来源合同 | 独立受控EXECUTE；不能从讨论结果、旧GEN grant或已预览推导EDIT/付费授权 |
| 资料查阅 | NONE/AVAILABLE/INSPECT分层，INSPECT实际实现尚未完成 | AVAILABLE只给目录，不假报已经读图；能力未证明不得广告READY |
| 状态与回放 | 不变Admission `ADMITTED/0`；原GET返回当前RequestView | 请求可已RUNNING或COMPLETED；immutable IDs/scope/revision严格匹配，状态/版本不跨领域相等比较 |

详设v2及早期schema-3讨论入口是架构候选；具体自然讨论以原子typed合同v1为准，**不再另建schema-3讨论、第二套会话或问题状态机**。独立执行v3继续有效。旧冻结文件/fixture hash不变，新语义通过回执补充v1.1显式细化。

本轮真实只读核验：Web891精确树13文件**193通过/0失败**，旧语音harness问题未复现；固定合法状态probe仍**1通过/2失败**。API8fc精确组合无冲突，但typed receipt仍从RUNNING聚合状态复制；API测试NOT_RUN。两候选均未晋升，见[证据](integration-evidence-20260928/typed-receipt-adoption-20261001/manifest.json)。这项真实协议问题是下一修复对象，不以套件通过、分支包含fast或文档交付掩盖。

### 接下来如何指导开发 Agent

以[融合开发计划](fusion-implementation-plan-v2.md)拆独立路径任务，每包固定合同版本、base commit、允许写集、验收 selector 和未完成项；不要求 Agent 重新设计第二套会话或全盘重写聚义厅。

当前顺序：API/Web先修回执与实时状态领域分离，保持原负向与版本防回退 → 验证V3 CHECK-catalog最小child、完整62V3后82V2及typed原子闭包/真实数据库 → 同一composer的自然多轮与既有执行链联调 → 真实受控查阅和全部媒体闭环 → 双接应/浏览器/正式交付验收 → 达到对应里程碑条件后分版本发布。Owner 自检，不创建独立 Reviewer；所有 Gradle 经 orchestrator。

本次执行文档/远端核验与上述轻量定向源码测试，不跑应用构建、Provider 或浏览器；定向测试不计作 34 项产品用例。发布前重新核对线上版本与 release refs，旧计划示例号不得覆盖已有版本；有/无参考图画鸟、继续修改、预览下载、保存及真实需求完成均须对应目标版本实测，才能通知“可以验收”。执行 Owner/gate 仍只在主工作区 runtime ledger，本节不是第二台账。

## 1. 分支交付及远端核验

四仓均使用 `codex/juyiting-multimedia-deliberation`。本次重新 fetch 远端精确分支，以 `merge-base --is-ancestor` 核验当前 fast HEAD；四仓均已包含，无需重复 merge、重置或改写原 fast 分支。

| 仓库 | 本次核验 feature HEAD | 当前远端 fast HEAD | fast 已合入 | 当前 develop 独有提交数 |
| --- | --- | --- | --- | --- |
| SDD | `c880d56c0d4e6e0ba0b1d79030ac8550c7af1f7f` | `9f47e63e456a7965d954e6d1e645a083920d784e` | 是 | 1 |
| API | `b1e7b06817f041804f1e1d613ff4aa280641e904` | `caee54fc27a08146f9cc57219cf86c763e41c531` | 是 | 3 |
| Web | `7ac3bbc3fd21bfb1b053a8fbe249cc2b17d42a1d` | `96838f17fc24fbf21781be39476aa9723dee3a2c` | 是 | 4 |
| Agent Client | `0d4224e2dbbe52788a69be0cb0844f0ad743c6b2` | `68dbe8992a56c8e1041056a9123b1156d1d2b35e` | 是 | 0 |

完整 tree、远端 develop SHA、核验时间见[可复核快照](fusion-branch-handoff-verification-20260930.json)。SDD SHA 是本次文档提交前的核验点，包含本文的提交另由 Git 历史确定。

**已合入 fast 不表示已包含最新 develop。** develop 独有提交须在后续集成前按实际差异补齐及定向回归；本次不顺带合 develop、不改组件研发 pin、不发布。历史融合冲突处理与测试范围保留在[初始整合回执](integration-baseline-20260928.md)，不把旧结果改写成新测试通过。

## 2. 长期架构：一个产品、多个受控运行策略

```text
需求原文 + 可选精确资料版本
       ↓ 显式目标 Agent / 点将并办理
assignment + grant + 唯一 bootstrap/outbox
       ↓ 同一悬赏议事 / 同一 durable request、turn、事件体系
权威上下文 + 按需路由
       ├─ 进度查询：读事实，不生成
       ├─ CHAT：讨论/澄清，轻量上下文，不挂载执行目录
       ├─ INSPECT：本轮指定资料，受权只读
       └─ EXECUTE：本次授权操作、输入、run/lease、输出提交
                     ↓
            持久 conversation asset + message parts
                     ↓
          实时展示 / 预览下载 / 继续讨论和修改
                     ├─ 用户选择 → 保存个人空间
                     └─ 精确成果集合 → 正式交付 → 验收 → 任务完成
```

- `fast-deliberation` 长期保留为 CHAT 运行策略，不作为独立聊天产品；`multimedia-deliberation` 是同一会话的媒体/办理能力。
- 每轮不默认加载全部资料、全部工具；附件目录元数据不等于已读图片。分别记录 availableRefs 和 materializedRefs。
- 已明确且已授权的“画一只鸟”可直接执行；必要时才澄清，不强制先问 fast 模型，再问执行模型。
- 旧 `/chat/stream`、fast-v1 EXECUTE=false 保持边界。新的 native 执行声明与服务端准入另行证明，不借聊天提示词或 execute hint 提权。
- 同一会话不等于同一模型线程：线程按身份/目标/profile隔离，平台持久快照为事实源。严格 no-tools 必须有实际引擎证据，不能仅由 sandbox/approval 配置推断。

这是长期领域设计；只有 legacy 协议适配是过渡措施。退出适配须证明支持客户端迁移、旧在途请求处理及回放恢复，不按任意日期删除。

## 3. 用户流程与实现职责

| 用户动作 | 权威实现 | 不可混淆的事实 |
| --- | --- | --- |
| 提“画一只鸟”，可选参考图 | 固定需求 revision、空间文件版本/摘要和任务资料关联 | 选择资料不是全空间读取授权 |
| 点将并办理 | 目标能力协商 + task/grant/assignment + outbox | grant 不是 TaskDTO；允许操作集合不是首轮动作 |
| 自动新增/进入悬赏议事 | 采用服务端确切 conversation/initial request，加载历史与事件 | 不由浏览器再发一遍首轮需求 |
| 生成或澄清 | 服务端授权/费用/资料检查；执行或保存澄清关联 | 能力 READY 不等于已获费用许可 |
| 实时看图片/音频/文件 | 文本增量、执行状态；完整媒体提交验证后 part.ready | 不承诺逐像素生图；本机路径不是交付件 |
| 不满意继续补充/修改 | 同会话新明确意图，绑定上一稿 asset/revision | 重试/刷新不创建第二次收费执行 |
| 保存到工作空间 | 源读取权 + 个人空间写权限，精确快照幂等归档 | 未保存成果仍持久可读；归档不自动验收 |
| 确定完成并验收 | 固定最终集合；正式提交/验收/完成分阶段恢复 | OUTPUT_COMMITTED 不等于 task.completed |

完整用户验收保持图片、音频、文本、文件范围，不因当前图片纵切而缩窄。照片式鸟图须按需求实际生成/提交，可预览且下载真实字节；不能以 mock 图、Markdown 外链、生成成功自述代替。

## 4. 一份内容，三种用途与双接应目录

**共享的是不可变内容身份与来源，不是三种用途的权限，也不是要求共享一个物理挂载。**

```text
不可变内容引用（摘要/MIME/长度/实际私有字节）
  ├─ 会话 asset/message part：会话 ACL
  ├─ 个人 WorkspaceFileVersion：用户主动保存，个人 ACL
  └─ 正式 ArtifactVersion：用户选定，任务/验收 ACL
```

复用现有 `workspace-private` 与 `task-artifacts-private` 两个私有存储根；必要的正式交付复制校验同一摘要，不新增第三套文件系统、不做跨 owner 物理去重。示例部署路径和配置原则见原详设第3节；实际位置以运行配置为准，不由文档硬编码。

山寨安顿/自家接应每个 Agent 都保留自己的配置根；每次执行另建 run 隔离的 `inputs/outputs/scratch`。平台下发精确受权 manifest，客户端领取、验摘要并物化 inputs；提示词说明本次可读路径及输出约定，客户端/服务端负责权限、START fence、上传及 commit，**提示词不是授权和成果提交机制**。不向 Agent 暴露平台绝对私有目录，不扫描客户端全部工作目录认领产物。

双接应使用同协议，各自声明真实能力；一个客户端就绪不能推断另一个也就绪。执行目录只是临时加工区，平台资产才是可跨客户端预览、下载与归档的持久事实。

## 5. 详设施工入口及影响范围

| 内容 | 权威文档/合同 |
| --- | --- |
| 整体长期决策及适配退出 | [长期融合方案](long-term-fusion-plan-20260928.md) |
| admission、grant、路由、上下文、状态/恢复 | [融合详设 v2](fusion-detailed-design-v2.md) |
| UI、多媒体 parts、资产、存储、归档、验收 | [媒体详设](design.md) |
| 现有码/表/端点映射 | [M0 源码映射](m0-source-mapping-and-contract.md) |
| 页面点将与首轮采用 | [入口详设](point-and-start-entry-design-v1.md)、[原操作只读恢复](assignment-operation-read-contract-v1.md) |
| 首轮动作与多操作 grant | [初始动作合同](initial-operation-contract-v1.md) |
| 原生声明、当前session与只读协商 | [原生能力合同](native-bounty-capability-contract-v1.md) |
| 精确成果与验收恢复 | [finalization 合同](finalization-contract-v1.md) |
| Owner工作包、依赖、验证 | [融合开发计划](fusion-implementation-plan-v2.md) |
| 34项产品验收 | [验收 AC01–AC22](acceptance.md) + [详设 FD01–FD12](fusion-detailed-design-v2.md) |

影响四仓：SDD 定义合同/基线；API 的 task、chat、agent、workspace、delivery 负责领域协同；Web 的需求/点将/会话/媒体/归档/验收组件负责体验；Client 负责能力、精确输入、执行和上传。属于跨仓功能增量，不是整个聚义厅重写。不更改 map/roster 分流、显式 Agent 点将不变量，不顺带重构资金榜、多Agent流程、钱包或另建存储服务。

## 6. 开发顺序与给 Agent 的指令

1. 在冻结 native 合同下完成 API/Web/Client 能力协商及实际点将页面接线；原键恢复永不 legacy 降级。
2. 补真实参考图选择/任务关联/精确版本回读，以及合法费用授权桥；无授权不调用付费 Provider，不挪用悬赏 escrow/hosting/skill 等用途凭据。
3. 补同会话澄清续办、上一稿引用/EDIT/派生资产；仅广告实际支持的操作。
4. 完成保存、正式提交/验收/领域完成真实联调，以及文本、音频、文件和混排。
5. 补齐当前 develop 独有改动，按 exact SHA/tree/selector/fixture 验证双接应、恢复、迁移及全部产品范围；达到条件后再按发布政策推进。

可直接交给实施 Agent：

> 在本仓 `codex/juyiting-multimedia-deliberation` 的独立 worktree 上，先阅读本 feature README、融合详设v2及对应冻结合同。只领取一个有明确路径边界和依赖的工作包，保留 fast 轻量权限边界及既有 PRIVATE/TASK。实现时复用持久请求/事件和平台资产，固定身份、资料版本、原幂等键、grant/assignment/lease；不得重发首轮或以提示词授予权限。Owner自检并交付 exact commit/tree、实际定向测试、DB fixture digest（适用时）与剩余缺口。Gradle 经 orchestrator；不创建 Reviewer，不改他人脏文件，不部署、不迁移真实库、不调用未获授权的付费 Provider。

性能目标只作观测及优化排序，不依据时延SLO拒绝/取消下一步。真实鉴权、事务、幂等、锁归属、明确传输超时和用户取消仍保留。

## 7. 本次交付结论与未完成事项

- **已完成**：四仓同名 feature 分支、fast ancestry 与远端 HEAD 重新核验、长期方案/详设/实施计划及本交接入口。复用此前精确源码的定向证据，本次不重复跑未变源码测试。
- **尚未完成产品验收**：native能力/真实页面组合、完整参考图、合法费用授权、澄清/EDIT/派生输入、双接应/真实 Provider、完整浏览器流程与发布。能力声明或局部schema/单测通过不能关闭这些项。
- **本次未执行**：develop合入、生产构建、部署、生产数据库迁移、付费调用或画鸟浏览器验收。34项产品状态不改 PASS。

状态详见[集成清单](integration.yaml)。运行推进仍只使用 `docs/implementation/TASKS.yaml#runtime_ledger_json`；本文不新增 Owner/运行门禁台账。


## 8. 需求参考图施工期间的远端复核（2026-09-30）

[本次精确远端快照](integration-evidence-20260928/branch-reference-intake-verification-20260930.json)重新 fetch 四仓 feature / fast / develop 并核验 ancestry：SDD `97c06613`、API `5668c747`、Web `ab317fa`、Client `1812e5b` 均包含当前远端 fast HEAD。develop 独有提交仍分别为1/3/4/0，不能将 fast 合入等同 develop 收敛。此处是本次文档提交前的观测点，不是将原交接表的历史SHA改写。

需求前可选图片按[原子受理合同 v1](requirement-reference-intake-contract-v1.md)继续实施；API事务与Web选择器/创建入口各自在隔离worktree。Main真实父表单、真实图片选择器及真实创建composable的两项组合测试已经通过，HTTP仍为隔离夹具，并非已部署API/浏览器/Provider证据。选择器异步替换的具体竞态由原Owner修复，修复后须精确组合树验证，当前远端Web pin未提前提升。

完整34项产品用例仍NOT_RUN。原操作长期保留是安全恢复措施，不是完整错误退出体验；产品发布前还须为确定拒绝、失效参考图等原意图提供有服务端无副作用证明的明确处置，不得以清localStorage、换键或GET404冒充可以新建的证明。本补充不扩展冻结receipt接口，也不授权生产迁移或付费调用。


## 9. 原子创建源码晋升与费用门禁详设补充

[四仓远端readback](integration-evidence-20260928/four-repo-remote-readback-after-intake.json)再次确认当前fast HEAD均已包含。该快照SDD `09536f3c`是本补充提交前的精确核验点；宿主时间戳按原值保存，不作为当前日期或发布日期。

最新研发pins：API `083f9846` / tree `fbc21df0`，Web `7821209c` / tree `d829db4c`，Client `1812e5b5` / tree `43029628`。API原子参考图创建20项通过，含实际MySQL2和Spring事务2，零跳过；[证据及历史失败](integration-u1-atomic-reference-intake-source-20261001.md)已便携提交，不重复未变源码验证。当前develop独有仍SDD1/API4/Web4/Client0；voice/Redis4真实修复要在发布前收敛，未执行develop融合或发布。

[Provider权限与pre-call长期详设补充](provider-authority-and-precall-enforcement-design-v1.md)依据实码纠正“一次START等于一次扣费”的误读：现有通用executor内部没有工具调用前计数门禁。平台账户operator delegation和任务owner同意是两个权限事实。拟采用受控图像adapter或可信pre-call gateway的条件路线，尚未选择/切换账户、冻结费用wire或实现门禁；费用仍UNAVAILABLE，不写假costRef或以提示词替代。

后续先冻结合法账户/调用前合同，并补同会话澄清、上一稿/EDIT及恢复；完整34产品用例仍NOT_RUN。完成版本同源制品、双接应及浏览器交付/验收后才能通知用户可验收。


## 本次分支与详设交付复核
本次以 fetch + 独立远端 readback + `merge-base --is-ancestor` 重新确认：用户要求的新特性分支已存在于四仓并已合入当前 fast 代码。保持现有分支和开发成果，不重复建分支、伪造新 merge 或重置已提交代码。
| 仓库 | 本次文档提交前远端 feature HEAD | fast 已包含 | develop 尚独有提交 |
| --- | --- | --- | --- |
| sdd | `0032e526fb4561b4267b2531801826786705d929` | 是 | 1 |
| api | `083f9846ee26835e6db79892e4f7186accff467a` | 是 | 4 |
| web | `7821209c874995621d139da9047983f3b586d0b0` | 是 | 4 |
| client | `1812e5b5d090013338265d16ca34b0b9c257da49` | 是 | 0 |

完整 fast/develop/tree 和核验原始时间见[只读证据](integration-evidence-20260928/branch-design-reverification.json)。其中时间为采集主机时钟，不作为发布日期。SDD 行为本次文档提交前观测点；API/Web gitlink 与上述源码 HEAD 一致。本次只做文档静态校验，不把历史测试重写成刚执行，不改34项产品验收状态。

长期详设交付包括：
- [长期融合方案](long-term-fusion-plan-20260928.md)：一个会话产品，fast 为轻量策略，读取/执行按需授权；只有 legacy 适配是过渡措施。
- [融合详设 v2](fusion-detailed-design-v2.md)：admission、分层上下文、授权、路由、状态/事件、执行关联、兼容和迁移；[媒体详设](design.md)补充预览/下载、现有存储根、三种内容用途、双接应输入输出目录。
- [开发计划](fusion-implementation-plan-v2.md)及[验收矩阵](acceptance.md)：跨仓工作包与依赖，AC22 + FD12 共34项产品用例，Owner 自检，不新增 Reviewer。
- [Provider 调用前控制](provider-authority-and-precall-enforcement-design-v1.md)与[多轮续办设计准备](multiround-followup-design-notes-v1.md)：明确真实费用授权和澄清/EDIT缺口；core合同已冻结不等于真实费用链已实施。

下一可执行步骤：按融合计划领取尚未完成的授权/续办工作包，在独立 worktree 实现并做最小相关自检。后续集成必须收敛上表 develop 独有改动，不能将 fast ancestry 当作最新 develop 完整包含证明。本次不修改任何在途 Owner 源码、运行台账或测试夹具。


## 最新分支与详设交付核验（2026-10-01）

本次重新查询四仓远端 feature/fast，并核验当前 fast HEAD 是 feature HEAD 的祖先。新分支和既有合入成果均保留，不制造重复 merge。[精确远端回执及文档静态验证](integration-evidence-20260928/fusion-current-branch-design-readback.json)记录如下提交；SDD 为本回执提交前的观测点。

| 仓库 | 已推送 feature commit | 当前 fast 全部包含 |
| --- | --- | --- |
| SDD | `b3287b11d13034174cbefe9897282ad8876c742b` | 是 |
| API | `99ff1a43a9a02d2c83ad6c6ebf9a131212ce3130` | 是 |
| Web | `8244f5aca0f4060540cc3e2983bd20382fd14edf` | 是 |
| Agent Client | `554805226ddfcbe7ab15f499f9d0fa31d035b2f6` | 是 |

**本次请求已交付**：同名 feature 分支、fast 代码合入、长期融合方案、详细设计与开发计划。权威入口仍是本文件第5节及 README 阅读顺序，不另建第二份长期合同。详设覆盖统一 admission、按需上下文/能力、服务端授权、双接应精确输入输出、媒体持久展示/下载、主动归档、正式交付与验收恢复。

本次静态核验9份入口文档的124条相对文件链接、integration.yaml 解析/源码 commit+tree、API/Web gitlinks，均一致；105份便携证据的文件与原始字节摘要一致。重新解析既有 v16 的11份 XML 得到56项、零失败/错误/跳过；这是已执行测试的证据复核，不是本次重新运行测试。原始 Web stdout 的末尾空行保持不动；此前提交的 diff-check 对这些原始证据有3处警告，不冒称全提交 whitespace 检查无警告。本次新增文档 diff 另行静态检查。

**长期决策不变**：同一会话，fast 是轻量 CHAT 策略；资料和工具按当前意图、精确引用及权限加载；明确且已授权的需求可直接执行，只有信息不足才澄清。模型提示词不能授予工具/费用/文件访问权；同一会话不共用带执行权限的模型线程。

**不等于产品完成**：Bridge-A 的 grant/execution/START 完整桥、多轮澄清/续办/上一稿 EDIT、双接应与完整浏览器验收仍须完成；34产品用例及29共同桥 fixture 仍 NOT_RUN。当前没有 develop 合入、版本发布、真实账户选择或付费调用。本次不重复验证未变源码、不改在途 Owner 的代码与运行台账。

下一可执行步骤：实施 Agent 从[融合开发计划](fusion-implementation-plan-v2.md)及[受控费用桥详设](controlled-image-grant-start-bridge-design-v1.md)领取尚未完成的跨仓闭环工作包，按已有共同 fixture 实现、Owner 自检，并提交 exact commit/tree 与实际测试证据。


## 本轮独立远端读回与长期详设状态（2026-10-01）

已通过独立`ls-remote`读回并以精确SHA核验fast ancestry；不因现有分支已经建立而重复merge或改写fast。四仓分支均为`codex/juyiting-multimedia-deliberation`。

| 仓库 | 本轮远端feature观测点 | 当前fast为祖先 | 当前develop独有提交 |
| --- | --- | --- | --- |
| SDD | `1eab54cb` | 是 | 0 |
| API | `99ff1a43` | 是 | 10 |
| Web | `8b8c951d` | 是 | 0 |
| Agent Client | `55480522` | 是 | 0 |

SDD为本文提交前观测点。完整commit/tree/远端develop/采集时间见[只读回执](integration-evidence-20260928/fusion-current-remote-heads-20261001.json)。**分支、fast合入及长期详设已完成；API新桥仍独立验证，未提前替换研发pin；完整产品未验收或发布。**[最新实际进展](integration-controlled-bridge-verification-progress.md#agent桥实际通过chat诊断逐步推进2026-10-01)明确Agent实际57项/真实MySQL3通过和Chat新增诊断，不冒称整桥通过。

长期设计继续使用本文件第5节的权威文档：同一会话产品、fast轻量CHAT策略、按需受权INSPECT/EXECUTE；明确且已授权的需求可直接执行，只有信息不足才澄清。资料和成果复用不可变内容身份，按会话/个人空间/正式交付分别授权；双接应各自run隔离，以受权manifest/API领取与提交，不共享任意工作目录。[新增runtime v3精确来源/EDIT合同](controlled-image-v3-source-wire-contract-v1.md)补齐上一稿来源及每次调用的wire；仅是runtime增量，不把尚未冻结/实现的owner澄清与费用HTTP接口视为完成。后续按冻结包继续实现，不另造两套议事/三套文件系统。


本轮API bridge后续已推进到精确feature`f89d4de3`/tree`b54dee07`，详见[源码推送readback](integration-evidence-20260928/controlled-bridge-v7-source-accepted/source-push-readback.json)和[最新实际状态](integration-controlled-bridge-verification-progress.md#api桥源码已验证并推送2026-10-01)。上表`99ff1a43`是此前独立远端采集点，保留历史；本次SDD pin/gitlink采用已推送新API源。长期详设本身不因测试诊断改写；没有完整产品验收或版本发布。
