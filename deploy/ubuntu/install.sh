#!/usr/bin/env bash
# Install / update BizLens on Ubuntu (app only — Cloudflare Tunnel is separate).
# Usage (as the app user, from repo root):
#   bash deploy/ubuntu/install.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python3
fi

echo "==> Using $($PYTHON_BIN --version)"

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  echo "==> Creating .env from deploy/ubuntu/env.production.example"
  cp deploy/ubuntu/env.production.example .env
  # Generate secrets if still placeholders
  if grep -q 'CHANGE_ME_SECRET' .env; then
    SEC="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
    JWT="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
    sed -i "s|CHANGE_ME_SECRET_KEY|$SEC|g" .env
    sed -i "s|CHANGE_ME_JWT_SECRET|$JWT|g" .env
  fi
  echo "    Edit .env if you need Postgres / DEMO_SEED changes."
fi

echo "==> Building React SPA"
if [[ -f web/package-lock.json ]]; then
  npm --prefix web ci || npm --prefix web install
else
  npm --prefix web install
fi
npm --prefix web run build
test -f web/dist/index.html

mkdir -p backend/instance/uploads/lens

echo "==> Done."
echo "    Start (foreground): bash deploy/ubuntu/run-gunicorn.sh"
echo "    Or enable systemd (see deploy/ubuntu/README.md)"
