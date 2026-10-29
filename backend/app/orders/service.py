"""Orders: placing, and the order lifecycle PLACED -> PREPARING -> READY -> SERVED.

- A customer (or staff) can cancel only while the order is PLACED. The stock goes back, and
  whatever was paid is refunded (Razorpay automatically; cash at the counter).
- UPI orders are paid (Razorpay signature verified) before they are placed. CASH_ON_PICKUP orders
  are paid at the counter: staff record the cash with the customer's pickup code.
- An order is SERVED only when it is READY, PAID, and the customer shows the pickup code.
- Every step is saved as an OrderEvent (the timeline) and notifies the customer.
"""
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import activity
from app.auth.security import utcnow
from app.config import CASH_MAX_UNPAID_ORDERS, CASH_PAYMENTS_ENABLED, payment_required
from app.database.models import (
    ACTIVE_ORDER_STATUSES,
    ADMIN,
    CANTEEN_STAFF,
    EVENT_CASH_RECEIVED,
    EVENT_REFUNDED,
    NOTIFY_ORDER_CANCELLED,
    NOTIFY_ORDER_PLACED,
    NOTIFY_ORDER_PREPARING,
    NOTIFY_ORDER_READY,
    NOTIFY_ORDER_SERVED,
    NOTIFY_PAYMENT_RECEIVED,
    NOTIFY_REFUNDED,
    ORDER_CANCELLED,
    ORDER_PAYMENT_CANCELLED,
    ORDER_PAYMENT_PAID,
    ORDER_PAYMENT_PENDING,
    ORDER_PAYMENT_REFUND_PENDING,
    ORDER_PAYMENT_REFUNDED,
    ORDER_PLACED,
    ORDER_PREPARING,
    ORDER_READY,
    ORDER_SERVED,
    PAY_CASH,
    PAY_ONLINE,
    PAYMENT_REFUND_PENDING,
    PAYMENT_USED,
    Cart,
    Inventory,
    Notification,
    Order,
    OrderEvent,
    OrderItem,
    User,
)
from app.inventory import service as inventory_service
from app.payments import service as payments_service
from app.orders.schemas import (
    OrderOut,
    OrderPlacedOut,
    OrderSummaryOut,
    can_cancel,
    estimated_ready_minutes,
    order_event_out,
    order_item_out,
)


def to_order_out(order: Order, show_pickup_code: bool = False) -> OrderOut:
    """show_pickup_code only for the customer who placed the order: staff must get it from them."""
    return OrderOut(
        order_id=order.order_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        estimated_ready_at=order.estimated_ready_at,
        estimated_ready_minutes=estimated_ready_minutes(order),
        items=[order_item_out(oi) for oi in order.items],
        payment_id=order.payment.razorpay_payment_id if order.payment else None,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        paid_at=order.paid_at,
        pickup_code=order.pickup_code if show_pickup_code else None,
        can_cancel=can_cancel(order),
        timeline=[order_event_out(e) for e in order.events],
    )


def to_summary(order: Order) -> OrderSummaryOut:
    return OrderSummaryOut(
        order_id=order.order_id,
        status=order.status,
        total_amount=order.total_amount,
        item_count=sum(oi.quantity for oi in order.items),
        created_at=order.created_at,
        estimated_ready_at=order.estimated_ready_at,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        can_cancel=can_cancel(order),
    )


def _rs(amount) -> str:
    return f"Rs {float(amount):g}"


def _add_event(order: Order, event: str, by: Optional[User], note: Optional[str] = None) -> None:
    order.events.append(OrderEvent(event=event, note=note, changed_by=by, created_at=utcnow()))


def _notify(db: Session, order: Order, type_: str, message: str) -> None:
    db.add(Notification(user_id=order.user_id, order=order, type=type_, message=message[:255]))


def _make_order_code(order: Order) -> str:
    # The DB primary key guarantees uniqueness, e.g. ORD-20261010-0001
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{order.id:04d}"


