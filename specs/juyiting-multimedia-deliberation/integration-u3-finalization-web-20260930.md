# 正式验收界面：固定成果与原操作恢复

日期：2026-09-30。Web 已推送 `e81aa451d8a5358fd071cbba053cf983f5b2a371` / tree `35e87095e503f89376c180fe14dd42076174701c`，远端回读一致。API仍固定已验证 `194ec91a`；后端正式晋升/验收实现尚在独立Owner工作树中，未整合、未验证。本记录只验收Web源码切片，不是完整业务验收。

## 实作

- 成果区复用新 `useHallBountyFinalization`，删除只信 `TASK_COMPLETED/accepted/deliveryId` 的旧内存处理。
- 发送前持久并回读原body/key；正文、选中来源与摘要、任务版本和指派版本固定。恢复凭据损坏/不可写时不发送新的验收。
- 刷新/remount恢复同身份会话的原操作，不自动POST。已知operation查ID，否则携原键查request；查询纯读，404不证明未受理。
- 显式“继续原验收”先查再按原键/固定正文恢复；鉴权/冲突/网络错误不自动补POST。未知结果不能用新选择、新版本或新键覆盖。
- 固定最终选择并显示恢复入口；轮询、投影更新和切换根请求不丢失原验收意图。身份/会话切换abort并隔离迟到回执。
- 完整回执须匹配任务/会话、原版本、精确六字段有序成果集合、正整数stateVersion、真实领域状态和交付ID；版本、阶段或已确认完成事实不能回退。只有服务端真实accepted/completed投影才能显示“需求已完成”。
- 版本解析不再将空串转0；拒绝非规范/不安全整数。保存到工作空间与正式验收继续独立。

[冻结跨仓合同](finalization-contract-v1.md)明确三个HTTP端点、阶段、原键恢复、受信producer晋升和真实用户决策要求；不是已部署接口清单。Web测试里的完整回执是mock，不是正式交付或数据库完成证据。

## 实测与归因

五组 **57 PASS / 0 FAIL / 0 SKIP**：23项finalization、15项Gallery、6项目录、10项归档、3项inline。新composable通过Node语法、定向ESLint；diff whitespace通过。原inline fixture仍有缺stub/变量的Vue warnings，如实保留。

初跑45通过/2失败来自两处既有SFC harness遗漏新composable依赖；补实际依赖，不放宽完成回执校验。加入终态回退检查后的五组曾56通过/1失败：旧preview测试的50次setImmediate循环未等到第二次native摘要/DOM插入。改为MutationObserver等待真实图片插入，不增大任意等待循环/生产超时；改变测试输入后最终57项通过。

[便携来源与测试摘要](integration-evidence-20260928/u3-finalization-web-verification-20260930.json)。本地日志：`/home/isp/wsps/cyf/evidence/u3-finalization-v1/web/targeted-tests.log`；失败归因同目录 `failure-attribution.json`。

## 继续条件

API Owner仍须真正持久晋升/阶段操作/3端点，取得合法work-item/run/lease并复用正式submit与owner decision的领域完成事务；不能为获租约新开Provider执行，也不能伪造runtime回执或删除lease校验。候选提交后经orchestrator串行相关Gradle与隔离MySQL验证，再更新API pin。

没有develop/release合入、部署、Provider调用或浏览器验收。本次不能通知可验收；完整34项AC/FD、双接应、参考图/上一稿/澄清、多媒体保存和exact版本发布仍须逐项真实收口。
