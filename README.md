# BizLens

**Cash-flow forecasting and sales capture for Georgian small businesses.**

BizLens answers one practical question: *“Will I have enough cash for rent, salaries, and suppliers — and when might I run short?”*

It does that by combining three things most shop owners already have (or can start using today):

1. **Sales capture** — a simple POS till, photo-based fiscal receipt capture (Lens Mode), or CSV/Excel history upload  
2. **Known outflows** — rent, salaries, utilities, and supplier payments on their real due schedule  
3. **A Georgia-aware forecast** — weekday patterns, seasonality, Orthodox holidays, fasting, tourism, and local events blended into a 30 / 60 / 90-day cash picture  

**Stack:** Flask API · React (Vite) SPA · SQLAlchemy · JWT · Georgian Intelligence Layer · Prophet (optional) · local OCR (RapidOCR)

---

## Who it is for

Georgian bakeries, cafés, retail shops, pharmacies, salons, and similar small businesses that:

- Already take payments at a till or fiscal terminal  
- Know their rent / salary / supplier rhythm roughly, but not how sales and outflows collide over the next months  
- Do **not** need a full ERP — they need a clear forward cash view and early warnings  

Primary UI language is **Georgian** (`ka`), with a full **English** switch. Currency is **₾ (GEL)**.

Demo business (auto-seeded when `DEMO_SEED=true`): **Mziuri Bakery** — `demo@bizlens.ge` / `demo1234`

---

## Core idea

Traditional accounting looks backward. BizLens looks **forward**.

```
Today’s sales  +  known expenses  +  Georgian seasonality
        ↓
  Daily revenue series
        ↓
  Sales forecast (30–90 days)
        ↓
  Cash-flow projection (best / likely / worst)
        ↓
  Alerts when cash is about to hit the danger zone
```

Every sale — whether it came from the POS, a photographed receipt, or a CSV row — updates the same **daily revenue** table. That table is the single input to the forecasting engine. Expenses and supplier payments are expanded onto the calendar. The result is a day-by-day cash balance the owner can actually act on.

---

## What it does (product surface)

| Area | What the user gets |
|------|--------------------|
| **Landing** | Brand intro, feature overview, KA/EN + theme toggle |
| **Auth** | Register / login with JWT; session kept in the browser |
| **Onboarding** | 4-step setup: business profile → fixed expenses → suppliers → cash on hand |
| **POS / Till** | Tap products into a cart, choose cash or card, save the sale |
| **Products** | Catalog CRUD (name, price, category, active flag) |
| **Today’s sales** | Day total, POS vs Lens vs CSV breakdown, cash/card split |
| **Lens Mode** | Photograph a fiscal receipt → OCR/parse → review → confirm as a sale |
| **CSV import** | Upload CSV/Excel with date + revenue; replace or merge history |
| **Expenses** | Monthly fixed costs + recurring supplier payments |
| **Dashboard** | History vs forecast charts, 30/60/90 sales & cash cards, holiday markers |
| **Alerts** | Danger / warning / opportunity notices (bilingual) |
| **Settings** | Business profile, language, Lens expected-receipts-per-day |

All of the above uses **live API data**, not static mocks.

---

## How the product works end-to-end

### 1. Account & business

1. User registers (`email`, password, optional name).  
2. JWT access token is issued (`Flask-JWT-Extended`).  
3. Until onboarding is finished, the app routes them to `/onboarding`.  
4. Onboarding creates a `Business` owned by that user:

   - Name, type (`bakery` | `restaurant` | `retail` | `pharmacy` | `salon` | `other`)  
   - City (`Tbilisi`, `Batumi`, `Kutaisi`, …)  
   - Fixed expenses (rent, salaries, utilities, other) with **due day of month**  
   - Supplier payments with **amount**, **every N days**, **next due date**  
   - **Cash on hand** baseline (starting balance for projections)

Business type matters: it selects the Georgian seasonality multipliers used in forecasts and alerts.

