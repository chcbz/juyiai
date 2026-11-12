> **2026-11-06 现行规则：** 用户告知云效额度用完，CYF 默认改为本地测试、构建、打包和受控部署；不自动启动 Flow。正式证据绑定真实本地构建批次、完整 commit/tree、必要测试与制品 SHA-256，不伪造 Run/CI 身份。保留发布授权、身份/ACL、锁、备份、可恢复安装与线上验收；develop 不自动部署。Gradle 仍先读构建文件并经现有编排器串行执行。下文冲突的 Flow-only/禁止本地构建说明仅作历史，完整规则见根 `AGENTS.md`“本地构建与部署（2026-11-06 用户最新决定）”。本次仅改规则，未改工具/云端配置或实际构建部署；旧 Flow-only 安装器须明确适配本地来源并验证后才能使用。

# 运维、测试与变更指南

## 运行配置线索

`common:jia-common-starter` 的 `application.properties` 给出默认 profile、Hikari、Tomcat、MyBatis、PageHelper、Redis session、Jackson、Swagger/Knife4j 等共性参数。各 starter 的 `application-dev.properties` / `application-prod.properties` 补充环境值；这些值及外部环境变量才是实际运行配置来源。

前端 Vite dev server 默认 8080 并使用本地 TLS 文件；Flow 生产构建输出 `web/dist/`。构建/测试/部署策略见 [`docs/aliyun-flow-cicd-strategy.md`](../aliyun-flow-cicd-strategy.md)，部署运行细节见 [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md)。

## 验证选择（2026-10-22资源分工更新）

Flow卸载高内存测试/构建/打包并执行授权部署；本机可做轻量检查、查询、协调和上线核验。按实际负载而非工具名称划分。本机不生产打包，Run本轮执行完即结束，不挂外部配对/ready文件/验收等待；详细策略见根AGENTS及上述部署策略。本次仅改规则，未修改工具或云端配置。

| 改动范围 | 最小验证 | 补充验证 |
| --- | --- | --- |
| 根仓知识/规格 | Markdown 链接、路径、git status | 审阅子模块 SHA 是否正确 |
| Web 一般改动 | 轻量定向检查可本机；重型测试和Vite生产构建走Flow4403172 | 对应 Mocha/组件测试摘要与制品 SHA |
| 聚义厅 UI/逻辑 | 相关 `web/tests/` 按实际负载分层；重型回归走Flow | 地图、遮挡、scene/SSE、public beta smoke 脚本 |
| 后端领域改动 | 固定commit/tree经orchestrator：重型模块测试走Flow5260799，低开销诊断可本机 | Flow中的`validateLayering`、fresh `bootJar`、真实Run/日志与制品摘要；相关隔离集成/数据库验证 |
| 身份、ACL、迁移、事务 | 专项测试按负载分工，重型执行走Flow；保留数据恢复计划 | Owner 自检，保留隔离 fixture、原子性及授权；不另设 Reviewer，生产动作按实际授权 |

## 变更落点速查

- 任务/Agent API：`api/agent/jia-agent-service`，契约/DTO：`api/agent/jia-agent-{api,core}`，持久化：`api/agent/jia-agent-mapper`。
- 聚义厅页面：`web/src/components/world/JuyiHall.vue`；组件：`web/src/components/juyiting/`；逻辑：`web/src/composables/juyiting/`；场景：`web/src/game/`。
- Chat stream/会话：`api/chat/jia-chat-service` 与 `web/src/composables/juyiting/useHallConversation.js`。
- 全局 HTTP/OAuth：`web/src/composables/useHttp.js`、`web/src/stores/api.js`、`api/oauth/**`。

## 更新本知识库

功能变更若影响接口、模块、数据边界或运维命令，必须同步更新对应 KB 文档。接口变化需同时更新 [`04-backend-api-index.md`](04-backend-api-index.md) 与 [`04-backend-api-inventory.md`](04-backend-api-inventory.md)；重新生成后更新 [`BASELINE.yaml`](BASELINE.yaml) 的日期、api/web SHA 和计数。应保留生成方法，避免把手工摘要与自动提取清单混淆。

## 图片技能与统一接口交付的运行边界（2026-10-16）

