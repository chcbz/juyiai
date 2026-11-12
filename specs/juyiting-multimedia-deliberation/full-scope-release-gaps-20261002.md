# 完整交付缺口核对（2026-10-02 12:00 Asia/Shanghai）

本记录是交接证据，不替代 TASKS.yaml 的唯一运行台账。

## 本次接受

Client installer `b1e8cceac3e064f6d6759ac8d9c085f21374e8e1`，tree `fa630138c96a77f60bce23edd331f8356cecffd6`，parent `9f78b95baab69609f8954785d9baa2d199f62797` 已 byte-exact FF 到融合特性分支并推送、远端 readback。完整 payload 43 文件、runtime import closure 28 文件，无缺失；每文件摘要和原子 current 切换，保留持久状态。Owner 隔离安装 selector 为 10 PASS、0 FAIL、35 未选中 SKIP，不表述为45项全通过；Main核验原证据摘要，未重复测试。证据见 `integration-evidence-20260928/client-installer-b1e8cce-20261002/`。尚未安装生产。

## 不能缩小的剩余范围

- Client：Owner只读查明V3声明/就绪固定关闭且缺生产poll lane。必须补真实GENERATE_IMAGE/EDIT_IMAGE能力、源revision及重启幂等接线，不以已有inspect或V2生成代替编辑；typedInspectionCaBundlePath须核对normalize。已由原Client Owner继续实现。
- Web：源码确实读取 `VITE_JUYITING_FOLLOWUP_EXECUTE_V3_UI`；下一共同候选须在现有两flag之外启用该编辑UI。尚未修改云端配置。正式构建仅Flow。
- API：生产relay构造器修复候选 `d0b1eee8770bf1e2ab80dfe1d52da9b3303d540d` 已存在，真实迁移/完整Spring接线与最终JAR仍待Owner验证；不以此前SKIP或恢复旧JAR健康冒充通过。
- 安装启用：必须包含workspace及formal artifact两个私有存储、typed inspect、媒体/归档/交互、bootstrap/execution、selected-output finalization/formal delivery、controlled-image V3。只读预检方案不能当作最终发布方案。
- 身份：冻结测试账号既有local/server精确目标及归属。无授权不创建身份、不bind/reprovision、不操作foreign服务；当前403须定位真实原因而非泛化为不可用。
- 产品：AC01–AC22、FD01–FD12仍未完成验收，须真实理解、生成、原图编辑、版本/血缘、预览下载保存、正式交付和完成任务；两种接应均须证据。已有额度授权不是伪造consent/grant的许可，亦不能将CONSENT_REQUIRED当作任务成功。

## Web协作

voice UX Owner `01a0faaf-fa6c-7771-8b57-d50ff13a447a` 独立树负责Composer/VoiceControls/必要Hud及voice test；本任务Web Owner `01a0fa90-6916-75c3-aca8-f5638c515f82` 独占component-behavior loader fixture。共同基线3a4cdf，最终由Main集成后冻结exact SHA，先核查自动Run再触发，保持4403172控制权与deployment hold。不使用历史Reviewer作为门禁。

## 12:24 身份与合同补充

- Runtime Owner只读确认测试账号既有local身份wuyong(binding1)、linchong(binding2) ACTIVE且owner/client/tenant匹配；候选选择wuyong，不新建身份、不并发注册同agentId。安装仍需现存服务custody确认，Main未控制foreign服务。
- server既有binding15和identity为SUSPENDED，hosted-profile缺失。403为有效key后的WebSocket归属拒绝，不是公网匿名入口限制。已向用户询问仅恢复既有身份和必要关联记录的授权；尚未收到明确授权，不DML、不repair、不reprovision、不充值。不能以本次自动goal continuation推导授权。
- Runtime Owner报告12:19 API10018无listener，原恢复Owner正在只读归因，未自动重启。
- API候选9ab62 Owner确认producerRequestRevision由服务端解析、持久化并在执行前对照归档权威复核，不能开放Client伪造输入。Main只读验证resolver确有比较。现有Client wire绑定version/generation/assetRevision/digest，无需盲目新增字段。

## 12:32 运行故障已归因

- Kernel精确证据：2026-10-02 11:57:28（Asia/Shanghai）global OOM killed Java PID3155665/uid987，所属本任务旧API恢复scope；不是正常应用退出。Main已核验Owner证据SHA256SUMS，12:32仍无该PID。
- 先前一次恢复健康是历史事实，不能当作当前可用性。唯一台账MMD-U4已记录environment_resource故障；现有API fixture PIDs3223665/3223691/3223733仍live，Main未控制、取消或重启。
- 原一次canonical start授权已消耗，已向用户请求新的精确一次启动授权，尚未收到明确回复。不得以goal自动继续消息推导授权。
- Client历史service Owner Agent句柄不可用，不代表foreign服务无主；未完成custody交接，不修改或重启该服务。已授权开发和现有额度测试继续执行，生产恢复/身份修复分别等待必要授权。

## 12:59 Client安装静态候选接受

- 融合Client feature现为 `7d1d7eb6e552a1a5c68e106ccc3ec02e815c5579` / tree `81d53d246752199a8614e14184a34e8d9259532f`，包含a7ea生产接线与48文件安装payload候选（28runtime模块）。Owner定向候选16PASS；installer1PASS、40非目标SKIP。
- Main指出并纠正原候选的1/2/15硬编码persona黑名单和预期能力/实测就绪混用；现在区分provider-binding namespace来源证据，模板仅STATIC_VALID/SYNTHETIC_EXPECTED_REGISTRATION，真实捕获比对仅READBACK_MATCH。Main同tree现有依赖环境直接静态调用确认providerBindingEvidenceStatus=UNVERIFIED、fullInstallationReadiness=false。
- endpoint/model/binding/policy/identity/secret仍需冻结，provider局部policy不是正式成果存储、归档、selected-output等完整启用策略。未安装、未重启、未付费调用；不能以静态模板通过解除运行依赖。

## 13:22 定向发现：真实生成配置与双模式目标缺口

Runtime Owner完成现有配置及精确测试账号范围只读枚举，无生产写入/Provider探测/服务操作：

- 现有Responses通路只证明文本/理解路径；已安装环境缺专用controlled-image key，模型目录39项未发现gpt-image/DALL-E名称。这不证明上游永不支持图片，但当前没有已验证生成/编辑endpoint/model、provider binding ID/epoch及operator政策，不得据此宣称生成就绪。
- 精确账号范围9个persona bindings、0个hosted profiles；4条online runtime标记停在11:57:21.951，不能证明当前健康，也不能作为server模式替代目标。没有找到既有ACTIVE hosted/server目标；binding15仍SUSPENDED。双模式验收不得缩成仅本地模式。
- 完整inactive API配置已由Owner生成并明确NOT_READY，缺失值保留MISSING占位，未安装。配置范围包含workspace/formal storage、bootstrap/execution/media、typed INSPECT、archive、selected-output/final delivery及受控图片V3，而非仅单个provider开关。
- 需要Provider/account custodian提供真实生成/编辑绑定及专用秘密安全引用；需要服务custody移交和既有server身份/必要关联配置的明确修复授权。不得将普通开发授权扩展为新租赁、充值、创建新身份或操作foreign服务。
- API工程继续推进：CHECK literal大小写及typed schema先于父表初始化的真实缺陷已形成修复，当前候选3080dc7b/tree0105e845，完整fixture与bootJar结果尚待Owner交付，不宣称通过。

只读发现不改变hold，不构成发布或34项验收证据；最小下一步是补齐真实Provider配置/运行授权，同时完成正在推进的API工程验证。

## 13:32 恢复路径澄清：不将缺hosted_profile误判成必须新增

- Owner补查发现binding15有合法原managed-hosting来源：唯一ACTIVE lease/initial intent、有效entitlement、原managed key及scope一致的既有claim。该路径不依赖agent_hosted_profile；此前没有可直接使用的ACTIVE目标结论仍成立，但恢复不必迁移到另一种profile发布机制。
- 最小待授权动作是fresh CAS恢复现有binding15及同一identity生命周期，随后调用一次已有零账本扣款free reprovision恢复原managed runtime。需要明确production DML、reprovision及managed service custody授权；不新建identity/profile/key、不重绑、不租赁/充值。此时仍未授权、未执行。
- 不应调用要求hosted_profile的通用repair端点来代替原managed-hosting恢复；新建profile属于更广迁移，不在最小方案内。Provider生成/编辑真实绑定仍独立缺失，不因身份修复自动就绪。
- Owner明确允许共享的四份脱敏证据已校验SHA256并保存于integration-evidence-20260928/runtime-recovery-scope-20261002；其余私有配置/凭据指纹未复制。

## 13:35 用户明确授权：最小运行恢复

用户针对上一条精确请求回复“允许”。授权范围为责任Owner接管相关服务、恢复API，且仅恢复既有binding15及同一identity，并执行一次不扣款的原managed-hosting重新部署。不新建identity/hosted_profile/key，不重绑、不租赁、不充值。图片生成/编辑provider配置仍单独NOT_READY，此授权不产生缺失的真实配置/能力证据。

Main指定Runtime Owner Shannon（01a0fa77-8e55-7151-a0b5-1b0b1b526358）执行，Main不直接操作服务。执行顺序：与API Owner协调释放重型验证资源；fresh资源、原制品及进程归属校验后一次canonical API恢复并验证健康；重新核对精确scope/lease/intent/claim/key及竞争状态，在CAS事务中恢复原两行生命周期；使用fresh幂等键及expected lease version进行一次已有free reprovision，响应未知先查状态；核验实际runtime与身份注册。不得抢占foreign进程或安装NOT_READY配置。

已向两名Owner直接发送授权及资源交接要求。此段只证明授权与责任分配，不证明已执行DML、恢复成功或功能可验收；实际结果以Owner脱敏回执与运行readback为准。

