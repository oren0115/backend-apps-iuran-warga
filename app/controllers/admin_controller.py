from app.models.schemas import UserResponse
from app.utils.auth import AuthManager
from app.config.database import get_database
from datetime import datetime, timedelta
import uuid

class AdminController:
    def __init__(self):
        self.auth_manager = AuthManager()

    async def init_sample_data(self) -> dict:
        """Initialize sample data for testing"""
        db = get_database()
        
        # Create sample users
        sample_users = [
            {
                "id": str(uuid.uuid4()),
                "username": "admin",
                "password": self.auth_manager.hash_password("admin123"),
                "nama": "Admin RT/RW",
                "alamat": "Jl. Merdeka No. 1",
                "nomor_rumah": "001",
                "nomor_hp": "08123456789",
                "is_admin": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "username": "budi",
                "password": self.auth_manager.hash_password("budi123"),
                "nama": "Budi Santoso",
                "alamat": "Jl. Melati No. 12",
                "nomor_rumah": "012",
                "nomor_hp": "08123456790",
                "is_admin": False,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "username": "siti",
                "password": self.auth_manager.hash_password("siti123"),
                "nama": "Siti Rahayu",
                "alamat": "Jl. Mawar No. 8",
                "nomor_rumah": "008",
                "nomor_hp": "08123456791",
                "is_admin": False,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Clear existing data
        await db.users.delete_many({})
        await db.fees.delete_many({})
        await db.payments.delete_many({})
        await db.notifications.delete_many({})
        
        # Insert sample users
        await db.users.insert_many(sample_users)
        
        # Generate sample fees for current month
        current_month = datetime.utcnow().strftime("%Y-%m")
        fee_categories = [
            {"kategori": "Keamanan", "nominal": 50000},
            {"kategori": "Kebersihan", "nominal": 30000},
            {"kategori": "Kas", "nominal": 20000}
        ]
        
        sample_fees = []
        for user in sample_users:
            if not user["is_admin"]:
                for category in fee_categories:
                    sample_fees.append({
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "kategori": category["kategori"],
                        "nominal": category["nominal"],
                        "bulan": current_month,
                        "status": "Belum Bayar",
                        "due_date": datetime.utcnow() + timedelta(days=30),
                        "created_at": datetime.utcnow()
                    })
        
        await db.fees.insert_many(sample_fees)
        
        return {"message": "Data sampel berhasil dibuat"}

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