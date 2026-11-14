# 内测事项费用闭环：人民币成本账与文钱包

任务：BETA-WEN-BILLING-20261105；Owner：本聊天。2026-11-05用户逐项确认。
当前上线与验收（2026-11-08）：API `a1aefc9e46553028b54186f6ad78fe4d26efd6a3` / 1.1.42-SNAPSHOT、Web `f694161` / 1.16.126、Runtime `d7e51840` / 1.3.66已受控安装。2026-11-07生产41表切换和115项LEGACY_FREE历史事实保留，本轮不重新迁移。已启用3500文进厅活动、用户确认的人民币单价及12条可信承办路由。真实浏览器事项610：推荐1文→承办预占1文→原生文本成果→验收CAPTURED；事项611：推荐1文→预占1文→取消RELEASED。当次验收结束钱包3499文、预占0（历史验收快照，非当前实时余额）；5笔流水各自借贷平衡。重复进厅不重复赠送；好汉详情实见`gpt-6-luna`。证据见handoff接续56及`/home/isp/state/cyf-local-build/tasks/beta-transport-a1aefc9-20261108/browser/`。

当前报价方案：模型直接估计整事项输入/输出Token，再乘已登记人民币单价、最终向上取整到1文；不引入复杂度系数或具体工作量换算。1.1.42修正推荐客户端连接配置解析；134项定向回归及发布基线全部通过，分层/fresh JAR通过。同源码两次测试构建打包累计293.722秒；首次构建期间主机OOM导致API中断已恢复，原失败证据不重标，详见handoff。生产推荐调用成本分别0.002842/0.002848元；两次原生执行用量及修复前未获回执的推荐attempt仍PENDING_USAGE，不猜0、不自动重放。MEDIA/独立收费工具因单价未确认仍不可报价，不能宣称全模型及工具成本核销完成。

本文件为本次内测费用目标；同范围冲突的旧银两/微银两、预览报价及分账口径不用于新实施。不修改旧冻结bundle及历史证据，不宣称全部经济模块已迁移。

## 事项报价数据源修订（2026-11-14，已实施并部署）

本次用户确认以现有认证Runtime上报并已保存的`executionModel`作为报价模型，不新增模型下发／确认／验证或Runtime改动；每模型显式选择数据库中的事项报价价目，模型／工具价格在线维护，不再按Agent及任务类型登记静态路由。平台报价渠道不冒充Runtime真实采购渠道，实际成本仍按原调用证据核算。原报价及资金／成本快照保持，不因换模或调价重算。

字段、责任层、旧配置删除、历史版本读取、开源配置边界与验收以[事项报价修复详设](task-quote-database-design-20261114.md)为本次唯一详细定义；下文2026-11-08的静态配置／15条路由记录仅保留当时事实，不作为新实施要求。活动、租费、主机和全量配置迁移不在本次修复范围。API `43feb23d914c2316dd6d7aa460e4a8599f4d67e4`（1.1.53-SNAPSHOT）已安装，五表价目迁移与141个旧配置键删除完成；318项后端测试、独立浏览器/资金验收与生产只读报价冒烟的范围见详设§13。本次未执行生产试扣费或付费Provider调用。

## 1. 已确认规则（唯一当前口径）

1. 对外统一使用“文”；不保留银两展示。1人民币元=100文，钱包交易最小单位1文，赠送/报价/预占/扣款/释放均整数文。 技能管理在用记录的币种同样只保留WEN；残留SILVER由一次性受控数据迁移统一，不在读取或请求路径增加SILVER兼容转换。2026-11-08补漏盘点为3条技能变更DTO、1条旧报价DTO，金额均为0；仅修正price.currency，备份与历史冻结证据保留原字节，不改账本、金额或执行权益。
2. 实际成本以人民币元记账，保留6位小数、HALF_UP；BigDecimal中间计算保留必要精度，入账一次舍入。保留原始用量及价格依据，不逐Token写账，不用float/double运算金额。
3. 最终事项报价=ceil(预估人民币费用×100)。仅最终报价取整；例如0.123456元→13文，1.000001元→101文。不能因先将预估数中间取整而误报。不得擅加最低价或风险加价。
4. 登录后首次进入聚义厅触发内测赠送3500文；不按注册时间区分。相同活动每人一次，不同活动独立资格。重复事件/登录/请求不能重复发放。
5. 页面只上报已认证业务事件；活动规则配置编号、触发条件、金额、有效期及启停。同类活动新增/停用不改代码。费用模块核验资格并发放；普通可伪造统计埋点不能直接授权资金。发放失败不阻塞页面且可幂等恢复。调整同一活动金额不使已领取者再次领取。
6. 推荐调用同时由模型直接预估整个事项累计输入Token与输出Token（包括预计多轮上下文和工具结果），后端以候选Runtime已上报模型查询平台明确选择的事项价目，分别乘人民币输入与输出单价，合并已配置收费工具费用后统一向上取整到1文。接受估算误差，不设简单/标准/复杂三档，不再用资料数或成果数乘Token系数，不以精度标定作为本轮闭环前置条件。不增加纯报价模型调用，不让模型决定单价或余额；真实成本仍另记实际usage。
7. 缺少某候选所需模型/收费工具价格时，仅该候选暂无法报价/确认；不猜价格、不记免费，不阻塞其他可报价候选。
8. 确认承办才预占，确认与预占原子完成。推荐或创建事项不冻结；前端余额只作展示，服务端费用模块统一判断。
9. 验收成功扣除固定预占金额；成本回执不齐不阻塞验收扣款和事项完成，后台继续核对。
10. 取消事项释放全部预占；实际成本保留。取消后不派发新的收费执行；取消与验收竞争只能有一个终态，迟到回执不能重新冻结/扣款。已发出的调用不因账务释放被假定已停止或零成本。
11. 单轮失败、成果不满意或结果未知不影响预占；不设单独失败退款。长期不验收一直预占，无超时释放/自动扣款/催验收。
12. 确认后正常追问、修改和重新生成包含在原报价内，不追加收费或预占；全新需求另建事项，不使用模型猜测强行终止正常修改。
13. 价格表更新不改变已有报价。修改需求、资料、承办人或重新推荐才产生新报价；历史与已确认报价不重算。旧预览5分钟自动报价失效不是新规则，不机械沿用。
14. 价格由管理员人工换算成人民币登记，不配置汇率、不自动换汇；价格版本、渠道/模型及依据可追溯。官方价格仅参考，不能冒充实际采购账单。未来财务管理岗位/技能通过模块接口维护价格和核账，不直写余额；该岗位不是本期依赖。
15. 不开放充值、提现或分账。余额不足只提示；补余额走活动或有流水的管理员发放。
16. 单事项持续消耗只后台记录，不加前端提醒或执行中费用门禁。本方案是固定报价准入与结算，不是平台成本硬封顶；取消和超估成本由平台承担，不偷偷恢复补扣/循环预算门禁。
17. 旧资金清空、不做等值转换；清理前备份并固定目标、范围、切换批次及恢复方案。事项/成果/身份/技能权益/真实调用记录不得随资金清空删除。哪些表/关联记录可清须以真实目录盘点为准，不全库truncate。
18. 切换前已经承办的事项明确标识为免费存量：不补预占、后续验收不扣款。尚未承办的旧事项按新规则报价/预占；不能单凭“无资金记录”推断全部新事项免费。切换需停写协调，避免确认承办与分类竞态。

## 费用与好汉交接规则（2026-11-12修订，实现状态另记）

本节为现行合同，不重标历史上线结果。2026-11-12用户决定取代“自行部署复用原用户Runtime、所有部署解绑必须等待远端停止/清理、租约登记依赖入站控制通道”的旧要求。下文历史实现切片不能覆盖本节；实施见[当前handoff](../../docs/implementation/handoffs/RUNTIME-LEASE-SEPARATION-20261112.md)。

### 部署、资产与租约职责
- API持有部署套餐、用户/Agent绑定、租约与资金事实；Runtime只持有本机执行事实。按用户与Agent的绑定计费，不按主机、连接或Runtime主服务数量计费。部署类型不从控制通道/IP/在线状态推断。
- 主动离线、长期离线、永久失联均不暂停租期或自动停止续费；余额充足且未停止续费则按原30天规则续期。没有Runtime回执不影响续费，不新增在线条件。
- 默认每台受管主机一个Runtime主服务；同主机不同用户/Agent的安装授权、私有目录、会话、凭证、执行子进程和持久状态隔离。公共程序/依赖可复用；目录分开不等于已证明安全隔离。单Agent解绑不停止主服务或影响其他Agent。
- 两种部署使用相同的Runtime主动接入API协议；自行部署无固定IP/入站端口/mTLS控制服务前置。平台安装与主进程监督属于部署运维，不是租约协议。
- 自行部署资产属于接入方：解绑不要求本机在线、停止或清理，不删除本地数据，不转交原Runtime给新用户。API仍须处理自己的在途业务/资金，按精确旧关系撤销平台授权；不得伪造任务完成、远端停止或清理证明。
- 新用户自行部署创建新的Agent执行实例与安装授权；目标主机已有Runtime主服务则复用主服务，而非旧用户实例/凭证/会话。平台托管可按平台资产规则复用实例，但必须先完成旧用户私有隔离。
- 存量免费登记以固定可信安装/绑定和明确套餐为输入，同事务写入TRANSITION租约及首次调度；不得以Runtime adopt回执、控制路由或心跳作为登记条件。重试不延长期限，不追扣历史费用。

### 邀请接线合同（2026-11-13最小必要性复审）
- 收费规则、原预占/捕获/退款/续费责任不变，不新增财务流程。控制接入只由[Runtime规范](../runtime-self-host-onboarding/spec.md)及其详设定义，本节不复制协议字段。
- 每主机一份管理凭据，按Agent精确授权；不再每次邀请生成SETUP/CONTROL两份secret。一个Runtime主服务不限制为一个HTTP轮询，复用现有每Agent进程内worker和单项ACK协议，不新增连接世代或批调度。
- 平台托管自动按原配置准备目标，不要求用户取得运维JSON/手工配对。自部署只首次登记主机，同机后续邀请不重复生成凭据或启动主服务。
- 原setupId、实际目标库存、原reserve事务和SERVICE_READY→capture流程保留；不新增target世代/生命周期，不改现有server/local接口值。
- GET及命令结果重查无执行副作用；新观察由原协调器明确发起。精确前安装FAILED_NO_EFFECT→REFUNDED可新邀请，已有/未知安装不得扩大退款边界。
- 关闭关系只撤该Agent旧平台授权；自部署不发cleanup。离线、回执缺失、主机凭据撤销都不自动停止续费。
- 存量TRANSITION登记独立于控制映射，不重建付款/安装历史。路由沿受控配置切换，无隐式fallback/双发，不建设动态路由平台。
- 本次范围的代码锁序、wire消费入口和生产依据核查已收口，禁止一边开发一边选择方案；事实与未实施项见[审查](../runtime-self-host-onboarding/review.md)。当前自动续费开关未启用；既有RETAINED按本文件§7.3不是0文付费，需在原自动续费发现/到期待办与单条入口明确排除该历史来源，避免阻断同用户PAID/TRANSITION；保留原期限、历史及显式PAID续期，不伪造转换或扩大为新调度系统。详见[详设](../runtime-self-host-onboarding/design.md)。其他历史费用/价格正文和既有证据不因本轮控制收缩而修改。

### 费用
- 平台托管500文/30天，自行部署50文/30天，均自动续费、不采用自然月。首次邀请/重新请回首期另计实际目标实例已有技能数×50文，目标已有技能不重装；自行部署不继承前用户资产，后续只收正常租费。108好汉差异化价格目前仅为[配置草案](../juyiting-agent-model-governance/hero-model-assignments.md)，2026-11-13硬编码候选已撤回，现按用户决定实现数据库配置读取及显式初始化SQL；未执行生产迁移，未取代此处已上线租费。
- 续费不得切换部署套餐类型：资金责任层在续费报价事务中核对原租约planId，拒绝跨套餐报价，钱包和租约保持不变；同套餐的新价格版本仍沿用已有报价确认流程。风险是托管租约误用自行部署低价；不新增查询或在Web/Runtime重复校验。定向回归为`HostingRentLedgerServiceRealTransactionTest.renewalCannotSwitchDeploymentPlanEvenWhenOwnerAndLeaseVersionMatch`，本轮验证状态见handoff。
- 首次邀请确认时预占，部署成功且服务可用后扣款起算30天，明确失败/取消释放。平台托管重新请回可复用已完成隔离的原实例；自行部署使用新用户的新实例及授权。首期按实际目标实例已有技能清单收费，不沿用旧用户本地清单，原剩余租期不结转。
- 首期已有技能数量按确认报价对应的已安装清单计算：每种技能计一次，停用但未卸载仍计入；已卸载技能、历史版本和系统基础工具不计入。清单与金额随报价固定，清单变化需重新报价并由用户确认，不得确认后临时加钱。
- 首费报价边界：Runtime在事务外读取原生技能发现和当前管理安装记录；API核实调用方、同一Agent和主机，冻结清单摘要/公开安装引用，费用模块只按已确认数量计算，不执行Runtime I/O。清单未知、原生发现错误或孤儿本地目录不能按0种报价；不会为报价创建实例或发起模型对话。
- 报价对外同时给出总额`amountWen`、正常租费`recurringAmountWen`、已有技能数`initialSkillCount`与首次技能费`initialSkillAmountWen`。确认前重读清单，主机或摘要变化返回`HOSTING_RENT_QUOTE_STALE`且不预占；成功确认重放使用原资金事实，不依赖新清单可用。首次总额用于预占/扣款/退款，租约仅保存正常租费用于后续续租。
- 公开清单只包含技能键、来源、版本摘要、启停状态及管理安装的公开产品/安装/包摘要；不包含本地路径、会话正文或凭证。保留安装引用不等于已授权新关系，后续新关系权益必须在技能授权责任层落地，不改写原安装成功事实。
- 新关系的保留技能授权复用已有事实：当前有效绑定对应的首期租金已实际扣款，且其冻结清单含精确安装/版本/包摘要。仅报价或预占不授予新关系权益；普通续租/免费重整不丢失原首期来源。技能授权责任层统一解析该来源，安装事实和原购买记录仍不可变，不另复制订单、安装回执或派生授权台账；当前启停/准入政策继续生效，原生技能不伪造商城安装ID。读取每个Agent的目录/推荐批次至多加载一次该清单，无网络或后台重建；解除绑定后不再授权新关系。此项正在实现，源码候选与实测见原handoff，不能视为已上线。
- 技能新安装50文、升级20文，确认预占、成功扣款、明确失败/取消释放；卸载后重装按新安装，原操作重试/恢复不重复收费。
- 存量两种部署均从实际切换时给予30天过渡期，不追扣历史或已有技能费用，期满只收正常租费。登记使用明确的非金融TRANSITION来源，不造支付/预占/服务就绪回执；没有钱包时仅创建零余额账户，重复登记不改原余额或期限、不触发赠送活动。套餐和到期调度沿用正常租费能力。2026-11-11 API78b1cb1c9b定向65项及layering通过；显式迁移、运维批次和生产切换仍待完成。
- 存量租约与重新邀请使用身份注册表中的精确canonical Agent ID，不按新ID生成器前缀推断合法性；仍按tenant/client/owner授权，别名不能替代canonical。平台托管重新邀请仅在原关系交接已完成、原实例已解除绑定后创建新的关系身份，保留原canonical及历史记录；自行部署不复用旧实例canonical，新建主体使用opaque生成器，任意未注册legacy文本不能创建身份。保留原实例目录不等于复用旧安装授权：Runtime为新关系生成新的installation身份，旧授权不能恢复。2026-11-11候选API68fb800824的入口/身份/真实MySQL定向57项通过；不代表存量静态实例的30天过渡登记或生产迁移已完成。
- 到期按可用余额自动扣费；不足锁定。余额足够恢复时从成功扣款解锁起算30天，锁定期间不收费。按到期时间及固定同时间顺序处理，不足不阻塞其他Agent。
- 连续欠费满15天（含等于）进入最终解除，即使此时余额足够也不自动扣费。主动移除同样停止续费，当期不退款。