## 13:45 fresh CAS发现历史runtime投影不一致

恢复Owner在DML前发现同canonical Agent存在一条历史offline runtime：无endpoint/token/current task，但binding/client/owner投影与binding15不匹配。先前精确scope查询的“无runtime”不能外推为canonical Agent全局不存在行。注册实现按canonical Agent读取并校验scope，不能让reprovision绕过此拒绝。

已在任何生产数据修改前停止binding/identity/reprovision分支，向用户请求仅对这一条既有detached offline runtime做投影CAS realignment，保留row ID与canonical Agent，保持offline且无endpoint/token/task，不新增/删除行。此前仅两行生命周期授权不自动扩展至该行。API恢复授权仍有效且独立继续，在API Owner明确释放重型验证窗口后恢复基础设施、一次canonical start及健康核验；需要API入口的free reprovision必须在API健康后执行。共享脱敏异常证据及摘要已保存。

## 13:50 API完整升级与制品验证通过；Provider门禁语义纠正

- Main已核验API Owner最终清单摘要、clean commit/tree、全部9个变更路径摘要、v28真实JUnit 1/0/0/0、相关证据摘要及253586846字节bootJar SHA256 `b4e53624b017901db7d50a5b9023cb029ac37330e17c4ae5aa9bc737d1b09824`。最终源码 `0a4d4299122e9041c815cae067584212d8f5176a` / tree `5036922df1d086e963fa2785c3d63da882942048` 已byte-exact FF到API融合feature并push/readback，不重跑相同tree。构建来源为local_user_authorized，仅API既有授权例外，非Flow发布或产品验收。
- 完整JiaApplication真实启动、旧catalog升级后第二次幂等启动、错误scope/OR TRUE/source负向拒绝均由Owner完成；owned Redis/DB清理，重型窗口已明确移交Runtime Owner。API工程fixture/JAR缺口已关闭，运行安装、完整真实配置与双模式产品验收仍未完成。
- Client Owner核实bindingId/epoch是本平台Operator配置/轮换栅栏，不是上游发放对象；此前要求“上游单独签发binding receipt”无生产合同依据，应撤销这一解释。候选checker的来源字段不等于外部能力证据，正在修正仅任意type/path/hash即可VERIFIED的缺陷。真实缺口为可用Images origin/model/凭据来源及合同匹配、平台独立policy冻结与认证registration/presence readback。
- 当前生产adapter追加 `/v1/images/generations` 与 `/v1/images/edits`；编辑要求JSON images[].image_url，响应要求base64 PNG。不能由Responses理解成功或models名称列表推断该合同兼容，也不能虚构不存在的上游binding API作为硬阻塞。

## 13:55 Client Operator配置来源修正已合入

Client feature已FFpush/readback `407db0a67d0446f345680f3fe7dab5d3d368d1b2` / tree `004678a3839e0a558196242fbe8aebb06b11974a`。Main核验5文件范围、diff、22pass/0fail/0skip报告与SHA256；未重复测试不变tree。候选不再要求上游签发binding，必须实际读取Operator冻结普通文件、验证字节摘要及精确policy tuple才能称配置来源VERIFIED。仅模板声明仍UNVERIFIED；STATIC_VALID、认证READBACK_MATCH与Provider实际兼容性保持分离。证据在integration-evidence-20260928/client-operator-binding-407db0a-20261002。未安装、未调用Provider或操作服务；原V3生成/编辑生产执行合同不变。

## 13:56 API可用性恢复完成，不等于新功能部署

Runtime Owner在13:50执行一次已授权canonical恢复；13:54–13:55 readback确认PID3275655、精确scope、六控制器归属及旧JAR摘要均匹配。Main独立读取10018 listener及HTTP200/UP。原API恢复阻塞已消除，不再重复start。安装的仍是旧JAR `632012a3…`，不是新多媒体候选 `b4e53624…`，不得称多媒体上线。

runtime/binding/identity生产DML及free reprovision仍未执行，单行历史scope修正待追加授权。Owner原readback含实际身份scope，未直接复制；归档的是省略scope/命令行的脱敏回执及原始SHA256。同步纠正integration.yaml滞后的Web/Client pin到实际c74a/407db0a，保持“开发基线非已发布”的标注。

## 用户最新指令：既定恢复范围不重复确认

用户明确要求“不需要重复让我确认”。结合此前已允许责任Owner恢复现有binding15、同一身份和原managed服务，Main通知Runtime Owner：同一恢复目标所必需的已发现单条detached offline runtime投影修正不再作为逐次审批阻塞；自检后执行精确CAS，保留row ID/canonical Agent及offline/无endpoint/token/task状态，与原binding/identity生命周期恢复按事务核验；已有零扣款free reprovision仅一次，未知响应先查询。API已UP，不重复start。

边界不变：不新增身份、租赁、充值、凭据，不跨账号或绕过ACL，不操作无关进程。真实归属无法证明、新收费或超出目标的破坏性操作才停止对应动作并说明；不能把用户免重复确认解释为伪造缺失Provider配置或验收证据。Owner按实际结果主动汇报，不再为同一范围内正常恢复步骤反复请求确认。

## 14:18 既有托管目标恢复并实际注册

Runtime Owner已完成授权范围三行CAS：binding15/identity15 ACTIVE，既有runtime37投影与精确scope一致，影响行数各1。首个候选显式赋值generated-column被MySQL拒绝并完整回滚；修正候选仅更新普通字段后提交，保留了真实失败归因。14:12:41既有managed service自动从pending_ack恢复为registered，runtime有fresh last_seen及正常endpoint/token attachment。

未再次启动API，未重启/停止原Client服务，未发reprovision、未建幂等键/receipt、未扣款。目标已自动恢复且出现current_task，重复reprovision不再必要，会干扰当前任务，因此不执行多余部署。原恢复目标已达成，不将未调用这个可选恢复动作作为人为阻塞。

脱敏回执及SHA256已归档。该结果不证明旧Client具有新多媒体能力；仍需实际版本/能力读回、完整配置与版本化安装，避免打断目标现有任务。原API/身份恢复授权阻塞已关闭。

## 14:30 线上配置缺口收敛

只读生产catalog确认snapshot/bootstrap两表均不存在，新0a4d将走缺表初始化而非已存在CHECK比较；没有实证表明线上存在本次关注的格式drift。binding1/15均ONLINE，但当前都由同一个旧版共享Client服务刷新；独立local unit inactive，且运行版没有新typed INSPECT/V3生成/编辑声明，不能把两个ONLINE目标当作双模式新功能验收。

真正必须取得的外部信息只有已授权图片服务的HTTPS origin、精确model、Images权限凭据的私有引用以及生成/编辑HTTP合同。平台binding/epoch/issuer/revision等由Operator冻结，不再作为向用户索取的上游凭证。下一步仅向用户询问图片服务配置位置，不重复请求已授予的开发/恢复许可；其他升级/模式切换计划继续准备，不打断实际在途任务。

## 14:39 恢复后真实浏览器基线

Main使用系统Chromium与私有profile，旧登录失效后通过真实登录表单重新登录指定测试账号，成功打开聚义厅和点将册，并以截图实际检查。公孙胜/吴用均展示“候命”，但无新生成/编辑能力（公孙胜未录本领、吴用仅旧能力标签）。因此runtime.current_task非空不能单独证明真实在途任务，已交Runtime Owner继续结合执行状态/lease判断升级互斥，不用陈旧字段制造无限等待，也不凭UI状态抢占。

本次未提交需求/点将/模型调用/验收，未修改既有事项；只是旧部署恢复后的真实浏览器基线，不计34项新功能PASS。自有浏览器已正常关闭，截图留私有路径，仓库只归档脱敏结论与摘要。

## 双模式真实工程缺口继续实施

Runtime最终只读确认旧current_task没有对应任务/成员/work-item/有效lease，不再据此禁止升级；但共享service子进程归属仍需运行Owner核对。现有生产installer/launcher不支持独立实例且通用PID匹配不适合多实例，已安排独立Client Writer实现隔离安装/控制，不因Provider配置缺失停下可做工程。详见client-instance-rollout-20261002.md；同共享service两个profile不能充当双模式验收。旧profile忙时reload会退出全进程，不把hotreload包装成安全drain，当前无生产迁移动作。

## 15:00 完整API私有候选的本地静态收口

Runtime Owner已按既有存储根和两目标scope填入可确定字段，Main指定的平台binding/epoch/issuer/revision进入私有候选（0600）；候选SHA256 `cfc59ed071fd27b429b07f71dabbc088fe687152d8d27cd35207f2102119f29a`。Main独立对照0a4d完整应用fixture启用键，脱敏配置索引覆盖全部相关true/fullFeatureWiring开关。此检查仅证明键覆盖，不能证明值有效或运行就绪。真实origin/model/custody/Images凭据来源及HTTP合同仍MISSING_EXTERNAL；expiry在激活时冻结。候选保持NOT_READY/INACTIVE/DO_NOT_INSTALL，未复制秘密或安装到线上。

## 15:19 实例fixture越界事故，40a1候选暂停提升

实例Writer报告早期空slug测试误走默认共享安装路径并写入生产root，称current/launcher已恢复，留下release-目录。即使没有systemctl重启，这也是真实生产文件写入，不能称为“未执行生产安装/无生产影响”。该候选40a1尚未合入feature/develop；既有Client pin仍407db0a。

Main独立只读核验：current指向原20260926104830-29fda32，agent-client摘要与先前只读记录一致，service MainPID3274483/启动时间13:47:56未改变，API仍HTTP200/UP。其他compat链接、权限、私有状态和launcher写前基线尚待授权Runtime Owner核验，不能宣称完整恢复。Main没有删除目录或操作服务。

