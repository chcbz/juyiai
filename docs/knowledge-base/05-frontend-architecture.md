# 前端架构与调用边界

> 有效性：原有章节沿用 `BASELINE.yaml` 的 2026-08-15 静态基线，未在本轮全量复核。下方“议事 UI 组件职责”独立注明 2026-10-08 核对范围；不能据此认为全部路由、HTTP 或构建说明已更新。


## 技术组成

前端是 Vue 3 单页应用：Vite 构建、Vue Router 路由、Pinia 状态、Varlet UI、vue-i18n、PWA 工具链；聚义厅场景使用 MelonJS。Vite 使用 `@` 指向 `web/src`，生产构建按 `melonjs`、Vue、UI、Markdown、utilities 分 chunk，并可按环境变量启用压缩、旧浏览器构建与 bundle 分析。

## 页面与状态

- 路由定义：[`web/src/router/index.js`](../../web/src/router/index.js)。根路径重定向 `/juyiting`。
- App shell：[`web/src/App.vue`](../../web/src/App.vue)，负责 app bar、侧菜单、PWA 更新/安装提示和 `router-view`。
- Pinia stores：`api`（令牌及 OAuth 回调）、`agent`（Agent/任务数据）、`global`（UI shell）、`message`、`i18n`、`util`。
- 页面域：chat、Juyi Hall、通用任务、礼品/支付/订单、个人资料、消息、帮助、投票、短语、短链、微信公众号管理。

## HTTP 边界

[`web/src/composables/useHttp.js`](../../web/src/composables/useHttp.js) 是请求单入口：

1. `VITE_API_BASE_URL` 存在时为相对 URL 加前缀。
2. 默认 JSON 请求、超时 AbortSignal、可选流式读取。
3. 默认请求认证；从 `api` store 取 token 并发送 `Authorization: Bearer ...`。
4. HTTP 401 会清令牌并尝试一次重新取令牌/重试。
5. `createApi(basePath)` 生成 `taskApi`、`agentApi`、`chatApi` 等按根路径的门面。

开发服务器仅代理 `/api/**`（以及 OAuth/login 子路径）并剥离 `/api` 前缀；非 `/api` 的相对请求如何到达后端取决于部署反向代理或 `VITE_API_BASE_URL`。

## 游戏与聚义厅

`web/src/components/world/JuyiHall.vue` 是页面编排点；它组合数据、任务、会话、场景、声音、面板、命令队列、后端场景状态等 composable。`web/src/game/` 将场景划分为相机、输入、地图/TMX、遮挡、实体、模拟、sprite 与 debug 子域；`HallScene.js` 为核心场景之一。

角色肖像解析集中在 `useWaterMarginRoles.js`，角色元数据集中在 `constants/juyiting.js`。这两处是人物显示/名称/风格变更的稳定入口。

<a id="hall-discussion-composition"></a>
## 议事 UI 组件职责（2026-10-08 局部核对）

源码基线：Web `75766a3b78c2e552ef448e924a813ed2dfc7ecd4`（本次读取的本地 `origin/develop` 引用，非实时远端/线上证明）。核对 `src/components/juyiting/ChatPanel.vue`、`HallChatComposer.vue`；控件接线在前两者核对，语音内部状态机未在本轮复核。

| 层 | 责任 | 不应混入 |
| --- | --- | --- |
| `JuyiHall.vue` 页面编排 | 将业务上下文连接到议事面板；页面样式入口 | 不因布局调整重写身份/任务状态 |
| `ChatPanel.vue` | 话头工具栏、会话展示、资料选择器状态及 Composer 事件转接 | 不复制输入/语音控件实现 |
| `HallChatComposer.vue` | 草稿输入、提及、更多/资料/发送按钮、materials 插槽与语音控件挂载 | 不凭点击或前端展示判定后台任务完成 |
| `HallVoiceControls.vue` 接线 | Composer 通过 recording-target 放置录音按钮，通过 settings-visible 控制设置；voice-apply 向上传递 | 不把菜单关闭当成语音业务终止 |

布局与资料选择器解耦：`materials` 插槽在更多菜单外，`open-materials` 由 ChatPanel 的 `toggleMaterialPicker` 处理；语音设置与进行中反馈仍由独立条件控制。具体行为、禁用边界与回归入口见 [聚义厅专题](06-juyiting-end-to-end.md#hall-discussion-ui)。

**2026-10-09 输入区轻量化补充**：核对 Web `3e9b0aff365c25faab524e905b7c2f1aff53c3f1`，仅覆盖 `HallChatComposer.vue`、`ChatPanel.vue` 的本次差异。Composer 统一草稿派生值和目标标签映射，移除无消费者的 `open-workspace` 事件/转发及重复、未使用样式；百宝箱入口仍由 ChatPanel 资料选择器直接发出 `open-workspace`。不改变协议、身份、输入锁、语音状态机或线上版本。其余本节保留原基线。

**2026-10-09 会话协议收敛补充**：核对 Web `e3afb42dc69272f43699c2c423b06da7539f0671`，范围仅 `useHallConversation.js`、`JuyiHall.vue`、ChatPanel 与公议/密议/悬赏面板的发送和取消接线。发送统一当前 durable 契约，不再能力失败时切换旧 payload；面板只转发 `cancel-deliberation` 的明确 turn/allPending 目标，移除旧 `/stop_stream` 接线。普通文本响应、SSE 和只读恢复不是旧发送协议，仍保留。恢复与幂等边界见 [聚义厅专题](06-juyiting-end-to-end.md#hall-current-protocol)。这是源码基线，不代表生产发布。

**2026-10-09 面板转发与发送入口补充**：核对 Web `74dffae9379c8259283aa653304484981a66ace7`，范围仅三种议事面板、静态 `discussionPanelContract.js` 和 `useHallConversation.js` 的本次差异。公共 props/events 声明只维护一份，不新增组件层；公议默认值显式覆盖，密议保留上下文副标题，悬赏过滤自身业务字段后向 ChatPanel 传递输入，typed结果/恢复及任务完成事件仍在原面板。草稿直接按 props 下传、update事件上送，不保留额外草稿代理或逐字段映射。发送同步校验复用原忙碌状态，异步身份/作用域检查不变；无消费者的 `canCancelDurable` 已删除，取消仍使用 `durableCancelTarget`。其余职责与核对基线不变，不代表线上发布。

历史来源：[1.0.6 UI 收口导航](../../specs/juyiting-ui-baseline-20261006/README.md)。该版本的“不改业务逻辑”只描述当次 UI patch，不能套用到后续源码；本次核对版本已有额外完成态锁定逻辑。

### 局部源码补充：事项筛选表头（2026-10-09）

核对范围仅 `BountyPanel.vue`、`BountyActionIcon.vue` 与 `JuyiHall.vue` 的事项表头；基线 commit `5eb117fa3f7a68e9af26ea62d33e5329d603634e` 加本地未提交修复，不代表线上状态，其余章节保留原核对基线。

- 嵌入事项页表头仅含榜号查询、本领筛选与刷新，三列等高布局。表头不再提供重复的“提出需求”按钮。
- 其他创建入口仍经 `openDefaultRequirementCreate` 调用 `BountyPanel.openCreateRequirement`；共享表单、资料选择、原请求恢复与身份隔离仍有活跃调用，不应随表头按钮删除。
- 局部实现和轻量检查边界见 `docs/implementation/handoffs/BOUNTY-TOOLBAR-20261009.md`；未取得本候选正式 Flow 或上线证据。
