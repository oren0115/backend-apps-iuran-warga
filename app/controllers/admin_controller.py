from app.models import UserResponse
from app.security.auth import AuthManager
from app.config.database import get_database
from app.services.websocket_manager import websocket_manager
from datetime import datetime, timedelta, timezone
import uuid

class AdminController:
    def __init__(self):
        self.auth_manager = AuthManager()

    async def broadcast_dashboard_update(self):
        """Broadcast dashboard stats update to all connected admin users"""
        try:
            # Get updated dashboard stats
            dashboard_stats = await self.get_dashboard_stats()
            
            # Broadcast to all connected users
            await websocket_manager.broadcast_to_all({
                "type": "dashboard_update",
                "data": dashboard_stats
            })
        except Exception as e:
            print(f"Failed to broadcast dashboard update: {e}")

    async def init_sample_data(self) -> dict:
        """Initialize sample data for testing"""
        db = get_database()
        
        # Clear existing data
        await db.users.delete_many({})
        await db.fees.delete_many({})
        await db.payments.delete_many({})
        await db.notifications.delete_many({})

    async def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics (admin only)"""
        db = get_database()
        
        # Count users
        total_users = await db.users.count_documents({"is_admin": False})
        
        # Count fees by status
        total_fees = await db.fees.count_documents({})
        paid_fees = await db.fees.count_documents({"status": "Lunas"})
        pending_fees = await db.fees.count_documents({"status": "Pending"})
        
        # Count unpaid fees: includes "Belum Bayar" and fees with failed payments
        unpaid_fees = await db.fees.count_documents({"status": "Belum Bayar"})
        
        # Also count fees that have failed payments (Deny, Cancel, Expire)
        failed_payment_fees = await db.fees.aggregate([
            {
                "$lookup": {
                    "from": "payments",
                    "localField": "id",
                    "foreignField": "fee_id",
                    "as": "payments"
                }
            },
            {
                "$match": {
                    "status": {"$in": ["Belum Bayar", "Pending"]},
                    "payments.status": {"$in": ["Deny", "Cancel", "Expire"]}
                }
            },
            {
                "$count": "count"
            }
        ]).to_list(1)
        
        # Add failed payment fees to unpaid count
        if failed_payment_fees:
            unpaid_fees += failed_payment_fees[0].get("count", 0)
        
        # Count payments by status - using correct status values
        pending_payments = await db.payments.count_documents({"status": "Pending"})
        approved_payments = await db.payments.count_documents({
            "$or": [{"status": "Settlement"}, {"status": "Success"}]
        })
        
        # Calculate current month collection
        jakarta_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(jakarta_tz)
        current_month = current_time.strftime("%Y-%m")
        
        # Get current month fees
        current_month_fees = await db.fees.find({"bulan": current_month}).to_list(None)
        current_month_collection = sum(fee.get("nominal", 0) for fee in current_month_fees if fee.get("status") == "Lunas")
        
        # Calculate collection rate
        total_expected = sum(fee.get("nominal", 0) for fee in current_month_fees)
        collection_rate = round((current_month_collection / total_expected * 100) if total_expected > 0 else 0, 1)
        
        # Calculate monthly fees for chart (last 6 months)
        monthly_fees = []
        for i in range(6):
            month_date = current_time - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m")
            month_name = month_date.strftime("%b")
            
            month_fees = await db.fees.find({"bulan": month_str}).to_list(None)
            month_total = sum(fee.get("nominal", 0) for fee in month_fees if fee.get("status") == "Lunas")
            
            monthly_fees.append({
                "month": month_name,
                "total": month_total
            })
        
        monthly_fees.reverse()  # Show oldest to newest
        
        return {
            "totalUsers": total_users,
            "totalFees": total_fees,
            "pendingPayments": pending_payments,
            "approvedPayments": approved_payments,
            "currentMonthCollection": current_month_collection,
            "collectionRate": collection_rate,
            "monthlyFees": monthly_fees,
            "unpaidFees": unpaid_fees
        }

    async def get_unpaid_users(self, bulan: str = None) -> list[dict]:
        """Get users who haven't paid their fees (admin only)"""
        db = get_database()
        
        # Get current month if not specified
        if bulan is None:
            jakarta_tz = timezone(timedelta(hours=7))
            current_time = datetime.now(jakarta_tz)
            bulan = current_time.strftime("%Y-%m")
        
        # Get all unpaid fees for specified month (including failed payments)
        unpaid_fees = await db.fees.aggregate([
            {
                "$lookup": {
                    "from": "payments",
                    "localField": "id",
                    "foreignField": "fee_id",
                    "as": "payments"
                }
            },
            {
                "$match": {
                    "bulan": bulan,
                    "$or": [
                        {"status": "Belum Bayar"},
                        {
                            "status": "Pending",
                            "payments.status": {"$in": ["Deny", "Cancel", "Expire"]}
                        }
                    ]
                }
            }
        ]).to_list(1000)
        
        # Get user details for each unpaid fee
        unpaid_users = []
        for fee in unpaid_fees:
            user = await db.users.find_one({"id": fee["user_id"]}, {"_id": 0})
            
            # Get latest payment status for this fee
            latest_payment = None
            if fee.get("payments"):
                # Sort by created_at descending to get the latest payment
                latest_payment = sorted(fee["payments"], key=lambda x: x.get("created_at", ""), reverse=True)[0]
            
            if user:
                # User exists - normal case
                unpaid_users.append({
                    "user_id": user["id"],
                    "username": user["username"],
                    "nama": user["nama"],
                    "nomor_rumah": user.get("nomor_rumah", ""),
                    "nomor_hp": user.get("nomor_hp", ""),
                    "tipe_rumah": user.get("tipe_rumah", ""),
                    "fee_id": fee["id"],
                    "kategori": fee["kategori"],
                    "nominal": fee["nominal"],
                    "due_date": fee["due_date"],
                    "created_at": fee["created_at"],
                    "is_orphaned": False,
                    "payment_status": latest_payment.get("status") if latest_payment else None,
                    "payment_failed": latest_payment.get("status") in ["Deny", "Cancel", "Expire"] if latest_payment else False
                })
            else:
                # User deleted but fee exists - orphaned fee
                unpaid_users.append({
                    "user_id": fee["user_id"],
                    "username": "USER DIHAPUS",
                    "nama": "User Sudah Dihapus",
                    "nomor_rumah": "N/A",
                    "nomor_hp": "N/A",
                    "tipe_rumah": "N/A",
                    "fee_id": fee["id"],
                    "kategori": fee["kategori"],
                    "nominal": fee["nominal"],
                    "due_date": fee["due_date"],
                    "created_at": fee["created_at"],
                    "is_orphaned": True,
                    "payment_status": latest_payment.get("status") if latest_payment else None,
                    "payment_failed": latest_payment.get("status") in ["Deny", "Cancel", "Expire"] if latest_payment else False
                })
        
        return unpaid_users

    async def get_paid_users(self, bulan: str = None) -> list[dict]:
        """Get users who have paid their fees (admin only)"""
        db = get_database()
        
        # Get current month if not specified
        if bulan is None:
            jakarta_tz = timezone(timedelta(hours=7))
            current_time = datetime.now(jakarta_tz)
            bulan = current_time.strftime("%Y-%m")
        
        # Get all paid fees for specified month
        paid_fees = await db.fees.find({
            "status": "Lunas",
            "bulan": bulan
        }).to_list(1000)
        
        # Get user details for each paid fee
        paid_users = []
        for fee in paid_fees:
            user = await db.users.find_one({"id": fee["user_id"]}, {"_id": 0})
            if user:
                # Get payment details for this fee
                payment = await db.payments.find_one(
                    {"fee_id": fee["id"], "status": {"$in": ["Settlement", "Success"]}},
                    {"_id": 0}
                )
                
                paid_users.append({
                    "user_id": user["id"],
                    "username": user["username"],
                    "nama": user["nama"],
                    "nomor_rumah": user.get("nomor_rumah", ""),
                    "nomor_hp": user.get("nomor_hp", ""),
                    "tipe_rumah": user.get("tipe_rumah", ""),
                    "fee_id": fee["id"],
                    "kategori": fee["kategori"],
                    "nominal": fee["nominal"],
                    "due_date": fee["due_date"],
                    "created_at": fee["created_at"],
                    "payment_date": payment.get("settled_at", payment.get("created_at", "")) if payment else "",
                    "payment_method": payment.get("payment_method", "") if payment else "",
                    "is_orphaned": False
                })
            else:
                # User deleted but fee exists - orphaned fee
                paid_users.append({
                    "user_id": fee["user_id"],
                    "username": "USER DIHAPUS",
                    "nama": "User Sudah Dihapus",
                    "nomor_rumah": "N/A",
                    "nomor_hp": "N/A",
                    "tipe_rumah": "N/A",
                    "fee_id": fee["id"],
                    "kategori": fee["kategori"],
                    "nominal": fee["nominal"],
                    "due_date": fee["due_date"],
                    "created_at": fee["created_at"],
                    "payment_date": "",
                    "payment_method": "",
                    "is_orphaned": True
                })
        
        return paid_users