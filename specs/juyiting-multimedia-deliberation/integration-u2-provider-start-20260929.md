# U2 原生生图单次 Provider START：融合分支证据（2026-09-29）

API `jia` 的融合分支已快进到 `27aa2c78a64ae66a74fdce7bcfd77adf177992ee`（tree `ef4cff717b982ba21d3cdaade66560689753a0a3`），并推送远端；本 SDD 更新相同 gitlink。Provider 开始前在服务端任务根/grant/execution 锁下核验当前租约、精确资料版本、授权，原子持久化一次 `conversation_provider_started_at` 与租约版本。已 START 的执行不能重新领取/重复 START；响应丢失必须按未知结果对账，不许自动再次付费。新的 MySQL `v1_16` 增量迁移为单个 `ALTER TABLE`，部分列或缺少有效 CHECK 将禁止启动。`mmdU2ConversationOutput` exact-tree 定向 **51/51 PASS**（4 schema、22 service、23 runtime/security、2 真实隔离 MySQL 8.0.21 旧库升级/部分列与缺失 CHECK 负向，0 skip），日志 `evidence/u2-references/gradle-provider-start-mysql-27aa2c78.log`；隔离实例在测试后关闭、未连接生产数据库。**这不是生产迁移或付款许可。**

Client 独立候选 `codex/juyiting-mmd-native-image-executor` 原提交 `03214a1c71ee61dd45c5fe23d9e4bd03fd45a9a9`（tree `50a413ea4a6dd3076b9e501d5929ed47baf02e6c`），在已确认原生输入、存在执行器、尚有效租约时，向上述精确 endpoint 提交 fenced `POST /internal/agent/tasks/{taskId}/runs/{runId}/conversation/provider-start`。只有收到严格 `{started:true}` 成功响应才调用内置 imagegen；未知/格式不符/错误响应均停止且不报告虚假失败，不自动重试。定向测试 13/13，全目录 Node 测试 **417/417 PASS**（本地复用另一隔离工作树已有依赖，无生产构建或付费调用）；截至 2026-09-30 已与参考图受控读取合入 Client 主融合分支；组合树真实状态以 [组合证据](integration-u2-client-references-20260930.md) 为准。原文 `costAuthorizationRef(null)` 仍不授权收费，显式环境开关默认关闭。

下一步：成本授权/预算事实和收费 Provider 的人工确认；会话 `part.ready`、归档/正式交付、浏览器预览下载验收依旧未完成。**未合入 develop、未发布、未达到画鸟可验收。**
