# 修复项与待验证项全量复验（2026-10-22）

Owner：chat-stop-main，单Agent。核对时间11:15—12:14，北京时间。范围：上一报告O01–O08、V01–V06；用户补充授权第二测试账号。**逐项核对已记录，但动态验收没有全部完成，更没有全部通过。** 本轮没有修复代码、发布、重启、清盘、解除ES保护或清理生产数据。

## 1. 当前基线与昨日不同

11:16只读查询并fetch远端，不checkout、不覆盖工作区：

| 组件 | 本地HEAD | 当前远端develop / 安装来源 | 发布记录 |
|---|---|---|---|
| Web | 9dbd132e8bc25119c0532cbed672ab7fa4a214b3 | 5ec7e2096f838136ae71b6d4a66e148756aad54d | 1.16.40，Flow4403172/287，online_verified |
| API | 94b4c8a5e5b1402ef44097b5a337a75431a0ec1b | 6dc75fc632ad697bbe29c60a8a257c637ba937d6 / tree2e76b192ad45bda813f2b09f199f466bac0c5737 | 1.16.26，Flow5260799/224，发布回执verified |
| Runtime | 本轮不操作源码 | current实际指向releases/1.2.3，进程读取该目录 | 不沿用昨日1.2.2描述当前状态 |

API安装JAR记录摘要：01bf43ee8e88c8aa7985d5e7fe1620504e2e46672d1a6b524a87d4d36d8875da。Web制品记录摘要：6d43006dbc3f7c90047343d6fc98b161b03873fd223c83d503451f639b63d637。以上是版本绑定，不等于当前健康；本轮未重新运行正式Flow，也没有声称重新逐文件验证全部安装制品。

基线证据：`/var/tmp/cyf-reverify-20261022/baseline.json`及主机versioned-release-224.json。源码核对使用固定远端commit的git show，不拿较旧本地HEAD代表线上。

## 2. 必须先处理的新增阻塞

### B01：Elasticsearch磁盘水位保护使知识写入失败

- 11:25只读查询：逻辑索引chat_memory实际返回chat_memory_v2；read_only_allow_delete=true，ES节点磁盘96%，可用约2.1GB；主机df约97%。向量mapping仍为1024维。
- 10月22日02:00定时任务已启动，但会话同步写入报cluster_block_exception / flood-stage watermark；syncPendingConversations抛错后，后续日汇总没有执行。11:00再次同根因失败，待处理快照保留。
- 当前索引40条：20 project、19 conversation、1 daily_summary；日汇总仍为10月21日那条。不能把昨天成功或读检索可用当作今天写入可用。
- **处理建议**：先只读核对磁盘占用、可清理范围及恢复措施，由Owner进行受控容量治理；水位恢复后核对索引保护解除，再让原待处理快照补偿。不能在磁盘仍高水位时只强制解除block，不能任意删业务资料或备份。
- 证据：es-current-readonly.json、memory-failure.log、memory-failure-stack.log。

### B02：生产API发生Metaspace OOM，PDF预览失败并影响继续验证

- B账号上传596字节自制PDF成功（201、COMMITTED），列表即时新增且自动选中；随后preview返回503/WORKSPACE_UNAVAILABLE。
- 11:53:41该预览请求的服务端栈为`Handler dispatch failed: java.lang.OutOfMemoryError: Metaspace`。11:59其他请求继续出现Metaspace OOM。当前进程参数包含MaxMetaspaceSize=192m。
- 单次12秒只读健康查询没有收到响应（HTTP000）；这是诊断请求超时，不是新增产品deadline，也不表示已证明所有请求都失败。
- **结论**：不是“PDF上传失败”，也不能仅凭时间顺序断言PDF解析器泄漏。直接失败机制已确认，类加载增长、容量设置或泄漏的长期根因尚未证实。
- **处理建议**：先取得现有进程/类加载和容量证据，确定受控恢复方案，再恢复服务与重新验证；不盲目无限提高内存、不重复上传压测、不未经授权重启。
- 证据：pdf-preview-server-error.log、backend-health.txt、b/browser/pdf-recheck.json、preview响应request_id ca2a8e33-d743-4ef0-ae91-fbb1c6703b65。

### B03：语音合成本次失败，转写仍可用

- B账号实际合成一次自制短句：HTTP504，约3.2秒；日志VOICE_PROVIDER_TIMEOUT，request_id eab1c829-c85d-4783-914f-43e8db3cc863。没有拿失败合成输出继续转写。
- 改用昨日自制合法WAV独立验证STT：HTTP200/E0，约6秒，识别文字与样本一致。不是再次调用合成，也不是完整TTS→STT通过。
- **处理建议**：对照该请求查Provider连接/实际超时配置和上游回执；当前证据只能确认provider timeout，不能直接归因余额、模型质量或宣称故障持续必现。
- 证据：b/browser/voice-recheck.json、stt-standalone.json及服务器日志。

