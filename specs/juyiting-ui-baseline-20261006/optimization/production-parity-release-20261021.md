# 页面补差与选择资料发布核验（2026-10-21）

## 范围和版本

- Owner：chat-stop-main，单Agent；沿用CHAT-STOP-FIX-20261019。仅处理用户批准的一、二项：实页报告G01/G02/G04/G05/G06/G07/G08/G09/R01及最新选择资料交互。不扩展Metaspace治理、真实麦克风、推荐无候选、付费或Agent执行功能。
- 原型：`web/prototypes/juyiting/`；规格：该目录`specs/prototype-spec.md`。统一接口规范`api/docs/interface-standard.md` v1.2；本次不变更后端契约。
- 旧线上Web1.16.29：`e69507b8de111847cc6ca481f9196eb83eb4e950`。
- 新线上Web **1.16.30**：commit `e908c3a43fe4022f4afb9af0fa3d4fae1ea21c4d`，tree `4dd67bba956812694c24f5009336b54c36f8f06b`，已集成develop。
- Flow **4403172/270**：正式测试、构建、部署全部SUCCESS；3167通过、0失败、2原有pending（不计通过）。同Run制品SHA-256：`9b57dab912f6a537b3a7aad22298d4cdab1bd79029e10a37fcc4b1b5df0a456e`。
- 归档清单366项逐个核对安装文件尺寸/摘要；线上index.html及实际加载的JuyiHall JS/CSS摘要与安装一致。Flow结束后恢复原CI-only配置并readback APPLIED，无develop自动部署。
- API未构建/部署/重启；沿用本次起始基线1.16.20，不把本轮Web证据扩大为API新发布。

## 改动与实际页面复验

生产已登录隔离浏览器，PC1440×1000和移动390×844；不操作用户原型标签页。

| 编号 | 实现与本轮证据 |
|---|---|
| G01 | 仅两份真实上传资料、空正文，开始办事按钮可点；创建491回执COMMITTED，title=资料处理，附件固定版本各v1，进入待点将。Unicode36字标题/完整正文由正式回归覆盖，本轮不额外创建长标题事项。 |
| G02 | 首页填写未提交文字→真实刷新→原文恢复；随后清空测试文字。身份隔离由组件/正式回归覆盖，不在生产切换账号。 |
| G04 | 实页帮助为“描述需求，第1步，共4步”，替代旧十步；四步导航、旋转与视口边界由正式回归覆盖。 |
| G05 | 移动事项列表待点将0条显示筛选无结果文案；审计浏览器离线重查后只显示一条Failed to fetch，不再显示空列表提示；重新联网重查恢复。不是服务端故障。 |
| G06及选材 | 真实上传PC文件、移动文件后累计2份自动选中；已添加禁用、下载按钮0个；上传紧邻已选数量，PC36px/移动40px，移动取消/完成各178×44px平分底行；无常驻演示小字、无横向越界。完成后两份资料进入首页。移动预览/收起预览实际切换且保留选择；PC直接预览。 |
| G07 | 既有吴用事项话头A输入未发文字→新话头空白→填B→历史回A恢复A→另起话头恢复B。两处测试文字清空，不发送、不创建服务端新话头。 |
| G08 | 真实案卷检索“验收”→引入传令→提出需求正式草稿，摘录在需求描述；无公议输入框、不自动提交。 |
| G09 | 本轮上传文件“用于新委托”→正式提出需求，固定附件v1；阅读器引用当前段落→同一正式草稿，含典籍定位及摘录。均不要求先选执行好汉/私人可见范围；不保存/提交测试草稿。 |
| R01 | 吴用既有图片消息只保留预览，不再显示内联下载/保存；放大预览使用SVG关闭图标，独立预览仍有下载文件；文本片段归档能力保留。 |

新选材共用组件接入首页及正式草稿；未知上传原操作重试、退出/身份切换晚回执隔离、多文件串行、已有选择保留，由定向和正式回归覆盖。

### 保护性拦截说明

第一次上传未放行带`/agent`前缀的真实路径，被审计浏览器阻断：界面保留选择并提供“核对原上传”；准确放行后点击原操作重试成功，未另开新上传意图。案卷搜索首次POST也被审计保护阻断，准确放行`/chat/library/search`后真实检索成功。上述不是生产接口故障。阅读器自动进度PUT保持阻断，不修改既有阅读进度，也不据此声称进度写入通过。

