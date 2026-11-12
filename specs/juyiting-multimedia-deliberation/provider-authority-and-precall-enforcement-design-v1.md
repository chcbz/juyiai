# Provider权限来源与调用前控制：长期详设补充 v1

适用日期：2026-09-30。状态：**源代码核验后的设计约束；费用wire尚未冻结，未实现或启用**。不修改现有native-v1冻结合同，不选择/切换Provider账户，不推断真实计费授权。宿主证据时间戳保留原值（部分为2026-10-01），不据此推断当前日期或发布日期。

## 1. 明确纠正：一次START不是一次扣费

当前客户端只保证每个native execution最多取得一次不可安全重放的executor-start attempt：在启动执行器前持久调用 `/provider-start`，ACK丢失即不启动、不重试。这个边界应保留，但**不等于生图工具仅调用一次，也不等于Provider仅扣费一次**。

Client `1812e5b5d090013338265d16ca34b0b9c257da49` / tree `430296285683b3597f7401c21e7368c5fd078107` 的实码：

| 位置 | 当前事实 | 不能推导的保证 |
| --- | --- | --- |
| `conf/codex-ws-agent/conversation-native.mjs:187–195` | START后才调用整个execute；丢ACK拒绝启动 | 同一execute内部每次工具调用均已获permit |
| `conf/codex-ws-agent/agent-client.mjs:3854–3885,3970–3977` | 启动一个通用`codex exec`，带sandbox/approval/image输入 | 工具调用allowlist/计数/调用前callback |
| 同文件`:4013–4023,4324–4340` | stdout结果/已completed的image_generation事件及最终结果计数 | 第二次调用前已拒绝；失败前未产生费用 |
| 同文件`:4407–4418` | 提示词要求exactly once | 可执行的费用门禁 |
| `conf/codex-ws-agent/app-server-adapter.mjs:366–420,482–508` | turn/start已启动模型，收到请求/通知后处理 | 无付费对话模型前置的直接生图；builtin imagegen pre-call钩子 |

仓库固定的app-server schema中`image_generation_call`也是result/status观察，不是证实可批准或拒绝调用前的hook。本核验不评价未检查的未来SDK/CLI版本。没有执行Provider探测；没有读取auth.json。

**不得宣传**：单进程、提示词、结果数=1、maxOperationCount=1或输出验证失败，能保证单次imagegen调用/单次账单。START事实也不是Provider接受或付款事实。

## 2. 两个主体、两份权限事实

### 2.1 自家接应

Profile提供CODEX_HOME，runCodex使用其凭据。客户端目前不验证实际Provider账户所有权。隔离Home和owner-issued runtime key仅证明平台身份/目录边界，不是Provider账户所有权证据。

必须区分：

- **账户operator许可**：操作者明确声明其有权使用这份非秘密binding所代表的凭据，并授权指定主体/任务/目标/用途；声明来源如owner attestation或platform operator delegation必须如实标识，不能叫Provider已验证所有权。
- **任务owner操作同意**：同意本次exact task/target/operation/input使用这个账户来源；不能扩大账户operator许可。

同一人可以具有两个角色，但仍记录各自来源。凭据不能用浏览器自报、钱包/托管/悬赏ID代替。不能读取、上传或hash auth.json来生成binding ID。

### 2.2 山寨安顿

`conf/codex-ws-agent/managed-host.mjs:349–366`从部署operator配置的`AGENT_MANAGED_HOST_TEMPLATE_HOME`复制config/auth到隔离Home；配置允许平台/第三方共享模板账户。隔离目录不改变账户来源。

必须有平台operator的独立delegation。普通task owner consent不能授权花费平台/第三方额度；Agent ownership、托管租赁或WebSocket API key也不能替代。服务器根据真实managed registration/provisioning来源判定custody，不接受客户端把shared模板自报成owner账户。

## 3. 可实施的长期执行边界

### 首选：独立受控image executor

仅在**已被operator授权且实际支持直接图像操作**的现有账户/endpoint可用时落地独立executor。它直接调用图像端点，不先通过通用聊天turn选择工具；继续复用现有run目录、精确inputs、lease、stage/commit和会话资产。

- endpoint/凭据来自受信部署/账户authority adapter；不接受浏览器URL、token或付款标志，不将Codex登录凭据假定为直接API凭据。
- 权限绑定tenant/client/owner/task/target、操作、requirement/assignment/grant版本、exact input digest、credential binding/epoch、operator delegation及撤销状态。
- START事务在现有task-root→grant→execution锁链中原子消费本次permit，记录run/lease；只有首次成功的实际caller可进行外部请求。
- 对“画一只鸟”的单次生成，上游明确授权一次outbound image request attempt；禁止HTTP库隐式重试、自动跨endpoint重定向、后备Provider/账户切换。Provider自己如何计费须依据其真实回执，不把一个HTTP请求推断成一笔确定金额账单。
- 结果未知不自动再次外发。区分PERMIT_CONSUMED、REQUEST_ATTEMPTED、PROVIDER_ACCEPTED（若证实）、OUTPUT_COMMITTED和CHARGE_OBSERVED（若可得）。记录nonce/request identity，但不保存秘密。
- 新意图/重试生成必须重新获得合法范围内permit；恢复现有执行仅查询和补交已产生结果，不再调用Provider。

