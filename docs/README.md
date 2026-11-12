> **JuyiAI 开源迁移（2026-11-12）**：组件现在位于 `api/`、`web/`、`runtime/`；内部运行证据与会话历史不公开。下方历史证据链接可能不可达，不作为公开候选的通过证明。配置见根 README。

# CYF 文档总入口

导航核对：2026-11-10。**本页负责发现与分流，不是全库实现/线上已验真的声明。** 当前规则以[根AGENTS](../AGENTS.md)和用户明确决定为准。规格、实现、测试、发布状态分别取证，日期新不自动更权威。

[仓库README](../README.md) · [本目录维护规则](AGENTS.md)

## Agent 最短阅读路径

1. 根AGENTS → **本页** → 下表选一条责任路径；进入specs时同时读[规格维护规则](../specs/AGENTS.md)。不要默认加载全部docs/specs。
2. 查业务合同用[现行责任与退役索引](../specs/INDEX.md) → 对应主spec → 主spec明确指定的专项合同；查实现用相关源码及带范围的知识条目。
3. 执行前查[现有工具](../ops/orchestration/README.md)，核对实际源码和授权；历史计划、旧Run命令、模型/账号信息不是当前操作授权。
4. 测试从[聚义厅全局回归](../specs/juyiting-unified-experience/global-regression.md)进入。119项为定义，原17项仅有固定候选历史证据，不继承为今天PASS。
5. 找不到或有冲突时，在现有责任专题修正正文和真实消费者，不再新建同义“最新方案”。无法确认的内容标未核实，不自动升格成现行指令。

## 按任务找文档

| 要做什么 | 唯一首选入口 | 深入路径/边界 |
| --- | --- | --- |
| 理解仓库、组件和代码落点 | [项目地图](codex-project-map.md) | [知识库](knowledge-base/README.md)按主题检索；旧静态基线须核对源码 |
| 查全部需求与合同 | [35个现行专题及退役索引](../specs/INDEX.md) | [规格入口](../specs/README.md)；spec/design是目标合同，不是已上线证明 |
| 统一开发职责/性能/必要校验/兼容 | [开发约束](../specs/architecture-convergence/development-principles.md) | 根规则优先；专项业务合同仍归各责任专题 |
| 聚义厅办事/议事/资料/成果 | [聚义厅Runbook](juyiting-runbook.md) | [功能阅读地图](juyiting-feature-guide.md)、[整体体验合同](../specs/juyiting-unified-experience/spec.md) |
| 全局回归、冒烟、影响回归 | [全局回归手册](../specs/juyiting-unified-experience/global-regression.md) | [119项数据](../specs/juyiting-unified-experience/global-regression-cases.json)；密议与正式议事分测；拍照/相册排除 |
| UI/交互/原型 | [唯一交互原型规格](../web/prototypes/juyiting/specs/prototype-spec.md) | [体验详设](../specs/juyiting-ui-baseline-20261006/optimization/detailed-design.md)、[水浒风格参考](water-margin-style-reference.md) |
| 地图遮挡/图层/素材扩展 | [遮挡系统设计](juyiting-occlusion-system-design.md) | 原串行执行计划/视觉报告是历史，不重启旧角色/审批 |
| 技能、原生执行、管理 | [技能主spec](../specs/juyiting-skill-execution/spec.md) | [RB-1](../specs/juyiting-skill-execution/responsibility-boundaries.md)、主spec指定的原生/管理合同 |
| WEN钱包、事项报价和成本 | [文钱包合同](../specs/agent-economy-marketplace/beta-wen-billing.md) | 无SILVER兼容；实际托管/移除等以合同实施和当轮验收区分 |
| 典籍、阅读器、手札/案卷 | [典籍维护](../specs/archive-agent-maintenance/spec.md) · [阅读器](../specs/archive-pavilion-reader-mvp/spec.md) | 查询成功不证明发布/写操作已验收 |
| 账号、权限、租户隔离 | [账号安全](../specs/account-security-foundation/spec.md) · [环境租户](../specs/full-tenant-gray/spec.md) | 以责任层、实际部署和权限证据为准 |
| 任务调度/公共议事/团队协作 | [调度](../specs/task-scheduling/spec.md) · [协作](../specs/juyiting-task-collaboration/spec.md) | 设计中、开关关闭和未实现能力不冒充已上线 |
| 执行历史专项诊断 | [原工具操作说明](../specs/juyiting-execution-recovery/contract-pilot/README.md) | 只服务执行历史；不是全站、身份或发布通过证明 |
| 测试/构建/安装/恢复 | [部署指南](DEPLOYMENT.md) | [执行工具及参数](../ops/orchestration/README.md)、[构建策略](aliyun-flow-cicd-strategy.md)；默认本地，不自动启Flow |
| 包保留和磁盘清理 | [现行保留策略](../ops/maintenance/LOCAL_ARTIFACT_RETENTION.md) | 历史Flow清理报告不作为当前清理范围或删除授权 |
| 发布安排与检查边界 | [发布安排](aliyun-flow-release-scheduling.md) · [检查职责](aliyun-flow-gate-policy.md) | 规则归根AGENTS，不从旧Flow计划获得授权 |
| 旧bridge协议参考 | [历史/局部基线](codex-ws-agent.md) | 只用于定位，现行原生执行以技能主spec指定合同和实际源码为准 |
| Git与跨仓集成交付 | [Git说明](workspace-git.md) · [SDD流程](sdd-workflow.md) | 脏修改保留、只暂存本任务文件、develop不自动部署 |
| Agent角色/活动任务归属 | [实施入口](implementation/README.md) | [角色说明](../.codex/README.md)、[路由配置](implementation/MODEL_ROUTING.yaml)、唯一TASKS内嵌ledger |
| 追溯历史为何这样做 | [历史决定分类](../specs/codex-history-closeout-20261023/summary-20261107.md) | 按专题链接查原handoff/receipt；[旧路径映射](sdd-document-map.json)不当作现行实现 |

