# 选择资料自动翻页及重复预览入口修正（2026-11-17）

## 范围与基线

- Owner：material_picker_autoload_owner_20261117；任务：WEB-MATERIAL-PICKER-AUTOLOAD-20261117。
- Web：现有工作区 /home/isp/wsps/cyf/web，develop，base commit d3fbbaa9e5174b694a37a3ad8778b1d4e0495296 / tree e76cc709e671d407dc03dde4e5bbe52bb6679f5a；开工组件干净。根仓其他Owner脏修改不动。
- 目标：共用“选择资料”列表接近底部自动加载下一页；仅保留一个文件预览按钮。
- 非目标：不改API/Runtime、目录分页契约、选择/固定版本语义、上传、保存或现场恢复逻辑；本轮用户要求开发，不自动推断新增生产发布授权。
- 责任层：Web列表交互；API游标及usePersonalWorkspace既有请求、合并去重、身份取消/过期响应保护沿用。接口规范 api/docs/interface-standard.md，不改契约。

## 交互与实现计划

先更新唯一原型 web/prototypes/juyiting/prototype.js 及 specs/prototype-spec.md，再修改 HallMaterialPicker.vue。
列表末尾哨兵使用既有IntersectionObserver模式，root为真正滚动的列表容器，预加载范围120px。一次只发一个请求；追加后哨兵仍在视区则继续加载，直到滚动区填满或游标结束。正常无“加载更多”按钮，显示加载状态/已加载全部资料。失败保留列表、选择及原游标，暂停自动请求，仅用户点击“重试”后恢复。不支持Observer时保留手动加载后备。关闭选择器、切换移动预览及卸载时断开观察；旧回调不得再触发。

## 验收与验证

最早定向验证：真实挂载HallMaterialPicker，模拟Observer验证root、连续分页、防并发、失败停止/重试、末页、关闭/卸载及预览切换；只读/可编辑每行一个预览。复用已有议事资料、微信导入、草稿/首页组件回归。正式应用测试在203.32.84.239指定worker执行，不将控制机诊断当作发布证据。当前尚未测试或部署。

## 已完成开发与验证（2026-11-17 10:23 CST）

- Web develop/GitHub固定候选 `ef5903f0a19bc727569d9dcaab9910dc632003a6` / tree `8346d120a67d057ca128c3ad5cce8840f7e66d25`，工作区干净。未改变package版本1.16.150。原型、实现、组件及浏览器脚本同候选提交。
- 正式定向测试位于指定worker203.32.84.239：8个selector，**195 PASS / 0 FAIL / 0 pending**；测试执行7.637秒。覆盖自动游标分页、防并发、失败停止/显式重试、关闭/卸载旧观察回调、移动预览返回、无Observer后备、只读/编辑单预览、原资料选择、首页/草稿、微信导入及工作空间引用。
- worker测试使用现有RemoteBuild SSH/systemd受控执行、普通磁盘全新测试输出。完整源码commit/tree相同，定向稀疏快照；依赖复用原只读持久集合（未清缓存），记录Node二进制/锁摘要及实际输入文件摘要。测试结果不是生产打包或发布证据。
- 真实Chromium 1440×1000 / 390×844：原组件实际滚动、真实IntersectionObserver，每页7项，连续追加2页到21项；无重复、maxActive=1、末页停止、无横向溢出、pageerror为空。工作空间I/O为fixture，不冒充生产服务或微信真机验收。浏览器及其本任务Vite服务均已关闭。
- 控制机最小诊断34 PASS；初次缺tsx启动参数和测试fixture漏ACTIVE导致的失败均保留日志，修正后通过，非正式SSH结果。原型语法及git diff --check通过。
- 本轮不构建生产包、不部署。最初尝试原完整打包入口的源码准备，worker只剩213MB，已停止本任务传输，未进入测试/构建/安装。仅清除本任务中断的92MB传输临时文件，保留其SHA/大小回执及控制机原始包；不清他人目录/缓存/生产/备份。浅克隆完整对象也因空间失败，后采用只读复用原基线Git对象、固定候选增量bundle及一次稀疏源码快照完成定向测试；所有准备失败日志保留，不重标成功。
- 生产仍为先前 `d3fbbaa`；未改API/Runtime、未重启服务、无生产数据写入。正式包需在用户授权发布且worker空间可用后按现有构建/LOCAL安装链执行。
- 汇总证据 `/home/isp/state/cyf-material-picker-autoload-20261117/verification.json`；SSH `remote-test/{source,inputs,result,tests,attempt}.json`、`run.log`；浏览器 `browser/browser.json` 及picker-1440.png/picker-390.png；准备失败build.log/test-worker*.log、interrupted-transfer-cleanup.json。worker新测试输出 `/home/isp/state/cyf-local-build/tasks/cyf-material-picker-autoload-tests-20261117-01`。