## 3. 修复项逐项结果

| ID | 本次核查与结果 | 当前结论/最小下一步 |
|---|---|---|
| O01 存储限制/音频上传 | A通过真实“选择资料”上传合法WAV（268844字节），400/BAD_REQUEST，未新增、未选中。当前源码仍存在allowedMimeTypes、validateMime白名单；用户要求移除的实现尚未生效 | **复现，待修**。按已确认方案取消存储层业务格式白名单，保留安全与完整性；不是仅补audio/wav。恢复服务后验上传→目录→自动选中→预览/读取 |
| O02 知识敏感信息 | A真实检索结果仍显示历史登录凭据样例；本报告不抄录、未验证有效性。不能据此称泄漏到其他账号 | **复现，待修**。核查来源/有效性/可见范围，脱敏及按授权处置历史语料；不能拿旧清库授权直接清理 |
| O03 完整来源引用 | 原UI引入传令打开正式需求草稿，文本仍131字符；固定源码仍slice(0,120)、originRef=juyiting:library、inputs=[]，没有具体记录引用 | **复现，待修**。入口已改正确，但完整引用语义未闭环；明确来源标识/版本及后端权限解析。未保存或发送引用草稿 |
| O04 重交前多余澄清 | 保留496历史证据及当前实现核对；本轮未完成新一轮混合图文交付→仅改图保留文字→重交 | **当前版本动态复验未完成**，不能把旧问题直接说成今日已复现或修好。服务恢复后单独补完整场景，不操作已完成496 |
| O05 已完成历史提示 | 496当前正式成果页仍显示“本次交付范围尚不明确”，同时写“事项已完成，此处仅供查看成果”，PC/390px均留证 | **范围提示复现**；历史提交卡“请验收”子项没有新一轮完整页面证据，保留待验。统一权威终态只读提示，不改历史事实 |
| O06 摘要JSON/重复展示 | A真实结果直接显示summary/keyPoints等JSON；同内容项目记录出现多个不同ID。相同会话的不同时间摘要需与真重复区分 | **展示问题复现**。可读摘要、安全降级；按来源/版本核对去重，不能把所有同会话记录删成一条 |
| O07 录音失败文案 | A在真实议事输入框填测试文字后点录音，报Requested device not found；丢弃可退出，原文保留，随后测试文字清空未发送 | **英文错误复现；降级可退出**。补中文设备/权限/占用映射，真实硬件分支仍待真机 |
| O08 修改成果输入衔接 | A在497明确要求使用上一轮橙图改紫、禁止原蓝图；实际消息仍引用原蓝图，模型返回CLARIFY说明仅能读取蓝图，要求提供橙图；没有错误执行 | **功能缺口得到当前实链证据**，不是仅凭一句模型描述猜测。核对会话输出→固定输入引用/receipt的接线；本轮证明该路径未自动带入橙图，不泛化为所有修改均错图 |

O01 request_id：36ef9bd7-87d8-47bd-8d4f-bb3da48e17b0。O08请求：mmd-typed-request_e4560ad5ec21906d4299c4b048af9fff7524572e，userMessageId1889632，CLARIFY。凭据样例仅留私有证据，不复制到规格或报告。

## 4. 待验证项逐项结果

