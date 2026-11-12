#!/usr/bin/env bash
# Trusted helpers for the repository-local H06 isolated gate.  This file is
# sourced by the outer runner and by its mount/network namespace drivers.

h06_secure_create_run() {
  python3 - "$1" "$2" "${3:-${H06_WORKER_UID:-61006}}" "${4:-${H06_WORKER_GID:-61006}}" <<'PY'
import json, os, re, stat, sys
root, run_id, worker_uid, worker_gid = sys.argv[1:]
worker_uid, worker_gid = int(worker_uid), int(worker_gid)
marker_name = '.cyf-h06-evidence-root.json'
marker_data = (json.dumps({
    'purpose': 'CYF_H06_ISOLATED_EVIDENCE_ROOT',
    'schema': 'cyf-h06-evidence-root-v1',
}, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')
if os.geteuid() != 0: raise SystemExit('evidence allocation requires root')
if not os.path.isabs(root) or os.path.normpath(root) != root:
    raise SystemExit(f'evidence root must be one normalized absolute path: {root}')
if not re.fullmatch(r'/var/tmp/cyf-h06(?:-[A-Za-z0-9][A-Za-z0-9._-]{0,63})?', root):
    raise SystemExit(f'evidence root is outside the approved single-level /var/tmp/cyf-h06[-SUFFIX] prefix: {root}')
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', run_id): raise SystemExit('invalid evidence run ID')

def worker_bits(st):
    if worker_uid == st.st_uid: return (st.st_mode >> 6) & 7
    if worker_gid == st.st_gid: return (st.st_mode >> 3) & 7
    return st.st_mode & 7

def open_dir(parent_fd, name, label):
    try: st = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError: raise SystemExit(f'{label} is missing')
    if stat.S_ISLNK(st.st_mode): raise SystemExit(f'{label} is a symlink')
    if not stat.S_ISDIR(st.st_mode): raise SystemExit(f'{label} is not a directory')
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)

def verify_marker(rootfd):
    try: st = os.stat(marker_name, dir_fd=rootfd, follow_symlinks=False)
    except FileNotFoundError: return False
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise SystemExit('evidence root marker is not a physical regular file')
    markerfd = os.open(marker_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=rootfd)
    try:
        st = os.fstat(markerfd)
        if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o444 or st.st_nlink != 1:
            raise SystemExit('evidence root marker must be root:root mode 0444 with one link')
        chunks = []
        while True:
            block = os.read(markerfd, 4096)
            if not block: break
            chunks.append(block)
        if b''.join(chunks) != marker_data: raise SystemExit('evidence root marker content is not exact')
    finally:
        os.close(markerfd)
    return True

def create_marker(rootfd):
    markerfd = None
    try:
        markerfd = os.open(marker_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=rootfd)
        os.fchown(markerfd, 0, 0)
        offset = 0
        while offset < len(marker_data): offset += os.write(markerfd, marker_data[offset:])
        os.fsync(markerfd)
        os.fchmod(markerfd, 0o444)
        os.fsync(markerfd)
    except Exception:
        if markerfd is not None: os.close(markerfd); markerfd = None
        try: os.unlink(marker_name, dir_fd=rootfd)
        except OSError: pass
        raise
    finally:
        if markerfd is not None: os.close(markerfd)
    os.fsync(rootfd)
    if not verify_marker(rootfd): raise SystemExit('evidence root marker creation was not durable')

slashfd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
varfd = tmpfd = rootfd = None
root_created = False
temp = None
root_name = os.path.basename(root)
try:
    varfd = open_dir(slashfd, 'var', '/var')
    vst = os.fstat(varfd)
    if vst.st_uid != 0 or vst.st_gid != 0 or vst.st_mode & 0o022:
        raise SystemExit('/var ownership/mode is unsafe')
    tmpfd = open_dir(varfd, 'tmp', '/var/tmp')
    tst = os.fstat(tmpfd)
    if tst.st_uid != 0 or tst.st_gid != 0 or not (tst.st_mode & stat.S_ISVTX):
        raise SystemExit('/var/tmp must be a physical root:root sticky directory')
    try:
        rst = os.stat(root_name, dir_fd=tmpfd, follow_symlinks=False)
        if stat.S_ISLNK(rst.st_mode): raise SystemExit(f'evidence root is a symlink: {root}')
        if not stat.S_ISDIR(rst.st_mode): raise SystemExit(f'evidence root is not a directory: {root}')
    except FileNotFoundError:
        os.mkdir(root_name, 0o700, dir_fd=tmpfd)
        root_created = True
    rootfd = os.open(root_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=tmpfd)
    if root_created:
        os.fchown(rootfd, 0, 0)
        os.fchmod(rootfd, 0o711)
        os.fsync(rootfd); os.fsync(tmpfd)
    rst = os.fstat(rootfd)
    if rst.st_uid != 0 or rst.st_gid != 0 or stat.S_IMODE(rst.st_mode) != 0o711:
        raise SystemExit(f'existing evidence root must already be root:root mode 0711; it is never chmod/chowned: {root}')
    bits = worker_bits(rst)
    if not bits & 1 or bits & 2: raise SystemExit(f'evidence root worker traversal/write boundary failed for UID {worker_uid}: {root}')
    if not verify_marker(rootfd):
        entries = os.listdir(rootfd)
        if entries:
            raise SystemExit(f'existing evidence root has no exact marker and is not empty; refusing migration: {root}')
        create_marker(rootfd)
    temp = '.h06-inprogress-' + run_id
    final = run_id
    for name in (temp, final):
        try: os.stat(name, dir_fd=rootfd, follow_symlinks=False)
        except FileNotFoundError: pass
        else: raise SystemExit(f'evidence run path already exists: {os.path.join(root,name)}')
    os.mkdir(temp, 0o700, dir_fd=rootfd)
    runfd = os.open(temp, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=rootfd)
    try:
        os.fchown(runfd, 0, 0); os.fchmod(runfd, 0o711)
        st = os.fstat(runfd); bits = worker_bits(st)
        if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o711:
            raise SystemExit('temporary evidence run must be root:root mode 0711')
        if not bits & 1 or bits & 2:
            raise SystemExit(f'temporary evidence run traversal/write boundary failed for UID {worker_uid}')
        os.fsync(runfd)
    finally:
        os.close(runfd)
    os.fsync(rootfd)
    print(os.path.join(root, temp))
except Exception:
    if root_created and rootfd is not None:
        if temp is not None:
            try: os.rmdir(temp, dir_fd=rootfd)
            except OSError: pass
        try: os.unlink(marker_name, dir_fd=rootfd)
        except OSError: pass
        try:
            if not os.listdir(rootfd):
                os.close(rootfd); rootfd = None
                os.rmdir(root_name, dir_fd=tmpfd); os.fsync(tmpfd)
        except Exception: pass
    raise
finally:
    for fd in (rootfd, tmpfd, varfd, slashfd):
        if fd is not None:
            try: os.close(fd)
            except OSError: pass
PY
}

h06_secure_publish_run() {
  python3 - "$1" "$2" "$3" <<'PY'
import json,os,re,stat,sys
root,temp_name,final_name=sys.argv[1:]
marker_name='.cyf-h06-evidence-root.json'
marker_data=(json.dumps({'purpose':'CYF_H06_ISOLATED_EVIDENCE_ROOT','schema':'cyf-h06-evidence-root-v1'},ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
if os.geteuid()!=0: raise SystemExit('evidence publish requires root')
if not os.path.isabs(root) or os.path.normpath(root)!=root or not re.fullmatch(r'/var/tmp/cyf-h06(?:-[A-Za-z0-9][A-Za-z0-9._-]{0,63})?',root):
 raise SystemExit('invalid or unapproved evidence root')
rootfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
try:
 st=os.fstat(rootfd)
 if st.st_uid!=0 or st.st_gid!=0 or stat.S_IMODE(st.st_mode)!=0o711: raise SystemExit('evidence root ownership/mode changed from root:root 0711')
 mst=os.stat(marker_name,dir_fd=rootfd,follow_symlinks=False)
 if stat.S_ISLNK(mst.st_mode) or not stat.S_ISREG(mst.st_mode): raise SystemExit('evidence root marker changed type')
 markerfd=os.open(marker_name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=rootfd)
 try:
  mst=os.fstat(markerfd); data=b''
  while True:
   block=os.read(markerfd,4096)
   if not block: break
   data+=block
  if mst.st_uid!=0 or mst.st_gid!=0 or stat.S_IMODE(mst.st_mode)!=0o444 or mst.st_nlink!=1 or data!=marker_data:
   raise SystemExit('evidence root marker ownership/mode/content changed')
 finally: os.close(markerfd)
 src=os.path.basename(temp_name); dst=os.path.basename(final_name)
 if temp_name!=os.path.join(root,src) or final_name!=os.path.join(root,dst): raise SystemExit('evidence publish paths are not normalized root children')
 st=os.stat(src,dir_fd=rootfd,follow_symlinks=False)
 if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or st.st_gid!=0 or stat.S_IMODE(st.st_mode)!=0o555:
  raise SystemExit('sealed evidence run must be root:root mode 0555 before publish')
 try: os.stat(dst,dir_fd=rootfd,follow_symlinks=False)
 except FileNotFoundError: pass
 else: raise SystemExit('final evidence run already exists')
 renamed=False
 try:
  os.rename(src,dst,src_dir_fd=rootfd,dst_dir_fd=rootfd); renamed=True; os.fsync(rootfd)
 except Exception:
  if renamed:
   try: os.rename(dst,src,src_dir_fd=rootfd,dst_dir_fd=rootfd); os.fsync(rootfd)
   except Exception: pass
  raise
finally: os.close(rootfd)
PY
}

h06_path_is_physical() {
  [[ -e "$1" || -L "$1" ]] || return 1
  [[ ! -L "$1" ]]
}

h06_proc_identity() {
  local pid="$1" stat_line end rest start exe
  [[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 && -r "/proc/$pid/stat" ]] || return 1
  stat_line="$(cat "/proc/$pid/stat")" || return 1
  end="${stat_line##*)}"; rest="${end# }"
  start="$(awk '{print $20}' <<<"$rest")"
  exe="$(readlink -f -- "/proc/$pid/exe")" || return 1
  printf '%s\t%s\n' "$start" "$exe"
}

h06_track_pid() {
  local registry="$1" label="$2" pid="$3" expected_exe="$4" identity start exe
  expected_exe="$(readlink -f -- "$expected_exe")"
  for _ in {1..100}; do
    identity="$(h06_proc_identity "$pid" 2>/dev/null || true)"
    if [[ -n "$identity" ]]; then
      IFS=$'\t' read -r start exe <<<"$identity"
      if [[ "$exe" == "$expected_exe" ]]; then printf '%s\t%s\t%s\t%s\n' "$label" "$pid" "$start" "$exe" >> "$registry"; return 0; fi
    fi
    sleep 0.02
  done
  echo "$label executable mismatch/unavailable expected=$expected_exe pid=$pid actual=${exe:-missing}" >&2
  return 1
}

h06_pid_matches() {
  local pid="$1" expected_start="$2" expected_exe="$3" identity start exe
  identity="$(h06_proc_identity "$pid" 2>/dev/null)" || return 1
  IFS=$'\t' read -r start exe <<<"$identity"
  [[ "$start" == "$expected_start" && "$exe" == "$expected_exe" ]]
}

h06_stop_tracked_pids() {
  local registry="$1" label pid start exe
  [[ -f "$registry" && ! -L "$registry" ]] || return 0
  while IFS=$'\t' read -r label pid start exe; do
    h06_pid_matches "$pid" "$start" "$exe" && kill -TERM "$pid" 2>/dev/null || true
  done < <(tac "$registry")
  for _ in {1..50}; do
    local alive=0
    while IFS=$'\t' read -r label pid start exe; do h06_pid_matches "$pid" "$start" "$exe" && alive=1; done < "$registry"
    ((alive == 0)) && break
    sleep 0.1
  done
  while IFS=$'\t' read -r label pid start exe; do
    h06_pid_matches "$pid" "$start" "$exe" && kill -KILL "$pid" 2>/dev/null || true
  done < <(tac "$registry")
  wait 2>/dev/null || true
}

h06_safe_remove_run_local() {
  local run="$1" path="$2"
  [[ "$run" == /* && "$path" == "$run"/* ]] || { echo "refusing non-run-local cleanup: $path" >&2; return 1; }
  [[ -e "$path" || -L "$path" ]] || return 0
  rm -rf --one-file-system -- "$path"
}

h06_assert_root_owned_chain() {
  python3 - "$1" "$2" <<'PYSAFE'
import os,stat,sys
path,label=sys.argv[1:]
if not os.path.isabs(path): raise SystemExit(f'{label} path is not absolute')
try: st=os.lstat(path)
except FileNotFoundError: raise SystemExit(f'{label} is missing: {path}')
if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode): raise SystemExit(f'{label} is not a physical regular file: {path}')
cur=path
while True:
 st=os.lstat(cur)
 if stat.S_ISLNK(st.st_mode): raise SystemExit(f'{label} parent chain contains symlink: {cur}')
 if st.st_uid != 0 or st.st_mode & 0o022: raise SystemExit(f'{label} parent chain is not root-owned immutable: {cur}')
 if cur=='/': break
 cur=os.path.dirname(cur)
PYSAFE
}

h06_verify_sha256() {
  local path="$1" expected="$2" label="$3" actual
  [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || { echo "$label expected SHA-256 is invalid" >&2; return 1; }
  [[ -f "$path" && ! -L "$path" ]] || { echo "$label is not a physical regular file: $path" >&2; return 1; }
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "$label SHA-256 mismatch expected=$expected actual=$actual" >&2; return 1; }
}

h06_tree_digest() {
  python3 - "$1" <<'PYTREE'
import hashlib,os,pathlib,stat,sys
root=pathlib.Path(sys.argv[1]); h=hashlib.sha256()
if root.is_symlink() or not root.is_dir(): raise SystemExit('tree root is not a physical directory')
for p in sorted(root.rglob('*'),key=lambda x:x.relative_to(root).as_posix().encode()):
 rel=p.relative_to(root).as_posix().encode(); st=os.lstat(p)
 if stat.S_ISLNK(st.st_mode): h.update(b'L\0'+rel+b'\0'+os.readlink(p).encode()+b'\0')
 elif stat.S_ISREG(st.st_mode): h.update(b'F\0'+rel+b'\0'+oct(st.st_mode&0o777).encode()+b'\0'+hashlib.sha256(p.read_bytes()).hexdigest().encode()+b'\0')
 elif stat.S_ISDIR(st.st_mode): h.update(b'D\0'+rel+b'\0')
 else: raise SystemExit(f'special filesystem object in tree: {p}')
print(h.hexdigest())
PYTREE
}

h06_reject_special_files() {
  python3 - "$1" <<'PYSPECIAL'
import os,pathlib,stat,sys
root=pathlib.Path(sys.argv[1]); bad=[]
for p in root.rglob('*'):
 st=os.lstat(p)
 if stat.S_ISLNK(st.st_mode) or not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)): bad.append(str(p.relative_to(root)))
if bad:
 print('SPECIAL_OR_SYMLINK_OBJECTS=FAIL')
 for item in bad: print(item)
 raise SystemExit(1)
print('SPECIAL_OR_SYMLINK_OBJECTS=PASS')
PYSPECIAL
}

h06_worker_exec() {
  local uid="${H06_WORKER_UID:?}" gid="${H06_WORKER_GID:?}"
  setpriv --reuid="$uid" --regid="$gid" --clear-groups --no-new-privs "$@"
}


h06_worker_traversal_probe() {
  local target="$1" evidence_root="$2" run="$3"
  h06_worker_exec python3 - "$target" "$evidence_root" "$run" <<'PYTRAVERSE'
import os,pathlib,stat,sys
target,evidence_root,run=map(os.path.normpath,sys.argv[1:])
for label,value in (('target',target),('evidence_root',evidence_root),('run',run)):
 if not os.path.isabs(value): raise SystemExit(f'{label} is not absolute: {value}')
if target != run and not target.startswith(run + os.sep): raise SystemExit('driver is outside the run directory')
components=['/']
current='/'
for part in pathlib.PurePath(target).parts[1:]:
 current=os.path.join(current,part); components.append(current)
for index,path in enumerate(components):
 try: st=os.lstat(path)
 except OSError as exc:
  print(f'TRAVERSAL=FAIL PATH={path} ERROR={exc}',flush=True); raise SystemExit(1)
 if stat.S_ISLNK(st.st_mode):
  print(f'TRAVERSAL=FAIL PATH={path} ERROR=SYMLINK',flush=True); raise SystemExit(1)
 if index < len(components)-1:
  if not stat.S_ISDIR(st.st_mode):
   print(f'TRAVERSAL=FAIL PATH={path} ERROR=NOT_DIRECTORY',flush=True); raise SystemExit(1)
  if not os.access(path,os.X_OK):
   print(f'TRAVERSAL=FAIL PATH={path} ERROR=NO_EXECUTE',flush=True); raise SystemExit(1)
  print(f'TRAVERSAL_COMPONENT={path} EXECUTE=PASS',flush=True)
 else:
  if not stat.S_ISREG(st.st_mode) or not os.access(path,os.R_OK|os.X_OK):
   print(f'TRAVERSAL=FAIL PATH={path} ERROR=DRIVER_NOT_READ_EXECUTE',flush=True); raise SystemExit(1)
  print(f'DRIVER={path} READ_EXECUTE=PASS',flush=True)
for label,path in (('EVIDENCE_ROOT',evidence_root),('RUN',run)):
 if not os.access(path,os.X_OK):
  print(f'TRAVERSAL=FAIL PATH={path} ERROR={label}_NO_EXECUTE',flush=True); raise SystemExit(1)
 if os.access(path,os.W_OK):
  print(f'TRAVERSAL=FAIL PATH={path} ERROR={label}_WRITABLE',flush=True); raise SystemExit(1)
 if os.access(path,os.R_OK):
  print(f'TRAVERSAL=FAIL PATH={path} ERROR={label}_LISTABLE',flush=True); raise SystemExit(1)
 print(f'{label}={path} EXECUTE=PASS WRITE=DENIED LIST=DENIED',flush=True)
print('TRAVERSAL_PREFLIGHT=PASS',flush=True)
PYTRAVERSE
}

h06_start_mysql() {
  local run="$1" port="$2" database="$3" registry="$4"
  local root="${H06_MYSQL_ROOT:?trusted staged MySQL root required}"
  local mysqld="$root/bin/mysqld" mysql="$root/bin/mysql" mysqladmin="$root/bin/mysqladmin"
  local datadir="$run/private/mysql" socket="$run/private/mysql.sock" pidfile="$run/private/mysql.pid"
  local records="${H06_STAGE_RECORDS:-$run/records}" logs="${H06_STAGE_LOGS:-$run/logs}"
  for p in "$mysqld" "$mysql" "$mysqladmin"; do [[ -x "$p" && -f "$p" && ! -L "$p" ]] || return 11; done
  [[ "$port" =~ ^[0-9]+$ && "$port" -ne 3306 && "$port" -ne 33060 ]] || return 11
  mkdir -p "$run/private" "$datadir" "$logs" "$records"
  chmod 0700 "$run/private" "$datadir" "$logs"
  "$mysqld" --initialize-insecure --datadir="$datadir" --lower-case-table-names=1 --log-error="$logs/mysql-init.log"
  "$mysqld" --no-defaults --datadir="$datadir" --socket="$socket" --pid-file="$pidfile" \
    --port="$port" --bind-address=127.0.0.1 --skip-name-resolve --mysqlx=0 --lower-case-table-names=1 \
    --performance-schema=OFF --innodb-buffer-pool-size=64M --key-buffer-size=8M --max-connections=30 \
    --log-bin-trust-function-creators=1 --log-error="$logs/mysql-server.log" &
  H06_MYSQL_PID=$!; export H06_MYSQL_PID H06_MYSQL_SOCKET="$socket" H06_MYSQL_DATABASE="$database" H06_MYSQL_PORT="$port"
  h06_track_pid "$registry" mysql "$H06_MYSQL_PID" "$mysqld"
  for _ in {1..120}; do "$mysqladmin" --protocol=socket --socket="$socket" ping >/dev/null 2>&1 && break; sleep 0.25; done
  "$mysqladmin" --protocol=socket --socket="$socket" ping >/dev/null
  "$mysql" --protocol=socket --socket="$socket" -uroot -N -B -e 'SELECT VERSION(),@@version_compile_machine,@@port,@@mysqlx_port,@@lower_case_table_names,@@datadir' > "$records/mysql-server-identity.txt"
  grep -Eq $'^8\.0\.21\t.*\t' "$records/mysql-server-identity.txt" || return 12
  grep -Fq $'\t'"$port"$'\t0\t1\t'"$datadir/" "$records/mysql-server-identity.txt" || return 12
  [[ "$(readlink -f "/proc/$H06_MYSQL_PID/exe")" == "$(readlink -f "$mysqld")" ]] || return 12
  sha256sum "$mysqld" "$mysql" "$mysqladmin" > "$records/mysql-binary-sha256.txt"
  "$mysql" --protocol=socket --socket="$socket" -uroot -e "CREATE DATABASE \`$database\` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
}

h06_start_redis() {
  local run="$1" port="$2" registry="$3"
  local root="${H06_REDIS_ROOT:?trusted staged Redis root required}" server="$root/bin/redis-server" cli="$root/bin/redis-cli"
  [[ -x "$server" && -f "$server" && ! -L "$server" && -x "$cli" && -f "$cli" && ! -L "$cli" ]] || return 13
  local logs="${H06_STAGE_LOGS:-$run/logs}"
  mkdir -p "$run/private/redis" "$logs"
  cat > "$run/private/redis.conf" <<EOFREDIS
bind 127.0.0.1
port $port
requirepass h06-redis-secret
save ""
appendonly no
daemonize no
dir $run/private/redis
EOFREDIS
  chmod 0700 "$run/private/redis"; chmod 0600 "$run/private/redis.conf"
  "$server" "$run/private/redis.conf" > "$logs/redis.log" 2>&1 &
  H06_REDIS_PID=$!; export H06_REDIS_PID H06_REDIS_PORT="$port"
  h06_track_pid "$registry" redis "$H06_REDIS_PID" "$server"
  for _ in {1..80}; do printf 'AUTH h06-redis-secret\r\nPING\r\n' | "$cli" -h 127.0.0.1 -p "$port" --raw 2>/dev/null | grep -qx PONG && return 0; sleep 0.25; done
  return 13
}

# Import one quiescent UID61006 output tree into a root-only evidence directory.
# The source is revoked before copy; all traversal and copying is fd-relative and
# no-follow. Only physical directories and single-link regular files are accepted.
h06_import_worker_output() {
  python3 - "$1" "$2" "${3:-${H06_WORKER_UID:-61006}}" "${4:-${H06_WORKER_GID:-61006}}" <<'PYIMPORT'
import os, stat, sys
src, dst, worker_uid, worker_gid = sys.argv[1:]
worker_uid, worker_gid = int(worker_uid), int(worker_gid)
if os.geteuid() != 0: raise SystemExit('worker output import requires root')
for label,path in (('source',src),('destination',dst)):
 if not os.path.isabs(path) or os.path.normpath(path) != path: raise SystemExit(f'{label} path is not normalized absolute: {path}')
if os.path.commonpath([src,dst]) in (src,dst): raise SystemExit('worker output source/destination must be disjoint')

def open_dir(path,label):
 try: st=os.lstat(path)
 except OSError as exc: raise SystemExit(f'{label} lstat failed: {path}: {exc}')
 if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode): raise SystemExit(f'{label} is not a physical directory: {path}')
 return os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)

def entries(fd):
 return sorted(os.listdir(fd),key=lambda name:name.encode())

def validate(fd,rel='.'):
 st=os.fstat(fd)
 if not stat.S_ISDIR(st.st_mode): raise SystemExit(f'worker output directory changed type: {rel}')
 if st.st_uid not in (worker_uid,0) or st.st_gid not in (worker_gid,0): raise SystemExit(f'worker output directory owner is foreign: {rel}')
 for entry in entries(fd):
  st=os.stat(entry,dir_fd=fd,follow_symlinks=False); child=entry if rel=='.' else rel+'/'+entry
  if stat.S_ISLNK(st.st_mode): raise SystemExit(f'worker output symlink rejected: {child}')
  if stat.S_ISDIR(st.st_mode):
   childfd=os.open(entry,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
   try: validate(childfd,child)
   finally: os.close(childfd)
  elif stat.S_ISREG(st.st_mode):
   if st.st_nlink != 1: raise SystemExit(f'worker output multi-link file rejected: {child} links={st.st_nlink}')
   if st.st_uid not in (worker_uid,0) or st.st_gid not in (worker_gid,0): raise SystemExit(f'worker output file owner is foreign: {child}')
  else: raise SystemExit(f'worker output special object rejected: {child} mode={oct(st.st_mode)}')

def revoke(fd):
 for entry in entries(fd):
  st=os.stat(entry,dir_fd=fd,follow_symlinks=False)
  if stat.S_ISDIR(st.st_mode):
   childfd=os.open(entry,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
   try: revoke(childfd); os.fchown(childfd,0,0); os.fchmod(childfd,0o500); os.fsync(childfd)
   finally: os.close(childfd)
  else:
   filefd=os.open(entry,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
   try:
    before=os.fstat(filefd)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1: raise SystemExit(f'worker output file changed before revoke: {entry}')
    os.fchown(filefd,0,0); os.fchmod(filefd,0o400); os.fsync(filefd)
   finally: os.close(filefd)
 os.fchown(fd,0,0); os.fchmod(fd,0o500); os.fsync(fd)

def copy_tree(sfd,dfd,rel='.'):
 for entry in entries(sfd):
  st=os.stat(entry,dir_fd=sfd,follow_symlinks=False); child=entry if rel=='.' else rel+'/'+entry
  if stat.S_ISDIR(st.st_mode):
   os.mkdir(entry,0o700,dir_fd=dfd)
   cs=os.open(entry,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=sfd)
   cd=os.open(entry,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=dfd)
   try: copy_tree(cs,cd,child); os.fchmod(cd,0o500); os.fsync(cd)
   finally: os.close(cd); os.close(cs)
  elif stat.S_ISREG(st.st_mode):
   sf=os.open(entry,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=sfd)
   try:
    before=os.fstat(sf)
    if before.st_nlink!=1: raise SystemExit(f'worker output multi-link file appeared during import: {child}')
    df=os.open(entry,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o400,dir_fd=dfd)
    try:
     while True:
      block=os.read(sf,1024*1024)
      if not block: break
      view=memoryview(block)
      while view: view=view[os.write(df,view):]
     os.fsync(df); os.fchmod(df,0o400); os.fchown(df,0,0)
    finally: os.close(df)
    after=os.fstat(sf)
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
     raise SystemExit(f'worker output changed during import: {child}')
   finally: os.close(sf)
  else: raise SystemExit(f'worker output changed type during import: {child}')
 os.fsync(dfd)

sfd=open_dir(src,'worker output source')
try:
 validate(sfd); revoke(sfd); validate(sfd)
 parent=os.path.dirname(dst); name=os.path.basename(dst); pfd=open_dir(parent,'root evidence destination parent')
 try:
  pst=os.fstat(pfd)
  if pst.st_uid!=0 or pst.st_gid!=0 or pst.st_mode&0o022: raise SystemExit(f'root evidence destination parent must be root-owned and non-group/world-writable: {parent}')
  try: os.stat(name,dir_fd=pfd,follow_symlinks=False)
  except FileNotFoundError: pass
  else: raise SystemExit(f'worker output destination collision rejected: {dst}')
  os.mkdir(name,0o700,dir_fd=pfd); dfd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=pfd)
  try:
   try: copy_tree(sfd,dfd); os.fchown(dfd,0,0); os.fchmod(dfd,0o500); os.fsync(dfd)
   except Exception:
    os.close(dfd); dfd=None
    raise
  finally:
   if dfd is not None: os.close(dfd)
  os.fsync(pfd)
 finally: os.close(pfd)
finally: os.close(sfd)
print(f'WORKER_OUTPUT_IMPORT=PASS SOURCE={src} DESTINATION={dst}')
PYIMPORT
}