根因已有具体证据：TEST_MODE可省略隔离路径并回退真实APP_HOME/bin/systemd/systemctl；空slug最初又被当未选实例。要求在任何副作用前强制私有fixture-root与控制stub的完整约束，不能只修slug。该检查仅针对实事故的测试隔离，不给正常发布新增任意门禁。Writer已停止测试/提升并提供事故清单；独立运行custody Owner仅核验/恢复可证明属于本事故的路径，不处理其他release/进程。

## 15:37 越界残留有界清理完成，隔离修复仍在进行

Runtime Owner完成精确release-归属冻结和无外部引用检查后，仅删除该事故残留；Main独立readback确认目录不存在、current/active client摘要与旧基线一致，service PID3274483及13:47:56启动时间未变。未重启、未reload、未调用Provider。恢复launcher匹配407db0a及历史源码，但事故前线上launcher摘要与全部私有文件内容摘要不可追溯，保持NOT_PROVEN；这不是全量byte-exact恢复证明。配置/状态mtime早于事故，compat links实际曾被重建，均如实记录。

实现Owner正修TEST_MODE最早fail-closed私有fixture约束。Main静态检查发现全量installer仍需封住宿主npm fallback/cache/env出口，已反馈Owner；未执行该未冻结候选。40a1仍不提升，Client集成pin维持407db0a。脱敏恢复回执、Main静态检查快照及其局限保存在client-instance-fixture-incident-20261002证据目录。

同测试账号仅检查最新两条既有“画一只鸟”就绪交付元数据，均为document/summary（可见MIME为PDF），无tool/model/provider/endpoint证据。未读内容/存储URI、未下载或重放；不能推断其为Provider生图或静态绘图。现有Images origin/model/合法凭据引用/合同缺口未由历史查询解决，不虚构配置继续发布。

## 15:47 Client实例源码隔离修复已合入

最终3619d33d575a3b8b2c535214edbdf0cfc2740acb/tree cc166acb7177bb3bc0d18f893bdf05f934c8e194已byte-exact FF到Client融合feature并push/readback；包含40a1实例实现与后续fail-closed修复，不提升孤立40a1。Main核验clean tree、407祖先、48个payload字节摘要、installer摘要和diff。TEST_MODE要求私有fixture、全部路径/cache/HOME及显式工具stub，禁止宿主控制fallback。

Owner实际无特权UID99/env-i执行实例42pass；日志为事后终端导出（同期原始stdout未落盘），明确保留限制，不伪称原始制品。受影响workspace-manager installer子集另有原始日志10pass/35按selector排除/0fail，复用本地依赖，无真实npm或联网。manifest为最终源码静态重建，不冒充已清理fixture原件。证据见client-instance-3619-20261002。这里只关闭源码/隔离修复，双模式运行、真实Provider配置、正式发布与34用例仍未完成。

## 2026-10-02 用户纠正：优先复用Agent原生绘图通道

用户明确指出已有“gpt-image-2.5”，要求先核实现有Agent接入通道/绘图工具；**独立Images API或另建图片服务器不是业务前置条件**。此前把受控HTTP适配器所需origin/model/key当作全功能唯一出路的门禁撤回，相关历史NOT_READY仅适用于那份HTTP配置候选，不证明现有Agent无法生图。仅在实际通道核验失败且无可复用路径后，才列具体缺配置，不预先要求新凭据/新服务。

Main实际源码核验（Client3619d33）：agent-client.mjs已有runNativeConversationImage及CODEX_IMAGEGEN_NATIVE_V1分支，使用既有runCodex通道，接收生成结果后校验真实图片字节并物化到私有run目录；不是从零新增Images API才有执行入口。当前能力声明只列GENERATE_IMAGE；结果解析只接受顶层image_generation_call/completed/base64，单测为合成事件。因此“已有源码路径”不等于“实际账号工具可用”，还须核实际CLI/app-server事件、参考图编辑能力、认证通道与V3授权/幂等/upload链路适配。

只读发现顺序：目标Agent实际binary/version及tool schema→既有账号工具/能力声明与合法认证通道→确认真正返回结果形态及生成/改图路径→形成最小适配范围。主控自身image_gen工具不替代目标平台Agent；MCP列表或models列表未列图片模型也不能单独判定原生工具缺失。Fast CHAT不因此加载或执行绘图工具；生成/编辑仍按已有业务授权及execution/lease/产物校验办理。

模型证据纠正：用户裸名称gpt-image-2.5保持原样等待实际通道验证；侧聊和Main内部通信一度提及的flare/sunburst及“官方确认”均不采信。本轮web未得到可复核正文，直接抓取官方页面返回HTTP403；这些不足以证明型号存在或不存在，不写入运行配置。用户本次通知不新增付费授权，也不授权触发Flow/改运行配置/接管进程；本轮未作这些操作。原共享服务OTHER_SCOPE维护归属是独立问题，不与绘图服务配置混为一谈。

## 2026-10-02 既有Agent通道只读实证

目标实际Codex0.159.2（binary SHA256 1748767b230ebfc3d4ab7e4e254920d0c0ad9691fd8c11f190e7d44511a4a92e）含image generation/edit内部类型；两目标使用既有custom Responses通道。尚未证明账号图片权限，但也不能因未另配Images API判不可用。实际风险收敛为CLI事件合同：Client期望顶层Responses image_generation_call，binary静态exec序列化目录未显示该item，已有正向fixture系人工注入。下一步用自有隔离app-server/schema作零模型调用metadata readback，确认准确事件及生效工具配置，再决定最小适配；不先改模型/endpoint。

证据：native-image-channel-discovery-20261002，Main核验receipt摘要8d95f760。Owner回执末段“另行授权”不能成为重复确认门槛：此前既有额度内真实生成/改图授权保留，本轮先做零调用发现，不新增付费范围。shared runtime维护归属仍单独处理；尚未触发新Run或运行配置变更。

## 2026-10-02 原生工具请求归因：真实调用与离线捕获分开记录

实际0.159.2 app-server零模型调用readback显示`imageGeneration=true`；public产物合同为`item/completed.params.item.type=imageGeneration`，不能用现有人工顶层`image_generation_call` fixture代替。既有额度内一次实际主模型调用HTTP200且turn completed，但agentMessage为空、imageGeneration=0，无图片字节；未继续EDIT、未重试，具体原因尚未知。序列化回执失败发生在请求完成后，离线修复不算第二次Provider调用。

一次真实认证GET既有proxy `/models` HTTP200，目录列出用户指定`gpt-image-2.5`及flare/sunburst字符串；仅证明该私有通道广告这些ID，不证明官方身份、别名关系或生成权限。用户随后给出root auth文件位置；仅确认key存在及权限0600，未把key值写入证据/仓库，也不因此新增付费授权。

为避免重复消耗额度，Owner使用dummy key及无路由private network namespace对同版本CLI作capture-only：仅一次本地POST `/v1/responses`，主模型`gpt-5.6-luna`、tool_choice=auto，工具为request_user_input/get_goal/create_goal/update_goal/tool_search/web_search。**初始请求未直接包含image_generation或image_gen**。Sink故意返回400 diagnostic_capture_only、forward=0，不是实际Provider故障。临时auth已删、自有进程无残留。

结论只缩小问题：能力广告不等于初始直接工具声明；尚须排查tool_search延迟暴露及模型/auth/provider工具装配条件，不能把初始未列图片工具直接宣布为账号不支持，更不能转而强制要求另一套Images服务。已交Runtime Owner继续零Provider离线核验；API Owner只读拆分原生generate/edit业务不变量与HTTP专属契约。暂不修改运行配置/触发Flow/部署。

归档：`integration-evidence-20260928/native-image-request-attribution-20261002/manifest.json`，Main逐文件核对5份脱敏receipt/JSON SHA256。零调用能力、真实调用无结果、远程模型目录、dummy离线请求四类证据保持独立；全部不是34项产品验收PASS。全目标及共享服务OTHER_SCOPE custody边界不变。

## 2026-10-02 既有Codex图片skill实际生成与编辑成功

用户要求优先使用现成skill后，核实系统imagegen fallback受宿主Python3.6/缺SDK影响不能直接运行；另一已安装`gpt-image-api`为stdlib实现，读取现有Codex配置/认证，实证endpoint匹配原有通道。没有新增图片服务器、key或独立付费账户，也没有修改skill。

Runtime Owner使用用户指定`gpt-image-2.5`完成一次JSON GENERATE和一次以前稿为输入的multipart EDIT，均exit0，重试/fallback为0。生成PNG 1,940,751bytes，SHA256 `299c28a43a9d4a78db765a278109477393e29c75608c7d12c59d9b00674e8c17`；改蓝PNG 1,770,240bytes，SHA256 `74c1dd1aab92a5e6a80e6a574d9694b51c186d59cfe7a036ea2edede8af53243`。实际两图均1376×1143，与请求1024×1024不同，记录真实尺寸而不伪称size参数被严格执行。Main独立校验文件摘要/字节及view_image：同一鸟姿态、枝条、背景与构图保留，橙色胸部等羽毛改为蓝色。

模型结论仅为该私有连接接受此请求model并生成/编辑有效图片，不证明公开官方型号或底层模型身份。原skill未保留HTTP成功码/响应结构/b64与URL来源，维持NOT_CAPTURED；不能据此证明现有Client3619的JSON `images[].image_url`及严格data[0].b64_json parser兼容。Main已安排一次materially different现有V3执行器JSON编辑诊断、捕获脱敏响应结构，失败只离线replay不盲重试。

产品路线回到复用已有Agent接入+现有受控执行/upload/媒体/归档/验收链，不以新native authority迁移作为人为发布前置。是否需要HTTP payload最小适配待该真实结果决定。生成图片保留Owner分享输出路径，Git仅归档脱敏receipt及Main核验摘要：`integration-evidence-20260928/existing-codex-image-skill-20261002/`。此成功关闭“现有通道完全未知/不能生图”的缺口，不关闭平台34用例、双模式custody、正式版本发布与线上验收缺口。

