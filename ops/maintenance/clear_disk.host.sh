#!/bin/bash
# Conservative host disk recovery.  Flow artifact retention remains delegated to
# flow_host_cleanup.py; this script only removes expired, root-owned temporary
# cache files and empty Chromium directories only (never arbitrary temp trees).
# Temporary old release payloads use the separately locked, state-aware helper.
set -Eeuo pipefail

MODE="${1:-check}"
LOG_RUNNER=/usr/local/libexec/cyf/host_cleanup_log.py
if [[ "${BASH_SOURCE[0]}" == "$0" && "$MODE" == clean && "${CYF_CLEANUP_LOGGED:-0}" != 1 ]]; then
  [[ -r "$LOG_RUNNER" ]] || { echo 'Missing persistent cleanup logger; refusing unlogged cleanup.' >&2; exit 1; }
  exec /usr/bin/python3 -I -B "$LOG_RUNNER" "${BASH_SOURCE[0]}" clean
fi
MIN_FREE_GB="${MIN_FREE_GB:-5}"
RECOVERY_FREE_GB="${RECOVERY_FREE_GB:-8}"
TMP_KEEP_DAYS="${TMP_KEEP_DAYS:-2}"
LOG_KEEP_DAYS="${LOG_KEEP_DAYS:-30}"
RELEASE_KEEP_DAYS="${RELEASE_KEEP_DAYS:-2}"
DELIVERABLES_KEEP_DAYS="${DELIVERABLES_KEEP_DAYS:-30}"
DELIVERABLES_ROOT=/home/isp/wsps/cyf/deliverables
PLAN_DETAIL_LIMIT="${PLAN_DETAIL_LIMIT:-60}"
LOCK_FILE="${LOCK_FILE:-/run/lock/cyf-host-cleanup.lock}"
FLOW_CLEANUP=/usr/local/libexec/cyf/flow_host_cleanup.py
RELEASE_CLEANUP=/usr/local/libexec/cyf/release_payload_cleanup.py
REBUILDABLE_CLEANUP=/usr/local/libexec/cyf/rebuildable_cache_cleanup.py
RUNTIME_BACKUP_CLEANUP=/usr/local/libexec/cyf/runtime_backup_cleanup.py
GRADLE_CACHE_KEEP_DAYS="${GRADLE_CACHE_KEEP_DAYS:-2}"
COMPLETED_TASK_KEEP_HOURS="${COMPLETED_TASK_KEEP_HOURS:-24}"
PROCESS_SCANNER=/usr/local/libexec/cyf/host_cleanup_processes.py
PROCESS_ROOT=/proc
TEMP_ROOT=/tmp
LOG_ROOT=/home/isp/logs
NPM_CACHE_ROOTS=(/root/.npm/_cacache /root/.npm/_logs)

case "$MIN_FREE_GB:$RECOVERY_FREE_GB:$TMP_KEEP_DAYS:$LOG_KEEP_DAYS:$RELEASE_KEEP_DAYS:$DELIVERABLES_KEEP_DAYS:$PLAN_DETAIL_LIMIT:$GRADLE_CACHE_KEEP_DAYS:$COMPLETED_TASK_KEEP_HOURS" in
  *[!0-9:]*|:*|*::*) echo 'retention, free-space, and detail settings must be non-negative integers' >&2; exit 2 ;;
esac
# Interpret accepted settings as bounded DECIMAL integers (08 is not octal).
for setting in MIN_FREE_GB RECOVERY_FREE_GB TMP_KEEP_DAYS LOG_KEEP_DAYS RELEASE_KEEP_DAYS DELIVERABLES_KEEP_DAYS PLAN_DETAIL_LIMIT GRADLE_CACHE_KEEP_DAYS COMPLETED_TASK_KEEP_HOURS; do
  [[ "${!setting}" =~ ^[0-9]{1,9}$ ]] || { echo "Setting out of supported integer range: $setting" >&2; exit 2; }
  printf -v "$setting" '%s' "$((10#${!setting}))"
done
unset setting
if (( RECOVERY_FREE_GB < MIN_FREE_GB )); then
  echo 'RECOVERY_FREE_GB must be at least MIN_FREE_GB' >&2
  exit 2
fi

