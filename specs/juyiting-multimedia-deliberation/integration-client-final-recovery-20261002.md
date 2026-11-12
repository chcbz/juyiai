# INSPECT 结果持久化及重放：主 Owner 自检补充（2026-10-02）

本补充不改变领域协议、产品验收范围或运行台账。不宣称完整功能完成，也不据此发布。

## 已实际验证

证据见 [便携清单](integration-evidence-20260928/client-final-recovery-main-20261002/manifest.json)。

- v1 保留原始失败：发送返回 false 时误报 completed；发送抛异常时仍释放引擎恢复状态，结果无法重放。
- v2 只证明缺持久化回调时拒绝发送且保留引擎状态；不能当作恢复成功。
- v3 使用真实磁盘 PersistentChatInbox，重新创建实例加载记录，验证 false、throw、true-but-unconfirmed 三种情况。三种都重放相同正文、可信 receipt、outbound ID 和摘要，模型启动计数始终为 1；未收到服务端落库确认时仍为 unconfirmed。
- v3 的引擎和传输是替身，非真实服务端/真实模型验收；证据仅绑定文件摘要，不扩大到后续提交。

## 随后发现及修复接点

Client `3f76d29bd53f136b314f073975fc4772116ab132` 补充 processor recoveryControls 的 markFinalPrepared，并在恢复过程中落盘失败时保留引擎状态。定向测试由原实现 Owner 提供，不用之前探针替代 exact-source 测试。

## 尚未闭合的真实链路

API AgentWebSocketHandler 在 persistFinal 事务提交后发送既有 agent_message_saved；重复 final 也发送该回执。检查 Client 3f76d29 时尚未消费这个回执，成功发送也停留 recovery_required，因此必须补齐可信 socket、精确 profile/turn 绑定的持久终态与重试清理，并覆盖早到回执、丢回执后重复确认、重启及错误绑定。

不能因 WS 写入成功就标记服务端持久化成功；也不能无限重放作为最终产品方案。媒体实际理解、双接应、完整浏览器交付、版本构建发布仍未验收。

## 实际跨层接线增量（工作源码证据，不是冻结提交验收）

`processor-native-final-restart-v1` 运行通过：真实 AgentMessageProcessor 接受 INSPECT → runTypedInspection 接受响应丢失 → processor 调 recoverTypedInspection 查原生终态 → final 持久化 → 重建 processor/inbox 实例 → 重放相同 final。引擎启动 1 次、原生 readback 1 次、发送 2 次且内容及 ID 一致。唯一预期拒绝记录为 TURN_ACCEPTANCE_UNKNOWN。

核对 Git 对象时发现 chat-runtime 已含 Owner 正在实施的 ACK 改动，与 `3f76d29` 不同；已中止将其绑定该提交。四源码测试前后观测摘要一致，仅按记录的工作源码摘要保存，不宣称整体候选通过。引擎与 WS 仍是替身，结果仍未获服务端确认。冻结源码后才能据 exact tree 补完 ACK 及端到端验收。

## 冻结回执消费增量：8907400 已进入特性分支

[固定源码及原始测试清单](integration-evidence-20260928/client-final-ack-8907400/manifest.json)。Client 特性分支已 fast-forward 并远端 readback `8907400eccb3601c6c096e3cfdd9b6216910ef84` / tree `96cc59a2963600de0c6a04e18a56eaa382354017`；仅源码集成，默认关闭，未合 develop、安装或发布。

原有 agent_message_saved 现在按唯一已持久 INSPECT final 及目标 profile 绑定确认，持久终态后清重试；拒绝错误绑定/歧义/无准备结果/终态冲突。37项chat-runtime回归、4项ACK定向、3项processor恢复和1项typed恢复通过；存在重叠，未执行项按原日志 skip 保留，不能合计成唯一用例数。初次失败日志仍保留。

主 Owner 从 git archive 冻结源码执行真实 processor/runtime/inbox 交叉验证：接受响应未知→原生readback→落盘→发送失败→重建实例→相同final重放→早于发送返回的重复服务端回执→confirmed归档。启动/readback各1次，recovery记录与重试timer均为0，四源码摘要已核对Git对象。该回执、引擎与传输为替身，**不是实际API事务或模型理解验收**。

后续仍需真实API/Agent/媒体理解、双接应、完整浏览器及按版本发布；此前原生握手成功不提升为整个8907400候选的原生运行通过。

## 旧聊天回执兼容已补齐：d082e1c

原兼容候选979597b虽通过定向测试，但Main使用API实际非durable回执形状（无turnId/duplicate）仍复现提前严格校验误拒绝；原失败已保留。[修复及冻结验证证据](integration-evidence-20260928/client-final-ack-compat-d082e1c/manifest.json)绑定d082e1c。现在先识别唯一匹配的INSPECT turn，再校验其严格回执；旧聊天事件不改变INSPECT状态，歧义和已匹配INSPECT错误仍拒绝。

4项相关定向通过、113项未选中；Main在git archive固定源码中验证真实processor忽略旧API形状且无reject，同时原生接收响应丢失、readback、结果落盘、重启、相同final重放及早到重复ACK链仍通过（fake engine/transport/ACK）。Client特性分支已FF推送；未进行develop合入、安装、收费调用或发布。实际API服务恢复及测试账号模型额度授权仍待用户确认，不因自动续办消息视为授权。

## 当前冻结源码非收费原生验证

[精确源码非收费探查](integration-evidence-20260928/client-native-d082e1c-nonpaid/manifest.json)绑定d082e1c/tree afc199d。Main核对原始证据摘要、四个运行源码Git对象及禁止thread/turn调用的包装器；原生初始化、账号状态、模型目录、配置和MCP目录读取exit0。运行前后源码摘要一致。此证据独立于此前native-v6工作源码观测，未把历史证据改绑新tree。

模型目录元数据声明text/image不等于已看懂图片；当前`contractReady=false`、`declaration=null`，没有收费调用/turn/start，也没有音频理解能力广告。实际图片理解、生成和修改仍须授权后实测，不能用模型列表或模拟鸟图替代。当前没有在途原生进程，不重复探查以充当进度。服务恢复与现有额度使用授权已向用户询问，自动续办不是授权；本特性仍未发布。
