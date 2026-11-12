# 实施设计

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：聚义厅轻量工作台真实功能入口。**

### 最小责任链
Web复用现有业务组件和权威API；原型定义布局，不能提供生产假数据。

办事/事项/资料/我的入口→对应现有业务页→返回保留必要上下文。

### 实施约束
地图和点将册数据独立；不因新布局开启语音/资金/协作功能开关；63项历史追踪不是所有功能完成证明。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


1. 展示层：`useHallHomeMode()`首次默认 overview；地图继续由HallStage持有，回到地图保持同一个Stage实例/草稿/会话。工作台导航独立于 Stage，桌面侧栏216px、移动四宫格底栏62px + safe-area；左侧次级菜单进入原有 panel（而非替换）。
2. 业务层：`JuyiHall.vue`中的HallOverview、BountyPanel、ChatPanel、PersonalWorkspace、LibraryPanel、HallDraftEditor、FormalDeliveryList、HallPrivateMark、PersonaCatalogPanel继续拥有真实数据/异常/重试；`/agent/map`和`/agent/roster`不合流。路由 `/juyiting` 不改，登录/账号仍导航现有真实路由。
3. 弹层导航：只有顶层面板从工作台标签切换才替换panel栈；草稿未保存离开依旧经过原有保存屏障；内层返回、焦点和用户上下文继续使用原会话管理。详情/草稿仍为modal；任务/好汉/议事/百宝箱/典籍阁为工作区宽页面。
4. 议事：使用现有真实聊天室（包括历史/引用/流式/失败），布局仅允许消息区独立滚动，输入区固定可见，软键盘/短横屏需回归。消息与资料不转为Demo样例。
5. 视觉：正式实现态的字号/字体栈/距离/尺寸/色值/断点/按钮语义与路由详设以本目录 `ui-detail.md`、`ui-computed-attributes.md`、`ui-control-attributes.md` 及对应 evidence 为准；`docs/ui-workbench/ui-detail.md` 仅为 V3.1 静态 Demo 的历史实测基线，不等于正式组件细节。CSS 覆盖仅作用于工作台与现有组件包装层，地图的沉浸美术不改。保留焦点与按键可访问性；本地截图/空 API 测量不代替真实账号验收。
6. 后端合同：本特性无新增API或事件；保留当前组件原请求/响应/error/认证/授权与异步恢复语义。身份、权限、版本、SSE/WS及重放均由已有组件负责，不用 UI 假状态绕过。
