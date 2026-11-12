# 聚义厅健康监控

本目录从 2026-09-30 已安装的 root-owned 监控接管源文件维护；不替换 API 制品。

- 主机入口：`/usr/local/libexec/cyf-juyiting-health.py`；每分钟由 `/etc/cron.d/cyf-juyiting-health` 执行。
- 状态：`/home/isp/state/cyf-juyiting-health/state.json`。`--status` 只读；`--check-once` **可能启动/重启 API 并发邮件**，只用于授权恢复。
- 恢复 carrier 通过独立 `system.slice` scope 调用规范生命周期入口，保留自身 cgroup、进程身份、发布锁与制品校验。不要从交互会话反复裸启动 API：本次交互 `user.slice` 的 swappiness=0，已有恢复后再次 OOM 的证据。
- carrier 的 `--check` 只读验证规范入口权限与固定 SHA，不创建 scope、不启动 Java。主监控在预留恢复次数前执行它；pin 失配不再消耗恢复次数并伪装成“终态未知”。
- 升级规范入口时先自检 exact source，再更新 carrier 的 `CANONICAL_SHA256`；更新主监控的 `RECOVERY_CARRIER_SHA256`。**不删除哈希/权限验证，不自动信任磁盘新值。**
- 安装前备份两份 root-owned 文件，固定候选 SHA；等待 `monitor.lock`，锁内原子替换 carrier 和主监控、readback，部分失败只恢复本次写入。禁止覆盖他人的变更/状态。
- `SMTPAuthenticationError` 只记录安全的 `smtp_authentication_failed_<code>`；不记录邮件地址、口令或服务商报文，不把 SMTP 接受视作收件箱送达。
- SMTP 配置位于 `/root/.config/cyf-task-monitor/email.env`（root:root 0600），不进入仓库。认证被拒后需要授权操作人更新有效凭据，不盲目重复发送测试邮件。

轻量离线回归（不访问真实邮件、不操作生产进程）：

```bash
/usr/bin/python3 -B -m unittest discover -s /home/isp/wsps/cyf/ops/maintenance/tests -p test_juyiting_health_recovery.py -v
```

`--check-once` 返回的 `healthy` 可能仍描述恢复前快照：恢复成功必须核对 `native_exit_0`、`success_health_up` 和后续全健康探测，不能仅看 carrier scope 的 systemd `Succeeded`。

事故及安装证据：`/home/isp/wsps/cyf/docs/implementation/API_502_HEALTH_RECOVERY_20260930.md`。
