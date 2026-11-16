# Web/API 构建迁移到203.32.84.239

2026-11-16，Owner `build_migration_owner` / developer，任务 `REMOTE-BUILD-MIGRATION-20261116`。

## 范围与授权

用户授权“开始迁移构建任务并进行一次构建和发布”。迁移Web/API测试、构建、打包到已安装工具的服务器，生产机仍用原LOCAL受控安装事务。无功能代码变更，以当前已部署源码重建验证新链路。Runtime存在其他活动任务和未提交变更，本次不发布；不变更生产数据/模型/身份、不开付费Flow。

- 根控制器开发基线：`2b2abf4ec02ae050ad9f1fdc8dc9f05ab049a87f`，工具候选最终commit在执行证据中固定。
- API：`d6f03755ac524b7604495ed162943a5b30ec580f` / tree `2a24067cf6d9161ee1b9a347132928392d54b3e8`，版本 `1.1.56-SNAPSHOT`，工作区干净，等于当前生产源码。2026-11-16约09:48只读远端查询develop为 `377132f786c6a38b1cb9d2cb90bda7dc3a96ff0b`；不把本地候选宣称为远端最新，不自动取旧远端发布。
- Web：`2ee2349a1f727c1c712dd54b36e268075977300e` / tree `6d0474c094b073ecf699d11420e5b425b83b0733`，版本 `1.16.150`，干净，等于生产及当时远端develop。
- 生产API发布前JAR SHA-256：`f6c8fa110f2bc23acf1b8d39d4d6e59de8455a28a92f0d3f2ab7627268f8e840`；生产Web原buildId `runtime-lease-web-k2-toolbar-01-20261115`。执行前重新核对，不以此段替代前代摘要并发保护。

## 责任与最小联动

本次责任在既有编排/传输边界：local_release委托原Web/API builder，SSH传输不复制API业务权限/状态机。无接口、持久化或执行合同变化，不要求Web/API/Runtime业务代码联动。统一接口规范路径 `/home/isp/wsps/cyf/api/docs/interface-standard.md`，固定版本为上述API commit；RB-1职责与根AGENTS显式随controller快照携带。

## 实施与验证（进行中）

- 现有 `local_release.py` 添加显式SSH worker参数，远端systemd控制构建deadline，原生产安装保持独立；`remote_build.py`仅传输/源固定，不另造发布runner。
- 固定host key、浅Git快照排除脏字节、禁止覆盖接收目录、安全归档解包及deadline职责的隔离工具测试通过；原构建、安全/分层/fresh JAR与时限测试保留。完整日志在 `/home/isp/state/cyf-remote-build-migration-20261116/transport-tests.log`。
- 初次工具/缓存准备、真实构建批次、测试XML、制品SHA、安装及验收分别保留于同任务证据和构建批次目录。准备成功不代表应用构建通过。
- 未执行全局119项、真实Provider收费调用或故障注入；发布后验收限定原安装器全资源核对、API健康/签名/认证边界，以及明确记录的只读冒烟。

## 执行批次与故障归因

- controller 固定 `19c59363bc5ca211a02ebc18acada1a109db164d` / tree `eef01b0ddc03e2d886b6be4fbe53d6bb404b686d`；45项工具定向测试通过，日志 `/home/isp/state/cyf-remote-build-migration-20261116/final-transport-tests.log`。
- worker已安装 Node24.22.1/npm11.19.1、Dragonwell21.0.11、Gradle9.3.1，均在`/home/isp/apps`；Gradle迁移6688项缓存逐hash核验，通过原API plan-only与orchestrator preflight。缓存迁移不是应用验证。
- 首批 `remote-20261116-01`：源码准备197.675秒，单独记录；Web构建阶段414.446秒后Owner受控停止，`FAIL` / exit143，API未开始，生产未安装。Canvas GNU原生tarball从npm官方源持续低速下载，六分多钟仍未完成；预计余下必要构建/打包超600秒，未续时。不是单元测试失败，也不重标为成功。
- 首批证据 `/home/isp/state/cyf-remote-build-migration-20261116/release-01/release.json`，网络/停止现场和npm原日志在同根 `failure-01/`。修复选择迁入本机已有、逐blob匹配锁文件SRI的npm内容缓存，不改锁文件/依赖版本/测试要求。准备脚本曾因控制机默认Python3.6及残留准备目录失败，原日志另存；控制器正式执行必须用现有 `/root/.local/bin/python3.11`。

- npm缓存迁入554个锁定SRI内容blob，远端553项已有、1项新增（Canvas GNU）；完整锁文件不在本机cache的82项为其它平台等未缓存包，不伪称全部依赖已迁入。新批Web依赖11.568秒、53通过/2pending、构建12.464秒，worker全程41.431秒。
- 第二批 `remote-20261116-02`：Web（含回传）207.789秒通过；API 8.028秒失败，Gradle在测试前报告Groovy DSL不可变workspace缺失 `cp_init`/report输出。根因是迁移快照只归档文件而漏掉有语义的空目录，不是代码/测试失败；总构建215.817秒，生产未安装。已按原缓存目录清单补齐1224个目录并核验9752目录、6688原文件，未清空缓存。证据同根 `release-02/`、`gradle-cache-directories*.{json,log}`。
- 同期观察到回传约5Mbps，API原JAR约241MiB，不能仅靠热缓存承诺600秒。传输适配为SSH固定密钥的rsync块差量：旧程序/包仅作字节basis，接收完整归档SHA/大小必须匹配worker原归档后才解包；不复用测试结果、不改变原包。传输受本阶段剩余预算约束，不给生产进程下传deadline。9项transport及32项local工具测试通过，日志同根 `delta-{transport,local}-tests.log`。

## 接续

核验npm缓存迁移完成后启动独立新批次，Web/API继续共用单次600秒预算，回传后原受控安装。任何异常保留失败及原因，不覆写历史、不自动降级本机构建；精确完整制品可复用于安装重试。
