from datetime import date, datetime, time

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(8), default="ka", nullable=False)

    business = db.relationship("Business", back_populates="owner", uselist=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "language": self.language,
            "business_id": self.business.id if self.business else None,
            "onboarding_complete": bool(self.business and self.business.onboarding_complete),
        }


class Business(db.Model, TimestampMixin):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    business_type = db.Column(db.String(64), nullable=False, default="other")
    city = db.Column(db.String(64), nullable=False, default="Tbilisi")
    cash_on_hand = db.Column(db.Float, nullable=False, default=0.0)
    onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)
    cash_baseline_date = db.Column(db.Date, default=date.today, nullable=False)

    owner = db.relationship("User", back_populates="business")
    products = db.relationship("Product", back_populates="business", cascade="all, delete-orphan")
    sales = db.relationship("Sale", back_populates="business", cascade="all, delete-orphan")
    expenses = db.relationship(
        "FixedExpense", back_populates="business", cascade="all, delete-orphan"
    )
    suppliers = db.relationship(
        "SupplierPayment", back_populates="business", cascade="all, delete-orphan"
    )
    daily_sales = db.relationship(
        "DailySale", back_populates="business", cascade="all, delete-orphan"
    )
    alerts = db.relationship("Alert", back_populates="business", cascade="all, delete-orphan")
    csv_imports = db.relationship(
        "CsvImport", back_populates="business", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "business_type": self.business_type,
            "city": self.city,
            "cash_on_hand": self.cash_on_hand,
            "onboarding_complete": self.onboarding_complete,
            "cash_baseline_date": self.cash_baseline_date.isoformat(),
        }


class Product(db.Model, TimestampMixin):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(128), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    business = db.relationship("Business", back_populates="products")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "active": self.active,
        }


class Sale(db.Model, TimestampMixin):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(16), nullable=False)  # cash | card
    sold_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = db.Column(db.String(16), default="pos", nullable=False)  # pos | csv

    business = db.relationship("Business", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "total": self.total,
            "payment_method": self.payment_method,
            "sold_at": self.sold_at.isoformat(),
            "source": self.source,
            "items": [item.to_dict() for item in self.items],
        }


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    line_total = db.Column(db.Float, nullable=False)

    sale = db.relationship("Sale", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "line_total": self.line_total,
        }


class DailySale(db.Model, TimestampMixin):
    """Normalized daily revenue used by the forecasting engine."""

    __tablename__ = "daily_sales"
    __table_args__ = (
        db.UniqueConstraint("business_id", "sale_date", name="uq_business_sale_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=False, index=True)
    revenue = db.Column(db.Float, nullable=False, default=0.0)
    source = db.Column(db.String(16), default="pos", nullable=False)

    business = db.relationship("Business", back_populates="daily_sales")

    def to_dict(self):
        return {
            "date": self.sale_date.isoformat(),
            "revenue": self.revenue,
            "source": self.source,
        }


class FixedExpense(db.Model, TimestampMixin):
    __tablename__ = "fixed_expenses"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)  # rent, salaries, utilities, other
    amount = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)  # 1-28 safer for monthly

    business = db.relationship("Business", back_populates="expenses")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "due_day": self.due_day,
        }


class SupplierPayment(db.Model, TimestampMixin):
    __tablename__ = "supplier_payments"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    every_n_days = db.Column(db.Integer, nullable=False, default=14)
    next_due_date = db.Column(db.Date, nullable=False)

    business = db.relationship("Business", back_populates="suppliers")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "every_n_days": self.every_n_days,
            "next_due_date": self.next_due_date.isoformat(),
        }


class Alert(db.Model, TimestampMixin):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    severity = db.Column(db.String(16), nullable=False)  # danger | warning | opportunity
    title = db.Column(db.String(255), nullable=False)
    title_ka = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    message_ka = db.Column(db.Text, nullable=True)
    alert_date = db.Column(db.Date, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    acknowledged = db.Column(db.Boolean, default=False, nullable=False)

    business = db.relationship("Business", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "title_ka": self.title_ka,
            "message": self.message,
            "message_ka": self.message_ka,
            "alert_date": self.alert_date.isoformat() if self.alert_date else None,
            "amount": self.amount,
            "acknowledged": self.acknowledged,
            "created_at": self.created_at.isoformat(),
        }


class CsvImport(db.Model, TimestampMixin):
    __tablename__ = "csv_imports"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    rows_imported = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(32), default="completed", nullable=False)
    message = db.Column(db.Text, nullable=True)

    business = db.relationship("Business", back_populates="csv_imports")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "rows_imported": self.rows_imported,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }


def end_of_day(d: date) -> datetime:
    return datetime.combine(d, time(23, 59, 59))
