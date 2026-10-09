from typing import List

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Cart, CartItem, User
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
    quantity: int
    price: float
    subtotal: float
    available: bool


class CartOut(BaseModel):
    items: List[CartItemOut]
    item_count: int
    subtotal: float
    total: float


# ---------- Logic ----------

def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def to_cart_out(cart: Cart) -> CartOut:
    items = []
    for ci in cart.items:
        food = ci.food_item
        inv = food.inventory
        items.append(
            CartItemOut(
                item_id=ci.id,
                food_id=food.id,
                food=food.name,
                quantity=ci.quantity,
                price=food.price,
                subtotal=food.price * ci.quantity,
                available=bool(inv and inventory_service.is_available(inv) and ci.quantity <= inv.quantity),
            )
        )
    subtotal = sum(i.subtotal for i in items)
    return CartOut(
        items=items,
        item_count=sum(i.quantity for i in items),
        subtotal=round(subtotal, 2),
        # No taxes/fees yet, so total equals subtotal.
        total=round(subtotal, 2),
    )


def get_cart(db: Session, user: User) -> CartOut:
    cart = get_or_create_cart(db, user)
    db.commit()
    return to_cart_out(cart)


def add_item(db: Session, user: User, data: AddCartItem) -> CartOut:
    food = menu_service.get_food_item(db, data.food_id)
    cart = get_or_create_cart(db, user)

    existing = next((ci for ci in cart.items if ci.food_item_id == food.id), None)
    new_quantity = data.quantity + (existing.quantity if existing else 0)

    inv = inventory_service.get_inventory(db, food.id)
    inventory_service.ensure_quantity_available(inv, new_quantity, food.name)

    if existing:
        existing.quantity = new_quantity
    else:
        cart.items.append(CartItem(food_item_id=food.id, quantity=data.quantity))
    db.commit()
    db.refresh(cart)
    return to_cart_out(cart)


def _get_user_cart_item(db: Session, user: User, item_id: int) -> CartItem:
    item = db.scalar(
        select(CartItem).join(Cart).where(CartItem.id == item_id, Cart.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    return item


def update_item(db: Session, user: User, item_id: int, data: UpdateCartItem) -> CartOut:
    item = _get_user_cart_item(db, user, item_id)
    inv = inventory_service.get_inventory(db, item.food_item_id)
    inventory_service.ensure_quantity_available(inv, data.quantity, item.food_item.name)
    item.quantity = data.quantity
    db.commit()
    return get_cart(db, user)


def remove_item(db: Session, user: User, item_id: int) -> CartOut:
    item = _get_user_cart_item(db, user, item_id)
    db.delete(item)
    db.commit()
    db.expire_all()
    return get_cart(db, user)


def clear_cart(db: Session, user: User) -> CartOut:
    cart = get_or_create_cart(db, user)
    cart.items.clear()
    db.commit()
    return to_cart_out(cart)
