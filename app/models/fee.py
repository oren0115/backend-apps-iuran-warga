from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid


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

