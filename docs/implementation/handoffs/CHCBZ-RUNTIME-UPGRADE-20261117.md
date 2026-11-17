# chcbz.net Runtime 升级（2026-11-17）

## 范围与固定输入

- Owner：本次对话；用户明确要求升级 `isp@chcbz.net`，不是控制机或 Eva 的重复安装。
- 目标：`chcbz.net` / `173.230.149.118` / 主机 `li159-118`，x86_64，服务用户 `isp`。使用现有私有 SSH 配置，未复制或公开密钥。
- 原 Runtime **1.3.102 / bridge 1.1.71**，源 commit `bbf8db06a36a9fc48d1441d5cce9d639e4d4a80b`；升级到 **1.3.118 / bridge 1.1.80**。
- 固定源码 commit `c184e26bc88aab6e21bb62322117a1a9152c6a41`，tree `3822c091c91ad35d0b521e0f9ef178f36c85fdb0`，没有跟随移动中的 develop。
- 复用指定 SSH worker `203.32.84.239` 已测试代码包 `/home/isp/state/cyf-build/n6r05/package/runtime-code-1.3.118.tgz`，SHA-256 `53c976cffc8ef4a625d67c46d4ed3abb949261ff551562a26fbca876131f448f`；manifest SHA-256 `c72d627e45892651b746603fb3cec1d2f7f9ab0df855e4f145b86ddbf844f674`。
- 原构建 `native6-runtime-20261117-05`：1056 tests / 1045 pass / 11 skip / 0 fail，构建214.527秒、连回传216.643秒。此次只复用制品、准备目标依赖和安装/验收，没有重建或付费 Flow。
- 责任：RB-1 Runtime 安装、隔离、会话及执行适配；没有改动 API/Web 合同或业务权限。统一接口参考 `/home/isp/wsps/cyf/api/docs/interface-standard.md`；本次不修改接口。

## 安装与真实失败

使用原目标安装事务 `/home/isp/state/cyf-runtime-upgrades/likui-20261112-runtime13102/switch.py` 的受控适配：原 `/run/lock/cyf-agent-runtime-v1-release.lock`、前代 CAS、完整清单/模式核对、固定实体 app、停止后状态归档校验、精确 writer 归属和程序 rename 保留。没有绕锁、重建身份、重领租约或重放旧任务。

1. 目标准备成功：完整旧清单匹配；portable 字节/模式匹配；Node、node_modules、Python、浏览器、沙箱闭包保留目标自身版本并检查依赖输入；候选 validate 通过。stage 18.301秒。
2. 安装预检01：预期 writer 数错误（2，实际为 host、静态李逵、managed host 共3，均属于旧PID389574）。在停止/备份/迁移/程序写入之前失败，核实准确集合后修正，不伪标成功。
3. 安装02：停止后备份成功，但 shipped auth migration 以服务身份无法遍历原 root-only 程序备份父目录，创建 auth backup 时 EACCES。未改认证或程序；恢复旧程序运行（PID1396080）。日志、失败回执与首份归档均保留。
4. 安装03：不放宽原程序备份 ACL；改用任务私有目录生成 auth backup 并由 root 复制到原备份事务。重新备份当前停止态，迁移3文件（hosting 配置序列化、静态 Codex config、公开基线中的 config），保留静态 auth.json、manifest/profile、host 配置。完整闭包校验后切换并启动成功，安装22.91秒（不是构建计时）。

成功安装的备份：`/home/isp/baks/cyf-agent-runtime-v1/20261117-chcbz-runtime13118-attempt03/`；`program/` 保留旧程序/依赖。`private-state.tgz` 在停止状态下生成并 tar compare，SHA-256 `3697181811f72157085fc393c6a8d6ee0cc3b84ec84ef30d6b9a538501056ec5`。首次失败备份未覆盖。协议状态接受后只向前修复，不自动降级或重放。

## 验收

- `cyf-agent-runtime-v1@unified.service` enabled / active，PID **1397024**、NRestarts **0**；进程 exe 是固定 app 内 Node。
- 李逵 `jyt-jiafewnnv58ec2379c-likui` connected / registered / ready，实时心跳；原生启动沙箱、provider TLS、文档/浏览器/PDF/skill-script 探测均完成。
- 原发布锁内完整安装清单、portable 字节/模式、状态备份摘要、静态身份/profile/auth 与备份内容匹配；host 配置字节未变；shipped auth migration 再次 plan count0；最终 validate 通过。
- 真实私聊：request `runtime-smoke-cb5cbeb1b54e4f57856e3a31a934c6f2`，conversation `1760458009641`。李逵精确回复 `李逵升级验收正常-07ca1c30`，SSE completed；独立 GET 确认 `RESULT_COMMITTED` / `FINAL_PERSISTED`，最终消息 `2303191` 存在。没有重发 POST。
- 未跑全局119项回归，不把此处冒烟或历史构建升级成全局通过。API/Web未发布、未重启；之前 Eva 任务修复的公网 native6 网关路径此次直接复用。
- 目标磁盘安装后可用约938MiB（99%使用）；未删除他人数据、可复用缓存、历史状态或备份。

## 证据

- 控制机：`/home/isp/state/cyf-chcbz-upgrade-20261117/`，含 Owner/候选、实际安装脚本、历史失败、目标回传摘要、OAuth 私有会话、SSE与独立消息回读。私有证据不提交 Git。
- 目标：`/home/isp/state/cyf-runtime-upgrades/chcbz-20261117-runtime13118/`，含原制品、build-result、stage/install/verification/completion、迁移日志及失败回执。
- 原构建证据：`/home/isp/state/cyf-build/n6r05/build-result.json`。
- 线上安装来源：`/home/isp/apps/cyf-agent-runtime-v1/release-records/current.json`，终态 `VERIFIED_ACTIVE_CHANNEL_AND_CHAT`，不是控制机同路径的记录。

规则、源码构建、安装及业务验收分别取证；本手记不更新共享脏任务台账或改写旧失败。完整状态备份及认证备份均私有保存；不在本文列出任何口令、token 或私钥。
