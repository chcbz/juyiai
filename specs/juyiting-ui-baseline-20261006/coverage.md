## 2026-10-16 全页样式/交互复核（当前权威结论）

**不是全量生产一致验收。** 已重新认证核对工作台与二级页，并补正式议事、私人议事、成果入口；公共议事、账户设置、正常成果及部分真实历史状态仍有缺口。完整逐页矩阵、修复、明确提案与未验范围以 `style-audit-20261016.md` 为准，下方历史“全量对齐”措辞不作为当前结论。

本轮原地修正输入框尺寸/颜色、恢复传话上下文与字数、地图导航字体、已有事项新话头的连续性提示；历史样式限制到组件作用域。保留用户确认的推荐承办、连续议事及框内录音提案，不改生产、不重做原型。Web页面风格已写入 `web/AGENTS.md` 第九章。测试及精确文件摘要见 `evidence/style-audit-20261016/final/`。

## 2026-10-16 话头记录组件同步（当前增量）

原型的“当前话头/已保存话头”旧分块已替换为现有HallConversationHistory列表：标题、更新时间（未知显示“时间未记”）、当前选中、逐行删除图标、含话头标题的删除确认、loading/error/empty及“再取旧话头”。样式复用现有组件，列表位于议事工具栏下；点击工具栏话头记录图标展开/收起，无额外关闭按钮。

切换保留稳定话头ID、消息、资料、草稿与结果，选中后列表保持展开；删除本地话头不删除事项/冻结结果。正式/私人/公共议事隔离；取消事项不可删除，录音时历史操作锁定、退出后恢复。新增话头记录错误字段独立于正式成果错误状态，避免互相影响。

依据：2026-10-16公开入口仍index-CIv_J8tq.js，组件JS/CSS摘要与前次一致；公开bundle中的组件与本地web HEAD `2c8d6703eead623f555029341101cb688b9d448a` 下HallConversationHistory.vue/ChatPanel.vue结构一致。见 `evidence/history-refresh-20261016/public-readback.json`。这不是认证后真实话头列表DOM核验，也不是完整部署版本证明；本轮不读取/删除生产话头。

当前定向检查：文档93项；话头记录12组/9布局；语音10组/18布局，PC1440/手机390及320，异常/外部请求0，SHA一致。证据 `evidence/history-refresh-20261016/final/`。主线12组/27布局在错误字段隔离前候选通过，保留在diagnostic/pre-error-isolation，不冒充最终精确源码回归；没有本轮全站或生产验收。下方旧报告只属于各自候选。

## 2026-10-16 语音输入位置调整（当前增量）

录音状态和转写预览移到同一输入框内部，替代普通输入区，不在下方另开区域。录音时显示状态/示意波形、取消和停止转写；转写可编辑，确认仅追加/替换草稿，仍需手动发送。取消恢复原草稿与焦点，空转写不覆盖草稿。正式、私人、公共议事共用，PC1440及手机390/320覆盖。仅界面演示，不启用麦克风。

当前定向检查：文档93项；Chromium语音10组/18布局，异常及外部请求0，源码SHA一致，证据 `evidence/voice-inline-20261016/final/`。没有重跑全站或进行生产发布；下方旧报告仅属于相应旧候选，生产对齐未核实边界不变。

## 2026-10-16 复查纠正：事项内容与对齐边界（当前）

不能把“19页布局检查通过”视为“19页全部与生产一一对齐”。用户复查发现默认从首页进入事项没有内容：此前初始化只给议事/详情提供示例，列表又删掉其余快照卡，最终隐藏唯一空卡。已通过真实浏览器复现，不是旧revision参数导致的不同版本，也不是用户操作问题。原有全页报告只能证明当时所列布局断言通过，不能证明默认列表内容验收。

本次在原型原地补齐3个脱敏示例（待点将、已点将待开工、已完成），使用既有事项卡结构。列表浏览不创建用户事项、不自动发送；可以查榜号/标题、按本领和状态筛选、清除无结果筛选、打开各自详情/成果再返回。用户在原型新建的事项也保留在列表里，切换与再新建不丢原对话、结果或未发草稿；未完成回复期间不切换活动上下文。已有空会话无需reset即可补出示例，明确empty场景仍为空态。

