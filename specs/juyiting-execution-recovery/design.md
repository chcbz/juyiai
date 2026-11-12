# 冻结契约与边界

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：既有执行回执只读核对与新方案恢复。**

### 最小责任链
API保有执行/成果事实；Runtime恢复自身新方案状态；Web展示已知/未知与可操作范围。

通过原请求/执行标识读取→核对已有回执→显示权威状态；仅沿获准新方案恢复入口处理可恢复事实。

### 实施约束
不把UNKNOWN变失败重跑；旧协议已退役执行/恢复不恢复；完成回执不等于用户验收，不凭缺字段猜执行成功。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## API（JWT owner-only，private/no-store）
- `GET /agent/personal-workspace/executions?limit=20&beforeCreatedAt=<ms>&beforeExecutionId=<id>`：游标两项必须同时有或同时无；limit 1–100 为分页长度，不是性能取消阈值。按 created_at DESC、execution_id 字节序 DESC，以 limit+1 判断下一页。
- 返回 `{items:[{executionId,targetAgentId,state,outputContentMimeType,createdAt}],nextCursor:{createdAt,executionId}|null}`。不返回私密需求/输入正文/运行凭证；无条目不等于加载失败。
- `GET /agent/personal-workspace/executions/request`，以 `Idempotency-Key` header 查原请求：返回现有 ExecutionView，未查到404/EXECUTION_NOT_FOUND。只读，绝不调用 create。404不能证明在途POST以后不会提交。
- tenant/client/owner 严格匹配，数据库大小写/空白折叠不能扩大作用域；保留服务层防御校验。沿用现有400/404/503错误合同。
- 既有 `POST /internal/agent/tasks/{taskId}/runs/{runId}/failure` 仅补 runtime filter 的精确允许路径；仍验证 native-only、无Origin、有效runtime token、agent/runtime/owner，浏览器JWT不获得能力。

## 前端
- 提交后在当前交付台显示真实回执、执行者、编号与状态；QUEUED只解释为已受理且等待结果，不推断模型运行阶段。
- 当前在途/未知意图不允许再次普通提交；程序层防连击，不仅禁用按钮。传输未知查询同一个幂等键，不自动重发。
- 历史从服务端读取并可分页/选中恢复；选中/轮询/加载并发不得用旧回包覆盖新状态；身份变更立即清理。
- 仅可按已确认owner/client命名空间保存小型待核对key/执行ID；不能保存令牌、密码、私密正文或文件内容。服务端身份校验不依赖浏览器缓存。
- 关闭页面不是取消后台执行。文件详情返回真实select结果，才能从列表打开。

## 风险、发布、兼容
无DDL、无生产DML、无运行重派发。先验证API兼容现有前端，再发布配套前端；旧API上历史404必须呈现暂不可恢复，不伪报空。当地本地发布授权有效，不触发Flow；精确SHA、相关测试、制品哈希、互斥与实际健康仍必须保留。已有失败记录修复必须另有精确恢复授权，不能因上线而推导。
