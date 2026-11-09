"""Logika bisnis yang dipanggil langsung oleh Streamlit (tanpa FastAPI/HTTP)."""
import csv
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .inventory import create_stock_transaction, get_dashboard_summary, stock_status
from .models import Item, Subscription

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "inventory.csv"
DEFAULT_USER = "default_user"


class ServiceError(Exception):
    """Kesalahan yang aman ditampilkan langsung ke pengguna."""


def init_db() -> None:
    """Buat tabel, lalu impor data contoh dari CSV bila tabel items masih kosong."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Item.id).limit(1)) is not None:
            return
        if not DATA_FILE.exists():
            return
        with DATA_FILE.open("r", newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                db.add(Item(
                    sku=row["sku"],
                    name=row["name"],
                    category=row.get("category", "General"),
                    unit=row.get("unit", "pcs"),
                    quantity=int(row.get("quantity", 0)),
                    min_stock=int(row.get("min_stock", 0)),
                    unit_price=float(row.get("unit_price", 0)),
                ))
        db.commit()


def get_summary() -> dict:
    with SessionLocal() as db:
        return get_dashboard_summary(db)


def list_items() -> list[dict]:
    with SessionLocal() as db:
        items = db.scalars(select(Item).order_by(Item.name)).all()
        return [
            {
                "id": item.id,
                "sku": item.sku,
                "name": item.name,
                "category": item.category,
                "unit": item.unit,
                "quantity": item.quantity,
                "min_stock": item.min_stock,
                "unit_price": item.unit_price,
                "status": stock_status(item),
            }
            for item in items
        ]


def create_item(sku: str, name: str, category: str = "General", unit: str = "pcs",
                quantity: int = 0, min_stock: int = 0, unit_price: float = 0.0) -> None:
    sku, name = sku.strip(), name.strip()
    if not sku or not name:
        raise ServiceError("Kode barang (SKU) dan nama barang wajib diisi.")
    if quantity < 0 or min_stock < 0 or unit_price < 0:
        raise ServiceError("Stok, batas minimum, dan harga tidak boleh negatif.")
    with SessionLocal() as db:
        if db.scalar(select(Item).where(Item.sku == sku)):
            raise ServiceError("SKU sudah digunakan.")
        db.add(Item(
            sku=sku, name=name, category=category.strip() or "General",
            unit=unit.strip() or "pcs", quantity=quantity,
            min_stock=min_stock, unit_price=unit_price,
        ))
        db.commit()


def add_transaction(item_id: int, transaction_type: str, quantity: int, note: str = "") -> dict:
    with SessionLocal() as db:
        item = db.get(Item, item_id)
        if item is None:
            raise ServiceError("Barang tidak ditemukan.")
        try:
            transaction = create_stock_transaction(db, item, transaction_type, quantity, note)
        except ValueError as error:
            db.rollback()
            raise ServiceError(str(error)) from error
        return {
            "message": "Transaksi berhasil disimpan",
            "transaction_id": transaction.id,
            "item_id": item.id,
            "new_stock": item.quantity,
            "status": stock_status(item),
        }


def get_subscription_status() -> dict:
    with SessionLocal() as db:
        sub = db.scalars(
            select(Subscription)
            .where(Subscription.user_id == DEFAULT_USER)
            .order_by(Subscription.id.desc())
        ).first()
        if sub is None:
            sub = Subscription(user_id=DEFAULT_USER, plan_name="Free", is_active=True, end_date=None)
            db.add(sub)
            db.commit()
            db.refresh(sub)
        return {
            "plan_name": sub.plan_name,
            "is_active": sub.is_active,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
        }


def subscribe(plan_name: str, duration_days: int) -> dict:
    with SessionLocal() as db:
        for old in db.scalars(select(Subscription).where(Subscription.user_id == DEFAULT_USER)):
            old.is_active = False
        now = datetime.utcnow()
        db.add(Subscription(
            user_id=DEFAULT_USER, plan_name=plan_name, is_active=True,
            start_date=now, end_date=now + timedelta(days=duration_days),
        ))
        db.commit()
    return {"status": "success", "message": f"Berhasil berlangganan paket {plan_name}!"}