覆盖API6116a104、Web421f628c、Runtime6a9d8d3的2026-10-15实际发布，不是新部署。整体链路见[聚义厅SDD](06-juyiting-end-to-end.md#image-skill-contract)。

- 以下工具/制品绑定记录仅描述2026-10-15历史发布，不作为现行执行规则；新任务使用上述2026-10-22资源分工。历史正式工具使用[编排索引](../../ops/orchestration/README.md)：Web绑定Flow4403172的同Run制品，API绑定固定干净源码的本地build/log/JAR SHA；原安装器保留锁、身份、备份、制品校验、健康与业务核验。不得把本轮临时`install-after-prepare`/`finish-tested-cutover`脚本当长期部署接口或恢复已弃用的源码直发方式。
- Runtime版本化安装只替换制品及其systemd路径，实际配置使用`/home/isp/conf/cyf-agent-runtime-v1`；静态HOME位于`/home/isp/state/cyf-agent-runtime-v1/unified/agents/{角色}/codex-home`。本轮未修改Provider密钥、身份、HOME、资料ACL或费用策略。构建Python须使用已验证3.11工具链；系统python3.6无法安装固定Pillow10.4，不能为过构建而放宽锁定依赖。
- 先区分安装SUCCEEDED、目录CALLABLE、action接纳、Provider等待、RESULT_COMMITTED、可下载及内容正确六个事实。目录不可用先查认证回执、代际类型、权益和绑定，不重复购买；Provider在途不重复发新动作；下载必须比对manifest的output SHA/byteLength，不能误用result manifest的SHA。
- 已发生的失败与证据见[验收](../../specs/juyiting-skill-execution/acceptance.md)及其原字节副本索引；OCR仍失败，正式发布不等于全部验收。临时脚本清理保留可恢复备份及摘要清单，不删除原始回执或正式`ops/`工具。


## 议事 SSE 空闲连接诊断（2026-11-07 核验）

覆盖 API `69d7d1d537d332fbfe468c58dfcdc9a699640258`（develop 对应修复 `638896a`），仅传输层，不改变业务完成事实、最终回复落库或鉴权职责。

- `/chat/conversation/events` 的长连接由 `ChatStreamPolicy.keepAlive` 每30秒发送一次 `:keep-alive` 注释；不查数据库、不发业务事件、不推进消息游标。业务源只有一个订阅，背压时丢弃多余保活，取消/结束时释放定时器。
- Nginx `/chat` 的300秒空闲读取超时保持不变。诊断必须对比直连API与公网HTTP/2并观察超过300秒；不能只凭单元测试、HTTP200或短时连接认定修复。
- Web既有解析器忽略SSE注释，页面不应出现“keep-alive”消息。业务首帧耗时观测只统计业务源，保活不能掩盖模型/任务等待。
- 发布后的测试登录须验证有效性。旧测试令牌若返回401，应通过正常登录重新获取；保留失败样本，不以绕过鉴权进行探测。
- 精确源码、安装与公网实测证据见 `docs/implementation/handoffs/HALL-THREE-FIXES-20261106.md`。历史异常事项不因传输修复而自动重放或恢复。


## 统一调度与租费上线操作边界（2026-11-11 核验）

覆盖API `c7c0f2d78d4de51d4caed81cfe2caa1a6835b565`、独立SQL资源`87ccfef032662f15c5c60a820403b8edb2f65c66`、Runtime `7985667d1d73d3843d9f86dbc94f410a8ca520bd`。本节是已核对的配置/运维知识，不是完整业务验收；当前状态见[调度验收](../../specs/task-scheduling/acceptance.md)。

- `cyf.task.scheduling.enabled`与显式node-id、GENERAL/CONTROL容量、batch及lease/retry/recovery参数共同启用统一worker。node-id同一节点各消费者共用、重启稳定；租约心跳不是业务强制deadline。正常多OAuth客户端进程不要为了后台业务增加全局fixed-tenant.client-id；该字段会同时收窄原认证准入。明确维护CLI仍使用其固定tenant/client。
- 结构升级不由启动器自动执行。按固定SQL、实际停写快照、逐表回读执行；含不兼容结构的安装用原native forward-only恢复语义，不自动恢复旧JAR并运行于新结构。失败与新修复/验收另记，不改历史回执。
- Runtime清理需要独立运维公共基线和`CYF_RUNTIME_KNOWLEDGE_CONFIG_FILE`；后者指向Agent可变HOME之外、实际服务用户拥有的0600配置。没有该路由则不以假提取器确认清理。知识提取成本归平台，实际会话清理/Provider收费不能仅凭配置加载与在线心跳宣称通过。
- API mTLS文件必须按**实际API服务身份**检查可读；维护命令以root可读不等于生产用户可读。共享父目录只授予确切服务用户必要穿越，密钥只读，不为此开放全局目录或写权限。保存前后ACL/摘要与配置证据。
- 监控pause/resume可能因其现有互斥返回deferred；先核对实际进程/安装record，再于锁释放后沿原入口恢复。监控恢复失败不等于制品安装失败，不据此重复构建/安装或回滚资金事实。
