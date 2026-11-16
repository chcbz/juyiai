# 原生执行单轨收口（2026-11-16）

## 授权、Owner与状态

- 用户明确要求：删除后端文件预览转换、成果格式深度解析；Agent执行旧版本代码全部删除，只保留现行版本。
- 当前Owner：`native_protocol_owner_20261116`；任务 `NATIVE-PROTOCOL-SINGLE-TRACK-20261116`，无子Agent。
- 范围：CYF Agent执行协议链；不把公共HTTP protocolVersion、ACK存储schema、技能包版本等不同版本空间机械改成5。
- 不授权本次部署、迁移/删除数据库记录、清理生产HOME、自动重放旧任务或改变验收/资金规则。
- 状态：**仅第一处源码删除已实施，整体清理未完成，未编译/正式回归/合入/部署，不是可发布候选。**

## 固定基线

| 仓库 | commit | tree /状态 |
| --- | --- | --- |
| API | `bb4f89b7956abf0271376f957f448298101388ef` | `c8728cdd0da52b88c4b68673804960853f33b356`，开工组件干净 |
| Web | `5a1a1089b4015c4b3d9d58a800e7d21ce551467d` | `62ac7c4797ffdad3d98738261ec5004d425a430a`，开工组件干净 |
| Runtime | `6519b79070c3efb3dc47e470554392dfc95e72eb` | `53246296d5349fb3258327da07cecd57a9015587`，开工组件干净 |

根仓已有其他Owner修改，不覆盖/捎带提交。台账首次claim使用已有agent名字被拒，随后用本任务唯一Owner成功；未接管原任务。
规则已读：根/API/Runtime AGENTS、文档入口、编排README、RB-1、技能主spec。原型/前端正式修改前须补读具体原型与接口合同。

## 已确认的调用事实（源码，不是线上流量证明）

1. `PersonalWorkspaceExecutionServiceImpl.create(OwnerScope, SkillExecutionService.Create)` 创建v5；Runtime `skill-executor.mjs`/`skill-conversation.mjs`已只接纳v5。
2. API另有 `create(OwnerScope, CreateCommand, String)` 旧PRIVATE/TASK路径，未显式写protocol版本；旧Web `usePersonalWorkspaceExecution.js`仍向POST `/personal-workspace/executions`发请求。不能把“会话只派发v5”当作全部旧创建/派发已删除。
3. `runtimeExecution`原先仅拒绝v4以及CONVERSATION非v5，PRIVATE/TASK非v5仍可进入。旧start、runtimeQueuedCommands、stageOutput、commitOutput、fail等需按完整调用图退役，不能仅删一个else就宣称完成。
4. `createConversation`旧入口已拒绝，但旧DTO、受控图片V3辅助方法、结果处理分支仍在。某些v3/v4代码服务历史只读，删除执行不能导致旧成果不可访问；按Owner/任务/Chat ACL读取已提交事实，不触发执行重授权/补提交。
5. 原格式校验 `PersonalWorkspaceOutputFormatValidator` 只在非v5成果上传分支调用，不是用户验收主链，也不能据源码存在认定线上仍调用。
6. Runtime `SkillExecutionStore`仍有非v5目录/结果读取分支及descriptor式persistResult；生产入口只见 `SkillConversationLane`，但本地工具/效果相关回归仍依赖共享store，须分清已退役执行与现行工具能力，不能删除仍需要的本地脚本工具。
7. 后端预览转换还在 `PersonalWorkspacePreviewRenderer`，成果预览也复用它；本次第一处源码删除未处理该模块。前端预览接替须覆盖 `PersonalWorkspace`、`HallMaterialPicker`、`HallDraftEditor`、`HallMaterialThumbnail`、`HallMessageMedia`、`OutputPreview`及相关composable。

## 本轮已改（尚未正式验证）

- `api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`：`validateOutputUpload`只允许v5并调用原生元数据合同；删除非v5的output_1/后缀/预定MIME/内容解析fallback。没有把未知版本当成v5，也没有增加自动转换。
- 删除 `api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceOutputFormatValidator.java`，包括Office/图片重开、PDF包头包尾、UTF-8/NUL内容判断。
- 删除其专属测试及build.gradle的专属源选择；`PersonalWorkspaceConversationExecutionTest`原格式校验测试替换为null/1/2/3/4/6不可落入上传路径的负例。
- 保留存储字节数/摘要、身份与任务/版本绑定；POI依赖尚有预览调用，本轮不能删除依赖或生产类路径回归。
- 已执行 `git -C api diff --check`通过；源码Java/Gradle检索没有已删除校验类引用。**未执行Gradle，不能当测试通过。**

## 必须继续完成，不能漏掉的删除与接替

1. 先固定旧PRIVATE/TASK创建的真实UI消费者和旧Runtime命令端点；当前用户新意图走既有原生接纳链，不把历史任务转成新任务。
2. 删除旧创建/派发/start/upload/commit/fail/resume的实现、Controller/DTO/装配及废弃测试；保留“旧请求不得执行”的负例，而非保留支持旧执行的测试。
3. Runtime删除退役store/runner路径，但保留当前原生工具、未知副作用不重放、真实成果恢复及历史只读；当前恢复与旧执行恢复不同。
4. 原生协议准入为精确5，非5只读/拒绝执行；不要移除边界版本检查造成未知语义执行。
5. 旧preview/parts调用及后端转换须与前端原文件渲染一起切换。现有 `/content`授权/固定版本读取复用；新前端先可对接旧API的原文件接口，随后删除旧预览接口。旧已打开页面需刷新，不为它保留转换服务。
6. 不机械删数据库历史列/迁移脚本/备份；旧成果原字节与身份/任务归属不变。不把POI删除当所有文件处理/验收逻辑已清理。
7. 定向回归必须覆盖原生新建/续接/上传提交/原生恢复、旧协议禁止激活、历史成果只读、跨Owner拒绝、重复回执、摘要错误、取消/未知结果、正式交付验收及三个前端问题。

## 验证与发布边界

- API所有Gradle先读取相关build.gradle，使用现有编排器串行入口；正式测试/构建在203.32.84.239，固定候选600秒单次预算，不控制机重型构建。
- 本候选仅有第一处删除，旧PRIVATE/TASK正向测试会与新单轨目标冲突；需要删除其业务路径并更新消费者/测试后再作为完整候选验证，不能为绿灯简单跳过测试。
- 当前未commit、未push、未远端查询最新、未构建/部署。后续先查git diff，保留本任务与其他Owner变更。

## 2026-11-16 设计先行收口（本轮）

用户要求先明确详设、原型、接口再开发/部署验证。本轮仅修改现有文档与唯一离线原型，没有追加产品源码修改、安装依赖、构建或部署；前轮API局部删除仍未编译、未完成，不可发布。

### 已定义的唯一落点

- `specs/juyiting-ui-baseline-20261006/optimization/detailed-design.md#nf-1`：范围、保留/删除、四来源预览、格式支持、两类旧入口接替、切换/恢复、N01—N11。
- 同目录`code-frontend-design.md#nf-web`：逐文件变更、source/状态/代次模型、DOCX隔离宿主、XLSX工作线程/格式化/虚拟视窗、安全及体积边界。
- 同目录`code-backend-design.md#nf-api`：API/Runtime完整旧写链删除与当前恢复、历史只读、验收保留、测试落点。
- `api/docs/interface-catalog/critical-contracts.md#nf-wire`：路由处置、二进制/版本/身份、原异常映射、Web交接事件、正反例与消费者；统一规范及接口目录已链接，不升级公共protocolVersion。
- `web/prototypes/juyiting/index.html?scenario=original-files#chat`：原有入口增加固定样本场景；`document-preview.js`/既有CSS原地补充；规格`specs/prototype-spec.md#nf-prototype`。已有场景不受scenario控制台影响。
- 技能主spec、优化spec/tasks/acceptance同步入口与待测状态；无新同义设计文档，不覆盖其他Owner原修改。

### 本轮核实后的纠正

1. 议事/资料选择预览沿2026-10-26无下载决定，不采用前轮聊天“所有入口始终可下载”的过宽描述。资料详情/独立成果沿已有下载权限。
2. 旧写消费者还包括TaskMaterialLinks→useFormalTaskExecution与useHallDrafts对capabilities校验器的依赖，已纳入同候选删除接替。
3. 新意图只预填到密议/原事项议事，由用户发送；保留草稿冲突确认与来源内容，不机械把旧请求映射到新POST。
4. 原错误边界存在422/404/503不同映射，合同按具体入口保留，不谎称全链统一422。旧映射删除后的404/405不加兼容Controller。
5. 单工作项/summary清单/满15天托管收尾为明确业务规则，不能按“去特判”删除。

### 轻量检查与真实失败

- `node --check web/prototypes/juyiting/document-preview.js`通过。
- 根/API/Web `git diff --check`最终通过；首轮发现新增文档末尾空行，已移除。
- `./sddw check-docs --all-docs`：DOCUMENT_NAVIGATION_PASS，errors=[]；显式导出缺项仍按既有规则标不可验，不视为全文/产品通过。
- 原型Chromium真实浏览器1440/390/320：四来源下载边界，sheet/公式样本，失败→重读→成功，protected/denied/unsupported/partial，DOCX/HTML/XLS样本，Esc/焦点返回，权威状态模拟，草稿保留/替换；最终pageErrors=[]且无页面横向溢出。
- 首次浏览器失败：场景控制台被原议事层遮挡，调整本场景z-index；第二次失败：既有页面Esc逻辑与连续重开弹窗竞态，增加仅本场景预览的捕获处理/显式关闭。没有强制click绕过或跳过失败测试。第二次原日志保留browser-retry.log；首轮错误仅会话工具回执及本段归因，不伪造原始日志。
- 最终证据：`/home/isp/state/cyf-preview-sizing-20261116/prototype-check.json`、`browser-expanded.log`、`docs-check-final.log`，三张`prototype-{1440,390,320}.png`。检查脚本为本地原型诊断，不是正式应用runner或CI证据。
- 既有预览工具18786端口开工无监听，已由本任务启动供打开原型；不涉及生产服务。

### 仍须开发验证，不能由设计/原型替代

Office依赖许可证/漏洞及锁文件审查、DOCX隔离装载（含部署CSP/opaque origin约束）、真实DOCX/XLSX fixture、内存/解压风险与移动端表现、真实后台路由/权限/恢复、花荣张清业务回归均未完成。开发早期先测隔离加载，不因失败放宽sandbox或部署CSP。本文定义可支撑成套开发，但不承诺零调试、一次构建必过或一小时完成。下一步按用户后续开发指令实施；部署候选/授权另行固定。

## 2026-11-16 用户要求不增加复杂度：DOCX方案收简

已修订NF-WEB及主详设/tasks/原型规格的当前正文。前轮本handoff提及DOCX专用隔离宿主/opaque-origin脚本装载仅为被替代的设计记录，不再实施：普通前端组件解析到临时容器→复用现有DOMPurify/无脚本静态预览。删除计划中的allow-scripts、nonce/UMD/Blob脚本装载、postMessage及自建宿主；不新增服务或框架。不改公共HTTP接口、不扩大到重做Excel。

保留原文件授权、现有清洗/CSP/sandbox=""及代次清理。临时DOM不隔离解析库，最终静态隔离不保护解析内存/依赖漏洞，已在当前设计明确，不虚构安全保证。真实DOCX样式/图片清洗后表现及解析期间外链请求仍需开发验证。本轮仅文档修订，无产品代码/原型运行脚本/部署改动；前轮原型证据只覆盖当时原型，不能当新版解析方案实测。


## 2026-11-16 用户要求开发前确定：独立技术验证

本轮未继续修改业务源码、未安装项目依赖、未构建或部署。已回写NF-WEB、主详设和tasks，取代前轮“开发中验证选型”的安排；开发后的必要回归不取消。

证据目录：`/home/isp/state/cyf-preview-sizing-20261116/predevelopment/`。`probe-v5.log`及`predevelopment-result.json`实测：合成DOCX表格/四类内嵌图片、清洗安全样本、Excel解析/公式缓存与worker通过明确样本断言。发现并在独立脚本修正图片octet-stream MIME丢失、cell.value丢公式0/false；worker无DOMParser，已将设计改为主页面解析主题色。项目源未应用这些修正。

`dependency-resolution/audit-patched.json`仍有ExcelJS及uuid共两条moderate；DOMPurify3.4.18仅独立候选。不能声称依赖零漏洞。窄屏DOCX内容宽576/541大于390/320视口，展示策略尚待收口；完整Excel renderer、主题映射、Office/WPS作者样本、真实移动设备、异常/大文件边界及许可尚未全面核实。当前不标开发就绪，也不把原型或解析成功当产品验收。先完成这些开发前工作，再进入业务实施；不新增服务或框架。


## 2026-11-16 用户要求“都确认完，然后开发”：补充前置验证

沿原Owner、原三个组件HEAD，无新增业务源码修改/构建/部署。独立诊断不是正式候选测试。NF-WEB当前正文已更新确认项/环境缺项；唯一原型同步Word窄屏保留页式、文档内部横向滚动，不新增缩放框架。

新证据：`/home/isp/state/cyf-preview-sizing-20261116/predevelopment/predevelopment-closeout.json`，7份DOCX（4份元数据为Microsoft Office Word、3份LibreOffice）、Microsoft Excel及LibreOffice XLSX、损坏XML；主题色tint/索引边框、跨视窗合并、隐藏、日期/公式、1440/390/320内部滚动及稀疏百万行跨度模型。没有pageerror/外部请求；不宣称方程/所有Word能力保真，也不把作者元数据当编辑器亲测。图片/安全及worker沿前轮固定样本，不冒充整站测试。

发现的新增实施风险已提前处理到模型与详设：旧静态viewer的table display:block破坏Word布局，只在DOCX域覆盖；按最大行数循环getRow会实例化稀疏空行，改默认尺寸+例外区间坐标；主题tint按HSL亮度而不是每个RGB分量插值。所有修正仅在独立proof，产品源码尚未应用。

来源与失败：GitHub原始文件下载连接两次reset后不盲重试，改固定Git blob API并记录SHA；首次展示断言隐藏列在数据范围外导致NaN，修正样本后通过，原failure-01与日志保留。7份DOCX、XLSX及LICENSE精确来源在upstream-fixtures/authored-fixture-discovery/licenses JSON。依赖安全审计保持原moderate告警。浏览器模型不能证明任意大压缩包安全或真实手机可用。

**真实外部缺项：** 未提供可访问的目标移动设备/小程序测试环境，公开固定样本也没有取得WPS作者文件。已搜索工具，没有真实手机控制入口。按用户“全确认后再开发”的条件，不将模拟视口冒充真机、不把这两项挪到开发中后才试、不继续业务实现。需取得WPS保存的DOCX/XLSX及目标设备测试方式后继续；不影响前轮API局部未验证修改的保留，不称开发完成。

补充检查收尾：原型Word页式横向滚动1440/390/320已实际通过，证据`predevelopment/word-prototype-result.json`及对应截图；首轮复用同一页面未关模态导致诊断click被遮挡，补正常Esc关闭后重测，原word-prototype.log失败保留，不force click。`node --check`、根/Web diff检查、全量docs导航通过（`docs-check-predevelopment-closeout.log`）。npm固定ExcelJS浏览器bundle sourcemap核对534个来源，不含node-buffers/unzipper（`exceljs-browser-sources.json`）；不将Node安装图的缺license元数据机械等同于浏览器产物引入。无候选编译/业务测试/发布成功声明。

## 2026-11-16 用户明确开始开发

用户在获知WPS/真机缺项后授权“开始开发吧”，现继续既定NF方案，不再等待这些样本选型；缺项仍列发布前待验收、不伪报PASS。唯一Owner/三个组件基线不变，工作区其他Owner修改不纳入。先实现统一前端原文件展示和后台转换删除，再接替旧写消费者与退役旧执行；原身份/版本/租约/事务/正式验收规则不变。必要回归仍需固定候选，未获本轮部署授权，不安装生产。

## 2026-11-16 开发批次：原文件预览接入（未完成整项开发、未正式测试/构建/发布）

Owner、任务及API/Web/Runtime基线沿上节；改动尚在现有工作区，未提交/推送，不作为固定受测候选。根目录其他Owner修改保留，Runtime本批没有改动。

### 已写入源码，尚待正式回归

