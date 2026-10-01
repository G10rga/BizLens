#!/usr/bin/env bash
# Render start — use from the Start Command field:
#   bash bin/render-start.sh
set -euo pipefail

cd "$(dirname "$0")/.."

exec gunicorn \
  --chdir backend \
  run:app \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 \
  --threads 4 \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