### 资格与闭环位置
- 自行部署最终解除由API在精确原安装/绑定事务中完成：平台事项按既有结算规则收尾，已预占技能资金仍需真实结算；随后撤销旧安装与专用凭证、关闭租约、暂停原绑定/身份并清除活动归属。任何一步失败同事务回滚，历史完成重放不作用于其他安装。
- 本机技能启停同步、无资金的失败重试、离线状态、停止/清理回执不是自行部署解绑条件；原本机目录和未知执行历史保留，不编造成功/停止/退款。未结算资金与新工作准入在API责任层处理，不用远程删除资产代替结算。
- 关闭的自行部署实例保留历史但排除公共可复用实例发现；筛选在排序/LIMIT之前执行。新用户使用新canonical Agent、installation及独立私有上下文；主机主服务可复用。
- 正常→欠费可恢复收尾（LOCKED）→最终解除收尾（FINISHING）→交接完成可邀请。一个好汉同时只有一位有效邀请者；收尾中没有新邀请资格，实例仍保留原事务执行身份。
- 到期欠费即禁止新承办、密议新请求及全部新技能变更；已有事项及已受理技能操作继续，不能破坏收尾环境。
- 收尾不删除实例，在15天内保留完成旧事务必需的身份/凭证与原事项授权，原用户仍可在原事项入口继续议事、修改、执行、验收或取消。满15天按已交付自动验收扣款、未完成/失败自动取消释放预占的规则最终收尾。
- **平台托管的交接闭环放在实例再次邀请前**：旧事项全部完成/取消，已受理技能操作结束；已取消事项仍有在途执行时须收妥执行退出/成果落地状态，不能仅因业务取消就假定旧进程停止。
- 平台托管随后退出旧会话上下文、撤下旧用户私有凭证/目录/缓存的运行访问，确认私有内容隔离后才开放该实例的新邀请及首期报价预占。保留公共技能、公共配置、公共凭证；公共密钥不因邀请而公开给用户。
- 收尾未完成时任何用户（包括原用户）都不能重新邀请。主动移除仍等待旧事项自行验收/取消；欠费收尾按满15天自动终结规则处理，不能用主动移除绕过已开始的欠费期限。同一旧实例不能为了快速复用兼容跨用户并行；独立Agent可在同一Runtime主服务隔离运行。
- 公共技能升级/卸载与旧用户事项不并行，故不为本次交接新增长期多版本运行适配；已有执行快照/摘要完整性仍保留。
- 原调用成本迟到回执仍按原用户、事项及执行归属处理，不转账给新邀请者；待核价本身不作为实例收尾永久阻塞条件，交接必须保留可信原执行归属及安全回执补投能力。

### 主动移除接口（2026-11-10候选，未上线）
- `DELETE /agent/personas/{personaCode}/bind` 使用统一请求信封，`data` 必须包含用户确认时固定的 `agentId` 和 `leaseId`；不再允许无租约标识的破坏性解绑。Web须在确认弹窗前取得租约快照，确认后提交同一快照，不重新获取另一份租约替换用户确认对象。
- API使用认证主体核对付款人、私有归属、persona及当前绑定，再在同一事务停止该租约续费并登记收尾；不依赖当前套餐价格或Provider在线，不调用旧解绑的停用身份/清空Runtime绑定逻辑。
- 成功响应的`data`为`{agentId, leaseId, status: "FINISHING"}`，只证明停止续费并进入收尾，不证明私有交接完成。重复请求在关系仍处于收尾时返回同一结果，不重复扣款/退款；错付款人、旧租约绑定不匹配或错误persona不能改变新关系。
- HTTP消费者切换、目录关系投影和实际收尾处理尚未完成，不单独发布此契约候选。固定源码和回归证据见统一调度handoff。

### 私有数据与知识
所有会话为用户私有，数据库长期保留；同一实例先后被不同用户邀请不转移旧会话/私有文件/凭证访问权。按最新确认，最终收尾在旧执行真实退出后尝试提取可共享经验，再删除本地私有会话及其缓存/索引、私有凭证与数据；共享知识只能包含通用经验，不能包含或还原用户私有内容。提取失败不得阻塞私有清理，不新增用户提取费用；无法确认安全的内容不进入共享知识。不能直接删除整个CODEX_HOME而连带删除公共技能、配置或凭证。该交接尚未实现，不能把本节契约当作线上隔离完成。

### 实现责任与验收
API持有资格/原事项授权与交接状态，economy负责资金，Runtime负责实际上下文与本机私有访问隔离。统一调度仅唤醒，见[调度规格](../task-scheduling/spec.md)，不决定金额或交接授权。
必要验收：有旧事项时移除但不可重新邀请；验收/取消后收尾及交接可恢复；旧执行未退出不能跨用户交接；新用户无法读取旧会话/目录/凭证；公共技能保留且首期价正确；旧费用回执保持原归属；并发邀请/续费/移除不重复扣款或同时取得关系。当前租费/钱包/统一调度切片已通过独占MySQL15项，原资金回归43项仍通过；关系移除、首期技能报价、私有Runtime交接及完整发布验收仍待完成。固定候选与证据见统一调度handoff。

## 2. 固定源码与已核实差异

精确commit/tree、远端查询时间、接口规范摘要见`../../docs/implementation/evidence/beta-wen-billing-20261105/source-audit.json`。本轮使用git show/grep读取固定远端commit，无checkout/reset/fetch，主工作区脏改不动。

| 组件 | 2026-11-05查询远端develop | 证据边界 |
|---|---|---|
| API | 45440c6e71cf9b6e447e42114e866554f666d2ec | 不是本地主区旧HEAD，也不是已证明当前线上JAR |
| Web | b3de23bf40e7b8fdc7976a6a68aa706bcce5b33f | 固定源码；未重新做线上浏览器核验 |
| Runtime | b2d5f5700118dd148017a3db132e13d7e66bc020 | 安装记录也指向该源码/Run151/1.3.57；非新进程/全业务验收 |

### 可复用与必须改变

| 已核实入口（各自仓库相对路径） | 结论与最小改造 |
|---|---|
| API `economy/jia-economy-service/src/main/java/cn/jia/economy/api/EconomyWalletService.java` | 有钱包、账本、活动编号幂等发放。复用底层；amountMicro/SILVER须切换。活动金额已进入旧requestHash，需明确已领取后改配置仍返回原领取事实，不能把金额变化当第二次发放 |
| API `economy/jia-economy-core/src/main/java/cn/jia/economy/common/Money.java` | 绑定SILVER/MicroSilver，不是纯UI改名；同步API字段、存储语义、配置与消费者 |
| Web `src/composables/juyiting/useHostingRent.js`、`HostingRentPanel.vue` | 当前赠送调用在托管租金流程；本次搜索未发现首次进厅通用触发，不能说登录赠送已完成 |
| API `agent/.../service/funding/FundedBountyServiceImpl.java` | 旧资金事项在创建时reserve；复用账务reserve，不原样套旧业务入口 |
| API `agent/.../service/funding/FundedBountyQuoteCalculator.java`、`FundedBountyPreviewPriceBook.java` | 固定Token、单价、3%费用/收益等为SYNTHETIC_PREVIEW_FIXTURE_NOT_PROVIDER_PRICING，且旧QUOTE_TTL为300000ms；不是实际价格或有证据的估算基线，不能导入生产报价 |
| API `agent/.../service/funding/FundedBountySettlementServiceImpl.java` | 旧入口读取actualComputeMicro并处理旧结算；新固定报价不接受客户端实际成本作为扣款依据，复用事务/幂等但调整业务语义 |
| API `agent/.../service/impl/AgentTaskExecutionGrantServiceImpl.java#assignAndGrant` | 已有按owner取得事项根锁的事务入口，优先在此真实承办链整合预占，不在Controller和每层复制余额逻辑；其他指派旁路仍需有界核对 |
| API `chat/.../service/recommendation/AssigneeRecommendationModel.java#judge` | 取得ChatResponse后只返回输出text；未保留metadata usage。应在模型适配边界收集，不让事项模块解析供应商字段 |
| Runtime `conf/codex-bridge/app-server-adapter.mjs#_frame` | 有delta/final/terminal，未见专门token用量适配，其他事件通用emit。定向生产源码关键词搜索未命中用量处理，不等于Provider不返回或历史日志绝无用量 |

`...`表示该模块`src/main/java/cn/jia/agent`或`cn/jia/chat`前缀；不是新增文件名。检索阴性结果只代表此范围，不能宣称全库不存在费用能力。

## 3. 模型、渠道与样本的证据边界

- 固定API `starter/src/main/resources/application-prod.properties`配置推荐`gpt-6-luna`；支持运行时属性覆盖，因此尚不是当前请求实际模型证明。
- 只读systemd指定配置所指向的三名Agent codex-home/config.toml：吴用、林冲、卢俊义均配置`gpt-5.6-luna`、provider别名`gpt`。仅输出允许的model/model_provider字段，未复制密钥/原配置。配置别名不证明最终Provider model、账户计价或官方身份映射。
- 本轮官网抓取未取得可引用数值证据，直接抓取返回HTTP403；不从记忆编造或换用相近模型价格。`price-reference-status.json`明确未导入价格。用户已指定最终由人工登记人民币价格，系统不引入汇率。
- 不将旧preview固定18000/4000/6000/3000 Token当历史样本。当前尚未完成按精确请求/turn绑定的历史真实usage采样、累计/增量语义、收费工具和实际渠道核对。不能据此拟造有效预估参数。
- 后续只选已授权诊断任务的usage/model/requestId等最小元数据，不全量读取用户正文/附件/凭据。优先复用历史回执，不新发收费调用；采不到的链路标待核对而非0。

### 后续确认：统一模型及价格候选（2026-11-05）

- 用户确认内测推荐与承办执行统一使用 `gpt-6-luna`，不再为新配置保留 `gpt-5.6-luna`。上文旧模型是初查事实，不修改历史用量的实际模型或追溯套用新价格。
- 用户提供标准模式美元价表；沿用对话本次换算系数6.6879人民币元/美元（一次性换算依据，不是系统汇率配置）。尚未独立核验官方价格及实际渠道收费语义。
- `gpt-6-luna` 人民币单价（元/百万tokens）：普通输入0.668790、输出3.343950、缓存读取0.066879、缓存写入30分钟0.835988、缓存写入12小时1.671975。2026-11-07用户明确确认此前价表即当前接入渠道实际收费标准；登记依据为“用户确认的渠道价格”，不是独立官网核验或账单核销。单价已确认但尚未写入生产配置；2026-11-07用户进一步决定“那就先统一单价”，当前所有上下文长度统一采用该模型价表，shortContextMaxInputTokens不配置、longContextYuanPerMillionTokens为空。不增加长度溢价，也不把输入/输出/缓存各类别合并为同一单价；以后调整仅生成新价格版本，不改历史报价和调用前快照。不得将百万tokens单价误存为单token单价；各类别包含关系依渠道合同归一化，不能机械叠加。
- 本轮只更新方案；候选未导入生效，实际运行配置未切换，未重启或发起收费调用。实施时核对推荐有效配置及三名承办Agent配置来源，按配置变更备份、readback和生效核验收口，不将本段视为已完成切换。

### 本期附带需求：好汉详情展示模型（2026-11-05）

用户要求随本期内测费用改造交付，不单独扩大为模型管理功能。

- 在既有“好汉详情”身份信息下展示“使用模型”及完整模型标识；目标统一为`gpt-6-luna`，但不在Web写死该值或用目标配置填补未知事实。
- 数据来自该Agent最近已上报的有效模型配置，由后端按现有详情权限返回；这是Agent默认执行模型，不是推荐服务模型、工具专用模型或某次调用实际模型。调用成本账仍使用回执实际模型与对应价格，不读取展示字段定价。
- 未上报显示“暂未上报”，读取失败显示不可用；切换好汉不得沿用上一位模型。离线记录说明为最近上报配置，不宣称实时使用；不显示渠道地址、凭据或完整配置。
- 复用现有详情读取/刷新和Runtime配置上报链路，不新建轮询、模型探测调用或前端配置；先更新唯一原型，再实现真实受影响生产者/消费者。
- 本地源码初查：Web `src/components/juyiting/AgentPanel.vue`已有详情与技能读取；API `AgentRuntimeDTO`、`AgentRegisterDTO`和`chat/.../AgentProfileCapabilitiesService.ProfileCapabilities`未提供模型字段；Web `agentProfileCapabilitiesProjection`校验精确字段集合。不能只加一行静态文案宣称链路完成。实施需核对固定候选上的Runtime上报/存储入口，补必要字段并同步详情投影兼容与测试，不机械改无关接口。
- 验收：真实上报模型展示、缺省不假报、更新后刷新、跨Agent不串值、现有权限不泄漏、长模型名在桌面/移动端换行。初查时尚未实现；截至2026-11-06模型展示已有三端候选及正式回归，Web464/465制品完成桌面/手机合成HTTP状态验证，实际生产上报/安装验收尚未执行，不能把候选当已上线。

### 历史：具体工作量估价预演（2026-11-07，已不作为实施方向）
用户曾要求先预演“具体处理过程/成果规模/收费工具用量”方案；后续明确改回模型直接预计Token乘单价，以§1第6项为现行合同。以下保留当时预演事实及结论，不再要求完成该方案或系数标定。

已复用生产API a6eee0d2的实际economy-core归档，通过独立Java源码诊断运行原TaskQuoteCalculator；未启动API、无Gradle构建、无钱包/生产配置写入、无模型调用。7个**手工合成工作量**加3个取整/价格快照断言通过；证据`../../docs/implementation/evidence/beta-wen-billing-20261105/cutover-20261107/concrete-workload-offline-rehearsal.json`。这证明既有计算器能承接离线转换后的模型/工具数量，不证明新的推荐输出、估算参数或真实成本误差已经验证。

预演明确两项需要补足的依据：多轮输入须考虑重复上下文、前轮输出及被读回的工具结果，不能只以资料长度计一次；收费工具需绑定实际工具/规格/单位与价表，缺价保持不可报价。样例中图片0.2元/张纯为加法测试，不是用户或官方价格；同一报告加一轮修改从4文变6文也是敏感性演示，不是实际事项报价。原始资料长度不可得时保留未知，不能将文件数量当已读文本长度。合成轮次/输出预算不导入生产，不凭默认缓存命中压低估价。

真实模型预演已于2026-11-07获准执行：用户“允许，下次不用再问了”，后续同类小范围费用预演不再逐次询问；不扩大为无界调用、实际收费工具执行或生产金融操作授权。本批同一请求两次gpt-6-luna均HTTP200/completed、结构可解析，未执行工具。证据`../../docs/implementation/evidence/beta-wen-billing-20261105/cutover-20261107/concrete-workload-model-rehearsal.json`。

**结论：字段输出可行，但当前具体工作量估价设计不具备直接生产启用依据。** 同一报告预计文本输出11500/18400字符（+60%），代码5400/10000字符（+85.19%），图片配文800/1500字符；图片数量均为2且缺规格/价，缺资料案例均明确无法估算。两次不是统计稳定性结论。把原始结果机械套入未校准的1.5 token/字符、500固定输入样例映射，报告和代码均出现11/16文差异；这些数值存在资料预加载与工具读回重复计量风险，只作为诊断，绝不作为有效报价或生产默认。它们不能证明真实任务成本误差。

历史建议（本轮不实施）：后端持有实际可用资料规模、上下文覆盖关系、工具收费身份/规格和价格；模型给出阶段/次数、最终成果数量/规模，明确区分最终成果与中间过程输出。实际重发上下文仍须计入每次调用，但同一读取发生不能重复作为“初始已包含”和“新增内容”。资料未解析、工具变体或换算系数未知时保留未知，不让模型编造。已有资料提取可复用，不新增推荐阶段全量附件读取或另一套框架。固定提示/工具定义开销与字符换算需实际测量，不把本轮合成500/1.5变成默认值。

本批两次直接响应共1912输入、2191输出Token（包含reasoning，不重复加attribution），缓存读写均0；按用户确认单价参考折算0.008605元（6位），不是供应商账单核销、事项执行成本或用户扣款。前置Python默认CA路径缺失导致一次TLS验证失败，发生于HTTP发送前；显式使用主机系统CA并验证TLS后执行上述两次，无跳过证书校验、无付费请求自动重试。普通推荐API/原生app-server未参与本预演，不据此宣称生产业务全链通过。本期不据预演修改资金状态机或活动配置。