**仍未证明全量生产实页对齐**：议事/私人议事/公共议事/正式成果页本轮未进入线上逐页核验，仍按源码结构及用户确认的流程提案；个人中心保留不可用边界。逐页来源矩阵见coverage.md。仅离线原型，无生产变更。

本次证据 `evidence/tasks-content-20261016/`；`repro/` 为修复前复现，`final/` 为修复后定向检查。下方all-pages报告属于本次修复前候选，不冒充当前精确源码的全量验收。`revision`仅是预览标识，不是独立版本路由。

# 全量页面原地更新 · 2026-10-16（当前候选）

现有原型 **19页全部更新，PC1440 / 手机390及320同步覆盖**，没有另建应用。入口仍是 `index.html#home`，完整页面入口为 `pages.html`。本节取代下方历史章节中的“当前/最新”标识；历史报告仅属于对应旧候选。

保留生产导航、返回/关闭、浮层与内部滚动。主线不变：**填写需求 → 开始办事 → 系统推荐承办Agent → 确认或另选 → 同一议事澄清、展示结果、多轮修改**。首页不选承办，不设置“直接交办/先聊一聊”分支。

来源分为认证实页、源码结构、明确提案，不能将19页原型覆盖说成19页均完成生产认证核验。个人中心按生产不可用边界禁用；厅中实景为静态可点击背景而非游戏引擎；新版本上传等未实现操作明确禁用。消息、推荐、资料上传、回复和读书笔记只使用本地fixture/浏览器存储，不写真实账号。

当前证据：`evidence/all-pages-refresh-20261016/final/`（相对规格目录）。检查范围与逐页依据见 `coverage.md`，报告摘要见 `acceptance.md`。只完成交互原型，不代表生产修复、正式构建、发布或真实办理成功。

## 19页依据及更新范围

“本轮实页”指本轮认证只读PC1440/手机390截图；“前轮实页”指 `authenticated-refresh-20261016`；“源码”不等于线上验证。失败跳转截图放在 `failed-navigation/`，不计覆盖。

| 页面 | 依据 | 本轮更新/保留 |
|---|---|---|
| P01 首页 home | 前轮实页＋流程提案 | 生产主导航、首页入口、继续议事；无承办选择 |
| P02 事项 tasks | 前轮实页 | 查榜号/能力/状态筛选、刷新、详情返回 |
| P03 提出需求 create | 前轮实页＋流程提案 | 返回/关闭浮层、草稿和资料保留 |
| P04 好汉 agents | 前轮实页、本轮错误态＋源码 | 生产名册、筛选、头像/能力详情、私聊入口 |
| P05 详情 detail | 前轮未交办实页＋源码/提案 | 办理建议内推荐确认/另选、状态操作 |
| P06 议事 chat | 源码＋连续议事提案 | 同一对话澄清、资料、结果、修改；统一弹层 |
| P07 私人议事 private | 源码（本轮线上未进入） | 私聊上下文、输入/材料取消保留、返回 |
| P08 公共议事 public | 源码（本轮线上未进入） | 公共上下文及统一输入区/弹层 |
| P09 资料 workspace | 前轮实页＋源码 | 分类、搜索、查看、本地示例上传 |
| P10 我的 mine | 本轮实页 | 五类入口、帮助、个人中心不可用状态 |
| P11 典籍阁 library | 本轮书架/检索实页 | 封面、分类、检索、打开阅读、引用 |
| P12 消息 messages | 本轮实页＋本地状态 | 需我处理、刷新和空态、回原事项 |
| P13 招贤令 catalog | 本轮实页＋源码 | 概览、人物卡、保留Runtime示例边界 |
| P14 厅中实景 map | 本轮实页＋现有生产背景素材 | 全屏静态背景、工具条、热点、返回 |
| P15 资料详情 file | 本轮实页（内容遮罩）＋源码 | 预览/管理切换、版本、下载、重命名/回收、引用 |
| P16 阅读器 reader | 本轮实页＋源码 | 章节、书签、桌面笔记/手机折叠笔记、引用 |
| P17 帮助 help | 本轮实页结构＋流程提案 | 四步连续流程指引、前后步/稍后 |
| P18 个人中心 account | 本轮我的入口不可用＋显式边界 | 禁用设置，不伪造已接通账号功能 |
| P19 正式成果 results | 源码（本轮未做线上验收） | 现有成果/验收及终态保留，非新流程必经页 |

