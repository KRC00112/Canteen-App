"""Read access to every entity for the single permanent main canteen admin."""
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import as_utc, utcnow
from app.cart.service import CartOut, to_cart_out
from app.database.models import Cart, Notification, Order, StockAlert, User, UserSession
from app.notifications.service import NotificationOut, StockAlertOut, to_out
from app.orders.schemas import OrderOut
from app.orders.service import to_order_out
from app.staff.service import StaffOrderOut, list_orders
from app.users import service as users_service
from app.users.schemas import UserWithLoginStatus


# ---------- Schemas ----------

class AdminSessionOut(BaseModel):
    user_id: int
    institute_id: str
    username: str
    role: str
    session_id: str
    logged_in_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    logged_out_at: Optional[datetime]
    device: Optional[str]
    ip_address: Optional[str]
    active: bool


class AdminCartOut(BaseModel):
    user_id: int
    institute_id: str
    username: str
    cart: CartOut


class AdminNotificationOut(NotificationOut):
    user_id: int
    username: str


class AdminStockAlertOut(StockAlertOut):
    user_id: int
    username: str


class AdminUserDetail(UserWithLoginStatus):
    """Everything stored about one user (customer details for students and faculty)."""

    sessions: List[AdminSessionOut]
    cart: Optional[CartOut]
    orders: List[OrderOut]
    total_spent: float
    notifications: List[NotificationOut]
    stock_alerts: List[StockAlertOut]


# ---------- Logic ----------

def _session_out(s: UserSession) -> AdminSessionOut:
    u = s.user
    return AdminSessionOut(
        user_id=u.id,
        institute_id=u.institute_id,
        username=u.username,
        role=u.role.name,
        session_id=s.session_id,
        logged_in_at=s.created_at,
        last_seen_at=s.last_seen_at,
        expires_at=s.expires_at,
        logged_out_at=s.logged_out_at,
        device=s.device,
        ip_address=s.ip_address,
        active=s.logged_out_at is None and as_utc(s.expires_at) > utcnow(),
    )


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_detail(db: Session, user_id: int) -> AdminUserDetail:
    user = _get_user(db, user_id)
    summary = next(u for u in users_service.list_users(db) if u.id == user_id)
    sessions = db.scalars(
        select(UserSession).where(UserSession.user_id == user_id).order_by(UserSession.created_at.desc())
    ).unique()
    orders = db.scalars(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc(), Order.id.desc())
    ).unique().all()
    cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
    notifications = db.scalars(
        select(Notification).where(Notification.user_id == user_id).order_by(Notification.id.desc())
    )
    alerts = db.scalars(select(StockAlert).where(StockAlert.user_id == user_id)).unique()
    return AdminUserDetail(
        **summary.model_dump(),
        sessions=[_session_out(s) for s in sessions],
        cart=to_cart_out(db, cart) if cart is not None else None,
        orders=[to_order_out(o) for o in orders],
        total_spent=round(float(sum(o.total_amount for o in orders)), 2),
        notifications=[to_out(n) for n in notifications],
        stock_alerts=[
            StockAlertOut(food_id=a.food_item_id, food=a.food_item.name, created_at=a.created_at)
            for a in alerts
        ],
    )


def list_all_orders(
    db: Session, order_status: Optional[str] = None, user_id: Optional[int] = None
) -> List[StaffOrderOut]:
    orders = list_orders(db, order_status)
    if user_id is None:
        return orders
    institute_id = _get_user(db, user_id).institute_id
    return [o for o in orders if o.institute_id == institute_id]


def get_order(db: Session, order_code: str) -> StaffOrderOut:
    order = next((o for o in list_orders(db) if o.order_id == order_code), None)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def list_sessions(db: Session, active_only: bool = False) -> List[AdminSessionOut]:
    stmt = select(UserSession).order_by(UserSession.created_at.desc())
    if active_only:
        stmt = stmt.where(UserSession.logged_out_at.is_(None), UserSession.expires_at > utcnow())
    return [_session_out(s) for s in db.scalars(stmt).unique()]


def list_carts(db: Session) -> List[AdminCartOut]:
    """Every cart that has at least one item."""
    return [
        AdminCartOut(
            user_id=cart.user_id,
            institute_id=cart.user.institute_id,
            username=cart.user.username,
            cart=to_cart_out(db, cart),
        )
        for cart in db.scalars(select(Cart).order_by(Cart.id))
        if cart.items
    ]


def list_notifications(db: Session, user_id: Optional[int] = None) -> List[AdminNotificationOut]:
    stmt = select(Notification).order_by(Notification.id.desc())
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    users = {u.id: u.username for u in db.scalars(select(User))}
    return [
        AdminNotificationOut(**to_out(n).model_dump(), user_id=n.user_id, username=users[n.user_id])
        for n in db.scalars(stmt)
    ]


def list_stock_alerts(db: Session) -> List[AdminStockAlertOut]:
    users = {u.id: u.username for u in db.scalars(select(User))}
    return [
        AdminStockAlertOut(
            food_id=a.food_item_id,
            food=a.food_item.name,
            created_at=a.created_at,
            user_id=a.user_id,
            username=users[a.user_id],
        )
        for a in db.scalars(select(StockAlert).order_by(StockAlert.id.desc())).unique()
    ]
