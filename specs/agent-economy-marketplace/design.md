# 文钱包设计入口

现行入口核对：2026-11-10。业务流程为需求与报价事实→显式确认承办→资金预占→多轮办理→选版验收结算，或合法取消/失败释放。实际状态机、接口/持久化字段、锁序、成本与托管边界均按专项合同，不从旧SILVER设计转换出兼容执行分支。

## 唯一专项合同与责任

当前业务细则由[内测文钱包与成本账](beta-wen-billing.md)维护：统一WEN/整数文、报价/预占/验收/取消、人民币成本与未知用量分别处理；不保留SILVER请求/读取兼容，不恢复旧充值/提现/分账/逐token设计。身份、业务权限、资金事务、幂等与恢复保护保留。

技能定义/安装/岗位权限归技能与岗位责任层，economy只负责对应交易/资金事实；见[技能与经济职责分离](../juyiting-skill-execution/skill-economy-responsibility-separation.md)。统一执行与边界遵循[根规则](../../AGENTS.md)和[开发约束](../architecture-convergence/development-principles.md)。

**状态边界：** 专项合同中的设计、已授权迁移、源码、安装和验收按各节原日期/精确候选区分；2026-11-10文档导航整理不把未落地的移除/跨Owner交接或新操作标成已上线，不重放旧任务，也不新增生产资金迁移授权。

## 导航与历史

[主spec](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md) · [权威专项合同](beta-wen-billing.md)

被取代的旧主文档保留为[原字节快照](history/2026-11-10-documentation/design.md.original)，相对引用按原文件位置解释。v0冻结合同、schema/fixture、integration pin和原receipt不改写；旧结果不升级为新业务通过。
