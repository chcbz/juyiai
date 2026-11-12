# 同会话澄清、续办与上一稿修改：源映射及下一合同详设

适用日期：2026-09-30。状态：**只读准备/拟议合同，不是已冻结wire或已实现能力**。基于Web `7821209c874995621d139da9047983f3b586d0b0`、API `083f9846ee26835e6db79892e4f7186accff467a`。本补充不创建第二套会话、不开放费用、不修改原冻结协议。

## 1. 当前确实已有和仍缺少的部分

Hall已有唯一`useHallConversation`，同一conversation用于普通聊天、首轮bootstrap采用、成果展示和归档。缺口不是再造会话，而是普通composer与成果卡EDIT分别发送/恢复，API没有合法因果/资产输入合同。

| 实码位置 | 当前事实 |
| --- | --- |
| Web `JuyiHall.vue:2003–2067,556–609` | 单会话实例；把同一activeRequest交给议事面板 |
| Web `ChatPanel.vue:181–198` | composer发送普通send-message，没有结构化澄清关联 |
| Web `BountyExecutionOutputs.vue:193–223` | 自行POST interactions及维护局部edit恢复状态；不是另一个conversation |
| Web `useHallConversation.js:124–127,1208–1260` | 普通refs被裁为type/id，经legacy stream发送 |
| API `InteractionRouter.java:19–52` | legacy只允许CHAT/INSPECT，明确拒绝EXECUTE/STATUS hint |
| API `ChatDeliberationService.java:745–774` | legacy refs仅conversation/task/message严格二字段，不支持asset/version |
| API `ChatBountyInteractionController.java:67–72` | 无actionProposal时也拒绝非空refs/replyTo/continuationOf |
| API `ChatBountyInteractionAdmissionService.java:78–94` | 执行动作同样拒绝这些字段；当前digest不含此类因果/输入字段 |
| API `ChatBountyExecutionCoordinator.java:105–106` | 实际只执行GENERATE_IMAGE，EDIT_IMAGE等WAITING_CAPABILITY |

现有成果卡请求同时带conversation_output、continuationOf和edit_image，**按源码会在admission被拒绝**。不能只改前端参数便宣称上一稿修改接通。

## 2. 上一稿的权威来源与执行输入

现有`ChatBountyAssetProjector`已持久绑定conversation/generation、request/step/execution/run/output、MIME/hash/length/revision；`ChatBountyMediaController`只在源事实匹配时返回`assetRef {assetId,revision}`；Web `bountyOutputCatalog.js`严格校验此投影。

下一合同建议沿用这个非秘密精确引用，例如：

```json
{"kind":"conversation_asset","assetRef":{"assetId":"ast_…","revision":"1"}}
```

这只是**候选shape**，须与现有workspace refs共同冻结严格联合类型；不得据此直接修改旧wire。解析必须：

1. 从认证owner及path conversation为根，精确查assetId+revision；不用latest、URL、客户端路径/摘要或自拼output tuple作authority。
2. 核对scope、live conversation generation、当前task/assignment/target/grant及所请求操作。
3. 反查persisted producer lineage，验真实MIME/hash/length及可读字节。
4. 本轮固定input snapshot，物化源字节；产生新execution/新稿，不覆盖旧稿，不要求先归档workspace。

当前`PersonalWorkspaceExecutionService`只支持fileId/version来源；实现还只接受GENERATE_IMAGE。必须先扩展来源解析及真实EDIT能力，不能把conversation资产伪装成workspace文件，也不能把grant.allowOwnTaskDerivedAssets=false改为全任务无限读取。

## 3. 下一份合同必须定义的持久因果关系

拟新增明确interactionKind：DISCUSSION / CLARIFICATION_REPLY / EXECUTE。它是新interactions入口的业务语义，不授予工具或费用权，不放宽旧/chat/stream。

请求至少明确：schemaVersion、content、canonical task/target/expectedAssignmentRevision、operation（若执行）、严格inputRefs、replyTo/continuationOf的request+step关联。具体字段名/必选关系须独立冻结；HTTP path/auth/context已确定的值仍须作一致性检查。

