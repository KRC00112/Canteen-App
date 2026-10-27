import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from app.database.models import Cart, User
from app.payments.schemas import PaymentOrderOut, PaymentVerifyIn, PaymentVerifyOut


def create_payment_order(db: Session, user: User) -> PaymentOrderOut:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured",
        )

    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty")

    total = sum(
        (Decimal(str(item.food_item.price)) * item.quantity for item in cart.items),
        Decimal("0"),
    )
    amount = int((total * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart total must be greater than zero",
        )

    payload = json.dumps(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": f"cart-{user.id}-{uuid.uuid4().hex[:16]}",
            "notes": {"user_id": str(user.id)},
        }
    ).encode("utf-8")
    credentials = base64.b64encode(
        f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode("utf-8")
    ).decode("ascii")
    request = Request(
        "https://api.razorpay.com/v1/orders",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            razorpay_order = json.load(response)
    except HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider rejected the order request",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider is unavailable",
        ) from exc

    order_id = razorpay_order.get("id")
    if not isinstance(order_id, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider returned an invalid order",
        )

    return PaymentOrderOut(
        key_id=RAZORPAY_KEY_ID,
        order_id=order_id,
        amount=amount,
        currency="INR",
    )


def verify_payment(payment: PaymentVerifyIn) -> PaymentVerifyOut:
    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured",
        )

    message = f"{payment.razorpay_order_id}|{payment.razorpay_payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, payment.razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed",
        )

    return PaymentVerifyOut(
        verified=True,
        order_id=payment.razorpay_order_id,
        payment_id=payment.razorpay_payment_id,
        message="Payment verified successfully",
    )
