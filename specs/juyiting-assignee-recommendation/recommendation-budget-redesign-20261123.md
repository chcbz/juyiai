# 推荐承办与费用预算：非生成式检索、实测样本预算详设

- 日期：2026-11-23。
- 状态：**2026-11-23第二轮评审4项问题已修订并在设计/文档层闭合，Owner定向回读通过，见§11.7。** 前轮独立评审/U1续审及本轮初审结论保留，不冒称此次新增独立评审签字。业务代码、迁移、完整性能/效果测试和发布未完成。
- 责任入口：[推荐主spec](spec.md)、[文钱包主spec](../agent-economy-marketplace/spec.md)。公共接口沿[统一接口规范v1.4](../../api/docs/interface-standard.md)，公共信封protocolVersion仍为1。
- [取代：原单次生成模型推荐、模型估计整任务token、推荐接口内同步报价、推荐场景禁止规则排序/新增索引/Runtime改动]。保留候选权限、完整逐人呈现、固定报价/预占/结算/释放和原业务幂等，不扩成全项目重构。

## 1. 已确定的范围

1. 推荐不调用生成式大模型；Embedding使用既有Spring AI入口，统一选OpenAI `text-embedding-3-small`、1024维、网关 `https://codex.chcbz.net/v1`。不用智普替代，不新增CPU编码进程、Ollama或独立推理服务。
2. 新能力索引与聊天记忆索引隔离。**不删除、重建、重编码`chat_memory`及其实际索引**。全局切模型后旧记忆向量与新查询向量混用的质量风险已由用户接受；同为1024维不代表语义空间一致。
3. 推荐与预算两个请求、两个页面加载状态；不保留旧客户端分支，不增加`includeQuotes`，不暗中回调生成模型。
4. 测试历史可清理，但范围仅本次推荐/报价/执行成本关联数据；账号、资料、聊天和旧记忆索引保留。没有有效用户不等于允许破坏钱包账本或扩大为全库重置。
5. 预算冷启动使用获授权的真实基准执行，随后使用完整实测历史；付费基准执行仍需成本授权。本轮不调用付费执行、不切生产配置或删除数据。

## 2. 已核实事实与证据边界

| 事实 | 已检查的落点/结果 | 对方案的约束 |
| --- | --- | --- |
| 推荐现状 | `AssigneeRecommendationService`观察候选/资料后调用`model.judge`；`AssigneeRecommendationQuotes.prepare`在任务根事务中逐候选报价 | 删除生成式推荐依赖及内嵌报价；检索和估算移出任务锁 |
| 候选查询 | Agent候选和技能推荐链存在逐人Runtime/权限查询；已有局部缓存不等于整条链批量化 | 在原责任服务补批量读，不让调用方另造ACL过滤 |
| 资料 | `RecommendationMaterials`读关联的确切版本元信息；没有正文/OCR，summary为空；版本视图有byteLength | 只用可核实文本/类型/大小特征，不把字节数当token数或宣称读过附件 |
| 报价现状 | `TaskWorkload.estimate`固定`MODEL_TOKEN_ESTIMATE/1`；数据库按Runtime executionModel选价，工具按每交付物静态单位数算 | 新估算来源须换真实provenance；不能仅替换输入仍标模型估计 |
| ES部署 | 只读探测9.3.0、Basic、单节点、256MiB heap；`chat_memory`别名指向`chat_memory_v2`；候选范围内script_score探测成功；原生RRF返回许可证403 | 采用API侧RRF；小规模精确向量检索，不新增向量库或扩大heap |
| Embedding部署 | 仓库dev/grey已选OpenAI small/1024；仓库prod及此前核实的安装JAR仍是独立智普embedding endpoint/model；外部配置有独立embedding加密密钥 | 生产要同时核对endpoint、model、维数及凭据；不能只改源码model |
| 网关延迟 | 成功重试1024维耗时4260ms；随后同输入顺序三次OpenAI1946/899/1386ms，均200 | 只是连通性小样本，不是P95、并发能力或质量证明 |
| 旧成本 | 此前只读聚合中256条原生执行证据、339条聊天执行证据均待用量；已结算且有成本记录的61项均不完整 | 现有历史不能作为“完整任务成本”基线；数值是观察时快照 |
| Runtime接收 | `app-server-usage.mjs`明确将last/total保留为UNVERIFIED；adapter覆盖保存最后一个usageEvidence | 禁止差分累计值或将最后一次用量当整任务用量 |
| 上游来源 | 两个运行进程核实为codex-cli 0.167.0；两个现有会话均实际有token_usage_record | 证明来源存在，不证明全部原生任务及异常覆盖 |
| 清理生命周期 | `agent-client.mjs`的onCommitted/onFailed调用releaseAdapter；`isolated-engine-profile.mjs`默认删除engineState目录 | 必须在释放目录前转存用量；不能依赖日后扫描已删除的rollout |
| 资金与重放 | 取消事务调用billing.release；STOP经事务后路径；usage delivery独立重试；UsageCostServiceImpl可重新插入attempt | API取消成功不等于生产者停止；不得单独清空cost表或Runtime receipt |

本地详细调查材料：`/home/isp/tasks/cyf-embedding-openai-20261123/official-usage-audit/`与`industry-reference-audit/`。源码核实基于当时工作区（存在其他任务脏修改），不是新候选的构建/发布证明；实施时重新固定commit/tree及必要输入。

## 3. 推荐承办方案

### 3.1 数据及责任

- **Agent服务**负责当前可披露候选、技能/安装/授权事实与任务版本。批量读取沿原服务实现，不把所有权/租户检查复制到排序器。
- **索引适配器**使用既有ES客户端及公共分区规则，建立独立能力索引。文档粒度为可引用能力证据，含agentId、evidenceId、公开文本、事实版本、文本摘要、embedding模型/维数/模板版本。索引不保存私有技能正文、凭据、聊天或资料正文。
- **现有调度机制**异步增量编码，沿用`ScheduledJobHandler/CronScheduleService`；技能、公开能力或可用性变更触发修复，周期核对漏更新。一次失败保留待修复，不阻塞业务修改，也不无限在线重试。
- **授权实时生效**：检索前限定当前授权agent/evidence集合；检索后用当前事实版本验证引用。撤权、卸载、禁用不能等待索引最终一致。在线/忙碌仅作等待提示，不自行变成能力硬淘汰条件。
- 模型/模板换代只作用于这个新索引的独立代次及别名；不碰聊天记忆。无正确代次向量的证据仍可关键词检索，但不能把旧向量拿来比较。
- **内部证据身份**由原候选/技能服务生成：本领以agent及规范化公开文本摘要标识（同文本去重，不用数组序号），技能以真实安装/授权来源标识；公开展示的`ability:序号/public-skill:序号`不得直接作为持久索引主键。事实摘要覆盖实际可披露文本、安装/产品版本、授权关系和可引用状态，不仅检查安装版本号。私有来源ID不向Web暴露。
- 索引文档ID绑定可信分区、内部证据键、事实摘要和embedding代次；更新产生新内容地址，旧编码任务不能覆盖新文档。查询只允许本次权威观察的确切文档ID；旧文档可异步清理，但迟到写不使旧证据复活。双路/分批检索固定同一物理索引代次及一致读视图（PIT），不在途中重新解析别名；视图失效返回可诊断降级/失败，不拼接两个代次。

### 3.2 在线处理

1. 读取任务/确切关联资料版本，批量取得当前候选和可披露证据，形成观察摘要。空候选直接返回NO_CANDIDATES。 推荐标题、说明取当前 Owner 作用域内的正式需求；不得用详情页旧计划摘要或事项 ID 补作待编码文本。根上的能力要求、状态与需求快照须属于同一任务版本；两次读取间版本改变则返回 409，不启动本次检索。缺少需重新确认的正式需求也是冲突，不返回“无匹配”；无权/不可见为 404，完整性或来源故障为 503。仅约束推荐取数，不改变详情页的历史只读展示。
2. 规范化任务标题、描述、显式要求及资料元信息形成检索文本；超出模型输入预算时按固定字段优先级确定性截取并记录截取标志，不调用模型做摘要。
3. 查询向量缓存命中则复用，否则最多一次Embedding请求。缓存键包括可信scope/owner、文本摘要、模型、维数及模板版本；相同输入合并在途请求。不可跨用户复用私有任务缓存，日志只记摘要和耗时。
4. ES分别返回关键词与精确向量相似度结果；**过滤发生在评分之前**。向量为空或模型代次错误的文档不参与向量分支。按当前候选集合分批处理，而不是只取全库TopK后过滤。
5. 每路在ES先按agent折叠/分组，取得**每个授权候选的最佳有效证据**，返回数量按本批候选数而不是证据条数设置；禁止先按全局文档TopK截断再去重。跨批次合并同一读视图下的最佳分数，再形成全局候选排名，绝不融合批内rank。原始同分按agentId确定次序，同候选同分证据按内部证据键确定引用；无命中候选没有该路rank，RRF贡献为0。
6. API对两个全局候选排名做RRF：`sum(1/(k+rank))`。初版候选级窗口覆盖全部当前候选（N），不截断为文档窗口；k及未来窗口变化受排序版本管理，k初值可取60，但不是置信概率。重复低分证据、批大小/顺序变化必须不改变最佳证据和排序。
7. 输出所有当前候选，每人一次。证据充分度/匹配等级使用标注集校准的阈值；缺少证据或校准覆盖则UNKNOWN。低相似度本身不能证明“不具备能力”；LOW须有可解释的已知不匹配依据。
8. 沿原用户选择语义：合适组HIGH/MEDIUM优先，同组自有优先；LOW/UNKNOWN不得因自有身份压过适配的外部候选。组内按版本化检索排序，最终agentId稳定打破平分。理由由真实证据和固定模板生成，不补写未披露能力、不宣称任务必然成功。

**评级策略制品（B48–49 实施细化）**：Agent 的 `CandidateSuitability` 只解释离线冻结的规则，不在请求中训练，也不把 RRF 分数或名次当作概率。通过 `jia.agent.recommendation.calibration-file` 和独立固定的 `calibration-sha256` 启用，默认均空。没有经过盲标、分族划分、独立留出及对应模式验证的制品，不得配置生产。文件摘要证明字节身份，不证明标注真实或指标合格。无效制品仅禁用评级，不阻断候选选择或报价。权重/阈值不接受浏览器输入。

- 首版制品 `capability-level-v1` 绑定候选融合版本、查询/证据模板、实际物理索引、Embedding 配置/模型/维数、租户和客户端分区，以及校准集、留出集、评估报告各自的摘要。两项检索分数直接取各路最佳授权证据；关键词为 ES 原始词法分，向量为 `cosine+1`，不同信号不能共用量纲。物理索引从实际命中读取，不信任别名的名称。未启用、无对应模式/证据形态、版本或分区不符、超出已测候选数范围、查询截断时均不作正向判定。
- 按模式（混合/仅词法）、支持证据（仅词法/仅向量/两路同证据/两路不同证据）、是否有显式要求/关联资料和已测候选数区间，选择唯一一条规则。HIGH、MEDIUM 可各自缺省；设置了某级时，该级的所有已用路分数须达到各自阈值。显式要求还必须由本次可引用的能力标签全部覆盖；该保守约束不等价于理解所有自由文本条件。负面/条件描述与部分匹配仍须纳入盲标和留出验证。首版不从低分产生 LOW。输出先区分适配/其余，在各组内保留自有优先及 RRF 稳定顺序。降级模式即使有正等级，业务状态仍是 DEGRADED。
- 对外 `rankingVersion` 包含实际规则指纹。指纹不纳入事后产生的留出报告摘要，避免“须先知道验证报告才能冻结待测规则”的循环；部署仍核验包含证据引用的完整制品摘要。评级不增加外部调用，不向业务响应或日志输出原始任务、向量或分数。线上变更只更换该配置及固定制品，不改索引数据。

9. 返回前短事务重查任务及相关候选事实摘要，变化返回409；不在锁中调用Embedding、ES或执行全量样本检索。确认承办仍走原授权/幂等链。 最终读取正式需求时复用本次按所有者作用域锁定的事项根，不调用会再次获取根锁的独立读取入口。初读仍独立鉴权；最终候选名册、资料复核及版本冲突处理不得因复用根而省略。

输入不读取附件正文，因此不能保证对隐含需求完全理解。这是能力边界，不用“准确率保证”掩盖。后续若增加正文提取，应作为独立需求核实其隐私和成本，不混入此次优化。

### 3.3 接口和故障语义

`POST /agent/tasks/{taskId}/recommend`：请求仍为`expectedTaskVersion: string`，公共信封不变。

响应保留taskId/taskVersion/observedAt（毫秒时间戳）/recommendations/candidateSetComplete；recommendations中移除quote；移除内部生成式workload及模型生成的需求摘要，不为旧客户端保留伪空字段。每项保留agent、recommendationLevel、reason、evidence、gaps。新增`retrievalMode: HYBRID|LEXICAL_ONLY|UNAVAILABLE|NOT_NEEDED`、`rankingVersion: string`、`degradedReasons: string[]`。

状态按“身份/事实读取失败 → 事实变化 → 无候选 → 检索降级 → 正常评级”的优先级互斥决策：

