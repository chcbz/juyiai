# 聚义厅语音输入与会话

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：语音输入输出的基础适配。**

### 责任与业务流程
语音适配器负责真实音频协议/转写合成；议事仍处理普通请求；Web控制麦克风与播放生命周期。

用户授权录音→转写→普通议事→按配置合成/播放；错误明确反馈。

### 明确边界
不把网关健康/文字测试当真机音频通过，不因语音需求重复造会话/任务模型，未启用能力不自动打开。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
真实录音/播放、权限拒绝、取消释放设备、传输/解码错误、文本与语音输出一致；未测设备明确标出。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留语音基础合同/历史发布与未验边界，Realtime增量单列，不重复建旧STT/TTS接入。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


## 目标与范围

录音输入、转写、消息发送、语音输出、方向切换中断和录音资源释放；目标合同遵循 `docs/implementation/handoffs/JVC-OAI-SPRING-AI-REFACTOR.md` 的冻结音频架构/安全要求与本目录 design.md 的发布验收约束。accepted 源码只用于核对当前实现，不能替代应建/应验合同。本次只补齐跨仓 SDD 入口，不发明接口或扩大范围。

## 非目标

本次文档更新不创建新功能实现、不允许跳过现有安全合同、不宣布未验证的生产交付。

## 权威输入

- `docs/implementation/handoffs/JVC-OAI-RELEASE-COMPATIBILITY-20260905.md`
- `docs/implementation/handoffs/JVC-OAI-RELEASE-CONTINUATION-R4-CLOSEOUT.md`
