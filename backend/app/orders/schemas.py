from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class OrderItemOut(BaseModel):
    food_id: int
    food: str
    quantity: int
    price: float
    subtotal: float


class OrderOut(BaseModel):
    order_id: str
    status: str
    total_amount: float
    created_at: Optional[datetime]
    items: List[OrderItemOut]


class OrderPlacedOut(OrderOut):
    message: str = "Order placed successfully"


class OrderSummaryOut(BaseModel):
    order_id: str
    status: str
    total_amount: float
    item_count: int
    created_at: Optional[datetime]
