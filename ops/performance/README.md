# PERF-01 offline inventory

`inventory.py` is a dependency-free Python 3.6+ offline scanner/reconciler. It never starts the API or contacts a runtime.

## Commands

```sh
python3 ops/performance/inventory.py scan \
  --source-root /path/to/api \
  --profile grey --api-commit SHA --api-tree TREE \
  --framework-manifest framework-grey.json --output inventory-grey.json
python3 ops/performance/inventory.py reconcile \
  --inventory inventory-grey.json --runtime runtime-grey.json --profile grey \
  --expected-api-commit SHA --expected-api-tree TREE \
  --inventory-sha256 TRUSTED_INVENTORY_FILE_SHA256 \
  --runtime-sha256 TRUSTED_RUNTIME_FILE_SHA256
```

The scanner supports only literal `@RequestMapping` and Spring's verb mappings, literal `path` **or** `value`, literal string/string-array paths, and `RequestMethod` arrays. A mapping without a method is `ANY`. It scans production Java sources (excluding standard test-source roots) so controllers not named `*Controller.java` and custom annotation declarations cannot disappear solely because of filenames. Unknown type/meta-annotations are diagnosed before filename relevance filtering; this catches a dependency-defined marker such as `@GM class OddEndpoint` without attempting dependency resolution. Unknown annotations on relevant methods, custom composed mappings, aliases, inheritance, conditional expressions, and unsupported grammar are also fatal diagnostics; they are never inferred.

The explicit non-mapping annotation allowlist is `KNOWN_NON_MAPPING_ANNOTATIONS` in `inventory.py`. Extending it is a source-reviewed change: an unrecognized annotation may be a composed route mapping and therefore fails closed. This remains a bounded literal parser, not a Java compiler or Spring annotation resolver.

## Inventory schema and trusted pins

Scan output uses strict inventory schema version 3. Reconciliation rejects unknown/missing top-level fields, unknown or severity-altered diagnostic codes, malformed or unsorted controller records, a dirty source flag, malformed source/API digests, inconsistent `ok` status, and an embedded framework manifest whose canonical content hash does not match its source binding.

The following reconcile values are **trusted external pins**, not values discovered from the artifacts being checked:

- `--expected-api-commit` and `--expected-api-tree` come from the independently approved API source handoff.
- `--inventory-sha256` comes from the independently approved scan-artifact handoff.
- `--runtime-sha256` comes from the independently approved capture-artifact handoff.

Do not calculate one of these expected hashes from the candidate file and immediately treat that result as approval. The command computes actual file hashes only for comparison with caller-supplied pins. The inventory file hash binds its routes, diagnostics, clean-source assertion, Java-content digest, and embedded framework-manifest digest. A matching hash proves identity with the externally pinned artifact; it does not by itself prove that the original scan or capture process was trustworthy.

## Declared surfaces

The framework manifest is strict JSON bound to the exact profile/API commit/tree. Framework, management, and error route arrays are mandatory, non-empty, well formed, and independently reconciled:

```json
{
  "profile": "grey",
  "api_commit": "...",
  "api_tree": "...",
  "framework_routes": [{"method": "GET", "path": "/framework", "handler": "framework"}],
  "management_routes": [{"method": "GET", "path": "/actuator/health", "handler": "health"}],
  "error_routes": [{"method": "GET", "path": "/error", "handler": "error"}]
}
```

Legacy `routes`/`mappings`, empty arrays, unknown fields, malformed records, dirty source checkouts, and missing/mismatched bindings are nonzero. Static/controller, framework, and management lists remain separate in output.

## Trusted runtime envelope

A raw actuator export is not runtime evidence. The capture owner must provide this strict envelope:

```json
{
  "profile": "grey",
  "api_commit": "...",
  "api_tree": "...",
  "capture_content_sha256": "lowercase SHA-256 of canonical payload JSON",
  "payload": {
    "framework_mappings": {"contexts": {}},
    "management_mappings": {"contexts": {}},
    "error_mappings": {"contexts": {}}
  }
}
```

The internal payload hash is mandatory and verified over UTF-8 JSON serialized with sorted keys and compact separators. The independently supplied `--runtime-sha256` additionally binds the complete transport file. All three payload surfaces must enumerate at least one route. The error surface is kept separate from application/framework mappings, so moving `/error` between surfaces cannot cancel a mismatch. Direct strict route arrays and Actuator mappings are supported. Spring Boot 4 `details.requestMappingConditions.methods` plus `patterns` are expanded as a Cartesian product; malformed methods, paths, records, sections, or unknown shapes are rejected rather than skipped. Application/framework and management surfaces are compared independently, so moving a route between lists cannot conceal a mismatch.

