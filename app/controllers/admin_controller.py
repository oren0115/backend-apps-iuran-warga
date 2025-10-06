from app.models import UserResponse
from app.utils.auth import AuthManager
from app.config.database import get_database
from datetime import datetime, timedelta, timezone
import uuid

class AdminController:
    def __init__(self):
        self.auth_manager = AuthManager()

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
        unpaid_fees = await db.fees.count_documents({"status": "Belum Bayar"})
        
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
            "monthlyFees": monthly_fees
        }