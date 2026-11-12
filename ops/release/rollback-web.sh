#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: rollback-web.sh [--input PATH] [--dry-run|--execute] DEPLOY_RECORD.json

Default is read-only dry-run. Execution requires the same SHA-bound approval
variables as deploy-web.sh. The deployment record and both tree hashes are
verified before a same-filesystem staged rollback. The current kit is retained
as a rescue backup and restored automatically if health checks fail.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 1)) || die "one Web deploy record path is required"
for command in git python3 sha256sum curl realpath stat grep mv cp flock mktemp sync; do require_command "$command"; done
load_release_input "$INPUT_FILE"
require_execute_approval
print_mode
acquire_execution_lock web
verify_release_record_component web

WEB_LIVE_DIR="$(normalize_absolute_path 'Web live directory' "$(json_get "$RELEASE_INPUT" web.deploy.liveDir)")"
WEB_BACKUP_ROOT="$(normalize_absolute_path 'Web backup root' "$(json_get "$RELEASE_INPUT" web.deploy.backupRoot)")"
WEB_RECORD_ROOT="$(normalize_absolute_path 'Web record root' "$(json_get "$RELEASE_INPUT" web.deploy.recordRoot)")"
WEB_HEALTH_TIMEOUT="$(json_get "$RELEASE_INPUT" web.deploy.healthTimeoutSeconds)"
mapfile -t WEB_HEALTH_URLS < <(json_array_lines "$RELEASE_INPUT" web.deploy.healthUrls)
DEPLOY_RECORD="$(normalize_absolute_path 'Web deploy record' "${POSITIONAL[0]}")"
assert_path_within "Web deploy record" "$DEPLOY_RECORD" "$WEB_RECORD_ROOT"
[[ -f "$DEPLOY_RECORD" && ! -L "$DEPLOY_RECORD" ]] || die "Web deploy record is unavailable or symlinked"
verify_sha256_sidecar "$DEPLOY_RECORD"
assert_mode_0444 "Web deploy record" "$DEPLOY_RECORD"
assert_mode_0444 "Web deploy record checksum" "${DEPLOY_RECORD}.sha256"

BACKUP_DIR="$(normalize_absolute_path 'Web backup directory' "$(json_get "$DEPLOY_RECORD" backupDir)")"
EXPECTED_CURRENT_TREE="$(json_get "$DEPLOY_RECORD" candidateTreeSha256)"
EXPECTED_OLD_TREE="$(json_get "$DEPLOY_RECORD" previousLiveTreeSha256)"
EXPECTED_ARCHIVE_SHA="$(json_get "$DEPLOY_RECORD" artifactSha256)"
RECORD_STATUS="$(json_get "$DEPLOY_RECORD" status)"
RECORD_CHANGE_ID="$(json_get "$DEPLOY_RECORD" changeId)"
RECORD_API_HEAD="$(json_get "$DEPLOY_RECORD" apiHead)"
RECORD_API_TREE="$(json_get "$DEPLOY_RECORD" apiTree)"
RECORD_WEB_HEAD="$(json_get "$DEPLOY_RECORD" webHead)"
RECORD_WEB_TREE="$(json_get "$DEPLOY_RECORD" webTree)"
require_sha256 "current Web tree" "$EXPECTED_CURRENT_TREE"
require_sha256 "old Web tree" "$EXPECTED_OLD_TREE"
require_sha256 "deployed Web archive" "$EXPECTED_ARCHIVE_SHA"
[[ "$EXPECTED_CURRENT_TREE" == "$(json_get "${WEB_ARTIFACT}.json" distTreeSha256)" ]] \
  || die "Web deploy record tree does not match the verified release artifact"
[[ "$EXPECTED_ARCHIVE_SHA" == "$(artifact_sha256 "$WEB_ARTIFACT")" ]] \
  || die "Web deploy record archive does not match the verified release artifact"
[[ "$RECORD_STATUS" == "DEPLOYED_HEALTHY" ]] || die "Web deploy record is not a healthy deployment"
require_safe_id "Web deploy record changeId" "$RECORD_CHANGE_ID"
if (( EXECUTE == 1 )); then
  [[ "$CYF_RELEASE_APPROVAL_ID" == "$RECORD_CHANGE_ID" ]] \
    || die "rollback approval ID must match the original deploy record changeId"
