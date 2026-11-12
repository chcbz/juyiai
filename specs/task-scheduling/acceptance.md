# 验收范围

## 当前提交状态（2026-11-12，本次范围完成，提交用户验收）

- **API生产**：`c7c0f2d78d4de51d4caed81cfe2caa1a6835b565` / `1.1.48-SNAPSHOT`，PID1884855（22:51仅报价配置重启），固定JAR SHA `9edc1650750a998a3b7e650b8d04c17ea9376e6d37d39399650daf0a1189dfd6`。原`api-final-1`146项、layering、fresh JAR通过，197.962秒；本次复用制品，无重复构建。原安装器实际installed、身份/摘要匹配、HEALTH=UP，监控已恢复。
- **Web生产**：`c453e0898642b0aec80677df71c088f74563a349` / `1.16.134`。原`web-final-2`101通过/2原pending，177.303秒；本次原安装器32.002秒完成，613文件、30变更、256线上资源核验，record为online_verified。匿名真实桌面/移动浏览器均到达正常OAuth登录页，证书验证未关闭、无横向溢出；随后使用用户提供的账号走正常OAuth登录，已核对chcbz/用户5与李逵owner一致；真实桌面/390px移动个人中心及钱袋通过，可用3487文/预占1文，李逵模型gpt-6-luna。此为只读子集，不是资金全链通过。
- **数据库**：实际停API写入后备份24个受影响表到`/home/isp/baks/task-scheduling-20261111-production/affected-tables.sql.gz`（174722字节，摘要在production-switch-1/result.json），原配置/发布记录同时保存。固定独立迁移资源`87ccfef032662f15c5c60a820403b8edb2f65c66`的11项SQL已执行，逐表字段与schema-rehearsal-1完全一致，迁移前后业务行数不变。ES两scope关键词映射此前已完成，未读写旧文档正文或猜测归属。
- **实际免费接入**：吴用、林冲、卢俊义、李逵均已由正式维护CLI登记TRANSITION；实际cutoverAt固定`1794405723301`，30天租期不因后续重试改变。托管正常周期500文、自部署50文，周期2592000秒；两不可变套餐v1已登记。托管报价有效期300秒只属于托管报价，不改变事项报价无TTL合同。四租约ACTIVE、免费意图0文且无虚构报价/预占/扣款引用；交易总数仍74，没有新收费。原输入生产幂等重放13.131秒完成，独立回读同4租约/期限及交易总数不变（production-cutover-replay-1/readback.json）。扈三娘无已核实控制端点明确未接入，无安装关系不造事实。
- **统一调度已激活**：稳定node-id `cyf-api-prod-01`，GENERAL2/CONTROL1、batch2，lease/recovery60秒、retry/owner-retry5秒。这是2CPU主机初始后台容量，不是业务请求deadline或性能门禁。真实数据库已观察8条cron注册、123条时点工作记录（持续变化，非固定数量合同）和两个租户用户续费期限；最终源码的慢工作与租费隔离、Redis客户端失联/接管已在隔离实例定向通过（见下）；未在生产注入故障。生产Redis4.0.6单master/无副本，不冒充HA证明。
- **Runtime**：李逵已安装bbf8db06a36a9fc48d1441d5cce9d639e4d4a80b / 1.3.102 / bridge1.1.71、PID389574，354.374秒，原profile及host配置字节未变，新channel/ACK通过。该候选407PASS/10显式跳过/0FAIL，测试打包298.684秒，制品SHA c2b495d40298d888eb5286bdf05ab64132a8158ca79dd15985676c1a66e7d771。本机首轮备份ENOSPC、次轮备份及比较超过600秒，实际668.838秒含恢复；未把超时重标成功。前两次失败后曾恢复7985667 / 1.3.99 / bridge1.1.69，PID1963995。后续用户授权缩小备份范围后，第三次复用同一制品已安装1.3.102，PID2138777，154.760秒；新备份609422793字节，源码/配置身份不变。通道验收75.450秒通过，另两次间隔35秒的三Agent新心跳均connected/registered/ready，三个原生启动测量均ready。证据`local-runtime-native102-3/{result,acceptance,native-and-channel-followup}.json`；原失败不重标。网关17组精确路径已安装，不重开全/internal。
- **已登录真实事项闭环**：同事项648恢复正式议事，停止原pre-model网关失败回合后在原事项补充一次请求，李逵回复20字内欢迎语；UI选择成果并确认验收一次，事项已完成。SQL证明唯一预占1文、唯一验收扣款1文、escrow CAPTURED、可用3486；截图已查看。对话终态实际token证据input13104/output148（reasoning90含于output）已落库，按原合同保留UNVERIFIED/PENDING_USAGE，不称零成本/完整核销；两次推荐已知成本0.006457元，任务共3attempt/1pending。详细证据与边界见handoff 00:33。
- **失败如实保留**：production-switch-1在迁移/接入成功后因新增全局client缩窄原OAuth允许集合而启动失败，89.792秒；原FAIL保留，forward-only未恢复不兼容旧版。删除该不该新增的限制，保留原tenant和多client准入后重试；过程中发现API服务用户读不到root-only TLS文件，已只给cyf-api四级目录穿越及三个确切文件只读ACL，未授予写入/列目录/世界访问。第二批实际安装成功，但外层因monitor lock busy记录FAIL/169.929秒；原记录未改，另行恢复监控并以实际record/PID/HEALTH与production-switch-observation-1核实安装成功。未重新迁移/发放或重建包。
- **集成**：API独立SQL/docs HEAD87ccfef032、Web c453e08已FF合入本地和远端develop，ls-remote回读一致。实时只读云效source配置triggerEvents均为空，没有启动付费Run或改云端配置；原主工作区脏内容/分支及根gitlink保持不动。
- **真实知识Provider→中心账本**：`live-knowledge-sql-3`固定API87ccf/Runtimebbf，真实提取与复核两次调用经installation HTTP及实际MySQL形成2条PLATFORM attempt、4个revision，全部PRICED；重复flush不重复调用/记账，用户资金交易为0，关闭租约/撤销安装拒绝旧证据。1项联合测试及layering通过，314.425秒。使用合成会话、普通身份协作者和明确测试费率；0.002082元仅为测试算式结果，不是生产账单。原私有输入仍保留，不声称已做生产交接清理。
- **最终租费/调度回归**：`final-lifecycle-api-1`固定API87ccf/tree09697df29b5c7aac779ab5f3ecb1a53ac11f615e（相对生产c7c0仅迁移SQL/文档差异），7类64项全部通过、无跳过，layering通过。含18项真实MySQL续费/过渡/余额唤醒/15天边界/并发停止/首费不带入月租/交接绑定，以及收尾、旧事项继续执行、新入口限制和Redis客户端失联接管。441.611秒，其中受限阶段300.761秒、真实集成140.843秒；不是生产故障演练或完整远程关闭重邀。停止的合成MySQL仅data已回收，日志/源码/报告保留。
- **最终跨端交接子集**：`final-closure-api-1`以API87ccf/Runtimebbf真实源码运行2项、0失败/跳过，layering通过。托管链实际MySQL→Java UDS→Runtime完成500文首次扣款、旧关系停止/私有session清理/公共技能保留、原安装撤销及关系释放、新用户550文重新邀请与新安装ACTIVE/唯一扣款；重复旧完成不影响新关系，真实分录平衡。另验证自部署现存实例adopt/停止/证据重试/清理，未签发额外凭据。383.759秒（受限261.291秒、集成122.029秒，尾部依赖复核另计入总耗时），Runtime源码逐文件及依赖前后摘要一致。普通账户目录、executor注册/知识Provider仍为fixture；自部署此用例不包含50文实际账本完整重邀，不扩称全部生产整链。
- **扈三娘宿主**：`husanniang-host-observation-1`当前只读生产查询确认该实例offline，host为`chc-223-6c3ee548-aab2-48a1-8ce1-e47d40cdab54`；记录endpoint为平台WebSocket连接地址，不是可用宿主控制端点。没有将未知宿主误归本机/李逵，也未登记过渡或扣款。
- **两套餐资金/交接组合**：`selfhost-final-api-2`固定API测试候选d5754586f01d93ade54be6294ab37fb1b13b2467/tree876bb31a1fd6bc698b1f92db40742c9aa0df6cc7、Runtimebbf，两个真实MySQL→UDS→Runtime生命周期用例及layering均通过、无跳过。可信host配置选择50/500文套餐；自部署首次50文，原关系关闭清理后新用户保留1技能重新邀请收100文（周期50+首次技能50），新租约周期仍50；托管对应500/550/500。验证同一公共实例/技能保留、私有会话删除、旧安装撤销、新安装ACTIVE、捕获次数及分录平衡；共享helper不复制费用实现。294.435秒、受限205.741秒/集成88.018秒，最低空闲371716096字节。此处本地UDS及明确账户/executor/provider fixture不声称生产远程关停；远程mTLS及静态adopt保留各自实际适配器证据。首次ENOSPC失败原件保留，未改业务实现/超时/断言求通过。
- **测试源码集成及磁盘收口**：d575已FF本地/远端develop，实际查询Flow source triggerEvents=[]，未触发付费构建。仅测试变更，不重建/更改生产c7c0 JAR。停止的合成MySQL及已终态classes/非starter模块JAR已按精确记录回收；16个历史源码展开副本经tar --compare及SHA验证无损压缩保存，当前Runtime源码、正式应用JAR/包、测试报告/日志和有效生产备份均保留。02:20根盘观测782MiB可用，不是新资源门槛或未来安装空间保证。
- **本次范围与后续待办**：用户2026-11-12明确“扈三娘后面再处理”，其宿主接入与该实例验收延期，不再阻塞本次交付；未接入、未扣费，后续仍需宿主地址/连接方式。本次收费、统一调度及已接入四实例的发布范围已完成，提交用户验收，不代表用户已经验收通过。本机最终102已在原600秒内完成安装和通道/原生启动验收，不再需要20分钟例外。实际Provider到中心账本、最终租费/调度和两套餐完整资金交接用例已通过；生产故障注入及真实用户破坏性关闭重邀未执行，不以隔离回归冒充这些线上操作。

