# 用户名编码完整性与聊天发送者身份治理详设

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：用户名编码与权威发送者身份。**

### 最小责任链
OAuth适配器正确解码；账户服务保护主数据；聊天入口解析可信发送者；Web统一展示。

外部字节按协议解码→来源校验→不覆盖已有好值→服务端确定发送者→安全展示。

### 实施约束
不对所有西文高位字节强制转码；不可逆历史值不猜补；生产修复不因文档更新自动执行；客户端名称不授予身份。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 1. 设计摘要

彻底解决方案不是“再加一个乱码正则”，而是建立三条不可绕过的边界：

1. **字节边界**：外部 JSON 先保持为 bytes，再严格解码 UTF-8；错误不能静默替换或按 Latin-1 猜测。
2. **身份边界**：发送者身份来自认证上下文和服务器实体，不能来自浏览器/Agent payload 的显示字段。
3. **数据边界**：历史修复只处理有证据的可逆值；所有写入均 CAS、readback、可条件回滚。

前端共享 helper 只承担兼容展示，不再成为身份或数据正确性的来源。

## 2. 当前数据流与故障树

### 2.1 OAuth 污染链

```text
Provider UTF-8 JSON bytes
  -> OauthExternalHttpClient: RestTemplate.exchange(..., String.class)
  -> 缺 charset 时按 String converter 默认字符集解释
  -> DTO.nickname 已变成 raw Latin-1 mojibake
  -> OauthController.setNickname(...)
  -> UserService.upsert(...)
     -> user_info.nickname
     -> LDAP nickname
  -> /user/my -> globalStore.user.nickname
```

公共 `RestTemplateConfig` 已设置 UTF-8，但 OAuth 专用 Client 自行 `new RestTemplate(requestFactory)`，没有继承 converter 配置。OAuth 专用 Client 不应直接改成共享 `RestTemplate`，因为它有意不传播普通 API 的 performance deadline interceptor；正确做法是在专用 Client 内明确 bytes→UTF-8 边界。

### 2.2 聊天固化与二次破坏

```text
globalStore.user.nickname (可能已污染)
  -> Web resolveHallUserSenderName
  -> 先删除 C0/C1 control，丢失可逆字节
  -> 本地乐观消息显示碎片乱码
  -> POST /chat/stream.senderName
  -> ChatController Advisor context / JuyitingAgentRelayService
  -> Agent protocol payload + chat_message.sender_name + metadata.senderName
  -> 历史加载再次显示
```

普通聊天也发送客户端构造的 sender 字段。Agent WebSocket 虽认证了 agentId，但保存消息和 delta 事件仍从 payload 读取 `senderName`/`agentName`。

### 2.3 为什么此前修复不完整

- `UserProfile.vue` 与 `JuyiHall.vue` 各自加入了可逆 mojibake 兼容恢复。
- `hallConversationMessages.js` 仍只有控制字符删除，且处理顺序错误。
- 页面存在多套 helper，无法保证同值同显示。
- 烟测只覆盖若干中文乱码片段，未覆盖 Latin-1+C1 删除后的 `éæ\u00A0è¶` 形态。
- 账户显示修复没有阻止 OAuth 再污染，也没有治理聊天服务对客户端身份字段的信任。

## 3. 信任模型与威胁模型

### 3.1 可信来源

| 数据 | 权威来源 |
| --- | --- |
| 当前人类用户 | `EsContext.jiacn` + `EsContext.clientId`，再查 `UserService.findByJiacn()` |
| Agent 主体 | 已认证 WebSocket session 中登记且授权的 `agentId` |
| Agent 显示名 | 对应 `AgentRuntimeDTO.name`，其次 `personaName`，最后 `agentId` |
| 人类显示名 | 服务器用户实体中的有效 nickname，之后 username/context username/jiacn |
| 是否为当前用户 | 服务器返回的稳定 `jiacn`/owner identity 与当前认证身份比较 |

### 3.2 不可信来源

- HTTP request body 的 `senderName`、`senderType`。
- request metadata 中的 `senderName`、`senderType`。
- Agent WebSocket payload 的 `senderName`、`agentName`。
- 仅由前端展示文本推导的用户身份。
- 任何仅凭“看起来像乱码”得出的不可逆姓名猜测。

### 3.3 主要威胁

- 编码降级导致持久化污染。
- 第三方重复登录覆盖用户已修正昵称。
- 浏览器伪造 Agent/其他用户显示名。
- Agent session 伪造另一个 Agent 的显示名。
- 兼容 helper 误改合法西文名字。
- 批量修复误伤或覆盖并发更新。
- 日志、manifest 泄露昵称、token 或 provider body。

## 4. OAuth 响应严格 UTF-8 设计

