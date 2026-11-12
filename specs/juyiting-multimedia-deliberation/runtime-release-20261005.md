## 最新阻塞更新（2026-10-06 08:12 CST）

用户已提供测试账号并授权登录，浏览器已提交一次登录，未保存密码到文件/证据。实际服务端access记录：08:08:38 POST /login ->302，随后GET / ->444；真实nginx现有location /为return444，浏览器报告ERR_HTTP2_PROTOCOL_ERROR并进入data错误页，Browser Use URL policy阻止后续观察/导航。这不是已证实的密码错误，也不能据302证明登录成功。curl诊断403来自既有curl User-Agent限制，不当API整体故障；nginx自定义实例仍运行，systemd nginx inactive不证明服务停机。

停止该错误页的自动UI尝试，不切浏览器/提取cookie/修改防护/用终端代替浏览器登录来绕过。需要用户在现有IAB地址栏手动回到 https://kit.chaoyoufan.cn/juyiting ，然后只读核对实际身份再继续验收；若仍需登录，沿正式页面处理。密码不写入自动化提示或Git。三端发布证据不变，T05–T09仍未完成。

## 最新权威状态（2026-10-06 01:30 CST）

**三端正式发布已完成；真实chcbz业务验收尚未完成。** 用户要求立即发布已落实，无须等待下一次零点。

- API5260799/112正式SUCCESS及实际JAR/record/健康完整证明保持有效；Agent共享与wuyong-local均已安装4e70c4f。不重发、不重复安装。
- Web4403172/168最终SUCCESS，CI529287081/scan529287082/deploy529287083成功；部署单70646814唯一主机Success/client healthy。source f6b81b40ee4a579c579af4cb7ab1e0e76e362173/tree3f70c8a345ef09359b0169785ec66d5f8cdf5102，与同Run包内标记匹配。
- 同Run归档106693786 bytes，SHA256 cfff7cab8af652fa449463f6a12ce96b007fa879d50ed6f715cd743daf6fc672；3146测试通过/2pending/0失败/0skipped。364个dist文件完整manifest覆盖、安装字节及公开HTTPS逐个size/hash完全匹配。record未变化，run168/status与phase均online_verified，版本1.0.1。完整证明UTC2026-10-05T17:27:14.674810Z。
- 01:30核对API112/Web168安装record及两仓库远端develop均为本次源提交，随后恢复既有cyf-flow-backend-nightly.timer及cyf-flow-frontend-major-nightly.timer，均active；未手动Start任何额外Flow。
- IAB tab1刷新后已出现新版统一“添加资料（可选）”入口，随后身份校验跳转真实登录页。之前chcbz登录已失效，**当前需要用户在现有IAB页重新登录chcbz**。不索取密码、不提取浏览器秘密。此阻塞只影响真实业务验收，不影响已完成发布。T05–T09业务仍NOT_RUN，不以CI夹具替代。

证据：[Web同Run制品](implementation-evidence-20261004/runtime-release-20261005/web168-artifact-verification.json)、[线上完整字节](implementation-evidence-20261004/runtime-release-20261005/web168-online-verification.json)、[恢复调度](implementation-evidence-20261004/runtime-release-20261005/timers-restored-after-web168.json)。制品回执中的ONLINE_BYTES_PENDING是01:25阶段状态，01:27独立线上完整回执已覆盖，不改写历史。

下一步仅核对chcbz登录是否恢复，然后执行新事项T05–T09真实验收（work/real-acceptance-assets已有无个人信息材料）；不重复发布/清理/419或420/schema/helper安装。登录问题已通知，不反复提醒。

# 三端发布接续（2026-10-05 23:30 CST）

## 最新权威状态（主机北京时间2026-10-06 01:17 / UTC2026-10-05 17:17）

**API正式发布完成，Web正式发布中，真实业务验收仍NOT_RUN。** 用户立即发布授权已执行，不等待夜间窗口。

