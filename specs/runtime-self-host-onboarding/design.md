# Runtime接入与租约分离：最小详设

## 0. 状态与继任关系

2026-11-13再次审视后的收缩设计。**本次范围的设计依据核查已收口；目标设计不等于实现/上线。审查轮未启动开发；2026-11-13后续用户已授权开发，按完整候选测试后统一部署，不分片上线。** 取代上一稿的单通道批投递、hostGeneration/connect、targetGeneration/五态、专用轮换HTTP及四表整体重构要求。旧稿原字节已快照，当前正文不保留两套竞争目标。

公共协议沿API统一接口规范；[规范](spec.md)约束业务，[审查](review.md)记录事实/取舍/未核项，[任务](tasks.md)限定代码范围。

## 1. 复用结构，不另造调度系统

```text
原用户邀请入口 → 原HostingSetupService/HostingRentApplicationService
               → 原报价/reserve/installation/reconciler/capture
               → 精确Agent授权和原命令日志

同一个RuntimeHost（原独占锁）
  └─ 原HostingOutboundHost管理器
       ├─ 定期读取本机授权目录（主机凭据认证）
       ├─ Agent A原HostingOutbound异步worker → 原HostingControl
       └─ Agent B原HostingOutbound异步worker → 原HostingControl
```

现有worker就是同进程异步循环，使用同一个HostingControl/RuntimeHost；不新建系统服务或引擎。已有`withSubject`/`withAgent`保证同Agent操作串行。不同Agent原worker隔离保留，不把全主机排成一条等待队列，不再新增4槽/16批/公平性调度。

代价明确：请求数随活跃授权增加，沿现有pollIntervalMs配置。当前未测出必须用批协议解决的瓶颈，不以假想大规模负载提前建设。若后来有实测瓶颈再独立评估，不宣称当前方案无限扩展。

## 2. 主机身份：只补启动空宿主所缺的能力

### 2.1 凭据与归属

本机生成hostId及一个32字节随机秘密，沿现有`rth1_`格式；API只存完整令牌的SHA-256。私有文件及stateRoot沿现有安全写入/权限/独占锁能力。secret不进浏览器、URL、日志或Agent沙箱。

自部署用户经JWT登记hostId/tokenSha256；tenant/client/owner由可信边界确定。保留现有部署值`server/local`，不为了“命名统一”改为managed再联动所有消费者。server主机由受控运维登记，普通用户不能选择server伪造主机资格。

本机必须导入并确认API给出的hostId/mode/tenantId/clientId/ownerJiacn/tokenSha256公开元数据；hash应匹配本地secret，API origin来自可信配置。未确认归属不启动目录发现或执行。server主机owner=null，local主机固定owner；mode/归属不可由命令重写。

管理凭据只认证本机管理请求；每Agent命令仍须匹配当前授权及原业务关系。API不是“拿到host token即可控制任意Agent”。

### 2.2 不新增connect/连接世代

每次HTTPS请求独立核验主机凭据和Agent授权即可。`runtimeInstanceId`沿现有字段只作进程诊断，不增加expectedHostGeneration、connect握手、抢占、fencing、恢复世代或在线TTL。

同一受管stateRoot已有`acquireRuntimeOwnership`：锁占用拒绝第二writer；停止未确认不释放锁；崩溃遗留锁沿既有受控修复。不同目录/跨机复制不受本地锁保护，不能把此局限隐藏，但也不为本期不支持的克隆部署设计高可用协议。

### 2.3 密钥替换与撤销

保留受控维护入口以处理泄露/遗失：核对host和归属、撤旧hash/装新hash、重新启动或重载原连接。无需连接世代、双密钥宽限或新增用户rotate/revoke后台。本期不承诺无中断轮换；短时管理离线不停止续费。撤销主机管理凭据不等于解绑所有Agent，原Agent执行授权撤销仍走既有责任层。

## 3. Agent授权：沿用现有setup/关系，不新增目标状态机

