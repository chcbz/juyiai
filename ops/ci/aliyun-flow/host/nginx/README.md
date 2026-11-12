# Runtime 原生 HTTP 网关

2026-11-12 核对已部署 API `c7c0f2d78d4de51d4caed81cfe2caa1a6835b565` 的
`AgentRuntimeAuthenticationFilter.allowed` 及 `PlatformKnowledgeUsageController` 维护认证；本目录是网关配置源码，不是前后端应用发布。

- 将两个 `.conf` 固定摘要后安装到 `/home/isp/apps/nginx/conf/snippets/`。
- 仅在 `/home/isp/apps/nginx/conf/vhost/api.chaoyoufan.cn.conf` 的 server 块 include
  `/home/isp/apps/nginx/conf/snippets/cyf-runtime-native-locations.conf`。
- 保留既有 `/agent`、`/ws` 及默认拒绝路由；不代理整个 `/internal`。
- 当前17组精确路由覆盖议事工具目录/调用、材料输入、对话和执行用量、原生执行恢复/effects、技能结果/岗位、公共知识成本和归档维护；退役controlled-image-v3/provider-start等旧路径不恢复。配置源码/静态测试不等于已安装，实际状态见调度handoff。
- 只转发允许路径和方法；Authorization、五个 X-Agent 证明头、Origin 与重复头不改写。
  Runtime/session/channel/owner/task 的权限仍由后端核对。浏览器 CORS 不开放此 native 通道。
- 沿用现有 100m 主配置上传限制及代理超时；本变更不新增包大小/资源门禁。
- 生产变更在现有 coordinator→API release 锁内备份、核对前值、安装，`nginx -t` 后 reload；
  失败只恢复本次精确文件前值，不重启后端、Runtime或强杀旧worker。
- 定向静态测试：`python3 -B -m unittest discover -s ops/ci/aliyun-flow/tests -p test_runtime_native_nginx.py -v`。
  静态测试不代替实际公网鉴权与业务验收。后端白名单变化必须同步核对本配置。
- 已实测李逵公网轮询200、无凭据/伪凭据/普通用户JWT拒绝；通用文件交付尚未通过。
  具体范围与证据见 `docs/implementation/handoffs/LIKUI-SELFHOST-20261011.md`，不能将此当作全能力开通。

## 浏览器 ES module MIME（2026-10-22 核验）

Web 1.16.43（669bdc9d6439d1bd7eb71df5ed401202a648f419 / Flow4403172 Run295）
的 PDF.js worker 为 `/static/pdf.worker.min-Dkey6ZUl.mjs`。主配置 include 的
`/home/isp/apps/nginx/conf/mime.types` 必须把 `js mjs` 一并映射为
`application/javascript`。否则静态文件虽返回200，浏览器仍拒绝加载模块。
本目录 `javascript-module-mime.patch` 仅记录现行 mime.types 的一行增量，不是整文件替换模板；
未来升级 Nginx 时检查上游是否已含 mjs，禁止盲目重复应用或覆盖其他类型配置。

本次在 coordinator→API release 原锁内保存前值，配置测试通过后 graceful reload，
无 API/Runtime 重启、无应用重构建、未修改 default_type 或 PDF 内容类型。
公网 worker 响应与浏览器原事项514两页实际渲染均通过。PDF仍由浏览器预览；
Agent正文提取是独立技能，不由Java后端解析。
历史浏览器缓存是否保留旧 Content-Type 未逐一验证；遇到旧缓存先强制刷新核对响应，
不能仅以服务端新响应宣称所有既有客户端恢复。
证据见 `specs/juyiting-skill-execution/evidence/pdf-skill-release-20261022/browser-retest/`。