## 测试数据及副作用

- 新事项491：仅创建待点将，随后真实UI确认取消，status=cancelled。无指派、执行、Agent调用或扣费。
- 两个新文件`ui-parity-1.16.30-pc.txt`、`ui-parity-1.16.30-mobile.txt`：固定v1，均通过UI核对引用影响后移入回收站；常规列表已不显示。既有引用按原契约保留，不物理删除历史。
- 原有事项/成果只读；未保存新需求草稿，未发送议事消息。仅本隔离浏览器做离线故障注入，随后恢复联网。

## 时间、失败和边界

- 北京时间10:19开始，10:39提交产品实现。10:49约定期限前未完成整体处理；10:48主动报告延期风险。补充测试修正与发布、页面核验使总耗时超过30分钟，不能标记按期完成。
- Flow268固定tree遗漏更新，源码守卫拒绝，未部署；269正式回归8项失败，均为本次已确认交互变化对应旧断言，未部署；修正5个测试文件后247项定向通过，再固定新commit/tree进入270。未跳过测试、未本机打包、未复用其他Run制品。
- 10:54后核验部署/安装，10:55—11:12生产页面复验与测试数据收口。
- 这是本次页面补差验收，不是重新完成全产品验收：真实麦克风/软键盘、全部格式PDF/音频、支付、多Agent、无候选归因、完整新任务指派至验收及Metaspace长期稳定性不在本轮结论内。

## 证据

控制与原始证据目录：`/var/tmp/cyf-ui-parity-fixes-20261021/`。

- `release-r3/{release-input.json,status.json,web-artifact.json,artifact-verification.json,public-assets.json,restore-result.json}`：冻结源码、Flow、制品/安装/公网摘要与配置恢复。
- `final-targeted.log`（165通过）、`onboarding-final.log`（24通过）、`affected-regressions.log`（247通过）：定向诊断，不替代正式Flow。
- `browser-evidence-index.json`：截图摘要和实际写请求；`browser/readonly-network.json`包含保护性拦截。
- `browser/pc-four-step-help.png`、`mobile-upload-two-selected.png`、`mobile-preview-toggle.png`、`pc-upload-autoselected-success.png`、`pc-material-only-created.png`、`mobile-test-task-cancelled.png`、`mobile-filter-empty.png`、`mobile-error-no-false-empty.png`、`pc-file-formal-requirement.png`、`pc-library-formal-requirement.png`、`pc-reader-formal-requirement.png`、`pc-media-icon-close.png`、`mobile-thread-a-restored.png`、`test-files-recycled.png`。
- `pc-upload-autoselected.png`为首次审计保护阻断期间截图，**不是上传成功证据**，以带success的PC截图及移动实际回执为准。
- 原始Flow日志含平台环境信息，仅受限本地保留，不复制凭据/下载签名链接到文档。

## 12:34补充：四项选择资料返修发布（Web1.16.31）

### 对上轮结论的更正

上文G06只验证了自动选中计数、按钮大小和切换行为，没有验证上传项是否即时进入目录，也没有按同断点逐项比对卡片/预览布局和首页独立预览。因此上轮测试通过**不代表选择资料已完整对齐原型**；用户截图指出的四处差异均属实。本节覆盖这四项，不重标其他页面验收。

### 实现与冻结输入

- 单Agent；产品只改`web/src/components/juyiting/HallMaterialPicker.vue`，无API修改/发布。
- 规格先更新`web/prototypes/juyiting/specs/prototype-spec.md`的“四项实页纠偏”；保留既有原型设计，不反向迁就生产。
- Web **1.16.31**，commit `a924498d774402c04b1baa17220a3335d84defb6` / tree `9521c1eee508e4dfcaf1fbeea89974995bd07e28`；已push develop。
- Flow **4403172/272**：测试/构建/扫描/部署SUCCESS；**3171通过，0失败，2原有pending**。同Run制品SHA-256 `660c0c422fd4bf7314ccf451668a0921d42ac08c696679be852b63424d4e54da`；366项安装文件全部匹配，公网index及实际加载JuyiHall JS/CSS与安装摘要一致。恢复原CI-only配置，readback APPLIED。
- Flow271因旧底色断言失败（3169通过/1失败），未部署。修正断言至原型底色并增加几何/独立预览约束后重新固定源码；没有关闭测试或放宽无关检查。

