# ENTRY / selected-output finalization 组合候选验证（2026-09-30）

本记录是源码/验证证据补充，不是第二套执行 ledger。长期架构仍见 `fusion-detailed-design-v2.md`；本记录不修改冻结的 HTTP 合同，不表示产品可验收或已经发布。

## 当前组合候选

- 隔离工作树：`/home/isp/wsps/cyf/.worktrees/juyiting-multimedia-deliberation-20260928/api-entry-finalization-integration-v1`。
- commit：`f93febe983afe3619e1b5057937d9db330adece0`；tree：`8289c1a364df862427715e31cb71e3d318e593de`。
- 合入内容：当前需求修订读取、原点将操作投影、显式首轮动作及 selector-only v2 路由、选定产物正式交付/验收、core→deliberation→archive schema readiness。
- 已将精确测试过的组合树 fast-forward 合入 API `codex/juyiting-multimedia-deliberation`，推送后远端 readback=`f93febe983afe3619e1b5057937d9db330adece0`；跨仓 pin 同步为研发基线，仍不是产品 accepted/released。develop/release 未变更。

## 已修正的真实问题

1. nullable `INFORMATION_SCHEMA.STATISTICS.sub_part` 不再因 Optional 映射顺序产生 NPE；真实 prefix/index-column drift 仍拒绝。
2. 正式产物查询的非 NOT_FOUND ACL 异常统一转为已有安全异常，不泄漏依赖消息、不继续 publish。
3. finalization HTTP 在 service 之前验证 conversation/request/step/output 标识；合法人类文本仍允许斜线。
4. ACCEPTING→changes_requested 的测试夹具现在使用真实提交参数产生的 operationId/digest，不再被伪造 `op-1` 提前挡在投影验证；保留单调阶段与真实 delivery/task 状态断言。
5. 真实 MySQL 8.0.21 证明 CHECK 对 UNKNOWN 不拒绝：LEASED 的 null lease version、SUBMITTED 与 TASK_COMPLETED 的 null delivery state 曾漏检。DDL 对这些分支显式增加 IS NOT NULL；未降低检查或伪造 task completed。
6. 新 schema mutex 使用真正等待的 `GET_LOCK(...,-1)`，不以任意更大等待门槛替代旧 deadline；保留归属与 release 核验。

## 实测证据与边界

证据根：`/home/isp/wsps/cyf/evidence/u1u3-entry-finalization-integration-v1/`。

| 验证 | 结果 | 明确边界 |
| --- | --- | --- |
| bounded changed-source 编译 / JUnit v4 | 25 main + 10 selected test sources；99执行，0失败/错误/跳过 | immutable194ec依赖 + 当前源码overlay，不是正常模块构建 |
| 实际 JVM class-load | PASS | 证明实际改动类与测试从精确 overlay 加载，不证明整套应用启动 |
| 当前线程独立 MySQL DDL | 3表重复执行 PASS | 无生产 DML、无共享/其他线程库修改 |
| 实际 MySQL约束 | 26/26 PASS | 版本精度、租约credential清除、NULL防穿透、原键/选定源唯一、owner/case隔离 |
| 实际 MySQL锁 | PASS | 两个自有会话观测User lock；非Owner释放0、Owner释放1、等待者获取1、释放后空闲；未抢占/取消 |
| 正常模块依赖/source-set 回归 | 357次执行，0失败/错误/跳过；84个真实Gradle任务执行 | 正常依赖图/生产源码编译，未复用frozen overlay；含重叠selector，非357独立用例 |
| 生产构建/Provider/浏览器/发布 | NOT_PROVEN | 不产生“可验收”或发布成功声明 |

关键文件：`bounded-result-v4.json`、`gradle-bounded-v4.log`、`bounded-8289c1a3-v4/overlay-load-proof.json`、`mysql-finalization-8289c1a3-v1.json`、`normal-module-result-v1.json`、`gradle-normal-module-v1.log`。此前96/3、97/1及真实MySQL23/26失败证据保留，不改写PASS。

SQL_NULL变更尚未用于生产：旧实验schema与修正后schema采用不同的自有fixture库。`CREATE TABLE IF NOT EXISTS`不会改写已存在的旧CHECK；不能据重复DDL成功推断旧库约束升级完成。正式启用前必须检查真实schema定义，对旧实验schema进行明确授权的迁移或拒绝弱定义；不得无授权DROP/ALTER。

## 剩余施工依赖

1. 正常模块回归/研发feature已完成；仍需实际Java/MySQL生命周期、旧弱CHECK识别/授权迁移与整套构建证据，不能把研发pin用作直接生产激活授权。
2. 按实际服务端/目标Agent能力冻结能力协商合同，接通真实JuyiHall/useHallTaskActions；UI开关不是支持/费用授权。
3. 从工作空间引用必须形成真实owner/task/version/purpose关联；补同会话澄清、上一稿派生输入、EDIT与合法服务端费用授权。当前授权ref仍为空，不能注入假ref绕过WAITING_AUTHORIZATION。
4. 两种接应、真实授权Provider、浏览器生成/修改/预览/下载/保存/正式交付与验收完成后，按exact SHA创建版本release并记录制品及健康证据；全部满足后才通知可验收。

长期不变：一条持久会话，CHAT轻上下文、INSPECT精确读取、EXECUTE真实服务端准入；不是强制三次串行模型调用。一份平台权威资产用于会话展示、工作空间保存、正式交付，客户端目录只是隔离的输入/输出暂存区。
