# 正式 Vue 工作台 · CSS 计算属性附表（只读空 API fixture）

数据为 `evidence/computed-live-fixture.json` 的 Chromium 142 样本，CSS px。**这不是静态 Demo，也不是实际服务端登录或功能 E2E。** UI=本功能的无衬线回退栈，衬线=品牌回退栈，组件原样=原业务组件自身字体；精确 fontFamily、fontWeight、min/max、overflow、定位、aria 与 href 原值见证据 JSON。表中 W×H 为样本边界框，不能作为固定 CSS 宽高。`—` 表示此视口不存在/不显示，不是固定 0。颜色为计算 `rgb/rgba`，P/M 为 CSS `padding/margin`，gap `normal` 表示无显式 gap（不等于无间距）。

## 框架与概览（办事概览；1440×900 对比 390×844）

|选择器|桌面 W×H|桌面字体(族/大小/重/行高)|桌面 P / M / gap|手机 W×H|手机字体(族/大小/重/行高)|手机 P / M / gap|圆角(桌/手机)|文字 / 背景（桌/手机）|
|---|---|---|---|---|---|---|---|---|
|`.juyi-page`|1440.0×900.0|UI 15px/400/24.75px|0px / 0px / normal|390.0×844.0|UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|`.hall-workbench-sidebar`|216.0×900.0|UI 15px/400/24.75px|28px 15px 16px / 0px / normal|—|—|—|0px / —|rgb(36, 46, 43) / rgb(255, 254, 250)；—|
|`.workbench-brand`|185.0×54.0|衬线 23px/500/27.6px|0px 5px / 0px / 10px|—|—|—|0px / —|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；—|
|`.workbench-side-nav button`|185.0×44.0|UI 14px/500/20.3px|9px 12px / 0px / 12px|—|—|—|7px / —|rgb(146, 63, 48) / rgb(246, 238, 232)；—|
|`.workbench-map-entry`|185.0×66.0|UI 14px/500/20.3px|9px 12px / 0px 0px 14px / 12px|—|—|—|7px / —|rgb(36, 46, 43) / rgb(245, 244, 240)；—|
|`.hall-app-header`|1224.0×76.0|UI 15px/400/24.75px|12px 36px / 0px / 16px|390.0×64.0|UI 15px/400/24.75px|10px 16px / 0px / 8px|0px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|`.hall-header-tools`|297.2×42.8|UI 15px/400/24.75px|0px / 0px / 8px|168.0×42.8|UI 15px/400/24.75px|0px / 0px / 5px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|`.workbench-create-action`|105.2×42.8|UI 15px/400/24.75px|8px 12px / 0px / normal|—|—|—|7px / —|rgb(255, 254, 250) / rgb(146, 63, 48)；—|
|`.hall-portrait-home`|1224.0×824.0|UI 15px/400/24.75px|0px / 0px / 0px|390.0×780.0|UI 15px/400/24.75px|0px 0px 62px / 0px / 0px|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|`.hall-overview`|1224.0×769.2|UI 15px/400/24.75px|30px 36px 36px / 0px / normal|390.0×1079.3|UI 15px/400/24.75px|22px 16px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|`.overview-hero h2`|1152.0×42.0|衬线 28px/500/42px|0px / 0px 0px 6px / normal|358.0×37.5|衬线 25px/500/37.5px|0px / 0px 0px 6px / normal|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|`.overview-hero-actions button`|86.0×43.1|UI 14px/500/23.1px|9px 14px / 0px / normal|70.0×42.0|UI 12px/500/19.8px|9px 10px / 0px / normal|7px / 7px|rgb(255, 254, 250) / rgb(146, 63, 48)；rgb(255, 254, 250) / rgb(146, 63, 48)|
|`.overview-columns`|1152.0×520.2|UI 15px/400/24.75px|0px / 0px / 24px|358.0×834.0|UI 15px/400/24.75px|0px / 0px / 18px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|`.overview-main`|828.0×248.9|UI 15px/400/24.75px|22px 24px 0px / 0px / normal|358.0×294.9|UI 15px/400/24.75px|18px 16px 0px / 0px / normal|11px / 11px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|`.overview-list-heading`|778.0×37.8|UI 15px/400/24.75px|0px / 0px 0px 8px / 12px|324.0×37.8|UI 15px/400/24.75px|0px / 0px 0px 8px / 12px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|`.overview-tabs`|778.0×48.4|UI 15px/400/24.75px|0px / 0px / 10px|324.0×48.4|UI 15px/400/24.75px|0px / 0px / 10px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|`.overview-resource`|778.0×87.9|UI 15px/400/24.75px|20px / 18px 0px 0px / 12px|324.0×137.9|UI 15px/400/24.75px|18px 16px / 18px 0px 0px / 12px|11px / 11px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|`.overview-map-link`|300.0×176.0|衬线 15px/500/22.5px|20px 18px / 0px / normal|358.0×185.0|衬线 15px/500/22.5px|20px 18px / 0px / normal|11px / 11px|rgb(255, 249, 233) / rgba(0, 0, 0, 0)；rgb(255, 249, 233) / rgba(0, 0, 0, 0)|
|`.overview-aside-card`|300.0×168.0|UI 15px/400/24.75px|20px / 0px / normal|358.0×164.0|UI 15px/400/24.75px|18px / 0px / normal|11px / 11px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|`.workbench-mobile-nav`|—|—|—|390.0×62.0|UI 15px/400/24.75px|5px 12px / 0px / normal|— / 0px|—；rgb(36, 46, 43) / rgb(255, 254, 250)|
|`.workbench-mobile-nav button`|—|—|—|91.5×51.0|UI 11px/400/18.15px|5px / 0px / 4px|— / 7px|—；rgb(146, 63, 48) / rgb(246, 238, 232)|

