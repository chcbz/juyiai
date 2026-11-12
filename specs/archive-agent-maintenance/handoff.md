# Agent 实施交接：典籍阁 Agent 任职与内容维护

- **特性名称**：典籍阁 Agent 任职与内容维护
- **Feature ID**：`archive-agent-maintenance`
- **设计版本**：D2，2026-09-28，ready / 从 M0 开始实施准备，未派发。
- **目标分支**：根仓及组件 `develop`；此交接提交只含根仓文档，不改组件 gitlink。

## 1. 给接手 Agent 的任务

按 D2 实现：聚义厅中由宋江协调或直接交办已任职吴用，通过典籍维护技能和受控 API 新增/修订典籍；先草稿、确定性校验，再按显式授权发布不可变版本并读回。以《三国演义》为真实业务验收目标，但不预设底本、章数、生产身份或付费权限。

**先完成 M0 并记录实际源码映射，再进入工作包。不要从这份文档推断任何功能已经上线，不要把旧 D1 当作接口合同。**

建议阅读顺序：

1. [需求与范围](/home/isp/wsps/cyf/specs/archive-agent-maintenance/spec.md)
2. [D2 详细设计](/home/isp/wsps/cyf/specs/archive-agent-maintenance/design.md)，尤其 §2/§3/§7/§10/§13/§18
3. [开发计划与依赖](/home/isp/wsps/cyf/specs/archive-agent-maintenance/tasks.md)
4. [验收矩阵](/home/isp/wsps/cyf/specs/archive-agent-maintenance/acceptance.md)及机器用例
5. [集成状态](/home/isp/wsps/cyf/specs/archive-agent-maintenance/integration.yaml)
6. [原 D1 风险记录](/home/isp/wsps/cyf/specs/archive-agent-maintenance/impact-assessment.md)和源码观察（仅供定位，不是最新上线基线）

## 2. 必须保持的边界

- Agent 不直连 DB，不持用户 JWT；安装、任职、任务 grant、公共发布用途授权分离。
- 首期典籍管理面板 + 原会话卡；不扩旧 ItemRef/OVERVIEW-v1、不伪装 TASK/PRIVATE、不自动创建收费悬赏。
- 复用现有命令/执行/安装/存储能力；archive job/run 是内容业务与关联记录，不是第二套 scheduler/lease/聊天队列或文件系统。
- 显式 @/密议直达目标，不强制经过宋江；两入口共同幂等受理，不重复执行。
- legacy AgentRuntime 与独立 Runtime v1 区分；逐目标协商能力，不全局 cutover，不从“已安装 Runtime”推导“可执行”。
- 保留旧水浒正文/ID/hash/anchor、私人数据、续读与选文；内容 schema 桥接不恢复旧 tenant 身份兼容。
- 私人资料读取不授予公开发布权；发布成功依据 publication + 实际读回，不依据模型回复、ACK 或 inbox completed。
- 已提交相邻特性为 `juyiting-multimedia-deliberation`；它的设计状态不代表底座代码已合入。共享接口接线先核对实际组件，不整文件覆盖其他任务。

## 3. 第一次实施会话应完成什么

1. 阅读当前工作区 AGENTS、项目地图、聚义厅 runbook、唯一运行台账；检查聊天附件，选择路径归属明确的工作树。不操作其他任务进程、服务或 evidence。
2. 核对 root/API/Web/Client 最新可复现 develop SHA/tree，不用 dirty checkout pin；记录实际 schema、模块依赖和事务管理器。
3. 按 design.md §18 映射身份/安装/执行/传输接口，登记尚缺适配；给出锁顺序、DTO/错误 fixtures、共享热点 Owner 交接范围和测试 selector。
4. 在本目录产出 `implementation-baseline.md`，作为 M0 结果。实际执行状态只在 TASKS.yaml 的 runtime_ledger_json 通过 orchestrator 维护，本目录不另建状态台账。
5. 按 tasks.md §6 开始内容域、权限、安装适配和独立 Web 合同开发；有显式依赖才等待，不因某个聊天候选未就绪停止所有独立工作。

## 4. 完成与授权

每包 Owner 自检，不创建 Reviewer；所有 Gradle 经 orchestrator 串行。测试/构建/发布按执行时有效政策（包括尚有效的本地授权例外），记录 exact SHA/tree、selector、fixture digest、制品摘要与真实健康，不伪造 Flow Run。

此文档交付本身未启动实施或生产操作。接手后允许的动作仍由用户授权及项目政策决定；真实首任管理员、任职吴用、来源与公共发布用途、额外付费操作必须精确核对。未获生产激活授权时可继续源码与隔离 fixture 工作，不能新增真实典籍后再补授权。

完成回报需区分：源码完成、验证完成、应用发布、Agent 就绪、真实典籍上架；只报告实际达到的层级及一个可执行下一步。
