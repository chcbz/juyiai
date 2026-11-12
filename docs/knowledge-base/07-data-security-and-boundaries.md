# 数据、安全与风险边界

## 数据访问与租户上下文

MyBatis Mapper XML 由 `classpath*:cn/jia/**/*Mapper.xml` 发现，分页使用 PageHelper（MySQL dialect）。`EsContextFilter` 初始化请求上下文；JWT 资源服务器 filter 会从 token claim 填充 `jiacn`、`appcn`、`client_id`、`username`。因此业务代码的 `EsContextHolder` 值是重要的数据归属边界，新增查询/写入应验证是否正确应用 client/tenant 范围。

常见响应封装为 `JsonResult<T>`，分页为 `JsonResultPage<T>`；不要假设所有控制器均返回相同 HTTP status/业务 code 组合，Agent scene 和 Agent task 控制器有专用异常映射。

## 已发现的关键 schema

| 范围 | schema 资源 | 主要表/对象 |
| --- | --- | --- |
| Agent | `agent/.../resources/db/schema.sql` | persona、runtime、binding、identity registry/alias、dialogue template、task meta/member/work item/request/artifact/note、scene state/event/version/phase report |
| Agent 协作 | `task-collaboration-schema.sql` | task 协作字段、成员/工作项/请求/产物及索引演进 |
| Chat | `chat/.../resources/db/task-thread-schema.sql` | `agent_task_thread` |
| 通用业务域 | 各 mapper/service 的 `src/test/resources/db/schema.sql` | 面向模块测试的建表/数据基线 |

SQL 文件是 schema 意图和可重跑迁移线索，但不应在不了解当前库版本时直接执行。

## 认证路径

- 资源服务器对配置的 resource URI 使用 JWT；除了微信签名校验和短链查看等显式豁免外，默认要求认证。
- `/api/**` 另有 API Key filter chain：从 `X-API-Key` 或 `api_key` 参数读取 API key，认证成功后将 client/jiacn 写入上下文。
- 前端常规请求使用 Bearer token；开发 Vite proxy 的 `/api` rewrite 与后端 `/api/**` filter 是两个不同层面的路径概念，部署时必须验证网关后的最终路径。

## 必须单独评审的风险面

- OAuth/JWT 签名材料、加密口令、数据库与外部服务凭据只应由部署密钥管理提供；不要把实际值复制进知识库、示例或前端环境文件。
- API Key 支持 query parameter，可能进入访问日志、浏览器历史或代理日志；新增集成优先使用 Header，并评估淘汰 query 传递的兼容策略。
- Chat/AI 流、SSE 订阅和任务协作属于状态/授权敏感面；修改需检查 conversation/task scope、断线继续、重复事件和越权读取。
- agent task schema 含版本字段和协作索引；修改状态转换、lease、聚合或回填时应按 P0 事务/并发任务处理。
