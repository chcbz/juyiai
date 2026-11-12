#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: deploy-api.sh [--input PATH] [--dry-run|--execute]

Default is read-only dry-run. Execution additionally requires:
  CYF_RELEASE_APPROVED=YES
  CYF_RELEASE_APPROVAL_ID=<auditable-change-id>
  CYF_RELEASE_APPROVED_API_HEAD=<full SHA>
  CYF_RELEASE_APPROVED_API_TREE=<full tree SHA>
  CYF_RELEASE_APPROVED_WEB_HEAD=<full SHA>
  CYF_RELEASE_APPROVED_WEB_TREE=<full tree SHA>

The script never performs database or RabbitMQ operations. It backs up the
physical live JAR and the exact NUL-delimited process argv with checksums,
atomically installs the verified artifact, restarts with the saved argv, and
requires the configured health check to pass.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 0)) || die "unexpected positional arguments"
for command in git python3 sha256sum curl realpath stat cp mv sync flock nohup mktemp; do require_command "$command"; done
load_release_input "$INPUT_FILE"
require_execute_approval
print_mode
acquire_execution_lock api
assert_clean_candidate "API" "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
verify_release_record

API_LIVE_JAR="$(normalize_absolute_path 'API live JAR' "$(json_get "$RELEASE_INPUT" api.deploy.liveJar)")"
API_PID_FILE="$(normalize_absolute_path 'API PID file' "$(json_get "$RELEASE_INPUT" api.deploy.pidFile)")"
API_WORK_DIR="$(normalize_absolute_path 'API work directory' "$(json_get "$RELEASE_INPUT" api.deploy.workDir)")"
API_BACKUP_ROOT="$(normalize_absolute_path 'API backup root' "$(json_get "$RELEASE_INPUT" api.deploy.backupRoot)")"
API_RECORD_ROOT="$(normalize_absolute_path 'API record root' "$(json_get "$RELEASE_INPUT" api.deploy.recordRoot)")"
API_HEALTH_URL="$(json_get "$RELEASE_INPUT" api.deploy.healthUrl)"
API_HEALTH_REGEX="$(json_get "$RELEASE_INPUT" api.deploy.healthExpectedRegex)"
API_STOP_TIMEOUT="$(json_get "$RELEASE_INPUT" api.deploy.stopTimeoutSeconds)"
API_HEALTH_TIMEOUT="$(json_get "$RELEASE_INPUT" api.deploy.healthTimeoutSeconds)"
[[ "$API_STOP_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ && "$API_HEALTH_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ ]] \
  || die "API timeout configuration is invalid"
