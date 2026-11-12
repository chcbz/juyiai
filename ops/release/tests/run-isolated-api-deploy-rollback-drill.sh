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
OLD_SOURCE=/home/isp/hosts/cyf/api/cyf-api-kit.jar
PRODUCTION_PID_FILE=/home/isp/hosts/cyf/api/cyf-api-kit.pid
API_ARTIFACT="$ROOT/deliverables/releases/m2-c08-r6/api/cyf-api-e45ba398f116a210091c892abb9fbc8111dcc411-8b80bf35c418b2ca0cead919f805db5bb70166eb.jar"
API_SCHEMA="$ROOT/.worktrees/m2-api-base/starter/src/test/resources/db/schema.sql"
CHAT_SCHEMA="$ROOT/.worktrees/m2-api-base/chat/jia-chat-mapper/src/test/resources/db/schema.sql"
AGENT_SCHEMA="$ROOT/.worktrees/m2-api-base/agent/jia-agent-mapper/src/main/resources/db/schema.sql"
JAR_TOOL=/home/isp/apps/jdk21/bin/jar
JAVAC_TOOL=/home/isp/apps/jdk21/bin/javac
EVIDENCE_ROOT="${1:-$ROOT/deliverables/m2-c08-20260822/isolated-api-deploy-rollback-drill-v2}"
MIN_HOST_DISK_AVAILABLE_BYTES=5905580032
DRILL_MEMORY_MAX=1200M
DRILL_MEMORY_MAX_BYTES=1258291200
DRILL_MEMORY_SWAP_MAX=256M
DRILL_MEMORY_SWAP_MAX_BYTES=268435456
HOST_MEMORY_RESERVE_BYTES=268435456
MIN_HOST_MEM_AVAILABLE_BYTES=$((DRILL_MEMORY_MAX_BYTES + HOST_MEMORY_RESERVE_BYTES))
if [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
  SYSTEMD_MEMORY_MODE=cgroup-v2
  SYSTEMD_MEMORY_ARGS=(-p MemoryAccounting=yes -p MemoryMax="$DRILL_MEMORY_MAX" -p MemorySwapMax="$DRILL_MEMORY_SWAP_MAX")
else
  SYSTEMD_MEMORY_MODE=cgroup-v1-driver-enforced-memsw
  SYSTEMD_MEMORY_ARGS=(-p MemoryAccounting=yes -p MemoryLimit="$DRILL_MEMORY_MAX")
fi

(( EUID == 0 )) || { echo 'isolated deploy/rollback drill requires root for namespaces and mounts' >&2; exit 2; }
[[ ! -e "$EVIDENCE_ROOT" && ! -L "$EVIDENCE_ROOT" ]] \
  || { echo "evidence target already exists: $EVIDENCE_ROOT" >&2; exit 2; }
for command in bash unshare mount ip python3 sha256sum curl ss awk grep sed flock stat cmp ps runuser setpriv unzip systemd-run git find sort xargs; do
  command -v "$command" >/dev/null 2>&1 || { echo "missing command: $command" >&2; exit 2; }
done
acquire_heavy_resource_lock
for path in "$INPUT" "$OLD_SOURCE" "$PRODUCTION_PID_FILE" "$API_ARTIFACT" "$API_SCHEMA" "$CHAT_SCHEMA" "$AGENT_SCHEMA"; do
  [[ -f "$path" && ! -L "$path" ]] || { echo "required physical file missing: $path" >&2; exit 2; }
done
[[ -x "$JAR_TOOL" && ! -L "$JAR_TOOL" ]] || { echo "required JAR tool missing: $JAR_TOOL" >&2; exit 2; }
[[ -x "$JAVAC_TOOL" && ! -L "$JAVAC_TOOL" ]] || { echo "required javac tool missing: $JAVAC_TOOL" >&2; exit 2; }
IFS=$'\t' read -r PRODUCTION_PID PRODUCTION_START_TICKS < <(python3 - "$PRODUCTION_PID_FILE" "$OLD_SOURCE" <<'PYPROD'
import os, pathlib, sys
pid_text = pathlib.Path(sys.argv[1]).read_text().strip()
if not pid_text.isdigit():
    raise SystemExit('production API pidfile is not numeric')
pid = int(pid_text)
proc = pathlib.Path('/proc') / str(pid)
if not proc.is_dir():
    raise SystemExit('production API is not running; isolated high-memory drill is fail-closed')
args = (proc / 'cmdline').read_bytes().split(b'\0')
jar_args = []
for index, arg in enumerate(args[:-1]):
    if arg == b'-jar':
        jar_args.append(os.path.realpath(os.fsdecode(args[index + 1])))
if jar_args != [os.path.realpath(sys.argv[2])]:
    raise SystemExit('production API PID does not identify the expected live JAR')
stat = (proc / 'stat').read_text()
end = stat.rfind(')')
if end < 0:
    raise SystemExit('production API proc stat is malformed')
fields = stat[end + 2:].split()
print(f"{pid}\t{fields[19]}")
PYPROD
)
HOST_MEM_AVAILABLE_BEFORE="$(awk '/^MemAvailable:/ {print $2 * 1024}' /proc/meminfo)"
HOST_DISK_AVAILABLE_BEFORE="$(df -PB1 -- "$ROOT" | awk 'NR==2 {print $4}')"
if (( HOST_MEM_AVAILABLE_BEFORE < MIN_HOST_MEM_AVAILABLE_BYTES )); then
  echo "host memory observation below former threshold (non-blocking): available=$HOST_MEM_AVAILABLE_BEFORE former_required=$MIN_HOST_MEM_AVAILABLE_BYTES" >&2
fi
if (( HOST_DISK_AVAILABLE_BEFORE < MIN_HOST_DISK_AVAILABLE_BYTES )); then
  echo "host disk observation below former threshold (non-blocking): available=$HOST_DISK_AVAILABLE_BEFORE former_required=$MIN_HOST_DISK_AVAILABLE_BYTES" >&2
fi
HEALTH_EXPECTED_REGEX="$(python3 - "$INPUT" <<'PYHEALTH'
import json, sys
with open(sys.argv[1], encoding='utf-8') as stream:
    print(json.load(stream)['api']['deploy']['healthExpectedRegex'])
PYHEALTH
)"
for sample in '{"status":"UP"}' '{"status":{"code":"UP","description":""}}'; do
  [[ "$sample" =~ $HEALTH_EXPECTED_REGEX ]] || { echo 'release health regex does not accept both supported health payloads' >&2; exit 2; }
done
[[ ! '{"status":"DOWN"}' =~ $HEALTH_EXPECTED_REGEX ]] \
  || { echo 'release health regex accepts a DOWN payload' >&2; exit 2; }

RUN="$(mktemp -d /tmp/cyf-c08-api-rollback.XXXXXX)"
SANDBOX="$RUN/sandbox"
EVIDENCE="$RUN/evidence"
CONTROL_VIEW="$RUN/control-view"
CONTROL_RELEASE="$CONTROL_VIEW/ops/release"
CONTROL_RELEASES="$CONTROL_VIEW/deliverables/releases"
CONTROL_API_REPO="$RUN/control-api-repo"
mkdir -p "$SANDBOX/api" "$EVIDENCE" "$RUN"/{mysql-source,mysql-restore,redis,files,material,logs}
mkdir -p "$CONTROL_VIEW/ops" "$CONTROL_RELEASES"
chmod 0755 "$RUN"
chmod 0755 "$EVIDENCE"
cp -a --reflink=auto -- "$ROOT/ops/release" "$CONTROL_RELEASE"
cp -a --reflink=auto -- "$ROOT/deliverables/releases/m2-c08-r6" "$CONTROL_RELEASES/m2-c08-r6"
if find "$CONTROL_VIEW" -type l -print -quit | grep -q .; then
  echo 'isolated control view contains a symlink' >&2
  exit 2
fi
find "$CONTROL_VIEW" -type d -exec chmod 0755 {} +
ISOLATED_INPUT="$CONTROL_RELEASE/m2-c08-r6-input.json"
[[ "$(sha256sum "$ISOLATED_INPUT" | awk '{print $1}')" == "$(sha256sum "$INPUT" | awk '{print $1}')" ]] || exit 2

# The release scripts and every file contributing to releaseToolSha256 stay
# byte-for-byte identical. Runtime-only schema adaptation is provided by a Java
# executable bind-mount inside the private mount/PID/network namespace.
ORIGINAL_DEPLOY_SHA="$(sha256sum "$ROOT/ops/release/deploy-api.sh" | awk '{print $1}')"
ORIGINAL_ROLLBACK_SHA="$(sha256sum "$ROOT/ops/release/rollback-api.sh" | awk '{print $1}')"
ISOLATED_DEPLOY_SHA="$(sha256sum "$CONTROL_RELEASE/deploy-api.sh" | awk '{print $1}')"
ISOLATED_ROLLBACK_SHA="$(sha256sum "$CONTROL_RELEASE/rollback-api.sh" | awk '{print $1}')"
[[ "$ISOLATED_DEPLOY_SHA" == "$ORIGINAL_DEPLOY_SHA" ]] || exit 2
[[ "$ISOLATED_ROLLBACK_SHA" == "$ORIGINAL_ROLLBACK_SHA" ]] || exit 2
ORIGINAL_RELEASE_TOOL_SHA="$(bash -c 'source "$1/common.sh"; release_tool_digest' _ "$ROOT/ops/release")"
ISOLATED_RELEASE_TOOL_SHA="$(bash -c 'source "$1/common.sh"; release_tool_digest' _ "$CONTROL_RELEASE")"
RECORDED_RELEASE_TOOL_SHA="$(python3 - "$CONTROL_RELEASES/m2-c08-r6/release"/*.json <<'PYTOOLSHA'
import json, pathlib, sys
paths = [pathlib.Path(value) for value in sys.argv[1:]]
if len(paths) != 1:
    raise SystemExit(f'expected one joint release record, found={len(paths)}')
print(json.loads(paths[0].read_text())['releaseToolSha256'])
PYTOOLSHA
)"
[[ "$ORIGINAL_RELEASE_TOOL_SHA" == "$ISOLATED_RELEASE_TOOL_SHA" \
   && "$ISOLATED_RELEASE_TOOL_SHA" == "$RECORDED_RELEASE_TOOL_SHA" ]] || exit 2
cat > "$EVIDENCE/isolated-control-byte-exact.txt" <<EOF
scope=ISOLATED_CONTROL_COPY_ONLY
production_release_scripts_modified=NO
original_deploy_sha256=$ORIGINAL_DEPLOY_SHA
isolated_deploy_sha256=$ISOLATED_DEPLOY_SHA
original_rollback_sha256=$ORIGINAL_ROLLBACK_SHA
isolated_rollback_sha256=$ISOLATED_ROLLBACK_SHA
original_release_tool_sha256=$ORIGINAL_RELEASE_TOOL_SHA
isolated_release_tool_sha256=$ISOLATED_RELEASE_TOOL_SHA
recorded_release_tool_sha256=$RECORDED_RELEASE_TOOL_SHA
release_tool_byte_exact=PASS
EOF

# deploy-api.sh deliberately runs as isp and verifies the frozen source
# worktree before touching the isolated live path. The host worktree and its
# Git index/loose objects are root-owned, so expose a private byte-exact copy
# with a minimal standalone Git directory. It is mounted read-only over the
# original absolute worktree path only inside the drill mount namespace.
mkdir -p "$CONTROL_API_REPO"
cp -a -- "$ROOT/.worktrees/m2-api-base/." "$CONTROL_API_REPO/"
python3 - "$CONTROL_API_REPO/.git" <<'PYGITPTR'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
if not path.is_file() or path.is_symlink():
    raise SystemExit('frozen API worktree .git pointer is not a physical file')
path.unlink()
PYGITPTR
mkdir -p "$CONTROL_API_REPO/.git/refs/heads/feat"
cp -- "$ROOT/api/.git/worktrees/m2-api-base/index" "$CONTROL_API_REPO/.git/index"
cp -a -- "$ROOT/api/.git/objects" "$CONTROL_API_REPO/.git/objects"
printf '%s\n' 'ref: refs/heads/feat/m2-api-base-20260803' > "$CONTROL_API_REPO/.git/HEAD"
printf '%s\n' 'e45ba398f116a210091c892abb9fbc8111dcc411' \
  > "$CONTROL_API_REPO/.git/refs/heads/feat/m2-api-base-20260803"
cat > "$CONTROL_API_REPO/.git/config" <<'GITCONFIG'
[core]
  repositoryformatversion = 0
  filemode = true
  bare = false
  logallrefupdates = true
GITCONFIG
chown -hR isp:isp "$CONTROL_API_REPO"
runuser -u isp -- git -C "$CONTROL_API_REPO" rev-parse --is-inside-work-tree | grep -Fxq true
[[ "$(runuser -u isp -- git -C "$CONTROL_API_REPO" rev-parse HEAD)" == e45ba398f116a210091c892abb9fbc8111dcc411 ]]
[[ "$(runuser -u isp -- git -C "$CONTROL_API_REPO" rev-parse 'HEAD^{tree}')" == 8b80bf35c418b2ca0cead919f805db5bb70166eb ]]
[[ "$(runuser -u isp -- git -C "$CONTROL_API_REPO" symbolic-ref --short HEAD)" == feat/m2-api-base-20260803 ]]
[[ -z "$(runuser -u isp -- git -C "$CONTROL_API_REPO" status --porcelain=v1 --untracked-files=all)" ]]
chmod 0755 "$RUN" "$RUN/logs"
chown -hR isp:isp "$RUN/mysql-source" "$RUN/mysql-restore" "$RUN/redis" "$RUN/logs" "$RUN/files" "$RUN/material"

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
  set +e
  if ! production_identity_unchanged; then
    printf 'CRITICAL: production API identity changed or stopped during isolated drill; no automatic restart was attempted\n' >&2
  fi
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

