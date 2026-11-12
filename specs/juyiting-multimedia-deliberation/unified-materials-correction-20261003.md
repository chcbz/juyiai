# 通用资料与多媒体协作：产品纠偏及详设增量 v3

> **2026-10-03 最新实施指令**：用户明确“无需做太多兼容补丁，一切都按新方案实施”。新入口、新请求统一走通用资料与按需议事；不新增旧生图入口、双轨产品流程或回退适配工程。只保留身份隔离、幂等、未完成请求及既有内容保护，不以历史兼容覆盖率阻塞新方案。

日期：2026-10-03。依据：用户明确要求“参考图就是资料的一种，不应该单独出来”，并要求主控同步修正方案、详设、开发与验收。

**本增量是当前产品范围与实施优先级（文档v3不是runtime wire协议版本升级）。不是功能已实现，也不是新的发布回执。** 与早期“参考图入口”“先打通画鸟再补资料”的产品安排冲突时，以本增量为准。历史冻结 wire/fixture 保留原始内容和版本，不追改旧证据；通用合同必须单独版本化。特性名称仍为 `juyiting-multimedia-deliberation`（聚义厅多媒体悬赏议事与工作空间闭环），不另建生图产品。

## 1. 必须交付的用户流程

1. 提需求只有一个 **添加资料（可选）** 入口，从同一个工作空间选图片、文档、音频及平台已支持的普通文件；允许混选与空选。不得保留并列的“参考图”按钮或伪装为通用入口的图片白名单。
2. 所选资料统一附件卡展示名称、类型、精确版本及可用操作；可预览、播放/查看、移除。不能直接预览的格式显示明确限制并允许授权下载，不伪造预览。草稿移除只解除本次选择，不删除工作空间原件。
3. 点将时显式固定目标 Agent、需求版本及整份资料目录；可靠地自动新增/复用该任务的悬赏议事，送入需求原文与资料关联。用户无需再选“生图模式”或逐项确定技术 INPUT/REFERENCE。
4. Agent 根据需求及资料判断答复、按需查阅、澄清或执行。信息充分且能力/既有授权满足时直接办理；不为了兼容 fast 强制走一轮聊天，也不把有图片等同于生成图片。
5. 后续在同一议事输入框继续发文字、添加资料或引用上一稿；可补文档/音频，不能退回事项详情再重新点将才能补充。每条新消息有独立、明确的新业务意图；看进度、刷新及断线恢复不重执行。
6. 统一实时呈现文本、图片、音频和文件；支持预览/播放、下载、可选保存工作空间。选定最终精确内容集合后正式交付、验收、完成需求；个人归档不是交付前置。

参考图是本次任务中一份资料的**用途**，不是文件类别、独立存储域或第二入口。画鸟只是一项端到端用例，不能替代文档整理、音频资料处理和混合资料协作。

## 2. 纠偏开始时的具体偏差（历史核对；实施进度见末节）

- Web `HallOverview.vue` 同时有“资料（可选）”与“参考图（可选）”，选择通过 `selectionKind` 分流；`HallReferenceImagePicker.vue` 是图片专用选择器，`BountyPanel.vue` 另有入口。
- Web `hallRequirementCreateIntent.js` 的创建合同只接收 `purpose:REFERENCE`；旧创建 v1 限 JPEG/PNG，不能通过按钮改名宣称通用附件已接入。
- API 当前 `ChatBountyExecutionCoordinator` 首轮将操作限定为 `GENERATE_IMAGE`。通用资料不能一律送往 controlled-image V3，也不能把没有绘图能力视作不能议事。
- 当前会话资料有单独用途选择/显式查阅接口；通用输入框需连通相同授权目录与按需读取，不能只做前端卡片而不送 Agent。
- 实测任务420自动进入会话，但执行在 Provider START 前 FAILED、界面仍等待。终态投影必须修复，不能把无限等待当作 Agent 澄清。

## 3. 一份内容，多种关联；不新增文件系统

```text
既有私有内容/精确文件版本
  ├─ 用户工作空间目录与所有权
  ├─ 任务/需求资料关联 → 同会话某次消息的固定来源快照
  └─ 已验证会话成果 → 可选个人归档 / 用户选定的正式交付
```

复用现有 file/version、task-link、conversation asset/part 和 delivery 引用。避免因图片/音频/文档分别新建目录服务或重复上传；底层必要复制仍按既有生命周期和私有存储合同，不能为“去重”取消独立ACL。山寨安顿与自家接应保留各自工作目录：平台提供范围受限的领取接口及 input manifest，Agent 在私有 run 下 materialize 到 inputs，成果写 outputs 并验证上传；本机路径不能直接成为浏览器下载地址。

## 4. 通用附件合同（非线上接口说明）

### 4.1 业务选择与服务端快照

