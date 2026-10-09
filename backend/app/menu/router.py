from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.menu import service
from app.menu.schemas import CategoryOut, FoodItemOut

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("", response_model=List[FoodItemOut])
def get_menu(
    search: Optional[str] = Query(None, description="Search by food name or description"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    available_only: bool = Query(False, description="Only show items currently in stock"),
    db: Session = Depends(get_db),
):
    """List menu items with price and live availability."""
    return service.list_menu(db, search, category_id, available_only)


@router.get("/categories", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)


@router.get("/{food_id}", response_model=FoodItemOut)
def get_food_item(food_id: int, db: Session = Depends(get_db)):
    return service.to_food_out(service.get_food_item(db, food_id))
