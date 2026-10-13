#!/usr/bin/env bash
# Native Ubuntu install: gunicorn on 127.0.0.1:8020 + nginx on 127.0.0.1:8088.
# Public HTTPS is the existing Cloudflare Tunnel (merge hostname — do not replace).
# Run from the repo as root:
#
#   sudo ./deploy/setup-ubuntu.sh
#
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0" >&2
  exit 1
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="${BIZLENS_USER:-bizlens}"
APP_HOME="${BIZLENS_HOME:-/opt/bizlens}"
APP_PORT="${BIZLENS_PORT:-8020}"
NGINX_PORT="${BIZLENS_NGINX_PORT:-8088}"
DOMAIN="${BIZLENS_DOMAIN:-bizlens.g1orga.dev}"

systemctl stop bizlens.service 2>/dev/null || true

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
# Do NOT apt-install Ubuntu's `npm` — it pulls hundreds of node-* debs and can hang.
apt-get install -y \
  software-properties-common \
  git rsync curl build-essential \
  nginx \
  ca-certificates

# Prophet + RapidOCR need Python 3.11/3.12 (not 3.13+). Prefer 3.11 via deadsnakes.
if ! command -v python3.11 >/dev/null 2>&1; then
  echo "==> Installing Python 3.11 (deadsnakes)"
  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get update -y
  apt-get install -y python3.11 python3.11-venv python3.11-dev
fi
apt-get install -y python3-pip || true

PYTHON_BIN=python3.11
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python3.11 is required (Prophet/RapidOCR). Install failed." >&2
  exit 1
fi
echo "==> Using $($PYTHON_BIN --version)"

# Node.js + npm via NodeSource (single package). Skip if already present.
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "==> Installing Node.js 20 (NodeSource)"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
node --version
npm --version

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --home-dir "${APP_HOME}" --create-home --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${APP_HOME}"
if [[ "${REPO}" != "${APP_HOME}" ]]; then
  rsync -a --delete \
    --exclude '.venv' --exclude '.git' --exclude '*.db' --exclude '.env' \
    --exclude 'backend/instance' --exclude 'web/node_modules' --exclude 'web/dist' \
    "${REPO}/" "${APP_HOME}/"
  if [[ -d "${REPO}/.git" ]]; then
    rsync -a "${REPO}/.git" "${APP_HOME}/"
  fi
fi
chown -R "${APP_USER}:${APP_USER}" "${APP_HOME}"

# Recreate venv if missing or built with the wrong Python (e.g. system 3.13)
NEED_VENV=0
if [[ ! -d "${APP_HOME}/.venv" ]]; then
  NEED_VENV=1
elif ! "${APP_HOME}/.venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) else 1)' 2>/dev/null; then
  echo "==> Recreating .venv with Python 3.11"
  rm -rf "${APP_HOME}/.venv"
  NEED_VENV=1
fi
if [[ "${NEED_VENV}" -eq 1 ]]; then
  sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv "${APP_HOME}/.venv"
fi
sudo -u "${APP_USER}" "${APP_HOME}/.venv/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${APP_HOME}/.venv/bin/pip" install -r "${APP_HOME}/requirements.txt"

# Default: PostgreSQL as main DB (set BIZLENS_USE_POSTGRES=0 to keep SQLite)
USE_PG="${BIZLENS_USE_POSTGRES:-1}"
if [[ "${USE_PG}" =~ ^(1|true|yes)$ ]]; then
  echo "==> PostgreSQL"
  bash "${APP_HOME}/deploy/setup-postgres.sh"
fi

if [[ ! -f "${APP_HOME}/.env" ]]; then
  SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  install -o "${APP_USER}" -g "${APP_USER}" -m 600 /dev/null "${APP_HOME}/.env"
  sed \
    -e "s|CHANGE_ME_SECRET_KEY|${SECRET_KEY}|g" \
    -e "s|CHANGE_ME_JWT_SECRET|${JWT_SECRET}|g" \
    -e "s|^PORT=.*|PORT=${APP_PORT}|g" \
    -e "s|bizlens.g1orga.dev|${DOMAIN}|g" \
    "${APP_HOME}/deploy/env.production.example" > "${APP_HOME}/.env"
  chown "${APP_USER}:${APP_USER}" "${APP_HOME}/.env"
  chmod 600 "${APP_HOME}/.env"
fi

echo "==> Building React SPA"
sudo -u "${APP_USER}" bash -lc "
  cd '${APP_HOME}'
  if [[ -f web/package-lock.json ]]; then
    npm --prefix web ci || npm --prefix web install
  else
    npm --prefix web install
  fi
  npm --prefix web run build
  test -f web/dist/index.html
"
install -d -o "${APP_USER}" -g "${APP_USER}" "${APP_HOME}/backend/instance/uploads/lens"
# App user must own instance/ (sqlite + CSV uploads) — root-owned dirs cause Errno 13
chown -R "${APP_USER}:${APP_USER}" "${APP_HOME}/backend/instance"
chmod -R u+rwX "${APP_HOME}/backend/instance"

UNIT="/etc/systemd/system/bizlens.service"
sed \
  -e "s|/opt/bizlens|${APP_HOME}|g" \
  -e "s|User=bizlens|User=${APP_USER}|g" \
  -e "s|Group=bizlens|Group=${APP_USER}|g" \
  "${APP_HOME}/deploy/bizlens.service" > "${UNIT}"
sed -i "s/--bind 127.0.0.1:8020/--bind 127.0.0.1:${APP_PORT}/" "${UNIT}"

if ss -lnt | awk '{print $4}' | grep -qE "[:.]${APP_PORT}\$"; then
  echo "port ${APP_PORT} is already in use. Set BIZLENS_PORT to a free loopback port." >&2
  ss -lntp | grep -E "[:.]${APP_PORT}\b" || true
  exit 1
fi

systemctl daemon-reload
systemctl enable --now bizlens.service

echo "==> nginx site on 127.0.0.1:${NGINX_PORT}"
NGINX_CONF="/etc/nginx/sites-available/bizlens"
sed \
  -e "s|127.0.0.1:8020|127.0.0.1:${APP_PORT}|g" \
  -e "s|listen 127.0.0.1:8088|listen 127.0.0.1:${NGINX_PORT}|g" \
  -e "s|bizlens.g1orga.dev|${DOMAIN}|g" \
  "${APP_HOME}/deploy/nginx-bizlens.conf" > "${NGINX_CONF}"
ln -sf "${NGINX_CONF}" /etc/nginx/sites-enabled/bizlens
nginx -t
systemctl reload nginx

echo
echo "BizLens app:   127.0.0.1:${APP_PORT}"
echo "BizLens nginx: 127.0.0.1:${NGINX_PORT}"
echo "Check: curl -sS http://127.0.0.1:${NGINX_PORT}/api/health"
echo
echo "Cloudflare Tunnel — add this hostname (keep your other ingress rules):"
echo "  hostname: ${DOMAIN}"
echo "  service:  http://127.0.0.1:${NGINX_PORT}"
echo
echo "See deploy/cloudflared-ingress.snippet.yml then:"
echo "  sudo cloudflared tunnel route dns <TUNNEL_NAME> ${DOMAIN}"
echo "  sudo systemctl restart cloudflared"
echo
echo "Application files: ${APP_HOME}"
echo "Secrets file:      ${APP_HOME}/.env"
