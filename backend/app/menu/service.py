from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import NON_VEG, VEG, Category, FoodItem, StockAlert, User
from app.inventory import service as inventory_service
from app.inventory.service import Stock
from app.menu.schemas import CategoryOut, FoodItemOut


def to_food_out(item: FoodItem, stock: Stock, popular: bool = False, notify_me: bool = False) -> FoodItemOut:
    return FoodItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        category_id=item.category_id,
        category=item.category.name,
        food_type=item.food_type,
        is_veg=item.food_type == VEG,
        price=item.price,
        ingredients=item.ingredients or [],
        avg_cooking_time_minutes=item.avg_cooking_time_minutes,
        available=stock.available,
        stock_status=stock.status,
        stock_message=stock.message,
        max_order_quantity=stock.max_order_quantity,
        popular=popular,
        notify_me=notify_me,
    )


def _alerted_food_ids(db: Session, user: Optional[User]) -> set:
    if user is None:
        return set()
    return set(db.scalars(select(StockAlert.food_item_id).where(StockAlert.user_id == user.id)))


def list_menu(
    db: Session,
    user: Optional[User] = None,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    food_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = False,
) -> List[FoodItemOut]:
    stmt = select(FoodItem).order_by(FoodItem.category_id, FoodItem.name)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(FoodItem.name.ilike(pattern) | FoodItem.description.ilike(pattern))
    if category_id is not None:
        stmt = stmt.where(FoodItem.category_id == category_id)
    if food_type is not None:
        stmt = stmt.where(FoodItem.food_type == food_type)
    if min_price is not None:
        stmt = stmt.where(FoodItem.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(FoodItem.price <= max_price)

    user_id = user.id if user else None
    holds = inventory_service.active_holds(db, user_id)
    popular = inventory_service.popular_food_ids(db)
    alerted = _alerted_food_ids(db, user)

    result = []
    for item in db.scalars(stmt).unique():
        held, people = holds.get(item.id, (0, 0))
        stock = inventory_service.compute_stock(item.inventory, held, people, item.id in popular)
        if available_only and not stock.available:
            continue
        result.append(to_food_out(item, stock, item.id in popular, item.id in alerted))
    return result


def get_food_item(db: Session, food_id: int) -> FoodItem:
    item = db.get(FoodItem, food_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    return item


def get_food_out(db: Session, food_id: int, user: Optional[User] = None) -> FoodItemOut:
    item = get_food_item(db, food_id)
    stock = inventory_service.stock_for_user(db, item.inventory, user.id if user else None)
    popular = item.id in inventory_service.popular_food_ids(db)
    return to_food_out(item, stock, popular, item.id in _alerted_food_ids(db, user))


def list_categories(db: Session) -> List[CategoryOut]:
    types = {}
    for category_id, food_type in db.execute(select(FoodItem.category_id, FoodItem.food_type).distinct()):
        types.setdefault(category_id, set()).add(food_type)
    return [
        CategoryOut(id=c.id, name=c.name, food_types=[t for t in (VEG, NON_VEG) if t in types.get(c.id, ())])
        for c in db.scalars(select(Category).order_by(Category.id))
    ]
