# 办事/议事正常场景实测记录

核对时间：2026-10-27 22:55（Asia/Shanghai）；Owner：BUSINESS-NORMAL-20261027。

**首轮仍在执行，不是验收完成报告。** 状态以整条用例判断；局部通过仍记NOT_RUN并列已做部分，BLOCKED不等于失败或通过。异常测试不在本轮范围。

环境：真实 `kit.chaoyoufan.cn` 浏览器，非localhost原型；chcbz事项534、ziyue事项535。首轮API330/28700cc、Web344/1102350；发布后回归API1.17.11/3bca7cbd71（335 Run CANCELED，但同次主机安装随后完成且JAR/健康核验通过），Web350 SUCCESS/1.16.62/1fdae7355d（公网摘要匹配）；Runtime仍15483d5/1.3.20。本轮真实页面操作按各证据时间区分，不将发布前失败抹去。

证据根目录：`/home/isp/state/cyf-business-normal-20261027/`；截图及DOM分别在browser/、ziyue/；已脱敏的本任务权威结果与执行技能事实为task-action-facts-readonly.json。密码不落盘至报告。

## 首轮逐项记录

| ID | 场景 | 状态 | 已验证/缺口 |
|---|---|---|---|
| N01 | 我有一件事需要处理 | PASS | 回归新536从办事创建，确认后自然进入林冲原事项议事并收到首答，无二次启动/重复点将；n01-linchong-candidates、n01-linchong-progress、n06-linchong-first-final。首轮534/535的BUG01失败保留历史。 |
| N02 | 我想换个承办人 | PASS | 536推荐吴用→更换承办展开候选→选择林冲→确认；同一536进入林冲议事，n02-linchong-selected、n06-linchong-first-final。 |
| N03 | 我想先商量清楚 | PASS | 534/535各完成首答+两轮有上下文的正常追问，上一轮结束可继续输入。文本文件交付另记N16失败，不把纯聊天与技能交付混为一条。 |
| N04 | 我暂时只是问问题 | PASS | 534有首答成果后仅询问轮流主持/防冷场，返回ANSWER，未执行、未验收；原会话保留。 |
| N05 | 我要给吴用看图 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N06 | 我想用林冲办事 | FAIL | 536首答完成，但图片请求转修改子请求后发生与534相同的thread/start超时；Runtime已RECOVERY_REQUIRED，API仍DISPATCHED，未产生图片。n06-task536-followup.json、n06-runtime-recovery.json。未重复发送。 |
| N07 | 我想找之前聊过的内容 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N08 | 我想另开一个话题 | DEFERRED | 用户确认本轮不支持事项多会话；首轮BUG04失败作为历史保留，不记PASS。Web1.16.69实页539无新建/删除入口，原历史和消息可回看；普通公议/密议多会话未取消。 |
| N09 | 工具打开后我要继续输入 | PASS | Web350实页外点/三工具Esc仅收起工具并保留草稿；n09-mutual验证记录→更多互斥；本轮更多→选材收起前工具，内部预览/添加暂选/取消正常，原议事保留且未发送。n09-tools-post-release、n09-picker-internal/staged/cancelled。首轮Esc失败保留。 |
| N10 | 我想从已有资料里选几份 | PASS | 真实页面浏览文本/图片并预览固定v1、多选2份→完成→本事项资料显示2份；草稿保留且消息数未增，未自动发送。browser/n10-n12-materials.json、n12-explicit-current；本轮使用浏览路径，无搜索控件时不虚构搜索结果。 |
| N11 | 我想上传本机文件 | NOT_RUN | 前轮多文件上传/选择已有证据；发送并核对固定版本未完成。 |
| N12 | 我选错了，想取消或移除 | PASS | 534暂选取消不提交；536仅本条EXPLICIT勾选图片→完成→重开选中→取消勾选→完成→重开未选中，任务资料仍1份，原blue-square.png固定v1预览320×240正常，文字草稿保持。n12-before-remove-536、n12-after-remove-original-preserved-536、n12-original-preview-loaded-536。未发送消息。 |
| N13 | 这次只想让Agent看指定资料 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N14 | 我想读PDF再讨论 | NOT_RUN | 已有多页PDF翻页局部证据；BUG03动作发现已修复且实际目录含pdf-extract，但Agent实际读指定页与摘要仍未验收。 |
| N15 | 我想查看不同资料 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N16 | 我需要一份可交付文件 | FAIL | BUG03当前安装目录已修复且实际facts含文本/PDF；新文件修改转REVISION_REQUEST后，原子请求Runtime thread/start超时并RECOVERY_REQUIRED，后端却保留RUNNING（BUG05）。尚无文件，不重发原请求。 |
| N17 | 我想改一改刚生成的图片 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N18 | 我想从几稿中挑选 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N19 | 我不想等这轮回复了 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N20 | 我离开一会儿再回来 | PASS | 535从本人首页重进原议事、浏览器重新打开应用后仍可找到完成状态/原成果，无需重复点将或发送；x09-resume-observe、n22-final-state、n23-reopened-detail。 |
| N21 | 我同时有两件事 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N22 | 我决定验收这一版 | PASS | 535实际成果卡→预览→返回取消（未验收）→重新打开选择唯一文字成果→确认，最终事项已完成且议事只读。n22-preview-before-cancel、n22-cancelled、n22-final-state。多稿多选仍待N18形成样本。 |
| N23 | 我想回看已办完的事 | PASS | 首轮BUG06已保留；Web355后原535归档回看复用只读成果记录，已验收1/历史0/固定版本1，预览仍为原2小时安排，不再提供继续议事或再次验收。ziyue/n23-archive-fixed-355、n23-archive-preview-355、n23-archive-review-record-355。 |
| N24 | 我更方便用语音 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| N25 | 我在手机上办事 | NOT_RUN | 390px已实测535成果记录/归档页面并截图，无横向溢出；未完成手机创建/发送/真机软键盘，全用例未通过。 |
| X01 | 我刚来，没有自己的Agent | BLOCKED | ziyue实际已有卢俊义；不得删除该Agent伪造零Agent新用户。 |
| X02 | 我要找能帮我的吴用 | NOT_RUN | 535候选与详情显示吴用属于其他用户；零Agent新用户前置不满足，局部操作不作整条PASS。 |
| X03 | 我确认把这件事交给吴用 | FAIL | 535确认后曾长期PENDING（BUG01）；现已恢复首答，修复后的自然首轮待回归。 |
| X04 | 我只想先问一个简单问题 | BLOCKED | 535跨用户吴用首答+连续追问两轮均完成，同会话上下文准确；严格无自有Agent前置未满足。 |
| X05 | 我需要吴用生成一份文件 | BLOCKED | 严格零Agent前置不满足；旧动作目录缺陷已修复，534文件生成新遇BUG05，不能称跨用户文件已交付。 |
| X06 | 我有自己的资料要给吴用 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| X07 | 我想让吴用看图并修改 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| X08 | 我想补充要求或资料 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| X09 | 我明天还要接着办 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| X10 | 我满意了，要验收并留存 | NOT_RUN | 本轮尚未完成，不沿用历史PASS。 |
| X11 | 另一个新用户也要找吴用 | BLOCKED | 两指定账号均有既有Agent，缺少第二个严格零自有Agent样本。 |
| X12 | 我只用手机，没有Agent | BLOCKED | 零Agent前置不满足，完整手机外单主线未跑。 |

