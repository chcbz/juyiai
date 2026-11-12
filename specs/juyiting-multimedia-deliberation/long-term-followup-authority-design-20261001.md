# 长期融合详设补充：统一多轮入口与每意图授权

日期：2026-10-01。适用于 `juyiting-multimedia-deliberation`。**长期架构决策补充；具体 schema-3 HTTP/DDL 仍须由 API 责任 Owner 核对后冻结，不是已实现接口或上线能力。** 本文细化[融合详设 v2](fusion-detailed-design-v2.md)，不改写已冻结 v1/v2 图像桥和 [Client v3 来源合同](controlled-image-v3-source-wire-contract-v1.md)。原有多媒体、工作空间、正式交付/验收范围不缩减。

## 1. 最终产品与 fast 的关系

保留一个悬赏会话、一套持久 request/turn/step/event、一份权威资产；fast 和 multimedia 不是两个聊天系统。fast 是无执行工具、无附件字节默认预读的 CHAT 运行策略；multimedia 是同入口下可选择受权查阅、生成和编辑的业务能力。

```text
需求描述 + 可选工作空间精确参考版本
  → 显式目标点将 / 原子授权与首轮 bootstrap
  → 自动进入同一悬赏议事
      ├─ 讨论/状态：轻上下文，不默认读取附件
      ├─ 澄清：持久 pending question，可原位回复并补充资料
      ├─ 指定查阅：当轮 ACL + 能力 + 只读输入
      └─ 生成/修改：新意图 + 本轮授权 + 独立执行
  → 同会话新旧稿、多媒体 parts、预览/下载
  → 用户选择保存到空间（可选）
  → 正式提交所选成果 / 验收 / 需求完成
```

明确“画一只鸟”且授权/能力充分时可直接生成，不强制先跑 fast 模型；缺必要信息才澄清。聊天中显示图片/播放音频不等于给 Agent 读取、修改或付费权限。

## 2. 同会话多轮入口

长期分为三类显式 interaction，全部复用当前 conversation：

| kind | 用途 | 因果关系 | 执行副作用 |
| --- | --- | --- | --- |
| DISCUSSION | 普通讨论、补充文本与可用资料目录 | 无 replyTo / continuationOf | 不创建 execution/START/费用授权 |
| CLARIFICATION_REPLY | 回答仍 WAITING_USER 的精确问题 | replyTo 指向 request/step/clarificationRevision | 回复本身不产生收费执行；续办仍校验本轮权限 |
| EXECUTE | 新生成、再生成、编辑上一稿 | continuationOf 可表示前稿/规划父链，不是回复问题 | 每次新 intent、execution/run、command、consent |

`replyTo` 与 `continuationOf` 不可互换。服务端持久 pending question 及因果链，浏览器不能仅靠本地“正在回复”状态代替。

候选 HTTP 保留 `POST /chat/conversations/{conversationId}/interactions`，以独立 schemaVersion=3 分支受理；保留旧 schema-2 hash/语义及旧 `/chat/stream` 禁止 EXECUTE 的规则。候选 `GET .../interactions/request` 按原 Idempotency-Key 只读恢复。尚未冻结的字段/路径不得提前在 Web 当可用 API 开放。

## 3. 附件可用性与查阅授权分开

DISCUSSION/CLARIFICATION_REPLY **允许用户补充精确多媒体引用**，不能全部强制为空：

- `NONE`：没有 inputRefs。
- `AVAILABLE`：仅验证可见性并给出 availableRefs；不下载、不物化、CHAT 不预读字节。
- `INSPECT`：用户明确本轮查阅，目标具有真实查阅能力且来源 ACL/本轮授权有效，才固定快照并只读物化；不创建图像执行 claim/START/费用 consent。

非执行引用数量/媒体类型由实际查阅能力和权限合同定义，不套用图像执行 0–16 上限。文本、图片、音频、文件均在完整产品范围内；音频理解/生成分别核验目标能力，不因浏览器能播放而假定 Agent 能理解。

精确来源沿用独立联合类型：

```json
{"kind":"TASK_LINKED_WORKSPACE_VERSION","fileId":"...","version":"...","purpose":"REFERENCE"}
{"kind":"CURRENT_CONVERSATION_ASSET","assetRef":{"assetId":"ast_...","revision":"..."}}
```

