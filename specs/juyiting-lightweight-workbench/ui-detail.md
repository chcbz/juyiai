# 正式聚义厅 · 轻量工作台 UI 详设（实现态）

基线日期：2026-09-23；复核：2026-09-24。适用范围：`/juyiting` 内此次新增的工作台框架、概览和顶层业务面板；**不是**其他全站路由或静态 Demo 的全量样式规范。原型的逐控件 180 种目标、38 场景 CSSOM 与页面尺寸，分别见 `../../docs/ui-workbench/{ui-detail.md,component-attributes.md,control-targets.md,evidence/computed-ui.json}`。原型是假数据；下表是正式 Vue 实现的规则，不把原型属性误写成已实现属性。**正式接入的逐组件字号/字重/行高、实测 W×H、边距/gap/圆角与文字/背景色的桌面+手机对照请查 [计算属性附表](ui-computed-attributes.md)**；四视口 28 场景原始样本查 `evidence/computed-live-fixture.json`；**实际可见按钮、输入框/链接逐项登记**见 [正式控件属性索引](ui-control-attributes.md)及 `evidence/computed-controls-live-fixture.json`（含 320/844 断点和现有全局抽屉的 offscreen 链接）。

## 1. CSS 来源、层叠和计量

- 工作台框架样式：`web/src/components/world/JuyiHall.vue` 的 scoped `<style>`，限定 `.home-overview`；普通业务面板保留各自现有样式，非地图模式不修改 Stage 绘制。概览：`web/src/components/juyiting/HallOverview.vue` 的 scoped 样式；消息/会话、任务/文件/阅读的细部字体和按钮仍由各自组件定义，**未全站统一重写**。
- 框架 CSS 变量（仅工作台祖先）：`--work-paper:#FFFEFA`、`--work-ground:#F5F4F0`、`--work-line:#E3E5DC`、`--work-ink:#242E2B`、`--work-muted:#68716B`、`--work-brand:#923F30`；主按钮 hover `#793326`，选中背景 `#F6EEE8`，普通 hover `#F0F1EA`；焦点轮廓 `3px solid #923F3080`、offset `3px`。
- UI 正文字体栈 `-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`，基准 `15px/1.65`；品牌、欢迎大标题、地图预览文字用 `"Noto Serif CJK SC", "Songti SC", STSong, serif`。均为回退列表而非强制下载；不同操作系统的实际字形、换行待实机核对。Varlet 图标本地资源。
- 几何单位均为 CSS px；`minmax`、`env()` 按视口动态计算。`evidence/computed-live-fixture.json` 为 Chromium 中四视口 × 七表面的计算样式/包围盒/控件 aria/href 样本，**使用本地假认证 token 与空 API 响应，仅证明真实 Vue 的布局/导航，不是线上服务功能验收**。同目录 PNG 是视觉证据；样本无个人信息或口令。

### 2026-09-24 线上图标差异修订（待新版本发布）

线上 `/juyiting`（授权测试账号，仅浏览不写入）与 `deliverables/ui-workbench-demo/index.html` 对照：桌面七项侧栏和移动底栏四项的 Varlet 图标名/字形本来一致；不一致的是页头消息/账户为文字按钮、概览操作和资料卡缺图标，以及移动“全部入口”展开项只有文字。本次仅补这些图标，不改导航目标/权限/地图美术，原 28 场景 CSSOM 属修订前快照。

|位置|原型与修订后图标名|规则与无障碍|
|---|---|---|
|桌面侧栏七项/手机底栏四项|`home-outline`、`format-list-checkbox`、`chat-processing-outline`、`account-circle-outline`、`file-document-outline`、`notebook`、`bell-outline`；手机显示首/次/三/典籍四项|原有 19/21px 不变；图标装饰，按钮中文名不变|
|工作台页头|消息 `bell-outline`、提出需求 `plus`、个人中心 `account-circle-outline`、全部入口 `menu`|手机消息/账户/菜单 40×40 CSS px；按钮保留 `aria-label`，地图页头原文本不变|
|概览主动作/资料卡|提出需求 `plus`、先聊一聊 `chat-processing-outline`、资料 `file-document-outline`|动作图标 16px，文字仍可见；资料图标 22px，底托 44×44、圆角 9、底色 `#EAF2ED`/图标色 `#21604D`|
|手机展开“全部入口”|七项同侧栏，实景 `map-marker-outline`、个人中心 `account-circle-outline`、使用帮助 `help-circle-outline`|图标 19px、文字保持；菜单仍两列、可滚动、原动作及回焦不变|

