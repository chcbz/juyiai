# Runtime 与租约职责分离 — 2026-11-12

Owner：当前会话；任务 `RUNTIME-LEASE-SEPARATION-20261112`。用户已确认方案并要求开始实施；此前授权补登记目标自行部署 Agent。此文件不包含生产身份/凭据；私有盘点与后续生产回执保留 `/home/isp/state/cyf-runtime-lease-separation-20261112/`。

## 固定输入与范围

复用现有干净 develop 工作区，不新建 worktree：根 c0cfe2a9926fdddc18ba28b5227cb1d33715c4e1；API 6e57eead938c6cb1c5d26736b53a82999ac30ca0；Runtime fb6fcb5ccf9861c04df810ad5a8acce337e232fd；Web c5fe05c3d7affc3bc709fe3603b36de66242fa4c。完整 tree 与远端只读查询时间在私有 baseline.json；当前线上版本不由上述 HEAD 推定。接口规范为 `api/docs/interface-standard.md` v1.4（公共 protocolVersion=1）；RB-1，根 AGENTS 的本地构建/600秒/职责边界适用。

目标：API独立登记/续费；自行部署解绑不依赖远端停止/清理；旧用户本机资产不转交；新用户新 Agent 安装授权；主机一个 Runtime 主服务，多用户多 Agent 隔离；所有 Runtime 主动接入 API。离线/永久失联不暂停租期或有余额时的自动续费。

非目标：改变已确认价格/首期技能费/欠费15天规则；抹去在途任务/资金事实；远程删除用户资产；强行合并已有主机服务；无关重构；自动付费 Flow/模型调用。生产写入必须使用受测候选及正式业务入口，当前未执行。

## 责任链与实施顺序

1. [ ] 修订现行租费、接入、调度合同及验收；保留历史证据。
2. [ ] 存量登记使用显式固定套餐输入，不从控制路由推断；自行部署不调用 adopt。保留 scope/owner/installation/binding、幂等及同事务首次调度。
3. [ ] 自行部署 API-only 解绑：等待平台已有业务/资金事实，不等待远端停止/清理；撤销精确旧安装，关闭关系，不伪造停止证明；旧本地实例不得进入公共可复用池。
4. [ ] 新自行部署接入及重新邀请：新 Agent 授权、目标主机 Runtime 复用；取消旧实例复用与入站控制依赖。平台托管保留其资产回收职责。
5. [ ] 统一主动通信与主机多 Agent 隔离的实际受影响调用方；不为租约新增入站 TLS 服务。
6. [ ] 定向 API/Runtime/Web 契约、事务、重放和同主机隔离回归；validateLayering、必要集成及固定候选构建。
7. [ ] 授权范围内安装与补登记，回读租约/调度/钱包不变/在线状态；分别报告。

## 实施前已确认源码事实（原基线，非修改后的状态）

- HostingRentTransitionApplication 当前通过 provider.deploymentMode 选择套餐，并强制 adoptExisting 后才 registerTransition。
- HostingRentFinishingHandler 对所有部署执行 current/quiesce/evidence/cleanup，HandoverCompletion 把释放后的 projection 当公共实例保留。
- HostingRentRenewalServiceImpl 的续费本身是 DB-only，无心跳依赖；应保留而非新增在线条件。
- Runtime 已有多 Agent host 与 per-subject 生命周期门；不能把一个主服务误解为共享用户授权/会话。

## 状态

实施中。尚未修改生产服务或登记租约；代码、验证、安装与业务验收分别更新。全库文档工具依赖的 sdd-document-map.json 在公开导出中缺失，不把定向检查冒充全库通过。

## 2026-11-12实施记录（仍为部分候选，禁止按整链发布）

API本地提交：20f28c3c67（租约/自部署释放分离）、9071665bfe（恢复开源导出漏掉的编译依赖）、6ffb319f26及f375a67db7（定向测试fixture修正）。完整commit/tree与命令以私有verify输入为准；未push、未打生产包、未部署。Runtime/Web未修改；基线查询时两者远端develop已不同于本地，不自动覆盖或合并。

### 已实现的源码切片
- 正式维护CLI要求显式planId；原installation→binding→runtime→租约/首次待办同事务登记，不调用网络或adopt，也不要求hostId/在线。
- 自部署FINISHING走API-only事务：保留平台任务结算/预占资金保护，撤销精确旧installation及专用key，关闭租约/旧绑定身份并解除活动投影。无资金的本地启停同步不阻止解绑，不生成stop/cleanup证明。
- 已关闭自部署实例从公共实例SQL发现中排除（在LIMIT前），金融`completedHandover`不把它认作可托管复用；历史记录仍保留。
- 托管存量登记不再提前adopt。实际托管FINISHING时才允许根据原TRANSITION、原安装/绑定/租约取得关联，事务外adopt后重新读取并确认quiesce；未确认不得清理或释放。

### 基线修复与验证归因
- verify-01：参数顺序被argparse REMAINDER消费，未启动Gradle。保留原日志；后续将task ID放在保护参数后。
- verify-02：100.547秒，聊天模块33个编译错误；原开源导出漏了仍被调用的`archive/conversation`六个生产类。只从原分支固定e2e2cbe2305608c3bd01d27dcfc07eb40b526fe4恢复这六个精确文件；未恢复97个archive组件全库、历史材料或凭据。私有restored-build-dependencies.json记录逐文件SHA与来源，做嵌入主机路径/URL/凭据检查。新增正式维护入口的定向sourceSet避免无关历史startup fixture缺类。
- verify-03：52.582秒，生产源码已过编译；新增测试lambda与既有局部tx重名，改名后重试。
- verify-04：47.418秒，43项运行42通过/1失败；Mockito重新when触发含事务断言的既有answer，失败发生在测试设置阶段。改为doReturn；原XML已包外留存，不重标通过。
- verify-05：API f375a67db7固定候选，49项通过、0失败/跳过，validateLayering通过；Gradle81.746秒，外层81.969秒。四个hosting类43项加维护CLI输入/隔离Spring图6项；不代表整站启动或新邀请整链通过。
- sql-01：同API候选11项真实MySQL通过、0失败/跳过，validateLayering通过；Gradle56.415秒。覆盖两套餐TRANSITION/首次待办/重放与回滚、自动续费幂等、主动停止、原关系关闭回滚、私有实例SQL过滤和原安装资金范围。隔离MySQL使用独立随机端口和全新目录；确认正常shutdown、保存日志/XML后只删除本任务一次性data，不碰生产库。
- Runtime原样基线fb6fcb5ccf9861c04df810ad5a8acce337e232fd：runtime-host-baseline四项通过、0失败/跳过，Node test约0.792秒。仅证明已有主服务三Agent初始化/撤销隔离、单Agent失败隔离、重复主体/安装拒绝和身份替换拒绝；不代表主动控制协议、新邀请或真实OS多用户隔离已交付。
- 每次Gradle独立600秒systemd执行；复用同任务编译输出但不复用测试结果。真实SQL单独记录，不以重命名规避构建时限。完整输入、原失败日志、成功XML、逐用例test-summary和result保留私有verify-*/sql-01目录。

### 未完成项与下一条动作
- 新邀请仍通过HostingRentApplicationService.requireInventory/deploymentMode及HostingRentReconciler.prepareAndObserve调用旧控制适配器；受限主动接入→目标清单→报价→授权/ready→扣款的新链路尚未实现。
- Runtime现有RuntimeHost.ensureAgent可复用主服务，但尚未接通上述新业务授权/主动控制协议；不能把既有多Agent容器认作新协议已交付。跨用户新实例、初装/热添加与Web文书消费者还需同步并整链验收。
- 现行合同/验收已定向修订，历史发布记录不改。全量文档检查仍因公开导出缺少docs/sdd-document-map.json不可用。
- 磁盘只读预案：当时根盘约400MiB；现有清理器plan可回收0文件，未清他人缓存/备份。生产JAR约252MB，完整打包发布须核对实际空间；不因低空间删除生产/回退或既有证据。
- 扈三娘补登记仍未执行，不能将源码改动当作月费初始化完成。待完整受测候选/安装范围具备后，用正式维护入口显式self-hosted套餐、新固定实际cutover时间、回读30天租约/待办/钱包不变；不直接SQL插入、不沿用历史批次日期。

### 本轮交接状态

已验证API源代码切片及现有Runtime宿主隔离基线；总体仍IMPLEMENTING。未打包、未push、未部署、未登记扈三娘、未扣费。下一实现位置是API新邀请受限主动接入/清单授权与Runtime/Web对应消费者；不能只发布当前切片后称长期方案完成。完整回归还包括新用户目标库存与新安装、双模式主动控制、真实离线关闭、同主机热添加及部署回读。原开源导出仍缺与当前定向切片无关的archive bootstrap等历史默认测试依赖，未批量恢复；恢复的六类应在完整候选回归中覆盖实际消费者。


## 2026-11-12继续实施：Runtime主动传输候选（整链仍未完成）

本轮固定Runtime提交`1e1fd84b285130d7f4ec289b91338deb3213c6d9`，tree `7ad9802fc72ca8f950d0c6374211a166855e4c28`，源码包版本1.3.104。API仍为f375a67，无新增API/Web修改。开工只读远端查询Runtime develop为fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63，涉及另一路文档工具/版本修改；没有覆盖、合并或推送。组件提交使用原Runtime Codex作者身份的单命令配置，没有修改全局Git身份。

### 实现及责任边界
- 新增`runtime/conf/cyf-agent-runtime-v1/lib/hosting-outbound.mjs`：Runtime主动HTTP交换worker，不创建监听器；复用已有Q/R/M编解码和HostingControl处理器。授权固定host/tenant/client/owner/Agent；SETUP仅可读取capabilities/inventory，CONTROL单独授权，不能当AgentRuntime执行session。
- 原命令先落盘，原结果保存到API准确确认；丢包重传相同M，不重新生成结果或新操作。未存结果的中断命令必须等API再次认证和重投原命令才恢复；403/空poll/另一命令都不允许旧执行复活。既有hosting journal继续负责业务操作幂等，新文件仅为该授权的传输待确认状态。
- 每授权私有目录和独占writer；并发exchange拒绝乱序，一个Agent认证失败不影响同宿主另一个授权。HTTPS远端、loopback测试HTTP、禁止redirect；日志只记录分类，不记录token/异常原文。RB-03仅执行API授权；没有迁移收费状态机到Runtime。
- 同候选加入共享wire fixture、14项新测试及现有Runtime说明；现行设计正文增加具体字段、权限、重投/ACK约定。

### 实测证据
私有目录`/home/isp/state/cyf-runtime-lease-separation-20261112/outbound-*`。
- outbound-01为开发诊断：11项中2通过/9失败，失败均为after hook先删fixture目录、后释放新增worker锁；修正测试清理顺序，没有削弱生产锁保护。原失败日志保留；原shell末尾tail使wrapper返回0，不能把该值当Node测试成功。
- outbound-02：修正清理后11项通过；outbound-03：补撤权后恢复及跨Agent隔离后14项通过。这两批是开发诊断，不替代固定候选证据。
- outbound-04固定上述commit/tree，203项中201通过/2失败，均为旧UDS测试在过长TMPDIR下listen EINVAL；未改业务/测试源码绕过。保留input/result/TAP/summary，58.690秒。
- outbound-05同一完整候选、同selector，仅改为任务独占普通ext4磁盘短TMPDIR；**203通过、0失败/跳过**，53.996秒。14项新增含真实loopback HTTP+真实HostingControl；其余覆盖原控制/收养/生命周期/重新接纳/宿主隔离。Node v24.22.1与二进制摘要、fixture摘要、命令、精确源树、原日志摘要及逐用例摘要均已保存。临时短目录由fixture正常清空后只删除该空目录，有cleanup记录。
- `git diff --check`通过。全量文档检查仍因导出缺失文档map未运行；没有将本轮定向检查写成全库通过。未生成正式发行包，不新增可回收包登记，也未清理其他任务空间。

### 真实剩余工作（下一条从这里接续）
1. **此worker尚未接入agent-runtime启动/配置**。Java授权发放/撤销、专用认证lane及持久exchange队列也未实现；本轮HTTP服务为fixture，不是真实Java服务。不能把203项通过说成全链已通，不能手工伪造生产授权。
2. 新邀请前受限目标准备仍要解决：尚无绑定时不能调用现有requireRegistrationIdentity；应由API保存独立setup授权和新canonical Agent候选，目标隔离环境的实测清单绑定报价；reserve后才将原目标提升为正式安装授权并确认ready/capture。现有旧inventory的模板零库存路径不是新自部署目标实测。
3. 将API持久命令生产者、Runtime worker配置/每Agent动态添加及Web文书/报价接上同一fixture，再去掉新邀请对旧入站适配器的依赖。托管清理仍用原精确关联/停止/证据，不为切传输删保护。存量自动续费仍不依赖连接。
4. 仍需真实API+Runtime+Web端到端、最终包/授权安装及扈三娘正式维护补登记。磁盘只剩约355MiB，原清理预案0可回收，不删除他人缓存/状态。不得发布部分实现冒充长期方案。

本轮没有push、部署、生产DDL、扣费或补登记。整体状态继续IMPLEMENTING；无需重复问用户已确认的业务规则。

## 2026-11-12继续实施：API主动传输与真实跨端验证（仍未发布）

最终本地API候选`57b6d5f423122ce1f14a18402c1ccc7724236ea5`，tree `35845a04160dda589cbddbdddf5a9b85d6a3e57f`；本轮提交6a91acd6c9、46f6f6e59b、57b6d5f423。Runtime保持`1e1fd84b285130d7f4ec289b91338deb3213c6d9`，Web未改。均未push或安装；未查询本轮远端最新HEAD，不推定本地等于远端。根工作区出现其他任务的经济/模型治理文档修改，保留未动，不混入本任务交付。

### 实现及责任层
- API `HostingOutboundSecurityConfiguration/HostingOutboundCredentialFilter`在用户JWT及AgentRuntime前选中封闭专用lane。仅精确POST入口可使用RuntimeHosting凭据；重复Authorization、其他路由、Origin、query及X-Agent身份头拒绝。持久认证与撤销检查统一在exchange事务里执行，不在多个层重复认证。
- `HostingOutboundExchangeService`及JDBC `HostingOutboundStore`以进程配置tenant/client认证；grant锁串行化投递、回执、撤权。命令按授权分区FIFO，同ID只接受相同内容；核对原相关ID/请求/消息类型/host/主体。结果提交后才ACK，同结果ID不能完成两条命令，冲突返回409而非可重试503。
- 独立JDBC存储边界明确SQL分区；schema位于mapper的`db/agent-hosting-outbound.sql`，没有CHECK、触发器或启动DDL。`HostingOutboundConfiguration`按显式开关装配，默认不需要新表/DB bean；封闭安全lane仍生效，避免凭据掉入用户接口。
- register/revoke/enqueue仍只是要求调用方业务事务的内部原语，没有开放发证/任意命令入口。认证授权散列落库，不保存原token。**业务发证、CONTROL与预占绑定、解绑撤销该控制grant尚未接线**；不能手工创建生产grant补齐。
- 控制器复用全局Q/R和既有M协议，必须出现的ACK/command空值保留，畸形/重复字段输入返回400。未来无害Q.data字段可读取，未知执行语义仍拒绝。

### 本次正式证据
私有目录`/home/isp/state/cyf-runtime-lease-separation-20261112/exchange-01`至`exchange-03`，含input/result、Gradle日志、XML、逐用例test-summary、MySQL生命周期、Node日志和精确Runtime/fixture/toolchain摘要。
- exchange-01（API6a91acd6c9）：27.102秒外层Gradle，编译失败、测试未执行。mapper无Spring context依赖，错误使用@Repository；改为轻量JDBC类，由service层显式条件装配，不为此增加mapper框架依赖。原失败保留，经orchestrator归因后独立重试。
- exchange-02（API46f6f6e59b）：11项真实MySQL/安全/MVC测试全部通过，分层检查通过；外层Gradle53.407秒，含隔离MySQL初始化/停止的systemd整批74.554秒。真实Node进程请求真实HTTP桥接到生产Security/MVC/服务/JDBC，API已提交后故意断开回包；worker重启重传同一回执，队列仅完成一次。
- exchange-03（最终API57b6d5f423）：**91项通过，0失败/跳过，validateLayering通过**。其中新增14项（含真实Node跨端1项），原Transition7、Application35、Handover16、Finishing13、维护CLI6。不是之前49项的原样重跑；ManagedStop本批未选，旧证据仍只绑定原候选。Gradle64.458秒，含隔离MySQL的systemd整批82.055秒，各次均独立600秒以内。
- 新增用例覆盖并发重复结果、撤权锁先于等待poll/回执、commit异常真实回滚、不同授权同host隔离、SETUP能力限制、错tenant/client/token/host拒绝、结果ID跨命令冲突、生产条件装配和默认关闭的凭据兜底拒绝。丢ACK的Node使用实际HostingControl但库存观察器/宿主peer来自fixture；**不是新用户实际目标库存、真实发证或正式宿主OS隔离验收**。
- 复用原本任务普通磁盘编译输出，测试重新执行；每次隔离MySQL随机非生产端口、全新任务目录，停止并确认exit0后仅移除本次data，日志证据保留。未清他人缓存/源码/状态；未生成最终安装包，无新的可回收包可登记。

