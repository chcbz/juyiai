# Web develop 发布（2026-11-16）

Owner：`web_release_owner`（developer）；任务 `WEB-DEVELOP-DEPLOY-20261116`。

## 固定范围与候选

用户授权从GitHub前端develop拉取并部署；2026-11-16重新提交后已fetch并ff-only更新至`46768a2999dd1f3ddc24db1e1483656fdf06162a` / tree `aa82a22c748fa460538d2109f63fb8901170495e`，package版本仍为1.16.150。本次不改源码/版本号、不发API/Runtime、不提交微信小程序审核；小程序源更新不等于微信客户端已经发布。

GitHub此前返回2ee2349a，不能把此前旧候选幂等尝试当作本次发布。旧尝试因控制器Python3.11系统CA环境不同导致线上验证超时，原失败保留在`/home/isp/state/cyf-web-develop-deploy-20261116-1423/`；未改变生产。新安装调用原helper的系统Python，预检HTTPS200。

## 执行边界

固定干净Web源码；SSH worker203.32.84.239执行原local_web_build.py，使用原RemoteBuild传输和600秒构建/回传总预算。组合local_release.py无Web-only开关，故复用其原Web builder/传输/安装事务，不运行无授权的API构建或安装，不新增仓库runner。当前CLI调用留证在任务私有目录execute.py。

原8组基线追加wechat-material-import、juyiting-component-behavior、juyiting-prototype-draft-flow、juyiting-mini-program-orientation、mini-program-file-download、personal-workspace-essential。固定生产公开VITE配置核对；原helper负责锁、前代CAS、完整归档/安装摘要、备份恢复和线上入口/JS/CSS验证。接口规范路径`/home/isp/wsps/cyf/api/docs/interface-standard.md`，本次仅发布已有Web候选，不改API合同或后端。

## 证据与状态

执行中：`/home/isp/state/cyf-web-develop-deploy-20261116-1523/`，精确输入、SSH源码/传输、日志、release.json、install-descriptor.json；原包/测试报告`/home/isp/state/cyf-local-build/tasks/cyf-web-develop-20261116-01/web/`。安装/验收以新release.json实际结果为准。未执行全局119项或微信真机业务闭环。

## 已完成（2026-11-16约15:31 CST）

- `web-develop-20261116-01` RELEASED：worker203.32.84.239，源码准备194.957秒另计；必要测试/构建/打包/回传261.719秒（600秒内）；原安装16.512秒另计。
- 315项：313 PASS / 0 FAIL / 2 pending。package版本未变1.16.150，线上源码已变为上述46768a2；不能仅按版本字符串区分本次发布。
- 原包SHA-256 `20d60536127c575cde09f01902e1f472d7346506cf42762d7f76c4336cb40df5`；原安装器PASS，613安装文件完整验证、30变更文件、256线上入口/JS/CSS实时摘要通过。原备份`/var/lib/cyf-web-flow/backups/238e65aed168ed73d08c37f15bededa8c036e8968f5070576f4b72a928b0d185`。
- 完整原始报告及日志另存包外`web/`；原包按既有策略mark-complete登记。仅删除本任务远端干净源码快照及本机重复Git/传输包；构建产物、缓存、测试/传输/发布证据及备份保留，cleanup/receipt.json留证。
- 根文档检查已执行，详见docs-check.log；公开导出例外/未核实引用不当作业务通过。本轮未执行全局119项、已认证用户业务或微信真机；小程序仍需配套发布。未改变API/Runtime。

## 新候选发布（2026-11-16 15:44开始）

用户再次要求更新部署；GitHub fetch后干净工作区ff-only更新至`5a1a1089b4015c4b3d9d58a800e7d21ce551467d` / tree `62ac7c4797ffdad3d98738261ec5004d425a430a`。Owner不变，沿原CLI重新claimed，独立批次`web-develop-20261116-02`。本次保留上述14组基线及影响回归，旧发布/失败记录不改；不重新创建worktree，不发API/Runtime。变更主要在微信原生资料页（自动打开选择器、自动返回），已明确Web部署不代表小程序审核/发布完成。

