> **现行适用范围（2026-11-07）：** 本文是[所属专题](spec.md)的细则，不独立定义发布/角色/DFX规则；共用[统一开发约束](../architecture-convergence/development-principles.md)。旧日期候选/测试/安装仅代表当时范围，未核实部分不改成今日完成。业务协议/冻结输入不因文档整理改写。

# Codex 原生执行技术详设 v3.1：按职责交付与删除越界实现

> **2026-10-28后续用户决定：**以[RB-1“技能原生调用与用户自配凭据”](responsibility-boundaries.md#2026-10-28-用户更新技能原生调用与用户自配凭据)为准。生图/改图改由app-server原生运行技能脚本，后续支持用户为已安装技能单独配置密钥。下文与图中“bridge专用Provider工具出口/专用图片授权接线”的旧目标不再实施，相关实施明细待按本决定收口；通用隔离、任务权限、真实成果提交和未知事实保护继续保留。此更新不是源码迁移完成或上线证明。

修订：2026-10-28（Asia/Shanghai），v3.1单轨切换，不保留历史执行恢复。Owner：本聊天，任务CODEX-NATIVE-SKILLS-20261027。
状态：实施中。已接入隔离引擎、快照/提案及传输恢复；真实模型空技能读写和固定普通技能脚本执行已取得开发探测证据。API接纳/工具授权、完整删除及三端验收尚未完成，未构建部署，不代表核心交付。本版替代v2.1的实施范围和职责分配；原版保存在 `evidence/responsibility-boundary-20261028/`，原复核证据不重标。

必须遵循：[RB-1职责边界规格](responsibility-boundaries.md)、`/home/isp/wsps/cyf/AGENTS.md`、公共接口 `/home/isp/wsps/cyf/api/docs/interface-standard.md` v1.4。扩展见[扩展详设v3.1](native-execution-extensions-20261028.md)，范围入口见[落地方案](native-execution-plan-20261027.md)。固定源码/实际读取摘要见本任务handoff与本轮evidence；没有fetch或当前线上验证。

本版按[RB-1单轨切换补充](responsibility-boundaries.md#2026-10-28-单轨切换补充用户最新决定)执行，覆盖v3有限历史恢复要求。新方案自身恢复保留；旧执行不续跑、不补传/补提交、不自动迁入新协议。

配套视图：[逻辑、开发、运行、部署及场景（4+1）](native-execution-4plus1-20261028.md)。

## 0. 按职责收敛后的范围

核心只做一次“已授权任务→隔离模型工具执行→真实成果提交”的通用链路。技能是经验包，不是基础执行通行证；工具能力与授权决定能做什么，模型决定步骤。既有安装、执行记录、锁、文件存储、上传/提交/投影继续复用。

### 0.1 代码职责及唯一接收方

C编号仅用于延续追踪，不是七个新服务或七套框架。

| 范围 | API职责 | bridge职责 | 引擎/工具职责 | Web职责 |
| --- | --- | --- | --- | --- |
| C0 接纳/授权 | 执行身份、委派/ACL、可空技能集合、输入/输出合同、lease | 核验并绑定合同、落实边界；不重新定义业务授权 | 只能使用交付的能力 | 提交意图，不强制选技能 |
| C1 隔离执行 | 保留现有调度/执行记录 | 请求环境、引擎会话、事件及恢复关联 | 模型编排，app-server执行真实调用 | 显示进度，不维护第二套完成事实 |
| C2 材料/工作文件 | 原文件访问及来源ACL | 下载/校验/只读交付，隔离工作区 | 读取内容、解析、修改、生成 | 附件选择与失败提示 |
| C3 受控操作 | 通用操作事实、幂等和恢复许可 | 执行上下文、凭据隔离、操作身份/恢复协调 | 参数/Provider协议、远端查询、真实输出 | 通用进度，不按服务编排 |
| C4 正式交付 | stage/commit/投影/下载权威 | 候选快照、提案和终态核对、回执恢复 | 模型选择成果；工具检查内容 | 明确执行关联、成果卡片/安全预览 |
| C5 最小来源 | 受管资料引用、可访问性/删除规则 | 脚本/操作/成果版本关联和最小必要留存 | 提供真实调用/脚本，秘密不入包 | 不要求新增追踪控制台 |
| C6 既有包管理 | 来源/版本/安装授权 | 实体安装、固定版本只读视图与实测能力 | 发现技能并参考说明，不凭包自授权 | 复用技能管理 |

依赖：C0→C1；C0/C1→C2/C3/C6；C0/C2及C1真实终态→C4；C5随上述执行增量记录，不生成候选、不调用模型提取。E1–E5使用核心工具/文件/成果合同；E6使用C5和C6，核心不依赖E6。API不保存完整工具stdout/浏览器状态/引擎会话，仅保存业务恢复所需的通用事实与受管证据引用。

### 0.2 本次保留、移出与删除

- 保留核心：原生执行合同、实际引擎隔离、基础TXT/MD/HTML文件读写/下载、真实成果回传、必要恢复、已有技能版本绑定、已要求的生改读图不回退。
- 专业解析/制作移至工具与技能：Office、图片编码/尺寸、网页操作、FFmpeg、Provider协议。工具可留在同仓；不得通过整体搬目录冒充删除通用入口的业务分支。
- 从核心待办移出：视频制作、提取候选工作流等扩展业务；明确禁止新增Provider轮询器和按技能名的编排。新原生路径解除必须ACTION_REQUEST、必须安装业务技能才可读写文件的前提。不得把禁止项写成已经存在并已删除的代码事实。
- 删除/收缩过度设计：取消强制新增“原生配方runner”，整文件内存问题收窄到本次实际路径，不推为全项目存储重构。通用DAG/异步平台、第二套调度/市场及重复权威状态机继续明确禁止（不宣称旧版已经要求或源码已经存在）。具体Provider异步查询仅在其工具实现。
- 不新增：全量脚本/会话永久审计、逐权限审批、运行费用门禁、任意大小/时限。职责范围内的权限、锁、摘要和未知副作用处理保留。
- 技能主Home完整包与固定只读视图保留为C6目标；不把全量旧目录搬迁/历史清理设为无技能执行前置，只迁移本次安装/执行实际需要的实体。

### 0.3 开发与统一交付

| 开发切片 | 本次具体内容 | 依赖与结束条件 |
| --- | --- | --- |
| K1 端到端最小链路 | 空技能执行合同、TXT读取/真实工具写文件、快照/提案、原生成果关联、stage/commit/下载 | 不伪造技能/成果，真实引擎trace和下载内容一致 |
| K2 核心收口与旧分支删除 | 固定获准技能视图、受控操作接线、必要恢复、最小来源、§16逐项移除越界新入口 | 未完成项不能标完整核心；既有图片等能力不能被切断 |
| X1 已要求能力适配 | E1图片、E2文档、E3浏览器；不修改核心业务编排 | 各自工具/输出与权限依赖具备 |
| X2 扩展制作与沉淀 | E4具体外部服务适配、E5本地媒体、E6提取/私有安装 | 不作为核心的反向前置 |

以上是开发依赖，不要求按切片生产发布。按用户要求统一完成约定批次开发，再集中构建/部署/业务验证；开发中仅必要定向自检。既有Flow每Run≤600秒，不为赶进度跳过回归。核心完成不能冒充X1/X2完成；不因重排职责删除已要求的业务能力。

### 0.4 已确认产品规则

提取技能归当前用户私有；默认安装到当前有管理权的Agent，无管理权仅保存私有候选，其他有管理权的Agent可另行安装，不自动公开。保存的脱敏包独立保留至用户删除；原资料遵守既有删除规则与明确隐私/权利撤销要求。

安装/升级批准固定候选的requiredPermissions，缺真实依赖不得伪报READY。安装权限不是任意任务数据外发或付费重试授权；沿用现有任务权限语义，不增加逐权限/逐Agent确认。现有技能购买和悬赏业务不变。

### 0.5 严格执行

每项改动引用RB编号与下文D编号，在既有handoff记录路径、删除/迁移状态、真实风险和回归证据；不新建审批系统。普通新增技能不能要求三端核心改动。简单明确低风险工作直接完成；不以职责收敛为名整仓重构。职责修订阶段仅修改规格；后续实施状态与证据见任务handoff。§16删除项尚未全部完成，不能以新入口不调用旧代码代替删除验收。

## 1. 首先厘清三个不同的“返回”

1. **模型消息**：流式文字、工具进度、最终说明；用于展示，不授予操作权限，不证明文件存在。
2. **执行成果**：真实文件快照、结构化数据、输入交付证据、固定结果清单；由bridge控制收集和提交。
3. **后端提交/归档事实**：后端认可清单并完成业务投影；这是页面可用成果及任务完成的依据。

`turn/completed`只说明模型回合结束；HTTP 200、WebSocket发送成功、模型写“已生成”也不能单独代表任务完成。bridge不修改模型的业务结论来控制回传，而是控制哪些真实文件可以被提交、提交给哪个执行、何时可声明交付成功。

## 2. 已核实的现有基础与缺口

Runtime源码前缀：`/home/isp/wsps/chcbz/isp-install/conf/codex-bridge/`。

| 源码 | 已存在 | 原生执行所需改造 |
| --- | --- | --- |
| `skill-executor.mjs` / `executeSkill` | 精确包、TaskSkillBinding、claim/resume、runner、结果持久化、stage/commit/receipt | 加入真实原生执行runner，不绕过外层执行生命周期 |
| `agent-client.mjs` / `runSkillNativeModel` | 只读模型返回JSON，宿主后写成果 | 不能把现有native-model名称当原生文件操作；新增隔离工具执行模式 |
| `app-server-adapter.mjs` | thread/turn，文字/终态，read-only与拒绝server request | 明确执行模式策略，工具事件、授权回调、取消/恢复，不能全局取消限制 |
| `skill-conversation.mjs` | lease/fence、inputs、上传、result-commits、resume读回 | 接新runner和成果快照，扩展格式/元信息；保留摘要和持久回执 |
| `skill-execution-store.mjs` | 原子JSON/checkpoint、blob、结果绑定、SkillEffects | 模型草稿与可信blob分离、流式文件快照、多步tool/effect映射 |
| `conversation-native.mjs` | 输出MIME/内容校验 | 当前有固定16MiB和非空限制；不能直接作为新通用文件规格 |
| `skill-install-manager.mjs` | 受管安装、当前视图/保留版本 | 当前完整包实体收口及固定版本只读挂载 |

API入口已核对：
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceConversationRuntimeController.java`：stage、resume、result-commits。
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatSkillResultController.java`：用户结果查询；COMPLETE时核对关联状态后给出成果。

`report-outbox.mjs`的`work.result`执行报告及管理回执不是文件成果commit；不能把它的ACCEPTED当成文件已交付。原生文件继续复用conversation结果链，不额外并行提交第二个权威结果。

## 3. 从接纳到交付的完整时序

```text
用户 → Web/API：任务意图 + 附件引用
API：身份/任务权限 → 固定输入快照、执行、工具授权、可空技能集合和输出范围
bridge：claim/resume + lease/fence → 查询是否已有结果/未知effect
bridge：准备输入、固定技能视图、执行Home和工具能力
bridge → app-server：绑定thread/turn，提交指令和材料索引/原生图片
Codex → 本地工具：读文件、写草稿、调用技能脚本
Codex → 图片/浏览器MCP：受控操作，bridge记录工具/effect事实
Codex → artifact.stage：申请将实际草稿冻结为候选成果
bridge：安全打开/快照/校验/算摘要/持久化 → 返回artifact引用
Codex → result.propose：选择最终候选成果及说明（不提交后端）
app-server → bridge：回合completed
bridge：确认提案、工具状态、授权和输出合同，冻结唯一result
bridge → API：逐文件stage → 核对stage回执
bridge → API：提交result manifest → 核对commit回执
响应丢失：bridge → API resume读回持久事实；不重新执行模型/Provider
API：归档/投影 → 用户结果查询可返回可下载成果
bridge：持久receipt → 释放本执行资源；按可恢复性清理
```

MCP工具名 `artifact.stage`、`result.propose` 是本项目拟新增逻辑名称，最终transport合法工具名在固定MCP协议适配时映射；不是宣称Codex内置这些方法。

## 4. 执行身份、授权和单/多技能问题

### 4.1 服务端绑定的执行上下文

bridge在内存和私有checkpoint中绑定：tenant/client/owner、Agent、task/run/conversation及generation、executionId、commandId、输入snapshot摘要、可空的固定技能安装/摘要集合、工具能力、threadId/turnId、lease/fence、取消/撤销状态。

这些字段来自已认证API/受管本地状态。模型工具参数不得选择另一executionId、Owner、Provider凭据、安装版本或API地址。每个MCP连接/服务实例由bridge预绑定执行，不能仅信任模型传入taskId。

### 4.2 基础能力与技能执行授权（RB-02/03/06）

- 新原生接纳合同绑定执行身份、输入快照、工具能力、输出范围和**可为空**的精确技能集合；无技能不伪造TaskSkillBinding、不自动安装“万能技能”。
- 普通任务使用C1/C2基础工具即可探索、编写临时脚本并交付；临时脚本只能在当前沙箱权限内运行，不被当成已安装受信技能或新的网络授权。
- 现有v4 parseSkillCommand要求单skill/TaskSkillBinding，不能直接删校验或把null塞进去。新增原生执行合同显式协商，将公共claim/resume、材料、effects、结果提交生命周期复用/提炼给无技能和有技能入口；旧命令不再接纳或恢复，不得伪装成新原生命令。
- 非空技能集合复用现有安装/TaskSkillBinding权威，接纳时固定每包安装ID/摘要及授权，不挂全部主Home。新集合字段/执行语义同步API、Runtime和Web消费者，不依靠旧消费者忽略未知字段执行。
- 基础TXT/Markdown读取不新增购买项；任务使用付费/外部工具须有相应授权，技能为空不是任意外网/任意凭据权限。
- 输出合同来自用户任务和工具能力，不要求从某个技能manifest推导。要求MP4的任务明确允许该类型，纯读图解释可无文件；现有只允许单TXT的合同不能冒充支持视频。
- 需要未获准工具/技能时返回具体缺口，用户授权后按明确的新执行/授权修订绑定继续，保留旧执行未知effects，不偷偷重放。

### 4.3 新旧合同落点：复用生命周期，不冒充旧接口已支持空技能

| 现行约束 | v3.1目标职责 | 单轨/只读边界 |
| --- | --- | --- |
| parseSkillCommand及executor强制skill/descriptor | 通用执行入口先验证执行合同；非空技能逐包核验 | 切换后仅新执行合同可写；旧命令明确不支持，不进入执行 |
| 输出合同取descriptor.manifest.outputs | 无技能取服务端冻结的执行输出合同，有技能还满足其声明 | 不创建假manifest/虚拟已安装技能绕校验 |
| result/inputReceipts校验依赖runner | 原生载体按实际文件交付方式核验 | 不冒称local-script或已阅读全文 |
| claim/resume/result-commit及结果查询基于旧技能/协议 | 复用状态存储、锁和相同提交语义，扩展明确的原生接纳/读取分支 | 必须改API服务和消费者；不声称仅Runtime改造 |
| 用户结果查询含旧协议条件 | 能读取明确的新执行类型及其投影 | 旧历史按原摘要/绑定读取，未知执行语义不猜测 |

本文§9记录已核实的现有路由/preimage，作为复用基线，不保证无技能新合同能原样通过现有校验。实施时在现有管理合同列出实际字段/协议版本、生产者/消费者和混合回归；路径能复用则复用，不为命名统一另建结果系统。新结果绑定仍包括执行身份、输入快照、输出范围及有技能时的精确包，不因skills为空丢失授权来源。

### 4.3.1 普通消息生产者的明确协议（2026-10-28实施接线）

沿既有CHAT模型结构化动作选择、身份/授权、dispatch和EXECUTE step/link生产链，不按关键词触发，不要求用户手填动作请求，不新增旁路调度器。

- 认证注册`typedDeliberation.nativeExecution`新增可选能力声明：`{schemaVersion:1,executionProtocolVersion:5,toolPolicyRef:"NATIVE_LOCAL_FILES_V1",outputMimeTypes:[...]}`。当前基础文件候选为TXT/Markdown/HTML/JSON；广告范围必须与API真实配置/输出实现求交，不因Runtime支持就自动放行。
- 原生动作的facts明确使用`schemaVersion:6`；新增`{actionId,kind:"EXECUTE",operation:"EXECUTE_NATIVE",skill:null,parametersSchema,inputMimeTypes,minSources,maxSources,outputMimeTypes}`。`actionId`由API冻结，bridge视为不透明标识；当前parametersSchema是无额外字段的空对象。旧facts v5不接受此新操作，旧`EXECUTE_SKILL`仍必须有真实技能描述符，不能null降级。
- 模型最终结果仍为outcome v5的`ACTION_REQUEST`，选择精确actionId、instruction及获准sourceRefIds，parameters为`{}`；模型提议不是执行授权。API验证后才创建协议5命令，`skills:[]`合法，输出合同由API冻结。
- `NATIVE_LOCAL_FILES_V1`不授予图片Provider等外部工具。普通技能选择、Provider授权及effects接线必须分别完成，不从动作名称或技能内容推导授权。
- Runtime启动阶段由独立 `NativeExecutionProfileRuntime` 异步测量原生隔离/工具链就绪并缓存，不依赖 `inputCarriers`、资料materializer或资料证据；与资料Owner共用 `IsolatedEngineProfileRuntime` 隔离实现。探测、注册声明、实际执行、提交/失败清理必须使用同一原生Owner；任一能力失败不抑制另一能力，关闭期间不再启动/发布。registration只同步投影缓存，presence不带能力目录，不随心跳重启探测。缓存不是每次执行授权，实际执行仍校验固定字节、隔离和lease。
- 纯文字ANSWER继续走既有文本链。原生执行若尚未把文字持久化并提交为权威结果，文件动作必须要求真实artifact；不得用`artifactsRequired:false`加空data/空artifacts把未提交文字标成完成。

本节是当前未发布候选的明确接线合同，不代表普通消息生产者、全MIME、注册实机探测和三端验收已通过；定向证据及真实缺口见主handoff。

### 4.4 材料清单、失败材料与执行中新增材料

接纳时完整来源清单包含全部用户引用及其交付状态，冻结输入快照不静默移除失败项。当前v4要求每个冻结input都有DELIVERED回执，且不接受额外input；因此原生合同必须明确区分“所有来源的处理记录”“已交付输入集合”和“本次输出必需输入”，不能把失败附件伪报DELIVERED。

新原生合同在固定来源清单中绑定逐项成功/失败/未支持事实及范围；文件载体失败是通用交付事实，不要求API理解解析算法。仅当任务可独立完成且用户要求允许时交付部分结果，并说明缺失项。影响必须输出的材料失败则该目标不可成功。旧v4仅保留既有事实只读，不提供补回执/恢复，不修改其摘要。

浏览器下载、图片/视频工具输出属于执行中派生材料，不追加进原用户输入回执，也不覆盖原snapshotHash。bridge追加不可变派生记录：当前执行、产生的工具/operationRef、字节hash、来源地址或原材料引用（秘密脱敏）、当前ACL、可用于哪些后续工具。以新原生合同的派生清单摘要绑定最终结果。下载到文件不等于得到上传到另一站点的授权；后续外发仍核对范围。

### 4.5 有效能力计算

有效能力 = 固定引擎可用工具 ∩ Runtime实装依赖 ∩ Agent配置 ∩ 本执行授权。
公共supportedInputs由公共配置/载体探测产生，Agent仅覆盖差异。技能依赖探测和实际安装状态仍按现有registry；不把安装SKILL.md等同于依赖可用。
声明输入可交付与“保证语义解析成功”分开：能传原文件不代表能解密/读取任意Office；逐文件保留交付与处理状态。

## 5. 文件系统、技能包与进程边界

### 5.1 不可信可写区与可信结果库必须分开

以现有 `SkillExecutionStore.directory = <workspaceFileRootDir>/skill-runs/<scopeDigest>/<executionId>` 为可信执行状态根；该根不挂给模型。

```text
<execution-root>/
  identity.json / command.json / result.json / receipt.json  # bridge私有
  effect-*.json / tool-*.json / selection.json               # bridge私有事实
  outputs/<outputId>              # 已冻结可信blob，模型不可写
  inputs/                         # 校验后只读挂入 /inputs
  scratch/                        # 模型工作区 → /workspace
  drafts/                         # 拟新增，模型产物区 → /outputs
```

注意：**沙箱的 `/outputs` 是宿主 `drafts/`，不是现有store的 `outputs/`**。否则模型可以在hash后改写可信blob，破坏恢复和commit。

请求/执行Home沿既有inspection-state绑定路径保留配置/会话，不再次复制execution-root；通过一份私有映射绑定Home、execution、thread和挂载。路径示例不再扩建第二套结果存储。

### 5.2 挂载与隔离

- `/runtime`、`/inputs`、获准`skills/<key>`只读；`/workspace`和草稿`/outputs`可写。
- 主Home下配置、auth、其他技能、浏览器秘密、其他任务都不挂载。
- 进程状态目录按引擎实际需要最小放行；有效配置和能力由bridge固定，引擎不能通过模型写配置获得更多MCP/网络。需要可写Home状态时，不把“文件只读”作为唯一权限依据。
- 当前选定引擎的工具还会创建内层沙箱：外层用户命名空间采用非root身份映射并丢弃capabilities；只读中性根预建引擎必需的空`.git/.codex/.agents/.aws`挂载点（无配置/凭据）。这避免uid-map及只读挂载目标创建失败，不改变宿主身份、不关闭内层沙箱。绑定和真实command/exec回归固定该结构；详见handoff的2026-10-28探测。
- 复用bwrap namespace及固定工具链；本地命令无直接外网。模型服务、图片、浏览器访问走各自受控通道；不允许可执行包自行调用任意Provider绕过effect。
- 执行拥有明确进程组/生命周期记录；取消只处理本执行进程，不按进程名全局kill。重启核对PID/start身份，避免误杀PID复用后的进程。

### 5.3 引擎自动发现范围必须封闭

真实只读探测发现：系统Codex 0.164.0不仅发现CODEX_HOME中的技能，还发现cwd下`.agents/skills`，并自动具有system scope技能。此探测未运行模型，证明发现范围，未证明恶意技能已经执行。因而“只挂获准主Home包”不足以保证实际发现集合。

原生执行的thread cwd设为bridge控制的只读中性根（逻辑路径`/execution`），不设为用户附件目录或模型可写workspace；其祖先、引擎配置/插件及所有候选发现根按固定引擎实际机制治理。工作文件仍在`/workspace`，工具明确指定路径，不把可写目录当隐式受信项目根。若引擎仍扫描其他路径，使用实测支持的禁用/根配置或只读遮蔽；不能凭空假定有allowlist配置项。

初始化、技能刷新及恢复时核对实际发现清单：业务技能必须匹配授权路径/包hash；系统技能单独归入固定引擎受管清单，不能把其出现解释为安装/网络/付费授权。文件名为SKILL.md/AGENTS.md的附件和工作区生成文本只是资料，不能自动进入受信技能/开发者指令。发现越界项时阻止受影响执行并报告原因，不静默替换或自动授权。新原生路径统一使用隔离环境，包括无附件/纯TXT任务，不能沿旧hasNativeMedia分支落到主Home执行shell。

### 5.4 技能升级/停用

当前完整包在主Home `skills/<key>`；本节版本固定/安装恢复仅用于新方案，不用于保留旧协议执行器。新方案在途所需的包版本仍保留。安装锁内暂存校验、写迁移意图、归档旧包、发布新包、更新索引、完成记录；启动恢复处理半完成切换，不读混合包。
逐包只读bind固定到执行Home，不随主Home升级重挂。跨文件系统迁移不假设rename原子，先按摘要验证复制候选、切换索引，最后在无引用时清理旧实体。
停用禁止新接纳；既有明确撤销通过broker/API检查阻止后续受保护调用。目录移除不是授权撤销机制。原生并发执行不能修改共享技能脚本。

## 6. app-server与工具接线

### 6.1 适配器模式

保留现有只读CHAT模式；新增“已授权原生执行”策略对象，包含固定可读/可写挂载、网络通道、工具集合、执行绑定与输出范围。不是全局替换approval或sandbox常量。

实施第一步锁定实际交付的Codex二进制及生成schema，验证initialize、thread/start/resume、turn/start、事件、interrupt、skills/list、MCP状态和工具调用。系统0.164.0的发现探测不能代替生产候选验证。使用真实支持字段，不以未知字段被忽略当成安全策略生效。

### 6.2 工具如何执行

- 沙箱文件/命令工具由app-server实际执行；bridge靠外层隔离、只读挂载和出口限制控制边界。**不是每次shell调用都会回调bridge审批**。
- 图片/网页/成果工具经已配置的受控MCP服务。服务入口预绑定执行，内部检查有效授权/lease，并持久化操作事实。
- MCP工具调用与app-server向客户端发出的approval/user-input请求不是同一种消息，不能把处理某个server request当成所有工具均可用。
- bridge只处理固定schema中需要客户端回答的请求；未获准动作拒绝对应请求，用户澄清不直接增加权限；不要在原生模式继续无差别拒绝所有server request。

### 6.3 事件规范化与展示

adapter把真实事件映射为内部类别：模型文字、工具开始/进度/完成、候选成果、提案、回合终态、需要用户输入、异常。内部类别不是新的app-server方法名。

按execution/thread/turn/item关联；文本用于展示，工具stdout是非可信内容，不能解析某个“SUCCESS”字符串自动提交成果。工具参数/日志中的凭据和页面秘密脱敏，不保存或展示模型隐含推理。

已有事件消费者新增无害进度字段可忽略，但不能忽略新的执行/完成语义。事件重放按持久工具调用ID去重；若引擎未提供可靠序号，不伪造严格的引擎事件序号，bridge自己的发送序号仅用于自身下游游标。

## 7. bridge如何收集结果：具体工具合同

### 7.1 `artifact.stage`：收集一次真实文件快照

拟新增工具输入（仅业务参数）：

```json
{
  "path": "/outputs/analysis.xlsx",
  "displayName": "分析结果.xlsx",
  "mediaTypeHint": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

工具连接已绑定执行；path只允许草稿区文件，不接受任意host路径/URL。名称是显示建议，不参与宿主路径拼接；MIME hint不作为实际内容真实性依据。

执行算法：
1. 检查连接执行、授权、取消状态；禁止在最终清单冻结后新增/替换成果。
2. 以固定草稿根dirfd安全打开目标，拒绝绝对路径逃逸、`..`、软链接/magiclink、设备/FIFO/socket和目录；使用支持`openat2(RESOLVE_BENEATH/NO_SYMLINKS)`的固定小helper或等价逐层dirfd方案，不能用字符串startsWith或“realpath后再普通open”代替。
3. 从已打开FD流式复制到**bridge私有临时blob**并计算SHA-256/字节数，核对前后元信息；源在复制中变化则报告文件尚未稳定，允许模型关闭写入后重试。文件事件/inotify只作提示，不作为文件完成证明。
4. 调用格式适配器对复制后的同一字节快照做必要格式验证（不在通用收集器解析业务内容），fsync文件；分配稳定outputId并登记调用→output映射，将私有临时blob发布到可信outputs后fsync目录。失败临时文件仅清理本次拥有的对象。
5. 返回artifactRef/outputId、实际MIME、字节数、摘要、已快照状态。模型看到的是候选引用，不是后端已交付回执。

复制后模型再改草稿不会改变已冻结结果；要提交修改版必须stage一个新候选。重复同一调用使用已有映射，不能重读已经变动的源；模型主动再次stage视为新候选，可在本执行内对相同内容节约blob，但不同显示名称/选择意图仍独立记录。暂不跨Owner全局去重。

### 7.2 `result.propose`：指定最终成果集合

拟新增工具输入：

```json
{
  "summary": "已分析数据并生成结果。",
  "artifactRefs": ["artifact_generated_by_bridge"],
  "data": null
}
```

返回 `proposalId`、提案摘要、`pending-finalization`。只允许选择本执行已stage的引用，验证输出合同、多文件要求及dataSchema。模型不提供artifact hash、bytes、inputReceipts、manifestId或最终完成状态。

回合完成前可显式修订提案，旧提案留审计，不上传成正式结果。回合正常completed后，bridge核对无未决受保护工具、提案有效、授权/lease有效，冻结最后已接受提案。最终文字作为展示说明；不能从Markdown链接正则扫描宿主文件自动交付。

提案和回合终态也要可恢复：bridge持久绑定proposalRevision、所选artifact摘要集合、thread/turn及工具调用关闭事实，再核对引擎终态并冻结result。仅持久提案但终态事件丢失时须查询原回合；不能从模型最终一句话或候选文件存在推断completed。最终清单冻结与新候选接纳在同执行锁下互斥，收到晚到工具事件先核对既有调用，不覆盖已冻结清单。没有足够引擎终态证据时保留待核对，不新开回合重做付费步骤。

没有提案：纯文本任务若合同允许，bridge可将该回合最终文本作为文字结果；要求文件的任务不能静默空成果成功。可在同一执行继续明确的补交回合，但先查工具/effect状态，只收集已生成文件，不自动重跑外部操作。

### 7.3 部分成功、取消、失败

默认最终清单是原子交付集合，不能只上传其中成功文件就宣布全任务完成。允许部分交付时由用户意图/合同明确，记录缺失项；不能把失败操作从历史删除。
取消/失败回合的候选保留私有恢复证据，不自动发布为最终成果。用户后续明确要求取回部分结果时，通过获准恢复/交付路径使用已有快照，不重做Provider。

## 8. MIME、内容检查和输出元信息

校验目标是正确交付、防越界、防主动内容跨域，不是bridge理解每份表格业务。

| 类型 | 传输/成果检查 | 业务正确性验收 |
| --- | --- | --- |
| TXT/MD | 合法编码；允许合法零字节文件，不能以全格式非空统一拒绝 | 中文/范围读取/所需内容 |
| HTML | 合法文本，类型明确；预览隔离而非全盘删除用户代码 | 实际隔离浏览器加载 |
| CSV/JSON | 文本及对应结构；CSV公式按明确语义区分 | 重新读取核对字段/记录 |
| PNG/JPEG等 | 格式签名与必要解码，沿用图片行为 | 内容/尺寸/透明补边 |
| XLSX/DOCX | 验证OOXML必要结构，ZIP条目不越界；不执行宏/外部关系 | 相应库重开核对表格/段落 |
| PDF | 格式/必要解析，不执行主动内容 | 中文/页/提取/生成核对 |

对不可信压缩文档避免全量解压到任意目录；资源使用要实测并给具体错误，不无依据复制一套硬编码大小门槛。需要保护解压资源时按实测风险另写阈值依据，不承诺无限资源。

现有16MiB/非空规则及客户端、API、网关限制只核对本次交付经过的路径。空TXT有效，空XLSX无效。快照按流复制；上传/存储复用既有multipart。对本次文件范围实际导致内存或交付失败的整文件缓冲路径做定向修改，不承诺无限大小，不要求全项目流式存储重构，也不新建分片协议。仍存在的真实限制须明示，必要校验依RB-10写出依据。

现有结果摘要preimage只覆盖data、artifact outputId/hash/length、inputReceipts。显示文件名等新增元信息如参与安全/语义必须定义新的明确摘要版本或已绑定的元信息记录；不可偷偷加字段重算历史摘要。旧清单继续按原preimage校验。新旧摘要golden fixture在JS/Java双侧验证，不因JSON字段顺序或数字/字符串转换漂移。

## 9. bridge结果回传：复用现有精确HTTP链路

以下是已存在路由，公共信封/鉴权由现有transport适配；示例为业务层payload，不是可直接绕过鉴权调用的curl。

### 9.1 本地持久结果

bridge把已选择快照投影为现有result结构：executionId、snapshotDigest、data、artifacts及inputReceipts，先保存blob，再写result checkpoint（临时文件→fsync→rename→目录fsync）。输入交付回执由文件交付/载体层生成，不能让模型自证“已阅读”。“已交付”不等于“模型完整阅读全部内容”。

新原生runner必须扩展当前 `local-file`只允许`local-script`的回执规则，并在合同说明原生文件载体语义；不能假填`local-script`绕过校验。

同执行已经冻结结果时，不接受另一摘要覆盖。需要修改正式结果则走明确的新执行/修订，而不是修改旧manifest。

### 9.2 上传每个输出

```text
POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/outputs/{outputId}/content
multipart:
  file=<可信快照流>
  version=<lease version>
  token=<lease token>
  sha256=<快照SHA-256>
  byteLength=<十进制字符串>
```

bridge以受管Runtime身份调用，模型不能看到鉴权头/fence。后端再次校验身份、任务、lease/fence、长度、摘要；文件存储操作受现有执行锁协调。

现有stage回执含outputId、sha256、byteLength和STAGED/COMMITTED。bridge逐项匹配后才推进；一个文件失败则该文件待恢复，不能靠HTTP成功码认为全清单上传成功。同outputId同内容可重传/读回，异内容为冲突；不能换新ID制造重复成果。

已stage但未commit的是暂存，不向用户冒充正式可下载成果。

### 9.3 提交唯一结果清单

现有计算：

```text
preimage = { schemaVersion: 1, data,
             artifacts: [{ outputId, sha256, byteLength: number }], inputReceipts }
digest = SHA256(existingCanonicalJson(preimage))
manifestId = "manifest_" + digest
POST .../conversation/result-commits/{manifestId}
payload = { fence, snapshotSha256, data,
            artifacts: [{ outputId, sha256, byteLength: string }], inputReceipts }
```

数字/字符串转换沿现有明确投影，不能直接对wire字节hash替代preimage。artifact顺序冻结；语义变化必须升合同，不重排历史结果。

bridge核对回执：manifestId相等、state=RESULT_COMMITTED、resultSha256等于本地摘要、phase为ARCHIVING/COMPLETE；内部适配使用resultDigest，公共字段resultSha256，不能混用。

后端按RB-02在事务/执行锁下确认全部输出存在且摘要一致、绑定有效、没有冲突结果，再持久结果并推进归档投影。网络响应不构成跨文件存储/数据库的天然分布式事务：先stage后commit、恢复读取和孤儿暂存清理解决中间状态，不宣称上传事务可自动回滚外部存储。

### 9.4 回执持久化与完成语义

bridge保存receipt（execution/snapshot/localResultDigest/manifestId/resultDigest/state/phase）后可释放模型进程与挂载；删除唯一成果blob前要核对后端持久状态/完整性及恢复需要。

RESULT_COMMITTED + ARCHIVING：结果已提交，业务投影仍在完成，页面不能声称所有成果可用。
COMPLETE及关联链状态完整：用户结果接口给出正式outputs，下载经用户ACL。bridge不能直接把宿主路径或Provider临时URL当下载地址。

现有 `ChatSkillResultController`在COMPLETE时检查step/link/request等事实；沿用该路径。浏览器/Web刷新只是读投影，断线重连读回事实，不依靠一条易丢的“完成”推送。

### 9.5 前端成果发现也必须改，不能只复用展示卡片

现有`hallSkillResults.js/skillResultReferences`仅从schemaVersion6、outcomeContractVersion4的ACTION_REQUEST及其child EXECUTE关系取executionId；新原生直接执行即使后端提交完成，也不会自动进入这条发现链。新接纳时由后端在现有request/step/execution关系中持久化原生执行引用，Web通过明确版本化的请求/步骤投影发现并查询结果；不得伪造模型ACTION_REQUEST或扫描“最新成果”猜归属。

这属于Web/API的成果关联职责，不属于重新设计页面或新增执行调度。复用原成果卡片/下载，不等于数据源和合同无需改动。同步修改现有结果查询对协议4的条件、Web精确字段解析与允许的增量字段、刷新/恢复路径；旧结果引用与摘要继续可读。当前Web允许MP4作为下载项，但不在inline MIME集合，带预览URL会被拒绝；增加视频播放必须同时修改服务端预览策略、Web校验/播放器与回归，不能仅输出previewUrl。

## 10. 新方案结果状态与失败恢复表

本节仅用于新方案已接纳执行；不为切换前的旧协议执行恢复上传、commit或归档投影。

下列本地阶段是说明/checkpoint设计，非要求新增一整套API状态枚举：

```text
ADMITTED → RUNNING → CANDIDATES → RESULT_FROZEN
         → OUTPUTS_STAGED → RESULT_COMMITTED → PROJECTED → RETIRABLE
```

持久事实优先于内存阶段；恢复必须核对snapshot、版本、工具状态和后端allowedWork。只能在明确允许时继续执行。

| 故障点 | 持久证据 | 恢复动作 | 禁止 |
| --- | --- | --- | --- |
| turn/start响应丢失 | 执行→thread/clientMessage绑定 | 查询原回合；未知则保留未知 | 新建回合重做任务 |
| 草稿写完未stage | 工作区及工具记录 | 核对后可补收集 | 当文件存在就已交付 |
| stage复制中崩溃 | 私有temp、未完成收集记录 | 清本次temp/重收稳定草稿 | 使用半文件 |
| blob完成但结果未冻结 | 候选及选择提案 | 恢复选择/核对终态 | 扫目录全部上传 |
| 一个输出上传响应丢失 | outputId/hash/本地blob | 同ID确认/重传同字节 | 新生成文件或新outputId绕过去 |
| commit响应丢失 | result.json/manifestId | POST原resume，核对服务端清单；同manifest重交 | 调模型/Provider再生成 |
| commit完成、receipt未落盘 | 后端resultManifest | 验证清单后补本地receipt | 缺本地blob就误判任务未做 |
| ARCHIVING/投影失败 | 后端持久结果 | 修复/重试同一投影 | 重新stage并创建第二个执行 |
| Provider调用后断线 | effect START_RECORDED/UNKNOWN | 查询真实Provider事实；无法确认则待处理 | 盲重试付费操作 |
| lease过期/身份改变 | 原fence/身份 | 停止受保护新调用，resume重新确认权限 | 旧lease继续提交 |
| 取消与commit并发 | 后端执行锁下结果 | 按已持久先后读回真实状态 | 宣称已提交结果被撤回/外部操作被回滚 |

文件上传/查询等幂等恢复可以退避重试；“同根因同输入连续失败两次停止盲重试”不等于禁止已明确幂等的受控恢复，但不得对不确定副作用重复invoke。网络错误需分类；不因任意SLO中止模型流。

## 11. 通用工具调用与副作用机制（C3）

### 11.1 统一受控调用入口与多步effect

每个工具调用记录执行、工具名/版本、引擎item/tool call关联、授权摘要、输入摘要、开始/结果及产物引用；秘密字段不入日志。bridge分配持久操作ID，不把用户提示hash当操作身份。

多步执行允许多次生图：每次明确新调用获得新操作ID；同一传输重送映射原ID。当前image runner中固定`generate` effectId不能直接用于整个原生多步任务，须按持久工具步骤命名。参数发生变化而仍使用原ID必须冲突，不能覆盖旧收费事实。

现有SkillEffects保留“服务端start→本地start落盘→外部调用→结果blob落盘→report确认”顺序。恢复成功effect只读回/补报；未知effect停止依赖该结果的步骤。模型声称“再试一次”不能自动把未知付费调用包装为新ID。

### 11.2 原生多步恢复不能沿用旧runner的整体EXECUTE判定

已核对API现行resume：有任何effect且无最终manifest时，只给QUERY_EFFECT/RECOVER_LOCAL_RESULT，即使该effect已SUCCEEDED也不再给EXECUTE。现有SkillEffects.mayStart据此禁止新effect。这适合原单runner恢复，却会阻塞原生任务“完成图片后断线，再继续配音/合成”。

原生合同新增明确的续执行授权语义（具体wire枚举随合同固定）：在同execution/fence下恢复已确认步骤，允许尚未开始且仍获准的新步骤，禁止重放已有/未知操作。持久操作ID独立于模型turn/itemId，多个引擎重连ID可关联同一逻辑操作；不能仅以新callId认定用户要再付费一次。接纳新调用前向恢复上下文提供已有operationRef及其状态；UNKNOWN的替代调用不能用换ID绕过，确需重新操作须有明确处理决定。

错误分类区分未发送前校验失败、远端明确拒绝、调用后结果未知；当前invoke将异常统一UNKNOWN，不能直接当通用语义复用。任务必需外部操作UNKNOWN或仍在执行时不能报告完整成功。是否为必需操作按服务端冻结的输出/授权合同及真实产物依赖核对，不能由模型随意标成“非必需”来隐藏未知副作用。已确定失败的非必需探索步骤可继续替代方案，保留失败记录，并在最终清单记录相关操作依赖/未交付项；当前后端“所有effects必须SUCCEEDED”的commit校验须按新原生语义扩展，旧v4执行/提交校验随旧写路径退役，不把历史FAILED/UNKNOWN改写为成功。

### 11.3 通用工具与服务机制（C3）

C3的API部分仅保存业务授权与通用操作事实，bridge部分实现执行绑定、工具声明/版本、凭据引用、边界落实和持久操作恢复；图片HTTP编码、视频参数、Office算法不进入核心。工具是固定实现或已授权执行脚本的受控入口，不是模型自注册一个工具就获得权限。
Provider提交/轮询/取消/错误码映射由E4等具体工具负责，API不新增Provider专属调度，bridge核心不按job状态编排业务。通用外部HTTP调用属于E4，通过C3隔离凭据/记录effect；模型可以编写服务请求组织脚本，但不能读取秘密或绕过出口。新增服务不一律新增bridge分支。依赖声明只描述需要，不自动授权网络、收费或安装程序。

## 12. 扩展实现入口

图片、文档和浏览器的原详细约束已迁入扩展详设，并新增通用HTTP、本地视频及技能提取：`/home/isp/wsps/cyf/specs/juyiting-skill-execution/native-execution-extensions-20261028.md`。
本文§8保留通用成果安全/格式规则；具体库、Provider、浏览器步骤归扩展。扩展可以和核心同仓发布，逻辑依赖不得反向变成“核心要有视频技能才能运行”。

## 13. 持久化、并发、清理与观测

单execution只有一个有效提交者，由现有lease/fence及执行锁控制；不能仅靠进程内Map防并发。多个Agent/执行可以并行，不共享可写工作区和tool session。文件stage/最终提案通过本执行串行化点协调；final freeze后拒绝新候选，不截断仍在进行的工具操作假装完成。

保留已有store，拟新增工具调用映射、候选索引和提案checkpoint；不另建权威业务账本。后端仅在现有执行/绑定合同中增加必要集合/元信息；是否需DDL在定位现有存储后固定迁移，不凭方案臆造已存在表。新字段不修改历史hash原文。

清理分三类：
1. 模型进程/挂载：终态或有效取消后只释放本执行。
2. scratch/drafts/输入副本：结果/恢复证据足够且无活动引用后清理；保留未知effect必需资料。
3. 新方案可信blob/所需技能版本：后端持久成果已核对、无新方案恢复引用再回收；新方案在途绑定版本不能删除。旧协议状态只按历史数据保留规则处理，不因此保留旧执行器。删除意图/结果可恢复，孤儿先核对事实，不按年龄全删。

记录：执行/工具ID、模型与引擎版本、包摘要、输入交付状态、产物hash、upload/commit/投影状态、实际耗时和错误。绝不记录Key/完整Cookie/密码，不把敏感原文全量复制日志。性能观测不添加任意拒绝请求阈值。

### 13.1 执行来源的最小关联（C5，不含提取工作流）

记录应在执行开始建立，不等点击“提取技能”才找已删除文件。每次可观测的脚本运行关联：工具调用/命令身份、脚本内容摘要和私有版本快照、工具链版本、获准输入引用、退出/失败事实和所产成果。会话可跨多个执行，来源通过精确执行/修订引用串联，不共享未绑定可写工作区。

shell inline命令与生成脚本也纳入可观测快照；脚本/子进程在运行时动态修改、代码来源无法确定或引擎未暴露足够事件时，明确标记证据不完整，不能声称捕获了实际执行的全部代码。在受控命令入口捕获执行前版本并与运行后变化关联，不靠事后只扫最终文件。C5不要求无限制录制终端、浏览器密码或模型隐含推理。

API只管理受管资料引用及访问/删除，不保管整个引擎trace或解释脚本。提取所需源码包与临时scratch分开：在已授权任务留存范围内，将最小脚本版本/依赖/成功成果关联保存为私有资料，绑定Owner和ACL；不得把全部工作区当审计包长期保存。凭据注入在C3，不进入脚本；发现硬编码秘密时阻止其进入可复用/分享包，并将相关源证据按敏感资料规则处理。脱敏派生件有自己的hash，不能冒充原脚本hash。

后端提供来源可用性和保留策略，保留期限沿既有资料规则/明确设置，不在此臆定永久或固定天数。未实现持久来源归档前，不能在UI承诺任意历史会话都可提取；只显示仍可访问的来源。历史记录缺源时允许生成标注为重建/待验证的候选，但不能冒充从成功脚本直接提取。

### 13.2 回收条件补充

删除scratch前，若该执行在获准可提取留存范围内，先确认最小来源包已持久化或明确标记留存失败并交由既有保留策略处理；不能一边宣称可提取一边清掉唯一脚本。来源包删除与用户数据删除/权限撤销一致；提取中的来源引用在本任务内保护，完成后释放，不长期阻止全部目录清理。

## 14. 按职责的实现与测试入口

| 工作项 / RB | 路径或职责落点 | 最小有效验证 |
| --- | --- | --- |
| 接纳/恢复/成果 RB-02/08 | API既有SkillExecutionService、PersonalWorkspaceExecutionServiceImpl及controller | 空技能合法绑定、明确续执行、stage/commit幂等、历史摘要不变 |
| Web关联/展示 RB-01 | hallSkillResults.js、useHallSkillResults.js、bountyOutputCatalog.js | 不造ACTION_REQUEST也能找到成果；刷新一致；归档中不显示已交付 |
| 隔离/引擎 RB-03/04 | adapter、agent-client、profile | skills为空真实工具读写；主Home/凭据不可见；仅实际授权技能可发现 |
| 成果工具 RB-03/05 | 现有execution-store及snapshot、stage/propose接线 | 稳定快照、路径边界、空TXT、提案/回合绑定、丢回执恢复 |
| 受控工具 RB-05 | image-provider等工具注册/通用操作上下文 | 模型实际调用工具；不经通用入口固定编排；同操作不重复发出 |
| 包管理 RB-06 | 既有installer/registry | 当前/旧固定版本、停用/撤销、无技能依然可执行 |
| 来源 RB-07 | 私有最小脚本/成果关联及API资料引用 | 可访问来源能追溯；删除后不可用；无秘密/全工作区复制 |
| 删除 RB-11 | §16逐项代码路径 | 实际diff、旧执行/恢复不可达、新方案恢复及图片/文件能力不退化 |

不把E2/E3/E5/E6业务实现列为C0–C6通用模块；各自验证见扩展详设。复用已有Node测试及API SkillExecutionServiceTest、ConversationLeaseWireHttpTest等真实入口；执行前核对selector和固定源码，不另建大runner。

针对实际持久边界覆盖：上传/commit响应丢失、外部操作未知、取消与提交竞态、回合终态丢失、源文件替换/写入及落盘失败；按RB-10风险范围选择测试，不要求与改动无关的“所有阶段所有故障”排列组合。

必要测试/构建/打包默认在本地固定干净源码执行，复用既有工具；本地构建发布同批默认上限600秒，保留现有阶段拒绝及本批构建RuntimeMaxSec终止行为；预计或实际超限须向用户申请例外，未获批不延长、不绕过。此限制不用于业务请求或生产服务强杀，不删必要回归。业务验证包含真实工具trace、文件重开/下载和后端提交投影；模拟、局部快照测试、文档检查都不能替代。真实服务使用获准测试输入，不重放旧事项。

## 15. 实施前必须固定但不得假装已验证的参数

设计已选定：只读技能挂载、隔离草稿/可信blob、显式stage/propose、既有HTTP结果提交、受控图片/浏览器MCP、现有管理系统复用。

以下在K1/K2及对应扩展实施时取得真实值，记录到同一handoff，不要求再开一轮泛化架构讨论：
- 交付Codex版本、实际schema、MCP传输/配置字段和工具事件形态；不沿用未经验证的系统版本。
- 现有工具链中Python/Office/Chromium/Playwright精确版本、依赖锁/镜像摘要、sandbox内可达路径。
- 当前API/Web/网关格式/大小/空文件限制与所需协同修改、流式存储适配能力。
- 新原生执行合同（含空技能集合）、授权技能集合、输出元信息与提取来源/候选的实际协议版本/DTO；未支持新合同的Runtime不获派新任务，不自动降级旧runner；无害字段兼容不构成旧执行恢复。
- 安全文件打开helper与最终进程权限实测；跨重启包索引/挂载/回收验证。

这些是具体实现验证项，不是已上线能力。仅文档检查通过不得把本详设标成原生执行验收通过。


## 16. 既有越界实现与明确删除清单

核对日期2026-10-28；源码基线和工作区hash见本轮evidence。以下是**待实施删除/迁移任务**，不是已完成源码整改。路径缩写：RT=`/home/isp/wsps/chcbz/isp-install/conf/codex-bridge`；API=`/home/isp/wsps/cyf/api`；WEB=`/home/isp/wsps/cyf/web`。保留清单不能被误当删除清单。

| ID | 现有事实/源码 | 处置及正确接收方 | 删除条件与回归 |
| --- | --- | --- | --- |
| D01 | WEB/src/composables/juyiting/hallSkillResults.js只从ACTION_REQUEST的child EXECUTE发现结果 | 删除其作为所有新成果唯一发现前提；API提供真实原生执行引用，Web做统一关联。旧引用只作历史读取 | 直接原生结果、旧结果和刷新均可读；不伪造ACTION_REQUEST |
| D02 | API/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java的旧合同强单技能，local-file绑定local-script | 新原生入口删除基础文件执行必须有商品技能、特定runner的前提；旧v4执行/恢复分支删除，仅保留历史事实读取，不把null塞进去 | 空技能/获准多技能、跨Owner委派、载体回执测试；新接纳不落旧伪技能入口 |
| D03 | API/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatSkillResultController.java查询限定协议4 | 删除“只有协议4才有成果”的通用假设，按明确执行合同读取，保留ACL/关系及历史摘要 | 新旧结果各用正确摘要；越权/关系不完整不暴露成果 |
| D04 | RT/agent-client.mjs的bindMeasuredSkillSession将provider-operation直接绑定图片runner | 通用入口改为工具能力接线，删除把所有Provider操作等同图片及替模型决定整轮执行的入口。图片算法保留在工具适配器 | 新原生调用、图片生改、未知恢复及新增普通工具；不增加按skillKey分支 |
| D05 | RT/skill-runners/native-model.mjs固定text-file/data，并由宿主把模型JSON变成文本文件；runSkillNativeModel走只读回合 | 删除其作为新原生文件执行的生产者；模型在隔离工具中真实写文件，bridge只快照/提交。不为旧已接纳执行保留旧runner恢复 | 实际工具写文件的证据，不能用宿主预写替代；已正式提交旧成果只读；旧执行不可恢复 |
| D06 | API同服务resume有effect就不再EXECUTE，commit要求所有effect成功 | 原生新路径删除旧单runner规则的全局适用，改成通用事实与依赖核对；不把Provider流程迁入API | 已成功操作不重放、允许获准未执行步骤、UNKNOWN必需操作不假成功、已知非必需失败可保留 |
| D07 | v2.1扩展§7.2要求原生多步配方新增执行描述合同；核心实现表混入图片/浏览器/提取全链工作项 | 本版取消强制新配方runner，扩展工作项移到工具/管理交互。通用Provider调度平台是明确禁止项，不宣称既有源码已存在。E6提取步骤由模型完成 | 核心无扩展反向依赖；普通包不强制动作manifest；新增普通包无需三端核心业务修改 |
| D08 | API/Web旧源码/历史设计中的图片/费用特例、独立inspect入口线索 | 待核实当前调用方与存活入口，不能仅按旧文档整文件删。确认仍存且违反RB后必须迁移/删除，无引用直接删 | 记录当前路径和实际调用证据后进入本表；现有身份/费用购买/结算不得机械删除 |

D01–D06的新入口替代与旧接纳/执行/恢复实现删除在同一开发候选收口，不保留兼容执行器，不等待历史执行引用清空。发布切换停止旧接纳/调度并收口旧写权限，旧未完成执行明确不再支持恢复；不自动转新任务、不补传/补提交/重放。既有正式成果只读访问继续保留，历史未知操作不伪造终态。新方案自己的受控恢复照常运行。

**明确保留：**image-provider的Provider编码、输入归一化、尺寸转换、响应处理属于RB-05；它们应通过工具上下文调用，不因文件在bridge仓库就删除。执行锁/ACL/lease、effects未知保护、正式结果摘要和投影属于正确职责，不以“去防御代码”移除。当前未接入的native-artifact-snapshot函数属于RB-03快照基础，保留但不得宣称已经安全接通执行。

**退役验收：**每项记录实际删除diff、剩余调用方/引用、替代能力结果和故障恢复证据。若旧路径仍能接受新任务、恢复旧执行，或新路径仍依赖越界编排，该项不得标完成；只改目录、只加功能开关或只标deprecated不算删除。

### 2026-10-28 v3.1 实施补充：技能配置交付合同

本节落实前述用户更新，替代专用图片Provider授权出口，不增加配置UI。Runtime profile用 `skillExecutionConfigFile` 指向客户机私有JSON：`{schemaVersion:1,scope:{tenantId,ownerJiacn,clientId,agentId},installations:{"<skillInstallationId>":{configuration:{},networkOrigins:["https://service.example"]}}}`。文件必须属于实际Runtime用户、0600、真实非软链；scope与认证会话一致。仅当前command真实安装绑定可选中相应配置，不从其他安装或全局环境猜测密钥。configuration内容由技能定义，bridge不解析Provider协议。

选中配置只读交付 `/skill-config/<skillKey>.json`，环境仅给出固定目录 `CYF_SKILL_CONFIG_DIR=/skill-config`；同一执行的脚本均在同一权限域，不声称环境变量实现技能间密钥隔离。checkpoint绑定只持久配置摘要。正常suspend、进程exit和profile dispose移除临时配置文件，原执行引擎状态按既有恢复规则保留；宿主异常退出残留治理尚待验证，不作安全擦除保证。

`NATIVE_LOCAL_FILES_V1`不扩大语义；`NATIVE_SKILL_SCRIPT_V1`仅用于真实获准普通技能执行。API依据安装、task grant和权限事实接纳，Runtime按本机明确配置精确HTTPS origin允许CONNECT，保持直接外网隔离。网络配置不替代API授权。注册声明的可选 `supportedToolPolicyRefs` 仅在相应能力实测后出现；缺省不表示支持SCRIPT。API普通消息facts v6可广告真实普通技能身份（manifestSha256可null），安装ID只由API映射成v5 command的taskSkillBinding，不交由模型选择或构造。

实施与验收状态以原handoff为准：此补充与工作区源码不代表正式构建、安装或上线；精确权限语义、SCRIPT实测、图片安装及业务验收仍待收口。

### 已知引擎失败恢复补充（2026-10-28，RB-02/03/08/10）

当前候选沿既有 `conversation/failure` 和 `conversation/resume` 恢复，不新增执行状态机。resume请求仍绑定executionId/snapshotSha256，响应可空字段 `turnFailureCode` 仅表示服务端已持久的 `NATIVE_EXECUTION_TURN_FAILED` / `NATIVE_EXECUTION_TURN_INTERRUPTED`；null不推测失败原因。

- 已提交失败：resume返回 `phase=FAILED, allowedWork=[], lease=null, resultManifest=null`。bridge保存独立failure-receipt并清理匹配引擎；不得因为lease为空而重新claim，亦不得制造成果清单。身份、任务、Agent、授权、代际、snapshot仍由API核对。
- 本地已知终态而失败响应丢失：重建时先resume；服务端尚未收到事实时按既有互斥恢复租约，只用新fence重报原终态，不进入模型。旧runtime的fence不能跨实例复用。
- 已记录终态而已登记effect未决：resume为 `RESULT_UNKNOWN`、仅 `QUERY_EFFECT`，包含原turnFailureCode；允许依既有failure入口幂等收敛，仍未决就保持UNKNOWN，不生成新effect/结果或重新执行脚本。API对未登记脚本远端副作用不作成功/失败推断。
- 服务端与本地终态code冲突、未知code、非FAILED却缺租约：拒绝当前执行恢复，不改写本地事实、不借新claim绕过。该校验防止错误恢复造成重执行或伪终态；入口为Runtime `test/skill-conversation.test.mjs`、API `SkillExecutionServiceTest` / `ConversationLeaseWireHttpTest`。

这是候选合同和局部实现记录，不是Java类型编译、事务或真实HTTP验收证明；正式验证仍走现有Flow。

### 2026-10-30 材料读取事务修正（RB-02，已实现；生产修订E2E待验）

依据生产2026-10-30 01:17:45事项547/绑定1死锁及API基线f932d38，材料读取必须与原生WS变更保持同序：installation → binding/identity → runtime → task。`incomingTurn`内部也会锁任务并重入绑定，不能在身份fence之前调用。

- HTTP安全边界通过既有`withNativeFence`包住材料服务的`prepare`和`revalidate`两段短调用，认证实现不下沉业务服务；业务服务只接收既有可信Scope，定位turn、校验任务/材料授权并生成不可由HTTP构造的私有字段`Prepared`。不传Spring Authentication到应用服务，也不为跨模块服务依赖增加分层例外。
- 事务退出后读取文件，再以相同锁序进入第二个短事务核验Runtime身份、turn、任务权限及冻结输入。失效即不交付字节；不改ACL、放宽摘要校验或自动重放。
- 不给整个材料读取方法加外围事务，不让文件I/O占用Runtime/任务锁；不为此全局重排任务授予事务。
- 二进制Accept请求发生错误时，API明确返回JSON Content-Type和原错误状态，避免错误协商再次遮蔽失败。内部异常仅记录类型/代码位置，不记录密钥、文件内容或异常消息。
- 回归入口：`AgentMaterialsErrorHttpTest`（HTTP）、`ChatMaterialsFenceTest`（前后授权/撤权/I/O边界）、既有`skillManagementWire`中的`ChatMaterialsLockOrderMySqlTest`（私有MySQL并发，最小SQL身份/DAO适配器）。这些不是完整生产WS鉴权E2E；正式Flow/安装/线上验收另记handoff，不因补充详设宣称已修复上线。

核对基线：API `aa87ca4f049eaf90bff2c97934069d156adbdde1`，2026-10-30 Flow5260799/401已通过上述HTTP6/授权6/私有MySQL1及分层/freshJAR，主机已独立安装并核对摘要、健康和既有图片下载。此证据覆盖材料接口锁序/错误响应修复，不覆盖新的生产同会话修订或默认改图Provider全链；发布及限制见既有`CODEX-NATIVE-SKILLS-20261027.md`末节。


## 2026-10-30 核验补充：普通 typed CHAT 的持久完成边界

核对源码 Runtime `66e896f0238d411d364b1e03d1d722e7ed2889ef`（tree `9998234790df6a8a3d03e9f491f474502ae8fd89`），覆盖普通 typed CHAT 最终结果，不改变材料 CHAT、API 完成权威或模型业务编排。RB-02/08/10。

- `action-chat-final.mjs` 在发送前持久化原结果，绑定 request/turn/dispatch/Owner/上下文摘要及 outboundMessageId。WebSocket 发送成功或本地模型结束不等于 API 已保存。
- 收到既有 `agent_message_saved` 对应保存回执后，才将该本地 CHAT 归档完成；接收前发送失败/重连只复用原结果与消息身份，不重新调用模型。复用现有 inbox 恢复调度，不新增任务引擎。
- 摘要或绑定变化只拒绝当前不一致结果；旧已归档且没有 prepared final 的任务不补造结果、不自动重放。实际风险为模型已结束但最终消息未持久确认，导致 API 长期 STREAMING；并非所有历史 STREAMING 均可归因于此。
- 回归覆盖发送失败/异常、进程重载、自动恢复、回执先到/重复及跨绑定拒绝。Flow5264702/101：744通过、7跳过、0失败；生产新 task557 的 prepared final 已获保存确认，三个文件成果 RESULT_COMMITTED。完整发布及验收证据见既有 handoff 2026-10-30 收口节，不把此定向验证等同 Office/浏览器完成。

## 2026-11-03 增补：CHAT流式正文用途（展示元数据，非执行授权）

本增补仅改变议事CHAT增量展示；不改变最终outcome v5、原生执行合同、完成事实或授权。责任层为RB-03解析引擎结构化流，RB-02接纳/持久化转发，RB-01展示。实现与验证进度见 `docs/implementation/handoffs/DISCUSSION-RETEST-20261102.md`，规格不代表发布。

- `chat.message.delta`及对应已持久化`agent_message_delta`增加可选字符串`streamOutcomeKind`，值仅为`ANSWER`或`CLARIFY`。每个可见增量携带同一明确类型；不是新的`typedOutcome`、不是执行/收费/成果完成授权。
- bridge从同一次模型生成的**顶层JSON kind**完整值识别用途，只流出ANSWER/CLARIFY的顶层text。嵌套字段、自然语言、关键词、操作名称不作为识别依据；不另调分类模型。kind在text之后时先缓冲，类型确定后放行已缓存用户文本；未知用途和ACTION_REQUEST/REVISION_REQUEST/SUBMISSION_REQUEST等控制类型不发可见文本delta。不能承诺所有字段顺序都在首字前获得类型。
- 未知/不完整流等待最终结果。final仍完整校验并提交，已观测类型与final不一致或已发前缀被改写沿现有协议失败路径处理，不能据临时类型执行操作。这里只保证协议用途隔离，不声称能够语义识别模型误标的每句话。
- API复用已认证Agent身份、dispatch/turn/context绑定及deltaSeq，接纳枚举后原样持久化此字段；包含字段时幂等摘要绑定`[streamOutcomeKind,content]`，缺字段保持旧正文摘要算法，无表迁移、不重分类。非法用途只拒绝对应delta，不重写final；不因缺字段拒绝旧Runtime。
- Web仅当同一turn所有已接收连续delta都具有同一允许类型时提前显示；缺失/未知/冲突字段不把已有缓存反向升级为可见。其他turn与会话隔离、缺号恢复、重复/迟到处理不变。最终权威消息替换临时消息，不追加重复答复。私聊普通流不加此用途门槛。
- 混合版本：新Web+旧API/Runtime等待final；新Runtime+旧API字段可能被忽略，也等待final；旧Web保持原显示逻辑。新Runtime不再向这些链路发送操作指令delta，final原文只读存档不删除。安装顺序推荐API→Runtime→Web；实际部署及授权另记。
- 风险/验证：正文提前外泄在bridge阻止、序号重放用途篡改在API摘要绑定、缓存混合在Web展示层处理；用既有decoder/runtime、服务与handler、Web消息投影测试覆盖，不新增跨层重复语义审核。
