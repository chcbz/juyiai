# CYF 实现知识库入口

导航核对：2026-11-10。**本库不是当前源码的实时镜像。** `BASELINE.yaml`及生成API清单仍是2026-08-15静态基线；后续局部增量仅证明节内日期/commit/覆盖范围。不得将“当前”旧标题、旧SILVER/runner描述或过去发布结果直接用于今天实施。

Agent先读[统一文档入口](../README.md)，需求与现行合同查[specs索引](../../specs/INDEX.md)，行为以本次固定源码与实际运行证据确认。原2026-09-06/14状态盘点是历史，不是今日交付台账。

## 按责任定位

| 主题 | 入口 | 读取边界 |
| --- | --- | --- |
| 系统、领域、组件关系 | [系统总览](01-system-overview.md) | 旧静态摘要，检查本次组件/模块边界 |
| 仓库与构建 | [仓库/交付基线](02-repositories-build-and-delivery.md) | 发布执行改读[部署指南](../DEPLOYMENT.md)和根AGENTS，旧Flow-only和计时说明不生效 |
| 后端分层 | [后端架构](03-backend-architecture.md) | 查真实源码，不能摘要代替调用链 |
| API路由定位 | [API快速索引](04-backend-api-index.md) | 仍来自旧完整清单；实际接口查源码和接口规范 |
| API逐方法旧清单 | [完整清单](04-backend-api-inventory.md) | 冻结旧来源参考；其中resource AuthenticationController原路径已不存在，不虚构替代链接 |
| Vue/状态/路由 | [前端架构](05-frontend-architecture.md) | 局部已更新与其余旧基线分别读取 |
| 聚义厅实现线索 | [端到端基线](06-juyiting-end-to-end.md) | 业务当前入口是[Runbook](../juyiting-runbook.md)，WEN/原生执行/回归看责任spec |
| 数据/权限/租户 | [数据安全基线](07-data-security-and-boundaries.md) | 以环境租户、RB-1和本次源码核实，不能恢复旧迁移假设 |
| 操作/测试参考 | [运维基线](08-operations-testing-and-change-guide.md) | 操作以[工具说明](../../ops/orchestration/README.md)和[部署指南](../DEPLOYMENT.md)为准 |
| 静态数量 | [静态盘点](appendix-static-inventory.md) | 仅原基线统计，不代表今天文件/API数量 |

旧静态摘要保留作定向源码定位，已从默认项目当前检索移除；需要时按表阅读或显式全历史检索。不能因为默认不搜而认为旧基线已经刷新。

## 检索与新鲜度

```bash
# 当前项目规则/合同；旧基线、历史计划/证据不进默认项目检索
./docs/knowledge-base/kb-search.sh --project 'WEN|多轮|典籍'
# 有明确追溯需求才扩为全历史
./docs/knowledge-base/kb-search.sh --project-all 'SILVER|旧runner'
# 传统知识库定向检索，默认不含巨大API完整清单
./docs/knowledge-base/kb-search.sh 'agent|roster|map'
./docs/knowledge-base/kb-search.sh --api AgentController
# 只读核对基线与本地checkout；STALE/DIRTY不等于线上故障
./docs/knowledge-base/kb-search.sh --freshness
```

2026-11-10本轮只读检查仍显示根/API/Web为DIRTY，API/Web SHA与旧基线不同；该次检查未fetch远端、未重建全库API清单，不改BASELINE让结果虚假变绿。检查原件见[文档收口](../implementation/handoffs/DOCS-DISCOVERY-20261110.md)。

## 维护方式

稳定知识只回写对应条目，注明真实源码、日期、覆盖范围与未验证项；新合同维护责任spec，历史测试/安装证据沿原路径保留。不要新增平行“最新架构”，不要把本文或新鲜度检查当权限/部署授权。完整流程见[SDD文档收口](../sdd-workflow.md#feature-documentation-closeout)。

原导航内容保留在[原字节快照](../implementation/archive/2026-11-10-documentation/docs__knowledge-base__README.md)，按原README目录解释相对引用；原静态基线和API清单未改写。
