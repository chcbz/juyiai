# U2 初始/后续执行意图与安全 UI 投影（2026-09-29）

API feature commit `187fd535b87652890c11ec3f123381a169d0f9fa` / tree `877399b5e3df18d5d5ee00f2da1ccda339eb7e32` 已推送远端并读回；点将初始及明确 actionProposal 的后续交互均在服务端构造的用户消息元数据中保存 `permittedOperation`，供后续精确执行协调器使用。对于已有记录缺失操作或含资料且尚无 resolver 的请求，不可仅凭“EXECUTE”或用户文字猜测收费操作。本树经 orchestrator `:chat:jia-chat-service:chatDeliberation` **23 classes / 112 tests，0 failure/error/skip**，日志 `/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/evidence/u2-intent-snapshot/gradle-187fd535-attempt1.log`，key `7c527babc61e9cc3ce65a0a4f097526691dcbd12cd3e04a2f27f10d12bd886ee`。

Web feature commit `afc4fda8419c20987ef39af9099c30f226ccc005` / tree `73ebdf535162e656cccb285e4a1bd168b4f368e7` 已推送远端并读回。V2 UI 默认关闭，只在服务端能力声明与已持久化 `EXECUTE` step、`PLANNING` 状态一致时展示规划；fast CHAT 既有 `requestRevision=1` 不能作为 v2 标识，故无 proposal 的新旧 CHAT 均沿用原议事 UI，不将文字当作“画鸟完成”。主线程复跑 Mocha 定向 UI/parts/conversation **60 passing**（`evidence/web-multimedia-ui-afc4fda-corrected.log`）；Owner 另有包含会话回归的 93 passing。Web 仅前端单测，不代表实际 API 适配、真实 asset/消息/授权或浏览器验收。

当前两个 feature flags、执行及发布均未开启。Chat request 尚无持久可信 v2 CHAT 标识；Web 尚未对接有授权的媒体目录/outputId 发现，Agent native START/fence 新候选仍在 Owner 精确树复测。先把完整来源/能力/费用/真实资产打通，再合组件 develop、按版本发布与浏览器验收，不能将此开发 pin 当产品接受。
