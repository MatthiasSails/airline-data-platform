#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Longer interval than run_silver.sh (20s): the historical warehouse does not need
# live-map cadence, and every run wakes Redshift Serverless (billed per RPU-hour while
# active). 15 min keeps the workgroup mostly idle while still capturing history — see
# ADR 020. The incremental watermark means each run only processes new Bronze docs.
#
# heartbeat is touched only on success, so the healthcheck marks the container unhealthy
# when loads fail persistently (watermark stops advancing), not just when the loop hangs.
while true; do
    echo "[$(date)] Running silver_history..."
    if python3 silver_history.py; then
        touch heartbeat_history
    else
        echo "[$(date)] silver_history.py failed — see the log lines above, retrying next cycle."
    fi
    echo "[$(date)] Done. Sleeping 900s..."
    sleep 900
done
