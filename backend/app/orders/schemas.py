from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.database.models import Order, OrderItem
from app.database.models import PAYMENT_UPI


class PlaceOrderIn(BaseModel):
    payment_method: str = PAYMENT_UPI


class OrderItemOut(BaseModel):
    food_id: int
    food: str
    food_type: str
    quantity: int
    price: float
    subtotal: float


class OrderOut(BaseModel):
    order_id: str
    status: str
    total_amount: float
    payment_method: str
    payment_status: str
    created_at: Optional[datetime]
    # Based on the slowest item's average cooking time.
    estimated_ready_at: Optional[datetime]
    estimated_ready_minutes: Optional[int]
    items: List[OrderItemOut]
    # Razorpay payment that paid for it (None if placed while payments were off).
    payment_id: Optional[str] = None


class OrderPlacedOut(OrderOut):
    message: str = "Order placed successfully"


class OrderSummaryOut(BaseModel):
    order_id: str
    status: str
    total_amount: float
    item_count: int
    created_at: Optional[datetime]
    estimated_ready_at: Optional[datetime]


def order_item_out(oi: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        food_id=oi.food_item_id,
        food=oi.food_item.name,
        food_type=oi.food_item.food_type,
        quantity=oi.quantity,
        price=oi.price,
        subtotal=oi.price * oi.quantity,
    )


def estimated_ready_minutes(order: Order) -> Optional[int]:
    if order.estimated_ready_at is None or order.created_at is None:
        return None
    return round((order.estimated_ready_at - order.created_at).total_seconds() / 60)
