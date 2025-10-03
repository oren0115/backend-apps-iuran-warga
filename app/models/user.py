from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid


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
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    nama: Optional[str] = None
    alamat: Optional[str] = None
    nomor_rumah: Optional[str] = None
    nomor_hp: Optional[str] = None
    tipe_rumah: Optional[str] = None
    is_admin: Optional[bool] = None


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

