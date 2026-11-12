#!/usr/bin/env bash
set -Eeuo pipefail
PATH=/usr/sbin:/usr/bin:/sbin:/bin; export PATH
IFS=$'\n\t'
umask 077

ROOT="${H06_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)}"
API_WORKTREE=/home/isp/wsps/cyf/.worktrees/h05a-archive-question-api
API_REF=codex/h05a-archive-question-api
API_HEAD=8298b027c9c48ca42b0e0c819106b0d5e20008f2
API_TREE=226cd7985a141a06e00f0c9d8441fb83b085c39b
WEB_WORKTREE=/home/isp/wsps/cyf/.worktrees/h05w-archive-question-web
WEB_REF=codex/h05w-archive-question-web
WEB_HEAD=0b3d93041faaf6c3212a8a9f45a1ba64acd2108f
WEB_TREE=2ba166c2771175ef658e442b782a28992c81c8c3
EVIDENCE_ROOT=/var/tmp/cyf-h06
CHROME_PATH=/usr/lib64/chromium-browser/chromium-browser
STAGE=all
DRY_RUN=0
RUN=
RESULT=FAIL
RESULT_DETAIL='runner did not reach a terminal gate result'
FINALIZED=0
ORIGINAL_ARGS=("$@")

SOURCE_SHA=1023e78e50df0b0902b47ea2f29f0901aa14e55b6d243bd1ce8cfa3202440b47
MANIFEST_FILE_SHA=fe2c1cfd551e29ebc70665b121bf3480d1941728d8fa0cd0fa3f68d584335210
MANIFEST_SEMANTIC_SHA=1656be0bc81b6d73a9bd2bf44121df36ae5a5a66f39f34114bf108e91e317ccc
GOLDEN_SHA=a601e36874fa04b5425a391d34d228e7aa2cffbeea6c6db16afcaf88d8696a1d
EDITION_ID=shuihuzhuan-zh-120-v1
EXPECTED_CHAPTERS=120
EXPECTED_PREFACE_PARAGRAPHS=11
EXPECTED_CHAPTER_PARAGRAPHS=3666
EXPECTED_TOTAL_PARAGRAPHS=3677
MYSQLD=
MYSQL=
MYSQLADMIN=
GRADLE_LOCK=/tmp/cyf-gradle.lock
CYF_HEAVY_RESOURCE_LOCK=/tmp/cyf-heavy-resource.lock
BROWSER="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/archive-pavilion-h06-browser.mjs"
LIB="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/archive-pavilion-h06-lib.sh"
H06_WORKER_UID=61006
H06_WORKER_GID=61006
H06_CANDIDATE_COMMIT=${H06_CANDIDATE_COMMIT:-}
H06_CANDIDATE_TREE=${H06_CANDIDATE_TREE:-}
CANDIDATE_HEAD=
CANDIDATE_TREE=
BOOTSTRAP_DIR=
H06_CHROMIUM_TREE_SHA256=c47dcad2113aef43e03be8f16522f718ac01578c38e026f16cf2fef5cbe7b1d6
H06_CHROMIUM_EXEC_SHA256=08c7cca9bf311291f3e4f52843ecfd2d9003f067db1b5bd3df567743fa60ad13
H06_GRADLE_ALLOWLIST_SHA256=6b783a5b55417788c1067f009ae01cfdc4fcbee3e84596d53926d57854642a23
H06_MAIN_CANONICAL_SHA256=d53dc76b8cc82b192a6cb07d7301091a6b8921475a1f5bc237cf1faa642c2522
H06_BROWSER_FILE_SHA256=2c82ce39026d743d603418b186d6d34e4310ca1857687d0bc1e8472ae00f12c6
H06_LIB_FILE_SHA256=976e4ab905474b8ffd5dc4a3feef9e7562e9d049f7828f2a134f409d4099dd6d

usage() {
  cat <<'USAGE'
Usage: run-isolated-archive-pavilion-h06.sh [stage] [options]

Stages (choose one; default --all):
  --prepare        Candidate provenance, frozen pins, content and default-off gates
  --mysql          Prepare + disposable MySQL 8.0.21 exact H02/H03/H05A selectors
  --runtime        Prepare + pinned artifact build/verify + repo-local OAuth/API/Web/browser gate
  --release-drill  Prepare + pinned build/verify + namespaced execute deploy/off/rollback drill
  --all            Run every stage in order

Options:
  --dry-run                    Print the fail-closed frozen plan; no evidence/heavy work
  --evidence-root PATH         Outside-repository evidence parent (default /var/tmp/cyf-h06)
  --chromium PATH              Must equal frozen root-owned Chromium path
  --help

The API/Web worktrees, refs, heads and trees are compiled-in acceptance pins and
cannot be overridden. Runtime and release dependencies are started only by this
repo-local runner inside route-empty mount/network/PID namespaces. No external fixture executable, bearer token, accepted-evidence root, or self-signed runtime inventory is accepted. Non-dry execution requires this runner and every release dependency to be tracked in one clean committed candidate tree. Optional H06_CANDIDATE_COMMIT and H06_CANDIDATE_TREE pins are exact external anchors supplied by the orchestrator.

Exit codes: 0 PASS (or dry-run plan), 3 BLOCKED missing safe local prerequisite,
other nonzero FAIL. Production deployment and DB operations are never performed.
USAGE
}
die() { RESULT=FAIL; RESULT_DETAIL="$*"; printf 'FAIL: %s\n' "$*" >&2; exit 2; }
blocked() { RESULT=BLOCKED; RESULT_DETAIL="$*"; printf 'BLOCKED: %s\n' "$*" >&2; exit 3; }
log() { printf '[H06] %s\n' "$*"; [[ -z "$RUN" ]] || printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "${ROOT_LOGS:?}/commands.log"; }
require_command() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
h06_repo_git() { local repo="$1"; shift; git -c safe.directory="$repo" -C "$repo" "$@"; }
require_physical_file() { [[ -f "$1" && ! -L "$1" ]] || die "required physical file missing: $1"; }
require_full_oid() { [[ "$2" =~ ^[0-9a-f]{40}$ ]] || die "$1 is not a full lowercase Git object ID"; }
next_arg() { (($# >= 2)) || die "missing value for $1"; printf '%s' "$2"; }
acquire_heavy_resource_lock() {
  printf 'HEAVY_RESOURCE_LOCK_WAIT path=%s pid=%s\n' "$CYF_HEAVY_RESOURCE_LOCK" "$$" >&2
  exec {CYF_HEAVY_RESOURCE_LOCK_FD}>"$CYF_HEAVY_RESOURCE_LOCK"
  flock -x "$CYF_HEAVY_RESOURCE_LOCK_FD"
  printf 'HEAVY_RESOURCE_LOCK_ACQUIRED path=%s pid=%s capacity_admission=disabled\n' \
    "$CYF_HEAVY_RESOURCE_LOCK" "$$" >&2
}

while (($#)); do
  case "$1" in
    --prepare|--mysql|--runtime|--release-drill|--all) STAGE=${1#--} ;;
    --dry-run) DRY_RUN=1 ;;
    --evidence-root) EVIDENCE_ROOT="$(next_arg "$@")"; shift ;;
    --chromium) [[ "$(next_arg "$@")" == /usr/lib64/chromium-browser/chromium-browser ]] || die "--chromium is frozen to /usr/lib64/chromium-browser/chromium-browser"; shift ;;
    --api-worktree|--api-ref|--api-head|--api-tree|--web-worktree|--web-ref|--web-head|--web-tree)
      die "$1 is forbidden: H06 acceptance pins are immutable" ;;
    --help|-h) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done