cat > "$EVIDENCE/host-resource-preflight.txt" <<EOF
PRODUCTION_API_PID=$PRODUCTION_PID
PRODUCTION_API_START_TICKS=$PRODUCTION_START_TICKS
HOST_MEM_AVAILABLE_BYTES=$HOST_MEM_AVAILABLE_BEFORE
HOST_DISK_AVAILABLE_BYTES=$HOST_DISK_AVAILABLE_BEFORE
FIXED_RESOURCE_ADMISSION_GATE=DISABLED_BY_USER_2026_08_28
MIN_HOST_MEM_AVAILABLE_BYTES=$MIN_HOST_MEM_AVAILABLE_BYTES
HOST_MEMORY_RESERVE_BYTES=$HOST_MEMORY_RESERVE_BYTES
MIN_HOST_DISK_AVAILABLE_BYTES=$MIN_HOST_DISK_AVAILABLE_BYTES
SYSTEMD_OUTER_MEMORY_MODE=$SYSTEMD_MEMORY_MODE
CGROUP_MEMORY_MAX=$DRILL_MEMORY_MAX
CGROUP_MEMORY_MAX_BYTES=$DRILL_MEMORY_MAX_BYTES
CGROUP_MEMORY_SWAP_MAX=$DRILL_MEMORY_SWAP_MAX
CGROUP_MEMORY_SWAP_MAX_BYTES=$DRILL_MEMORY_SWAP_MAX_BYTES
EOF
{
  printf '%s\n' 'scope=READ_ONLY_RELEASE_HASH_PREFLIGHT'
  (
    cd "$(dirname "$INPUT")"
    sha256sum -c "$(basename "$INPUT").sha256"
  )
  while IFS= read -r -d '' sidecar; do
    (
      cd "$(dirname "$sidecar")"
      sha256sum -c "$(basename "$sidecar")"
    )
  done < <(find "$ROOT/deliverables/releases/m2-c08-r6" -type f -name '*.sha256' -print0 | sort -z)
  printf '%s\n' 'READ_ONLY_RELEASE_HASH_PREFLIGHT=PASS'
} > "$EVIDENCE/release-preflight.log" 2>&1
mapfile -t OLD_AGENT_MAPPER_ENTRIES < <("$JAR_TOOL" tf "$OLD_SOURCE" | grep -E '^BOOT-INF/lib/jia-agent-mapper-[^/]+\.jar$')
(( ${#OLD_AGENT_MAPPER_ENTRIES[@]} == 1 )) \
  || { echo "expected exactly one old agent mapper JAR; found=${#OLD_AGENT_MAPPER_ENTRIES[@]}" >&2; exit 2; }
mapfile -t OLD_CHAT_MAPPER_ENTRIES < <("$JAR_TOOL" tf "$OLD_SOURCE" | grep -E '^BOOT-INF/lib/jia-chat-mapper-[^/]+\.jar$')
(( ${#OLD_CHAT_MAPPER_ENTRIES[@]} == 1 )) \
  || { echo "expected exactly one old chat mapper JAR; found=${#OLD_CHAT_MAPPER_ENTRIES[@]}" >&2; exit 2; }
OLD_AGENT_MAPPER_JAR="$RUN/old-agent-mapper.jar"
OLD_AGENT_SCHEMA="$RUN/old-agent-schema.sql"
OLD_CHAT_MAPPER_JAR="$RUN/old-chat-mapper.jar"
OLD_CHAT_SCHEMA="$RUN/old-chat-schema.sql"
unzip -p "$OLD_SOURCE" "${OLD_AGENT_MAPPER_ENTRIES[0]}" > "$OLD_AGENT_MAPPER_JAR"
unzip -p "$OLD_AGENT_MAPPER_JAR" db/schema.sql > "$OLD_AGENT_SCHEMA"
unzip -p "$OLD_SOURCE" "${OLD_CHAT_MAPPER_ENTRIES[0]}" > "$OLD_CHAT_MAPPER_JAR"
mapfile -t OLD_CHAT_SCHEMA_ENTRIES < <("$JAR_TOOL" tf "$OLD_CHAT_MAPPER_JAR" | grep -E '^db/task-thread-schema\.sql$')
(( ${#OLD_CHAT_SCHEMA_ENTRIES[@]} == 1 )) \
  || { echo "expected exactly one old task-thread schema; found=${#OLD_CHAT_SCHEMA_ENTRIES[@]}" >&2; exit 2; }
unzip -p "$OLD_CHAT_MAPPER_JAR" "${OLD_CHAT_SCHEMA_ENTRIES[0]}" > "$OLD_CHAT_SCHEMA"
[[ -s "$OLD_AGENT_SCHEMA" && -s "$OLD_CHAT_SCHEMA" ]] \
  || { echo 'old API embedded agent/chat schema is empty' >&2; exit 2; }
OLD_SOURCE_SHA_BEFORE="$(sha256sum "$OLD_SOURCE" | awk '{print $1}')"
CANDIDATE_SHA="$(sha256sum "$API_ARTIFACT" | awk '{print $1}')"
[[ "$OLD_SOURCE_SHA_BEFORE" != "$CANDIDATE_SHA" ]] || { echo 'old and candidate API artifacts are identical' >&2; exit 2; }
cp --reflink=auto -- "$OLD_SOURCE" "$SANDBOX/api/cyf-api-kit.jar"
cp --reflink=auto -- "$OLD_SOURCE" "$RUN/old-api-artifact.jar"
chmod 0644 "$SANDBOX/api/cyf-api-kit.jar"
chmod 0444 "$RUN/old-api-artifact.jar"
OLD_API_SHA="$(sha256sum "$SANDBOX/api/cyf-api-kit.jar" | awk '{print $1}')"
[[ "$OLD_API_SHA" == "$OLD_SOURCE_SHA_BEFORE" ]] || exit 2
mkdir -p "$SANDBOX/baks/legacy-api/releases" "$SANDBOX/baks/legacy-api/release-records" "$SANDBOX/api/logs" "$SANDBOX/api/backups/db"
chown -hR isp:isp "$SANDBOX/api"
mkdir -p "$EVIDENCE/schema-transitions" "$EVIDENCE/schema-launches"
chown isp:isp "$EVIDENCE/schema-transitions" "$EVIDENCE/schema-launches"
chmod 0755 "$EVIDENCE/schema-transitions" "$EVIDENCE/schema-launches"
cat > "$SANDBOX/api/isolated-schema-transition.sh" <<'SCHEMATRANSITION'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

[[ "$#" == 1 && ( "$1" == old || "$1" == candidate ) ]] \
  || { echo 'usage: isolated-schema-transition.sh old|candidate' >&2; exit 2; }
target="$1"
socket="${CYF_C08_ISOLATED_SCHEMA_SOCKET:-}"
evidence="${CYF_C08_ISOLATED_SCHEMA_EVIDENCE:-}"
live_jar=/home/isp/hosts/cyf/api/cyf-api-kit.jar
agent=/home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar
old_sha="${CYF_C08_OLD_API_SHA256:-}"
candidate_sha="${CYF_C08_CANDIDATE_API_SHA256:-}"
agent_sha="${CYF_C08_ISOLATED_SCHEMA_AGENT_SHA256:-}"
real_java="${CYF_C08_REAL_JAVA:-}"
premain_mode="${CYF_C08_SCHEMA_AGENT_PREMAIN:-}"
[[ "$old_sha" =~ ^[0-9a-f]{64}$ && "$candidate_sha" =~ ^[0-9a-f]{64}$ && "$old_sha" != "$candidate_sha" ]] \
  || { echo 'isolated artifact identity is invalid' >&2; exit 2; }
[[ "$socket" == /tmp/cyf-c08-api-rollback.*/mysql-source/mysql.sock && -S "$socket" ]] \
  || { echo 'isolated schema socket is invalid' >&2; exit 2; }
run="${socket%/mysql-source/mysql.sock}"
[[ "$run" == /tmp/cyf-c08-api-rollback.* && -d "$run" && ! -L "$run" \
   && "$(realpath -e -- "$run")" == "$run" ]] \
  || { echo 'isolated run root is invalid' >&2; exit 2; }
datadir="$run/mysql-source"
pid_file="$datadir/mysql.pid"
state_dir="$run/schema-transition-state"
[[ "$evidence" == "$run/evidence/schema-transitions" && -d "$evidence" && ! -L "$evidence" \
   && "$state_dir" == /tmp/cyf-c08-api-rollback.*/schema-transition-state \
   && -d "$state_dir" && ! -L "$state_dir" ]] \
  || { echo 'isolated schema evidence/state path is invalid' >&2; exit 2; }
[[ -f "$live_jar" && ! -L "$live_jar" ]] || { echo 'isolated live JAR is invalid' >&2; exit 2; }
MYSQL_CLI=/home/isp/apps/mysql/bin/mysql
[[ -x "$MYSQL_CLI" && ! -L "$MYSQL_CLI" ]] || exit 2
for command in awk cmp cut flock mktemp mv python3 realpath sha256sum ss; do
  command -v "$command" >/dev/null 2>&1 || { echo "missing helper command: $command" >&2; exit 2; }
done
exec 9>"$state_dir/transition.lock"
flock -x 9

[[ -f "$pid_file" && ! -L "$pid_file" ]] || { echo 'isolated MySQL pidfile is invalid' >&2; exit 2; }
mysql_pid="$(cat -- "$pid_file")"
[[ "$mysql_pid" =~ ^[1-9][0-9]*$ && -d "/proc/$mysql_pid" ]] \
  || { echo 'isolated MySQL PID is invalid' >&2; exit 2; }
mysql_comm="$(cat -- "/proc/$mysql_pid/comm")"
[[ "$mysql_comm" == mysqld ]] || { echo 'isolated MySQL process identity is invalid' >&2; exit 2; }
mysql_start_ticks="$(python3 - "$mysql_pid" <<'PYTICKS'
import pathlib, sys
text = (pathlib.Path('/proc') / sys.argv[1] / 'stat').read_text()
end = text.rfind(')')
if end < 0:
    raise SystemExit('malformed isolated MySQL stat')
print(text[end + 2:].split()[19])
PYTICKS
)"
IFS=$'\t' read -r runtime_datadir runtime_socket runtime_port runtime_pid_file < <(
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT @@datadir,@@socket,@@port,@@pid_file"
)
[[ "$(realpath -e -- "${runtime_datadir%/}")" == "$datadir" \
   && "$runtime_socket" == "$socket" && "$runtime_port" == 33317 \
   && "$runtime_pid_file" == "$pid_file" ]] \
  || { echo 'isolated MySQL runtime identity mismatch' >&2; exit 2; }

allowed_java_pid=''
if [[ -n "$premain_mode" ]]; then
  [[ "$premain_mode" == YES ]] \
    || { echo 'invalid isolated schema javaagent premain marker' >&2; exit 2; }
  allowed_java_pid="$PPID"
  [[ "$allowed_java_pid" =~ ^[1-9][0-9]*$ && -d "/proc/$allowed_java_pid" \
     && "$(cat -- "/proc/$allowed_java_pid/comm")" == java \
     && "$real_java" == /tmp/cyf-c08-api-rollback.*/real-jdk/bin/java \
     && -x "$real_java" && ! -L "$real_java" \
     && "$(stat -Lc '%d:%i' -- "/proc/$allowed_java_pid/exe")" \
        == "$(stat -Lc '%d:%i' -- "$real_java")" \
     && -f "$agent" && ! -L "$agent" && "$agent_sha" =~ ^[0-9a-f]{64}$ \
     && "$(stat -c %a -- "$agent")" == 444 \
     && "$(sha256sum "$agent" | awk '{print $1}')" == "$agent_sha" ]] \
    || { echo 'isolated schema javaagent parent identity mismatch' >&2; exit 2; }
  parent_agent_count=0
  parent_jar_count=0
  previous=''
  while IFS= read -r -d '' arg; do
    [[ "$arg" != "-javaagent:$agent=$target" ]] || (( parent_agent_count += 1 ))
    if [[ "$previous" == -jar && "$arg" == "$live_jar" ]]; then
      (( parent_jar_count += 1 ))
    fi
    previous="$arg"
  done < "/proc/$allowed_java_pid/cmdline"
  (( parent_agent_count == 1 && parent_jar_count == 1 )) \
    || { echo 'isolated schema javaagent parent argv identity mismatch' >&2; exit 2; }
fi

if ss -H -lnt | awk '$4 ~ /:10018$/ { found=1 } END { exit !found }'; then
  echo 'API listener 10018 is still active before schema transition' >&2
  exit 2
fi
for proc in /proc/[0-9]*; do
  [[ -r "$proc/cmdline" && -r "$proc/comm" ]] || continue
  [[ "$(cat -- "$proc/comm")" == java ]] || continue
  [[ -n "$allowed_java_pid" && "${proc##*/}" == "$allowed_java_pid" ]] && continue
  previous=''
  while IFS= read -r -d '' arg; do
    if [[ "$previous" == -jar ]]; then
      if [[ "$arg" == "$live_jar" || ( "$arg" != /* && "$(realpath -m -- "$proc/cwd/$arg")" == "$live_jar" ) ]]; then
        echo "API Java JAR process still active before schema transition: ${proc##*/}" >&2
        exit 2
      fi
    fi
    previous="$arg"
  done < "$proc/cmdline"
done

jar_sha="$(sha256sum "$live_jar" | awk '{print $1}')"
case "$jar_sha" in
  "$old_sha") jar_target=old ;;
  "$candidate_sha") jar_target=candidate ;;
  *) echo 'isolated live JAR SHA is not approved' >&2; exit 2 ;;
esac
[[ "$target" == "$jar_target" ]] \
  || { echo "schema target/JAR mismatch: target=$target jar_target=$jar_target" >&2; exit 2; }

query_metadata() {
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT table_name,column_name,is_nullable,IF(column_default IS NULL,'<SQL_NULL>',CONCAT('VALUE:',column_default)),data_type,character_maximum_length,collation_name FROM information_schema.columns WHERE table_schema='c08' AND ((table_name='agent_task_thread' AND column_name='tenant_id') OR (table_name='agent_task_backfill_issue' AND column_name='tenant_id') OR (table_name='agent_task_backfill_manifest' AND column_name='tenant_id')) ORDER BY table_name"
}
write_expected() {
  local mode="$1" output="$2" contract_default
  [[ "$mode" == old ]] && contract_default='VALUE:0' || contract_default='<SQL_NULL>'
  printf 'agent_task_backfill_issue\ttenant_id\tYES\t%s\tvarchar\t50\tutf8mb4_0900_bin\n' "$contract_default" > "$output"
  printf 'agent_task_backfill_manifest\ttenant_id\tYES\t%s\tvarchar\t50\tutf8mb4_0900_bin\n' "$contract_default" >> "$output"
  printf 'agent_task_thread\ttenant_id\tNO\t%s\tvarchar\t50\tutf8mb4_0900_bin\n' "$contract_default" >> "$output"
}
record="$(mktemp "$evidence/schema-transition-${target}.XXXXXX")"
query_metadata > "${record}.before"
printf '%s\n' \
  $'agent_task_backfill_issue\ttenant_id\tYES\tvarchar\t50\tutf8mb4_0900_bin' \
  $'agent_task_backfill_manifest\ttenant_id\tYES\tvarchar\t50\tutf8mb4_0900_bin' \
  $'agent_task_thread\ttenant_id\tNO\tvarchar\t50\tutf8mb4_0900_bin' \
  > "${record}.base-expected"
cut -f1,2,3,5,6,7 "${record}.before" > "${record}.base-actual"
cmp "${record}.base-expected" "${record}.base-actual" \
  || { echo 'tenant_id non-default metadata drift detected' >&2; exit 2; }
write_expected old "${record}.old-expected"
write_expected candidate "${record}.candidate-expected"
if cmp -s "${record}.old-expected" "${record}.before"; then
  pre_state=OLD
elif cmp -s "${record}.candidate-expected" "${record}.before"; then
  pre_state=CANDIDATE
elif awk -F '\t' 'NF != 7 || ($4 != "VALUE:0" && $4 != "<SQL_NULL>") { bad=1 } END { exit bad || NR != 3 }' "${record}.before"; then
  pre_state=MIXED
else
  echo 'tenant_id defaults contain an unknown third state' >&2
  exit 2
fi

marker="$state_dir/ddl-in-progress"
if [[ "$pre_state" == MIXED ]]; then
  [[ -f "$marker" && ! -L "$marker" && "$(stat -c %a -- "$marker")" == 600 ]] \
    || { echo 'mixed schema state has no valid interrupted-transition marker' >&2; exit 2; }
  grep -Fxq 'schema=c08' "$marker" \
    && grep -Eq '^target=(old|candidate)$' "$marker" \
    && grep -Eq '^pre_state=(OLD|CANDIDATE|MIXED)$' "$marker" \
    && grep -Eq "^jar_sha256=($old_sha|$candidate_sha)$" "$marker" \
    && grep -Fxq "mysql_pid=$mysql_pid" "$marker" \
    && grep -Fxq "mysql_start_ticks=$mysql_start_ticks" "$marker" \
    || { echo 'interrupted-transition marker is malformed or stale' >&2; exit 2; }
fi
marker_temp="$(mktemp "$state_dir/.ddl-in-progress.XXXXXX")"
{
  printf 'schema=c08\n'
  printf 'target=%s\n' "$target"
  printf 'pre_state=%s\n' "$pre_state"
  printf 'jar_sha256=%s\n' "$jar_sha"
  printf 'mysql_pid=%s\n' "$mysql_pid"
  printf 'mysql_start_ticks=%s\n' "$mysql_start_ticks"
} > "$marker_temp"
chmod 0600 "$marker_temp"
mv -fT -- "$marker_temp" "$marker"

interrupt_after="${CYF_C08_SCHEMA_TEST_INTERRUPT_AFTER:-0}"
[[ "$interrupt_after" =~ ^[012]$ ]] || { echo 'invalid isolated interruption test value' >&2; exit 2; }
if [[ "${pre_state,,}" != "$target" || "$pre_state" == MIXED ]]; then
  if [[ "$target" == candidate ]]; then
    ddl_action='DROP DEFAULT'
  else
    ddl_action="SET DEFAULT '0'"
  fi
  changed=0
  for table in agent_task_thread agent_task_backfill_issue agent_task_backfill_manifest; do
    "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot c08 -e \
      "SET SESSION lock_wait_timeout=5; ALTER TABLE $table ALTER COLUMN tenant_id $ddl_action;"
    changed=$((changed + 1))
    if (( interrupt_after == changed )); then
      printf 'INTENTIONAL_ISOLATED_DDL_INTERRUPT=%s\n' "$changed" >&2
      exit 97
    fi
  done
fi
query_metadata > "${record}.after"
write_expected "$target" "${record}.expected"
cmp "${record}.expected" "${record}.after" \
  || { echo 'post-transition exact schema assertion failed' >&2; exit 2; }
rm -f -- "$marker"
{
  printf 'scope=ISOLATED_FIXTURE_ONLY\n'
  printf 'schema=c08\n'
  printf 'target=%s\n' "$target"
  printf 'pre_state=%s\n' "$pre_state"
  printf 'jar_sha256=%s\n' "$jar_sha"
  printf 'mysql_pid=%s\n' "$mysql_pid"
  printf 'mysql_start_ticks=%s\n' "$mysql_start_ticks"
  printf 'lock_wait_timeout_seconds=5\n'
  printf 'production_database_operation=NOT_PERFORMED\n'
  printf 'production_rabbitmq_operation=NOT_PERFORMED\n'
  sha256sum "${record}.before" "${record}.after" "${record}.expected" \
    "${record}.base-expected" "${record}.base-actual"
} > "$record"
chmod 0444 "$record" "${record}.before" "${record}.after" "${record}.expected" \
  "${record}.base-expected" "${record}.base-actual" \
  "${record}.old-expected" "${record}.candidate-expected"
SCHEMATRANSITION
chown root:root "$SANDBOX/api/isolated-schema-transition.sh"
chmod 0555 "$SANDBOX/api/isolated-schema-transition.sh"
SCHEMA_TRANSITION_SHA="$(sha256sum "$SANDBOX/api/isolated-schema-transition.sh" | awk '{print $1}')"
mkdir -p "$RUN/schema-transition-state" "$RUN/java-launch-state" "$RUN/real-jdk" \
  "$RUN/schema-agent-build/classes"
chown isp:isp "$RUN/schema-transition-state" "$RUN/java-launch-state"
chmod 0755 "$RUN/schema-transition-state" "$RUN/java-launch-state" "$RUN/real-jdk"
cat > "$RUN/schema-agent-build/IsolatedSchemaTransitionAgent.java" <<'JAVAAGENT'
package cn.cyf.release;

public final class IsolatedSchemaTransitionAgent {
    private IsolatedSchemaTransitionAgent() {
    }

    public static void premain(String target) throws Exception {
        if (!"old".equals(target) && !"candidate".equals(target)) {
            throw new IllegalArgumentException("invalid isolated schema transition target");
        }
        ProcessBuilder builder = new ProcessBuilder(
                "/home/isp/hosts/cyf/api/isolated-schema-transition.sh", target)
                .inheritIO();
        builder.environment().put("CYF_C08_SCHEMA_AGENT_PREMAIN", "YES");
        Process process = builder.start();
        int status = process.waitFor();
        if (status != 0) {
            throw new IllegalStateException(
                    "isolated schema transition failed before application main; status=" + status);
        }
    }
}
JAVAAGENT
cat > "$RUN/schema-agent-build/MANIFEST.MF" <<'AGENTMANIFEST'
Manifest-Version: 1.0
Premain-Class: cn.cyf.release.IsolatedSchemaTransitionAgent
Can-Redefine-Classes: false
Can-Retransform-Classes: false

AGENTMANIFEST
"$JAVAC_TOOL" -d "$RUN/schema-agent-build/classes" \
  "$RUN/schema-agent-build/IsolatedSchemaTransitionAgent.java"
"$JAR_TOOL" cfm "$SANDBOX/api/isolated-schema-transition-agent.jar" \
  "$RUN/schema-agent-build/MANIFEST.MF" -C "$RUN/schema-agent-build/classes" .
chown root:root "$SANDBOX/api/isolated-schema-transition-agent.jar"
chmod 0444 "$SANDBOX/api/isolated-schema-transition-agent.jar"
SCHEMA_AGENT_SHA="$(sha256sum "$SANDBOX/api/isolated-schema-transition-agent.jar" | awk '{print $1}')"

cat > "$SANDBOX/api/isolated-java-launch-shim.sh" <<'JAVASHIM'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

live_jar=/home/isp/hosts/cyf/api/cyf-api-kit.jar
helper=/home/isp/hosts/cyf/api/isolated-schema-transition.sh
agent=/home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar
real_java="${CYF_C08_REAL_JAVA:-}"
state_dir="${CYF_C08_JAVA_LAUNCH_STATE:-}"
evidence="${CYF_C08_SCHEMA_LAUNCH_EVIDENCE:-}"
old_sha="${CYF_C08_OLD_API_SHA256:-}"
candidate_sha="${CYF_C08_CANDIDATE_API_SHA256:-}"
helper_sha="${CYF_C08_ISOLATED_SCHEMA_TRANSITION_SHA256:-}"
agent_sha="${CYF_C08_ISOLATED_SCHEMA_AGENT_SHA256:-}"
[[ "$real_java" == /tmp/cyf-c08-api-rollback.*/real-jdk/bin/java && -x "$real_java" && ! -L "$real_java" ]] \
  || { echo 'isolated real Java path is invalid' >&2; exit 2; }
[[ "$state_dir" == /tmp/cyf-c08-api-rollback.*/java-launch-state && -d "$state_dir" && ! -L "$state_dir" \
   && "$evidence" == /tmp/cyf-c08-api-rollback.*/evidence/schema-launches && -d "$evidence" && ! -L "$evidence" ]] \
  || { echo 'isolated Java launch state/evidence is invalid' >&2; exit 2; }
[[ -x "$helper" && ! -L "$helper" && "$helper_sha" =~ ^[0-9a-f]{64}$ \
   && "$(sha256sum "$helper" | awk '{print $1}')" == "$helper_sha" ]] \
  || { echo 'isolated schema helper identity mismatch' >&2; exit 2; }
[[ -f "$agent" && ! -L "$agent" && "$agent_sha" =~ ^[0-9a-f]{64}$ \
   && "$(stat -c %a -- "$agent")" == 444 \
   && "$(sha256sum "$agent" | awk '{print $1}')" == "$agent_sha" ]] \
  || { echo 'isolated schema javaagent identity mismatch' >&2; exit 2; }
[[ "$old_sha" =~ ^[0-9a-f]{64}$ && "$candidate_sha" =~ ^[0-9a-f]{64}$ && "$old_sha" != "$candidate_sha" ]] \
  || { echo 'isolated approved JAR identities are invalid' >&2; exit 2; }

raw_args=("$@")
args=()
prior_agent_count=0
for arg in "${raw_args[@]}"; do
  case "$arg" in
    "-javaagent:$agent=old"|"-javaagent:$agent=candidate")
      (( prior_agent_count += 1 ))
      ;;
    *) args+=("$arg") ;;
  esac
done
(( prior_agent_count <= 1 )) \
  || { echo 'multiple replayed isolated schema javaagents detected' >&2; exit 2; }
jar_index=-1
for ((index=0; index < ${#args[@]} - 1; index++)); do
  if [[ "${args[$index]}" == -jar ]]; then
    (( jar_index == -1 )) || { echo 'multiple -jar options passed to isolated Java shim' >&2; exit 2; }
    jar_index=$index
  fi
done
(( jar_index >= 0 )) || { echo 'isolated Java shim only accepts -jar launches' >&2; exit 2; }
[[ "${args[$((jar_index + 1))]}" == "$live_jar" ]] \
  || { echo 'isolated Java shim received an unexpected JAR path' >&2; exit 2; }
jar_sha="$(sha256sum "$live_jar" | awk '{print $1}')"
case "$jar_sha" in
  "$old_sha") target=old ;;
  "$candidate_sha") target=candidate ;;
  *) echo 'isolated Java shim rejected unknown live JAR SHA' >&2; exit 2 ;;
esac
exec 8>"$state_dir/launch.lock"
flock -x 8

fault=none
mode_file="$state_dir/fault-mode"
if [[ -f "$mode_file" && ! -L "$mode_file" ]]; then
  mode="$(cat -- "$mode_file")"
  case "$mode:$target" in
    candidate-health-once:candidate|old-health-once:old)
      consumed="$state_dir/fault-consumed-$mode"
      [[ ! -e "$consumed" && ! -L "$consumed" ]] \
        || { echo 'isolated health fault was already consumed' >&2; exit 2; }
      printf 'mode=%s\ntarget=%s\njar_sha256=%s\n' "$mode" "$target" "$jar_sha" > "$consumed"
      chmod 0444 "$consumed"
      rm -f -- "$mode_file"
      fault="$mode"
      args+=(--server.port=10019 --management.server.port=10019)
      ;;
    candidate-health-once:old|old-health-once:candidate) ;;
    *) echo 'invalid isolated Java health fault mode' >&2; exit 2 ;;
  esac
fi
record="$(mktemp "$evidence/java-launch-${target}.XXXXXX")"
{
  printf 'scope=ISOLATED_JAVA_LAUNCH_SHIM\n'
  printf 'target=%s\n' "$target"
  printf 'jar_sha256=%s\n' "$jar_sha"
  printf 'schema_transition_sha256=%s\n' "$helper_sha"
  printf 'schema_agent_sha256=%s\n' "$agent_sha"
  printf 'schema_boundary=JAVA_AGENT_PREMAIN_BEFORE_APPLICATION_MAIN\n'
  printf 'replayed_schema_agent_removed=%s\n' "$prior_agent_count"
  printf 'fault=%s\n' "$fault"
  printf 'production_deployment=NOT_PERFORMED\n'
  printf 'production_database_operation=NOT_PERFORMED\n'
  printf 'production_rabbitmq_operation=NOT_PERFORMED\n'
} > "$record"
chmod 0444 "$record"
exec 8>&-
exec -a /home/isp/apps/jdk21/bin/java "$real_java" \
  "-javaagent:$agent=$target" "${args[@]}"
JAVASHIM
chown root:root "$SANDBOX/api/isolated-java-launch-shim.sh"
chmod 0555 "$SANDBOX/api/isolated-java-launch-shim.sh"
JAVA_LAUNCH_SHIM_SHA="$(sha256sum "$SANDBOX/api/isolated-java-launch-shim.sh" | awk '{print $1}')"

cat > "$EVIDENCE/source-old-artifact.txt" <<EOF
SOURCE_PATH=$OLD_SOURCE
SOURCE_SHA256=$OLD_SOURCE_SHA_BEFORE
SOURCE_STAT=$(stat -Lc '%d:%i %s %a %U:%G %y' "$OLD_SOURCE")
CANDIDATE_SHA256=$CANDIDATE_SHA
OLD_AGENT_SCHEMA_SHA256=$(sha256sum "$OLD_AGENT_SCHEMA" | awk '{print $1}')
OLD_AGENT_SCHEMA_SOURCE=${OLD_AGENT_MAPPER_ENTRIES[0]}!/db/schema.sql
OLD_CHAT_SCHEMA_SHA256=$(sha256sum "$OLD_CHAT_SCHEMA" | awk '{print $1}')
OLD_CHAT_SCHEMA_SOURCE=${OLD_CHAT_MAPPER_ENTRIES[0]}!/${OLD_CHAT_SCHEMA_ENTRIES[0]}
ISOLATED_SCHEMA_TRANSITION_SHA256=$SCHEMA_TRANSITION_SHA
ISOLATED_SCHEMA_AGENT_SHA256=$SCHEMA_AGENT_SHA
ISOLATED_JAVA_LAUNCH_SHIM_SHA256=$JAVA_LAUNCH_SHIM_SHA
ARTIFACTS_DIFFER=YES
EOF

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
  trap - EXIT
  set +e
  local current_mnt pid pid_mnt api_pids=()
  current_mnt="$(readlink /proc/self/ns/mnt 2>/dev/null || true)"
  for proc in /proc/[0-9]*; do
    [[ -r "$proc/cmdline" ]] || continue
    pid="${proc##*/}"
    pid_mnt="$(readlink "$proc/ns/mnt" 2>/dev/null || true)"
    [[ -n "$current_mnt" && "$pid_mnt" == "$current_mnt" ]] || continue
    if tr '\0' ' ' < "$proc/cmdline" | grep -Fq '/home/isp/hosts/cyf/api/cyf-api-kit.jar'; then
      api_pids+=("$pid")
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  for pid in "${REDIS_PID:-}" "${MYSQL_SOURCE_PID:-}" "${MYSQL_RESTORE_PID:-}"; do
    [[ -z "$pid" ]] || kill -TERM "$pid" 2>/dev/null || true
  done
  for _ in {1..30}; do
    local alive=0
    for pid in "${api_pids[@]}" "${REDIS_PID:-}" "${MYSQL_SOURCE_PID:-}" "${MYSQL_RESTORE_PID:-}"; do
      [[ -z "$pid" || ! -e "/proc/$pid" ]] || alive=1
    done
    (( alive == 0 )) && break
    sleep 1
  done
  for pid in "${api_pids[@]}" "${REDIS_PID:-}" "${MYSQL_SOURCE_PID:-}" "${MYSQL_RESTORE_PID:-}"; do
    [[ -z "$pid" || ! -e "/proc/$pid" ]] || kill -KILL "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  return "$exit_code"
}
trap cleanup_inner EXIT

mount --make-rprivate /
ip link set lo up
[[ -z "$(ip route show)" ]] || { echo 'isolated network namespace unexpectedly has a route' >&2; exit 10; }
mount --bind "$CONTROL_RELEASE" "$CONTROL_RELEASE"
mount -o remount,bind,ro "$CONTROL_RELEASE"
mount --bind "$CONTROL_RELEASES" "$CONTROL_RELEASES"
mount -o remount,bind,ro "$CONTROL_RELEASES"
mount --bind "$CONTROL_API_REPO" "$ROOT/.worktrees/m2-api-base"
mount -o remount,bind,ro "$ROOT/.worktrees/m2-api-base"
mount --bind "$CONTROL_RELEASES" "$ROOT/deliverables/releases"
mount -o remount,bind,ro "$ROOT/deliverables/releases"
runuser -u isp -- git -C "$ROOT/.worktrees/m2-api-base" rev-parse --is-inside-work-tree | grep -Fxq true
[[ "$(runuser -u isp -- git -C "$ROOT/.worktrees/m2-api-base" rev-parse HEAD)" == e45ba398f116a210091c892abb9fbc8111dcc411 ]]
[[ "$(runuser -u isp -- git -C "$ROOT/.worktrees/m2-api-base" rev-parse 'HEAD^{tree}')" == 8b80bf35c418b2ca0cead919f805db5bb70166eb ]]
[[ -z "$(runuser -u isp -- git -C "$ROOT/.worktrees/m2-api-base" status --porcelain=v1 --untracked-files=all)" ]]
runuser -u isp -- test -x "$CONTROL_RELEASE/deploy-api.sh"
runuser -u isp -- test -x "$CONTROL_RELEASE/rollback-api.sh"
runuser -u isp -- test -r "$INPUT"
runuser -u isp -- test -r "$API_ARTIFACT"
printf '%s\n' 'ISOLATED_CONTROL_VIEW_ACCESS=PASS' > "$EVIDENCE/isolated-control-view.txt"
mount --bind "$SANDBOX/api" /home/isp/hosts/cyf/api
mount --bind "$SANDBOX/baks" /home/isp/baks
mount --bind /home/isp/hosts/cyf/api/isolated-schema-transition.sh \
  /home/isp/hosts/cyf/api/isolated-schema-transition.sh
mount -o remount,bind,ro /home/isp/hosts/cyf/api/isolated-schema-transition.sh
mount --bind /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar \
  /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar
mount -o remount,bind,ro /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar
mount --bind /home/isp/apps/jdk21 "$RUN/real-jdk"
mount -o remount,bind,ro "$RUN/real-jdk"
mount --bind /home/isp/hosts/cyf/api/isolated-java-launch-shim.sh /home/isp/apps/jdk21/bin/java
mount -o remount,bind,ro /home/isp/apps/jdk21/bin/java
[[ "$(sha256sum /home/isp/hosts/cyf/api/isolated-schema-transition.sh | awk '{print $1}')" \
   == "$SCHEMA_TRANSITION_SHA" ]] || exit 10
[[ "$(sha256sum /home/isp/apps/jdk21/bin/java | awk '{print $1}')" \
   == "$JAVA_LAUNCH_SHIM_SHA" ]] || exit 10
[[ -f /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar \
   && ! -L /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar \
   && "$(stat -c %a -- /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar)" == 444 \
   && "$(sha256sum /home/isp/hosts/cyf/api/isolated-schema-transition-agent.jar | awk '{print $1}')" \
      == "$SCHEMA_AGENT_SHA" ]] || exit 10
[[ -x "$RUN/real-jdk/bin/java" && "$(sha256sum "$RUN/real-jdk/bin/java" | awk '{print $1}')" \
   != "$JAVA_LAUNCH_SHIM_SHA" ]] || exit 10
touch "$RUN/api-execution.lock"
chown isp:isp "$RUN/api-execution.lock"
mount --bind "$RUN/api-execution.lock" /tmp/cyf-release-api.lock
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
export NO_PROXY='127.0.0.1,localhost'
export no_proxy="$NO_PROXY"

MYSQL=/home/isp/apps/mysql/bin/mysqld
MYSQL_CLI=/home/isp/apps/mysql/bin/mysql
MYSQL_ADMIN=/home/isp/apps/mysql/bin/mysqladmin
MYSQL_DUMP=/home/isp/apps/mysql/bin/mysqldump
REDIS=/home/isp/apps/redis/bin/redis-server
REDIS_CLI=/home/isp/apps/redis/bin/redis-cli
JAVA=/home/isp/apps/jdk21/bin/java
for path in "$MYSQL" "$MYSQL_CLI" "$MYSQL_ADMIN" "$MYSQL_DUMP" "$REDIS" "$REDIS_CLI" "$JAVA"; do
  [[ -x "$path" ]] || { echo "missing executable: $path" >&2; exit 11; }
done

ip route show > "$EVIDENCE/network-routes.txt"
readlink /proc/self/ns/mnt > "$EVIDENCE/mount-namespace.txt"
readlink /proc/self/ns/net > "$EVIDENCE/network-namespace.txt"
readlink /proc/self/ns/pid > "$EVIDENCE/pid-namespace.txt"
grep -F ' /home/isp/hosts/cyf/api ' /proc/self/mountinfo > "$EVIDENCE/api-bind-mount.txt"
grep -F ' /home/isp/apps/jdk21/bin/java ' /proc/self/mountinfo > "$EVIDENCE/java-shim-bind-mount.txt"
grep -F " $RUN/real-jdk " /proc/self/mountinfo > "$EVIDENCE/real-jdk-bind-mount.txt"
ss -lntp > "$EVIDENCE/listeners-before.txt"
ps -eo pid=,ppid=,uid=,stat=,comm= > "$EVIDENCE/processes-before.txt"
health_response_matches() {
  grep -Eq -- "$HEALTH_EXPECTED_REGEX" "$1"
}

start_mysql() {
  local datadir="$1" socket="$2" port="$3" log="$4" variable="$5" pid
  "$MYSQL" --initialize-insecure --user=isp --datadir="$datadir" \
    --lower-case-table-names=1 --log-error="$log.init"
  "$MYSQL" --no-defaults --user=isp --datadir="$datadir" --socket="$socket" \
    --pid-file="$datadir/mysql.pid" --port="$port" --bind-address=127.0.0.1 \
    --skip-name-resolve --mysqlx=0 --lower-case-table-names=1 \
    --performance-schema=OFF --innodb-buffer-pool-size=64M --key-buffer-size=8M \
    --max-connections=20 --log-bin-trust-function-creators=1 --log-error="$log" &
  pid=$!
  printf -v "$variable" '%s' "$pid"
  export "$variable"
  for _ in {1..90}; do
    "$MYSQL_ADMIN" --protocol=socket --socket="$socket" ping >/dev/null 2>&1 && break
    kill -0 "$pid" 2>/dev/null || { cat "$log" >&2; exit 12; }
    sleep 1
  done
  "$MYSQL_ADMIN" --protocol=socket --socket="$socket" ping >/dev/null 2>&1 || exit 12
}

SOURCE_SOCKET="$RUN/mysql-source/mysql.sock"
RESTORE_SOCKET="$RUN/mysql-restore/mysql.sock"
export CYF_C08_ISOLATED_SCHEMA_TRANSITION=/home/isp/hosts/cyf/api/isolated-schema-transition.sh
export CYF_C08_ISOLATED_SCHEMA_TRANSITION_SHA256="$SCHEMA_TRANSITION_SHA"
export CYF_C08_ISOLATED_SCHEMA_AGENT_SHA256="$SCHEMA_AGENT_SHA"
export CYF_C08_ISOLATED_SCHEMA_SOCKET="$SOURCE_SOCKET"
export CYF_C08_ISOLATED_SCHEMA_EVIDENCE="$EVIDENCE/schema-transitions"
export CYF_C08_OLD_API_SHA256="$OLD_API_SHA"
export CYF_C08_CANDIDATE_API_SHA256="$CANDIDATE_SHA"
export CYF_C08_REAL_JAVA="$RUN/real-jdk/bin/java"
export CYF_C08_JAVA_LAUNCH_STATE="$RUN/java-launch-state"
export CYF_C08_SCHEMA_LAUNCH_EVIDENCE="$EVIDENCE/schema-launches"
start_mysql "$RUN/mysql-source" "$SOURCE_SOCKET" 33317 "$RUN/logs/mysql-source.log" MYSQL_SOURCE_PID
start_mysql "$RUN/mysql-restore" "$RESTORE_SOCKET" 33318 "$RUN/logs/mysql-restore.log" MYSQL_RESTORE_PID
for socket in "$SOURCE_SOCKET" "$RESTORE_SOCKET"; do
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B \
    -e 'SELECT CONCAT("lower_case_table_names=", @@lower_case_table_names)' \
    >> "$EVIDENCE/mysql-lower-case-table-names.txt"
done
[[ "$(grep -Fxc 'lower_case_table_names=1' "$EVIDENCE/mysql-lower-case-table-names.txt")" == 2 ]] || exit 12

"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -e \
  "CREATE DATABASE c08 CHARACTER SET utf8mb4 COLLATE utf8mb4_bin; CREATE USER 'c08'@'127.0.0.1' IDENTIFIED BY 'c08-pass'; GRANT ALL ON c08.* TO 'c08'@'127.0.0.1'; FLUSH PRIVILEGES;"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 < "$API_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 < "$CHAT_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 < "$OLD_AGENT_SCHEMA"
cat > "$RUN/fixture-columns-old-expected.tsv" <<'EOF'
agent_task_backfill_issue	tenant_id	YES	VALUE:0	varchar(50)	utf8mb4_0900_bin
agent_task_backfill_manifest	tenant_id	YES	VALUE:0	varchar(50)	utf8mb4_0900_bin
agent_task_thread	tenant_id	NO	VALUE:0	varchar(50)	utf8mb4_0900_bin
EOF
cat > "$RUN/fixture-columns-candidate-expected.tsv" <<'EOF'
agent_task_backfill_issue	tenant_id	YES	<SQL_NULL>	varchar(50)	utf8mb4_0900_bin
agent_task_backfill_manifest	tenant_id	YES	<SQL_NULL>	varchar(50)	utf8mb4_0900_bin
agent_task_thread	tenant_id	NO	<SQL_NULL>	varchar(50)	utf8mb4_0900_bin
EOF
fixture_columns_for_schema() {
  local socket="$1" schema="$2" output="$3"
  [[ "$schema" == c08 || "$schema" == c08_candidate_contract ]] || return 1
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT table_name,column_name,is_nullable,IF(column_default IS NULL,'<SQL_NULL>',CONCAT('VALUE:',column_default)),column_type,collation_name FROM information_schema.columns WHERE table_schema='$schema' AND ((table_name='agent_task_thread' AND column_name='tenant_id') OR (table_name='agent_task_backfill_issue' AND column_name='tenant_id') OR (table_name='agent_task_backfill_manifest' AND column_name='tenant_id')) ORDER BY table_name" \
    > "$output"
}
fixture_columns() {
  fixture_columns_for_schema "$1" c08 "$2"
}

# Derive the candidate metadata contract from the exact pinned candidate SQL,
# in a separate empty schema. The runtime transition's fixed expected metadata
# must match this source-derived contract before any deploy/rollback exercise.
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -e \
  "CREATE DATABASE c08_candidate_contract CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08_candidate_contract < "$API_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08_candidate_contract < "$CHAT_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08_candidate_contract < "$AGENT_SCHEMA"
fixture_columns_for_schema "$SOURCE_SOCKET" c08_candidate_contract \
  "$EVIDENCE/fixture-columns-candidate-from-pinned-source.tsv"
cmp "$RUN/fixture-columns-candidate-expected.tsv" \
  "$EVIDENCE/fixture-columns-candidate-from-pinned-source.tsv" \
  || { echo 'candidate runtime schema contract differs from pinned candidate SQL' >&2; exit 12; }
{
  printf '%s\n' 'scope=ISOLATED_PINNED_CANDIDATE_SCHEMA_CONTRACT'
  printf 'api_schema_sha256=%s\n' "$(sha256sum "$API_SCHEMA" | awk '{print $1}')"
  printf 'chat_schema_sha256=%s\n' "$(sha256sum "$CHAT_SCHEMA" | awk '{print $1}')"
  printf 'agent_schema_sha256=%s\n' "$(sha256sum "$AGENT_SCHEMA" | awk '{print $1}')"
  printf 'candidate_metadata_sha256=%s\n' \
    "$(sha256sum "$EVIDENCE/fixture-columns-candidate-from-pinned-source.tsv" | awk '{print $1}')"
  printf '%s\n' 'PINNED_CANDIDATE_SCHEMA_CONTRACT=PASS'
  printf '%s\n' 'production_database_operation=NOT_PERFORMED'
} > "$EVIDENCE/pinned-candidate-schema-contract.txt"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -e \
  "DROP DATABASE c08_candidate_contract;"

# The production artifact carries the old task-thread DDL separately from the
# agent mapper schema. Its embedded DDL omits the default, while the old
# ChatSchemaInitializer runtime validator requires DEFAULT '0'. Validate the
# embedded DDL exactly here, then apply the isolated fixture-only runtime
# normalization before invoking the old artifact transition helper.
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -e \
  "CREATE DATABASE c08_old_thread_contract CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08_old_thread_contract < "$OLD_CHAT_SCHEMA"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -N -B -e \
  "SELECT table_name,column_name,is_nullable,IF(column_default IS NULL,'<SQL_NULL>',CONCAT('VALUE:',column_default)),column_type,collation_name FROM information_schema.columns WHERE table_schema='c08_old_thread_contract' AND table_name='agent_task_thread' AND column_name='tenant_id'" \
  > "$EVIDENCE/fixture-column-old-thread-from-production-artifact.tsv"
grep -Fxq $'agent_task_thread\ttenant_id\tNO\t<SQL_NULL>\tvarchar(50)\tutf8mb4_0900_bin' \
  "$EVIDENCE/fixture-column-old-thread-from-production-artifact.tsv" || exit 12
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot -e \
  "DROP DATABASE c08_old_thread_contract;"

# The candidate chat schema creates thread.tenant_id with an SQL-NULL default,
# whereas the old artifact's runtime validator requires DEFAULT '0'. Normalize
# only this isolated fixture before the first old transition. Production DB and
# RabbitMQ are outside the namespace and are never touched by this drill.
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 -e \
  "SET SESSION lock_wait_timeout=5; ALTER TABLE agent_task_thread ALTER COLUMN tenant_id SET DEFAULT '0';"
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-old-runtime-normalized.tsv"
cmp "$RUN/fixture-columns-old-expected.tsv" "$EVIDENCE/fixture-columns-old-runtime-normalized.tsv"
cat > "$EVIDENCE/old-thread-runtime-contract-normalization.txt" <<EOF
scope=ISOLATED_FIXTURE_ONLY
old_embedded_thread_ddl_default=SQL_NULL
old_runtime_validator_expected_thread_tenant_default=VALUE:0
candidate_runtime_contract_thread_tenant_default=SQL_NULL
normalization=ALTER isolated c08.agent_task_thread.tenant_id SET DEFAULT '0'
production_database_operation=NOT_PERFORMED
production_rabbitmq_operation=NOT_PERFORMED
EOF

# Establish the exact old-artifact runtime contract first, attack mixed/unknown
# defaults, then bind the candidate JAR before creating the candidate snapshot.
runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" old
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-old-initial.tsv"
cmp "$RUN/fixture-columns-old-expected.tsv" "$EVIDENCE/fixture-columns-old-initial.tsv"

# A mixed state without an interrupted-transition marker must fail closed.
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 -e \
  "SET SESSION lock_wait_timeout=5; ALTER TABLE agent_task_backfill_issue ALTER COLUMN tenant_id DROP DEFAULT;"
if runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" old \
  > "$EVIDENCE/schema-mixed-without-marker-negative.log" 2>&1; then
  echo 'mixed schema without marker unexpectedly converged' >&2
  exit 12
fi
grep -Fq 'mixed schema state has no valid interrupted-transition marker' \
  "$EVIDENCE/schema-mixed-without-marker-negative.log" || exit 12
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 -e \
  "SET SESSION lock_wait_timeout=5; ALTER TABLE agent_task_backfill_issue ALTER COLUMN tenant_id SET DEFAULT '0';"
runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" old

cp --reflink=auto -- "$API_ARTIFACT" /home/isp/hosts/cyf/api/cyf-api-kit.jar
chmod 0644 /home/isp/hosts/cyf/api/cyf-api-kit.jar
[[ "$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')" == "$CANDIDATE_SHA" ]] || exit 12

# Simulate an interrupted multi-DDL transition. The first call leaves a
# marker-backed known mixed state; the second call is the only path allowed to
# converge that mixed state.
set +e
CYF_C08_SCHEMA_TEST_INTERRUPT_AFTER=1 runuser -u isp --preserve-environment -- \
  "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" candidate \
  > "$EVIDENCE/schema-interrupted-transition.log" 2>&1
interrupt_status=$?
set -e
[[ "$interrupt_status" == 97 && -f "$RUN/schema-transition-state/ddl-in-progress" ]] || exit 12
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-known-mixed.tsv"
if cmp -s "$RUN/fixture-columns-old-expected.tsv" "$EVIDENCE/fixture-columns-known-mixed.tsv" \
   || cmp -s "$RUN/fixture-columns-candidate-expected.tsv" "$EVIDENCE/fixture-columns-known-mixed.tsv"; then
  echo 'intentional interrupted transition did not create a mixed state' >&2
  exit 12
fi
runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" candidate
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-mixed-rescued.tsv"
cmp "$RUN/fixture-columns-candidate-expected.tsv" "$EVIDENCE/fixture-columns-mixed-rescued.tsv"
[[ ! -e "$RUN/schema-transition-state/ddl-in-progress" ]] || exit 12

# Any third default state remains fail-closed even when all non-default column
# metadata is still exact.
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 -e \
  "SET SESSION lock_wait_timeout=5; ALTER TABLE agent_task_backfill_manifest ALTER COLUMN tenant_id SET DEFAULT 'invalid-third-state';"
if runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" candidate \
  > "$EVIDENCE/schema-third-state-negative.log" 2>&1; then
  echo 'unknown third schema state unexpectedly converged' >&2
  exit 12
fi
grep -Fq 'unknown third state' "$EVIDENCE/schema-third-state-negative.log" || exit 12
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 -e \
  "SET SESSION lock_wait_timeout=5; ALTER TABLE agent_task_backfill_manifest ALTER COLUMN tenant_id DROP DEFAULT;"
runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" candidate

cat > "$EVIDENCE/fixture-compatibility-normalization.txt" <<'EOF'
scope=ISOLATED_FIXTURE_ONLY
production_database_operation=NOT_PERFORMED
production_rabbitmq_operation=NOT_PERFORMED
reason=old-and-candidate-exact-validators-require-mutually-exclusive-column-defaults
old_embedded_thread_ddl=agent_task_thread NOT NULL with SQL NULL default
old_runtime_contract=agent_task_thread NOT NULL DEFAULT '0'; B09 issue/manifest NULL DEFAULT '0'
candidate_runtime_contract=agent_task_thread NOT NULL with SQL NULL default; B09 issue/manifest NULL DEFAULT NULL
offline_sequence=old -> mixed-no-marker reject -> interrupted candidate mixed rescue -> candidate -> dump/restore candidate -> old
runtime_transition_boundary=byte-exact release scripts invoke saved Java argv; isolated Java executable shim selects schema from live JAR SHA before real Java exec
runtime_deploy_failure_sequence=candidate health fault -> stop candidate -> automatic old restore through shim
runtime_rollback_failure_sequence=old health fault -> stop old -> candidate rescue through shim
migration_risk_disposition=fixture-only; no production migration claim; production schema requires a separately approved migration audit
EOF
NOW_MS="$(python3 - <<'PY'
import time
print(int(time.time()*1000))
PY
)"
"$MYSQL_CLI" --protocol=socket --socket="$SOURCE_SOCKET" -uroot c08 <<SQL
INSERT INTO agent_task_meta
(id,task_id,reward_status,collaboration_mode,risk_level,max_agents,review_required,
 task_version,current_event_version,tenant_id,client_id,create_time,update_time)
