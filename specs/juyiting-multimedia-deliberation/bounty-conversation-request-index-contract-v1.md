# 悬赏同会话 request / 多稿发现：只读合同 v1

日期：2026-10-01。Main 冻结追加施工合同；**不是已实现接口，不是产品验收**。API源基线 `42d6e7e4196cbde7e0a8fe5a41d3e909d954fc3d`，Web源基线 `4f21fa4227bb8854f0bed41f926acd77084e5aad`。保持既有 RequestView、output、assetRef、archive、finalization、v1/v3每意图授权不变。

## 1. 已证实缺口与长期闭合

现 `BountyExecutionOutputs.vue` 只读取 activeRequest；F1受理只toast，换activeRequest清空旧稿；事件reducer过滤其他request；会话history与已知ID GET无法在刷新后发现所有稿。新增服务端owner权威只读索引，Web维护独立全会话catalog。activeRequest保留忙碌/取消/当前交互焦点，不是历史资产容器。此索引包含同会话所有可读request（CHAT、INSPECT、EXECUTE及旧终态）；只有既有outputs端点能证明成果存在。

**历史读取与当前执行资格分离**：已完成任务、已消费或失效grant不影响合法owner读取已产成果；不得复用仅能返回ACTIVE grant的 `interactions/context` 作为索引前置。当前编辑/正式选择仍逐次按各自权威端点验证；索引不会给予旧assignment成果当前写权限。

## 2. HTTP与精确投影

`GET /chat/conversations/{conversationId}/requests`

沿用用户JWT与EsContext owner/client/tenant解析，不接受浏览器owner、client、tenant、task、target、grant或SQL排序字段。响应成功与错误均用现JsonResult，`Cache-Control: private, no-store`。沿用 `chat.bounty-media.enabled` 的默认关闭边界；关闭时不可伪造空目录/支持能力。

唯一允许query（均单值；重复或未知query、非空body为400）：

| 参数 | 类型与语义 |
| --- | --- |
| expectedGeneration | optional canonical正decimal string。首扫无已知generation时可省略；已知时必须携带。分页续读（after>0或提供through）必须携带服务器首响应generation。 |
| after | optional canonical非负decimal string，默认 `0`；是已读最后一个数据库ordinal，不是用户/资产ID。 |
| through | optional canonical非负decimal string；首扫省略时取该exact scope当时可见MAX(chat_request.id)，无行则 `0`。续读固定原through，不可跟随增长。after>0时必须提供through，after<=through。 |
| pageSize | optional canonical正decimal；缺省/超大clamp复用已有JsonRequestPage DEFAULT_PAGE_SIZE/MAX_PAGE_SIZE（当前100），不是产品总上限。不能因超过100拒绝请求或停止后续页。 |

cursor/ordinal/generation上界是源库signed BIGINT支持的 `9223372036854775807`，不是性能门槛。拒前导零、符号、浮点/指数、JS number转换精度丢失。pageSize解析同样不先转JS number，超现有最大值只clamp。

JsonResult.data仅以下字段：

```json
{
  "schemaVersion": 1,
  "scope": {
    "conversationId": "conversation_1",
    "conversationGeneration": "1",
    "taskId": "task_1"
  },
  "after": "0",
  "through": "12",
  "nextAfter": null,
  "hasMore": false,
  "entries": [{
    "ordinal": "12",
    "request": {
      "requestId": "request_1", "requestRevision": "1",
      "conversationId": "conversation_1", "conversationGeneration": "1",
      "userMessageId": "101", "state": "COMPLETED", "stateVersion": "2",
      "turns": [],
      "steps": [{
        "stepId": "step_1", "stepNumber": "1", "taskId": "task_1",
        "assignmentRevision": "0", "targetAgentId": "agent_1",
        "kind": "EXECUTE", "state": "COMPLETED", "stateVersion": "2",
        "executionIntentId": "intent_1", "executionId": "execution_1",
        "executionState": "OUTPUT_COMMITTED"
      }]
    }
  }]
}
```

嵌套request **复用现 `ChatDeliberationService.RequestView`/StepView/TurnView原定义与既有状态域**；上例不是新状态域规范，不扩写事实/私有manifest。scope不含当前target/assignment/grant，request.steps携带不可改写的历史target/assignment。先校验所有row/request/step scope，再整页交付；不部分返回混入scope的页。