| ID | 覆盖与未覆盖 | 结论 |
|---|---|---|
| V01 运行中重入/自动解除忙态 | 497空闲时返回详情再进入成功。第一轮因O08澄清没有EXECUTE；随后按明确改变的输入做一次蓝图→紫图恢复测试，获得ACTION_REQUEST，后续权威投影显示WAITING_PROVIDER；观察器窗口内未捕获可用于导航的运行态，随后服务OOM阻断 | **未通过也未判该修复失效**。未形成“运行中重入→终态自动解除”完整证据。已有请求必须继续核对，不能重发 |
| V02 第二账号隔离 | A与授权B分别真实登录。A自有497、会话及原蓝图可读；B访问这些返回TASK_NOT_FOUND（HTTP200业务失败）、FILE_NOT_FOUND/404、BOUNTY_REQUEST_INDEX_NOT_FOUND_OR_FORBIDDEN/404。B新增独有文本可读；A访问其详情/content/preview均404；B访问A的content/preview均404 | **双向资料读隔离、B→A事项/会话拒绝通过（本组样本）**。未覆盖全部角色、写入越权、迟到响应和同浏览器切换身份 |
| V02 知识隔离补充 | 同一关键词A检索8条，B返回E0空列表；ES当前全部40条属于同一旧owner，没有B正样本，且当前写入被B01阻断 | **B未读取到A结果通过；双向正样本验证未完**。不能将B空列表宣称全部知识权限均通过 |
| V03 真机/录音权限/播放 | PC1440×1000、移动模拟390×844；系统没有音频capture设备，未发现adb | 无设备降级已验；**实体手机、真实麦克风/扬声器、系统权限/软键盘未验**。不以模拟替代 |
| V04 日/周/月调度 | 今天02点和11点实际任务日志均已核对；B01导致会话同步失败并阻断后续汇总。周日03点、每月1日04点的源码条件保留 | **日汇总今日失败**。周/月窗口仍未到：2026-10-25 03:00、2026-11-01 04:00，北京时间；未改cron/系统时间、未设自动任务 |
| V05 音频完整流程 | WAV上传400；独立STT通过，TTS本次504；不能进入完整音频资料选用流程 | **不通过/受阻**，先O01及B03后重验；不写“语音全链路已通” |
| V06 其余已有能力/格式 | B文本上传201、自动选中、自动预览与内容GET200；PDF上传201、自动选中但预览503；DOCX/XLSX只准备样本，尚未上传。PPTX、阅读进度/笔记、公议多目标、接应/安装和全部异常分支没有本轮完整验证 | **部分通过，PDF失败，其余未完成**。发现服务异常后停止新增操作，不为了凑覆盖继续打请求；实际付费/安装副作用也未擅自执行 |

“全量”按原清单逐项给出结果和缺口，不代表每项都已完成端到端测试，也不是全站所有功能/所有格式的穷举认证。

## 5. 原请求、测试数据及恢复边界

- 没有操作原事项480或替用户处理现有事项；495/496只读。B现有进行中事项不操作。
- 本轮在本会话自有测试事项497增加**两条**消息：一次橙图修改澄清；一次明确改用原蓝图的独立恢复测试（作为澄清回复）。后者不是自动重试前一个错误输入，也没有循环生图。
- 第二请求：mmd-typed-request_f88b1404d604b9e4df4dbea0e6c103bc5cbaaf87；userMessageId1889687；actionRequestId act_25ace6fc4a6d09ef9c2662369895b9fa94a7150f。
- 最后留存投影11:57：childRequestId 3391a42683615b3495007d7db73d4b0c5ac9d4b248966295cf245bd47f375743；executionId pwe_8c1dd5c5b302e8495a2deb255b3038c131fb8d8ad4705fd8f8bdf9bae517；phase/state WAITING_PROVIDER，未留存成功结果。**它可能随后继续运行，不能当作未执行而再提交；恢复后先查询该原请求。** 本轮未取消/清队列/验收497。
- B新增文件：isolation-b.txt / pws_7aa0583cc1a24803af3f677faa4d1194、reverify.pdf / pws_544726a6d5cd4607b1122d4ccabca0ba，均v1。PDF/文本是真实上传，不把模型结果伪造为测试产物。未保存新事项或给Agent使用B文件；服务异常后保留数据待核，不虚报已回收。
- A WAV上传失败，无成功文件ID。B执行一次TTS、一次独立STT，无充值/购买/退款。新账号密码只放私有临时文件，已删除；不写文档、不输出token。
- 案卷引用返回时自动保存草稿被验证工具写保护拦截，随后明确放弃未保存修改；这是工具保护，不是后端草稿故障。早期从仍覆盖的底层首页切换造成面板层级保护，清洁导航重验正常；**不把这些工具操作问题列为新的“继续议事按钮失效”缺陷**。

## 6. 建议后续顺序（尚未实施）

1. 先受控恢复基础服务：B02 Metaspace诊断/恢复、B01磁盘与ES写能力；不强行解除保护，不任意清业务资料。
2. 先读取497原pending执行、现有文件和知识待同步快照，确认真实状态，再补V01/O04，禁止重提未知请求。
3. 按已确认需求修O01，及O02/O03/O05/O06/O07/O08；涉及交互先更新原型/规格，不在本次核查中直接改产品。O04先用新完整样本确认当前表现，不凭旧版本重复修。
4. 补知识双身份正样本、音频/文档完整链、TTS诊断和必要回归；真机/未来调度仍独立列明条件。
5. 编码后沿现有Flow统一正式验证/版本发布，再验实际页面，不用本轮诊断或旧Flow冒充新版本交付。

## 7. 证据索引

根目录：`/var/tmp/cyf-reverify-20261022/`，权限700/600，包含私有语料，不公开分发原始JSON。

