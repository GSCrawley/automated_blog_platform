#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/automated-blog-system"

cd "$BACKEND_DIR"
source venv/bin/activate

# Keep default aligned with frontend API fallback.
PORT="${PORT:-5000}"
python src/main.py --port "$PORT"