源：`web/src/components/world/JuyiHall.vue` / `web/src/components/juyiting/HallOverview.vue`；图标本地 Varlet font 与 Demo 的 `assets/icons.css` 使用相同码位。线上旧版截图与本地候选图标对比仅为视觉修订记录，服务器重新发布前不可称线上已修复。

## 2. 页面结构和属性

|部件/选择器|常规桌面|≤1200|≤1000 / ≤760 / ≤600|短横屏 ≤560 高|
|---|---|---|---|---|
|`.juyi-page.home-overview`|grid `216px minmax(0,1fr)` × `76px minmax(0,1fr)`；height 100%，overflow hidden|列宽192|≤760 单列、行高 `64px minmax(0,1fr)`|行高 `58px minmax(0,1fr)`|
|`.hall-workbench-sidebar`|第一列两行、padding `28px 15px 16px`、`overflow-y:auto`、底部入口 `margin-top:auto`|水平padding10|≤760 隐藏|窄横屏可在侧栏内部滚动|
|品牌/栏目|品牌23px/500衬线，方印38×38，字21；说明11px/1.5；栏目11px + letter-spacing `.06em`、margin `30px 10px 10px`|同左|侧栏隐藏|同左|
|侧栏按钮|高度至少44、padding `9px 12px`、gap12、圆角7、14px/500；图标19；地图入口至少66、边框1、底距14|同左|手机底栏取代|同左|
|`.hall-app-header`|第二列首行、padding `12px 36px`，底边线1；品牌17；右侧工具按钮 min-height40 / padding `8px 12px` / radius7|padding左右26|≤760 首行 padding `10px 16px`；隐藏好汉和大号提出需求，保留消息/账户/全部入口|上下padding5，行高58|
|`.hall-overview`|最大宽1320、居中、`padding:30px 36px 36px`，背景 ground|padding26|≤600 `22px 16px`|滚动属于原 `HallPortraitHome` 内容区|
|概览标题与动作|眉题11px + 字距 `.08em`；h2 28px/500/1.5 衬线，字距 `.8px`；说明14；动作 gap10 / margin-top16；按钮最小42、radius7、14px/500|同左|≤600 h2 25px、字距0，动作12px|同左|
|`.overview-columns`|主栏 minmax(0,1fr) + 300，gap24；主卡 padding `22px 24px 0`、radius11、1px线|副栏264 / gap18|≤1000 单列，副卡两列；≤600 副卡单列，主卡 `18px 16px 0`|同左|
|事项页签/列表|页签 gap10，13px、padding `12px 8px`、横向滚动；列表上下padding17，标题15px/500/1.55，元信息12px，标签11px|同左|≤600 列表允许换行，元信息不裁掉动作|同左|
|概览副卡/资料|地图卡高176 / padding `20px 18px`，radius11；副卡和资料卡padding20，radius11；卡片间距18；副卡内操作至少36|地图卡默认同左|≤1000地图卡165；≤600地图卡185、资料/副卡padding18（资料左右16）|同左|
|顶层`.panel-overlay.is-workbench-panel`|absolute，从左216、上76，内padding `16px 24px`；面板最大宽1320，高100%，无深色遮罩|左192|≤760 inset 从上64至底 `62px + safe-area-inset-bottom`，padding0，面板全宽无圆角|上58；聊天重复简介隐藏|
|顶层`.floating-panel`|`width:min(1320px,100%)`，height100%、border1、radius12；标题最小56、padding `10px 20px`、字号20|同左|≤760标题最小44、padding `6px 16px`|最小40、padding上下4|
|`.workbench-mobile-nav`|隐藏|隐藏|≤760 显示；高度 `62px + env(safe-area-inset-bottom)`，`padding:5px 12px max(5px,env(safe-area-inset-bottom))`，边1，z-index30；每项均分，至少50高、竖向gap4、11px、图标21|≤760 同左|
|全部入口|≤760 前隐藏|同左|绝对定位右15、顶64、z-index32；`border-box` 宽 `min(330px,100% - 30px)`，padding12、gap6、2列；最大高 `100% - 64px - 62px - safe-area-bottom`，内部滚动|≤560高改顶58及对应最大高|

