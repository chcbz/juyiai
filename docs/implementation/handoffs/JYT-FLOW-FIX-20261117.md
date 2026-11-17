# 事项流程已定位 BUG 修复

Owner：jyt-flow-fix（developer）。用户2026-11-17授权修复、部署后真实回归。

范围：FLOW-17 API原生回答/文件输出合同；FLOW-08 Web摘要不覆盖详情；FLOW-24冲突后只读核对；FLOW-32概览激活刷新。FLOW-18仅重测，未定位根因不猜改，不新增诊断能力。RB-1职责不变；沿用 api/docs/interface-standard.md。

基线：API f4e94e607ef8f6bcdd75c39cb8b1b5bab7b41b94、Web 723f0ac1b13cbfd5416ba73f40c82c3a785339be，17:25及开发期间ls-remote均匹配develop。Runtime c184e26不修改。复用现有组件工作区，根脏修改属于其他任务不覆盖。

原型：web/prototypes/juyiting/delivery-entry.js、specs/prototype-spec.md；本机18786 PC1440/移动390预览可达，冲突演示入口可见，截图在下方证据目录。交互目标为保留原失败操作、读取当前业务终态，禁止重复验收。

最早验证：Web八组轻量诊断198 PASS（初轮1失败为原同版本摘要必须重复GET的旧断言，已改为保留现有详情且不重复读取）；不替代SSH正式测试。现有SFC有大量既存lint问题，不全站格式重构；本次新增unused import已移除。

证据：/home/isp/state/jyt-flow-fix-20261117/。设计依据：/home/isp/state/jyt-task-regression-20261117/analysis/最终开发详设.md v1.2。原回归证据不改写。

构建/部署/线上业务回归：待执行。使用原local_release SSH203.32.84.239，固定候选，单次600秒；不启Flow、不本机重型回退。生产当前API1.1.57、Web1.16.150均与本次基线对应。

## 18:08 交接：远端磁盘阻塞，未部署

- 固定候选：API `20be039283a3729f4dac9aa03aff70d9f554549b` / tree `1bc53eabebe2c09ec7d3ec82088a5021b18723ef`；Web `ad1830acfe5de48222da9cf9f1fdf62089b30de6` / tree `0cc6d471626f787394fbbf11c5f4e34e832f40a3`（1.16.151）。组件均为本地提交，尚未push；API目标版本1.1.58-SNAPSHOT。
- 当前候选Web定向轻量诊断：8组200 PASS / 0 FAIL，日志 `web-diagnostic-final.log`；不当作远端正式发布测试。
- `jyt-flow-fix-20261117-01`：真实FAIL，源码准备101.042秒，buildSeconds=0。SSH Web源码上传遇 `OSError: [Errno 28] No space left on device`。原plan-only、API测试、打包、安装均未执行；无应用构建超时，不申请扩时，不盲重试。
- worker `/dev/vda1` 40G/40G，初始可用28K。只清理本批未完成上传 `.transfer.tar` 101711872字节，留证后可用97M，仍不足继续。未删任何缓存、他人工作区、生产数据。其他构建源码目录共8.3G、输出目录5.9G；这些总量不等于可删量，需要用户授权后按绑定/锁/占用及日志保留规则判定。
- 生产仍API1.1.57基线、Web1.16.150基线；未进行修复后真实UI回归，无新测试事项或业务扣费。
- 下一动作：用户确认可清理的历史构建范围或扩容worker后，核对工作区无新增他人修改与生产前代，沿原SSH入口新批次验证固定候选（保留本FAIL）；通过后受控部署，再执行FLOW08/17/24/32、FLOW18观察及选版/资金回归。不能把当前代码提交称为线上修复完成。

## 18:32 接续

用户已允许核查并清理已结束/未占用的历史构建目录。仅清理worker `native6-web-20261117-01..04` 四份一次性源码副本（原Owner任务accepted，四个commit/tree均保存在控制机Web仓库，当前/回退为其它SHA，目录无脏源码/.keep/挂载/活动进程，持原Gradle/orchestrator锁）。原build state中的输出/日志/XML、共享node_modules目标和缓存全部保留；05/06及当前/回退不动。空间恢复3.19GB；完整预案/审计在cleanup-plan.json及cleanup-execution.jsonl。

批次02 Web253 PASS/2既有PENDING，已构建但未发布。复核发现对话拥有独立conversationTask，仅刷新selectedTask不能使对话工具栏收敛终态；在安装前中断本任务编排（FAIL/KeyboardInterrupt保留，buildSeconds77.978）。worker的Web单元已自然结束，未中断任何其它任务；API测试和安装尚未开始。追加Web提交d2aa361，复用refreshCurrentConversationTask，成功/失败共用reconcileReviewTask，不新增接口或状态系统。定向诊断15 PASS（不存在的测试文件名已更正，正式selector增加juyiting-hall-chat-context）。原02源码快照/回执在控制机保留，worker本任务01/02废弃源码副本经占用检查清理，输出证据未删。

批次03固定API20be039/Webd2aa361，通过同一SSH入口进行中；不能复用02Web测试作为新候选通过。

## 18:43 正式验证归因与API独立重试

