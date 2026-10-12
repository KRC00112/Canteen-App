from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.security import get_customer
from app.database.database import get_db
from app.database.models import User
from app.notifications import service
from app.notifications.service import NotificationOut, NotificationsOut, StockAlertIn, StockAlertOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsOut)
def my_notifications(
    unread_only: bool = Query(False),
    user: User = Depends(get_customer),
    db: Session = Depends(get_db),
):
    """Newest first (max 50). Poll this, e.g. every 30 s and when the app comes to the foreground."""
    return service.list_notifications(db, user, unread_only)


@router.post("/read-all", response_model=NotificationsOut)
def read_all(user: User = Depends(get_customer), db: Session = Depends(get_db)):
    return service.mark_all_read(db, user)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_one(notification_id: int, user: User = Depends(get_customer), db: Session = Depends(get_db)):
    return service.mark_read(db, user, notification_id)


@router.get("/stock-alerts", response_model=List[StockAlertOut])
def my_stock_alerts(user: User = Depends(get_customer), db: Session = Depends(get_db)):
    """Items you asked to be notified about."""
    return service.list_alerts(db, user)


@router.post("/stock-alerts", response_model=StockAlertOut, status_code=status.HTTP_201_CREATED)
def notify_me(data: StockAlertIn, user: User = Depends(get_customer), db: Session = Depends(get_db)):
    """'Notify me' for a sold-out or fully reserved item. You get a BACK_IN_STOCK notification."""
    return service.add_alert(db, user, data.food_id)


@router.delete("/stock-alerts/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_notify_me(food_id: int, user: User = Depends(get_customer), db: Session = Depends(get_db)):
    service.remove_alert(db, user, food_id)