VALUES (9901,'c08-backup-marker','open','solo','low',1,0,0,0,
        'c08-isolated','client-isolated',$NOW_MS,$NOW_MS);
SQL
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-candidate-prebackup.tsv"
cmp "$RUN/fixture-columns-candidate-expected.tsv" "$EVIDENCE/fixture-columns-candidate-prebackup.tsv"

DB_DUMP=/home/isp/hosts/cyf/api/backups/db/c08-isolated.sql
"$MYSQL_DUMP" --protocol=socket --socket="$SOURCE_SOCKET" -uroot \
  --set-gtid-purged=OFF --single-transaction --routines --triggers --events \
  --hex-blob --databases c08 > "$DB_DUMP"
[[ -s "$DB_DUMP" ]] || { echo 'isolated database dump is empty' >&2; exit 13; }
chmod 0444 "$DB_DUMP"
(
  cd "$(dirname "$DB_DUMP")"
  sha256sum "$(basename "$DB_DUMP")" > "$(basename "$DB_DUMP").sha256"
  chmod 0444 "$(basename "$DB_DUMP").sha256"
  sha256sum -c "$(basename "$DB_DUMP").sha256" > "$EVIDENCE/database-dump-check.txt"
)
cp "$DB_DUMP" "$EVIDENCE/c08-isolated.sql"
cp "${DB_DUMP}.sha256" "$EVIDENCE/c08-isolated.sql.sha256"
chmod 0444 "$EVIDENCE/c08-isolated.sql" "$EVIDENCE/c08-isolated.sql.sha256"
"$MYSQL_CLI" --protocol=socket --socket="$RESTORE_SOCKET" -uroot < "$DB_DUMP"
"$MYSQL_CLI" --protocol=socket --socket="$RESTORE_SOCKET" -uroot -e \
  "CREATE USER 'c08'@'127.0.0.1' IDENTIFIED BY 'c08-pass'; GRANT ALL ON c08.* TO 'c08'@'127.0.0.1'; FLUSH PRIVILEGES;"

