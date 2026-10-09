from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.orders import service
from app.orders.schemas import OrderOut, OrderPlacedOut, OrderSummaryOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderPlacedOut, status_code=status.HTTP_201_CREATED)
def place_order(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Place a pre-order from the items currently in the cart."""
    return service.place_order(db, user)


@router.get("", response_model=List[OrderSummaryOut])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Order history of the logged-in user (newest first)."""
    return service.list_my_orders(db, user)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get one order by its order ID, e.g. ORD-20261010-0001."""
    return service.get_order(db, user, order_id)
