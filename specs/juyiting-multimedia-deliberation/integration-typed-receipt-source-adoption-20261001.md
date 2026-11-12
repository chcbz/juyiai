# 多媒体议事融合：回执领域修复与详设实施优先级

日期：2026-10-01，Asia/Shanghai。状态：**Web 源码已接受并推送；API 精确候选已提交，V3 实际测试失败，未晋升；完整功能未发布、不可通知验收。**

本文是只读状态与详设实施补充，不改冻结合同，不另建运行台账。Owner/gate 唯一事实仍为主工作区 `docs/implementation/TASKS.yaml#runtime_ledger_json`。

## 1. 分支与精确基线

四仓继续统一使用 `codex/juyiting-multimedia-deliberation`。18:56 [直接远端核验](integration-evidence-20260928/typed-receipt-source-adoption-20261001/branch-readback.json)证明当时各仓当前 fast/develop HEAD 都是 feature 祖先。不是重新 merge 或创建第二个分支，也不能推导之后新增 develop 提交已包含。

| 仓库 | 已推送 feature HEAD | 本轮状态 |
| --- | --- | --- |
| API | `87c0acc16bef37c35f96f0edbbc078b5ff860a46` | 保留既有接受 pin；未把未测候选提升 |
| Web | `ebb664fc8a443845577f356d0823bd6368634dfa` | Main 独立验证、FF、push、ls-remote 确认 |
| Client | `2f6907274ea5395980df0643c6b3898fa522a54f` | 未改；INSPECT 未实现 |

API 本轮候选 `642e73238edde3354a8b23654e561a496a2691f3` / tree `b529963ae8ece8f916917e998cd25db9c7fd77f6`，parent `8fc61c4d20fb8879eab501c0938fed75937ebd4d`。Main 检查 clean、两条精确写集、hash、parent/tree 后 FF 到隔离组合和验证工作区；不 cherry-pick 改写同一个提交，不把这当测试通过。它包含 CHECK-catalog 最小修复及 typed 原子闭包，本轮 V3 实际结果为 Agent37 项中34通过、3真实MySQL失败；Chat25/V2/typed 均尚未运行，见第4节。

## 2. 长期架构不变，具体施工以领域合同优先

```text
需求＋可选精确参考版本 → 显式点将并办理 → 同一悬赏会话
  ├─ 自然讨论/精确澄清回复：typed schema1，复用 durable CHAT request/turn
  ├─ 指定资料查阅：明确授权 INSPECT，只读本轮 manifest
  └─ 新生成/编辑：每意图授权 EXECUTE v3，独立费用同意、run/START
                         ↓ 持久资产＋消息 parts
                 实时展示、预览、下载、继续讨论
                   ├─ 可选保存空间引用/版本
                   └─ 精确成果集合正式交付 → 验收 → 任务完成
```

- fast 是轻量策略，不是第二套会话；多媒体不默认读取全部资料或启用全部工具。AVAILABLE 只提供目录，既不宣称读图，也不自动升级授权。
- 自然讨论唯一具体入口是 `POST /chat/conversations/{conversationId}/interactions/discussion`，以[typed 原子合同 v1](typed-deliberation-atomic-followup-contract-v1.md)及[回执补充 v1.1](typed-deliberation-receipt-adoption-contract-v1.1.md)为准。整体详设 v2 中候选统一入口、早期 schema-3 讨论候选不是新增施工要求；不再实现第二套讨论/问题状态机。
- 独立 EXECUTE v3 继续有效；模型结果只给 proposal，不签发 grant、费用同意或 START。旧 GENERATE-only grant 不借权 EDIT，精确来源及当轮授权分别校验。
- 一份权威内容保留既有平台私有根，三种用途分别持有会话资产、空间版本、正式交付 manifest 的业务引用与 ACL，不等于各 Agent 共用一个目录。双接应物化各自 run inputs，在协议指定 outputs/staging 上交；提示词解释路径，不能代替权限和字节提交协议。
- 图片/音频展示能力与 Agent 理解/生成能力分别证明；当前 Client 的 INSPECT_NOT_ENABLED 不能改名为可用能力。只读 sandbox、空工具列表不等于已证明 STRICT_NO_TOOLS。

## 3. 受理回执与实时状态必须分域

| 事实 | 不变量 | 读取方式 |
| --- | --- | --- |
| Admission receipt | 持久 `ADMITTED` / `"0"`；同键 replay 保持原 IDs、cursor 与正文绑定 | typed 受理响应/原回执 replay |
| 当前 RequestView | 原 `RUNNING/PARTIAL/COMPLETED/FAILED/CANCELLED`；requestRevision 固定 `"1"` | 原 GET request |
| 当前 TurnView/outcome | 按各自版本前进；终态不被迟到非终态覆盖 | 原事件/turn/typed-outcome 投影 |