03 Web正式266 PASS/2既有PENDING，固定d2aa361，制品a17b998f2ad1c8e6afac3298caaf04acee79f32b0bc65823ebce74060fb96ff7。API扩大runtimeCapabilityRegression 246项中6失败，buildSeconds334.923，未安装。XML原样保存release-03-api-tests.xml.txt。

根因：TypedDeliberationSessionRegistryTest三处仍构造退役protocol5（当前解析仅6）；ChatRetainedOutputSourcesTest仍mock旧三参数DAO（当前调用四参数含tenant）；另外genericChat元数据越权用例异常类型预期失配，以及ES隔离测试缺任务fixture。上述失败生产路径相对基线均未改变。仅修复与本次原生读写/素材消费相关的四处fixture，提交API50218c4e1ed7ef92a128c0b4fe84926c73d94510；不改生产认证/记忆代码，不机械改越权测试预期。其余两项失败仍开放，不宣称扩大套件全通过。

04沿原RemoteBuild传输/local_build --package构建，使用现有runtimeCapabilityRegression明确11个原生能力/声明/身份/素材类selector、完整nativeSkillResultRegression和默认认证/权限/邮件/POI/制品安全/分层/fresh JAR。复用03精确匹配Web，不重复构建。一次命令参数--tests解析失败发生在plan-only，尚未启动构建；保留release-04-preflight-failure.log，改为--regression-arg=形式后复用已准备的同一源码。正式构建600秒从首次真正构建计，非续时。

控制机磁盘仅725MB，核对无占用后删除本任务已结束01/02的6个冗余bare clone（原source.tar、commit/tree在组件Git、transport回执全部保留），释放约470MB。清单controller-redundant-bare-cleanup.json；没有删除构建缓存、原失败回执或生产备份。

## 18:48 API04/05

04：423项中422 PASS、1 FAIL，223.345秒（含回传）；不是构建超时。四处native fixture修正均已通过。唯一剩余失败SkillNativeResultMySqlTest要求独立外部MySQL fixture，而worker默认只提供逐类自建fixture的mysqld路径。保留原失败XML；没有删除该测试。05沿完全相同API源码/selector，复用已固定04源码，新增仅本批独占的loopback45317 MySQL（无生产数据，独立state目录和systemd单元，初始化计入600秒，结束后停止本单元）。正式构建仍经local_build/串行Gradle，Web继续复用03。05非续时，新的完整回执在release-05。

## 19:10 最终交付与真实回归

- API05 **423 PASS/0FAIL/0ERROR/0SKIP**，fixture初始化/正式测试/构建/打包/回传260.841秒；同一selector未删04失败项。独立loopback MySQL已停止。API 50218c4 / tree c71819e，1.1.58-SNAPSHOT。Web复用03 d2aa361，1.16.151，266 PASS/2既有PENDING。
- 原受控安装完成：API90.629秒、Web35.830秒；API HEALTH=UP/ARTIFACT_ATTESTATION=MATCH，Web online_verified；health/JWKS/未认证401核对完成。API JAR SHA2d71fde8bc1bc60a3299f7ea2d02050e96c8447041a99a4d95ea1dc84ef56c1a；Web包SHAa17b998f2ad1c8e6afac3298caaf04acee79f32b0bc65823ebce74060fb96ff7。精确安装记录release-05/install.json。不能将此前01..04失败改成成功。
- 新真实UI fixture A697完成、B698取消。13个派生用例 **11PASS/1FAIL/1NOT_RUN**：FLOW08自动推荐一次、FLOW17零文件回答（data.answer/outputs=[]且RESULT_COMMITTED）、FLOW24双窗真实409后自动关闭旧确认并更新议事已完成、FLOW32取消返回首页刷新均通过；v1/v2并存时明确选择旧版验收，只有1次成功结算，钱包2467→2466文、原held2不变。原v1字节未变；手机390布局无水平溢出（不代表真机）。
- 内容缺陷仍开放：首份v1只写标记，漏预算120/8人；后续单次修订v2正确包含V2/150/10（换行分隔），旧FLOW18本轮未复现，不能称已修复其根因。未加诊断或猜改。原native能力测试套件另外两项无关失败仍开放（genericChat异常类型/ES fixture缺失）。
- FLOW32真正系统前后台切换NOT_RUN：headless三个页面始终visible/hasFocus=true，bringToFront未触发真实系统事件，不能拿它报FAIL或PASS；组件事件定向单元测试已通过，返回首页真实UI已通过。
- 回归报告与CSV/JSON：/home/isp/state/jyt-flow-fix-20261117/测试与部署结果.md、测试用例与结果.csv、results.json。原始截图/网络/文件/最终账务在ui/；不是全局119项或完整CORE17通过。
- 组件均本地develop已提交且干净。push时API GitHub空响应、Web443连接超时，随后只读ls-remote超时；远端同步未确认成功，不能宣称已push。待网络恢复先查询远端状态再续推，不force、不重建/重部署。最后成功查询远端基线仍API f4e94e6/Web723f0ac；本轮本地候选和安装源独立固定。
- 控制机另删除03已结束尝试的冗余bare clone（source.tar、组件Git、安装/测试证据均保留），仅本任务输入副本，不碰生产、备份、缓存及其他任务。清单controller-03-redundant-bare-cleanup.json。
