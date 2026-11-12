# Client实例隔离与真实双模式交付

日期：2026-10-02。状态：实例安装器源码3619d33已自检合入融合feature；未安装、未注册新实例、未验收。

## 实际缺口

- 线上binding1与15都由旧共享`codex-ws-agent.service`刷新；独立local unit未运行。两个身份不等于local/server两种运行模式。
- 旧installer只提供测试APP_HOME override；生产unit与launcher固定共享根。launcher按通用`agent-client.mjs`匹配PID，不能用于多实例控制。
- 旧runtime.current_task引用没有对应scope任务、成员、work-item或有效lease；不得将该字段非空直接作为永久升级阻塞。仍需实际执行/子进程归属检查，不能仅凭UI候命或“没查到lease”抢占工作。
- 当前profile reload并非安全drain：改变忙profile时`applyProfileConfig`会shutdown整个进程，dispose可能终止目标child。禁止将修改profile文件等同于无副作用下线。

## 已冻结的最小实例合同

1. 默认共享service/root保持兼容。新增显式、严格校验的instance参数，独立APP_HOME和unit；非法slug、路径穿越、shell/systemd注入及跨实例/符号链接路径拒绝。
2. 每实例独立`.env`、profile、PID、日志、state/inbox/outbox、provider ledger、session map及本地执行workspace。不得复制默认实例的真实身份、secret、会话或任务数据。
3. 不只隔离unit名称：现有env/profile示例的共享绝对路径也必须按实例生成或保持明确未配置；不能沿用全局inbox fallback。
4. release payload与source/tree/hash证明、安装前验证、原子current切换及失败恢复仍保留。实例安装不覆盖默认unit/APP_HOME或其他实例。
5. 新实例默认不start、不注册、不创建平台身份；需完整有效配置后由运行Owner启动。systemd-only实例控制可接受，不允许退回通用pgrep/tmux控制其它实例。
6. instance和托管模式分离：实例ID是运维边界，不是新平台Agent身份。既有binding1用于local目标，既有binding15保留server/managed目标；其租赁/身份/ACL不因安装器改变。

## 实装顺序（尚未执行）

- 固定最终Client SHA/tree、版本和payload；共享server与独立local均使用同一已验证源码，但独立配置/持久根。
- 保存实际配置/当前release和恢复值，证明精确进程/任务归属。共享service升级影响范围必须包含其所有profile；未查明归属的子进程不触碰。只读current_task或界面标签不替代实际执行观察。
- 在可证明目标无在途工作、不会被新任务竞入的受控窗口内，由同一Owner移交binding1；不能让共享profile和新local实例同时注册同一身份。若现有机制不能完成安全移交，先修机制，不假报模式切换。
- 新local实例配置明确关闭managed hosting，使用自家接应路径；共享server实例仍承担既有managed hosting及binding15。不通过新租赁/新身份绕过既有目标。
- 逐实例核验运行PID/unit/root、安装摘要、认证register/presence及API能力交集。配置文件存在/静态校验PASS不等于就绪。
- Provider origin/model/Images合同及合法凭据引用仍需实际来源；Operator可自行冻结binding/epoch/policy。不伪造上游receipt，也不把缺配置当作实现实例隔离的阻塞。
- 最终执行AC17及其余AC/FD真实业务用例：两个模式分别生成、引用改图、预览/下载/保存及正式交付验收；不使用开发助手直接造图或同一共享process两个profile冒充。

## Owner自检范围

两个隔离实例/默认实例互不写入、非法参数、持久配置保留、失败不改current、payload闭合、unit选择和foreign PID拒绝。全部用隔离目录及stub控制面，不操作真实systemd或Provider。Main接收源码后仍需实际安装/运行证据，不能把这组测试当双模式产品验收。

## 2026-10-02 实际首次移交缺口

运行Owner有界只读核验：binding1无有效lease/子进程/local inbox，但有旧无lease running项及4条queued，不删除、不自动重放。共享service还包含OTHER_SCOPE profile；当前idle不等于已获维护custody，也不等于新任务不会进入。既有status投影、runtime-v1 revoke均不控制当前legacy WS；新注册只换HTTP auth映射，旧WS仍参与投递，不能先启动新实例冒充互斥。

**首次加载新Client控制不能依赖先重启整个共享进程。** 需要全profile明确维护custody及真实无在途窗口，或先部署API侧按owner/binding/runtime精确CAS的持久移交控制。后者还须修正初始close/block建议：已部署非managed Client在reconnect耗尽时全局shutdown(1)，关闭旧binding1连接会间接影响其它profile。不能靠延长timeout或只观察几分钟证明无影响。

API-first候选合同必须在同一精确scope内封锁旧runtime业务派发/领取/投影覆盖，同时可保持旧连接control heartbeat、禁止其争回新runtime；指定新runtime唯一接管，保留旧backlog及撤销/查询语义。旧socket恢复/重连、API重启、未知响应、并发派发与目标变更需有真实测试。该合同尚未被实现Owner确认，不当作已有能力，不先激活fence。API Owner正核实最小入口及首次部署可行性；若不可行，明确需要覆盖共享profile的维护custody，而非循环声称安装新control后即可安装。

只读证据和Main对close/block的反证：integration-evidence-20260928/profile-handoff-readiness-20261002。没有执行配置变更、进程信号或生产数据操作。

## 2026-10-02 后续收敛：不为此次迁移另建无人维护的接管平台

API Owner核对后纠正：1 running+4 queued属于服务端历史队列，旧Client本地inbox确为0，不能以“本地有5个旧任务”阻塞。新进程runtime ID仍每次随机，不能为了提前指定接管目标而永久复用process ID、弱化已有session/lease隔离。

持久API-side takeover至少涉及CAS表、owner接口、WS/HTTP公共fence、一次性目标接管证明，以及按服务端旧队列截止线隔离（不修改旧行、不redrive）。仅一轮接管若消耗proof后要求每次重启再人工CAS，会给日常运行引入新的人工依赖；不能作为已完成长期方案或为凑本次上线直接实施。现阶段不新增这套控制面，也不执行试验性线上fence。

当前最直接且可恢复的发布路径，仍需具备覆盖共享服务全部profiles的明确维护custody，再由Runtime Owner在真实无在途窗口完成一次停机状态下的配置分离及安装；OTHER_SCOPE lujunyi目前idle不产生该授权。图片Provider的实际HTTPS origin/model/Images凭据私有引用/生成编辑合同则是独立必要输入。Main会向用户仅索取这两项缺失事实，不重复索取已授权代码开发/常规发布许可。已完成源码与测试不再无意义重跑；全部34项产品验收仍NOT_RUN。

## 2026-10-02 绘图通道前置纠正

按用户新指令，不再将独立Images API的私有配置作为唯一发布前置；优先查既有Agent原生绘图工具。详见full-scope-release-gaps-20261002.md最新补充。共享服务OTHER_SCOPE维护归属仍独立保留，未因此获得进程操作权限。
