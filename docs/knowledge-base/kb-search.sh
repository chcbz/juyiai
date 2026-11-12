#!/usr/bin/env bash
set -euo pipefail

KB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$KB_DIR/../.." && pwd)"
BASELINE="$KB_DIR/BASELINE.yaml"
INVENTORY="$KB_DIR/04-backend-api-inventory.md"
INDEX_BUILDER="$KB_DIR/build-api-index.py"

usage() {
  cat <<'USAGE'
Usage:
  kb-search.sh <ripgrep-pattern>       # summary docs; skips the large raw API inventory
  kb-search.sh --project <pattern>    # project current routes, including specs/regression
  kb-search.sh --project-all <pattern> # explicitly include history and unverified references
  kb-search.sh --all <pattern>         # include the raw API inventory
  kb-search.sh --api <ControllerName>  # print all matching Controller sections
  kb-search.sh --freshness             # returns nonzero for stale/dirty/missing state
  kb-search.sh --help
USAGE
}

yaml_value() {
  local key="$1"
  sed -nE "s/^[[:space:]]*${key}:[[:space:]]*\"?([^\"]+)\"?[[:space:]]*$/\1/p" "$BASELINE" | head -n 1
}

current_sha() {
  local component="$1"
  local directory="$ROOT_DIR"
  [[ "$component" == root ]] || directory="$ROOT_DIR/$component"
  if [[ ! -d "$directory" ]]; then
    printf 'unavailable'
    return
  fi
  git -C "$directory" rev-parse HEAD 2>/dev/null || printf 'unavailable'
}

worktree_state() {
  local component="$1"
  local directory="$ROOT_DIR"
  [[ "$component" == root ]] || directory="$ROOT_DIR/$component"
  if [[ ! -d "$directory" ]]; then
    printf 'missing'
  elif [[ -n "$(git -C "$directory" status --porcelain 2>/dev/null)" ]]; then
    printf 'dirty'
  else
    printf 'clean'
  fi
}

case "${1:-}" in
  --project|--project-all)
    [[ $# -eq 2 ]] || { usage >&2; exit 2; }
    if [[ "$1" == --project-all ]]; then
      exec python3 -B "$ROOT_DIR/ops/orchestration/sdd_docs.py" --search "$2" --history
    fi
    exec python3 -B "$ROOT_DIR/ops/orchestration/sdd_docs.py" --search "$2"
    ;;
  --api)
    controller="${2:-}"
    if [[ -z "$controller" ]]; then
      usage >&2
      exit 2
    fi
    controller="${controller#\`}"; controller="${controller%\`}"
    awk -v heading="## \`$controller\`" '
      /^## / { printing=($0 == heading); if (printing) found=1 }
      printing { print }
      END { if (!found) exit 3 }
    ' "$INVENTORY" || {
      status=$?
      if [[ $status -eq 3 ]]; then
        printf 'Controller section not found: %s\n' "$controller" >&2
      fi
      exit "$status"
    }
    ;;
  --all)
    pattern="${2:-}"
    if [[ -z "$pattern" ]]; then
      usage >&2
      exit 2
    fi
    exec rg -n -i --glob '*.md' -- "$pattern" "$KB_DIR"
    ;;
  --freshness)
    stale=0
    printf 'component  baseline                                  current                                   worktree state\n'
    root_current="$(current_sha root)"
    root_worktree="$(worktree_state root)"
    root_state=diagnostic
    if [[ "$root_worktree" != clean ]]; then
      root_state=DIRTY
      stale=1
    fi
    printf '%-10s %-41s %-41s %-8s %s\n' root not-version-pinned "$root_current" "$root_worktree" "$root_state"

    for component in api web; do
      expected="$(yaml_value "${component}_sha")"
      current="$(current_sha "$component")"
      worktree="$(worktree_state "$component")"
      state=current
      if [[ -z "$expected" || "$current" == unavailable || "$expected" != "$current" ]]; then
        state=STALE
        stale=1
      fi
      if [[ "$worktree" != clean ]]; then
        state="${state}+DIRTY"
        stale=1
      fi
      printf '%-10s %-41s %-41s %-8s %s\n' "$component" "${expected:-unavailable}" "$current" "$worktree" "$state"
    done

    expected_controllers="$(yaml_value controller_files)"
    expected_mappings="$(yaml_value method_mappings)"
    current_controllers="$(rg -c '^## `.*Controller`$' "$INVENTORY" || true)"
    current_mappings="$(rg -c '^\| [0-9]+ \|' "$INVENTORY" || true)"
    index_state=current
    if ! python3 "$INDEX_BUILDER" --check >/dev/null 2>&1; then
      index_state=STALE
      stale=1
    fi
    counts_state=current
    if [[ "$expected_controllers" != "$current_controllers" || "$expected_mappings" != "$current_mappings" ]]; then
      counts_state=STALE
      stale=1
    fi
    printf 'artifact   expected                                  current                                   state\n'
    printf '%-10s controllers=%-28s controllers=%-28s %s\n' inventory "$expected_controllers" "$current_controllers" "$counts_state"
    printf '%-10s mappings=%-31s mappings=%-31s %s\n' inventory "$expected_mappings" "$current_mappings" "$counts_state"
    printf '%-10s %-41s %-41s %s\n' api-index generated checked-in "$index_state"
    exit "$stale"
    ;;
  --help|-h|'')
    usage
    ;;
  *)
    exec rg -n -i --glob '*.md' --glob '!04-backend-api-inventory.md' -- "$1" "$KB_DIR"
    ;;
esac
