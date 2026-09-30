# BizLens

Cash-flow forecasting + web POS for Georgian small businesses.

**Stack:** Flask · SQLAlchemy · JWT · Facebook Prophet · Georgian Intelligence Layer  
**Frontend:** Stitch UI HTML mocks served at `/` and `/ui/...`

## Quick start

```powershell
cd C:\Users\user\BizLens
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
# Optional (Python 3.10–3.12 recommended): pip install -r backend\requirements-ml.txt
copy .env.example .env
cd backend
python run.py
```

> **Note:** On Python 3.14, Prophet may not install yet. The API still runs using the Georgian-aware seasonal baseline. For full Prophet, use Python 3.11/3.12 + `requirements-ml.txt`.

Open:
- UI index: http://127.0.0.1:5000/
- Health: http://127.0.0.1:5000/api/health

### Demo account (auto-seeded)

- Email: `demo@bizlens.ge`
- Password: `demo1234`
- Business: Mziuri Bakery (Tbilisi) with ~120 days of sales history

## API overview

All `/api/*` JSON endpoints (except auth register/login) require:

```
Authorization: Bearer <access_token>
```

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login → JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/onboarding/profile` | Business profile |
| POST | `/api/onboarding/expenses` | Fixed expenses |
| POST | `/api/onboarding/suppliers` | Supplier schedule |
| POST | `/api/onboarding/cash` | Cash on hand + finish |
| GET/POST/PUT/DELETE | `/api/products` | Product catalog |
| POST | `/api/sales` | Record POS sale |
| GET | `/api/sales/today` | Today's sales |
| GET/PUT | `/api/expenses` | Expenses + suppliers + cash |
| GET | `/api/forecast/dashboard` | 90-day cash forecast |
| POST | `/api/forecast/refresh-alerts` | Rebuild alerts |
| GET | `/api/alerts` | List alerts |
| POST | `/api/alerts/<id>/acknowledge` | Ack alert |
| POST | `/api/csv/preview` | Preview CSV (`multipart file`) |
| POST | `/api/csv/import` | Import CSV into daily sales |
| GET | `/api/csv/history` | Import history |
| GET/PUT | `/api/settings` | Language + profile |

### Record a sale

```json
POST /api/sales
{
  "payment_method": "cash",
  "items": [
    { "product_id": 1, "quantity": 2 }
  ]
}
```

### CSV format (BizLens Pro)

Minimum columns: `date,revenue`  
Also accepts common POS headers (`Amount`, `Total`, `თარიღი`, …).  
Sample file: `backend/sample_data/sample_pos_export.csv`

## Forecasting engine

1. Daily sales (from POS and/or CSV) → `daily_sales` table  
2. **Prophet** learns trend + weekly seasonality (+ yearly if enough history)  
3. **Georgian Intelligence Layer** adds holidays / fasting / tourism / school calendar as holiday effects + `geo_factor` regressor by business type  
4. Cash formula: `cash += predicted_income - expenses_due` for 90 days  
5. Zones: green > ₾1500, yellow ₾500–1500, red < ₾500  
6. Alerts generated from danger zones + upcoming Georgian events  

If Prophet is unavailable or history < 14 days, a seasonal baseline fallback is used automatically.

## Project layout

```
BizLens/
  backend/
    app/
      models.py
      routes/
      services/          # forecast, georgian calendar, cashflow, csv, alerts
      seed.py
    run.py
    requirements.txt
    sample_data/
  frontend/              # Stitch HTML screens + DESIGN.md
  .env.example
```

## Database

Default: SQLite at `backend/instance/bizlens.db`  
Postgres: set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/bizlens`

## Notes for Demo Day

- Weather regressors intentionally omitted  
- POS is intentionally thin (catalog → cart → cash/card → forecast feed)  
- UI mocks are static HTML; wire them to these APIs next (or keep API demo via curl/Postman for the pitch)