## 4. 责任与最小数据合同（设计方向，非已落地DDL）

- 事项：业务权限、根锁、需求版本/资料绑定、承办及验收取消状态；引用不可变报价和资金结果。
- economy：人民币价格版本、报价计算、活动发放、文余额/预占/结算、人民币成本明细与汇总；不读取事项内部表复制业务权限。
- 推荐适配：一次推荐返回现有建议及整事项输入/输出Token估计，费用模块直接按登记单价计算；不增加模型定价权。扩展影响真实输出Schema及其消费者，须对应联动回归。
- bridge/Provider适配：真实用量归一化与关联，不持有用户余额或实现退款业务。共用API接口规范v1.4、RB-1及根AGENTS分层职责；外仓规则显式交接。
- Web：用户进入事件、候选报价、余额/预占结果；原型先行，前端不判断资金安全，不显示持续消耗告警。

价格条目最少绑定计费渠道身份、实际模型、计费类别/单位、人民币单价、版本及维护依据；不用显示Provider密钥。报价保留事项/需求材料身份、候选、原始Token估计/估计方法版本及价格版本、计算依据、整数文金额。
成本明细绑定逻辑调用/尝试与Provider回执身份、事项、实际模型/渠道、原始用量、归一化类别、价格版本、人民币6位金额、完整性/计价状态。重复投递去重但真正第二次收费尝试另计；累计usage不逐条叠加，reasoning/cache是否包含于总量按真实合同归一化。币种来源非人民币时等人工价，不偷偷换汇。
人民币成本账不参与文钱包结算事务；已验收/取消的迟到成本仍可补齐且不二次扣款。成功、失败、取消均可有成本；无usage标待核对，缺价标待计价；原始依据保留，核对修订可追溯。

## 5. 性能与必要保护


### 长期结构与历史切换（2026-11-05用户补充）

- 按长期职责设计本期最小实现，不为兼容旧银两/微银两和旧收费流程新增临时适配层、双轨计费、单位猜测或长期运行时新旧分支；不提前建设尚无需求的通用框架。
- 新写入统一使用人民币成本账、整数文钱包和新事项生命周期合同。真实受影响的生产者、消费者、维护入口及测试一次改齐；替换范围内的旧收费入口随切换退役，不通过旧接口包装保留旧业务语义。
- 历史通过一次性、可恢复的数据切换处理：旧资金按已确认范围备份后清理，已承办存量显式标识免费，未承办存量进入新规则。免费存量是确定的业务分类，不靠缺字段/无账本猜测，也不另建旧结算执行链。
- 历史调用、成果与审计记录只读保留，不改写实际模型、不追溯套新价。一次性迁移工具与运行时业务分开，保留恢复证据，不将迁移逻辑留在常态请求路径或应用启动路径。
- 切换前核对实际依赖并协调发布/停写与恢复，不能为删除兼容代码而破坏未切换消费者或已有事实；不自动重放历史任务。合法无害新增字段的协议兼容仍按项目规则处理，不等于维持旧计费双轨。

### 用户补充实施约束（2026-11-05）

- 不过度设计、不过度防御，性能和业务主流程优先。复用现有模块、事务、配置及回执机制；不为本期新增微服务、通用计费/营销框架、独立消息中间件或多层校验体系。
- 规则只在明确责任层执行一次；检查须对应实际风险，不能用“以防万一”增加查询、逐行过滤或重复认证。保留资金原子性、业务授权、幂等和数据完整性，不将精简理解为移除这些保护。
- 主链路仅增加必要动作：推荐复用原调用估算；确认承办做报价/余额判断和短事务预占；验收固定结算；取消释放。事务内不进行模型、网络或文件I/O，不为报价额外调用模型。
- 实际成本统计、迟到usage补账、活动发放失败及模型展示读取失败，不阻塞进入页面、议事、验收或取消。复用已有可靠回执/恢复链，不为“异步”另造平台，也不用易丢的内存任务冒充可靠记账。
- 边界不变：余额不足、必要价格缺失只阻止对应承办确认；预占、结算或释放写入失败不得伪报业务成功，沿既有事务保证一致性。成本统计异常不等于资金事务失败。
- 模型展示复用详情接口和刷新，不增加轮询；无关字段、接口及模块不顺手重构。仅覆盖真实受影响链路的定向测试，观察实际查询/调用开销，不新增无依据性能门禁或业务强制deadline。


- 保留同库短事务，不拆资金微服务、不加分布式补偿平台。承办+预占、验收+扣款、取消+释放共用既有事务；网络/模型/文件I/O不在锁内。
- 余额/资金幂等由费用模块一次负责，权限/状态由事项模块一次负责，不重复JWT/tenant解析，不每个DAO再增加分区参数。
- 调用完成或既有回执带用量，后台一次记账；不逐token/逐帧fsync或写库。引用既有durable回执链补齐恢复，不靠易丢的内存异步线程宣称可靠。
- 只维护必要钱包与事项成本汇总，已成功入账/修正时原子更新，避免重复回执重复累加；列表不扫描所有调用明细。无新增轮询服务、摘要服务或通用活动引擎。
- 必要保护及风险：原子余额→防并发超额；业务幂等→防重复赠送/预占/扣款；事务互斥→防取消与验收双落账；固定报价绑定→防旧需求冒用；可信用量去重→防虚报/重复计费。缺数据只影响对应候选或成本记录，不升级为全站停用。
- 不新增数据库CHECK；现有必要主键/唯一键/外键/类型/非空、锁和事务保留，DDL/initializer/catalog与回归随真实结构变化同步。

## 6. 有界实施切片与验收

1. 固定单位/金额合同、真实资金引用清单与迁移方案；识别旧钱包与活动领取记录的重置边界、旧未验收资金和存量免费标识。只准备脚本，不自动执行清库。
2. 在唯一原型落实文余额、候选报价/无法报价/余额不足、预占和终态结果；API完成整数文账本与按活动一次的配置化赠送。
3. 价格/工作量估算模块及推荐联动，确认承办真实调用链预占；固定报价保持与失效条件按§1执行，不恢复旧TTL。
4. 验收固定扣款、取消全释放、存量免费和待承办新规则；异常/并发集中测试，不全链重复防御矩阵。
5. API推荐及Runtime/收费工具用量链逐项接入人民币成本账和汇总，缺数可核对不阻塞资金结算；真实价格和用量覆盖状态独立记录。
6. 按2026-11-06最新规则，受影响正式回归、构建及打包默认本地执行，绑定固定源码、真实批次和制品SHA-256，不启动付费Flow；授权切换后独立备份安装/资金重置及线上验收，不重复构建精确输入已验证的制品。

最小验收矩阵：同活动重复/并发/改金额/停用/新活动；0.123456→13文与整数边界；报价保留及需求变化；缺价候选不影响他人；多事项抢同余额只有足额成功；预占/指派任一失败全回滚；取消与验收竞争/重复；失败与长期未验不解冻；缺成本仍验收扣固定价；后续修改不追加；迟到成本不扣款；累计usage/cache包含关系/重复回执/真实重试独立计费；旧免费/旧待承办及切换竞态；不误删技能权益/成果。跨端真实浏览器及金额合同覆盖，原型/Mock不冒充线上资金验收。

## 6.1 文钱包及进厅事件候选合同（2026-11-05源码切片）

本节是新方案的候选实现说明，不修改旧冻结证据，不代表已上线或整个资金闭环完成。

- Money wire继续使用`amountMinor`十进制字符串，`currency`固定`WEN`，值就是整数文，不乘除百万。所有本次真实共享消费者同步`*Wen`字段及文显示；人民币成本仍独立6位精度，报价最终一次向上取整。
- 进入聚义厅的认证身份就绪后，Web通过既有HTTP客户端发送`POST /economy/events`，公共请求信封data为`{"event":"HALL_ENTERED"}`。服务端仅使用可信身份，活动/金额均来自配置；data返回`{grants:[{transactionId,status:"POSTED",amount:{amountMinor:"3500",currency:"WEN"},campaignRef}]}`。无符合活动为`grants:[]`，不是伪造已发钱。
- `economy.campaigns.grants`数组支持活动id、event、enabled、amount-wen、starts-at、ends-at；同事件可配置多个独立活动。起始时刻包含、结束时刻不包含。停用/新增同类活动无需修改代码；使用现有配置发布机制，不宣称自动热刷新或任意未实现的事件类型。
- 活动id+scope+actor唯一决定领取身份，改金额不产生第二次领取，重试返回原账本金额；新活动应使用新id。领取事实复用不可变账本，每活动短事务，不新增活动领取表。部分活动成功后再次发送事件不会重复发已成功活动。
- 活动请求不阻塞主页面，切身份/卸载取消旧请求并丢弃迟到回执；错误留未确认供重入/retry。租金确认不再顺带领取旧欢迎金。活动失败不等于免除将来的承办余额检查。
- 资金必要保护：领取幂等由原账本承担，防重复/并发发放；账本失败事务回滚，防只增加余额没有凭证；活动id唯一、正金额与有效期规则由配置入口承担，防配置冲突及错误发放。回归入口：`EconomyCampaignPropertiesTest`、`EconomyPostingServiceRealTransactionTest`、`EconomyWalletControllerTest`与Web `hall-campaign-grant.test.js`。不重复认证或逐层重验tenant。
- 源候选3500文活动默认关闭，旧托管微金额隐式默认已移除，不将其按文解释；旧资金切换与新托管文价格登记前不可单独上线此候选。未执行生产DDL/发钱/模型切换。

## 7. 当前实现与剩余边界（2026-11-08核对）

- 内测资金最小闭环已上线并通过真实浏览器+SQL验收：文钱包、配置活动、推荐报价、选择承办时预占、验收固定扣款、取消全额释放。创建/推荐不预占；未验收继续预占；历史事项显式LEGACY_FREE。
- 推荐人民币usage已实测PRICED。原生/CHAT逐调用计费证据仍待核实，保持PENDING而非0；该核实不阻断用户固定报价结算。五类工作量（DOCUMENT/DATA/CODE/MEDIA/GENERAL）均纳入已核实模型的Token报价；看图、音视频理解不因MEDIA标签被拒绝。额外收费图片生成/工具尚无价目，不启用其收费工具路由、不擅自当免费；Token报价不授予工具执行权限。
- 运行配置：`/home/isp/hosts/cyf/api/application-prod.properties`保存已确认价目/活动/可信路由；推荐回执`/home/isp/state/cyf-api/recommendation-usage`由cyf-api拥有、0700，须在部署初始化时保证可写，不在生产程序目录写回执。推荐transport复用Spring AI common/chat连接解析规则和HTTP customizers，单池、零自动重试，凭据不复制到费用配置。
- API发布及真实验收已完成，源码集成状态以handoff最终记录为准；不以本页代替远端提交核验。本轮未重建Web/Runtime。不足余额、缺价格及资金并发/幂等由既有定向真实HTTP/MySQL回归证明，不为线上测试耗尽真实用户钱包。
- 历史切片、冻结输入和原失败保留，不将下方当时“未上线”描述冒充当前状态。尚未确定价格的媒体能力、Provider核销及后续财务岗位不属于本次启用范围。

### 第四切片内部费用事务合同（2026-11-05候选，尚未接通业务入口）
- `TaskBillingService`全部调用要求已有业务事务；事项责任层在同事务持有事项根锁，负责当前身份/需求/资料/承办状态。费用层不读Agent任务表、不复制认证。报价生成前的模型/工具调用必须在该短事务外完成。
- `economy_task_quote`保存不可变报价、付款用户、需求revision/SHA、资料摘要、候选/推荐身份以及规则/用量/人民币单价快照。相同绑定重试读取原价，付款身份不可替换；不同推荐可以报价，预占必须携带用户选定的quoteId，不查“最新价”替换。
- `economy_task_charge`每owner事项唯一。预占严格使用quote固定整数文；`RESERVING`只存在于未提交事务，成功转`HELD`。验收`CAPTURED`、取消`RELEASED`互斥；同终态重复返回原流水，反向终态拒绝。没有执行失败/超时转移。0文仍保存状态但不制造0金额流水。
- 缺账单不能当免费：验收和已承办取消拒绝缺账单；明确未承办取消允许无账单。`LEGACY_FREE`仅由受控切换为已承办存量显式写入，运行服务不自动补此标记。
- 复用现有账户、分录、escrow和funding lot；预占/释放仍使用通用BOUNTY模板，固定验收收入新增`CAPTURE_TASK`→SYSTEM/TASK_FEE，不冒充MODEL_COST、不沿用旧分账比例。账户创建按已有统一锁序使用独占式无改值upsert，避免INSERT IGNORE共享锁升级死锁；原余额只能由posting服务改动。
- 必要保护及失败范围：owner/绑定错配只拒绝该次选择；余额不足使承办事务整体回滚；预占/结算与业务完成事实任何一步失败均一起回滚；冲突终态不再动钱。唯一键保护重复事实，根锁/charge行锁串行化状态；预占先原子插入（重复不改值）再锁账单，避免缺行FOR UPDATE后插入导致不同事项gap锁冲突；不存在逐层JWT、单价二次校验或新增数据库CHECK。
- 回归入口：`TaskBillingServiceMySqlTest`使用worker私有MySQL、生产mapper/posting、Spring MANDATORY代理和模拟调用者根锁，覆盖金额/绑定/0文/显式免费/外层回滚/并发。该测试不是实际Agent承办、验收或执行中取消的集成验收；后者尚待接入和验证。

### 人民币目录与直接Token报价（2026-11-08现行合同，已上线验收）
- 统一配置入口`economy.pricing.models/tools`；不再配置`rules`或维护`TaskEstimateRule`。模型价格绑定channel/model/tier/version/basis及人民币每百万Token单价；收费工具绑定channel/tool/unit/version/basis及人民币单位价。缺价不假定免费，无运行时汇率。
- `TaskWorkload`包含kind、inputTokens、outputTokens、deliverables和服务端路由解析的toolUnits。Token为模型对整个事项的预估，不是推荐调用自己的usage，不乘资料数/成果数，不假定缓存折扣。kind只选择既有路由，deliverables仅用于已有收费工具数量配置。
- `TaskBillingService.quote`先读取已存报价，重放不访问当前价表。新报价按`(inputTokens×输入每百万价 + outputTokens×输出每百万价)/1000000 + 已配置收费工具费用`精确计算人民币，总额×100后一次CEILING取整。快照保留原始估计、`MODEL_TOKEN_ESTIMATE`/版本1、价格依据及事项/候选绑定；旧快照保持只读，不重算、不迁移资金。
- 回归入口：`TaskWorkloadTest`、`EconomyPricingPropertiesTest`、`TaskBillingServiceMySqlTest`和既有承办/验收/取消HTTP及MySQL事务用例。对外报价DTO不变，无需修改Web或Runtime。

### 推荐同次Token估计内部合同（2026-11-07现行合同，候选已验证未部署）
- 同一次推荐输出`workload={kind,inputTokens,outputTokens,deliverables}`；类型为DOCUMENT/DATA/CODE/MEDIA/GENERAL，用于现有模型/工具路由，不是复杂度分档。成果数为正整数，一份答复也算一个成果。
- Token分别为非负long整数且不能同时为0；模型输出缺失、非整数、越界或未知kind时沿既有`RECOMMENDATION_INVALID_RESULT`拒绝本次无效结果，不静默生成免费报价。模型解码边界负责该检查，准确率偏差不是无效结果。
- 模型不得提供价格、余额或收费渠道；未知资料正文不伪装已读，但依据当前信息正常估计。工具结果作为输入估计；工具调用本身若另外收费，沿既有服务端toolUnits与价目单独计算，普通工具不凭调用次数统一加价。
- 看图识别、OCR、文档转换、文本/表格/代码、多附件混合均复用同一次Token估计，不追加“视觉附加费”、按文件数倍乘或复杂度档位；成果数量只作用于明确登记的收费工具单位数。workload为内部数据，显式JsonIgnore；对外仍返回既有候选quoteId与文金额。沿`AssigneeRecommendationServiceTest`、`AssigneeRecommendationControllerTest`、`AssigneeRecommendationModelTest`及路由/报价回归验证，不新增报价模型调用。

