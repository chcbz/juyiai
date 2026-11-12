> **现行适用范围（2026-11-07）：** 本文是[所属专题](spec.md)的细则，不独立定义发布/角色/DFX规则；共用[统一开发约束](../architecture-convergence/development-principles.md)。旧日期候选/测试/安装仅代表当时范围，未核实部分不改成今日完成。业务协议/冻结输入不因文档整理改写。

# 可复用原生技能包：盘点与安装契约

当前目录（2026-11-03最终核对）：图片识别、图片生成、图片编辑、文档处理、信息检索、网页操作，共6项。此前7项/9项是历史阶段；资料分析、文本文件、PDF提取均已下架并清除活动安装，历史记录保留。详见末节。

核对日期：2026-11-02。Owner：本会话。范围：已验证能力的经验提取与现有技能管理适配；不是自动“提取技能”平台开发。
遵循 [RB-1](responsibility-boundaries.md) 和 `api/docs/interface-standard.md` v1.4。

## 1. 能力盘点

| 技能 | 版本/处理 | 已有证据及限制 |
| --- | --- | --- |
| image-understanding | 新包1.0.0候选（用户补充要求） | 复用task563原生读图历史能力证据；封装内容描述、文字核对、多图比较与改图核对经验，新包模型执行尚未验收 |
| image-generate | 复用现有1.3.1商品，不另建native-image商品 | task564，256×256蓝底白圆；历史技术验收通过 |
| image-edit | 复用现有1.3.1商品 | task563读图/改图通过；首次1254×1254未保持目标尺寸，后续模型调用离线缩放至256×256通过，不隐去首次问题 |
| document-workbench | 新包1.0.0候选 | task562覆盖TXT/Markdown/HTML/XLSX/中文PDF内容；提取按格式处理、内容核对和成果交付经验 |
| browser-workbench | 新包1.0.0候选 | task562覆盖本地HTML表单/按钮操作与截图；外网站点操作仍需目标站点验收 |
| web-research | 新增1.0.0候选（用户继续授权，非历史已打通能力） | app-server隔离启动回读live与发现通过；模型服务真实检索另见§8证据，不用本地网页验收替代 |

历史证据根：`/home/isp/state/cyf-native-skills-20261028/pdf-development-20261031/`。
总索引 `mainline-final-verification.json`；具体证据：
- `acceptance/image-generate-r114-verification.json`
- `acceptance/image-edit-original-verification.json`
- `acceptance/image-resize-post419-verification.json`
- `acceptance/documents-r114-content-verification.json`

这些是API419/8ab1a42、Runtime114/dedf9c7下的历史技术验证，不是新包已发布/安装或当前版本的重新验收，也不代表用户业务签收。
DOCX仅有同制品隔离探针，OCR、视频、B站字幕没有本轮用户流程证据，不列入已验收包。读图底层仍是原生载体能力，新增image-understanding仅封装识图经验，不另造OCR服务。大文件流式传输、授权、隔离、上传恢复、部署和磁盘清理不提取为本批业务技能。

## 2. 源码与职责

源码根：`/home/isp/wsps/chcbz/isp-install/conf/skills/`。

- `native-image/variants/image-generate.md`、`image-edit.md`：现有发布入口；复用对应scripts/vendor，密钥不入包。
- `image-understanding/SKILL.md`：独立识图经验包，无脚本、密钥或新服务。
- `document-workbench/SKILL.md`及`references/formats.md`：按需使用UTF-8文件工具、openpyxl、pypdf和中文PDF方法。
- `browser-workbench/SKILL.md`：复用共享withBrowser，模型根据实际页面选择步骤。

新包只有说明与经验，不复制Python、浏览器、字体、用户材料、会话或凭据。工具链由Runtime共享提供；文档技能生成PDF不需要另安装浏览器技能。四个新包不互相依赖，不含固定业务步骤或新的runner。

RB职责：API负责商品/权益、业务权限和完成事实；Runtime负责安装、执行视图、目录/进程/网络隔离、配置交付及成果适配；工具实现格式/浏览器协议；模型编排；技能给经验；Web展示权威结果。原能力提取不修改API/Web/bridge核心；用户后续要求的搜索缺口仅在Runtime通用配置责任层适配，见§8，不新增按skillKey的执行分支。技能指令不是安全隔离实现。

## 3. 包与版本契约

- 普通ZIP，根目录`SKILL.md`；frontmatter `name`等于skillKey，`metadata.version`等于skillVersion。
- 新包版本均`1.0.0`，kind=`INSTRUCTION`，不带`manifest.json`，manifestSha256为显式null。
- 发布绑定商品版本、技能版本、精确包字节SHA-256、长度及来源源码；已发布字节变化必须升版，不覆盖旧SHA。
- 技能版本与Runtime/API版本独立。只发布技能不需要重发应用。
- 现有包存储上限16MiB、描述器最多256条/解压总64MiB，沿用消费者，不在本任务改限制。
- `NOT_EXECUTABLE`表示没有旧runner manifest，不表示原生模型不能读取技能或执行其脚本。安装成功、工具可用、原生业务成功分别验收。
- 新包不需要技能密钥；现有图片包各自使用获准的`/skill-config/image-generate.json`或`image-edit.json`。不共享其他用户配置，不将凭据加入包或发布metadata。

已有图片商品分别为`sp_se2_image_generate`、`sp_se2_image_edit`，商品版本为`spv_se2_image_generate_1_3_1`、`spv_se2_image_edit_1_3_1`。历史发布绑定见`/home/isp/state/cyf-native-skills-20261028/business-acceptance-20261029/image-acceptance/maintenance131/packages.json`。正式复用前核实存储对象/摘要，不能只凭旧本地路径存在。