fi
[[ "$RECORD_API_HEAD" == "$API_HEAD" && "$RECORD_API_TREE" == "$API_TREE" ]] \
  || die "Web deploy record does not match the jointly verified API candidate"
[[ "$RECORD_WEB_HEAD" == "$WEB_HEAD" && "$RECORD_WEB_TREE" == "$WEB_TREE" ]] \
  || die "Web deploy record does not match the pinned candidate"
assert_path_within "Web backup directory" "$BACKUP_DIR" "$WEB_BACKUP_ROOT"
[[ -d "$BACKUP_DIR" && ! -L "$BACKUP_DIR" ]] || die "Web backup directory is unavailable or symlinked"
[[ -d "$WEB_LIVE_DIR" && ! -L "$WEB_LIVE_DIR" ]] || die "live Web kit is unavailable or symlinked"
[[ "$WEB_HEALTH_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ ]] || die "Web health timeout is invalid"
for url in "${WEB_HEALTH_URLS[@]}"; do
  [[ "$url" =~ ^https://[^[:space:]]+$ ]] || die "Web health URL must use HTTPS: $url"
done
[[ "$(hash_tree "$WEB_LIVE_DIR")" == "$EXPECTED_CURRENT_TREE" ]] \
  || die "current Web tree does not match the deployment being rolled back"
[[ "$(hash_tree "$BACKUP_DIR")" == "$EXPECTED_OLD_TREE" ]] \
  || die "Web backup tree checksum mismatch"
WEB_LIVE_PARENT="$(dirname -- "$WEB_LIVE_DIR")"
[[ -d "$WEB_LIVE_PARENT" && ! -L "$WEB_LIVE_PARENT" ]] || die "Web live parent is unavailable or symlinked"
assert_path_within "Web backup root" "$WEB_BACKUP_ROOT" "$WEB_LIVE_PARENT"
assert_path_within "Web record root" "$WEB_RECORD_ROOT" "$WEB_BACKUP_ROOT"
assert_disk_gate "$WEB_LIVE_PARENT" "Web rollback filesystem"
assert_disk_gate "$WEB_BACKUP_ROOT" "Web rollback backup filesystem"
[[ "$(stat -c %d -- "$WEB_LIVE_PARENT")" == "$(stat -c %d -- "$WEB_BACKUP_ROOT")" ]] \
  || die "Web live, staging and backup paths must share one filesystem"

log "Web rollback dry-run evidence: current_tree_sha256=$EXPECTED_CURRENT_TREE restore_tree_sha256=$EXPECTED_OLD_TREE"
if (( EXECUTE == 0 )); then
  printf 'DRY_RUN=PASS\nCOMPONENT=web-rollback\nCURRENT_TREE_SHA256=%s\nRESTORE_TREE_SHA256=%s\nBACKUP_DIR=%s\n' \
    "$EXPECTED_CURRENT_TREE" "$EXPECTED_OLD_TREE" "$BACKUP_DIR"
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CHANGE_ID="$CYF_RELEASE_APPROVAL_ID"
STAGE_DIR="$WEB_LIVE_PARENT/.kit-rollback-stage-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}"
RESCUE_DIR="$WEB_BACKUP_ROOT/kit-rescue-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}"
ROLLBACK_RECORD="$WEB_RECORD_ROOT/web-rollback-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}.json"
CURRENT_MOVED=0
RESTORED_INSTALLED=0

restore_candidate_on_error() {
  local exit_code=$?
  trap - EXIT
  set +e
  if (( RESTORED_INSTALLED == 1 )) && [[ -d "$WEB_LIVE_DIR" ]]; then
    local failed="$WEB_BACKUP_ROOT/kit-rollback-failed-${STAMP}-${WEB_HEAD}-${CHANGE_ID}"
    [[ -e "$failed" ]] || mv -T -- "$WEB_LIVE_DIR" "$failed"
  fi
  if (( CURRENT_MOVED == 1 )) && [[ -d "$RESCUE_DIR" && ! -e "$WEB_LIVE_DIR" ]]; then
    mv -T -- "$RESCUE_DIR" "$WEB_LIVE_DIR"
    if rescued_entry="$(verify_web_health "$WEB_LIVE_DIR" "$WEB_HEALTH_TIMEOUT" "${WEB_HEALTH_URLS[@]}")"; then
      log "pre-rollback Web candidate restore health check PASS: entry_asset=$rescued_entry"
    else
      log "CRITICAL: pre-rollback Web candidate restore health check failed"
    fi
  fi
  [[ ! -e "$STAGE_DIR" ]] || rm -rf --one-file-system -- "$STAGE_DIR"
  exit "$exit_code"
}
trap restore_candidate_on_error EXIT

[[ ! -e "$STAGE_DIR" && ! -e "$RESCUE_DIR" && ! -e "$ROLLBACK_RECORD" ]] \
  || die "Web rollback staging, rescue or record path already exists"
mkdir -- "$STAGE_DIR"
cp -a -- "$BACKUP_DIR/." "$STAGE_DIR/"
[[ "$(hash_tree "$STAGE_DIR")" == "$EXPECTED_OLD_TREE" ]] || die "staged Web rollback checksum mismatch"
sync -f "$STAGE_DIR" 2>/dev/null || true
mv -T -- "$WEB_LIVE_DIR" "$RESCUE_DIR"
CURRENT_MOVED=1
[[ "$(hash_tree "$RESCUE_DIR")" == "$EXPECTED_CURRENT_TREE" ]] || die "Web rescue backup checksum mismatch"
mv -T -- "$STAGE_DIR" "$WEB_LIVE_DIR"
RESTORED_INSTALLED=1
sync -f "$WEB_LIVE_PARENT" 2>/dev/null || true
[[ "$(hash_tree "$WEB_LIVE_DIR")" == "$EXPECTED_OLD_TREE" ]] || die "restored Web tree checksum mismatch"

ENTRY_ASSET="$(verify_web_health "$WEB_LIVE_DIR" "$WEB_HEALTH_TIMEOUT" "${WEB_HEALTH_URLS[@]}")" \
  || die "Web rollback health check failed"

python3 - "$ROLLBACK_RECORD" "$CHANGE_ID" "$WEB_HEAD" "$WEB_TREE" \
  "$DEPLOY_RECORD" "$EXPECTED_OLD_TREE" "$EXPECTED_CURRENT_TREE" "$BACKUP_DIR" \
  "$RESCUE_DIR" "$ENTRY_ASSET" <<'PY'
import datetime, json
import sys
(path, change_id, web_head, web_tree, deploy_record, restored_tree,
 replaced_tree, source_backup, rescue_backup, entry_asset) = sys.argv[1:]
record = {
  "schema": "cyf-web-rollback-record-v1", "status": "ROLLED_BACK_HEALTHY",
  "changeId": change_id, "completedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "webHead": web_head, "webTree": web_tree,
  "rolledBackDeployRecord": deploy_record,
  "restoredTreeSha256": restored_tree, "replacedTreeSha256": replaced_tree,
  "sourceBackupDir": source_backup, "rescueBackupDir": rescue_backup,
  "entryAsset": entry_asset,
  "databaseOperation": "NOT_PERFORMED", "rabbitMqOperation": "NOT_PERFORMED"
}
with open(path, 'x', encoding='utf-8') as stream:
    json.dump(record, stream, sort_keys=True, indent=2); stream.write("\n")
PY
chmod 0444 "$ROLLBACK_RECORD"
write_sha256_sidecar "$ROLLBACK_RECORD" >/dev/null
trap - EXIT
CURRENT_MOVED=0
RESTORED_INSTALLED=0
printf 'ROLLBACK_WEB=PASS\nRESTORED_TREE_SHA256=%s\nRESCUE_DIR=%s\nROLLBACK_RECORD=%s\nENTRY_ASSET=%s\n' \
  "$EXPECTED_OLD_TREE" "$RESCUE_DIR" "$ROLLBACK_RECORD" "$ENTRY_ASSET"
