from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import get_optional_customer
from app.database.database import get_db
from app.database.models import User
from app.menu import service
from app.menu.schemas import CategoryOut, FoodItemOut, FoodType

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("", response_model=List[FoodItemOut])
def get_menu(
    search: Optional[str] = Query(None, description="Search by food name or description"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    food_type: Optional[FoodType] = Query(None, description="VEG or NON_VEG"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    available_only: bool = Query(False, description="Only show items that can be ordered now"),
    user: Optional[User] = Depends(get_optional_customer),
    db: Session = Depends(get_db),
):
    """List menu items with price, Veg/Non-Veg type, cooking time and stock status.

    The token is optional; when sent, stock in your own cart is not counted as reserved.
    """
    return service.list_menu(
        db, user, search, category_id, food_type, min_price, max_price, available_only
    )


@router.get("/categories", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)


@router.get("/{food_id}", response_model=FoodItemOut)
def get_food_item(
    food_id: int, user: Optional[User] = Depends(get_optional_customer), db: Session = Depends(get_db)
):
    return service.get_food_out(db, food_id, user)
