"""Razorpay payments: create an order for the cart, verify the payment signature, and let
POST /orders use each verified payment once."""
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

from app import activity
from app.auth.security import utcnow
from app.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from app.database.models import PAYMENT_CREATED, PAYMENT_PAID, Cart, Payment, User
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

    amount = to_paise(cart_total(cart))
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

    db.add(Payment(
        user_id=user.id,
        razorpay_order_id=order_id,
        amount=amount,
        currency="INR",
        status=PAYMENT_CREATED,
        created_at=utcnow(),
    ))
    db.commit()
    activity.event(f"Payment started: Razorpay order {order_id} for Rs {amount / 100:g}")

    return PaymentOrderOut(
        key_id=RAZORPAY_KEY_ID,
        order_id=order_id,
        amount=amount,
        currency="INR",
    )


def verify_payment(db: Session, user: User, payment: PaymentVerifyIn) -> PaymentVerifyOut:
    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured",
        )

    # Only Razorpay orders this user created through POST /payments/orders can be verified.
    record = db.scalar(
        select(Payment).where(Payment.razorpay_order_id == payment.razorpay_order_id).with_for_update(of=Payment)
    )
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
    if record.status != PAYMENT_CREATED:
        if record.razorpay_payment_id == payment.razorpay_payment_id:
            # Already verified (e.g. the app retried): same answer again.
            return _verified_out(record)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This payment order was already paid")

    message = f"{payment.razorpay_order_id}|{payment.razorpay_payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, payment.razorpay_signature):
        activity.event(f"Payment verification FAILED for {payment.razorpay_order_id} (bad signature)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed",
        )

    record.razorpay_payment_id = payment.razorpay_payment_id
    record.status = PAYMENT_PAID
    record.verified_at = utcnow()
    db.commit()
    activity.event(f"Payment verified: {record.razorpay_payment_id}, Rs {record.amount / 100:g}")
    return _verified_out(record)


def _verified_out(record: Payment) -> PaymentVerifyOut:
    return PaymentVerifyOut(
        verified=True,
        order_id=record.razorpay_order_id,
        payment_id=record.razorpay_payment_id,
        message="Payment verified successfully",
    )


def cart_total(cart: Cart) -> Decimal:
    return sum(
        (Decimal(str(item.food_item.price)) * item.quantity for item in cart.items),
        Decimal("0"),
    )


def to_paise(rupees: Decimal) -> int:
    return int((rupees * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def take_verified_payment(db: Session, user: User, total: Decimal) -> Payment:
    """For POST /orders: the user's newest verified, unused payment for exactly this total."""
    record = db.scalar(
        select(Payment)
        .where(Payment.user_id == user.id, Payment.status == PAYMENT_PAID, Payment.order_id.is_(None))
        .order_by(Payment.verified_at.desc(), Payment.id.desc())
        .with_for_update(of=Payment)
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Please complete the payment before placing the order",
        )
    if record.amount != to_paise(total):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Your cart changed after payment: paid Rs {record.amount / 100:g}, cart is "
            f"Rs {to_paise(total) / 100:g}. Change the cart back to what you paid for",
        )
    return record
