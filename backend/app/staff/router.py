from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.staff import service
from app.staff.service import CustomerCartOut, InventoryUpdate, StaffInventoryOut, StaffOrderOut

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
    staff: User = Depends(require_role(CANTEEN_STAFF)),
    db: Session = Depends(get_db),
):
    """Set the stock (e.g. restock). Staff only. Customers with 'Notify me' get a BACK_IN_STOCK notification."""
    return service.update_inventory(db, food_id, data)


@router.get("/carts", response_model=List[CustomerCartOut])
def customer_carts(staff: User = Depends(require_role(CANTEEN_STAFF)), db: Session = Depends(get_db)):
    """Every customer's current (non-empty) cart, with stock holds. Staff only."""
    return service.list_carts(db)
