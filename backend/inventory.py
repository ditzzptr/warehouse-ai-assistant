from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Item, StockTransaction

def stock_status(item: Item) -> str:
    if item.quantity == 0:
        return "OUT_OF_STOCK"
    if item.quantity <= item.min_stock:
        return "LOW_STOCK"
    return "NORMAL"

def create_stock_transaction(
    db: Session,
    item: Item,
    transaction_type: str,
    quantity: int,
    note: str = "",
) -> StockTransaction:
    kind = transaction_type.upper()
    if kind not in {"IN", "OUT"}:
        raise ValueError("transaction_type harus IN atau OUT")
    if quantity <= 0:
        raise ValueError("quantity harus lebih besar dari 0")

    if kind == "OUT" and item.quantity < quantity:
        raise ValueError(
            f"Stok tidak cukup. Stok tersedia: {item.quantity} {item.unit}"
        )

    if kind == "IN":
        item.quantity += quantity
    else:
        item.quantity -= quantity

    transaction = StockTransaction(
        item_id=item.id,
        transaction_type=kind,
        quantity=quantity,
        note=note,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    db.refresh(item)
    return transaction

def get_dashboard_summary(db: Session) -> dict:
    items = db.scalars(select(Item)).all()
    return {
        "total_products": len(items),
        "total_units": sum(item.quantity for item in items),
        "low_stock": sum(
            1 for item in items
            if 0 < item.quantity <= item.min_stock
        ),
        "out_of_stock": sum(1 for item in items if item.quantity == 0),
        "total_stock_value": round(
            sum(item.quantity * item.unit_price for item in items), 2
        ),
    }
