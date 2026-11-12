# 事项教程阻塞修复与重录

> **当前状态更正（2026-11-12 15:09）**：用户指出验收前不可下载，并展示既有“成果与验收记录”入口。此前新增预览下载属误改，现已通过原安装器的local_restore在原发布锁内撤回到原Web1.16.134，record/index摘要与原值完全一致。Web源码及原型/测试已撤销这两个功能提交，纠正提交`c5fe05c`（候选1.16.138，未构建/未部署）。Runtime五项能力修复保留。旧下载补录移出delivery为私有撤回证据，正确入口的新18号教程已重录。

Owner：当前会话；日期：2026-11-12。用户授权先打通受阻/不支持能力，再真实移动端模拟录制；原账号及付费授权沿用。非目标：共享盘服务重配、无关公开Demo修改、历史任务重放、全站整改。

## 固定基线
- 根：9d9cfc25d19e3bc7a090f500f4abe20b8423df1a（存在其他任务脏修改，不覆盖）。
- API：6e57eead938c6cb1c5d26736b53a82999ac30ca0，干净。
- Web：8ebf83041c33b1669849d0e81843c39021171019，组件干净；根gitlink变动属于其他任务。
- Runtime：fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63，干净。已迁移到本项目runtime/；不沿旧共享仓路径修改。
- 上述为本地读取，不宣称远端最新或当前生产源码相同。线上版本另从实际安装记录核验。

## 定位及责任边界
- 网页651/653的实际执行final均为ERR_TUNNEL_CONNECTION_FAILED；先核对受管技能授权origin和隔离代理，不能关闭TLS/沙箱/网络隔离（RB-03/05/09）。
- PPTX：native-document-toolchain的依赖闭包wanted及DOCUMENT_MIMES仅含DOCX/XLSX，现有requirements虽有python-pptx，不代表隔离环境已挂载。Office容器适配和readiness应在Runtime工具层扩充（RB-05/09），技能仅补经验说明。
- TXT654：已检查的执行inputs-snapshot为空，需追溯第一次聊天的材料关联/投递，不从模型回复推断附件坏了。API持有授权固定版本，Web负责真实选择；不补贴正文冒充通过。
- 推荐656：API日志12:03:36一次model调用3939ms后503，异常被业务层转换；相邻其他推荐成功。原始根因尚未定位，不先加自动重放或伪造报价。

## 验收
依次定向单测/隔离工具核验、固定候选受控安装与业务验收，最后新事项真实UI录屏：TXT只上传不贴正文；网页真实导航/点击及截图；Excel公式和图表；PPTX六页文本、结构及可打开性。新证据不覆盖旧失败。默认本地构建，单次600秒，包/日志/SHA分开记录；不启付费Flow。

接口规范：api/docs/interface-standard.md（当前文件核验后绑定commit）；RB-1：specs/juyiting-skill-execution/responsibility-boundaries.md。以下初始定位不代表完成，执行进展及未完成项以本文后续分阶段证据为准。

## 2026-11-12 本轮修复进展（尚未业务验收）
- Runtime候选 `fb6fcb5ccf9861c04df810ad5a8acce337e232fd` / tree `febccc8349c21fdc909081593d38aa0fa9d8d07d`，版本1.3.103 / bridge1.1.72；本地develop提交，未push，不宣称远端最新。
- TXT根因补证：首次planning收到taskMaterials UNAVAILABLE且nativeMaterials无carrier，但availableSources有固定资料、availableActions有接受text/plain的EXECUTE_NATIVE。规划说明现明确：没有规划carrier不等于没有可执行资料，按已公布actionId/sourceRefIds请求下一已授权读取回合，不虚构提前读过或要求重复粘贴。
- PPTX补依赖闭包、MIME能力、OOXML部件识别、生成/重开probe与工具说明；隔离真实测试包括DOCX/XLSX/PPTX编辑、重开和原输入不变。技能说明源码为1.0.1候选，未替换生产已安装技能包。
- 网页：卢俊义缺少skillExecutionConfigFile。候选按其真实tenant/owner/client/agent及当前browser安装绑定仅授权IANA、example、kit五个origin；未扩大任意外网，未关闭TLS/沙箱。配置备份/readback随受控安装进行。
- 推荐：新诊断事项661重新显示真实卢俊义推荐及1文报价，未承办/预占；已通过UI申请取消。只能记本轮未复现，不能声称定位原503根因。