## 4. 聚义厅安装适配（复用，不另建接口）

1. 固定干净源码后，本地执行必要测试并打包不可变技能制品，记录真实构建批次/工具链/源码及SHA；受控安装核对同批来源。临时fixture ZIP仍不能冒充正式制品。
2. 通过现有`POST /agent/skill-maintenance/product-versions`发布，multipart含metadata和package；使用真实ROLE_ADMIN身份，不直接写库、不复用旧root发布harness绕过入口。
3. metadata依现有接口提供productId/productVersionId/name/description/skillKey/skillVersion/priceMicro/deploymentRestriction/approvedPermissionsManifest/packageSha256/manifestSha256/expectedProductVersion。新商品revision=0，升级读取真实revision；价格、权限与部署范围不得凭技能文本授权。正式商品ID及发布值在实际发布前核对，本文不伪造已注册记录。
4. 聚义厅沿用技能目录、quote/order及`POST /agent/{agentId}/skill-changes`。不同Agent安装同一个商品版本，各自产生安装归属/ID/修订；不复制别人权益或借用安装记录。
5. Runtime现有installer下载并验证ZIP、PREPARE→ACTIVATE、持久ACK/result；每Agent安装至自己的主Home技能目录。任务执行时，registry按API授权TaskSkillBinding解析精确安装，Runtime再交付隔离Home可见视图；包不自行链接主Home或选择宿主路径。
6. 工具、网络和凭据许可来自当前执行合同，技能安装不自动扩大权限。普通技能目录可见与具体任务的绑定解析是不同检查；临时安装测试不替代真实app-server发现及模型执行验收。

## 5. 定向回归与剩余交付

轻量回归：`conf/codex-bridge/test/reusable-skill-packages.test.mjs`。
使用真实installer与registry、内存ZIP/模拟下载，在临时目录分别为两个Agent安装每个新包，核对所有文件字节、PREPARED/APPLIED/NOT_EXECUTABLE、安装目录独立、同包SHA一致、正确任务绑定可解析、跨Agent绑定拒绝；结束清理临时目录。不替代API权益测试，不访问生产、不调用模型。

剩余：固定候选并生成正式Flow制品 → 管理员发布至现有技能管理 → 分别安装至目标Agent → 新包原生发现与业务验收。现阶段未运行以上生产步骤；不能用历史task562证明新包已在线安装。不同Agent目标尚未固定，不擅自批量安装所有Agent，不调用付费图片服务重复验证。

## 6. 基线（2026-11-02盘点时）

- Runtime源码HEAD/origin develop：`2464af90f1b34f9086563e12bf15cfb765152a89`，tree `7d5ecfa486ae528366e5ad7f9c9d7758b5e770d8`。
- API origin develop：`ebed9d91492dbb71d94ba679a3fc3e559328180b`，tree `863d69a6b48ade1ae71767e323b803ee88a7281d`。API工作区不是该版本，接口核对用固定远端引用内容。
- Web origin develop：`a3462bd7e5aacde7c88d8202a74726acfd43bbae`。
- 生产记录盘点：API425/ebed9d9；Runtime114/1.3.31/dedf9c7。源码与线上不混同，本轮未部署或重启。

## 7. 网页搜索缺口诊断（2026-11-02补充）

用户反馈曾询问最新新闻但Agent表示无网页搜索能力。本轮未定位该次具体任务日志，因此不声称还原当次全部原因；已直接核对源码和当前安装程序存在明确限制：

- `conf/codex-bridge/typed-inspection-profile.mjs:buildTypedInspectionCodexConfig`生成`web_search = "disabled"`。
- `native-execution-profile.mjs:buildNativeExecutionCodexConfig`只替换沙箱模式并追加权限，不移除上述禁用项；原生任务继承禁用。
- `/home/isp/apps/cyf-agent-runtime-v1/app/codex-bridge/`下上述两份安装程序同样如此。只读检查，未改生产配置。
- 浏览器导航是另一条链路：`native-execution.mjs`从技能配置networkOrigins确定网络许可，`native-execution-profile.mjs`继续绑定允许origin。本地HTML浏览器通过，不意味着能访问搜索引擎及任意新闻来源。

结论：缺少搜索不能靠新增SKILL.md解决。搜索技能可以提供时效、来源及引用核对经验，但必须先有真实搜索工具/服务。若选择app-server原生搜索，需要在Runtime通用配置责任层调整禁用策略并验证所用Provider实际支持；若选择现有浏览器或技能脚本调用搜索服务，需要实际网络许可与必要配置，不能通过技能文字自行放开网络。两者不应同时盲目实现，更不能新增bridge按“新闻技能名”的业务分支。

本轮只诊断，不新增未经验证的“新闻搜索”商品，不切换生产搜索配置。搜索能力接线及最新新闻端到端验收另作为真实缺口；识图新增不依赖它，也不需要修改bridge核心。

## 8. 原生搜索最小适配候选（用户继续授权后）

本节覆盖§7“本轮只诊断”的阶段状态；不改变历史生产记录。新增`web-research 1.0.0`候选，提供最新信息检索、原始来源核对、日期辨析和引用经验；不包含搜索引擎SDK、凭据或浏览器依赖，不声称已经线上可用。

### 通用配置责任层