| 条件 | state / retrievalMode | 等级与HTTP |
| --- | --- | --- |
| 身份/任务或候选事实不可可靠读取，或事实变化 | 无成功业务结果 | 原401/404/503，变化409；不以空数组掩盖 |
| 可信候选集合确为空，未发起检索 | NO_CANDIDATES / NOT_NEEDED | 200/E0，空recommendations，degradedReasons为空 |
| 非空候选、两路检索完整可用，有HIGH/MEDIUM | READY / HYBRID | 200/E0；按已校准混合模式评级 |
| 非空候选、两路完整可用，无HIGH/MEDIUM | NO_MATCH / HYBRID | 200/E0；LOW须有已知不匹配依据，否则UNKNOWN |
| 非空候选、向量不可用但关键词结果完整 | DEGRADED / LEXICAL_ONLY | 200/E0及非空degradedReasons；仅该模式独立校准后可有HIGH/MEDIUM，否则UNKNOWN |
| 非空候选、检索整体不可信（包括词法失败而仅剩向量） | DEGRADED / UNAVAILABLE | 200/E0，完整候选均UNKNOWN；初版不新增未校准的VECTOR_ONLY路径 |

- HTTP 404 指调用人不可见的**事项**（含名册策略复核时失去可见性）。事项已授权，但无法可靠取得全部候选能力事实，例如仍有效的自有身份缺少对应运行信息，返回 503；不披露问题候选或内部记录，不以 404、空名册或正常无匹配掩盖。
- `candidateSetComplete`只表示候选是否完整，不表示语义判断可靠。当前整体逐人合同不静默截断候选；若无法完整读取则503，不用TopK假装全量。
- Web解析和投影采用上表，删除“READY等价于存在HIGH/MEDIUM”的旧断言：已校准降级也可能有推荐等级，但必须展示降级说明。DEGRADED不等于无人可选；手选报价仍经独立授权入口。

不用排名分数直接当推荐概率，不按技能名、人物名、文件后缀维护业务映射表。扩展来自能力数据、模型/索引代次与排序参数，而不是继续增加角色分支。

## 4. 费用预算方案

### 4.1 先补计量，不能直接拟合旧金额

预算有三种不同事实，不能混称：

- **实测用量**：响应/工具真实报告的单位数量。
- **参考价预算**：将兼容样本用量按平台选定的当前价目计算，供固定WEN报价；不等于供应商已收取的账单。
- **实际成本账**：保留真实计费模型、渠道、价格及完整性证据，未知仍待核实；不因生成了预算就补成已知成本。

既有Runtime executionModel继续用于选择平台报价价目。历史样本必须有可核实的执行配置/路由身份及完整用量，不能把requestedModel冒充实际计费model。网关如不能证明实际模型/计费口径，实际成本保持未知；可在**明确固定执行配置且经过基准验证的参考价样本分组**中估预算，快照标记REFERENCE_TARIFF，不能标为已对账实付。

数据合同分开保存：`MeasuredQuantities`含计量分类/数量、归一化依据、证据摘要与coverage，但不要求编造实际模型；`ActualBillingIdentity`为可空的真实channel/model/tier及证据；`ReferenceTariffIdentity`为平台确定的报价channel/model/tier/价目版本与REFERENCE_TARIFF标记。样本消费前者及参考价身份，**不以实际账本PRICED为入样条件**。

现有`TokenUsageCost.Usage`要求真实身份，不能直接装载参考身份。实际身份未核实时保留原始计量及样本侧MeasuredQuantities，实际账本不构造伪Usage/PRICED；沿待核实状态增加原因`BILLING_IDENTITY_UNKNOWN`并展示“计量已取得、实际计费身份待核实”。裸usageMetadata.amount未证明币种/计费口径时仅作原始证据。

### 4.2 Runtime采集及持久化

正式计量主源改为§4.2.1的Runtime显式出口，记录独立请求清单和渠道返回的usage。已核查的internal-only `rawResponse/completed`及rollout `TokenUsageRecord`仅作可选辅证；二者均不能独立证明全任务完整，也不再作为预算可用性的唯一协议依赖。方案：

1. 在现有Runtime受限出口增加**版本绑定的来源适配**，逐请求预写、逐响应保存，不再以最后一次通知快照计量。只有实际验证了来源协议、流式/单位语义的版本才启用归一化；未知版本保留原始计量证据并报告不支持，不默认为0。app-server适配只提供可核实的补充关联。
2. 计量出口为主源，实时通知与rollout仅可补充已绑定请求的同一响应；按可信渠道命名空间及原响应身份去重。原execution/capture绑定必填；thread/turn/rootTurn只在有可信关联时作为可空追溯字段，不猜测生成、不用于改写执行归属。fork/resume复制的旧记录不能归入新任务重复计费。同身份不同内容报告冲突，不取最大值掩盖冲突。
3. 在原执行store中持久化精简的响应计量及完成清单，不保存提示词、推理、工具stdout或私有配置。正常终止、失败、中断、恢复均走同一采集收尾。
4. **releaseAdapter删除engineState前**，在既有writer/执行锁保护下完成停止、日志补采和原始计量持久化；不能只改后台扫描。转存失败则保留待恢复状态，不阻止已经确认的业务完成事实、不重新执行模型；磁盘失败告警并阻止该来源被静默清掉。
5. 完成清单包含观察到的响应身份、缺失usage、异常终止、子执行、压缩、工具计费来源及协议版本。仅看到task_complete或一条usage不构成完整性证明；断连/缺少预期响应边界时标INCOMPLETE。
6. 沿现有usage delivery与UsageCostService实现幂等投递及修订，不另建钱包/计费框架。新逐响应成本来源与旧整执行UNVERIFIED来源不能对同一次调用重复入账；旧数据只留追溯，不进入新样本。
7. 新样本投影保存执行完成清单及coverage状态；成本汇总必须显示“执行证据不完整”，不能因现有响应都已定价、pending计数为0就宣称全成本已知。补齐清单/响应后可幂等更新投影，不改历史报价。
8. 归一化按渠道协议：cache从普通input中分离，reasoning若包含在output中则不重复加，cache-write时长/图片分类不明则未知。用量缺失不当作零，只有明确的0才可作0。

官方固定版本中正常完成、所查本地压缩路径、带responseId的部分失败会留下计量；全路径覆盖、崩溃持久性及通知实际可达性仍须实施后的定向测试，不将上游单元测试冒充CYF通过。

#### 4.2.1 完整性来源：选定Runtime内显式计量出口，U1设计层已闭合

**当前选择**：复用现有Runtime进程、执行状态目录和受限网络出口，增加执行绑定的Responses计量处理；不以修改Codex源码、改造外部网关或新增常驻推理进程为默认方案。真实Codex0.167.0与非付费模拟上游的最小协议探针已运行，详见下文；业务代码/生产网络与凭据配置尚未改动，当前生产仍没有这一完整性来源。固定候选已获本轮独立续审PASS_DESIGN，U1仅在设计可实施性范围关闭，回执见§10。

```text
Codex及本次执行的子来源（只持有执行临时token）
  → 既有Runtime受限出口的显式Responses计量处理
  → 请求意图异步写盘并确认 → HTTPS发送至原网关
  ← 流式响应与usage → 独立结果证据持久化
  → 原Runtime投递链 → API执行绑定与去重 → Economy计量/参考价样本
```

这是**明确配置的应用层转发适配器**，不是读取既有CONNECT隧道明文或替换上游证书的TLS解密代理。原公网provider仍要求HTTPS；本地明文段只在受控执行网络内到精确计量入口，不能把公网HTTPS校验改成任意HTTP。原网关仍为请求目的地，不修改其服务或凭据；模型输入输出只经内存流式转发，不另存正文。

**实际复用落点**：`runtime/conf/codex-bridge/typed-inspection-network.mjs`已有Runtime内HTTP server、执行Owner/netns绑定、nft出站限制和精确CONNECT控制；本模式为该出口增加受控HTTP处理，不再新增一套出口进程。`controlled-image-gpt-cli-egress-gate.mjs`已有“本地baseUrl/临时token、Runtime注入上游凭据”的同类实现，可复用其边界经验，但它当前的内存计数不是本方案的持久化模型调用清单。配置/鉴权接入落在既有`isolated-engine-profile.mjs`与`native-execution-runtime.mjs`，不把新的路由逻辑放入Economy或Web。

##### A. 独立来源和完整性合同

Runtime提供可信执行绑定的来源结果，API验证来源适配版本和原执行身份，Economy只消费归一化计量。`captureState`（来源已持久化）、`deliveryState`（API已ACK）、`coverageState`（本来源范围完整）分开，实际价格是否已知也独立。

1. **预期集合来自真实外发边界**：适配器为每次准备向网关发送的请求分配`captureId/sourceId/epoch/sequence/attemptId`，绑定原execution及允许的操作；写盘确认之后才能发送请求头/正文。它不依赖usage通知或已成功的响应，不用`turn/start`次数代替模型调用次数。即使无responseId，也有独立attempt占位。预写失败不发送；不得先转发再异步补记。
2. **请求与响应不是同一身份**：每次客户端重试都是独立请求attempt；响应ID、usage、状态/错误绑定原attempt。适配器不另加自动重试、重定向跟随或备用直连。多个attempt观察同一response按§4.2.2合并/报告冲突，不重复计费；多个不同response也不当同一记录的修订。
3. **停止与关闭可证明**：先停止本执行及子来源产生新调用，再收敛适配器在途请求和写入，最后持久化最终sequence/清单摘要/未决项。sequence关闭水位指已分配序号的上界，不是实际外发请求数；预写失败可能留下序号缺口，必须保留并使该来源不完整，不能把预写失败算成已外发或免费调用。关闭后拒绝新调用；进程退出、task_complete或API pending=0不替代该记录。回收须沿§4.2.3既有停止→采集→ACK→cleanup顺序，不在业务完成时先删原始来源。
4. **恢复不猜测**：预写后发送前崩溃、发送后结果写入前崩溃、半条尾记录、流截断、缺usage都保留INCOMPLETE/未决身份；不推断免费，不重跑模型“补日志”。新epoch连接前代来源，不能覆盖未决项；重复读取/投递复用原身份。完整用量缺失时完整总量为null，已观察部分总量只能另列。
5. **COMPLETE正例**：来源版本/执行绑定正确、发送路径均在覆盖范围、关闭及连续性可核验、全部attempt已有可信单位报告或确证不计费依据、无冲突/未决项时才成立。未知是否计费的失败样本允许永久不完整，不要求所有失败都恢复为COMPLETE；但正常完整执行必须能产生并恢复COMPLETE，不能一律拒收来规避可用性。
6. **范围不能夸大**：这证明的是本执行向已配置渠道发出的客户端请求及渠道返回的计量已收齐，不证明渠道内部隐式重试/隐藏路由或最终账单已经对齐。`ActualBillingIdentity`和供应商对账仍可未知；`ReferenceTariffIdentity`不能替代真实计费身份。其他计费工具沿各自来源合同闭合，模型出口完整不能把尚未闭合的工具成本变完整。

##### B. 必须一起落地的路由、凭据和DFX约束

- **不可绕过**：metered模式禁止现有CONNECT直接通向模型网关，并防止通过`additionalOrigins`再次放行同一模型目的地；不提供故障后直连。保留原Owner/PID/netns绑定与nft精确出站读回，允许的本地地址/端口由运行时创建并绑定本执行，不由任务正文任意指定。
- **凭据不下放**：真实provider凭据只在Runtime出站侧使用；Codex隔离HOME只放本执行临时token的私有auth文件，不把真实auth.json继续复制进去。临时token不得写入argv、日志或业务回执，不作为上游token转发。执行结束立即撤销，不可跨执行复用；旧凭据/路由模式不能获得新来源COMPLETE。
- **请求边界**：验证临时token、精确方法/路径、固定上游及本次执行仍有效；关闭后拒绝，未知端点/WS升级不得透传或静默直连。公网HTTP、任意Host/绝对URL、重定向目标、旁路CONNECT均不能由请求控制。业务任务授权仍归API，不在适配器重建业务权限体系。
- **协议覆盖显式**：首个来源协议按HTTP Responses的逐请求/流式响应建立；Codex配置关闭WS传输，原型也拒绝upgrade。正式声明支持的压缩、子执行、HTTP重试及非流式端点须在实际路由上补齐解析与回归。未覆盖路径不可生成完整样本，不把本轮普通HTTP正例泛化为全Codex功能已验收；新provider/协议按来源版本扩展，不按人物/模型品牌硬编码业务。
- **单请求来源范围**：在既有 HTTP 上传流上观察实际请求而非从提示词推断。识别请求结构、输入模态和工具声明；命名空间需递归检查每个工具，不能因外层是 namespace 而把内部当本地函数。仅声明由客户端执行的函数不等于已计量函数的实际执行；仍须核对整执行中独立工具来源。遇到服务端工具或未知工具、非文本输入、未识别结构/截断/有界解析失败，原请求仍按原授权转发，保留安全的报告用量和固定原因码，不为这次响应构造纯文本归一化计量。观察无反例只排除本次已识别的不兼容项，不作为渠道、完整性或价格证明，不存输入内容或工具参数。
- **资源与持久化**：沿§6.0采用可等待的非阻塞写入，不新增同步fsync热路径、无限内存队列或正文日志。正式流转发必须有背压、分片/UTF-8边界处理及受现有请求策略约束的缓冲；探针中的1MiB夹具限额不作为新生产限制。I/O失败停止受影响调用/保留未决来源，不让其他执行停摆，不关闭已有安全校验。
- **持久状态与升级**：生产来源位于既有长期执行状态体系，不放72小时任务区；来源格式/适配版本进入原执行plan与发布清单。§7.1的Runtime/API回退约束继续适用，旧读取器不得把新状态当无成本。不得把改provider.base_url视为无需安全/隔离回归的单纯配置替换。

##### C. 实际可行性探针与阶段判据

