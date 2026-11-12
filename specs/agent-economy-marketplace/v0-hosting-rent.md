# V0 addendum — 招贤令「山寨安顿」租金

用户新增需求：2026-09-05。实现入口已确认：招贤令 `mode=server` 是「山寨安顿」，`mode=local` 是「自家接应」。本文件扩展开发预览，不改动已冻结生产设计 bundle。

## 已确认规则与开发预览定价

- **只有 server 托管模式收取 SILVER 租金；local 模式不收托管租金。** Token 用量、悬赏和技能购买另计，不混入租金。
- 付款人只能是当前已认证用户，租约绑定其 scope、canonical Agent、binding 和服务端配置的租赁方案。
- 2026-09-05 用户回复“你定吧”，授权由开发方决定定价；本版选定 **每个 Agent 1,000 SILVER / 固定 30 天**，属于开发预览价，不是已上线收费或成本覆盖承诺。方案由服务端版本化配置；未配置/不完整仍返回 `HOSTING_RENT_NOT_CONFIGURED`，不能静默按 0 收费。
- 以下是本版实现方案而非额外用户定价决定：按期预付、手动续租、不自动续扣、不追收既有 Agent 历史费用。历史托管记录的迁入须单独展示并确认；不影响已有运行服务。

## 预览方案 v1（已定价，未启用）

- `planVersion`: `"1"`
- `currency`: `"SILVER"`
- `amountMicro`: `"1000000000"`（1,000 银两）
- `periodSeconds`: `"2592000"`（30 × 24 小时，不按自然月长度浮动）
- 每个 Agent 独立一份租约；按期预付、手动续租、不自动续扣。初始租期从安顿成功且服务可用时起算，续租从 `max(now, paidThrough)` 顺延 30 天。
- 安顿明确失败按原单全额退款；未知状态仍待确认。Token/技能/悬赏另计，local 不收托管租金，既有 Agent 不追收历史租金。
- 定价确认不等于激活：保留默认关闭的收费开关，完成支付/安顿/补偿/续租的定向验证和独立审查后，才随开发预览发布启用。服务端报价仍需当前付款人明确确认；不能由后台静默扣费。
- 调价发布新方案版本，不改写已付租期或已提交订单；预览外的正式商业价格另行评估。

开发预览配置目标（由 R01 Owner 接入代码，以下不是部署命令）：

```properties
agent.hosting-rent.enabled=false
agent.hosting-rent.plan-version=1
agent.hosting-rent.amount-micro=1000000000
agent.hosting-rent.period-seconds=2592000
```

## 最小闭环

1. 点击「山寨安顿」先取得服务端报价，显示每 Agent 租金/周期、预计期限、钱包余额及“任务 token 费用另计”，用户确认后付款。local 维持原接应文书流程。
2. 报价绑定 actor/persona/现有 Agent（若有）/planVersion/amountMicro/periodSeconds/有效期；新建时 Agent identity 在服务端事务生成，不接受伪造 owner、价格或到期时间。
3. 事务锁定业务租约/绑定根，校验 ownership、报价、余额、幂等；全额预留租金，生成持久 provisioning intent。余额不足不创建新绑定/租约，不写半笔账，不触发 profile 创建。
4. **托管文件写入和 Agent 启动不在资金事务内。** 提交后执行受管、幂等的安顿步骤；绑定 intent + canonical Agent，不按 personaCode 单独确定计费/工作目录归属。准备成功后事务结算租金并激活租约；从服务可用时刻计算期限。
5. 确认准备失败且无可用托管实例后全额退回，原账保留退款引用；结果未知时保留待确认/托管状态，不盲目退款，不把数据库回滚等同文件或进程回滚。失败补偿只处理本订单创建的资源，不删既有绑定/数据。
6. 同幂等键重试、重复点击、有效租期内「重整接应」不得重复扣租金或重置到期日；显式续租按 version CAS，每个续租意图最多记账一次，从 `max(now,paidThrough)` 顺延一个配置周期。
7. 租期到期显示「待续租」。本版方案：服务端拒绝新增托管工作，保留已有结果、技能授权与数据；不强停正在执行的任务、不删除目录、不通过本编排线程控制其他线程服务。续租完成后恢复新工作准入。
8. 取消未生效安顿走补偿退款；已生效租约提前退租/转 local 的剩余租期退费规则尚未确认，本版不得自动执行资金退款或自动切换以规避准入。

