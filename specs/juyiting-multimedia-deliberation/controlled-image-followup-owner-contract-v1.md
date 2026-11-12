# 受控图像多轮 owner HTTP 与每意图授权合同 v1

日期：2026-10-01。状态：**Main 冻结本源码工作包合同，允许责任 Owner 实施；不是产品能力就绪或上线声明。** API 基线为 develop 融合候选 `8121e8d89ad0be13ddb79012b61955bac5ae8caa` / tree `e106bfa99b78c97ac2e6a765a7032a1db20dc9bf`，仍需当前组合验证后提升研发 pin。具体运行状态仅在唯一 runtime ledger，不由本文建第二台账。

## 1. 合同组成与优先级

1. 本文的边界与接线规则。
2. [最终 Owner 决策](controlled-image-followup-owner-contract-v1-owner-decisions.md)：严格 expectedPreview、嵌套 assetRef、EDIT 精确父链、错误/envelope/实际长度边界、Owner原71个精确允许路径。
3. [基础 HTTP/持久/事务详设](controlled-image-followup-owner-contract-v1-base.md)：六个端点、严格正文/响应、身份/摘要/根锁顺序、表字段与兼容验证；其 proposal/待 Main 选择字样是原始 Owner 准备记录，此处只冻结被前两项确认的内容。
4. [机器合同/允许路径](controlled-image-followup-owner-contract-v1.json) 与 [离线共同向量](fixtures/controlled-image-followup-owner-v1.json)。
5. [冻结 runtime v3](controlled-image-v3-source-wire-contract-v1.md)。旧 v1/v2 wire、初始点将与 locator 语义保持原样。

冲突以前项优先：基础详设的 flat assetId/revision 改为 nested assetRef；未定义 acknowledgement 改为既有 `UNPRICED_EXTERNAL_ACCOUNT_ONE_IMAGE_REQUEST_ATTEMPT`；issue 正文增加 exact expectedPreview；EDIT continuationOf 必填且匹配所选资产服务器 producer request/step。其余已有数值域/状态/摘要/事务合同保留。

## 2. 必须实现的业务闭包

- Preview 只读；issue 当前 server 重算 source/instruction/payload 与 model/custody/policyRevision，并精确核对用户刚看到的 expectedPreview；任何漂移 409、零写。
- 独立 operationGrant 与 FOLLOWUP_EXECUTE consent 同事务签发，admit 与 execution/run/source/chat link 同事务保留；首次 START 同事务消费；每意图仅一次外发许可。
- 原 baseline 只验证 ACTIVE/current/assignment/target/requirement/revoke，不改 operations/version/inputScope/derived flag/单费用 locator；旧 allowed.contains(operation) 不放宽、不传假 GENERATE 来执行 EDIT。
- 精确上一稿 asset 直接作为来源，不要求先归档；源由服务器反查完整 producer lineage/ACL/字节。新稿不覆盖原稿。
- 原 key GET 为纯只读；同键同正文返回已有事实，异正文 409；未知不换 key、不降级、不额外授权/执行。
- 注册 sibling、实际 inputs-v3、独立 v3 inbox/command/START 与安全过滤闭包必须真的接通；不以 DTO/parser 测试代替服务器运行链。

**源码证据补齐的72号路径**：机器合同增加 `agent/jia-agent-service/src/main/java/cn/jia/agent/security/AgentRuntimeAuthenticationFilter.java`。当前 `allowed()` 的GET只允许共享inbox，POST只允许原inputs/provider-start路径；新增v3 inbox/inputs-v3/provider-start-controlled-image-v3否则会在controller前403。仅增加冻结的三个精确method/path，保留Origin/身份/header/编码路径拒绝，不能放开整个internal前缀；新增安全集成测试覆盖正负向。Owner原71路径准备保留历史，本补充及机器合同优先。

**Spring MVC 接线约束**：`POST /chat/conversations/{conversationId}/interactions` 只能有一个映射，由现 controller 按严格 schemaVersion 分派，不在新增 controller 再注册相同 POST 造成启动歧义。新增 V3 controller 可承载独立 preview/consents/GET；必须通过包含新旧 controller 的实际 MVC mapping 回归。schema2 的正文、digest、response与拒绝行为保持兼容。

## 3. 分包不缩减全产品目标

本包冻结 `interactionKind=EXECUTE` 的生成/上一稿编辑与合法 per-intent 权限/runtime 闭包。普通无资料 CHAT 继续 fast；**并非把长期产品缩成只有手动生图**。

待续包必须闭合：同一会话持久 pending clarification/reply/resume、DISCUSSION/CLARIFICATION_REPLY 可携精确文本/图片/音频/文件 refs、AVAILABLE 不预读与显式 INSPECT、多 lineage 事件与服务端发现、唯一 Hall composer/成果卡编排与恢复、双接应、保存/正式交付/验收/需求完成。

未实现的 kind 不广告可用，不用 legacy 空 refs 回退冒充成功；WAITING_USER 不能最终成为不可回复的终点。全34产品用例/29桥fixture继续 NOT_RUN，只有完整实际证据才能通知可验收。

## 4. 实施/验证与授权

API 责任 Owner 在独占 worktree 按机器合同72路径实施，若实码发现遗漏路径先提交精确证据再由Main扩展矩阵；不把目录通配视为授权。可在API基线组合验证期间独立写源码，但提升/发布必须有合格的融合与新包组合证据。

新 bounded selector 为 Agent/Chat `mmdControlledImageFollowupV3`；连同初始 provider core、credential binding、controlled bridge全部回归。必须包括真实 MySQL/事务/并发/原键无写、初始 locator/version不变、consent-only/GEN-only不能EDIT、model/custody/policy/source preview漂移409零写、current asset lineage、重复START与runtime filter边界。

不修改 voice、初始桥语义、旧wire、正式交付或别仓源，不选择真实Provider/账户、不付费调用、不执行生产DDL。无独立Reviewer；Owner自检。Gradle仅经orchestrator，当前本地验证按已有临时授权记录 local_user_authorized；不伪造Flow。

离线共同向量是规范预期与canonical hash，不是授权或产品PASS。Owner必须用真实实现执行相应case并提交stdout/XML/事务/DB证据，保留旧失败。