证据根：`/home/isp/state/cyf-local-build/tasks/task-scheduling-20261109/`。主批次`production-switch-1/2`、`production-control-access-1`、`production-switch-observation-1`、`production-web-install-1`、`production-browser-entry-1`、`local-knowledge-route-1`、`likui-knowledge-route-1`、`component-integration-1`。历史测试/安装失败保持原件，详细时间与恢复见既有handoff。

- **本轮只读复核**：`production-ledger-audit-5`四类账本异常均0，42账户/76交易/152分录，可用3486文，未新增扣款；API健康UP。`production-service-user-control-3`真实API UID987到李逵mTLS通过、错误owner/缺证书拒绝及固定API路径测试通过。未新增付费事项、未重放迁移/过渡，历史任务648和固定源码组合回归保持各自证据范围，不冒称本轮重新执行生产关闭/重邀。备份保留plan无eligible项，最近两份仍保护；磁盘余量约165MiB，不把安装成功解释为长期容量充足。

## 历史提交状态（2026-11-11 16:42，本地/远程控制定向通过、整体未交付）

- API `c2f717dac45cb122192f8cedd0cb68f55fbe00fb` / tree `0f3f5cafb5e3aff4c27747c31e9f3811d55f6344`，Runtime `8e556e9f7611c69593e09a6fe486eb47554ebb2b`：`tls-api-3`真实执行99项，**97通过、2失败**，486.248秒，layering通过。实际Java→mTLS→Runtime静态探测/adopt/current/停止/证据/私有清理通过，缺客户端密钥及错误服务端身份被拒绝；应用28项和免费重整H2事务5项均通过。
- 未通过项是原本地UDS握手的精确字段断言（fixture新增remoteAddress:null）和静态清理第一次调用返回false。前者已改为只在TLS fixture返回该字段；后者未猜测为成功或超时，增加直接exchange异常/响应和Runtime安全阶段耗时诊断，保持原超时/清理断言。
- 修正候选API `897e5095800f7fc294b0858f04b2767a4954d654` / tree `0f6e6875110780d84ba03e3eff39f9a29d0dc7ea`，Runtime `bd73fe4`（测试fixture变更）：`tls-api-4` **29/29通过、0失败/错误/跳过、layering通过**，489.176秒（全部计入本次600秒）。实际Java TLS链8.793秒、原托管UDS链30.095秒、静态UDS链1.979秒。本地UDS同样增加选中hostId回显核对，避免错主机库存进入报价。静态首次清理本次CLEANED实测32.997ms，原false未复现；初轮无原因信息，不能反推成已证明的超时或重写原FAIL。此前通过的70项未重标为本候选完整验收。当前本任务无在途构建/测试。
- `tls-api-1`是任务源码pin未更新而在Gradle启动前被拒绝；`tls-api-2`是新增fixture缺Map引用而编译失败。原FAIL与归因保持，不能并入后续成功。每批独立600秒、串行、普通磁盘短tmp，无应用超时调整。
- API候选已接入可信host路由和Spring SSL bundles；李逵仍运行此前Runtime1.3.71、PID306359、没有hostingControlPath/TLS端点，未新增生产扣费/清理/发布。自部署50文计价与Web确认、两模式存量30天过渡/首次调度、legacy canonical ID重邀及最终迁移/发布/真实验收仍未完成。

