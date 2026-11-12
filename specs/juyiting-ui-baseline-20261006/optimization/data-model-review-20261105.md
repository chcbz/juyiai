# 聚义厅数据模型复核（2026-11-05）

## 范围与证据边界
- Owner沿用JUYITING-POLLING-20261102；API候选基线`cb1abefb409297bec1caca17d3d3c153ca244a29`；包含此前未提交20条分页调整，本轮不修改产品代码/DDL。未读取生产库，不声称与线上一致。
- 本次按列盘点两份核心DDL的14张表、224个列定义（包括维护表、重复scope列及尚未上线的两个delivery索引列）。会话/消息与Agent成果域另作边界核对；未审完所有Agent执行表、升级DDL及JSON内部每个键，不宣称全项目逐字段完成。
- 下表区分字段用途与独立持久化必要性：有读写不等于必须保留；“关联/边界/时间”不是删除许可或全部优化已完成。没有生产数据分布/查询计划，因此不承诺删列收益。

## 已确认问题
1. `chat_conversation_event.event_version`在当前writer中由`event_sequence`直接赋值，增加一次UPDATE；属于确定派生列。可保持wire字段由序号生成，无需先改客户端协议。
2. `chat_turn.last_delta_digest`在生产源码未找到业务读取或非空赋值；`last_delta_seq`新回合只有0初始化，旧取消文本恢复/重备判断/目录仍读取。两者不能以“有测试引用”为保留理由，也不能在旧消费者未移除时直接drop。
3. `chat_typed_admission.state/state_version`是固定ADMITTED/0的回执，不是独立状态机；`chat_typed_proposal.state/state_version`也只是旧PROPOSED/0。
4. 新v5最终写入校验content==outcome.text，随后消息content、outcome.text列、outcome_json.text同时持久化；outcome.source_catalog_json复制admission同字段。binding_json/facts_json是可重建投影，当前读端为比较这些副本而重建大量输入。
5. step与execution_link由唯一step_id形成0..1执行扩展；确有合表空间，但两侧状态分别在执行结果投影/终止链更新，需统一这些写入而不是丢弃幂等意图/完成事实。

## 表是否必须拆分
- 会话/消息：1:N，保持分离。请求/回合：现有通用入口循环目标好汉，是同一用户输入多目标分发的实现；这只能证明代码支持，不能证明产品需要广播。按用户本轮澄清的“每个好汉不同指令各为请求”，应重新评估request/turn合并，不把现有循环当作保留两表的需求依据。
- 回合/快照：状态小行与大输入分离，重备输入还会保留旧快照；并表并非显然更优。消息/结构化结果：可选扩展有意义，重复正文/材料副本不因此合理。
- request/admission：前者生命周期，后者幂等回执；普通消息请求、typed与原生执行子请求不同，不能简单视为两套任务。可缩减回执常量/副本，不能删除唯一幂等约束。
- step/link：合表候选，不是已决定迁移。pending_question：可变答复CAS与不可变最终结果不同职责，可保留状态而去掉问题正文副本。proposal：历史协议结构候选，不计作新原生执行所必需。
- outbox/event：前者负责待发送/重试/租约，后者负责已发生事实回放，状态与消费方式不同；不因都是“事件”合并。
- 文件产物/正式artifact/交付批次：生成文件、固定正式版本、验收批次是不同事实；一批可含多个版本，不能合成单条“成果状态”。正式item是多项关联，不是无意义中间表。

## 逐列用途与判断（核心DDL）

### chat_context_snapshot

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `snapshot_id` | 保留 | 执行输入快照身份；未执行的上下文重备可产生新快照，不能假定永远一回合一行 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `target_agent_id` | 边界 | 目标好汉绑定 |
| `route` | 语义 | CHAT/INSPECT等合同路由；历史读仍需辨别 |
| `source_vector_json` | 保留 | 输入来源版本向量，参与contextDigest与派发输入 |
| `facts_manifest_json` | 保留 | 执行时事实/合同；与当前动态配置不同 |
| `context_digest` | 保留 | 绑定执行输入内容；快照读、派发回报使用 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |

