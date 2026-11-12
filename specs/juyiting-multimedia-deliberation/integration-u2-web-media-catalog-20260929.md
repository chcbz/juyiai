# U2 Web 受权输出展示（2026-09-29）

Web `codex/juyiting-multimedia-deliberation` 提交 `4cc676e2d385629d1c507b345a49bc529ee90697` / tree `c355e6b61ebe3f8a60376a9a299132fb20912e32`，由隔离工作树快进合入并推送；SDD web gitlink 更新为该精确提交。仅在已有议事 v2 UI 开关开启且活动 request 属于当前 conversation 时按 request→EXECUTE step 查输出目录；服务端受权接口返回 URL 后，浏览器使用用户 token 按需获取 Blob，再渲染图片/音频/文本与下载。不使用 Agent 自报公开 URL；过滤不匹配的目录/媒体。身份/会话/request 变化时取消在途请求、释放 Blob URL，并抑制旧身份异步错误；输出仅是预览/下载，**不等于保存工作空间或正式交付**。

最终树本地定向 Mocha `juyiting-bounty-output-catalog.test.js`、`juyiting-bounty-v2-binding.test.js` **4/4** 通过；`BountyExecutionOutputs.vue`、`BountyDiscussionPanel.vue`、`JuyiHall.vue` 经 Vue SFC script/template 静态编译通过，`git diff --check` 通过。未进行真实浏览器/云端构建/发布；未证明实时消息内媒体 part.ready 或可选参考素材可用。开关仍关闭，不能通知产品验收。
