# 验收与发布证据

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：业务会话与原生thread的适用映射。**

### 必须验证的业务结果
同会话两轮原文记忆、不同会话/身份无串线、重启后映射恢复、材料输入不丢历史、20条历史分页。

### 不回归边界
同一业务会话可涉及多个Agent的原生thread，不作全局严格1:1承诺；材料/工具合同变化不机械新建thread，必要更换必须说明具体隔离/能力原因。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## 准确候选

| 模块 | commit / tree | 验证 | 独立审查 |
| --- | --- | --- | --- |
| Agent | 9888214d00e575deda12638c58af583327e40e93 / 2bb084bfa103364b67164ca2cf7f8bcb3dbf9c5b | config-runtime 33 PASS，语法/diff-check PASS | Leibniz ACCEPT，P0/P1/P2=0 |
| Web | 24e5e5d0bdf0b28eaee3f37f5f32c759a98283d7 / a33f7d5daf87b42a926505875916beeecc4dff39 | 会话/历史33 PASS，指定语音3 PASS，生产构建rc0且树干净 | Godel ACCEPT，P0/P1/P2=0 |

Agent 模块命令：`node --test test/config-runtime.test.mjs`；依赖使用当时准确 release 的 ws/yauzl，只读临时链接已移除。

Web 工作目录：`/home/isp/wsps/cyf/.worktrees/jy-session-web-20260910`。

```bash
node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec --timeout 15000 tests/juyiting-hall-conversation.test.js
node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter spec --timeout 15000 tests/juyiting-voice-conversation.test.js --grep 'keeps text chat usable with flag off and renders correct controls with flag on|keeps cancellation reachable and rejects panel/context changes while capture is locked|keeps mounted Hall locked while sending and preserves turn B when timed-out turn A settles late'
NODE_OPTIONS=--max-old-space-size=512 npm run build
```

覆盖新业务ID+历史Home仍new、准确resume/缺失失败/跨Agent隔离、thread_id捕获、command不覆盖聊天映射、持久化rename前后失败边界；前端范围隔离、历史分页（兼容失真的total）、失败重试原ID、等待回复禁止重发、新话头取消旧请求加载状态。

## Web 发布

已正常非force推送 origin/develop24e5e5d。dist/stage/live SHA-256均为 `cf37e63bebfd348bcbaf24e8f5aa457bfd85b853cc0addd4bf34431d67dce3c2`。
`/`、`/juyiting` 与 `/static/index-DiYwnxni.js` 公共检查通过，入口JS与本地产物字节一致。
发布记录：`/home/isp/hosts/cyf/web/bak/release-records/kit_release_20260910_014009_24e5e5d.json`。

## Agent 发布

等待 Owner 的准确 release/进程/注册及正常 master 推送回执；源码接受不冒充已上线。

## 证据与保留边界

- 本任务证据：`/var/tmp/cyf-jy-session-20260910/`；源接受回执分别为 agent-source-acceptance.json 和 web-source-acceptance.json；构建完整日志 web-build-r2.log。
- 没有真实付费模型对话或登录态端到端验收，不据公共静态检查声称这两项已验证。
- 旧4个映射对应2个session的混合历史未改写/拆分，Home/业务历史不自动清理。
- 沿用既有认证接口与当前用户默认列表过滤；未改后端权限模型、Long序列化或SSE重放机制，既存后端边界不在本次修复声明内。
- 主Web checkout原有未提交修改保持不动；发布来自独立干净候选。根仓原有分叉不在本任务中合并/推送，准确候选以本文件和integration.yaml为准。
