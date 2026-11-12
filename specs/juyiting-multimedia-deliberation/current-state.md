> **2026-10-07 当前状态补录**：[已实现/发布/业务证据](delivery-status.md) · [剩余任务](remaining-tasks-20261007.md) · [新最短流程实测](shortest-flow-test-20261007.md)。下方2026-10-04及更早记录保持历史，旧“暂停/未执行”不覆盖已实际发布的API117/Web177。整体验收仍NOT_COMPLETE；不重做已实现功能、不因文档构建或部署。

# 当前能力、存储与依赖基线

> **2026-09-28 整合增量**：下文是9月27日原始观察；当前研发分支与精确源码以 [整合回执](integration-baseline-20260928.md) 为准。未重新核对生产配置，不由研发分支推导已上线。

日期：2026-09-27。以下区分已有源码、前期本机只读观察与未来设计；不表示已完成线上验收。根仓远端 develop 文档基线为 `02d66c044a379c5b602ee854b92a56bdb1a12496`。

## 1. 远端源码基线（本次再次核对）

| 仓库 | develop | fast-deliberation 候选 |
| --- | --- | --- |
| API | e15e1a9d947e86e5f81a3288948087466a8a879c | caee54fc27a08146f9cc57219cf86c763e41c531 |
| Web | 9854173f7f409ca2f1c862eb153b0e3574ee58ff | 96838f17fc24fbf21781be39476aa9723dee3a2c |
| Client | 29fda32acca7a4c4f7a66a4188946853086e6dcb | 68dbe8992a56c8e1041056a9123b1156d1d2b35e |

候选合并模拟：API 6 个内容冲突、Web 2 个、Client 1 个测试冲突，根仓 2 个 gitlink 冲突。评估 Web 79 / Client 141 通过只是候选定向测试，不是最终 merged tree，也没有验证本需求。

原开发交接位于 SDD 特性分支 `codex/juyiting-codex-fast-deliberation-context` 的 `specs/juyiting-codex-fast-context-20260925/developer-handoff-20260927.md` 和 `merge-assessment-20260927.md`。该目录尚未随功能合入 develop，不创建虚假本分支链接。

## 2. 前期已观察的本机部署配置（不是本次重新核验）

API 配置文件 `/opt/cyf/service/api/application.properties`：

```properties
agent.personal-workspace-storage.enabled=true
agent.personal-workspace-storage.root-directory=/opt/cyf/service/workspace-private
agent.task-artifact-storage.enabled=true
agent.task-artifact-storage.root-directory=/opt/cyf/service/task-artifacts-private
```

个人内容对象路径：

```text
/opt/cyf/service/workspace-private/v1/
  <scopeHash前2>/<scopeHash64>/<contentHash前2>/<contentHash64>
```

scope 为 tenant/client/owner；文件名、版本、MIME、storageRef 由数据库管理，并非用户文件夹原名。当前存储实现 tenant 限于 `0`；不宣称已经开放通用多租户。

本机 Agent Profile `/home/isp/apps/codex-ws-agent/codex-profiles.conf` 配置受控执行根 `/home/isp/apps/codex-ws-agent/data/private-runs`，每次执行为 `<taskId>/<runId>/inputs|outputs|scratch`。自家接应使用自己的配置根，不能推定与本机一致。

## 3. Agent 如何知道读写位置

不是只靠自然语言提示。既有运行时接收受控输入/输出声明，领取任务输入、校验字节，创建 run 工作目录，设置执行 cwd 并注入 workspaceFilePrompt；工具产生真实文件后按输出声明校验并上传 manifest。默认工作目录与受控 run 目录可不同，均保留。

新增方案只扩展精确输入类型、输出用途及会话关联，不要求平台与所有 Agent 挂载同一路径。界面用平台认证内容接口，不暴露 Agent 路径，也不把 Markdown 路径当完成。

## 4. 复用与缺口

| 能力 | 已有/观察 | 本需求增量 |
| --- | --- | --- |
| 个人空间 | 列表、上传、版本、预览/下载、回收站 | 选择参考资料；用户主动从会话归档 |
| 文件执行 | PRIVATE/TASK、输入领取、native START、输出/manifest | 会话产物用途；精确未归档资产输入；turn/run/part 关联 |
| 正式交付 | 成果清单、提交、用户决定 | 选中集合桥接，不自动提交所有试稿 |
| 会话 | task-thread、流式消息/事件 | 点将后可靠 bootstrap、混排媒体、快照可重建 |
| fast-deliberation 候选 | durable 请求/轮次/事件结构 | 先修身份/能力/冷上下文/INSPECT，再复用 |

当前 PRIVATE 输出会创建个人文件，TASK 还会建立正式交付；故本需求须新增显式会话用途，不能只改前端文案。

## 5. 实施时重点源码入口（绝对路径）

- `/home/isp/wsps/cyf/web/src/components/juyiting/BountyDiscussionPanel.vue`
- `/home/isp/wsps/cyf/web/src/composables/juyiting/useHallConversation.js`
- `/home/isp/wsps/cyf/web/src/composables/juyiting/hallConversationMessages.js`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/ChatController.java`
- `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/api/AgentTaskThreadController.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceController.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/PersonalWorkspaceRuntimeFileController.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentTaskFormalDeliveryController.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/PersonalWorkspaceExecutionServiceImpl.java`
- `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/FileSystemPersonalWorkspaceStorage.java`
- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/agent-client.mjs`
- `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/workspace-file-bridge.mjs`

这些是导航位置；实施须在最新 exact SHA worktree 核对，不能把当前 dirty 工作树当版本依据。