### 推荐报价接口（2026-11-05第七切片候选）
- 原`POST /agent/tasks/{taskId}/recommend`公共信封不变，每个`recommendations[]`新增必填`quote`。可报价为`{state:"AVAILABLE",quoteId,recommendationId,amount:{amountMinor:"13",currency:"WEN"},unavailableReason:null}`；不可报价为`{state:"UNAVAILABLE",quoteId:null,recommendationId,amount:null,unavailableReason}`。金额为非负整数文字符串；0文仅来自显式已配置的计算，不由缺价推断。没有TTL字段。
- 不可报价仅影响该候选，仍显示能力推荐理由。原因包括`BILLING_ROUTE_MISSING`、`MODEL_PRICE_MISSING`、`TOKEN_PRICE_MISSING`、`TOOL_PRICE_MISSING`和`QUOTE_AMOUNT_OVERFLOW`；Web分别解释计费配置、模型价目、Token价目、收费工具价目或金额超界，未知新增原因仍可展示通用费用未就绪，不诱导反复付费推荐；未预占、不读余额、不让模型定价。只有已保存的quoteId能作为后续承办入口的选择标识；本切片报价展示不能单独宣称预占已完成。
- **历史实现（2026-11-08；已由2026-11-14数据库价目实现取代）**：服务端路由入口`jia.agent.task-pricing.routes`按`agentId + kind`精确登记`channel/model/tier`和工具估算项`{channel,tool,unit,unitsPerDeliverable}`。工具列表必须显式给出（无独立收费工具为`[]`），不根据显示模型、技能名或Provider品牌猜测。路由是与实际执行渠道核对后登记的运营配置，不改变Agent真实执行配置；缺省空，当前核实的3位gpt-6-luna承办人必须覆盖全部5种kind（15条），MEDIA含看图识别等Token工作，不等于付费生图授权。新增承办人仍须登记核实后的执行渠道/模型，不根据展示字段给未知实例猜价。2026-11-08覆盖修复的实际安装状态见handoff接续61。
- 现行覆盖回归复用`ops/release/tests/AssigneeQuoteCoverageProbe.java`，使用精确安装JAR中的数据库价目实现及原计算器，在只读MySQL事务中覆盖全部有效绑定和平台支持模型×五种kind，金额与独立冻结向量比对；不生成quoteId、不写钱包、不调用Provider。旧Spring Binder离线配置探针已退出，真实推荐/资金及舍入等回归分别由详设§11—13指定的测试证明。
- 模型调用始终在事务外。结束后原事项根锁内重新核对任务/候选/材料，再读取当前需求与执行授权服务的全量去重固定版本输入目录；所有候选共用一次资料快照和一次推荐ID。报价绑定需求revision/SHA、现有`TASK_LINKED_INPUT_SNAPSHOT_V1`摘要、候选ID与recommendationId，付款身份来自可信Actor的actorId（JWT sub），不能用ownerJiacn代替。
- 缺价等`TaskPricingService.Unavailable`在任何报价写入前发生，允许上层转成单候选不可报价，不标记整个MANDATORY事务回滚。SQL、快照写入及其他资金完整性异常仍整体回滚；真实MySQL覆盖可报价/缺价混合候选。

## 2026-11-05 承办预占接线候选（定向Flow已通过，未发布）

- 普通v2 assign携带`quoteId/recommendationId`；point-and-deliberate data为`targetAgentId/expectedTaskVersion/requirementRevision/quoteId/recommendationId`，版本保持十进制字符串。共享请求data样例见`fixtures/task-assignment-quote.json`；外层沿公共接口v1.4。付款用户只从认证JWT取得，不接收客户端payer、不以ownerJiacn代替。
- 共用assignLocked在既有根锁事务的assignment validator中调用economy.reserve，再修改承办状态、grant和bootstrap。资金层核对报价scope/需求/全事项资料摘要/承办人/推荐标识、payer及余额，失败整体回滚。普通point复用同根锁全目录及快照，不重复锁每个文件；controlled执行资料子集不替代全事项目录的报价绑定。
- quote/recommendation进入承办幂等摘要，controlled preview同步相同摘要。原操作重试读取原账单并核对payer/quote，不重新预占；原CAPTURED/RELEASED不恢复HELD。缺账单不视为免费。失败报价409、付款主体不符403、余额不足409，不产生启动意图。
- Web新本地恢复记录v3保存完整原body，在异步读取前冻结选择，重试同一原键/报价；历史v1/v2仅只读事实，不补价/重放。API操作查询响应仍版本2。聚义厅恢复路由同步v3。
- 必要资金校验依据：同业务owner不等于同钱包user。身份属接口入口，根锁/权限/状态属Agent，付款绑定/余额/账本属economy；拒绝范围为此次承办事务。回归入口为`AgentTaskExecutionGrantServiceImplTest`、`AgentTaskExecutionGrantControllerTest`、`AgentTaskBountyBootstrapOutboxServiceImplTest`及`TaskBillingServiceMySqlTest`。
- 原API候选d6b9的验证遗漏已修复；最终`26e63c2b77d4feb1a6448ad97addbcac197ff1f4` / tree `867c2e50915f2340d35e2fd56a0c069bed561fc6`通过Flow5260799/527（504项、0失败、1既有Runtime联测跳过），正式验收capture接线同轮通过；Web`78c069cf94631c07d1d93e7d2f59268632872217`有333项轻量回归。旧non-v2/funded入口未退役，执行中取消release/usage账未接齐，Agent+真实账本同库原子性集成仍待验证；不可单独上线。Run519误跑develop、520初始化被本Owner取消均不是候选验证；共享Flow被其他任务改动后未抢占。详见handoff及`implementation-slice-8.json`。

### 正式验收结算接线（2026-11-05第九切片候选，定向Flow已通过，未发布）
- `AgentTaskFormalDeliveryDecisionServiceImpl.decideLocked`在原事项根锁事务内，验证待验收成果/工作项/承办成员后，先调用`TaskBillingService.capture`，再写验收、事项/工作项/成员完成及事件。使用原事项账单固定文金额，不传实际usage，不查当前模型价格、不新增网络调用。
- 资金账单缺失不推断免费，扣款失败中止本次决策；任一后续业务写入失败应与扣款一起回滚。`LEGACY_FREE`仅由受控切换显式登记，不在验收时补造。资金与完成事实仍由各自责任层实现，共用原事务而非另造补偿流程。
- `CHANGES_REQUESTED`不调用capture/release，保持预占；已有正式决策重放只读返回原事实，不补扣历史费用或自动重放执行。当前HTTP请求/响应不变，不要求Web联动。
- 必要回归：原正式验收/返工用例、持根锁先扣款后写完成、缺账单不写任何完成事实、历史已验收重放不补扣。费用服务真实MySQL已有扣款幂等/事务回滚回归；**完整Agent+真实账本同库原子性仍需集成验证，不以Mock单测替代。**
- 第八切片新增Grant错误影响既有Provider费用授权错误映射，已补报价不可用/余额不足→CONFLICT、付款人不匹配→FORBIDDEN，保留原失败原因；定向测试覆盖三类，非新增权限或重验付款人。

- 本节候选正式证据：Flow5260799/527，62 suites /504项，503通过、0失败、1因缺CYF_GSS_RUNTIME_TEST_SOURCE跳过；validateLayering/fresh bootJar/同Run上传通过。源码、摘要与局限见`docs/implementation/evidence/beta-wen-billing-20261105/implementation-slice-9.json`及handoff。未合develop/发布；单模块MySQL与服务Mock回归不等于完整跨模块原子性或真实浏览器验收。

### 2026-11-05 同库事务与初始取消补充核验
- 固定API `0c83bdaae082e30f1dbe35e2d4977e3243659b23`经Flow5260799/529，新增七项真实MySQL的事项/资金同库集成通过：承办/预占和验收/扣款的失败回滚、提交可见性、重放/并发及返工保持预占。身份/资料和外部broker为替身，提交成果为准备fixture，不覆盖Runtime提交链。
- 固定API `27bb05bc61c35eb9670766f3286eb795b43304a3`经Flow5260799/530，未启动事项取消已在原根锁事务接`TaskBillingService.release`。原取消重放不重复调用资金；已承办事实要求账单，明确未承办无账单可取消。沿用原业务终止及撤销能力，不新增钱款适配层/接口字段；无新CHECK。608项中607通过、1既有Runtime联测跳过，完整initialCancellation 97项通过。
- 该取消回归的资金边界为替身，真实取消+资金集成仍待补充；执行/命令事实存在时仍沿原规则拒绝，**不代表执行中取消闭环完成**。已发出的调用不得被当成已停止/零成本，扩大取消能力须补派发及迟到回执验证。
- 上文“Agent+真实账本同库原子性待验证”仅在承办/验收范围由本补充更新，其他待办不重标完成。结果与摘要见既有handoff及`implementation-slice-10/11.json`；没有合develop、部署或生产资金/活动/模型变更，仍不可单独上线。

### 未派发启动意图取消规则（2026-11-05，候选实施中）
- 初始取消可关闭无租约、未admit的PENDING或RETRY启动意图；同事项根锁和outbox行锁/版本CAS内标DEAD、原因TASK_CANCELLED，释放预占并撤销grant。PENDING保留真实attempt_count=0，不能为兼容历史失败语义伪造一次尝试；该终态重放不重新派发/退款。
- PENDING必须尚无重试时间/已admit身份，RETRY保留已有尝试事实。零次DEAD只在明确TASK_CANCELLED时作为未派发取消事实读取。CLAIMED（包括租约已过期但未由worker回收）不由这一步抢占：并发claim先成功则取消拒绝并保持原预占，取消先成功则后续claim查询不再领取。完整执行中取消另行处理，不能把此范围扩大解释为Provider已停止。
- 责任层：状态语义由事项取消服务；排队状态/版本CAS和claim互斥由现有DAO；钱款由TaskBillingService。内部方法改名cancelQueuedBootstrap并同步真实调用/测试，不保留旧方法适配，不变更外部接口或DDL。回归入口为initialCancellation及AgentTaskBillingMySqlTransactionTest。

### 2026-11-05 初始取消真实资金验收补充
- 上节PENDING/RETRY未派发取消已实现于API `0d985fce937155364834a14a157c4153dc761868`，Flow5260799/533通过（618项、0失败、1既有Runtime联测跳过）；不代表已上线。此前“真实取消+资金集成待补”在**初始取消**范围更新为已验证。
- 真实同库Agent+economy用例15项通过，新增8项覆盖原付款退款/重放/并发、事件及occupation最后写入失败全回滚、提交前不可见、未承办无账单与已承办缺账单、PENDING取消保留0次尝试且不可再领取、claim对取消竞争。实际DAO和费用服务没有替身；Chat基础表复用mapper测试DDL，生产执行表按取消读取所需DDL准备，不冒充完整Runtime迁移、relay或提交链验收。
- CLAIMED/执行中/已有命令事实的取消尚未放开；实际usage账、旧旁路退役及跨端验收仍待完成。费用模块不读取事项表，事项服务在原根锁短事务调用费用服务；队列关闭复用原DAO版本CAS，无额外模型/网络调用。固定证据见既有handoff与`implementation-slice-12.json`。

### 已领取但未admit的启动意图（2026-11-05，候选）
- 覆盖上一节“CLAIMED一律拒绝”的阶段性限制：CLAIMED只表示议事admission被worker领取，不等同于模型执行。Owner取消已通过原事项权限、根锁及current inventory确认无active Chat/native execution/command事实时，可使该启动意图终态化。
- 责任层：事项根锁串行化取消与Chat admission（Chat原事务内grants.admit）；取消DAO以已锁行id/version CAS写DEAD/TASK_CANCELLED、清领取租约、版本+1，保留真实尝试次数；费用release同事务。原worker所有旧版本reconcile拒绝，不能写回ADMITTED/RETRY；原grant admission拒绝。取消失败恢复原lease/version/预占，worker可按原合同继续reconcile。
- 这是授权业务取消使旧领取失效，不是夺取worker进程或运维锁，不伪造Provider已停止。已admit/开始执行的其他事实仍按既有规则拒绝；本节不扩展为完整执行中取消。回归沿AgentTaskBillingMySqlTransactionTest、initialCancellation，外部接口/DDL不变。

### 2026-11-05 已领取未admit取消核验
- 上节已由API `ee95be6bda44d5a2a2760817d8bcfaabd65d1cd9` / Flow5260799/535验证：621项中620通过、1既有Runtime联测跳过；initialCancellation 100项与真实同库资金17项全部通过。CLAIMED取消后旧grant admission及三类旧reconcile回执均拒绝；取消故障回滚原lease/version/资金预占；不增加HTTP字段、DDL或网络调用。
- 范围仍限未admit启动意图，不表示active Chat/模型执行取消、完整Chat/Runtime跨端或独立usage成本账完成。内部接口统一`cancelUnadmittedBootstrap`，无旧名包装。未合develop、未部署；原始证据`api-claimed-cancel-fixed-*`，汇总`implementation-slice-13.json`及handoff。

### 无报价承办入口退役（2026-11-05，第十四切片）
- `/agent/tasks/{taskId}/assign`只进入`AgentTaskExecutionGrantService.assignAndGrant`；JWT付款身份先由HTTP入口解析，旧body不再按是否有v2字段分流到无报价服务。缺报价/推荐标识沿既有责任层拒绝，不能推断免费或制造报价。
- 删除HTTP `auto-assign`，AgentService直接assign/autoAssign接口及实现，AgentTools直接分配工具，WS `task.assign`处理器。WS旧消息由原不支持消息类型分支拒绝，不把Agent身份转换成钱包付款人、不增加临时适配。历史任务读取/既有非执行task.event及注册/上报不随该删除变更。
- Web普通事项只保留用户显式选择单名承办人的报价point-and-start链；移除旧自动/多选分配按钮、checkbox状态和旧RewardBoard/store直接分配请求。旧RewardBoard保留只读列表并提示从办事页核对报价；不能在API未返回时自行把任务改为assigned。原请求恢复优先级不变。
- 责任边界：入口删除消除绕行；权限/账单/事务仍由grant及economy统一实现，不逐层追加资金判断。底层versioned assignment仍为新grant及旧funded claim实际依赖，未整类删除。旧funded quotes/claim、legacy report和已有历史表此次未退役，不能据此宣称全入口已闭环。
- API `6eb823c1e6989a01208114659192310c17a18edc`经Flow5260799/537通过，824项中823通过、1既有Runtime联测跳过；validateLayering/fresh bootJar/上传通过。536保留真实测试失败，不用于发布。Web正式Flow/全链浏览器验收待完成；未合develop、未部署或操作生产资金。详见第十四切片handoff与证据。

### 旧资金榜HTTP写入口退役（2026-11-06，候选）
- `/agent/tasks/{taskId}/quotes`、`/claim`、`/funding/cancel`不再注册写路由，不重定向到新预占/退款；现有普通事项取消及正式验收仍走其原根锁资金事务。
- `/agent/tasks`仍先认证JWT；有非null的`grossBountyAmountWen`、`settlementPolicy`或`requiredSkillRequirements`字段（包括空字符串/空数组）时返回HTTP410、`FUNDED_BOUNTY_RETIRED`、不可重试，不创建普通事项、不写旧资金。风险是旧浏览器恢复请求被误转普通创建或再次收费，因此由唯一HTTP协议边界识别退休的资金语义；普通请求既有服务校验不复制。
- 历史事项/资金/结算读取与原始记录保留。此候选尚未完成Web消费者及旧内部写实现退役，不得单独发布；不以HTTP路由移除宣称历史余额已清理或执行中费用已闭环。
- 定向回归：`AgentFundedBountyControllerTest`覆盖路由/依赖消失、普通JWT创建、旧请求重复/空字段拒绝；保留新grant、资金原子性与既有历史funded服务测试。执行结果以handoff记录为准。