固定Codex0.167.0官方发行二进制SHA256为`cdcb45aaa01d0f14e298985e09465aebccd47f64ecd298aea44814af7b62bbda`。在既定SSH worker的独立mount/net namespace运行真实`exec`和`app-server`，仅loopback模拟上游；引擎使用无权限UID，nft只允许计量入口，独立直连模拟上游返回连接拒绝。模拟oracle只用于测试断言，来源分类器仅从自己的持久文件读取，完全不读取oracle计数或Codex用量通知。

已运行的最小场景包括：正常两请求及重启只读恢复、app-server第二响应缺usage且消费侧丢弃全部用量通知、HTTP500后重试、预写后发送前kill、响应收到但结果写盘前kill、预写失败不外发、重复响应身份。正常路径产生COMPLETE，故障/缺项保留INCOMPLETE；坏token和不支持端点在本地拒绝，不发送上游。模型、token和文本全为夹具，**不是实际预算基准、准确性数据或真实网关对账**。两请求夹具使用的update_plan在该配置下返回unsupported tool，确实诱发第二次HTTP请求，但不把它称为工具成功/压缩/子代理已覆盖。

最终固定探针批次`cyf-usage-source-feasibility-20261123-09`的9个场景符合各自期望：probe SHA256 `7c105feec32694235fc91ffc29c5d81f476a92c9385a7330605875422afbd765`，relay SHA256 `e6744476ced459a846626e6f3a9e541a63a172764d09e11a68b130c21f751c97`，回传映射SHA256 `a04c76b2b330b7712548119877354ed39d386b51b7f4b03a34a76f3954b0bc84`。每场景实际nft读回及独立直连负例均留证；生产netns/全链路验收未由此替代。

探针源码、精确SHA、独立oracle、来源记录、回传和结果存于`/home/isp/tasks/cyf-embedding-openai-20261123/u1-feasibility-r2/`，遵循72小时TTL。初期夹具nft语法和无权限UID目录遍历失败另存，后续通过私有mount视图修复；没有放宽宿主目录权限、nft规则或替换生产二进制。本轮未调用付费模型，未改变业务源码、生产模型配置、索引或部署。

**阶段不能混用**：设计层U1依据“实际发送入口可接、正常可完整、遗漏可发现、崩溃保留未决”的固定探针与独立回读关闭；生产者→Runtime→API→Economy集成、完整故障矩阵、压缩/子执行等声明路径、容量/性能、安全和真实网关兼容性属于实施验收，不能省略。付费基准仍需授权；只有实际实现并验收的来源可进入真实预算样本。设计可实施不等于当前生产已经能报价。

##### D. 排除的方案及先前核查保留

原官方固定版本中`RawResponseCompleted`被rollout策略列为不持久化，usage为None时也不写TokenUsageRecord；app-server通知没有连续序号/关闭水位。HTTP/WS遥测回调位于发送之后，OTel为批量best-effort导出。因此原“通知＋补读rollout”“只开启OTel”路线仍不成立，不能把旧样本回填成完整。此前源码核查及7项静态断言保留在`u1-source-probe`，不是本轮真实二进制探针。

外部网关公开首页自报CLI Proxy API Server，但没有核实其管理日志/持久化/完整性合同，因此不把它当权威调用清单来源。引擎fork也是可选技术路线，但worker当前无Rust工具链/缓存，既有Runtime构建入口不编译Codex；本方案不为预算引入该版本维护和构建依赖，不改全机Codex或外部网关。

#### 4.2.2 逐响应账本与修订合同

- 新执行启动前持久化`usage-capture-plan`，固化计量协议版本、来源kind（本路线为METERED_HTTP_RESPONSES_V1）、原执行/来源命名空间及引擎/持久化来源目录绑定。该执行全程只选`RESPONSE_V2`或既有整执行来源之一；不在执行中途切换计费所有者。不把遗留无plan的执行自动迁成逐响应来源。
- 来源适配器以出口结果为主、融合经核实关联的通知/rollout同一响应辅证，使用`source=NATIVE_RESPONSE_USAGE`和由**原执行固化的渠道命名空间＋原始响应身份**生成的`sourceAttemptId`。原execution/capture是不可变归属，thread/rootTurn在真实可得时仅作追溯；不因重放、fork复制或当前配置变化生成新计费身份，复制来源只能引用原归属，不能在子任务重记。
- 一个响应对应一个账本attempt；多个响应是不同attempt。revision只修订同一响应，因此沿现有UsageCostService的“减去该attempt旧值、加新值”语义，不把响应B当响应A的下一版。
- 新逐响应观察明确`schemaVersion=2, executionId, sourceAttemptId, sourceRevision, receiptId, expectedRevision, evidenceSha256, measuredQuantities, actualBillingIdentity`及原执行认证绑定；完整wire及字段嵌套位置以§4.2.4为准（计量/响应身份在observation内），不另造一份扁平DTO。sourceRevision为该来源不可变证据版本，ledger revision由API返回；二者不是STARTED/TERMINAL固定1/2。receiptId绑定原响应及来源修订/提交身份，首次expectedRevision=0，后续基于确认的账本revision。
- 同receiptId同内容返回原ACK，同receiptId异内容409；新增真实证据产生新的sourceRevision与receiptId，不能覆盖旧观察。ACK至少绑定attemptId、已接受sourceRevision/证据摘要、ledger revision及成本状态。ACK丢失只重投原请求；expectedRevision冲突先读回原receipt/当前观察并核对前驱，不能盲加版本或修改同receiptId内容。若有独立补价修订，先归并其已接受版本，再用新的提交身份提交后续来源修订；不丢掉补价/来源任一历史。
- 同响应通知与rollout内容一致则合并，不生成第二个attempt；互相矛盾保持冲突，不能以更大值覆盖。尚未核实usage的revision可以待用量，随后明确证据可修订；不能把未经解释的差异包装成正常修订。
- 旧执行整条UNVERIFIED记录只属于旧计量模式；新模式不再创建它作为额外成本占位。已有旧数据保持原始追溯/未知状态，不改成零来清pending；新执行coverage单独由清单表达。

必要验例：A=0.1元、B=0.2元，双来源和ACK丢失重投后总额0.3元；A合法修订为0.12元后总额0.32元；乱序、同revision异内容、fork复制不产生额外贡献。

#### 4.2.3 终态与取消后的可恢复采集

- `usage-capture-plan`在引擎启动前持久化，最终`usage-capture-finalized`作为**正向**完成证明，绑定已保存计量/清单的摘要和版本。不能依赖异常时才写的cleanup-pending；磁盘满时后者也可能写失败。
- 既有pending发现逻辑须增加独立的采集恢复分支：存在新plan却无finalized的执行，即便已有业务receipt/failure-receipt或已取消，也会被发现。由持久化plan恢复目录/身份绑定，不只依赖内存suspendedNativeStates。仅在原writer gate及确认停止后读取原始来源，绝不claim/resume模型或重复提交业务结果。
- 取消/租约停止、正常提交、失败以及重启恢复统一遵循：**停止并确认无写入 → source-only补采并持久化 → finalized → 幂等投递/ACK → 满足保留策略后清理**。`flush`先调用此采集收尾并显式返回capture/delivery/coverage三个状态；现有pending=0不得授权删源。
- 可恢复的转存/fsync失败沿既有退避重试、受限批次及告警保留来源；来源不可恢复或协议不能证明完整时，将已取得证据与原因原子封存为`SEALED_INCOMPLETE`，不是COMPLETE。封存必须先持久化；磁盘失败时不能仅凭超时删除唯一来源。其实际成本继续未知、样本不可入选，但业务完成事实不回滚。
- finalized仅证明来源已转存/明确封存；ACK只证明接收持久化；coverage不完整或价格未知不妨碍已安全转存来源按原保留策略收尾。凭据、auth和skill-config仍按原安全生命周期移除，不为恢复复制或长期保留密钥。


#### 4.2.4 完整性证据投递、ACK与API投影（R3-02修订）

**受限本地工具策略的信任边界（C42）**：Agent 仅在原 TASK 执行创建时，对已启用计量且未选技能的执行冻结运维独立核实的配置摘要；空值或不合法的值不启用策略。该摘要覆盖策略、引擎、计量口径、可跨执行比较的配置组、路由组、工具组和渠道命名空间，不从此次 PLAN 反算批准值。配置轮换不能改变旧执行。投影在关联完成后读取原执行冻结值，并比对原作用域、参与方与 run。Economy 保存和投影计量事实，不决定 Runtime 可用工具或调用权限。

`NATIVE_LOCAL_ARTIFACT_TEXT_V1` 首版仅支持单根来源、epoch=0 且至少一次请求。冻结摘要匹配是必要而非充分条件：逐请求实际形态和用量、关联、关闭水位与最终清单均须通过；未匹配、未知出口或不能归一化时，不得补零。该策略不证明实际价格、付费账户或整事项已经合格。新增可空列需在安装候选 API 前按原迁移流程执行；本轮没有执行生产迁移。


**路由和责任。** 扩展现有`POST /internal/agent/executions/{executionId}/runs/{runId}/usage`，新capture固定使用下述业务schemaVersion=2；不将旧STARTED/TERMINAL兼容解析为新来源。公共信封仍为统一规范v1.4的`{protocolVersion:1,requestId,data}`。Agent沿现有历史执行查找和Runtime身份fence核实原execution/run、owner、agent及capture归属，形成可信绑定；Runtime负责来源协议归一化，API来源适配器验证已声明版本，Economy只保存归一化证据、计费及投影。请求不接受客户端task/owner/tenant替换原绑定。新执行准入时沿原执行记录固化usageMode及captureProtocol；RESPONSE_V2的`captureId=SHA256(canonical(["CAPTURE_V2",executionId,runId]))`，API和Runtime均能从原执行计算，不等待首条usage才生成预期成员身份。同一run恢复沿用capture并新增来源epoch；遗留执行不补造该模式。

复用原delivery的逐条重放，不一次发送无界清单。**一种持久记录对应一次HTTP投递**；PLAN、SOURCE、REQUEST、RESPONSE、SOURCE_FINAL、CAPTURE_FINAL共享同一接收流程，不新增独立队列/通用事件框架。API长期保存收到的精简来源记录，不把原始记录只留在72小时任务区。现有执行查找拿不到可信归属时404；不按当前grant已结束直接否定原执行的迟到计量。

**公共业务字段（所有种类必填，明确可空者除外）。** `schemaVersion`为数字2；`executionId/runId/captureId/receiptId`为1–100字符不透明ID，沿既有ID语法；`kind`为上述六值；`recordId`为稳定64hex键；`sourceRevision`为正十进制字符串；`previousEvidenceSha256`首次为null，否则为同record上一证据摘要；`evidenceSha256`为本记录摘要；`observedAt`为安全整数毫秒；`expectedRevision`仅RESPONSE为非负十进制字符串，其他为null；`observation`为下表对应的封闭业务对象。计数/epoch/sequence/revision一律为非负十进制字符串（正值在表中约束），不得经JS Number比较；SHA字段为64位小写hex。省略必填字段与显式null不同。

| kind | observation必填字段/类型 | 唯一身份与含义 |
| --- | --- | --- |
| PLAN | `captureProtocol: "METERED_CAPTURE_V2"`、`snapshotSha256: SHA`、`executionConfigSha256: SHA`、`engineVersion: string`、`coveragePolicyVersion: string`、`rootSourceId: ID`；可选 `dispatchGroup:{version:"NATIVE_DISPATCH_GROUP_V1",executionConfigSha256:SHA,routeSha256:SHA,toolConfigSha256:SHA}` | 每capture一个PLAN；引擎启动前本地持久化。policy固定准许的模型/工具来源及未知来源处理，不因漏上报把来源范围缩小 |
| SOURCE | `sourceId: ID`、`epoch: decimal`、`sourceKind: string`、`adapterVersion: string`、`channelNamespace: string`、`parentSourceRecordId: SHA或null`、`previousEpochSourceRecordId: SHA或null` | 每(sourceId,epoch)一个SOURCE，先注册并持久化再准许该来源调用；恢复新epoch必须链接前代，子来源必须链接父SOURCE，不复用旧epoch覆盖记录 |
| REQUEST | `sourceId: ID`、`epoch: decimal`、`sequence: positive decimal`、`attemptId: ID`、`resolution: PENDING或RESPONSE或UNRESOLVED`、`sourceAttemptId: SHA或null`、`reasonCodes: string[]` | 每(sourceId,epoch,sequence)一个记录；初版PENDING、sourceAttemptId=null。结果修订为RESPONSE时引用真实响应；无responseId则UNRESOLVED且引用null、原因非空。PENDING不等于未发送或免费 |
| RESPONSE | `sourceId: ID`、`epoch: decimal`、`sourceAttemptId: SHA`、`providerResponseId: string`、`reportedUsage: object或null`、`measuredQuantities: object或null`、`actualBillingIdentity: object或null`、`reasonCodes: string[]` | 每capture及原渠道命名空间内的响应身份一条，sourceAttemptId沿§4.2.2，不以重试/投递次数生成新响应身份；实际账本继续跨capture核对原归属 |
| SOURCE_FINAL | `sourceId: ID`、`epoch: decimal`、`reservedSequenceHighWatermark/requestCount/responseCount: decimal`、`recordsSha256: SHA`、`closeState: DRAINED或SEALED_INCOMPLETE`、`reasonCodes: string[]` | 每(sourceId,epoch)一个可修订关闭记录；requestCount是已持久化REQUEST数，不冒充已发网关次数；recordsSha256绑定本SOURCE及该来源全部REQUEST/RESPONSE的确切修订 |
| CAPTURE_FINAL | `planEvidenceSha256: SHA`、`sourceCount: decimal`、`sourcesSha256: SHA`、`closeState: DRAINED或SEALED_INCOMPLETE`、`reasonCodes: string[]` | 每capture一个关闭记录；引擎及全部子生产者停止、来源关闭后才生成；sourceCount含全部epoch及工具来源，sourcesSha256绑定全部SOURCE_FINAL的确切修订 |

