# CYF 全量 Markdown 覆盖矩阵

> 审计日期：2026-07-18  
> 冻结范围：审计开始时仓库内除主 checklist 外的 **82 份源 Markdown**。  
> 每份文件均必须有唯一 DOC ID、内容摘要、代码/仓库证据、完整度和后续建议。纯规则、历史记录、废弃说明也纳入，判定其一致性或“无需实现”。

## 覆盖统计

- 源 Markdown：**82/82 已登记**。
- 接口端点：详见 `docs/project-api-endpoint-audit.md`。
- 实施计划 Task：详见 `docs/project-plan-task-audit.md`。

## 逐文件 Checklist

| DOC ID | Markdown 文件 | 类型 | 功能、概设或约束摘要 | 代码/仓库证据 | 完整度 | 建议 |
| --- | --- | --- | --- | --- | --- | --- |
| DOC-001 | `AGENTS.md` | 说明/约束 | 仓库工作规则、快速迭代、聚义厅不变量、验证和编辑纪律 | 当前目录结构、测试命令及数据边界均已核对 | ✅ 完整 100% | 持续保持为最高优先级工作约束 |
| DOC-002 | `api/README.md` | README | 微服务框架、技术栈、模块结构、用户/OAuth/Workflow/Base/Kefu/Material/SMS/Task/DWZ/ISP/WX/MCP | 现有 Gradle 多模块与大部分业务目录；README 声明的 `api/mcp/` 当前不存在 | 🟡 基本完整 82% | 更新版本、Java/Gradle要求并移除或补回 MCP 模块 |
| DOC-003 | `api/docs/changes/graalvm-native-support/design.md` | 设计/规格 | Native Image 反射、动态加载、WebSocket、MyBatis、错误码和迁移设计 | native 配置与 annotation processor 已有，但仍存在 Class.forName | 🟠 部分实现 62% | 完成真实 native build 并消除剩余反射 |
| DOC-004 | `api/docs/changes/graalvm-native-support/proposal.md` | 说明/约束 | 引入 GraalVM 原生镜像能力并修改动态加载点 | 配置和部分代码改造存在，构建能力未闭环 | 🟠 部分实现 68% | 补 nativeCompile/nativeTest/启动 smoke |
| DOC-005 | `api/docs/changes/graalvm-native-support/specs/generated-errcode-registry-example.md` | 设计/规格 | 错误码注解、处理器、生成 Registry 和启动注册示例 | `ErrorCodeModule`、`ErrCodeProcessor`、多模块注解存在；Holder 仍反射加载 Registry | 🟡 基本完整 70% | 改成静态入口或 ServiceLoader |
| DOC-006 | `api/docs/changes/graalvm-native-support/specs/native-image-config/spec.md` | 设计/规格 | reflect/resource/WebSocket/proxy 配置及验收标准 | common starter 配置文件存在，未验证完整 native acceptance | 🟠 部分实现 68% | CI 执行真实原生镜像验收 |
| DOC-007 | `api/docs/changes/graalvm-native-support/tasks.md` | 实施计划 | Native 配置、代码改造、构建、测试和第三方库五阶段任务 | 文档 Phase 1/2 多项勾选，但源码仍有反射；Phase 3-5 多项未完成 | 🟠 部分实现 62% | 按实际证据重置 checkbox 并完成构建与第三方验证 |
| DOC-008 | `api/docs/changes/juyiting/specs/juyiting/spec.md` | 设计/规格 | 聚义厅 Agent、Persona、通信、任务、API、数据模型、数据库与 MVP | Agent/Chat/Task 主链路、WebSocket、场景状态和测试已落地 | ✅ 完整 90% | 拆出历史/当前版本并同步最新 Scene State 契约 |
| DOC-009 | `api/docs/specs/interfaces/agent-scene-state-api.md` | 接口规格 | 租户隔离快照、可续传 SSE、幂等 Phase 回报和安全错误 | 3 个端点、DTO/DAO/Service/Controller 与测试完整 | ✅ 完整 93% | 补容量、代理超时和生产 retention 验证 |
| DOC-010 | `api/docs/specs/interfaces/jia-agent-interface-spec.md` | 接口规格 | Agent 注册、状态、能力、Persona、任务、评估和对话模板；文档声明 30 个端点 | `api/agent/`、Agent Controller/Service/DAO/Tests；逐端点见 `docs/project-api-endpoint-audit.md` | ✅ 完整 94% | 补权限、审计和评分可解释性 |
| DOC-011 | `api/docs/specs/interfaces/jia-base-interface-spec.md` | 接口规格 | 字典、多语言、缓存、日志和公告；文档声明 7 个端点 | `api/base/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 82% | 补日志/公告 Controller 与订阅闭环 |
| DOC-012 | `api/docs/specs/interfaces/jia-chat-interface-spec.md` | 接口规格 | 会话、消息、流式响应、记忆和聚义厅通信；文档声明 6 个端点 | `api/chat/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 85% | 补长效记忆降级、索引初始化和跨节点一致性 |
| DOC-013 | `api/docs/specs/interfaces/jia-dwz-interface-spec.md` | 接口规格 | 短链接生成、还原、管理和访问；文档声明 7 个端点 | `api/dwz/`；逐端点见 `docs/project-api-endpoint-audit.md` | ✅ 完整 92% | 补 URL 安全、过期清理和访问统计 |
| DOC-014 | `api/docs/specs/interfaces/jia-isp-interface-spec.md` | 接口规格 | 车辆、品牌、ISP、CMS、DNS、LDAP、文件和编排服务；文档声明 61 个端点 | `api/isp/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 80% | 重写已落后于代码的模块规格并补契约测试 |
| DOC-015 | `api/docs/specs/interfaces/jia-kefu-interface-spec.md` | 接口规格 | 客服消息、订阅、FAQ 和消息类型；文档声明 11 个端点 | `api/kefu/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 84% | 补实时会话、统计和智能 FAQ 验证 |
| DOC-016 | `api/docs/specs/interfaces/jia-material-interface-spec.md` | 接口规格 | 媒体、新闻、短语、投票、提示和 PV；文档声明 39 个端点 | `api/material/`；逐端点见 `docs/project-api-endpoint-audit.md` | ✅ 完整 93% | 补内容审核、文件安全和专项服务测试 |
| DOC-017 | `api/docs/specs/interfaces/jia-oauth-interface-spec.md` | 接口规格 | OAuth 服务端/客户端/资源服务器、LDAP 和 API Key；文档声明 12 个端点 | `api/oauth/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 76% | 修复空返回并补协议级集成测试 |
| DOC-018 | `api/docs/specs/interfaces/jia-point-interface-spec.md` | 接口规格 | 积分账户、流水、消费、邀请奖励和礼品兑换；文档声明 14 个端点 | `api/point/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 88% | 补并发账本、幂等和对账 |
| DOC-019 | `api/docs/specs/interfaces/jia-sms-interface-spec.md` | 接口规格 | 短信发送、模板、记录、供应商适配和验证码；文档声明 17 个端点 | `api/sms/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 72% | 统一供应商能力并补回执/审核闭环 |
| DOC-020 | `api/docs/specs/interfaces/jia-task-interface-spec.md` | 接口规格 | 周期任务、任务明细、调度执行和日志；文档声明 12 个端点 | `api/task/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 88% | 补分布式锁、误触发保护和日志查询 |
| DOC-021 | `api/docs/specs/interfaces/jia-user-interface-spec.md` | 接口规格 | 用户、角色、组织、分组、权限和消息；文档声明 80 个端点 | `api/user/`；逐端点见 `docs/project-api-endpoint-audit.md` | ✅ 完整 92% | 补权限审计、缓存失效和导入回滚 |
| DOC-022 | `api/docs/specs/interfaces/jia-workflow-interface-spec.md` | 接口规格 | 流程部署、定义、实例、任务、变量和批注；文档声明 25 个端点 | `api/workflow/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 74% | 新增 Camunda 集成测试并清理 null 分支 |
| DOC-023 | `api/docs/specs/interfaces/jia-wx-interface-spec.md` | 接口规格 | 公众号、用户、菜单、素材、模板消息和微信支付；文档声明 57 个端点 | `api/wx/`；逐端点见 `docs/project-api-endpoint-audit.md` | 🟡 基本完整 84% | 补支付通知幂等、退款对账和公众号契约测试 |
| DOC-024 | `api/docs/specs/jia-api-interface-spec.md` | 设计/规格 | 各后端模块接口文档索引 | 接口文件均存在，逐端点结构审计见端点附件 | ✅ 完整 95% | 在 CI 中自动校验索引与 Controller |
| DOC-025 | `api/docs/specs/jia-api-optimization-spec.md` | 设计/规格 | 依赖、构建、代码质量、性能、安全、可观测和文档优化建议 | 部分 Gradle/测试/架构优化存在，统一观测与安全门禁不足 | 🟠 部分实现 68% | 把建议转成有 owner 的可执行 backlog |
| DOC-026 | `api/docs/specs/jia-api-project-spec.md` | 设计/规格 | Jia API 架构、模块、技术栈、分层和非功能设计 | 主体多模块架构成立，部分描述与当前模块/版本漂移 | 🟡 基本完整 86% | 按当前 settings.gradle 自动生成模块图 |
| DOC-027 | `api/docs/specs/modules/jia-agent-module-spec.md` | 设计/规格 | Agent 注册、状态、能力、Persona、任务、评估和对话模板 | `api/agent/`、Agent Controller/Service/DAO/Tests | ✅ 完整 94% | 补权限、审计和评分可解释性 |
| DOC-028 | `api/docs/specs/modules/jia-base-module-spec.md` | 设计/规格 | 字典、多语言、缓存、日志和公告 | `api/base/` | 🟡 基本完整 82% | 补日志/公告 Controller 与订阅闭环 |
| DOC-029 | `api/docs/specs/modules/jia-chat-longterm-memory-spec.md` | 设计/规格 | 对话摘要、向量记忆、Advisor、同步/清理任务和检索 | `api/chat/` memory/advisor/job/service 实现与测试 | 🟡 基本完整 78% | 完成 ES 索引自动创建、热更新和降级 |
| DOC-030 | `api/docs/specs/modules/jia-chat-module-spec.md` | 设计/规格 | 会话、消息、流式响应、记忆和聚义厅通信 | `api/chat/` | 🟡 基本完整 85% | 补长效记忆降级、索引初始化和跨节点一致性 |
| DOC-031 | `api/docs/specs/modules/jia-common-module-spec.md` | 设计/规格 | 基础实体、DAO、工具、异常、缓存和测试支持 | `api/common/` | 🟡 基本完整 88% | 收敛反射和历史工具类技术债 |
| DOC-032 | `api/docs/specs/modules/jia-dwz-module-spec.md` | 设计/规格 | 短链接生成、还原、管理和访问 | `api/dwz/` | ✅ 完整 92% | 补 URL 安全、过期清理和访问统计 |
| DOC-033 | `api/docs/specs/modules/jia-isp-module-spec.md` | 设计/规格 | 车辆、品牌、ISP、CMS、DNS、LDAP、文件和编排服务 | `api/isp/` | 🟡 基本完整 80% | 重写已落后于代码的模块规格并补契约测试 |
| DOC-034 | `api/docs/specs/modules/jia-kefu-module-spec.md` | 设计/规格 | 客服消息、订阅、FAQ 和消息类型 | `api/kefu/` | 🟡 基本完整 84% | 补实时会话、统计和智能 FAQ 验证 |
| DOC-035 | `api/docs/specs/modules/jia-material-module-spec.md` | 设计/规格 | 媒体、新闻、短语、投票、提示和 PV | `api/material/` | ✅ 完整 93% | 补内容审核、文件安全和专项服务测试 |
| DOC-036 | `api/docs/specs/modules/jia-oauth-module-spec.md` | 设计/规格 | OAuth 服务端/客户端/资源服务器、LDAP 和 API Key | `api/oauth/` | 🟡 基本完整 76% | 修复空返回并补协议级集成测试 |
| DOC-037 | `api/docs/specs/modules/jia-plugin-module-spec.md` | 设计/规格 | Gradle 共享依赖管理插件 | `api/plugin/` | ✅ 完整 90% | 增加 Gradle TestKit 兼容性测试 |
| DOC-038 | `api/docs/specs/modules/jia-point-module-spec.md` | 设计/规格 | 积分账户、流水、消费、邀请奖励和礼品兑换 | `api/point/` | 🟡 基本完整 88% | 补并发账本、幂等和对账 |
| DOC-039 | `api/docs/specs/modules/jia-sms-module-spec.md` | 设计/规格 | 短信发送、模板、记录、供应商适配和验证码 | `api/sms/` | 🟡 基本完整 72% | 统一供应商能力并补回执/审核闭环 |
| DOC-040 | `api/docs/specs/modules/jia-task-module-spec.md` | 设计/规格 | 周期任务、任务明细、调度执行和日志 | `api/task/` | 🟡 基本完整 88% | 补分布式锁、误触发保护和日志查询 |
| DOC-041 | `api/docs/specs/modules/jia-user-module-spec.md` | 设计/规格 | 用户、角色、组织、分组、权限和消息 | `api/user/` | ✅ 完整 92% | 补权限审计、缓存失效和导入回滚 |
| DOC-042 | `api/docs/specs/modules/jia-workflow-module-spec.md` | 设计/规格 | 流程部署、定义、实例、任务、变量和批注 | `api/workflow/` | 🟡 基本完整 74% | 新增 Camunda 集成测试并清理 null 分支 |
| DOC-043 | `api/docs/specs/modules/jia-wx-module-spec.md` | 设计/规格 | 公众号、用户、菜单、素材、模板消息和微信支付 | `api/wx/` | 🟡 基本完整 84% | 补支付通知幂等、退款对账和公众号契约测试 |
| DOC-044 | `deliverables/codex-ws-agent-package/INSTALL.md` | 运维/交付 | Codex WebSocket Agent 安装、配置、systemd 和验证 | 交付包、客户端、profile 配置和启动脚本存在 | ✅ 完整 92% | 加入自动安装验收和版本校验 |
| DOC-045 | `deliverables/codex-ws-agent-package/files/app/README.md` | README | 多 Profile、热加载、重连、消息路由、Codex 调用和关闭行为 | 交付版 agent-client 与配置文件存在 | ✅ 完整 92% | 增加客户端单测和协议兼容矩阵 |
| DOC-046 | `docs/DEPLOYMENT.md` | 运维/交付 | 前后端/Agent 发布、日志、数据库、回滚和检查清单 | 三个部署脚本及主要目录存在 | ✅ 完整 90% | 定期验证路径并自动化数据库迁移门禁 |
| DOC-047 | `docs/codex-project-map.md` | 说明/约束 | 仓库、Git、前后端目录和文档入口地图 | 路径与当前结构一致 | ✅ 完整 98% | 新增关键文档时同步维护 |
| DOC-048 | `docs/codex-ws-agent.md` | 说明/约束 | WebSocket 协议、多 Profile 客户端、部署和 Persona 绑定 | `docs/agent-client.mjs`、后端 WebSocket handler、绑定 API 和脚本存在 | ✅ 完整 92% | 增加协议测试和密钥轮换说明 |
| DOC-049 | `docs/juyiting-collaboration-implementation-plan.md` | 实施计划 | 主操作、显式点将、传令上下文、溢出展示、拆分和验收 | 协作契约测试覆盖，阶段一至三完成，后续增强部分完成 | ✅ 完整 94% | 回填阶段状态并将未完成项迁入 backlog |
| DOC-050 | `docs/juyiting-feature-guide.md` | 说明/约束 | 聚义厅定位、页面、数据边界、流程、状态、代码索引和优化建议 | 当前主流程已实现，部分路径仍是历史路径 | ✅ 完整 92% | 修正文档路径并标记已完成优化项 |
| DOC-051 | `docs/juyiting-runbook.md` | 运维/交付 | 聚义厅主文件、数据边界、画像、UI 不变量和验证 | 与当前代码和测试高度一致 | ✅ 完整 96% | 持续保持短小并自动检查禁用接口 |
| DOC-052 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | 实施计划 | TMX、资源加载、melonJS 场景、精灵点击、DOM fallback 和发布 | 功能任务均有代码和测试；计划 checkbox 未回填 | ✅ 完整 95% | 标记 superseded/completed，发布步骤与功能步骤分离 |
| DOC-053 | `docs/superpowers/specs/2026-06-29-juyiting-high-immersion-ui-design.md` | 设计/规格 | Tiled 地图、spritesheet、melonJS/Vue 分工、体验和降级 | Canvas 舞台、TMX、sprites 和降级已实现 | ✅ 完整 95% | 标记由统一设计继承 |
| DOC-054 | `docs/water-margin-style-reference.md` | 说明/约束 | 公版来源、UI 文案规则和聚义厅词汇表 | 大部分聚义厅文案与角色元数据符合 | ✅ 完整 90% | 补语料来源文件并增加文案 lint |
| DOC-055 | `docs/workspace-git.md` | 说明/约束 | 根协调仓、api/web submodule 和 gitw 用法 | 当前协调仓结构与说明一致 | ✅ 完整 100% | 无需功能实现，保持路径准确 |
| DOC-056 | `web/README-test.md` | README | Mocha 测试安装、结构、命令和示例 | 当前 `npm run test` 通过 473 项，但部分命令描述较旧 | 🟡 基本完整 88% | 同步当前 tsx/mocha 配置和脚本名 |
| DOC-057 | `web/README.md` | README | Vue/Vite 项目启动和基础说明 | 项目可构建运行，但 README 仍接近模板 | 🟡 基本完整 78% | 补实际功能、环境变量、路由和部署入口 |
| DOC-058 | `web/docs/assets/juyiting/songjiang-style-review/generation.md` | 说明/约束 | 宋江精灵生成、去绿幕、风格派生、角度和 runtime sheet 过程 | 生成记录、manifest、sheet 和测试存在 | ✅ 完整 96% | 保留生成工具版本与源资产校验和 |
| DOC-059 | `web/docs/assets/juyiting/songjiang-style-review/review.md` | 说明/约束 | 宋江精灵人工风格评分和目标尺度验收 | review 证据与最终资源存在 | ✅ 完整 96% | 增加评审人/日期和自动视觉差异 |
| DOC-060 | `web/docs/changelogs/juyiting-changelog.md` | 变更记录 | 聚义厅历史实施状态和版本变更 | 历史记录可追溯但与当前状态存在时间差 | ✅ 完整 90% | 仅保留历史事实，当前状态链接主 checklist |
| DOC-061 | `web/docs/juyiting-development-guide.md` | 说明/约束 | Camera/Input 稳定 facade、响应式、生命周期和验证 | facade、测试和行为均已实现 | ✅ 完整 96% | 修正旧工作目录/PowerShell 命令 |
| DOC-062 | `web/docs/juyiting-feature-guide.md` | 说明/约束 | Camera/Input、TMX/Sprite、场景状态和仿真验证指南 | 相关代码和测试完整 | ✅ 完整 96% | 同步 feature flag 灰度状态 |
| DOC-063 | `web/docs/juyiting-public-beta-readiness.md` | 说明/约束 | 本地启动、发布验证、UI smoke、公测门禁和剩余项 | 大部分自动验证脚本存在；日期性结论不能视为永久有效 | 🟡 基本完整 86% | 每次发布重新生成证据并清理历史提交列表 |
| DOC-064 | `web/docs/juyiting-public-beta-runbook.md` | 运维/交付 | 发布窗口、责任、配置、监控、告警、发布、回滚和观察 | 流程文档存在，监控/告警自动化证据不足 | 🟡 基本完整 78% | 明确责任人、指标地址和自动回滚条件 |
| DOC-065 | `web/docs/juyiting/modular-layer-prompts.md` | 说明/约束 | 八类模块化场景资产 prompt、透明处理和运行时契约 | 对应资产与资源测试存在 | ✅ 完整 95% | 增加模型/seed/license 和校验和 |
| DOC-066 | `web/docs/specs/app-spec.md` | 设计/规格 | Chat、聚义厅、Task、Phrase、Vote、Gift、DWZ、OAuth、组件、路由和非功能 | 主要页面和 API 已实现；非聚义厅测试较少 | 🟡 基本完整 86% | 按功能拆分规格并补 E2E/安全/性能验收 |
| DOC-067 | `web/docs/specs/juyiting-spec.md` | 设计/规格 | 聚义厅 Agent 地图、名册、任务、传令、人格、讨论和视觉交互 | 主协作闭环基本完整 | ✅ 完整 90% | 对齐最新 Scene State 和删除旧实现描述 |
| DOC-068 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | 实施计划 | 变换、输入迁入 HallScene、移除 DOM 场景、热点和发布 | 代码与回归测试完成 | ✅ 完整 95% | 标记 completed/superseded |
| DOC-069 | `web/docs/superpowers/plans/2026-07-04-juyiting-modular-layer-assets.md` | 实施计划 | 已废弃的模块化资产 manifest 说明 | 文档明确 obsolete，无实现要求 | ✅ 无需实现 100% | 保留重定向到现行资源契约 |
| DOC-070 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | 实施计划 | 场景模型、持久化、版本、SSE、Phase、接口、业务写入和开关 | 后端全链路及专项测试完成 | ✅ 完整 94% | 回填 checkbox 并补生产容量测试 |
| DOC-071 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | 实施计划 | TypeScript 工具、camera、input、facade、响应式和验证 | 类型化模块与测试完成 | ✅ 完整 96% | 回填任务状态并增加实机矩阵 |
| DOC-072 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | 实施计划 | A*、slot、状态适配、单 Agent 引擎、REST/SSE、debug 和 smoke | 纵向闭环与单测已完成 | ✅ 完整 94% | 推进默认启用并补生产事件监控 |
| DOC-073 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | 实施计划 | movement schema、校验、TMX 编辑、snapshot/preview、精灵门禁 | 工具链、资源和测试完整 | ✅ 完整 97% | 纳入 CI 强制门禁 |
| DOC-074 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | 实施计划 | 六 Persona、多人限制、碰撞、预约、队列、重规划、24/12规模和 Android 性能 | 仅有多 Agent 基础引擎、slot 和 replanning 指标；核心多人系统缺失 | 🟠 部分实现 43% | 按 Task 1-10 完成实现与设备证据 |
| DOC-075 | `web/docs/superpowers/plans/2026-07-11-juyiting-unified-rollout-index.md` | 实施计划 | Phase 1/2 依赖顺序、门禁和发布检查点 | Phase 1 基本通过，Phase 2 未达到门禁 | 🟡 基本完整 76% | 回填统一状态并阻止未达标 Phase 2 发布 |
| DOC-076 | `web/docs/superpowers/specs/2026-07-01-juyiting-melonjs-scene-design.md` | 设计/规格 | melonJS 场景迁移、镜头输入、热点、错误和验证 | 设计已实现 | ✅ 完整 96% | 标记已完成并链接统一设计 |
| DOC-077 | `web/docs/superpowers/specs/2026-07-04-juyiting-modular-layer-assets-design.md` | 设计/规格 | 废弃设计说明 | 明确 obsolete，无实现要求 | ✅ 无需实现 100% | 无需改动 |
| DOC-078 | `web/docs/superpowers/specs/2026-07-09-juyiting-mobile-map-interaction-design.md` | 设计/规格 | 移动加载、缩放、拖动、键盘、面板、生命周期和降级 | Camera/Input 与组件测试覆盖主要要求 | ✅ 完整 94% | 补设备性能与浏览器兼容证据 |
| DOC-079 | `web/docs/superpowers/specs/2026-07-10-juyiting-interaction-and-npc-simulation-design.md` | 设计/规格 | 交互、TMX 管线、寻路、队列、多人移动、精灵、后端语义和模块化 | Phase 1 已实现；多人碰撞/排队/性能仍缺 | 🟡 基本完整 78% | 拆分已完成与 Phase 2 未完成要求 |
| DOC-080 | `web/docs/superpowers/specs/2026-07-11-juyiting-unified-map-and-agent-simulation-design.md` | 设计/规格 | 统一架构、场景契约、TMX、Sprite、仿真、交互、错误、测试和分阶段开关 | Phase 1 完整度高；Phase 2 和正式 rollout 不完整 | 🟡 基本完整 82% | 以本规格作为唯一现行基线并维护 requirement IDs |
| DOC-081 | `web/src/components/world/DESIGN.md` | 设计/规格 | 梁山泊开放世界、Agent、108 将、WebSocket、任务、区域、状态、Chat、AI、战斗、装备和成就 | 聚义厅/Agent/任务/区域/Chat 已部分或完整实现；战斗、物品装备、成就未形成模块 | 🟠 部分实现 58% | 明确拆成现行聚义厅与未来游戏化 roadmap |
| DOC-082 | `web/src/composables/README.md` | README | useHttp loading、错误、token、响应式、API 工厂、回调和 SSE | `useHttp.js`、API factories 和相关测试存在 | ✅ 完整 92% | 同步实际函数签名并拆分超大 composable |

## 零遗漏规则

- `/tmp/cyf-md-source-list.txt` 是本轮冻结清单；最终验证会重新扫描并与本表路径逐一比较。
- 新增 Markdown 不自动视为已覆盖，必须分配新的 DOC ID 并补充要求与证据。
- 接口规格不只按文件计数，必须同时通过逐端点附件。
- 实施计划不以 checkbox 为真实进度，必须同时通过 Task 级代码与测试证据。
