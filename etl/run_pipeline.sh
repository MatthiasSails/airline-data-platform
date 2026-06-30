#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"


while true; do
    echo "[$(date)] Running pipeline..."
    if ! python3 bronze.py || ! python3 silver.py; then
        echo "[$(date)] Pipeline iteration failed — see pipeline.log, retrying next cycle."
    fi
    echo "[$(date)] Done. Sleeping 45s..."
    sleep 45
done