复用现有客户所有、按安装ID精确绑定的`skillExecutionConfigFile`，在安装配置条目增加可选`webSearch`：仅支持`disabled`（缺省）与`live`。`configuration`仍为对象，`networkOrigins`仍是本机脚本/浏览器获准访问的精确HTTPS origin。示例只展示单个安装条目，不是可直接覆盖生产的完整配置：

```json
{
  "configuration": {},
  "networkOrigins": [],
  "webSearch": "live"
}
```

仅`NATIVE_SKILL_SCRIPT_V1`合同下本次已获API授权的精确技能安装能加载该本地配置；不从技能名、描述或网页内容推导权限。`NATIVE_LOCAL_FILES_V1`、未配置安装、其他Agent、未选中技能和只读inspection保持禁用。多个获准技能在一个任务中共享同一执行环境，启用的是该任务的引擎能力，不承诺同任务内逐技能调用隔离。

这是显式的模型服务侧检索授权，**不是**为任意新闻网站开放本机出口；远端搜索涉及的站点不受本机CONNECT的origin列表约束，不能把此能力描述为仅能检索列表内域名。默认禁用以避免将文件任务内容无意扩展到检索服务。技能提醒最小化查询内容，但不将提醒当安全强制措施。API仍负责安装/任务权限，客户本地配置只限定已获准执行的能力。

### 实现与恢复

- `native-skill-config.mjs`读取枚举并绑定配置摘要；未知值只使受影响执行失败，防止拼写错误被当成启用。缺省/显式disabled不改变既有摘要。
- `native-execution-profile.mjs`从已选配置生成执行绑定；只有live进入新绑定字段，影响恢复摘要。更改搜索许可后不可复用旧执行目录/线程；新执行使用新合同。已有不启用搜索的绑定不发生无关变化。
- `typed-inspection-profile.mjs`只在原生执行Home按绑定生成web_search，inspection保持disabled。app-server config/read必须回读期望值，避免配置被覆盖后误称已授权或已启用。
- 不新增动态搜索工具、不改API/Web、不按web-research名称分支、不扩大shell网络、更不启用全局搜索。Provider是否支持由独立真实探针验证；配置回读通过不证明搜索业务成功。

### 回归与证据

定向文件：`native-skill-config.test.mjs`、`native-execution-profile.test.mjs`、`native-execution.test.mjs`。2026-11-02本机轻量测试50项，44通过、6原有跳过、0失败；日志`/home/isp/state/cyf-reusable-skills-20261102/search-config-tests-final.log`。覆盖授权安装选择、禁用默认/摘要保持、未知配置拒绝、live进入独立绑定、inspection不变、外网origin不扩张、引擎回读不符拒绝以及许可变化后恢复拒绝。

验证来源：官方文档检索工具未返回可用正文，直接抓取官方配置页面返回Forbidden；本轮不将其作为已读文档证据。配置字段及实际支持以当前固定app-server回读与搜索事件验证，不能仅凭兼容Responses端点推断支持。

独立app-server隔离探针配置回读`live`且技能发现路径精确通过：`/home/isp/state/cyf-reusable-skills-20261102/search-config-probe.json`；无模型调用、无生产配置变更。四个包各两个临时Agent安装测试4通过/0失败，见`install-test-with-search.log`。精确候选文件摘要见`search-candidate-verification.json`，不是正式Flow或线上验收证据。

真实模型探针结果：`search-model-probe.json`使用当前吴用配置的gpt-6-luna与同一模型服务，隔离Home内web_search回读live、技能发现通过、turn正常终止，但模型明确表示没有搜索工具，thread/read的webSearch条目为0。因此**检索业务未通过**；不能将配置成功包装成网页搜索已打通。只调用了一次真实模型探针，无业务资料/DB写入或任务签收，服务计费未独立核算。接续用本机synthetic Provider抓取真实引擎发出的工具类型（无真实密钥/远端模型调用），区分引擎未广告工具与下游连接不支持/模型未调用，不盲目重复相同检索请求。

## 9. 模型目录根因及修复后的真实验证

本节覆盖§8中“检索业务未通过”的中间结论，保留原失败证据，不重标旧探针。

### 根因与必要适配

仅live配置没有使当前引擎向模型广告搜索。Codex0.164可将工具放在请求input的additional_tools中，不能只看顶层tools。纯本机模拟Provider对比表明：普通启动、thread/start显式live、改用引擎目录默认模型或仅在thread/start指定模型目录都未广告搜索；**在app-server进程启动时加载匹配的自定义模型目录**后，才出现`web_search`且`external_web_access=true`。模拟端点只捕获请求并返回预设400，无真实模型调用；400是探针设计，不是生产故障。

因此候选新增Agent profile可选`nativeModelCatalogPath`，不更换模型、不默认读取其他账号HOME。Runtime读取运营者明确配置的公开模型元数据快照，复制到隔离Home并只读挂载；目录摘要进入native执行绑定，变更后不能恢复原摘要的执行；app-server初始化回读其隔离路径。原生目录交付仅在Runtime责任层完成，不搬进技能包。影响实现为`agent-client.mjs`（配置透传）、`native-skill-config.mjs`、`native-execution-profile.mjs`、`typed-inspection-profile.mjs`；无API/Web改动，无按技能名分支。运维配置写入现有Runtime self-host说明。

明确的校验依据：管理员误配可写/非普通目录文件会让模型能力目录可被替换，限定当前用户/root所有的不可组/全局写常规文件；配置/目录摘要变化影响线程能力，恢复必须保持绑定；引擎回读不匹配则不能把live/正确目录当成功。回归集中在native-execution-profile测试，不逐个业务调用方重复验证。未配置目录保持现有行为，文档不宣称所有Provider都需要自定义目录。