## 问题汇总

1. **BUG01：首轮准备议事停滞。** 临时数据库断连后首轮调度停止；候选已修复、云测通过，尚未发布。原任务在本任务修复发布前已恢复，不归因给本修复。
2. **BUG02：话头记录只能再次点原按钮收起。** 输入框真实pointer点击后列表仍展开；更多操作可正常收起。待统一修复并复测Esc/切工具/草稿。
3. **BUG03：显示可调用的文本文件/PDF未进入实际动作目录。** 534文本文件请求实际返回CLARIFY；数据库只读核对534/535后续轮的availableActions均仅image-edit、image-generate。现用文本文件1.0.1有三份历史安装、PDF1.0.0有两份历史安装，但各自activeInstallationId唯一；UI读取readCurrent，动作构造及新的执行接纳读取全历史并按同key/version要求唯一，导致合法当前技能被历史记录排除。不得删历史安装、去掉身份/授权校验或让模型猜动作；修复应统一新动作选择当前有效安装，已接纳执行继续保留固定来源。

4. **BUG04：另起话头后首次发送无反馈。** 534已自然结束前一轮，点击另起话头后写入选书问题，真实点击发送只观察到事项GET，数分钟后仍空白且草稿保留。没有新聊天请求，未重复点击。旧话头可在列表找到；具体根因待核实，不把本机自动化辅助失败当应用缺陷。证据browser/n08-new-topic、n08-new-topic-reply及network.jsonl。

## 已完成的代码验证（不等于页面验收）

API5260799/333，86f8ed1da1c9f4d9a6a99aedc7e330aa21034d62，SUCCESS；3289总项，3125非跳过、164跳过、0失败/错误；首轮恢复新增8/8。validateLayering/fresh bootJar执行通过。CI-only无安装，默认配置已恢复；同Run包摘要见ci-clock-fix/api-artifact.json。

## 下一步

