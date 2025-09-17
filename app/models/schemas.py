from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# User Models
class UserBase(BaseModel):
    username: str
    nama: str
    alamat: str
    nomor_rumah: str
    nomor_hp: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    password: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(UserBase):
    id: str
    is_admin: bool
    created_at: datetime

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Fee Models
class FeeBase(BaseModel):
    kategori: str
    nominal: int
    bulan: str

class Fee(FeeBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: str = "Belum Bayar"
    due_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeeResponse(FeeBase):
    id: str
    user_id: str
    status: str
    due_date: datetime
    created_at: datetime

# Payment Models (Midtrans Only)
class PaymentBase(BaseModel):
    amount: int
    payment_method: str  # credit_card, bank_transfer, gopay, etc.

class PaymentCreate(PaymentBase):
    fee_id: str

class Payment(PaymentBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    fee_id: str
    user_id: str
    status: str = "Pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
    status: str
    created_at: datetime
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

class PaymentWithDetails(PaymentResponse):
    user: Optional[UserResponse] = None
    fee: Optional[FeeResponse] = None

# Notification Models
class NotificationBase(BaseModel):
    title: str
    message: str
    type: str

class Notification(NotificationBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime

# Response Models
class MessageResponse(BaseModel):
    message: str

class GenerateFeesRequest(BaseModel):
    bulan: str

# Midtrans specific models
class MidtransPaymentRequest(BaseModel):
    fee_id: str
    payment_method: str  # credit_card, bank_transfer, gopay, etc.

# Payment creation response
class PaymentCreateResponse(BaseModel):
    payment_id: str
    transaction_id: str
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
    gross_amount: str
    fraud_status: Optional[str] = None
    bank: Optional[str] = None
    va_number: Optional[str] = None
    signature_key: str