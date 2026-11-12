# 实施任务

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前实施与收口方式（2026-11-07）

**本专题：实时语音传输与会话生命周期。**

**实施目标：** 授权建立实时通道→音频分块→事件/文本显示→用户停止/断线释放与明确恢复。
**责任落点：** Realtime适配器处理音频会话/网络事件；业务权限与请求事实保持API职责。

按当前获授权的变更范围执行，不自动重开后文历史未勾选任务或旧版本排程：

1. 核对当前合同及实际责任层调用链：PCM分块大小不是总音频限制；不把传输分片当业务请求逐块入库/鉴权；不臆造Provider能力或自动启用付费服务。
2. 复用现有任务/工作区和验证入口实现最小差异；被替代临时路径与对应过时测试同批收口，不新增Reviewer/审批/独立台账。
3. 运行实际受影响回归：真实设备收发、打断/断线、权限/身份切换、资源释放与错误提示；传输可用和完整业务验收分别取证。
4. 记录精确源码/测试/未覆盖项；获部署授权才按当前本地来源工具发布，健康与业务验收分开。未获得新范围授权不重放历史任务、迁移或收费调用。

共用规则：[统一开发约束](../architecture-convergence/development-principles.md)。原任务ID、失败样本、未覆盖需求与历史证据保留；未核实的旧待办先对照后续交付，不直接重做。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


- API Owner：`VOICE-REALTIME-API-20260930`，独立 API worktree，owned paths chat voice main/test sources plus narrowly necessary starter voice config. Existing chat/Agent routing is out of scope.
- Web Owner：`VOICE-REALTIME-WEB-20260930`，独立 Web worktree，owned paths voice composable/controls, new PCM recorder/worklet, targeted voice tests. Existing shared main checkout stays untouched.
- Integration Owner：本聊天，合同、台账、相关验证、精确 SHA 合入、版本发布证据。无独立 Reviewer；Gradle 串行走 orchestrator。

运行进度仅以 docs/implementation/TASKS.yaml#runtime_ledger_json 为准。
