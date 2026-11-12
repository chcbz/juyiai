# U2 fenced 原生输入合同（2026-09-29）

API `codex/juyiting-multimedia-deliberation` 精确提交 `eb10400627c1002fdf040601b587e75b4be06d29` / tree `f2a93567f221c8f0b9dbcaad0ef96a5d50c95ee7`，Client `isp-install` 精确提交 `376953cf40039161b6174c76e5e91d60a295b5ca` / tree `ea4c46c7adbf4da3129668b5533da520e6ff545b`，各自从隔离分支 byte-exact 快进合入并推送研发特性分支；**没有合 develop/发布**。

API 新增仅原生 Agent Runtime 可调用的 `POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/inputs`，JSON 正文为当前 `{version,token}`；在同一任务根锁下校验当前 Agent/owner/client/tenant、真实 grant、未过期租约、run 身份与锁定执行的持久输入行。仅当输入行真实为空时返回 `executionId,leaseVersion,noReferencedMaterials:true,inputs:[]`；若未知或存在输入行则拒绝，不落回旧的无 fence `/inputs`。Client 只有在领取后读取到严格匹配的、空且 `noReferencedMaterials=true` 的权威快照才考虑执行；缺失、异版本、异 execution、有参考资料一律失败关闭。**Client 仍未装配真实执行器；绝不调用付费 Provider、伪造生成图或假装参考图已支持。**

API 首轮在编译/测试途中被宿主内存 OOM 杀死（kernel 2026-09-29 17:07:21 +08:00，PID 1374235），有界 JVM 单 worker 第二轮 43 项中 1 项测试断言把 MockMvc 的 dot-segment 400 误认为必然 403，服务仍拒绝非法路径；仅调整测试为未经归一化的 `/extra`，归因和修复矩阵在隔离证据目录 `evidence/u2-native-inputs/remediation-matrix.md`。**最终 API 精确树**由 orchestrator 有界串行运行 `:agent:jia-agent-service:mmdU2ConversationOutput` 43/43（18 服务、21 真实安全过滤器、4 schema，0失败/错误/跳过），日志 `evidence/u2-native-inputs/gradle-eb104006.log`，证据 key `2c89f13707853e224f23706209f09ee9291a5e0cd2191db71558b27a83b5977c`。Client 最终树定向 `conversation-native`, `agent-client`, `chat-runtime` Node **160/160** 通过，日志 `evidence/u2-native-inputs/client-native-evidence-rerun.log`；最初隔离工作树缺 node_modules 导致测试进程装载失败，复用已有依赖目录后重跑通过，未修改代码或仓库依赖。

剩余：可信参考图片/上一稿输入版本的物化与原生受 fence 字节下载、付费授权/真实图像执行器、媒体消息持久关联/ready、工作空间保存/正式交付及验收、真实 MySQL/浏览器/部署。默认开关保持关闭，不可通知用户验收。
