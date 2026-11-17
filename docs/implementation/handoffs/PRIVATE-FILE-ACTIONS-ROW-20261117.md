# 密议文件操作同排与原件下载（2026-11-17）

- Owner：private_file_actions_owner_20261117；任务 WEB-PRIVATE-FILE-ACTIONS-20261117。
- Web现有工作区develop，开工干净，base commit ef5903f0a19bc727569d9dcaab9910dc632003a6 / tree 8346d120a67d057ca128c3ad5cce8840f7e66d25。
- 目标：密议就绪文件卡片“预览 / 保存 / 下载”同一操作行；保存状态/错误仍在下方。事项/公议不新增保存或下载，原验收操作不变。文本片段原保存保持；非就绪文件不新增操作。
- 责任：HallMessageParts决定密议操作可见性，沿用HallMessageMedia.actions插槽；Media负责既有鉴权资产读取和下载取消/错误，复用outputDownload.saveOutputBlob（含小程序原生文件桥）。不新增下载API/依赖/业务开关，不先保存个人资料，不使用模型URL或文件路径；接口规范 api/docs/interface-standard.md 不变。
- 先更新唯一原型及规格，再改产品。测试覆盖同排/原文件名及字节、只发GET、防重复下载、失败重试、身份/资产切换及卸载取消、小程序既有桥、事项无新入口、保存原幂等/状态查询。真实浏览器手机/桌面；正式定向测试在指定SSH worker，非控制机重型构建。
- 本轮用户未要求发布；不重复部署上次候选，不自动跟踪新HEAD；生产仍按独立授权安装事务。

## 开发完成与验证（2026-11-17 10:40 CST）

- Web develop/GitHub候选 `62fffa7443b3d33b2729e9dd7a1631bed8546de9` / tree `4c131eeab34f2dcb7f70a62472371cd3c0b65bc7`。包含上次尚未上线的自动分页ef5903f，未改package/lock版本；组件工作区干净。
- 原型先改result操作行及规格，产品由HallMessageParts把文件保存按钮放入现有HallMessageMedia.actions插槽，与预览/下载同排；密议专属nowrap保持短文件名卡片也不换行。文本资产的原保存及下方状态查询不变，事项/公议仍无保存/下载。
- Media只提供下载能力和busy插槽参数，业务可见性由Parts既有discussionVariant负责。复用鉴权资产GET、outputDownload.saveOutputBlob原文件名净化/浏览器及小程序桥。无POST或个人资料写入，无新增后端接口/依赖/全局配置开关。
- 单次下载防重复点击，失败显示错误且可重试；独立AbortController在身份/资产/版本切换及卸载时取消，不让旧下载越过身份切换后落盘。不把下载完成显示成资料已保存。
- 203.32.84.239固定候选稀疏源码及原只读依赖：7个selector **186 PASS / 0 FAIL / 0 pending**，执行6.282秒，含证据回传7.461秒。范围：保存原幂等/状态恢复、真实文件行及事项验收隔离、原始下载字节/文件名/鉴权GET、防重复/失败重试/桥失败、身份/资产切换/卸载取消、已有小程序下载桥、原预览、选材、原型流程。不是生产构建/包或发布证据。
- 第一次worker185PASS/1FAIL：稀疏测试输入遗漏既有completed-message-delivery-v3.json，未改产品或测试断言；保留原失败，补齐同commit的真实fixture后新批02通过。中间一次准备命令参数不适配git及一次复用已存在传输证据目录均在测试前失败，原日志保留；未覆盖失败回执。
- 控制机最小诊断135 PASS。真实Chromium 1440×1000、390×844、320×740：长/短文件名两张原组件卡片均预览/保存/下载同排、无横向溢出；保存状态变化、原文件名和字节下载通过，一次GET，pageerror为空。仅API/保存I/O使用fixture，不冒充微信真机或线上验收。浏览器及本任务Vite服务已关闭。
- 未生产构建/打包/部署，未重启任何生产服务。生产安装记录仍d3fbbaa9e5174b694a37a3ad8778b1d4e0495296；上一项自动分页及本项均待另行授权发布。worker仍低磁盘，不清缓存/他人目录/生产/备份来强行打包。
- 汇总 `/home/isp/state/cyf-private-file-actions-20261117/verification.json`；`remote-test02/{source,inputs,result,tests,attempt}.json`、`run.log`，首次失败在remote-test/；browser/browser.json及三尺寸截图。worker测试输出 `/home/isp/state/cyf-local-build/tasks/cyf-private-file-actions-tests-20261117-02`，源码身份与Node/锁/依赖回执/实际输入摘要已留存。


## 本轮Web统一发布及线上验收（2026-11-17）

- 用户明确授权“现在部署”；仅Web，固定候选 `62fffa7443b3d33b2729e9dd7a1631bed8546de9` / tree `4c131eeab34f2dcb7f70a62472371cd3c0b65bc7`，包括此前ef5903f单预览/自动分页及密议操作行。不自动跟随其他HEAD。GitHub develop只读核对同候选。
- 指定SSH worker执行原 `local_web_build.py`：**656 PASS / 0 FAIL / 2既有pending**，31个selector；fresh生产包、完整性检查和回传合计 **267.913秒**，未超过600秒。构建本体113.433秒；不以原195/186测试替代本批成功。原LOCAL安装事务 **17.190秒**，621项包内文件、264项线上文件核验，当前记录online_verified。
- 初次655PASS/1FAIL/2pending：稀疏快照遗漏 `tests/fixtures/interface-standard/http-envelope-fixtures.json`，补齐同commit真实fixture后在全新输出02重新执行；原失败/26.072秒记录保留。另一次02准备脚本转义错误未进入应用构建，脚本及日志保留。未修改产品、断言或安装保护。
- 构建准备仅删除本线程d3批次已核验对象字节一致且有独立完整Git副本的web-snapshot重复传输仓库；保留原源码、构建证据、缓存、生产/回退包及其他Owner内容。沿用62固定快照，收窄无关地图截图fixture物化；生产src/public/static及根配置709文件逐一核对Git blob，实际输入890文件SHA记录。没有切换tmpfs或控制机源码构建。
- 真实生产Chromium：办事桌面1440×1000、移动390×844每行一个预览/一个移除，固定V2文本原件预览正确；桌面资料列表真实滚动由50到80项、80唯一ID，无手点加载更多。花荣已有两个XLSX文件卡片三按钮同排，移动/桌面均核对；下载 `NATIVE6_MATERIAL_V2.xlsx` 为5139字节有效XLSX、原V2标记正确；原件表格预览显示V2、¥1,234.50和25%。未点击生产保存，不将可见性验证冒充新增个人资料写入成功。
- API PID1549576前后相同、HEALTH=UP、ARTIFACT_ATTESTATION=MATCH；未改API/Runtime、未发起新Agent执行/正式事项，个人资料保存POST为0，pageerror为空。未验证微信真机，不宣称119项全局回归或全部历史事项通过。
- 证据 `/home/isp/state/cyf-preview-actions-release-20261117/release.json`、`live-acceptance.json`、`download-verification.json`、`install.log`及after-*.png；正式包和构建证据 `/home/isp/state/cyf-local-build/tasks/cyf-preview-actions-web-20261117-02/`。包SHA-256 `0803e2bb3bf9a545affdf100b1bf570d4dd461623c33e582b520e8369ddedd96`；原备份 `/var/lib/cyf-web-flow/backups/61f80dd05fd0fa3939fc8e4251df57522cc42638b76d353a6708693852627fe2`。控制机包已按原入口登记完成保留；worker缓存和历史包不额外清理。
