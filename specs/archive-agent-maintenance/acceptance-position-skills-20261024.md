# 职位技能修订验收状态（2026-10-24）

**结论：实现候选已形成，最终定向诊断已通过，候选已推送；未整体验收、未部署。** 本文件仅记录四小时计划 A01–A12；不覆盖旧 D2 84 项状态。

## 必选矩阵

| ID | 已取得的证据 | 尚缺 / 门槛 |
|---|---|---|
| A01 | 两种枚举、多对多、可配置岗位容量、默认项变更的领域测试；真实管理 HTTP 配置 | 定向诊断通过，不等同完整产品验收 |
| A02 | 真实 native HTTP 下载1.1.1包、durable installer 写入独立 HOME、当前会话回执后才就绪 | 完整已安装 Runtime 的实际 WebSocket 注册及产品操作 |
| A03 | 真实卸任后删除 POSITION 文件；GENERAL 文件、Descriptor 与 entitlement 合法保留 | 完整 Runtime 运行验收 |
| A04 | 同 Agent 两职位共享同一技能，撤一个不删、撤最后一个才删；领域重复撤任幂等 | 产品交互验收 |
| A05 | 领域测试覆盖在职补装、移除默认项和显式 GENERAL 卸载后的语义 | 完整 Runtime 配置变更闭环 |
| A06 | MySQL 隔离、native 认证/持久 session 回归；签名 OAuth 管理接口拒绝普通用户、旧 auth_epoch、跨 owner；JWT 不可冒充 native | 浏览器登录与完整账号流程 |
| A07 | 真实 DB 锁串行发布/撤任；native 撤任后轮询跳过作业，提交拒绝；已提交事实可恢复 | 完整 Runtime 离线/重连端到端 |
| A08 | 两种结构的仓外 UUID 文本经实际 parser、native HTTP 入库；书架/目录/正文读回；受测 API/Client 源码前后未变 | 无完整《三国演义》底本；完整产品浏览器读回未做 |
| A09 | DRAFT 不上架，AUTO 需要许可；人工发布同 importer/CAS；冲突变 FAILED 且可重交办，不阻塞其他书籍 | 产品端到端 |
| A10 | 新 edition、历史目录/正文读取、已发布正文不可篡改；真实 DB 书签/手札跨 owner 与 edition 隔离，旧版可更新、下架后拒绝更新；Web reader 回归 | 完整产品浏览器端到端 |
| A11 | Web 持久原键、刷新/重挂载、身份切换、原输入重试；Runtime 丢安装回执恢复；DB 同键并发只产生一单 | 真实浏览器网络丢包/刷新及完整 Runtime 重启恢复 |
| A12 | 精确源码/摘要、编译、分层、定向回归及已做的组件视觉检查 | **正式 Flow/生产 build 未跑，独立只读复核未做；不通过总门槛** |

## 证据边界

- `verification-20261024/source-inputs.json` 固定本轮候选；Root gitlinks 与 integration.yaml 对齐，不替换旧 D2 历史记录。
- `verification-20261024/` 保存脱敏测试摘要、精确来源、Flow guard 只读回执和真实组件视觉截图。原始诊断日志保留在本任务隔离测试目录，不复制任何测试凭据或 native session。
- native fixture 使用生产 DAO、身份/账户校验、session 服务、真实 HTTP 和 Node RuntimeV1Client/安装器/解析器，但通过显式 `auth.bind` 建立通道存活条件；**不是真实 WebSocket 注册**。
- 组件截图来自真正的 ArchiveMaintenance.vue，但使用明确标注的只读模拟接口；不是后端 E2E，也没有进行真实林冲任命。
- Flow5260799/4403172 的现行 branch guard 不允许本特性分支。未修改 guard、未为了CI合入 develop、未调用本机生产打包代替。
- 计划保留独立只读复核，同时不派子 Agent；本轮只有 Owner 自查，未将其冒充独立复核。

## Owner 自查与已修复问题

- 固定来源、版本、包摘要、任职修订与真实身份；权限由后端判定，提示词/文件不提供权限。
- 解析失败、发布 CAS 冲突都有持久终态和原来源重交办；丢响应保留原键，明确首次业务拒绝可改正输入。
- 撤权后的轮询不再污染外层 native 事务为 rollback-only；新安装 generation 不接受旧回执。
- 1.1.0 包元数据真实安装失败，保留原字节；使用新1.1.1包修复，未覆盖旧ZIP。
- 新作业表与历史 D2 同名表隔离，旧数据不自动转换；没有启动 DDL、自动批准或虚构商城订单。

## 交付后仍需

1. 决定现有 Flow 的特性分支验证入口或受审集成策略；跑正式 API/Web 测试与 production build，不部署。
2. 在获准隔离环境执行完整 Runtime WebSocket 注册、浏览器 OAuth→任命→维护→阅读→撤任和恢复验收。
3. 完成计划要求的独立只读复核，关闭阻断项后再判断 A01–A12 整体验收；生产迁移、内容上架与部署另行授权。

## 最终固定候选诊断（不代替正式 Flow）

| 层次 | 结果 | 固定证据 |
|---|---|---|
| API | 113 项通过，0失败/错误/跳过；编译与 validateLayering 通过 | verification-20261024/api-final-tests.json |
| Web | 100 项通过；8个受影响文件无新增 lint 诊断 | verification-20261024/web-final-tests.json |
| Runtime | 安装/native/解析155项 + host6项通过，0失败/跳过 | verification-20261024/client-final-tests.json |
| 源码一致性 | API工作区干净；Client测试前后摘要相同，340个输入文件与精确提交逐字节匹配 | verification-20261024/client-archive-source-proof.json |

Web 并非全项目 lint 通过：JuyiHall 保留冻结 develop 的141 errors/108 warnings，reader测试保留1个既有quote error；未新增问题，不将基线债务抹成通过。测试未修改API/Client源码；新书样本在源码仓外生成。所有远端组件候选完整SHA已读回核对。

**四小时计划交付结论：源码候选和定向诊断完成；必选总体目标未完成。** A12正式Flow/production build、独立复核及完整Runtime/浏览器闭环仍缺，不能以本轮测试总数宣布验收。测试用临时MySQL与本地预览已按PID/命令归属停止，保留日志和数据。
