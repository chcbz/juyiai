# 通用资料原子创建合同 v2（2026-10-03）

状态：M1创建子流程已实施并有源码自检；不是线上已可用。优先产品方向仍为`unified-materials-correction-20261003.md`。本合同只固定普通需求创建/恢复，不把尚待实现的通用点将、会话按需分派宣称完成。

## 1. HTTP / DTO

- `POST /agent/tasks/creation-operations/v2`：JWT当前tenant/client/owner；单一`Idempotency-Key`，禁止query/重复header。`Content-Type: application/json`；严格拒绝重复JSON字段、尾随token、未知字段。
- 正文允许`title`（必填非空）、`description`、`requiredAbilities`、`reward`（沿普通创建既有presence/null语义），以及可选`attachments`。资料省略或`[]`均可；显式null拒绝。
- `attachments`最多32项，继承已有JSON数组数据库CHECK的实际容量。每项**恰为**`{fileId:string, version:positive Java int}`。不接收purpose、MIME、hash、owner、URL、path、provider/model/operation或执行授权。相同fileId/version重复拒绝；不同版本可独立引用。按fileId UTF-8字节、version升序规范化，选择顺序不形成新意图。
- 初次201、同键同body重放200；均`Cache-Control: private, no-store`。
- 响应：`{schemaVersion:2, operationId, taskId, requirementRevision:1, state:"COMMITTED", attachments:[{fileId,version}], task}`。无业务参考图字段，也不返回内部关系role。
- `GET /agent/tasks/creation-operations/v2/request`：相同JWT/单一原key，无query，纯读恢复同一receipt。404不证明在途POST未发生，Web不得创建新key/自动重发执行。
- 400 BAD_REQUEST；401 UNAUTHENTICATED；403 TASK_CREATION_FORBIDDEN；404 TASK_CREATION_NOT_FOUND；409 IDEMPOTENCY_CONFLICT（含同一key的合同版本不符）；503 TASK_CREATION_UNAVAILABLE。错误不列他人文件信息。

## 2. 复用既有事务与存储，不新增文件体系或第二创建引擎

同一REQUIRED事务内，既有operation reserve+lock→task/原始需求snapshot→全部精确版本task-link→COMMITTED。任何资料失效、越权、link写入或最终CAS失败，整个需求和所有关联回滚。创建不点将、不建立执行/Provider授权，不读取正文到Agent。

资料选择v2以私有workspace的owner/client/tenant及固定file/version为真相；要求ACTIVE及该身份可访问的精确版本，不限定JPEG/PNG。文件名称/MIME/hash/长度由服务端既有文件版本读取，后续授权manifest再固定引用/摘要；客户端不能伪造。内部沿既有通用task-link `INPUT`角色关联，但这不决定某项是参考图，不意味着进入绘图或授权外部执行。后续Agent按需求决定用途。

复用`agent_task_creation_operation`，不ALTER旧表、不改原数组CHECK、不把数组改成envelope、不重写历史行。**显式持久版本标签**使用服务端生成的、不允许客户端赋值的operationId类型前缀：旧v1为`atco_`，新v2为`atco2_`；后缀仍随机UUID32hex。它是协议资源类型标签，不从MIME、是否有附件、数组第一项、当前task状态猜版本。空附件也能明确恢复版本。DB标识字段现有100字符容量足够。

v1持久数组沿旧`{fileId,version,purpose:"REFERENCE"}`；v2数组为`{fileId,version}`。读时先由持久资源类型选严格解析器，再验证字段/类型/唯一性/规范顺序；不宽松混读。类型标签为不可变receipt元数据，不能因切换页面重写。

## 3. 版本标识、幂等和未完成请求保护

- 旧POST/GET路由、JPEG/PNG限定、`inputRefs/purpose:REFERENCE`、schemaVersion1和hash字节序不变，旧Web未知意图仍走旧GET。
- v2 hash域固定`AGENT_TASK_CREATION_OPERATION_V2`；v1仍`AGENT_TASK_CREATION_OPERATION_V1`，标题/描述保留原文和可选字段presence语义。v2在内部hash中用INPUT角色；业务JSON不传该字段。
- 两版共用owner隔离的key唯一索引。同key跨版POST冲突而不是再创建；GET调用错误版本也409，尤其覆盖空附件，不能把v1receipt当v2已成功。
- 无DDL迁移、无历史回填。回退到不支持v2的API时，新Web必须保留v2原意图，不能降级为旧POST或新key创建；旧API不提供v2路由。升级回来后按原key恢复。旧v1操作与其恢复仍可用。
- 资金悬赏仍不经普通创建接口，不推导任何额外付费授权。

## 4. 必需回归与后续依赖

HTTP：真实Controller序列化，2字段资料/空选/严格字段、身份与no-store、重放/GET、v1不接收v2字段。服务：图+PDF+音频+文本混选、固定旧版本、重复/越权/回收站拒绝、同键换正文/资料/版本冲突、空选跨合同冲突、读无写。事务：第二份资料失败/最终CAS失败时task/snapshot/event/operation/link一并回滚；并发同键只有一份需求。MySQL仍需实际隔离库验证JSON重排与索引语义，不由H2替代。

Web已接通：BountyPanel与Overview共用通用selector和v2原子创建，新草稿不再走QuickMatter先建任务后逐份link链路。历史未完成意图只保留必要的原键保护，不新增旧业务入口或扩展兼容工程。下一步接通点将后全部资料目录、Agent按需INSPECT/EXECUTE及FAILED终态。上述链路未完成前，不将本合同或局部绿测标为原34项/UM整体验收完成。
