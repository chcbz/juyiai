# 案卷阁阅读 MVP acceptance

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：数据驱动的典籍阅读与个人进度。**

### 必须验证的业务结果
不同书籍/可空引首/多章节、活动版本一致性、个人数据隔离、内容读取与启动无书籍导入、阅读器受影响设备布局。

### 不回归边界
不写死水浒传/120回/必需引首；书籍内容不进入启动classpath，不在启动导入/全文对账。PPT取消预览不影响典籍正文阅读。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


<!-- SDD delivery reconciliation 2026-09-06 -->
## Contract/content

- [x] 内容来源、许可归属、上游 commit、原始 SHA-256 和 manifest SHA-256 可审计。
- [x] 引首11段与120回正文共3677个 reader paragraphs 均有稳定ID、API路径、byte length/hash；每回重复的两行 Wikisource 许可元数据不进入正文。
- [x] ACTIVE 内容恰有 120 个连续章回；章节/段落 ID、manifest 与 versioned weak ETag 可按 golden vectors 确定性重建，并按 HTTP weak comparison 处理 `If-None-Match`。
- [x] 发布后正文不可原地修改；内容变化会产生新 `editionId`。

## Reading and personal data

- [ ] 认证用户可浏览目录、完整章回、继续阅读、上一回/下一回。
- [ ] 阅读进度跨会话恢复；两个标签页并发不会静默覆盖。
- [ ] 用户可创建/删除书签和私人手札；冲突时保留本地草稿。
- [ ] 两个 OAuth 身份和两个 client 的进度、书签、手札完全隔离；越权统一 404。
- [ ] 缺失认证 scope 时零写入并 fail closed。

## Ask Agent

- [ ] 中文多字节、跨段选文由服务端按 byte offset/hash 精确重建。
- [ ] 默认 responder 明确为“案卷书吏”，不得冒充吴用或使用当前 selectedAgent。
- [ ] 问题创建重放不重复调度；版本/sequence全程使用 canonical decimal string，越过 `Long.MAX_VALUE` fail closed。
- [ ] SSE live-before-replay、watermark/buffer exact-next、gap/cursor-ahead/truncation/overflow `resync_required`、snapshot替换及服务端/客户端资源清理通过。
- [ ] provider 故障不影响阅读、进度、书签和手札。

## Compatibility/release

- [ ] `/chat/library/search` 与旧“引入传令”行为保持兼容。
- [ ] Elasticsearch 停止时典籍阅读和私人数据仍可用。
- [ ] API targeted/full、隔离 MySQL、Web tests/build 和真实浏览器 smoke 有可复用证据。
- [ ] feature flag 默认关闭；部署制品 SHA-pinned，备份/恢复和回滚步骤验证通过。

## Verification evidence

- API revision:
- Web revision:
- Content artifact/manifest:
- Commands/tests:
- Result: pending