## 先前子链状态（2026-11-11 16:08，Runtime端通过、整体未交付）

- API `b49120979dc04eec629a443fa20492932dea2358` / tree `ad0595efb45132b58887e5a3af5b29ee557db012`：`adoption-api-1` **62/62通过、0失败/错误/跳过、validateLayering通过**，356.945秒。包含实际Java→UDS→Runtime的静态adopt/current/停止/证据/私有清理、原托管UDS链，以及安装锁与免费重整无注册元数据；未生成最终JAR。原生注册/执行器和知识provider仍明确fixture。
- Runtime `2488e71dfb869572937eb0fc97fe364d563aea91` / tree `8de91ed2d655a87d3a3dc51d24d9b0fed73257d4`：`adoption-runtime-2` **232/232通过、0失败/取消/跳过**，124.130秒，依赖摘要前后一致；包含实际私有目录清理、同HOME重新邀请和旧关联失效。后续 `e54aa6c`只新增Java跨端静态fixture，已随上述API62项运行；未把前轮232项重标为新源码全量通过。
- Runtime远程控制候选1.3.98：`121efd99924846b7cc8d4116f731e5a5d58d2548` / tree `c29cd9bae595acbd519895ef717df095cb42dd87`，`tls-runtime-1` **235/235通过、0失败/取消/跳过/待办**，150.318秒。实际TLS双向认证和原UDS共享journal，Agent停止后宿主仍可回收证据；覆盖客户端缺证书/不可信证书、服务端身份不匹配、超大帧、私钥权限错误及启动失败清理。
- 后续`6ccbfcbb41cc26ecbd635cd66d56c5cbda4e796b` / tree `b6d47b9fad36c33ff2eaedde6a31252ec2f11bde`只补TLS配置边界测试与运维指南，`tls-runtime-2` **12/12通过**，9.426秒；含凭证不得放入Agent可写目录、别名和不安全CA权限。两批各核对582个Git blob及相同依赖摘要；第二批没有重标第一批为最终源码全量验收。使用本地临时证书，不是李逵远程实测。
- 存量身份入口 `cac049e991` 28项通过；续费套餐绑定 `0c583d6c77` 20项通过。证据分别为`existing-identity-api-1`、`renewal-plan-api-2/report-audit.json`；不改写后者原汇总误判FAIL。
- **剩余真实缺口**：API远程宿主路由与TLS客户端接线、自部署50文报价/确认与套餐路由、存量两种模式30天过渡租约和首次调度登记；随后生产DDL/ES mapping迁移、最终fresh制品/受控发布、真实Web/WS/钱款/故障与混合容量验收。
- 李逵本次仅已升级到已生产验证的Runtime1.3.71/bridge1.1.59，在线ready通过；未安装本轮1.3.98候选，未接入收费或执行真实清理。主任务没有新增生产扣费。
- 证据根仍为`/home/isp/state/cyf-local-build/tasks/task-scheduling-20261109/`；`adoption-runtime-1`保留原7项失败及归因，第二批才通过。当前无本任务在途构建/测试进程。

