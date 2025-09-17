from fastapi import HTTPException, status
from app.models.schemas import Payment, PaymentCreate, PaymentResponse, PaymentWithDetails, UserResponse, FeeResponse
from app.config.database import get_database
from datetime import datetime
import uuid

class PaymentController:
    async def create_payment(self, payment_data: PaymentCreate, user_id: str) -> PaymentResponse:
        """Create a new payment"""
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
        
        # Create payment
        payment_dict = payment_data.dict()
        payment_dict["id"] = str(uuid.uuid4())
        payment_dict["user_id"] = user_id
        payment_dict["status"] = "Pending"
        payment_dict["created_at"] = datetime.utcnow()
        
        await db.payments.insert_one(payment_dict)
        
        # Update fee status
        await db.fees.update_one(
            {"id": payment_data.fee_id},
            {"$set": {"status": "Pending"}}
        )
        
        return PaymentResponse(**payment_dict)

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

    async def approve_payment(self, payment_id: str, admin_id: str) -> dict:
        """Approve a payment (admin only)"""
        db = get_database()
        
        payment = await db.payments.find_one({"id": payment_id})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pembayaran tidak ditemukan"
            )
        
        if payment["status"] != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pembayaran sudah diproses sebelumnya"
            )
        
        # Update payment
        await db.payments.update_one(
            {"id": payment_id},
            {"$set": {
                "status": "Approved",
                "approved_at": datetime.utcnow(),
                "approved_by": admin_id
            }}
        )
        
        # Update fee
        await db.fees.update_one(
            {"id": payment["fee_id"]},
            {"$set": {"status": "Lunas"}}
        )
        
        return {"message": "Pembayaran berhasil disetujui"}

    async def reject_payment(self, payment_id: str) -> dict:
        """Reject a payment (admin only)"""
        db = get_database()
        
        payment = await db.payments.find_one({"id": payment_id})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pembayaran tidak ditemukan"
            )
        
        if payment["status"] != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pembayaran sudah diproses sebelumnya"
            )
        
        # Update payment
        await db.payments.update_one(
            {"id": payment_id},
            {"$set": {"status": "Rejected"}}
        )
        
        # Update fee back to unpaid
        await db.fees.update_one(
            {"id": payment["fee_id"]},
            {"$set": {"status": "Belum Bayar"}}
        )
        
        return {"message": "Pembayaran ditolak"}

    async def get_all_payments(self) -> list[PaymentResponse]:
        """Get all payments (admin only)"""
        db = get_database()
        
        payments = await db.payments.find({}, {"_id": 0}).to_list(1000)
        return [PaymentResponse(**payment) for payment in payments]