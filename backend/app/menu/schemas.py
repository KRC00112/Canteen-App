from typing import Optional

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str


class FoodItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category_id: int
    category: str
    price: float
    quantity: int
    available: bool