## 先前子集状态（2026-11-11 14:08，托管组合验证通过、整体未交付）

用户本轮两小时目标截止北京时间14:55；不是应用请求超时。仍需完整产品与上线证据，不能以测试通过替代交付。

| 范围 | 最新可核实结果 | 尚缺 |
|---|---|---|
| 托管关闭→重邀 | `closure-api-5`完整API/MySQL/UDS组合PASS：500文首费、停止/私有清理、旧租约关闭与安装撤销、保留技能、新报价550文/新关系ACTIVE及扣费、旧回执不影响新关系、账目平衡；分层通过 | `closure-api-6`已在默认60秒窗口重复通过全链，冷库存30019.752ms、后续2893.541ms。账户目录、executor注册、知识Provider仍为明确fixture，不是线上验收 |
| Runtime冷库存与完整性 | bba4f8b：去掉同次测量重复全量哈希，保留文件前后状态及实际执行身份核验；测量期间同size/mtime篡改有拒绝回归。固定source7组合135个唯一用例PASS，原生库存用例28.95秒 | 完整组合默认窗口现已通过；未安装，不承诺任何生产负载都低于该时长 |
| API线上基线 | f3a97a5224已合并当前部署cbeab0d8c5，避免回退已上线session/WS刷新修复 | 合并后实际执行101项全部通过（0失败/错误/跳过），含认证/WS/维护权限与真实Redis客户端失联接管；未生成最终JAR |
| 生产Redis与Memory | 有独占Redis/ES定向测试；本机Redis进程/监听已只读观察 | 只读INFO已确认Redis4.0.6单机master/无副本，生产JAR默认127.0.0.1:6379/db0；不等于故障接管验收。Memory生产mapping及数据库迁移未执行 |
| 未实现业务 | 平台托管首费、周期费、已有技能首费及维护账本有分层证据 | 自行部署50文完整生命周期、存量Agent收费切换仍未实现，不是改价格即可 |
| 交付 | 源码与原失败/成功证据保留 | 最终fresh包、受控安装、真实Web/WS/资金与故障验收未完成；没有新生产扣费或付费模型调用 |