### 验证分层与局限

证据根仍为`/home/isp/state/cyf-reusable-skills-20261102/`：

- `search-model-probe-without-catalog.json`：旧失败，模型表示没有搜索，webSearch=0。
- `search-wire-probe-before-catalog.json`、`search-wire-probe-thread-catalog.json`、`wire-request-*.json`：仅本机模拟请求；初始化目录的最终请求含真实web_search工具声明。模型比较未调用其他模型服务，更未启用DeepSeek。
- `search-model-probe-with-catalog.json`：同一gpt-6-luna/同一模型服务，live与目录回读通过，真实出现webSearch；按2026年11月筛选未得到足够可靠结果，模型选择说明不足而非编造。
- `search-latest-available-probe.json`：取消过窄月份条件后，真实search/openPage事件与来源链接返回，模型明确标注结果日期和“不能断言官网截至今天最新”的限制。
- `cma-source-verification.html`和`cma-source-http.txt`：独立只读GET返回HTTP200，标题及PubDate与模型引用一致。**只证明该引用可核对，不证明新闻全量排序或今天最新。** thread/read的results为null，不能声称拿到了搜索服务完整原始结果集合。
- 真实模型诊断共3个turn（初次无目录、目录后月份查询、目录后可见结果查询）；本机模拟端点未调用模型。服务实际计费未独立核算。

这是源码候选的隔离能力验证，不是技能商品正式发布/生产安装/完整聚义厅端到端验收。未更改生产profile/model-catalog/技能配置，未重启API/Runtime，未开Flow。正式发布前仍须固定源码、升Runtime/bridge版本、Flow验证制品、真实管理员注册包及目标Agent受管安装验收；不将现有两张图片技能商品重复发布。

最终本机定向回归：`final-focused-tests.log`，56项、50通过、6原有跳过、0失败（包含四包各两个临时Agent）。精确候选源码路径/摘要、隔离检索及独立来源核验汇总在`final-verification.json`；状态为源码候选和隔离验证完成、尚未正式发布。无本地生产打包，无新建worktree，无覆盖并发任务修改。

## 10. 正式交付证据更新（2026-11-02）

用户授权部署发布后已固定Runtime1.3.33/bridge1.1.23，源码32416ed5bbde7ee25ba199ad586dbd0e4386e89c、tree c1a6ad9e6f9a02719205111e4cc8fea4ba3cc572。Flow5264702/116成功，779通过/10跳过/0失败；四技能1.0.0正式ZIP及Runtime来自同Run，包与固定源码逐字节核验通过。web-research展示名称为“信息检索”，技术key不变。源码/构建已完成不等于受管技能已上线。

真实chcbz维护接口发布返回403 SKILL_PUBLICATION_FORBIDDEN，需要ROLE_ADMIN身份；无数据库或权限绕过，没有新增商品/订单/安装。当前包为发布就绪，不宣称已可供Agent安装；受管执行验收仍待正式发布及明确安装目标。正式证据和后续安装结论见既有handoff `REUSABLE-SKILLS-20261102.md`及`/home/isp/state/cyf-reusable-skills-20261102/release/`。无需为补管理员会话或重试发布重复构建。

## 11. 技能管理岗位授权（2026-11-02 用户最新决定，实施中）

覆盖§4对发布者ROLE_ADMIN的要求，历史403证据保持原状。新增岗位“技能管理”，资源`skills:platform`，审核及发布整个平台技能目录（限认证环境tenant/client，不跨环境）。岗位挂在既有owner scope中、任职绑定具体Agent；不按岗位显示名称授权，不将技能包或模型文字当权限凭证。

- 权限责任为API RB-02。`MANAGE_POSITIONS/positions`继续控制配置/任命；新增`SKILL_REVIEW/skills:platform`和`SKILL_PUBLISH/skills:platform`为授予该资源的上界。没有这两项授权的普通岗位管理者不能自建同名岗位提权。任职、撤职、revision、binding和原有操作幂等复用，不增加角色系统。
- 发布HTTP仍为`POST /agent/skill-maintenance/product-versions`，JWT认证Owner代办一个明确指定的任职Agent。metadata新增必填`positionAuthority`对象：`appointmentId`、`appointmentRevision`、`positionRevision`、`agentId`、`bindingId`；所有版本和ID按既有接口规范1.4传字符串。scope不接受请求覆盖。无ROLE_ADMIN后门；管理员没有有效岗位也不能发布。
- `positionAuthority`是定位/并发条件，不是自签授权。API锁内读取任职、岗位、绑定与上界权限。发布前做一次权限准入，包准备仍在事务外；提交前重新锁定并验证，审核通过事实(APPROVED)与发布(PUBLISHED)在该事务中共同写入。准备期间撤职会拒绝提交，已开始的提交与撤职串行，撤职返回后不得再提交。不能声称撤职能逆转此前已完成发布。
- 当前产品只有维护发布的合并“审核通过并发布”入口，本轮不虚构独立待审队列/驳回/审批工单。Owner代办不等于吴用模型已实际阅读/审核包；独立Agent自主审核及工具调用未由本接口证明。现有Runtime内部令牌不能直接调用JWT维护接口，不把Owner JWT或平台凭据放入技能包。
- 商品不可变版本、包/manifest SHA、权限manifest、价格、明确升级覆盖策略、幂等及事务规则保持；本轮不改技能购买/安装`ADMIN_ONLY`策略，不授予资金权限。Web/bridge不复制该授权，当前无此发布表单的Web不做无关修改。

