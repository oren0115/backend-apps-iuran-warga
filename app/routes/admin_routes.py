from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    UserResponse, FeeResponse, PaymentResponse, MessageResponse, 
    GenerateFeesRequest, NotificationResponse, UserUpdate, PasswordUpdate, UserCreate, ResetPasswordRequest
)
from app.controllers.user_controller import UserController
from app.controllers.fee_controller import FeeController
from app.controllers.payment_controller import PaymentController
from app.controllers.notification_controller import NotificationController
from app.controllers.admin_controller import AdminController
from app.utils.auth import get_current_admin
from fastapi import Path
from typing import List
from datetime import datetime, date
import io
import pandas as pd

router = APIRouter()
user_controller = UserController()
fee_controller = FeeController()
payment_controller = PaymentController()
notification_controller = NotificationController()
admin_controller = AdminController()

# User Management
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user = Depends(get_current_admin)):
    """Create a new user (admin only)"""
    return await user_controller.register_user(user_data)

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user = Depends(get_current_admin)):
    """Get all users (admin only)"""
    return await user_controller.get_all_users()

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_profile_admin(
    user_id: str = Path(..., description="ID pengguna"),
    updates: UserUpdate = None,
    current_user = Depends(get_current_admin)
):
    """Update user profile by id (admin only)"""
    return await user_controller.update_user_by_id(user_id, updates)

@router.put("/users/{user_id}/password", response_model=MessageResponse)
async def update_user_password_admin(
    user_id: str = Path(..., description="ID pengguna"),
    payload: PasswordUpdate = None,
    current_user = Depends(get_current_admin)
):
    """Update user password by id (admin only)"""
    return await user_controller.update_user_password_by_id(user_id, payload)

@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Delete user by id (admin only)"""
    return await user_controller.delete_user_by_id(user_id)

@router.patch("/users/{user_id}/promote", response_model=UserResponse)
async def promote_user_to_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Promote user to admin (admin only)"""
    return await user_controller.promote_user_to_admin(user_id)

@router.patch("/users/{user_id}/demote", response_model=UserResponse)
async def demote_user_from_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Demote user from admin (admin only)"""
    return await user_controller.demote_user_from_admin(user_id)

@router.patch("/users/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password_admin(
    user_id: str = Path(..., description="ID pengguna"),
    request: ResetPasswordRequest = None,
    current_user = Depends(get_current_admin)
):
    """Reset user password by id (admin only)"""
    return await user_controller.reset_user_password_by_id(user_id, request.password)

# Fee Management
@router.post("/generate-fees", response_model=MessageResponse)
async def generate_monthly_fees(request: GenerateFeesRequest, current_user = Depends(get_current_admin)):
    """Generate monthly fees for all users (admin only)
    Tarif IPL dikirim dari frontend berdasarkan tipe rumah.
    """
    tarif_config = {
        "60M2": request.tarif_60m2,
        "72M2": request.tarif_72m2,
        "HOOK": request.tarif_hook,
    }
    return await fee_controller.generate_monthly_fees(request.bulan, tarif_config)

@router.get("/fees", response_model=List[FeeResponse])
async def get_all_fees(current_user = Depends(get_current_admin)):
    """Get all fees (admin only)"""
    return await fee_controller.get_all_fees()

@router.post("/regenerate-fees", response_model=MessageResponse)
async def regenerate_fees_for_month(request: GenerateFeesRequest, current_user = Depends(get_current_admin)):
    """Regenerate fees for a specific month based on current user house types (admin only)"""
    tarif_config = {
        "60M2": request.tarif_60m2,
        "72M2": request.tarif_72m2,
        "HOOK": request.tarif_hook,
    }
    return await fee_controller.regenerate_fees_for_month(request.bulan, tarif_config)

# Payment Management
@router.get("/payments", response_model=List[PaymentResponse])
async def get_all_payments(current_user = Depends(get_current_admin)):
    """Get all payments (admin only)"""
    return await payment_controller.get_all_payments()

# Notification Management
@router.post("/notifications/broadcast", response_model=MessageResponse)
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "pengumuman",
    current_user = Depends(get_current_admin)
):
    """Send notification to all users (admin only)"""
    return await notification_controller.create_bulk_notifications(title, message, notification_type)

# Dashboard
@router.get("/dashboard")
async def get_dashboard_stats(current_user = Depends(get_current_admin)):
    """Get dashboard statistics (admin only)"""
    return await admin_controller.get_dashboard_stats()

# Endpoint init-sample-data telah dihapus karena tidak lagi menggunakan data dummy

# Reports Export
@router.get("/reports/fees/export")
async def export_fees(
    bulan: str = Query(..., description="Format YYYY-MM"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    current_user = Depends(get_current_admin),
):
    data = await fee_controller.get_fees_by_month(bulan)
    # Convert Pydantic models to dicts
    records = [d.model_dump() if hasattr(d, "model_dump") else dict(d) for d in data]
    df = pd.DataFrame(records)
    if format == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Fees")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="fees_{bulan}.xlsx"'},
        )
    else:
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it.")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        textobject = c.beginText(40, 800)
        textobject.textLine(f"Laporan Iuran {bulan}")
        for row in df.to_dict(orient="records"):
            textobject.textLine(str(row))
        c.drawText(textobject)
        c.showPage()
        c.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="fees_{bulan}.pdf"'},
        )

@router.get("/reports/payments/export")
async def export_payments(
    start: date = Query(..., description="Start date YYYY-MM-DD"),
    end: date = Query(..., description="End date YYYY-MM-DD"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    current_user = Depends(get_current_admin),
):
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    data = await payment_controller.get_payments_by_date_range(start_dt, end_dt)
    records = [d.model_dump() if hasattr(d, "model_dump") else dict(d) for d in data]
    df = pd.DataFrame(records)
    if format == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Payments")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="payments_{start}_{end}.xlsx"'},
        )
    else:
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it.")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        textobject = c.beginText(40, 800)
        textobject.textLine(f"Laporan Pembayaran {start} s.d {end}")
        for row in df.to_dict(orient="records"):
            textobject.textLine(str(row))
        c.drawText(textobject)
        c.showPage()
        c.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="payments_{start}_{end}.pdf"'},
        )