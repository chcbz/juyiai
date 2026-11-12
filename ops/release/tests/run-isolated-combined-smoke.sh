#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
CYF_HEAVY_RESOURCE_LOCK=/tmp/cyf-heavy-resource.lock

acquire_heavy_resource_lock() {
  printf 'HEAVY_RESOURCE_LOCK_WAIT path=%s pid=%s\n' "$CYF_HEAVY_RESOURCE_LOCK" "$$" >&2
  exec {CYF_HEAVY_RESOURCE_LOCK_FD}>"$CYF_HEAVY_RESOURCE_LOCK"
  flock -x "$CYF_HEAVY_RESOURCE_LOCK_FD"
  printf 'HEAVY_RESOURCE_LOCK_ACQUIRED path=%s pid=%s capacity_admission=disabled\n' \
    "$CYF_HEAVY_RESOURCE_LOCK" "$$" >&2
}
INPUT="$ROOT/ops/release/m2-c08-r6-input.json"
API_JAR="$ROOT/deliverables/releases/m2-c08-r6/api/cyf-api-e45ba398f116a210091c892abb9fbc8111dcc411-8b80bf35c418b2ca0cead919f805db5bb70166eb.jar"
R6_WEB_ARTIFACT="$ROOT/deliverables/releases/m2-c08-r6/web/cyf-web-266583f2e59d5f1362ed4d653f58d02b78a0e6b5-ba7ed4f167c43b3af8a7f07d34d626308496cd36.tar.gz"
R6_RELEASE_RECORD="$ROOT/deliverables/releases/m2-c08-r6/release/cyf-release-e45ba398f116a210091c892abb9fbc8111dcc411-8b80bf35c418b2ca0cead919f805db5bb70166eb-266583f2e59d5f1362ed4d653f58d02b78a0e6b5-ba7ed4f167c43b3af8a7f07d34d626308496cd36.json"
WEB_ARCHIVE="$ROOT/deliverables/m2-c08-20260822/web/cyf-web-kit-266583f2e59d5f1362ed4d653f58d02b78a0e6b5-smoke-on.tar.gz"
WEB_PROVENANCE="$ROOT/deliverables/m2-c08-20260822/records/web-smoke-on-r6-provenance.json"
WEB_BUILD_LOG="$ROOT/deliverables/m2-c08-20260822/records/web-build.log"
WEB_SOURCE_REFS="$ROOT/deliverables/m2-c08-20260822/records/source-refs.txt"
WEB_FILES_MANIFEST="$ROOT/deliverables/m2-c08-20260822/records/web-smoke-on-files.sha256"
API_SCHEMA="$ROOT/.worktrees/m2-api-base/starter/src/test/resources/db/schema.sql"
CHAT_SCHEMA="$ROOT/.worktrees/m2-api-base/chat/jia-chat-mapper/src/test/resources/db/schema.sql"
AGENT_SCHEMA="$ROOT/.worktrees/m2-api-base/agent/jia-agent-mapper/src/main/resources/db/schema.sql"
EXPECTED_API_SHA="c71b3ff21078bd6cf48b71a2fd510e29f25d2e8677a5a9bab51337ec4853260b"
EXPECTED_R6_WEB_SHA="911a9479d28ada12e3dbaf8565ccb893520cb12405f87b1dbdc63674e074e6b7"
EXPECTED_WEB_SHA="34eb6e067234b7d3fb5811630915772e04721f19dd195d12b8c759658f3da563"
EXPECTED_R6_INPUT_SHA="797767b9851dc35d5b1b2a20499f377d79c65aff7dc436495dc0d600b883b89f"
EXPECTED_R6_RELEASE_RECORD_SHA="d39cfc7c6ccf7c279d58e19e6b5557575f37fde720c1c37a758ba5582e250ba9"
EXPECTED_WEB_PROVENANCE_SHA="33594aeacc90ed78cfb9761024f769c415c3a4f2e53f4aa69ccfdd6b461e4743"
EVIDENCE_ROOT="${1:-$ROOT/deliverables/m2-c08-20260822/isolated-combined-smoke-v3}"
PRODUCTION_PID_FILE=/home/isp/hosts/cyf/api/cyf-api-kit.pid
PRODUCTION_LIVE_JAR=/home/isp/hosts/cyf/api/cyf-api-kit.jar
MIN_HOST_DISK_AVAILABLE_BYTES=5905580032
SMOKE_MEMORY_MAX=1200M
SMOKE_MEMORY_MAX_BYTES=1258291200
SMOKE_MEMORY_SWAP_MAX=256M
SMOKE_MEMORY_SWAP_MAX_BYTES=268435456
HOST_MEMORY_RESERVE_BYTES=268435456
MIN_HOST_MEM_AVAILABLE_BYTES=$((SMOKE_MEMORY_MAX_BYTES + HOST_MEMORY_RESERVE_BYTES))
if [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
  SYSTEMD_MEMORY_MODE=cgroup-v2
  SYSTEMD_MEMORY_ARGS=(-p MemoryAccounting=yes -p MemoryMax="$SMOKE_MEMORY_MAX" -p MemorySwapMax="$SMOKE_MEMORY_SWAP_MAX")
else
  SYSTEMD_MEMORY_MODE=cgroup-v1-driver-enforced-memsw
  SYSTEMD_MEMORY_ARGS=(-p MemoryAccounting=yes -p MemoryLimit="$SMOKE_MEMORY_MAX")
fi

(( EUID == 0 )) || { echo 'isolated combined smoke requires root for namespaces and mounts' >&2; exit 2; }
[[ ! -e "$EVIDENCE_ROOT" && ! -L "$EVIDENCE_ROOT" ]] \
  || { echo "evidence target already exists: $EVIDENCE_ROOT" >&2; exit 2; }
for command in bash unshare mount ip openssl sha256sum tar curl ss awk grep sed python3 base64 ps setpriv systemd-run flock; do
  command -v "$command" >/dev/null 2>&1 || { echo "missing command: $command" >&2; exit 2; }
done
acquire_heavy_resource_lock
for path in "$INPUT" "$API_JAR" "$R6_WEB_ARTIFACT" "$R6_RELEASE_RECORD" \
  "$WEB_ARCHIVE" "$WEB_PROVENANCE" "$WEB_BUILD_LOG" "$WEB_SOURCE_REFS" \
  "$WEB_FILES_MANIFEST" "$API_SCHEMA" "$CHAT_SCHEMA" "$AGENT_SCHEMA" \
  "$PRODUCTION_PID_FILE" "$PRODUCTION_LIVE_JAR"; do
  [[ -f "$path" && ! -L "$path" ]] || { echo "required physical file missing: $path" >&2; exit 2; }
done
verify_exact_sidecar() {
  local file="$1" side="${1}.sha256" expected
  [[ -f "$side" && ! -L "$side" ]] || { echo "missing sidecar: $side" >&2; return 1; }
  expected="$(sha256sum "$file" | awk '{print $1}')  $(basename "$file")"
  [[ "$(cat "$side")" == "$expected" ]] || { echo "sidecar mismatch: $file" >&2; return 1; }
  [[ "$(stat -c %a "$file")" == 444 && "$(stat -c %a "$side")" == 444 ]] \
    || { echo "immutable input mode mismatch: $file" >&2; return 1; }
}
for path in "$INPUT" "$API_JAR" "$R6_WEB_ARTIFACT" "$R6_RELEASE_RECORD" \
  "$WEB_ARCHIVE" "$WEB_PROVENANCE" "$WEB_BUILD_LOG" "$WEB_SOURCE_REFS" "$WEB_FILES_MANIFEST"; do
  verify_exact_sidecar "$path"
done
[[ "$(sha256sum "$INPUT" | awk '{print $1}')" == "$EXPECTED_R6_INPUT_SHA" ]] || exit 2
[[ "$(sha256sum "$API_JAR" | awk '{print $1}')" == "$EXPECTED_API_SHA" ]] || exit 2
[[ "$(sha256sum "$R6_WEB_ARTIFACT" | awk '{print $1}')" == "$EXPECTED_R6_WEB_SHA" ]] || exit 2
[[ "$(sha256sum "$R6_RELEASE_RECORD" | awk '{print $1}')" == "$EXPECTED_R6_RELEASE_RECORD_SHA" ]] || exit 2
[[ "$(sha256sum "$WEB_ARCHIVE" | awk '{print $1}')" == "$EXPECTED_WEB_SHA" ]] || exit 2
[[ "$(sha256sum "$WEB_PROVENANCE" | awk '{print $1}')" == "$EXPECTED_WEB_PROVENANCE_SHA" ]] || exit 2
python3 - "$WEB_PROVENANCE" "$INPUT" "$R6_WEB_ARTIFACT" "$R6_RELEASE_RECORD" \
  "$WEB_ARCHIVE" "$WEB_BUILD_LOG" "$WEB_SOURCE_REFS" "$WEB_FILES_MANIFEST" <<'PYPROV'
import hashlib, json, pathlib, sys
(provenance_path, release_input, release_web, release_record, smoke_archive,
 build_log, source_refs, files_manifest) = sys.argv[1:]
def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
with open(provenance_path, encoding='utf-8') as stream:
    p = json.load(stream)
expected = {
    'schema': 'cyf-m2-c08-combined-smoke-web-provenance-v1',
    'purpose': 'ISOLATED_FLAG_ON_SMOKE_ONLY',
    'deployableReleaseArtifact': False,
    'productionDeployment': 'NOT_PERFORMED',
    'sourceRepo': '/home/isp/wsps/cyf/.worktrees/m2-web-base',
    'sourceRef': 'feat/m2-web-base-20260803',
    'sourceHead': '266583f2e59d5f1362ed4d653f58d02b78a0e6b5',
    'sourceTree': 'ba7ed4f167c43b3af8a7f07d34d626308496cd36',
    'smokeArchive': smoke_archive,
    'smokeArchiveSha256': sha(smoke_archive),
    'smokeArchiveFilesManifest': files_manifest,
    'smokeArchiveFilesManifestSha256': sha(files_manifest),
    'buildLog': build_log,
    'buildLogSha256': sha(build_log),
    'sourceRefsRecord': source_refs,
    'sourceRefsRecordSha256': sha(source_refs),
    'r6ReleaseInput': release_input,
    'r6ReleaseInputSha256': sha(release_input),
    'r6DefaultOffWebArtifact': release_web,
    'r6DefaultOffWebArtifactSha256': sha(release_web),
    'r6ReleaseRecord': release_record,
    'r6ReleaseRecordSha256': sha(release_record),
}
for key, value in expected.items():
    if p.get(key) != value:
        raise SystemExit(f'Web smoke provenance mismatch for {key}')
if p.get('featureFlag') != {'VITE_JUYITING_TASK_WORKSPACE_ENABLED': 'true'}:
    raise SystemExit('Web smoke provenance feature flag mismatch')
if p.get('relationship') != 'SAME_FROZEN_SOURCE_HEAD_TREE; FLAG_ON_SMOKE_VARIANT IS NOT THE DEFAULT_OFF DEPLOYABLE ARTIFACT':
    raise SystemExit('Web smoke provenance relationship mismatch')
record = json.loads(pathlib.Path(release_record).read_text())
if record.get('webHead') != p['sourceHead'] or record.get('webTree') != p['sourceTree']:
    raise SystemExit('r6 release record does not bind the smoke source HEAD/tree')
refs = pathlib.Path(source_refs).read_text().splitlines()
if f"web_sha={p['sourceHead']}" not in refs or f"web_tree={p['sourceTree']}" not in refs:
    raise SystemExit('source refs do not bind the smoke source HEAD/tree')
log = pathlib.Path(build_log).read_text()
if 'default_off_build_start=' not in log or 'flag_on_build_start=' not in log or 'build_end=' not in log:
    raise SystemExit('Web build log does not prove both flag variants')
PYPROV

[[ -z "$(git -C "$ROOT/.worktrees/m2-api-base" status --porcelain=v1 --untracked-files=all)" ]] || { echo 'API candidate worktree is dirty' >&2; exit 2; }
[[ -z "$(git -C "$ROOT/.worktrees/m2-web-base" status --porcelain=v1 --untracked-files=all)" ]] || { echo 'Web candidate worktree is dirty' >&2; exit 2; }
[[ "$(git -C "$ROOT/.worktrees/m2-api-base" rev-parse HEAD)" == e45ba398f116a210091c892abb9fbc8111dcc411 ]] || exit 2
[[ "$(git -C "$ROOT/.worktrees/m2-api-base" rev-parse HEAD^{tree})" == 8b80bf35c418b2ca0cead919f805db5bb70166eb ]] || exit 2
[[ "$(git -C "$ROOT/.worktrees/m2-web-base" rev-parse HEAD)" == 266583f2e59d5f1362ed4d653f58d02b78a0e6b5 ]] || exit 2
[[ "$(git -C "$ROOT/.worktrees/m2-web-base" rev-parse HEAD^{tree})" == ba7ed4f167c43b3af8a7f07d34d626308496cd36 ]] || exit 2
HEALTH_EXPECTED_REGEX="$(python3 - "$INPUT" <<'PYHEALTH'
import json,sys
with open(sys.argv[1], encoding='utf-8') as stream:
    print(json.load(stream)['api']['deploy']['healthExpectedRegex'])
PYHEALTH
)"
for sample in '{"status":"UP"}' '{"status":{"code":"UP","description":""}}'; do
  [[ "$sample" =~ $HEALTH_EXPECTED_REGEX ]] || { echo 'r6 health regex rejected a supported UP payload' >&2; exit 2; }
