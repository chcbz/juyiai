# CYF规格索引（导航核对：2026-11-10）

本索引维护**30个现行责任专题**；另有5个已闭环专题、4个已退役专题和1个历史来源目录，仅供追溯。目录仍有40个不代表存在40套现行方案，另有新特性模板。**文档修订版本不等于软件版本、全部实现或线上验收。** 当前责任、业务链、边界和验收从各专题主文档开始；不按旧文件日期、任务未勾选项或历史Run推断今天的状态。

## 开发先读

- [Agent文档总入口](../docs/README.md) · [聚义厅全局回归119项](juyiting-unified-experience/global-regression.md)（定义未执行）

- [根规则](../AGENTS.md) · [规格维护规则](AGENTS.md)（含术语表与冲突仲裁） · [统一性能/职责/校验/兼容/DFX约束](architecture-convergence/development-principles.md)
- [当前交互原型](../web/prototypes/juyiting/specs/prototype-spec.md) · [实现知识库](../docs/knowledge-base/README.md) · [SDD工作流](../docs/sdd-workflow.md)
- 默认本地测试、构建和受控部署；精确源码/测试/制品摘要、锁与恢复保护保留。2026-11-09规则：单次单元测试/构建发布上限600秒，异常重试重新计时，回归验证不受此限；超限须申请例外，不向业务请求或生产服务下传deadline；不自动启动Flow或发布develop。

## 现行责任专题（30个）

表中内容为现行合同目的，不是交付状态。每个主spec已说明责任层、业务流程、边界与验收落点，并导航到原设计/任务/验收和必要继任合同。原始测试/发布状态仍查对应日期证据。

