# 聚义厅智能推荐承办 R1

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：单次模型推荐与用户显式确认承办。**
**文档与交付状态：** 本专题已有历次部署与候选记录，最后模型投影说明不等于业务/性能验收通过；不重复执行旧部署。

### 责任与业务流程
API提供授权候选/版本事实；模型做逐人评价；API校验引用并投影；Web保持推荐顺序和用户选择。

读取事项与最小候选证据→一次无工具模型调用→逐人等级/理由→页面展示→用户确认；报价扩展按文钱包合同。

### 明确边界
不增规则评分/额外报价模型/业务自动重试/自动派单；旧候选子集不覆盖完整逐人评价；手选仍经原授权。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
候选遗漏/重复/跨候选证据、事项变化409、无候选与无匹配不同、无害字段兼容、页面请求合并/迟到结果隔离；模型效果与静态Prompt测试分开。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->

<!-- 阅读路径：本文唯一生效合同 = 上方「现行规格」摘要 + 「现行合同正文」 + 「必要校验与失败范围」表 + 标 [现行] 的节；标 [历史]/[历史证据]/[候选未部署]/[部分部署] 的日期节仅供溯源，不构成当前可执行要求，冲突以现行合同为准。 -->
## 现行合同正文（2026-11-07）

2026-10-28；任务 JYT-MODEL-RECOMMEND-20261028；实施合同；推荐已随后续API381/Web377上线，真实推荐503；2026-10-30已撤回鉴权401归因，定位参数类型ClassCastException，修复已合develop bb1b744956，轻量SDK HTTP smoke及共享Flow401推荐相关19项回归通过，401整轮SUCCESS；共享401已安装并健康；真实事项552返回502，同类诊断复现无证据候选被推荐。第二轮修复已合develop16a769bd72，Flow402完整构建及推荐相关32次测试执行通过，主机已安装1.1.4-SNAPSHOT且health UP/摘要MATCH；真实事项554一次请求200/READY，推荐吴用并显示图片生成经验依据及缺口，未指派/执行，验收事项已取消。历史构建/发布阻塞见handoff。

单轨升级 `POST /agent/tasks/{taskId}/recommend`，公共信封遵循API统一规范v1.4。无第二套推荐、无旧数组兼容。团队推荐/自动指派属于其他用例，本次不改变。

请求data：`expectedTaskVersion`（当前服务端任务版本字符串）。
响应data：`taskId, taskVersion, observedAt, state, requirementSummary, recommendations, questions, candidateSetComplete`。
**2026-11-01逐人评价合同（22:07已授权部署API423/Web392；安装、健康及线上资源摘要核验通过，真实模型语义效果未抽测）：**
state：READY至少一位HIGH/MEDIUM；NO_MATCH所有候选均为LOW/UNKNOWN，但仍返回逐人评价；NO_CANDIDATES只有候选集为空时返回，recommendations为空。questions固定空数组，不要求补充需求。
每个recommendation：`agent`（agentId/name/status/abilities/canOperate/boundToMe/providerDisplayName）、`recommendationLevel`（HIGH/MEDIUM/LOW/UNKNOWN）、`reason`（面向用户的简短理由）、`evidence`（服务端投影依据）、`gaps`。recommendations覆盖当前授权可选Agent，每人恰好一次，不再只返回模型认可的子集。全部候选及其允许披露的能力信息在单次请求交给模型；无公开依据的外部候选也评价为资料不足，不读私有能力。
推荐度由模型直接判断，不是概率或服务器打分：高=关键能力明确适配；中=基本适配但有局限；低=已有信息不匹配；资料不足=不能合理判断。离线/忙碌说明等待，不等同低能力。通用整理、归纳、一般分析、简单统计不拆成每步专用技能门槛；图片成绩统计应优先推荐有识图/图中文字读取用途的候选，不要求专用成绩统计技能，不能将仅生图用途虚构为识图。
证据：`id, kind, label, description, available`。本领是声明，技能是用途经验，不证明未报告的依赖或最终结果；普通的不保证提示不应机械否决全部候选。
模型返回agentId、recommendationLevel、reason、evidenceIds、gaps、questions、requirementSummary，不返回Agent完整对象。API从当前候选组装结果、据等级汇总state，不二次评分。现有候选权限/资料归属/快照409不变。
必要校验及失败边界：未知/重复候选、遗漏输入候选或未知评级会破坏完整评价语义，整次502；引用必须属于该候选且available=true，防止伪造/借用依据；HIGH/MEDIUM/LOW须有引用，UNKNOWN可空引用。无依据不强行填写正面评级。非空questions仍为502。回归入口ServiceTest/ControllerTest/ModelTest及Web recommendation/component-behavior/task-presentation；无新通用门禁。
Web每张卡展示等级和理由，高/中优先但不自动指派，低/未知可手选、不默认选中；地图只标记高/中。等待采用转环与普通文案，保留原请求合并与禁用操作；需求理解默认折叠，移除底部独立刷新图标，保留重新推荐及错误展示。正常议事澄清不变。