共用材料选择、预览、历史、语音设置等弹层同步更新。个人/公共/事项议事保持上下文隔离，不因共用外观合并数据。无生产发送、交办、上传、阅读进度保存、执行、扣费或部署；只读守卫拦截写请求（名册POST为源码确认的只读查询）。

---

## 历史记录（以下不是当前验收）

> **2026-10-16 当前补充**：登录阻塞已解除。认证只读核对首页/事项/未交办详情/提出需求/资料/我的/好汉的PC1440及手机390；原型在原入口修正导航、需求弹层、生产分类。用户确认的推荐承办与连续议事仍为提案，不称生产功能。当前检查见 `evidence/authenticated-refresh-20261016/final/`；此前候选结果仅为历史。未核验全部生产二级页，未发送生产需求或部署。

## 当前局部候选：连续议事（2026-10-16）

- P01/P03：首页与表单不选 Agent；开始办事后推荐承办，确认或另选后进入议事。无“直接交办/先聊一聊”模式选择。
- P06：处理状态、澄清、补资料、成果卡片、预览下载、引用修改、多轮版本均在同一对话。
- P01/P02 返回同一议事；刷新不重发；发送失败/未知保留输入，不自动重跑。
- 仅离线交互设计。固定候选与检查：`evidence/conversation-continuity-20261016/`。此前双起点候选已被用户否定，不再有效。
- 未覆盖历史场景继续使用下方原基线，不代表产品执行链路已修复。


## 2026-10-13 控件反馈修订

P02 在页内标题右侧统一“提出需求”（空/非空、桌面/手机），搜索与刷新独占一行，能力/状态下移；P09 去旧渐变hover，保留主按钮/选中分类层级和键盘可见焦点。仅离线提案，不改业务契约。根基线 `5db58c2d17dfbab868f6e550f84d6a4ed8c48203` + 本地文件，输入SHA和证据见 `evidence/ui-feedback-20261013/`；下方简化轮的空态创建与搜索三列描述由本节更新。

---

## 当前增量：界面简化候选（2026-10-13）

P01 首页收敛为需求与当前事项列表；P02 四组筛选 + 10种细状态与搜索交集；P05 按沟通、办理、验收、未知、终态突出唯一主操作。范围为离线设计，不是对应产品源码已实现。原值与新证据在 `evidence/ui-simplify-20261013/`，原源码同步和历史覆盖在下方保留。来源为根 `77bd860c3660763911dc79bce7a3278420a5e2b2` 加此前未提交原型，受测输入以报告 SHA 为准。

---

# 当前增量覆盖 · 2026-10-13

源码 `cb730681`，仅本轮列明切片；原外壳与历史覆盖保留下方，不代表整站最新或线上验收。

