# CYF 项目方案功能与实现完整度 Checklist

> 审计日期：2026-07-18  
> 审计范围：审计开始时仓库内除本 checklist 外的 **82 份源 Markdown**，包括规则、README、设计、规格、接口、计划、运维、交付、变更记录、美术生成记录和代码级说明。  
> 核验方式：逐文件登记 + 功能/约束提取 + 源码精读 + Controller/Service/DAO/实体链路检查 + 接口逐端点匹配 + 计划 Task 逐项核验 + 现有测试执行。

## 1. 完整度口径

| 等级 | 分数 | 判定口径 |
| --- | ---: | --- |
| ✅ 完整 | 90-100% | 主链路、异常处理和自动化验证均已落地，可直接使用 |
| 🟡 基本完整 | 70-89% | 主链路已落地，但存在测试、边界、运营化或部分子能力缺口 |
| 🟠 部分实现 | 40-69% | 有模型、接口或局部实现，但尚未形成完整可交付闭环 |
| ❌ 未实现 | 0-39% | 仅文档、占位或极少量代码，不能视为功能完成 |

说明：实施计划中的 checkbox 大量未回填，不能代表真实进度。本清单以当前代码和测试结果为准。

### 严格审计附件

| 审计层 | 覆盖量 | 文档 |
| --- | ---: | --- |
| Markdown 逐文件覆盖 | 82/82 | `docs/project-markdown-coverage-matrix.md` |
| 接口文档逐端点覆盖 | 381/381 | `docs/project-api-endpoint-audit.md` |
| 实施计划 Task/Phase 覆盖 | 81/81 | `docs/project-plan-task-audit.md` |

上述三份附件是本 checklist 的组成部分。主表负责跨文档去重后的产品功能完整度，附件负责证明没有遗漏任何源 Markdown、接口端点或计划 Task。

## 2. 方案文档归并结果

