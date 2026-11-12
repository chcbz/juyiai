#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: rollback-api.sh [--input PATH] [--dry-run|--execute] DEPLOY_RECORD.json

Default is read-only dry-run. Execution requires the same SHA-bound approval
variables as deploy-api.sh. The deploy record, old JAR, exact argv backup and
all SHA-256 sidecars are verified before rollback. The current release is also
backed up so a failed rollback can be reversed.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 1)) || die "one API deploy record path is required"
for command in git python3 sha256sum curl realpath stat cp mv flock nohup mktemp sync; do require_command "$command"; done
load_release_input "$INPUT_FILE"
require_execute_approval
print_mode
acquire_execution_lock api
verify_release_record_component api

API_LIVE_JAR="$(normalize_absolute_path 'API live JAR' "$(json_get "$RELEASE_INPUT" api.deploy.liveJar)")"
API_PID_FILE="$(normalize_absolute_path 'API PID file' "$(json_get "$RELEASE_INPUT" api.deploy.pidFile)")"
API_WORK_DIR="$(normalize_absolute_path 'API work directory' "$(json_get "$RELEASE_INPUT" api.deploy.workDir)")"
API_BACKUP_ROOT="$(normalize_absolute_path 'API backup root' "$(json_get "$RELEASE_INPUT" api.deploy.backupRoot)")"
API_RECORD_ROOT="$(normalize_absolute_path 'API record root' "$(json_get "$RELEASE_INPUT" api.deploy.recordRoot)")"
API_HEALTH_URL="$(json_get "$RELEASE_INPUT" api.deploy.healthUrl)"
API_HEALTH_REGEX="$(json_get "$RELEASE_INPUT" api.deploy.healthExpectedRegex)"
API_STOP_TIMEOUT="$(json_get "$RELEASE_INPUT" api.deploy.stopTimeoutSeconds)"
API_HEALTH_TIMEOUT="$(json_get "$RELEASE_INPUT" api.deploy.healthTimeoutSeconds)"
DEPLOY_RECORD="$(normalize_absolute_path 'API deploy record' "${POSITIONAL[0]}")"
assert_path_within "API deploy record" "$DEPLOY_RECORD" "$API_RECORD_ROOT"
[[ -f "$DEPLOY_RECORD" && ! -L "$DEPLOY_RECORD" ]] || die "API deploy record is unavailable or symlinked"
verify_sha256_sidecar "$DEPLOY_RECORD"
assert_mode_0444 "API deploy record" "$DEPLOY_RECORD"
assert_mode_0444 "API deploy record checksum" "${DEPLOY_RECORD}.sha256"

BACKUP_DIR="$(normalize_absolute_path 'API backup directory' "$(json_get "$DEPLOY_RECORD" backupDir)")"
BACKUP_JAR_NAME="$(json_get "$DEPLOY_RECORD" backupJar)"
EXPECTED_CURRENT_SHA="$(json_get "$DEPLOY_RECORD" artifactSha256)"
EXPECTED_OLD_SHA="$(json_get "$DEPLOY_RECORD" previousLiveJarSha256)"
EXPECTED_OLD_ARGV_SHA="$(json_get "$DEPLOY_RECORD" savedArgvSha256)"
RECORD_STATUS="$(json_get "$DEPLOY_RECORD" status)"
RECORD_CHANGE_ID="$(json_get "$DEPLOY_RECORD" changeId)"
RECORD_API_HEAD="$(json_get "$DEPLOY_RECORD" apiHead)"
RECORD_API_TREE="$(json_get "$DEPLOY_RECORD" apiTree)"
RECORD_WEB_HEAD="$(json_get "$DEPLOY_RECORD" webHead)"
RECORD_WEB_TREE="$(json_get "$DEPLOY_RECORD" webTree)"
require_sha256 "deployed API artifact" "$EXPECTED_CURRENT_SHA"
require_sha256 "old API artifact" "$EXPECTED_OLD_SHA"
require_sha256 "saved API argv" "$EXPECTED_OLD_ARGV_SHA"
[[ "$EXPECTED_CURRENT_SHA" == "$(artifact_sha256 "$API_ARTIFACT")" ]] \
  || die "API deploy record artifact does not match the verified release artifact"
