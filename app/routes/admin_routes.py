from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    UserResponse, FeeResponse, PaymentResponse, MessageResponse, 
    GenerateFeesRequest, NotificationResponse, UserUpdate, PasswordUpdate
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

# Sample Data
@router.post("/init-sample-data", response_model=MessageResponse)
async def init_sample_data():
    """Initialize sample data for testing"""
    return await admin_controller.init_sample_data()

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