### 生产页面逐项复验（12:23—12:33，北京时间）

| 用户问题 | 修复和实测 |
|---|---|
| 选择器样式 | PC1440×1000：弹窗980×760居中；移动390×844：全屏、卡片箭头/已添加、无横向溢出。上传紧邻已选计数，取消/完成各174×44平分底行，不加常驻说明小字。 |
| 预览效果 | 真实既有图片加载成功，contain完整显示；移动中间预览、底部左收起右添加（64×40），不在图片上方堆操作。PC默认显示预览，无预览开关；选择器无下载。 |
| 上传不刷新 | PC和移动各真实上传一份合成文本；不重开弹窗，新文件立即出现在目录并自动定位/已添加；按fileId无重复，既有选择保留，累计3份。根因是原workspace更新只替换现有行，不插入新行；在picker合并COMMITTED回执并刷新ACTIVE目录，不泛改工作空间。 |
| 办事预览误入选择器 | 完成带入3份后，移动预览既有图片、PC预览新文本，均直接打开独立dialog，选择器数量0；网络只读文件固定v1及预览内容、不重新请求目录。标准×、真实Escape键对关闭、聚焦触发按钮后关闭恢复焦点通过；选择仍3份。独立预览保留下载，文本下载走真实content GET。 |

### 清理和覆盖边界

- 新建且仅回收本次两文件：`pws_d91c66b428f54a68832a99c8798fb45e`（PC）和`pws_cb5b5955db1049ec87446486f36a6183`（移动）；均经实际UI核对引用影响0后确认回收，常规列表测试行0；本隔离浏览器未提交选择已清空。
- 既有图片只读；未创建事项、发送消息、调用Agent、扣费或改动其他人的资料。
- 定向67通过、配色补充32通过，仅作开发诊断；正式依据是272。目录刷新失败保留已确认项、版本缺失不替换、晚回执隔离由回归覆盖，不声称生产注入过全部异常。没有复测全部PDF/音频/真机软键盘。
- 11:54启动，12:09产品代码提交；正式旧断言修正及Flow发布、实页核验至12:33。编码与发布等待分别记录，整体约39分钟，不声称30分钟完成全部验证。

### 证据路径

`/var/tmp/cyf-picker-parity-20261021/`：
- `release-r2/{release-input.json,status.json,web-artifact.json,artifact-verification.json,public-assets.json,restore-result.json}`。
- `browser-evidence-index.json`：截图摘要、明确授权写请求、实页观察与边界。
- `browser/live-pc-picker-1-16-31.png`、`live-pc-upload-refreshed.png`、`live-mobile-picker-list.png`、`live-mobile-image-preview.png`、`live-mobile-upload-refreshed.png`、`live-mobile-standalone-preview.png`、`live-pc-standalone-text.png`、`live-test-files-recycled.png`。
- `component-*.png`仅本地真实组件/fixture诊断，不用作生产证据；实页以`live-*.png`为准。

## 15:12补充：事项详情资料卡与重复验收入口纠偏（Web1.16.32）

### 范围与根因
下方“资料与成果”原实现只是第二个验收跳转按钮，没有按原型读取资料；属实现与原型不一致，不是两个不同验收流程。先修正原型规格中“资料只在原议事查看”的错误文字和数量/只读/异常契约，再修实现。原型已有资料卡布局无需反向改变。

- 待验收只保留上方“查看成果并验收”，保留中性“继续议事”。
- 新增HallTaskResources，复用现有workspace分页读取、ACL与固定版本预览；按有效INPUT/REFERENCE去重展示名称/版本/直接预览，无添加/移除/上传。
- RESULT数量复用同任务、状态、版本的既有权威context，包含文字成果、排除MANIFEST；未知时明确区分OUTPUT引用与正式成果。无额外轮询、无新后端接口。
- 原已完成/只读历史入口保留；加载/失败/重试与空态分开，切换事项/身份隔离晚回执，离开详情返回列表后重读。

