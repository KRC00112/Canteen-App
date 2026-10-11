from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.staff import service
from app.menu.schemas import FoodItemOut
from app.staff.service import FoodItemUpdate, InventoryUpdate, StaffInventoryOut, StaffOrderOut

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/orders", response_model=List[StaffOrderOut])
def incoming_orders(
    status: Optional[str] = Query(None, description="Filter by status, e.g. PLACED"),
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """Incoming orders for canteen staff. Students/Faculty get 403 Forbidden."""
    return service.list_orders(db, status)


@router.get("/inventory", response_model=List[StaffInventoryOut])
def inventory(
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)), db: Session = Depends(get_db)
):
    """Exact stock per item, with how much is held in carts and ordered today."""
    return service.list_inventory(db)


@router.put("/inventory/{food_id}", response_model=StaffInventoryOut)
def update_inventory(
    food_id: int,
    data: InventoryUpdate,
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """Set the stock (e.g. restock). Customers with 'Notify me' get a BACK_IN_STOCK notification."""
    return service.update_inventory(db, food_id, data)


@router.patch("/menu/{food_id}", response_model=FoodItemOut)
def update_food_item(
    food_id: int,
    data: FoodItemUpdate,
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """Change Veg/Non-Veg type, ingredients, average cooking time, price or description."""
    return service.update_food_item(db, food_id, data)
