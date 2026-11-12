# codex-bridge（原 codex-ws-agent）接口文档与对接方案

## 2026-10-29 当前注册与文本容量（局部核对）

本节仅核对 API `de6776fb3092a3e71aa5004d115c1280b742f2aa` 与 Runtime `a4940cbb21342e9acfbc7904e4bc48e4241c097e`；下文旧协议、独立服务与 CLI 路径仍为历史说明，不能据此执行。公共信封以 `api/docs/interface-standard.md` 1.2 为准。

- Agent 端点单独设置文本接收容量 **65,536 UTF-16 code units**（当前 Tomcat 口径），不是 UTF-8 字节/压缩帧大小，也不是附件上传限制；超过容量由容器1009关闭，不截断协议消息。普通聊天、二进制和数据库容量不联动修改。
- 注册删除无消费者的 `inputCarriers` 和现代路由不需要的固定重复描述。保留身份/会话、白名单能力、六字段 `runtimeCapabilities`、实际消费的材料/原生执行声明及当前技能目录；API先升级以接受精简声明，再升级Runtime。
- 周期心跳/状态不携带技能目录或重复能力，不把历史ACK、结果、技能旧版本累加进注册；不能再按下文旧“每次presence重新合并全部技能”实现。
- 当前技能目录和支持输入类型集合仍可按数量线性增长；64K及去重不是无限容量保证。不静默截断、不擅设技能数量上限，也未新增分片/差量同步框架。
- 必要性、字段取舍和增长实测见 `specs/juyiting-skill-execution/management-contract.md` 本日末节；源码、正式测试、独立主机安装、连续通道验证及遗留限制分别见 `docs/implementation/handoffs/CODEX-NATIVE-SKILLS-20261027.md` 最新记录。


> **2026-10-26命名与修复**：源码和安装候选已改为 `isp-install/conf/codex-bridge/`；2026-10-26线上已通过Flow5264702/65迁移至`app/codex-bridge/`（Runtime1.3.11 / d97449c），task530改图与验收通过。当前任务合同、必要校验及验证状态见 `docs/implementation/handoffs/CODEX-BRIDGE-REPAIR-20261026.md`（仓库根相对路径）。以下旧路径/协议作为历史说明保留，不据此部署。

> **本机运维入口更新（2026-10-12）**：下文独立服务及 `/home/isp/apps/codex-ws-agent` 部署路径为历史说明，不能再照此启动。本机已统一到 `cyf-agent-runtime-v1@unified`，旧目录归档、旧服务masked；现行路径见 `/home/isp/docs/SERVER_ARCHITECTURE.md` 与 `docs/juyiting-runbook.md` 的目录收口小节。内嵌执行库仍保留。本次路径核验对应 Runtime1.0.2/源码 `5b902c1bcd3efced9720e015e3b8240d39ce0738`，并非下文全部协议内容的重新核验。

## 一、架构概览

```
┌─────────────────┐                    ┌─────────────────┐
│  codex-ws-agent  │  ws://host:10018  │   CYF API       │
│  (另一台服务器)  │ <──────────────> │   (port 10018)   │
│                  │  /ws/agent/channel │                 │
│  Node.js 20+     │                    │  Spring Boot    │
│  + codex CLI     │                    │  + WebSocket    │
└─────────────────┘                    └─────────────────┘
```

- 通信方式：WebSocket (JSON 文本帧)
- 认证方式：URL 参数 `api_key`
- 心跳间隔：30s，重连窗口 30 分钟（指数退避）

---

## 二、WebSocket 接口

### 2.1 连接

```
GET ws://<host>:10018/ws/agent/channel?api_key=<API_KEY>
```

成功握手后服务端下发：

```json
{"type":"connected","sessionId":"...","channel":"agent",
 "capabilities":["chat.stream","chat.stop","ping","agent.register","agent.status","agent.message","task.assign","task.report","task.event"]}
```

### 2.2 上行 (Agent → Server)