- API5260799 **Run112 SUCCESS**，CI529282011/deploy529282012均SUCCESS；部署单70646647、唯一主机Success/client healthy。源码329d44fd/tree69d2cb54；同Run归档226549272 bytes、SHA55c0789aca1822f8dc506d8bcb3bac3a1eada79393d425cccb72ea389d59a42f；JAR3170b50d已核验与canonical、installer record、consumed approval完全匹配。
- 实际PID1229757、attestation MATCH、端口PID归属/运行用户/真实Actuator UP均通过。当前Actuator status为对象code=UP，与正式launcher同一语义核验。云测312 suite/2667计数（部分重叠）、0fail/error/101skipped，如实保留。
- F06 postinstall PASS，两表existing_equivalent，无DDL。E05本次**not_admitted，未调用runner**；不得把之前候选对真实E05表的只读equivalent称为正式E05激活。三端功能真实验收与schema校验仍分开。
- 01:11:54.978（UTC2026-10-05T17:11:54.978Z）完成私有 `flow-forward-only/api-final-release-healthy-verified.json` 完整真实API回执（实际回执UTC at为准），随后用既有restore-mmd-forward-flow-deployment.cjs恢复Web原deploy **一次**，actual config SHA23743de5835db6bc98864ebd792c26cfd5d7e0ed169902508dd750e51cc420aa，原CI/source/tests不变，不再apply。
- 既有controller已创建 **Web4403172 Run168**（build/test529287081、scan529287082、deploy529287083），01:12:55创建，CI运行中；目标f6b81b40ee4a579c579af4cb7ab1e0e76e362173/tree3f70c8a3。Start UNKNOWN已只读核对唯一168、时间/config、provider实际checkout marker及CI_COMMIT_SHA环境匹配，01:16:27 proof写回并在controller mutex写4403172-168.json。**不是backend形式的echo相等断言**，同Run包内source/tree仍待最终制品核验。没有重试Start。
- Agent双实例4e70c4f已完成，不重复安装。监控maintenance已恢复；两个nightly timer仍临时暂停防重，**Web168正式成功且线上dist确切字节/record匹配后恢复既有两个timer**，不等待全部业务验收才恢复正常调度。

下一步只读跟进168；新Run的完整测试/scan/构建/同Run制品/部署单/record/线上dist字节核验完成后，恢复timers并做真实chcbz T05–T09。IAB已登录，无需再次提醒。不得重复Start112/168、API/Webapply、旧110/111schema、已有helper安装或历史数据清理。只修实际失败，不降级JAR/schema，不用subagent/reviewer，不本地构建兜底，不打印原始Flow日志（可能含敏感环境，仅提取明确非秘密字段）。后文均为阶段性历史，由本段覆盖。

## 最新权威状态（主机北京时间2026-10-06 01:04）

API111最终FAIL（CI成功、同字节新版JAR健康）：F06 runner仍固定旧ownerless SQL SHA，与当前JAR自带的新owner-fenced SQL不符。旧110/111 schema报告均not_attempted，完整保留，不重放、不改历史记录。最新主机JVM PID1214410，健康monitor整体healthy/maintenance=false。

已据**确切Flow111 JAR资源**更新F06固定字节允许列表和SHA为 `ecd557ae6f46810cb3ae9d250df80560976504d07b96650d780f3b699b214e75`，只接受mandatory owner_jiacn以及owner-fenced确切索引，旧ownerless结构拒绝；只允许当前fresh/initializer两个均带owner的确切列布局，不是旧版本兼容。E05 SQL字节保持原样，仅校验本次AgentSchemaInitializer已有的mandatory owner列/精确owner index；未知列/index/check继续拒绝。没有数据库DDL/DML。历史Run49 literal fixture原样保留，当前owner衍生fixture显式标为synthetic，补旧ownerless及缺owner/index拒绝回归。