- Web新增`FilePreview/useFilePreview`，DOCX组件、ExcelJS worker、稀疏视窗展示模型；固定版本原字节、身份/请求代次、取消、URL释放、worker终止。DOCX复用既有DOMPurify与无脚本iframe；Excel只展示保存结果，隐藏sheet/行列、合并、主题tint、基本样式/数字格式沿冻结模型。
- 依赖manifest与lock均更新为冻结版本；`npm install --package-lock-only --ignore-scripts --no-audit --no-fund`完成，未安装产品node_modules、未进行产品构建。日志`/home/isp/state/cyf-preview-sizing-20261116/npm-lock-development.log`。先前独立审计的两条moderate仍未被宣称消失。
- 已改`usePersonalWorkspace/useOutputs`只取`/content`，接入资料详情、议事资产、资料选择、草稿结果、独立成果；删除3处“已回话”Toast；资料卡只用图标。选择器/议事没有新增下载，资料详情和独立成果原有下载保留。
- 调用图补齐两个真实消费者：`hallReferenceImageSelection.js`继续授权读取固定图片原件并自行管理缩略URL；`BountyExecutionOutputs.vue`及`JuyiHall.vue`选中成果验收弹窗同用FilePreview，保留原摘要/长度校验与验收状态。不能只搜`/preview`字符串而遗漏通过composable间接读取的消费者。
- API删除`PersonalWorkspacePreviewRenderer/AgentTaskDeliverablePreviewAdapter`及两类preview/parts路由、专属服务方法/DTO/转换测试。原`/content`流式读取、JWT scope、存储完整性未改变；原上传/追加版本/归档/验收未删除。前轮格式validator删除仍保留待验状态。
- API定向测试已改写退役路由不可达、原字节不解析/不转码、作用域、关闭输入流；Web补充共享viewer生命周期/公式缓存/稀疏合并模型测试，改写workspace原文件与静态接线测试。**写入测试不等于运行通过。**
- 移除成果读取中的64MiB前端/旧派生读取上限；保留实际存储政策和字节完整性，不新建文件大小/解压时间门槛。

### 本机轻量诊断与修正

- SFC parse/compileTemplate（仅语法，不打包）、改动JS的`node --check`通过；结果`/home/isp/state/cyf-preview-sizing-20261116/product-syntax.log`。前次错误：PersonalWorkspace批量替换误伤相邻版本操作模板，已按本地HEAD恢复那些原操作后局部替换；无脚本纯模板组件被诊断器误判，已修正诊断器。没有把前次失败改写为通过。
- 定向eslint最初发现已无用`exactBoolean`，随后发现新增DocxPreview属性换行；均已修正。最终运行退出0，日志`/home/isp/state/cyf-preview-sizing-20261116/development-lint-final.log`（仅该次静态检查，不是全站lint/正式回归）。Browserslist旧数据提示未借机更新依赖。
- `output-preview-document.test.mjs/output-preview-pdf.test.mjs`静态源码接线断言通过，不当作浏览器/网络/Office渲染验收。
- 审核API删除差异时发现辅助删除范围误含`scope/upload`方法，已立即逐字恢复本地HEAD原鉴权和上传方法；最终删除清单仅派生预览分支。尚无Java编译证据，不能称后端测试通过。
- 未运行Gradle、Web全量测试/生产构建；未使用Flow、未碰生产服务或数据库。

### 必须继续，不能标任务完成

1. **旧执行链尚未删除**：Web私人/正式执行入口→同密议/同事项议事预填、冲突确认；`useHallDrafts`旧capabilities依赖；API旧create/dispatch/start/upload/commit/recovery及DTO；Runtime非v5 store/结果分支。不能把前轮上传guard和本批preview删除说成单轨切换完成。
2. 继续迁移受影响组件测试：多个既有SFC测试使用手工import替换/老preview假数据，仍需按新FilePreview/source合同改齐；重点`rich-document-preview/entries-browser`、draft/prototype/overview/workspace组件、bounty gallery/inline、unified-discussion材料及原浏览器smoke。不应删除整个相关测试或跳过失败。
3. 尚未实跑新测试、打包验证worker/CJS互操作或浏览器集成；补齐旧链删除后固定完整候选，通过现有SSH worker `203.32.84.239`进行必要测试、分层、fresh包。仍按每次600秒，失败先归因，原证据保留；不自动在控制机重型构建。
4. POI不能全库机械删除：当前生产源码`UserController`仍用`ExcelUtil.importExcel`；common还包含Word/Excel工具，starter有生产POI类路径测试。agent转换生产引用已删，但依赖应结合真实最终runtime图处理，当前未改全项目POI依赖或跳过classpath测试。
5. WPS作者样本/真机小程序未验、独立安全样本不等于所有恶意/巨型Office安全；许可证随产物交付及最终依赖安全状态仍需核对。部署未获本轮授权，不安装。

## 2026-11-16 继续实施及发布授权

用户明确要求“全部完成，并进行部署”，覆盖前文未获部署授权的当时状态。继续同一Owner与任务，先完成余下实现与必要回归，再固定组件完整commit/tree并按现有SSH worker构建、原受控安装事务发布；不发布未测试WIP，不将旧包或他人候选作为本次完成证明。实际部署结果另记。

## 2026-11-16 接续：直接删除旧接口、统一上线（开发未完成，禁止把本段当发布成功）

用户明确授权“旧接口直接删除后统一上线”。继续原Owner及固定组件基线；未提交、未push、未执行SSH正式构建或任何生产安装。本段记录实际工作区源码，不称受测候选已固定。保留其他Owner脏修改。

### 本次已落源码

- API删除 `PersonalWorkspaceExecutionController` 的 capabilities/create/revoke 映射与请求DTO；保留JWT owner history/list/get/request。删除整个 `PersonalWorkspaceRuntimeFileController`。
- 删除旧 `create(CreateCommand,key)`、`createConversation`、start/queue/input/stage/commit/fail/revoke执行链、PRIVATE归档与旧TASK发布辅助链。仅保留 `SkillExecutionService.create` 的原生执行入口；Runtime准入在解析授权scope时即排除所有非v5/非CONVERSATION行，历史读不改持久状态。
- 原生 `withConversationRoot` 去掉受控v2/v3执行分流，保留root/grant/会话代次/租约及结果事务。历史已提交成果仍保留原ACL与字节证据读取（历史读取需要的v3描述核对不是恢复执行入口）。
- `WorkspaceExecutionWire` 不再序列化旧command；历史`runtimeCommand`始终null；未完成退役记录显式透出`recoveryStatus=UNSUPPORTED_RETIRED_PROTOCOL`，不将旧任务恢复/重放。
- 补齐先前漏掉的三个真实旧create调用方：删除协作POST，仅留带会话ACL的GET；删除返工执行POST及`AgentTaskReworkExecutionService`接口/实现，正式交付/验收保留；删除Hall draft的CREATE/REVISION/TASK_ACTION提交分支，shared submit只保留TASK_CREATE，旧已提交请求只能经只读接口查询。
- native认证allow-list删除旧workspace queue/input/output/start/failure/commit通道；`NativeConversationWorkMapper`查询只发现v5 CONVERSATION，退役行不再发WORKSPACE_FILE唤醒。
- 更新少量HTTP退役/只读及wire测试；`SkillExecutionServiceTest`扩展PRIVATE/TASK/CONVERSATION的1—4协议拒绝并断言旧公开方法缺席。**尚有旧Java测试引用删除的类/方法，未编译，不能发布。**
- Runtime store只接受v5且在建目录前拒绝旧协议，删除persistResult旧分支，保留原生结果/输入receipt/恢复；local-script测试改走原生结果并保留receipt防冒充断言（本次仅语法检查，未跑本地脚本隔离/进程测试）。
- Web完成前轮预览消费者测试迁移：真实FilePreview加载器替代旧派生parts mock；JSON归入文本；失败清理Blob URL；固定版本重新预览重置source key。未完成旧执行UI的预填替换。

### 实际轻量诊断（不是SSH正式构建/安装证据）

证据目录 `/home/isp/state/cyf-preview-sizing-20261116/continuation/`。
- `runtime-store-diagnostic.log`：store 13项通过。
- `web-preview-diagnostic.log`：基础预览64项通过（为子集，不能与下项机械相加）。
- `web-preview-consumers-08.log`：13个定向Web suite，245 passing/0 failing，15秒。仍有Vue测试harness未注册组件警告，不称零告警；这些包括尚未迁移的旧执行UI行为，不证明旧协议已端到端退役。
- 原始失败保留：web-consumers 01—06 / renderers01 / consumers-final / requirement07等日志。最后两项分别是漏迁移的原文件fixture、统一renderer使用全局URL而旧test仅mockworkspace URL；修正真实HTTP fixture/真实FilePreview注入与逐例恢复URL spy后08通过，不重标前失败。
- API/Web/Runtime `git diff --check`通过；改动Java仅词法括号平衡检查通过，**不是Java编译**；local-script test `node --check`通过。

### 必须继续、尚未解决的具体链路

1. Web `PersonalWorkspace.vue` / `usePersonalWorkspaceExecution.js`、`TaskMaterialLinks.vue` / `useFormalTaskExecution.js`、HallDraftEditor/useHallDrafts仍调用旧写接口及capabilities。须按NF预填契约一次替换，不部署当前后端删除候选。
2. 新密议尚无conversationId时，ChatPanel现有attachMaterials依赖已存在会话；直接预填不能自动POST，`useHallConversation`现有onConversationResolved发生在stream开始后，不能用它先发送无资料再补关联。`ChatController`现有会话创建只在/stream内部，/conversation/update只是更新，不是ensure/create。**需补齐首次显式Send的固定资料授权/会话创建衔接合同与实现；不得丢失资料、造inputRef或先发假消息。** 既有设计对此不充分，本段纠正，不再宣称全部调用链已核实。尚未新增端点/服务或改chat DTO。
3. Runtime主文件仍有旧实际消费者：`conf/codex-bridge/agent-client.mjs` 的 poll/start/stopWorkspaceFilePoller、WorkspaceFileBridge执行、注册workspaceFileWorkNotifications；`conf/cyf-agent-runtime-v1/lib/execution-adapter.mjs`的WORKSPACE_FILE唤醒。API/chat `AgentWebSocketHandler`仍注册并回送该通知能力。须整套删旧执行/恢复及能力宣告，不能仅以store只接v5宣称Runtime已单轨。共享workspaceFileApiOrigin/root及本地toolchain仍被当前native使用，不可按名称批量删除。
4. 旧DAO/mapper执行写方法仍需查无当前调用后清理；历史数据/已提交内容不删。`NativeConversationWorkDiscoveryMySqlTest`及WorkspaceFileQueueMySqlTest等专项测试要同步真实SQL退役边界。候选检索清单`api-test-migration-candidates.txt`仅宽搜索（含同名无关CreateCommand），不可据此批删测试。
5. 固定最终三组件commit/tree后，按现有SSH worker编排执行必要测试/构建/打包及600秒单次预算；统一受控安装及真实健康/业务/原文件权限验收另记。未运行Flow、未部署任何半套、未执行花荣张清回归；WPS作者样本/真实目标小程序设备仍无新增证据。

## 2026-11-16 再接续：Runtime旧执行通道与队列收口（仍未完成、未部署）

沿原任务/Owner和三个组件HEAD；本段均为未提交工作区改动。未执行正式SSH构建、push或生产安装，不将本段当作统一上线证明。根目录其他Owner改动未纳入。

### 本轮真实源码改动

- Runtime `agent-client.mjs` 删除旧 WorkspaceFileBridge 实例、文件执行/模型输出落盘辅助、HTTP旧队列轮询、生命周期启动/停止、旧通知能力宣告及清理回调接线。保留当前原生会话执行、E05租约/结果流程及其共享配置/目录/toolchain。
- 删除 `workspace-file-bridge.mjs` 及其专属旧执行正例测试。两个当前消费者只需要的 HTTPS/loopback origin 校验移到小型 `native-api-origin.mjs`，保留同一边界而不带回旧执行器；同步 managed-chat-scope-config、typed-inspection-runtime 和现有运行依赖闭包清单。
- `runManagedCommand` 对退役 commandType/actionType/manifest 在通用executor回退前直接拒绝；E05原有绑定验证先行，避免改变该独立当前协议的错误语义。`agent-message-wire.mjs` 删除旧文件manifest长度适配，旧文件命令直接拒绝解码，不转换成当前协议。
- Runtime execution-adapter 删除 WORKSPACE_FILE 唤醒协商、绑定和分发。API `AgentWebSocketHandler` 删除相应订阅集合/能力回执/唤醒目标，只保留原生会话订阅和原身份/代次检查。
- API mapper/DAO/impl 删除无当前生产调用的旧文件队列 `listQueuedByTarget[After]` 和 v2/v3 `markControlledProviderStarted[V3]`。当前会话队列 SQL 在排序/LIMIT前固定 `execution_protocol_version=5`、`conversation_provider_started_at IS NULL`，保留原授权grant及tenant/client/agent精确匹配。历史读接口/数据未删。
- API安全测试迁移：删除旧RuntimeFileController专属正例测试；现有 AgentRuntimeSecurityIntegrationTest 补旧路由即便真实Runtime也不可准入，源读取途中身份撤销/关闭流及准入后代次变更迁移到当前原生输入/lease；ConversationLeaseWireHttpTest不再装配已删除Controller。
- 现有 MySQL专项从 WorkspaceFileQueueMySqlTest 改为 NativeConversationQueueMySqlTest，并同步既有 Gradle include，测试当前队列的退役记录不能挤占前页、精确隔离、executor grant、二进制游标与只读；NativeConversationWorkDiscoveryMySqlTest改断言旧lane不发现；notifier测试不再宣称双lane可执行。**这些Java测试尚未编译/执行。**

### 本轮轻量诊断及真实失败

证据仍在 `/home/isp/state/cyf-preview-sizing-20261116/continuation/`，不作为SSH正式候选构建/发布证据。

- `runtime-retirement-01.log`：8项通过（早期子集）。
- `runtime-retirement-consumers-01.log`：扩展诊断失败且停滞，精确终止本任务测试父/子进程；原日志保留。发现E05错误语义被过早退役判断改变，已把退役检查放到原E05绑定验证之后。
- `runtime-heartbeat-isolation-01.log`：单独用例15秒测试deadline取消，捕获 `ReferenceError: isExactImageGenerationResult is not defined`。原因是旧文件执行段删除时误删了通用Codex事件解码器共享的小函数。已在通用executor旁恢复这个事件判定函数，**没有恢复旧文件执行器**。此测试deadline只约束诊断测试，不进入服务/业务请求。
- `runtime-retirement-consumers-03.log`：修正后34项通过，含原E05心跳/租约/结果恢复与当前原生poller、退役命令拒绝。不是全部Runtime suite。
- `runtime-retirement-consumers-02.log`：9项定向通过，含WebSocket退役通知拒绝与当前原生唤醒（与其他日志有重叠，不累加总数）。
- `runtime-origin-consumers-01.log`：当前 managed-chat-scope-config/typed-inspection-runtime 34项通过。
- `runtime-wire-retirement-01.log`：6项通过，包含旧manifest不再适配/解码与现行wire边界。
- `runtime-undefined-check.log`：ESLint命令配置格式不匹配失败；`runtime-undefined-check-02.log`改用该安装支持的显式旧配置模式后 no-undef通过，仍有工具弃用提示。未改全局工具配置或依赖。
- 三组件 `git diff --check`、改变的JS语法、Java词法括号检查通过；Java词法检查不是编译。最新收束诊断另见 `runtime-retirement-final-diagnostic.log`，最终结果须读实际日志，不继承前次结果。

### 接续仍必须完成

1. **Web旧执行UI/旧capabilities/草稿提交消费者未迁移**；必须完成同语境显式发送前的预填及冲突确认。
2. 新密议首次显式Send的固定资料授权/建会话衔接仍未实现；前文发现继续有效，不能自动POST/发假消息/丢资料/造inputRef。
3. API旧服务测试仍引用已删create/commit/queue/types，特别 `PersonalWorkspaceExecutionServiceImplTest`、`PersonalWorkspaceConversationExecutionTest`、两个Native*FenceTest（部分实际是旧协议fixture）、旧Rework/ControlledV3和Hall draft提交测试。**当前API不具备可宣称编译通过的候选**；按风险迁移到当前v5/只读历史/退役负例，不跳过必要安全用例。
4. 重新检查剩余DTO/控制器死辅助、当前文档与真实调用图，完成后固定commit/tree与Owner状态，经203.32.84.239现有入口正式测试/构建/打包，统一受控安装及健康/业务验收。没有发布半套，也没有执行花荣/张清线上回归。
5. WPS/真实小程序设备、完整新Office产品bundle/worker浏览器验收仍不能从本轮诊断推断通过。

收束诊断实际结果：`runtime-retirement-final-diagnostic.log` 40项通过/0失败，4.947秒，覆盖旧命令/通知拒绝、E05租约/结果恢复/心跳、原生poller、origin及受信配置继承的选定用例；不是全量Runtime或Java/产品构建。`runtime-wire-retirement-01.log` 6项和 `runtime-origin-consumers-01.log` 34项为各自定向范围，不与重叠日志相加冒充总覆盖。当前无本任务在途构建/测试/安装进程，未提交任何组件；接续仍从上述待完成1—5推进。

### 2026-11-16 page-return 固定分支集成（本地，未发布）

按用户明确要求合入 GitHub 的 `codex/page-return`：根分支固定 `c71b9c544899ede0020a48579b364912849ae7aa`，合并提交 `94300286e6d279f9d8e8853cb4d0fe98d559d6e5`；Web固定 `d52f808e5897b2b5f9ae82a937822c685f3535fa`，当前 develop 已快进至该提交。API/Runtime未追踪其他任务HEAD。原预览/协议退役WIP恢复，根其它Owner改动未覆盖。临时stash和恢复前patch保留在 `/home/isp/state/cyf-preview-sizing-20261116/page-return-integration/` 所记位置；不把WIP当分支已提交内容。

