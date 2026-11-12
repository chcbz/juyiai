# 回复流内的多媒体片段消费回归

Web 特性分支快进并推送 `af5c6cb984a3d8a612be539fc8b2d919b917e335`，tree `22cc795cabeb742a54ca8b8b51307e8386901f6d`。此前请求回复流若收到附有 `requestId` 的 `part.ready/part.failed/part.processing`，会被状态分支提前消费，导致现有会话片段 reducer 不执行；SSE 路径已正常走该 reducer。现让回复流的三类片段使用相同的会话身份/消息版本 reducer，保持其他请求状态和文本回复逻辑不变。

本地定向 `node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter dot tests/juyiting-multimedia-parts.test.js tests/juyiting-bounty-inline-results.test.js tests/juyiting-bounty-output-gallery.test.js tests/juyiting-bounty-output-catalog.test.js tests/juyiting-bounty-v2-binding.test.js`：**16/16 PASS**，其中新增实际 `useHallConversation.sendHallMessage → onStream → 消息片段` 的挂载外行为用例验证重复、旧版、跨会话输入不覆盖既有 ready。`git diff --check` PASS。定向 ESLint 在修改文件报 `force`、`safeMetadataSource` 两个未使用变量；原 HEAD 同文件逐字 lint 报完全相同两项（原行号 864/1174），本次未引入 lint 诊断，未以此宣称 lint 全绿。

**未实现**：后端持久化 `part.ready`、会话资产的受权内容端点/归档、正式成果/验收与在线浏览器验证。此补丁只确保未来服务端事件不会在回复流上被 Web 吞掉，不等于画鸟流程可用。
