#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# shellcheck source=common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() {
  cat <<'USAGE'
Usage: promote-release.sh --source-input PATH [--input PATH]

Promotes byte-exact immutable API/Web artifacts from a previously attested
release input into a new release input without rebuilding source. The source
and target refs, HEADs, trees, and artifact names must be identical. Source
sidecars, metadata, and the joint release record are validated first. Target
metadata records promotion provenance and current tool/input digests.
No deployment, database, or RabbitMQ operation is performed.
USAGE
}

SOURCE_INPUT_FILE=""
INPUT_FILE="$CYF_RELEASE_DEFAULT_INPUT"
SHOW_HELP=0
while (($#)); do
  case "$1" in
    --source-input)
      (($# >= 2)) || die "--source-input requires a path"
      SOURCE_INPUT_FILE="$2"
      shift 2
      ;;
    --input)
      (($# >= 2)) || die "--input requires a path"
      INPUT_FILE="$2"
      shift 2
      ;;
    --help|-h)
      SHOW_HELP=1
      shift
      ;;
    --execute|--dry-run)
      die "promote-release.sh does not accept deployment mode options"
      ;;
    *) die "unexpected argument: $1" ;;
  esac
done
if (( SHOW_HELP == 1 )); then usage; exit 0; fi
[[ -n "$SOURCE_INPUT_FILE" ]] || die "--source-input is required"

for command in git python3 sha256sum jar tar realpath df awk stat mktemp sync; do
  require_command "$command"
done

load_release_input "$INPUT_FILE"
TARGET_VERIFY_PROFILE="$RELEASE_VERIFY_PROFILE"
assert_clean_candidate "API" "$API_REPO" "$API_REF" "$API_HEAD" "$API_TREE"
assert_clean_candidate "Web" "$WEB_REPO" "$WEB_REF" "$WEB_HEAD" "$WEB_TREE"
assert_disk_gate "$ARTIFACT_ROOT" "target release artifact root"

SOURCE_INPUT="$(normalize_absolute_path 'source release input' "$SOURCE_INPUT_FILE")"
[[ -f "$SOURCE_INPUT" && ! -L "$SOURCE_INPUT" ]] \
  || die "source release input is missing, non-regular, or symlinked: $SOURCE_INPUT"
validate_input_shape "$SOURCE_INPUT" || die "invalid source release input: $SOURCE_INPUT"
SOURCE_VERIFY_PROFILE="$(release_input_verification_profile "$SOURCE_INPUT")"
[[ "$SOURCE_VERIFY_PROFILE" == "$TARGET_VERIFY_PROFILE" ]] \
  || die "source/target verificationProfile mismatch: source=$SOURCE_VERIFY_PROFILE target=$TARGET_VERIFY_PROFILE"
SOURCE_RELEASE_ID="$(json_get "$SOURCE_INPUT" releaseId)"
SOURCE_ARTIFACT_ROOT="$(normalize_absolute_path 'source artifact root' "$(json_get "$SOURCE_INPUT" artifactRoot)")"
[[ "$SOURCE_RELEASE_ID" != "$RELEASE_ID" ]] || die "source and target release IDs must differ"
[[ "$SOURCE_ARTIFACT_ROOT" != "$ARTIFACT_ROOT" ]] || die "source and target artifact roots must differ"

for tuple in \
  "api.ref=$API_REF" "api.head=$API_HEAD" "api.tree=$API_TREE" \
  "web.ref=$WEB_REF" "web.head=$WEB_HEAD" "web.tree=$WEB_TREE"; do
  key="${tuple%%=*}"
  expected="${tuple#*=}"
  [[ "$(json_get "$SOURCE_INPUT" "$key")" == "$expected" ]] \
    || die "source/target candidate mismatch for $key"
done

SOURCE_API_ARTIFACT="$SOURCE_ARTIFACT_ROOT/api/$API_ARTIFACT_BASENAME"
SOURCE_WEB_ARTIFACT="$SOURCE_ARTIFACT_ROOT/web/$WEB_ARTIFACT_BASENAME"
SOURCE_RELEASE_RECORD="$SOURCE_ARTIFACT_ROOT/release/$RELEASE_RECORD_BASENAME"
for path in "$SOURCE_API_ARTIFACT" "$SOURCE_WEB_ARTIFACT" \
  "${SOURCE_API_ARTIFACT}.json" "${SOURCE_WEB_ARTIFACT}.json" "$SOURCE_RELEASE_RECORD"; do
  verify_sha256_sidecar "$path"
  assert_mode_0444 "promotion source" "$path"
  assert_mode_0444 "promotion source checksum" "${path}.sha256"
done
validate_web_archive "$SOURCE_WEB_ARTIFACT"
jar tf "$SOURCE_API_ARTIFACT" | grep -Fx 'META-INF/MANIFEST.MF' >/dev/null \
  || die "source API artifact has no JAR manifest"
jar tf "$SOURCE_API_ARTIFACT" | grep -q '^BOOT-INF/classes/' \
  || die "source API artifact is not a Spring Boot executable JAR"

SOURCE_INPUT_SHA="$(artifact_sha256 "$SOURCE_INPUT")"
SOURCE_RELEASE_RECORD_SHA="$(artifact_sha256 "$SOURCE_RELEASE_RECORD")"
SOURCE_API_METADATA_SHA="$(artifact_sha256 "${SOURCE_API_ARTIFACT}.json")"
SOURCE_WEB_METADATA_SHA="$(artifact_sha256 "${SOURCE_WEB_ARTIFACT}.json")"
SOURCE_API_SHA="$(artifact_sha256 "$SOURCE_API_ARTIFACT")"
SOURCE_WEB_SHA="$(artifact_sha256 "$SOURCE_WEB_ARTIFACT")"
python3 - "$SOURCE_RELEASE_ID" "$SOURCE_INPUT_SHA" \
  "${SOURCE_API_ARTIFACT}.json" "${SOURCE_WEB_ARTIFACT}.json" "$SOURCE_RELEASE_RECORD" \
  "$API_REF" "$API_HEAD" "$API_TREE" "$API_ARTIFACT_BASENAME" "$SOURCE_API_SHA" \
  "$WEB_REF" "$WEB_HEAD" "$WEB_TREE" "$WEB_ARTIFACT_BASENAME" "$SOURCE_WEB_SHA" \
  "$SOURCE_VERIFY_PROFILE" <<'PY'
import json, re, sys
(source_release_id, source_input_sha, api_metadata_path, web_metadata_path,
 release_record_path, api_ref, api_head, api_tree, api_name, api_sha,
 web_ref, web_head, web_tree, web_name, web_sha, verify_profile) = sys.argv[1:]

def load(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SystemExit(f'duplicate JSON key in {path}: {key}')
            result[key] = value
        return result
    with open(path, encoding='utf-8') as stream:
        return json.load(stream, object_pairs_hook=unique_object)

api = load(api_metadata_path)
web = load(web_metadata_path)
record = load(release_record_path)
components = (
    (api, 'cyf-api-artifact-v1', api_ref, api_head, api_tree, api_name, api_sha),
    (web, 'cyf-web-artifact-v1', web_ref, web_head, web_tree, web_name, web_sha),
)
for item, schema, ref, head, tree, name, sha in components:
    expected = {
        'schema': schema, 'releaseId': source_release_id, 'sourceRef': ref,
        'sourceHead': head, 'sourceTree': tree, 'artifact': name,
        'artifactSha256': sha, 'releaseInputSha256': source_input_sha,
    }
    for key, value in expected.items():
        if item.get(key) != value:
            raise SystemExit(f'source artifact metadata mismatch for {key}')
tool_sha = api.get('releaseToolSha256')
if not isinstance(tool_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', tool_sha):
    raise SystemExit('source API metadata has invalid release tool digest')
if web.get('releaseToolSha256') != tool_sha:
    raise SystemExit('source component metadata tool digests differ')
for item in (api, web):
    if 'verificationProfile' in item and item['verificationProfile'] != verify_profile:
        raise SystemExit('source artifact metadata verificationProfile mismatch')
expected_record = {
    'schema': 'cyf-m2-c08-release-record-v1', 'releaseId': source_release_id,
    'verification': 'PASS', 'apiRef': api_ref, 'apiHead': api_head,
    'apiTree': api_tree, 'apiArtifact': api_name, 'apiArtifactSha256': api_sha,
    'webRef': web_ref, 'webHead': web_head, 'webTree': web_tree,
    'webArtifact': web_name, 'webArtifactSha256': web_sha,
    'releaseInputSha256': source_input_sha, 'releaseToolSha256': tool_sha,
    'apiFeatureDefault': False, 'webFeatureDefault': False,
    'productionDatabaseOperation': 'NOT_PERFORMED',
    'rabbitMqOperation': 'NOT_PERFORMED', 'deployment': 'NOT_PERFORMED',
}
for key, value in expected_record.items():
    if record.get(key) != value:
        raise SystemExit(f'source release record mismatch for {key}')
if record.get('verificationProfile', 'm2-default') != verify_profile:
    raise SystemExit('source release record verificationProfile mismatch')
if record.get('webDistTreeSha256') != web.get('distTreeSha256'):
    raise SystemExit('source release record Web tree digest mismatch')
PY

install_immutable_file "$SOURCE_API_ARTIFACT" "$API_ARTIFACT" 0444
write_sha256_sidecar "$API_ARTIFACT" >/dev/null
assert_disk_gate "$ARTIFACT_ROOT" "target release artifact root after API promotion"
install_immutable_file "$SOURCE_WEB_ARTIFACT" "$WEB_ARTIFACT" 0444
write_sha256_sidecar "$WEB_ARTIFACT" >/dev/null
assert_disk_gate "$ARTIFACT_ROOT" "target release artifact root after Web promotion"

TARGET_INPUT_SHA="$(artifact_sha256 "$RELEASE_INPUT")"
TARGET_TOOL_SHA="$(release_tool_digest)"
for component in api web; do
  if [[ "$component" == api ]]; then
    source_metadata="${SOURCE_API_ARTIFACT}.json"
    source_metadata_sha="$SOURCE_API_METADATA_SHA"
    target_metadata="${API_ARTIFACT}.json"
  else
    source_metadata="${SOURCE_WEB_ARTIFACT}.json"
    source_metadata_sha="$SOURCE_WEB_METADATA_SHA"
    target_metadata="${WEB_ARTIFACT}.json"
  fi
  temp_metadata="$(mktemp "$(dirname -- "$target_metadata")/.source.$(basename -- "$target_metadata").XXXXXX")"
  python3 - "$source_metadata" "$temp_metadata" "$RELEASE_ID" "$TARGET_INPUT_SHA" \
    "$TARGET_TOOL_SHA" "$SOURCE_RELEASE_ID" "$SOURCE_INPUT_SHA" \
    "$source_metadata_sha" "$SOURCE_RELEASE_RECORD_SHA" "$TARGET_VERIFY_PROFILE" <<'PY'
import json, sys
(source, target, release_id, input_sha, tool_sha, source_release_id,
 source_input_sha, source_metadata_sha, source_record_sha, verify_profile) = sys.argv[1:]
with open(source, encoding='utf-8') as stream:
    data = json.load(stream)
data['releaseId'] = release_id
data['releaseInputSha256'] = input_sha
data['releaseToolSha256'] = tool_sha
data['verificationProfile'] = verify_profile
data['promotion'] = {
    'method': 'BYTE_EXACT_IMMUTABLE_ARTIFACT_PROMOTION',
    'sourceReleaseId': source_release_id,
    'sourceReleaseInputSha256': source_input_sha,
    'sourceArtifactMetadataSha256': source_metadata_sha,
    'sourceReleaseRecordSha256': source_record_sha,
    'productionDatabaseOperation': 'NOT_PERFORMED',
    'rabbitMqOperation': 'NOT_PERFORMED',
    'deployment': 'NOT_PERFORMED',
}
with open(target, 'w', encoding='utf-8') as stream:
    json.dump(data, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write('\n')
PY
  chmod 0444 "$temp_metadata"
  install_immutable_file "$temp_metadata" "$target_metadata" 0444
  rm -- "$temp_metadata"
  write_sha256_sidecar "$target_metadata" >/dev/null
done

"$CYF_RELEASE_SCRIPT_DIR/verify-release.sh" --input "$RELEASE_INPUT"
log "byte-exact release promotion PASS: source=$SOURCE_RELEASE_ID target=$RELEASE_ID"
printf 'SOURCE_RELEASE_ID=%s\nTARGET_RELEASE_ID=%s\nAPI_ARTIFACT_SHA256=%s\nWEB_ARTIFACT_SHA256=%s\nSOURCE_RELEASE_RECORD_SHA256=%s\n' \
  "$SOURCE_RELEASE_ID" "$RELEASE_ID" "$SOURCE_API_SHA" "$SOURCE_WEB_SHA" "$SOURCE_RELEASE_RECORD_SHA"
