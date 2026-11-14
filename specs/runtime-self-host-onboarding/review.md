# 2026-11-13全方案最小必要性复审

## 结论

**上一版纠正双凭据问题时，又引入了过度设计。现明确撤回，不继续叠加修复。** 一台机器一个Runtime不等于一个HTTP轮询；每Agent的进程内异步worker也不等于多个Runtime。没有实测瓶颈，不能先把它们合成批队列，再为此增加容量、公平性、世代和状态机。

本轮确定最小方向：保留已有单主服务/独占锁、按Agent异步worker、生命周期journal、安装会话、沙箱和原资金体系；只分离主机凭据与单次Agent邀请，让托管自动取得授权、纠正实际入口和幂等问题。

## 逐项裁决

| 项目 | 决定 | 原因 |
|---|---|---|
| hostGeneration、connect、CAS抢占/恢复 | 删除本轮新增设计 | 现有单writer已覆盖同状态根正常启停；用户未要求双主/克隆接管 |
| targetGeneration | 删除新增设计 | 新邀请用新授权ID，保留原安装/意图/执行世代即可；不再叠加一套计数 |
| 每主机只能一个poll | 撤回限制 | 不是用户要求，强制归并才引出额外调度问题 |
| 16条批命令/结果、capacity、4执行槽、公平轮转 | 删除 | 复用既有独立worker与单项回执，没有实测理由整体换协议 |
| 每Agent异步worker | 保留复用 | 已在同一主进程，隔离慢/失败Agent，无需新调度器 |
| SETUP/CONTROL双秘密及父子发现 | 删除 | 不应每次邀请重新配主机密钥；API授予业务权限，不用第二token表示付款 |
| 每主机一份管理凭据 | 保留 | 空主机需要认证接入，多Agent共用同一宿主；不能随单次解绑撤整机凭据 |
| 只读本机Agent授权目录 | 最小新增 | 否则托管/新Agent仍需手改本机配置；复用现有refresh/worker管理器 |
| target五态、targetId新路由/全面更名 | 删除 | 复用setupId、原安装/租约/收尾状态和实际库存结果；不造平行权威 |
| managed替换现有server wire值 | 删除 | 无业务收益、徒增三端变更 |
| 强制五表合四表、Mapper/Service全面改名 | 撤回 | 表数和类名不构成业务问题；只改真实身份和字段职责 |
| 主机rotate/revoke公共后台、动态route数据库 | 不新增 | 密钥维护/路由切换走已有受控运维，不建立主机管理平台 |
| 精确授权、持久ACK、稳定operationId、原事务 | 保留 | 分别防越权、回执丢失、重复副作用和资金不一致 |
| 新财务调度、钱包、容器/隔离平台 | 不做 | 原机制已经存在；只检查实际接线 |

## 本轮直接核查的源码

以下是静态事实，不冒充运行或并发验证：

- `/home/isp/wsps/cyf/runtime/conf/cyf-agent-runtime-v1/lib/runtime-host.mjs`的`acquireRuntimeOwnership`通过原子mkdir取得`.runtime-writer.lock`；第二writer返回RUNTIME_WRITER_BUSY，释放校验原目录/owner事实。锁范围是同一受管root，不是全机器/跨机。
- 同文件已有`withAgent`；`/home/isp/wsps/cyf/runtime/conf/cyf-agent-runtime-v1/lib/hosting-control.mjs`已有`withSubject`及持久操作记录。正常Agent串行与生命周期幂等不需要重建。
- `/home/isp/wsps/cyf/runtime/conf/cyf-agent-runtime-v1/lib/hosting-outbound-host.mjs`的workers是同一RuntimeHost/HostingControl下的Promise/AbortController，支持独立启动/停止；不是新系统进程。
- `/home/isp/wsps/cyf/runtime/conf/cyf-agent-runtime-v1/lib/hosting-outbound.mjs`已有单命令落盘、原结果重放和ACK验证；新批协议不是补齐这些能力所必需。
- `/root/.codex/worktrees/runtime-lease-setup/api/agent/jia-agent-service/src/main/java/cn/jia/agent/hosting/HostingSetupService.java`使用server/local模式，原稿改managed没有必要。
- 同目录`HostingOutboundProvisioning.java`仍存在“完成后读取多数method再次入队”；`HostingRentApplicationService.java`仍有新setup全局接管及已有binding拒绝；`../api/AgentHostingRentController.java`仍有第二hash入口不一致。它们是要修的具体问题，不因设计精简消失。
- 原托管手工JSON UI、授权作用域及存量映射问题仍保留审查结论；需要改正确责任层，不重写原正常托管流程。

