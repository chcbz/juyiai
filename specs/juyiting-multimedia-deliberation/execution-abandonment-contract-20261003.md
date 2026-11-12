# 已开始但未交付执行：用户放弃接收合同

状态：API/Web 1.13.60 已发布；原417请求通过真实UI放弃并只读回查成功。没有鸟图交付，整体34项仍未验收。该能力不代替 result-only 恢复、真实鸟图交付或完整34项验收。

## 目的与语义

- 用户明确放弃**本轮尚未交付的结果**，收敛悬赏议事中永久 RUNNING 的 request/EXECUTE step/execution link。
- 不证明 Agent/Provider 已停止，不证明其它主机没有副本，不退款，不撤销已消费 START，不恢复/删除付费 claim，不生成新 intent。
- 服务端已有任一 output 行（包括 STAGED、COMMITTED）时拒绝放弃，应先恢复/读取已有成果。原417没有可恢复字节属于历史事实，不硬编码到服务。
- 底层 execution 复用既有 `FAILED/AGENT_DELIVERY_FAILED`（交付未完成，不是“Provider 未执行”）；精确原因 `OWNER_ABANDONED_UNDELIVERED` 写入事务内审计回执与明确 failure_message。已 FAILED 则保留既有 failure_code/message/failed_at。
- **无需放宽数据库 CHECK、无需新表、无生产 DML 修复。** 原 execution CHECK 仅允许通用交付失败码；MySQL 红测确认这一合同。独立具体业务原因保存在不可变 journal，不伪造新的运行时失败码。

## HTTP

`POST /chat/conversations/{conversationId}/requests/{requestId}/abandon-execution`

- 身份来自既有 TenantScopeResolver/HumanSenderIdentityResolver，body 禁止身份字段。
- Header `Idempotency-Key`：8–100字符，允许字母数字及 `._~:/+-`，同会话作用域中一个 key 只对应一个命令。
- 严格 JSON：仅以下五个字符串字段；拒绝重复键、额外键、缺字段、数值版本、尾随 JSON。

```json
{
  "stepId": "<exact-step-id>",
  "executionId": "<exact-execution-id>",
  "expectedRequestStateVersion": "0",
  "expectedStepStateVersion": "2",
  "reason": "OWNER_ABANDONED_UNDELIVERED"
}
```

200 使用既有 JsonResult envelope；`data` 是：

```json
{
  "operationId": "<scoped-sha256>",
  "conversationId": "<id>",
  "requestId": "<id>",
  "stepId": "<id>",
  "executionId": "<id>",
  "state": "CANCELLED",
  "requestStateVersion": "1",
  "stepStateVersion": "3",
  "reason": "OWNER_ABANDONED_UNDELIVERED",
  "providerAlreadyStarted": true,
  "providerStopped": false,
  "paidFactsPreserved": true
}
```

`GET` 同一路径、同一 Idempotency-Key：仅查询原回执，不重复终止，更不执行 Provider。

错误：400 INVALID_REQUEST；404 NOT_FOUND_OR_FORBIDDEN（不存在与无权不区分）；409 CONFLICT（版本/状态/已有成果/同key异命令）；503 UNAVAILABLE。响应 no-store/nosniff，未知异常不返回数据库详情。GET404 **不能证明**并发 POST 未提交；保留原key与命令继续核对，不生成新key。

## 锁、事务与幂等

1. 非锁定索引读取仅用于定位任务根；锁序：owner-scoped task root → execution → conversation → request/step/link → journal。
2. 当前 owner/client/tenant、任务目标、assignment、grant绑定、conversation generation/任务scope/目标ACL、intent到execution的 `conv_ + SHA256(intentId)` 关系必须精确一致。
3. READ_COMMITTED + 锁后当前读取。锁前快照只核对不可变绑定，不以状态/版本变化拒绝合法同key并发重放。
4. 优先读取同key已提交回执并核对命令摘要与当前绑定。仅新操作检查 RUNNING/CAS、已START且execution处于QUEUED或FAILED、无output行。
5. 同一事务执行 execution终态、step/link/request CANCELLED及版本递增、唯一 `chat_conversation_event` 审计与序号。任何一步失败全部回滚。
6. 只有 afterCommit 推送 `execution_abandoned`；审计 payload含 type/conversationId/requestId/stepId/commandDigest/receipt。实时帧另含eventId/eventSequence/eventVersion。断线重放读journal；不按事件内容重新执行终止。
7. 保留 START时间/版本、传输lease、grant/consent/operation等原事实；FAILED状态使原fence不能晚到提交。与实际stage/commit共用任务根互斥，不抢占。

