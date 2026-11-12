# P1 基础包候选与证据快照

记录时间：2026-09-06T13:14:40+08:00。此为交接证据，不是第二执行台账；当前 owner/gate 仅查 TASKS.yaml runtime_ledger_json。

## 候选
- Web commit `a4962c4f191c48ab008780bd147026ce5109a914` / tree `e76e0a293062928c2dd8a7572cc4958c37c43d96`。
- Parent `cc625953ee047fef80b184bc958189cc7ad8da69`；本次仅预览组件和组件测试两文件整改，累计基于101ac新增P1约定四文件。协调者已核对clean、父提交和改动清单。
- 原 Terra Owner `01a07470-7977-7b72-a7c5-9f0b4c336336`；未接入现有页面/引擎，不修改共享文件或包配置。

## 验证
- R4 显式双selector：1 suite invocation，9 tests，pass9/fail0/error0/skip0。
- 共享日志：`/tmp/jy-live-preview-terra01a07470-p1-targeted-test-r4.log`。
- 命令（在本任务worktree）：
  `node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec --timeout 30000 --exit tests/unit/juyiting/live-map-preview-policy.test.js tests/unit/juyiting/hall-live-map-preview.test.js`
- 本候选尚无独立 ACCEPT；未运行 production build 或真实浏览器/微信验证。

## 不覆盖历史结论
- 旧cc625/56b31的9PASS不覆盖其唯一Reviewer `01a0750c-296d-7673-b441-a0a786dead9e` 的 REJECT0/1/1。
- 新修复针对IO首次可见性、卸载晚回调和有限操作数产生无效宽高比；是否关闭 finding 必须由新exact-tree fresh Reviewer判断。
- R3失败实际在卸载后读取已被test-utils清理的事件历史，非运行时IO事件丢失；R4仅更正外部事件spy，未误重写已修组件。
- 归因矩阵 `/tmp/jy-live-preview-coordination-20260906-r{1,2,3,4}.md` 保留，不将失败改记PASS。

## 尚未解锁的后续工作
- 新候选fresh P1 Review待准入；已按orchestrator发送只读槽位冲突告警，不抢占其他任务或创建超额Reviewer。
- P2仍需原共享路径正式交接，并与新布局任务核对不重叠；计划承接已部署d81/d712或主控正式确认的被接受后继，保留reader与SCREEN修复。
- P1基础包不等于动态地图功能完成，不证明单Canvas/运动连续/真实20fps/浏览器滚动；整功能接入、最终构建、集成Review与发布仍待完成。

## 后续独立验收回执（2026-09-06T13:25:58+08:00）

此段更新前述“本候选尚无独立ACCEPT”的历史状态，不更改旧tree的REJECT或失败证据。
- 唯一 fresh 权威 Reviewer：`01a07526-9aac-7381-bce0-b2828aa3f7d5`（Raman4）。
- exact `a4962c4f191c48ab008780bd147026ce5109a914` / tree `e76e0a293062928c2dd8a7572cc4958c37c43d96` 获 **P1_FOUNDATION ACCEPT，P0/P1/P2=0/0/0**。
- 旧 findings **2/2 关闭**：IO首回调前不制造可见、无IO降级及disposed晚回调保护；width/height商再次验证并对Infinity/0回退。
- Reviewer独立核对源码blob/clean/四新增路径和R4共享9/9测试证据；没有重复运行test/build或修改源码。
- **仅P1基础子门禁通过；整个功能未完成、未构建发布、未证明真实Canvas或人物运动。**
- P2仍等待包含reader/SCREEN及新LAYOUT的被接受累计后继与exact共享路径回执。旧d81是历史已部署参考，不能作为覆盖后续已接受布局修改的依据。
- 已主动回报主控，请在唯一ledger登记子门禁及释放已完成Reviewer；后续仍由原Terra实施，最终集成另作fresh独立Review。
