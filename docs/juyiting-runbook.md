# 聚义厅开发与回归 Runbook

导航与现行合同核对：2026-11-10。开发遵循[根AGENTS](../AGENTS.md)，本文是责任导航和排障方法，不是追加的业务合同或线上版本台账。

## 从哪开始

| 任务 | 首选合同/材料 |
| --- | --- |
| 需求→承办→议事→成果→验收/取消 | [整体体验](../specs/juyiting-unified-experience/spec.md)、[承办推荐](../specs/juyiting-assignee-recommendation/spec.md) |
| 正式议事、多轮、普通密议和历史 | [多媒体议事](../specs/juyiting-multimedia-deliberation/spec.md)、[会话](../specs/juyiting-conversation-sessions/spec.md)、[20条投影详设](../specs/juyiting-ui-baseline-20261006/optimization/detailed-design.md) |
| 全部技能、修订子轮、文件产物 | [技能执行主spec](../specs/juyiting-skill-execution/spec.md)、[职责RB-1](../specs/juyiting-skill-execution/responsibility-boundaries.md) |
| 资料上传/固定版本、预览和验收选版 | [个人资料](../specs/juyiting-creative-delivery-mvp/spec.md)、[UI细则](../specs/juyiting-ui-baseline-20261006/optimization/spec.md) |
| WEN钱包/预占/结算/人民币成本 | [文钱包合同](../specs/agent-economy-marketplace/beta-wen-billing.md) |
| 岗位/技能管理/托管 | [技能管理合同](../specs/juyiting-skill-execution/management-contract.md)、[托管责任](../specs/agent-economy-marketplace/spec.md) |
| 典籍维护/阅读器/手札 | [维护](../specs/archive-agent-maintenance/spec.md)、[阅读器](../specs/archive-pavilion-reader-mvp/spec.md) |
| UI及帮助/反馈 | [唯一原型](../web/prototypes/juyiting/specs/prototype-spec.md)、[UI规格](../specs/juyiting-ui-baseline-20261006/optimization/spec.md) |
| 自托管/程序路径/安装 | [自托管合同](../specs/runtime-self-host-onboarding/spec.md)、[部署指南](DEPLOYMENT.md) |

## 关键边界

- API持有业务权限、状态、事务、幂等和完成事实；bridge落实已授权执行及本机隔离；模型编排、工具处理协议/文件；Web展示权威结果。不按单个用户、好汉、技能或Provider品牌在公共层打补丁。
- 需求保存、推荐与确认承办是不同事实。发送、预览/已查看、成果正式提交与用户验收也不等价；取消不保证撤回已发生的外部副作用。
- 正式议事与普通密议按实际scope验证。典籍查询和技能查询须在同一普通密议连续两轮验证，不能借正式事项或旧回复充数。
- 固定资料版本和原成果保留；多轮修订读取真实旧成果，不把成果JSON按接口响应信封误验。工具/Provider调用、修订关系及提交终态均须有证据。
- 费用统一WEN，不保留SILVER兼容。未知成本不是0，预占不是消费，人民币工具成本不与WEN余额混算。
- 按根2026-10-24兼容规则，允许合同明确的无害新增字段及历史完成事实只读；不是“2.0以下一律不兼容”，也不重放未知/退役执行。
- 真实读取失败、未启用、未授权、未实现和合法空数据分开；通道ready、健康UP、目录可列出不证明业务或技能执行成功。

## 全局回归统一入口

使用[14类119项回归手册](../specs/juyiting-unified-experience/global-regression.md)与[权威用例数据](../specs/juyiting-unified-experience/global-regression-cases.json)。CORE17/FULL/CHANGE_IMPACT的前提、步骤、优先级、风险、证据和状态统一在该处维护，不再复制测试目录。

- 当前目录修订只是定义，全部119项NOT_RUN；原核心17项有固定候选历史通过，映射及oracle限定区域保留在手册。
- 拍照、相册实际调用按用户要求排除；普通上传和选择资料仍测试。新技能必须补齐实际目录→成功场景映射，不能目录查询代替执行。
- 缺授权、双账号、真机、开关或隔离fixture如实标状态；管理写、故障注入和服务重启只在实际获准的专用环境，不用生产他人状态造负例。
- 真UI触发；只读接口/日志/文件解析仅作辅助断言，直接调API或合成故障不冒充真实UI和正常Provider成功。

## 排障顺序

1. 记录时间、UI现象与实际部署完整版本/commit/tree/制品摘要，区分本地源码与线上。
2. 对齐脱敏Owner/tenant/client及task/session/request/execution，定位权威业务状态和真实错误码。先确认是UI操作还是直接API，缺权限/状态冲突不只报一个500。
3. 沿真实链路定位责任层。依次核对授权/状态、当前合同、工具入参、Provider原始回执、成果摘要与提交终态；不要因模型解释/HTTP200直接判成功。
4. 保留原失败，绑定固定候选修复公共根因，再验证同输入和真实影响范围；不反复催问、补发、换Agent或清HOME制造“通过”。同根因同输入连续失败两次停止盲重试。
5. 按[已有工具](../ops/orchestration/README.md)在授权范围执行验证；构建发布与回归分开计时。验收收尾核对资金、文件SHA及自有进程，不清他人缓存/生产身份。

## 当前状态与历史证据怎么读

当前部署须实际只读核验，本文不硬编码“正在运行”的历史版本。已知R5核心17项的固定候选与报告只由[核心基线](../specs/juyiting-skill-execution/core-ui-regression-baseline.json)证明原范围；不等于新全局全量通过。旧轮询、技能、典籍、帮助与发布细节沿原专题/交接追溯，不能在Runbook里层层追加成互相矛盾的当前状态。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__juyiting-runbook.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
