# 正式 Vue 工作台 · 可见控件详设索引（只读空 API 样本）

来源：2026-09-23 Chromium 142，**正式生产构建的本地预览**（不是静态 Demo）。四视口×七顶层表面共 28 个快照，660 条已布局控件记录；其中非视口内的控件（例如现有全局抽屉位于 x=-240 的链接）按 `withinViewport=false` 单独标记，不当作页面当前可见。每条完整属性见 [`evidence/computed-controls-live-fixture.json`](evidence/computed-controls-live-fixture.json)：矩形、字号、字族/字重/行高/字距、padding/margin/gap、颜色、边框/半径/最小尺寸/阴影、type/role/aria/disabled、href 和 resolvedHref。只读取空 API，所以实际会话、数据行、授权按钮、次级页面**不在该采样中**；此索引不能冒充全部业务状态或真实服务验收。

以下两表只列当前视口内、按 `(区域, 标签, 文案, role, href, class)` 去重后的第一条状态样本；样本若在不同页面变色或 disabled，查原始 JSON 每页的具体记录。W×H 是 CSS 像素包围盒，**不是**可写死的设计规则。`—` 为不存在的属性，不代表有 URL 导航。区域 `.panel-overlay` 的标签是当前工作区内容。

## 1440×900（常规字体，仅视口内）

