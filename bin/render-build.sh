#!/usr/bin/env bash
# Render build: Python deps + React SPA
set -euo pipefail

echo "==> Python $(python --version)"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Building React SPA"
cd web
# Need Vite (devDependency) at build time — do not use --omit=dev here
npm ci || npm install
npm run build
cd ..

echo "==> Verifying SPA build"
test -f web/dist/index.html
echo "==> Build complete"
