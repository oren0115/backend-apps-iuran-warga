from app.models import Fee, FeeResponse, FeeRegenerationAudit
from app.config.database import get_database
from datetime import datetime, timedelta, timezone
from calendar import monthrange
import uuid

class FeeController:
    def _get_month_end_date(self, bulan: str, timezone_obj) -> datetime:
        """Calculate the last day of the month for due date"""
        try:
            # Parse bulan format (e.g., "2024-12")
            year, month = map(int, bulan.split('-'))
            
            # Get the last day of the month
            last_day = monthrange(year, month)[1]
            
            # Create datetime for the last day of the month at 23:59:59
            month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone_obj)
            
            return month_end
        except (ValueError, IndexError):
            # Fallback to 30 days from current time if parsing fails
            return datetime.now(timezone_obj) + timedelta(days=30)
    
    async def get_user_fees(self, user_id: str) -> list[FeeResponse]:
        """Get all fees for a specific user - only show latest versions (not regenerated)"""
        db = get_database()
        
        # Get all fees for the user, excluding regenerated ones
        fees = await db.fees.find({
            "user_id": user_id,
            "status": {"$ne": "Regenerated"}  # Exclude regenerated fees
        }, {"_id": 0}).to_list(1000)
        
        return [FeeResponse(**fee) for fee in fees]

    async def get_user_latest_fees(self, user_id: str) -> list[FeeResponse]:
        """Get latest fees for a specific user - handles regeneration properly"""
        db = get_database()
        
        # Get all fees for the user, excluding regenerated ones
        all_fees = await db.fees.find({
            "user_id": user_id,
            "status": {"$ne": "Regenerated"}
        }, {"_id": 0}).to_list(1000)
        
        # Group fees by month and get the latest version for each month
        fees_by_month = {}
        for fee in all_fees:
            month = fee["bulan"]
            version = fee.get("version", 1)
            
            # If no fee for this month yet, or this fee has higher version
            if month not in fees_by_month or version > fees_by_month[month].get("version", 1):
                fees_by_month[month] = fee
        
        # Convert to list and sort by month (newest first)
        latest_fees = list(fees_by_month.values())
        latest_fees.sort(key=lambda x: x["bulan"], reverse=True)
        
        return [FeeResponse(**fee) for fee in latest_fees]

    async def generate_monthly_fees(self, bulan: str, tarif_config: dict) -> dict:
        """Generate monthly fees for all users (admin only)
        Tarif IPL tidak di-hardcode; diterima dari frontend via tarif_config.
        tarif_config keys: 60M2, 72M2, HOOK (case-insensitive supported)
        """
        db = get_database()
        
        # Use Jakarta timezone for all timestamps
        jakarta_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(jakarta_tz)
        
        # Calculate due date as last day of the month
        due_date = self._get_month_end_date(bulan, jakarta_tz)
        
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
                    "due_date": due_date,
                    "created_at": current_time
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

    async def regenerate_fees_for_month(self, bulan: str, tarif_config: dict, admin_user: str = "system") -> dict:
        """Smart regenerate fees for a specific month - PRESERVE PAYMENT HISTORY"""
        db = get_database()
        jakarta_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(jakarta_tz)
        
        # Check for existing paid fees
        paid_fees = await db.fees.find({
            "bulan": bulan,
            "status": {"$in": ["Berhasil", "Selesai", "Lunas"]}
        }).to_list(1000)
        
        unpaid_fees = await db.fees.find({
            "bulan": bulan,
            "status": {"$in": ["Belum Bayar", "Menunggu Verifikasi"]}
        }).to_list(1000)
        
        # Soft delete unpaid fees (mark as regenerated)
        if unpaid_fees:
            await db.fees.update_many(
                {
                    "bulan": bulan,
                    "status": {"$in": ["Belum Bayar", "Menunggu Verifikasi"]}
                },
                {
                    "$set": {
                        "status": "Regenerated",
                        "regenerated_at": current_time,
                        "regenerated_reason": "Admin regenerate with new rates",
                        "is_regenerated": True
                    }
                }
            )
        
        # Generate new fees
        fees_created = await self._generate_fees_for_month(bulan, tarif_config, current_time, jakarta_tz)
        
        # Create audit log
        audit_log = {
            "id": str(uuid.uuid4()),
            "action": "regenerate_fees",
            "month": bulan,
            "admin_user": admin_user,
            "timestamp": current_time,
            "details": {
                "tarif_config": tarif_config,
                "paid_fees_preserved": len(paid_fees),
                "unpaid_fees_regenerated": len(unpaid_fees)
            },
            "affected_fees_count": len(unpaid_fees) + fees_created,
            "paid_fees_preserved": len(paid_fees),
            "unpaid_fees_regenerated": len(unpaid_fees),
            "reason": "Admin regenerate with new rates"
        }
        await db.fee_audit_logs.insert_one(audit_log)
        
        message = f"{fees_created} tagihan berhasil dibuat ulang untuk bulan {bulan}"
        if paid_fees:
            message += f". {len(paid_fees)} tagihan yang sudah dibayar tetap dipertahankan."
        
        return {
            "message": message,
            "paid_fees_preserved": len(paid_fees),
            "unpaid_fees_regenerated": len(unpaid_fees),
            "new_fees_created": fees_created
        }

    async def _generate_fees_for_month(self, bulan: str, tarif_config: dict, current_time: datetime, jakarta_tz: timezone) -> int:
        """Helper method to generate fees for a month"""
        db = get_database()
        
        # Calculate due date as last day of the month
        due_date = self._get_month_end_date(bulan, jakarta_tz)
        
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
                "due_date": due_date,
                "created_at": current_time,
                "version": 1,
                "regenerated_at": None,
                "regenerated_reason": None,
                "parent_fee_id": None,
                "is_regenerated": False
            }
            await db.fees.insert_one(fee_dict)
            fees_created += 1
        
        return fees_created

    async def get_regeneration_history(self, bulan: str) -> list[dict]:
        """Get regeneration history for a specific month"""
        db = get_database()
        
        history = await db.fee_audit_logs.find(
            {"month": bulan, "action": "regenerate_fees"},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(100)
        
        return history

    async def get_fee_versions(self, fee_id: str) -> list[dict]:
        """Get all versions of a specific fee"""
        db = get_database()
        
        # Get the original fee
        original_fee = await db.fees.find_one({"id": fee_id}, {"_id": 0})
        if not original_fee:
            return []
        
        # Get all fees for the same user and month
        versions = await db.fees.find(
            {
                "user_id": original_fee["user_id"],
                "bulan": original_fee["bulan"],
                "kategori": original_fee["kategori"]
            },
            {"_id": 0}
        ).sort("created_at", 1).to_list(100)
        
        return versions

    async def rollback_regeneration(self, bulan: str, admin_user: str = "system") -> dict:
        """Rollback last regeneration for a month"""
        db = get_database()
        jakarta_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(jakarta_tz)
        
        # Get the last regeneration audit log
        last_regeneration = await db.fee_audit_logs.find_one(
            {"month": bulan, "action": "regenerate_fees"},
            sort=[("timestamp", -1)]
        )
        
        if not last_regeneration:
            return {"message": "Tidak ada regenerasi untuk bulan ini", "success": False}
        
        # Restore regenerated fees to unpaid status
        result = await db.fees.update_many(
            {
                "bulan": bulan,
                "status": "Regenerated",
                "regenerated_at": {"$gte": last_regeneration["timestamp"]}
            },
            {
                "$set": {
                    "status": "Belum Bayar",
                    "regenerated_at": None,
                    "regenerated_reason": None,
                    "is_regenerated": False
                }
            }
        )
        
        # Delete the new fees created in last regeneration
        await db.fees.delete_many({
            "bulan": bulan,
            "created_at": {"$gte": last_regeneration["timestamp"]},
            "version": 1,
            "is_regenerated": False
        })
        
        # Create rollback audit log
        rollback_audit = {
            "id": str(uuid.uuid4()),
            "action": "rollback",
            "month": bulan,
            "admin_user": admin_user,
            "timestamp": current_time,
            "details": {
                "rolled_back_regeneration": last_regeneration["id"],
                "fees_restored": result.modified_count
            },
            "affected_fees_count": result.modified_count,
            "reason": "Admin rollback regeneration"
        }
        await db.fee_audit_logs.insert_one(rollback_audit)
        
        return {
            "message": f"Rollback berhasil. {result.modified_count} tagihan dikembalikan ke status 'Belum Bayar'",
            "success": True,
            "fees_restored": result.modified_count
        }