done
[[ ! '{"status":"DOWN"}' =~ $HEALTH_EXPECTED_REGEX ]] || { echo 'r6 health regex accepted DOWN' >&2; exit 2; }

IFS=$'\t' read -r PRODUCTION_PID PRODUCTION_START_TICKS < <(python3 - "$PRODUCTION_PID_FILE" "$PRODUCTION_LIVE_JAR" <<'PYPROD'
import os, pathlib, sys
pid_text = pathlib.Path(sys.argv[1]).read_text().strip()
if not pid_text.isdigit(): raise SystemExit('production API pidfile is not numeric')
pid = int(pid_text); proc = pathlib.Path('/proc') / str(pid)
if not proc.is_dir():
    raise SystemExit('production API is not running; isolated high-memory smoke is fail-closed')
args = (proc / 'cmdline').read_bytes().split(b'\0')
jars = [os.path.realpath(os.fsdecode(args[i+1])) for i, value in enumerate(args[:-1]) if value == b'-jar']
if jars != [os.path.realpath(sys.argv[2])]:
    raise SystemExit('production API PID does not identify the expected live JAR')
text = (proc / 'stat').read_text(); end = text.rfind(')')
if end < 0: raise SystemExit('production API proc stat is malformed')
print(f"{pid}\t{text[end+2:].split()[19]}")
PYPROD
)
HOST_MEM_AVAILABLE_BEFORE="$(awk '/^MemAvailable:/ {print $2 * 1024}' /proc/meminfo)"
HOST_DISK_AVAILABLE_BEFORE="$(df -PB1 -- "$ROOT" | awk 'NR==2 {print $4}')"
PRODUCTION_LIVE_JAR_SHA_BEFORE="$(sha256sum "$PRODUCTION_LIVE_JAR" | awk '{print $1}')"
if (( HOST_MEM_AVAILABLE_BEFORE < MIN_HOST_MEM_AVAILABLE_BYTES )); then
  echo "host memory observation below former threshold (non-blocking): available=$HOST_MEM_AVAILABLE_BEFORE former_required=$MIN_HOST_MEM_AVAILABLE_BYTES" >&2
fi
if (( HOST_DISK_AVAILABLE_BEFORE < MIN_HOST_DISK_AVAILABLE_BYTES )); then
  echo "host disk observation below former threshold (non-blocking): available=$HOST_DISK_AVAILABLE_BEFORE former_required=$MIN_HOST_DISK_AVAILABLE_BYTES" >&2
fi