- 主机候选62离线回归全部通过；01:00:00按coordinator/release/runner互斥、before SHA CAS及after读回安装。私有 `schema-owner-gate/install-result.json`。
- 00:53:44用候选只读核对真实运行JAR内确切SQL及实际MySQL catalog：F06两表/E05一表全部equivalent；移除owner/owner index/check的负控制全部拒绝。**无DDL**，详见 `schema-owner-gate/readonly-preflight.json`。因此先证实新schema gate符合真实新版，再建新Run，不盲目循环发布。
- 当前正式 **API5260799 Run112**（CI529282011、deploy529282012）01:00:39创建，正在运行。Start UNKNOWN只读核对唯一新增112、时间/config和真实检出相等断言完成，01:03:06 proof和controller intent已写，未重复Start。源码仍329d44fd/tree69d2cb54。
- 当前主机helpers：F06 `076f46d84029836ee71f2a45bc7431f9425a2ba61d65a99bb82821fe4fdcf392`；E05 `f76fd49ec7f9cf573bcdb0ca40c401671af9a813b26cda852ceea67bc15bece7`；adapter `6a81032f19eddfcf41a5d6bcaa8a6da6d8fc0f5994b2860f70f572917b2ddc22`。不要用旧SDD整文件覆盖实际新基线；最小patch留存。

下一步只读跟进112，**只有最终Run完整测试/制品/部署单/安装record/实际运行JAR/真实健康及F06/E05结果**核验完成，才写API健康发布回执、恢复Webdeploy一次并立即发布。112 Start与110/111schema不得重放。Agent已完成，Web待发布，T05–T09 NOT_RUN。监控已恢复，两个nightly timer仍临时暂停，API/Web正式发布完结且record匹配后恢复。后文所有“当前”均是阶段性历史，被本段覆盖。

## 当前权威状态（2026-10-06 00:40 CST）

用户要求立即发布，不等零点。Agent双实例已实装4e70c4f，不重复升级。API Run110测试/同Run制品通过，新版已健康运行，但最终Flow仍FAIL（发布后F06 hook拒绝test-results目录），不能称正式发布完成。原失败/runner报告完整保留，不改历史记录、不重放Run110的schema操作。

- Run110依次修复：制品仅允许安全XML/summary报告且不提取；旧canonical hardlink字节相同单link规范化；launcher使用物理root-owned日志目录；仅确切失败候选可前向重启。主机40回归（39通过/1跳过）及monitor15通过。原日志别名和备份不搬移。
- 00:23:56执行Run110 JAR内确切`chat-selected-output-finalization-completed-message-v1.sql`（SHA256 3631eb240f9775850f8b388426e3490cf5b4dc519989568d7466a0255f027407），release互斥及原MySQL named lock、catalog CAS、父/子表均0行。新增五列、nullable step/output、message唯一键和source约束均读回通过；无DML/drop，不重放。
- 同Run110最后retry job529265324/order70645996安装成功；实际PID1203671、JAR SHA256 3170b50d19b9c28bcd734e1a6a474023be3a2e6a7a4196a12993e9fddf98caa8、attestation MATCH、端口归属及HEALTH=UP；record installed/approval consumed。该job随后因F06 package_member_invalid失败，报告两表not_attempted，不篡改为PASS。
- 00:33:57修复F06/E05固定SQL runner的相同报告catalog问题，并repin adapter的E05 runner hash。60离线回归通过；在coordinator/release/F06 runner锁下CAS安装，不执行schema，不移除门禁。最新helper SHA见回执及最小patch。
- 必须使用新Run验证，**API5260799 Run111**于00:34:46创建：CI529269938运行，deploy529269939待执行。Start响应UNKNOWN已只读核对唯一新增111、时间、冻结配置及真实CI相等断言329d44fd，00:39:58核对完成并在controller mutex写5260799-111.json。未重复Start。旧110失败证据保留。
- API监控维护已00:29恢复，最新只读snapshot API/Web/MySQL/Redis/Agent健康。两个nightly timer仍临时暂停防重复，API/Web发布实际完结且records匹配后必须恢复。Web仍CI-only；在**Run111完整正式成功且同Run制品/部署/实际JAR/健康**确认后才写api-final-release-healthy-verified.json，恢复Web原deploy一次并立即启动，不等00:30。
- IAB已登录chcbz，无需用户再次登录；T05–T09真实业务验收仍NOT_RUN，不拿fixture代替。

