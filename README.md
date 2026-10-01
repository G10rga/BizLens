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

OCR backends (optional):

| Setup | Behavior |
|-------|----------|
| `OPENAI_API_KEY` in `.env` | Vision model extracts receipt text |
| System Tesseract + `pip install pytesseract` | Local OCR |
| Neither | **Demo receipt** still works; photo uploads need manual totals |

```powershell
pip install Pillow
# optional:
pip install pytesseract
# plus install Tesseract OCR for your OS
```

## Import your shop CSV

Upload a file with `date,revenue` (or Excel Date + Total). Use clear/replace on the CSV page when switching datasets.

Then open **დაფა** for the forward forecast.

## Python note

On Python 3.14, Prophet may not install. Forecasting still runs via the Georgian-aware seasonal baseline. For Prophet: Python 3.11/3.12 + `pip install -r backend\requirements-ml.txt`.
