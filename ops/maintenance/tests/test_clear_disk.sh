#!/bin/bash
# Isolated host-script regression tests; never clean the real deliverables tree.
set -Eeuo pipefail
SCRIPT="${1:-/home/isp/bin/clear_disk.sh}"
# Avoid interpreting the test's positional script path as the cleanup mode.
source "$SCRIPT" check
if [[ -r "${SCRIPT%/*}/host_cleanup_processes.py" ]]; then PROCESS_SCANNER="${SCRIPT%/*}/host_cleanup_processes.py"; fi
FIXTURE=$(mktemp -d /tmp/host-cleanup-test.XXXXXXXX)
trap 'rm -rf -- "$FIXTURE"' EXIT
DELIVERABLES_ROOT="$FIXTURE/deliverables"
mkdir -m 0775 "$DELIVERABLES_ROOT"
ACTIVE_PATHS=()
PASS=0
ok() { PASS=$((PASS + 1)); printf 'PASS %s\n' "$1"; }
fail() { echo "FAIL $1" >&2; exit 1; }
# Verify scheduling on an isolated child, without changing the test runner or a
# production process. The remaining fixture tests use an inert scheduling hook.
(
  renice() { [[ "$1 $2 $3" == '-n 19 -p' && "$4" == "$BASHPID" ]] || exit 1; echo cpu >>"$FIXTURE/priority"; }
  ionice() { [[ "$1 $2 $3" == '-c 3 -p' && "$4" == "$BASHPID" ]] || exit 1; echo io >>"$FIXTURE/priority"; }
  background_cleanup_priority
)
[[ $(cat "$FIXTURE/priority") == $'cpu\nio' ]] || fail 'cleanup scheduling did not target itself'
ok 'cleanup lowers only its own CPU and IO priority before spawning work'
(
  renice() { return 1; }
  ionice() { fail 'IO change ran after CPU scheduling failure'; }
  if background_cleanup_priority; then fail 'priority failure hidden'; fi
)
ok 'cleanup priority failure remains an error'
background_cleanup_priority() { :; }
old_file() {
  mkdir -p -- "${1%/*}"
  printf 'fixture\n' > "$1"
  chmod 0644 "$1"
  touch -d '40 days ago' -- "$1"
}
accept() { is_safe_deliverable "$1" || fail "$2"; ok "$2"; }
reject() { if is_safe_deliverable "$1"; then fail "$2"; fi; ok "$2"; }
# Scanner framing and fail-closed behavior, before later tests stub refreshes.
saved_proc_root="$PROCESS_ROOT"
mkdir -p "$FIXTURE/fake-proc/123/fd"
printf '' > "$FIXTURE/fake-proc/123/maps"
old_file "$FIXTURE/process-scan/old.zip"
ln -s "$FIXTURE/process-scan/old.zip" "$FIXTURE/fake-proc/123/fd/4"
PROCESS_ROOT="$FIXTURE/fake-proc"
snapshot_active_paths || fail 'valid fixture process snapshot rejected'
is_active "$FIXTURE/process-scan/old.zip" || fail 'open process file missed'
ok 'process scanner success marker enables FD/inode protection'
rm "$FIXTURE/fake-proc/123/fd/4"
printf 'malformed maps\n' > "$FIXTURE/fake-proc/123/maps"
if snapshot_active_paths >"$FIXTURE/scan-error.log" 2>&1; then fail 'failed process snapshot returned success'; fi
[[ "$ACTIVE_SCAN_OK" == 0 ]] || fail 'failed snapshot marked complete'
is_active "$FIXTURE/process-scan/old.zip" || fail 'failed snapshot treated as idle'
ok 'failed snapshot protects candidates even inside a Bash conditional'
root_saved="$DELIVERABLES_ROOT"
DELIVERABLES_ROOT="$FIXTURE/process-scan"
if is_safe_deliverable "$DELIVERABLES_ROOT/old.zip"; then fail 'incomplete snapshot permits deletion'; fi
DELIVERABLES_ROOT="$root_saved"
ok 'deliverables safety rejects candidates when process scan is incomplete'
printf '' > "$FIXTURE/fake-proc/123/maps"
snapshot_active_paths || fail 'fresh complete snapshot did not recover'
if is_active "$FIXTURE/process-scan/old.zip"; then fail 'unused fixture file marked active'; fi
ok 'subsequent valid snapshot restores bounded eligibility'
# NUL framing preserves newline-containing paths without splitting them.
newline_path="$FIXTURE/process-scan/with"$'\n'"newline.zip"
old_file "$newline_path"
ln -s "$newline_path" "$FIXTURE/fake-proc/123/fd/4"
snapshot_active_paths || fail 'newline snapshot rejected'
is_active "$newline_path" || fail 'newline path protection lost'
ok 'NUL-framed process metadata retains newline-containing paths'
rm "$FIXTURE/fake-proc/123/fd/4"
PROCESS_ROOT="$saved_proc_root"
ACTIVE_PATHS=(); ACTIVE_INODES=(); ACTIVE_SCAN_OK=1
old_file "$DELIVERABLES_ROOT/old package.tgz"
accept "$DELIVERABLES_ROOT/old package.tgz" 'old archive under existing root:root 0775 accepted'
for suffix in jar zip tar.gz tmp part; do
  old_file "$DELIVERABLES_ROOT/batch/old.$suffix"
  accept "$DELIVERABLES_ROOT/batch/old.$suffix" "allowlisted .$suffix accepted"
