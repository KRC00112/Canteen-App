from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Category, FoodItem, Inventory
from app.menu.schemas import CategoryOut, FoodItemOut


def to_food_out(item: FoodItem) -> FoodItemOut:
    inv = item.inventory
    return FoodItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        category_id=item.category_id,
        category=item.category.name,
        price=item.price,
        quantity=inv.quantity if inv else 0,
        available=bool(inv and inv.availability and inv.quantity > 0),
    )


def list_menu(
    db: Session,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    available_only: bool = False,
) -> List[FoodItemOut]:
    stmt = select(FoodItem).order_by(FoodItem.category_id, FoodItem.name)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(FoodItem.name.ilike(pattern) | FoodItem.description.ilike(pattern))
    if category_id is not None:
        stmt = stmt.where(FoodItem.category_id == category_id)
    if available_only:
        stmt = stmt.join(Inventory).where(Inventory.availability.is_(True), Inventory.quantity > 0)
    return [to_food_out(item) for item in db.scalars(stmt).unique()]


def get_food_item(db: Session, food_id: int) -> FoodItem:
    item = db.get(FoodItem, food_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    return item


def list_categories(db: Session) -> List[CategoryOut]:
    return [CategoryOut(id=c.id, name=c.name) for c in db.scalars(select(Category).order_by(Category.id))]
