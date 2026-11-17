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