**边框**：样本的每个选择器 `style.borderColor` 等完整值记录在 JSON；工作台主要分割线 `#E3E5DC` 1px，`borderRadius` 在表中实测，不能将样本无边框元素的默认 `borderColor` 误解为有边框。

## 业务表面（每页新增部分；共用框架不重复）

|页面|选择器|桌面 W×H；字体|桌面 P / M / gap|手机 W×H；字体|手机 P / M / gap|圆角(桌/手机)|文字 / 背景（桌/手机）|
|---|---|---|---|---|---|---|---|
|tasks|`.panel-overlay`|1224.0×824.0；UI 15px/400/24.75px|16px 24px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|tasks|`.floating-panel`|1176.0×792.0；UI 15px/400/24.75px|0px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|12px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|tasks|`.panel-title`|1174.0×57.0；UI 15px/500/24.75px|10px 20px / 0px / 12px|390.0×47.0；UI 15px/500/24.75px|6px 16px / 0px / 6px|0px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|tasks|`.panel-close`|36.0×36.0；UI 15px/500/24.75px|0px 12px / 0px / normal|36.0×34.0；UI 15px/500/24.75px|0px 9px / 0px / normal|8px / 8px|rgb(74, 52, 35) / rgba(0, 0, 0, 0)；rgb(74, 52, 35) / rgba(0, 0, 0, 0)|
|tasks|`.panel-toolbar`|1174.0×62.0；UI 13px/400/21.45px|12px 16px / 0px / 10px|390.0×198.0；UI 13px/400/21.45px|12px 16px / 0px / 10px|0px / 0px|rgb(118, 95, 64) / rgba(0, 0, 0, 0)；rgb(118, 95, 64) / rgba(0, 0, 0, 0)|
|tasks|`.bounty-panel`|1174.0×733.0；UI 15px/400/24.75px|0px / 0px / normal|390.0×671.0；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|chat|`.panel-overlay`|1224.0×824.0；UI 15px/400/24.75px|16px 24px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|chat|`.floating-panel`|1176.0×792.0；UI 15px/400/24.75px|0px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|12px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|chat|`.panel-title`|1174.0×57.0；UI 15px/500/24.75px|10px 20px / 0px / 12px|390.0×47.0；UI 15px/500/24.75px|6px 16px / 0px / 6px|0px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|chat|`.panel-close`|36.0×36.0；UI 15px/500/24.75px|0px 12px / 0px / normal|36.0×34.0；UI 15px/500/24.75px|0px 9px / 0px / normal|8px / 8px|rgb(74, 52, 35) / rgba(0, 0, 0, 0)；rgb(74, 52, 35) / rgba(0, 0, 0, 0)|
|chat|`.discussion-brief`|1174.0×72.5；UI 15px/400/24.75px|12px 14px / 0px / 10px|390.0×72.5；UI 15px/400/24.75px|12px 14px / 0px / 10px|0px / 0px|rgb(63, 40, 21) / rgb(245, 234, 214)；rgb(63, 40, 21) / rgb(245, 234, 214)|
|chat|`.chat-panel`|1174.0×660.5；UI 15px/400/24.75px|0px / 0px / normal|390.0×598.5；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(255, 250, 240)；rgb(36, 46, 43) / rgb(255, 250, 240)|
|chat|`.panel-toolbar`|1174.0×49.0；UI 12px/400/19.8px|8px 10px 6px / 0px / 8px|390.0×49.0；UI 12px/400/19.8px|8px 10px 6px / 0px / 8px|0px / 0px|rgb(118, 95, 64) / rgba(0, 0, 0, 0)；rgb(118, 95, 64) / rgba(0, 0, 0, 0)|
|chat|`.hall-messages`|1174.0×492.5；UI 15px/400/24.75px|16px 20px / 0px / normal|390.0×434.5；UI 15px/400/24.75px|10px 16px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(251, 243, 228)；rgb(36, 46, 43) / rgb(251, 243, 228)|
|chat|`.hall-chat-composer`|1174.0×118.9；UI 15px/400/24.75px|10px 20px 12px / 0px / 7px|390.0×114.9；UI 15px/400/24.75px|8px 16px 10px / 0px / 7px|0px / 0px|rgb(36, 46, 43) / rgb(255, 250, 240)；rgb(36, 46, 43) / rgb(255, 250, 240)|
|library|`.panel-overlay`|1224.0×824.0；UI 15px/400/24.75px|16px 24px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgb(245, 244, 240)；rgb(36, 46, 43) / rgb(245, 244, 240)|
|library|`.floating-panel`|1176.0×792.0；UI 15px/400/24.75px|0px / 0px / normal|390.0×718.0；UI 15px/400/24.75px|0px / 0px / normal|12px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|library|`.panel-title`|1174.0×57.0；UI 15px/500/24.75px|10px 20px / 0px / 12px|390.0×47.0；UI 15px/500/24.75px|6px 16px / 0px / 6px|0px / 0px|rgb(36, 46, 43) / rgb(255, 254, 250)；rgb(36, 46, 43) / rgb(255, 254, 250)|
|library|`.panel-close`|36.0×36.0；UI 15px/500/24.75px|0px 12px / 0px / normal|36.0×34.0；UI 15px/500/24.75px|0px 9px / 0px / normal|8px / 8px|rgb(74, 52, 35) / rgba(0, 0, 0, 0)；rgb(74, 52, 35) / rgba(0, 0, 0, 0)|
|library|`.library-tabs`|1146.0×38.8；UI 15px/400/24.75px|0px / 0px / 8px|362.0×38.8；UI 15px/400/24.75px|0px / 0px / 8px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|library|`.library-tabs button`|80.0×38.8；UI 15px/400/24.75px|7px 10px / 0px / normal|80.0×38.8；UI 15px/400/24.75px|7px 10px / 0px / normal|7px / 7px|rgb(255, 248, 232) / rgb(35, 72, 62)；rgb(255, 248, 232) / rgb(35, 72, 62)|
|library|`.library-panel`|1174.0×733.0；UI 15px/400/24.75px|14px / 0px / 12px|390.0×671.0；UI 15px/400/24.75px|14px / 0px / 12px|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|
|treasure|`.personal-workspace`|1174.0×733.0；UI 16px/400/26.4px|28px 30px / 0px / normal|390.0×671.0；UI 16px/400/26.4px|20px 16px / 0px / normal|0px / 0px|rgb(63, 40, 24) / rgb(255, 249, 237)；rgb(63, 40, 24) / rgb(255, 249, 237)|
|agents|`.agent-panel`|1174.0×733.0；UI 15px/400/24.75px|0px / 0px / normal|390.0×671.0；UI 15px/400/24.75px|0px / 0px / normal|0px / 0px|rgb(36, 46, 43) / rgba(0, 0, 0, 0)；rgb(36, 46, 43) / rgba(0, 0, 0, 0)|

