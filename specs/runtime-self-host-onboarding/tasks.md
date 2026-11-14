# 最小变更范围

## 状态

**2026-11-13已获用户开发及完成后部署验证授权，当前开发中；不分片上线。** 本页替换上一稿扩张清单，不再要求批队列、世代、五态、四表重构或整批类更名。已核实事实和上线缺口见[审查](review.md)，不再把它们留给编码阶段决定。

## 保留，不重写

- 原经济quote/reserve/capture/refund/renewal和TRANSITION补登记。
- 原安装授权、manifest、provision/session generation及生命周期journal。
- 原Runtime主服务、独占锁、按Agent串行门、进程内worker管理器。
- 原codex-bridge隔离启动器及native profile；只检查新增Agent真实接线。
- 原setupId/用户报价确认路径、逐授权单命令/单结果/ACK形状。

## 需要修改的责任位置

以下绝对根下文件均为原实现位置，不要求新建同义实现：

### API：`/root/.codex/worktrees/runtime-lease-setup/api`

- `agent/jia-agent-service/src/main/java/cn/jia/agent/api/AgentHostingRentController.java`及现有hosting接口适配层：去setup双hash输入，托管host自动解析，主机首次登记/列表、主机认证授权目录。新增接口仅因真实新能力，不为了拆类建立一套后台。
- `agent/jia-agent-service/src/main/java/cn/jia/agent/api/HostingOutboundController.java`与`security/HostingOutboundCredentialFilter.java`、`config/HostingOutboundSecurityConfiguration.java`：host认证＋精确Agent授权；原单项exchange，不加connect/批协议。
- `agent/jia-agent-service/src/main/java/cn/jia/agent/hosting/HostingSetupService.java`：主机登记与邀请权限分离，去双secret/CONTROL发现；保持现有setup服务职责，不重复创建目标框架。
- 同目录`HostingRentApplicationService.java`：保留原收费事务，恢复托管自动准备及窄条件退款重请；不得按bean存在全局接管。
- 同目录`HostingOutboundExchangeService.java`：host所属授权核对、原ACK/撤权逻辑；只读授权目录不发命令。
- 同目录`HostingOutboundProvisioning.java`：稳定原业务操作ID、纯结果查询、显式观察刷新；去“完成后读即再排队”。
- 同目录`UnixManagedHostingProvisioner.java`及既有配置：按已核实主机配置明确选择控制适配器，无猜测fallback；不引入route数据库。
- 同目录`HostingRentReconciler.java`：在原窄条件退款事务末端撤销精确旧授权，失败整体回滚，不扩大退款资格。
- 同目录`HostingRentHandoverCompletion.java`：关闭精确旧Agent授权；保留selfhost API-only边界，托管原清理条件不动。
- `agent/jia-agent-mapper/src/main/java/cn/jia/agent/mapper/hosting/HostingSetupStore.java`、`HostingOutboundStore.java`及`resources/db/agent-hosting-outbound.sql`：独立host凭据、Agent授权去secret、必要关系索引/原操作幂等；不预定合表/全盘改名，FK/导入约束按design固定结构实施。
- `starter/src/main/java/cn/jia/maintenance/HostingRentCutover.java`等既有维护入口：原收费补登记保留；主机登记/撤销及关系导入各用明确维护动作，不混为重新邀请/付款。
- `economy/jia-economy-mapper/src/main/java/cn/jia/economy/mapper/EconomyHostingRenewalMapper.java`：duePageForUpdate/nextDeadline按原latest intent的RETAINED来源排除非自动收费历史；不能仅过滤金额。
- `economy/jia-economy-service/src/main/java/cn/jia/economy/service/impl/HostingRentRenewalServiceImpl.java`：单条入口用原selectIntent识别RETAINED，保留lease锁根，未知来源拒绝；正常付费/TRANSITION算法不重写。
- 本次真实变更的接口目录、必要校验理由和fixture同步，不扩为全API迁移。

### Runtime：`/home/isp/wsps/cyf/runtime`

- `conf/cyf-agent-runtime-v1/lib/hosting-outbound.mjs`：沿原worker/journal使用共享host凭据＋该Agent授权，不再生成/发现第二token；付款阶段变化不改变其不可变身份。
- `conf/cyf-agent-runtime-v1/lib/hosting-outbound-host.mjs`：复用refresh/reconcile/独立worker生命周期，从API本机授权目录发现，而不是人工维护每次邀请授权文件。
- `conf/cyf-agent-runtime-v1/lib/hosting-config.mjs`、`hosting-control.mjs`：主机凭据配置、可信Agent主体匹配；保留现有本机权限/生命周期，不复制API付款状态机。
- `conf/cyf-agent-runtime-v1/lib/runtime-host.mjs`：原则不改锁/进程结构，只在接线确需时改调用；禁止引入主机世代。
- `shell/cyf_runtime_hosting_setup.mjs`：每主机一次生成/确认材料；删除第二secret；不新增设备登录/自动签发系统。
- 既有安装/validate清单与指南按真实import闭包修改，不扩大为安装器重构。

### Web：`/home/isp/wsps/cyf/web`

- `src/components/juyiting/HostingRentPanel.vue`：托管无手工配对，自部署主机首次登记/选择；不增加主机管理后台。
- `src/composables/juyiting/useHostingRent.js`、`hostingRentContract.js`：原setup/quote/确认路径，去双hash；不改已有server/local命名。
- `prototypes/juyiting/interaction-completion.js`及`tests/hosting-rent.test.js`、`tests/hosting-rent-ui.test.js`同步真实界面合同。

## 测试范围

沿原HostingOutboundMySqlTest、Controller、ApplicationService、Reconciler、HandoverCompletion、Transition、ManagedHostingCredentials及Runtime hosting-outbound/host/config/control/setup-cli/java-bridge测试补必要差异。不能删安全/资金断言来让新设计通过。

必须覆盖：真实MVC字段→service→MySQL→Runtime；主机token不能越host/Agent授权；Agent慢/撤销不影响其他worker；无副作用退款重请；同结果重复无二次执行/扣费；托管不用JSON；实际沙箱隔离；离线续费和selfhost离线解绑；存量DB-only登记。

## 明确不列入开发

hostGeneration/connect、targetGeneration、新target生命周期、批commands/results、capacity、公平队列/4槽调度、主机route表、公开rotate/revoke界面、四表收缩、统一新错误码全量重命名、重写钱包/任务WS/沙箱。

本轮核查已收口，但仅执行核查/文档。后续实现严格按以上范围，不把本轮只读结果当应用测试；受控启用自动续费、通道切换和扈三娘补登记属于后续生产动作，不在本轮执行。后续新增文件应由具体职责缺口证明。


---
## 历史材料（非本次目标合同，不据此重跑或认定通过）



- API Owner：后端 local 文书改为 Runtime scope/指南，定向测试。
- Web Owner：移除旧 API Key 安装教程，导入安全登记材料及现有接口交接，定向诊断。
- Main：isp-install 准备工具/测试/完整说明/技能更新，跨仓契约核对与集成。
不设独立Reviewer；每位Owner只写所属组件，不覆盖无关改动。初轮源码交付不执行生产操作；2026-10-12续接用户“那就都更新”后由Main统一正式验证与版本化发布，子Agent仅交付制品、不自行安装。
