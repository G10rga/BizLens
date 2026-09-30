# BizLens

Cash-flow forecasting + web POS for Georgian small businesses.

**Stack:** Flask API · React (Vite) SPA · SQLAlchemy · JWT · Georgian Intelligence Layer · Prophet (optional)

The live UI is the React app in `web/` (built to `web/dist/` and served by Flask). There is no separate static HTML frontend.

## Features

- Login / Register (JWT)
- Onboarding (business profile, fixed expenses, suppliers, cash on hand)
- POS till (cart → cash/card → saved sales)
- Products CRUD
- Today’s sales
- Dashboard forecast (30 / 60 / 90 days) from real daily sales
  - Model: **Prophet** when installed, otherwise **seasonal baseline**
  - Cards show a **likely** total plus a **low–high** range
  - Forecast starts the day after the last history date (not “today” if you uploaded older data)
- Alerts from cash-flow projection
- CSV / Excel import (Pro)
  - Clear imported data so a new file can be uploaded
  - Optional **replace** on import (wipe daily sales before loading)
- Expenses / settings

## Requirements

- **Python 3.11 or 3.12** recommended (needed for Prophet)
- Node.js 18+ (for the Vite SPA)
- Windows / macOS / Linux

Python 3.14 can run the API with the seasonal baseline, but Prophet often will not install cleanly.

## Quick start

### 1. Python env + backend deps

```powershell
cd C:\Users\user\BizLens

# Prefer 3.11 for Prophet
py -3.11 -m venv .venv

# If Activate.ps1 is blocked by execution policy, call the venv python directly:
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

# Optional — enables Prophet forecasting
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ml.txt
```

Or with activation (if allowed):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install -r backend\requirements-ml.txt
```

### 2. Build the React UI

```powershell
cd web
npm install
npm run build
cd ..
```

### 3. Run Flask (serves API + SPA)

```powershell
cd backend
..\..\BizLens\.venv\Scripts\python.exe run.py
# or, if venv is activated:
# python run.py
```

Open http://127.0.0.1:5000/

### Demo account (auto-seeded)

When `DEMO_SEED=true` (default in `.env.example`):

| | |
|---|---|
| Email | `demo@bizlens.ge` |
| Password | `demo1234` |

Copy `.env.example` → `.env` to override secrets / database.

## Dev mode (hot reload UI)

Terminal 1 — API:

```powershell
cd backend
C:\Users\user\BizLens\.venv\Scripts\python.exe run.py
```

Terminal 2 — UI:

```powershell
cd web
npm run dev
```

Open http://127.0.0.1:5173/ (Vite proxies `/api` to Flask on port 5000).

## Import shop sales (CSV / Excel)

1. Open **CSV / Excel იმპორტი**
2. Optionally click **მონაცემების წაშლა** to clear old daily sales / imports / POS rows
3. Upload a file with columns like **Date** + **Total** (or `date` / `revenue`)
   - Date forms such as `6/25/2023 (Sun)` are supported
   - `.xlsx` and `.csv` both work
4. Prefer **replace** checked so a new file fully replaces old daily sales
5. Open the dashboard — forecast starts after the last date in the file

### Sample data

Under `backend/sample_data/`:

| File | Coverage |
|------|----------|
| `fake_shop_mar_oct_2026.xlsx` | ~Mar–Oct 2026 daily shop totals |
| `fake_shop_jul_oct_2026.xlsx` | Jul–Oct subset |
| `fake_shop_120_days.csv` | ~120 days |
| `sample_pos_export.csv` | Small POS-style sample |

Tip: for stronger forecasts, upload **open trading days** (skip long closed gaps, or the app fills missing calendar days as `0` and that can pull averages down).

## Forecasting notes

| Topic | Behavior |
|-------|----------|
| Active model | Dashboard subtitle shows `prophet` or `seasonal_baseline` |
| Prophet | Fits on each request from uploaded history (weekly seasonality; yearly only if ≥ ~2 years) |
| Baseline | Multi-month blend + weekday / week templates when Prophet is unavailable |
| Backtest box | Scores the **last 30 days already in history** — not the same as the future 30-day cards |
| Ranges | Cards show likely total plus a tightened low–high band (~±5–12%) |

Install Prophet:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ml.txt
.\.venv\Scripts\python.exe -c "from prophet import Prophet; print('prophet OK')"
```

Then restart Flask and refresh the dashboard.

## Project layout

```
BizLens/
├── README.md
├── .env.example
├── backend/
│   ├── run.py                 # Flask entry (threaded)
│   ├── requirements.txt
│   ├── requirements-ml.txt    # prophet, etc.
│   ├── sample_data/           # demo CSV / Excel
│   └── app/
│       ├── routes/            # /api/*
│       ├── services/          # forecast, cashflow, CSV parser, alerts
│       ├── models.py
│       └── seed.py
└── web/                       # React + Vite SPA (the real UI)
    ├── src/pages/             # Login, POS, Dashboard, CSV, …
    └── dist/                  # production build served by Flask
```

## API smoke check

With the server running:

```powershell
cd backend
..\..\BizLens\.venv\Scripts\python.exe smoke_test.py
```

## License / demo

Built for Demo Day use with Georgian SMB cash-flow workflows. Not production-hardened by default (dev secrets in `.env.example`).