require_full_oid api-head "$API_HEAD"; require_full_oid api-tree "$API_TREE"
require_full_oid web-head "$WEB_HEAD"; require_full_oid web-tree "$WEB_TREE"
[[ "$EVIDENCE_ROOT" == /* ]] || die 'evidence root must be absolute'
EVIDENCE_ROOT_RAW="$EVIDENCE_ROOT"
EVIDENCE_ROOT="$(python3 -c 'import os,sys;print(os.path.normpath(sys.argv[1]))' "$EVIDENCE_ROOT_RAW")"
[[ "$EVIDENCE_ROOT_RAW" == "$EVIDENCE_ROOT" ]] || die 'evidence root must already be normalized without trailing slash, dot, or parent traversal'
[[ "$EVIDENCE_ROOT" =~ ^/var/tmp/cyf-h06(-[A-Za-z0-9][A-Za-z0-9._-]{0,63})?$ ]] \
  || die 'evidence root must be /var/tmp/cyf-h06 or one single-level /var/tmp/cyf-h06-SUFFIX directory'

print_plan() {
  cat <<EOFPLAN
H06_MODE=DRY_RUN
STAGE=$STAGE
API_WORKTREE=$API_WORKTREE
API_REF=$API_REF
API_HEAD=$API_HEAD
API_TREE=$API_TREE
WEB_WORKTREE=$WEB_WORKTREE
WEB_REF=$WEB_REF
WEB_HEAD=$WEB_HEAD
WEB_TREE=$WEB_TREE
EVIDENCE_ROOT=$EVIDENCE_ROOT
CONTENT_SOURCE_SHA256=$SOURCE_SHA
CONTENT_MANIFEST_FILE_SHA256=$MANIFEST_FILE_SHA
CONTENT_MANIFEST_SEMANTIC_SHA256=$MANIFEST_SEMANTIC_SHA
CONTENT_GOLDEN_FILE_SHA256=$GOLDEN_SHA
MYSQL_SELECTORS=cn.jia.chat.archive.service.ArchiveMySqlIntegrationTest,cn.jia.chat.archive.service.ArchiveReaderDataMySqlIntegrationTest,cn.jia.chat.archive.service.ArchiveQuestionMySqlIntegrationTest
GRADLE_SERIALIZATION=flock_-w_600_-x_/tmp/cyf-gradle.lock;--no-daemon;--max-workers=1
GRADLE_USER_HOME=fresh_run_local_UID61006_owned
GRADLE_CACHE_SNAPSHOT=lock_held_candidate_pin_6b783a5b55417788c1067f009ae01cfdc4fcbee3e84596d53926d57854642a23;wrapper_gradle_9.3.1;modules-2/files-2.1;source_before_equals_staged_equals_source_after_equals_pin
GRADLE_MUTABLE_STATE_COPY=EXCLUDED
WEB_ARCHIVE_READER_REGRESSION=pinned_tree_exact_38_pass_0_fail;node_and_npm_digest_version_bound
RELEASE_INPUT_LIFECYCLE=single_byte_sequence_single_sha_same_logical_artifactRoot
BUILD_NETWORK_NAMESPACE=HOST_NETWORK_ALLOWED_FOR_DEPENDENCY_RESOLUTION
RUNTIME_FIXTURE_EXEC=REJECTED
RELEASE_FIXTURE_EXEC=REJECTED
EXTERNAL_BEARER_TOKENS=REJECTED
CANDIDATE_COMMIT_PIN=${H06_CANDIDATE_COMMIT:-OPTIONAL_EXACT_RUNNER_PIN}
CANDIDATE_TREE_PIN=${H06_CANDIDATE_TREE:-OPTIONAL_EXACT_RUNNER_PIN}
CANDIDATE_TRUST=clean_committed_tree_plus_versioned_dependency_digests
EXTERNAL_ACCEPTED_EVIDENCE=REJECTED
EXTERNAL_RUNTIME_INVENTORY=REJECTED
PRIVILEGE_MODEL=root_namespace_setup_then_uid61006_no_new_privs
FIXTURE_IMPLEMENTATION=REPO_LOCAL_TRUSTED_NAMESPACE_DRIVER
RUNTIME_RELEASE_NETWORK_POLICY=unshare_mount_network_pid;loopback_only;empty_routes
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
PRODUCTION_DB_OPERATION=NOT_PERFORMED
DRY_RUN_RESULT=PLAN_ONLY_NOT_GATE_PASS
EOFPLAN
}

if ((DRY_RUN)); then
  print_plan
  exit 0
fi

bootstrap_cleanup() {
  local status=$?
  if [[ -n "${BOOTSTRAP_DIR:-}" && "${H06_BOOTSTRAPPED:-0}" == 1 && -d "$BOOTSTRAP_DIR" ]]; then
    rm -rf --one-file-system -- "$BOOTSTRAP_DIR" 2>/dev/null || true
  fi
  return "$status"
}
trap bootstrap_cleanup EXIT

verify_candidate_checkout() {
  local top status rel
  top="$(h06_repo_git "$ROOT" rev-parse --show-toplevel 2>/dev/null)" || die 'H06 must run from a committed Git worktree'
  [[ "$(cd "$top" && pwd -P)" == "$ROOT" ]] || die "candidate root mismatch: derived=$ROOT git=$top"
  CANDIDATE_HEAD="$(h06_repo_git "$ROOT" rev-parse --verify HEAD)"
  CANDIDATE_TREE="$(h06_repo_git "$ROOT" rev-parse --verify 'HEAD^{tree}')"
  require_full_oid candidate-head "$CANDIDATE_HEAD"; require_full_oid candidate-tree "$CANDIDATE_TREE"
  [[ -z "$H06_CANDIDATE_COMMIT" ]] || require_full_oid H06_CANDIDATE_COMMIT "$H06_CANDIDATE_COMMIT"
  [[ -z "$H06_CANDIDATE_TREE" ]] || require_full_oid H06_CANDIDATE_TREE "$H06_CANDIDATE_TREE"
  [[ -z "$H06_CANDIDATE_COMMIT" || "$CANDIDATE_HEAD" == "$H06_CANDIDATE_COMMIT" ]] || die "candidate commit mismatch expected=$H06_CANDIDATE_COMMIT actual=$CANDIDATE_HEAD"
  [[ -z "$H06_CANDIDATE_TREE" || "$CANDIDATE_TREE" == "$H06_CANDIDATE_TREE" ]] || die "candidate tree mismatch expected=$H06_CANDIDATE_TREE actual=$CANDIDATE_TREE"
  status="$(h06_repo_git "$ROOT" status --porcelain=v1 --untracked-files=all)"
  [[ -z "$status" ]] || die 'candidate worktree is not clean (tracked, staged, or untracked bytes present)'
  while IFS= read -r rel; do
    h06_repo_git "$ROOT" ls-files --error-unmatch -- "$rel" >/dev/null 2>&1 || die "candidate dependency is not tracked: $rel"
    require_physical_file "$ROOT/$rel"
    h06_repo_git "$ROOT" cat-file blob "HEAD:$rel" | cmp -s - "$ROOT/$rel" || die "candidate dependency bytes differ from HEAD: $rel"
  done <<'EOFCANDIDATE'
ops/release/tests/run-isolated-archive-pavilion-h06.sh
ops/release/tests/archive-pavilion-h06-browser.mjs
ops/release/tests/archive-pavilion-h06-lib.sh
ops/release/common.sh
ops/release/build-api.sh
ops/release/build-web.sh
ops/release/promote-release.sh
ops/release/verify-release.sh
ops/release/deploy-api.sh
ops/release/deploy-web.sh
ops/release/rollback-api.sh
ops/release/rollback-web.sh
specs/archive-pavilion-reader-mvp/content/source/shuihu_raw.txt
specs/archive-pavilion-reader-mvp/content/manifest.json
specs/archive-pavilion-reader-mvp/content/golden-summary.json
EOFCANDIDATE
}

bootstrap_digest() {
  python3 - "$1" "$2" "$3" <<'PYBOOT'
import hashlib,pathlib,re,sys
path,expected,kind=sys.argv[1:]; data=pathlib.Path(path).read_bytes()
if kind=='main':
 data=re.sub(rb'(?m)^H06_MAIN_CANONICAL_SHA256=[0-9a-f_]{64,}$',b'H06_MAIN_CANONICAL_SHA256='+b'0'*64,data)
actual=hashlib.sha256(data).hexdigest()
if actual!=expected: raise SystemExit(f'{kind} provenance mismatch expected={expected} actual={actual}')
PYBOOT
}
verify_candidate_checkout
bootstrap_digest "${BASH_SOURCE[0]}" "$H06_MAIN_CANONICAL_SHA256" main
bootstrap_digest "$BROWSER" "$H06_BROWSER_FILE_SHA256" browser
bootstrap_digest "$LIB" "$H06_LIB_FILE_SHA256" lib
if [[ "${H06_BOOTSTRAPPED:-0}" != 1 ]]; then
  BOOTSTRAP_DIR="$(mktemp -d /var/tmp/cyf-h06-bootstrap.XXXXXXXX)"
  chmod 0700 "$BOOTSTRAP_DIR"
  cp --no-preserve=ownership,mode,timestamps -- "${BASH_SOURCE[0]}" "$BOOTSTRAP_DIR/run-isolated-archive-pavilion-h06.sh"
  cp --no-preserve=ownership,mode,timestamps -- "$BROWSER" "$BOOTSTRAP_DIR/archive-pavilion-h06-browser.mjs"
  cp --no-preserve=ownership,mode,timestamps -- "$LIB" "$BOOTSTRAP_DIR/archive-pavilion-h06-lib.sh"
  chmod 0500 "$BOOTSTRAP_DIR/run-isolated-archive-pavilion-h06.sh"; chmod 0400 "$BOOTSTRAP_DIR/archive-pavilion-h06-browser.mjs" "$BOOTSTRAP_DIR/archive-pavilion-h06-lib.sh"
  bootstrap_digest "$BOOTSTRAP_DIR/run-isolated-archive-pavilion-h06.sh" "$H06_MAIN_CANONICAL_SHA256" main
  bootstrap_digest "$BOOTSTRAP_DIR/archive-pavilion-h06-browser.mjs" "$H06_BROWSER_FILE_SHA256" browser
  bootstrap_digest "$BOOTSTRAP_DIR/archive-pavilion-h06-lib.sh" "$H06_LIB_FILE_SHA256" lib
  exec env H06_BOOTSTRAPPED=1 H06_BOOTSTRAP_DIR="$BOOTSTRAP_DIR" H06_REPO_ROOT="$ROOT" H06_CANDIDATE_COMMIT="$CANDIDATE_HEAD" H06_CANDIDATE_TREE="$CANDIDATE_TREE" /bin/bash "$BOOTSTRAP_DIR/run-isolated-archive-pavilion-h06.sh" "${ORIGINAL_ARGS[@]}"
fi
BOOTSTRAP_DIR="${H06_BOOTSTRAP_DIR:?staged bootstrap directory missing}"

for command in bash env git python3 sha256sum stat find sort chmod chown date ss ps awk sed grep flock unshare ip mount curl tar unzip openssl node realpath readlink tac setpriv certutil cmp xargs head tail cp mktemp pgrep; do require_command "$command"; done
((EUID == 0)) || die 'non-dry H06 requires root for mount/network/PID namespaces'
acquire_heavy_resource_lock
pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 && blocked "dedicated H06 worker UID $H06_WORKER_UID is already in use"
require_physical_file "$BROWSER"
require_physical_file "$LIB"
# shellcheck source=archive-pavilion-h06-lib.sh
source "$LIB"
for trusted_name in bash env git python3 sha256sum stat find sort chmod chown date ss ps awk sed grep flock unshare ip mount curl tar unzip openssl node realpath readlink tac setpriv certutil cmp xargs head tail cp mktemp pgrep rm mkdir df sleep; do
  trusted_system="$(command -v "$trusted_name")"; resolved="$(readlink -f "$trusted_system")"; h06_assert_root_owned_chain "$resolved" "system executable $trusted_name"
done
h06_assert_root_owned_chain "$CHROME_PATH" 'Chromium executable'
h06_verify_sha256 "$CHROME_PATH" "$H06_CHROMIUM_EXEC_SHA256" 'Chromium executable'
[[ "$(h06_tree_digest /usr/lib64/chromium-browser)" == "$H06_CHROMIUM_TREE_SHA256" ]] || die 'Chromium trusted tree digest mismatch'

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$-$(python3 - <<'PY'
import secrets
print(secrets.token_hex(4))
PY
)"
FINAL_RUN="$EVIDENCE_ROOT/$RUN_ID"
RUN="$(h06_secure_create_run "$EVIDENCE_ROOT" "$RUN_ID" "$H06_WORKER_UID" "$H06_WORKER_GID")"
ROOT_RECORDS="$RUN/root-records"
ROOT_LOGS="$RUN/root-logs"
WORKER_OUTPUT="$RUN/worker-output"
WORKER_ARTIFACTS="$RUN/worker-output/build/artifacts"
mkdir -p "$RUN"/{config,mysql,runtime,browser,release,sandbox,artifacts,tmp,private,trusted/h06,worker/home} "$ROOT_RECORDS" "$ROOT_LOGS" "$WORKER_OUTPUT"
chown root:root "$ROOT_RECORDS" "$ROOT_LOGS" "$WORKER_OUTPUT" "$RUN/artifacts"
chmod 0700 "$ROOT_RECORDS" "$ROOT_LOGS" "$RUN/artifacts"; chmod 0711 "$WORKER_OUTPUT"
for output_stage in build mysql runtime release browser; do
  mkdir -p "$WORKER_OUTPUT/$output_stage/records" "$WORKER_OUTPUT/$output_stage/logs"
  [[ "$output_stage" != build ]] || mkdir -p "$WORKER_ARTIFACTS"
  chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$WORKER_OUTPUT/$output_stage"
  chmod 0700 "$WORKER_OUTPUT/$output_stage" "$WORKER_OUTPUT/$output_stage/records" "$WORKER_OUTPUT/$output_stage/logs"
done
cp --no-preserve=ownership,mode,timestamps -- "$BROWSER" "$RUN/trusted/h06/archive-pavilion-h06-browser.mjs"
cp --no-preserve=ownership,mode,timestamps -- "$LIB" "$RUN/trusted/h06/archive-pavilion-h06-lib.sh"
chmod 0444 "$RUN/trusted/h06/"*; chmod 0555 "$RUN/trusted" "$RUN/trusted/h06"
h06_verify_sha256 "$RUN/trusted/h06/archive-pavilion-h06-browser.mjs" "$H06_BROWSER_FILE_SHA256" 'evidence-staged browser'
h06_verify_sha256 "$RUN/trusted/h06/archive-pavilion-h06-lib.sh" "$H06_LIB_FILE_SHA256" 'evidence-staged library'
BROWSER="$RUN/trusted/h06/archive-pavilion-h06-browser.mjs"; LIB="$RUN/trusted/h06/archive-pavilion-h06-lib.sh"
EVIDENCE_MARKER="$EVIDENCE_ROOT/.cyf-h06-evidence-root.json"
[[ "$(stat -c '%U:%G %a' -- "$EVIDENCE_ROOT")" == 'root:root 711' ]] || die 'evidence root is not root:root mode 0711 after allocation'
[[ "$(stat -c '%U:%G %a' -- "$RUN")" == 'root:root 711' ]] || die 'temporary evidence run is not root:root mode 0711 after allocation'
[[ -f "$EVIDENCE_MARKER" && ! -L "$EVIDENCE_MARKER" && "$(stat -c '%U:%G %a' -- "$EVIDENCE_MARKER")" == 'root:root 444' ]] \
  || die 'evidence root marker is not one root:root mode 0444 physical file'
printf 'TEMP_RUN=%s\nFINAL_RUN=%s\nEVIDENCE_ROOT_OWNER_MODE=root:root_0711\nTEMP_RUN_OWNER_MODE=root:root_0711\nEVIDENCE_MARKER=%s\nEVIDENCE_MARKER_SHA256=%s\nWORKER_UID=%s\nWORKER_GID=%s\n' \
  "$RUN" "$FINAL_RUN" "$EVIDENCE_MARKER" "$(sha256sum "$EVIDENCE_MARKER" | awk '{print $1}')" "$H06_WORKER_UID" "$H06_WORKER_GID" > "$ROOT_RECORDS/evidence-allocation.txt"
printf 'PRODUCTION_DEPLOYMENT=NOT_PERFORMED\nPRODUCTION_DB_OPERATION=NOT_PERFORMED\n' > "$RUN/production-boundary.txt"
printf 'H06_RUN_ID=%s\nSTARTED_AT=%s\nSTAGE=%s\n' "$RUN_ID" "$(date -u +%FT%TZ)" "$STAGE" > "$RUN/run.txt"
printf 'CANDIDATE_HEAD=%s\nCANDIDATE_TREE=%s\nCANDIDATE_STATUS=CLEAN\nCANDIDATE_COMMIT_PIN=%s\nCANDIDATE_TREE_PIN=%s\n' "$CANDIDATE_HEAD" "$CANDIDATE_TREE" "${H06_CANDIDATE_COMMIT:-NOT_SUPPLIED}" "${H06_CANDIDATE_TREE:-NOT_SUPPLIED}" > "$ROOT_RECORDS/candidate-provenance.txt"

capture_host_state() {
  local suffix="$1"
  python3 - /home/isp/hosts/cyf/api/cyf-api-kit.pid /home/isp/apps/jdk21/bin/java /home/isp/hosts/cyf/api/cyf-api-kit.jar <<'PYPID' > "$ROOT_RECORDS/production-$suffix.txt"
import hashlib,os,pathlib,stat,sys
pidfile,expected_java,kit_jar=map(pathlib.Path,sys.argv[1:]); print('PRODUCTION_PID_FILE='+str(pidfile))
try: pst=os.lstat(str(pidfile))
except FileNotFoundError: print('PRODUCTION_PIDFILE_PHYSICAL=ABSENT'); print('PRODUCTION_STATE=ABSENT'); raise SystemExit
if stat.S_ISLNK(pst.st_mode) or not stat.S_ISREG(pst.st_mode): print('PRODUCTION_PIDFILE_PHYSICAL=FAIL'); print('PRODUCTION_STATE=FOREIGN'); raise SystemExit
print('PRODUCTION_PIDFILE_PHYSICAL=PASS')
raw=pidfile.read_bytes(); print('PRODUCTION_PIDFILE_VALUE_SHA256='+hashlib.sha256(raw).hexdigest())
try: pid=int(raw.decode().strip())
except Exception: print('PRODUCTION_STATE=STALE'); raise SystemExit
proc=pathlib.Path('/proc')/str(pid)
if not (proc/'stat').is_file(): print('PRODUCTION_STATE=STALE'); print('PRODUCTION_PID='+str(pid)); raise SystemExit
statline=(proc/'stat').read_text(); end=statline.rfind(')'); start=statline[end+2:].split()[19]
exe=os.path.realpath(str(proc/'exe')); cmdraw=(proc/'cmdline').read_bytes(); argv=[item.decode('utf-8','surrogateescape') for item in cmdraw.split(b'\0') if item]
expected_exe=os.path.realpath(str(expected_java)); expected_jar=os.path.realpath(str(kit_jar))
jar_bound=any(os.path.realpath(arg)==expected_jar for arg in argv if arg.startswith('/'))
state='LIVE' if exe==expected_exe and jar_bound and kit_jar.is_file() and not kit_jar.is_symlink() else 'FOREIGN'
print('PRODUCTION_STATE='+state); print('PRODUCTION_PID='+str(pid)); print('PRODUCTION_START_TICKS='+start); print('PRODUCTION_EXE='+exe)
print('PRODUCTION_EXPECTED_EXE='+expected_exe); print('PRODUCTION_EXPECTED_JAR='+expected_jar); print('PRODUCTION_CMDLINE_KIT_JAR_BOUND='+('PASS' if jar_bound else 'FAIL'))
print('PRODUCTION_CMDLINE_SHA256='+hashlib.sha256(cmdraw).hexdigest())
if kit_jar.is_file() and not kit_jar.is_symlink(): print('PRODUCTION_JAR_SHA256='+hashlib.sha256(kit_jar.read_bytes()).hexdigest())
PYPID
  printf 'CAPTURED_AT=%s\n' "$(date -u +%FT%TZ)" >> "$ROOT_RECORDS/production-$suffix.txt"
  ss -lntp > "$ROOT_RECORDS/listeners-$suffix.txt"
  ps -eo pid=,ppid=,uid=,stat=,comm= > "$ROOT_RECORDS/processes-$suffix.txt"
  { awk '/^MemAvailable:|^SwapFree:/ {print}' /proc/meminfo; df -PB1 -- "$ROOT" "$EVIDENCE_ROOT"; } > "$ROOT_RECORDS/resources-$suffix.txt"
}

terminate_dedicated_worker_uid() {
  local -a pids=() pid
  mapfile -t pids < <(pgrep -u "$H06_WORKER_UID" 2>/dev/null || true)
  ((${#pids[@]} == 0)) && return 0
  for pid in "${pids[@]}"; do [[ "$pid" =~ ^[0-9]+$ ]] && kill -TERM "$pid" 2>/dev/null || true; done
  for _ in {1..50}; do pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 || return 0; sleep 0.1; done
  mapfile -t pids < <(pgrep -u "$H06_WORKER_UID" 2>/dev/null || true)
  for pid in "${pids[@]}"; do [[ "$pid" =~ ^[0-9]+$ ]] && kill -KILL "$pid" 2>/dev/null || true; done
  for _ in {1..20}; do pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 || return 0; sleep 0.1; done
  return 1
}

import_all_worker_output() {
  local stage
  pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 && { echo "worker UID still active before evidence import" >&2; return 1; }
  : > "$ROOT_RECORDS/worker-output-import.txt"
  for stage in build mysql runtime release browser; do
    [[ -d "$WORKER_OUTPUT/$stage/records" && ! -L "$WORKER_OUTPUT/$stage/records" ]] || return 1
    [[ -d "$WORKER_OUTPUT/$stage/logs" && ! -L "$WORKER_OUTPUT/$stage/logs" ]] || return 1
    h06_import_worker_output "$WORKER_OUTPUT/$stage/records" "$ROOT_RECORDS/$stage" "$H06_WORKER_UID" "$H06_WORKER_GID" >> "$ROOT_RECORDS/worker-output-import.txt" || return 1
    h06_import_worker_output "$WORKER_OUTPUT/$stage/logs" "$ROOT_LOGS/$stage" "$H06_WORKER_UID" "$H06_WORKER_GID" >> "$ROOT_RECORDS/worker-output-import.txt" || return 1
  done
  printf 'WORKER_UID_QUIESCENT_BEFORE_IMPORT=PASS\nWORKER_OUTPUT_NOFOLLOW_IMPORT=PASS\nWORKER_OUTPUT_SPECIAL_HARDLINK_REJECTION=ENFORCED\n' >> "$ROOT_RECORDS/worker-output-import.txt"
}

finalize() {
  local status=$? finalization_ok=1 requested_result="$RESULT" requested_detail="$RESULT_DETAIL"
  ((FINALIZED == 0)) || return "$status"
  FINALIZED=1; trap - ERR; set +e
  # Failure and success finalization both quiesce the dedicated worker, remove
  # every non-evidence worker-writable directory, import output no-follow, and
  # remove the output staging tree before any remaining final root record write.
  local worker_quiescent=1 worker_path
  find "$RUN" -xdev -type f -name '*pids.tsv' -print0 2>/dev/null | while IFS= read -r -d '' registry; do h06_stop_tracked_pids "$registry" || exit 1; done || { finalization_ok=0; worker_quiescent=0; }
  terminate_dedicated_worker_uid || { finalization_ok=0; worker_quiescent=0; }
  pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 && { finalization_ok=0; worker_quiescent=0; }
  for worker_path in "$RUN/private" "$RUN/tmp" "$RUN/mysql" "$RUN/runtime" "$RUN/browser" "$RUN/release" "$RUN/sandbox" "$RUN/worker"; do
    h06_safe_remove_run_local "$RUN" "$worker_path" || finalization_ok=0
  done
  if ((worker_quiescent)); then import_all_worker_output || finalization_ok=0; fi
  h06_safe_remove_run_local "$RUN" "$RUN/worker-output" || finalization_ok=0
  capture_host_state after || finalization_ok=0
  python3 - "$ROOT_RECORDS/production-before.txt" "$ROOT_RECORDS/production-after.txt" > "$ROOT_RECORDS/production-identity-check.txt" <<'PYIDENT'
import sys
def read(path):
 d={}
 for line in open(path,encoding='utf-8'):
  if '=' in line:
   k,v=line.rstrip().split('=',1); d[k]=v
 return d
b,a=map(read,sys.argv[1:]); bs=b.get('PRODUCTION_STATE','UNKNOWN'); ass=a.get('PRODUCTION_STATE','UNKNOWN')
print('PRODUCTION_STATE_BEFORE='+bs); print('PRODUCTION_STATE_AFTER='+ass)
if bs!=ass: print('PRODUCTION_STATE_STABLE=FAIL'); raise SystemExit(1)
if bs=='LIVE':
 keys=['PRODUCTION_PID','PRODUCTION_START_TICKS','PRODUCTION_EXE','PRODUCTION_CMDLINE_SHA256','PRODUCTION_JAR_SHA256']; changed=[k for k in keys if b.get(k)!=a.get(k)]
 print('PRODUCTION_LIVE_IDENTITY_UNCHANGED='+('PASS' if not changed else 'FAIL')); print('CHANGED_KEYS='+','.join(changed))
 if changed: raise SystemExit(1)
elif bs in ('ABSENT','STALE','FOREIGN'):
 keys=['PRODUCTION_PIDFILE_PHYSICAL','PRODUCTION_PIDFILE_VALUE_SHA256','PRODUCTION_PID','PRODUCTION_START_TICKS','PRODUCTION_EXE','PRODUCTION_CMDLINE_SHA256','PRODUCTION_CMDLINE_KIT_JAR_BOUND']; changed=[k for k in keys if b.get(k)!=a.get(k)]
 print('PRODUCTION_STATE_STABLE='+('PASS' if not changed else 'FAIL')); print('PRODUCTION_LIVE_IDENTITY_UNCHANGED=NOT_APPLICABLE'); print('CHANGED_KEYS='+','.join(changed))
 if changed: raise SystemExit(1)
else: raise SystemExit(1)
PYIDENT
  [[ $? -eq 0 ]] || { finalization_ok=0; requested_result=FAIL; requested_detail='production API state/identity changed during isolated gate'; }
  grep -E ':(10018|3306|33060)\b' "$ROOT_RECORDS/listeners-before.txt" > "$ROOT_RECORDS/production-listeners-before.txt" || true
  grep -E ':(10018|3306|33060)\b' "$ROOT_RECORDS/listeners-after.txt" > "$ROOT_RECORDS/production-listeners-after.txt" || true
  cmp -s "$ROOT_RECORDS/production-listeners-before.txt" "$ROOT_RECORDS/production-listeners-after.txt" || { finalization_ok=0; requested_result=FAIL; requested_detail='production listeners changed during isolated gate'; }

  # Trusted staged executables are no longer needed; worker-writable paths were
  # already removed before the post-run host-state evidence was written.
  h06_safe_remove_run_local "$RUN" "$RUN/trusted" || finalization_ok=0
  find "$RUN" -xdev -type f \( -iname '*.jwt' -o -iname '*.key' -o -iname '*.pem' -o -iname '*secret*' -o -iname '*password*' -o -name 'isolated.properties' -o -name 'h06*.properties' \) -delete 2>/dev/null || finalization_ok=0
  find "$RUN" -xdev -type d \( -name 'chromium-profile' -o -name 'chrome-profile' \) -prune -exec rm -rf --one-file-system -- {} + 2>/dev/null || finalization_ok=0
  if find "$RUN" -xdev \( -type l -o -type p -o -type s -o -type b -o -type c \) -print -quit | grep -q .; then finalization_ok=0; fi
  h06_reject_special_files "$RUN" > "$ROOT_RECORDS/evidence-object-scan.txt" || finalization_ok=0
  python3 - "$RUN" <<'PYSCAN' > "$ROOT_RECORDS/sensitive-scan.txt"
import pathlib,re,sys
root=pathlib.Path(sys.argv[1]); findings=[]
patterns=[
 re.compile(rb'-----BEGIN [^-\r\n]*PRIVATE KEY-----',re.I), re.compile(rb'(?im)^(?:authorization|proxy-authorization|cookie|set-cookie)\s*:'),
 re.compile(rb'\bBearer\s+[A-Za-z0-9._~+/-]{12,}',re.I), re.compile(rb'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}'),
 re.compile(rb'(?i)(?:access[_-]?token|refresh[_-]?token|client[_-]?secret|api[_-]?key|private[_-]?key)\s*[=:]\s*["\x27]?(?!\[REDACTED\]|NOT_PERFORMED|unused)([^\s"\x27]{4,})'),
 re.compile(rb'(?i)(?:password|secret)\s*[=:]\s*["\x27]?(?!\[REDACTED\]|NOT_PERFORMED|unused)([^\s"\x27]{4,})')]
for p in root.rglob('*'):
 if not p.is_file() or p.name=='MANIFEST.sha256': continue
 try: data=p.read_bytes()
 except OSError as e: findings.append(f'{p.relative_to(root)}:unreadable:{e}'); continue
 if any(rx.search(data) for rx in patterns): findings.append(str(p.relative_to(root)))
print('SENSITIVE_PAYLOAD_SCAN='+('PASS' if not findings else 'FAIL'))
for item in findings: print(item)
if findings: raise SystemExit(1)
PYSCAN
  [[ $? -eq 0 ]] || finalization_ok=0
  if ((finalization_ok)); then
    printf 'SECRETS_REMOVED_BEFORE_SEAL=PASS\nTLS_PRIVATE_KEY_RETAINED=NO\nBEARER_TOKEN_RETAINED=NO\nPRIVATE_CONFIG_RETAINED=NO\n' > "$ROOT_RECORDS/secret-cleanup.txt"
  else
    requested_result=FAIL; requested_detail='evidence cleanup/revocation/secret scan failed'; rm -f "$RUN/gate-pass.txt" "$ROOT_RECORDS/secret-cleanup.txt"
  fi
  [[ "$requested_result" == BLOCKED && $status -eq 3 ]] || [[ "$requested_result" != FAIL ]] || status=2
  printf 'RESULT=%s\nDETAIL=%s\nPRODUCTION_DEPLOYMENT=NOT_PERFORMED\nPRODUCTION_DB_OPERATION=NOT_PERFORMED\nFINISHED_AT=%s\n' "$requested_result" "$requested_detail" "$(date -u +%FT%TZ)" > "$RUN/result.txt"

  if ((finalization_ok)); then
    (cd "$RUN" && find . -type f ! -name MANIFEST.sha256 -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > MANIFEST.sha256 && sha256sum -c MANIFEST.sha256 >/dev/null) || finalization_ok=0
    find "$RUN" -type f -exec chmod 0444 {} + || finalization_ok=0
    find "$RUN" -type d -exec chmod 0555 {} + || finalization_ok=0
    find "$RUN" -type f ! -perm 0444 -print -quit | grep -q . && finalization_ok=0
    (cd "$RUN" && sha256sum -c MANIFEST.sha256 >/dev/null) || finalization_ok=0
  fi
  if ((finalization_ok)); then
    h06_secure_publish_run "$EVIDENCE_ROOT" "$RUN" "$FINAL_RUN" || finalization_ok=0
  fi
  if ((finalization_ok)); then
    RUN="$FINAL_RUN"; RESULT="$requested_result"; RESULT_DETAIL="$requested_detail"
    printf 'H06_RESULT=%s EVIDENCE=%s\n' "$RESULT" "$RUN" >&2
    rm -rf --one-file-system -- "$BOOTSTRAP_DIR" 2>/dev/null || true
    return "$status"
  fi
  RESULT=FAIL; RESULT_DETAIL='evidence finalization failed; no successful evidence was published'; status=2
  chmod -R u+w "$RUN" 2>/dev/null || true; rm -f "$RUN/gate-pass.txt" 2>/dev/null || true
  printf 'RESULT=FAIL\nDETAIL=evidence finalization failed; no successful evidence was published\nPRODUCTION_DEPLOYMENT=NOT_PERFORMED\nPRODUCTION_DB_OPERATION=NOT_PERFORMED\n' > "$RUN/result.txt" 2>/dev/null || true
  printf 'H06_RESULT=FAIL UNPUBLISHED_EVIDENCE=%s\n' "$RUN" >&2
  rm -rf --one-file-system -- "$BOOTSTRAP_DIR" 2>/dev/null || true
  return "$status"
}

trap finalize EXIT
on_error() {
  local code=$? line="$1" command="$2"
  if [[ "$RESULT" != BLOCKED ]]; then RESULT=FAIL; RESULT_DETAIL="command failed (status=$code line=$line): $command"; fi
  return "$code"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR
capture_host_state before

API_STAGED="$RUN/worker/api"
WEB_STAGED="$RUN/worker/web"
H06_RELEASE_ROOT="$RUN/trusted/release"

stage_release_tools() {
  mkdir -p "$H06_RELEASE_ROOT"
  while IFS=$'\t' read -r name expected; do
    local src="$ROOT/ops/release/$name" dst="$H06_RELEASE_ROOT/$name"
    require_physical_file "$src"; h06_verify_sha256 "$src" "$expected" "release tool $name" || die "release tool provenance mismatch: $name"
    cp --no-preserve=ownership,mode,timestamps -- "$src" "$dst"; chmod 0555 "$dst"
    h06_verify_sha256 "$dst" "$expected" "staged release tool $name" || die "staged release tool changed: $name"
  done <<'EOFTOOLS'
common.sh	c4c44b6f56e41103083ad6649c5ada73a8df49d6241aa830e1270da99552740f
build-api.sh	f52f5266b3fbc2f96c422cdfffaf9385d108ab0cc558735377a9a0d9f9b803f1
build-web.sh	b3425830fa96fc4f393dd56f476b75f83315c18da7e640923f14bf1b592339b0
promote-release.sh	34eef5bb8836083f6ddcb958d4b7661eef7c32a05cdf80b86ae3137a8a0d3c2b
verify-release.sh	4758da19f345d1bf2ce6ddec4370fa28bd21fa05051c6980de5e206eaf3da918
deploy-api.sh	e6af6b70d4b4dd1771ec322fc8671e8f115de4944dbda14a51a0045e20ac3488
deploy-web.sh	26307057d0adfd3f92f56e15f1c83c6d5014186090e4eb8329ced61a34199b1b
rollback-api.sh	9f47c893102dd23418e3abb322822db497185975e3c142200d93d9f0a8b6c720
rollback-web.sh	13ca5bf7a495e885f311df06ba18e4403e83fe90a86ae2e1e702e423ddd0bbea
EOFTOOLS
  find "$H06_RELEASE_ROOT" -type d -exec chmod 0555 {} +
  (cd "$ROOT" && sha256sum ops/release/tests/run-isolated-archive-pavilion-h06.sh ops/release/tests/archive-pavilion-h06-browser.mjs ops/release/tests/archive-pavilion-h06-lib.sh ops/release/common.sh ops/release/build-api.sh ops/release/build-web.sh ops/release/promote-release.sh ops/release/verify-release.sh ops/release/deploy-api.sh ops/release/deploy-web.sh ops/release/rollback-api.sh ops/release/rollback-web.sh specs/archive-pavilion-reader-mvp/content/source/shuihu_raw.txt specs/archive-pavilion-reader-mvp/content/manifest.json specs/archive-pavilion-reader-mvp/content/golden-summary.json) > "$ROOT_RECORDS/candidate-release-dependency-digests.txt"
}

stage_pinned_worktrees() {
  [[ ! -e "$API_STAGED" && ! -L "$API_STAGED" && ! -e "$WEB_STAGED" && ! -L "$WEB_STAGED" ]] || die 'staged worktree path already exists'
  mkdir -p "$RUN/worker" "$WORKER_ARTIFACTS"
  git clone --quiet --no-hardlinks --no-checkout "$API_WORKTREE" "$API_STAGED"
  h06_repo_git "$API_STAGED" checkout --quiet -B "$API_REF" "$API_HEAD"
  git clone --quiet --no-hardlinks --no-checkout "$WEB_WORKTREE" "$WEB_STAGED"
  h06_repo_git "$WEB_STAGED" checkout --quiet -B "$WEB_REF" "$WEB_HEAD"
  assert_candidate STAGED_API "$API_STAGED" "$API_REF" "$API_HEAD" "$API_TREE" "$ROOT_RECORDS/staged-api-pin.txt"
  assert_candidate STAGED_WEB "$WEB_STAGED" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$ROOT_RECORDS/staged-web-pin.txt"
  h06_verify_sha256 "$API_STAGED/gradlew" fb3cbfe6d066ee52bc07f62ed61ff77bde195384f52496c94280a83008d9f531 "pinned Gradle wrapper script" || die "Gradle wrapper provenance mismatch"
  h06_verify_sha256 "$API_STAGED/gradle/wrapper/gradle-wrapper.jar" ed2c26eba7cfb93cc2b7785d05e534f07b5b48b5e7fc941921cd098628abca58 "pinned Gradle wrapper JAR" || die "Gradle wrapper JAR provenance mismatch"
  h06_verify_sha256 "$API_STAGED/gradle/wrapper/gradle-wrapper.properties" cb2a8c71fb56cfa3ae90c6b4109879de6e7df27831fcc1ed04db55f6d74ca110 "pinned Gradle wrapper properties" || die "Gradle wrapper properties provenance mismatch"
  chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$RUN/worker"
  chmod 0711 "$RUN/worker"
  chmod 0700 "$API_STAGED" "$WEB_STAGED" "$RUN/worker/home"
  stage_release_tools
}

stage_gradle_cache_snapshot() {
  local source_root=/root/.gradle destination="$RUN/worker/gradle-home"
  local record="$ROOT_RECORDS/gradle-cache-snapshot.json" paths="$ROOT_RECORDS/gradle-cache-snapshot-paths.txt"
  local wrapper_properties="$API_STAGED/gradle/wrapper/gradle-wrapper.properties"
  [[ ! -e "$destination" && ! -L "$destination" ]] || die "fresh Gradle home path already exists: $destination"
  require_physical_file "$wrapper_properties"
  /usr/bin/flock -w 600 -x "$GRADLE_LOCK" /usr/bin/python3 - "$source_root" "$destination" "$record" "$paths" "$wrapper_properties" "$H06_WORKER_UID" "$H06_WORKER_GID" "$H06_GRADLE_ALLOWLIST_SHA256" <<'PYGRADLE'
import hashlib,json,os,pathlib,re,shutil,stat,sys
source_root,destination,record,path_record,wrapper_properties=map(pathlib.Path,sys.argv[1:6]); uid=int(sys.argv[6]); gid=int(sys.argv[7]); expected_allowlist=sys.argv[8]
if not re.fullmatch(r'[0-9a-f]{64}',expected_allowlist): raise SystemExit('candidate Gradle allowlist SHA-256 pin is invalid')
expected_properties_sha='cb2a8c71fb56cfa3ae90c6b4109879de6e7df27831fcc1ed04db55f6d74ca110'
expected_url=r'distributionUrl=https\://mirrors.cloud.tencent.com/gradle/gradle-9.3.1-bin.zip'
dist_base='wrapper/dists/gradle-9.3.1-bin/e6fpmcitnr2cbhj7h6pdk7btv'
allowlist=[dist_base+'/gradle-9.3.1',dist_base+'/gradle-9.3.1-bin.zip.ok','caches/modules-2/files-2.1']
excluded=['daemon','workers','notifications','registry','locks','journal','tmp','caches/build-cache-*','caches/*/fileHashes','caches/*/fileChanges','caches/*/executionHistory','caches/modules-2/metadata-*','caches/modules-2/modules-2.lock',dist_base+'/gradle-9.3.1-bin.zip.lck']
def file_hash(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''): h.update(block)
 return h.hexdigest()
def safe_nodes(base,rel,require_root_owner=True):
 root=base/rel
 try: first=os.lstat(root)
 except FileNotFoundError: raise SystemExit('Gradle snapshot allowlist input missing: '+str(root))
 def visit(path,marker):
  st=os.lstat(path)
  if stat.S_ISLNK(st.st_mode): raise SystemExit('symlink forbidden in Gradle snapshot: '+str(path))
  if require_root_owner and (st.st_uid!=0 or st.st_mode&0o022): raise SystemExit('Gradle snapshot source must be root-owned and non-group/world-writable: '+str(path))
  if stat.S_ISDIR(st.st_mode):
   yield path,marker,st
   with os.scandir(path) as scan: entries=sorted(list(scan),key=lambda e:e.name.encode())
   for entry in entries: yield from visit(pathlib.Path(entry.path),marker+'/'+entry.name)
  elif stat.S_ISREG(st.st_mode): yield path,marker,st
  else: raise SystemExit('special object forbidden in Gradle snapshot: '+str(path))
 yield from visit(root,rel)
def digest(base,paths,require_root_owner=True):
 combined=hashlib.sha256(); details=[]
 for rel in paths:
  one=hashlib.sha256(); files=0; size=0
  for path,marker,st in safe_nodes(base,rel,require_root_owner):
   encoded=marker.encode()
   if stat.S_ISDIR(st.st_mode): one.update(b'D\0'+encoded+b'\0')
   else:
    content=file_hash(path); one.update(b'F\0'+encoded+b'\0'+content.encode()+b'\0'); files+=1; size+=st.st_size
  value=one.hexdigest(); combined.update(rel.encode()+b'\0'+value.encode()+b'\0')
  details.append({'path':rel,'sha256':value,'regularFiles':files,'bytes':size})
 return combined.hexdigest(),details
def copy_node(source,target):
 st=os.lstat(source)
 if stat.S_ISLNK(st.st_mode): raise SystemExit('symlink appeared during Gradle snapshot: '+str(source))
 if stat.S_ISDIR(st.st_mode):
  target.mkdir(mode=0o700)
  with os.scandir(source) as scan: entries=sorted(list(scan),key=lambda e:e.name.encode())
  for entry in entries: copy_node(pathlib.Path(entry.path),target/entry.name)
 elif stat.S_ISREG(st.st_mode):
  target.parent.mkdir(mode=0o700,parents=True,exist_ok=True); shutil.copyfile(source,target)
  target.chmod(0o700 if st.st_mode & 0o111 else 0o600)
 else: raise SystemExit('special object appeared during Gradle snapshot: '+str(source))
def enforce_owner(path):
 st=os.lstat(path)
 if stat.S_ISLNK(st.st_mode): raise SystemExit('staged Gradle symlink forbidden: '+str(path))
 os.chown(path,uid,gid)
 if stat.S_ISDIR(st.st_mode):
  os.chmod(path,0o700)
  with os.scandir(path) as scan:
   for entry in scan: enforce_owner(pathlib.Path(entry.path))
 elif stat.S_ISREG(st.st_mode): os.chmod(path,0o700 if st.st_mode & 0o111 else 0o600)
 else: raise SystemExit('staged Gradle special object forbidden: '+str(path))
def assert_secure_directory_chain(path,label):
 path=path.absolute()
 while True:
  st=os.lstat(path)
  if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode): raise SystemExit(label+' directory chain is not physical: '+str(path))
  if st.st_uid!=0 or st.st_mode&0o022: raise SystemExit(label+' directory chain is not root-owned/non-writable: '+str(path))
  if path==path.parent: break
  path=path.parent
assert_secure_directory_chain(source_root,'Gradle cache root')
for rel in allowlist: assert_secure_directory_chain((source_root/rel).parent,'Gradle allowlist parent')
properties=wrapper_properties.read_bytes()
if hashlib.sha256(properties).hexdigest()!=expected_properties_sha: raise SystemExit('pinned Gradle wrapper properties digest mismatch during snapshot')
lines=properties.decode('utf-8').splitlines()
if expected_url not in lines: raise SystemExit('Gradle wrapper URL/version is not exact 9.3.1 frozen value')
if any(line.startswith('distributionSha256Sum=') for line in lines): raise SystemExit('unexpected Gradle wrapper distribution checksum policy change')
if destination.exists() or destination.is_symlink(): raise SystemExit('Gradle home is not fresh: '+str(destination))
before,before_details=digest(source_root,allowlist)
if before!=expected_allowlist: raise SystemExit('Gradle source allowlist digest mismatch expected='+expected_allowlist+' actual='+before)
destination.mkdir(mode=0o700,parents=False)
for rel in allowlist:
 target=destination/rel; target.parent.mkdir(mode=0o700,parents=True,exist_ok=True); copy_node(source_root/rel,target)
staged,staged_details=digest(destination,allowlist)
after,after_details=digest(source_root,allowlist)
if not (before==staged==after==expected_allowlist): raise SystemExit('Gradle allowlist source-before/staged/source-after/candidate-pin digest mismatch')
if before_details!=staged_details or before_details!=after_details: raise SystemExit('Gradle allowlist per-path digest/count mismatch')
dist=destination/dist_base/'gradle-9.3.1'
for rel in ('bin/gradle','lib/gradle-core-9.3.1.jar','lib/gradle-launcher-9.3.1.jar','lib/gradle-wrapper-shared-9.3.1.jar'):
 p=dist/rel
 if p.is_symlink() or not p.is_file(): raise SystemExit('Gradle 9.3.1 distribution structure missing: '+rel)
ok=destination/(dist_base+'/gradle-9.3.1-bin.zip.ok')
if ok.is_symlink() or not ok.is_file() or ok.stat().st_size!=0: raise SystemExit('Gradle wrapper .zip.ok marker is not the expected empty physical file')
for forbidden in ('daemon','workers','notifications','registry','caches/9.3.1/fileHashes','caches/9.3.1/fileChanges','caches/9.3.1/executionHistory'):
 if (destination/forbidden).exists() or (destination/forbidden).is_symlink(): raise SystemExit('mutable Gradle state was copied: '+forbidden)
enforce_owner(destination)
owned,owned_details=digest(destination,allowlist,require_root_owner=False)
if owned!=expected_allowlist or owned_details!=before_details: raise SystemExit('Gradle staged bytes changed while assigning UID61006 ownership')
path_record.write_text('GRADLE_SOURCE_WHOLE_TREE_EXPECTED_DIGEST=NOT_USED\nGRADLE_ALLOWLIST_CANDIDATE_PIN='+expected_allowlist+'\nGRADLE_USER_HOME_FRESH='+str(destination)+'\nLOCK=/tmp/cyf-gradle.lock\n' + ''.join('ALLOWLIST='+x+'\n' for x in allowlist) + ''.join('EXCLUDED='+x+'\n' for x in excluded),encoding='utf-8')
record.write_text(json.dumps({'schema':'cyf-h06-gradle-cache-snapshot-v1','result':'PASS','lock':'/tmp/cyf-gradle.lock','source':str(source_root),'destination':str(destination),'wholeSourceTreeDigest':'NOT_COMPUTED_OR_PINNED','candidateAllowlistSha256':expected_allowlist,'wrapper':{'propertiesSha256':expected_properties_sha,'distributionUrl':'https://mirrors.cloud.tencent.com/gradle/gradle-9.3.1-bin.zip','version':'9.3.1','distributionDirectory':dist_base+'/gradle-9.3.1'},'allowlist':before_details,'excludedMutableState':excluded,'sourceBeforeSha256':before,'stagedSha256':staged,'sourceAfterSha256':after,'ownedStagedSha256':owned,'workerUid':uid,'workerGid':gid},sort_keys=True,indent=2)+'\n',encoding='utf-8')
PYGRADLE
  [[ -d "$destination" && ! -L "$destination" ]] || die 'fresh staged Gradle home was not created'
}

