# 后端 HTTP/SSE 接口静态清单

> 生成基线：2026-08-15；`api` SHA：`a3253ef6432c4c9c1f41a6abec0b8a84d99e176e`。
> 提取范围：`**/*Controller.java` 中的 Spring mapping 注解。注解原文保留；class mapping 与 method mapping 需拼接为最终路由。动态网关、条件 Bean、继承映射和运行时安全策略不在此静态清单内。

共扫描 **38** 个 Controller 文件，提取 **393** 条方法 mapping。

## `AgentController`

- 源码：[`api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentController.java`](../../api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentController.java)
- 类级映射：`@RequestMapping("/agent")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 51 | `register` | `@PostMapping("/register")` | `—` |
| 56 | `list` | `@GetMapping("/list")` | `—` |
| 64 | `mapAgents` | `@GetMapping("/map")` | `—` |
| 69 | `capabilities` | `@GetMapping("/capabilities")` | `—` |
| 75 | `personaCatalog` | `@GetMapping("/personas/catalog")` | `—` |
| 80 | `bindPersona` | `@PostMapping("/personas/{personaCode}/bind")` | `—` |
| 90 | `unbindPersona` | `@DeleteMapping("/personas/{personaCode}/bind")` | `—` |
| 96 | `roster` | `@PostMapping("/roster")` | `—` |
| 103 | `get` | `@GetMapping("/{agentId}")` | `—` |
| 108 | `updateStatus` | `@PutMapping("/{agentId}/status")` | `—` |
| 113 | `getTasks` | `@GetMapping("/{agentId}/tasks")` | `—` |
| 118 | `personas` | `@GetMapping("/personas")` | `—` |
| 123 | `persona` | `@GetMapping("/persona/{name}")` | `—` |
| 128 | `dialogue` | `@PostMapping("/dialogue")` | `—` |
| 133 | `stats` | `@GetMapping("/stats")` | `—` |
| 138 | `searchTasks` | `@PostMapping("/tasks/search")` | `—` |
| 143 | `countTasksByStatus` | `@PostMapping("/tasks/status-counts")` | `—` |
| 148 | `createTask` | `@PostMapping("/tasks")` | `—` |
| 153 | `getTask` | `@GetMapping("/tasks/{taskId}")` | `—` |
| 158 | `assignTask` | `@PostMapping("/tasks/{taskId}/assign")` | `—` |
| 163 | `recommendTaskAssignees` | `@PostMapping("/tasks/{taskId}/recommend")` | `—` |
| 169 | `autoAssignTask` | `@PostMapping("/tasks/{taskId}/auto-assign")` | `—` |
| 174 | `reportTask` | `@PostMapping("/tasks/{taskId}/report")` | `—` |
| 179 | `addTaskNote` | `@PostMapping("/tasks/{taskId}/notes")` | `—` |
| 184 | `listTaskNotes` | `@GetMapping("/tasks/{taskId}/notes")` | `—` |
| 189 | `archiveTask` | `@PostMapping("/tasks/{taskId}/archive")` | `—` |
| 194 | `evaluate` | `@PostMapping("/evaluate")` | `—` |
| 199 | `compare` | `@PostMapping("/compare")` | `—` |
| 204 | `evaluationHistory` | `@GetMapping("/evaluation/{agentName}")` | `—` |
| 209 | `latestEvaluation` | `@GetMapping("/evaluation/latest/{agentName}")` | `—` |
| 214 | `evaluationStats` | `@GetMapping("/evaluation/stats")` | `—` |
| 219 | `deleteEvaluation` | `@DeleteMapping("/evaluation/{id}")` | `—` |

## `AgentSceneController`

- 源码：[`api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentSceneController.java`](../../api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentSceneController.java)
- 类级映射：`@RequestMapping("/agent/scenes")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 48 | `snapshot` | `@GetMapping("/{sceneId}/snapshot")` | `—` |
| 58 | `events` | `@GetMapping(value = "/{sceneId}/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)` | `—` |
| 80 | `phase` | `@PostMapping("/{sceneId}/phases")` | `—` |

## `DictController`

- 源码：[`api/base/jia-base-service/src/main/java/cn/jia/base/api/DictController.java`](../../api/base/jia-base-service/src/main/java/cn/jia/base/api/DictController.java)
- 类级映射：`@RequestMapping("/dict")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 32 | `find` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('dict-get')")` |
| 45 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('dict-create')")` |
| 58 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('dict-update')")` |
| 71 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('dict-list')")` |
| 87 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('dict-delete')")` |
| 99 | `locale` | `@RequestMapping(value = "/locale", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('dict-locale')")` |
| 109 | `cleanCache` | `@RequestMapping(value = "/cleanCache", method = RequestMethod.GET)` | `—` |

## `ActiveAgentController`

- 源码：[`api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ActiveAgentController.java`](../../api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ActiveAgentController.java)
- 类级映射：`@RequestMapping("/agent")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 22 | `activeAgents` | `@GetMapping("/active")` | `—` |

## `AgentTaskThreadController`

- 源码：[`api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/AgentTaskThreadController.java`](../../api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/AgentTaskThreadController.java)
- 类级映射：`@RequestMapping("/chat/task-threads")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 28 | `getOrCreateTeamThread` | `@PostMapping("/{taskId}/team")` | `—` |
| 39 | `getTeamThread` | `@GetMapping("/{taskId}/team")` | `—` |
| 48 | `appendTeamMessage` | `@PostMapping("/{taskId}/team/messages")` | `—` |
| 57 | `listTeamMessages` | `@GetMapping("/{taskId}/team/messages")` | `—` |

## `ChatController`

