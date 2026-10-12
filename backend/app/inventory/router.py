from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.security import get_optional_customer
from app.database.database import get_db
from app.database.models import User
from app.inventory import service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class InventoryOut(BaseModel):
    food_id: int
    available: bool
    stock_status: str
    stock_message: str
    max_order_quantity: int


@router.get("/{food_id}", response_model=InventoryOut)
def get_inventory(
    food_id: int, user: Optional[User] = Depends(get_optional_customer), db: Session = Depends(get_db)
):
    """Check availability of a food item. Exact stock counts are only shown to staff."""
    inv = service.get_inventory(db, food_id)
    stock = service.stock_for_user(db, inv, user.id if user else None)
    return InventoryOut(
        food_id=food_id,
        available=stock.available,
        stock_status=stock.status,
        stock_message=stock.message,
        max_order_quantity=stock.max_order_quantity,
    )
