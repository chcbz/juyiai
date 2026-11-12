# 需求前可选参考图：Web组合源码整合

日期：2026-10-01；定向测试执行于2026-09-30。本次仅提升Web研发pin，不是跨仓API联调、发布或产品验收。

## 精确来源与结果

- 远端feature：`84b14a5ecfb8362382cc8ddf551d81ea1caa6edd`。
- tree：`593d4761605c77b1ba49ccf36a72821ccf421763`。
- 创建/恢复候选`328dafe`、真实父子组合测试`44b5633`、选择器Owner最终修复`e8859d4`经无冲突merge进入上述精确树，feature push/readback一致。
- **213 passed / 0 failed**，包含新入口41、选择器9、真实父表单+真实选择器+真实创建composable组合2，以及native/点将/首轮采用/验收/funded相关原回归；完整selectors、夹具摘要、日志摘要见[manifest](integration-evidence-20260928/u1-reference-intake-web-20261001/exact-integrated-manifest.json)。
- 七个新增源码/测试文件的 scoped ESLint PASS，SFC compile与mounted测试包含在上述213中。没有本地生产构建。
- 可复用证据key：`ddc57d02c13b7f50a7be158511828e53bf29f76f2834dc33592319936dc93053`；实际运行台账仍只有主工作区runtime ledger。

## 用户入口与具体修复

实际张榜前表单可不选资料，或从本人工作空间选JPEG/PNG精确版本；真正创建调用原子`creation-operations`入口，不再拆成创建task再独立link写入。保留完整原文及null/空语义，身份隔离的原键/正文持久readback，刷新只GET；未知结果只允许明确继续原张榜，回执核对后才采用真实task。

选择器先读有效文件/精确版本详情，再取授权Blob预览；latest升级不替换所选旧版本。已修复旧replacement迟到清除新身份/新replacement、新版本预览URL，以及authoritative空model未取消旧恢复的问题。实际Hall的NUL分隔scope不再误作resource ID拒绝；这只是浏览器namespace验证，不扩大服务端权限。

真实父表单组合两项覆盖有参考和无参考张榜、精确v2而非latest v3、仅GET选图、单原子POST、原键与完整正文、确切回执采用及URL释放。**HTTP服务端是隔离fixture，不是已部署API；没有真实浏览器、Agent或Provider执行。**

## 保留失败与未完成边界

首次样式失败及新组合夹具错误保留；后者因fixture误用`post/keyFactory/onCreated`而不是实际`create/createIdempotencyKey/onCommitted`，修正fixture后原断言通过，不降低业务要求。缓存登记首次被拒因ledger仍旧tree，已先绑定精确整合tree再登记，无重复跑测试冒充进展；[manifest](integration-evidence-20260928/u1-reference-intake-web-20261001/exact-integrated-manifest.json)保留归因。

API原子创建实现仍由原Owner隔离施工，未提升API pin；新表/真实Spring启动/实际事务与MySQL证据须单独核实。当前native入口仍`EMPTY_ONLY`，不会凭草稿或选择器放开资料读取/外发/费用。下一步接真实task-file关联回读与执行输入、合法费用授权、同会话澄清/EDIT/派生输入、保存及正式交付验收、双接应、真实Provider/浏览器和exact版本发布。确定拒绝原意图的无副作用退出仍是产品待办。

完整34项产品用例仍**NOT_RUN**；本次未合develop、未部署、未迁移生产数据、未调用付费Provider，不通知可验收。