**2026-11-01 后续精简上线（API efcb87549d / Web 7b44dec766，23:12已部署API424/Web394，安装及线上技术核验通过）：**
- 待确认承办正常态移除推荐完成摘要、需求理解、能力依据、重新推荐区和通用交办说明；移除全部/我的/外部筛选，展示完整候选卡片及确认操作。LOADING保留动态提示和选择/确认禁用；ERROR/STALE保留简短提示和显式重试。其他费用/资金规则、候选加载分页与权威空态不变。
- 模型根据agent.boundToMe识别自有归属；在HIGH/MEDIUM均满足关键需求的候选中，自有优先于外部，各组内再按适配程度；LOW/UNKNOWN自有候选不得压过合适的外部候选。不因归属抬高评级，不漏外部候选。recommendations数组为模型推荐顺序，API沿用原顺序、Web删除评级二次排序并按返回顺序展示及默认选取首个HIGH/MEDIUM，不自动指派。
- wire字段与校验、ACL/快照保护不改，无额外模型调用或代码硬编码归属打分。ModelTest覆盖Prompt规则；Web recommendation/component-behavior覆盖顺序保留、自有MEDIUM先于外部HIGH、外部HIGH先于自有LOW、精简界面及加载/重试/手选/空态。真实模型语义效果另验，不将静态Prompt断言视为效果证明。

错误：400 BAD_REQUEST；401 UNAUTHENTICATED；404 RECOMMENDATION_NOT_FOUND；409 RECOMMENDATION_STALE（事项/候选变化）；503 RECOMMENDATION_UNAVAILABLE；502 RECOMMENDATION_INVALID_RESULT。无成功空数组伪装错误。
模型一次正常调用，无工具/记忆、无业务层自动重试、不执行/扣费/派单。provider传输沿现有无重试配置。不开新收费链路；真实模型联调费用归属待核验。
模型输入为任务标题/描述/本领要求、最小候选证据以及当前ACTIVE INPUT/REFERENCE关联资料元信息（2026-10-31用户增补）。资料包括名称、关联版本原文件名/MIME类型、版本、用途和文件状态；不以当前最新版本或文件mediaFamily替代关联版本。summary当前为null：权威工作空间模型尚无摘要字段，不编造摘要，也不宣称已支持摘要采集/存储。未来存在权威摘要来源时再接入，不能把文件名当摘要。
不读取正文/预览、不发送存储路径/下载URL/身份或哈希、不新增模型调用或历史成果查询。不限定资料类型，不设置类型/后缀到技能的映射。模型根据资料名称、原文件名（含后缀）、已有摘要和任务目标自行判断所需能力，MIME仅作辅助；不能声称已阅读附件内容，也不能把相关但不同的能力视为等价。按2026-11-01目标修订，利用原始文件名后缀/组合后缀（大小写无关）、名称和MIME推断格式，再结合任务目标判断操作并匹配技能用途；冲突/未知格式不伪装确定。简短描述主动结合资料线索判断，非关键未知在gaps说明但不变相要求补充；关键证据不足返回NO_MATCH，不强行推荐。
资料读取复用既有工作空间服务权限；分页完整读取关系及确切历史版本。关系解除、资料重命名、关联版本或元信息变化会使推荐过期（409 RECOMMENDATION_STALE），防止返回对旧输入的建议；缺失确切版本同样409，不用最新版本补齐。读取失败不当作无附件，模型不调用。回归入口RecommendationMaterialsTest、AssigneeRecommendationServiceTest、AssigneeRecommendationModelTest；未读取内容、不开放工具或执行权限，公共推荐HTTP合同不变。

Web按任务版本、身份隔离请求，合并同一在途调用，不自动轮询或失败重试。页面重新进入可重新推荐；缓存只保留当前页面观察结果。推荐失败与无候选区分；手选不依赖推荐成功、不冒充推荐。确认仍走原承办授权/幂等链路。

校验和回归见handoff。本特性不新增SLO拒绝、DAG、向量库、审批、DDL或Runtime协议。必要验证在本地固定候选执行，当前源码结果不等于上线。