## 文档角色与有效性

| 角色 | 怎么用 | 默认检索 |
| --- | --- | --- |
| ENTRY / CURRENT_GUIDE | 发现入口和当前工作方法；不复制业务合同 | 包含 |
| CURRENT_SPEC / CURRENT_DETAIL | 当前目标、边界、状态和可观察验收；旧结果仍只限原候选 | 包含 |
| SELECTED_VERSIONED_CONTRACT | 被当前主spec明确选中的固定版本合同；保留原字节/版本 | 包含 |
| FROZEN_REGRESSION | 原核心17项固定手册；通过范围看原候选证据 | 包含 |
| BASELINE_REFERENCE | 旧源码基线摘要/API清单/协议参考，必须查相关源码；不能写成“当前已验证” | 仅显式全历史检索/定向阅读，不混入当前合同 |
| HISTORICAL_CONTEXT / HISTORICAL_EVIDENCE | 原计划、会话、交接、测试/发布证据；可追溯，不是今天指令 | 仅显式全历史检索 |
| UNSELECTED_VERSIONED_REFERENCE | 未被现行主spec选中的版本合同，不因名字有contract就恢复旧协议 | 仅显式全历史检索 |
| REFERENCE_UNVERIFIED | 归属已有专题但有效性未核实的支持资料；不得直接执行 | 仅显式全历史检索 |
| CONTENT_SOURCE | 固定内容来源/版权归属，不是操作或已上线证明 | 仅显式全历史检索 |
| TEMPLATE | 新合同/交接填写骨架，不是已完成结果 | 仅显式全历史检索 |

分类元数据维护在既有[sdd-document-map.json](sdd-document-map.json)的discovery段；原removed/历史轮次和pin不改。全量目录由原工具按实际文件生成，不维护第二套任务或发布台账。历史来源留在原路径，**不因“旧”而删除或批量改日期**；未核实资料不会静默归为有效。

## 检索与持续检查

```bash
# 默认当前入口/合同，不混入旧基线或历史执行计划
./docs/knowledge-base/kb-search.sh --project '聚义厅|多轮|WEN'
# 有追溯需求才显式包含历史、未核实资料和模板
./docs/knowledge-base/kb-search.sh --project-all 'SILVER|Run50'
# 全量Markdown角色目录：每份文件有角色、默认可检索性和责任入口
./sddw check-docs --catalog
# 全部专题入口 + 默认当前文档本地链接 + 从根AGENTS的可达性
./sddw check-docs --all-docs
# 仅知识库旧基线对比，非零表示应查源码，不伪更新BASELINE
./docs/knowledge-base/kb-search.sh --freshness
```

检查是本地路径/分类/可发现性检查，不验证远端URL、所有锚点、每条业务陈述或当前线上。默认正文搜索仍可能命中当前文档中明确标记的旧历史段，命中后须阅读节内边界；不能把搜索结果直接当有效指令。新当前资料须在责任主文档加链接，并更新discovery中的支持资料选择；新主spec/design/tasks/acceptance可自动归类，但未接入索引会被可达性检查发现。

本次范围与未核实内容见[2026-11-10收口](implementation/handoffs/DOCS-DISCOVERY-20261110.md)。本轮不执行生产操作、不重写历史验收，也不将文档整理说成业务回归通过。