冲突合并保留page-return的身份/语境/草稿检查、picker确认中保护及原文件FilePreview；详设/原型两套相关章节均保留。`combined-diagnostic-01.log` 本地轻量诊断83项通过（page-return、overview、discussion materials、file-preview），仍有测试替身缺少组件的Vue警告；不是正式worker测试/构建或生产验收。继续完成上述未迁移的真实消费者和API测试，不能据此发布半套。

#### 同轮继续开发与结果（不改变未发布状态）

- Excel原文件投影补齐General默认对齐（数值/日期右、布尔/错误中、文本左，明确对齐优先）；富文本片段只覆盖自己声明的字体属性，避免无字体片段重置整个单元格字体。既有原型样本与规格同步，新增两项投影用例。
- 组合测试替身补齐`HallMessageWindow`，避免合并后缺组件的无效VNode警告。`combined-diagnostic-02.log`因误在根目录执行Node入口而失败（依赖解析失败，未运行用例）；改回Web工作目录后的`combined-diagnostic-03.log`85项通过/0失败、约7秒。仍有overview测试未stub的var-icon警告，不冒充浏览器全功能验收。
- API补齐当前结果通知的单轨条件：`signalProjectionAfterCommit`只接受协议5，不再仅排除4而放过其它旧/未知协议。原事务后通知、回滚不通知、通知失败不改提交事实均保留；对应测试补null/1/2/3/4/6不入通知队列。
- 两个ControlledImageV3测试类的已退役DTO正例改为退役契约断言（原生inbox唯一Command、旧start/input不暴露、历史owner入口只读）；清除无调用的旧command/asset构造。保留其它测试仍引用的真实认证事务fixture，未跳过Native*Fence安全用例。**Java尚未编译验证；这不代表其余已知旧测试引用都已修复。**
- Web/API `git diff --check`通过。除page-return既有合并外，本轮业务WIP仍未提交/推送/正式worker构建/部署。旧执行UI预填、首次私人Send资料链、其余API测试迁移仍是必须完成的剩余项；不能宣称整体开发完成。

## 2026-11-16 架构复审：不接受当前WIP作为可发布候选

本节响应用户“把所有改动重新审核一遍，统一长期方案，不要打补丁”。本轮只读源码/差异并修正文档，不继续业务开发、不提交组件、不构建、不部署。此前“设计已全部确认、可直接一次开发完成”的口径撤回；保留历史诊断，不重标通过。

### 范围及证据边界

- 固定根HEAD `94300286e6d279f9d8e8853cb4d0fe98d559d6e5`，Web `d52f808e5897b2b5f9ae82a937822c685f3535fa`，API `bb4f89b7956abf0271376f957f448298101388ef`，Runtime `6519b79070c3efb3dc47e470554392dfc95e72eb`；均为本地核对，不代表当前远端/生产版本。
- 三组件WIP范围清单：Web43、API54、Runtime15，共112个改变/新增/删除路径。另有本任务NF文档与已合入page-return差异；Web page-return提交区间独立涉及34个路径，不与WIP机械累加。
- 快照、各文件SHA256及完整跟踪差异：`/home/isp/state/cyf-preview-sizing-20261116/architecture-audit/{scope.json,web.diff,api.diff,runtime.diff}`。删除文件摘要为null。范围清点不是每行正确性证明；下表为已沿真实调用链核实的发现，不声称112文件均已动态验证。
- 根目录其他Owner的材料职责/租约/目录/密钥/音频技能等修改不属于本任务；不合并其成果为本任务完成证据。

### 已证实的问题及处置

| ID/级别 | 事实与源码锚点（路径相对组件根） | 影响与处置 |
|---|---|---|
| A01 阻断 | API删除PersonalWorkspaceExecutionController创建/capabilities/revoke；Web `usePersonalWorkspaceExecution.js`仍GET capabilities、POST executions/revoke，PersonalWorkspace、TaskMaterialLinks/useFormalTaskExecution仍使用；useHallDrafts仍读capabilities | 生产者/消费者未同步。必须迁移真实调用方后同候选退役；不能上线后靠404或恢复旧执行接口补救 |
| A02 阻断 | API `ChatTypedDiscussionAdmissionService.admitInternal`校验bounty/task binding/assignment；`ChatTypedDeliberationContextService.resolve`要求taskId；`PersonalWorkspaceExecutionServiceImpl.create(SkillExecutionService.Create)`要求taskId/taskGrant并锁任务根；运行输入/结果也经过withConversationRoot | 当前v5原生执行不是可直接接入的无任务私人执行。NF“带入密议后复用现有原生链”缺少接替能力；不仅缺首次建会话。不能伪造taskId/隐式创建正式事项/只把taskId改可空 |
| A03 阻断 | ChatController首次会话在stream内创建；Web onConversationResolved在stream启动后；ChatDeliberationService.authorizeInputRefs只接受type/id的conversation/task/message。JuyitingAgentRelayService.trustedTaskMaterials在无taskId时返回null；ConversationLinkService的关联API依赖已有会话 | 固定文件版本不能塞进inputRefs；关联资料也不等于当前执行已获输入授权。首次显式发送的会话归属、授权快照、幂等受理必须设计完整，不能先无资料派发再补挂 |
| A04 阻断 | HallRequestDraftServiceImpl只保留TASK_CREATE提交分支；前端HallDraftEditor/useHallDrafts仍有旧CREATE/REVISION/TASK_ACTION编辑/提交与能力查询 | 旧协议退役不等于删除业务能力。新建需求、正式议事、改稿、历史查看要分别映射到实际现行入口；不能统统改成字符串预填。正式返工需保持原delivery/decision版本及因果来源 |
| A05 阻断 | API测试仍引用已删CreateCommand/InputSelection、stageOutput/commitOutputs和AgentTaskReworkExecutionService；build.gradle相关source set仍纳入PersonalWorkspaceExecutionServiceImplTest | 静态即存在编译阻断；本轮未执行编译。删除旧正例/反射检查“类不存在”不能替代v5权限、事务、重复提交、结果丢失和历史只读回归 |
| A06 需修正 | PersonalWorkspaceServiceImpl仍维护PREVIEW_MIME_TYPES、previewCapability和READY/UNSUPPORTED；Web新增filePreviewKind再判支持 | 展示支持的责任仍重复。API保留真实MIME/版本/可访问性，浏览器支持性归共享renderer。相关展示字段/消费者同候选收口，不继续两边加格式列表 |
| A07 需修正 | HallMaterialThumbnail删除全部图片读取改成图标；BountyExecutionOutputs删除expandedUrl放大层；useOutputs原text/csv支持迁移后filePreviewKind没有CSV | 用户可见能力倒退，不是去转码的必然代价。保留原图授权读取缩略图和放大交互、CSV原文本展示；不恢复旧preview接口 |
| A08 需限定 | 新DOCX/ExcelJS/SSF渲染、worker、主题/格式投影已写；XLSX仍完整解压/加载工作簿，虚拟化仅控制可见单元格；DOCX异步返回可丢弃但解析不能真正中断 | 不宣称任意文件无内存风险或完整Office保真；安全展示复用已有清洗+静态iframe。不得为此新建文档服务/脚本宿主，也不得随意新增文件大小门槛。实际包体、目标设备、复杂样本另验 |
| A09 需限定 | page-return协调器只管理页面现场、精确owner/target、草稿冲突和既有资料关联意图；validTarget对chat要求已有conversationId | 保留用户明确要求的合入，不让其变成首次会话创建器、原生执行器或全站草稿框架。localStorage readback不是数据库CAS；后台仍负责权限和幂等 |
| A10 正确方向但未全验 | Runtime删除旧file bridge/通知/轮询，store仅接v5；API队列在LIMIT前筛v5且provider未启动，结果通知仅v5；历史owner输出读取没有被统一v5判断直接删掉 | 保留单轨方向、当前执行恢复与历史只读。共享origin/toolchain/current checkpoint不能按旧命名批删；已发生共享解码函数误删并修复，说明必须按调用图清理 |

补充：Runtime `runManagedCommand`对旧commandType/actionType及manifest形状拒绝后仍有通用executor fallback。需要按现行命令合同核对准入集合；不能把“出现inputManifest字段”当作所有命令的版本判定，也不能仅以文件执行器已删除宣称所有未知执行都无法回退。这是剩余调用图核验项，不在无用例证据下宣称存在可利用漏洞。E05重派、管理命令、HTTP协议版本、本地存储schema不是旧文件执行协议，不按数字/名称批删。

### 长期架构裁决（修正方向，不冒充已实现）

1. **原文件是唯一文件事实。** 上传/存储/授权读取保留原字节、版本、摘要和长度；预览不生成另一份业务成果，不读Office内容判业务合格。API现有Excel用户导入仍使用POI，与本次预览/成果验收解析不同，不全库删除POI。
2. **展示只有一套实现，资源权限不强行合并。** 页面提供可信身份epoch、固定资源引用及现有鉴权读取函数，FilePreview选择格式renderer并管理取消/URL/worker。资料、成果、会话asset继续用各自已有授权接口；不另开公共无鉴权地址。缩略/全屏是展示方式差异，不是另一套执行链。
3. **业务发起留在既有业务层，统一执行不统一成一个无差别按钮。** 私人对话不自动创建正式事项；正式事项保持承办/任务版本/资金/验收边界；返工保持交付链和决定版本。草稿/预填只是UI，不是授权或受理。明确发送/确认之前不产生执行副作用。
4. **所有Agent复用同一原生执行内核。** API产生授权后的不可变执行快照，Runtime只落实目录/身份/进程隔离、原文件输入、执行、成果提交和现行恢复；模型编排、工具处理文件。不能按花荣/张清/吴用名字分支，不能按Provider品牌在通用层写业务步骤。
5. **私人/任务两种业务上下文不等于两版执行协议。** 保留两者必须有的授权差异，收敛在API准入与结果归属责任处，再共用执行内核；不能沿Runtime每一步复制两条流程。当前实现只有任务授权的这条v5链，若要承接旧私人生成，必须补齐现行内核的私人上下文合同。禁止借旧PRIVATE协议复活、隐藏任务或宽松null校验假装统一。
6. **接替方案要以“业务意图→权威受理→授权输入快照→执行→成果→业务归档”闭环定义。** 输入引用与会话/事项关联是不同事实。必须明确首次会话与request键的稳定绑定、同键同体重放、响应未知查询、关联失败不派发、结果原版本归档和明确取消。不能用“映射现有机制”代替这些合同。
7. **原完成权威不变。** API判断受理/执行结果/正式交付/验收完成，消息、流EOF、预览成功不代表完成。删除误导Toast合理；不换成另一个推测完成提示。保留身份、ACL、不可变元数据、租约、fence、CAS、事务、幂等和未知副作用保护。
8. **历史只读与现行恢复分离。** 旧未完成记录不自动FAILED、不自动重跑；已提交原成果可按原权限读。现行执行恢复继续使用原执行/效果/结果日志，不换幂等键创建新执行。部署回退不能重新激活旧队列。

### 改动归类与实际影响

- **保留并修正细节**：共享预览组件/现有授权原文件读取/Office按需加载/静态安全展示/删除误导Toast/page-return合入/旧队列退役/current恢复与历史只读。
- **整体重做接替设计，再实现**：旧私人执行和旧草稿提交到现行原生入口的映射；首次显式发送的资料快照与稳定会话/请求绑定；正式返工的完整因果合同。不是给现有旧接口再包一层。
- **删除到调用图闭合**：后端派生预览/parts/格式深检、旧文件执行写链/轮询/通知/专属恢复、旧前端capabilities及创建/撤销消费者。当前安全测试按风险迁移，不按类名整批删除。
- **纠正不必要退化**：图片缩略图/放大、CSV展示。能力判定移回Web，不再扩API预览MIME白名单。
- **不扩入本任务**：独立密钥服务、重新设计Agent认证、全站返回/草稿框架、资金/工作项规则改造、其它Owner工作区和生产数据清理。

### 尚未完成的设计与验收（禁止再标“已全部确认”）

- 私人上下文在现行执行快照、输入来源、授权撤销、租约根、结果归属和技能授权中的准确字段/事务/锁序尚未冻结；当前taskGrant不能用假值替代。这不是Office预览的问题，但旧私人执行能力退役后必须有正确接替，不能隐性取消。
- 首次会话创建、资料选择、请求幂等的完整存储/事务边界仍需确认；本轮没有证明一个现有事务能覆盖全部写入，因此不指定未经核实的新HTTP端点，也不承诺“无需改wire/无需迁移”。
- 普通发送、typed正式议事、改稿及执行确认的准确事件/接口映射必须写进既有NF-WIRE；目前“所有预填复用/stream且wire不变”已被源码否定。
- 当前WIP没有正式SSH候选构建/三端统一安装/花荣张清产品回归；历史85项Web诊断与40项Runtime诊断只证明各自选择范围，不能掩盖API编译缺口。目标小程序设备、WPS作者样本、完整构建增量包体和大文件实测缺口仍在。

后续顺序：在既有NF详设/接口/原型中收口上述边界（不另建“最终版”）→真实消费者与生产者同候选实现→迁移风险测试并固定三端commit/tree→按既有SSH构建与受控统一安装→业务验收。设计阶段发现的问题不能留到部署后临时补丁。本次没有新增审批/框架或部署动作。


## 2026-11-16 详设重定与密议术语纠正（设计，无产品发布）

用户确认密议没有事项、成果交付，也没有归档概念；可以处理/预览文件，主动保存选定文件到个人资料。此前把保存称作“归档”的表述撤回。archive-operations仅现有文件保存接口技术名称，不新增密议归档流程/状态/按钮。

已更新既有NF主详设、前后端代码设计、接口目录、需求、任务、验收矩阵及原型规格；技能主spec明确选择目标6扩展。当前5为源码基线，目标6尚未实现；一套执行内核支持PRIVATE/TASK，真实业务授权各在API负责。新增必要结构变更，撤回无需迁移的旧承诺。保存复用现有服务但需解除bounty唯一准入；首发真实会话/请求同事务，原生执行行+既有afterCommit工作发现，不新建PRIVATE outbox。

进一步源码核对：chat_interaction_step四任务/授权字段NOT NULL；原生技能绑定必须taskGrantId/taskGrantVersion；两用量Controller使用task地址；执行表已有唯一executionId，无需新增被其覆盖的run复合索引。迁移显式执行，schema initializer只核验，不在启动时擅自DDL。新绑定精确字段在NF-WIRE，认证通道/安装事实核对不是新签名服务。

文字原型补充密议文件卡、保存状态及无交付/归档；本轮未更新离线HTML，不宣称该原型全部已实测。未改业务代码、未构建/迁移/部署；既有WIP和编译/测试缺口未因文档关闭。WPS/真实目标设备与最终包体仍无当前候选证据，验收N01—N14均待执行。


## 2026-11-17 用户“开始实施”：预览与元数据落地，整体仍在开发

沿既有Owner/任务，本轮转implementing；无子Agent。开工root/API/Web/Runtime现有脏修改保留；Web d52f808e5897b2b5f9ae82a937822c685f3535fa、API bb4f89b7956abf0271376f957f448298101388ef、Runtime 6519b79070c3efb3dc47e470554392dfc95e72eb，未查询远端最新、未改线上版本。证据目录`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/`保存开工diff、当前源码hash及诊断日志。

### 本轮实际源码修改

- Web共享filePreview恢复CSV安全文本识别；通用MIME仅按已确认后缀尝试，具体MIME冲突不放宽。HallMaterialThumbnail恢复鉴权固定版本原图缩略，复用usePersonalWorkspace+useFilePreview的独立URL/身份代次清理，Office缩略不读取Office字节。
- FilePreview新增可选图片放大交互，由BountyExecutionOutputs开启，复用同一已鉴权Blob，不新增下载/再次读取；关闭/Esc回焦点、身份/资源切换清弹窗。删除Bounty旧失效放大CSS。修复原WIP将key放在非v-for template上的lint错误，真实容器按source.key重建，防旧解析实例沿用。
- 密议文件操作/保存文案统一“文件操作”“保存到个人资料”，个人资料来源显示“Agent生成”；内部archive-operations名称及幂等/恢复逻辑不改，不新增归档业务。旧私人执行表单尚待整体删除，不能因此声称全部旧文案已经消失。
- API删除PersonalWorkspaceViews/PersonalWorkspaceWire中的previewState/capabilities.preview，以及ServiceImpl的浏览器MIME/mediaFamily白名单；保留文件身份、固定版本、真实MIME、长度/hash及读/写/下载能力。同步所有已查到的Java构造消费者与源码测试，新增HTTP响应不返回浏览器支持性字段且完整元数据不丢的断言。未运行Gradle，不能当Java编译/测试已过。
- 同步现行接口目录§2返回字段，不保留一份与NF冲突的当前DTO；历史预览DTO标退役。Web测试fixture去除previewState，不靠旧字段验证新客户端。

### 诊断与原失败

- 197项Web定向诊断PASS（13秒），覆盖共享预览/资料/消息/选择器/成果/静态清洗相关消费者；另外保存/正式动作相关40项PASS（1秒），与197有重叠，不能相加当237个独立用例。CSV字面文本、图片放大回焦点/同Blob/身份清理、缩略原图与Office不预取等新增真实组件断言。
- 相关预览组件/util/worker/保存composable ESLint最终exit0；只剩现有Browserslist数据年龄提示。Web/API diff检查通过。以上是控制机轻量诊断，不是SSH固定候选正式构建或全局业务验收。
- 初次组合入口漏用项目tsx导致JSON import attribute错误；按既有入口补`--import tsx`，不改应用JSON加载方式。随后扩大消费者检查，因page-return已合入而测试动态加载器未注入真实新模块，先root hook失败、再178PASS/19FAIL；已按真实模块补齐三个现有加载器，重跑197PASS。原失败日志全部保留，不删除失败用例或伪造通过。
- 源码与诊断绑定见`source-receipt.json`；没有应用构建、生产迁移、安装/重启或真实Agent调用。