[[ "$RECORD_STATUS" == "DEPLOYED_HEALTHY" ]] || die "API deploy record is not a healthy deployment"
require_safe_id "API deploy record changeId" "$RECORD_CHANGE_ID"
if (( EXECUTE == 1 )); then
  [[ "$CYF_RELEASE_APPROVAL_ID" == "$RECORD_CHANGE_ID" ]] \
    || die "rollback approval ID must match the original deploy record changeId"
fi
[[ "$RECORD_API_HEAD" == "$API_HEAD" && "$RECORD_API_TREE" == "$API_TREE" ]] \
  || die "API deploy record does not match the pinned candidate"
[[ "$RECORD_WEB_HEAD" == "$WEB_HEAD" && "$RECORD_WEB_TREE" == "$WEB_TREE" ]] \
  || die "API deploy record does not match the jointly verified Web candidate"
assert_path_within "API backup directory" "$BACKUP_DIR" "$API_BACKUP_ROOT"
[[ -d "$BACKUP_DIR" && ! -L "$BACKUP_DIR" ]] || die "API backup directory is unavailable or symlinked"
[[ "$BACKUP_JAR_NAME" =~ ^cyf-api-old-[0-9a-f]{64}\.jar$ ]] || die "API backup JAR name is invalid"
OLD_JAR="$BACKUP_DIR/$BACKUP_JAR_NAME"
[[ -f "$OLD_JAR" && ! -L "$OLD_JAR" ]] || die "old API JAR backup is unavailable"
verify_sha256_sidecar "$OLD_JAR"
verify_sha256_sidecar "$BACKUP_DIR/old.argv.nul"
verify_sha256_sidecar "$BACKUP_DIR/old.cwd"
verify_sha256_sidecar "$BACKUP_DIR/old.exe"
verify_sha256_sidecar "$BACKUP_DIR/old.pid"
verify_sha256_sidecar "$BACKUP_DIR/old.start-ticks"
[[ "$(artifact_sha256 "$OLD_JAR")" == "$EXPECTED_OLD_SHA" ]] || die "old API JAR does not match deploy record"
[[ "$(artifact_sha256 "$BACKUP_DIR/old.argv.nul")" == "$EXPECTED_OLD_ARGV_SHA" ]] \
  || die "saved API argv does not match deploy record"
[[ "$(artifact_sha256 "$API_LIVE_JAR")" == "$EXPECTED_CURRENT_SHA" ]] \
  || die "current API JAR does not match the deployment being rolled back"
[[ "$API_STOP_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ && "$API_HEALTH_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ ]] \
  || die "API timeout configuration is invalid"