done
old_file "$DELIVERABLES_ROOT/recent.zip"
touch "$DELIVERABLES_ROOT/recent.zip"
reject "$DELIVERABLES_ROOT/recent.zip" 'recent archive retained'
old_file "$DELIVERABLES_ROOT/notes.json"
reject "$DELIVERABLES_ROOT/notes.json" 'metadata retained'
old_file "$DELIVERABLES_ROOT/source.py"
reject "$DELIVERABLES_ROOT/source.py" 'source retained'
for name in releases release verification maintenance cleanup diagnostics records design backup-drill rollback evidence src node_modules vendor .git .codex; do
  old_file "$DELIVERABLES_ROOT/$name/old.zip"
  reject "$DELIVERABLES_ROOT/$name/old.zip" "protected $name retained"
done
old_file "$DELIVERABLES_ROOT/other/worktree-evidence.tar.gz"
reject "$DELIVERABLES_ROOT/other/worktree-evidence.tar.gz" 'evidence-named archive retained'
old_file "$DELIVERABLES_ROOT/pinned/old.zip"
touch "$DELIVERABLES_ROOT/pinned/.keep"
reject "$DELIVERABLES_ROOT/pinned/old.zip" '.keep subtree retained'
rm "$DELIVERABLES_ROOT/pinned/.keep"
ln -s missing "$DELIVERABLES_ROOT/pinned/.keep"
reject "$DELIVERABLES_ROOT/pinned/old.zip" 'dangling .keep marker retained'
old_file "$DELIVERABLES_ROOT/writable.zip"
chmod 0664 "$DELIVERABLES_ROOT/writable.zip"
reject "$DELIVERABLES_ROOT/writable.zip" 'group-writable file retained'
old_file "$DELIVERABLES_ROOT/unsafe/old.zip"
chmod 0777 "$DELIVERABLES_ROOT/unsafe"
reject "$DELIVERABLES_ROOT/unsafe/old.zip" 'world-writable directory retained'
old_file "$DELIVERABLES_ROOT/nonroot.zip"
chown 65534 "$DELIVERABLES_ROOT/nonroot.zip"
reject "$DELIVERABLES_ROOT/nonroot.zip" 'non-root file retained'
old_file "$FIXTURE/outside/old.zip"
ln -s "$FIXTURE/outside" "$DELIVERABLES_ROOT/linked-dir"
reject "$DELIVERABLES_ROOT/linked-dir/old.zip" 'symlink directory not followed'
ln -s "$FIXTURE/outside/old.zip" "$DELIVERABLES_ROOT/linked.zip"
reject "$DELIVERABLES_ROOT/linked.zip" 'symlink file retained'
old_file "$DELIVERABLES_ROOT/hardlink.zip"
ln "$DELIVERABLES_ROOT/hardlink.zip" "$FIXTURE/hardlink.zip"
reject "$DELIVERABLES_ROOT/hardlink.zip" 'hardlinked file retained'
ACTIVE_PATHS=("$DELIVERABLES_ROOT/old package.tgz")
reject "$DELIVERABLES_ROOT/old package.tgz" 'open file retained'
ACTIVE_PATHS=("$DELIVERABLES_ROOT/batch")
reject "$DELIVERABLES_ROOT/batch/old.zip" 'active task working directory retained'
accept "$DELIVERABLES_ROOT/old package.tgz" 'unrelated inactive task still eligible'
ACTIVE_PATHS=()
old_file "$DELIVERABLES_ROOT/mounted/old.zip"
findmnt() { printf '%s\n' "$DELIVERABLES_ROOT/mounted"; }
reject "$DELIVERABLES_ROOT/mounted/old.zip" 'nested mount retained'
unset -f findmnt
# The fixture mount is synthetic; preserve that artifact for subsequent tests.
touch "$DELIVERABLES_ROOT/mounted/.keep"
touch "$DELIVERABLES_ROOT/.keep"
reject "$DELIVERABLES_ROOT/old package.tgz" 'root .keep preserves entire tree'
rm "$DELIVERABLES_ROOT/.keep"
plan=$(plan_deliverables_cleanup)
[[ "$plan" == *'Eligible deliverables files: 6;'* ]] || fail "plan candidates: $plan"
[[ -f "$DELIVERABLES_ROOT/old package.tgz" ]] || fail 'plan mutated fixture'
ok 'plan lists exactly six eligible files and does not delete'
snapshot_active_paths() { :; }
recovery_reached() { return 0; }
clean_deliverables >/dev/null
[[ -f "$DELIVERABLES_ROOT/old package.tgz" ]] || fail 'recovery target ignored'
ok 'cleanup stops when recovery target already met'
recovery_reached() { return 1; }
clean_deliverables >/dev/null
[[ ! -e "$DELIVERABLES_ROOT/old package.tgz" && ! -e "$DELIVERABLES_ROOT/batch/old.zip" ]] || fail 'eligible files not removed'
[[ -d "$DELIVERABLES_ROOT/batch" && -f "$DELIVERABLES_ROOT/releases/old.zip" && -f "$DELIVERABLES_ROOT/notes.json" && -f "$FIXTURE/outside/old.zip" ]] || fail 'protected content affected'
ok 'cleanup only unlinks eligible fixture files, retains directories and protected content'
# Reject path replacement between selection and unlink.
old_file "$FIXTURE/race/old.zip"
identity=$(stat -c '%d:%i:%s:%Y:%Z' "$FIXTURE/race/old.zip")
mv "$FIXTURE/race/old.zip" "$FIXTURE/race/original.zip"
old_file "$FIXTURE/race/old.zip"
if unlink_deliverable "$FIXTURE/race/old.zip" "$identity" 2>/dev/null; then fail 'changed inode unlinked'; fi
[[ -f "$FIXTURE/race/old.zip" ]] || fail 'replacement removed'
ok 'replaced file identity rejected before unlink'
identity=$(stat -c '%d:%i:%s:%Y:%Z' "$FIXTURE/outside/old.zip")
if unlink_deliverable "$DELIVERABLES_ROOT/linked-dir/old.zip" "$identity" 2>/dev/null; then fail 'symlink ancestor followed'; fi
[[ -f "$FIXTURE/outside/old.zip" ]] || fail 'outside target removed'
ok 'fd-based unlink rejects symlink ancestors even with matching target identity'
# Locale-independent numeric type checks and strictly bounded temp cache scope.
TEMP_ROOT="$FIXTURE/tmp"
mkdir -m 1777 "$TEMP_ROOT"
old_file "$TEMP_ROOT/tsx-0/old.js"
old_file "$TEMP_ROOT/node-compile-cache/version/old.cache"
old_file "$TEMP_ROOT/cyf-unused-database/data/mysql.ibd"
old_file "$TEMP_ROOT/cyf-unused-release/candidate-api.jar"
old_file "$TEMP_ROOT/.org.chromium.Chromium.nonempty/report.json"
mkdir "$TEMP_ROOT/.org.chromium.Chromium.empty"
touch -d '40 days ago' "$TEMP_ROOT/.org.chromium.Chromium.empty"
for language in C zh_CN.UTF-8; do
  LC_ALL="$language" is_safe_entry "$TEMP_ROOT/tsx-0/old.js" || fail "locale $language file rejected"
  LC_ALL="$language" is_safe_entry "$TEMP_ROOT/tsx-0" || fail "locale $language directory rejected"
  ok "locale $language uses numeric and shell file-type checks"
