# 当前实际页面 · 基线原型

**这是现状还原，不是新方案。** 2026-10-04 使用测试账号只读查看线上聚义厅，复用实际页面 DOM、已部署样式和现有图标资源；不是依据最新未发布源码猜测线上界面。后续只在这份基线上标注和修改，不再沿用上一版独立设计作为页面起点。

[打开基线原型](index.html) · [来源记录](baseline-source.json) · [浏览器检查](prototype-checks.json)

## 页面

通过现有侧栏/底部菜单和页面按钮浏览。没有新增顶部原型菜单或四步导航。

| 现有页面/状态 | 直接打开 | 桌面 | 移动端 |
|---|---|---|---|
| 办事首页 | [打开](index.html#home) | [图](screenshots/desktop-home.png) | [图](screenshots/mobile-home.png) |
| 我的事项/悬赏榜 | [打开](index.html#tasks) | [图](screenshots/desktop-tasks.png) | [图](screenshots/mobile-tasks.png) |
| 提出需求/张榜表单 | [打开](index.html#create) | [图](screenshots/desktop-create.png) | [图](screenshots/mobile-create.png) |
| 点将册 | [打开](index.html#agents) | [图](screenshots/desktop-agents.png) | [图](screenshots/mobile-agents.png) |
| 事项详情 | [打开](index.html#detail) | [图](screenshots/desktop-detail.png) | [图](screenshots/mobile-detail.png) |
| 榜文议事 | [打开](index.html#chat) | [图](screenshots/desktop-chat.png) | [图](screenshots/mobile-chat.png) |
| 资料/百宝箱 | [打开](index.html#workspace) | [图](screenshots/desktop-workspace.png) | [图](screenshots/mobile-workspace.png) |
| 我的 | [打开](index.html#mine) | [图](screenshots/desktop-mine.png) | [图](screenshots/mobile-mine.png) |
| 现有资料选择 | [打开](index.html#materials) | [图](screenshots/desktop-materials.png) | [图](screenshots/mobile-materials.png) |
| 现有参考图选择 | [打开](index.html#reference) | [图](screenshots/desktop-reference.png) | [图](screenshots/mobile-reference.png) |

## 还原边界

- 保留原有红褐色风格、桌面侧栏、移动底栏、页面组成、按钮位置与文案，不提前合入新方案。
- **当前线上仍有独立“参考图（可选）”与“生成图片”等旧入口，因此此版如实保留。** 这不是撤回统一资料需求，而是先建立对照基线，再按用户意见修改。
- 账号、头像、事项标题、文件名及内部标识改为示例；长列表保留代表性行。会话图片替换为明确示意图，未复制私有文件内容。它是可编辑页面原型，不是完整线上数据副本或逐像素截图承诺。
- 原型支持现有页面之间的跳转和基本输入/选择；未覆盖的动作提示原型边界，不伪报业务成功。新建、提交、点将执行、支付、保存和验收均不调用真实接口。
- 只采样了表中十个界面状态。地图游戏、个人设置、文件详情和完整 Agent 执行不在本次现状还原范围；未从上一版拼接新流程。
- 采样使用独立浏览器；除登录外只读访问，任务推荐等非读取请求被拦截，未发送聊天或调用 Provider。截图来自离线原型渲染，不是功能或发布验收。
- CSS 与本地公开资源来自部署目录，来源摘要见记录；没有导入生产应用 JS、登录态、密钥或 API 配置。原型通过 CSP 禁止网络业务请求，打开无需登录。

## 接下来怎么改

保留此基线；用户指出具体页面与改动后，在独立调整版复用相同页面，逐项改，不重做导航、主题或其他未要求部分。