继续完成不受BUG03阻断的正常交互及图片主线；按当前安装指针修复BUG03与BUG02，合并BUG01候选统一正式验证、按授权发布后再通过浏览器回归。零Agent/真实手机等样本缺口单独报告，不把普通跨用户成功代替。

## 2026-10-27 08:49 接续更新（不覆盖首轮原始失败）

- BUG03已提交API3bca7cbd71，Flow5260799/334测试/构建成功，未部署；页面文件/PDF场景仍待回归，不记PASS。
- N09重新实际鼠标验证：原534话头记录展开后点击输入框可收起，证据browser/n09-recheck-open、n09-recheck-closed。纠正先前“没有outside处理”的源码推断：旧主工作区并非固定发布基线。
- N09真实Escape却退出整个议事页；父层键盘冒泡先消费事件，工具document监听未执行。已准备History/Composer捕获阶段处理及3项嵌套父层回归，尚未云测/发布。N09整体仍FAIL，不因一项outside操作通过而关闭问题。
- 37条首轮、统一发布和浏览器回归仍未完成。
- 334同Run包内测试明细：3293总项、3129非跳过、164跳过、0失败/错误；技能动作发现11/11、派发保护8/8。仅代码验证，不等于正常业务37条通过。

## 2026-10-27 10:10 接续实测与候选（覆盖上文旧“未发布”结论）

- BUG01/03已按精确API3bca7c部署，原事项的恢复不能归因于发布前候选；新事项自动首轮路径仍待自然回归。BUG02/Esc已由Web350发布，三工具实际按键/外点与草稿保留见上表；先前outside缺失归因已纠正。
- 新BUG05：Runtime原子请求恢复记录明确APP_SERVER_RPC_TIMEOUT:thread/start；API处理非明确模型错误的recovery_required ACK只确认收件，未同步turn/request；页面修改卡持续显示处理中。证据n16-runtime-recovery.json及n16-revision-*.json。未知请求未重放。
- 已在原API/Web工作区准备最小状态同步与提示修复，保留ACL/原dispatch绑定/终态与幂等；Web定向5项通过，API尚未云测，两个候选均未发布。不得将这条修复写成线上已生效。
- 535验收的是已明确预览的原文字成果（2小时版本），不是将后续90分钟建议冒充新文件。已验证取消不提交、完成态只读；尚待归档后回读。
- 浏览器进程在接续时已退出，核实PID不存在后复用各自原私有profile重开，未动用户原型或重发业务。部分脚本点选早于控件加载/选择器不匹配的失败是测试工具问题，不记应用缺陷。

## 2026-10-27 11:17 发布回归更新

- Web1.16.64 /58210f1已通过Flow355测试/构建/同Run部署，3465 passing、2 pending，终态SUCCESS（251.023秒首次观测）。公网入口与业务JS及同Run包摘要匹配，ziyue原535实际浏览器归档回看通过。前一次354部署脚本的备份路径冲突导致FAIL，已修正独立备份路径，不覆盖旧备份或将354重标成功。
- N06林冲536的图片执行同样遇到Runtime thread/start超时，尚无图片，记FAIL；原请求未重发。状态同步API候选虽通过336但未部署，不能把前端提示发布等同于Runtime执行已修复。
- 首轮37条仍未全部完成，用户指定账号均非严格零Agent样本；不把BLOCKED/NOT_RUN改成PASS。

## 2026-10-27 11:59 状态同步候选补测

API Flow338 同 Run summary：3299 总项、3135 非跳过、164 跳过、0 失败/错误；恢复 ACK 的三个参数在同 Run Handler XML 实际执行且通过。候选 `129571cd61aec7b48663488f4ffc51a7bd5e111c` 仅 CI，尚未部署；不代表 thread/start 的根因、534/536 历史状态或业务执行已修复。详细证据和边界见 `docs/implementation/handoffs/BUSINESS-NORMAL-20261027.md`。

## 2026-10-27 14:24 文件正常场景后续

新增真实页面事项537，12:53:28确认吴用承办；14:23:12重新打开仍无文件，页面同时显示“结果待核实”和“吴用正在回复”，14:23:55执行子请求API仍RUNNING。文件生成闭环未通过，不能据此断定具体底层原因；未重发。证据与详细限制见 `docs/implementation/handoffs/BUSINESS-NORMAL-20261027.md` 14:24节。

## 2026-10-27 15:38 UNKNOWN提示子问题发布回归

Web1.16.66 / b049f9348dc5966af3d1f92f5b9dbdc48f3e7b56，Flow4403172/359 SUCCESS（3481 passing / 2 pending，测试、构建、扫描和同Run部署通过）。chcbz真实浏览器重新打开原537，已统一显示“结果待核实”，不再同时提示正在回复/等待回话；原消息保留，未知执行的输入/发送仍禁用，无重发。390px视口无横向溢出，不等于真机验收。证据`browser/unknown537-after359-assertions.json`及桌面/移动截图；版本/摘要证据`release-web-unknown-status/`。