- DISCUSSION：轻量C0，不读取未授权附件、不附带执行副作用。
- CLARIFICATION_REPLY：只能关联仍WAITING_USER的确切pending request/step及其clarification revision；持久回复与resume事实，重验assignment/grant/input/账户authority。
- 新生成/再生成：新的显式意图，独立原key/body与permit；不是未知旧执行的隐式重试。
- EDIT：恰有符合合同的上一稿图片asset及真实EDIT-capable target；固定源revision/lineage，不借仅GENERATE能力冒充。

原幂等digest包含完整normalized kind、operation、refs、reply/continuation及scope版本；同key异正文/refs/parent为409。replyTo和continuationOf含义不能混用，不只保存在浏览器sessionStorage。

响应/GET状态至少投影request/step、kind/operation、parent lineage、pending clarification、input snapshot、execution/run关联、stateVersion/statusUrl/replay。新增字段的BigInt精度、历史缺失兼容、事件回放及服务端表/唯一约束必须一起冻结，不能仅在DTO中添字段。

## 4. 等待澄清与执行占用不能共用一个禁用开关

Web当前非终态request均busy，composer整段禁止发送；即使以后返回WAITING_USER，也无法回复。API当前按request key/intentId幂等，未提供可依赖的conversation/task收费执行占用冲突投影。

下一合同应区分：

- WAITING_USER：持久pending clarification，释放实际generation lease，允许确切回复。
- PLANNING/RUNNING等实际占用阶段：不能并发创建另一条未授权收费执行；锁范围/等待规则依据真实任务/执行事实定义，不用性能SLO或“剩余预算”拒绝请求。
- 普通讨论/只读状态与收费执行分别判定，不能为阻止第二次生成把所有聊天一起禁用。
- 权威占用投影提供owner-safe blocking request/step/state/version；这是观察，实际admission仍事务重验。未实现前不能在Web猜造GENERATION_BUSY成功/错误。
- 未知POST先按原键GET；404不证明未受理。只有用户明确继续原操作才原key/body重放；不换key、不降级legacy/CHAT/空refs。

## 5. 复用现有首轮及恢复链

继续复用`hallPointAndStartIntent`、`useHallPointAndStart`、`hallBountyBootstrap`和`useHallConversation`现有身份/授权代际、原键、状态readback与SSE恢复。initialOperation只是首轮动作，不是后续EDIT的授权集合。

成果卡和composer都向Hall同一个follow-up编排入口提交结构化意图：固定identity/conversation/task/assignment/target、原key/body、上一稿asset和父链。保留多个request lineage，而不把单个activeRequest当完整历史。未知回执/身份切换/重派/迟到事件受现有fence保护。

最小Web写集：新增纯intent/recovery helper及composable；成果卡停止自行POST；useHallConversation统一bounty follow-up；DiscussionPanel/ChatPanel/Composer显示并可取消“回复哪条澄清/哪一稿”的上下文；JuyiHall只接线，不复制resolver或恢复状态。API合同冻结前不开放相关按钮。

## 6. 实施与验证顺序

1. 冻结严格wire、因果状态/错误、输入source联合类型及assignment/grant权限；与[调用前权限设计](provider-authority-and-precall-enforcement-design-v1.md)互相引用但不混成同一授权。
2. API先实现持久pending clarification/lineage、资产resolver和事务占用事实；隔离schema/ACL/并发回归。
3. Client/API落实实际EDIT来源/执行适配及调用前门禁；不广告尚未支持的操作。
4. Web纯intent/recovery helper先测，再将成果卡与composer接到唯一Hall入口；真实跨仓组合后才开放动作。
5. 验证同会话initial→WAITING_USER→reply→resume，精确旧稿EDIT，新旧稿共存，未知回执/同key异refs409、身份/重派/迟到fence、澄清释放lease与执行并发保护。
6. mock/单测不等于真实Provider或浏览器通过；最终仍完成文本/图片/音频/文件、归档、正式交付/验收及双接应完整34产品用例，再按exact版本发布。

本包只读准备，不claim、不写应用代码、不跑Gradle/Provider、不操作生产数据；运行Owner及gate仍只在唯一runtime ledger，不增第二份台账。
