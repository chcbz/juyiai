# 好汉详情密议入口修复（2026-11-17）

- 任务：AGENT-DETAIL-PRIVATE-ENTRY-20261117；Owner：agent_detail_private_entry_owner_20261117。
- 范围：好汉名册/详情进入普通密议的导航；不修改后端/Runtime/执行协议，不处理另一问题“未恢复现场”。
- 工作区：`/home/isp/wsps/cyf/web`，develop；base commit `b47358e631e54c4e830483538d68e9401c90ef16`，tree `99af4603edd3758d3e77dcf1114bf7989b09ed94`。开工组件干净；根仓其他Owner脏修改保留。未查询远端最新，不声明此base是当前GitHub最新。
- 接口规范：`api/docs/interface-standard.md`；无接口字段/语义变化，无相关消费者联动。

## 原因与修正

`JuyiHall`的panelDepth把好汉详情计作一层，“我的→好汉名册→好汉详情”已达到三层。`handleStartAgentConversation`原先直接`openPanel('chat')`，被三层限制拒绝，正是截图Toast来源。正式承办入口已使用`consumeAgentSelection`移除选将页及其详情层后进入议事，但普通密议漏用。

复用该既有能力：密议入口改为`openPanel('chat', { consumeAgentSelection: true })`。其余权限、语音锁、草稿保存、层级约束保持原样；不增加导航特例框架、服务或开关。名册/详情进入后返回原来源页，如“我的”；首页/地图无agents frame时行为不变。

## 原型先行与覆盖

先更新唯一原型`web/prototypes/juyiting/prototype.js`的`openPrivate/go`及`specs/prototype-spec.md`，明确选将页由密议替换、返回来源页；随后修改产品一行。原型只做语法检查，未冒称浏览器/小程序真机已验收。

## 轻量定向诊断（不是正式SSH构建/发布证据）

证据目录：`/home/isp/state/cyf-agent-private-entry-20261117/`。

- 新增4项真实挂载JuyiHall/真实模板事件回归：横竖两种体验×名册/详情，按钮事件进入private、目标精确绑定、返回我的、不残留agent frame，外部好汉拒绝。
- 修前4项失败：详情无法进入chat，名册保留多余agents frame；`before-reproduction.log`。
- 修后首次fixture漏填真实chat context消费的agents列表，导致context保持public；保留`after-diagnostic.log`。修正fixture同时提供真实agents/operableRosterAgents，不修改产品权限逻辑。
- 最终上述4项＋原正式承办导航2项＋原外部承办权限1项＋原三层导航1项：8 PASS，约3秒，`after-fixture-diagnostic.log`。既有var-dialog stub warning未当错误掩盖。
- 最初从根目录启动Node找不到tsx，仅命令位置错误，保留`before.log`；之后在web目录执行。没有安装依赖或清缓存。
- 原讨论入口草稿保持测试原有提取边界包含后来新增的material handoff及watch，出现`watch is not defined`（`draft-diagnostic.log`）；仅收紧该入口测试的函数截取边界，保留失败证据。修后12 PASS，16ms（`draft-fixed-diagnostic.log`）。最终两组轻量定向诊断共20 PASS，不是全量前端测试通过。
- `node --check prototypes/juyiting/prototype.js`与`git diff --check`通过。

## 交付状态

源码已修改、受影响轻量定向诊断通过；未运行正式SSH测试/构建，未提交/推送本候选、未部署，截图所示线上版本尚未因此改变。实体微信小程序未验证。后续若获发布授权，按根AGENTS在203.32.84.239固定完整commit/tree构建，通过既有LOCAL安装事务发布，不复用旧版制品冒充本次验证。


## 已授权部署与线上验收（2026-11-17 09:45 CST）

已按用户明确授权与文件“保存”范围修复同批发布；本节取代上文开发阶段的未提交/未部署状态。GitHub develop及线上commit `d3fbbaa9e5174b694a37a3ad8778b1d4e0495296`，tree `e76cc709e671d407dc03dde4e5bbe52bb6679f5a`，buildId `private-entry-save-web-20261117-02`。

SSH正式测试357PASS/2既有pending/0FAIL，含回传247.361秒；原LOCAL安装35.704秒，621文件/264线上资源核验通过。390×844下花荣、张清均从“我的→好汉→详情”直接进入对应密议，花荣返回“我的”正常；1440×1000同链路通过。API PID1549576未变，HEALTH=UP/ARTIFACT_ATTESTATION=MATCH；不重启Runtime，未验实体小程序。

唯一发布任务`WEB-PRIVATE-ENTRY-SAVE-20261117`已accepted。首批失败/新候选、完整摘要/备份、安装前预检查纠正、包登记和空间处理均见[同批保存入口handoff](PRIVATE-FILE-SAVE-ENTRY-20261117.md)；汇总证据`/home/isp/state/cyf-ui-fixes-release-20261117/release.json`。
