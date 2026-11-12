# 原生能力协商：四仓源码整合与长期方案实施补充

日期：2026-09-30。**研发源码基线，不是产品验收、生产启用或已发布版本。** 本文补充此前同日交接的状态；不改写冻结合同、旧测试和失败记录，不建立第二套运行台账。

## 1. 分支与精确基线

四仓均为 `codex/juyiting-multimedia-deliberation`，本次重新 fetch 后验证远端 HEAD 与本地一致，且各自远端 fast HEAD 均为祖先。完整快照与证据摘要见 [JSON](integration-native-capability-source-20260930.json)。

| 仓库 | 已推送 commit | tree |
| --- | --- | --- |
| API | `5668c747464f8a25cb779bbfe9004aa8e607c2fa` | `b8b44811cde339fac9e9eaaba17425d8095964f7` |
| Web | `ab317fa99b52c7df51005517e2252c65b2db72b6` | `5950efee3b7643eb9bc1cab0835ad871e3087e04` |
| Client | `1812e5b5d090013338265d16ca34b0b9c257da49` | `430296285683b3597f7401c21e7368c5fd078107` |

SDD 本次同步 API/Web gitlinks 及 Client manifest pin；其提交以包含本文的 Git 历史确定。此前交接的 SHA 表是历史核验点，保留不覆盖。**包含 fast 不表示已吸收最新 develop**；后者独有提交及精确 SHA 见 JSON，后续收敛需按实际差异处理。

## 2. 关闭的源码切片

冻结业务边界仍为 [native 能力合同 v1](native-bounty-capability-contract-v1.md)：

- **API**：成功注册/回执后才激活 native 声明；当前持久身份和绑定有效、连接未替代且在线，才可广告 READY。独立于 fast-v1 能力。Owner 精确任务/目标只读协商返回实际缺口；依赖失效不伪造未声明或成功。
- **Web**：实际 JuyiHall 点将处理接入 native 协商；既有 v2 原键/正文先恢复，不因能力缺失或未知响应回落 legacy。OFFLINE/UNDECLARED 等事实保持原样；身份、task、target、后续观察和卸载均 fence 迟到响应。持久意图不可读/损坏不视作“没有”。明确受限的 legacy 文本路径不冒充生图。
- **Client**：真实图片执行器、HTTP poll、必要配置与 live socket 就绪才声明启用；山寨安顿/自家接应逐实例证明，不因安装 skill 就声称能执行。**不改 fast-v1 EXECUTE=false。**

这不是两个长期产品：平台仍复用会话、持久 request/turn、事件和资产；CHAT 的无预加载边界保持，受控 INSPECT/EXECUTE 是按需独立授权策略。native transport 与旧 wire 适配不等于另建文件系统或会话。

## 3. 实际验证与失败归因

| 精确源码 | 验证 | 结论及范围 |
| --- | --- | --- |
| API `5668c747` | native 六类含实际 Spring bean 构造 20；既有 BF08 60；managed handshake 3 | **83 执行，0失败/错误/跳过**；正常源与依赖图，无冻结源码覆盖。不是整套应用启动或真实浏览器证明 |
| Web `ab317fa` | native/point-and-start/bootstrap/finalization 137；task actions 7；两个 SFC 编译 | **144 定向通过**；含实际页面闭包，仍非 live API 或浏览器 |
| Client `1812e5b` | agent-client 116、config-runtime 34、conversation-native 14、conversation-imagegen 3、native declaration 5 | Owner **172 通过**，精确 tree 证据缓存已核对；不重复执行，未安装或调用 Provider |

API/Client 旧 wire fixture 字节相同，SHA-256 为 `10534e0347fbac81ff5298ad182ee5f8549005c8a6aa73ee874e64ede98a6eb6`。

API 的先前失败全部保留：
1. orchestrator 参数位置导致未启动测试，修正调用结构，不算测试执行。
2. 本任务 Gradle daemon 被内核 OOM 杀死。后续串行、单 worker 配置 JVM heap384MiB/metaspace192MiB，属于实际故障后的 JVM 管理配置，**不是资源准入门槛**，不操作其他任务进程。
3. 两个 Mockito 重设抛异常 stub 的夹具问题，改用 `doThrow` 保留撤权/依赖故障断言。
4. 新增实际 Spring 构造测试暴露 `No default constructor found`，生产代码给预期公开构造器补 `@Autowired`；未绕过默认关闭、身份或费用判断。

API 日志与 XML 摘要位于 `/var/tmp/cyf-mmd-main-api-native-20260930/`；Web 日志位于 `/var/tmp/cyf-mmd-main-web-native-20260930/`。Client 使用唯一证据缓存 `/home/isp/wsps/cyf/docs/implementation/EVIDENCE_CACHE.json` 的 exact-tree 记录；摘要/键见 JSON。不存在的测试文件不计入通过数。以上数量不能替代 34 项产品用例。

## 4. 尚未关闭的业务及下一顺序

当前入口仍真实声明 `inputRefsPolicy=EMPTY_ONLY`、`authorization=UNAVAILABLE`、`paidExecutionAuthorized=false`、`newStart.eligible=false`。**不能靠改布尔值、伪造 costRef 或放宽 fast 协议来让生图“成功”。**

1. 在需求创建前选可选 JPEG/PNG 精确工作空间版本；接普通任务创建的原键恢复、需求 revision 与 task-file 关联事务/对账，再放开受权引用入口。选择器源码单独完成不能关闭实际需求流程。
2. 冻结并实现合法执行费用授权桥，明确来源、用途、目标/操作/输入边界、撤销和 START 校验；不挪用 reward escrow、hosting、skill 或钱包余额作为执行同意。
3. 同会话澄清 continuation、上一稿 asset/revision、EDIT 与派生输入按实际支持广告；继续补充是一条新明确意图，不是未知结果后的自动重跑。
4. 正式保存、精确提交/验收/完成真实联调；文本、图片、音频、文件范围不缩水。
5. 收敛 develop、相关迁移/应用启动、双接应及真实 Provider/浏览器，再按精确 SHA 生产构建和版本发布；发布后验证可预览、可下载的真实字节。

长期方案和施工详设继续以 [融合详设 v2](fusion-detailed-design-v2.md)、[媒体/存储详设](design.md)、[实施计划](fusion-implementation-plan-v2.md) 为权威。执行只更新 `/home/isp/wsps/cyf/docs/implementation/TASKS.yaml#runtime_ledger_json`，Owner自检、不创建独立 Reviewer。

## 5. 授权与发布说明

早期文档中的“仅分支/详设、不部署”对应当时动作范围，保留历史含义。当前持续目标为用户“落实下去吧，然后按版本发布，可以验收的时候通知我”：允许完成实施，达到上线条件后自检合组件 develop，并按最新发布政策进行普通版本发布；**本次并未执行 develop 合入、构建、部署或激活**。

这一授权不涵盖未明确同意的付费 Provider 调用、生产 DML/迁移或外部数据传输；缺少实际授权时如实记录，不伪造端到端通过。云效不可用期间沿用 2026-09-17 本地发布例外，真实发布证据仍须绑定 exact SHA/tree、测试、制品 SHA-256 和健康/版本；不得伪造 Flow Run。

`1.13.45` 已被语音版本占用，后续版本只在发布前核实线上版本及远端 release refs 后分配，不覆盖旧 release。当前 34 项产品验收、生产构建、Provider、浏览器与部署均 **NOT_RUN**；完成源码切片可报告进展，但只有实际达到产品验收条件才通知“可验收”。