新业务选择仅含 `{fileId, version}`；会话追加还可引用**当前会话**中已授权的 `{assetId, assetRevision}`。请求不信任客户端传来的 MIME/哈希/owner/任意 URL/本机路径；服务端从当前身份的可访问精确版本获取 displayName、contentMimeType、byteLength、sha256。正文和附件目录一起固定入需求/消息快照，不能只保存 latest 指针。重复项按相同来源/版本识别，不按文件扩展名或“参考图”标记分支。

业务资料与执行输入分层：资料目录可以包含多个媒体类型；某次执行的 input manifest 只包含完成当前意图所需且已获授权的精确来源。Agent 提出的“参考图/待总结文档/待转写音频”等用途须经服务端策略、目标能力与ACL验证；用途不是扩大读权限或付费权限的凭证。

### 4.2 HTTP与异步边界

| 入口 | v3目标合同 | 当前实现与版本边界 |
| --- | --- | --- |
| 创建需求 | 正文 + 可选通用 `attachments:[{fileId,version}]` 原子持久化；无点将/Provider副作用 | 现有 `POST /agent/tasks/creation-operations` 及 `GET /agent/tasks/creation-operations/request` v1严格字段集不变；新增显式版本化合同，由M1固定独立v2路由或显式协商，不能向旧v1静默塞字段 |
| 点将并议事 | explicit target + expected requirement/assignment revisions；固定所有资料引用，创建一次会话/首条请求 | 复用现有任务根事务、assignment-operation只读核对、bootstrap outbox；通用受理不暴露或强制 `GENERATE_IMAGE`，M1冻结通用路由/DTO，绘图专用参数收敛到执行适配层，不作为新业务入口或通用点将前置 |
| 会话补充 | 原会话+期望代次/版本+正文+本轮来源选择；形成新request/step | 复用统一 interaction admission/typed discussion，发布前冻结新schema及快照digest；不得让已有v1/v3 strict parser宽松接收未知字段 |
| 内容读取 | 同身份/目标/任务/会话代次与精确版本绑定，读取元数据与内容分离 | 保留现有私有媒体读取、runtime scope/fence/manifest，不开放整工作空间或任意URL |
| 事件/历史 | 同一 request/step/message/part 的增量、revision和真实终态；媒体晚到不丢 | 复用journal和SSE回放，不新造图片专用通道；FAILED必须结束等待并给出可操作原因，不自动重试执行 |

新增写入口沿用幂等键：同键同body返回原意图；同键异body冲突；未知结果先GET原操作，404不证明写入未发生。鉴权错误不泄露别人的附件；版本漂移返回冲突并保留当前草稿；某项不可读要明确指出该项，不静默丢弃后执行。不支持的**处理能力**与能否选择/保存/下载该资料是不同问题。

**M1创建子合同已固定：**见[通用原子创建v2](unified-materials-creation-v2-contract-20261003.md)，包含显式v2路由/字段集、持久版本标签及幂等/旧恢复。点将与会话通用分派、能力目录与媒体组合校验仍待冻结/实施。不得把本节示意字段直接宣称线上可用，也不得未经合同自检就改生产表或松绑冻结协议。

### 4.3 fast 与多媒体的长期关系

同一业务会话采用按需步骤，不是两个互斥产品模式：纯聊天不预加载工具与文件正文；附件目录随业务上下文可见，确需查阅时进入受限INSPECT；确需产出时经授权进入EXECUTE。默认不装载所有资料不等于永不允许读取资料。Agent允许自然澄清，明确需求也允许直接执行；工具选择不能替代服务端的准入、权限和费用验证。

### 4.4 执行适配与输出

绘图的模型名、reference-image数组、PNG/JPEG限制、编辑参数、START fence留在受控绘图适配器内。其他Agent能力走各自受控适配，不伪称现有所有Agent都能处理所有格式；能力缺失在议事里澄清/提示可行处理路径，不能要求用户另建图片服务器。优先复用已配置Agent接入通道，未经证实的模型名不写入配置。

媒体asset达到ready前必须有真实字节、MIME、长度与摘要，统一part renderer处理文本/图片/音频/文件。保存工作空间只归档选中内容；交付只晋升用户选定精确集合。不因保存失败重新调用生成；执行失败不得遗留RUNNING请求；禁止把只剩本地spool的成果误称服务端已可恢复。

## 5. 开发拆分与依赖（唯一运行台账不变）