**已核实的重要状态语义**：CONVERSATION stage成功时 output是STAGED，但execution仍可能QUEUED。不能只看execution_state，也不能把 OUTPUT_STAGED 当作唯一安全判断。

## 前端实施要求（源码已实现，正式发布待核验）

- 明确展示“放弃本轮未交付结果”，说明“不会撤销已发生的生成费用，也不表示已停止服务商执行”。不得把它替换为无提示的普通取消。
- 使用当前明确request/step/execution和服务端版本，不依赖隐式选中Agent。身份/会话切换后禁止旧响应更新新界面。
- 请求中的原key/命令按身份作用域保留；POST未知结果只以原key GET核对，不自动重放生图、点将或创建授权。
- 收到receipt/事件后读取服务端request投影；SSE只是刷新提示，不以孤立帧伪造交付完成。终态显示“本轮结果已放弃”，继续需求需新明确意图。
- 完成后台合同不代表原417已经终止；通过正式业务入口执行后另存审计证据。

## 验证与边界

候选测试覆盖真实MySQL生产DDL、执行/journal MyBatis、事务回滚、根锁并发、真实runtime stage/commit及旧fence拒绝；任务根和conversation DAO使用隔离表上的scoped locking SQL适配，非生产整机测试。HTTP测试覆盖严格JSON和身份解析，不代替网关/线上验收。

发布前还需：前端未知结果恢复/事件刷新、集成回归及版本制品安装健康；原417业务终止与后续result-only恢复、真正Agent生图→展示预览下载→可选保存→交付验收仍独立未完成。


## 2026-10-03 12:19 源码验收记录（不是线上验收）

- API feature `codex/bounty-execution-termination-main-20261003`：commit `79bd61966cf59ba31d1d1507c4cf0d20f19d27f2` / tree `3ade5d77fb690f3d5d914c613ab5b61cb0c1fa79`，remote readback一致。仅chat service/controller、两测试及定向sourceSet共五路径。
- `:chat:jia-chat-service:mmdExecutionTermination`：**22 passed / 0 failed / 0 skipped**；17真实隔离MySQL + 5 Controller。API测试沿用local_user_authorized例外，经orchestrator串行；不作为Flow或前端生产构建证据。
- v3测试保全execution上原consent/operation/inputSnapshot/START绑定、重放回执及schema重启；不冒充真实Provider/消费事务端到端验收。终止后旧runtime提交被拒绝，未调用authority重新准入。
- 首次编译前缺少既有publishing占位配置；随后修复新测试void Supplier用法。首次SQL运行发现execution failure CHECK与stage状态假设错误；均保留原始失败日志并按真实合同修正，未关闭CHECK/跳过测试。
- 不触发Flow、不修改线上配置、不调用Provider、不终止原417、不合develop。完整多媒体验收仍未完成。
- 证据：`integration-evidence-20260928/execution-abandonment-source-20261003/source-result.json`；Main原日志 `/var/tmp/cyf-mmd-execution-termination-main-20261003/`。
- 下一步唯一集成候选纳入Web明确放弃入口、原key查询恢复、事件触发权威readback，再按版本发布；不要为了单纯新增API入口重复发布前端。

## 2026-10-03 12:54 Web 源码验收（不是上线或整体验收）

