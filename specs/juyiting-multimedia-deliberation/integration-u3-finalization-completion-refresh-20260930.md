# 正式验收后刷新真实任务投影

日期：2026-09-30。Web `02af2d062cf6f87969f42901948059a1d95624ea` / tree `a949445631dd269f2e61eaccd2eaf8b9fd1c10ba` 已推送并回读一致。本切片扩展 [原操作恢复界面](integration-u3-finalization-web-20260930.md)，不改写冻结HTTP合同。

## 用户闭环联动

只有已通过原范围、版本、精确成果与accepted/completed领域事实校验的完整回执才从Gallery发出一次task-completed事件。事件绑定当前身份/会话/operation，公开投影仅含taskId、conversationId、operationId、deliveryId、taskVersion，无producer/租约/路径。

BountyDiscussionPanel原样转发，JuyiHall调用既有loadTasks重新读取服务端任务列表；不直接把浏览器内任务改成completed，不自动提交或验收，不重新生成。重复查询已完成操作不重复触发刷新；unknown结果及身份切换后的迟到回执不发完成事件。回执显示与任务列表刷新分别使用服务端事实，刷新失败不伪装为任务已重新读取。

## 实测与边界

七组61 PASS / 0 FAIL / 0 SKIP：23项finalization、15项Gallery、6项目录、10项归档、3项inline、3项完成联动、1项页面v2绑定。实际Gallery覆盖完成事件仅发一次、unknown不发、身份变化隔离；真实Discussion组件测试转发且不改任务对象；实际页面模板绑定只读任务刷新。三个改变SFC的script/template编译通过。inline历史fixture仍有缺stub/变量Vue warnings。

[便携源码/合同/日志哈希](integration-evidence-20260928/u3-finalization-completion-refresh-verification-20260930.json)。本地日志：`/home/isp/wsps/cyf/evidence/u3-finalization-v1/web/completion-refresh-tests.log`。使用完整mock领域回执，不是后端实际提交/验收/完成或浏览器证明。

API正式闭环仍由独立Writer实施，source pin保持已验证194ec91a；另外已安排source schema readiness Writer复现/修复archive InitializingBean校验ApplicationRunner源表之前的启动依赖，不删除真实schema检查。两者均未计为完成，后续必须以候选exact SHA/测试和真实MySQL证据收口。未合入develop/release、未部署、未调用Provider；34项产品验收保持未完成。