[[ "$API_HEALTH_URL" =~ ^https?://[^[:space:]]+$ ]] || die "API health URL is invalid"
[[ -d "$API_WORK_DIR" && ! -L "$API_WORK_DIR" ]] || die "API work directory is unavailable or symlinked"
[[ -f "$API_LIVE_JAR" && ! -L "$API_LIVE_JAR" ]] || die "live API JAR is unavailable or symlinked"
assert_path_within "API live JAR" "$API_LIVE_JAR" "$API_WORK_DIR"
assert_path_within "API PID file" "$API_PID_FILE" "$API_WORK_DIR"
API_LOG_DIR="$(normalize_absolute_path 'API log directory' "$API_WORK_DIR/logs")"
assert_path_within "API log directory" "$API_LOG_DIR" "$API_WORK_DIR"
assert_disk_gate "$API_WORK_DIR" "API rollback filesystem"
assert_disk_gate "$API_BACKUP_ROOT" "API rollback backup filesystem"

CURRENT_PID="$(find_single_java_jar_pid "$API_LIVE_JAR")"
CURRENT_TICKS="$(process_start_ticks "$CURRENT_PID")"
CURRENT_ARGV_SHA="$(proc_argv_sha256 "$CURRENT_PID")"
log "API rollback dry-run evidence: pid=$CURRENT_PID current_sha256=$EXPECTED_CURRENT_SHA old_sha256=$EXPECTED_OLD_SHA argv_sha256=$CURRENT_ARGV_SHA"
if (( EXECUTE == 0 )); then
  printf 'DRY_RUN=PASS\nCOMPONENT=api-rollback\nCURRENT_PID=%s\nCURRENT_SHA256=%s\nRESTORE_SHA256=%s\n' \
    "$CURRENT_PID" "$EXPECTED_CURRENT_SHA" "$EXPECTED_OLD_SHA"
  exit 0
fi

mkdir -p -- "$API_LOG_DIR"
assert_not_symlink "API log directory" "$API_LOG_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CHANGE_ID="$CYF_RELEASE_APPROVAL_ID"
RESCUE_DIR="$API_BACKUP_ROOT/api-rescue-${STAMP}-${API_HEAD}-${API_TREE}-${CHANGE_ID}"
ROLLBACK_RECORD="$API_RECORD_ROOT/api-rollback-${STAMP}-${API_HEAD}-${API_TREE}-${CHANGE_ID}.json"
STAGE_JAR="$(dirname -- "$API_LIVE_JAR")/.cyf-api-rollback-stage-${CHANGE_ID}.jar"
RESCUE_STAGE_JAR="$(dirname -- "$API_LIVE_JAR")/.cyf-api-rescue-stage-${API_HEAD}-${API_TREE}-${CHANGE_ID}.jar"
ROLLBACK_LOG="$API_LOG_DIR/rollback-${STAMP}-${API_HEAD}-${CHANGE_ID}.log"
RESTORED_PID=""
ROLLBACK_CHANGED=0
RESCUE_JAR_NAME=""

[[ ! -e "$RESCUE_DIR" && ! -L "$RESCUE_DIR" ]] || die "API rescue backup path already exists"
[[ ! -e "$ROLLBACK_RECORD" && ! -L "$ROLLBACK_RECORD" ]] || die "API rollback record path already exists"
[[ ! -e "$STAGE_JAR" && ! -L "$STAGE_JAR" ]] || die "API rollback staging path already exists"
[[ ! -e "$RESCUE_STAGE_JAR" && ! -L "$RESCUE_STAGE_JAR" ]] || die "API rescue staging path already exists"

restore_candidate_on_error() {
  local exit_code=$?
  trap - EXIT
  set +e
  if (( ROLLBACK_CHANGED == 1 )); then
    log "rollback failed; attempting to restore the pre-rollback API candidate"
    if [[ -n "$RESTORED_PID" ]] && kill -0 "$RESTORED_PID" 2>/dev/null; then
      kill -TERM "$RESTORED_PID" 2>/dev/null
      for _ in {1..30}; do kill -0 "$RESTORED_PID" 2>/dev/null || break; sleep 1; done
    fi
    atomic_install_jar "$RESCUE_DIR/$RESCUE_JAR_NAME" "$API_LIVE_JAR" "$RESCUE_STAGE_JAR"
    launch_from_argv_backup "$RESCUE_DIR/old.argv.nul" "$RESCUE_DIR/old.cwd" \
      "$API_LIVE_JAR" "$ROLLBACK_LOG.rescue" "$RESCUE_DIR/rescued.pid"
    local rescued_pid="$(cat -- "$RESCUE_DIR/rescued.pid")"
    if wait_for_health "$API_HEALTH_URL" "$API_HEALTH_REGEX" "$API_HEALTH_TIMEOUT"; then
      printf '%s\n' "$rescued_pid" > "$API_PID_FILE"
      log "pre-rollback API candidate restored; pid=$rescued_pid"
    else
      log "CRITICAL: pre-rollback API candidate restore health check failed"
    fi
  fi
  rm -f -- "$STAGE_JAR" "$RESCUE_STAGE_JAR"
  exit "$exit_code"
}
trap restore_candidate_on_error EXIT

mapfile -t RESCUE_CAPTURE < <(capture_api_runtime "$API_LIVE_JAR" "$CURRENT_PID" "$RESCUE_DIR")
((${#RESCUE_CAPTURE[@]} == 3)) || die "API rescue backup did not return complete evidence"
[[ "${RESCUE_CAPTURE[0]}" == "$EXPECTED_CURRENT_SHA" && "${RESCUE_CAPTURE[2]}" == "$CURRENT_TICKS" ]] \
  || die "current API runtime changed before rescue backup completed"
RESCUE_JAR_NAME="${RESCUE_CAPTURE[1]}"

stop_process "$CURRENT_PID" "$CURRENT_TICKS" "$API_STOP_TIMEOUT"
ROLLBACK_CHANGED=1
atomic_install_jar "$OLD_JAR" "$API_LIVE_JAR" "$STAGE_JAR"
[[ "$(artifact_sha256 "$API_LIVE_JAR")" == "$EXPECTED_OLD_SHA" ]] || die "restored API JAR checksum mismatch"
launch_from_argv_backup "$BACKUP_DIR/old.argv.nul" "$BACKUP_DIR/old.cwd" \
  "$API_LIVE_JAR" "$ROLLBACK_LOG" "$BACKUP_DIR/rollback.pid"
RESTORED_PID="$(cat -- "$BACKUP_DIR/rollback.pid")"
sleep 2
kill -0 "$RESTORED_PID" 2>/dev/null || die "rolled-back API exited before health check"
[[ "$(find_single_java_jar_pid "$API_LIVE_JAR")" == "$RESTORED_PID" ]] || die "rolled-back API process identity is ambiguous"
wait_for_health "$API_HEALTH_URL" "$API_HEALTH_REGEX" "$API_HEALTH_TIMEOUT" \
  || die "rolled-back API failed the configured health check"
PID_TEMP="$(mktemp "$(dirname -- "$API_PID_FILE")/.tmp.$(basename -- "$API_PID_FILE").XXXXXX")"
printf '%s\n' "$RESTORED_PID" > "$PID_TEMP"
chmod 0644 "$PID_TEMP"
mv -fT -- "$PID_TEMP" "$API_PID_FILE"

python3 - "$ROLLBACK_RECORD" "$CHANGE_ID" "$API_HEAD" "$API_TREE" \
  "$DEPLOY_RECORD" "$EXPECTED_OLD_SHA" "$EXPECTED_CURRENT_SHA" "$BACKUP_DIR" \
  "$RESCUE_DIR" "$RESTORED_PID" <<'PY'
import datetime, json
import sys
(path, change_id, api_head, api_tree, deploy_record, restored_sha,
 replaced_sha, original_backup, rescue_backup, restored_pid) = sys.argv[1:]
record = {
  "schema": "cyf-api-rollback-record-v1", "status": "ROLLED_BACK_HEALTHY",
  "changeId": change_id, "completedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "apiHead": api_head, "apiTree": api_tree,
  "rolledBackDeployRecord": deploy_record,
  "restoredJarSha256": restored_sha, "replacedJarSha256": replaced_sha,
  "originalBackupDir": original_backup, "rescueBackupDir": rescue_backup,
  "restoredPid": int(restored_pid),
  "databaseOperation": "NOT_PERFORMED", "rabbitMqOperation": "NOT_PERFORMED"
}
with open(path, 'x', encoding='utf-8') as stream:
    json.dump(record, stream, sort_keys=True, indent=2); stream.write("\n")
PY
chmod 0444 "$ROLLBACK_RECORD"
write_sha256_sidecar "$ROLLBACK_RECORD" >/dev/null
trap - EXIT
ROLLBACK_CHANGED=0
printf 'ROLLBACK_API=PASS\nPID=%s\nRESTORED_SHA256=%s\nRESCUE_DIR=%s\nROLLBACK_RECORD=%s\n' \
  "$RESTORED_PID" "$EXPECTED_OLD_SHA" "$RESCUE_DIR" "$ROLLBACK_RECORD"
