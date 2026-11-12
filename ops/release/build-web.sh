#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: build-web.sh [--input PATH]

Runs npm ci and the production build in the exact clean Web candidate, then
publishes an immutable deterministic full-SHA-named archive, SHA-256 sidecar,
and audit metadata. This script never updates Git refs.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
(( EXECUTE == 0 )) || die "build-web.sh does not accept --execute"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 0)) || die "unexpected positional arguments"

for command in git python3 sha256sum tar gzip realpath df awk stat mktemp sync node; do
  require_command "$command"
done
load_release_input "$INPUT_FILE"
assert_clean_candidate "Web" "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"
assert_disk_gate "$WEB_REPO" "Web build worktree"
assert_disk_gate "$ARTIFACT_ROOT" "release artifact root"
[[ -x "$WEB_NPM_BIN" && ! -L "$WEB_NPM_BIN" ]] \
  || die "pinned npm binary is unavailable or symlinked: $WEB_NPM_BIN"
[[ -f "$WEB_REPO/package-lock.json" && ! -L "$WEB_REPO/package-lock.json" ]] \
  || die "Web package-lock.json is missing or symlinked"

log "building Web candidate head=$WEB_HEAD tree=$WEB_TREE ref=$WEB_REF"
(
  cd -- "$WEB_REPO"
  "$WEB_NPM_BIN" ci --no-audit --no-fund
  "$WEB_NPM_BIN" run build
)
assert_clean_candidate "Web after build" "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"

DIST_DIR="$WEB_REPO/$WEB_DIST_RELATIVE_PATH"
[[ -d "$DIST_DIR" && ! -L "$DIST_DIR" && -f "$DIST_DIR/index.html" ]] \
  || die "Web dist is incomplete or symlinked: $DIST_DIR"
DIST_TREE_SHA="$(hash_tree "$DIST_DIR")"
SOURCE_EPOCH="$(release_repo_git "$WEB_REPO" show -s --format=%ct "$WEB_HEAD")"
TEMP_DIR="$(mktemp -d "$(nearest_existing_path "$ARTIFACT_ROOT")/.cyf-web-build.XXXXXX")"
trap 'rm -rf --one-file-system -- "$TEMP_DIR"' EXIT
TEMP_ARCHIVE="$TEMP_DIR/$WEB_ARTIFACT_BASENAME"
(
  cd -- "$DIST_DIR"
  tar --sort=name --mtime="@$SOURCE_EPOCH" --owner=0 --group=0 --numeric-owner \
    --format=posix --pax-option=delete=atime,delete=ctime -cf - . | gzip -n > "$TEMP_ARCHIVE"
)
validate_web_archive "$TEMP_ARCHIVE"
WEB_ARTIFACT_SHA="$(artifact_sha256 "$TEMP_ARCHIVE")"
WEB_METADATA="${WEB_ARTIFACT}.json"
TEMP_METADATA="$TEMP_DIR/$(basename -- "$WEB_METADATA")"
TOOL_SHA="$(release_tool_digest)"
INPUT_SHA="$(artifact_sha256 "$RELEASE_INPUT")"
PACKAGE_LOCK_SHA="$(artifact_sha256 "$WEB_REPO/package-lock.json")"
NODE_VERSION="$(node --version)"
NPM_VERSION="$("$WEB_NPM_BIN" --version)"
TAR_VERSION="$(tar --version | head -1)"
GZIP_VERSION="$(gzip --version | head -1)"
python3 - "$TEMP_METADATA" "$RELEASE_ID" "$SOURCE_EPOCH" "$WEB_REF" \
  "$WEB_HEAD" "$WEB_TREE" "$WEB_ARTIFACT_BASENAME" "$WEB_ARTIFACT_SHA" \
  "$TEMP_ARCHIVE" "$DIST_TREE_SHA" "$INPUT_SHA" "$TOOL_SHA" \
  "$PACKAGE_LOCK_SHA" "$NODE_VERSION" "$NPM_VERSION" "$TAR_VERSION" "$GZIP_VERSION" <<'PY'
import json, os
(path, release_id, source_epoch, source_ref, source_head, source_tree,
 artifact_name, artifact_sha, artifact_path, dist_tree_sha, input_sha,
 tool_sha, package_lock_sha, node_version, npm_version, tar_version,
 gzip_version) = __import__('sys').argv[1:]
record = {
    "schema": "cyf-web-artifact-v1",
    "releaseId": release_id,
    "recordedAtSourceEpoch": int(source_epoch),
    "sourceCommitEpoch": int(source_epoch),
    "sourceRef": source_ref,
    "sourceHead": source_head,
    "sourceTree": source_tree,
    "artifact": artifact_name,
    "artifactSha256": artifact_sha,
    "artifactBytes": os.path.getsize(artifact_path),
    "distTreeSha256": dist_tree_sha,
    "installCommand": "npm ci --no-audit --no-fund",
    "buildCommand": "npm run build",
    "releaseInputSha256": input_sha,
    "releaseToolSha256": tool_sha,
    "packageLockSha256": package_lock_sha,
    "nodeVersion": node_version,
    "npmVersion": npm_version,
    "tarVersion": tar_version,
    "gzipVersion": gzip_version,
    "archiveCommand": "tar --sort=name --mtime=@SOURCE_EPOCH --owner=0 --group=0 --numeric-owner --format=posix --pax-option=delete=atime,delete=ctime -cf - . | gzip -n"
}
with open(path, 'w', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
PY
chmod 0444 "$TEMP_METADATA"
install_immutable_file "$TEMP_ARCHIVE" "$WEB_ARTIFACT" 0444
[[ "$(write_sha256_sidecar "$WEB_ARTIFACT")" == "$WEB_ARTIFACT_SHA" ]] \
  || die "published Web artifact digest changed after metadata preparation"
install_immutable_file "$TEMP_METADATA" "$WEB_METADATA" 0444
write_sha256_sidecar "$WEB_METADATA" >/dev/null

log "Web artifact published: $WEB_ARTIFACT"
printf 'WEB_HEAD=%s\nWEB_TREE=%s\nWEB_ARTIFACT=%s\nWEB_ARTIFACT_SHA256=%s\nWEB_DIST_TREE_SHA256=%s\n' \
  "$WEB_HEAD" "$WEB_TREE" "$WEB_ARTIFACT" "$WEB_ARTIFACT_SHA" "$DIST_TREE_SHA"
