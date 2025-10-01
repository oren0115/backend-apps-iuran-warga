from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import datetime, timezone, timedelta
import uuid

# -------------------------
# User Models
# -------------------------
class UserBase(BaseModel):
    username: str
    nama: str
    alamat: str
    nomor_rumah: str
    nomor_hp: str
    # Optional: tipe rumah pengguna, contoh: "60M2", "72M2", "HOOK"
    tipe_rumah: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nama: Optional[str] = None
    alamat: Optional[str] = None
    nomor_rumah: Optional[str] = None
    nomor_hp: Optional[str] = None
    tipe_rumah: Optional[str] = None

class PasswordUpdate(BaseModel):
    new_password: str

class ResetPasswordRequest(BaseModel):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    password: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=7))))

class UserResponse(UserBase):
    id: str
    is_admin: bool
    created_at: datetime

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# -------------------------
# Fee Models
# -------------------------
class FeeBase(BaseModel):
    kategori: str
    nominal: int
    bulan: str

class Fee(FeeBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: str = "Belum Bayar"
    due_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=7))))

class FeeResponse(FeeBase):
    id: str
    user_id: str
    status: str
    due_date: datetime
    created_at: datetime

# -------------------------
# Payment Models
# -------------------------
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
    created_at: Union[datetime, str]
    transaction_id: Optional[str] = None
    payment_token: Optional[str] = None
    payment_url: Optional[str] = None
    midtrans_status: Optional[str] = None
    payment_type: Optional[str] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    expiry_time: Optional[Union[datetime, str]] = None
    settled_at: Optional[Union[datetime, str]] = None

    # validator: convert str -> datetime
    @validator("created_at", "expiry_time", "settled_at", pre=True, always=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                try:
                    dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                    return dt.replace(tzinfo=timezone.utc)
                except Exception:
                    return None
        return v

class PaymentWithDetails(PaymentResponse):
    user: Optional['UserResponse'] = None
    fee: Optional['FeeResponse'] = None

# -------------------------
# Notification Models
# -------------------------
class NotificationBase(BaseModel):
    title: str
    message: str
    type: str

class Notification(NotificationBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=7))))

class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime

# -------------------------
# Response Models
# -------------------------
class MessageResponse(BaseModel):
    message: str

class GenerateFeesRequest(BaseModel):
    bulan: str
    # Tarif IPL per tipe rumah; dikirim dari frontend
    tarif_60m2: int
    tarif_72m2: int
    tarif_hook: int

# -------------------------
# Midtrans Models
# -------------------------
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
