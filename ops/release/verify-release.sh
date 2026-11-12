#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: verify-release.sh [--input PATH]

Verifies both clean SHA/tree-pinned candidates, immutable artifacts and their
metadata, input-bound profile-specific default-off flags, archive safety, and
release-tool digest. A missing input verificationProfile defaults to m2-default;
archive-h06 selects the frozen archive reader/question checks. An ambient
CYF_RELEASE_VERIFY_PROFILE may only assert the same input-bound value. Unknown
or mismatched profiles fail closed. On success it publishes a deterministic
joint release record plus SHA-256.
USAGE
}

SHOW_HELP=0
parse_common_args "$@"
(( EXECUTE == 0 )) || die "verify-release.sh does not accept --execute"
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
((${#POSITIONAL[@]} == 0)) || die "unexpected positional arguments"

for command in git python3 sha256sum jar tar grep realpath stat mktemp sync; do
  require_command "$command"
done
load_release_input "$INPUT_FILE"
VERIFY_PROFILE="$RELEASE_VERIFY_PROFILE"
if [[ -n "${CYF_RELEASE_VERIFY_PROFILE+x}" && "$CYF_RELEASE_VERIFY_PROFILE" != "$VERIFY_PROFILE" ]]; then
  die "ambient CYF_RELEASE_VERIFY_PROFILE does not match input verificationProfile: ambient=$CYF_RELEASE_VERIFY_PROFILE input=$VERIFY_PROFILE"
fi
assert_clean_candidate "API" "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
assert_clean_candidate "Web" "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"
verify_sha256_sidecar "$API_ARTIFACT"
verify_sha256_sidecar "$WEB_ARTIFACT"
verify_sha256_sidecar "${API_ARTIFACT}.json"
verify_sha256_sidecar "${WEB_ARTIFACT}.json"
for immutable in "$API_ARTIFACT" "$WEB_ARTIFACT" "${API_ARTIFACT}.json" "${WEB_ARTIFACT}.json" \
  "${API_ARTIFACT}.sha256" "${WEB_ARTIFACT}.sha256" \
  "${API_ARTIFACT}.json.sha256" "${WEB_ARTIFACT}.json.sha256"; do
  assert_mode_0444 "release artifact input" "$immutable"
done
validate_web_archive "$WEB_ARTIFACT"
jar tf "$API_ARTIFACT" | grep -Fx 'META-INF/MANIFEST.MF' >/dev/null \
  || die "API artifact has no JAR manifest"
jar tf "$API_ARTIFACT" | grep -q '^BOOT-INF/classes/' \
  || die "API artifact is not a Spring Boot executable JAR"

API_SHA="$(artifact_sha256 "$API_ARTIFACT")"
WEB_SHA="$(artifact_sha256 "$WEB_ARTIFACT")"
TOOL_SHA="$(release_tool_digest)"
INPUT_SHA="$(artifact_sha256 "$RELEASE_INPUT")"
python3 - "${API_ARTIFACT}.json" "${WEB_ARTIFACT}.json" \
  "$RELEASE_ID" "$API_REF" "$API_HEAD" "$API_TREE" "$API_ARTIFACT_BASENAME" \
  "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$WEB_ARTIFACT_BASENAME" \
  "$API_SHA" "$WEB_SHA" "$TOOL_SHA" "$INPUT_SHA" "$VERIFY_PROFILE" <<'PY'
import json, sys
(am_path, wm_path, release_id, api_ref, ah, at, api_artifact, web_ref, wh,
 wt, web_artifact, artifact_a, artifact_w, tool, input_sha, verify_profile) = sys.argv[1:]
with open(am_path, 'r', encoding='utf-8') as stream:
    api = json.load(stream)
with open(wm_path, 'r', encoding='utf-8') as stream:
    web = json.load(stream)
checks = [
    (api, 'schema', 'cyf-api-artifact-v1'),
    (api, 'releaseId', release_id), (api, 'sourceRef', api_ref),
    (api, 'sourceHead', ah), (api, 'sourceTree', at), (api, 'artifact', api_artifact),
    (api, 'artifactSha256', artifact_a),
    (api, 'releaseToolSha256', tool), (api, 'releaseInputSha256', input_sha),
    (web, 'schema', 'cyf-web-artifact-v1'),
    (web, 'releaseId', release_id), (web, 'sourceRef', web_ref),
    (web, 'sourceHead', wh), (web, 'sourceTree', wt), (web, 'artifact', web_artifact),
    (web, 'artifactSha256', artifact_w),
    (web, 'releaseToolSha256', tool), (web, 'releaseInputSha256', input_sha),
]
for obj, key, expected in checks:
    if obj.get(key) != expected:
        raise SystemExit(f'artifact metadata mismatch for {key}')
if not isinstance(web.get('distTreeSha256'), str) or len(web['distTreeSha256']) != 64:
    raise SystemExit('web metadata has no valid distTreeSha256')
for item in (api, web):
    if 'verificationProfile' in item and item['verificationProfile'] != verify_profile:
        raise SystemExit('artifact metadata verificationProfile mismatch')
PY

verify_exact_git_flag() {
  local repo="$1" head="$2" path="$3" expected="$4" label="$5" count content
  release_repo_git "$repo" cat-file -e "$head:$path" 2>/dev/null || die "$label source is missing from pinned candidate: $path"
  content="$(release_repo_git "$repo" show "$head:$path")" \
    || die "$label could not read pinned candidate source: $path"
  count="$(grep -Fxc "$expected" <<< "$content" || true)"
  [[ "$count" == 1 ]] || die "$label must occur exactly once as $expected: $path"
}

verify_m2_default_flags() {
  # The former task-event/task-workspace declarations were historical feature
  # flags, not release correctness evidence.  They are intentionally not a
  # release gate: source/artifact identity and runtime health remain verified.
  log 'release verification profile=m2-default; no legacy feature-flag gate'
}
verify_archive_h06_flags() {
  local path env_file source_file content grep_status
  local -a reader_profiles=(
    chat/jia-chat-service/src/main/resources/application.properties
    chat/jia-chat-starter/src/main/resources/application-dev.properties
    starter/src/main/resources/application-dev.properties
    starter/src/main/resources/application-grey.properties
    starter/src/main/resources/application-prod.properties
  )
  local -a question_profiles=(
    chat/jia-chat-service/src/main/resources/application.properties
    chat/jia-chat-starter/src/main/resources/application-dev.properties
  )
  for path in "${reader_profiles[@]}"; do
    verify_exact_git_flag "$API_REPO" "$API_HEAD" "$path" 'archive.reader.enabled=false' 'archive reader default-off flag'
  done
  for path in "${question_profiles[@]}"; do
    verify_exact_git_flag "$API_REPO" "$API_HEAD" "$path" 'archive.question.enabled=false' 'archive question default-off flag'
  done
  set +e
  release_repo_git "$API_REPO" grep -n -E '^archive\.(reader|question)\.enabled=true$' "$API_HEAD" -- '*application*.properties' >/dev/null
  grep_status=$?
  set -e
  case "$grep_status" in
    0) die 'pinned API contains an archive reader/question default-true declaration' ;;
    1) ;;
    *) die "pinned API git grep failed while rejecting archive default-true declarations: status=$grep_status" ;;
  esac
  for env_file in .env .env.production; do
    release_repo_git "$WEB_REPO" cat-file -e "$WEB_HEAD:$env_file" 2>/dev/null || die "pinned Web environment file is missing: $env_file"
    content="$(release_repo_git "$WEB_REPO" show "$WEB_HEAD:$env_file")" \
      || die "cannot read pinned Web environment file: $env_file"
    if grep -E '^VITE_[A-Z0-9_]*(ARCHIVE|READER|QUESTION)[A-Z0-9_]*=' <<< "$content" >/dev/null; then
      die "Web production/default environment must not force-enable archive reader/question: $env_file"
    fi
  done
  for source_file in \
    src/components/juyiting/LibraryPanel.vue \
    src/components/juyiting/archive/ArchiveReader.vue \
    src/composables/juyiting/useArchiveReader.js; do
    release_repo_git "$WEB_REPO" cat-file -e "$WEB_HEAD:$source_file" 2>/dev/null || die "pinned Web archive source is missing: $source_file"
    content="$(release_repo_git "$WEB_REPO" show "$WEB_HEAD:$source_file")" \
      || die "cannot read pinned Web archive source: $source_file"
    if grep -E '(import\.meta|process)\.env' <<< "$content" >/dev/null; then
      die "Web archive reader/question source must not be enabled by build environment state: $source_file"
    fi
  done
  verify_exact_git_flag "$WEB_REPO" "$WEB_HEAD" src/components/juyiting/LibraryPanel.vue "import ArchiveReader from './archive/ArchiveReader.vue'" 'Web archive reader composition'
  verify_exact_git_flag "$WEB_REPO" "$WEB_HEAD" src/components/juyiting/LibraryPanel.vue "const activeTab = ref('reader')" 'Web archive reader default tab'
  verify_exact_git_flag "$WEB_REPO" "$WEB_HEAD" src/composables/juyiting/useArchiveReader.js "export const useArchiveReader = ({ api = createApi('/archive/v1'), autoInitialize = true, saveDelay = 800 } = {}) => {" 'Web archive API-backed feature boundary'
  content="$(release_repo_git "$WEB_REPO" show "$WEB_HEAD:src/components/juyiting/LibraryPanel.vue")" \
    || die 'cannot read pinned Web LibraryPanel source for composition count'
  [[ "$(grep -c '<ArchiveReader' <<< "$content" || true)" == 1 ]] \
    || die 'Web archive reader component must be composed exactly once'
  content="$(release_repo_git "$WEB_REPO" show "$WEB_HEAD:src/composables/juyiting/useArchiveReader.js")" \
    || die 'cannot read pinned Web archive composable for question count'
  [[ "$(grep -c 'const createQuestion =' <<< "$content" || true)" == 1 ]] \
    || die 'Web archive question implementation must be present exactly once behind the API boundary'
}

