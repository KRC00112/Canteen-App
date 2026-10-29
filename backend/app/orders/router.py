from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.orders import service
from app.orders.schemas import CancelOrderIn, OrderOut, OrderPlacedOut, OrderSummaryOut, PlaceOrderIn

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderPlacedOut, status_code=status.HTTP_201_CREATED)
def place_order(
    data: Optional[PlaceOrderIn] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place a pre-order from the items currently in the cart.

    Body (optional): {"payment_method": "UPI"} (default; needs a verified Razorpay payment when
    payments are on) or {"payment_method": "CASH_ON_PICKUP"} (pay at the counter before pickup).
    ONLINE / CASH are accepted too."""
    return service.place_order(db, user, (data or PlaceOrderIn()).payment_method)


@router.get("", response_model=List[OrderSummaryOut])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Order history of the logged-in user (newest first)."""
    return service.list_my_orders(db, user)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get one order by its order ID, e.g. ORD-20261010-0001. Poll it for status updates."""
    return service.get_order(db, user, order_id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: str,
    data: Optional[CancelOrderIn] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel your order. Only possible while it is PLACED (409 once the kitchen has started).
    Online payments are refunded automatically; a cash payment is handed back at the counter."""
    order = service.cancel_order(db, user, order_id, data.reason if data else None)
    return service.to_order_out(order, show_pickup_code=True)
