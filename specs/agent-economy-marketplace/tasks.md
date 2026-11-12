# 文钱包实施与接续

现行入口核对：2026-11-10。**本页是接续方式，不是全项重新待办或完成清单。**

1. 按专项合同及实际handoff核对已集成/已安装/未实现的具体切片，固定源码、Owner和授权。
2. 只实现真实未完成且已授权范围；资金事务/幂等/权限/恢复与相关回归不能省。不得照旧ISSUE_SILVER、分账或历史逐token任务重开开发。
3. 迁移/托管/移除/跨用户交接需实际授权和固定恢复措施；文档收口不授权生产写。
4. 使用现有本地工具及单次计时规则；源码、测试、制品、安装与业务验收分别取证，不从旧任务勾选或历史Run推定今天完成。

## 唯一专项合同与责任

当前业务细则由[内测文钱包与成本账](beta-wen-billing.md)维护：统一WEN/整数文、报价/预占/验收/取消、人民币成本与未知用量分别处理；不保留SILVER请求/读取兼容，不恢复旧充值/提现/分账/逐token设计。身份、业务权限、资金事务、幂等与恢复保护保留。

技能定义/安装/岗位权限归技能与岗位责任层，economy只负责对应交易/资金事实；见[技能与经济职责分离](../juyiting-skill-execution/skill-economy-responsibility-separation.md)。统一执行与边界遵循[根规则](../../AGENTS.md)和[开发约束](../architecture-convergence/development-principles.md)。

**状态边界：** 专项合同中的设计、已授权迁移、源码、安装和验收按各节原日期/精确候选区分；2026-11-10文档导航整理不把未落地的移除/跨Owner交接或新操作标成已上线，不重放旧任务，也不新增生产资金迁移授权。

## 导航与历史

[主spec](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md) · [权威专项合同](beta-wen-billing.md)

被取代的旧主文档保留为[原字节快照](history/2026-11-10-documentation/tasks.md.original)，相对引用按原文件位置解释。v0冻结合同、schema/fixture、integration pin和原receipt不改写；旧结果不升级为新业务通过。
