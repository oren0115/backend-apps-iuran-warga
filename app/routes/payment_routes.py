from fastapi import APIRouter, Depends
from app.models.schemas import PaymentCreate, PaymentResponse
from app.controllers.payment_controller import PaymentController
from app.utils.auth import get_current_user
from typing import List

router = APIRouter()
payment_controller = PaymentController()

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment_data: PaymentCreate, current_user = Depends(get_current_user)):
    """Create a new payment"""
    return await payment_controller.create_payment(payment_data, current_user["id"])

@router.get("/payments", response_model=List[PaymentResponse])
async def get_user_payments(current_user = Depends(get_current_user)):
    """Get all payments for the current user"""
    return await payment_controller.get_user_payments(current_user["id"])