> **现行适用范围（2026-11-07）：** 本文是[所属专题](spec.md)的细则，不独立定义发布/角色/DFX规则；共用[统一开发约束](../architecture-convergence/development-principles.md)。旧日期候选/测试/安装仅代表当时范围，未核实部分不改成今日完成。业务协议/冻结输入不因文档整理改写。

# 用户名乱码存量数据修复计划

## 1. 安全前提

1. 先发布并验证 OAuth strict UTF-8、外部昵称保护和服务器 sender authority；否则修复会被下一次登录/发消息重新污染。
2. 生产只读审计与生产写入分开授权。
3. 本计划不授予生产 DML、LDAP 写、部署、重启或 provider 回读权限。
4. 不在仓库提交含明文/可逆编码昵称的 manifest；明细存放在受控、加密、最小权限位置。
5. 不使用“匹配乱码正则即批量 update”的不可审计脚本。

## 2. 数据分类

| 类别 | 定义 | 自动修复资格 |
| --- | --- | --- |
| A raw reversible | code point ≤ 0xFF；存在高置信 UTF-8 byte pattern；Latin-1 bytes 经 fatal UTF-8 解码成功；round-trip 完全一致 | 可生成自动候选 |
| B percent reversible | 高置信 `%xx` 序列；严格 `decodeURIComponent` 成功；结果通过显示名校验 | 可生成自动候选 |
| C irreversible | C1 bytes 已被删除、出现 replacement char、截断或多次错误转码，无法唯一还原 | 不自动修；需回源/用户确认/可信映射 |
| D normal | 正常 Unicode，或合法西文重音名 | 不修改 |

一个记录只有在候选 after 通过无 control、列长度、round-trip/证据校验后才进入写 manifest。

## 3. 阶段 0：冻结修复算法和应用版本

记录：

- API/Web 已发布 exact commit/tree、Flow Run、artifact SHA-256。
- 离线 classifier 工具 exact commit 与 SHA-256。
- 规则版本，例如 `display-name-repair/v1`。
- 部署后新登录/新消息 smoke 证明没有新污染。

## 4. 阶段 1：只读生产审计

### 4.1 Schema 与连接

只读采集：

```sql
SHOW CREATE TABLE user_info;
SHOW CREATE TABLE chat_message;
SELECT @@character_set_client,
       @@character_set_connection,
       @@character_set_results,
       @@collation_connection,
       @@character_set_server,
       @@collation_server;
```

结论必须区分表默认 charset、列 charset 与当前 connection charset。

### 4.2 用户昵称样本

从授权范围导出最小字段：

```sql
SELECT id, jiacn, nickname, HEX(nickname) AS nickname_hex
FROM user_info
WHERE nickname IS NOT NULL AND nickname <> ''
ORDER BY id;
```

实际导出应经受控通道；普通日志和公开报告不输出 `nickname`。离线 classifier 产生 A/B/C/D 和 reason code。

### 4.3 聊天数据样本

```sql
SELECT id, client_id, jiacn, sender_type,
       sender_name, HEX(sender_name) AS sender_name_hex,
       JSON_VALID(metadata) AS metadata_valid,
       CASE WHEN JSON_VALID(metadata)
            THEN JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.senderName'))
            ELSE NULL END AS metadata_sender_name
FROM chat_message
WHERE sender_type = 'user'
  AND (sender_name IS NOT NULL
       OR (JSON_VALID(metadata) AND JSON_EXTRACT(metadata, '$.senderName') IS NOT NULL))
ORDER BY id;
```

不要把 Agent/system 名称放入人类昵称 classifier。

### 4.4 LDAP 对账

按授权的精确 uid 集合读取：

```text
uid, nickname, entry version/modifyTimestamp（若可用）
```

LDAP nickname 与 MySQL nickname 独立分类，并标记：一致、仅 MySQL 坏、仅 LDAP 坏、两边同坏、两边不同。

## 5. Manifest 设计

### 5.1 受限明细 manifest

建议 JSON Lines，每条包含：

```json
{
  "manifestVersion": "display-name-repair/v1",
  "recordType": "user_info|ldap|chat_message|chat_metadata",
  "primaryKey": "...",
  "ownerJiacnUtf8Base64": "...",
  "ownerJiacnHash": "sha256:...",
  "clientId": "...",
  "senderType": "user",
  "beforeUtf8Base64": "...",
  "afterUtf8Base64": "...",
  "classification": "A|B|C",
  "evidence": "strict_latin1_utf8_roundtrip|strict_percent_utf8|provider_readback|user_confirmed|trusted_identity_map",
  "sourceVersion": "..."
}
```

`before/after` 即使 Base64 仍是 PII，必须加密保存且不入 Git。整个文件计算 SHA-256。

### 5.2 公开摘要

只含：