| 包 | 修改边界 | 必须产出 | 依赖与验证 |
| --- | --- | --- | --- |
| M1 通用合同/API | requirement creation、资料快照、bootstrap、通用interaction/coordinator | 通用资料版本化受理、全目录随任务进入会话、按业务意图而非固定生图分派 | 先冻结兼容/ACL/事务/幂等合同；实际服务/HTTP+隔离MySQL回归，旧图像合同继续通过 |
| M2 Web入口 | HallOverview/BountyPanel、统一picker、create intent/附件卡 | 单一“添加资料（可选）”，图片/文档/音频/普通文件混选、空选、预览和移除；删除技术用途必选/图片分流 | 可与M1按冻结合同并行；必须测试非图片真实payload，不只snapshot文案 |
| M3 会话与Agent | ChatPanel/composer、typed context/INSPECT、两个runtime模式 | 同会话补文字与各类资料，Agent判断用途、答复/澄清/执行；真实限定版本读取 | 基于M1；资料内提示视为不可信内容，非执行授权；保留独立run目录 |
| M4 终态/成果 | execution→Chat投影、统一媒体、归档、交付恢复 | FAILED不一直等待，媒体实时更新；text/image/audio/file共用预览下载保存与验收 | 与M2/M3独立源码边界可并行；CAS/事务/重放/冷恢复、服务端无stage上传恢复 |
| M5 统一验收发布 | 主控集成exact API/Web/Client | 完整AC01–AC22 + FD01–FD12与下列强制子例、同版本发布证据 | 不用鸟图覆盖通用用例；Web正式test/build仅Flow4403172同Run制品，API沿既有实际授权；不抢占foreign Run |

以上是工作包职责，不冒充已派发Owner；当前唯一Main负责协调。独立Writer不可用时Main顺序实现，不等待不存在的线程，不创建Reviewer。现有图像底层修复作为M1/M3适配器子项保留；不能以其通过宣布通用入口具备上线条件。

## 6. 必须验收的补充子例

保留原34项ID，不抹掉既有局部证据；下列UM子例是原用例的加强范围，不以旧图片测试抵扣。

| 子例 | 映射 | 可观察通过条件 |
| --- | --- | --- |
| UM01 | AC01/AC02 | 需求入口只有“添加资料（可选）”；空选照常提交；没有单独参考图入口 |
| UM02 | AC02/AC16 | 同一选择器混选PNG + 文档 + 音频 + 已支持普通文件；四类均进入真实请求/服务端快照，预览/移除有效；无图片隐藏过滤 |
| UM03 | AC02/AC03/AC04 | 各类资料选v2后源新增v3，点将与Agent读取仍绑定v2/摘要；重复点击/断线不丢附件、不重建 |
| UM04 | AC05/AC06/FD01–FD06 | 无图需求可直接办；有图可以是描述/分析而非生成；PDF/文字整理无需绘图能力；不充分时原会话澄清 |
| UM05 | AC09/AC10/AC20 | 同会话后补文档/音频/图片，消息与来源真实关联；Agent按需读取；引用未归档上一稿可继续修改 |
| UM06 | AC07/AC08/AC09/AC11 | 文字、图片、音频、文件混排与晚到事件实时可见、真实预览/播放/下载；局部失败不隐藏其他项 |
| UM07 | AC12/AC14/AC15 | 各类选中项可选保存；不先归档也能正式交付验收；失败只恢复原操作，不再生成 |
| UM08 | AC17/AC18/FD11/FD12 | 山寨安顿与自家接应各跑有/无资料及非绘图业务；工作目录独立、能力不足如实说明，无静默降级 |
| UM09 | AC15/AC21 | 执行FAILED后会话停止等待并显示真实失败；补充形成新意图，不自动重发旧START/收费请求 |
| UM10 | AC16/AC19/AC22 | 第二账号/撤权/恶意文档/伪造来源拒绝；无全空间授权；旧PRIVATE/TASK/纯聊天、原交付保留 |

通用产品当前状态：**NOT_COMPLETE；UM01–UM10尚未验证通过。** 画鸟真实图像成果的既有证据继续有效，但不能据此把“全部多媒体协作可验收”标为完成。

## 7. 本轮已有修复与发布边界

- API线上仍1.13.67 `b8053da6`；Web仍1.13.64 `0b665640` / Flow4403172 Run164 SUCCESS，含voice SVG `e58644a`；Client仍1.13.62。
- 任务420的参考v2/点将/自动进入会话已实际观察，但执行FAILED且未Provider START；未重放418/419/420，没有新生图调用。
- 本轮修复候选 `bb52cd7bb11a6113d389ca2b35d94f2af9626846` / tree `87a26c673384ddc19ac23e7bb9010c681cdf2b09`：全局响应脱敏器将DTO转Map重新加回source的13字段，导致NON_NULL失效；仅原生受鉴权inputs-v3方法保留其无秘密的精确DTO序列化，普通接口脱敏不变。两个有效红测失败，修复后12项通过，包括真实Filter/Controller/Advice/Converter组合、浏览器Origin/缺鉴权拒绝与来源拒绝回执回归（认证和执行服务为stub，不冒充真实账号ACL验收）。一次夹具语法错误、一次隔离source-set缺运行依赖已修正，原日志保留。
- 候选仅独立feature推送，**未合develop、未生产构建、未发布**；预备的1.13.68不是已发布版本。纠偏通知不取消、不抢占任何Run；本轮未触发Flow或操作运行服务。