### 验证与构建证据
私有根 `/home/isp/state/cyf-tutorial-unblock-20261112`，不提交生产身份/会话/日志。
- attempt01失败：旧prompt/MIME断言及导出目录可组写。attempt02失败：PPTX测试断言扩充但fixture未生成该输出。均归因后修正，不覆盖原回执。
- attempt03固定候选测试149项：141通过、8跳过、0失败，含显式启用真实Office隔离probe；toolchain image准备及artifact closure validation通过。但重复整树核验达到600秒，精确归属watchdog终止该进程，保留deadline-enforcement.json，不把RUNNING旧回执改为成功。生产未切换。
- attempt04作为独立重试：针对完整树核验成本，按精确Git archive重新核对源码，复用同候选已完成测试/工具镜像；同一inode只在本次调用内按dev/ino/size/mtime/ctime一致性复用摘要，保留完整manifest，改用按路径比较，不删检查。191.007秒打包完成，artifact SHA-256 `004796214b9dfe5a558f3e1c59b6a4dda936e6e6fd6f81a6b568e4740c8f5d8b`。
- 额外真实浏览器隔离回归1/1通过、0跳过：真实app-server、网页点击/截图、精确origin放行、未授权origin/重定向拒绝、未信任TLS拒绝、空origin本地浏览器可用且无外网授权。日志 `browser-regression/test.log`；不等同生产网页事项已通过。
- 受控安装复用现有身份/锁/停写/备份/manifest/fixed-app入口，正在执行；安装与channel/业务验收分别记。安装不受600秒构建时限限制。

## 安装与五项真实事项验收（2026-11-12）
- Runtime固定app已受控安装为1.3.103/bridge1.1.72，PID2391354；旧PID2138777。安装664.931秒（安装不在构建600秒范围），状态备份/原配置/程序留在 `/home/isp/baks/cyf-agent-runtime-v1/20261112-tutorial-unblock-runtime13103`。不恢复旧会话覆盖新事实。
- 三Agent fresh connected/registered/ready及presence ACK已核对，`installation/acceptance.json` 为VERIFIED_ACTIVE_CHANNEL；通道核验与下述业务事实分开。
- 新事项662：只上传TXT，不贴正文，真实提取参数、场景、限制、待确认信息，289字符含空白；原文件SHA核对。首次验收finalization返回500，原operation/key/body显式重试一次后成功，任务completed/version4。旧500证据与录像保留，不宣称零失败。
- 新事项663：生成39755字节PPTX及逐页提纲；python-pptx重开六页，日期/14—16点/书屋/16人/免费/报名/建议标记核对。任务completed/version4。未进行桌面Office视觉渲染，不把结构可打开说成完美排版。
- 新事项664：真实访问IANA页面、交付网页截图及中文摘要，原件SHA核对，任务completed/version4。未关闭TLS或沙箱。
- 新事项665：真实打开kit首页、点击“免登录看示例”、交付两张截图；示例目标页自身为离线示例，但本次浏览、点击、截图是实际工具执行，不把目标页模拟内容说成AI执行。任务completed/version4。
- 新事项666：推荐本轮未复现原503；交付XLSX与PNG，重开核对三日利润公式及SUM总计，独立核算营收4500/成本2550/利润1950，PNG数值对应500/650/800。任务completed/version4；未进行桌面Office渲染。
- 五项完成事实及源码/文件校验在 `/home/isp/state/cyf-tutorial-recording-20261112-batch03/delivery/05-过程记录`。移动端432×768浏览器模拟，不是真机；本批五个新完整流程原始录像已关闭保存，剪辑版仅删等待，保留真实顺序及B04失败/重试，不冒充实时速度。

