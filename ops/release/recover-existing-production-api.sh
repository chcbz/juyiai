#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SELF="$ROOT/ops/release/recover-existing-production-api.sh"
INPUT="$ROOT/ops/release/m2-c08-r6-input.json"
LAUNCH_HELPER="$ROOT/ops/release/lib/launch-existing-api.py"
RECOVERY_TOOL_MANIFEST="$ROOT/ops/release/production-api-recovery-tools.sha256"
LEGACY_START_SCRIPT=/home/isp/bin/cyf_api_kit_start.sh
LIVE_JAR=/home/isp/hosts/cyf/api/cyf-api-kit.jar
WORK_DIR=/home/isp/hosts/cyf/api
PID_FILE=/home/isp/hosts/cyf/api/cyf-api-kit.pid
LOG_DIR=/home/isp/hosts/cyf/api/logs
APP_LOG_FILE=/home/isp/hosts/cyf/api/logs/root.log
RUNTIME_USER=isp
LOCK_FILE=/tmp/cyf-production-api-recovery.lock
API_RELEASE_LOCK_FILE=/tmp/cyf-release-api.lock
EXPECTED_LIVE_JAR_SHA256=8b8f2e7dcab7601ed8085436d41b11b99c2b040a566072170f9c2082662cb0c3
EXPECTED_START_SCRIPT_SHA256=536b6f5feaddf8e262a9a4cd324a229ec908987278078ba635c1118f501bcb30
EXPECTED_INPUT_SHA256=797767b9851dc35d5b1b2a20499f377d79c65aff7dc436495dc0d600b883b89f
HEALTH_URL=http://127.0.0.1:10018/actuator/health
HEALTH_TIMEOUT_SECONDS=180
MIN_HOST_MEM_AVAILABLE_BYTES=1073741824
MIN_HOST_DISK_AVAILABLE_BYTES=5368709120
MODE=dry-run

usage() {
  printf 'Usage: %s [--dry-run|--execute]\n' "$0"
}

case "${1:---dry-run}" in
  --dry-run) MODE=dry-run ;;
  --execute) MODE=execute ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac
(( $# <= 1 )) || { usage >&2; exit 2; }

for command in bash python3 sha256sum stat flock curl ss nohup awk grep date readlink kill seq mktemp df basename cat chmod chown sleep id touch; do
  command -v "$command" >/dev/null 2>&1 || { echo "missing command: $command" >&2; exit 2; }
done
for path in "$SELF" "$INPUT" "$LAUNCH_HELPER" "$RECOVERY_TOOL_MANIFEST" \
  "$RECOVERY_TOOL_MANIFEST.sha256" "$LEGACY_START_SCRIPT" "$LIVE_JAR" "$PID_FILE"; do
  [[ -f "$path" && ! -L "$path" ]] || { echo "required physical file missing: $path" >&2; exit 2; }
done
[[ -d "$WORK_DIR" && ! -L "$WORK_DIR" && -d "$LOG_DIR" && ! -L "$LOG_DIR" ]] \
  || { echo 'production API work/log directory must be physical directories' >&2; exit 2; }
[[ "$(stat -c %a "$SELF")" == 555 && "$(stat -c %a "$LAUNCH_HELPER")" == 555 ]] \
  || { echo 'production recovery tools must be sealed mode 0555' >&2; exit 2; }
[[ "$(stat -c %a "$RECOVERY_TOOL_MANIFEST")" == 444 \
   && "$(stat -c %a "$RECOVERY_TOOL_MANIFEST.sha256")" == 444 ]] \
  || { echo 'production recovery tool manifest and sidecar must be mode 0444' >&2; exit 2; }
EXPECTED_MANIFEST_SIDECAR="$(sha256sum "$RECOVERY_TOOL_MANIFEST" | awk '{print $1}')  $(basename "$RECOVERY_TOOL_MANIFEST")"
[[ "$(cat "$RECOVERY_TOOL_MANIFEST.sha256")" == "$EXPECTED_MANIFEST_SIDECAR" ]] \
  || { echo 'production recovery tool manifest sidecar mismatch' >&2; exit 2; }
(cd "$ROOT" && sha256sum -c "${RECOVERY_TOOL_MANIFEST#$ROOT/}") >/dev/null \
  || { echo 'production recovery tool digest verification failed' >&2; exit 2; }
RECOVERY_TOOL_MANIFEST_SHA256="$(sha256sum "$RECOVERY_TOOL_MANIFEST" | awk '{print $1}')"
[[ "$(sha256sum "$INPUT" | awk '{print $1}')" == "$EXPECTED_INPUT_SHA256" ]] \
  || { echo 'r6 input SHA-256 mismatch' >&2; exit 2; }
[[ "$(sha256sum "$LIVE_JAR" | awk '{print $1}')" == "$EXPECTED_LIVE_JAR_SHA256" ]] \
  || { echo 'existing production JAR SHA-256 mismatch' >&2; exit 2; }
[[ "$(sha256sum "$LEGACY_START_SCRIPT" | awk '{print $1}')" == "$EXPECTED_START_SCRIPT_SHA256" ]] \
  || { echo 'legacy start script SHA-256 mismatch' >&2; exit 2; }
RUNTIME_UID="$(id -u "$RUNTIME_USER")"
RUNTIME_GID="$(id -g "$RUNTIME_USER")"
[[ "$RUNTIME_UID" =~ ^[0-9]+$ && "$RUNTIME_GID" =~ ^[0-9]+$ ]] \
  || { echo 'production API runtime identity is invalid' >&2; exit 2; }
"$LAUNCH_HELPER" \
  --start-script "$LEGACY_START_SCRIPT" \
  --expected-start-script-sha256 "$EXPECTED_START_SCRIPT_SHA256" \
  --jar "$LIVE_JAR" \
  --expected-jar-sha256 "$EXPECTED_LIVE_JAR_SHA256" \
  --work-dir "$WORK_DIR" --expected-runtime-user "$RUNTIME_USER" --validate-only
"$LAUNCH_HELPER" \
  --start-script "$LEGACY_START_SCRIPT" \
  --expected-start-script-sha256 "$EXPECTED_START_SCRIPT_SHA256" \
  --jar "$LIVE_JAR" \
  --expected-jar-sha256 "$EXPECTED_LIVE_JAR_SHA256" \
  --work-dir "$WORK_DIR" --expected-runtime-user "$RUNTIME_USER" --validate-runtime-identity-only

HEALTH_EXPECTED_REGEX="$(python3 - "$INPUT" <<'PY'
import json,sys
with open(sys.argv[1], encoding='utf-8') as stream:
    print(json.load(stream)['api']['deploy']['healthExpectedRegex'])
PY
)"
for sample in '{"status":"UP"}' '{"status":{"code":"UP","description":""}}'; do
  [[ "$sample" =~ $HEALTH_EXPECTED_REGEX ]] || { echo 'r6 health matcher rejected a supported UP payload' >&2; exit 2; }
done
[[ ! '{"status":"DOWN"}' =~ $HEALTH_EXPECTED_REGEX ]] \
  || { echo 'r6 health matcher accepted DOWN' >&2; exit 2; }

production_is_down() {
  local pid
  pid="$(cat "$PID_FILE")"
  [[ "$pid" =~ ^[0-9]+$ ]] || { echo 'production API pidfile is not numeric' >&2; return 1; }
  [[ ! -d "/proc/$pid" ]] || { echo 'pidfile currently identifies a live process' >&2; return 1; }
  [[ -z "$(ss -lntH 'sport = :10018')" ]] || { echo 'production API port 10018 is already listening' >&2; return 1; }
}
production_is_down
host_resources_ready() {
  local memory_available disk_available
  memory_available="$(awk '/^MemAvailable:/ {print $2 * 1024}' /proc/meminfo)"
  disk_available="$(df -PB1 -- "$WORK_DIR" | awk 'NR==2 {print $4}')"
  if (( memory_available < MIN_HOST_MEM_AVAILABLE_BYTES )); then
    echo "host memory observation below former threshold (non-blocking): available=$memory_available former_required=$MIN_HOST_MEM_AVAILABLE_BYTES" >&2
  fi
  if (( disk_available < MIN_HOST_DISK_AVAILABLE_BYTES )); then
    echo "host disk observation below former threshold (non-blocking): available=$disk_available former_required=$MIN_HOST_DISK_AVAILABLE_BYTES" >&2
  fi
  HOST_MEM_AVAILABLE_BYTES="$memory_available"
  HOST_DISK_AVAILABLE_BYTES="$disk_available"
}
host_resources_ready

if [[ "$MODE" == dry-run ]]; then
  cat <<EOF
RECOVERY_MODE=DRY_RUN
RECOVERY_READY=YES
EXISTING_LIVE_JAR_SHA256=$EXPECTED_LIVE_JAR_SHA256
LEGACY_START_SCRIPT_SHA256=$EXPECTED_START_SCRIPT_SHA256
R6_INPUT_SHA256=$EXPECTED_INPUT_SHA256
RECOVERY_TOOL_MANIFEST_SHA256=$RECOVERY_TOOL_MANIFEST_SHA256
HOST_MEM_AVAILABLE_BYTES=$HOST_MEM_AVAILABLE_BYTES
MIN_HOST_MEM_AVAILABLE_BYTES=$MIN_HOST_MEM_AVAILABLE_BYTES
HOST_DISK_AVAILABLE_BYTES=$HOST_DISK_AVAILABLE_BYTES
FIXED_RESOURCE_ADMISSION_GATE=DISABLED_BY_USER_2026_08_28
MIN_HOST_DISK_AVAILABLE_BYTES=$MIN_HOST_DISK_AVAILABLE_BYTES
RUNTIME_USER=$RUNTIME_USER
RUNTIME_UID=$RUNTIME_UID
RUNTIME_GID=$RUNTIME_GID
PRODUCTION_DATABASE_OPERATION=NOT_PERFORMED
PRODUCTION_RABBITMQ_OPERATION=NOT_PERFORMED
PRODUCTION_ARTIFACT_REPLACEMENT=NOT_PERFORMED
PRODUCTION_PROCESS_START=NOT_PERFORMED
EXECUTE_REQUIRES_EXPLICIT_BOUND_APPROVAL=YES
EOF
  exit 0
fi

(( EUID == 0 )) || { echo 'production API recovery execute requires root' >&2; exit 2; }
[[ "${CYF_PRODUCTION_RECOVERY_APPROVED:-}" == YES ]] \
  || { echo 'execute requires CYF_PRODUCTION_RECOVERY_APPROVED=YES' >&2; exit 2; }
[[ "${CYF_PRODUCTION_RECOVERY_APPROVAL_ID:-}" =~ ^[A-Za-z0-9._:-]{1,128}$ ]] \
  || { echo 'execute requires a safe CYF_PRODUCTION_RECOVERY_APPROVAL_ID' >&2; exit 2; }
[[ "${CYF_PRODUCTION_RECOVERY_EXPECTED_JAR_SHA256:-}" == "$EXPECTED_LIVE_JAR_SHA256" ]] \
  || { echo 'recovery approval is not bound to the existing JAR SHA-256' >&2; exit 2; }
[[ "${CYF_PRODUCTION_RECOVERY_EXPECTED_START_SCRIPT_SHA256:-}" == "$EXPECTED_START_SCRIPT_SHA256" ]] \
  || { echo 'recovery approval is not bound to the legacy start script SHA-256' >&2; exit 2; }
[[ "${CYF_PRODUCTION_RECOVERY_EXPECTED_TOOL_MANIFEST_SHA256:-}" == "$RECOVERY_TOOL_MANIFEST_SHA256" ]] \
  || { echo 'recovery approval is not bound to the recovery tool manifest SHA-256' >&2; exit 2; }

for lock_path in "$API_RELEASE_LOCK_FILE" "$LOCK_FILE"; do
  [[ ! -L "$lock_path" && ( ! -e "$lock_path" || -f "$lock_path" ) ]] \
    || { echo "production API lock path is unsafe: $lock_path" >&2; exit 2; }
done
exec 8>"$API_RELEASE_LOCK_FILE"
flock -n 8 || { echo 'another API deploy/rollback operation is active' >&2; exit 2; }
exec 9>"$LOCK_FILE"
flock -n 9 || { echo 'another production API recovery is active' >&2; exit 2; }
production_is_down
host_resources_ready
[[ "$(sha256sum "$RECOVERY_TOOL_MANIFEST" | awk '{print $1}')" == "$RECOVERY_TOOL_MANIFEST_SHA256" ]] || exit 2
(cd "$ROOT" && sha256sum -c "${RECOVERY_TOOL_MANIFEST#$ROOT/}") >/dev/null || exit 2
[[ "$(sha256sum "$INPUT" | awk '{print $1}')" == "$EXPECTED_INPUT_SHA256" ]] || exit 2
[[ "$(sha256sum "$LIVE_JAR" | awk '{print $1}')" == "$EXPECTED_LIVE_JAR_SHA256" ]] || exit 2
[[ "$(sha256sum "$LEGACY_START_SCRIPT" | awk '{print $1}')" == "$EXPECTED_START_SCRIPT_SHA256" ]] || exit 2

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$LOG_DIR/recovery-existing-old-$STAMP-$$-$RANDOM.log"
HEALTH_BODY="$(mktemp /tmp/cyf-production-api-recovery-health.XXXXXX.json)"
NEW_PID=''
NEW_START_TICKS=''
PID_TMP=''
SUCCESS=0
proc_start_ticks() {
  python3 - "$1" <<'PYPROC'
import pathlib,sys
text=(pathlib.Path('/proc')/sys.argv[1]/'stat').read_text(); end=text.rfind(')')
if end < 0: raise SystemExit('malformed proc stat')
print(text[end+2:].split()[19])
PYPROC
}
same_recovery_process() {
  [[ -n "$NEW_PID" && -n "$NEW_START_TICKS" && -d "/proc/$NEW_PID" ]] || return 1
  [[ "$(proc_start_ticks "$NEW_PID" 2>/dev/null)" == "$NEW_START_TICKS" ]]
}
listener_owned_by_recovery_process() {
  ss -lntpH 'sport = :10018' 2>/dev/null | grep -Eq "pid=$NEW_PID([,)]|$)"
}
process_owned_by_runtime_user() {
  [[ "$(awk '/^Uid:/ {print $2}' "/proc/$NEW_PID/status" 2>/dev/null)" == "$RUNTIME_UID" ]]
  [[ "$(awk '/^Gid:/ {print $2}' "/proc/$NEW_PID/status" 2>/dev/null)" == "$RUNTIME_GID" ]]
}
cleanup() {
  local exit_code=$?
  set +e
  if (( SUCCESS == 0 )) && same_recovery_process; then
    kill -TERM "$NEW_PID" 2>/dev/null || true
    for _ in {1..30}; do
      same_recovery_process || break
      sleep 1
    done
    same_recovery_process && kill -KILL "$NEW_PID" 2>/dev/null || true
    wait "$NEW_PID" 2>/dev/null || true
  fi
  python3 - "$HEALTH_BODY" "$PID_TMP" <<'PY' >/dev/null 2>&1 || true
from pathlib import Path
import sys
for value in sys.argv[1:]:
    if not value:
        continue
    try:
        Path(value).unlink()
    except FileNotFoundError:
        pass
PY
  return "$exit_code"
}
trap cleanup EXIT

nohup "$LAUNCH_HELPER" \
  --start-script "$LEGACY_START_SCRIPT" \
  --expected-start-script-sha256 "$EXPECTED_START_SCRIPT_SHA256" \
  --jar "$LIVE_JAR" \
  --expected-jar-sha256 "$EXPECTED_LIVE_JAR_SHA256" \
  --work-dir "$WORK_DIR" --expected-runtime-user "$RUNTIME_USER" \
  --application-log "$APP_LOG_FILE" --recovery-log "$LOG_FILE" \
  >/dev/null 2>&1 < /dev/null 8>&- 9>&- &
NEW_PID=$!
for _ in {1..20}; do
  NEW_START_TICKS="$(proc_start_ticks "$NEW_PID" 2>/dev/null || true)"
  [[ -n "$NEW_START_TICKS" ]] && break
  sleep 0.1
done
[[ -n "$NEW_START_TICKS" ]] || { echo "recovery launcher exited before identity capture; inspect $LOG_FILE" >&2; exit 3; }

ready=0
http_code=''
for _ in $(seq 1 "$HEALTH_TIMEOUT_SECONDS"); do
  same_recovery_process \
    || { echo "existing production API exited during recovery; inspect $LOG_FILE" >&2; exit 3; }
  http_code="$(curl --noproxy '*' --silent --output "$HEALTH_BODY" --max-time 5 --write-out '%{http_code}' "$HEALTH_URL" 2>/dev/null || true)"
  if [[ "$http_code" == 200 ]] && listener_owned_by_recovery_process \
    && grep -Eq -- "$HEALTH_EXPECTED_REGEX" "$HEALTH_BODY"; then
    ready=1
    break
  fi
  sleep 1
done
(( ready == 1 )) || { echo "existing production API did not become healthy; inspect $LOG_FILE" >&2; exit 3; }
same_recovery_process || { echo 'recovered process identity changed before commit' >&2; exit 3; }
process_owned_by_runtime_user || { echo 'recovered process runtime user/group mismatch' >&2; exit 3; }
listener_owned_by_recovery_process || { echo 'recovered process does not own API port 10018' >&2; exit 3; }
[[ "$(readlink -f "/proc/$NEW_PID/exe")" == /home/isp/apps/jdk21/bin/java ]] \
  || { echo 'recovered process executable identity mismatch' >&2; exit 3; }
[[ "$(sha256sum "$LIVE_JAR" | awk '{print $1}')" == "$EXPECTED_LIVE_JAR_SHA256" ]] \
  || { echo 'production JAR changed during recovery' >&2; exit 3; }
START_TICKS="$NEW_START_TICKS"
PID_TMP="$(mktemp --tmpdir="$WORK_DIR" .cyf-api-kit.pid.recovery.XXXXXX)"
printf '%s\n' "$NEW_PID" > "$PID_TMP"
chmod 0644 "$PID_TMP"
chown isp:isp "$PID_TMP"
python3 - "$PID_TMP" "$PID_FILE" <<'PY'
import os,sys
os.replace(sys.argv[1],sys.argv[2])
PY
SUCCESS=1
cat <<EOF
RECOVERY_MODE=EXECUTE
RECOVERY_RESULT=HEALTHY
APPROVAL_ID=$CYF_PRODUCTION_RECOVERY_APPROVAL_ID
PID=$NEW_PID
START_TICKS=$START_TICKS
RUNTIME_USER=$RUNTIME_USER
RUNTIME_UID=$RUNTIME_UID
RUNTIME_GID=$RUNTIME_GID
LIVE_JAR_SHA256=$EXPECTED_LIVE_JAR_SHA256
LEGACY_START_SCRIPT_SHA256=$EXPECTED_START_SCRIPT_SHA256
RECOVERY_TOOL_MANIFEST_SHA256=$RECOVERY_TOOL_MANIFEST_SHA256
HEALTH_HTTP_STATUS=$http_code
LOG_FILE=$LOG_FILE
PRODUCTION_DATABASE_OPERATION=NOT_PERFORMED_BY_RECOVERY_SCRIPT
PRODUCTION_RABBITMQ_OPERATION=NOT_PERFORMED_BY_RECOVERY_SCRIPT
PRODUCTION_ARTIFACT_REPLACEMENT=NOT_PERFORMED
EOF