## HTTP/账本实现边界（待实现）

- 新增受保护租金 quote/租约查询/手动续租接口，具体 DTO 随 API 任务冻结；所有金额、版本、时间、周期使用规范字符串。
- **原 `POST /agent/personas/{personaCode}/bind` 的所有 server 入口必须走租金门禁**，不能只在新 endpoint/UI 收费而留下旧免费创建路径。local 及默认 local 不扣租金。
- 建议账本类型 `RESERVE_HOSTING_RENT` / `CAPTURE_HOSTING_RENT` / `REFUND_HOSTING_RENT`，租约专属 escrow，平台收入 `SYSTEM:HOSTING_RENT`；租金流水显示 Agent、租期、金额、状态、退款引用。不复用 ISSUE_SILVER 或技能订单类型伪装租金。
- 复用 W02 平衡、不可变流水、actor-scoped 幂等与 W03 钱包接口。对账：`gross = captured + refunded + remaining`，每笔 journal 和为 0。

## 路径与工作包

- `ECO-V0-R00`：独立、无扣费的前置准入切片；配置默认关闭/无价格，server 在绑定/文件写入前拒绝未配置或未就绪租金，local/默认 local 兼容。仅新 agent 模块入口/配置/测试，不依赖 W03 钱包，可在独立 worktree 与 W03 验证并行；此切片不表示租约、扣费或报价成功已实现。
- `ECO-V0-R01`：租金方案、租约/租金账本、幂等/准入/受管 provisioning 补偿及 API；依赖 W03 accepted。事务/ACL 核心 Owner 按项目 P0 路由，其他冻结集成可交 Terra。仅 API 独立 worktree；不要修改正在验证的 W03 tree。
- `ECO-V0-R02`：招贤令报价确认、租期/续租/失败退款状态；依赖 R01 DTO 冻结，交 Terra。主要路径 `web/src/components/juyiting/PersonaCatalogPanel.vue`、`web/src/components/world/JuyiHall.vue`、`web/src/composables/juyiting/useHallData.js` 及相应测试；独立 worktree，与 W11/W12 接口先核对后合并。
- `ECO-V0-R03`：定向 API/MySQL/Web 验证、独立审查和开发预览烟测；依赖 R01/R02，纳入 W13/W14 一起交付，不声称已上线。
- 现有 API 入口：`agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentController.java`；安顿实现：同模块 `service/impl/AgentServiceImpl.java#bindPersona/buildServerHostedBinding`。当前实现是在事务中写文件，新租金路径必须拆分为持久 intent + 提交后准备 + 确认/补偿，不能在旧方法上简单插一行扣款。

## 验收

- [ ] local 创建/重整：租金余额与租金流水不变。
- [ ] server 预览 v1 报价：每 Agent 1,000 银两 / 固定 30 天；接口为 `amountMicro="1000000000"`、`periodSeconds="2592000"`，token 另计、需确认清楚可见；未配置不创建收费实例。
- [ ] 余额不足/越权/报价过期：不扣款、不新建绑定/租约、不写托管 profile。
- [ ] server 成功：一份租约、一次准确收租、到期时间可见，钱包和平台收入守恒。
- [ ] 重试/重整/并发续租：不重复收租；版本冲突不延长租期。
- [ ] 安顿明确失败：准确退款；结果未知不错误退款；不破坏已存在实例/数据。
- [ ] 旧 server bind 不能绕过租金；到期准入由服务端执行，不仅禁用前端按钮。
- [ ] 既有 Agent 不补扣，不删除数据/技能，不强停其他线程进程。
