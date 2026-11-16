# CYF 构建、制品与发布策略

现行入口核对：2026-11-16。文件名为历史延续，**不是Flow-only策略**。今后Web/API/Runtime统一采用[根AGENTS的现行策略](../AGENTS.md#juyiting-build-release-policy)：自有SSH worker `203.32.84.239` 测试/构建/打包，控制机回传核验并执行已获授权的原LOCAL安装事务。不自动回退控制机重型构建，不自动启动付费Flow或追踪最新develop；LOCAL是真实来源，不是Flow Run。

## 唯一操作入口

- [部署指南](DEPLOYMENT.md)：固定候选→必要验证→不可变LOCAL制品→获授权安装→健康/业务验收；不把集成develop当自动发布。
- [现有编排工具](../ops/orchestration/README.md)：参数、真实实现限制、共享依赖和串行Gradle。不要在策略文档复制一套会漂移的命令。
- [保留/回收策略](../ops/maintenance/LOCAL_ARTIFACT_RETENTION.md)：按限定范围发现历史输出（完成登记保持兼容但不作为全部回收前置），保留当前/回退绑定、身份、锁、摘要、恢复与审计。
- [SDD流程](sdd-workflow.md)：候选精确输入、测试/安装/业务结果分开，不为文档绿而改历史pin。

## 三组件执行边界

- Web/API沿用 `local_release.py` 的显式SSH参数，API内部仍由 `local_build.py --package` 委托编排器串行Gradle；先读构建文件并核对 `--plan-only`。
- Runtime沿用 `runtime_build.py` 与同一SSH传输，保留必要原生隔离测试；只生成portable代码包，不带生产身份/状态或目标ABI依赖。安装仍走原锁/CAS、固定实体目录和备份恢复事务。
- `/home/isp/apps` 放工具、`wsps/cyf-build/<批次>` 放干净快照、`state` 放磁盘输出/临时目录/持久缓存、`conf/cyf-build` 放私有配置；worker的tmpfs `/tmp` 不用于构建。
- 统一策略不代表三端一键发布器或无参自动远端已实现。具体参数、固定host key、工具链及Runtime原生兼容仅维护在既有编排说明；历史成功版本不固定为未来候选。

## 后端默认构建基线

后续API任务沿用[根规范的2026-11-13基线](../AGENTS.md#api-local-build-policy)，执行参数、单组件模板、缓存选择与失败归因统一在[编排说明](../ops/orchestration/README.md#api-local-build-baseline)。正常复用编译缓存时，同批必要测试/构建/打包及锁等待以≤300秒为性能目标；既有600秒受控停止/例外规则不变，不把一次141.108秒实测外推为冷缓存或所有负载下的保证。

在worker上使用现有LOCAL入口及专用init：保留编译缓存、关闭一次性输出的无用增量分析和Test/bootJar状态快照、只解析目标OpenCV artifact、输出无外层gzip的api.tar、结构检查一次并在发布前复核摘要。认证/权限/生产邮件/POI/制品安全、分层检查、fresh最终JAR、锁及恢复保护不删；相关业务变更须追加回归，不固定测试数量。详细参数不在此复制，Web/Runtime不机械套用API优化。

## 不变要求

制品须绑定完整源码commit/tree、版本、必要测试及SHA-256；复用必须输入与证据一致。普通磁盘构建，不用内存盘，不从脏目录或生产程序目录编译，不借旧receipt伪造本批成功。

单次必要单测/构建/打包、构建锁/排队等待及回传共用600秒；源码/工具/缓存准备单独留证，构建入口内实际依赖安装/核验不移出计时。安装/备份恢复/启动/健康及独立业务回归另计；不向生产安装或服务下传构建deadline。异常重试经归因从零计时、保留真实失败，同根因同输入连续两次失败不盲重试。工具是否已按新计时规则适配须按入口核实，不能只靠规则更新推断。超限例外及生产/收费授权仍按根规则。

Flow仅在另有实际授权时使用，不自动触发/恢复额度后自动切回、不取消他人Run。历史Run、release profile、缓存与耗时实验仅证明当时输入；若复用其仍适用测试选择，须核对实际源码/变更影响，不把同Run历史结果当本地或当前证据。

## 历史来源

本页已按2026-11-10现行责任入口收敛；旧实施记录、状态和被取代规则保留在[原文快照](implementation/archive/2026-11-10-documentation/docs__aliyun-flow-cicd-strategy.md)，按原位置解释相对引用，不作为今天执行指令。文档更新不等于全量源码/线上复验。
