"""Stock rules.

Stock in someone's cart is *held* for CART_HOLD_MINUTES after they last add/change it,
so when only a few portions are left, the people who already have them in their cart
are guaranteed to get them, and others see "reserved" instead of failing at checkout.
When stock is low, each customer can take at most LOW_STOCK_MAX_PER_CUSTOMER.

Customers never see exact stock numbers, only a status and a message.
"""
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Iterable, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.auth.security import utcnow
from app.config import CART_HOLD_MINUTES, LOW_STOCK_MAX_PER_CUSTOMER, LOW_STOCK_THRESHOLD
from app.database.models import ORDER_CANCELLED, Cart, CartItem, FoodItem, Inventory, Order, OrderItem

# Same upper bound as the cart request schemas.
MAX_CART_QUANTITY = 50
# Items ordered at least this often in the last 24 h (and in the top 3) are "popular".
POPULAR_TOP_N = 3

IN_STOCK = "IN_STOCK"
LOW_STOCK = "LOW_STOCK"
HIGH_DEMAND = "HIGH_DEMAND"
ALL_RESERVED = "ALL_RESERVED"
OUT_OF_STOCK = "OUT_OF_STOCK"


@dataclass
class Stock:
    status: str
    message: str
    available: bool
    max_order_quantity: int
    # Internal numbers; only exposed to staff.
    free: int
    others_holding: int


def get_inventory(db: Session, food_id: int, lock: bool = False) -> Inventory:
    """Fetch the inventory row for a food item.

    lock=True takes a row lock (SELECT ... FOR UPDATE) so that concurrent orders
    and cart holds cannot claim the same stock.
    """
    stmt = (
        select(Inventory)
        .join(FoodItem)
        .where(Inventory.food_item_id == food_id, FoodItem.removed_at.is_(None))
    )
    if lock:
        stmt = stmt.with_for_update(of=Inventory)
    inv = db.scalar(stmt)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    return inv


def is_available(inv: Inventory) -> bool:
    return inv.availability and inv.quantity > 0


def hold_expiry():
    return utcnow() + timedelta(minutes=CART_HOLD_MINUTES)


def active_holds(
    db: Session, exclude_user_id: Optional[int] = None, food_ids: Optional[Iterable[int]] = None
) -> Dict[int, Tuple[int, int]]:
    """food_id -> (units held, number of customers holding) for unexpired cart holds."""
    stmt = (
        select(CartItem.food_item_id, func.sum(CartItem.quantity), func.count(distinct(Cart.user_id)))
        .join(Cart)
        .where(CartItem.reserved_until > utcnow())
        .group_by(CartItem.food_item_id)
    )
    if exclude_user_id is not None:
        stmt = stmt.where(Cart.user_id != exclude_user_id)
    if food_ids is not None:
        stmt = stmt.where(CartItem.food_item_id.in_(list(food_ids)))
    return {food_id: (int(units), int(people)) for food_id, units, people in db.execute(stmt)}


def units_ordered_last_24h(db: Session) -> Dict[int, int]:
    stmt = (
        select(OrderItem.food_item_id, func.sum(OrderItem.quantity))
        .join(Order)
        .where(Order.created_at > utcnow() - timedelta(hours=24), Order.status != ORDER_CANCELLED)
        .group_by(OrderItem.food_item_id)
    )
    return {food_id: int(units) for food_id, units in db.execute(stmt)}


def popular_food_ids(db: Session) -> set:
    ranked = sorted(units_ordered_last_24h(db).items(), key=lambda kv: kv[1], reverse=True)
    return {food_id for food_id, units in ranked[:POPULAR_TOP_N] if units > 0}


def compute_stock(
    inv: Optional[Inventory], held_by_others: int = 0, others_holding: int = 0, popular: bool = False
) -> Stock:
    if inv is None or not is_available(inv):
        return Stock(OUT_OF_STOCK, "Sold out", False, 0, 0, others_holding)

    free = max(inv.quantity - held_by_others, 0)
    if free == 0:
        return Stock(
            ALL_RESERVED,
            f"All remaining portions are in other customers' carts. They may free up within "
            f"{CART_HOLD_MINUTES} min - tap 'Notify me'",
            False,
            0,
            0,
            others_holding,
        )

    low = inv.quantity <= LOW_STOCK_THRESHOLD
    limit = min(free, LOW_STOCK_MAX_PER_CUSTOMER if low else MAX_CART_QUANTITY)
    if free <= LOW_STOCK_THRESHOLD and (others_holding > 0 or popular):
        if others_holding:
            who = f"{others_holding} other customer(s) have it in their cart"
        else:
            who = "it is one of today's most ordered items"
        return Stock(
            HIGH_DEMAND,
            f"High demand: only a few left and {who}. Add it to your cart to hold it for {CART_HOLD_MINUTES} min",
            True,
            limit,
            free,
            others_holding,
        )
    if free <= LOW_STOCK_THRESHOLD:
        return Stock(LOW_STOCK, "Only a few left", True, limit, free, others_holding)
    return Stock(IN_STOCK, "Available", True, limit, free, others_holding)


def stock_for_user(db: Session, inv: Optional[Inventory], user_id: Optional[int]) -> Stock:
    """Stock as seen by one customer (their own cart hold doesn't count against them)."""
    if inv is None:
        return compute_stock(None)
    held, people = active_holds(db, user_id, [inv.food_item_id]).get(inv.food_item_id, (0, 0))
    return compute_stock(inv, held, people, inv.food_item_id in popular_food_ids(db))


def ensure_can_hold(db: Session, inv: Inventory, user_id: int, requested: int, food_name: str) -> None:
    """Check a customer may have `requested` units in their cart (inventory row should be locked)."""
    stock = stock_for_user(db, inv, user_id)
    if requested <= stock.max_order_quantity:
        return
    if stock.status == OUT_OF_STOCK:
        detail = f"{food_name} is sold out. Tap 'Notify me' to get an alert when it is back"
    elif stock.status == ALL_RESERVED:
        detail = (
            f"All remaining {food_name} are reserved in other customers' carts. "
            f"Try again in a few minutes or tap 'Notify me'"
        )
    elif inv.quantity <= LOW_STOCK_THRESHOLD and stock.free >= LOW_STOCK_MAX_PER_CUSTOMER:
        detail = f"{food_name} is running low: maximum {LOW_STOCK_MAX_PER_CUSTOMER} per customer"
    else:
        detail = f"You can have at most {stock.max_order_quantity} {food_name} right now"
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def ensure_quantity_available(
    db: Session, inv: Inventory, user_id: int, requested: int, food_name: str
) -> None:
    """Checkout check: the requested units must not eat into other customers' active holds."""
    held, _ = active_holds(db, user_id, [inv.food_item_id]).get(inv.food_item_id, (0, 0))
    if not is_available(inv):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{food_name} is sold out"
        )
    if requested > inv.quantity - held:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough {food_name} left - others reserved it first. Please reduce the quantity",
        )


def set_quantity(inv: Inventory, quantity: int) -> None:
    """Update stock; items automatically become unavailable at zero."""
    inv.quantity = max(quantity, 0)
    inv.availability = inv.quantity > 0