每条ordinal严格递增且 `after < ordinal <= through`；每页requestId不重复。hasMore必须boolean；true时entries非空且nextAfter等于最后ordinal；false时nextAfter=null（最后页可以非空或为空）。through=0只可空entries/false/null。所有ID按既有exact非空ID/codepoint域；版本按原字段正/非负decimal域，assignmentRevision可 `0`。EXECUTE link/steps或必需存储不可用是503，不能伪造空steps。旧纯CHAT无steps仍可读。

## 3. Owner/数据安全与实现落点

每页read-only事务以认证来源取scope；tenant沿用当前任务领域固定0的支持边界，未支持tenant不猜0、不跨租户读。必须证明：

1. conversation exact tenant/client/owner，ID匹配、未deleted、generation>=1、type=juyiting、scopeType=bounty、scopeKey=`task:<taskId>`、persisted taskId合法；expectedGeneration若提供必须当前一致。
2. task root以 `AgentTaskMetaDao.findByTaskIdInOwnerScope(tenant,client,owner,taskId)` 读回且完整owner/client/tenant/task一致；允许已完成/取消/撤权后历史读，不要求task可执行或ACTIVE grant。
3. index SQL的MAX与页谓词都同时含exact tenant/owner/client/conversation/generation，绝不全表分页再过滤，绝不仅凭cursor读取；绑定值SQL，不浏览器ORDER BY。
4. 每row复用既有 getRequest 读取，再验证requestId/revision/conversation/generation、所有StepView.taskId exact当前会话task；历史step target/assignment保留，不强行等于当前target/assignment；同task/同conversation/generation的旧target可标为历史草稿，不混入当前写/验收资格。getRequest继续校验turn/step/link身份，不绕过已知ID/输出/字节ACL。
5. 事务一致读取保障该页scope与数据确实共存；不使用逆序锁，原则上纯SELECT一致快照足够。并发删除/改派允许当时真实可读快照或typed conflict，不承诺响应发送时仍最新；每次后续读/下载/写照常重鉴权，Web按自身fence抑制迟到响应。

业务零写：不触发repair/bootstrap/bind/grant/consent/step/request/message/outbox/execution/START/Provider，不更新版本/updated_at，不读取附件/输出字节，无新DDL/迁移/索引硬门禁。引用既有task DAO不扩大其权限。

候选新增路径（均与当前API74path Owner不重叠）：mapper的 `ChatBountyRequestIndexStore`、service的 `ChatBountyRequestIndexService`、api的 `ChatBountyRequestIndexController`，及chatDeliberationTest下三个同名Test。不修改现74paths、build.gradle或既有接口；使用现chatDeliberation sourceSet纳入测试。独立正式验证矩阵由Main在完整child后固定。

## 4. 分页一致性：不作虚假的快照承诺

首扫记录through，keyset每页ORDER BY id ASC、读既有pageSize+1探测hasMore，移除探测行后投影。不允许只下载第一页，逐页直到false；没有总行数/总轮数/等待deadline产品门槛。cursor仅扫描坐标，不签发authority；换cursor不能逃过每页scope ACL。

**跨HTTP页不是同一个MVCC快照**。自增ID不代表commit顺序：低ordinal事务晚提交可能被一次扫描遗漏；状态/asset projection也会在扫描期间推进。因此启动/重连、受理、part.ready或显式刷新均进行从after=0的新扫（through重新取）；周期轮询沿用当前机制只为调度，不是失败门槛。发现新row/状态后merge，单次缺失不能当删除依据；直到真实owner-safe404/任务/身份/会话generation失效才撤去该scope。不要仅从最后through增量扫描，也不要因单次空页清除旧稿。晚提交低ID与多于一页必须实际数据库/Web用例覆盖。

索引不返回eventCursor，不宣称同步冻结事件/资产版本。part.ready是read hint，不是已产资产证明；已有outputs/assetRef/内容摘要端点为产物权威。

## 5. 错误与可用性