极窄复排补充（不改变上表常规断点）：宽 ≤240 CSS px 时页头仅保留品牌/“全部入口”（消息/个人中心仍在展开菜单），底栏前三项只显示图标并加同名 `aria-label`，最后一项继续显示“典籍阁”，图标按钮 font-size10/padding3；标题文字不换行而省略，议事工具栏可横向滚动且按钮可聚焦，议事输入 max-height56、上下 padding2。宽 ≤180 时标题视觉隐藏但 `aria-labelledby` 仍保留中文标题、工具栏 padding `2px 6px`、消息区 padding `4px 8px`、辅助文案单行省略。高 ≤260 且宽 ≤760 的极短屏中，**仅议事**窗口本身增加纵向滚动、消息区 min-height80/max-height40vh，草稿和发送按钮可以滚动进入视口；不覆盖常规模式。源码在 `JuyiHall.vue`；先以四个半尺寸 CSS 视口 + DPR2 预检，另在本文件 §3.1 使用 Chromium 实际页签 200% 缩放补验；两类证据与局限分别见 `evidence/compact-reflow-review.md`、`evidence/actual-zoom-review.md`。

页头在顶层工作台页签和消息/好汉/资料页可操作；打开草稿/详情等次级对话时不可操作。顶层工作区对话 `aria-modal=false`，次级/地图场景对话为 `true`；只有模态层执行焦点循环。打开和返回沿用原有 panelFrames 与草稿离开保存屏障，不把红色错误提示转为成功。

## 3. 厅内议事和其他真实业务面板

- 议事仍由 `PublicDiscussionPanel` / `BountyDiscussionPanel` / `PrivateDiscussionPanel` → `ChatPanel` → `HallChatComposer` 提供会话分页/删除、@选择、固定版本引用、流式与失败恢复。工作台只在顶层议事面板内覆盖 `.hall-messages` 为 `flex:1 1 auto; min-height:0; padding:16px 20px`（≤760 `10px 16px`），独立 `overflow-y:auto` 继承既有组件；输入区 padding `10px 20px 12px`（≤760 `8px 16px 10px`；短横屏 `6px 16px 6px`）。消息区并非固定高度，空会话实测记录见证据；有历史浮层、引用选择器或系统键盘时剩余空间会变。
- 短横屏≤560高隐藏重复 `.discussion-brief`，保留工具条 `.context-summary` 的话头标题和状态；不隐藏历史、引用、发消息控件。164px/390视口之类的极端键盘高度尚未验收。
- 悬赏榜、点将册、百宝箱、典籍阁、消息使用**同一批现有业务组件**，没有将 Demo 字体栈/按钮规格强行覆盖所有旧业务组件；详细字段/按键/间距仍由源文件及计算样式证据约束。非顶层内页（资料预览、草稿、固定版本成果、典籍阅读）的内层布局需继续遵循原组件规则，不以本表“卡片圆角12”覆盖内层。

### 3.1 本地 Chromium 实测（空数据，只读布局）

|视口|页头宽×高|侧栏宽|概览主卡宽|地图卡宽×高|移动底栏高|议事消息区高|页面水平溢出|
|---|---:|---:|---:|---:|---:|---:|---|
|1440×900|1224×76|216|828|300×176|隐藏|492.52|无（scrollWidth=1440）|
|390×844|390×64|隐藏|358|358×185|62|434.52|无（scrollWidth=390）|
|320×740|320×64|隐藏|288|288×185|62|330.52|无（scrollWidth=320）|
|844×390|652×58|192|600|600×165|隐藏|129.06|无（scrollWidth=844）|

**极窄/极短实测补表（候选 `8f47a12`，半尺寸 CSS 视口 + DPR2，非实际浏览器缩放）：**

