# 用户名编码完整性与聊天发送者身份治理

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行规格（2026-11-07）

**本专题：用户名编码与权威发送者身份。**

### 责任与业务流程
OAuth适配器正确解码；账户服务保护主数据；聊天入口解析可信发送者；Web统一展示。

外部字节按协议解码→来源校验→不覆盖已有好值→服务端确定发送者→安全展示。

### 明确边界
不对所有西文高位字节强制转码；不可逆历史值不猜补；生产修复不因文档更新自动执行；客户端名称不授予身份。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。业务字段、状态、错误及测试细节仍由本专题下文和详设维护。

### 验收落点
中文/emoji与合法西文、缺charset JSON、坏昵称不污染、伪造sender拒绝、可逆/不可逆历史分型、日志无敏感正文。

存量修复只按[专用数据修复计划](data-repair-plan.md)及实际授权执行；该计划不是生产DML授权或当前已完成证明。

**入口：** [需求](spec.md) · [设计](design.md) · [实施](tasks.md) · [验收](acceptance.md)

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


> 文档收口（2026-10-23）：保留编码/身份合同、源码审计及未授权数据修复方案；它不是可删除的已完成临时修复。 本轮仅核对文档归属与覆盖，不重新验证源码/上线；执行规则以根AGENTS为准。


- Feature ID：`username-encoding-integrity`
- 生命周期：`draft`
- 基线确认日期：2026-09-26（Asia/Shanghai）
- 适用仓库：根仓、`api/`、`web/`

## 问题

聊天中用户名会出现 `éæ\u00A0è¶` 一类乱码，而且个人中心、聚义厅账户入口与聊天消息可能表现不一致。问题不是单一 CSS、字体或数据库字符集故障，而是四层问题叠加：

1. OAuth 专用 HTTP 客户端自行创建 `RestTemplate`，使用 `StringHttpMessageConverter` 的默认字符集解释未声明 `charset` 的 JSON；UTF-8 中文字节可能被按 ISO-8859-1/Latin-1 解码。
2. OAuth 回调把第三方昵称直接交给通用 `upsert`，现有用户登录时也会把坏昵称写入 MySQL，并同步到 LDAP；因此第三方重复登录可反复污染已修正数据。
3. 聊天 HTTP/Advisor/聚义厅转发链信任客户端提交的 `senderType`、`senderName`，既会把乱码固化到 `chat_message`，也允许客户端伪造展示身份。
4. Web 有三套名称清洗逻辑。聊天逻辑先删除 C1 控制字符，破坏了 mojibake 可逆恢复所需字节；个人中心与聚义厅账户入口虽有兼容恢复，聊天仍可能显示被截断后的 `éæ\u00A0è¶`。

截图中的现象可以由“`陈惠超` UTF-8 字节被按 Latin-1 解码，再删除 C1 控制字符”精确复现，详见 [source-audit-20260926.md](./source-audit-20260926.md)。

## 目标

1. **阻止新污染**：所有外部 OAuth JSON 以字节接收并严格按 UTF-8 解码，不能再依赖缺失 `charset` 时的 String converter 默认值。
2. **保护账户主数据**：第三方昵称经过来源专属校验；异常昵称不得覆盖已有好值，也不得因重新登录重复污染 MySQL/LDAP。
3. **建立服务器权威身份**：用户及 Agent 的 `senderType`、`senderName` 均由已认证主体和服务器数据解析，客户端字段只做兼容接收，不参与权威结果。
4. **统一 Web 展示**：全站使用同一显示名兼容函数；可逆历史值恢复后再清除控制字符，不可逆值安全回退。
5. **修复存量数据**：以只读审计、分型、可复核 manifest、compare-and-set、readback 和条件回滚方式修复 MySQL、LDAP 与聊天历史。
6. **建立可观测闭环**：能区分 provider 解码失败、昵称拒绝、运行时 fallback、历史修复候选与不可逆记录，不记录 token、响应 body 或明文昵称。
7. **消除身份伪造面**：普通聊天、聚义厅 relay、Advisor、Agent WebSocket、持久化 metadata 和事件展示使用同一权威身份。

## 非目标

