# CYF 验证与发布检查边界

核对：2026-11-16。规则只由[根AGENTS](../AGENTS.md)和[统一开发约束](../specs/architecture-convergence/development-principles.md)维护；本文不新增门禁、Reviewer或一套重复审批。历史文件名不代表默认必须走Flow。

- Web/API/Runtime默认在自有SSH worker `203.32.84.239` 固定源码验证/构建；控制机只编排、回传核验和受控安装，不自动回退重型构建或启动付费Flow；实际安装入口见[部署指南](DEPLOYMENT.md)，工具参数/现状见[编排说明](../ops/orchestration/README.md)。
- 必要检查须有风险与责任依据；保留身份/ACL、资金、幂等、事务、锁、制品摘要和恢复。公共机制覆盖后不在每层复制相同校验，契约不变不机械联动全部组件。
- 单次必要单元测试/构建/打包、构建锁/排队等待及回传共用600秒，异常重试经归因重新计时并保留失败；生产安装/备份恢复/启动/健康及独立业务回归另计。超限申请该次例外，不向应用请求或生产服务下传强制deadline，不原样盲重试。
- 用固定commit/tree、selector/fixture和有效证据判断可复用性；必要测试失败不能发布。文档导航成功不等于源码、制品、安装或业务验收成功。
- 变更验证按真实影响范围；全局业务结论按[聚义厅回归目录](../specs/juyiting-unified-experience/global-regression.md)明确覆盖/未测，不用核心17项冒充全局119项通过。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__aliyun-flow-gate-policy.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