### chat_request

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `id` | 保留 | 数据库顺序键；请求目录/上下文水位使用，不是request_id的无用副本 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `request_digest` | 保留 | 已受理请求身份/输入完整性 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `user_message_id` | 关联 | 该请求对应的用户消息 |
| `aggregate_state` | 派生状态 | 汇总多个回合或执行请求的状态，有读取用途；派生并不自动等于应删除 |
| `state_version` | 并发 | 该实体CAS版本；固定值表在专表说明覆盖 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_turn

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `turn_id` | 关联 | 一个好汉回合；请求可有多目标回合 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `target_agent_id` | 边界 | 目标好汉绑定 |
| `snapshot_id` | 关联 | 当前绑定快照；重备上下文时可更换 |
| `context_digest` | 重复绑定 | 快照摘要的回合绑定，执行回报使用；不是独立业务事实 |
| `dispatch_id` | 关联 | Runtime派发/回报绑定，与某次重试编号不同 |
| `route` | 语义 | CHAT/INSPECT等合同路由；历史读仍需辨别 |
| `state` | 状态 | 该实体状态；是否独立必要须看具体表，不能按名称合并 |
| `state_version` | 并发 | 该实体CAS版本；固定值表在专表说明覆盖 |
| `last_delta_seq` | 旧链候选 | 当前源码新回合只写0，未找到推进写入；旧取消文本/重备条件/响应仍读取，需连同消费路径收口 |
| `last_delta_digest` | 废弃候选 | 当前生产源码只有字段/INSERT占位/schema定义，未发现非空赋值或业务读取 |
| `final_digest` | 保留 | 固定最终回复的完整性/重复提交判定 |
| `final_message_id` | 关联 | 最终持久消息；未完成为null |
| `terminal_reason` | 保留 | 失败/取消原因，非最终回复正文 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_dispatch_outbox

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `event_id` | 保留 | 幂等派发事件身份 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `turn_id` | 关联 | 一个好汉回合；请求可有多目标回合 |
| `dispatch_id` | 关联 | Runtime派发/回报绑定，与某次重试编号不同 |
| `event_type` | 保留 | DISPATCH/取消/动作等处理类型 |
| `task_grant_id` | 边界 | 事项执行授权身份 |
| `task_grant_version` | 边界 | 授权版本 |
| `task_assignment_revision` | 边界 | 任务指派绑定 |
| `task_requirement_revision` | 边界 | 任务要求绑定 |
| `status` | 保留 | 派发/重试状态，不等于模型执行终态 |
| `payload_json` | 保留但可瘦身 | 冻结的派发/事件合同；有快照重复，重试语义需保持 |
| `version` | 并发 | outbox行CAS |
| `available_at` | 调度 | 下次可领取时刻 |
| `lease_owner` | 并发 | 当前领取者 |
| `lease_until` | 并发 | 领取租约 |
| `attempt_count` | 运维 | 派发尝试次数；不是唯一去重依据 |
| `fencing_token` | 并发 | 区分过期领取者与当前领取者 |
| `last_error` | 运维 | 最近派发失败原因 |
| `sent_at` | 时间 | 派发发送时间，不等于执行完成 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_conversation_event

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `event_sequence` | 保留 | 持久事件递增游标，重连/顺序读取使用 |
| `event_id` | 保留 | 业务事件确定性身份/去重；不等同递增序号 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `turn_id` | 关联 | 一个好汉回合；请求可有多目标回合 |
| `dispatch_id` | 关联 | Runtime派发/回报绑定，与某次重试编号不同 |
| `event_type` | 保留 | 客户端解释事件类型 |
| `event_version` | 确定派生 | assignEventVersion显式设置为event_sequence；可由序号派生，当前多一次UPDATE |
| `payload_json` | 回放副本 | 持久事件回放需要；最终事件含正文与结果，不是新的业务真相 |
| `occurred_at` | 时间 | 事件发生时刻 |

