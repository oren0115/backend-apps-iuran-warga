from app.config.midtrans import midtrans_config
from app.models import MidtransPaymentRequest, PaymentCreateResponse, MidtransNotificationRequest
from app.config.database import get_database
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
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
        
        # Check if Midtrans is properly configured
        if not self.snap or not self.core_api:
            logger.error("Midtrans not properly configured - missing API keys")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Midtrans tidak dikonfigurasi dengan benar. Silakan hubungi administrator."
            )
        
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
        # Generate shorter order_id (max 50 chars for Midtrans)
        # Use UTC for consistent timestamp
        timestamp = int(datetime.now(timezone.utc).timestamp())
        order_id = f"RT{timestamp}{payment_request.fee_id[-8:]}"  # Use last 8 chars of fee_id
        transaction_details = {
            "order_id": order_id,
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
                "callbacks": midtrans_config.get_frontend_callback_urls(),
                "notification_url": midtrans_config.get_notification_url()
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
            try:
                response = self.snap.create_transaction(transaction_data)
            except Exception as api_error:
                logger.error(f"Midtrans API call failed: {str(api_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Gagal menghubungi Midtrans: {str(api_error)}"
                )
            
            # Check if response contains required fields (Snap API success indicators)
            if not response.get("token") or not response.get("redirect_url"):
                error_msg = response.get('status_message', 'Invalid response from Midtrans')
                logger.error(f"Midtrans API error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gagal membuat transaksi: {error_msg}"
                )
            
            # Generate transaction_id if not provided by Midtrans (Snap API doesn't return it)
            transaction_id = response.get("transaction_id") or f"txn_{timestamp}_{payment_request.fee_id[-8:]}"
            
            # Save payment to database with UTC timezone
            current_time = datetime.now(timezone.utc)
            payment_data = {
                "id": f"pay_{timestamp}",
                "fee_id": payment_request.fee_id,
                "user_id": user_id,
                "order_id": order_id,
                "amount": fee["nominal"],
                "payment_method": payment_request.payment_method,
                "status": "Pending",
                "created_at": current_time,
                "transaction_id": transaction_id,
                "payment_token": response.get("token"),
                "payment_url": response.get("redirect_url"),
                "midtrans_status": "pending",
                "payment_type": payment_request.payment_method,
                "bank": None,  # Will be updated via webhook
                "va_number": None,  # Will be updated via webhook
                "expiry_time": current_time + timedelta(hours=24)  # Default 24 hours expiry
            }
            
            await db.payments.insert_one(payment_data)
            
            # Update fee status
            await db.fees.update_one(
                {"id": payment_request.fee_id},
                {"$set": {"status": "Pending"}}
            )
            
            return PaymentCreateResponse(
                payment_id=payment_data["id"],
                order_id=order_id,
                transaction_id=transaction_id,
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
            logger.error(f"Invalid signature for notification: {notification.dict()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Find payment by transaction_id; fallback to order_id
        payment = await db.payments.find_one({"transaction_id": notification.transaction_id})
        if not payment:
            payment = await db.payments.find_one({"order_id": notification.order_id})
            if payment and not payment.get("transaction_id"):
                # Backfill transaction_id from notification
                await db.payments.update_one(
                    {"id": payment["id"]}, {"$set": {"transaction_id": notification.transaction_id}}
                )
                payment["transaction_id"] = notification.transaction_id
        if not payment:
            logger.error(
                f"Payment not found for transaction_id: {notification.transaction_id} or order_id: {notification.order_id}"
            )
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
        
        if new_status == "Success":
            # Use UTC for settled_at
            update_data.update({
                "status": "Success",
                "settled_at": datetime.now(timezone.utc)
            })
            
            # Update fee status
            await db.fees.update_one(
                {"id": payment["fee_id"]},
                {"$set": {"status": "Lunas"}}
            )
            
        elif new_status == "Failed":
            update_data["status"] = "Failed"
            
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
            "capture": "Success",
            "settlement": "Success", 
            "pending": "Pending",
            "deny": "Failed",
            "cancel": "Failed",
            "expire": "Failed",
            "failure": "Failed"
        }
        return status_mapping.get(midtrans_status, "Pending")
    
    async def check_payment_status(self, identifier: str) -> dict:
        """Check payment status from Midtrans using order_id (preferred) or transaction_id"""
        try:
            # If identifier looks like a transaction_id (UUID format), try to find the order_id first
            if len(identifier) == 36 and identifier.count('-') == 4:  # UUID format
                db = get_database()
                payment = await db.payments.find_one({"transaction_id": identifier})
                if payment and payment.get("order_id"):
                    identifier = payment["order_id"]
                else:
                    logger.error(f"No order_id found for transaction_id {identifier}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Transaction not found in database"
                    )
            
            # Midtrans Core API expects order_id for status checks
            response = self.core_api.transactions.status(identifier)
            
            if not response:
                logger.error(f"Empty response from Midtrans for order_id: {identifier}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found in Midtrans"
                )
            
            return {
                "identifier": identifier,
                "status": response.get("transaction_status"),
                "payment_type": response.get("payment_type"),
                "gross_amount": response.get("gross_amount"),
                "fraud_status": response.get("fraud_status")
            }
        except Exception as e:
            error_status = getattr(e, 'status_code', 'Unknown')
            logger.error(f"Failed to check payment status: Midtrans API is returning API error. API status code: `{error_status}`.")
            if hasattr(e, 'response') and e.response:
                logger.error(f"API response: {e.response}")
            
            # Handle specific error cases
            if error_status == 404:
                # Try to update the payment status to expired if it's still pending
                try:
                    db = get_database()
                    payment = await db.payments.find_one({"order_id": identifier})
                    if payment and payment.get("status") == "Pending":
                        await db.payments.update_one(
                            {"order_id": identifier},
                            {"$set": {"status": "Failed", "midtrans_status": "expire"}}
                        )
                        # Update fee status back to unpaid
                        await db.fees.update_one(
                            {"id": payment["fee_id"]},
                            {"$set": {"status": "Belum Bayar"}}
                        )
                except Exception as update_error:
                    logger.error(f"Failed to update expired payment: {str(update_error)}")
                
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaksi tidak ditemukan di Midtrans. Mungkin sudah expired atau dibatalkan."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Gagal mengecek status pembayaran"
                )
