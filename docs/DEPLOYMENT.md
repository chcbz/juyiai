# CYF 部署与恢复指南

现行规则入口核对：2026-11-10。唯一执行规则为[根AGENTS](../AGENTS.md)，具体参数和实现限制为[现有工具说明](../ops/orchestration/README.md)。本文不硬编码当前线上版本、磁盘余量或旧Run作为发布输入。

## 正式交付路径

1. 固定任务、实际授权、组件版本及完整commit/tree，分别确认本地、集成候选和实际线上；保留脏修改，不自动pull/reset或批量暂存。
2. 在独立于生产安装目录的干净源码/普通磁盘输出位置，本地执行必要单元测试、构建和打包；Web/API/本项目Runtime默认都不是Flow-only，不自动启动付费Flow。
3. 保存真实LOCAL批次、工具链、selector/fixture、必要测试结果及制品SHA-256；必要测试失败不得安装。精确输入和有效证据匹配才复用，不伪造Flow Run或把旧receipt改成本次结果。
4. 在实际发布授权内，用现有受控安装入口核对目标、锁、身份、完整性、备份与恢复条件，再安装固定制品。develop合入、构建成功和本页更新不自动授权发布。
5. 安装执行、进程/通道健康、线上文件摘要与真实业务验收分别记录。健康UP、ready或HTTP200不等于全量业务回归通过。

## 使用已有入口，不复制另一套命令

| 范围 | 权威工具/说明 |
| --- | --- |
| Web/API本地组合构建发布 | [编排说明](../ops/orchestration/README.md)，核对`local_release.py`及其实际参数/限制 |
| 后端Gradle | 先读相关build.gradle，经既有`cyf_orchestrator.py gradle`串行入口；保留定向回归、分层检查、fresh最终JAR |
| Web依赖与构建 | 同说明的共享不可变依赖集合、本地Web构建；不能对共享链接运行npm install/ci |
| Runtime/bridge | [项目固定目录规则](../AGENTS.md)、[自托管合同](../specs/runtime-self-host-onboarding/spec.md)及本任务固定外部Runtime源码/安装说明；不把Web/API组合入口当Runtime安装器 |
| 历史包/磁盘回收 | [LOCAL_ARTIFACT_RETENTION](../ops/maintenance/LOCAL_ARTIFACT_RETENTION.md)；仅明确登记且核验允许的包 |
| 业务验收 | [全局回归目录](../specs/juyiting-unified-experience/global-regression.md)及实际变更影响集 |

## 计时规则

单次构建发布时限与例外以[根AGENTS](../AGENTS.md)§单次构建发布时限为唯一口径，此处不重复。联合/集成回归、真实UI回归和业务验收单独计时，不受该上限。执行前按本次入口核实旧工具是否适配，不以规则写入冒充。

## 固定目录与恢复边界

- API生产JAR实体为 `/home/isp/hosts/cyf/api/cyf-api-kit.jar`；`/opt/cyf/service/api`仅兼容链接，不恢复第二套生产实体或在安装目录编译。
- CYF Runtime程序实体为 `/home/isp/apps/cyf-agent-runtime-v1/app/`，内部组件为`codex-bridge`。保留版本、source/hash与release-records；退役程序按根规则归档到`/home/isp/baks/cyf-agent-runtime-v1/<batch>/`，不新建按版本切换的current/release实体。
- 身份/授权/会话/ACK/锁/私有HOME及业务状态不是旧程序；不因升级、回退或省盘覆盖/清理新状态。不改身份来绕权限，不将仅程序回退当作状态兼容已验证。
- 只能控制本任务明确归属的进程和资源，不停他人服务、不抢发布锁、不清未知历史包。风险操作依实际授权与可恢复方案，不从旧计划复制命令执行。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__DEPLOYMENT.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