- 源码：[`api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatController.java`](../../api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatController.java)
- 类级映射：`@RequestMapping("/chat")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 100 | `handleChat` | `@RequestMapping(value = "/stream", method = RequestMethod.POST, produces = MediaType.TEXT_EVENT_STREAM_VALUE)` | `—` |
| 371 | `stopStream` | `@RequestMapping(value = "/stop_stream", method = RequestMethod.POST)` | `—` |
| 378 | `deleteConversation` | `@RequestMapping(value = "/conversation/delete", method = RequestMethod.DELETE)` | `—` |
| 384 | `getConversationContent` | `@RequestMapping(value = "/conversation/content", method = RequestMethod.GET)` | `—` |
| 389 | `conversationEvents` | `@RequestMapping(value = "/conversation/events", method = RequestMethod.GET, produces = MediaType.TEXT_EVENT_STREAM_VALUE)` | `—` |
| 396 | `listConversations` | `@RequestMapping(value = "/conversation/list", method = RequestMethod.POST)` | `—` |
| 412 | `updateConversation` | `@RequestMapping(value = "/conversation/update", method = RequestMethod.POST)` | `—` |
| 418 | `searchLibrary` | `@RequestMapping(value = "/library/search", method = RequestMethod.POST)` | `—` |
| 446 | `saveLibraryDocument` | `@RequestMapping(value = "/library/documents", method = RequestMethod.POST)` | `—` |

## `JuyitingActionController`

- 源码：[`api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/JuyitingActionController.java`](../../api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/JuyitingActionController.java)
- 类级映射：`@RequestMapping("/juyiting")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 24 | `dispatch` | `@PostMapping("/actions/{intentId}/dispatch")` | `—` |
| 31 | `mailbox` | `@GetMapping("/agents/{agentId}/mailbox")` | `—` |

## `DwzController`

- 源码：[`api/dwz/jia-dwz-service/src/main/java/cn/jia/dwz/api/DwzController.java`](../../api/dwz/jia-dwz-service/src/main/java/cn/jia/dwz/api/DwzController.java)
- 类级映射：`@RequestMapping("/dwz")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 35 | `view` | `@RequestMapping(value = "/view/{uri:.+}/**", method = RequestMethod.GET)` | `—` |
| 64 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `—` |
| 77 | `gen` | `@RequestMapping(value = "/gen", method = RequestMethod.POST)` | `—` |
| 90 | `restore` | `@RequestMapping(value = "/restore", method = RequestMethod.GET)` | `—` |
| 103 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `—` |
| 116 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `—` |
| 129 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `—` |

## `CarController`

- 源码：[`api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/CarController.java`](../../api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/CarController.java)
- 类级映射：`@RequestMapping("/car")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 40 | `listBrand` | `@RequestMapping(value = "/list/brand", method = RequestMethod.POST)` | `—` |
| 57 | `findBrandById` | `@RequestMapping(value = "/brand/get", method = RequestMethod.GET)` | `—` |
| 71 | `createBrand` | `@RequestMapping(value = "/brand/create", method = RequestMethod.POST)` | `—` |
| 82 | `updateBrand` | `@RequestMapping(value = "/brand/update", method = RequestMethod.POST)` | `—` |
| 93 | `deleteBrand` | `@RequestMapping(value = "/brand/delete", method = RequestMethod.GET)` | `—` |
| 109 | `listBrandAudi` | `@RequestMapping(value = "/list/brandAudi", method = RequestMethod.POST)` | `—` |
| 125 | `findBrandAudiById` | `@RequestMapping(value = "/brandAudi/get", method = RequestMethod.GET)` | `—` |
| 139 | `createBrandAudi` | `@RequestMapping(value = "/brandAudi/create", method = RequestMethod.POST)` | `—` |
| 150 | `updateBrandAudi` | `@RequestMapping(value = "/brandAudi/update", method = RequestMethod.POST)` | `—` |
| 161 | `deleteBrandAudi` | `@RequestMapping(value = "/brandAudi/delete", method = RequestMethod.GET)` | `—` |
| 177 | `listBrandVersion` | `@RequestMapping(value = "/list/brandVersion", method = RequestMethod.POST)` | `—` |
| 193 | `findBrandVersionById` | `@RequestMapping(value = "/brandVersion/get", method = RequestMethod.GET)` | `—` |
| 207 | `createBrandVersion` | `@RequestMapping(value = "/brandVersion/create", method = RequestMethod.POST)` | `—` |
| 218 | `updateBrandVersion` | `@RequestMapping(value = "/brandVersion/update", method = RequestMethod.POST)` | `—` |
| 229 | `deleteBrandVersion` | `@RequestMapping(value = "/brandVersion/delete", method = RequestMethod.GET)` | `—` |
| 245 | `listBrandMf` | `@RequestMapping(value = "/list/brandMf", method = RequestMethod.POST)` | `—` |
| 261 | `findBrandMfById` | `@RequestMapping(value = "/brandMf/get", method = RequestMethod.GET)` | `—` |
| 275 | `createBrandMf` | `@RequestMapping(value = "/brandMf/create", method = RequestMethod.POST)` | `—` |
| 286 | `updateBrandMf` | `@RequestMapping(value = "/brandMf/update", method = RequestMethod.POST)` | `—` |
| 297 | `deleteBrandMf` | `@RequestMapping(value = "/brandMf/delete", method = RequestMethod.GET)` | `—` |

## `CmsController`