### 正式证据
- commit `c61efdf00bec8721fa978c6035d72ef0662cc188`，tree `01739d2054295ec0bb71cf67de7ac045ff25dd86`，版本1.16.32。
- Flow4403172/273失败于旧布局断言，未部署；保留测试语义修正断言后，Flow274：3180通过、0失败、2原有pending；扫描与构建成功，部署单71519565/1台主机Success、healthy。
- 同Run归档SHA256 `b04c5b44cdf134770115a1c3e5ba7b2abed2a278e13467e85ecc59c759c9fa89`；366项安装文件全匹配；实际公网index与JuyiHall JS/CSS匹配。流水线恢复原CI-only配置且readback APPLIED，develop不自动部署。
- 证据根 `/var/tmp/cyf-task-resources-20261021/`；release保留273失败，release-r2保存274源码/测试/同Run制品/安装/公网/部署/配置恢复证据。

### 真实页面核验与边界
- 现有493（待验收、文字成果）：1440/390下验收按钮均1个，下方资料卡空态而非第二按钮，摘要0份资料/1份成果；入口打开原验收弹窗，未提交验收。
- 现有492（待点将、1份图片资料）：名称/v1正确，PC/390点击直接预览而不打开选择器，2000×5812长图contain完整展示，关闭、真实Escape和焦点恢复通过。返回事项列表有数据，重开详情重读资料；320无横向溢出，资料卡仅预览控件。
- 截图：browser/detail-pc-pending-acceptance.png、detail-mobile-pending-acceptance.png、detail-pc-material-card.png、detail-mobile-material-card.png、detail-pc-fixed-preview.png、detail-mobile-fixed-preview.png、detail-narrow-material-card.png、mobile-acceptance-entry-destination.png。
- browser/return-check.json记录真实鼠标/Escape/返回重读；browser-evidence-index.json索引边界；readonly-network.json保留网络审计。无业务写入/新增测试数据/Agent调用/扣费。
- 异常重试/身份隔离/迟到回执由组件回归覆盖，未故障注入生产；移动是桌面浏览器视口模拟，不声称真机验证。最初诊断脚本程序化click无焦点转移、固定3.5秒等待图片未就绪的观察保留；真实输入和就绪等待后通过，不以删证据方式掩盖。

## 15:37补充：首页待验收入口统一（Web1.16.33）

- 根因：HallOverview把review提示传给openOverviewTask，后者据此赋值formalTaskRef，错误转到旧“正式成果与验收”页；事项列表则打开BountyPanel详情。上轮修复未覆盖该入口。
- 修复：正式事项按钮统一“查看进展”（UNKNOWN仍“核对事项”），openOverviewTask保留review提示但不再用于选择页面；统一进入详情，由用户点击唯一验收按钮打开原权威验收弹窗。显式历史成果入口及私人/草稿不变。原型baseline-ui消息卡及prototype-spec先同步。
- commit `f4ccaa94cd37db025078d5afac514ad86674d584` / tree `f8861aebf94be2ee4137a7c6ba87dcf2b7318138`，Flow4403172/275正式3180通过/0失败/2原有pending；部署单71523407主机Success/healthy。
- 同Run制品SHA256 `5c82e55b780276ef645249f2e563b9196aa702521590110143a42a4f544a52e5`，366项安装manifest匹配，公网index及JuyiHall JS/CSS匹配。已恢复原CI-only配置并readback APPLIED。
- `/var/tmp/cyf-overview-entry-20261021/browser/navigation-check.json`：PC1440、移动390，现有493从首页与事项列表进入的详情逐字段一致；旧成果页组件0个、验收主入口1个、资料卡1个，无横向溢出，能打开/返回原验收弹窗。截图home-1440/390、home-detail-1440/390、list-detail-1440/390、review-dialog-1440/390。
- 无新增数据、提交验收、Agent或支付调用；移动为视口模拟非真机。历史查看/私人草稿不变由相关组件回归覆盖，本轮生产实测范围限两条正式待验收入口与返回。定向169通过；业务写请求护栏与网络审计保留。

## 18:31补充：格式无关的已有成果提交（已部署，业务验收中）

