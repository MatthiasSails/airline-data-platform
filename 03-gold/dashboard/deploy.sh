#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "${REPO_DIR}/.env"

SSH_HOST="ubuntu@63.185.229.117"
SSH_KEY="$HOME/.ssh/airline_vm"
REMOTE_DIR="~/airline-data-platform"

ssh -i "$SSH_KEY" "$SSH_HOST" bash <<REMOTE
  set -e
  if [ ! -d "$REMOTE_DIR" ]; then
    git clone https://github.com/MatthiasSails/airline-data-platform.git $REMOTE_DIR
  fi
  git -C $REMOTE_DIR fetch origin
  git -C $REMOTE_DIR reset --hard origin/main
  echo "MONGO_URI='${MONGO_URI}'" > $REMOTE_DIR/.env
  cd $REMOTE_DIR/deployment
  docker compose up -d --build
REMOTE

echo "Done — http://63.185.229.117:8501"