- manifest SHA-256；
- 规则版本；
- A/B/C/D 数量；
- 各表候选数；
- CAS success/conflict；
- LDAP readback success/failure；
- rollback 状态；
- 不含 id、jiacn、nickname、可逆编码值。

## 6. Dry-run

对每条候选执行但不写：

1. 重新读取当前值和 HEX。
2. 验证仍等于 manifest before。
3. 再次运行 classifier，结果必须与 manifest 一致。
4. 验证 after 满足目标列长度和无 control。
5. 查询关联 LDAP/chat 数量。
6. 输出 `ready/conflict/needs-manual`，固定 dry-run 报告 SHA-256。

输入或规则未变化时，不盲目重复失败请求。

## 7. 用户主数据与 LDAP 修复

MySQL 与 LDAP 无分布式事务，采用记录级补偿状态机：

```text
PLANNED
  -> PRECHECKED
  -> MYSQL_UPDATED
  -> LDAP_UPDATED
  -> VERIFIED
或
  -> CONFLICT / COMPENSATED / MANUAL_COORDINATION
```

### 7.1 MySQL CAS

示意：

```sql
UPDATE user_info
SET nickname = :after
WHERE id = :id
  AND jiacn = :jiacn
  AND BINARY nickname = BINARY :before;
```

要求：

- affected rows 必须等于 1；0 为 conflict，>1 为硬失败。
- 立即按 id/jiacn readback，并比较 `BINARY nickname` 与 after。
- 批量大小根据实际锁耗时和复制状态观测决定，不设置无依据固定门槛。

### 7.2 LDAP 条件写

优先使用 LDAP assertion control：uid、旧 nickname、entry version/modifyTimestamp 同时匹配。若基础设施不支持 assertion：

1. 精确 uid read-before。
2. 当前值必须等于 manifest before。
3. 写 after。
4. 立即 readback。
5. 失败时，仅当 MySQL 当前值仍等于 after，执行 MySQL after→before 条件补偿；若补偿也 conflict，进入人工协调，不覆盖新值。

### 7.3 C 类处理

允许证据：

- provider 通过已授权、安全 API 回读，并能由 immutable provider ID 绑定到该用户；
- 用户在认证会话中明确确认；
- 已验证的 MySQL/LDAP/账号目录可信映射。

不允许：

- 根据 `éæ\u00A0è¶` 猜“最像的中文”；
- 依据聊天正文、联系人备注或同名用户自动推断；
- 用 username 覆盖 nickname 主数据而不记录来源。

## 8. 聊天历史修复

### 8.1 sender_name

仅根据已确认 owner 映射修复人类消息：

```sql
UPDATE chat_message
SET sender_name = :after
WHERE id = :message_id
  AND client_id = :client_id
  AND jiacn = :owner_jiacn
  AND sender_type = 'user'
  AND BINARY sender_name = BINARY :before;
```

### 8.2 metadata.senderName

只有 JSON 合法且路径精确匹配时更新：

```sql
UPDATE chat_message
SET metadata = JSON_SET(metadata, '$.senderName', :after)
WHERE id = :message_id
  AND client_id = :client_id
  AND jiacn = :owner_jiacn
  AND sender_type = 'user'
  AND JSON_VALID(metadata)
  AND BINARY JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.senderName')) = BINARY :before;
```

如果 metadata 无 `senderName`、JSON 非法或已被并发修改，则不补造、不强写，记录状态即可。若列实际类型/数据库版本不支持上述函数，以生产只读审计结果生成等价候选并重新评审。

### 8.3 一致性

同一消息的列值和 metadata 如果都列入 manifest，应在同一数据库事务中执行，各自 affected rows 必须符合预期；否则回滚该事务。修复后通过 owner-scoped API 读取历史，确认 UI 使用服务器 sender identity。

## 9. 回滚

### 9.1 MySQL

```sql
UPDATE user_info
SET nickname = :before
WHERE id = :id
  AND jiacn = :jiacn
  AND BINARY nickname = BINARY :after;
```

Chat sender_name 与 metadata 使用相同 after→before 条件。当前值不再等于 after 时不得回滚覆盖。

### 9.2 LDAP

只有 uid、当前 nickname=after、entry version 符合 manifest 执行上下文时恢复 before；readback 并记录。冲突进入人工协调。

### 9.3 触发条件

- after 与权威回源不一致；
- 应用显示或身份映射回归；
- LDAP/MySQL 无法协调；
- classifier 被证明存在误判。

不因单纯请求慢或性能 SLO 超标回滚正确数据。

## 10. 完成报告

最终报告必须包含：

- 应用版本与 Flow/制品证据；
- 只读审计时间、范围、schema/connection 摘要；
- manifest/dry-run/执行报告 SHA-256；
- A/B/C/D 数量；
- MySQL、LDAP、chat 成功/冲突/补偿/人工项；
- 回滚演练结果；
- 修复后 OAuth 重登、新聊天、历史刷新验证；
- 未解决 C 类清单数量与唯一下一步，不含 PII。
