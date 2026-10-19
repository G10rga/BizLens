"""Seed demo data for Mziuri Bakery — Demo Day ready."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from .extensions import db
from .models import (
    Business,
    FixedExpense,
    Product,
    Sale,
    SaleItem,
    SupplierPayment,
    User,
)
from .services.georgian_calendar import daily_seasonality_factor
from .services.sales_agg import upsert_daily_revenue
from .services.tax_accrual import rebuild_tax_reserves


DEMO_EMAIL = "demo@bizlens.ge"
DEMO_PASSWORD = "demo1234"


def seed_demo_if_needed(app) -> None:
    with app.app_context():
        existing = User.query.filter_by(email=DEMO_EMAIL).first()
        if existing:
            _ensure_demo_tax_profile(existing)
            return
        _create_demo()


def _ensure_demo_tax_profile(user: User) -> None:
    """Backfill tax fields for an already-seeded demo business."""
    business = user.business
    if not business:
        return
    if business.tax_profile_complete and business.legal_form:
        return
    business.legal_form = business.legal_form or "ie"
    business.tax_regime = business.tax_regime or "small"
    business.is_vat_payer = False
    business.has_employees = True
    business.pension_participants = True
    business.llc_distributes_profit = False
    business.tax_profile_complete = True
    rebuild_tax_reserves(business)
    db.session.commit()


def _create_demo() -> None:
    random.seed(42)
    user = User(email=DEMO_EMAIL, full_name="Nino Beridze", language="ka")
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    db.session.flush()

    business = Business(
        owner_id=user.id,
        name="Mziuri Bakery",
        business_type="bakery",
        city="Tbilisi",
        cash_on_hand=1850.0,
        onboarding_complete=True,
        cash_baseline_date=date.today(),
        legal_form="ie",
        tax_regime="small",
        is_vat_payer=False,
        has_employees=True,
        pension_participants=True,
        llc_distributes_profit=False,
        tax_profile_complete=True,
        tax_reserve=0.0,
        vat_reserve=0.0,
    )
    db.session.add(business)
    db.session.flush()

    products = [
        ("შოთის პური", 2.5, "პური", "4780001000001"),
        ("იმერული ხაჭაპური", 7.0, "ცომეული", "4780001000002"),
        ("აჭარული ხაჭაპური", 9.0, "ცომეული", "4780001000003"),
        ("ლობიანი", 5.5, "ცომეული", "4780001000004"),
        ("ყავა Capuccino", 6.0, "სასმელი", "4780001000005"),
        ("ნაპოლეონი", 4.5, "დესერტი", "4780001000006"),
        ("ქათმის ღვეზელი", 3.5, "ცომეული", "4780001000007"),
        ("წყალი", 1.5, "სასმელი", "4780001000008"),
    ]
    product_rows = []
    for name, price, category, barcode in products:
        p = Product(
            business_id=business.id,
            name=name,
            price=price,
            category=category,
            barcode=barcode,
        )
        db.session.add(p)
        product_rows.append(p)
    db.session.flush()

    # Due days chosen so Demo Day shows an upcoming cash collision
    next_week_day = min(28, (date.today() + timedelta(days=12)).day)
    expenses = [
        ("rent", 2400.0, next_week_day),
        ("salaries", 3200.0, 1),
        ("utilities", 410.0, 10),
        ("other", 200.0, 20),
    ]
    for name, amount, due_day in expenses:
        db.session.add(
            FixedExpense(
                business_id=business.id, name=name, amount=amount, due_day=due_day
            )
        )

    db.session.add(
        SupplierPayment(
            business_id=business.id,
            name="Flour supplier",
            amount=680.0,
            every_n_days=14,
            next_due_date=date.today() + timedelta(days=5),
        )
    )

    # ~120 days of synthetic daily revenue with weekly + Georgian seasonality
    today = date.today()
    base = 420.0
    for i in range(120, 0, -1):
        d = today - timedelta(days=i)
        dow = d.weekday()
        weekly = [0.85, 0.9, 0.95, 1.0, 1.15, 1.35, 1.2][dow]
        geo = daily_seasonality_factor(d, "bakery")
        noise = 1.0 + random.uniform(-0.12, 0.12)
        # mild growth
        trend = 1.0 + (120 - i) * 0.0008
        revenue = round(base * weekly * geo * noise * trend, 2)
        upsert_daily_revenue(business.id, d, revenue, source="seed")

        # sprinkle a few POS sale rows for "today" and recent days
        if i <= 3:
            _add_sample_pos_sales(business.id, product_rows, d, revenue)

    rebuild_tax_reserves(business)
    db.session.commit()


def _add_sample_pos_sales(business_id, products, d, day_revenue):
    # Create 2-4 sample ticket aggregates for realism on recent days
    remaining = day_revenue
    tickets = random.randint(2, 4)
    for t in range(tickets):
        p = random.choice(products)
        qty = random.randint(1, 4)
        line = round(p.price * qty, 2)
        if t == tickets - 1:
            line = round(max(p.price, remaining), 2)
            qty = max(1, int(line // p.price) or 1)
            line = round(p.price * qty, 2)
        remaining = max(0.0, remaining - line)
        sale = Sale(
            business_id=business_id,
            total=line,
            payment_method=random.choice(["cash", "card"]),
            sold_at=datetime.combine(d, datetime.min.time())
            + timedelta(hours=9 + t * 2, minutes=random.randint(0, 50)),
            source="pos",
        )
        db.session.add(sale)
        db.session.flush()
        db.session.add(
            SaleItem(
                sale_id=sale.id,
                product_id=p.id,
                product_name=p.name,
                unit_price=p.price,
                quantity=qty,
                line_total=line,
            )
        )
