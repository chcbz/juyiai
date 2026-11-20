# 原生密议：代码改动与测试

<a id="coding-contract"></a>
> 历史实现依据，不再作为新增业务工具接线的编码指令。密议与事项议事的现行目标见[职责边界](../juyiting-skill-execution/responsibility-boundaries.md)；不以扩充 provider 注册表代替技能调用业务 API。

## 领域 API 调用边界（2026-11-20；固定源码与生产验收分列）

- 已验证候选：API `902dc32b`、Runtime `03c1a509`。`runNativeExecution` 在领域策略下才挂载 `/business-api.sock`；脚本只发送资源、动作和参数。`skill-conversation.mjs` 的可信调用方从当前执行取快照与租约，发送已认证请求；`ExecutionDomainController` 复核执行仍在运行，`InstalledDomainAuthority` 核对真实岗位与活动安装。Unix socket 识别的是沙箱，**不是**脚本文件名。脚本不能自报安装身份。
- 已实现：`native-installation-selection.mjs` 将多候选的选择与执行分离：已有唯一绑定的事项复用该绑定；存在多个候选时，选择阶段只看已验证的安装元数据，不加载包或业务 socket。模型可选一个安装或不用技能；用户不必选。结果只引用此次冻结的安装 ID，不接受路径、权限或自报摘要。实际执行前由 API 核对所选 ID 属于原候选集合、安装仍有效、会话未换代；`ExecutionSkillSelection` 绑定持久化后只向新隔离执行加载该包。普通说明技能也可选，但不挂业务 socket；选空时不挂包。候选不等于授权，不从多选快照直接签发领域调用。
- 性能与故障要求：单一既有绑定不增加模型轮次；多候选选择不在数据库事务中等待模型。重连复用同一请求的已提交绑定，不能跨请求缓存动态授权；授权撤销和版本切换后拒绝旧绑定，不重选后自动重放写入。模型选择耗时、用量与执行用量均按真实回执记录。构建测试与真实业务验收分开，以本任务部署和业务回执为准。
- 验收须覆盖同一 Agent 同时安装两个领域技能时的双向选择、未选择者不能调用、普通回复不取得业务权限、选择与执行间撤权/换版、重连无重复写入；真实密议与事项须各自读回，不用历史写入证明新链路。

## 历史设计（下文不作为开发指令）

以下行号定位 2026-11-19 工作区，落补丁以**方法名和现有语句**为准。API 以任务候选 `c1b96f486b0f337ef4411087becad01cc24390b2` 接续，Runtime 基线 `2c4e3909fa654970e581c9a233f573084a18be1d`。Java/JS 片段是拟改逻辑，标为「新增」的方法不是现有 API。

## 1. 密议准入：替换固定空技能

`ChatDeliberationService.java#173–250`，`admitPrivate`：保留 `known != null → replayPrivate`，不要把发现移动到重发判断之前。分三处改：

```java
// ① 在 observed=privateRuntime(...) 后、privateAdmissionTransaction.execute 前：
var prepared = privateCapabilities.prepare(ownerScope, intent.target(), observedFence);
// ② 在事务内 requirePrivateConversation、observed.equals(current) 之后：
var selection = privateCapabilities.freeze(prepared, currentFence);
// ③ 替换 snapshot.put("skills",List.of())；保留既有 parameters/inputs/outputs：
snapshot.put("skills", selection.nativeSelections());
selection.privateTools().ifPresent(tools -> snapshot.put("privateTools", tools));
```