证据目录：`/home/isp/state/cyf-local-build/tasks/task-scheduling-20261109/`。`closure-runtime-7`仍记134PASS/1SKIP的FAIL；同一源码和依赖的`closure-inventory-8`补跑全部6项后，组合记录为`closure-runtime-combined-acceptance-8.json`，不改写原失败。当前API回归记录为`closure-api-6/result.json`：101/101 PASS、分层通过、1866.891秒；API完整commit `f3a97a5224bf29f3f7a2761b2385e8690b888d45`、tree `f06853285388dc837abe29b460dd129e24ada96c`，Runtime完整commit `bba4f8b3913721bd6a2124b365b1477296bd645a`、tree `dd52728fec8636c47e7e664a5a858d320a0256c4`。

以下11:58记录保留为历史；不得据其将已通过的重邀组合再次列成同一个未修复故障，也不得把诊断窗口成功当默认窗口成功。

## 历史提交状态（2026-11-11 11:58，验收未通过、尚未上线）

本轮“去过度设计/临时旧路径”整改已提交代码，但未完成完整收费闭环，不能作为上线验收通过。

| 范围 | 已完成/可核实 | 未完成 |
|---|---|---|
| 去旧流程整改 | 删除旧托管文件开通状态机、publisher及无调用写DAO/Mapper；保留历史只读表/实体及现行投影通知。生产责任层不新增框架，复用同事务锁定绑定 | 最终应用JAR尚未产出；不把源码删除当部署完成 |
| 受影响API测试 | 121个独立单测/Mapper用例通过，报告及与最终候选未变输入已核对 | 不包含失败的组合生命周期用例 |
| Runtime测试 | e543c40候选61/61通过，87.993秒，依赖前后摘要不变 | 最终20e2b7c仅新增组合fixture安全时序日志；真实生产WS/Provider验收未完成 |
| 真实API/MySQL/UDS组合链 | 走到首次收费、旧关系停机/清理/关闭、保留技能后重新报价550文及确认 | 新关系未到ACTIVE，最终扣款/重新准入断言未通过；不得称完整闭环 |
| 统一调度/维护成本 | 持久领取、协调、CONTROL容量与已迁移消费者有分批证据；平台维护账本已有真实SQL验证 | 生产配置、Redis故障接管、ES迁移及真实混合负载未验收 |
| 其余收费及发布 | 规则已有记录 | 自部署50文、存量切换尚未接入；真实Web端到端、最终包、受控安装和线上资金验收未完成 |

