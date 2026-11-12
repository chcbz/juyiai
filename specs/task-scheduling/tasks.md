# 实施任务

## 当前入口（2026-11-12）

API c7c0f2d78d、Web c453e08已生产安装，11项SQL迁移87ccfef032已执行，四个真实实例已登记固定30天免费过渡，统一调度已启用。用户正常登录后，李逵事项648已真实完成回复、验收与唯一1文扣款；不再把登录或该事项原生就绪列为阻塞。Runtime最终1.3.102候选已完成407PASS/10显式跳过的回归及制品，李逵已安装，本机在保留原失败后第三次154.760秒安装成功，三Agent通道及原生启动测量通过；真实知识Provider→中心平台账本联合验证已通过（合成会话/测试费率）；最终API租费/收尾/调度64项及layering通过。最终两套餐资金/关闭重邀组合及自部署静态停止/清理验证通过；测试候选d575已合入本地/远端develop，生产应用实现未改。本机最终安装已完成。用户2026-11-12明确扈三娘后续处理，其宿主接入及实例验收列为延期待办，不纳入本次交付；当前范围完成并提交用户验收，不表示用户已验收通过。精确线上状态、原失败及剩余工作以[验收](acceptance.md)首节和[handoff](../../docs/implementation/handoffs/TASK-SCHEDULING-UNIFICATION-20261109.md)为准；以下旧勾选只作历史，不覆盖当前结果或作为重新执行授权。

## 历史实施记录

Owner：本会话；调查基线API49f6b4d20。实现工作区 `/home/isp/wsps/worktrees/task-scheduling-api`，分支 `codex/task-scheduling-20261109`，基于实际查询并fetch的develop c661e6421346d610ee063b0fb9b614e282e7bcca；不覆盖主工作区其他修改。联合验证候选2dd788cb0bda04a5d5f24f78ecc3a95da6c74bba已通过196项及分层检查。bd7d8d34c85838d4e5bd2ea0a9836d547c161715主动停止续费已通过72项定向验证。ee943d71845496e31bf55a95936ce54dc9f75d46技能50/20文与新技能租期准入已通过65项及分层检查，未合入/发布。

- [x] 调查task注册/cron/执行器及旧计划业务消费者。
- [x] 定位余额统一posting、现有进程内通知与实际锁顺序风险。
- [x] 整理调度/业务职责、作用域、可靠待办和验收候选。
- [x] 无I/O调度状态模型与原子唯一处理器注册：22项测试及validateLayering通过；不等于持久化/多容器实现。
- [x] 固定Redis协调实现：同线程锁归属、通知合并、集中恢复；独占Redis双客户端回归通过。
- [ ] 生产Redis拓扑/真实断连接管演练；不能以测试客户端代替生产高可用证据。
- [x] 固定DDL候选与同库事务存储、claim/version、过期接管；14项真实MySQL回归通过，包含现行TaskTenantConfiguration插件。未执行生产迁移。
- [x] 调度worker、事务提交后通知、单次期限发现、节点归属/灰度开关和条件生命周期装配；70项task测试通过，未启用。
- [x] cron及错过时间恢复源码：6cd01771f1/79f545c4e1已通过真实MySQL发生点/游标/维护分区回归，详见handoff；未生产启用。
- [ ] 生产迁移与真实混合任务容量验收。
- [x] 统一posting余额增加事实扩展；43项H2真实事务回归通过（含旧租金事务回归），无额外Agent查询。
- [x] Agent余额订阅适配4项验证：当前分区、用户键、异常传播、默认不启用；无Agent查询/扣费。
- [x] 实际钱包→调度→续费切片：MySQL17项（分区、并发、到账、排序、回滚、15天边界、锁序及下一期限原子登记）通过；关系移除与私有交接仍未实现。
- [x] 新承办/新密议资格门禁收口，旧事项派发不重复拦截：联合196项验证通过；不等于关系收尾或全部收费完成。
- [x] 主动停止续费资金事务与并发/回滚验证；精确租约移除HTTP候选6b6db73257已通过47项及分层，Web/目录投影/实际收尾尚未完成，不可单独上线。
- [x] 技能固定50/20文、报价确认/结果结算和新操作租期准入：65项定向验证通过；主动取消新协议及完整发布仍待完成。
- [ ] 接入其余收费业务及关系收尾；费用规则按用户确认实施，不能以调度完成代替收费完成。
- [ ] 逐项切换已有系统后台任务，关闭对应旧定时入口，保留原队列业务责任。
- [ ] 本地正式回归、validateLayering、fresh包和授权受控发布；遵守用户本轮提供的AGENTS：同一固定源码/批次受限阶段累计600秒，不按阶段或重试重置；真实集成回归另计，不将单元测试改名豁免。扩时仅用于明确获批候选，普通磁盘。
- [ ] 多容器/重启/业务验收、文档收口及临时目录回收。

