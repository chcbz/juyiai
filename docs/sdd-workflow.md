> **2026-11-06 现行规则：** 用户告知云效额度用完，CYF 默认改为本地测试、构建、打包和受控部署；不自动启动 Flow。正式证据绑定真实本地构建批次、完整 commit/tree、必要测试与制品 SHA-256，不伪造 Run/CI 身份。保留发布授权、身份/ACL、锁、备份、可恢复安装与线上验收；develop 不自动部署。Gradle 仍先读构建文件并经现有编排器串行执行。下文冲突的 Flow-only/禁止本地构建说明仅作历史，完整规则见根 `AGENTS.md`“本地构建与部署（2026-11-06 用户最新决定）”。本次仅改规则，未改工具/云端配置或实际构建部署；旧 Flow-only 安装器须明确适配本地来源并验证后才能使用。

# Multi-repository SDD workflow

## Source-of-truth rule

| Question | Authoritative location |
| --- | --- |
| What should be built and accepted? | `specs/<feature-id>/` in the root repository |
| What does the system currently do? | Exact task source and actual runtime evidence; `docs/knowledge-base/` is a scoped baseline reference |
| How does it run or get deployed? | `docs/` runbooks and deployment material |
| How is it implemented? | `api/` and `web/` submodules |
| Which backend/frontend pair is an integrated baseline? | The root commit's `api` and `web` gitlinks |

`specs/` records feature intent, current contracts and historical acceptance; use its index to distinguish active guidance from preserved history. `docs/knowledge-base/` is a reverse-engineered baseline reference whose scope/date must be checked, not a live source mirror. Neither replaces source code for implementation details.

<a id="development-efficiency"></a>
## 开发效率与上下文管理（2026-10-08）

### 通用执行规则：所有任务适用

1. **确认范围与基线**：使用现有任务ID和handoff，固定Owner、目标/非目标、验收、源码commit/tree和worktree。分别记录本地HEAD、远端develop（实际查询时间）、受测候选与线上版本，不能相互替代。共享工作区有未提交修改时不自动pull/reset，以免覆盖其他任务。
2. **最小充分上下文**：从根AGENTS → 项目地图 → 相关模块/工具说明 → 当前handoff进入，按需搜索代码。日志、历史证据只记录路径及必要摘要；不要为“补全背景”全量读取。压缩/交接摘要包含目标、范围、源码、已确认结论、证据、阻塞、下一条可执行动作及禁止操作。
3. **连续实现与分层验证**：复用已有工具，先做能暴露本次问题的定向检查，再覆盖相关回归。Owner在授权内连续推进，不逐阶段等待批准，不新增独立Reviewer。精确输入和证据完整性匹配才复用结果；按2026-11-06规则，在固定干净源码、独立输出位置本地执行必要测试、构建和打包；所有Gradle先读构建文件并经编排器串行入口。已有工具、身份、锁、完整性和恢复保护保留；发布须有实际授权，安装、健康及业务验收分别记录。2026-11-09澄清：600秒限定单次构建发布，随构建执行的单元测试计入；异常重试经归因重新计时，不跨候选/尝试累计。回归验证不限时，混合入口按实际阶段记录。超限申请该次例外，不向业务请求或生产服务下传deadline。
4. **接续与收口**：Owner向子Agent/独立worktree显式传递最新项目规则路径、任务ID、源码基线、相关工具和handoff；确认接收方读过，不假设继承聊天或自动重载。在途任务自然接续时提醒，不打断其他任务。稳定知识回写已有模块/架构/运维指南，测试事实保留原证据路径。
5. **效果评估**：沿用[handoff模板](implementation/handoffs/TEMPLATE.md)记录定位、实现、验证、等待与返工原因；未知留空，按可比任务判断端到端收益。下一项真实业务任务优先使用现有流程；只有可证实的实际阻塞才驱动工具扩展，不为提效再建一套框架/台账/审批。

### 按范围裁剪文档与工具，不裁掉风险控制

- 无跨仓契约变化的局部UI/单模块修复，沿用已有任务及handoff、更新受影响说明，不仅为日常进度创建五件套SDD。
- 跨仓功能仍按下文Required feature artifact组织；身份/ACL、事务、迁移、异步契约变化保留明确设计及相关回归。任务大小不替代风险判断。
- 专项验证器只服务其声明范围：执行历史工具及 `--browser` 见[原操作说明](../specs/juyiting-execution-recovery/contract-pilot/README.md)，不是所有功能的统一门禁。不重复维护命令/参数说明。

