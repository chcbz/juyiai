# 聚义厅全局回归测试用例

修订：2026-11-10-v1。归属：聚义厅整体体验整合。**本轮仅完善测试定义，不执行回归、不构建、不部署，不触发收费调用或生产业务写入。**

- 权威用例数据：[global-regression-cases.json](global-regression-cases.json)；本文为同修订的人读操作目录，修改用例须同步两者。
- 共 **14类、119项**：保留原核心17项的一对一映射，补充102项。119项的本修订执行状态均为 **NOT_RUN**。
- 旧17项的历史通过只证明原固定候选和原范围；不代表新增102项、当前版本、全部全局P0或全局回归已通过。
- 拍照、相册实际调用按用户要求排除，单列EXCLUDED，不包含在119项，不计PASS。普通文件上传仍须回归。
- 这是业务回归用例，不是单元测试清单，也不是已实现119项自动化脚本；浏览器操作可人工或复用已有UI工具，断言可辅以只读API、日志、数据库事实和文件解析。**直接调API不能替代UI操作通过。**

## 1. 分类与优先级

P0：核心闭环、资金/权限/终态等高风险回归；P1：其余重要功能和边界。优先级不代表已经上线或已有测试资源。CORE17不等于全局全部P0。

| 分类 | 范围 | 用例数 | P0 | 原核心历史映射数 |
| --- | --- | ---: | ---: | ---: |
| ENTRY | [入口、导航与响应式](#cases-entry) | 8 | 1 | 0 |
| TASK | [需求与事项生命周期](#cases-task) | 10 | 4 | 2 |
| ASSIGN | [推荐、承办与外部委派](#cases-assign) | 7 | 3 | 0 |
| TALK | [正式议事、密议与多轮上下文](#cases-talk) | 11 | 6 | 2 |
| MATERIAL | [资料选择、上传、固定版本与工作空间](#cases-material) | 11 | 4 | 0 |
| SKILL | [全部现有技能与产物质量](#cases-skill) | 12 | 10 | 9 |
| DELIVERY | [成果、预览、选版与验收](#cases-delivery) | 9 | 6 | 3 |
| ECON | [WEN钱包、报价与成本](#cases-econ) | 8 | 5 | 0 |
| AGENT | [好汉、技能管理、岗位与托管](#cases-agent) | 9 | 1 | 0 |
| ARCHIVE | [典籍、阅读器、手札与案卷](#cases-archive) | 9 | 1 | 1 |
| HELP | [我的、消息、帮助与反馈](#cases-help) | 5 | 0 | 0 |
| VOICE | [语音输入输出与实时会话](#cases-voice) | 5 | 0 | 0 |
| RELIABILITY | [异常恢复、隔离与系统稳定性](#cases-reliability) | 10 | 7 | 0 |
| COLLAB | [公共议事、团队与扩展协作](#cases-collab) | 5 | 0 | 0 |

## 2. 执行集与通过标准

### CORE17：原核心冒烟

沿原[17项真实UI操作手册](../juyiting-skill-execution/core-ui-regression.md)使用新A/B事项和新普通密议。保留原单次请求、自然修订、真实工具/Provider、终态/费用及文件摘要断言，不通过催促、补发或手工改数据让本轮变绿。

建议自然顺序（括号为原编号）：
1. 启动 `JYT-TASK-03`（01）的新建/确认承办里程碑；首次目录 `JYT-SKILL-01`（02）。
2. A分支：`SKILL-02`（03）→ `DELIVERY-01`（04）→ `TALK-03`（05）→ `SKILL-03`（06）→ `SKILL-04`（07）→ `SKILL-05`（08）→ `TASK-04`（14）。
3. B分支：`SKILL-06`（09）→ `SKILL-07`（10）→ `SKILL-08`（11）→ `SKILL-09`（17，验收前保留字节并核验）→ `DELIVERY-02`（12）→ `DELIVERY-03`（13）。
4. 新普通密议：`ARCHIVE-01`（15）→ **同密议下一轮** `TALK-04`（16）。不能换成正式事项或新会话代替连续性验证。
5. A取消、B完成后，收尾 `TASK-03` 的钱包断言；全局执行再做 `RELIABILITY-10` 收尾。

上述简写均带 `JYT-` 前缀。JSON的depends_on表示所需数据/里程碑，不是强制上游整条复合用例先PASS：TASK-03包含启动与收尾两段，不能等它全部结束才开始技能测试。

### FULL：全局回归

对119项逐项评估实际部署入口、功能开关、合同实现状态和资源前提，形成**完整选项及结果**；按当前启用合同执行适用项，允许复用同轮自然流程的原始证据，但每项断言分别给结论。不得省略高风险项或只跑17项后报告全局通过。

SKILL-01必须记录当轮实际可调用技能清单及版本，映射每个技能的正常成功场景。目录变更时补充具体用例；“技能目录能列出”“模型说自己会”“原生识图成功”不等于所有技能都执行成功。SKILL-10内每种已启用格式单列实际结果，不能一种成功覆盖所有格式。所有复合用例须各子断言满足才能PASS。

### CHANGE_IMPACT：变更影响回归

CORE17加上实际变更责任层、合同及真实消费者涉及的用例，固定具体ID与理由。适合局部变更验证，**不能当作全局全量回归通过**。不要求向所有好汉广播相同请求；公共边界用代表样本及必要多主体隔离组合，技能能力按实际授权逐项覆盖。

### 结果状态

| 状态 | 含义 |
| --- | --- |
| PASS | 在该轮固定部署/输入下，步骤及全部断言有实际证据 |
| FAIL | 实际行为不满足合同，保留原始失败与复现输入 |
| BLOCKED | 适用但缺账号、权限、资金、fixture或环境；不是产品通过 |
| NOT_RUN | 未执行或尚无足够证据 |
| SKIPPED_DISABLED | 实际未启用，有配置证据及原因；不计PASS，不暗中开启 |
| PLANNED_NOT_IMPLEMENTED | 合同/实现尚未落地，列规划缺口，不把目标设计当线上功能 |
| EXCLUDED | 明确排除范围，目前为拍照、相册实际调用 |

全局结论必须同时给119项状态分布、排除项、实际启用范围及未覆盖风险。**当前启用且适用的必测项有FAIL/BLOCKED/NOT_RUN时，不得称全量通过**；未启用/待实现仅能形成明确限定范围的结论。核心历史结果也不能补算本轮PASS。

失败应记录UI现象→请求/执行关联→权威状态→责任层根因→修复→固定新候选复验；权限/状态冲突不应只暴露通用500。修复公共机制后覆盖真实影响范围，不做只针对单用户或单Agent的补丁。相同根因相同输入连续失败两次停止盲重试。重测另存结果，不覆写原FAIL。

## 3. 固定测试前提与资源

各用例F编号是准备要求，**不是已存在fixture或已授权执行的声明**。

| 前提 | 内容和准备方式 |
| --- | --- |
| F0 | 固定Web/API/Runtime/bridge完整commit、tree、版本、实际制品摘要与访问环境；记录授权测试账号及匿名化tenant/client/owner。确认是真实应用而非原型。UI负责业务操作，辅助读取只用合法身份。费用、资源归属和清理范围在执行前明确。 |
| F1 | 文件组：已有[红方蓝圆PNG](../juyiting-skill-execution/fixtures/core-ui-shapes.png)，640×480、18587B、SHA-256 `5261f79df8bec3de932682be9368d2d596d60328bba4398ba8a5a1741f7ba746`。文本/JSON/正常PDF/损坏PDF/加密PDF/DOCX/表格/PPTX及大图等其余样本**待按适用项准备**，记录原字节SHA、版本、合法来源及预期，不能拿同一损坏样本解释所有错误。 |
| F2 | 每轮新A网页文档事项、新B图片事项和固定会话/请求；不重放历史终态。草稿/待承办/进行中/完成/取消等状态用独立专属数据准备。依赖用例完成前保留原成果字节及关联ID。 |
| F3 | 核心固定输入沿旧手册：自控 `https://kit.chaoyoufan.cn/robots.txt`（200、空title、固定URL；历史文本SHA `efe979eaf2e1e3ceb544fd286d283b24e6b05fa58627b0e20522f29d3a029cca`，执行前核对变化）；IANA真实来源；活动方案120文/8人及24、28、48、12、8，修订150文/10人及30、35、60、15、10；图片800×600白底红方蓝圆→绿圆。输入中的“文”是文档业务内容，不是实际钱包扣费报价。 |
| F4 | 自有可读的PUBLISHED/active典籍维护job与READY书籍，新普通密议及专属手札/案卷。执行前记录workId/jobId/标题/实际章节数；固定核心样本按原预期，通用阅读用不同章数/可空引首等真实样本，不硬编码所有书都是120章。 |
| F5 | 专用隔离环境/Runtime/普通测试技能包、岗位、托管实例及实际管理权限；准备资金、快照和可恢复方案。未准备不能执行故障注入、共享写、管理写、重启及破坏性场景，不触碰他人的服务/任务/状态。 |
| F6 | 两个明确授权账号及必要的不同tenant/client隔离环境，资源属于指定测试Owner；不探测他人真实数据，不借另一用户凭据或HOME。跨租户需实际隔离环境，不让Web选择或覆盖业务tenant。 |
| F7 | 真机麦克风、无隐私音频样本、实际启用配置及真实语音Provider证据；未启用不自动打开，不用文字mock替代音频。 |
| F8 | 实际公共议事/团队入口、已落地协作合同、明确成员与权限。规划中的多成员能力列待实现，不把单承办闭环当高级协同通过。 |

**费用与授权：** 本次仅整理定义。后续执行沿实际测试授权和累计预算；原回归活动的100文上限不得通过新批次重置，历史已用8文只是原回执，不作为新一轮扣费证据。新增共享写、资金领取、托管、技能/典籍发布、双账号、故障及语音调用须具备相应隔离资源和授权，缺失记BLOCKED，不以本目录作为生产操作授权。

## 4. 执行模式、证据与收尾

- `REAL_UI`：从真实页面触发，保留页面、网络请求与业务事实。文件checker/解析器是辅助断言，不能替代UI成功；UI拒绝/权限样本可辅以受控只读接口证据，明确区分。
- `ISOLATED_UI_FAULT`：仅专用隔离环境通过真实UI观察可控故障。模拟工具/响应、故障注入、合成事件只证明相应错误处理，**不替代真实Provider正常成功链路**。即使表中前提未重复写F5，带FAULT一律遵守隔离规则。
- 风险标签：READ只读、OWN_WRITE自有资源写、PAID可能计费、SHARED_WRITE共享资源变更、FAULT故障注入、DEVICE真机相关、TWO_ACCOUNT双账号。标签不是授权；未标PAID也须核对实际端到端调用是否收费。
- 可用性：VERIFY_DEPLOYED_ENTRY＝先核实部署入口，不承诺已上线；ISOLATED_AND_AUTHORIZED＝专用隔离资源和实际授权；CONTRACT_OR_IMPLEMENTATION_PENDING＝合同/实现待核实或未落地；FEATURE_FLAG_AND_REAL_DEVICE＝开关与真机；FEATURE_FLAG_AND_CONTRACT＝开关与已落地合同。不能仅因本地文件存在推断线上能力。
- 每个新执行批次绑定本目录修订及JSON SHA、实际部署摘要、工具版本、输入fixture SHA和完整执行范围。日志脱敏，不保存密钥、完整令牌或他人隐私。
- 回归单独计时，不受单次单元测试/构建发布10分钟上限限制；不向应用请求下传该deadline，不人为催促/中断以凑时间。性能先记录实际观测，不新增无依据阈值。
- 收尾核对预占归零或逐笔解释未释放原因，核对实际消费及Provider次数；只关闭本轮自有browser/profile/collector，保留失败、SHA和必要恢复证据，不清生产身份/备份/他人缓存。

### 单项执行记录模板（放当轮既有证据目录，不另建测试平台）

```text
批次 / 用例ID / 目录修订及SHA：
环境 / Web、API、Runtime、bridge版本及完整commit/tree/制品SHA：
测试Owner / 脱敏账号与tenant/client / 开关 / 权限及授权范围：
输入fixture、版本、SHA / 前置状态与依赖里程碑：
实际UI入口与逐步操作 / 预期 / 实际：
状态及理由 / 起止时间 / 证据路径：
关联task/session/request/execution/tool/Provider ID（按实际可得）：
成果文件名、类型、长度、SHA / 权威终态 / 费用前后及累计预算：
失败现象 / 责任层根因 / 修复候选 / 重测记录（不覆盖原失败）：
收尾与残留副作用 / 缺失证据与未覆盖风险：
```

## 5. 全量用例目录

下表“历史”只是旧核心编号引用；**本修订所有项仍NOT_RUN**。用例操作/断言均应逐条执行；JSON保留数组结构及精确依赖，分类规格链接为对应责任合同，不复制另一套权限或状态机规则。

<a id="cases-entry"></a>

### ENTRY · 入口、导航与响应式

责任合同：[juyiting-lightweight-workbench/spec.md](../juyiting-lightweight-workbench/spec.md) · [juyiting-ui-optimization/spec.md](../juyiting-ui-optimization/spec.md) · [juyiting-dual-orientation-experience/spec.md](../juyiting-dual-orientation-experience/spec.md) · [juyiting-live-map-preview/spec.md](../juyiting-live-map-preview/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-ENTRY-01<br>P0 · 登录与未登录入口 | F0：授权账号及未登录浏览器 | 1. 未登录进入聚义厅<br>2. 按实际认证入口登录<br>3. 返回聚义厅<br>4. 退出登录后再次打开受保护入口 | 1. 不展示他人私有数据<br>2. 登录后进入真实业务页而非原型<br>3. 退出后受保护操作不可继续 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-02<br>P1 · 四大工作台入口与返回 | F0；办事/事项/资料/我的均启用 | 1. 依次打开四入口<br>2. 进入一项详情<br>3. 返回来源列表 | 1. 入口和当前页一致<br>2. 保留来源筛选及合理滚动位置<br>3. 没有重复层或误创建事项 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-03<br>P1 · PC与手机布局 | F0；320/390/1440视口 | 1. 依次打开首页/事项/议事/资料<br>2. 在三视口检查 | 1. 关键按钮及输入可操作<br>2. 无遮挡、横向溢出或重复滚动<br>3. 手机软键盘另记真机证据 | READ, DEVICE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-04<br>P1 · 横竖屏和低高度切换 | F0；未发送草稿和已选资料 | 1. 输入草稿<br>2. 打开预览<br>3. 切换横竖屏及低高度<br>4. 返回 | 1. 不丢草稿/引用<br>2. 不重复发送<br>3. 地图与工作台状态不混用<br>4. 弹层可关闭 | DEVICE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-05<br>P1 · 弹层、键盘与焦点 | F0；键盘操作可用 | 1. 打开一级/子级弹层<br>2. Tab遍历<br>3. Esc逐层返回 | 1. 子级优先关闭<br>2. 焦点限制并恢复触发入口<br>3. 纯图标有无障碍名称<br>4. 不误提交 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-06<br>P1 · 深层导航与未保存内容 | F0；详情内有草稿 | 1. 详情进入其他入口<br>2. 触发返回/未保存提示<br>3. 取消离开<br>4. 明确离开 | 1. 不静默丢失草稿<br>2. 按现有深度规则提示返回<br>3. 不残留背景锁或不可关闭面板 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-07<br>P1 · 地图与名册互不污染 | F0；含在线/离线/多名好汉 | 1. 打开地图与名册<br>2. 切换名册状态筛选<br>3. 打开地图预览 | 1. 名册筛选不改地图人物事实<br>2. 只读预览不新建第二业务状态或发执行<br>3. 隐藏人数可达 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ENTRY-08<br>P1 · 加载、空态与失败态 | F0；空数据账号/隔离读取故障 | 1. 进入空列表<br>2. 切为读取失败<br>3. 恢复读取 | 1. 加载/空列表/筛选无结果/失败可区分<br>2. 错误不伪装0项成功<br>3. 不显示示例假数据 | READ, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-task"></a>

### TASK · 需求与事项生命周期

责任合同：[juyiting-unified-experience/spec.md](../juyiting-unified-experience/spec.md) · [juyiting-assignee-recommendation/spec.md](../juyiting-assignee-recommendation/spec.md) · [juyiting-ui-baseline-20261006/optimization/spec.md](../juyiting-ui-baseline-20261006/optimization/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-TASK-01<br>P0 · 文字需求保存与草稿 | F0；无活动事项 | 1. 填写有效需求<br>2. 保存/开始办事<br>3. 查看待承办详情 | 1. 保存需求不等于授权执行<br>2. 正文与标题按合同保留<br>3. 记录事项ID/版本 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-02<br>P1 · 纯资料需求与无效提交 | F0、F1；无正文草稿 | 1. 空内容尝试提交<br>2. 只选固定版本资料<br>3. 保存需求 | 1. 空正文且无资料不误创建<br>2. 纯资料需求可保存<br>3. 标题兜底不截短实际正文 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-03<br>P0 · 新建、确认承办及费用闭环 | F0、F1、F2；两新事项且资金已授权 | 1. 创建A/B事项<br>2. 分别显式确认承办，记录本用例启动里程碑<br>3. 依次完成各分支技能/交付用例<br>4. B验收、A取消后核对钱包，完成本用例收尾断言 | 1. 确认前不执行/不预占<br>2. 按真实报价冻结WEN<br>3. B仅结算一次、A释放预占<br>4. held归零、预算未超 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-01 |
| JYT-TASK-04<br>P0 · 取消后保留历史成果 | F2；A已有截图/JSON/检索JSON/两版PDF且无新在途请求 | 1. UI取消A并确认<br>2. 查看取消态<br>3. 认证读取原成果 | 1. 取消关闭后续执行并释放预占<br>2. 不承诺外部调用立即撤回<br>3. 原文件200且长度/SHA不变 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-14 |
| JYT-TASK-05<br>P1 · 待承办编辑与无变化保存 | F0、F1；待承办事项 | 1. 修改标题/描述/固定资料<br>2. 保存<br>3. 原值不变再次保存 | 1. 真实变化才推进版本并使旧推荐失效<br>2. 无变化不重复推荐/清空手选<br>3. 不会承办已过期需求 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-06<br>P1 · 编辑并发与迟到保存 | F0；同一待承办事项两个自有tab | 1. 两tab读取同版<br>2. A保存<br>3. B保存旧版<br>4. 按页面冲突说明处理 | 1. 拒绝静默覆盖<br>2. 不丢新需求/资料<br>3. 保留可核对原操作与草稿<br>4. 不重复写入 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-07<br>P1 · 事项列表组合筛选和分页 | F0；跨多页不同状态/承办人/关键词样本 | 1. 组合筛选<br>2. 翻页<br>3. 打开详情<br>4. 返回 | 1. 列表、total与计数使用同一条件且分页前筛选<br>2. 按实际承办ID<br>3. 返回保持筛选<br>4. 首页不被列表筛选污染 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-08<br>P1 · 首页最近与待处理投影 | F0；足量自有事项及待处理记录 | 1. 查看首页最近/待处理/归档<br>2. 打开目标<br>3. 完成后返回 | 1. 按现行排序与数量投影真实记录<br>2. 状态更新正确<br>3. 首页摘要不替代完整列表，不多次全量加载 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-09<br>P1 · 完成态只读与重新办理 | F2；已完成事项 | 1. 打开详情/原议事<br>2. 查看成果<br>3. 尝试继续入口<br>4. 明确新建另一需求 | 1. 完成态不继续执行/催验收<br>2. 查看不扣费<br>3. 新需求有独立事项/授权，不复用旧终态执行 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TASK-10<br>P0 · 取消与执行/验收并发 | F0、F2；隔离环境可控执行及资金 | 1. 执行落成果或验收提交时在另一tab取消<br>2. 核对双方最终事实 | 1. 以权威并发结果收敛<br>2. 无完成又全额退款等冲突<br>3. 资金/成果一致<br>4. 不强停共享Runtime | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-assign"></a>

### ASSIGN · 推荐、承办与外部委派

责任合同：[juyiting-assignee-recommendation/spec.md](../juyiting-assignee-recommendation/spec.md) · [juyiting-external-commission-mvp/spec.md](../juyiting-external-commission-mvp/spec.md) · [juyiting-agent-skill-display/spec.md](../juyiting-agent-skill-display/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-ASSIGN-01<br>P0 · 推荐解释与手动选择 | F0；至少两名合法候选 | 1. 保存需求<br>2. 查看真实推荐<br>3. 改选其他候选<br>4. 返回详情 | 1. 推荐是建议而非指派<br>2. 展示可解释的实际候选<br>3. 手选不受推荐失败绑死<br>4. 未确认无执行 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-02<br>P1 · 推荐失败、重读及报价未知 | F0；隔离推荐服务失败/缺价样本 | 1. 保存需求<br>2. 触发推荐失败/报价不可得<br>3. 查看可用操作 | 1. 已保存需求保留<br>2. 未知不显示免费/0<br>3. 手选及确认能力按实际合同区分<br>4. 不默认为有价 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-03<br>P0 · 确认后自动首轮与重复点击 | F0；可承办事项且报价已确认 | 1. 确认承办一次<br>2. 快速重复点击/刷新<br>3. 查看请求及资金事实 | 1. 只有同一承办授权/首轮/预占<br>2. 不要求额外开始按钮<br>3. 响应未知只核对原操作不重发 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-04<br>P1 · 离线或忙碌候选 | F0；已获准模拟离线/忙碌候选 | 1. 选候选<br>2. 查看确认文案<br>3. 确认<br>4. 等待候选就绪 | 1. 按合同可委派时明确等待<br>2. 不伪报已开始<br>3. 候选恢复后原授权仅启动一次，不换身份 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-05<br>P1 · 外部好汉接单开关及资格 | F0、F6；两账号的可测试外部Agent | 1. 服务方开/关接外单<br>2. 委托方刷新候选<br>3. 查看所属用户 | 1. 仅有效同平台范围的公开候选可选<br>2. 私有好汉不泄漏<br>3. 关闭只阻止新外单，已接任务不被取消 | TWO_ACCOUNT, SHARED_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-06<br>P1 · 外单完整委派与验收 | F0、F1、F6；外部委派授权及预算 | 1. 委托方确认外部承办并带固定资料<br>2. 服务方办理<br>3. 委托方选版验收 | 1. 仅授予本事项资料<br>2. 不需服务方额外逐单审批<br>3. 正式交付可验收<br>4. 私聊与其他事项不泄漏 | TWO_ACCOUNT, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ASSIGN-07<br>P0 · 候选变更与旧授权失效 | F0；隔离绑定/资格代际变化 | 1. 打开候选确认<br>2. 在隔离环境变更归属/资格<br>3. 提交旧确认 | 1. 旧确认不能授权给新Owner/实例<br>2. 返回可理解冲突<br>3. 无预占/授权部分成功 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-talk"></a>

### TALK · 正式议事、密议与多轮上下文

责任合同：[juyiting-multimedia-deliberation/spec.md](../juyiting-multimedia-deliberation/spec.md) · [juyiting-conversation-sessions/spec.md](../juyiting-conversation-sessions/spec.md) · [juyiting-codex-fast-context-20260925/spec.md](../juyiting-codex-fast-context-20260925/spec.md) · [juyiting-ui-baseline-20261006/optimization/detailed-design.md](../juyiting-ui-baseline-20261006/optimization/detailed-design.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-TALK-01<br>P0 · 正式议事连续三轮 | F0、F2；自有进行中事项 | 1. 发送首问<br>2. 正常终态后追问<br>3. 再修改一项约束 | 1. 请求/回合/消息绑定清晰<br>2. 每轮解锁且消费前文<br>3. 不重复首问/自动并行排队<br>4. 不广播无关好汉 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-02<br>P1 · 普通密议新建、草稿与历史 | F0；自有好汉私议入口 | 1. 从详情进密议<br>2. 新建话头<br>3. 留草稿并返回<br>4. 打开历史话头 | 1. 普通密议无taskId、不自动创建正式事项<br>2. 目标明确<br>3. 历史与新话头/草稿不串用 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-03<br>P0 · 跨轮读取旧JSON而非信封 | F2；已提交网页JSON | 1. 仅发送一次读取旧JSON请求<br>2. 看三字段<br>3. 对比执行/文件目录 | 1. 值与原文件一致<br>2. 无新EXECUTE/文件<br>3. 合法成果JSON不按接口响应信封误验 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-05 |
| JYT-TALK-04<br>P0 · 密议续轮真实查询技能 | F4；紧接同会话典籍查询 | 1. 在原普通密议发skill_list与两项skill_read只读请求<br>2. 核对回执及UI | 1. 同engine下一轮DELTA连续<br>2. 真实两项skill_read<br>3. 无RECOVERY_REQUIRED/信封错误<br>4. 不以本地SKILL.md或旧回复替代 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-16 |
| JYT-TALK-05<br>P0 · 话头切换与迟到消息 | F0；两个不同话头且有延迟回复 | 1. A发问<br>2. 切B并编辑草稿<br>3. A回复到达<br>4. 返回A | 1. A结果只入A<br>2. 不覆盖B正文/草稿/目标<br>3. 返回可读取完整最终回复 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-06<br>P1 · 历史分页与连续窗口 | F0；超过20条且跨页有附件/成果会话 | 1. 进入历史<br>2. 向前加载<br>3. 返回最新<br>4. 断线后补读 | 1. 以现行20条页级投影及连续游标消费<br>2. 无缺页/重复/乱序<br>3. 不逐条全量补查<br>4. 正文完整 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-07<br>P0 · 资料作用范围与临时引用 | F0、F1、F2；任务资料和仅本条资料各一份 | 1. 在议事选择本任务/仅本条/不带资料<br>2. 发送<br>3. 下一轮再核对 | 1. 仅发送声明范围的固定版本<br>2. 临时移除不删任务持久关联<br>3. 无资料不隐式授权整个文件库 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-08<br>P0 · 输入状态与重复发送 | F0；有草稿、引用及明确目标 | 1. 发送一次<br>2. 处理中连续点击<br>3. 完成再发送下一轮 | 1. 处理中不重复提交<br>2. 成功只清本轮已提交草稿<br>3. 失败/未知保留必要内容<br>4. 下一轮不被上一轮finally锁住 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-09<br>P1 · 停止回复与取消事项分离 | F0、F2；可控长回复 | 1. 发起回复<br>2. 点击停止回复<br>3. 读取原事项/执行状态 | 1. 明确实际停止范围<br>2. 不把UI停止等同退款/撤回外部副作用/取消事项<br>3. 已提交成果保留 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-10<br>P1 · 记录删除与关联资源 | F0；专用可删除测试话头 | 1. 打开话头记录<br>2. 取消删除<br>3. 再确认删除<br>4. 检查关联事项及成果 | 1. 取消不变更<br>2. 删除仅本话头合法范围<br>3. 不级联删除事项/正式成果<br>4. UI按当前能力如实处理 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-TALK-11<br>P1 · 选文保存与起草不发送 | F0；长回复/典籍摘录/案卷各一份 | 1. 选中文字保存片段或引入需求<br>2. 查看草稿及出处<br>3. 取消 | 1. 保留合法来源与明确截取范围<br>2. 不凭截短摘录宣称读全文<br>3. 不自动发送/承办/执行 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-material"></a>

### MATERIAL · 资料选择、上传、固定版本与工作空间

责任合同：[juyiting-creative-delivery-mvp/spec.md](../juyiting-creative-delivery-mvp/spec.md) · [juyiting-ui-baseline-20261006/optimization/spec.md](../juyiting-ui-baseline-20261006/optimization/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-MATERIAL-01<br>P0 · 工作空间上传与列表 | F0、F1；用户自有空测试目录 | 1. 资料页上传固定PNG/JSON/PDF<br>2. 刷新列表<br>3. 查看文件详情 | 1. 显示真实fileId/version/大小/类型<br>2. 文件未预览时列表不读整文件<br>3. 字节/SHA匹配 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-02<br>P1 · 多文件串行上传与中途失败 | F0、F1；隔离使第二项失败 | 1. 批选三文件上传<br>2. 等第二项失败<br>3. 观察第三项及成功项 | 1. 串行处理<br>2. 已成功保留，失败停止后续<br>3. 不重复上传第一项<br>4. 失败可定位 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-03<br>P0 · 上传未知结果核对 | F0、F1；隔离丢失提交响应 | 1. 上传一次<br>2. 使响应丢失<br>3. 使用现有核对入口<br>4. 重新进入目录 | 1. 按原上传意图核对<br>2. 已提交自动选中同fileId/version<br>3. 不盲重传或产生重复版本 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-04<br>P1 · 资料弹层完成与取消 | F0、F1；已有选中资料 | 1. 打开选择器<br>2. 改选资料<br>3. 取消<br>4. 再打开并完成 | 1. 取消保留原选择且不提交关联<br>2. 完成才带入<br>3. 窄屏预览/关闭/焦点恢复正常<br>4. 不自动发送 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-05<br>P0 · 固定版本而非最新文件 | F0、F1；同文件两个不同内容版本 | 1. 选择版本1绑定事项<br>2. 文件库新增版本2<br>3. 原事项执行读取 | 1. 原授权仍读版本1且摘要匹配<br>2. 不会静默读最新版本<br>3. 新选择需明确绑定新版本 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-06<br>P1 · 重命名与解除事项关联 | F0、F1；固定版本已绑定专用事项 | 1. 重命名文件<br>2. 从事项解除关系<br>3. 读取原历史成果/库文件 | 1. 名称与内容身份分离<br>2. 解除关系不误删库文件/正式成果<br>3. 原已提交来源仍按权限可核对 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-07<br>P0 · 跨用户文件越权 | F0、F6；各有私有同名文件 | 1. A选择文件<br>2. B通过真实页面尝试访问A私有固定资源<br>3. 查看拒绝 | 1. 页面及下载均无内容泄漏<br>2. 不能凭猜ID/URL取得权限<br>3. 相同文件名不串身份 | TWO_ACCOUNT<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-08<br>P1 · 存储与预览能力分离 | F0、F1；PPTX和不支持在线预览格式 | 1. 上传/选择文件<br>2. 打开预览<br>3. 到资料页下载 | 1. 不支持在线预览如实说明<br>2. PPT/PPTX不恢复逐页渲染<br>3. 仍可存储、授权下载并校验原字节 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-09<br>P1 · 取消系统文件选择 | F0；已有草稿与暂存 | 1. 打开普通上传选择<br>2. 取消系统选择<br>3. 返回弹层 | 1. 已有暂存/选择/草稿不变<br>2. 不报伪上传失败<br>3. 不产生文件或执行 | DEVICE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-10<br>P1 · 预览切换与资源释放 | F0、F1；两张图和两版文档 | 1. 连续切换文件<br>2. 关闭预览<br>3. 换身份或退出页面 | 1. 不显示上一文件迟到内容<br>2. 撤销临时URL/取消旧渲染<br>3. 不残留大文件或旧用户授权 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-MATERIAL-11<br>P1 · 从文件与案卷起草事项 | F0、F1；可读文件/案卷 | 1. 从文件详情或案卷选起草<br>2. 查看新需求<br>3. 返回 | 1. 固定fileId/version与出处保留<br>2. 不携私人sourceRef或他人targetAgentId<br>3. 不自动提交/承办 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-skill"></a>

### SKILL · 全部现有技能与产物质量

责任合同：[juyiting-skill-execution/spec.md](../juyiting-skill-execution/spec.md) · [juyiting-skill-execution/responsibility-boundaries.md](../juyiting-skill-execution/responsibility-boundaries.md) · [juyiting-skill-execution/core-ui-regression.md](../juyiting-skill-execution/core-ui-regression.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-SKILL-01<br>P0 · 首次技能目录一致性 | F0、F2；进行中事项首次进议事 | 1. 首次展开目录<br>2. 不点刷新<br>3. 对比同次权威目录及执行绑定<br>4. 记录当轮全部实际可调用技能的名称、版本及授权范围，逐项关联成功场景；缺项单列未覆盖，不沿用历史目录宣称全部技能通过 | 1. 自动显示真实可调用项<br>2. 不出现假0项/须手动刷新才恢复<br>3. 安装不等于本任务授权 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-02 |
| JYT-SKILL-02<br>P0 · 网页操作：截图和JSON | F2、F3；可用browser-workbench | 1. 只读打开自控robots.txt<br>2. 交付截图及title/url/httpStatus JSON<br>3. 核对真实工具 | 1. selected action与技能绑定正确<br>2. 真实浏览器非curl截图<br>3. 200/空标题/固定URL准确<br>4. RESULT_COMMITTED | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-03 |
| JYT-SKILL-03<br>P0 · 信息检索真实取源 | F2、F3；可用web-research | 1. 实际读取IANA来源<br>2. 交付结论、两段短引文及sourceUrl的JSON | 1. 真实本轮取源且回执可追踪<br>2. 引文/日期与原文一致<br>3. 不得凭模型记忆或解释判成功 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-06 |
| JYT-SKILL-04<br>P0 · 中文PDF制作 | F2、F3；document-workbench就绪 | 1. 只执行一次生成120文8人活动方案PDF<br>2. UI预览<br>3. 下载提取文本 | 1. 一页中文可读<br>2. 24/28/48/12/8合计120<br>3. 预览非无限loading<br>4. 文件名/类型/字节真实 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-07 |
| JYT-SKILL-05<br>P0 · PDF多轮修订 | F2、F3；原PDF已提交 | 1. 只发一次修订150文10人及30/35/60/15/10要求<br>2. 预览新版<br>3. 读取旧版 | 1. 实际读取旧PDF<br>2. 自动续轮<br>3. 新版一页且数字改齐/其他内容保留<br>4. 旧版SHA不变<br>5. REPLACE对话关系不冒充文件级替换 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-08 |
| JYT-SKILL-06<br>P0 · 图片识别提交文字 | F2、F3；固定红方蓝圆PNG且识别能力就绪 | 1. 仅要求识别并提交一句文字<br>2. 核对模型实际载体和提交成果 | 1. 输入摘要匹配<br>2. 红色正方形/蓝色圆形正确<br>3. 不生图<br>4. 文字正式待验收<br>5. 原生阅读不伪称独立执行技能 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-09 |
| JYT-SKILL-07<br>P0 · 修订子轮自动生图 | F2、F3；原识别文字已提交 | 1. 仅一次要求保留文字并追加800×600白底红方蓝圆<br>2. 等正常修订及执行 | 1. REVISION_REQUEST→delivery-revision→ACTION_REQUEST→真实生成<br>2. 无需催促<br>3. 尺寸/背景明确入参<br>4. 文字保留<br>5. 唯一Provider调用需回执 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-10 |
| JYT-SKILL-08<br>P0 · 图片编辑与原图保留 | F2、F3；刚生成PNG可读 | 1. 仅一次要求蓝圆改绿、保留红方白底/800×600<br>2. 预览下载<br>3. 读取原图 | 1. 来源真实为原生成图<br>2. 绿圆/红方/无文字符合视觉要求<br>3. 原图独立且SHA不变<br>4. 不宣称未编辑区逐像素相同 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-11 |
| JYT-SKILL-09<br>P0 · 严格背景与透明度 | F3；当前生成图及编辑图原字节 | 1. 运行既有背景checker<br>2. 核对前景框/8px排除区<br>3. 验证254负例 | 1. 全图alpha255<br>2. 颜色定义前景框及8px外所有像素RGB255<br>3. 254负例失败<br>4. 不能把固定条带遇图形误判成背景<br>5. 不证明全语义背景 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-17 |
| JYT-SKILL-10<br>P1 · DOCX/表格/PPTX按实际能力交付 | F0、F1；已启用document-workbench所支持格式 | 1. 分别提出明确格式输入/修改/生成请求<br>2. 下载<br>3. 用对应解析器或应用核对 | 1. 每种格式独立记录执行/内容/SHA<br>2. PPTX仅文件交付无在线渲染要求<br>3. 不支持能力明确说明不伪造成功 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-SKILL-11<br>P0 · 合法工具故障与协议错误展示 | F0；隔离环境可控工具失败/错误响应 | 1. 发一次合法请求<br>2. 注入工具失败/不合法响应<br>3. 查看UI和权威状态 | 1. 失败状态、相关标识与可操作范围准确<br>2. 无5xx掩盖业务拒绝<br>3. 不无限处理中、不假成果或自动重放 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-SKILL-12<br>P1 · 新技能通用接入与隔离 | F0、F5；隔离测试包及独立测试主体 | 1. 按真实技能管理入口装普通测试包<br>2. 获得任务授权<br>3. 执行读写固定fixture | 1. 不修改通用层按技能名/好汉名编排<br>2. 不越出授权目录/任务<br>3. 无凭据泄漏<br>4. 只证明该包实际能力 | SHARED_WRITE, PAID<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |

<a id="cases-delivery"></a>

### DELIVERY · 成果、预览、选版与验收

责任合同：[juyiting-unified-experience/spec.md](../juyiting-unified-experience/spec.md) · [juyiting-creative-delivery-mvp/spec.md](../juyiting-creative-delivery-mvp/spec.md) · [juyiting-ui-baseline-20261006/optimization/spec.md](../juyiting-ui-baseline-20261006/optimization/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-DELIVERY-01<br>P0 · JSON和截图预览下载 | F2；网页输出已提交 | 1. 真实点JSON预览<br>2. 点截图预览<br>3. 认证下载同输出 | 1. 内容而非响应信封展示<br>2. 图片实际加载<br>3. 长度/SHA与目录相符<br>4. 议事预览不新增下载按钮 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-04 |
| JYT-DELIVERY-02<br>P0 · 原文字与编辑图两项选版验收 | F2；B原文字、旧蓝图、新绿图各已提交 | 1. 点编辑图验收此版<br>2. 同时选原文字<br>3. 核对两项<br>4. 确认 | 1. 不误选旧图/附加文本<br>2. finalization COMPLETED/review COMMITTED/delivery ACCEPTED/task completed<br>3. 只结算一次 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-12 |
| JYT-DELIVERY-03<br>P0 · 完成后历史成果可读 | F2；B已完成 | 1. 重新认证读取原生成图与编辑图<br>2. 对比验收前SHA<br>3. 看完成态UI | 1. 两版200且长度/SHA一致<br>2. 完成后不再执行/验收<br>3. 无下载权限误收紧 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-13 |
| JYT-DELIVERY-04<br>P1 · 工具栏验收与空选择 | F0、F2；至少两版可验成果 | 1. 从工具栏打开验收<br>2. 保持空选<br>3. 取消<br>4. 再从某消息验收 | 1. 工具栏默认不选<br>2. 消息入口只预选固定版<br>3. 取消不提交<br>4. 空选不能错误结算 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-DELIVERY-05<br>P1 · 历史版、多文件及明确替换关系 | F0、F2；同文件/多成果历史版本 | 1. 选一历史版和其他文件<br>2. 核对清单<br>3. 验收<br>4. 查看交付manifest | 1. 所有source/hash固定且清单一致<br>2. 不默选latest<br>3. 对话REPLACE与文件级replaces不混淆 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-DELIVERY-06<br>P0 · 预览或已查看不等于验收 | F0、F2；待验收成果 | 1. 预览/下载/标已查看/归档<br>2. 查看事项及资金<br>3. 明确验收 | 1. 查看/归档不改变验收事实或结算<br>2. 仅显式验收才完成，不自动替用户验收 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-DELIVERY-07<br>P0 · 验收冲突与重复提交 | F0、F2；两个tab同一交付 | 1. A选版确认<br>2. B以旧版本确认<br>3. 刷新/核对原操作 | 1. 并发冲突明确<br>2. 原操作可查且不重结算/重生成<br>3. 已接受manifest不被旧tab替换 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-DELIVERY-08<br>P1 · 损坏、加密PDF与大图布局 | F0、F1；坏PDF/密码PDF/长页/临界高度文件 | 1. 逐项打开预览<br>2. 输入密码或按错误返回<br>3. 分页/缩放/关闭 | 1. 坏文件明确失败<br>2. 密码不假成功<br>3. 经典滚动条/临界高度不反复重绘<br>4. 移动端contain与页码正确 | READ, DEVICE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-DELIVERY-09<br>P0 · 成果来源未确认与读取失败 | F0；隔离丢失来源映射/读取失败 | 1. 打开成果<br>2. 查看预览及验收入口<br>3. 恢复读取 | 1. 未知来源不猜测关联或冒称可验收<br>2. 保留具体读取错误和重读<br>3. 不复制另一事项成果填充 | READ, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-econ"></a>

### ECON · WEN钱包、报价与成本

责任合同：[agent-economy-marketplace/beta-wen-billing.md](../agent-economy-marketplace/beta-wen-billing.md) · [task-scheduling/spec.md](../task-scheduling/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-ECON-01<br>P0 · WEN金额和无SILVER兼容 | F0；授权测试钱包/明确币种样本 | 1. 打开钱包/报价/资金记录<br>2. 查看API权威字段及页面 | 1. 当前合同统一WEN及amountMinor整数<br>2. 不靠SILVER兼容兜底<br>3. 无误乘汇率或浮点精度损失 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-02<br>P0 · 余额不足原子拒绝 | F0；隔离低余额钱包和可承办事项 | 1. 保存需求<br>2. 确认超过余额的报价<br>3. 核对任务/授权/账本 | 1. 不产生部分预占或执行授权<br>2. 拒绝原因明确<br>3. 草稿/事项可继续处理 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-03<br>P0 · 创建、推荐、承办的扣费时点 | F0；独立钱包记录和新事项 | 1. 只保存需求<br>2. 查看推荐<br>3. 显式确认承办<br>4. 读取钱包 | 1. 保存/推荐不冒充承办预占<br>2. 确认报价与冻结一致<br>3. 不再套旧合成预览价 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-04<br>P0 · 失败及取消释放预占 | F0；隔离确定失败执行与独立取消事项 | 1. 使执行确定失败或取消<br>2. 按现行终态流程收口<br>3. 读取资金 | 1. 应释放部分只释放一次<br>2. 未知不直接退款/重跑<br>3. 外部已发生成本不补扣用户 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-05<br>P0 · 验收幂等及多轮固定报价 | F0；明确报价的一事项多轮修改 | 1. 确认报价<br>2. 多轮议事/修订<br>3. 验收一次<br>4. 重读结算 | 1. 按现行固定报价结算，不按Provider实际成本追补<br>2. 重复验收无重复扣费<br>3. 清晰区分费用与方案内预算 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-06<br>P1 · 人民币用量、迟到回执和未知成本 | F0；隔离usage迟到/重复/缺价样本 | 1. 执行单次有成本操作<br>2. 延迟或重复usage回执<br>3. 核对成本账 | 1. 按原执行/用户/调用前价格版本归属<br>2. 缺价/PENDING_USAGE不是0<br>3. 幂等<br>4. 不将图片成本当全任务成本 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ECON-07<br>P1 · 赠送领取、刷新与重复领取 | F0；隔离活动及未领取专用账号 | 1. 首次进入领取合同入口<br>2. 刷新/重复进入<br>3. 更改活动价格后查询旧领取事实 | 1. 符合活动条件才发<br>2. 同活动幂等一次<br>3. 已领事实不因现价变化重发<br>4. 不凭本用例生产发款 | OWN_WRITE, PAID<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-ECON-08<br>P1 · 报价变更、缺价与过期意图 | F0；隔离价格版本变更场景 | 1. 打开报价<br>2. 修改价格配置/需求<br>3. 提交旧确认<br>4. 读回原操作 | 1. 按合同绑定需求及价格快照<br>2. 不能套无依据TTL<br>3. 缺价不假免费<br>4. 不重复扣款 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-agent"></a>

### AGENT · 好汉、技能管理、岗位与托管

责任合同：[juyiting-agent-model-governance/spec.md](../juyiting-agent-model-governance/spec.md) · [juyiting-agent-skill-display/spec.md](../juyiting-agent-skill-display/spec.md) · [juyiting-skill-execution/management-contract.md](../juyiting-skill-execution/management-contract.md) · [runtime-self-host-onboarding/spec.md](../runtime-self-host-onboarding/spec.md) · [agent-economy-marketplace/beta-wen-billing.md](../agent-economy-marketplace/beta-wen-billing.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-AGENT-01<br>P0 · 名册、默认模型和就绪事实 | F0；两名模型/就绪情况不同的好汉 | 1. 打开详情<br>2. 切好汉<br>3. 刷新<br>4. 查看离线记录 | 1. 真实已上报默认模型、安装、原生就绪分别展示<br>2. 缺值不借上一位<br>3. 不泄漏渠道/凭据<br>4. 默认模型不是某次调用模型 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-AGENT-02<br>P1 · 刷新技能与能力代际 | F0；隔离新注册/旧响应延迟 | 1. 打开目录<br>2. 模拟安装或能力更新<br>3. 刷新<br>4. 旧响应到达 | 1. 消费最新授权代际事实<br>2. 旧结果不覆盖新状态<br>3. 不靠重装/重新enroll恢复正常刷新 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-AGENT-03<br>P1 · 普通技能安装/升级/停用/卸载 | F0、F5；专用普通包及权限/预算 | 1. 通过真实管理入口逐项确认<br>2. 查看完成状态<br>3. 执行可用性检查 | 1. 权限及版本差异明确<br>2. 状态来自安装回执<br>3. 停用/卸载不冒称已安装可执行<br>4. 失败不伪报升级成功 | SHARED_WRITE, PAID<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-AGENT-04<br>P1 · 安装升级失败、未知及保旧版 | F0、F5；隔离传输/安装失败 | 1. 安装或升级一次<br>2. 注入失败/未知<br>3. 核对原操作<br>4. 重读当前版本 | 1. 确定失败按合同保留有效旧版<br>2. UNKNOWN不重复买/装<br>3. 未完成不计已安装<br>4. 不破坏在途合法执行 | SHARED_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-AGENT-05<br>P1 · 岗位技能与普通手动安装边界 | F0、F5、F6；独立岗位授权样本 | 1. 无任命账号尝试岗位技能<br>2. 合法任命<br>3. 核对技能/资源范围<br>4. 解除专用任命 | 1. 任命、技能安装、任务授权各自独立<br>2. 共享目录分类一致<br>3. 不能因换Owner或本地缺定义绕过岗位权限 | TWO_ACCOUNT, SHARED_WRITE<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-AGENT-06<br>P1 · 技能管理密议写操作 | F0、F5；专用未发布技能及明确维护权 | 1. 密议建立草稿<br>2. 修改<br>3. 校验<br>4. 明确发布/下架<br>5. 实际只读查回 | 1. 模型回复不替代平台操作回执<br>2. 无权限则明确拒绝而非500<br>3. 不同阶段不混为发布完成<br>4. 不改公共在用技能 | SHARED_WRITE, PAID<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-AGENT-07<br>P1 · 邀请托管首期与续费 | F0、F5；隔离可租实例及资金 | 1. 查看资格/技能首期价<br>2. 显式邀请<br>3. 就绪<br>4. 到模拟续费时点核对 | 1. 租约、预占、真实通道就绪分别确认<br>2. 幂等一次<br>3. 续费/不足依当前合同，不以进程存在伪报ready | SHARED_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-AGENT-08<br>P1 · 移除、收尾及跨用户重新邀请 | F0、F5、F6；已部署当前移除合同后执行 | 1. 有旧事项时明确移除<br>2. 收妥旧执行/事项<br>3. 完成私有交接<br>4. B尝试新邀请 | 1. 停止续费不等于已交接<br>2. 旧执行未收口不可串用户<br>3. 私有目录/会话/凭据隔离，公共技能保留<br>4. 迟到成本仍属旧执行 | TWO_ACCOUNT, SHARED_WRITE, PAID<br>REAL_UI<br>CONTRACT_OR_IMPLEMENTATION_PENDING | 无 |
| JYT-AGENT-09<br>P1 · 免费重整/自托管重连 | F0、F5；授权专用实例且当前入口已实现 | 1. 读取身份租约<br>2. 执行允许的重整/断线重连<br>3. 核对新就绪及旧事项 | 1. 保留身份/授权/状态且无重复首期收费<br>2. 不重启其他Agent<br>3. 不以复制HOME/换钥/移除锁绕过恢复 | SHARED_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |

<a id="cases-archive"></a>

### ARCHIVE · 典籍、阅读器、手札与案卷

责任合同：[archive-agent-maintenance/spec.md](../archive-agent-maintenance/spec.md) · [archive-pavilion-reader-mvp/spec.md](../archive-pavilion-reader-mvp/spec.md) · [juyiting-lightweight-workbench/spec.md](../juyiting-lightweight-workbench/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-ARCHIVE-01<br>P0 · 普通密议查询典籍维护事实 | F0、F4；自有可读已发布job | 1. 新建普通密议<br>2. 仅archive_read读取固定job<br>3. 核对UI及工具回执 | 1. 真实当轮查询标题/workId/PUBLISHED/active/章节数<br>2. taskId为空<br>3. 无导入/发布/重试<br>4. 不是目录列举能力证明 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | JYT-15 |
| JYT-ARCHIVE-02<br>P1 · 书架、目录与逐章阅读 | F0、F4；两书籍/不同章节数量和可空引首 | 1. 书架选书<br>2. 目录<br>3. 前后章<br>4. 切书 | 1. 按活动READY版/实际章节数读取<br>2. 不硬编码水浒传/120章/必需引首<br>3. 不混读两个版本 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-03<br>P1 · 续读与跨端进度 | F0、F4；同账号两个自有设备 | 1. 阅读到固定锚点<br>2. 退出再进<br>3. 第二设备继续<br>4. 并发保存进度 | 1. 进度按用户/work/edition保存<br>2. 冲突明确不静默覆盖<br>3. 不是其他用户进度 | OWN_WRITE, DEVICE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-04<br>P1 · 书签与私人手札 | F0、F4、F6；专用可清理笔记 | 1. 创建书签/手札<br>2. 编辑删除<br>3. B查看同位置 | 1. 固定选文锚点/版本正确<br>2. 仅A可见私人内容<br>3. 未保存冲突不丢失<br>4. 不误删共享正文 | OWN_WRITE, TWO_ACCOUNT<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-05<br>P1 · 选文提问及起草 | F0、F4；有效与失效锚点 | 1. 选择正文提问/起草<br>2. 核对edition及选文<br>3. 尝试已失效锚点 | 1. 引用来源准确且服务端核验选文<br>2. 不自动执行正式事项<br>3. 失效不猜测另一版文本 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-06<br>P1 · 案卷搜索、全文及引用 | F0、F6；有权/无权案卷和长文本 | 1. 按关键词或语义搜索<br>2. 打开命中<br>3. 引入议事草稿 | 1. 相关性与授权分别验证<br>2. 无ES/向量依赖时真实降级/失败<br>3. 摘录不冒称全文<br>4. 不泄漏他人私有案卷 | READ, TWO_ACCOUNT<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-07<br>P1 · 成果入案卷与重复归档 | F0、F2；专用可归档成果 | 1. 已完成成果收入案卷<br>2. 重复点击<br>3. 搜索重开 | 1. 归档记录关联固定来源且幂等<br>2. 不是再次验收/生成<br>3. 下载内容与已提交版本一致 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-ARCHIVE-08<br>P1 · 典籍草稿、校验及受控发布 | F0、F4、F5；专用合法公版小书/任职授权 | 1. 密议要求整理<br>2. 创建草稿/版本<br>3. 校验<br>4. 显式发布<br>5. 阅读器读回 | 1. 各阶段均有真实回执<br>2. READY版本不可原位改<br>3. 活动版一致<br>4. 无权发布明确拒绝不500 | SHARED_WRITE, PAID<br>REAL_UI<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-ARCHIVE-09<br>P1 · 书籍版本切换及并发维护 | F0、F4、F5；专用两版本内容 | 1. 打开旧版阅读及维护草稿<br>2. 发布新版<br>3. 切书/活动版<br>4. 旧锚点回读 | 1. 活动版本切换一致<br>2. 旧响应不污染新书<br>3. 不偷偷迁移个人锚点<br>4. 并发校验不部分发布 | SHARED_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |

<a id="cases-help"></a>

### HELP · 我的、消息、帮助与反馈

责任合同：[juyiting-lightweight-workbench/spec.md](../juyiting-lightweight-workbench/spec.md) · [juyiting-ui-optimization/spec.md](../juyiting-ui-optimization/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-HELP-01<br>P1 · 我的入口与账号退出 | F0；登录且有私有草稿 | 1. 从我的打开资料/钱包/帮助<br>2. 返回<br>3. 显式退出 | 1. 入口为真实能力<br>2. 退出保留合法路由但撤销私有操作<br>3. 无隐藏账户假页面<br>4. 不丢其他用户状态 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-HELP-02<br>P1 · 消息列表、未读和定位 | F0；自有不同事项通知及多页消息 | 1. 进入消息<br>2. 翻页/标读<br>3. 点事项通知<br>4. 返回 | 1. 未读计数与列表事实一致<br>2. 定位正确事项/会话<br>3. 首页有限投影不限制独立消息页<br>4. 不重复动作 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-HELP-03<br>P1 · 帮助分类、搜索与业务跳转 | F0；帮助内容启用 | 1. 从工作台和我的开帮助<br>2. 搜索同义词<br>3. 打开文章<br>4. 跳真实业务页<br>5. 返回 | 1. 两入口共用真实内容<br>2. 搜索无结果明确<br>3. 跳转不多占详情深度/不自动提交<br>4. 焦点可恢复 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-HELP-04<br>P1 · 新手引导隔离与重看 | F0；新/老引导版本及两个账号 | 1. 首次进入引导<br>2. 稍后/跳过/完成<br>3. 从帮助重开<br>4. 换账号 | 1. 按身份及版本隔离<br>2. 引导本身不创建/发送/承办<br>3. PC与手机定位可见真实入口 | OWN_WRITE, TWO_ACCOUNT<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-HELP-05<br>P1 · 反馈提交与未知结果 | F0、F5；专用反馈收件环境 | 1. 编辑反馈<br>2. 取消<br>3. 再提交一次并丢失响应<br>4. 核对原结果 | 1. 取消不发送<br>2. 未知不自动重发<br>3. 成功提示有回执<br>4. 身份变化清草稿并隔离迟到响应，不污染真实客服 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |

<a id="cases-voice"></a>

### VOICE · 语音输入输出与实时会话

责任合同：[juyiting-voice-conversation/spec.md](../juyiting-voice-conversation/spec.md) · [juyiting-voice-realtime/spec.md](../juyiting-voice-realtime/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-VOICE-01<br>P1 · 录音权限和取消 | F0、F7；实际支持麦克风的授权设备 | 1. 拒绝麦克风<br>2. 再授权开始录音<br>3. 取消 | 1. 拒绝提示明确<br>2. 取消不清文字草稿/引用、不发消息<br>3. 设备轨道释放，不持续录音 | DEVICE<br>REAL_UI<br>FEATURE_FLAG_AND_REAL_DEVICE | 无 |
| JYT-VOICE-02<br>P1 · 转写进入草稿不自动发送 | F0、F7；固定无隐私语音片段 | 1. 录音<br>2. 停止并转写<br>3. 修改转写文字<br>4. 明确发送一次 | 1. 真实语音转写正确，入草稿而非自动发送<br>2. 不重复请求<br>3. 保留原引用/明确目标 | DEVICE, PAID<br>REAL_UI<br>FEATURE_FLAG_AND_REAL_DEVICE | 无 |
| JYT-VOICE-03<br>P1 · 语音输出与播放生命周期 | F0、F7；语音输出已授权启用 | 1. 取得文字回复<br>2. 播放/暂停<br>3. 切话头/身份/退出 | 1. 语音与实际回复一致<br>2. 旧会话音频不串播放<br>3. 释放设备/URL<br>4. 文本可继续使用 | DEVICE, PAID<br>REAL_UI<br>FEATURE_FLAG_AND_REAL_DEVICE | 无 |
| JYT-VOICE-04<br>P1 · 断网、解码及转写失败 | F0、F7；隔离音频传输/Provider故障 | 1. 录制或播放中断网/注入错误<br>2. 恢复<br>3. 用文本继续 | 1. 不把网关健康/文字mock当音频通过<br>2. 错误可区分<br>3. 不自动重发付费语音/议事<br>4. 设备可释放 | DEVICE, FAULT<br>ISOLATED_UI_FAULT<br>FEATURE_FLAG_AND_REAL_DEVICE | 无 |
| JYT-VOICE-05<br>P1 · 实时语音打断与方向切换 | F0、F7；Realtime实际已启用且合同已落地 | 1. 开始实时会话<br>2. 明确打断<br>3. 切方向/退后台<br>4. 结束 | 1. 按真实协议收口当前回合<br>2. 无旧音频/双连接/麦克风泄漏<br>3. 不把打断等同取消正式事项 | DEVICE, PAID<br>REAL_UI<br>CONTRACT_OR_IMPLEMENTATION_PENDING | 无 |

<a id="cases-reliability"></a>

### RELIABILITY · 异常恢复、隔离与系统稳定性

责任合同：[juyiting-execution-recovery/spec.md](../juyiting-execution-recovery/spec.md) · [account-security-foundation/spec.md](../account-security-foundation/spec.md) · [juyiting-skill-execution/responsibility-boundaries.md](../juyiting-skill-execution/responsibility-boundaries.md) · [api-performance-3s-slo/spec.md](../api-performance-3s-slo/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-RELIABILITY-01<br>P0 · 断网重连与漏事件补读 | F0、F2；隔离可控网络 | 1. 发起一次请求<br>2. 断开SSE/WS<br>3. 重连并补读<br>4. 观察终态 | 1. HTTP/DB权威状态补齐<br>2. 无重复执行/消息/扣费<br>3. SSE EOF不直接当业务完成 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-02<br>P0 · 刷新与浏览器重开恢复 | F0、F2；进行中及已完成请求 | 1. 发送一次<br>2. 刷新/重开页面<br>3. 打开原事项/执行 | 1. 只恢复原请求/成果<br>2. 不重新发POST/Provider调用<br>3. 草稿/引用和终态按各自事实恢复 | OWN_WRITE, PAID<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-03<br>P0 · UNKNOWN与RECOVERY_REQUIRED | F0；隔离确定响应丢失及恢复环境缺失 | 1. 发一次请求<br>2. 制造UNKNOWN/恢复前提缺失<br>3. 查看核对入口 | 1. 未知不等于未提交/失败重跑<br>2. 明确原因及可读原事实<br>3. 不换Agent/换钥/清状态制造新执行 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-04<br>P1 · Runtime/工具Owner重启恢复 | F0、F5；专用隔离Runtime及实际执行合同 | 1. 执行后受控重启该实例<br>2. 恢复回执/成果<br>3. 核对Provider次数 | 1. 仅新方案自身合法恢复<br>2. 不恢复退役runner<br>3. 身份/ACK/幂等保留，无重复外部副作用<br>4. 不动生产其他实例 | SHARED_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>ISOLATED_AND_AUTHORIZED | 无 |
| JYT-RELIABILITY-05<br>P0 · 登录过期与换身份迟到响应 | F0、F6；A在途读写、B独立会话 | 1. A请求中退出或令牌过期<br>2. B登录<br>3. A响应到达 | 1. 清理A私有草稿/缓存/文件访问<br>2. 旧响应不覆盖B<br>3. 刷新不绕认证/自动重放A操作 | TWO_ACCOUNT, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-06<br>P0 · 跨事项、Agent和租户隔离 | F0、F6；不同事项/好汉及隔离不同tenant/client样本 | 1. 分别正常访问自有资源<br>2. UI尝试不获准资源<br>3. 收集受控越权证据 | 1. 身份/业务关系由责任层统一校验<br>2. 不跨租户发现/领取/读取<br>3. 拒绝无副作用，不做单用户补丁 | TWO_ACCOUNT, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-07<br>P0 · 业务拒绝与5xx可诊断性 | F0；隔离无权限/状态冲突/不可用依赖 | 1. 通过合法UI触发三类拒绝<br>2. 查看提示/请求关联<br>3. 读取原结果 | 1. 业务拒绝不是通用500<br>2. 保留安全requestId/错误码便于定位<br>3. 不展示栈/密钥<br>4. 失败不伪成功或无限等待 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-08<br>P1 · 多tab事件乱序与重复回执 | F0、F2；隔离乱序/重复提示 | 1. 两个tab查看同任务<br>2. 延迟/重复状态事件<br>3. 刷新 | 1. 按代际/版本/权威快照收敛<br>2. 无状态倒退或重复成果/账本<br>3. 不同请求不按文本误去重 | OWN_WRITE, FAULT<br>ISOLATED_UI_FAULT<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-09<br>P1 · 性能与资源生命周期观测 | F0、F5；固定同类负载、只读采样范围 | 1. 同一真实场景采首字/完成/查询/字节<br>2. 多次开关页面<br>3. 比较基线 | 1. 记录实际延迟/内存/连接及范围<br>2. 不以超时杀业务或快速失败冒充提速<br>3. 无新增无依据资源门槛 | READ<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |
| JYT-RELIABILITY-10<br>P0 · 测试资金与自有进程收尾 | F0；当轮所有测试ID与进程归属已记录 | 1. 结束或取消自有测试事项<br>2. 核对钱包/Provider<br>3. 关闭自有browser/collector并核对 | 1. held归零或逐笔解释<br>2. 累计预算不重置<br>3. 证据留存<br>4. 只清自有profile/进程，不删生产身份/备份/他人缓存 | OWN_WRITE<br>REAL_UI<br>VERIFY_DEPLOYED_ENTRY | 无 |

<a id="cases-collab"></a>

### COLLAB · 公共议事、团队与扩展协作

责任合同：[juyiting-task-collaboration/spec.md](../juyiting-task-collaboration/spec.md) · [juyiting-multimedia-deliberation/spec.md](../juyiting-multimedia-deliberation/spec.md)。

| ID / 优先级 / 场景 | 前提 | 操作 | 预期断言 | 风险 / 模式 / 可用性 | 历史 |
| --- | --- | --- | --- | --- | --- |
| JYT-COLLAB-01<br>P1 · 公共议事参与者与可见范围 | F0、F8；真实已启用公共议事入口 | 1. 选择明确参与者<br>2. 发只读问题<br>3. 查看各自回话和可见范围 | 1. 公共不等于泄露私人会话/文件<br>2. 目标来自显式参与者<br>3. 不自动广播全部好汉或创建正式事项 | OWN_WRITE, PAID<br>REAL_UI<br>FEATURE_FLAG_AND_CONTRACT | 无 |
| JYT-COLLAB-02<br>P1 · 团队推荐与显式确认 | F0、F8；真实团队入口及候选 | 1. 提出适合协作需求<br>2. 查看推荐团队<br>3. 修改成员<br>4. 取消/确认 | 1. 推荐不等于授权<br>2. 角色/成员/任务范围明确<br>3. 未确认无执行，不把单承办流程冒充团队通过 | OWN_WRITE, PAID<br>REAL_UI<br>FEATURE_FLAG_AND_CONTRACT | 无 |
| JYT-COLLAB-03<br>P1 · 多成员工作项与独立成果 | F0、F8；已交付多成员合同才执行 | 1. 显式派发两个工作项<br>2. 两成员分别产出<br>3. 查看聚合状态 | 1. 请求/回合/执行/成果各自绑定<br>2. 局部完成不冒称整任务完成或自动验收<br>3. 不重复派工 | OWN_WRITE, PAID<br>REAL_UI<br>CONTRACT_OR_IMPLEMENTATION_PENDING | 无 |
| JYT-COLLAB-04<br>P1 · 局部失败、退出与其他成员 | F0、F8；隔离两个在途工作项 | 1. 一成员失败/退出<br>2. 另一成员完成<br>3. 核对任务与资源 | 1. 失败不污染无关执行/租约<br>2. 不强停共享Runtime<br>3. 成员终态和事项聚合准确，无权限外转单 | OWN_WRITE, PAID, FAULT<br>ISOLATED_UI_FAULT<br>CONTRACT_OR_IMPLEMENTATION_PENDING | 无 |
| JYT-COLLAB-05<br>P1 · 协调管理及资源权限 | F0、F5、F8；明确协调权限及独立资源 | 1. 合法协调者查看/操作专用成员或计划<br>2. 无权限者尝试<br>3. 实际查回 | 1. 协调工具不越过任职/资源/事项授权<br>2. 无权限明确拒绝<br>3. 原型/M4/M5规划不能填为已实现 | SHARED_WRITE, PAID<br>REAL_UI<br>CONTRACT_OR_IMPLEMENTATION_PENDING | 无 |

## 6. 旧17项映射与历史证据

- [旧核心手册](../juyiting-skill-execution/core-ui-regression.md)、[固定通过基线](../juyiting-skill-execution/core-ui-regression-baseline.json)、[背景checker](../juyiting-skill-execution/tools/check-flat-graphic-background.mjs)保留原字节及SHA，不以新全局目录覆盖。
- 历史R5报告：[report.md](/home/isp/state/juyiting-root-cause-20261109/full-r5/report.md)；[verification-summary.json](/home/isp/state/juyiting-root-cause-20261109/full-r5/verification-summary.json)。历史候选：Web1.16.136 `092962d10134970851159e6ae348597700b55d19`；API1.1.47-SNAPSHOT `cbeab0d8c51fc7fdabfb724a71bde35251dac955`；Runtime1.3.71 / bridge1.1.59 `01914a4f8b1777e0e7496548d240cb46d138efde`。
- R5历史结论为 `PASS_WITH_ORACLE_CORRECTION`：旧JYT-17固定条带碰到前景抗锯齿；保留原252/249非白计数，修正为饱和颜色定义前景框、排除框及8px后严格RGB255/全图alpha255，254负例失败。**不证明全语义背景或未编辑区逐像素不变。**旧R4失败不重标。

| 原ID | 全局ID | 场景 |
| --- | --- | --- |
| JYT-01 | JYT-TASK-03 | 新建、确认承办及费用闭环 |
| JYT-02 | JYT-SKILL-01 | 首次技能目录一致性 |
| JYT-03 | JYT-SKILL-02 | 网页操作：截图和JSON |
| JYT-04 | JYT-DELIVERY-01 | JSON和截图预览下载 |
| JYT-05 | JYT-TALK-03 | 跨轮读取旧JSON而非信封 |
| JYT-06 | JYT-SKILL-03 | 信息检索真实取源 |
| JYT-07 | JYT-SKILL-04 | 中文PDF制作 |
| JYT-08 | JYT-SKILL-05 | PDF多轮修订 |
| JYT-09 | JYT-SKILL-06 | 图片识别提交文字 |
| JYT-10 | JYT-SKILL-07 | 修订子轮自动生图 |
| JYT-11 | JYT-SKILL-08 | 图片编辑与原图保留 |
| JYT-12 | JYT-DELIVERY-02 | 原文字与编辑图两项选版验收 |
| JYT-13 | JYT-DELIVERY-03 | 完成后历史成果可读 |
| JYT-14 | JYT-TASK-04 | 取消后保留历史成果 |
| JYT-15 | JYT-ARCHIVE-01 | 普通密议查询典籍维护事实 |
| JYT-16 | JYT-TALK-04 | 密议续轮真实查询技能 |
| JYT-17 | JYT-SKILL-09 | 严格背景与透明度 |

## 7. 维护要求

新功能或合同变化直接更新责任分类中的具体步骤/断言、fixture和对应JSON；新增ID稳定递增，不复用已退役ID。变更目录修订和执行选集时保留旧执行记录绑定的原目录快照/SHA。目录完整性静态检查只证明定义可读和导航有效，不证明实现、线上可用或回归通过。本轮文件落盘不等于已Git提交、推送或合入。

## 8. 2026-11-14会话收口快照（非新的全量通过基线）

核对保留的`/home/isp/state/cyf-runtime-lease-separation-20261112/task-ui-20261113-224052/full-regression-status.json`：119项中**33 PASS、1 FAIL、85 NOT_RUN**。该文件按各用例记录当时组件版本/证据，不对应一个全部通过的新候选；本次只读汇总，未重跑UI或资金验收。

- 明确失败：`JYT-TALK-01`正式议事连续三轮。原事项678第二轮多行`reviewReason`被写入/历史读取/Web消费者按单行标识规则拒绝，事务回滚，未取得多轮→验收→结算闭环证据。API修复已到`377132f786`，Web修复已到`f64c127`并合入develop，但合入不等于安装或原事项复验通过。
- 单个事项创建→承办→执行→文字/文件选版验收→完成及归档已有分项证据；其中事项674首次只返回文件，补充文字轮后才完成两项验收，不记为“一次执行完整交付”。不能据此把更宽的`JYT-TASK-03`全部断言标通过。
- `JYT-ASSIGN-03`有真实确认发送中刷新、唯一grant/bootstrap/预占证据；它只证明该分支，不虚构重复POST覆盖。单元/组件测试数量不混入119项。
- 后续续做先读原状态文件和[handoff](../../docs/implementation/handoffs/RUNTIME-LEASE-SEPARATION-20261112.md)，核对实际安装源码与原事项资金状态，再完成失败案例及剩余断言；不重复创建/确认/扣款来掩盖原请求失败。

稳定回归原则：自然语言修改理由与身份/ID字段分开校验；一次核对入口、事务、DAO、历史读模型及真实消费者，保留身份、版本、幂等和事务约束。正常LF/CR/TAB不是非法身份；不可全局放宽ID校验。历史失败与中止构建原件保留，删除Codex聊天不删除业务/发布证据。