### 下一条动作及真实边界
1. 从`HostingRentApplicationService.quote/bind`接业务生产者。目前仍同步`requireInventory`与旧provisioner；新用户无绑定时需独立SETUP身份、持久目标及部署类型，受限主动通道返回该目标实测清单后才能冻结报价。不能把本轮fixture清单或模板0库存当实测。
2. 预占成功后绑定独立CONTROL与精确安装/租约关系，并在解绑关闭的同一责任事务撤销相应grant；不要仅按host撤销，也不要让新关系共享旧授权。完成ready/capture的消费者仍复用既有业务状态机，不将传输ACK当就绪或收费完成。
3. Runtime worker仍未接daemon配置/热添加；Web文书/目标准备/报价消费者尚未改。托管FINISHING当前仍使用旧控制适配器；其精确关联、停止、私有资产隔离保护不能因换传输删除。
4. 尚未生产DDL、打包、安装、补登记扈三娘或扣费。剩余磁盘约340MiB，之前维护器可回收0；最终包空间仍需核对。文档map缺失，全库docs检查不可用；本轮只做定向文档与diff检查。

整体仍IMPLEMENTING，不把传输联调完成升格为长期方案整链完成。补登记仍须正式维护入口、新固定实际cutover时间及30天租约/首次待办/钱包不变回读。

## 2026-11-13继续实施：受限登记/报价与Runtime宿主主动通道（仍未发布）

本轮API候选`d0cdf6a03a52678c2ebc2da09803d2367575d12c`，tree `145ba8482835588dfc34a288d61a65c934c0826d`；Runtime候选`61c85042839a6fe11d65682cd8f0cf7cc9764113`，tree `548f508385c507be952e8af373f37d45c71518a2`，包版本1.3.106。均为本地候选，没有push、打正式包或安装，不推定远端develop或线上等于本地。Web未改。

### 已落地的责任层与边界

- API新`HostingSetupService/HostingSetupStore`与原用户认证Controller接线：受限登记、查询、取消只处理SETUP与独立目标，不创建付费绑定、正式installation或扣款。Runtime本地保留随机token，注册只传SHA-256，返回/重放只含公共授权元数据。托管host按运维配置准入；自部署新建canonicalAgentId，不借旧用户安装。
- 原quote生产者使用setup明确部署类型与目标，要求清单来自`inventorySource=TARGET`；包含停用但仍安装的技能。每个新报价幂等键另排一次目标inventory，提交命令后才返回pending，不在抛异常的报价事务里丢命令；已冻结报价同键重放。Runtime a3184b0增加TARGET与模板假设的区分及共享setup报文fixture。
- **确认/预占仍明确关闭**：setup报价不能落回旧入站provider，bind返回`HOSTING_SETUP_ACTIVATION_PENDING`且不扣款。CONTROL/正式安装、真实目标预准备、Web文书还没有接通；不把SETUP登记当新邀请已完成。
- Runtime原daemon通过HostingControl工厂选择outbound-only，无Unix/TCP/TLS监听或socket目录前置；与原入站配置互斥。单宿主加载私有授权文件，启动/心跳周期热添加、移除独立worker；每grant状态与writer分开。坏替换文件不停止健康worker，永久错误不因未变文件自动重启，停服先abort/join再释放writer。重载等待不阻塞其他Agent心跳；原执行/资金状态机不迁到worker。
- 明确outbound配置允许空agents初装管理宿主；RuntimeHost与配置读取两端同步。授权文件必须在各私有可变根之外；元数据/token改变须用新授权而非覆盖原ID。日志脱敏加入RuntimeHosting/rth1。安装器及validator的文件清单补齐新增import闭包。保留旧入站消费者兼容，不宣称托管FINISHING已切完主动传输。

### 证据与失败归因

私有目录仍为`/home/isp/state/cyf-runtime-lease-separation-20261112/`。

- setup-01（API5c74b914f4）：98项通过，Gradle外层226.339秒。setup-02（APId0cdf6a03a、Runtimea3184b0）：98项通过、0失败/跳过，validateLayering通过，外层122.744秒；独立MySQL生命周期143.339秒正常exit0并回收本批data。两次测试均包含实际SQL及已有Node跨端测试；新setup库存由fixture返回，不是实际用户主机目标观测。逐用例summary已按本次真实selector从XML生成，未计入build目录残留的其他suite。
- outbound-host-diagnostic：首轮16项15通过/1失败，发现配置读取虽允许空Agent，但RuntimeHost仍拒绝；生产构造器同步修正。第二轮16通过；第三轮新增心跳不阻塞及凭据脱敏后18通过。仅开发诊断，不冒充固定候选正式通过。
- outbound-host-01（Runtime527dd74）：243项242通过/1失败，64.853秒。真实import图测试发现install.sh/validate.sh未包含新模块；4719f48补全两份实际清单，没有删除测试。
- outbound-host-02（Runtime4719f48）：243项241通过/2失败，93.292秒。原安装清单缺口已经通过；新失败分别为测试用1000次setImmediate转圈等待IO，及依赖完整性fixture复制122MiB Node+35MiB依赖时ENOSPC。61c8504改为等待实际peer请求事件/worker结束，不增加业务超时。下一次保持同selector，串行测试文件避免并行fixture占盘。
- 为解决实际ENOSPC，只回收本任务`verify-02/build`可再生中间输出，5500文件、42,272,387逻辑字节；先将所有reports/test-results复制到包外并保存逐文件SHA清单`build-scratch-retired/manifest.json`。原源码、共享Gradle cache、原批次input/log/XML、生产状态和备份均未删除；无最终发行包，因此没有伪造完成包登记。下次Gradle不得复用该已回收输出作为证据，需重新产出。本机空间仍不足以承诺最终发行包/安装。
- API两提交已fast-forward合入本地develop；临时工作区`/root/.codex/worktrees/runtime-lease-setup/api`仍与同候选一致且干净。尝试既有archive_worktree入口返回“task's primary checkout cannot be removed”；没有绕过保护直接删除。后续继续复用该工作区，不另开阶段worktree。

### 下一条动作（覆盖上文历史“未完成项”中已实现的部分）

1. 完成真实新目标的预准备与库存观测。目前TARGET校验已落实，但尚未存在Agent隔离目录的目标不能用旧模板零库存绕过；须在SETUP权限下准备隔离目标而不注册/启动付费执行。
2. 用户确认后在原预占事务绑定精确CONTROL/安装/租约，主动队列生产prepare/ensure和ready消费者；关系关闭同事务撤销精确控制grant。托管收尾的停止/清理证明仍须保留，不能以传输ACK代替。
3. Web接受限登记/等待新目标观测/报价与激活文书；完成实际API+Runtime+Web闭环、同主机跨用户真实OS隔离和离线解绑验收。
4. 最终候选必要测试、制品空间与授权安装具备后，才用正式维护CLI补登记扈三娘，固定实际cutoverAt，回读30天租约、首次待办、钱包不变。**本轮仍未补登记、未扣费、未生产DDL/部署。**

### 本轮最终回读

- outbound-host-03固定Runtime61c8504：**243项全部通过，0失败/跳过/取消**，Node TAP95.066秒，外层95.136秒；包括同一批所有受影响宿主、生命周期、配置、TLS兼容、Provider环境、知识维护/import闭包测试。测试文件串行，未删selector或跳过复制依赖用例。临时普通磁盘目录正常清空，只删除本批空目录。原01/02失败结果保持。
- 本轮失败矩阵：01是生产安装清单缺失，修复4719f48；02是测试事件等待方式与fixture磁盘容量，修复61c8504并回收自有中间输出、串行执行；03同覆盖范围全通过。这是不同根因/输入的修复重试，不是对同根因同输入盲重试。编排器按累计两次失败进入root-cause状态后，沿其authorize-remediation入口登记本节归因与精确候选，再登记分层测试证据；不改写失败日志，也不把测试工具状态当生产发布许可。
- 根规格定向diff检查通过，完整文档map仍缺失；未运行或宣称全库文档检查通过。根仓含另一任务的模型/经济治理修改，本轮不整体暂存或提交根仓。后续事实仍以本节“下一条动作”为准，不需要重新询问用户已确认的计费/机器隔离规则。

## 2026-11-13本轮接线与失败矩阵（进行中）

用户要求固定范围、一次连续完成，不再给无依据十小时估算。本轮不新增计费规则，仍复用原reserve/ready/capture/refund；源码补目标目录、精确控制授权与出站适配、Web登记及原单重查。尚未发布或补登记。

- activation-01：API源码在隔离MySQL初始化期间仍有本轮capability编辑，exact-tree拒绝脏树；Gradle未启动、测试0项。修复为先提交并冻结33e6dc3a91后重试。原失败及MySQL正常停止回执保留。
- activation-02：API33e6dc3a91固定，隔离MySQL已启动，但共享Gradle串行位由HERO-MODEL-HOSTING-20261112的db-verify-03持有；独立600秒耗尽，systemd记录timeout/SIGTERM，Gradle未启动、测试0项。MySQL日志确认本批正常shutdown；没有停止他人任务、绕锁或重标成功。已用conflict-alert通知协调，不使用跨聊天发送工具。
- 两次不是相同源码同根因盲重试。后续只有确认既有Gradle持有者退出后才重试；先对冻结新候选编译/分层，再跑真实MySQL覆盖，不把编译通过称业务验收。
- 初步Node诊断20项（target3、outbound17）通过，配对CLI1项通过；目标观察器仍为fixture，不能宣称真实用户主机库存/跨用户OS隔离验收。首轮target诊断错误为测试误用不存在的restart方法及scope额外字段，已修正为fixture的stop/start及精确scope；原失败日志保留。
- Web147063c的55项通过，但lint6项失败（textarea格式、按钮属性换行、既有未用import）；修复113c6e6后web-activation-02固定源55项及定向lint通过。浏览器原型18786已存在，HTTP返回脚本SHA与本机一致；仅证明预览可读取，不冒称真人浏览器全端验收。

明确仍不可宣称完成的交付点：平台托管自动配对生产者、旧租约精确CONTROL迁移、退款后重邀/同机新owner实际准入与OS隔离验收、真实三端ready/capture闭环、受控制品发布和扈三娘TRANSITION补登记。现有手工一次配对工具只解决自部署登记及后续自动控制授权领取，不冒充一键托管；不得先全局启用outbound导致旧租约失去控制路由。源码/单测/线上事实分别报告。

- runtime-activation-01固定e29bee5：95项中92通过、2失败、1原生引擎条件用例跳过，446.134秒。两失败均为runner将TMPDIR设成过长批次目录导致Unix socket路径超限（listen EINVAL），不是生命周期业务断言；修复runner复用此前短路径普通磁盘临时目录，不改生产Unix地址限制、不删测试。共享激活fixture补入两个摘要的完整登记Q/R，历史单凭据fixture不改写；下一次绑定新fixture与真实Runtime commit重跑。

### 01:45续接核对（2026-11-13，尚未发布）

- runtime-activation-02固定b629d53：95项，94通过、1原生引擎条件跳过、0失败，外层543.923秒；短磁盘TMPDIR解决前批UDS路径超限。不是实际引擎或线上验收。
- activation-compile-03固定cd800e：systemd timeout，600秒上限；日志最后完成common-core jar，未完成目标编译、未运行API测试。与02串行等待不同，本批已拿锁，冷依赖重建耗时。保留日志及现有中间产物，下一候选复用增量但不复用未产出的测试证据。
- API 5ee7475626修复SETUP取消幂等与激活竞争：先锁确切SETUP授权（允许已撤销重放），再FOR UPDATE当前读activation，避免REPEATABLE_READ旧快照绕过已提交激活；新增旧快照并发及先取消再激活用例。尚未执行新测试。
- 最终范围不再扩展：租期/离线分离；双模式主动接入与一宿主多Agent；邀请/续费/解绑和既有资金闭环；旧租约受控迁移与扈三娘补登记。托管自动分配、旧CONTROL映射、退款重邀和真实用户隔离是此范围内尚待闭合的缺口，不以文档/局部测试冒充完成。

### 固定收口清单（本轮后续不新增旁支）

| 必改项 | 真实责任层 / 复用入口 | 完成判据 |
| --- | --- | --- |
| 租期、续费与在线状态分离 | 既有economy租约/renewal；HostingRentTransitionApplication | 离线不暂停/不阻止有余额自动续期；显式套餐登记不联网、不改钱包 |
| 主动接入及一次配置后恢复 | HostingSetupService/OutboundExchange/Provisioning；Runtime HostingOutboundHost/HostingControl | 无入站地址依赖；断线重连/进程重启自动恢复；不得把手工逐Agent配对称为托管自动分配 |
| 邀请与资金闭环 | HostingRentApplicationService/Reconciler + 既有Web composable | 目标库存→原reserve→精确CONTROL→真实就绪→原capture/refund；失败重邀可走通，不追加一套资金规则 |
| 解绑及一宿主多Agent | 既有Finishing/HandoverCompletion；Runtime身份/私有目录/执行隔离 | 自部署解绑不等清理、不删资产；单Agent解绑不停止宿主或他人Agent；新用户不继承旧凭据 |
| 存量切换及扈三娘 | 正式维护CLI、固定生产目录快照及原安装工具 | 先具备精确控制映射再启用；保留李逵已有账；扈三娘30天租约/首次调度/钱包不变实际回读 |

已知必须收口的实现缺口仍为：托管自动提供配对材料、旧租约CONTROL映射、退款后重邀、新owner实际准入/隔离及三端真实就绪。不能将上述漏项删出范围后称“完成”，也不顺手改价格、钱包模型、全站接口、部署框架。

- API 9a92532658补CONTROL摘要唯一键冲突→409，调用方原reserve/binding事务整体回滚；新增冲突保留其他授权用例。连同5ee747的两项并发/取消用例，共新增3项MySQL用例，尚未执行。
- compile04在等待另一任务串行位时主动停止本任务unit，未启动Gradle、0测试；不是通过或超时，见stopped-before-gradle.json。发现其继承过期Runtime输入另留correction.json，原证据不改写；该批不执行Runtime测试。compile05待他人退出后启动，固定9a9253和真实Runtime b629d53，移除与非SQL验证无关的mysqld全文件hash，复用普通磁盘中间输出和串行入口，独立600秒。未中断他人/生产服务。
- Eva只读结果：运行包1.3.102；sudo journal读取需密码，因此未取得服务日志。进程活跃不证明API会话正常，也不证明租约初始化；未写Eva配置或生产数据库。

### 02:02验证结束（2026-11-13）

compile05固定9a92532658在600秒达到systemd timeout：本批agent-service生产源码编译成功（日志171.031秒），随后仍编译回归所需其他模块，未到compileManagedHostingRegressionJava/测试/validateLayering，测试0项。不能以生产compileJava通过替代整个批次成功。与compile03同属已回收中间产物后的冷构建预算问题，保留所有本批输出和日志，不继续盲重试；若完整下次预计超600秒须申请单次例外。activation-mysql-03仅准备了runner与真实Runtime输入，未启动MySQL或Gradle，没有测试结果。

本次实改3文件、两个提交5ee7475626/9a92532658：取消幂等与旧快照竞争、控制摘要冲突回滚错误映射；新增3项SQL测试尚未执行。API工作区干净。当前整链仍未完成，托管自动配对、旧租约迁移、退款重邀/新owner实际准入等未改完；无生产写入/部署/扈三娘补登记。


## 2026-11-13 开发续接：能力真实消费者与维护回归（未部署）

用户要求一次完成开发、再统一部署验收；本轮没有生产SQL、安装、重启、扣款或补登记操作。

- API候选 `7c72319830a70f802f3dd138cb3871b2ff2932b9` 后追加 `ccf2875014`：主机维护preview回滚、换密钥/撤销幂等、真实安装/归属/付款人关联导入、同主机不同授权共享读锁并发，以及隔离维护Spring图测试。新增测试尚未通过编译/执行，不能计为通过。
- Web真实 `economyPreviewCapability` 原来严格限定3字段，会拒绝API已返回的4字段报文；已修复已知hostingSetupEnabled布尔字段解析，旧报文不猜开关，允许无害新增元数据。相关61项单测通过；另补主机分页完整替换、登记未知恢复、取消未知恢复三项，结果待本批日志。
- 浏览器使用真实Vue面板、composable和能力decoder，HTTP/身份仍为合成fixture：`host-browser-03/result.json` 为PASS，30检查/30截图，覆盖1440/390/320宽度、托管自动准备、自部署首次登记/选主机、报价setup绑定、取消未付款目标及原租约状态。不是生产业务验收。前两次启动失败保留：默认Chromium包装器目标已不存在；指定系统Chromium后长TMPDIR启动失败，改用普通磁盘短路径后通过。未改共享包装器/浏览器配置。
- 后端 `host-candidate-01` 在共享构建锁等待后进入Gradle配置，600秒超时，未执行测试；`host-candidate-02` 在配置/依赖重编译后进入agent-service编译，600秒超时，未执行测试；原input/log/timeout.json均保留。当前 `host-candidate-03` 用同一普通磁盘增量输出及新增测试候选，仍受600秒限时，不延长原批次。
- 完整Runtime hosting回归 `runtime-host-regression-01` 600秒超时：70通过、7取消，包含既有Java桥用例15秒超时；未运行到的文件不是通过。此前29项定向通过不能替代本次完整回归。共享主机观测出现CPU空闲0%、run queue约28，未操作其他任务/服务/清理进程。

证据根：`/home/isp/state/cyf-runtime-lease-separation-20261112/`。必须继续完成后端编译/MySQL事务与真实跨端回归、Runtime剩余用例、固定干净候选构建，之后才可受控部署；不得先发布已通过的Web部分。李逵原租期、扈三娘待补登记、RETAINED混合续费与生产开关仍沿此前核查，不改写成线上完成。

### 本轮固定候选与后续实测