- 邀请沿现有setupId；它是此次邀请的授权关联，不是主机凭据。无需新targetId及targetGeneration。
- 预准备仅允许capabilities/target/inventory；原reserve事务提交后允许原安装动作。权限以API已提交的绑定/租约/意图关系为依据，不靠本机把SETUP改名CONTROL自行扩权。
- 删除两份token及SETUP发现第二CONTROL secret的逻辑。一个邀请使用一份稳定授权元数据和一个原worker；付款前后只改变API允许的方法，不重建worker身份或另发管理秘密。
- 本机固定host/tenant/client/owner/canonicalAgent身份，复用原生命周期journal。API对付款状态负责；Runtime不复制钱包状态机。
- 安装/provisionGeneration/sessionGeneration、manifest及原intent校验保留。这些是已有执行合同，不是本轮新增“连接世代”。
- 原“准备中/可报价”展示从实际目标/库存结果计算；“已付费/待就绪/收尾”由现有意图与租约给出。不再持久化PREPARING/AVAILABLE/ASSIGNED/FINISHING/CLOSED第二套target状态。
- 前安装安全退款重试：先确认原窄退款条件，关闭旧授权，创建新授权ID和新报价/意图，保留同owner合法绑定解析；不增加授权版本计数。已有或未知安装不走此捷径。自部署正式解绑后新邀请不接管旧私有状态。

## 4. HTTP最小变化

沿公共Q/R/M及真实HTTP状态码，现有`E0`成功码不变。原long ID/金额/时间字段保持既有wire格式，不顺手改名。命令data继续使用既有hosting.* fixture。当前样本见[报文](host-control-v1.json)；它是目标样本，不是已通过联调记录。

### 4.1 用户与运维

| 入口 | 最小差异 |
|---|---|
| 新POST `/agent/hosting-hosts` | JWT；Q.data=`{hostId,tokenSha256}`，只登记local；原幂等头。R.data返回上述公开主机归属元数据；不返回secret |
| 新GET `/agent/hosting-hosts` | 只列当前owner已登记local主机供选择；cursor/pageSize及items/nextCursor/hasMore同下节，按hostId升序；不做主机监控/运维面板 |
| 原POST `/agent/personas/{personaCode}/hosting-setups` | Q.data=`{mode,hostId}`；local必须指定已登记本人的host；server的hostId=null，由原配置自动选择；不收tokenSha256/controlTokenSha256 |
| 原setup查询/取消 | 沿原setupId；查询不排新命令；取消已付费关系必须走原正式解绑，不绕过资金 |
| 原报价/绑定确认/租约查询/续费/解绑 | 保留现有路径/主体字段；quote的setupId保留，真实目标库存及原reserve原子关联不变 |
| 主机登记/换密钥/撤销维护 | 沿既有受控维护入口，不新增用户connect/rotate/revoke接口或动态路由后台 |

托管用户在原界面操作，Web自动调用准备/查询，不要求主机配对材料。自部署只首次主机登记有材料确认；之后邀请只选已有host。

主机登记复用原Idempotency-Key/请求摘要规则：同键同请求返回原元数据，同键不同请求409；已有同host的同归属同hash通过原键POST重放或GET重查；不能用新键POST成功冒充已记录别名键，不能通过重新登记替换归属/密钥。普通用户不可登记server或选择其他owner；失败沿现有HOSTING_OUTBOUND_REJECTED/CONFLICT等错误责任层返回，不复制新错误框架。主机hash失效或被撤销的已成形原生凭据返回401；授权不属于本host/已撤销返回403；非法字段/报文沿原边界错误，不向其他主体泄露归属。401停止主机管理循环，403只隔离该授权；业务session和收费不因此停止。

### 4.2 Runtime发现目录

新增只读GET `/agent/runtime/v1/hosting/authorizations`，`Authorization: RuntimeHosting <主机token>`。不接受任意host/owner过滤扩大范围；host由凭据确定，环境tenant固定。

R.data包含`host`（已固定的公开归属）、`items`（本机有效授权）、`nextCursor`、`hasMore`。最后两者沿统一接口规范§6，不另创分页信封。每项沿既有字段`authorizationId,hostId,tenantId,clientId,ownerJiacn,canonicalAgentId`，不含secret/资金详情。现有安全过滤器仅放行无query的exchange POST，必须为此目录GET单独增加精确method/path白名单，只允许cursor/pageSize各出现一次，GET无body；exchange仍拒绝query，其他原生身份边界不放宽。采用授权ID升序keyset分页，pageSize为1至100的整数，缺省100；此为接口返回批次合同，不宣称经过容量压测。cursor为上一页最后授权ID，首次省略；主机范围必须在排序/LIMIT前限定。ID为已有最大100字符格式；hasMore=true时nextCursor必须为本页最后ID；末页nextCursor=null、hasMore=false；用同一查询范围探测下一条确定是否还有页，不伪造total。page成功不表示全部目录已读取。

