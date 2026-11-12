# 原生执行详设 v2 复核：规格、源码与模拟

> 本文为v2.1历史设计复核；当前实施入口已更新为[RB-1职责规格](responsibility-boundaries.md)和[核心详设v3](native-execution-technical-design-20261027.md)。旧发现与测试结果保留，不代表v3验收；关于强制原生配方runner等目标以v3为准。

日期：2026-10-28（Asia/Shanghai）。Owner：本聊天主Agent。
结论：原方向可保留，但v2有8项缺口/需要细化的边界，已修订为v2.1；私有技能归属与删除/保留语义已于2026-10-28获用户确认（§4）。不是产品代码修复、发布或完整安全审计，也不能证明所有遗漏已消除。

## 1. 核对范围与证据强度

- 规格：统一接口v1.4、现有skill-execution spec/design、management-contract末节兼容及2026-10-26简化权限/依赖要求，以及本聊天3份原生设计。
- 源码：Runtime executor/store/lane/registry/manifest/typed profile/adapter；API平台包发布、执行resume/commit、用户结果查询；Web成果发现、投影及下载预览。
- 固定本地四仓HEAD/tree仍与原handoff一致，但工作区有既存脏文件；本次测试的是读取时实际文件，不把HEAD当受测字节。`input-manifest.json`记录源码/规格SHA-256；未fetch、未查询生产版本。
- 外部Runtime仅只读及轻量测试，已读取其AGENTS并沿CYF规则；不修改外部仓库、不启动Flow或服务。
- 官方搜索/页面工具未返回有效正文；Codex判断采用本地真实发现探测，不编造官方文档引用。

证据根：`/home/isp/wsps/cyf/specs/juyiting-skill-execution/evidence/design-review-20261028/`。

| 类型 | 结果 | 能证明 / 不能证明 |
| --- | --- | --- |
| 既有Runtime 4文件定向测试 | 54/54通过 | 现行命令、结果、effects、恢复及registry模拟边界；非Java真实HTTP/数据库验证 |
| 新增直接调用源码的反例探测 | 10/10通过 | 现行代码确实拒绝/接受所测输入；不是新原生功能已实现 |
| 新增设计/源码派生状态模拟 | 7/7通过 | 复现简化旧规则的反例、验证修订逻辑方向；不是生产状态机实现测试 |
| 真实系统app-server只读发现 | 发现工作区repo技能及system技能 | Codex CLI0.164.0实际发现范围；没有thread/turn、模型或Provider调用，不证明生产引擎/执行能力 |
| 文档检查 | 导航及新增文档结构检查 | 非应用构建、上线或完整协议验证 |

合计71项本地检查通过（54+10+7），另有一次真实发现探测。首次新探测fixture多传一个根级taskId造成2项失败，已去除该fixture错误；不是产品修复。首次日志保留为`design-counterexamples-attempt1.tap`，最后结果为`design-counterexamples.tap`。第一次证据清单脚本因本机Python3.6不支持subprocess text参数失败，改用universal_newlines后生成；不影响受测源码。

复现入口：

```bash
node --test --test-concurrency=1 \
  /home/isp/wsps/chcbz/isp-install/conf/codex-bridge/test/skill-executor.test.mjs \
  /home/isp/wsps/chcbz/isp-install/conf/codex-bridge/test/skill-execution-store.test.mjs \
  /home/isp/wsps/chcbz/isp-install/conf/codex-bridge/test/skill-conversation.test.mjs \
  /home/isp/wsps/chcbz/isp-install/conf/codex-bridge/test/skill-registry.test.mjs
node --test --test-concurrency=1 /home/isp/wsps/cyf/specs/juyiting-skill-execution/evidence/design-review-20261028/design-counterexamples.test.mjs
node /home/isp/wsps/cyf/specs/juyiting-skill-execution/evidence/design-review-20261028/skill-discovery-probe.mjs
```

最后一项会创建并删除自己的临时Home和自有app-server进程；不得拿生产Home或其他进程替换。证据脚本使用合成身份、合成技能/文件，没有真实凭据。

## 2. 发现与修订

### R1 / 高：只挂载获准Home技能，并不能限制引擎的全部发现来源