RUN="$(mktemp -d /tmp/cyf-c08-combined-smoke.XXXXXX)"
EVIDENCE="$RUN/evidence"
mkdir -p "$EVIDENCE" "$RUN"/{mysql,redis,web,files,material,logs,chrome}
chmod 0755 "$RUN"
ISOLATED_API_JAR="$RUN/candidate-api.jar"
ln -- "$API_JAR" "$ISOLATED_API_JAR"
[[ "$(stat -Lc '%d:%i' "$ISOLATED_API_JAR")" == "$(stat -Lc '%d:%i' "$API_JAR")" ]] || exit 2
[[ "$(sha256sum "$ISOLATED_API_JAR" | awk '{print $1}')" == "$EXPECTED_API_SHA" ]] || exit 2
runuser -u isp -- test -r "$ISOLATED_API_JAR"
chown -R isp:isp "$RUN/mysql" "$RUN/redis" "$RUN/files" "$RUN/material"
chown isp:isp "$RUN/logs"
chmod 0755 "$RUN/logs"
cat > "$EVIDENCE/host-resource-preflight.txt" <<EOF
PRODUCTION_API_PID=$PRODUCTION_PID
PRODUCTION_API_START_TICKS=$PRODUCTION_START_TICKS
PRODUCTION_LIVE_JAR_SHA256=$PRODUCTION_LIVE_JAR_SHA_BEFORE
HOST_MEM_AVAILABLE_BYTES=$HOST_MEM_AVAILABLE_BEFORE
HOST_DISK_AVAILABLE_BYTES=$HOST_DISK_AVAILABLE_BEFORE
FIXED_RESOURCE_ADMISSION_GATE=DISABLED_BY_USER_2026_08_28
MIN_HOST_MEM_AVAILABLE_BYTES=$MIN_HOST_MEM_AVAILABLE_BYTES
HOST_MEMORY_RESERVE_BYTES=$HOST_MEMORY_RESERVE_BYTES
MIN_HOST_DISK_AVAILABLE_BYTES=$MIN_HOST_DISK_AVAILABLE_BYTES
SYSTEMD_OUTER_MEMORY_MODE=$SYSTEMD_MEMORY_MODE
CGROUP_MEMORY_MAX=$SMOKE_MEMORY_MAX
CGROUP_MEMORY_MAX_BYTES=$SMOKE_MEMORY_MAX_BYTES
CGROUP_MEMORY_SWAP_MAX=$SMOKE_MEMORY_SWAP_MAX
CGROUP_MEMORY_SWAP_MAX_BYTES=$SMOKE_MEMORY_SWAP_MAX_BYTES
EOF
cat > "$EVIDENCE/web-smoke-provenance.txt" <<EOF
R6_DEFAULT_OFF_WEB_SHA256=$EXPECTED_R6_WEB_SHA
FLAG_ON_SMOKE_WEB_SHA256=$EXPECTED_WEB_SHA
WEB_PROVENANCE_SHA256=$EXPECTED_WEB_PROVENANCE_SHA
SOURCE_HEAD=266583f2e59d5f1362ed4d653f58d02b78a0e6b5
SOURCE_TREE=ba7ed4f167c43b3af8a7f07d34d626308496cd36
FLAG_ON_VARIANT=ISOLATED_SMOKE_ONLY
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
EOF

