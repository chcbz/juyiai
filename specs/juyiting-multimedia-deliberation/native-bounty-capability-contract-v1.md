# 原生悬赏执行能力与点将协商合同 v1

日期：2026-09-30。状态：施工合同冻结；不是已实现、已启用或产品验收证明。
源码依据：API `f93febe983afe3619e1b5057937d9db330adece0`、Client `0d4224e2dbbe52788a69be0cb0844f0ad743c6b2`。后续schema修复不改变本协议。

## 1. 与 fast-deliberation 的长期边界

fast `runtimeCapabilities` v1 的 EXECUTE.supported/enabled 仍为 false，旧 `/chat/stream` 不能取得执行权限。原生悬赏执行是独立的已授权 HTTP-poll transport，复用同一平台会话和持久 request/step/execution，并非第二套聊天。

D03 `WORKSPACE_FILE_EXECUTE`、Rabbit command.dispatch、Runtime-v1 心跳、abilities 或fast的CHAT能力，都不能独自证明当前目标支持会话生图。新的注册声明只证明协议和启用的执行器，不证明任务ACL、费用授权、START、Provider成功或交付。

## 2. 注册增量：nativeBountyExecution

在现有 `agent.register` 的正常payload内增加 sibling 字段，不更改原消息封装、runtimeCapabilities或旧客户端语义：

```json
{
  "nativeBountyExecution": {
    "schemaVersion": 1,
    "enabled": true,
    "transport": "PERSONAL_WORKSPACE_CONVERSATION_HTTP_V1",
    "commandSchemaVersions": [1],
    "leaseProtocolVersions": [1],
    "providerStartFenceVersions": [1],
    "resultCommitProtocolVersions": [1],
    "operations": [{
      "operation": "GENERATE_IMAGE",
      "inputManifest": {"schemaVersion": 1,"minItems": 0,"maxItems": 32,"mimeTypes": ["image/jpeg","image/png"]},
      "resultManifest": {"schemaVersion": 1,"minItems": 1,"maxItems": 1,"outputId": "output_1","mimeTypes": ["image/png"]}
    }]
  }
}
```

- 精确键/类型解析；未知键、重复operation、未知版本/transport/operation等不得被忽略或变为READY。缺字段是UNDECLARED，非法声明是UNSUPPORTED；不使fast-v1获得EXECUTE。
- disabled仅允许operations=[]；enabled必须具有上述实际操作合同。v1只声明GENERATE_IMAGE，不广告EDIT、音频生成或澄清续跑已接通。
- 0–32引用和唯一output_1来自当前服务端conversation admission/reference/result实现，不是新设性能门禁；32引用也不意味着用户有这些文件的读取/外发权限。
- 引用为JPEG/PNG、固定版本、task/owner/grant绑定；执行器只物化受权inputs，本地目录不能替代平台资产事实。
- 客户端仅在真实执行器启用、所需本地配置可用、协议实现完整时声明enabled；不能依据fast能力、UI开关或安装过skill推断。不得发起付费探测。
- 两种接应使用同一协议，每个runtimeInstance独立声明；山寨安顿就绪不代表自家接应也就绪。

## 3. 当前注册会话的只读能力源

在agent-api提供只读lookup，在拥有成功注册WebSocket的chat实现。查询参数是服务端确认的tenant/client/owner/canonicalAgent；响应只含state、schemaVersion、transport、operation目录。

状态：READY / OFFLINE / UNDECLARED / DISABLED / UNSUPPORTED / AMBIGUOUS。

READY必须同时证明：
1. AgentService.register成功；精确WebSocket仍open。
2. 绑定tenant/client/owner/Agent/runtimeInstance；仍是AgentRuntimeAuthenticationService的当前binding。
3. 当前API key、注册token摘要、account auth epoch、active identity/binding和runtime online|busy仍有效。
4. 声明enabled且协议/操作受支持。

仅在register、native-auth bind和agent_registered回执成功后激活声明。回执失败、disconnect、显式offline、重注册/替代binding或身份失效后，旧声明不能继续READY；旧session迟到disconnect不能清除新session能力。

lookup不返回session ID、runtime凭据/auth epoch，不写数据库、不claim锁/lease、不调Provider、不做网络探测。身份校验必须复用真实持久身份源；不能因为没有调用方token而跳过注册token校验。存储依赖不可读必须报告source unavailable，不能假装能力未声明或继续执行。

## 4. Owner点将协商HTTP

```http
GET /agent/tasks/{taskId}/point-and-start-capability?targetAgentId=agent-1
```

owner JWT鉴权，服务端精确tenant/client/owner/task/target。仅允许唯一targetAgentId查询参数，未知/重复/非法参数400；跨owner或不存在task/target404；实际支持不足返回200结构化阻塞原因；权威依赖不可读503。所有响应private,no-store，无私有目录、token或费用凭据。

