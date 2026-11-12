# 受控图像 v2 Client：源码整合与真实修复证据

状态：Client 源码已精确 FF/push/readback；**不是完整合法费用桥、双接应、真实 Provider、浏览器或产品验收通过**。运行 Owner/gate 仍只在主工作区唯一 ledger；本文件为精确树的交接证据。

## 1. 精确树与验证

- Client feature：`554805226ddfcbe7ab15f499f9d0fa31d035b2f6` / tree `59af3c8d45a46e48210d42a7569e481e29f31478`，从 `69765549` 字节精确 FF 后已推送、远端 readback 一致。
- Owner 实际 focused Node **157/157**，失败/取消/跳过/todo 均0；Main未重跑未变树，核对原stdout SHA及共同fixture，并新增12项纯parser断言。
- 原stdout解压SHA：`b494f83b271c717f2ab4477be970faa9cd90fa51215302393991fe57f3dc4d20`；[便携manifest、日志与实际发现](integration-evidence-20260928/controlled-image-v2-client-source/manifest.json)。
- [共同fixture](fixtures/controlled-image-bridge-v1.json) 字节仍为 `d19264d19ed04d10e737c526479b2c956b9afb182eb7c26c86a42f50c981ca87`；五组29项共同预期未作为跨仓套件执行，不改成全PASS。34项产品用例仍NOT_RUN。

## 2. 本切片实现

独立 `controlledImageBountyExecution` sibling广告 v2 command / v2 START、16个JPEG/PNG输入与一个PNG output_1。真实启用的配置、executor、credential与HTTP poll都就绪才声明 enabled；旧fast-v1、native-v1和PRIVATE/TASK不放宽。

客户端在lease/输入/START前严格核对command descriptor与当前binding/epoch/model配置；START只接受精确身份、lease、descriptor一致的首次v2回执，之后现有受控持久claim与单次HTTP adapter办理输出stage/commit。未知/claim歧义不自动fallback/重试或POST终态failure。测试网络与executor均为隔离fake，不表示实际HTTP生成收费或有效可预览照片。

## 3. 实际发现与修复（不以旧PASS掩盖）

初稿 `330d63e` 曾报告154定向通过，但Main真实纯parser/fake-lane探针发现：core合法binding/model的`.`/`:`不被command接受；epoch错误接受number或超JavaLong；CONTROLLED_IMAGE_OUTCOME_UNKNOWN被误报failure；成功测试实际只停在错误STAGED摘要。

原Owner在 `451821e` 修复grammar、canonical positive Java-long string、UNKNOWN/claim歧义并补成功fake stage+commit和真实受控executor fake网络未知组合。Main随后再次实际重现regex把number/array强制转换为binding/model合法值。最终 `5548052` 强制primitive string并补number/array/object/null负例。两轮实际发现均便携保留；最终157项与初稿154项是不同候选证据，不混算。

## 4. 下一完整链路与真实缺口

APIcore候选6f68保持未提升：persistent正常生产图已能编译/指纹复用，但v8实际scoped fixture编译暴露缺少org.hamcrest.Matcher依赖，0tests/XML；原Owner按真实imports修复，不删测试、不借baseline、不禁AP。v6堆失败与v7离线缺jar保留为失败；不是“正常图已验证”。

BRIDGE-A仍在独立APIworktree做点将+BOUND、execution+RESERVED、START+CONSUMED原子桥；BRIDGE-W已分配原Client Owner到独立Webworktree接显式同意、immutable wrapper、原键恢复及同一首轮会话采用。一次完整Webcheckout真实NoSpace，恢复为仅排除无关public/occlusion大素材的稀疏工作树；没有删除他人文件、更改Git源树或用此声明生产build/browser通过。

仍须完成真实MySQL/事务/并发、跨仓联调、澄清/续办/EDIT、文本/图片/音频/文件展示归档和正式验收完成、最新develop语音融合、双接应与34产品用例、exact版本制品发布及线上验收。未选择账户/模型、未付费、未部署；不通知可验收。
