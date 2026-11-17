# 密议文件保存入口范围修正（2026-11-17）

- 任务：PRIVATE-FILE-SAVE-ENTRY-20261117；Owner：agent_detail_private_entry_owner_20261117。
- 范围：仅普通密议显示会话文件“保存”，简化按钮文案；不修改事项成果/验收、后端接口、Runtime、原文件字节、独立文字片段保存或“未恢复现场”。
- 工作区：`/home/isp/wsps/cyf/web` develop，base `b47358e631e54c4e830483538d68e9401c90ef16` / tree `99af4603edd3758d3e77dcf1114bf7989b09ed94`。保留此前好汉详情密议导航修复及根仓其他Owner修改；未查询GitHub最新。
- 接口规范：`api/docs/interface-standard.md`；本次无接口字段或后端语义改变。

## 原因与实现

`ChatPanel`共用`HallMessageParts`；原保存条件只检查ready、assetId/revision及类型，不区分密议与正式事项。之前扩大文件类型覆盖时漏了业务上下文，因此正式事项也展示“保存到个人资料”。

先更新唯一原型`web/prototypes/juyiting/prototype.js`：普通密议产物独有“保存”；同步其`specs/prototype-spec.md`。之后产品沿现有`discussionVariant`透传到`HallMessageParts`，只在private下渲染整块保存区域（含状态及重试）。default/public/bounty均不显示；不新增独立业务开关、不以“非事项”猜测密议。

按钮普通/重试状态统一“保存”，busy“保存中…”，成功“已保存”；继续使用原幂等保存/只读状态查询，不改请求或创建额外操作。文件预览和正式事项验收slot不变。独立“保存文字片段”不在本次文件按钮范围内，未改。

## 验证与状态

控制机轻量定向诊断，非正式SSH构建/发布证明：

- `juyiting-conversation-archive.test.js` + `juyiting-bounty-inline-results.test.js`共44 PASS，约6秒。
- 真实挂载ChatPanel/BountyDiscussionPanel与HallMessageParts：正式事项无保存且仍可验收；private显示“保存”；切换public移除入口。
- 单组件private就绪text/image/audio/file仍可保存；非private/default既不展示入口也不读取其保存状态。原未知结果/原key恢复、身份变化等已有相关测试随同执行。
- 证据：`/home/isp/state/cyf-private-save-entry-20261117/diagnostic.log`。
- 原型`node --check`及`git diff --check`通过；原型与产品未做浏览器/实体小程序验证。

源码已修改，未提交/推送本候选，未正式SSH构建，未部署；线上仍为此前发布，不把44项诊断或原发布证明当本次上线证据。后续发布需固定完整commit/tree，在203.32.84.239按现有入口构建，并按明确授权执行LOCAL安装事务。


## 已授权部署与线上验收（2026-11-17 09:45 CST）

本节取代上文开发阶段的“未提交/未部署”状态。用户明确要求部署两项Web修复；不含“未恢复现场”的整改，不发布API/Runtime。

- GitHub develop/线上候选：`d3fbbaa9e5174b694a37a3ad8778b1d4e0495296`，tree `e76cc709e671d407dc03dde4e5bbe52bb6679f5a`；版本1.16.150，buildId `private-entry-save-web-20261117-02`。组件已提交/推送、工作区干净；控制器固定根commit `bc6c782d7ff7d0805a8650393fd51738c104efdb`，不带其他Owner工作区修改。
- 唯一发布任务 `WEB-PRIVATE-ENTRY-SAVE-20261117`；原Owner自检，不增加Reviewer。按统一接口规范，无API契约变化。
- SSH worker `203.32.84.239`正式基线+受影响selectors：359 total / **357 PASS / 2既有pending / 0 FAIL**。构建本体99.456秒，连同回传247.361秒，未超过600秒。首次批次01测试356PASS/2pending/1FAIL（静态测试截取了无关material handler）；32.056秒，保留FAIL/完整日志，未发布。只修正测试截取边界后新批02成功，未删测试或重标失败。
- 原LOCAL Web-only事务安装35.704秒，621文件完整性检查、264线上资源核验通过；改动33文件。包SHA-256 `9fac933c8580e7a83aa048e11cab8805aee520721e1e19f0a4626801140a5d07`，包107944944字节，前代CAS/锁/备份恢复均保留。
- 真实线上390×844：从“我的→好汉→详情”花荣/张清均直接进入对应密议；返回“我的”正常。花荣既有密议639原文件卡片显示2个“保存”，无旧长文案。1440×1000桌面同链路及保存文案通过。
- 真实线上既有张清正式事项693：保存按钮0个，预览入口仍在，读取原文件确认为`NATIVE6_TASK_ZQ_OK`。未重复创建/执行/验收事项，未再次保存个人资料；历史模型正文原样保留。浏览器pageerror为空。
- API PID1549576前后不变，HEALTH=UP/ARTIFACT_ATTESTATION=MATCH；没有重启Runtime。实体微信小程序未验，不将浏览器手机尺寸检查说成小程序真机验证。
- 证据：`/home/isp/state/cyf-ui-fixes-release-20261117/release.json`、同目录install.log与before/after截图JSON；正式输出`/home/isp/state/cyf-local-build/tasks/cyf-private-entry-save-web-20261117-02/`。包已按原mark-complete登记，不执行历史包/缓存清理。
- 安装前调用脚本两次仅本地预检查失败：第一次误用PASS（builder实际BUILT），第二次误把未被builder更新的publishable字段作为授权判据。核对原local_release后改用相同BUILT+sourceUnchanged+测试/制品/配置检查；均未调用安装器、未改生产。preflight01/02日志保留，未修改构建回执。
- 只清除了已核对SHA/tree、可独立重建的本任务旧/新重复传输副本，为普通磁盘准备空间；原产物/日志/源码、缓存、生产状态与备份保留。远端首批已结束后只移除其重复web-snapshot，保留完整实际源码和失败输出。首次保留登记参数误传绝对artifact被安全拒绝，改用组件root+相对package/web.tgz后登记成功；未运行clean。