### 数据迁移与验收

既有`agent_position_authority`有仅含三个权限键的CHECK，修改CREATE TABLE脚本不升级已有表。部署前须只读核对生产SHOW CREATE TABLE/实际CHECK名称，再通过既有受控schema入口删除该权限枚举CHECK，权限词汇与授权规则由API业务层统一实现；不删除其他约束，不授予全站角色。新建schema与旧schema升级均需在隔离MySQL验证。正式授权只对已核实的chcbz owner/client及吴用binding执行；岗位定义/任命走现有HTTP幂等入口。权限行初始化没有现成用户自助授予入口，使用用户本次明确授权的受控数据操作，保存前值、只补缺项、回读；不得直接写商品发布事实。

验收须覆盖普通用户/仅ROLE_ADMIN拒绝、授权者无ROLE_ADMIN成功、跨owner/client拒绝、档案岗位不可发布技能、过期岗位/任职/绑定拒绝、撤职并发/准备期间撤职拒绝、原不可变版本/升级覆盖不回归。源码完成、Flow、schema迁移、实际任命及四包发布分别记证据；目前不是生产已生效声明。

### 2026-11-02 最新扩围说明

用户要求其他业务表同样删除CHECK，替代上文只删除authority枚举CHECK的范围。具体规则归档在API `docs/interface-catalog/database-check-rules-20261102.md`（当前任务worktree候选），全库删除不能先于schema initializer/目录校验/测试适配。岗位业务授权不变，PK/UK/FK/NOT NULL/事务/锁等不在删除范围。2026-11-02已按下节完成生产DDL、技能岗位任命及四技能发布；原阶段记录不再代表当前状态。

### 2026-11-02 生产验收收口（API Run439）

- API `8ad42be7815e499077c6a97439f0f13c96c7650e` / tree `129909ac3c71c022fffe3256bf16c0f17c9ee046`，Flow5260799/439成功，3659项中3617通过、42原有跳过、0失败。主机独立安装及JAR摘要核验通过，无CHECK正常启动后health UP；临时启动诊断已关闭。Runtime保持既有116版本，未重启。
- 生产jia库44表82条CHECK已受控删除，列/索引/其他约束保持不变，正常启动后仍0条CHECK。未替换为触发器；规则保留于API `docs/interface-catalog/database-check-rules-20261102.md`。
- chcbz所属吴用已任职“技能管理”，范围`skills:platform`，岗位和任职revision均1、binding1。Owner仅补三条岗位管理/技能审核/技能发布authority，没有授全站ROLE_ADMIN。实际HTTP通过真实Owner会话代办并回读，不声称吴用模型自主完成审核或发布。
- 识图、文档工作台、网页操作与验收、信息检索四包已通过发布接口正式发布，均1.0.0、免费、NONE、权限清单空；目录回读名称/版本/可安装匹配。包仍来源Runtime116，四份落盘对象摘要匹配且0444。没有自动给生产Agent安装四包，没有新增模型调用。
- 主机包存储目录`/home/isp/state/cyf-skill-packages`应由实际API服务身份拥有写权限，以承接受岗位授权的发布。此次只将目录owner改为cyf-api，保留0750、原group/ACL及11个既有对象；不递归chown、不开放组/公共写，不改变内容寻址和只读对象契约。此前root只读目录导致503，修复后四包均200。
- 最终证据：`/home/isp/state/cyf-reusable-skills-20261102/skill-position-release/production-final-verification.json`，细分证据同目录`publication-verification.json`、`position-appointment-private.json`及`check-removal/production-check-apply-private.json`。发布和正常启动验证有API不可用窗口；不把构建成功或单个health采样冒充无中断发布/全业务验收。

## 安装展示与原生就绪语义修正（2026-11-02）

本节针对安装提示误报与报价按钮阻断；源码修复及上线证据见既有handoff，不能以本规格视为已发布。

- `INSTRUCTION` 包的 `manifestJson/manifestSha256` 均为空是现行合同，不是安装证据缺失。详情使用真实受管安装的 `verifiedNative()`，继续核对安装ID、包摘要、运行主机/会话及当前目录；不能通过伪造可执行manifest或订单消除提示。
- Runtime 的 `NOT_EXECUTABLE` 对普通技能表示“不提供独立runner”。匹配已核验安装、启用策略和当前目录的普通技能可供原生模型使用，详情可以显示运行就绪；这不授予任务权限或工具调用权。受管列表原始 `admissionEnabled` 仍指独立可执行技能准入，不改DB值让页面变绿。Web明确展示“已启用（原生技能）/原生技能包已就位（由模型使用）”。
- 后台读取不应反复禁用已经准备好的报价按钮。Web使用已收到的权威候选及版本发起请求；版本变化仍由服务端拒绝，响应继续核对固定意图，不能以轮询结束代替业务版本检查。
- 退役runner不会重新开放。文本文件与资料分析按同一原生普通包合同发布1.1.0，保留原有能力目标，不在bridge增加技能名分支。旧图片包替换为现有1.3.1原生包。无升级政策时不得自行授予付费升级权益；使用明确免费报价的正常卸载/重新安装路径，历史成果和在途执行事实不改写。
- 回归入口：ChatActionCapabilityServiceTest（原生安装、无会话、精确安装ID及停用）、SkillManagementTransactionTest（真实安装/APPLIED与原生准入）、Web skill-market-ui-lifecycle.test.js（轮询中报价、原生状态、不自动购买）、Runtime reusable-skill-packages.test.mjs（不同Agent同包安装及绑定隔离）。

