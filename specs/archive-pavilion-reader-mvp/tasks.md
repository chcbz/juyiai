# 案卷阁阅读 MVP tasks

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：数据驱动的典籍阅读与个人进度。**

**实施目标：** 选择书籍→读取READY活动版目录→按章读取→保存个人进度/书签/手札。
**责任落点：** 内容服务提供活动版本；阅读服务维护个人进度/书签/手札；Web按稳定原型阅读。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：不写死水浒传/120回/必需引首；书籍内容不进入启动classpath，不在启动导入/全文对账。PPT取消预览不影响典籍正文阅读。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：不同书籍/可空引首/多章节、活动版本一致性、个人数据隔离、内容读取与启动无书籍导入、阅读器受影响设备布局。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## Control/content

- [x] **H01 Contract/content**：冻结来源、许可归属、原始 SHA、120 回连续性、稳定 ID、manifest/golden fixture 和失败矩阵。Owner：main orchestrator；独立只读 Review。

## API (`api/`)

- [x] **H02 Catalog/schema**：正文 schema、initializer、确定性导入、catalog/chapter API、ETag、feature flag。P0 migration；`critical_worker` + independent reviewer。
- [x] **H03 Reader data/ACL**：进度、书签、私人手札 exact-scope、CAS、幂等、tombstone 和真实 MySQL 隔离验证。P0 ACL/transaction；`critical_worker` + independent reviewer。
- [x] **H05A Question backend**：服务端选文重建、问题/outbox/event/SSE、案卷书吏 fallback，不接受目标 Agent。P0 transaction/replay；H04 后实施。

## Web (`web/`)

- [x] **H04 Reader UI**：案卷阁双页签、目录/正文/继续阅读、进度、书签、手札、冲突状态和 responsive/accessibility。契约冻结后由 `balanced_worker` 实施。
- [x] **H05W Ask Agent UI**：选文问案卷书吏、snapshot/SSE reducer、断线恢复；不得读取 selectedAgent。

## Integration and verification

- [ ] **H06 Integration/release**：真实 MySQL、120 回 hash/count、两身份两 client ACL、浏览器闭环、ES 停止降级、旧案卷检索回归、SHA-pinned artifact、备份/恢复和 feature-flag 回滚。

## Review cadence

- H01、H02、H03、H05A 为即时独立 Review。
- H04/H05W 的低风险 UI 细项自测后按垂直切片 Review，不按按钮逐项正式 Review。
- H06 只复用匹配 tree SHA + selector + fixture digest 的证据；最终 tree 全量验证一次。