| type | 说明 | 关键字段 |
|------|------|---------|
| `agent.register` | 注册 | `agentId`,`name`,`personaName`,`abilities[]` |
| `agent.status` / `agent.presence` | 更新状态并刷新能力 | `agentId`,`status`(online/busy/offline/error),`abilities[]`,`currentTask?` |
| `agent.message` | 发送回复 | `agentId`,`conversationId`,`conversationType`,`content`,`senderName` |
| `agent.message.delta` | 流式增量 | `agentId`,`conversationId`,`content` |
| `task.report` | 任务回报 | `agentId`,`taskId`,`status`,`output`,`errorMessage?`,`durationMs` |
| `capability.lookup` | 查询聚义厅能力名册 | `requestId?` |
| `ping` | 心跳 | 需带 `requestId` |

### 2.3 下行 (Server → Agent)

| type | 说明 | 关键字段 |
|------|------|---------|
| `connected` | 连接成功 | `sessionId`,`capabilities[]` |
| `agent_registered` | 注册确认 | `agentId` |
| `pong` | 心跳响应 | 回显 `requestId` |
| `agent_direct_message` | 厅内传令(核心!) | `conversationId`,`conversationType`,`content`,`agentId`,`senderName`,`metadata` |
| `task_assigned` | 任务委派 | `taskId`,`title`,`status` |
| `task_event` | 任务事件 | `eventType`,`taskId`,`title`,`status` |
| `agent_status` | 广播状态 | `agentId`,`status`,`currentTask?` |
| `agent_capability_index` | 宋江首领能力名册 | `agents[]`，包含 `agentId`,`abilities`,`roles`,`status`,`collaborationHint` |

所有消息 JSON 顶层含 `type`,`requestId`,`agentId`,`senderType`,`senderName`。

### 2.4 对接流程

**注册上线：**
```
Agent ──connect──> Server
Agent <──connected── Server
Agent ──agent.register──> Server   (agentId, name, abilities)
Agent <──agent_registered── Server
Agent ──agent.status──> Server     ("online")
```

**厅内传令（聚义厅）：**
```
Server ──agent_direct_message──> Agent   {conversationId, content, agentId}
Agent ──agent.message──> Server          {content: "结果...", agentId}
Agent ──task.report──> Server            {status: "completed", output, durationMs}
```

**任务委派：**
```
Server ──task_assigned──> Agent   {taskId, title, status}
Agent 执行 codex exec ...
Agent ──task.report──> Server     {taskId, status: "completed"}
```

---

## 三、codex-ws-agent 详设

### 3.1 目录结构

```
/home/isp/apps/codex-ws-agent/
├── .env                       # 环境变量
├── .codex/                    # $CODEX_HOME（config.toml, auth.json, session_index.jsonl）
├── .codex-wuyong/             # Profile 独立 CODEX_HOME
├── .codex-linchong/
├── agent-client.mjs           # 主程序
├── codex-profiles.conf        # Profile 定义 (INI格式)
├── package.json               # {"type":"module"}
└── logs/                      # 启动+运行日志
```

### 3.2 核心机制

**多 Profile**：一个进程管理多个 Codex 实例，各自独立 WebSocket 连接。

**重连**：断开后指数退避重连 (1s→2s→4s→8s→16s→30s)，error 后 1s 内无 close 则强制重连，防止卡死。

**能力刷新**：客户端在注册和每次 presence 心跳时，重新合并基础能力、profile 的 `abilities`/`skills` 配置，以及 profile `CODEX_HOME`、插件缓存和工作区内发现的 `SKILL.md` 名称。后端将其写入 `agent_runtime.abilities`；persona abilities 只用于旧客户端首次接入 fallback。

**Profile 热加载**：运行中监听 `CODEX_PROFILES_FILE`，新增 `[agent.*]` 自动接入，删除 profile 自动发送 `offline` 并关闭连接，变更关键配置时仅重连对应 profile。配置写坏或半写入时跳过本次重载，继续使用上一份有效配置。

**Codex 调用**：收到 `agent_direct_message` 或 `task_assigned` 后，通过 `spawn(codexBin, ["exec","--cd",workdir,"--skip-git-repo-check",prompt])` 执行，结果通过 WebSocket 回报。

**厅内回复**：Codex 执行完毕后自动发送 `agent.message` + `task.report`，前端聚义厅界面实时显示。

