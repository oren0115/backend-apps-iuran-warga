from app.models.schemas import Fee, FeeResponse
from app.config.database import get_database
from datetime import datetime, timedelta
import uuid

class FeeController:
    async def get_user_fees(self, user_id: str) -> list[FeeResponse]:
        """Get all fees for a specific user"""
        db = get_database()
        
        fees = await db.fees.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        return [FeeResponse(**fee) for fee in fees]

    async def generate_monthly_fees(self, bulan: str) -> dict:
        """Generate monthly fees for all users (admin only)"""
        db = get_database()
        
        # Get all non-admin users
        users = await db.users.find({"is_admin": False}).to_list(1000)
        
        fee_categories = [
            {"kategori": "Keamanan", "nominal": 50000},
            {"kategori": "Kebersihan", "nominal": 30000},
            {"kategori": "Kas", "nominal": 20000}
        ]
        
        fees_created = 0
        for user in users:
            for category in fee_categories:
                # Check if fee already exists
                existing_fee = await db.fees.find_one({
                    "user_id": user["id"],
                    "kategori": category["kategori"],
                    "bulan": bulan
                })
                
                if not existing_fee:
                    fee_dict = {
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "kategori": category["kategori"],
                        "nominal": category["nominal"],
                        "bulan": bulan,
                        "status": "Belum Bayar",
                        "due_date": datetime.utcnow() + timedelta(days=30),
                        "created_at": datetime.utcnow()
                    }
                    await db.fees.insert_one(fee_dict)
                    fees_created += 1
        
        return {"message": f"{fees_created} tagihan berhasil dibuat untuk bulan {bulan}"}

    async def get_all_fees(self) -> list[FeeResponse]:
        """Get all fees (admin only)"""
        db = get_database()
        
        fees = await db.fees.find({}, {"_id": 0}).to_list(1000)
        return [FeeResponse(**fee) for fee in fees]

    async def get_fees_by_month(self, bulan: str) -> list[FeeResponse]:
        """Get fees filtered by specific month string (format YYYY-MM) for export"""
        db = get_database()
        
        fees = await db.fees.find({"bulan": bulan}, {"_id": 0}).to_list(5000)
        return [FeeResponse(**fee) for fee in fees]

    async def update_fee_status(self, fee_id: str, status: str) -> dict:
        """Update fee status"""
        db = get_database()
        
        result = await db.fees.update_one(
            {"id": fee_id},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            return {"message": "Tagihan tidak ditemukan atau tidak ada perubahan"}
        
        return {"message": "Status tagihan berhasil diubah"}