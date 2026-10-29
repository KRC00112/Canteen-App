from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.staff import service
from app.orders import service as orders_service
from app.orders.schemas import CancelOrderIn
from app.staff.service import (
    CashPaymentIn,
    CustomerCartOut,
    InventoryUpdate,
    PickupCodeIn,
    RefundIn,
    StaffInventoryOut,
    StaffOrderOut,
    to_staff_order_out,
)

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/orders", response_model=List[StaffOrderOut])
def incoming_orders(
    status: Optional[str] = Query(
        None, description="Filter by status: PLACED, PREPARING, READY, SERVED or CANCELLED"
    ),
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """Incoming orders for canteen staff. Students/Faculty get 403 Forbidden."""
    return service.list_orders(db, status)


# Order lifecycle: PLACED -> PREPARING -> READY -> SERVED. Each step notifies the customer.

@router.post("/orders/{order_id}/preparing", response_model=StaffOrderOut)
def start_preparing(
    order_id: str, staff: User = Depends(require_role(CANTEEN_STAFF)), db: Session = Depends(get_db)
):
    """PLACED -> PREPARING. From now on the customer can no longer cancel."""
    return to_staff_order_out(orders_service.start_preparing(db, staff, order_id))


@router.post("/orders/{order_id}/ready", response_model=StaffOrderOut)
def mark_ready(
    order_id: str, staff: User = Depends(require_role(CANTEEN_STAFF)), db: Session = Depends(get_db)
):
    """PREPARING -> READY. The customer is told to come to the counter (and to pay, for cash)."""
    return to_staff_order_out(orders_service.mark_ready(db, staff, order_id))


@router.post("/orders/{order_id}/cash-payment", response_model=StaffOrderOut)
def record_cash_payment(
    order_id: str,
    data: CashPaymentIn,
    staff: User = Depends(require_role(CANTEEN_STAFF)),
    db: Session = Depends(get_db),
):
    """Record cash taken at the counter for an unpaid order (any stage before SERVED).
    Needs the customer's pickup code and amount_received >= total; returns the change to give.
    The customer gets a PAYMENT_RECEIVED notification."""
    order = orders_service.record_cash_payment(db, staff, order_id, data.pickup_code, data.amount_received)
    return to_staff_order_out(order)


@router.post("/orders/{order_id}/serve", response_model=StaffOrderOut)
def serve(
    order_id: str,
    data: PickupCodeIn,
    staff: User = Depends(require_role(CANTEEN_STAFF)),
    db: Session = Depends(get_db),
):
    """READY -> SERVED (verified and picked up). Refused with 402 until the order is PAID,
    and with 403 if the pickup code is wrong."""
    return to_staff_order_out(orders_service.serve(db, staff, order_id, data.pickup_code))


@router.post("/orders/{order_id}/cancel", response_model=StaffOrderOut)
def cancel_order(
    order_id: str,
    data: Optional[CancelOrderIn] = None,
    staff: User = Depends(require_role(CANTEEN_STAFF)),
    db: Session = Depends(get_db),
):
    """Cancel a PLACED order (e.g. an item ran out). Stock goes back; the customer is refunded."""
    order = orders_service.cancel_order(db, staff, order_id, data.reason if data else None, by_staff=True)
    return to_staff_order_out(order)


@router.post("/orders/{order_id}/refund", response_model=StaffOrderOut)
def settle_refund(
    order_id: str,
    data: Optional[RefundIn] = None,
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """For a cancelled order whose payment is REFUND_PENDING: retries the Razorpay refund
    (online), or records the cash handed back at the counter (cash; needs the pickup code)."""
    order = orders_service.settle_refund(db, staff, order_id, data.pickup_code if data else None)
    return to_staff_order_out(order)


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
