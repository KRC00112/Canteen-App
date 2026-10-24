from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.auth.security import as_utc, utcnow
from app.config import CART_HOLD_MINUTES
from app.database.models import VEG, Cart, CartItem, User
from app.inventory import service as inventory_service
from app.menu import service as menu_service


# ---------- Schemas ----------

class AddCartItem(BaseModel):
    food_id: int
    quantity: int = Field(1, ge=1, le=50)


class UpdateCartItem(BaseModel):
    quantity: int = Field(..., ge=1, le=50)


class CartItemOut(BaseModel):
    item_id: int
    food_id: int
    food: str
    food_type: str
    is_veg: bool
    avg_cooking_time_minutes: int
    quantity: int
    price: float
    subtotal: float
    # False when this quantity can no longer be ordered (sold out / taken by others).
    available: bool
    stock_status: str
    max_order_quantity: int
    # The stock is held for you until this time; after that others may take it.
    reserved_until: Optional[datetime]
    reservation_active: bool
    # Show this under the item, e.g. "Held for you for 10 min" or "Sold out - remove it".
    message: str


class CartOut(BaseModel):
    items: List[CartItemOut]
    item_count: int
    subtotal: float
    total: float
    # Items are cooked in parallel, so this is the slowest item's average cooking time.
    estimated_ready_minutes: int
    # True when every item can be ordered; otherwise checkout will fail.
    can_checkout: bool


# ---------- Logic ----------

def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def _item_message(ci: CartItem, available: bool, stock: inventory_service.Stock) -> str:
    if stock.status == inventory_service.OUT_OF_STOCK:
        return "Sold out - please remove it from your cart"
    if not available:
        return "Not enough left for this quantity - others reserved it first. Reduce the quantity"
    if ci.reserved_until and as_utc(ci.reserved_until) > utcnow():
        minutes = max(1, int((as_utc(ci.reserved_until) - utcnow()).total_seconds() // 60))
        return f"Held for you for {minutes} more min - check out before it expires"
    if stock.status in (inventory_service.HIGH_DEMAND, inventory_service.LOW_STOCK):
        return "Hold expired and only a few are left - check out now or others may take it"
    return f"Hold expired - change the quantity or check out to hold it again for {CART_HOLD_MINUTES} min"


def to_cart_out(db: Session, cart: Cart) -> CartOut:
    holds = inventory_service.active_holds(db, cart.user_id, [ci.food_item_id for ci in cart.items])
    items = []
    for ci in cart.items:
        food = ci.food_item
        held, people = holds.get(food.id, (0, 0))
        stock = inventory_service.compute_stock(food.inventory, held, people)
        # The customer's own quantity counts as available if it fits in the unreserved stock.
        available = stock.status != inventory_service.OUT_OF_STOCK and ci.quantity <= stock.free
        active = bool(ci.reserved_until and as_utc(ci.reserved_until) > utcnow())
        items.append(
            CartItemOut(
                item_id=ci.id,
                food_id=food.id,
                food=food.name,
                food_type=food.food_type,
                is_veg=food.food_type == VEG,
                avg_cooking_time_minutes=food.avg_cooking_time_minutes,
                quantity=ci.quantity,
                price=food.price,
                subtotal=food.price * ci.quantity,
                available=available,
                stock_status=stock.status,
                max_order_quantity=max(stock.max_order_quantity, ci.quantity if available else 0),
                reserved_until=ci.reserved_until,
                reservation_active=active and available,
                message=_item_message(ci, available, stock),
            )
        )
    subtotal = sum(i.subtotal for i in items)
    return CartOut(
        items=items,
        item_count=sum(i.quantity for i in items),
        subtotal=round(subtotal, 2),
        # No taxes/fees yet, so total equals subtotal.
        total=round(subtotal, 2),
        estimated_ready_minutes=max((i.avg_cooking_time_minutes for i in items), default=0),
        can_checkout=bool(items) and all(i.available for i in items),
    )


def get_cart(db: Session, user: User) -> CartOut:
    cart = get_or_create_cart(db, user)
    db.commit()
    return to_cart_out(db, cart)


def add_item(db: Session, user: User, data: AddCartItem) -> CartOut:
    food = menu_service.get_food_item(db, data.food_id)
    cart = get_or_create_cart(db, user)

    existing = next((ci for ci in cart.items if ci.food_item_id == food.id), None)
    new_quantity = data.quantity + (existing.quantity if existing else 0)

    # Lock the stock row so two customers can't both hold the last portion.
    inv = inventory_service.get_inventory(db, food.id, lock=True)
    inventory_service.ensure_can_hold(db, inv, user.id, new_quantity, food.name)

    if existing:
        existing.quantity = new_quantity
        existing.reserved_until = inventory_service.hold_expiry()
    else:
        cart.items.append(
            CartItem(
                food_item_id=food.id,
                quantity=data.quantity,
                reserved_until=inventory_service.hold_expiry(),
            )
        )
    db.commit()
    db.refresh(cart)
    activity.event(
        f"Cart: {food.name} x{new_quantity}, stock held {CART_HOLD_MINUTES} min "
        f"(stock {inv.quantity})"
    )
    return to_cart_out(db, cart)


def _get_user_cart_item(db: Session, user: User, item_id: int) -> CartItem:
    item = db.scalar(
        select(CartItem).join(Cart).where(CartItem.id == item_id, Cart.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    return item


def update_item(db: Session, user: User, item_id: int, data: UpdateCartItem) -> CartOut:
    item = _get_user_cart_item(db, user, item_id)
    inv = inventory_service.get_inventory(db, item.food_item_id, lock=True)
    # Lowering the quantity within an active hold is always allowed; anything else renews
    # the hold, so it must fit the stock that isn't held by others.
    hold_active = bool(item.reserved_until and as_utc(item.reserved_until) > utcnow())
    if data.quantity > item.quantity or not hold_active:
        inventory_service.ensure_can_hold(db, inv, user.id, data.quantity, item.food_item.name)
    old_quantity = item.quantity
    item.quantity = data.quantity
    item.reserved_until = inventory_service.hold_expiry()
    db.commit()
    activity.event(f"Cart: {item.food_item.name} x{old_quantity} -> x{data.quantity}, hold renewed")
    return get_cart(db, user)


def remove_item(db: Session, user: User, item_id: int) -> CartOut:
    item = _get_user_cart_item(db, user, item_id)
    activity.event(f"Cart: removed {item.food_item.name}, stock released")
    db.delete(item)
    db.commit()
    db.expire_all()
    return get_cart(db, user)


def clear_cart(db: Session, user: User) -> CartOut:
    cart = get_or_create_cart(db, user)
    activity.event(f"Cart cleared ({len(cart.items)} item(s) released)")
    cart.items.clear()
    db.commit()
    return to_cart_out(db, cart)
