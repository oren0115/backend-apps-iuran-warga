from fastapi import HTTPException, status
from app.models.schemas import (
    Payment, PaymentCreate, PaymentResponse, PaymentWithDetails, 
    UserResponse, FeeResponse, PaymentCreateResponse
)
from app.config.database import get_database
from app.services.midtrans_service import MidtransService
from datetime import datetime
import uuid

class PaymentController:
    def __init__(self):
        self.midtrans_service = MidtransService()
    
    async def create_payment(self, payment_data: PaymentCreate, user_id: str, user_data: dict) -> PaymentCreateResponse:
        """Create a new payment using Midtrans"""
        db = get_database()
        
        # Verify fee exists and belongs to user
        fee = await db.fees.find_one({"id": payment_data.fee_id, "user_id": user_id})
        if not fee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tagihan tidak ditemukan"
            )
        
        # Check if payment already exists for this fee
        existing_payment = await db.payments.find_one({
            "fee_id": payment_data.fee_id,
            "status": {"$in": ["Pending", "Approved"]}
        })
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pembayaran untuk tagihan ini sudah ada"
            )
        
        # Create payment using Midtrans
        from app.models.schemas import MidtransPaymentRequest
        midtrans_request = MidtransPaymentRequest(
            fee_id=payment_data.fee_id,
            payment_method=payment_data.payment_method
        )
        
        return await self.midtrans_service.create_payment(midtrans_request, user_id, user_data)

    async def get_user_payments(self, user_id: str) -> list[PaymentResponse]:
        """Get all payments for a specific user"""
        db = get_database()
        
        payments = await db.payments.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        return [PaymentResponse(**payment) for payment in payments]

    async def get_pending_payments(self) -> list[PaymentWithDetails]:
        """Get all pending payments with user and fee details (admin only)"""
        db = get_database()
        
        # Get pending payments
        payments = await db.payments.find({"status": "Pending"}, {"_id": 0}).to_list(1000)
        
        # Manually add user and fee info
        result = []
        for payment in payments:
            user = await db.users.find_one({"id": payment["user_id"]}, {"_id": 0, "password": 0})
            fee = await db.fees.find_one({"id": payment["fee_id"]}, {"_id": 0})
            
            payment_with_details = PaymentWithDetails(**payment)
            if user:
                payment_with_details.user = UserResponse(**user)
            if fee:
                payment_with_details.fee = FeeResponse(**fee)
            
            result.append(payment_with_details)
        
        return result


    async def get_all_payments(self) -> list[PaymentResponse]:
        """Get all payments (admin only)"""
        db = get_database()
        
        payments = await db.payments.find({}, {"_id": 0}).to_list(1000)
        return [PaymentResponse(**payment) for payment in payments]
    
    async def handle_midtrans_notification(self, notification_data: dict) -> dict:
        """Handle Midtrans payment notification"""
        from app.models.schemas import MidtransNotificationRequest
        notification = MidtransNotificationRequest(**notification_data)
        return await self.midtrans_service.handle_notification(notification)
    
    async def check_payment_status(self, transaction_id: str) -> dict:
        """Check payment status from Midtrans"""
        return await self.midtrans_service.check_payment_status(transaction_id)