**原派发快照绑定（C39）**：新投递的 PLAN 必须携带实际执行命令的 `snapshotSha256`。Agent 先在原身份栅栏确认 execution/run 归属，再按原始 tenant/client/事项或私密执行所有者/execution 键，仅读原 `agent_skill_execution.snapshot_sha256` 比对；无需传原始输入内容。原执行不可见仍为404；摘要格式错误400，缺绑定或与原始派发不一致409，不写入任何收件/账本。不依赖当前租约或当前配置；历史证据和既有回执保持原字节，GET 不要求补发。该摘要仅证明 PLAN 对应已授权的命令快照，**不是**引擎/出口/完整性证明，也不替代单运行 `executionConfigSha256` 或跨事项的 dispatchGroup。

`reportedUsage`保存来源适配版本明确准许的原始数值计量片段（如input_tokens/output_tokens及其计量明细），缺失为null；禁止夹带请求/回复正文、HTTP头或密钥，未知来源字段不无条件接收。未能安全保存/解释计量时只封存可保存的证据和原因并保持INCOMPLETE，不把摘要当已保存原值。该片段与归一化结果都随证据摘要持久化，不能API只存归一化null、ACK后又清掉唯一可恢复计量。`measuredQuantities`在初版模型来源中为`{normalizationBasis:string,tokens:{Category:decimal},coverage:"COMPLETE"}`；Category沿现有`ModelTokenPrice.Category`，数量为非负整数十进制字符串。只有来源协议明确覆盖全部计费类别时才构造该对象；明确为0才可空tokens对象，缺失/无法归一化则整个对象null，原精简用量可留在Runtime证据但不伪造计费数量。`actualBillingIdentity`若非null，必含非空`channel/model/tier`及`evidenceSha256`，只能来自已核实实际身份。工具扩展必须有独立adapterVersion及单位schema，遵守§4.3互斥计费；初版未实现的工具来源只允许封存INCOMPLETE，不能把模型闭合当工具未调用。

**摘要与版本。** 新记录沿现有`skillCanonicalJson`（对象键递归排序、数组保序、UTF-8、显式null）的摘要语义，Java使用同一固定fixture核对；不修改历史消息算法。`recordId=SHA256(canonical(["USAGE_RECORD_V2",captureId,kind,identity]))`，identity依次为：PLAN/CAPTURE_FINAL取空数组；SOURCE/SOURCE_FINAL取[sourceId,epoch]；REQUEST取[sourceId,epoch,sequence]；RESPONSE取[sourceAttemptId]。新来源的`sourceAttemptId=SHA256(canonical(["NATIVE_RESPONSE_USAGE",channelNamespace,providerResponseId]))`，沿原账本source+sourceAttemptId生成attemptId；不重算遗留来源身份。`evidenceSha256`覆盖`schemaVersion/executionId/runId/captureId/kind/recordId/sourceRevision/previousEvidenceSha256/observedAt/observation`组成的对象，不含公共信封、receiptId、expectedRevision或自身。SOURCE_FINAL的recordsSha256对所属SOURCE、REQUEST、RESPONSE的`[recordId,sourceRevision,evidenceSha256]`按recordId字典序组成数组求同算法摘要；CAPTURE_FINAL的sourcesSha256对所有SOURCE_FINAL同样处理。空集合有确切摘要，不用null表示。

PLAN的执行配置/policy/rootSourceId、SOURCE的来源/归属/前代及REQUEST的attempt身份一旦登记不可改绑；修订只增加结果或证据。身份/同版本内容矛盾在认证绑定内留存冲突标记并使样本不可选，再返回409；不能随异常整体回滚掉隔离标记。正常账本CAS竞争不等同来源内容冲突。同recordId同sourceRevision异摘要409并隔离该capture的样本资格；同一版本重复不会增加计数。修订必须链接上一证据摘要，缺前驱可持久接收为待关联，不激活、不覆盖；前驱矛盾则冲突。封闭后的请求集合不再扩充；迟到的既有请求/响应补证可产生新revision及对应新FINAL，不能靠增加关闭水位授权新模型调用。引用旧修订的FINAL不能使新数据自动COMPLETE。

**ACK及幂等。** `Idempotency-Key=receiptId`，同次提交requestId/key均保持。可信原执行绑定＋receiptId唯一，同key不同完整业务请求409；证据修订或解决账本CAS冲突使用新receiptId，不能改写旧提交。成功仍HTTP200/E0，data为：`{schemaVersion:2,executionId,runId,captureId,receiptId,recordId,sourceRevision,evidenceSha256,acceptedAt,acceptance:"DURABLE",ledger}`。`ledger`只在RESPONSE非null，含`attemptId:SHA,revision:decimal,status:PENDING_USAGE|PENDING_PRICE|PRICED,costYuan:decimal-string或null`；其他种类为null。返回并持久保存原ACK字节用于重放；ACK不含会随后台变化的“当前COMPLETE”结论。DURABLE仅证明记录可恢复，不能作为报价许可。

新增同Controller下只读`GET /{executionId}/runs/{runId}/usage/receipts/{receiptId}`返回原ACK的data（GET公共信封使用本次requestId，不复制旧请求信封；ACK业务数据保持原字节语义；尚未完成ACK则409 `USAGE_ACK_PENDING`，已记录内容冲突则409 `USAGE_CAPTURE_CONFLICT`，不存在404），以及`GET /{executionId}/runs/{runId}/usage/records/{recordId}`返回`{recordId,sourceRevision,evidenceSha256,ledgerRevision}`当前已关联版本（无账本时ledgerRevision=null）。两者沿同一原执行鉴权，无模型/资金副作用；用于丢ACK和409后核对前驱，不成为另一个写入口。类型/摘要错误400 `USAGE_CAPTURE_INVALID`，不支持的业务版本400 `USAGE_CAPTURE_VERSION_UNSUPPORTED`，内容/前驱/CAS冲突409 `USAGE_CAPTURE_CONFLICT`，持久化故障503 `USAGE_CAPTURE_STORE_UNAVAILABLE`。旧鉴权401/404保持，未知覆盖版本可以留存证据但coverage为INCOMPLETE，而不是按已支持版本归一化。

**持久化与事务（明确不假定REQUIRES_NEW能加入外层原子事务）。** 在Economy现有用量持久化边界增加三类相互绑定的领域记录：`economy_usage_capture`保存可信绑定、inputRevision、projectionRevision及coverage；`economy_usage_capture_record`保存上述不可变证据修订和关联状态；`economy_usage_capture_receipt`保存提交请求摘要、expectedRevision、处理状态及不可变ACK。名称为实施目标；唯一约束依次为scope+execution/run/capture、capture+recordId+sourceRevision、可信原执行+receiptId。多个提交可引用同一证据修订（如账本CAS冲突后新receiptId），不复制成两个来源记录。SOURCE/REQUEST没有供应商响应时只在capture记录占位，不伪造费用attempt。

1. 接收事务依次锁定关联样本、capture及记录/提交身份，保存证据及待处理标记；无task的执行只操作capture，不创建整事项样本。**同事务增加capture.inputRevision和关联事项sample.evidenceRevision并把可能入样的事项样本置WAITING_EVIDENCE**，后续新报价不再选择旧READY投影；CANCELLED等已明确排除者保持EXCLUDED。重复完全相同证据不增加revision。初次响应的身份来源、PLAN或前驱未到时同样先留证待关联；已ACK不意味着关联完成。
2. RESPONSE先确认来源/前驱关联，再沿原`UsageCostService.record(REQUIRES_NEW)`幂等落账；不在接收事务持锁时嵌套调用它。实际身份未知则保持原待核实账本及`BILLING_IDENTITY_UNKNOWN`，归一化计量单独保存，不妨碍参考价样本的计量条件。进程在账本提交后崩溃，恢复以原receipt重投取回原ledger结果，绝不制造下一笔attempt。
3. 非RESPONSE在证据事务提交后即可保存并返回DURABLE ACK；RESPONSE在账本结果确认后另一个短事务标记已应用并保存带ledger的ACK。缺PLAN/前驱导致不能落账则返回409 `USAGE_ACK_PENDING`并保留原请求，待关联后同key可完成；409 CAS冲突按§4.2.2读回版本并用新提交身份解决。仅因暂缺依赖不把记录改成收费失败或免费。
4. 沿现有调度/用量恢复入口扫描待关联/待应用记录，不新增消息中间件；最终按固定capture.inputRevision计算各capture覆盖，再按sample.evidenceRevision计算整事项投影；各自短事务CAS核对输入版本未变才更新对应projectionRevision。冲突只重算投影，不重做模型。报价prepare只选sampleState=READY且sample.evidenceRevision=sample.projectionRevision的快照；persist复查所选样本修订仍可选，与失效处理共用样本行锁并按稳定键顺序加锁，变化409而不重算价格。已提交报价不因后来补证而追溯改价。

**API判定与收尾。** 没有合法PLAN、CAPTURE_FINAL或某来源/响应尚在传输，coverage为WAITING_EVIDENCE；PLAN必须有rootSourceId对应的epoch="0"根SOURCE；所有子/后继epoch须可达此根且无环。没有根SOURCE不能把空sources摘要当完整。policy还必须覆盖执行配置准许的全部潜在收费出口；未封闭工具路径即便没有调用日志，也标INCOMPLETE/UNSUPPORTED_COST_SOURCE，不因此阻止原有业务执行或追加费用门禁。全部声明记录已到后，核对sourceCount、摘要、每来源requestCount/responseCount、连续sequence及引用修订。高水位大于REQUEST数量表示明确缺口，关闭来源保持INCOMPLETE，不把未持久化序号算成外发请求；相同response被两个不同请求引用、缺usage、未知适配、未决来源或SEALED_INCOMPLETE均不完整。初版不实现供应商失败免费证明，因此失败只能保持未决，不能构造0用量。只有所有实际登记来源闭合、摘要一致、引用去重且计量完备时才COMPLETE；actualBillingIdentity未知不否定计量完整，但不产生PRICED实付账。

Runtime只在**计划、全部来源记录及最终清单的确切修订均收到匹配DURABLE ACK并本地保存**后标delivery完成；只收到FINAL的ACK或所有RESPONSE的ACK都不够。API拥有可恢复的全部原始精简证据后，即使投影仍WAITING/INCOMPLETE，来源可按原保留策略收尾；不删除API唯一证据来假装无pending。跨进程原始记录、账本与样本从而允许异步，但不会把一半提交当完整样本。

固定完整请求/ACK及正常、缺响应、乱序、丢ACK反例见[新用量契约夹具](usage-capture-v2-fixtures.json)。夹具仅是设计合同，合成token不进入基准；产品实现必须由Java/Runtime消费者共用并通过相同测试后才能宣称接口实现。

**PLAN 配置承诺的口径（实现核对，11月24日）**：外层 `executionConfigSha256` 仍绑定本次运行的布局和命令，不作跨事项分组。可选 `dispatchGroup` 是原生派发层从本地已测引擎、明确的模型与推理设置、固定指令策略、技能/工具及网络权限得出的配置承诺，不携带指令正文、主机路径或凭据。缺少明确的派发设置不生成该字段，旧 PLAN 不回填。`routeSha256` 标识本地配置的模型和网关，不是实际供应商/计费身份，也不等同于 Economy 价目版本。以后的 READY 判断必须另核确认配置、参考路由绑定、全部成员及来源覆盖；仅收到这组摘要不得升级覆盖策略。

### 4.3 样本和估算器

不训练大模型、不部署Python推理进程。由Economy内的普通Java估算器消费已准备的结构化特征和样本。

新增整事项`economy_task_cost_sample`投影（名称为实施目标，不表示已建表），以可信scope/owner/task/已确认报价及初始特征绑定；唯一键防止重复入样，具体生命周期及成员闭包见§4.3.1。一次执行只是其明细，不单独作为整事项训练样本。默认只使用本Owner可访问历史及平台明确批准的基准，不能为提高命中率跨用户共享私有任务特征。跨Owner统计必须另有明确的数据授权与去标识规则，本次不默认启用。主要字段：

- featureVersion、estimatorVersion、任务特征摘要、执行配置/路由版本、技能/工具配置摘要；
- 全部成员执行/请求计量引用、工具计费单位引用、coverage状态/原因、API事项验收终态、完成时间；
- 样本来源BENCHMARK/HISTORY、入样/退役状态；不保留未授权用户正文。

特征仅取需求文本向量、显式目标、输入文件数/类型/byteLength、确切版本及明确要求的交付数量；未知交付数量保持未知，不能默认1冒充用户事实。新记录可与已知数量的相似样本比较，但缺失特征计入距离/可用性判断。byteLength不得换算成“已读token”。

分组与计算：

1. 按执行配置/路由、工具能力/计费方式兼容性及featureVersion分组；不用角色姓名分组，不拿低价模型样本直接换一个模型单价。
2. 在同组内按文本与结构化特征找近邻；标准化尺度从训练样本取得，缺失特征不填0伪造相似。距离权重、邻居数、最小有效样本数和最大适用距离写入版本化配置，由验证集选择，不拍脑袋塞复杂度系数。
3. 每个样本按**逐响应**当前参考价重算，再加实测工具单位价；不能把所有响应token合并后套一个上下文阶梯。现有`ModelTokenPrice.cost`支持单请求阶梯，`estimateCost`明确只用整任务基础估价，两者不能混用。
工具计量按原始外部操作身份及`chargeComponentId`去重，明确`billingBasis=TOKEN|UNIT|EXPLICIT_ZERO`；同一费用只能选择一种依据。只有渠道合同明确不同费用组成时才可为同一操作叠加不同component，不能把同一图片调用同时按图片token和图片张数计费。普通模型响应与另一次图片调用可以分别收费，但必须有不同的真实操作归属。

