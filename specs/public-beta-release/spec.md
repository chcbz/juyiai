# 公共公测发布与安全整合

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：公测范围与真实交付验收。**

### 公开 Demo 与实际工作台对齐（2026-11-12）

取代原公开 Demo 的三角色分工幻灯片：公开入口使用实际办事／事项／资料／我的命名、暖白朱砂主题与移动底栏，按需求→显式确认单承办与报价→议事→成果与验收演示。模板 handoff ID 保持 research/content/collaboration，登录仅传白名单模板和原有安全宿主上下文，不传示例会话或修改后的需求。

示例状态仅在组件内存，不调用业务API、不写登录状态/钱包/事项、不上传资料，不在业务组件加入跨层 demo 分支。复用纯展示组件及导航常量；不挂载会发请求的真实工作台。固定示例余额与报价明确标注，无后台“正在生成”的假进度；验收、取消与重开显式动作，查看成果不自动验收。未演示功能说明需登录，不伪装成功。

原型及验收范围见 [本次交接](../../docs/implementation/handoffs/JUYIAI-DEMO-WORKBENCH-20261112.md)。源码完成、构建、公开分支推送与线上部署分别记录。

### 责任与业务流程
Owner按特性范围核对安全/功能/运维证据；既有发布工具负责安装事务。

固定候选和公测范围→必要测试→本地不可变制品→获授权安装→健康与真实用户主流程验收。

### 明确边界
不是所有规划功能的自动启用许可；开发、安装、健康、业务验收不能合并为一个PASS；资金/生产迁移须已有实际授权。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
身份/ACL、真实onboarding、关键用户旅程、已知限制、制品摘要与恢复边界；600秒只作整批墙钟目标。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留跨功能公测安全与实际onboarding未完成验收，不当作单次版本发布临时稿。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


## 目标与范围

按认证 tenant/client 隔离托管 Profile 与任务列表/计数，服务器运行密钥不出浏览器；公测 onboarding 与安全 preflight 集成。账号注销、交易、语音启用不随本包自动纳入。

## 非目标

本次文档更新不创建新功能实现、不允许跳过现有安全合同、不宣布未验证的生产交付。

## 权威输入

- `docs/implementation/handoffs/PWA-PREFLIGHT-SAFETY-P1.md`
- `specs/account-security-foundation/design.md`
- `specs/oauth-public-client-hardening/spec.md`
