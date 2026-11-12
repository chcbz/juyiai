# 典籍阁 Agent 维护：兼容性与并行开发影响评估

日期：2026-09-28。对象：原 D1 草案。状态：历史兼容性评估；下列调整已纳入 D2 目标合同与验收，运行验证仍未执行。

## 1. 结论与证据边界

总体方向可保留：宋江协调/直接交办任职 Agent → 受控 API → 草稿、校验、不可变版本、发布。Agent 不直连数据库。

**D1 不是可直接开工的冻结合同**：存在一处已确认的办事列表合同不兼容，以及执行、身份、技能安装等共享边界未收敛。当前只有文档，因此本方案尚未造成运行时冲突；这不代表实施后无影响。

- 当前源码、已有精确源审计及共享规格为依据；本轮未 fetch、未核验线上版本、未执行合并模拟或应用测试。
- 运行台账采用 `/home/isp/wsps/cyf/docs/implementation/TASKS.yaml#runtime_ledger_json`，其更新时间为 2026-09-26T19:28:52+08:00。状态是记录，不证明相应 Owner 此刻仍在写代码。
- fast-deliberation 结论引用 2026-09-27 共享评估，不能视为本轮对最新远端的复测。未读取该任务的临时 evidence 目录。
- 本文保留 D1 问题的发现记录；本次交接已同步修订 design/spec/tasks/acceptance/integration 为 D2。底座到实际源码的映射仍由 M0 执行，不能称风险已通过运行验证。
- 后续文档提交核对了根仓远端 develop ccd6cbabe0c9f737ae61237c0d01c4df821e8a5c；已提交相邻特性名称为 juyiting-multimedia-deliberation。该核对不刷新此前组件源码/生产观察。

## 2. 冲突与影响矩阵

| 范围 | 性质及证据 | 可能影响 | D2 要求 |
| --- | --- | --- | --- |
| 统一办事台 | **确认不兼容**：D1 §2.3 新增 `sourceType=archive-maintenance`，OVERVIEW-v1 只接受 DRAFT/PRIVATE_CASE/LEGACY_EXECUTION/TASK；当前 HallReadServiceImpl 的类型检查及 action switch 也封闭 | 新类型被拒绝，分区可能返回错误；分页、计数、动作、权限与 mark 无配套 | 首期独立典籍管理面板、会话卡深链；暂不注入旧列表。以后版本化扩展整个投影合同，不伪装 TASK/PRIVATE |
| 多媒体悬赏议事 | 2026-09-27 redesign 是 proposed/design-only；其会话、逐轮执行、存储设计与本功能存在架构交集 | 同一需求从 chat/task 两条路径重复执行；第三套会话、调度或文件存储；发布与验收混淆 | archive job 只管理内容业务，关联统一 request/execution；共享执行身份、输入授权、传输和存储适配。发布、个人保存、正式交付/验收保持独立 |
| 快速议事及宋江上下文 | 共享评估记录候选身份、逐目标 capability、上下文恢复和 INSPECT 声明缺陷，非 merge-ready | 新工具进入不可信身份路径、吴用收到不支持的命令、重建会话丢来源或版本；共享文件文本冲突 | 经修正的统一受理/可信上下文合同接入；不另造绕过路径，不把未合入候选当稳定基座。仅对典籍请求限制工具集，不全局删其他工具 |
| Agent 通讯协作 | 合同要求 @/密议直达真实 Agent，宋江仅在明确选择协调时介入；D02 台账 accepted | 若规定所有维护都经宋江，会改变直达语义与密议可见性 | 支持宋江交办及直接对任职吴用交办，调用同一业务授权。保留 PRIVATE 的 OUTPUT_COMMITTED/manifest 成功事实，不要求 legacy 回执 |
| 招贤、任职与单租户隔离 | 同 tenant/client/persona 单一活跃绑定；招贤 roster 修复台账仍待针对性验证 | 错认吴用所有者、重复绑定、换绑后旧授权仍写入、公共查询泄漏 Agent/runtime 身份 | 使用权威 Agent ID、当前绑定版本、owner/client 校验；不抢绑、不按角色名授权。任职摘要按读者身份脱敏 |
| Runtime 接入 | legacy AgentRuntime native 认证与独立 Runtime v1 是不同协议；后者 README 明确尚未定义消费/执行命令通道 | 把“已发布 Runtime”误判为“吴用可执行”；混用 Bearer 与 AgentRuntime 凭据、扩大路径权限 | 按真实目标协商命令能力/版本，固定 transport adapter；未支持则如实待就绪。不强制全体 cutover，不复制密钥或操作其他 Agent 服务 |
| 技能市场与能力治理 | 已安装权益依赖商业订单/安装事实；deliverable skill 是交付能力治理，不等于安装包/权限 | 重复 installer/registry、伪造订单、隐含扣费、技能标签变成 ACL | 平台免费技能作为统一安装事实的新来源，保留商业合同；安装、任职、单次 grant 分离。维护结果不自动变成正式 accepted artifact 证据 |
| 现有典籍阅读 | 固定水浒/120回、schema 精确校验、种子导入、active edition、私人进度及选文校验均见源码审计 | 启动失败、重启重激活种子版、书签手札失效、旧断点被覆盖、选文引用错误版本 | 内容域通用化不能仅加书架。保留旧 catalog 形状、ID/hash/anchors、读取进度后续读、历史已发布版本访问；单独设计内容 schema 兼容发布与恢复 |