## 2026-10-02 真实V3执行器请求定位并修复响应兼容

Client3619现有V3执行器的一次真实JSON EDIT请求HTTP200、direct response且返回有效PNG；因此无需推测或切换multipart才能接通。实际失败来自data[0]包含`b64_json,generation_id`（后者为string），旧parser要求只含b64_json而拒收。Provider调用1次，retry/fallback0；这是私有诊断而非平台lease或任务，不能计产品验收。

Main独立Owner最小修复两个同构HTTP executor：允许已观测的非空string generation_id并仅作为不输出的opaque metadata，图片base64/PNG/大小/唯一结果、身份和持久claim不变。新增正向、畸形metadata、替代URL/输出身份、重复调用负向回归。旧源码2个正向均RED；修复34个executor用例PASS。扩展子集首轮缺yauzl导致49pass1fail，复用既有360KB本地依赖到自有树后54pass，不联网安装、不运行build。

真实响应投影仅保留原b64、保留generation_id键/type并脱敏值：同一projection旧V3拒绝、新V3成功，输出1,764,364bytes/SHA256 `fea5ee52d8acf25ba86b3053bee1798e81cb3f73e3e56c021536bed7aef5415c`与真实Provider图一致；第二execute在fetch前被原claim拒绝。该修复验证0额外Provider请求。

Client融合feature已FF/push/readback `d170c9778c51a14852b39ddc772e53d95d292d72` / tree `8f7349ec2823ecc6d10e23cab73036938b4a6098`，祖先3619保留。证据`integration-evidence-20260928/client-image-metadata-d170-20261002/manifest.json`。Runtime Owner下一步完善既有通道私有激活候选与版本化部署步骤，重核共享服务custody；当前没有生产配置写入、service操作或新Flow Run，未发布/未验收。

## 2026-10-02 托管模式图片能力映射修复已源码整合

实际发现managed继承函数一律清空controlled-image配置，不能把“有配置候选”当server模式可用。责任critical Owner新增Operator私有`AGENT_MANAGED_IMAGE_SCOPES_FILE`映射，精确匹配tenant/client/owner/agent/generation/profileId；完整endpoint/keyEnv/model/binding/epoch/ledger来自私有Operator文件，拒绝继承共享默认凭据/绑定，错scope和重叠ledger关闭。Managed请求不取得新增授权。既有local及未配置managed行为保留。

Client `5ec83789d1fe603cd339ba22c332c4a0bebb5f87` / tree `80aa58cdaad96d2a82e0eb30f36322df3786b47f` 已基于d170 FF/push/readback。Owner194pass/0fail/0skip（8selectors），包含scope错配/目录重叠/配置私有性及真实registration/poll组件组装；0Provider/0build/0deploy。初轮依赖缺失、后轮payload count应由48更新50的真实失败已在selfcheck归因，未掩盖。Main核验10份源码hash、原始测试与静态日志hash、父/tree/clean状态，不重复全套测试。证据`integration-evidence-20260928/client-managed-image-scope-5ec-20261002/`。

Runtime Owner正在将inactive候选更新为5ec并用实际loader核对scope/预期UID/权限；没有向生产复制配置。API0a4d新JAR与旧JAR恢复副本已在Owner独立0700 staging准备，Main独立核对完整SHA b4e53624…9824与632012a3…5fad及SHA256SUMS，实际两文件总505,785,550bytes，未新增固定余量门禁。staging不等于安装。

共享Client维护会短暂影响lujunyi/linchong等非本次测试目标；Main已就这一个额外范围向用户明确一次维护窗口请求，尚未收到答复，不重启/reload/profile-write。普通API/Web版本发布沿用既有授权，不重复确认。最终Web同Run候选已生成但仍未Update/Start；正在核对被调用现有installer的门禁策略与真实package_version（c74为1.0.1，与历史产品release label不同），未提前冻结1.13.48或声称已发布。完整34项产品验收仍待真实部署后执行。

## 2026-10-02 用户指定技能改为 gpt-image-cli

- 后续图片技能入口改为 `/root/.codex/skills/gpt-image-cli/SKILL.md` 及其 `scripts/run.py`，不再以 `gpt-image-api` 作为新调用入口。保留历史诊断回执，不把旧技能成功改记为新技能成功。
- 保留用户指定请求模型 `gpt-image-2.5`，不静默改用技能默认模型；本机原装 CLI 的模型校验接受 `gpt-image-` 前缀，但这不证明实际服务模型身份或调用成功。
- 复用已授权的现有配置/本地 auth，密钥只经子进程环境传递；不新增图片服务器、账号或付费授权。此次技能切换不发起生图，不改 Flow、不重启共享 Agent。
- 本机检查发现技能示例环境 `/home/isp/wsps/daily/.venv/bin/python` 不存在；系统 Python 为3.6.8，`uv python find '>=3.11' --no-python-downloads` 未找到可用解释器。技能 wrapper 依赖 Python3.11+（tomllib）；尚需为本项目准备隔离运行环境并执行 `--check`、generate/edit `--dry-run`。不得复用其他项目授权或修改原装系统 imagegen CLI 来绕过限制。
- 平台接入仍须保留身份/执行权限、输出登记和工作空间边界；开发会话使用技能不等于平台 Agent 已部署该能力，也不替代全部34项验收。

## 2026-10-02 19:32 CLI源码与发布准备收敛（未部署）

- 用户指定的 `gpt-image-cli` 已真正接入 Client `aedcd3da12543f588f85f4678898f4ac3ea777b4` / tree `63cf84799ca22c297167c27f0e143e57852179ed`，以非force FF 推送融合feature与develop并readback一致。使用原装runner/imagegen/verifier，不修改系统技能，不把直接HTTP改名冒充CLI。一次性loopback出口保留START/持久claim/身份scope/上传提交；SDK内部重试不能变成第二次Provider外发。
- 原装Python CLI+本地fake upstream实测82项core通过，安装打包64项通过，0fail/skip；真实Provider0。Main核对18源码摘要、parent/tree/clean及原始日志。该证据是Client源码/离线执行，不是正式平台或真实账号生图验收。
- 隔离Python3.11.13、SDK3.23.0、Pillow12.3.0已准备；原skill12测试和generate/edit dry-run通过。冻结技能18文件摘要和只读权限已独立核对。必须保留venv invocation path；resolve后的基础Python没有SDK，已用失败/成功对照定位并归档v2更正。无auth/config复制入技能快照。
- 最终前端同Run候选SHA `9a4043e26a1abcd0b22e785ff9710e45221944376d2470516068b0af3faa4ea4` 已冻结，包含3个既定UI flag、同Run helper+dist与恢复路径。19:06 live配置仍为f948…、无VMDeploy；没有Update/Start。历史Run150不可重标为本次最终发布。
- 浏览器验收工具 `88398dfa` 修复签名URL脱敏与操作失败后继续执行的问题，离线行为自检通过；34项产品用例保持NOT_RUN。不是新Reviewer或人工审批门禁。
- Runtime Owner正在验证exact aed的私有inactive配置。共享Client维护请求尚未获答复，不重启或改共享profile；普通API/Web发布授权不重复申请。`1.13.48`仅候选产品label，最新只读release refs确认未占用，尚未创建release refs；Web包实际仍1.0.1，公开版本不能由旧部署记录推断。

## 2026-10-02 19:44 实际托管身份长度缺陷阻止运行激活

Runtime Owner用exact aed及真实binding scope构造：local binding1通过；managed binding15的scope loader和CLI路径/摘要通过，但executor/ledger把完整canonical profileId（130字符）按普通SAFE_ID的100上限拒绝。此前146项离线测试通过并不能证明该真实托管身份可运行。已保存原始脱敏失败回执、记录首个root cause并交原Owner修复；不截断/替换身份、不任意加大上限、不重跑未变输入。ledger物理目录已有完整identity hash，继续保持；同时核对claim字节界限的推导。

epoch1仅私有Operator候选，不是服务端真实授权/lease。真实key未加载，Provider/native/poll/execute均0，无profile/env/服务写入。共享process.env的秘密对同进程可见；exact capability scope隔离不等于per-profile秘密存储。维护授权边界和全部34项NOT_RUN保持不变。

### 旧5ec私有readback证据范围更正

Main只读旧probe确认其注入了`createLedger/createExecutor/createPollProtocol` stub，因此过去的PASS仅支持真实scope/profile映射、精确参数传递及registration投影，不支持实际ledger/executor构造或托管运行就绪。旧源码194测试仍保留原结果；不将配置投影成功扩写为真实执行成功。新aed候选用真实构造才暴露130/100冲突。保留所有旧原件，仅追加 `old-5ec-probe-evidence-qualification.json` 限定证据范围，无新增Provider或运行操作。

## 2026-10-02 19:58 canonical managed身份修复已合入

Client `5bcb16bd8e2cf9a2fde50ac114367ae272c0335f` / tree `e195b7fb150c3d45adc512e876cb4516de785b5b` 已非force快进feature和develop并远端核对。按实际ManagedHost身份生成合同推导最大159字符，普通ID仍100；不截断身份、不变完整身份hash目录，同步推导ledger读界限。Owner91项通过、0fail/skip，真实130字符binding15离线构造通过；Main核验7源码和4日志摘要及父/tree/clean。Runtime Owner正独立重新探测，不把Owner离线通过替代实际运行授权/连接。Provider0、未安装、共享维护授权仍未获答复，34项产品验收仍NOT_RUN。

### 2026-10-02 20:05 独立inactive运行构造复验完成