| 专题 | 现行目标 | 同范围专项合同 |
| --- | --- | --- |
| [account-security-foundation](account-security-foundation/spec.md) | 账号认证、安全会话与撤销 | 主spec及design |
| [agent-economy-marketplace](agent-economy-marketplace/spec.md) | 内测文钱包与人民币成本账 | [细则](agent-economy-marketplace/beta-wen-billing.md) |
| [api-performance-3s-slo](api-performance-3s-slo/spec.md) | 可用性优先的API性能观测与热点治理 | 主spec及design |
| [task-scheduling](task-scheduling/spec.md) | 统一后台调度、可靠唤醒与集群执行（设计中） | [设计](task-scheduling/design.md) |
| [architecture-convergence](architecture-convergence/spec.md) | 统一事实归属、性能与DFX职责 | [细则](architecture-convergence/development-principles.md) |
| [archive-agent-maintenance](archive-agent-maintenance/spec.md) | 典籍任职、资料整理与受控内容维护 | [细则](archive-agent-maintenance/design.md) |
| [archive-pavilion-reader-mvp](archive-pavilion-reader-mvp/spec.md) | 数据驱动的典籍阅读与个人进度 | 主spec及design |
| [command-observability-v1-9](command-observability-v1-9/spec.md) | 只读协作运行看板与异常定位 | 主spec及design |
| [full-tenant-gray](full-tenant-gray/spec.md) | 环境租户隔离与冻结剩余项 | 主spec及design |
| [juyiting-agent-model-governance](juyiting-agent-model-governance/spec.md) | 好汉实际模型与能力治理 | 主spec及design |
| [juyiting-assignee-recommendation](juyiting-assignee-recommendation/spec.md) | 单次模型推荐与用户显式确认承办 | 主spec及design |
| [juyiting-codex-fast-context-20260925](juyiting-codex-fast-context-20260925/spec.md) | 议事上下文连续性与执行热路径 | [细则](juyiting-codex-fast-context-20260925/../juyiting-ui-baseline-20261006/optimization/detailed-design.md) |
| [juyiting-conversation-sessions](juyiting-conversation-sessions/spec.md) | 业务会话与原生thread的适用映射 | 主spec及design |
| [juyiting-creative-delivery-mvp](juyiting-creative-delivery-mvp/spec.md) | 个人资料与固定版本文件交付 | 主spec及design |
| [juyiting-dual-orientation-experience](juyiting-dual-orientation-experience/spec.md) | 横竖屏展示壳与资源生命周期 | 主spec及design |
| [juyiting-execution-recovery](juyiting-execution-recovery/spec.md) | 既有执行回执只读核对与新方案恢复 | 主spec及design |
| [juyiting-external-commission-mvp](juyiting-external-commission-mvp/spec.md) | 同平台外部Agent承办与正式成果验收 | 主spec及design |
| [juyiting-lightweight-workbench](juyiting-lightweight-workbench/spec.md) | 聚义厅轻量工作台真实功能入口 | 主spec及design |
| [juyiting-live-map-preview](juyiting-live-map-preview/spec.md) | 复用同一地图状态的只读预览 | 主spec及design |
| [juyiting-multimedia-deliberation](juyiting-multimedia-deliberation/spec.md) | 普通请求驱动的多媒体议事闭环 | 主spec及design |
| [juyiting-skill-execution](juyiting-skill-execution/spec.md) | 原生技能执行与管理的职责收敛 | [细则](juyiting-skill-execution/native-execution-technical-design-20261027.md) |
| [juyiting-task-collaboration](juyiting-task-collaboration/spec.md) | 任务/请求/回合扩展性与协作事实 | 主spec及design |
| [juyiting-ui-baseline-20261006](juyiting-ui-baseline-20261006/spec.md) | 现行原型与议事消息/成果展示 | [细则](juyiting-ui-baseline-20261006/optimization/detailed-design.md) |
| [juyiting-unified-experience](juyiting-unified-experience/spec.md) | 最小清晰办事体验与事实展示 | 主spec及design；[全局回归119项](juyiting-unified-experience/global-regression.md)及[用例数据](juyiting-unified-experience/global-regression-cases.json)（定义未执行） |
| [juyiting-voice-conversation](juyiting-voice-conversation/spec.md) | 语音输入输出的基础适配 | 主spec及design |
| [juyiting-voice-realtime](juyiting-voice-realtime/spec.md) | 实时语音传输与会话生命周期 | 主spec及design |
| [personal-center-navigation-v1-8](personal-center-navigation-v1-8/spec.md) | 个人中心身份与功能导航 | 主spec及design |
| [public-beta-release](public-beta-release/spec.md) | 公测范围与真实交付验收 | 主spec及design |
| [runtime-self-host-onboarding](runtime-self-host-onboarding/spec.md) | 自托管Runtime安装与就绪交接 | 主spec及design |
| [username-encoding-integrity](username-encoding-integrity/spec.md) | 用户名编码与权威发送者身份 | 主spec及design |

## 已闭环专题（5个，只保留最终规格）

功能已完成发布/验收，不再作为开发入口。仅保留最终 spec（本文即最终规格）与 evidence/integration.yaml；设计/任务/验收过程文档已删除。历史发布/验收证据查各专题 `evidence/` 与 `integration.yaml`。

| 专题 | 最终规格 | 闭环依据 |
| --- | --- | --- |
| [juyiting-agent-skill-display](juyiting-agent-skill-display/spec.md) | 点将册与好汉详情的轻量能力展示 | accepted；1.16.8/1.16.9 已部署并完成范围内在线验收 |
| [juyiting-ui-optimization](juyiting-ui-optimization/spec.md) | 移动交互、导航和可访问性 | accepted；软键盘/导航/可访问性发布验收通过 |
| [agent-client-skill-refresh](agent-client-skill-refresh/spec.md) | Agent技能事实刷新 | released；2026-08-23 生产部署并核验 |
| [agent-workspace-capability-refresh](agent-workspace-capability-refresh/spec.md) | Agent执行工作目录能力刷新 | released；生产发布并核验 |
| [oauth-public-client-hardening](oauth-public-client-hardening/spec.md) | OAuth公共客户端与回调边界 | released；OAuth 加固已生产发布 |