- 源码：[`api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/CmsController.java`](../../api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/CmsController.java)
- 类级映射：`@RequestMapping("/cms")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 48 | `listTable` | `@RequestMapping(value = "/table/list", method = RequestMethod.POST)` | `—` |
| 66 | `findTableById` | `@RequestMapping(value = "/table/get", method = RequestMethod.GET)` | `—` |
| 81 | `createTable` | `@RequestMapping(value = "/table/create", method = RequestMethod.POST)` | `—` |
| 93 | `updateTable` | `@RequestMapping(value = "/table/update", method = RequestMethod.POST)` | `—` |
| 105 | `deleteTable` | `@RequestMapping(value = "/table/delete", method = RequestMethod.GET)` | `—` |
| 118 | `listColumn` | `@RequestMapping(value = "/column/list", method = RequestMethod.POST)` | `—` |
| 135 | `findColumnById` | `@RequestMapping(value = "/column/get", method = RequestMethod.GET)` | `—` |
| 150 | `createColumn` | `@RequestMapping(value = "/column/create", method = RequestMethod.POST)` | `—` |
| 162 | `updateColumn` | `@RequestMapping(value = "/column/update", method = RequestMethod.POST)` | `—` |
| 174 | `deleteColumn` | `@RequestMapping(value = "/column/delete", method = RequestMethod.GET)` | `—` |
| 185 | `findConfig` | `@RequestMapping(value = "/config/get", method = RequestMethod.GET)` | `—` |
| 197 | `updateConfig` | `@RequestMapping(value = "/config/update", method = RequestMethod.POST)` | `—` |
| 227 | `listRow` | `@RequestMapping(value = "/row/list", method = RequestMethod.POST)` | `—` |
| 247 | `findRowById` | `@RequestMapping(value = "/row/get", method = RequestMethod.POST)` | `—` |
| 266 | `createRow` | `@RequestMapping(value = "/row/create", method = RequestMethod.POST)` | `—` |
| 317 | `updateRow` | `@RequestMapping(value = "/row/update", method = RequestMethod.POST)` | `—` |
| 405 | `deleteRow` | `@RequestMapping(value = "/row/delete", method = RequestMethod.POST)` | `—` |

## `FileController`

- 源码：[`api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/FileController.java`](../../api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/FileController.java)
- 类级映射：`@RequestMapping("/file")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 41 | `findByURI` | `@RequestMapping(value = "/res/{uri:.+}/**", method = RequestMethod.GET)` | `—` |

## `IspController`

- 源码：[`api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/IspController.java`](../../api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/IspController.java)
- 类级映射：`@RequestMapping("/isp")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 47 | `listServer` | `@RequestMapping(value = "/server/list", method = RequestMethod.POST)` | `—` |
| 65 | `findServerById` | `@RequestMapping(value = "/server/get", method = RequestMethod.GET)` | `—` |
| 80 | `createServer` | `@RequestMapping(value = "/server/create", method = RequestMethod.POST)` | `—` |
| 93 | `updateServer` | `@RequestMapping(value = "/server/update", method = RequestMethod.POST)` | `—` |
| 105 | `deleteServer` | `@RequestMapping(value = "/server/delete", method = RequestMethod.GET)` | `—` |
| 118 | `refreshSSL` | `@RequestMapping(value = "/server/ssl/refresh", method = RequestMethod.GET)` | `—` |
| 124 | `refreshSSL` | `@RequestMapping(value = "/domain/record/delete", method = RequestMethod.GET)` | `—` |
| 136 | `hosts` | `@RequestMapping(value = "/dns/hosts", method = RequestMethod.GET, produces = "text/plain;charset=UTF-8")` | `—` |
| 163 | `updateDnsRecord` | `@RequestMapping("/dns/update_record")` | `—` |

## `LdapController`

- 源码：[`api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/LdapController.java`](../../api/isp/jia-isp-service/src/main/java/cn/jia/isp/api/LdapController.java)
- 类级映射：`@RequestMapping("/ldap")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 59 | `userFind` | `@GetMapping(value = "/user/get")` | `—` |
| 86 | `userSearch` | `@PostMapping(value = "/user/search")` | `—` |
| 104 | `userCreate` | `@PostMapping(value = "/user/create")` | `—` |
| 130 | `userUpdate` | `@PostMapping(value = "/user/update")` | `—` |
| 144 | `userDelete` | `@GetMapping(value = "/user/delete")` | `—` |
| 157 | `userFindAll` | `@GetMapping(value = "/user/findAll")` | `—` |
| 174 | `userGroupFindByCn` | `@GetMapping(value = "/usergroup/findByCn")` | `—` |
| 185 | `userGroupFindAll` | `@GetMapping(value = "/usergroup/findAll")` | `—` |
| 199 | `userGroupCreate` | `@PostMapping(value = "/usergroup/create")` | `—` |
| 227 | `userGroupUpdate` | `@PostMapping(value = "/usergroup/update")` | `—` |
| 242 | `userGroupMemberAdd` | `@PostMapping(value = "/usergroup/member/add")` | `—` |
| 267 | `userGroupMemberDelete` | `@PostMapping(value = "/usergroup/member/delete")` | `—` |
| 290 | `userGroupDelete` | `@GetMapping(value = "/usergroup/delete")` | `—` |
| 304 | `accountFindByUid` | `@GetMapping(value = "/account/findByUid")` | `—` |

## `KefuController`

