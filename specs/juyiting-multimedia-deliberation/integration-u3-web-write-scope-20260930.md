# Web 会话保存与验收写入回执的身份隔离

日期：2026-09-30。Web 研发分支提交 `cc4ca66ed073236a3b55964cb3143296dae09936`，tree `220ff37d993da83438a634aeee4cdf5b82ce927b`；远端同分支已推送。此前 `BountyExecutionOutputs.vue` 的工作空间保存、验收及修改请求在身份/会话切换时重置了展示状态，但尚未返回的异步写操作仍可把旧身份的文件 ID、验收结果或修改状态写回新身份界面。请求投影 stateVersion 更新也会无条件重置这些尚未确认的意图，导致本次页面会话中重试不能保留原键。

现在身份/会话/根请求变化或卸载后，以页面作用域 epoch 拒绝迟到的保存、正式验收及改稿回执/错误展示；下载失败同样不得显示在新身份。相同根请求的状态版本刷新仅更新成果列表，不丢弃当前作用域待确认的写意图。**已经发出的 POST 不等于被取消**；切换身份后不能据此宣称服务端没有受理，跨页面/跨端写操作状态恢复及验收 API 仍待后端闭环。

本机相同源码树执行：`node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter dot tests/juyiting-bounty-output-gallery.test.js tests/juyiting-bounty-output-catalog.test.js tests/juyiting-bounty-output-recovery.test.js tests/juyiting-bounty-inline-results.test.js --timeout 30000`，**15 passing，0 failing**，新增两例覆盖投影刷新保存意图和身份切换后的迟到保存/验收回执；`git diff --check` 通过。测试含其他组件的既有 Vue 模板警告。没有真实后端、浏览器验收、正式构建、流水线或发布证据。