Runtime Owner已留下新版真实默认构造probe及PASS回执，随后工具终态为model capacity error；Main直接核验现有证据，不重复重跑。源快照102文件与exact5bcb逐字节一致，local1/managed15真实ledger/CLI executor/poll protocol构造、registration投影及私有ledger持久化/replay通过；Main独立核对两份claim摘要与完整身份长度。无factory stub，scope mismatch拒绝。首次缺yauzl已通过现有同package/lock依赖只读绑定修正，失败原件保留。只证明inactive配置构造，不证明线上授权/鉴权注册或Provider；未写运行目录/环境/生产profile，未操作服务，epoch1仍候选。共享维护授权尚未收到，34项平台用例、同Run正式发布仍未完成。

## 2026-10-02 20:10 用户统一授权与版本候选冻结

用户已明确“统一授权”，此前共享服务维护授权缺口解除。不重复确认，不扩大到新付费资源或无关生产数据；原Runtime Owner接续fresh核对和可恢复激活。三个组件均先查release ref不存在，再非force创建并readback `release/1.13.48`：API0a4d/Webc74/Client5bcb。这是冻结候选，不是发布成功；Web实际package_version仍1.0.1。证据 `integration-evidence-20260928/release-1.13.48-freeze-20261002/candidate-freeze.json`。Frontend Owner仅获L1单次配置更新并readback，不Start；正式Run等实际运行依赖就绪。全部34产品验收仍待执行。

### 2026-10-02 20:31 API已可恢复激活，尚非整体验收

Runtime Owner于20:24激活API exact0a4d，制品b4e53624，PID3506165，功能properties摘要9a53e3f4；Main20:31独立核对已安装JAR完整摘要、六controller归属和HTTP200/UP。首次argv空格/NUL断言错误和第二次实际ENOSPC均发生生产变更前，原归因保留；仅清本任务失败临时inode，复用已验证同fs候选完成切换，不删foreign文件。真实Chromium新隔离profile使用测试账号登录并返回聚义厅成功，但仍是旧前端，未发需求/Provider，不计产品验收。Client迁移/共享重启及正式前端同Run部署仍待完成；34项NOT_RUN不变。

### 2026-10-02 21:19 Client激活与正式Run151

共享Client5bcb已由原Owner完成单次重启，PID3521733，lujunyi/linchong/binding15实际registered；原Owner随后model capacity终态，Main依据统一授权接手剩余本地实例。fresh零实际lease、旧共享wuyong offline、五份配置/凭据引用摘要匹配后，Main单次启动独立wuyong-local，PID3527199，观察到真实registered和DB presence。未双注册，不重复共享重启。此前DB helper从abilities字符串推断V3能力并不正确：V3声明保存在会话，不能从该字段false断言缺失；旧V1 capability unavailable同样不代表V3失败/成功。实际V3业务仍待验收。

前端正式Run151于21:10单次启动，实际checkout c74已官方核对，扫描成功、测试/构建仍运行、部署INIT；非历史150制品。冻结版本1.13.48尚未声称整体上线或验收。

### 2026-10-02 21:33 两个独立实证失败待修

官方Run151终态FAIL：build527428900失败、scan成功、deploy527428902未启动。完整日志归因由Web Owner执行，Main未retry/start。真实浏览器已登录账号对既有local/managed悬赏会话的V3 interactions/context各一次GET均503 BOUNTY_FOLLOWUP_V3_UNAVAILABLE；不是此前legacyV1不可用的推断。context只读事务内部调用锁定读为待验证嫌疑，原critical Owner正在隔离树精确归因和回归，不擅自改生产数据。两者不得互相归因；未发新生图/验收请求。证据 `integration-evidence-20260928/release-1.13.48-live-failures-20261002/`。

### 2026-10-02 21:48 修复候选与真实只读事务诊断

Web固定DNF墙钟门槛修复7aaca891/tree71c0536已两文件最小自检并FF推fusion feature；保留签名/RPM/allowlist/真实失败及Flow取消，只有dnf/yum显式timeout0。全bootstrap18项通过；最初17/1来自Owner sparse树未materialize已跟踪fixture，已恢复精确blob并更正，不能写成源码缺fixture。develop及冻结1.13.48仍c74，等API关联修复就绪再统一候选。

API5c5580是待实际targeted测试候选：context改普通事务保留全部锁和零业务写，H2/Spring测试仍在执行准备。Main补真实MySQL零行只读诊断：普通WHERE1=0 SELECT通过，同SQL FORUPDATE被拒SQLState25006/vendor1792，回滚完成、DML0/数据行读取0。这验证部署数据库只读事务与锁定读冲突，但不冒充原HTTP异常stack或修复上线证明。既有ledger已向责任Owner开放targeted_verification，不把缺新增任务当行政门禁。

### 2026-10-02 22:15 context修复源码、打包及空间故障处理

API5c5580/treea0e84已定向6项通过并非force推develop。测试为真实Spring事务代理/REQUIRED传播配合mock DAO，不声称H2实际锁SQL通过；真实MySQL诊断证据范围仍如前述。正常bootJar依赖66项通过，但首轮写包实际ENOSPC；仅删除Owner无效partial，未盲重试。Main确认本任务旧b4重复source/staging同inode、摘要一致且无打开FD后，保留独立live inode并建立恢复硬链，释放253586846字节，可用空间由249696256增至503300096。改变资源条件后单次重试成功，187任务中186 up-to-date，复用原测试证据。

新制品d5c7fb9a/253586852字节，仅chat-service内部context类变化；Main独立核验source/tree/clean、制品及日志/差异报告摘要。冻结制品从build输出MOVE至本次Main staging，无source软/硬链残留，避免后续build写穿运行inode。22:15已在fresh四Agent零实际lease后进入本线程API可恢复安装，尚待健康和真实V3 GET核验。Web7aaca仍待统一推develop/新Run；34项整体验收未通过，不将打包成功写成发布完成。

### 2026-10-02 22:20 API就绪、1.13.49冻结及正式Run152

API5c5580/d5c7fb9a在独立Main scope安装完成，PID3558818、健康UP、实际启动62秒，原properties与launcher摘要不变，旧b4可恢复文件保留。重启后浏览器旧token GET为401/空体，重新通过真实测试账号表单登录后，两条旧会话context均409 BOUNTY_FOLLOWUP_V3_CONFLICT；此前503消失，但不将旧任务合同冲突当新任务200/生图验收。

Web7aaca已非force合入develop，三组件新release/1.13.49分别固定API5c5580/Web7aaca/Client5bcb并远端readback，未移动1.13.48。完整分页确认没有push自动新Run及活动Run后，Main22:19:15单次Start返回4403172/152；参数{}，raw及canonical配置CAS匹配。实际checkout、云端tests/build/artifact/deploy和34产品用例仍待观察，不能仅凭目标SHA宣称部署。共享Client授权/激活ledger旧文案已纠正；统一集成归Main MMD-U4条目，避免重复active Agent归属。

### 2026-10-02 23:08 Run152测试/构建通过，部署派发故障待归因

官方actual checkout7aaca与预期一致。test/build527459231 SUCCESS、scan527459232 SUCCESS；日志可见2873 passing/2 pending、E14 passed、Vite11.07s和364file manifest。more=false但本地safe reader输出截断，未声称日志全文完整。DNF已成功完成，不再是151旧超时根因。

同Run制品path aone2/2049636/1790952434215/cyf_web_flow_4403172.tgz，106568069bytes；Owner内存流式SHA-256=14cb69357b2abe28fa9f88854ab23b8c22d9889d490fe2e7860a58446397ac23，不写本地重复包。部署527459233 FAIL/order70590729，hostgroup28833唯一机器clientStatus=unhealthy。机器日志API成功但deployLog空；本机无该rdc脚本日志、无downloads/152，未进入已知安装脚本。

与Flow状态不同，ECS DescribeCloudAssistantStatus=true且有当前心跳，CloudAssistant InvocationCount1309；本机aliyun.service原PID持续heartbeat200/newTasksfalse。hostgroup仍绑定存在的ecs连接149711，但ListServiceConnections不证明凭据有效/调用权限。DescribeInvocations=0仅当前本机AK查询视角，不得外推Flow连接无invoke。准确平台拒绝原因尚未知，不能归因本机服务失活、磁盘、安装器或voice。未重启健康共享服务/未盲retry/未重建；继续只读核对连接/机器状态差异，有据修复后复用同Run部署。34产品用例仍NOT_RUN，未宣称可验收。

### 2026-10-02 23:14 同Run安装输入独立复验

Main再次流式读取Run152实际包，不落本地tgz或解包树；压缩字节/摘要与Owner记录一致，source-tree精确71c0536，364个dist成员逐个size/SHA与release.json完全匹配且覆盖无遗漏，安装helper摘要匹配冻结be51。同Run制品确实可用于后续恢复，但不代表已部署。实际包106568069B + dist108224162B +最大文件2937819B =217730050B；此刻可用219103232B，余量仅1373182B且尚有helper/记录/并发写入，未来恢复前应fresh按实际占用核对，不能由这个时点保证足够。没有任意预留门槛/未清他人文件。

23:11官方部署单仍Failed/unhealthy。连接只读API实际仅返回createTime/id/name/type/uuid，无可验证的禁用/过期/认证/账号字段；不存在可用登录态或云效控制台connector。已请求用户提供主机组28833异常详情或控制台登录态（不是再次申请授权）。现有证据不足以安全修复平台健康状态，未盲改hostgroup或retry；等待外部错误详情，目标仍为完整发布及34项真实验收。

### 恢复执行后的独立点将准入诊断（原始采样时刻见回执）

