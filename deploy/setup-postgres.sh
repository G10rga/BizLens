#!/usr/bin/env bash
# Create local Postgres role/database for BizLens and point .env at it.
# Safe to re-run. Usage (root):
#   sudo ./deploy/setup-postgres.sh
#
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0" >&2
  exit 1
fi

APP_USER="${BIZLENS_USER:-bizlens}"
APP_HOME="${BIZLENS_HOME:-/opt/bizlens}"
DB_NAME="${BIZLENS_DB_NAME:-bizlens}"
DB_USER="${BIZLENS_DB_USER:-bizlens}"
DB_PASS="${BIZLENS_DB_PASS:-}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y postgresql postgresql-contrib libpq-dev
systemctl enable --now postgresql

ENV_FILE="${APP_HOME}/.env"

if [[ -z "${DB_PASS}" && -f "${ENV_FILE}" ]]; then
  DB_PASS="$(python3 - <<PY
import re, urllib.parse
from pathlib import Path
text = Path("${ENV_FILE}").read_text()
m = re.search(r"^DATABASE_URL=(.+)$", text, re.M)
if not m:
    raise SystemExit
u = m.group(1).strip()
for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgresql://"):
    if u.startswith(prefix):
        u = "postgresql://" + u[len(prefix):]
        break
mm = re.match(r"postgresql://[^:]+:([^@]+)@", u)
if mm:
    print(urllib.parse.unquote(mm.group(1)))
PY
)" || DB_PASS=""
fi

if [[ -z "${DB_PASS}" ]]; then
  DB_PASS="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  echo "Generated new DB password"
fi

DB_PASS_ENC="$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "${DB_PASS}")"

# Escape single quotes for SQL string literals
DB_PASS_SQL="${DB_PASS//\'/\'\'}"

sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS_SQL}';
  ELSE
    ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASS_SQL}';
  END IF;
END
\$\$;
SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
SQL

sudo -u postgres psql -d "${DB_NAME}" -v ON_ERROR_STOP=1 <<SQL
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER SCHEMA public OWNER TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
SQL

DATABASE_URL="postgresql://${DB_USER}:${DB_PASS_ENC}@127.0.0.1:5432/${DB_NAME}"

mkdir -p "${APP_HOME}"
if [[ ! -f "${ENV_FILE}" ]]; then
  if [[ -f "${APP_HOME}/deploy/env.production.example" ]]; then
    SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    sed \
      -e "s|CHANGE_ME_SECRET_KEY|${SECRET_KEY}|g" \
      -e "s|CHANGE_ME_JWT_SECRET|${JWT_SECRET}|g" \
      -e "s|CHANGE_ME_DB_PASSWORD|${DB_PASS_ENC}|g" \
      "${APP_HOME}/deploy/env.production.example" > "${ENV_FILE}"
  else
    touch "${ENV_FILE}"
  fi
fi

set_env () {
  local key="$1" val="$2"
  if grep -q "^${key}=" "${ENV_FILE}"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "${ENV_FILE}"
  else
    echo "${key}=${val}" >> "${ENV_FILE}"
  fi
}

set_env DATABASE_URL "${DATABASE_URL}"
set_env DEMO_SEED "${DEMO_SEED:-false}"

if id -u "${APP_USER}" >/dev/null 2>&1; then
  chown "${APP_USER}:${APP_USER}" "${ENV_FILE}"
fi
chmod 600 "${ENV_FILE}"

install -d -o "${APP_USER}" -g "${APP_USER}" "${APP_HOME}/backend/instance/uploads/lens" 2>/dev/null \
  || mkdir -p "${APP_HOME}/backend/instance/uploads"
if id -u "${APP_USER}" >/dev/null 2>&1; then
  chown -R "${APP_USER}:${APP_USER}" "${APP_HOME}/backend/instance"
fi

if [[ -x "${APP_HOME}/.venv/bin/pip" ]]; then
  sudo -u "${APP_USER}" "${APP_HOME}/.venv/bin/pip" install -q 'psycopg2-binary>=2.9.13'
fi

# Create tables now (don't wait for opaque first request)
if [[ -x "${APP_HOME}/.venv/bin/python" ]]; then
  sudo -u "${APP_USER}" bash -lc "
    cd '${APP_HOME}'
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
    cd backend
    ../.venv/bin/python - <<'PY'
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('tables ok:', sorted(db.metadata.tables.keys()))
PY
  "
fi

systemctl restart bizlens.service 2>/dev/null || true

echo
echo "PostgreSQL ready for BizLens"
echo "  database: ${DB_NAME}"
echo "  user:     ${DB_USER}"
echo "  .env:     ${ENV_FILE}"
echo
echo "Verify:"
echo "  sudo -u postgres psql -d ${DB_NAME} -c '\\dt'"
echo "  curl -sS http://127.0.0.1:8088/api/health"
echo
echo "Then open https://bizlens.g1orga.dev — register (or demo if DEMO_SEED=true) and import CSV."
