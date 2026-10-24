from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.database.models import FoodItem, Order
from app.inventory import service as inventory_service
from app.menu import service as menu_service
from app.menu.schemas import FoodItemOut, FoodType
from app.orders.schemas import OrderItemOut, order_item_out


class StaffOrderOut(BaseModel):
    order_id: str
    customer: str
    institute_id: str
    total: float
    status: str
    created_at: Optional[datetime]
    estimated_ready_at: Optional[datetime]
    items: List[OrderItemOut]


def list_orders(db: Session, status: Optional[str] = None) -> List[StaffOrderOut]:
    stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    if status:
        stmt = stmt.where(Order.status == status.upper())
    return [
        StaffOrderOut(
            order_id=o.order_id,
            customer=o.user.username,
            institute_id=o.user.institute_id,
            total=o.total_amount,
            status=o.status,
            created_at=o.created_at,
            estimated_ready_at=o.estimated_ready_at,
            items=[order_item_out(oi) for oi in o.items],
        )
        for o in db.scalars(stmt).unique()
    ]


# ---------- Inventory & menu management ----------

class StaffInventoryOut(BaseModel):
    food_id: int
    food: str
    category: str
    food_type: str
    quantity: int
    available: bool
    # Units held right now in customers' carts, and by how many customers.
    held_in_carts: int
    customers_holding: int
    ordered_last_24h: int
    stock_status: str


class InventoryUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=10000)
    # Optional manual switch, e.g. to stop selling an item that is still in stock.
    available: Optional[bool] = None


class FoodItemUpdate(BaseModel):
    food_type: Optional[FoodType] = None
    ingredients: Optional[List[str]] = None
    avg_cooking_time_minutes: Optional[int] = Field(None, ge=1, le=180)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None


def list_inventory(db: Session) -> List[StaffInventoryOut]:
    holds = inventory_service.active_holds(db)
    ordered = inventory_service.units_ordered_last_24h(db)
    popular = inventory_service.popular_food_ids(db)
    result = []
    on_menu = select(FoodItem).where(FoodItem.removed_at.is_(None))
    for food in db.scalars(on_menu.order_by(FoodItem.category_id, FoodItem.name)).unique():
        inv = food.inventory
        held, people = holds.get(food.id, (0, 0))
        result.append(
            StaffInventoryOut(
                food_id=food.id,
                food=food.name,
                category=food.category.name,
                food_type=food.food_type,
                quantity=inv.quantity if inv else 0,
                available=bool(inv and inventory_service.is_available(inv)),
                held_in_carts=held,
                customers_holding=people,
                ordered_last_24h=ordered.get(food.id, 0),
                stock_status=inventory_service.compute_stock(inv, held, people, food.id in popular).status,
            )
        )
    return result


def update_inventory(db: Session, food_id: int, data: InventoryUpdate) -> StaffInventoryOut:
    inv = inventory_service.get_inventory(db, food_id, lock=True)
    old_quantity = inv.quantity
    inventory_service.set_quantity(inv, data.quantity)
    if data.available is not None:
        inv.availability = data.available and inv.quantity > 0
    db.commit()
    activity.event(
        f"Stock: {inv.food_item.name} {old_quantity} -> {inv.quantity}"
        + ("" if inv.availability else " (not available)")
    )
    return next(i for i in list_inventory(db) if i.food_id == food_id)


def update_food_item(db: Session, food_id: int, data: FoodItemUpdate) -> FoodItemOut:
    food = menu_service.get_food_item(db, food_id)
    changes = data.model_dump(exclude_unset=True)
    if "ingredients" in changes:
        changes["ingredients"] = [i.strip() for i in changes["ingredients"] or [] if i.strip()]
    for field, value in changes.items():
        setattr(food, field, value)
    db.commit()
    activity.event(f"Menu: edited {food.name} ({', '.join(changes) or 'no changes'})")
    return menu_service.get_food_out(db, food_id)
