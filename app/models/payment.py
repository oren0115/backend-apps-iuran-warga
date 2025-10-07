from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid


class PaymentBase(BaseModel):
    amount: int
    payment_method: str  # credit_card, bank_transfer, gopay, etc.


class PaymentCreate(PaymentBase):
    fee_id: str


class Payment(PaymentBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    fee_id: str
    user_id: str
    order_id: Optional[str] = None
    status: str = "Pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=7))))

    # Midtrans fields
    transaction_id: Optional[str] = None
    payment_token: Optional[str] = None
    payment_url: Optional[str] = None
    midtrans_status: Optional[str] = None
    payment_type: Optional[str] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    expiry_time: Optional[datetime] = None
    settled_at: Optional[datetime] = None


class PaymentResponse(PaymentBase):
    id: str
    fee_id: str
    user_id: str
    order_id: Optional[str] = None
    status: str
    created_at: datetime
    transaction_id: Optional[str] = None
    payment_token: Optional[str] = None
    payment_url: Optional[str] = None
    midtrans_status: Optional[str] = None
    payment_type: Optional[str] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    expiry_time: Optional[datetime] = None
    settled_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    # validator: convert str -> datetime and ensure UTC
    @validator("created_at", "expiry_time", "settled_at", pre=True, always=True)
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v)
                if dt.tzinfo is None:
                    # If no timezone, assume it's UTC
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                try:
                    dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                    return dt.replace(tzinfo=timezone.utc)
                except Exception:
                    return None
        if isinstance(v, datetime):
            # Ensure datetime has timezone info (UTC)
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        return v


class PaymentWithDetails(PaymentResponse):
    user: Optional[dict] = None
    fee: Optional[dict] = None

