# 议事、执行与成果：现状及最小优化建议

核对日期：2026-11-01。Owner：当前会话。状态：分析建议，未作为批准实施规格；本轮无产品代码修改、构建、部署或业务写操作。

## 1. 范围与证据

目标：按现有原型梳理议事→执行→成果→修改→验收→归档。非目标：推荐、岗位、多会话、性能/OOM和技能管理重设计。

固定源码（按安装记录取源码，不使用较旧且有未提交内容的工作区替代）：

- Web：`7b44dec7665d1e32bf02de119043e20fd55cbf58`，1.16.86，Flow4403172/394；主机记录 online_verified。
- API：`efcb87549d332c5bfd5b18507b2524360d241263`，Flow5260799/424；主机记录 installed，不等于本轮业务验收。
- Runtime：发布历史1.3.31，`dedf9c75734b719bd262d7e84b88f49bcc11b141`，Flow5264702/114。本轮核对该版本源码，未新做运行进程/业务验收。
- 主机记录：`/home/isp/state/cyf-web-flow/record.json`、`/home/isp/state/cyf-api-flow/record.json`；Runtime历史：`/home/isp/apps/cyf-agent-runtime-v1/RELEASES.md`。
- 原型目标：`/home/isp/wsps/cyf/web/prototypes/juyiting/specs/prototype-spec.md` C07/C08/C10；离线原型不证明生产实现。
- 历史浏览器报告：`/home/isp/wsps/cyf/specs/juyiting-unified-experience/business-discussion-test-results-20261031.md`，受测Web1.16.81。12通过/5失败/18阻塞/1未执行/1延期是历史结果，不能当作本次版本结果。

## 2. 核心结论

不是缺少完整流程，而是同一轮的内部消息、结构化答复、执行请求、成果和正式交付被分别展示；状态含义和用户操作边界又没有充分分开。当前已有聚合与统一验收实现，应补齐而非重建。

三个边界必须保留：
1. 聊天答复结束 ≠ 执行完成。
2. 文件生成/登记 ≠ 正式提交，更不等于用户验收。
3. 归档 ≠ 删除成果，也不自动验收。

## 3. 当前链路

```text
用户在原事项议事中发送需求/资料
  → API受理并绑定事项、会话、承办及固定资料版本
  → Runtime完成CHAT回合，返回正文及结构化意图
      ├─ 普通答复：保存消息，结束这次答复
      ├─ 澄清：保存问题，等待关联的用户补充
      ├─ 执行：API生成并派发关联执行请求
      │    → Runtime/工具处理资料、生成候选成果
      │    → 成果上传/登记取得服务端权威事实
      │    → Web在关联回复展示可用成果
      ├─ 修改：绑定旧成果/正式交付，按明确修改意图继续处理
      └─ 正式交付：API固定交付集合，提交为待验收，不自动接受
  → 用户打开统一验收窗，预览并选择固定成果版本
  → 用户确认：必要时先正式提交所选集合，再验收该精确集合
  → API确认事项完成
  → 历史只读；归档后仍应能查看成果和验收记录
```

并非每次对话都执行、生成文件或正式交付。纯文字交付也有固定消息来源；普通闲聊不能全部当成果。Runtime的 artifact_stage/result_propose 是候选冻结/选择，不是业务完成凭证。

当前两条交付入口可以共存：Agent明确交付意图触发后台提交；用户选中成果确认验收时，若没有匹配正式批次则先提交再验收。后者不是未经同意自动验收，也不需要给用户增加两个重复确认框。

### 答复为何重复、何时出现

Runtime输出正文text及同一份结构化意图；API最终校验要求消息content与outcome.text一致，并关联同一个assistantMessageId保存。Web先展示流式/最终正文，再根据结构化投影渲染“议事答复”卡，卡中又展示outcome.text。澄清卡还单列question，因此可能再次重复。

这段重复不是两个独立模型答复；卡片晚出现可来自最终结果到达/投影加载。具体截图每块的精确生成时刻仍需对应requestId/messageId及事件时间，不能凭视觉顺序编造时间。执行子请求则确实可能是后续独立执行，但应在同一逻辑轮内呈现。

## 4. 主要问题与建议