for entry in "source:$SOURCE_SOCKET" "restore:$RESTORE_SOCKET"; do
  name="${entry%%:*}"; socket="${entry#*:}"
  "$MYSQL_DUMP" --protocol=socket --socket="$socket" -uroot \
    --set-gtid-purged=OFF --no-data --skip-comments --routines --triggers --events \
    --databases c08 > "$EVIDENCE/database-schema-$name.sql"
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT CONCAT('SELECT ', QUOTE(table_name), ', COUNT(*) FROM ', CHAR(96), REPLACE(table_name, CHAR(96), CONCAT(CHAR(96), CHAR(96))), CHAR(96), ';') FROM information_schema.tables WHERE table_schema='c08' AND table_type='BASE TABLE' ORDER BY table_name" \
    > "$RUN/count-$name.sql"
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B c08 \
    < "$RUN/count-$name.sql" > "$EVIDENCE/database-row-counts-$name.tsv"
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT CONCAT('CHECK TABLE ', CHAR(96), REPLACE(table_name, CHAR(96), CONCAT(CHAR(96), CHAR(96))), CHAR(96), ';') FROM information_schema.tables WHERE table_schema='c08' AND table_type='BASE TABLE' ORDER BY table_name" \
    > "$RUN/check-$name.sql"
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B c08 \
    < "$RUN/check-$name.sql" > "$EVIDENCE/database-check-table-$name.tsv"
  if grep -Fv $'\tstatus\tOK' "$EVIDENCE/database-check-table-$name.tsv" | grep -q .; then
    echo "CHECK TABLE failed for $name" >&2; exit 14
  fi
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT user,host,plugin,account_locked,password_expired FROM mysql.user WHERE user='c08' AND host='127.0.0.1'; SHOW GRANTS FOR 'c08'@'127.0.0.1';" \
    > "$EVIDENCE/database-account-$name.tsv"
  "$MYSQL_CLI" --protocol=socket --socket="$socket" -uroot -N -B -e \
    "SELECT table_name,column_name,is_nullable,IF(column_default IS NULL,'<SQL_NULL>',CONCAT('VALUE:',column_default)),column_type,collation_name FROM information_schema.columns WHERE table_schema='c08' AND ((table_name='agent_task_thread' AND column_name='tenant_id') OR (table_name='agent_task_backfill_issue' AND column_name='tenant_id') OR (table_name='agent_task_backfill_manifest' AND column_name='tenant_id')) ORDER BY table_name" \
    > "$EVIDENCE/fixture-compatibility-columns-$name.tsv"
  cmp "$RUN/fixture-columns-candidate-expected.tsv" \
    "$EVIDENCE/fixture-compatibility-columns-$name.tsv" || exit 14
