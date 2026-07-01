#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

while true; do
    echo "[$(date)] Running bronze..."
    if ! python3 bronze.py; then
        echo "[$(date)] bronze.py failed — see pipeline.log, retrying next cycle."
    fi
    touch heartbeat
    echo "[$(date)] Done. Sleeping 50s..."
    sleep 50
done