由现有宿主refresh机制读取，新增授权热加原worker；每次读取只获取元数据，无安装或资金副作用。不把某页没出现的授权当作已撤销；删除以API明确撤销结果或完整成功目录刷新为准。分页期间新增项下次刷新发现，已撤销项在exchange边界立即拒绝，不依赖目录缓存及时更新。

### 4.3 原单项exchange继续使用

保留POST `/agent/runtime/v1/hosting/exchanges`及Q.data：
`{authorizationId,hostId,runtimeInstanceId,result:M|null}`。

R.data：`{authorizationId,hostId,acknowledgedMessageId:string|null,command:M|null}`。删除`controlAuthorization`父子发现；其余保持现有单命令/单结果语义。主机token证明host，authorizationId决定具体Agent；API核对授权所属host、scope、状态与精确业务方法。没有capacity、commands[]、results[]、targetGeneration或hostGeneration。

每worker保留原命令落盘→既有控制执行→结果落盘→重发同结果直到ACK。结果ID不能用来完成其他命令；ACK只是持久化收到，不代表SERVICE_READY或扣费。401主机凭据错误暂停相关管理循环；单Agent授权撤销只停止该worker，保留本机日志及其他Agent。

同授权元数据中host/owner/Agent身份不得原位替换；允许API付款阶段变化但不把它放入worker不可变身份指纹。Runtime不能只因重新读取目录就重放未知/永久失败操作。

## 5. 持久化只改承担真实职责的位置

保留现有五个职责：Agent授权、setup登记、setup_quote、已付款关系映射、exchange命令/结果。**不预设合为四表，不为表数重写所有Mapper。** 主机凭据需要独立的host记录，因为空主机无Agent、同主机凭据不能随单次邀请撤销；这是本期确实新增的身份职责。

在现有outbound维护DDL中新增host存储：scope、hostId、mode、owner（server为null）、tokenHash、启用/撤销事实、登记幂等键/请求hash、创建时间。唯一host身份和token hash；类型沿现有范围。无hostGeneration、runtimeInstance认证字段、route或目标调度时间列。现有授权记录引用host，不再持有每Agenttoken hash；setup去除controlTokenHash。

原setup→已付款关系映射可保留，它记录业务关系是合理的；问题在于过去用它决定“有没有主机凭据和通道”，不是“一次邀请对应一份租约”本身。存量控制关系导入用原真实身份及租约建立映射，不伪造已付款邀请/历史扣款；维护导入与新邀请走不同明确入口，不能伪造setup历史来凑字段。已核对现有activation以(scope,setup_id)为主键并强制FK到setup，不能直接导入无setup的存量。目标调整为(scope,authorization_id)主键，setup_id可空且保留(scope,setup_id)唯一约束和原FK，保留lease唯一约束及authorization FK。新邀请setup_id非空；真实存量映射setup_id为空，由授权主体、原binding/lease/installation核验，不伪造setup或quote。撤权路径按授权及真实关系查验，不再无条件解引用setup。此处是目标结构，未执行DDL；生产执行范围仍以实际目录为准。

保留PK/UK/FK、NOT NULL、事务、环境分区与原幂等；不新增CHECK、触发器、启动DDL。旧字段/表的生产删除只在固定真实目录盘点后授权执行。未发布候选源码退役与生产DDL不是同一件事。

## 6. 资金、命令幂等与事务

### 必须修复的实际缺陷

1. 目前`HostingOutboundProvisioning.exchange`除prepare外，读到完成结果会新排一条同义操作。改成读取无副作用；mutating方法按原业务operationId重放，新增观察仅由原协调器明确发起。不要增加新的reconciler或自动轮询财务状态机。
2. 原setup启用后全局接管quote，且拒绝所有已有binding，会破坏托管及安全退款重请；改为精确路径解析，不以bean存在代替路由/资格判断。
3. 原setup Controller不允许controlTokenSha256而Service必填。新目标是删除双secret契约，三端真实HTTP fixture同改；不先给即将退役的第二token单独补洞。

