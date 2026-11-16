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

## 接续

待完成worker Gradle/依赖缓存准备，固定工具候选，执行API plan-only与任务状态检查，再在600秒单次构建预算内执行Web/API原必要基线及fresh打包，回传校验后受控安装。任何异常保留失败及原因，不覆写历史、不自动降级本机构建；精确完整制品可复用于安装重试。
