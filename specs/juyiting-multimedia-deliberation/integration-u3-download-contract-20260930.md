# 实际下载 MIME 合同收口

日期：2026-09-30。API `a0697cc1585b4bbbfc8cb7f00f77df7f2ea269da` / tree `462845b84b07f3d5fbee991a7906e2d58cfbe040`；Web `4e321ea6303d3523f9a181cab61474da69162f81` / tree `d3b575b7e3a93d2d1aa7f7f3db09447e7f4b4047`。两仓特性分支已推送，根仓 pin 同步。

源码对照发现此前服务端在 `download=true` 时将已验证 PNG 等文件全部标成 `application/octet-stream`，而 Web 对预览/下载均要求 Blob MIME 与素材清单一致。因此前端 mock 返回 PNG 的测试通过，并不代表实际接口 PNG 下载可用。已修复：受控被动格式（四种栅格图像、五种音频、文本、PDF、Office）下载、HEAD、Range 保留真实 MIME；仍用 attachment + nosniff，未知/主动内容仅作 octet-stream 下载，不提供可执行预览。Web 按对应下载表示类型验证，未知文件仍验证长度和 SHA-256；文件名按可信输出 ID/MIME补 `.png/.m4a/.pdf` 等扩展名，未知用 `.bin`。API/Web 同步补齐 MP4/WebM 音频预览目录，不将其误作任意文件。

验证：串行 orchestrator、本地授权定向 Gradle，exact API `ChatBountyMediaControllerTest` **11/11 PASS，0 failure/error/skip**，包括所有上述 MIME 的下载/HEAD/Range、权限和主动内容负向。缓存 key `2564a2db4b3002e6a261b679c1ea120bd4060567be75c5b0848e1d64d389dedc`；XML 在该 `api-media-download-contract` 工作树的 `chat/jia-chat-service/build/test-results/chatDeliberation/`。首个控制面调用因 argparse REMAINDER 参数顺序错误失败，没有启动 Gradle；按归因更正后运行成功，不掩盖该失败。日志为主工作区 `evidence/u3-media-download-contract/gradle-a0697cc1-attempt2.log`。Web 四组定向 Mocha **17/17 PASS**，新增可下载 PNG/不安全格式仅 opaque 文件、可用扩展名及 MP4/WebM 目录测试；两仓 `git diff --check` 通过。

仍未做真实 Provider 画鸟、浏览器、生产构建或发布；asset 持久化及正式验收未闭合。另发现成果区保存仍发送 `outputRef/CREATE`，而当前 Chat 归档 Controller 只接受 `mode=create/items[].assetRef`；持久 asset 合入后必须接通精确映射，不能以本次 MIME 修复宣称保存功能完成。
