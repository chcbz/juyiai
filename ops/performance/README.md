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