<a id="efficiency-findings-20261008"></a>
### 效果评估：已证实与待验证（核对：2026-10-08）

- **已证实**：执行历史已有单命令入口，复用隔离后端/数据库与浏览器诊断；精确输入证据完整性核验后可免重复执行。同一固定输入，本次完整验证142.684秒、证据复用23.234秒、首次廉价反馈20.868秒。这是单次验证/缓存观测，不是业务开发前后对照，不外推整体提速比例。
- **未证实**：尚无可比真实业务任务的定位、实现、等待全程数据，不能宣称“小功能从几天降到几小时”，也未测得上下文压缩频率或token消耗下降。
- **证据和边界**：见[本次handoff](implementation/handoffs/EXECUTION-HISTORY-BROWSER-20261008.md)及其中的固定API/Web与proof引用；详细操作沿用[执行历史说明](../specs/juyiting-execution-recovery/contract-pilot/README.md)。此工具只适用于执行历史相关任务，本地浏览器诊断不是正式前端构建、整站OAuth验收或部署证明。

## Required feature artifact

Use one directory per cross-repository feature:

```text
specs/<feature-id>/
├── spec.md             # Problem, goals, non-goals, scope
├── design.md           # UX, API/event/data/security and compatibility contract
├── tasks.md            # Explicit API/Web/integration owners and work items
├── acceptance.md       # Observable acceptance criteria and evidence
└── integration.yaml    # Candidate submodule SHAs and verification state
```

The API contract in `design.md` must state method/path, request/response/event shape, error behavior, authentication/authorization, compatibility, and version/replay semantics when it is asynchronous.

## Lifecycle

1. **Draft** — Create the feature: `./sddw new <feature-id> "title"`; define the problem, goal, non-goal and scope.
2. **Ready** — Agree the contract and split `tasks.md` into `api/`, `web/`, and integration work. Identify migrations, ACL, transactions, SSE/WebSocket replay, and rollback constraints before implementation.
3. **Implementing** — Implement in each submodule on independently reviewable commits. Do not commit one repository's source into the other or into the root.
4. **Integration-ready** — Use the intended clean API/Web worktrees, run relevant tests under the current local-build and workload policy, then pin only the authorized template-format candidate and run `./sddw verify <feature-id>`. Do not change shared checkouts or historical pins to make an audit pass.
5. **Accepted** — Record test commands/results in `acceptance.md`; set `integration.yaml` status to `accepted`; commit the spec update and both submodule gitlinks together in the root repository.
6. **Released** — Add deployment/release evidence only after the actual deployment process succeeds. The root SHA is the reproducible delivery baseline.

## 文档发现与收口

Agent从[根规则](../AGENTS.md)→[文档总入口](README.md)→[责任专题](../specs/INDEX.md)进入。当前正文不要复制历史状态或同义“最新方案”；新支持细则须从责任主spec可达并维护既有`sdd-document-map.json`的discovery选择。默认项目检索用`kb-search.sh --project`，追溯才用`--project-all`。`./sddw check-docs --catalog`列全量角色，`--all-docs`检查所有当前链接及根AGENTS可达性；分类不等于每条陈述已与源码/线上复验。

## Daily commands

```bash
# Inspect coordinated and implementation state
./sddw status

# Read-only current document navigation (not tests or release acceptance)
./sddw check-docs
./sddw check-docs agent-task-collaboration

# Start a cross-repository feature
./sddw new agent-task-collaboration "Agent task collaboration"

# After API and Web commits are checked out locally
./sddw pin agent-task-collaboration
./sddw verify agent-task-collaboration

git add specs/agent-task-collaboration api web
# Stage only this task's specifically reviewed documentation paths, never all docs/.
git commit -m "feat(sdd): integrate agent-task-collaboration"
git push origin master
```

## Integration gate

A root integration commit must include all applicable items:

- `spec.md`, `design.md`, `tasks.md`, and `acceptance.md` are current.
- `integration.yaml` binds the exact candidate actually tested; documentation-only edits preserve existing historical pins and do not run pin against a dirty checkout.
- API, Web, and integration verification commands/results are recorded.
- Breaking behavior, schema migrations, access-control changes, and async replay semantics are explicitly assessed.
- The root commit updates the submodule gitlinks only after the submodule commits are pushed and reproducible.