## 继续核实结果（2026-11-13）

### 源码已闭合的具体缺口

1. 原生凭据过滤器只放行无query的exchange POST。目录GET必须增加cursor/pageSize的精确例外并补齐公共分页hasMore，不能以permitAll或整体放开query处理。
2. activation原主键/FK强制setup历史。目标改成授权主键、可空setup及保留唯一/FK；存量导入不伪造邀请。撤权也必须移除必需setup的假设。
3. 原退款仅撤managed key，未撤出站授权。补在原窄条件退款事务末端，不新建退款流程。
4. 原Runtime构造器/持久身份和宿主指纹依赖purpose/token，去双凭据必须同步这些真实消费者；不是仅删JSON字段。
5. reserve、W02、退款、安装、解绑、TRANSITION及续费已逐链静态核对，详见design事务表。未运行并发测试，不宣称全链无死锁。

### 已闭合的生产事实（本次核查范围）

范围是本机现行生产API及其jia库、本机平台托管Runtime、Eva扈三娘，以及API配置中的李逵旧TLS控制端点。不是所有未知环境的兼容承诺。未发布候选代码与当前部署分开记录。

1. **数据源已对应。** 当前API PID 3787147、prod profile，包内数据源为127.0.0.1:3306/jia；外部文件、CLI和环境未发现数据源/config import覆盖，进程有到本机3306的真实连接。本机socket查询对应此MySQL，数据库会话时区+08:00。旧PID消失后已重新固定新PID，不复用旧进程事实。
2. **扈三娘未补登记。** Eva profile的Agent ID匹配scope 0绑定；有效binding/installation但无lease。另一个scope的同名Agent不是本次对象。补登记须沿原TRANSITION维护入口，明确self-hosted套餐和执行时固定cutover，不预占、不enroll、不追扣过去。
3. **李逵租约和调度已存在。** ACTIVE、agent-self-hosted、50文/2592000秒；北京时间2026-11-11 22:02:03.301至2026-12-11 22:02:03.301。对应reconcile-user待办due与到期一致、未被领取；付款人WEN可用钱包ACTIVE、采样余额3486。owner与payer文本不同已用User精确关系和HostingRentOwnerResolver核对，是既有身份映射，不擅自统一改写。
4. **自动续费尚未启用。** 已部署包的RenewalHandler/LeaseWakeup/BalanceWakeup有auto-renew-enabled=true条件；当前prod包、外部配置、CLI/环境均未设置该开关。不能用已有待办证明处理器正在运行；不在本轮打开开关或触发费用。
5. **启用前还有真实存量边界。** 同一付款人有两条ACTIVE、amount_wen=0的RETAINED旧权益，对应binding已SUSPENDED、期限已过。现duePage/nextDeadline未区分RETAINED，reconcileLocked却把非正金额视为DATA_CORRUPT，会阻断同用户正常续费。原文钱包§7.3已定义RETAINED为归档保留权益、并非0文付费，不能改金额或伪造新付款。最小责任修正见design；不能直接打开全局开关后再修。
6. **502原因已定位到API启动窗口。** 网关记录session POST返回502；当前API09:37:08开始启动，09:43:51监听10018，09:43:54启动完成；session在09:44:12/09:44:17恢复200。Eva随后connected/registered/ready=true，多次采样presence ACK继续前进。旧lastFailure仍保留502，不能把历史错误字段当成仍断线。以上证明此窗口的API业务连接恢复，不冒充新管理控制链已安装；不推定是谁发起重启。
7. **现行路由确定。** 平台主机通过本地UDS；李逵通过既有mTLS端点；Eva没有管理控制配置/出站配置，仅有原业务连接。李逵TLS只读current/observe通过现有证书及真实M校验：CURRENT、INITIAL、generation=1，observe=UNKNOWN；不把CURRENT或业务在线当成生命周期SERVICE_READY，也未发送ensure/adopt/cleanup。
8. **旧操作没有被忽略。** 本机控制journal有4个subject、5条operation，其中公孙胜的一条REPROVISION标记recoveryRequired=true；数据库该原重整为SERVICE_READY，事实不一致不能自动重放或清空。李逵当前关系是原INITIAL，DB无其未完成重整。该受影响Agent在切换时保持隔离，保留原journal/operationId，不要求新建全机恢复框架。
9. **无已部署出站五表迁移。** 当前MySQL各schema未发现hosting_outbound表；本机/Eva配置未启用候选出站链。此处应按新增候选schema安装，而不是编造旧双凭据的线上数据迁移。对未盘点环境不授权删除/迁移；维护入口遇到未知旧结构/记录拒绝该次安装并保留事实。