离线/忙碌不作为普通事项推荐的硬淘汰条件；服务端附加等待提示，是否能受理仍由现有委派接口核验。外部提供方名称仅使用公开候选摘要。

## 必要校验与失败范围（2026-10-28）

| 风险/条件 | 处理范围 | 实现/回归入口 |
| --- | --- | --- |
| JWT、租户或Owner上下文不一致；事项不可访问 | 当前请求401/404，不读取候选/调用模型 | AssigneeRecommendationController / ControllerTest |
| 事项版本不匹配，推理期间事项或候选事实改变 | 当前推荐409；不据旧观察派单 | AssigneeRecommendationService / ServiceTest |
| 模型伪造候选、跨候选引用或引用不可用证据 | 当前结果502；不用规则评分替代 | Service.decode / ServiceTest |
| 评级未知、候选遗漏/重复、非空questions或非结构化JSON；Web状态与评级不一致 | 当前结果502；允许无害新增字段 | ServiceTest / juyiting-assignee-recommendation.test.js |
| 默认模型带工具，或输出工具调用 | 默认工具503、输出工具502；不接入ChatClient/工具Advisor | AssigneeRecommendationModel / ModelTest |
| 候选分页游标重复 | 当前请求失败，不将部分候选冒充全集 | AgentServiceImpl.listTaskAssigneeCandidates / AgentServiceImplTest |
| 浏览器身份/事项切换，旧响应晚到 | 取消本页旧请求并丢弃结果，不改新身份状态 | useHallData / juyiting-hall-data.test.js |
| 模型或传输失败 | 当前推荐明确不可用；无业务层自动重试；手选仍需明确确认 | ServiceTest / juyiting-flow-ui.test.js |

旧AgentTools.recommendTaskAssignees入口同步删除，不保留调用已删除Service方法的工具。旧DTO仍被团队推荐和自动指派使用，不为本次单人推荐改动删掉这些其他用例。

## 待确认承办详情纠偏（2026-10-31）
- 推荐刷新由Web先读取权威事项详情再发起一次推荐，连续点击合并；失败不自动再次调用模型。身份/事项切换取消原读取和推荐，服务端RECOMMENDATION_STALE保护不变。
- 手选候选与模型推荐是独立事实。无推荐、需补充、过期或模型失败不等于无人可选；只有当前事项候选成功读取、列表为空且无下一页才可显示招贤空态。读取失败/加载中不下无人结论，所属筛选空态不影响全集结论。
- 沿用唯一原型的内联候选卡与全部/我的/外部筛选。推荐读取/判断时展示动态状态并禁用改选与确认，避免结果切换导致误操作；筛选不清空显式选择。
- 回归入口：Web tests/juyiting-assignee-recommendation.test.js及tests/juyiting-component-behavior.test.js。不改API/Runtime契约、Prompt或模型配置。实现、Flow及上线结论以现有handoff证据为准。

## 2026-11-01 承办候选渐进展开

- 待确认承办：有合适推荐时默认显示「推荐承办」、姓名、所属/状态及推荐理由，候选列表默认收起。不恢复需求理解/证据面板/归属筛选。理由沿用模型原文，自然换行，不编造或截断关键信息。
- 「更换承办人」展开候选，展开入口改为「收起候选列表」。选择任意可承办候选后自动收起，焦点回到入口；上方改为「已选承办」。选择不发送请求，仅点击「确认由{姓名}承办」才确认。长姓名和理由可换行，移动端不溢出。
- 无HIGH/MEDIUM合适推荐时不预选，直接展开列表，显示「请选择承办人」；LOW/UNKNOWN仍可手选。无候选空态只采用权威查询结果，加载/错误不得当作空态。
- 等级文案：HIGH优先推荐，MEDIUM可以考虑，LOW匹配较低，UNKNOWN资料不足；接口枚举和模型排序不变。
- 加载初始收起，推荐到达后按是否有合适推荐决定默认状态；用户主动展开保持展开。加载/发送期间保留禁用与重试。身份、事项或版本变化清除选择与展开偏好，失效选择不指派。
- 离线原型入口index.html?scenario=assignee-recommendation#detail；覆盖READY/LOADING/NO_MATCH/NO_CANDIDATES/ERROR/STALE、390px与1440px。原型通过不等于产品上线。

状态（2026-11-02核对）：原型、规格与Web已实现并合develop 9a4e8b195b551af2b7e44797b29c8e7379c6f2e2（1.16.87），Flow4403172/396正式回归/构建通过；2026-11-02后续用户授权安装，同Run制品安装及612个文件/公网入口与聚义厅资源核验通过。证据：evidence/evidence-collapse-recommend-20261102.json；API/模型排序未改。