### 仍需连续完成（不可发布）

1. NF执行6的PRIVATE/TASK唯一内核合同、API受理事务与真实conversation、materialRefs固定授权、现有task硬绑定解除；运行地址/技能binding/usage/effects/当前恢复三端闭包。
2. 必要DDL及schema/row mapper/NULL语义、现行5在途与投影/用量安全收尾和受控切换；本轮没有新建migration资源或执行DDL。
3. 资料→密议与事项资料→原议事的真实接替，删除旧私人执行表单/旧capabilities消费者、正式改稿因果接替；旧执行Java测试仍有已删DTO引用，未解决API全候选编译。
4. 会话asset投影/读取/保存解除bounty唯一准入；保留同会话ACL、显式保存幂等、文件独立保存事实，不把放开按钮当后端完成。
5. 固定完整候选SSH必要测试/构建、设备及Office样本回归、获授权统一安装及花荣/张清验证。不得将本节预览诊断当上述完成证明。

## 2026-11-17 续实施：Runtime6唯一执行合同（源码及轻量诊断，未发布）

同一Owner继续，未创建子Agent、未合入/提交/安装。根/API/Web/Runtime HEAD仍沿上一节固定基线，工作区其它Owner修改保留。本轮没有Gradle、应用打包、生产迁移、服务重启或真实模型调用。**整体任务仍在implementing，API仍是5的生产者/授权链，不能单独安装本轮Runtime6。**

### 本轮实现

- `skill-executor.mjs`只接收6；Command以scope={kind,conversationId,conversationGeneration,taskId}替代重复顶层task/conversation。PRIVATE明确taskId=null，TASK明确真实taskId，D1代次拒绝溢出；1–5/未知版本以及旧授权字段在领取前拒绝。两类scope继续调用同一个runNative，无按Agent名字/Provider新增流程。
- 原生`native-task-skill-binding-v5.schema.json`删除，新增`execution-binding-v6.schema.json`；codec、registry、executor和安装依赖闭包同时迁移。绑定使用executionId/scopeSha256/grantRevision及原安装/包/权限身份；原生技能配置实际消费者`native-skill-config.mjs`也改executionBinding。管理SM-C1 TaskSkillBinding/requireExact未改，不按名字删除独立管理协议。
- 同一lane和source-only usage delivery改为`/internal/agent/executions/commands`及`/executions/{executionId}/runs/{runId}`，覆盖lease/input/output/commit/effects/resume/failure/usage/provider-usage。输入快照schema6新增WORKSPACE_VERSION来源；manifest2、HTTP信封1、checkpoint本地schema、ARCHIVING内部提交阶段不机械改号。
- Runtime HTTP路由准入明确拒绝退役task地址及编码别名/query/hash，不能作为“无关internal API”透过。失败回执按相同scope/执行/run/Agent验证，QUEUED保持未知；NF-WIRE同步该运行时回执，API生产端尚待实现，不以历史owner view猜测scope。
- store、artifact session、native readiness宣告仅6；当前恢复不重复执行模型，source-only停机用量flush保留原Owner和不可知费用，不复活旧命令。旧命令扫描隔离保留，部署前必须收尾已有5的用量。
- D06通用任务命令明确限既有六种声明类型；携带原生executionProtocolVersion的任务包装和未知命令不得落入generic执行器。SM-C1/E05仍走自己的既有合同；不是把所有任务协议改6。
- shared注册fixture（Runtime与API同名副本）目标宣告改6；Node peer原生解析操作传executionBinding，独立resolveTask仍用旧管理绑定。API Java调用该测试peer的fixture仍待同步，不宣称跨语言测试已过。

### 诊断、真实失败和覆盖边界

证据仍在`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/`，`runtime6-source-receipt.json`记录本轮最终修改字节，`runtime6-after.diff`记录Runtime WIP。

- `runtime6-diagnostic-04.log`：121 PASS/0 FAIL（约5秒），六个核心suite；包括PRIVATE/TASK共用执行、私人原版本输入、scope串会话拒绝、旧命令/快照拒绝、丢失提交恢复不二次执行、用量只投递、精确技能安装绑定等。`03`之前119项，不能当另一套独立通过数量。
- `runtime6-consumers-diagnostic-04.log`：30 PASS/0 FAIL（约37秒），注册、技能包跨两个临时Agent独立安装绑定、脚本宿主安全、原生技能配置、stdin/stdout管理peer。只用临时目录，无生产安装/模型调用。
- `runtime6-dispatch-diagnostic-01.log`：8 PASS/0 FAIL（约0.7秒），普通六种TASK保留、E05拒绝未就绪、旧文件命令/未知原生包装不回退。`runtime6-install-binding-diagnostic-01.log`另2项PASS（约3秒）；与其它suite不据此累加全局业务通过数。
- 初始代码编辑误用系统Python3.6（零宽split不支持）导致部分测试fixture未迁移；切回既定Python3.11补齐，保留`runtime6-diagnostic-01`失败。`02`两项source-only flush仍断言旧task URL，迁移真实路由后`03/04`通过。
- 扩展消费者初次86项为76 PASS/4 FAIL/6 SKIP，不改写成功：注册共享fixture仍5、document-workbench测试固定1.0.0与当前源码SKILL.md 1.0.1不符、脚本fixture缺JSON schema dialect。仅修测试真实输入，没有修改技能包/放松安装器。后续误判local-file不应进入native store，新增拒绝断言失败；核对现行host-delivered receipt合同后撤回该错误假设，保留宿主摘要匹配及不允许native-model/provider伪装的断言，最终30项通过。两个失败回执`consumers-01/02`保留。
- 上述86项中的6个真实环境探针SKIP未补跑，不把它们当native shell/网络隔离/真实设备通过。native-execution/profile普通定向项仅在该失败组合内有逐项结果，正式worker候选必须重跑全部相关selector。
- `git diff --check`及文档导航通过；本机轻量诊断不替代固定干净候选SSH正式构建，也不证明生产/花荣/张清产品回归。N01–N14不因此标PASS。

### 下一步精确落点（无需重做上述Runtime设计）

1. API按NF-API.2改SkillExecutionService的PrivateScope/TaskScope/Create、Command.scope、AuthorizedSkill.executionBinding；`PersonalWorkspaceConversationRuntimeController.SkillCommandResponse`同步唯一wire，无顶层旧身份。当前API Command还是5/task必填。
2. `SkillManagementCodec.validateNativeTaskBinding`与`SkillManagementService.nativeTaskBinding`迁移executionBinding；仅原生schema，不动SM-C1 taskBinding。Service private helper当前boolean nativeV5共用安装身份查询，需保持准确安装/权限核对；新6用scope摘要和execution.grantRevision。同步Java→Node `resolveNativeTask`输入和注册能力期望。
3. `PersonalWorkspaceExecutionServiceImpl.create/skillCommand/nativeSelections`、任务/会话锁及fence根、输入授权、历史只读和执行队列/恢复/用量所有入口一起改6。不要只把数字5替换6；当前大量task根、grant、bounty强绑定必须按NF责任层实现PRIVATE。
4. DDL/schema/nullable Step、首发原意图幂等受理事务、Web旧写UI真实接替和会话asset读取/保存仍未开发完成；没有隐藏任务或自动个人归档的临时替代方案。
5. 然后清理已知旧Java编译引用、固定三端候选，按SSH worker策略测试构建；先核对5在途/投影/usage安全收尾再统一安装，分别记录花荣/张清、正式/密议及预览/保存业务验收。当前没有部署候选，不重启生产。

## 2026-11-17 续实施：API6上下文、绑定、显式DDL与队列（未编译/不可发布）

本节接续Runtime6，不重做已完成消费者；同一Owner、同一任务，保留各仓及其他Owner脏修改，无提交/生产操作。上节“API仍是5”的源码状态由本节局部实现更新，**尚无端到端可运行API6，不可单独安装Runtime或API**。

### 已落源码

- `SkillExecutionService`新增sealed PrivateScope/TaskScope、Create(scope)、Command.scope和AuthorizedSkill.executionBinding；任务生产者ChatActionExecutionService两处snapshot改6/nested scope。原SM-C1管理taskBinding不动，原生SkillManagementCodec/Service改scopeSha256/grantRevision，复用安装/权限查询。已读codec.map源码确认返回可变LinkedHashMap，无put不可变Map问题。
- PersonalWorkspaceExecutionServiceImpl创建6：TASK保持真实task根/授权；PRIVATE从既有会话生命周期锁开始、复用AgentService本人Agent授权，不造task/grant。技能选择使用实际注册proof/session fence；新workspace原版本输入和同会话asset选择不借用TASK链接权限。历史result显式只读4/5/6；其它历史读口仍须逐项审查。
- WorkspaceConversationAccessService增加withLockedAccessible，Chat实现复用lockScopedById和同一事务；NativeSkillScriptSessionLookup与typed native声明更新6，去掉脚本就绪性对taskId的无关依赖，保留真实注册身份/能力/fence。
- execution.businessScope、request.clientIntentSha256及Step两个Long nullable字段已加；新增两份显式native-v6 SQL（均未应用），不改历史JSON、不补假task。PRIVATE首发请求hash/受理事务尚未落地，字段存在不等于幂等完成。
- 两个执行/会话schema initializer改核验而不DDL/回填。重新核对发现它们**原本已经在schema-maintenance profile内**，本次是维护入口行为变化，不是新移除正常启动DDL。现有schema说明追加限定变更；删除已失去消费者的deliberation-schema.allow-additive-migration三处配置/测试属性，typed/review独立开关不动。新库测试必须改成显式DDL准备，尚未全面同步。
- 队列SQL仅发现6，ORDER/LIMIT前以互斥business_scope分支区分PRIVATE本人/空task字段与TASK准确grant/executor；保留同一keyset队列，不内连接grant误排PRIVATE。TASK关联身份改精确字节比较。新增mapper合同测试断言这些条件和分页位置（尚未执行Java）。runtime executionScope/锁根仍旧task寻址，故当前队列不是可运行闭环。
- commandView的可空task身份比较改Objects.equals，避免PRIVATE两端均NULL被非空constant-time helper错误拒绝；不改非空认证字段比较。
- Java原生绑定/Command测试fixture及Node peer调用同步；新增API/Runtime两份相同native-execution-v6-local-files.json和Runtime共享wire测试，旧5fixture只保留历史。部分旧Java删除接口引用仍未修完。

### 证据及限制

`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/api6-shared-wire-node-diagnostic-01.log`为3 PASS（约0.76秒），仅Node PRIVATE transport/input/shared fixture诊断；不证明Java序列化/HTTP路由、真实数据库或生产运行。
本轮API/Runtime `git diff --check`通过。API新增Java/SQL尚未编译、执行或迁移；没有Gradle、固定候选SSH构建、应用安装、重启或Agent实际业务调用。前轮Runtime诊断结果不替代此轮API验证。

### 下一步（真实待完成，不是新需求）

1. 首先改SkillExecutionService/PersonalWorkspaceExecutionService运行方法、controller、DAO findForRuntime及service executionScope/runtimeExecution/withConversationRoot为executionId+runId；TASK task→conversation→execution锁，PRIVATE conversation→execution锁；scope持久行与snapshot一致，PRIVATE当前目标权限重验，失败回执scope。队列调用仍传candidate.taskId必须同批改。
2. 两种usage/controller/auth matcher及cost authority地址同步，旧task runtime路由删除；历史5只读与部署前drain不混成活动兼容。
3. 首次密议/chat/stream原意图hash、materialRefs、conversation/request/turn/EXECUTE/execution/link同事务及竞争回滚；asset投影/源读取/显式保存解除bounty硬绑定。当前尚未完成。
4. Web旧执行表单/capabilities/revoke/草稿接替和真实发送；完善旧Java测试、显式schema fixtures、NULL安全TASK消费者与受影响回归。
5. 固定三端干净候选后指定SSH worker正式测试/构建；收尾5、显式迁移、统一安装、花荣/张清正式与密议及文件全链回归。N01–N14仍全部待产品验收，不更新PASS。

## 2026-11-17 续实施：API运行地址/锁根/用量6迁移（源码推进，仍不可发布）

上一轮为真实源码进展，不是等待；本轮继续同Owner，无澄清阻塞。全部仍未提交、未编译/打包/安装，不能将下述“已修改”当端到端验证完成。

### 本轮落点

- PersonalWorkspaceConversationRuntimeController唯一根改`/internal/agent/executions`，11个mapping为commands和`/{executionId}/runs/{runId}/...`，删除conversation路径段，无兼容别名。删除该Controller已无消费者的旧Provider常量/恢复DTO/helper；新的failure回执是RuntimeFailure(executionId,runId,scope,targetAgentId,state,failureCode)，不复用Owner ExecutionView冒充Runtime scope。
- SkillExecutionService和PersonalWorkspaceExecutionService的运行方法参数改executionId。实现claim/renew/inputs/inputContent/output/effects/resume/commit/failure同步，包括队列产生command时的execution地址。Owner历史输出read/list/open仍保留task参数，**私人输出读链还未接替，不能宣称文件闭环完成**。
- findForRuntime按准确executionId+runId、协议6和PRIVATE/TASK互斥权限查询；无旧execution_mode PRIVATE/TASK活动回退。runtimeExecution按owner+execution主键读/锁，再核run。TASK继续真实grant/受托executor身份，PRIVATE要求owner是executor且task/grant/assignment全NULL。
- withConversationRoot锁顺序为TASK根（仅TASK）→真实会话生命周期锁→execution→授权/输入/输出。检查持久业务scope与不可变snapshot.scope、conversation/generation一致。PRIVATE复用本人Agent权限锁，不引入grant服务；权限失效转换现有GRANT_REVOKED，让队列按既定stale策略跳过。TASK保持grant准入。requireGrantTarget源码已核实为只读，不先取得task/grant行锁。
- NativeExecutionBinding加入businessScope，输出存储I/O前后核对包含它；SkillInputPreparation携带真实taskId供Chat source adapter，不能把新route executionId误传为taskId。Chat source adapter本身的PRIVATE支持仍待下一步。
- 两种usage controller改execution地址并核对body/path同一执行；recorders与DAO去掉task寻址，经济Binding仍用持久真实taskId（PRIVATE为NULL）。Native cost SQL只6：TASK保留原executor binding、允许已取消/改版grant迟到成本证据；PRIVATE准确原owner/target与runtime身份，无假task。成本接收不执行、不恢复、不改变业务状态/资金账。
- AgentRuntimeAuthenticationFilter明确整个executions前缀进入原生凭据边界，准入/停机证据/上传fence token路由一起更新，旧task native routes不再allowed。普通六类task/work-item路径不动。StreamingFileMultipartConfiguration同步原字节上传新路径。
- 补发现NativeConversationWorkMapper仍筛5，改6；它只是target级唤醒投影，不承担新业务授权，真实队列的分页前授权继续由PersonalWorkspaceExecutionMapper承担。

### 测试源码/诊断状态

- 更新SkillExecutionServiceTest当前调用地址、businessScope和DAO mock；新增PRIVATE续租/输入无task授权、错误run/旧task作为地址拒绝、scope漂移和生命周期代次变化拒绝断言。已有TASK/受托Owner/原生效果/恢复测试保留。
- ConversationLeaseWireHttpTest同步新HTTP路由和共享fixture，新增PRIVATE失败回执、当前原生路由强制原生凭据及旧路由拒绝。两种usage controller/recorder测试迁移，新增私人用量无task与body/route冲突不写入断言。
- NativeConversationQueueMySqlTest现有未跟踪fixture从5迁移6并新增business_scope/assignment字段，追加私人/正式共队列、无grant PRIVATE仍可见、跨Owner/未知scope不占分页。NativeConversationWorkDiscoveryMySqlTest切6并保留5排除；TaskExecutionCancellationMySqlTest增加显式native-v6 DDL、改cost查询签名/原grant迟到证据和大小写隔离。**这些Java/MySQL测试均未运行**。
- `api6-route-source-diagnostic-01.log`只证明：11个Controller mapping源码精确集合、两用量path/body绑定存在、MyBatis动态SQL XML可解析、API/Runtime共享fixture字节相同（SHA256 e8f62c9cecf6a36fcf2b76fbb6b1773180c895b4c68ddb03c880597fe8231146）。不是SQL执行/HTTP调用/编译/正式回归证据。API diff检查通过。
- 已知其它旧安全fixture仍包含task native路径，AgentExternalServicePolicyMySqlTest仍用旧findForRuntime寻址；应按本轮活动6目标改正例、保留退役路径负例，不能批量替换所有旧路径把负例改成正例。历史controlled-image测试应证明不再执行，而非恢复兼容。旧私人CreateDTO测试与显式schema准备仍未全修。

### 后续顺序