### 业务会话与 Codex 会话

- `codexSessionMode=resume` 只续接 `agentId:conversationId` 的准确映射，且会话必须存在于该 profile 的 Codex Home；无映射执行 new，不再回退 `--last --all`。映射会话丢失明确失败。
- 当前 CLI 的 `thread.started/thread_id` 用于保存映射；不再按 Home 最近修改的文件猜测本轮会话归属。显式 new 与隔离任务 workspace 的 forceNew 保持独立新建。
- 聚义厅“话头记录”展示当前用户/聊天范围的业务历史，选择后继续使用原 conversationId；“另起话头”下次发送才创建新会话。历史不是 Codex 工具日志，不自动清理历史文件。
- 旧版本已经将多个业务 ID 映射到同一 Codex session 的记录会保留；本次不自动拆分混合历史。要开始干净上下文，请另起话头。
- 设计、准确候选与验证/发布证据：`specs/juyiting-conversation-sessions/`。版本源码在 `/home/isp/wsps/chcbz/isp-install/conf/codex-ws-agent/`，本机现用部署副本在 `/home/isp/apps/cyf-agent-runtime-v1/app/codex-ws-agent/`。2026-10-23固定目录迁移记录见 `docs/implementation/handoffs/RUNTIME-FIXED-DIR-20261023.md`：沿用Runtime1.2.6，候选1.2.7未部署；本说明不代表其他主机已迁移。

### 3.3 文件内容

#### `.env`

```bash
WS_URL=ws://<cyf-api-host>:10018/ws/agent/channel
OPENCLAW_API_KEY=cdx_xxxxxxxx
DEFAULT_CODEX_PROFILE=wuyong
CODEX_PROFILES_FILE=/home/isp/apps/codex-ws-agent/codex-profiles.conf
HEARTBEAT_MS=30000
RECONNECT_MAX_MS=1800000
CODEX_PROFILE_RELOAD_MS=5000
```

#### `codex-profiles.conf`

```ini
[default]
codexBin=/usr/local/bin/codex
codexWorkdir=/home/isp
codexSandbox=workspace-write
codexApproval=never
codexSessionMode=resume
codexTimeoutMs=900000
# 可选补充标签；已安装 SKILL.md 会自动发现
abilities=backend,review
skills=cyf-quick-iterate

[agent.wuyong]
agentId=wuyong
codexWorkdir=/home/isp/hosts/cyf/workspace/cyf
agentName=吴用
personaName=智多星
codexHome=/home/isp/apps/codex-ws-agent/.codex-wuyong
isDefault=true
enabled=true
```

Set `enabled=false` on an `[agent.*]` section to take that profile out of service. The running `codex-ws-agent` hot reload will close that profile connection and skip registration; changing it back to `enabled=true` reconnects it. `active=false` and `status=disabled|inactive|unavailable` are also treated as disabled.

#### `.codex/config.toml`

```toml
openai_base_url = "https://codex.chcbz.net/v1"
model = "gpt-5.4"
model_provider = "gpt"
preferred_auth_method = "apikey"

[model_providers."gpt"]
name = "GPT"
base_url = "https://codex.chcbz.net/v1"
wire_api = "responses"
requires_openai_auth = true

[projects."/home/isp/hosts/cyf/workspace/cyf"]
trust_level = "trusted"

[projects."/home/isp"]
trust_level = "trusted"
```

### 3.4 启动脚本 `codex_ws_agent_start.sh`

```bash
#!/usr/bin/env bash
# Usage: ./codex_ws_agent_start.sh {start|stop|restart|status}
# 用 tmux 或 nohup+setsid 持久化运行
```

---

## 四、新服务器部署

### 前置条件

- Node.js >= 20
- `codex` CLI 已安装并登录
- 防火墙放通到 cyf-api 10018 端口

### 步骤