### 2026-11-06 旧资金与事项上报写链单轨收口
- 历史funded应用服务只提供资金/技能要求/结算读取，读取不依赖preview收费开关；create/cancel/quote/claim/complete旧写服务与HTTP入口退役。Web历史任务只读、未知旧请求仅展示，不自动转换或重发；新事项承办与验收使用文报价账务事务。API候选be1fa7daf1/Flow541通过；Web候选cf90b49为定向轻量验证，均未上线。
- 旧`/tasks/{taskId}/report`、`reportAgentTask`工具及`task.report/task_report` WS不得再修改事项/工作项/成员完成状态；所有事项完成须由正式成果与用户验收产生。服务入口和内部report状态机同候选删除，不新增funded/普通/Hall三套guard。新grant仍依赖的版本化承办协作写入保留；身份、根锁和新资金回归不随旧功能移除。
- Runtime执行成功/失败保留原执行结果/恢复回执，不再另发整事项完成报告；取消/迟到成本处理与此独立，不因旧报告消失将费用记为零。API ff9274c61d正在Flow验证，Runtime04b16fb本机30项定向回归通过，未正式跨端验收或发布。

### 执行中取消责任层补充（2026-11-06候选）
- 整事项取消由已认证Owner入口持事项根事务；租约责任层`cancelForTask`只用于该内部流程，要求已有事务，不新增HTTP/Agent工具入口。保留精确owner/task/work/version绑定与CAS；CLAIMED/RUNNING撤销清除租约，不依赖Agent在线/仍active或租约未过期，不增加attempt、不先重排工作。保留历史成果/终态，失败整体回滚。它不是Runtime/Provider已停止证明。
- Chat责任层`TaskDiscussionCancellation`在已持根锁的事务内按conversation→turn取消CHAT/INSPECT，复用原持久STOP outbox、部分回答留存及request聚合；已提交final不重写，不增加直接网络调用。EXECUTE/技能执行由执行责任层撤销，不能把取消讨论当所有执行停止。此接口与租约撤销均需接入整事项协调后才构成完整能力；当前候选不能单独上线。
- 资金释放仍与业务取消同事务；真实usage独立留存，取消不把已发调用成本归零。租约原语回归`AgentWorkItemLeaseServiceImplTest`，讨论回归`ChatCancellationVersionTest`；完整竞争/事务/迟到结果回归须在真实协调接通后执行。

### 2026-11-06 事项执行取消状态（候选实现，未接通整事项协调）
- Agent执行层采用显式`CANCELLED`，不借`FAILED`或`INPUTS_REVOKED`表示事项取消；仅TASK/CONVERSATION未终态执行适用，PRIVATE语义不变。已经提交/失败/撤销的终态保持原记录，暂存输出、技能effects/result manifest、Provider已开始和租约历史均保留。
- 内部`TaskExecutionCancellationService`要求加入调用方既有根事务，按精确owner/task锁执行后锁技能附件，使用原版本CAS；任一写失败整体回滚。未提交技能READY/RUNNING/WAITING_PROVIDER/RESULT_UNKNOWN/RESULT_READY可关闭为CANCELLED，不据此声称外部副作用已经撤回或不再产生费用。
- Chat沿已有afterCommit投影hint及持久扫描映射为CANCELLED；Web停止该执行的轮询并展示原记录，不能显示成果已提交或免除费用。既有成果读取、状态扫描/初始化合法值同步，未新增数据库CHECK/生产迁移。
- 回归入口：TaskExecutionCancellationMySqlTest验证真实MySQL范围、CAS/回滚、并发与历史事实保留；WorkspaceProjectionQueryMySqlTest验证exact唤醒与扫描使用同一终态条件；Web既有personal/formal execution与Hall回归。当前端口尚未接入事项取消服务，不据此放开执行中取消或宣称资金闭环完工。

### 取消时未消费Provider许可（2026-11-06，候选）
- 事项取消在原根事务内调用既有Provider consent服务，精确锁定本owner/task的ISSUED/BOUND/RESERVED后复用原revoke/revokeFollowup状态及版本CAS；覆盖首次执行、后续执行与普通action，不新增外部授权入口。
- CONSUMED表示已经发生的付费尝试，REVOKED表示既有撤销事实，两者保持不变；撤销未用许可不清除binding/reserved执行身份，不伪造Provider退款或取消成功。取消重放不改历史版本或重复调用供应商。未知purpose拒绝本次事务，不按其他类型猜测使用。
- 本能力尚未接通整事项协调。真实MySQL验收需覆盖三种purpose×三种未消费状态、已消费全行不变、与执行状态共同回滚、精确owner/task及MANDATORY事务，资金原子性仍由后续整合验证，不把内部许可测试当整事项完成。

### 6.2 实际成本账实施边界（2026-11-06，进行中）

- 已实现并通过Flow555的`TokenUsageCost`只做单次用量计价，不是持久化账本。`Usage`必须由真实来源适配器明确整次收费尝试和不重叠类别后构造；未知累计/增量或cache包含语义保持待核对，不能将`last`或`total`字段名当计费依据。结果区分`PENDING_USAGE`、`PENDING_PRICE`、`PRICED`；pending金额为空，真实显式零用量可记0.000000。
- 模型渠道/名称/处理档位按实际响应或经核验的调用合同精确绑定。调用前保留人民币价快照和版本；迟到回执不能查当天默认价补算历史。请求配置模型只作请求证据，不能冒称真实模型。缺某非零用量类别价格只影响该调用，不能将部分合计伪报完整成本。
- 账本后续沿`economy`原模块分为收费尝试身份、追加核对修订、事项成本汇总三个职责，不复用文交易/预占记录承载成本。按可信scope和attempt绑定事项；真正第二次Provider收费尝试有独立attempt，投递重试复用原身份。已有回执身份加内容摘要用于重复检测，不使用文本相似度或时间窗口猜重复。
- 修订保留原始计数证据、来源及其回执引用、归一化依据、完整价快照、六位人民币和计价状态；新修订必须绑定此前版本，重复回执不新增修订。完整写入与事项汇总的金额差额、pending计数变化同一短事务提交，不扫描全调用明细累加、不接入文钱包事务。
- 可靠投递与业务终态分离：复用原调用/执行durable恢复链，先保存原始依据，后计价；API接受成本依据必须验证其既有调用/任务/身份绑定，但不要求事项仍可执行业务。取消后能补成本，不能借成本回执重新领取lease、提交成果或扣钱包。缺失/不可恢复的用量显式待核对，禁止自动重放收费调用来补账。
- 原生app-server通知证据目前只支持已知字段采集并标`UNVERIFIED`。Runtime成功终态复用本地terminal checkpoint保存，失败异常携带证据；仍须打通独立成本接收与ack，以及原执行状态清理前的证据保留，不能以这一步宣称可靠完整到账。推荐侧直接ChatModel的metadata、普通议事及真实收费工具同样要逐入口接入；不新增通用全局拦截器猜业务事项，不把工具金额换算成token。
- 必要校验归属：来源适配器负责usage语义、实际route和attempt绑定；接收边界负责认证/协议；费用服务负责重复/修订版本和汇总事务；事项权限/状态和钱包保持原责任层。用量不可核实仅留下待核对，不升级为议事/验收/取消失败。该节是实施合同，不代表后三项持久化表、接收端或全入口已经完成。

### 6.3 原生执行成本证据回执（2026-11-06候选，未上线）
- 统一信封固定主工作区`api/docs/interface-standard.md` v1.4，SHA256 `2d36ffac1dc52c6db8d54b860695edd845b6688ea0808528c53218e39aec7a08`。新增Runtime-only `POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/usage`；Q.data为`{executionId,phase,requestedModel,usageEvidence}`；phase必填STARTED或TERMINAL，后两项可null，STARTED不允许携带usage。`requestedModel`仅配置证据，usageEvidence为原生通知证据对象，不接受调用方提供价格/金额/owner。
- 成功R.data：`{executionId,attemptId,revision,status,costYuan}`；revision为十进制字符串，status沿成本域PENDING_USAGE/PENDING_PRICE/PRICED，costYuan未知为null、已核验为6位人民币字符串。成功表示原始证据持久接收，不表示已计价、免费或业务完成。示例`{"executionId":"exec","attemptId":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","revision":"1","status":"PENDING_USAGE","costYuan":null}`。
- 接收使用现有Runtime认证和native fence；历史权限专属SQL绑定execution/task/run/tenant/client/target agent、原grant不可变executor owner/binding和当前认证Runtime绑定。grant撤销/替换version及执行CANCELLED/FAILED/RESULT_COMMITTED不阻止历史成本写；不放宽原findForRuntime业务入口。未知/不匹配历史绑定404，证据冲突409，只影响本次成本投递。
- 该来源命名`NATIVE_EXECUTION_EVIDENCE`，sourceAttemptId=executionId；STARTED以receiptId=started/expectedRevision=0创建revision1，TERMINAL以receiptId=terminal/expectedRevision=1更新同一attempt至revision2；旧回执重投返回原revision，不计第二个attempt；它是执行层待核对证据，不声称一次原生turn等于一次Provider付费调用。last/total不求和或取差，不查事后价格伪装调用前快照；当前归一化与价格均null，后续经核验另行修订，不自动重放收费调用。
- Runtime在调用引擎前复用native-start-attempt持久化requestedModel；保留成功native-final-message或失败native-usage-failure，终态恢复使用native-usage-recovered（即使usage缺失也明确pending，不取当前模型冒充原请求模型）；业务receipt/failure-receipt不代表费用已ACK。沿现有skill-runs安全扫描同时发现待投递费用，业务终态也继续发现；固定payload重投只发送费用HTTP，不恢复lease/模型/成果。先投递STARTED并存native-usage-start-receipt，再投递TERMINAL并存native-usage-receipt，分别保存payload摘要及服务端receipt；无终态的断进程执行也由开始标记发现并投递pending，业务回执不隐藏它；丢响应/断进程不清证据，复用现有轮询与15秒至5分钟退避（不是请求截止）。成本投递失败只记录usageErrors，不把已完成业务改为失败；身份切换/存储不安全仍按原边界终止。
- 本候选已接调用前本地持久化开始记录及重启后的pending投递，API不阻塞在每次模型调用前等待网络：进程存活期间仍在现有轮询投递，崩溃后由恢复发现。永久丢失本地状态无法据此恢复完整usage；各真实Provider子调用归属/价格，以及普通CHAT/INSPECT/付费工具来源仍待补齐，不能以本节宣称全来源成本核算完成。engine Home清理与skill-runs证据目录是不同范围；当前源证据目录没有自动删除路径，不通过业务ACK删除费用快照。

### 7. 受控切换准备：真实目录与保留边界（2026-11-06核对，未执行迁移）

本节基于API候选`d357aca448eb082262902b7b836eb819f8230558`及本机MySQL `jia`库只读目录/聚合查询；证据`billing-live-catalog-readonly.json`、`billing-live-aggregate-readonly.json`。使用只读事务、无业务正文/凭据输出、无DDL/DML。**这不是停写一致性备份，尚未核实运行API的datasource确实绑定该库，不能直接用于生产执行。** `jia_dev`也有事项表，禁止按名称猜测后批量清理两个环境。

已发现必须保留的实际依赖：
- 314个SILVER账户、316笔transaction、632条entry；3个escrow和3条funding lot。不能改币种/列名就把旧微银两数值解释为文，也不能只清balance而留新账可重放的旧资金幂等事实。
- 14条ACTIVE技能订单、8项安装、8项权益，外键由installation/entitlement/receipt指向order，再由order关联quote/product version。**不能把`economy_*`全部当可删资金表。** 技能包版本/摘要、授权、安装/权益、管理请求与结果保留；旧订单金融字段与新文价格登记的切换需在完整依赖快照上准备，不删除权益或禁用外键来凑清库。
- 3条托管lease（2 ACTIVE、1 REFUNDED）、既有provisioning/reprovision记录存在；身份/实际托管服务及已有效租期不是旧余额，不能清资金时删除、退款或重新开通。新托管文单价必须另行登记，不能使用旧micro默认值。
- 121条事项根，当前聚合108条具有至少一项已承办事实（状态/指派时间或Agent/成员/授权）。这只是候选统计，**不是最终迁移名单**；不按创建时间或“缺账单”推断免费。受控停写后的固定scope/owner/task清单才用于写入`LEGACY_FREE`，amount_wen=0，不补预占、quote或Provider调用。其余未承办事项走新报价；历史已取消/归档不恢复或重放。
- 新`economy_task_quote/charge`与`economy_usage_attempt/revision/task_cost`尚未出现在该目录中。费用调用记录即使pending也不属于旧钱包清理范围。真实目录有不可变流水触发器与外键；不可执行直接DELETE/TRUNCATE或全库CHECK/触发器清理。

执行准备顺序（仍须另获实际安装/数据切换授权）：
1. 将获授权运行目标、datasource/环境scope、完整三端commit/tree/正式构建批次及制品SHA（2026-11-06起默认本地）、配置前值绑定同一批次；不部署develop浮动HEAD。停止旧资金/承办相关写入及其后台入口，保留Runtime身份/会话/业务状态，不能用成本投递替代旧执行授权。
2. 对该真实目标做完整可恢复备份，固定SHOW CREATE/外键/触发器/行级关联及承办分类清单。根据快照生成一次性、作用域明确的变更，不用源码DDL冒充线上目录；不提供未核实依赖的通用清库脚本。
3. 在隔离库复演新文账基础创建、旧资金归档清空、存量免费标记、权益/租期/成果保留与恢复；保持主外键/唯一键、事务和锁归属。原旧金额仅留在明确历史备份中，不以临时业务双轨读取旧金额。非资金依赖的保留结构/迁移表达须在复演前定案，当前尚未完成此部分DML设计。
4. 配置候选仍保持`economy.campaigns.grants[0].enabled=false`，活动id为`beta-hall-welcome-v1`、事件HALL_ENTERED、金额3500；真正启用只改配置而非改代码，停止活动保留既有领取事实，不换id制造同活动第二次发放。模型/工具的手工人民币单价及可信路由需完整登记（不再登记估算系数规则）；不按缺价=0放行，不新增运行时汇率。
5. 安装/数据切换/配置生效/业务验收分别记录。真实验收覆盖赠送一次、报价向上取整、足额预占、验收固定扣款、取消释放、迟到成本不重复扣、旧免费事项及既有技能权益。恢复不能直接覆盖已发生的新文交易/业务完成事实；若已恢复写入，应先对新事实做受控恢复设计，不能盲还原旧库快照。

本节完成了真实只读盘点与执行边界梳理，**未完成可执行迁移、隔离复演或生产切换**；不能因其他测试已绿而单独安装新货币候选。

### 价格参考复核（2026-11-06，未登记生产价格）
本轮已实际打开官方API Pricing与gpt-6-luna模型页，标准短上下文每百万token的美元基础价与用户表一致（输入0.10、输出0.50、缓存读0.01、30分钟写0.125、12小时写0.25）；证据`official-luna-price-reference-20261106.json`保存来源与时间。此前11月5日抓取未取得的记录仍是历史事实，不改写成当时已验证。

适用范围不能省略：官方模型页说明超过272000输入token时整请求输入/缓存乘2、输出乘1.5；区域处理在适用时另加10%，不同处理速度不是同一单价。当前配置模型只有channel/model/tier平面索引，尚未表达上下文价格适用范围；**登记基础价前须补明确范围/保留调用前价格依据，不能对长上下文静默套短价，也不能用费用计价限制中断模型请求。** 本次不更新既有一次性人民币转换系数、不设置运行时汇率，实际渠道采购账单仍须与配置对应。

官方app-server页面此次仍只明确thread级usage通知及独立model reroute事件，未建立last/total逐Provider请求计价合同；所以原生证据保持UNVERIFIED/PENDING_USAGE，而不是用模型请求参数假充实际计费模型。

### 承办资金拒绝的前端反馈（2026-11-06候选）
后端既有`TASK_FUNDS_INSUFFICIENT`/HTTP409是首次承办资金事务被拒绝的权威结果。Web保留此错误码，仅在原意图已按既有规则释放、状态为REJECTED时提示“可用文余额不足，无法确认承办；本次未预占费用。”UNKNOWN/原请求恢复/已经确认的承办仍沿原核对提示，不能据迟到错误承诺零预占；不预读余额、不新增轮询、不复制服务端资金准入。原型在既有承办演示追加`funds=insufficient`，验证以handoff与固定制品为准。