- v2缺口：授权包逐个ro-bind后默认实际技能集合受控；未覆盖cwd/祖先/系统发现根。
- 事实：`skill-discovery-result.json`中，原先只有audit-approved及system技能；添加工作区`.agents/skills/audit-untrusted-workspace/SKILL.md`后，真实skills/list返回scope=repo、enabled=true。
- 风险：附件解压/临时脚本形成的目录可能作为技能说明被发现；发现不等于已获得工具权限，但会污染受信说明来源。不能把探测扩大宣称为已证明越权执行。
- 修订：核心§5.3，线程cwd固定只读中性根，工作文件与发现根分开；实际扫描根/插件配置按固定引擎治理，初始化/刷新/恢复核对发现集合。system技能单独固定清单，不自动授予安装/网络能力；纯文本/无附件原生任务也必须隔离。
- 验收待办：生产候选真实sandbox中的发现范围及动态刷新、配置/祖先路径、原生shell权限；本轮未运行模型。

### R2 / 高：私有提取包不能直接套用平台商品发布和旧runner

- v2缺口：仅写“复用现有技能管理安装”，漏掉普通用户私有来源及原生配方执行描述的接纳路径。
- 源码：`/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/skill/SkillPackagePublicationService.java`的publish要求platformAdmin，persist限定PLATFORM商品；现行TaskSkillBinding必需productVersionId。Runtime manifest-v1只有三种runner；说明型包是INSTRUCTION/NOT_EXECUTABLE。
- 反例：新探测确认缺productVersionId或虚构native-agent runner不能通过旧解析；既有registry测试确认说明包不产生可执行能力。
- 修订：扩展§7.2，新增Owner私有来源/版本登记与受管安装来源联合，复用现有安装/恢复而非假商品/假订单/提权发布；新增明确原生配方合同，旧INSTRUCTION和旧runner语义不变。依赖准备与业务验证分别记录，不能因提取成功伪造READY。
- 产品语义已确认：私有所有权/跨有管理权Agent使用范围见§4；API/Runtime实际DTO和持久结构在实施固定，现有接口尚不能完成该闭环。

### R3 / 高：后端有成果，不等于Web能发现原生执行成果

- 源码：`/home/isp/wsps/cyf/web/src/composables/juyiting/hallSkillResults.js`仅接受ACTION_REQUEST→child EXECUTE派生引用；`ChatSkillResultController.java`存在协议4条件。新直接执行不自动出现在旧列表。
- 反例：旧action fixture能发现1项，直接结果对象发现0项；Web对未列字段拒绝。MP4无previewUrl可下载，有previewUrl则被当前inline MIME规则排除。
- 修订：核心§9.5；后端在既有request/step/execution关系持久原生执行引用，Web按新合同发现，不伪造ACTION_REQUEST或扫描最新结果。结果查询、精确字段、视频预览同步改造，保留旧历史。
- 状态：设计已修订，Web/API产品代码未改。

### R4 / 高：单runner恢复规则不能直接支撑多步原生续执行

- 源码：`/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`的resume在已有effect、无manifest时仅给QUERY_EFFECT/RECOVER_LOCAL_RESULT；Runtime mayStart要求EXECUTE。
- 反例：完成一个effect后重启，即使全部已知SUCCEEDED，后续新步骤也得不到EXECUTE；仅用新turn/toolCallId去重又可能把原未知付费调用当新操作。
- 修订：核心§11.2；原生续执行授权要明确到恢复步骤/允许的新操作，逻辑operationId独立于引擎调用ID，UNKNOWN不通过换ID绕过。旧v4整体恢复不放宽。
- 状态：源码派生/设计模型反例成立；未实现新续执行协议，不宣称重连已可完成多步视频。

### R5 / 高：返回jobId只是异步提交成功，不是视频任务完成

- 源码：当前SkillEffects.invoke将正常返回value持久为SUCCEEDED。
- 反例：真实类收到`{jobId: job1}`后report状态为SUCCEEDED；简化“turn完成+effect成功”条件会错误允许业务仍RUNNING的任务最终交付。
- 修订：扩展§5.4；提交effect与异步业务操作分离，持久jobId/operationRef和查询恢复位置；只有业务完成及真实文件验证才能满足交付依赖。现有Runtime恢复调度承担查询，不新增常驻队列或Flow等待。
- 状态：现有机制可复用但不够，不宣称外部服务严格exactly-once。

### R6 / 中高：探索允许明确失败，但现有commit要求所有effects成功

