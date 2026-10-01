# BizLens

Cash-flow forecasting + web POS for Georgian small businesses.

**Stack:** Flask API · React (Vite) SPA · SQLAlchemy · JWT · Georgian Intelligence Layer (+ Prophet optional)

## Quick start

```powershell
cd C:\Users\user\BizLens
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd web
npm install
npm run build

cd ..\backend
python run.py
```

Open http://127.0.0.1:5000/

### Demo account (auto-seeded)

- Email: `demo@bizlens.ge`
- Password: `demo1234`

### Dev mode (hot reload UI)

Terminal 1 — API:
```powershell
cd backend
python run.py
```

Terminal 2 — UI:
```powershell
cd web
npm run dev
```

Open http://127.0.0.1:5173/ (proxies `/api` to Flask).

## What works (live data, not static mocks)

- Login / Register
- Onboarding (profile, expenses, suppliers, cash)
- POS till (cart → cash/card → saved sales)
- **Lens Mode** — photograph fiscal receipts → OCR/AI parse → sales (no full POS)
- Products CRUD
- Today’s sales
- Dashboard forecast (30/60/90) from real daily sales
- Alerts generated from forecast
- CSV import (Pro)
- Expenses / settings

The live UI is the React app in `web/` (built to `web/dist/`).

## Lens Mode

For businesses that have a fiscal terminal but do not want a full POS:

1. Open **Lens Mode** in the sidebar
2. Photograph a printed receipt or terminal screen (or click **Demo receipt**)
3. Review extracted date, time, total, payment, optional items
4. Confirm — writes a `lens` sale + daily revenue for forecasting
5. Completeness bars show capture rate vs expected receipts/day; low capture **widens** forecast ranges

OCR backends (**free-first**, no paid API required):

| Priority | Setup | Cost |
|----------|--------|------|
| 1 | **OCR.space** — set `OCR_SPACE_API_KEY` from [ocr.space/ocrapi](https://ocr.space/ocrapi) (or leave unset for demo key `helloworld`) | Free tier |
| 2 | **Tesseract** local — OS package + `pytesseract` | Free |
| 3 | `OPENAI_API_KEY` | Paid optional |
| — | **Demo receipt** button | Always works |

On Render: add env `OCR_SPACE_API_KEY` = your free key. Photos are parsed → review → confirm → written to the database.

## Import your shop CSV

Upload a file with `date,revenue` (or Excel Date + Total). Use clear/replace on the CSV page when switching datasets.

Then open **დაფა** for the forward forecast.

## Deploy on Render

This repo is set up for [Render](https://render.com) (Python 3.11 + Postgres + gunicorn).

### Option A — Blueprint (recommended)

1. Push to GitHub
2. Render Dashboard → **New** → **Blueprint**
3. Select this repo (`render.yaml` is at the root)
4. Apply — creates `bizlens` web service + `bizlens-db` Postgres
5. Wait for build (npm build + pip install, including Prophet)

App URL will look like `https://bizlens.onrender.com`  
Demo login: `demo@bizlens.ge` / `demo1234` (when `DEMO_SEED=true`)

### Option B — Manual web service

| Setting | Value |
|---------|--------|
| Runtime | Python 3 |
| Build command | `bash bin/render-build.sh` |
| Start command | `bash bin/render-start.sh` |
| Health check | `/api/health` |

If the form rejects scripts, use these equivalents:

**Build**
```bash
pip install -r requirements.txt && npm --prefix web ci && npm --prefix web run build
```

**Start**
```bash
gunicorn --chdir backend run:app -b 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180
```

**Environment variables**

| Key | Notes |
|-----|--------|
| `SECRET_KEY` | Generate in Render |
| `JWT_SECRET_KEY` | Generate in Render |
| `DATABASE_URL` | From Render Postgres (auto if Blueprint) |
| `DEMO_SEED` | `true` for demo account |
| `OPENAI_API_KEY` | Optional — Lens photo OCR |
| `PYTHON_VERSION` | `3.11.11` |

Files involved: `render.yaml`, `Procfile`, `runtime.txt`, `bin/render-build.sh`, root `requirements.txt`.

**Notes**
- Ephemeral disk: Lens uploads reset on redeploy (sales in Postgres stay)
- Prophet + first forecast can be slow — gunicorn timeout is 180s
- Free tier may sleep after idle; first request can be slow
- Prefer **Python 3.11** (see `runtime.txt`); 3.14 often breaks Prophet

## Python note

Local Python 3.14 may skip Prophet. Production on Render uses **3.11** via `runtime.txt`. Install everything with:

```powershell
pip install -r requirements.txt
# or
pip install -r backend\requirements.txt
```