- `PrivateNativeCapabilityLookup`（新增于 `jia-agent-api`）的 `prepare`/`freeze` 由 Agent 服务实现。`ownerScope` 从可信 sender 构造；`observedFence/currentFence` 由注册证明与当前会话核对得到，不从请求解包。`prepare` 批读当前安装/岗位及本代 Runtime 上报，`freeze` 在原准入事务内复核可变指针和权限。会话/主体校验失败拒绝；无技能返回空列表；仅可选目录依赖不可用时用空能力并在 `authorizedContext` 标记不可用。已冻结执行不得改快照。
- `InstalledSkillDescriptorService.readCurrent` 当前按 key 调 `findState`；不要从新路径循环调它。增加批量投影：按可信 scope+agent 集合读活动安装、归属与成功回执；与同 fence 的 enabled `INSTRUCTION` 按 installationId 建索引，校验 key/version/包摘要及 Runtime 安装/主机；同 key 不可唯一确定则不选。只选能签发原生 binding 的安装。结果按 key、installationId 排序。`skills` 每项形如 `{skill:{installationId,key,version,packageSha256,manifestSha256:null}}`，无 `providerBinding`。
- `PersonalWorkspaceExecutionServiceImpl.verifiedNativeSkills`（1418 起）及 `create`（1562–1572）：新 PRIVATE 分支传批量事实给核验和 `SkillManagementService` 的绑定构造；替换循环内逐项 `executionBinding(...)` 的查库部分，保留它的归属与摘要条件。批量获取事实后按既有稳定顺序生成每项绑定；无事务内冷包读取。`skillCommand` 的出队复核也使用批量读取。TASK 原有绑定及无技能路径不增加查询。

## 2. API→Runtime：能力位、命令字段和摘要

| 现有代码锚点 | 增改代码段 |
|---|---|
| `native-execution-runtime.mjs` 生成 native declaration（约247）；`TypedDeliberationDeclaration.nativeExecution`（74起）；`TypedDeliberationSessionRegistry.nativeScriptDeclared`（103起） | 在 native 声明中增可选 `privateBusinessToolsVersion:1`，仅具备该实现的 Runtime 声明；Java 解析、投影时保留数字 1。新增独立的当前 session 查询，不复用脚本策略位。未协商不发扩展。 |
| `PersonalWorkspaceExecutionServiceImpl` 命令枚举（635）、领取（750）、`skillCommand`（1641）、`resume`（1811） | 提取 `requireCommandCapabilities(scope,execution,skill)`：保留原脚本校验；**另行**在 snapshot 含 `privateTools` 时查 live fence 与声明。不要在 `requireNativeScriptSession` 对本地文件策略的早退之后接新逻辑。恢复执行/补做工作的分支要查能力；已提交成果的只读回执不触发重跑。 |
| `SkillExecutionService.Command`；`PersonalWorkspaceConversationRuntimeController` 命令响应 DTO（299起）；`skill-conversation.mjs` 的 `snapshotSha256` 映射（17–19）；`skill-executor.mjs:31` `parseSkillCommand` | 生产者从原 snapshot 带出 `privateTools`，无值省略，不序列化 null；JS 在白名单返回对象上**显式**保留验证后的扩展。仅 `PRIVATE + NATIVE_LOCAL_FILES_V1` 合法；版本、schema、重名或摘要错误拒绝命令，不退回无工具重跑。旧命令字节不变。 |

`privateTools = {version:1,tools:[{type:"function",name,description,inputSchema}],catalogSha256}`。按 name 的 UTF-16 顺序排序，不得与成果工具重名；只有非空业务目录才发此字段。API 在算原 snapshot 摘要之前加入扩展。目录 preimage **不含自己的摘要**：

```js
const preimage = {version: 1, tools: sortedTools}
const catalogSha256 = skillDigest(preimage) // Java：SHA-256(UTF-8(SkillCanonicalJson.write(preimage)))
// 测试向量（空目录仅用于编码测试）：
// {"tools":[],"version":1} → 8ace068ed2f4ef0dea8b8cea71e84bff8fcdbf629cf97ba2dd0bb9c0d7bdb8b6
```

## 3. Runtime：在一个原生 policy 中组合工具

`native-execution.mjs:11,29–33`：在参数中接 `callPrivateTool`，将 `nativeExecution:{...session.policy(),networkAccess}` 替换为下列组合。`agent-client.mjs:4229` 已用 `...request` 透传，不再组装一份目录。

```js
const local = session.policy()
const business = command.privateTools?.tools ?? []
const names = new Set(business.map(s => s.name)) // 构造前已校验两目录无重名
const nativeExecution = { ...local, networkAccess, tools: [...local.tools, ...business],
  callTool: ctx => {
    if (!names.has(ctx.tool)) return local.callTool(ctx)
    session.requireBoundTurn(ctx) // 从 native-artifact-session.mjs:42 起抽取共用绑定检查
    return callPrivateTool(ctx)
  }
}
```