- 源码：同一API commitResult逐项要求effects.status=SUCCEEDED；Runtime对invoke抛错统一UNKNOWN。
- 反例：非必需步骤确定失败后成功完成替代方案，旧全成功门槛仍拒绝提交。不能把这个门槛直接全删，否则未知付费操作被隐藏。
- 修订：核心§11.2；区分未发送/明确失败/结果未知，原生清单关联必需操作与明确未交付项，确定失败的非必需探索可保留事实后继续。必需操作UNKNOWN或仍执行不能报告完整成功。旧v4状态语义原样保留。
- 约束：不是新增通用DAG框架；只记录当前执行步骤/成果关系。费用仍遵守现有“不加运行预算审批”规则。

### R7 / 中高：动态下载/部分材料失败不能硬塞进原输入回执

- 源码：validateSkillInputReceipts和API commit要求冻结inputs与DELIVERED回执一一对应；local-file只允许local-script。
- 反例：缺少一个回执、多出下载材料引用、native-model使用local-file都被当前校验拒绝。
- 修订：核心§4.4；新原生合同区分完整来源清单/交付事实/必需材料/派生材料，追加派生记录而非改写原snapshot。部分结果必须说明缺失；新下载数据外发另受原任务授权，不从下载成功推导权限。
- 状态：合同设计修订，既有摘要不改写；API/Runtime需同步实现。

### R8 / 中：提案、终态和来源留存需补足崩溃恢复边界

- v2不足：规定“回合completed后冻结”但没有说终态事件丢失、提案落盘与晚到工具事件如何协调；来源清理与当前ACL也需具体处理。
- 修订：核心§7.2增加proposalRevision/选定文件/原turn与工具关闭事实的持久关联，最终冻结与候选接纳互斥；终态证据不足先reconcile，不从最终文字或文件存在推断完成。C5保留可验证脚本版本和不完整标记；提取前及继续处理时复核当前ACL，候选不得携带凭据或其他Owner资料。
- 证据：快照修改隔离和跨Owner提取是设计模拟；并未实现新成果工具或真实filesystem竞态测试。此项为审阅发现的未定义边界，不伪称现有生产漏洞已复现。

## 3. 已有设计合理、但仍是实现改造的部分

- 现有本地结果→文件stage→manifest commit→resume读回→receipt链条可以复用，现行54项测试支持其模拟故障边界。
- 草稿和可信blob隔离、结果hash冻结、ARCHIVING与COMPLETE分开，方向正确；不是将模型“完成”字符串变成业务事实。
- 已写出的16MiB/非空/整文件内存路径问题，经源码探测再次确认，但属于已有v2待改项，不重复计作新缺口。
- 现有hash preimage不含displayName，新元信息需明确绑定方式；本轮直接调用skillResultPayload确认，不得改写历史hash。
- 固定挂载技能/依赖、按引用回收、既有图片算法复用、核心与扩展单向依赖仍保留。

## 4. 用户已确认的两项产品语义（2026-10-28）

### Q1 私有技能的归属和安装范围

已确认：提取技能属于当前用户的私有版本，默认安装到当前有权管理的Agent；若当前是他人/共享Agent且用户无管理权，则只保存私有候选，不擅自安装。用户其他有权管理的Agent可另行安装。默认不公开、不进入市场、不赋予其他用户访问权。保存、安装、公开分享是不同动作。
用户已同意按此默认规则执行。该决定影响私有来源ACL、命名空间和管理列表，不代表相关接口已实现。

### Q2 删除原会话/任务后，已保存技能是否独立保留

已确认：已保存的脱敏技能包独立保留到用户删除；原视频/图片/账号/会话正文不随包复制。源证据沿既有任务资料保留规则，删除后来源标不可用，不能再声称可从原脚本重新提取；如存在隐私/权利撤销要求，按明确资料规则处理受影响包，不以独立保留绕过删除授权。
不设置永久源会话留存或固定天数。该决定影响源资料删除、候选引用、已保存版本及来源展示。

## 5. 尚不能由本轮检查证明的事项

- 生产固定app-server的原生工具、MCP配置及所有技能/指令发现根，真实sandbox下的目录/凭据/网络边界。
- 无技能新合同、私有包来源、原生续执行、异步operation、artifact/propose工具尚未实现；不能靠模拟宣称兼容已经打通。
- 未跑Java/MySQL HTTP集成、浏览器UI端到端、真实图片/视频服务；正式重型验证沿既有Flow且每Run<=600秒，部署仍需授权。
- 未为本轮新增常驻服务、权限审批层或任务预算；未改其他任务脏文档/源码。稳定规格原文件只读，待实施将本次差异同步到既有管理合同及消费者，不把详设新增条款冒充冻结wire。
