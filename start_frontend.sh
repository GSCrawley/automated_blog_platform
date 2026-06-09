#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/blog-frontend"

cd "$FRONTEND_DIR"

# Keep frontend API target aligned with local backend default.
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:5000/api}"

npm run dev