|CSS 视口|底栏单项 W×H|前三项文字 / 典籍阁文字|议事消息区高度|议事窗可视高 / 滚动内容高|
|---|---:|---|---:|---:|
|160×370|34×51px|隐藏 / 可见；四项中文 `aria-label` 均保留|62.06px|250 / 250px|
|195×422|42.75×51px|隐藏 / 可见；四项中文 `aria-label` 均保留|97.06px|302 / 302px|
|422×195|99.5×51px|均可见|100px|75 / 301px，需滚到输入区|
|720×450|174×51px|均可见|129.06px|330 / 330px|

这些是按当前空数据和字体环境测得的包围盒；小屏的 `font-size:10px` / `padding:3px` 与 11px 常规底栏字号、非链接按钮语义见 §2、§4；窗口高度受输入法、内容和安全区影响，不能写死。原始 `width/height/labelDisplay` 和截图见 [`compact-reflow-fixture.json`](evidence/compact-reflow-fixture.json) 与 [`compact-reflow-review.md`](evidence/compact-reflow-review.md)。

**消息内容态补测**：在与上述空会话结果**不同**的隔离 fixture 中，真实 Vue 会话路径渲染 28 条合成 Markdown，按 100% 两手机视口和实际页签 200% 四视口量测消息气泡、列表、代码块、链接、独立滚动及输入区边界；390×844/100% 消息区 434.52px、首气泡 358×205.94px、正文与链接 15px/23.25px、链接 `#7f4a22` 下划线且 offset2px，源码生成的本地片段 `href="#local-fixture"` 无 target/rel；160 CSS px 宽/200% 时气泡宽144px、代码块宽120px且代码块内部可横滚，正文保持15px。六种条件 28 条真实 Vue DOM 气泡均不越界，且滚动限于消息区/极短屏工作窗。逐项高度、字体、包围盒和边界见 [`rendered-chat-review.md`](evidence/rendered-chat-review.md)、[`rendered-chat-native-fixture.json`](evidence/rendered-chat-native-fixture.json)、[`rendered-chat-actual-zoom-fixture.json`](evidence/rendered-chat-actual-zoom-fixture.json)。这只是**合成 API 回复**；不是从服务端取到真实长会话，也未测试 SSE/键盘。

**实际浏览器缩放补样**：另用隔离的 Chromium 页签 API `setZoom(2)`/`getZoom()` 验证原始 320×740、390×844、844×390、1440×900 四个视口实际缩为对应半尺寸 CSS 视口，消息区约 62.05/97.05/100/129.05px，28 段合成内容仍由消息区独立滚动；极短视口工作窗可滚到发送按钮。与上表“半尺寸 CSS 视口 + DPR2”**证据性质不同**；来源/几何/安全界限见 [`actual-zoom-review.md`](evidence/actual-zoom-review.md) 与 [`actual-zoom-fixture.json`](evidence/actual-zoom-fixture.json)。这不是实体设备或项目固定 Chrome 133 的测试。 同一真实缩放页签还从“全部入口”逐一核对七个顶层页面的空数据 DOM 容器与标题、典籍“案卷检索”内页、返回概览，并测得各面板与底栏无重叠、页面无横向溢出；详细逐项矩形在 `evidence/actual-zoom-fixture.json` 的 `primarySurfaces` 和 `returnToOverview`，判定界限见 `evidence/actual-zoom-review.md`。内容态/授权态内页控件字号与链接仍需在条件出现时按 §3.2/§4 和真实 CSSOM 核验。

手机底栏实际高度经 `box-sizing:border-box` 与面板底预留 62px 一致，**不是** 62px 高再额外加上下 padding。消息区是空话头/关闭引用与历史选取器时的高度，不是有键盘或长消息时的恒定值。已另用实际 Vue 渲染 28 条**合成** Markdown 消息在四视口＋720×450 核对消息自身滚动且输入不被遮挡，数值见 `evidence/long-chat-fixture.json`；这只验证视图布局，不表示真实话头数据已从服务端读取，也不等于 200% 浏览器缩放测试。另补 `evidence/compact-reflow-fixture.json` 只证明等效半尺寸 CSS 视口的布局和操作入口，**不**等于实际浏览器缩放。更多位置、各页签 computed 字体/间距/颜色见 [计算属性附表](ui-computed-attributes.md)，可见区域的原始 CSS/aria/href 样本见 `evidence/computed-live-fixture.json`；正文表按最终 CSS 约束取整，几何小数仅报告实测样本。