- 源码：[`api/kefu/jia-kefu-service/src/main/java/cn/jia/kefu/api/KefuController.java`](../../api/kefu/jia-kefu-service/src/main/java/cn/jia/kefu/api/KefuController.java)
- 类级映射：`@RequestMapping("/kefu")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 55 | `listFaq` | `@RequestMapping(value = "/faq/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-faq_list')")` |
| 76 | `findFaqById` | `@RequestMapping(value = "/faq/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('kefu-faq_get')")` |
| 92 | `createFaq` | `@RequestMapping(value = "/faq/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-faq_create')")` |
| 106 | `updateFaq` | `@RequestMapping(value = "/faq/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-faq_update')")` |
| 119 | `deleteFaq` | `@RequestMapping(value = "/faq/delete", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('kefu-faq_delete')")` |
| 136 | `listMessage` | `@RequestMapping(value = "/message/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-message_list')")` |
| 158 | `findMessageById` | `@RequestMapping(value = "/message/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('kefu-message_get')")` |
| 173 | `createMessage` | `@RequestMapping(value = "/message/create", method = RequestMethod.POST)` | `—` |
| 195 | `updateMessage` | `@RequestMapping(value = "/message/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-message_update')")` |
| 208 | `deleteMessage` | `@RequestMapping(value = "/message/delete", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('kefu-message_delete')")` |
| 226 | `updateLogo` | `@RequestMapping(value = "/image/upload", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('kefu-image_upload')")` |

## `MediaController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/MediaController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/MediaController.java)
- 类级映射：`@RequestMapping("/media")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 50 | `findById` | `@GetMapping(value = "/get")` | `—` |
| 66 | `findContentById` | `@GetMapping(value = "/get/content")` | `—` |
| 80 | `create` | `@PostMapping(value = "/create")` | `—` |
| 93 | `update` | `@PostMapping(value = "/update")` | `—` |
| 105 | `delete` | `@GetMapping(value = "/delete")` | `—` |
| 120 | `list` | `@PostMapping(value = "/list")` | `—` |
| 143 | `upload` | `@PostMapping(value = "/upload")` | `—` |
| 195 | `thumbnail` | `@RequestMapping(value = "/thumbnail", method = RequestMethod.GET)` | `—` |

## `NewsController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/NewsController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/NewsController.java)
- 类级映射：`@RequestMapping("/news")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 79 | `findById` | `@GetMapping(value = "/get")` | `—` |
| 96 | `create` | `@PostMapping(value = "/create")` | `—` |
| 107 | `update` | `@PostMapping(value = "/update")` | `—` |
| 118 | `delete` | `@GetMapping(value = "/delete")` | `—` |
| 128 | `list` | `@PostMapping(value = "/list")` | `—` |
| 153 | `send` | `@GetMapping(value = "/send")` | `—` |

## `PhraseController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/PhraseController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/PhraseController.java)
- 类级映射：`@RequestMapping("/phrase")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 26 | `findById` | `@GetMapping(value = "/get")` | `—` |
| 40 | `create` | `@PostMapping(value = "/create")` | `—` |
| 51 | `update` | `@PostMapping(value = "/update")` | `—` |
| 62 | `delete` | `@GetMapping(value = "/delete")` | `—` |
| 76 | `getRandom` | `@PostMapping(value = "/get/random")` | `—` |
| 90 | `vote` | `@PostMapping(value = "/vote")` | `—` |
| 101 | `read` | `@GetMapping(value = "/read")` | `—` |

## `PvLogController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/PvLogController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/PvLogController.java)
- 类级映射：`@RequestMapping("/pvlog")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 42 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('pvlog-get')")` |
| 57 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('pvlog-create')")` |
| 78 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('pvlog-update')")` |
| 90 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('pvlog-delete')")` |
| 101 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('pvlog-list')")` |

## `TipController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/TipController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/TipController.java)
- 类级映射：`@RequestMapping("/tip")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 28 | `findById` | `@GetMapping(value = "/get")` | `—` |
| 42 | `create` | `@PostMapping(value = "/create")` | `—` |
| 53 | `update` | `@PostMapping(value = "/update")` | `—` |
| 64 | `delete` | `@GetMapping(value = "/delete")` | `—` |
| 78 | `list` | `@PostMapping(value = "/list")` | `—` |

## `VoteController`

- 源码：[`api/material/jia-material-service/src/main/java/cn/jia/mat/api/VoteController.java`](../../api/material/jia-material-service/src/main/java/cn/jia/mat/api/VoteController.java)
- 类级映射：`@RequestMapping("/vote")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 30 | `findById` | `@GetMapping(value = "/get")` | `—` |
| 47 | `create` | `@PostMapping(value = "/create")` | `—` |
| 58 | `update` | `@PostMapping(value = "/update")` | `—` |
| 69 | `delete` | `@GetMapping(value = "/delete")` | `—` |
| 79 | `list` | `@PostMapping(value = "/list")` | `—` |
| 94 | `findTicks` | `@PostMapping(value = "/get/ticks")` | `—` |
| 105 | `findRandom` | `@GetMapping(value = "/get/random")` | `—` |
| 117 | `tick` | `@PostMapping(value = "/tick")` | `—` |

## `AuthenticationController`

- 源码：[`api/oauth/jia-oauth-client-starter/src/main/java/cn/jia/oauth/api/AuthenticationController.java`](../../api/oauth/jia-oauth-client-starter/src/main/java/cn/jia/oauth/api/AuthenticationController.java)
- 类级映射：`(none)`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 12 | `token` | `@GetMapping("/token")` | `—` |

## `AuthenticationController`

- 源码：[`api/oauth/jia-oauth-resource/src/main/java/cn/jia/oauth/api/AuthenticationController.java`](../../api/oauth/jia-oauth-resource/src/main/java/cn/jia/oauth/api/AuthenticationController.java)
- 类级映射：`(none)`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 10 | `token` | `@GetMapping("/resource")` | `—` |

## `OauthController`