Web 必须先验证 immutable userMessage/turn/conversation/generation/target/requestRevision 等绑定，再按实时领域采用 GET 状态；不能要求当前状态等于受理状态。API 不再从 GET 聚合状态复制 Admission，新受理与 replay 均坚持 ADMITTED/0，损坏持久回执拒绝。冻结原合同/fixture 字节不改。

本轮 API 两条修复写集仅是 `ChatTypedDiscussionAdmissionService.java` 及对应测试；覆盖 RUNNING GET 与 fresh admission 分离、COMPLETED 后 replay、损坏回执，保留正文摘要、pending CAS、身份隔离及事务边界。仍需真正 JUnit/MySQL 证明，源码静态检查不等于事务正确。

## 4. Main 实际证据及保留失败

详见[便携证据](integration-evidence-20260928/typed-receipt-source-adoption-20261001/portable-manifest.json)，包含原始日志、probe、hash 与远端回执，不覆盖前轮失败。

- Web exact ebb：13 文件 Mocha **196 PASS / 0 FAIL**；合法 RequestView 进度 probe **3/3 PASS**，正确状态域 immutable-binding probe **7/7 PASS**，原六边界、UNKNOWN 恢复及同版本 OPEN CAS probe 通过。
- 旧合成 binding probe **6 PASS / 1 FAIL** 原样保留：其唯一正向使用不合法 RequestView ADMITTED/turn WAITING。新独立 7 项 probe 使用正确 RUNNING/RECEIVED，不能为旧正向放行错误状态，也不能用旧六负向冒充本轮绑定证明。
- scoped lint **overall exit 1，不是 PASS**：896/1209 两条 unused 是未改行的基线问题，Main 对 parent 复跑 findings 相同；本轮测试文件 lint clean。
- API 最初真实 gpt_test_runner 因 `model_not_found` / unknown provider 在运行前失败，未开始 Gradle。已保留错误，关闭该句柄；明确只验证的 Terra fallback 绑定实际 Owner。没有改全局路由、启用 DeepSeek 或假装原 Verifier 在施工。
- API exact642e 正常图实测 **Agent37：34 PASS / 3 FAIL / 0 SKIP**，Main 独立核对9份新鲜XML/hash及clean source。3个实际MySQL均失败于新增 `agent_task_provider_cost_consent.chk_atpcc_purpose_union` 校验（315行）；不是此前已修的legacy CHECK。Chat25V3、82V2及typed全部11类因前序失败 **NOT_RUN**，不重复失败输入。registered raw artifact 未落盘的事实保留；实际daemon日志和9份XML已保存，不伪称完整rawlog。pgrep命中自身shell不是活Gradle；Main以真实java/orchestrator argv独立核对无残留。最小私有fixture诊断两次控制脚本分别因缺USE、手工转录缺右括号失败，own schemas 已清理且prefix=0；没有实际CHECK目录结论，未进行第三次。新的源码Owner先做source-exact计划静态核对，需新明确授权才可复现；不能改生产DDL或放宽CHECK。
- Chromium 已按 UID1000、不用 no-sandbox 实际启动，CDP Browser/Target 与正常退出通过。这仅证明浏览器前置，不是登录、Agent 沙箱、多媒体或画鸟验收。
- 18:34 观测线上 API loopback10018 connection refused、公网 empty reply；Main 已 conflict-alert，未重启 foreign 服务。该观测不是后来仍故障或已经恢复的证明；业务浏览器实测前须重新核对实际健康与精确 Runtime Owner。

## 5. 后续执行与发布条件

1. API 正常依赖图执行完整 **62 V3（含3真实隔离MySQL）→82 V2→typed全部11类现有及新增测试**；逐 phase 实际成功才进下一步，原16共同预期没跨端运行的继续 NOT_RUN。失败归因，不减 selector、借 classes 或改 fixture 过测。
2. 成功才提升 API feature 并同步 pin/便携证据；Web 的源码接受不能代替 API 或页面闭包。
3. 冻结并实施真实 INSPECT（精确 manifest、input-only 物化、诚实能力、持久单次引擎调用与未知恢复）；同一 composer 联调自然讨论/澄清/新生成/编辑。
4. 完成图、音、文、文件实时展示/预览/下载/保存，以及精确成果正式提交、验收、任务完成，覆盖双接应及有/无参考图画鸟的真实浏览器闭环。
5. 按实际里程碑发布：上线条件达成后自检合组件 develop，从验证 exact SHA 创建尚未被占用的 release；版本发布前重新核对，不覆盖旧 release。当前 release_version 仍 null，不占用示例版本号。

所有 Gradle 经 orchestrator 串行；不创建独立 Reviewer。云效暂不可用的用户临时授权下记录 `build_origin=local_user_authorized`、exact commit/tree、测试及制品 SHA-256，绝不伪造 Flow。性能仅观测，不用时延门槛中断后续步骤；权限、锁归属、事务、真实网络错误与用户取消仍保留。Provider 付费和生产数据操作没有由此获得授权。

**原 TRA01–TRA06 跨端预期、34 产品用例、按本特性版本发布均尚未完成；本轮只晋升 Web 源码，不通知“可以验收”。**