def place_order(db: Session, user: User, payment_method: str = PAY_ONLINE) -> OrderPlacedOut:
    """Convert the user's cart into an order in a single transaction.

    Steps: lock cart -> validate -> verified payment for this total (UPI, when payments are
    on) or the unpaid-cash-order limit (CASH_ON_PICKUP) -> lock inventory rows -> check stock (not
    counting other customers' active cart holds) -> create order and items -> reduce
    inventory -> use up the payment -> clear cart -> notify -> commit.
    """
    # Locking the cart serialises concurrent/repeated "place order" requests from the
    # same user, so a double-tap cannot create two orders from one cart.
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id).with_for_update())
    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty")

    payment = None
    if payment_method == PAY_CASH:
        _check_can_order_cash(db, user)
    elif payment_required():
        payment = payments_service.take_verified_payment(db, user, payments_service.cart_total(cart))

    # Lock inventory rows in a consistent order (by food id) to avoid deadlocks, and so
    # two customers cannot consume the same stock.
    cart_items = sorted(cart.items, key=lambda ci: ci.food_item_id)
    total = Decimal("0")
    order_items = []
    stock_changes = []
    for ci in cart_items:
        food = ci.food_item
        inv = inventory_service.get_inventory(db, food.id, lock=True)
        inventory_service.ensure_quantity_available(db, inv, user.id, ci.quantity, food.name)
        stock_changes.append(f"{food.name} x{ci.quantity} (stock {inv.quantity}->{inv.quantity - ci.quantity})")
        inventory_service.set_quantity(inv, inv.quantity - ci.quantity)
        total += food.price * ci.quantity
        order_items.append(OrderItem(food_item_id=food.id, quantity=ci.quantity, price=food.price))

    # Items are cooked in parallel, so the slowest one decides when the order is ready.
    cooking_minutes = max(ci.food_item.avg_cooking_time_minutes for ci in cart_items)
    now = utcnow()
    order = Order(
        order_id=f"TMP-{uuid.uuid4().hex}",
        user_id=user.id,
        total_amount=total,
        status=ORDER_PLACED,
        created_at=now,
        estimated_ready_at=now + timedelta(minutes=cooking_minutes),
        items=order_items,
        payment_method=payment_method,
        payment_status=ORDER_PAYMENT_PENDING,
        pickup_code=f"{secrets.randbelow(10000):04d}",
    )
    db.add(order)
    db.flush()
    order.order_id = _make_order_code(order)
    if payment is not None:
        payment.status = PAYMENT_USED
        payment.order_id = order.id
        order.payment = payment
        order.payment_status = ORDER_PAYMENT_PAID
        order.paid_at = payment.verified_at
    _add_event(order, ORDER_PLACED, user, f"{payment_method}, {_rs(total)}")
    if order.payment_status == ORDER_PAYMENT_PAID:
        pay_note = "Paid online"
    else:
        pay_note = f"Pay {_rs(total)} in cash at the counter"
    _notify(
        db, order, NOTIFY_ORDER_PLACED,
        f"Order {order.order_id} placed. {pay_note}. Ready in about {cooking_minutes} min. "
        f"Pickup code: {order.pickup_code}",
    )

    cart.items.clear()
    db.commit()
    db.refresh(order)
    if payment:
        paid_by = f", paid by {payment.razorpay_payment_id}"
    elif payment_method == PAY_CASH:
        paid_by = ", cash at the counter"
    else:
        paid_by = ", no payment (payments off), collect at the counter"
    activity.event(
        f"Order {order.order_id} placed: Rs {total}, ready in ~{cooking_minutes} min"
        + paid_by + "; " + ", ".join(stock_changes)
    )

    out = to_order_out(order, show_pickup_code=True)
    return OrderPlacedOut(**out.model_dump())


def _check_can_order_cash(db: Session, user: User) -> None:
    if not CASH_PAYMENTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cash payment is not available right now. Please pay online",
        )
    unpaid = db.scalar(
        select(func.count(Order.id)).where(
            Order.user_id == user.id,
            Order.payment_method == PAY_CASH,
            Order.payment_status == ORDER_PAYMENT_PENDING,
            Order.status.in_(ACTIVE_ORDER_STATUSES),
        )
    )
    if unpaid >= CASH_MAX_UNPAID_ORDERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a cash order that is not paid yet. Pay for it at the "
            "counter (or cancel it) before placing another cash order, or pay online",
        )


def list_my_orders(db: Session, user: User) -> List[OrderSummaryOut]:
    orders = db.scalars(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc(), Order.id.desc())
    ).unique()
    return [to_summary(o) for o in orders]


def get_order(db: Session, user: User, order_code: str) -> OrderOut:
    order = db.scalar(select(Order).where(Order.order_id == order_code))
    # Customers may only view their own orders; staff/admin can view any order.
    if order is None or (order.user_id != user.id and user.role.name not in (CANTEEN_STAFF, ADMIN)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return to_order_out(order, show_pickup_code=order.user_id == user.id)


# ---------- Lifecycle ----------

def lock_order(db: Session, order_code: str) -> Order:
    """Fetch an order with a row lock, so two staff taps can't both move it on."""
    order = db.scalar(select(Order).where(Order.order_id == order_code).with_for_update(of=Order))
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _require_status(order: Order, expected: str, action: str) -> None:
    if order.status != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order {order.order_id} is {order.status}: it can be {action} only when it is {expected}",
        )


