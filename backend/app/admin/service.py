"""The single permanent main canteen admin: read access to every entity, staff approval
and deciding which items the menu has."""
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.security import as_utc, utcnow
from app.cart.service import CartOut, to_cart_out
from app.database.models import (
    ACCOUNT_ACTIVE,
    ACCOUNT_INACTIVE,
    CANTEEN_STAFF,
    NOTIFY_ITEM_REMOVED,
    Cart,
    CartItem,
    Category,
    FoodItem,
    Inventory,
    Notification,
    Order,
    StockAlert,
    User,
    UserSession,
)
from app.menu import service as menu_service
from app.menu.schemas import FoodItemOut, FoodType
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


class FoodItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Paneer Wrap"])
    price: float = Field(..., gt=0, examples=[60])
    description: Optional[str] = Field(None, examples=["Grilled paneer in a soft wrap"])
    # Existing category name, or a new one (it is created).
    category: str = Field(..., min_length=1, max_length=50, examples=["Snacks"])
    food_type: FoodType = "VEG"
    ingredients: List[str] = Field(default_factory=list, examples=[["Paneer", "Wrap", "Onion"]])
    avg_cooking_time_minutes: int = Field(10, ge=1, le=180)
    # Starting stock; staff can restock later with PUT /staff/inventory/{food_id}.
    quantity: int = Field(0, ge=0, le=10000)


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


# ---------- Staff management ----------

def list_staff(db: Session, account_status: Optional[str] = None) -> List[UserWithLoginStatus]:
    staff = users_service.list_users(db, CANTEEN_STAFF)
    if account_status is not None:
        staff = [s for s in staff if s.account_status == account_status]
    return staff


def _get_staff(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.role.name != CANTEEN_STAFF:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found")
    return user


def _staff_out(db: Session, user_id: int) -> UserWithLoginStatus:
    return next(s for s in list_staff(db) if s.id == user_id)


def approve_staff(db: Session, user_id: int) -> UserWithLoginStatus:
    """Approve a pending staff account (or re-activate a deactivated one)."""
    _get_staff(db, user_id).account_status = ACCOUNT_ACTIVE
    db.commit()
    return _staff_out(db, user_id)


def deactivate_staff(db: Session, user_id: int) -> UserWithLoginStatus:
    """Block a staff account (or reject a pending one). Their logins end immediately."""
    user = _get_staff(db, user_id)
    user.account_status = ACCOUNT_INACTIVE
    now = utcnow()
    for s in user.sessions:
        if s.logged_out_at is None:
            s.logged_out_at = now
    db.commit()
    return _staff_out(db, user_id)


# ---------- Menu management ----------

def create_food_item(db: Session, data: FoodItemCreate) -> FoodItemOut:
    name = data.name.strip()
    duplicate = db.scalar(
        select(FoodItem).where(func.lower(FoodItem.name) == name.lower(), FoodItem.removed_at.is_(None))
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{name} is already on the menu")

    category_name = data.category.strip()
    category = db.scalar(select(Category).where(func.lower(Category.name) == category_name.lower()))
    if category is None:
        category = Category(name=category_name)
        db.add(category)
        db.flush()

    food = FoodItem(
        name=name,
        description=(data.description or "").strip() or None,
        category_id=category.id,
        price=data.price,
        food_type=data.food_type,
        ingredients=[i.strip() for i in data.ingredients if i.strip()],
        avg_cooking_time_minutes=data.avg_cooking_time_minutes,
    )
    db.add(food)
    db.flush()
    db.add(Inventory(food_item_id=food.id, quantity=data.quantity, availability=data.quantity > 0))
    db.commit()
    return menu_service.get_food_out(db, food.id)


def remove_food_item(db: Session, food_id: int) -> None:
    """Take an item off the menu. Past orders keep it; carts and "Notify me" requests drop it."""
    food = menu_service.get_food_item(db, food_id)
    food.removed_at = utcnow()
    if food.inventory is not None:
        food.inventory.availability = False

    cart_lines = db.scalars(select(CartItem).where(CartItem.food_item_id == food_id)).unique().all()
    for ci in cart_lines:
        db.add(Notification(
            user_id=ci.cart.user_id,
            food_item_id=food_id,
            type=NOTIFY_ITEM_REMOVED,
            message=f"{food.name} is no longer on the menu and was removed from your cart",
        ))
        db.delete(ci)
    db.execute(delete(StockAlert).where(StockAlert.food_item_id == food_id))
    db.commit()