| 方案域 | 主要文档 | 功能与概设摘要 | 归并结论 |
| --- | --- | --- | --- |
| Web 应用总规 | `web/docs/specs/app-spec.md` | Chat、聚义厅、Task、Phrase、Vote、Gift、ShortLink、OAuth、路由、状态管理、HTTP 封装和非功能要求 | 作为前端通用功能基线 |
| 聚义厅业务协作 | `docs/juyiting-feature-guide.md`、`docs/juyiting-collaboration-implementation-plan.md`、`api/docs/changes/juyiting/specs/juyiting/spec.md` | Agent 地图/名册、显式点将、传令上下文、悬赏、讨论、人格、状态与会话 | 当前协作主链路已落地 |
| 聚义厅沉浸舞台 | `docs/superpowers/specs/2026-06-29-juyiting-high-immersion-ui-design.md`、`docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | melonJS、TMX 地图、人物动画、热点、DOM 降级 | 已被后续统一设计吸收，主体已落地 |
| 聚义厅场景迁移 | `web/docs/superpowers/specs/2026-07-01-juyiting-melonjs-scene-design.md`、对应 migration plan | 镜头、缩放、输入、Canvas 主舞台、点击路由 | 已落地并有回归测试 |
| 聚义厅模块化美术 | `web/docs/superpowers/specs/2026-07-04-juyiting-modular-layer-assets-design.md`、对应 assets plan | 模块化场景图层、资源命名、透明通道和运行时契约 | 资源及门禁已落地，设计文档本身过短 |
| 聚义厅移动交互 | `web/docs/superpowers/specs/2026-07-09-juyiting-mobile-map-interaction-design.md` | 横竖屏、软键盘、触摸手势、面板、加载、超时和降级 | 已并入 Camera/Input 实现 |
| 聚义厅 NPC 仿真 | `web/docs/superpowers/specs/2026-07-10-juyiting-interaction-and-npc-simulation-design.md` | TMX 内容管线、寻路、岗位、行为队列、多人移动、精灵标准、Debug | Phase 1 基本完成，Phase 2 未完整完成 |
| 聚义厅统一设计 | `web/docs/superpowers/specs/2026-07-11-juyiting-unified-map-and-agent-simulation-design.md`、统一 rollout 与五份 phase plan | 前后端场景契约、REST/SSE、A*、恢复、Phase 回报、多人仿真和性能门禁 | 当前最权威设计基线 |
| 后端总规 | `api/docs/specs/jia-api-project-spec.md`、`jia-api-optimization-spec.md`、`jia-api-interface-spec.md` | 多模块 Gradle 架构、分层、统一响应、优化方向、接口索引 | 模块结构已形成，部分优化目标未闭环 |
| 后端模块规格 | `api/docs/specs/modules/*.md` | Agent、Base、Chat、Common、DWZ、ISP、Kefu、Material、OAuth、Plugin、Point、SMS、Task、User、Workflow、WX | 按模块逐项核验，详见第 5 节 |
| 后端接口规格 | `api/docs/specs/interfaces/*.md`、`agent-scene-state-api.md` | 各模块 REST 契约和场景状态接口 | 作为 Controller/API 证据，不重复计算功能数 |
| Chat 长效记忆 | `api/docs/specs/modules/jia-chat-longterm-memory-spec.md` | 摘要、向量存储、Advisor、同步任务、清理与检索 | 主体存在，但文档已声明仍有进行中项 |
| GraalVM Native | `api/docs/changes/graalvm-native-support/*` | native-image 配置、反射收敛、错误码注册、第三方库兼容和构建验证 | 配置与部分改造已落地，原生构建闭环不足 |
| 梁山泊开放世界 | `web/src/components/world/DESIGN.md` | 世界模型、108 将、WebSocket、任务、区域、状态、Chat、AI、战斗、装备和成就 | 聚义厅相关能力已落地，高级游戏化能力多数未实现 |
| Codex WebSocket Agent | `docs/codex-ws-agent.md`、交付包 INSTALL/README | 多 Profile、热加载、重连、Codex 调用、任务回报和部署 | 客户端和后端协议主体完整 |
| 运维与发布 | `docs/DEPLOYMENT.md`、公测 readiness/runbook、Git/项目地图 | 前后端发布、Agent 运维、数据库、监控、回滚、Git 边界 | 脚本存在，监控告警与责任人仍需产品化 |
| 工程 README/代码说明 | `api/README.md`、`web/README*.md`、`web/src/composables/README.md` | 模块结构、测试、启动、HTTP 封装和开发约束 | 部分 README 已落后于当前代码 |

## 3. 总体结论

| 领域 | 综合完整度 | 结论 |
| --- | ---: | --- |
| 前端通用业务 | 86% | 页面和主流程较完整，非聚义厅模块自动化测试明显不足 |
| 聚义厅协作业务 | 95% | 地图/名册隔离、悬赏点将、传令上下文、讨论域等核心链路完整 |
| 聚义厅场景 Phase 1 | 93% | Camera/Input、TMX、Sprite、REST/SSE、单 Agent A* 和恢复已形成纵向闭环 |
| 聚义厅场景 Phase 2 | 43% | 多 Agent 基础容器存在，但碰撞、预约、排队、规模性能门禁尚未完整落地 |
| 后端业务模块 | 84% | 多数模块具备 Controller-Service-DAO-Entity 链路，少数规格超前或测试不足 |
| Codex WebSocket Agent | 92% | 多 Profile、热加载、重连、消息协议和任务回报均有实现 |
| 梁山泊开放世界总体愿景 | 58% | 聚义厅/Agent/任务/区域已实现，战斗、装备、成就未形成业务模块 |
| 运维、发布与工程说明 | 83% | 部署脚本和公测门禁存在，文档漂移及监控告警自动化不足 |
| 基础设施与 Native | 68% | 通用基础较成熟，GraalVM 仍缺真实 native build 与第三方兼容验收 |
| **项目综合** | **80%** | 严格纳入全部 Markdown 后，高级开放世界、Phase 2、Native、Workflow 测试和运维自动化拉低总分 |

## 4. 前端功能 Checklist

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| WEB-01 | Chat 会话列表、创建、切换、删除 | `web/src/components/chat/`、Chat store 与会话 API 已接入 | ✅ 95% | 增加真实后端 E2E 与会话并发切换测试 |
| WEB-02 | Chat 流式消息与停止生成 | `Chat.vue` 使用流式请求并处理 SSE/文本块 | ✅ 92% | 统一流式协议解析，移除组件内重复解析逻辑 |
| WEB-03 | Chat Agent 能力选择与上下文 | `ChatCapabilities.vue`、Agent store 已接入 | 🟡 88% | 增加能力不可用、Agent 离线和权限边界测试 |
| WEB-04 | Task 日历视图与日期筛选 | `TaskIndex.vue`、`CalendarPanel.vue`、`TaskListPanel.vue` 已实现 | ✅ 92% | 增加跨月、时区和大量任务性能测试 |
| WEB-05 | Task 创建、周期类型、更新删除 | `TaskAdd.vue` 与 task API 已覆盖主要操作 | 🟡 88% | 将周期枚举集中管理并补表单契约测试 |
| WEB-06 | Task 详情与历史记录 | `TaskDetailDialog.vue`、`TaskHistory.vue` 已存在 | 🟡 85% | 补历史分页、失败重试和权限测试 |
| WEB-07 | Phrase 随机语录与复制 | `Phrase.vue` 已实现随机读取和复制 | ✅ 92% | 增加 Clipboard API 失败降级测试 |
| WEB-08 | Phrase 点赞/踩、添加、反馈 | Phrase API、`PhraseAddDialog.vue`、`PhraseFeedbackDialog.vue` 已接入 | 🟡 88% | 当前无专项前端测试，应补交互和防重复提交测试 |
| WEB-09 | Phrase 打赏与微信支付 | tip/wx API 已接入 `Phrase.vue` | 🟡 80% | 补支付取消、重复回调和订单状态核验 |
| WEB-10 | Vote 随机题目、提交、结果反馈 | `VoteTick.vue` 与 vote API 已实现 | 🟡 85% | 当前无前端专项测试，补积分奖励与重复答题规则 |
| WEB-11 | Gift 列表、详情和库存展示 | `GiftList.vue` 已实现 | 🟡 88% | 补库存并发、空商品和图片失败状态 |
| WEB-12 | Gift 积分/微信支付 | `GiftPay.vue` 对接 gift/wx API | 🟡 82% | 增加支付幂等、库存锁定和失败恢复闭环 |
| WEB-13 | Gift 历史订单 | `OrderList.vue` 与路由已实现 | 🟡 84% | 补分页、订单状态筛选与自动刷新 |
| WEB-14 | ShortLink 生成与还原 | `ShortLink.vue`、DWZ API 已接入 | ✅ 90% | 增加恶意 URL、协议白名单与失败提示测试 |
| WEB-15 | ShortLink 二维码与有效期 | 页面具备二维码/期限交互，但契约验证较弱 | 🟡 78% | 将有效期能力与后端字段做端到端契约测试 |
| WEB-16 | OAuth2 PKCE 登录与回调 | router callback、API store token 交换已实现 | 🟡 82% | 补 state/nonce 校验、刷新令牌和回调错误页 |
| WEB-17 | 用户资料、消息中心、帮助中心 | 对应页面和路由存在 | 🟡 75% | 这些能力未在总规中充分细化，补规格和专项测试 |
| WEB-18 | 微信公众号管理 | `WxMpManager.vue` 已接入 wx API | 🟡 78% | 补菜单、模板、签名配置的契约与权限测试 |
| WEB-19 | Pinia 状态、HTTP 封装、统一 API 工厂 | `stores/`、`useHttp.js` 已形成公共层并有基础测试 | ✅ 90% | 拆分过大的 `useHttp.js`，统一错误码与取消语义 |
| WEB-20 | PWA 与本地缓存策略 | 存在 PWA/service-worker 专项测试 | 🟡 85% | 增加版本升级、离线回退和缓存清理发布门禁 |

## 5. 聚义厅功能 Checklist

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| JYT-01 | 地图 Agent 与名册 Agent 独立数据流 | `/agent/map` 与 `/agent/roster` 分离，测试明确禁止 `/agent/active` | ✅ 100% | 保持此不变量，接口变化必须更新契约测试 |
| JYT-02 | Agent 地图展示、选择和详情 | `HallStage.vue`、melonJS 场景、选中卡片已联动 | ✅ 96% | 增加真实浏览器点击与后端状态变化 E2E |
| JYT-03 | 名册状态/能力筛选 | 状态筛选已实现，能力数据可用 | 🟡 88% | 将能力筛选做成正式 UI，并补加载/空/错状态 |
| JYT-04 | 悬赏查询、创建、状态计数和归档 | `BountyPanel.vue`、`RewardBoard.vue` 与 task API 已形成闭环 | ✅ 94% | 增加批量操作和服务端排序/筛选 |
| JYT-05 | 显式点将、推荐和自动点将 | clicked row 显式传 `agentId`，推荐与 auto-assign 已接入 | ✅ 98% | 记录推荐评分解释和人工覆盖原因 |
| JYT-06 | 厅内传令保留 Agent/任务/scene 上下文 | `useHallChatContext.js` 与会话测试覆盖 metadata | ✅ 96% | 提供用户可见的上下文摘要与发送前确认 |
| JYT-07 | 公共悬赏讨论、私聊、任务讨论隔离 | 多个 discussion panel 与 scope service 已实现 | ✅ 93% | 后端增加更严格的参与人授权测试 |
| JYT-08 | 案卷阁检索 | `LibraryPanel.vue`、`useHallLibrary.js`、`/chat/library/search` 已接入 | ✅ 90% | 补索引新鲜度、无结果解释和引用来源展示 |
| JYT-09 | 人格目录、绑定/解绑与招贤令 | `PersonaCatalogPanel.vue` 与 bind API 已实现 server/local 模式 | ✅ 91% | 增加安装状态回查、失败补偿和安全审计日志 |
| JYT-10 | 108 水浒角色映射与画像降级 | 角色元数据、PNG/atlas/SVG fallback 及测试齐全 | ✅ 96% | 增加资源体积预算和视觉回归基线 |
| JYT-11 | melonJS 主舞台、热点和人物点击 | DOM 场景主体已移除，Canvas 场景负责地图和人物 | ✅ 96% | 清理仍保留的历史组件/资源，降低维护面 |
| JYT-12 | Camera 变换、预设、缩放、复位和 resize 保焦点 | `game/camera/` 类型化模块与测试完整 | ✅ 96% | 增加低端移动设备实机回归 |
| JYT-13 | Pointer/Touch/Keyboard 输入和交互锁 | `game/input/`、面板锁、手势分类和焦点生命周期已测试 | ✅ 95% | 增加无障碍键盘全流程和 Safari 手势验证 |
| JYT-14 | 横竖屏、软键盘、响应式面板 | 设备分类、rotation hint、viewport resize 竞态均有测试 | ✅ 94% | 建立机型矩阵并自动保存 smoke 证据 |
| JYT-15 | TMX 唯一事实源、movement schema、稳定 ID | parser、validator、edit ops、snapshot、preview 均已落地 | ✅ 97% | 将地图编辑/校验纳入 CI 必跑任务 |
| JYT-16 | Sprite manifest、尺寸/格式门禁与降级 | loader/validator/manifest 及 PNG 严格校验测试齐全 | ✅ 96% | 扩展六个最终 persona 的正式精灵资源 |
| JYT-17 | 后端租户隔离场景快照 | Agent scene DTO/DAO/service/controller 与 scope 测试存在 | ✅ 94% | 增加数据库迁移版本和生产数据清理策略 |
| JYT-18 | SSE 增量事件、断线续传和 resync | broker、前端 cursor、gap 检测、轮询降级已实现 | ✅ 93% | 增加代理层超时、长连接容量与混沌测试 |
| JYT-19 | 单 Agent A*、命令优先级、slot 和到达/阻塞 | pathfinder、queue、allocator、engine 测试齐全 | ✅ 95% | 将仿真 feature flag 从试验态推进到默认启用 |
| JYT-20 | 刷新/重连后的运动恢复 | backend adapter 按路径长度和时间恢复，边界测试完整 | ✅ 93% | 加入跨版本地图恢复和过期命令监控 |
| JYT-21 | Phase arrived/blocked 幂等回报 | 前后端 phase API、重试与幂等模型已存在 | ✅ 90% | 增加失败死信、后台补偿和可观察告警 |
| JYT-22 | sceneDebug 安全聚合 | debug aggregator、桥接和全局清理测试已存在 | 🟡 88% | 增加敏感字段静态扫描和线上采样导出 |
| JYT-23 | Phase 1 发布开关与回滚模式 | `VITE_JUYITING_SIMULATION_ENABLED` 默认关闭，可回退静态模式 | 🟡 76% | 明确灰度比例、默认开启日期和回滚判据 |
| JYT-24 | 24 人可见、12 人移动的多人仿真 | 引擎可容纳多 agent，但缺完整碰撞/预约/排队/重规划闭环 | 🟠 48% | 按 Phase 2 plan 实现 reservation table、碰撞和 queue slot |
| JYT-25 | 多人性能预算、Android 30 FPS 和 long-task 证据 | 有 debug 指标基础，未发现完整设备性能证据链 | ❌ 30% | 建立可重复性能场景、设备采样和发布阻断阈值 |

## 6. 后端模块 Checklist

| ID | 模块 / 功能特性 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| API-01 | Agent 注册、列表、地图、详情、状态、能力和统计 | Controller/Service/Runtime DAO/DTO 完整，服务测试较丰富 | ✅ 94% | 对外 API 增加限流、审计和更细粒度权限 |
| API-02 | Agent Persona 目录、绑定、解绑和详情 | Persona/Binding 实体、DAO、接口和部署模式均存在 | ✅ 93% | 增加绑定状态机与安装任务可观测性 |
| API-03 | Agent 任务创建、搜索、分配、推荐、报告、笔记、归档 | Task meta/note 全链路实现并有聚义厅调用 | ✅ 94% | 增加任务事件表和状态转换约束 |
| API-04 | Agent 能力评估、对比、历史和统计 | Evaluation/Comparison DAO、Service 和 DTO 已实现 | ✅ 90% | 增加评估模型版本与可解释评分 |
| API-05 | Agent 对话模板与水浒台词 | DialogueTemplate 实体/DAO/API 已存在 | 🟡 85% | 模板版本化、审核和多语言支持 |
| API-06 | Base 字典、多语言和缓存 | Dict Controller/Service/DAO 及测试存在 | ✅ 92% | 增加缓存一致性和批量接口测试 |
| API-07 | Base 系统日志 | Log Service/DAO/Entity 存在，但 API 暴露和分析能力弱 | 🟡 72% | 增加查询 Controller、索引、留存与脱敏策略 |
| API-08 | Base 通知公告 | Notice Service/DAO/Entity 存在，发布/订阅闭环不充分 | 🟡 70% | 增加 Controller、订阅通道和阅读状态 |
| API-09 | Chat 会话、消息、流式响应与事件 | Chat Controller、会话/消息服务、事件 broker 与测试较完整 | ✅ 92% | 统一 SSE/WebSocket 事件模型和限流策略 |
| API-10 | Chat 聚义厅动作分发与 Agent WebSocket | Dispatcher、mailbox、announcement、WebSocket 安全测试已存在 | ✅ 90% | 补跨节点 mailbox、一致性和重放保护 |
| API-11 | Chat 长效记忆、摘要、向量检索和定时同步 | Advisor、Repository、Summary、Job 已实现；文档仍列进行中项 | 🟡 78% | 完成 ES 索引自动创建、热更新和降级策略 |
| API-12 | Common 基础实体、DAO、日期、缓存、异常和测试支持 | 通用模块结构成熟且测试数量多 | 🟡 88% | 收敛反射、空返回和历史工具类技术债 |
| API-13 | DWZ 短链生成、还原、管理和访问 | Controller/Service/DAO 完整且有测试 | ✅ 92% | 增加 URL 安全策略、访问统计和过期清理 |
| API-14 | ISP 品牌、车辆、第三方查询和同步 | Car/Isp/Cms/Dns/Ldap/File/Orche 多服务已存在 | 🟡 80% | 规格与现有扩展能力不一致，应重写模块文档并补契约测试 |
| API-15 | Kefu 消息、订阅和 FAQ | Controller 与多 Service/DAO 实现齐全 | 🟡 84% | 增加会话级模型、实时通道和智能 FAQ 质量评估 |
| API-16 | Material 媒体、新闻、短语、投票、提示和 PV | 六个 Controller、Service/DAO/实体链路完整 | ✅ 93% | 增加文件安全扫描、内容审核和更系统的 service 测试 |
| API-17 | OAuth 服务端、客户端、资源服务器和第三方登录 | 多 starter、配置、Controller、client/service 均存在 | 🟡 76% | 修复 resource `AuthenticationController` 空返回，补协议级集成测试 |
| API-18 | Gradle Plugin 依赖管理 | 独立 plugin 模块和共享依赖插件存在 | ✅ 90% | 增加 TestKit 插件行为测试和版本兼容矩阵 |
| API-19 | Point 账户、收入、消费、记录与礼品兑换 | Point/Gift Controller、Service、DAO 与测试较完整 | 🟡 88% | 增加账本幂等、并发扣减和对账机制 |
| API-20 | SMS 单发、群发、模板、验证码、记录 | 多供应商实现和 Controller 存在；Aliyun 部分方法明确不支持 | 🟡 72% | 统一供应商能力矩阵、状态回执和模板审核流程 |
| API-21 | Task 周期任务、调度、日志和即时执行 | Task/Job Controller、Service、DAO 与测试存在 | 🟡 88% | 增加误触发保护、分布式锁和执行日志查询闭环 |
| API-22 | User 用户、角色、组织、分组、权限和消息 | 七个 Controller、多 Service/DAO、实体与 15 个测试 | ✅ 92% | 增加权限变更审计、缓存失效和批量导入回滚 |
| API-23 | Workflow 定义、部署、实例、任务、变量和批注 | Workflow Controller/Service 覆盖面广，但模块无专项测试且存在 null 分支 | 🟡 74% | 优先补 Camunda 集成测试、异常语义和变量/批注契约 |
| API-24 | WX 公众号、支付、授权、模板消息和用户管理 | WxMp/WxPay Controller、多 Service/DAO 与测试存在 | 🟡 84% | 增加支付通知幂等、退款/对账和公众号菜单测试 |

## 7. 基础设施与非功能 Checklist

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| INF-01 | GraalVM native-image 配置文件 | common starter 已包含 reflect/resource/native-image 配置 | 🟡 78% | 配置应按模块拆分并自动验证资源完整性 |
| INF-02 | 动态类加载与反射收敛 | `ClassUtil` 有 native mode，但多处仍使用 `Class.forName` | 🟠 58% | 替换剩余动态加载或补 RuntimeHints/显式注册 |
| INF-03 | 错误码零反射注册 | annotation processor 已实现，但 `ErrCodeHolder` 仍反射加载生成类 | 🟠 65% | 生成稳定入口或 ServiceLoader，彻底消除启动反射 |
| INF-04 | Native 第三方库兼容 | 文档覆盖 MyBatis/Druid/Redis/Camunda/OAuth，未发现完整 native 验收证据 | 🟠 50% | CI 增加真实 nativeCompile/nativeTest 和启动 smoke |
| INF-05 | 前端自动化测试 | 全量执行通过 `473 passing`，聚义厅覆盖非常充分 | ✅ 94% | 为 Phrase/Vote/Gift/DWZ/WX 增加同等级专项测试 |
| INF-06 | 后端自动化测试 | 核心模块有测试，但 Workflow 为 0，部分模块主要依赖 starter 测试 | 🟡 78% | 建立模块级最低测试门禁和 Controller 契约测试模板 |
| INF-07 | 文档与代码路径准确性 | 多份旧文档仍引用 `web/jia-web-kit`、Windows 路径和未回填 checkbox | 🟠 60% | 统一文档基准路径并给历史方案加 superseded 标识 |
| INF-08 | 发布与回滚 | 前后端部署脚本、runbook 和公测门禁存在 | 🟡 86% | 将 smoke、回滚和数据库迁移检查自动化为流水线 |
| INF-09 | 可观测性 | 日志、sceneDebug、部分统计存在，跨模块指标体系不足 | 🟡 70% | 建立统一 tracing、业务指标、错误预算和告警面板 |
| INF-10 | 安全与权限 | OAuth、WebSocket 安全测试和租户 scope 已有基础 | 🟡 76% | 补 API 权限矩阵、文件上传安全、URL 安全和审计日志 |

## 8. 梁山泊开放世界设计 Checklist

来源：`web/src/components/world/DESIGN.md`。该文档包含早期开放世界愿景，不能全部等同于当前聚义厅范围。

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| OWD-01 | 世界 Schema、区域和地图模型 | TMX regions、hotspots、movement schema 和 HallScene 已形成地图模型 | ✅ 92% | 将世界 Schema 正式版本化并区分业务 ID/TMX stable ID |
| OWD-02 | Agent 注册、上线、下线和运行状态 | Agent Runtime、WebSocket 注册/状态、状态监控均已实现 | ✅ 94% | 增加事件时间线和状态审计 |
| OWD-03 | 108 将初始配置和 Persona | 108 Persona seed、前端角色元数据和画像 fallback 已实现 | ✅ 96% | 增加配置版本、审核和资源完整性门禁 |
| OWD-04 | WebSocket 世界通信协议 | Agent WebSocket 支持注册、状态、消息、任务和能力查询 | ✅ 92% | 统一协议版本和兼容性测试 |
| OWD-05 | 任务发布、接取、分配、执行和回报 | Agent Task 与通用 Task 主流程存在，聚义厅显式点将完整 | ✅ 92% | 增加依赖任务、多 Agent 协作和回滚 |
| OWD-06 | 区域系统和 Agent 区域移动 | TMX Region、A*、slot 和 scene state 已实现 Phase 1 | 🟡 86% | 完成多人区域容量、碰撞和排队 |
| OWD-07 | 聚义厅实时聊天和私密/公共讨论 | Chat/Conversation scope/WebSocket/讨论面板已实现 | ✅ 93% | 增加参与人权限与跨节点实时一致性 |
| OWD-08 | Agent AI 对话集成 | Chat LLM、Agent direct message、Codex Agent 执行链路存在 | 🟡 88% | 增加模型失败降级、成本和提示版本治理 |
| OWD-09 | 世界地图完整开放探索 | 当前产品聚焦聚义厅单场景，不是多区域开放世界 | 🟠 45% | 明确是否继续该产品方向；若继续，先定义世界路由和持久化 |
| OWD-10 | 战斗系统 | 未发现独立战斗领域模型、服务、页面或测试 | ❌ 10% | 作为独立产品 Epic 重新规格化，不应继续留在已实现设计中 |
| OWD-11 | 物品、背包和装备系统 | Gift/Point 不能替代游戏物品、背包和装备领域 | ❌ 10% | 定义 Item/Inventory/Equipment 模型、交易和持久化 |
| OWD-12 | 成就系统 | 未发现成就实体、规则引擎、API、页面或测试 | ❌ 5% | 定义成就事件源、规则、奖励和展示 |

## 9. Codex WebSocket Agent Checklist

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| CWA-01 | WebSocket API Key 连接与握手能力声明 | 后端 handler、安全测试和客户端连接实现存在 | ✅ 94% | 增加协议版本字段和密钥轮换 |
| CWA-02 | Agent 注册、状态和心跳 | 双端支持 register/status/ping/pong | ✅ 96% | 增加超时判定和离线原因指标 |
| CWA-03 | 厅内传令与流式回复 | `agent_direct_message`、`agent.message`、delta 已实现 | ✅ 93% | 增加消息顺序号、去重和断线补发 |
| CWA-04 | 任务委派、执行和回报 | task assigned/event/report 与 Codex 子进程调用存在 | ✅ 92% | 增加任务取消、隔离和输出大小限制 |
| CWA-05 | 能力名册查询 | capability lookup/index 双端实现且有测试 | ✅ 92% | 增加能力版本和缓存失效 |
| CWA-06 | 多 Profile 独立 CODEX_HOME 与消息路由 | profile 配置、target 路由和 default profile 已实现 | ✅ 94% | 增加 profile 级限流和资源配额 |
| CWA-07 | Profile 热加载和错误配置保留旧状态 | `watchFile`、periodic reload、signature 和安全切换存在 | ✅ 93% | 增加客户端自动化测试和原子配置写入工具 |
| CWA-08 | 指数退避重连与优雅关闭 | 1-30 秒退避、30 分钟窗口、SIGTERM/SIGKILL 清理存在 | ✅ 92% | 增加 systemd watchdog 和异常退出告警 |

## 10. 运维、发布与文档约束 Checklist

| ID | 功能特性 / 概设 | 代码核验 | 完整度 | 后续建议 |
| --- | --- | --- | ---: | --- |
| OPS-01 | 前端 Flow 扫描、测试、构建和发布 | `4403172 / cyf-web-kit` Run 86 已完整成功 | 🟡 92% | 标准 YAML 化、改用 `npm ci`，补 `develop` CI-only |
| OPS-02 | 后端 Flow 测试、`bootJar`、不可变制品和部署 | `5260799 / cyf-api-kit-ci` Run 13 已完整成功 | 🟡 92% | 版本化 ticket 刷新 controller，补 CI-only |
| OPS-03 | Codex Agent 启停和状态管理 | `/home/isp/bin/codex_ws_agent_start.sh` 与安装文档存在 | ✅ 92% | 统一 systemd 与脚本的单一运维入口 |
| OPS-04 | 数据库迁移和回滚纪律 | migration 文件与部署注意事项存在 | 🟡 78% | 使用 Flyway/Liquibase 或统一 schema version 表 |
| OPS-05 | 聚义厅 preflight、UI smoke、Agent smoke | package scripts 和测试脚本均存在 | ✅ 92% | 纳入 CI/CD，避免依赖人工顺序执行 |
| OPS-06 | 发布窗口、责任人和检查清单 | runbook 有字段和 preflight 文档校验 | 🟡 75% | 填写实际责任人、审批和通知机制 |
| OPS-07 | 监控与告警确认 | runbook 有要求，仓库内未见完整指标面板/告警配置 | 🟠 55% | 建立可执行监控 URL、阈值和告警接收人 |
| OPS-08 | 自动回滚与发布后观察 | 有手工回滚步骤，自动判定和自动回滚不足 | 🟡 68% | 定义错误率/健康检查触发的自动回滚 |
| OPS-09 | 根协调仓和 api/web submodule | 根协调仓追踪 `api/`、`web/` submodule，`gitw` 存在 | ✅ 100% | 保持项目地图与实际仓库一致 |
| OPS-10 | README、开发命令和路径准确性 | 多数命令可用，但仍存在 Windows/旧目录/MCP/版本漂移 | 🟠 62% | 统一 Linux 当前路径并自动生成模块/脚本清单 |

## 11. 优先优化路线

### P0：阻断性缺口

- [ ] 完成聚义厅 Phase 2：多人碰撞、预约、排队、阻塞重规划和规模化性能门禁。
- [ ] 修复普通巡逻的同步重置：场景展示状态更新不得重置角色的路线进度、当前位置或移动目标；补齐“随机台词期间持续巡逻”的回归测试。
- [ ] 在上述普通巡逻修复验收后，把 `VITE_JUYITING_SIMULATION_ENABLED` 从长期实验开关升级为有灰度计划的正式能力，并完成生产观测、灰度与回滚判据。
- [ ] 修复 OAuth resource controller 空返回及关键认证协议测试缺口。
- [ ] 为 Workflow 增加可运行的集成测试，清理关键 `return null` 分支。
- [ ] 建立真实 GraalVM native build + startup smoke，验证第三方依赖而非只提交配置文件。

### P1：质量与一致性

- [ ] 为 Phrase、Vote、Gift、DWZ、WX 增加前端专项测试和端到端契约测试。
- [ ] 统一 Chat SSE/WebSocket、聚义厅事件和错误码模型。
- [ ] 为支付、积分、任务分配、场景 Phase 回报增加幂等与并发测试。
- [ ] 将 TMX/Sprite 校验、前端测试、后端模块测试纳入固定 CI 门禁。
- [ ] 清理旧路径、Windows 命令、未回填 checkbox，并标记被统一设计取代的历史方案。

### P2：产品化增强

- [ ] 建立全项目可观测体系：trace、在线 Agent、任务吞吐、失败率、SSE 重连、仿真 FPS。
- [ ] 增加权限矩阵、审计日志、文件/URL 安全策略和敏感信息扫描。
- [ ] 对 Agent 推荐、能力评估和长期记忆提供可解释结果与版本治理。
- [ ] 补多语言、无障碍、低端移动设备和弱网验收矩阵。
- [ ] 明确开放世界高级功能的产品决策：正式立项战斗/装备/成就，或将其标记为取消/非目标。

## 12. 本次验证记录

- [x] 前端全量测试：`cd web && npm run test`，结果 `473 passing`。
- [x] 前端源码、路由、组件、composable、game 模块和测试目录逐项核验。
- [x] 后端各业务模块 Controller、Service、DAO、Entity 和测试分布核验。
- [x] 聚义厅前后端 Scene State、SSE、A*、命令队列、slot、恢复与 Phase 回报精读。
- [x] GraalVM native 配置、错误码处理器和剩余动态类加载点核验。
- [x] 后端组合测试：`bash gradlew :agent:jia-agent-service:test :chat:jia-chat-service:test :task:jia-task-service:test :user:jia-user-service:test :workflow:jia-workflow-service:test`，结果 `BUILD SUCCESSFUL`；Workflow 测试任务为 `NO-SOURCE`。
- [x] 82 份源 Markdown 全部登记到逐文件覆盖矩阵。
- [x] 381 个接口文档端点全部关联到当前 Controller/处理方法或映射路径。
- [x] 81 个实施计划 Task/Phase 全部给出代码证据、完整度和后续动作。
- [x] 补核 `web/src/components/world/DESIGN.md`，确认战斗、物品/装备和成就未完整实现。
- [x] 补核 Codex WebSocket Agent 客户端、后端 handler、交付包和部署脚本。

## 13. 审计维护规则

- 新增方案必须在本文件增加对应 checklist 项，避免方案只存在于独立文档中。
- 功能完成后必须同时补充“代码证据”和“测试证据”，仅有 Controller 或页面不计为 100%。
- 被新统一设计取代的旧方案应在标题处标记 `Superseded`，但保留历史决策背景。
- 每次大版本发布前更新完整度；分数变化必须写明新增证据或新发现缺口。
- 源 Markdown 数、覆盖矩阵路径数、接口端点数和计划 Task 数必须通过自动对账，任何差异均视为审计失败。