### 6.4 普通CHAT成本来源（2026-11-06，实施合同）
- 成本attempt允许`taskId=null`，仅表示真实非事项调用；owner/source/sourceAttemptId仍必填且不可改绑。无事项时只写同一attempt/revision账，不创建虚构事项汇总；有事项仍按原短事务维护economy_task_cost。没有新增钱包或会话计费规则。
- CHAT来源以原dispatchId作为sourceAttemptId（source=`CHAT_EXECUTION_EVIDENCE`）。`POST /internal/agent/chat/dispatches/{dispatchId}/usage`采用公共Q/R及STARTED/TERMINAL两相，与原生执行一样分别固定receiptId started/terminal、revision1/2。调用方不提交owner/taskId，服务从原dispatch读取归属。请求字段为phase、requestedModel、usageEvidence；响应dispatchId/attemptId/revision/status/costYuan。
- 迟到成本授权只读原dispatch/turn身份与原grant的executor owner/binding，不要求当前事项、grant、dispatch或turn仍active；旧grant撤销、事项取消不能删除已有费用。非事项/既有多成员owner-only dispatch仍仅允许原owner的目标Agent；不借成本入口恢复业务权限、重跑模型或返还/补扣资金。
- Runtime在现有CHAT inbox责任范围独立保留usage source/ACK文件，不放入7天/容量清理的业务archive。runTurn前落STARTED，返回/明确失败/恢复读取后落TERMINAL，再做业务正文校验。投递使用原后台节奏，先STARTED获ACK再TERMINAL；源保留至独立费用ACK，不依赖最终消息ACK、不按token写盘、不新增同步API前置调用。无usage或未核实last/total语义继续PENDING_USAGE，不计算伪精确成本。
- 必要回归：无事项记账及不可改绑；原dispatch授权下取消/迟到/换绑/跨owner；原始usage先于正文失败留存；业务archive清理不丢费用、丢ACK/重启恢复、无二次runTurn。规格写入不是代码/正式验证完成。

#### §6.4候选实现核对（2026-11-06）
API公共认证入口通过`AuthenticatedRuntimeOperation`调用现有session fence，成本业务服务不依赖具体认证实现；Runtime1.3.63/bridge1.1.52在现有CHAT inbox中维护`usage-pending`及`usage-acknowledged`，后台投递与native discovery共用调度、不前置于模型调用。已通过API573定向/真实MySQL与Runtime160正式回归，额外公共Q/R及认证代理回归以handoff的API574终态为准。均为未部署候选，不能据此视作生产账单或原生last/total计价语义已经确认。

### 6.5 单请求上下文价表与事项估算分离（2026-11-06实施约束）
**当前启用策略（2026-11-07用户决定）：先统一单价，不按上下文长度加价。** 使用既有空阈值/空长价配置即可，不删除通用计价能力、不新增代码分支或双轨适配。各Token类别仍保留已确认的独立单价；本决定不将未核实usage变成已核实，也不把统一单价理解为每事项固定同一报价。生产配置和实际验收状态另记。
`ModelTokenPrice`保留手工人民币基础价表，新增可选`shortContextMaxInputTokens`及`longContextYuanPerMillionTokens`，与channel/model/tier/version/basis一并快照。阈值未配置表示该登记价表明确按平价使用；配置阈值后，单请求所有非重叠输入类别合计超过阈值时整请求各类别使用长上下文价表，不按超出部分阶梯累加。不配置长价/某项长价则该实际成本PENDING_PRICE，不回落到短价或0。长价也手动登记人民币，不在运行时引入美元换算或厂商倍率。
事项估算tokens是多轮累计，不是单请求输入；事项报价仍使用所登记基础估算价，不能用累计数量触发实际请求的上下文溢价。纯计价层区分`estimateCost`与单请求`cost`，不修改预占、验收及取消状态机，不增加任何网络请求或业务前置限额。实际channel的登记依据须包含采购渠道/地域等计费范围，不能用缺失地域推定区域折扣；本节不宣称实际渠道已核实或配置已启用。
必要回归：阈值等于/超过（缓存输入参与、输出不参与）、整请求长价而非分段、缺价保持pending、旧价表快照在配置更改后不变、整事项估算不误套请求阈值；沿既有pricing/usage测试入口，不新增检查框架。

### 6.6 推荐原始费用回执落库恢复（2026-11-06实施约束）
推荐适配器保留原STARTING短事务；付费调用前准备专用持久回执目录，未配置/不可写时不开始该调用，不影响其他业务。收到原生响应后，仅将可信绑定、原始usage/模型/tier、规范化用量、调用前价表、原revision及原observedAt落一个私有文件，随后调用现有幂等成本账；不保存提示词/正文，不逐token写盘。文件先完整写入并force，再同目录原子发布，发布后才允许数据库投递。数据库失败保留原文件并返回业务响应，不将数据库故障转成二次付费调用；文件发布失败仍抛错，STARTING保持pending，不虚报已可靠记账。
恢复只扫描进程配置scope对应目录，定时重投同一Observation，不查询当前价格、不改owner/task、不重跑模型、不修改钱包；数据库提交成功/已提交回放后才删除文件。未知提交结果保持可幂等重投。目录非临时/非业务成果目录，归API服务账号所有，目录0700/文件0600，迁移/恢复须保留，不供模型或Runtime写入。无目录配置不启动推荐付费调用；生产路径只提供候选，不自动创建生产状态或启用。
必要回归：DB失败与进程重建、提交后ACK丢失、价格/原时间稳定、文件失败不开始付费调用、不同scope分区、损坏文件不删除/不阻挡其他来源、业务正文解析前留存。进程在收到响应与首次持久写入之间仍存在不可消除的崩溃窗口，STARTING明确pending，不能承诺与Provider分布式原子性。

### 6.7 真实钱包HTTP与资金数据库验收边界（2026-11-06）
在Flow既有独占MySQL夹具内启用真实loopback Tomcat、签名JWT验证、生产公共Q/R codec、钱包Controller/Service/Mapper及资金事务；不得使用模拟HTTP或SQL结果替代。覆盖HALL_ENTERED仅首用领取3500文、同活动改金额不重复/原金额回执、停活动不再领取、新活动可配置、跨用户/租户/客户端隔离和非法信封无资金写入。
事项资金测试可通过真实TaskBillingService持调用方事务及夹具根锁创建报价/预占/验收/取消，再经真实HTTP读取余额与流水；证明资金责任层与钱包展示读模型，不冒充Agent承办Controller/启动意图/实际模型执行链路。真实usage在验收后录入，不改变可用/预占及扣款流水。完整Agent承办与整站浏览器仍单独验收，本切片不能替代它们；不调用付费Provider、不访问生产数据库。

#### 受控切换的零价技能事实补充（2026-11-06只读盘点）
新增`billing-value-shapes-readonly.json`仅查询金额ZERO/NONZERO分布、不读取用户正文：当前本机jia目录19个技能产品版本、21个购买quote、14个ACTIVE订单和2条order receipt均为零价；订单均无escrow/reserve/capture交易引用。`SkillPackages`验证package SHA、技能身份和权限摘要，价格来自数据库产品投影，不在这里重写技能ZIP。
因此候选技能迁移可在正式停写快照**再次证明全部零价且无资金关联**后，原位把四个非空BIGINT列`agent_skill_product_version.price_micro`、`economy_skill_order.price_micro`、`economy_skill_order_receipt.price_micro`及`economy_skill_purchase_quote.expected_price_micro`改为新`*_wen`名称并保持0；这是保留明确免费事实，不是把旧非零资金换算为文。保留全部主外键、唯一键、订单/安装/权益关系与包/权限摘要，不重签/重装技能；不需要额外LEGACY价格兼容字段或双读。发现非零价或关联资金则不能套用该候选，先重新归因；此次目录不是停写一致性快照，尚未执行ALTER或隔离复演。
托管不能套用此捷径：3条原intent均为非零价（2 ACTIVE/1 REFUNDED），1个ACTIVE具有Runtime安装身份，另有SERVICE_READY的reprovision事实。其身份、租期、恢复绑定仍须单独保留；不能将非零amount_micro直接改名冒充文，也不能清除reserve/capture字段后让原身份逻辑猜测完成状态。

### 7.1 零价技能列切换与恢复的执行合同（2026-11-06候选）
只覆盖§7已盘点的四个零价技能列，不清账、不变更托管、不创建事项免费分类。维护SQL放既有API `agent/jia-agent-mapper/src/main/resources/db/migrations/`，显式安装/调用/删除一次性routine，不进入任何initializer或应用启动路径。调用方先绑定目标datasource及完整停写备份、停全部这些表的写入，再执行；routine使用既有`cyf:economy-v0:skill-schema`锁，竞争时立即失败不抢锁。
资金完整性责任：在任何ALTER之前，四个目标表分别必须只有一个旧/新价格列、类型仍为非空有符号BIGINT、全表价格为0；order不得有escrow/reserve/capture/refund资金引用，receipt不得有escrow引用。该前提来自此次真实目录：不得把非零金额换单位或抹掉其历史。缺列/双列/非零/资金引用只拒绝该维护调用，不变更资金、不绕外键、不修改运行代码。
执行仅RENAME COLUMN，保持所有行与主外键/索引/触发器/包及权限摘要；四个MySQL DDL并非跨表事务原子。停写期间若在中途失败，保留已完成的目录事实；再次调用可识别每表唯一旧/新列并继续目标方向，不增加业务双读。反向仅限恢复写入之前、仍全零且无资金关联的同一备份窗口；如已恢复业务写入，先按新事实另做恢复设计，不盲逆转或覆盖快照。必要回归：完整关联保留、重入/中断续行/反向、非零/资金引用/混合列拒绝、锁归属与无锁泄漏。正式测试只在Flow独占库复演，不运行于本机真实jia。

### 承办回执与费用重放职责补正（2026-11-06，实际HTTP发现）
授权grant的request_hash仍使用能从原授权事实复算的事项/承办人/版本/输入/操作域，不能再包一层只有费用模块持有的quote/recommendation摘要，否则预占已提交而原operation恢复读取返回INTEGRITY_ERROR。费用模块在原task锁/事务内统一核对重放的quote、付款人和原recommendation；只在重放路径读取已存在的不可变quote snapshot，不重新推荐/估价、不查当前价格、不重新预占。Agent不读取费用表，operation GET也不新增账务查询或付款操作。历史授权只读摘要规则保持，未发布错误候选不加兼容读分支。真实HTTP+MySQL回归覆盖首次与重复确认、原operation投影、替换quote/recommendation拒绝、固定验收和取消释放；不以Mock grant/readback响应冒充该边界。

### 7.2 非零托管切换业务口径（2026-11-06用户确认）

API `013cda02485a0cf774091fd7f043447ede6f1ad4` 的 `HostingRentLedgerServiceImpl` 会把原intent的金额、capture/refund交易号作为重放结果；报价和租金计划要求正金额。故把旧列直接改为`amount_wen`会改变金额含义，清交易而保留原intent则留下无对应账本的收据；把金额置零也不是现有免费托管能力。关闭新托管入口不解决已有ACTIVE租期及SERVICE_READY恢复读取。这是资金切换的具体依赖，不扩展为全项目兼容改造。

用户已确认：旧资金留在完整只读归档；现有有效托管身份/剩余租期无偿保留至原到期日，不退还或兑换旧单位，新续期才按文报价收费。原已退款事实只保留历史，不生成新文退款。SERVICE_READY恢复只沿原身份/原操作确认，不重建Runtime或重扣款。**此确认是业务规则授权，不是生产清账、数据迁移或部署授权；不得伪造0元付款或增发租期。** 在租期/结算责任层表达既有租期的非收费来源并隔离复演，不让业务常态请求读取微银两或进行运行时换算。原到期时间、身份及已有恢复操作保持不变；旧退款只读留档，不产生文交易。

实际迁移仍需要获授权目标的停写快照；此前只读本机目录不是运行datasource证明。固定目标、权益清单与恢复方案之前，不生成自动全库清理命令。

#### 保留租期的结算来源（接续36实施合同）
- 责任层：费用域intent显式`settlementKind=PAID|RETAINED`（新单PAID）。RETAINED是已核定权益来源，不是0元付款，也不是运行时旧币转换。租约读模型携带最新intent的来源；租期/身份/原恢复操作不变。只有停写迁移将已核实终态ACTIVE/REFUNDED事实标为RETAINED，不能对在途预占或未知结果推断。
- RETAINED记录新单位金额为0，reserve/capture/refund交易引用清除；原金额及原交易保留在固定只读归档。旧财务请求不得重放为新文付款/退款。保留的ACTIVE租约仍可到期、免费重整及以新PAID报价续期，续期后最新intent和金额来自新交易。
- Wire变化只涉及托管租约读取：`lease.settlementKind`。Web据明确RETAINED显示保留权益及原到期日，不展示“已付0文”或伪造流水；不以零金额推断赠送。新的报价/确认仍要求正整数文。固定接口规范仍是v1.4，不改变统一信封、授权和幂等。
- 定向验证：费用域拒绝RETAINED旧资金重放、新续期真实扣款；实际Mapper/数据库读取来源；租期/身份/恢复事实不变；Web可读保留权益、续期/重整入口、无假流水。迁移只做独占合成库演练，生产需另绑定授权datasource及完整备份；当前段为实现目标，不代表迁移已完成。
- 浏览器托管恢复记录按文使用独立命名空间`cyf-hosting-rent-wen-v1`。不读取、转换或重放旧单位的本地报价/付款请求；旧缓存不再挡住保留租期的服务端读取，也不清理用户其他存储。此切换与“生产迁移前全部旧托管付款已明确终态”的前提配套，不允许丢弃未知支付来重新付款。

### 2026-11-07实现与验证边界（接续39）
- 保留租期PAID/RETAINED及Web独立文缓存等补充已合入组件develop：API a6eee0d2680a98b6b4d84d796571156c5cb68be7，Web b1c97e2ba909f08cda36eba8b7246027b30cfbeb；API1.1.40/Web1.16.124本地包成功。真实资金浏览器使用本次Web包、JWT/Tomcat/隔离MySQL，足额预占与不足拒绝通过；非资金辅助资料仍是fixture。具体fresh/复用边界见handoff接续39及对应result，不用单个总数替代证据范围。
- 旧非零租金迁移已完成合成库复演；本条不意味着生产旧账清空/权益迁移完成。生产目标datasource、停写快照与恢复、精确旧免费事项清单、安装/配置/活动生效仍需绑定实际授权再执行，3500文活动保持关闭。
- 已授权的一次直接文本采样只确认该次响应model/token证据，不确认采购人民币账单、非零缓存写入TTL/单价或原生app-server逐调用语义。未知成本继续PENDING，不以测试通过或单次响应宣称全部成本准确可计价；未增加付费采样。

### 个人中心钱袋入口（2026-11-08）

钱袋是个人中心常规功能，不依赖前端经济开发预览构建开关。个人中心从移动端“我的”及办事/事项/资料常规页直接可达，不把普通页面打开状态当作模态锁；真实模态面板与语音锁、未完成工作离开确认保留。个人中心与钱袋使用聚义厅米白、朱红风格和独立标题/返回入口；身份、钱袋、基本资料、登录安全优先展示，其余能力折叠在“更多功能”，无权限内部看板不展示。用户从“我的钱袋”进入，查看可用文、预占文与收支记录，并可返回个人中心。服务端身份/权限与开放状态仍为权威；不可用或请求失败留在钱袋显示错误和重试，不能静默跳回或显示假零余额。账号切换清空旧金额并忽略旧请求返回。只读查询不触发赠送、预占、扣费或退款；不扩大到充值/提现。Web1.16.126 / f694161已上线，已用390px真实触屏链路验证“我的→个人中心→钱袋→返回”，并检查桌面布局及直接刷新；证据见handoff接续59收口。

### 图片Provider子调用成本（2026-11-08实施合同）

图片技能generate/edit每次HTTP调用单独记账，不混入编排模型的token，不用图片像素/文件大小/估算token替代usage。本地resize无Provider调用，不产生模型用量。报价/预占/验收固定结算合同不变；实际成本独立汇总到原事项。

