#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# heartbeat is only touched on success, so the healthcheck (deployment/bronze.yml)
# marks the container unhealthy when runs fail persistently, not just when the loop
# hangs. Caveat: bronze.py exits 0 even when individual fetches fail (per-source
# errors are caught and logged inside) — only total failures (Mongo/env) exit non-zero.
while true; do
    echo "[$(date)] Running bronze..."
    if python3 bronze.py; then
        touch heartbeat
    else
        echo "[$(date)] bronze.py failed — see the log lines above, retrying next cycle."
    fi
    echo "[$(date)] Done. Sleeping 2s..."
    sleep 2
done
