import csv
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Item, StockTransaction
from .inventory import (
    stock_status,
    create_stock_transaction,
    get_dashboard_summary,
)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "inventory.csv"

def seed_inventory():
    """Import sample CSV data once, only when the items table is empty."""
    with Session(engine) as db:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_inventory()
    yield

app = FastAPI(
    title="Warehouse AI Assistant API",
    description="API sederhana untuk monitoring persediaan gudang.",
    version="1.0.0",
    lifespan=lifespan,
)

class ItemCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    category: str = "General"
    unit: str = "pcs"
    quantity: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    unit_price: float = Field(default=0, ge=0)

class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    category: str
    unit: str
    quantity: int
    min_stock: int
    unit_price: float

class TransactionCreate(BaseModel):
    item_id: int
    transaction_type: str = Field(pattern="^(IN|OUT|in|out)$")
    quantity: int = Field(gt=0)
    note: str = ""

@app.get("/")
def root():
    return {"message": "Warehouse AI Assistant API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)

@app.get("/items")
def list_items(db: Session = Depends(get_db)):
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

@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Item).where(Item.sku == payload.sku))
    if existing:
        raise HTTPException(status_code=409, detail="SKU sudah digunakan")
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.post("/transactions", status_code=201)
def add_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    item = db.get(Item, payload.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    try:
        transaction = create_stock_transaction(
            db, item, payload.transaction_type, payload.quantity, payload.note
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {
        "message": "Transaksi berhasil disimpan",
        "transaction_id": transaction.id,
        "item_id": item.id,
        "new_stock": item.quantity,
        "status": stock_status(item),
    }

@app.get("/transactions")
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    rows = db.scalars(
        select(StockTransaction)
        .order_by(StockTransaction.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "item_id": row.item_id,
            "item_name": row.item.name,
            "transaction_type": row.transaction_type,
            "quantity": row.quantity,
            "note": row.note,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]

from .models import Subscription
from datetime import datetime, timedelta

class SubscriptionSchema(BaseModel):
    plan_name: str
    duration_days: int

@app.get("/subscription/status")
def get_subscription_status(db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == "default_user").order_by(Subscription.id.desc()).first()
    if not sub:
        sub = Subscription(user_id="default_user", plan_name="Free", is_active=True, end_date=None)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return {
        "plan_name": sub.plan_name,
        "is_active": sub.is_active,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "end_date": sub.end_date.isoformat() if sub.end_date else None
    }

@app.post("/subscription/subscribe")
def subscribe_plan(payload: SubscriptionSchema, db: Session = Depends(get_db)):
    db.query(Subscription).filter(Subscription.user_id == "default_user").update({"is_active": False})
    end_date = datetime.utcnow() + timedelta(days=payload.duration_days)
    new_sub = Subscription(
        user_id="default_user",
        plan_name=payload.plan_name,
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=end_date
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return {"status": "success", "message": f"Berhasil berlangganan paket {payload.plan_name}!"}