工具记录含unit、quantity及`REPORTED|MISSING|NOT_INVOKED`：未调用必须由独立调用清单证明，已调用未报告量保持MISSING；价格已知也不能补0或按交付物数量猜。工具和模型都按样本逐操作与本次参考价快照重算，缺计费方式/单位/所需价目则不可报价，不混用历史实付单价。

4. 近邻的重算任务总额做归一化距离加权均值。`estimatedYuan = sum(w_i * repricedSampleYuan_i)`，`sum(w_i)=1`；BigDecimal计算，最终沿现有规则一次`ceil(estimatedYuan*100)`得到整数WEN，不增加最低价或暗藏风险加价。
5. 样本数量、距离、独立留出集误差满足当前版本标准才AVAILABLE；无样本、分布外、证据不完整、未知所需工具单价则UNAVAILABLE。不得回退生成式估价、固定token数或静态每交付物工具数量。
6. 快照固化样本ID/修订和权重、特征摘要、配置版本、逐请求参考价格版本、估算额/误差摘要。样本或价格随后变化不能重算已经确认的报价。
7. 执行模型/路由、工具配置或计量协议改变即切换样本分组；旧样本不无条件混入。新真实结果按时间监测误差和覆盖率漂移，超出已校准范围的分组停止自动报价并补基准；网关隐藏路由变化不能仅靠本地配置摘要排除，明确保留这一外部不确定性。

冷启动先做经成本授权的代表性真实基准：覆盖当前确实支持的任务、规模、配置和工具。训练/校准/留出按模板族及时间隔离，同一任务改写或重试不能泄漏到两边。没有基准的分组暂不可报价，不能把“没有有效用户”当作已有训练集。数据不足影响可报价覆盖率，要与误差一起公开评估，不能只挑容易报价的案例报告准确率。

#### 4.3.1 整事项样本边界与生命周期（R3-01修订）

**预测对象是完成整事项的执行参考成本，不是一次模型回合或一次Runtime执行。** 采用`TASK_LIFECYCLE_V1`：从已确认固定quote对应的初始需求/资料快照开始，到API权威正式验收完成，包含原报价承诺的正常追问、修改、失败重试和重新生成。用户取消及长期未完成者只作取消成本/覆盖率等独立统计，不作为完成事项的低价训练标签。成本是该范围全部独立实际操作按同一参考价快照重算后相加；模型/工具费用互斥规则不变。推荐、报价Embedding等承办前平台开销不进入该预测目标，单独记录，不在确认后隐性追加收费。

将原拟议`economy_task_execution_sample`**替换为整事项投影`economy_task_cost_sample`**，不并列保留两个同义训练来源。执行/逐请求明细沿原usage及§4.2.4的capture记录留存。唯一键为可信scope+owner+taskId+最终确认的quoteId+sampleDefinitionVersion；sampleRevision是同一样本修订，不是新增样本数。没有正式quote/确认的BENCHMARK可在独立基准授权记录下使用固定benchmarkCaseId作为等价绑定，仍须声明整事项完成标准及真实执行闭包；探针合成值、旧LEGACY_FREE和无法绑定初始特征的历史不得自动入选。

| 字段/事实 | 类型与来源 | 用途/空值语义 |
| --- | --- | --- |
| sampleDefinitionVersion、featureVersion、estimatorVersion | 非空版本字符串 | 初版定义固定TASK_LIFECYCLE_V1，算法/特征版本独立 |
| sampleId、sampleRevision | 稳定ID、正十进制字符串 | 同一整事项只有一个当前版本；原修订不可覆盖 |
| quoteId、initialRequirementSha256、initialInputSnapshotSha256、initialFeatureSha256 | 原quote ID及SHA；批准基准的quoteId为null并必填benchmarkCaseId，其余初始SHA仍必填 | 固定报价前可知特征；后续修改内容/最终回合数不能回填成预测输入，避免泄漏未来信息 |
| lifecycleState、terminalFactId、terminalFactRevision、closedAt | ACTIVE/ACCEPTED/CANCELLED；API可信事实ID/版本及毫秒时间 | ACTIVE的终态字段为null；ACCEPTED须对应正式验收完成，不由Runtime退出码或资金CAPTURED单独推断 |
| membershipRevision、executionCount、executionSetSha256 | 十进制字符串及SHA，由Agent执行责任层产生 | 集合项为可信executionId/runId/captureId及归属摘要；不能由收到usage的条数反推集合 |
| evidenceRevision、projectionRevision、sampleState、reasonCodes | 十进制字符串、WAITING_EVIDENCE/READY/EXCLUDED、字符串数组 | READY须业务验收、集合封闭、全部计量完整且版本相等；其他状态不进入近邻集 |
| executionConfigSha256、routeVersion、toolConfigSha256、capturePolicyVersion | 固定兼容组事实 | 确认快照与全部成员的实际配置相符才属于该组；未知或中途换组按下文排除 |

**权威执行集合由Agent提供，不能让Economy扫描Agent表。** 在原确认/原生执行注册/正式验收/取消入口接入窄的样本生命周期通知：确认原quote时固化初始特征；每个正式任务执行在原业务授权事务内登记归属及membershipRevision，再允许dispatch。执行ID已有幂等重放不再增计；原执行恢复/重复投递仍为同成员，真实新run是新成员。Runtime内部子调用/子来源归其capture，独立API子执行则作为另一成员登记；同一外部响应仍只计一次。历史私聊复用成果不把原私聊调用移入新事项收费范围。

正式验收或取消沿现有任务root事务冻结成员集合的revision/count/digest并提交终态事实，正常返工不是终态。原事务后的既有投递/调度以这个固定事实幂等交付Economy；发送失败保留可重试标记，不能靠内存回调宣称通知成功。API阻止新业务执行注册越过该终态fence，已登记且在途的执行仍须停止/完成并封存capture；**业务验收/固定扣款不等待用量**。Economy必须收到完整成员明细及相同revision的终态集合摘要，才能判断任务集合封闭；没有生命周期通知仅保持WAITING，不能由现有cost pending=0推导完成。

- ACCEPTED＋集合封闭＋所有成员capture COMPLETE＋相同兼容组，才生成READY。1元首轮与2元返工在同一事项下构成一条3元标签，不能作为两个1/2元标签平均。READY表示样本事实可选，不等于该组样本数量/效果已经允许自动报价。
- 失败后重试成功的事项：失败轮若有完整用量也必须并入；失败轮用量未知则整个事项WAITING或EXCLUDED，不能丢掉失败轮后标完整。已登记但未启动者也不能凭“没有usage”计零；只有原dispatch责任层能证明从未交付、派发已撤销且不会迟到启动时，才提供明确NOT_DISPATCHED终态证据作为零调用成员，否则等待。该证明必须绑定execution/run、原派发记录修订及不可再领取的fence，不接受Runtime自报“没看到调用”。
- ACTIVE始终WAITING；CANCELLED为EXCLUDED/CANCELLED_OUTCOME，不训练完成成本；已验收但某来源永久SEALED_INCOMPLETE则EXCLUDED/USAGE_INCOMPLETE。这些记录及成本仍保留审计，并单列覆盖率分母；不把取消成本加到其他用户报价，不加风险系数。
- 中途换模型/路由/技能计费配置，或初始配置未知：整事项EXCLUDED/MIXED_EXECUTION_CONFIG或CONFIG_UNKNOWN。初版不把旧模型token按新模型价格猜测补齐、不将同事项拆成多条完成样本；后续支持混合组需独立版本和验证。排除不改变已确认固定报价/执行权利，偏差风险由平台承担，不重新预占。
- 迟到证据/合法修订到达后，§4.2.4的接收事务先使原READY不可选；按**同一sampleId的新revision**重聚合。旧quote保留原样本修订及价格快照。发现成员遗漏或终态集合冲突则EXCLUDED/EXECUTION_SET_CONFLICT，走原业务责任层修正事实，不能由统计器补造成员或另行启动任务。

报价初始特征与完整结果跨事项划分训练/校准/留出，同事项全部run、重试、修订及模板族必须同侧。独立留出真值也采用上述整事项闭包；计量可靠但取消/未验收的数据只报告单独统计。新增成员、终态及usage三个异步来源可以乱序，但只有三个维度均闭合才READY；没有真实样本时仍不可报价。

### 4.4 独立报价接口与事务

新增`POST /agent/tasks/{taskId}/quotes`，请求`expectedTaskVersion: string`、`agentIds: string[]`（非空且去重，必须在当前可授权候选内）。不接收客户端金额、模型、样本或tenant；不要求生成式推荐先成功，保留手选报价路径。

**报价批次幂等**：按公共规范携带`Idempotency-Key`，Web为一次明确取价意图生成并保存key/requestId；网络重试保留，重新取价才新建。服务端在原报价持久化边界保存批次记录（扩展既有领域持久化，不另建通用幂等服务），唯一约束为可信主体/scope＋task/操作＋key；输入摘要由expectedTaskVersion和排序去重后的agentIds形成，记录响应顺序也按规范化ID顺序。

认证/资源访问授权通过后，**先查已提交批次**：同key同摘要返回原完整响应（包括UNAVAILABLE原因、observedAt、recommendationId及全部quoteId），不先按当前价目/样本重算；同key异摘要409。新批次在原任务事务中原子保存批次结果和各候选报价；并发相同key仅一个提交，其他读回赢家结果。锁外并行重复准备允许，但不产生多批报价或额外模型执行。准备失败而未提交不能伪造成功回执；任务/权限变更仍按责任层处理，不泄露原数据。旧批次可读回不代表其仍能承办，确认入口继续核对当前任务/授权。

新样本可用或价格变化后，原key仍返回旧UNAVAILABLE/旧价格；用户明确重新取价才换key。不把公共requestId当幂等键，也不依赖客户端在丢响应后知道服务端生成的recommendationId。

响应`taskId/taskVersion/observedAt/quotes[]`，每项：

| 字段 | 类型/约束 |
| --- | --- |
| agentId | 本次已授权候选ID，每个请求ID恰好一项 |
| state | AVAILABLE或UNAVAILABLE |
| quoteId | AVAILABLE时非空，否则null |
| recommendationId | 服务端生成的报价批次绑定ID，沿用现有确认接口字段；不是客户端授权凭证，也不声称经过模型推荐 |
| amount | AVAILABLE时现有Money.wen整数结构，否则null；明确0与未知不同 |
| unavailableReason | AVAILABLE时null；否则NO_BASELINE / OUT_OF_DISTRIBUTION / USAGE_INCOMPLETE / BILLING_ROUTE_MISSING / PRICE_MISSING等明确业务原因 |
| estimateSummary | 可公开的method/version/sampleCount/qualityStatus；不返回他人任务ID/样本正文；不可用时可为null |

处理顺序：鉴权后先查原批次 → Agent锁外按§4.4.1独立准备可信特征及候选执行配置 → Economy估算 → 短任务事务内复查需求/资料/授权和报价准备所依赖的配置版本 → 固化不可变报价。共享特征准备失败沿§4.4.1返回真实502/503，不固化候选UNAVAILABLE批次。候选局部基线/价格缺失不取消其他候选报价；数据库/权限等全局故障返回真实错误，不吞成UNAVAILABLE。重放仍先读取原不可变报价，不用当前价目覆盖。

在报价首读和固化复核两个短事务中，Agent 需求服务直接使用本次授权锁回调给出的原事项根，按租户、客户端、所有者、事项及根版本读取当前需求，不再次查询并锁定同一根。事务活跃标志不能证明持有哪些行锁，不能传入自行构造或先前事务缓存的根；锁外调用仍由需求服务自行取得根锁。该优化不省略固化前复核，也不把估算移入事务。

新prepare与persist职责需要在`TaskBillingService`/`TaskPricingService`内部明确拆开，不能将原逐人quote循环换个方法名后仍在锁内检索。 锁外prepare返回Economy-owned不可变`PreparedEstimate`：精确人民币值及WEN、全部样本修订/权重、逐响应/工具互斥组成、完整价目快照（或具备不可变保留保证的引用）、输入摘要/配置版本和估算方法。锁内不重新读取已可变的计算输入，只复查权威版本并在同事务保存整个批次及各项快照；任何持久化失败整批回滚。Economy不读取Agent表。价格准备的版本冲突只影响当前报价，不自动重试产生新费用。报价不扣款；预占/确认/结算/取消继续原金融事务。

Web先显示推荐，再对当前选择/需要展示的候选批量取价，不强迫首屏等全部108人报价；两路分别做身份/任务版本/请求代次隔离。只有所选候选AVAILABLE才可确认。切换选择、任务变化、页面销毁后迟到报价不得覆盖当前选择。无金额显示“暂不可估算”而非0文。

#### 4.4.1 独立报价的特征准备及失败语义（R3-03修订）

**独立不等于重新造编码器。** Agent应用服务在锁外准备`TaskFeatureSnapshot`，通过Agent API内的窄端口（拟命名`TaskFeatureEncoder`）请求编码；实现放在现有Chat/Spring AI适配侧，沿原Agent接口、Chat实现的依赖方向，不让Agent反向依赖Chat service，也不让Economy调用Embedding。推荐与报价共用这一端口及作用域缓存，但两者可以独立首次调用；绝不调用recommend来取得预算前置结果。

