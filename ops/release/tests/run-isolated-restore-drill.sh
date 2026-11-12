#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
INPUT="$ROOT/ops/release/m2-c08-input.json"
EVIDENCE_ROOT="${1:-$ROOT/deliverables/m2-c08-20260822/isolated-restore-drill}"
RUN="$(mktemp -d /tmp/cyf-m2-c08-restore-drill.XXXXXX)"
SANDBOX="$RUN/sandbox"
mkdir -p "$SANDBOX/api" "$SANDBOX/web/kit/static" "$SANDBOX/baks/legacy-api" "$SANDBOX/baks/legacy-web" "$RUN/evidence" "$RUN/build"

cleanup() {
  python3 - "$RUN" <<'PY' >/dev/null 2>&1 || true
import shutil, sys
shutil.rmtree(sys.argv[1], ignore_errors=True)
PY
}
trap cleanup EXIT

for command in bash unshare mount ip javac jar openssl python3 sha256sum curl ss; do
  command -v "$command" >/dev/null 2>&1 || { echo "missing command: $command" >&2; exit 2; }
done

cat > "$RUN/build/HealthMain.java" <<'JAVA'
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
public final class HealthMain {
  private static void respond(HttpExchange exchange, int code, String body) throws IOException {
    byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
    exchange.getResponseHeaders().set("Content-Type", "application/json");
    exchange.sendResponseHeaders(code, bytes.length);
    exchange.getResponseBody().write(bytes);
    exchange.close();
  }
  public static void main(String[] args) throws Exception {
    HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 10018), 16);
    server.createContext("/actuator/health", exchange -> respond(exchange, 200, "{\"status\":\"UP\",\"source\":\"isolated-old\"}"));
    server.createContext("/", exchange -> respond(exchange, 404, "{\"status\":\"NOT_FOUND\"}"));
    server.start();
    Thread.currentThread().join();
  }
}
JAVA
javac -d "$RUN/build/classes" "$RUN/build/HealthMain.java"
printf 'Main-Class: HealthMain\n' > "$RUN/build/MANIFEST.MF"
jar cfm "$SANDBOX/api/cyf-api-kit.jar" "$RUN/build/MANIFEST.MF" -C "$RUN/build/classes" .
OLD_API_SHA="$(sha256sum "$SANDBOX/api/cyf-api-kit.jar" | awk '{print $1}')"

cat > "$SANDBOX/web/kit/index.html" <<'HTML'
<!doctype html><html><head><script type="module" src="/static/index-old.js"></script></head><body>isolated-old</body></html>
HTML
printf 'console.log("isolated-old");\n' > "$SANDBOX/web/kit/static/index-old.js"

cat > "$RUN/openssl.cnf" <<'OPENSSL'
[req]
distinguished_name=dn
x509_extensions=v3
prompt=no
[dn]
CN=kit.chaoyoufan.cn
[v3]
subjectAltName=DNS:kit.chaoyoufan.cn
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
basicConstraints=critical,CA:FALSE
OPENSSL
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -keyout "$RUN/tls.key" -out "$RUN/tls.crt" -config "$RUN/openssl.cnf" >/dev/null 2>&1

cat > "$RUN/https_server.py" <<'PY'
import http.server, os, socketserver, ssl, sys
root, cert, key = sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        raw = super().translate_path(path)
        rel = os.path.relpath(raw, os.getcwd())
        target = os.path.join(root, rel)
        if os.path.isfile(target):
            return target
        return os.path.join(root, 'index.html')
    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)