done
is_safe_temp "$TEMP_ROOT/tsx-0/old.js" || fail 'expired TSX cache rejected'
is_safe_temp "$TEMP_ROOT/node-compile-cache/version/old.cache" || fail 'expired Node cache rejected'
is_safe_temp "$TEMP_ROOT/.org.chromium.Chromium.empty" || fail 'empty Chromium dir rejected'
for path in "$TEMP_ROOT/cyf-unused-database" "$TEMP_ROOT/cyf-unused-release/candidate-api.jar" "$TEMP_ROOT/.org.chromium.Chromium.nonempty"; do
  if is_safe_temp "$path"; then fail "arbitrary temp content accepted: $path"; fi
done
ok 'temp scope rejects database/release trees and nonempty Chromium directory'
touch "$TEMP_ROOT/tsx-0/.keep"
if is_safe_temp "$TEMP_ROOT/tsx-0/old.js"; then fail '.keep cache unprotected'; fi
rm "$TEMP_ROOT/tsx-0/.keep"
ln "$TEMP_ROOT/tsx-0/old.js" "$FIXTURE/external-tsx.js"
if is_safe_temp "$TEMP_ROOT/tsx-0/old.js"; then fail 'hardlink cache accepted'; fi
rm "$FIXTURE/external-tsx.js"
ok '.keep and external hardlinks protect temp files'
ACTIVE_PATHS=("$TEMP_ROOT/tsx-0")
if is_safe_temp "$TEMP_ROOT/tsx-0/old.js"; then fail 'active cache accepted'; fi
ACTIVE_PATHS=()
plan=$(plan_temp_cleanup)
[[ "$plan" == *'Eligible temporary entries: 3;'* ]] || fail "unexpected temp plan: $plan"
[[ -f "$TEMP_ROOT/tsx-0/old.js" ]] || fail 'temp plan mutated files'
ok 'temp plan lists exactly three disposable entries without mutation'
clean_temp >/dev/null
[[ ! -e "$TEMP_ROOT/tsx-0/old.js" && ! -e "$TEMP_ROOT/.org.chromium.Chromium.empty" ]] || fail 'temp caches retained'
[[ -d "$TEMP_ROOT/tsx-0" && -d "$TEMP_ROOT/node-compile-cache/version" && -f "$TEMP_ROOT/cyf-unused-database/data/mysql.ibd" && -f "$TEMP_ROOT/cyf-unused-release/candidate-api.jar" && -f "$TEMP_ROOT/.org.chromium.Chromium.nonempty/report.json" ]] || fail 'protected temporary contents affected'
ok 'temp clean only unlinks cache files/rmdirs empty Chromium; database/source/release/evidence untouched'
# Rejected aged candidates must remain visible in plan and clean counters.
old_file "$TEMP_ROOT/tsx-0/unsafe-old.js"
chmod 0666 "$TEMP_ROOT/tsx-0/unsafe-old.js"
old_file "$TEMP_ROOT/tsx-0/active-old.js"
ACTIVE_PATHS=("$TEMP_ROOT/tsx-0/active-old.js")
plan=$(plan_temp_cleanup)
[[ "$plan" == *'Eligible temporary entries: 0; skipped by safety checks: 2;'* ]] || fail "hidden skip counters: $plan"
ok 'permission-rejected and active aged cache candidates counted rather than hidden'
clean_temp >/dev/null
[[ "$SKIPPED_UNSAFE_COUNT" == 1 && "$SKIPPED_ACTIVE_COUNT" == 1 ]] || fail 'clean skip counters incorrect'
[[ -f "$TEMP_ROOT/tsx-0/unsafe-old.js" && -f "$TEMP_ROOT/tsx-0/active-old.js" ]] || fail 'rejected cache removed'
ok 'clean retains rejected cache candidates and records both skip classes'
ACTIVE_PATHS=()
# Deep audit: caches are file-only; log candidates require specific rotations.
NPM_CACHE_ROOTS=("$FIXTURE/npm/_cacache" "$FIXTURE/npm/_logs")
cache="${NPM_CACHE_ROOTS[0]}"
old_file "$cache/content-v2/hash/old-cache"
old_file "$cache/recent-cache"
touch "$cache/recent-cache"
is_safe_npm_file "$cache/content-v2/hash/old-cache" "$cache" || fail 'old NPM cache rejected'
if is_safe_npm_file "$cache/recent-cache" "$cache"; then fail 'recent NPM cache accepted'; fi
ok 'old NPM cache eligible while recent cache retained'
touch "$cache/content-v2/.keep"
if is_safe_npm_file "$cache/content-v2/hash/old-cache" "$cache"; then fail 'NPM .keep ignored'; fi
rm "$cache/content-v2/.keep"
ok 'NPM ancestor .keep protects subtree'
ln "$cache/content-v2/hash/old-cache" "$FIXTURE/cache-alias"
if is_safe_npm_file "$cache/content-v2/hash/old-cache" "$cache"; then fail 'NPM hardlink accepted'; fi
rm "$FIXTURE/cache-alias"
ok 'NPM external hardlink protected'
findmnt() { printf '%s\n' "$cache/content-v2"; }
if is_safe_npm_file "$cache/content-v2/hash/old-cache" "$cache"; then fail 'NPM bind mount accepted'; fi
unset -f findmnt
ok 'NPM same-device bind mount protected'
ACTIVE_PATHS=("$cache/content-v2/hash/old-cache")
if is_safe_npm_file "$cache/content-v2/hash/old-cache" "$cache"; then fail 'active NPM cache accepted'; fi
ACTIVE_PATHS=()
ok 'active NPM cache protected'
clean_npm_caches >/dev/null
[[ ! -e "$cache/content-v2/hash/old-cache" && -d "$cache/content-v2/hash" && -f "$cache/recent-cache" ]] || fail 'NPM file-only cleanup scope'
ok 'NPM cleanup retains directories and recent files without recursive rm'
LOG_ROOT="$FIXTURE/logs"
old_file "$LOG_ROOT/service/server.log.1.gz"
old_file "$LOG_ROOT/service/server.log.20260901T120000.gz"
old_file "$LOG_ROOT/service/evidence.tgz"
old_file "$LOG_ROOT/service/evidence.log.1.gz"
old_file "$LOG_ROOT/service/current.log"
is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz" || fail 'numeric log rotation rejected'
is_safe_rotated_log "$LOG_ROOT/service/server.log.20260901T120000.gz" || fail 'timestamp rotation rejected'
ok 'numeric and known timestamp log rotations accepted'
for log in evidence.tgz evidence.log.1.gz current.log; do
 if is_safe_rotated_log "$LOG_ROOT/service/$log"; then fail "protected archive/log accepted: $log"; fi
