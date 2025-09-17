from fastapi import APIRouter, Depends, Request
from app.models.schemas import (
    PaymentCreate, PaymentResponse, PaymentCreateResponse, 
    MidtransNotificationRequest
)
from app.controllers.payment_controller import PaymentController
from app.utils.auth import get_current_user
from typing import List

router = APIRouter()
payment_controller = PaymentController()

@router.post("/payments", response_model=PaymentCreateResponse)
async def create_payment(payment_data: PaymentCreate, current_user = Depends(get_current_user)):
    """Create a new payment using Midtrans"""
    return await payment_controller.create_payment(payment_data, current_user["id"], current_user)

@router.get("/payments", response_model=List[PaymentResponse])
async def get_user_payments(current_user = Depends(get_current_user)):
    """Get all payments for the current user"""
    return await payment_controller.get_user_payments(current_user["id"])

@router.post("/payments/notification")
async def handle_midtrans_notification(request: Request):
    """Handle payment notification from Midtrans (webhook)"""
    # Get form data from request
    form_data = await request.form()
    notification_data = dict(form_data)
    
    return await payment_controller.handle_midtrans_notification(notification_data)

@router.get("/payments/status/{transaction_id}")
async def check_payment_status(transaction_id: str):
    """Check payment status from Midtrans"""
    return await payment_controller.check_payment_status(transaction_id)