def _check_pickup_code(order: Order, pickup_code: Optional[str]) -> None:
    if order.pickup_code is None:
        return  # placed before pickup codes existed
    if not pickup_code or not hmac.compare_digest(order.pickup_code, pickup_code.strip()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wrong pickup code. Ask the customer for the code shown in their app",
        )


def _restore_stock(db: Session, order: Order) -> None:
    # Same lock order as place_order (by food id) to avoid deadlocks.
    for oi in sorted(order.items, key=lambda oi: oi.food_item_id):
        inv = db.scalar(
            select(Inventory).where(Inventory.food_item_id == oi.food_item_id).with_for_update()
        )
        if inv is None:
            continue
        if inv.quantity == 0:
            inv.availability = True  # it was sold out only because of the stock
        inv.quantity += oi.quantity


def cancel_order(
    db: Session, user: User, order_code: str, reason: Optional[str] = None, by_staff: bool = False
) -> Order:
    """Cancel a PLACED order (customers: only their own). Puts the stock back and refunds."""
    order = lock_order(db, order_code)
    if not by_staff and order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status == ORDER_CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This order is already cancelled")
    if order.status != ORDER_PLACED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order {order.order_id} can't be cancelled: the canteen has already started on it "
            f"(status {order.status}). Orders can only be cancelled while they are PLACED",
        )

    _restore_stock(db, order)
    order.status = ORDER_CANCELLED
    if order.payment_status == ORDER_PAYMENT_PAID:
        order.payment_status = ORDER_PAYMENT_REFUND_PENDING
        if order.payment is not None:
            order.payment.status = PAYMENT_REFUND_PENDING
            refund_note = f" {_rs(order.total_amount)} will be refunded to your original payment method."
        else:
            refund_note = (
                f" Collect your {_rs(order.total_amount)} cash refund at the counter "
                f"(pickup code {order.pickup_code})."
            )
    else:
        order.payment_status = ORDER_PAYMENT_CANCELLED
        refund_note = ""
    _add_event(order, ORDER_CANCELLED, user, reason)
    who = " by the canteen" if order.user_id != user.id else ""
    because = f" ({reason})" if reason else ""
    _notify(
        db, order, NOTIFY_ORDER_CANCELLED,
        f"Order {order.order_id} was cancelled{who}{because}.{refund_note}",
    )
    db.commit()
    activity.event(
        f"Order {order.order_id} CANCELLED by {user.username}" + (f" ({reason})" if reason else "")
        + f"; stock returned, payment {order.payment_status}"
    )

    if order.payment is not None:
        refund_online(db, order_code)
    return order


def refund_online(db: Session, order_code: str, by: Optional[User] = None) -> bool:
    """Send (or retry) the Razorpay refund of a cancelled online order. Commits."""
    order = lock_order(db, order_code)
    if order.payment is None or order.payment_status != ORDER_PAYMENT_REFUND_PENDING:
        db.rollback()
        return order.payment_status == ORDER_PAYMENT_REFUNDED
    if not payments_service.refund(order.payment):
        db.commit()  # release the lock; the payment stays REFUND_PENDING for a retry
        return False
    order.payment_status = ORDER_PAYMENT_REFUNDED
    _add_event(order, EVENT_REFUNDED, by, f"Razorpay refund {order.payment.refund_id}")
    _notify(
        db, order, NOTIFY_REFUNDED,
        f"{_rs(order.total_amount)} for cancelled order {order.order_id} has been refunded to your "
        f"original payment method. It can take 5-7 working days to show up",
    )
    db.commit()
    return True