workspace 来源须验证任务已关联的精确版本；asset 来源由服务器反查 producer lineage、scope、MIME/hash/length，不信浏览器提供的本机路径、URL、producer tuple 或摘要作为权限。编辑上一稿不要求先保存到空间。

图像执行边界保持冻结合同：GENERATE_IMAGE 为任务关联 JPEG/PNG、0–16；EDIT_IMAGE 为当前会话 JPEG/PNG asset、恰 1。其它媒体不能偷塞进此 wire，也不能为支持更多媒体直接放宽旧协议。

## 4. 每意图操作授权：解决 EDIT 的真实缺口

当前 controlled 首次点将 grant 只允许 GENERATE_IMAGE，`allowOwnTaskDerivedAssets=false`；首轮费用 locator 仅允许 NULL→locator CAS。**现源码不能仅凭新 consent 或可读 asset 就执行 EDIT。**

长期采用两层并列授权事实：

1. **parentAssignmentGrant**：原点将/task/target/assignment 的根事实；必须仍 ACTIVE/current，撤销、重派、目标漂移均阻止新的执行。
2. **perIntentOperationGrant**：认证 owner 对当前新意图的明确操作与来源授权；模型、Agent、runtime 无签发权。精确绑定 scope、task/conversation/generation、parent grant/version、assignment/requirement revision、target、request/step/intent、operation、normalized source digest、独立 consent 与 execution/run。

EDIT 本轮授权必须明确包含 EDIT_IMAGE 与所选 CURRENT_CONVERSATION_ASSET 来源；不能把 GENERATE 权限推导为 EDIT。operator account delegation、owner consent、source ACL、当前能力/租约均各自校验，互不替代。

禁止：
- 扩大或重写初始 permittedOperations；
- 简单提高 baseline grantVersion 来获得 EDIT；
- 覆盖首轮 costAuthorizationRef/locator；
- 复用 CONSUMED consent、旧 intent/run/command 或 UNKNOWN 调用；
- 用“已预览/已归档”推导新外发授权。

per-intent 签发/消费/撤销不改变原 baseline version/locator，因此不会仅因一次修改授权使已提交资产失去读取、预览、归档和正式交付权限。这些动作仍各自校验现有 owner/task/asset/formal-delivery ACL。

新任务未来可增加独立 v3 初始 operation-set，但必须显式授权、独立 preview/hash/wire；不 retroactively 扩大旧 GENERATE-only grant，也不能替代现有任务的 per-intent 授权。

## 5. 一份内容、三种用途与 Agent 目录

平台持久私有字节 + 精确版本/摘要是事实源；conversation asset、workspace file version、正式 delivery manifest 是不同业务引用/保留关系，不是三套独立文件系统。

山寨安顿和自家接应继续有各自工作目录，它们是执行缓存/沙箱，不是用户空间事实源。Agent 通过受 fence 的 manifest 获取本轮 inputs，物化到 run 隔离目录，按 command 指定的 outputs/staging 上交；服务端校验执行归属、字节长度/摘要和 producer lineage 后才能发布 part.ready。提示词只说明路径/用途，不承担授权，不能直接给任意平台目录读取权。

用户未主动保存时，会话产物仍持久且可预览/下载/编辑；保存创建工作空间引用/版本，交付创建正式所选成果快照。平台已有具体存储根/用途约束继续按[存储详设](design.md)及部署配置，不把逻辑统一误写成各 Agent 都挂载同一物理目录。

## 6. 幂等、等待与恢复

同 scope 原 key 固定完整 normalized kind/content/operation/refs/replyTo/continuationOf/版本/授权正文摘要；同键同正文回读，异正文 409。费用 preview/issue/admit 需在 HTTP 合同中明确本轮 digest 与签发时机，不混用旧首轮同意。

刷新先原 key GET；404 不证明在途 POST 未受理。UNKNOWN 不换 key、不降级 legacy/空资料，只有用户明确继续原操作才原 key/正文重放。多轮本地恢复按 request/step 保存，不能只保留 activeRequest。

WAITING_USER 允许精确澄清回复和明确讨论，不将全部 composer 禁用。没有必要信息时不产生 execution/reserve/command/START/fetch。付费执行的实际互斥和真实租约保留；忙碌按真实占用事实表达，不用 SLO、首帧慢或剩余时延预算中断。

