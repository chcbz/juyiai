# 聚义厅 63 条功能逐条复核索引（正式候选 vs 原型）

2026-09-23。本表按旧 [Demo 功能覆盖清单](../../docs/ui-workbench/feature-coverage.md) **F01–F63 一一对照**，检查的是本地 `web` 基线候选 `fe43ebc5`（当前 `8f47a12` 相对于该基线仅增加手机菜单限界与极窄/极短复排 CSS/相应测试）上原 Vue 组件/Router 的保留与入口（非线上账号功能实测）。**判定“保留”只表示代码链路没有被 Demo 假页面替换，不是对应 API/权限/数据已通过验收**。行为边界、缺陷与真实操作见 [接入复核](feature-integration-audit.md)、[验收进度](acceptance.md)、[真实服务复核步骤](real-service-qa.md)。旧清单里的“缺失/偏差”判的是**静态 Demo**，不能移植为本正式候选的判定。

复核方法：正式 `/juyiting` 的 `JuyiHall.vue` → 原业务组件（下表文件）→ 原回调/路由；登录/外部模块仅核对 Router 和原组件未删除；本地四视口空 API 只观察顶层可达，不写入后端；后续补充的授权账号**局部只读**观察不改变下表静态判定等级，见 `evidence/real-readonly-browser-20260924.md`。每行的路径是**源码定位**而不是页面 `href`。本表的审计范围是这 63 条，**不是全站所有模块或所有状态的全集**。

