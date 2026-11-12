#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
# shellcheck source=../common.sh
source "$ROOT/ops/release/common.sh"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
TMP="$(mktemp -d /tmp/cyf-release-common-test.XXXXXX)"
trap 'rm -rf --one-file-system -- "$TMP"' EXIT

marker="$TMP/exit-trap-fired"
if bash -c 'set -Eeuo pipefail; source "$1"; marker="$2"; trap '\''printf fired > "$marker"'\'' EXIT; die simulated' _ \
    "$ROOT/ops/release/common.sh" "$marker" >/dev/null 2>&1; then
  fail 'die unexpectedly succeeded'
fi
[[ "$(cat -- "$marker")" == fired ]] || fail 'die bypassed EXIT recovery trap'
pass 'die triggers EXIT recovery trap'

printf '/bin/false\0-jar\0placeholder.jar\0' > "$TMP/argv.nul"
printf '%s\n' "$TMP" > "$TMP/cwd"
if (launch_from_argv_backup "$TMP/argv.nul" "$TMP/cwd" "$TMP/live.jar" \
      "$TMP/logs/launch.log" "$TMP/pid") >/dev/null 2>&1; then
  fail 'failed background launch was reported as successful'
fi
pass 'failed background launch is detected'


# A restarted API must not inherit the deployment lock or approval environment;
# otherwise it permanently blocks future rollback and leaks control-plane state.
exec {CYF_RELEASE_EXECUTION_LOCK_FD}>"$TMP/execution.lock"
flock -n "$CYF_RELEASE_EXECUTION_LOCK_FD" || fail 'cannot acquire test execution lock'
export CYF_RELEASE_APPROVED=YES CYF_RELEASE_APPROVAL_ID=secret-approval
export CYF_RELEASE_APPROVED_API_HEAD=dummy CYF_RELEASE_APPROVED_API_TREE=dummy
export CYF_RELEASE_APPROVED_WEB_HEAD=dummy CYF_RELEASE_APPROVED_WEB_TREE=dummy
cat > "$TMP/probe.sh" <<'PROBE'
#!/usr/bin/env bash
if [[ -e "/proc/$$/fd/$1" ]]; then printf inherited > "$2"; else printf closed > "$2"; fi
if [[ -n "${CYF_RELEASE_APPROVED:-}${CYF_RELEASE_APPROVAL_ID:-}" ]]; then
  printf inherited > "$3"
else
  printf cleared > "$3"
fi
sleep 30
PROBE
chmod +x "$TMP/probe.sh"
printf '%s\0%s\0%s\0%s\0%s\0%s\0' \
  /bin/bash "$TMP/probe.sh" "$CYF_RELEASE_EXECUTION_LOCK_FD" "$TMP/fd-state" "$TMP/env-state" -jar placeholder \
  > "$TMP/probe.argv.nul"
launch_from_argv_backup "$TMP/probe.argv.nul" "$TMP/cwd" "$TMP/live.jar" \
  "$TMP/logs/probe.log" "$TMP/probe.pid"
for _ in {1..20}; do [[ -s "$TMP/fd-state" && -s "$TMP/env-state" ]] && break; sleep 0.1; done
[[ "$(cat "$TMP/fd-state")" == closed ]] || fail 'restarted process inherited execution lock FD'
[[ "$(cat "$TMP/env-state")" == cleared ]] || fail 'restarted process inherited approval environment'
kill "$(cat "$TMP/probe.pid")" 2>/dev/null || true
unset CYF_RELEASE_APPROVED CYF_RELEASE_APPROVAL_ID CYF_RELEASE_APPROVED_API_HEAD \
  CYF_RELEASE_APPROVED_API_TREE CYF_RELEASE_APPROVED_WEB_HEAD CYF_RELEASE_APPROVED_WEB_TREE
exec {CYF_RELEASE_EXECUTION_LOCK_FD}>&-
pass 'restarted process drops release lock and approval environment'

printf stable > "$TMP/source"
printf stable > "$TMP/destination"
chmod 0644 "$TMP/destination"
if (install_immutable_file "$TMP/source" "$TMP/destination" 0444) >/dev/null 2>&1; then
  fail 'mutable existing destination was accepted as immutable'
fi
pass 'mutable existing destination is rejected'

printf payload > "$TMP/artifact-real"
printf '%s  artifact\n' "$(sha256sum "$TMP/artifact-real" | awk '{print $1}')" > "$TMP/sidecar-real"
ln -s artifact-real "$TMP/artifact"
ln -s sidecar-real "$TMP/artifact.sha256"
if (verify_sha256_sidecar "$TMP/artifact") >/dev/null 2>&1; then
  fail 'symlinked artifact/sidecar was accepted'