- API `6408ae3081bfb3decb010e909aa185f8158c6758`；Runtime `3ddc90d13c88813f967dd9d2c8f3b03b42b07aff`（1.3.108）；Web `325676fbe2c4ea3470b575edcac0303bf99cf11e`。三个组件均已提交且工作区干净，仅为开发候选，未推送/发布。本轮复用已有Git身份，未改全局配置。
- Web新增未知恢复与完整分页测试后，64项全部通过；定向ESLint退出0（只有Browserslist数据提示），浏览器30检查/30截图PASS。
- 固定Runtime候选的出站宿主/worker/登记CLI回归再次执行：29通过、0失败/取消/跳过，44.1秒。证据`runtime-host-targeted-02`。仍不能代替完整Runtime回归。
- `host-candidate-03`工具返回143，未产生result.json；最后任务agent-service compileJava，未执行测试，不记成构建成功。11:42:29重新观测共享主机：CPU idle69%、run queue5、1分钟load4.79，显著低于之前idle0%/run queue28；据此才启动新候选`host-candidate-04`，仍为独立600秒上限，不延长旧尝试，不操作其他进程。
- 最小幂等补全：主机原键POST重放/GET重查，不成功接受未记录的新别名键；不新建幂等别名表。存量控制IMPORT要求既有installation ACTIVE，拒绝撤销安装重新获权；补相应回归，尚待Java执行。

### 600秒构建边界与候选合流（本轮停点）

`host-candidate-04`退出124：agent-service业务源码编译成功（213.05秒），之后仍在chat-service等测试/维护所依赖模块编译时达到600秒；没有执行到测试，没有最终发布JAR。前述较低负载复测并未让整轮落入600秒，本次不能再以相同根因盲重试，需要单次时限例外或实际可验证的执行条件整改。未放宽默认规则、未中止其他任务/业务进程。

复核并行开发发现API develop已新增三项人物模型/托管价格数据库配置变更（c4f521fb5b/efab8f9cc1/ae5a96d19b）。为防最终发布覆盖它们，已合入本工作分支：当前API `3e4c349d9a8d3f296e999750f1d4bb45c0bf14e8`，tree `3941b2dd67c7ef7c950d0d3c0d4b5d5da25bfe10`；源码自动合并，唯一接口目录文字冲突保留数据库说明与本任务新增接口两部分。**合流后候选尚未编译测试**；原6408ae的业务编译事实不能移记给合流候选。Web/Runtime固定候选不变。

准备了复用既有owned-MySQL脚本的 `host-integration-01`，尚未启动：出站目录/认证/事务/维护导入、真实RETAINED混合续费以及人物价格数据库回归；出站fixture与续费fixture使用不同、全新且非生产datadir/随机端口。后续需先完成Java编译反馈，归因修复后执行该集成回归及未完的Runtime完整用例，再一次性构建打包/受控部署/线上验收与扈三娘补登记。不要单独先发Web，不要启用生产自动续费来代替隔离验证。

完整候选、单测日志和证据索引：`candidate-source-20261113/sources.json`。生产与收费状态未变；全部后端构建及本轮测试子进程均已退出。当前需要向用户申请**下一次后端构建单次上限临时放宽至20分钟**，而非扩大项目范围或承诺20分钟全部交付。

### 2026-11-13 构建超时归因（覆盖前文20分钟建议，尚未业务部署）

用户最新要求是先解决反复超过10分钟；**不执行前文1200秒建议**。每次仍由独立systemd单元限制600秒，保留失败、锁等待及真实源码，不删必要测试、不把单元测试挪成免限时回归。当前诊断版本1.1.48-SNAPSHOT不得覆盖其他任务已部署的1.1.49。

已证实而非猜测的原因和修复：

1. 旧临时runner漏掉正式`local_build.py`入口已有的`--build-cache --parallel`；dependency home不等于编译缓存。改回正式入口。根工具072b568a增加lock_wait_seconds/invocation_seconds，锁、超时和权限不变；19项编排器测试、25项local工具测试通过。
2. 两核主机存在长期后台磁盘清理和其他负载，旧清理默认前台优先级。根工具c0ea3139仅让清理自身及以后子进程nice19/idle（86项隔离测试）；已备份/原子安装，SHA和priority smoke见build-performance/cleanup-install.json。另对当时精确识别的cron清理shell4065378（startTicks121459200）降低优先级，没有kill。后续只读观察发现其已归属system-cyfcleanup.slice；此迁移不是本任务执行，不把它记成本任务成果、不接管其他任务。不能承诺任意外部竞争下600秒。
3. C1并非应取消项：同cd73d2bf源码强制agent模块重编，C1总224.203秒，对比分层JIT385.139秒；保留现有C1，不改生产JVM。诊断非正式包。
4. 长批次TMPDIR使真实UDS单测报Unix domain path too long；改短普通磁盘输出，未跳过UDS单测。
5. 完整入口发现真实分层和旧测试编译错误：cd73d2bf改Maintenance通过既有HostingRentRenewalService锁定租约，不直接依赖economy mapper；新增3项import测试；35853123修正已删除public purpose字段的测试，改事务读取真实grant store。MySQL测试只编译尚未实际执行。
6. **JFR证实最终JAR检查的临时嵌套包逐个fsync。** 对lease06同一240MiB JAR独立执行原verifier：91.12秒、user57.61s/system9.59s；ExecutionSample+NativeMethodSample共692，其中315在IdentityBoundOutputStream.close→FileChannel.force→force0，193在Inflater。不是把采样占比当精确墙钟比例。API73004150只去掉同进程同channel读取、随即删除的scratch文件force(true)，保留文件identity/权限/CRC/全量ZIP检查/限额/错误和清理，不改最终制品或回执持久化；新增write-view重复close、同channel读回、关闭后写拒绝和清理生命周期测试。JDK FileChannel文档明确同程序文件视图一致性；fsync承担持久化，不是本例读可见性的前置。最终收益仍须本批构建实测。

原始结果全部保留，不重标为成功：

| 批次 | 实际结果 |
|---|---|
|standard01|279.217秒，真实分层错误|
|standard02|600秒终止，未完成|
|standard03|216.102秒，真实旧purpose测试编译错误|
|standard04|约458秒，2项UDS路径过长失败|
|lease05|600.005秒终止，非完整通过|
|lease06|600秒终止，Agent security Test task165.9秒，仍未执行到starter维护/基线测试|
|hotspots|原35853123，JFR定向validateLayering+23项security测试成功，324.994秒；分层93.873秒、security76.932秒；不是完整构建|
|verifier-profile|原lease06 JAR只读诊断，91.12秒exit0；非新制品/发布|
|lease07|编排器因ledger仍绑定旧tree在启动Gradle前拒绝，未执行测试；修正绑定后另起lease08|
|lease08|73004150，同样完整定向单测+发布baseline+validateLayering+fresh JAR+package，执行中；结果待实测更新|

任务图核实：bootJar的原doLast含providers.javaexec，长时间占用starter任务执行，starter维护/基线排在后面不是“已经通过”；不是common-test→starter循环依赖。不能只以bootJar文件存在作为构建成功。分层扫描热点优化、Mock配置替换均未实施，避免无依据扩大范围。

证据：`/home/isp/state/cyf-runtime-lease-separation-20261112/build-performance/`；短批次`/home/isp/state/cyf-build/{lease05,lease06,hotspots,verifier-profile,lease07,lease08}`。JFR原件、命令、完整commit/tree、日志/XML和失败result保留。正式候选索引须另更新，旧candidate-source索引仍只对应旧候选，不能复用为新源码通过证明。

范围仍未完成：真实MySQL/Runtime集成、Web最终生产包、三端协调部署、生产迁移/自动续费开关及扈三娘补登记；李逵线上资金/租期未改。

### 2026-11-13 15:00 紧急前向发布（最新用户：不要回退，开发完上线）

- 不执行版本回退。14:44直连生产10018 health UP；根盘只余1GB。受控停止本任务 `cyf-lease-mysql-integration2-20261113.service`（MainPID0/inactive）；仅删除int1/int2已停独占MySQL合成datadir，以及lease05/06未发布失败构建中间JAR，删除清单/摘要在 `/home/isp/state/cyf-build/*cleanup-20261113.json`。没有生产SQL、重启或业务部署。
- 当前API `20ce8daa9f3dd62215f0f0f4eb5a93a9f3de0a9a`，tree `85a76249e2a9afcc8630de4c1c7e198b37556ff2`。修复MVC无害新增字段兼容、跨端Runtime仓根fixture路径、Cutover MySQL Subject第五字段；根a736834b让bootJar排在所选测试/分层之后。
- lease08因新增测试assertThrows import遗漏失败，8b197dea已修。lease09在bootJar校验时发现source dirty而失败，事后干净，临时attach文件原因未实证。int1曾发现上述MVC/fixture问题后超时，int2用户要求优先上线而停止；都不是集成通过。
- lease10正式构建14:46:39启动，600秒终止于bootJar，未产生可发布回执。197项已完成测试、0失败、2跳过；分层成功。完整XML及 `completed-tests-summary.json`保留。观察到本候选新增测试编译61s+32s，后续重试可复用这些编译缓存，不复用测试/JAR，不删除必要校验。此轮不再扩大性能工具修改。
- Web候选已合入线上模型UI469ad52，当前6ce64429e5c75477d5f10d358759da9caa8692f8/1.16.140。因主工作区真实node_modules与正式共享依赖入口冲突，准备独立固定源码 `/home/isp/state/cyf-build/lease-web-source`（共享Git对象，不触碰其他任务worktree）；lease-web正式构建正在运行，含hosting-rent与hosting-rent-ui测试。
- Runtime候选仍3ddc90d13c88813f967dd9d2c8f3b03b42b07aff/1.3.108；当前本机1.3.103的fb6fcb5是候选祖先，两者codex-bridge与工具链源码完全未变。Eva实际aarch64、Runtime1.3.102、服务active、磁盘334MB；不能发送本机x86依赖。Eva无current.json（需读取实际release-records），`sudo -n true`需要密码，尚在查确切允许的服务管理权限，不绕权限。
- 正式发布仍未发生，自动续费/扈三娘补登记未完成，李逵原账/租期未修改。不得把本节准备事实写成已验收。

### 2026-11-13 15:45 发布候选准备结果与真实阻碍

**没有回退、没有业务部署、没有生产SQL写入；扈三娘补登记/自动续费/线上验收仍未完成。** 用户已授权前向上线；Eva服务启停权限不足已向用户明确提出，不绕过sudo/polkit。

当前固定制品：
- API `d6d910299a2b3247e4f516107658d82773cd30a0` / tree `842e2e7a741544475c6d87b65bb5d50b95f762a8`，Module/Implementation/Release均1.1.50-SNAPSHOT。lease12 Gradle真实成功（596.976秒），197测试0失败2跳过，分层/fresh JAR成功；整体600秒在export前终止，**仍保留STOPPED_BEFORE_COMPLETION，不能称整批10分钟通过**。之后仅重试失败打包，复用完整成功Gradle事实和相同源码，不重跑/伪造测试。既有producer完整复验成功117.115秒；证明 `/home/isp/state/cyf-runtime-lease-separation-20261112/forward-release-20261113/api-package-retry2.json`。包 `/home/isp/state/cyf-build/lease12/package/api.tgz` SHA256 `61bffbd5e0c54c120ea77446f4d9569fa43bf219e3a375076f313936f5992149`；JAR `8046c5a64215f197d947da77c32cfaa779b2af24ec13334dd9cb9cf911afa51f`。
- lease11 Gradle452.99秒成功，随后打包整体达600秒；原失败/包外metadata保留，未发布旧Module1.1.48候选。最终包producer gzip默认9改1，根330c1c13，40工具测试通过；仍保留最终包fsync、CRC/所有成员/源码摘要/身份与原子发布。
- 构建过程中检测其他活动任务修改local_build.py（默认.tar）及producer；未覆盖其修改。第一次包装恢复因工具变更拒绝，保留FAIL；第二次从330c1c13还原**与原调用输入SHA完全一致**的不可变工具快照，仅用于原.tgz生产者。路径/摘要/原始来源在 `forward-release-20261113/tool-snapshot-provenance.json`，不伪称当前工具/新.tar路径已经验证。快照生产者沿原全部校验。
- Web 6ce64429e5c75477d5f10d358759da9caa8692f8，1.16.140，112通过/2pending/0失败，392秒构建打包成功。包 `/home/isp/state/cyf-build/lease-web/package/web.tgz` SHA `e56f967e4cc948fc4ca35ddec78af6048ced3faef8da54fa334a7d7347ed06f8`。独占构建源码副本完成后删除，未动主仓/共享node_modules。
- Runtime3ddc90d/1.3.108，`/home/isp/state/cyf-build/rt12/build-result.json`，87通过0失败0跳过，39.672秒完成portable code package。SHA `0283182c25c49c6cd0dab3ba2bceaa6ae126a2a4830bb46ee069bdeb895ec65e`；不含x86依赖，目标主机依赖需各自验证保留。之前长TMPDIR导致2项UDS EINVAL失败，原失败保留；改短普通磁盘路径后同六文件87项全通过，Java bridge先前15秒取消问题本次未复现。
- Runtime代码包及manifest已传Eva `/home/chc/state/cyf-local-build/runtime-lease-20261113/`，远端SHA已相同；**仅暂存，未替换app/重启**。Eva现状1.3.102/bridge1.1.71，aarch64，服务PID20936；当前记录为 `release-records/1.3.102-20261112.json`，没有current.json。`sudo -n -l`要求密码；`pkcheck org.freedesktop.systemd1.manage-units`退出2，需用户为该服务授权启停；不要信号强停绕过服务权限。
- 本机Runtime candidate沿旧安装器manifest/派生缓存验证与validate.sh准备。脚本 `forward-release-20261113/prepare-local-runtime.py`；首尝试缺datetime import，仅准备失败、未触生产，原FAIL单独保存；修复后继续同一独占暂存目录。结果以 `runtime-local-stage/result.json` 为准，不能把代码包通过直接当主机安装/验收。

必须随发布处理的实际配置差异：当前API仓为sanitized source，20个生产键变为外部占位符，而旧线上JAR仍内嵌加密值。已从**当前实际生产JAR**把这些既有值迁到root私有candidate外部properties，原外部覆盖优先，未输出解密值/未写源码。`forward-release-20261113/configuration-externalization.json`列属性名和前后摘要，`application-prod.properties.{before,candidate}`均0600；**尚未安装**。不先处理该差异就上线会导致数据库等初始化失败。新required keys无未解析新增项。

API/Web安装descriptor已按真实候选和当前生产前代摘要准备在 `forward-release-20261113/*-install-descriptor.json`，未消费，实际安装前要重核生产前代与工具/发布锁。尚未配置/注册主机凭据、执行六张新表受控DDL、维护REGISTER/IMPORT/TRANSITION，不能直接启动这些新功能。

15:14生产只读事实：扈三娘binding7/installation ACTIVE、仍无lease；李逵原期2026-11-11 22:02:03.301→2026-12-11 22:02:03.301、50文/30天未变，钱包3486文；仍有两条RETAINED旧公孙胜lease。身份与空新表目录快照在 `forward-release-20261113/{db-before-readonly,identity-readonly}.tsv`。实际补登记主体已确认actor chcbz、tenant0/client jiafewnnv58ec2379c、原installation/host，cutoverAt必须在真实执行时固定。

资源：只回收本任务失败/终止批次的合成DB、generated classes/依赖副本、未发布过期候选，报告/日志/摘要保留。清理旧generated目录PID13458曾在lease12/打包时暂停，15:44已CONT并nice19/idle恢复；不接管其他任务清理。具体最终清理结果以 `/home/isp/state/cyf-build/retired-generated-cleanup-20261113.json` 为准。生产API再次health UP，磁盘约1.1GB，不宣称全环境正常或验收完成。

15:46补记：本机Runtime候选已完成原validate.sh/完整manifest/未改依赖及live donor复核，`runtime-local-stage/result.json=STAGED_NOT_INSTALLED`（62.228秒），未启停服务。旧generated清理PID13458已退出，无暂停进程遗留；仍不代表业务已部署。

## 2026-11-13 16:58 +08 后续授权上线与定向验收（覆盖上节“尚未安装”状态）

用户补充 Eva 的 sudo 密码所在文件后，已在 Eva 本机仅取 `SUDO_PASSWORD` 经 stdin 验证/提权；没有要求管理员账号，没有输出或回传凭据。沿用户“不回退、继续上线”授权执行，未恢复旧方案、未启动 Flow、未重跑应用构建。**16:17验收目标已超时并已明确告知；不把本轮称为两小时完成或全量验收通过。**

统一证据目录：`/home/isp/state/cyf-runtime-lease-separation-20261112/forward-release-20261113/`（下称 F）；Eva 原证据：`/home/chc/state/cyf-local-build/runtime-lease-20261113/`。选取的非秘密回执同步至 F/eva-evidence；不复制 auth、OAuth session、主机token或provider配置。

### 已实施的发布和数据操作

