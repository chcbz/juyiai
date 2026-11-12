# 用户名乱码源码审计（2026-09-26）

## 1. 审计边界

本审计只读取本地 Git 对象、项目文档和用户提供截图；没有访问生产数据库、LDAP、provider 接口、线上日志或云效运行环境，没有执行 Gradle/Vite 构建，也没有修改现有源代码。

由于本地 `web/` checkout 落后且有大量用户修改，Web 结论基于 `origin/develop` 的固定 Git 对象，不基于工作树。根仓和 `specs/INDEX.md` 也已有其他用户修改，本次不触碰。

> 更正记录（2026-09-26）：用户确认实际名称为“陈惠超”。初稿曾按“陈超”举例，漏掉“惠”字；本版已按实际名称重新计算完整字节链和验收夹具。

## 2. 固定基线

```text
root HEAD:
02d66c044a379c5b602ee854b92a56bdb1a12496

API origin/develop:
commit 3873dd6ab18992c70800658102d492c606216d63
tree   23aa90383f125f14c5ce688ed51eb62c66a60073

Web origin/develop:
commit d030a200d95eac6cea7fb0d91c0dd915aacf3ada
tree   49e101bb5ffa8b3d9f36baef8f3389cae65845c7
```

本地 checkout（仅用于说明为何不基于工作树审计）：

```text
root local HEAD: 02d66c044a379c5b602ee854b92a56bdb1a12496
api local HEAD:  3873dd6ab18992c70800658102d492c606216d63
web local HEAD:  c567e0593bd0334a4f6d47536e235fc1c3af7bb5
web vs origin/develop: ahead 1, behind 358
```

关键 blob：

| 仓库 | 文件 | blob |
| --- | --- | --- |
| API | `oauth/.../OauthExternalHttpClient.java` | `d65af906703aafc5ba1814ba27c0971c3b2d6ca7` |
| API | `common/.../RestTemplateConfig.java` | `e0e2181f96ea4b175dd009af01b8883f6a41f6f9` |
| API | `oauth/.../OauthController.java` | `326251e3950c095e6110abb6ad5cc405e77580c5` |
| API | `user/.../UserServiceImpl.java` | `d06b9e2c824c21517530e511cfa30653fb937d9d` |
| API | `chat/.../ChatController.java` | `00a940f547c39371691f3f5961e8a76a0af6dfe9` |
| API | `chat/.../JuyitingAgentRelayService.java` | `2bbfd54f31d56478db950cabd6fdff82735a270a` |
| API | `chat/.../DatabaseChatMemoryAdvisor.java` | `df2901e9774beb75323c234cf8a1743585d89ed5` |
| API | `chat/.../AgentWebSocketHandler.java` | `f1a482c45f2fcd80a95ceaae883f76cd2fb84675` |
| API | `chat/.../ConversationMetadataPolicy.java` | `63a3b4f00aa02e48598abecada84242caf042594` |
| Web | `src/components/UserProfile.vue` | `1037d6167426d03a6381b38864caad7de375837b` |
| Web | `src/components/world/JuyiHall.vue` | `67ab1b727e14fcb7d1bc75b61770eefa2e68f517` |
| Web | `src/composables/juyiting/hallConversationMessages.js` | `54b06accc2bcc3afb91efd11bf6caa40a9ce7b88` |
| Web | `src/composables/juyiting/useHallConversation.js` | `623a2dab48e9004e7e1d3b7d0fea693579cd0f2f` |

## 3. 截图复现

用户确认实际名称是“陈惠超”。其乱码在截图中呈现为 `éæ\u00A0è¶`（中间含 `U+00A0`）形态：

```text
原始 Unicode：陈惠超
UTF-8 bytes：E9 99 88 E6 83 A0 E8 B6 85
错误 Latin-1 解码 code points：
é U+00E9, U+0099, U+0088, æ U+00E6, U+0083, U+00A0, è U+00E8, ¶ U+00B6, U+0085
聊天前端删除 U+007F..U+009F 后：éæ\u00A0è¶
```

这与截图中保留 `é`、`æ`、`U+00A0`、`è`、`¶`，且 C1 控制字符位置消失的形态高度一致。该复现证明截图不需要假设字体损坏或随机数据库 corruption；“UTF-8 被按 Latin-1 解码 + 前端删除 C1”即可解释。

## 4. 根因证据

### 4.1 OAuth 专用 Client 绕过公共 UTF-8 converter

`OauthExternalHttpClient.java:25-38`：

```java
restTemplate = new RestTemplate(requestFactory);
...
restTemplate.exchange(url, method, entity, String.class)
```

`RestTemplateConfig.java:28-43` 则明确遍历 converter，把 `StringHttpMessageConverter` 默认 charset 设置为 UTF-8。OAuth 专用 Client 没有使用该配置。

Spring 的 `StringHttpMessageConverter` 文档明确说明其默认字符集为 ISO-8859-1；RFC 8259 §8.1 要求开放系统间交换的 JSON 使用 UTF-8。因此“不带 charset 的 UTF-8 JSON 被专用 Client 按默认 charset 读成 String”是最高置信新污染源。

### 4.2 Provider nickname 直接持久化

`OauthController.java`：