stage_runtime_inventory() {
  mkdir -p "$RUN/trusted/runtime"
  python3 - "$RUN/trusted/runtime" "$ROOT_RECORDS/candidate-runtime-inventory.json" <<'PYINV'
import hashlib,json,os,pathlib,shutil,stat,sys
outroot,out=map(pathlib.Path,sys.argv[1:])
# Versioned constants in the committed H06 candidate are the runtime trust policy.
# No external inventory file is read or accepted.
specs={
 'mysql':{'expected':'1ef280fefaf25753aa5c8b2fad296dac8fae70b4bcbee3ceefdaafd29880ed8a','root':'/home/isp/apps/mysql','paths':['bin/mysqld','bin/mysql','bin/mysqladmin','lib/private','lib/plugin','share']},
 'redis':{'expected':'7982368f77fb0b3e8355061a92672ffadbf45e36bf2e8f7d7568106a7bcf73a4','root':'/home/isp/apps/redis','paths':['bin/redis-server','bin/redis-cli']},
 'jdk':{'expected':'824410ab7c2c3a2aed326fb89627dcc00cc42d70428df1c257df803c6e90eef5','root':'/home/isp/apps/jdk21','paths':['bin/java','bin/javac','bin/jar','lib','conf','release']},
 'node':{'expected':'0dad332849ea92d40607b1cfff0a36e3f1da4d0bfc50e86ec97c1e4bfd337b7c','root':'/home/isp/apps/node','paths':['bin/node','lib/node_modules/npm']},
 'nginx':{'expected':'8d24dddd0ebd63fac8de77a1edac966e02c1713b121dcf5c284979df273017f1','root':'/home/isp/apps/nginx','paths':['sbin/nginx','conf/mime.types']}}
def file_hash(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  while True:
   block=stream.read(8*1024*1024)
   if not block: break
   h.update(block)
 return h.hexdigest()
def inventory_items(name,root,paths):
 items=[]
 for rel in paths:
  source=root if rel=='.' else root/rel
  marker=name if rel=='.' else name+'/'+rel
  try: st=os.lstat(str(source))
  except FileNotFoundError: raise SystemExit('candidate-pinned runtime input missing: '+str(source))
  items.append((source,marker))
  if stat.S_ISDIR(st.st_mode):
   for child in source.rglob('*'): items.append((child,marker+'/'+child.relative_to(source).as_posix()))
 return sorted(items,key=lambda item:item[1].encode())
def digest(name,root,paths):
 h=hashlib.sha256(); files=0; size=0
 for path,marker in inventory_items(name,root,paths):
  st=os.lstat(str(path)); rel=marker.encode()
  if stat.S_ISLNK(st.st_mode): h.update(b'L\0'+rel+b'\0'+os.readlink(str(path)).encode()+b'\0')
  elif stat.S_ISDIR(st.st_mode): h.update(b'D\0'+rel+b'\0')
  elif stat.S_ISREG(st.st_mode):
   h.update(b'F\0'+rel+b'\0'+file_hash(path).encode()+b'\0'); files+=1; size+=st.st_size
  else: raise SystemExit('special runtime object forbidden: '+str(path))
 return h.hexdigest(),files,size
def copy_one(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 st=os.lstat(str(source))
 if stat.S_ISDIR(st.st_mode): shutil.copytree(str(source),str(target),symlinks=True)
 elif stat.S_ISLNK(st.st_mode): os.symlink(os.readlink(str(source)),str(target))
 elif stat.S_ISREG(st.st_mode): shutil.copy2(str(source),str(target),follow_symlinks=False)
 else: raise SystemExit('special runtime source forbidden: '+str(source))
summary=[]
for name in sorted(specs):
 spec=specs[name]; root=pathlib.Path(spec['root']); paths=spec['paths']; expected=spec['expected']
 if root.is_symlink() or not root.is_dir(): raise SystemExit('runtime source root unavailable/linked: '+str(root))
 before,files,size=digest(name,root,paths)
 if before!=expected: raise SystemExit('%s source digest mismatch expected=%s actual=%s'%(name,expected,before))
 target=outroot/name
 if paths==['.']: copy_one(root,target)
 else:
  target.mkdir(parents=True)
  for rel in paths: copy_one(root/rel,target/rel)
 copied,copy_files,copy_size=digest(name,target,paths)
 after,_,_=digest(name,root,paths)
 if copied!=expected or after!=expected or (copy_files,copy_size)!=(files,size): raise SystemExit('%s pre/copy/post digest mismatch'%name)
 for path in sorted(target.rglob('*'),reverse=True):
  if path.is_symlink(): continue
  st=os.lstat(str(path))
  if stat.S_ISDIR(st.st_mode): path.chmod(0o555)
  elif stat.S_ISREG(st.st_mode): path.chmod(0o555 if st.st_mode&0o111 else 0o444)
 target.chmod(0o555)
 summary.append({'name':name,'source':str(root),'expectedDigest':expected,'sourceBefore':before,'staged':copied,'sourceAfter':after,'regularFiles':files,'bytes':size})
out.write_text(json.dumps({'schema':'cyf-h06-candidate-runtime-constants-v1','result':'PASS','components':summary},sort_keys=True,indent=2)+'\n')
PYINV
  # Chromium is staged as a complete tree because its runtime resources are path-relative.
  [[ "$(h06_tree_digest /usr/lib64/chromium-browser)" == "$H06_CHROMIUM_TREE_SHA256" ]] || blocked 'candidate-pinned Chromium source tree digest mismatch'
  cp -a --no-preserve=ownership -- /usr/lib64/chromium-browser "$RUN/trusted/runtime/chromium"
  [[ "$(h06_tree_digest "$RUN/trusted/runtime/chromium")" == "$H06_CHROMIUM_TREE_SHA256" ]] || die 'staged Chromium tree digest mismatch'
  python3 - /usr/lib64/chromium-browser "$RUN/trusted/runtime/chromium" "$RUN/trusted/runtime/chromium-executables.list" <<'PYCHROMIUM'
import os,pathlib,stat,sys
source,destination,out=map(pathlib.Path,sys.argv[1:]); executables=[]
for src in sorted(source.rglob('*'),key=lambda p:p.relative_to(source).as_posix().encode()):
 rel=src.relative_to(source); dst=destination/rel; ss=os.lstat(src); ds=os.lstat(dst)
 if stat.S_ISDIR(ss.st_mode):
  if not stat.S_ISDIR(ds.st_mode) or dst.is_symlink(): raise SystemExit('Chromium staged directory mismatch: '+str(rel))
  dst.chmod(0o555)
 elif stat.S_ISREG(ss.st_mode):
  if not stat.S_ISREG(ds.st_mode) or dst.is_symlink(): raise SystemExit('Chromium staged file mismatch: '+str(rel))
  executable=bool(ss.st_mode & 0o111); dst.chmod(0o555 if executable else 0o444)
  if executable: executables.append(rel.as_posix())
 elif stat.S_ISLNK(ss.st_mode):
  if not stat.S_ISLNK(ds.st_mode) or os.readlink(src)!=os.readlink(dst): raise SystemExit('Chromium staged symlink mismatch: '+str(rel))
 else: raise SystemExit('Chromium special source object rejected: '+str(rel))
destination.chmod(0o555)
required={'chromium-browser','chrome-sandbox','chrome_crashpad_handler','headless_shell'}
if not required.issubset(executables): raise SystemExit('Chromium required executable set missing: '+repr(sorted(required-set(executables))))
for rel in executables:
 p=destination/rel; st=os.lstat(p)
 if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode)!=0o555: raise SystemExit('Chromium executable mode/type mismatch: '+rel)
out.write_text(''.join(x+'\n' for x in executables),encoding='utf-8'); out.chmod(0o444)
PYCHROMIUM
  H06_MYSQL_ROOT="$RUN/trusted/runtime/mysql"; H06_REDIS_ROOT="$RUN/trusted/runtime/redis"; H06_JDK_ROOT="$RUN/trusted/runtime/jdk"; H06_NODE_ROOT="$RUN/trusted/runtime/node"; H06_NGINX_ROOT="$RUN/trusted/runtime/nginx"; CHROME_PATH="$RUN/trusted/runtime/chromium/chromium-browser"
  export H06_MYSQL_ROOT H06_REDIS_ROOT H06_JDK_ROOT H06_NODE_ROOT H06_NGINX_ROOT H06_WORKER_UID H06_WORKER_GID
  MYSQLD="$H06_MYSQL_ROOT/bin/mysqld"; MYSQL="$H06_MYSQL_ROOT/bin/mysql"; MYSQLADMIN="$H06_MYSQL_ROOT/bin/mysqladmin"
  h06_verify_sha256 "$CHROME_PATH" "$H06_CHROMIUM_EXEC_SHA256" 'staged Chromium executable' || die 'staged Chromium executable mismatch'
  stage_gradle_cache_snapshot
}

assert_candidate() {
  local label="$1" repo="$2" ref="$3" head="$4" tree="$5" out="$6"
  [[ -d "$repo" && ! -L "$repo" ]] || die "$label worktree unavailable or symlinked: $repo"
  local ah at ar status
  ah="$(h06_repo_git "$repo" rev-parse --verify HEAD)"
  at="$(h06_repo_git "$repo" rev-parse --verify 'HEAD^{tree}')"
  ar="$(h06_repo_git "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  status="$(h06_repo_git "$repo" status --porcelain=v1 --untracked-files=all)"
  [[ "$ah" == "$head" ]] || die "$label HEAD mismatch expected=$head actual=$ah"
  [[ "$at" == "$tree" ]] || die "$label tree mismatch expected=$tree actual=$at"
  [[ "$ar" == "$ref" ]] || die "$label ref mismatch expected=$ref actual=${ar:-DETACHED}"
  [[ -z "$status" ]] || die "$label worktree is dirty"
  printf 'LABEL=%s\nWORKTREE=%s\nREF=%s\nHEAD=%s\nTREE=%s\nSTATUS=CLEAN\n' "$label" "$repo" "$ref" "$head" "$tree" > "$out"
}

write_release_input() {
  local npm_real="$H06_NODE_ROOT/lib/node_modules/npm/bin/npm-cli.js" release_id
  [[ -x "$npm_real" && -f "$npm_real" && ! -L "$npm_real" ]] || die "trusted staged physical npm CLI unavailable: $npm_real"
  release_id="h06-${RUN_ID//[^A-Za-z0-9._-]/-}"
  python3 - "$RUN/config/release-input.json" "$release_id" "$RUN/artifacts" \
    "$API_STAGED" "$API_REF" "$API_HEAD" "$API_TREE" "$WEB_STAGED" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$npm_real" <<'PYINPUT'
import json,sys
(path,rid,artifact_root,api,ar,ah,at,web,wr,wh,wt,npm)=sys.argv[1:]
payload={'schema':'cyf-m2-c08-release-input-v1','releaseId':rid,'verificationProfile':'archive-h06','minimumFreeBytes':5368709120,'artifactRoot':artifact_root,
 'api':{'repo':api,'ref':ar,'head':ah,'tree':at,'gradleTask':':starter:bootJar','jarRelativePath':'starter/build/libs/starter-1.1.2-SNAPSHOT.jar','deploy':{'liveJar':'/home/isp/hosts/cyf/api/cyf-api-kit.jar','pidFile':'/home/isp/hosts/cyf/api/cyf-api-kit.pid','workDir':'/home/isp/hosts/cyf/api','backupRoot':'/home/isp/baks/legacy-api/releases','recordRoot':'/home/isp/baks/legacy-api/release-records','healthUrl':'http://127.0.0.1:18018/actuator/health','healthExpectedRegex':'"status"[[:space:]]*:[[:space:]]*"UP"','stopTimeoutSeconds':30,'healthTimeoutSeconds':90}},
 'web':{'repo':web,'ref':wr,'head':wh,'tree':wt,'npmBin':npm,'distRelativePath':'dist','deploy':{'liveDir':'/home/isp/hosts/cyf/web/kit','backupRoot':'/home/isp/baks/legacy-web','recordRoot':'/home/isp/baks/legacy-web/release-records','healthUrls':['https://kit.h06.invalid:18443/','https://kit.h06.invalid:18443/juyiting'],'healthTimeoutSeconds':30}}}
with open(path,'x',encoding='utf-8') as stream:
 json.dump(payload,stream,ensure_ascii=False,sort_keys=True,indent=2); stream.write('\n')
PYINPUT
}

artifact_bind_permission_preflight() {
  local driver="$RUN/tmp/artifact-bind-preflight.sh" record="$ROOT_RECORDS/artifact-bind-permission-preflight.txt" detail
  cat > "$driver" <<'BINDPREFLIGHT'
#!/usr/bin/env bash
set -Eeuo pipefail
/usr/bin/mount --make-rprivate /
source_identity="$(/usr/bin/stat -Lc '%d:%i' -- "$WORKER_ARTIFACTS")"
target_host_identity="$(/usr/bin/stat -Lc '%d:%i' -- "$ROOT_ARTIFACTS")"
[[ "$source_identity" != "$target_host_identity" ]] || { echo 'BIND_PREFLIGHT=FAIL source and host target unexpectedly alias before bind' >&2; exit 1; }
/usr/bin/mount --bind "$WORKER_ARTIFACTS" "$ROOT_ARTIFACTS"
[[ "$(/usr/bin/stat -Lc '%d:%i' -- "$ROOT_ARTIFACTS")" == "$source_identity" ]] || { echo 'BIND_PREFLIGHT=FAIL target does not expose source identity after bind' >&2; exit 1; }
exec /usr/bin/setpriv --reuid="$H06_WORKER_UID" --regid="$H06_WORKER_GID" --clear-groups --no-new-privs   /usr/bin/python3 - "$ROOT_ARTIFACTS" <<'PYBINDPREFLIGHT'
import os, pathlib, stat, sys
target=pathlib.Path(sys.argv[1])
st=os.lstat(target)
if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.geteuid(): raise SystemExit('bind target is not the worker-owned source view')
release=target/'release'
os.mkdir(release,0o700)
dirfd=os.open(release,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
try:
 fd=os.open('.h06-verify-mkdir-probe',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=dirfd)
 try: os.write(fd,b'bind-view-write\n'); os.fsync(fd)
 finally: os.close(fd)
 os.unlink('.h06-verify-mkdir-probe',dir_fd=dirfd); os.fsync(dirfd)
finally: os.close(dirfd)
os.rmdir(release); rootfd=os.open(target,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC); os.fsync(rootfd); os.close(rootfd)
print('ARTIFACT_BIND_VIEW_RELEASE_CREATE=PASS')
print('ARTIFACT_BIND_VIEW_UID='+str(os.geteuid()))
PYBINDPREFLIGHT
BINDPREFLIGHT
  chown root:root "$driver"; chmod 0555 "$driver"
  : > "$record"
  if ! WORKER_ARTIFACTS="$WORKER_ARTIFACTS" ROOT_ARTIFACTS="$RUN/artifacts" H06_WORKER_UID="$H06_WORKER_UID" H06_WORKER_GID="$H06_WORKER_GID"     /usr/bin/unshare -m -p --fork --kill-child=KILL --mount-proc /bin/bash "$driver" >> "$record" 2>&1; then
    detail="$(tail -n 24 "$record" | awk 'NF {gsub(/[[:space:]]+/," "); out=(out?out" | ":"")$0} END {print out}')"
    die "artifact bind permission preflight failed: ${detail:-diagnostic record empty}"
  fi
  /usr/bin/python3 - "$WORKER_ARTIFACTS" "$RUN/artifacts" <<'PYBINDHOST' >> "$record"
import os,stat,sys
source,target=sys.argv[1:]
for label,path,uid,mode in [('source',source,61006,0o700),('host-target',target,0,0o700)]:
 st=os.lstat(path)
 if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode): raise SystemExit(f'{label} is not a physical directory')
 if st.st_uid!=uid or stat.S_IMODE(st.st_mode)!=mode: raise SystemExit(f'{label} owner/mode mismatch uid={st.st_uid} mode={oct(stat.S_IMODE(st.st_mode))}')
 if os.listdir(path): raise SystemExit(f'{label} retained bind-probe output: {os.listdir(path)!r}')
print('ARTIFACT_BIND_SOURCE_EMPTY_AFTER_PROBE=PASS')
print('ARTIFACT_HOST_TARGET_ROOT_ONLY_AFTER_PROBE=PASS')
print('BUILD_NETWORK_NAMESPACE=HOST_NETWORK_ALLOWED_FOR_DEPENDENCY_RESOLUTION')
PYBINDHOST
  pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 && die 'UID61006 remained active after artifact bind permission preflight'
  grep -Fxq 'ARTIFACT_BIND_VIEW_RELEASE_CREATE=PASS' "$record" || die 'artifact bind preflight did not prove release directory creation'
  grep -Fxq 'ARTIFACT_HOST_TARGET_ROOT_ONLY_AFTER_PROBE=PASS' "$record" || die 'artifact bind preflight did not preserve root-only host target'
}

worker_permission_preflight() {
  chmod 0711 "$RUN" "$RUN/worker" "$WORKER_OUTPUT"
  chmod 0555 "$RUN/config" "$RUN/tmp" "$RUN/trusted" "$RUN/trusted/h06" "$RUN/trusted/runtime" "$H06_RELEASE_ROOT"
  mkdir -p "$WORKER_ARTIFACTS"
  chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$API_STAGED" "$WEB_STAGED" "$RUN/worker/home" "$RUN/worker/gradle-home" "$WORKER_ARTIFACTS" "$RUN/mysql" "$RUN/runtime" "$RUN/browser" "$RUN/release" "$RUN/sandbox"
  chmod 0700 "$API_STAGED" "$WEB_STAGED" "$RUN/worker/home" "$RUN/worker/gradle-home" "$WORKER_ARTIFACTS" "$RUN/mysql" "$RUN/runtime" "$RUN/browser" "$RUN/release" "$RUN/sandbox"
  local check="$RUN/tmp/permission-preflight.sh"
  cat > "$check" <<'PREFLIGHT'
#!/usr/bin/env bash
set -uo pipefail
/usr/bin/python3 - <<'PYPREFLIGHT'
import errno, os, secrets, stat, subprocess, sys
uid=os.geteuid()
def fail(path,expected,actual):
 print(f'PERMISSION_PREFLIGHT=FAIL PATH={path} EXPECTED={expected} ACTUAL={actual}',file=sys.stderr,flush=True); raise SystemExit(1)
def physical(path,kind):
 try: st=os.lstat(path)
 except OSError as exc: fail(path,kind,f'lstat:{exc}')
 if stat.S_ISLNK(st.st_mode): fail(path,kind,'symlink')
 if kind=='physical regular file' and not stat.S_ISREG(st.st_mode): fail(path,kind,oct(st.st_mode))
 if kind=='physical directory' and not stat.S_ISDIR(st.st_mode): fail(path,kind,oct(st.st_mode))
 return st
def require_access(path,mode,expected):
 if not os.access(path,mode): fail(path,expected,'os.access denied')
 print(f'ACCESS=PASS PATH={path} EXPECTED={expected}',flush=True)
def writable_probe(path,label):
 physical(path,'physical directory'); require_access(path,os.R_OK|os.W_OK|os.X_OK,f'{label}:read/write/execute')
 name='.h06-write-fsync-probe-'+str(os.getpid())+'-'+secrets.token_hex(4); dirfd=fd=None
 try:
  dirfd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=dirfd)
  payload=(label+'\n').encode(); os.write(fd,payload); os.fsync(fd); os.close(fd); fd=None
  st=os.stat(name,dir_fd=dirfd,follow_symlinks=False)
  if not stat.S_ISREG(st.st_mode) or st.st_uid!=uid or st.st_nlink!=1: fail(os.path.join(path,name),f'{label}:worker single-link regular probe','unexpected owner/type/link count')
  os.unlink(name,dir_fd=dirfd); os.fsync(dirfd)
 except Exception as exc:
  if fd is not None:
   try: os.close(fd)
   except OSError: pass
  if dirfd is not None:
   try: os.unlink(name,dir_fd=dirfd)
   except OSError: pass
  fail(path,f'{label}:create+write+fsync+remove+directory-fsync',repr(exc))
 finally:
  if dirfd is not None:
   try: os.close(dirfd)
   except OSError: pass
 print(f'WRITE_PROBE=PASS PATH={path} LABEL={label} CREATE=PASS FSYNC=PASS REMOVE=PASS',flush=True)
def denied_write_probe(path,label):
 physical(path,'physical directory')
 if os.access(path,os.W_OK): fail(path,f'{label}:write denied','os.access reports writable')
 probe=os.path.join(path,'.h06-denied-write-probe-'+str(os.getpid())+'-'+secrets.token_hex(4)); fd=None
 try:
  try: fd=os.open(probe,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
  except OSError as exc:
   if exc.errno not in (errno.EACCES,errno.EPERM,errno.EROFS): fail(path,f'{label}:write denied',repr(exc))
  else:
   os.close(fd); fd=None; os.unlink(probe); fail(path,f'{label}:write denied','actual create succeeded')
 finally:
  if fd is not None:
   try: os.close(fd)
   except OSError: pass
 print(f'WRITE_DENIED_PROBE=PASS PATH={path} LABEL={label}',flush=True)
read_files=[
 os.path.join(os.environ['API_WORKTREE'],'gradlew'),os.path.join(os.environ['API_WORKTREE'],'gradle/wrapper/gradle-wrapper.jar'),os.path.join(os.environ['API_WORKTREE'],'gradle/wrapper/gradle-wrapper.properties'),
 os.path.join(os.environ['WEB_WORKTREE'],'package.json'),os.path.join(os.environ['WEB_WORKTREE'],'package-lock.json'),os.path.join(os.environ['WEB_WORKTREE'],'tests/archive-reader.test.js'),
 os.environ['INPUT'],os.environ['BROWSER'],os.environ['LIB'],os.environ['CHROMIUM_EXEC_LIST']]
release_names=('common.sh','build-api.sh','build-web.sh','promote-release.sh','verify-release.sh','deploy-api.sh','deploy-web.sh','rollback-api.sh','rollback-web.sh')
exec_files=[os.path.join(os.environ['H06_RELEASE_ROOT'],name) for name in release_names]+[
 os.path.join(os.environ['H06_MYSQL_ROOT'],'bin/mysqld'),os.path.join(os.environ['H06_MYSQL_ROOT'],'bin/mysql'),os.path.join(os.environ['H06_MYSQL_ROOT'],'bin/mysqladmin'),
 os.path.join(os.environ['H06_REDIS_ROOT'],'bin/redis-server'),os.path.join(os.environ['H06_REDIS_ROOT'],'bin/redis-cli'),
 os.path.join(os.environ['H06_JDK_ROOT'],'bin/java'),os.path.join(os.environ['H06_JDK_ROOT'],'bin/javac'),os.path.join(os.environ['H06_JDK_ROOT'],'bin/jar'),
 os.path.join(os.environ['H06_NODE_ROOT'],'bin/node'),os.environ['NPM_CLI'],os.path.join(os.environ['H06_NGINX_ROOT'],'sbin/nginx'),os.environ['CHROME_PATH']]
with open(os.environ['CHROMIUM_EXEC_LIST'],encoding='utf-8') as stream:
 for rel in [line.strip() for line in stream if line.strip()]: exec_files.append(os.path.join(os.environ['CHROMIUM_ROOT'],rel))
for path in read_files: physical(path,'physical regular file'); require_access(path,os.R_OK,'readable physical regular file')
for path in dict.fromkeys(exec_files): physical(path,'physical regular file'); require_access(path,os.R_OK|os.X_OK,'readable executable physical regular file')
write_dirs=[
 ('API_STAGED',os.environ['API_WORKTREE']),('WEB_STAGED',os.environ['WEB_WORKTREE']),('WORKER_ARTIFACTS',os.environ['WORKER_ARTIFACTS']),('WORKER_HOME',os.environ['HOME']),('FRESH_GRADLE_HOME',os.environ['GRADLE_USER_HOME']),
 ('MYSQL_WORK',os.environ['MYSQL_WORK']),('RUNTIME_WORK',os.environ['RUNTIME_WORK']),('BROWSER_WORK',os.environ['BROWSER_WORK']),('RELEASE_WORK',os.environ['RELEASE_WORK']),('SANDBOX_WORK',os.environ['SANDBOX_WORK'])]
for stage in ('build','mysql','runtime','release','browser'):
 for kind in ('records','logs'): write_dirs.append((f'{stage.upper()}_{kind.upper()}',os.path.join(os.environ['WORKER_OUTPUT'],stage,kind)))
for label,path in write_dirs: writable_probe(path,label)
for label,path in [('ROOT_RECORDS',os.environ['ROOT_RECORDS']),('ROOT_LOGS',os.environ['ROOT_LOGS']),('ROOT_ARTIFACTS',os.environ['ROOT_ARTIFACTS']),('H06_RELEASE_ROOT',os.environ['H06_RELEASE_ROOT']),('RUN_TRUSTED',os.environ['RUN_TRUSTED']),('WORKER_OUTPUT_PARENT',os.environ['WORKER_OUTPUT']),('EVIDENCE_ROOT',os.environ['EVIDENCE_ROOT'])]: denied_write_probe(path,label)
gradle=os.environ['GRADLE_USER_HOME']
for rel in ('wrapper/dists/gradle-9.3.1-bin/e6fpmcitnr2cbhj7h6pdk7btv/gradle-9.3.1/bin/gradle','wrapper/dists/gradle-9.3.1-bin/e6fpmcitnr2cbhj7h6pdk7btv/gradle-9.3.1/lib/gradle-core-9.3.1.jar'):
 path=os.path.join(gradle,rel); physical(path,'physical regular file'); require_access(path,os.R_OK,'readable Gradle 9.3.1 file')
require_access(os.path.join(gradle,'wrapper/dists/gradle-9.3.1-bin/e6fpmcitnr2cbhj7h6pdk7btv/gradle-9.3.1/bin/gradle'),os.X_OK,'executable Gradle 9.3.1 launcher')
for rel in ('daemon','workers','notifications','registry','caches/9.3.1/fileHashes','caches/9.3.1/fileChanges','caches/9.3.1/executionHistory'):
 path=os.path.join(gradle,rel)
 if os.path.lexists(path): fail(path,'mutable Gradle state absent','present')
for label,repo in (('API_STAGED',os.environ['API_WORKTREE']),('WEB_STAGED',os.environ['WEB_WORKTREE'])):
 proc=subprocess.run(['/usr/bin/git','-c','safe.directory='+repo,'-C',repo,'status','--porcelain=v1','--untracked-files=all'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if proc.returncode!=0: fail(repo,f'{label}:git status succeeds',proc.stderr.decode('utf-8','replace').strip() or f'status={proc.returncode}')
 if proc.stdout: fail(repo,f'{label}:git status clean',proc.stdout.decode('utf-8','replace').strip())
 print(f'GIT_STATUS=PASS LABEL={label} PATH={repo} STATUS=CLEAN',flush=True)
print(f'UID={uid}',flush=True); print('GRADLE_HOME_OWNER_WRITE=PASS',flush=True); print('GRADLE_9_3_1_DISTRIBUTION=PASS',flush=True); print('GRADLE_MUTABLE_STATE_BASELINE=ABSENT',flush=True); print('ROOT_FINAL_RECORD_LOG_WRITE=DENIED',flush=True); print('PERMISSION_PREFLIGHT=PASS',flush=True); print('SERVICES_STARTED=0',flush=True)
PYPREFLIGHT
PREFLIGHT
  chown root:root "$check"; chmod 0555 "$check"
  local record="$ROOT_RECORDS/worker-permission-preflight.txt" detail npm_cli="$H06_NODE_ROOT/lib/node_modules/npm/bin/npm-cli.js"
  : > "$record"
  if ! h06_worker_traversal_probe "$check" "$EVIDENCE_ROOT" "$RUN" >> "$record" 2>&1; then
    detail="$(tail -n 24 "$record" | awk 'NF {gsub(/[[:space:]]+/," "); out=(out?out" | ":"")$0} END {print out}')"; die "UID${H06_WORKER_UID} traversal preflight failed: ${detail:-diagnostic record empty}"
  fi
  if ! h06_worker_exec env API_WORKTREE="$API_STAGED" WEB_WORKTREE="$WEB_STAGED" INPUT="$RUN/config/release-input.json" BROWSER="$BROWSER" LIB="$LIB" H06_RELEASE_ROOT="$H06_RELEASE_ROOT" H06_MYSQL_ROOT="$H06_MYSQL_ROOT" H06_REDIS_ROOT="$H06_REDIS_ROOT" H06_JDK_ROOT="$H06_JDK_ROOT" H06_NODE_ROOT="$H06_NODE_ROOT" H06_NGINX_ROOT="$H06_NGINX_ROOT" CHROME_PATH="$CHROME_PATH" CHROMIUM_ROOT="$RUN/trusted/runtime/chromium" CHROMIUM_EXEC_LIST="$RUN/trusted/runtime/chromium-executables.list" NPM_CLI="$npm_cli" GRADLE_USER_HOME="$RUN/worker/gradle-home" HOME="$RUN/worker/home" WORKER_ARTIFACTS="$WORKER_ARTIFACTS" WORKER_OUTPUT="$WORKER_OUTPUT" MYSQL_WORK="$RUN/mysql" RUNTIME_WORK="$RUN/runtime" BROWSER_WORK="$RUN/browser" RELEASE_WORK="$RUN/release" SANDBOX_WORK="$RUN/sandbox" ROOT_RECORDS="$ROOT_RECORDS" ROOT_LOGS="$ROOT_LOGS" ROOT_ARTIFACTS="$RUN/artifacts" RUN_TRUSTED="$RUN/trusted" EVIDENCE_ROOT="$EVIDENCE_ROOT" /bin/bash "$check" >> "$record" 2>&1; then
    detail="$(tail -n 24 "$record" | awk 'NF {gsub(/[[:space:]]+/," "); out=(out?out" | ":"")$0} END {print out}')"; die "UID${H06_WORKER_UID} permission preflight failed: ${detail:-diagnostic record empty}"
  fi
  grep -Fxq 'TRAVERSAL_PREFLIGHT=PASS' "$record" || die 'worker traversal preflight did not emit PASS'
  grep -Fxq 'PERMISSION_PREFLIGHT=PASS' "$record" || die 'worker permission preflight did not emit PASS'
  artifact_bind_permission_preflight
}
seal_worker_driver() {
  local driver="$1"
  chown root:root "$driver"; chmod 0555 "$driver"
  h06_worker_exec test -r "$driver"
  h06_worker_exec test -x "$driver"
  printf '%s\tUID%s_READ_EXECUTE=PASS\n' "$driver" "$H06_WORKER_UID" >> "$ROOT_RECORDS/worker-driver-permissions.txt"
}

prepare_gate() {
  log 'freezing source/API catalogs, transaction/lock boundaries, allowlists, and acceptance coverage'
  assert_candidate API "$API_WORKTREE" "$API_REF" "$API_HEAD" "$API_TREE" "$ROOT_RECORDS/api-pin.txt"
  assert_candidate WEB "$WEB_WORKTREE" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$ROOT_RECORDS/web-pin.txt"
  stage_pinned_worktrees
  stage_runtime_inventory
  cat > "$ROOT_RECORDS/frozen-catalogs.txt" <<EOFREC
EVENT_CATALOG=archive question QUESTION_QUEUED,QUESTION_RUNNING,ANSWER_DELTA,QUESTION_SUCCEEDED,QUESTION_FAILED_RETRYABLE,QUESTION_FAILED_FINAL,QUESTION_RETRY_QUEUED,resync_required
API_CATALOG=/archive/v1/catalog,/archive/v1/editions/{editionId}/preface,/archive/v1/editions/{editionId}/chapters/{chapterId},/archive/v1/me/progress/{editionId},/archive/v1/me/bookmarks,/archive/v1/me/notes,/archive/v1/me/questions/{questionId},/archive/v1/me/questions/{questionId}/events,/chat/library/search
OWNER_SCOPE=(tenant_id,client_id,owner_jiacn);owner_jiacn=jiacn
ALLOWED_SCOPES=(h06-owner-a,h06-client-a),(h06-owner-a,h06-client-b),(h06-owner-b,h06-client-a),(h06-owner-b,h06-client-b)
LOCK_ORDER=mutation-key-row -> exact-owner-resource-row -> dependent-event-row; selectors are authoritative
TRANSACTION_BOUNDARIES=each idempotent mutation and state/event transition is one service transaction; selectors are authoritative
SENSITIVE_PAYLOAD_ALLOWLIST=JWT claims and token SHA256 only; bearer/password/private-key bytes forbidden from evidence
ACCEPTANCE_TEST_COVERAGE=content:prepare;schema-concurrency:H02/H03/H05A selectors;identity-ACL:runtime-probe;browser:CDP;ES-down:runtime;release:real build/verify/deploy/rollback
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
PRODUCTION_DB_OPERATION=NOT_PERFORMED
EOFREC
  local source="$ROOT/specs/archive-pavilion-reader-mvp/content/source/shuihu_raw.txt"
  local manifest="$ROOT/specs/archive-pavilion-reader-mvp/content/manifest.json"
  local golden="$ROOT/specs/archive-pavilion-reader-mvp/content/golden-summary.json"
  local bundled="$API_STAGED/chat/jia-chat-service/src/main/resources/archive/$EDITION_ID"
  for path in "$source" "$manifest" "$golden" "$bundled/manifest.json" "$bundled/golden-summary.json"; do require_physical_file "$path"; done
  cmp -s "$manifest" "$bundled/manifest.json" || die 'root and API bundled manifest differ byte-for-byte'
  cmp -s "$golden" "$bundled/golden-summary.json" || die 'root and API bundled golden summary differ byte-for-byte'
  python3 - "$source" "$manifest" "$golden" "$SOURCE_SHA" "$MANIFEST_FILE_SHA" "$MANIFEST_SEMANTIC_SHA" "$GOLDEN_SHA" "$EXPECTED_CHAPTERS" "$EXPECTED_PREFACE_PARAGRAPHS" "$EXPECTED_CHAPTER_PARAGRAPHS" "$EXPECTED_TOTAL_PARAGRAPHS" > "$ROOT_RECORDS/content-gate.json" <<'PY'
import hashlib,json,pathlib,sys
source,manifest,golden,source_sha,manifest_file_sha,manifest_semantic_sha,golden_sha,*counts=sys.argv[1:]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if sha(source)!=source_sha: raise SystemExit('frozen source SHA mismatch')
if sha(manifest)!=manifest_file_sha: raise SystemExit('frozen manifest file SHA mismatch')
if sha(golden)!=golden_sha: raise SystemExit('frozen golden file SHA mismatch')
m=json.loads(pathlib.Path(manifest).read_text(encoding='utf-8')); g=json.loads(pathlib.Path(golden).read_text(encoding='utf-8'))
chapters=m.get('chapters',[]); preface=m.get('preface',{}).get('paragraphs',[])
chapter_paragraphs=sum(len(c.get('paragraphs',[])) for c in chapters)
actual=[len(chapters),len(preface),chapter_paragraphs,len(preface)+chapter_paragraphs]
expected=list(map(int,counts))
if actual!=expected: raise SystemExit(f'content counts mismatch actual={actual} expected={expected}')
internal=m.get('manifestSha256') or m.get('manifest_sha256') or g.get('manifestSha256') or g.get('manifest_sha256')
if internal!=manifest_semantic_sha: raise SystemExit(f'declared manifest semantic SHA mismatch: {internal}')
semantic=dict(m); semantic.pop('manifestSha256',None); semantic.pop('manifest_sha256',None)
canonical=(json.dumps(semantic,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
recomputed=hashlib.sha256(canonical).hexdigest()
if recomputed!=manifest_semantic_sha: raise SystemExit(f'independently recomputed semantic SHA mismatch expected={manifest_semantic_sha} actual={recomputed}')
print(json.dumps({'result':'PASS','sourceFileSha256':source_sha,'manifestFileSha256':manifest_file_sha,'declaredManifestSemanticSha256':internal,'recomputedCanonicalManifestSemanticSha256':recomputed,'canonicalization':'remove manifestSha256/manifest_sha256; ensure_ascii=false; indent=2; sort_keys; trailing LF; UTF-8','goldenFileSha256':golden_sha,'chapters':actual[0],'prefaceParagraphs':actual[1],'chapterParagraphs':actual[2],'totalParagraphs':actual[3]},ensure_ascii=False,sort_keys=True,indent=2))
PY
  local reader_output question_output
  local -a reader_flags=() question_flags=()
  if ! reader_output="$(h06_repo_git "$API_STAGED" grep -h '^archive.reader.enabled=' "$API_HEAD" -- '*application*.properties' | LC_ALL=C sort)"; then
    die 'pinned staged API git grep failed for archive.reader.enabled declarations'
  fi
  if ! question_output="$(h06_repo_git "$API_STAGED" grep -h '^archive.question.enabled=' "$API_HEAD" -- '*application*.properties' | LC_ALL=C sort)"; then
    die 'pinned staged API git grep failed for archive.question.enabled declarations'
  fi
  [[ -z "$reader_output" ]] || mapfile -t reader_flags <<< "$reader_output"
  [[ -z "$question_output" ]] || mapfile -t question_flags <<< "$question_output"
  ((${#reader_flags[@]} == 5 && ${#question_flags[@]} == 2)) \
    || die "archive bundled default-off declaration count mismatch: reader=${#reader_flags[@]} question=${#question_flags[@]}"
  for line in "${reader_flags[@]}" "${question_flags[@]}"; do [[ "$line" == *=false ]] || die "archive bundled flag is not false: $line"; done
  printf '%s\n' "${reader_flags[@]}" > "$ROOT_RECORDS/archive-reader-default-off.txt"
  printf '%s\n' "${question_flags[@]}" > "$ROOT_RECORDS/archive-question-default-off.txt"
  write_release_input
  chmod 0444 "$RUN/config/release-input.json"
  sha256sum "$RUN/config/release-input.json" > "$ROOT_RECORDS/release-input.sha256"
  cat > "$ROOT_RECORDS/command-catalog.txt" <<EOFCOMMANDS
PREPARE=candidate commit/tree/clean + frozen pin/tree/clean + content byte/hash/count + bundled default-off + lock-held fresh Gradle 9.3.1 allowlist snapshot
MYSQL=unshare -m -n -p; disposable MySQL; flock -w 600 -x /tmp/cyf-gradle.lock; H02 then H03 then H05A exact one-test selectors + exact SSE cursor/overflow/live-before-replay/disconnect-cleanup/service-stop-cleanup selectors
RUNTIME=unshare -m -n -p; loopback-only fixture; four bearer scopes; direct API ACL/zero-write; CDP browser
RELEASE_BUILD=unshare -m -p host-network build namespace; one immutable release-input byte sequence; worker artifact source bind-mounted at the same logical host artifactRoot; build-api/build-web/Web-38/verify-release; UID-quiescent no-follow import; root-only common metadata/sidecar/release-record verification
RELEASE_DRILL=unshare -m -n -p; sandbox bind mounts; real execute deploy-api/deploy-web then flag-off restart then rollback-web/rollback-api
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
PRODUCTION_DB_OPERATION=NOT_PERFORMED
EOFCOMMANDS
  worker_permission_preflight
  log 'prepare gate PASS'
}

mysql_gate() {
  [[ -x "$MYSQLD" && -x "$MYSQL" && -x "$MYSQLADMIN" ]] || blocked 'local MySQL 8.0.21 executables are unavailable'
  local port suffix driver
  chmod 0711 "$RUN"; chmod 0555 "$RUN/trusted" "$RUN/trusted/h06"
  chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$RUN/mysql"; chmod 0700 "$RUN/mysql"
  port=$((24000 + RANDOM % 12000)); [[ "$port" != 3306 && "$port" != 33060 ]] || port=27771
  suffix="${RUN_ID//[^A-Za-z0-9]/}"; suffix="${suffix: -12}"
  driver="$RUN/tmp/mysql-driver.sh"
  cat > "$driver" <<'DRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'; umask 077
if [[ "${1:-}" != --worker ]]; then
  mount --make-rprivate /; ip link set lo up; [[ -z "$(ip route show)" ]] || exit 20
  exec setpriv --reuid="$H06_WORKER_UID" --regid="$H06_WORKER_GID" --clear-groups --no-new-privs /bin/bash "$0" --worker
fi
source "$LIB"
[[ "$EUID" -eq "$H06_WORKER_UID" && -z "$(ip route show)" ]] || { echo 'worker identity/network boundary mismatch' >&2; exit 20; }
ss -lntp > "$OUT_RECORDS/mysql-listeners-before.txt"
"$MYSQLD" --initialize-insecure --datadir="$RUN/mysql" --lower-case-table-names=1 --log-error="$OUT_LOGS/mysql-init.log"
"$MYSQLD" --no-defaults --datadir="$RUN/mysql" --socket="$RUN/mysql/mysql.sock" --pid-file="$RUN/mysql/mysql.pid" --port="$PORT" --bind-address=127.0.0.1 --skip-name-resolve --mysqlx=0 --lower-case-table-names=1 --performance-schema=OFF --innodb-buffer-pool-size=64M --key-buffer-size=8M --max-connections=20 --log-bin-trust-function-creators=1 --log-error="$OUT_LOGS/mysql-server.log" &
MYSQL_PID=$!
REG="$RUN/mysql-pids.tsv"; : > "$REG"; h06_track_pid "$REG" mysql "$MYSQL_PID" "$MYSQLD"
cleanup(){ set +e; h06_stop_tracked_pids "$REG"; printf 'MYSQL_PROCESS_CLEANUP=PASS\nMYSQL_DATADIR_DISPOSABLE=%s\nPRODUCTION_3306_33060=NOT_TOUCHED\n' "$RUN/mysql" > "$OUT_RECORDS/mysql-cleanup.txt"; }
trap cleanup EXIT
for _ in {1..90}; do "$MYSQLADMIN" --protocol=socket --socket="$RUN/mysql/mysql.sock" ping >/dev/null 2>&1 && break; kill -0 "$MYSQL_PID" 2>/dev/null || exit 21; sleep 1; done
"$MYSQLADMIN" --protocol=socket --socket="$RUN/mysql/mysql.sock" ping >/dev/null
"$MYSQL" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -N -B -e 'SELECT VERSION(),@@version_compile_machine,@@port,@@mysqlx_port,@@lower_case_table_names,@@datadir' > "$OUT_RECORDS/mysql-version.txt"
[[ "$(readlink -f /proc/$MYSQL_PID/exe)" == "$(readlink -f "$MYSQLD")" ]] || { echo 'MySQL server executable mismatch' >&2; exit 22; }
sha256sum "$MYSQLD" "$MYSQL" "$MYSQLADMIN" > "$OUT_RECORDS/mysql-binary-sha256.txt"
grep -Eq $'^8\.0\.21\t.*\t' "$OUT_RECORDS/mysql-version.txt" || { echo 'MySQL version is not 8.0.21' >&2; exit 22; }
grep -Fq $'\t'"$PORT"$'\t0\t1\t'"$RUN/mysql/" "$OUT_RECORDS/mysql-version.txt" || { echo 'MySQL server endpoint/datadir identity mismatch' >&2; exit 22; }
for prefix in h02 h03 h05a; do db="cyf_${prefix}_${SUFFIX}"; "$MYSQL" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -e "CREATE DATABASE \`$db\` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"; done
run_selector(){
 local key="$1" db="$2" selector="$3" method="$4" fixture="$5" expected_digest="$6" log="$7"
 local result="$API_WORKTREE/chat/jia-chat-service/build/test-results/test/TEST-${selector}.xml"
 [[ "$(sha256sum "$fixture"|awk '{print $1}')" == "$expected_digest" ]] || { echo "$key fixture digest mismatch before selector" >&2; exit 23; }
 rm -rf "$API_WORKTREE/chat/jia-chat-service/build/test-results/test" "$API_WORKTREE/chat/jia-chat-service/build/reports/tests/test"
 local -a command=(bash "$API_WORKTREE/gradlew" :chat:jia-chat-service:test --tests "$selector" --rerun-tasks --no-daemon --max-workers=1 --no-build-cache '-Dorg.gradle.jvmargs=-Xmx384m -Dfile.encoding=UTF-8' -PrepoUsername=unused -PrepoPassword=unused)
 printf '%q ' env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$H06_JDK_ROOT/bin:/usr/bin:/bin" flock -w 600 -x /tmp/cyf-gradle.lock "${command[@]}" >> "$OUT_RECORDS/mysql-gradle-commands.txt"; printf '\n' >> "$OUT_RECORDS/mysql-gradle-commands.txt"
 env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$H06_JDK_ROOT/bin:/usr/bin:/bin" "CYF_${key}_MYSQL_ISOLATED=true" "CYF_${key}_MYSQL_URL=jdbc:mysql://127.0.0.1:${PORT}/${db}" "CYF_${key}_MYSQL_DATABASE_CONFIRM=${db}" "CYF_${key}_MYSQL_USER=root" "CYF_${key}_MYSQL_PASSWORD=" \
   flock -w 600 -x /tmp/cyf-gradle.lock "${command[@]}" > "$log" 2>&1
 [[ -s "$log" && -f "$result" && ! -L "$result" ]] || { echo "$key selector log/JUnit XML missing" >&2; exit 23; }
 [[ "$(sha256sum "$fixture"|awk '{print $1}')" == "$expected_digest" ]] || { echo "$key fixture changed after selector" >&2; exit 23; }
 python3 - "$key" "$API_TREE" "$selector" "$method" "$expected_digest" "$log" "$result" >> "$OUT_RECORDS/mysql-selector-evidence.jsonl" <<'PYSELECTOR'
import hashlib,json,pathlib,sys,xml.etree.ElementTree as ET
key,tree,selector,method,fixture,log,result=sys.argv[1:]
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
 return h.hexdigest()
root=ET.parse(result).getroot(); cases=list(root.iter('testcase'))
if len(cases)!=1: raise SystemExit('%s expected exactly one testcase, got %s'%(key,len(cases)))
case=cases[0]
if case.get('classname')!=selector or case.get('name')!=method: raise SystemExit('%s testcase mismatch classname=%r name=%r'%(key,case.get('classname'),case.get('name')))
if list(root.iter('failure')) or list(root.iter('error')) or list(root.iter('skipped')): raise SystemExit(key+' selector was not a clean pass')
tests=sum(int(suite.get('tests','0')) for suite in [root] if suite.tag=='testsuite')
if tests!=1: raise SystemExit('%s JUnit tests attribute is not exactly one: %s'%(key,tests))
print(json.dumps({'label':key,'apiTree':tree,'selector':selector,'testcaseClass':case.get('classname'),'testcaseName':case.get('name'),'tests':1,'failures':0,'errors':0,'skipped':0,'fixtureSha256':fixture,'logSha256':sha(log),'junitXmlSha256':sha(result)},sort_keys=True))
PYSELECTOR
}
run_plain_selector(){
 local key="$1" selector="$2" method="$3" fixture="$4" digest="$5" log="$6"
 local result="$API_WORKTREE/chat/jia-chat-service/build/test-results/test/TEST-${selector}.xml"
 [[ "$(sha256sum "$fixture"|awk '{print $1}')" == "$digest" ]] || exit 24
 rm -rf "$API_WORKTREE/chat/jia-chat-service/build/test-results/test" "$API_WORKTREE/chat/jia-chat-service/build/reports/tests/test"
 local exact="$selector.$method"; local -a command=(bash "$API_WORKTREE/gradlew" :chat:jia-chat-service:test --tests "$exact" --rerun-tasks --no-daemon --max-workers=1 --no-build-cache '-Dorg.gradle.jvmargs=-Xmx384m -Dfile.encoding=UTF-8' -PrepoUsername=unused -PrepoPassword=unused)
 printf '%q ' env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$H06_JDK_ROOT/bin:/usr/bin:/bin" flock -w 600 -x /tmp/cyf-gradle.lock "${command[@]}" >> "$OUT_RECORDS/mysql-gradle-commands.txt"; printf '\n' >> "$OUT_RECORDS/mysql-gradle-commands.txt"
 env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$H06_JDK_ROOT/bin:/usr/bin:/bin" flock -w 600 -x /tmp/cyf-gradle.lock "${command[@]}" > "$log" 2>&1
 [[ -s "$log" && -f "$result" && ! -L "$result" && "$(sha256sum "$fixture"|awk '{print $1}')" == "$digest" ]] || exit 24
 python3 - "$key" "$API_TREE" "$selector" "$method" "$digest" "$log" "$result" >> "$OUT_RECORDS/mysql-selector-evidence.jsonl" <<'PYPLAIN'
import hashlib,json,sys,xml.etree.ElementTree as ET
key,tree,selector,method,fixture,log,result=sys.argv[1:]; root=ET.parse(result).getroot(); cases=list(root.iter('testcase'))
tests=int(root.get('tests','-1')); failures=int(root.get('failures','-1')); errors=int(root.get('errors','-1')); skipped=int(root.get('skipped','0'))
if len(cases)!=1 or tests!=1 or failures!=0 or errors!=0 or skipped!=0 or cases[0].get('classname')!=selector or cases[0].get('name')!=method or list(root.iter('failure')) or list(root.iter('error')) or list(root.iter('skipped')): raise SystemExit(key+' exact testcase/JUnit evidence mismatch')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
print(json.dumps({'label':key,'apiTree':tree,'selector':selector+'.'+method,'testcaseClass':selector,'testcaseName':method,'tests':tests,'failures':failures,'errors':errors,'skipped':skipped,'fixtureSha256':fixture,'logSha256':sha(log),'junitXmlSha256':sha(result)},sort_keys=True))
PYPLAIN
}
BASE="$API_WORKTREE/chat/jia-chat-service/src/test/java/cn/jia/chat/archive/service"
run_selector H02 "cyf_h02_${SUFFIX}" cn.jia.chat.archive.service.ArchiveMySqlIntegrationTest realMysqlSchemaImportRestartConcurrencyMismatchAndDriftFailClosed "$BASE/ArchiveMySqlIntegrationTest.java" 4f7c275b2d14dfcdcf20794bf2cfebc053ca80a691ee915c27075ac0e6f494cc "$OUT_LOGS/mysql-h02.log"
run_selector H03 "cyf_h03_${SUFFIX}" cn.jia.chat.archive.service.ArchiveReaderDataMySqlIntegrationTest realMysqlExactScopeReplayCasRollbackTombstonesCompletionAndDriftFailClosed "$BASE/ArchiveReaderDataMySqlIntegrationTest.java" 6ccd3fb5ac53c0b3cf4304f273630391e7e9865dd60f50ca288edd5b9a23a282 "$OUT_LOGS/mysql-h03.log"
run_selector H05A "cyf_h05a_${SUFFIX}" cn.jia.chat.archive.service.ArchiveQuestionMySqlIntegrationTest realMysqlFourScopesReplayConcurrencyFencingExhaustionZeroWriteAndDriftFailClosed "$BASE/ArchiveQuestionMySqlIntegrationTest.java" aa3ef26a424e07d91c00aba35a4ff3cd3a853c57e45aed087481c8d7cc465425 "$OUT_LOGS/mysql-h05a.log"
SSE_FIXTURE="$BASE/ArchiveQuestionSseServiceTest.java"; SSE_DIGEST="$(sha256sum "$SSE_FIXTURE"|awk '{print $1}')"
run_plain_selector H06_SSE_CURSOR cn.jia.chat.archive.service.ArchiveQuestionSseServiceTest cursorAheadTruncationReplayGapAndEmptyHistoryAllResyncWithoutPersistentSequence "$SSE_FIXTURE" "$SSE_DIGEST" "$OUT_LOGS/sse-cursor-contract.log"
run_plain_selector H06_SSE_OVERFLOW cn.jia.chat.archive.service.ArchiveQuestionSseServiceTest boundedPreReplayBufferOverflowResyncsClosesAndLateCallbacksCannotWrite "$SSE_FIXTURE" "$SSE_DIGEST" "$OUT_LOGS/sse-overflow-contract.log"
run_plain_selector H06_SSE_LIVE_BEFORE_REPLAY cn.jia.chat.archive.service.ArchiveQuestionSseServiceTest subscribesBeforeReplayAndDeduplicatesLiveWatermarkOverlapInExactOrder "$SSE_FIXTURE" "$SSE_DIGEST" "$OUT_LOGS/sse-live-before-replay-contract.log"
run_plain_selector H06_SSE_DISCONNECT_CLEANUP cn.jia.chat.archive.service.ArchiveQuestionSseServiceTest explicitDisconnectCancelsReplaySubscriptionHeartbeatAndPreventsLateWrites "$SSE_FIXTURE" "$SSE_DIGEST" "$OUT_LOGS/sse-disconnect-cleanup-contract.log"
run_plain_selector H06_SSE_SERVICE_STOP_CLEANUP cn.jia.chat.archive.service.ArchiveQuestionSseServiceTest serviceStopClosesAllStreamsAndRejectsLateReplayOrLiveWrites "$SSE_FIXTURE" "$SSE_DIGEST" "$OUT_LOGS/sse-service-stop-cleanup-contract.log"
[[ $(wc -l < "$OUT_RECORDS/mysql-gradle-commands.txt") == 8 ]] || exit 24
awk 'index($0,"GRADLE_USER_HOME=")==0 || index($0,"JAVA_HOME=")==0 || index($0,"flock -w 600 -x /tmp/cyf-gradle.lock")==0 || index($0,"--no-daemon")==0 || index($0,"--max-workers=1")==0 || index($0,"--tests")==0 {exit 1}' "$OUT_RECORDS/mysql-gradle-commands.txt" || exit 24
sha256sum "$OUT_RECORDS/mysql-gradle-commands.txt" > "$OUT_RECORDS/mysql-gradle-commands.sha256"
python3 - "$OUT_RECORDS/mysql-selector-evidence.jsonl" "$API_TREE" <<'PYINDEX'
import json,pathlib,sys
path=pathlib.Path(sys.argv[1]); tree=sys.argv[2]; rows=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
expected=['H02','H03','H05A','H06_SSE_CURSOR','H06_SSE_OVERFLOW','H06_SSE_LIVE_BEFORE_REPLAY','H06_SSE_DISCONNECT_CLEANUP','H06_SSE_SERVICE_STOP_CLEANUP']
if [row['label'] for row in rows]!=expected or any(row['tests']!=1 or row['apiTree']!=tree for row in rows): raise SystemExit('exact selector evidence index mismatch')
path.with_suffix('.summary.json').write_text(json.dumps({'result':'PASS','apiTree':tree,'selectors':rows,'exactTestcaseCount':len(rows)},sort_keys=True,indent=2)+'\n')
PYINDEX
for db in "cyf_h02_${SUFFIX}" "cyf_h03_${SUFFIX}" "cyf_h05a_${SUFFIX}"; do "$MYSQL" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -N -B -e "SELECT CONCAT('$db=',COUNT(*)) FROM information_schema.tables WHERE table_schema='$db'"; done > "$OUT_RECORDS/mysql-schema-post-test.txt"
ss -lntp > "$OUT_RECORDS/mysql-listeners-after-selectors.txt"
printf 'MYSQL_GATE=PASS\nPORT=%s\nDATABASES=cyf_h02_%s,cyf_h03_%s,cyf_h05a_%s\n' "$PORT" "$SUFFIX" "$SUFFIX" "$SUFFIX" > "$OUT_RECORDS/mysql-result.txt"
DRIVER
  seal_worker_driver "$driver"
  sha256sum \
    "$API_STAGED/chat/jia-chat-service/src/test/java/cn/jia/chat/archive/service/ArchiveMySqlIntegrationTest.java" \
    "$API_STAGED/chat/jia-chat-service/src/test/java/cn/jia/chat/archive/service/ArchiveReaderDataMySqlIntegrationTest.java" \
    "$API_STAGED/chat/jia-chat-service/src/test/java/cn/jia/chat/archive/service/ArchiveQuestionMySqlIntegrationTest.java" \
    "$API_STAGED/chat/jia-chat-service/src/test/java/cn/jia/chat/archive/service/ArchiveQuestionSseServiceTest.java" \
    > "$ROOT_RECORDS/mysql-fixture-digest.txt"
  find "$API_STAGED/chat" -type f -name 'archive*-schema.sql' -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$ROOT_RECORDS/mysql-schema-digest.txt"
  find "$API_STAGED/chat" -type f -name 'archive*-schema.sql' -print0 | LC_ALL=C sort -z | xargs -0 cat | sha256sum | awk '{print "COMBINED_ARCHIVE_SCHEMA_SHA256=" $1}' >> "$ROOT_RECORDS/mysql-schema-digest.txt"
  RUN="$RUN" PORT="$port" SUFFIX="$suffix" MYSQLD="$MYSQLD" MYSQL="$MYSQL" MYSQLADMIN="$MYSQLADMIN" API_WORKTREE="$API_STAGED" LIB="$LIB" H06_WORKER_UID="$H06_WORKER_UID" H06_WORKER_GID="$H06_WORKER_GID" H06_MYSQL_ROOT="$H06_MYSQL_ROOT" \
    unshare -m -n -p --fork --kill-child=KILL --mount-proc -- env RUN="$RUN" OUT_RECORDS="$WORKER_OUTPUT/mysql/records" OUT_LOGS="$WORKER_OUTPUT/mysql/logs" PORT="$port" SUFFIX="$suffix" MYSQLD="$MYSQLD" MYSQL="$MYSQL" MYSQLADMIN="$MYSQLADMIN" API_WORKTREE="$API_WORKTREE" LIB="$LIB" bash "$driver"
  rm -rf --one-file-system -- "$RUN/mysql"
  mkdir "$RUN/mysql"
  printf 'DISPOSABLE_MYSQL_DATADIR_REMOVED=PASS\n' >> "$ROOT_RECORDS/mysql-cleanup.txt"
  log 'MySQL selector gate PASS'
}

write_web_regression_verifier() {
  local helper="$1"
  cat > "$helper" <<'PYWEBVERIFY'
#!/usr/bin/python3
import hashlib,json,pathlib,sys
report_path,log_path,test_path,expected,head,tree,node_path,npm_path,versions_path=sys.argv[1:]
report=pathlib.Path(report_path); log=pathlib.Path(log_path); test_file=pathlib.Path(test_path)
node=pathlib.Path(node_path); npm=pathlib.Path(npm_path); versions=pathlib.Path(versions_path)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''): h.update(block)
 return h.hexdigest()
for path in (report,log,test_file,node,npm,versions):
 if path.is_symlink() or not path.is_file(): raise SystemExit('Web regression evidence/input is not a physical file: '+str(path))
 st=path.stat()
 if st.st_nlink!=1: raise SystemExit('Web regression evidence/input is multi-linked: '+str(path))
if sha(test_file)!=expected: raise SystemExit('Web regression test digest mismatch')
data=json.loads(report.read_text(encoding='utf-8')); stats=data.get('stats') or {}; tests=data.get('tests') or []; failures=data.get('failures') or []
actual={'tests':stats.get('tests'),'passes':stats.get('passes'),'failures':stats.get('failures'),'pending':stats.get('pending')}
if actual!={'tests':38,'passes':38,'failures':0,'pending':0} or len(tests)!=38 or failures: raise SystemExit('Web regression result is not exactly 38 pass / 0 fail: '+repr(actual))
titles=[str(item.get('fullTitle') or item.get('title') or '') for item in tests]
coverage={
 'ambiguity':any('ambiguous' in x for x in titles),'idempotency':any('idempotency' in x for x in titles),
 'version':any('version' in x for x in titles),'overflow':any('overflow' in x for x in titles),
 'duplicate':any('duplicate' in x for x in titles),'staleCleanup':any('stale' in x and ('clean' in x or 'callback' in x or 'work' in x) for x in titles),
 'decimalString':any('decimal strings' in x for x in titles)}
if not all(coverage.values()): raise SystemExit('Web regression semantic coverage title gate failed: '+repr(coverage))
version_lines=versions.read_text(encoding='utf-8').splitlines()
if len(version_lines)!=2: raise SystemExit('Node/npm version evidence malformed')
print(json.dumps({'result':'PASS','webHead':head,'webTree':tree,'testFile':'tests/archive-reader.test.js','testFileSha256':expected,'tests':38,'passes':38,'failures':0,'pending':0,'coverage':coverage,'node':{'path':str(node),'sha256':sha(node),'version':version_lines[0]},'npmCli':{'path':str(npm),'sha256':sha(npm),'version':version_lines[1]},'mochaJsonSha256':sha(report),'logSha256':sha(log),'command':'node --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter json --reporter-option output=<worker-record> --timeout 10000 --exit tests/archive-reader.test.js'},sort_keys=True,indent=2))
PYWEBVERIFY
  chown root:root "$helper"; chmod 0555 "$helper"
}

root_verify_imported_release() {
  local input="$RUN/config/release-input.json" expected_input_sha="$1"
  (
    set -Eeuo pipefail
    PATH="$H06_JDK_ROOT/bin:$H06_NODE_ROOT/bin:/usr/bin:/bin"; export PATH
    # shellcheck disable=SC1090
    source "$H06_RELEASE_ROOT/common.sh"
    load_release_input "$input"
    [[ "$ARTIFACT_ROOT" == "$RUN/artifacts" ]] || die "root artifactRoot mismatch: $ARTIFACT_ROOT"
    [[ "$(artifact_sha256 "$RELEASE_INPUT")" == "$expected_input_sha" ]] || die 'release input changed before root verification'
    assert_clean_candidate 'root API artifact verification' "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
    assert_clean_candidate 'root Web artifact verification' "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"
    verify_component_metadata api
    verify_component_metadata web
    verify_release_record
    printf 'ROOT_COMMON_METADATA_SIDECAR_RECORD_VERIFY=PASS\nRELEASE_INPUT_SHA256=%s\nRELEASE_VERIFY_PROFILE=%s\nRELEASE_TOOL_SHA256=%s\nRELEASE_RECORD=%s\n' \
      "$(artifact_sha256 "$RELEASE_INPUT")" "$RELEASE_VERIFY_PROFILE" "$(release_tool_digest)" "$RELEASE_RECORD"
  ) > "$ROOT_RECORDS/root-release-validation.txt"
}

build_verified_artifacts() {
  [[ -f "$ROOT_RECORDS/artifacts-verified.txt" ]] && return 0
  log 'building and verifying exact pinned artifacts through one host-logical release input in a UID61006 bind-mount namespace'
  export VITE_API_BASE_URL=https://api.h06.invalid:18443
  export VITE_OAUTH_CLIENT_ID=h06-client-a
  local build_records="$WORKER_OUTPUT/build/records" build_logs="$WORKER_OUTPUT/build/logs"
  local input="$RUN/config/release-input.json" driver="$RUN/tmp/build-verify-driver.sh" verifier="$RUN/tmp/web-regression-verifier.py"
  local node_bin="$H06_NODE_ROOT/bin/node" npm_cli="$H06_NODE_ROOT/lib/node_modules/npm/bin/npm-cli.js"
  local test_file="$WEB_STAGED/tests/archive-reader.test.js" expected_test_sha=fdc2a41efdcaa1ced49bb4e024d0e08b5f062bc4573fde9c45ab2e33605b48d4
  local input_sha
  input_sha="$(sha256sum "$input" | awk '{print $1}')"
  [[ "$(sha256sum "$test_file" | awk '{print $1}')" == "$expected_test_sha" ]] || die 'pinned Web archive-reader test digest mismatch before build namespace'
  [[ ! -L "$RUN/artifacts" && -d "$RUN/artifacts" && "$(stat -c '%u:%g:%a' "$RUN/artifacts")" == '0:0:700' ]] || die 'host artifact target is not root-only before build namespace'
  [[ -z "$(find "$RUN/artifacts" -mindepth 1 -print -quit)" ]] || die 'host artifact target is not empty before build namespace'
  [[ ! -L "$WORKER_ARTIFACTS" && -d "$WORKER_ARTIFACTS" && "$(stat -c '%u:%g:%a' "$WORKER_ARTIFACTS")" == "$H06_WORKER_UID:$H06_WORKER_GID:700" ]] || die 'worker artifact source owner/mode mismatch'
  [[ -z "$(find "$WORKER_ARTIFACTS" -mindepth 1 -print -quit)" ]] || die 'worker artifact source is not empty before build namespace'
  write_web_regression_verifier "$verifier"
  printf '%q ' "$node_bin" --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter json --reporter-option 'output=<worker-record>' --timeout 10000 --exit tests/archive-reader.test.js > "$ROOT_RECORDS/web-archive-reader-command.txt"
  printf '\n' >> "$ROOT_RECORDS/web-archive-reader-command.txt"
  cat > "$driver" <<'BUILDDRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail; IFS=$'\n\t'; umask 077
if [[ "${1:-}" != --worker ]]; then
  [[ "$EUID" -eq 0 ]] || exit 51
  /usr/bin/mount --make-rprivate /
  source_identity="$(/usr/bin/stat -Lc '%d:%i' -- "$WORKER_ARTIFACTS")"
  host_target_identity="$(/usr/bin/stat -Lc '%d:%i' -- "$RUN/artifacts")"
  [[ "$source_identity" != "$host_target_identity" ]] || exit 51
  /usr/bin/mount --bind "$WORKER_ARTIFACTS" "$RUN/artifacts"
  [[ "$(/usr/bin/stat -Lc '%d:%i' -- "$RUN/artifacts")" == "$source_identity" ]] || exit 51
  exec /usr/bin/setpriv --reuid="$H06_WORKER_UID" --regid="$H06_WORKER_GID" --clear-groups --no-new-privs /bin/bash "$0" --worker
fi
[[ "$EUID" -eq "$H06_WORKER_UID" ]] || exit 51
[[ -w "$RUN/artifacts" ]] || { echo 'worker cannot write artifactRoot bind view' >&2; exit 51; }
mkdir -p "$OUT_RECORDS" "$OUT_LOGS"
input_before="$(sha256sum "$INPUT" | awk '{print $1}')"
[[ "$input_before" == "$EXPECTED_INPUT_SHA" ]] || { echo 'release input SHA mismatch at namespace entry' >&2; exit 51; }
python3 - "$INPUT" "$RUN/artifacts" <<'PYARTROOT'
import json,os,sys
path,expected=sys.argv[1:]
with open(path,encoding='utf-8') as stream: data=json.load(stream)
if data.get('artifactRoot')!=expected: raise SystemExit('release input artifactRoot is not the host logical path')
if os.path.realpath(data['artifactRoot'])!=os.path.realpath(expected): raise SystemExit('release input artifactRoot normalization mismatch')
PYARTROOT
printf 'BUILD_NETWORK_NAMESPACE=HOST_NETWORK_ALLOWED_FOR_DEPENDENCY_RESOLUTION\nBUILD_MOUNT_NAMESPACE=unshare_-m_-p_--fork_--kill-child\nARTIFACT_BIND_LOGICAL_PATH=%s\nARTIFACT_BIND_SOURCE=%s\nRELEASE_INPUT=%s\nRELEASE_INPUT_SHA256_BEFORE=%s\n' "$RUN/artifacts" "$WORKER_ARTIFACTS" "$INPUT" "$input_before" > "$OUT_RECORDS/artifact-lifecycle.txt"
worker_path="$H06_JDK_ROOT/bin:$H06_NODE_ROOT/bin:/usr/bin:/bin"
env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$worker_path" VITE_API_BASE_URL="$VITE_API_BASE_URL" VITE_OAUTH_CLIENT_ID="$VITE_OAUTH_CLIENT_ID" \
  /bin/bash "$H06_RELEASE_ROOT/build-api.sh" --input "$INPUT" > "$OUT_LOGS/build-api.log" 2>&1
env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$worker_path" VITE_API_BASE_URL="$VITE_API_BASE_URL" VITE_OAUTH_CLIENT_ID="$VITE_OAUTH_CLIENT_ID" \
  /bin/bash "$H06_RELEASE_ROOT/build-web.sh" --input "$INPUT" > "$OUT_LOGS/build-web.log" 2>&1
mocha_json="$OUT_RECORDS/web-archive-reader-mocha.json"; web_log="$OUT_LOGS/web-archive-reader-test.log"; versions="$OUT_RECORDS/web-runtime-versions.txt"
[[ "$(sha256sum "$WEB_TEST_FILE" | awk '{print $1}')" == "$WEB_TEST_SHA" ]] || exit 52
(
 cd "$WEB_WORKTREE"
 env HOME="$RUN/worker/home" PATH="$worker_path" "$NODE_BIN" --import tsx ./node_modules/mocha/bin/mocha.js --no-config --require ./tests/setup.js --reporter json --reporter-option "output=$mocha_json" --timeout 10000 --exit tests/archive-reader.test.js
) > "$web_log" 2>&1
"$NODE_BIN" --version > "$versions"; "$NODE_BIN" "$NPM_CLI" --version >> "$versions"
[[ "$(sha256sum "$WEB_TEST_FILE" | awk '{print $1}')" == "$WEB_TEST_SHA" ]] || exit 52
"$WEB_TEST_VERIFIER" "$mocha_json" "$web_log" "$WEB_TEST_FILE" "$WEB_TEST_SHA" "$WEB_HEAD" "$WEB_TREE" "$NODE_BIN" "$NPM_CLI" "$versions" > "$OUT_RECORDS/web-archive-reader-regression.json"
env HOME="$RUN/worker/home" GRADLE_USER_HOME="$RUN/worker/gradle-home" JAVA_HOME="$H06_JDK_ROOT" PATH="$worker_path" CYF_RELEASE_VERIFY_PROFILE=archive-h06 \
  /bin/bash "$H06_RELEASE_ROOT/verify-release.sh" --input "$INPUT" > "$OUT_LOGS/verify-release.log" 2>&1
input_after="$(sha256sum "$INPUT" | awk '{print $1}')"
[[ "$input_after" == "$input_before" && "$input_after" == "$EXPECTED_INPUT_SHA" ]] || { echo 'release input changed during build/verify namespace' >&2; exit 53; }
printf 'RELEASE_INPUT_SHA256_AFTER=%s\nSINGLE_INPUT_BYTE_IDENTITY=PASS\nWORKER_VERIFY_RELEASE=PASS\nVERIFY_RECORD_STAGED_UNDER_BIND=PASS\n' "$input_after" >> "$OUT_RECORDS/artifact-lifecycle.txt"
sync -f "$RUN/artifacts" 2>/dev/null || true
BUILDDRIVER
  chown root:root "$driver"; chmod 0555 "$driver"
  seal_worker_driver "$driver"
  /usr/bin/unshare -m -p --fork --kill-child=KILL --mount-proc -- env \
    RUN="$RUN" INPUT="$input" EXPECTED_INPUT_SHA="$input_sha" WORKER_ARTIFACTS="$WORKER_ARTIFACTS" OUT_RECORDS="$build_records" OUT_LOGS="$build_logs" \
    H06_WORKER_UID="$H06_WORKER_UID" H06_WORKER_GID="$H06_WORKER_GID" H06_RELEASE_ROOT="$H06_RELEASE_ROOT" H06_JDK_ROOT="$H06_JDK_ROOT" H06_NODE_ROOT="$H06_NODE_ROOT" \
    API_WORKTREE="$API_STAGED" WEB_WORKTREE="$WEB_STAGED" WEB_HEAD="$WEB_HEAD" WEB_TREE="$WEB_TREE" WEB_TEST_FILE="$test_file" WEB_TEST_SHA="$expected_test_sha" \
    NODE_BIN="$node_bin" NPM_CLI="$npm_cli" WEB_TEST_VERIFIER="$verifier" VITE_API_BASE_URL="$VITE_API_BASE_URL" VITE_OAUTH_CLIENT_ID="$VITE_OAUTH_CLIENT_ID" \
    /bin/bash "$driver" > "$ROOT_LOGS/build-namespace-driver.log" 2>&1
  pgrep -u "$H06_WORKER_UID" >/dev/null 2>&1 && die 'UID61006 remained active after build/verify namespace'
  [[ "$(sha256sum "$input" | awk '{print $1}')" == "$input_sha" ]] || die 'release input changed after build/verify namespace exit'
  [[ -z "$(find "$RUN/artifacts" -mindepth 1 -print -quit)" ]] || die 'worker wrote host root-only artifact target outside namespace'
  h06_import_worker_output "$build_records" "$ROOT_RECORDS/build-verified-worker" "$H06_WORKER_UID" "$H06_WORKER_GID" > "$ROOT_RECORDS/build-output-import.txt"
  h06_import_worker_output "$build_logs" "$ROOT_LOGS/build-verified-worker" "$H06_WORKER_UID" "$H06_WORKER_GID" >> "$ROOT_RECORDS/build-output-import.txt"
  python3 - "$RUN/artifacts" <<'PYRMDIR'
import os,sys
os.rmdir(sys.argv[1])
PYRMDIR
  h06_import_worker_output "$WORKER_ARTIFACTS" "$RUN/artifacts" "$H06_WORKER_UID" "$H06_WORKER_GID" > "$ROOT_RECORDS/artifact-import.txt"
  find "$RUN/artifacts" -type f -exec chmod 0444 {} +
  find "$RUN/artifacts" -type d -exec chmod 0555 {} +
  "$verifier" "$ROOT_RECORDS/build-verified-worker/web-archive-reader-mocha.json" "$ROOT_LOGS/build-verified-worker/web-archive-reader-test.log" "$test_file" "$expected_test_sha" "$WEB_HEAD" "$WEB_TREE" "$node_bin" "$npm_cli" "$ROOT_RECORDS/build-verified-worker/web-runtime-versions.txt" > "$ROOT_RECORDS/web-archive-reader-regression.json"
  cmp -s "$ROOT_RECORDS/build-verified-worker/web-archive-reader-regression.json" "$ROOT_RECORDS/web-archive-reader-regression.json" || die 'root Web regression validation differs from worker namespace result'
  grep -Fxq "RELEASE_INPUT_SHA256_BEFORE=$input_sha" "$ROOT_RECORDS/build-verified-worker/artifact-lifecycle.txt" || die 'worker lifecycle evidence lacks input SHA before'
  grep -Fxq "RELEASE_INPUT_SHA256_AFTER=$input_sha" "$ROOT_RECORDS/build-verified-worker/artifact-lifecycle.txt" || die 'worker lifecycle evidence lacks identical input SHA after'
  grep -Fxq 'BUILD_NETWORK_NAMESPACE=HOST_NETWORK_ALLOWED_FOR_DEPENDENCY_RESOLUTION' "$ROOT_RECORDS/build-verified-worker/artifact-lifecycle.txt" || die 'build network policy evidence is missing'
  root_verify_imported_release "$input_sha"
  assert_candidate POST_BUILD_API "$API_STAGED" "$API_REF" "$API_HEAD" "$API_TREE" "$ROOT_RECORDS/post-build-api-pin.txt"
  assert_candidate POST_BUILD_WEB "$WEB_STAGED" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$ROOT_RECORDS/post-build-web-pin.txt"
  verify_archive_artifact
  local api="$RUN/artifacts/api/cyf-api-$API_HEAD-$API_TREE.jar"
  local web="$RUN/artifacts/web/cyf-web-$WEB_HEAD-$WEB_TREE.tar.gz"
  python3 - "$api.json" "$web.json" "$API_HEAD" "$API_TREE" "$WEB_HEAD" "$WEB_TREE" "$input" "$input_sha" > "$ROOT_RECORDS/runtime-artifact-binding.json" <<'PYBIND'
import hashlib,json,pathlib,sys
ap,wp,ah,at,wh,wt,input_path,input_sha=sys.argv[1:]; a=json.load(open(ap)); w=json.load(open(wp))
for obj,head,tree in ((a,ah,at),(w,wh,wt)):
 if obj.get('sourceHead')!=head or obj.get('sourceTree')!=tree: raise SystemExit('artifact metadata source pin mismatch')
 if obj.get('releaseInputSha256')!=input_sha: raise SystemExit('artifact metadata release input SHA mismatch')
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
actual_api=sha(ap[:-5]); actual_web=sha(wp[:-5])
if sha(input_path)!=input_sha: raise SystemExit('release input bytes changed after root verification')
if a.get('artifactSha256')!=actual_api or w.get('artifactSha256')!=actual_web: raise SystemExit('artifact bytes do not match pinned metadata')
print(json.dumps({'result':'PASS','releaseInput':{'path':input_path,'sha256':input_sha,'singleByteIdentity':True,'artifactRoot':str(pathlib.Path(ap).parents[1])},'api':{'head':ah,'tree':at,'artifactSha256':a['artifactSha256'],'actualSha256':actual_api},'web':{'head':wh,'tree':wt,'artifactSha256':w['artifactSha256'],'actualSha256':actual_web},'webBuildApiOrigin':'https://api.h06.invalid:18443'},sort_keys=True,indent=2))
PYBIND
  printf 'ARTIFACTS_PIN_BOUND=PASS\nREAL_BUILD_API=PASS\nREAL_BUILD_WEB=PASS\nREAL_VERIFY_RELEASE=PASS\nWEB_ARCHIVE_READER_38_PASS=PASS\nSINGLE_RELEASE_INPUT_SHA=PASS\nWORKER_HOST_ARTIFACT_WRITE=DENIED\nWORKER_BIND_ARTIFACT_WRITE=PASS\nWORKER_ARTIFACT_NOFOLLOW_IMPORT=PASS\nROOT_COMMON_RELEASE_RECORD_VERIFY=PASS\nBUILD_NETWORK_NAMESPACE=HOST_NETWORK_ALLOWED_FOR_DEPENDENCY_RESOLUTION\n' > "$ROOT_RECORDS/artifacts-verified.txt"
}

verify_archive_artifact() {
  local api="$RUN/artifacts/api/cyf-api-$API_HEAD-$API_TREE.jar" extract="$RUN/tmp/archive-artifact"
  require_physical_file "$api"; rm -rf "$extract"; mkdir -p "$extract"
  mapfile -t service_entries < <(unzip -Z1 "$api" | grep '^BOOT-INF/lib/jia-chat-service-.*\.jar$')
  ((${#service_entries[@]} == 1)) || die "expected exactly one nested jia-chat-service JAR, found ${#service_entries[@]}"
  unzip -p "$api" "${service_entries[0]}" > "$extract/chat-service.jar"
  mapfile -t starter_entries < <(unzip -Z1 "$api" | grep '^BOOT-INF/lib/jia-chat-starter-.*\.jar$')
  ((${#starter_entries[@]} == 1)) || die "expected exactly one nested jia-chat-starter JAR, found ${#starter_entries[@]}"
  unzip -p "$api" "${starter_entries[0]}" > "$extract/chat-starter.jar"
  unzip -p "$extract/chat-service.jar" "archive/$EDITION_ID/manifest.json" > "$extract/manifest.json"
  unzip -p "$extract/chat-service.jar" "archive/$EDITION_ID/golden-summary.json" > "$extract/golden-summary.json"
  unzip -p "$extract/chat-service.jar" application.properties > "$extract/chat-service.properties"
  unzip -p "$extract/chat-starter.jar" application-dev.properties > "$extract/chat-starter-dev.properties"
  for profile in dev grey prod; do unzip -p "$api" "BOOT-INF/classes/application-$profile.properties" > "$extract/starter-$profile.properties"; done
  cmp -s "$extract/manifest.json" "$ROOT/specs/archive-pavilion-reader-mvp/content/manifest.json" || die 'artifact manifest differs byte-for-byte'
  cmp -s "$extract/golden-summary.json" "$ROOT/specs/archive-pavilion-reader-mvp/content/golden-summary.json" || die 'artifact golden differs byte-for-byte'
  ! /usr/bin/grep -R -n -E '^archive\.(reader|question)\.enabled=true$' "$extract" || die 'artifact contains archive default true'
  local reader_false_files=0 flag_file
  while IFS= read -r -d '' flag_file; do
    if /usr/bin/grep -q -E '^archive\.reader\.enabled=false$' "$flag_file"; then
      ((reader_false_files += 1))
    fi
  done < <(/usr/bin/find "$extract" -type f -print0)
  ((reader_false_files >= 4)) || die 'reader default false is incomplete in packaged profiles'
  /usr/bin/grep -q -E '^archive\.question\.enabled=false$' "$extract/chat-service.properties" || die 'service question default false missing'
  /usr/bin/grep -q -E '^archive\.question\.enabled=false$' "$extract/chat-starter-dev.properties" || die 'starter question default false missing'
  sha256sum "$api" "$extract/chat-service.jar" "$extract/chat-starter.jar" "$extract/manifest.json" "$extract/golden-summary.json" > "$ROOT_RECORDS/archive-artifact-digests.txt"
  printf 'NESTED_CHAT_SERVICE_COUNT=1\nNESTED_CHAT_STARTER_COUNT=1\nREADER_DEFAULT_FALSE=PASS\nQUESTION_DEFAULT_FALSE=PASS\n' > "$ROOT_RECORDS/archive-artifact-flags.txt"
}

write_runtime_probe() {
  cat > "$RUN/tmp/runtime-probe.py" <<'PY'
import concurrent.futures,hashlib,json,pathlib,ssl,subprocess,sys,threading,time,urllib.error,urllib.parse,urllib.request,uuid
phase,api,ca,token_dir,out,mysql_bin,mysql_socket,database=sys.argv[1:]; api=api.rstrip('/'); out=pathlib.Path(out); ctx=ssl.create_default_context(cafile=ca)
if phase not in ('positive','negative'): raise SystemExit('runtime probe phase must be positive or negative')
expected={'a_a':('h06-owner-a','h06-client-a'),'a_b':('h06-owner-a','h06-client-b'),'b_a':('h06-owner-b','h06-client-a'),'b_b':('h06-owner-b','h06-client-b')}
tokens={k:pathlib.Path(token_dir,k+'.jwt').read_text().strip() for k in expected}
tables=['archive_reader_progress','archive_bookmark','archive_note','archive_idempotency','archive_question','archive_question_mutation','archive_question_event','archive_outbox']
def req(path,token=None,method='GET',body=None,headers=None,expect=(200,),read_limit=1048576):
 h={'Accept':'application/json',**(headers or {})}; data=None
 if token: h['Authorization']='Bearer '+token
 if body is not None: data=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode(); h['Content-Type']='application/json'
 r=urllib.request.Request(api+path,data=data,headers=h,method=method)
 try:
  with urllib.request.urlopen(r,context=ctx,timeout=30) as x: status=x.status; raw=x.read(read_limit)
 except urllib.error.HTTPError as e: status=e.code; raw=e.read(read_limit)
 if status not in expect: raise SystemExit('%s %s: status=%s expected=%s body=%r'%(method,path,status,expect,raw[:400]))
 try: value=json.loads(raw) if raw else None
 except Exception: value=None
 if isinstance(value,dict) and 'data' in value: value=value['data']
 return status,value
def mysql_query(sql,schema=database):
 command=[mysql_bin,'--protocol=socket','--socket='+mysql_socket,'-uroot','-N','-B']
 if schema: command.append(schema)
 command.extend(['-e',sql]); result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if result.returncode: raise SystemExit('snapshot mysql failed: '+result.stderr.decode(errors='replace')[-1000:])
 return result.stdout
def snapshot(label):
 index=[]
 for table in tables:
  cols=mysql_query("SELECT GROUP_CONCAT(CONCAT('IF(`',COLUMN_NAME,'` IS NULL,0x7e4e554c4c7e,HEX(CAST(`',COLUMN_NAME,'` AS BINARY)))') ORDER BY ORDINAL_POSITION SEPARATOR ',') FROM COLUMNS WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s'"%(database,table),'information_schema').decode().strip()
  order=mysql_query("SELECT GROUP_CONCAT(CONCAT('`',COLUMN_NAME,'`') ORDER BY SEQ_IN_INDEX SEPARATOR ',') FROM STATISTICS WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s' AND INDEX_NAME='PRIMARY'"%(database,table),'information_schema').decode().strip() or '1'
  if not cols: raise SystemExit('snapshot table unavailable: '+table)
  rows=mysql_query('SELECT CONCAT_WS(0x09,%s) FROM `%s` ORDER BY %s'%(cols,table,order))
  count=0 if not rows else len(rows.splitlines()); index.append({'table':table,'tupleCount':count,'contentSha256':hashlib.sha256(rows).hexdigest()})
 raw=json.dumps(index,sort_keys=True,separators=(',',':')).encode(); return {'label':label,'tables':index,'indexSha256':hashlib.sha256(raw).hexdigest()}
def guarded(case,operation,records):
 before=snapshot(case+'-before'); result=operation(); after=snapshot(case+'-after')
 if before['indexSha256']!=after['indexSha256'] or before['tables']!=after['tables']: raise SystemExit('zero-write snapshot changed for '+case)
 records.append({'case':case,'before':before,'after':after,'status':result[0] if isinstance(result,tuple) else 'PASS'})
 return result
def parse_sse(stream,stop_terminal=True):
 frames=[]; frame={}; terminal_at=None
 while True:
  raw=stream.readline()
  if not raw: break
  line=raw.decode().rstrip('\r\n')
  if not line:
   if frame:
    frame['receivedAtNs']=int(time.monotonic()*1000000000); frames.append(frame)
    typ=frame.get('event')
    if stop_terminal and typ in ('QUESTION_SUCCEEDED','QUESTION_FAILED_FINAL'): terminal_at=frame['receivedAtNs']; break
    frame={}
   continue
  if line.startswith('event:'): frame['event']=line[6:].strip()
  elif line.startswith('id:'): frame['id']=line[3:].strip()
  elif line.startswith('data:'):
   try: frame['data']=json.loads(line[5:].strip())
   except Exception: frame['data']=None
 return frames,terminal_at
def validate_sequence(frames):
 persisted=[f for f in frames if f.get('event')!='resync_required' and f.get('event')]
 values=[]
 for frame in persisted:
  raw=frame.get('id',''); data_sequence=str((frame.get('data') or {}).get('sequence',''))
  if not (raw=='0' or (raw and raw[0] in '123456789' and raw.isdigit())) or raw!=data_sequence: raise SystemExit('SSE id/data.sequence is not canonical/equal: '+repr(frame))
  value=int(raw)
  if value<0 or value>9223372036854775807: raise SystemExit('SSE sequence outside signed BIGINT: '+raw)
  values.append(value)
 if len(values)<3 or any(value<=values[index-1] for index,value in enumerate(values) if index): raise SystemExit('SSE sequence is not strictly increasing: '+repr(values))
 return [str(value) for value in values]
def live_sse(path,token,submit):
 opened=threading.Event(); proceed=threading.Event(); result={}; failure=[]
 def consume():
  try:
   request=urllib.request.Request(api+path,headers={'Authorization':'Bearer '+token,'Accept':'text/event-stream','Last-Event-ID':'0'})
   with urllib.request.urlopen(request,context=ctx,timeout=60) as stream:
    result['status']=stream.status; result['contentType']=stream.headers.get('Content-Type',''); result['openedAtNs']=int(time.monotonic()*1000000000); opened.set()
    if not proceed.wait(15): raise RuntimeError('submit-after-open barrier timed out')
    result['frames'],result['terminalAtNs']=parse_sse(stream)
  except Exception as error: failure.append(error); opened.set()
 thread=threading.Thread(target=consume,daemon=True); thread.start()
 if not opened.wait(15) or failure: raise SystemExit('SSE did not establish before submit: '+repr(failure))
 if result.get('status')!=200 or 'text/event-stream' not in result.get('contentType',''): raise SystemExit('SSE response was not open text/event-stream: '+repr(result))
 result['submitStartedAtNs']=int(time.monotonic()*1000000000); submit(); result['submitCompletedAtNs']=int(time.monotonic()*1000000000); proceed.set(); thread.join(60)
 if thread.is_alive() or failure: raise SystemExit('live SSE failed: '+repr(failure))
 types=[f.get('event') for f in result['frames']]; sequences=validate_sequence(result['frames'])
 if not ('QUESTION_QUEUED' in types and 'QUESTION_RUNNING' in types and 'QUESTION_SUCCEEDED' in types): raise SystemExit('SSE success sequence incomplete: '+repr(types))
 if not (result['openedAtNs']<=result['submitStartedAtNs']<=result['submitCompletedAtNs']<=(result['terminalAtNs'] or 0)): raise SystemExit('SSE open/submit/terminal ordering failed: '+repr(result))
 return {'types':types,'sequenceIds':sequences,'terminal':'QUESTION_SUCCEEDED','liveStreamOpenedBeforeSubmitAndTerminal':True,'openedAtNs':str(result['openedAtNs']),'submitStartedAtNs':str(result['submitStartedAtNs']),'terminalAtNs':str(result['terminalAtNs'])}
state_path=out/'probe-state.json'
if phase=='positive':
 matrix=[]; created={}; anchors={}; sse={}; positive_count=0
 for key,token in tokens.items():
  _,catalog=req('/archive/v1/catalog',token); edition=catalog['activeEdition']; eid=edition['editionId']; chapter=edition['chapters'][0]
  _,content=req('/archive/v1/editions/%s/chapters/%s'%(urllib.parse.quote(eid),urllib.parse.quote(chapter['blockId'])),token)
  p=content['paragraphs'][0]; progress_offset=list(expected).index(key)*3; loc={'editionManifestSha256':edition['manifestSha256'],'blockType':'CHAPTER','blockId':content['blockId'],'paragraphId':p['paragraphId'],'byteOffset':progress_offset,'paragraphSha256':p['sha256']}
  raw=p['text'].encode()[:120]
  while raw:
   try: raw.decode(); break
   except UnicodeDecodeError: raw=raw[:-1]
  anchor={'editionManifestSha256':edition['manifestSha256'],'blockType':'CHAPTER','blockId':content['blockId'],'segments':[{'paragraphId':p['paragraphId'],'startByte':0,'endByte':len(raw),'paragraphSha256':p['sha256']}],'selectionSha256':hashlib.sha256(raw).hexdigest()}; anchors[key]=anchor
  progress_body={'expectedVersion':'0','location':loc,'markCompleted':False}; req('/archive/v1/me/progress/'+eid,token,'PUT',progress_body,{'Idempotency-Key':str(uuid.uuid4())},(200,201)); _,progress=req('/archive/v1/me/progress/'+eid,token)
  bid=str(uuid.uuid4()); bookmark_body={'expectedVersion':'0','editionId':eid,'location':loc}; req('/archive/v1/me/bookmarks/'+bid,token,'PUT',bookmark_body,{'Idempotency-Key':str(uuid.uuid4())},(200,201)); req('/archive/v1/me/bookmarks/'+bid,token); req('/archive/v1/me/bookmarks?editionId='+urllib.parse.quote(eid),token)
  nid=str(uuid.uuid4()); note_body={'expectedVersion':'0','editionId':eid,'text':'H06 '+key,'anchor':anchor}; req('/archive/v1/me/notes/'+nid,token,'PUT',note_body,{'Idempotency-Key':str(uuid.uuid4())},(200,201)); req('/archive/v1/me/notes/'+nid,token); req('/archive/v1/me/notes?editionId='+urllib.parse.quote(eid),token)
  qid=str(uuid.uuid4()); question_body={'anchor':anchor,'question':'请概述这段文字。'}; idem=str(uuid.uuid4()); req('/archive/v1/me/questions/'+qid,token,'PUT',question_body,{'Idempotency-Key':idem},(200,201,202))
  sse[key]=live_sse('/archive/v1/me/questions/'+qid+'/events',token,lambda: req('/archive/v1/me/questions/'+qid,token,'PUT',question_body,{'Idempotency-Key':idem},(200,201,202)))
  _,terminal=req('/archive/v1/me/questions/'+qid,token)
  if terminal.get('status')!='SUCCEEDED' or terminal.get('responder')!={'id':'archive-clerk-v1','displayName':'案卷书吏','mode':'fallback'}: raise SystemExit('terminal/responder mismatch for '+key)
  created[key]={'edition':eid,'progress':progress,'bookmark':bid,'bookmarkBody':bookmark_body,'note':nid,'noteBody':note_body,'question':qid,'questionBody':question_body}; positive_count+=1
  matrix.append({'scope':key,'authorizedProgressMutationRead':'PASS','authorizedBookmarkMutationListRead':'PASS','authorizedNoteMutationListRead':'PASS','authorizedQuestionMutationReadLiveSse':'PASS'})
 keys=list(tokens); guarded_records=[]; cross_count=0
 for target in keys:
  item=created[target]
  for actor in [x for x in keys if x!=target]:
   relation='same-identity-wrong-client' if expected[target][0]==expected[actor][0] else 'foreign-identity-'+('same-client' if expected[target][1]==expected[actor][1] else 'wrong-client')
   def check(case,operation,expected_status=None,absent_id=None):
    nonlocal_marker=None
    result=guarded(case,operation,guarded_records)
    if expected_status is not None and result[0]!=expected_status: raise SystemExit(case+' status mismatch')
    if absent_id is not None and absent_id in json.dumps(result[1],ensure_ascii=False): raise SystemExit(case+' list exposed foreign resource')
    return result
   actor_token=tokens[actor]
   _,actor_progress=check('%s-%s-progress-read-isolation'%(target,actor),lambda:req('/archive/v1/me/progress/'+item['edition'],actor_token),(200,))
   if actor_progress==item['progress']: raise SystemExit('progress scope isolation failed')
   checks=[
    ('bookmark-read',lambda:req('/archive/v1/me/bookmarks/'+item['bookmark'],actor_token,expect=(404,)),404,None),
    ('bookmark-mutation',lambda:req('/archive/v1/me/bookmarks/'+item['bookmark'],actor_token,'PUT',item['bookmarkBody'],{'Idempotency-Key':str(uuid.uuid4())},(404,)),404,None),
    ('bookmark-list',lambda:req('/archive/v1/me/bookmarks?editionId='+urllib.parse.quote(item['edition']),actor_token),(200,),item['bookmark']),
    ('note-read',lambda:req('/archive/v1/me/notes/'+item['note'],actor_token,expect=(404,)),404,None),
    ('note-mutation',lambda:req('/archive/v1/me/notes/'+item['note'],actor_token,'PUT',item['noteBody'],{'Idempotency-Key':str(uuid.uuid4())},(404,)),404,None),
    ('note-list',lambda:req('/archive/v1/me/notes?editionId='+urllib.parse.quote(item['edition']),actor_token),(200,),item['note']),
    ('question-read',lambda:req('/archive/v1/me/questions/'+item['question'],actor_token,expect=(404,)),404,None),
    ('question-mutation',lambda:req('/archive/v1/me/questions/'+item['question'],actor_token,'PUT',item['questionBody'],{'Idempotency-Key':str(uuid.uuid4())},(404,)),404,None),
    ('question-sse',lambda:req('/archive/v1/me/questions/'+item['question']+'/events',actor_token,expect=(404,)),404,None)]
   cross_count+=1; matrix.append({'target':target,'actor':actor,'relation':relation,'resource':'progress-read-isolation','status':200})
   for resource,operation,status,absent in checks:
    check('%s-%s-%s'%(target,actor,resource),operation,status,absent); cross_count+=1; matrix.append({'target':target,'actor':actor,'relation':relation,'resource':resource,'status':status or 200})
 expected_cross=len(keys)*(len(keys)-1)*10
 if cross_count!=expected_cross or len(guarded_records)!=expected_cross: raise SystemExit('cross-scope matrix size mismatch actual=%s expected=%s'%(cross_count,expected_cross))
 state_path.write_text(json.dumps({'anchors':anchors,'created':created},ensure_ascii=False,sort_keys=True)+'\n')
 (out/'acl-zero-write-snapshots.json').write_text(json.dumps(guarded_records,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 (out/'acl-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 (out/'question-sse-matrix.json').write_text(json.dumps(sse,sort_keys=True,indent=2)+'\n')
 (out/'runtime-positive.json').write_text(json.dumps({'result':'PASS','positiveScopeCount':positive_count,'crossScopeCaseCount':cross_count,'expectedCrossScopeCaseCount':expected_cross,'perCaseFullSideEffectSnapshot':True},sort_keys=True,indent=2)+'\n')
else:
 state=json.loads(state_path.read_text()); anchors=state['anchors']; created=state['created']; missing_claims=pathlib.Path(token_dir,'missing-claims.jwt').read_text().strip(); valid=tokens['a_a']; hp,sig=valid.rsplit('.',1); tampered=hp+'.'+(('A' if not sig.startswith('A') else 'B')+sig[1:])
 auth_cases=[('missing-auth',None),('malformed','not.a.jwt'),('signature-tampered',tampered),('missing-claims',missing_claims)]; records=[]; neg=[]; eid=created['a_a']['edition']; existing=created['a_a']['question']
 resource_ops=lambda token:[
  ('progress-read',lambda:req('/archive/v1/me/progress/'+eid,token,expect=(401,403))),('progress-write',lambda:req('/archive/v1/me/progress/'+eid,token,'PUT',{'expectedVersion':'0','location':{},'markCompleted':False},{'Idempotency-Key':str(uuid.uuid4())},(401,403))),
  ('bookmark-list',lambda:req('/archive/v1/me/bookmarks?editionId='+urllib.parse.quote(eid),token,expect=(401,403))),('bookmark-write',lambda:req('/archive/v1/me/bookmarks/'+str(uuid.uuid4()),token,'PUT',{'expectedVersion':'0','editionId':eid,'location':{}},{'Idempotency-Key':str(uuid.uuid4())},(401,403))),
  ('note-list',lambda:req('/archive/v1/me/notes?editionId='+urllib.parse.quote(eid),token,expect=(401,403))),('note-write',lambda:req('/archive/v1/me/notes/'+str(uuid.uuid4()),token,'PUT',{'expectedVersion':'0','editionId':eid,'text':'不得写入','anchor':None},{'Idempotency-Key':str(uuid.uuid4())},(401,403))),
  ('question-read',lambda:req('/archive/v1/me/questions/'+existing,token,expect=(401,403))),('question-write',lambda:req('/archive/v1/me/questions/'+str(uuid.uuid4()),token,'PUT',{'anchor':anchors['a_a'],'question':'不得写入'},{'Idempotency-Key':str(uuid.uuid4())},(401,403))),('question-sse',lambda:req('/archive/v1/me/questions/'+existing+'/events',token,expect=(401,403)))]
 for auth_label,token in auth_cases:
  for resource,operation in resource_ops(token):
   status,_=guarded(auth_label+'-'+resource,operation,records); neg.append({'case':auth_label,'resource':resource,'status':status})
 expected_negative=len(auth_cases)*9
 if len(neg)!=expected_negative or len(records)!=expected_negative: raise SystemExit('auth-negative matrix size mismatch')
 legacy_status,legacy=req('/chat/library/search',tokens['a_a'],'POST',{'keyword':'H06不存在关键词'},expect=(200,))
 if legacy not in (None,[]) and not (isinstance(legacy,dict) and not legacy.get('items')): raise SystemExit('legacy ES-down search not graceful-empty')
 (out/'auth-negative-zero-write-snapshots.json').write_text(json.dumps(records,sort_keys=True,indent=2)+'\n')
 (out/'negative-auth.json').write_text(json.dumps(neg,sort_keys=True,indent=2)+'\n')
 (out/'runtime-probe.json').write_text(json.dumps({'result':'PASS','authNegativeCaseCount':len(neg),'expectedAuthNegativeCaseCount':expected_negative,'allResourceFamiliesReadWriteAndSseCovered':True,'perCaseFullSideEffectSnapshot':True,'legacySearchStatus':legacy_status,'legacyGracefulEmpty':True},sort_keys=True,indent=2)+'\n')
PY
}
write_oauth_tools() {
  cat > "$RUN/tmp/get-h06-tokens.py" <<'PY'
import base64,hashlib,json,os,sys
from urllib.parse import parse_qs,urljoin,urlparse,urlencode
import requests
api,redirect,ca,out=sys.argv[1:]; pairs=[('a_a','h06-user-a','h06-pass-a','h06-client-a'),('a_b','h06-user-a','h06-pass-a','h06-client-b'),('b_a','h06-user-b','h06-pass-b','h06-client-a'),('b_b','h06-user-b','h06-pass-b','h06-client-b')]
os.makedirs(out,exist_ok=True)
def b64(v): return base64.urlsafe_b64encode(v).decode().rstrip('=')
def acquire(user,password,client):
 s=requests.Session(); verifier=b64(os.urandom(48)); challenge=b64(hashlib.sha256(verifier.encode()).digest())
 authorize=api+'/oauth2/authorize?'+urlencode({'response_type':'code','client_id':client,'scope':'openid','redirect_uri':redirect,'code_challenge':challenge,'code_challenge_method':'S256','state':'h06'})
 first=s.get(authorize,verify=ca,allow_redirects=False,timeout=20)
 login=s.post(api+'/login',data={'loginType':'password','username':user,'password':password,'redirect_uri':''},verify=ca,allow_redirects=False,timeout=20)
 location=login.headers.get('Location') or first.headers.get('Location') or authorize; code=''
 for _ in range(16):
  target=urljoin(api+'/',location)
  if target.startswith(redirect): code=parse_qs(urlparse(target).query).get('code',[''])[0]; break
  r=s.get(target,verify=ca,allow_redirects=False,timeout=20); location=r.headers.get('Location','')
  if not location: break
 if not code: raise SystemExit(f'authorization code unavailable user={user} client={client}')
 r=s.post(api+'/oauth2/token',data={'grant_type':'authorization_code','code':code,'redirect_uri':redirect,'client_id':client,'code_verifier':verifier},verify=ca,timeout=20); r.raise_for_status(); return r.json()['access_token']
for key,user,password,client in pairs: open(os.path.join(out,key+'.jwt'),'w').write(acquire(user,password,client)+'\n')
r=requests.post(api+'/oauth2/token',data={'grant_type':'client_credentials','scope':'openid'},auth=('h06-claims-probe','h06-claims-secret'),verify=ca,timeout=20); r.raise_for_status(); open(os.path.join(out,'missing-claims.jwt'),'w').write(r.json()['access_token']+'\n')
PY
  cat > "$RUN/tmp/verify-h06-jwt.mjs" <<'JS'
import { createHash, createPublicKey, verify } from 'node:crypto'; import { readFile, writeFile } from 'node:fs/promises'
const [jwksPath,metadataPath,tokenDir,outPath]=process.argv.slice(2); const jwks=JSON.parse(await readFile(jwksPath)); const meta=JSON.parse(await readFile(metadataPath)); const expected={a_a:['h06-owner-a','h06-client-a'],a_b:['h06-owner-a','h06-client-b'],b_a:['h06-owner-b','h06-client-a'],b_b:['h06-owner-b','h06-client-b']}; const evidence={}
const dec=s=>JSON.parse(Buffer.from(s.replace(/-/g,'+').replace(/_/g,'/'),'base64url'))
for (const [key,pair] of Object.entries(expected)) { const token=(await readFile(`${tokenDir}/${key}.jwt`,'utf8')).trim(); const [h,p,s]=token.split('.'); const header=dec(h), claims=dec(p), jwk=jwks.keys.find(x=>x.kid===header.kid); if(!jwk||header.alg!=='RS256'||!verify('RSA-SHA256',Buffer.from(`${h}.${p}`),createPublicKey({key:jwk,format:'jwk'}),Buffer.from(s,'base64url'))) throw new Error(`JWT signature invalid: ${key}`); const now=Math.floor(Date.now()/1000); if(claims.iss!==meta.issuer||claims.exp<=now||claims.iat>now+30||(claims.nbf&&claims.nbf>now+30)) throw new Error(`JWT time/issuer invalid: ${key}`); const aud=Array.isArray(claims.aud)?claims.aud:[claims.aud]; if(!aud.includes(pair[1])||claims.jiacn!==pair[0]||claims.client_id!==pair[1]) throw new Error(`JWT claims invalid: ${key}`); evidence[key]={jiacn:claims.jiacn,client_id:claims.client_id,issuer:claims.iss,audience:aud,expiresAt:claims.exp,tokenSha256:createHash('sha256').update(token).digest('hex'),signature:'PASS'} }
{ const key='missing-claims'; const token=(await readFile(`${tokenDir}/${key}.jwt`,'utf8')).trim(); const [h,p,s]=token.split('.'); const header=dec(h), claims=dec(p), jwk=jwks.keys.find(x=>x.kid===header.kid); if(!jwk||header.alg!=='RS256'||!verify('RSA-SHA256',Buffer.from(`${h}.${p}`),createPublicKey({key:jwk,format:'jwk'}),Buffer.from(s,'base64url'))) throw new Error('missing-claims JWT signature invalid'); const now=Math.floor(Date.now()/1000), aud=Array.isArray(claims.aud)?claims.aud:[claims.aud]; if(claims.iss!==meta.issuer||claims.exp<=now||(claims.nbf&&claims.nbf>now+30)||claims.client_id!=='h06-claims-probe'||!aud.includes('h06-claims-probe')||claims.jiacn!=null) throw new Error('missing-claims JWT validation failed'); evidence[key]={client_id:claims.client_id,jiacn:null,issuer:claims.iss,audience:aud,expiresAt:claims.exp,tokenSha256:createHash('sha256').update(token).digest('hex'),signature:'PASS'} }
await writeFile(outPath,JSON.stringify({result:'PASS',jwksUri:meta.jwks_uri,tokens:evidence},null,2)+'\n')
JS
}

runtime_gate() {
  [[ -x "$CHROME_PATH" && -f "$CHROME_PATH" && ! -L "$CHROME_PATH" ]] || blocked "isolated Chromium unavailable: $CHROME_PATH"
  python3 -c 'import requests' >/dev/null 2>&1 || blocked 'Python requests is required for repo-local OAuth PKCE fixture'
  build_verified_artifacts; write_runtime_probe; write_oauth_tools
  local driver="$RUN/tmp/runtime-driver.sh" api="$RUN/artifacts/api/cyf-api-$API_HEAD-$API_TREE.jar" web="$RUN/artifacts/web/cyf-web-$WEB_HEAD-$WEB_TREE.tar.gz"
  cat > "$RUN/tmp/runtime-isolated-hosts" <<'HOSTS'
127.0.0.1 localhost kit.h06.invalid api.h06.invalid
::1 localhost
HOSTS
  chmod 0444 "$RUN/tmp/runtime-isolated-hosts"
  cat > "$driver" <<'DRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail; IFS=$'\n\t'; umask 077
if [[ "${1:-}" != --worker ]]; then
  source "$LIB"; mount --make-rprivate /; ip link set lo up; [[ -z "$(ip route show)" ]] || exit 30
  mkdir -p "$RUN/runtime/private" "$RUN/runtime/web" "$RUN/runtime/public" "$RUN/browser"
  mount --bind "$RUN/tmp/runtime-isolated-hosts" /etc/hosts
  chmod 0711 "$RUN"; chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$RUN/runtime" "$RUN/browser"
  exec setpriv --reuid="$H06_WORKER_UID" --regid="$H06_WORKER_GID" --clear-groups --no-new-privs /bin/bash "$0" --worker
fi
source "$LIB"; [[ "$EUID" -eq "$H06_WORKER_UID" && -z "$(ip route show)" ]] || exit 30
export H06_STAGE_RECORDS="$OUT_RECORDS" H06_STAGE_LOGS="$OUT_LOGS"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; export NO_PROXY='127.0.0.1,localhost,kit.h06.invalid,api.h06.invalid'; export no_proxy="$NO_PROXY"
REG="$RUN/runtime/private/pids.tsv"; : > "$REG"; cleanup(){ set +e; cp "$REG" "$OUT_RECORDS/runtime-owned-processes.tsv" 2>/dev/null || true; h06_stop_tracked_pids "$REG"; printf 'RUNTIME_TRACKED_PROCESS_CLEANUP=PASS\n' > "$OUT_RECORDS/runtime-cleanup.txt"; h06_safe_remove_run_local "$RUN" "$RUN/runtime/private"; }; trap cleanup EXIT
readlink /proc/self/ns/{mnt,net,pid} > "$OUT_RECORDS/runtime-namespaces.txt"; ip route show > "$OUT_RECORDS/runtime-routes.txt"
h06_start_mysql "$RUN/runtime" "$MYSQL_PORT" cyf_h06_runtime "$REG"
MC="$H06_MYSQL_ROOT/bin/mysql"; S="$H06_MYSQL_SOCKET"; DB="$H06_MYSQL_DATABASE"
$MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/starter/src/test/resources/db/schema.sql"
$MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/chat/jia-chat-mapper/src/test/resources/db/schema.sql"
$MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/agent/jia-agent-mapper/src/main/resources/db/schema.sql"
NOW=$(python3 -c 'import time;print(int(time.time()*1000))')
$MC --protocol=socket --socket="$S" -uroot "$DB" <<SQL
INSERT INTO oauth_client (id,client_id,client_id_issued_at,client_secret,client_name,client_authentication_methods,authorization_grant_types,redirect_uris,post_logout_redirect_uris,scopes,client_settings,token_settings,create_time,update_time,tenant_id,appcn) VALUES
('h06-ca','h06-client-a',CURRENT_TIMESTAMP,NULL,'H06 A','none','authorization_code,refresh_token','https://kit.h06.invalid:18443/oauth2/callback','','openid','{"settings.client.require-proof-key":true,"settings.client.require-authorization-consent":false}','',$NOW,$NOW,'h06','h06-a'),
('h06-cb','h06-client-b',CURRENT_TIMESTAMP,NULL,'H06 B','none','authorization_code,refresh_token','https://kit.h06.invalid:18443/oauth2/callback','','openid','{"settings.client.require-proof-key":true,"settings.client.require-authorization-consent":false}','',$NOW,$NOW,'h06','h06-b'),
('h06-neg','h06-claims-probe',CURRENT_TIMESTAMP,'h06-claims-secret','H06 claims negative','client_secret_basic','client_credentials','','','openid','{}','',$NOW,$NOW,'h06','h06-neg');
INSERT INTO user_info (id,username,password,jiacn,status,create_time,update_time,client_id,tenant_id) VALUES
(90601,'h06-user-a','h06-pass-a','h06-owner-a',1,$NOW,$NOW,'h06-client-a','h06-owner-a'),
(90602,'h06-user-b','h06-pass-b','h06-owner-b',1,$NOW,$NOW,'h06-client-b','h06-owner-b');
SQL
h06_start_redis "$RUN/runtime" "$REDIS_PORT" "$REG"
mkdir -p "$RUN/runtime/web"; tar -xzf "$WEB_ARTIFACT" -C "$RUN/runtime/web"
cat > "$RUN/runtime/private/openssl.cnf" <<'SSL'
[req]
distinguished_name=dn
x509_extensions=v3_ca
prompt=no
[dn]
CN=H06 isolated CA
[v3_ca]
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
SSL
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -keyout "$RUN/runtime/private/ca.key" -out "$RUN/runtime/public/ca.crt" -config "$RUN/runtime/private/openssl.cnf" >/dev/null 2>&1
cat > "$RUN/runtime/private/leaf.cnf" <<'SSL'
[req]
distinguished_name=dn
req_extensions=v3
prompt=no
[dn]
CN=kit.h06.invalid
[v3]
subjectAltName=DNS:kit.h06.invalid,DNS:api.h06.invalid
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
SSL
openssl req -newkey rsa:2048 -nodes -keyout "$RUN/runtime/private/tls.key" -out "$RUN/runtime/private/tls.csr" -config "$RUN/runtime/private/leaf.cnf" >/dev/null 2>&1
openssl x509 -req -in "$RUN/runtime/private/tls.csr" -CA "$RUN/runtime/public/ca.crt" -CAkey "$RUN/runtime/private/ca.key" -CAcreateserial -days 1 -extensions v3 -extfile "$RUN/runtime/private/leaf.cnf" -out "$RUN/runtime/public/tls.crt" >/dev/null 2>&1
SPKI=$(openssl x509 -in "$RUN/runtime/public/ca.crt" -pubkey -noout | openssl pkey -pubin -outform DER | openssl dgst -sha256 -binary | openssl base64 -A); printf '%s\n' "$SPKI" > "$RUN/runtime/public/tls-spki.txt"
ES_PORT="$ES_PORT"; ! ss -lnt | grep -Eq "127\\.0\\.0\\.1:$ES_PORT\\b" || exit 31
cat > "$RUN/runtime/private/isolated.properties" <<EOFPROP
spring.application.name=cyf-h06-isolated
server.address=127.0.0.1
server.port=18018
server.ssl.enabled=false
server.shutdown=graceful
server.forward-headers-strategy=framework
spring.main.banner-mode=off
spring.main.lazy-initialization=false
spring.datasource.type=com.zaxxer.hikari.HikariDataSource
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver
spring.datasource.url=jdbc:mysql://127.0.0.1:$MYSQL_PORT/$DB?useUnicode=true&characterEncoding=utf-8&allowPublicKeyRetrieval=true&useSSL=false
spring.datasource.username=root
spring.datasource.password=
spring.datasource.hikari.minimum-idle=1
spring.datasource.hikari.maximum-pool-size=3
dynamic.datasource.enable=false
spring.data.redis.host=127.0.0.1
spring.data.redis.port=$REDIS_PORT
spring.data.redis.password=h06-redis-secret
spring.session.store-type=none
spring.autoconfigure.exclude=org.springframework.boot.amqp.autoconfigure.RabbitAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpClientAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpToolCallbackAutoConfiguration
spring.ai.mcp.client.enabled=false
spring.ai.mcp.client.toolcallback.enabled=false
spring.ai.model.chat=openai
spring.ai.model.embedding=openai
spring.ai.openai.api-key=h06-isolated-key
spring.ai.openai.base-url=http://127.0.0.1:19999/v1
spring.ai.openai.chat.options.model=h06-isolated
spring.ai.openai.embedding.options.model=h06-isolated
spring.elasticsearch.uris=http://127.0.0.1:$ES_PORT
spring.elasticsearch.connection-timeout=1s
spring.elasticsearch.socket-timeout=1s
management.health.elasticsearch.enabled=false
management.endpoints.web.exposure.include=health
management.endpoint.health.show-details=always
management.health.ldap.enabled=false
management.health.rabbit.enabled=false
camunda.bpm.enabled=false
jia.chat.service.websocket.enable=false
spring.task.scheduling.enabled=false
jia.file.path=$RUN/runtime/files
mat.web.realpath=$RUN/runtime/material
cors.allowed.origin.patterns=https://kit.h06.invalid:18443
oauth.resource.uris[0]=/archive/**
oauth.resource.uris[1]=/chat/**
archive.reader.enabled=true
archive.question.enabled=true
archive.reader.allowed-scopes[0].tenant-id=h06-owner-a
archive.reader.allowed-scopes[0].client-id=h06-client-a
archive.reader.allowed-scopes[1].tenant-id=h06-owner-a
archive.reader.allowed-scopes[1].client-id=h06-client-b
archive.reader.allowed-scopes[2].tenant-id=h06-owner-b
archive.reader.allowed-scopes[2].client-id=h06-client-a
archive.reader.allowed-scopes[3].tenant-id=h06-owner-b
archive.reader.allowed-scopes[3].client-id=h06-client-b
logging.file.name=$OUT_LOGS/runtime-api.log
EOFPROP
chmod 0600 "$RUN/runtime/private/isolated.properties"
for x in archive.reader.enabled=true archive.question.enabled=true; do grep -Fxq "$x" "$RUN/runtime/private/isolated.properties" || exit 32; done
[[ $(grep -c '^archive.reader.allowed-scopes\[[0-3]\]\.tenant-id=' "$RUN/runtime/private/isolated.properties") == 4 ]] || exit 32
"$H06_JDK_ROOT/bin/java" -Xms96m -Xmx384m -jar "$API_ARTIFACT" --spring.config.location="file:$RUN/runtime/private/isolated.properties" > "$OUT_LOGS/runtime-api-stdout.log" 2>&1 & APP=$!; h06_track_pid "$REG" api "$APP" "$H06_JDK_ROOT/bin/java"
for _ in {1..720}; do code=$(curl -sS -o "$OUT_RECORDS/runtime-health.json" -w '%{http_code}' http://127.0.0.1:18018/actuator/health 2>/dev/null || true); [[ "$code" == 200 ]] && break; sleep .25; done
[[ "$code" == 200 ]] || { tail -200 "$OUT_LOGS/runtime-api-stdout.log" >&2; exit 33; }
cat > "$RUN/runtime/private/nginx.conf" <<EOFNG
pid $RUN/runtime/private/nginx.pid; error_log $OUT_LOGS/runtime-nginx-error.log notice; daemon off; master_process off;
events { worker_connections 256; }
http { include $H06_NGINX_ROOT/conf/mime.types; access_log $OUT_LOGS/runtime-nginx-access.log; server { listen 18443 ssl; server_name kit.h06.invalid; ssl_certificate $RUN/runtime/public/tls.crt; ssl_certificate_key $RUN/runtime/private/tls.key; root $RUN/runtime/web; location / { try_files \$uri \$uri/ /index.html; } } server { listen 18443 ssl; server_name api.h06.invalid; ssl_certificate $RUN/runtime/public/tls.crt; ssl_certificate_key $RUN/runtime/private/tls.key; location / { proxy_pass http://127.0.0.1:18018; proxy_http_version 1.1; proxy_set_header Host \$host; proxy_set_header X-Forwarded-Proto https; proxy_set_header X-Forwarded-Port 18443; proxy_buffering off; proxy_cache off; proxy_read_timeout 120s; add_header X-Accel-Buffering no always; } } }
EOFNG
"$H06_NGINX_ROOT/sbin/nginx" -t -c "$RUN/runtime/private/nginx.conf" -p "$RUN/runtime" > "$OUT_RECORDS/nginx-test.txt" 2>&1
"$H06_NGINX_ROOT/sbin/nginx" -c "$RUN/runtime/private/nginx.conf" -p "$RUN/runtime" > "$OUT_LOGS/runtime-nginx.log" 2>&1 & NG=$!; h06_track_pid "$REG" nginx "$NG" "$H06_NGINX_ROOT/sbin/nginx"
for _ in {1..120}; do curl --cacert "$RUN/runtime/public/ca.crt" -fsS https://kit.h06.invalid:18443/ >/dev/null 2>&1 && break; sleep .25; done
curl --cacert "$RUN/runtime/public/ca.crt" -fsS https://api.h06.invalid:18443/oauth2/jwks > "$RUN/runtime/public/jwks.json"
curl --cacert "$RUN/runtime/public/ca.crt" -fsS https://api.h06.invalid:18443/.well-known/openid-configuration > "$RUN/runtime/public/openid.json"
python3 "$RUN/tmp/get-h06-tokens.py" https://api.h06.invalid:18443 https://kit.h06.invalid:18443/oauth2/callback "$RUN/runtime/public/ca.crt" "$RUN/runtime/private/tokens"
node "$RUN/tmp/verify-h06-jwt.mjs" "$RUN/runtime/public/jwks.json" "$RUN/runtime/public/openid.json" "$RUN/runtime/private/tokens" "$OUT_RECORDS/token-claims.json"
snapshot_db(){
 local label="$1" dir="$OUT_RECORDS/db-snapshot-$label" table cols order rows count hash
 mkdir -p "$dir"
 for table in archive_reader_progress archive_bookmark archive_note archive_idempotency archive_question archive_question_mutation archive_question_event archive_outbox; do
  cols="$($MC --protocol=socket --socket="$S" -uroot -N -B information_schema -e "SELECT GROUP_CONCAT(CONCAT('IF(\\`',COLUMN_NAME,'\\` IS NULL,0x7e4e554c4c7e,HEX(CAST(\\`',COLUMN_NAME,'\\` AS BINARY)))') ORDER BY ORDINAL_POSITION SEPARATOR ',') FROM COLUMNS WHERE TABLE_SCHEMA='$DB' AND TABLE_NAME='$table'")"
  order="$($MC --protocol=socket --socket="$S" -uroot -N -B information_schema -e "SELECT GROUP_CONCAT(CONCAT('\\`',COLUMN_NAME,'\\`') ORDER BY SEQ_IN_INDEX SEPARATOR ',') FROM STATISTICS WHERE TABLE_SCHEMA='$DB' AND TABLE_NAME='$table' AND INDEX_NAME='PRIMARY'")"
  [[ -n "$cols" ]] || exit 34; [[ -n "$order" ]] || order=1
  rows="$dir/$table.rows.hex.tsv"; $MC --protocol=socket --socket="$S" -uroot -N -B "$DB" -e "SELECT CONCAT_WS(0x09,$cols) FROM \\`$table\\` ORDER BY $order" > "$rows"
  count=$(wc -l < "$rows"); hash=$(sha256sum "$rows"|awk '{print $1}'); printf '%s\t%s\t%s\n' "$table" "$count" "$hash" >> "$dir/index.tsv"
 done
 sha256sum "$dir/index.tsv" | awk '{print "SNAPSHOT_INDEX_SHA256=" $1}' > "$dir/result.txt"
}
snapshot_db before
$MC --protocol=socket --socket="$S" -uroot -N -B "$DB" -e "SELECT COUNT(*) FROM archive_reader_progress; SELECT COUNT(*) FROM archive_bookmark; SELECT COUNT(*) FROM archive_note; SELECT COUNT(*) FROM archive_question" > "$OUT_RECORDS/counts-before.txt"
awk 'NF!=1 || $1!=0 {exit 1}' "$OUT_RECORDS/counts-before.txt" || exit 34
mkdir -p "$OUT_RECORDS/runtime-probe"
python3 "$RUN/tmp/runtime-probe.py" positive https://api.h06.invalid:18443 "$RUN/runtime/public/ca.crt" "$RUN/runtime/private/tokens" "$OUT_RECORDS/runtime-probe" "$MC" "$S" "$DB"
snapshot_db after-positive
$MC --protocol=socket --socket="$S" -uroot -N -B "$DB" -e "SELECT COUNT(*) FROM archive_reader_progress; SELECT COUNT(*) FROM archive_bookmark; SELECT COUNT(*) FROM archive_note; SELECT COUNT(*) FROM archive_question" > "$OUT_RECORDS/counts-after-positive.txt"
awk 'NF!=1 || $1!=4 {exit 1}' "$OUT_RECORDS/counts-after-positive.txt" || exit 34
$MC --protocol=socket --socket="$S" -uroot -N -B "$DB" -e "SELECT tenant_id,client_id,owner_jiacn,COUNT(*) FROM archive_question GROUP BY tenant_id,client_id,owner_jiacn ORDER BY 1,2,3" > "$OUT_RECORDS/db-owner-matrix.txt"
[[ $(wc -l < "$OUT_RECORDS/db-owner-matrix.txt") == 4 ]] || exit 34
python3 "$RUN/tmp/runtime-probe.py" negative https://api.h06.invalid:18443 "$RUN/runtime/public/ca.crt" "$RUN/runtime/private/tokens" "$OUT_RECORDS/runtime-probe" "$MC" "$S" "$DB"
snapshot_db after-negative
cmp -s "$OUT_RECORDS/db-snapshot-after-positive/index.tsv" "$OUT_RECORDS/db-snapshot-after-negative/index.tsv" || exit 35
for table in archive_reader_progress archive_bookmark archive_note archive_idempotency archive_question archive_question_mutation archive_question_event archive_outbox; do cmp -s "$OUT_RECORDS/db-snapshot-after-positive/$table.rows.hex.tsv" "$OUT_RECORDS/db-snapshot-after-negative/$table.rows.hex.tsv" || exit 35; done
$MC --protocol=socket --socket="$S" -uroot -N -B "$DB" -e "SELECT COUNT(*) FROM archive_reader_progress; SELECT COUNT(*) FROM archive_bookmark; SELECT COUNT(*) FROM archive_note; SELECT COUNT(*) FROM archive_question" > "$OUT_RECORDS/counts-after-negative.txt"
cmp -s "$OUT_RECORDS/counts-after-positive.txt" "$OUT_RECORDS/counts-after-negative.txt" || exit 35
printf 'AUTH_NEGATIVE_DB_ZERO_WRITE=PASS\n' > "$OUT_RECORDS/auth-zero-write.txt"
TOKEN="$RUN/runtime/private/tokens/a_a.jwt"
mkdir -p "$RUN/browser"; chmod 0700 "$RUN/browser" "$RUN/runtime/private" "$RUN/runtime/private/tokens"; chmod 0400 "$TOKEN"; chmod 0444 "$RUN/runtime/public/ca.crt"
env TMPDIR="$RUN/runtime/private" H06_FRONTEND_URL=https://kit.h06.invalid:18443 H06_BACKEND_URL=https://api.h06.invalid:18443 H06_BROWSER_EVIDENCE_DIR="$BROWSER_RECORDS" H06_BROWSER_TOKEN_FILE="$TOKEN" H06_BROWSER_CA_FILE="$RUN/runtime/public/ca.crt" H06_BROWSER_CERT_SPKI="$SPKI" H06_ISOLATED_HOSTS_FILE="$RUN/tmp/runtime-isolated-hosts" H06_CHROME_PATH="$CHROME_PATH" H06_CHROME_LAUNCHER_SHA256="$H06_CHROMIUM_EXEC_SHA256" H06_CHROME_EXECUTABLE_SHA256="$H06_CHROMIUM_EXEC_SHA256" "$H06_NODE_ROOT/bin/node" "$BROWSER"
printf 'RUNTIME_GATE=PASS\nFOUR_SCOPES=PASS\nACL_MATRIX_COUNTS=DYNAMICALLY_ASSERTED\nPER_CASE_FULL_SIDE_EFFECT_SNAPSHOT=PASS\nAUTH_ZERO_WRITE=PASS\nJWT_SIGNATURE_ISSUER_AUDIENCE_EXPIRY=PASS\nES_DOWN_NAMESPACE_LOCAL=PASS\nPRODUCTION_DEPENDENCY_ROUTE=NONE\n' > "$OUT_RECORDS/runtime-result.txt"
ss -lntp > "$OUT_RECORDS/runtime-listeners.txt"
DRIVER
  seal_worker_driver "$driver"
  local mysql_port=$((24000 + RANDOM % 8000)) redis_port=$((34000 + RANDOM % 8000)) es_port=$((43000 + RANDOM % 8000))
  unshare -m -n -p --fork --kill-child=KILL --mount-proc -- env RUN="$RUN" OUT_RECORDS="$WORKER_OUTPUT/runtime/records" OUT_LOGS="$WORKER_OUTPUT/runtime/logs" BROWSER_RECORDS="$WORKER_OUTPUT/browser/records" LIB="$LIB" API_WORKTREE="$API_STAGED" WEB_WORKTREE="$WEB_STAGED" API_ARTIFACT="$api" WEB_ARTIFACT="$web" MYSQL_PORT="$mysql_port" REDIS_PORT="$redis_port" ES_PORT="$es_port" CHROME_PATH="$CHROME_PATH" BROWSER="$BROWSER" H06_WORKER_UID="$H06_WORKER_UID" H06_WORKER_GID="$H06_WORKER_GID" H06_MYSQL_ROOT="$H06_MYSQL_ROOT" H06_REDIS_ROOT="$H06_REDIS_ROOT" H06_JDK_ROOT="$H06_JDK_ROOT" H06_NGINX_ROOT="$H06_NGINX_ROOT" H06_CHROMIUM_EXEC_SHA256="$H06_CHROMIUM_EXEC_SHA256" /bin/bash "$driver"
  log 'runtime/API/OAuth/browser gate PASS'
}

release_gate() {
  build_verified_artifacts
  local driver="$RUN/tmp/release-driver.sh" api="$RUN/artifacts/api/cyf-api-$API_HEAD-$API_TREE.jar"
  write_oauth_tools; write_runtime_probe
  cat > "$RUN/tmp/OldHealth.java" <<'JAVAOLD'
import com.sun.net.httpserver.*;import java.net.*;import java.nio.charset.StandardCharsets;public final class OldHealth{static void send(HttpExchange x,int c,String s)throws Exception{byte[]b=s.getBytes(StandardCharsets.UTF_8);x.getResponseHeaders().set("Content-Type","application/json");x.sendResponseHeaders(c,b.length);x.getResponseBody().write(b);x.close();}public static void main(String[]a)throws Exception{HttpServer s=HttpServer.create(new InetSocketAddress("127.0.0.1",18018),8);s.createContext("/actuator/health",x->send(x,200,"{\"status\":\"UP\",\"source\":\"h06-old\"}"));s.createContext("/chat/library/search",x->send(x,200,"{\"status\":200,\"code\":\"E0\",\"msg\":\"ok\",\"data\":[]}"));s.start();Thread.currentThread().join();}}
JAVAOLD
  printf 'Main-Class: OldHealth\n' > "$RUN/tmp/OLD.MF"
  cat > "$RUN/tmp/old-server.py" <<'PYOLD'
import http.server,json
class H(http.server.BaseHTTPRequestHandler):
 def send(self,status,payload):
  raw=json.dumps(payload,separators=(',',':')).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
 def do_GET(self): self.send(200,{'status':'UP','source':'h06-old'}) if self.path=='/actuator/health' else self.send(404,{'status':404})
 def do_POST(self): self.send(200,{'status':200,'code':'E0','msg':'ok','data':[]}) if self.path=='/chat/library/search' else self.send(404,{'status':404})
 def log_message(self,*args): pass
http.server.ThreadingHTTPServer(('127.0.0.1',18018),H).serve_forever()
PYOLD
  chmod 0444 "$RUN/tmp/OldHealth.java" "$RUN/tmp/OLD.MF" "$RUN/tmp/old-server.py" "$RUN/tmp/get-h06-tokens.py" "$RUN/tmp/verify-h06-jwt.mjs" "$RUN/tmp/runtime-probe.py"
  h06_worker_exec /bin/bash -c 'set -Eeuo pipefail; mkdir -p "$1/baks/legacy-api/releases" "$1/baks/legacy-api/release-records" "$1/api/logs" "$1/api/tmp" "$1/api/files" "$1/api/material" "$1/web/kit/static" "$1/baks/legacy-web/release-records"; printf "%s\n" "<!doctype html><body>h06-old<script src=\"/static/index-old.js\"></script>" > "$1/web/kit/index.html"; printf "old\n" > "$1/web/kit/static/index-old.js"' h06-worker "$RUN/sandbox"
  chmod 0711 "$RUN"
  cat > "$RUN/tmp/release-hosts" <<'HOSTS'
127.0.0.1 localhost kit.h06.invalid api.h06.invalid
::1 localhost
HOSTS
  : > "$RUN/tmp/release-api.lock"; : > "$RUN/tmp/release-web.lock"
  chmod 0444 "$RUN/tmp/release-hosts"; chmod 0666 "$RUN/tmp/release-api.lock" "$RUN/tmp/release-web.lock"
  cat > "$driver" <<'DRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail; IFS=$'\n\t'; umask 077
if [[ "${1:-}" != --worker ]]; then
 source "$LIB"; mount --make-rprivate /; ip link set lo up; [[ -z "$(ip route show)" ]] || exit 40
 mkdir -p "$RUN/release/private" "$RUN/release/public"
 mount --bind "$RUN/sandbox/api" /home/isp/hosts/cyf/api; mount --bind "$RUN/sandbox/web" /home/isp/hosts/cyf/web; mount --bind "$RUN/sandbox/baks" /home/isp/baks
 mount --bind "$RUN/tmp/release-hosts" /etc/hosts; mount --bind "$RUN/tmp/release-api.lock" /tmp/cyf-release-api.lock; mount --bind "$RUN/tmp/release-web.lock" /tmp/cyf-release-web.lock
 chown -R "$H06_WORKER_UID:$H06_WORKER_GID" "$RUN/release" "$RUN/sandbox"
 exec setpriv --reuid="$H06_WORKER_UID" --regid="$H06_WORKER_GID" --clear-groups --no-new-privs /bin/bash "$0" --worker
fi
source "$LIB"; [[ "$EUID" -eq "$H06_WORKER_UID" && -z "$(ip route show)" ]] || exit 40
export H06_STAGE_RECORDS="$OUT_RECORDS" H06_STAGE_LOGS="$OUT_LOGS"
EVIDENCE="$OUT_RECORDS/release-drill"; mkdir -p "$EVIDENCE"
input_before="$(sha256sum "$INPUT" | awk '{print $1}')"; [[ "$input_before" == "$EXPECTED_INPUT_SHA" ]] || exit 40
printf 'RELEASE_INPUT=%s\nRELEASE_INPUT_SHA256_BEFORE=%s\nRELEASE_INPUT_REUSED_FROM_BUILD_VERIFY=PASS\n' "$INPUT" "$input_before" > "$EVIDENCE/release-input-lifecycle.txt"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; export NO_PROXY='127.0.0.1,localhost,kit.h06.invalid,api.h06.invalid'; export no_proxy="$NO_PROXY"
mkdir -p /home/isp/hosts/cyf/api/tmp/old-classes; "$H06_JDK_ROOT/bin/javac" -d /home/isp/hosts/cyf/api/tmp/old-classes "$RUN/tmp/OldHealth.java"; "$H06_JDK_ROOT/bin/jar" cfm /home/isp/hosts/cyf/api/cyf-api-kit.jar "$RUN/tmp/OLD.MF" -C /home/isp/hosts/cyf/api/tmp/old-classes .
REG="$RUN/release/private/pids.tsv"; : > "$REG"; cleanup(){ set +e; cp "$REG" "$OUT_RECORDS/release-owned-processes.tsv" 2>/dev/null || true; h06_stop_tracked_pids "$REG"; printf 'RELEASE_TRACKED_PROCESS_CLEANUP=PASS\n' > "$OUT_RECORDS/release-cleanup.txt"; h06_safe_remove_run_local "$RUN" "$RUN/release/private"; }; trap cleanup EXIT
h06_start_mysql "$RUN/release" "$MYSQL_PORT" cyf_h06_release "$REG"; MC="$H06_MYSQL_ROOT/bin/mysql"; S="$H06_MYSQL_SOCKET"; DB="$H06_MYSQL_DATABASE"; $MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/starter/src/test/resources/db/schema.sql"; $MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/chat/jia-chat-mapper/src/test/resources/db/schema.sql"; $MC --protocol=socket --socket="$S" -uroot "$DB" < "$API_WORKTREE/agent/jia-agent-mapper/src/main/resources/db/schema.sql"; h06_start_redis "$RUN/release" "$REDIS_PORT" "$REG"
NOW=$(python3 -c 'import time;print(int(time.time()*1000))')
$MC --protocol=socket --socket="$S" -uroot "$DB" <<SQLSEED
INSERT INTO oauth_client (id,client_id,client_id_issued_at,client_secret,client_name,client_authentication_methods,authorization_grant_types,redirect_uris,post_logout_redirect_uris,scopes,client_settings,token_settings,create_time,update_time,tenant_id,appcn) VALUES
('h06-ca','h06-client-a',CURRENT_TIMESTAMP,NULL,'H06 A','none','authorization_code,refresh_token','https://kit.h06.invalid:18443/oauth2/callback','','openid','{"settings.client.require-proof-key":true,"settings.client.require-authorization-consent":false}','',$NOW,$NOW,'h06','h06-a'),
('h06-cb','h06-client-b',CURRENT_TIMESTAMP,NULL,'H06 B','none','authorization_code,refresh_token','https://kit.h06.invalid:18443/oauth2/callback','','openid','{"settings.client.require-proof-key":true,"settings.client.require-authorization-consent":false}','',$NOW,$NOW,'h06','h06-b'),
('h06-neg','h06-claims-probe',CURRENT_TIMESTAMP,'h06-claims-secret','H06 claims negative','client_secret_basic','client_credentials','','','openid','{}','',$NOW,$NOW,'h06','h06-neg');
INSERT INTO user_info (id,username,password,jiacn,status,create_time,update_time,client_id,tenant_id) VALUES (90601,'h06-user-a','h06-pass-a','h06-owner-a',1,$NOW,$NOW,'h06-client-a','h06-owner-a'),(90602,'h06-user-b','h06-pass-b','h06-owner-b',1,$NOW,$NOW,'h06-client-b','h06-owner-b');
SQLSEED
cat > /home/isp/hosts/cyf/api/h06-on.properties <<EOFPROP
server.address=127.0.0.1
server.port=18018
server.ssl.enabled=false
server.shutdown=graceful
spring.main.banner-mode=off
spring.main.lazy-initialization=false
spring.datasource.type=com.zaxxer.hikari.HikariDataSource
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver
spring.datasource.url=jdbc:mysql://127.0.0.1:$MYSQL_PORT/$DB?useSSL=false&allowPublicKeyRetrieval=true
spring.datasource.username=root
spring.datasource.password=
spring.datasource.hikari.minimum-idle=1
spring.datasource.hikari.maximum-pool-size=3
dynamic.datasource.enable=false
spring.data.redis.host=127.0.0.1
spring.data.redis.port=$REDIS_PORT
spring.data.redis.password=h06-redis-secret
spring.session.store-type=none
spring.autoconfigure.exclude=org.springframework.boot.amqp.autoconfigure.RabbitAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpClientAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpToolCallbackAutoConfiguration
spring.ai.mcp.client.enabled=false
spring.ai.mcp.client.toolcallback.enabled=false
spring.ai.model.chat=openai
spring.ai.model.embedding=openai
spring.ai.openai.api-key=h06-isolated-key
spring.ai.openai.base-url=http://127.0.0.1:19999/v1
spring.ai.openai.chat.options.model=h06-isolated
spring.ai.openai.embedding.options.model=h06-isolated
spring.elasticsearch.uris=http://127.0.0.1:$ES_PORT
management.health.elasticsearch.enabled=false
management.endpoints.web.exposure.include=health
management.health.ldap.enabled=false
management.health.rabbit.enabled=false
camunda.bpm.enabled=false
jia.chat.service.websocket.enable=false
spring.task.scheduling.enabled=false
jia.file.path=/home/isp/hosts/cyf/api/files
mat.web.realpath=/home/isp/hosts/cyf/api/material
oauth.resource.uris[0]=/archive/**
oauth.resource.uris[1]=/chat/**
archive.reader.enabled=true
archive.question.enabled=true
archive.reader.allowed-scopes[0].tenant-id=h06-owner-a
archive.reader.allowed-scopes[0].client-id=h06-client-a
archive.reader.allowed-scopes[1].tenant-id=h06-owner-a
archive.reader.allowed-scopes[1].client-id=h06-client-b
archive.reader.allowed-scopes[2].tenant-id=h06-owner-b
archive.reader.allowed-scopes[2].client-id=h06-client-a
archive.reader.allowed-scopes[3].tenant-id=h06-owner-b
archive.reader.allowed-scopes[3].client-id=h06-client-b
EOFPROP
 cp /home/isp/hosts/cyf/api/h06-on.properties /home/isp/hosts/cyf/api/h06-off.properties
 sed -i -E 's/^archive\.reader\.enabled=.*/archive.reader.enabled=false/;s/^archive\.question\.enabled=.*/archive.question.enabled=false/' /home/isp/hosts/cyf/api/h06-off.properties
 cp /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties
 chmod 0600 /home/isp/hosts/cyf/api/h06-on.properties /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties
 sha256sum /home/isp/hosts/cyf/api/h06-on.properties /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties > "$EVIDENCE/flag-properties-baseline.sha256"
 cmp -s /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties || exit 41
cat > "$RUN/release/private/openssl.cnf" <<'SSL'
[req]
distinguished_name=dn
x509_extensions=v3
prompt=no
[dn]
CN=kit.h06.invalid
[v3]
subjectAltName=DNS:kit.h06.invalid
basicConstraints=critical,CA:TRUE
SSL
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -keyout "$RUN/release/private/tls.key" -out "$RUN/release/public/tls.crt" -config "$RUN/release/private/openssl.cnf" >/dev/null 2>&1
cat > "$RUN/release/private/server.py" <<'PY'
import http.server,os,ssl,sys
root,crt,key=sys.argv[1:]
class H(http.server.SimpleHTTPRequestHandler):
 def translate_path(self,p):
  q=os.path.join(root,p.split('?',1)[0].lstrip('/')); return q if os.path.isfile(q) else os.path.join(root,'index.html')
 def log_message(self,*a): pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',18443),H);c=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);c.load_cert_chain(crt,key);s.socket=c.wrap_socket(s.socket,server_side=True);s.serve_forever()
PY
python3 "$RUN/release/private/server.py" /home/isp/hosts/cyf/web/kit "$RUN/release/public/tls.crt" "$RUN/release/private/tls.key" > "$OUT_LOGS/release-web-server.log" 2>&1 & WP=$!; h06_track_pid "$REG" web-server "$WP" "$(readlink -f "$(command -v python3)")"
(cd /home/isp/hosts/cyf/api && exec "$H06_JDK_ROOT/bin/java" -jar /home/isp/hosts/cyf/api/cyf-api-kit.jar --spring.config.location=file:/home/isp/hosts/cyf/api/h06-active.properties > logs/old.log 2>&1) & OLD=$!; h06_track_pid "$REG" old-api "$OLD" "$H06_JDK_ROOT/bin/java"; printf '%s\n' "$OLD" > /home/isp/hosts/cyf/api/cyf-api-kit.pid
for _ in {1..120}; do curl -fsS http://127.0.0.1:18018/actuator/health > "$EVIDENCE/old-health-before.json" && break; sleep .25; done; grep -q h06-old "$EVIDENCE/old-health-before.json" || exit 41
for route in catalog me/questions/00000000-0000-4000-8000-000000000000 me/questions/00000000-0000-4000-8000-000000000000/events; do code=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:18018/archive/v1/$route"); [[ "$code" == 404 ]] || exit 41; done
curl -fsS -X POST -H 'Content-Type: application/json' --data '{"keyword":"h06"}' http://127.0.0.1:18018/chat/library/search > "$EVIDENCE/legacy-old-baseline-off.json" || exit 41
printf 'OLD_BASELINE_EXPLICIT_OFF=PASS
' > "$EVIDENCE/old-baseline-flags.txt"
cp /home/isp/hosts/cyf/api/h06-on.properties /home/isp/hosts/cyf/api/h06-active.properties; chmod 0600 /home/isp/hosts/cyf/api/h06-active.properties
cmp -s /home/isp/hosts/cyf/api/h06-on.properties /home/isp/hosts/cyf/api/h06-active.properties || exit 41
sha256sum /home/isp/hosts/cyf/api/h06-active.properties > "$EVIDENCE/flag-active-before-deploy.sha256"
export CYF_RELEASE_APPROVED=YES CYF_RELEASE_APPROVAL_ID="h06-$RUN_ID" CYF_RELEASE_APPROVED_API_HEAD="$API_HEAD" CYF_RELEASE_APPROVED_API_TREE="$API_TREE" CYF_RELEASE_APPROVED_WEB_HEAD="$WEB_HEAD" CYF_RELEASE_APPROVED_WEB_TREE="$WEB_TREE" CURL_CA_BUNDLE="$RUN/release/public/tls.crt"
"$H06_RELEASE_ROOT/deploy-api.sh" --input "$INPUT" --execute > "$OUT_LOGS/deploy-api.log" 2>&1; AR=$(sed -n 's/^DEPLOY_RECORD=//p' "$OUT_LOGS/deploy-api.log"|tail -1); [[ -f "$AR" ]] || exit 42; NEW=$(cat /home/isp/hosts/cyf/api/cyf-api-kit.pid); h06_track_pid "$REG" deployed-api "$NEW" "$H06_JDK_ROOT/bin/java"
python3 - "$NEW" /home/isp/hosts/cyf/api/h06-active.properties /home/isp/hosts/cyf/api/h06-on.properties <<'PYARGV' > "$EVIDENCE/candidate-deploy-argv-flags.txt"
import os,pathlib,sys
pid,active,on=sys.argv[1:]; raw=(pathlib.Path('/proc')/pid/'cmdline').read_bytes(); argv=[x.decode() for x in raw.split(b'\0') if x]
expected='--spring.config.location=file:'+os.path.realpath(active)
if expected not in argv: raise SystemExit('candidate deploy argv lacks explicit flag-on properties: '+repr(argv))
if pathlib.Path(active).read_bytes()!=pathlib.Path(on).read_bytes(): raise SystemExit('candidate deploy active properties are not explicit on bytes')
print('CANDIDATE_DEPLOY_ARGV_FLAG_ON=PASS'); print('ACTIVE_PROPERTIES='+os.path.realpath(active))
PYARGV
"$H06_RELEASE_ROOT/deploy-web.sh" --input "$INPUT" --execute > "$OUT_LOGS/deploy-web.log" 2>&1; WR=$(sed -n 's/^DEPLOY_RECORD=//p' "$OUT_LOGS/deploy-web.log"|tail -1); [[ -f "$WR" ]] || exit 43
mkdir -p "$RUN/release/private/tokens" "$EVIDENCE/on-probe"
python3 "$RUN/tmp/get-h06-tokens.py" http://127.0.0.1:18018 https://kit.h06.invalid:18443/oauth2/callback /etc/pki/tls/certs/ca-bundle.crt "$RUN/release/private/tokens"
python3 "$RUN/tmp/runtime-probe.py" positive http://127.0.0.1:18018 /etc/pki/tls/certs/ca-bundle.crt "$RUN/release/private/tokens" "$EVIDENCE/on-probe" "$MC" "$S" "$DB"
TOKEN=$(cat "$RUN/release/private/tokens/a_a.jwt"); code=$(curl -sS -H "Authorization: Bearer $TOKEN" -o "$EVIDENCE/catalog-on.json" -w '%{http_code}' http://127.0.0.1:18018/archive/v1/catalog); [[ "$code" == 200 ]] || exit 44
printf 'VALID_OAUTH_TOKEN_READER=200\nVALID_OAUTH_TOKEN_QUESTION=SUCCEEDED\nVALID_OAUTH_TOKEN_LIVE_SSE=QUESTION_SUCCEEDED\n' > "$EVIDENCE/flag-on-status.txt"
cp /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties; chmod 0600 /home/isp/hosts/cyf/api/h06-active.properties; cmp -s /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties || exit 44
CUR=$(cat /home/isp/hosts/cyf/api/cyf-api-kit.pid); CUR_ROW=$(awk -F '\t' -v p="$CUR" '$1=="deployed-api"&&$2==p{print $3"\t"$4}' "$REG" | tail -1); IFS=$'\t' read -r CUR_TICKS CUR_EXE <<<"$CUR_ROW"; h06_pid_matches "$CUR" "$CUR_TICKS" "$CUR_EXE" || exit 44; kill -TERM "$CUR"; for _ in {1..120}; do h06_pid_matches "$CUR" "$CUR_TICKS" "$CUR_EXE" || break; sleep .25; done; h06_pid_matches "$CUR" "$CUR_TICKS" "$CUR_EXE" && exit 44
(cd /home/isp/hosts/cyf/api && exec "$H06_JDK_ROOT/bin/java" -jar /home/isp/hosts/cyf/api/cyf-api-kit.jar --spring.config.location=file:/home/isp/hosts/cyf/api/h06-active.properties > logs/off.log 2>&1) & OFF=$!; h06_track_pid "$REG" off-api "$OFF" "$H06_JDK_ROOT/bin/java"; printf '%s\n' "$OFF" > /home/isp/hosts/cyf/api/cyf-api-kit.pid
for _ in {1..360}; do curl -fsS http://127.0.0.1:18018/actuator/health > "$EVIDENCE/off-health.json" && break; sleep .25; done
for route in catalog me/questions/00000000-0000-4000-8000-000000000000 me/questions/00000000-0000-4000-8000-000000000000/events; do code=$(curl -sS -H "Authorization: Bearer $TOKEN" -o /dev/null -w '%{http_code}' "http://127.0.0.1:18018/archive/v1/$route"); [[ "$code" == 404 ]] || exit 45; done
curl -fsS -X POST -H 'Content-Type: application/json' --data '{"keyword":"h06"}' http://127.0.0.1:18018/chat/library/search > "$EVIDENCE/legacy-off.json" || exit 46
"$H06_RELEASE_ROOT/rollback-web.sh" --input "$INPUT" --execute "$WR" > "$OUT_LOGS/rollback-web.log" 2>&1; "$H06_RELEASE_ROOT/rollback-api.sh" --input "$INPUT" --execute "$AR" > "$OUT_LOGS/rollback-api.log" 2>&1; RESTORED=$(cat /home/isp/hosts/cyf/api/cyf-api-kit.pid); h06_track_pid "$REG" restored-old-api "$RESTORED" "$H06_JDK_ROOT/bin/java"
for _ in {1..120}; do curl -fsS http://127.0.0.1:18018/actuator/health > "$EVIDENCE/old-health-after.json" && break; sleep .25; done; grep -q h06-old "$EVIDENCE/old-health-after.json" || exit 47
cmp -s /home/isp/hosts/cyf/api/h06-off.properties /home/isp/hosts/cyf/api/h06-active.properties || exit 47
for route in catalog me/questions/00000000-0000-4000-8000-000000000000 me/questions/00000000-0000-4000-8000-000000000000/events; do code=$(curl -sS -H "Authorization: Bearer $TOKEN" -o /dev/null -w '%{http_code}' "http://127.0.0.1:18018/archive/v1/$route"); [[ "$code" == 404 ]] || exit 47; done
curl -fsS -X POST -H 'Content-Type: application/json' --data '{"keyword":"h06"}' http://127.0.0.1:18018/chat/library/search > "$EVIDENCE/legacy-rollback.json" || exit 47
find /home/isp/baks/legacy-api /home/isp/baks/legacy-web -type f -printf '%m %s %p\n' | sort > "$EVIDENCE/backup-inventory.txt"; find /home/isp/hosts/cyf -type f -name '*.sha256' -print0 | xargs -0 -r -n1 sh -c 'cd "$(dirname "$1")" && sha256sum -c "$(basename "$1")"' _ > "$EVIDENCE/backup-sidecars.txt"
input_after="$(sha256sum "$INPUT" | awk '{print $1}')"; [[ "$input_after" == "$input_before" && "$input_after" == "$EXPECTED_INPUT_SHA" ]] || exit 47
printf 'RELEASE_INPUT_SHA256_AFTER=%s\nRELEASE_INPUT_UNCHANGED_THROUGH_DEPLOY_ROLLBACK=PASS\n' "$input_after" >> "$EVIDENCE/release-input-lifecycle.txt"
printf 'RELEASE_DRILL=PASS\nOLD_BASELINE_EXPLICIT_OFF=PASS\nCANDIDATE_DEPLOY_ARGV_FLAG_ON=PASS\nFLAG_ON_READER_QUESTION_SSE=PASS\nFLAG_OFF_ARCHIVE_READER_QUESTION_SSE_404=PASS\nFLAG_OFF_LEGACY=PASS\nARTIFACT_ROLLBACK=PASS\nOLD_HEALTH=PASS\nBACKUP_SIDECARS=PASS\nSINGLE_RELEASE_INPUT_THROUGH_DEPLOY=PASS\nPRODUCTION_DEPLOYMENT=NOT_PERFORMED\nPRODUCTION_DB_OPERATION=NOT_PERFORMED\n' > "$EVIDENCE/result.txt"
DRIVER
  chmod 0555 "$driver"; local mp=$((25000 + RANDOM%7000)) rp=$((35000 + RANDOM%7000)) ep=$((45000 + RANDOM%7000)) input_sha
  input_sha="$(sha256sum "$RUN/config/release-input.json" | awk '{print $1}')"
  unshare -m -n -p --fork --kill-child=KILL --mount-proc -- env RUN="$RUN" OUT_RECORDS="$WORKER_OUTPUT/release/records" OUT_LOGS="$WORKER_OUTPUT/release/logs" RUN_ID="$RUN_ID" LIB="$LIB" H06_RELEASE_ROOT="$H06_RELEASE_ROOT" INPUT="$RUN/config/release-input.json" EXPECTED_INPUT_SHA="$input_sha" API_WORKTREE="$API_STAGED" API_HEAD="$API_HEAD" API_TREE="$API_TREE" WEB_HEAD="$WEB_HEAD" WEB_TREE="$WEB_TREE" MYSQL_PORT="$mp" REDIS_PORT="$rp" ES_PORT="$ep" H06_WORKER_UID="$H06_WORKER_UID" H06_WORKER_GID="$H06_WORKER_GID" H06_MYSQL_ROOT="$H06_MYSQL_ROOT" H06_REDIS_ROOT="$H06_REDIS_ROOT" H06_JDK_ROOT="$H06_JDK_ROOT" PATH="$H06_JDK_ROOT/bin:$H06_NODE_ROOT/bin:/usr/bin:/bin" /bin/bash "$driver"
  log 'release build/verify/deploy/off/rollback gate PASS'
}

prepare_gate
case "$STAGE" in
  prepare) ;;
  mysql) mysql_gate ;;
  runtime) runtime_gate ;;
  release-drill) release_gate ;;
  all) mysql_gate; runtime_gate; release_gate ;;
  *) die "internal stage error: $STAGE" ;;
esac
RESULT=PASS
RESULT_DETAIL="H06 isolated $STAGE gate completed"
printf 'H06_GATE=PASS\nSTAGE=%s\n' "$STAGE" > "$RUN/gate-pass.txt"
