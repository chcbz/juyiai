# D3.1影响范围：统一任务承办能力

> 2026-10-21；设计影响分析，不是实施完成清单。历史源码观察保留在 `design-recheck-20261021.md`，其中D2.1新增流程要求已撤销。

## 必改与复用

| 范围 | 必要改动 | 明确不做 |
|---|---|---|
| Web Agent详情 | 本人逐Agent开关行，加载/失败/并发处理 | 独立接单卡片、接单后台 |
| Web任务承办 | 统一候选、公开所属用户、原确认区资料说明；任务继续使用assignedTarget | 外单确认页面、二次启动、专属待指令 |
| API政策/候选 | 绑定级开关；复用注册表，tenant/client精确相等；推荐仅排序 | 白名单、任务类型/费用策略引擎 |
| API原委派 | point-and-deliberate统一解析两主体，扩展现有assignment/grant | 新外单提交API、订单/委派状态机、prepare-only outbox |
| API执行与Chat | B调度/认证、A数据归属，修复领取/输入/ACK/回报/恢复一致性 | 两套执行器、全局放开owner检查 |
| Runtime | 按真实缺口补上下文及线程隔离，沿原协议和runner | 外单专用runner、命令体系 |
| 数据与迁移 | 政策记录、既有授权执行主体及必要索引 | delegation新表、独立撤回与转单表 |
| 成果/验收/取消/成本 | 复用既有能力并回归跨主体授权 | 新运行中撤单、服务方撤回、收费或成本模块 |

## 定向代码落点（基于既有复核，不宣称最新线上实现）

- Web：`web/src/composables/juyiting/useHallData.js`、`web/src/components/juyiting/BountyPanel.vue`、`web/src/components/world/JuyiHall.vue`。去掉任务承办对本人名册和在线/能力的硬依赖，保留私人管理守卫；他人摘要不调用owner-only能力详情。
- API agent：`AgentTaskDeliberationOperationController`、`AgentTaskExecutionGrantServiceImpl`、`AgentServiceImpl`及相关mapper。主改原点将入口及目标解析，不扩出外单专属服务流程。
- API execution：`PersonalWorkspaceExecutionServiceImpl`及mapper。区分任务scope与Runtime主体，统一领取/输入/effect/结果/恢复校验。
- API chat：`ChatBountyBootstrapAdmissionService`保留自动首轮；`ChatDeliberationOutboxRelay`、`ChatDeliberationOutboxService`、`AgentWebSocketHandler`校准双向主体。任务继续与正式成果不另开通道。
- Runtime：`/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/chat-runtime.mjs`及同模块agent-client，检查持久线程键/ACK恢复；以真实缺口决定修改，不预设整模块重写。

## 撤销上一版扩大项
D2.1 R03所述自动首轮是本版应复用的行为，不是缺陷；R06不再要求新增三种撤回协调；R07不再要求独立外单资料子集协议，统一确认当前任务资料；R08不扩建换承办；R10不为本需求建设通用回执平台。其余身份、隐私、幂等及并发问题仍须在既有架构内修正。

## 当前基线与风险
本轮本地读取：root `93f7e0afe81f3eb8d9e23e6a7555ea960c6010c2`，API `510b2937696495b54a9203729784660e62c65082`，Web `9dbd132e8bc25119c0532cbed672ab7fa4a214b3`。只重读原入口与相关组件，不声称重新全量审查或查询最新远端/线上；上一轮生产证据维持其原时间与版本。

UI改动小，但跨用户执行授权不是仅加按钮；最主要风险是按B误读A的数据、ACK归属错误、关闭和提交竞态、重试重复启动。实施必须回归本人链路与真实A/B/C隔离，不用减少页面代替权限测试。已有工作区无关改动不在本轮范围。

## D3.1定向核验
本轮重新读取注册表/原grant DDL、identity/PWE实体、point-and-deliberate控制器与assignLocked锁序：bindingId为BIGINT，PWE已有taskGrantId/taskGrantVersion，grant缺执行owner/binding。由此固定单平台共享tenant/client、grant新增两主体字段及policy revision，取消平台映射和资料重新确认工作。具体编码合同见design.md§9；新增政策表同时保存开关修订和幂等回执，不建第二张回执表。没有重跑生产浏览器或声称正式验证成功。
