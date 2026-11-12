# 文钱包验收入口

现行入口核对：2026-11-10。**本轮没有新增业务执行/通过记录。** 实际验收按专项合同与固定候选原始证据读取，不继承历史SILVER检查项。

## 可观察范围

- WEN显示/金额语义和无SILVER兼容；报价未知不冒充免费。
- 需求保存、推荐、确认承办的资金时点正确；余额不足原子拒绝，无半成功。
- 多轮/重复点击/回执乱序下只预占、释放或结算一次；资金与事项终态一致。
- 验收/取消/失败恢复后核对账本及held，保留真实失败、重测与累计预算。
- 人民币成本的实际使用、未到达/未知回执与业务WEN分别记录。
- 托管/赠送/管理及双账号等场景须实际授权与隔离资源，未启用/未实现不得标PASS。

聚义厅长期用例统一引用[全局ECON分类及相关TASK/DELIVERY用例](../juyiting-unified-experience/global-regression.md#cases-econ)，不复制第二套状态台账。

## 唯一专项合同与责任

当前业务细则由[内测文钱包与成本账](beta-wen-billing.md)维护：统一WEN/整数文、报价/预占/验收/取消、人民币成本与未知用量分别处理；不保留SILVER请求/读取兼容，不恢复旧充值/提现/分账/逐token设计。身份、业务权限、资金事务、幂等与恢复保护保留。

技能定义/安装/岗位权限归技能与岗位责任层，economy只负责对应交易/资金事实；见[技能与经济职责分离](../juyiting-skill-execution/skill-economy-responsibility-separation.md)。统一执行与边界遵循[根规则](../../AGENTS.md)和[开发约束](../architecture-convergence/development-principles.md)。

**状态边界：** 专项合同中的设计、已授权迁移、源码、安装和验收按各节原日期/精确候选区分；2026-11-10文档导航整理不把未落地的移除/跨Owner交接或新操作标成已上线，不重放旧任务，也不新增生产资金迁移授权。

## 导航与历史

[主spec](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md) · [权威专项合同](beta-wen-billing.md)

被取代的旧主文档保留为[原字节快照](history/2026-11-10-documentation/acceptance.md.original)，相对引用按原文件位置解释。v0冻结合同、schema/fixture、integration pin和原receipt不改写；旧结果不升级为新业务通过。
