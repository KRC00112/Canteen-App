from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.database.models import (
    ORDER_PLACED,
    PAY_ONLINE,
    PAYMENT_METHOD_ALIASES,
    Order,
    OrderEvent,
    OrderItem,
)


class OrderItemOut(BaseModel):
    food_id: int
    food: str
    food_type: str
    quantity: int
    price: float
    subtotal: float


class OrderEventOut(BaseModel):
    # PLACED | PREPARING | READY | SERVED | CANCELLED | CASH_RECEIVED | REFUNDED
    event: str
    at: datetime
    # Who did it (None = done automatically)
    by: Optional[str]
    by_role: Optional[str]
    note: Optional[str]


class OrderOut(BaseModel):
    order_id: str
    # PLACED -> PREPARING -> READY -> SERVED, or CANCELLED (only possible while PLACED)
    status: str
    total_amount: float
    created_at: Optional[datetime]
    # Based on the slowest item's average cooking time.
    estimated_ready_at: Optional[datetime]
    estimated_ready_minutes: Optional[int]
    items: List[OrderItemOut]
    # Razorpay payment that paid for it (None for cash, or if placed while payments were off).
    payment_id: Optional[str] = None
    # UPI | CASH_ON_PICKUP
    payment_method: str
    # PENDING (pay at the counter) | PAID | REFUND_PENDING | REFUNDED | CANCELLED (nothing was paid)
    payment_status: str
    paid_at: Optional[datetime] = None
    # Show this at the counter: staff need it to take cash and hand over the food.
    # Only sent to the customer who placed the order.
    pickup_code: Optional[str] = None
    can_cancel: bool
    timeline: List[OrderEventOut]


class OrderPlacedOut(OrderOut):
    message: str = "Order placed successfully"


class OrderSummaryOut(BaseModel):
    order_id: str
    status: str
    total_amount: float
    item_count: int
    created_at: Optional[datetime]
    estimated_ready_at: Optional[datetime]
    payment_method: str
    payment_status: str
    can_cancel: bool


class PlaceOrderIn(BaseModel):
    # UPI = pay with Razorpay first (POST /payments/orders + /payments/verify).
    # CASH_ON_PICKUP = pay at the counter; the food is handed over only after staff record the cash.
    # Case-insensitive; ONLINE / CASH also work.
    payment_method: Literal["UPI", "CASH_ON_PICKUP"] = PAY_ONLINE

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalise(cls, v):
        if isinstance(v, str):
            v = v.strip().upper()
            return PAYMENT_METHOD_ALIASES.get(v, v)
        return v


class CancelOrderIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=200, examples=["Ordered by mistake"])


def order_item_out(oi: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        food_id=oi.food_item_id,
        food=oi.food_item.name,
        food_type=oi.food_item.food_type,
        quantity=oi.quantity,
        price=oi.price,
        subtotal=oi.price * oi.quantity,
    )


def order_event_out(e: OrderEvent) -> OrderEventOut:
    return OrderEventOut(
        event=e.event,
        at=e.created_at,
        by=e.changed_by.username if e.changed_by else None,
        by_role=e.changed_by.role.name if e.changed_by else None,
        note=e.note,
    )


def can_cancel(order: Order) -> bool:
    return order.status == ORDER_PLACED


def estimated_ready_minutes(order: Order) -> Optional[int]:
    if order.estimated_ready_at is None or order.created_at is None:
        return None
    return round((order.estimated_ready_at - order.created_at).total_seconds() / 60)