| HTTP | code |
| --- | --- |
| 400 | BOUNTY_REQUEST_INDEX_INVALID_REQUEST：path/query/body或cursor域错误 |
| 401 | 沿用现标准鉴权 |
| 404 | BOUNTY_REQUEST_INDEX_NOT_FOUND_OR_FORBIDDEN：其他owner/client/tenant、非本悬赏、deleted、无合法owned task |
| 409 | BOUNTY_REQUEST_INDEX_CONFLICT：已知本scope generation不符/本页上下文矛盾 |
| 503 | BOUNTY_REQUEST_INDEX_UNAVAILABLE：真实数据库/必要投影存储不可用或持久link损坏；不以SLO慢/预算拒绝 |

异常不得漏出路径、私有facts、Provider绑定、源bytes、其他owner对象存在性。暂时503保留已验证旧稿与可重试提示；页面禁止自动POST、随机探测ID、伪造已完成或重建执行。真实传输timeout/用户取消/身份切换仍按已有处理，不增加等待总时限。

## 6. Web独立catalog与写资格

新增 `useHallBountyRequestCatalog.js` + 纯验证primitive。scope唯一identity/auth generation/conversation/task；每个await捕获Hall已有task/requirement/target/assignment/disposal fence和scan generation。首次无已知conversationGeneration只做read-only发现，不能拿未验证response建立执行权限；后续页验证同scope/generation/through。切换身份/会话/任务清catalog、撤Object URL并失效旧await；activeRequest移动不得清历史catalog。

request merge分别比较request aggregate、每个turn、每个step的既有stateVersion，不得仅凭request.stateVersion相等就拒绝正常step/link推进（它们是不同领域版本）。同requestId/revision的immutable字段不同是wire冲突；各自版本相等但对应state不同是wire冲突；旧版本不覆盖新版。EXECUTE link没有返回独立version时，使用同一scan/readback串行与scan fence避免迟到视图覆盖，不伪造link版本或跨页MVCC保证。

同scope扫描串行，受理/event hint合并为待刷新标记，不重入并行无限POST/GET；失败结束当次读取但保留已验证条目，之后真实事件或用户/现轮询可重新读。不要反复盲重试同失败输入，也不能因一个未projection request挡住其他已完成稿。

F1 onAdmitted与相关part.ready只通知catalog权威重读，不凭receipt/event追加合成成功稿、不切坏初始bootstrap guards。`useHallConversation`的active request事件边界不放宽：另返回狭窄只读read-hint接口/订阅，避免其他request夺走当前忙碌/取消焦点。

gallery按catalog中request.steps发现所有合法EXECUTE，保留完整 `(requestId,stepId,outputId)`、sha256/MIME/byteLength、原服务器输出URL、assetRef/revision及draft source。同output_1跨request不碰撞，旧稿预览/下载/归档source不被activeRequest更新覆盖。outputs/bytes仍通过原端点及摘要验证；没有assetRef时不得主动归档，却仍可安全预览已验证output。

**读得见不等于可编辑/可验收**：旧assignment/target草稿可读，但编辑走current context/新意图授权及对应source resolver；正式选择只接受当前finalization合同允许的task/assignment/版本tuple。不能将历史StepView改写成当前assignment或借当前grant验收；混scope选择本地抑制且服务器保持最终权威。无current context时历史预览/下载仍可用，新写action禁用或独立显式校验。

## 7. 真实自检与验收项（当前全部NOT_RUN）

API：真实MVC envelope/no-store/query/body/default-off/JWT隔离；真实isolated MySQL owner/client/tenant/generation过滤、分页101+、晚提交低ID二扫补发现、终态任务/失效grant可读、strict step/link/task scope、全业务行/版本/updated_at零写、concurrent deletion typed结果。测试必须经orchestrator串行，不操作foreign服务。

Web：实际Vue/Page初始+F1两request保持旧稿；无localStorage刷新恢复；两个output_1完整键；超过一页与晚commit重扫；part.processing不claim/part.ready only hint；失效await无UI写/无POST；旧assignment预览不current验收；archive原key及verified byte/MIME/hash回归。fixture只绑定预期，静态检查不是上述通过。

自然ANSWER/CLARIFY/EXECUTION_PROPOSAL、真实INSPECT、音频/文件输入与双接应仍独立闭环；本合同不缩减完整34产品/29桥、真实Provider/浏览器/发布目标。
