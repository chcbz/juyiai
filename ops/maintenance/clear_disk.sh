#!/bin/bash
# Compatibility entry for /etc/crontab; no builds, broad pruning, or space quotas.
# The running host entry additionally has independent bounded cache/log stages.
set -Eeuo pipefail
MODE="${1:-check}"
rc=0
/usr/bin/python3 -I -B /usr/local/libexec/cyf/flow_host_cleanup.py "$MODE" || rc=$?
case "$MODE" in
  plan|clean)
    /usr/bin/python3 -I -B /usr/local/libexec/cyf/runtime_backup_cleanup.py "$MODE" || rc=4
    ;;
esac
exit "$rc"
