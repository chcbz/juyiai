# 用户名编码完整性与聊天发送者身份治理验收

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：用户名编码与权威发送者身份。**

### 必须验证的业务结果
中文/emoji与合法西文、缺charset JSON、坏昵称不污染、伪造sender拒绝、可逆/不可逆历史分型、日志无敏感正文。

### 不回归边界
不对所有西文高位字节强制转码；不可逆历史值不猜补；生产修复不因文档更新自动执行；客户端名称不授予身份。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 1. 验收原则

- 每个结论绑定 exact API/Web commit 与 tree SHA。
- 本地静态/单元检查可用于诊断，正式测试、构建、制品和部署以云效同 Run 证据为准。
- “页面看起来正常”不等于数据已修复；“数据库已修”也不等于新污染已阻断。
- 生产数据写验收必须包含授权、manifest SHA、CAS/readback 和回滚证据。

## 2. API 验收矩阵

| ID | 场景 | 预期 |
| --- | --- | --- |
| A01 | Provider 返回 UTF-8 JSON，`Content-Type` 无 charset，昵称为中文 | DTO 与持久化值保持原中文，不出现 Latin-1 mojibake |
| A02 | 微信/微博/GitHub 名称含中文、emoji | 严格解码成功；长度符合生产列能力时正常保存/展示 |
| A03 | UTF-8 BOM + JSON | 只去开头 BOM，JSON 正常解析 |
| A04 | malformed UTF-8 | 安全失败或按可选 profile 策略降级；不产生 replacement char、不写坏值、不记录 body/token |
| A05 | 合法 `José`、`Zoë`、`François` | 原样保留，不进行 Latin-1→UTF-8 误转 |
| A06 | JSON 合法但 nickname 含 ISO control | nickname 被拒绝；已有用户保留旧值；登录主流程按策略继续 |
| A07 | 已有用户的 provider nickname 为坏值 | MySQL 和 LDAP 原好昵称均不被覆盖 |
| A08 | 新用户 nickname 无效 | 身份可建立时使用 username/jiacn fallback，不持久化乱码片段 |
| A09 | 同一用户重复 OAuth 登录 | 不会反复污染或把修正值覆盖回坏值 |
| A10 | 客户端 POST 伪造 `senderType=agent`、`senderName=宋江` | 服务端忽略；持久化和事件仍是认证 user 的权威身份 |
| A11 | metadata 使用标量伪造 sender 字段 | 字段不从客户端 allowlist 进入；服务器值覆盖所有别名 |
| A12 | 普通 `/chat/stream` | Advisor 保存的 sender 与 resolver 结果一致 |
| A13 | 聚义厅 direct relay | `chat_message`、外层/内层 Agent payload、metadata 使用同一 sender |
| A14 | 内建宋江 fallback | 用户消息为权威人类 sender；Agent 消息继续是服务器常量 |
| A15 | Agent WS payload 伪造其他 Agent 名称 | final/delta/DB 均使用 session agentId 对应 runtime/persona 名称 |
| A16 | Agent runtime name 缺失/非法 | 依次回退 personaName、agentId，无控制字符 |
| A17 | 数据库 nickname 为可逆 raw mojibake | 请求内存解析可恢复用于显示，但请求路径不写库 |
| A18 | 数据库 nickname 为 `éæ\u00A0è¶` 等不可逆值 | 不猜测，回退 username/context username/jiacn/`用户` |
| A19 | provider 非 2xx | 安全错误，不记录 URL secret/query/body |
| A20 | 事务内调用 OAuth provider | 继续被拒绝，现有事务边界不退化 |

## 3. Web 验收矩阵

