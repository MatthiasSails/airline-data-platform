#!/usr/bin/env bash
# Flips the q-gold-dash Portainer stack's IMAGE_TAG env var and redeploys it
# via git/redeploy. Called from both GitHub Actions (build-push.yml's
# deploy-q job, q-reset.yml) and, for debugging, a human at the terminal —
# same script either way, so a CI failure can be reproduced and fixed
# locally instead of only guessed at from workflow logs.
#
# Required env: PORTAINER_URL, PORTAINER_API_KEY, PORTAINER_Q_ENDPOINT_ID,
# PORTAINER_Q_STACK_ID. In CI these are GitHub repo secrets; locally, export
# them yourself (PORTAINER_API_KEY from the macOS Keychain — see
# CLAUDE.local.md "Q environment").
#
# Usage: set-q-image-tag.sh <tag>   e.g. set-q-image-tag.sh pr-42
set -euo pipefail

TAG="${1:?Usage: set-q-image-tag.sh <tag>}"
: "${PORTAINER_URL:?}" "${PORTAINER_API_KEY:?}" "${PORTAINER_Q_ENDPOINT_ID:?}" "${PORTAINER_Q_STACK_ID:?}"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# git/redeploy REPLACES the stack's whole Env array — always fetch it first
# and patch only the field we need, never construct an env array from
# scratch. (Incident 2026-07-03: a bare env:[] test call crash-looped
# gold_api for ~30s until DATABASE_URL was restored.)
STATUS=$(curl -s -o "$TMPDIR/stack.json" -w "%{http_code}" \
  -A "curl/8.0" -H "X-API-Key: $PORTAINER_API_KEY" \
  "$PORTAINER_URL/api/stacks/$PORTAINER_Q_STACK_ID")
if [ "$STATUS" != "200" ]; then
  echo "GET stack failed with HTTP $STATUS" >&2
  exit 1
fi

NEW_ENV=$(jq --arg tag "$TAG" \
  '.Env | map(if .name == "IMAGE_TAG" then .value = $tag else . end)' \
  "$TMPDIR/stack.json")

# git/redeploy is PUT, not POST, on Portainer 2.42 — verified 2026-07-03
# against the live server (POST returns 405, undocumented at the time).
STATUS=$(curl -s -o "$TMPDIR/redeploy.json" -w "%{http_code}" \
  -A "curl/8.0" -H "X-API-Key: $PORTAINER_API_KEY" -H "Content-Type: application/json" \
  -X PUT "$PORTAINER_URL/api/stacks/$PORTAINER_Q_STACK_ID/git/redeploy?endpointId=$PORTAINER_Q_ENDPOINT_ID" \
  -d "{\"env\": $NEW_ENV, \"pullImage\": true}")
if [ "$STATUS" != "200" ]; then
  echo "Redeploy failed with HTTP $STATUS" >&2
  exit 1
fi

echo "q-gold-dash stack redeployed with IMAGE_TAG=$TAG (HTTP $STATUS)"