1. 继续PRIVATE `/chat/stream` materialRefs/原意图幂等与同事务conversation/request/turn/EXECUTE/execution/link，避免CHAT+EXECUTE重复调用计费。当前只有基础字段，未实现受理闭环。
2. Chat asset source/open、统一projector与owner输出读取、显式保存解除task/bounty硬绑定；统一锁顺序，PRIVATE只会话文件、不自动个人资料。新运行锁顺序须与projector/取消链一起检查。
3. Web旧表单/API消费者真实接替与正式业务因果；全面修复当前候选编译引用/新库显式DDL/真实受影响回归。
4. 固定干净三端候选SSH必要测试构建；现行5执行/投影/usage自然收尾、显式迁移及统一安装，花荣/张清产品验证。仍不具备发布条件，N01–N14未通过。

## 2026-11-17 续实施：PRIVATE受理事务与execution寻址的会话文件读取（未编译、不可发布）

继续同一Owner/任务；没有新增业务澄清。以下包含上次压缩前尚未记入handoff的受理实现及本轮修正。**全部为未提交源码，Java/MySQL测试尚未执行，未固定SSH构建候选，未迁移/部署/重启，N01–N14仍待验收。** 不把上一轮Runtime诊断当本轮API验证。

### PRIVATE受理源码

- ChatMessageDTO增加materialRefs；ChatSkillSourceAccessService冻结WORKSPACE_VERSION精确版本和CURRENT_CONVERSATION_ASSET精确revision，使用真实私人会话/目标，task为NULL；PersonalWorkspaceService.readableVersion只读精确版本元数据，不取latest/转码。request mapper实际写client_intent_sha256。
- ChatDeliberationService.admitPrivate用现有事务管理器的TransactionTemplate负责首次conversation、USER、request、context snapshot、EXECUTE turn、原生execution、Step及link同事务。原始null conversationId/正文/目标/资料选择独立摘要；重放先核原摘要及当前会话ACL，不重新解析资料、不观察当前Runtime、不创建新执行。唯一键异常在失败事务整体回滚后用新事务读取赢家；禁止在rollback-only事务继续写。既有execution afterCommit唤醒保持，没有新增PRIVATE outbox或第二次CHAT模型调用。
- Controller在创建独立会话前进入私人受理；已有会话先按既有服务ACL读取真实scope，缺失/伪造private声明不得回落旧CHAT。新的推断private请求仍必须满足明确PRIVATE DTO合同，不为旧客户端猜造字段。generic admitTrusted明确拒绝private，历史读取不受影响。
- 修正factsManifest只读CHAT策略误用于PRIVATE的问题：沿同一helper传真实NATIVE_LOCAL_FILES_V1。目前该受理snapshot为skills=[]/LOCAL_FILES，**安装技能是否应如何纳入PRIVATE原生能力仍须沿冻结详设核对，不宣称全能力已完成**。
- 修正长正文：原CHAT authorizedContext超8192字节会把currentUserMessage改成dispatch.content引用；PRIVATE没有该dispatch。私人快照保留原有有标识的历史摘要，但把完整currentUserMessage放回parameters.authorizedContext，instruction只给固定执行提示，不复制/截断200000上限内的正文进入8000限制字段。原始正文摘要不变。Runtime native-execution.mjs实际传递instruction和parameters，已源码核对，不是模型端实测。
- targetAgentIds使用JSON语义精确单元素比较，不因持久JSON空白拒绝；material kind非字符串走合同错误，不再ClassCastException。
- acceptedPrivate沿已有事件观察，不发CHAT；终态判断识别RESULT_COMMITTED及INPUTS_REVOKED→CANCELLED映射。**EXECUTE turn最终状态投影尚未实现，因此不能宣称SSE正常收尾**。

### Owner文件读取/保存源码

- PersonalWorkspaceExecutionService三个Owner read/open/listConversationOutputs统一改executionId+runId，不再把taskId或NULL当寻址。实现withOwnerConversationRoot：TASK根（仅TASK）→会话生命周期→execution；PRIVATE无task/grant根；协议6核持久scope、snapshot.scope和会话generation。输出目录/不可变描述符/字节校验及I/O后重验保持；历史完成文件只读，不恢复执行。
- markProjected复用该Owner锁根，不再无条件拿task根。历史读取仍有必要历史格式授权检查，不等于旧协议活动兼容。
- 全部实际生产read/open/list调用方已定向改为持有的execution身份：BountyMedia、Projector、SelectedOutputFinalization、ActionFinal、两个HistoricalReader、SkillSourceAccess、ConversationArchive及InspectionAuthority（PreparedContent追加准确executionId）。未改用户输出URI或加入task/exec两义寻址回退。
- BountyMedia允许经request/step/link权威投影获得的NULL task，并与execution用Objects.equals比较。JdbcChatConversationArchiveStore来源SQL加入互斥PRIVATE会话分支：task/grant/assignment全NULL、scopeKey/target与单元素目标一致；原TASK分支保持。显式保存validSource接受真实NULL task，打开源文件使用executionId；不自动保存、不引入密议归档。
- **Projector仍有TASK根/bounty硬绑定和旧协议扫描条件，尚未接通PRIVATE结果、消息、asset及turn终态。仅修改其输出读取地址，不宣称完整文件链路可用。** 下一轮需整体改锁序/投影/取消/历史消息可见性，而不是只放开task空值。

### 新增测试源码与证据边界

- ChatPrivateNativeAdmissionTest新增9项：首发只有一个native执行无task/CHAT outbox；原始null重放不重新发现来源/Runtime；正文/目标/会话/资料冲突；后续link失败全部回滚；模拟唯一键败者回滚后新事务读取赢家；旧generic私人受理拒绝；代次变更拒绝；非法kind；长消息完整传递。使用真实H2事务边界+mock repository写journal，**不等于真实MySQL唯一键并发测试**。
- SkillExecutionServiceTest新增PRIVATE Owner空输出目录、execution寻址、代次变化拒绝两项；原有6运行链测试保留。MediaStreaming/ConversationArchive mock寻址同步。其它旧Owner测试仍有task寻址fixture，必须更新且保留退役执行负例。
- 本轮只执行git diff --check（通过），未运行Java或H2测试。证据目录`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/`保留private-admission-review.py、owner-output-address6.py等源码编辑记录；它们不是生产runner或测试成功证据。前轮api6-runtime-address-source-receipt不涵盖本轮修改。

### 下一步精确顺序

1. ChatBountyAssetProjector：只活动6；TASK根/PRIVATE会话根，取得会话→执行锁再查结果、资料和投影；PRIVATE no task/no grant；同事务消息/asset/Step/link/request/EXECUTE turn收尾。核对普通answer数据展示、授权历史上下文包含已完成PRIVATE回复；终态事件和SSE一致。取消必须使关联执行fence失效，不能只取消turn。
2. PRIVATE的安装技能准备/选择按原冻结合同核清并接入已有能力，不加Agent名称分支。实际MySQL首发并发/唯一键失败回滚、来源撤销、保存幂等回归。
3. Web真实materialRefs发送和旧写UI删除，Java旧接口编译引用、schema显式DDL fixture及Owner寻址测试全面同步。仍需核对PersonalWorkspaceConversationExecutionTest等历史只读授权fixture适配新会话锁，不能把旧活动协议测试恢复为正例。
4. 固定三端干净候选，按原SSH worker工具plan-only/必要测试/构建/回传。5在途执行、投影、用量自然收尾后显式DDL和统一受控安装；花荣/张清PRIVATE/TASK及原件预览/显式保存全链验证；不得部署当前WIP。

## 2026-11-17 接续：PRIVATE投影与统一取消（源码已改，尚未测试）

承接前轮尚未落盘的实现记录；本节覆盖上述“projector/取消尚未实现”的源码状态，不覆盖未验证声明。仍为同Owner未提交候选；没有编译、MySQL测试、迁移、部署或业务验收。

- ChatBountyAssetProjector只发现活动6，并以准确身份JOIN；TASK根（仅TASK）→会话→执行锁，核对scope/代次/目标；PRIVATE无task/grant/assignment。消息、asset、Step/link/request、EXECUTE turn同事务终态投影；单answer数据展示正文。失败/取消收尾，既有事件修复校验同一消息和结果。保留已有个人资料显式保存，文件消息不再暗示自动归档。
- SkillExecutionService.cancel成为PRIVATE/TASK共享原生取消入口。Task取消协调器只发现准确执行并调用它；私人取消先会话/执行再turn，不先伪造CHAT终态。已提交结果优先；取消使活动租约失效，保留Provider历史、未知外部效果和原错误；由持久投影完成界面终态。历史1–5不重新执行/取消。
- PRIVATE受理明确materialRefs必填、最多32、重复拒绝；首次null不允许会话asset；正文须非空。不自动补造用户处理指令。
- 新增ChatPrivateNativeProjectionTest、NativeCancellationFixture及受理/核心/任务取消/计费/投影查询测试源码。仅git diff --check曾通过；这些测试未执行，mock顺序断言不作为真实MySQL锁/回滚/并发证据。
- 安装技能边界已源码核对：冻结PRIVATE发送合同不含技能选择授权；LOCAL_FILES就绪探针覆盖python-docx/openpyxl等原生文件工具。不能自动授予所有安装技能，也不引入第二个执行器。基本文件处理沿既有LOCAL_FILES；显式授权技能沿共用executionBinding。该结论是合同/源码核对，不是模型端或所有Agent能力实测。
- 本次继续Web材料冻结发送、首次本地暂存、终态和旧表单接替；之后修正剩余编译fixture、真实数据库回归，固定干净候选后SSH测试构建。部署前5自然收尾、显式DDL、受控安装和花荣/张清验收仍全部待做。

## 2026-11-17 接续：Web PRIVATE材料发送与原生终态（源码完成本段，整体仍不可发布）

同Owner继续；四仓HEAD仍为前述固定基线，均未为本任务形成可发布候选。下述不是已通过测试或已上线声明。

### 本段修改

- ChatPanel允许PRIVATE首次无conversationId打开既有资料选择器。固定版本在本地暂存，首次不读取/写入会话关联，不提前创建空会话；现有会话保留既有资料关联管理。请求附件单独记录本轮显式选择，不自动把历史全部关联资料作为新请求授权。移除私人请求附件只移除选择；历史关联仍在选择器管理。身份、会话、目标Agent切换清空本地选择，不能串用。
- PrivateDiscussionPanel原来吞掉send-message参数，现逐层透传materialRefs；JuyiHall真实send调用携带该字段。私人标题不再拼接事项名。typed TASK来源分支未替换，真实任务/承办授权检查保持。
- hallPrivateMaterials.js只做准确资料引用快照：固定WORKSPACE版本/已有会话asset revision；去重保序、32项、合法整数边界；不携带显示字段/latest。sendHallMessage在异步协议协商前冻结引用，PRIVATE首次显式null，不传taskId，引用是body字段而非metadata/inputRefs。原request恢复不重新POST或用受理后ID改原body。
- 语音context及CAS包含同一份冻结材料；选择变动后原语音快照不能默认为新授权。文件正文仍非空，附件不自动补造处理指令。
- 原生RESULT_COMMITTED加入流提示及request收尾判断，仍须真实GET、正确身份/请求/代次和全部turn终态，不能仅收到结果事件就放开下一轮。服务端终态投影前继续保留发送锁。
- 复用safeOutgoingMetadata/inputRefsFor冻结原有允许字段；没有把任意UI metadata序列化上传或扩充权限。

### 新增回归源码与已执行诊断

- 新增juyiting-private-materials.test.js：引用去重/顺序/冻结、版本范围、首次asset拒绝、32项、语音CAS。
- juyiting-unified-discussion-materials.test.js新增首次PRIVATE上传后仅本地暂存、显式发送、目标切换清除及历史关联不自动发送断言；更新私人移除附件不撤销历史关联的断言。
- juyiting-hall-conversation.test.js新增协商等待期间冻结原null/固定版本及非法选择不POST、不丢正文；juyiting-codex-fast-deliberation.test.js新增原生结果已提交但EXECUTE turn未投影终态时保持锁，终态后释放一次。
- **上述测试未运行。** 本机仅Node --check（新增/修改JS）、Vue compiler-sfc语法解析（ChatPanel/PrivateDiscussionPanel/JuyiHall）及git diff --check；诊断日志`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/web-private-send-syntax.log`。没有正式单测/构建产物、实际浏览器或数据库验证。SFC解析不等于样式/交互/网络合同通过。

### 尚待完成，不能据此收尾

1. PersonalWorkspace旧私人执行/输出MIME/撤销表单、TaskMaterialLinks旧正式表单、usePersonalWorkspaceExecution/useFormalTaskExecution/useHallDrafts capabilities消费者仍存在。不能部署到已删除这些写接口的API；下一步按原NF-WEB.5改为本地open-deliberation预填并接父级，保留历史只读及正式返工原业务API。
2. 本地预填资料必须纳入现有草稿冲突确认与身份epoch；当前本段组件暂存不是已完成的跨页草稿交接机制。现有会话资料管理与显式本次选择的真实操作回归尚未跑。
3. 修完Java旧接口编译fixture、显式DDL准备和Owner output寻址，真实MySQL首发并发/回滚、投影/取消/显式保存/ACL回归。当前新增测试不能作为已有PASS。
4. 固定干净三端候选后，按现有SSH worker入口必要测试/构建/回传；5自然收尾、显式迁移及统一受控安装，花荣/张清PRIVATE/TASK与原件预览/保存验收。N01–N14仍待验收，无部署、无生产变更。

## 2026-11-17 接续：旧执行表单退役与本地资料交接（源码WIP，未发布）

本节补记前轮尚未落盘的源码变更及本轮继续收口；不重标上文历史结果。四仓仍未为本任务形成干净发布候选，尚无正式应用测试、构建、DDL执行或生产部署。

### 已落盘的接替

- TaskMaterialLinks保留真实资料关联管理，旧PDF执行/撤销/恢复表单改为带入本事项议事；事件只含准确TASK/taskId/targetAgentId/instruction/固定inputs。BountyPanel透传准确detailTask；删除useFormalTaskExecution和useFormalTaskExecutionScope及JuyiHall旧上下文接线。
- PersonalWorkspace旧私人执行表单改为Agent、指令、固定版本与“在密议中处理”；嵌入资料详情同样可本地带入。usePersonalWorkspaceExecution只导出历史只读hook，保留所属Agent读取、历史列表与准确记录GET、身份/序号/abort；无创建、撤销、能力探测、恢复或旧MIME白名单。
- ChatPanel及两类DiscussionPanel提供本地materialDraft/prepare/apply；JuyiHall接收所有相关入口的open-deliberation，核身份epoch/目标、读取已有TASK会话、固定关联、草稿冲突确认及应用前CAS。没有自动创建会话、发送、执行或关联写入；取消不清源表单。
- HallDraftEditor移除私人输出MIME选择、能力读取和PRIVATE_CASE新修改执行入口，私人动作只预填，历史结果保留只读。清掉不可达revisionSource及私人授权确认模板；正式创建确认保持TASK_CREATE限定。useHallDrafts只允许TASK_CREATE新submit，CREATE/REVISION/TASK_ACTION仅保留对应编辑/历史读取，不通过通用草稿submit执行。正式delivery/outcome/decision返工仍走原业务入口。
- 原型规格在产品修改前补充本地预填、冲突取消、读取完成及busy行为；真实浏览器原型对照仍未完成。

### 本轮进一步发现并修正

1. PRIVATE本地带入原先只nextTick，可能与在途历史会话恢复竞争。现在先等待既有loadHallMessages读取（复用同scope在途promise），再准备/应用材料，避免恢复conversationId后清掉刚带入的引用；没有新建会话HTTP操作。完整父级生命周期回归仍待执行。
2. canApplyMaterialDraft补入实际上传busy、关联写入busy、待确认材料、流式/等待回话/语音锁，prepare与apply都使用同一条件；关联版本移除后不能应用旧prepare结果。
3. 本地事件只提取fileId/version，不再让来源对象覆盖kind。
4. 旧草稿组件与adapter测试迁移为私人本地交接、历史只读负例及TASK_CREATE的幂等/unknown恢复保障；不再让测试要求调用已删除的capabilities/私人submit。新增ChatPanel准确TASK版本、准备后移除、PRIVATE无关联写入及busy/身份切换行为测试源码。

### 已执行检查及边界

- 本轮git -C web diff --check通过；修改的JS/tests通过Node --check。
- ChatPanel、HallDraftEditor、JuyiHall通过Vue compiler-sfc解析及compileScript inlineTemplate静态语法检查。
- **上述不是测试运行。** 没有运行Mocha、Java/MySQL、Runtime、生产bundle或实际浏览器；测试源码新增不记为PASS。此前web-private-send-source-receipt不覆盖本轮修改。

### 后续准确工作

1. 继续核父级实际prefill生命周期与材料草稿跨会话保存（当前子组件scope切换清空附件，不能宣称完整恢复）；funded task的原assignedTarget/roster差异只读核清，不用新分支绕过既有正式授权。
2. API仍有PersonalWorkspaceExecutionServiceImplTest等旧CreateCommand调用，必须按现行能力改成新原生/历史只读及退役负例，不能保留不存在方法而进入构建；其它Owner寻址/DDL/MySQL fixtures继续收口。Web动态组件替身和其它旧入口期望仍须逐真实消费者检查。
3. 准备固定三端干净候选，现有SSH worker工具plan-only及必要测试/构建/回传，保留600秒单次预算。5在途自然收尾后显式DDL和受控统一安装，花荣/张清PRIVATE/TASK、原件预览、显式保存真实验收。N01–N14仍未通过；无生产变更。