done
python3 - "$EVIDENCE" <<'PY'
import hashlib, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
# MySQL 8.0.21 can make an implied column character set explicit after a
# dump/restore round trip (for example, COLLATE utf8mb4_bin becomes
# CHARACTER SET utf8mb4 COLLATE utf8mb4_bin). It also serializes an omitted
# default on the two nullable B09 tenant_id columns as explicit DEFAULT NULL.
# Normalize only these exact semantic equivalences; all other DDL bytes remain
# fail-closed, and the metadata query above must already match exactly.
pattern = re.compile(r' CHARACTER SET ([A-Za-z0-9_]+) COLLATE \1_')
records = []
for name in ('source', 'restore'):
    raw_path = root / ('database-schema-' + name + '.sql')
    canonical_path = root / ('database-schema-' + name + '-canonical.sql')
    raw = raw_path.read_text()
    canonical = pattern.sub(r' COLLATE \1_', raw)
    current_table = None
    normalized_lines = []
    default_null_removals = 0
    for line in canonical.splitlines(True):
        match = re.match(r'^CREATE TABLE `([^`]+)` \($', line.rstrip('\n'))
        if match:
            current_table = match.group(1)
        if current_table in {'agent_task_backfill_issue', 'agent_task_backfill_manifest'} \
                and line.startswith('  `tenant_id` varchar(50) COLLATE utf8mb4_0900_bin DEFAULT NULL COMMENT '):
            line = line.replace(' DEFAULT NULL COMMENT ', ' COMMENT ', 1)
            default_null_removals += 1
        normalized_lines.append(line)
        if line.startswith(') ENGINE='):
            current_table = None
    expected_removals = 0 if name == 'source' else 2
    if default_null_removals != expected_removals:
        raise SystemExit('%s B09 DEFAULT NULL normalization count mismatch: %s' %
                         (name, default_null_removals))
    canonical = ''.join(normalized_lines)
    canonical_path.write_text(canonical)
    records.append('%s_raw_sha256=%s' % (name, hashlib.sha256(raw.encode()).hexdigest()))
    records.append('%s_canonical_sha256=%s' % (name, hashlib.sha256(canonical.encode()).hexdigest()))
    records.append('%s_b09_default_null_removals=%s' % (name, default_null_removals))
