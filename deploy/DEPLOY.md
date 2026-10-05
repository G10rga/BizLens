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
sudo -u bizlens git pull --ff-only
sudo -u bizlens bash deploy/install-app.sh
sudo systemctl restart bizlens
```