## 2026-11-17 接续：API退役测试消费者与历史只读收口（仍未编译/发布）

上一轮属于有效进展（产品/测试源码和handoff已改）；本轮继续同一Owner，没有阻塞等待，也没有扩大授权。

- PersonalWorkspaceExecutionServiceImplTest保留历史目录分页、精确Owner/client/tenant、幂等key只读与输入归属测试；旧CreateCommand/无围栏队列/start/格式门禁/自动个人资料提交等正例删除，补旧1–5/未知协议可读但不得claim与旧写方法不存在负例。现行执行正例归SkillExecutionServiceTest及新PRIVATE/取消/投影测试，不把旧正例改版本号冒充新版覆盖。
- HallRequestDraftSubmissionServiceTest保留历史已提交私人记录GET、旧草稿submit拒绝、TASK_CREATE预留key冲突/数据库完整性失败、历史固定成果及ACL；旧私人创建/旧TASK_ACTION直接执行正例移除。
- HallRequestDraftSubmissionMySqlTest改由真实事务内的HallTaskCreationService测试适配器写fixture_task，保留同key/同draft并发CAS及失败回滚；明确这是草稿SQL/事务测试，不冒充真实任务服务整合。旧私人revision改成并发拒绝、零新case/执行、历史固定版本不变负例。数据库尚未运行；环境变量控制仍保留。
- HallRequestDraftServiceImpl历史case/result的allowedActions现在仅VIEW，不再向新客户端宣告CREATE_REVISION；移除submit内不可达私人完整字段检查。草稿CRUD与历史事实读取没有被删；正式TASK_CREATE与原正式返工路径不变。Controller测试同步只读动作。
- 已删除旧AgentTaskReworkExecutionService的专属测试及其Gradle源包含项，不恢复已经退役的实现。正式验收/返工的现行delivery/outcome/decision/原生执行回归仍必须验证，不能用删除旧测试等同已覆盖。
- ConversationLeaseWireHttpTest把旧task upload/commit正例改成实际404且零服务调用；现行execution-addressed multipart流式测试保留。ControlledImageConversationStartTest改为旧入口不存在。PersonalWorkspaceConversationExecutionTest去掉不存在的ConversationCreate/start/stageOutput/fail/queue调用，保留历史文件只读并改executionId寻址及会话锁fixture；退役协议集合含5、不再误把6作为旧版。
- 源码审阅另发现Jackson2 readValue的checked exception没有接住：skillMap、持久bindings与结果data解析已分别映射为原TASK_CONFLICT/BAD_REQUEST，避免编译错误；未改变信封/签名/摘要内容。

**证据边界：** 仅git diff --check通过和源码调用扫描；没有Gradle、Java/MySQL实际执行、构建或生产操作。编辑记录在`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/retired-execution-test-consumers.py`及`hall-mysql-native-retirement.py`，不是验证runner/通过回执。已知具体剩余编译消费者：PersonalWorkspaceNativeOutputFenceTest、PersonalWorkspaceNativeTaskPublicationFenceTest仍调用已删stageOutput/commitOutputs；需把仍必要的存储I/O外置、持久身份fence、结果提交完整性语义迁入当前6 fixture，再移除旧自动发布正例。CommitItem/CommitView及NativeOutputWire旧commit投影随最后消费者一起删除；不能只修编译而丢现行安全回归。

下一步优先完成上述明确消费者和实际编译候选，随后在指定SSH worker运行原构建入口取真实失败/成功证据；三端整体验收与部署仍未完成。不得将本轮源码检索零CreateCommand引用宣称为全量编译通过。

## 2026-11-17 接续：首个API固定编译候选及存储围栏测试迁移

- API在原工作区切到本任务分支`codex/native-protocol-single-track-20261117`并固定候选`10777c5caf041a7d06e680ecccfa7da7104dbd8e`，tree `03022394b20a1cf44a1dbe84b927fc81cedc5f6a`。这是待验证候选，不是合入develop/发布。未推送；根、Web、Runtime的其他修改保持原状。
- 剩余旧stageOutput/commitOutputs正例迁到现行SkillExecutionServiceTest：真实认证服务事务代理、持久身份代次变化、存储I/O与根锁/认证事务分离、插入顺序、已暂存回执重试仍验身份、不同内容/存储元组冲突、结果验证期间身份/租约/存储元组变化不得提交。mock DAO/事务管理器不是实际MySQL锁证明。
- 新增明确负例：原生文件结果提交/丢ACK恢复不得自动调用个人资料写服务、事项成果发布或正式交付。删除3份已退役旧执行/自动发布fixture，去掉不再使用的StartFixture和CommitItem/CommitView/ConversationResultRecovery及旧commit wire投影；历史协议拒绝由现行套件完整覆盖1–5，未恢复旧方法。
- 编辑记录：`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/native-output-tests6.py`和`native-output-tests6-followup.py`。git diff --check已通过；新增测试尚未运行通过。
- 首次SSH构建批次`native6-api-20261117-01`，指定worker `203.32.84.239`。复用RemoteBuild传输和local_build.py原builder，远端干净controller/API快照、真实Owner台账，plan-only已生成。加入agent SkillExecutionServiceTest及chat ChatPrivateNative*测试，保留默认必要测试/validateLayering/fresh JAR；不装生产。输入、plan、控制日志在`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-01/`。本节写入时构建运行中，终态需后续回填，不据此声称编译或测试通过。

### 首轮真实失败及归因（不是测试通过）

`native6-api-20261117-01`为FAIL：远端builder执行59.642秒，包含失败证据回传的本次阶段105.037秒，193项Gradle任务（129执行/64缓存）；这不是193项测试。compileJava发现3处Jackson2 checked catch用于实际Jackson3 mapper，validateLayering发现chat能力适配器直接引用agent认证实现违反G1。未生成可发布制品、未运行新增业务测试、未部署。

已修复为Jackson3异常；身份查询/精确scope/前后proof一致性由agent执行责任层负责，现有NativeSkillScriptSessionLookup接口携带可信SessionFence，chat只核实时会话能力/声明及前后同一事实。不新增G1豁免、不修改分层规则、不让请求提供fence授权。修复候选`45293cfee8`已提交同一任务分支；02批次使用新固定干净源码执行原builder，01失败日志与回执保持不变。此处写入时02仍运行，后续应按真实结果更新。

### 02/03失败矩阵与下一候选

| 批次 | 精确输入/结果 | 根因 | 已实施整改/下次差异 |
| --- | --- | --- | --- |
| 01 | API10777c5caf；FAIL，59.642秒构建/105.037秒含回传 | Jackson2 catch不适用于Jackson3；chat直接引用agent认证实现违反G1 | 45293cfee8修复异常类型，认证留agent，chat只接可信SessionFence；不增加分层豁免 |
| 02 | API45293cfee8；生产源码compileJava及validateLayering已通过；测试源码编译FAIL，65.323秒/71.490秒含回传 | 本任务owner controller测试仍调用已删create；全量默认test编译还命中无关Economy/Memory共享MySQL fixture缺失 | 192e0f3f41将该tenant断言改为保留的owner GET；复用已有nativeSkillResultRegression lane加入同样native/private选择器及owner/session测试，不恢复旧写方法，不把全量编译失败标PASS |
| 03 | API192e0f3f41；FAIL，0.528秒/2.470秒含回传，无Gradle执行 | 连续两次失败后原编排器要求authorize-remediation，普通transition被拒绝；shell未启set-e导致仍发送候选，worker在原准入处正确拒绝 | 不手改ledger，不绕保护。以本矩阵走原authorize-remediation，再新批04；后续shell使用set -e。03保持原失败且无包/安装 |

02/03真实日志、plan、inputs/result及回传摘要均在`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-{02,03}/`。默认test的既有全量fixture依赖问题不当成本次已修复；准确新增native/private/owner选择器必须实跑，MySQL/其余定向回归仍另行完成，不能凭局部选择器发布。

04保留FAIL：0.542秒构建/2.471秒含回传，仍未进入Gradle。原因是authorize-remediation只转到remediating，本轮遗漏紧接的targeted_verification转换。已经通过原transition完成该步骤（不是手改ledger），05携带准确targeted_verification/Owner/候选192e0f3f41运行。03/04均为工具准入拒绝，不计作应用编译/测试失败或通过。下一轮应先核任务current_gate再启动，不重复这两次操作错误。

05真实运行FAIL（34.562秒构建，37.050秒含回传）：native定向源码编译仅剩新增围栏fixture的AgentTaskEventsGate类限定名缺失；默认安全套件已实际跑23项，21通过/2失败。失败正例仍访问旧任务输入/旧workspace队列，认证过滤器正确403，未进入要验证的输出关闭/身份轮换逻辑。已将正例及其stub/参数迁到准确execution-addressed inputs与commands；旧route拒绝负例原样保留，不把预期400/200简单改成403绕过保护。候选`22ab3f8db7`，06沿原状态转换与远端builder运行；此时06未出结果。所有新业务断言仍须以实际XML结果为准。

06为真实FAIL：33.869秒构建/37.027秒含回传；本批已编译新增定向套件，实际127项测试124PASS/3FAIL（23项安全全过，78项核心77过，6项投影全过，8项Owner全过，1项脚本会话全过，11项PRIVATE受理9过）。核心失败是测试还声称v5任务寻址resume/commit可用；受理两个失败是Mockito重新when已有带写入Answer导致在受测事务之前执行旧Answer，不是已证明生产事务失效。修复为新execution路径准入且旧路径拒绝、doThrow注入故障，保持真实H2回滚/唯一键败者回滚后读取winner断言。MySQL仍未跑，不把H2/mock当MySQL证据。本次与05根因不同，保留失败，通过原authorize-remediation及transition推进新固定候选。

## 2026-11-17 首批有效API构建与定向测试证据（07；仍未发布）

- 候选：API `6fc7e58fca9dbc063e0d6648a305243533eee40c`，tree `b429c5075329b283738059e73af9d12617d5e473`，本任务分支`codex/native-protocol-single-track-20261117`，本地源码干净。未合入develop、未推送；Web/Runtime仍为原WIP。
- SSH worker `203.32.84.239`批次`native6-api-20261117-07`：原local_build.py、原Gradle串行入口、plan-only、fresh输出、默认必要基线+准确native结果测试选择器、validateLayering及fresh JAR/原包均执行。Gradle79.255秒；builder92.397秒；包含原包和证据回传102.410秒，未超过本次600秒。205项Gradle任务不是205项测试；73项缓存任务不当成本批测试。
- 实际XML合计**200 tests / 0 failures / 0 errors / 0 skipped**：runtime安全23；生产邮件2；认证传输4；归档/配置/公开制品65；POI生产类路径2；SkillExecutionServiceTest78；PRIVATE投影6；Owner历史HTTP8；脚本能力会话1；PRIVATE受理11。后两类事务/DAO测试包括H2与mock，不是实际MySQL并发证明。
- API包：`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-07/api/package/api.tar`，251832320 bytes，SHA256 `afeaaaeb2116fa38235ff886b9195f257644dc687ab46f47959625a129db3c42`。原SSH传输校验保留`ssh/transport.json`，原输入/测试XML/日志/bootJar proof均在同批`api/`；汇总`verification-summary.json`。原builder结果`BUILT`，`publishable:false`保持原样，不以局部成功改写成业务验收/上线许可。
- 01/02/05/06失败及03/04准入拒绝均保留；没有覆盖回执、清缓存、绕锁、跳过安全/分层或部署失败包。07不重标之前全量默认test编译缺失共享fixture为PASS。

### 准确下一步（不要重做已通过的同候选切片）

1. 扩展实际受影响的API定向验证：历史文件读取/Owner寻址、草稿TASK_CREATE及退役拒绝、真实MySQL首次受理唯一键/回滚、队列/投影/取消、资料显式保存幂等和原正式delivery/outcome/decision。当前200项不是这些全部覆盖。复用已有对应sourceSet/原builder；不把默认全量test缺失无关共享fixture当作理由删除必要测试。
2. Web继续父级本地prefill生命周期/资料草稿跨会话边界及相关替身测试，固定本任务干净候选并在SSH worker跑准确组件回归/生产构建；Runtime同样固定候选跑原builder。原规格/原型里已承诺的图片/CSV/DOCX/XLSX/HTML原件预览必须实测。
3. 全部三端受影响验证完成后，检查协议5在途执行/投影/计费自然收尾，按明确DDL与恢复要求统一受控安装，再花荣/张清各自PRIVATE/TASK、预览/显式保存验收。**当前无DDL、无生产修改、无真实业务验收，N01–N14仍待验收。**

## 2026-11-17 实际MySQL补充（08失败归因；09待结果）

- 新增ChatPrivateNativeAdmissionMySqlTest：实际Chat/执行MyBatis DAO、事务管理器和生产迁移，覆盖首次发送/丢ACK、并发唯一键败者回滚、末端link失败回滚九张表、请求内容及会话代次变化拒绝重放。外部Agent授权/就绪和零附件解析为mock，不冒充真实Agent业务验收。
- HallRequestDraftSubmissionMySqlTest和TaskExecutionCancellationMySqlTest改用既有SkillManagementMySqlFixture私有进程，不连接配置服务器、不再以环境缺失跳过。Hall相关sourceSet和默认编译补准确共享fixture来源；取消套件尚未进入本批选择器。
- 工具准备独立于构建：从控制机MySQL8.0.21生成去debug符号的测试二进制，仅转移bin/lib/share/LICENSE，没有复制datadir/凭据/服务配置。worker路径`/home/isp/apps/mysql-fixture-8.0.21-native6`，版本和ldd通过。构建专用toolchain.env追加CYF_REVIEW_MYSQLD及普通磁盘短socket目录，原值备份`/home/isp/conf/cyf-build/toolchain.env.before-native6-mysql`；未改生产服务环境。准备证据`/home/isp/state/cyf-preview-sizing-20261116/mysql-fixture-prep/`。
- API候选ff49b4f00f的08批次FAIL，包含回传34.430秒：资源处理阶段把整个MMD资源目录引入造成无关schema catalog重名，尚无MySQL通过证据。通过原fail记录归因，未禁用重复检查，改为只引入contracts/revision-chat-tables.sql。
- 修复候选2bb1eca9ae，09批次沿原RemoteBuild/local_build.py执行，证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-09/`，写入时运行中。本轮无生产DDL、部署或真实业务验收，Web/Runtime仍未固定验证候选。

09终态FAIL，包含回传27.769秒：准确资源重复已解决，新增MySQL测试编译缺少`cn.jia.agent.service.impl.PersonalWorkspaceWriteService`导入；不是生产代码失败或事务测试通过。补准确导入后，按连续失败保护走authorize-remediation再targeted_verification。08/09不同根因均保留，不盲重复相同输入。

10实际MySQL结果：HallRequestDraftSubmissionMySqlTest **13/13通过、零跳过**；PRIVATE新增4项全部失败，首个写入提示execution_protocol_version不存在。来源是新增fixture遗漏既有ControlledImageFollowupV3SchemaInitializer的协议/输入摘要列及skill-v1可空MIME迁移，不通过手写列补丁绕过生产schema。已复用既有initializer、economy-v0-skill-application.sql前置receipt目录及agent-personal-workspace-skill-v1.sql。10批含回传127.286秒，失败回执保留，未生成部署包。

11候选API `63a10f4bb9`沿原builder运行，证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-11/`。本节写入时运行中；后续必须取XML及包证据，不把schema补齐当作测试通过。MySQL测试fixture只启动自己拥有的私有mysqld、临时库，生产数据库未连接/迁移。仍需真实取消/队列/发现/投影/显式保存/正式交付以及Web、Runtime与最终花荣/张清验收。

### 11有效结果及接续边界

- 固定候选API `63a10f4bb95d766066c5d88d62a520407bc05abb` / tree `a452a27c737ff063a6817bc1c3c987bf3f35c5ba`：**217 tests / 0fail / 0error / 0skip**。其中真实私有MySQL8.0.21：Hall13项、PRIVATE首次受理/丢ACK/唯一键并发/九表事务回滚/代次冲突4项；其余200项同本任务基线类型，不把mock和实际MySQL混称。
- validateLayering、fresh JAR与原包通过；builder144.255秒，含制品回传155.251秒。本批api.tar251832320bytes，SHA256 `023904cf9668c07905087c8f251077bbc214d972d2436dfeb449a1626aa7637d`。原result中publishable:false、productionAuthorized:false保持；不是统一部署/真实Agent验收。
- 复查发现真实维护消费者遗漏：SkillExecutionSchemaInitializer仅把协议4/5视为成对执行，schema-maintenance检查会把有效6判为orphan且漏查6缺attachment。已扩为4/5/6（历史只读不恢复执行入口），新增真实MySQL检测器正例/删除attachment负例。此修复在11固定候选之后，**尚未验证**；API当前任务分支HEAD为随后提交，不能用11证明新HEAD通过。
- 下一条动作：固定当前API HEAD并沿原状态转换/worker builder验证检测器；再补真实queue/discovery/cancel/projection/显式保存与正式交付消费者。Web/Runtime WIP尚未固定验证；不发布API单端、不重放历史协议。无需重新传MySQL工具，使用已备份配置；无在途构建（11已收包结束）。