- baseline.json；es-current-readonly.json；memory-failure*.log；pdf-preview-server-error.log；backend-health.txt。
- a/browser/audio-recheck.json、library-searched.json、citation.json、completed-history-pc.json、completed-history-mobile.png、microphone-recheck.json、current-basis-response.json、explicit-source-response.json。
- a/browser/initial-permissions.json、library-searched.json中的crossRead及请求回执；b/browser/initial-permissions.json、isolation-results.json、uploaded-isolation.json。
- b/browser/voice-recheck.json、stt-standalone.json、pdf-recheck.json。
- discussion-write-receipts.json、new-interaction-outcomes.json；a/browser/clarification-no-execute-observations.json与reentry-observations.json。观察器失败仅说明没获得所需时序，不当作业务成功/失败。
- 两个browser目录下readonly-network.json、response-*.json记录真实读请求、一次许可写入和HTTP/业务结果。401/403/404、HTTP200中的失败code不混计为成功。

收尾：两个自有浏览器均已关闭，临时登录文件和浏览器profile已清理；B的profile删除发生一次ENOTEMPTY，确认自有Chromium已退出后仅清理该精确目录与遗留runner，未操作应用进程或用户原型浏览器。


## 8. 2026-10-22 16:34—16:57续验（PDF按用户要求暂停）

- 用户明确“PDF先不验”；PDF保留上午失败事实，当前版本复验暂停，不计通过。本段仅只读检查及页面导航，没有发送生成/提交/验收请求，没有清盘、重启、改配置或发布。
- 线上基线已变：Web1.16.42，Flow4403172/291，commit `ddda0d34647074b973d6b95e869c8fb6ad4434b1`；API1.16.28，Flow5260799/228，commit `1d05101d267bc0e0cf50678fb6d80cb967136d34`、tree `ca05f21f1d6f7cbf42f3ae0b85182045c739f376`，安装JAR记录SHA `0bb2752967dcd7d03a15f5649ee22975cd3baee906d325c728d6333983de80b0`。记录读取不等于本轮重新构建验收；Runtime进程路径1.2.4。没有宣称该版本由本会话发布。
- B02：本轮健康接口HTTP200，status.code=UP，API进程已更换，仍配置MaxMetaspaceSize=192m。只能确认当前恢复响应，不能据此宣称上午Metaspace问题根因已修复或长期稳定。
- B01仍阻塞：16:37 ES `chat_memory_v2` 的read_only_allow_delete仍为true，节点磁盘97%；16:50主机根盘99%，可用884MB。未强行解锁；知识写入/双账号知识正样本/汇总恢复继续待验。宽目录只读容量盘点耗时较长，已终止本会话自己的du，未删其他任务临时目录、制品、备份或业务数据。
- **497原未知执行已核实入库**：原child `3391a42683615b3495007d7db73d4b0c5ac9d4b248966295cf245bd47f375743` 与execution `pwe_8c1dd5c5b302e8495a2deb255b3038c131fb8d8ad4705fd8f8bdf9bae517`，请求索引和详情均RESULT_COMMITTED；没有重发。PC真实议事页面显示紫色方块成果、“本轮结果已登记”，输入可用，无停止按钮。
- 497移动模拟390×844：议事→返回详情→继续议事后，仍显示本轮结果已登记、三张会话图片加载成功、输入框未禁用、没有停止按钮；document.scrollWidth=390，无整页横向溢出。本次通过的是**终态后重入**；没有观察运行中进入到终态的连续时序，V01精确动态场景仍待验，不扩大结论。
- 新证据：`/var/tmp/cyf-reverify-20261022/continuation/`中的es-current-readonly.json、health.json，以及a/browser/original-request-terminal.json、original-request-detail.json、terminal-chat-pc.png、terminal-reentry-mobile.json/.png。PDF专用第二浏览器未执行预览或新上传，临时凭据文件已删除。

### 17:03 +08:00 补齐已完成历史页面核查
- O05在Web1.16.42/API1.16.28再次复现两个子项：496历史成果页同时出现“本次交付范围尚不明确”和“事项已完成，此处仅供查看成果”；从该页“查看议事记录”进入后，最后提交卡仍显示“成果已提交，请查看并验收。”。
- 已完成议事未显示议事输入框，未执行任何写入或重复验收。这证明终态提示未统一，不据此宣称已完成事项可再次提交或验收。
- 证据：continuation/a/browser/completed-history-mobile.json/.png、completed-chat-stale-copy.json/.png。O05此前未核实的历史提交卡子项现已有当前页面证据；O04新一轮重交动态场景仍未验，不能以496旧对话替代。
- 截至本段，新增验证通过范围为497原执行终态及PC/移动模拟终态后重入；ES写入仍阻塞，PDF按用户要求暂停，其余缺口沿用前表。不新增生成请求、不以非PDF已查页面代表全量验收。
