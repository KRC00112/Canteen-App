from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Inventory


def get_inventory(db: Session, food_id: int, lock: bool = False) -> Inventory:
    """Fetch the inventory row for a food item.

    lock=True takes a row lock (SELECT ... FOR UPDATE) so that concurrent orders
    cannot consume the same stock.
    """
    stmt = select(Inventory).where(Inventory.food_item_id == food_id)
    if lock:
        stmt = stmt.with_for_update()
    inv = db.scalar(stmt)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    return inv


def is_available(inv: Inventory) -> bool:
    return inv.availability and inv.quantity > 0


def ensure_quantity_available(inv: Inventory, requested: int, food_name: str) -> None:
    if not is_available(inv):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{food_name} is currently unavailable"
        )
    if requested > inv.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only {inv.quantity} {food_name} left in stock",
        )


def set_quantity(inv: Inventory, quantity: int) -> None:
    """Update stock; items automatically become unavailable at zero."""
    inv.quantity = max(quantity, 0)
    inv.availability = inv.quantity > 0