**最后一轮明确失败，不是PASS。** `closure-api-4`：1个组合用例FAIL，分层检查已执行；fresh bootJar因前置用例失败未执行。原生库存实测首次60074.081ms、后续965.988ms，首次超过默认60000ms传输窗口；测试临时显式使用120000ms后走过报价，但不修改生产配置、不据此宣布性能问题解决。新的失败点是Java组合fixture的RuntimeHost未接`admitRelationship`（只读运行诊断为`undefined`），而真实RuntimeHost重新准入要求该适配器；不能用无条件成功stub绕过。

API候选 `71b8033dea9de91bdfcb470068e004b43d1e7bc1` / tree `bbe36b797a9c222fdba35e7afd1ece038b0ae51d`；生产整改在其父候选 `ed5010e882450222eb59814a68a16a4f9dc04b68`，后续仅组合测试窗口变化。Runtime测试候选 `20e2b7cf55a017a278c72e6df2ca7d785d319f87` / tree `6ae6292b619fdf45000f36caea048b38f19af75e`，本轮相对7a7089d仅测试fixture变更。

证据根：`/home/isp/state/cyf-local-build/tasks/task-scheduling-20261109/`。保留`closure-api-{1,2,3,4}`原始FAIL、`closure-runtime-2/result.json`、`closure-api-unchanged-unit-evidence.json`、`closure-readmission-wiring-diagnostic.json`及时序日志。账户目录、executor注册与知识Provider仍为明确合成边界，不冒充真实WS/付费模型验收。本轮未生产安装、迁移、真实扣费或付费模型调用。

下一步只补组合fixture的真实重新准入接线并验证，再定位默认窗口下的冷启动；不扩大业务改造、不放宽身份/资金/私有隔离断言。完整上线仍受上表独立余项阻塞。

## 验收要求

1. 同一scope/业务键重复登记不生成重复执行；不同租户、用户及节点任务互不串扰。
2. 业务事务回滚不留下余额待办；提交后进程立即崩溃/通知失败，重启或兜底仍能恢复。
3. 事件在领取前、执行中、完成并发时到达均不会丢；旧claim不能覆盖新revision或取消状态。
4. 两容器争抢、所有者宕机/失锁、旧执行者迟到，钱款只按同一期次扣一次，状态写回有正确归属。
5. 入账登记与续费并发，真实MySQL验证没有钱包/调度反向锁序；不能用Mock替代资金原子性。
6. 无待办不反复查询业务表；余额事件仅检查对应用户。记录真实查询计数，不承诺零Redis协调或零数据库兜底。
7. 最近dueAt提前、取消、批量到期与重启恢复均正确；慢处理器不阻塞时间唤醒。
8. 未知handler不丢任务；重复注册不静默覆盖；异步失败能查到真实结果；无通用参数绕过收费授权。
9. Memory等迁移项只有一个定时入口；旧TaskPlan创建/修改/提醒查询不受新表影响；灰度禁用继续生效。
10. 节点文件恢复不被另一容器消费；连接心跳和执行续租不误变全局单例。
11. 费用消费者另验证可用余额、自动续费排序、欠费恢复起租、锁定超15天移除竞争、旧事项继续及技能预占结算。