### 3.2 原业务内页属性（源 CSS 声明；不作为全部状态的实测值）

以下只记录本次导航**实际复用**的内页关键控件；均为 `web/src/` 的组件源码规则，与 §3.1 空数据 CSSOM 的数值证据等级不同。字号未单独声明时继承该组件/父级，不能把工作台 `15px` 强行当成所有表单控件的 computed 字号；例如原生输入在 Chromium 中可能为 `13.3333px`。W×H 随数据、容器、字体和内容变化。

|入口 / 源组件选择器|字体、颜色|距离、大小和排布|响应式/状态|
|---|---|---|---|
|厅内议事 `ChatPanel.vue` `.panel-toolbar` / `.icon-button`|工具条 12px `#765f40`；上下文标题 14px/700 `#3f2815`；状态 12px；图标按钮 `#4a3423` / `#efe0c6`|工具条 padding `8px 10px 6px`、gap8；按钮 34×34、圆角8、相邻gap6|引用区打开时额外占高 `max-height:min(42vh,270px)`；消息区取剩余高度|
|同组件 `.hall-message` / `.message-content`|消息文字 `#4a3423`、行高1.55；发送者13px、状态12px；用户背景 `#e8f2ed`，Agent/系统 `#fffdf6`|气泡 max-width 88%、padding `10px 12px`、底距10、圆角8；Markdown 段落下距8，列表左内距20，代码块 padding `8px 10px`|长消息独立纵向滚动，代码块/表格内部横向滚动；消息正文链接下划线且 `#7f4a22`|
|`HallChatComposer.vue` `.composer-textarea` / `.composer-send`|输入颜色 `#3f2815`、背景 `#fffdf6`，继承字体、行高1.45；发送 `#fff8e8` / `#7f4a22`|输入最小42、最大132高，padding `11px 12px`、圆角8；操作按钮宽42/最小高42、圆角8；操作 gap6；@标签高26、max-width128、gap4、padding `0 8px`|≤760由工作台覆盖外层 padding `8px 16px 10px`；短屏≤560高 `6px 16px 6px`，不缩小消息字体|
|我的事项 `BountyPanel.vue` `.task-create-form` / `.task-card`|内页主字继承；榜文正文/时间12px `#765f40`；卡片背景 `#f7ecd7`，选中 `#ead3a9`|创建表单四列 `minmax(150px,1fr) minmax(180px,1.4fr) minmax(140px,.8fr) auto`、gap8、padding `0 16px 12px`；卡片 padding12、底距10、圆角8；状态标签 gap8/底内距12；单任务操作 34×34|创建/详情/经济动作受原权限和断点控制；真实数据行未被空数据样本测量|
|点将册 `AgentPanel.vue` `.agent-panel-body` / `.status-filter`|工具条13px `#765f40`；状态选中 `#fff` / `#23483e`，未选 `#4a3423` / `#efe0c6`；次级字12px|列表+详情列 `minmax(0,1fr) minmax(260px,320px)`、gap12、padding `0 12px 12px`；状态按钮 min-height36、左右padding12、gap8、圆角8；列表行 padding10、底距8；头像38/58|≤900px 单列，详情排在列表之前；≤620px 工具条上下排列|
|典籍阁 `LibraryPanel.vue` `.library-tabs` / `.library-search`|页签继承当前字体；激活背景 `#23483e`、字 `#fff8e8`；表单字 `#3f2815`、背景 `#fffdf6`|容器 padding14、gap12；页签 gap8、padding `7px 10px`、圆角7；搜索列 `minmax(180px,1fr) 132px auto`，gap8；输入/下拉高38、左右padding10、圆角8；搜索按钮高至少38、左右padding12|**容器**宽≤520px 时检索表单单列，不按浏览器窗口宽度判断；双页签仍是内部按钮|
|原文阅读 `archive/ArchiveReader.vue` `.archive-reader-fullscreen` / `.reader-paragraph`|正文 `serif`、`clamp(16px,1.35vw,20px)`、行高2；章题 `serif`、`clamp(22px,2.5vw,30px)`|阅读全屏 fixed、`100dvh`、z-index10000；gap12、padding `clamp(12px,2vw,24px)`；正文 max-width50em、段距 `0 auto 1.05em`；内容区三列（目录打开）/两列（关闭），gap12、内边距 `clamp(12px,2vw,22px)`|≤900px 内容变单列，目录抽屉宽 `min(82vw,330px)`、笔记抽屉 `min(88vw,390px)`；设备横屏/虚拟旋转及安全区另有覆盖，不能只照常规表|
|百宝箱 `PersonalWorkspace.vue` `.is-hall-treasure` / `.treasure-content`|根字体16px；标题22px/500/1.45（≤600为19px），说明14px/1.6；主按钮 `#fff9ee` / `#8d402c`|根 padding `28px 30px`（≤600为 `20px 16px`）；按钮 min-height44、padding `8px 14px`、圆角4；页签 gap8、下距18；搜索区 gap12、margin `18px 0 12px`；输入 min-height44|文件版本/预览/管理在内页切换，不使用新路由；短屏≤500有独立紧凑规则|

