#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

cd "$ROOT_DIR/frontend"

if [[ ! -d "node_modules" ]]; then
  npm install
fi

export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"

npm run dev -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