done
ok 'arbitrary archives evidence-named rotations and current logs protected'
touch "$LOG_ROOT/service/.keep"
if is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz"; then fail 'log .keep ignored'; fi
rm "$LOG_ROOT/service/.keep"
ln -s missing "$LOG_ROOT/.keep"
if is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz"; then fail 'log dangling .keep ignored'; fi
rm "$LOG_ROOT/.keep"
ok 'log ancestor and dangling root .keep markers respected'
findmnt() { printf '%s\n' "$LOG_ROOT/service"; }
if is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz"; then fail 'log bind mount accepted'; fi
unset -f findmnt
ok 'same-device log mount protected'
ACTIVE_PATHS=("$LOG_ROOT/service/server.log.1.gz")
if is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz"; then fail 'active log accepted'; fi
ACTIVE_PATHS=()
touch "$LOG_ROOT/service/server.log.1.gz"
if is_safe_rotated_log "$LOG_ROOT/service/server.log.1.gz"; then fail 'refreshed log age not checked'; fi
ok 'active and refreshed log rotations protected'
touch -d '40 days ago' "$LOG_ROOT/service/server.log.1.gz"
plan=$(plan_cache_and_logs)
[[ "$plan" == *'Eligible rotated logs: 2;'* && -f "$LOG_ROOT/service/server.log.1.gz" ]] || fail 'cache/log readonly plan incorrect'
ok 'readonly plan now covers cache and rotated-log stages'
clean_rotated_logs >/dev/null
[[ ! -e "$LOG_ROOT/service/server.log.1.gz" && ! -e "$LOG_ROOT/service/server.log.20260901T120000.gz" ]] || fail 'eligible rotated logs not removed'
[[ -f "$LOG_ROOT/service/evidence.tgz" && -f "$LOG_ROOT/service/current.log" && -d "$LOG_ROOT/service" ]] || fail 'log protected contents affected'
ok 'log clean only removes old eligible rotations and retains evidence and directories'
# Extra mounts ABOVE a whitelist root are just as protected as nested mounts.
old_file "$TEMP_ROOT/tsx-0/ancestor-mount.js"
old_file "$cache/ancestor-mount.cache"
old_file "$LOG_ROOT/service/server.log.3.gz"
old_file "$DELIVERABLES_ROOT/ancestor-mount/old.zip"
findmnt() { printf '/tmp\n'; }
if is_safe_temp "$TEMP_ROOT/tsx-0/ancestor-mount.js"; then fail 'ancestor temp mount accepted'; fi
ok 'mount above temporary-cache whitelist root protected'
if is_safe_npm_file "$cache/ancestor-mount.cache" "$cache"; then fail 'ancestor NPM mount accepted'; fi
ok 'mount above NPM whitelist root protected'
if is_safe_rotated_log "$LOG_ROOT/service/server.log.3.gz"; then fail 'ancestor log mount accepted'; fi
ok 'mount above log whitelist root protected'
if is_safe_deliverable "$DELIVERABLES_ROOT/ancestor-mount/old.zip"; then fail 'ancestor deliverables mount accepted'; fi
ok 'mount above deliverables whitelist root protected'
unset -f findmnt
# Exercise integration with inert stand-ins, never production Flow/cache cleanup.
print_status() { :; }
run_flow() { return 1; }
run_releases() { return 1; }
run_admissions() { return 0; }
run_rebuildables() { return 0; }
run_runtime_backups() { return 0; }
plan_temp_cleanup() { :; }
plan_cache_and_logs() { :; }
MODE=plan
output=$(main 2>&1)
[[ "$output" == *'Eligible deliverables files:'* ]] || fail 'Flow failure hides deliverables plan'
ok 'Flow plan failure does not hide independent deliverables plan'
MODE=clean
LOCK_FILE="$FIXTURE/cleanup.lock"
needs_cleanup() { return 1; }
clean_basic_caches() { fail 'cache cleanup called above free-space threshold'; }
clean_deliverables() { fail 'deliverables cleanup called above free-space threshold'; }
if main >/dev/null 2>&1; then fail 'failed Flow stage hidden above free-space threshold'; else [[ $? == 4 ]] || fail 'wrong stage failure status'; fi
ok 'failed stage returns nonzero even above free-space trigger'
run_flow() { return 0; }
main >/dev/null 2>&1
ok 'free-space threshold protects deliverables cleanup'
runtime_called=0
run_runtime_backups() { runtime_called=$((runtime_called + 1)); }
main >/dev/null 2>&1
[[ "$runtime_called" == 1 ]] || fail 'Runtime retention skipped above space trigger'
ok 'Runtime retention runs even above free-space trigger'
run_runtime_backups() { return 1; }
if main >/dev/null 2>&1; then fail 'Runtime failure hidden'; else [[ $? == 4 ]] || fail 'wrong Runtime failure status'; fi
ok 'Runtime stage failure returns 4 even above free-space trigger'
run_runtime_backups() { return 0; }
if DELIVERABLES_KEEP_DAYS=invalid bash "$SCRIPT" check >"$FIXTURE/invalid.out" 2>&1; then
  fail 'invalid retention accepted'
