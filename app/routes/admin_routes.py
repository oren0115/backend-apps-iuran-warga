from fastapi import APIRouter, Depends
from app.models.schemas import (
    UserResponse, FeeResponse, PaymentWithDetails, MessageResponse, 
    GenerateFeesRequest, NotificationResponse
)
from app.controllers.user_controller import UserController
from app.controllers.fee_controller import FeeController
from app.controllers.payment_controller import PaymentController
from app.controllers.notification_controller import NotificationController
from app.controllers.admin_controller import AdminController
from app.utils.auth import get_current_admin
from typing import List

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

# Fee Management
@router.post("/generate-fees", response_model=MessageResponse)
async def generate_monthly_fees(request: GenerateFeesRequest, current_user = Depends(get_current_admin)):
    """Generate monthly fees for all users (admin only)"""
    return await fee_controller.generate_monthly_fees(request.bulan)

@router.get("/fees", response_model=List[FeeResponse])
async def get_all_fees(current_user = Depends(get_current_admin)):
    """Get all fees (admin only)"""
    return await fee_controller.get_all_fees()

# Payment Management
@router.get("/payments", response_model=List[PaymentWithDetails])
async def get_pending_payments(current_user = Depends(get_current_admin)):
    """Get all pending payments with details (admin only)"""
    return await payment_controller.get_pending_payments()

@router.put("/payments/{payment_id}/approve", response_model=MessageResponse)
async def approve_payment(payment_id: str, current_user = Depends(get_current_admin)):
    """Approve a payment (admin only)"""
    return await payment_controller.approve_payment(payment_id, current_user["id"])

@router.put("/payments/{payment_id}/reject", response_model=MessageResponse)
async def reject_payment(payment_id: str, current_user = Depends(get_current_admin)):
    """Reject a payment (admin only)"""
    return await payment_controller.reject_payment(payment_id)

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