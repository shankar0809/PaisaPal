#!/usr/bin/env bash
set -euo pipefail
uv run uvicorn paisapal.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