For identity/ACL/transaction/migration changes, the single Owner self-checks the actual affected boundary and recovery behavior. Do not add an independent Reviewer or repeated approval stages. Ordinary component integration goes to develop after self-check; deployment requires the actual release authorization.

CYF uses local tests, builds and packaging on fixed clean source with independent output. Preserve exact commit/tree, real LOCAL build evidence, tests and artifact SHA-256, identity, locks, backup and recoverability. Read the relevant build.gradle before Gradle and use the existing orchestrator; reuse Web test/build commands. Cloud Flow is not the default prerequisite. As clarified on 2026-11-09, each unit-test/build/release attempt is limited to 600 seconds; a diagnosed retry starts a new attempt while retaining the previous failure. Regression and business acceptance are timed separately without that limit. Do not rename phases or running attempts to evade limits, apply the build deadline to application requests/production services, or retry blindly. Expected or actual overruns require an explicit exception for that attempt; verify the real tool behavior before execution. Record build, install, health and business acceptance separately. Production data and paid operations remain scoped to actual authorization.

## 2026-09-14 reconciliation and archival rules

- Current feature index: `specs/INDEX.md`; full execution/planning audit: `docs/implementation/SDD_STATUS_20260914.md`.
- `delivery-status.md` is a dated read-only projection, not a second owner/gate ledger. Runtime transitions remain exclusively orchestrated in TASKS.yaml.
- A frozen SHA-bound contract must not be rewritten for routine progress. Add a dated status supplement; preserve the original bundle and evidence binding. Contract changes need their own reviewed version.
- Keep intent/design, source acceptance, integration, artifact release, activation and actual user acceptance distinct. A build or API health check does not prove functional acceptance.
- Archive completed delivery records with exact evidence and residual follow-up links. Do not remove live tasks, evidence, worktrees, services or notification jobs. Historical failures/waivers stay failures/waivers, not PASS.
- Only archive an entire feature when its own scope is accepted and released. A prior release can be archived while later defects remain active. Record archival separately; do not invent an `archived` runtime gate.
- Never run `sddw pin` against stale/dirty implementation checkouts just to make a document verifier pass. Preserve historical pins; missing release-pair evidence remains explicit. Client-only features can have Web N/A, which the current strict `sddw verify` does not support.
- Document-only reconciliation requires structure/link/schema/evidence-consistency checks, not Gradle/Vite, deployment or a separate Reviewer. Never mass-stage unrelated working-tree changes.

<a id="feature-documentation-closeout"></a>
## Feature documentation closeout（2026-10-08）

已核验特性收口时，更新现有主题说明而不是把实施记录拼入一份巨大架构文档：

| 稳定知识 | 长期归属 |
| --- | --- |
| 系统组成、模块职责和依赖 | `docs/knowledge-base/01-system-overview.md`、03/05 架构主题 |
| 功能行为、接口/事件、状态流与权限边界 | 对应模块主题（如 `06-juyiting-end-to-end.md`、07 数据安全） |
| 配置、排障、发布与恢复 | 现有 runbook / 发布策略 |
| 关键取舍及原因 | 既有 DECISIONS / 对应决策记录 |
| 原需求、冻结设计、执行计划、测试/发布回执 | 原路径保留为历史来源，日常入口链接现行主题 |

操作顺序：核对精确源码和已有验收范围 → 提炼稳定知识到相应主题 → 写明核对日期、commit、章节覆盖与未验证边界 → 特性目录增加来源导航/收口说明 → 当前入口指向主题，追溯才进入历史材料。

- 只完成一部分时按切片收口；保留其他活动任务，不将整个 feature 重标 released/archived。源码已实现未发布时明确标注，历史上线时间不代表当前线上版本。
- 冻结文件、证据和其路径不改写、不搬动；优先新增目录导航建立双向引用。需要物理归档时另核引用和证据绑定，不借整理删除历史失败或活跃待办。
- 局部复核不更新全库 `BASELINE.yaml` 的生成日期；未复核内容明确沿用旧基线。文档状态是阅读提示，不是第二份 Owner/gate 台账。
- 不新增独立审查、审批或应用构建；文档改动仅检查链接、内容/源码证据对应及原材料未变。整理完成不等于功能新增验收通过。
- 样板：[聚义厅 UI 当前规格](../specs/juyiting-ui-baseline-20261006/spec.md)。


<a id="sdd-document-cleanup"></a>
## SDD 文档整理（2026-10-23）