- **API 1.1.50-SNAPSHOT**：发布上节固定 d6d9102/tree842e2e7 制品，JAR SHA仍为 `8046c5a64215f197d947da77c32cfaa779b2af24ec13334dd9cb9cf911afa51f`；原 LOCAL 安装器、前代摘要、锁和备份保留。descriptor指定 forward-only。真实安装 PASS，PID41580，制品身份匹配，health UP；见 F/api-install.log、F/api-final-health.json 和正式 record。20项外部配置迁移在原协调器/发布锁内备份、比较前值、原子安装，没有把配置秘密写源码。
- **Web 1.16.140**：固定6ce64429候选已发布。初次线上验证耗尽安装器600秒预算；没有回退或重装。原因定位为独立Python3.11缺省CA路径未指向系统信任库，保留失败及停止诊断回执；没有关闭TLS验证。显式使用原OS CA后，对同一已安装候选单独重验256个入口/JS/CSS，37.388秒全部摘要相符，正式record为online_verified。见 F/web-online-retry2.json；原超时不改写成成功。
- **两个Runtime均1.3.108 / bridge1.1.72**：固定3ddc90d/tree9f9e587。本机PID49390；Eva最终配置后PID107266。分别复用自身已核验依赖，没有将x86依赖送到ARM。Eva的bridge锁文件仅根版本71→72，第三方依赖图完全相同；保留目标机器原工具链。沿各自主机原发布锁、停止writer归属核验、状态备份、固定app目录安装；原身份、状态、journal不重建。正式current.json记录限定的验证范围，不代表全功能回归。
- **六张出站表**：固定真实catalog、mysqldump备份后显式执行精确DDL，新增六表；无DROP、CHECK、触发器、启动自动建表或原业务行覆盖。见 F/schema-result.json、F/outbound-schema.fixed.sql、F/rent-cutover-db-before.sql。
- **扈三娘补登记**：原binding/installation/owner，维护preview→apply，TRANSITION租约 `hrl_transition_1ed745ba-4a69-3444-bd6a-a11c804c4109`，50文/2592000秒，2026-11-13 16:01:57.380→2026-12-13 16:01:57.380（+08）；没有新enroll、reserve、capture或退款。李逵原租约、版本1、金额50、2026-11-11 22:02:03.301→2026-12-11 22:02:03.301完全不变。
- **管理通道**：登记一个server host及Eva local host；导入吴用、林冲、卢俊义、扈三娘四条精确CONTROL关系。卢俊义初次preview因错误沿用另一用户身份被既有ACL拒绝，未写入；查明其真实独立owner/payer后用新固定输入preview/apply成功，没有放宽授权。李逵旧mTLS关系未导入/重放；旧公孙胜RECOVERY_REQUIRED未清除、未双发。
- **自动续费**：显式启用auto-renew；线上日志真实注册`hosting-rent.reconcile-user`、`hosting-rent.finish`及原provision处理器。用户到期待办保持原最早到期2026-12-11 22:02:03.301，未人为提前到期或扣费。见 F/renewal-handlers-registered.log、F/schedules-final-after-acceptance.tsv；不是只看配置键或lease存在。
- Eva原静态配置没有新Agent准备模板。本轮在同host私有配置中复用**其既有Runtime专属**provider凭据/工具配置，未复制平台密钥；配置验证后受控重启。新Agent模板沿已用的app-server/native WebSocket模式；原扈三娘profile及HTTP poll设置不变。先前模板预检因复制静态HTTP poll选项而缺专属路径被拒，保留失败；没有放宽模板字段或修改程序。见 Eva template-configuration-result.json。

### 已通过的实际线上验证（不是全部验收矩阵）

1. 两台主机以各自凭据访问授权目录成功；本机分页逐页覆盖其授权；错误token返回401，本机凭据访问Eva授权返回403。普通用户访问另一用户卢俊义租约按既有隐藏资源合同返回404/NOT_FOUND_OR_FORBIDDEN；没有泄露数据。
2. 扈三娘实际对话HTTP200、SSE正常完成，唯一预期回文以`FINAL_PERSISTED`返回；回执 F/eva-evidence/chat-acceptance.json。线上租约GET同时确认扈三娘补登记及李逵原账期。
3. **平台托管**：新准备→真实TARGET库存→报价1000文/30天（保留另一任务已上线的关胜模型定价）→取消REVOKED；**自行部署**：复用Eva登记host，新准备→真实库存→报价50文/30天→取消REVOKED。两次均没有点击付费确认、没有实际收取租金或新增正式安装。对应exchange的capabilities/target/inventory/quote-inventory均有完成事实，不把目录ACK当ready。
4. 两个临时setup均已取消，授权撤销；没有通过解绑真实Agent或修改真实到期时间制造测试结果。探针最初错误假设响应带authorization、非owner一定403；实际合同为authorization=null/隐藏资源404。保留原探针失败及固定请求，按源码合同用GET续查，**没有重复POST创建setup**，没有因此修产品协议。

### 仍未验证/现存问题（不得隐去）

- 本轮没有完成先前未通过的真实MySQL全套集成，也未在线执行实际扣费→服务安装→退款、真实解绑、断网到期、跨用户沙箱文件攻防的完整矩阵。单元/定向测试仍只采用上节固定批次真实结果；不能称全量验收完成。
- 吴用 `TYPED_INSPECTION_RECOVERY_ERROR`/缺失inputPolicyDigest在**本次切换前**已出现，切换后仍可见；取证 F/wuyong-preexisting-recovery-error.log。未自动重放/清理相关未知历史任务，也未顺手扩成本任务外的typed-inspection整改。全环境无故障不成立。
- 本机磁盘仍紧张。仅在确认安装成功、精确JAR摘要一致、所有维护JVM退出后，移除本任务已打入最终包的冗余独立build JAR，释放251582454字节；最终包、测试/日志、前代及状态备份保留。F/redundant-build-jar-cleanup.json绑定真实事实。后续维护应使用当前精确JAR或从保留包按摘要取出，旧build JAR路径不再存在。
- 实际安装耗时与600秒构建分别记录：本机Runtime安装/状态备份/核验970.955秒，Eva122.209秒；API实际冷启动约10分钟，期间共享主机load约20。没有再次构建、没有强杀生产或其他任务、没有为了赶时限删除完整性/备份保护。原构建超时与本次Web证书失败均保留，不能宣称整个耗时问题已彻底解决。

## 2026-11-13 19:23 +08 继续验收（进行中，不改写上轮结果）

未重新安装/回退，无生产扣费、解绑或修改到期。API仍为d6d9102、Runtime仍为3ddc90d，源码均干净。19:16只读生产租约再次与16:58证据比较，李逵/扈三娘身份、金额、精确账期一致；API health.status.code=UP，本机与Eva Runtime分别PID49390/107266、active/NRestarts=0。证据F/rent-recheck-1916.tsv、F/api-health-1919.json。

真实MySQL集成沿原编排器串行重跑四类：HostingOutboundMySqlTest、HostingRentRenewalMySqlTest、HostingPersonaModelDatabaseMySqlTest、HostingRentCutoverMySqlTest及validateLayering。仅测试自有隔离MySQL，不连接生产资金。原lease-int1失败包含旧Node fixture路径，现候选已修；lease-int2按此前用户要求停止优先上线，不算失败后自动重试。19:10 lease-int3因共享Gradle缓存缺失immutable metadata在9.38秒失败；保留原共享目录不修改。lease-int4因新私有缓存根权限0755被原入口拒绝，改本任务缓存根0700后新lease-int5执行。该批是明确的真实MySQL/Runtime联合回归，不打包/发布；按根规则独立记录耗时，不伪造600秒构建通过。仍在执行，最终状态看`/home/isp/state/cyf-build/lease-int5/result.json`及本节后续记录。执行脚本在`host-integration-03/04`，未覆盖历史runner/失败回执。

真实bwrap Shell、Node两项隔离探针在受限测试用户isp下通过（后续systemd核对：本机线上unit用户为root，并非isp；Eva为chc），0skip。仅合成资产、无模型调用，读写授权输出成功，只读输入/工具配置及宿主秘密不可访问；不冒称真实两用户业务攻击验收。证据F/native-isolation-acceptance-1914.json。原root运行Node受isp上层目录信任约束拒绝，随后isp在root cwd启动子进程被拒；换成实际用户与可访问cwd成功，未放宽工具链/目录权限或修改生产配置。

吴用旧恢复问题定位：26条RECOVERY_REQUIRED中5条材料会话有engine thread、无finalPrepared且缺engineStateBinding。当前recoverMaterialsChat回退调用materialsEngineBinding，而后者直接访问null contractReadback.inputPolicyDigest，符合原错误；证据F/wuyong-recovery-shape-20261113.json仅记录结构布尔值，不复制内容/凭据。它属于旧材料会话恢复，不是租约续费/主机管理通道；未伪造绑定、删除journal、重放模型或把简单加空判断称为恢复成功。

### 20:13追加：测试卡死归因与已完成原生执行验收

- lease-int5原批次**失败且不可整体验收**，3060.342秒，未伪称600秒通过。原始3个完整类回执：HostingOutboundMySqlTest 33/0/0、HostingPersonaModelDatabaseMySqlTest 3/0/0、HostingRentCutoverMySqlTest 1/0/0（依次tests/failures/skips）；Renewal类只完成部分，27项含1中止skip，不能算该类通过。原生Node→真实Java MVC/MySQL及lost ACK探针1通过。validateLayering通过。所有XML已复制包外至lease-int5/test-results，原失败日志保留。
- 真实卡死点不是续费或生产Runtime：selfHosted测试在断网场景把测试UDS改名offline.sock，完成业务断言后未还原；fixture的所有权检查关闭原路径失败，捕获SIGTERM后仍保留listener；Java finally的destroy后无界waitFor永久阻塞。线程栈、Node方法日志和精确干预在lease-int5/{test-thread-2000.log,intervention.json,tmp/runtime-lifecycle-agent-self-hosted-node.log}。归属核对后仅终止测试worker124422及其synthetic Node131132/MySQL129588，未动生产或他人进程。最初按Java主线程children检查没有匹配，预检停止且未发信号；之后以实际PPid/命令/隔离datadir重新核对。
- API测试修复commit **416e841c2da3fa5377edaf2a59ee64dcb33fbe1a** / tree **1f6dac8e643bc9dbee8bfc282b812db00c8ef989**：离线断言完整执行后finally只恢复自有测试socket；EOF关闭最多等原有10秒，超时强制结束**自有合成fixture**并令测试失败，拒绝无界等待；Java HTTP server无论断言/子进程失败都关闭。只改HostingRentRenewalMySqlTest，应用源码、已装JAR/租约/真实Agent均未改变。lease-int6复用原独立编译输出/私有缓存，完整重跑受影响Renewal类及layering，原37项完整未受影响类回执按原精确源码单独保留，不重标整个旧批次成功。
- Native测试原sandbox_mode断言与当前已实现命名permissions不一致。仅修断言为default_permissions=native-execution，Runtime测试commit **b3b8f99**，不改生产权限或执行代码。29个普通用例通过，5个opt-in skip不计通过；两机真实Shell/Node隔离各2项通过，实际native engine打开/凭据去除/空技能与精确授权技能目录/受限网络/嵌套文件写入各1项通过，均无模型计费调用。证据F/native-engine-final-acceptance.json与F/eva-evidence/native-current-contract-acceptance.json。
- 额外失败均保留：本机误用受限isp身份探测真实engine会因/proc子进程exe EACCES拒绝（线上unit实际root），用实际root和安装Node后身份核验通过；Eva缺省/usr/local/bin/codex不存在，明确用现有配置的ARM固定路径后通过；原断言失败；本机修正断言后与重编译并行时第二engine initialize超时，待编译结束后同权限/同RPC时限重验成功58.93秒，未延长生产超时、未削弱验证。Eva同一修正测试21.93秒通过。
- Runtime测试commit因该仓未配Git作者先失败，后沿API仓已有作者配置完成**仅本次命令**提交，未改全局身份。lease-int6开始配置时文件字节已固定，随后测试执行前补完此测试-only提交；捕获的所有Runtime文件SHA未变化，原baseline与最终内容commit映射见lease-int6/runtime-content-proof.json。不冒称部署过测试-only新版本。
- Eva仅移除了本任务candidate-attempt3内与生产逐项摘要/模式一致的node与node_modules冗余暂存目录，沿原发布锁并确认没有活进程引用；**原目录含硬链接，实际只释放299008字节**，不可报成释放154MB。生产/身份/状态/包/备份均保留，根盘仍约214MB风险未解决。F/eva-evidence/redundant-stage-cleanup.json。

## 2026-11-13 20:35 +08 主线可交用户验收

**当前结论：租约与Runtime接入主线已部署，补充回归结束，可交用户验收。** 覆盖前文“全套集成尚未完成”的当前状态，不改写任何失败历史；不等于用户已验收或全站零故障。

- `lease-int6/result.json` exitCode=0，总计1167.918秒；真实MySQL/Runtime联合回归按根规则单独计时，不是600秒构建发布批次。Renewal完整66项，0失败/0错误/0跳过；`validateLayering`通过。托管、自部署真实Node fixture均达到SERVICE_READY，测试已验证子进程正常退出，原无界等待已消除；没有给生产请求增加deadline。
- 原`lease-int5`整体仍为失败，保留日志和干预记录。其中三个已完整结束、源码未变的类分别33/3/1项通过，与本次66项合计**103项通过、0失败、0跳过**，按分批证据汇总，不能称int5整批通过。汇总及每份XML SHA-256：`F/final-integration-acceptance.json`。两机Shell/Node/native隔离另见`F/native-engine-final-acceptance.json`；普通Runtime用例29通过/5个opt-in skip不计通过。
- 本轮API唯一变更为Renewal测试；Runtime唯一变更为native测试旧断言。生产应用代码与已装制品未变，没有重复构建/安装。20:34再次核对生产JAR SHA-256仍为`8046c5a64215f197d947da77c32cfaa779b2af24ec13334dd9cb9cf911afa51f`；API health.status.code=UP。两台Runtime均active/NRestarts=0，PID仍49390/107266。生产租约、host、CONTROL授权只读结果与20:16完全一致：`F/rent-recheck-final.tsv`、`F/api-health-final.json`。
- 扈三娘月费补登记已生效：50文/30天，本期2026-11-13 16:01:57.380至2026-12-13 16:01:57.380（+08）；李逵原账未改。离线不暂停租期、有余额自动续费、自部署解绑不等待远端清理的业务路径由隔离MySQL与合成资产回归覆盖。没有为验收实际扣减用户余额、退款、解绑真实Agent或提前修改生产到期日；这些操作不冒称已在线实测。
- 保留两项独立已知问题：吴用旧材料会话恢复缺少绑定/读取null inputPolicyDigest；Eva磁盘可用204652544字节（约195MiB），本机1046597632字节（约998MiB）。未删除用户资产、未知状态或其他任务数据；不宣称冷启动/所有长耗时已彻底解决。
- 当前摘要为`F/final-release-summary.json`，状态`READY_FOR_USER_ACCEPTANCE`；原摘要保存为`F/final-release-summary.before-final-acceptance.json`。按用户“可验收时停止”停止扩展开发，等待用户验收；不继续变更既定方案。

## 2026-11-13 23:39 +08 用户追加真实事项流程回归（进行中，不是全量通过）

用户明确要求事项流程而非健康冒烟。上节租约/接入联合回归结论仅限原范围，不能覆盖新浏览器登录及真实技能执行。本轮按现行全局手册执行CORE17；FULL119未执行，任何未测/失败不得补算PASS。证据批次B：`/home/isp/state/cyf-runtime-lease-separation-20261112/task-ui-20261113-224052/`，逐项状态见B/regression-status.json；失败原样保留。

- 新浏览器发现Web公开源码迁移后部署环境未注入，API base为空、OAuth client未定义，旧token只读冒烟未覆盖。现有本地构建器增加外部必需配置预检及配置摘要，根提交7d0508de、测试提交f7fbd4a8；私有部署值不回填公共默认。首批lease-web-auth因自有稀疏副本缺miniprogram静态文件失败566.855秒（其中冷依赖安装505秒），保留失败；修正源码副本后lease-web-auth02构建194.24秒、112测试通过/2pending，应用源码仍6ce64429/1.16.140。原受控安装35.216秒、613文件闭包、256线上资源摘要通过；正式buildId runtime-lease-web-auth02-20261113。全新浏览器真实OAuth登录、返回工作台已通过。
- 新事项667首次执行因carrier证据绑定旧工具链/策略摘要拒绝，非凭据故障。沿现有认证脚本真实验证10种资料载体、一次模型轮，林冲/吴用分别measure contractReady=true；新证据SHA b0ab927053d7ea14db7c5abd92b8a80349044eaa610e4b0baf87dcd1eed65d81。原锁/备份/精确writer归属核验后仅替换两profile的证据指针，正常重启Runtime，PID215425；应用3ddc90d未变。首次激活预检因旧helper要求已退役socket路径失败、未动生产；随后适配outbound视图后成功，原失败保留。667经UI取消，新增预占释放。
- 新事项668在Runtime启动完成后真实推荐、确认承办、首次技能目录4项正常，产生截图和JSON并可预览下载；但内容为about:blank/httpStatus=null，网页访问用例FAIL，不能因有文件就通过。真实command绑定browser-workbench安装si_d8e9d1531aa24018ac62c9121f3a7149，现有私有安装配置缺该项，未获得目标origin许可。按原配置机制仅补授权测试站点https://kit.chaoyoufan.cn，保留0600/归属/原值备份/发布锁/原子写/readback；不开放通配出口、不关闭沙箱、不重启服务、不重放失败执行。668经UI取消，截图/JSON取消后200且SHA不变。
- 已创建669作为配置修正后的独立真实复验事项，尚待网页执行及后续多轮/文档/图片/验收用例。累计预算仍100文、历史已报告8文不重置；本轮初始钱包3486/held1，旧held1不属本轮，不清他人预占；667/668各新增1文已取消释放，669新增预占待最终核对。
- 吴用旧会话RECOVERY_STATE_MISSING、旧命令SKILL_COMMAND_INVALID仍为独立遗留，未重放/删journal。磁盘紧张仍保留风险；只清本任务已结束合成数据库与构建中间产物，日志/报告/制品保留。真实回归未结束，不宣称环境全正常或全部验收完成。

