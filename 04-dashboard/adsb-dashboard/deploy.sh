#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "${REPO_DIR}/.env"
ssh Liora_VM "cd ~/airline-data-platform 2>/dev/null || git clone https://github.com/MatthiasSails/airline-data-platform.git ~/airline-data-platform && git -C ~/airline-data-platform fetch origin && git -C ~/airline-data-platform reset --hard origin/main && cd ~/airline-data-platform/04-dashboard/adsb-dashboard && MONGO_URI='${MONGO_URI}' docker compose up -d --build"
echo "Done — http://liora-vm.matthiaskoehler.com:8502"