内部快照中的ID/摘要/版本按原强类型对象传递，向量不由Web上传。快照包含`featureVersion/textTemplateVersion`、可信需求与资料摘要、`textSha256`、`embeddingIdentity:{providerConfigVersion,model,dimensions}`、`vector: float[1024]`及已定义结构化特征。向量只允许有限数、确切维数及对应代次，缺失不填零数组；模型身份沿§1已选配置。初始报价快照保留这些不可变特征供后续整事项样本使用，不保留私有原文。向量仍属私有衍生数据，沿Owner隔离和原任务授权保管；不能因为是向量就跨用户共享。

1. 先完成当前调用方鉴权/原事项访问核验和批次key查询。**存在同key同摘要的已提交批次，直接返回原响应，连新特征、当前价目、样本列表和网关都不访问**；不同摘要409。已经确认的历史回读不受当前模型配置影响，但仍受资源访问授权约束。
2. 新批次读一次当前任务/确切资料快照，按§3.2同一规范化模板构造文本；候选数不增加文本编码次数。相同可信scope/owner、规范文本SHA、model/dimensions/provider配置代次和模板版本合并在途请求。热命中0次Embedding，冷请求最多1次实际外发；不启隐藏重试或切其他模型。推荐已建立缓存仅是可选命中，不是前置条件；摘要不符或模型代次不符视为未命中。
3. 编码在任务事务外执行；复用现有传输配置和取消机制，网络失败/超时返回下表，不将§6的P95目标直接当强制请求deadline。单个页面取消只释放本订阅者，不取消仍被另一报价/推荐订阅的共享请求；失败移除在途占位，不缓存伪成功。规范化只发送本次已授权的最小文本，不额外读附件正文。
4. Agent把版本化快照及候选配置交给Economy；初版估算方法必须有同代次文本向量，**不支持缺向量时偷偷改成纯结构化距离**。候选缺基线/价目仍为局部UNAVAILABLE。锁内仅复查权威输入/配置及所选样本修订，整个报价批次原子持久化。

| 情况 | HTTP / 业务结果 | 是否固化批次及重试 |
| --- | --- | --- |
| 已提交同key同摘要，网关不可用 | 200/E0，原完整响应 | 不新建批次/向量，不重新报价 |
| 新批次共享编码连接失败/超时/上游限流 | 503 `QUOTE_FEATURE_UNAVAILABLE` | 不写报价批次；Web显示“预算暂不可用，可重试”，保持key/requestId，用户重试可恢复；不自动循环 |
| 网关成功但向量维数/数值/模型代次非法 | 502 `QUOTE_FEATURE_INVALID` | 不写批次/不缓存；告警，不显示0文或候选无能力 |
| 授权失败/任务不存在/观察事实变化 | 沿原401/404/409 | 不返回旧私有数据；409刷新事实，新的明确取价意图再换key |
| 向量正常，某候选无样本/缺价/分布外 | 200/E0，该项UNAVAILABLE，其余独立 | 固化原完整批次；将来重新取价用新key，同key仍回放原UNAVAILABLE |

同key并发准备允许共享同一编码；若某请求准备失败而另一请求已提交，失败返回前可读回已提交同key结果（仍核对摘要/授权）。否则真实失败不留成功回执；再次重试仍先查批次。Web沿独立预算请求代次隔离迟到结果，不把预算错误覆盖为“推荐失败”，也不清空仍有效的用户手选。报价延迟指标新增`featureCache/featureEncode`分段；§6单选500ms目标明确为特征缓存热且样本已准备的路径，冷编码耗时及失败另列，不能将Embedding时间排除后冒充端到端耗时。

## 5. 历史测试数据清理

**推荐优化不依赖清空历史账本。** 新索引/新样本版本天然隔离旧数据，不把兼容历史成本当新算法前置条件。

1. 生成明确任务/执行/报价/用量ID清单及依赖只读报告，不按全库时间或状态猜删除范围。
2. 经现有取消接口释放目标HELD；CAPTURED不自动退款、不手改钱包余额。核对原交易引用及余额/冻结差额不变量。
3. 确认目标执行停止、STOP/outbox收敛，按§4.2.3在原writer gate下先source-only补采并验证finalized，再flush剩余原始用量；保持原auth绑定。取消已提交而Runtime仍运行、缺采集证明或pending/error非0，均不得删来源。pending=0单独不是可删证据，coverage/价格未知不等于投递未ACK。
4. 对仍被task/grant/assignment/replay引用的quote/charge和用量幂等证据，**本次保留**并排除新样本。无引用、无迟到重放来源的测试派生行可物理删除；先从派生/子记录到父记录，使用限定ID事务，数量不符则回滚。
5. Runtime receipt、原始provider源文件及复制journal不可分别删除。无法证明全部重放来源已退役时，保留该执行证据，不制造回传风暴或重新入账。
6. 清理后验证：目标派生行变化符合清单；保留账户/资料/聊天/记忆索引不变；无悬挂引用；迟到重复投递不增加成本或扣费；重新启动delivery不会重建已清理数据。

若需要连仍被引用的账务及执行证据也全部删除，必须另行明确相关任务/执行闭包范围；当前窄范围授权不等同全库重置。不为本次清理新增通用退役框架，不提供绕过业务释放的TRUNCATE脚本。

## 6. 性能、准确性与DFX验收

以下数字是**建议验收目标，不是已测结果或无条件承诺**。实施前固定数据规模、并发和版本；不以测试不足证明达标。

| 维度 | 验收方法/建议目标 |
| --- | --- |
| 推荐延迟 | 当前候选规模及108候选合成边界分别测，区分缓存热/冷；并发1/5/10。热缓存P95≤500ms，冷请求P95≤3s作为优化目标；上游延迟单列，超时/降级计入结果，不只统计成功快请求 |
| 报价延迟 | 样本已准备、单选及批量候选分别测，特征热/冷分组；热特征单选P95≤500ms作为目标，冷特征编码计入端到端另报；不含新基准执行，不在请求中采样或重算整个历史库 |
| 查询/调用规模 | 热请求0次Embedding，冷请求≤1次；无逐候选Embedding/LLM。候选SQL按批次增长，记录批次数/扫描文档数/锁等待，而非只比较接口总时间 |
| 推荐质量 | 独立人工标注留出集，HIGH precision目标≥95%、Top3适配候选覆盖目标≥90%；同时报告样本数、置信区间、UNKNOWN率、无匹配及降级分组，不把RRF分数当概率 |
| 预算误差 | 独立真实整事项留出集，WAPE目标≤25%、P90相对误差≤50%；零实际成本单列绝对误差；同时报告低估率、可报价覆盖率和每组样本量。小样本只能标试验结果 |
| 计量可靠性 | 重复通知/投递不重复记费；同ID内容冲突可见；失败/中断有用量仍记；缺失不变0；正常/压缩/子执行/恢复覆盖；cleanup前持久化及崩溃重放可恢复 |
| 安全 | 授权过滤前置、撤权即时失效、索引/缓存分区、秘密和正文不入日志。Embedding仅发送本次明确的最小文本，不新增附件外发 |
| 可维护性 | 参数/特征/索引/样本/价目均有独立版本；通过现有配置/调度管理，不按人物或Provider品牌在通用层编排业务 |
| 资源 | 不增加常驻推理进程；1024 float32仅原始向量为4096B/条（1万条约39MiB），不是ES/JVM总占用保证。现有256MiB ES heap下测实际文档规模、GC、RSS和并发；未测前不扩容或宣称够用 |
| 可恢复性 | 新能力索引可从授权事实重建；旧聊天索引不动；失败停用新算法并明确不可用，不恢复隐蔽LLM；发布/回退须按§7.1同时约束API/Web、Runtime生产端及usage/quote持久格式，成本原始证据不因回退被覆盖 |

数据库负载验证仅在测试自有实例、单一测试库的独立请求窗口中取计数差。按库汇总 SELECT 次数、检查和返回行数、语句累计耗时；行锁等待次数和毫秒为专属实例的 InnoDB 计数。累计时间可跨并发请求叠加，不是单次请求的锁等待或 P95；不采请求正文、SQL 实参，也不要求生产开通逐句日志。

指标沿现有日志/metrics接入：candidateRead/embedding/lexical/vector/rank/estimate/persist耗时、缓存命中、索引版本滞后、UNKNOWN/UNAVAILABLE原因、用量遗漏/冲突/待投递数及重放次数。标签不含任务正文、密钥或高基数原始用户ID。

### 6.0 用量细粒度记录：本轮存储诊断及设计约束（2026-11-23）

已做两轮**隔离、小规模、非生产负载测试**：控制机普通ext4目录，各40个模拟调用/80条小记录；同步轮调用当前工作树的`SkillExecutionStore.write`，异步轮只在任务目录内实现相同file sync→rename→directory sync顺序的I/O原型。每轮测量窗口约1秒，无网络/付费请求；没有进行Runtime产品构建或修改业务源码。模拟token是夹具，不能进入预算样本。

| 指标 | 当前同步存储 | 异步I/O原型 |
| --- | ---: | ---: |
| 单条记录持久化样本P50 | 5.460ms | 5.400ms |
| 单条记录持久化样本P95 | 12.893ms | 13.595ms |
| 连续两条持久化样本P95 | 21.584ms | 30.011ms |
| 写入前已调度的immediate回调等待样本P95 | 21.649ms | 0.402ms |

结论只支持：**同步写盘会阻塞当前Node事件循环；异步等待可让该回调先得到调度，但不能消除磁盘等待。** 这不是端到端延迟改善证明，不能从分时小样本声称异步一定更快。真实请求的开始/结果通常相隔模型执行时长，连续两条写入仅用于展示阻塞，不当一次模型请求增加的真实时间。这两轮存储测试未测并发、崩溃恢复、数据库和长期负载；后续来源协议探针与U1状态见§4.2.1及§10，不由本节I/O测量推定。

两轮均读回80条记录，异步/同步对应文件字节完全一致。每轮正文合计30201B，文件分配327680B（320KiB），尚不含目录/回执/数据库；不能只按JSON字节推算总空间。整进程RSS没有独立导入基线，不用作新增日志内存结论。源码摘要和完整测量结果保存在`/home/isp/tasks/cyf-embedding-openai-20261123/usage-storage-probe/`，按72小时任务TTL处理；正式裁决留在本文，不把临时探针提升为新runner。

据此约束正式实现：

- **存储体系复用，热路径不机械复用同步函数。** 当前`SkillExecutionStore.write`采用同步文件/目录fsync；逐调用热路径应使用可等待的非阻塞持久化实现，同时保留身份、目录权限、原子写入及落盘确认。不得批量替换无关既有检查点，也不据此启动独立CPU推理服务。
- **记录先可靠保存，再发送请求。** 异步是让其他工作能运行，不是先发模型请求后补日志。写入失败只阻止受影响调用，不能绕过记录继续外发；结果无法持久化则保留来源并标不完整，不能把模型请求重新执行来“修复日志”。
- **并发顺序明确。** 每个来源的序号与关闭操作串行化，生产者等待自身持久化确认，不能堆积无限内存记录。跨来源可并发，但关闭必须等待全部来源确认；group commit未实现/未测，不计入收益，只有真实负载证明需要才增加。
- **存储层与来源层分别验收。** 本节写盘原型不证明能拦到实际调用；来源方案和后续真实二进制探针见§4.2.1的Runtime计量出口。异步I/O测量本身不授予COMPLETE或关闭U1。
- **性能测试分层。** 固定来源适配后，通过既有非生产入口测预写P50/P95/最大值、调度延迟、上报积压、数据库事务及文件/inode增长；与未启用采集的同输入基线比较。预算请求只读已汇总样本，不能在请求中扫描来源日志。当前没有依据承诺新增延迟/内存的硬数值上限。

### 6.1 效果验收的可计算定义

- 标注以固定任务及当时授权能力事实为单位，预先定义可接受承办集合和资料不足情况；包含短描述、多附件、否定/条件需求、同义表达、只有单项相关但无法覆盖整个需求等负例。不能用待测排序器自己的输出生成正确答案，不能以检索相关代替完成能力。
- `HIGH precision = 标为HIGH且人工认定可接受的候选数 / 全部HIGH候选数`；`Hit@3 = 前三位至少有一个可接受候选的任务数 / 至少有一个可接受候选的任务数`。本文原“Top3适配候选覆盖”明确指Hit@3，不指召回全部合适候选的Recall@3。没有适配候选的任务另报误推荐率，UNKNOWN/降级比例及业务覆盖率同时展示。
- 参考价预算的留出真值为**§4.3.1同一已验收事项的全部成员执行完整计量，按同一版本参考价逐调用重算后相加的总额**，不是未知供应商实付。`WAPE=sum(abs(预测额-参考真值))/sum(参考真值)`；P90相对误差在正真值样本上计算，零真值单列绝对误差。实际成本对账是另一项验收，不能由参考价预测误差替代。
- 无HIGH输出时precision为不可评估，不是100%；没有有效留出样本或WAPE分母为0时不能报告误差达标。输出样本量、置信区间与分组结果；是否达标按实施前固定的判据，不用小样本点估计冒充精度保证。
- 数据集、划分、评分脚本及价目快照绑定版本；本轮U1设计证明不替代正式来源接入，基准采集只有在该来源实际实现并验收后才可能形成完整样本。未经授权的付费执行不因“需要验收”自动启动。


## 7. 代码改动清单及实施次序

