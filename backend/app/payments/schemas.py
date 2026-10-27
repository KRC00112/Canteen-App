from pydantic import BaseModel


class PaymentOrderOut(BaseModel):
    key_id: str
    order_id: str
    amount: int
    currency: str


class PaymentVerifyIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyOut(BaseModel):
    verified: bool
    order_id: str
    payment_id: str
    message: str