os.chdir(root)

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
server = Server(('127.0.0.1', 443), Handler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(cert, key)
server.socket = ctx.wrap_socket(server.socket, server_side=True)
server.serve_forever()
PY

cat > "$RUN/hosts" <<'HOSTS'
127.0.0.1 localhost kit.chaoyoufan.cn
::1 localhost
HOSTS

cat > "$RUN/driver.sh" <<'DRIVER'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077
mount --make-rprivate /
ip link set lo up
mount --bind "$SANDBOX/api" /home/isp/hosts/cyf/api
mount --bind "$SANDBOX/web" /home/isp/hosts/cyf/web
mount --bind "$SANDBOX/baks" /home/isp/baks
mount --bind "$RUN/hosts" /etc/hosts
touch "$RUN/api-execution.lock" "$RUN/web-execution.lock"
mount --bind "$RUN/api-execution.lock" /tmp/cyf-release-api.lock
if [[ -e /tmp/cyf-release-web.lock ]]; then
  mount --bind "$RUN/web-execution.lock" /tmp/cyf-release-web.lock
else
  touch /tmp/cyf-release-web.lock
  mount --bind "$RUN/web-execution.lock" /tmp/cyf-release-web.lock
fi
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
export NO_PROXY='127.0.0.1,localhost,kit.chaoyoufan.cn'
export no_proxy="$NO_PROXY"
mkdir -p /home/isp/baks/legacy-api /home/isp/hosts/cyf/api/logs /home/isp/baks/legacy-web

cleanup_inner() {
  set +e
  [[ -z "${WEB_PID:-}" ]] || kill "$WEB_PID" 2>/dev/null
  [[ -z "${API_PID:-}" ]] || kill "$API_PID" 2>/dev/null
  local current_mnt_ns pid pid_mnt_ns
  current_mnt_ns="$(readlink /proc/self/ns/mnt 2>/dev/null || true)"
  for pid in $(find /proc -maxdepth 1 -type d -name '[0-9]*' -printf '%f\n' 2>/dev/null); do
    [[ -r "/proc/$pid/cmdline" ]] || continue
    pid_mnt_ns="$(readlink "/proc/$pid/ns/mnt" 2>/dev/null || true)"
    [[ -n "$current_mnt_ns" && "$pid_mnt_ns" == "$current_mnt_ns" ]] || continue
    if tr '\0' ' ' < "/proc/$pid/cmdline" | grep -Fq '/home/isp/hosts/cyf/api/cyf-api-kit.jar'; then
      kill "$pid" 2>/dev/null
    fi
  done
}
trap cleanup_inner EXIT

ip route show > "$EVIDENCE/network-routes.txt"
[[ ! -s "$EVIDENCE/network-routes.txt" ]] || { echo 'isolated namespace unexpectedly has a route' >&2; exit 20; }
ss -lntp > "$EVIDENCE/listeners-before.txt"

CURL_CA_BUNDLE="$RUN/tls.crt" python3 "$RUN/https_server.py" \
  /home/isp/hosts/cyf/web/kit "$RUN/tls.crt" "$RUN/tls.key" \
  > "$EVIDENCE/https-server.log" 2>&1 &
WEB_PID=$!

(
  cd /home/isp/hosts/cyf/api
  /home/isp/apps/jdk21/bin/java -jar /home/isp/hosts/cyf/api/cyf-api-kit.jar \
    --spring.config.location=file:/home/isp/hosts/cyf/api/required-missing.properties \
    > logs/isolated-old.log 2>&1
) &
API_PID=$!
printf '%s\n' "$API_PID" > /home/isp/hosts/cyf/api/cyf-api-kit.pid

for _ in {1..30}; do
  curl --fail --silent --max-time 2 http://127.0.0.1:10018/actuator/health > "$EVIDENCE/api-old-health-before.json" 2>/dev/null && break
  sleep 1
done
[[ -s "$EVIDENCE/api-old-health-before.json" ]] || { echo 'old isolated API did not start' >&2; exit 21; }
for _ in {1..30}; do
  CURL_CA_BUNDLE="$RUN/tls.crt" curl --fail --silent --show-error --max-time 2 https://kit.chaoyoufan.cn/ > "$EVIDENCE/web-old-before.html" 2> "$EVIDENCE/web-old-curl.err" && break
  kill -0 "$WEB_PID" 2>/dev/null || break
  sleep 1
done
if ! grep -Fq '/static/index-old.js' "$EVIDENCE/web-old-before.html"; then
  echo 'old isolated Web did not start' >&2
  cat "$EVIDENCE/https-server.log" >&2 || true
  cat "$EVIDENCE/web-old-curl.err" >&2 || true
  exit 22
fi

export CYF_RELEASE_APPROVED=YES
export CYF_RELEASE_APPROVAL_ID=c08-isolated-drill
export CYF_RELEASE_APPROVED_API_HEAD=e45ba398f116a210091c892abb9fbc8111dcc411
export CYF_RELEASE_APPROVED_API_TREE=8b80bf35c418b2ca0cead919f805db5bb70166eb
export CYF_RELEASE_APPROVED_WEB_HEAD=266583f2e59d5f1362ed4d653f58d02b78a0e6b5
export CYF_RELEASE_APPROVED_WEB_TREE=ba7ed4f167c43b3af8a7f07d34d626308496cd36
export CURL_CA_BUNDLE="$RUN/tls.crt"

set +e
"$ROOT/ops/release/deploy-api.sh" --input "$INPUT" --execute \
  > "$EVIDENCE/api-deploy-failure-restore.log" 2>&1
API_DEPLOY_STATUS=$?
set -e
printf '%s\n' "$API_DEPLOY_STATUS" > "$EVIDENCE/api-deploy-status.txt"
(( API_DEPLOY_STATUS != 0 )) || { echo 'API failure drill unexpectedly deployed candidate' >&2; exit 23; }
if ! grep -Fq 'deployment failed; attempting automatic API artifact/runtime restore' \
  "$EVIDENCE/api-deploy-failure-restore.log"; then
  echo 'API automatic restore was not invoked' >&2
  cat "$EVIDENCE/api-deploy-failure-restore.log" >&2 || true
  exit 24
fi
ACTUAL_OLD_SHA="$(sha256sum /home/isp/hosts/cyf/api/cyf-api-kit.jar | awk '{print $1}')"
[[ "$ACTUAL_OLD_SHA" == "$OLD_API_SHA" ]] || { echo 'old API JAR was not restored' >&2; exit 25; }
for _ in {1..30}; do
  curl --fail --silent --max-time 2 http://127.0.0.1:10018/actuator/health > "$EVIDENCE/api-old-health-after.json" 2>/dev/null && break
  sleep 1
done
grep -Fq 'isolated-old' "$EVIDENCE/api-old-health-after.json" || { echo 'old API runtime was not restored' >&2; exit 26; }
API_PID="$(cat /home/isp/hosts/cyf/api/cyf-api-kit.pid)"
find /home/isp/baks/legacy-api/releases -maxdepth 2 -type f -printf '%m %s %p\n' \
  | sort > "$EVIDENCE/api-backup-inventory.txt"
find /home/isp/baks/legacy-api/releases -type f -name '*.sha256' -print0 \
  | xargs -0 -r -n1 sh -c 'cd "$(dirname "$1")" && sha256sum -c "$(basename "$1")"' _ \
  > "$EVIDENCE/api-backup-sidecars.txt"

"$ROOT/ops/release/deploy-web.sh" --input "$INPUT" --execute \
  > "$EVIDENCE/web-deploy.log" 2>&1
WEB_DEPLOY_RECORD="$(sed -n 's/^DEPLOY_RECORD=//p' "$EVIDENCE/web-deploy.log")"
[[ -n "$WEB_DEPLOY_RECORD" && -f "$WEB_DEPLOY_RECORD" ]] || { echo 'Web deploy record missing' >&2; exit 27; }
CURL_CA_BUNDLE="$RUN/tls.crt" curl --fail --silent --max-time 5 https://kit.chaoyoufan.cn/ \
  > "$EVIDENCE/web-candidate-before-rollback.html"
grep -Eq '/static/index-[A-Za-z0-9_-]+\.js' "$EVIDENCE/web-candidate-before-rollback.html" \
  || { echo 'candidate Web was not activated' >&2; exit 28; }

"$ROOT/ops/release/rollback-web.sh" --input "$INPUT" --execute "$WEB_DEPLOY_RECORD" \
  > "$EVIDENCE/web-rollback.log" 2>&1
CURL_CA_BUNDLE="$RUN/tls.crt" curl --fail --silent --max-time 5 https://kit.chaoyoufan.cn/ \
  > "$EVIDENCE/web-old-after-rollback.html"
grep -Fq '/static/index-old.js' "$EVIDENCE/web-old-after-rollback.html" \
  || { echo 'old Web was not restored' >&2; exit 29; }

find /home/isp/baks/legacy-web -maxdepth 3 -type f -printf '%m %s %p\n' \
  | sort > "$EVIDENCE/web-backup-record-inventory.txt"
find /home/isp/baks/legacy-web -type f -name '*.sha256' -print0 \
  | xargs -0 -r -n1 sh -c 'cd "$(dirname "$1")" && sha256sum -c "$(basename "$1")"' _ \
  > "$EVIDENCE/web-record-sidecars.txt"
ss -ntp > "$EVIDENCE/network-connections-after.txt"
if rg -n ':(3306|33060|5672|6379|9200|9300)\b' "$EVIDENCE/network-connections-after.txt"; then
  echo 'forbidden dependency connection observed in isolated drill' >&2
  exit 30
fi

git -C "$ROOT/.worktrees/m2-api-base" status --porcelain=v1 --untracked-files=all \
  > "$EVIDENCE/api-candidate-status-after.txt"
git -C "$ROOT/.worktrees/m2-web-base" status --porcelain=v1 --untracked-files=all \
  > "$EVIDENCE/web-candidate-status-after.txt"
[[ ! -s "$EVIDENCE/api-candidate-status-after.txt" && ! -s "$EVIDENCE/web-candidate-status-after.txt" ]] \
  || { echo 'candidate worktree changed during drill' >&2; exit 31; }

printf 'ISOLATED_API_FAILURE_RESTORE=PASS\nISOLATED_WEB_DEPLOY_ROLLBACK=PASS\nPRODUCTION_DB_OPERATION=NOT_PERFORMED\nPRODUCTION_DEPLOYMENT=NOT_PERFORMED\n' \
  > "$EVIDENCE/result.txt"
(
  cd "$EVIDENCE"
  find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256
)
DRIVER
chmod +x "$RUN/driver.sh"

OLD_API_SHA="$OLD_API_SHA" ROOT="$ROOT" INPUT="$INPUT" RUN="$RUN" SANDBOX="$SANDBOX" \
  EVIDENCE="$RUN/evidence" unshare -m -n -- env \
  OLD_API_SHA="$OLD_API_SHA" ROOT="$ROOT" INPUT="$INPUT" RUN="$RUN" SANDBOX="$SANDBOX" \
  EVIDENCE="$RUN/evidence" bash "$RUN/driver.sh"

python3 - "$RUN/evidence" "$EVIDENCE_ROOT" <<'PY'
import os, shutil, sys
source, target = sys.argv[1:]
if os.path.exists(target):
    raise SystemExit(f'evidence target already exists: {target}')
os.makedirs(os.path.dirname(target), exist_ok=True)
shutil.copytree(source, target)
PY
printf 'ISOLATED_RESTORE_DRILL=PASS\nEVIDENCE=%s\n' "$EVIDENCE_ROOT"
