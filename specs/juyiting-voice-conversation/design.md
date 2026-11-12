# 聚义厅语音输入与会话 — 设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：语音输入输出的基础适配。**

### 最小责任链
语音适配器负责真实音频协议/转写合成；议事仍处理普通请求；Web控制麦克风与播放生命周期。

用户授权录音→转写→普通议事→按配置合成/播放；错误明确反馈。

### 实施约束
不把网关健康/文字测试当真机音频通过，不因语音需求重复造会话/任务模型，未启用能力不自动打开。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


分阶段发布：先完成 canonical host 生命周期/运行时交接与 flags-OFF API 交付，再验证认证后的真实 STT/TTS 与 scoped Nginx，最后启用 Web。不能从文本模型可用推断音频能力；不得把 source ACCEPT、build PASS 或离线组合覆盖当作激活证明。

## 契约来源及兼容

以下原始合同为细节权威，本入口为全量盘点时补录，不替代已冻结请求/响应、ACL、事件、错误及版本合同。

- `docs/implementation/handoffs/JVC-OAI-RELEASE-COMPATIBILITY-20260905.md`
- `docs/implementation/handoffs/JVC-OAI-RELEASE-CONTINUATION-R4-CLOSEOUT.md`

无本次代码/Schema/迁移改动；后续实现必须沿现有任务 Owner 与 scoped worktree。

## 音频目标合同入口

`docs/implementation/handoffs/JVC-OAI-SPRING-AI-REFACTOR.md` 冻结 Spring AI 音频架构、admission-before-spool、handle-based 音频处理、身份/缓存隔离、内容类型/大小/时间界限及配置覆盖验收要求。发布合同还受 `JVC-OAI-RELEASE-CONTINUATION-R4-CLOSEOUT.md` 的三阶段边界约束。应建/应验要求来自这些文档；accepted API/Web 源码仅证明现状。HTTP 请求/响应逐字段合同入口尚未集中整理，列为合同追踪补齐项，不能因源码 accepted 自动认定完整语音验收。