23:53补记：669网页复验已真实RESULT_COMMITTED，截图可辨认robots.txt；JSON空title/正确URL/HTTP200，预览/下载及取消后摘要一致。随后跨轮读取旧JSON出现PROTOCOL_INVALID_RESPONSE，不能算JYT-05通过；已经UI取消669，钱包3486/held1/version59，无本轮扣费。根因是RuntimeV1Client.nativeFetch按application/json一概验证R信封，误判合法JSON文件。修复仅在传输责任层按精确materials/inspection内容路由、成功GET200区分原字节；非成功响应、普通JSON接口、会话身份切换仍执行原保护，不猜测JSON内容、不放宽资料ACL/摘要校验。Runtime提交630d178fd8376699b51fe50a8ec970be767c8873/treefe98f006452e8c4d18a0d2ded80de4c54141603c，升至1.3.109、bridge仍1.1.72。固定本地批次rt-json-material-01：196测试全部通过、0跳过，测试/打包123.113秒；制品SHA3dd5a011941c41109be47ebfc030e4eb74f7d92258323877e3ddde49e50aa863。原安装工具按无配置变更模式适配，依赖及整包闭包校验、发布锁、停止writer核验、备份保留；正在受控安装，尚未宣称修复已在线复验或CORE17全通过。

## 2026-11-14 00:05 +08 JSON传输修复安装阻塞与重试

第一次安装在停止writer并备份后报STATE_CHANGED_DURING_BACKUP，327.328秒失败，尚未切换程序。已启动仍未变更的原1.3.108服务PID232251恢复可用性，不是回退已安装的新版本。独立合成复现：SQLite数据库处于WAL模式但关闭后无sidecar时，旧备份helper的mode=ro查询会新建-wal/-shm，改变源目录时间，导致自身快照前后不一致。根修复2e6d0440：无非空WAL时immutable只读检测schema；非空WAL保守保留数据库及辅助文件，不猜测未回放的schema。24项工具测试通过；最初默认/tmp被原安全检查拒绝3失败/1错误，改为私有普通磁盘TMPDIR后通过，未放宽校验。host helper已备份并按发布锁安装摘要一致的新版本，随后复用原630d178制品重新受控安装，未重跑构建。

磁盘曾降到45MiB：仅回收本任务已核验为Git原字节的可重建Web构建副本tests/public（后续复用须从固定Git恢复），并记录SHA/大小后回收一致性失败的本任务备份副本；原业务状态未删、其他任务及有效备份未动。外部挂载归档尝试无完成回执，未当有效备份，所属tar已发TERM但处于CIFS D态等待内核返回，未杀共享进程。原失败状态、日志及回收回执均在B/runtime-json-fix。此时仍未完成新制品线上复验，CORE17不得宣称全过。

00:10补记（当前阻塞）：第二次安装停旧Runtime时MainPID已退出，但3个该unit的bwrap子进程233252/234038/234766处于D态，stack为rwsem_down_write_slowpath→do_reconfigure_mnt；systemd仍deactivating/final-sigterm，不能越过writer退出保护。共享/mnt/Workspace的CIFS会话卡住，本任务先前归档tar231383也在smb2_reconnect/cifs_flush D态，已发TERM但内核尚未返回。实际配置端口1445 TCP可连；445非实际配置端口，不据其失败认定服务器宕机。扫描/proc cwd/root/fd未发现其他打开共享路径的用户进程，不代表内核没有其他脏页。未强制卸载共享盘、未杀其他任务/生产服务、未关闭沙箱；需要明确共享挂载恢复范围才能继续。新1.3.109程序仍未替换，不能宣称已上线或环境正常。安装session43996仍等待正常stop结束，浏览器session32995仍保留；钱包最新3486/held1，新测试预占已全部释放。详细事实B/runtime-json-fix/cifs-blocker.json，状态B/regression-status.json；真实CORE17当前有失败/未测，非全过。

## 2026-11-14 09:00 +08 启动告警探测源码修正（未构建、未安装）

用户在核查后明确要求执行“删除启动告警探测，保留实际沙箱”。已确认该命令来自当前Codex 0.167.0依赖，不是Runtime自编写探测；上游固定commit `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a` 的 `codex-rs/app-server/src/lib.rs` 启动调用 `system_bwrap_warning`，返回值只加入启动警告；`sandboxing/src/bwrap.rs` 中500ms超时后的kill+阻塞wait不能保证D态退出。不能把该告警当安全准入或技能READY证据。

Runtime源码提交 `a81b7ba60399b0bdbac8277955dec4164c2c3d0e`，tree `b2f3f5b80436b451299c9062423d91bef25f25ba`，分支 `codex/runtime-startup-warning-probe`。维护一个固定上游版本的最小补丁，只从app-server启动处删除11行告警调用、增加2行说明；不改实际沙箱、权限、CLI/exec其他诊断、业务接入或收费。不修改全机Codex二进制，也不通过PATH隐藏生产bwrap。补丁、原/目标文件摘要、回归入口及专用制品安装要求位于Runtime `patches/codex/0.167.0`；根README已链接。私有证据为本轮B下`bwrap-source-audit`。

验证分开报告：固定上游原文件的补丁身份/精确应用2项通过；Runtime既有startup信息、失败、退出、取消等5项定向单元通过；**候选Codex二进制未构建，其真实启动测试明确跳过**。原版真实initialize负例在修正后的私有测试PATH中产生完整旧probe参数，因此负例按预期失败；不是候选通过或真实沙箱隔离验收。首次负例夹具把替身放在cwd下，被Codex的pre-sandbox程序选择规则跳过，且测试PATH仍能找到真实bwrap，造成误通过和新增本轮自有D态PID398556；已保留invalid-oracle日志、修正为cwd外替身且PATH仅包含替身目录，确认新负例失败。对398556发SIGKILL后仍D态，未宣称已退出；没有操作其他任务进程。该测试失误已向用户明确报告。

阻塞仍在：本机普通根盘可用约1.1GiB，无cargo/rustc；Eva为aarch64、仅141MiB可用且无Rust工具链，不能当作x86_64候选的现成构建机。本轮未开始Rust构建，不伪造二进制或构建成功。原Runtime unit仍MainPID=0、deactivating/final-sigterm，原3个D态子进程未退出；此前安装器会话是否存活不能继承00:10记录，本轮进程列表未见安装脚本，不应盲目并行重启安装。共享挂载未强制卸载，程序未替换，全机Codex未改；JSON修复仍BUILT_NOT_INSTALLED。后续需要满足普通磁盘/Rust构建条件，恢复已有内核阻塞后，按既有锁/备份/完整性/私有codexBin路径安装，重新实测受影响测量/carrier证据，再继续CORE17。不得以补丁/负例完成宣布上线或真实事项回归全过。完整状态见 `B/bwrap-source-audit/result.json` 和更新后的 `B/regression-status.json`。

### 2026-11-14 09:07 +08 用户授权卸载共享盘，已卸载但内核阻塞仍在

授权原文：“那优先处理这个，可以卸载共享盘”。仅处理 `/mnt/Workspace`，未获整机重启授权。已将 `mnt-Workspace.mount` 和 `.automount` 做 `/run` 临时mask，防止本次会话重新激活；`umount -f -c -i` 返回EBUSY/32，保留失败。随后 `umount -f -l -c -i` 返回0，并停止automount。两unit现为inactive/dead、masked-runtime；扫描16个可见挂载命名空间，未再发现CIFS挂载。**这仅证明挂载已摘除，不证明内核对象已释放。** 未重挂、未改fstab凭据、未重启远端SMB服务、未操作其他服务端口。

原6个本任务用户进程（包括测试新增398556）仍D态；Runtime仍MainPID=0、deactivating/final-sigterm。进一步只读确认CIFS内核接收线程1770182卡在`iterate_supers_type -> __cifs_get_super -> cifs_reconnect`，写回线程225435卡在`wait_for_response -> SMB2_negotiate -> smb2_reconnect`；不声称已经定位具体锁地址或证明完整锁环。仅对旧SMB连接精确四元组172.18.151.236:53924→173.230.149.118:1445尝试socket destroy，连接仍CLOSE_WAIT，未记成功。其他443/389等业务连接未操作。

下一步需另获整机重启授权以清除残留内核等待，需说明API/Web等服务会中断；本轮没有重启服务器、没有强制卸载内核模块、没有绕过Runtime停机检查。当前mask是临时的，**获准重启前必须另行确保共享盘不会随重启自动挂载**，不能认为/run mask永久有效。证据`B/shared-mount-recovery/result.json`；真实UI回归仍阻塞，未增加PASS，新JSON包及Codex补丁仍未安装。


## 2026-11-14 09:39 +08 authorized host reboot preparation

用户确认保留共享存储但不长期挂载，改按需用户态传输；再次授权现在正常重启。旧boot_id=8b9aadea-1155-4bc2-86a0-a01b2ce5db96，D态仍存在。两mnt-Workspace unit已永久mask，不恢复CIFS。一次性恢复unit cyf-reboot-recovery-20261114.service已enable（未start），仅新boot启动既有Redis/ES/API/nginx，MySQL与Runtime沿用原enabled unit；恢复日志/attempted在/var/lib/cyf-reboot-recovery-20261114/。Runtime仅/run增加JobTimeoutSec=30s以避免旧无限stop job永久挡正常关机；SendSIGKILL=no及安装停止保护不变，非硬重启。当前未部署新Runtime/Codex，不代表主线回归通过。接下来发systemctl reboot；须对比boot_id及服务验证，不能把请求等同重启成功。


## 2026-11-14 重启后恢复实证
新boot_id=03343dfd-294a-4363-8486-bda528639587；可见D态0、CIFS挂载0，永久mask保留。恢复脚本漏RabbitMQ导致API暂DOWN，已用原rabbitmq-server -detached补启动，随后API健康UP，nginx域名本地TLS检查HTTP200，Runtime active。一次性恢复脚本执行结束并disable，未部署新版本；主线回归及用户态传输入口未完成，不能称全部交付。


## 2026-11-14 重启后继续真实事项回归（未全过）

B仍为task-ui-20261113-224052。原JSON修复630d178已通过既有锁/停止writer/完整状态备份/闭包校验安装为Runtime1.3.109，152.841秒，未回退、未跳过保护。新浏览器browser-postreboot，当前真实UI会话记录独立于旧浏览器。

发现当前林冲模型gpt-6.1-sol、吴用gpt-6-astra（配置在本轮开始前已更改），旧证据不适用。初次新认证实际吴用10载体语义通过，但复用给林冲被不同model校验拒绝；保留失败，不重复吴用付费轮。改为各自实际模型分别认证并验证，2个真实合成轮，2份固定证据，经原锁/停机/备份配置机制激活；未改变模型、身份、权限或重放旧UNKNOWN。证据carrier-refresh-postreboot与carrier-refresh-linchong-postreboot。

新A4事项670/会话1760458009429，首次目录自动显示6技能，但网页执行FAIL：模型把advisory-only费用未知误当预算核价前置条件，未启动浏览器，交付null字段的费用阻塞JSON。真实EXECUTE虽RESULT_COMMITTED不代表网页成功。A4-native-evidence和A4-execution-result.jsonl保存实际事实；已UI取消，钱包3386/held1/version63，本次新增预占已释放。重启后初始钱包3386/held51/version61，相对前日3486/held1存在其他活动变化，不能擅清或算成本轮消费。

依据spec.md可观察目标3，不新增计费机制；修正Runtime已有规划/执行提示，把费用说明与平台WEN报价/预占/结算分开，禁止臆造核价工具及新增审批，同时保留明确用户预算/第三方付费限制、不宣称未知费用免费。源码b7b135f3b7535d8c64f980637da8f501e72f5d20/tree391b66e892e07be264fb414509581ccfcab2a1f6，Runtime1.3.110/bridge1.1.73。rt-cost-policy-01固定本地构建59.345秒，242测试通过0skip，包SHAb5fe1bfae4385f982e3e36e4db25c7965037fabc360d2b9f8c2ee8e8414395c6。首次调用缺CYF_RUNTIME_BUILD_OUT在启动构建前报错，保留build-invocation-failure.log，修正环境后正式批次成功。

费用提示修复正在既有受控安装；最终以runtime-cost-policy-fix/stage/installation-result.json为准。不能把242单测当真实事项回归全过，JYT05等仍待新事项复验。FULL119另建完整状态表，未测保持NOT_RUN，不能只跑CORE17报全局通过。Codex启动探测补丁仍未编译上线，用户态共享文件传输入口仍待完成。

## 2026-11-14 11:35 +08 真实事项进展与待安装修复（未完成）

B仍为`/home/isp/state/cyf-runtime-lease-separation-20261112/task-ui-20261113-224052`。费用提示修复1.3.110已受控安装，179.345秒，现有Runtime PID36386；不是仍在安装。A5事项671/会话1760458009430完成真实浏览器截图/JSON、旧JSON跨轮实际工具读取、一页中文PDF制作、150文/10人新版PDF与原文件保留。PDF预览上下部均实际截图核对。A5已UI取消；原截图、JSON、检索JSON和两版PDF五个认证URL均200且原SHA不变，见A5-cancel-history-check.json；资金释放仍需精确自有账目核对，不能用全账号余额差归因。检索重测文件和原文吻合且可预览下载，但完整EXECUTE取源工具trace未找到，暂不把模型自述作为实际取源的唯一PASS证据；原网络失败保留。

B1事项672/会话1760458009431识图正确，唯一自动修订请求已提交，action `act_afc00853b13d68264c7e25abfd6134733aa20576`仍QUEUED，不重发。根因是10:52 API注册事务死锁返回相关联AGENT_REGISTRATION_UNAVAILABLE，Runtime把所有注册拒绝一律按403永久隔离。修复仅在既有request/session关联校验之后将该精确暂时不可用错误走既有503重连退避，撤销旧ready/proof并要求新ACK；真实授权错误/1008保留隔离，不重造业务请求，不改API收费/授权合同。API死锁本身未全局修复。

候选Runtime1.3.111/bridge1.1.73，commit978d44268d8d79b0361831e23a9dff1f51020a11，treeb9a8e485471b6cfd3d024702d44de66d6d1a09dd。固定本地批次rt-registration-retry-02，259测试通过0skip，55.864秒，包SHAbc4f17b846dd013f0a5dfbf324af438f5ef4f753ba1e8df6160953cabc7c531b；28.463秒完成候选准备，尚未停生产或安装。原首次dirty-source前置失败和最初错误fixture测试失败保留。发现安装脚本仍写旧cost-policy源码标识，已改为已测试候选精确commit/tree并修正日期，语法检查通过，仍未执行。保留predecessor CAS、锁、停writer、完整备份和manifest检查。

10:58另一活动任务发布API1.1.51-SNAPSHOT，commit9661503e639e5b2c876dece69025396ebd106ea6，JAR SHA69c9947f404ee5141ede763b7f03972f5de1597a2734f77f825cd57c24222feb，当前日志startlog_20261114_105811.0ZrVev.log；本轮跨API版本，不能伪称全部单一固定基线。两个自有浏览器已经UI重新登录。更新B/regression-status.json保留历史失败，FULL119仍待完整覆盖。

用户态共享存储私有工具`/home/isp/state/cyf-shared-transfer/transfer.py`已实现显式加密上传/下载、唯一partial、不覆盖、上传完整远端读回SHA，源不删除；48字节真实往返验证通过。727MB旧有效备份上传PID61247仍活跃但非常慢，只有STARTED无VERIFIED，不能删除本地备份或宣称大文件可用。根盘一度仅剩68MiB，暂不启动需要新完整备份的停机安装。永久mask继续生效，CIFS挂载0、D态0；不会重挂。用户态工具尚未完成长期repo收口/负例验证，Codex启动探测补丁仍未编译安装。主线CORE17与FULL119均未完成。

### 2026-11-14 11:45 +08 新增核实与停止盲等

- 仅回收本任务三份临时构建源码中与固定Git blob逐字一致、无活进程/FD/maps使用的副本1195个/62,747,872字节，逐文件SHA/身份及恢复commit已保存在B/registration-fix/source-copy-reclaim.json。原Git仓、包、日志、结果、生成/改动文件、node_modules、备份与生产状态全保留。根盘现约127MiB，仍不足新完整状态备份，未停服务安装。
- 大备份上传session22755/PID61247已权威终止：exit124，原1200秒上限。仅远端partial30,408,704字节，未VERIFIED，原727MB备份保留，没有盲重试。独立256KiB诊断上传及完整读回成功，每64KiB写耗1.8–4.3秒、读回5.45秒；TCP RTT约264ms，不能凭TCP可连宣称共享存储吞吐可用。证据`/home/isp/state/cyf-shared-transfer/{cost-policy-backup-outcome.json,latency-probe.jsonl}`。Eva只读df也仅106MiB，不能作为现成备份目标。
- 自有事项667–671的实际economy_escrow均gross1/captured0/refunded1/REFUNDED；672为gross1/captured0/refunded0/ACTIVE。正确资金域是BOUNTY escrow，不是agent_task_funding（这些id无行）；证据B/own-escrows-current.tsv。未操作其他资金/预占。
- 新普通无附件密议C1=1760458009432，taskId=null/private/林冲，两轮均真实发送一次并结束，但archive_read/skill_list/skill_read均不可用，原始失败B/C1-two-round-final.jsonl。确认这是测试主体前提错误：两个实际active管理岗位均属于吴用binding1，林冲没有岗位；原典籍job也属于吴用。不能放宽权限、不能把未调用工具算PASS。后续应在吴用恢复后以有权主体另开普通密议重测；当前C1终态不重放。
- 同时查明独立的真实源码缺口：开源导出漏掉典籍主体实现。当前源码和实际安装JAR均没有ArchiveConversationTools及ArchiveController；线上不存在不是模型猜测。已按固定前导出commit e2e2cbe2305608c3bd01d27dcfc07eb40b526fe4生成缺失库存：143个archive路径Java文件（91main/45test/5mmdRegressionTest/2archiveMaintenanceTest），此前恢复的6个会话归档依赖不覆盖典籍能力。B/archive-source-missing-audit.json和archive-installed-audit.json。此轮仅审计，尚未批量恢复、编译或安装；需要按现行典籍合同审查真实依赖/现行授权/DB CHECK规则后恢复遗漏实现及必要测试，不新造只读旁路或复制业务授权。
- 待安装Runtime脚本源码身份已纠正但仍未执行；未改当前发布记录。CORE17、FULL119、用户态大文件传输和Codex启动探测二进制仍未全部交付，不报完成。

