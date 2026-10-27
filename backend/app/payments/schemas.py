from pydantic import BaseModel


class PaymentOrderOut(BaseModel):
    key_id: str
    order_id: str
    amount: int
    currency: str

