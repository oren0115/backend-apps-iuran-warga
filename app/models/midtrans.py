from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MidtransPaymentRequest(BaseModel):
    fee_id: str
    payment_method: str  # credit_card, bank_transfer, gopay, etc.


class PaymentCreateResponse(BaseModel):
    payment_id: str
    order_id: str
    transaction_id: Optional[str] = None
    payment_token: str
    payment_url: str
    expiry_time: datetime
    payment_type: str
    bank: Optional[str] = None
    va_number: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MidtransNotificationRequest(BaseModel):
    transaction_id: str
    transaction_status: str
    payment_type: str
    order_id: str
    status_code: str
    gross_amount: str
    fraud_status: Optional[str] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    signature_key: str