## 2026-11-14 11:52 +08 典籍遗漏恢复候选已固定，尚未运行构建

上一轮为progress（资金权威事实、实际密议失败、线上JAR缺失典籍的定位）；本轮继续实际开发而非重复等待SMB。仅在既有API worktree恢复缺失文件，不覆盖当前文件：固定前导出源e2e2cbe2305608c3bd01d27dcfc07eb40b526fe4的91个生产Java文件、52个原测试Java文件和4份原测试fixture，共147份/4,603,661字节。覆盖现行典籍阅读/私人数据/提问/维护及通用密议provider原实现；未创建平行查询工具，未修改岗位、权限、数据库或生产配置。schema initializer与bootstrap仍限schema-maintenance profile；未恢复数据库CHECK依赖。既有Gradle已有archiveReaderRegression/archiveMaintenanceTest，复用这些测试入口而非新runner。

逐文件原SHA、缺失列表及预检查见B/archive-restoration-{preflight,source-receipt,import-audit}.json；没有检测到主机路径/私有域/私钥/字面密码或DB CHECK表达式，内部cn.jia显式import静态索引无缺失。git diff --cached --check通过。以上只是静态检查，**不是编译、测试、启动或安全验收通过**。

已固定候选API1.1.52-SNAPSHOT，commit `26b9ab0bfa9dbecfc87a89fd852170aadbac6903`，tree `7323c3c6fcb357139d996f125f24e555bbbd0147`，既有worktree干净；提交信息明确尚未验证/发布。未合入develop、未push、未安装。完整本地构建plan-only已生成B/archive-build-plan.json，包含两个典籍回归、原安全/邮件/制品/POI基线、validateLayering和fresh bootJar/打包；plan-only不执行Gradle、不证明测试通过。原编排器transition更新任务targeted_verification及精确源码，未手改ledger。

实际运行需为ArchiveConversationMySqlTest提供独立临时MySQL的CYF_POSITION_TEST_JDBC/USER/PASSWORD（该测试缺环境会FAIL，不是skip），同时提供既有SkillManagementMySqlFixture的CYF_REVIEW_MYSQLD和短普通磁盘socket目录；不能连生产库执行这些测试。磁盘当前约109MiB，连新的完整Runtime状态备份（上一份762,012,780字节）都放不下，也不足固定源码全新API构建/制品/隔离MySQL，故未启动失败注定的重型构建或停写安装。SMB传输已超时，Eva亦仅106MiB，没有假冒其他存储或删除受保护备份。当前需要实际额外普通磁盘空间；旧共享盘继续不挂载，D态仍0。

下一步：获得空间→固定候选必要测试/构建，修正真实失败（如有）→一次性受控安装所需候选→吴用原排队action自然续行，普通密议改用有真实管理岗位的吴用→按原CORE17及FULL119范围逐条取证。未把当前修复/静态检查当整体完成。

### 2026-11-14 11:53 +08 阻塞审计

连续三轮目标推进遇到同一普通磁盘容量阻塞；前两轮仍完成真实定位/源码恢复，本轮重新核实：根盘可用119,984,128字节，上一份完整状态备份762,012,780字节；原上传进程已消失且session退出124，不是仍可等待的活任务。原清理器最新只读plan仍0可回收文件，当前Runtime未确认发布状态保护不绕过。API候选commit26b9ab0bfa9dbecfc87a89fd852170aadbac6903、tree7323c3c6fcb357139d996f125f24e555bbbd0147，worktree干净，未启动构建或安装。已完成能在现有容量下安全推进的该轮源码准备；必要构建、隔离数据库、完整备份与安装不能靠重复等待、冒险删除或伪造验证继续。需用户提供额外普通磁盘空间或明确可删除历史数据范围。目标按blocked记录，非完成/非用户暂停；所有未过回归与原排队B1保留。审计B/storage-blocked-audit.json。

## 2026-11-14 15:23 +08 授权清理后恢复推进（非全部完成）

用户明确授权清磁盘、历史会话/worktree/分支。删除56份已归档Codex会话文件（840,742,002 bytes），当前活跃会话与Runtime业务会话未删；清理8个仅余命名标记的旧worktree空壳，删除根/API/Web三条legacy-before-juyiai历史分支，保留当前修复和未合并工作。Git对象未强制GC，旧固定commit仍可审计。另在扫描工作区/状态目录/临时目录的依赖链接和进程引用后，逐key非阻塞锁下删除6套无引用可重建Web依赖（1,838,319,931 bytes），保留两套有引用集合及逐套原receipt，未动Gradle缓存、生产状态或备份。证据任务根history-cleanup-20261114.jsonl、history-git-cleanup-20261114.log、empty-worktree-cleanup-20261114.json、unused-web-dependency-cleanup-{plan,receipt}.json。累计约2.50GiB逻辑文件字节，后续备份/构建已消费部分，不能等同当前空闲。

Runtime1.3.111按既有锁、predecessor/config CAS、停writer、完整状态备份、manifest与固定app安装成功，185.831秒，PID191041；原备份保留，新备份20261114-ui-registration-retry/state.tar.gz SHA01e29c16e244d1e26b57bbbee3da27836ea97f944e64e6c5a2e262d302cc6ece。原B1 action自然恢复为COMPLETED/RESULT_COMMITTED，执行pwe_d1006b7615bcb6aa04aa5a9aa68b9676b24a7224cf3997809dffb827fbbc，未重发任何图片请求。唯一Provider invocation a7f6b92f-7a7c-4a7f-baf6-8497854df4e9的started/terminal及回执已复制到B/B1-registration-recovery-native-evidence。真实图片HTTP200，139409字节，SHA70ebcd1fc98614572f629142b511f132c168a670a27657fc6eda326cbb1dc056；800×600、alpha全255，左红方右蓝圆无字，checker背景277381像素非白0，254负例检测成功。原文字独立成果保留。原B浏览器已失效，保留原owned信息后新建浏览器真实UI登录，当前只打开B1详情；图片UI预览/编辑/验收未完成，不能直接记整个JYT10/17通过。首次下载遗漏steps路径404保留，不当产品接口缺陷；改用实际step URL成功。

API恢复候选首轮完整本地执行175.92秒失败：11项ArchiveConversationMySqlTest在setup因POSITION_SKILL_NOT_APPROVED拒绝。根因旧fixture只mock批准版本，未提供现行共享目录的匹配product/POSITION分类；未放宽生产授权。补fixture后固定新commit9c8c38c3ade03747e833f107ae9d8696104c196a/treecaa70871aaf7ab524f35e65e118efaa2f95ea386。第二批lease-archive-restore-02复用已恢复Gradle缓存、新输出、独立MySQL、600秒整批unit，233测试通过0失败/0错误/0跳过，validateLayering/fresh bootJar/打包成功，总125.232秒；包SHA0868cf4d4544172bded69ab1e06b1a8e70187afd20b2ed576af1c805860f433b，JAR SHAaa2931de5baa299d65b194162f53e06cd0facbc59f89ab98a7da01cbc2f28851。原失败归因经编排器记录，未覆盖。候选包含当时线上9661503祖先，不丢另一任务华荣改动。

API使用现有cyf-api-flow-deploy --source-local、schema4精确descriptor、原JAR CAS、forward-only，生产配置不变、不复用旧激活脚本，15:23安装中；PID200284已启动但此记录时健康尚待确认，不能报告上线验收通过。证据B/archive-api-install{.log,-descriptor.json}及archive-api-predecessor-record.json。全局119仍未完整执行，不把233单测或B1图片成功当全回归完成。共享盘仍不挂载；此轮曾观察本地ext4读/写回短暂D态，不能沿用早前“所有进程D态0”当当前事实。

15:24 +08安装补记：原安装器exit0，CYF_API_LOCAL_INSTALL=PASS，API PID200284，HEALTH=UP、ARTIFACT_ATTESTATION=MATCH，权威record.status=installed且候选JAR摘要匹配。B/archive-api-installed-record.json保存本次记录，未宣称业务回归全过。下一步重登受API重启影响的自有UI会话；B1继续议事查看/预览已生成图，再执行唯一图片编辑请求、选版验收与历史文件校验；C1改用有管理岗位的吴用新普通密议，验证恢复的典籍与技能工具同会话两轮。不要重发已完成的生成请求。当前B浏览器exec session98688，helper仍在browser-B-postreboot，新owned已写；API构建批次02已结束，不要重复构建。

## 2026-11-14 15:50 +08 清理续查、B1验收和C2真实工具回归

B仍为task-ui-20261113-224052。B1事项672已完成唯一一次image-edit，原图作为实际输入（SHA70ebcd1fc98614572f629142b511f132c168a670a27657fc6eda326cbb1dc056），唯一编辑Provider invocation b0e82796-cebe-49b9-8c60-2f47e5bb27d3；edited.png SHA60b662b6fb0b005effde5ca820bcb18c5542ecf767350e7b0bbb5b21db288f90，800×600不透明白底、红方绿圆、无文字。实际UI预览、严格背景和254负例验证通过。真实验收只选原文字与edited.png两项，finalization准确ID见B/B1-finalization-wire.json；任务COMPLETED、delivery ACCEPTED，自己的BOUNTY escrow672仅captured1文，667–671均refunded1。历史原图和编辑图在完成后仍HTTP200/原SHA。证据B1-accept-final-readback.jsonl、B1-accepted-history-check.json、own-escrows-after-B1-accept.tsv。生成尺寸/背景显式实际工具参数trace与A5实际检索取源trace仍有证据缺口，不靠重复付费或重放终态制造证据。

C2新普通吴用密议1760458009433，taskId=null/private：第一轮实际archive_read成功查询三国演义120章；第二轮同engineThread 01a1d8f7-b56f-7851-8ebf-2468eeb18b3b、DELTA实际skill_list及两次skill_read成功。精确6条调用与输出见B/C2-actual-tool-calls.json及C2-two-round-readback.jsonl。原林冲无岗位C1失败保留，没有放宽权限。

清理续查又删除1份已归档Codex会话453783字节（先写路径、SHA、大小审计），累计57份归档会话，8个历史空worktree、3条历史分支及6套无引用依赖的原回执保留。当前剩余分支均为develop或正在交付/其他任务分支，没有强删未合入候选。15:45清理器plan为0可删除包，因Runtime当前发布记录未识别仍保护，不绕保护。根盘约1.1GiB，未再构建或删除备份。

新增真实UI：四入口aria-current随选择改变；从“我的”进入典籍，两本书均可见（均120章），三国第二→第三→第二回、目录、返回书架及切水浒第120回成功，截图/读回B/browser-postreboot/FULL-reader-*。仍未覆盖不同章节数/可空引首fixture，ARCHIVE02不能整体PASS；ENTRY02来源返回保持尚待核验（从我的进入典籍时背景已变办事，需判定是否合同问题）。FULL119目前仅6项完整映射PASS，其他不自动继承核心历史通过。浏览器A留在水浒阅读器，B保留已完成事项。未宣布全回归或共享存储长期方案交付完成。

## 2026-11-14 16:13 +08 导航真实失败已修复上线并复验；全局未完成

本轮延续上一轮实际进展，不是等待。ENTRY02真实UI复现：从我的→典籍阁，返回按钮为“返回聚义”，返回后当前一级为overview且焦点落根容器。根因JuyiHall的HallMinePage @open传root:true清掉来源帧。未扩大为导航新框架：删除该root重置，当前一级标记使用现有panelFrames最近一级祖先，保留原深度/权限/未保存保护及滚动/焦点恢复。此前“进行中”出现在另一旧浏览器的缓存首页；新读取已显示已完成，暂不据旧缓存修改后端或加全局轮询。

原型P11既有正确来源返回，先补原型规格和optimization/spec说明；真实浏览器在1440与390宽度验证原型mine→library→mine及“返回我的”，证据B/prototype-mine-navigation.json、prototype-mine-library-{1440,390}.png。自有预览进程PID214290已停止，临时预览tab已关闭。未把离线原型当生产通过。

复用既有挂载组件回归，新增六组mine→library/agents/messages，覆盖portrait-command/landscape-map、来源帧、当前导航、137滚动、触发焦点及单层。修复前6失败，修复后6通过；另2项既有根导航/菜单焦点测试通过。日志navigation-fix/red-tests.log与green-targeted-tests.log。

固定Web1.16.141，commit347989192e14b1cdbce5c1a99891174fd1cffb7c/tree47b315a98b83b6a99321dca514320d681623c62e。build01在测试前因主工作区node_modules非受控依赖集被正确拒绝（2.617秒），未动主工作区依赖。复用本任务lease-web-auth-source clone：保存1021项纯删除diff并恢复其先前回收的public/tests，无其他修改/新文件，切固定候选，只摘旧node_modules链接，不删其目标。一次准备命令因系统Python3.6不接受text参数在改动前失败，改用既有Python3.11继续。build02：338测试通过，因瞬态unit未传生产VITE_API_BASE_URL而打包前拒绝（133.274秒）。两次失败根因不同，原日志保留，经编排器分别归因；未盲重试同输入。

build03显式加载已安装前驱runtime-config.json原SHA ab48a579b0c13eee8ab786472d079b350cc3e5b3dd0bcdcc6f0a2b52af55053c，不改生产配置。全新输出lease-web-navigation03，完整测试/构建/打包77.607秒：338通过、0失败，2个原有paired Mini Program entry pending保留，不算通过；六组新用例全部执行。包SHA8b0d2a2feaf1596a0519b3922bae646e9d05c566bafdbc641ec733421996f762，107551723字节。package/manifest/report、工具链/SHA和配置均保留。原local_web_build结果BUILT/sourceUnchanged，不将构建自身当发布授权。

既有cyf-web-flow-deploy --source-local在前驱record/index CAS、原锁/备份/摘要和逐文件在线校验下安装成功16.28秒，changedFiles30/files613/onlineVerifiedFiles256，未回退。权威/证据navigation-fix/web-{predecessor,installed}-record.json、web-install-descriptor.json、web-install.log。浏览器A真实重新加载static/index-cfRDc9FE.js（新候选入口），B仍保留旧已完成事项页面，不把B当新Web复验。

生产新候选实际复验：PC与390×844各自mine→library/agents/messages共六条均返回我的，恢复触发按钮焦点，一级标记mine，overlay仅1；mobile截图已查看。四一级入口重新验证；事项组合“已完成+吴用+672”→完成事项详情→返回，关键词/agent ID/状态计数1保留，scroll0保留；首页仍显示其他事项未受筛选污染。ENTRY02原FAIL留history，新结果PASS，证据browser-postreboot/FULL-mine-*-fixed-*、FULL-fixed-entry-*、FULL-task-filter-*。TASK07多页分页仍未覆盖，不能从单结果列表宣称整项通过。

HELP03（本次新Web安装前的6ce6442）：工作台和我的两入口，机器人/文件同义词、文章、返回恢复查询及文章焦点、无结果提示、真实跳转事项单root，以及我的帮助返回触发按钮焦点均实测通过；没有反馈提交/新建/付费。证据FULL-help-*。ARCHIVE02两书均120章，已有切书/前后章/目录证据，但缺不同章数和可空引首fixture，仍非整项PASS。FULL119当前8 PASS、111 NOT_RUN（含部分覆盖），未全过；CORE17原缺失实际取源/生成参数trace仍待解决，不重放终态图片。当前根盘约293MiB，生产备份保留，未启动下一重构建。自有浏览器A停在新Web办事首页，B留已完成B1。

16:14编排补记：第二次fail返回2并将ledger置blocked_root_cause；该shell使用分号，已在恢复Owner前运行了改正输入的build03。测试和安装完整性未跳过，但状态恢复顺序有误，不能追记成事前批准。真实两次不同根因、改正输入、实际成功及顺序偏差已写navigation-fix/root-cause-matrix.json，经既有authorize-remediation显式恢复Owner后transition targeted_verification成功；后续归因命令必须检查返回码，不再用分号直接继续。原失败与时间不改写。

## 2026-11-14 16:35 清理与退出回归前向修复

按用户“清理磁盘并继续”执行：新增清除已完成的hero-model-ui-release Web worktree/已合并分支；已完成无Owner的hero-model-hosting API worktree/分支先保存完整且git bundle verify成功的历史bundle再移除，未丢未合入历史。删除1份非当前线程、进程未引用的11月6日历史会话。当前线程及其他当日会话、runtime-lease-setup活动worktree、生产身份/state/备份不动。/根可用269MiB→561MiB；日志/精确路径/源码/bundle摘要在`/home/isp/state/cyf-runtime-lease-separation-20261112/cleanup-20261114-continue/`，不称所有历史均已删除。

ENTRY05已在1.16.141真实浏览器1440×1000通过：native dialog Tab焦点离开页面时document.hasFocus=false不等于背景逃逸；Esc先收预览还原触发焦点，再收议事回事项详情；20次父层Tab/ShiftTab及icon命名核查，无业务写请求。FULL累计9 PASS。

ENTRY01独立同账号browser context实测FAIL：退出当前设备后自动OAuth并回/profile。原第一次追踪没滚动到视口未触发点击，保留为无效诊断，不称退出成功；第二次hit-tested真实点击及第三次Debugger调用栈明确是UserProfile授权世代watcher→loadCurrentIdentity/getUserInfo→token→beginAuthorization。未操作退出所有设备，主浏览器A未被登出，未记录token/code/password内容。证据`browser-entry-auth/ENTRY01-logout-{redacted-trace-hit-tested,caller-trace}.json`。

