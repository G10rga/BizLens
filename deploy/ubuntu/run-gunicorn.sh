#!/usr/bin/env bash
# Foreground gunicorn (useful for smoke tests)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source .venv/bin/activate
set -a
# shellcheck disable=SC1091
source .env
set +a

PORT="${PORT:-8000}"
exec gunicorn \
  --chdir backend \
  run:app \
  --bind "127.0.0.1:${PORT}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${WEB_THREADS:-4}" \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