Flow152部署故障仍未解除，但Main继续检查可独立验证的产品准入。真实已认证测试账号对既有task415 local/managed各一次只读capability GET均200：serverLaneREADY、controlledExecutionUNAVAILABLE、CONTROLLED_EXECUTION_DISABLED/OPERATOR_POLICY_UNAVAILABLE、authorization:null。直接读取j.data，没有把业务authorization人为脱敏。未点将/创建任务/调用Provider；诊断后关闭本线程browser。

用exactWeb7aaca原装load/parse函数回放该真实响应，两目标均MALFORMED；JuyiHall.vue assignTask2373之后的分支会拒绝办理。仅在离线对照恢复非null authorization对象后仍UNAVAILABLE，故不是单字段修复即可恢复整条链。默认SensitiveSanitizeConfig将authorization列为NULL敏感字段，是需要原Owner核实的实际过滤路径；不得为业务对象关闭全局秘密过滤。另需核对初始点将使用的旧ControlledImageExecutionSessionLookup与CLI仅V3ready声明之间的合同，不能再把旧V1 capability当与用户主流程无关。

原critical Owner已接只读归因/最小修复合同设计；这份证据是准入缺陷诊断，不是实际新任务完整操作，也不把34产品用例改成PASS。Run152制品仍保留，但即使部署恢复也尚不足以认定功能可验收。


### 2026-10-02 18:13 UTC 续记：Runner恢复、主入口纠偏和真实MySQL通过

用户重装既有Runner后，Main实际核验unit active/running、PID3630220，缺失配置已恢复；原派发阻塞解除。官方最近仍为152 FAIL，未重跑旧包、未新Start。真实浏览器又证明默认“提出需求”误入PRIVATE；Web修复4dc65cb/tree969db74已FF合Main feature，改走既有原子requirement-create及可选参考picker，补嵌入详情重入可见性回归；Owner58/46项定向通过，尚未推develop或云端验证。

API准入改根schema3/executionAuthorization与controlled V3；全局敏感字段脱敏未关闭。真实MySQL8.0.46暴露REGEXP BINARY与既有bin collation不兼容，修为保持严格小写hex的REGEXP，并仅规范化实证的三种固定字面量旧binary cast/_ascii表示；不移除CHECK。首轮DDL失败及第二轮_ascii规范化失败均保留。当前d85bc64/tree7280d0d：Main直接解析XML核对4+3共7个真实MySQL方法PASS、0fail/skip，另11个schema canonicalizer单测XML曾核对PASS；桥接XML随后被恢复测试替换，未保留独立旧XML副本，不虚填其摘要。

安装恢复已纠正旧manifest：旧5c初始化器严格比较完整列、索引和CHECK集合，不能直接声称会忽略新增列。实际旧jar类加载器与Spring条件注册2项测试证明，仅关闭bridge-enabled可避开不兼容桥接准入，保留其它初始化器及V3数据；这不是生产环境完整回退演练。Main已准备旧jar硬链和精确恢复配置，正常前向配置不关闭功能。新版本1.13.50仍是候选，未创建新release refs，1.13.48/49不动。证据见 [本次固定快照](integration-evidence-20260928/primary-v3-recovery-20261002/candidate-state.json)。正式制品交接、同Run前端发布和全34项产品验收仍未完成，不通知可验收。


### 2026-10-02 18:40 UTC 续记：1.13.50冻结、API安装及正式Run153

API d85bc64/tree7280d0d、Web4dc65cb/tree969db74、Client5bcb/treee195已非force合develop并冻结各自release/1.13.50，远端readback一致，未移动1.13.48/49。API正常bootJar66测试PASS；Main逐个核验37源码hash、制品a970ca4a/253595965B和ZIP CRC，build输出已MOVE到独立staging，无后续构建输出路径写穿运行inode。

首次安装新API已真实UP，但Main新增健康检查错误假设status为字符串，实际为{code:UP}，误触发自动回退；此为Main发布脚本错误，不归因应用、迁移、Runner或Flow。旧5c+仅bridge-disabled恢复配置实际启动UP，schema及V3数据保留。已按canonical launcher支持的status.code/string形状修复，并验证2份真实body及7项正负夹具；新目录、fresh PID/配置CAS下单次重装成功，PID3677903、制品a970、正常配置9a53均核对，健康UP。失败与恢复证据保留。

正式前端Run153于18:38:06 UTC单次启动；推送后及Start前均无自动新Run，配置未变。官方SCM日志完整commit4dc65cb已核对，build527570069和scan527570070 RUNNING，deploy527570071 INIT。不把expected tree或旧152制品当新Run证据。最近源码比较证明b9 voice三文件字节不变，已send_input通知voice协调Main。尚待同Run正式test/build/artifact/deploy、在线字节及完整34项真实产品验证，未宣称可验收。固定证据目录 [release1.13.50](integration-evidence-20260928/release-1.13.50-20261002/candidate-freeze.json)。


### 2026-10-03 03:07 CST：Run153正式发布通过，真实点将仍被400阻断

Runner重装后的4403172/153官方SUCCESS，actual source4dc65cb/tree969db74；2878 passing、2 pending，build/scan/deploy全部成功，部署单70593938唯一主机healthy。流式读取同Run制品106572406B，SHA256 7b4dd9f327ac717918b83073b1240409a40cff5a32066a3f68782273d76d4cf1；364个dist文件及helper逐一校验manifest无遗漏。真实已登录Chromium读取线上index与JuyiHallEntry JS/CSS，三者字节和摘要均匹配本Run制品。没有新增Run或重试旧152。

产品验收不等于发布成功：默认“提出需求”已创建无参考图task417“画一只鸟·1.13.50实测”，明确公孙胜后费用同意实际ISSUED；bridge POST400 CONTROLLED_IMAGE_BRIDGE_BAD_REQUEST，原请求GET404。一次原key/原正文诊断重放仍400，已停止继续重放；未生成鸟图，不将404解释为绝对无副作用。真实wrapper中expectedTaskVersion=0、requirementRevision=1、workflowVersion=2、consent expectedVersion为字符串1，已交API/Web Owner精确定位，尚未归因到具体校验行。详情仍含固定PDF文案/入口，是另一个真实UI缺陷，也已交Web Owner。全34项范围不缩减，当前不能通知可验收。证据见本目录release1.13.50/run153-release-and-product-status.json及run153-online-independent-verification.json。

03:10 CST根因补证：Main核对d85源码，ControlledImagePointAndStartServiceImpl.validate将expectedTaskVersion<1判BAD_REQUEST，而Controller明确允许0，真实新task417/current为0。即初建任务零版本的合同边界不一致；API Owner已收到真实wrapper和具体校验行，待最小修复及create→consent→bridge真实回归。两次原意图失败均写orchestrator归因，停止不变输入重试；有修复候选后才开启下一次验证，不把此局部门禁当整项目无法推进。

### 2026-10-02 19:38 UTC：零版本修复候选、前端1.13.51并行正式验证

API Owner源码372123e仅把受控桥接expectedTaskVersion下界从1改为0，保持负值拒绝/CAS/原意图；后续ae66af9增加真实MySQL新任务零版本submit夹具，实际测试/制品仍待Owner终态，不将mock Controller/service测试称真实产品通过。

Web9cbcbbe/tree7038ffb修正同任务已持久化controlledImageBridge路由在BOUND/清offer/详情重入后继续生效，不误露PDF入口；普通历史PDF任务保留。UNKNOWN显示真实message，不伪称拿到错误code。Owner47定向通过，Main两路径/FF/voice三文件字节一致核验，已非force推develop并新冻结release/1.13.51，1.13.50不动。该UI-only修复无新API合同依赖，故无需把API测试完成作为前端开跑门禁；完整153个历史Run核查无自动/活动后，于19:23:15UTC单次Start154。官方SCM确认actual9cb，build527587862 RUNNING、scan527587863 SUCCESS、deploy527587864 INIT；未声称发布完成。

只退役本Main终态Run153的本地重复下载包106572406B：互斥锁下核对record153、完整SHA7b4dd9f3和无打开FD后删除；线上dist/回退及远端同Run制品均保留。原API5c直接旧恢复文件也未删。后续前端安装和API新jar打包需按实际磁盘占用串行错开，不能同时消耗不足空间。真实task417原profile/原key仍保留且browser已关闭，修复部署前不再重放。AC01/FD02按实测标FAIL，其余NOT_RUN，完整34项不缩减。

### 2026-10-02 UTC 续记：保留154失败，修复断言后转新候选155

Run154 actual9cb最终FAIL：2878 passing、2 pending、1 failing。唯一失败为W06 personal-workspace-task-material-links.test.js:213要求旧裸v-if表达式，与新增图片分流guard不符；扫描SUCCESS，生产build未到达，部署INIT未启动，线上仍153/4dc。没有重跑原候选或移动冻结release/1.13.51。

Owner child3d9f9ae/tree9bee27f仅修改该测试，断言新的完整guard及持久化图像route依据，保留普通PDF/原议事事件约束；两个相关selector共55 passing。Owner磁盘受限sparse树显示413个未materialize D，不是文件系统clean，但index/commit无删除、三相关blob匹配；Main从commit干净FF，runtime src对9cb字节不变，不把缺文件状态当上线源码。已非force推develop和新release/1.13.52。全154历史Run核查无新自动/活动后19:44:44UTC单次Start155；官方19:46:19UTC仍RUNNING，build527596581/scan527596582 RUNNING，deploy527596583 INIT，actual checkout尚未读取，不假定已验证。

API ae66实际启动Owner独立MySQL和Gradle验证中；新增SQL测试包含真实consent/bridge事务写入，但task/legacy/grant/requirement存在mock，不冒充完整HTTP创建或产品验收。尚无最终新API制品/安装结论。Main已准备保留原task417/key/profile的恢复路径，修复未部署前不重放。

### 2026-10-03 04:18 CST：1.13.52 发布成功，真实点将后续链仍失败

