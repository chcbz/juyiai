# Web 会话成果预览/下载：真实字节不匹配反馈

日期：2026-09-30。Web feature 提交 `0292c379e742e601a8b1c32df51c3f7425442425` / tree `5eb1be814ada00651c3aa2a22afdcb1ab36faf0a`，已推送并回读远端同SHA；根仓同步指向此 gitlink。修复现有成果区对不合法响应或字节长度不等时静默返回的行为：明确报错，不生成预览 URL、不下载损坏字节；即使 SHA 正确，预览**和下载**也需校验实际响应 MIME 与服务端目录一致。身份切换或主动取消依旧静默放弃晚到响应而不误报失败。

在提交前的相同源码树中，本机使用 `node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter dot tests/juyiting-bounty-output-gallery.test.js tests/juyiting-bounty-output-catalog.test.js tests/juyiting-bounty-output-recovery.test.js tests/juyiting-bounty-inline-results.test.js --timeout 30000`：**13 passing，0 failing**。首次新增测试未等异步摘要计算完成而失败；改为等待可见错误后，定向用例及四组相关测试通过。`git diff --check` 退出码 0。现有 Web 源文件模板以及测试中的旧语法规则在 `npx eslint <组件> <测试>` 下报告 15 项存量错误（主要模板属性换行/测试环境全局量）；未运行或伪报完整前端构建/云端测试。此次修改的行未引入这些错误，也未借机改写无关模板。

此检查只证实前端拒绝并解释**虚拟 API 返回**的失配。服务端持久会话资产仍未合入，真实图片生成、预览、下载、归档、正式验收、浏览器测试及发布均未执行；34 项产品验收保持 NOT_RUN。