### 原生包安装与执行环境（2026-11-02 实际安装复核）

- 技能安装不会自动配置模型、载体或Provider密钥。`INSTRUCTION/NOT_EXECUTABLE`只说明包已被运行端发现且不提供独立runner；真实原生执行仍以认证会话的`nativeExecution`实测声明及每任务`availableActions`为准。技能包不能承担RB-03环境开通，也不能把安装成功伪造成全部工具可用。
- 自托管Agent在现行Runtime1.3.33中须配置既有`inputCarriers`（独立rootDir/stateRoot、匹配引擎/Provider/model及载体合同）；Runtime启动实测网络/沙箱/工具链后更新注册。无该配置的Agent可以安装普通包，但不会获得原生文件执行操作。不同Agent允许有不同能力，不机械复制身份/可写Home。
- 每技能私有配置通过`skillExecutionConfigFile`按真实scope、安装ID绑定；免费安装不等于运行服务免费。新安装ID不能自动继承另一主体的密钥，需Owner管理配置；秘密不放技能ZIP或Web，不能省略现有授权及网络范围。
- 启动通道ready不等于异步工具测量完成。不得在测量尚未完成时宣称文件执行已验收；已有冻结请求不因后续注册变化自动重放，后续用户动作取得新上下文。林冲事项577实证：无配置/测量未完成时actions为空，实测完成后的新请求含通用原生操作及4个已安装包操作。

2026-11-02验收补充：API442/ef702265与Web406/98f7682已上线；林冲四包完成真实UI安装，事项577文本输出通过，吴用事项578生图和基于上传成果改图均RESULT_COMMITTED、正式下载摘要/尺寸及目视通过。Runtime仍116/32416ed5，仅补林冲隔离配置后重启并独立测量，三Agent新鲜ready。此结论不覆盖普通快速聊天文件执行、其他未执行技能或历史任务恢复。证据 `/home/isp/state/cyf-skill-install-repair-20261102/production-final-verification.json`。

## 2026-11-03 技能发现文案整理（已上线核验）

现有生产9项技能的市场标题/描述由 `economy_skill_product` 持有；`SkillManagementService.recommendationSkills` → `AssigneeRecommendationService` 将这份文案提供给承办推荐模型。安装包内 `SKILL.md` 则供执行模型发现/使用，二者不是同一份存储。此次先更正商品发现文案，不改固定技能key、包字节/版本/摘要、安装ID、价格、权限及任务授权，不把商品文案更新冒充已安装SKILL.md更新。

最小更新入口复用技能发布Controller/Service和技能管理岗位授权，`PUT /agent/skill-maintenance/product-metadata`；JSON为productId/name/description/expectedProductVersion（十进制字符串）/positionAuthority（现有五字段）。岗位鉴权事务内锁定当前平台商品并CAS更新，仅写name/description/version/update_time。不上传包、不修改immutable version，不触发安装/重启；名称不空且不超过255、描述不空且不超过4000，依据现有数据库字段与发现用途限制。旧版本/无权限/非平台商品拒绝；同一次写入丢回执后的相同内容重试返回RECORDED且不再增版。正式测试/上线状态见既有handoff。

文案统一包含“用户目标、输入与产出、容易混淆的技能边界”；保持“识图”“信息检索”名称。标题映射：图片生成、图片编辑、文本与结构化文件、资料分析与对比、文档与表格处理、PDF正文提取、网页浏览与操作。完整候选保留 `skill-discovery-metadata-20261103.json`，是受管更新输入，不是新的运行框架。

补充技能评估：现有9项已覆盖图片、常规文本/表格/PDF、资料分析、公开信息检索、网页操作，不另建重复的摘要/翻译/新闻/网页截图技能。候选缺口为DOCX处理指导、音视频转写/字幕（含用户此前B站字幕需求）、演示文稿；须先核实工具/来源访问/格式能力再补包，不能仅增加描述宣称具备。识图不替代批量OCR，资料分析不等于音频转写；本次不自动新增这些未经验收的能力。

文案边界用于减少误选，不是互斥路由或额外准入。例如“搜集最新公告并整理成报告”可组合信息检索→资料分析与对比→文本与结构化文件；“读取Excel比较季度数据并输出PDF”可组合文档与表格处理→资料分析。模型仍按任务和实际可用工具编排，不在API/bridge新增按技能名或关键词分发的判断器。基于已安装版本的能力核验、任务授权继续独立生效。

上线核对：API c58a41a450 / Flow458，110项全通过，9项岗位授权metadata更新均200且目录/真实UI回读一致；原包版本、价格、权限保持不变。证据 `/home/isp/state/cyf-skill-routing-20261103/production-final-verification.json`。此节只证明商品发现文案上线，不代表包内SKILL.md重发或新增格式能力。

### 2026-11-03 精简发现文案（第二版）
用户确认的7项标题及短描述以 `skill-discovery-metadata-20261103.json` 为准，替代此前9项长描述作为目标清单。图片识别、图片生成、图片编辑、文档处理、资料分析、信息检索、网页操作；7项描述合计207个字符。文档处理负责文件操作，资料分析负责归纳比较与结论，二者分开。

本次已通过既有岗位授权元数据接口更新这7项商品，真实技能管理UI/readback通过；不改权限、价格、包摘要或安装，不重启服务、不新开Flow。当前线上目录仍有9项：`text-file`和`pdf-extract`尚未下架，不能把目标7项写成已完成目录合并。已安装SKILL.md未随商品文案变更。既有文档包已包含文本、表格、文本型PDF处理；旧包退出目录及推荐须走业务生命周期，不能用文案别名伪装安装迁移，也不能直接删安装/历史。