- 微信公众号：`user.setNickname(userDTO.getNickname())`。
- 微博：`user.setNickname(userDTO.getScreenName())`。
- GitHub：`user.setNickname(name != null ? name : login)`。
- 完成回调：`userService.upsert(user)`。

`UserServiceImpl.handleExistingUserUpdate()`：

```java
baseDao.updateById(user);
user.setJiacn(existingUser.getJiacn());
...
updateExistingLdapUser(user);
```

`updateExistingLdapUser()` 对非空 nickname 写入 LDAP。因此坏值可同时进入 MySQL 与 LDAP，并在第三方重新登录时再次覆盖。

### 4.3 聊天链信任客户端 sender

- `ChatController.createAIStream()` 把 `chatMessage.senderType/senderName` 放入 Advisor context。
- `JuyitingAgentRelayService` 把 request sender 写入外层/内层 Agent payload，并持久化到 `chat_message`。
- `DatabaseChatMemoryAdvisor` 从 context 保存 sender 字段。
- `ConversationMetadataPolicy.SAFE_KEYS` 包含 `senderType`、`senderName`；现有测试只证明嵌套对象会被类型过滤，没有证明标量 spoof 被拒绝。
- `AgentWebSocketHandler` 根据已认证 agentId 限制 scope，但 final/delta 的显示名仍优先取 payload `senderName/agentName`。

这是编码完整性与身份可信度的共同缺陷。

### 4.4 Web 聊天先删恢复所需字节

`hallConversationMessages.js:11-14`：

```js
value.replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim()
```

`useHallConversation.js` 用该函数解析 `globalStore.user.nickname`，既用于乐观消息，也随 `/chat/stream` 请求发送。C1 code point 在 raw mojibake 中对应原 UTF-8 continuation bytes；删除后无法恢复原中文。

### 4.5 已有 UI 修复是孤立的

- `UserProfile.vue` 有 percent decode + fatal UTF-8 恢复。
- `JuyiHall.vue` 有一份近似但重复的实现。
- 聊天使用另一份仅删除 control 的 helper。

因此同一账户可以出现“个人中心正常、账户入口正常、聊天用户名仍乱码”。

## 5. 时间线

| 日期 | commit | 结论 |
| --- | --- | --- |
| 2026-09-12 | `e896936d25c5ba8954cf1b009542a8b03a7ac8c1` | 引入 OAuth 专用 Client；开始存在自行创建 RestTemplate 的路径 |
| 2026-09-13 | `d924ef55bf0926884e679c9008c4d771bcb8c148` | 调整 callback deadline，但保留自行 new RestTemplate |
| 2026-09-18 | `7b8d35022ce54c85945103de878cb34469c67fed` | 个人中心加入历史名称恢复 |
| 2026-09-18 | `docs/implementation/evidence/mvp-audit-20260918/summary.json` | 线上审计记录个人中心 nickname mojibake |
| 2026-09-25 | `050f658413c1ff583a2b2912c1c134f4c4bdf64a` | 聚义厅账户入口加入独立恢复逻辑 |
| 2026-09-26 | 本审计 | 确认聊天 helper、客户端 sender 信任和 Agent WS sender 信任仍未闭环 |

## 6. 已排除或不足以解释全链的问题

- **字体/CSS**：不能解释字节级可逆复现，也不能解释坏值进入请求和数据库字段。
- **仅数据库不是 utf8mb4**：测试 schema 使用 utf8mb4，且截图模式在进数据库前即可生成；生产 schema 仍需只读核验，但不是当前最高置信起点。
- **仅前端 decodeURIComponent**：raw Latin-1 mojibake 不是 percent encoding，且聊天在恢复前已删除 C1。
- **只修个人中心**：不影响 OAuth 新污染、聊天持久化或 Agent 协议。
- **全量 Latin-1→UTF-8**：会误伤合法西文名，不能采用。
- **replacement character `�` 扫描**：raw Latin-1 和删 C1 后的 `éæ\u00A0è¶` 不一定含 `�`，现有烟测覆盖不足。

## 7. 尚未确认的生产事实

以下必须通过授权后的只读审计确认，不能从源码推断为生产事实：

- 生产 `user_info`、`chat_message` 的实际 DDL、charset、collation。
- 受影响记录数量和 A/B/C/D 分布。
- MySQL 与 LDAP 当前是否一致。
- 哪些坏值仍可由 provider 回读。
- 历史 metadata 中 senderName 的具体 JSON 形态。
- 最新生产部署实际对应的 API/Web SHA 和 Flow Run。

## 8. 结论置信度

| 结论 | 置信度 |
| --- | --- |
| 截图可由 UTF-8→Latin-1→删 C1 复现 | 高 |
| OAuth 专用 String converter 是新污染源 | 高 |
| 通用 upsert 可把坏昵称写入 MySQL/LDAP | 高 |
| 聊天客户端 sender 信任会固化乱码并允许 spoof | 高 |
| 个人中心/账户入口修复未覆盖聊天 | 高 |
| 生产受影响记录数量/具体列配置 | 未知，待只读审计 |


## 9. 外部规范参考

- [Spring `StringHttpMessageConverter` Javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/converter/StringHttpMessageConverter.html)
- [RFC 8259 §8.1 Character Encoding](https://www.rfc-editor.org/rfc/rfc8259#section-8.1)
