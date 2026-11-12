#!/usr/bin/env bash
# Shared fail-closed helpers for the CYF SHA-pinned release pipeline.

if [[ -z "${BASH_VERSION:-}" ]]; then
  printf 'ERROR: bash is required\n' >&2
  exit 2
fi

readonly CYF_RELEASE_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly CYF_RELEASE_DEFAULT_INPUT="$CYF_RELEASE_SCRIPT_DIR/m2-c08-input.json"
readonly CYF_GRADLE_LOCK="/tmp/cyf-gradle.lock"

log() {
  printf '[cyf-release] %s\n' "$*" >&2
}

die() {
  log "ERROR: $*"
  exit 1
}

require_command() {
  command -v -- "$1" >/dev/null 2>&1 || die "required command is unavailable: $1"
}

require_full_git_oid() {
  local label="$1" value="$2"
  [[ "$value" =~ ^[0-9a-f]{40}$ ]] || die "$label must be one full lowercase 40-hex Git object ID"
}

require_sha256() {
  local label="$1" value="$2"
  [[ "$value" =~ ^[0-9a-f]{64}$ ]] || die "$label must be one lowercase SHA-256 digest"
}

release_repo_git() {
  local repo="$1"
  shift
  git -c safe.directory="$repo" -C "$repo" "$@"
}

require_safe_id() {
  local label="$1" value="$2"
  [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]] \
    || die "$label must match [A-Za-z0-9][A-Za-z0-9._-]{0,79}"
}

