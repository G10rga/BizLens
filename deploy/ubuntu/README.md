# BizLens on Ubuntu + Cloudflare Tunnel

Public URL: **https://bizlens.g1orga.dev**

Architecture:

```
Internet → Cloudflare (TLS) → cloudflared on server → gunicorn 127.0.0.1:8000 → Flask + SPA
```

No open ports on the VPS are required if you use a Cloudflare Tunnel.

---

## 1. Server packages

```bash
sudo apt update
sudo apt install -y git curl build-essential python3.11 python3.11-venv python3-pip nodejs npm
# If python3.11 is missing on your Ubuntu, use deadsnakes or system python3.12
```

Install Cloudflare Tunnel daemon:

```bash
# Official package (example for amd64):
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
cloudflared --version
```

---

## 2. App user + code

```bash
sudo useradd --system --create-home --home-dir /opt/bizlens --shell /bin/bash bizlens || true
sudo mkdir -p /opt/bizlens
sudo chown -R bizlens:bizlens /opt/bizlens

sudo -u bizlens -H bash -lc '
  cd /opt/bizlens
  if [[ ! -d .git ]]; then
    git clone https://github.com/G10rga/BizLens.git .
  else
    git pull --ff-only
  fi
  bash deploy/ubuntu/install.sh
'
```

Edit secrets if needed:

```bash
sudo -u bizlens nano /opt/bizlens/.env
```

Set at least:

- `SECRET_KEY` / `JWT_SECRET_KEY` (install.sh auto-generates if you used the example)
- `CORS_ORIGINS=https://bizlens.g1orga.dev`
- `FLASK_ENV=production`
- `DEMO_SEED=true` (or `false`)

Smoke-test locally on the box:

```bash
sudo -u bizlens -H bash -lc 'cd /opt/bizlens && bash deploy/ubuntu/run-gunicorn.sh'
# other terminal:
curl -sS http://127.0.0.1:8000/api/health
# expect: {"status":"ok","app":"BizLens"}
```

---

## 3. systemd (keep the app running)

```bash
sudo cp /opt/bizlens/deploy/ubuntu/bizlens.service /etc/systemd/system/bizlens.service
sudo systemctl daemon-reload
sudo systemctl enable --now bizlens
sudo systemctl status bizlens --no-pager
```

Logs:

```bash
sudo journalctl -u bizlens -f
```

Update deploy later:

```bash
sudo -u bizlens -H bash -lc 'cd /opt/bizlens && git pull && bash deploy/ubuntu/install.sh'
sudo systemctl restart bizlens
```

---

## 4. Cloudflare Tunnel → `bizlens.g1orga.dev`

### Option A — Zero Trust dashboard (easiest)

1. Cloudflare Dashboard → **Zero Trust** → **Networks** → **Tunnels** → **Create tunnel**
2. Name it e.g. `bizlens-vps`
3. Install connector: copy the `cloudflared service install <TOKEN>` command and run it **on the Ubuntu server**
4. Add a **Published application route**:
   - Subdomain: `bizlens`
   - Domain: `g1orga.dev`
   - Service type: `HTTP`
   - URL: `http://127.0.0.1:8000`
5. Save — DNS for `bizlens.g1orga.dev` is created automatically (CNAME to the tunnel)

### Option B — Config file

```bash
cloudflared tunnel login
cloudflared tunnel create bizlens
# note the Tunnel ID printed

sudo mkdir -p /etc/cloudflared
sudo cp /root/.cloudflared/<TUNNEL_ID>.json /etc/cloudflared/
sudo nano /etc/cloudflared/config.yml
```

Use `deploy/ubuntu/cloudflared-config.example.yml` as the template (hostname `bizlens.g1orga.dev` → `http://127.0.0.1:8000`).

```bash
cloudflared tunnel route dns bizlens bizlens.g1orga.dev
sudo cloudflared service install
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared --no-pager
```

---

## 5. Cloudflare / app checks

1. Open https://bizlens.g1orga.dev/api/health  
2. Open https://bizlens.g1orga.dev/ → login  
   - Demo: `demo@bizlens.ge` / `demo1234` (if `DEMO_SEED=true`)
3. In Cloudflare DNS, `bizlens` should be **Proxied** (orange cloud)

Optional: Zero Trust Access policies if you want login gated by email before the app.

---

## 6. Firewall note

With a Tunnel you typically **do not** open 80/443 on the VPS.  
Keep SSH locked down (`ufw allow OpenSSH`). Gunicorn listens on `127.0.0.1:8000` only.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 502 from Cloudflare | `systemctl status bizlens` — app down or not on `:8000` |
| Blank page | Rebuild SPA: `bash deploy/ubuntu/install.sh` then `systemctl restart bizlens` |
| Lens OCR 502 / OOM | Raise `MemoryMax` in systemd or enter totals manually |
| Wrong CORS | Set `CORS_ORIGINS=https://bizlens.g1orga.dev` in `.env` |
| Tunnel connected but DNS fails | Ensure route hostname is exactly `bizlens.g1orga.dev` on zone `g1orga.dev` |
