# 2026-09-30 同会话改图意图恢复

Web 特性分支 `codex/juyiting-multimedia-deliberation` 自 `ca58830` 快进至 `4a123eadf0f6643dedc1171f6555e8fc3f7279f3`，tree `d28a190d8559a8137624c937cfdafa2837616ff6`（先 `0cb52c0`，后续修正重试时输入只读并显示原始正文）。聚义厅成果区的「引用此稿修改」原先在网络结果未知时每点一次都生成新幂等键，存在重复付费生成风险；编辑请求已受理后 `followupRequestIds` 只存内存，刷新丢失新稿索引。本次在当前浏览器会话内将精确原稿/身份/会话/根请求范围的编辑意图及已受理后续请求保存为可恢复记录；发送前保存原幂等键，未知结果仅能显式重试同一请求，已受理的后续请求在刷新后重新查询服务端目录。身份或会话改变隔离记录，不自动重新生成。

Exact HEAD 本地定向检查：`node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter dot tests/juyiting-bounty-output-recovery.test.js tests/juyiting-bounty-output-gallery.test.js tests/juyiting-bounty-text-selection.test.js tests/juyiting-multimedia-parts.test.js tests/juyiting-hall-conversation.test.js tests/juyiting-codex-fast-deliberation.test.js`：**95/95 PASS**；`git diff --check` PASS。包含首次网络结果未知、刷新后保持同一幂等键和请求体、后续请求重新 GET、错误身份范围隔离。

只保证同一个浏览器会话对已知请求的恢复；服务端跨端请求列表与正式 finalization endpoint 尚未实现，不得宣称验收可用或生产已发布。没有真实 Provider 或浏览器图片证据。