| 编号 | 本轮覆盖 | 入口 |
|---|---|---|
| P19 | 正式成果独立页；无页面工作空间入口 | [打开](prototype/index.html?reset=1&scenario=results#results) |
| S16 | 未开工事项取消确认/保留，成功后只读 | [打开](prototype/index.html?reset=1&scenario=cancel-ready#detail) |
| S17 | 取消未知：保留原事项，只核对不重提 | [打开](prototype/index.html?reset=1&scenario=cancel-unknown#detail) |
| S18 | 已取消历史成果，两类重读/示例下载 | [打开](prototype/index.html?reset=1&scenario=cancelled#results) |
| S19 | 历史读取失败不伪报恢复、不重跑 | [打开](prototype/index.html?reset=1&scenario=history-error#results) |
| S20 | Runtime 首次接入/脱敏 handoff/单次登记示意 | [打开](prototype/index.html?reset=1&scenario=runtime-ready#catalog) |
| S21 | 已有安装仅查询，不重复登记 | [打开](prototype/index.html?reset=1&scenario=runtime-existing#catalog) |
| S22 | 登记未知只查询同一安装，不自动注册 | [打开](prototype/index.html?reset=1&scenario=runtime-unknown#catalog) |
| S23 | 材料不匹配或过期拒绝登记（固定失败示例） | [打开](prototype/index.html?reset=1&scenario=runtime-invalid#catalog) |

P03 替换旧任务榜内嵌表单为 HallDraftEditor 独立私人草稿；覆盖保存、确认交办、选人后重存/授权、刷新原回执及不修改正式事项。P02 同步单行搜索/本领/44px 刷新按钮，移除榜内重复创建入口；P04 点将/密议按钮排列保留；P05/P15/P19 纳入新交互。运行时状态仅本地 fixture，PENDING/ACTIVE 不等于在线。取消仅可用于明确未开始的无资金示例，不能推导真实服务端授权/幂等已验收。

---

# 页面与状态覆盖 · 交互补全 2026-10-07

唯一主入口：[优化界面原型](prototype/index.html#home)。[可点击索引](prototype/pages.html) · [交互说明](interaction-guide-20261007.md)。覆盖只表示离线交互，不代表产品上线或真实业务闭环通过。

## 页面 P01–P18

| 编号与名称 | 交互范围 | 入口 |
|---|---|---|
| P01 · 办事 | 快速需求、资料选择、最近事项 | [打开](prototype/index.html?reset=1&scenario=ready#home) |
| P02 · 事项 | 状态筛选、空列表、事项入口 | [打开](prototype/index.html?reset=1&scenario=ready#tasks) |
| P03 · 提出需求 | 正文/附件-only、成功清空、失败保留 | [打开](prototype/index.html?reset=1&scenario=ready#create) |
| P04 · 点将册 | 选择好汉、点将、密议、招贤令 | [打开](prototype/index.html?reset=1&scenario=ready#agents) |
| P05 · 事项详情 | 资料、进展、回议事、正式验收 | [打开](prototype/index.html?reset=1&scenario=ready#detail) |
| P06 · 榜文议事 | 需求、补充、多媒体、稿件引用 | [打开](prototype/index.html?reset=1&scenario=results#chat) |
| P07 · 密议 | 每位好汉独立话头与草稿 | [打开](prototype/index.html?reset=1&scenario=ready#private) |
| P08 · 厅前公议 | 与正式事项、密议隔离 | [打开](prototype/index.html?reset=1&scenario=ready#public) |
| P09 · 资料/百宝箱 | 分类、可选保存、回收站、再引用 | [打开](prototype/index.html?reset=1&scenario=ready#workspace) |
| P10 · 资料详情 | 预览、下载、重命名、回收/恢复 | [打开](prototype/index.html?reset=1&scenario=ready#file) |
| P11 · 我的 | 原有次级入口、全部入口 | [打开](prototype/index.html?reset=1&scenario=ready#mine) |
| P12 · 典籍阁 | 书架、案卷检索、结果/空态 | [打开](prototype/index.html?reset=1&scenario=ready#library) |
| P13 · 阅读器 | 目录、章节、书签、手札 | [打开](prototype/index.html?reset=1&scenario=ready#reader) |
| P14 · 消息 | 待处理事项、草稿与空态 | [打开](prototype/index.html?reset=1&scenario=ready#messages) |
| P15 · 招贤令 | 好汉与接入/安顿边界 | [打开](prototype/index.html?reset=1&scenario=ready#catalog) |
| P16 · 厅中实景 | 原美术与功能入口、静态地图 | [打开](prototype/index.html?reset=1&scenario=ready#map) |
| P17 · 使用帮助 | 当前最短流程及页面索引 | [打开](prototype/index.html?reset=1&scenario=ready#help) |
| P18 · 个人中心入口 | 保留外部账号模块边界 | [打开](prototype/index.html?reset=1&scenario=ready#account) |

## 状态 S01–S15

| 编号与名称 | 交互范围 | 入口 |
|---|---|---|
| S01 · 可输入 | 最新工具栏与输入框 | [打开](prototype/index.html?reset=1&scenario=ready#chat) |
| S02 · 空话头 | 空消息与可编辑输入 | [打开](prototype/index.html?reset=1&scenario=empty#chat) |
| S03 · 等待回复 | 禁重复发送与操作 | [打开](prototype/index.html?reset=1&scenario=waiting#chat) |
| S04 · 流式示意 | 回话未尽，不运行真实SSE | [打开](prototype/index.html?reset=1&scenario=streaming#chat) |
| S05 · 读取失败 | 重试只读原话头，不重发 | [打开](prototype/index.html?reset=1&scenario=error#chat) |
| S06 · 录音示意 | 停止、取消，不启用麦克风 | [打开](prototype/index.html?reset=1&scenario=recording#chat) |
| S07 · 转写待确认 | 追加/替换/丢弃，不自动发送 | [打开](prototype/index.html?reset=1&scenario=voice-review#chat) |
| S08 · 多媒体成果 | 预览下载、保存可选、引用修改 | [打开](prototype/index.html?reset=1&scenario=results#chat) |
| S09 · 已完成 | 只读成果，不再验收或改稿 | [打开](prototype/index.html?reset=1&scenario=completed#detail) |
| S10 · 创建失败 | 保留草稿与资料，返回修改 | [打开](prototype/index.html?reset=1&scenario=create-failure#home) |
| S11 · 创建未知 | 核对状态，不重复创建 | [打开](prototype/index.html?reset=1&scenario=create-unknown#home) |
| S12 · 发送未明确受理 | 创建点将后发送补充，保留输入 | [打开](prototype/index.html?reset=1&scenario=reply-failure#home) |
| S13 · 验收状态未知 | 创建点将后验收，查询原操作 | [打开](prototype/index.html?reset=1&scenario=accept-unknown#home) |
| S14 · 验收失败 | 冻结成果保留，不伪报成功 | [打开](prototype/index.html?reset=1&scenario=accept-failure#home) |
| S15 · 独立root阻塞 | 来源关联待实现，不能确认验收 | [打开](prototype/index.html?reset=1&scenario=independent-roots#home) |

## 验证与边界

真实 Chromium 检查桌面1440、手机390及窄屏320布局、原生点击、示例下载与音频播放；报告见 [acceptance.md](acceptance.md)。并非真机、生产应用或线上视觉采样。固定源码来源和历史美术不改。

不模拟真实 Agent/Provider、SSE、支付、数据库、权限、麦克风、系统键盘、完整账号模块、实时地图、真实书库。独立图文 root 长期关联恢复 R01 仍待实现；相关验收被明确阻塞，不能由示例成功替代。

## 2026-10-16 生产外观重新对齐
线上公开 CSS 已读取并复用；PC侧栏、移动底部导航与二级返回路径按当前源码/用户生产截图修正。推荐位于已有事项详情内，不另起弹窗。登录后的当前生产DOM未核对，旧快照及补充样例不标为线上实测。证据：evidence/production-refresh-20261016/。


## 2026-10-16 资料必要修复局部同步

现行资料详情新增按需100+2历史版本演示、字符串版本选择、部分预览提示与提交成功后详情读取失败/只读重试。保留旧导航和风格；交互为离线fixture，不是真实写入。PC1440/手机390/320定向Chromium检查3组/3布局通过、异常和外部请求均0，93项文档检查通过；其余页面未重新全量截图。证据：`/home/isp/wsps/cyf/docs/implementation/evidence/workspace-management-audit-20261016/essential-repair/prototype/`。

## 2026-10-17 点将册技能/本领增量（待审核）

入口仍为prototype/index.html#agents。新增技能安装/运行两状态、本领分区及当前详情刷新；保留密议和条件点将。7种目录/权限/失败示例均离线模拟，既有业务流程和派单规则不改。仅原型，不是生产功能；证据evidence/agent-skill-display-20261017/。

### 点将册布局审核补充（2026-10-17）

手机≤720px改为名册→详情，详情顶部返回名册，底部密议/条件点将常驻，中间内容独立滚动；桌面加宽详情区并固定卡片操作区。替代此前名册/详情上下堆叠规则。保留筛选、选中、返回和原业务条件。仅原型；证据evidence/agent-roster-layout-20261017/final。
