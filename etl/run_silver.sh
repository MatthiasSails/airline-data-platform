#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# heartbeat is only touched on success, so the healthcheck (deployment/silver.yml)
# marks the container unhealthy when refreshes fail persistently (map1 going stale),
# not just when the loop hangs.
while true; do
    echo "[$(date)] Running silver..."
    if python3 silver.py; then
        touch heartbeat
    else
        echo "[$(date)] silver.py failed — see the log lines above, retrying next cycle."
    fi
    echo "[$(date)] Done. Sleeping 2s..."
    sleep 2
done