## 办事页重复预览的统一源码复核（2026-11-17）

用户补充办事页同症状后，核对Web当前HEAD `62fffa7443b3d33b2729e9dd7a1631bed8546de9` / tree `4c131eeab34f2dcb7f70a62472371cd3c0b65bc7`，组件工作区干净；安装记录 `/home/isp/state/cyf-web-flow/record.json` 仍为 `d3fbbaa9e5174b694a37a3ad8778b1d4e0495296`。这是源码检查及安装记录核对，不新增线上界面验收或部署声明。

- 办事HallOverview、草稿HallDraftEditor、事项详情HallTaskResources均直接使用HallMaterialPicker的已选资料行。生产候选d3该行确有两个相同`previewSelectedMaterial(material)`按钮；ef5903已在共用组件删除重复，62fffa包含此修复，不需逐页补丁。
- ChatPanel的议事/密议输入附件由独立composer-attachment-card渲染，每行只有一个预览和一个移除；其HallMaterialPicker及HallRequirementEditor均为dialog-only，不会再渲染共用已选行。BountyPanel通过HallTaskResources展示资料，编辑按钮为选择资料而非第二个预览。
- 独立文件/成果入口同时核对PersonalWorkspace、HallDraftEditor成果、BountyExecutionOutputs、HallCompletedRecords、HallDeliveryReviewDialog及HallMessageParts→HallMessageMedia。未发现同一文件操作区重复的两个预览按钮；下载、验收、关闭、失败重试及图片自身放大入口不作重复预览误删。HallMaterialThumbnail只显示缩略图/文件图标，无额外预览按钮。
- 已有定向组件用例 `web/tests/juyiting-unified-discussion-materials.test.js` 明确覆盖readOnly=false/true各一枚可用预览及0/1枚移除；其正式通过证据仍仅引用上文原候选195 PASS，本轮未新增测试运行，不宣称全部页面真实界面回归通过。
- 结论：此次办事截图与此前事项详情属于同一个共享组件缺陷；当前修复尚未生产发布，不能归因为浏览器缓存。本轮未再改产品代码、未改API/Runtime、未部署。


## 本轮Web统一发布及线上验收（2026-11-17）

- 用户明确授权“现在部署”；仅Web，固定候选 `62fffa7443b3d33b2729e9dd7a1631bed8546de9` / tree `4c131eeab34f2dcb7f70a62472371cd3c0b65bc7`，包括此前ef5903f单预览/自动分页及密议操作行。不自动跟随其他HEAD。GitHub develop只读核对同候选。
- 指定SSH worker执行原 `local_web_build.py`：**656 PASS / 0 FAIL / 2既有pending**，31个selector；fresh生产包、完整性检查和回传合计 **267.913秒**，未超过600秒。构建本体113.433秒；不以原195/186测试替代本批成功。原LOCAL安装事务 **17.190秒**，621项包内文件、264项线上文件核验，当前记录online_verified。
- 初次655PASS/1FAIL/2pending：稀疏快照遗漏 `tests/fixtures/interface-standard/http-envelope-fixtures.json`，补齐同commit真实fixture后在全新输出02重新执行；原失败/26.072秒记录保留。另一次02准备脚本转义错误未进入应用构建，脚本及日志保留。未修改产品、断言或安装保护。
- 构建准备仅删除本线程d3批次已核验对象字节一致且有独立完整Git副本的web-snapshot重复传输仓库；保留原源码、构建证据、缓存、生产/回退包及其他Owner内容。沿用62固定快照，收窄无关地图截图fixture物化；生产src/public/static及根配置709文件逐一核对Git blob，实际输入890文件SHA记录。没有切换tmpfs或控制机源码构建。
- 真实生产Chromium：办事桌面1440×1000、移动390×844每行一个预览/一个移除，固定V2文本原件预览正确；桌面资料列表真实滚动由50到80项、80唯一ID，无手点加载更多。花荣已有两个XLSX文件卡片三按钮同排，移动/桌面均核对；下载 `NATIVE6_MATERIAL_V2.xlsx` 为5139字节有效XLSX、原V2标记正确；原件表格预览显示V2、¥1,234.50和25%。未点击生产保存，不将可见性验证冒充新增个人资料写入成功。
- API PID1549576前后相同、HEALTH=UP、ARTIFACT_ATTESTATION=MATCH；未改API/Runtime、未发起新Agent执行/正式事项，个人资料保存POST为0，pageerror为空。未验证微信真机，不宣称119项全局回归或全部历史事项通过。
- 证据 `/home/isp/state/cyf-preview-actions-release-20261117/release.json`、`live-acceptance.json`、`download-verification.json`、`install.log`及after-*.png；正式包和构建证据 `/home/isp/state/cyf-local-build/tasks/cyf-preview-actions-web-20261117-02/`。包SHA-256 `0803e2bb3bf9a545affdf100b1bf570d4dd461623c33e582b520e8369ddedd96`；原备份 `/var/lib/cyf-web-flow/backups/61f80dd05fd0fa3939fc8e4251df57522cc42638b76d353a6708693852627fe2`。控制机包已按原入口登记完成保留；worker缓存和历史包不额外清理。

