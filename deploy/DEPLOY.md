# Deploy BizLens → https://bizlens.g1orga.dev

Same pattern as Teoria / Qalaqobana: **unused loopback port + existing Cloudflare Tunnel**.

```
Internet → Cloudflare Tunnel → nginx 127.0.0.1:8088 → gunicorn 127.0.0.1:8020 → Flask + SPA
```

| What | Port |
|------|------|
| nginx (tunnel target) | **8088** (localhost) |
| gunicorn | **8020** (localhost) |
| Teoria (already on host) | 8012 |
| Reserved / other apps | 8000 / 8001 |

## 1. Get the code

```bash
sudo mkdir -p /opt/bizlens
sudo git clone https://github.com/G10rga/BizLens.git /opt/bizlens
# later updates: cd /opt/bizlens && sudo -u bizlens git pull
```

## 2. Install (app + systemd + nginx)

Uses **Python 3.11** (deadsnakes) — system 3.13 cannot install Prophet / RapidOCR.

```bash
cd /opt/bizlens
sudo ./deploy/setup-ubuntu.sh
```

Smoke test:

```bash
curl -sS http://127.0.0.1:8088/api/health
# {"status":"ok","app":"BizLens"}
```

If 8088 or 8020 is taken:

```bash
sudo BIZLENS_PORT=8021 BIZLENS_NGINX_PORT=8089 ./deploy/setup-ubuntu.sh
```

## 3. Cloudflare Tunnel (merge — do not replace)

Add this hostname to `/etc/cloudflared/config.yml` without removing your other rules
(see `deploy/cloudflared-ingress.snippet.yml`):

```yaml
  - hostname: bizlens.g1orga.dev
    service: http://127.0.0.1:8088
```

Then:

```bash
sudo cloudflared tunnel route dns <TUNNEL_NAME> bizlens.g1orga.dev
sudo systemctl restart cloudflared
```

## 4. Check

1. https://bizlens.g1orga.dev/api/health  
2. https://bizlens.g1orga.dev/ — demo login `demo@bizlens.ge` / `demo1234` (if `DEMO_SEED=true`)

## Update later

```bash
cd /opt/bizlens
sudo -u bizlens git pull --ff-only origin main
sudo -u bizlens bash deploy/install-app.sh
sudo chown -R bizlens:bizlens /opt/bizlens/backend/instance
sudo systemctl restart bizlens
```

## Optional: PostgreSQL (instead of SQLite)

SQLite is fine for a single VPS. Postgres is optional (you already have `postgresql@16-main` on the host).

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

DB_PASS="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bizlens') THEN
    CREATE ROLE bizlens LOGIN PASSWORD '${DB_PASS}';
  ELSE
    ALTER ROLE bizlens WITH PASSWORD '${DB_PASS}';
  END IF;
END
\$\$;
SELECT 'CREATE DATABASE bizlens OWNER bizlens'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'bizlens')\gexec
GRANT ALL PRIVILEGES ON DATABASE bizlens TO bizlens;
SQL
sudo -u postgres psql -d bizlens -c 'GRANT ALL ON SCHEMA public TO bizlens;'

# Point the app at Postgres (keeps existing .env keys)
sudo -u bizlens bash -lc "
  cd /opt/bizlens
  grep -q '^DATABASE_URL=' .env && sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://bizlens:${DB_PASS}@127.0.0.1:5432/bizlens|' .env \\
    || echo 'DATABASE_URL=postgresql://bizlens:${DB_PASS}@127.0.0.1:5432/bizlens' >> .env
"
sudo systemctl restart bizlens
```

Fresh DB means login/demo users are recreated on next start if `DEMO_SEED=true`.

## Fix: CSV import “Permission denied” on uploads

Not Postgres — the `bizlens` user cannot write `backend/instance/uploads`:

```bash
sudo mkdir -p /opt/bizlens/backend/instance/uploads
sudo chown -R bizlens:bizlens /opt/bizlens/backend/instance
sudo systemctl restart bizlens
```