- 工具在宿主提供的`CYF_PROVIDER_USAGE_DIR`写每调用UUID的STARTED/TERMINAL原始回执；先持久化开始再发请求，收到JSON后先留usage再校验图片/执行缩放，因此坏图片/后处理失败仍可核算真实消耗。网络未知或缺usage记录null，不记0、不重发付费请求。
- Runtime仅按执行目录扫描通用Provider回执，复制到原skill-runs可信journal，利用原发现/重试/独立ACK投递。源及ACK与业务成果回执分离，已验收/取消也允许按原授权补记。只对新调用有效，不重放历史任务；不得删除尚未投递的scratch/.provider-usage目录。文件永久丢失不能恢复未知用量，不保证覆盖绕开授权技能脚本的自行调用。
- 新`POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/provider-usage`使用既有Q/R、Runtime认证和native fence。请求data为executionId、observation（schemaVersion=1、invocationId、protocol、channel、tier、priceVersion、requestedModel、operation、phase、observedAt、evidence）。evidence仅含usage/responseModel/providerRequestId，不含提示词、图片正文、端点凭据。响应复用executionId/attemptId/revision/status/costYuan。owner与task来源于原执行历史绑定，不接收用户指定归属。
- API按`NATIVE_PROVIDER_CALL`与`executionId:invocationId`记账，started/terminal对应revision1/2。第一次STARTED选择与priceVersion精确匹配的人民币价表，TERMINAL及ACK丢失重投复用已存快照，不因当前价格变更重算；缺价保持pending。响应模型若明确变化，则不沿请求模型价表错价；不明alias不自动替换。
- `openai-images-v1`规范化以input_tokens_details.text_tokens/image_tokens与output_tokens为准，输入分项必须与总量一致。INPUT/CACHED_INPUT分别表示非缓存/缓存文本，新增IMAGE_INPUT/CACHED_IMAGE_INPUT/IMAGE_OUTPUT。缓存总量须有可解释的文本/图片分项；正缓存数无分项、冲突计数、负数或未知输出模态留PENDING_USAGE。保留原始usage以便之后明确修订，不把不确定usage记成0。
- 记录金额人民币6位HALF_UP；所有类别先相加再舍入。新输出类别不计入长上下文输入阈值；当前统一单价，无长上下文加价。

当前登记价格（2026-11-08）：`gpt-image-2.5-flare`、channel=gpt、tier=standard、version=`image-flare-cny-20261108-v1`。来源llmrates/llm-pricing-dataset的data/models.json blob `c817674a056edd0ad862f8316b0fb9060247d2be`；标准美元/百万token文本5、缓存文本1.25、图片输入8、缓存图片2、图片输出30。一次性沿当前Luna人民币价格使用的换算基准6.6879（不是2026-11-08实时汇率），登记人民币/百万token分别33.439500、8.359875、53.503200、13.375800、200.637000。不引入运行时汇率；这是核算价格基准，不冒充渠道发票实际扣款。

2026-11-08已按本地来源上线API1.1.43-SNAPSHOT（e229e52806）、Runtime1.3.67（5dc596c）；价格配置已读回生效。图片生成/编辑1.3.2已发布，吴用生成/编辑和林冲生成共3处安装通过正式升级流程SUCCEEDED/runtimeSynced=true，新installationId配置精确价目版本。已使用真实安装helper与bridge做无网络的合成回执验收，未付费生图；实际渠道响应的usage形状与账单仍待自然业务验证。详情与完整源码/包/配置摘要见既有handoff“图片用量补齐收口”。

## 2026-11-10 用户更新：欠费即收尾，满15天最终解除

本节覆盖此前“超过15天才开始收尾”和欠费允许新增技能策略变更的口径。
- 到期扣费失败立即进入可恢复收尾；内部沿用`LOCKED`表示此阶段，不新增并行状态机。禁止新承办、新密议及全部新技能变更，已受理操作和旧事项继续。`FINISHING`表示主动移除或已满15天的不可恢复最终解除。
- 连续欠费从租期到期计时，调度停机/延迟不顺延宽限期；不足15天余额恢复则自动扣费，成功时重起30天。达到15天（含等于）先进入最终解除，不再续费；即使首次到期处理延迟至此也不补扣。
- 满15天后，已交付待验收事项自动验收并扣除预占；未完成/失败事项自动取消并释放预占。沿事项既有权威状态机及资金事务，不能通过改状态字段冒充结算；重复处理不能重复扣款/退款。
- 事项终结后停止相关执行并确认真实进程退出，再提取允许共享的通用知识、清理本地私有数据。公共技能、公共配置、公共凭证与Agent实例保留，后端历史仍归原用户。不能仅删除sessions目录；会话数据库、私有工作文件、快照、临时数据及私有凭证均须由Runtime边界处理。
- Runtime清理入口复用原subject生命周期串行锁及持久handover记录：必须同installation/operation/原owner、已QUIESCED且无executor、evidenceAccepted后才调用存储清理。仅存储清理明确完成后持久写入cleanupComplete；缺适配器、失败或未确认不得写成功，重试仍为原操作。清理回执不是API关系释放或新用户授权，重启仍保持旧执行停止。该控制journal及writer锁不属于待删除私有业务材料。
- API托管适配器cleanup与quiesce/flushEvidence复用事务外UDS调用和完整回执绑定；只接受同原请求所有字段、相同host和CLEANED结果，丢回复、EVIDENCE_ACCEPTED、QUIESCED或CLEANUP_PENDING均不作为清理完成。该适配器不自行重新登记身份、扣费或完成业务关系释放。跨端共享hosting-cleanup-v1.json，验收须包含真实Java编码/Node控制服务/磁盘清理，不仅模拟响应。
- 静态／自行部署配置可在Agent条目声明publicFilesPath：读取运维持有0600的JSON，必须精确匹配manifest的tenantId/clientId/canonicalAgentId，只允许config.toml及可选auth.json的公共内容。源文件必须在所有Agent可变根及host state之外，启动时读取并冻结，不从旧HOME复制，不经控制请求传入。缺该基线不改变普通执行，但不能通过最终清理；上线前须配置真实运维来源，源码支持不等于已配置。
- 托管清理控制使用hosting.cleanup/hosting.cleanup.result，沿quiesce/evidence的完整原关系、候选部署代次和handoverId，只有当前已admitted操作可调用；仅CLEANED表示Runtime持久清理成功，CLEANUP_PENDING不能推进API关系释放。请求不能携带路径、publicFiles或凭据。managed publicFiles由已持久化subject.template.codexConfig生成，公共Provider环境原样保留在可信模板；旧HOME/auth不作为公共凭据来源。工厂缺真实知识提取adapter时明确拒绝，不用固定成功桩启用生产清理。候选CLI可从operator专用平台模型配置接通真实会话分批读取/提取/复核/公共保存，未配置时不启用；实际配置与验收/生产状态以handoff为准。
- 知识提取在同一handover控制记录持久REQUESTED之后才调用Provider，EXTRACTED/FAILED结果须在任何私有删除前持久保存；清理后续失败或重启复用该事实，不重复提取。重启只见REQUESTED表示前次结果不明，记FAILED并继续清理，不自动再次耗费token，也不伪称已提取。请求状态写入失败不调用Provider、不删除材料；记录仅含状态，不含私有正文或原始错误。
- 私有清理聚合先预检公共HOME基线、stateRoot及全部材料根，再尝试按同operation幂等提取知识；提取失败允许继续删除，但只记FAILED，不保存可能含私有正文的错误消息。材料按执行端实际根处理：workspaceFileRootDir、生图ledger、typedInspection输入/状态的hex(agentId)子目录及非公共工作目录；不扫typed父目录，不扫公共workspace policy根。知识尝试、原技能退休及state清理、材料清理、HOME重建全部执行后才返回confirmed供Host写最终回执，局部成功不得冒充整体完成。
- Runtime stateRoot清理先通过同一真实SkillInstallManager定位器退休原关系，未收到技能结果回执或归属不符不得清除私有状态。仅保留handover.json、当前.runtime-writer.lock和已退休的公共技能管理journal/packages，沿公共技能目录的祖先逐层清理其余inbox、会话凭证及私有工作数据；不得整删inbox导致公共包丢失，也不得整留inbox泄露旧用户数据。stateRoot局部完成仍非最终cleanupComplete。
- CODEX_HOME存储清理在原证据送达、技能退休和知识提取尝试之后执行：只保留公共skills目录，config.toml及需要落盘的公共auth.json从可信operator/template重建，不从旧HOME复制；删除其余会话、SQLite及WAL/SHM、日志、快照、临时数据与未知私有文件。公共配置来源未就绪或HOME与公共仓库重叠时不得开始删除；子链接仅删除链接，不跟随到外部目标。HOME局部完成不等于所有私有根或最终关系解除完成。
- **公共仓库边界（2026-11-10用户确认）**：共享项目仓库及其Git历史属于公共数据，解除关系时保留；不得因清理Agent私有数据删除仓库、共享Git对象、分支或历史提交，也不得将配置的codexWorkdir直接视为可递归删除的私有目录。该分类不将私有会话、附件、凭证及专用临时数据转为公共数据；这些仍按原关系归属清理。任务worktree与共享仓库的关系须在Runtime存储边界识别，不能递归清理整个workspace policy根，也不能用改写共享Git历史代替私有根清理。保留不表示新增对外公开或跨用户授权。
- 公共知识候选只含去除用户/业务/凭据/路径/原始片段后的通用方法，发布前独立隐私复核；复核不通过不发布，不能用模型自称授权替代清理/公开边界。模型复核须经过实际材料语义验收，结构测试不等于隐私保证。公共知识和平台成本回执存于独立host根下，不放在将被清理的CODEX_HOME/用户state/work内；不为保留知识而保留原会话或draft。平台调用先持久STARTED，响应成本证据先于输出验证保存；未知结果不重试花费、记待核算，清理恢复沿原handover事实避免重复调用。当前候选模块及未接通边界见同任务handoff，不能据此认定生产已启用。
- 提取不得原样公开私有会话，提取失败留记录、不阻断私有清理；清理失败不得释放重新邀请资格。公共知识提取产生的模型费用由平台承担（2026-11-10用户确认）：按实际usage与对应模型单价记录平台成本，人民币保留6位精度；不扣原用户的文、不占用用户余额、不计入原事项费用或验收结算。保留Agent及提取批次关联以供追溯，不能因关联原关系而将费用归给原用户；缺usage或价格时记待核算，不伪记零成本。原事项执行的迟到费用仍按原绑定记账，与本次平台知识提取费用分开。
- 本节是确认合同；源码、定向验证、完整收尾及上线状态分别记录于现有handoff，不代表全链已完成。

### 平台知识成本上报与清理顺序（2026-11-10，候选未发布）
- 成本入口为`POST /internal/agent/hosting-leases/{leaseId}/knowledge-usage`，沿统一HTTP Q/R及原生Runtime认证，不使用用户JWT或请求指定的费用承担人。API在原生身份fence内核对原owner/Agent的FINISHING关系；不要求已停止的执行通道在线，不重新enroll/register。Runtime负责QUIESCED无执行进程、已补送原执行证据的清理准入。
- 请求data为`{handoverId, observation:{batchId,stage,phase,channel,requestedModel,requestedTier,evidence}}`；stage仅extract/privacy-review，phase仅STARTED/RESPONDED，当前requestedTier为standard。STARTED先本地持久，再由API保存价格快照并确认，之后才调用模型；RESPONDED上报providerReceiptId/actualModel/serviceTier/usage/httpStatus，不能用requestedModel补实际模型。缺usage/价格仍进入平台待核算，不阻止保留已知事实。
- API成本来源PUBLIC_KNOWLEDGE_EXTRACTION，sourceAttemptId为JSON数组`[agentId,leaseId,handoverId,batchId,stage]`；无owner/task绑定。沿成本journal的SHA-256(JSON([source,sourceAttemptId]))得到attemptId。响应data为`{handoverId,attemptId,revision,status,costYuan}`，revision为字符串（started=1/responded=2）、金额为六位精度人民币字符串或null。重复同回执返回原revision/快照；迟到现价不改已保存事实。
- Runtime同一启动instanceId用于执行与维护原生会话。host平台journal按subject及lease/handover分区；每个阶段按attempt保存STARTED、RESPONDED和绑定原receipt摘要的API ACK，不保存输入、原会话、draft或平台密钥。不扫描所有历史Agent记录，不给业务执行热路径增加成本查询。
- 清理持久EXTRACTED/FAILED后，必须补送本次所有未ACK成本证据；仅补传回执、不再调用模型。上传失败/ACK错误/凭据不可用时保留原私有数据与凭据，等待同handover恢复，不标CLEANED。提取本身失败不阻断清理的前提是费用证据已入平台账；只有STARTED而无响应时保留PENDING_USAGE也可确认，不伪记零消费。已全部ACK的恢复不再创建原生会话或重复发送。
- 以上是跨端候选合同，不代表完整FINISHING业务handler、真实Provider语义验收、生产迁移或发布完成。

### 自动验收事实来源（2026-11-10）
- 已满15天最终收尾的自动验收复用正式交付决定/capture事务，不新增用户可传的自动验收标记或HTTP入口。事项owner仍为原用户，但reviewed_by_jiacn留空、review_reason固定hosting_rent_expired，不能写成原用户手动操作。
- FORMAL_DELIVERY_ACCEPTED系统来源：actorType=system、actorId=null，现有payload六字段之外增加reasonCode=hosting_rent_expired。手动来源仍为role/task_owner且无reasonCode；system没有固定原因或手动来源冒用该原因均不是合法事实。快照/SSE读取同步该明确来源，旧记录保留不重标。
- 自动验收只有submitted正式交付才可执行；reviewing却无该交付属于数据不一致，不猜验收也不改作退款。已终态事项只读跳过，过期关系/旧调度不能处理新邀请者事项；失败事项仍走取消释放预占。

### Runtime停止阶段合同补充（2026-11-10，候选未启用）
- 复用受限UDS与公共protocolVersion=1信封，新增`hosting.quiesce`/`hosting.quiesce.result`。data沿用当前已受理prepare/ensure的完整关系与候选字段，另加非空`handoverId`（由最终收尾业务操作稳定生成，不用每次传输requestId替代）。`operationId`仍指原INITIAL/REPROVISION，不挪作终结ID；provisionGeneration仍为十进制字符串，validUntilAt/runtimeInstallationId映射保持现行合同。
- API必须在事务外调用，按FINISHING原关系取得已知候选，不重新prepare/enroll。Runtime校验配置允许scope、journal原owner/binding/lease/intent/operation、installation/manifest/generation且该operation为当前已受理代次；不接收任何路径、命令或凭据。迟到旧代次拒绝；成功仅返回原请求字段+`outcome:QUIESCED`+`hostId`。
- Runtime在原subject gate/持久handover.json下实际关闭执行；等待中的原subject注册可取消并join，不停其他Agent。相同handoverId可重试/重启读取；不同ID冲突。停止后拒绝新reprovision，既有事实可查询。丢响应/API交换失败不能证明已停止；重试同一业务ID，不重新扣费或创建实例。
- QUIESCED不证明私有清理、知识提取或关系解除；最终handler不能只收到本回执就完成schedule/开放邀请。本补充不新增公开HTTP停止入口，也未启用生产调度。
- 两端共享合成报文：Runtime `conf/cyf-agent-runtime-v1/test/fixtures/hosting-quiesce-v1.json`、API `agent/jia-agent-service/src/test/resources/hosting/hosting-quiesce-v1.json`，SHA256 `5230221928fbf0c6155cb9a655f2e5e192aa92e744098ff9a2c63c50d57e6324`。沿用统一接口规范1.2/RB-1；回归必须分别覆盖生产编码、解码和实际状态作用，不把合成报文视为线上验收。

### 2026-11-10 停止后费用证据收尾（RB-03，内部生命周期候选）