- 源码：[`api/oauth/jia-oauth-service/src/main/java/cn/jia/oauth/api/OauthController.java`](../../api/oauth/jia-oauth-service/src/main/java/cn/jia/oauth/api/OauthController.java)
- 类级映射：`@RequestMapping("/oauth")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 99 | `thirdPartyWxMp` | `@GetMapping("/third-party/wxmp")` | `—` |
| 197 | `thirdPartyWeiXin` | `@GetMapping("/third-party/weixin")` | `—` |
| 257 | `thirdPartyWeiBo` | `@GetMapping("/third-party/weibo")` | `—` |
| 351 | `thirdPartyGithub` | `@GetMapping("/third-party/github")` | `—` |
| 410 | `thirdPartyAutoLogin` | `@GetMapping("/third-party/autologin")` | `—` |
| 498 | `getAccessConfirmation` | `@RequestMapping("/confirm_access")` | `—` |
| 516 | `findClientId` | `@RequestMapping(value = "/clientid", method = RequestMethod.GET)` | `—` |
| 534 | `find` | `@RequestMapping(value = "/client/get", method = RequestMethod.GET)` | `—` |
| 550 | `updateClient` | `@RequestMapping(value = "/client/update", method = RequestMethod.POST)` | `—` |
| 567 | `info` | `@RequestMapping(value = "/user", method = RequestMethod.GET)` | `—` |

## `GiftController`

- 源码：[`api/point/jia-point-service/src/main/java/cn/jia/point/api/GiftController.java`](../../api/point/jia-point-service/src/main/java/cn/jia/point/api/GiftController.java)
- 类级映射：`@RequestMapping("/gift")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 35 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `—` |
| 47 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('gift-create')")` |
| 59 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('gift-update')")` |
| 71 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('gift-delete')")` |
| 82 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `—` |
| 98 | `usageAdd` | `@RequestMapping(value = "/usage/add", method = RequestMethod.POST)` | `—` |
| 114 | `usageCancel` | `@RequestMapping(value = "/usage/cancel/{giftUsageId}", method = RequestMethod.POST)` | `—` |
| 126 | `usageDelete` | `@RequestMapping(value = "/usage/delete/{giftUsageId}", method = RequestMethod.POST)` | `—` |
| 139 | `usageListByGift` | `@RequestMapping(value = "/usage/list/gift/{giftId}", method = RequestMethod.POST)` | `—` |
| 155 | `usageListByUser` | `@RequestMapping(value = "/usage/list/user/{user}", method = RequestMethod.POST)` | `—` |

## `PointController`

- 源码：[`api/point/jia-point-service/src/main/java/cn/jia/point/api/PointController.java`](../../api/point/jia-point-service/src/main/java/cn/jia/point/api/PointController.java)
- 类级映射：`@RequestMapping("/point")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 29 | `init` | `@RequestMapping(value = "/init", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('point-init')")` |
| 42 | `sign` | `@RequestMapping(value = "/sign", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('point-sign')")` |
| 55 | `referral` | `@RequestMapping(value = "/referral", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('point-referral')")` |
| 68 | `luck` | `@RequestMapping(value = "/luck", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('point-luck')")` |

## `SmsController`

- 源码：[`api/sms/jia-sms-service/src/main/java/cn/jia/sms/api/SmsController.java`](../../api/sms/jia-sms-service/src/main/java/cn/jia/sms/api/SmsController.java)
- 类级映射：`@RequestMapping("/sms")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 49 | `validateSmsCode` | `@RequestMapping(value = "/validate", method = RequestMethod.GET)` | `—` |
| 68 | `useSmsCode` | `@RequestMapping(value = "/use", method = RequestMethod.GET)` | `—` |
| 88 | `gen` | `@RequestMapping(value = "/gen", method = RequestMethod.GET)` | `—` |
| 133 | `sendSms` | `@RequestMapping(value = "/send", method = RequestMethod.POST)` | `—` |
| 168 | `listSend` | `@RequestMapping(value = "/send/list", method = RequestMethod.POST)` | `—` |
| 186 | `sendSmsBatch` | `@RequestMapping(value = "/sendBatch", method = RequestMethod.POST)` | `—` |
| 221 | `balance` | `@RequestMapping(value = "/balance", method = RequestMethod.GET)` | `—` |
| 238 | `receive` | `@RequestMapping(value = "/receive", method = RequestMethod.GET)` | `—` |
| 275 | `listReply` | `@RequestMapping(value = "/reply/list", method = RequestMethod.POST)` | `—` |
| 291 | `findConfig` | `@RequestMapping(value = "/config/get", method = RequestMethod.GET)` | `—` |
| 304 | `updateConfig` | `@RequestMapping(value = "/config/update", method = RequestMethod.POST)` | `—` |
| 319 | `findTemplateById` | `@RequestMapping(value = "/template/get", method = RequestMethod.GET)` | `—` |
| 335 | `createTemplate` | `@RequestMapping(value = "/template/create", method = RequestMethod.POST)` | `—` |
| 348 | `updateTemplate` | `@RequestMapping(value = "/template/update", method = RequestMethod.POST)` | `—` |
| 361 | `deleteTemplate` | `@RequestMapping(value = "/template/delete", method = RequestMethod.GET)` | `—` |
| 375 | `listTemplate` | `@RequestMapping(value = "/template/list", method = RequestMethod.POST)` | `—` |
| 394 | `buy` | `@RequestMapping(value = "/buy", method = RequestMethod.GET)` | `—` |

## `JobController`

- 源码：[`api/task/jia-task-service/src/main/java/cn/jia/task/api/JobController.java`](../../api/task/jia-task-service/src/main/java/cn/jia/task/api/JobController.java)
- 类级映射：`@RequestMapping("/job")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 37 | `list` | `@GetMapping("/list")` | `@PreAuthorize("hasAuthority('job-list')")` |
| 50 | `get` | `@GetMapping("/get")` | `@PreAuthorize("hasAuthority('job-get')")` |
| 72 | `execute` | `@PostMapping("/execute")` | `@PreAuthorize("hasAuthority('job-execute')")` |
| 88 | `executeAsync` | `@PostMapping("/execute/async")` | `@PreAuthorize("hasAuthority('job-execute')")` |
| 104 | `status` | `@GetMapping("/status")` | `@PreAuthorize("hasAuthority('job-status')")` |

## `TaskController`

- 源码：[`api/task/jia-task-service/src/main/java/cn/jia/task/api/TaskController.java`](../../api/task/jia-task-service/src/main/java/cn/jia/task/api/TaskController.java)
- 类级映射：`@RequestMapping("/task")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 36 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('task-get')")` |
| 49 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('task-create')")` |
| 63 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('task-update')")` |
| 76 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('task-delete')")` |
| 89 | `cancel` | `@RequestMapping(value = "/cancel", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('task-cancel')")` |
| 101 | `search` | `@RequestMapping(value = "/search", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('task-search')")` |
| 117 | `searchItem` | `@RequestMapping(value = "/item/search", method = RequestMethod.POST)` | `—` |

## `GroupController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/GroupController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/GroupController.java)
- 类级映射：`@RequestMapping("/group")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 39 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('group-get')")` |
| 55 | `findUsers` | `@RequestMapping(value = "/get/users", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-get_users')")` |
| 72 | `findRoles` | `@RequestMapping(value = "/get/roles", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-get_roles')")` |
| 89 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-create')")` |
| 102 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-update')")` |
| 115 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('group-delete')")` |
| 127 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-list')")` |
| 144 | `userBatchAdd` | `@RequestMapping(value = "/users/add", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-users_add')")` |
| 157 | `userBatchDel` | `@RequestMapping(value = "/users/del", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-users_del')")` |
| 170 | `changeRole` | `@RequestMapping(value = "/role/change", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('group-role_change')")` |

## `LoginController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/LoginController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/LoginController.java)
- 类级映射：`@RequestMapping("/login")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 95 | `login` | `@GetMapping("/index.html")` | `—` |
| 176 | `gen` | `@RequestMapping(value = "sms/gen", method = RequestMethod.GET)` | `—` |
| 213 | `register` | `@GetMapping("/register")` | `—` |
| 220 | `register` | `@PostMapping("/register")` | `—` |
| 254 | `resetPassword` | `@GetMapping("/resetPassword")` | `—` |
| 322 | `resetPassword` | `@PostMapping(value = "/resetPassword")` | `—` |
| 354 | `info` | `@RequestMapping(value = "/user", method = RequestMethod.GET)` | `—` |
| 359 | `userInfo` | `@GetMapping(value = "/user/info")` | `—` |
| 376 | `updateUser` | `@PostMapping(value = "/user/info/update")` | `—` |
| 396 | `changePassword` | `@GetMapping(value = "/user/password/change")` | `—` |
| 418 | `updateAvatar` | `@PostMapping(value = "/user/avatar/update")` | `—` |

## `MsgController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/MsgController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/MsgController.java)
- 类级映射：`@RequestMapping("/msg")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 30 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `—` |
| 43 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('msg-create')")` |
| 56 | `read` | `@RequestMapping(value = "/read", method = RequestMethod.GET)` | `—` |
| 71 | `unread` | `@RequestMapping(value = "/unread", method = RequestMethod.GET)` | `—` |
| 86 | `readAll` | `@RequestMapping(value = "/readall", method = RequestMethod.GET)` | `—` |
| 99 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `—` |
| 111 | `recycle` | `@RequestMapping(value = "/recycle", method = RequestMethod.GET)` | `—` |
| 123 | `restore` | `@RequestMapping(value = "/restore", method = RequestMethod.GET)` | `—` |
| 135 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `—` |