Run155 actual3d9f9ae/tree9bee27f：正式云端2879 passing、2 pending，构建/扫描成功。同Run首次部署单70594579失败，Runner主机healthy且106574481B包已下载；installer笼统报invalid/truncated archive。Main独立流式验证远端包全382成员和SHA6084db34，本地包摘要一致，dist实际108225702B高于失败后观测可用78721024B。仅退役本Main旧5c二级恢复三硬链，释放253586852B，保留当前d85直接恢复与新8c8a；同一helper独立stage364文件/manifest通过，不调用publish。改变资源条件后仅单次RetryPipelineJobRun部署，无新Start、无配置变化、无重建：新job527607479/单70594763成功，唯一主机healthy，Run155最终SUCCESS。原失败保留；未捕获原始errno，资源不足归因来自完整包/实际空间/同helper补救验证，不伪造ENOSPC日志。

API ae66af9/treeea12b62独立核验源码/冻结JAR/内嵌类/真实MySQL XML后FF推develop并新冻结release/1.13.52；Client5bcb同样冻结52，旧release不动。API制品8c8ad5f1/253595968B，build_origin=local_user_authorized，正常启动52秒后PID3722320/UP，原配置9a53与launcher94de未改，准确Main scope与d85恢复副本保留。真实Chromium重新登录后，线上index、JuyiHallEntry JS/CSS三个摘要和大小全部与155制品一致。这里只声明版本安装成功，不把整个需求标released/accepted。

原task417/profile/key/consent均保留。真实UI继续原点将：POST201，grant ACTIVE、原consent BOUNDv2，零版本400已修；紧接着GET assignment-operation500 ASSIGNMENT_OPERATION_INTEGRITY_ERROR。后台协调在createConversation的validCreate/text报BAD_REQUEST，两次同因后relay停止，未把已创建grant视为图片生成成功。原API Owner继续联合归因read与coordinator，Main不再重复POST/provider、不清生产数据。AC01/FD02在52仍FAIL，其余NOT_RUN，完整34项不缩减；没有本次可交付鸟图。证据见integration-evidence-20260928/release-1.13.52-progress/，当前不通知可验收。

Run155终态后，Main在部署锁下核对record155、精确6084摘要及无打开FD，仅退役本地下载重复包106574481B，远端同Run制品、线上dist及API恢复文件保留；可用空间295305216→401887232B。后续验证仍可按远端同Run制品流式取证，不声称本地下载路径继续存在。后端候选51e62198/tree9a679ec4已包含read协议3绑定校验与多行instruction修复，测试尚在Owner原handle执行，未合入/发布；前端155无需为此重建。


### 2026-10-03 CST：1.13.53安装、原议事恢复，新增缺口已分派

API d355d455/tree d661691e正式本地授权制品04d1ad38/253596977B已于05:01:03安装并HTTP200/UP；develop及新release/1.13.53非force推送，旧release不动。read协议3绑定核验与仅instruction允许LF联合修复保持授权、CAS及其余控制字符约束。Main独立保留XML17项；Owner另报多行selector通过，但其XML已被后续同Task覆盖，不将该数字冒充Main独立XML统计。前端仍复用4403172/155实际3d9、2879pass/2pending及同Run制品6084，无API-only重复构建。

原task417真实assignment-operation GET从500恢复200，自动打开conversation1760458004760并显示原需求；bootstrap ADMITTED，尚无executionId/本次鸟图。05:00:50及05:00:55 CST协调器实际代理提交抛UnexpectedRollbackException，relay重复同因后停止。底层授权未就绪原因尚未确证，已交原API Owner做真实Spring参与事务RED/GREEN；不关闭rollback-only检查、不反复重启或重复点将。

05:09:33 CST真实UI单次选原持久消息1675335的codepoint0..4“画一只鸟”保存文字，业务POST400 CONVERSATION_ARCHIVE_INVALID_REQUEST；OPTIONS200不算成功。前端发CREATE/textSelection，现API只收create/items.assetRef。已交Web Owner核对既定文本归档合同和端点，再与API Owner冻结最小闭环；没有生成文本文件或重试。首次双击digest竞态仅源码疑点，另要求有据回归，不先认定实测缺陷。

voice独立Owner交真实VarIcon3.10.9/字体loaded/公网CSS实验：microphone/settings/stop名称无glyph，idle隐藏文字使按钮空白；不是字体未加载。Main独立核验共享结论SHA c214e9dd。已将三个明确18x18 inline SVG及非mock真实窄viewport回归分配voice Main唯一Owner，保留ARIA/布局/context/CAS/行为，统一候选后云效验证，不抢跑或另开发布。本轮全部34项范围不缩减，仍不可通知验收。

脱敏进度见 integration-evidence-20260928/release-1.13.53-progress/release-and-product-status.json；历史52矩阵保留当时失败，不用其500覆盖53恢复事实。


### 2026-10-02 21:54 UTC：1.13.54后端安装，前端156在跑，原需求仍未执行

API5fe27328/treeeb34b44、Webc4a2512/treed104074、Client5bcb均已非force推develop及新release/1.13.54并readback，旧release不动。Main独立核验API51项定向XML/66项正常打包图XML（含复用）、JAR4a35b084/253597460B/ZIP CRC和四生产class；对04d1旧JAR逐成员比对，仅agent/chat两模块JAR变化。真实事务回归使用Spring代理、参与式REQUIRED与H2写入证据，DAO仍有mock，不冒充完整MySQL/HTTP或线上生成。Python3.6验证helper首轮误用text参数，改为universal_newlines后通过；不是制品失败。

四目标fresh实际work/execution lease均0后，从验证制品可恢复安装。21:46:01UTC实际PID3793597/UP，启动57秒，配置/launcher不变，保留04d1直接恢复。原task417通过真实登录/查看进展再次GET200并显示原需求，无重复点将。当前request及step实际WAITING_AUTHORIZATION/stateVersion1、executionId=null；persisted grantACTIVE/consentBOUND并不证明当前准入tuple通过。新部署日志未再观察rollback-only，但底层实际denied原因未确定，原critical Owner继续查明并设计同意图恢复，不以永久等待冒充修复成功，不清状态或补一份新付费意图。

Web包含voicee586三inline SVG最小修复及text归档digest并发、身份/选区切换、卸载和digest失败本地重试修复；34voice与7text定向通过。Main检查f6候选发现未成形body:null可能重放，补c4a回归后才集成。Web旧textSelection payload尚未改合同，归档400仍未解决。完整155历史Run查询无自动/活动、配置3eed未变后，21:44:44UTC单次Start返回156。21:54:28UTC官方source确认为c4a及f6/e586祖先，build527641071RUNNING、scan527641072SUCCESS、deploy527641073INIT；没有云端通过/制品/上线结论，当前线上仍155。已向voice Main发送source/Run通知。

按实际空间顺序，只退役Main已过时d85及ae66二级副本硬链；Owner各自退役其链接后，Main锁下核对摘要/inode/nlink、无FD、当前健康与直接恢复再删自己的链接，保留全部报告。最新一次回收253595968B，可用53665792→307326976B；不清foreign文件，不设置任意预留门槛。54浏览器首启误读旧DevToolsActivePort而ECONNREFUSED，确认无遗留自身Chrome后改为等待新端口记录并就绪核验，原profile/意图保留，未重启共享服务。

当前34矩阵：AC01 PARTIAL、FD02 FAIL、AC12 FAIL，其余未实测，不通知可验收。脱敏依据见integration-evidence-20260928/release-1.13.54-progress/。

### 2026-10-02 22:18 UTC：Run156成功发布，线上图标已确认；刷新恢复发现真实缺陷

Run156官方22:02:27UTC终态SUCCESS，exact c4a25123/tree d104074；build527641071、scan527641072、deploy527641073全SUCCESS，云端2887 passing/2 pending；部署单70595823单批唯一主机Success/healthy。106578156B同Run包SHA256 5cafe1d542cad1ff9596e7e2739ad40e4fc26f87b385265fc9e6f94f7a157fd9已完整流式读取382成员，364个dist文件逐一匹配manifest。22:04:37UTC真实浏览器线上index/JuyiHallEntry JS/CSS三文件大小及摘要匹配。没有为验证重新build、Start或更改Flow配置。

22:15:26UTC明确进入task417已指派公孙胜的议事页，仅检查部署控件，不发送消息/点生成。实际麦克风与设置均为18x18 SVG、paintBBox非空、aria-hidden=true/focusable=false；Main已view_image确认可见。未开始录音、不宣称stop控件实际设备或Provider验收。已通过send_input向voice主控发送正式终态及线上实测。独立合并核验证据SHA256 ed52190950fe844d2007f5ac25c6cd1a20b0f6c18512fec866ff17297b78a341。

真实刷新后用户资料未hydration：保留owner/client但tenant空，当前scope由tenant/client/owner退为client/owner，与原task417持久意图不匹配。因此“查看进展”不读取原assignment，错误展示旧PDF办理区。只读核对原意图仍为ADMITTED且有controlled bridge；没有跨scope复制/扫描恢复、重复点将或生成。独立critical Writer已接最小身份恢复与隔离/race回归，尚未交付/发布。手动进入议事仅用于图标检查，不能替代自动恢复验收。

34项完整矩阵继续保留：AC03的刷新子例FAIL；AC11生成媒体/断线/乱序子例仍NOT_RUN（没有媒体），标注恢复前置缺陷；AC01 PARTIAL、FD02授权等待FAIL、AC12文本保存400 FAIL维持。整体仍未可验收，task417尚无鸟图；后续先修原请求授权/能力分类与身份恢复，保持同一意图继续。

### 2026-10-02 22:43 UTC：身份恢复最小修复进入Run157；保留原请求恢复要求

