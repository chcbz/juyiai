# U3 受权媒体 HTTP HEAD / 单段 Range

API 四仓融合分支已快进并推送 `94492ea2e185ef5cbd631dc3bd41845b3a9aaa96`，tree `67f6308ce2e460a2a620b18467646f6a8a2e9b46`。`GET/HEAD /chat/requests/{requestId}/steps/{stepId}/outputs/{outputId}` 在每次响应前仍按当前身份验证 owner→request→step→CONVERSATION execution，并核验已提交内容字节数、MIME、SHA-256；不采信公开 URL 或浏览器自报 run。范围只允许单个 `bytes=start-end`、`bytes=start-`、`bytes=-suffix`；206 有 `Content-Range` 和精确长度；非法或不满足返回 416；`If-Range` 失配返回完整 200；HEAD 无正文。完整/部分响应均不缓存并保留 nosniff。当前仍是整份私有字节读取、校验后按需切片，不宣称存储层流式读取。

责任 Owner 本地 exact-tree 测试：`chatDeliberation` **24 类/123 项 PASS，0 失败/错误/跳过**（含控制器新用例和既有范围/越权回归）；仅该控制器 **9/9 PASS**。Gradle 通过 orchestrator `/tmp/cyf-gradle.lock` 串行；第一次配置因缺少非发布 repo 扩展属性在编译前失败；补非发布 init 后主机内核 OOM 杀死 Gradle daemon，按真实内核日志归因；使用 `-Xmx512m`、单 worker/测试 worker 256m 的已检查参数重新运行并通过。成功证据缓存 key：完整 `eb8dbf2bd20b9ecc26711080c9a64127b83773bb91d2b884141fdba829bddd50`、控制器 `f8995d95d2bbfcb82d0ab009936f4d253df17675a7a2692477e2a0496309b510`；测试 XML 在该 API worktree 的 `chat/jia-chat-service/build/test-results/chatDeliberation/`。不把先前 API `27aa2c78` 的 Provider START / MySQL **51/51** 当成此新树的重复验证。

**未合 develop、未部署、未做真实浏览器/音频文件的网络播放测试。** `part.ready` 与会话关联、工作空间主动保存、正式成果晋升/验收、费用授权及音频真实能力仍未闭合；不能通知用户验收。