### 4.1 接口调整

`OauthExternalHttpClient` 保持专用 request factory、现有网络超时和“事务外调用”约束，但将响应实体改为 bytes：

```java
ResponseEntity<byte[]> exchangeBytes(
    String url, HttpMethod method, HttpEntity<?> entity);

<T> T exchangeJson(
    String url, HttpMethod method, HttpEntity<?> entity, Class<T> responseType);
```

推荐 `exchangeJson` 内部流程：

1. `restTemplate.exchange(..., byte[].class)`。
2. 验证 2xx；错误信息不包含 URL query、response body、token。
3. body 为 null 时按空响应处理。
4. 仅移除开头可选 UTF-8 BOM `EF BB BF`。
5. 使用 `StandardCharsets.UTF_8.newDecoder()`，并设置：
   - `onMalformedInput(CodingErrorAction.REPORT)`；
   - `onUnmappableCharacter(CodingErrorAction.REPORT)`。
6. 严格解码成功后再调用 `JsonUtil.fromJson`。
7. 解码或 JSON 解析失败，抛出只含 provider/stage 分类的安全异常。

跨开放系统的 JSON 按 UTF-8 处理；不能因为 provider 漏写 `charset` 就回退 Latin-1。Spring `StringHttpMessageConverter` 的默认字符集行为也是本次规避的直接原因。

### 4.2 错误与可用性

- **Token 响应整体 malformed UTF-8/JSON**：无法安全提取 token，当前登录安全失败。
- **必需 profile 响应整体 malformed**：无法确认 provider identity，安全失败。
- **JSON 合法但 nickname 字段异常**：不得让非关键昵称阻断登录；丢弃该昵称并按 5 节策略继续。
- 不新增任意性能 deadline，不改变现有明确传输超时，不记录 body。

### 4.3 测试夹具

每个 provider 至少覆盖：

- `Content-Type: application/json` 无 charset，body 为 UTF-8 中文与 emoji。
- 显式 `charset=UTF-8`。
- UTF-8 BOM。
- malformed UTF-8。
- 非 2xx。
- 合法 JSON 中 nickname 为 null、空白、控制字符、超长和正常西文名。

## 5. 外部显示名策略

新增来源专属组件，建议名：

```text
ExternalIdentityDisplayNamePolicy
ExternalDisplayNameDecision
- acceptedValue: String?
- classification: ACCEPTED | EMPTY | CONTROL | TOO_LONG | SUSPECT_LEGACY_ENCODING
- preserveExisting: boolean
```

### 5.1 校验规则

对 provider 已严格解码后的 Unicode 字符串：

1. Unicode-aware trim/strip。
2. 空值视为“本次未提供”。
3. 拒绝 ISO control。
4. 长度上限按 `user_info.nickname VARCHAR(50)` 的实际字符语义与数据库配置核验后实现；不得凭空另设更小数字。
5. 检出高置信 raw mojibake 时拒绝写入，但不在通用用户编辑路径自动转码。
6. 合法 Unicode、中文、emoji、重音字符原样保留。

### 5.2 更新语义

- **已有用户 + 有效 provider nickname**：按既有产品规则更新。
- **已有用户 + 无效/缺失 nickname**：传递 null/“不更新”语义；MySQL 和 LDAP 均保留已有 nickname。
- **新用户 + 有效 nickname**：正常写入。
- **新用户 + 无效/缺失 nickname**：nickname 可为空；展示层按 username → context username → jiacn → `用户` 回退。不得把乱码片段合成昵称。

推荐把“是否更新 nickname”表示为显式 patch/decision，而不是依赖模糊的空串语义。若保持现有 `upsert(UserEntity)`，必须增加测试证明 null 不会覆盖 MySQL，且 `updateExistingLdapUser` 保留 LDAP 旧值。

### 5.3 观测

仅记录：provider、stage、classification、existing/new、accepted/preserved。不得记录明文昵称、token、provider body 或带 secret 的 URL。

## 6. 服务器权威的人类发送者

### 6.1 新对象

```java
record ServerResolvedSender(
    String type,        // 固定 "user"
    String displayName,
    String jiacn,
    String clientId,
    DisplayNameSource source // NICKNAME/USERNAME/CONTEXT_USERNAME/JIACN/FALLBACK
) {}
```

新增 `HumanSenderIdentityResolver`，输入必须来自服务端认证上下文，不接收 request sender 字段：

```java
ServerResolvedSender resolve(EsContext context)
```

解析顺序：

1. `UserService.findByJiacn(context.jiacn).nickname`，必须通过显示名校验。
2. 用户实体 `username`。
3. `EsContext.username`。
4. `EsContext.jiacn`。
5. 常量 `用户`。

