# 多轮 owner HTTP v1.1 补充：只读 current context

日期：2026-10-01。**Main 冻结的追加接口/前后端施工合同；API Owner 源码自检与实际验证仍待完成。** 不覆盖、不重写 [v1](controlled-image-followup-owner-contract-v1.md) 的六端点、摘要、授权、事务及 72 路径矩阵，不增加执行权限。长期完整产品范围保持原样。

## 1. 实际缺口与决策

Web `8b8c951d` 当前刷新后没有一个权威读取闭合完整 tuple：初始点将投影不是当前 baseline grant；旧 request 或成果卡不能提供完整 generation/task/assignment/requirement/target。preview 已要求这些 expected 字段，不能以 preview 自己引导读取，不能猜版本 `"1"` 或从 hidden selectedAgent 拼权威 target。

新增唯一 Chat-owned 查询：

```text
GET /chat/conversations/{conversationId}/interactions/context
```

现用户 JWT/认证入口解析 tenant/client/owner，与 v1 相同；无 query、无 body、无 `Idempotency-Key` 要求。拒绝额外 query/body（400），不把用户传入 scope/target 当可信事实。成功和错误都使用现有 `JsonResult`；响应 `Cache-Control: private, no-store`，不进浏览器/共享缓存。

## 2. 精确成功投影

`JsonResult.data` **仅**以下九个字段：

```json
{
  "schemaVersion": 1,
  "conversationId": "conversation_1",
  "conversationGeneration": "1",
  "taskId": "task_1",
  "targetAgentId": "agent_1",
  "taskVersion": "0",
  "assignmentRevision": "0",
  "baselineGrantVersion": "1",
  "requirementRevision": "1"
}
```

schemaVersion=1 是此只读投影自己的版本，**不是** schema-3 interaction，也不是候选计划中的 schemaVersion=3。三个 ID 均为 string，按 v1 各自 ID 验证域；五个版本字段（含 conversationGeneration）均为 canonical decimal string，不是 JS number。`taskVersion/assignmentRevision >= 0`；`conversationGeneration/baselineGrantVersion/requirementRevision >= 1`。上界沿用 v1 及对应源领域已经支持的范围，不新增任意门槛；错误 wire、前导零、`+0`、溢出、缺字段不供 Web 继续。

不返回 grantId、consentId、费用 locator、Provider binding/model/policy、credential、源字节、路径、asset lineage、私有 snapshot 或工具清单；这些分别由对应 v1 preview/source/runtime/资产接口提供。

## 3. 当前事实与一致性

服务器从 exact owner/client/tenant 的当前悬赏 conversation → 当前 bounty binding → task root/assignment → ACTIVE/current baseline grant → 当前 confirmed requirement 得到全部字段。必须同时成立：

- 会话是仍有效的本任务悬赏议事，生命周期 generation 当前且目标唯一。
- 当前 binding 指向此 conversation，task/assignment/target 与会话及任务根一致；不返回旧 assignment 的 tuple。
- baseline grant 属于同 scope/task/target/assignment、仍 ACTIVE 且 current，其 requirementRevision 对应当前 confirmed requirement。
- 任务仍允许后续办理；已完成/撤销/重新点将不能作为新执行上下文。

不能先任意读八个表字段后拼出未共存过的 tuple。实现可以复用既有根锁/按既有顺序 task-root→grant→binding→conversation 的一致读取，或事务一致快照并验证当前事实；若采用锁不得制造逆序，锁互斥等待而非抢占/超时 SLO 失败。纯 SELECT/SELECT FOR UPDATE 可以用于一致性；**业务零写**，不更新 updated_at/乐观版本，不修复/bootstrap/bind/grant/requirement。

GET 只读资料元数据验证，不读取/物化任何参考图/asset 的内容字节。不调用模型/Provider，不 reserve，不创建 consent/operationGrant/request/step/message/outbox/execution/run/command/START，不刷新租约，不修改初始 operations/version/inputScope/derived flag/费用 locator。

## 4. 错误语义

与 v1 前缀/envelope 一致：

| HTTP | code / 语义 |
| --- | --- |
| 400 | `BOUNTY_FOLLOWUP_V3_INVALID_REQUEST`，路径 ID 或多余 query/body 无效 |
| 401 | 沿用现标准鉴权错误，不伪造 v3 权限 |
| 404 | `BOUNTY_FOLLOWUP_V3_NOT_FOUND_OR_FORBIDDEN`，不属于 owner/client/tenant，或缺少可操作的当前悬赏/ACTIVE grant；不泄露其他 scope 是否存在 |
| 409 | `BOUNTY_FOLLOWUP_V3_CONFLICT`，本 scope 内已知会话的当前 binding/assignment/generation/requirement/任务状态漂移，不能组装一致 tuple |
| 503 | `BOUNTY_FOLLOWUP_V3_UNAVAILABLE`，真实存储/必要事实读取不可用；性能慢/SLO 不构成此错误 |

失败没有部分 tuple，不能回旧 schema2 或 `/chat/stream` 执行，也不换 key/补 POST。部署开关关闭或不支持接口时维持现功能关闭的明确行为；前端不将缺失 GET 当执行就绪。

## 5. 前端唯一用途与 fence

Web 每个新 EXECUTE 先读当前投影，确认 exact conversation/task/target 与 Hall 当前业务选择一致，组装 v1 preview 的 expected 字段。**context 不是执行授权**：仍须 preview→展示服务器实际 preview→用户明确 acknowledgement→独立 issue key→原 final key admit。任何阶段都服务端再验证，GET 后变化 409 即停止该意图，不自动重新同意。

在 await 前 capture identity/auth generation、Hall 会话/task/target、所选 refs/本地 intent revision 和 disposal fence；迟到响应不显示/persist/签发/执行，不改变用户当前选中任务。收到合法 current tuple 后才能建立新意图；不能用它悄悄改写已有原-key恢复记录。两个原-key GET 继续用于恢复已经 issue/admit 的事实，不依赖 context GET 替代原键读取。

## 6. 精确施工范围与自检

API仍限 v1 的 72 路径；优先在已有允许路径新增 read-only grant current projection、Chat preview/context service 方法、V3 wire/controller GET，以及其既有测试文件。没有授权新增其他模块/目录、修改语音或放宽 runtime filter。若实码必须新增路径，由 Owner 提供原因/证据后另扩精确矩阵。

必需真实测试（此文均 NOT_RUN）：

1. 合法 owner exact tuple；task/assignment `"0"` 不被误拒；decimal string 严格域。
2. owner/client/tenant 不同与其他 conversation 同响应 owner-safe 404。
3. current binding/generation/target/assignment/requirement/终态漂移不能成功拼 tuple。
4. 控制器 query/body拒绝、JsonResult/no-store 与新旧 MVC 同时加载映射无歧义。
5. DB 前后业务行计数/版本/updated_at 相等；outbox/consent/execution/START/Provider/bytes 全为0。
6. 与重派/撤权并发只返回当时真实一致 tuple 或 typed conflict，无越权/写入。
7. Web GET 后 context/selection/identity 变化抑制所有后续 POST；不默认版本1、不以context为权限。
8. 原-key恢复不自动 GET 后重写原正文/授权，未知/404/409/503恢复零 POST。

本补充只闭合 EXECUTE 的 pre-preview 元数据缺口；不把它当 DISCUSSION refs、AVAILABLE/INSPECT、澄清续办、全媒体、多 lineage、双接应和34产品用例完成。无需独立 Reviewer，责任 Owner 自检后提交 exact child，实际组合与版本发布由 Main 按既定授权推进。