### 剩余问题与非阻塞限制
- 662第一次500被API泛化为FINALIZATION_INTERNAL_ERROR，缺原cause日志；重试通过不等于根因修复。同时已读到13:33:16 task666根锁与persona binding锁序反转的真实InnoDB死锁，不将不同时间的死锁猜成662异常唯一原因。未删除授权/锁、未修改API或直接写DB修状态。此并发稳定性问题仍待定向修复，不作为已解决项。
- 原推荐656的503根因尚未定位；661/666只证明本轮未复现，不声明永久解决。
- 共享盘CIFS原写入阻塞不在本次业务修复范围；不重新挂载、不承诺已同步 `/mnt/Workspace`。本机素材完整保留。

## 误判新增议事预览下载（已撤回，仅保留事故记录）
五项通过后错误地把HallMessageMedia预览无下载判成能力缺失。实际系统已有HallCompletedRecords的“成果与验收记录→已验收成果→下载/保存”，用户明确验收前不能下载。以下build02/build03是误改历史证据，不是现行交付。
- 责任层仅Web：复用既有会话资产授权GET `?download=true`、saveOutputBlob及小程序桥接，不改API协议/权限/原件。下载仅在独立预览弹窗，保留消息行既有预览/验收；失败可显式重试，下载中禁重入，身份/事项/资产变化或卸载取消旧请求/交接。未增加外链或任意URL下载。
- 唯一原型 `web/prototypes/juyiting/prototype.js`、`specs/prototype-spec.md` 更新，432/1280预览均发现一个下载文件按钮，截图在私有web-download证据。产品实现 `HallMessageMedia.vue`；旧无下载断言依新需求更新，保留原MIME预览、错误、焦点、取消测试。
- Web候选1.16.137，commit `9fe1f8fdf960566acd059162f5664ad91412ccff` / tree `a4ac2a8378c97fc2a4f226155252e0206f4dd1b3`。本地develop，未push。
- 诊断初次四项失败均为原“不允许下载”的旧断言，更新后53/53通过；组件lint已修格式后通过（仅Browserslist历史数据库提示）。正式固定源码构建首轮因误填不存在的output-download selector及补lint格式由Owner停止，保留143退出和原因，不算成功；第二轮使用真实mini-program-file-download selector，当前测试190通过/2pending/0失败，构建/安装另记。


### Web固定输入归因重试及安装
- build02：190通过/2pending/0失败，355.147秒BUILT，但安装在线资源核验耗尽600秒预算，实际603.893秒退出。原失败保留；安装器自动恢复后的record/index摘要均与原值完全一致，浏览器原账号可见五项completed，证据`web-download/recovery02.json`。
- 同时发现build02漏带生产VITE API/OAuth/DWZ非秘密配置，导致页面错误请求本站而不能确认身份。配置遗漏是该客户端故障的已知原因，**未证明它就是安装器摘要核验超时的原因**，二者分开记录。
- build03从恢复后实际入口JS `static/index-3qLIprbP.js`提取并固定三项既有非秘密配置，来源及文件SHA记录在`web-download/runtime-config03.json`，未写入公开源码。精确源码仍9fe1f8f/tree a4ac2a8；不伪造CI环境，600秒独立计时。
- build03：190通过/2pending/0失败，271.154秒BUILT；包SHA-256 `741b00152a0460eaa1c713f0efd6f07fec187b9bdb99540116b8705e8f2d3649`。受控安装42.987秒（工具内部41.005秒），38个变化文件、613个总文件，256个在线JS/CSS+入口逐一摘要通过，当前Web1.16.137/ONLINE_VERIFIED。原锁/备份/恢复/全部摘要检查未减免。
- 安装网络校验仅追加URL/异常观测，不改变校验、重试或预算；本次未复现安装超时。build03证据在原任务根web03/，安装回执`web-download/installation-result03.json`。两次自有干净源码checkout均在成功打包后保存记录并清理，未删除共享依赖目标。