## `OrgController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/OrgController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/OrgController.java)
- 类级映射：`@RequestMapping("/org")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 57 | `findAllById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('org-get')")` |
| 86 | `findParent` | `@RequestMapping(value = "/get/parent", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('org-get_parent')")` |
| 102 | `findNameById` | `@RequestMapping(value = "/get/name", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('org-get_name')")` |
| 117 | `findUsers` | `@RequestMapping(value = "/get/users", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-get_users')")` |
| 134 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-create')")` |
| 146 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-update')")` |
| 158 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('org-delete')")` |
| 169 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-list')")` |
| 185 | `listSub` | `@RequestMapping(value = "/list/sub", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-list_sub')")` |
| 202 | `userBatchAdd` | `@RequestMapping(value = "/users/add", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-users_add')")` |
| 225 | `userBatchDel` | `@RequestMapping(value = "/users/del", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-users_del')")` |
| 243 | `findDirector` | `@RequestMapping(value = "/get/director", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('org-get_director')")` |
| 273 | `updateLogo` | `@RequestMapping(value = "/update/logo", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('org-update_logo')")` |

## `PermsController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/PermsController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/PermsController.java)
- 类级映射：`@RequestMapping("/action")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 34 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `—` |
| 47 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('action-create')")` |
| 60 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('action-update')")` |
| 73 | `refresh` | `@RequestMapping(value = "/refresh", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('action-refresh')")` |
| 86 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('action-delete')")` |
| 98 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `—` |

## `RoleController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/RoleController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/RoleController.java)
- 类级映射：`@RequestMapping("/role")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 47 | `findById` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('role-get')")` |
| 59 | `findUsers` | `@RequestMapping(value = "/get/users", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-get_users')")` |
| 76 | `findPerms` | `@RequestMapping(value = "/get/perms", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-get_perms')")` |
| 95 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-create')")` |
| 107 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-update')")` |
| 119 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('role-delete')")` |
| 131 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-list')")` |
| 147 | `changePerms` | `@RequestMapping(value = "/perms/change", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-perms_change')")` |
| 159 | `userBatchAdd` | `@RequestMapping(value = "/users/add", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-users_add')")` |
| 172 | `userBatchDel` | `@RequestMapping(value = "/users/del", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('role-users_del')")` |

## `UserController`