Main真实只读GET `/user/my` 200确认服务端仍返回同用户及字符串tenantId="0"，不调用setUser、不改localStorage。独立critical Owner提交3bad445/tree7e4020f：根据完整服务端profile判断hydration，不因缓存userId跳过；scope必须tenant/client/owner齐全、保留数字/字符串0；不猜租户或迁移旧scope；异步身份generation/卸载变化阻止继续初始化。5路径限定JuyiHall、helper及相关测试；Owner定向17+26=43通过/scoped lint通过（缓存记录无原始输出文件，因此不称Main独立复跑）。Main检查精确diff与parent后FF，非force推Web develop及新release/1.13.55，旧release未移动。

全156历史Run均终态且配置3eed未变；推送后再检查自动Run，22:42:12UTC单次Start返回157。22:43:10UTC正式状态RUNNING，build527664460/scan527664461 RUNNING，deploy527664462 INIT，sources.commit仍null，不能把目标3bad视作已checkout。API仍1.13.54/5fe，Client5bcb未重启；这是独立前端修复发布，不为未完成的后端凭空增加发布等待依赖。

Main只读验证当前managed绘图配置：部署模块的HTTP/CLI resolver均通过，凭据存在且CLI pin匹配；公孙胜实际roster online。无Provider调用、配置修改或重启。该证据不等于live能力lookup就绪，更不等于已经生成鸟图。API Owner的4e154021正在自检离线授权分类，尚未合入/发布；Main指出原417已处WAITING_AUTHORIZATION，而旧扫描只接ADMITTED/PLANNING，故下次后端修复必须提供同意图恢复及授权回归，不能只换等待文案或重置生产数据。

Run156完成后，Main在部署锁下核对record156/精确5cafe摘要/无打开FD，仅退役本线程106578156B下载重复包；远端制品、线上dist、当前API4a35及直接恢复04d1保留，可用135528448→242135040B。正式Web阶段优先使用实际约106MB下载+108MB staging空间，API未新bootJar；不设置任意预留门槛、不删foreign数据。

### 2026-10-02 23:20 UTC：Run157真实失败已归因；测试夹具修正8/8通过，未冒充发布

Run157实际checkout3bad445；最终FAIL，build527664460 FAIL/scan527664461 SUCCESS/deploy527664462 INIT。云端2884 passing、2 pending、8 failing，无制品/无部署。8失败来自7个历史Hall挂载夹具漏接新增identity helper及旧源码断言，不归因voice SVG。Main补真实helper接线和已hydrated测试身份，保留OAuth/generation/卸载隔离断言；新child78b83f8/tree076e96只改7tests，生产src tree与3bad逐字节一致。失败8例定向8/8通过；ESLint原有27错误未增减，不能写全lint通过。本机复用node_modules与候选lock不一致，仅便宜诊断，正式locked install仍Flow。此刻未推develop、未创建新Run；release/1.13.55不移动。

API e7c3ba13/tree722b8830已完成持久等待同意图恢复；Main独立核对6源路径、12项fresh XML、8项逐字节复用authority证据及2项预期RED。尚未新打包/安装，线上仍5fe/1.13.54。磁盘按实际新JAR253.6MB与前端安装约214MB串行安排；Main仅将自有无外部连接旧fixture MySQL clean shutdown，全文件SHA验证后可恢复压缩10,520,768B，退役135MB数据目录，未动生产/foreign进程；live4a35和直接恢复04d1保留。

task417没有本次鸟图，仍不可验收；保持原request/intent/grant/consent，不重放点将、不重建授权、不生产DML复位。详见本目录release-1.13.56-progress/source-progress.json；完整AC01–AC22/FD01–FD12范围不变。

### 2026-10-03 00:24 UTC：1.13.56 前后端已发布；原417暴露输出上传404

API e7/tree722b正常bootJar产物ffdda747（253597826B）已按本地明确授权发布，PID3863755，52秒HEALTH UP，配置不变、直接恢复4a35保留。v1校验器nested临时解包失败并未捕获底层IOException，不写成已证明ENOSPC；资源整改后的同源同命令v2成功，187tasks/1executed，七个改变class和JAR CRC已独立核对。

Web remote develop及新release/1.13.56固定78b83f8/tree076e96。Run158正式2892passing/2pending，build527681324和scan527681325成功。首次deploy527681326/order70596770失败：主机free0与ENOSPC实测、下载55193600B不完整；deploy日志也截断，额外瞬时占盘来源未知，不归因其他Owner或声称完整wget错误。互斥下核对terminal/无FD/record156，记录hash后只退役该失败下载；实际制品+stage+新增线上文件+最大atomic文件预算219694631B，整改后可用288MB。单次只retry该Run部署，新job527694630/order70597028 SUCCESS；不重建、不Start、不改Flow配置。完整同Run106583353B包SHA256 bd7898c0d0c8941c4f9317c7c252d7c246ebab9f85806fc834ecc84ce0cc7f90，382成员/364dist逐项绑定；线上364文件及真实浏览器index/HallJS/HallCSS三资源摘要匹配。

真实原profile导航刷新，开始hydration未结束时scope为空，待实际加载完成自动恢复tenant字符串0/user5与原417scope匹配，无重新登录、无setUser/localStorage迁移、无重放点将；该刷新子例通过。voicee586图标保持既有Run156线上实测结论，已send_input通知voice主控。

但原417只恢复了同intent RUNNING，并未交付图片：23:37:06UTC provider-start200，23:37:43UTC output-content404及failure404，不能再称生成较慢。Controller存在，Service统一Failure映射404，需查具体locator/协议/lease/权限条件；不得简单放宽ACL。部署Client在验证PNG后上传，finally无条件删除runDirectory；只读确认目标Agent目录无文件、原paid claim仍CLAIMED。没有可预览的存留PNG证据，不冒充鸟图交付、不清claim/重新付费生成。Shannon负责API精确根因；Client须补持久输出后可重传，API修复不能补回已删除字节。

AC12文本归档de4dd601仍source-only，合同/迁移/测试未完成不得混入原417紧急修复。完整34项范围不变，整体仍不可验收。结构化证据：integration-evidence-20260928/release-1.13.56-progress/release-progress.json。

### 2026-10-03 00:44 UTC：404修复与结果保全候选，不冒充自动恢复

API25bb98a4/tree18c15bc已feature推送，RESULT authority最小修复正在唯一Owner经orchestrator验证；Main已恢复自有隔离MySQL315文件并逐一hash核验，TCP仅127.0.0.1:33793，授权只作用测试前缀，不动生产。Client8b3c35fa/treee307f98a已feature推送/readback一致：上传前保全有效PNG/receipt，404/过期/ACK不确定不删除；53相关mock通过、7可选CLI跳过。旧lane上7leaf回归红，Node含父组计9fail。此Client未合主分支、未重启runtime、无Provider调用；既有inbox/START lease不能恢复已START执行，故不宣称自动重传或原417恢复。后续独立结果传输权限与无spool终止边界见result-delivery-recovery-design-20261003.md。


### 2026-10-03 09:31 API1.13.57已发布；原417仍未交付，AC12前后端继续闭环

native404候选`cabb8b5c`/tree`d746ced8`已非force合remote develop并新冻结release/1.13.57。Main独立汇总Owner真实隔离MySQL XML：75项、0失败/错误/跳过；包含initial/followup preSTART failure与consumed RESULT准入。正常bootJar经orchestrator串行完成（API既有本地授权，`build_origin=local_user_authorized`），JAR253599215B/SHA256`cad49493eb88353afd3ffc8cf18d21824caa955c13785074188e7642786b35ac`；CRC、三个核心class与Gradle输出一致，仅agent-api/service两内嵌模块变化。首次CLI参数顺序错误发生在Gradle执行前，改为options-before-task后成功，未重放实际失败构建。

09:25:45可恢复安装完成，PID3927834、Main1.13.57scope、health UP；properties/launcher未变，保留e7c3上一版JAR及原配置。API没有新自动Flow Run，未伪报云端结果；Web保持正式Run158/78b83f8（含e586语音SVG），未新建前端Run。实际浏览器重新登录后09:28:59读取原417 GET200，仍原request/execution RUNNING/stateVersion3、没有鸟图。新代码不会恢复已删除的旧PNG，不重付费，不生产DML，完整34项仍不可验收。

Client保全源已追加真实安装清单修复：`ed6f66c7`/tree`8159d93e` feature push/readback。发现8b新增leaf漏入显式RELEASE_PAYLOAD，现55文件/34递归runtime模块逐字节完整；installer/candidate64通过0跳过，真实隔离copy闭包1通过（40非目标跳过），旧installer红测1按预期失败。旧闭包固定28断言已按真实依赖校正为实际模块+manifest完整相等，不减文件校验。Client仍未运行时升级，线上保持5bcb；没有自动重传实现。

AC12 Web`8e9809ab`/tree`ecf68d4f`已feature push：31文字+3inline+34voice共68定向通过、旧源六项红测、scoped ESLint/diff通过。请求冻结为lowercase create/items[textSelection]，202和不明确回执重放同key，Unicode边界/摘要、receipt身份与revision单调性明确核验；不传客户端正文。API AC12仍由唯一Owner完成编译、真实隔离MySQL/迁移自检，未合Web develop或用本地构建代替Flow。

证据：[1.13.57运行快照](integration-evidence-20260928/release-1.13.57-progress/release-progress.json)、[API制品绑定](integration-evidence-20260928/release-1.13.57-progress/api-artifact-independent-verification.json)、[AC12 Web源码](integration-evidence-20260928/release-1.13.57-progress/ac12-web-source.json)、[Client安装闭包](integration-evidence-20260928/release-1.13.57-progress/client-retention-packaging-source.json)。下一步：完成AC12 API与前端同Run集成，安装Client保全，并实现result-only恢复/无spool可审计业务终止；不把本次基础修复等同整体交付。
