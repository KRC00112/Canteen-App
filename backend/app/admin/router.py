from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.service import (
    AdminCartOut,
    AdminNotificationOut,
    AdminSessionOut,
    AdminStockAlertOut,
    AdminUserDetail,
)
from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, User
from app.staff.service import StaffOrderOut
from app.users import service as users_service
from app.users.schemas import UserWithLoginStatus

# Main canteen admin only. Staff, students and faculty get 403.
# The admin can also use every /staff and /users endpoint.
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
    status: Optional[str] = Query(None, description="Filter by status, e.g. PLACED"),
    user_id: Optional[int] = Query(None, description="Only this customer's orders"),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Every order from every customer, newest first."""
    return service.list_all_orders(db, status, user_id)


@router.get("/orders/{order_id}", response_model=StaffOrderOut)
def order_detail(order_id: str, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Any order by its order ID (e.g. ORD-20261010-0001), with the customer who placed it."""
    return service.get_order(db, order_id)


@router.get("/sessions", response_model=List[AdminSessionOut])
def all_sessions(
    active_only: bool = Query(False, description="Only sessions that are logged in right now"),
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Login history of every account: device, IP, login/logout times."""
    return service.list_sessions(db, active_only)


@router.get("/carts", response_model=List[AdminCartOut])
def all_carts(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Every customer's current (non-empty) cart, with stock holds."""
    return service.list_carts(db)


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
