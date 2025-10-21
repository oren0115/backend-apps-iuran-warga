from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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
    # Versioning and regeneration tracking
    version: int = 1
    regenerated_at: Optional[datetime] = None
    regenerated_reason: Optional[str] = None
    parent_fee_id: Optional[str] = None  # Link to original fee if regenerated
    is_regenerated: bool = False


class FeeResponse(FeeBase):
    id: str
    user_id: str
    status: str
    due_date: datetime
    created_at: datetime
    # Include versioning info in response (optional for backward compatibility)
    version: Optional[int] = 1
    regenerated_at: Optional[datetime] = None
    regenerated_reason: Optional[str] = None
    parent_fee_id: Optional[str] = None
    is_regenerated: Optional[bool] = False


class FeeRegenerationAudit(BaseModel):
    """Audit log for fee regenerations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str  # "regenerate_fees", "rollback", "smart_regenerate"
    month: str
    admin_user: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=7))))
    details: Dict[str, Any]
    affected_fees_count: int
    paid_fees_preserved: int = 0
    unpaid_fees_regenerated: int = 0
    reason: Optional[str] = None

