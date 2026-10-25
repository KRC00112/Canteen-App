"""In-app notifications, read by the app by polling GET /notifications.

Stock changes over time (cart holds expire, other people order), so notifications are
worked out when the customer polls: "Notify me" alerts whose item is available again,
and cart items that can no longer be ordered.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.auth.security import as_utc, utcnow
from app.database.models import (
    NOTIFY_BACK_IN_STOCK,
    NOTIFY_CART_ITEM_LOW_STOCK,
    NOTIFY_CART_ITEM_SOLD_OUT,
    Cart,
    Notification,
    StockAlert,
    User,
)
from app.inventory import service as inventory_service
from app.items import service as items_service


# ---------- Schemas ----------

class NotificationOut(BaseModel):
    id: int
    # BACK_IN_STOCK | CART_ITEM_SOLD_OUT | CART_ITEM_LOW_STOCK | ORDER_PLACED | ITEM_REMOVED
    type: str
    message: str
    food_id: Optional[int]
    created_at: Optional[datetime]
    read: bool


class NotificationsOut(BaseModel):
    unread_count: int
    notifications: List[NotificationOut]


class StockAlertIn(BaseModel):
    food_id: int


class StockAlertOut(BaseModel):
    food_id: int
    food: str
    created_at: Optional[datetime]


# ---------- Logic ----------

def _notify_once(db: Session, user: User, food_id: int, type_: str, message: str) -> None:
    """Add a notification unless the same unread one already exists."""
    exists = db.scalar(
        select(Notification.id).where(
            Notification.user_id == user.id,
            Notification.food_item_id == food_id,
            Notification.type == type_,
            Notification.read_at.is_(None),
        )
    )
    if exists is None:
        db.add(Notification(user_id=user.id, food_item_id=food_id, type=type_, message=message))


def refresh(db: Session, user: User) -> None:
    for alert in db.scalars(select(StockAlert).where(StockAlert.user_id == user.id)).unique():
        food = alert.food_item
        if inventory_service.stock_for_user(db, food.inventory, user.id).available:
            _notify_once(
                db, user, food.id, NOTIFY_BACK_IN_STOCK,
                f"{food.name} is available again - add it to your cart to hold it",
            )
            db.delete(alert)

    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    for ci in cart.items if cart else []:
        if ci.reserved_until and as_utc(ci.reserved_until) > utcnow():
            continue  # an active hold is guaranteed
        food = ci.food_item
        stock = inventory_service.stock_for_user(db, food.inventory, user.id)
        if stock.status == inventory_service.OUT_OF_STOCK:
            _notify_once(
                db, user, food.id, NOTIFY_CART_ITEM_SOLD_OUT,
                f"{food.name} in your cart has sold out",
            )
        elif ci.quantity > stock.free:
            _notify_once(
                db, user, food.id, NOTIFY_CART_ITEM_LOW_STOCK,
                f"{food.name} is in high demand and not enough are left for your cart. "
                f"Reduce the quantity to keep it",
            )
    db.commit()


def to_out(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        type=n.type,
        message=n.message,
        food_id=n.food_item_id,
        created_at=n.created_at,
        read=n.read_at is not None,
    )


def list_notifications(db: Session, user: User, unread_only: bool = False) -> NotificationsOut:
    refresh(db, user)
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(50)
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    items = [to_out(n) for n in db.scalars(stmt)]
    unread = db.scalars(
        select(Notification.id).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ).all()
    return NotificationsOut(unread_count=len(unread), notifications=items)


def mark_read(db: Session, user: User, notification_id: int) -> NotificationOut:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    n.read_at = n.read_at or utcnow()
    db.commit()
    return to_out(n)


def mark_all_read(db: Session, user: User) -> NotificationsOut:
    for n in db.scalars(
        select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ):
        n.read_at = utcnow()
    db.commit()
    return list_notifications(db, user)


def _alert_out(alert: StockAlert) -> StockAlertOut:
    return StockAlertOut(food_id=alert.food_item_id, food=alert.food_item.name, created_at=alert.created_at)


def list_alerts(db: Session, user: User) -> List[StockAlertOut]:
    stmt = select(StockAlert).where(StockAlert.user_id == user.id).order_by(StockAlert.id)
    return [_alert_out(a) for a in db.scalars(stmt).unique()]


def add_alert(db: Session, user: User, food_id: int) -> StockAlertOut:
    food = items_service.get_food_item(db, food_id)
    if inventory_service.stock_for_user(db, food.inventory, user.id).available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{food.name} is available now - add it to your cart",
        )
    alert = db.scalar(
        select(StockAlert).where(StockAlert.user_id == user.id, StockAlert.food_item_id == food_id)
    )
    if alert is None:
        alert = StockAlert(user_id=user.id, food_item_id=food_id)
        db.add(alert)
        db.commit()
        activity.event(f"Notify me: {food.name} when it is back")
        db.refresh(alert)
    return _alert_out(alert)


def remove_alert(db: Session, user: User, food_id: int) -> None:
    alert = db.scalar(
        select(StockAlert).where(StockAlert.user_id == user.id, StockAlert.food_item_id == food_id)
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    activity.event(f"Notify me cancelled: {alert.food_item.name}")
    db.delete(alert)
    db.commit()
