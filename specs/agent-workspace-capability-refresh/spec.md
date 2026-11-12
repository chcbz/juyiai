# Agent workspace capability refresh

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：Agent执行工作目录能力刷新。**

### 责任与业务流程
Runtime验证本机目录可用性与隔离；API记录能力观察；业务服务决定任务是否可用该能力。

配置或执行目录变化→Runtime验证并上报→API更新→页面读取能力事实。

### 明确边界
不是用户资料库管理；目录可用不等于授权任意文件，读取能力不触发执行或复制整个工具链。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
目录变化、失效/恢复、重复上报、身份及目录隔离、读取不触发本机扫描。

**状态：** 已闭环（released；工作目录能力刷新已生产发布并核验）。最终规格以本文为准；发布/验收证据见 [integration.yaml](integration.yaml)。过程文档已删除。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留工作目录能力刷新契约及原发布记录，与资料文件库不同。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


<!-- SDD delivery reconciliation 2026-09-06 -->
## Problem

客户端只根据基础能力、Profile 配置和已安装 Skill 上报 abilities，宋江无法区分 Agent 当前工作目录中已有的项目类型、技术栈和模块范围。

## Goals

- 每次注册和 presence 心跳根据 Profile `codexWorkdir` 重新识别项目能力。
- 将安全、稳定的工作区标签合并进现有 runtime abilities，直接供能力名册和宋江调度使用。
- 不上传绝对路径、任意文件名、依赖版本、文件内容或未知目录名称。
- 宽泛 home/host 目录没有项目 manifest 或源码标记时不推断项目能力。

## Non-goals

- 工作区标签不是 ACL、生产权限或可执行性证明。
- 不递归索引源代码，不构建语义代码搜索或向量库。
- 不修改 API/WebSocket schema、数据库字段或任务事务模型。

## Scope

- Client：`codex-ws-agent` 工作目录能力发现、注册/心跳快照和测试。
- API/Web：沿用现有 `abilities` 合同，无源代码变更。

## Constraints and risks

- 扫描必须有目录条目、深度和 manifest 大小上限，并拒绝 symlink workdir。
- 只输出固定 allowlist 标签，避免将客户名、仓库名或秘密文件名传播到服务端。
- 推断能力仍然只是调度 hint；API key、绑定、身份和 workspace policy 保持独立校验。