历史数据库 nickname 若是**高置信、严格可逆** raw mojibake，可只在内存中恢复后返回；不得在请求路径顺带写库。若已成为 `éæ\u00A0è¶` 等不可逆值，则跳过并回退 username/jiacn。

`chat/jia-chat-service` 增加 `implementation project(':user:jia-user-api')`。当前 `user` 模块不依赖 `chat`，源审计未发现环；正式实现仍须由 Gradle/Flow 验证依赖图。

### 6.2 `/chat/stream` 合约

方法与路径保持：

```text
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

请求兼容：

```json
{
  "content": "...",
  "conversationId": "...",
  "conversationType": "normal|juyiting",
  "senderType": "deprecated; accepted but ignored",
  "senderName": "deprecated; accepted but ignored",
  "metadata": {}
}
```

行为：

1. `ChatController.handleChat` 在完成认证身份读取后只解析一次 `ServerResolvedSender`。
2. 该对象显式传给：
   - `createAIStream` / `DatabaseChatMemoryAdvisor` context；
   - `createBuiltinSongJiangStream`；
   - `JuyitingAgentRelayService.relay`；
   - 用户消息持久化；
   - Agent protocol payload。
3. `senderType` 固定为 `user`；`senderName` 来自 resolver。
4. 客户端字段不进行“相等则接受”，而是无条件忽略，避免时序和规范化差异。
5. 兼容窗口内 DTO 字段保留并标注 deprecated；观测旧字段使用率后另行决定删除版本。

### 6.3 Metadata 策略

`ConversationMetadataPolicy.SAFE_KEYS` 当前允许标量 `senderType`、`senderName`。改造后：

- 从**客户端可复制 allowlist** 移除这两个 key。
- 在持久化/协议组装的最后一步，由服务器写入权威 `senderType`、`senderName`、`jiacn`（如协议允许）。
- 服务器 scope、owner、sender 字段始终覆盖 request metadata。
- 测试必须使用标量 spoof 值，不能只测试嵌套对象被类型过滤。

### 6.4 Advisor 与 relay

`DatabaseChatMemoryAdvisor` 不再从可被请求影响的任意 context 读取 sender；调用方传入已解析对象，或使用不可被 metadata 覆盖的专用 context key。`JuyitingAgentRelayService` 的直接消息、内层 protocol payload、`chat_message.sender_*` 和 metadata 必须复用同一实例，避免不同路径各自 fallback。

## 7. Agent 发送者权威化

`AgentWebSocketHandler` 已校验 session 注册的 agentId 和会话范围，但不得继续使用 payload `senderName`/`agentName`。

新增或复用：

```text
AgentSenderIdentityResolver.resolve(authenticatedAgentId)
  runtime.name -> runtime.personaName -> agentId