- API1.16.21，commit `21c32034b4b60cad497db5640966fdd7635d44b8` / tree `520aae2a32dc22188e74fa159a6cd0d10e02687d`，Flow5260799/214，部署单71542331 Success/healthy。2749执行、2627pass、122skip、0fail/error，MySQL30pass。制品SHA256 `d94b0b968b05917d5d19e6443c55538d057ec7c4a7fdd5f085ae2b0494537186`，安装JAR `464c2328bc863f72e5dde94fa885cd9d922481af2c4579a65bbac9f6647aaa5a`。
- Web1.16.34，commit `19a322a4b3b51856f8c1235a73d3aac4d848b022` / tree `311bc4974f7c0e5a9028178630041282555782bf`，Flow4403172/278，部署单71543252 Success/healthy。3186pass、2pending、0fail；制品SHA256 `56afda6d6897b74cb57aeb1b1dfd65970a60ff270d61c6f4adfd0b527fc6df03`；366个安装文件及公网入口/JuyiHall JS/CSS匹配同Run。两Flow恢复原CI-only且readback APPLIED。
- Runtime1.2.2，commit `5e8742aac6b9261a8d6cc94f77da1175e8ae74e2` / tree `9448db77464f4a01cc07172880f21d332996cc3c`，已push develop，安装`/home/isp/apps/cyf-agent-runtime-v1/releases/1.2.2`；manifest SHA256 `81ab5fc628e4b952c04b3ea202e45cccff811dd3ab9ab4b16657e56fdf97ddbd`。225pass/1skip；协调激活后PID13318，三个静态Agent连接/声明/心跳核验，current/RELEASES/持久记录一致，身份摘要不变。
- Flow214部署前通过固定源码原initializer、共享schema锁完成唯一CHECK扩展，无业务DML/通用迁移开关开启；完整catalog前后校验、数据库备份`/home/isp/baks/cyf-submission-kind-flow-214/`。Runtime一致状态备份`/home/isp/baks/cyf-runtime-submission-1.2.2/`；林冲历史RECOVERY_REQUIRED原样保留，不重放付费动作。
- 实现为v5 SUBMISSION_REQUEST，精确冻结父摘要、保留targets、复用原outbox/finalization/review。说明不作为文字成果，提交不再生成文件；多独立根须显式选择，不按最新默认提交。新增文件格式由生成/预览适配，不改主提交状态机。原事项480未代选择、提交或验收。
- 工具诊断边界：Web同Run归档历史helper未执行，实际versioned helper另有固定SHA及入口校验；两角色核对见`web-release/helper-role-verification.json`，未替换现行主机工具/放宽完整性。公网TLS由系统curl验证（独立Python缺CA信任并非网站故障）。浏览器guard最初误阻挡点将/上传，修正精确许可后复用原幂等意图，不计为产品缺陷。
- 证据根`/var/tmp/cyf-media-delivery-20261021/`，api-release/web-release包含完整源码、Flow、部署、安装与恢复证据；production-browser包含网络与真实页面。独立495最初PDF要求因无能力而CLARIFY，改为上传自制PNG输入并明确取消PDF、一次改色、确认后再提交。初次生成已RESULT_COMMITTED且实页预览为绿色方块；自然“提交已有成果”请求携带精确媒体parent，后续结果仍待验证。PC/移动业务验收未完成，不把本地原型、正式CI或服务健康写成全链路成功。

### 19:01最终补漏与验收结果