usage() {
  cat <<'USAGE'
Usage: /home/isp/bin/clear_disk.sh {check|plan|clean}

check  Show disk space and the bounded cleanup scope.
plan   List eligible expired artifacts without changing files.
clean  Run Flow and Runtime recovery-payload retention (newest two + current pin).
       Runtime retirement is independent of disk pressure; records remain. If free space is below MIN_FREE_GB (default: 5),
       remove only inactive, root-owned, non-symlink cache files older
       than TMP_KEEP_DAYS (default: 2).  Stops at RECOVERY_FREE_GB (default: 8).
       Also considers allowlisted files under /home/isp/wsps/cyf/deliverables
       older than DELIVERABLES_KEEP_DAYS (default: 30): .jar/.zip/.tgz/.tar.gz,
       .tmp/.part. Releases, evidence, source/dependency directories, .keep-marked
       trees, symlinks, mounts, unsafe permissions, and active paths are skipped.
       Old temporary release JARs/known cloud packages use a state/lock-aware
       per-file helper (RELEASE_KEEP_DAYS default: 2). Embedded records are copied
       and byte-verified before cloud package deletion; all directories remain.
       Also considers inactive Gradle cache files aged GRADLE_CACHE_KEEP_DAYS+1
       days (default 3 days) and node_modules declared in the private completed-task
       registry after COMPLETED_TASK_KEEP_HOURS (default 24). Explicit final packages
       in that same registry retain newest two batches per component plus authoritative
       current/rollback pins; release locks and content identity are rechecked.
       Unregistered packages are never inferred disposable. Never infers completion
       from age/inactivity. No deliverables/temp directory tree is removed; plan never deletes.
       Clean stdout/stderr/exit status persists in /home/isp/logs/clear_disk.log.

Protected unconditionally: databases, middleware data, application/runtime files,
worktrees, source repositories, deployment evidence, Codex data, locks/sockets,
and Flow incoming payloads.  Flow backups/downloads are handled only by the
state- and deployment-lock-guarded Python helper.
USAGE
}

# Automatic retention must yield to builds and serving traffic on the shared host.
# Only this cleanup shell and its future descendants are affected, never a PID
# found by the process scanner or an already running cleanup invocation.
background_cleanup_priority() {
  renice -n 19 -p "$BASHPID" >/dev/null || return 1
  ionice -c 3 -p "$BASHPID" || return 1
}

free_bytes() { df -PB1 / | awk 'NR == 2 {print $4}'; }
human_bytes() { numfmt --to=iec-i --suffix=B "$1" 2>/dev/null || printf '%sB' "$1"; }
threshold_bytes() { printf '%s' "$(( $1 * 1024 * 1024 * 1024 ))"; }
recovery_reached() { (( $(free_bytes) >= $(threshold_bytes "$RECOVERY_FREE_GB") )); }
needs_cleanup() { (( $(free_bytes) < $(threshold_bytes "$MIN_FREE_GB") )); }

print_status() {
  echo '== Filesystem =='
  df -hT /
  printf 'Automatic trigger: below %s GiB; recovery target: %s GiB\n' "$MIN_FREE_GB" "$RECOVERY_FREE_GB"
  echo
  echo '== Bounded cleanup areas =='
  du -xsh /tmp /var/tmp /var/log/journal /root/.npm/_cacache /root/.cache /home/isp/logs \
    /home/isp/baks /home/isp/state/cyf-api-flow /home/isp/state/cyf-web-flow "$DELIVERABLES_ROOT" 2>/dev/null || true
  printf 'Deliverables: allowlisted files older than %s days; releases/evidence protected\n' "$DELIVERABLES_KEEP_DAYS"
}

# No generic cyf-*/tmp.* directory is disposable: it may contain a database,
# source, deployment evidence, or a release payload. Only exact cache areas below
# participate; old temporary release files belong to RELEASE_CLEANUP instead.
is_candidate_name() {
  local root="$1" name="$2"
  [[ "$root" == "$TEMP_ROOT" ]] || return 1
  case "$name" in .org.chromium.Chromium.*|node-compile-cache|tsx-0) return 0 ;; esac
  return 1
}

# Never treat preservation material or synchronization primitives as disposable.
is_protected_name() {
  local name="${1,,}"
  case "$name" in
    .agents|.codex|.git|tmux-*|hsperfdata_*|systemd-private-*|*.lock|*.sock|*.socket|*evidence*|*preservation*|*incident*|*notification*|*recovery*|*gradle-ready*|*.init.gradle|*df-attribution*)
      return 0 ;;
  esac
  return 1
}