## 已退役专题（4个，不作为开发入口）

原路径保留历史要求、失败、版本和验收证据；不再维护平行现行合同，默认项目检索不加载这些目录。未实现要求没有因退役被标为完成。

| 历史来源 | 当前责任入口 | 处理依据 |
| --- | --- | --- |
| [economy-readonly-preview-v1-7](economy-readonly-preview-v1-7/spec.md) | [责任专题](agent-economy-marketplace/spec.md) | 旧SILVER、合成预览报价和TTL已由WEN合同接替；历史预览不作为真实收费或免费凭证。只读操作不产生订单/资金/安装副作用，接口失败不伪装零余额。 |
| [single-tenant-role-isolation](single-tenant-role-isolation/spec.md) | [责任专题](full-tenant-gray/spec.md) | 字面tenant0归零迁移已被环境租户合同接替；个人owner/角色授权保留，不重跑旧迁移，不恢复冻结剩余整改。 |
| [juyiting-flow-repair-20261008](juyiting-flow-repair-20261008/spec.md) | [责任专题](juyiting-unified-experience/spec.md) | 一次性闭环修复转为整体体验和全局回归维护；旧样本不自动重放，旧Flow发布步骤不再生效。 |
| [juyiting-formal-flow-bugfix-20260923](juyiting-formal-flow-bugfix-20260923/spec.md) | [责任专题](juyiting-unified-experience/spec.md) | 旧BF缺陷/版本计划保留追溯；派发、固定资料、正式交付和返工由整体体验/技能执行合同及全局回归承接，不重开旧版本发布。 |

历史会话目录另见[codex历史来源](codex-history-closeout-20261023/spec.md)，不是业务专题。

## 明确替代关系

| 旧口径 | 现行合同 | 不变的保护 |
| --- | --- | --- |
| 云效为默认正式前置、禁止本机重型构建 | 根AGENTS本地固定源码执行；Flow仅另获授权使用 | 身份、精确制品、互斥、恢复和真实验收 |
| SILVER/微银两、合成预览价、旧报价TTL | [文钱包与人民币成本账](agent-economy-marketplace/beta-wen-billing.md) | 资金事务、幂等、金额精度、切换授权 |
| 字面tenant0、请求/JWT决定业务tenant | [环境租户](full-tenant-gray/spec.md) | 个人owner权限、公共持久化隔离；冻结剩余不重启 |
| 按技能/Provider编排通用Runtime、旧runner执行恢复 | [RB-1](juyiting-skill-execution/responsibility-boundaries.md)及原生详设 | 执行隔离、完整性、旧事实只读、新方案恢复 |
| 全量历史、50条、逐条/ID集合补查 | [20条页级投影及连续窗口](juyiting-ui-baseline-20261006/optimization/detailed-design.md) | 游标连续性、固定成果版本、身份切换隔离 |
| 取消最终回复、流缓存拼接落库 | 保留完整最终回复；流仅实时预览 | 最终事实事务与幂等 |
| 3秒/启动预算硬终止 | 性能观测与优化目标 | 真实网络错误、传输超时、用户取消 |

## 历史与模板

- [模板](_template/spec.md)：新特性填写真实业务责任、输入输出、最小失败域和验收，不复制旧资金/调度/发布方案。
- [历史会话归类](codex-history-closeout-20261023/summary-20261107.md)和[旧路径承接映射](../docs/sdd-document-map.json)保留来源；已删除旧D2/D3/UI提案不得重新生成作为当前方案。
- `integration.yaml`原有精确pin及冻结bundle/fixture/receipt不为这次整理改写。新补推荐专题未虚构SHA；未填写表示本次没有候选绑定。
- 文档检查：`./sddw check-docs`。全量文件分类/未改证据摘要及本轮差异见[收口记录](../docs/implementation/handoffs/SPEC-FULL-REFRESH-20261107.md)。
