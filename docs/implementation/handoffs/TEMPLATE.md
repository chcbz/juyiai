# Task Handoff: {TASK_ID} {TITLE}

> 当前状态必须先写入 `docs/implementation/TASKS.yaml#runtime_ledger_json`；本文件只保存不可压缩的实施、失败与 Owner 自检证据，不作为第二任务台账。

## 1. 唯一台账快照

```yaml
owner: {agent: "...", profile: "...", mode: "writer|verifier|support"} # 或 null
exact_sha_tree:
  commit_sha: "40-char SHA" # 或 null
  tree_sha: "40-char SHA"   # 或 null
current_gate: "claimed|implementing|targeted_verification|verifying|blocked_*|accepted|done"
blocker: null # 或仅引用下方失败矩阵；计数和当前阻断仍以唯一台账为准
next_action: "一条可直接执行的动作"
```

## 2. 实现范围

- 目标 / 可观察验收：
- 非目标 / 已授权的下一步：
- 仓库及确认过的集成引用（记录读取时间；本地 origin/develop 不代表实时远端或线上）：
- Base commit / tree：
- Branch：
- Worktree：
- Changed files：
- 未修改/禁止范围：
- 最早定向验证（命令/selector、fixture、预期暴露的问题）：
- 接续最小上下文（规则/模块/工具路径；已确认结论；证据；阻塞；下一条动作）：
- 交接对象与入口阅读确认（仅发生交接时填写，未确认不写已收到）：

## 3. 关键设计决定

-

## 4. 验证证据

- Evidence key：`tree SHA + exact selector + fixture digest`
- Cache result：`HIT（复用，不重跑） / MISS（本 tree 新跑）`
- Exact worktree：`clean / dirty（dirty 不得登记 accepted evidence）`

```text
命令：
结果：
```

## 5. 验收条件逐项核对

- [ ] 条件一
- [ ] 条件二

## 6. 失败归因（仅失败时填写）

| 轮次 | commit/tree、selector、fixture | 分类 | 直接证据 | 根因 | 整改动作 |
| ---: | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |

> 每次失败先经统一入口登记真实归因；策略为同根因、同输入连续失败两次停止盲重试。当前工具累计两次即阻塞，尚未区分输入/根因；不得伪改计数或绕过。已进入 blocked_root_cause 时，按现有 authorize-remediation 绑定本节矩阵后有界整改，不把不同根因写成同一根因。

## 7. Owner 自检结论（不设独立 Reviewer）

- 自检 Owner / 时间：
- 验收与 diff 核对：
- 相关身份/ACL、幂等、事务、锁和恢复检查（不适用则说明）：
- 是否复用 accepted evidence：
- 残余风险：

## 8. 主动通知

- Event：`completed / abnormality / user_action_required`
- Summary：
- Executable next action：
- Notification ID / outbox record：

- 已授权下一步的执行/接收确认（无需交接时由原 Owner 继续；outbox 不代表接续）：

## 9. 开发效率记录（适用所有任务，非新台账/门禁）

仅在自然阶段变化时补记；时间使用带时区的 ISO 8601（本项目 +08:00）。未知时间留空，不推算为零，不补造历史数据。

| 里程碑 | 实际时间 | commit/tree 或证据引用 |
| --- | --- | --- |
| 开始定位 | | |
| 基线和范围确认 | | |
| 首次有效代码（不是功能完成） | | |
| 首次定向验证结果（通过或失败） | | |
| 定向验证通过 | | |
| 集成通过 / 开发完成 | | |
| 发布授权就绪（如适用） | | |
| 版本上线核验完成（如适用） | | |

| 开始—结束 | 阶段：定位/实现/验证/等待 | 原因或返工标签 | 证据 / 等待解除方式 |
| --- | --- | --- | --- |
| | | | |

- 时间段用互不重叠的任务主路径区间；并行工作只链接证据，不将多 Agent 用时相加冒充端到端耗时。返工作为实现/验证的标签，不重复计入总时间。
- 等待原因区分环境、合同、协调、授权或其他；授权等待与开发完成分列。无法完整覆盖的时间标为未知。
- 结果摘要：开发历时 / 已知等待 / 返工轮次 / 新发现缺陷与残余风险；未发布写未发布。
- 比较仅限范围、风险和验收近似的任务；没有可比历史数据时，本项仅建立基线。不得为了指标跳过必要回归、弱化断言或承诺未实测提速。