本次证据`/home/isp/state/cyf-web-develop-deploy-20261116-1544/`，包`/home/isp/state/cyf-local-build/tasks/cyf-web-develop-20261116-02/web/package/web.tgz`。实际结果以新release.json为准。

### 第二批已完成（2026-11-16约15:56 CST）

- 新候选5a1a108正式RELEASED，318项316PASS/0FAIL/2pending；源码准备203.35秒另计，构建/打包/回传482.614秒，未超过600秒；安装41.898秒另计。网络中途降速后恢复，没有扩时/重试、清缓存或修改带宽。原网络观测日志保留。
- 制品SHA `ca84fe05c9af9bbee5c24a61a27a5dec15eb7af0f92f025df5fc1bd7380f53fd`，原helper613安装文件及256线上资源摘要验证通过。**changedFiles=0**：本提交只改小程序/原型/测试，生产Web静态字节与上一批完全相同；安装记录已绑定新候选，但不能声称微信端交互已上线，仍须单独发布小程序。
- 原事务备份`/var/lib/cyf-web-flow/backups/10f55501be9f7ced39e2abed5de121f1f97236540255f037dd092a0bf0dcc65d`；包与测试/构建/传输/发布证据保留并mark-complete，仅本任务重复源快照/传输归档已清理。API/Runtime未改。

## 2026-11-17 微信资料返回误冲突修复（用户已授权修复并部署）

Owner仍为web_release_owner；复用当前干净Web工作区，base cb3be686e2e75539a6f815110451c985d4afff38 / tree035c1ba4a95711232b18a0a948d7b5dc5f9d6555。只修共用page-return恢复生命周期/版本同步，不改API/Runtime/微信原生上传合同；接口规范仍为api/docs/interface-standard.md。
诊断证据：/home/isp/state/cyf-wechat-return-diagnosis-20261117/conclusion.md（线上完整花荣密议受控取消返回，两条连续提示均复现；非真机）。
原型先更新现有material-wechat.js与prototype-spec.md的初始化直返/真实冲突规则；不新增视觉组件。修复在协调器阻止恢复前初始化保存，业务scene比较排除纯UI版本变化，完成/保留共用版本同步；保留实际跨页保护与未知写入意图。最早定向验证page-return用例，追加真实组件初始化与继续编辑回归。正式验证走原SSH worker/LOCAL安装事务，600秒构建/回传预算，安装另计。证据目录/home/isp/state/cyf-wechat-return-release-20261117；尚未构建/发布。

### 本次固定候选与构建/安装证据

- Web `8b69e1d7a668775d0facec20cf95b368045e4d5f` / tree `696126b05f02ee918edcd8f932a3da260c856d11` 已提交GitHub develop并获用户本轮部署授权；package版本仍1.16.150。只改2个产品JS、原型JS/规格和page-return测试，不加依赖、不改API/Runtime。
- 控制机轻量定向36PASS；第一次35PASS/1FAIL发现采用恢复稿未清旧error，已修并在新候选重验。正式SSH原33组选择器708PASS/0FAIL/2pending，含首页/公共/密议/事项初始化、取消/文件结果、真实材料删除冲突、两种冲突选择后空稿/继续编辑、重复返回和未知写入等。非全局119项。
- 原型PC1440/移动390取消初始化直返PASS，截图与prototype.json在本批证据目录。原型首次重复goto同URL保留上轮dialog导致脚本点被遮挡，独立重新载入后通过，不作为产品失败/正式业务通过。
- 构建服务器空间不足：仅退役本Owner已结束的web-develop-20261116-01/02的两份冗余worker包副本，逐份核对控制机保留原包与SHA、当前/回退保护、锁/占用/keep；保留全部原始日志、源码、缓存和控制机原包。方案/回执replica-retirement*.json。
- 正式批次`wechat-return-web-20261117-01`沿原builder/SSH rsync直接回传包与小证据归档，避免再造103MB运输副本。测试/构建/回传236.174秒；最后核验脚本误假定旧producer有artifact.size，报KeyError，原失败日志保留；未重建、未改回执，额外只读核对worker实际size/SHA后完整收口291.864秒，仍在600秒内。
- 包107948545字节，SHA256 `b15672df919f85b4132a69f085191bd222dc5633a111750bf2922d0151e98aa8`；原LOCAL安装器37.707秒，265线上入口/资源摘要PASS。备份`/var/lib/cyf-web-flow/backups/8381f5529f390f391d2319906340557a27f95dbc37ca18951eb5b05c930499a0`。正式测试/制品在`/home/isp/state/cyf-local-build/tasks/cyf-wechat-return-web-20261117-01/web/`；发布/验收在`/home/isp/state/cyf-wechat-return-release-20261117/`。
- 线上完整页面回归继续执行中，不能以安装成功代替业务验收；微信原生调用为受控替身，不宣称真机。

