from app.models import Notification, NotificationResponse
from app.config.database import get_database
from app.services.websocket_manager import websocket_manager
import uuid
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class NotificationController:
    async def get_user_notifications(self, user_id: str) -> list[NotificationResponse]:
        """Get all notifications for a specific user"""
        db = get_database()
        
        notifications = await db.notifications.find(
            {"user_id": user_id}, 
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return [NotificationResponse(**notification) for notification in notifications]

    async def create_notification(self, user_id: str, title: str, message: str, notification_type: str = "pengumuman") -> NotificationResponse:
        """Create a new notification"""
        db = get_database()
        
        # Use UTC timezone for created_at (consistent with payment data)
        utc_tz = timezone.utc
        notification_dict = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "is_read": False,
            "created_at": datetime.now(utc_tz)
        }
        
        await db.notifications.insert_one(notification_dict)
        
        return NotificationResponse(**notification_dict)

    async def create_bulk_notifications(self, title: str, message: str, notification_type: str = "pengumuman") -> dict:
        """Create notifications for all users (admin only)"""
        db = get_database()
        
        # Use UTC timezone for created_at (consistent with payment data)
        utc_tz = timezone.utc
        current_time = datetime.now(utc_tz)
        
        # Get all users
        users = await db.users.find({}, {"_id": 0}).to_list(1000)
        
        notifications = []
        for user in users:
            notification_data = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "title": title,
                "message": message,
                "type": notification_type,
                "is_read": False,
                "created_at": current_time
            }
            notifications.append(notification_data)
        
        if notifications:
            # Insert notifications to database
            await db.notifications.insert_many(notifications)
            
            # Send real-time notifications to connected users in parallel
            import asyncio
            tasks = []
            for notification in notifications:
                task = websocket_manager.send_notification(
                    notification["user_id"], 
                    notification
                )
                tasks.append(task)
            
            # Execute all WebSocket sends in parallel
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        return {"message": f"Notifikasi berhasil dikirim ke {len(notifications)} pengguna"}

    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> dict:
        """Mark a notification as read"""
        db = get_database()
        
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": user_id},
            {"$set": {"is_read": True}}
        )
        
        if result.modified_count == 0:
            return {"message": "Notifikasi tidak ditemukan atau sudah dibaca"}
        
        return {"message": "Notifikasi berhasil ditandai sebagai telah dibaca"}

    async def delete_notification(self, notification_id: str, user_id: str) -> dict:
        """Delete a notification"""
        db = get_database()
        
        result = await db.notifications.delete_one({"id": notification_id, "user_id": user_id})
        
        if result.deleted_count == 0:
            return {"message": "Notifikasi tidak ditemukan"}
        
        return {"message": "Notifikasi berhasil dihapus"}