版本下界逐领域核对：现 taskVersion/assignmentRevision 可为 0，不可一律正数；conversationGeneration、clarificationRevision、workspaceVersion、assetRevision 的独立领域约束由 Owner 源码核对后冻结。新 long wire 用 canonical decimal string，禁止 number 精度损失、+0、前导零、溢出；不把所有 revision 套一个正数规则。

## 7. Web 唯一编排与实时展示

拟 `useHallBountyFollowup` 成为 composer 和成果卡唯一意图/恢复入口；成果卡只构造精确 assetRef 和编辑请求，不自行 POST。普通无资料/无 pending 文本可以由该入口委派现有 sendHallMessage，不重构 fast。

保持 identity/auth generation、conversation/task/target/assignment/event fence；迟到读回不能改变新选择的任务或消费授权。用户可见明确“回复哪条澄清”“修改哪一稿”，可继续补充文本和资料。媒体事件必须对应持久已验证资产，刷新/重连可回放；不以本地文件路径或模型文字当图片生成成功。

## 8. 实施包、依赖及自检

| 包 | 最小范围 | 依赖/证据 |
| --- | --- | --- |
| F0 | 当前 develop 融合，保留 fast 祖先及既有媒体闭包 | exact parents/tree/blob；相关 voice + 桥实际组合 |
| F1 API Owner | schema-3 HTTP/DDL/fixture 冻结；per-intent authority、精确来源、澄清/因果链/原键回读 | 身份/ACL、事务回滚、并发/重派/撤销、真实 MySQL |
| F2 Client Owner | v3 inputs/START、真实 EDIT adapter、durable single-fetch claim 与恢复 | API F1；v2 回归、不重复外发；不得提前广告 READY |
| F3 Web Owner | 唯一 follow-up、refs 与 pending UX、统一原意图恢复、成果卡接线 | F1 HTTP 冻结后可与 F2 独立并行；页面闭包测试 |
| F4 Integration | 双接应真实组合、图音文文件预览下载/保存、正式提交验收完成 | 全部共同桥及34产品用例；构建/版本/健康证据 |

不创建独立 Reviewer；各责任 Owner 自检，Gradle 仅经 orchestrator 串行。只读准备不占构建/数据库资源，不另建运行台账。按当前本地发布临时授权记录 local_user_authorized 及 exact SHA/tree、测试和制品 SHA-256；不伪造 Flow Run。版本号发布前重新核实，1.13.45 已被其它发布占用，不能覆盖已有 release 分支。

最低新增回归：同会话 WAITING_USER→精确回复；有 refs 的 AVAILABLE 不读取字节；显式 INSPECT 不 EXECUTE；原 GENERATE grant 不能 EDIT；每意图授权+新 consent 的精确 EDIT；旧稿/新稿并存且都可读；同键异 refs/parent/kind 409；重派/撤销/迟到 fence；未知调用不再外发；归档/交付不依赖 per-intent 消费状态。

## 9. 当前状态与完成标准

截至本补充：四仓 feature 已包含 fast。API 桥 f89d4de3、Web 8b8c951、Client 71b26ce6 是已推送研发源码；Client v3 43 离线定向通过但强制 disabled、生产 poller 不调度。API develop 融合 8121e8d8 是待组合验证候选，不提前提升 pin。

schema-3 owner HTTP/per-intent/完整澄清续办仍待实现；真实 Provider 账户未选、未付费调用、34产品用例和29共同桥 fixture 仍 NOT_RUN、尚未按本特性发布。**分支/文档交付已完成，完整画鸟产品没有完成，不能通知“可以验收”。**


## 9. Owner HTTP 与 pre-preview current context 冻结补充

[owner HTTP v1](controlled-image-followup-owner-contract-v1.md)已冻结 EXECUTE 的 per-intent/source/runtime闭包，不把它误写成全部讨论/澄清已实现。[current context v1.1](controlled-image-followup-owner-context-v1.1.md)追加只读权威 tuple，解决刷新后新意图不能拼 generation/grant/assignment/requirement/target 的真实缺口；context自己的schemaVersion1不替代schema3 intent，读回无权限/字节/Provider/业务写。Web可以依冻结接口独立施工，实际API组合与页面联调后才可声称闭合。
