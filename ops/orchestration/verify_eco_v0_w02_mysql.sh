#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT=/home/isp/wsps/cyf
WT="$ROOT/.worktrees/eco-v0-api"
ORCH="$ROOT/ops/orchestration/cyf_orchestrator.py"
MYSQL=/home/isp/apps/mysql/bin/mysql
SOCKET=/home/isp/apps/mysql/mysql.sock
TASK=ECO-V0-W02
COMMIT=dff38cb99e5905c6d5cc2577ab51106c30d3a465
TREE=079e695ffe05ef57e5e7b1227f4cfd2733509d69
SELECTOR=economy-core+mapper+service:test-r5-mysql-ephemeral-user
FIXTURE=277ca789224cba5012f4320c782c054e4adf61b01b77a91c783cb0872d6406ac
ARTIFACT=/var/tmp/eco-v0-w02-r5-verify-20260902.txt
DB_PREFIX=eco_w02_verify_
USER_NAME="eco_w02v_$(date +%s)_$$"
PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
RUN_RC=99

mysql_root() {
  "$MYSQL" --protocol=socket --socket="$SOCKET" -uroot --batch --skip-column-names "$@"
}

cleanup() {
  local original_rc=$?
  trap - EXIT
  set +e
  mysql_root -e "DROP USER IF EXISTS '${USER_NAME}'@'127.0.0.1'" >/dev/null 2>&1
  local user_drop_rc=$?
  local db_left user_left
  db_left="$(mysql_root -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE LEFT(SCHEMA_NAME, CHAR_LENGTH('${DB_PREFIX}'))='${DB_PREFIX}'" 2>/dev/null)"
  user_left="$(mysql_root -e "SELECT COUNT(*) FROM mysql.user WHERE User='${USER_NAME}' AND Host='127.0.0.1'" 2>/dev/null)"
  printf 'W02_FIXTURE_CLEANUP user_drop_rc=%s db_left=%s user_left=%s\n' "$user_drop_rc" "${db_left:-query_failed}" "${user_left:-query_failed}"
  if [[ "$user_drop_rc" -ne 0 || "${db_left:-1}" != 0 || "${user_left:-1}" != 0 ]]; then
    exit 97
  fi
  exit "$original_rc"
}
trap cleanup EXIT

[[ "$(git -C "$WT" rev-parse HEAD)" == "$COMMIT" ]]
[[ "$(git -C "$WT" rev-parse HEAD^{tree})" == "$TREE" ]]
[[ -z "$(git -C "$WT" status --short)" ]]
[[ "$(mysql_root -e 'SELECT VERSION()')" == 8.0.21* ]]
[[ "$(mysql_root -e 'SELECT @@port')" == 3306 ]]
[[ "$(mysql_root -e 'SELECT @@datadir')" == /home/isp/apps/mysql/data/ ]]
[[ "$(mysql_root -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE LEFT(SCHEMA_NAME, CHAR_LENGTH('${DB_PREFIX}'))='${DB_PREFIX}'")" == 0 ]]
[[ "$(mysql_root -e "SELECT COUNT(*) FROM mysql.user WHERE LEFT(User, CHAR_LENGTH('eco_w02v_'))='eco_w02v_' AND Host='127.0.0.1'")" == 0 ]]

mysql_root <<SQL
CREATE USER '${USER_NAME}'@'127.0.0.1' IDENTIFIED BY '${PASSWORD}';
GRANT CREATE, DROP, SELECT, INSERT, UPDATE, DELETE, ALTER, INDEX, REFERENCES,
      CREATE TEMPORARY TABLES, LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW,
      CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER
ON *.* TO '${USER_NAME}'@'127.0.0.1';
SQL

export ECO_V0_W02_MYSQL_URL='jdbc:mysql://127.0.0.1:3306/?useUnicode=true&characterEncoding=utf8&useSSL=false&allowPublicKeyRetrieval=true'
export ECO_V0_W02_MYSQL_USER="$USER_NAME"
export ECO_V0_W02_MYSQL_PASSWORD="$PASSWORD"
export ECO_V0_W02_MYSQL_ISOLATED_FIXTURE=true
export ECO_V0_W02_MYSQL_DATABASE_PREFIX=eco_w02_verify
export ECO_V0_W02_MYSQL_EXPECTED_PORT=3306
export ECO_V0_W02_MYSQL_EXPECTED_DATADIR=/home/isp/apps/mysql/data/

set +e
python3 "$ORCH" gradle \
  --cwd "$WT" \
  --tree-sha "$TREE" \
  --selector "$SELECTOR" \
  --fixture-digest "$FIXTURE" \
  --artifact "$ARTIFACT" \
  "$TASK" \
  "$WT/gradlew" \
  -PrepoUsername=unused -PrepoPassword=unused \
  :economy:jia-economy-core:test \
  :economy:jia-economy-mapper:test \
  :economy:jia-economy-service:test \
  --stacktrace >"$ARTIFACT" 2>&1
RUN_RC=$?
set -e
cat "$ARTIFACT"
exit "$RUN_RC"
