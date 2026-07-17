#!/usr/bin/env bash
# Flips the IMAGE_TAG env var of every Q Portainer stack and redeploys them via
# git/redeploy. Called from both GitHub Actions (build-push.yml's deploy-q job,
# q-reset.yml) and, for debugging, a human at the terminal — same script either
# way, so a CI failure can be reproduced and fixed locally instead of only
# guessed at from workflow logs.
#
# Q runs the full pipeline (bronze + silver + both dashboards), so a PR deploy
# has to move every stack's tag, not just gold-dash's — otherwise Q would mix a
# PR's API with main's ETL and prove nothing. Stack ids come from
# PORTAINER_Q_STACK_IDS (comma-separated); q-cloudflared is deliberately absent,
# it pins a cloudflared release and has no IMAGE_TAG.
#
# Required env: PORTAINER_URL, PORTAINER_API_KEY, PORTAINER_Q_ENDPOINT_ID,
# PORTAINER_Q_STACK_IDS (e.g. "17,20,21,22"). In CI these are GitHub repo
# secrets; locally, export them yourself (PORTAINER_API_KEY from the macOS
# Keychain — see CLAUDE.local.md "Q environment").
#
# Usage: set-q-image-tag.sh <tag>   e.g. set-q-image-tag.sh pr-42
set -euo pipefail

TAG="${1:?Usage: set-q-image-tag.sh <tag>}"
: "${PORTAINER_URL:?}" "${PORTAINER_API_KEY:?}" "${PORTAINER_Q_ENDPOINT_ID:?}"
# Back-compat: accept the old single-stack variable if the plural one is unset.
STACK_IDS="${PORTAINER_Q_STACK_IDS:-${PORTAINER_Q_STACK_ID:?PORTAINER_Q_STACK_IDS (or legacy PORTAINER_Q_STACK_ID) required}}"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

FAILED=0

IFS=',' read -ra IDS <<< "$STACK_IDS"
for ID in "${IDS[@]}"; do
  ID="${ID// /}"
  [ -z "$ID" ] && continue

  # git/redeploy REPLACES the stack's whole Env array — always fetch it first
  # and patch only the field we need, never construct an env array from
  # scratch. (Incident 2026-07-03: a bare env:[] test call crash-looped
  # gold_api for ~30s until DATABASE_URL was restored.)
  STATUS=$(curl -s -o "$TMPDIR/stack.json" -w "%{http_code}" \
    -A "curl/8.0" -H "X-API-Key: $PORTAINER_API_KEY" \
    "$PORTAINER_URL/api/stacks/$ID")
  if [ "$STATUS" != "200" ]; then
    echo "stack $ID: GET failed with HTTP $STATUS" >&2
    FAILED=1
    continue
  fi

  NAME=$(jq -r '.Name' "$TMPDIR/stack.json")

  # Only touch stacks that actually declare IMAGE_TAG. Adding it to a stack whose
  # compose never references it would be harmless but misleading, and silently
  # skipping tells us the id list drifted from reality.
  if ! jq -e '.Env | map(.name) | index("IMAGE_TAG")' "$TMPDIR/stack.json" >/dev/null; then
    echo "stack $ID ($NAME): no IMAGE_TAG in env — skipped" >&2
    continue
  fi

  NEW_ENV=$(jq --arg tag "$TAG" \
    '.Env | map(if .name == "IMAGE_TAG" then .value = $tag else . end)' \
    "$TMPDIR/stack.json")

  # git/redeploy is PUT, not POST, on Portainer 2.42 — verified 2026-07-03
  # against the live server (POST returns 405, undocumented at the time).
  STATUS=$(curl -s -o "$TMPDIR/redeploy.json" -w "%{http_code}" \
    -A "curl/8.0" -H "X-API-Key: $PORTAINER_API_KEY" -H "Content-Type: application/json" \
    -X PUT "$PORTAINER_URL/api/stacks/$ID/git/redeploy?endpointId=$PORTAINER_Q_ENDPOINT_ID" \
    -d "{\"env\": $NEW_ENV, \"pullImage\": true}")
  if [ "$STATUS" != "200" ]; then
    echo "stack $ID ($NAME): redeploy failed with HTTP $STATUS" >&2
    FAILED=1
    continue
  fi

  echo "stack $ID ($NAME): redeployed with IMAGE_TAG=$TAG"
done

exit "$FAILED"
