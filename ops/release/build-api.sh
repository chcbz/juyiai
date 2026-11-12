#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: build-api.sh [--input PATH]

Builds the exact clean API candidate with Gradle serialized by
/tmp/cyf-gradle.lock, then publishes an immutable full-SHA-named JAR,
SHA-256 sidecar, and audit metadata. This script never updates Git refs.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
(( EXECUTE == 0 )) || die "build-api.sh does not accept --execute"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 0)) || die "unexpected positional arguments"

for command in git python3 sha256sum flock jar realpath df awk stat mktemp sync bash java grep; do
  require_command "$command"
done
load_release_input "$INPUT_FILE"
assert_clean_candidate "API" "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
assert_disk_gate "$API_REPO" "API build worktree"
assert_disk_gate "$ARTIFACT_ROOT" "release artifact root"

GRADLEW="$API_REPO/gradlew"
[[ -f "$GRADLEW" && ! -L "$GRADLEW" ]] || die "candidate Gradle wrapper is unavailable or symlinked: $GRADLEW"
log "building API candidate head=$API_HEAD tree=$API_TREE ref=$API_REF"
(
  cd -- "$API_REPO"
  flock -w 600 -x "$CYF_GRADLE_LOCK" bash "$GRADLEW" \
    :starter:clean "$API_GRADLE_TASK" \
    --no-daemon --max-workers=1 --no-build-cache \
    -Dorg.gradle.jvmargs='-Xmx384m -Dfile.encoding=UTF-8' \
    -PrepoUsername=unused -PrepoPassword=unused
)

assert_clean_candidate "API after build" "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
BUILT_JAR="$API_REPO/$API_JAR_RELATIVE_PATH"
[[ -s "$BUILT_JAR" && -f "$BUILT_JAR" && ! -L "$BUILT_JAR" ]] \
  || die "expected API JAR was not produced: $BUILT_JAR"
jar tf "$BUILT_JAR" | grep -Fx 'META-INF/MANIFEST.MF' >/dev/null \
  || die "API artifact has no JAR manifest"
jar tf "$BUILT_JAR" | grep -q '^BOOT-INF/classes/' \
  || die "API artifact is not a Spring Boot executable JAR"

SOURCE_EPOCH="$(release_repo_git "$API_REPO" show -s --format=%ct "$API_HEAD")"
TOOL_SHA="$(release_tool_digest)"
INPUT_SHA="$(artifact_sha256 "$RELEASE_INPUT")"
JAVA_VERSION="$(java -version 2>&1 | head -1)"
GRADLE_DISTRIBUTION_URL="$(grep '^distributionUrl=' "$API_REPO/gradle/wrapper/gradle-wrapper.properties" | cut -d= -f2-)"
API_ARTIFACT_SHA="$(artifact_sha256 "$BUILT_JAR")"
API_METADATA="${API_ARTIFACT}.json"
mkdir -p -- "$(dirname -- "$API_METADATA")"
TEMP_METADATA="$(mktemp "$(dirname -- "$API_METADATA")/.source.$(basename -- "$API_METADATA").XXXXXX")"
python3 - "$TEMP_METADATA" "$RELEASE_ID" "$SOURCE_EPOCH" "$API_REF" \
  "$API_HEAD" "$API_TREE" "$API_ARTIFACT_BASENAME" "$API_ARTIFACT_SHA" \
  "$BUILT_JAR" "$API_GRADLE_TASK" "$CYF_GRADLE_LOCK" "$INPUT_SHA" "$TOOL_SHA" \
  "$JAVA_VERSION" "$GRADLE_DISTRIBUTION_URL" <<'PY'
import json, os, sys
(path, release_id, source_epoch, source_ref, source_head, source_tree,
 artifact_name, artifact_sha, artifact_path, gradle_task, gradle_lock,
 input_sha, tool_sha, java_version, gradle_distribution_url) = sys.argv[1:]
record = {
    "schema": "cyf-api-artifact-v1",
    "releaseId": release_id,
    "recordedAtSourceEpoch": int(source_epoch),
    "sourceCommitEpoch": int(source_epoch),
    "sourceRef": source_ref,
    "sourceHead": source_head,
    "sourceTree": source_tree,
    "artifact": artifact_name,
    "artifactSha256": artifact_sha,
    "artifactBytes": os.path.getsize(artifact_path),
    "gradleTask": gradle_task,
    "gradleLock": gradle_lock,
    "releaseInputSha256": input_sha,
    "releaseToolSha256": tool_sha,
    "javaVersion": java_version,
    "gradleWrapperDistributionUrl": gradle_distribution_url,
    "buildCommand": ":starter:clean " + gradle_task + " --no-daemon --max-workers=1 --no-build-cache -Dorg.gradle.jvmargs=-Xmx384m -Dfile.encoding=UTF-8 -PrepoUsername=unused -PrepoPassword=unused",
    "gradleJvmArgs": "-Xmx384m -Dfile.encoding=UTF-8",
    "publicationCredentials": "NONPUBLISHING_DUMMY"
}
with open(path, 'w', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
PY
chmod 0444 "$TEMP_METADATA"
install_immutable_file "$BUILT_JAR" "$API_ARTIFACT" 0444
[[ "$(write_sha256_sidecar "$API_ARTIFACT")" == "$API_ARTIFACT_SHA" ]] \
  || die "published API artifact digest changed after metadata preparation"
install_immutable_file "$TEMP_METADATA" "$API_METADATA" 0444
rm -f -- "$TEMP_METADATA"
write_sha256_sidecar "$API_METADATA" >/dev/null

log "API artifact published: $API_ARTIFACT"
printf 'API_HEAD=%s\nAPI_TREE=%s\nAPI_ARTIFACT=%s\nAPI_ARTIFACT_SHA256=%s\n' \
  "$API_HEAD" "$API_TREE" "$API_ARTIFACT" "$API_ARTIFACT_SHA"