颜色和 font-family 的层叠边界：品牌/欢迎/地图卡明确衬线、正文为工作台回退栈；阅读正文写的是通用 `serif`，百宝箱内部有 `font-family:serif` 的二级标题；这些**不是同一套强制字体文件**。业务内页/条件数据态的每个像素没有真实身份的逐状态截图就不声称“全量实测”；应按相关组件 `<style scoped>` 与挂载后 CSSOM 两级复验。

## 4. 链接、控件目的和页面返回

|可见位置|标签|动作/目标|URL属性|
|---|---|---|---|
|桌面侧栏和手机底栏首项|办事概览|关闭当前顶层业务面板、显示权威 `HallOverview`|无 href，仍在 `/juyiting`|
|桌面侧栏和手机底栏第二项|我的事项|根切换 `openPanel('tasks')` → 真实 BountyPanel；原张榜/查榜/指派/推荐仍从组件内进入|无 href|
|桌面侧栏和手机底栏第三项|厅内议事|根切换 `openPanel('chat',mode:'public')` → 真实会话；具体私议/事项议事从上下文动作进入|无 href|
|桌面侧栏和手机底栏最后一项|典籍阁|根切换 `openPanel('library')` → 典籍阅读和案卷检索 tabs|无 href|
|侧栏其余项/全部入口|点将册、百宝箱、消息通知|进入真实 agents、treasure、messages，不改变账户权限或服务端状态|无 href|
|首页需求/聊天/资料/好汉/地图卡|提出需求、先聊一聊、打开百宝箱、打开点将册、厅中实景|原 `openPrivateDraft`、会话/资料/点将/`homeMode=map`；地图加载仍靠 HallStage|无 href|
|工作台“使用帮助”|使用帮助|原 `HallOnboarding` 重新打开|无 href|
|工作台“个人中心”|个人中心|调用现有 `router.push({name:'UserProfile'})`，由原离厅确认与路由守卫保护|`/profile`，按钮本身无 href|
|地图 HUD“办事概览”|办事概览|`setHomeMode('overview')` 返回同一 `/juyiting`，Stage 不销毁|无 href|
|典籍阁两个页签|典籍阅读/案卷检索|同一个 `LibraryPanel` 内状态切换；原 Reader 章节/书签/笔记/选段和检索继续复用|无 href|

**内页真实链接/下载的例外**（本次工作台没有新增这些链接）：