| 项目 | 核对到的现状 | 最小建议与责任层 |
| --- | --- | --- |
| 答复重复 | ChatPanel同时渲染content与typed卡；卡再次展示text | Web只保留一次正文；结构化结果驱动问题/进度/成果操作，不再复制正文 |
| 聚合不完整 | hallDiscussionTurns已有ACTION_REQUEST父子聚合，但仅部分精确关联且有parts的子消息被收拢 | 扩展现有展示投影，使用任务/会话/消息/请求关联；不按相似文本去重，不合并底层执行记录 |
| 状态误导 | request COMPLETED/FINAL_PERSISTED/PUBLISHED映射“已完成”，经connectionStatus进入页头；关联执行另有状态 | 页头只表达事项状态；本轮回复表达执行状态；正常连接不占主要状态位；API权威事项完成才显示“事项已完成” |
| 区域过多 | 状态栏、typed恢复提示、本轮成果选择、技能结果、轮次操作分散；inline成果组件仍可能展示原始结构化data | 正常过程收进对应回复；失败/未知保留就地恢复；技术data不作为默认面向用户的成果卡 |
| 普通提问被成果选择阻塞 | submit在普通CHAT发送前遇到多份独立成果就要求选择“本轮成果”，并可能因成果读取不全禁止发送 | 普通问答不必选成果；明确修改/提交才绑定对象，歧义就澄清。Web主改，核对API可选parent及实际消费者；不删除后端歧义保护 |
| 澄清操作不自然 | 点击“回答此问”才绑定pendingQuestion；直接输入走普通DISCUSSION | 同一输入框加紧凑“正在回答…”标记，可取消；若自动关联唯一问题，须回归话题转移，不能无条件绑定 |
| 参考资料与成果混淆 | 资料范围、成果上下文、正式验收集合是不同来源 | 资料入口只管理本轮输入；成果卡表示输出；验收窗固定采用版本，不让用户理解内部ID |
| 阅读历史被拉底 | ChatPanel深度监听messages后无条件scrollTop=scrollHeight | Web仅在用户接近底部时跟随；阅读历史显示新消息提示，历史加载不抢位置 |
| 停止语义混淆 | 已有停止答复和“放弃本轮未交付结果”两种操作 | 保留区别，后者默认折叠；不承诺撤销费用/停止服务商，不自动重放未知执行 |
| 归档成果显示矛盾 | 详情只对completed传completed=true；数量取currentDelivery，无当前批次可显示0，并写“当前尚无正式成果” | Web区分当前待验收与历史已验收；复用正式记录读取。不能用当前批次为空推断历史无成果；若API读模型缺事实才改API |

黄色处理区不是所有事项固定存在：现有多媒体展示函数按能力、请求与PLANNING/EXECUTE等条件产生。正常进度可移入本轮回复，但不能一概删除真实失败/未知/恢复提示。

## 5. 推荐的页面形态（遵从原型，不新增大区域）

```text
事项名称 · 承办人 · 事项状态              [成果与验收] [更多]

你：请根据这份资料整理会议纪要。
吴用：正在整理资料…                    ← 低强调，原位更新
完成后：已整理，重点如下……
        [会议纪要 · 第1版   预览 / 验收此版]

你：保留第一部分，把第二部分改短。
吴用：已修改第二部分。
        [会议纪要 · 第2版   预览 / 验收此版]

[＋资料]  输入需求、追问或修改要求              [语音] [发送]
```

- 一个用户回合在视觉上对应一组答复、必要状态和成果，而非强行只存一条消息。
- 无成果的正常问答不出现空成果区域；真实追问不能被去重隐藏。
- 沿用顶部统一验收入口，卡片“验收此版”只是预选并打开同一弹窗；打开/关闭不写验收决定。
- 不新增独立“议事成果”栏、固定待验收横幅或“引用修改”按钮。按既定原型，议事文件卡提供预览/验收；下载仍在资料管理等既有位置。
- 修改目标明确就继续原议事；多份独立成果且指代不明时才澄清。不默认用最新文件覆盖全部成果。
- 修改某一成果时保留其他成果；旧版本和已验收版本可追溯，不靠标题或时间判断版本关系。
- 已完成/归档保持只读，展示验收的是哪些固定版本；普通输入、验收入口按权威状态收起。

## 6. 功能链风险：与纯展示修复分开

10月31日浏览器发现五项问题：资料范围被遮挡、PDF可预览但Agent称未收到附件、生成文件名/预览不正确、停止后的部分正文重进丢失、归档详情错误显示无正式成果。这些是旧版本实测，当前源码分析不能代替新版复测。

最早定向验证及责任归属：