- 实际暴露问题：SUBMISSION_REQUEST识别/存储正确，但outbox独立调用final reader开启READ ONLY，媒体授权的既有FOR UPDATE被MySQL1792拒绝。不是模型再次生图，也不是状态按钮隐藏。只将final read/loadAction与混合text resolve改为原REQUIRED读写事务，保留所有锁/身份/幂等；新增3个真实MySQL事务/锁/回滚测试。不是无锁查询或独立事务规避。
- API1.16.22 commit `53a29aca08a804f08a1012294c9130b209b33cbc` / tree `d422286cc427c1f9cac29c212e145e150411d955`，Flow5260799/215 SUCCESS、部署单71546817 Success/healthy；2752执行/2630pass/122skip/0fail/error，MySQL33pass。归档SHA256 `f8a7a1c1c3438aeefd1357f1f6ffe2fcd8ed37b04589b8825eb0983b165f09cc`；JAR `823dbeff089b358c780b79d4b08f151446f0c1d43e22f8cdfc7d301b1a53750d`，PID30921/canonical cwd/healthUP。CI-only已恢复/APPLIED；Web1.16.34和Runtime1.2.2维持已验证版本，Runtime重连/新鲜ACK复核。
- 独立495实链：一次图片编辑完成→自然语言提交已有成果（精确媒体parent）→SUBMISSION_REQUEST→原outbox在修复后自然恢复SENT→正式delivery→待验收→移动模拟视口原UI确认验收→COMMITTED/ACCEPTED、任务COMPLETED/version4。提交过程中没有再次生成；真实请求catalog只有1个EXECUTE，正式仅1个RESULT及系统MANIFEST。
- 输出/正式RESULT SHA256均 `bb55b6f81cf89aefd4fbd74479fee6ae90c46e1d3c87ebe2ffb1b22f2efc3729`，PNG263676字节。PC1440、移动390均打开正式成果并显示绿色方块，详情和首页终态同步；验收后历史只读。实际验收POST只有移动视口一次，不冒充两端独立完整运行。测试最初PDF前提不满足，已通过明确对话更改测试需求，不代表PDF能力已上线。
- 原480只读时实际已有3条独立成果，选择器默认空值，无替用户选择/业务写入；与早期2条诊断是不同时间快照。用户须自行选定目标成果，再在原议事明确提交。
- 未覆盖生产实测：混合文媒、自然媒体修改重交、新格式生成、真机和第二账号权限；相关静态/组件/服务回归不升级为线上证据。非阻塞文案遗留：已完成议事的历史提交卡仍写“请查看并验收”，主状态/只读权限正确；本轮未另发前端修文案。
- 证据：`/var/tmp/cyf-media-delivery-20261021/{release-receipt.json,api-lock-release/,production-browser/business-verification.json,production-browser/task480-readonly-check.json}`。root-cause-stack保留真实失败，未隐藏或重标为一次上线成功；原30分钟期限未满足。

## 2026-10-21 20:25 +08 续核：混合成果、媒体修改重交与图片预览

### 精确发布输入及正式验证
- API1.16.23，commit `510b2937696495b54a9203729784660e62c65082` / tree `2c34d7065d760ca77c046860d9f11b5da8cfe271`；Flow5260799/216、部署71549967 SUCCESS/healthy。2759执行、2637pass/122skip/0fail/error；PersistedRevisionReplay新增7项全部执行通过，MySQL原33项通过。制品SHA256 `0f47499315221443db1b8b7a5ed2949750d7d85366990b32d5261b0fef66125a`，JAR `3269145c2a920accc9b873a7bb2bfe7f0f42290f55201d68ac941236c50a2cfe`。
- Web1.16.35，commit `68552ea79a033e62159f4ee99fae6c724adb243c` / tree `6168a00facd9b0168d5213b09f5167ad0dde0fdb`；Flow4403172/279、部署71551557 Success/healthy。3191pass/2pending/0fail，含新增5项图片策略回归。制品SHA256 `49581da80486bb93719447c2d57942ca96babc4cbcb79a5598bee469791e7397`；366安装文件逐项一致，公网index/JuyiHall JS/CSS摘要一致。开发分支push本身未部署；两流水线已恢复CI-only/readback APPLIED。
- Runtime保持1.2.2/`5e8742aa`，本续核未改动或重启。未新增DDL、清队列、直接业务DML或重放付费生成；外部委托原型及AGENTS未提交修改保持原样，仅选择性提交本轮规格追加。

### 真实根因与有限修复
1. 原496自然修改事件校验失败不是模型返回坏JSON：`ChatActionFinalService.loadRevision`重验时丢弃已持久化原生资料receipt。仅恢复原receipt传入并校验v5封包，不放松身份、目录、摘要、修改依据或事件绑定。216上线后原事件自然恢复SENT。
2. 496修订PNG为1,429,926字节；`outputPreviewKind`先执行1MiB文本阈值，错误挡住合法图片。仅PNG/JPEG先走已有合法长度/64MiB内容契约，保留4096边长/1600万像素、MIME、取消及URL释放校验。原型已有contain图片展示，本轮规格明确边界；不新增下载按钮、不改布局、不改文本/PDF/Office或其他格式。