源码/selector/fixture和实际测试、安装证据沿handoff记录；生产迁移及已安装组件见本页当前提交状态，以下早期验证记录不代表当前线上。

## 已验证子集与未验证边界（2026-11-09）
- `ScheduledWorkStoreMySqlTest`：生产DDL/Mapper、实际租户插件、Spring事务，独占本机MySQL8.0.21测试实例；20项全部执行，无跳过；还覆盖提交后通知合并、回滚无通知、嵌套事务、通知失败不影响提交、最近期限、worker/未知handler与关闭语义。业务事实与登记同时提交/回滚、存储失败回滚业务事实、独立连接可在回调前登记、新事件保留、并发worker唯一领取、SKIP LOCKED不等待、并发事件合并、分区在LIMIT前生效、节点归属、接管后旧token拒绝、取消/改期优先、CAS、续租、禁止worker嵌入钱包事务、精确字符串键和索引/无CHECK均覆盖。
- 存储恢复测试是**重新创建store并接管数据库过期claim**，不是容器重启/Redis故障演练；并发是独立数据库连接，不声称已运行多个生产容器。
- 早期存储测试只用最小业务事实表；后续HostingRentRenewalMySqlTest已接入真实EconomyPostingService/租费服务/调度store验证同库事务和锁序，不代表关系交接/生产多容器故障验收完成。
- 首轮真实测试暴露重复租户解析导致锁定SQL语法错误；保留失败证据，限定新Mapper跳过重复改写后回归通过，旧Mapper公共隔离未改。
- 新增Redis双客户端6项、runner查询计数3项、手动执行边界2项、条件装配/灰度禁用3项；与原有core22和Task业务14项共70项。Redis失败无降级为注入异常测试；真实网络分区、容器宕机及混合慢任务负载仍未验收。
- 经济posting及旧hosting共43项H2事务测试，通过余额增加同步事件、重放不重复发、观察者登记失败回滚、非可用资金增加不触发。Agent订阅适配4项为mock调度接口/真实条件装配验证；后续真实钱包→调度→租约自动扣费MySQL15项已通过，详细范围和局限见下项。
- `HostingRentRenewalMySqlTest`15项验证生产DDL/catalog、真实发放与幂等重放、可用余额扣款、最早期限、不足不阻塞、同到期稳定排序、101项欠费后的可支付尾项、严格15天、FINISHING仍保留实例slot、失败同回滚、并发付款一次、并发入账锁序及分区；与适配4项/原资金43项同候选共62项零跳过。FINISHING只登记待办，没有关系解除或Runtime隔离验收。
- cron、旧任务切换、关系移除/私有交接和发布尚未完成。上述完整条目不能据此全部勾选。

准入候选c800400c3d的Agent租期门禁3项、授权54项、既有事项领取34项通过；同轮Chat源集编译失败，未执行派发/密议测试，失败记录保留。d06503d0c3已补现有测试辅助类及最近用户期限同事务登记/两个MySQL回归，尚未运行，不冒充最后候选已全面通过。


### 2026-11-11 双模式收费入口候选验证
API3fdfb9d724的54项覆盖两种mode共用真实HTTP信封/资金应用边界、缺省/null/free请求拒绝、50文套餐、原套餐续租、库存/主机类型变化、免费重整事务及lease.planId投影。Gradle257.117秒exit0/layering通过；外层driver exit143原因未明，原result保留，独立completion-audit核对全部XML及摘要，不宣称外层或发布通过。Webbf6d870定向51项及1440/390/320三视口18检查通过，包括报价类型不匹配禁确认、200文首费/50文周期及local确认字段；浏览器HTTP为合成fixture。证据：`/home/isp/state/cyf-local-build/tasks/task-scheduling-20261109/pricing-http-3/completion-audit.json`、`pricing-web-1/result.json`及`pricing-web-1/browser/result.json`。当前未迁移生产、未发布、未新增扣费，存量过渡/最终李逵全链仍待验收。