1. 资料范围遮挡：Web布局；普通用户可见点击三种范围并实际发送。
2. PDF上下文：沿固定fileId/version核对Web提交→API资料绑定→Runtime输入文件→工具/模型读取；只修第一个真实丢失边界。浏览器能预览不证明Runtime拿到了文件，不能直接归因于PDF解析类。
3. 文件预览：核对成果真实文件、文件名、MIME、登记元数据及预览分派；区分生成/适配/展示问题，不给未知文件强行伪造类型。
4. 停止后重进：对照取消回执、流式部分文本是否持久化、历史读取及前端恢复；确定责任层再改，不把新问题能答当作整条通过。
5. 归档：固定已验收交付集合对照详情/记录/预览；现有Web分支已能解释误导风险，没有证据证明成果被删除。

## 7. 实施边界与顺序建议

### 第一批：Web展示收口

复用ChatPanel、BountyTypedOutcomeCard、hallDiscussionTurns、BountyDiscussionPanel、BountyExecutionOutputs、hallDeliberationState、HallTaskResources/BountyPanel。去重复、区分状态、收拢本轮、正确滚动和历史空态。契约不变，不默认改API/Runtime。

### 第二批：让真实操作顺畅

调整useHallTypedDeliberation的普通问答与成果修改绑定；保留明确问题与修改来源。针对上一节五项历史问题定向复测，再按真实边界修复。资料读取/执行/登记问题可能需要API或Runtime，不能承诺全靠样式解决。

### 第三批：验完整闭环

用同一事项完成：补资料→澄清→执行→预览→修改→选择版本验收→归档→重进。普通问答、纯文字成果、文件成果各验证；本人Agent与他人吴用覆盖同一主线。严格零自有Agent场景仍需合适账号样本，不能用既有账号跨用户操作冒充。

不新增事项/话头表，不启用多会话，不重写执行状态机，不新增审批/开关；不修改推荐。职责遵守RB-1与接口标准：API权威业务事实，Runtime执行/文件适配，Web负责展示与交互；只对真实契约变化联动消费者。

## 8. 本范围最低回归清单

| 场景 | 通过标准 |
| --- | --- |
| 连续普通追问 | 正文各显示一次，上下文连续，不误触发执行/验收 |
| 澄清后补充、转移话题 | 同一输入完成回答，绑定正确；无关问答不错误关闭问题 |
| 上传/选择/取消资料 | 不自动发送，草稿保留；范围控件可用且发送内容符合选择 |
| PDF/图片带资料提问 | Agent能回答文件内可核对事实，不止验证预览 |
| 文字/文件执行 | 本轮进度原位更新，未登记不宣称可验收；成果可读 |
| 多份成果后普通提问 | 不强迫选择修改目标；有歧义的修改才要求明确 |
| 指定版本修改 | 改动正确对象，未修改成果保留，历史可查 |
| 阅读历史时流式回复 | 不强制拉底，返回底部后继续跟随 |
| 停止答复后重进/继续 | 停止结果及应保留正文一致，后续正常发送 |
| 查看/取消/确认验收 | 打开取消不写决定；确认固定集合成功才事项完成 |
| 完成/归档后重进 | 只读且成果、版本、验收记录一致，不出现假空态 |
| 手机窄屏 | 输入/资料/预览/验收可达、弹层可关闭；真机键盘另实测 |

本轮为源码与既有证据分析，以上不是本轮测试通过清单。

## 9. 关键源码索引

以下路径均为上述固定commit中的文件；当前工作区可能较旧，不应直接按本地内容视为线上代码。

- Web：`/home/isp/wsps/cyf/web/src/components/juyiting/ChatPanel.vue`、`BountyTypedOutcomeCard.vue`、`BountyDiscussionPanel.vue`、`BountyExecutionOutputs.vue`、`BountyExecutionTermination.vue`、`HallTaskResources.vue`、`BountyPanel.vue`（后六文件同目录）。
- Web组合逻辑：`/home/isp/wsps/cyf/web/src/composables/juyiting/hallDiscussionTurns.js`、`hallDeliberationState.js`、`useHallConversation.js`、`useHallTypedDeliberation.js`、`useHallSelectedOutputReview.js`、`useHallBountyFinalization.js`（同目录）。
- API：`/home/isp/wsps/cyf/api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatDeliberationService.java`、`ChatActionFinalService.java`、`ChatDeliverySubmissionService.java`、`ChatDeliveryRevisionService.java`、`ChatSelectedOutputFinalizationService.java`（同目录）。
- Runtime：`/home/isp/wsps/chcbz/isp-install/conf/codex-bridge/action-chat-final.mjs`、`native-execution.mjs`、`native-artifact-session.mjs`（同目录）。

## 2026-11-02 浏览器复测后的修复契约（候选，尚未发布）