## 列表底部状态视觉收口（2026-11-17，尚未发布）

- Owner：本线程；基线Web `62fffa7443b3d33b2729e9dd7a1631bed8546de9`。用户截图要求底部提示居中并保持项目统一样式，未授权本次新候选部署。
- 先更新唯一原型 `web/prototypes/juyiting/prototype.js` / `interaction-completion.css` 及原型规格，再更新 `HallMaterialPicker.vue`。
- 复用PersonalWorkspace已有列表尾提示的居中、16px留白及辅助色节奏；12px字号、1.5行高，移除段落默认margin，错误重试按钮保留8px间距。加载中、继续滚动、末页及错误共用状态容器，手机/桌面一致；不改分页观察器、接口、文件权限或底部导航。
- 已执行原型JS语法检查及 `git diff --check`，均通过。尚未执行SSH正式测试/构建、真实界面回归或部署，不继承此前62候选的通过证据。

## GitHub develop合入并发布（2026-11-17）

- 用户明确授权“拉取develop最新代码并部署”。GitHub抓取到 `ff663c8`（包含908111f与ff663c8小程序应用视口修复），本线程将底部状态样式提交为194385d后合入；原型规格仅解决追加段落冲突，两项内容均保留。固定发布候选 `cb3be686e2e75539a6f815110451c985d4afff38` / tree `035c1ba4a95711232b18a0a948d7b5dc5f9d6555` 已push GitHub develop。后续ls-remote只读查询挂起后精确停止本线程git进程，不将未返回查询当作另一次最新确认。
- 原SSH worker与原LOCAL builder执行32 selector：674项中672 PASS / 0 FAIL / 2既有pending；构建95.216秒。没有API/Runtime构建、安装或重启，API PID仍1549576。
- 首次完整传输tar因worker空间不足失败，原成功包与失败日志保留；仅删除本次失败的重复transport tar，保留大小/SHA记录，不清缓存、原源码或生产/回退包。复用原SSH固定主机rsync原语，将同一成功包直接传回、证据单独传回，双端SHA/大小重新核对，不重复构建。接收校验最初读取result不存在的artifact.size字段报KeyError，包SHA已一致；改为双端独立读取真实size复验，原异常日志保留。
- 正式包107,948,860字节，SHA256 `1c6748085c0bf8d3761e4f1df96dcbf024c132f8f33bbc78c82cba90184601da`；原LOCAL安装事务16.781秒，265项线上资源摘要验证，online_verified。证据 `/home/isp/state/cyf-develop-web-release-20261117-03/`，构建目录 `/home/isp/state/cyf-local-build/tasks/cyf-develop-web-20261117-03/`。原保留入口完成登记。
- 真实线上Chromium桌面1440×1000、移动390×844与模拟小程序环境均滚动至“已加载全部资料”；居中、16px内距、12px字号、18px行高、项目辅助色、段落零margin，无横向溢出、pageerror=[]。截图mobile.png已人工查看。初两次对话框采样退出后footer等待超时，失败日志保留；增加首次加载后的稳定等待后三视口通过，不据此宣称修复了另一产品缺陷。
- 普通浏览器viewport仍允许原网页缩放；模拟小程序viewport具备minimum-scale=1 / maximum-scale=1 / user-scalable=no。**未执行微信真机验收**，原生浮层是否消失仍须问题真机确认。未新增执行、保存资料、生产数据写入；不宣称全局119项通过。
