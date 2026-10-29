from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.service import (
    AdminNotificationOut,
    AdminPaymentOut,
    AdminSessionOut,
    AdminStockAlertOut,
    AdminUserDetail,
    FoodItemCreate,
    FoodItemUpdate,
)
from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, User
from app.items.schemas import FoodItemOut
from app.staff.service import StaffOrderOut
from app.users import service as users_service
from app.users.schemas import UserWithLoginStatus

# Main canteen admin only. Staff, students and faculty get 403.
# Stock (PUT /staff/inventory) and customer carts (GET /staff/carts) are staff only.
router = APIRouter(prefix="/admin", tags=["Admin"])
admin_only = require_role(ADMIN)


@router.get("/users", response_model=List[UserWithLoginStatus])
def all_users(
    role: Optional[Literal["STUDENT", "FACULTY", "CANTEEN_STAFF", "ADMIN"]] = Query(
        None, description="Only users with this role"
    ),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Every account (customers and staff) with login status. No password hashes."""
    return users_service.list_users(db, role)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def user_detail(user_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Full customer details: profile, login history, cart, orders, notifications, stock alerts."""
    return service.get_user_detail(db, user_id)


@router.get("/orders", response_model=List[StaffOrderOut])
def all_orders(
    order_status: Optional[str] = Query(None, alias="status", description="Filter by status, e.g. PLACED"),
    user_id: Optional[int] = Query(None, description="Only this customer's orders"),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Every order from every customer, newest first."""
    return service.list_all_orders(db, order_status, user_id)


@router.get("/orders/{order_id}", response_model=StaffOrderOut)
def order_detail(order_id: str, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Any order by its order ID (e.g. ORD-20261010-0001), with the customer who placed it."""
    return service.get_order(db, order_id)


@router.get("/payments", response_model=List[AdminPaymentOut])
def all_payments(
    payment_status: Optional[Literal["CREATED", "PAID", "USED", "REFUND_PENDING", "REFUNDED"]] = Query(
        None,
        alias="status",
        description="CREATED = checkout started, PAID = verified, USED = order placed, "
        "REFUND_PENDING / REFUNDED = that order was cancelled",
    ),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Every Razorpay payment, newest first, with the customer and the order it paid for."""
    return service.list_payments(db, payment_status)


@router.get("/sessions", response_model=List[AdminSessionOut])
def all_sessions(
    active_only: bool = Query(False, description="Only sessions that are logged in right now"),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Login history of every account: device, IP, login/logout times."""
    return service.list_sessions(db, active_only)


@router.get("/notifications", response_model=List[AdminNotificationOut])
def all_notifications(
    user_id: Optional[int] = Query(None, description="Only this user's notifications"),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Notifications sent to every user."""
    return service.list_notifications(db, user_id)


@router.get("/stock-alerts", response_model=List[AdminStockAlertOut])
def all_stock_alerts(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Every customer's "Notify me" request."""
    return service.list_stock_alerts(db)


@router.get("/staff", response_model=List[UserWithLoginStatus])
def all_staff(
    account_status: Optional[Literal["PENDING", "ACTIVE", "INACTIVE"]] = Query(
        None, alias="status", description="PENDING = waiting for your approval"
    ),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Canteen staff accounts. Self-registered staff are PENDING until you approve them."""
    return service.list_staff(db, account_status)


@router.post("/staff/{user_id}/approve", response_model=UserWithLoginStatus)
def approve_staff(user_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Approve a pending staff account (or re-activate a deactivated one) so it can log in."""
    return service.approve_staff(db, user_id)


@router.post("/staff/{user_id}/deactivate", response_model=UserWithLoginStatus)
def deactivate_staff(user_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Reject a pending staff account or block an active one. Their logins end immediately."""
    return service.deactivate_staff(db, user_id)


@router.post("/items", response_model=FoodItemOut, status_code=status.HTTP_201_CREATED)
def create_food_item(data: FoodItemCreate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Add a food item: name, price, category, optional description, Veg/Non-Veg, ingredients and
    average cooking time. It starts with 0 stock (not available) until staff restock it."""
    return service.create_food_item(db, data)


@router.patch("/items/{food_id}", response_model=FoodItemOut)
def update_food_item(
    food_id: int, data: FoodItemUpdate, admin: User = Depends(admin_only), db: Session = Depends(get_db)
):
    """Edit an item: name, price, description, category, Veg/Non-Veg, ingredients, cooking time.
    Only the fields sent are changed. Past orders keep the price they were placed at."""
    return service.update_food_item(db, food_id, data)


@router.delete("/items/{food_id}")
def remove_food_item(food_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Remove an item. Past orders still show it; it is taken out of carts."""
    service.remove_food_item(db, food_id)
    return {"message": "Food item removed"}
