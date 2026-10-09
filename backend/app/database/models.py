from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
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

# Order status (only PLACED is used for Demo 1)
ORDER_PLACED = "PLACED"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Institute ID is the login identifier for every user (students, faculty and staff).
    institute_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    account_status: Mapped[str] = mapped_column(String(20), default=ACCOUNT_ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role: Mapped[Role] = relationship(lazy="joined")
    cart: Mapped[Optional["Cart"]] = relationship(back_populates="user", uselist=False)
    orders: Mapped[List["Order"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    food_items: Mapped[List["FoodItem"]] = relationship(back_populates="category")


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

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

    user: Mapped[User] = relationship(back_populates="orders", lazy="joined")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Unit price at the time of ordering (menu prices may change later).
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    food_item: Mapped[FoodItem] = relationship(lazy="joined")
