# 2026-10-07 新最短完整流程测试

**结果：PASS_BUSINESS_CLOSURE_WITH_UI_GAPS。** 新纯文字业务闭环已实际完成；无绕数据库、直接API写或旧任务重放。流畅最短UI仍有4项确定缺口及1项待核对显示观察。完整多媒体验收仍NOT_COMPLETE。

## 测试基线与边界

线上API117（49fe947d…）、Web177/version1.0.5（9020f382…）及Client f29c2ad…；版本详情见[状态](delivery-status.md)。本轮没有源码构建或新发布，不把根旧gitlinks说成当前线上组合。真实已授权账号，经正常UI创建无附件、无悬赏资金事项，点将公孙胜；只要求两行纯文字，不调用工具或生文件。

## 实际可用完整路径

输入需求→开始办事→选择公孙胜→点将并议事→自动会话及真实答复→返回（进入点将册）→关闭点将册→事项→待开工（已点将）→打开426议事→返回（进入事项详情）→查看正式成果与验收→确认验收→全页刷新→事项/已完成/426→返回详情/重开成果→查询验收状态（只读）。

业务上的最短链已具备：创建→点将→成果→验收→completed。当前UI额外导航与状态核对不是业务前置，应按下方最小修复消除，不先铺集合系统。

## 精确服务端事实

| 项 | 实际回执 |
|---|---|
| 新task / conversation | 426 / 1760458005117 |
| request | mmd-typed-request_9d12b1aa52032f0b745b7d7fd85543c281ab4503 |
| final message | 1737392；typed READY / ANSWER / deliverable=true |
| 验收operation | fin_e2dd17013746417c9c7022134450b3f1039a28c3d72ce6fe93dfaaa4c499588f |
| 正式delivery | finalization_delivery_ac7819b693c49fc89e6a562b4b40019e1dc5718c29ad179dcf37fea2727565ba；accepted，revision1 / deliveryVersion1 |
| 领域task | completed / taskVersion4（创建0→点将1→正式验收完成4） |
| 正式成果 | UTF-8 55字节；SHA256 671eb094fbe5916c30e0a06747b5ec56a7fc54491ab000fefc863917252c59a7 |
| 刷新与查询 | 领域仍completed；仅原operation GET后成果UI完成，未二次验收POST |

原文：
```
最短流程已走通。
验证标记：Cedar path 807.
```

messageSource.finalDigest与文本字节SHA用途不同，均留存原值。只冻结本次1项正文，没有“可选保存”前置；正式delivery另外包含manifest，并非第二个业务成果。

## 最短流程缺口（记录，尚未修复）

| ID | 实测缺口 | 最小补齐与完成条件 |
|---|---|---|
| SF01 | 点将自动议事的返回进入点将册，不是事项详情；成果验收入口需要事项列表绕行。 | 原task作用域返回事项详情，提供可达的成果入口；不新建成果查询/集合系统。 新事项创建、点将、议事完成后正常返回即可到同事项成果验收；不需要关闭/找列表/再进入议事。 |
| SF02 | 点将及验收完成后Overview卡片仍待领令/待安排，刷新后才变已完成/公孙胜。 | 复用成功操作回执触发当前事项Overview读取/投影刷新，保留身份隔离。 一次点将/验收后无需页面重载，Overview与领域状态一致；不发送第二次业务POST。 |
| SF03 | 创建成功及验收后首页输入仍保留88字原需求；全页刷新后为0字。 | 只在创建明确成功后清空本次已提交正文，歧义/失败保留草稿。 成功创建后草稿清空；未受理时不清空，也不因为输入残留创建第二事项。 |
| SF04 | 刷新重开已完成事项成果页，恢复持久验收intent后显示继续验收/验收尚未完成；点击查询验收状态的原operation GET才恢复完成。 | 恢复原验收intent时自动只读核对同operation；未核对时显示未知而非尚未完成，不自动POST。 刷新重开保持同一operation/selectedOutputs，读取后显示需求已完成，不要求用户再次验收；未知/失败不伪报成功。 |

SF05：议事DOM快照含两处原需求；需先核对可见引导/原消息是否重复，**不推断服务器重复请求**。catalog只读确认仅一条request，未重新调用Agent。

## 证据与计数限制

[机器摘要](../../docs/implementation/evidence/mmd-shortest-flow-20261007/summary.json)、[服务端刷新回执](../../docs/implementation/evidence/mmd-shortest-flow-20261007/refreshed-server-readback.json)、[验收单次UI网络](../../docs/implementation/evidence/mmd-shortest-flow-20261007/accept-once.json)、[重开后只读查询](../../docs/implementation/evidence/mmd-shortest-flow-20261007/queried-accept-status.json)、[证据摘要](../../docs/implementation/evidence/mmd-shortest-flow-20261007/manifest.json)。

点将和验收各自观察窗口实际各1次业务POST；创建监听当时仅捕获chat，未捕获agent创建POST，故只证明UI点击一次及服务端新事项，不虚构创建POST精确计数。list/search/status-counts/recommend是查询型POST，不写成全程0POST。CDP网络记录未捕获HTTP响应，HTTP200及终态由独立只读task/operation/formal-deliveries回执证明。

first-server-readback中point查询因诊断探针未传原Idempotency-Key返回400，不属于应用失败；后续使用task/catalog/原operation只读回执，不盲重试该探针。

混合改单项/精确验收、附件-only/自然澄清、音频、第二认证账号及Client develop集成仍见[余项](remaining-tasks-20261007.md)。本次通过不能替代这些NOT_COMPLETE项。

## 后续只读页面走查补录

[2026-10-07页面走查](page-interaction-prototype-20261007.md)已确认SF05为同一用户消息气泡内两段可见的重复正文，而非单纯DOM隐藏节点。没有新的业务写入/Agent调用证据，不能推断服务器重复请求。SF01–SF05尚未产品修复；离线原型只展示补齐后的目标交互。