### 2. Three ways sales enter the system

All paths write (or update) `Sale` / `DailySale` records so forecasting always sees one consistent history.

#### A. POS till (`/pos`)

1. Active products are listed; user builds a cart.  
2. Checkout with `cash` or `card`.  
3. Backend creates a `Sale` (`source=pos`) + `SaleItem` lines.  
4. Daily revenue for today is upserted (`DailySale`).  
5. Cash payments also bump `business.cash_on_hand` (demo-friendly running till).

#### B. Lens Mode (`/lens`) — fiscal terminal without a full POS

For shops that already print fiscal receipts but do not want to ring every item in BizLens:

1. Photograph a printed receipt or terminal screen (or use **Demo receipt**).  
2. Image is compressed and run through OCR (**local-first**):

   | Priority | Engine | Notes |
   |----------|--------|--------|
   | 1 | **RapidOCR** (`rapidocr-onnxruntime`) | Pip install only; works offline after model load |
   | 2 | **Tesseract** | Optional OS install |
   | 3 | OCR.space / OpenAI Vision | Only if API keys are set (off by default) |
   | — | **Demo receipt** | Always works for demos |

3. Parsed fields: date, time, total, payment method, optional TIN, optional line items, confidence score.  
4. User reviews and edits if needed, then **confirms**.  
5. Confirm creates a `Sale` (`source=lens`) linked to a `ReceiptCapture`, and upserts that day’s revenue.

**Completeness → confidence:** each business sets `lens_expected_receipts_per_day`. Capture rate over recent days drives a **range widen factor**. Incomplete Lens capture widens the best/worst bands on the dashboard so owners see uncertainty honestly.

Tips for real receipts: good light, receipt flat, fill the frame, avoid blur. Always review the extracted total before confirm.

#### C. CSV / Excel import (`/csv`)

1. Upload a file with date + revenue columns (English or Georgian headers accepted: `date`/`თარიღი`, `revenue`/`თანხა`/`total`, etc.).  
2. Parser normalizes weekday suffixes like `6/25/2023 (Sun)`.  
3. Rows become `DailySale` history (`source=csv`); optional clear/replace when switching datasets.  
4. Dashboard forecast runs immediately on the imported history.

Sample files live under `backend/sample_data/`.

### 3. Expenses & suppliers

- **Fixed expenses** expand onto every month’s due day (clamped for short months).  
- **Supplier payments** walk forward/back by `every_n_days` across the forecast window.  
- Both become **expense markers** on the cash timeline (what hits which day).

### 4. Forecasting engine

Endpoint: `GET /api/forecast/dashboard`

Pipeline:

1. Load daily revenue for the business.  
2. Infer `as_of` = last day with sales (so holdout tests start after history, not “today”).  
3. **Sales forecast** (`forecast_sales`):

   - Prefer **Facebook Prophet** when ≥ ~21 history days and Prophet is installed (20s timeout).  
   - Otherwise (or on timeout/error): **seasonal baseline** — multi-month level, weekday open probability, real week-shape templates from history, soft Georgian seasonality.  
   - Fills missing calendar days as 0 so closed days do not inflate averages.  
   - Winsorizes outliers; blends ~90 days so one hot/cold month cannot dominate.  
   - Optional backtest on the last 30 days is **diagnostic** (does not invent upward future calibration).

4. **Georgian Intelligence Layer** (`georgian_calendar.py`) applies cultural seasonality:

   - New Year, Orthodox Christmas / Easter, Great Lent, Independence Day  
   - Tourism season, Mariamoba, school start, Tbilisoba, Giorgoba, winter slowdown  
   - Multipliers differ by business type (e.g. bakery up during fasting; restaurant down)