- 私有清理的费用前置条件为原用户/安装归属的消耗证据已由API持久接收，而不是每笔费用已定价；`PENDING_USAGE`/`PENDING_PRICE`保留未知，不补零、不重调模型。业务验收/失败回执不代替独立usage回执。
- Runtime在已持久`QUIESCED`、本subject writer/gate仍持有且executor已退出的条件下执行`flushAgentEvidence`。沿既有`handover.json`绑定原installation、handover operation和owner；跨owner请求拒绝。后端原关系仍有效期间，复用原Runtime authorization创建仅供native HTTP发送的session，不注册在线、不恢复业务队列/lease/模型执行；完成或失败后撤掉本机session。
- 普通CHAT与native/provider原始源共用既有receipt/幂等协议；一次flush最多发送源的STARTED与TERMINAL两个阶段，网络失败不在该调用中无限重试。重试仍是发送原source，不以新用户/新task归属发送。旧命令无法解析、source/receipt不一致或未收到明确回执时不能宣称费用证据收尾成功。
- `evidenceAccepted=true`只是在永久停止条件下记录本地费用证据已送达，**不是清理/重新邀请/业务结清完成标志**；公共技能保留、私有清理、知识提取及关系释放需各自完成。现阶段通过下述hosting.evidence内部控制合同提供，API最终收尾handler尚未接入。源码、定向验证及生产状态以当前handoff分别记录。

### 2026-11-10 公共技能安装事实与关系退休（RB-03）

- 同Agent实例保留的技能是可验证的公共安装事实（包/版本、权限摘要、manifest、不可变包摘要及当前启用视图），不是把旧用户的管理命令作为下一个用户的运行权限。SkillInstallManager为该分离的唯一责任层；Web/API不解析本机journal或复制包。
- 本机journal format3将公共installation metadata与私有commands/messages/identity分开；format2只在既有initialize锁下校验后做一次原子结构升级，原包与marker不改写，旧命令在关系退休前仍保留回执/恢复能力。不是按版本双轨执行或重放历史任务。
- 停止后的关系退休须匹配原身份及同handover操作，且无live session；已有管理执行的结果须收到原后端receipt（仅RECEIVED可证明未开始）。保留技能前核对所有留存包及当前视图，不把损坏包标为公共可信安装。
- 退休原子移除旧身份与管理命令、消息、执行fence，保留公共安装事实和不含原身份明文的退休标识。重复同操作幂等，其他关系不能清空原记录。退休不等于私有目录已清理，也不授予新用户自动bindSession；必须由最终清理及授权重新邀请链路显式准入。
- 实施/测试状态见同任务handoff。此节不表示已接通最终handler、自部署、私有清理/知识提取或生产启用。


### 2026-11-10 原主体停机证据通道补充（源码候选，未上线）
- `hosting.evidence`/`hosting.evidence.result`复用quiesce的完整原关系、当前已受理代次、handoverId和私有UDS权限；API事务外调用，不重新prepare/enroll。Runtime只有持久QUIESCED且executor为空才发送原成本及管理结果；不接受路径/命令/凭据、不恢复执行。回执仅原请求字段+hostId+outcome（EVIDENCE_ACCEPTED或EVIDENCE_PENDING），不产生cleanupComplete。
- `POST /internal/agent/skill-management/results`为独占native HTTP，公共请求data承载原不可变work.result报文，响应data承载同一业务服务提交后的原work.result.receipt。外层HTTP requestId与内部原消息标识分开，重投不得改写原摘要/关联ID。复用原结果事务/幂等/owner-install-host-command绑定；无有效原Runtime身份不得回退用户认证。
- 该路径及原CHAT/conversation/provider usage POST允许无在线channel送达，仍校验持久主体、安装、会话代次和授权。其他命令发现、技能下载、执行lease及成果提交仍要求原执行准入。方法、query及编码别名不扩大权限。
- 未收到原技能结果receipt不得退休journal；仅RECEIVED的未开始命令沿既有规则处理。成本未知保留PENDING，不推断为零。管理PREPARED证据仍可能创建后续ACTIVATE，最终业务handler须根据停机事实结清未执行操作，不能将证据送达当财务全部结清。
- 所有原证据送达后持久evidenceAccepted/evidenceOwnerJiacn；重启同操作幂等，跨owner/代次/操作拒绝。原usage-only候选未上线，字段及helper直接单轨替换，不新增兼容层。该回执不授权删除私有数据、重新邀请或释放关系。
- 两端共享hosting-evidence-v1.json及skill-management-result-http-v1.json，实际运行及摘要见同任务handoff；冻结接口规范1.2/RB-1保持不变。


### 2026-11-10 停机未开始技能结果与管理私有残留清理
- 在永久QUIESCED的原主体gate内，证据补报先由SkillInstallManager按原journal完成无副作用结果归档：RECEIVED且未开始的PREPARE/ACTIVATE/POLICY生成NOT_STARTED+ENTITLEMENT_TERMINATED，保留原command/request/runtime身份；不得再下载或执行。READ只复用原只读marker观察，缺失原命令仍UNKNOWN；已存在结果包含UNKNOWN均不可改写。
- API继续用原结果处理/资金事务：有确切NOT_STARTED才结束安装并幂等释放原预占；未知准备或无法证明未切换的激活继续保留HELD/RECOVERY_REQUIRED，不因terminal reason假退款。Runtime补报未知只是移交事实，不是结清证明。
- 原管理结果全部收到后退休journal。提交退休事实后清理同manager下的staging、旧lock元数据、未完成的临时journal写、未登记包及HOME/.cyf-skill-view-staging；仅保留校验过的包、公开installation事实、journal及当前持有的installer锁。只在原受控路径删除，不跟随私有残留里的链接到外部目录。
- 退休commit之后失败可按同operation恢复清理；不同owner/operation不能清空旧数据。重启创建的空临时目录可再次清理。此步骤仅覆盖技能管理私有残留，不代表整个HOME/会话/工作目录已清理，不授予重新绑定。

### 最终收尾定位实际已受理代次（2026-11-10，候选）
- 新增只读受限UDS `hosting.current`，输入为原INITIAL完整关系，不带候选/路径/凭据；Runtime按原subject gate核对initialAssociation，从持久activeOperationKey返回已admitted的完整operation关系、installation/manifest/generation及hostId。响应CURRENT只说明当前已受理代次，不证明在线、停止、证据送达或清理完成；无已受理代次返回UNKNOWN，不可据此解除关系。
- 此查询不prepare/ensure/enroll，不创建操作、增加代次或启动执行。已prepare但未admit的较高代次不得覆盖返回值；原关系之外的owner/binding/lease不返回任何候选。API按原INITIAL关系核对响应，将CURRENT作为quiesce/evidence/cleanup的明确目标；并发代次变化仍由原quiesce检查拒绝，重新查询同原关系，不猜成功。
- CURRENT的operationId/operationKind/requestedAt/validUntilAt可以不同于输入INITIAL，但tenant/client/owner/Agent/binding/lease/initialIntent/reservedAt必须一致；provisionGeneration仍为十进制字符串，runtimeInstallationId沿公共字段映射。禁止从业务表“最高授权代次”推断当前执行者。此补充不是最终handler完成或生产上线证明。

### 最终解除的财务占位收口（2026-11-10，候选未接最终handler）
- Agent生命周期责任层必须先确认原关系事项终结、进程停止、原证据及技能费用结清、知识平台费用回执和私有清理完成，再在原binding释放/凭据撤销事务内调用内部completeHandover。财务层不重复调用Runtime、不自行判断清理、不暴露用户可提交“已清理”的HTTP接口。
- 财务层锁定原lease并核对原付款主体、binding、Agent；仅FINISHING可转CLOSED并置live_slot=NULL。已CLOSED同关系重放保持原结果；换owner/binding/Agent或ACTIVE/LOCKED不能关闭。保留原租期、报价/金额、intent及历史归属，无退款、新扣费或额外续费调度。此调用要求现有事务，后续关系/撤销失败必须一起回滚；不同邀请者不能通过旧租约重放关闭新租约。
- 此为最终释放的一项依赖，不能单独接到移除入口，也不证明完整关系解除或同实例再邀请已完成。公共实例、公共技能和共享仓库/Git保留。

### 关系最终提交事务（2026-11-10，候选）
- HostingRentHandoverCompletion.completeManaged是生命周期Owner收到原关系CLEANED之后才调用的DB-only内部步骤，无HTTP入口，不把current/quiesce或调用者自报布尔值作为清理成功。完整handler接通之前此步骤不能挂到旧unbind。
- 同事务按installation→binding→INITIAL intent→lease取锁，核对原owner/付款人/Agent/安装摘要及Runtime host映射，仍有未终结事项则拒绝。撤销原Runtime安装授权及存在时的原专用key、关闭财务live slot、挂起原binding/identity并清除Runtime原用户投影。任一步失败全事务回滚；不删除Agent实例/技能/知识库/仓库/Git或原私有后端历史。
- CLOSED原关系重放只读返回，不再次撤销或触碰后续邀请者Runtime投影；旧关系换owner不视为合法重放。后台按原持久事实结清，不要求原用户仍处于可登录状态。候选单元/事务代理验证不替代真实全链路及线上验收。

### 2026-11-10 实际停止与在途技能结算边界（候选，未上线）

- `LOCKED`和`FINISHING`仅表示业务阶段，不证明进程已经退出；真实停止前，已受理技能安装仍可按原结果完成。新增字段`economy_hosting_lease.handover_id/executor_stopped_at`只记录原Runtime明确确认的QUIESCED事实，由最终收尾Owner在原绑定事务持久化，不由定时到期、在线状态、缺消息或请求发出推导。历史行不回填停止时间，迁移不改变账本。
- 同一原lease/binding/Agent/付款人/handover幂等记录；不同handover或关系不符拒绝。该事实不释放实例占位、不撤销旧证据传输身份、不表示知识提取、清理或最终移除完成。
- 已停止后原`PREPARED`回执仍被接收并原样保存。如果原命令尚未创建ACTIVATE，则在同一技能事务将变更终结并释放原安装费用；这是API尚未创建激活意图这一确定事实，不是把PREPARED改写为NOT_STARTED。已存在ACTIVATE的缺失或UNKNOWN结果不能据此退款；真实APPLIED仍按原订单结算。
- 实际停止后禁止继续派发技能变更命令，观察READ不冒充新执行。DISABLE本来已关闭API准入，原NOT_STARTED/ENTITLEMENT_TERMINATED回执在停止事实下终结其修复命令，不再永久PENDING。此规则仅作用于技能管理收尾，不增加普通事项执行派发门禁。
- 责任层为原租约事务和SkillManagement结果/派发边界；不新增各层重复查询或定时全量扫描。最终Owner接线、未收到的原命令证据补齐与所有技能资金终结仍须完成后，才能进入私有清理和关系释放。源码、验证和上线状态以任务handoff为准。
- 实际停止生产者顺序固定为：原INITIAL关系只读查询当前已admitted代次 → 原绑定及未完成事项校验 → 事务外`hosting.quiesce` → 原绑定事务记录停止事实。handoverId复用原leaseId，响应或提交丢失均重试同一业务身份；不以新的requestId生成另一收尾，不触发prepare/ensure。停止记录与最终关系释放复用同一原关系校验/锁序。该协调器已进入候选并完成定向验证，最终调度handler和完整业务验收尚未完成。

### 停机后的技能预占收口（2026-11-10，候选实现）
- 原关系的真实停止事实是收口前提，FINISHING本身不等于停机。仅在技能业务服务的原关系/原订单事务内结算，不由Runtime修改账本。
- 原生产outbox从未领取、版本及attempt次数均为初始值、无租约且原wire/摘要完整时，可取消原未派发市场命令并释放预占；只看PENDING或Runtime没有journal不成立。API记CANCELLED，不伪造Runtime结果。position不使用这条市场派发证明。
- 已按原合法回执形成FAILED_RETRYABLE的变更，在确认停止后不再允许重试，终结为FAILED_FINAL并按原订单幂等退款；保留失败安装/entitlement、原回执及原公共包，不再执行一次安装失败状态转换。退款与业务终结在同一事务，父事务失败须全部回滚。
- UNKNOWN、已领取但无确定结果的操作继续待核实；已APPLIED而实际完成的安装费用不因停止而退款。这些规则不新增用户操作入口，不改变正常在租期内的失败重试行为。
- 当前是候选实现/定向验证范围；最终FINISHING调度接线、全链路验收及生产发布分别留证，不以局部资金回归通过代替完成。

### 旧直接解绑入口退役（2026-11-10，候选实施）
- 删除旧POST `/agent/personas/bindings/{bindingId}/repair`及`AgentPersonaProvisioningService.repair/unbind`、`AgentHostedBindingTransaction.resumeRepair/prepareUnbind/completeUnbind`的旧执行链。不将旧SUSPENDING自动转换为新的清理完成事实，不为历史状态保留直接停用关系的路径。
- 主动移除仍经明确原Agent/lease的DELETE bind进入FINISHING，最终关系释放只由确认原Runtime清理后的收尾事务负责。仍被正常运行时使用的公共身份、目录及状态发布工具保留；历史绑定/托管记录不删、不重写。
- Web当前源码没有该旧repair接口消费者，因此此接口移除不默认改Web。旧源库存明确为历史；对新移除链及真实HTTP无旧映射做定向验证，不以删除旧路径测试替代身份/资金/收尾回归。

### 同实例历次关系身份（2026-11-10候选，未上线）
- 公共Agent ID随实例保留；每次邀请新建binding及对应registry关系记录，不修改旧记录的owner/client/binding或原会话/事项归属。registry的canonical不再代表“仅第一次邀请”；改为同一canonical最多一条PROVISIONED/ACTIVE关系，已停止释放的SUSPENDED/RETIRED关系保留。
- 当前注册/执行只解析当前可用关系；历史只读使用同owner下已激活过的关系，不能被同用户新建但未激活的邀请遮蔽。历史读资格不是重新执行、注册或读取其他用户私有数据的授权。别名仍绑定原registry ID与原scope，不转移给新邀请。
- 复用已有registry/binding和公共runtime，不另设身份注册表、不修改旧owner、不去掉不可变触发器/别名外键。通过生成列live_agent_id唯一索引维持一个可用关系；原canonical列保留普通检索索引，binding唯一性继续保留。旧库需显式维护迁移，启动不自动改造。
- 本段只描述当前身份基础候选；真正重邀仍必须由已确认清理的收尾记录开放、复用公共实例、换新私有凭据，不能仅凭SUSPENDED身份或索引变更放行。报价/确认、Runtime重邀、技能保留计费和全链路验收仍待完成。

### 清理后的同实例报价与确认（2026-11-10候选，未上线）
- 无当前邀请关系时，按可信tenant/client/persona读取保留的公共实例；有实例则报价使用其原Agent ID。必须已解除原私有绑定，费用域最新租约为CLOSED、已有实际停机事实，且原INITIAL installation与公共实例投影一致。单独停机、原CLOSED之前的历史记录或其他installation均不授予重邀资格。
- 确认再次取得persona/公共实例锁并核对报价Agent；不允许旧报价建立第二个公共实例。新费用预占、新binding、新关系身份、公共runtime空绑定CAS均在原事务中提交或回滚。公共配置/标识保留，原私有关系/费用证据不改归属。
- 当前API定向候选已实现；Runtime同根重邀、已安装技能首期计价及完整真实多用户回归未完成，不能以本段作为已上线说明。

### 租约查询的收尾状态（2026-11-11候选，未上线）
- 原租约查询继续返回同一lease/intent及原预占、扣款流水。`lease.status=LOCKED/FINISHING`时，`admission`分别为`LOCKED/FINISHING`，不再统称PENDING。查询不扣费、不触发重新邀请。
- Web接收同租约的更高版本权威快照：ACTIVE→LOCKED/FINISHING、LOCKED→ACTIVE/FINISHING；允许刷新错过中间状态。相同版本冲突、旧版本和FINISHING/REFUNDED复活仍拒绝。新邀请必须明确新操作并使用新lease，不能用旧租约替换身份。
- LOCKED/FINISHING只显示真实状态、原流水及重查入口，不提供初租、手动续租、免费重整动作。首次总价可能包含技能费用，租约历史amountWen标注“租约金额”，不冒充正常周期租费或已付事实。执行派发链不增加租费拦截。
- 正常到期未续费进入FINISHING；LOCKED兼容读取已有权威锁定状态，不以Web推导后端状态。FINISHING停止续费，按原15天收尾规则处理；公共技能及仓库/Git保留。
