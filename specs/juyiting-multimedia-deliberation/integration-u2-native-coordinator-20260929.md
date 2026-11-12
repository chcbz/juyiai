# U2 原生接应与服务端执行协调（2026-09-29）

API feature exact commit `289312f0bf59c942a659609f767be101c603a989` / tree `e467a50cafeeeae276ba7ceda6370b6d2d471e2c`，已推送/readback 远端特性分支；不属于 develop 或线上版本。合并 Agent 原生 fence/inbox 与 Chat server-only 议事执行协调的测试/代码，仍**默认关闭**。当前协调仅支持没有参考资料的 `GENERATE_IMAGE` 第一纵切，所有收费执行先核对服务端任务 grant 与费用授权；无授权标记 WAITING_AUTHORIZATION，参考资料或其他操作等待所需 resolver/能力，普通聊天不能借模型文本开启执行。原生输出提交/领取须通过 Agent Runtime 身份和 fence，不把 lease 发往前端。

独立 Agent 子树 `10c958403ba3167136d4fce7a120553c6b032491` / `a5f42a176bede6a186c154776d23a78db3dbf034`：Agent 37/37、grant 18/18；合并中保留前一输出清单测试且修复两个测试方法衔接符，**最终集成树**经 orchestrator 串行有界本地测试：

| 选择器 | 结果 | 证据缓存 key |
| --- | --- | --- |
| `:chat:jia-chat-service:chatDeliberation` | 24 classes / 119 tests，0 fail/error | `fdd860fdc1181bb7949fe54acecef694886468935548cee8fb166690b7ac83ac` |
| `:agent:jia-agent-service:mmdU2ConversationOutput` | 3 classes / 39 tests，0 fail/error | `333028849ff3bf82058ce9fe5489e2257dc30418a2e603ab8b207df5260ea5be` |
| `:agent:jia-agent-service:mmdU1Grant` | 3 classes / 18 tests，0 fail/error | `6b573820fcacd29c679d58e6a67ca18a86c3dd90fb446712c45e251c95a08880` |

`ChatBountyExecutionCoordinatorTest` 5/5 属 119 项：陌生/缺失 step 不启动、异常孤儿请求拒绝、没有付费授权只等待、精确授权生成意图仅创建一次并绑定执行。单独树 `2b5c832e` 的冷构建第一次因缺本地 Gradle 发布占位参数失败，第二次 Linux OOM 于 16:17:23 杀死 daemon pid 1354027；根因分别归属，固定参数及有界内存后通过。集成树首轮测试合并失一处括号，新增修复 `289312f0` 后重测最终树。所有门禁都是**本地定向证据**，不是 MySQL 并发、发布/Provider、双接应能力或浏览器画鸟验收。

仍必须解决：有效队列可能被前 16 条长期失效记录饿死（Agent Owner 已接续修复）；使用用户已有真实付费授权机制而非伪造 `costAuthorizationRef`；可选参考图/上一稿精确输入和文件 ACL、Client 原生 fence 协议与真实生成、会话媒体 part.ready/实时展示、归档及正式交付/验收；真实数据库/迁移/用户浏览器测试。当前**不得启用新执行开关，也不得通知用户可验收**。
