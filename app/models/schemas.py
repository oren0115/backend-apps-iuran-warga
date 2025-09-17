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

# Payment Models
class PaymentBase(BaseModel):
    amount: int
    method: str
    bukti_transfer: Optional[str] = None

class PaymentCreate(PaymentBase):
    fee_id: str

class Payment(PaymentBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    fee_id: str
    user_id: str
    status: str = "Pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: str
    fee_id: str
    user_id: str
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

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