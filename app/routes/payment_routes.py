from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import List
from app.models import (
    PaymentCreate,
    PaymentResponse,
    PaymentCreateResponse,
    MidtransNotificationRequest,
)
from app.controllers.payment_controller import PaymentController
from app.security.auth import get_current_user
from app.security.webhook_security import validate_webhook_request

router = APIRouter()
payment_controller = PaymentController()


@router.post("/payments", response_model=PaymentCreateResponse)
async def create_payment(
    payment_data: PaymentCreate, current_user=Depends(get_current_user)
):
    """Create a new payment using Midtrans"""
    return await payment_controller.create_payment(
        payment_data, current_user["id"], current_user
    )


@router.get("/payments", response_model=List[PaymentResponse])
async def get_user_payments(current_user=Depends(get_current_user)):
    """Get all payments for the current user"""
    return await payment_controller.get_user_payments(current_user["id"])


@router.post("/payments/notification")
async def handle_midtrans_notification(request: Request):
    """Handle payment notification from Midtrans (webhook)"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Get signature from headers
        signature = request.headers.get("X-Midtrans-Signature") or request.headers.get("X-Signature")
        
        # Validate webhook signature
        validate_webhook_request(body_str, signature)
        
        # Parse JSON data
        notification_data = await request.json()

        # Normalisasi VA info jika dikirim dalam va_numbers
        if isinstance(notification_data, dict) and notification_data.get("va_numbers"):
            try:
                va = notification_data["va_numbers"][0]
                notification_data["bank"] = va.get("bank")
                notification_data["va_number"] = va.get("va_number")
            except Exception:
                pass

        # Validasi dengan Pydantic (supaya error handling lebih rapi)
        notification = MidtransNotificationRequest(**notification_data)

        # Teruskan ke controller sebagai model Pydantic
        return await payment_controller.handle_midtrans_notification(notification)

    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/payments/status/{transaction_id}")
async def check_payment_status(transaction_id: str, current_user=Depends(get_current_user)):
    """Check payment status from Midtrans"""
    return await payment_controller.check_payment_status(transaction_id)


@router.get("/payments/check/{payment_id}")
async def check_payment_by_id(payment_id: str, current_user=Depends(get_current_user)):
    """Check payment status by payment ID"""
    return await payment_controller.check_payment_by_id(payment_id, current_user["id"])


@router.post("/payments/force-check/{payment_id}")
async def force_check_payment_status(
    payment_id: str, current_user=Depends(get_current_user)
):
    """Force check payment status from Midtrans and update database"""
    return await payment_controller.force_check_payment_status(
        payment_id, current_user["id"]
    )