### 业务验收（独立测试496、吴用）
- 首批同一delivery含图片+文字；PC图片、移动文字预览通过。普通议事明确仅改图片至深绿色、保留文字，原正式图片固定artifact作为技能输入（不是原蓝色参考文件）。
- 修订结果提交后新delivery `finalization_delivery_b6c7a5aaa4a80c361f017cb848da625d6321b23faa5f634df234dc4a19793637`仅2RESULT+原MANIFEST：图片SHA `dfcf18399d4fd4775f5d68c590d05afb0f37dcb7d03ef8a96428663636cab169`；文字以FORMAL_ARTIFACT保留，SHA `dcacc889e0685526534db090085ab85ddc1551ec0189b3e4ef15beb1d67fb37a`与旧批完全一致。旧图不重复带入、旧批CHANGES_REQUESTED。
- Agent曾提示当前候选只有图并请求澄清；原UI回答“只提交已有图、不重新生成/追加文字”后SUBMISSION_REQUEST成功，后台自动保留原文字。说明当前提示尚不够清晰，不声称全程没有多余追问。
- 生产PC1440×1000/移动390×844实际查看修订图（1254×1254像素）与原文；预览修复前失败截图保留。只在移动模拟视口点击一次确认验收：`review_236af9b1754087f1458735312a88e94802ce106419c07e9cc5230f251c00fe4e` COMMITTED/ACCEPTED，任务COMPLETED/version6；整页刷新重入仍完成。不是两端各生成一次，也不是真机测试。
- 数据只读核对该会话正好2次EXECUTE（初始+修订），提交/澄清未增加执行。原480没有选成果、提交或验收；495已完成未重做。

### 未关闭项与后续边界
- **重入执行中会话忙态残留**：服务端请求和执行均RESULT_COMMITTED、页面成果可见，但仍“等待回话”/发送禁用，重取回话未解除，整页刷新恢复。根因尚未证实；下一步用本次固定请求/catalog/GET证据复现前端恢复与active request归属，补定向回归后修复。不新增监听、不自动重发执行、不通过清队列解决。
- Agent对“保留原文字重交”的多余澄清，以及历史提交卡在已完成时保留“查看并验收”旧文案，均未在本次图片修复中处理。
- 因此结论为主链路通过、仍有明确前端恢复/提示遗留，不标整体零缺陷或全部验收完成。原17:19期限未达到，不追改时间记录。

证据根 `/var/tmp/cyf-media-delivery-20261021/`：`revision-receipt-release/`、`image-preview-release/`、`followup-browser/business-verification.json`及截图/网络审计；最新续核回执 `followup-release-receipt.json`，原`release-receipt.json`保留495及当时版本事实，不混作最新版本。

### 2026-10-21 20:58 +08:00 重入终态忙态修复发布收口
- Web1.16.36，commit `9dbd132e8bc25119c0532cbed672ab7fa4a214b3` / tree `adacb21c069236c728ecd494f425210495153ee5`；Flow4403172/281 SUCCESS，部署71553147 Success/healthy。3198pass、2pending、0fail；7项新增恢复回归全部纳入正式套件。前次280的2项bootstrap失败保留，未部署、未削弱测试，修正为共享原调度而非重复GET后再发布。
- 同Run制品SHA256 `ab65817a411ae7adda1676ceffa1eebe84251c46084da9ce4cd65a21ade87600`；366安装文件、TLS公网index及JuyiHallEntry JS/CSS精确一致。Flow配置已恢复原CI-only/readback APPLIED，不将develop push改为自动部署。API1.16.23/Runtime1.2.2未改。
- 生产496仅只读：PC1440×1000、移动模拟390×844，已完成详情→历史成果→议事记录→原重取按钮→返回均可用，API保持completed/version6、1份资料2份成果；没有业务写/付费执行/重复验收，也未操作480/495。移动议事紧凑头部本身不显示完成状态文字，详情/API已核验；不误记为移动头部有该文案。
- 该bug的运行中终态转换由真实composable定向反例及Flow回归覆盖，本轮未重跑新的生产EXECUTE。模型重交前额外澄清、已完成历史文案（含提交卡验收提示、成果页范围提示）继续留项，不扩本次修复。原型沿用projection-recovery场景并已补规格；无新按钮/监听/轮询/业务事件。
- 完整证据 `/var/tmp/cyf-media-delivery-20261021/busy-recovery-release-r2/release-receipt.json`，浏览器证据同根`busy-recovery-browser/verification.json`及截图；稳定恢复规则回写既有runbook与前端详设。外部委托原型/AGENTS脏变更未纳入发布。
