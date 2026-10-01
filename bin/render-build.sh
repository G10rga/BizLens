#!/usr/bin/env bash
# Render build: Python deps + React SPA
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Python $(python --version 2>&1)"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Building React SPA"
npm --prefix web ci || npm --prefix web install
npm --prefix web run build

echo "==> Verifying SPA build"
test -f web/dist/index.html
ls -la web/dist | head
echo "==> Build complete"