production_identity_unchanged() {
  [[ -d "/proc/$PRODUCTION_PID" ]] || return 1
  [[ "$(python3 - "$PRODUCTION_PID" <<'PYTICKS'
import pathlib,sys
text=(pathlib.Path('/proc')/sys.argv[1]/'stat').read_text(); end=text.rfind(')')
print(text[end+2:].split()[19])
PYTICKS
)" == "$PRODUCTION_START_TICKS" ]]
}
cleanup() {
  local exit_code=$?
  if ! production_identity_unchanged; then
    printf 'CRITICAL: production API identity changed or stopped during isolated smoke; no automatic restart was attempted\n' >&2
  fi
  set +e
  for pid in "${CHROME_PID:-}" "${NGINX_PID:-}" "${APP_PID:-}" "${REDIS_PID:-}" "${MYSQL_PID:-}"; do
    [[ -z "$pid" ]] || kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  if [[ "${CYF_KEEP_FAILED_RUN:-1}" == 1 && "$exit_code" != 0 ]]; then
    printf 'FAILED_RUN=%s\n' "$RUN" >&2
    return
  fi
  python3 - "$RUN" <<'PYCLEAN' >/dev/null 2>&1 || true
import shutil, sys
shutil.rmtree(sys.argv[1], ignore_errors=True)
PYCLEAN
}
trap cleanup EXIT

tar -xzf "$WEB_ARCHIVE" --no-same-owner --no-same-permissions -C "$RUN/web"
[[ -f "$RUN/web/index.html" ]] || { echo 'Web archive has no index.html' >&2; exit 2; }

cat > "$RUN/driver.sh" <<'DRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

configure_memory_cgroup_guard() {
  local cgroup_path base actual_memory actual_memsw total_limit
  if [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
    cgroup_path="$(awk -F: '$1 == "0" {print $3; exit}' /proc/self/cgroup)"
    base="/sys/fs/cgroup${cgroup_path}"
    printf '%s\n' "$CGROUP_MEMORY_MAX_BYTES" > "$base/memory.max"
    printf '%s\n' "$CGROUP_MEMORY_SWAP_MAX_BYTES" > "$base/memory.swap.max"
    actual_memory="$(cat "$base/memory.max")"
    actual_memsw="$(cat "$base/memory.swap.max")"
    [[ "$actual_memory" == "$CGROUP_MEMORY_MAX_BYTES" && "$actual_memsw" == "$CGROUP_MEMORY_SWAP_MAX_BYTES" ]] \
      || { echo 'cgroup v2 memory guard verification failed' >&2; exit 9; }
    printf 'CGROUP_VERSION=2\nCGROUP_PATH=%s\nMEMORY_MAX_BYTES=%s\nSWAP_MAX_BYTES=%s\n' \
      "$cgroup_path" "$actual_memory" "$actual_memsw" > "$EVIDENCE/cgroup-memory-guard.txt"
    return
  fi
  cgroup_path="$(awk -F: 'index($2,"memory") {print $3; exit}' /proc/self/cgroup)"
  [[ -n "$cgroup_path" ]] || { echo 'memory cgroup path unavailable' >&2; exit 9; }
  base="/sys/fs/cgroup/memory${cgroup_path}"
  total_limit=$((CGROUP_MEMORY_MAX_BYTES + CGROUP_MEMORY_SWAP_MAX_BYTES))
  # cgroup v1 requires the combined memory+swap ceiling to be set before
  # lowering the memory-only ceiling.
  printf '%s\n' "$total_limit" > "$base/memory.memsw.limit_in_bytes"
  printf '%s\n' "$CGROUP_MEMORY_MAX_BYTES" > "$base/memory.limit_in_bytes"
  actual_memory="$(cat "$base/memory.limit_in_bytes")"
  actual_memsw="$(cat "$base/memory.memsw.limit_in_bytes")"
  [[ "$actual_memory" == "$CGROUP_MEMORY_MAX_BYTES" && "$actual_memsw" == "$total_limit" ]] \
    || { echo 'cgroup v1 memory guard verification failed' >&2; exit 9; }
  printf 'CGROUP_VERSION=1\nCGROUP_PATH=%s\nMEMORY_LIMIT_BYTES=%s\nMEMORY_PLUS_SWAP_LIMIT_BYTES=%s\n' \
    "$cgroup_path" "$actual_memory" "$actual_memsw" > "$EVIDENCE/cgroup-memory-guard.txt"
}
configure_memory_cgroup_guard

cleanup_inner() {
  local exit_code=$?
  set +e
  local pid
  for pid in "${CHROME_PID:-}" "${APP_PID:-}" "${NGINX_PID:-}" "${REDIS_PID:-}" "${MYSQL_PID:-}"; do
    [[ -z "$pid" ]] || kill -TERM "$pid" 2>/dev/null || true
  done
  for _ in {1..30}; do
    local alive=0
    for pid in "${CHROME_PID:-}" "${APP_PID:-}" "${NGINX_PID:-}" "${REDIS_PID:-}" "${MYSQL_PID:-}"; do
      [[ -z "$pid" || ! -e "/proc/$pid" ]] || alive=1
    done
    (( alive == 0 )) && break
    sleep 1
  done
  for pid in "${CHROME_PID:-}" "${APP_PID:-}" "${NGINX_PID:-}" "${REDIS_PID:-}" "${MYSQL_PID:-}"; do
    [[ -z "$pid" || ! -e "/proc/$pid" ]] || kill -KILL "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  return "$exit_code"
}
trap cleanup_inner EXIT

mount --make-rprivate /
ip link set lo up
[[ -z "$(ip route show)" ]] || { echo 'isolated network namespace unexpectedly has a route' >&2; ip route show >&2; exit 10; }
cat > "$RUN/hosts" <<'HOSTS'
127.0.0.1 localhost kit.chaoyoufan.cn api.chaoyoufan.cn
::1 localhost
HOSTS
mount --bind "$RUN/hosts" /etc/hosts
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
export NO_PROXY='127.0.0.1,localhost,kit.chaoyoufan.cn,api.chaoyoufan.cn'
export no_proxy="$NO_PROXY"

MYSQL=/home/isp/apps/mysql/bin/mysqld
MYSQL_CLI=/home/isp/apps/mysql/bin/mysql
MYSQL_ADMIN=/home/isp/apps/mysql/bin/mysqladmin
REDIS=/home/isp/apps/redis/bin/redis-server
REDIS_CLI=/home/isp/apps/redis/bin/redis-cli
JAVA=/home/isp/apps/jdk21/bin/java
NGINX=/home/isp/apps/nginx/sbin/nginx
CHROME=/usr/bin/chromium-browser
for path in "$MYSQL" "$MYSQL_CLI" "$MYSQL_ADMIN" "$REDIS" "$REDIS_CLI" "$JAVA" "$NGINX" "$CHROME"; do
  [[ -x "$path" ]] || { echo "missing executable: $path" >&2; exit 11; }
done

ip route show > "$EVIDENCE/network-routes.txt"
readlink /proc/self/ns/pid > "$EVIDENCE/pid-namespace.txt"
ss -lntp > "$EVIDENCE/listeners-before.txt"
ps -eo pid=,ppid=,uid=,stat=,comm= > "$EVIDENCE/processes-before.txt"

"$MYSQL" --initialize-insecure --user=isp --datadir="$RUN/mysql" \
  --lower-case-table-names=1 --log-error="$RUN/logs/mysql-init.log"
"$MYSQL" --no-defaults --user=isp --datadir="$RUN/mysql" \
  --socket="$RUN/mysql/mysql.sock" --pid-file="$RUN/mysql/mysql.pid" \
  --port=33317 --bind-address=127.0.0.1 --skip-name-resolve --mysqlx=0 \
  --lower-case-table-names=1 --performance-schema=OFF \
  --innodb-buffer-pool-size=64M --key-buffer-size=8M --max-connections=20 \
  --log-bin-trust-function-creators=1 --log-error="$RUN/logs/mysql-server.log" &
MYSQL_PID=$!
export MYSQL_PID
for _ in {1..90}; do
  "$MYSQL_ADMIN" --protocol=socket --socket="$RUN/mysql/mysql.sock" ping >/dev/null 2>&1 && break
  kill -0 "$MYSQL_PID" 2>/dev/null || { cat "$RUN/logs/mysql-server.log" >&2; exit 12; }
  sleep 1
done
"$MYSQL_ADMIN" --protocol=socket --socket="$RUN/mysql/mysql.sock" ping >/dev/null 2>&1 || exit 12
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -N -B \
  -e 'SELECT CONCAT("lower_case_table_names=", @@lower_case_table_names)' \
  > "$EVIDENCE/mysql-lower-case-table-names.txt"
grep -Fxq 'lower_case_table_names=1' "$EVIDENCE/mysql-lower-case-table-names.txt" || exit 12
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -e \
  "CREATE DATABASE c08 CHARACTER SET utf8mb4 COLLATE utf8mb4_bin; CREATE USER 'c08'@'127.0.0.1' IDENTIFIED BY 'c08-pass'; GRANT ALL ON c08.* TO 'c08'@'127.0.0.1'; FLUSH PRIVILEGES;"
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 < "$API_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 < "$CHAT_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 < "$AGENT_SCHEMA"

NOW_MS="$(python3 - <<'PY'
import time
print(int(time.time()*1000))
PY
)"
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 <<SQL
INSERT INTO oauth_client
(id,client_id,client_id_issued_at,client_secret,client_name,
 client_authentication_methods,authorization_grant_types,redirect_uris,
 post_logout_redirect_uris,scopes,client_settings,token_settings,
 create_time,update_time,tenant_id,appcn)
VALUES
('c08-client','client-a',CURRENT_TIMESTAMP,'c08-secret','C08 isolated client',
 'none','authorization_code,refresh_token',
 'https://kit.chaoyoufan.cn/oauth2/callback','', 'openid',
 '{"settings.client.require-proof-key":true,"settings.client.require-authorization-consent":false}',
 '',$NOW_MS,$NOW_MS,'owner-a','c08');
INSERT INTO oauth_client
(id,client_id,client_id_issued_at,client_secret,client_name,
 client_authentication_methods,authorization_grant_types,redirect_uris,
 post_logout_redirect_uris,scopes,client_settings,token_settings,
 create_time,update_time,tenant_id,appcn)
VALUES
('c08-machine-client','client-machine',CURRENT_TIMESTAMP,'c08-secret','C08 isolated machine client',
 'client_secret_basic','client_credentials','','','openid','{}','',
 $NOW_MS,$NOW_MS,'owner-a','c08-machine');
INSERT INTO user_info
(id,username,password,jiacn,status,create_time,update_time,client_id,tenant_id)
VALUES (9001,'c08-user','c08-pass','owner-a',1,$NOW_MS,$NOW_MS,'client-a','owner-a');
SQL

cat > "$RUN/redis/redis.conf" <<EOF
bind 127.0.0.1
port 36379
requirepass c08-redis
save ""
appendonly no
daemonize no
dir $RUN/redis
EOF
chmod 0600 "$RUN/redis/redis.conf"
chown isp:isp "$RUN/redis/redis.conf"
setpriv --reuid=isp --regid=isp --init-groups \
  "$REDIS" "$RUN/redis/redis.conf" > "$RUN/logs/redis.log" 2>&1 &
REDIS_PID=$!
export REDIS_PID
redis_ping() {
  printf 'AUTH c08-redis\r\nPING\r\n' \
    | "$REDIS_CLI" -h 127.0.0.1 -p 36379 --raw 2>/dev/null \
    | grep -qx PONG
}
for _ in {1..60}; do
  redis_ping && break
  kill -0 "$REDIS_PID" 2>/dev/null || { cat "$RUN/logs/redis.log" >&2; exit 13; }
  sleep 1
done
redis_ping || exit 13

cat > "$RUN/isolated.properties" <<EOF
spring.application.name=cyf-c08-isolated
server.address=127.0.0.1
server.port=18018
server.ssl.enabled=false
server.shutdown=graceful
spring.main.banner-mode=off
spring.main.lazy-initialization=false
spring.datasource.type=com.zaxxer.hikari.HikariDataSource
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver
spring.datasource.url=jdbc:mysql://127.0.0.1:33317/c08?useUnicode=true&characterEncoding=utf-8&allowPublicKeyRetrieval=true&useSSL=false
spring.datasource.username=c08
spring.datasource.password=c08-pass
spring.datasource.hikari.minimum-idle=1
spring.datasource.hikari.maximum-pool-size=3
dynamic.datasource.enable=false
spring.data.redis.host=127.0.0.1
spring.data.redis.port=36379
spring.data.redis.database=0
spring.data.redis.password=c08-redis
spring.session.store-type=none
spring.autoconfigure.exclude=org.springframework.boot.amqp.autoconfigure.RabbitAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpClientAutoConfiguration,org.springframework.ai.mcp.client.common.autoconfigure.McpToolCallbackAutoConfiguration
spring.ai.mcp.client.enabled=false
spring.ai.mcp.client.toolcallback.enabled=false
spring.ai.model.chat=openai
spring.ai.model.embedding=openai
spring.ai.openai.api-key=isolated-test-key
spring.ai.openai.base-url=http://127.0.0.1:19999/v1
spring.ai.openai.chat.options.model=isolated
spring.ai.openai.embedding.options.model=isolated
spring.elasticsearch.uris=http://127.0.0.1:19200
spring.elasticsearch.connection-timeout=1s
spring.elasticsearch.socket-timeout=1s
management.health.elasticsearch.enabled=false
camunda.bpm.enabled=false
jia.chat.service.websocket.enable=false
juyiting.scene-state.enabled=false
juyiting.scene-events.enabled=false
agent.task-events.enabled=true
agent.task-events.allowed-scopes[0].tenant-id=owner-a
agent.task-events.allowed-scopes[0].client-id=client-a
oauth.resource.uris[0]=/agent/**
management.endpoints.web.exposure.include=health
management.endpoint.health.show-details=always
management.health.ldap.enabled=false
jia.file.path=$RUN/files
mat.web.realpath=$RUN/material
logging.level.root=INFO
logging.level.org.springframework.security=INFO
logging.level.org.springframework.security.oauth2=INFO
logging.level.org.springframework.web.servlet.DispatcherServlet=DEBUG
logging.level.org.springframework.web.servlet.mvc.method.annotation=DEBUG
logging.level.cn.jia.agent=DEBUG
server.error.include-message=always
server.error.include-exception=true
server.error.include-stacktrace=always
server.forward-headers-strategy=framework
logging.file.name=$RUN/logs/app.log
spring.task.scheduling.enabled=false
cors.allowed.origin.patterns=https://kit.chaoyoufan.cn
EOF
chmod 0600 "$RUN/isolated.properties"
chown isp:isp "$RUN/isolated.properties"

health_response_matches() {
  grep -Eq -- "$HEALTH_EXPECTED_REGEX" "$1"
}

start_api() {
  local ordinal="$1"
  : > "$RUN/logs/api-$ordinal.stdout.log"
  (
    cd "$RUN"
    exec setpriv --reuid=isp --regid=isp --init-groups \
      "$JAVA" -Xms96m -Xmx384m -jar "$API_JAR" \
      --spring.config.location="file:$RUN/isolated.properties" \
      > "$RUN/logs/api-$ordinal.stdout.log" 2>&1
  ) &
  APP_PID=$!
  export APP_PID
  local started=0 ready=0 code='' jwks_code='' login_code=''
  local health_body="$RUN/api-$ordinal-health.json"
  # Do not send HTTP until the non-lazy Spring context has fully started.
  # Readiness is release-contract bound: actuator health must be HTTP 200 and its
  # response body must match the exact health regex pinned by the r6 input.
  for _ in {1..180}; do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
      tail -240 "$RUN/logs/api-$ordinal.stdout.log" >&2 || true
      exit 14
    fi
    if grep -Fq 'Started JiaApplication' "$RUN/logs/api-$ordinal.stdout.log"; then
      started=1
      break
    fi
    sleep 1
  done
  (( started == 1 )) || { tail -240 "$RUN/logs/api-$ordinal.stdout.log" >&2 || true; exit 14; }
  for _ in {1..60}; do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
      tail -240 "$RUN/logs/api-$ordinal.stdout.log" >&2 || true
      exit 14
    fi
    code="$(curl --silent --output "$health_body" --max-time 15 --write-out '%{http_code}' http://127.0.0.1:18018/actuator/health 2>/dev/null || true)"
    jwks_code="$(curl --silent --output "$RUN/jwks-$ordinal.json" --max-time 15 --write-out '%{http_code}' http://127.0.0.1:18018/oauth2/jwks 2>/dev/null || true)"
    login_code="$(curl --silent --output /dev/null --max-time 15 --write-out '%{http_code}' http://127.0.0.1:18018/login/index.html 2>/dev/null || true)"
    if [[ "$code" == 200 && "$jwks_code" == 200 && "$login_code" =~ ^(200|401|3[0-9][0-9])$ ]] \
      && health_response_matches "$health_body" \
      && grep -q '"keys"' "$RUN/jwks-$ordinal.json"; then
      ready=1
      break
    fi
    sleep 1
  done
  (( ready == 1 )) || { tail -320 "$RUN/logs/api-$ordinal.stdout.log" >&2 || true; exit 14; }
  printf '%s\n' "$APP_PID" > "$EVIDENCE/api-$ordinal.pid"
  printf '%s\n' "$code" > "$EVIDENCE/api-$ordinal-health-http-status.txt"
  cp "$health_body" "$EVIDENCE/api-$ordinal-health.json"
  printf 'JWKS=%s\nLOGIN=%s\n' "$jwks_code" "$login_code" > "$EVIDENCE/api-$ordinal-security-readiness.txt"
}

stop_api() {
  local pid="$APP_PID"
  kill -TERM "$pid"
  for _ in {1..60}; do
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid"
    wait "$pid" 2>/dev/null || true
  else
    wait "$pid" 2>/dev/null || true
  fi
  APP_PID=''
  for _ in {1..30}; do
    if ! ss -lnt | grep -Eq '127\.0\.0\.1:18018\b'; then return 0; fi
    sleep 1
  done
  echo 'candidate API port remained open after stop' >&2
  exit 15
}

cat > "$RUN/openssl.cnf" <<'OPENSSL'
[req]
distinguished_name=dn
x509_extensions=v3
prompt=no
[dn]
CN=kit.chaoyoufan.cn
[v3]
subjectAltName=DNS:kit.chaoyoufan.cn,DNS:api.chaoyoufan.cn
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
basicConstraints=critical,CA:FALSE
OPENSSL
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -keyout "$RUN/tls.key" -out "$RUN/tls.crt" -config "$RUN/openssl.cnf" >/dev/null 2>&1

cat > "$RUN/smoke.html" <<'HTML'
<!doctype html><meta charset="utf-8"><title>C08 isolated browser smoke</title>
<meta name="c08-result" content="pending"><pre id="result">pending</pre>
<script>
(async () => {
  const out = document.querySelector('meta[name=c08-result]')
  const pre = document.querySelector('#result')
  const mode = new URL(location.href).searchParams.get('mode')
  const secret = new URLSearchParams(location.hash.slice(1))
  const token = secret.get('token') || ''
  const machine = secret.get('machine') || ''
  const actor = 'agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
  const base = '/__api/agent/tasks/task-c08'
  const encode = value => btoa(unescape(encodeURIComponent(JSON.stringify(value))))
  const finish = value => { const text = JSON.stringify(value); out.content = encode(value); pre.textContent = text; document.documentElement.dataset.c08Done = 'true' }
  const jsonCall = async (url, bearer) => {
    const response = await fetch(url, { headers: bearer ? { Authorization: `Bearer ${bearer}` } : {} })
    let body = null
    try { body = await response.json() } catch { body = null }
    return { status: response.status, cacheControl: response.headers.get('cache-control'), body }
  }
  const readSse = async (since, expected, bearer) => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 20000)
    const response = await fetch(`${base}/events?actorAgentId=${encodeURIComponent(actor)}&sinceVersion=${encodeURIComponent(since)}`, {
      headers: { Authorization: `Bearer ${bearer}`, Accept: 'text/event-stream', 'Last-Event-ID': String(since) },
      signal: controller.signal
    })
    const headers = {
      status: response.status,
      contentType: response.headers.get('content-type'),
      cacheControl: response.headers.get('cache-control'),
      xAccelBuffering: response.headers.get('x-accel-buffering')
    }
    if (!response.ok || !response.body) { clearTimeout(timer); return { headers, events: [] } }
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; const events = []
    try {
      while (events.length < expected) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
        let cut
        while ((cut = buffer.indexOf('\n\n')) >= 0) {
          const block = buffer.slice(0, cut); buffer = buffer.slice(cut + 2)
          const event = { event: '', id: null, data: null }
          for (const line of block.split('\n')) {
            if (line.startsWith('event:')) event.event = line.slice(6).trim()
            else if (line.startsWith('id:')) event.id = line.slice(3).trim()
            else if (line.startsWith('data:')) event.data = JSON.parse(line.slice(5).trim())
          }
          if (event.event) events.push(event)
          if (events.length >= expected) break
        }
      }
    } finally {
      clearTimeout(timer); try { await reader.cancel() } catch {}
    }
    return { headers, events }
  }
  try {
    if (mode === 'workspace-acl') {
      const valid = await jsonCall(`${base}/workspace?actorAgentId=${actor}`, token)
      const unauth = await jsonCall(`${base}/workspace?actorAgentId=${actor}`, '')
      const missingClaims = await jsonCall(`${base}/workspace?actorAgentId=${actor}`, machine)
      const wrongActor = await jsonCall(`${base}/workspace?actorAgentId=agt_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, token)
      finish({ ok: valid.status === 200 && valid.body?.task?.taskId === 'task-c08' && valid.body?.currentVersion === '1' && unauth.status === 401 && missingClaims.status === 403 && wrongActor.status === 404, valid, unauth, missingClaims, wrongActor })
    } else if (mode === 'sse-initial') {
      const stream = await readSse('0', 1, token)
      finish({ ok: stream.headers.status === 200 && /^text\/event-stream/.test(stream.headers.contentType || '') && stream.headers.cacheControl === 'private, no-store' && stream.headers.xAccelBuffering === 'no' && stream.events[0]?.event === 'task_event' && stream.events[0]?.id === '1' && stream.events[0]?.data?.eventId === 'c08-event-1', stream })
    } else if (mode === 'old-token-after-restart') {
      const result = await jsonCall(`${base}/workspace?actorAgentId=${actor}`, token)
      finish({ ok: result.status === 401, result })
    } else if (mode === 'sse-replay-after-restart') {
      const stream = await readSse('1', 1, token)
      finish({ ok: stream.headers.status === 200 && stream.events[0]?.event === 'task_event' && stream.events[0]?.id === '2' && stream.events[0]?.data?.eventId === 'c08-event-2', stream })
    } else if (mode === 'sse-resync') {
      const stream = await readSse('99', 1, token)
      finish({ ok: stream.headers.status === 200 && stream.events[0]?.event === 'resync_required' && stream.events[0]?.data?.currentVersion === '2' && stream.events[0]?.data?.reason === 'cursor_ahead', stream })
    } else throw new Error(`unknown mode: ${mode}`)
  } catch (error) { finish({ ok: false, error: String(error?.stack || error) }) }
})()
</script>
HTML

cat > "$RUN/nginx.conf" <<EOF
pid $RUN/nginx.pid;
error_log $RUN/logs/nginx-error.log notice;
daemon off;
master_process off;
events { worker_connections 256; }
http {
  include /home/isp/apps/nginx/conf/mime.types;
  default_type application/octet-stream;
  access_log $RUN/logs/nginx-access.log;
  sendfile on;
  server {
    listen 443 ssl;
    server_name kit.chaoyoufan.cn;
    ssl_certificate $RUN/tls.crt;
    ssl_certificate_key $RUN/tls.key;
    root $RUN/web;
    location = /__c08_smoke.html { alias $RUN/smoke.html; add_header Cache-Control 'no-store' always; }
    location /__api/ {
      proxy_pass http://127.0.0.1:18018/;
      proxy_http_version 1.1;
      proxy_set_header Host api.chaoyoufan.cn;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_buffering off;
      proxy_cache off;
      proxy_read_timeout 60s;
      add_header X-Accel-Buffering no always;
    }
    location / { try_files \$uri \$uri/ /index.html; }
  }
  server {
    listen 443 ssl;
    server_name api.chaoyoufan.cn;
    ssl_certificate $RUN/tls.crt;
    ssl_certificate_key $RUN/tls.key;
    location / {
      proxy_pass http://127.0.0.1:18018;
      proxy_http_version 1.1;
      proxy_set_header Host \$host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_buffering off;
      proxy_cache off;
      proxy_read_timeout 60s;
      add_header X-Accel-Buffering no always;
    }
  }
}
EOF
"$NGINX" -t -c "$RUN/nginx.conf" -p "$RUN" > "$EVIDENCE/nginx-config-test.txt" 2>&1
"$NGINX" -c "$RUN/nginx.conf" -p "$RUN" > "$RUN/logs/nginx-stdout.log" 2>&1 &
NGINX_PID=$!
export NGINX_PID
for _ in {1..60}; do
  curl --cacert "$RUN/tls.crt" --fail --silent --max-time 2 https://kit.chaoyoufan.cn/ > "$EVIDENCE/web-index.html" 2>/dev/null && break
  kill -0 "$NGINX_PID" 2>/dev/null || { cat "$RUN/logs/nginx-error.log" >&2; exit 16; }
  sleep 1
done
grep -Fq '<div id="app"></div>' "$EVIDENCE/web-index.html" || exit 16

cat > "$RUN/get_tokens.py" <<'PY'
from __future__ import print_function
import base64, hashlib, json, os, sys
from urllib.parse import urlencode, urljoin, urlparse, parse_qs
import requests
api, redirect, cert, output = sys.argv[1:]

def b64url(raw):
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')

debug=[]
def trace(label, response):
    debug.append({'label':label,'status':response.status_code,'location':response.headers.get('Location'),'url':response.url,'body':response.text[:1000]})

def auth_code_token():
    s = requests.Session()
    verifier = b64url(os.urandom(48))
    challenge = b64url(hashlib.sha256(verifier.encode('ascii')).digest())
    authorize = api + '/oauth2/authorize?' + urlencode({
        'response_type':'code','client_id':'client-a','scope':'openid',
        'redirect_uri':redirect,'code_challenge':challenge,
        'code_challenge_method':'S256','state':'/juyiting'
    })
    first=s.get(authorize, verify=cert, allow_redirects=False, timeout=15); trace('authorize-first',first)
    login = s.post(api + '/login', data={
        'loginType':'password','username':'c08-user','password':'c08-pass','redirect_uri':''
    }, verify=cert, allow_redirects=False, timeout=15)
    trace('login',login)
    location = login.headers.get('Location') or authorize
    code = ''
    for _ in range(12):
        target = urljoin(api + '/', location)
        if target.startswith(redirect):
            code = parse_qs(urlparse(target).query).get('code',[''])[0]
            break
        response = s.get(target, verify=cert, allow_redirects=False, timeout=15); trace('redirect-%s' % _, response)
        location = response.headers.get('Location') or ''
        if not location: break
    if not code:
        with open(output + '.debug.json','w') as d: json.dump(debug,d,sort_keys=True,indent=2)
        raise RuntimeError('authorization code was not returned')
    token = s.post(api + '/oauth2/token', data={
        'grant_type':'authorization_code','code':code,'redirect_uri':redirect,
        'client_id':'client-a','code_verifier':verifier
    }, verify=cert, timeout=15)
    token.raise_for_status()
    return token.json()['access_token']

def machine_token():
    response = requests.post(api + '/oauth2/token', data={
        'grant_type':'client_credentials','scope':'openid'
    }, auth=('client-machine','c08-secret'), verify=cert, timeout=15)
    response.raise_for_status()
    return response.json()['access_token']

def claims(token):
    part = token.split('.')[1]; part += '=' * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part.encode('ascii')).decode('utf-8'))
user = auth_code_token(); machine = machine_token()
with open(output, 'w') as stream:
    json.dump({'user':user,'machine':machine}, stream)
with open(output + '.claims.json', 'w') as stream:
    json.dump({'user':claims(user),'machine':claims(machine)}, stream, sort_keys=True, indent=2)
PY

get_tokens() {
  local ordinal="$1"
  python3 "$RUN/get_tokens.py" https://api.chaoyoufan.cn \
    https://kit.chaoyoufan.cn/oauth2/callback "$RUN/tls.crt" "$RUN/tokens-$ordinal.json"
  chmod 0600 "$RUN/tokens-$ordinal.json"
  cp "$RUN/tokens-$ordinal.json.claims.json" "$EVIDENCE/token-$ordinal-claims.json"
}

fragment_for() {
  local token_file="$1"
  python3 - "$token_file" <<'PY'
import json,sys
try:
 from urllib.parse import urlencode
except ImportError:
 from urllib import urlencode
v=json.load(open(sys.argv[1]))
print(urlencode({'token':v['user'],'machine':v.get('machine','')}))
PY
}

run_browser() {
  local mode="$1" token_file="$2" expected_current="$3"
  local fragment dom result
  fragment="$(fragment_for "$token_file")"
  dom="$EVIDENCE/browser-$mode.html"
  result="$EVIDENCE/browser-$mode.json"
  set +e
  timeout 45 "$CHROME" --headless=new --no-sandbox --disable-gpu \
    --disable-dev-shm-usage --ignore-certificate-errors --disable-background-networking \
    --disable-component-update --disable-default-apps --disable-sync --metrics-recording-only \
    --no-first-run --user-data-dir="$RUN/chrome/$mode" --virtual-time-budget=25000 \
    --dump-dom "https://kit.chaoyoufan.cn/__c08_smoke.html?mode=$mode#$fragment" \
    > "$dom" 2> "$EVIDENCE/browser-$mode.stderr.txt"
  local status=$?
  set -e
  (( status == 0 )) || { cat "$EVIDENCE/browser-$mode.stderr.txt" >&2; exit 17; }
  python3 - "$dom" "$result" <<'PY'
from __future__ import print_function
import base64, html, json, re, sys
text=open(sys.argv[1], encoding='utf-8').read()
m=re.search(r'<meta name="c08-result" content="([^"]+)">', text)
if not m or m.group(1) == 'pending': raise SystemExit('browser result meta is missing or pending')
raw=base64.b64decode(html.unescape(m.group(1))).decode('utf-8')
value=json.loads(raw)
with open(sys.argv[2], 'w') as out: json.dump(value,out,sort_keys=True,indent=2); out.write('\n')
if not value.get('ok'): raise SystemExit('browser smoke reported failure: '+raw)
PY
  python3 - "$result" "$expected_current" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); expected=sys.argv[2]
if expected and expected != '-':
 body=v.get('valid',{}).get('body',{})
 if body.get('currentVersion') != expected: raise SystemExit('unexpected workspace currentVersion')
PY
}

start_api 1
get_tokens 1
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 <<SQL
INSERT INTO agent_persona_binding
(id,jiacn,persona_code,agent_id,bound_at,status,tenant_id,client_id,create_time,update_time)
VALUES (9001,'owner-a','wuyong','agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',$NOW_MS,1,
        'owner-a','client-a',$NOW_MS,$NOW_MS);
INSERT INTO agent_identity_registry
(id,canonical_agent_id,canonical_type,lifecycle_status,client_id,owner_jiacn,tenant_id,
 binding_id,provisioned_at,activated_at,audit_reason,create_time,update_time)
VALUES (9001,'agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','OPAQUE','ACTIVE','client-a','owner-a','owner-a',
        9001,$NOW_MS,$NOW_MS,'c08 isolated smoke fixture',$NOW_MS,$NOW_MS);
INSERT INTO agent_task_meta
(id,task_id,reward_status,collaboration_mode,risk_level,max_agents,review_required,
 task_version,current_event_version,tenant_id,client_id,create_time,update_time)
VALUES (9001,'task-c08','assigned','team','low',3,0,1,1,'owner-a','client-a',$NOW_MS,$NOW_MS);
INSERT INTO agent_task_member
(id,task_id,agent_id,member_role,member_status,assignment_source,version,
 tenant_id,client_id,create_time,update_time)
VALUES (9001,'task-c08','agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','worker','accepted','manual',0,
        'owner-a','client-a',$NOW_MS,$NOW_MS);
INSERT INTO agent_task_event
(id,task_id,event_version,event_id,event_type,actor_type,actor_id,aggregate_type,aggregate_id,
 event_json,occurred_at,tenant_id,client_id,create_time,update_time)
VALUES (9001,'task-c08',1,'c08-event-1','TASK_ASSIGNED','system',NULL,'task','task-c08',
        '{"fromStatus":"open","toStatus":"assigned","resultVersion":1}',
        $NOW_MS,'owner-a','client-a',$NOW_MS,$NOW_MS);
SQL
USER_TOKEN_1="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["user"])' "$RUN/tokens-1.json")"
for target in direct proxy; do
  if [[ "$target" == direct ]]; then
    url='http://127.0.0.1:18018/agent/tasks/task-c08/workspace?actorAgentId=agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    tls_args=()
  else
    url='https://api.chaoyoufan.cn/agent/tasks/task-c08/workspace?actorAgentId=agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    tls_args=(--cacert "$RUN/tls.crt")
  fi
  curl "${tls_args[@]}" --silent --show-error --max-time 20 \
    --dump-header "$EVIDENCE/workspace-$target-before-browser.headers.txt" \
    --output "$EVIDENCE/workspace-$target-before-browser.json" \
    --write-out '%{http_code}\n' -H "Authorization: Bearer $USER_TOKEN_1" "$url" \
    > "$EVIDENCE/workspace-$target-before-browser.status.txt"
  grep -Fxq '200' "$EVIDENCE/workspace-$target-before-browser.status.txt" || {
    echo "workspace $target diagnostic failed" >&2
    cat "$EVIDENCE/workspace-$target-before-browser.headers.txt" >&2
    cat "$EVIDENCE/workspace-$target-before-browser.json" >&2
    exit 17
  }
done
unset USER_TOKEN_1
run_browser workspace-acl "$RUN/tokens-1.json" 1
run_browser sse-initial "$RUN/tokens-1.json" -

OLD_TOKEN_ONLY="$RUN/old-token.json"
python3 - "$RUN/tokens-1.json" "$OLD_TOKEN_ONLY" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); json.dump({'user':v['user'],'machine':''},open(sys.argv[2],'w'))
PY
stop_api

NOW2_MS="$(python3 - <<'PY'
import time
print(int(time.time()*1000))
PY
)"
"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot c08 <<SQL
INSERT INTO agent_task_event
(id,task_id,event_version,event_id,event_type,actor_type,actor_id,aggregate_type,aggregate_id,
 event_json,occurred_at,tenant_id,client_id,create_time,update_time)
VALUES (9002,'task-c08',2,'c08-event-2','TASK_STARTED','system',NULL,'task','task-c08',
        '{"fromStatus":"assigned","toStatus":"running","expectedVersion":1,"resultVersion":2}',
        $NOW2_MS,'owner-a','client-a',$NOW2_MS,$NOW2_MS);
UPDATE agent_task_meta SET reward_status='running',task_version=2,current_event_version=2,update_time=$NOW2_MS
WHERE tenant_id='owner-a' AND client_id='client-a' AND task_id='task-c08';
SQL
start_api 2
run_browser old-token-after-restart "$OLD_TOKEN_ONLY" -
get_tokens 2
run_browser sse-replay-after-restart "$RUN/tokens-2.json" -
run_browser sse-resync "$RUN/tokens-2.json" -

curl --cacert "$RUN/tls.crt" --silent --show-error --fail \
  -H "Authorization: Bearer $(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["user"])' "$RUN/tokens-2.json")" \
  'https://api.chaoyoufan.cn/agent/tasks/task-c08/workspace?actorAgentId=agt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' \
  > "$EVIDENCE/workspace-after-restart.json"
python3 - "$EVIDENCE/workspace-after-restart.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v['currentVersion']=='2' and v['task']['taskId']=='task-c08'
assert [e['version'] for e in v['recentEvents']]==['1','2']
PY

"$MYSQL_CLI" --protocol=socket --socket="$RUN/mysql/mysql.sock" -uroot -N -B c08 -e \
  "SELECT CONCAT(task_id,'|',reward_status,'|',task_version,'|',current_event_version) FROM agent_task_meta WHERE id=9001; SELECT CONCAT(event_version,'|',event_id,'|',event_type) FROM agent_task_event WHERE task_id='task-c08' ORDER BY event_version;" \
  > "$EVIDENCE/database-fixture-final.txt"
ss -lntp > "$EVIDENCE/listeners-during.txt"
ss -ntp > "$EVIDENCE/network-connections-after.txt"
if grep -E ':(3306|33060|5672|6379|9200|9300)\b' "$EVIDENCE/network-connections-after.txt"; then
  echo 'forbidden production dependency connection observed' >&2
  exit 18
fi
cp "$RUN/logs/api-1.stdout.log" "$EVIDENCE/api-1.stdout.log"
cp "$RUN/logs/api-2.stdout.log" "$EVIDENCE/api-2.stdout.log"
cp "$RUN/logs/mysql-init.log" "$EVIDENCE/mysql-init.log"
cp "$RUN/logs/mysql-server.log" "$EVIDENCE/mysql-server.log"
cp "$RUN/logs/redis.log" "$EVIDENCE/redis.log"
cp "$RUN/logs/nginx-error.log" "$EVIDENCE/nginx-error.log"
cp "$RUN/logs/nginx-access.log" "$EVIDENCE/nginx-access.log"

git -C "$ROOT/.worktrees/m2-api-base" status --porcelain=v1 --untracked-files=all > "$EVIDENCE/api-candidate-status-after.txt"
git -C "$ROOT/.worktrees/m2-web-base" status --porcelain=v1 --untracked-files=all > "$EVIDENCE/web-candidate-status-after.txt"
[[ ! -s "$EVIDENCE/api-candidate-status-after.txt" && ! -s "$EVIDENCE/web-candidate-status-after.txt" ]] || exit 19

cat > "$EVIDENCE/artifact-inputs.txt" <<EOF
API_HEAD=e45ba398f116a210091c892abb9fbc8111dcc411
API_TREE=8b80bf35c418b2ca0cead919f805db5bb70166eb
API_ARTIFACT_SHA256=$EXPECTED_API_SHA
WEB_HEAD=266583f2e59d5f1362ed4d653f58d02b78a0e6b5
WEB_TREE=ba7ed4f167c43b3af8a7f07d34d626308496cd36
R6_RELEASE_INPUT_SHA256=$EXPECTED_R6_INPUT_SHA
R6_RELEASE_RECORD_SHA256=$EXPECTED_R6_RELEASE_RECORD_SHA
R6_DEFAULT_OFF_WEB_ARTIFACT_SHA256=$EXPECTED_R6_WEB_SHA
FLAG_ON_SMOKE_WEB_ARCHIVE_SHA256=$EXPECTED_WEB_SHA
FLAG_ON_WEB_PROVENANCE_SHA256=$EXPECTED_WEB_PROVENANCE_SHA
HEALTH_EXPECTED_REGEX=$HEALTH_EXPECTED_REGEX
EOF
cat > "$EVIDENCE/result.txt" <<'EOF'
REAL_CHROMIUM=PASS
REAL_NGINX_REVERSE_PROXY=PASS
CANDIDATE_SPRING_BOOT=PASS
API_HEALTH_R6_CONTRACT=PASS
WORKSPACE_SNAPSHOT=PASS
SSE_INITIAL_REPLAY=PASS
API_RESTART=PASS
OLD_JWT_REJECTED_AFTER_RESTART=PASS
SSE_REPLAY_AFTER_RESTART=PASS
SSE_RESYNC_CURSOR_AHEAD=PASS
ACL_UNAUTHENTICATED_401=PASS
ACL_MISSING_CLAIMS_403=PASS
ACL_WRONG_ACTOR_404=PASS
PRODUCTION_DATABASE_OPERATION=NOT_PERFORMED
PRODUCTION_RABBITMQ_OPERATION=NOT_PERFORMED
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
EOF
python3 - "$EVIDENCE" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
needles = (b'--jasypt.encryptor.password=',)
leaks = []
for path in root.rglob('*'):
    if path.is_file() and not path.is_symlink():
        data = path.read_bytes()
        if any(needle in data for needle in needles):
            leaks.append(str(path.relative_to(root)))
if leaks:
    raise SystemExit('sensitive production argv material in evidence: ' + repr(leaks))
PY
DRIVER
chmod +x "$RUN/driver.sh"

SMOKE_UNIT="cyf-c08-combined-smoke-$$-$(date +%s)"
systemd-run --wait --pipe --collect --unit "$SMOKE_UNIT" -p Type=exec \
  "${SYSTEMD_MEMORY_ARGS[@]}" \
  /usr/bin/unshare -m -n -p --fork --kill-child=KILL --mount-proc -- \
  /usr/bin/env ROOT="$ROOT" RUN="$RUN" EVIDENCE="$EVIDENCE" API_JAR="$ISOLATED_API_JAR" \
  API_SCHEMA="$API_SCHEMA" CHAT_SCHEMA="$CHAT_SCHEMA" AGENT_SCHEMA="$AGENT_SCHEMA" \
  EXPECTED_API_SHA="$EXPECTED_API_SHA" EXPECTED_R6_INPUT_SHA="$EXPECTED_R6_INPUT_SHA" \
  EXPECTED_R6_RELEASE_RECORD_SHA="$EXPECTED_R6_RELEASE_RECORD_SHA" \
  EXPECTED_R6_WEB_SHA="$EXPECTED_R6_WEB_SHA" EXPECTED_WEB_SHA="$EXPECTED_WEB_SHA" \
  EXPECTED_WEB_PROVENANCE_SHA="$EXPECTED_WEB_PROVENANCE_SHA" \
  HEALTH_EXPECTED_REGEX="$HEALTH_EXPECTED_REGEX" \
  CGROUP_MEMORY_MAX_BYTES="$SMOKE_MEMORY_MAX_BYTES" \
  CGROUP_MEMORY_SWAP_MAX_BYTES="$SMOKE_MEMORY_SWAP_MAX_BYTES" \
  /bin/bash "$RUN/driver.sh"
production_identity_unchanged \
  || { echo 'production API identity changed during isolated smoke' >&2; exit 20; }
[[ "$(sha256sum "$PRODUCTION_LIVE_JAR" | awk '{print $1}')" == "$PRODUCTION_LIVE_JAR_SHA_BEFORE" ]] \
  || { echo 'production API JAR changed during isolated smoke' >&2; exit 20; }
printf '%s\n' 'PRODUCTION_API_IDENTITY_UNCHANGED=PASS' 'PRODUCTION_API_JAR_UNCHANGED=PASS' \
  >> "$EVIDENCE/host-resource-preflight.txt"

python3 - "$RUN" <<'PY'
import os, pathlib, sys
run = os.fsencode(sys.argv[1])
leaks = []
for proc in pathlib.Path('/proc').iterdir():
    if not proc.name.isdigit() or int(proc.name) == os.getpid():
        continue
    try:
        cmdline = (proc / 'cmdline').read_bytes()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if run in cmdline:
        leaks.append((proc.name, cmdline.replace(b'\0', b' ')[:500].decode('utf-8', 'replace')))
if leaks:
    raise SystemExit('isolated smoke process leak: ' + repr(leaks))
PY

# The outer runner appends production identity/JAR attestations only after the
# isolated unit exits. Seal and verify the final evidence bytes after that
# append so the copied manifest cannot attest a stale pre-append file.
(
  cd "$EVIDENCE"
  find . -type f \
    ! -name MANIFEST.sha256 ! -name MANIFEST.sha256.sha256 \
    ! -name manifest-check.txt ! -name manifest-check.txt.sha256 \
    -print0 | sort -z | xargs -0 sha256sum > "$RUN/MANIFEST.sha256.final"
  sha256sum -c "$RUN/MANIFEST.sha256.final" > "$RUN/manifest-check.final.txt"
  mv -fT -- "$RUN/MANIFEST.sha256.final" MANIFEST.sha256
  sha256sum MANIFEST.sha256 > MANIFEST.sha256.sha256
  mv -fT -- "$RUN/manifest-check.final.txt" manifest-check.txt
  sha256sum manifest-check.txt > manifest-check.txt.sha256
)

python3 - "$EVIDENCE" "$EVIDENCE_ROOT" <<'PY'
import os, shutil, sys
source,target=sys.argv[1:]
os.makedirs(os.path.dirname(target), exist_ok=True)
shutil.copytree(source,target)
PY
printf 'ISOLATED_COMBINED_SMOKE=PASS\nEVIDENCE=%s\n' "$EVIDENCE_ROOT"