### chat_interaction_step

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `step_id` | 关联 | 具体执行/交互步骤身份 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `step_number` | 顺序 | 请求内步骤排序与唯一键；原生创建目前常为1，不代表所有旧消费者可删 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `task_id` | 关联 | 所属事项，与会话并非同一实体 |
| `assignment_revision` | 边界 | 事项指派版本，不等同请求/回合状态版本 |
| `grant_id` | 边界 | 步骤固定授权 |
| `grant_version` | 边界 | 步骤固定授权版本 |
| `target_agent_id` | 边界 | 目标好汉绑定 |
| `kind` | 语义 | 步骤种类；执行与非执行步骤需区分 |
| `state` | 状态 | 该实体状态；是否独立必要须看具体表，不能按名称合并 |
| `state_version` | 并发 | 该实体CAS版本；固定值表在专表说明覆盖 |
| `input_snapshot_digest` | 边界 | 执行输入快照摘要，不是模型最终答复摘要 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_step_execution_link

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `execution_intent_id` | 保留语义/合表候选 | 幂等执行意图；step_id有唯一约束，可考虑字段并入步骤表而非丢弃意图 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `step_id` | 关联 | 唯一对应步骤 |
| `execution_id` | 关联 | 对应执行实例；原绑定前允许null |
| `state` | 投影/合表候选 | RUNNING/RESULT_COMMITTED等Chat侧完成投影；不等同Runtime原始执行状态 |
| `state_version` | 并发/合表候选 | 该投影CAS；并表须合并真实事务而非只改列名 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_bounty_binding

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `task_id` | 关联 | 所属事项，与会话并非同一实体 |
| `conversation_id` | 关联 | 为事项保留/绑定一个用户议事会话，事务内可暂为null |
| `assignment_revision` | 边界 | 绑定的指派代际；与conversation.task_id信息有重叠，但预留唯一性不能直接丢 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_deliberation_schema_version

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `version` | 维护 | 持久schema维护版本，不是业务状态 |
| `stage` | 维护 | 维护阶段，initializer读取 |
| `updated_at` | 维护时间 | 维护状态更新时间 |

### chat_conversation_asset

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `asset_id` | 关联 | 消息附件对外身份，字节仍在workspace |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `step_id` | 关联 | 来源步骤 |
| `execution_id` | 关联 | 来源执行 |
| `run_id` | 关联 | 来源运行绑定 |
| `output_id` | 关联 | 来源产物 |
| `message_id` | 关联 | 展示在哪条消息 |
| `part_id` | 关联 | 消息内部附件部分 |
| `kind` | 展示 | 附件媒体类别 |
| `content_mime_type` | 展示/完整性 | 固定文件类型 |
| `sha256` | 完整性 | 固定附件内容摘要 |
| `byte_length` | 完整性 | 固定附件大小 |
| `revision` | 关联 | 附件引用版本，不等于文件的业务验收版本 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |

### chat_typed_outcome

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `outcome_id` | 关联 | 结构化结果身份，与消息展示身份不同 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `turn_id` | 关联 | 一个好汉回合；请求可有多目标回合 |
| `task_id` | 关联 | 所属事项，与会话并非同一实体 |
| `assignment_revision` | 边界 | 事项指派版本，不等同请求/回合状态版本 |
| `assistant_message_id` | 关联 | 同事务提交的最终消息 |
| `final_digest` | 完整性 | 固定业务答复摘要 |
| `kind` | 可查询投影 | 答复类型，JSON内也有；用于轻量过滤，可保留索引投影 |
| `text` | 确定重复 | 与message.content及outcome_json内text一致；writer校验一致后同时持久化 |
| `binding_json` | 可重建副本 | 绑定信息大部分可由turn/admission/snapshot重建；当前reader用来重验 |
| `facts_json` | 可重建副本 | 快照中合同事实的规范化投影；当前reader重建后逐字对比 |
| `outcome_json` | 业务结果 | 已验证结构化最终答复；含text及业务语义，历史版本必须明确读取 |
| `source_catalog_json` | 确定复制 | persist复制admission.sourceCatalogJson；read再次比较二者 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `delivery_target_agent_id` | 候选派生索引 | 本优化候选新增，从已验证binding写入以查询交付head；不是新的授权来源，未上线 |
| `delivery_parent_outcome_id` | 候选派生索引 | 本优化候选新增，从已验证关系写入以查询父子head；需旧数据受控回填，未上线 |

