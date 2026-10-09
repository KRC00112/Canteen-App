from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.inventory import service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class InventoryOut(BaseModel):
    food_id: int
    quantity: int
    available: bool


@router.get("/{food_id}", response_model=InventoryOut)
def get_inventory(food_id: int, db: Session = Depends(get_db)):
    """Check current stock and availability of a food item."""
    inv = service.get_inventory(db, food_id)
    return InventoryOut(food_id=food_id, quantity=inv.quantity, available=service.is_available(inv))
