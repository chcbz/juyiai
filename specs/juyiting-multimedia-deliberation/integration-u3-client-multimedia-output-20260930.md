# Agent Client 多媒体会话输出：源码推进及本地定向自检

日期：2026-09-30。研发分支 `codex/juyiting-multimedia-deliberation` 快进至远端提交 `0d4224e2dbbe52788a69be0cb0844f0ad743c6b2`、tree `476e6665ded7fc5ca2eed38d593aef8680629adc`；原 pin `a2519de` 为此提交祖先，未重写快进历史。`conversation-native.mjs` 扩展受控输出 MIME/字节签名验证与文件后缀；服务端最终字节、权限和格式检查仍为权威，Client 本地判定不构成平台资产已就绪。

在此精确 Client tree 下，从 `conf/codex-ws-agent/` 执行 `node --check conversation-native.mjs`、`node --check conversation-reference-inputs.mjs`，均退出码 0；`node --test test/conversation-native.test.mjs test/agent-client.test.mjs`：130 tests / 130 pass / 0 fail / 0 skipped。首次尝试包括不存在的 `test/conversation-reference-inputs.test.mjs`，命令因找不到文件退出 1；随后检查实际测试文件清单，按上述正确的两个测试文件执行成功。增量 `git diff --check a2519de..0d4224e` 退出码 0。

本切片没有真实音频生成或图像 Provider 调用，没有 Agent 安装、API 联调、Web 浏览器媒体预览下载、MySQL 迁移、正式交付和生产发布证据；格式扩展不等于多媒体功能验收。未变更 API/Web pin，34 项产品验收仍以 `acceptance.md` 为准。

## 跨仓实际限制（下一步必须补齐）

在同日 API pin `a4f6501f`，`PersonalWorkspaceExecutionServiceImpl.createConversation` 只接受 `GENERATE_IMAGE` 且输出 MIME 仅 `image/png` / `image/jpeg`；其 `SUPPORTED_OUTPUT_MIME_TYPES` 及服务端 `PersonalWorkspaceOutputFormatValidator` 也没有开启音频、WebP/GIF、纯文本或 JSON 的 conversation 输出。Client 扩展的是**已授权后运行时本地验证能力**，不是服务端发单/上传/发布能力。下一 API Owner 应在真实 grant/目标能力/配置允许范围内按格式贯通准入、服务端字节检验、受权资产和预览/归档，并测负向误报；不能仅用 Client 130 项通过宣布音频或普通文件可交付。图片生成仍可先按现有受限格式完成纵切，但不能据此把整个多媒体版本标验收通过。