`requireBoundTurn` 比对持久 `native-turn` 的 execution/thread/turn 和合法 callId，并 `checkActive()`；成果工具保留原有结果冻结与日志检查。业务调用在结果冻结或终态后不得新发。`AppServerAdapter` 仍只接 `nativeExecution`，不传第二个 `conversationTools`。已存在 thread 只按原布局摘要恢复，不替换目录、不启动新模型轮次重做写操作。

`skill-conversation.mjs:174–205` 的 `process`：在 `ctx.runNative` 注入闭包，固定 origin、execution/run，并从 `common()` 取**当前** fence 和快照摘要。`skill-usage-delivery.mjs:32` 的 `request` 扩展受限元数据参数，仅允许由 bridge 设置 `X-Request-Id`、`Idempotency-Key` 和取消信号；原调用签名/行为不变。复用认证 transport 的公共信封包装与 `readNativeJson`，不要双层包装；业务 4xx 读取已验证的错误码，不一概映射成传输未知。首次 POST 前持久化 requestId、callId 和输入摘要；连接中断只发 GET 对账。GET 无记录不证明写入未发生，保留未确认，不换键写。

## 4. 工具回调：接口、业务代码、事务

在 `runtime-client.mjs:skillConversationHttpScope` 和 `AgentRuntimeAuthenticationFilter.allowed` 两端精确登记同一资源的 POST/GET；不用前缀通配，不加入停机后的 usage/evidence 通道。保持 native-only 认证；Runtime 的 POST 校验 Idempotency-Key 与路径一致，GET 无 body，不接收 query/编码别名。仅入口可达不是执行授权，controller 仍须检查完整调用合同。

在 `PersonalWorkspaceConversationRuntimeController`（已有类前缀 `/internal/agent/executions`）新增两方法：

| 方法 | 协议及断言 |
|---|---|
| `POST /{executionId}/runs/{runId}/tool-calls/{callId}` | 公共 v1 JSON 请求；`data` 精确为 `{fence:{version,token},snapshotSha256,catalogSha256,threadId,turnId,tool,arguments}`，版本为十进制字符串。`Idempotency-Key=callId`、`X-Request-Id=requestId`；由认证主体和执行构造 scope。检查 PRIVATE、当前 lease、活跃回合、冻结目录成员，再交业务 provider。 |
| `GET` 同路径 | 无 body、URL 无 token；以当前读取身份、执行/会话可见性及工具的读权限返回原已提交写回执，不调用业务写。不可见或无记录 404。 |

成功 200/E0 返回原业务回执；字段/头不一致 400，无认证 401，无权 403/不可见 404，异参或前值冲突 409，业务内容不合法 422，依赖不可用 503。用原稳定业务码，不将失败封装成 HTTP 200。

`ModelConversationToolAdapter.java:56–125`：提取原 `catalog/call/withAuthority/admit` 可复用的 schema、岗位校验、参数解析和领域操作。新增原生 provider 方法 `descriptors(view)`、`authorize(ctx,op)`、`prepare(op,args)`、`applyAuthorized(prepared)`、`authorizeReceiptRead(ctx,tool)`，旧 `ConversationToolProvider` 合同不变。模式由 provider 显式注册，不从名字推断。首批只有四项：

| 工具 / 模式 | 精确参数 | 调用点 |
|---|---|---|
| `model_read_price` / READ | `model` | 原价目权限 → `prices.find`；缺项 `configured:false` |
| `model_add_price` / LOCAL_TRANSACTIONAL_WRITE | `model` | `source.read(model)` 在事务外；事务内原价目权限 → `prices.create`，原双档、来源、`CREATED/UNCHANGED` 不变 |
| `model_read_hero_binding` / READ | `personaCode` | 原绑定权限 → `hero(...).modelId()`，返回配置值 |
| `model_set_hero_binding` / LOCAL_TRANSACTIONAL_WRITE | `personaCode,expectedModel,model` | 原绑定权限 → 原相同值核对或 `bindings.changeModel(...)`，保留目标套餐检查与 CAS |

新增 `api/agent/jia-agent-mapper/src/main/resources/db/agent-private-tool-call-v1.sql`（显式迁移，不由启动执行）：