### 移动端真实下载补录与六段视频
- 复用已完成663/666，不重新生成/重复验收；真实界面路径：办事→最近事项“查看进展”→查看议事记录→预览→下载文件。浏览器download事件实际取得PPTX、TXT、XLSX、PNG四文件，所有SHA与前次已验收原件一致，零API错误。
- 本批新增5段流程MP4+1段下载MP4，6段均全片解码退出0；前五段仅删等待/定位空档，下载段完整正常速度。保留6份原WebM，移动浏览器模拟432×768，非真机、无配音、没有登录密码画面。
- 当前累计三个批次共19个MP4，含历史失败证据及状态补录；不是19条全部成功的新教程，也不是19个不同成功场景。第三批6条为5个成功事项流程+1下载补录。
- 实际交付`/home/isp/state/cyf-tutorial-recording-20261112-batch03/delivery`；未写入或声称同步`/mnt/Workspace`。下载文件核对`05-过程记录/UI点击下载校验.json`，视频核对同目录两份视频校验JSON。

### 未完成项及下一动作
- API本轮无源码修改/构建/发布。662首轮500原因、原推荐503原因仍未定位；不能因为新事项成功标记修复。
- 死锁的数据库证据确认为task根/身份binding反序。源码另见`AgentRuntimeAuthenticationService.withFence`先持binding/runtime，再执行joined callback；`AgentWebSocketHandler.withSessionMutationFence`的chat回调可能随后持task根，而`admitDiscussionBaseline`按task根→identity。这是需定向验证的责任边界候选，**尚无tx1 Java栈，不把推断说成已闭环根因**。下一步补带任务绑定的同事务锁序回归，再确定最小改动；不得简单移除认证fence或授权锁。
- 当前包位于web02/web03嵌套输出，超出现行清理器只接受直接任务根或固定api/web/runtime子根的登记形状；Runtime原输出也不在登记base内。当前安装回执仍精确引用包原路径，未为登记擅自移动或复制当前包、改写回执、扩大清理范围，最终包登记待受控处理。所有包外日志/manifest/测试已保存。


## 用户纠正后的验收与正式素材
- 正确路径：办事→已完成事项详情→查看成果与验收记录→已验收成果→下载；不在议事预览添加下载，也不因已完成就把所有议事版本当已验收。
- 用户截图对应既有`HallCompletedRecords.vue`，不是缺功能；无需为此改API或增加并行下载入口。原HallMessageMedia预览/原型及无下载断言均恢复。纠正源码定向测试48通过；另用真实juyiting-completed-records/juyiting-completed-text-delivery selector运行40通过，共88通过，0失败。第一次误写hall-completed-records selector有Mocha警告，未算该不存在suite通过，随后已单独补跑真实两项。
- 原受控发布的恢复证据`web-download/withdraw03-result.json`；线上当前为已恢复的1.16.134，不把源码候选1.16.138说成上线。
- 真实未验收事项521只读打开验收窗口，0下载按钮、保留预览/确认验收；没有提交验收、取消或生成。记录`验收前界面检查.json`限定为UI观察，未声称API直连下载权限已审计。
- 正确的新18号视频在原版本入口对已验收663/666下载四件原成果，四SHA匹配、0 API错误、全片解码0。名称`18-验收后从成果记录下载PPTX-Excel及图表.mp4`。撤回的旧18号及旧原片在批次私有`withdrawn-download03/`，不计入有效交付。
- 有效交付仍为第三批6MP4、6原片；三批19MP4包含历史失败与补录，不是19个成功场景。五项Runtime事项流程未受Web误改影响。