### chat_typed_pending_question

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `pending_question_id` | 关联 | 可作答澄清问题身份 |
| `outcome_id` | 关联 | 结构化结果身份，与消息展示身份不同 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `state` | 状态 | 该实体状态；是否独立必要须看具体表，不能按名称合并 |
| `state_version` | 并发 | 该实体CAS版本；固定值表在专表说明覆盖 |
| `question` | 重复正文 | 也存在不可变outcome JSON；状态需要独立，问题文本未必需再存一份 |
| `required_facts_json` | 重复正文 | 问题要求也存在outcome JSON；当前读取依赖，不能直接删 |
| `reply_request_id` | 关联 | 实际回答该问题的请求 |
| `reply_idempotency_key` | 幂等 | 防止同一问题重复答复推进 |
| `reply_body_digest` | 幂等 | 同键不同回答内容冲突判定 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |
| `updated_at` | 时间 | 更新时刻/调度或展示；具体每个索引效益未做数据库实测 |

### chat_typed_proposal

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `proposal_id` | 历史结构 | 旧EXECUTION_PROPOSAL身份；当前原生ACTION_REQUEST不从本表编排 |
| `outcome_id` | 关联 | 结构化结果身份，与消息展示身份不同 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `state` | 历史常量 | 现有writer写PROPOSED，store无推进方法 |
| `state_version` | 历史常量 | writer固定0；不是活跃CAS状态机 |
| `operation` | 历史结构 | 旧操作类型 |
| `instruction` | 历史结构 | 旧操作指令 |
| `source_ref_ids_json` | 历史结构 | 旧输入引用ID |
| `source_selectors_json` | 历史结构 | 旧引用选择器 |
| `parent_request_id` | 历史结构 | 旧编辑操作来源请求 |
| `parent_step_id` | 历史结构 | 旧编辑来源步骤 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |

### chat_typed_admission

| 字段 | 分类 | 实际用途与判断 |
| --- | --- | --- |
| `admission_id` | 关联 | 持久幂等受理记录身份 |
| `tenant_id` | 边界 | 环境分区；实际SQL/索引约束使用，不按重复列机械删除 |
| `owner_jiacn` | 边界 | 数据Owner及读取/执行范围；与执行好汉身份不同 |
| `client_id` | 边界 | 客户端数据范围；与tenant/owner共同限定 |
| `conversation_id` | 关联 | 绑定所属会话；跨请求查询/生命周期边界 |
| `conversation_generation` | 边界 | 会话生命周期代际，阻止旧执行关联到新生命周期 |
| `idempotency_key` | 保留 | 同键重放原受理回执，不再启动任务 |
| `request_digest` | 保留区别 | 用户命令加解析后的sourceCatalog摘要；与body_digest不一定相同 |
| `body_digest` | 保留区别 | 用户提交正文摘要，重试先比较，不依赖当前目录重算 |
| `intent` | 语义 | 受理命令类型 |
| `task_id` | 关联 | 所属事项，与会话并非同一实体 |
| `assignment_revision` | 边界 | 事项指派版本，不等同请求/回合状态版本 |
| `parent_outcome_id` | 关联 | 后续请求的父结果 |
| `pending_question_id` | 关联 | 答复澄清时绑定原问题 |
| `request_id` | 关联 | 处理请求的持久身份，不等同消息ID |
| `request_revision` | 关联 | 请求合同修订绑定；新建通常为1，但纳入外部合同/复合键，非本轮直接删 |
| `user_message_id` | 回执副本 | 原受理消息ID，回放Accepted使用 |
| `turn_ids_json` | 回执副本 | 原受理回合集合；普通typed一项，原生执行子请求可为空，不能直接改为单个turn_id |
| `source_catalog_json` | 保留快照 | 受理时授权材料解析结果，后续执行/重放依赖 |
| `state` | 固定回执字段 | 当前writer写ADMITTED，reader要求该值；非动态请求状态 |
| `state_version` | 固定回执字段 | 当前writer与receipt要求0，可由回执合同派生 |
| `event_cursor` | 保留 | 原受理时事件水位，用于重放/继续订阅，不应改成当前水位 |
| `created_at` | 时间 | 创建时刻/排序追溯；未据此证明每个副本均须独立持久化 |