```sql
CREATE TABLE agent_private_tool_call_receipt (
  tenant_id VARCHAR(50) NOT NULL, client_id VARCHAR(50) NOT NULL, owner_jiacn VARCHAR(50) NOT NULL,
  execution_id VARCHAR(100) NOT NULL, run_id VARCHAR(100) NOT NULL, call_id VARCHAR(100) NOT NULL,
  tool_name VARCHAR(100) NOT NULL, input_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  receipt_json JSON NOT NULL, created_at BIGINT NOT NULL,
  PRIMARY KEY (tenant_id,client_id,owner_jiacn,execution_id,run_id,call_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
```

写服务控制流（伪代码；只读操作不插回执）：

```text
preflight: 验认证/执行范围/岗位；已提交则核读权限及输入摘要，直接返回原回执
prepared = provider.prepare(op,args)                  // 仅未命中；报价/冷包不持锁
同数据源事务，沿现有 native fence、conversation root、execution、岗位锁序：
  复核 lease、非终态、snapshot、目录、当前岗位及绑定安装
  old = receiptMapper.selectByKeyForUpdate(scope,executionId,runId,callId)
  if old: 摘要不符 → 409；否则核读权限并返回 old.receipt
  result = provider.applyAuthorized(prepared)          // 包括现有 MANDATORY create 或绑定 CAS
  receiptMapper.insert(key,tool,inputSha256,result,now)
事务提交后返回 result；任一步失败整笔回滚
```

`inputSha256` 对 `{executionId,runId,threadId,turnId,callId,snapshotSha256,catalogSha256,tool,arguments}` 作同一规范化摘要，**不含**租约 token、version、时间。不要在旧 `withAuthority` 的每次 `Boundary.execute` 写回执，不用 `REQUIRES_NEW` 或 `startEffect/WAITING_PROVIDER`。同回合加两条价目、改一次绑定按三笔独立操作核对。

## 5. 定向测试：fixture、动作、断言

| 测试落点 | 增加的用例及断言 |
|---|---|
| `ChatPrivateNativeAdmissionTest.firstSendCreatesOnlyOneNativeExecutionAndNoTaskOrChatOutbox` 及 `nullConversationReplayReturnsOriginalWithoutReadinessOrMaterialRediscovery` | 第一条消息装配一次；重复同 requestId 不再调用 `prepare`。空目录保留纯文本；旧安装/跨岗位过滤；持久快照中只有已核验版本，无 CHAT dispatch。`ChatPrivateNativeAdmissionMySqlTest` 验并发同键仅一条执行。 |
| `TypedDeliberationDeclarationTest`、`NativeSkillScriptSessionLookupImplTest` 同模块；命令/lease/resume 服务用例 | 声明缺失、合法 1、未知版本、换实例。新 API+旧 Runtime 不派带扩展命令；按 ID 直领也拒绝。旧 API+新 Runtime 的无扩展 fixture 序列化不变。TASK、非本地策略、摘要错、重名分别拒绝非法扩展。 |
| `test/skill-conversation.test.mjs`、`test/native-execution.test.mjs` | 用固定非空目录交叉验证 Java/JS 摘要；捕获 `policy.tools` 和 fetch 请求，断言旧成果工具仍在、同一回合业务读后可 `result_propose`，认证头/信封各一次，错 turn/lease 不发 POST，材料不扩大工具集合；断线后仅 GET。原无业务工具用例保留。 |
| `ModelConversationToolsTest`；`positionSkillsTest` 下新增真实 MySQL 用例 `PrivateNativeToolReceiptMySqlTest` | 同键并发只写一次、同键异参 409；令 receipt insert 抛错，查价目版本/当前指针或目标绑定均未改；提交后模拟响应丢失，GET 返回原结果；报价准备后撤职，不产生业务变更或回执。读价与读绑定权限不互借。 |
| 批量 DAO/集成性能 fixture | 同一候选、相同消息，用 0、1、N、2N 个安装分别计准入/出队 SQL 和 Runtime RPC；无逐技能 DB/网络往返、无锁内报价或冷包读取。分冷/热和连续回合记录样本量、准入及首字 P50/P95、锁时长、schema 字节/提示 token；Runtime 本地校验/发现单列，不用 mock 延迟当实测。 |
| 真实前端密议 | 与吴用一次发起两条价目录入及孙二娘改绑；逐项对指定 BaseLLM 中文源、输入/输出/缓存价格及档位，读回两条版本和 `configuredModel`。缺价、无套餐、仅部分成功分别如实显示；不以回复文本替代工具回执。 |