### 核查收口与实施边界

本次范围内的设计依据核查已收口，发现的问题已有明确责任位置和处理规则，不再保留“开发时再选”的替代协议。详设固定：单主服务、原逐Agent worker/单项ACK、主机凭据+精确Agent授权、原租约/资金体系；不引入世代、批队列或新调度器。

**核查完成不等于功能完成或允许直接上线。** 后续实现及验收必须解决目录过滤器、存量关系FK、退款撤权、worker身份、明确路由，以及RETAINED续费发现边界；上线前还需实际候选测试、受控通道切换、开关/处理器回读和扈三娘补登记。未知原操作保留隔离，不通过删除日志消除阻断。不把其他环境、真实OS跨用户沙箱和未执行并发测试标为通过。

本轮未改功能代码、未修改生产配置/数据库、未收费、未重启或提交。已有完整源码/文档依据足以按详设实现；不能再以“长期方案”为由扩大系统。

## 风险和不支持范围

- 单主机密钥失窃影响该主机已授权Agent，因此必须不进入执行沙箱、具备受控撤销；不承诺单Agent级密钥泄露影响面。
- 一台机器故障影响其主服务，属于当前部署模型；不为此自动加高可用。
- 每Agent轮询有请求成本，沿现有配置；没有性能实测就不能宣称没有瓶颈，也不能预先造批调度框架。
- API撤权不能撤回已交付的本机操作；原幂等/关系核验保留。复制同一host秘密到另一机器不属于受支持正常流程。
- 离线照常续费、selfhost不清资产是已确认业务，不重新讨论或增加清理门槛。

## 输入和证据边界

API commit `9a92532658ace9b8cf23b31159f263b7e588bb3f` / tree `5f5a8906a3acdd51c7d3b71bfb222a43b14e18ff`；Runtime `b629d53b522fec27b816af869ce3dd0d6da385b6`；Web `113c6e69938387dd10439b30a1be22245f3544cc`。本轮包含源码、只读生产配置/数据库、既有TLS只读方法及健康采样核查，不重复或追认历史测试。

原设计/fixture/审查快照和SHA-256：`/home/isp/state/cyf-runtime-lease-separation-20261112/minimality-review-brm17irg/before-manifest.json`。既有历史handoff、测试原fixture和发布receipt未改。上轮没有生产查询；本次续核已执行上述只读SSH/数据库查询。没有应用构建、生产写入、迁移、收费、部署或提交；没有把任何未测项标为通过。

完整导航检查此前因缺少`docs/sdd-document-map.json`失败；该缺失不阻止阅读源码，但不能声称全量导航已验收。当前链接/JSON检查结果在本次快照目录单独记录，不能复用旧文档摘要冒充本版。

本次收口的原文快照、数据源/启动/网关事实、只读SQL与结果、脱敏控制结果及Eva连续采样：`/home/isp/state/cyf-runtime-lease-separation-20261112/closure-i55jr4ok`。不得将此目录的只读核查当作构建/发布receipt。