## 8. 2026-10-03 21:54 实施增量（源码候选，不是上线）

- Web独立`codex/mmd-unified-materials-web-20261003`：`6a2b71e2162bcdb70b48be1919209f10781d9f90` / tree `5651935a289788b7e27cc7f6957ddc0a6d696a39`，已push/readback，未合develop。
- M2先行基础已落地：Overview仅“添加资料（可选）”，删除图片筛选/专用selectionKind/用途下拉；真实workspace adapter的图片、PDF、音频、文本四类混选固定版本进入组件提交payload；卡片预览、版本预览/下载/移除，取消与身份切换保留隔离。现阶段QuickMatter仍用既有task-link INPUT适配，**不是最终通用原子创建合同已完成**。
- 后端workspace既有音频/GIF/WebP能力未在前端白名单接通，现补详情、上传、原生audio预览与两种workspace界面；不自动播放。显式video/HTML等MIME不按扩展名伪装为audio，SVG/HTML/script仍不内联。旧预览和文件详情晚到有真实红测，加入代次隔离，不能覆盖新选资料或撤销新Blob URL。
- 8个真实存在的选择器共66 PASS、0失败、0pending；实际Vue组件+真实adapter、HTTP与媒体bytes为fixture，不冒充系统Chromium解码、真实账号、服务端快照或Agent验收。JS/测试ESLint零错误；两SFC有42项原有问题（基线44），按rule/message增量0，不能写全量lint已通过。
- BountyPanel仍待替换；M1通用原子创建合同、M3非固定绘图分派、M4 FAILED终态与仅spool恢复仍未实现。不能把此局部候选合develop自动发布后称纠偏完成；待共同候选具备上线条件再由4403172正式测试/构建/同Run发布。
- 未调用Flow Start/Update、无本地生产构建、无Provider/生产DML，不重放418/419/420。API bb52修复保留。详见[本轮源码证据](integration-evidence-20260928/unified-materials-correction-20261003/web-source-progress.json)。原34项+UM子例仍NOT_COMPLETE。

## 8. 2026-10-03 后续实施：新方案创建入口已接线（未发布）

- API候选 `6a855a6de88b69baa9cdefe75e375a04da078249` / tree `2a3cfb55247b4051289203ea45dcbd5dc3091a00`，独立分支`codex/mmd-unified-materials-api-20261003`。通用v2创建支持图片/PDF/音频/文本及空选；复用原事务，资料、需求任一持久化失败整体回滚，不增加文件体系、不改生产schema。30定向测试PASS/0失败/0跳过（Controller/Service/H2真实事务/隔离MySQL等）。
- Web候选 `43645f179b60ba869c9496e2722bc40d981f7783` / tree `ac4e7030c105f84d19807738478020cb1c7682f4`，独立分支`codex/mmd-unified-materials-web-20261003`。Overview与Bounty共用`HallMaterialPicker.vue`；只提交`attachments:[{fileId,version}]`。混合固定版本、统一预览/下载/取消/移除；业务层无INPUT/REFERENCE及图片过滤。
- 两个入口均使用通用v2原子创建，Overview不再调用QuickMatter先创建再逐份关联；完整原文不截成30字标题。创建不点将、不执行、不调用Provider。未知结果进入同一原请求恢复；身份隔离/幂等保护不构成第二产品流程。资金悬赏权限范围不扩展。
- 90项通用选择/创建/集成回归 + 14项实际JuyiHall/Bounty组件定向回归，共104 PASS/0失败/0pending；新共享组件ESLint零问题，修改文件按rule/message计数相对基线新增0。存量lint问题仍存在，不宣称全量lint已通过。
- 测试采用真实Vue组件/真实工作空间adapter及HTTP媒体fixtures；本轮没有实际Chromium、线上Agent或浏览器解码验收。详见[创建子流程源码证据](integration-evidence-20260928/unified-materials-correction-20261003/atomic-materials-source-progress.json)。
- **下一步只推进新方案**：通用点将与全部资料目录→Agent按需答复/澄清/查阅/执行→同会话追加与多媒体交付。失败终态投影、仅spool恢复及原34+UM整体验收仍未完成。不再安排独立参考图或旧生图入口的兼容扩展，不把局部绿测称为可验收发布。
- 以上均独立候选，未合develop、未触发Flow或部署；既有API/Web线上版本未由本轮变更。SDD gitlinks保持真实已发布版本。