```json
{
  "schemaVersion": 1,
  "taskId": "task-1",
  "targetAgentId": "agent-1",
  "lane": "ORDINARY_SINGLE_AGENT_ASSIGN_AND_START",
  "serverLane": {"state": "READY","blockingReasons": []},
  "nativeExecution": {
    "state": "READY",
    "transport": "PERSONAL_WORKSPACE_CONVERSATION_HTTP_V1",
    "schemaVersion": 1,
    "supportedOperations": ["GENERATE_IMAGE"]
  },
  "authorization": {"state": "UNAVAILABLE","paidExecutionAuthorized": false},
  "newStart": {"eligible": false,"blockingReasons": ["COST_AUTHORIZATION_UNAVAILABLE"]},
  "requestedOperations": ["GENERATE_IMAGE"],
  "initialOperation": "GENERATE_IMAGE",
  "inputRefsPolicy": "EMPTY_ONLY",
  "originalIntentRecovery": {
    "legacyFallbackAllowed": false,
    "unknownOrNotFoundMeans": "RECOVERY_REQUIRED",
    "replayPolicy": "EXPLICIT_USER_EXACT_ORIGINAL_KEY_AND_BODY_ONLY"
  }
}
```

这是条件示例，不是当前服务实际READY。使用nativeExecution作为native能力权威字段；不得复用fast-v1的EXECUTE为其开关。

- serverLane READY/DISABLED/NOT_RUNNING：storage真实enabled、conversation execution flag、WebSocket enable，以及bootstrap/execution relay真实isRunning共同证明；Disabled storage bean存在不等于就绪。两个owner只读入口开关仍需可用，避免写后无恢复。
- supportedOperations只描述当前native声明；requestedOperations取服务端已实现操作、当前native能力和本任务可启动策略的交集。交集仅GENERATE_IMAGE时initialOperation才为GENERATE_IMAGE；否则空集合/null。
- newStart.eligible必须同时具备task新启动资格、serverLane就绪、目标native能力、必要读取/恢复入口和合法费用授权；runtime READY不能独自使其true。
- 当前无合法costAuthorizationRef签发/关联桥，authorization保持UNAVAILABLE/false。后续合法授权状态需独立冻结合同，本v1不凭空定义READY授权或把用户/模型字段当授权。
- 输入策略EMPTY_ONLY是本入口包的真实支持范围；后续必须接通task-file link创建/选择/回读合同才广告TASK_LINKED_REFERENCE。optional reference不是产品非目标，而是剩余必做项。
- 协商GET无写、副作用或Provider调用；是观察不是锁定/授权。真正assign、admit、START和commit继续重新校验，防观察后替代runtime/撤权。

## 5. 浏览器接入与恢复

只接普通单Agent的新办理入口；资金榜、多Agent和原支持legacy行为不变，但不冒充多媒体办理。

- 点击动作使用精确task/target/auth generation；不能借隐藏selectedAgent。
- **一旦同身份task已有persisted-v2原键/正文，永远优先原操作只读恢复，不回落legacy**；capability未声明、disabled、503、原操作404/UNKNOWN都不证明原写不存在。
- remount只GET；显式“继续原点将”才重放原key+原body。不换Agent、版本、inputs或key，不重发首轮聊天。
- newStart不足显示具体缺口；不要发新的v2请求、伪造paid authority或把legacy成功称为生图成功。
- 采用已有grant/task分离、canonical assignment投影、bootstrap初始会话/request和native终态只读恢复组件；不新建第二条议事、不重发“画一只鸟”。

## 6. 费用授权与残留产品工作

现有reward escrow、hosting reserve、skill order、wallet balance和EconomyPostingService都不是本目的的执行同意，不能挪用它们的ID或伪造costAuthorizationRef。原任务grant保持allowOwnTaskDerivedAssets=false、costAuthorizationRef=null直到新合法授权/派生输入合同实装。

本包不代替合法费用签发桥、optional refs、澄清/continuation、EDIT/派生资产、真实Provider、两种接应浏览器验收与版本发布。当前完整“画鸟→修改→保存→正式交付→验收完成”仍NOT_PROVEN。

## 7. 最小验证

- fast-v1正向EXECUTE仍拒绝；native declaration正向/缺失/disabled/非法版本/未知键分开。
- register失败、回执失败、旧session离线、替代注册、scope/key/token/authEpoch失效不得READY，且不泄露secret。
- owner HTTP400/401/404/503、private/no-store、target精确绑定、GET零副作用。
- server disabled/offline/unsupported与费用缺失分别报告；所有supported交集和首轮选择有真实源。
- UI：新意图协商；既有原键绝不legacy；remount零POST、404显式原键重放、task/target/身份切换的迟到结果隔离。
- 客户端enabled仅来自实际可用执行器；不调用Provider来测试声明。
- Owner自检后按exact SHA验证和整合；源代码/协议PASS不等同生产启用或34项产品验收。