- Web `codex/bounty-execution-abandonment-web-20261003`：`db48052e0d812c3ff6678cc79e0803dfa748fb4b` / tree `c265a199300fb0f77f3cebd949f25bd5078127c0`，feature remote readback一致；九个路径，未更改voice/context/CAS合同。
- 真实SFC明确告知不可撤销已发生费用、不是停止Provider；原intent先存sessionStorage并readback再POST，未知结果保原key/body，只查询或显式继续原操作，不重放生成。身份/会话变更取消自己的传输并丢弃旧回执。
- API79bd exact22项证据复用；Web十个相关测试文件 **141 passing/0 failing/0 pending**（轻量本地辅助，不代替Flow）；包括实际createApi/useHttp/fetch、真实SFC DOM与真实SSE parser。非法foreign SSE继续使用既有“拒绝帧并重读当前授权会话”恢复，不按foreign payload改状态。
- 新增与直接相关文件定向ESLint通过；既有集成文件同baseline对比无新增诊断，原188+2+3项未伪造全绿。
- system Chromium133实际900/390 viewport，idle/unknown四组截图与尺寸通过、已人工查看截图；使用真实SFC/composable/CSS与禁止网络的HTTP adapter、模拟请求。不是全产品、Provider或线上验收。自有预览和浏览器均关闭。
- 组件诊断初次入口误放在Vite SPA fallback之后，及直引第二份Vue runtime的问题均已归因修正；不是产品通过证据。测试红测/修正日志保留。
- API已FF推develop79bd；Web暂留feature，等待API1.13.60无迁移/无配置变更的exact构建安装，再合Web develop走Flow4403172唯一同Run测试/构建/制品/部署。
- 未操作原417、0Provider、0本地前端生产构建；result-only恢复及完整鸟图34项验收仍未完成。源码证据见 `integration-evidence-20260928/execution-abandonment-web-source-20261003/`。

## 2026-10-03 13:30 正式发布与原417业务验证

- API79bd与Webdb48052已非force合入各自develop，冻结`release/1.13.60`并remote readback一致。API依既有local_user_authorized例外，经orchestrator正常bootJar图构建与恢复式安装；JAR `b18663ff5573972f1bd612914b5e0e707334f65cfa37af01068f4e8cf5119c39`、PID4018216、Main独立scope，健康UP；无schema/config变更。
- Web只使用Flow4403172/Run161：实际checkout `db48052e0d812c3ff6678cc79e0803dfa748fb4b`，**2952 passing / 2 pending / 0 failing**，scan/build/deploy全部SUCCESS，部署单70600370/1机healthy。同Run制品SHA256 `97d8c3c06f28fa5ca848315da6f3e2abb6688dd560e55925b35ad374fad42b48`；364线上文件一致，浏览器实际入口/Hall JS/CSS/SW四文件同摘要。未本地构建前端、未改Flow配置、三个既有UI flag保留。
- 原Main浏览器profile正常导航更新，没有清缓存；原认证会话跳回登录后通过真实测试账号登录控件恢复。桌面/实际390viewport已检查，新增提示与Composer均可见、没有横向溢出；mic/settings仍真实18×18非空SVG，未录音或调用Provider。
- 原测试417通过**一次可见按钮**提交放弃，HTTP200，request/step版本3→4并CANCELLED。关闭/重开面板只恢复原intent，没有自动POST；再点“查询原操作结果”，同key GET200，回执逐字段一致。操作 `dde1357bc31ccfbb9934c305005faea5cdb6802fad8a888b2c1b5b8f35dd4b10`，`paidFactsPreserved=true`、`providerAlreadyStarted=true`、`providerStopped=false`。没有直接HTTP POST或生产SQL DML，没有重放原START/生成。
- 服务端目录权威读回CANCELLED v4，前端不再显示原轮等待忙碌；没有把孤立SSE帧当成果，也没有完成任务验收。旧PNG没有恢复，鸟图交付仍空。
- 证据目录：`integration-evidence-20260928/release-1.13.60/`。完整多媒体34项、真实新一轮生图/改图/交付与result-only传输恢复仍需继续；不能把本节成功当整体验收。
