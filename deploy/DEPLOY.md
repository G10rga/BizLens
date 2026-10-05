# Deploy BizLens → https://bizlens.g1orga.dev

Same pattern as Teoria / Qalaqobana: **unused loopback port + existing Cloudflare Tunnel**.

```
Internet → Cloudflare Tunnel → nginx 127.0.0.1:8088 → gunicorn 127.0.0.1:8020 → Flask + SPA
                                                                          ↓
                                                              PostgreSQL 127.0.0.1:5432
```

| What | Port |
|------|------|
| nginx (tunnel target) | **8088** (localhost) |
| gunicorn | **8020** (localhost) |
| PostgreSQL | **5432** (localhost) |
| Teoria (already on host) | 8012 |

## 1. Get the code

```bash
sudo mkdir -p /opt/bizlens
sudo git clone https://github.com/G10rga/BizLens.git /opt/bizlens
# later: cd /opt/bizlens && sudo -u bizlens git pull --ff-only origin main
```

## 2. Install app + Postgres + nginx

Uses **Python 3.11** and **PostgreSQL** as the main database.

```bash
cd /opt/bizlens
sudo ./deploy/setup-ubuntu.sh
```

Or Postgres only (app already installed):

```bash
cd /opt/bizlens
sudo ./deploy/setup-postgres.sh
sudo mkdir -p /opt/bizlens/backend/instance/uploads
sudo chown -R bizlens:bizlens /opt/bizlens/backend/instance
sudo systemctl restart bizlens
```

Smoke test:

```bash
curl -sS http://127.0.0.1:8088/api/health
sudo -u postgres psql -d bizlens -c '\dt'
```

## 3. Cloudflare Tunnel (merge — do not replace)

Add to `/etc/cloudflared/config.yml` (keep other hostnames):

```yaml
  - hostname: bizlens.g1orga.dev
    service: http://127.0.0.1:8088
```

```bash
sudo cloudflared tunnel route dns <TUNNEL_NAME> bizlens.g1orga.dev
sudo systemctl restart cloudflared
```

## 4. Check

1. https://bizlens.g1orga.dev/api/health  
2. Register a user (or demo if `DEMO_SEED=true`)  
3. CSV import your sales → Dashboard

## Update later

```bash
cd /opt/bizlens
sudo -u bizlens git pull --ff-only origin main
sudo -u bizlens bash deploy/install-app.sh
sudo chown -R bizlens:bizlens /opt/bizlens/backend/instance
sudo systemctl restart bizlens
```

## Fix: CSV “Permission denied” on uploads

```bash
sudo mkdir -p /opt/bizlens/backend/instance/uploads
sudo chown -R bizlens:bizlens /opt/bizlens/backend/instance
sudo systemctl restart bizlens
```
