# U2 Client 原生 fenced 执行接应（2026-09-29）

Agent Client `isp-install` 特性分支提交 `e52c5986925540b74e904859bb235712243c14b3` / tree `7a9e1211b7c9bfc6f5c5c1f3b811618af3aecfb8`，由隔离工作树快进合入 `codex/juyiting-multimedia-deliberation` 并推送。新增独立 CONVERSATION inbox/租约续期/受 fence 的 stage、commit、failure；独立 run 目录，不走普通 CHAT 工具与旧 unfenced 文件命令。未配置执行器时领取后真实报告 `CONVERSATION_EXECUTOR_NOT_AUTHORIZED`，不调用模型、不伪造图片/费用成功。

Owner 对该**精确树**定向 Node 测试 124/124、47/47 通过，合入为 byte-exact fast-forward。模拟免费执行器的单测仅说明协议；现有 API **没有 fenced CONVERSATION 输入读取端点或可信无参考资料标记**，也没有实际已授权的免费图像执行器/付费 Provider 授权。参考图必须 fail closed；在设计和实现准确输入端点及资金权限之前，不得开启真实生图或宣布“画鸟”可验收。本记录不是发布或实际浏览器执行证明。