# Snapshot metadata only. Failed/partial scans protect every candidate, even if
# Bash errexit is suppressed by an enclosing conditional cleanup-stage call.
ACTIVE_PATHS=()
declare -A ACTIVE_INODES=()
ACTIVE_SCAN_OK=1
snapshot_active_paths() {
  local -a records=()
  local record
  ACTIVE_SCAN_OK=0
  ACTIVE_PATHS=()
  ACTIVE_INODES=()
  [[ -r "$PROCESS_SCANNER" ]] || { echo 'WARNING: missing process scanner; candidates protected.' >&2; return 1; }
  mapfile -d '' -t records < <(/usr/bin/python3 -I -B "$PROCESS_SCANNER" --proc-root "$PROCESS_ROOT")
  if (( ${#records[@]} == 0 )) || [[ "${records[-1]}" != '__CYF_PROCESS_SNAPSHOT_COMPLETE__' ]]; then
    echo 'WARNING: process snapshot incomplete; candidates protected.' >&2
    return 1
  fi
  for record in "${records[@]}"; do
    case "$record" in
      /*) ACTIVE_PATHS+=("$record") ;;
      @inode:*) ACTIVE_INODES["${record#@inode:}"]=1 ;;
    esac
  done
  ACTIVE_SCAN_OK=1
}

is_active() {
  local path="$1" active identity
  (( ACTIVE_SCAN_OK == 1 )) || return 0
  identity=$(stat -Lc '%d:%i' -- "$path" 2>/dev/null) || return 0
  [[ -n "${ACTIVE_INODES[$identity]+present}" ]] && return 0
  for active in "${ACTIVE_PATHS[@]}"; do
    case "$active" in "$path"|"$path"/*) return 0 ;; esac
  done
  return 1
}

# Root-owned, non-group/world-writable entries in sticky temp roots cannot be
# swapped by an unprivileged user after validation.  Symlinks are never removed.
is_safe_entry() {
  local path="$1" uid mode
  [[ ! -L "$path" && ( -f "$path" || -d "$path" ) ]] || return 1
  # Numeric fields + shell type tests: never compare translated stat %F output.
  IFS='|' read -r uid mode < <(stat -c '%u|%a' -- "$path" 2>/dev/null) || return 1
  [[ "$uid" == 0 ]] || return 1
  (( (8#$mode & 8#022) == 0 )) || return 1
}

REMOVED_COUNT=0
SKIPPED_UNSAFE_COUNT=0
SKIPPED_ACTIVE_COUNT=0

is_safe_temp() {
  local path="$1" parent mount_target
  is_safe_entry "$path" || return 1
  [[ "$(realpath -e -- "$path")" == "$path" ]] || return 1
  case "$path" in
    "$TEMP_ROOT"/.org.chromium.Chromium.*)
      # Chromium's generated root can only be removed if it is EMPTY.
      [[ "${path%/*}" == "$TEMP_ROOT" && -d "$path" ]] || return 1
      [[ -z $(find -P "$path" -mindepth 1 -maxdepth 1 -print -quit) ]] || return 1 ;;
    "$TEMP_ROOT"/node-compile-cache/*|"$TEMP_ROOT"/tsx-0/*)
      [[ -f "$path" && $(stat -c '%h' -- "$path") == 1 ]] || return 1 ;;
    *) return 1 ;;
  esac
  [[ -n $(find -P "$path" -maxdepth 0 -mtime +"$TMP_KEEP_DAYS" -print) ]] || return 1
  mount_target=$(findmnt -rn -T "$path" -o TARGET) || return 1
  # Root-space recovery must not delete through an ancestor bind/separate mount.
  [[ "$mount_target" == / ]] || return 1
  is_active "$path" && return 1
  parent=${path%/*}
  while [[ "$parent" != "$TEMP_ROOT" ]]; do
    is_safe_entry "$parent" || return 1
    [[ ! -e "$parent/.keep" && ! -L "$parent/.keep" ]] || return 1
    is_active "$parent" && return 1
    parent=${parent%/*}
  done
  [[ ! -e "$TEMP_ROOT/.keep" && ! -L "$TEMP_ROOT/.keep" ]] || return 1
}

remove_candidate() {
  local path="$1" identity
  if is_active "$path"; then
    SKIPPED_ACTIVE_COUNT=$((SKIPPED_ACTIVE_COUNT + 1))
    printf 'SKIP temporary cache (active): %q\n' "$path"
    return 0
  fi
  if ! is_safe_temp "$path"; then
    SKIPPED_UNSAFE_COUNT=$((SKIPPED_UNSAFE_COUNT + 1))
    printf 'SKIP temporary cache (safety/retention/mount/keep/parent-active): %q\n' "$path"
    return 0
  fi
  identity=$(stat -c '%d:%i:%s:%Y:%Z' -- "$path") || return 0
  snapshot_active_paths
  is_safe_temp "$path" || { SKIPPED_UNSAFE_COUNT=$((SKIPPED_UNSAFE_COUNT + 1)); return 0; }
  if [[ -d "$path" ]]; then
    # rmdir cannot remove evidence/content even if another process adds a file.
    rmdir -- "$path" || return 0
  else
    unlink_deliverable "$path" "$identity" || return 0
  fi
  printf 'REMOVED temporary cache: %q\n' "$path"
  REMOVED_COUNT=$((REMOVED_COUNT + 1))
}

list_temp_candidates() {
  local root="$1" path
  [[ "$root" == "$TEMP_ROOT" && -d "$root" && ! -L "$root" ]] || return 0
  [[ "$(realpath -e -- "$root")" == "$root" ]] || return 0
  [[ ! -e "$root/.keep" && ! -L "$root/.keep" ]] || return 0
  # Return aged, allowlisted entries including rejected ones; callers must
  # validate them. Otherwise the safety-skip count was always misleadingly zero.
  while IFS= read -r -d '' path; do
    printf '%s\0' "$path"
  done < <(
    find -P "$root" -xdev -mindepth 1 -maxdepth 1 -type d \
      -name '.org.chromium.Chromium.*' -mtime +"$TMP_KEEP_DAYS" -print0 2>/dev/null
    for path in "$root/node-compile-cache" "$root/tsx-0"; do
      [[ -d "$path" && ! -L "$path" ]] || continue
      find -P "$path" -xdev -maxdepth 4 \
        -type f -mtime +"$TMP_KEEP_DAYS" -print0 2>/dev/null
    done
  )
}

plan_temp_cleanup() {
  local path count=0 bytes=0 blocks detail=0 skipped=0
  while IFS= read -r -d '' path; do
    if is_safe_temp "$path"; then
      blocks=$(du -sk -- "$path" 2>/dev/null | awk '{print $1}')
      blocks=${blocks:-0}
      bytes=$((bytes + blocks * 1024))
      count=$((count + 1))
      if (( detail < PLAN_DETAIL_LIMIT )); then
        printf 'ELIGIBLE %s\n' "$path"
        detail=$((detail + 1))
      fi
    else
      skipped=$((skipped + 1))
      if (( skipped <= PLAN_DETAIL_LIMIT )); then printf 'SKIP temporary cache (safety/active/keep/mount): %q\n' "$path"; fi
    fi
  done < <(list_temp_candidates "$TEMP_ROOT")
  if (( count > detail )); then
    printf '... %s additional eligible entries omitted (PLAN_DETAIL_LIMIT=%s)\n' "$((count - detail))" "$PLAN_DETAIL_LIMIT"
  fi
  printf 'Eligible temporary entries: %s; skipped by safety checks: %s; estimated reclaim: %s\n' \
    "$count" "$skipped" "$(human_bytes "$bytes")"
}

clean_temp() {
  local path
  REMOVED_COUNT=0
  SKIPPED_UNSAFE_COUNT=0
  SKIPPED_ACTIVE_COUNT=0
  while IFS= read -r -d '' path; do
    recovery_reached && break
    remove_candidate "$path"
  done < <(list_temp_candidates "$TEMP_ROOT")
  printf 'Temporary cleanup: removed %s; skipped safety/mount/keep %s, active %s.\n' \
    "$REMOVED_COUNT" "$SKIPPED_UNSAFE_COUNT" "$SKIPPED_ACTIVE_COUNT"
}

# No cache tree deletion: inspect each old file and every parent, retain all dirs.
is_safe_npm_file() {
  local path="$1" root="$2" parent mount_target active
  [[ "$path" == "$root"/* && -f "$path" ]] || return 1
  is_safe_entry "$path" || return 1
  [[ "$(realpath -e -- "$path")" == "$path" && $(stat -c '%h' -- "$path") == 1 ]] || return 1
  is_protected_name "${path##*/}" && return 1
  [[ "${path##*/}" != .keep ]] || return 1
  [[ -n $(find -P "$path" -maxdepth 0 -mtime +"$TMP_KEEP_DAYS" -print) ]] || return 1
  mount_target=$(findmnt -rn -T "$path" -o TARGET) || return 1
  # Root-space recovery must not delete through an ancestor bind/separate mount.
  [[ "$mount_target" == / ]] || return 1
  is_active "$path" && return 1
  parent=${path%/*}
  while :; do
    is_safe_entry "$parent" || return 1
    [[ ! -e "$parent/.keep" && ! -L "$parent/.keep" ]] || return 1
    is_active "$parent" && return 1
    [[ "$parent" == "$root" ]] && break
    is_protected_name "${parent##*/}" && return 1
    parent=${parent%/*}
  done
}

list_npm_candidates() {
  local root="$1"
  [[ -d "$root" && ! -L "$root" && "$(realpath -e -- "$root")" == "$root" ]] || return 0
  find -P "$root" -xdev -maxdepth 12 -type f -mtime +"$TMP_KEEP_DAYS" -print0 2>/dev/null
}

clean_npm_caches() {
  local root path identity removed=0 skipped=0
  for root in "${NPM_CACHE_ROOTS[@]}"; do
    while IFS= read -r -d '' path; do
      recovery_reached && break
      snapshot_active_paths
      if ! is_safe_npm_file "$path" "$root"; then skipped=$((skipped + 1)); continue; fi
      identity=$(stat -c '%d:%i:%s:%Y:%Z' -- "$path") || continue
      is_safe_npm_file "$path" "$root" || { skipped=$((skipped + 1)); continue; }
      unlink_deliverable "$path" "$identity" || continue
      printf 'REMOVED NPM cache file: %q\n' "$path"
      removed=$((removed + 1))
    done < <(list_npm_candidates "$root")
  done
  printf 'NPM cache cleanup: removed %s files; skipped %s; all directories retained.\n' "$removed" "$skipped"
}

clean_basic_caches() {
  journalctl --vacuum-size=200M >/dev/null 2>&1 || true
  dnf clean all >/dev/null 2>&1 || yum clean all >/dev/null 2>&1 || true
  clean_npm_caches
}

is_safe_rotated_log() {
  local path="$1" parent mount_target active name="${1##*/}"
  [[ "$path" == "$LOG_ROOT"/* && -f "$path" ]] || return 1
  # Not every .gz is a log: never treat arbitrary archives/evidence as rotation.
  [[ "$name" =~ ^.+\.log(\.gz|\.[0-9]+(\.gz)?|\.[0-9]{8}T[0-9]{6}(\.gz)?)$ ]] || return 1
  is_deliverables_protected_name "$name" && return 1
  is_safe_entry "$path" || return 1
  [[ "$(realpath -e -- "$path")" == "$path" && $(stat -c '%h' -- "$path") == 1 ]] || return 1
  [[ -n $(find -P "$path" -maxdepth 0 -mtime +"$LOG_KEEP_DAYS" -print) ]] || return 1
  mount_target=$(findmnt -rn -T "$path" -o TARGET) || return 1
  # Root-space recovery must not delete through an ancestor bind/separate mount.
  [[ "$mount_target" == / ]] || return 1
  is_active "$path" && return 1
  parent=${path%/*}
  while :; do
    [[ -d "$parent" && ! -L "$parent" && ! -e "$parent/.keep" && ! -L "$parent/.keep" ]] || return 1
    for active in "${ACTIVE_PATHS[@]}"; do [[ "$active" != "$parent" ]] || return 1; done
    # The established shared log root is isp-owned/sticky; child dirs must be safe.
    [[ "$parent" == "$LOG_ROOT" ]] && break
    is_safe_deliverables_directory "$parent" || return 1
    is_deliverables_protected_name "${parent##*/}" && return 1
    parent=${parent%/*}
  done
}

list_rotated_logs() {
  [[ -d "$LOG_ROOT" && ! -L "$LOG_ROOT" && "$(realpath -e -- "$LOG_ROOT")" == "$LOG_ROOT" ]] || return 0
  find -P "$LOG_ROOT" -xdev -maxdepth 4 -type f -mtime +"$LOG_KEEP_DAYS" \
    \( -name '*.log.gz' -o -name '*.log.*' \) -print0 2>/dev/null
}

plan_cache_and_logs() {
  local root path count=0 skipped=0 bytes=0 blocks
  for root in "${NPM_CACHE_ROOTS[@]}"; do
    while IFS= read -r -d '' path; do
      if is_safe_npm_file "$path" "$root"; then
        blocks=$(stat -c '%b' -- "$path") || continue
        bytes=$((bytes + blocks * 512)); count=$((count + 1))
        if (( count <= PLAN_DETAIL_LIMIT )); then printf 'ELIGIBLE NPM cache %q\n' "$path"; fi
      else skipped=$((skipped + 1)); fi
    done < <(list_npm_candidates "$root")
  done
  printf 'Eligible NPM cache files: %s; skipped: %s; estimated reclaim: %s\n' "$count" "$skipped" "$(human_bytes "$bytes")"
  count=0; skipped=0; bytes=0
  while IFS= read -r -d '' path; do
    if is_safe_rotated_log "$path"; then
      blocks=$(stat -c '%b' -- "$path") || continue
      bytes=$((bytes + blocks * 512)); count=$((count + 1))
      if (( count <= PLAN_DETAIL_LIMIT )); then printf 'ELIGIBLE rotated log %q\n' "$path"; fi
    else skipped=$((skipped + 1)); fi
  done < <(list_rotated_logs)
  printf 'Eligible rotated logs: %s; skipped: %s; estimated reclaim: %s\n' "$count" "$skipped" "$(human_bytes "$bytes")"
}

clean_rotated_logs() {
  local path identity removed=0 skipped=0
  while IFS= read -r -d '' path; do
    recovery_reached && break
    snapshot_active_paths
    if ! is_safe_rotated_log "$path"; then skipped=$((skipped + 1)); continue; fi
    identity=$(stat -c '%d:%i:%s:%Y:%Z' -- "$path") || continue
    is_safe_rotated_log "$path" || { skipped=$((skipped + 1)); continue; }
    unlink_deliverable "$path" "$identity" || continue
    printf 'REMOVED rotated log: %q\n' "$path"
    removed=$((removed + 1))
  done < <(list_rotated_logs)
  printf 'Rotated log cleanup: removed %s; skipped %s.\n' "$removed" "$skipped"
}

# Deliverables are not disposable trees. Only generated archive/temp files are
# eligible; keep release payloads until a deployment-aware retention policy exists.
is_deliverables_protected_name() {
  is_protected_name "$1" && return 0
  case "${1,,}" in
    .*|releases|release|verification|maintenance|cleanup|diagnostics|records|design|*backup*|*rollback*|*report*|*source*|src|node_modules|vendor)
      return 0 ;;
  esac
  return 1
}

is_deliverables_candidate_name() {
  case "$1" in *.jar|*.zip|*.tgz|*.tar.gz|*.tmp|*.part) return 0 ;; esac
  return 1
}

# The existing deliverables root is root:root 0775. Permit root-group write on
# directories only; never relax the existing safety rule for candidate files.
is_safe_deliverables_directory() {
  local path="$1" uid gid mode
  [[ -d "$path" && ! -L "$path" ]] || return 1
  IFS='|' read -r uid gid mode < <(stat -c '%u|%g|%a' -- "$path") || return 1
  [[ "$uid" == 0 ]] || return 1
  (( (8#$mode & 8#002) == 0 )) || return 1
  (( (8#$mode & 8#020) == 0 )) || [[ "$gid" == 0 ]]
}

is_safe_deliverable() {
  local path="$1" parent active mount_target
  case "$path" in "$DELIVERABLES_ROOT"/*) ;; *) return 1 ;; esac
  [[ -f "$path" ]] && is_safe_entry "$path" || return 1
  is_deliverables_candidate_name "${path##*/}" || return 1
  is_deliverables_protected_name "${path##*/}" && return 1
  [[ "$(realpath -e -- "$path")" == "$path" ]] || return 1
  [[ $(stat -c '%h' -- "$path") == 1 ]] || return 1
  # Recheck age at deletion time, not only when the candidate list was built.
  [[ -n $(find -P "$path" -maxdepth 0 -type f -mtime +"$DELIVERABLES_KEEP_DAYS" -print) ]] || return 1
  mount_target=$(findmnt -rn -T "$path" -o TARGET) || return 1
  # Root-space recovery must not delete through an ancestor bind/separate mount.
  [[ "$mount_target" == / ]] || return 1
  is_active "$path" && return 1
  parent=${path%/*}
  while :; do
    is_safe_deliverables_directory "$parent" || return 1
    [[ ! -e "$parent/.keep" && ! -L "$parent/.keep" ]] || return 1
    for active in "${ACTIVE_PATHS[@]}"; do
      # A process working in any ancestor may still be producing these files.
      case "$active" in "$parent") return 1 ;; esac
    done
    [[ "$parent" == "$DELIVERABLES_ROOT" ]] && break
    is_deliverables_protected_name "${parent##*/}" && return 1
    parent=${parent%/*}
  done
}

list_deliverables_candidates() {
  local path
  [[ -d "$DELIVERABLES_ROOT" && ! -L "$DELIVERABLES_ROOT" ]] || return 0
  [[ "$(realpath -e -- "$DELIVERABLES_ROOT")" == "$DELIVERABLES_ROOT" ]] || return 0
  while IFS= read -r -d '' path; do
    if is_safe_deliverable "$path"; then printf '%s\0' "$path"; fi
  done < <(find -P "$DELIVERABLES_ROOT" -xdev -mindepth 1 \
    \( -type d \( -name '.*' -o -name releases -o -name release -o -name verification \
      -o -name maintenance -o -name cleanup -o -name diagnostics -o -name records \
      -o -name design -o -iname '*evidence*' -o -iname '*backup*' -o -iname '*rollback*' \
      -o -name src -o -name node_modules -o -name vendor \) -prune \) -o \
    \( -type f -mtime +"$DELIVERABLES_KEEP_DAYS" \
      \( -name '*.jar' -o -name '*.zip' -o -name '*.tgz' -o -name '*.tar.gz' \
         -o -name '*.tmp' -o -name '*.part' \) -print0 \) 2>/dev/null)
}

plan_deliverables_cleanup() {
  local path count=0 bytes=0 blocks
  while IFS= read -r -d '' path; do
    blocks=$(stat -c '%b' -- "$path") || continue
    bytes=$((bytes + blocks * 512))
    count=$((count + 1))
    if (( count <= PLAN_DETAIL_LIMIT )); then printf 'ELIGIBLE deliverable %q\n' "$path"; fi
  done < <(list_deliverables_candidates)
  printf 'Eligible deliverables files: %s; estimated reclaim: %s\n' "$count" "$(human_bytes "$bytes")"
}

# Workspace ancestors can be renamed by their owners. Walk with O_NOFOLLOW and
# unlink through the opened parent fd, only if the original file identity matches.
unlink_deliverable() {
  /usr/bin/python3 -I -B - "$1" "$2" <<'PYUNLINK'
import os
import stat
import sys

path, expected = sys.argv[1:]
fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
try:
    parts = path.split('/')[1:]
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise ValueError('invalid absolute path')
    for part in parts[:-1]:
        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        os.close(fd)
        fd = child
    st = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
    identity = '%d:%d:%d:%d:%d' % (st.st_dev, st.st_ino, st.st_size,
                                    int(st.st_mtime), int(st.st_ctime))
    if (identity != expected or not stat.S_ISREG(st.st_mode) or st.st_uid != 0
            or st.st_mode & 0o022 or st.st_nlink != 1):
        raise ValueError('deliverable changed before unlink')
    os.unlink(parts[-1], dir_fd=fd)
except (OSError, ValueError) as exc:
    print('SKIP deliverable: %s: %s' % (path, exc), file=sys.stderr)
    sys.exit(1)
finally:
    os.close(fd)
PYUNLINK
}

clean_deliverables() {
  local path identity count=0
  while IFS= read -r -d '' path; do
    recovery_reached && break
    identity=$(stat -c '%d:%i:%s:%Y:%Z' -- "$path") || continue
    # Refresh process use and safety immediately before each individual unlink.
    snapshot_active_paths
    is_safe_deliverable "$path" || continue
    unlink_deliverable "$path" "$identity" || continue
    printf 'REMOVED deliverable: %q\n' "$path"
    count=$((count + 1))
  done < <(list_deliverables_candidates)
  printf 'Deliverables cleanup: removed %s files; directories/releases/evidence preserved.\n' "$count"
}

run_flow() {
  [[ -x "$FLOW_CLEANUP" ]] || { echo "Missing Flow cleanup helper: $FLOW_CLEANUP" >&2; return 1; }
  /usr/bin/python3 -I -B "$FLOW_CLEANUP" "$1"
}

run_releases() {
  local mode="$1"
  [[ -r "$RELEASE_CLEANUP" ]] || { echo "Missing release cleanup helper: $RELEASE_CLEANUP" >&2; return 1; }
  if [[ "$mode" == clean ]]; then
    /usr/bin/python3 -I -B "$RELEASE_CLEANUP" clean --keep-days "$RELEASE_KEEP_DAYS" --target-gib "$RECOVERY_FREE_GB" --host-lock-fd 9
  else
    /usr/bin/python3 -I -B "$RELEASE_CLEANUP" plan --keep-days "$RELEASE_KEEP_DAYS" --target-gib "$RECOVERY_FREE_GB"
  fi
}

run_rebuildables() {
  local mode="$1"
  [[ -r "$REBUILDABLE_CLEANUP" ]] || { echo 'Missing rebuildable cache helper' >&2; return 1; }
  local args=("$mode" --cache-keep-days "$GRADLE_CACHE_KEEP_DAYS" --task-keep-hours "$COMPLETED_TASK_KEEP_HOURS" --target-gib "$RECOVERY_FREE_GB" --min-free-gib "$MIN_FREE_GB")
  [[ "$mode" == clean ]] && args+=(--host-lock-fd 9)
  /usr/bin/python3 -I -B "$REBUILDABLE_CLEANUP" "${args[@]}"
}

run_runtime_backups() {
  local mode="$1"
  [[ -r "$RUNTIME_BACKUP_CLEANUP" ]] || { echo 'Missing Runtime backup cleanup helper' >&2; return 1; }
  local args=("$mode")
  [[ "$mode" == clean ]] && args+=(--host-lock-fd 9)
  /usr/bin/python3 -I -B "$RUNTIME_BACKUP_CLEANUP" "${args[@]}"
}

main() {
  case "$MODE" in
    check)
      print_status
      echo
      run_flow check
      ;;
    plan)
      print_status
      snapshot_active_paths
      echo
      echo '== Runtime recovery-payload retention plan =='
      run_runtime_backups plan || echo 'WARNING: Runtime backup plan stopped safely.' >&2
      echo '== Flow retention plan =='
      run_flow plan || echo 'WARNING: Flow plan unavailable; showing independent temporary/deliverables plan.' >&2
      echo
      echo '== Old temporary release payload plan =='
      run_releases plan || echo 'WARNING: release plan stopped safely; see reason above.' >&2
      echo
      echo "== Expired temporary artifacts (>${TMP_KEEP_DAYS} days) =="
      plan_temp_cleanup
      echo
      echo "== Expired deliverables files (>${DELIVERABLES_KEEP_DAYS} days; releases/evidence excluded) =="
      plan_deliverables_cleanup
      echo
      echo '== Rebuildable caches and explicitly completed task dependencies/final packages =='
      run_rebuildables plan || echo 'WARNING: rebuildable plan stopped safely.' >&2
      echo '== Expired NPM cache files and rotated logs =='
      plan_cache_and_logs
      ;;
    clean)
      [[ $(id -u) == 0 ]] || { echo 'clean mode must run as root' >&2; exit 1; }
      install -d -m 0755 /run/lock
      exec 9>"$LOCK_FILE"
      flock -n 9 || { echo 'Another host cleanup is running; exit'; exit 0; }
      background_cleanup_priority || { echo 'Cannot lower cleanup scheduling priority; no retention started.' >&2; return 4; }
      # Do not let a recursive diagnostic du delay low-space recovery or hold
      # the cleanup lock for minutes before the retention stages even start.
      echo '== Filesystem before retention =='
      df -hT /
      echo
      echo '== Flow retention =='
      local stage_failed=0
      if ! run_flow clean; then stage_failed=1; echo 'WARNING: Flow retention failed/stopped safely; inspect cleanup log.' >&2; fi
      echo '== Runtime recovery-payload retention =='
      if ! run_runtime_backups clean; then stage_failed=1; echo 'WARNING: Runtime backup cleanup stopped safely.' >&2; fi
      if ! needs_cleanup; then
        echo 'Free-space trigger is not met; no generic temporary cleanup is needed.'
        (( stage_failed == 0 )) || return 4
        return 0
      fi
      snapshot_active_paths
      echo '== Basic caches =='
      clean_basic_caches
      recovery_reached || { echo '== Rebuildable caches and completed task dependencies/final packages =='; if ! run_rebuildables clean; then stage_failed=1; echo 'WARNING: rebuildable cleanup failed/stopped safely.' >&2; fi; }
      recovery_reached || { echo '== Old temporary release payloads =='; if ! run_releases clean; then stage_failed=1; echo 'WARNING: release cleanup failed/stopped safely; protected payloads preserved.' >&2; fi; }
      recovery_reached || { echo '== Expired temporary cache files/empty directories =='; clean_temp; }
      recovery_reached || { echo '== Expired deliverables files =='; clean_deliverables; }
      recovery_reached || { echo '== Old rotated logs =='; clean_rotated_logs; }
      echo
      echo '== Filesystem after retention =='
      df -hT /
      # Recursive du belongs to explicit check/plan, never a lock-holding
      # automatic clean epilogue on this IO-constrained shared host.
      if ! needs_cleanup; then
        echo 'Minimum free-space target restored.'
        (( stage_failed == 0 )) || return 4
      else
        echo 'WARNING: still below the automatic target; protected data was not touched.' >&2
        return 3
      fi
      ;;
    -h|--help|help) usage ;;
    *) usage >&2; exit 2 ;;
  esac
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main; fi