### 不变的资金责任

- 实际库存及quote冻结仍在原责任层；未知不能填零，停用但仍安装的技能照原合同计算。
- 仍沿已有确认时库存核对，不发明第三轮预检或新的quote付款入口；确认后的prepare仍核对原摘要，变化按原无副作用失败/重新报价处理。
- 原reserve与业务绑定/授权激活须同事务；installation、manifest、注册session和SERVICE_READY成立后原capture一次。
- 退款仍限INITIAL、FAILED_NO_EFFECT、未capture、未serviceReady、无installation/manifest及原执行generation=0。断网/超时不能扩大退款条件。
- 原续费与TRANSITION维护只操作API数据库，不读取主机在线/清理状态。
- 已核实退款协调器仅撤旧managed key，没有撤outbound授权。必须在原退款事务内，完成原ledger/credential步骤后撤销精确旧授权，失败整体回滚；安全重请使用新授权ID，不扩大退款条件。

### 已核实的事务调用链与接入边界

以下为静态调用核查，不是并发测试通过：

| 入口 | 原调用/加锁顺序 |
|---|---|
| 首次确认 | quote/原intent→persona/binding→ledger.reserve→绑定/身份/投影→授权激活 |
| reserve内部 | quote→原intent/live lease→资金账户准备→W02→lease/intent写入 |
| W02 | 幂等事务→funding→既有排序账户锁→escrow→记账，不回调控制服务 |
| capture/refund | binding→intent→lease→原ledger/W02；退款末端撤key及精确旧授权 |
| 安装 | ensureInstallation先锁真实installation，再binding→intent→lease；不换成普通create |
| 解绑 | installation→binding→原intent/lease→投影；末端撤精确授权，不锁整机来做资金 |
| TRANSITION | installation→binding→投影→原intent/lease/live slot→固定首期及原调度；无网络 |
| 自动续费 | 分区内due lease排序/锁定→原钱包→原调度；不查host/grant/心跳 |
| 控制exchange | 认证host→单授权→原命令/结果；不反向调用资金/安装业务 |

host认证与撤密钥保持事务一致，使用短事务共享读锁，单授权沿原排他锁；不在每次poll更新host行造成锁升级。撤主机凭据只更新host，不持该锁进入资金业务。业务入口在原锁根之后关联/撤授权，不能反向获取控制锁再执行reserve/refund。保留原账户排序和幂等锁，不新增锁框架。现有调用顺序不同不等于已证明无死锁；实际跨入口并发及回滚须在实现后按验收执行。

worker不可变身份仅包括原host/scope/owner/Agent/authorizationId。当前构造器及持久身份依赖purpose、宿主指纹包含token，必须一起调整；付款SETUP→CONTROL不重建worker身份，共享主机token不进入Agent身份指纹或沙箱。去掉acceptControl父子发现，但保留UNKNOWN隔离及原结果/ACK核验；重新读目录不能自动解除执行隔离。新目录fixture不能宣称直接兼容未修改的消费者。

本机授权校验复用HostingControl，但可信主体只能由已认证目录/worker以内部上下文传入，不能从命令data接受任意scope覆盖。UDS旧入口不获得这个上下文，仍走原配置权限。启动/恢复时先读取已确认主机的授权目录，再允许相关worker执行；旧journal的结构/摘要校验与当前执行授权分离，撤权后保留日志，不因授权消失删除状态或自动重放。目录不可用时不执行未授权管理命令，原业务Agent按其安装/session运行，不因管理暂不可用停租。

### 存量RETAINED与续费启用（实际核查缺口，不是新增收费规则）

沿文钱包§7.3：RETAINED只是原归档权益，并非零文付款，不把它猜成PAID/TRANSITION。此次发现两条已过期旧权益会进入按用户的自动续费扫描并报DATA_CORRUPT。