fi
pass 'symlinked artifact/sidecar is rejected'

for script in deploy-api.sh deploy-web.sh rollback-api.sh rollback-web.sh; do
  grep -Eq '^trap [a-zA-Z0-9_]+ EXIT$' "$ROOT/ops/release/$script" \
    || fail "$script does not install EXIT recovery"
  if grep -Eq '^trap [a-zA-Z0-9_]+ ERR$' "$ROOT/ops/release/$script"; then
    fail "$script regressed to ERR-only recovery"
  fi
done
pass 'all cutover scripts use EXIT recovery'

grep -Fq 'flock -w 600 -x "$CYF_GRADLE_LOCK" bash "$GRADLEW"' \
  "$ROOT/ops/release/build-api.sh" || fail 'Gradle lock timeout invariant missing'
pass 'Gradle lock is serialized with timeout'

heavy_scripts=(
  run-isolated-combined-smoke.sh
  run-isolated-api-deploy-rollback-drill.sh
  run-isolated-archive-pavilion-h06.sh
)
for script in "${heavy_scripts[@]}"; do
  path="$ROOT/ops/release/tests/$script"
  [[ "$(grep -Fc 'CYF_HEAVY_RESOURCE_LOCK=/tmp/cyf-heavy-resource.lock' "$path")" == 1 ]] \
    || fail "$script does not use the one global heavy-resource lock path"
  grep -Fq 'flock -x "$CYF_HEAVY_RESOURCE_LOCK_FD"' "$path" \
    || fail "$script does not wait for the heavy-resource lock"
  if grep -Eq 'flock[[:space:]]+(-n|-w[[:space:]]+[0-9]+).*CYF_HEAVY_RESOURCE_LOCK_FD' "$path"; then
    fail "$script uses a non-waiting or timed heavy-resource lock"
  fi
done
python3 - "$ROOT/ops/release/tests" <<'PYLOCK'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
markers = {
    'run-isolated-combined-smoke.sh': 'RUN="$(mktemp',
    'run-isolated-api-deploy-rollback-drill.sh': 'RUN="$(mktemp',
    'run-isolated-archive-pavilion-h06.sh': 'RUN_ID="$(date',
}
for name, marker in markers.items():
    lines = (root / name).read_text(encoding='utf-8').splitlines()
    calls = [index for index, line in enumerate(lines) if line == 'acquire_heavy_resource_lock']
    if len(calls) != 1:
        raise SystemExit(f'{name}: expected one heavy-resource lock acquisition, found={len(calls)}')
    marker_index = next((index for index, line in enumerate(lines) if marker in line), None)
    if marker_index is None or calls[0] >= marker_index:
        raise SystemExit(f'{name}: heavy-resource lock must be acquired before run allocation')
PYLOCK
pass 'isolated heavy-resource runners wait on one global non-admission flock'

grep -Fq 'rollback approval ID must match the original deploy record changeId' \
  "$ROOT/ops/release/rollback-api.sh" || fail 'API rollback approval binding missing'
grep -Fq 'rollback approval ID must match the original deploy record changeId' \
  "$ROOT/ops/release/rollback-web.sh" || fail 'Web rollback approval binding missing'
pass 'rollback approval is bound to deploy changeId'

load_release_input "$ROOT/ops/release/m2-c08-r6-input.json"
health_regex="$(json_get "$RELEASE_INPUT" api.deploy.healthExpectedRegex)"
for body in '{"status":"UP"}' '{"status":{"code":"UP","description":""}}'; do
  [[ "$body" =~ $health_regex ]] || fail 'r6 health regex rejected a supported UP payload'
done
for body in '{"status":"DOWN"}' '{"status":{"code":"DOWN"}}'; do
  [[ ! "$body" =~ $health_regex ]] || fail 'r6 health regex accepted a DOWN payload'
done
pass 'r6 health regex supports legacy/current UP payloads and rejects DOWN'

release_digest_source="$(sed -n '/^release_tool_digest() {$/,/^}$/p' "$ROOT/ops/release/common.sh")"
[[ "$release_digest_source" == *'promote-release.sh'* ]] \
  || fail 'artifact promotion tool is missing from release_tool_digest'
pass 'artifact promotion tool is included in release tool digest'

printf 'ALL_COMMON_RELEASE_TESTS=PASS\n'