```

要求：

- 使用 session 已认证并被 `requireAllowedSessionAgentId` 接受的精确 agentId。
- `agent.message` 持久化、`agent_message` final、`agent_message_delta` 使用同一解析结果。
- payload 中同名字段兼容接收但忽略；可记录 spoof mismatch 计数，不记录伪造值。
- 复用 `AgentTaskThreadCreationTransaction.trustedSenderName()` 的约束：trim 后相等、最长 100、无 ISO control；建议抽成公共 resolver，避免规则漂移。
- 内建宋江消息继续使用服务器常量。

## 8. Web 统一显示名设计

### 8.1 共享模块

新增：

```text
web/src/utils/displayName.js
```

建议导出：

```js
normalizeDisplayName(value)
resolveAccountDisplayName(user, fallback)
isOwnMessage(message, identity)
```

所有页面替换本地重复实现：

- `src/components/UserProfile.vue`
- `src/components/world/JuyiHall.vue`
- `src/composables/juyiting/hallConversationMessages.js`
- `src/composables/juyiting/useHallConversation.js`
- `src/components/chat/Chat.vue`
- `src/components/chat/ChatMessage.vue`

### 8.2 兼容处理顺序

```text
输入类型检查
→ trim
→ 仅对高置信 percent-encoded UTF-8 尝试严格 decodeURIComponent
→ 仅对高置信 raw Latin-1 mojibake 尝试 bytes + fatal UTF-8 decode
→ 删除剩余 C0/C1 control
→ trim
→ 空值回退
```

关键点：**恢复必须先于控制字符删除**。raw mojibake 中 `U+0088/U+0099` 等 C1 code point 正是原 UTF-8 continuation byte；先删会变成不可逆 `éæ\u00A0è¶`。

高置信 raw mojibake 条件至少包括：

- 所有 code point ≤ `0xFF`；
- 存在 UTF-8 lead-byte 范围字符后跟 continuation-byte 范围字符，或包含 C1 continuation pattern；
- ISO-8859-1 bytes 经 fatal UTF-8 解码成功；
- decoded 值回编码 UTF-8 后与输入 byte 序列完全一致；
- decoded 值非空且无 ISO control。

普通 `José/Zoë/François` 不满足 lead+continuation 组合，不应被改写。

### 8.3 自己的消息

- 乐观 USER 消息增加 `isSelf: true`，标签直接显示 `你`，不依赖昵称。
- 后端消息返回并保留 owner `jiacn`（或等价稳定主体字段）；历史加载通过精确 identity 比较设置 `isSelf`。
- 自己的历史消息显示 `你`；其他用户和 Agent 显示服务器提供的 senderName。
- 在后端兼容期内，Web 停止发送 `senderName`、`senderType`；旧后端仍可用默认值，但正式验收以新后端权威行为为准。

## 9. 数据模型与迁移

本方案不要求新增表或扩大列：

- `user_info.nickname`：测试 schema 为 `VARCHAR(50)`。
- `chat_message.sender_name`：测试 schema 为 `VARCHAR(100)`。
- `chat_message.metadata`：text JSON，只有 `JSON_VALID` 且路径旧值精确匹配时才更新。

是否需要 DDL 必须由生产 `SHOW CREATE TABLE` 只读结果决定；未知字符集/排序规则只记录，不凭测试 schema 假定生产状态。完整方案见 [data-repair-plan.md](./data-repair-plan.md)。

## 10. 可观测性

新增低基数指标/结构化事件：

- `oauth_provider_utf8_decode_failure_total{provider,stage}`
- `external_display_name_rejected_total{provider,reason,existing}`
- `chat_sender_fallback_total{source}`
- `chat_sender_spoof_ignored_total{channel,http|metadata|agent_ws}`
- `display_name_legacy_repair_total{surface,kind}`（前端仅本地 telemetry 已允许时；不得上传原值）
- 数据修复报告：分类数量、CAS success/conflict、LDAP readback success/failure、rollback result。

日志禁止包含 nickname 原文、provider body、token、authorization header、带 secret/query 的 URL。

## 11. 发布顺序

1. **API 第 1 阶段**：OAuth bytes + strict UTF-8、外部昵称保护、服务端人类/Agent sender resolver、metadata 收敛。
2. **Web 阶段**：共享 helper、停止发送 sender 字段、自己消息显示“你”、历史 identity 判断。
3. **线上验证**：新登录、新聊天、历史刷新、Agent final/delta 一致；确认没有新污染。
4. **只读数据审计**：生成 A/B/C/D 分类和修复 manifest 候选。
5. **生产写授权后修复**：先用户主数据与 LDAP，再聊天历史；逐批 readback。
6. **兼容收敛**：观察旧客户端字段使用率；未来独立版本删除 DTO deprecated 字段。

应用修复必须先于数据修复，避免修完后再次被登录/聊天覆盖。

## 12. 回滚

### 12.1 应用回滚

- API/Web 按同 Run 制品和 exact SHA 回滚。
- 即使 Web 回滚，API 仍应继续忽略客户端 sender 字段；身份安全修复不应作为普通 UI 回滚的一部分撤销。
- OAuth strict UTF-8 若暴露 provider 非合规响应，回滚前必须确认不会重新引入数据污染；优先修兼容 parser，不回到 silent Latin-1。

### 12.2 数据回滚

- 每条修复记录保存 before/after 的受限 manifest。
- 回滚只在当前值仍 `BINARY = after` 时写回 before。
- LDAP 仅在 readback 仍等于 after 时回写 before。
- Chat metadata 仅在 `JSON_VALID` 且当前 `$.senderName = after` 时回滚。
- CAS conflict 不强行覆盖，转人工核验。

## 13. 决策记录

| ID | 决策 | 原因 |
| --- | --- | --- |
| UNE-DES-01 | OAuth JSON 使用 byte[] + strict UTF-8 | 消除 converter 默认 charset 歧义 |
| UNE-DES-02 | 不直接注入共享 RestTemplate | 保持 OAuth 不传播普通 API deadline 的既有边界 |
| UNE-DES-03 | sender identity 服务器解析 | 同时解决乱码固化和身份伪造 |
| UNE-DES-04 | 前端仅做兼容展示 | UI 不能成为数据源事实 |
| UNE-DES-05 | 不自动修不可逆值 | 避免把错误猜测固化为身份 |
| UNE-DES-06 | 数据修复使用 CAS/readback/条件回滚 | 防止覆盖并发修改并提供可恢复性 |
| UNE-DES-07 | 不新增任意性能门槛 | 遵守 availability-first 与 evidence-based gate policy |
