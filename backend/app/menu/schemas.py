from typing import List, Literal, Optional

from pydantic import BaseModel

FoodType = Literal["VEG", "NON_VEG"]


class CategoryOut(BaseModel):
    id: int
    name: str
    # Which of VEG / NON_VEG items this category contains.
    food_types: List[FoodType]


class FoodItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category_id: int
    category: str
    food_type: FoodType
    is_veg: bool
    price: float
    ingredients: List[str]
    avg_cooking_time_minutes: int
    available: bool
    # IN_STOCK | LOW_STOCK | HIGH_DEMAND | ALL_RESERVED | OUT_OF_STOCK
    stock_status: str
    stock_message: str
    # Most this customer can have in their cart right now (disable "+1" beyond it).
    max_order_quantity: int
    # Among the most ordered items of the last 24 hours.
    popular: bool
    # True when the logged-in customer asked to be notified when it is available again.
    notify_me: bool = False