## 3. 必须独立处理的安全与正确性风险

1. **公共发布不继承私人输入授权**：用户把私人文件交给吴用读取，不等于同意把文件、手札、会话或其中的身份信息公开。发布 grant 必须绑定目标书库、精确内容版本与明确用途；来源可读与允许发布分别校验。
2. **模型输出不是执行事实**：不得把“已新增《三国演义》”、客户端 completed 或文件上传成功当 PUBLISHED。须有发布事务记录、active 指针和实际读回；消息投影可重放，不能反向制造成功。
3. **撤任、换绑、取消与发布竞争**：沿用 D1 的事务序列化边界及 epoch/grant 校验，幂等重试不重复导入/激活；不得以等待过久抢锁或放宽权限。
4. **来源正文不是指令**：书稿、导入 manifest、聊天引用仅为数据；不得通过提示注入扩权、下载任意内部地址、执行 SQL 或访问任意文件。发布前保留来源与内容校验。
5. **迁移不能借用身份兼容后门**：D1 所述旧/新 schema 兼容仅限内容结构，不恢复 `tenant_id=owner` 的旧身份读写。公共内容不附带他人私人阅读数据。
6. **性能影响与可用性分开**：导入、校验、索引和读取争用需要观测真实耗时/锁等待；不能因任意 SLO 或剩余性能预算中断工作。会话等待不长期占执行 lease，真实取消与传输错误仍保留。

## 4. 并行开发与实施顺序

不需要等待全部历史任务完成，也不需要新增独立 Reviewer。

- **M0/D2 先收敛**：冻结业务 job 与统一 execution 映射、唯一受理与幂等键、Agent/绑定/授权查询接口、安装事实适配、目标 runtime capability、前端入口及内容迁移边界。修订 design/tasks/acceptance/integration 后才把这些新合同称为冻结。
- **可独立并行**：通用 manifest 校验与 fixtures、典籍内容/版本模型、任职规则测试、独立管理面板。共享边界用已协商接口，不自行补第二套基础设施。
- **需 Owner 交接后集成**：ChatController、JuyitingAgentRelayService、AgentWebSocketHandler、认证 filter、useHallConversation、hallConversationMessages 和 agent-client。按精确提交/路径归属交接，不整文件覆盖其他修复。
- **最小闭环先行**：有权管理者通过内容 API 新增并读回一部书 → 任职吴用以草稿模式执行 → 接宋江/直达入口 → 显式预授权自动发布 → 最后扩统一办事投影。
- **上线前针对性验证**：旧水浒 reader/书签/手札/选文与续读；跨 owner/client、换绑及撤任；旧/新客户端混用；重复交办与断线恢复；私人材料到公开内容边界；内容 schema 升级/重启/恢复。文档检查不替代这些测试。

本次用户授权输出并提交文档，由其他 Agent 实施。本文不启动实施、生产 DML、任职、付费模型调用或部署，也不调整其他任务台账。

## 5. 依据

- [D2 设计与源码差距](/home/isp/wsps/cyf/specs/archive-agent-maintenance/design.md)
- [精确源码审计](/home/isp/wsps/cyf/specs/archive-agent-maintenance/source-audit.json)
- [统一办事台冻结合同](/home/isp/wsps/cyf/specs/juyiting-unified-experience/agent-execution-plan.md)
- [当前 HallReadServiceImpl 类型校验](/home/isp/wsps/cyf/api/agent/jia-agent-service/src/main/java/cn/jia/agent/service/impl/HallReadServiceImpl.java)
- [多媒体议事重设计](/home/isp/wsps/cyf/specs/juyiting-creative-delivery-mvp/workspace-redesign-20260927.md)
- [快速议事候选合入评估（2026-09-27）](/home/isp/wsps/cyf/specs/juyiting-creative-delivery-mvp/fast-deliberation-merge-assessment-20260927.md)
- [通讯协作合同](/home/isp/wsps/cyf/specs/juyiting-task-collaboration/connectivity-detailed-design-20260922.md)
- [角色隔离规格](/home/isp/wsps/cyf/specs/single-tenant-role-isolation/spec.md)
- [能力治理设计](/home/isp/wsps/cyf/specs/juyiting-agent-model-governance/design.md)
- [独立 Runtime v1 范围](/home/isp/wsps/chcbz/isp-install/conf/cyf-agent-runtime-v1/README.md)
- [运行台账](/home/isp/wsps/cyf/docs/implementation/TASKS.yaml)

以上共享工作区历史文档可能尚未提交到根 develop；它们只用于说明发现过程，不作为交接包必需文件。D2 §18 已内含实施所需约束；新实施以 M0 精确源码核对为准，不提交其他任务未发布的文档。
