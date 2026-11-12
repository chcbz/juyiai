# 验收

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：实时语音传输与会话生命周期。**

### 必须验证的业务结果
真实设备收发、打断/断线、权限/身份切换、资源释放与错误提示；传输可用和完整业务验收分别取证。

### 不回归边界
PCM分块大小不是总音频限制；不把传输分片当业务请求逐块入库/鉴权；不臆造Provider能力或自动启用付费服务。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


- [x] API 新模式只连接 Realtime；离线协议/错误/清理及 WAV/身份/缓存回归通过。
- [x] 浏览器可生成 24k mono PCM16 WAV，转写确认与明确 Agent/上下文发送语义保留。
- [x] 正确识别 WAV 回复，取消/迟到/身份隔离与旧相关测试通过。
- [x] exact API/Web commit/tree 的构建及制品摘要，采用用户授权本地发布时标 build_origin=local_user_authorized。
- [x] 已验证 SHA 非覆盖合入 develop，冻结新 release 分支，按既有互斥/可恢复安装/健康规则发布。
- [x] 生产 Realtime 语音启用：R2 配置/launcher/Java 环境、API health、enabled Web live tree、公网浏览器形态 CORS/认证及引用 JS 摘要核验 PASS。
- [ ] 真实用户设备端到端验收：两次 Provider 调用预算保留，尚未发起，不冒充麦克风/扬声器验收。

已有网关能力证据：docs/implementation/VOICE_REALTIME_VERIFICATION_20260930.md。不是本实现的页面验收。

代码发布记录：`deliverables/releases/v1.13.45-voice-realtime-local-20260930/release-outcome.json`。105 API/83 Web相关测试与两组件构建PASS，API UP、Web / 与 /juyiting 200，production voice=false。浏览器worklet为oscillator验收，不冒充物理设备验收。

当前已启用结果：`docs/implementation/VOICE_REALTIME_ACTIVATION_20260930.md`；不可变 `deliverables/releases/v1.13.46-voice-realtime-activation-local-20260930/activation/activation-outcome-r2.json`。Web 新增显式确认发送，84 项相关测试及 enabled production build PASS；API 复用原 105 项测试/原制品，14 项配置解析与 actual no-JWT env PASS。首次 missing-smoke gate 失败已恢复并保留 outcome，R2 最小修正成功。自动 Provider 调用0、用户真实设备验收pending。
