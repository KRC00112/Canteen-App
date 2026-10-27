from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.payments import service
from app.payments.schemas import PaymentOrderOut, PaymentVerifyIn, PaymentVerifyOut

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/orders", response_model=PaymentOrderOut, status_code=status.HTTP_201_CREATED)
def create_payment_order(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create a Razorpay payment order for the authenticated user's current cart."""
    return service.create_payment_order(db, user)


@router.post("/verify", response_model=PaymentVerifyOut)
def verify_payment(
    payment: PaymentVerifyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Verify the Razorpay signature before the app creates a canteen order. Body: the
    razorpay_order_id, razorpay_payment_id and razorpay_signature that checkout returns.
    After this, POST /orders places the order (once per payment)."""
    return service.verify_payment(db, user, payment)
