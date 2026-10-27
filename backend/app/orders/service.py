import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.auth.security import utcnow
from app.database.models import (
    ADMIN,
    CANTEEN_STAFF,
    NOTIFY_ORDER_PLACED,
    ORDER_PLACED,
    Cart,
    Notification,
    Order,
    OrderItem,
    User,
)
from app.inventory import service as inventory_service
from app.orders.schemas import (
    OrderOut,
    OrderPlacedOut,
    OrderSummaryOut,
    estimated_ready_minutes,
    order_item_out,
)


def to_order_out(order: Order) -> OrderOut:
    return OrderOut(
        order_id=order.order_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        estimated_ready_at=order.estimated_ready_at,
        estimated_ready_minutes=estimated_ready_minutes(order),
        items=[order_item_out(oi) for oi in order.items],
    )


def to_summary(order: Order) -> OrderSummaryOut:
    return OrderSummaryOut(
        order_id=order.order_id,
        status=order.status,
        total_amount=order.total_amount,
        item_count=sum(oi.quantity for oi in order.items),
        created_at=order.created_at,
        estimated_ready_at=order.estimated_ready_at,
    )


def _make_order_code(order: Order) -> str:
    # The DB primary key guarantees uniqueness, e.g. ORD-20261010-0001
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{order.id:04d}"


def place_order(db: Session, user: User) -> OrderPlacedOut:
    """Convert the user's cart into an order in a single transaction.

    Steps: lock cart -> validate -> lock inventory rows -> check stock (not counting
    other customers' active cart holds) -> create order and items -> reduce inventory
    -> clear cart -> notify -> commit.
    """
    # Locking the cart serialises concurrent/repeated "place order" requests from the
    # same user, so a double-tap cannot create two orders from one cart.
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id).with_for_update())
    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty")

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
    )
    db.add(order)
    db.flush()
    order.order_id = _make_order_code(order)
    db.add(
        Notification(
            user_id=user.id,
            type=NOTIFY_ORDER_PLACED,
            message=f"Order {order.order_id} placed. It will be ready in about {cooking_minutes} min",
        )
    )

    cart.items.clear()
    db.commit()
    db.refresh(order)
    activity.event(
        f"Order {order.order_id} placed: Rs {total}, ready in ~{cooking_minutes} min; "
        + ", ".join(stock_changes)
    )

    out = to_order_out(order)
    return OrderPlacedOut(**out.model_dump())


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
    return to_order_out(order)