### 备选：可信Provider gateway的pre-call permit

仅当所有实际生图调用都无法绕过gateway，且每次转发前同步原子消费permit时可用。stdout监听、OS wrapper或提示词不符合这个条件。当前仓库没有此hook/gateway实现。

**当前选择状态**：上述为可实施路线条件，不是已选择或已具备的Provider适配器。`CODEX_BUILTIN_IMAGEGEN`现有通用executor不能广告调用前计数保证；严格受控费用lane在缺少真实adapter/authority时继续UNAVAILABLE。不能为“先跑通”擅自换账户或放开无限工具调用。

## 4. 费用同意领域及拟议wire

当前API `083f9846ee26835e6db79892e4f7186accff467a`仍保留Grant costAuthorizationRef=null和paid=false；与74b4相比本包未改native授权代码。`AgentTaskExecutionGrantServiceImpl.verifyAdmission`仅检查costRef非空不是合法签发/消费服务，将来必须替换，不得往该列随便写字符串。

下一份**独立冻结合同**需定义：

1. 非秘密credential binding（bindingId/epoch/providerLane/custody/authoritySource），及真实当前runtime/session关联；不能单凭自声明便使READY。
2. operator delegation签发/撤销入口和权限；owner consent签发/撤销入口、原幂等键、exact assignment intent。服务器重算request/input摘要，不接受浏览器计算值作为authority。
3. 独立持久authority/consent记录：scope、target、操作、原action/key/hash、requirement/assignment/grant/input versions、binding/epoch、issuer、许可来源、状态、operator政策规定的期限、consumed run/lease。
4. capability区分UNAVAILABLE、CONSENT_REQUIRED、ACTIVE、STALE_BINDING、REVOKED、EXPIRED、CONSUMED；GET只观察，不写、不调用Provider。新START只有全部真实条件满足才eligible。
5. 原子消费与撤销race、START丢ACK、过期/身份/runtime换代、原键同正文恢复及拒绝不明确操作的语义。
6. 价格不可观测时明示UNPRICED_EXTERNAL_ACCOUNT、金额未知；不得编造payer/quoteId/金额，不把synthetic bounty preview定价当Provider价格。请求次数边界与金额预算分开表达，未经operator允许的未知费用模式不能启用。

范围内已有资金/托管/技能业务不重构。新schema必须独立拥有，不修改刚验证的atomic-intake initializer。未实际签发、消费及pre-call回归前，浏览器仍不显示假授权成功。

## 5. 最小负向自检（技术回归，不替换34产品验收）

问题证据来自本节列明的真实源码边界；仅增加对应最小检查，不增任意时延/磁盘数值门禁。

- 无operator许可、有taskOwner consent：不能消费或外发。
- 有operator许可、无owner exact意图：不能消费或外发。
- 共享template自报OWNER_PROFILE：按真实来源拒绝提权。
- scope/target/assignment/grant/input digest/binding epoch变化、撤销或过期：拒绝旧permit。
- 两个并发caller、第二次内部请求、进程重启和断连重放：外部适配器请求尝试计数不得超过实际被授权次数；使用fake计数器证明门禁位置，不把mock当真实Provider计费证据。
- START/permit ACK丢失：不盲目重试Provider、不宣称成功/未扣费。
- 多个返回产物/非可信输出：不提交为成功，但不得据此宣称未发生费用。
- CHAT/INSPECT仍无EXECUTE授权；legacy endpoint及PRIVATE/TASK边界不变。

## 6. 施工顺序与授权边界

1. 冻结账户operator许可、owner exact consent、调用前adapter合同与真实性声明；明确现有账户是否具备直接图像端点或可信gateway。
2. 按非重叠worktree实现Client声明/执行adapter、API authority/事务及Web同意体验；Owner自检，无独立Reviewer。未满足前保留默认关闭，不伪造READY。
3. 先做fake Provider调用前门禁/隔离MySQL/恢复回归，再取得**具体真实账户和调用范围**的付费操作授权，最后真实生图验证。
4. 继续同会话澄清/EDIT、文本/音频/文件保存与正式验收；收敛最新develop、绑定exact版本制品并完成双接应及34产品用例后才通知可验收。

本补充不授权生产DML/迁移、真实Provider付费调用、账户切换或服务操作；整套产品目标保持不变。