### 2026-11-03 目录合并上线收口
API `767d631e1edfd4e0c59acabdff68cc523fceeef5` 已经Flow5260799/463验证并独立主机安装。通过吴用既有技能管理岗位HTTP入口，`sp_se2_text_file`、`sp_se2_pdf_extract`已置为既有`RETIRED`状态。当前发布目录及吴用/林冲的安装候选均为7项，标题/短描述与本目录JSON逐项一致，覆盖上一节“仍9项/尚未下架”的线上状态。

文档处理复用已发布document-workbench的文本、表格及文本型PDF操作，不引入新执行器。旧商品退出新目录/承办推荐，已有安装仍管理可见、保留既有授权及固定包；不会把旧text-file/PDF安装伪装成document-workbench，也没有自动卸载或跨技能迁移。因而已有旧安装的Agent管理页可能超过7行，这是已安装/历史记录，不是新安装目录仍有重复项。已安装SKILL.md未变。

责任仅在API商品生命周期、推荐投影及安装管理读模型；Web/Runtime程序未改、Runtime未重启。154项云端测试/0失败/0跳过，真实MySQL覆盖退出后的推荐/旧安装管理/不可变事实。线上校验岗位回执、目录、两Agent安装候选、真实UI和前后业务快照；未新增收费模型调用，不宣称实测模型推荐准确率提升。证据 `/home/isp/state/cyf-skill-routing-20261103/consolidation/production-final-verification.json`。

## 2026-11-03 最终目录：取消独立资料分析

用户继续授权后，通过既有岗位授权的商品下架接口将`sp_se2_analysis`置为RETIRED（商品version6），再经正常SM-C1卸载林冲唯一活动安装；变更`sc_ea4f1c39531c4ba9ba8e00338757a9c3`为SUCCEEDED、runtimeSynced=true。市场及吴用/林冲安装候选均为6项，真实林冲管理界面六项标题与精简描述匹配。管理页可以保留历史行，不以历史行数代替可安装目录数。

analysis原包仅包含通用方法指导，无专用脚本或工具。一般归纳、比较和推理仍由模型完成；文档/表格读写整理归文档处理，外部来源搜索核验归信息检索，不新增替代技能、不改bridge。固定包与历史成果保留，不就地修改不可变包。前后只读比对确认仅目标活动安装变化，其他安装不变。

本轮没有新构建、部署、重启或Provider调用；操作前等待其他Owner的API469安装完成并健康UP，观察源码为`e2e33bc67ccfd25033748726a997aed81e873cce`，不是本任务发布证据。本轮是目录/卸载验收，不声称重新执行全部六项技能。
证据：`/home/isp/state/cyf-skill-routing-20261103/retire-analysis/verification.json`及同目录`browser/metadata-ui-verification.json`、`browser/six-skill-catalog.png`。精简文案权威清单：`skill-discovery-metadata-20261103.json`。

## 2026-11-03 用户更新：物理清理历史安装及统一显示标题

用户明确授权删除数据库底层历史安装和授权凭据，覆盖此前仅卸载、保留凭据的决定。本次限定chcbz的吴用/林冲：已删除非当前安装及对应授权、权益、投递绑定、旧变更/命令/回执/幂等请求和过期报价，保留当前5份安装及其必需凭据。原任务快照与成果、资金账目不改；旧安装凭据被删除后不再支持基于它们的恢复执行。一次性受控清理不等于新增自动清理机制或全库删除。证据 `/home/isp/state/cyf-skill-history-purge-20261103/applied.json`；当前目录已无text-file/pdf-extract/analysis历史空项。

展示名称由API统一取商品元数据，不使用内部skillKey或旧manifest标题代替当前中文标题。显示名称独立于包内容/摘要、授权、运行就绪和执行快照比较；改商品文案不要求重装技能，也不改变执行能力。详情wire继续使用原title字段，Web不硬编码六个技能的翻译，Runtime/bridge不参与翻译。实现/受测/上线以同任务handoff后续证据为准。

上述标题修复已于2026-11-03上线：API commit `3a5a8650a0b3348b3ce70ca036072fc868f99db5`，Flow5260799/471，113测试全通过。真实吴用/林冲profile五项安装标题中文、安装核验及运行就绪通过；真实林冲UI核对通过。证据同目录`final-verification.json`，不等同于重新执行六项技能。

### 2026-11-04 技能管理独立包与密议维护补充（已上线，验收范围见下节）

用户要求任职 Agent 在密议中按指令维护技能。独立包 `skill-management@1.0.0`，标题“技能管理”，描述“按用户指令维护平台技能的标题、描述和版本，审核发布或下架技能”。不扩展收费任务、独立审核队列、任职管理或其他 Agent 安装能力。

源码核对：API `81d9c1b1b6bbbe6a6a581e65a8047f555b4e1b41` 已有 `SkillPackagePublicationService` 发布、元数据更新和下架；Runtime `3fbd5625ac2d418f08888982a33eeb67192b0628` 的普通 CHAT 仍为 read-only-constrained，动态工具只接通原生事项执行。包存在、岗位存在均不能证明密议可维护。