- 在既有EconomyHostingRenewalMapper的duePageForUpdate与nextDeadline按真实latest_intent关联排除明确RETAINED，仍先scope/user后排序LIMIT；不以amount_wen>0过滤掩盖损坏的正常付费租约，不依赖Runtime在线、也不跨域连接Agent绑定表。
- 单条reconcile入口使用已有selectIntent读取该lease的确切latest intent；明确RETAINED不产生自动扣款/自动延期，原期限/历史原样保留，返回原状态；新PAID报价续期沿已有合同。缺失/未知来源拒绝，不当作RETAINED跳过。保留lease锁根，不新增intent FOR UPDATE倒置锁序。
- 正常PAID/TRANSITION仍按既有30天金额、余额、幂等和欠费规则执行。历史RETAINED通过原显式PAID续期转成真实付费来源后，正常进入自动续费；不为旧记录伪造quote、付款或安装。
- 这是原经济续费责任层的小范围接线修正，不另建调度器，不清除旧权益/资金记录，也不修改正常租期。
- 上线必须先验证该混合历史场景，再受控设置auto-renew-enabled=true并确认处理器注册/待办；不只看配置文件。当前开关未设置，本次不启用、不触发余额事件或续费调用。

## 7. 隔离、路由与迁移不扩建

### 控制路由选择规则

1. 有当前setupId时以其精确授权/host为准；已安装Agent以原scope/Agent→授权/安装关系解析host，不从调用者URL或全局bean推断。
2. 存在经业务事务激活的出站关系就只用该出站授权；暂未导入出站关系的存量只走已配置且归属匹配的旧host适配器。出站超时/撤权/UNKNOWN绝不回退旧通道；同一关系不得同时向两条通道提交新命令。
3. 新托管准备复用原localHostId对应且被managedHosts允许的已登记主机；无该默认项时仅允许唯一匹配候选，零个返回未配置、多个返回明确配置冲突。不引入按负载分配/自动扩容。自行部署只选择本人登记host，不每次新增运维路由。
4. 旧关系导入前停止该关系的新生命周期命令，核对API意图与原journal后导入授权；旧journal/安装/operationId保持原字节，切换仅改变命令投递。已发现RECOVERY_REQUIRED的公孙胜关系保持隔离，不能从新目录自动重新执行；其他Agent不被整机阻塞。
5. 状态字段/返回业务事实不同不能靠重新adopt“修正”；李逵current= CURRENT但observe=UNKNOWN按原实际含义处理，不为迁移伪造ready。Eva补租约不要求先补管理通道。

### 原有隔离及受控安装

复用`IsolatedEngineProfileRuntime`及原native profile；验证新Agent真实启动进入已有沙箱。共享主机secret放在Agent不可见位置；目录分开并不等于跨用户隔离已验收。不新增容器平台、UID管理框架或第二套安全上下文。

沿现有主机/适配器配置明确选择旧控制路径或出站。不得因outbound bean存在就接管所有托管，也不得失败自动转旧路由。切换前停止该范围的新生命周期入队并核对旧未知请求；未知不双发。采用受控配置切换，不新建host.route数据库和动态路由系统。当前盘点确认：平台host走本地UDS，李逵host走原mTLS，Eva未配置管理路径；本轮不改这些配置。

扈三娘补登记与通道安装分开，李逵记录不得覆盖。租约无需假造控制setup，旧安装不重新enroll。当前库没有候选出站表，应按新增schema处理；不输出DROP旧表指令，不对未知环境自动迁移。

## 8. 范围约束

尚未关闭的源代码/存量事实由本专题明确记录，不借此扩大为重写全项目。新的公共框架、额外状态计数、审批系统或后台均不在本期。发现不能复用的真实位置先给出证据及最小差异，不以“长期可扩展”作新增系统理由。


---
## 历史材料（非本次目标合同，不据此重跑或认定通过）




任务 SELFHOST-ONBOARDING-20261012；Main 集成 Owner。源码基线：API cd1e6d6ebe714767273c440abc5edd925c2333e3，Web 235048e6820afd24f21c6ca78b4b4c30901508b7，isp-install 807b86d66153b765529bba1d547e4bcfbf0a3706；三者本地/远端 develop 已核对一致，组件工作区干净。根仓其他改动不触碰。

## 历史交接契约（原2026-10-12候选；新邀请以现行设计为准）
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