case "$VERIFY_PROFILE" in
  m2-default) verify_m2_default_flags ;;
  archive-h06) log 'release verification profile=archive-h06'; verify_archive_h06_flags ;;
esac

for script in "$CYF_RELEASE_SCRIPT_DIR"/*.sh; do
  if grep -En '(^|[;&|[:space:]])git[[:space:]]+(p[u]ll|f[e]tch|r[e]set|c[h]eckout|s[w]itch|m[e]rge|r[e]base|c[l]ean)([;&|[:space:]]|$)' "$script" >/dev/null; then
    die "release source contains a prohibited Git network update command: $script"
  fi
done
if ! grep -F 'flock -w 600 -x "$CYF_GRADLE_LOCK" bash "$GRADLEW"' \
  "$CYF_RELEASE_SCRIPT_DIR/build-api.sh" >/dev/null; then
  die "API build does not visibly hold the required Gradle lock"
fi

mkdir -p -- "$(dirname -- "$RELEASE_RECORD")"
TEMP_RECORD="$(mktemp "$(dirname -- "$RELEASE_RECORD")/.source.$RELEASE_RECORD_BASENAME.XXXXXX")"
API_SOURCE_EPOCH="$(release_repo_git "$API_REPO" show -s --format=%ct "$API_HEAD")"
WEB_SOURCE_EPOCH="$(release_repo_git "$WEB_REPO" show -s --format=%ct "$WEB_HEAD")"
WEB_DIST_SHA="$(json_get "${WEB_ARTIFACT}.json" distTreeSha256)"
python3 - "$TEMP_RECORD" "$RELEASE_ID" "$API_REF" "$API_HEAD" "$API_TREE" \
  "$API_ARTIFACT_BASENAME" "$API_SHA" "$API_SOURCE_EPOCH" "$WEB_REF" \
  "$WEB_HEAD" "$WEB_TREE" "$WEB_ARTIFACT_BASENAME" "$WEB_SHA" "$WEB_DIST_SHA" \
  "$WEB_SOURCE_EPOCH" "$INPUT_SHA" "$TOOL_SHA" "$VERIFY_PROFILE" <<'PY'
import json, sys
(path, release_id, api_ref, api_head, api_tree, api_artifact, api_sha,
 api_epoch, web_ref, web_head, web_tree, web_artifact, web_sha,
 web_dist_sha, web_epoch, input_sha, tool_sha, verify_profile) = sys.argv[1:]
record = {
    "schema": "cyf-m2-c08-release-record-v1",
    "releaseId": release_id,
    "verification": "PASS",
    "verificationProfile": verify_profile,
    "apiRef": api_ref,
    "apiHead": api_head,
    "apiTree": api_tree,
    "apiArtifact": api_artifact,
    "apiArtifactSha256": api_sha,
    "apiSourceCommitEpoch": int(api_epoch),
    "webRef": web_ref,
    "webHead": web_head,
    "webTree": web_tree,
    "webArtifact": web_artifact,
    "webArtifactSha256": web_sha,
    "webDistTreeSha256": web_dist_sha,
    "webSourceCommitEpoch": int(web_epoch),
    "releaseInputSha256": input_sha,
    "releaseToolSha256": tool_sha,
    "apiFeatureDefault": False,
    "webFeatureDefault": False,
    "productionDatabaseOperation": "NOT_PERFORMED",
    "rabbitMqOperation": "NOT_PERFORMED",
    "deployment": "NOT_PERFORMED"
}
with open(path, 'w', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")
PY
chmod 0444 "$TEMP_RECORD"
install_immutable_file "$TEMP_RECORD" "$RELEASE_RECORD" 0444
rm -f -- "$TEMP_RECORD"
RELEASE_RECORD_SHA="$(write_sha256_sidecar "$RELEASE_RECORD")"

log "joint release verification PASS"
printf 'RELEASE_RECORD=%s\nRELEASE_RECORD_SHA256=%s\nAPI_ARTIFACT_SHA256=%s\nWEB_ARTIFACT_SHA256=%s\n' \
  "$RELEASE_RECORD" "$RELEASE_RECORD_SHA" "$API_SHA" "$WEB_SHA"
