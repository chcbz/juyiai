# CYF 实施计划 Task 逐项审计

> 审计日期：2026-07-18  
> 范围：所有名称或内容属于实施计划的 Markdown。Task/Phase 按可交付能力核验；“提交、推送、手工执行某命令”等过程步骤不单独计算产品功能，但其验证结果会记录在对应 Task。

## Task Checklist

| ID | 计划文档 | Task/Phase | 可交付内容 | 当前证据 | 完整度 | 后续动作 |
| --- | --- | --- | --- | --- | --- | --- |
| PLAN-001 | `docs/juyiting-collaboration-implementation-plan.md` | 阶段一 | 地图/名册隔离、显式点将和协作闭环 | `JuyiHall.vue`、`useHallData.js`、协作契约测试 | ✅ 98% | 保持显式 agentId 不变量 |
| PLAN-002 | `docs/juyiting-collaboration-implementation-plan.md` | 阶段二 | 传令 Agent/任务/scene 上下文增强 | `useHallChatContext.js`、chat context tests | ✅ 96% | 增加用户可见上下文摘要 |
| PLAN-003 | `docs/juyiting-collaboration-implementation-plan.md` | 阶段三 | 页面、数据和会话职责拆分 | `components/juyiting/`、`composables/juyiting/` | ✅ 92% | 继续清理历史组件 |
| PLAN-004 | `docs/juyiting-collaboration-implementation-plan.md` | 阶段四 | 能力筛选、实时更新、推荐评分和 E2E | 部分能力/推荐已有，实时订阅和完整 E2E 不足 | 🟠 58% | 转为正式 backlog |
| PLAN-005 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 1 | TMX parser | `web/src/game/tiledMap.js`、TMX tests | ✅ 97% | 标记 completed |
| PLAN-006 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 2 | 资源加载与 game readiness | `resources.js`、`JuyitingGame.js`、runtime tests | ✅ 96% | 标记 completed |
| PLAN-007 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 3 | 从 Tiled map 构建 melonJS scene | `HallScene.js`、map tests | ✅ 96% | 标记 completed |
| PLAN-008 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 4 | Agent spritesheet 动画与点击 | `HallAgent.js`、scene click tests | ✅ 95% | 标记 completed |
| PLAN-009 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 5 | HallStage Canvas 主层与 DOM fallback | `HallStage.vue`、component behavior tests | ✅ 95% | 说明当前已不再保留完整 DOM 场景 |
| PLAN-010 | `docs/superpowers/plans/2026-06-29-juyiting-melonjs-immersive-stage.md` | Task 6 | 全量验证与部署 | 当前前端 473 tests 通过；本轮未重新部署 | 🟡 85% | 拆分持续验证与历史部署证据 |
| PLAN-011 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | Task 1 | Scene transform helpers | `sceneTransform.js`、transform tests | ✅ 97% | completed |
| PLAN-012 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | Task 2 | Pan/zoom/input 迁入 HallScene | `HallScene.js`、camera/input modules | ✅ 96% | completed |
| PLAN-013 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | Task 3 | 移除 HallStage DOM 场景主体 | `HallStage.vue` 与 DOM absence tests | ✅ 98% | completed |
| PLAN-014 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | Task 4 | 热点、Agent 和失败态 | scene/game/component tests | ✅ 96% | completed |
| PLAN-015 | `web/docs/superpowers/plans/2026-07-01-juyiting-melonjs-scene-migration.md` | Task 5 | Smoke 与部署验证 | 自动测试通过；历史部署需单独保留证据 | 🟡 85% | 增加每次发布记录链接 |
| PLAN-016 | `web/docs/superpowers/plans/2026-07-04-juyiting-modular-layer-assets.md` | Obsolete note | 文档明确废弃，无当前 Task | 现行资源契约在 prompts/assets/tests | ✅ 100% | 无需实现 |
| PLAN-017 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 1 | API contracts 与 core models | AgentScene service/DTO/contract tests | ✅ 97% | 回填 checkbox |
| PLAN-018 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 2 | 租户隔离 persistence schema/mapper | scene state/event/report DAO 与 schema tests | ✅ 96% | 增加迁移版本治理 |
| PLAN-019 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 3 | 单调 state/scene versions | AgentSceneServiceImpl version tests | ✅ 96% | 增加极限容量监控 |
| PLAN-020 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 4 | 可续传 SSE broker | event broker/backlog/live tests | ✅ 94% | 增加代理和压力测试 |
| PLAN-021 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 5 | 幂等 Phase report | phase report entity/service tests | ✅ 95% | 增加死信/补偿 |
| PLAN-022 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 6 | snapshot/SSE/phase endpoints | AgentSceneController tests | ✅ 97% | 回填 checkbox |
| PLAN-023 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 7 | 业务操作写入语义场景状态 | AgentService/scene integration | ✅ 91% | 扩展更多业务事件 |
| PLAN-024 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-backend-scene-state.md` | Task 8 | feature flags、完整验证和 API 文档 | flags + interface spec + tests | ✅ 92% | 明确灰度策略 |
| PLAN-025 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 1 | TypeScript test/lint 工具 | typed game modules and tests | ✅ 95% | 统一命令文档 |
| PLAN-026 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 2 | 焦点 camera transform 与 resize | cameraTransform/resize tests | ✅ 98% | 增加设备 smoke |
| PLAN-027 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 3 | camera controller/presets/clamp/reset | cameraController/viewPresets tests | ✅ 97% | 增加动画性能监控 |
| PLAN-028 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 4 | gesture/hit priority/interaction lock | input modules tests | ✅ 97% | 补 Safari 实机 |
| PLAN-029 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 5 | 集成 HallScene/game facade | JuyitingGame/HallScene facade tests | ✅ 96% | 稳定公开 API |
| PLAN-030 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 6 | 响应式面板/地图锁/超时/resize | HallStage component behavior tests | ✅ 96% | 扩展机型矩阵 |
| PLAN-031 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-camera-input.md` | Task 7 | 最终验证与文档 | 473 tests、guide files | ✅ 94% | 回填 checkbox |
| PLAN-032 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 1 | 可替换 A* graph pathfinding | graphPathfinder.ts tests | ✅ 97% | 保留 PathFinder 接口 |
| PLAN-033 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 2 | home/parking slot 与 command ordering | slotAllocator/commandQueue tests | ✅ 96% | 扩展 queue slots |
| PLAN-034 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 3 | 后端语义状态适配与时间恢复 | backendSceneStateAdapter tests | ✅ 97% | 补跨地图版本恢复 |
| PLAN-035 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 4 | 单 Agent movement engine/phase events | movementEngine tests | ✅ 96% | 推进生产启用 |
| PLAN-036 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 5 | REST snapshot/SSE lifecycle composable | useHallBackendSceneState tests | ✅ 95% | 补混沌测试 |
| PLAN-037 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 6 | 后端状态桥接到 simulation | useHallSceneState tests | ✅ 94% | 增加事件可观测 |
| PLAN-038 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 7 | simulation lifecycle/snapshot rendering | HallStage/JuyiHall integration tests | ✅ 93% | 清理静态巡逻 rollback 技术债 |
| PLAN-039 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 8 | 只读 sceneDebug | aggregator/bridge tests | ✅ 94% | 增加脱敏静态检查 |
| PLAN-040 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 9 | UI smoke/preflight 纵向闭环 | preflight/ui smoke configs | ✅ 90% | 接入 CI 浏览器执行 |
| PLAN-041 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-simulation-integration.md` | Task 10 | 跨仓 Phase 1 验证 | 前端 473 tests + 后端组合 BUILD SUCCESSFUL | ✅ 93% | 记录固定 release artifact |
| PLAN-042 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 1 | movement schema/parser | movementSchema/tmxMovementParser tests | ✅ 98% | CI 必跑 |
| PLAN-043 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 2 | 结构化 scene validator | mapValidation tests | ✅ 98% | 保持确定性错误 |
| PLAN-044 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 3 | 通过 edit ops 编写 hall.tmx movement data | tmxEditOps tests and production TMX | ✅ 97% | 保留原子更新 |
| PLAN-045 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 4 | snapshot 与 clean/debug preview | tmxSnapshot/Preview tests | ✅ 97% | 发布校验和 |
| PLAN-046 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 5 | 宋江风格样本 review | generation/review docs and assets | ✅ 95% | 补评审元数据 |
| PLAN-047 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 6 | sprite manifest/validator | manifest/validation tests | ✅ 98% | 扩展正式 personas |
| PLAN-048 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 7 | 最终宋江 sheet 与降级 | spriteLoader/runtime tests | ✅ 96% | 监控降级率 |
| PLAN-049 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase1-tmx-sprites.md` | Task 8 | TMX validation 集成 mount/preflight | mount/preflight tests | ✅ 97% | CI 阻断 |
| PLAN-050 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 1 | 六个正式 Persona sheets | 当前完整门禁主要验证宋江/manifest，未见六人最终交付 | ❌ 35% | 完成资源、review 和 manifest |
| PLAN-051 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 2 | 集中 multiplayer limits | 未见独立 multiplayer limits 模块 | ❌ 35% | 建立 24 visible/12 moving 配置 |
| PLAN-052 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 3 | spatial collision world | 仅地图障碍校验，无 agent-agent collision world | ❌ 20% | 实现空间索引与碰撞 |
| PLAN-053 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 4 | path/slot reservation | slot owner 存在，路径 reservation table 不完整 | ❌ 38% | 实现时间窗路径预约 |
| PLAN-054 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 5 | behavior queue/staggered departure | 命令队列存在，行为排队/错峰不完整 | ❌ 35% | 增加行为队列 |
| PLAN-055 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 6 | waiting/no-progress/bounded replanning | 有 replanningCount，无完整 no-progress 状态机 | ❌ 38% | 实现等待与有界重规划 |
| PLAN-056 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 7 | 24 visible/12 moving integration | UI 可见 Agent 多于 12 有提示，引擎无规模验收 | 🟠 42% | 增加确定性 24/12 场景 |
| PLAN-057 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 8 | performance harness/debug metrics | 有部分 debug metrics，无完整 harness | ❌ 32% | 建立 FPS/long task harness |
| PLAN-058 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 9 | Android evidence/tuning | 未发现完整设备证据 | ❌ 10% | 记录 Android 基线和调优 |
| PLAN-059 | `web/docs/superpowers/plans/2026-07-11-juyiting-phase2-multiplayer-performance.md` | Task 10 | Phase 2 release gate | 未达到前述门禁 | ❌ 10% | 门禁全部通过后再发布 |
| PLAN-060 | `web/docs/superpowers/plans/2026-07-11-juyiting-unified-rollout-index.md` | Task 1 | 建立 Phase 1 执行检查点 | Phase 1 代码与测试证据完整，计划状态未回填 | ✅ 92% | 补 release checkpoint 记录 |
| PLAN-061 | `web/docs/superpowers/plans/2026-07-11-juyiting-unified-rollout-index.md` | Task 2 | 用可测验收门禁 Phase 2 | Phase 2 性能/多人门禁未通过 | ❌ 25% | 保持阻断状态 |
| PLAN-062 | `api/docs/changes/graalvm-native-support/tasks.md` | 1.1 | 创建 native-image 目录 | common starter 目录存在 | ✅ 100% | 保持 |
| PLAN-063 | `api/docs/changes/graalvm-native-support/tasks.md` | 1.2 | reflect-config | 文件存在，但完整性未用 native build 验证 | 🟡 80% | 自动生成/校验 |
| PLAN-064 | `api/docs/changes/graalvm-native-support/tasks.md` | 1.3 | resource-config | 文件存在 | ✅ 90% | 运行 native resource smoke |
| PLAN-065 | `api/docs/changes/graalvm-native-support/tasks.md` | 1.4 | native-image.properties | 文件存在 | ✅ 90% | 验证参数兼容 |
| PLAN-066 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.1 | 修改 ClassUtil | native mode 存在但仍 Class.forName | 🟠 60% | 完成静态映射 |
| PLAN-067 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.2 | 修改 BaseDaoImpl | fallback 存在，仍动态 wrapper 加载 | 🟠 65% | 注册 wrapper 映射 |
| PLAN-068 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.3 | 修改 PayOrderParse | 当前仍可检索到 Class.forName | 🟠 40% | 改为注入注册表 |
| PLAN-069 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.4 | 修改 SpringContextHolder | 存在 native/availability 处理 | 🟡 70% | 补原生测试 |
| PLAN-070 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.5 | 零反射 ErrCodeHolder | processor 存在，Holder 仍反射加载 Registry | 🟠 65% | 生成静态入口 |
| PLAN-071 | `api/docs/changes/graalvm-native-support/tasks.md` | 2.6 | 错误码注册流 | 多模块注解存在，端到端生成验证不足 | 🟡 70% | 加入编译产物测试 |
| PLAN-072 | `api/docs/changes/graalvm-native-support/tasks.md` | 3.1 | 更新 build.gradle native plugin | 未形成完整 Spring Boot native 构建 | ❌ 30% | 接入插件与任务 |
| PLAN-073 | `api/docs/changes/graalvm-native-support/tasks.md` | 3.2 | Gradle properties | 部分属性存在，缺正式构建配置闭环 | 🟠 50% | 统一 profile |
| PLAN-074 | `api/docs/changes/graalvm-native-support/tasks.md` | 4.1 | JVM mode tests | 现有组合测试 BUILD SUCCESSFUL | 🟡 85% | 保持 |
| PLAN-075 | `api/docs/changes/graalvm-native-support/tasks.md` | 4.2 | Native image build tests | 未执行真实 native image | ❌ 10% | CI 构建启动 |
| PLAN-076 | `api/docs/changes/graalvm-native-support/tasks.md` | 4.3 | Agent 采集配置 | 未发现稳定自动采集产物流程 | ❌ 20% | 增加 agent run profile |
| PLAN-077 | `api/docs/changes/graalvm-native-support/tasks.md` | 5.1 | MyBatis Plus native 配置 | 有部分 reflect/resource 配置 | 🟠 55% | 真实 CRUD smoke |
| PLAN-078 | `api/docs/changes/graalvm-native-support/tasks.md` | 5.2 | Druid native 配置 | 未见完整验收 | ❌ 30% | 连接池 smoke |
| PLAN-079 | `api/docs/changes/graalvm-native-support/tasks.md` | 5.3 | Redis/Redisson native 配置 | 未见完整验收 | ❌ 30% | 连接与序列化 smoke |
| PLAN-080 | `api/docs/changes/graalvm-native-support/tasks.md` | 5.4 | Camunda native 配置 | 未见完整验收 | ❌ 20% | Workflow native smoke |
| PLAN-081 | `api/docs/changes/graalvm-native-support/tasks.md` | 5.5 | OAuth/JWT native 配置 | 有相关类但未完成原生验收 | ❌ 30% | 授权流程 native smoke |

- Task/Phase 总数：**81**。
- Phase 1 已基本形成完整纵向闭环。
- Phase 2 多人仿真和 GraalVM 原生构建是最集中的未完成区域。