(root / 'database-schema-normalization.txt').write_text('\n'.join(records) + '\n')
PY
cmp -s "$EVIDENCE/database-schema-source-canonical.sql" "$EVIDENCE/database-schema-restore-canonical.sql" \
  || { diff -u "$EVIDENCE/database-schema-source-canonical.sql" "$EVIDENCE/database-schema-restore-canonical.sql" >&2 || true; exit 15; }
cmp -s "$EVIDENCE/database-row-counts-source.tsv" "$EVIDENCE/database-row-counts-restore.tsv" \
  || { diff -u "$EVIDENCE/database-row-counts-source.tsv" "$EVIDENCE/database-row-counts-restore.tsv" >&2 || true; exit 15; }
cmp -s "$EVIDENCE/database-account-source.tsv" "$EVIDENCE/database-account-restore.tsv" \
  || { diff -u "$EVIDENCE/database-account-source.tsv" "$EVIDENCE/database-account-restore.tsv" >&2 || true; exit 15; }
"$MYSQL_CLI" --protocol=socket --socket="$RESTORE_SOCKET" -uroot -N -B c08 -e \
  "SELECT CONCAT(task_id,'|',tenant_id,'|',client_id) FROM agent_task_meta WHERE id=9901" \
  > "$EVIDENCE/database-restored-marker.txt"
grep -Fxq 'c08-backup-marker|c08-isolated|client-isolated' "$EVIDENCE/database-restored-marker.txt" || exit 15
cp --reflink=auto -- "$RUN/old-api-artifact.jar" /home/isp/hosts/cyf/api/cyf-api-kit.jar
chmod 0644 /home/isp/hosts/cyf/api/cyf-api-kit.jar
[[ "$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')" == "$OLD_API_SHA" ]] || exit 15
python3 - "$RUN/old-api-artifact.jar" "$OLD_API_SHA" "$EVIDENCE/old-api-artifact-prune-before-api.txt" <<'PYOLDARTIFACTPRUNE'
import hashlib, os, pathlib, stat, sys
path = pathlib.Path(sys.argv[1])
expected_sha = sys.argv[2]
evidence = pathlib.Path(sys.argv[3])
run = path.parent
if not str(run).startswith('/tmp/cyf-c08-api-rollback.') or path.name != 'old-api-artifact.jar':
    raise SystemExit('refusing unsafe isolated old artifact cleanup path')
st = path.lstat()
if path.is_symlink() or not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
    raise SystemExit('isolated old artifact is not a single-link physical file')
digest_state = hashlib.sha256()
with path.open('rb') as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest_state.update(chunk)
digest = digest_state.hexdigest()
if digest != expected_sha:
    raise SystemExit('isolated old artifact SHA mismatch before cleanup')
for proc in pathlib.Path('/proc').glob('[0-9]*'):
    for name in ('cwd', 'root'):
        try:
            target = os.readlink(proc / name)
        except OSError:
            continue
        if target == str(path) or target.startswith(str(path) + '/'):
            raise SystemExit('isolated old artifact path still referenced by process')
    fd_dir = proc / 'fd'
    try:
        fds = list(fd_dir.iterdir())
    except OSError:
        continue
    for fd in fds:
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if target == str(path):
            raise SystemExit('isolated old artifact file still referenced by process')
allocated = st.st_blocks * 512
path.unlink()
if path.exists() or path.is_symlink():
    raise SystemExit('isolated old artifact cleanup failed')
evidence.write_text(
    'scope=ISOLATED_RUN_ONLY\n'
    'artifact=%s\n'
    'artifact_sha256=%s\n'
    'process_cwd_root_fd_refs=NONE\n'
    'allocated_bytes_reclaimed=%d\n'
    'production_deployment=NOT_PERFORMED\n'
    'production_database_operation=NOT_PERFORMED\n'
    'production_rabbitmq_operation=NOT_PERFORMED\n'
    'old_artifact_copy_pruned_before_api=PASS\n' % (path, digest, allocated)
)
PYOLDARTIFACTPRUNE
runuser -u isp --preserve-environment -- "$CYF_C08_ISOLATED_SCHEMA_TRANSITION" old
fixture_columns "$SOURCE_SOCKET" "$EVIDENCE/fixture-columns-old-before-runtime.tsv"
cmp "$RUN/fixture-columns-old-expected.tsv" "$EVIDENCE/fixture-columns-old-before-runtime.tsv" || exit 15

# Restore verification is complete. Stop the second MySQL before starting
# Redis/Java so the high-memory phases never overlap.
"$MYSQL_ADMIN" --protocol=socket --socket="$RESTORE_SOCKET" shutdown >/dev/null 2>&1 || true
for _ in {1..30}; do
  [[ ! -e "/proc/$MYSQL_RESTORE_PID" ]] && break
  sleep 1
done
[[ ! -e "/proc/$MYSQL_RESTORE_PID" ]] || { echo 'restore MySQL did not stop before API phase' >&2; exit 15; }
wait "$MYSQL_RESTORE_PID" 2>/dev/null || true
MYSQL_RESTORE_PID=""
python3 - "$RUN/mysql-restore" "$EVIDENCE/resource-phase-boundary.txt" <<'PYRESTOREPRUNE'
import os, pathlib, shutil, sys
path = pathlib.Path(sys.argv[1])
evidence = pathlib.Path(sys.argv[2])
if not str(path).startswith('/tmp/cyf-c08-api-rollback.') or path.name != 'mysql-restore' or path.is_symlink():
    raise SystemExit('refusing unsafe restore MySQL cleanup path')
for proc in pathlib.Path('/proc').glob('[0-9]*'):
    for name in ('cwd', 'root'):
        try:
            target = os.readlink(proc / name)
        except OSError:
            continue
        if target == str(path) or target.startswith(str(path) + '/'):
            raise SystemExit('restore MySQL path still referenced by process')
    fd_dir = proc / 'fd'
    try:
        fds = list(fd_dir.iterdir())
    except OSError:
        continue
    for fd in fds:
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if target == str(path) or target.startswith(str(path) + '/'):
            raise SystemExit('restore MySQL file still referenced by process')
allocated = sum(item.stat().st_blocks * 512 for item in path.rglob('*') if not item.is_symlink())
shutil.rmtree(path)
with evidence.open('w') as stream:
    stream.write('RESTORE_MYSQL_STOPPED_BEFORE_API=PASS\n')
    stream.write('RESTORE_MYSQL_DATADIR_REFERENCES=NONE\n')
    stream.write('RESTORE_MYSQL_DATADIR_PRUNED_BEFORE_API=PASS\n')
    stream.write('RESTORE_MYSQL_ALLOCATED_BYTES_RECLAIMED=%d\n' % allocated)
PYRESTOREPRUNE

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
  kill -0 "$REDIS_PID" 2>/dev/null || { cat "$RUN/logs/redis.log" >&2; exit 16; }
  sleep 1
done
redis_ping || exit 16

