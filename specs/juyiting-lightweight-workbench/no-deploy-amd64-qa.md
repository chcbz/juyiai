# 候选提交无部署 amd64 全量验证移交单（待授权执行）

2026-09-23 编写，2026-09-24 更新。本文件是**操作前检查单**，不是运行报告或通过证明。图标修订后目标提交仅限 `cyf-web-kit` 的 `7dd607d69373794897e28b3267943b66a614c73f`（远端 `codex/juyiting-lightweight-workbench` 已核对）；不得把当前 `develop`、旧 Flow Run 147 或本机 Chromium 142 的结果归给该提交。API 源码未改，root 特性分支已为服务器合并预先 pin 该 Web gitlink；验收状态仍未完成，详见 `acceptance.md`。

## 环境与权限

- [ ] 取得一次**明确授权**的隔离 Linux **x86-64 Alinux3/root** 测试 worker；只运行测试/构建/扫描，不部署、不推送 `develop`/`master`、不重试生产作业。当前前端 Flow `4403172` 的源码触发过滤器仅接收 `develop` 和一条历史特例分支，不接收本分支；其构建脚本还校验 `develop` 身份，**不能**假称把候选分支手动塞给现有发布流水线就完成无部署测试。
- [ ] 确认 worker 可读取独立仓库、固定 Node 20.20.2 / Chrome 133.0.6943.141 / WebP 1.2 的已签名依赖；完整哈希与系统依赖在 `web/scripts/ci/prepare-runtime.mjs`，不换浏览器、不禁用签名/哈希，不放宽 E14 p95/p99 或测试超时。执行用户需满足项目 CI 的 root、dnf/yum 和 `/usr/local/bin/chromium-headless-smoke` 条件；不是通用 Debian 安装说明。
- [ ] 不含账号口令、session/token 的新工作目录及私有日志位置；测试结束核对工作区，隔离产物，不把临时密钥/下载签名写入版本库。旧性能报告和 mochawesome 报告由 `ci-test.mjs` 在新运行前隔离，不能重复用旧报告。

## 仅在上述环境获授权后执行

```bash
# 在隔离的 Alinux3 amd64 worker 上；不要在生产服务器部署目录执行。
git clone --single-branch --branch codex/juyiting-lightweight-workbench https://github.com/chcbz/juyiai-web.git cyf-web-candidate
cd cyf-web-candidate
test "$(git rev-parse HEAD)" = 7dd607d69373794897e28b3267943b66a614c73f
npm ci
CI=1 npm test            # 原完整 Mocha、固定浏览器、E14 新报告/性能门禁
npm run build             # 生产打包；不得把构建成功称为服务端/线上验收
```

`CI=1` 是源码 `scripts/ci-test.mjs` 所支持的独立 worker 启动方式；需分别保存 shell 退出码，不能因为后续 `npm run build` 通过就忽略 `npm test` 失败。若组织正式门禁还要求 `JavaScript code scan`，必须另取得**同一 SHA** 的扫描结果；旧 Run 147 两项 FAIL 且日志 API 内容为空，不能当成本候选扫描结果。

## 应返还的可核验证据

1. `uname -m`、系统/Node/npm 信息，worker 标识和时间；实际 checkout 的**完整** Web SHA 与候选分支名。
2. `CI=1 npm test` **完整退出码**、固定浏览器版本与真实可执行文件 SHA、E14 此次生成报告里的五项 gate、10s/60s 采样及 p95≤2ms、p99≤4ms、完整 Mocha 通过/失败/待决统计、`mochawesome-report/mochawesome.{json,html}`。控制台 `CYF_E14_REPORT_BASE64=` 只来自**本次**运行，不能拼上其他作业日志；压缩/截断的日志不得宣称完整。
3. 单独标明 E9A/E9B、E1 基线重定向、两条 TMX（编辑 CLI、快照/预览）的结果：本机 aarch64 曾发生缺固定浏览器及 60/20 秒超时，需确认此受控环境结果；失败须保留原样并定位，不跳过用例。

   本机同 SHA 的 TMX 编辑 CLI 定时补测为 30.124s + 29.487s（两个子进程均 exit 0），再加测试开销超过其 60s 限额，说明本机超时**可由性能解释**，却不证明锁定 worker 会通过；快照/预览的 20s 用例内有 10 次 CLI 调用；本机前 3 次独立重放各约 2.16s、返回预期状态，说明同样存在时间门槛风险，但未验证固定 worker 的结果。详细来源见 `evidence/local-full-recheck.md`，不得据此提高超时/跳过测试。
4. `npm run build` 退出码、生成资源清单/摘要；安全扫描同 SHA 的作业与报告（若为验收门禁），不得用历史成功报告顶替。
5. root 特性分支已为服务器合并预先 pin Web gitlink（不代表验收）；上述门禁与 `real-service-qa.md` 的授权账号业务流程**均通过**后，再评估将 `integration.yaml` 更新为 `accepted`、用户最终确认及发布记录。在此之前维持 `implementing`，不写“已上线”。

若没有合规 worker/授权，把实际拒绝原因记在 `acceptance.md`，不要在 aarch64 本机用系统浏览器冒充固定 Chrome，也不要向现有 `develop` 发布流水线推送候选。
