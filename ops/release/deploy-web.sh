#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: deploy-web.sh [--input PATH] [--dry-run|--execute]

Default is read-only dry-run. --execute requires the six CYF_RELEASE_APPROVED*
variables documented by deploy-api.sh. The verified archive is extracted into
a sibling staging directory, checked, and activated by same-filesystem rename.
The current physical kit directory is atomically moved to a checksummed backup.
No database or RabbitMQ operation is performed.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 0)) || die "unexpected positional arguments"
for command in git python3 sha256sum curl realpath stat tar grep mv flock mktemp sync; do require_command "$command"; done
load_release_input "$INPUT_FILE"
require_execute_approval
print_mode
acquire_execution_lock web
assert_clean_candidate "Web" "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"
verify_release_record
validate_web_archive "$WEB_ARTIFACT"

WEB_LIVE_DIR="$(normalize_absolute_path 'Web live directory' "$(json_get "$RELEASE_INPUT" web.deploy.liveDir)")"
WEB_BACKUP_ROOT="$(normalize_absolute_path 'Web backup root' "$(json_get "$RELEASE_INPUT" web.deploy.backupRoot)")"
WEB_RECORD_ROOT="$(normalize_absolute_path 'Web record root' "$(json_get "$RELEASE_INPUT" web.deploy.recordRoot)")"
WEB_HEALTH_TIMEOUT="$(json_get "$RELEASE_INPUT" web.deploy.healthTimeoutSeconds)"
mapfile -t WEB_HEALTH_URLS < <(json_array_lines "$RELEASE_INPUT" web.deploy.healthUrls)
[[ "$WEB_HEALTH_TIMEOUT" =~ ^[1-9][0-9]{0,3}$ ]] || die "Web health timeout is invalid"
for url in "${WEB_HEALTH_URLS[@]}"; do
  [[ "$url" =~ ^https://[^[:space:]]+$ ]] || die "Web health URL must use HTTPS: $url"
done
[[ -d "$WEB_LIVE_DIR" && ! -L "$WEB_LIVE_DIR" ]] \
  || die "live Web kit must be one physical directory: $WEB_LIVE_DIR"
WEB_LIVE_PARENT="$(dirname -- "$WEB_LIVE_DIR")"
[[ -d "$WEB_LIVE_PARENT" && ! -L "$WEB_LIVE_PARENT" ]] || die "Web live parent is unavailable or symlinked"
assert_path_within "Web backup root" "$WEB_BACKUP_ROOT" "$WEB_LIVE_PARENT"
assert_path_within "Web record root" "$WEB_RECORD_ROOT" "$WEB_BACKUP_ROOT"
assert_disk_gate "$WEB_LIVE_PARENT" "Web deploy filesystem"
assert_disk_gate "$WEB_BACKUP_ROOT" "Web backup filesystem"

CURRENT_TREE_SHA="$(hash_tree "$WEB_LIVE_DIR")"
CANDIDATE_TREE_SHA="$(json_get "${WEB_ARTIFACT}.json" distTreeSha256)"
require_sha256 "web dist tree" "$CANDIDATE_TREE_SHA"
ARCHIVE_SHA="$(artifact_sha256 "$WEB_ARTIFACT")"
log "Web dry-run evidence: current_tree_sha256=$CURRENT_TREE_SHA candidate_tree_sha256=$CANDIDATE_TREE_SHA archive_sha256=$ARCHIVE_SHA"

if (( EXECUTE == 0 )); then
  printf 'DRY_RUN=PASS\nCOMPONENT=web\nCURRENT_TREE_SHA256=%s\nCANDIDATE_TREE_SHA256=%s\nARCHIVE_SHA256=%s\n' \
    "$CURRENT_TREE_SHA" "$CANDIDATE_TREE_SHA" "$ARCHIVE_SHA"
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CHANGE_ID="$CYF_RELEASE_APPROVAL_ID"
STAGE_DIR="$WEB_LIVE_PARENT/.kit-stage-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}"
BACKUP_DIR="$WEB_BACKUP_ROOT/kit-backup-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}"
FAILED_DIR="$WEB_BACKUP_ROOT/kit-failed-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}"
DEPLOY_RECORD="$WEB_RECORD_ROOT/web-deploy-${STAMP}-${WEB_HEAD}-${WEB_TREE}-${CHANGE_ID}.json"
BACKED_UP=0
INSTALLED=0

restore_web_on_error() {
  local exit_code=$?
  trap - EXIT
  set +e
  if (( INSTALLED == 1 )) && [[ -d "$WEB_LIVE_DIR" && ! -e "$FAILED_DIR" ]]; then
    mv -T -- "$WEB_LIVE_DIR" "$FAILED_DIR"
  fi
  if (( BACKED_UP == 1 )) && [[ -d "$BACKUP_DIR" && ! -e "$WEB_LIVE_DIR" ]]; then
    mv -T -- "$BACKUP_DIR" "$WEB_LIVE_DIR"
    if restored_entry="$(verify_web_health "$WEB_LIVE_DIR" "$WEB_HEALTH_TIMEOUT" "${WEB_HEALTH_URLS[@]}")"; then
      log "automatic Web restore health check PASS: entry_asset=$restored_entry"
    else
      log "CRITICAL: automatic Web restore health check failed"
    fi
  fi
  [[ ! -e "$STAGE_DIR" ]] || rm -rf --one-file-system -- "$STAGE_DIR"
  exit "$exit_code"
}
trap restore_web_on_error EXIT

mkdir -p -- "$WEB_BACKUP_ROOT" "$WEB_RECORD_ROOT"
assert_not_symlink "Web backup root" "$WEB_BACKUP_ROOT"
assert_not_symlink "Web record root" "$WEB_RECORD_ROOT"
[[ "$(stat -c %d -- "$WEB_LIVE_PARENT")" == "$(stat -c %d -- "$WEB_BACKUP_ROOT")" ]] \
  || die "Web live, staging and backup paths must share one filesystem"
[[ ! -e "$STAGE_DIR" && ! -e "$BACKUP_DIR" && ! -e "$FAILED_DIR" && ! -e "$DEPLOY_RECORD" ]] \
  || die "Web staging or backup path already exists"
mkdir -- "$STAGE_DIR"
tar -xzf "$WEB_ARTIFACT" --no-same-owner --no-same-permissions -C "$STAGE_DIR"
find "$STAGE_DIR" -type d -exec chmod 0755 {} +
find "$STAGE_DIR" -type f -exec chmod 0644 {} +
[[ -f "$STAGE_DIR/index.html" ]] || die "staged Web release has no index.html"
STAGED_TREE_SHA="$(hash_tree "$STAGE_DIR")"
[[ "$STAGED_TREE_SHA" == "$CANDIDATE_TREE_SHA" ]] || die "staged Web tree checksum mismatch"
sync -f "$STAGE_DIR" 2>/dev/null || true

mv -T -- "$WEB_LIVE_DIR" "$BACKUP_DIR"
BACKED_UP=1
[[ "$(hash_tree "$BACKUP_DIR")" == "$CURRENT_TREE_SHA" ]] || die "Web backup tree checksum mismatch"
mv -T -- "$STAGE_DIR" "$WEB_LIVE_DIR"
INSTALLED=1
sync -f "$WEB_LIVE_PARENT" 2>/dev/null || true
[[ "$(hash_tree "$WEB_LIVE_DIR")" == "$CANDIDATE_TREE_SHA" ]] || die "deployed Web tree checksum mismatch"

ENTRY_ASSET="$(verify_web_health "$WEB_LIVE_DIR" "$WEB_HEALTH_TIMEOUT" "${WEB_HEALTH_URLS[@]}")" \
  || die "Web health check failed"

python3 - "$DEPLOY_RECORD" "$CHANGE_ID" "$API_HEAD" "$API_TREE" "$WEB_HEAD" \
  "$WEB_TREE" "$WEB_ARTIFACT" "$ARCHIVE_SHA" "$CANDIDATE_TREE_SHA" \
  "$CURRENT_TREE_SHA" "$WEB_LIVE_DIR" "$BACKUP_DIR" "$ENTRY_ASSET" \
  "${WEB_HEALTH_URLS[@]}" <<'PY'
import datetime, json
import sys
(path, change_id, api_head, api_tree, web_head, web_tree, artifact,
 artifact_sha, candidate_tree_sha, previous_tree_sha, live_dir, backup_dir,
 entry_asset, *health_urls) = sys.argv[1:]
record = {
  "schema": "cyf-web-deploy-record-v1", "status": "DEPLOYED_HEALTHY",
  "changeId": change_id, "completedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "apiHead": api_head, "apiTree": api_tree,
  "webHead": web_head, "webTree": web_tree,
  "artifact": artifact, "artifactSha256": artifact_sha,
  "candidateTreeSha256": candidate_tree_sha,
  "previousLiveTreeSha256": previous_tree_sha,
  "liveDir": live_dir, "backupDir": backup_dir,
  "entryAsset": entry_asset, "healthUrls": health_urls,
  "databaseOperation": "NOT_PERFORMED", "rabbitMqOperation": "NOT_PERFORMED"
}
with open(path, 'x', encoding='utf-8') as stream:
    json.dump(record, stream, sort_keys=True, indent=2); stream.write("\n")
PY
chmod 0444 "$DEPLOY_RECORD"
write_sha256_sidecar "$DEPLOY_RECORD" >/dev/null
trap - EXIT
BACKED_UP=0
INSTALLED=0
printf 'DEPLOY_WEB=PASS\nBACKUP_DIR=%s\nDEPLOY_RECORD=%s\nTREE_SHA256=%s\nENTRY_ASSET=%s\n' \
  "$BACKUP_DIR" "$DEPLOY_RECORD" "$CANDIDATE_TREE_SHA" "$ENTRY_ASSET"