5. **Cash-flow projection** (`project_cashflow`):

   - Start from `cash_on_hand`  
   - Each day: `cash += forecast income − expenses`  
   - Three paths: **likely** (`yhat`), **best** (`yhat_upper`), **worst** (`yhat_lower`)  
   - Zones: green ≥ ₾1500, yellow ≥ ₾500, red below (configurable)  
   - Summary cards: sales & cash at 30 / 60 / 90 with tightened low–high ranges  
   - Lens incompleteness can widen those ranges

6. Dashboard returns history, income forecast, holiday markers, cash timeline, expense markers, summary, and Lens completeness.

### 5. Alerts

`build_alerts` turns the cash timeline + Georgian calendar into bilingual notices:

- **Danger** — cash enters the red zone; message cites nearby expenses and how much to prepare  
- **Warning** — e.g. fasting period starting (tone depends on business type)  
- **Opportunity** — e.g. New Year surge; prepare stock cash 2–3 weeks ahead  

Alerts regenerate from the current forecast (`/api/forecast/refresh-alerts`) and appear under **Alerts**.

---

## Architecture

```
web/                     React + Vite SPA (Chart.js)
  src/pages/             Landing, auth, onboarding, POS, Lens, dashboard, …
  src/i18n/              ka.js + en.js
  dist/                  Production build served by Flask

backend/
  run.py                 App entry
  app/
    models.py            Users, businesses, products, sales, expenses, alerts, …
    routes/              REST blueprints under /api/*
    services/            forecast, cashflow, alerts, OCR, CSV, Georgian calendar
    seed.py              Demo bakery dataset
  sample_data/           Example CSVs / receipt text
  instance/              SQLite DB + Lens uploads (local)

deploy/                  Ubuntu + nginx + Cloudflare Tunnel scripts
bin/                     Render build/start scripts
render.yaml              Render Blueprint (web + Postgres)
```

**Request flow (production-style):**

```
Browser → SPA (web/dist)
       → /api/* → Flask blueprints → SQLAlchemy → SQLite or Postgres
       → services (forecast / OCR / cashflow) → JSON for charts & alerts
```

**Auth:** JWT on protected routes; `require_business` ensures the caller owns a business.

**SPA serving:** Flask serves `web/dist` for `/` and client routes; API 404s stay JSON.

---

## Data model (conceptual)

| Entity | Role |
|--------|------|
| `User` | Account, language preference |
| `Business` | Profile, cash baseline, Lens expected receipts/day |
| `Product` | Till catalog |
| `Sale` / `SaleItem` | Individual transactions (`pos` \| `lens` \| `csv`) |
| `DailySale` | Normalized daily revenue for forecasting |
| `FixedExpense` | Monthly costs by due day |
| `SupplierPayment` | Recurring outflows |
| `Alert` | Generated warnings (EN + KA fields) |
| `CsvImport` | Import audit log |
| `ReceiptCapture` | Lens photo, OCR text, parse result, link to sale |

---

## API map (high level)

| Prefix | Purpose |
|--------|---------|
| `GET /api/health` | Health check |
| `/api/auth` | Register, login, me |
| `/api/onboarding` | Business setup steps |
| `/api/products` | Product CRUD |
| `/api/sales` | Create sale, today’s summary |
| `/api/lens` | Upload/parse/confirm receipts, completeness, OCR status |
| `/api/csv` | Import history |
| `/api/expenses` | Fixed expenses & suppliers |
| `/api/forecast` | Dashboard payload, refresh alerts, backtest |
| `/api/alerts` | List / acknowledge |
| `/api/settings` | Business & preferences |

---

## Tech stack detail

| Layer | Choice |
|-------|--------|
| API | Flask 3, Flask-CORS, Flask-JWT-Extended |
| ORM / DB | SQLAlchemy 2 · SQLite (dev) or PostgreSQL (Render/prod) |
| ML / forecast | pandas, numpy, Prophet (optional), custom seasonal baseline |
| OCR | RapidOCR + ONNX Runtime; optional Tesseract / cloud |
| Frontend | React 19, Vite 7, React Router 7, Chart.js |
| i18n | In-app Georgian / English dictionaries |
| Deploy | gunicorn · Render Blueprint · Ubuntu systemd + nginx + Cloudflare Tunnel |