日常入口采用每项需求的 spec/design/tasks/acceptance（现有代码级详设可按需保留），入口不累加历史日期的状态覆盖。已完成的临时变更，业务契约并入现有详设、结果并入验收；被取代的版本/过期工期在确认关键内容已承接后删除，不靠文件名日期批量清理。

首轮整理CYF索引、聚义厅体验优化及外单旧设计副本。根源码基线 `5e6ab2b6f1a156c320189f17d76941fbe623738a`；不修改API/Web源码，不查询远端或生产，不重标功能状态。首轮其余特性只更新索引导航；后续全目录整理范围见下文。冻结合同、原始证据、活动handoff、历史会话来源索引保留不改。

精确旧路径→承接文档及项目外备份见 [sdd-document-map.json](sdd-document-map.json)。历史证据中的旧路径/摘要保留原义，用映射或备份追溯，不能把它们的旧SHA改成新文档SHA。备份含删除前原文和本轮修改前文件，恢复时仅按manifest逐文件核对，不覆盖后续修改或其他任务。


### 全目录收口

同日按用户要求继续检查全部CYF specs特性目录，逐项保留/合并结论已写入INDEX和sdd-document-map；索引包括账号/权限、Agent/Runtime、任务、媒体/资料、知识库、UI、经济和交付，以及模板/历史会话来源。已将明确取代的D1–D4/SE-1旧稿、两套旧UI提案和过期排期移出工作区；不是删除所有历史文件，也不是重判所有功能完成。

技术边界在原spec/design/tasks/acceptance承接，未覆盖测试/冻结bundle/发布记录/数据修复计划继续保留；含版本的基础+增量协议不可机械删除。本轮未修改api/web源码、tools/fixtures、integration pins、运行台账、应用或生产，也不修改其他项目/全局规则。新旧文件SHA及恢复清单保存在项目外备份，原证据链接用删除映射解析，不能改旧摘要冒充新合同。


<a id="sdd-document-check"></a>
## 文档导航检查与候选核验分开（2026-10-23）

- `./sddw check-docs [feature-id]`：复用现有SDD入口进行只读轻量检查。全目录模式覆盖根/组件AGENTS、项目地图、SDD流程/索引、知识入口、Web原型规格和特性五件套/README/体验优化主文档；核对本地Markdown链接目标（剥离query/fragment）、相关规则中的路径、删除映射及integration中既定的当前文档标量引用。历史来源目录显式作为例外，不补造功能五件套。
- 结果 `DOCUMENT_NAVIGATION_PASS` **仅表示上述导航检查通过**。不解析全量YAML schema，不核验所有锚点/源码符号/远端链接/全部证据摘要，不执行测试、构建、发布或修改pin；API/Web未指定或历史SHA与checkout不同，不在此检查中视为功能失败。畸形/不支持的当前导航标量明确失败。
- `./sddw verify <feature-id>` 仍是**模板格式候选的双端精确checkout比对**：要求 `pinned_revisions.api_commit/web_commit` 的现有模板形态，不是全库历史审计器。嵌套component、candidate_commit及N/A等非模板记录可用check-docs检查导航，但候选核验仍需按真实格式显式核对源码和已有验证证据；不能因为文档通过就冒称这些候选通过verify，也不为此把历史记录改成当前SHA。
- 本轮仅修正文档指针，未改变历史源码commit/tree、测试结果或发布事实。技能SE-1原design已通过integration.previous_design指向项目外备份；复制工作区时须同时保留清理映射及备份索引，不能把新SE-2的design.md当旧稿。
- 历史before快照中的相对路径按原位置解释，原名/摘要不改写，删除原文查`sdd-document-map.json`。旧工作台63项来源`docs/ui-workbench/feature-coverage.md`和静态API盘点中的旧resource AuthenticationController目前不在工作区；这两处是未恢复的历史来源，不是当前导航成功或功能重新验收的证明，不擅自链接到不同内容。
- 既有索引仍区分意图、实现、历史发布和当前线上；更新本节不刷新知识库旧基线。定向工具测试：`python3 -B -m unittest discover -s ops/orchestration/tests -p test_sdd_docs.py -v`。


### 校验必要性（2026-10-24）

新建/保留拒绝条件必须在对应规格写清风险、输入条件、失败影响和回归；不能仅因旧代码或旧测试存在就保留。无依据项默认待移除，先按实际调用链识别会否削弱身份/资金/数据完整性，必要则补完整理由，否则删除。沿用[校验必要性规格](../api/docs/interface-catalog/validation-policy.md)，不新增统一校验平台、逐项审批或硬门禁。