|来源/元素|href/解析目标|target、rel、下载属性|出现条件和验证界限|
|---|---|---|---|
|`PersonaCatalogPanel.vue` 本地接入指引 `<a>`|源码常量 `https://gitee.com/chcbz/isp-install/blob/master/skills/codex-ws-agent-install/SKILL.md`|`target="_blank"`，`rel="noopener noreferrer"`，无 download|只在招贤令特定接入状态可见；此处是**源码合同**，非空数据 DOM 实测|
|`ChatPanel.vue` 本地合成 Markdown 锚点|`#local-fixture`，仅合成消息的相对片段|无 target/rel/download|28 条经真实 Vue 渲染后的 **100% 和 200%** CSSOM/URL 属性见 `evidence/rendered-chat-review.md`；不能据此推断服务器消息链接地址或安全性|
|`ChatPanel.vue` 服务端消息 Markdown `<a>`|由消息内容生成；`marked` 输出经 DOMPurify 净化后渲染，无法给固定 URL|未在组件显式指定 `target`/`rel`/download，最终属性依净化后的消息内容，**不能假定外链均新窗**|字体/距离遵循 `.message-content :deep(a)` 的 `#7f4a22`、下划线、offset2px；仅有真实消息时出现，需另做 URL 安全核验|
|`PersonalWorkspace.vue` 版本“下载”按钮|可见按钮 `href=null`；鉴权取得所选版本 Blob，`savePersonalWorkspaceBlob` 临时创建并撤销 `blob:` URL|临时 `<a download="安全文件名">`；不是持久可分享链接|需相应文件与版本权限；空数据样本不能证明下载成功或写死 href|
|旧全局抽屉中的 3 个 `<a>`|`/profile`、`/messages`、`/help`|源码/快照未新增 `target`/`rel`/download|在空响应浏览器 DOM 中但位于 x=-240、关闭时不在视口；不是工作台新增导航|
|典籍阁案卷引用、原文选段提问|`href=null`，触发内部业务动作|不适用|有搜索结果/选段且有权限时才出现；尚未做实际搜索/写入|

上述动态/权限态均未包含在空数据逐控件 CSSOM 中，需授权环境分别核对 URL 安全、下载权限及版本号。

所有上述工作台按钮当前为 `type="button"` 内部动作，**不是**带 `href` 的锚点；文档“/profile”表示调用 Vue Router 后实际应到达的路由，不等于账户按钮的 DOM href。典籍阁内的两个 `<button role="tab">` 带 `aria-selected`、`aria-controls` 与 `tabindex`，键盘左右切换；后续新增链接需另列实际 URL/target/rel 与权限。当前页面不会为这些按钮生成可分享的面板深链。本次未引入新路径或外链，顶层页签不会修改 pathname/hash；浏览器 Back 不等价于面板 Back。外部链接（如招贤令安装指引）按原组件权威 URI/权限展示，本次不伪造通用 URL；本地空 API 的正式页面还采到原全局抽屉（关闭时 x=-240，不在视口）的真实 `a[href]`：`/profile`（个人中心）、`/messages`（消息中心）、`/help`（帮助与反馈）；这是旧全局导航，不是工作台新增的按钮链接，不能说整个站点没有 href。全站原 `/`, `/demo`, `/oauth2/callback`, `/profile`, `/workspace` 等路由仍由原 Router 管理。

### 4.1 精确尺寸/排版/链接索引（避免把导航按钮误认作 URL）

以下为**正式候选**（1440×900、390×844、320×740、844×390），不借用 Demo 假状态。先查本文件 §2 的 CSS 规则/断点，再查 [实测字体·尺寸·距离·颜色](ui-computed-attributes.md) 和 [按钮·输入·链接逐项明细](ui-control-attributes.md)；四视口每一个已布局控件的 `rect`/字体族字号字重行高字距/`padding`/`margin`/`gap`/前景背景/边框圆角/ARIA/type/`href`/resolvedHref 在 [`computed-controls-live-fixture.json`](evidence/computed-controls-live-fixture.json)。实测值是状态快照，不等于对所有条件状态下固定的尺寸承诺。

