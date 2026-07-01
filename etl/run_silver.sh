#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

while true; do
    echo "[$(date)] Running silver..."
    if ! python3 silver.py; then
        echo "[$(date)] silver.py failed — see pipeline.log, retrying next cycle."
    fi
    touch heartbeat
    echo "[$(date)] Done. Sleeping 10s..."
    sleep 10
done