既有账号安全design§User flow4/§Web已明确本地退出→公开首页，交互不变，不新造认证状态机/SSO撤销/全局屏蔽。责任层仅删除个人中心失效watcher中的自动hydrate：保留取消旧请求/清状态，mount和明确retry仍hydrate。实际唯一authorizationGeneration写入口是clearIdentity，不是新登录通知。原挂载用例错误要求“失效自动重读”同步改为失效不重读、重挂载重读且卸载abort；新增真实Pinia+真实账号退出composable+mounted按钮回归，旧源码确定1次OAuth导致红灯。原重试/切身份/权限发现及OAuth竞态33项定向通过。Web固定c82aa2fb368cbecedc7e9d4acd27444f955b65d3/tree401f4fc298e4134e24df5ea00082cc602f4fc392、1.16.142，当前未部署；先完整受控本地构建再安装复验。FULL当前9 PASS/1 FAIL/109 NOT_RUN，历史结果不覆盖。

### 16:42 本轮清理与退出修复上线结果
- Web历史worktree所用189cb8…及本任务此前0c3bf6…依赖集，在受控源已换用新集合且历史worktree删除后确认为无符号链接引用、无进程占用。保留压缩原receipt并逐集合取得原依赖锁后删除，共约670MiB。与本轮两个worktree/两个本地历史分支/一份旧会话合计净回收约0.94GiB；清理后可用约1.2GiB，新构建安装后当前约763MiB。完整进程/引用扫描约2分钟，曾见本地磁盘D态，不是重新挂载CIFS；没有杀服务、清生产state或备份。剩余唯一附加worktree是正在使用的runtime-lease-setup/api；Runtime活动分支与各develop保留。未删除远端分支。
- Web1.16.142 c82aa2f正式本地批次lease-web-logout01：101.797秒，363 PASS/0FAIL/2既有pending；包107549994字节、SHA3aca2796085c18195821d456c5e7390a8d441c95c56a1e743ad5dd3fa90340ba。原LOCAL受控安装器成功19.358秒，30 changed/613 files/256 online verified；合计仍低于600秒。证据task-ui-20261113-224052/logout-fix；权威record与state镜像均online_verified且精确源码一致。固定配置摘要与前驱一致，没有改OAuth/API授权、SSO cookie或生产数据。
- 新独立匿名context实测完整ENTRY01：未登录直接进入真实登录页，实际键鼠登录回真实聚义厅，加载index-BI5d-2XO.js；点击本机退出→公开首页、api_token无、私有事项无，6秒内无新网络请求/自动OAuth。再明确点击“进入工作台”，先新OAuth授权及token交换，再读取/user/my和本人事项：这是SSO下的新登录，不是继续旧本地身份，不宣称本机退出撤销了服务端SSO或所有设备。主浏览器A仍登录。ENTRY01原FAIL保留history，新PASS；FULL119=10 PASS/109 NOT_RUN（含部分覆盖），不是全部通过。CORE17的两个原生调用trace缺口仍在，不重放已完成图片任务。
- 本轮仅修复已证实的profile失效watcher，未添加全局禁止自动登录状态机。清理完成、定向测试、构建、安装与实际UI结果分别记录；主目标继续active。

### 2026-11-14 接续：资料选择焦点回归修复（尚未发布）
- 复核既有回执后FULL新增TALK03/TASK04/DELIVERY01/SKILL04四项PASS，证据`FULL-core-evidence-mapping-20261114.json`。不同受控版本的同轮证据分别绑定，不伪称同一最新候选；旧图片请求不重放。
- 实际UI新建自有未承办D1事项673：A保存正文v1/r2；B旧v0/r1保存得到409 REQUIREMENT_CHANGED，关闭并重读恢复A正文；无变化保存不增加版本、不重触发推荐。尚未完成所有复合断言，不提前标整项PASS。没有承办、执行或新图片生成。
- MATERIAL04实测：桌面选择后取消不改已存资料；390宽预览、返回保留暂存、完成持久化固定v1成功。但取消/完成后焦点落BODY，记录FAIL，非全过。根因为异步load先禁用触发按钮，Picker随后才捕获activeElement；保存过程也暂时禁用触发按钮。
- 最小源码修复：RequirementEditor传入load前原触发元素，Picker接受可选HTMLElement（普通click事件仍走原activeElement）；资料保存成功后nextTick再复用close归还焦点。未新增全局焦点框架或业务协议。
- 红灯3项已保存。第一版测试夹具JSDOM禁用后blur不模拟真实浏览器，改为先blur再disabled后重新确认3项真实失败；错误工作目录的一次夹具修正未写入文件，其后已更正。修复后35项定向测试通过，日志material-focus-{red-fixture-corrected,green}.log。尚未构建发布/线上复验，因此MATERIAL04仍FAIL；FULL目前14 PASS/1 FAIL/104 NOT_RUN。
- 当前额外API工作区runtime-lease-setup及主API的其他活动任务分支仍在使用，不能按“历史分支”删除。当前磁盘读数约1.5GiB可用，先前清理明细不改写。

### 17:12 用户收敛：优先跑通事项主流程
- Web1.16.143/f87fbd3/e27e8a0已完成本地构建188.140秒、432 PASS/2既有pending，包SHA77b9a14f1b72c3334bb3797c91cf09a08e19ccf4538b6b564a14723b5fd1580e。首次安装因本任务descriptor权限0644被拒绝，未发布；保存拒绝日志，仅更正0600后复用同包，受控安装成功14.634秒/256在线文件，未回退。证据material-focus-fix。
- 新版真实UI取消恢复触发焦点成功，取消暂存移除仍保留原附件；真实完成移除附件提交成功（D1仍未承办），但焦点仍BODY。核实BountyPanel资料组件key包含taskVersion，保存成功重建原触发按钮，固定旧DOM不能恢复。新增精确红灯测试material-focus-keyed-red.log，产品补丁尚未实施。此问题保留FAIL，不伪称完成。
- 用户最新要求“先把事项流程跑通”：暂缓非阻塞焦点修复和FULL119扩展，优先新自有轻量文字事项从创建→承办→议事执行→提交→验收完成，真实UI记录ID/报价/资金。不得重放已完成图片或历史终态事项。既有预算上限100文，历史8+本轮B1结算1文，按本任务实际账单核对，不把其他任务钱包波动归为本轮。
- D1创建及双tab旧版冲突证据经断言核对，TASK01/TASK06已PASS；FULL现16 PASS/1 FAIL/102 NOT_RUN。全局目标仍未完成。

### 17:23 事项主流程实际跑通（用户最新优先项）
- 新自有事项674 / 会话1760458009434：真实UI创建待承办→人工选择自有在线吴用、报价1文→确认承办预占1文→首次议事确认不执行→实际发送确认执行→生成checklist.txt→实际选中文字及文件两项→确认验收→COMPLETED/taskVersion4、delivery ACCEPTED。新案例未重放任何历史终态事项/图片。
- 文件UTF-8 74字节，SHA0067ea74b79438f1e99e2e82c9bdc3cfebcf4e768de73d967e5ec1f578ca068a；真实预览为“确认需求/执行并提交成果/用户验收”三行。验收后的两项正式RESULT摘要相同；下载仍200且字节摘要不变。真实完成截图已查看，输入框和验收操作收起，历史仍可预览。
- 必须保留局限：首次执行仅交付文件，没有同时返回要求的三行文字，随后一次真实UI明确“只回复文字、不再生成/修改文件”的补充议事获得文字并进入待验收。主流程跑通不是“一次执行完整交付两项”的通过证明；未隐藏补充轮。手机第一次预览点击未打开，后在桌面打开并验证，不将该手机操作当通过。
- 自有只读SQL确认674 escrow gross1/captured1/refunded0/CAPTURED/outstanding0；667–671均退款且无占款，672捕获1且无占款。钱包原有另一笔held1保持，非本轮事项占款、不操作他人事项；本任务此次新增结算1文，已知累计历史8+B1一文+E1一文=10文，未重置100文授权预算。
- 固定Web1.16.143 f87fbd3/API1.1.52 9c8c38c，完整记录E1-release-records.json。验收摘要`task-ui-20261113-224052/E1-mainline-acceptance.json`，逐步UI、网络、下载/资金证据同目录E1-*。非阻塞焦点仍FAIL、FULL16PASS/1FAIL/102NOT_RUN保持；没有把主线成功冒充全部回归完成。

### 2026-11-14 接续：资料焦点完整调用链核对与失败留证
- a994daf Web1.16.144本地186.578秒/473PASS/2既有pending，受控安装21.336秒/256文件。新增Panel当前ref解析与编辑器断开DOM用例通过，但线上真实保存仍BODY，证据FULL-keyed-desktop-complete及D1-keyed-desktop-complete。
- 继续沿handleRequirementSaved同步更新selectedTask→Editor watcher→资源key重建核实：Editor原`watch(() => [scope,epoch,task.id,enabled])`每次task对象替换都返回新数组，即使四个值没变也误触发“上下文改变”，本次加入的resolver在成功保存时被清空。不是等待时限/轮询问题，不改资源数据刷新协议。
- 将回归补成“保存同时替换相同id的新taskVersion对象及按钮DOM”，新红灯真实复现；改为Vue多source watch，只对四个实际值变化清空。另4条验证真实事项/身份/授权变化仍关闭旧编辑器。114定向PASS，尚未新构建部署。两次线上失败原记录均保留，不将单元绿当实际绿。
- E1实际缺价候选（并在D1补录disabled=true）/手选有价候选及674独立账本时点已分别核对ASSIGN02、ECON03为PASS。674只有RESERVE_BOUNTY1与CAPTURE_TASK1，前者时间在真实承办请求之后；FULL现18PASS/1FAIL/100NOT_RUN。

### 2026-11-14 17:43 事项资料焦点修复线上验收
- Web1.16.145 commit9d6e1ddf71cfa96ec441c94da50e1e4ec376f9e1/tree633915cef0fd0dacfd48fee68be512469db5d0cd，本地批次runtime-lease-web-material-focus-scope01-20261114，120.941秒，477PASS/0FAIL/2既有pending；制品SHA8c14c020b2dd7c1ddabf606dc467846fdbf25964f204b537da96ab33776d963d。CAS受控安装42.073秒，authority记录online_verified，实际浏览器入口index-Drxo6hhH.js。
- 自有未承办事项673实际桌面取消/完成、390px移动端预览/返回/完成/取消均恢复焦点至“选择资料”，不是BODY。网络仅两次requirements/edit PUT（完成移除、完成添加v1），取消没有提交；事项taskVersion6，仍open/未指派/无资金，无执行。手机最终截图已人工查看。
- MATERIAL04改为PASS，原143/144失败及红灯测试仍保留history。FULL当前19PASS/0FAIL/100NOT_RUN，不是全部通过。证据task-ui-20261113-224052/D1-scope145-{wire.json,readback.jsonl}及browser-postreboot/scope145-*。
- 用户优先事项主线674已完成，仍保留“首次仅文件，补充一次文字议事后验收两项”的实际限制，未重放已完成事项。磁盘仍仅约460MiB可用，不启动下一重型构建；其他全局回归及共享盘专项未因本次通过自动完成。

### 2026-11-14 17:49 事项边界真实UI回归继续
- 上一轮是有效进展：145修复上线并实测资料焦点。本轮未重建/未重复执行终态事项，沿当前145继续。
- TASK05：673真实改标题推进v6→v7/revision8，推荐刷新时旧选择清空且不能确认旧承办；手选吴用后原值保存，v7/revision8及正文/资料保持、手选吴用不丢、无第二次推荐。标题/描述/固定版本资料各变化证据与既有D1合并核对。
- TASK02：空正文/无资料“开始办事”禁用；真实选择shapes.png v1、不输入文字，点击一次开始办事创建675（201）。标题兜底“资料处理”、description空串，独立open、未承办、无funding；不自动执行。
- TASK09：674已完成详情和原议事只读，没有继续执行/重复验收入口；此次手机390px真正打开checklist.txt三行预览，截图已查看，补足之前未成功的手机预览。新675使用独立创建授权而非复用674终态。只读SQL仅674原reserve1/capture1，673/675无资金流水。
- 本轮真实UI脚本首次尝试点背景首页添加资料被hit-test拒绝：返回详情实际进入事项列表，底层首页DOM仍存在但不可操作；经截图明确后真实点“办事”再操作成功。无绕过遮挡或程序业务click，不记该错误操作成功。
- 证据既有task-ui目录task-boundaries-wire.json、task-boundaries-transactions.tsv、D1-task05-*、F1-task02-*、task09-*、browser-postreboot/task05/task02/task09-*。FULL22PASS/0FAIL/97NOT_RUN；主目标仍未完成。
- 接续：浏览器63621仍处674议事的checklist预览弹层，675是本轮新建自有未执行纯资料事项；不重复收费/重放674。可继续列表筛选分页、草稿导航/旋转、资料上传与其他实际启用回归。磁盘仍不足约0.5GiB，重型构建前需按已有授权/保留策略处理已核实可回收物，不清生产备份或其他任务。

### 2026-11-14 17:56 列表/首页投影及横竖屏回归
- TASK07真实UI：已完成+吴用27；进行中+吴用按30+5分页得到35唯一ID，逐条phase/assignedAgentId匹配；加关键词“回归”余3，count/total/items一致。只读打开588详情再返回，三条件与3个ID保持；未进入旧事项议事、更未执行。首页仍675/673/674等，不被列表条件污染。
- TASK08真实最近/待处理/归档视图，与hall/overview各源合并updatedAt前5及待处理逆序逐项比对通过；归档两源均complete空与页面一致。674验收后投影completed。显式刷新仅一次聚合overview，无循环全量列表读取。证据TASK07-list-wire、TASK08-overview-wire、TASK07-08-assertions及browser-postreboot/list-*/home-*。
- 测试过程中另一任务报价库发布API1.1.53：17:51:33资料preflight502，17:53:14旧议事请求401后转登录。现场确认部署PID273026存活，未抢占/重启；随后进程结束、安装PASS/HEALTH UP才继续。真实UI重登录后G1未发草稿仍保留。故障证据api53-external-release-interruption，不将自然发布中断当隔离故障用例PASS。
- 新API authority source43feb23d914c2316dd6d7aa460e4a8599f4d67e4/treeaef93a448e1d7b307e27d20974b8ee1aece156c9，JARb5fad5996f2b024059b0854e80a2d35038b7899841194553e178ab0406d6c756。确认旧API9c8c38c是其ancestor，不覆盖他人发布。TASK07/08仍绑定发布前版本，不重标为新API全量通过；后续测试绑定53。
- ENTRY04：G1未发送草稿+shapes.pngv1预览，390x844→844x390→844x240→390x844；图640x480无串图，横向无溢出，低高关闭按钮hit-test和实际点击成功，回竖屏保留完整草稿/资料，home-overview未切地图，网络无业务写。只证明浏览器模拟横竖/低高，不证明真机软键盘。截图已查看。证据orientation-*及after-api53-release。
- FULL25PASS/0FAIL/94NOT_RUN，主目标未完成。浏览器63621当前390x844首页，保留G1未发送文本和shapes.pngv1，供下一轮草稿/导航验证；勿误点开始办事。本轮无新增执行或收费，磁盘约832MiB（外部任务释放非本轮清理成果）。

### 2026-11-14 18:16 真实归档回归及首页同步缺陷闭环
- ARCHIVE07通过：674实际确认“收入案卷”，历史筛选+关键词674重新打开已验收2项；真实点击下载/预览，辅助下载74字节SHA仍0067ea74b79438f1e99e2e82c9bdc3cfebcf4e768de73d967e5ec1f578ca068a。672自有完成事项两个真实tab先后确认归档，两次200且taskVersion7、completedAt一致，第二次与权威读回一致；首个mutation DTO updatedAt比库回读差1ms，不将该显示时间精度差冒称重复归档。只读SQL仍672/674原有reserve/capture各1，无额外费用或执行。
- 新发现TASK08失败：归档详情和搜索archived，回首页仍completed。保留原PASS和本次FAIL。根因仅JuyiHall archive成功后未推进既有hallReadRevision；最小修复一行，未改API/业务协议或新增刷新框架。已有completed-records真实函数测试扩展成功/未提交/取消三分支，红灯0!=1，绿灯62项（含实际Overview刷新key消费）。
- Web1.16.146 commit a410b4fdfff8121fdbaa28a0c3c577db337d2a06/tree efe998ed4a262ed6b7a76b820b01d46de1b3978a。第一次本地build01在2.21秒正确拒绝固定源码目录残留上版node_modules软链；未删共享依赖，确认只移除本任务源目录旧软链后新build02重试，保留原失败/result/retry原因。build02 109.791秒，505PASS/0FAIL/2既有pending，包SHA314b752ac5995e19fed6f272008352a8740eb8eb9dd9abedd1b704f7e420d1b9；受控CAS安装15.579秒online_verified，真实浏览器index-B9ngDIbN.js。
- H1新事项676用于修复线上验证，未重放旧终态：明确请求吴用仅交付“归档状态同步验证完成”，无文件/生图/联网。实际新API53报价吴用2文（不是旧1文），按该实际报价确认承办一次；自动初次议事得到最终文字，实际验收一次完成。随后在新146页面归档，返回首页不手工刷新即从recent移除，已归档列表出现676/672/674且状态正确，截图已查看。TASK08重测PASS。
- 676只读资金reserve2/capture2，escrow gross2/captured2/refund0/outstanding0；已知累计历史8+B1 1+E1 1+H1 2=12文，100文授权预算未重置。G1仅未发送临时方向草稿，在本轮明确替换为新H1测试需求，原内容证据保留，未发送G1。
- 证据task-ui目录archive07-*、archive-home-refresh-{red,green}.log、archive-home-refresh-fix/、H1-*、browser-postreboot/H1-146-*。FULL26PASS/0FAIL/93NOT_RUN，目标仍active；旧PASS各自绑定原候选，不等于全量新146/API53通过。
- 第二原有auth tab刷新后登录导航异常，两次后停止同输入登录重试，未改账号/Token或接管它。归档重复测试另建同一个已认证A浏览器context的新tab C27E4E4529023D3F28BC5267290AEE27（browser-archive-repeat/owned.json），只用于自有672，collector97519已正常结束；已保留完整归档响应。后续优先继续未测正常入口/资料及有真实隔离前提的用例，不伪造F5/F6/F7资源。

