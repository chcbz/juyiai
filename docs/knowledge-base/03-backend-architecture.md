# 后端架构与领域

## 分层约束

后端以 Gradle 子项目表达领域和层。`core` 提供领域对象/基础能力，`api` 暴露跨模块契约，`service` 提供业务与 HTTP 控制器，`mapper` 负责 MyBatis/DAO 及 XML，`starter` 负责可运行装配。根 `validateLayering` 任务将 mapper→service、api→service 和 service 层 DAO 视为违规。

`common` 是横切基础：结果封装（`JsonResult`、`JsonResultPage`）、上下文、异常/响应处理、通用服务、Mapper 支持和 starter 配置。业务服务通常 `implementation` 依赖 `common-service`，并对外 `api` 自身领域 API。

## 领域地图

| 领域 | 静态职责线索 | 主要接口面 |
| --- | --- | --- |
| `agent` | 人格、运行态、身份、能力评估、悬赏任务、协作工作项、场景状态/事件 | `/agent/**`、`/agent/scenes/**` |
| `chat` | 会话、消息流、聚义厅消息中继、任务团队线程、知识库检索 | `/chat/**`、`/chat/task-threads/**`、`/juyiting/**` |
| `oauth` | OAuth 授权服务器/资源服务器/API Key | `/oauth/**`、安全 filter chain |
| `user` | 用户、组织、角色、权限、消息 | `/user/**`、`/msg/**` 等 |
| `task` | 通用任务计划、任务项与 Job 执行 | `/task/**`、`/job/**` |
| `material` | 媒体、新闻、短语、提示、投票、PV | `/media`、`/news`、`/phrase`、`/vote` 等 |
| `point` | 积分、礼品、使用记录 | `/point/**`、`/gift/**` |
| `wx` | 微信公众号、菜单、用户、支付 | `/wx/**` |
| `isp` | 域名/DNS、服务器、文件、CMS、车辆、LDAP | `/isp/**`、`/cms/**`、`/file/**` 等 |
| 其他 | base 字典、dwz 短链、kefu、sms、workflow | 对应控制器映射 |

此表来自 `settings.gradle`、控制器和 Mapper/实体命名，不代表全部产品策略。

## Agent 与 Chat 的耦合

`chat:jia-chat-service` 依赖 `agent:jia-agent-api`，并依赖 task 核心/API；agent service 同时以 compile-only 使用 task 与 oauth API。Chat starter 又装配 agent service 和 task mapper。这说明聚义厅的对话、任务和 Agent 身份是跨领域整合，而非单独前端模拟。

Agent 持久化资源中包括人格/运行态/绑定/身份别名、对话模板、任务元数据/成员/工作项/请求/产物/笔记以及场景 state/event/version/phase report。Chat 另含任务线程 schema。详见 [数据与安全边界](07-data-security-and-boundaries.md)。

## 启动与依赖

`api/starter/build.gradle` 使用 Spring Boot 4.0.1，并汇入安全、OAuth2 authorization/resource/client、Redis、LDAP、Elasticsearch、AMQP、Actuator、WebSocket、Camunda、Spring AI（DeepSeek/OpenAI）等依赖。依赖存在不等同于每个部署环境均启用；需结合 profile 和外部配置确认。