def settle_refund(db: Session, staff: User, order_code: str, pickup_code: Optional[str]) -> Order:
    """A cancelled order whose refund is still pending: retry the Razorpay refund, or record
    that the cash was handed back at the counter (needs the customer's pickup code)."""
    order = lock_order(db, order_code)
    if order.payment_status != ORDER_PAYMENT_REFUND_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No refund is pending for order {order.order_id} (payment {order.payment_status})",
        )
    if order.payment is not None:
        db.rollback()
        if not refund_online(db, order_code, staff):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Razorpay did not accept the refund. Try again later",
            )
        return order

    _check_pickup_code(order, pickup_code)
    order.payment_status = ORDER_PAYMENT_REFUNDED
    _add_event(order, EVENT_REFUNDED, staff, f"{_rs(order.total_amount)} cash handed back")
    _notify(
        db, order, NOTIFY_REFUNDED,
        f"{_rs(order.total_amount)} cash refunded for cancelled order {order.order_id}",
    )
    db.commit()
    activity.event(f"Order {order.order_id}: {_rs(order.total_amount)} cash refunded by {staff.username}")
    return order


def start_preparing(db: Session, staff: User, order_code: str) -> Order:
    order = lock_order(db, order_code)
    _require_status(order, ORDER_PLACED, "moved to PREPARING")
    # The order can't be cancelled from here on, so cooking time counts from now.
    cooking_minutes = max(oi.food_item.avg_cooking_time_minutes for oi in order.items)
    order.status = ORDER_PREPARING
    order.estimated_ready_at = utcnow() + timedelta(minutes=cooking_minutes)
    _add_event(order, ORDER_PREPARING, staff)
    _notify(
        db, order, NOTIFY_ORDER_PREPARING,
        f"Order {order.order_id} is being prepared. Ready in about {cooking_minutes} min",
    )
    db.commit()
    activity.event(f"Order {order.order_id} PREPARING (~{cooking_minutes} min)")
    return order


def mark_ready(db: Session, staff: User, order_code: str) -> Order:
    order = lock_order(db, order_code)
    _require_status(order, ORDER_PREPARING, "marked READY")
    order.status = ORDER_READY
    _add_event(order, ORDER_READY, staff)
    if order.payment_status == ORDER_PAYMENT_PAID:
        todo = f"show pickup code {order.pickup_code} at the counter"
    else:
        todo = f"pay {_rs(order.total_amount)} in cash and show pickup code {order.pickup_code} at the counter"
    _notify(db, order, NOTIFY_ORDER_READY, f"Order {order.order_id} is ready! Please {todo}")
    db.commit()
    activity.event(f"Order {order.order_id} READY")
    return order


def record_cash_payment(
    db: Session, staff: User, order_code: str, pickup_code: str, amount_received: Decimal
) -> Order:
    """Staff took cash at the counter. The customer must be there: their pickup code is needed."""
    order = lock_order(db, order_code)
    if order.status not in ACTIVE_ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order {order.order_id} is {order.status}: no payment can be taken for it",
        )
    if order.payment_status != ORDER_PAYMENT_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order {order.order_id} is already {order.payment_status}: do not take cash again",
        )
    _check_pickup_code(order, pickup_code)
    if amount_received < order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order total is {_rs(order.total_amount)}; only {_rs(amount_received)} was entered",
        )

    change = amount_received - order.total_amount
    order.payment_status = ORDER_PAYMENT_PAID
    order.paid_at = utcnow()
    order.cash_received = amount_received
    _add_event(
        order, EVENT_CASH_RECEIVED, staff,
        f"{_rs(amount_received)} received, change {_rs(change)}",
    )
    # Tells the customer straight away, so a payment recorded without them paying gets noticed.
    _notify(
        db, order, NOTIFY_PAYMENT_RECEIVED,
        f"Cash payment of {_rs(order.total_amount)} received for order {order.order_id} "
        f"(you gave {_rs(amount_received)}, change {_rs(change)}). Not you? Tell the canteen staff",
    )
    db.commit()
    activity.event(
        f"Order {order.order_id}: cash {_rs(amount_received)} received by {staff.username}, change {_rs(change)}"
    )
    return order


def serve(db: Session, staff: User, order_code: str, pickup_code: str) -> Order:
    """Hand the food over: the order must be READY and PAID, and the customer shows the code."""
    order = lock_order(db, order_code)
    _require_status(order, ORDER_READY, "served")
    if order.payment_status != ORDER_PAYMENT_PAID:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Order {order.order_id} is not paid yet. Collect {_rs(order.total_amount)} in cash "
            f"and record it before handing over the food",
        )
    _check_pickup_code(order, pickup_code)
    order.status = ORDER_SERVED
    _add_event(order, ORDER_SERVED, staff, "Pickup code verified")
    _notify(db, order, NOTIFY_ORDER_SERVED, f"Order {order.order_id} picked up. Enjoy your meal!")
    db.commit()
    activity.event(f"Order {order.order_id} SERVED by {staff.username}")
    return order
