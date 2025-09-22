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
        timestamp = int(datetime.utcnow().timestamp())
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
                "callbacks": {
                    "finish": "https://yourdomain.com/payment/finish",
                    "unfinish": "https://yourdomain.com/payment/unfinish", 
                    "error": "https://yourdomain.com/payment/error"
                },
                "notification_url": "https://yourdomain.com/api/payments/notification"
            }
            
            # Log transaction data for debugging
            logger.info(f"Creating Midtrans transaction with order_id: {order_id}")
            logger.info(f"Transaction data: {transaction_data}")
            
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
            
            # Log response for debugging
            logger.info(f"Midtrans response: {response}")
            
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
            
            # Save payment to database
            payment_data = {
                "id": f"pay_{timestamp}",
                "fee_id": payment_request.fee_id,
                "user_id": user_id,
                "amount": fee["nominal"],
                "payment_method": payment_request.payment_method,
                "status": "Pending",
                "created_at": datetime.utcnow(),
                "transaction_id": transaction_id,
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
        
        # Log notification for debugging
        logger.info(f"Received Midtrans notification: {notification.dict()}")
        
        # Verify signature
        if not self._verify_signature(notification):
            logger.error(f"Invalid signature for notification: {notification.dict()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Find payment by transaction_id
        payment = await db.payments.find_one({"transaction_id": notification.transaction_id})
        if not payment:
            logger.error(f"Payment not found for transaction_id: {notification.transaction_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        logger.info(f"Found payment: {payment['id']} with current status: {payment['status']}")
        
        # Update payment status based on Midtrans status
        new_status = self._map_midtrans_status(notification.transaction_status)
        logger.info(f"Mapping Midtrans status '{notification.transaction_status}' to '{new_status}'")
        
        update_data = {
            "midtrans_status": notification.transaction_status,
            "payment_type": notification.payment_type,
            "bank": notification.bank,
            "va_number": notification.va_number
        }
        
        if new_status == "Success":
            update_data.update({
                "status": "Success",
                "settled_at": datetime.utcnow()
            })
            
            logger.info(f"Updating payment to Success status for payment: {payment['id']}")
            
            # Update fee status
            await db.fees.update_one(
                {"id": payment["fee_id"]},
                {"$set": {"status": "Lunas"}}
            )
            logger.info(f"Updated fee {payment['fee_id']} to Lunas status")
            
        elif new_status == "Failed":
            update_data["status"] = "Failed"
            logger.info(f"Updating payment to Failed status for payment: {payment['id']}")
            
            # Update fee status back to unpaid
            await db.fees.update_one(
                {"id": payment["fee_id"]},
                {"$set": {"status": "Belum Bayar"}}
            )
            logger.info(f"Updated fee {payment['fee_id']} to Belum Bayar status")
        
        # Update payment
        await db.payments.update_one(
            {"transaction_id": notification.transaction_id},
            {"$set": update_data}
        )
        logger.info(f"Updated payment {payment['id']} with data: {update_data}")
        
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