事实与证据统一见 `/home/isp/wsps/cyf/docs/implementation/handoffs/DISCUSSION-RETEST-20261102.md`。原源码分析不再直接当作线上缺陷：两文件同批次生成后普通提问本次成功；单文件修改触发澄清，选择追加后执行FAILED，后者仍待定位。

- **正文去重**：相同的消息正文/typed答复只显示一次；不同文本仍保留。澄清问题、操作按钮、执行状态和失败提示不因去重移除。事项状态与单轮回话状态分开。
- **资料与阅读**：资料范围置于弹框独立网格行，PC/移动端均可点击；阅读旧消息时不自动拉底，提供小型“查看新消息”入口，不新增面板。归档事项不以当前待验收批次为空推断历史成果为零。
- **文件名称**：复用已提交输出的 `original_filename`。会话实时part/历史part的既有`filename`填入真实名称；`GET /chat/requests/{requestId}/steps/{stepId}/outputs`增加可选展示字段`filename`（缺失/空仍按旧客户端回退）。Web验收选择列表优先用文件名。文件名不参与来源身份、选择摘要或验收幂等，不从Prompt猜测、不改原文件、不新增表。历史查询按现有asset对应的同scope/execution/output/hash关联读取名称；缺失时保留历史part而不伪造名称。
- **文件预览**：复用已授权asset读取。按服务端MIME展示text/plain、text/markdown、application/json的纯文本以及application/pdf；文本不可执行HTML，其他格式不由扩展名猜测。预览失败不改变成果/验收状态。PDF前端预览与Agent实际读取PDF是两个问题，不能用前者通过替代后者。
- **停止回复的历史保留**：API在既有会话/turn锁和取消事务中，将该turn已持久化的delta按顺序合为一条普通历史消息，metadata增加`partial:true,completionState:"CANCELLED"`。没有正文则不造空消息；重复取消不重复写入。不得设置finalMessageId/finalDigest、创建typed完成事实或正式成果。Web刷新后显示“已停止（未完成）”。既有事件保留，不迁表、不批量补写历史停止记录；旧记录的只读重建尚未实施。
- **职责与联动**：Web负责去重、布局和展示；API负责输出名称投影、停止事务/幂等。Runtime本轮尚未修改。PDF载体声明为空、追加执行FAILED与停止后的503分别核对，不靠前端隐藏或自动重放处理。
- **必要验证**：API补目录filename HTTP契约、历史名称投影及取消幂等/非final测试，重型测试待Flow；Web定向组件/消息测试与资料弹框真实浏览器几何验证分开记录。没有正式Flow/安装证据前不能称为上线或全链验收通过。

### 2026-11-02 接续：预览交付与验收分离

真实事项575的追加文件执行已写出并暂存roles-v2.txt，但没有result_propose；已完成的模型回合最后称“staged for preview only; did not submit it for acceptance”，bridge因此按缺少提案失败。修正通用执行指令与工具说明：预览候选同样需要artifact_stage→result_propose，后者不是用户验收、付款或归档，不自动推断/补写缺失提案，不重放失败执行。责任RB-03/04/07，无新增wire/表/开关。候选模拟24测试通过，尚未正式Flow或实测修复后的模型行为。

新验收标题从已有已验证目录filename取得，来源身份request/step/output/hash不变；旧已验收标题不回写，历史显示仍待只读投影处理。对应轻量选择验收测试10通过，非正式发布证据。

### 2026-11-02 历史验收名称投影补充（候选，非线上结论）

已完成/归档记录只读使用已有CONVERSATION_OUTPUT来源：以requestId、stepId、outputId、contentHash匹配原目录filename；匹配不到则保留正式成果标题（技术outputId回退“成果 N”）。复用既有授权GET和HTTP身份生命周期，切换身份/事项清空名称及中止请求。读取名称失败不删除验收行、不影响原正式预览、不自动重放或改写验收历史。新验收仍按前述目录filename提交展示标题。Web候选6cad1f9，轻量16测试通过；正式及线上结果见handoff。


## 2026-11-02 08:36线上复测补充

本轮Web400/API425/Runtime115已安装；源码与安装绑定、真实浏览器通过及未通过项见`docs/implementation/handoffs/DISCUSSION-RETEST-20261102.md`。已验证归档空态、历史技术名称回退、固定正文预览及PC/移动资料选择。新事项576原生预览执行FAILED（TURN_INTERRUPTED，工具记录ENOENT，根因未确认），567继续发送实测503，阻塞后续业务闭环；不得将正式测试通过或通道ready等同端到端通过。取消部分正文持久化和追加/验收/归档仍未完成新版本实测；PDF输入未修。