## 其余断点、控件和未采样区域

- `320×740` 与 `844×390` 的同一 7 个页面、全部采样元素的 rect/字号/字重/行高/字距/边距/gap/颜色/边框/半径/overflow/zIndex、可见性与语义属性在 `evidence/computed-live-fixture.json` 中；采样共 28 条视口×页面记录，37 个选择器（单页未必全部可见）。特别是 844×390 的议事消息区为 129.06px，不能把 390×844 的尺寸直接外推到横屏。
- `docs/ui-workbench/component-attributes.md`、`control-targets.md` 和 `evidence/computed-ui.json` 记录的是 **Demo 当时 38 场景的 5,139 个节点**，不是 Vue 正式页 CSS；参照设计可查，但不能用它来宣称本表以外的正式页面已按 Demo 实现。
- 本表只是可采样的工作台外壳及 4 个顶层内容容器，不枚举内层旧业务组件的每个按钮、页签、文件行、典籍正文/侧栏。那些样式遵循各自 Vue `<style>` 与组件条件分支。缺真实身份/数据时没有渲染的节点不能虚构像素；后续在授权环境按状态扩展取证。

**来源补注**：2026-09-24 授权账号只读补核的是数据读取与界面布局；本附表和关联 JSON 始终来自 2026-09-23 的空 API fixture。真实数据导致卡片/消息/阅读器高度变化时须现场重新量测，不得直接套用空数据的 W×H。
