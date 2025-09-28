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

    async def generate_monthly_fees(self, bulan: str, tarif_config: dict) -> dict:
        """Generate monthly fees for all users (admin only)
        Tarif IPL tidak di-hardcode; diterima dari frontend via tarif_config.
        tarif_config keys: 60M2, 72M2, HOOK (case-insensitive supported)
        """
        db = get_database()
        
        # Get all non-admin users
        users = await db.users.find({"is_admin": False}).to_list(1000)
        
        fees_created = 0
        for user in users:
            tipe = (user.get("tipe_rumah") or "").upper()
            # Normalisasi tipe agar sesuai keys config
            if tipe in ["60M2", "60", "60 M2", "TYPE 60", "TYPE60"]:
                key = "60M2"
            elif tipe in ["72M2", "72", "72 M2", "TYPE 72", "TYPE72"]:
                key = "72M2"
            elif tipe in ["HOOK", "TYPE HOOK", "TIPE HOOK"]:
                key = "HOOK"
            else:
                # Jika tipe tidak dikenali, lewati pembuatan tagihan untuk user tsb
                continue

            # Ambil nominal dari tarif_config; dukung variasi key case
            nominal = (
                tarif_config.get(key)
                or tarif_config.get(key.lower())
                or tarif_config.get(key.capitalize())
            )
            if not isinstance(nominal, int) or nominal <= 0:
                continue

            # Buat satu tagihan IPL per user per bulan berdasarkan tipe rumah
            existing_fee = await db.fees.find_one({
                "user_id": user["id"],
                "kategori": key,  # simpan kategori sebagai tipe rumah
                "bulan": bulan
            })
            if not existing_fee:
                fee_dict = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "kategori": key,
                    "nominal": nominal,
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

    async def regenerate_fees_for_month(self, bulan: str, tarif_config: dict) -> dict:
        """Regenerate fees for a specific month based on current user house types (admin only)"""
        db = get_database()
        
        # Delete existing fees for the month
        await db.fees.delete_many({"bulan": bulan})
        
        # Get all non-admin users
        users = await db.users.find({"is_admin": False}).to_list(1000)
        
        fees_created = 0
        for user in users:
            tipe = (user.get("tipe_rumah") or "").upper()
            # Normalisasi tipe agar sesuai keys config
            if tipe in ["60M2", "60", "60 M2", "TYPE 60", "TYPE60"]:
                key = "60M2"
            elif tipe in ["72M2", "72", "72 M2", "TYPE 72", "TYPE72"]:
                key = "72M2"
            elif tipe in ["HOOK", "TYPE HOOK", "TIPE HOOK"]:
                key = "HOOK"
            else:
                # Jika tipe tidak dikenali, lewati pembuatan tagihan untuk user tsb
                continue

            # Ambil nominal dari tarif_config; dukung variasi key case
            nominal = (
                tarif_config.get(key)
                or tarif_config.get(key.lower())
                or tarif_config.get(key.capitalize())
            )
            if not isinstance(nominal, int) or nominal <= 0:
                continue

            # Buat tagihan IPL per user per bulan berdasarkan tipe rumah
            fee_dict = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "kategori": key,
                "nominal": nominal,
                "bulan": bulan,
                "status": "Belum Bayar",
                "due_date": datetime.utcnow() + timedelta(days=30),
                "created_at": datetime.utcnow()
            }
            await db.fees.insert_one(fee_dict)
            fees_created += 1
        
        return {"message": f"{fees_created} tagihan berhasil dibuat ulang untuk bulan {bulan}"}