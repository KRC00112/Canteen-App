from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Order
from app.orders.schemas import OrderItemOut


class StaffOrderOut(BaseModel):
    order_id: str
    customer: str
    institute_id: str
    total: float
    status: str
    created_at: Optional[datetime]
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
            items=[
                OrderItemOut(
                    food_id=oi.food_item_id,
                    food=oi.food_item.name,
                    quantity=oi.quantity,
                    price=oi.price,
                    subtotal=oi.price * oi.quantity,
                )
                for oi in o.items
            ],
        )
        for o in db.scalars(stmt).unique()
    ]