## 2026-11-10 当前消费者核验（源码不等于上线）

- 已验证迁移：hosting-rent.provision、skill.native-delivery、推荐usage本节点恢复、native订阅通知恢复、事项Bootstrap恢复、成果投影恢复。具体固定源码/报告见既有handoff，均未随本节发布。
- 成果投影43ab7beeca：即时提示继续合并，统一30秒节点恢复，SQL发现前置tenant/client；12项单测+3项真实MySQL及layering通过。
- Agent状态迁移f8aae90f1e：本地连接刷新与集群超时扫描已拆分，15项及分层检查通过；完整线上验收仍未完成。
- Memory、Wx迁移源码与定向回归已通过（2026-11-11，见下）；Memory真实隔离ES10项验证已通过；生产mapping迁移、混合容量与全消费者最终审计仍待收口。ArchiveQuestionWorker业务发现、命令恢复（保留原关闭开关）、AgentTaskEventReplay已验证迁移。连接/SSE/执行租约心跳保留本机归属。
- ChatBountyExecutionRelay已退役且未注册为组件，其Coordinator不再执行旧协议；不得为了清理计时器重新启用。Asset投影服务则仍服务原生协议5，不得误删。
- 完整租费闭环仍缺保留技能全量库存/首期报价冻结/新关系技能资格、首费与基本续租分离、自部署50文/既有30天过渡和真实关闭→重邀链路；生产迁移、多容器/混合容量、Web桌面移动端验收及最终发布仍在总范围内。

- 密议Outbox25c5444ecc6：统一持久唤醒、原并发容量与本机执行租约保留，34项（14单测+20真实R8）和同源分层通过；未上线。

- 事项事件补查e507d428f8：71项（含原20次竞态重复）及同源分层已通过，精确case核对凭据见event-replay-scheduling-2/verification-audit.json；原外层数量误判FAIL保留，未上线。用户2026-11-10在本会话临时取消本任务时限，仍记录耗时，长期规则未改。

- Rabbit出站调度迁移d4a1afc7a3：38项及分层检查通过，包含真实H2事务/固定client发现。命令恢复b6c29aaaad另批35项及分层检查通过，包含原H2事务和新增固定client分区；二者均未发布。
- 本任务2026-11-10后续本地验证/构建/发布暂时取消时限（用户明确授权），实际阶段/墙钟耗时仍记录，原超时/失败保留；不修改项目长期规则，不减免锁/授权/完整性及恢复保护。

- Archive问答发现与JobExecutor无业务作用的旧cron扫描：API8e015b3b3a，Archive76+task18共94项及分层检查通过（0fail/error/skip），含真实MySQL2项与受控clock真实续租/过期反例。归档私有范围由配置提供并在SQL发现LIMIT前分区；原任务业务lease保留，旧TaskAlert没有被自动激活。证据archive-question-scheduling-4，未上线。

## 2026-11-11 定向验证更新（未发布）