| ID | 场景 | 预期 |
| --- | --- | --- |
| W01 | `陈惠超` 正常 Unicode | 所有页面一致显示 `陈惠超` |
| W02 | raw Latin-1 mojibake `é\u0099\u0088æ\u0083\u00A0è¶\u0085` | 先恢复为 `陈惠超`，不会先删除 C1 字节 |
| W03 | percent-encoded UTF-8 | 高置信、合法编码恢复；malformed 保留后安全清洗 |
| W04 | 已截断 `éæ\u00A0è¶` | 不误称已恢复；自己的消息显示“你”，其他位置走稳定 fallback |
| W05 | 合法西文重音名 | 不改写、不丢字符 |
| W06 | emoji/扩展 Unicode | 不损坏、不出现 replacement char |
| W07 | 个人中心与聚义厅账户入口 | 使用同一 helper，结果一致 |
| W08 | 聚义厅乐观 USER 消息 | 立即显示“你”，不显示全局 nickname 乱码 |
| W09 | 普通聊天发送请求 | request 不再包含权威 senderName/senderType |
| W10 | 聚义厅发送请求 | request 不再包含权威 senderName/senderType |
| W11 | 刷新并加载历史 | 本人按稳定 identity 显示“你”，Agent 显示服务器名称 |
| W12 | SSE final/delta | 同一 Agent 名称一致，不被 payload 碎片或本地 helper 改坏 |
| W13 | 身份切换 | 旧 identity 的消息/缓存不被标成新用户本人 |
| W14 | 空 nickname/username | UI 使用规定 fallback，不留空标签或乱码碎片 |

## 4. 数据审计与修复验收

| ID | 场景 | 预期 |
| --- | --- | --- |
| D01 | `SHOW CREATE TABLE` 与 connection charset/collation | 只读证据归档；不以测试 schema 冒充生产事实 |
| D02 | A 类 raw mojibake | 仅严格逆转、round-trip 成功的记录进入自动候选 |
| D03 | B 类 percent encoded | 仅严格 percent UTF-8 解码成功的记录进入自动候选 |
| D04 | C 类 stripped irreversible | 不自动猜；要求 provider 回读、用户确认或可信映射 |
| D05 | D 类正常 Unicode | 不进入写 manifest |
| D06 | `José/Zoë/François` | 明确属于 D 类，不误修 |
| D07 | manifest | 受限明细与公开摘要分离；两者均有 SHA-256，公开摘要无 PII |
| D08 | MySQL nickname | `id + BINARY before` CAS；0 行视为 conflict，不重试覆盖 |
| D09 | LDAP nickname | 条件写/readback；失败触发记录级补偿或协调清单 |
| D10 | chat sender_name | 仅 owner/client/user sender/旧值精确匹配时修改 |
| D11 | chat metadata | 仅 `JSON_VALID` 且路径旧值精确匹配时修改 |
| D12 | Agent/system 消息 | 不进入人类昵称批量修复 |
| D13 | 回滚演练 | 只有当前值仍等于 after 时恢复 before；冲突不覆盖 |
| D14 | 修复后再次登录和发消息 | 不产生新坏值，历史刷新保持正确 |

## 5. 安全与可观测验收

- [ ] 日志、指标 label、公开报告均不包含 token、provider body、明文 nickname、Authorization header 或 secret URL。
- [ ] spoof 指标只记录 channel/计数，不记录伪造名称。
- [ ] sender identity 查找使用认证 jiacn/clientId，不接受 request owner alias。
- [ ] 读取/写入会话继续遵守现有 owner/client/conversation generation 校验。
- [ ] 没有通过绕过锁、伪报成功、取消慢请求或新增任意 deadline 达成验收。

## 6. 云效与发布证据

- [ ] API Flow pipeline：`5260799 / cyf-api-release`。
- [ ] Web Flow pipeline：`4403172 / cyf-web-release`。
- [ ] exact API commit/tree：待实现后填写。
- [ ] exact Web commit/tree：待实现后填写。
- [ ] Flow Run IDs：待填写。
- [ ] 测试摘要：待填写。
- [ ] artifact SHA-256：待填写。
- [ ] 部署顺序：API → Web → 线上验证 → 数据只读审计 → 获授权的数据修复。
- [ ] 实际健康与功能 readback：待填写。

## 7. 当前证据状态（2026-09-26）

| 项目 | 状态 |
| --- | --- |
| 截图与编码复现 | 已完成 |
| 固定 API/Web 源码审计 | 已完成 |
| 根因设计与任务拆分 | 已完成 |
| API 实现/测试 | 未开始 |
| Web 实现/测试 | 未开始 |
| 生产只读数据审计 | 未授权、未执行 |
| 生产修复 | 未授权、未执行 |
| 发布与线上验收 | 未开始 |
