# 源码核对与边界

这是**设计前只读源码核对**，不是生产巡检、运行验收、正式测试或发布证明。审计数据见 [source-audit.json](/home/isp/wsps/cyf/specs/archive-agent-maintenance/source-audit.json)。

## 1. 观察到的版本

| 仓库/位置 | 本地 HEAD | 观察到的 origin/develop |
| --- | --- | --- |
| `/home/isp/wsps/cyf` | `02d66c044a379c5b602ee854b92a56bdb1a12496` | 本轮未核对 |
| `/home/isp/wsps/cyf/api` | `3873dd6ab18992c70800658102d492c606216d63` | `e15e1a9d947e86e5f81a3288948087466a8a879c` |
| `/home/isp/wsps/cyf/web` | `c567e0593bd0334a4f6d47536e235fc1c3af7bb5` | `9854173f7f409ca2f1c862eb153b0e3574ee58ff` |
| `/home/isp/wsps/chcbz/isp-install`（client 源仓） | `40cd349637a409c1cd900e833642094272e445d9` | 本轮未核对 |

根仓、Web 和客户端路径有既有修改。本轮没有 checkout/reset/merge/pin/fetch、未操作其他聊天工作树或 evidence。远程跟踪 ref 是本地缓存，不声称最新远程或当前生产。审计同时记录 Git blob SHA 和实际工作文件 SHA-256，二者不同不能混用。

API 主要 archive/native/tool 配置在上述 HEAD 与跟踪分支之间无差异（针对检查路径的 git diff），但这不证明整个仓库相同。Web 本地 HEAD 中缺少 reader 文件；本设计读者链路以指定 origin/develop Git 对象为参考，不把该文件在工作区的缺失视为线上回归。

## 2. 关键事实与源码落点

| 事实 | 源码绝对路径（带指定 revision 的内容见审计 JSON） |
| --- | --- |
| 固定水浒书名、版本、原始/manifest 摘要、120 回 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/content/ArchiveManifestLoader.java` |
| 底层结构已有 work/edition/chapter/paragraph，但 CHECK 仍单书约束 | `/home/isp/wsps/cyf/api/chat/jia-chat-mapper/src/main/resources/db/archive-schema.sql` |
| 启动按精确列/索引/外键/CHECK 比对，不自动处理新结构 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/config/ArchiveSchemaCatalog.java` |
| 启动种子导入会走 activateExistingReady/activateLocked，可能切 active 指针 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/service/ArchiveContentImporter.java` |
| reader 固定一部作品/active 版本与统计值 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/service/ArchiveReaderServiceImpl.java` |
| 个人数据内容校验查询固定 work=shuihuzhuan 与 active | `/home/isp/wsps/cyf/api/chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/store/JdbcArchivePersonalDataStore.java` |
| 选文重建固定 edition 与章节 ID 范围，不能只改书架 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/service/ArchiveTextSelectionValidator.java` |
| API 已有阅读 Controller，无内容管理 Controller | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/archive/http/ArchiveController.java` |
| 任务工具提供创建、分配、推荐等，不代表典籍发布权限 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/tool/AgentTools.java` |
| 聊天 defaultTools 包含 AgentTools 和 ShellTools 等，不能称天然宋江私有 | `/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/config/ChatClientConfig.java` |
| Runtime principal 与 OAuth 用户身份分开且只放行固定方法/路径 | `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/security/AgentRuntimeAuthentication.java`、`/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/security/AgentRuntimeAuthenticationFilter.java` |
| 生效技能查询依赖 ACTIVE order + SUCCEEDED installation + ACTIVE entitlement | `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/skill/InstalledSkillEntitlementLookup.java` |
| 既有命令 payload/类型有严格校验，不能任意加字段 | `/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/AgentCommandCanonicalCodec.java` |
| Web 跟踪分支已有 reader 和私人数据交互，本地 HEAD 缺少 | `/home/isp/wsps/cyf/web/src/composables/juyiting/useArchiveReader.js`、`/home/isp/wsps/cyf/web/src/components/juyiting/archive/ArchiveReader.vue`、`/home/isp/wsps/cyf/web/tests/archive-reader.test.js`（以上均在指定跟踪 revision） |
| Client 已有 durable command inbox、skill installer 和 workspace file bridge，但不存在本设计典籍维护协议 | `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/agent-client.mjs`、`/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/skill-install-manager.mjs`、`/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/workspace-file-bridge.mjs` |

## 3. 对前面对话方案的补充

- “已有阅读接口，还需维护 API”方向正确，但还必须修复阅读 SQL、选文验证、schema CHECK 和 bootstrap，否则只会形成半闭环。
- “技能安装可复用”只适用于安装机制，不等于可以复用需要交易/订单的服务调用且宣称无费用依赖。
- “撤任立即失效”准确表述应为事务提交线性化：撤任提交后新写入/发布失效；撤任前已提交发布需另行有权下架。
- “通过 API”不必给模型暴露所有低层 endpoint；托管 bridge/skill SDK 持凭据并固定调用目标，模型主要提供业务意图与整理结果。

## 4. 本轮未验证

未登录生产、未确认真实管理者/吴用 owner/runtime、未安装技能、未获取或决定《三国演义》实际底本、未查生产 schema 或执行 DML/DDL、未调用收费模型、未运行 Gradle/Vite/Node 应用测试、未发布。所有拟议能力均不能写为已上线。

## 5. D2 文档提交补充（2026-09-28）

为交接仅刷新根仓 origin/develop，提交前基线为 ccd6cbabe0c9f737ae61237c0d01c4df821e8a5c，包含相邻特性 juyiting-multimedia-deliberation 的文档。独立文档工作树不带入根工作区既有修改，不更新 api/web gitlink。上述 23 文件审计仍是此前观察，未重采组件/线上基线；source-audit.json 的未 fetch 标记只描述该次源码审计，不描述后续根仓文档提交。