### 完整页面验收补齐只读初始化分支（第二固定候选）

首批手动真实页面已验证原两条误报消失；冷启动自动化发现另一条相同生命周期遗漏：会话历史仍在读取时恢复进入readonly，资料刷新把尚未展示的pickerOpen=false写回；之后可编辑时丢失重开选择框标记。线上存储调用栈记录当时刷新按钮/正文均disabled（private-huarong-cancel-failure-1794891439500.json），新增用例先36PASS/1FAIL复现，再修正为38PASS。最终改动只在同一canPersist中排除readonly恢复状态，不全局禁止业务忙碌后的权威正文清空（另有post-send回归），不增加新恢复分支/延时。
第二候选`723f0ac1b13cbfd5416ba73f40c82c3a785339be` / tree`d8db986c5ec23b2cb0f9c70fd68e3d1468addded`，新固定批次`wechat-return-web-20261117-02`；第一批安装/验收中发现的缺口及脚本等待失误全部保留，未重标全通过。第二批证据`/home/isp/state/cyf-wechat-return-release-20261117-02/`。本候选仍为Web-only授权，不创建消息/执行/关联/上传等业务副作用。

### 最终部署与验收完成（2026-11-17）

- 最终Web `723f0ac1b13cbfd5416ba73f40c82c3a785339be` 已推送GitHub develop、已受控部署。原33组测试710PASS/0FAIL/2pending；第二固定批次必要测试/构建/打包/回传236.457秒，安装18.708秒；265线上资源摘要通过。包SHA256 `fa397b9ebc0ff4c944b8dbfdafced975e321f96022b4813dcaafd8bb7c4732b2`。
- 线上完整页面：花荣密议PC取消返回、张清密议移动尺寸取消返回、既有事项600移动尺寸取消返回、首页移动尺寸取消返回、花荣真实页面人为构造不同本地稿后选择“保留当前稿”，5项均PASS；每项继续输入并清空正文，保存正确且无二次误报。选择框恢复成功。只读真实业务接口，原生postMessage/redirectTo与取消结果为受控替身；未发送消息/执行、未上传、未保存或关联资料，不声称微信真机验收。
- 自动化初期提前点击/错用移动端桌面选择器的失败日志保留；最终用已就绪会话与移动端实际“添加资料→微信”路径，不修改产品延迟/超时来掩盖。readonly缺陷有独立失败用例及线上disabled状态存储调用栈证明，不归为脚本失误。
- GitHub第一次普通推送网络空响应、下一次超时后先匿名读ref确认仍8b69；现有凭据API200核验后用同凭据进程内预认证HTTP/1.1完成push。无凭据写入Git/参数/回执，无强推/远端配置修改。
- API前后PID1549576，UP/attestation MATCH；本批未改Runtime。回退备份`/var/lib/cyf-web-flow/backups/6c22002e142d5baf67ccba5d2ae6955ac94f3e82888efef1f3cc5edfd1032e68`。完整收口`/home/isp/state/cyf-wechat-return-release-20261117-02/final-verification.json`与acceptance.json/截图；首批诊断、构建、安装与失败证据仍保留。不宣称全局119项。
