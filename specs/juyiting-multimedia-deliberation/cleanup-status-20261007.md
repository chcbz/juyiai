# 2026-10-07 历史开发资源清理

已删除与本功能相关的 **61个历史worktree、60个本地分支、10个远端分支**；47个远端分支查询时已经不存在，不重复计为删除。限定本任务历史范围，未清空全项目资源。

删除前核对进程cwd/Owner、fetch/readback、未合入状态；HEAD工作改动/index/untracked分别保存，未合入Git提交以bundle恢复并校验。删除本地ref采用精确SHA比较，远端采用精确lease并readback，不force删除变更远端。

保留：其他Owner活跃api-primary-v3-admission；3个远端因SHA不同于原目标，分别SDD codex/juyiting-multimedia-deliberation（b50bb7ee）、API codex/ac12-text-archive-20261003（de4dd601）、API codex/juyiting-multimedia-deliberation（d85bc64e）。最新SDD已只读导入本轮状态；不因此擅删两个API新提交。吴用、共享Client和API运行进程未操作。

**阶段一历史快照：会话删除0个。** 当时已询问是聚义厅历史测试会话还是Codex开发会话，尚无回答；不把Git分支等同业务会话、不把归档说成永久删除，不直接清空Codex状态数据库。现有已受理成果/验收/新task426证据保留。

[机器清单](../../docs/implementation/evidence/mmd-shortest-flow-20261007/cleanup-manifest.json)含精确HEAD、删除readback及恢复bundle摘要；实际恢复内容放私有维护目录，不公开凭据/未提交补丁。此前2026-10-05 chcbz旧测试议事清理是独立历史记录，不计为本轮删除。

## 用户明确Codex开发会话后的补录

用户已确认清理对象为Codex开发会话。**通过原生thread/delete实际删除34个历史子会话**，逐个回执、线程索引和原rollout文件均已核对；不是仅归档。限定为已归档、与本次已清理worktree有精确路径引用且无现有ledger Owner的历史开发记录。

第一阶段31个有明确task_complete或turn_aborted；另3个旧rollout缺结束记录，先保留，随后以原生thread/turns/list确认最新轮次为interrupted，删除前再次核对同turnId/终态，补备份后清理。没有因旧task_started或归档标记猜测会话已经结束。34份rollout及作用域内元数据已保存为两份私有恢复归档，逐个内容摘要与归档读回校验；不公开会话正文或凭据，保留备份不等于安全擦除。

当前聊天、仍有任务归属的主会话01a0dde8-fd03-7ee0-be21-293ca13bb336及所有非目标会话保留。没有删除聚义厅业务会话，也没有手工SQLite DML、重启共享Codex daemon或操作共享Agent/API。

[原生删除与readback](../../docs/implementation/evidence/mmd-codex-history-cleanup-20261007/result.json)、[验证](../../docs/implementation/evidence/mmd-codex-history-cleanup-20261007/verification.json)。原阶段一Git清理manifest的sessionsDeleted=0保留澄清前历史；最新余项/集成投影为34删除、终态不明候选0。
