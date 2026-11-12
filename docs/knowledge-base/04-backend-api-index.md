# 后端 API 快速索引

本页用于先定位领域、模块、Controller 和类级路径；只有在需要逐方法 mapping、源码行号或 `@PreAuthorize` 时，才读取[完整静态清单](04-backend-api-inventory.md)的对应段落。

当前索引覆盖 **38** 个 Controller。生成基线见 [`BASELINE.yaml`](BASELINE.yaml)。本文件由 [`build-api-index.py`](build-api-index.py) 确定性生成。

| 领域 | 模块 | Controller | 类级映射 | 完整段落 |
| --- | --- | --- | --- | --- |
| `agent` | `jia-agent-service` | `AgentController` | `@RequestMapping("/agent")` | [查看](04-backend-api-inventory.md#agentcontroller) |
| `agent` | `jia-agent-service` | `AgentSceneController` | `@RequestMapping("/agent/scenes")` | [查看](04-backend-api-inventory.md#agentscenecontroller) |
| `base` | `jia-base-service` | `DictController` | `@RequestMapping("/dict")` | [查看](04-backend-api-inventory.md#dictcontroller) |
| `chat` | `jia-chat-service` | `ActiveAgentController` | `@RequestMapping("/agent")` | [查看](04-backend-api-inventory.md#activeagentcontroller) |
| `chat` | `jia-chat-service` | `AgentTaskThreadController` | `@RequestMapping("/chat/task-threads")` | [查看](04-backend-api-inventory.md#agenttaskthreadcontroller) |
| `chat` | `jia-chat-service` | `ChatController` | `@RequestMapping("/chat")` | [查看](04-backend-api-inventory.md#chatcontroller) |
| `chat` | `jia-chat-service` | `JuyitingActionController` | `@RequestMapping("/juyiting")` | [查看](04-backend-api-inventory.md#juyitingactioncontroller) |
| `dwz` | `jia-dwz-service` | `DwzController` | `@RequestMapping("/dwz")` | [查看](04-backend-api-inventory.md#dwzcontroller) |
| `isp` | `jia-isp-service` | `CarController` | `@RequestMapping("/car")` | [查看](04-backend-api-inventory.md#carcontroller) |
| `isp` | `jia-isp-service` | `CmsController` | `@RequestMapping("/cms")` | [查看](04-backend-api-inventory.md#cmscontroller) |
| `isp` | `jia-isp-service` | `FileController` | `@RequestMapping("/file")` | [查看](04-backend-api-inventory.md#filecontroller) |
| `isp` | `jia-isp-service` | `IspController` | `@RequestMapping("/isp")` | [查看](04-backend-api-inventory.md#ispcontroller) |
| `isp` | `jia-isp-service` | `LdapController` | `@RequestMapping("/ldap")` | [查看](04-backend-api-inventory.md#ldapcontroller) |
| `kefu` | `jia-kefu-service` | `KefuController` | `@RequestMapping("/kefu")` | [查看](04-backend-api-inventory.md#kefucontroller) |
| `material` | `jia-material-service` | `MediaController` | `@RequestMapping("/media")` | [查看](04-backend-api-inventory.md#mediacontroller) |
| `material` | `jia-material-service` | `NewsController` | `@RequestMapping("/news")` | [查看](04-backend-api-inventory.md#newscontroller) |
| `material` | `jia-material-service` | `PhraseController` | `@RequestMapping("/phrase")` | [查看](04-backend-api-inventory.md#phrasecontroller) |
| `material` | `jia-material-service` | `PvLogController` | `@RequestMapping("/pvlog")` | [查看](04-backend-api-inventory.md#pvlogcontroller) |
| `material` | `jia-material-service` | `TipController` | `@RequestMapping("/tip")` | [查看](04-backend-api-inventory.md#tipcontroller) |
| `material` | `jia-material-service` | `VoteController` | `@RequestMapping("/vote")` | [查看](04-backend-api-inventory.md#votecontroller) |
| `oauth` | `jia-oauth-client-starter` | `AuthenticationController` | `(none)` | [查看](04-backend-api-inventory.md#authenticationcontroller) |
| `oauth` | `jia-oauth-resource` | `AuthenticationController` | `(none)` | [查看](04-backend-api-inventory.md#authenticationcontroller-1) |
| `oauth` | `jia-oauth-service` | `OauthController` | `@RequestMapping("/oauth")` | [查看](04-backend-api-inventory.md#oauthcontroller) |
| `point` | `jia-point-service` | `GiftController` | `@RequestMapping("/gift")` | [查看](04-backend-api-inventory.md#giftcontroller) |
| `point` | `jia-point-service` | `PointController` | `@RequestMapping("/point")` | [查看](04-backend-api-inventory.md#pointcontroller) |
| `sms` | `jia-sms-service` | `SmsController` | `@RequestMapping("/sms")` | [查看](04-backend-api-inventory.md#smscontroller) |
| `task` | `jia-task-service` | `JobController` | `@RequestMapping("/job")` | [查看](04-backend-api-inventory.md#jobcontroller) |
| `task` | `jia-task-service` | `TaskController` | `@RequestMapping("/task")` | [查看](04-backend-api-inventory.md#taskcontroller) |
| `user` | `jia-user-service` | `GroupController` | `@RequestMapping("/group")` | [查看](04-backend-api-inventory.md#groupcontroller) |
| `user` | `jia-user-service` | `LoginController` | `@RequestMapping("/login")` | [查看](04-backend-api-inventory.md#logincontroller) |
| `user` | `jia-user-service` | `MsgController` | `@RequestMapping("/msg")` | [查看](04-backend-api-inventory.md#msgcontroller) |
| `user` | `jia-user-service` | `OrgController` | `@RequestMapping("/org")` | [查看](04-backend-api-inventory.md#orgcontroller) |
| `user` | `jia-user-service` | `PermsController` | `@RequestMapping("/action")` | [查看](04-backend-api-inventory.md#permscontroller) |
| `user` | `jia-user-service` | `RoleController` | `@RequestMapping("/role")` | [查看](04-backend-api-inventory.md#rolecontroller) |
| `user` | `jia-user-service` | `UserController` | `@RequestMapping("/user")` | [查看](04-backend-api-inventory.md#usercontroller) |
| `workflow` | `jia-workflow-service` | `WorkflowController` | `@RequestMapping("/workflow")` | [查看](04-backend-api-inventory.md#workflowcontroller) |
| `wx` | `jia-wx-service` | `WxMpController` | `@RequestMapping("/wx/mp")` | [查看](04-backend-api-inventory.md#wxmpcontroller) |
| `wx` | `jia-wx-service` | `WxPayController` | `@RequestMapping("/wx/pay")` | [查看](04-backend-api-inventory.md#wxpaycontroller) |

## 使用方式

```bash
./docs/knowledge-base/kb-search.sh --api AgentController
python3 docs/knowledge-base/build-api-index.py --check
python3 docs/knowledge-base/build-api-index.py
```

若按基础路径、方法名或权限检索，直接对完整清单执行定向 `rg`，不要先读取整个文件。