normalize_absolute_path() {
  local label="$1" value="$2"
  [[ "$value" == /* ]] || die "$label must be an absolute path"
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || die "$label contains a line break"
  realpath -m -- "$value"
}

nearest_existing_path() {
  local path="$1"
  while [[ ! -e "$path" ]]; do
    [[ "$path" != "/" ]] || break
    path="$(dirname -- "$path")"
  done
  printf '%s\n' "$path"
}

assert_not_symlink() {
  local label="$1" path="$2"
  [[ ! -L "$path" ]] || die "$label must not be a symbolic link: $path"
}

assert_mode_0444() {
  local label="$1" path="$2"
  [[ -f "$path" && ! -L "$path" ]] || die "$label must be a physical regular file: $path"
  [[ "$(stat -c %a -- "$path")" == "444" ]] || die "$label must have mode 0444: $path"
}

assert_path_within() {
  local label="$1" path="$2" root="$3"
  path="$(normalize_absolute_path "$label" "$path")"
  root="$(normalize_absolute_path "$label root" "$root")"
  case "$path" in
    "$root"|"$root"/*) ;;
    *) die "$label is outside the approved root: path=$path root=$root" ;;
  esac
}

json_get() {
  local file="$1" dotted="$2"
  python3 - "$file" "$dotted" <<'PY'
import json, sys
path, dotted = sys.argv[1:]
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result
with open(path, 'r', encoding='utf-8') as stream:
    value = json.load(stream, object_pairs_hook=unique_object)
for part in dotted.split('.'):
    if not isinstance(value, dict) or part not in value:
        raise SystemExit(f'missing JSON field: {dotted}')
    value = value[part]
if isinstance(value, bool):
    print('true' if value else 'false')
elif isinstance(value, (str, int)) and not isinstance(value, bool):
    text = str(value)
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        raise SystemExit(f'control character in JSON scalar: {dotted}')
    print(text)
else:
    raise SystemExit(f'JSON field is not a scalar: {dotted}')
PY
}

json_array_lines() {
  local file="$1" dotted="$2"
  python3 - "$file" "$dotted" <<'PY'
import json, sys
path, dotted = sys.argv[1:]
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result
with open(path, 'r', encoding='utf-8') as stream:
    value = json.load(stream, object_pairs_hook=unique_object)
for part in dotted.split('.'):
    if not isinstance(value, dict) or part not in value:
        raise SystemExit(f'missing JSON field: {dotted}')
    value = value[part]
if not isinstance(value, list) or not value:
    raise SystemExit(f'JSON field must be a non-empty array: {dotted}')
for item in value:
    if not isinstance(item, str) or not item or any(ord(ch) < 32 or ord(ch) == 127 for ch in item):
        raise SystemExit(f'invalid array value in: {dotted}')
    print(item)
PY
}

validate_input_shape() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, os, re, sys
path = sys.argv[1]
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result
with open(path, 'r', encoding='utf-8') as stream:
    data = json.load(stream, object_pairs_hook=unique_object)
if data.get('schema') != 'cyf-m2-c08-release-input-v1':
    raise SystemExit('unsupported release input schema')
profile = data.get('verificationProfile', 'm2-default')
if profile not in ('m2-default', 'archive-h06'):
    raise SystemExit('verificationProfile must be m2-default or archive-h06')
required = {
    'releaseId', 'minimumFreeBytes', 'artifactRoot', 'api', 'web'
}
if not required.issubset(data):
    raise SystemExit('release input is missing required top-level fields')
if (not isinstance(data['minimumFreeBytes'], int) or isinstance(data['minimumFreeBytes'], bool)
        or data['minimumFreeBytes'] <= 0):
    raise SystemExit('minimumFreeBytes must be a positive, evidence-derived byte count')
for component in ('api', 'web'):
    item = data[component]
    for key in ('repo', 'ref', 'head', 'tree', 'deploy'):
        if key not in item:
            raise SystemExit(f'missing {component}.{key}')
    if not re.fullmatch(r'[0-9a-f]{40}', item['head']):
        raise SystemExit(f'{component}.head is not a full Git SHA')
    if not re.fullmatch(r'[0-9a-f]{40}', item['tree']):
        raise SystemExit(f'{component}.tree is not a full Git tree SHA')
    if not os.path.isabs(item['repo']):
        raise SystemExit(f'{component}.repo is not absolute')
if not os.path.isabs(data['artifactRoot']):
    raise SystemExit('artifactRoot is not absolute')
for key in ('gradleTask', 'jarRelativePath'):
    if key not in data['api']:
        raise SystemExit(f'missing api.{key}')
if not re.fullmatch(r':[A-Za-z0-9:_-]+', data['api']['gradleTask']):
    raise SystemExit('api.gradleTask is unsafe')
if data['api']['jarRelativePath'].startswith('/') or '..' in data['api']['jarRelativePath'].split('/'):
    raise SystemExit('api.jarRelativePath is unsafe')
for key in ('npmBin', 'distRelativePath'):
    if key not in data['web']:
        raise SystemExit(f'missing web.{key}')
if data['web']['distRelativePath'].startswith('/') or '..' in data['web']['distRelativePath'].split('/'):
    raise SystemExit('web.distRelativePath is unsafe')
api_deploy = data['api']['deploy']
web_deploy = data['web']['deploy']
for key in ('liveJar', 'pidFile', 'workDir', 'backupRoot', 'recordRoot',
            'healthUrl', 'healthExpectedRegex', 'stopTimeoutSeconds',
            'healthTimeoutSeconds'):
    if key not in api_deploy:
        raise SystemExit(f'missing api.deploy.{key}')
for key in ('liveJar', 'pidFile', 'workDir', 'backupRoot', 'recordRoot'):
    if not isinstance(api_deploy[key], str) or not os.path.isabs(api_deploy[key]):
        raise SystemExit(f'api.deploy.{key} must be an absolute path')
for key in ('stopTimeoutSeconds', 'healthTimeoutSeconds'):
    if not isinstance(api_deploy[key], int) or isinstance(api_deploy[key], bool):
        raise SystemExit(f'api.deploy.{key} must be an integer')
for key in ('liveDir', 'backupRoot', 'recordRoot', 'healthUrls', 'healthTimeoutSeconds'):
    if key not in web_deploy:
        raise SystemExit(f'missing web.deploy.{key}')
for key in ('liveDir', 'backupRoot', 'recordRoot'):
    if not isinstance(web_deploy[key], str) or not os.path.isabs(web_deploy[key]):
        raise SystemExit(f'web.deploy.{key} must be an absolute path')
if not isinstance(web_deploy['healthTimeoutSeconds'], int) or isinstance(web_deploy['healthTimeoutSeconds'], bool):
    raise SystemExit('web.deploy.healthTimeoutSeconds must be an integer')
if (not isinstance(web_deploy['healthUrls'], list) or not web_deploy['healthUrls'] or
        any(not isinstance(value, str) or not value for value in web_deploy['healthUrls'])):
    raise SystemExit('web.deploy.healthUrls must be a non-empty string array')
PY
}

release_input_verification_profile() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as stream:
    data = json.load(stream)
profile = data.get('verificationProfile', 'm2-default')
if profile not in ('m2-default', 'archive-h06'):
    raise SystemExit('unknown release verification profile')
print(profile)
PY
}

load_release_input() {
  local requested="${1:-$CYF_RELEASE_DEFAULT_INPUT}"
  RELEASE_INPUT="$(normalize_absolute_path 'release input' "$requested")"
  [[ -f "$RELEASE_INPUT" ]] || die "release input does not exist: $RELEASE_INPUT"
  assert_not_symlink "release input" "$RELEASE_INPUT"
  validate_input_shape "$RELEASE_INPUT" || die "invalid release input: $RELEASE_INPUT"

  RELEASE_ID="$(json_get "$RELEASE_INPUT" releaseId)"
  RELEASE_VERIFY_PROFILE="$(release_input_verification_profile "$RELEASE_INPUT")"
  export RELEASE_VERIFY_PROFILE
  MINIMUM_FREE_BYTES="$(json_get "$RELEASE_INPUT" minimumFreeBytes)"
  ARTIFACT_ROOT="$(normalize_absolute_path 'artifact root' "$(json_get "$RELEASE_INPUT" artifactRoot)")"

  API_REPO="$(normalize_absolute_path 'API candidate repo' "$(json_get "$RELEASE_INPUT" api.repo)")"
  API_REF="$(json_get "$RELEASE_INPUT" api.ref)"
  API_HEAD="$(json_get "$RELEASE_INPUT" api.head)"
  API_TREE="$(json_get "$RELEASE_INPUT" api.tree)"
  API_GRADLE_TASK="$(json_get "$RELEASE_INPUT" api.gradleTask)"
  API_JAR_RELATIVE_PATH="$(json_get "$RELEASE_INPUT" api.jarRelativePath)"

  WEB_REPO="$(normalize_absolute_path 'Web candidate repo' "$(json_get "$RELEASE_INPUT" web.repo)")"
  WEB_REF="$(json_get "$RELEASE_INPUT" web.ref)"
  WEB_HEAD="$(json_get "$RELEASE_INPUT" web.head)"
  WEB_TREE="$(json_get "$RELEASE_INPUT" web.tree)"
  WEB_NPM_BIN="$(normalize_absolute_path 'npm binary' "$(json_get "$RELEASE_INPUT" web.npmBin)")"
  WEB_DIST_RELATIVE_PATH="$(json_get "$RELEASE_INPUT" web.distRelativePath)"

  require_safe_id "releaseId" "$RELEASE_ID"
  require_full_git_oid "api.head" "$API_HEAD"
  require_full_git_oid "api.tree" "$API_TREE"
  require_full_git_oid "web.head" "$WEB_HEAD"
  require_full_git_oid "web.tree" "$WEB_TREE"

  API_ARTIFACT_BASENAME="cyf-api-${API_HEAD}-${API_TREE}.jar"
  WEB_ARTIFACT_BASENAME="cyf-web-${WEB_HEAD}-${WEB_TREE}.tar.gz"
  API_ARTIFACT="$ARTIFACT_ROOT/api/$API_ARTIFACT_BASENAME"
  WEB_ARTIFACT="$ARTIFACT_ROOT/web/$WEB_ARTIFACT_BASENAME"
  RELEASE_RECORD_BASENAME="cyf-release-${API_HEAD}-${API_TREE}-${WEB_HEAD}-${WEB_TREE}.json"
  RELEASE_RECORD="$ARTIFACT_ROOT/release/$RELEASE_RECORD_BASENAME"

  case "$ARTIFACT_ROOT" in
    "$API_REPO"|"$API_REPO"/*|"$WEB_REPO"|"$WEB_REPO"/*)
      die "artifact root must be outside both candidate worktrees"
      ;;
  esac
}

assert_clean_candidate() {
  local label="$1" repo="$2" expected_ref="$3" expected_head="$4" expected_tree="$5"
  [[ -d "$repo" ]] || die "$label candidate directory does not exist: $repo"
  assert_not_symlink "$label candidate directory" "$repo"
  release_repo_git "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "$label candidate is not a Git worktree: $repo"

  local actual_head actual_tree actual_ref status
  actual_head="$(release_repo_git "$repo" rev-parse --verify HEAD)"
  actual_tree="$(release_repo_git "$repo" rev-parse --verify 'HEAD^{tree}')"
  actual_ref="$(release_repo_git "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  status="$(release_repo_git "$repo" status --porcelain=v1 --untracked-files=all)"

  [[ "$actual_head" == "$expected_head" ]] \
    || die "$label HEAD mismatch: expected=$expected_head actual=$actual_head"
  [[ "$actual_tree" == "$expected_tree" ]] \
    || die "$label tree mismatch: expected=$expected_tree actual=$actual_tree"
  [[ "$actual_ref" == "$expected_ref" ]] \
    || die "$label ref mismatch: expected=$expected_ref actual=${actual_ref:-DETACHED}"
  [[ -z "$status" ]] || die "$label candidate is dirty; refusing release work"
  [[ "$(release_repo_git "$repo" cat-file -t "$expected_head")" == commit ]] \
    || die "$label expected HEAD is not a commit"
  [[ "$(release_repo_git "$repo" cat-file -t "$expected_tree")" == tree ]] \
    || die "$label expected tree is not a tree object"
  [[ "$(release_repo_git "$repo" rev-parse "${expected_head}^{tree}")" == "$expected_tree" ]] \
    || die "$label expected commit does not resolve to expected tree"
  release_repo_git "$repo" diff --check --cached -- >/dev/null \
    || die "$label index diff-check failed"
  release_repo_git "$repo" diff --check -- >/dev/null \
    || die "$label worktree diff-check failed"
}

assert_disk_gate() {
  local path="$1" label="${2:-filesystem}"
  local existing available
  existing="$(nearest_existing_path "$(normalize_absolute_path "$label path" "$path")")"
  available="$(df -PB1 -- "$existing" | awk 'NR==2 {print $4}')"
  [[ "$available" =~ ^[0-9]+$ ]] || die "cannot determine free bytes for $label: $existing"
  if (( available < MINIMUM_FREE_BYTES )); then
    log "$label free-space observation below former threshold (non-blocking): available=$available former_required=$MINIMUM_FREE_BYTES path=$existing"
  else
    log "$label free-space observation: available=$available former_required=$MINIMUM_FREE_BYTES path=$existing"
  fi
}

artifact_sha256() {
  sha256sum -- "$1" | awk '{print $1}'
}

write_sha256_sidecar() {
  local artifact="$1" basename digest tmp sidecar expected
  basename="$(basename -- "$artifact")"
  digest="$(artifact_sha256 "$artifact")"
  sidecar="${artifact}.sha256"
  expected="$digest  $basename"
  if [[ -e "$sidecar" ]]; then
    [[ -f "$sidecar" && ! -L "$sidecar" ]] || die "SHA-256 sidecar is not a regular file: $sidecar"
    [[ "$(stat -c %a -- "$sidecar")" == "444" ]] \
      || die "immutable SHA-256 sidecar does not have mode 0444: $sidecar"
    [[ "$(cat -- "$sidecar")" == "$expected" ]] \
      || die "immutable SHA-256 sidecar already exists with different content: $sidecar"
    printf '%s\n' "$digest"
    return 0
  fi
  tmp="$(mktemp "$(dirname -- "$artifact")/.tmp.$(basename -- "$artifact").sha256.XXXXXX")"
  printf '%s\n' "$expected" > "$tmp"
  chmod 0444 "$tmp"
  if ! ln -- "$tmp" "$sidecar" 2>/dev/null; then
    rm -f -- "$tmp"
    die "cannot atomically publish SHA-256 sidecar: $sidecar"
  fi
  rm -f -- "$tmp"
  sync -f "$(dirname -- "$sidecar")" 2>/dev/null || true
  printf '%s\n' "$digest"
}

verify_sha256_sidecar() {
  local artifact="$1" sidecar="${1}.sha256" actual expected recorded
  [[ -f "$artifact" && ! -L "$artifact" ]] || die "artifact is missing, non-regular or symlinked: $artifact"
  [[ -f "$sidecar" && ! -L "$sidecar" ]] || die "SHA-256 sidecar is missing, non-regular or symlinked: $sidecar"
  actual="$(artifact_sha256 "$artifact")"
  expected="$actual  $(basename -- "$artifact")"
  recorded="$(cat -- "$sidecar")"
  [[ "$recorded" == "$expected" ]] \
    || die "artifact SHA-256 sidecar is not the exact expected tuple: $artifact"
}

install_immutable_file() {
  local source="$1" destination="$2" mode="${3:-0444}"
  local parent temp source_sha existing_sha
  parent="$(dirname -- "$destination")"
  mkdir -p -- "$parent"
  assert_not_symlink "artifact directory" "$parent"
  source_sha="$(artifact_sha256 "$source")"
  if [[ -e "$destination" ]]; then
    [[ -f "$destination" && ! -L "$destination" ]] || die "immutable destination is not a regular file: $destination"
    [[ "$(stat -c %a -- "$destination")" == "${mode#0}" ]] \
      || die "immutable destination has unexpected mode: $destination"
    existing_sha="$(artifact_sha256 "$destination")"
    [[ "$existing_sha" == "$source_sha" ]] \
      || die "immutable artifact already exists with different content: $destination"
    log "immutable artifact already present with matching SHA-256 and mode: $destination"
    return 0
  fi
  temp="$(mktemp "$parent/.tmp.$(basename -- "$destination").XXXXXX")"
  (umask 077; cp --reflink=auto -- "$source" "$temp")
  chmod "$mode" "$temp"
  sync -f "$temp" 2>/dev/null || true
  if ! ln -- "$temp" "$destination" 2>/dev/null; then
    rm -f -- "$temp"
    die "cannot atomically publish immutable artifact: $destination"
  fi
  rm -f -- "$temp"
  sync -f "$parent" 2>/dev/null || true
}

hash_tree() {
  local directory="$1"
  python3 - "$directory" <<'PY'
import hashlib, os, stat, sys
root = os.path.abspath(sys.argv[1])
if not os.path.isdir(root) or os.path.islink(root):
    raise SystemExit('tree root must be one physical directory')
digest = hashlib.sha256()
entries = []
for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
    dirs.sort()
    files.sort()
    for name in dirs + files:
        path = os.path.join(current, name)
        rel = os.path.relpath(path, root).replace(os.sep, '/')
        entries.append((rel, path))
for rel, path in sorted(entries):
    encoded = rel.encode('utf-8', 'surrogateescape')
    info = os.lstat(path)
    if stat.S_ISDIR(info.st_mode):
        digest.update(b'D\0' + encoded + b'\0')
    elif stat.S_ISREG(info.st_mode):
        digest.update(b'F\0' + encoded + b'\0' + str(info.st_size).encode() + b'\0')
        with open(path, 'rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        digest.update(b'\0')
    elif stat.S_ISLNK(info.st_mode):
        target = os.readlink(path).encode('utf-8', 'surrogateescape')
        digest.update(b'L\0' + encoded + b'\0' + target + b'\0')
    else:
        raise SystemExit(f'unsupported filesystem entry: {rel}')
print(digest.hexdigest())
PY
}

validate_web_archive() {
  local archive="$1"
  python3 - "$archive" <<'PY'
import posixpath, sys, tarfile
archive = sys.argv[1]
seen = set()
has_index = False
with tarfile.open(archive, 'r:gz') as bundle:
    for item in bundle.getmembers():
        name = item.name
        while name.startswith('./'):
            name = name[2:]
        normalized = posixpath.normpath(name)
        if not name or normalized in ('', '.'):
            continue
        if name.startswith('/') or normalized == '..' or normalized.startswith('../'):
            raise SystemExit(f'unsafe archive path: {item.name}')
        if normalized in seen:
            raise SystemExit(f'duplicate archive path: {item.name}')
        seen.add(normalized)
        if not (item.isdir() or item.isfile()):
            raise SystemExit(f'unsupported archive entry type: {item.name}')
        if normalized == 'index.html' and item.isfile():
            has_index = True
if not has_index:
    raise SystemExit('web archive has no root index.html')
PY
}

release_tool_digest() {
  (
    cd -- "$CYF_RELEASE_SCRIPT_DIR"
    for file in common.sh build-api.sh build-web.sh promote-release.sh verify-release.sh \
      deploy-api.sh deploy-web.sh rollback-api.sh rollback-web.sh; do
      [[ -f "$file" && ! -L "$file" ]] || die "release tool file is missing or symlinked: $file"
      printf '%s\0' "$file"
      sha256sum -- "$file"
    done
  ) | sha256sum | awk '{print $1}'
}

verify_component_metadata() {
  local component="$1" artifact metadata schema head tree ref basename
  case "$component" in
    api)
      artifact="$API_ARTIFACT"; schema="cyf-api-artifact-v1"; head="$API_HEAD"; tree="$API_TREE"
      ref="$API_REF"; basename="$API_ARTIFACT_BASENAME"
      ;;
    web)
      artifact="$WEB_ARTIFACT"; schema="cyf-web-artifact-v1"; head="$WEB_HEAD"; tree="$WEB_TREE"
      ref="$WEB_REF"; basename="$WEB_ARTIFACT_BASENAME"
      ;;
    *) die "unknown release component: $component" ;;
  esac
  metadata="${artifact}.json"
  verify_sha256_sidecar "$artifact"
  verify_sha256_sidecar "$metadata"
  assert_mode_0444 "$component artifact" "$artifact"
  assert_mode_0444 "$component artifact metadata" "$metadata"
  assert_mode_0444 "$component artifact checksum" "${artifact}.sha256"
  assert_mode_0444 "$component metadata checksum" "${metadata}.sha256"
  python3 - "$metadata" "$schema" "$RELEASE_ID" "$ref" "$head" "$tree" "$basename" \
    "$(artifact_sha256 "$artifact")" \
    "$(artifact_sha256 "$RELEASE_INPUT")" "$(release_tool_digest)" "$RELEASE_VERIFY_PROFILE" <<'PY'
import json, sys
path, schema, release_id, ref, head, tree, artifact, artifact_sha, input_sha, tool_sha, verify_profile = sys.argv[1:]
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result
with open(path, 'r', encoding='utf-8') as stream:
    data = json.load(stream, object_pairs_hook=unique_object)
expected = {
    'schema': schema, 'releaseId': release_id, 'sourceRef': ref,
    'sourceHead': head, 'sourceTree': tree, 'artifact': artifact,
    'artifactSha256': artifact_sha, 'releaseInputSha256': input_sha,
    'releaseToolSha256': tool_sha
}
for key, value in expected.items():
    if data.get(key) != value:
        raise SystemExit(f'artifact metadata mismatch for {key}')
if 'verificationProfile' in data and data['verificationProfile'] != verify_profile:
    raise SystemExit('artifact metadata verificationProfile mismatch')
PY
}

verify_release_record_component() {
  local component="$1" component_artifact component_artifact_name component_sha
  case "$component" in
    api)
      component_artifact="$API_ARTIFACT"
      component_artifact_name="$API_ARTIFACT_BASENAME"
      ;;
    web)
      component_artifact="$WEB_ARTIFACT"
      component_artifact_name="$WEB_ARTIFACT_BASENAME"
      ;;
    *) die "unknown release-record component: $component" ;;
  esac
  verify_component_metadata "$component"
  [[ -f "$RELEASE_RECORD" && ! -L "$RELEASE_RECORD" ]] \
    || die "verified joint release record is missing or symlinked: $RELEASE_RECORD"
  verify_sha256_sidecar "$RELEASE_RECORD"
  assert_mode_0444 "joint release record" "$RELEASE_RECORD"
  assert_mode_0444 "joint release record checksum" "${RELEASE_RECORD}.sha256"
  component_sha="$(artifact_sha256 "$component_artifact")"
  python3 - "$RELEASE_RECORD" "$component" "$RELEASE_ID" \
    "$API_HEAD" "$API_TREE" "$WEB_HEAD" "$WEB_TREE" \
    "$component_artifact_name" "$component_sha" \
    "$(release_tool_digest)" "$(artifact_sha256 "$RELEASE_INPUT")" "$RELEASE_VERIFY_PROFILE" <<'PY'
import json, sys
(path, component, release_id, ah, at, wh, wt, artifact_name, artifact_sha,
 tool_digest, input_sha, verify_profile) = sys.argv[1:]
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result
with open(path, 'r', encoding='utf-8') as stream:
    data = json.load(stream, object_pairs_hook=unique_object)
expected = {
    'schema': 'cyf-m2-c08-release-record-v1',
    'releaseId': release_id,
    'apiHead': ah, 'apiTree': at, 'webHead': wh, 'webTree': wt,
    f'{component}Artifact': artifact_name,
    f'{component}ArtifactSha256': artifact_sha,
    'releaseToolSha256': tool_digest,
    'releaseInputSha256': input_sha,
    'verification': 'PASS'
}
for key, value in expected.items():
    if data.get(key) != value:
        raise SystemExit(f'release record mismatch for {key}')
if data.get('verificationProfile', 'm2-default') != verify_profile:
    raise SystemExit('release record verificationProfile mismatch')
if data.get('apiFeatureDefault') is not False or data.get('webFeatureDefault') is not False:
    raise SystemExit('release record feature defaults are not false')
for key in ('productionDatabaseOperation', 'rabbitMqOperation', 'deployment'):
    if data.get(key) != 'NOT_PERFORMED':
        raise SystemExit(f'release record unsafe operation state for {key}')
PY
}

verify_release_record() {
  verify_release_record_component api
  verify_release_record_component web
  python3 - "$RELEASE_RECORD" "$(json_get "${WEB_ARTIFACT}.json" distTreeSha256)" <<'PY'
import json, sys
path, web_dist = sys.argv[1:]
with open(path, 'r', encoding='utf-8') as stream:
    data = json.load(stream)
if data.get('webDistTreeSha256') != web_dist:
    raise SystemExit('release record mismatch for webDistTreeSha256')
PY
}

acquire_execution_lock() {
  local component="$1" lock_path
  (( EXECUTE == 1 )) || return 0
  case "$component" in api|web) ;; *) die "unknown execution lock component: $component" ;; esac
  lock_path="/tmp/cyf-release-${component}.lock"
  exec {CYF_RELEASE_EXECUTION_LOCK_FD}>"$lock_path"
  flock -n "$CYF_RELEASE_EXECUTION_LOCK_FD" \
    || die "another $component deploy/rollback operation holds $lock_path"
  log "exclusive $component execution lock acquired: $lock_path"
}

parse_common_args() {
  INPUT_FILE="$CYF_RELEASE_DEFAULT_INPUT"
  EXECUTE=0
  POSITIONAL=()
  while (($#)); do
    case "$1" in
      --input)
        (($# >= 2)) || die "--input requires a path"
        INPUT_FILE="$2"
        shift 2
        ;;
      --execute)
        EXECUTE=1
        shift
        ;;
      --dry-run)
        EXECUTE=0
        shift
        ;;
      --help|-h)
        SHOW_HELP=1
        shift
        ;;
      --)
        shift
        POSITIONAL+=("$@")
        break
        ;;
      -*) die "unknown option: $1" ;;
      *) POSITIONAL+=("$1"); shift ;;
    esac
  done
}

require_execute_approval() {
  (( EXECUTE == 1 )) || return 0
  [[ "${CYF_RELEASE_APPROVED:-}" == "YES" ]] \
    || die "--execute requires CYF_RELEASE_APPROVED=YES"
  require_safe_id "CYF_RELEASE_APPROVAL_ID" "${CYF_RELEASE_APPROVAL_ID:-}"
  [[ "${CYF_RELEASE_APPROVED_API_HEAD:-}" == "$API_HEAD" ]] \
    || die "approved API HEAD does not match release input"
  [[ "${CYF_RELEASE_APPROVED_API_TREE:-}" == "$API_TREE" ]] \
    || die "approved API tree does not match release input"
  [[ "${CYF_RELEASE_APPROVED_WEB_HEAD:-}" == "$WEB_HEAD" ]] \
    || die "approved Web HEAD does not match release input"
  [[ "${CYF_RELEASE_APPROVED_WEB_TREE:-}" == "$WEB_TREE" ]] \
    || die "approved Web tree does not match release input"
}

print_mode() {
  if (( EXECUTE == 1 )); then
    log "mode=EXECUTE approval_id=${CYF_RELEASE_APPROVAL_ID}"
  else
    log "mode=DRY-RUN (no deployment state will be changed)"
  fi
}

process_start_ticks() {
  local pid="$1"
  python3 - "$pid" <<'PY'
import sys
pid = sys.argv[1]
with open(f'/proc/{pid}/stat', 'r', encoding='utf-8') as stream:
    text = stream.read()
end = text.rfind(')')
if end < 0:
    raise SystemExit('malformed proc stat')
fields = text[end + 2:].split()
print(fields[19])
PY
}

find_single_java_jar_pid() {
  local live_jar="$1" pid arg previous target target_identity exe found=()
  local live_identity
  live_identity="$(stat -Lc '%d:%i' -- "$live_jar")"
  for proc in /proc/[0-9]*; do
    [[ -r "$proc/cmdline" ]] || continue
    pid="${proc##*/}"
    exe="$(readlink -e -- "$proc/exe" 2>/dev/null || true)"
    [[ "$(basename -- "$exe")" == java ]] || continue
    previous=""
    while IFS= read -r -d '' arg; do
      if [[ "$previous" == "-jar" ]]; then
        if [[ "$arg" == /* ]]; then
          target="$proc/root$arg"
        else
          target="$proc/cwd/$arg"
        fi
        target_identity="$(stat -Lc '%d:%i' -- "$target" 2>/dev/null || true)"
        if [[ -n "$target_identity" && "$target_identity" == "$live_identity" ]]; then
          found+=("$pid")
          break
        fi
      fi
      previous="$arg"
    done < "$proc/cmdline"
  done
  ((${#found[@]} == 1)) \
    || die "expected exactly one Java -jar process for $live_jar; found=${#found[@]}"
  printf '%s\n' "${found[0]}"
}

proc_argv_sha256() {
  local pid="$1"
  [[ -r "/proc/$pid/cmdline" ]] || die "cannot read process argv for PID $pid"
  sha256sum -- "/proc/$pid/cmdline" | awk '{print $1}'
}

stop_process() {
  local pid="$1" expected_ticks="$2" timeout_seconds="$3"
  [[ "$(process_start_ticks "$pid")" == "$expected_ticks" ]] \
    || die "PID identity changed before stop: $pid"
  kill -TERM "$pid"
  local deadline=$((SECONDS + timeout_seconds))
  while kill -0 "$pid" 2>/dev/null; do
    (( SECONDS < deadline )) || die "PID $pid did not stop within ${timeout_seconds}s; no force-kill attempted"
    sleep 1
  done
}

launch_from_argv_backup() {
  local argv_file="$1" cwd_file="$2" live_jar="$3" log_file="$4" pid_output="$5"
  local -a argv=()
  local index jar_index=-1 log_dir pid
  mapfile -d '' -t argv < "$argv_file"
  ((${#argv[@]} > 2)) || die "saved API argv is empty"
  for ((index = 0; index < ${#argv[@]} - 1; index++)); do
    if [[ "${argv[$index]}" == "-jar" ]]; then
      (( jar_index == -1 )) || die "saved API argv contains multiple -jar options"
      jar_index=$index
    fi
  done
  (( jar_index >= 0 )) || die "saved API argv has no -jar option"
  argv[$((jar_index + 1))]="$live_jar"
  local cwd
  cwd="$(cat -- "$cwd_file")"
  [[ -d "$cwd" && ! -L "$cwd" ]] || die "saved API cwd is unavailable: $cwd"
  log_file="$(normalize_absolute_path 'API launch log' "$log_file")"
  pid_output="$(normalize_absolute_path 'API launch PID output' "$pid_output")"
  log_dir="$(dirname -- "$log_file")"
  mkdir -p -- "$log_dir" "$(dirname -- "$pid_output")"
  assert_not_symlink "API launch log directory" "$log_dir"
  assert_not_symlink "API launch PID directory" "$(dirname -- "$pid_output")"
  (
    cd -- "$cwd"
    if [[ "${CYF_RELEASE_EXECUTION_LOCK_FD:-}" =~ ^[0-9]+$ ]]; then
      eval "exec ${CYF_RELEASE_EXECUTION_LOCK_FD}>&-"
    fi
    unset CYF_RELEASE_APPROVED CYF_RELEASE_APPROVAL_ID \
      CYF_RELEASE_APPROVED_API_HEAD CYF_RELEASE_APPROVED_API_TREE \
      CYF_RELEASE_APPROVED_WEB_HEAD CYF_RELEASE_APPROVED_WEB_TREE
    nohup "${argv[@]}" >> "$log_file" 2>&1 < /dev/null &
    pid=$!
    printf '%s\n' "$pid" > "$pid_output"
    sleep 1
    kill -0 "$pid" 2>/dev/null || exit 1
  ) || die "saved API process failed to launch"
}

wait_for_health() {
  local url="$1" expected_regex="$2" timeout_seconds="$3"
  local deadline=$((SECONDS + timeout_seconds)) body
  while (( SECONDS < deadline )); do
    body="$(curl --fail --silent --show-error --max-time 5 -- "$url" 2>/dev/null || true)"
    if [[ "$body" =~ $expected_regex ]]; then
      return 0
    fi
    sleep 2
  done
  return 1
}

verify_web_health() {
  local live_dir="$1" timeout_seconds="$2"
  shift 2
  local -a urls=("$@")
  local entry_asset deadline body url origin
  [[ -d "$live_dir" && ! -L "$live_dir" && -f "$live_dir/index.html" ]] || return 1
  entry_asset="$(grep -oE '/static/index-[A-Za-z0-9_-]+\.js' "$live_dir/index.html" | head -1)"
  [[ -n "$entry_asset" ]] || return 1
  ((${#urls[@]} > 0)) || return 1
  for url in "${urls[@]}"; do
    deadline=$((SECONDS + timeout_seconds))
    body=""
    while (( SECONDS < deadline )); do
      body="$(curl --proto '=https' --tlsv1.2 --fail --silent --show-error --max-time 8 -- "$url" 2>/dev/null || true)"
      [[ "$body" == *"$entry_asset"* ]] && break
      sleep 2
    done
    [[ "$body" == *"$entry_asset"* ]] || return 1
  done
  origin="$(python3 - "${urls[0]}" <<'PYWEB'
from urllib.parse import urlsplit
import sys
value = urlsplit(sys.argv[1])
print(f'{value.scheme}://{value.netloc}')
PYWEB
)"
  curl --proto '=https' --tlsv1.2 --fail --silent --show-error --max-time 10 \
    --output /dev/null -- "$origin$entry_asset" || return 1
  printf '%s\n' "$entry_asset"
}

capture_api_runtime() {
  local live_jar="$1" pid="$2" backup_dir="$3"
  local ticks final_ticks before_argv_sha after_argv_sha old_sha old_name
  ticks="$(process_start_ticks "$pid")"
  before_argv_sha="$(proc_argv_sha256 "$pid")"
  old_sha="$(artifact_sha256 "$live_jar")"
  old_name="cyf-api-old-${old_sha}.jar"

  (umask 077; mkdir -- "$backup_dir")
  assert_not_symlink "API backup directory" "$backup_dir"
  cp -a -- "$live_jar" "$backup_dir/$old_name"
  [[ "$(artifact_sha256 "$backup_dir/$old_name")" == "$old_sha" ]] \
    || die "API JAR backup checksum mismatch"
  printf '%s  %s\n' "$old_sha" "$old_name" > "$backup_dir/$old_name.sha256"
  cat -- "/proc/$pid/cmdline" > "$backup_dir/old.argv.nul"
  chmod 0600 "$backup_dir/old.argv.nul"
  after_argv_sha="$(artifact_sha256 "$backup_dir/old.argv.nul")"
  [[ "$after_argv_sha" == "$before_argv_sha" ]] \
    || die "API argv changed while it was being backed up"
  printf '%s  old.argv.nul\n' "$after_argv_sha" > "$backup_dir/old.argv.nul.sha256"
  readlink -e -- "/proc/$pid/cwd" > "$backup_dir/old.cwd"
  readlink -e -- "/proc/$pid/exe" > "$backup_dir/old.exe"
  printf '%s\n' "$pid" > "$backup_dir/old.pid"
  printf '%s\n' "$ticks" > "$backup_dir/old.start-ticks"
  chmod 0600 "$backup_dir"/*
  write_sha256_sidecar "$backup_dir/old.cwd" >/dev/null
  write_sha256_sidecar "$backup_dir/old.exe" >/dev/null
  write_sha256_sidecar "$backup_dir/old.pid" >/dev/null
  write_sha256_sidecar "$backup_dir/old.start-ticks" >/dev/null
  sync -f "$backup_dir" 2>/dev/null || true
  final_ticks="$(process_start_ticks "$pid")"
  [[ "$final_ticks" == "$ticks" ]] || die "API PID identity changed while runtime was being backed up"
  printf '%s\n%s\n%s\n' "$old_sha" "$old_name" "$ticks"
}

atomic_install_jar() {
  local artifact="$1" live_jar="$2" stage="$3"
  [[ -f "$artifact" && ! -L "$artifact" ]] || die "API artifact is not a regular file"
  [[ -f "$live_jar" && ! -L "$live_jar" ]] || die "live API JAR is not a physical regular file"
  [[ ! -e "$stage" && ! -L "$stage" ]] || die "API staging path already exists: $stage"
  [[ "$(stat -c %d -- "$(dirname -- "$live_jar")")" == "$(stat -c %d -- "$(dirname -- "$stage")")" ]] \
    || die "API stage and live JAR are not on the same filesystem"
  cp --reflink=auto -- "$artifact" "$stage"
  chmod --reference="$live_jar" "$stage"
  chown --reference="$live_jar" "$stage"
  sync -f "$stage" 2>/dev/null || true
  mv -fT -- "$stage" "$live_jar"
  sync -f "$(dirname -- "$live_jar")" 2>/dev/null || true
}