cat > /home/isp/hosts/cyf/api/isolated.properties <<EOF
spring.application.name=cyf-c08-api-rollback-isolated
server.address=127.0.0.1
server.port=10018
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
management.health.rabbit.enabled=false
management.health.ldap.enabled=false
camunda.bpm.enabled=false
jia.chat.service.websocket.enable=false
juyiting.scene-state.enabled=false
juyiting.scene-events.enabled=false
agent.task-events.enabled=false
oauth.resource.uris[0]=/agent/**
management.endpoints.web.exposure.include=health
management.endpoint.health.show-details=always
jia.file.path=$RUN/files
mat.web.realpath=$RUN/material
logging.level.root=INFO
logging.file.name=$RUN/logs/app.log
spring.task.scheduling.enabled=false
EOF
chmod 0600 /home/isp/hosts/cyf/api/isolated.properties
chown isp:isp /home/isp/hosts/cyf/api/isolated.properties

(
  cd /home/isp/hosts/cyf/api
  exec setpriv --reuid=isp --regid=isp --init-groups \
    "$JAVA" -Xms96m -Xmx384m -jar /home/isp/hosts/cyf/api/cyf-api-kit.jar \
    --spring.config.location=file:/home/isp/hosts/cyf/api/isolated.properties \
    > "$RUN/logs/old-api.stdout.log" 2>&1
) &
OLD_PID=$!
printf '%s\n' "$OLD_PID" > /home/isp/hosts/cyf/api/cyf-api-kit.pid
chown isp:isp /home/isp/hosts/cyf/api/cyf-api-kit.pid
chmod 0644 /home/isp/hosts/cyf/api/cyf-api-kit.pid
for _ in {1..180}; do
  if ! kill -0 "$OLD_PID" 2>/dev/null; then tail -240 "$RUN/logs/old-api.stdout.log" >&2; exit 17; fi
  grep -Fq 'Started JiaApplication' "$RUN/logs/old-api.stdout.log" && break
  sleep 1
done
for _ in {1..60}; do
  curl --fail --silent --show-error --max-time 5 http://127.0.0.1:10018/actuator/health \
    > "$EVIDENCE/api-old-health-before.json" 2>/dev/null && health_response_matches "$EVIDENCE/api-old-health-before.json" && break
  sleep 1
done
health_response_matches "$EVIDENCE/api-old-health-before.json" || { tail -300 "$RUN/logs/old-api.stdout.log" >&2; exit 17; }
printf 'OLD_PID=%s\nOLD_SHA256=%s\n' "$OLD_PID" "$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')" > "$EVIDENCE/api-old-runtime-before.txt"

if env -u CYF_RELEASE_APPROVED -u CYF_RELEASE_APPROVAL_ID \
  -u CYF_RELEASE_APPROVED_API_HEAD -u CYF_RELEASE_APPROVED_API_TREE \
  -u CYF_RELEASE_APPROVED_WEB_HEAD -u CYF_RELEASE_APPROVED_WEB_TREE \
  runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/deploy-api.sh" \
    --input "$INPUT" --execute > "$EVIDENCE/api-execute-without-approval.log" 2>&1; then
  echo 'API execute unexpectedly succeeded without external approval variables' >&2
  exit 18
fi
grep -Fq 'CYF_RELEASE_APPROVED=YES' "$EVIDENCE/api-execute-without-approval.log" || exit 18
[[ "$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')" == "$OLD_API_SHA" ]] || exit 18
cat > "$EVIDENCE/isolated-approval-scope.txt" <<EOF
APPROVAL_GATE_DEFAULT_DENY=PASS
APPROVAL_INJECTION=ISOLATED_SYNTHETIC_ONLY
PRODUCTION_APPROVAL=NOT_TESTED
EOF

export CYF_RELEASE_APPROVED=YES
export CYF_RELEASE_APPROVED_API_HEAD=e45ba398f116a210091c892abb9fbc8111dcc411
export CYF_RELEASE_APPROVED_API_TREE=8b80bf35c418b2ca0cead919f805db5bb70166eb
export CYF_RELEASE_APPROVED_WEB_HEAD=266583f2e59d5f1362ed4d653f58d02b78a0e6b5
export CYF_RELEASE_APPROVED_WEB_TREE=ba7ed4f167c43b3af8a7f07d34d626308496cd36
approval_stamp="$(date -u +%Y%m%dT%H%M%SZ)"

assert_live_state() {
  local expected_sha="$1" expected_schema="$2" health_output="$3" schema_output="$4"
  [[ "$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')" == "$expected_sha" ]] || return 1
  curl --fail --silent --show-error --max-time 5 http://127.0.0.1:10018/actuator/health > "$health_output"
  health_response_matches "$health_output" || return 1
  fixture_columns "$SOURCE_SOCKET" "$schema_output"
  cmp "$RUN/fixture-columns-${expected_schema}-expected.tsv" "$schema_output"
}
arm_health_fault() {
  local mode="$1"
  [[ "$mode" == candidate-health-once || "$mode" == old-health-once ]] || return 1
  [[ ! -e "$RUN/java-launch-state/fault-mode" && ! -L "$RUN/java-launch-state/fault-mode" ]] || return 1
  printf '%s\n' "$mode" > "$RUN/java-launch-state/fault-mode"
  chown isp:isp "$RUN/java-launch-state/fault-mode"
  chmod 0600 "$RUN/java-launch-state/fault-mode"
}
retain_release_record() {
  local record="$1" destination
  [[ -f "$record" && ! -L "$record" && -f "${record}.sha256" && ! -L "${record}.sha256" ]] || return 1
  mkdir -p "$RUN/retained-release-records"
  destination="$RUN/retained-release-records/$(basename -- "$record")"
  [[ ! -e "$destination" && ! -L "$destination" ]] || return 1
  cp -- "$record" "${record}.sha256" "$RUN/retained-release-records/"
  chmod 0444 "$destination" "${destination}.sha256"
  (
    cd "$RUN/retained-release-records"
    sha256sum -c "$(basename -- "$destination").sha256" >/dev/null
  )
  printf '%s\n' "$destination"
}
prune_isolated_backup_path() {
  local backup="$1" kind="$2" label="$3" source="$4" output
  output="$EVIDENCE/isolated-backup-prune-${label}.txt"
  python3 - "$backup" "$kind" "$source" "$output" <<'PYBACKUPPRUNE'
import os, pathlib, re, shutil, sys
backup = pathlib.Path(sys.argv[1])
kind = sys.argv[2]
source = sys.argv[3]
evidence = pathlib.Path(sys.argv[4])
root = pathlib.Path('/home/isp/baks/legacy-api/releases')
patterns = {
    'deploy': re.compile(r'^api-(?!rescue-)[0-9]{8}T[0-9]{6}Z-[0-9a-f]{40}-[0-9a-f]{40}-[A-Za-z0-9._-]+$'),
    'rescue': re.compile(r'^api-rescue-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{40}-[0-9a-f]{40}-[A-Za-z0-9._-]+$'),
}
pattern = patterns.get(kind)
if pattern is None:
    raise SystemExit('unknown isolated backup cleanup kind')
if backup.parent != root or not pattern.fullmatch(backup.name) \
        or backup.is_symlink() or not backup.is_dir():
    raise SystemExit('refusing unsafe isolated %s backup cleanup path' % kind)
if pathlib.Path(os.path.realpath(backup.parent)) != root:
    raise SystemExit('isolated backup root physical path mismatch')
for proc in pathlib.Path('/proc').glob('[0-9]*'):
    for name in ('cwd', 'root'):
        try:
            target = os.readlink(proc / name)
        except OSError:
            continue
        if target == str(backup) or target.startswith(str(backup) + '/'):
            raise SystemExit('isolated backup still referenced by process')
    fd_dir = proc / 'fd'
    try:
        fds = list(fd_dir.iterdir())
    except OSError:
        continue
    for fd in fds:
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if target == str(backup) or target.startswith(str(backup) + '/'):
            raise SystemExit('isolated backup file still referenced by process')
allocated = backup.stat().st_blocks * 512
allocated += sum(item.stat().st_blocks * 512 for item in backup.rglob('*') if not item.is_symlink())
shutil.rmtree(backup)
if backup.exists() or backup.is_symlink():
    raise SystemExit('isolated backup cleanup failed')
evidence.write_text(
    'scope=ISOLATED_SANDBOX_ONLY\n'
    'source=%s\n'
    'backup=%s\n'
    'backup_kind=%s\n'
    'process_cwd_root_fd_refs=NONE\n'
    'allocated_bytes_reclaimed=%d\n'
    'production_deployment=NOT_PERFORMED\n'
    'production_database_operation=NOT_PERFORMED\n'
    'production_rabbitmq_operation=NOT_PERFORMED\n'
    'backup_pruned=PASS\n' % (source, backup, kind, allocated)
)
PYBACKUPPRUNE
}
prune_isolated_backup_from_record() {
  local record="$1" field="$2" kind="$3" label="$4" backup
  backup="$(python3 - "$record" "$field" <<'PYBACKUPFIELD'
import json, pathlib, sys
record = pathlib.Path(sys.argv[1])
field = sys.argv[2]
value = json.loads(record.read_text()).get(field)
if not isinstance(value, str) or not value:
    raise SystemExit('isolated release record backup field is missing')
print(value)
PYBACKUPFIELD
)"
  prune_isolated_backup_path "$backup" "$kind" "$label" "$record:$field"
}
find_isolated_rescue_backup() {
  local change_id="$1"
  python3 - /home/isp/baks/legacy-api/releases "$change_id" <<'PYFINDRESCUE'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
change_id = sys.argv[2]
if not re.fullmatch(r'[A-Za-z0-9._-]+', change_id):
    raise SystemExit('unsafe isolated rescue change ID')
matches = [path for path in root.iterdir()
           if path.name.startswith('api-rescue-') and path.name.endswith('-' + change_id)]
if len(matches) != 1:
    raise SystemExit('expected exactly one isolated rescue backup; found=%d' % len(matches))
print(matches[0])
PYFINDRESCUE
}
retain_failed_deploy_record_and_prune() {
  local change_id="$1" record retained
  record="$(python3 - /home/isp/baks/legacy-api/release-records "$change_id" <<'PYFAILEDRECORD'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1]); change_id = sys.argv[2]
matches = []
for path in root.glob('api-deploy-*.json'):
    try:
        value = json.loads(path.read_text())
    except Exception:
        continue
    if value.get('changeId') == change_id and value.get('status') == 'PREPARED':
        matches.append(path)
if len(matches) != 1:
    raise SystemExit('expected exactly one failed deploy PREPARED record; found=%d' % len(matches))
print(matches[0])
PYFAILEDRECORD
)"
  mkdir -p "$EVIDENCE/failed-release-records"
  retained="$EVIDENCE/failed-release-records/$(basename -- "$record")"
  cp -- "$record" "$retained"
  chmod 0444 "$retained"
  (
    cd "$EVIDENCE/failed-release-records"
    sha256sum "$(basename -- "$retained")" > "$(basename -- "$retained").sha256"
    chmod 0444 "$(basename -- "$retained").sha256"
  )
  prune_isolated_backup_from_record "$record" backupDir deploy failed-deploy-auto-restore
}

# 1. Normal deploy and explicit rollback through the frozen release scripts.
export CYF_RELEASE_APPROVAL_ID="c08-normal-$approval_stamp"
runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/deploy-api.sh" --input "$INPUT" --dry-run > "$EVIDENCE/api-deploy-dry-run.log" 2>&1
runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/deploy-api.sh" --input "$INPUT" --execute > "$EVIDENCE/api-deploy.log" 2>&1
NORMAL_DEPLOY_RECORD="$(sed -n 's/^DEPLOY_RECORD=//p' "$EVIDENCE/api-deploy.log")"
[[ -n "$NORMAL_DEPLOY_RECORD" && -f "$NORMAL_DEPLOY_RECORD" ]] || { cat "$EVIDENCE/api-deploy.log" >&2; exit 18; }
CANDIDATE_PID="$(sed -n 's/^PID=//p' "$EVIDENCE/api-deploy.log")"
assert_live_state "$CANDIDATE_SHA" candidate "$EVIDENCE/api-candidate-health.json" \
  "$EVIDENCE/fixture-columns-candidate-after-deploy.tsv" || exit 18
python3 - "$NORMAL_DEPLOY_RECORD" "$CANDIDATE_SHA" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v['status']=='DEPLOYED_HEALTHY'
assert v['artifactSha256']==sys.argv[2]
assert v['databaseOperation']=='NOT_PERFORMED'
assert v['rabbitMqOperation']=='NOT_PERFORMED'
PY
printf 'CANDIDATE_PID=%s\nCANDIDATE_SHA256=%s\nDEPLOY_RECORD=%s\n' \
  "$CANDIDATE_PID" "$CANDIDATE_SHA" "$NORMAL_DEPLOY_RECORD" > "$EVIDENCE/api-candidate-runtime.txt"

runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/rollback-api.sh" --input "$INPUT" --dry-run "$NORMAL_DEPLOY_RECORD" > "$EVIDENCE/api-rollback-dry-run.log" 2>&1
runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/rollback-api.sh" --input "$INPUT" --execute "$NORMAL_DEPLOY_RECORD" > "$EVIDENCE/api-rollback.log" 2>&1
NORMAL_ROLLBACK_RECORD="$(sed -n 's/^ROLLBACK_RECORD=//p' "$EVIDENCE/api-rollback.log")"
RESTORED_PID="$(sed -n 's/^PID=//p' "$EVIDENCE/api-rollback.log")"
[[ -n "$NORMAL_ROLLBACK_RECORD" && -f "$NORMAL_ROLLBACK_RECORD" ]] || { cat "$EVIDENCE/api-rollback.log" >&2; exit 19; }
assert_live_state "$OLD_API_SHA" old "$EVIDENCE/api-old-health-after-rollback.json" \
  "$EVIDENCE/fixture-columns-old-after-rollback.tsv" || exit 19
python3 - "$NORMAL_ROLLBACK_RECORD" "$OLD_API_SHA" "$CANDIDATE_SHA" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v['status']=='ROLLED_BACK_HEALTHY'
assert v['restoredJarSha256']==sys.argv[2]
assert v['replacedJarSha256']==sys.argv[3]
assert v['databaseOperation']=='NOT_PERFORMED'
assert v['rabbitMqOperation']=='NOT_PERFORMED'
PY
printf 'RESTORED_PID=%s\nRESTORED_SHA256=%s\nROLLBACK_RECORD=%s\n' \
  "$RESTORED_PID" "$OLD_API_SHA" "$NORMAL_ROLLBACK_RECORD" > "$EVIDENCE/api-restored-runtime.txt"
ORIGINAL_NORMAL_DEPLOY_RECORD="$NORMAL_DEPLOY_RECORD"
ORIGINAL_NORMAL_ROLLBACK_RECORD="$NORMAL_ROLLBACK_RECORD"
NORMAL_DEPLOY_RECORD="$(retain_release_record "$ORIGINAL_NORMAL_DEPLOY_RECORD")"
NORMAL_ROLLBACK_RECORD="$(retain_release_record "$ORIGINAL_NORMAL_ROLLBACK_RECORD")"
prune_isolated_backup_from_record "$ORIGINAL_NORMAL_DEPLOY_RECORD" backupDir deploy normal-deploy-after-rollback
prune_isolated_backup_from_record "$ORIGINAL_NORMAL_ROLLBACK_RECORD" rescueBackupDir rescue normal-rollback-rescue-after-rollback

# 2. Candidate health fault: deploy must fail, then its unchanged EXIT trap must
# restore the old artifact/runtime; the second old launch is not faulted.
export CYF_RELEASE_APPROVAL_ID="c08-deploy-fault-$approval_stamp"
arm_health_fault candidate-health-once
if runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/deploy-api.sh" --input "$INPUT" --execute \
  > "$EVIDENCE/api-deploy-candidate-health-fault.log" 2>&1; then
  echo 'candidate health fault deploy unexpectedly succeeded' >&2
  exit 19
fi
[[ -f "$RUN/java-launch-state/fault-consumed-candidate-health-once" \
   && ! -e "$RUN/java-launch-state/fault-mode" ]] || exit 19
grep -Fq 'new API failed the configured health check' "$EVIDENCE/api-deploy-candidate-health-fault.log" || exit 19
grep -Fq 'automatic API restore health check PASS' "$EVIDENCE/api-deploy-candidate-health-fault.log" || exit 19
assert_live_state "$OLD_API_SHA" old "$EVIDENCE/api-old-health-after-deploy-fault.json" \
  "$EVIDENCE/fixture-columns-old-after-deploy-fault.tsv" || exit 19
if ss -H -lnt | awk '$4 ~ /:10019$/ { found=1 } END { exit !found }'; then
  echo 'fault-injected candidate listener leaked after automatic restore' >&2
  exit 19
fi
retain_failed_deploy_record_and_prune "$CYF_RELEASE_APPROVAL_ID"

# 3. Deploy candidate normally again, then inject an old health failure during
# rollback. The unchanged rollback EXIT trap must rescue the candidate.
export CYF_RELEASE_APPROVAL_ID="c08-rollback-fault-$approval_stamp"
runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/deploy-api.sh" --input "$INPUT" --execute \
  > "$EVIDENCE/api-deploy-before-rollback-fault.log" 2>&1
RESCUE_DEPLOY_RECORD="$(sed -n 's/^DEPLOY_RECORD=//p' "$EVIDENCE/api-deploy-before-rollback-fault.log")"
[[ -n "$RESCUE_DEPLOY_RECORD" && -f "$RESCUE_DEPLOY_RECORD" ]] || exit 19
assert_live_state "$CANDIDATE_SHA" candidate "$EVIDENCE/api-candidate-health-before-rollback-fault.json" \
  "$EVIDENCE/fixture-columns-candidate-before-rollback-fault.tsv" || exit 19

arm_health_fault old-health-once
if runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/rollback-api.sh" --input "$INPUT" --execute "$RESCUE_DEPLOY_RECORD" \
  > "$EVIDENCE/api-rollback-old-health-fault.log" 2>&1; then
  echo 'old health fault rollback unexpectedly succeeded' >&2
  exit 19
fi
[[ -f "$RUN/java-launch-state/fault-consumed-old-health-once" \
   && ! -e "$RUN/java-launch-state/fault-mode" ]] || exit 19
grep -Fq 'rolled-back API failed the configured health check' "$EVIDENCE/api-rollback-old-health-fault.log" || exit 19
grep -Fq 'pre-rollback API candidate restored' "$EVIDENCE/api-rollback-old-health-fault.log" || exit 19
assert_live_state "$CANDIDATE_SHA" candidate "$EVIDENCE/api-candidate-health-after-rollback-rescue.json" \
  "$EVIDENCE/fixture-columns-candidate-after-rollback-rescue.tsv" || exit 19
if ss -H -lnt | awk '$4 ~ /:10019$/ { found=1 } END { exit !found }'; then
  echo 'fault-injected old listener leaked after candidate rescue' >&2
  exit 19
fi
FAILED_ROLLBACK_RESCUE_DIR="$(find_isolated_rescue_backup "$CYF_RELEASE_APPROVAL_ID")"
prune_isolated_backup_path "$FAILED_ROLLBACK_RESCUE_DIR" rescue \
  failed-rollback-rescue-after-candidate-restore "failed-rollback:$CYF_RELEASE_APPROVAL_ID"

# 4. A final normal rollback proves the rescued candidate remains usable and
# leaves the isolated runtime in the old artifact/schema state.
runuser -u isp --preserve-environment -- "$CONTROL_RELEASE/rollback-api.sh" --input "$INPUT" --execute "$RESCUE_DEPLOY_RECORD" \
  > "$EVIDENCE/api-final-rollback-after-rescue.log" 2>&1
FINAL_ROLLBACK_RECORD="$(sed -n 's/^ROLLBACK_RECORD=//p' "$EVIDENCE/api-final-rollback-after-rescue.log")"
[[ -n "$FINAL_ROLLBACK_RECORD" && -f "$FINAL_ROLLBACK_RECORD" ]] || exit 19
assert_live_state "$OLD_API_SHA" old "$EVIDENCE/api-old-health-final.json" \
  "$EVIDENCE/fixture-columns-old-final.tsv" || exit 19

candidate_transition_count="$(grep -l '^target=candidate$' "$EVIDENCE"/schema-transitions/schema-transition-candidate.* 2>/dev/null | wc -l)"
old_transition_count="$(grep -l '^target=old$' "$EVIDENCE"/schema-transitions/schema-transition-old.* 2>/dev/null | wc -l)"
candidate_launch_count="$(grep -l '^target=candidate$' "$EVIDENCE"/schema-launches/java-launch-candidate.* 2>/dev/null | wc -l)"
old_launch_count="$(grep -l '^target=old$' "$EVIDENCE"/schema-launches/java-launch-old.* 2>/dev/null | wc -l)"
(( candidate_transition_count >= 6 && old_transition_count >= 8 \
   && candidate_launch_count >= 4 && old_launch_count >= 5 )) || exit 19
printf 'CANDIDATE_TRANSITIONS=%s\nOLD_TRANSITIONS=%s\nCANDIDATE_LAUNCHES=%s\nOLD_LAUNCHES=%s\n' \
  "$candidate_transition_count" "$old_transition_count" "$candidate_launch_count" "$old_launch_count" \
  > "$EVIDENCE/schema-transition-counts.txt"
mkdir -p "$EVIDENCE/release-records"
for record in "$NORMAL_DEPLOY_RECORD" "$NORMAL_ROLLBACK_RECORD" "$RESCUE_DEPLOY_RECORD" "$FINAL_ROLLBACK_RECORD"; do
  cp "$record" "${record}.sha256" "$EVIDENCE/release-records/"
done
chmod 0444 "$EVIDENCE/release-records"/*
(
  cd "$EVIDENCE/release-records"
  for sidecar in *.sha256; do sha256sum -c "$sidecar"; done
) > "$EVIDENCE/release-record-sidecars-durable.txt"

find /home/isp/baks/legacy-api -type f -printf '%m %s %p\n' | sort > "$EVIDENCE/api-backup-record-inventory.txt"
find /home/isp/baks/legacy-api -type f -name '*.sha256' -print0 \
  | xargs -0 -r -n1 sh -c 'cd "$(dirname "$1")" && sha256sum -c "$(basename "$1")"' _ \
  > "$EVIDENCE/api-backup-record-sidecars.txt"
python3 - /home/isp/baks/legacy-api/release-records "$EVIDENCE/api-record-modes.txt" <<'PY'
import json, os, pathlib, sys
root, output = map(pathlib.Path, sys.argv[1:])
rows = []
counts = {'PREPARED': 0, 'DEPLOYED_HEALTHY': 0, 'ROLLED_BACK_HEALTHY': 0}
for path in sorted(root.glob('*.json')):
    data = json.loads(path.read_text())
    status = data.get('status')
    if status not in counts:
        raise SystemExit(f'unknown release record status: {path.name}: {status}')
    counts[status] += 1
    mode = path.stat().st_mode & 0o777
    sidecar = pathlib.Path(str(path) + '.sha256')
    if status == 'PREPARED':
        if mode != 0o600 or sidecar.exists():
            raise SystemExit(f'failed deploy PREPARED record boundary mismatch: {path.name}')
    elif mode != 0o444 or not sidecar.is_file():
        raise SystemExit(f'completed release record boundary mismatch: {path.name}')
    rows.append(f'{mode:03o}\t{status}\t{path}')
if counts != {'PREPARED': 1, 'DEPLOYED_HEALTHY': 2, 'ROLLED_BACK_HEALTHY': 2}:
    raise SystemExit(f'unexpected release record counts: {counts}')
output.write_text('\n'.join(rows) + '\n')
PY

ss -lntp > "$EVIDENCE/listeners-during.txt"
ss -ntp > "$EVIDENCE/network-connections-after.txt"
if grep -E ':(3306|33060|5672|6379|9200|9300)\b' "$EVIDENCE/network-connections-after.txt"; then
  echo 'forbidden production dependency connection observed' >&2; exit 21
fi
runuser -u isp -- git -C "$ROOT/.worktrees/m2-api-base" status --porcelain=v1 --untracked-files=all > "$EVIDENCE/api-candidate-status-after.txt"
[[ ! -s "$EVIDENCE/api-candidate-status-after.txt" ]] || exit 22
cp "$RUN/logs/old-api.stdout.log" "$EVIDENCE/old-api.stdout.log"
cp "$RUN/logs/mysql-source.log" "$EVIDENCE/mysql-source.log"
cp "$RUN/logs/mysql-restore.log" "$EVIDENCE/mysql-restore.log"
cp "$RUN/logs/redis.log" "$EVIDENCE/redis.log"

cat > "$EVIDENCE/result.txt" <<EOF
ISOLATED_DATABASE_DUMP=PASS
ISOLATED_DATABASE_RESTORE=PASS
ISOLATED_DATABASE_SCHEMA_COMPARE=PASS
ISOLATED_DATABASE_ALL_TABLE_ROW_COUNTS_COMPARE=PASS
ISOLATED_DATABASE_CHECK_TABLE=PASS
ISOLATED_DATABASE_ACCOUNT_GRANTS_COMPARE=PASS
ISOLATED_STAGED_SCHEMA_TRANSITIONS=PASS
MIXED_SCHEMA_WITHOUT_MARKER_FAIL_CLOSED=PASS
INTERRUPTED_MIXED_SCHEMA_RESCUE=PASS
UNKNOWN_THIRD_SCHEMA_STATE_FAIL_CLOSED=PASS
CANDIDATE_SCHEMA_DUMP_RESTORE=PASS
PINNED_CANDIDATE_SCHEMA_CONTRACT=PASS
OLD_SCHEMA_BEFORE_AND_AFTER_RUNTIME=PASS
RELEASE_TOOL_BYTE_EXACT=PASS
JAVA_LAUNCH_SHIM_SCHEMA_BOUNDARY=PASS
JAVA_AGENT_PREMAIN_SCHEMA_BOUNDARY=PASS
OLD_REAL_API_ARTIFACT_SHA256=$OLD_API_SHA
CANDIDATE_API_ARTIFACT_SHA256=$CANDIDATE_SHA
ARTIFACTS_DIFFER=PASS
API_PINNED_DEPLOY=PASS
API_DEPLOY_RECORD=DEPLOYED_HEALTHY
API_EXPLICIT_ROLLBACK=PASS
API_ROLLBACK_RECORD=ROLLED_BACK_HEALTHY
API_DEPLOY_HEALTH_FAULT_AUTO_RESTORE_OLD=PASS
API_ROLLBACK_OLD_HEALTH_FAULT_RESCUE_CANDIDATE=PASS
API_FINAL_ROLLBACK_AFTER_RESCUE=PASS
PRODUCTION_DATABASE_OPERATION=NOT_PERFORMED
PRODUCTION_RABBITMQ_OPERATION=NOT_PERFORMED
PRODUCTION_DEPLOYMENT=NOT_PERFORMED
APPROVAL_GATE_DEFAULT_DENY=PASS
APPROVAL_INJECTION=ISOLATED_SYNTHETIC_ONLY
PRODUCTION_APPROVAL=NOT_TESTED
EOF
DRIVER
chmod +x "$RUN/driver.sh"

DRILL_UNIT="cyf-c08-api-drill-$$-$(date +%s)"
systemd-run --wait --pipe --collect --unit "$DRILL_UNIT" -p Type=exec \
  "${SYSTEMD_MEMORY_ARGS[@]}" \
  /usr/bin/unshare -m -n -p --fork --kill-child=KILL --mount-proc -- \
  /usr/bin/env OLD_API_SHA="$OLD_API_SHA" CANDIDATE_SHA="$CANDIDATE_SHA" \
  ROOT="$ROOT" INPUT="$ISOLATED_INPUT" RUN="$RUN" SANDBOX="$SANDBOX" EVIDENCE="$EVIDENCE" \
  SCHEMA_TRANSITION_SHA="$SCHEMA_TRANSITION_SHA" SCHEMA_AGENT_SHA="$SCHEMA_AGENT_SHA" JAVA_LAUNCH_SHIM_SHA="$JAVA_LAUNCH_SHIM_SHA" \
  CONTROL_RELEASE="$CONTROL_RELEASE" CONTROL_RELEASES="$CONTROL_RELEASES" CONTROL_API_REPO="$CONTROL_API_REPO" \
  API_ARTIFACT="$API_ARTIFACT" \
  API_SCHEMA="$API_SCHEMA" CHAT_SCHEMA="$CHAT_SCHEMA" AGENT_SCHEMA="$AGENT_SCHEMA" \
  OLD_AGENT_SCHEMA="$OLD_AGENT_SCHEMA" OLD_CHAT_SCHEMA="$OLD_CHAT_SCHEMA" HEALTH_EXPECTED_REGEX="$HEALTH_EXPECTED_REGEX" \
  CGROUP_MEMORY_MAX_BYTES="$DRILL_MEMORY_MAX_BYTES" \
  CGROUP_MEMORY_SWAP_MAX_BYTES="$DRILL_MEMORY_SWAP_MAX_BYTES" \
  /bin/bash "$RUN/driver.sh"
production_identity_unchanged \
  || { echo 'production API identity changed during isolated drill' >&2; exit 24; }
printf '%s\n' 'PRODUCTION_API_IDENTITY_UNCHANGED=PASS' >> "$EVIDENCE/host-resource-preflight.txt"

OLD_SOURCE_SHA_AFTER="$(sha256sum "$OLD_SOURCE" | awk '{print $1}')"
[[ "$OLD_SOURCE_SHA_AFTER" == "$OLD_SOURCE_SHA_BEFORE" ]] || { echo 'production source JAR changed during isolated drill' >&2; exit 23; }
printf 'SOURCE_SHA256_AFTER=%s\nSOURCE_UNCHANGED=PASS\n' "$OLD_SOURCE_SHA_AFTER" >> "$EVIDENCE/source-old-artifact.txt"
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
(
  cd "$EVIDENCE"
  find . -type f ! -name MANIFEST.sha256 ! -name MANIFEST.sha256.sha256 \
    ! -name manifest-check.txt ! -name manifest-check.txt.sha256 \
    -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256
  sha256sum MANIFEST.sha256 > MANIFEST.sha256.sha256
)
(cd "$EVIDENCE" && sha256sum -c MANIFEST.sha256) > "$RUN/manifest-check.txt"
mv "$RUN/manifest-check.txt" "$EVIDENCE/manifest-check.txt"
(cd "$EVIDENCE" && sha256sum manifest-check.txt > manifest-check.txt.sha256)
python3 - "$RUN" <<'PY'
import os,pathlib,sys
run=os.fsencode(sys.argv[1]); leaks=[]
for proc in pathlib.Path('/proc').iterdir():
    if not proc.name.isdigit() or int(proc.name)==os.getpid(): continue
    try: cmd=(proc/'cmdline').read_bytes()
    except (FileNotFoundError,PermissionError,ProcessLookupError): continue
    if run in cmd: leaks.append((proc.name,cmd.replace(b'\0',b' ')[:500].decode('utf-8','replace')))
if leaks: raise SystemExit('isolated rollback process leak: '+repr(leaks))
PY
python3 - "$EVIDENCE" "$EVIDENCE_ROOT" <<'PY'
import os,shutil,sys
source,target=sys.argv[1:]
os.makedirs(os.path.dirname(target),exist_ok=True)
shutil.copytree(source,target)
PY
printf 'ISOLATED_API_DEPLOY_ROLLBACK_DRILL=PASS\nEVIDENCE=%s\n' "$EVIDENCE_ROOT"
