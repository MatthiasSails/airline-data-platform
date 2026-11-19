#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Cadence is bounded by adsb.lol's quota, not by how fresh we would like the map to be.
# The API allows 500 requests/day per client IP, advertised per response as
# `x-ratelimit-limit: 500, 500;w=86400` — one request every 86400/500 = 173s.
# At the previous 30s sleep bronze asked for ~2100/day: it burned the daily quota in
# under 6h and then collected HTTP 429 (`x-envoy-ratelimited: true`,
# `x-ratelimit-remaining: 0`) for the remaining ~18h, writing nothing.
#
# 180s gives 86400/180 = 480 requests/day, leaving 20 for manual probing. The window is
# a fixed UTC day: the `resets in` value counts down to 00:00Z. The earlier 170s asked
# for ~508/day: on a full day the quota would run dry around 23:37Z (500 x 170s after
# midnight, computed, not observed) and the map would freeze until the reset.
#
# Note the quota is per IP: a Docker bridge network egresses over IPv4, so the
# container shares the host's IPv4 budget and nothing else. Moving the container to
# IPv6 egress only buys a second 500/day budget, it does not raise the rate.
#
# Override per environment via BRONZE_SLEEP_SECONDS (set in the Portainer stack env).
SLEEP_SECONDS="${BRONZE_SLEEP_SECONDS:-180}"

# heartbeat is only touched on success, so the healthcheck (deployment/bronze.yml)
# marks the container unhealthy when runs fail persistently, not just when the loop
# hangs. Caveat: bronze.py exits 0 even when individual fetches fail (per-source
# errors are caught and logged inside) — only total failures (Mongo/env) exit non-zero.
# That healthcheck window must stay larger than this sleep plus one run duration.
echo "[$(date)] bronze loop starting, image built from commit ${GIT_SHA:-unknown}"
while true; do
    echo "[$(date)] Running bronze..."
    if python3 bronze.py; then
        touch heartbeat
    else
        echo "[$(date)] bronze.py failed — see the log lines above, retrying next cycle."
    fi
    echo "[$(date)] Done. Sleeping ${SLEEP_SECONDS}s..."
    sleep "$SLEEP_SECONDS"
done