Python **3.11** is the supported production version (`runtime.txt`). Newer interpreters often break Prophet / RapidOCR wheels.

---

## Quick start (local)

```bash
# from repo root
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate

pip install -r backend/requirements.txt

cd web && npm install && npm run build && cd ..

cd backend && python run.py
```

Open http://127.0.0.1:5000/

### Demo account

- Email: `demo@bizlens.ge`  
- Password: `demo1234`

### Dev mode (hot reload UI)

Terminal 1 — API:

```bash
cd backend && python run.py
```

Terminal 2 — UI:

```bash
cd web && npm run dev
```

Open http://127.0.0.1:5173/ (Vite proxies `/api` to Flask).

Copy `.env.example` to `.env` to tune secrets, database URL, CORS, and optional OCR keys.

For Lens photo OCR locally:

```bash
pip install rapidocr-onnxruntime onnxruntime Pillow
# restart Flask, then photograph a receipt in Lens Mode
```

---

## Import your shop CSV

Upload a file with `date,revenue` (or Excel Date + Total). Use clear/replace on the CSV page when switching datasets. Then open **Dashboard** (`დაფა`) for the forward forecast.

---

## Deploy on Render

This repo is set up for [Render](https://render.com) (Python 3.11 + Postgres + gunicorn).

### Option A — Blueprint (recommended)

1. Push to GitHub  
2. Render Dashboard → **New** → **Blueprint**  
3. Select this repo (`render.yaml` at the root)  
4. Apply — creates `bizlens` web service + `bizlens-db` Postgres  
5. Wait for build (npm build + pip install, including Prophet)

App URL looks like `https://bizlens.onrender.com`  
Demo login works when `DEMO_SEED=true`.

### Option B — Manual web service

| Setting | Value |
|---------|--------|
| Runtime | Python 3 |
| Build command | `bash bin/render-build.sh` |
| Start command | `bash bin/render-start.sh` |
| Health check | `/api/health` |

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

**Notes**

- Ephemeral disk: Lens uploads reset on redeploy (sales in Postgres stay)  
- Prophet + first forecast can be slow — gunicorn timeout is 180s  
- Free tier may sleep after idle; first request can be slow  
- Prefer **Python 3.11**; 3.14 often breaks Prophet  

---

## Host on Ubuntu + Cloudflare Tunnel

Same layout as sibling apps: nginx on an unused loopback port, hostname merged into an **existing** Cloudflare Tunnel. Full steps: **[deploy/DEPLOY.md](deploy/DEPLOY.md)**.

```
Internet → Cloudflare Tunnel → nginx 127.0.0.1:8088 → gunicorn 127.0.0.1:8020 → Flask + SPA
```

```bash
sudo mkdir -p /opt/bizlens
sudo git clone https://github.com/G10rga/BizLens.git /opt/bizlens
cd /opt/bizlens
sudo ./deploy/setup-ubuntu.sh
```

Add hostname to `/etc/cloudflared/config.yml` (see `deploy/cloudflared-ingress.snippet.yml`):

```yaml
  - hostname: bizlens.g1orga.dev
    service: http://127.0.0.1:8088
```

```bash
sudo cloudflared tunnel route dns <TUNNEL_NAME> bizlens.g1orga.dev
sudo systemctl restart cloudflared
curl -sS http://127.0.0.1:8088/api/health
```

If 8088 is taken: `sudo BIZLENS_NGINX_PORT=8089 ./deploy/setup-ubuntu.sh` and point the tunnel at that port.

---

## Why BizLens exists (one-line pitch)

**Georgian small shops do not lack a till — they lack a forward cash picture.** BizLens turns today’s sales (till, receipt photo, or spreadsheet) and known bills into a 30–90 day forecast with seasonality that actually matches Georgia.
