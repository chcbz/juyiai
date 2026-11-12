# 成果区 output → 持久资产 → 工作空间保存合同收口

日期：2026-09-30。已推送 API `194ec91a596c28f9575a64aef47a5bf7b9fb6778` / tree `10d312e61057b1a83da1485238c2f3acf63e5361`；Web `22c34a90428daa8729d03e7025865226c2f81589` / tree `ab6f09d6f0a089c8d96ee0c61c985aca5db8493d`。两仓只在 `codex/juyiting-multimedia-deliberation` 收口；没有 develop/release/生产动作。

## 合同与实现

现有 `GET /chat/requests/{requestId}/steps/{stepId}/outputs` 增加可选：

```json
{"assetRef":{"assetId":"ast_<persisted-id>","revision":"1"}}
```

不是新增写接口。旧媒体字段和六参 OutputItem 源码调用兼容；未启用投影或尚未投影时 `assetRef` 为 null/省略，原预览/下载不受影响，保存等待真实资产登记。读目录只定位持久关系，不调用 projector、Provider、execution 创建或归档。

`findOutput` 基于同一 owner/tenant/client/step/output 身份计算既有资产定位，使用原 live-generation SQL；核对 request/step/execution/run/output 与会话来源。Controller 再核对完整身份、generation、MIME/hash/length 和正整数 revision，不把摘要当作用户可认领的凭据。来源异常返回既有 owner-safe 不可用错误，无外链、目录或租约泄漏。

Web 校验可选 assetRef 的精确结构和十进制字符串 revision，冻结引用；未登记资产时禁用保存并解释等待原因，下一次只读轮询可发现真实引用，不自动发起保存。保存全部复用 `useHallConversationArchive.js`，发送：

```json
{"mode":"create","items":[{"assetRef":{"assetId":"ast_<persisted-id>","revision":"1"}}]}
```

不再发送 `CREATE/outputRef/sha256/displayName` 的错误合同，不新增第三套保存客户端/文件系统。原幂等意图在 POST 前持久，刷新复用原键；已知操作优先 GET 对账，pending 时显式动作才重放原 POST。只有逐项服务端回执指明真实 fileId/version 才显示保存成功，身份切换取消/隔离迟到回执。

## 实测

- exact API Chat **30 类 / 160 项 PASS**，0 failure/error/skip，含精确映射、未投影兼容、foreign/stale/hash 负向、读取不发布/不生成，以及原归档/资产回归。
- exact Web 四组 **28/28 PASS**，含未登记不写、真实保存合同、丢 ACK 后 remount 原键恢复、pending 后只读查询、身份切换与既有预览/下载/修改。既有 inline transcript fixture 有未定义 stub 的 Vue warning，未掩盖为零警告。
- 首次 Gradle 缺 repoUsername/repoPassword 配置，无测试执行；离线惰性占位属性修正后，第二次内核 global OOM 杀死本线程精确 daemon PID 1785125。按独立根因矩阵，第三次仅调整该调用的 ActiveProcessorCount=2/SerialGC，保持测试内容、单worker和原heap/metaspace设置，完整通过。无 foreign 进程操作或资源硬门禁。
- 无 DDL/SQL 变更：与上一 exact API 的资产 schema 和 findCurrent SQL 字节相同；仅复用已有隔离 MySQL 证据，不宣称此轮真实 Spring/MySQL 保存通过。`git diff --check` 通过。

[便携验证摘要、XML/日志与源码证据哈希](integration-evidence-20260928/u3-output-asset-archive-verification-20260930.json)。本地完整日志在 `/home/isp/wsps/cyf/evidence/u3-output-asset-archive/`。

## 剩余闭环

源码对接修复不等于真实归档端到端验收。发布前须核验同一版本的 asset/media/archive/private-storage 配置和 schema 准备顺序，避免 archive InitializingBean 早于 Chat ApplicationRunner 时首次空库缺源表；开关仍默认关闭。

正式 finalization 尚未实现：应绑定精确选中集合、受信 producer 晋升、原任务/指派版本和用户验收，复用正式 decision 的领域 task completion，保存分阶段恢复。不能让浏览器成为 producer，也不能再调用生成来伪造正式成果。仍需有/无参考、上一稿修改、澄清、双接应、多媒体/文本保存及真实浏览器/版本发布；产品34项AC/FD保持未验收。
