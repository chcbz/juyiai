# 任务418：真实图片已生成，提交确认未完成

日期：2026-10-03。状态：**尚不可验收；不可重新生图、重放START或删除paid claim。**

## 业务与实证

真实浏览器创建任务418「画一只鸟 · 20261003交付验证」，无参考图；点将公孙胜、单次授权后自动进入会话1760458004761。Agent执行`pwe_210ca4556d8d4a129ca6315786c060a2`，run `pwe_run_2712cab649b74e098ba148c227a9d737`。

生成PNG为1370×1148、1,863,523字节，SHA-256 `2bc30dd5c2acc8434d3be2bde0757bb5346f2d9597f43f95ed9f1ed896fe35a8`。独立核验outputs/与delivery/字节相同，实际解码显示枝头翠鸟、绿色虚化背景。只读数据库核验平台output_1同摘要/长度、状态STAGED、publication PENDING；因此不是“无图”或“上传字节未到平台”，而是**commit未完成**。本地保全不作为平台交付。

14:14:58.483服务端记录精确conversation/output-commits POST404。原lease1已过期；诊断期间0额外Provider、无生产SQL写、无运行服务修改。

## 确定根因与源码修复

Client原实现生成`native_ + SHA(executionId/outputId/hash).slice(0,40)`；API严格校验`pwe_m_ + SHA(taskId/runId/outputId/hash/length/末尾换行)`。实际发送`native_5145fa516a1b55c543d0c1305ccda8b6d88a8e1a`，应为`pwe_m_28812c78fb2ce5215c8a0fe1f099fdfa46a77987d82e5fe3f4894ba7b22a4a98`。必然触发OUTPUT_CONFLICT，旧Controller将服务异常统一映射404。不是Provider失败，也不需要新增图片服务器。

Client `9bfb6b35cfbcdaf76266acf65122d31d6a4b1ed5` / tree `35217748bcfa167cc14f0fc0a1a7996644b2ae2a`已推特性分支及develop：三条conversation lane复用既有`buildOutputCommit`，保持fence和conversation路由。旧mock只回显请求manifest，所以漏测；新fixture独立按服务端合同计算，旧源码5失败/42通过，修复后100通过；运行/安装关联75通过、1项既有可选skip。没有新模块安装遗漏。

**源码已合入，不代表运行端已升级或418已恢复。** 当前仍运行ed6f保全版。

## 恢复优先级

418的平台已有不可变STAGED字节，首先实现独立、鉴权的结果确认/对账入口，按原execution、command/message、input digest及输出proof幂等提交，不能放宽旧START/通用commit的过期fence，也不手工借用runtime凭据提交。已COMMITTED读回同回执；缺STAGED则如实拒绝，不变成新Provider调用。

后续才补“只有本地保全字节”的result-only上传租约。两条路径均需要当前ACL、原CONSUMED START事实、原执行/会话范围、活跃外部租约不抢占与事务原子性。完整设计见`result-delivery-recovery-design-20261003.md`，不能把计划写成已实现。

证据：`integration-evidence-20260928/task418-result-delivery-20261003/`。图片保留在Agent私有目录，未复制进文档Git仓库。