```bash
# 1. 创建目录
mkdir -p /path/to/codex-ws-agent/logs
mkdir -p /path/to/codex-ws-agent/.codex-my-agent

# 2. 放入 4 个文件：agent-client.mjs, package.json, .env, codex-profiles.conf

# 3. 编辑 .env —— 修改 WS_URL 和 OPENCLAW_API_KEY

# 4. 编辑 codex-profiles.conf —— 修改 agentId, codexWorkdir, codexHome

# 5. 配置 Codex
codex login
# 或用已有 auth.json + config.toml

# 6. 启动
node agent-client.mjs
# 或用启动脚本
bash codex_ws_agent_start.sh start

# 7. 验证
tail -f logs/startlog_*.log
# 预期: websocket connected | profile=xxx | agentId=xxx
```

### 排查

| 现象 | 原因 |
|------|------|
| `non-101 status code` | API Key 无效或后端未启 |
| `reconnect window exceeded` | 30分钟未连上，检查网络/启动脚本 |
| 连接后秒断 | 后端异常（查后端 ERROR 日志） |
| 传令无回复 | 确认 `codex exec "echo test"` 可执行 |

---

## 五、聚义厅招贤馆绑定

招贤馆调用：

```http
POST /agent/personas/{personaCode}/bind
```

请求体 `mode` 支持：

| mode | 说明 |
|------|------|
| `server` | 在服务器 `/home/isp/apps/codex-ws-agent/codex-profiles.conf` 追加 profile，并创建工作目录 `/home/isp/hosts/cyf/agent-clients/{agent}`。运行中的 `codex-ws-agent` 会自动检测配置变化并接入新 Agent。 |
| `local` | 完成人物绑定，并返回 `.env`、`codex-profiles.conf` 示例和启动命令，供用户在自己电脑运行 `codex-ws-agent`。 |

服务器代管观察命令：

```bash
tail -f /home/isp/apps/codex-ws-agent/logs/startlog_*.log
```

本机接入时，用户需要准备 Node.js 20+、可用的 `codex` CLI、`agent-client.mjs`、`package.json`，并向管理员获取 `OPENCLAW_API_KEY`。

## 2026-10-06：typed INSPECT 网络隔离自检（T05–T09 Owner）

- slirp sandbox 必须在独立、**递归 private** 的 mount namespace 内启动：固定 `/usr/bin/unshare --mount --propagation private -- /usr/bin/slirp4netns ...`，不提供直接 slirp 兜底。不关闭 sandbox/seccomp、精确进程归属、nft default-drop 或固定 provider CONNECT 代理。
- 使用已经核对 Owner、可执行文件、startticks 和 namespace 的 `/proc/<holderPid>/ns/net` 精确路径及 `--netns-type=path`。本机 SUID bwrap 在服务 uid0/gid1000 环境中，slirp PID 模式的隐式 userns entry 实测导致后续 netns entry EPERM；相同隔离 fixture 的精确 netns 路径模式已成功 READY。
- 外部命令的成功回读和失败 stderr 等待 `close`（stdio 排空），不能在 `exit` 时直接结算。只记录本地 nft/slirp 诊断，不记录 provider 凭据或任意 provider 错误内容。
- 网络契约改变必须重做真实 carrier、绑定当前 profile/policy/native attestation；无模型测量成功不等于 carrier 或真实业务通过。新增验证同时核对 PID1 mountinfo 和保护进程 cgroup/startticks 未变，不在共享服务上重放危险旧路径。
- typed INSPECT 声明与 CHAT transport capability 是独立契约。后端派发应采用独立 typed registry 的唯一当前、精确 tenant/owner/client/Agent/session READY 项，并匹配 admission manifest profile；不能放宽旧 capability 验证或伪报 READY。2026-10-06 的后端派发修复仍须绑定 Flow 与上线验证，不能把候选文档当作上线结果。

## 统一接口迁移：历史示例执行边界（2026-10-15）

本文上述`node agent-client.mjs`独立部署、query api_key及type顶层帧教程是历史协议资料，不是当前统一Runtime安装指南。`docs/agent-client.mjs`仍是可执行文件，不能仅因为位于docs就当作非消费者。统一迁移详设要求在发布候选中移出可执行部署入口并明确拒绝旧启动，不把它升级成第二个Runtime或恢复旧认证/任务lane；当前仅明确文档边界，尚未改脚本或停止任何进程。现行统一Runtime身份与隔离配置保留，遵循项目入口和统一接口规范，不复制本历史示例到生产。