## 2026-11-17 API12扩展覆盖与实际失败归因

12固定候选de044be698；含回传209.717秒，FAIL。新增真实MySQL：PRIVATE5（含维护检测器完整性正负例）、queue5、discovery3、projection3均通过；实际HTTP租约17、原件预览7、正式成果outcome9+H2事务4、formal decision9通过。Task cancellation12中6失败，另历史conversation只读suite11中1个SQL字符串断言失败；不将部分通过当完整成功。

根因：NativeCancellationFixture消费者把snapshot_sha256写成a重复64，生产skillRow按真实canonical snapshot验证正确拒绝；之前的mock没有证明这条真实数据库链成功。修复共享fixture计算真实SHA，并同步TaskExecutionCancellationMySqlTest和AgentTaskBillingMySqlTransactionTest两个真实消费者；不修改生产完整性验证。历史只读suite中SQL字符串仍期待非BINARY的owner/grant比较，现行查询已按byte-exact加强且实际MySQL队列正负例已通过；断言同步准确SQL并明确PRIVATE/TASK与协议6。按原fail/authorize-remediation推进新候选，不盲重试或重标12。

Web源码同时补预填异步生命周期：等待期间离开再回到同面板、新带入、身份/目标/会话变化丢弃旧结果。先更新既有原型规格，再复用JuyiHall本地序号/面板watch；新增实际挂载父组件生命周期测试（仍待worker执行）。未产生Web正式测试/构建结果。

## 2026-11-17 接续：API13通过、Web01失败与API14扩展

- API13固定e732b33ccbf350c5d42f4dda3f6d22f9fa0ecee5/tree6c0e8700beae750950a177ac1fb4ef22ba1d416d：285测试0失败0跳过，分层、fresh JAR、打包通过；含回传229.442秒。包SHA d51b7a9764b9f77237209402dc6edbd5c1b0c8f904c9324d6d24f4f20f98524a。证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-13/`。未安装，不等于N01–N14通过。
- Web01固定3d8748a：828项800通过26失败2pending，含回传63.305秒；未进入生产构建。失败归为页面返回依赖mock缺失、PRIVATE仍期待taskId、旧提交缓存断言、已退役预览内部结构断言，以及预填生命周期mock缺少busy状态。实际发现一个产品问题：新表单挂载时资料initialContext清掉已有selectedAgent；先补原型，再让新表单显式初始目标优先、否则保留选定Agent；不影响存储草稿或跨身份清空。Web02固定e8c733b，沿原worker入口待测，不还原旧转换或阈值。
- API14固定a9d23aac59，新增选定文件保存服务/真实MySQL/Controller/个人资料原件保存套件，含回传34.396秒FAIL：新增编译范围的PersonalWorkspaceServiceImplTest用POI生成真实多sheet公式XLSX，chat测试compileClasspath不继承agent的implementation依赖。仅为该定向测试源集补POI compileOnly（运行仍来自既有agent运行依赖），不增加生产转换。新增MySQL保存测试采用原owned fixture，不读生产DB、无环境缺失跳过。API14失败保留，须经原fail/恢复后新候选执行。

API15 c242190b85：含回传28.552秒FAIL，编译前解析POI默认传递poi-ooxml-lite5.4.0未命中离线缓存；agent现行依赖已明确排除lite、选择full。本轮精确复用相同排除+full组合，不开在线兜底/下载另一套schema，也不改生产依赖。该次与14编译缺依赖根因不同，均留证；16前按连续失败流程authorize-remediation→targeted_verification，不复跑相同输入。

Web02 e8c733b：828项818通过8失败2pending，含回传71.826秒。新表单目标修复、PRIVATE字段、共享预览路由、旧草稿非提交断言均通过。剩余6项父组件生命周期阻塞于conversation mock缺refreshHallProjections；2项语音测试使用自身SFC loader（不是selected-agent-card loader）遗漏useHallPageReturn。补齐原依赖，不修改产品fallback或删除测试；Web03固定新候选待测。

Runtime本任务原dirty文件与既有runtime6-source-receipt逐项比对（仅后补native6共享JSON fixture不在旧receipt），在原6519b79音频能力基线上固定新分支5a3876b，Runtime1.3.117/bridge1.1.79；无覆盖音频任务、无合入/部署。正式worker全基线及新增native6相关测试待执行，既有121项控制机诊断不作为发布证据。

API16 bbdab72bb2：324测试319通过5失败0跳过；含回传237.359秒，FAIL不打包。新个人资料原件保存（真实XLSX多sheet/公式）及Controller通过。4项MySQL失败为手工最小step表漏grant_id/grant_version/assignment_revision，生产SQL为PRIVATE要求这些为空；按实际列补全并新增三项授权字段污染负例。1项保存服务测试的workspace mock只返UploadView，没有实际打开惰性InputStream，因此执行读取器正确从未被调用；改为mock消费源并核真实字节，然后重复保存仍只读/写一次。没有改生产授权或惰性存储边界。API17候选74db09f82c待执行。

## Web03正式worker通过（2026-11-17，未上线）

固定35bc5bb9fcdf6fe5f640ccafebcf3f8f469cd4a6/tree cce4985330c935f79a7734a6001847adc8911614；828项826PASS/0FAIL/2pending。两项pending为既有paired Mini Program冷启动/方向恢复合同，不能当物理小程序验收通过。新增真实挂载父组件6项预填生命周期全通过。worker必要测试/依赖核验/生产构建/包完整性122.615秒，含回传295.160秒；生产JS构建12.51秒，70.961秒用于共享依赖完整性核验，未清缓存。包SHA `9f72d6895d91264f6573257d72de56c446b0fb3fec6186d458a6761b8fc90780`，本机回传后重新核对一致。

证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-web-20261117-03/verification-summary.json`、原tests.log/mochawesome/build.log/result.json/package/web.tgz。控制机另跑output-preview-document.test.mjs/output-preview-pdf.test.mjs均通过，只证明源码连接不证明真实Office解析；日志在`/home/isp/state/cyf-preview-sizing-20261116/implementation-20261117/web03-source-checks/`。无生产安装；API17、Runtime完整验证与真实浏览器/双Agent验收仍待完成。

## API17正式worker通过（2026-11-17，未上线）

固定74db09f82ca6014d1b11c1f72404c4f0337e9e22/tree f31f7f82e678d1234e96c429c4aa2fd5a4fbaf0b；324PASS/0FAIL/0ERROR/0SKIP，含回传262.410秒，分层/fresh JAR/打包通过。新增PRIVATE显式保存的真实MySQL scope/三类grant为空条件/事务与CAS、惰性原始字节读取及幂等重复保存已通过，PersonalWorkspace实际XLSX原件保真及身份隔离通过。包SHA `2993de03085de4f5c818ca1b1b5f438f8eab6f810198381175a87688460113b0`，251832320字节；证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-17/verification-summary.json`及原XML/result/package。此前13只覆盖285，本批替代新增保存范围的候选，不重标14–16失败。

Runtime01固定c7b038e48ed13af201fe337cbaf03f1f4656c0d4，版本117/79；既有34基线文件+15受影响文件，原worker隔离/工具fixture/600秒入口，启动完整构建。精确锁依赖在worker单独准备，未动生产或控制机node_modules。控制机HTML浏览器诊断首试未启动Chrome（旧全局wrapper指向已不存在的cache提取目录）；无浏览器成功结论，不覆盖全局wrapper、不清缓存。按原仓库Chrome133固定SHA工具准备到本任务磁盘目录，后续用显式CHROME_PATH运行。

HTML/Markdown浏览器定向第二次通过：原`rich-document-preview-browser.mjs`，任务局部Chrome133固定archive SHA cec67d7e4baf84814a8602ea59aa07a669f31d95e63e935b5e7b39e5986895a2；1440/390/320六组真实Chromium格式、内联样式、opaque sandbox、无脚本/外网、无整页横向溢出通过。仅生产sanitizer模块，不是全页面文件入口/Office/WPS/手机小程序验收。`web03-source-checks/html-browser-02.json`、`html-browser-source.json`及`browser-runtime-20261117/provenance.json`保存源码/依赖/工具摘要；首试全局Chrome失效日志保留，未改全局launcher。已解开Web03受测包到任务browser-web03-dist用于后续实际bundle验收（不是重建或发布）。

## Runtime01失败归因与02候选（2026-11-17接续）

Runtime01实际1053项：1027PASS/15FAIL/11SKIP，含回传215.066秒；无包、无部署。15个失败计数包含子测试父级失败：退役workspace runner源码断言1项、清理旧测试误删共享lifecycleAdapter导致3项、开源导出没有历史SE2 ZIP导致子项及父项失败、构建输出路径过长导致5项Unix socket EINVAL。原日志/结果保留`/home/isp/state/cyf-local-build/tasks/cyf-native6-runtime-20261117-01/`。

02修正：恢复原生命周期fixture；认证断言改为实际installation-derived内存凭据/禁止profile注入且旧runner不再存在；SE2安装测试用原ZIP fixture从当前受版本管理的SKILL.md/manifest.json生成真实包，以实际版本及SHA校验安装字节，不冒充缺失的历史1.0.0包，历史W08精确归档测试不动。构建输出改既有短路径`/home/isp/state/cyf-build/n6r02`，保持socket产品检查与完整34+15测试选择器。以上只修测试与构建路径，不放宽生产凭据/摘要/隔离；02未出结果前不宣称通过。

Runtime02固定338d42d7e2b487a0d3aa28db71bdf8d720d99318/tree2f5547c4a2701f0cc814c55fa48f38cb824bdf4c，实际1053项1039PASS/3FAIL/11SKIP，含回传214.532秒，仍无包。01生命周期/旧认证断言/全部socket失败已消除；剩余analysis/text-file及父测试失败来自导出源历史不一致：manifest=1.1.0，SKILL.md=1.0.1，安装器正确拒绝。03不改历史包/生产校验：测试ZIP明确生成与manifest一致的SKILL.md版本作为合成fixture，同时新增两个原始不一致源包必须拒绝且不安装的负例；当前普通INSTRUCTION analysis/text-file真实源双Agent绑定测试保留。不将这两个合成ZIP声称历史原包，也不改release-inputs历史摘要。

## Runtime03与实际Office产物验收（2026-11-17，尚未安装）

Runtime03固定3a1776fd3fd83a3b83a8febe87fc5346c0d81970/tree7144c395e5e15822d04acd5fa0fa114f12d65e89，1055项1044PASS/0FAIL/11SKIP，原34+15文件全选，包含回传217.174秒。原工具/隔离检查保留；包`/home/isp/state/cyf-build/n6r03/package/runtime-code-1.3.117.tgz` SHA e91ea0e96c23c6330f45a2561ca606ea34b65006e78df81aef2bc4b6dcd91736。原结果及TAP在n6r03；传输/plan/invocation/attempt在`/home/isp/state/cyf-local-build/tasks/cyf-native6-runtime-20261117-03/`。版本117/79未安装。

Web03实际生产bundle（非重新编译）在任务局部Chrome跑Office：1440/390/320的DOCX文本/粗体/颜色/表格/图片、opaque sandbox、外链altChunk不执行/不发网、无整页溢出；XLSX合并单元格/行高/列宽/底色/粗体、人民币/百分比/日期/1904日期、公式缓存0/FALSE、未计算公式提示、隐藏sheet排除、320窄屏横向滚动后虚拟单元格可达，以及LibreOffice作者样本、损坏Word错误提示。12组通过、无JS异常/外网请求。证据`implementation-20261117/office-bundle-browser03/result.json`、截图及实际加载chunk/fixture SHA；01为10组基本通过，02错误地要求320px离屏虚拟格已挂载而失败，03按真实滚动交互验证，不改产品虚拟化。此为独立挂载实际组件，不冒充完整入口/授权保存/物理小程序/WPS作者文件验收。

04:37—04:40生产只读预检查：线上API bb4f89b、Web5a1a108、Runtime6519b79(116/78)。协议5全部150行为终态（133 RESULT_COMMITTED/17 FAILED），unfinished=0，原投影pending查询零行；协议4有4条QUEUED历史，按冻结合同不转换/重放。安装配置所列host/三自主管理state/托管managedRoot共发现8条原生5本地command，按线上receipt语义只读检查均无待执行/模型用量/provider用量；未调用store构造/写入/flush/模型。必须安装锁内重新检查，当前快照不是永久drain证明。DB新列尚不存在/任务列仍NOT NULL，无DDL。首次把ENC属性直接当登录凭据失败已保留，随后复用既有内存Jasypt只读helper成功，不持久化明文密码。证据`deploy-preflight-20261117/`。

Runtime原安装准备脚本按固定117包/当前116前代复用，`deploy-native6-20261117/prepare-local-runtime.py`仅stage/校验，不停服务/迁移身份；最终stage结果另取，不以日志开始当通过。

补充实际依赖覆盖：API17已测执行取消，但共享NativeCancellationFixture的真实资金事务消费者AgentTaskBillingMySqlTransactionTest尚未执行。本轮将其接到原owned MySQL fixture（取消环境缺失整类skip），在既有taskQuoteRegression/managedHosting编译入口精确补共享fixture来源，不新建runner、不改生产资金逻辑；准备追加原taskQuoteRegression精确选择器，单独API18候选必须重建验证，不用17的324项冒充新增资金覆盖。

Runtime117安装准备终态：STAGED_NOT_INSTALLED，47.065秒；候选manifest SHA becfd82a8138b44fb7f2eb03a8c660f84e6fa3b0e66258c0aece8cecb576e88b，前代record SHA 0cb242738b8afdb0546204611646e457a0623ab3506a40f22f321cc6603d40c1，原依赖图仅版本变化/原validate通过、生产字节未改。stage路径`deploy-native6-20261117/stage/`，包含portable/candidate/前代配置快照/校验日志；未运行install-runtime、未停服务。
API18固定50a7e03c02a869e49bb506bc6ad309229db17ce0/tree5156ef439a65daa2c0ecc9b8bbdcacf7560ae882，沿原worker候选及API17所有选择器，追加taskQuoteRegression精确Billing类（browser可选入口按原任务排除）；写入时构建中，证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-18/`。

发布准备补充：低磁盘未清缓存/历史包/他人目录。仅对本任务API11/13/17与Web03的4个重复传输外壳`*-output.tar`逐个核验transport原SHA/大小和每一成员与已解包文件的内容完全一致，先写证据再删除重复外壳，释放878305280字节；真实包、测试XML、日志、回执、transport.json保留。`deploy-preflight-20261117/duplicate-transport-cleanup.json`列精确路径/摘要，磁盘约2.9GB可用。旧备份/生产状态/依赖缓存未删。

04:45远端develop只读查询：Web a28b0c1b65143b74963df3f91c0446d47726ccc2，API377132f786c6a38b1cb9d2cb90bda7dc3a96ff0b，Runtime4fd0951fec5d5a89c05985b96465169ff7e39e39；均落后当前本地候选/已部署部分前代，不把远端HEAD自动加入本次发布，未合入/push。Web本地develop d52f808、API bb4f89b、Runtime6519b79；三端本任务候选仍独立codex分支。

API18在途日志已发现Billing原fixture遗漏生产既有TaskDeliberationRuntimeLookup：所有需要点将的正例被默认false正确拒绝（不是生产取消/资金事务失败）。已准备下一源码修正：沿原fixture外部identity/material观察mock范围，明确提供正确executor scope的ready=true观察，另加实际MySQL“未就绪零点将/零冻结资金”负例；不改生产准入。当前此单个测试文件修改未提交，须等18完整终态/XML归因再固定19，不能复用18失败包或声称所有测试通过。

API18终态FAIL：330tests/302PASS/28FAIL/0ERROR/0SKIP，含回传499.236秒；未达300秒目标、未超过600秒。全部28失败均为上述漏注入就绪观察造成的直接拒绝或异常类型/HTTP结果不符；不宣称资金事务执行通过。因Gradle失败止步，原默认AgentRuntimeSecurityIntegrationTest的23项未运行（不是删选择器；17已有其原候选通过）。原生/保存等已运行的原组仍通过。下一API19保留18完整选择器，不为时限删测；固定d8b7a65fc6，实际资金消费者包含明确就绪观察和新增零资金负例。原orchestrator记录fail触发blocked_root_cause，按已有authorize-remediation再transition，未手改ledger。

API19已沿原RemoteBuild/local_build启动（d8b7a65fc6，完整选择器不减），证据`/home/isp/state/cyf-local-build/tasks/cyf-native6-api-20261117-19/`。受控安装准备边界写入`deploy-native6-20261117/RECOVERY.md`，尚未写/执行协调切换脚本；不能直接运行旧audio116安装脚本（它包含已存在dropin的新建逻辑）。现有API LOCAL descriptor已支持`rollback_policy=forward-only`且安装器以descriptor为准，不能仅传临时环境变量。必须锁内停写后重查drain，不能以04:40快照直接DDL。仍无生产变更。

