from app.config.midtrans import midtrans_config
from app.models.schemas import MidtransPaymentRequest, PaymentCreateResponse, MidtransNotificationRequest
from app.config.database import get_database
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)

class MidtransService:
    def __init__(self):
        self.snap = midtrans_config.get_snap_client()
        self.core_api = midtrans_config.get_core_api_client()
    
    async def create_payment(self, payment_request: MidtransPaymentRequest, user_id: str, user_data: dict) -> PaymentCreateResponse:
        """Create payment transaction with Midtrans"""
        db = get_database()
        
        # Verify fee exists and belongs to user
        fee = await db.fees.find_one({"id": payment_request.fee_id, "user_id": user_id})
        if not fee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tagihan tidak ditemukan"
            )
        
        # Check if payment already exists for this fee
        existing_payment = await db.payments.find_one({
            "fee_id": payment_request.fee_id,
            "status": {"$in": ["Pending", "Approved"]}
        })
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pembayaran untuk tagihan ini sudah ada"
            )
        
        # Create transaction details
        transaction_details = {
            "order_id": f"RT-RW-{payment_request.fee_id}-{int(datetime.utcnow().timestamp())}",
            "gross_amount": fee["nominal"]
        }
        
        # Customer details
        customer_details = {
            "first_name": user_data["nama"].split()[0] if user_data["nama"] else "User",
            "last_name": " ".join(user_data["nama"].split()[1:]) if len(user_data["nama"].split()) > 1 else "",
            "email": f"{user_data['username']}@example.com",  # You might want to add email field to user
            "phone": user_data["nomor_hp"]
        }
        
        # Item details
        item_details = [{
            "id": payment_request.fee_id,
            "price": fee["nominal"],
            "quantity": 1,
            "name": f"Tagihan {fee['kategori']} - {fee['bulan']}"
        }]
        
        # Call Midtrans Snap API
        try:
            # Prepare transaction data for Snap
            transaction_data = {
                "transaction_details": transaction_details,
                "customer_details": customer_details,
                "item_details": item_details,
                "callbacks": {
                    "finish": "https://yourdomain.com/payment/finish",
                    "unfinish": "https://yourdomain.com/payment/unfinish",
                    "error": "https://yourdomain.com/payment/error"
                }
            }
            
            # Add payment method specific configurations
            if payment_request.payment_method == "credit_card":
                transaction_data["credit_card"] = {
                    "secure": True
                }
            elif payment_request.payment_method == "bank_transfer":
                transaction_data["bank_transfer"] = {
                    "bank": "bca"  # Default to BCA, you can make this configurable
                }
            elif payment_request.payment_method == "gopay":
                # GoPay will be available in Snap by default
                pass
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Metode pembayaran tidak didukung"
                )
            
            # Create Snap transaction
            response = self.snap.create_transaction(transaction_data)
            
            if response.get("status_code") != "201":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gagal membuat transaksi: {response.get('status_message', 'Unknown error')}"
                )
            
            # Save payment to database
            payment_data = {
                "id": f"payment_{int(datetime.utcnow().timestamp())}",
                "fee_id": payment_request.fee_id,
                "user_id": user_id,
                "amount": fee["nominal"],
                "method": payment_request.payment_method,
                "status": "Pending",
                "created_at": datetime.utcnow(),
                "transaction_id": response.get("transaction_id"),
                "payment_token": response.get("token"),
                "payment_url": response.get("redirect_url"),
                "midtrans_status": "pending",
                "payment_type": payment_request.payment_method,
                "bank": None,  # Will be updated via webhook
                "va_number": None,  # Will be updated via webhook
                "expiry_time": datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
            }
            
            await db.payments.insert_one(payment_data)
            
            # Update fee status
            await db.fees.update_one(
                {"id": payment_request.fee_id},
                {"$set": {"status": "Pending"}}
            )
            
            return PaymentCreateResponse(
                payment_id=payment_data["id"],
                transaction_id=payment_data["transaction_id"],
                payment_token=payment_data["payment_token"],
                payment_url=payment_data["payment_url"],
                expiry_time=payment_data["expiry_time"],
                payment_type=payment_data["payment_type"],
                bank=payment_data["bank"],
                va_number=payment_data["va_number"]
            )
            
        except Exception as e:
            logger.error(f"Midtrans payment creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal membuat pembayaran"
            )
    
    async def handle_notification(self, notification: MidtransNotificationRequest) -> dict:
        """Handle payment notification from Midtrans"""
        db = get_database()
        
        # Verify signature
        if not self._verify_signature(notification):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Find payment by transaction_id
        payment = await db.payments.find_one({"transaction_id": notification.transaction_id})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update payment status based on Midtrans status
        new_status = self._map_midtrans_status(notification.transaction_status)
        
        update_data = {
            "midtrans_status": notification.transaction_status,
            "payment_type": notification.payment_type,
            "bank": notification.bank,
            "va_number": notification.va_number
        }
        
        if new_status == "Approved":
            update_data.update({
                "status": "Approved",
                "settled_at": datetime.utcnow()
            })
            
            # Update fee status
            await db.fees.update_one(
                {"id": payment["fee_id"]},
                {"$set": {"status": "Lunas"}}
            )
        elif new_status == "Rejected":
            update_data["status"] = "Rejected"
            
            # Update fee status back to unpaid
            await db.fees.update_one(
                {"id": payment["fee_id"]},
                {"$set": {"status": "Belum Bayar"}}
            )
        
        # Update payment
        await db.payments.update_one(
            {"transaction_id": notification.transaction_id},
            {"$set": update_data}
        )
        
        return {"message": "Notification processed successfully"}
    
    def _verify_signature(self, notification: MidtransNotificationRequest) -> bool:
        """Verify Midtrans notification signature"""
        try:
            # Create signature string
            signature_string = f"{notification.order_id}{notification.status_code}{notification.gross_amount}{midtrans_config.server_key}"
            
            # Generate signature
            signature = hashlib.sha512(signature_string.encode()).hexdigest()
            
            return signature == notification.signature_key
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def _map_midtrans_status(self, midtrans_status: str) -> str:
        """Map Midtrans status to internal status"""
        status_mapping = {
            "capture": "Approved",
            "settlement": "Approved",
            "pending": "Pending",
            "deny": "Rejected",
            "cancel": "Rejected",
            "expire": "Rejected",
            "failure": "Rejected"
        }
        return status_mapping.get(midtrans_status, "Pending")
    
    async def check_payment_status(self, transaction_id: str) -> dict:
        """Check payment status from Midtrans"""
        try:
            response = self.core_api.transactions.status(transaction_id)
            return {
                "transaction_id": transaction_id,
                "status": response.get("transaction_status"),
                "payment_type": response.get("payment_type"),
                "gross_amount": response.get("gross_amount"),
                "fraud_status": response.get("fraud_status")
            }
        except Exception as e:
            logger.error(f"Failed to check payment status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal mengecek status pembayaran"
            )