**这只通过状态展示的定向回归，不是文件交付成功。** N16仍FAIL，N08另起话头仍FAIL；未补跑的正常用例和零Agent样本缺口不改PASS，37条整体仍未验收。性能调查已按用户要求暂停。

### 2026-10-27 BUG04修复候选验证补记（非生产验收）

- N08仍未标PASS：完成同事项空话头创建/回读的前后端候选，依赖新增成员关系表；尚未生产迁移与部署。
- 本机新话头/实际页面handler/会话回归98项通过，实际Hall初始化/布局另6项通过；原型桌面及390px实鼠标往返保留各自草稿/旧消息/引用，选中后列表收起。证据见同日handoff及`browser/topic-prototype-assertions.json`；不将离线原型当线上办事验证。
- API339/340为CI分支配置不匹配，341为新增MySQL测试泛型断言编译失败，均保留FAIL并已修正相应输入。342仅CI候选进行中，非部署；最终状态见handoff后续补记。
- 正常业务统计不变；文件交付、真实新话头发送和验收链仍需继续跑，禁止据源码检查或局部测试宣布全部通过。

- 16:55补记：API342 CI-only SUCCESS，583b347，3311总项/164跳过/0失败错误；新话头HTTP4项、service6项、preview7项、MySQL37项全部执行通过。同Run制品摘要和日志见handoff。Web合并后a73a49b轻量98+6项通过。**未生产迁移、未部署、未真实站点N08回归，因此正式业务状态仍不改为PASS。**

## 2026-10-27 22:55 单会话发布后真实页面回归

- Web **1.16.69 /960841394c5f671b5615b6b1bef9e802722cd1ec**，Flow4403172/366 SUCCESS，首次终态259.1秒。正式3492 passing、2 pending、0 failing；同Run制品SHA256及公网入口/聚义厅入口JS摘要匹配。默认配置已CAS恢复。详见single-conversation/release/verified-366.json；本轮未发布API/Runtime或迁移数据库。
- 真实chcbz页面539：刷新应用→原事项→继续议事，仍恢复原需求和回复；历史只显示原记录，无另起/删除入口。桌面与390px截图已留，手机scrollWidth=390。此证据仅覆盖单会话恢复/布局，不冒充整条N25或普通聊天实页回归。
- v5技能回执读取和UNKNOWN父子展示已发布并实页复验：539现在显示“结果待核实”，不再将讨论父请求完成误报为文件已完成。截图browser/task539-discussion-366、task539-history-366、task539-mobile-366；无自动重发。
- **N16仍未通过**：539 Runtime本地native-model effect为UNKNOWN，无result.json、无输出文件；只能证明执行结果未确认，现有记录不能还原原始invoke异常，不认定CPU/内存为根因。脱敏证据single-conversation/task539-runtime-evidence.json。
- 外单新540：ziyue实际选择“吴用 / 其他用户·在线”，22:43确认承办并自然进入议事。22:51:48权威首轮请求仍RUNNING/turn DISPATCHED/lastDeltaSeq=0，22:50页面仍“正在理解”；尚未首答，不能记X03回归通过或继续发送第二轮。证据ziyue/external-*、single-conversation/task540-first-response.json。两账号有Agent，严格零Agent样本缺口仍存在。
- 原37条并未全部通过；N08按批准范围延后，文件交付及新外单首答仍是功能阻塞。保留旧失败，不以单测/发布成功替代业务验收。

### 2026-10-27 23:00 外单540阻塞证据补充

22:57实页仍无首答。只读找到本次精确request的Runtime inbox recovery：`state=ACCEPTANCE_UNKNOWN`，`recoveryReason=TURN_ACCEPTANCE_UNKNOWN: APP_SERVER_RPC_TIMEOUT:turn/start`，receivedAt1793112320968、claimedAt1793112326374、recoveredAt1793112799790。脱敏证据`single-conversation/task540-runtime-recovery.json`。这证明请求已送达Runtime，阻塞发生在模型turn/start接纳/回读链路；不是“用户没有自己的Agent不能接外单”，也不能把RPC超时进一步推定为CPU/内存不足。当前接口仍RUNNING而恢复记录已UNKNOWN，需继续核对该精确请求的ACK同步及原turn权威回读；不得重发、改库终态或凭未知结果验收。已安装adapter在turn/start异常后会尝试thread/read reconcile，结果未形成已完成回执，不能绕现有未知执行保护。
