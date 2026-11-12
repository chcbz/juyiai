# 会话成果保存请求的悬挂状态恢复（2026-09-30）

Web 特性分支已快进并远端回读 `ebae2341ebc1226a0e0396b983ba3e679c8dc7c5` / tree `a1a3c3a64ed77d8c15b7f385b1929139b71c075d`。同身份会话内收到服务端操作 ID 后，用户点击“继续原保存”会**先按原操作 ID 查询**；若服务端仍为 pending/saving 且保有最初的幂等键，再以**原键及原资产引用**显式重发 POST，供服务端对账/恢复。GET 返回 saved 时不再发 POST；网络/身份/状态回执不明确时不盲重试，也不将本地记录视为保存成功。此举修复页面刷新后仅重复读取永远 pending 的操作而无法主动恢复的情况。

本地 Owner 定向执行 `node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter dot` 加 7 个聚义厅多媒体/归档/展示测试文件：**30/30 通过**；两处改动 ESLint 与 `git diff --check` 通过。未运行生产构建/浏览器，服务端归档 POST/GET 仍在实施；不代表归档完成、需求交付或可验收。

2026-09-30 追加：Web 快进至 `a03ad71e2f5aacfcc061fa6890a8c3d346f1cdca` / tree `b58e7a747cad8839ef30e1f4851401e912bb11ba`（已推送特性分支）。UI 的“查询保存状态”仅执行 GET、不自动重发 POST；“继续原保存”才按前述原键显式续写，无 operationId 时不展示查询。新增只读及按钮职责测试；7 个定向测试文件 **32/32 通过**，ESLint 与 `git diff --check` 通过。本地静态与定向验证，不代表服务端实现或浏览器/生产验收。