浏览器额外安全覆盖：在真实Web03产物中新增task-local OOXML fixture，image relationship明确TargetMode=External且指向preview-security.invalid；实际Docx组件预览结束，无JS异常、无外网请求，证据`implementation-20261117/office-external-image/{result.json,check.mjs,external-image.docx}`。首次fixture生成误用系统Python3.6导致xml_declaration参数错误，留下不完整临时文件（office-bundle-browser03/external-image.docx），未作为测试输入；随后用既定Python3.11生成新目录完整fixture。该补充不冒充WPS作者样本。

后续真实业务验收身份准备：应使用既有`/home/isp/state/cyf-audio-skill-20261116/owner-session-private.json`的chcbz会话（不把token写入证据/argv）。只读花荣/张清profile-capabilities两个请求均HTTP200，`deploy-preflight-20261117/chcbz-owner-session-readback.json`。最初沿旧meeting诊断helper的session属于其它Owner，两请求均防枚举404，已保留原readback；不能用它创建chcbz业务，未刷新/伪造Token、未写数据或调用Agent。安装后必须重新验证真实Owner和当前会话权限。

## API19终态与候选集成（2026-11-17接续）

API19固定d8b7a65fc668f69f91f07dec287a2bebe7acc3b0/tree9fd19b8739ef1a0c0a8156d4d4415c396fbaf31d，原XML28个suite实际354PASS/0FAIL/0ERROR/0SKIP；新增Billing30项含真实资金事务及未就绪零冻结。必要测试/分层/fresh JAR/包与回传531.006秒，超过300秒性能目标但未超过600秒。包SHA2a3c297dc459f67a380287afb37386b6933189e3d034f6ea47f42283c9f3bb23，JAR SHA c1d804b90413581ab81eea504be35e573959d455b75fc041937fa1825a8cc125；原verification-summary.json保存完整selector/fixture/XML结果。没有以17/18证明19或删除失败历史。

Web35bc5bb、Runtime3a1776f已将精确受测候选fast-forward合入本地develop并推送GitHub；API19已fast-forward本地develop，push终态另记。未拉入任意新远端HEAD。当前仍无生产DDL/停服/安装/实际模型调用；开始复用原安装器准备本次协调切换（API coordinator→release/lifecycle，Runtime原锁及原备份/写者退休，锁内drain后仅3条DDL、forward-only，不改全局工具/配置）。

## 三端已受控安装，开始真实业务验收（2026-11-17 05:30）

原安装事务与本任务有限协调脚本位于`/home/isp/state/cyf-preview-sizing-20261116/deploy-native6-20261117/`。首次仅在制品父目录0755被原隐私校验拒绝，生产未变；精确任务包摘要不变，仅将API19/Web03包目录改0700，失败回执以attempt01保留。第二次通过原API payload preflight，原coordinator锁内持API release FD8→原lifecycle stop，Runtime原锁/CAS/旧writer精确退休和原state scope备份。停写后原生5unfinished=0、projection=0、8个旧command无pending execution/native/provider usage。数据库完整schema和三表数据备份在`/home/isp/baks/cyf-native6-20261117/`；三条固定DDL逐条APPLIED，结构复查与历史行数一致，无任务转换/重放。Runtime状态备份SHA02c3b1f6a80d09b682831ac2e93428206af19207fe17598b071c68674827db53；原程序/记录/配置保留在`/home/isp/baks/cyf-agent-runtime-v1/20261117-native6/`。

原API LOCAL forward-only安装成功，PID1508907，HEALTH=UP/ARTIFACT_ATTESTATION=MATCH。Runtime117固定app安装、配置/身份未迁移，PID1511154；启动测量期间初次观察尚未全部ready（未误报通过），05:28精确portable字节/依赖/当前PID五主体ready/connected/registered验证通过，原记录锁内更新verified-active。Web原安装器45文件变更、621完整文件、264线上资源验证通过。三端完整源码/包摘要沿前节；coordinated-result=INSTALLED_HEALTHY_BUSINESS_ACCEPTANCE_PENDING，安装635.602秒不是构建超600；不受构建时限限制。

部署前chcbz有效JWT在API重启后401：ResourceServerConfig.jwkSource每次启动新建RSA/keyID，原bb4f89b到本候选此文件无改动。没有伪造/重签JWT或绕过认证；使用用户已配置JYT_TEST_USER=chcbz及私有凭据，通过既有浏览器OAuth PKCE+真实登录页成功重新授权，新的task-local私有session已保存，两个Owner Agent GET200。此为既有认证行为，不扩展本次修复成密钥架构重构。张清=agt_0130b9efcc3a42eba3394851e7fa2d2d；花荣=agt_44f93f9a92c5483582a20c7c88f67f5c。

真实N01两Agent已开始：首请求误用Accept:application/json收到406（无受理，原GET404）；保留同body/key仅改SSE Accept后发送，当前等待真实结果，未记PASS。证据`live-acceptance-20261117/`。浏览器真实页面Owner身份恢复，后续完整预览/显式保存/正式TASK仍需验收。

API GitHub push两次Empty reply；只读归因HTTP1.1请求90秒无回应，HTTP2初始200但upload-pack帧错误，非源码/冲突。不继续盲重试。API本地develop精确受测已合，远端仍未证实更新；Web/Runtime已推送。此残项与线上安装状态分开。

## N01真实失败与统一完成合同修正（2026-11-17接续）

花荣/张清N01实际均FAILED，不能记通过。两次模型生成正确文本但没有调用result_propose；PRIVATE outputs.dataSchema要求answer结构，原finalize按合同拒绝无提案完成，engine-failure=NATIVE_EXECUTION_TURN_FAILED。证据保留live-acceptance-20261117/private-{hr,zq}-status01.json及原执行store，不重放/改写失败。根因是通用工具/开发者提示偏向文件交付，没有明确纯文本同样需要提交结构化结果。

Runtime修正仅统一成功turn的result_propose要求、零文件artifactRefs=[]及dataSchema约束，保留缺提案失败、原校验/幂等，不增加PRIVATE/Agent特判或从散文猜结构。补无文件结构化结果及缺提案/null负例、重复工具调用测试。候选663a49a（118/80）已提交，待Runtime04原worker完整34+15选择器及真实模型验证；尚未安装。API/Web无需重建，DDL不得重放，后续仅Runtime前向修复。原117已安装事实不变，全部业务验收仍未完成。

Runtime04实际1056项1044PASS/1FAIL/11SKIP，含回传219.708秒，未出包、未安装。新结构化零文件测试fixture漏真实合同要求的$schema声明，validateSkillData正确拒绝；已按API实际2020-12声明补齐，产品验证不放宽。118安装准备在读取FAIL回执时立即拒绝，未触碰生产，原失败保留；下一05同完整选择器重新验证。

Runtime05固定c184e26bc88aab6e21bb62322117a1a9152c6a41/tree3822c091c91ad35d0b521e0f9ef178f36c85fdb0，118/80；沿原worker34+15选择器，不复用04失败结果。安装准备目录deploy-native6-runtime118-20261117；必须绑定117前代，Runtime单独前向修复，不重启API/不重放DDL。磁盘仅删除本任务API19已完整解包且所有成员字节/传输SHA一致的252887040字节重复传输外壳，真实包/缓存/备份保留，证据deploy-preflight-20261117/duplicate-api19-transport-cleanup.json。

Runtime05终态PACKAGED_NOT_INSTALLED：1056项1045PASS/0FAIL/11SKIP，原34+15选择器全保留；含回传216.643秒。包SHA53c976cffc8ef4a625d67c46d4ed3abb949261ff551562a26fbca876131f448f。实际生产仍117；开始仅118 staging，真实PRIVATE复测尚未执行。

05:52 GitHub传输恢复：Runtime118精确c184e26已fast-forward develop并push成功；同一主机GitHub Runtime push已成功的新观察后再次执行API精确候选push，377132f786→d8b7a65fc6成功。未force、未引入新远端HEAD、未修改全局Git配置，原网络失败保留。

Runtime118已完成原锁/CAS受控安装，PID1530115，source c184e26，程序/依赖validate通过，593.965秒（安装/备份/验证时间，不计构建600秒）。状态备份SHA9bc7d6c19769d084975bd4d5ed748859b94bbf87bf45978a5cdc450d2913409d，旧117程序/记录/配置保留20261117-native6-runtime118。API/Web未重启、DDL未重放、配置/身份未改。初次当前PID健康检查遇启动期旧health文件而拒绝，失败日志保留verify-attempt01.log，不能算通道通过；待当前PID5通道就绪后才发新测试请求。

06:08 Runtime118精确程序/依赖/保留配置和当前PID1530115全部5主体ready+connected+registered验证通过，原锁内record更新verified-active，证据deploy-native6-runtime118-20261117/verification-summary.json。花荣/张清新N01请求使用明确新ID n6-private-{hr,zq}-20261117-02开始，不重放原失败01。真实业务结果另记。

## 真实PRIVATE与文件入口验收接续（2026-11-17 06:12）

118后两Agent新N01均RESULT_COMMITTED/FINAL_PERSISTED，单个EXECUTE、taskId/assignmentRevision为空、消息含准确NATIVE6_HR_OK/NATIVE6_ZQ_OK；N01-api-text02-summary.json。花荣已提交请求同key并发两次重放保持原conversation/turn/execution完全一致，异体409，N03-committed-replay-summary.json；仅此子场景，不冒充全部N03。

花荣通过真实UI在原密议1760458009632发新文件需求（request d7babd9b-5432-4776-b99e-a54462ad5447，不重放原失败文字turn）；张清新密议1760458009636/request n6-private-files-zq-20261117-02。两者均RESULT_COMMITTED，真实DOCX/XLSX/HTML已投影。花荣Excel真实模态预览显示合并标题/百分比，原文件formatCode=¥#,##0.00触发现有SSF不支持，UI明确原值降级提示；保留hr-ui-xlsx-before-save.bin及receipt，暂不算该货币格式保真通过，不擅自为单字符编写格式解析补丁。

实际UI发现NF-WEB§文件保存按钮遗漏：HallMessageParts仍保留历史仅text的显示条件，HallMessageMedia已只负责预览；共享useHallConversationArchive早已支持text/image/audio/file，后端保存能力不缺。按既有原型specs/prototype-spec.md§文件就绪和NF-WEB612修正责任组件的可见类型集合，沿同一保存composable/接口，不增加旁路或业务逻辑。更新真实挂载测试四类就绪资产均显示并调用保存，缺asset/revision、processing/failed不显示；现处Web分支codex/native6-file-save-ui-20261117，待固定候选与原worker全选择器验证后仅发布Web，API/Runtime不重建。此前Web826通过中旧用例错误锁定text-only，不能作为该需求已实现证据。

## 06:40真实UI接续及剩余缺口

Web04 3c0084e已GitHub推送，原worker828项826PASS/2pending/0FAIL，301.573秒含回传。安装首次descriptor0644被原私有文件保护拒绝（未写生产）；仅改本任务descriptor0600、包字节不变后原安装成功，39.693秒，621文件/264线上资源校验通过。证据deploy-native6-web04-20261117/install-attempt{01,02}.log。张清DOCX/XLSX/HTML显式保存及同key幂等、下载原字节一致均PASS，live-acceptance中zq-{xlsx,docx,html}02证据。花荣DOCX真实预览2行4单元格、红色粗体和HTML表格/脚本移除/opaque sandbox均已取证；未将货币格式降级标为保真。

正式事项692花荣真实UI推荐→确认承办自动进入议事→TXT预览→验收完成PASS；实际1文报价/预占/验收动作留证，native execution RESULT_COMMITTED。但页面仍显示“正在核对成果”：真实GET404，ChatSkillResultController的只读SQL遗漏6，仅IN(4,5)。API候选f4e94e607e在原读取边界补6，保留4/5历史只读，不改完成事实/重新执行；加真实MySQL controller查询与跨owner拒绝验证，原workerAPI20验证中，未安装。

重新进入花荣密议635还发现已完成纯文本被事件重放恢复成等待，且历史切换按钮因busy禁用。原生成结果事件含executionId但无turnId；重放受理投影没有steps，前端只以activeRequest.steps认定执行消息，漏触发权威请求读取。修正沿原事件提示→原GET→权威状态链，以持久event.executionId作为读取提示，绝不以正文直接完成、不重发/重放执行、不加新监听/轮询。既有原型恢复交互补明此边界，新Web候选另行worker验证；花荣旧文件UI保存需等待修正后再验收。

磁盘仅删除本任务Web04/API07重复transport tar：逐包原传输SHA/大小和全部已解包文件SHA校验后删除；原包/源码/证据/缓存/生产备份均保留。各批duplicate-transport-cleanup.json留证。

## 2026-11-17 最终候选、线上验证及范围

- API20 `f4e94e607ef8f6bcdd75c39cb8b1b5bab7b41b94` / tree `f74ff825c362fc778ec555e9ae53bdfb1a4c2f5b`：355测试通过、0失败/错误/跳过，541.669秒含回传（未达300秒目标、未超600）；新增真实MySQL结果读取6/历史4、5及跨owner拒绝执行通过。Mock controller用例虽接入编译，但不在此批XML运行集合，不计通过。包SHA `91ada6fc63fa8b576abb605c3157123bad332a66f942be1485eec803657b7dff`，实际JAR `30fff8e174fe9dd9efa2324dd4df933183891b6eeeff0ad90917ea893bc96d3e`。原LOCAL API-only安装PASS，PID1549576，启动246秒，HEALTH=UP/ARTIFACT_ATTESTATION=MATCH；未重放DDL、未改Runtime或身份。GitHub develop已推送。
- Web06 `b47358e631e54c4e830483538d68e9401c90ef16` / tree `99af4603edd3758d3e77dcf1114bf7989b09ed94`：829项827PASS/2pending/0FAIL，267.617秒含回传；原安装81.121秒，621文件/264线上资源通过。Web05原826PASS/1FAIL/2pending保留：新fixture在dispose已取消流后又close，清理重复导致失败；修正fixture不改产品，单用例轻量诊断89ms仅辅助，正式证据仍Web06整组worker回归。Web06 GitHub传输状态另记，不能把已安装当已推送。
- Runtime仍118/80、固定c184e26，1045PASS/11skip/0FAIL；API重启后未重启Runtime，当前PID1530115五主体继续ready/connected/registered，原字节/配置未改。三端统一汇总 `/home/isp/state/cyf-preview-sizing-20261116/final-release-verification-20261117.json`。

### 本轮真实业务

花荣692、张清693均通过UI确认承办自动进入议事、实际TXT原件预览、选择成果显式验收，最终completed；均报价1文，无充值/外部购买。原API结果404已由真实GET200/COMPLETE验证；重入历史议事不再“正在核对成果”。密议纯文字635、固定资料639重新进入均回读权威RESULT_COMMITTED、解除等待，历史切换恢复，不从正文判断完成。

花荣资料回归：`n6-material-hr-20261117-01`从选定个人XLSXv1生成asset，再`-02`从同会话指定asset/revision修改C1；两轮同会话1760458009639、独立新用户意图、无task。第一轮HTTP读取90秒超时，只查原request，最终约130秒提交成功，未换键/重新发送。两份原件ZIP检查C1 V1/V2、B2数值/引号货币格式、B3百分比值、合并均符合；个人原资料SHA不变。真实UI新版XLSX显示¥1,234.50/25%及新标记。未把最初不受支持的未引号货币格式当作保真通过。

花荣原3文件通过真实UI逐个保存，明确显示fileId/v1；下载保存原件字节一致，同key回执一致。张清3文件通过真实API保存后，显式删除仅本任务已完成测试会话1760458009636，原asset404、三份独立个人资料仍可读且SHA不变。未登录原文件/个人资料拒绝、同Owner跨会话asset404。证据 `N02-original-file-checks.json`、`N05-hr-real-ui-save-summary.json`、`N04-N06-live-summary.json` 及原请求/receipt均在live-acceptance-20261117。1440/390/320真实Web保存界面无横向溢出/JS异常，不冒充小程序真机。

仅本任务完成后的重复源码传输和tar外壳按精确SHA/tree/解包字节一致性回收；原包、测试、源码、缓存、配置和生产备份保留。Web01/02/04重复shallow传输仓与01/02源码tar清理分别有同批receipt；API20重复output transport亦已逐文件核对后清理，不删实际API包。

验收边界：没有实体小程序/WPS作者样本，也没有在生产实施N01—N14全套并发撤权、断电/整库恢复/费用故障注入；分层用例与线上子场景分开，不宣称全局119项通过。Excel复杂格式按冻结合同降级提示，不新增解析补丁或服务。本次已实施、安装和验证的范围以acceptance执行表及精确证据为准。

API20超过300秒目标的证据：原gradle.log中nativeSkillResultRegression及taskQuoteRegression为长任务，包含本轮新增真实MySQL/资金/取消等业务选择器；原任务计时可能重叠，不相加作总时间。实际整批541.669秒，未缩减必要测试/清缓存或归咎下载。文档可达性检查PASS（161 current/default可达，0不可达），只是文档检查不是产品回归。

07:18 Web06 GitHub已推送：默认Git v2 push/读取出现Empty reply，HTTP/1.1只读35秒超时，均保留；GitHub首页可达而Git v0只读立即返回原3c0084e，据此仅该次命令使用`-c protocol.version=0`推送，3c0084e→b47358e成功。不修改全局Git、不force、不改变应用协议。三组件精确已测候选均在GitHub develop。