| 批次 | 实际落点 | 验收/依赖 |
| --- | --- | --- |
| A 配置准备 | 核对dev/grey现有配置，仅修改尚未切换的prod及部署外部embedding密钥覆盖 | endpoint最终拼接为HTTPS `/v1/embeddings`；复用加密凭据、不写入Git；环境readback和维数验证。已有200不等于已切生产 |
| B 推荐/接口 | Agent推荐service/controller/DTO、候选/技能批量接口、ES适配及调度；Web `hallAssigneeRecommendation.js`、`useHallData.js`、`BountyPanel.vue`、`useHallPointAndStart.js` | 新索引准备与标注集；删除模型调用及内嵌quote，不改授权责任 |
| C 真实用量 | 既有Runtime受限出口的Responses计量处理、隔离provider配置/临时凭据、native-execution与releaseAdapter收尾及usage receipts；API对应source adapter、§4.2.4 capture接收/ACK与现有usage ledger | 固定引擎/来源协议版本；实际出口不可绕过、预写/结果/关闭持久化、去重/coverage及全链路回归；不fork引擎、不重做失败模型请求 |
| D 预算 | Economy整事项样本投影/估算器、TaskWorkload/TaskPricingService/TaskQuoteCalculator/TaskBillingService；Agent确认/执行登记/验收/取消的生命周期通知与独立quotes特征准备 | Runtime完整用量、Agent封闭执行集合及获授权基准；Economy不依赖Agent，Agent传可信特征；冻结新报价快照 |
| E 清理/验收 | 既有取消/释放、delivery及限定ID清理操作 | C已确保不会清掉唯一证据；只读清单与实际执行结果分开；不要求先清库才能测试 |

B与C可独立开发，但新Web预算功能必须配套D，不以部分安装冒充全部完成。当前无旧客户端兼容需求，部署时用同一获授权固定候选协调API/Web切换，不添加双轨HTTP分支。

测试复用现有入口：Agent `AssigneeRecommendationServiceTest/ControllerTest/RecommendationMaterialsTest/AssigneeRecommendationQuotesTest`及新的独立quotes用例；Economy `TaskQuoteCalculatorTest`、价目/报价/资金/usage定向回归；Runtime现有`app-server-usage`、`native-execution`、`native-execution-profile`及usage-delivery测试；Web推荐、报价、迟到结果及组件行为测试。退休的生成式ModelTest不再当新排序效果证明，仍在使用的其他聊天模型链不顺手删除。

必要测试/构建/打包沿现有SSH worker及编排工具，先读build.gradle、plan-only、串行Gradle和validateLayering；遵循根AGENTS单次600秒规则，不跑付费Flow或控制机重型构建。纯本文更新只做文档检查。

### 7.1 三端切换及不可逆数据边界

- 固定API接收端、Runtime生产端、Web及数据库/原始store格式版本的同一发布清单。先暂停本次受影响的新任务/报价受理并排空旧执行与投递，再安装API接收能力、Runtime新生产能力，最后成对启用API/Web新接口；暂停范围只限实际受影响入口，不改身份或其他任务。未确认排空则不开始不可兼容切换，不做新旧双轨客户端。
- **切换边界是数据，而非进程启动成功。** 第一条新usage/checkpoint/ACK或新quote快照持久化后，仅当旧候选已证明可安全读取并继续这些精确格式，才允许程序回退；没有证明就默认不兼容。不能把“原始字节仍在”当兼容性证明。
- 不兼容时走既有forward-only前修，保持受影响入口停止/明确不可用，保留新记录及待投递来源，禁止旧reader领取；修复同格式候选后从原receipt/修订继续，不重跑模型、不恢复覆盖新账本的数据库备份。
- API安装器已有`CYF_API_FLOW_FORWARD_ONLY`保护，但本次实际LOCAL编排、Runtime安装和回退路径必须在plan-only及隔离失败演练中验证传递/等效保护；若未覆盖，只修改原入口，不绕锁、不伪造Flow身份。未验证前不能宣称回退链已适配。
- 新格式尚未落盘时也须核对版本/状态后才回退；Web旧包不能独自配新API。故障用例必须包含已有未ACK新修订、API安装失败、Runtime安装失败与Web失败，确认旧reader不消费、恢复后只投递一次。


## 8. 行业实践取舍与来源

本轮直接获取并检查以下官方资料，抓取摘要保存在任务目录；网页工具未返回可用引用，不伪造检索引用编号。

| 官方来源 | 借鉴点 | 不照搬的部分 |
| --- | --- | --- |
| Elastic script_score文档，`https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-script-score-query` | 精确向量计算工作量随匹配文档数增长，故先限定授权候选范围 | 不在256MiB heap上直接全库扫描或凭空保证耗时 |
| Elastic RRF文档，`https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion` | 通过排名融合不同召回分数尺度，参数版本化 | 本机许可证不支持原生RRF，故API实现同类排名融合，而非依赖付费能力 |
| Stripe用量记录文档，`https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api` | 稳定事件身份、幂等上报、异步汇总与可见性延迟分离 | 不引入Stripe付费产品或重建钱包；应用于现有usage ledger |
| OpenAI Codex固定源`openai/codex`，tag `rust-v0.167.0`，经GitHub contents API取得 | 逐响应事件与持久化记录交叉核对；按已部署版本适配而不是猜通知累计语义 | internal-only事件不当长期稳定公共协议；requestedModel/amount不冒充完整实际账单 |

OpenAI公开Embedding指南本轮HTTP403，未据此宣称当前官方文档已验证；模型/维数连通性依据此前真实网关探测。网关兼容性和生产凭据仍由部署验证负责。

## 9. 收口状态

- 已完成：当前链路/部署限制调查，推荐与预算分开设计、行业实践取舍及用户要求的一轮独立评审；原稿的合同缺口及裁决见§10。
- 前轮设计关项（历史）：首轮12项在设计层修订，U1依据选定的Runtime内计量出口、固定真实Codex＋模拟上游9场景及独立定向回读关闭。正式来源接入与全链路验收尚未完成；付费基准仍需实际授权，网关实际计费模型/口径未知不能靠参考价补齐。
- 未完成且不能提前声称：新代码、真实基准集、独立质量/压力测试、清理演练、配置切换、部署与线上业务验收。

当前设计结论以§11.7修订回读为准：R3-01–03已补入正文并定向回读闭合，R3-04入口状态已统一；没有将前轮13项关项直接当本轮通过。实际预算样本仍须等待正式来源接入及验收，不能使用探针合成token。设计、代码、测试与上线状态分别报告。

### 本轮文档验证

- 两个责任专题的`./sddw check-docs <feature>`均通过；本次改动的`git diff --check`通过。
- `./sddw check-docs --all-docs`未全绿：全局回归手册引用的旧任务`full-r5/report.md`、`full-r5/verification-summary.json`缺失。未修改该手册或伪造旧证据；本次新详设可达，无新增不可达当前文档。
- 未运行应用构建或业务回归；不把文档检查当推荐质量/报价误差/资金验收。


## 10. 2026-11-23独立方案评审（用户单次要求）

> 本节为前轮历史记录，其中“当前”“全部闭合”指当轮固定输入与审查范围；最新整体结论见§11。原回执和裁决不改写。

此前只有Owner自检；本轮由三个独立只读评审任务分别审查架构/推荐/API、预算/计量/账务、Runtime恢复/清理/DFX。三者原始结论均为**有条件通过**，不是默认批准。本次不新增永久Reviewer角色、审批或常规重复构建阶段。

原稿SHA-256：`3cf3f6162fb2af5f3cc706bd2628c673ea57877ac33d4a28840c4cedb735fb2c`。原稿、源码基线摘要和评审材料存于`/home/isp/tasks/cyf-embedding-openai-20261123/design-review-r1/`。评审所用未提交源码不冒充固定发布候选。原稿发现13条意见，去重为11项；Owner补充2项验收/文档问题，共13项（8项P1、5项P2），未报告P0。

| 编号 | 严重性/来源 | 问题与裁决 | 状态 |
| --- | --- | --- | --- |
| R01 | P1 / A1 | 候选最佳证据先聚合、跨批全局排名，再RRF；禁止文档TopK截断。见§3.2 | 原评审者回读确认设计闭合，待实现测试 |
| R02 | P1 / A2、B5 | 报价Idempotency-Key原子绑定完整批次，先重放后查价；prepare冻结全部依据。见§4.4 | 原评审者回读确认设计闭合，待实现测试 |
| R03 | P1 / B1 | COMPLETE须有独立预期调用与来源闭合证明；本轮新增选定路线及真实二进制探针。见§4.2.1 | **U1设计层CLOSED；本轮独立续审PASS_DESIGN，产品实现待验收** |
| R04 | P1 / B2、C2 | 响应一对一账本attempt、修订/receipt/ACK合同；旧整执行与新来源不能双记。见§4.2.2 | 原评审者回读确认设计闭合，待实现测试 |
| R05 | P1 / B4 | 外部操作的计费组成互斥；工具缺数量不是0。见§4.3 | 原评审者回读确认设计闭合，待实现测试 |
| R06 | P1 / C1 | 预先持久化capture-plan、缺正向finalized即恢复；不能依赖异常时标记。见§4.2.3 | 原评审者回读确认设计闭合，待实现测试 |
| R07 | P1 / C3 | 取消停写后先补采再flush，区分采集/ACK/coverage。见§4.2.3及§5 | 原评审者回读确认设计闭合，待实现测试 |
| R08 | P1 / C4 | 三端版本及持久格式共同约束回退；不可兼容时forward-only前修。见§7.1 | 原评审者回读确认设计闭合，待失败演练 |
| R09 | P2 / A3 | READY/DEGRADED互斥矩阵及Web消费者规则。见§3.3 | 原评审者回读确认设计闭合，待实现测试 |
| R10 | P2 / A4 | 稳定内部证据键、事实摘要、固定索引读视图。见§3.1 | 原评审者回读确认设计闭合，待实现测试 |
| R11 | P2 / B3 | 实测单位、真实计费身份和参考价身份分离。见§4.1 | 原评审者回读确认设计闭合，待实现测试 |
| R12 | P2 / Owner | Hit@3/precision/预算误差真值与空分母定义。见§6.1 | 设计已修订，未测效果 |
| R13 | P2 / Owner | design/tasks/acceptance当前入口仍有旧生成式要求，改为新详设责任入口 | 文档修订，不重标历史证据 |

本轮发现说明原稿尚不足以直接实施完整预算，撤回将“方案收口”理解为无阻断的表述。修订不等于原有代码已经满足新合同；U1不因增加UNKNOWN状态或文字约束而关闭。

### 首轮修订回读（保留原结论）

原三位评审者对修订副本`bc2597bdfa28207830ea8653519b59e706ade02645bc81c0247e7e452ffab79d`做了定向回读：A1–A4、B2–B5、C1–C4在设计层闭合，限定范围未发现新增矛盾；B1/U1明确未关闭。该副本和原意见均留存在本轮任务目录，后续状态记载不改写原稿或回读输入。

首轮最终结论为**有条件通过**：独立评审去重11项中的10项设计闭合，Owner补充2项已修订，1项P1 OPEN。业务代码与故障演练未执行，不据此承诺完整预算可用。后续先验证U1的实际来源能力，再进入依赖完整样本的预算实施。


### 本轮U1定向续审：设计关项，不是实施/发布验收

原B评审任务不可恢复，本轮由一位独立只读架构评审者Goodall（`01a20822-fc9d-7170-bb32-16d7ebd11df2`）接续检查U1及来源切换对原合同的影响。固定回读输入方案SHA256为`b13a07af9d0a17223d7ed932caf3386a8c5541128986939c6d721700005b58a2`；探针及09批证据摘要见§4.2.1，输入副本与实际回执位于本轮`u1-feasibility-r2`任务目录。回读后的本文仅更新关项状态及本节回执说明，原输入和首轮材料不重写。

**评审结论PASS_DESIGN**：实际调用入口可接、正常能恢复完整、缺项能独立发现、崩溃保留未决；来源分类器不读oracle/通知，模型通知丢失不再成为发现调用的唯一依据。真实凭据保留Runtime、精确本地路由及禁止旁路、不可变execution/capture绑定、原ledger去重/修订、停止采集清理和回退边界均已明确，限定范围未发现遗留设计P1/P2或重新打开原问题。

因此本方案**13项评审问题均在设计层闭合，当前没有未闭合的设计P1/P2**。此结论是“首轮原三路修订＋本轮U1定向续审”的组合，不是声称原三位重新批准了新路由。未要求所有失败变COMPLETE；INCOMPLETE样本拒收是正常合同结果。

实施阶段仍必须完成：正式执行认证/跨执行隔离及上游HTTPS；声明支持的压缩、子执行、重试、流分片；Runtime→API→ledger ACK/修订/重启续采/cleanup；真实存储故障、并发关闭、背压/容量/性能与安装回退演练。真实网关/付费基准、推荐与预算效果验收以及生产发布后FULL回归均未由本轮替代。当前生产没有新计量出口，也没有因本轮探针取得可用于报价的真实样本。


## 11. 第二轮完整详设评审（2026-11-23，R3）

> §11.1–11.6保留修订前初审记录；当前修订状态与限定回读结论见§11.7。

### 11.1 范围、固定输入与结论

用户要求“再进行一轮详设评审”。本轮由Owner重新审读完整设计并对照当前工作树源码与现行资金合同，**不是新增独立评审者的签字，也不声称原三位评审者再次批准**。R3为证据目录序号，接续首轮评审和U1定向续审；本轮是第二轮完整详设评审。

固定输入为修订前401行详设，SHA256：`e3e1bdb0a96d396b1030c9ef9380b7e1630a3ad6453a1c4920b2ae401305ab69`。输入副本及源码文件摘要存于`/home/isp/tasks/cyf-embedding-openai-20261123/detailed-review-r3/`，沿72小时任务区规则退役；正式意见保存在本节。工作树有其他任务未提交修改，HEAD仅作定位，不是本轮源码全量身份或发布证明。下列行号均指固定输入，不指追加评审后的新行号。