|编号|原清单能力|正式候选链路定位|本轮结论|需要的补充验证/边界|
|---|---|---|---|---|
|F01|默认工作台、地图可达|`web/src/components/world/JuyiHall.vue`|布局/入口已测；行为待授权验收|本地空 API 可见入口/布局；真实身份、数据、软键盘或实景行为待测。|
|F02|最近/待处理/案卷概览|`web/src/components/juyiting/HallOverview.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F03|概览分区重试与分页|`web/src/components/juyiting/HallOverview.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F04|原正式任务/私人事项/旧执行/草稿入口|`web/src/components/juyiting/HallOverview.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F05|消息中心的待处理语义|`web/src/components/juyiting/HallOverview.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F06|事项状态、本领筛选|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F07|按榜号查榜|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F08|原张榜表单与本领要求|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F09|简述型正式任务创建|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F10|正式旧稿不支持字段处置|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F11|私人交办输入/目标选择|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F12|账号草稿恢复、放弃、修订冲突|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F13|资料选择与预览返回|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F14|交办授权、外部服务与费用告知|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F15|提交不明核对、离开保存屏障|`web/src/components/world/JuyiHall.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F16|私人事项执行历史与修改再执行|`web/src/components/juyiting/HallDraftEditor.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F17|个人归档、撤销归档、成果已查看|`web/src/components/juyiting/HallPrivateMark.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F18|正式成果批次与固定版本下载|`web/src/components/deliveries/FormalDeliveryList.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F19|正式验收与退回修改|`web/src/components/deliveries/FormalDeliveryList.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F20|单好汉显式指派|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F21|多好汉指派|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F22|宋江自动点将|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F23|候选推荐和匹配解释|`web/src/components/juyiting/BountyPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F24|团队推荐预演|`web/src/components/juyiting/TeamRecommendationPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F25|工作项规划|`web/src/components/juyiting/WorkItemPlanPanel.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F26|资金悬赏/报价/撤销/结算|`web/src/components/juyiting/BountyPanel.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F27|任务协作工作台|`web/src/components/juyiting/TaskWorkspacePanel.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F28|协作文件传输与成果治理|`web/src/components/world/JuyiHall.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F29|点将册列表/状态/能力/详情|`web/src/components/world/JuyiHall.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F30|地图与点将册数据独立|`web/src/components/world/JuyiHall.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F31|108好汉招募与接入|`web/src/components/juyiting/PersonaCatalogPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F32|接入参数、命令复制与安装链接|`web/src/components/juyiting/PersonaCatalogPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F33|服务端托管|`web/src/components/juyiting/HostingRentPanel.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F34|公议/私议/事项议事|`web/src/components/juyiting/ChatPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F35|真正新建会话|`web/src/components/juyiting/ChatPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F36|历史选取/删除/分页|`web/src/components/juyiting/HallConversationHistory.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F37|@好汉与清除目标/草稿|`web/src/components/juyiting/HallChatComposer.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F38|议事固定版本资料增删|`web/src/components/juyiting/ChatPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F39|流式回复/加载失败/恢复重试|`web/src/components/juyiting/ChatPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F40|语音交互|`web/src/components/world/JuyiHall.vue`|条件入口保留，取决于开关/权限|条件能力默认可关闭；需在目标构建+授权主体下验证。|
|F41|聊天空间与独立滚动|`web/src/components/juyiting/ChatPanel.vue`|布局/入口已测；行为待授权验收|本地空 API 可见入口/布局；真实身份、数据、软键盘或实景行为待测。|
|F42|文件分类/搜索/预览/下载|`web/src/components/workspace/PersonalWorkspace.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F43|上传确认与显示名|`web/src/components/workspace/PersonalWorkspace.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F44|文件版本、追加、重命名|`web/src/components/workspace/PersonalWorkspace.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F45|回收站/引用次数确认/恢复|`web/src/components/workspace/PersonalWorkspace.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F46|文件载入/错误/空/分页|`web/src/components/workspace/PersonalWorkspace.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F47|典籍阅读/案卷检索双入口|`web/src/components/juyiting/LibraryPanel.vue`|布局/入口已测；行为待授权验收|本地空 API 可见入口/布局；真实身份、数据、软键盘或实景行为待测。|
|F48|水浒传目录/章节/阅读进度|`web/src/components/juyiting/archive/ArchiveReader.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F49|书签添加/打开/删除|`web/src/components/juyiting/archive/ArchiveReader.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F50|私人笔记增改删|`web/src/components/juyiting/archive/ArchiveReader.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F51|选段提问/重试/引用起草|`web/src/components/juyiting/archive/ArchiveReader.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F52|案卷关键词/来源过滤/引用|`web/src/components/juyiting/LibraryPanel.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F53|沉浸阅读及横竖屏安全区|`web/src/components/juyiting/archive/ArchiveReader.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F54|地图拖动缩放/场所/好汉入口|`web/src/components/world/JuyiHall.vue`|布局/入口已测；行为待授权验收|本地空 API 可见入口/布局；真实身份、数据、软键盘或实景行为待测。|
|F55|实时场景、移动、气泡、模拟、声音|`web/src/components/world/JuyiHall.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F56|横竖屏/只读实景预览|`web/src/components/world/JuyiHall.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F57|新手引导/访客模板交接|`web/src/components/world/JuyiHallEntry.vue`|原组件链路保留；服务行为待验|原型缺口不可用静态 UI 补；需要以真实服务复测权限、失败/冲突与写操作。|
|F58|个人资料权威读取与错误|`web/src/components/UserProfile.vue`|既有组件/路由入口保留（仅静态）|全站路由/身份能力在厅外；生产 OAuth 登录及 `/user/my` 200 已另证实，但**候选部署的回调/CORS、厅外页面及安全写操作未验**。|
|F59|退出当前设备/全部设备确认|`web/src/components/UserProfile.vue`|既有组件/路由入口保留（仅静态）|全站路由/身份能力在厅外；生产 OAuth 登录及 `/user/my` 200 已另证实，但**候选部署的回调/CORS、厅外页面及安全写操作未验**。|
|F60|运行看板与经济发现入口|`web/src/components/UserProfile.vue`|既有组件/路由入口保留（仅静态）|全站路由/身份能力在厅外；生产 OAuth 登录及 `/user/my` 200 已另证实，但**候选部署的回调/CORS、厅外页面及安全写操作未验**。|
|F61|登录/回调与会话恢复|`web/src/router/index.js`|既有组件/路由入口保留（仅静态）|全站路由/身份能力在厅外；生产 OAuth 登录及 `/user/my` 200 已另证实，但**候选部署的回调/CORS、厅外页面及安全写操作未验**。|
|F62|偏好设置|`web/src/components/world/JuyiHall.vue`|原型新增偏好，非旧功能（未移植）|原型的字号/色温偏好不是既有账号设置；若要求上线，应另列需求与持久化合同。|
|F63|弹层返回、焦点与移动导航|`web/src/components/world/JuyiHall.vue`|布局/入口已测；行为待授权验收|本地空 API 可见入口/布局；真实身份、数据、软键盘或实景行为待测。|

**核对合计**：63/63 条有明确边界；5 条入口/布局本地观察，6 条条件入口需有能力时测试，4 条全站入口仅做保留检查，1 条（F62）是 Demo 自设偏好而非现有功能，其余 47 条只做静态组件链路复核。上述类别**不是通过率**，不能把 63/63 误读为 63 条功能可用。正式页没有把静态 Demo 的假数据、假回复、TXT 下载或阅读样章部署进来；系统运行状态取决于既有组件/后端/身份。真正的验收门禁仍是 `acceptance.md` A1–A7。

**补充**：2026-09-24 的真实只读证据将概览、地图/名册目录、典籍章回和会话列表的部分读取提升为已观察；F01–F63 原始分类专指 2026-09-23 的“源码/空数据布局”取证批次，不随附带读请求自动变成“业务通过”。七入口和待测项的更新总表见 `feature-integration-audit.md`。