[[ "$API_HEALTH_URL" =~ ^https?://[^[:space:]]+$ ]] || die "API health URL is invalid"
[[ -d "$API_WORK_DIR" && ! -L "$API_WORK_DIR" ]] || die "API work directory is unavailable or symlinked"
[[ -f "$API_LIVE_JAR" && ! -L "$API_LIVE_JAR" ]] || die "live API JAR is unavailable or symlinked"
assert_path_within "API live JAR" "$API_LIVE_JAR" "$API_WORK_DIR"
# The canonical API launcher writes its PID under the root-owned runtime
# directory /run/cyf-api.  Legacy/test candidates may keep their PID inside
# the API work directory; any outside-workdir path must be this one exact,
# non-symlinked, root-owned runtime endpoint.  Do not generalize this to an
# arbitrary /run path: deploy must not be allowed to signal a foreign PID.
API_CANONICAL_LAUNCHER=""
if [[ "$API_PID_FILE" == "$API_WORK_DIR" || "$API_PID_FILE" == "$API_WORK_DIR"/* ]]; then
  assert_path_within "API PID file" "$API_PID_FILE" "$API_WORK_DIR"
else
  API_CANONICAL_RUNTIME_PID_DIR="/run/cyf-api"
  API_CANONICAL_RUNTIME_PID_FILE="$API_CANONICAL_RUNTIME_PID_DIR/cyf-api-kit.pid"
  API_CANONICAL_LAUNCHER="/usr/local/sbin/cyf-api-kit"
  [[ "$API_PID_FILE" == "$API_CANONICAL_RUNTIME_PID_FILE" ]] \
    || die "API PID file outside work directory is not the canonical runtime PID file: $API_PID_FILE"
  [[ -d "$API_CANONICAL_RUNTIME_PID_DIR" && ! -L "$API_CANONICAL_RUNTIME_PID_DIR" ]] \
    || die "canonical API runtime PID directory is unavailable or symlinked"
  [[ "$(stat -c '%a %U %G' -- "$API_CANONICAL_RUNTIME_PID_DIR")" == "750 root root" ]] \
    || die "canonical API runtime PID directory must be root-owned mode 0750"
  [[ -f "$API_PID_FILE" && ! -L "$API_PID_FILE" ]] \
    || die "canonical API runtime PID file is unavailable or symlinked"
  [[ "$(stat -c '%a %U %G' -- "$API_PID_FILE")" == "644 root root" ]] \
    || die "canonical API runtime PID file must be root-owned mode 0644"
  [[ -f "$API_CANONICAL_LAUNCHER" && ! -L "$API_CANONICAL_LAUNCHER" && -x "$API_CANONICAL_LAUNCHER" ]] \
    || die "canonical API launcher is unavailable or symlinked"
  [[ "$(stat -c '%a %U %G %h' -- "$API_CANONICAL_LAUNCHER")" == "755 root root 1" ]] \
    || die "canonical API launcher must be single-link root:root mode 0755"
fi
API_LOG_DIR="$(normalize_absolute_path 'API log directory' "$API_WORK_DIR/logs")"
assert_path_within "API log directory" "$API_LOG_DIR" "$API_WORK_DIR"
assert_disk_gate "$API_WORK_DIR" "API deploy filesystem"
assert_disk_gate "$API_BACKUP_ROOT" "API backup filesystem"

launch_api_runtime() {
  local launch_log="$1" pid_output="$2" lock_path lock_identity
  if [[ -z "$API_CANONICAL_LAUNCHER" ]]; then
    launch_from_argv_backup "$BACKUP_DIR/old.argv.nul" "$BACKUP_DIR/old.cwd" \
      "$API_LIVE_JAR" "$launch_log" "$pid_output"
    return 0
  fi

  # The canonical launcher owns the root-only Jasypt/voice environment.  Pass
  # our already-held API release lock on its documented FD 8 contract so this
  # handoff cannot race another API lifecycle operation.
  [[ "${CYF_RELEASE_EXECUTION_LOCK_FD:-}" =~ ^[0-9]+$ ]] \
    || die "canonical launcher requires the API release execution lock"
  lock_path="/tmp/cyf-release-api.lock"
  [[ -e "/proc/$$/fd/$CYF_RELEASE_EXECUTION_LOCK_FD" ]] \
    || die "API release execution lock FD is unavailable"
  lock_identity="$(stat -Lc '%d:%i' -- "$lock_path")"
  [[ "$(stat -Lc '%d:%i' -- "/proc/$$/fd/$CYF_RELEASE_EXECUTION_LOCK_FD")" == "$lock_identity" ]] \
    || die "API release execution lock identity changed"
  (
    exec 8>&"$CYF_RELEASE_EXECUTION_LOCK_FD"
    # The child keeps FD 8 for the launcher contract only.  Close the
    # dynamically allocated parent FD in this child so the Java daemon cannot
    # retain /tmp/cyf-release-api.lock after the launcher returns.
    eval "exec ${CYF_RELEASE_EXECUTION_LOCK_FD}>&-"
    export CYF_RELEASE_LOCK_INHERITED_FD=8
    export CYF_RELEASE_LOCK_DEVICE="${lock_identity%%:*}"
    export CYF_RELEASE_LOCK_INODE="${lock_identity##*:}"
    export CYF_RELEASE_LOCK_HELD=1
    "$API_CANONICAL_LAUNCHER" start
  )
  [[ -f "$API_PID_FILE" && ! -L "$API_PID_FILE" ]] \
    || die "canonical API launcher did not produce a physical PID file"
  NEW_PID="$(cat -- "$API_PID_FILE")"
  [[ "$NEW_PID" =~ ^[0-9]+$ ]] || die "canonical API launcher produced an invalid PID"
  printf '%s\n' "$NEW_PID" > "$pid_output"
}

OLD_PID="$(find_single_java_jar_pid "$API_LIVE_JAR")"
OLD_TICKS="$(process_start_ticks "$OLD_PID")"
OLD_JAR_SHA="$(artifact_sha256 "$API_LIVE_JAR")"
OLD_ARGV_SHA="$(proc_argv_sha256 "$OLD_PID")"
NEW_JAR_SHA="$(artifact_sha256 "$API_ARTIFACT")"
log "API dry-run evidence: live_pid=$OLD_PID live_jar_sha256=$OLD_JAR_SHA argv_sha256=$OLD_ARGV_SHA"
log "API candidate artifact_sha256=$NEW_JAR_SHA"

if (( EXECUTE == 0 )); then
  printf 'DRY_RUN=PASS\nCOMPONENT=api\nLIVE_PID=%s\nLIVE_JAR_SHA256=%s\nSAVED_ARGV_SHA256=%s\nCANDIDATE_SHA256=%s\n' \
    "$OLD_PID" "$OLD_JAR_SHA" "$OLD_ARGV_SHA" "$NEW_JAR_SHA"
  exit 0
fi

mkdir -p -- "$API_LOG_DIR"
assert_not_symlink "API log directory" "$API_LOG_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CHANGE_ID="$CYF_RELEASE_APPROVAL_ID"
BACKUP_DIR="$API_BACKUP_ROOT/api-${STAMP}-${API_HEAD}-${API_TREE}-${CHANGE_ID}"
DEPLOY_RECORD="$API_RECORD_ROOT/api-deploy-${STAMP}-${API_HEAD}-${API_TREE}-${CHANGE_ID}.json"
DEPLOY_RECORD_COMPLETE_TEMP="${DEPLOY_RECORD}.complete.tmp"
STAGE_JAR="$(dirname -- "$API_LIVE_JAR")/.cyf-api-stage-${API_HEAD}-${API_TREE}-${CHANGE_ID}.jar"
RESTORE_STAGE_JAR="$(dirname -- "$API_LIVE_JAR")/.cyf-api-restore-${API_HEAD}-${API_TREE}-${CHANGE_ID}.jar"
LAUNCH_LOG="$API_LOG_DIR/release-${STAMP}-${API_HEAD}-${CHANGE_ID}.log"
NEW_PID_FILE="$BACKUP_DIR/new.pid"
DEPLOY_CHANGED=0
NEW_PID=""
OLD_JAR_NAME=""

[[ ! -e "$BACKUP_DIR" && ! -L "$BACKUP_DIR" ]] || die "API backup path already exists"
[[ ! -e "$DEPLOY_RECORD" && ! -L "$DEPLOY_RECORD" ]] || die "API deploy record path already exists"
[[ ! -e "$DEPLOY_RECORD_COMPLETE_TEMP" && ! -L "$DEPLOY_RECORD_COMPLETE_TEMP" ]] \
  || die "API completed-record staging path already exists"
[[ ! -e "$STAGE_JAR" && ! -L "$STAGE_JAR" ]] || die "API staging path already exists"
[[ ! -e "$RESTORE_STAGE_JAR" && ! -L "$RESTORE_STAGE_JAR" ]] || die "API restore staging path already exists"

restore_old_on_error() {
  local exit_code=$?
  trap - EXIT
  set +e
  if (( DEPLOY_CHANGED == 1 )); then
    log "deployment failed; attempting automatic API artifact/runtime restore"
    if [[ -n "$NEW_PID" ]] && kill -0 "$NEW_PID" 2>/dev/null; then
      kill -TERM "$NEW_PID" 2>/dev/null
      for _ in {1..30}; do
        kill -0 "$NEW_PID" 2>/dev/null || break
        sleep 1
      done
    fi
    atomic_install_jar "$BACKUP_DIR/$OLD_JAR_NAME" "$API_LIVE_JAR" "$RESTORE_STAGE_JAR"
    launch_api_runtime "$LAUNCH_LOG.restore" "$BACKUP_DIR/restored.pid"
    local restored_pid="$(cat -- "$BACKUP_DIR/restored.pid")"
    if wait_for_health "$API_HEALTH_URL" "$API_HEALTH_REGEX" "$API_HEALTH_TIMEOUT"; then
      printf '%s\n' "$restored_pid" > "$API_PID_FILE"
      log "automatic API restore health check PASS; restored_pid=$restored_pid"
    else
      log "CRITICAL: automatic API restore health check failed"
    fi
  fi
  rm -f -- "$STAGE_JAR" "$RESTORE_STAGE_JAR" "$DEPLOY_RECORD_COMPLETE_TEMP"
  exit "$exit_code"
}
trap restore_old_on_error EXIT

mkdir -p -- "$API_BACKUP_ROOT" "$API_RECORD_ROOT" "$API_WORK_DIR/logs"
assert_not_symlink "API backup root" "$API_BACKUP_ROOT"
assert_not_symlink "API record root" "$API_RECORD_ROOT"
mapfile -t CAPTURE < <(capture_api_runtime "$API_LIVE_JAR" "$OLD_PID" "$BACKUP_DIR")
((${#CAPTURE[@]} == 3)) || die "API runtime backup did not return complete evidence"
[[ "${CAPTURE[0]}" == "$OLD_JAR_SHA" && "${CAPTURE[2]}" == "$OLD_TICKS" ]] \
  || die "API runtime changed before backup completed"
OLD_JAR_NAME="${CAPTURE[1]}"

python3 - "$DEPLOY_RECORD" "$CHANGE_ID" "$API_HEAD" "$API_TREE" "$WEB_HEAD" \
  "$WEB_TREE" "$API_ARTIFACT" "$NEW_JAR_SHA" "$API_LIVE_JAR" "$OLD_JAR_SHA" \
  "$BACKUP_DIR" "$OLD_JAR_NAME" "$OLD_ARGV_SHA" "$OLD_PID" "$API_HEALTH_URL" "$STAMP" <<'PY'
import json, sys
(path, change_id, api_head, api_tree, web_head, web_tree, artifact,
 artifact_sha, live_jar, old_jar_sha, backup_dir, backup_jar, argv_sha,
 old_pid, health_url, stamp) = sys.argv[1:]
record = {
  "schema": "cyf-api-deploy-record-v1",
  "status": "PREPARED",
  "changeId": change_id,
  "apiHead": api_head, "apiTree": api_tree,
  "webHead": web_head, "webTree": web_tree,
  "artifact": artifact, "artifactSha256": artifact_sha,
  "liveJar": live_jar, "previousLiveJarSha256": old_jar_sha,
  "backupDir": backup_dir, "backupJar": backup_jar,
  "savedArgvSha256": argv_sha, "oldPid": int(old_pid),
  "healthUrl": health_url, "preparedAt": stamp,
  "databaseOperation": "NOT_PERFORMED", "rabbitMqOperation": "NOT_PERFORMED"
}
with open(path, 'x', encoding='utf-8') as stream:
    json.dump(record, stream, sort_keys=True, indent=2); stream.write("\n")
PY
chmod 0600 "$DEPLOY_RECORD"

stop_process "$OLD_PID" "$OLD_TICKS" "$API_STOP_TIMEOUT"
DEPLOY_CHANGED=1
atomic_install_jar "$API_ARTIFACT" "$API_LIVE_JAR" "$STAGE_JAR"
[[ "$(artifact_sha256 "$API_LIVE_JAR")" == "$NEW_JAR_SHA" ]] || die "installed API JAR checksum mismatch"
launch_api_runtime "$LAUNCH_LOG" "$NEW_PID_FILE"
NEW_PID="$(cat -- "$NEW_PID_FILE")"
[[ "$NEW_PID" =~ ^[0-9]+$ ]] || die "new API PID is invalid"
sleep 2
kill -0 "$NEW_PID" 2>/dev/null || die "new API process exited before health check"
[[ "$(find_single_java_jar_pid "$API_LIVE_JAR")" == "$NEW_PID" ]] \
  || die "new API process identity is ambiguous"
wait_for_health "$API_HEALTH_URL" "$API_HEALTH_REGEX" "$API_HEALTH_TIMEOUT" \
  || die "new API failed the configured health check"
PID_TEMP="$(mktemp "$(dirname -- "$API_PID_FILE")/.tmp.$(basename -- "$API_PID_FILE").XXXXXX")"
printf '%s\n' "$NEW_PID" > "$PID_TEMP"
chmod 0644 "$PID_TEMP"
mv -fT -- "$PID_TEMP" "$API_PID_FILE"

python3 - "$DEPLOY_RECORD" "$DEPLOY_RECORD_COMPLETE_TEMP" "$NEW_PID" <<'PY'
import json, os, sys
path, temporary, pid = sys.argv[1:]
with open(path, 'r', encoding='utf-8') as stream:
    record = json.load(stream)
record['status'] = 'DEPLOYED_HEALTHY'
record['newPid'] = int(pid)
record['completedAt'] = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
with open(temporary, 'x', encoding='utf-8') as stream:
    json.dump(record, stream, sort_keys=True, indent=2); stream.write('\n')
    stream.flush(); os.fsync(stream.fileno())
os.chmod(temporary, 0o600)
os.replace(temporary, path)
directory = os.open(os.path.dirname(path), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
try:
    os.fsync(directory)
finally:
    os.close(directory)
PY
chmod 0444 "$DEPLOY_RECORD"
write_sha256_sidecar "$DEPLOY_RECORD" >/dev/null
trap - EXIT
DEPLOY_CHANGED=0
printf 'DEPLOY_API=PASS\nPID=%s\nBACKUP_DIR=%s\nDEPLOY_RECORD=%s\nARTIFACT_SHA256=%s\n' \
  "$NEW_PID" "$BACKUP_DIR" "$DEPLOY_RECORD" "$NEW_JAR_SHA"
