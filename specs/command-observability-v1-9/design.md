# 1.9合同 v1（2026-09-17）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：只读协作运行看板与异常定位。**

### 最小责任链
业务模块提供权威执行/投递事实；看板只读投影，审计及指标不控制业务状态。

授权读取→展示积压/待回执/失败/未知→按既有标识关联诊断。

### 实施约束
投递完成不等于任务完成；不从看板自动重试/重放/扣费/迁移，不为观测每片输出写库。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 1 基线/权限

API develop `0b5cfe8cbcafcadca7dcef07874d6b397f0ab1e4`，Web develop `7099b176e06e2322c6a79f258a4ad74d6221c358`；必须保留1.8祖先。新Web路由`/command-observability`，name=`CommandObservability`，个人中心唯一入口“协作运行看板”。无独立Reviewer，各Owner自检。

复用D09权限`agent-command-ops-read`、JWT中exact jiacn/client_id/sub且authentication.name=sub。不得接受其他主体类型、自动trim、persona推导或默认scope。原指标/DLQ/audit方法鉴权不变。生产read-enabled默认false；不改默认、不授新权限、不触碰redrive/reissue或服务进程。

## 2 唯一新增接口：安全发现能力

GET `/agent/internal/command-operations/capabilities`。独立轻量Controller始终注册，不依赖数据库/Rabbit或已关闭的OperationsService bean。读取既有`agent.rabbit-operations.read-enabled`，默认false。

正常有效JWT响应HTTP200、Cache-Control private,no-store：
`{"code":"E0","data":{"contractVersion":"command-observability-v1","available":true,"readOnly":true,"reason":null}}`。

同样有效scope但无read权限：available=false、reason=FORBIDDEN；有read权限但开关关闭：available=false、reason=DISABLED；readOnly恒true。匿名/未认证/非JWT=401；malformed/missing/noncanonical scope、name/sub不符=403。可用性必须服务端计算，前端不得从解码JWT/缓存profile猜测权限。响应不得含scope/token/密钥/权限清单。无DB读写、无运维计数查询。

## 3 复用现有三个只读接口（保持原路径/DTO/权限）

- GET `/agent/internal/command-operations/metrics`：E0 data为AgentCommandOpsMetrics。deliveryByStatus/inboxByStatus/inboxByResult/outboxByStatus/operationsByTypeAndOutcome为冻结状态标签→long计数；ackLatencySeconds为观测耗时，outboxBacklog/outboxOldestAgeSeconds/publishFailureTotal/rabbitDlqCount/waitingDueCount/sentUnacknowledgedCount/reconnectQueueDepth/expiryProximityCount/capturedAt。非安全整数或无效值显示未知，不算0、不设SLO拦截。
- GET `/agent/internal/command-operations/dlq?afterDeliveryId=0&limit=20`：E0 data `{items,nextAfterDeliveryId,hasMore}`。条目deliveryId/commandId/eventId/messageId/taskId/targetAgentId为字符串；deliveryStatus/outboxStatus/inboxStatus/inboxResultStatus；activeAttempt/publishAttemptCount；publishedAt/processedAt可null、expiresAt/updatedAt毫秒。只呈现这些已有事实，不猜故障原因，不显示wireSha256或消息payload。
- GET `/agent/internal/command-operations/audit?afterId=0&limit=20`：E0 data `{items,nextAfterId,hasMore}`。选择展示id/operationId/phase/operationType/taskId/targetAgentId/deliveryId/sourceAttempt/newAttempt/requestedAt/completedAt/outcome/errorCode/createdAt。不展示/复制reason、ticketReference、requester/approver/createdBy、wireSha256等无关细节，不console原响应。

分页使用服务端字符串cursor，禁止Number转ID；hasMore=true而无合法进展cursor为协议错误，不能循环。DTO与实际现有Controller精确对齐，未定义字段不据猜测渲染。既有401/403/404/503及E0以外业务码必须失败呈现；404可能是服务尚未部署/未启用，不声称空列表。

## 4 前端数据与生命周期

复用useHttp鉴权/取消，建立仅含GET的独立client，不导出mutation方法。先capabilities验证available/readOnly/version/reason，再并发三块独立读取，局部失败不伪报全页成功。操作只手动刷新/下一页/重试，不自动poll，不偷偷调用业务POST。

身份generation或当前用户变化：立即清空能力和全部数据、游标与错误；取消本页请求并拒收迟到结果。每块有自身request generation；重复点击不产生乱序覆盖。卸载取消，只取消本页拥有的请求。手动全刷新重置分页且不能让旧追加请求污染新列表。401/403撤权时清空既有敏感展示，不保留旧数据；临时网络错误可保留同身份数据但显著标过期。

profile只做能力发现，不拉metrics/DLQ/audit；不影响1.8经济预览与账号退出。有效无权限/关闭时不提供可用入口；直接路由显示明确无权限/未启用并可返回。网络发现失败可重试，不触发登录风暴；不改变全站401登录策略。

## 5 页面/验证/发布

三块：指标概览、失败/死信列表、操作审计。布局可滚动，长ID不撑破移动端；页面固定内部返回profile。使用文字解释投递和任务完成区别，不用绿色“全部健康”掩盖不可读状态；记录刷新时间。

相关测试覆盖能力/权限/禁用/错误、scope、未知数值、字符串ID、分页/去重/迟到响应、撤权与卸载、入口/路由/1.8导航回归。真实Chromium访问本地最终bundle、API隔离mock，验证桌面/横竖屏、非空fixture、分页/刷新、失败/禁用/无权限无数据请求以及零mutation；不当作生产双账号/真机验收。

自检后合develop，exact测试与本地制品摘要绑定，创建release/1.9.0（包含1.8祖先），通知用户可安排统一发布。保留release/1.8.0不改、不独立发布。本轮不自动授权flags/roles/生产DML/Provider或部署。

## 实现澄清

`ackLatencySeconds`按既有DTO为有限非负double，保留0.125等小数；计数仍须安全整数。分页cursor按canonical十进制非负Long字符串比较长度/字典序，hasMore时严格前进，不经Number。最终源码与验证绑定见integration.yaml。