下一步只读跟进111，不重跑Start/110schema/已安装helper；实质失败才前向修复。正式成功后立即Web，然后真实验收、恢复timers及SDD推送。

## 最新覆盖指令：立即发布（2026-10-05 23:47 CST）

用户明确要求“不用等0点，现在直接发布”，覆盖下面历史的夜间等待。API已通过既有controller启动 **5260799/110**，CI job529247617，deploy job529247618。Start返回UNKNOWN是Flow source缺少commint（仅repo/branch），不是未创建；已只读核对唯一新增110、创建时间23:43:05、冻结上下文/配置及真实CI检出329d44fd的相等断言，未重试Start。23:47在原controller互斥下使用既有write_intent写5260799-110.json，旧kind backend-nightly仅是既有机器契约，真实授权是本次立即发布，未伪造零点时间。

两个既有timer为避免零点/00:30重复发布已**临时暂停**（不取消任何Flow/其他任务）。本次API/Web新版实际安装record匹配且发布完结后恢复原timer；若失败需前向修复，保持证据并由接续工作处理恢复，不能遗忘。API完整健康后恢复Webdeploy并**立即启动Web**，不再等00:30。真实验收仍NOT_RUN。chcbz浏览器已登录，不需再次登录。

私有证据 `flow-forward-only/immediate-release-authorization.json`、`run110-reconciled.json`、真实nightly intent。完整验真仍须最终Run测试/制品/部署/运行JAR/健康，而不是上述启动证明。

## 历史结论（已被上方当前状态覆盖）

以下是23:30时的历史记录，不用于当前调度决策。

用户最新决定：**直接升级到新版本，不兼容旧版本**。已放弃两阶段兼容包装；不得恢复该方案。新版失败保留候选、诊断与原备份，向前修复，不自动重启旧 JAR，不降级 schema。

## 已完成及证据

统一回执：[manifest](implementation-evidence-20261004/runtime-release-20261005/manifest.json)。

- Client `4e70c4fc90aaf72ee6a1e58aae7703853af449f1` / tree `4fe55783502e027ba226babea6301a0c720ec02f`，已推 feature/develop。修复真实安装失败：显式 payload 缺少导入模块 `juyiting-action-outcome.mjs`；补 relative-import 闭包回归，53 PASS，56文件。
- 共享 `codex-ws-agent.service` 与独立 `codex-ws-agent@wuyong-local.service` 于22:16:30安装上述确切提交；持久配置原字节保留，manifest与安装器hash已读回。共享全部profiles及本地实例先证实空闲再维护，无真实Provider调用。
- 现有零点调度 `flow-control.cjs` 只修 listRuns 分页。18回归通过，实际109条完整读回且无活动Run；没有创建新Run。
- API安装器增加显式 `CYF_API_FLOW_FORWARD_ONLY=1`：候选切换后失败只写原failed记录并保留候选，不 detach/restore/旧JAR start。默认其他发布行为不改。故障记录写失败也不落入旧版恢复。
- 实际备份根是已有别名 `/var/lib/cyf-api-flow/backups -> /home/isp/baks/flow-api`。只允许该精确root:root别名，物理目标仍root:root0700；其他别名/离线fixture别名拒绝。保持逻辑backup路径，不搬移目录、不改历史记录。
- 两个主机helper以**实际已安装的新基线**作最小patch，在 `/tmp/cyf-release-api.lock` 下CAS/备份/原子安装/hash读回；不覆盖脏主仓库、不改launcher、不重启应用。实际主机候选26回归PASS/0失败/0跳过，bash语法通过；SDD确切源码另外在隔离Linux fixture中26回归PASS/0失败/0跳过。SDD代码是对应最小差异，不是整份主机文件的替换来源。
- 23:23恢复API5260799原deploy段，明确forward-only；原CI源码、测试、同Run制品和主机组不变。实际配置SHA256 `a2e5d4617e110fba303a18e02115714880a4cef09a72b6858e1b08cd8d9667ed`，已normalized readback验证。未调用Start。