|来源页 / 区域|控件（标签·文案）|type / role / aria|href → 目标|W×H|字体大小 / 字重 / 行高|padding；margin；gap|文字 / 背景|边框 / 半径|
|---|---|---|---|---|---|---|---|---|
|overview / hall-workbench-sidebar|button · 聚 聚义厅 一起，把事情办成。|button / — / —|—|185×54|23px/500/27.6px|0px 5px；0px；10px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(36, 46, 43) / 0px|
|overview / hall-workbench-sidebar|button · 办事概览|button / — / Current=page|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(146, 63, 48) / rgb(246, 238, 232)|0px none rgb(146, 63, 48) / 7px|
|overview / hall-workbench-sidebar|button · 我的事项|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 厅内议事|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 点将册|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 百宝箱|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 典籍阁|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 消息通知|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 厅中实景 去梁山走一走|button / — / —|—|185×66|14px/500/20.3px|9px 12px；0px 0px 14px；12px|rgb(36, 46, 43) / rgb(245, 244, 240)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-workbench-sidebar|button · 使用帮助|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-workbench-sidebar|button · 个人中心|button / — / —|—|185×44|14px/500/20.3px|9px 12px；0px；12px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-app-header|button · 聚义厅|button / — / —|—|75×44.05|17px/400/28.05px|8px 12px；0px；12px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · 好汉|button / — / —|—|56×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · 消息|button / — / Label=查看消息|—|56×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · ＋ 提出需求|button / — / —|—|105.17×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(255, 254, 250) / rgb(146, 63, 48)|1px solid rgb(146, 63, 48) / 7px|
|overview / hall-app-header|button · 账户|button / — / Label=个人中心|—|56×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 提出需求|button / — / —|—|86×43.09|14px/500/23.1px|9px 14px；0px；normal|rgb(255, 254, 250) / rgb(146, 63, 48)|1px solid rgb(146, 63, 48) / 7px|
|overview / hall-overview|button · 先聊一聊|button / — / —|—|86×43.09|14px/500/23.1px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 悬赏榜|button / — / —|—|64×37.8|12px/500/19.8px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 刷新|button / — / — / disabled|—|52×37.8|12px/500/19.8px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 最近事项|button / — / —|—|68×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(146, 63, 48) / rgba(0, 0, 0, 0)|/ 7px|
|overview / hall-overview|button · 需要我处理|button / — / —|—|81×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 案卷|button / — / —|—|42×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 打开百宝箱 →|button / — / —|—|105.34×42|12px/500/19.8px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 聚义厅 厅中实景 · 去梁山走一走 →|button / — / —|—|300×176|15px/500/22.5px|20px 18px；0px；normal|rgb(255, 249, 233) / rgba(0, 0, 0, 0)|1px solid rgb(202, 199, 181) / 11px|
|overview / hall-overview|button · 查看待处理列表 →|button / — / —|—|258×36|13px/500/21.45px|7px 0px；0px；normal|rgb(146, 63, 48) / rgba(0, 0, 0, 0)|0px none rgb(146, 63, 48) / 7px|
|overview / hall-overview|button · 打开点将册 →|button / — / —|—|258×36|13px/500/21.45px|7px 0px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(36, 46, 43) / 7px|
|tasks / panel-overlay is-workbench-panel|button · 关闭面板|button / — / Label=关闭面板|—|36×36|15px/500/24.75px|0px 12px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 竖向|button / — / Label=切换竖向布局|—|54×36|14px/500/23.1px|0px 12px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|1px solid rgb(200, 173, 132) / 8px|
|tasks / panel-overlay is-workbench-panel|input · 查榜号|— / — / —|—|640.13×38|13.3333px/400/normal|0px 10px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|tasks / panel-overlay is-workbench-panel|select · 不拘本领|— / — / —|—|150×36|13.3333px/400/normal|0px 10px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 重查|— / — / —|—|64.94×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 张榜|button / — / —|—|64.94×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 起草正式任务|button / — / —|—|102×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 起草交办|button / — / —|—|76×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 待点将 0|— / — / —|—|99×34|15px/400/24.75px|0px 10px；0px；6px|rgb(255, 248, 232) / rgb(124, 31, 27)|0px none rgb(255, 248, 232) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 已点将 0|— / — / —|—|99×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 在办 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 交令 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 失手 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 入档 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 关闭面板|button / — / Label=关闭面板|—|36×36|15px/500/24.75px|0px 12px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 竖向|button / — / Label=切换竖向布局|—|54×36|14px/500/23.1px|0px 12px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|1px solid rgb(200, 173, 132) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 引用资料|button / — / Label=引用资料,Expanded=false|—|68×34|12px/400/19.8px|0px 8px；0px；4px|rgb(96, 67, 35) / rgb(231, 219, 196)|0px none rgb(96, 67, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 百宝箱|button / — / Label=打开百宝箱|—|56×34|12px/400/19.8px|0px 8px；0px；4px|rgb(93, 54, 28) / rgb(234, 211, 169)|0px none rgb(93, 54, 28) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 重取回话|button / — / Label=重取回话|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 话头记录|button / — / Label=话头记录,Expanded=false|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 另起话头|button / — / Label=另起话头|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(255, 248, 232) / rgb(109, 63, 31)|0px none rgb(255, 248, 232) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|textarea · 向众好汉传话，或 @某位好汉|— / — / —|—|1084×44|15px/400/21.75px|11px 12px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 传令|submit / — / Label=传令 / disabled|—|42×44|13.3333px/400/normal|1px 6px；0px；normal|rgb(255, 248, 232) / rgb(127, 74, 34)|0px none rgb(255, 248, 232) / 8px|
|library / panel-overlay is-workbench-panel|button · 典籍阅读|button / tab / Selected=true|—|80×38.75|15px/400/24.75px|7px 10px；0px；normal|rgb(255, 248, 232) / rgb(35, 72, 62)|0px none rgb(255, 248, 232) / 7px|
|library / panel-overlay is-workbench-panel|button · 案卷检索|button / tab / Selected=false|—|80×38.75|15px/400/24.75px|7px 10px；0px；normal|rgb(63, 40, 21) / rgb(234, 218, 187)|0px none rgb(63, 40, 21) / 7px|
|library / panel-overlay is-workbench-panel|button · 重试|button / — / —|—|52×40.75|15px/400/24.75px|8px 11px；0px；normal|rgb(63, 40, 21) / rgb(234, 218, 187)|0px none rgb(63, 40, 21) / 7px|
|treasure / panel-overlay is-workbench-panel|button · 上传资料|button / — / —|—|94×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(255, 249, 238) / rgb(141, 64, 44)|1px solid rgb(141, 64, 44) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 全部|button / — / —|—|60×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(141, 64, 44) / rgba(0, 0, 0, 0)|/ 0px|
|treasure / panel-overlay is-workbench-panel|button · 资料|button / — / —|—|60×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|button · 成果|button / — / —|—|60×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|button · 回收站|button / — / —|—|76×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|input · 搜索文件名称|— / — / —|—|360×44|13px/700/21.45px|10px 12px；0px；normal|rgb(81, 57, 34) / rgb(255, 253, 248)|1px solid rgb(213, 189, 152) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 搜索|submit / — / —|—|62×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|1px solid rgb(213, 189, 152) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 重新读取|button / — / —|—|86×44|14px/400/22.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|1px solid rgb(213, 189, 152) / 4px|
|agents / panel-overlay is-workbench-panel|button · 全寨|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(255, 255, 255) / rgb(35, 72, 62)|0px none rgb(255, 255, 255) / 8px|
|agents / panel-overlay is-workbench-panel|button · 候命|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 办事|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 出征|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 失联|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 招贤令|button / — / —|—|51×23.44|13px/400/21.45px|1px 6px；0px；normal|rgb(0, 0, 0) / rgb(239, 239, 239)|0px none rgb(0, 0, 0) / 0px|
|messages / hall-overview is-messages|button · 刷新|button / — / — / disabled|—|52×37.8|12px/400/19.8px|9px 14px；0px；normal|rgb(88, 62, 40) / rgba(0, 0, 0, 0)|0px none rgb(88, 62, 40) / 4px|

## 390×844（常规字体，仅视口内）

|来源页 / 区域|控件（标签·文案）|type / role / aria|href → 目标|W×H|字体大小 / 字重 / 行高|padding；margin；gap|文字 / 背景|边框 / 半径|
|---|---|---|---|---|---|---|---|---|
|overview / hall-app-header|button · 聚义厅|button / — / —|—|75×44.05|17px/400/28.05px|8px 12px；0px；12px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · 消息|button / — / Label=查看消息|—|56×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · 账户|button / — / Label=个人中心|—|56×42.75|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-app-header|button · 全部入口|button / — / Label=全部入口,Expanded=false|—|46×40|15px/400/24.75px|8px 12px；0px；normal|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / workbench-mobile-nav|button · 办事概览|button / — / Current=page|—|91.5×51|11px/400/18.15px|5px；0px；4px|rgb(146, 63, 48) / rgb(246, 238, 232)|0px none rgb(146, 63, 48) / 7px|
|overview / workbench-mobile-nav|button · 我的事项|button / — / —|—|91.5×51|11px/400/18.15px|5px；0px；4px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / workbench-mobile-nav|button · 厅内议事|button / — / —|—|91.5×51|11px/400/18.15px|5px；0px；4px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / workbench-mobile-nav|button · 典籍阁|button / — / —|—|91.5×51|11px/400/18.15px|5px；0px；4px|rgb(104, 113, 107) / rgba(0, 0, 0, 0)|0px none rgb(104, 113, 107) / 7px|
|overview / hall-overview|button · 提出需求|button / — / —|—|70×42|12px/500/19.8px|9px 10px；0px；normal|rgb(255, 254, 250) / rgb(146, 63, 48)|1px solid rgb(146, 63, 48) / 7px|
|overview / hall-overview|button · 先聊一聊|button / — / —|—|70×42|12px/500/19.8px|9px 10px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 悬赏榜|button / — / —|—|64×37.8|12px/500/19.8px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 刷新|button / — / — / disabled|—|52×37.8|12px/500/19.8px|9px 14px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 最近事项|button / — / —|—|68×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(146, 63, 48) / rgba(0, 0, 0, 0)|/ 7px|
|overview / hall-overview|button · 需要我处理|button / — / —|—|81×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 案卷|button / — / —|—|42×47.44|13px/500/21.45px|12px 8px；0px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|0px none rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 打开百宝箱 →|button / — / —|—|105.34×42|12px/500/19.8px|9px 14px；0px 0px 0px 184.656px；normal|rgb(36, 46, 43) / rgba(0, 0, 0, 0)|1px solid rgb(227, 229, 220) / 7px|
|overview / hall-overview|button · 聚义厅 厅中实景 · 去梁山走一走 →|button / — / —|—|358×185|15px/500/22.5px|20px 18px；0px；normal|rgb(255, 249, 233) / rgba(0, 0, 0, 0)|1px solid rgb(202, 199, 181) / 11px|
|tasks / panel-overlay is-workbench-panel|button · 关闭面板|button / — / Label=关闭面板|—|36×34|15px/500/24.75px|0px 9px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 竖向|button / — / Label=切换竖向布局|—|48×34|14px/500/23.1px|0px 9px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|1px solid rgb(200, 173, 132) / 8px|
|tasks / panel-overlay is-workbench-panel|input · 查榜号|— / — / —|—|358×38|13.3333px/400/normal|0px 10px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|tasks / panel-overlay is-workbench-panel|select · 不拘本领|— / — / —|—|358×36|13.3333px/400/normal|0px 10px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 重查|— / — / —|—|358×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 张榜|button / — / —|—|64.94×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 起草正式任务|button / — / —|—|102×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 起草交办|button / — / —|—|76×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 待点将 0|— / — / —|—|99×34|15px/400/24.75px|0px 10px；0px；6px|rgb(255, 248, 232) / rgb(124, 31, 27)|0px none rgb(255, 248, 232) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 已点将 0|— / — / —|—|99×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 在办 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|tasks / panel-overlay is-workbench-panel|button · 交令 0|— / — / —|—|84×34|15px/400/24.75px|0px 10px；0px；6px|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 关闭面板|button / — / Label=关闭面板|—|36×34|15px/500/24.75px|0px 9px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 竖向|button / — / Label=切换竖向布局|—|48×34|14px/500/23.1px|0px 9px；0px；normal|rgb(74, 52, 35) / rgba(0, 0, 0, 0)|1px solid rgb(200, 173, 132) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 引用资料|button / — / Label=引用资料,Expanded=false|—|68×34|12px/400/19.8px|0px 8px；0px；4px|rgb(96, 67, 35) / rgb(231, 219, 196)|0px none rgb(96, 67, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 百宝箱|button / — / Label=打开百宝箱|—|56×34|12px/400/19.8px|0px 8px；0px；4px|rgb(93, 54, 28) / rgb(234, 211, 169)|0px none rgb(93, 54, 28) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 重取回话|button / — / Label=重取回话|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 话头记录|button / — / Label=话头记录,Expanded=false|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 另起话头|button / — / Label=另起话头|—|34×34|12px/400/19.8px|1px 6px；0px；normal|rgb(255, 248, 232) / rgb(109, 63, 31)|0px none rgb(255, 248, 232) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|textarea · 向众好汉传话，或 @某位好汉|— / — / —|—|312×44|15px/400/21.75px|11px 12px；0px；normal|rgb(63, 40, 21) / rgb(255, 253, 246)|1px solid rgb(215, 195, 162) / 8px|
|chat / panel-overlay is-chat-overlay is-workbench-panel|button · 传令|submit / — / Label=传令 / disabled|—|38×44|13.3333px/400/normal|1px 6px；0px；normal|rgb(255, 248, 232) / rgb(127, 74, 34)|0px none rgb(255, 248, 232) / 8px|
|library / panel-overlay is-workbench-panel|button · 典籍阅读|button / tab / Selected=true|—|80×38.75|15px/400/24.75px|7px 10px；0px；normal|rgb(255, 248, 232) / rgb(35, 72, 62)|0px none rgb(255, 248, 232) / 7px|
|library / panel-overlay is-workbench-panel|button · 案卷检索|button / tab / Selected=false|—|80×38.75|15px/400/24.75px|7px 10px；0px；normal|rgb(63, 40, 21) / rgb(234, 218, 187)|0px none rgb(63, 40, 21) / 7px|
|library / panel-overlay is-workbench-panel|button · 重试|button / — / —|—|52×40.75|15px/400/24.75px|8px 11px；0px；normal|rgb(63, 40, 21) / rgb(234, 218, 187)|0px none rgb(63, 40, 21) / 7px|
|treasure / panel-overlay is-workbench-panel|button · 上传资料|button / — / —|—|94×44.39|16px/400/26.4px|8px 14px；0px；normal|rgb(255, 249, 238) / rgb(141, 64, 44)|1px solid rgb(141, 64, 44) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 全部|button / — / —|—|56×44.39|16px/400/26.4px|8px 12px；0px；normal|rgb(141, 64, 44) / rgba(0, 0, 0, 0)|/ 0px|
|treasure / panel-overlay is-workbench-panel|button · 资料|button / — / —|—|56×44.39|16px/400/26.4px|8px 12px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|button · 成果|button / — / —|—|56×44.39|16px/400/26.4px|8px 12px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|button · 回收站|button / — / —|—|72×44.39|16px/400/26.4px|8px 12px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|0px none rgb(83, 57, 34) / 0px|
|treasure / panel-overlay is-workbench-panel|input · 搜索文件名称|— / — / —|—|290.08×44|13px/700/21.45px|10px 12px；0px；normal|rgb(81, 57, 34) / rgb(255, 253, 248)|1px solid rgb(213, 189, 152) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 搜索|submit / — / —|—|55.92×70.78|16px/400/26.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|1px solid rgb(213, 189, 152) / 4px|
|treasure / panel-overlay is-workbench-panel|button · 重新读取|button / — / —|—|86×44|14px/400/22.4px|8px 14px；0px；normal|rgb(83, 57, 34) / rgba(0, 0, 0, 0)|1px solid rgb(213, 189, 152) / 4px|
|agents / panel-overlay is-workbench-panel|button · 全寨|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(255, 255, 255) / rgb(35, 72, 62)|0px none rgb(255, 255, 255) / 8px|
|agents / panel-overlay is-workbench-panel|button · 候命|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 办事|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 出征|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 失联|— / — / —|—|50×36|13px/400/21.45px|0px 12px；0px；normal|rgb(74, 52, 35) / rgb(239, 224, 198)|0px none rgb(74, 52, 35) / 8px|
|agents / panel-overlay is-workbench-panel|button · 招贤令|button / — / —|—|358×23.44|13px/400/21.45px|1px 6px；0px；normal|rgb(0, 0, 0) / rgb(239, 239, 239)|0px none rgb(0, 0, 0) / 0px|
|messages / hall-overview is-messages|button · 刷新|button / — / — / disabled|—|52×37.8|12px/400/19.8px|9px 14px；0px；normal|rgb(88, 62, 40) / rgba(0, 0, 0, 0)|0px none rgb(88, 62, 40) / 4px|

## 链接归属与限制

- 工作台新增的侧栏、顶栏、底栏、地图卡与典籍双页签均为 `button`，**DOM href 为 null**，按本文 `ui-detail.md` 的动作表在 `/juyiting` 内根切换；“账户”按钮调用 Vue Router 导向 `/profile`，不要误认为按钮带 href。
- 另外还可在**原全局抽屉（关闭时 x=-240，当前不在视口）**观察到 `<a href="/profile">个人中心</a>`、`<a href="/messages">消息中心</a>`、`<a href="/help">帮助与反馈</a>`，属于现有全局导航，不能与工作台按钮的内部动作混写。详见 JSON `withinViewport=false` 与 `section=""`。样本内无外链和带查询参数的可见链接。
- 320×740、844×390 的控件行也保存在原始 JSON；本文只列 1440、390 两个代表样本以避免重复 660 行。静态 Demo 曾登记的 180 种控件目标另见 `../../docs/ui-workbench/control-targets.md`，**与这批正式页面控件不是一套属性**。

**授权账号补核（2026-09-24）**：典籍正文/进度、书签和笔记已只读显示，数据来自真实服务但未重新生成本文件的 660 条空响应 CSSOM 记录；不能将真实正文的可见性当作该索引已包含内页控件测量。源码中的条件外链（招贤令安装说明）、动态 Markdown 链接和版本 Blob 下载的 `href`/`target`/`rel` 边界见 [`ui-detail.md` §4](ui-detail.md#4-链接控件目的和页面返回)，缺少授权条件下 DOM 取样的项保持“未实测”。

**展开态补样**：`4feaa7d` 修复“全部入口”菜单的 `border-box` 宽度和短屏上下界；前序 `a935440` 进一步把宽度改为相对 `.juyi-page` 的百分比，320×320 外框 x15..305/y58..258，内部滚动后辅助项仍可聚焦；六个视口的完整矩形/scroll 与同批候选截图见 [`menu-short-screen-review.md`](evidence/menu-short-screen-review.md)。本文件前述 660 行/28 快照仍是**前序 `fe43ebc5` 的关闭态**，新证据只检查菜单容器与 10 个按钮存在/末项焦点，没有给 10 个按钮逐一重测 fontFamily/padding/边框，不能直接相加为 670 条。

**当前 `8f47a12` 极窄复排补样**：≤240px CSS 宽度只显示页头“全部入口”，消息/账户由该菜单保留；底栏前三项变图标但各自 `aria-label` 保留中文动作名，右下典籍阁仍显示字样，均是无 `href` 的 Vue 按钮；议事工具栏变为内部水平滚动。≤180px 标题视觉省略，但对话框的 `aria-labelledby` 仍能取得“厅内议事”名称。浏览器原始几何/按钮标签仅覆盖空数据四个半尺寸 CSS 视口，见 [`compact-reflow-review.md`](evidence/compact-reflow-review.md)，非先前 660 条控件 CSSOM 的增量全状态重采。
