from app.models.schemas import UserResponse
from app.utils.auth import AuthManager
from app.config.database import get_database
from datetime import datetime, timedelta
import uuid

class AdminController:
    def __init__(self):
        self.auth_manager = AuthManager()

    # Fungsi init_sample_data telah dihapus karena tidak lagi menggunakan data dummy

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
        
        # Count payments by status
        pending_payments = await db.payments.count_documents({"status": "Pending"})
        approved_payments = await db.payments.count_documents({"status": "Approved"})
        
        # Calculate total revenue
        pipeline = [
            {"$match": {"status": "Approved"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        revenue_result = await db.payments.aggregate(pipeline).to_list(1)
        total_revenue = revenue_result[0]["total"] if revenue_result else 0
        
        return {
            "total_users": total_users,
            "total_fees": total_fees,
            "paid_fees": paid_fees,
            "pending_fees": pending_fees,
            "unpaid_fees": unpaid_fees,
            "pending_payments": pending_payments,
            "approved_payments": approved_payments,
            "total_revenue": total_revenue
        }