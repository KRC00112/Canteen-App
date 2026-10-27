from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

# Role names
STUDENT = "STUDENT"
FACULTY = "FACULTY"
CANTEEN_STAFF = "CANTEEN_STAFF"
ADMIN = "ADMIN"
ALL_ROLES = [STUDENT, FACULTY, CANTEEN_STAFF, ADMIN]

# Account status
ACCOUNT_ACTIVE = "ACTIVE"
ACCOUNT_INACTIVE = "INACTIVE"
# Self-registered staff wait in this state until the admin approves them.
ACCOUNT_PENDING = "PENDING"

# Order status (only PLACED is used for Demo 1)
ORDER_PLACED = "PLACED"

# Every food item is either veg or non-veg.
VEG = "VEG"
NON_VEG = "NON_VEG"
FOOD_TYPES = [VEG, NON_VEG]

# Notification types
NOTIFY_BACK_IN_STOCK = "BACK_IN_STOCK"
NOTIFY_CART_ITEM_SOLD_OUT = "CART_ITEM_SOLD_OUT"
NOTIFY_CART_ITEM_LOW_STOCK = "CART_ITEM_LOW_STOCK"
NOTIFY_ORDER_PLACED = "ORDER_PLACED"
NOTIFY_ITEM_REMOVED = "ITEM_REMOVED"

# Razorpay payment status: order created -> signature verified -> used for one canteen order.
PAYMENT_CREATED = "CREATED"
PAYMENT_PAID = "PAID"
PAYMENT_USED = "USED"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("uq_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Institute ID is the login identifier for every user (students, faculty and staff).
    institute_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Optional, stored lowercase. Used to email a code when the password is forgotten.
    email: Mapped[Optional[str]] = mapped_column(String(254))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    account_status: Mapped[str] = mapped_column(String(20), default=ACCOUNT_ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role: Mapped[Role] = relationship(lazy="joined")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user")
    cart: Mapped[Optional["Cart"]] = relationship(back_populates="user", uselist=False)
    orders: Mapped[List["Order"]] = relationship(back_populates="user")


class PasswordReset(Base):
    """A one-time code emailed for "Forgot password". Only its hash is stored."""

    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Set when the code is used, replaced by a newer code, or has too many wrong attempts.
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class UserSession(Base):
    """One row per login. The JWT carries the session_id (jti), so a session can be
    listed as "logged in" and ended on logout."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logged_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    device: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="sessions", lazy="joined")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    food_items: Mapped[List["FoodItem"]] = relationship(back_populates="category")


class FoodItem(Base):
    __tablename__ = "food_items"
    __table_args__ = (
        CheckConstraint("food_type IN ('VEG', 'NON_VEG')", name="ck_food_items_food_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    food_type: Mapped[str] = mapped_column(String(10), nullable=False, server_default=VEG, index=True)
    # Ingredient names only, e.g. ["Rice", "Onion"]; quantities are not tracked.
    ingredients: Mapped[Optional[List[str]]] = mapped_column(JSON)
    avg_cooking_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    # Set when the admin removes the item. It is kept (not deleted) so past orders still show it.
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    category: Mapped[Category] = relationship(back_populates="food_items", lazy="joined")
    inventory: Mapped[Optional["Inventory"]] = relationship(
        back_populates="food_item", uselist=False, lazy="joined"
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    food_item: Mapped[FoodItem] = relationship(back_populates="inventory")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.id"
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "food_item_id", name="uq_cart_food"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stock is held for this cart line until this time; other customers can't take it.
    reserved_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    cart: Mapped[Cart] = relationship(back_populates="items")
    food_item: Mapped[FoodItem] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Human-readable unique order ID shown to customers, e.g. ORD-20261010-0001
    order_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ORDER_PLACED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Based on the slowest item's average cooking time.
    estimated_ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="orders", lazy="joined")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="order", uselist=False, lazy="joined")


class Payment(Base):
    """A Razorpay payment for a cart. It must be PAID (signature verified) before
    POST /orders accepts the cart, and each payment pays for one order only."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    # In paise (Rs 160 = 16000), as Razorpay uses.
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PAYMENT_CREATED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # The canteen order this payment paid for (set when the order is placed).
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"), unique=True)

    user: Mapped[User] = relationship(lazy="joined")
    order: Mapped[Optional[Order]] = relationship(back_populates="payment")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Unit price at the time of ordering (item prices may change later).
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    food_item: Mapped[FoodItem] = relationship(lazy="joined")


class StockAlert(Base):
    """A customer asked to be notified when a sold-out / fully reserved item frees up."""

    __tablename__ = "stock_alerts"
    __table_args__ = (UniqueConstraint("user_id", "food_item_id", name="uq_stock_alert"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    food_item: Mapped[FoodItem] = relationship(lazy="joined")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