- Memory API0b99bdd02e：52项及layering通过，含真实MySQL发生点去重、前置scope发现；现有普通手动入口保留。同一STARTED/终态发生点不重做模型，后续周期可处理pending。ES SQL消费者已同步trusted client，真实隔离ES9.3.0节点10项验证已通过（API6e5bb6df71，memory-es-4），含前置scope KNN/topK/摘要limit及维护范围；生产mapping未改，不能提前启用。
- Wx APIc1578b9c94：63项及layering通过，含真实同库计划/调度事务、并发REPEATABLE_READ当前读竞争、外部发送前提交STARTED/结果回滚不重发。替换旧cron/Redis15分钟锁/内存DelayQueue；固定scope、随机期限持久化、精确模板/接收者、素材前置LIMIT及答题指针三维分区均有定向证据。缺省不重放未知发送，跨日过期待办不补发；未向真实用户发送，未执行生产DDL或发布。
- 以上仅关闭相应实现/定向验证项；生产Redis拓扑/接管、慢业务与租费混合容量、全量技能首费及正常续租拆分、自部署/过渡期、完整重邀及Web/上线验收仍待完成。
- 2026-11-11 首单/续租金额分离定向验证：API8803d6a393，`rent-recurring-split-3` 92/92及layering通过（posting26、H2 rent19、真实MySQL renewal47）。首次全额预占/扣款/退款，租约只保存周期金额，手动/自动续租不重复收首次附加费用；完整Runtime库存计价与生产迁移仍未完成，不将此资金边界测试当完整首费闭环。
- 2026-11-11 完整库存来源及只读端到端候选：Runtime faa0b322（1.3.93/bridge1.1.68）167项通过；其后仅fixture/测试变更7204b704，hosting40项通过。API7c2ae8aa35 20项及layering通过，包含实际Java→UDS→原生引擎库存（普通/项目/禁用技能、无Provider调用），并保留原生命周期回放。首期库存冻结/总价生成/确认时重核及新关系技能权益尚未接入，不能作为完整首次计费或上线完成证据。详情与精确输入见原handoff。
- [x] 2026-11-11混合容量源码858dfcc1cf：CONTROL/GENERAL独立有界容量、SQL LIMIT前筛选、handler期限索引及明确control-workers配置；`scheduler-capacity-api-1/result.json`51/51及layering通过，含实际租费与合成慢外部回调并行。只关闭源码/定向验证项；生产DDL、真实Memory/Wx混合负载及上线配置未完成。

## 2026-11-11 后续收费/交接验证更新（证据核对，未发布）

当前API工作区为`/home/isp/wsps/worktrees/task-scheduling-api-next`；此前源码/报告仍保留，不将旧报告重标为新候选全量验收。下列结果均已读取对应result.json，详细边界见原handoff：

- API9650453056 `prepare-inventory-api-1`88/88、Runtime456fe048 `prepare-inventory-runtime-1`通过：首期公共库存冻结与准备时再次校验；API2751453c8e `unissued-refund-api-1`56/56通过，明确FAILED_NO_EFFECT未签发凭据的退款路径，UNKNOWN保留预占。
- APIc69dbb5 `rent-lifecycle-api-3`28/28通过：实际保留技能新关系升级20文一次结算、原关系账本/权益不变，以及租约查询状态映射；不等于已完成整个实例交接。
- Web f2f2596/8e7019e：`web-rent-lifecycle-1`59项、`web-rent-lifecycle-browser-3`桌面/移动三尺寸组件回归通过。HTTP为合成fixture，尚无线上资金验收。
- API511fa4ad7d `reinvite-session-api-1`30/30及layering通过：真实身份SQL保留旧关系并选择当前live identity签发普通会话，保留授权围栏。
- API72d98fbe34/Runtime7a7089d（1.3.95）正在验证原安装维护费用授权：原账户停用不阻塞平台知识记账，但不得获得普通session/新执行资格。`maintenance-auth-api-1`61项目标仍在途。Runtime冻结验证缺依赖而FAIL，待补齐同锁依赖重测，不能以主仓诊断23项通过替代冻结验证。

完整待交付仍包含：API/MySQL→同一Runtime实际收尾/清理→重新报价预占扣费→新关系准入；自部署50文及两种存量部署30天过渡；维护认证的完整关系SQL/运行验收；生产Redis拓扑及接管、Memory mapping迁移、各调度消费者真实混合负载；最终固定制品、受控迁移/安装、线上业务验收和稳定文档/包回收。临时取消本任务时间限制继续有效，长期规则不变。

