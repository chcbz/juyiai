# 自家接应闭环（2026-10-12）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：自托管Runtime安装与就绪交接。**

### 最小责任链
安装器管理文件/身份/恢复；Runtime回报目标进程与能力就绪；API确认注册/授权。

固定候选与配置→隔离暂存验证→受控安装→目标进程身份/ready→通道健康→必要业务验证。

### 实施约束
CYF固定app实体目录，不恢复版本目录/current链接；Node/Python依赖可共享但可变身份/state隔离；不以shell退出或端口存在代替ready。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


任务 SELFHOST-ONBOARDING-20261012；Main 集成 Owner。源码基线：API cd1e6d6ebe714767273c440abc5edd925c2333e3，Web 235048e6820afd24f21c6ca78b4b4c30901508b7，isp-install 807b86d66153b765529bba1d547e4bcfbf0a3706；三者本地/远端 develop 已核对一致，组件工作区干净。根仓其他改动不触碰。

## 冻结契约
- local bind 不创建 installation、不注册/启停 Runtime、不返回任何密钥。保留 agentId/profileId；新增 runtimeSetup 对象：runtimeProtocolVersion="v1", tenantId/clientId/canonicalAgentId（来自可信 Scope 和绑定结果）, manifestVersion="1", installationCreatePath="/agent/runtime/v1/installations", guideUrl="https://github.com/chcbz/juyiai-runtime/blob/main/docs/cyf-agent-runtime-v1-self-host.md"。不写死 tenant/client。local 旧 envExample/profileExample 不再返回旧 API Key 教程。
- 目标端仓内工具 shell/cyf_runtime_enrollment_prepare.mjs：显式 --tenant-id --client-id --agent-id --output --expires-at（UTC ISO 或毫秒，文档固定毫秒）生成新目录中的 manifest.json、enrollment-secret（0600）、installation-request.json（6个已有 API 请求字段）、handoff.json（scope+request）。调用既有 digestManifest/runtimeSubjectKey 实现，不发网络、不登记、不启服务、不触碰旧状态。重入拒绝覆盖、输入校验、禁止 symlink 路径、不输出 secret。
- Web local 文书显示真实 scope、Runtime 指引、目标端准备及 enroll 命令；支持导入 handoff.json，仅接受协议约定 scope+request（无明文secret/JWT/API Key），scope 必须匹配当前文书；明确点击“登记安装”后，沿用登录的 agentApi 请求 POST /runtime/v1/installations，随后可 GET 同 installationId 查询。只发送6字段 request，禁止传租户或 owner 伪装作用域。禁止自动登记、定时轮询、未知响应后自动重复创建；可先查询同ID。PENDING/ACTIVE 是安装授权状态，不当作在线/业务验收。组件销毁/角色或登录scope变化忽略旧回包并清状态。请求路径固定、不接收导入URL。
- 后端沿用现有 JWT+owner 身份鉴权，不新增认证表/接口/数据库脚本，不修改 create/enroll 权限。
- 旧客户端首次迁入与新 Runtime 原位版本升级分开：后者不重新 enroll。旧状态备份保留，不导入/重放；运行中或未知业务须说明处置，不造历史迁移系统。切换需实际管理员权限且单一writer；共用Runtime影响需确认。说明系统模板 root 不能被非root无意使用，需匹配文件UID和运行用户。
- 文档提供安装->prepare->网页登记->profile/host配置->validate->enroll->service切换->新事项验收完整路径，并说明文本/图片能力边界。不把artifact安装成功当服务上线。

## 验证与发布边界
小范围离线Node/源码测试先行；前端正式Flow4403172，后端通过编排器串行测试及validateLayering。当前主机2026-10-12约78MiB空闲，不能启动重型构建制造磁盘耗尽，不删除他人证据。本任务不授权生产登记、服务重启、付费调用或自动发布。

### 范围澄清：现有 hosted Scope（2026-10-12）
源码发现 AgentHostedBindingTransaction.Scope 构造器现有 tenant=0 限制，local bind 也复用了它。本次不扩大为托管/绑定多区域重构，不放宽既有scope权限。文书必须从真实Scope投影，不再额外写死tenant/client；API测试使用合法tenant0和不同client/owner。准备工具和Web按显式scope校验可处理非默认tenant，但这不代表服务端多区域绑定已开放，后续专项处理。