**结论：REQUIRES_CHANGES，不能将整份详设判为全部通过。** 新发现4项：2项P1、2项P2；R3-04文档状态已修正，其余3项OPEN。没有撤销U1“实际发送入口能够建立独立来源”的可行性结论；本轮补查的是业务样本范围及跨进程合同等未覆盖细节。不是因为产品代码尚未实现就判设计不通过。

| 编号 | 级别 | 位置（固定输入） | 结论 | 状态 |
| --- | --- | --- | --- | --- |
| R3-01 | P1 | §4.3，193–213行；§6.1，304行 | 单执行样本与整事项固定报价的统计单位不一致，缺入样终态和聚合边界 | OPEN |
| R3-02 | P1 | §4.2.1 A、§4.2.2–4.2.3，132–186行 | 本地完整性清单缺Runtime→API具体投递/ACK/落库合同 | OPEN |
| R3-03 | P2 | §4.3，199–204行；§4.4，219–243行 | 独立报价需要文本向量，但没有独立取向量与失败契约 | OPEN |
| R3-04 | P2 | 两个主spec与design/tasks/acceptance当前入口 | 主spec仍称U1未闭合，与详设及其余入口状态矛盾 | CLOSED_DOC_ONLY |

### 11.2 R3-01：先定义整事项样本，不能把一次执行当完成事项成本

**证据与风险。** §4.3拟建`economy_task_execution_sample`，绑定task/执行快照、记录执行终态，并把近邻的金额称为“任务总额”；但没有定义哪些业务终态可入样，如何聚合一个事项下的多次执行、修改、失败及重生成。计量COMPLETE只证明观察范围内用量收齐，不证明用户事项已验收完成。

仍生效的`/home/isp/wsps/cyf/specs/agent-economy-marketplace/beta-wen-billing.md`第28–29行明确：单轮失败不结束预占，正常追问、修改和重新生成包含在原固定报价内。`/home/isp/wsps/cyf/api/economy/jia-economy-api/src/main/java/cn/jia/economy/task/TaskBillingService.java`的资金主键仍是Task，不能由一次Runtime退出代替事项结算范围。

**反例。** 同一固定需求先执行花费参考价1元，再修改花费2元，最后验收；两次执行分别COMPLETE。若各自作为整事项样本，均值可能为1.5元，而本事项参考真值是3元。提前取消但计量完整的0.1元执行若直接入样，还会把“未完成需求”的低成本当成完成成本。该反例是合同推演，未声称已发生线上错误。

**所需修订。** 在Economy样本投影及Agent提供的可信生命周期事实之间明确：预测对象/唯一键、报价对应的需求基线、纳入的执行集合、业务验收终态、取消/失败/仍进行中数据的用途、跨执行配置变化的分组策略，以及迟到计量/修订如何使投影等待或退役。可以保留逐执行明细，但完整事项样本必须另有确定聚合语义；不能简单删掉失败成本。§6.1留出真值须与该范围一致。不得借修订改成逐轮收费、补扣或强制结束正常修改。

**关项验例。** 同事项两轮1+2最终只形成一个3元的整事项训练观察；其中一轮用量未闭合则不产生完整真值；完整计量的取消事项不冒充已完成事项；重复和乱序投递不增加样本数/金额；跨配置处理有明确结果。具体样本准入方案须修订后回读，不能仅追加这些测试名称便关项。

### 11.3 R3-02：本地来源完整不等于API收到完整证明

**证据与风险。** §4.2.1定义了本地请求意图、epoch/sequence、关闭清单与未决项，§4.2.2给出的新wire则以逐响应`sourceAttemptId/sourceRevision/measuredQuantities`为中心，§4.2.3要求ACK后才能清理。尚未定义capture-plan、无responseId的请求、关闭水位/缺口/工具子来源及最终清单通过哪个既有操作/消息变体投递，字段类型与完整性绑定是什么，也未定义该清单的幂等身份、ACK含义、API落库及投影触发原子边界。

当前`/home/isp/wsps/cyf/runtime/conf/codex-bridge/native-usage-receipts.mjs`第14–38行只投递STARTED/TERMINAL并认revision1/2；`/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/NativeExecutionUsageCostController.java`第18–19行的Request/Receipt及对应Recorder也是旧执行用量合同。这些事实仅说明不能把“复用delivery”当现成闭合协议，**不是要求当前代码已经实现新设计**。

**反例。** A响应有usage并已ACK，B预写后没有responseId而终止。Runtime本地正确判INCOMPLETE，但若API只收到A，现有响应账本无法区分“只有A”与“A+B丢了B”。反向情况是最终清单先到、最后一条响应晚到，若没有原子可用性规则，可能错误入样；仅ACK响应也不能授权清理唯一最终清单。

**所需修订。** 在既有Runtime用量投递和API来源适配边界补充完整的版本化业务报文/持久化映射（不另造公共信封或通用框架）：来源计划/请求集合/最终清单的身份及摘要绑定、无响应尝试的表示、分批或一次提交策略、清单修订与ACK重放、乱序到达规则、API完整状态与样本投影的提交条件。API执行绑定继续归Agent，价格与样本投影归Economy，不把供应商协议解析复制到资金层。

**关项验例。** A已ACK/B无响应、清单先到响应后到、清单ACK丢失、同清单身份异内容、API在接收与更新投影之间崩溃、Runtime重启清理重放；既有统一接口v1.4下有逐字段正反例且生产者/消费者能作一致判断。U1原型无需为本项重新付费运行；缺的是正式跨进程设计合同。

### 11.4 R3-03：补全不经过推荐的独立报价路径

**证据与风险。** §4.3近邻距离必需“需求文本向量”，但目前明确的查询编码仅在§3.2推荐路径。§4.4允许不先推荐直接手选报价，流程只写“Agent锁外读取可信特征→Economy估算”。没有说明冷缓存下由谁通过既有Embedding入口构造向量、如何绑定模型/维数/模板版本，也没有说明网关失败时HTTP错误与候选UNAVAILABLE的区别。依赖推荐缓存会破坏独立生命周期；偷偷去掉向量又会改变已校准距离。

**所需修订。** 明确Agent侧可信特征准备复用既有Embedding适配/作用域缓存，或选定另一个不依赖推荐调用的实际路径；Economy仍只消费确定的版本化特征，不读取Agent表、不触发外部模型请求。规定冷/热路径调用边界、文本规范化与缓存身份、缺向量/编码失败的接口语义和Web重试行为；若支持无向量估算，须作为单独校准的方法而非隐式替代。已有不可变批次重放必须在新特征准备之前完成，不能因网关不可用失去重放能力。

**关项验例。** 从未调用recommend且缓存为空时直接quotes可按明确流程得到报价或明确失败；Embedding失败不返回0文、不写伪成功批次；既有同key批次在网关失败期间仍可原样重放；报价缓存不跨Owner泄漏任务文本。

### 11.5 R3-04：统一入口状态，保留历史结论

输入时推荐主spec与Economy主spec标题仍为“有条件通过，U1未闭合”，design/tasks/acceptance和详设标题却称全部设计问题闭合。会使不同组件按不同阶段安排实施。已将两个主spec和三个入口统一指向本轮§11及“需修订”的当前结论，详设§9也同步；§10原审查记录保留为历史，未改成当时未通过，也未声称原评审者否定自己的结论。

本项只修正文档状态，不代表R3-01–03已修订/复核。本轮两个责任专题的`./sddw check-docs <feature>`均返回0；受影响tracked文档的`git diff --check`通过，未跟踪详设另查行尾空白。未重跑全局文档检查，不沿用前轮结果声称全局通过；未运行应用测试。

### 11.6 保持不变的裁决与本轮边界

- 推荐去掉生成式调用、保留既有Embedding；推荐/报价独立，无旧客户端兼容、不改旧聊天记忆索引、不增加本地推理进程。
- Runtime显式计量出口的可行性结论保留；真实身份未知不伪造，原响应去重/资金幂等/停止后补采及forward-only边界保留。
- 未将“模型切换后旧报价仍有效”列为缺陷：原固定报价合同明确不重算，不能擅自要求重新预占或追加收费。
- 本轮不改业务代码、不重跑真实模型/模拟探针、不清数据、不部署。外部官方页面检索未返回可用内容，没有据此新增行业能力判断；本轮发现依据固定详设、现行本地合同与源码，不冒充外部独立背书。
- 需要先修订R3-01–03并针对反例回读，再更新设计结论；不能以文档检查通过替代设计关项，也不扩大为全项目重构。


### 11.7 R3修订与Owner定向回读（2026-11-23）

**当前结论：OWNER_DESIGN_RECHECK_PASS；R3-01–04均在设计/文档层闭合。** 原11.1–11.6的REQUIRES_CHANGES及原问题表仍代表修订前，不改写原评审记录。这次是Owner对既有发现的修订与定向回读，不冒称新增独立评审者批准，也不是产品实现/质量/性能/发布验收。

回读正文固定输入SHA256为`065508fdd11916336d5795dbb4d10bd36c9924f5ec61088f9ed20bf8f18c0d9b`；含新定义和固定夹具链接，尚未附本小节及状态更新。契约夹具SHA256为`23c1dd3df298d8e6a01c75e53c85b0d02134a7f916f2f5a2d7d041f70d55c62d`。回读副本、逐步检查和实际文档校验保存在`/home/isp/tasks/cyf-embedding-openai-20261123/detailed-review-r3/fix/`，沿任务TTL处理；正式设计及夹具在本专题保存。

| 问题 | 正文修订 | 回读裁决 |
| --- | --- | --- |
| R3-01 / P1 | §4.3.1整事项唯一键、初始特征、Agent封闭成员集合、验收终态及排除/修订规则；§6.1真值同步 | CLOSED_DESIGN：执行明细不再充当整事项标签；失败成本不能遗漏，取消/未完成/混合配置不伪装完成样本 |
| R3-02 / P1 | §4.2.4六类分条记录、确切字段/摘要、持久ACK、接收/账本/投影分阶段恢复；固定请求/ACK夹具 | CLOSED_DESIGN：无responseId请求可表达；FINAL和计费ACK不等于COMPLETE；实际REQUIRES_NEW事务边界明确 |
| R3-03 / P2 | §4.4.1独立特征端口/作用域缓存、冷/热调用边界、502/503与候选UNAVAILABLE区分、重放优先 | CLOSED_DESIGN：直接手选quotes不依赖recommend；共享编码失败不会冻结成0文或永久UNAVAILABLE批次 |
| R3-04 / P2 | 两个主spec、design/tasks/acceptance及本文当前状态统一 | CLOSED_DOC_ONLY：当前结论指向本节，历史通过/未通过均保留 |

**反例逐项回读（合同推演，不是上线测试）：**

| 固定反例 | 修订后唯一允许结果 | 依据 |
| --- | --- | --- |
| 同事项首轮1元、返工2元，最终验收 | 一条3元整事项标签，不是两条执行标签 | §4.3.1 |
| 失败轮未取得完整用量、后续成功 | 整事项不READY，不删失败轮凑完整 | §4.3.1 |
| 取消事项计量完整 / 正在进行 | EXCLUDED / WAITING_EVIDENCE，不训练完成成本 | §4.3.1 |
| 同执行重放、同样本修订 / 中途换组 | 不增加样本数 / 初版排除混合配置 | §4.3.1 |
| A有usage且ACK，B无responseId | 独立REQUEST保留B，最终INCOMPLETE，完整总量null | §4.2.4及缺响应夹具 |
| 最终清单先到、响应或前驱后到 | 先WAITING_EVIDENCE；关联及摘要齐全才判覆盖 | §4.2.4 |
| FINAL的ACK丢失 / 同身份异内容 | 原ACK重放 / 409且冲突样本不可选 | §4.2.4 |
| 账本已提交、RESPONSE ACK未保存即崩溃 | 原ledger receipt恢复，不生成下一笔费用attempt | §4.2.4分阶段事务 |
| 证据已接收、投影更新前崩溃 | 原READY已失效；恢复后按输入revision CAS发布 | §4.2.4 |
| 报价prepare后样本又收到修订 | persist复查修订不符409；已提交报价不重算 | §4.2.4及§4.4 |
| 从未recommend且冷缓存，直接quotes | 独立准备一次任务向量，不按候选逐个编码 | §4.4.1 |
| 首次编码故障 / 已有同key批次且网关故障 | 503且不提交批次 / 原响应直接重放，0次外发 | §4.4.1 |
| 网关返回非法向量 / 其他Owner相同文本 | 502、不缓存 / 不跨Owner命中私有特征 | §4.4.1 |

**实际完成的检查：** 用现有Runtime `skillDigest/skillCanonicalJson`对固定夹具运行376项字段/身份/前驱/摘要/ACK关联及计量一致性断言，结果通过。两请求正常夹具推导COMPLETE、合成总量240；第二请求无响应夹具推导INCOMPLETE、完整总量null、已观察120。这里只检查设计数据和约束；Java消费者、真实HTTP鉴权、数据库崩溃、并发与实际ACK恢复均未执行，不把断言数量当业务回归数量。

两个责任专题`check-docs`与受影响文档空白检查通过。全量`check-docs --all-docs`仍仅报原全局手册的`full-r5/report.md`和`full-r5/verification-summary.json`两处历史目标缺失，无新增不可达当前文档；未伪造历史文件。本轮未修改业务代码、生产配置、索引或数据，未调用付费模型，未构建/部署。

下一步可以按§7进入实现；正式来源、生命周期通知与样本投影、独立报价、跨端契约/故障/性能及准确性验收仍须在真实固定候选上完成。没有真实授权基准时对应分组继续不可报价；设计关项不构成生产可用承诺。