fi
ok 'invalid retention rejected before any action'
# Inert main: residual low disk must not be reported as a successful run.
print_status() { fail 'automatic clean invoked recursive diagnostic du'; }
run_flow() { return 0; }
run_releases() { return 0; }
clean_basic_caches() { :; }
clean_temp() { :; }
clean_deliverables() { :; }
clean_rotated_logs() { :; }
needs_cleanup() { return 0; }
recovery_reached() { return 1; }
if main >"$FIXTURE/low-disk.out" 2>&1; then
  fail 'below-minimum disk returned success'
else
  [[ $? == 3 ]] || fail 'wrong below-minimum status'
fi
ok 'residual disk below minimum returns exit 3 without expanding deletion scope'
ok 'automatic clean epilogue avoids recursive diagnostic du while holding lock'
if ! MIN_FREE_GB=05 RECOVERY_FREE_GB=08 bash "$SCRIPT" -h >"$FIXTURE/decimal.out" 2>&1; then fail 'decimal leading zeros rejected'; fi
[[ $(cat "$FIXTURE/decimal.out") != *'value too great for base'* ]] || fail 'octal settings error'
ok 'leading-zero settings normalized to bounded decimal integers'
if MIN_FREE_GB=9999999999999999999999999 bash "$SCRIPT" -h >"$FIXTURE/overflow.out" 2>&1; then fail 'overflow setting accepted'; fi
ok 'oversized integer setting rejected without arithmetic overflow'
printf '\nAll %s tests passed.\n' "$PASS"
