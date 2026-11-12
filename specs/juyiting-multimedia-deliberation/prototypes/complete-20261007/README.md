> **2026-10-07 原型入口纠正**：后续新需求统一基于[最近优化的UI原型](../../../juyiting-ui-baseline-20261006/prototype/index.html)及其页面/状态索引。本页的 `complete-20261007` / `adjusted` 是历史中间成果，不是当前界面基准；历史证据保留，真实业务仍 NOT_COMPLETE。

# 浏览器走查后的完整交互原型 · 2026-10-07

[打开主流程](index.html) · [分支与恢复场景](scenarios.html) · [线上走查与交互矩阵](../../page-interaction-prototype-20261007.md) · [浏览器检查](prototype-checks.json)

**离线设计原型，不是生产应用，不证明缺口已修复或多媒体业务已验收。** 复用已有current历史快照的外壳与样式，按本轮线上走查补交互。沿用现有红褐主题、侧栏、手机四项底栏、点将册和浮层议事；无新顶部导航、无多选验收、无“调整交付内容”、无集合状态机。保留 `current/` 与 `adjusted/` 作为历史对照。

## 主流程

1. 办事页输入明确需求，或只添加附件；可从资料库选择、预览、取消、确认、移除，也可用系统文件选择器添加本机示例文件。
2. 开始办事：明确成功后清空本次草稿和附件，进入点将册；失败或未知保留草稿，不自动提交第二次。
3. 选择好汉 → 点将并议事：自动带入原需求和固定资料。模糊需求/附件-only先演示自然澄清，明确需求演示回复。
4. 同一议事可继续补充、引用稿件修改；旧稿保留。图片放大、音频播放、文件/文字预览下载；保存到资料区是可选动作，不是验收前置。
5. 返回 → **同一事项详情** → 查看正式成果与验收 → 继续修改回原议事，或一次确认验收。验收中、失败、未知、完成分别展示，不把未知写成未完成；查询原操作不再次提交。
6. 完成后详情、首页和列表同步；刷新保留同一演示操作。成果只读，不能再次验收、发送或引用修改。事项状态筛选有空状态。

## 其他交互

- 点将册 → 指定好汉密议 → 返回点将册；每位好汉的消息、草稿与资料独立，不修改正式事项。密议中的保存仍是演示。
- 输入框只有“＋ / 发送”。“＋”内资料、语音输入、语音设置。录音、转写是明确示例：取消不改草稿，编辑后放入输入框，**不自动发送**，不启用麦克风。
- 本机文件只在原型标签内使用，不上传。不支持解析的格式明确提示；不冒充 PDF/Office/音频原生能力已经上线。
- 独立图片/文字 root 场景只展示阻塞与回原议事路径，**不伪造R01关联恢复入口**。其具体设计与真实实现仍待完成。
- 我的、账户、资金悬赏、招贤、收入案卷等非本次多媒体最短流程入口不伪造业务能力；保留既有外观和范围提示。

## 模拟边界

所有 Agent 回复、状态、操作ID与交付清单均为本地示例。图片是已有SVG插画，音频是2秒合成示意音，文档是固定示例，文字由规则分支产生，不是在线Agent输出。演示交付清单复用数组，不定义新的后端合同，不代表跨独立root自动关联可用。已保存文件可再次作为资料引用。

不同场景用独立 sessionStorage key；同标签刷新保留，关闭标签不承诺长期持久化。大文件受浏览器存储能力影响，原型不等于真实上传/持久化。刷新遇到待回复仅显示状态待核对，不自动重发；验收恢复只沿用原演示操作。成功示例不替代ACL、CAS、身份隔离与服务端真实回执。

CSP `connect-src 'none'`，无API、账号、Provider、扣费、业务写入。本轮没有Web/API源码修复、Flow构建或版本部署。

## 截图与复核

| 场景 | 桌面/异常 | 手机 |
|---|---|---|
| 首页与资料 | [首页](screenshots/desktop-home.png) / [资料](screenshots/desktop-materials.png) | [首页](screenshots/mobile-home.png) / [资料](screenshots/mobile-materials.png) |
| 点将与议事 | [点将](screenshots/desktop-agents.png) / [议事](screenshots/desktop-chat.png) | [议事](screenshots/mobile-chat-active.png) |
| 验收及只读结果 | [验收](screenshots/desktop-accept.png) / [完成](screenshots/desktop-complete.png) | [结果](screenshots/mobile-accept.png) |
| 密议与保存 | [密议](screenshots/desktop-private.png) / [资料区](screenshots/desktop-workspace.png) | [密议](screenshots/mobile-private.png) |
| 草稿保留 | [失败](screenshots/create-failure.png) / [未知](screenshots/create-unknown.png) | 核对完成条件见矩阵 |
| 验收恢复 | [失败](screenshots/accept-failure.png) / [未知](screenshots/accept-unknown.png) | 核对完成条件见矩阵 |
| 待实现边界 | [独立root](screenshots/independent-roots.png) | R01未实现 |

轻量浏览器复核（不是产品构建）：在本目录的父目录启动静态HTTP服务，然后 `node check.cjs`；默认服务根 `http://127.0.0.1:35111`，可用 `PROTOTYPE_ORIGIN` 指定。脚本只启动并关闭自己的临时Chromium，不操作共享服务。

## 本轮最终复核结果

Chromium真实点击/渲染：33项交互检查通过，37项布局观察通过，0浏览器异常；覆盖1440、390、320px及8个分支入口。测试绑定源文件SHA，见prototype-checks.json；这里只是离线原型PASS，线上缺口与全产品验收仍NOT_COMPLETE。
