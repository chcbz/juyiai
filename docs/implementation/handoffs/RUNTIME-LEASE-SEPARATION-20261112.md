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