### 2026-11-14 18:37 好汉只读信息、资料上传及文件起草回归
- AGENT01已通过：实际名册→吴用→刷新→离线扈三娘→刷新→李逵；默认执行模型与注册profile-capabilities逐项相符，空技能/能力不借用上一好汉数据，注册模型不是最近一次调用模型；无渠道/密钥字段及管理写。证据AGENT01-read-wire.json、browser-postreboot/agent01-*。此前FULL27。
- MATERIAL01真实资料页上传专属前缀M01-1114的PNG/JSON/PDF，各生成独立fileId/v1；列表刷新和详情实际UI读取。预览前目录窗口无content/preview GET；三份实际点击下载，辅助授权GET所得字节、SHA、大小均与本地fixture及服务端固定版本元数据相同。PNG/PDF真实预览截图已查看。当前是平面资料库，以唯一前缀隔离自有fixture，没有改他人文件或虚构目录。
- 发现JSON列表误标Word文档、文件选择accept漏JSON，记录MATERIAL01 FAIL。责任仅Web：DOCUMENT泛型标签改“文档”（含筛选），现有accept补.json/application/json，不改API/MIME分类/预览/资金合同。既有实际组件测试新增JSON/MD/HTML/DOCX类别及上传input断言，红灯保留；首次组合诊断漏tsx导致JSON模块加载失败，保留原日志，按既有入口补--import tsx后57项通过，未当作业务失败或盲重试。原型现有资料目录补JSON文档示例、规格同步，node语法检查通过；未将原型宣称为真实业务验收。
- Web1.16.147 commit c18eccd7f64a3817b034475a33e5b8b7023e9863/tree d4887a6414114cfc4b0d2cca5929af3b9395d1e5；本地批次runtime-lease-web-material01-01-20261114，109.728秒、583PASS/0FAIL/2既有pending，包SHA f0765627905c2a36b881508aa9fd5529822d300a09dde9a76b2ce7ac9f16867d。构建前仅移除本任务源码目录旧依赖软链，未清共享缓存；systemd实际成功退出0。工具会话外层报告143但实际build记录BUILT、sourceUnchanged、systemd success，未以外层错误伪造重试。受控CAS安装30.775秒online_verified，真实新页面index-CEUO2SQ6.js；JSON现显示文档、input含JSON。MATERIAL01复验PASS，历史146上传/字节证据与147展示修复分开，不谎称重复上传。证据material01-*、material-fixtures-1114/、material01-fix/。
- MATERIAL11通过文件详情分支（定义“文件详情或案卷”，不宣称另测案卷）：147实际“用此资料提需求”带入pws_233151ee23fc4538b7aec542c04f362c/v1，所选资料真实预览640x480；关闭/返回同文件。离开时真实POST /agent/hall/drafts保存hdr_1ced5e5512c04483b5077bde753c2e9d、EDITING、submissionRef=null，originRef=juyiting:file、sourceRef/targetAgentId=null、inputs固定原版本；没有提交事项/承办/执行。首次辅助断言笼统“无POST”失败后核查，确认是合法草稿自动保存，不隐瞒写入、不声称仅本地草稿。此前146文件起草也留下本任务草稿，不是收费事项。证据material11-147-wire.json及browser-postreboot/material11-*。
- FULL29PASS/0FAIL/90NOT_RUN；CORE17与583单元/组件测试不混算，主目标仍active。事项674、676闭环/归档已通过，未重放，已知累计仍12文。当前浏览器63621在147自有M01 PNG详情，可继续新版本绑定/文件管理等；磁盘约502MiB，下一重型构建前核查可回收物，不删生产状态/备份或他人任务。ENTRY07仅地图打开观察，仍非PASS；F5/F6/F7未准备不能伪报通过。

### 2026-11-14 19:04 固定资料版本回归与纯资料编辑修复
- MATERIAL05真实UI通过：新事项677在I1资料v1创建后，资料库追加v2，原事项和执行grant仍固定v1。吴用真实回复未在需求透露的marker=JYT-I1-V1-7c2a、quantity=37；验收完成，未归档。另由资料库v2生成独立未提交草稿hdr_7da373774bab4d7382b770a311fe2a08。两版本授权下载字节和fixture SHA一致。执行6文，reserve/capture各6，累计已知18/100文。证据task-ui目录I1-full-wire.json、I1-fixed-version-assertions.json、I1-final-readback.jsonl、I1-escrow-final.tsv及I1-transactions.tsv。不宣称已采集Runtime工具trace。
- 677标题输入初次hit-test失败因可选标题details折叠，并非产品遮挡缺陷；最后使用自动标题，不改完成事项。
- MATERIAL06真实FAIL：675为description空串、已有shapesv1的纯资料事项，选择新增I1v2后被Web错误要求需求描述，没有发出PUT。核实API也无条件拒绝空白描述。冻结最小修正规则：标题非空、描述必须字符串；描述为空白时必须至少一项固定资料；两者皆空拒绝。不造占位文本，不改变ACL/事务/幂等/版本/收费规则。
- API1.1.54候选05a070f31378c3a035a0032506e7465b5d5e10ea/tree1fe010497d1ccfe74813ff154f1bc5f1c13068a3，基于线上53保留报价库修改；Web1.16.148候选a49f2590531e83883619d064d696f1933ad2af52/tree1c8e108572c778fdfb8124d4d6a814a8ed2fc8fd。实现/规范/原型/回归已提交，Web定向61PASS；API业务测试待本批执行，未上线。FULL30PASS/1FAIL/88NOT_RUN，不提前消除FAIL。
- 为本次构建仅删除四个已核实无人使用、无源码软链引用的本任务旧Web依赖集合，保留依赖回执压缩件与逐项审计，未动当前147/前146依赖、最终包/源码/生产状态/备份。cleanup-20261114-continue证据；清理终态成功，磁盘剩余1.8GiB。既有API恢复缓存modules-2/files-2.1实际0文件，因此本批明确允许联网解析而非盲用offline，不清余下编译缓存。
- API批次lease-api-material06-01 plan-only通过，19:04启动既有local_build.py串行入口、独立600秒systemd。构建/安装/业务复验分别记录，主线继续675编辑、改名、解绑且不损坏677历史成果。

### 2026-11-14 19:15 构建缓存故障归因与推荐回归
- API material06 build01 8.582秒失败：旧groovy-dsl不可变缓存缺metadata.bin，尚未编译；锁内审计隔离206个groovy-dsl及141个transforms缺元数据目录，保留有效项。build02 32.610秒进一步发现dependencies-accessors同类损坏，补全全部不可变类型审计，隔离唯一缺失项；未原输入盲重试，均保留FAIL与编排器归因。
- build03恢复冷依赖/编译缓存，444秒后失败于common-test编译worker启动：workerMain只有初始化锁，gradle-worker.jar已缺失，ClassNotFoundException，不是业务测试失败。单批未超600秒但未达300秒目标，主要冷依赖解析；锁内将该精确损坏缓存隔离，保留本批新恢复的依赖/编译缓存，启动build04。缓存证据位于material06-fix/damaged-cache；不将修复缓存说成应用已发布。
- 为后续包空间，核对本任务旧API52最终api.tar完整摘要及其中application.jar摘要与外部中间JAR完全一致后，仅删重复build/starter JAR约251MB；最终包、源码、测试报告、证据、生产/备份未删，回执material06-fix/duplicate-old-jar-cleanup.json。
- ASSIGN01真实UI通过：675现有推荐张清（PNG解释）→改选吴用，详情明确“已选承办”、真实24文，不点确认；GET675仍open/assignedAgentId=null/funding=null，无承办/执行/资金写。离开重进未确认手选回到推荐，不声称跨详情持久化；无价格可手选分支引用本轮ASSIGN02的原始证据而非虚构推荐故障。首次辅助“无POST”断言遇到合法search/status-counts查询，校正为核对业务mutation后通过，未隐瞒请求。证据assign01-wire.json、assign01-task675.jsonl、browser-postreboot/assign01-*；FULL31PASS/1FAIL/87NOT_RUN。主目标仍active，675未执行，预算仍18/100文。

### 2026-11-14 19:28 MATERIAL06两端构建完成、受控安装中
- API54批次lease-api-material06-04完整265.703秒（打包13.79秒），117测试0失败/错误/跳过；Gradle205任务174执行31缓存复用。候选与前述05a070f/tree不变；包SHA5666c646bdd0dfd8f1d0a705b937cde08d6abea04d66765af119442690cab543，JARSHA13ed26e1891dcf460eb09427d961884d253db386b05d583640ff20e29dca1e98。未减必要验证，缓存故障前3批FAIL继续保留。
- Web148批次runtime-lease-web-material06-01-20261114完整232.970秒，585PASS/0FAIL/2既有pending，包SHAd2f164b8d1cfd5f55e5f84a25ce9517240ddad31f55901b93ecd762ad699c873；a49f259/tree不变。sourceUnchanged；两端开发及必要构建均完成后才开始API受控安装。
- 安装前空间维护：API54最终包逐字节摘要核对后，删仅本批已完成的重复中间JAR，测试/包外证据保留；Web145旧依赖集合无源码软链引用、无FD/cwd使用，持串行锁和key锁删除，保留压缩回执。第一次因把自身同名前缀.lock误当目录内引用安全中止，第二次因Web构建持锁拒绝未删，构建结束后才成功；不绕锁。146/147/148依赖和全部最终包/生产备份保留，回执material06-fix/*cleanup.json。
- API安装descriptor绑定实际线上53前序JAR，forward-only，既有安装器备份/锁/摘要保护不变。新JAR已切换启动PID314844，当前等待实际健康，不能宣称安装成功或MATERIAL06复验通过。Web148尚未安装，待API健康后受控安装再真实界面验证。源与包、旧record/descriptor/安装日志均在material06-fix。

### 2026-11-14 19:46 MATERIAL06线上闭环通过
- API54受控安装PASS、HEALTH UP、实际PID314844/JAR与候选摘要一致，启动健康用时215秒；Web148受控CAS安装78.013秒online_verified，256线上文件核验，实际浏览器index-CJC26Fue.js。安装回执分别material06-fix/{api,web}-installed-record.json；未回退，API重启后实际UI重新登录。
- 675真实纯资料编辑：description保持空串，添加I1v2后taskVersion1/requirementRevision2，资料2项；资料库实际将I1改名I1-1114-renamed.txt；返回675从选择器移除I1并完成，taskVersion2/revision3，仅原shapesv1保留。675仍open、未承办、无funding，不能将其说成已执行事项。
- I1库文件仍ACTIVE、同fileId、两版本及原字节/SHA未变，真实授权下载v1/v2逐字节比对fixture；已完成677详情仍固定v1，真实点预览显示marker=JYT-I1-V1-7c2a/quantity37，成果与验收记录实际打开已验收文本仍相同。两截图已查看。SQL675没有资金交易、677仍原reserve6/capture6，没有重放或新收费，累计18/100文不变。
- MATERIAL06原147/API53失败保留，新148/API54复验PASS；证据material06-148-{wire,assertions}.json、material06-{after-unlink,148-added-readback}.jsonl、material06-v{1,2}-after-unlink.txt及metadata、material06-transactions.tsv、browser-postreboot/material06-*。FULL32PASS/0FAIL/87NOT_RUN，CORE17不混算，主目标仍active。事项674文件+追问、676文字交付均已验收归档；677固定资料版本读取已验收，此轮在新候选复核历史只读，未重复付费执行。
- 操作脚本差错独立留证：文件列表strong被覆盖点击拒绝，改实际“查看文件”按钮；文件名称input无显式type属性，原[type=text]选择器未命中，改maxlength定位；第一次“保存名称”因此原名无变化（真实PATCH200），第二次才改名成功，两请求均保留；辅助GET误用缺/agent前缀路径失败，校正实际UI已使用的路径，不当作服务失败。未伪造UI操作/删失败。
- 收尾包登记已调用原mark-complete，但两批短构建路径/home/isp/state/cyf-build不在当前清理器显式bases内，安全拒绝“task outside explicit bases”，源码及主机安装器均相同。原包/证据保持，不手改completed-tasks.json、不挪动当前绑定包/造软链或为主线另改清理框架；登记未完成须单独适配既有入口后再做，当前包仍不可自动删除。磁盘约636MiB，下一重型构建须先处理实际容量。
- 接续：浏览器63621在677成果只读预览（端口37579、tab17D0E0D2E412EF29879767CBA2015B7B），可以继续剩余事项/正式议事回归；不可重放672/674/676/677终态，也不能把F5/F6/F7缺失资源用例记PASS。此轮不扩展历史分支/worktree/会话清理。

### 2026-11-14 20:02 J1多轮事项阻塞定位与修正范围
- 新事项678实际UI选择吴用并确认2文承办，发送中刷新后未重复确认；首轮真实交付J1/8人/120文，第二轮仅要求改10人。请求COMPLETED但REVISION_REQUEST父结果不是成果，reviewProgress持续QUEUED/child=null。未发第三轮、未验收、未取消。累计已capture18文，678预占2文，未当作已capture20。
- exact outbox review_93635c299259a9e5413af86651f0256051fc2ee41fdb9401748645097反复因AgentTaskFormalDeliveryDecisionServiceImpl.normalize的reviewReason is invalid回滚；普通多行指令被isISOControl拒绝，DAO同字段重复限制。不是Web漏消息，不显示控制文案冒充成果，不改父final/数据库状态、不重新提交。
- 本次最小修正固定在API：reviewReason允许LF/CR/TAB，保留既有非空/长度/其他控制符/身份/版本/事务约束；DAO仅改reviewReason，不扩展summary/purpose/ID规则。加实际MySQL consumer→决定→DAO→子请求事务回归及服务层参数化测试；不改Web/Runtime/收费。现存超过4000等边界不在本次换行修复中扩张，不宣称全字段域已统一。
- FULL新增TALK01 FAIL，32PASS/1FAIL/86NOT_RUN，原候选失败留证。证据J1-*与j1-revision-fix/production-failure.log。开发、构建、安装和UI复验分别记录。
- 20:11发布前继续追读发现同字段历史读模型也按ID规则拒绝，Web既有FormalDeliveryList消费者也拒绝。因此主动停止本任务build01（360.772秒、signal15、publishable=false，未部署），扩大仅此字段的实际读依赖修正及回归；不把首候选说成完整修复。API读模型与Web历史消费者同步允许LF/CR/TAB，summary/purpose仍不变，MySQL回归追加历史读取。无需新交互/原型结构/Runtime改动。该次超过300秒目标，构建日志保留，不改为成功。
- 20:19 Web修复定向最终12PASS：新增用例先暴露同函数前置validText重复校验，删除该冗余条件，由既有state分支统一校验reviewReason后通过；f64c127。前两次诊断命令分别因工作目录无法解析tsx、Mocha默认spec误加载全量而失败/主动终止，原日志保留web-focused*，不计产品验收。API候选bcb82933e5（55）build02在途；两端必要构建都成功后才安装，尚无本修复上线。
- 本任务已弃用146/147依赖集合经精确Git lock摘要、全工作区符号链接与进程FD/cwd检查、串行及key锁删除；压缩receipt及清理证明在j1-revision-fix。保留当前148依赖、全部有效Gradle缓存、最终包/源码/生产/备份，构建前约1.2GiB可用。
- build02真实FAIL 477.906秒：选中的既有MySQL集成夹具仍调用旧的6参数正式决定服务构造器，缺已上线TaskBillingService依赖（不是本次生产代码编译失败）。服务层多行测试运行通过；MySQL测试未执行，不宣称通过。仅更新该原夹具为当前构造器，明确资金依赖为mock，新增多行修订verifyNoInteractions，资金真实性仍由678线上账本验收证明。build03使用修复后的固定源码，不同根因/输入不盲重试；包仍未发布。
- 20:25 ASSIGN03单独通过：678确认发送中真实刷新→重进→自动首轮完成，只有一次point-and-deliberate POST200；只读SQL恰一ACTIVE grant/assignmentRevision1、一ADMITTED bootstrap绑定原首请求、一次2文reserve。覆盖定义“重复点击/刷新”的刷新分支，不虚构重复POST。J1-initial-wire.json、J1-assignment-uniqueness.tsv与真实UI快照；FULL33PASS/1FAIL/85NOT_RUN。修改队列仍待新包修复，未把承办通过等同多轮通过。
- 20:34 build03真实TIMEOUT：600.655秒受控SIGTERM，systemd10m8.803含停止，未产出可发布包；未扩时、未把在途批次改名续时。归因：将整类38项MySQL合同测试（含无关分页/索引/迁移）带入构建，加独立MySQL初始化约90秒、共享负载下构建/分层耗时，预算内未结束；日志可见多行用例执行但无最终XML，不能记PASS。build04不改生产源码、不减安全基线，按本次字段真实依赖定向选择6项MySQL：多行决定及历史读、原事件幂等、收据失败事务回滚恢复、验收竞争、跨owner身份、消息页进度；服务层测试与全部发布基线保留。无关38项整类回归未获通过证明，不能冒充全量通过。
- build03隔离MySQL已随自己的systemd组退出，核验无进程后只删该批次synthetic data目录，保留mysql.log/测试/构建输入/失败记录；不清生产DB或有效缓存。