A capture owner must export the real Spring Boot HandlerMapping/management mapping payload for one exact profile, then wrap it in this envelope; the tool performs no live capture itself. The optional normalized registry input is an exact four-surface projection (`kind` = `controller`, `framework`, `management`, or `error`; each entry contains only `kind`, `method`, `path`) and must cover every declared route with no unknown, wildcard, duplicate, or dynamic entry. This slice provides no YAML parser and no claim that any real grey/prod runtime has passed reconciliation until trusted capture and registry artifacts are supplied.

## 承办推荐留出集评分（非生产，详设 §6.1）

`recommendation_holdout.py` 是离线评分工具，不生成标签、不训练阈值、不调用模型或写业务数据。先由标注人员在**不看推荐结果**时冻结任务、当时可披露的授权能力快照、任务族和可接受候选。任务归属只出现一次，同模板/同源改写归同一个 `familyId`，校准与留出不能混用。事实快照由采集责任方核验；工具只核对摘要相等，不能证明来源真实。文件及独立冻结摘要留在获授权的非生产证据区，不提交私有任务或响应。

```sh
python3.11 ops/performance/recommendation_holdout.py labels.json run.json \
  --expected-labels-sha256 "$FROZEN_LABELS_SHA" \
  --expected-ranking-version "$FROZEN_API_RANKING_VERSION" \
  --expected-configuration-sha256 "$FROZEN_RANKING_CONFIG_SHA" > report.json
```

- `labels.json`：`format=recommendation-labels-v1`，`cases[]` 每项为 `caseId, familyId, partition(CALIBRATION/HOLDOUT), taskId, taskVersion, factsSha256, candidates, caseTags`。`candidates` 将当时**全部**授权候选ID映射到 `ACCEPTABLE / NOT_ACCEPTABLE / INSUFFICIENT`。`caseTags` 可以为空或多选：`SHORT_DESCRIPTION, MULTI_ATTACHMENT, NEGATED_OR_CONDITIONAL, PARAPHRASE, PARTIAL_CAPABILITY`。报告列出留出样本数量为零的类型。
- `run.json`：`format=recommendation-run-v1`，`labelsSha256, configurationSha256, rankingVersion, results[]`。每个留出任务一项 `caseId, factsSha256, data`；`data` 使用真实推荐接口信封中的业务对象，保留用户实际看到的候选顺序。配置摘要绑定实际候选代码、检索/排序参数、索引与编码代次、评级策略。固定同一输入下的降级场景另存一份运行，不复制任务当独立样本。存在失败或缺失的请求，不丢弃后计算整体成功率；保留原始失败并将该运行标为无法完整评分。
- `highPrecision` 分母含所有HIGH（含人工认为资料不足的HIGH，不能计为正确）；`hitAt3` 按可接受集合非空的任务计，包括只排入前三而未给正等级的情况。两者不能替代业务覆盖（至少一个HIGH/MEDIUM的任务比例）。确定无匹配且有候选的任务另报误推荐率，资料不足不当作确定无匹配。UNKNOWN按候选计，降级按任务计，整体与各检索模式分别报告。没有分母时输出 `null`，不是0或100%。
- 区间是按任务族聚合的保守双侧Hoeffding边界，单项95%，非多指标联合保证；须满足不同任务族独立、评估分母权重固定的条件，不要求族内候选相互独立。报告只含计数、比率、区间及输入/评分程序摘要；不自动批准等级上线。正式验收前固定判据、抽样方案与适用人群，不能在看完留出结果后调整再用原集宣称达标。

- B49/E02：额外分别给出 `mediumPrecision`、`positivePrecision`（HIGH/MEDIUM）和 `suitableRatedTaskCoverage`（确有适配候选的任务里，至少一人被正确正向评级的比例）。各 caseTag 独立给出相同统计，标签可重叠，不合并相加。Top3 命中但只给正确候选 UNKNOWN 时，不计入正确正向评级覆盖。这些是诊断量，不降低原 HIGH precision / Hit@3 目标。

- `FROZEN_API_RANKING_VERSION` 在留出运行前从固定候选及其实际加载的策略独立核对并保存，不从待评 `run.json` 回填。即使整批响应都一致地返回了另一版本（例如未加载配置而退回基础 RRF），也拒绝为原策略出具报告。无策略基线试验须明确固定基础版本。

- `byResponseState` 单列 READY、NO_MATCH、NO_CANDIDATES 与 DEGRADED（仅出现的组）；特别检查人工判有可承办人但 API 返回 NO_MATCH 的任务，不把空名册并入。运行须保留原 `degradedReasons`；降级无原因或正常响应附降级原因的矛盾输入不能评分。