- 不把所有西文高位字符一律做 Latin-1→UTF-8 转码；`José`、`Zoë`、`François` 等合法名字必须原样保留。
- 不用前端“看起来正常”替代后端根因修复或存量治理。
- 不通过扩大任意超时、增加性能 deadline、取消请求或伪报成功来处理编码问题。
- 不在本规格阶段执行生产 DML、LDAP 写入、部署、重启或付费操作。
- 不改造与显示名无关的用户名登录规则、Jia 账号规则或第三方账号绑定模型。
- 不自动猜测已经丢字节的名称；不可逆值必须回源、用户确认或回退稳定账号标识。

## 范围

### API

- `oauth/jia-oauth-service`
  - OAuth provider 响应的严格 UTF-8 解码。
  - 第三方显示名校验和 source-aware 更新策略。
- `user/jia-user-api`、`user/jia-user-service`
  - 当外部身份资料需在应用内更新时提供“外部身份资料更新”窄接口；不得把来源专属转码放入通用用户编辑路径。
  - MySQL/LDAP 的保留旧值语义与测试。
- `chat/jia-chat-service`
  - 认证用户发送者解析器。
  - `/chat/stream`、Advisor、聚义厅 relay、Agent payload、持久化消息和 metadata 的身份收敛。
  - Agent WebSocket 发送者名称根据已认证 session agentId 和 runtime/persona 解析。
- 数据治理
  - `user_info.nickname`、LDAP nickname、`chat_message.sender_name` 及合法 JSON metadata 中 `senderName`。

### Web

- 新增共享显示名工具，替换个人中心、聚义厅账户入口、聚义厅聊天与普通聊天的重复逻辑。
- 客户端不再发送权威 `senderName`/`senderType`。
- 当前用户消息显示“你”；历史消息通过服务器返回的稳定身份字段判定是否为本人。
- 历史 raw mojibake/percent-encoded 值仅做兼容恢复；不可逆值回退。

### 测试、发布与证据

- API/Web 实现完成后，对 exact SHA 运行相关云效测试、构建、同 Run 制品发布与实际健康核验。
- 数据修复独立于应用发布，必须在新污染阻断上线后、完成只读审计且得到生产写授权后执行。

## 需求分层

| 层级 | 必须结果 | 失败行为 |
| --- | --- | --- |
| 根因修复 | Provider JSON 严格 UTF-8 | 响应整体不是合法 UTF-8/JSON 时安全失败；不记录敏感 body |
| 新污染阻断 | 异常昵称不覆盖好值 | 昵称字段异常时保留旧值；可从可信账号标识回退并继续可用流程 |
| 身份权威 | 客户端不能决定 sender identity | 忽略兼容字段，使用认证上下文和服务器实体 |
| UI 兼容 | 同一值在各页面显示一致 | 可逆则恢复；不可逆则显示“你”或稳定 fallback，不显示碎片乱码 |
| 存量治理 | 可审计、可回滚、无盲改 | CAS/readback 不满足即停止该记录并报告，不覆盖并发变更 |

## 约束和风险

- 当前根仓、`api/`、`web/` 工作树均存在大量其他用户变更；本规格只新增本目录，不修改 `specs/INDEX.md`。
- `web/` 本地 checkout 落后于 `origin/develop` 且有用户修改，源审计基于固定的远端 revision，不 reset、不覆盖。
- MySQL 与 LDAP 无跨系统原子事务，修复需显式补偿状态机。
- 聊天历史可能包含人类、Agent、system 三类发送者；修复必须按 owner、client、sender_type 和旧值精确限定。
- `éæ\u00A0è¶` 一类已删除 C1 字节的值不可逆；自动猜测会造成错误身份展示。
- 身份/ACL 和生产数据修复属于高风险范围，由任务 Owner 自检并保留恢复边界；不创建独立 Reviewer。

## 完成定义

只有同时满足以下条件才可从 `draft` 提升为 `accepted`：

- 新 OAuth 流量不再生成 mojibake；第三方重复登录不能覆盖已有好昵称。
- 客户端伪造 sender 字段不会影响 HTTP、SSE、Advisor、Agent relay、WebSocket、数据库或 UI。
- 个人中心、聚义厅入口、普通聊天和聚义厅聊天使用统一显示规则。
- 存量审计完成并给出 A/B/C/D 分型；获授权的修复完成 CAS/readback/回滚演练。
- exact API/Web SHA 的云效证据、制品 digest、部署顺序和线上验证均已记录。
