from fastapi import HTTPException, status
from app.models.schemas import (
    Payment, PaymentCreate, PaymentResponse, PaymentWithDetails,
    UserResponse, FeeResponse, PaymentCreateResponse, MidtransPaymentRequest
)
from app.config.database import get_database
from app.services.midtrans_service import MidtransService
from datetime import datetime
import uuid


class PaymentController:
    def __init__(self):
        self.midtrans_service = MidtransService()

    def generate_order_id(self, user_id: str, fee_id: str) -> str:
        """
        Generate a unique Midtrans order_id <= 50 characters
        Format: USERID-FEEID-UUID
        """
        short_user_id = str(user_id)[:10]
        short_fee_id = str(fee_id)[:10]
        unique_part = str(uuid.uuid4())[:8]
        order_id = f"{short_user_id}-{short_fee_id}-{unique_part}"

        return order_id[:50]

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

        # Generate unique order_id
        order_id = self.generate_order_id(user_id, payment_data.fee_id)

        # Create Midtrans request
        midtrans_request = MidtransPaymentRequest(
            fee_id=payment_data.fee_id,
            payment_method=payment_data.payment_method
        )

        # Call Midtrans service
        return await self.midtrans_service.create_payment(midtrans_request, user_id, user_data)

    async def get_user_payments(self, user_id: str) -> list[PaymentResponse]:
        """Get all payments for a specific user"""
        db = get_database()
        payments = await db.payments.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        # Handle backward compatibility for old 'method' field
        processed_payments = []
        for payment in payments:
            # If payment has old 'method' field, rename it to 'payment_method'
            if 'method' in payment and 'payment_method' not in payment:
                payment['payment_method'] = payment.pop('method')
            processed_payments.append(PaymentResponse(**payment))
        
        return processed_payments

    async def get_pending_payments(self) -> list[PaymentWithDetails]:
        """Get all pending payments with user and fee details (admin only)"""
        db = get_database()
        payments = await db.payments.find({"status": "Pending"}, {"_id": 0}).to_list(1000)

        result = []
        for payment in payments:
            # Handle backward compatibility for old 'method' field
            if 'method' in payment and 'payment_method' not in payment:
                payment['payment_method'] = payment.pop('method')
            
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
        
        # Handle backward compatibility for old 'method' field
        processed_payments = []
        for payment in payments:
            # If payment has old 'method' field, rename it to 'payment_method'
            if 'method' in payment and 'payment_method' not in payment:
                payment['payment_method'] = payment.pop('method')
            processed_payments.append(PaymentResponse(**payment))
        
        return processed_payments

    async def get_payments_by_date_range(self, start: datetime, end: datetime) -> list[PaymentResponse]:
        """Get payments filtered by created_at date range for export"""
        db = get_database()
        payments = await db.payments.find({
            "created_at": {"$gte": start, "$lte": end}
        }, {"_id": 0}).to_list(5000)
        
        # Handle backward compatibility for old 'method' field
        processed_payments = []
        for payment in payments:
            # If payment has old 'method' field, rename it to 'payment_method'
            if 'method' in payment and 'payment_method' not in payment:
                payment['payment_method'] = payment.pop('method')
            processed_payments.append(PaymentResponse(**payment))
        
        return processed_payments

    async def handle_midtrans_notification(self, notification_data: dict) -> dict:
        """Handle Midtrans payment notification"""
        from app.models.schemas import MidtransNotificationRequest
        notification = MidtransNotificationRequest(**notification_data)
        return await self.midtrans_service.handle_notification(notification)

    async def check_payment_status(self, transaction_id: str) -> dict:
        """Check payment status from Midtrans"""
        return await self.midtrans_service.check_payment_status(transaction_id)
    
    async def check_payment_by_id(self, payment_id: str, user_id: str) -> dict:
        """Check payment status by payment ID and update if needed"""
        db = get_database()
        
        # Get payment from database
        payment = await db.payments.find_one({"id": payment_id, "user_id": user_id})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # If payment is still pending, check with Midtrans
        if payment["status"] == "Pending" and payment.get("transaction_id"):
            try:
                midtrans_status = await self.midtrans_service.check_payment_status(payment["transaction_id"])
                new_status = self.midtrans_service._map_midtrans_status(midtrans_status.get("status", "pending"))
                
                # Update payment status if changed
                if new_status != payment["status"]:
                    update_data = {
                        "status": new_status,
                        "midtrans_status": midtrans_status.get("status", "pending")
                    }
                    
                    if new_status == "Success":
                        update_data["settled_at"] = datetime.utcnow()
                        # Update fee status
                        await db.fees.update_one(
                            {"id": payment["fee_id"]},
                            {"$set": {"status": "Lunas"}}
                        )
                    elif new_status == "Failed":
                        # Update fee status back to unpaid
                        await db.fees.update_one(
                            {"id": payment["fee_id"]},
                            {"$set": {"status": "Belum Bayar"}}
                        )
                    
                    await db.payments.update_one(
                        {"id": payment_id},
                        {"$set": update_data}
                    )
                    
                    # Update local payment data
                    payment.update(update_data)
                    
            except Exception as e:
                # If Midtrans check fails, return current status
                pass
        
        return {
            "payment_id": payment["id"],
            "status": payment["status"],
            "midtrans_status": payment.get("midtrans_status", "pending"),
            "settled_at": payment.get("settled_at")
        }
    
    async def force_check_payment_status(self, payment_id: str, user_id: str) -> dict:
        """Force check payment status from Midtrans and update database"""
        db = get_database()
        
        # Get payment from database
        payment = await db.payments.find_one({"id": payment_id, "user_id": user_id})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if not payment.get("transaction_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transaction ID found for this payment"
            )
        
        try:
            # Force check with Midtrans
            midtrans_status = await self.midtrans_service.check_payment_status(payment["transaction_id"])
            new_status = self.midtrans_service._map_midtrans_status(midtrans_status.get("status", "pending"))
            
            logger.info(f"Force check - Midtrans status: {midtrans_status.get('status')}, mapped to: {new_status}")
            
            # Update payment status if changed
            if new_status != payment["status"]:
                update_data = {
                    "status": new_status,
                    "midtrans_status": midtrans_status.get("status", "pending")
                }
                
                if new_status == "Success":
                    update_data["settled_at"] = datetime.utcnow()
                    # Update fee status
                    await db.fees.update_one(
                        {"id": payment["fee_id"]},
                        {"$set": {"status": "Lunas"}}
                    )
                    logger.info(f"Force check - Updated fee {payment['fee_id']} to Lunas")
                elif new_status == "Failed":
                    # Update fee status back to unpaid
                    await db.fees.update_one(
                        {"id": payment["fee_id"]},
                        {"$set": {"status": "Belum Bayar"}}
                    )
                    logger.info(f"Force check - Updated fee {payment['fee_id']} to Belum Bayar")
                
                await db.payments.update_one(
                    {"id": payment_id},
                    {"$set": update_data}
                )
                logger.info(f"Force check - Updated payment {payment_id} with data: {update_data}")
                
                return {
                    "payment_id": payment_id,
                    "status": new_status,
                    "midtrans_status": midtrans_status.get("status", "pending"),
                    "settled_at": update_data.get("settled_at"),
                    "updated": True
                }
            else:
                return {
                    "payment_id": payment_id,
                    "status": payment["status"],
                    "midtrans_status": payment.get("midtrans_status", "pending"),
                    "settled_at": payment.get("settled_at"),
                    "updated": False,
                    "message": "Status already up to date"
                }
                
        except Exception as e:
            logger.error(f"Force check failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check payment status: {str(e)}"
            )