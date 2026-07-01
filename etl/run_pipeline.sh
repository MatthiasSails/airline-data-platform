#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[$(date)] Running pipeline..."
python3 bronze.py && python3 silver.py
echo "[$(date)] Done."