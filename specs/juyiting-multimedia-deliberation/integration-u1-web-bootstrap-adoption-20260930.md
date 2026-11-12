# 首轮悬赏议事采用与本轮成果终态：源码整合证据

日期：2026-09-30。Web `0e9be06f741f2fc1a5f7a85ea8527f160a73fe2c` / tree `265d5c2ae8fcaee3789358f1469619e0ad2c352c` 已正常快进到feature并推送/readback。前置采用提交 `3ac40312aa169322e92530a25d9a3bbe7e74e65a` 保留；不是产品验收或发布。

## 实现与真实源码依据

`useHallConversation.adoptBountyBootstrap` 按确切原首轮request读 `/chat/requests/{initialRequestId}`；要求本任务bounty scope、显式目标、assignment、conversation、请求/step/turn的实际字符串fence匹配，然后读取确切会话历史并接既有受认证事件流。不查列表第一条、不POST、不重发首轮、不本地伪造assigned/completed。请求核对通过后历史失败仍保留受理事实，显式重试仍只读；身份/任务/目标变化及迟到响应隔离，读取期间阻止新的发送与列表自动恢复。

实际 `ChatBountyAssetProjector` 将成功提交的原生媒体请求更新为 `OUTPUT_COMMITTED`，不是 `COMPLETED`。Web补齐该**本轮请求**终态并显示“本轮成果已就绪”；收到原请求的媒体final/ready只触发确切请求只读核对，不从事件内容/模型文字宣称任务完成。后续该bootstrap的readback仍验证精确源关联与不回退版本，错误任务回执不能解除忙碌。领域正式提交/验收/任务完成仍须独立finalization合同事实。

## 验证

- exact已提交树上的五文件定向回归 **130 passing，0 failing**，其中本切片 **35** 条新增用例。
- 新validator/state helper/test的ESLint、Node语法、diff-check通过。既有composable仍有两条与父树相同的unused变量问题，保留父树证明，不称全文件lint全绿。
- 用实际composable、受认证SSE reader/parser + 受控测试流验证native final引发只读核对、错误task回执拒绝、本轮busy解除不改变task。测试流不是Provider、浏览器或线上运行。
- 原失败保留：regex/indent/setImmediate lint问题逐项修正；SSE测试dispose已关闭reader后重复close的清理错误修正，未改生产取消边界。
- [便携证据](integration-evidence-20260928/u1-web-bootstrap-adoption-20260930.json)记录exact SHA/tree/selector/fixture和日志摘要。

## 未闭合与下一步

实际页面点将仍走旧写入口，本切片尚未接入 `JuyiHall.assignTask`。权威current requirement候选 `9421dd77`、原键projection候选 `877bc5f8`、finalization候选 `8d4ab3f8` 已提交但未整合/正式测试；schema readiness `79165b93` 的新源已局部overlay编译，JUnit与正常构建/MySQL未验证。没有据候选更新API pin。

[初始动作与授权集合合同](initial-operation-contract-v1.md)已冻结并分配两个不重叠包：grant/DTO显式初始动作与只读投影新旧hash适配。该合同不是已实现证明；后续仍需点将原key/body存储、canonical task回读、自动采用会话、引用/上一稿解析、真实澄清和多轮修改、成本授权事实、实际Provider/双接应/浏览器、正式验收及版本发布。**AC/FD整体未验收，不通知可验收。**