## 历史夜间顺序（立即发布指令已覆盖，禁止据此等待/重复触发）

1. 由已有 `cyf-flow-backend-nightly.timer` 于**2026-10-06 00:00北京时间**启动API5260799；不要提前手动启动，不重复触发。核对现有timer/最新Run/实际intent；未知Start结果只读reconcile。
2. API目标 `329d44fd7f8d0b2402853f5eac4cf47c99fcbed9` / tree `69d2cb5448aa165b35ead9794bac0971736f1a7d`。只认新最终Run的云测、同Run制品、部署单/主机、安装record、实际运行JAR及健康。当前旧API PID19026/source b8053da6不等于目标。若失败保留证据并修新版，不自动降级。
3. API完整健康确认后，才在私有 `flow-forward-only/api-final-release-healthy-verified.json` 写真实回执，再用已有准备脚本恢复Web4403172的原deploy；脚本此门禁不可提前伪造。Web目标 `f6b81b40ee4a579c579af4cb7ab1e0e76e362173` / tree `3f70c8a345ef09359b0169785ec66d5f8cdf5102`。00:30 Web major timer仍存在，API未健康则Web不得恢复deploy。小版本仅在API健康后依既有规则启动。
4. Web同Run制品和线上dist逐字节核对，再做chcbz真实验收：无素材→明确选真实Agent→结果→同会话改稿→预览下载→不保存直接验收；混合图片/文件/音频及仅附件实际读取；纯文字/单项修改保留兄弟；刷新同确切原源且不生成；可选保存空间重开同字节；跨用户/任务及密议隔离；桌面和实际窄屏“＋”。既有预算/模型/工具，不新增付费服务。
5. 浏览器：Chrome控制桥报auth method错误；已通过现有IAB安全替代打开聚义厅，当前到登录页（tab1，api.chaoyoufan.cn/login/index.html）。用户已被通知登录chcbz，密码不要发到聊天。不要读取/导出浏览器秘密或用脚本绕过浏览器安全。API/发布仍可继续，不因页面登录阻塞而停全部工作。
6. 记录观察和失败/修复，更新SDD、目标特性分支；未实际满足的验收不标PASS。状态无变化保持安静，只在真实阻塞/用户行动/全部完成时通知。

## 接续位置与限制

主机私有根 `/home/isp/wsps/private-maintenance/mmd-runtime-release-20261005-payloadfix`：`forward-only`包含helper安装前后/26回归，`scheduler-fix`包含分页安装/18回归，`flow-forward-only`包含新的单次更新intent/config读回。

`/var/tmp/restore-mmd-forward-flow-deployment.cjs` 是新的单次配置更新上下文。API已APPLIED，不可再次apply；Web仅API健康后prepare/apply一次。旧 `/var/tmp/restore-mmd-flow-deployment.cjs` 的API更新已尝试、无forward-only，**不得重跑**。

SDD `D:\workspace\mmd-plan-1004`，自有分支 `codex/mmd-version-progress-20261004` 推 `HEAD:refs/heads/codex/juyiting-multimedia-deliberation`。API/Web/Client worktrees及远端脏主目录保留。正式测试构建发布Flow-first；不得把CI-only制品手工安装冒充Flow发布；不使用子Agent或Reviewer；不抢占/取消别人的Run；未知写入只读核对。

chcbz历史清理已完成，不再删除、不重放419/420、不全局重启ES/Redis。监控 `--status` 只读；`--check-once`可能恢复/发邮件，不用作只读探测。

## 2026-10-05 23:37:40 CST 只读跟进

既有00:00/00:30 timer仍active，Agent双实例active，API/Web/MySQL/Redis监控健康，无维护/恢复动作。IAB tab1已由用户登录；通过个人中心可见账号 `chcbz` 已核对，随后返回聚义厅并保留页签。登录阻塞已解除，不再请求用户登录。未创建事项、调用Agent/Provider或启动Flow；等待00:00既有发布调度，业务验收仍NOT_RUN。