## 额外核对：基础会话/消息与成果域
- `chat_message.sync_status`有LongTermMemoryServiceImpl.syncPendingConversations/syncConversation消费者；不是流式发送ACK。`jiacn/client_id/tenant_id`用于查询隔离；message_type/sender_type/sender_name分别是消息角色/展示发送者类型/名称快照。不能看到名字相近就删。
- `chat_message.metadata`保存requestId/turnId/outcomeId、附件/取消等扩展；这是一个JSON容器，不能声称其全部历史键均必要。应逐条写入合同核对，不能把整列当一个已经证明合理的字段。
- `chat_conversation`的scope/type/task/target字段支持公共/事项/私聊不同范围；`lifecycle_generation/deleted_at`服务删除隔离。taskId与bounty_binding存在关系副本，但binding还承担并发预留，不能仅由字段重复判定可删除。
- artifact的title/MIME/size与执行产物存在展示重叠，但固定正式版本与执行临时产物有不同保留期和权限；正式delivery.items的artifactId/version/hash/purpose不可用最新文件代替。
- Agent表中created_at/create_time/update_time等时间副本、全部执行schema字段以及历史迁移差异本轮没有完成逐列消费者审查，明确留待核对，不列入已批准删除。

## 可复核源码入口
- [新最终正文一致性与摘要](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatActionFinalValidator.java#L48)
- [消息/结果/最终事件同事务写入](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatDeliberationService.java#L857)
- [重复结果字段写入与读取重验](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatActionFinalService.java#L140)
- [事件版本复制更新](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-mapper/src/main/java/cn/jia/chat/deliberation/ChatDeliberationMapper.java#L83)
- [固定准入回执状态](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatTypedDiscussionAdmissionService.java#L33)
- [幂等两种摘要的实际区别](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatTypedDiscussionAdmissionService.java#L278)
- [旧流式序号读取/取消部分正文](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatDeliberationService.java#L1170)
- [step/link写入与CAS](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-mapper/src/main/java/cn/jia/chat/deliberation/ChatInteractionStepStore.java#L78)
- [原生执行step/link/admission同时创建](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatActionExecutionService.java#L122)
- [完成事实投影更新link/step/request](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyAssetProjector.java#L313)
- [消息记忆同步消费者](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-service/src/main/java/cn/jia/chat/service/impl/LongTermMemoryServiceImpl.java#L180)
- [旧proposal持久化与读取](/home/isp/wsps/worktrees/hall-history-window-api/chat/jia-chat-mapper/src/main/java/cn/jia/chat/deliberation/JdbcChatTypedDeliberationStore.java#L84)

## 本轮处置
仅审计并记录候选。不新增读取接口/缓存表，不改数据库，不删历史协议数据，不执行Flow。下一步先确认模型收敛范围；字段/表迁移需要对应写入、读取、约束和历史只读路径一起修改，不能以此报告当作已经实施。

## 用户追问后的语义澄清
- 现有request是受理/聚合单元，turn是该request给某个目标好汉的处理单元；不是“用户消息+助手消息”这一对，也不是模型内部一次工具调用，不直接等同codex-app-server turn。
- ChatDeliberationService受理时同一content循环targetAgentIds，为每个目标创建turn/快照/派发；这属于多目标分发能力，不等同不同指令的协同分工。是否保留此能力必须由实际产品需求决定，不能由表结构倒推。
- 普通议事发送会同时创建一条用户消息和一个request；ChatActionExecutionService原生执行子request复用原user_message_id，因此现状并非全局严格1:1。语义上这是“同一用户消息触发后续内部执行”，不代表用户又发了一条消息。
- 模型收敛方向（尚未实施）：消息记录对话内容；请求明确为一次给一个好汉的处理指令；内部执行作为请求下执行事实，不为了复用受理链再伪装成用户请求。若不保留一request多目标分发且无独立turn生命周期需求，request/turn有合并空间；Runtime实际调用和重试不应自动迫使业务层保留两套状态。