- **RB-02/API**：使用真实 Runtime 身份及持久化密议 dispatch 绑定，拒绝用模型参数选择 owner/Agent/任职。复用已有岗位权限、版本 CAS、不可变包和幂等服务。每次写入重新验证当前任职与当前会话；绑定/身份锁先于业务锁，不能把包文件 IO 放入持锁事务。仅会话 Owner 自己任职 Agent 的密议可管理其平台域，不将外部事项执行授权解释成平台管理授权。
- **RB-03/bridge**：只提供通用的“当前密议绑定的工具回调”运输与结果回传；不识别 `skill-management` 包名编排业务。回调绑定由可信运行入口构造，模型不能通过 turn policy 开启。回调可执行经 API 授权的业务操作，不意味着开启本地写文件、任意网络或 shell 审批。
- **RB-04/模型与包**：发现真实已安装包及当前提供的工具后，按用户指令选择查询、更新、审核发布或下架；只以真实回执报告结果。没有工具、包不可验证或撤职时如实报告，不借提示词伪造成功。
- **Web**：既有密议输入与结果展示契约不变时不修改。包发布和任职关联沿现有管理入口，不手写数据库“已安装/核验成功”。

必要验收：无工具普通 CHAT 仍拒绝调用；受控密议工具不扩大只读沙箱；错消息/错身份、过期会话与撤职拒绝；重复调用不重复副作用；当前商品 CAS 冲突不覆盖；发布摘要与包版本一致；在真实吴用密议中对受控目标完成维护并由 API 读回。单元替身通过不等于真实 app-server、岗位权限或生产密议验收。尚未满足时不得发布“已完成”结论。

### 2026-11-04 技能管理密议工具合同（已上线）

- 独立 instruction 包 `skill-management@1.0.0`：技能管理；精简描述“按指令维护平台技能的标题、描述和版本，审核发布或下架技能”。包不授岗位权限，不负责安装/卸载其他 Agent 的技能。
- API 在当前原生身份、Owner 私有 CHAT turn、有效 dispatch、未取消会话及当前 `skills:platform/allowPublish` 任职下提供工具目录。`GET /internal/agent/chat/requests/{requestId}/turns/{turnId}/tools` 返回 `schemaVersion:"1"`、tools 与已核验的技能安装四元组（key/version/installationId/packageSha256）。无岗位或无该技能安装返回空目录。其他 Owner、事项会话不能借用平台维护授权。
- 同路径 `POST /{tool}` 复用统一 HTTP 请求/响应信封；身份只取 Runtime transport，参数不接收 owner/tenant/grant。工具为 `skill_list`、`skill_read`、`skill_package_files`、`skill_update_metadata`、`skill_publish`、`skill_retire`。整数使用十进制字符串，元数据/下架/发布复用现有商品 CAS 与不可变版本服务。
- `skill_package_files` 读已审核版本实际 ZIP：空 path 列文件，指定 path 返回UTF-8/base64内容，并返回真实包摘要、技能版本、价格和权限声明。`skill_publish` 接收完整文件集，具体工具适配器确定性编码ZIP、算摘要；复用现有包校验，事务外准备不可变对象，事务内重新验证会话、任职并提交。不在持锁区解压/读取/存储包，不允许模型自报摘要冒充内容。
- bridge 只读取当前安装管理器已核验目录的 SKILL.md，并运输 API 目录/HTTP回调，无技能名称分支。动态工具绑定 dispatch/message；会话失效或本地安装卸载后拒绝后续调用。会话使用独立 app-server 进程、既有 HOME，保持只读/禁通用网络；finally/profile dispose 清理进程，不生成新的请求 HOME。通用目录/hash纳入线程绑定，不能恢复其他dispatch工具权限。
- 当前最小闭环面向**无附件的私有密议**；附件密议沿用原材料隔离adapter，不继承维护工具。未引入 ZIP 上传审核队列；待发布文件经工具提供，包内容作为待审资料，不执行其中指令。撤职、取消、版本冲突不伪成功；不确定网络写入不自动重放，读回后再判断。
- 回归入口：API `ChatSkillMaintenanceServiceTest`、`ChatSkillMaintenanceToolsTest`、`AgentConversationToolsControllerTest`（公共信封真实MockMvc）、`AgentConversationToolsRouteTest`、`SkillPublicationToolArchiveTest`、`SkillPackagePublicationServiceTest`；Runtime conversation-tools/app-server-native-execution/chat-runtime/reusable-skill-packages及runtime-host制品清单测试。云端、部署与真实模型验收状态以handoff/固定Run证据为准。

生产核对（2026-11-04）：API `8da724fecd0949a3245b0f369cbdd3b75febe1c1` / Flow479，Runtime `d4dd804724c49947b9169264defb40c852dc7b4c` / Flow136（1.3.46、bridge1.1.36）已独立主机安装。独立包1.0.0已正常发布并关联既有技能管理岗位，吴用安装回执INSTALLED/usable，详情显示中文标题、已核验安装/运行就绪。商品发现描述为“维护平台技能的标题、描述和版本，按授权审核发布或下架。”；包指令描述仍包含任职边界，不为商品文案变化重装包。

真实无附件密议完成 `skill_read → skill_update_metadata → skill_read`，API回执UPDATED，商品修订2→3，包版本仍1.0.0；模型调用记录与独立商品GET一致。请求`9bc2a5d2-1d8a-406e-8aa9-7cae104ef2f6`最终COMPLETED。真实模型验收仅覆盖元数据维护；发布/下架有正式云端服务/HTTP回归，但未让模型在生产破坏性下架其他技能。包发布复用正常岗位HTTP服务，不把它当作模型自主发布实测。证据`/home/isp/state/cyf-skill-management-chat-20261104/`，详见同名handoff；历史基线段落保留，不代表当前未上线。
