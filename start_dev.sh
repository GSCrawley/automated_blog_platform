#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SCRIPT="$SCRIPT_DIR/start_backend.sh"
FRONTEND_SCRIPT="$SCRIPT_DIR/start_frontend.sh"
BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://127.0.0.1:5000/api/blog/dashboard/stats}"

if [[ ! -x "$BACKEND_SCRIPT" ]]; then
  chmod +x "$BACKEND_SCRIPT"
fi
if [[ ! -x "$FRONTEND_SCRIPT" ]]; then
  chmod +x "$FRONTEND_SCRIPT"
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

"$BACKEND_SCRIPT" &
BACKEND_PID=$!

for _ in {1..30}; do
  if curl -fsS "$BACKEND_HEALTH_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$BACKEND_HEALTH_URL" >/dev/null 2>&1; then
  echo "Backend did not become healthy at $BACKEND_HEALTH_URL"
  exit 1
fi

"$FRONTEND_SCRIPT"