- 源码：[`api/user/jia-user-service/src/main/java/cn/jia/user/api/UserController.java`](../../api/user/jia-user-service/src/main/java/cn/jia/user/api/UserController.java)
- 类级映射：`@RequestMapping("/user")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 75 | `find` | `@RequestMapping(value = "/get", method = RequestMethod.GET)` | `—` |
| 109 | `findNameById` | `@RequestMapping(value = "/get/name", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-get_name')")` |
| 126 | `findRoles` | `@RequestMapping(value = "/get/roles", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-get_roles')")` |
| 144 | `findOrgs` | `@RequestMapping(value = "/get/orgs", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-get_orgs')")` |
| 158 | `check` | `@RequestMapping(value = "/check", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-check')")` |
| 182 | `create` | `@RequestMapping(value = "/create", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-create')")` |
| 195 | `update` | `@RequestMapping(value = "/update", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-update')")` |
| 208 | `sync` | `@RequestMapping(value = "/sync", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-sync')")` |
| 221 | `delete` | `@RequestMapping(value = "/delete", method = RequestMethod.DELETE)` | `@PreAuthorize("hasAuthority('user-delete')")` |
| 234 | `list` | `@RequestMapping(value = "/list", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-list')")` |
| 260 | `search` | `@RequestMapping(value = "/search", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-search')")` |
| 282 | `changePoint` | `@RequestMapping(value = "/point/change", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-point_change')")` |
| 295 | `changeRole` | `@RequestMapping(value = "/role/change", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-role_change')")` |
| 308 | `changeGroup` | `@RequestMapping(value = "/group/change", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-group_change')")` |
| 321 | `changeOrg` | `@RequestMapping(value = "/org/change", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-org_change')")` |
| 334 | `userInfo` | `@RequestMapping(value = "/my", method = RequestMethod.GET)` | `—` |
| 358 | `changePassword` | `@RequestMapping(value = "/password/change", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-password_change')")` |
| 374 | `resetPassword` | `@RequestMapping(value = "/password/reset", method = RequestMethod.GET)` | `—` |
| 395 | `batchImport` | `@RequestMapping(value = "/batch/import", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-batch_import')")` |
| 417 | `changePosition` | `@RequestMapping(value = "/position/change", method = RequestMethod.GET)` | `@PreAuthorize("hasAuthority('user-position_change')")` |
| 470 | `updateAvatar` | `@RequestMapping(value = "/update/avatar", method = RequestMethod.POST)` | `@PreAuthorize("hasAuthority('user-update_avatar')")` |

## `WorkflowController`

- 源码：[`api/workflow/jia-workflow-service/src/main/java/cn/jia/workflow/api/WorkflowController.java`](../../api/workflow/jia-workflow-service/src/main/java/cn/jia/workflow/api/WorkflowController.java)
- 类级映射：`@RequestMapping("/workflow")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 53 | `deployProcess` | `@RequestMapping(value = "/deploy", method = RequestMethod.POST)` | `—` |
| 69 | `getDeployment` | `@RequestMapping(value = "/deployment/list", method = RequestMethod.POST)` | `—` |
| 95 | `getDeploymentById` | `@RequestMapping(value = "/deployment/find", method = RequestMethod.GET)` | `—` |
| 114 | `getDeploymentResourceNames` | `@RequestMapping(value = "/deployment/resource/list", method = RequestMethod.GET)` | `—` |
| 132 | `getDeploymentResource` | `@RequestMapping(value = "/deployment/resource/find", method = RequestMethod.GET)` | `—` |
| 152 | `deleteDeployment` | `@RequestMapping(value = "/deployment/delete", method = RequestMethod.GET)` | `—` |
| 164 | `getDefinition` | `@RequestMapping(value = "/definition/list", method = RequestMethod.POST)` | `—` |
| 195 | `getDefinitionById` | `@RequestMapping(value = "/definition/find", method = RequestMethod.GET)` | `—` |
| 223 | `getProcessDiagram` | `@RequestMapping(value = "/definition/diagram", method = RequestMethod.GET)` | `—` |
| 243 | `activateDefinition` | `@RequestMapping(value = "/definition/activate", method = RequestMethod.GET)` | `—` |
| 255 | `suspendDefinition` | `@RequestMapping(value = "/definition/suspend", method = RequestMethod.GET)` | `—` |
| 269 | `startProcess` | `@PostMapping(value = "/start/{processDefinitionKey}/{businessKey}")` | `—` |
| 285 | `deleteProcess` | `@PostMapping(value = "/delete/{processInstanceId}")` | `—` |
| 297 | `listWait` | `@PostMapping(value = "/list/wait")` | `—` |
| 335 | `listHistory` | `@PostMapping(value = "/list/history")` | `—` |
| 370 | `listHistoryByBusinessKey` | `@PostMapping(value = "/list/process")` | `—` |
| 412 | `listHistoricProcessInstances` | `@PostMapping(value = "/list/my")` | `—` |
| 462 | `complete` | `@PostMapping(value = "/complete/{taskId}")` | `—` |
| 490 | `delegateTask` | `@GetMapping(value = "/task/delegate")` | `—` |
| 502 | `claimTask` | `@GetMapping(value = "/task/claim")` | `—` |
| 515 | `setAssignee` | `@GetMapping(value = "/task/assign")` | `—` |
| 528 | `getTaskByBusinessKey` | `@GetMapping(value = "/find/bybusinesskey")` | `—` |
| 560 | `listTaskByBusinessKey` | `@GetMapping(value = "/list/bybusinesskey")` | `—` |
| 587 | `getTaskById` | `@GetMapping(value = "/find")` | `—` |
| 621 | `getInstanceDiagram` | `@RequestMapping(value = "/instance/diagram", method = RequestMethod.GET)` | `—` |

## `WxMpController`

- 源码：[`api/wx/jia-wx-service/src/main/java/cn/jia/wx/api/WxMpController.java`](../../api/wx/jia-wx-service/src/main/java/cn/jia/wx/api/WxMpController.java)
- 类级映射：`@RequestMapping("/wx/mp")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 124 | `checkSignature` | `@RequestMapping(value = "/checksignature", method = RequestMethod.GET)` | `—` |
| 143 | `receiveMsg` | `@RequestMapping(value = "/checksignature", method = RequestMethod.POST)` | `—` |
| 484 | `menuCreate` | `@RequestMapping("/menu/create")` | `—` |
| 499 | `menuGet` | `@RequestMapping("/menu/get")` | `—` |
| 511 | `menuDelete` | `@RequestMapping("/menu/delete")` | `—` |
| 525 | `userGet` | `@RequestMapping("/user/get")` | `—` |
| 538 | `userInfoBatchGet` | `@RequestMapping("/user/info/batchget")` | `—` |
| 550 | `userSync` | `@RequestMapping("/user/sync")` | `—` |
| 603 | `oauth2Authorize` | `@RequestMapping("/oauth2/authorize_url")` | `—` |
| 618 | `oauth2AccessToken` | `@RequestMapping("/oauth2/access_token")` | `—` |
| 633 | `oauth2Userinfo` | `@RequestMapping("/oauth2/userinfo")` | `—` |
| 652 | `oauth2RefreshToken` | `@RequestMapping("/oauth2/refresh_token")` | `—` |
| 667 | `oauth2ValidateAccessToken` | `@RequestMapping("/oauth2/auth")` | `—` |
| 684 | `createJsapiSignature` | `@RequestMapping("/jsapi/signature")` | `—` |
| 696 | `getkflist` | `@RequestMapping("/customservice/getkflist")` | `—` |
| 708 | `getwaitcase` | `@RequestMapping("/customservice/kfsession/getwaitcase")` | `—` |
| 721 | `customMessageSend` | `@RequestMapping("/message/custom/send")` | `—` |
| 734 | `templateMessageSend` | `@RequestMapping("/message/template/send")` | `—` |
| 749 | `materialBatchGet` | `@RequestMapping("/material/batchget")` | `—` |
| 768 | `materialAddNews` | `@RequestMapping("/material/add_news")` | `—` |
| 819 | `materialAdd` | `@RequestMapping("/material/add_material")` | `—` |
| 844 | `findMpInfoById` | `@RequestMapping(value = "/info/get", method = RequestMethod.GET)` | `—` |
| 859 | `createMpInfo` | `@RequestMapping(value = "/info/create", method = RequestMethod.POST)` | `—` |
| 872 | `updateMpInfo` | `@RequestMapping(value = "/info/update", method = RequestMethod.POST)` | `—` |
| 884 | `deleteMpInfo` | `@RequestMapping(value = "/info/delete", method = RequestMethod.GET)` | `—` |
| 897 | `listMpInfo` | `@RequestMapping(value = "/info/list", method = RequestMethod.POST)` | `—` |

## `WxPayController`

- 源码：[`api/wx/jia-wx-service/src/main/java/cn/jia/wx/api/WxPayController.java`](../../api/wx/jia-wx-service/src/main/java/cn/jia/wx/api/WxPayController.java)
- 类级映射：`@RequestMapping("/wx/pay")`

| 行 | 方法 | 方法级 mapping | `@PreAuthorize` |
| ---: | --- | --- | --- |
| 83 | `queryOrder` | `@GetMapping("/queryOrder")` | `—` |
| 105 | `closeOrder` | `@GetMapping("/closeOrder/{outTradeNo}")` | `—` |
| 116 | `createOrder` | `@PostMapping("/createOrder")` | `—` |
| 132 | `createOrder` | `@GetMapping("/createOrder")` | `—` |
| 246 | `unifiedOrder` | `@PostMapping("/unifiedOrder")` | `—` |
| 260 | `unifiedOrder` | `@GetMapping("/unifiedOrder")` | `—` |
| 304 | `refund` | `@PostMapping("/refund")` | `—` |
| 332 | `refundQuery` | `@GetMapping("/refundQuery")` | `—` |
| 344 | `parseOrderNotifyResult` | `@PostMapping("/parseOrderNotifyResult")` | `—` |
| 374 | `parseRefundNotifyResult` | `@PostMapping("/parseRefundNotifyResult")` | `—` |
| 386 | `parseScanPayNotifyResult` | `@PostMapping("/parseScanPayNotifyResult")` | `—` |
| 437 | `sendRedpack` | `@PostMapping("/sendRedpack")` | `—` |
| 455 | `queryRedpack` | `@GetMapping("/queryRedpack/{mchBillNo}")` | `—` |
| 474 | `entPay` | `@PostMapping("/entPay")` | `—` |
| 491 | `queryEntPay` | `@GetMapping("/queryEntPay/{partnerTradeNo}")` | `—` |
| 514 | `createScanPayQrcodeMode1` | `@PostMapping("/scanPay/qrcode")` | `—` |
| 542 | `createScanPayQrcodeMode1` | `@GetMapping("/scanPay/qrcodeLink")` | `—` |
| 582 | `report` | `@PostMapping("/report")` | `—` |
| 613 | `downloadBill` | `@GetMapping("/downloadBill")` | `—` |
| 632 | `micropay` | `@PostMapping("/micropay")` | `—` |
| 650 | `reverseOrder` | `@PostMapping("/reverseOrder")` | `—` |
| 655 | `getSandboxSignKey` | `@GetMapping("/getSandboxSignKey")` | `—` |
| 660 | `sendCoupon` | `@PostMapping("/sendCoupon")` | `—` |
| 665 | `queryCouponStock` | `@PostMapping("/queryCouponStock")` | `—` |
| 671 | `queryCouponInfo` | `@PostMapping("/queryCouponInfo")` | `—` |
| 677 | `queryComment` | `@PostMapping("/queryComment")` | `—` |
| 687 | `findPayInfoById` | `@RequestMapping(value = "/info/get", method = RequestMethod.GET)` | `—` |
| 701 | `createPayInfo` | `@RequestMapping(value = "/info/create", method = RequestMethod.POST)` | `—` |
| 712 | `updatePayInfo` | `@RequestMapping(value = "/info/update", method = RequestMethod.POST)` | `—` |
| 723 | `deletePayInfo` | `@RequestMapping(value = "/info/delete", method = RequestMethod.GET)` | `—` |
| 734 | `listPayInfo` | `@RequestMapping(value = "/info/list", method = RequestMethod.POST)` | `—` |
