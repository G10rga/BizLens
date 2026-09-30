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
- Products CRUD
- Today’s sales
- Dashboard forecast (30/60/90) from real daily sales
- Alerts generated from forecast
- CSV import (Pro)
- Expenses / settings

Old Stitch HTML mockups remain under `frontend/` for reference only (`/stitch/...`). The real app is `web/`.

## Import your shop CSV

Upload a file with `date,revenue` (hourly rows OK if you aggregate first, or use daily totals).

Then open **დაფა** and choose **30 დღე** for a 30-day forward estimate.

## Python note

On Python 3.14, Prophet may not install. Forecasting still runs via the Georgian-aware seasonal baseline. For Prophet: Python 3.11/3.12 + `pip install -r backend\requirements-ml.txt`.
