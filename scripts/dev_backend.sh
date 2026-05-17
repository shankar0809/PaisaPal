#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

UV_BIN="${UV_BIN:-$(command -v uv || true)}"
if [ -z "$UV_BIN" ]; then
  UV_BIN="/Users/shankars/Library/Python/3.9/bin/uv"
fi
"$UV_BIN" run uvicorn paisapal.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
