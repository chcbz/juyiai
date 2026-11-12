# 典籍职位技能合入 develop：主流程影响分析

核对时间：2026-10-24T09:30:17.343821+08:00（Asia/Shanghai）。范围：Root/API/Web/Runtime 四仓。本次用户授权为“分析是否影响主流程，不影响才合入 develop”。

## 结论

**不满足无主流程影响的合入条件，本次不合入 develop。** 已只读刷新并二次核对四仓远端 develop；未执行 merge、reset、force-push、改流水线、生产迁移、部署或重启。不能把此前旧冻结基线上的113/100/161项诊断，直接作为最新 develop 整合后的回归结果。

原因不是典籍读写业务本身，而是本候选依赖的共享技能安装/资格/运行时生命周期已落后于最新 develop 的 SM-C1。旧实现和新主链不能机械择一，必须先做统一适配。

## 精确输入

| 仓库 | 本轮候选 | 本次远端develop |
|---|---|---|
| Root | `2f63f616a659c97707bef504df86d75fd5a35f49` | `d2d8e02102ae28c894d2b28ac94c9419ae7271a4` |
| API | `4520d81971bbe9b093a89f2ecba4964adb18d1c1` | `cf6b8714201326bb571731d0e00797165bd154b8` |
| Web | `45a217baf80c28b0c33b4da1a85f491323d1c1e0` | `8c84e51b3b60d101a4ea1e929e28f77d77bbdbda` |
| Runtime | `bade440cccbf835859d790ed05f5f6cdab02ede2` | `90f24090be110293011e1d3aef6dbc733ca440d9` |

Root/Web的Git三方合并预演无文本冲突；API有4处、Runtime有4处文本冲突，均未写入checkout或移动分支。文件路径及树对象保留于 `verification-mainflow-20261024/*-merge-tree.log`。文本无冲突不等于语义或测试通过。

## 阻断性发现

### P1：共享安装器命令协议互斥，不能覆盖最新主链

- 特性分支 `conf/codex-ws-agent/skill-install-manager.mjs` 的 `validateSkillInstallCommand` 接收旧平面命令（增加了 SKILL_GRANT_INSTALL）。
- 最新develop同名安装器只接受经过 `parseManagementMessage` 校验的当前SM-C1信封，命令持久接收、PREPARE/ACTIVATE/POLICY与结果回执属于同一journal状态机。
- 实际库探针：develop标准管理命令通过develop解析器，却被本分支安装器拒绝；本分支合法职位命令则被develop解析器拒绝，观察到 `PROTOCOL_INVALID_MESSAGE`。
- 因此不能用“保留本分支安装器”消除文本冲突：这会丢失当前技能管理命令主路径。也不能假称新旧两套格式已经适配。

### P1：保留develop安装器时，职位技能收敛会调用不存在的接口

- `position-skill-reconciler.mjs` 仍调用 `manager.removeGranted(...)`，然后执行旧格式 `manager.execute(row)`，并按旧工作结果构造安装回执。
- develop的SkillInstallManager没有removeGranted；execute要求当前管理信封与已持久接收的命令，旧职位row并不能直接传入。
- 用真实develop类prototype和真实特性Reconciler运行纯接口探针，首次职位期望即抛出 `TypeError: this.manager.removeGranted is not a function`；没有真实安装或后端调用。
- 不能只解决Git冲突后宣称任职/回收可用；需保留共享安装器的一套授权、测量与持久结果语义。

### P1：旧安装描述格式无法进入当前测量/就绪链

- develop的SkillRegistry要求skillInstallationId、productVersionId、kind、policyRevision、enabled等当前管理事实；本分支安装器仍返回旧描述格式。
- 使用当前SkillRegistry与真实manifest解析器运行输入形状控制：旧形状被拒绝为 `SKILL_INSTALL_SOURCE_INVALID`；补齐当前形状的对照输入可测量为READY。
- 这是纯形状兼容性证据，不是一次真实Runtime启动。它证明保留旧安装器、配上develop当前registry并不等于安全合并；共享技能目录/就绪能力会不匹配，涉及当前执行主链。

### 必须保留的后端主链语义

API的InstalledSkillDescriptorService、InstalledSkillEntitlementLookup与两个build.gradle存在冲突。develop已增加管理授权来源过滤和management.qualifies校验，后者要求当前active installation、desiredEnabled、admissionEnabled及真实READY。合入时必须同时保留这些能力和职位授予来源，不能以旧ACTIVE entitlement替代新停用/策略资格。此项为源码审查发现的合并要求，未伪装成已复现的越权或已运行的整合后数据库测试。

## 其余主流程边界

- 新职位服务由agent.position-skills.enabled显式启用；本候选不修改应用默认开关、不执行启动DDL。不能仅凭这点忽略共享安装器的集成冲突。
- 新Runtime适配在已确认native通道后，先resume原执行，再异步收敛；源码上不是把典籍处理放在注册/ACK前。但最终整合后仍须验证恢复、离线和报错不阻塞原任务。
- 新native端点没有改为OAuth/API-key fallback；原OAuth管理与native执行身份分离要求继续保留。新增method/path白名单不能代替完整主链回归。
- Web变更主要在典籍阁页签和reader历史版本；本次与最新develop预演无文本冲突。未因后端已确定阻断而虚构全前端或新整合候选Flow成功。
- 本次没有实际应用合并树、没有运行Gradle、没有触发Flow；不存在本次整合后的业务通过结论。先前正式Flow/完整Runtime浏览器/独立复核缺口也不因本报告关闭。

## 已执行验证及证据

目录：`specs/archive-agent-maintenance/verification-mainflow-20261024/`。

1. source-pairs.json / remote-develop-check.json：四仓fetch后的精确commit/tree及结束前远端再核验。
2. 四个merge-tree日志：无checkout修改的三方合并预演；API/Runtime冲突定位。
3. compatibility-result.json：5个纯库控制/预期负例，确认不兼容，**不是五项业务验收通过**。
4. code-locations.json / probe-manifest.json：真实源码行号、文件摘要、诊断入口和Node版本；原诊断脚本保留于本任务diagnostics，不含生产凭据。

## 后续适配范围

1. 基于最新develop统一技能生命周期：POSITION/GENERAL作为授权来源维度，不另起旧安装协议；复用当前SM-C1持久接收、安装/策略应用、policyRevision、测量与回执。
2. 明确非商城职位授予如何进入当前管理授权/包引用，继续禁止虚构市场订单；共享POSITION最后来源回收、GENERAL保留合法资格需在同一模型下验证。
3. 手动整合资格查询并保留禁用、历史任务冻结安装和新任务准入语义；补真实安装/撤任/重连与现有付费技能升级/启停回归。
4. 通过准确整合候选的定向诊断、主链回归与正式Flow后，再按用户当前授权判断合入develop。未完成适配前，不拆出单独Web提前合入，避免跨仓功能对不齐。

本报告只作本次条件合并决策：**当前拒绝合入，develop及线上均未改动。** 没有修改旧D2 84项或本轮A01–A12为PASS。