|控件/场景|桌面 1440×900|手机 390×844|语义、目标及采样界限|
|---|---|---|---|
|侧栏“典籍阁”|185×44；14px/500/20.3px；padding 9px 12px；相邻侧栏项 gap3px|不显示|按钮无 href，切到原 `LibraryPanel` 的阅读/案卷页签；侧栏底区与顶区分开|
|底栏右下“典籍阁”|不显示|91.5×51；11px/400/18.15px；padding5px，图标21px；底栏62高，底/顶内边距5px/5px（安全区为0时）|按钮无 href；仍在 `/juyiting`，不是 `/archive` 或下载链接|
|页头“全部入口”|不显示|46×40；15px/400/24.75px；padding8px 12px；位于 x328/y12.02（此单视口）|`aria-label=全部入口`/`aria-expanded`；只在展开时显示菜单，关闭态计算样本没有菜单子项|
|议事工作区关闭按钮|36×36；15px/500/24.75px；padding 0 12px|36×34；15px/500/24.75px；padding 0 9px|`aria-label=关闭面板`，无 href；属于顶层返回逻辑，次级表单返回需单独检查|
|账户按钮与旧抽屉链接|账户 56×42.75；15px/400/24.75px|同桌面|账户本身无 href、Vue Router 到 `/profile`；关闭的全局抽屉有三条 `a[href]` `/profile`、`/messages`、`/help`（x=-240，非视口内），它们不属于本工作台新增链接|

展开菜单的**源码规则**：相对 `.juyi-page` 绝对定位 `top:64px; right:15px; z-index:32`（≤560高为 top58）；`box-sizing:border-box` 宽 `min(330px, 100% - 30px)`；`max-height:calc(100% - 64px - 62px - env(safe-area-inset-bottom))`（短屏替换64为58）、`overflow-y:auto`、内部滚动不传到底页；内边距12、两等宽列、gap6、圆角10、背景 `#FFFEFA`、边框1px `#E3E5DC`、阴影 `0 18px 38px #242e2b29`；文字换行、左对齐。它的字体沿用工作台继承栈/页头按钮规则（15px、padding 8px 12px、min-height40）；**原 28 场景控件 CSSOM 仍为关闭态；现候选 `a935440` 新展开态另在六视口实测了外框 W×H、scroll、定位祖先与末项焦点（`evidence/menu-short-screen-fixture.json`），未重采 10 个菜单按钮的完整计算字体/边距，因此本段文字属性仍是源码约束而非全状态实测**。320×320 短屏下菜单可在页头58px与底栏顶缘258px之间滚动；展开态实测与同期截图见 `evidence/menu-short-screen-review.md`，不代表实际软键盘/安全区已通过。

链接目录的界限：上述页签、典籍阅读/案卷检索切换、使用帮助、厅中实景都是 Vue 按钮，没有可分享深链、`target`/`rel`；典籍正文动态内容、招贤令外部安装指引、事项/文件详情和权限依赖的下载 URL 不在空数据采样内，**不能从这张表推断无链接或固定目的地**。需要在授权环境显示相应状态后补充标签→实际 URL/目标/权限，避免填造链接。源文件 `web/src/router/index.js` 注册 `/juyiting`、`/profile`、`/messages` 和 `/help`，本次没有新增路由。

## 5. 响应式和验收边界

- 工作台切换、厅中实景和已挂载 Stage 的同实例测试依赖真实 Vue 组件；既有 28 场景图像/CSSOM 证据采用**本地只读空响应 fixture**，仅测试展示/入口/溢出与焦点。前序 Web `fe43ebc5` 曾以临时进程内只读代理和授权真实账号检查概览、章节与会话列表、实景 snapshot，详见 `evidence/real-readonly-browser-20260924.md`；此证据**不改变**上述 28 场景 computed 属性的来源，也不等于本候选已部署。账号资料权限不足/错误文案是模拟 API 的结果，不得认为线上服务出现此故障；阅读原文的进度写入、真实资料下载、SSE、报价/支付、指派等仍必须分别用已有业务测试与有授权服务验证。
- 真实软键盘、安全区（headless 的 `env()`=0）、实际宋体安装、辅助文字 11px 的可读性、所有子组件 200% 缩放和屏幕阅读器不是此布局采样的通过项目。
- 功能完整性审计矩阵与当前状态见 `../../docs/ui-workbench/feature-coverage.md`（**静态 Demo 的缺口，不代表本次正式接入新增了这 63 个功能**）和本规格目录 `acceptance.md`；保留依赖现有功能的入口，不宣称这次重新实现了其业务逻辑。