### 2026-11-11 后续定向闭合（未上线）
- [x] 新邀请在原子绑定时重置Runtime安装/host/instance/session generation，释放后待邀请仍保留原安装供交接核验；2126fe84eb，真实身份与Runtime SQL+普通session围栏34项PASS，1081.352秒。
- [x] 平台维护知识费用的真实installation/binding/intent/lease SQL与usage账本闭合：0949b3b4ed，实际Node HTTP跨端用例PASS+layering，590.871秒；关闭关系/撤销安装拒绝写入、旧账户停用不阻断原维护授权、原价和丢ACK重放均验证。普通session身份/account与provider仍是合成fixture，不等同于完整Runtime交接。
- [ ] 将上述SQL链与既有真实UDS Runtime收尾/清理串成完整关闭重邀验收；完整产品及上线余项维持上文，不以定向绿灯替代。

### 2026-11-11 11:58 本轮复审提交
- [x] 清除旧托管写路径与重复关系读取；受影响121项单测/Mapper证据核对，Runtime61项通过。
- [ ] 完整组合验收：最后失败于新关系重新准入；fixture缺admitRelationship接线，详情见验收页。原生库存冷启动60074ms另超默认窗口，未修改生产超时。
- [ ] fresh最终应用包、完整产品缺口与生产上线仍未完成。原失败不重标，无新兼容框架。

### 2026-11-11 14:08 最新子集验收（整体未交付）
- [x] 托管API/MySQL/UDS全链在生产默认60秒库存窗口通过：首费、停止/清理、旧关系关闭/安装撤销、公共技能保留、550文重邀/新租约ACTIVE/捕获、旧完成重放不影响新关系及账目平衡。完整组合仍使用明确account/executor注册/Provider fixture。
- [x] Runtime冷库存重复哈希收口及测量期间篡改拒绝：固定bba4f8b组合135个唯一用例PASS；API组合冷库存实测30.020秒，未提高生产窗口。
- [x] 合并已部署认证修复后的101项/分层通过，含真实Redis客户端关闭、watchdog过期后接管；只读核实生产Redis4.0.6单机master，无生产故障注入。
- [ ] 自行部署50文生命周期及存量收费切换仍未实现；最终制品、受控迁移/安装、真实Web/WS/资金与故障验收未完成。没有新增生产扣费。
- 本轮证据：closure-api-6、closure-runtime-combined-acceptance-8、production-redis-observation-20261111.json；原失败不重标，停止后的本任务MySQL data已回收，包外日志/报告仍保留。


## 2026-11-11 远程控制传输进展（未发布）

- [x] Runtime1.3.98候选在原HostingControl上增加可选双向TLS入口，UDS/journal/关系控制共用；235项回归通过，补充TLS配置/凭证根隔离12项通过。固定源码、测试范围及证据见acceptance，非生产证书/远程验收。
- [x] API共享provider已接入可信host路由与Spring SSL bundles客户端；报价/安装已有host时不再查询运行投影，库存/current/免费重整才单次精确查询。实际Java mTLS静态控制链通过；后续固定候选897e509580的两类29项全部通过，含原托管/静态UDS链，旧FAIL保持，整体不能标验收完成。
- [x] `tls-api-4`两类29项和layering通过，489.176秒；握手字段已纠正，静态清理本次实测32.997ms通过，原false原因无证据不猜测、不改写旧FAIL。
- [ ] 自部署50文同账本套餐及Web确认、存量双模式30天过渡、首个调度登记、legacy规范ID重邀及最终发布验收。不能仅因控制端可达就启用收费。

- [x] 2026-11-11 自部署套餐和双模式确认源码：API3fdfb9d724、Webbf6d870；按可信主机冻结套餐，原套餐续费，关闭HTTP/Web免费local入口，租约投影增加planId。域服务/路由前候选42项通过，后继HTTP/事务54项XML及layering通过（外层driver exit143见handoff），Web51项及三视口18检查通过；均为候选验证，不勾选生产发布或存量过渡。

- [x] 2026-11-11 保留legacy canonical重新邀请入口与身份责任层接线：API68fb800824，35应用+21身份+1真实MySQL共57项及layering通过（214.262秒）；原b89e8回执计数错误FAIL保留，见handoff。此为候选，不勾选30天过渡/生产迁移/真实李逵验收。
